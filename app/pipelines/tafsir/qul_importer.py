"""QUL Tafsir importer: complete Tafsir Ibn Kathir (ar/ur/en) -> corpus -> DB.

Source of record: Quranic Universal Library (QUL) by Tarteel AI
(https://qul.tarteel.ai). Retrieved via the public MIT-licensed mirror
spa5k/tafsir_api on jsDelivr, pinned to an exact commit for determinism;
QUL is recorded as the true origin in provenance.

Unlike the quran.com editions (whose Urdu covered only 2,101/6,236 ayat),
every QUL edition here covers all 6,236 ayat. On success this importer
supersedes the earlier quran.com tafsir editions so the corpus holds one
authoritative, complete, trilingual Ibn Kathir aligned per ayah.
"""

import json

from sqlalchemy import delete, select

from app.models.quran import Verse
from app.models.tafsir import TafsirEdition, TafsirEntry, TafsirWork
from app.pipelines.common.importer import BaseImporter

PINNED_COMMIT = "5bbe0895543219f9ec3fe4ee808acce701a7bb4a"
CDN_BASE = f"https://cdn.jsdelivr.net/gh/spa5k/tafsir_api@{PINNED_COMMIT}"

# QUL resource id, mirror slug, language, display name
EDITIONS = (
    (22, "ar-tafsir-ibn-kathir", "ar", "Tafsir Ibn Kathir (Arabic)"),
    (30, "tafseer-ibn-e-kaseer-urdu", "ur", "Tafseer Ibn-e-Kaseer (Urdu)"),
    (35, "en-tafisr-ibn-kathir", "en", "Tafsir Ibn Kathir (English)"),
)

# quran.com tafsir editions this import supersedes
SUPERSEDED_EDITION_IDS = (14, 160, 169)

WORK_KEY = "ibn-kathir"
ARCHIVE_BASE = "tafsir/qul/ibn-kathir"


class QulTafsirImporter(BaseImporter):
    source_key = "qul"
    source_name = "Quranic Universal Library (QUL) - Tarteel AI"
    source_base_url = "https://qul.tarteel.ai"
    source_license = "See QUL resource terms; distributed via spa5k/tafsir_api (MIT)."
    source_attribution = (
        "Tafsir Ibn Kathir from the Quranic Universal Library (qul.tarteel.ai), "
        f"retrieved via github.com/spa5k/tafsir_api at commit {PINNED_COMMIT}."
    )
    importer_name = "tafsir.ibn_kathir.qul"
    importer_version = "1.0.0"

    def __init__(self, session, corpus_root="corpus"):
        super().__init__(session, corpus_root)
        import httpx

        self._http = httpx.Client(timeout=120.0, follow_redirects=True)

    def execute(self) -> dict:
        verse_ids = dict(
            self.session.execute(select(Verse.verse_key, Verse.id)).all()
        )
        if len(verse_ids) != 6236:
            raise RuntimeError(
                f"Canonical Quran incomplete ({len(verse_ids)} verses)."
            )

        work = self.session.query(TafsirWork).filter_by(key=WORK_KEY).one_or_none()
        if work is None:
            work = TafsirWork(
                key=WORK_KEY, name="Tafsir Ibn Kathir", author_name="Hafiz Ibn Kathir"
            )
            self.session.add(work)
            self.session.flush()

        superseded = self._supersede_previous()

        stats: dict = {"superseded_quran_com_editions": superseded, "editions": {}}
        for resource_id, slug, lang, name in EDITIONS:
            stats["editions"][f"{lang}:{resource_id}"] = self._import_edition(
                work, resource_id, slug, lang, name, verse_ids
            )
        return stats

    def _supersede_previous(self) -> dict:
        """Remove the earlier, incomplete quran.com tafsir editions.

        Only derived tafsir rows are removed; their import runs and raw
        artifacts remain in `metadata` as an audit trail, and their archived
        files stay on disk (write-once).
        """
        counts = {}
        for edition_id in SUPERSEDED_EDITION_IDS:
            if self.session.get(TafsirEdition, edition_id) is None:
                continue
            n = self.session.execute(
                delete(TafsirEntry).where(TafsirEntry.edition_id == edition_id)
            ).rowcount
            self.session.execute(
                delete(TafsirEdition).where(TafsirEdition.id == edition_id)
            )
            counts[str(edition_id)] = n
        self.session.flush()
        return counts

    def _import_edition(self, work, resource_id, slug, lang, name, verse_ids) -> dict:
        edition = TafsirEdition(
            id=resource_id,
            work_id=work.id,
            language_code=lang,
            name=name,
            slug=slug,
            source_id=self.run.source_id,
        )
        self.session.add(edition)
        self.session.flush()

        inserted = 0
        seen: set[str] = set()
        for surah in range(1, 115):
            url = f"{CDN_BASE}/tafsir/{slug}/{surah}.json"
            response = self._http.get(url)
            response.raise_for_status()
            artifact = self.archive_bytes(
                f"{ARCHIVE_BASE}/{slug}/surah_{surah:03d}.json",
                response.content,
                endpoint=url,
                http_status=response.status_code,
            )
            for item in json.loads(response.content):
                verse_key = f"{item['surah']}:{item['ayah']}"
                if verse_key in seen:
                    raise ValueError(f"{slug}: duplicate verse_key {verse_key}")
                seen.add(verse_key)
                text = (item.get("text") or "").strip()
                if not text:
                    continue
                self.session.add(
                    TafsirEntry(
                        edition_id=edition.id,
                        verse_id=verse_ids[verse_key],
                        text=item["text"],
                        raw_artifact_id=artifact.id,
                    )
                )
                inserted += 1
            self.session.flush()

        missing = 6236 - len(seen)
        if missing:
            raise ValueError(f"{slug}: only {len(seen)}/6236 ayat covered")
        return {"entries_inserted": inserted, "verse_keys_covered": len(seen)}


def _main() -> None:
    from app.db.session import SessionLocal

    with SessionLocal() as session:
        importer = QulTafsirImporter(session)
        run = importer.run_import()
        print(f"Import run {run.id}: {run.status}")
        print(json.dumps(run.stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    _main()
