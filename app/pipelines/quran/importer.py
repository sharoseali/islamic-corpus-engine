"""Quran importer: quran.com (Quran Foundation API) -> corpus -> PostgreSQL.

Imports, with full provenance:
  1. All 114 chapters (surahs)
  2. All verses with Uthmani text (paginated per chapter)
  3. Translation resource metadata for the selected editions
  4. Ayah-by-ayah translations for the selected editions

Text is stored exactly as served - including embedded footnote markers in
translations. Deterministic and idempotent: re-runs reuse archived bytes and
upsert identical rows.
"""

import json

from app.core.config import get_settings
from app.models.quran import Chapter, TranslationResource, Verse, VerseTranslation
from app.pipelines.common.importer import BaseImporter
from app.pipelines.quran.client import QuranFoundationClient

# quran.com translation editions to import (extendable):
#   20  = Saheeh International (English)   - quran.com default English
#   234 = Fatah Muhammad Jalandhari (Urdu) - quran.com default Urdu
TRANSLATION_IDS = (20, 234)

VERSES_PER_PAGE = 50
VERSE_FIELDS = "text_uthmani"
ARCHIVE_BASE = "quran/quran_foundation"


class QuranImporter(BaseImporter):
    source_key = "quran_foundation"
    source_name = "Quran Foundation API (quran.com)"
    source_base_url = "https://apis.quran.foundation"
    source_license = (
        "Content served under Quran Foundation Developer Terms of Service; "
        "text must not be altered."
    )
    source_attribution = "Quran.com / Quran.Foundation"
    importer_name = "quran.core"
    importer_version = "1.0.0"

    def __init__(self, session, corpus_root="corpus"):
        super().__init__(session, corpus_root)
        self.client = QuranFoundationClient(get_settings())

    # ------------------------------------------------------------------ #

    def execute(self) -> dict:
        chapters = self._import_chapters()
        verse_ids_by_chapter, verses_total = self._import_verses(chapters)
        resources = self._import_translation_resources()
        translations_total = self._import_translations(verse_ids_by_chapter)
        return {
            "chapters": len(chapters),
            "verses": verses_total,
            "translation_resources": len(resources),
            "verse_translations": translations_total,
        }

    # ------------------------------------------------------------------ #

    def _import_chapters(self) -> list[dict]:
        response = self.client.get("/chapters")
        artifact = self.archive_bytes(
            f"{ARCHIVE_BASE}/chapters/chapters.json",
            response.content,
            endpoint="/chapters",
            http_status=response.status_code,
        )
        chapters = response.json()["chapters"]
        if len(chapters) != 114:
            raise ValueError(f"Expected 114 chapters, source returned {len(chapters)}")

        for ch in chapters:
            translated = ch.get("translated_name") or {}
            self.session.merge(
                Chapter(
                    id=ch["id"],
                    name_arabic=ch["name_arabic"],
                    name_simple=ch["name_simple"],
                    name_complex=ch["name_complex"],
                    translated_name=translated.get("name"),
                    revelation_place=ch["revelation_place"],
                    revelation_order=ch["revelation_order"],
                    verses_count=ch["verses_count"],
                    bismillah_pre=ch["bismillah_pre"],
                    raw_artifact_id=artifact.id,
                )
            )
        self.session.flush()
        return chapters

    def _import_verses(self, chapters: list[dict]) -> tuple[dict[int, list[int]], int]:
        verse_ids_by_chapter: dict[int, list[int]] = {}
        total = 0
        for ch in chapters:
            chapter_id = ch["id"]
            verse_ids: list[int] = []
            page = 1
            while page is not None:
                params = {
                    "fields": VERSE_FIELDS,
                    "per_page": VERSES_PER_PAGE,
                    "page": page,
                }
                response = self.client.get(
                    f"/verses/by_chapter/{chapter_id}", params=params
                )
                artifact = self.archive_bytes(
                    f"{ARCHIVE_BASE}/verses/chapter_{chapter_id:03d}_page_{page:03d}.json",
                    response.content,
                    endpoint=f"/verses/by_chapter/{chapter_id}",
                    request_params=params,
                    http_status=response.status_code,
                )
                payload = response.json()
                for v in payload["verses"]:
                    self.session.merge(
                        Verse(
                            id=v["id"],
                            chapter_id=chapter_id,
                            verse_number=v["verse_number"],
                            verse_key=v["verse_key"],
                            text_uthmani=v["text_uthmani"],
                            juz_number=v["juz_number"],
                            hizb_number=v.get("hizb_number"),
                            rub_el_hizb_number=v.get("rub_el_hizb_number"),
                            ruku_number=v.get("ruku_number"),
                            manzil_number=v.get("manzil_number"),
                            sajdah_number=v.get("sajdah_number"),
                            page_number=v.get("page_number"),
                            raw_artifact_id=artifact.id,
                        )
                    )
                    verse_ids.append(v["id"])
                    total += 1
                page = payload["pagination"]["next_page"]

            if len(verse_ids) != ch["verses_count"]:
                raise ValueError(
                    f"Chapter {chapter_id}: imported {len(verse_ids)} verses, "
                    f"source metadata says {ch['verses_count']}"
                )
            verse_ids_by_chapter[chapter_id] = verse_ids
            self.session.flush()
        return verse_ids_by_chapter, total

    def _import_translation_resources(self) -> list[int]:
        response = self.client.get("/resources/translations")
        artifact = self.archive_bytes(
            f"{ARCHIVE_BASE}/resources/translations.json",
            response.content,
            endpoint="/resources/translations",
            http_status=response.status_code,
        )
        by_id = {t["id"]: t for t in response.json()["translations"]}
        imported = []
        for resource_id in TRANSLATION_IDS:
            meta = by_id.get(resource_id)
            if meta is None:
                raise ValueError(f"Translation resource {resource_id} not offered by source")
            self.session.merge(
                TranslationResource(
                    id=resource_id,
                    language_code={"english": "en", "urdu": "ur"}.get(
                        meta["language_name"], meta["language_name"][:8]
                    ),
                    name=meta["name"],
                    author_name=meta.get("author_name"),
                    slug=meta.get("slug"),
                    source_id=self.run.source_id,
                )
            )
            imported.append(resource_id)
        self.session.flush()
        return imported

    def _import_translations(self, verse_ids_by_chapter: dict[int, list[int]]) -> int:
        total = 0
        for resource_id in TRANSLATION_IDS:
            for chapter_id, verse_ids in verse_ids_by_chapter.items():
                params = {"chapter_number": chapter_id}
                response = self.client.get(
                    f"/quran/translations/{resource_id}", params=params
                )
                artifact = self.archive_bytes(
                    f"{ARCHIVE_BASE}/translations/{resource_id}/chapter_{chapter_id:03d}.json",
                    response.content,
                    endpoint=f"/quran/translations/{resource_id}",
                    request_params=params,
                    http_status=response.status_code,
                )
                items = response.json()["translations"]
                if len(items) != len(verse_ids):
                    raise ValueError(
                        f"Resource {resource_id}, chapter {chapter_id}: "
                        f"{len(items)} translations for {len(verse_ids)} verses"
                    )
                # The source returns translations in verse order for the chapter.
                for verse_id, item in zip(verse_ids, items):
                    existing_id = self.session.execute(
                        VerseTranslation.__table__.select()
                        .with_only_columns(VerseTranslation.id)
                        .where(
                            VerseTranslation.verse_id == verse_id,
                            VerseTranslation.resource_id == resource_id,
                        )
                    ).scalar()
                    self.session.merge(
                        VerseTranslation(
                            id=existing_id,
                            verse_id=verse_id,
                            resource_id=resource_id,
                            text=item["text"],
                            raw_artifact_id=artifact.id,
                        )
                    )
                    total += 1
                self.session.flush()
        return total


def _main() -> None:
    from app.db.session import SessionLocal

    with SessionLocal() as session:
        importer = QuranImporter(session)
        run = importer.run_import()
        print(f"Import run {run.id}: {run.status}")
        print(json.dumps(run.stats, indent=2))


if __name__ == "__main__":
    _main()
