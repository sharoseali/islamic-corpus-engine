"""Build search.chunks: split every search document into passages and embed them.

Derived data only (see app.models.search_chunks). Deterministic: the same
documents, chunker version and model files produce the same chunks and
vectors. Resumable: documents that already have chunks are skipped, so an
interrupted run continues where it stopped.

Run:  qlib/bin/python -m app.services.embedding_indexer
"""

import re
import sys
import time
from datetime import datetime, timezone

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.search import SearchDocument
from app.models.search_chunks import EMBEDDING_DIM, EmbeddingState, SearchChunk
from app.services import embeddings

CHUNKER_VERSION = "1.0.0"

# Passage sizing in characters. Arabic and Urdu run roughly three to four
# characters per model token, so 1000 chars stays inside the 512-token
# window with room for the prefix.
TARGET_CHARS = 1000
MAX_SINGLE_CHUNK = 1300  # shorter documents are embedded whole
MIN_TAIL_CHARS = 200  # a trailing fragment shorter than this joins the previous chunk

EMBED_BATCH = 32
COMMIT_EVERY_DOCS = 200

# Documents are processed short-first so the index becomes useful early.
DOC_TYPE_ORDER = ["quran_verse", "quran_translation", "hadith_text", "tafsir_entry"]

_HTML_TAG = re.compile(r"<[^>]+>")
# Manuscript variant notes in the Arabic Ibn Kathir edition: [[في جـ: ...]]
_EDITORIAL_NOTE = re.compile(r"\[\[.*?\]\]", re.S)
_PARAGRAPH_BREAK = re.compile(r"\n\s*\n|\s*٭٭\s*|\n")
_SENTENCE_END = re.compile(r"(?<=[.!?؟۔])\s+")
# Classical Arabic text has few full stops; fall back to clause boundaries.
_CLAUSE_END = re.compile(r"(?<=[،,;؛:])\s+")
_SPACES = re.compile(r"[ \t]+")


# Tashkeel, Quranic signs and tatweel. Vocalised Arabic costs the model
# about one token per character and most of its training text is
# unvocalised, so the marks are removed from what the model reads (never
# from what is displayed). Also halves the work.
_DIACRITICS = re.compile("[\u0610-\u061a\u064b-\u065f\u06d6-\u06ed\u0640]")


def clean_for_embedding(text_: str) -> str:
    """Display text -> plain prose for the model (markup, notes, marks removed)."""
    text_ = _HTML_TAG.sub(" ", text_)
    text_ = _EDITORIAL_NOTE.sub(" ", text_)
    text_ = _DIACRITICS.sub("", text_)
    return _SPACES.sub(" ", text_).strip()


def _split_long_unit(unit: str, offset: int) -> list[tuple[int, int]]:
    """Break a sentence longer than TARGET_CHARS at clauses, then at words."""
    if len(unit) <= TARGET_CHARS:
        return [(offset, offset + len(unit))]
    out: list[tuple[int, int]] = []
    pos = 0
    pieces = _CLAUSE_END.split(unit) if _CLAUSE_END.search(unit) else [unit]
    for piece in pieces:
        if not piece:
            continue
        p = unit.index(piece, pos)
        pos = p + len(piece)
        if len(piece) <= TARGET_CHARS:
            out.append((offset + p, offset + p + len(piece)))
            continue
        # Hard fallback: cut at the last space before the limit.
        q = 0
        while q < len(piece):
            end = min(q + TARGET_CHARS, len(piece))
            if end < len(piece):
                sp = piece.rfind(" ", q + TARGET_CHARS // 2, end)
                if sp > 0:
                    end = sp
            out.append((offset + p + q, offset + p + end))
            q = end
            while q < len(piece) and piece[q] == " ":
                q += 1
    return out


def chunk_spans(display: str) -> list[tuple[int, int]]:
    """Character spans of passages inside the display text."""
    if len(display) <= MAX_SINGLE_CHUNK:
        return [(0, len(display))]

    # Sentence-level units with their offsets, paragraph breaks respected.
    units: list[tuple[int, int]] = []
    pos = 0
    for para in _PARAGRAPH_BREAK.split(display):
        if not para:
            continue
        start = display.index(para, pos)
        pos = start + len(para)
        inner = 0
        for sent in _SENTENCE_END.split(para):
            if not sent:
                continue
            s = para.index(sent, inner)
            inner = s + len(sent)
            for u in _split_long_unit(sent, start + s):
                units.append(u)

    spans: list[tuple[int, int]] = []
    cur_start: int | None = None
    cur_end = 0
    for s, e in units:
        if cur_start is None:
            cur_start, cur_end = s, e
        elif e - cur_start <= TARGET_CHARS:
            cur_end = e
        else:
            spans.append((cur_start, cur_end))
            cur_start, cur_end = s, e
    if cur_start is not None:
        if spans and cur_end - cur_start < MIN_TAIL_CHARS:
            spans[-1] = (spans[-1][0], cur_end)
        else:
            spans.append((cur_start, cur_end))
    return spans


class EmbeddingIndexer:
    def __init__(self, session: Session):
        self.session = session

    def pending_documents(self):
        """Documents without chunks, short types first, stable order."""
        order = " ".join(f"WHEN '{t}' THEN {i}" for i, t in enumerate(DOC_TYPE_ORDER))
        return self.session.execute(
            text(
                f"""
                SELECT d.id, d.doc_type, d.language_code, d.collection_key,
                       d.citation, d.text_display
                FROM search.documents d
                LEFT JOIN search.chunks c ON c.document_id = d.id
                WHERE c.id IS NULL
                ORDER BY CASE d.doc_type {order} ELSE 99 END, d.id
                """
            )
        )

    def build(self, log=print) -> dict:
        total_docs = self.session.scalar(select(func.count()).select_from(SearchDocument))
        done_docs = self.session.scalar(
            select(func.count(func.distinct(SearchChunk.document_id)))
        )
        log(f"documents: {total_docs}, already embedded: {done_docs}")
        log(f"embedding device: {embeddings.get_embedder().device}")

        # (doc meta, chunk_index, start, end, passage, vector-or-None)
        pending_rows: list[tuple] = []
        docs_in_batch = 0
        processed = 0
        reused = 0
        started = time.time()
        # Ibn Kathir repeats one commentary for every ayah of a group, so
        # identical texts arrive back to back; their vectors are reused.
        recent: dict[str, list] = {}

        def flush():
            nonlocal pending_rows, docs_in_batch
            if not pending_rows:
                return
            todo = [i for i, r in enumerate(pending_rows) if r[5] is None]
            if todo:
                vectors = embeddings.embed_passages(
                    [pending_rows[i][4] for i in todo], EMBED_BATCH
                )
                for i, vec in zip(todo, vectors):
                    r = pending_rows[i]
                    pending_rows[i] = (*r[:5], vec)
            self.session.execute(
                SearchChunk.__table__.insert(),
                [
                    {
                        "document_id": r[0]["id"],
                        "chunk_index": r[1],
                        "doc_type": r[0]["doc_type"],
                        "language_code": r[0]["language_code"],
                        "collection_key": r[0]["collection_key"],
                        "text": r[4],
                        "char_start": r[2],
                        "char_end": r[3],
                        "embedding": r[5].tolist(),
                    }
                    for r in pending_rows
                ],
            )
            self.session.commit()
            # Remember the vectors of the last few documents for reuse.
            for r in pending_rows:
                recent.setdefault(r[0]["text_key"], []).append((r[2], r[3], r[5]))
            while len(recent) > 16:
                recent.pop(next(iter(recent)))
            pending_rows = []
            docs_in_batch = 0

        for row in self.pending_documents():
            meta = dict(row._mapping)
            display = meta.pop("text_display")
            citation = meta.pop("citation")
            # Key on the text alone: the citation prefix differs per ayah but
            # the commentary is the same, so vectors can still be reused.
            meta["text_key"] = f"{meta['language_code']}:{hash(display)}"
            known = recent.get(meta["text_key"])
            if known is None:
                # Same text may be queued but not flushed yet.
                known = [(r[2], r[3], r[5]) for r in pending_rows if r[0]["text_key"] == meta["text_key"]] or None
            for i, (s, e) in enumerate(chunk_spans(display)):
                passage = clean_for_embedding(display[s:e])
                if not passage:
                    continue
                vec = None
                if known is not None:
                    match = [v for a, b, v in known if a == s and b == e and v is not None]
                    if match:
                        vec = match[0]
                        reused += 1
                # Tafsir passages carry their ayah so a fragment keeps its context.
                if meta["doc_type"] == "tafsir_entry":
                    passage = f"{citation}. {passage}"
                pending_rows.append((meta, i, s, e, passage, vec))
            docs_in_batch += 1
            processed += 1
            if docs_in_batch >= COMMIT_EVERY_DOCS or len(pending_rows) >= EMBED_BATCH * 8:
                flush()
                rate = processed / max(time.time() - started, 1e-6)
                remaining = (total_docs - done_docs - processed) / max(rate, 1e-6)
                log(
                    f"{done_docs + processed}/{total_docs} docs  "
                    f"{rate * 60:.0f} docs/min  ETA {remaining / 60:.0f} min  "
                    f"reused {reused} vectors  last: {meta['doc_type']}/{meta['language_code']}"
                )
        flush()

        chunk_count = self.session.scalar(select(func.count()).select_from(SearchChunk))
        docs_indexed = self.session.scalar(
            select(func.count(func.distinct(SearchChunk.document_id)))
        )
        settings = embeddings.get_settings()
        model_name = f"{settings.EMBEDDING_MODEL} [{settings.EMBEDDING_MODEL_DIR}]"
        self.session.execute(text("DELETE FROM search.embedding_state"))
        self.session.add(
            EmbeddingState(
                id=1,
                built_at=datetime.now(timezone.utc),
                model_name=model_name,
                model_dim=EMBEDDING_DIM,
                model_files=embeddings.model_file_checksums(settings.EMBEDDING_MODEL_DIR),
                chunker_version=CHUNKER_VERSION,
                chunk_count=chunk_count,
                documents_indexed=docs_indexed,
            )
        )
        self.session.commit()
        return {"documents_indexed": docs_indexed, "chunks": chunk_count, "model": model_name}


def _main() -> None:
    from app.db.session import SessionLocal

    def log(msg: str) -> None:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

    with SessionLocal() as session:
        result = EmbeddingIndexer(session).build(log)
        log(f"done: {result}")


if __name__ == "__main__":
    sys.exit(_main())
