"""Tafsir importer: Tafsir Ibn Kathir (ar/ur/en) from quran.com -> corpus -> DB.

For each edition, walks all 114 chapters (paginated), archives every raw
response, and stores per-ayah entries keyed to canonical quran.verses rows.
Empty entries (ayat whose commentary is grouped under a neighbouring ayah)
are skipped and counted honestly in the run stats.
"""

import json

from sqlalchemy import select

from app.core.config import get_settings
from app.models.quran import Verse
from app.models.tafsir import TafsirEdition, TafsirEntry, TafsirWork
from app.pipelines.common.importer import BaseImporter
from app.pipelines.quran.client import QuranFoundationClient

# quran.com tafsir resource ids for Tafsir Ibn Kathir
EDITIONS = (
    (14, "ar", "Tafsir Ibn Kathir (Arabic)"),
    (160, "ur", "Tafseer Ibn-e-Kaseer (Urdu)"),
    (169, "en", "Ibn Kathir (Abridged, English)"),
)

WORK_KEY = "ibn-kathir"
WORK_NAME = "Tafsir Ibn Kathir"
WORK_AUTHOR = "Hafiz Ibn Kathir"

PER_PAGE = 50
ARCHIVE_BASE = "tafsir/quran_foundation/ibn-kathir"


class TafsirIbnKathirImporter(BaseImporter):
    source_key = "quran_foundation"
    source_name = "Quran Foundation API (quran.com)"
    source_base_url = "https://apis.quran.foundation"
    source_attribution = "Quran.com / Quran.Foundation"
    importer_name = "tafsir.ibn_kathir"
    importer_version = "1.0.0"

    def __init__(self, session, corpus_root="corpus"):
        super().__init__(session, corpus_root)
        self.client = QuranFoundationClient(get_settings())

    def execute(self) -> dict:
        verse_ids = dict(
            self.session.execute(select(Verse.verse_key, Verse.id)).all()
        )
        if len(verse_ids) != 6236:
            raise RuntimeError(
                f"Canonical Quran incomplete ({len(verse_ids)} verses) - "
                "run the Quran importer first."
            )

        work = (
            self.session.query(TafsirWork).filter_by(key=WORK_KEY).one_or_none()
        )
        if work is None:
            work = TafsirWork(key=WORK_KEY, name=WORK_NAME, author_name=WORK_AUTHOR)
            self.session.add(work)
            self.session.flush()

        stats: dict = {"editions": {}}
        for resource_id, lang, name in EDITIONS:
            existing = self.session.get(TafsirEdition, resource_id)
            if existing is not None:
                raise RuntimeError(
                    f"Tafsir edition {resource_id} already imported - "
                    "re-imports must be an explicit, reviewed operation."
                )
            stats["editions"][f"{lang}:{resource_id}"] = self._import_edition(
                work, resource_id, lang, name, verse_ids
            )
        return stats

    def _import_edition(
        self, work, resource_id: int, lang: str, name: str, verse_ids: dict
    ) -> dict:
        edition = TafsirEdition(
            id=resource_id,
            work_id=work.id,
            language_code=lang,
            name=name,
            source_id=self.run.source_id,
        )
        self.session.add(edition)
        self.session.flush()

        inserted = empty = 0
        seen_keys: set[str] = set()
        for chapter_id in range(1, 115):
            page: int | None = 1
            while page is not None:
                params = {"per_page": PER_PAGE, "page": page}
                response = self.client.get(
                    f"/tafsirs/{resource_id}/by_chapter/{chapter_id}", params=params
                )
                artifact = self.archive_bytes(
                    f"{ARCHIVE_BASE}/{resource_id}/chapter_{chapter_id:03d}_page_{page:03d}.json",
                    response.content,
                    endpoint=f"/tafsirs/{resource_id}/by_chapter/{chapter_id}",
                    request_params=params,
                    http_status=response.status_code,
                )
                payload = response.json()
                for item in payload["tafsirs"]:
                    verse_key = item["verse_key"]
                    if verse_key in seen_keys:
                        raise ValueError(
                            f"Edition {resource_id}: duplicate verse_key {verse_key}"
                        )
                    seen_keys.add(verse_key)
                    text = (item.get("text") or "").strip()
                    if not text:
                        empty += 1
                        continue
                    self.session.add(
                        TafsirEntry(
                            edition_id=edition.id,
                            verse_id=verse_ids[verse_key],
                            source_entry_id=int(item["id"]),
                            text=item["text"],
                            raw_artifact_id=artifact.id,
                        )
                    )
                    inserted += 1
                page = payload["pagination"]["next_page"]
            self.session.flush()

        missing = 6236 - len(seen_keys)
        return {
            "entries_inserted": inserted,
            "empty_entries_skipped": empty,
            "verse_keys_covered": len(seen_keys),
            "verse_keys_missing": missing,
        }


def _main() -> None:
    from app.db.session import SessionLocal

    with SessionLocal() as session:
        importer = TafsirIbnKathirImporter(session)
        run = importer.run_import()
        print(f"Import run {run.id}: {run.status}")
        print(json.dumps(run.stats, indent=2))


if __name__ == "__main__":
    _main()
