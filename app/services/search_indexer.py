"""Search indexer.

Rebuilds the `search.documents` table from the canonical schemas. This is
pure derived data: it reads quran/hadith/tafsir, never writes to them, and
can be dropped and rebuilt at any time without loss. Each document keeps a
pointer back to its canonical row, and the build records a fingerprint so a
stale index is detectable.

Text search config: PostgreSQL ships no Arabic/Urdu stemmers, so those use
the 'simple' config over already-normalized text (diacritics stripped,
letter forms unified); English uses the 'english' config. Fuzzy matching is
served by the trigram index on text_normalized.
"""

import json
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.hadith import Hadith, HadithCollection, HadithText
from app.models.quran import TranslationResource, Verse, VerseTranslation
from app.models.search import SearchDocument, SearchIndexState
from app.models.tafsir import TafsirEdition, TafsirEntry
from app.services.text_normalize import normalize, search_tokens, ts_config

INDEXER_VERSION = "1.4.0"  # 1.2: in-place upsert (stable ids), Turkish; 1.3: vocabulary; 1.4: Uthmani spelling rules
BATCH = 2000


class SearchIndexer:
    def __init__(self, session: Session):
        self.session = session

    def rebuild(self) -> dict:
        """Rebuild search.documents in place.

        Rows are matched on their identity (doc_type, source_row_id,
        language_code) and updated, so document ids stay stable and the
        embeddings in search.chunks survive a keyword re-index. Chunks are
        dropped only for documents whose text changed, and documents that
        no longer exist in the canonical schemas are removed.
        """
        conn = self.session.connection()
        conn.execute(
            text(
                "CREATE TEMP TABLE new_docs "
                "(LIKE search.documents INCLUDING DEFAULTS EXCLUDING INDEXES) "
                "ON COMMIT DROP"
            )
        )
        conn.execute(text("ALTER TABLE new_docs DROP COLUMN id"))

        counts: dict[str, int] = {}
        counts["quran_verse"] = self._index(self._quran_verses())
        counts["quran_translation"] = self._index(self._quran_translations())
        counts["hadith_text"] = self._index(self._hadith_texts())
        counts["tafsir_entry"] = self._index(self._tafsir_entries())

        identity = (
            "d.doc_type = n.doc_type AND d.source_row_id = n.source_row_id "
            "AND d.language_code = n.language_code"
        )
        # Embeddings of changed texts are stale: drop them for re-embedding.
        stale = conn.execute(
            text(
                f"""
                DELETE FROM search.chunks c
                USING search.documents d, new_docs n
                WHERE c.document_id = d.id AND {identity}
                  AND d.text_display IS DISTINCT FROM n.text_display
                """
            )
        ).rowcount
        conn.execute(
            text(
                """
                INSERT INTO search.documents
                    (doc_type, language_code, collection_key, source_row_id,
                     citation, ref, text_display, text_normalized, tsv)
                SELECT doc_type, language_code, collection_key, source_row_id,
                       citation, ref, text_display, text_normalized, tsv
                FROM new_docs
                ON CONFLICT (doc_type, source_row_id, language_code) DO UPDATE SET
                    collection_key = EXCLUDED.collection_key,
                    citation = EXCLUDED.citation,
                    ref = EXCLUDED.ref,
                    text_display = EXCLUDED.text_display,
                    text_normalized = EXCLUDED.text_normalized,
                    tsv = EXCLUDED.tsv
                """
            )
        )
        removed = conn.execute(
            text(
                f"""
                DELETE FROM search.documents d
                WHERE NOT EXISTS (SELECT 1 FROM new_docs n WHERE {identity})
                """
            )
        ).rowcount

        total = sum(counts.values())
        self._write_state(total, counts)
        self.session.commit()
        return {
            "total_documents": total,
            "by_type": counts,
            "removed_documents": removed,
            "stale_chunks_dropped": stale,
            "vocabulary_lexemes": self.refresh_vocabulary(),
        }

    def refresh_vocabulary(self) -> int:
        """Rebuild search.vocabulary from the tsvectors: every lexeme per
        language with the number of documents it occurs in."""
        self.session.execute(text("DELETE FROM search.vocabulary"))
        total = 0
        for lang in self.session.scalars(
            text("SELECT DISTINCT language_code FROM search.documents ORDER BY 1")
        ):
            stats = f"SELECT tsv FROM search.documents WHERE language_code = '{lang}'"
            result = self.session.execute(
                text(
                    """
                    INSERT INTO search.vocabulary (language_code, lexeme, ndoc)
                    SELECT :lang, word, ndoc FROM ts_stat(:stats)
                    WHERE length(word) >= 3
                    """
                ),
                {"lang": lang, "stats": stats},
            )
            total += result.rowcount
        self.session.commit()
        return total

    # -- row generators ---------------------------------------------------

    def _quran_verses(self):
        rows = self.session.execute(
            select(Verse.id, Verse.verse_key, Verse.text_uthmani)
        )
        for verse_id, verse_key, uthmani in rows:
            yield {
                "doc_type": "quran_verse",
                "language_code": "ar",
                "collection_key": "quran",
                "source_row_id": verse_id,
                "citation": f"Quran {verse_key}",
                "ref": json.dumps({"verse_key": verse_key}),
                "text_display": uthmani,
                "text_normalized": normalize(uthmani, "ar"),
                "tokens": search_tokens(uthmani, "ar"),
                "ts_config": ts_config("ar"),
            }

    def _quran_translations(self):
        rows = self.session.execute(
            select(
                VerseTranslation.id,
                Verse.verse_key,
                TranslationResource.language_code,
                TranslationResource.name,
                VerseTranslation.text,
            )
            .join(Verse, Verse.id == VerseTranslation.verse_id)
            .join(
                TranslationResource,
                TranslationResource.id == VerseTranslation.resource_id,
            )
        )
        for row_id, verse_key, lang, res_name, body in rows:
            yield {
                "doc_type": "quran_translation",
                "language_code": lang,
                "collection_key": "quran",
                "source_row_id": row_id,
                "citation": f"Quran {verse_key} ({res_name})",
                "ref": json.dumps({"verse_key": verse_key, "resource": res_name}),
                "text_display": body,
                "text_normalized": normalize(body, lang),
                "tokens": search_tokens(body, lang),
                "ts_config": ts_config(lang),
            }

    def _hadith_texts(self):
        rows = self.session.execute(
            select(
                HadithText.id,
                HadithText.language_code,
                HadithText.text,
                Hadith.hadith_number,
                HadithCollection.key,
                HadithCollection.name,
            )
            .join(Hadith, Hadith.id == HadithText.hadith_id)
            .join(HadithCollection, HadithCollection.id == Hadith.collection_id)
        )
        for row_id, lang, body, number, coll_key, coll_name in rows:
            yield {
                "doc_type": "hadith_text",
                "language_code": lang,
                "collection_key": coll_key,
                "source_row_id": row_id,
                "citation": f"{coll_name} {number}",
                "ref": json.dumps({"collection": coll_key, "hadith_number": number}),
                "text_display": body,
                "text_normalized": normalize(body, lang),
                "tokens": search_tokens(body, lang),
                "ts_config": ts_config(lang),
            }

    def _tafsir_entries(self):
        rows = self.session.execute(
            select(
                TafsirEntry.id,
                TafsirEdition.language_code,
                TafsirEdition.name,
                TafsirEntry.text,
                Verse.verse_key,
            )
            .join(TafsirEdition, TafsirEdition.id == TafsirEntry.edition_id)
            .join(Verse, Verse.id == TafsirEntry.verse_id)
        )
        for row_id, lang, ed_name, body, verse_key in rows:
            yield {
                "doc_type": "tafsir_entry",
                "language_code": lang,
                "collection_key": "ibn-kathir",
                "source_row_id": row_id,
                "citation": f"Tafsir Ibn Kathir {verse_key}",
                "ref": json.dumps({"verse_key": verse_key, "edition": ed_name}),
                "text_display": body,
                "text_normalized": normalize(body, lang),
                "tokens": search_tokens(body, lang),
                "ts_config": ts_config(lang),
            }

    # -- helpers ----------------------------------------------------------

    def _index(self, rows) -> int:
        # Rows go to the per-run staging table; the tsvector is built in the
        # database from the Python-side token expansion (word + spelling
        # variants + stem) with the per-language config.
        stmt = text(
            """
            INSERT INTO new_docs
                (doc_type, language_code, collection_key, source_row_id,
                 citation, ref, text_display, text_normalized, tsv)
            VALUES (:doc_type, :language_code, :collection_key, :source_row_id,
                    :citation, CAST(:ref AS jsonb), :text_display, :text_normalized,
                    to_tsvector(CAST(:ts_config AS regconfig), :tokens))
            """
        )
        batch: list[dict] = []
        n = 0
        for row in rows:
            batch.append(row)
            if len(batch) >= BATCH:
                self.session.execute(stmt, batch)
                n += len(batch)
                batch.clear()
        if batch:
            self.session.execute(stmt, batch)
            n += len(batch)
        return n

    def _write_state(self, total: int, counts: dict) -> None:
        self.session.execute(text("DELETE FROM search.index_state"))
        self.session.add(
            SearchIndexState(
                id=1,
                built_at=datetime.now(timezone.utc),
                indexer_version=INDEXER_VERSION,
                document_count=total,
                corpus_fingerprint=counts,
            )
        )


def _main() -> None:
    from app.db.session import SessionLocal

    with SessionLocal() as session:
        result = SearchIndexer(session).rebuild()
        import json

        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    _main()
