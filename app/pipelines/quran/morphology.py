"""Quran morphology importer: QUL word root / lemma / stem files -> DB.

The source files are the SQLite archives downloaded from qul.tarteel.ai
(Quranic Arabic Corpus morphology, "Word by word" resources) into
corpus/original/qul/morphology/. Each file addresses words as
surah:ayah:position. Words are aligned to quran.verses.text_uthmani by
position: pause marks and similar signs in the Uthmani text are not words
and are skipped; 37:130 is written as two tokens by quran.com and counted
as one word by the corpus. Any other disagreement between the two word
counts stops the import.

Run:  qlib/bin/python -m app.pipelines.quran.morphology
"""

import io
import json
import re
import sqlite3
import tempfile
import zipfile
from pathlib import Path

from sqlalchemy import delete, select

from app.models.quran import Lemma, Root, Stem, Verse, Word
from app.pipelines.common.importer import BaseImporter
from app.services.text_normalize import normalize_arabic

ARCHIVE_BASE = "qul/morphology"
FILES = {
    "root": "word-root.db.zip",
    "lemma": "word-lemma.db.zip",
    "stem": "word-stem.db.zip",
}
RESOURCE_PAGE = "https://qul.tarteel.ai/resources/morphology"
WORDS_IN_QURAN = 77429

_ARABIC_LETTER = re.compile(r"[\u0621-\u064A\u0671-\u06D3\u06FA-\u06FF]")
# verse_key -> (first, last) 1-based token positions that form one word
_JOINED_TOKENS = {"37:130": (3, 4)}


def verse_words(verse_key: str, text_uthmani: str) -> list[str]:
    """The words of a verse in corpus numbering (signs dropped, 37:130 joined)."""
    words = [w for w in text_uthmani.split() if _ARABIC_LETTER.search(w)]
    joined = _JOINED_TOKENS.get(verse_key)
    if joined:
        first, last = joined
        words[first - 1 : last] = [" ".join(words[first - 1 : last])]
    return words


class QuranMorphologyImporter(BaseImporter):
    source_key = "qul"
    source_name = "Quranic Universal Library (QUL), Tarteel AI"
    source_base_url = "https://qul.tarteel.ai"
    source_attribution = "Quranic Arabic Corpus morphology, distributed by QUL"
    importer_name = "quran.morphology"
    importer_version = "1.0.0"

    def __init__(self, session, corpus_root="corpus", files_dir: str | Path | None = None):
        super().__init__(session, corpus_root)
        self.files_dir = Path(files_dir) if files_dir else self.archive.original / ARCHIVE_BASE

    def execute(self) -> dict:
        verses = self.session.execute(
            select(Verse.id, Verse.verse_key, Verse.text_uthmani)
        ).all()
        if len(verses) != 6236:
            raise RuntimeError(
                f"Canonical Quran incomplete ({len(verses)} verses) - run the Quran importer first."
            )

        artifacts = {}
        data = {}
        for kind, name in FILES.items():
            content = (self.files_dir / name).read_bytes()
            artifacts[kind] = self.archive_bytes(
                f"{ARCHIVE_BASE}/{name}",
                content,
                endpoint=RESOURCE_PAGE,
                request_params={"resource": f"Word {kind}", "file": name, "format": "sqlite"},
            )
            data[kind] = self._read_sqlite(content, kind)

        # Replace earlier rows: this data has exactly one source.
        self.session.execute(delete(Word))
        for model in (Root, Lemma, Stem):
            self.session.execute(delete(model))

        roots = [
            {
                "id": rid,
                "letters": letters.replace(" ", ""),
                "letters_spaced": " ".join(letters.split()),
                "buckwalter": bw,
                "words_count": wc,
                "uniq_words_count": uwc,
                "raw_artifact_id": artifacts["root"].id,
            }
            for rid, letters, bw, wc, uwc in data["root"]["entries"]
        ]
        lemmas = [
            {"id": i, "text": t, "text_clean": tc, "raw_artifact_id": artifacts["lemma"].id}
            for i, t, tc in data["lemma"]["entries"]
        ]
        stems = [
            {"id": i, "text": t, "text_clean": tc, "raw_artifact_id": artifacts["stem"].id}
            for i, t, tc in data["stem"]["entries"]
        ]
        self.session.execute(Root.__table__.insert(), roots)
        self.session.execute(Lemma.__table__.insert(), lemmas)
        self.session.execute(Stem.__table__.insert(), stems)

        links = {kind: dict(data[kind]["words"]) for kind in FILES}  # location -> id
        # The stem file covers every word, so it defines the word count the
        # text must agree with. The other files may carry stray entries at
        # positions that do not exist (the published lemma file has three);
        # those are skipped and counted, never guessed.
        max_pos: dict[str, int] = {}
        for loc in links["stem"]:
            s, a, w = loc.split(":")
            key = f"{s}:{a}"
            max_pos[key] = max(max_pos.get(key, 0), int(w))

        rows = []
        mismatches = []
        counts = {"root": 0, "lemma": 0, "stem": 0}
        out_of_range = {"root": [], "lemma": [], "stem": []}
        for verse_id, verse_key, text in verses:
            words = verse_words(verse_key, text)
            if max_pos.get(verse_key, 0) != len(words):
                mismatches.append((verse_key, len(words), max_pos.get(verse_key, 0)))
                continue
            for kind in FILES:
                for pos in range(len(words) + 1, len(words) + 4):
                    if f"{verse_key}:{pos}" in links[kind]:
                        out_of_range[kind].append(f"{verse_key}:{pos}")
            for pos, word in enumerate(words, start=1):
                loc = f"{verse_key}:{pos}"
                ids = {kind: links[kind].get(loc) for kind in FILES}
                for kind, value in ids.items():
                    counts[kind] += value is not None
                rows.append(
                    {
                        "verse_id": verse_id,
                        "position": pos,
                        "text_uthmani": word,
                        "text_normalized": normalize_arabic(word),
                        "root_id": ids["root"],
                        "lemma_id": ids["lemma"],
                        "stem_id": ids["stem"],
                        "raw_artifact_id": artifacts["stem"].id,
                    }
                )
        if mismatches:
            raise RuntimeError(
                f"word positions disagree with the corpus in {len(mismatches)} verses, "
                f"e.g. {mismatches[:5]} (verse_key, our words, corpus words)"
            )
        for start in range(0, len(rows), 5000):
            self.session.execute(Word.__table__.insert(), rows[start : start + 5000])

        self.run.notes = (
            "Quranic Arabic Corpus morphology as distributed by QUL (Word root / "
            "lemma / stem, SQLite). Licence: as stated on the QUL resource page."
        )
        return {
            "roots": len(roots),
            "lemmas": len(lemmas),
            "stems": len(stems),
            "words": len(rows),
            "words_in_quran_reference": WORDS_IN_QURAN,
            "words_with_root": counts["root"],
            "words_with_lemma": counts["lemma"],
            "words_with_stem": counts["stem"],
            "verses": len(verses),
            "source_entries_at_nonexistent_positions": {
                kind: locs for kind, locs in out_of_range.items() if locs
            },
        }

    @staticmethod
    def _read_sqlite(content: bytes, kind: str) -> dict:
        """Entries and word links of one QUL archive (a zip holding one .db)."""
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            members = [m for m in zf.namelist() if m.endswith(".db")]
            if len(members) != 1:
                raise RuntimeError(f"{kind}: expected one .db in the archive, found {members}")
            db_bytes = zf.read(members[0])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "m.db"
            path.write_bytes(db_bytes)
            con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            try:
                if kind == "root":
                    entries = con.execute(
                        "SELECT id, arabic_trilateral, english_trilateral, words_count, "
                        "uniq_words_count FROM roots"
                    ).fetchall()
                    words = con.execute("SELECT word_location, root_id FROM root_words").fetchall()
                else:
                    entries = con.execute(f"SELECT id, text, text_clean FROM {kind}s").fetchall()
                    words = con.execute(
                        f"SELECT word_location, {kind}_id FROM {kind}_words"
                    ).fetchall()
            finally:
                con.close()
        return {"entries": entries, "words": words}


def _main() -> None:
    from app.db.session import SessionLocal

    with SessionLocal() as session:
        run = QuranMorphologyImporter(session).run_import()
        print(json.dumps({"run_id": run.id, "status": run.status, "stats": run.stats}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _main()
