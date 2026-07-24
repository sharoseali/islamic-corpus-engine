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

from datetime import datetime, timezone

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.hadith import Hadith, HadithCollection, HadithText
from app.models.quran import TranslationResource, Verse, VerseTranslation
from app.models.search import SearchDocument, SearchIndexState
from app.models.tafsir import TafsirEdition, TafsirEntry
from app.services.text_normalize import normalize

INDEXER_VERSION = "1.0.0"
BATCH = 2000


class SearchIndexer:
    def __init__(self, session: Session):
        self.session = session

    def rebuild(self) -> dict:
        conn = self.session.connection()
        conn.execute(text("TRUNCATE search.documents RESTART IDENTITY"))

        counts: dict[str, int] = {}
        counts["quran_verse"] = self._index(self._quran_verses())
        counts["quran_translation"] = self._index(self._quran_translations())
        counts["hadith_text"] = self._index(self._hadith_texts())
        counts["tafsir_entry"] = self._index(self._tafsir_entries())

        # Build the tsvector column by language (Arabic/Urdu: simple; English)
        conn.execute(
            text(
                "UPDATE search.documents SET tsv = to_tsvector('simple', "
                "text_normalized) WHERE language_code IN ('ar','ur')"
            )
        )
        conn.execute(
            text(
                "UPDATE search.documents SET tsv = to_tsvector('english', "
                "text_normalized) WHERE language_code = 'en'"
            )
        )

        total = sum(counts.values())
        self._write_state(total, counts)
        self.session.commit()
        return {"total_documents": total, "by_type": counts}

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
                "ref": {"verse_key": verse_key},
                "text_display": uthmani,
                "text_normalized": normalize(uthmani, "ar"),
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
                "ref": {"verse_key": verse_key, "resource": res_name},
                "text_display": body,
                "text_normalized": normalize(body, lang),
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
                "ref": {"collection": coll_key, "hadith_number": number},
                "text_display": body,
                "text_normalized": normalize(body, lang),
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
                "ref": {"verse_key": verse_key, "edition": ed_name},
                "text_display": body,
                "text_normalized": normalize(body, lang),
            }

    # -- helpers ----------------------------------------------------------

    def _index(self, rows) -> int:
        batch: list[dict] = []
        n = 0
        for row in rows:
            batch.append(row)
            if len(batch) >= BATCH:
                self.session.execute(SearchDocument.__table__.insert(), batch)
                n += len(batch)
                batch.clear()
        if batch:
            self.session.execute(SearchDocument.__table__.insert(), batch)
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
