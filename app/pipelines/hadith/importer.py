"""Hadith importer (interim mirror): fawazahmed0/hadith-api -> corpus -> DB.

INTERIM SOURCE - clearly labeled as a mirror, pinned to an exact git commit
for determinism. When the official sunnah.com API key arrives, an official
importer will cross-check every record and fill canonical gaps; differences
are flagged, never silently merged.

Per collection, imports the Arabic, Urdu, and English editions:
  - validates that all three editions carry the same hadith numbers in the
    same order with the same book references (alignment proof);
  - archives each edition file byte-for-byte with SHA-256;
  - loads books (kutub), hadith entries, and per-language texts;
  - skips empty texts but counts them honestly in the run stats.
"""

import json

import httpx

from app.models.hadith import Hadith, HadithBook, HadithCollection, HadithText
from app.pipelines.common.importer import BaseImporter

# Pinned commit of https://github.com/fawazahmed0/hadith-api (branch "1")
PINNED_COMMIT = "df57907be35291c91ad6a6691180e22ca9920784"
CDN_BASE = f"https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@{PINNED_COMMIT}"

COLLECTIONS = ("bukhari", "muslim")
# language editions: (edition prefix, ISO language code) - Urdu before English
LANGUAGES = (("ara", "ar"), ("urd", "ur"), ("eng", "en"))

ARCHIVE_BASE = "hadith/fawazahmed0"
BATCH_SIZE = 1000


class HadithMirrorImporter(BaseImporter):
    source_key = "fawazahmed0_hadith_api"
    source_name = "fawazahmed0/hadith-api mirror (INTERIM, pending sunnah.com)"
    source_base_url = CDN_BASE
    source_license = "Unlicense (public domain dedication) per repository"
    source_attribution = (
        "Hadith data mirrored from github.com/fawazahmed0/hadith-api "
        f"at commit {PINNED_COMMIT}; texts originate from public hadith "
        "digitizations. Pending verification against sunnah.com official API."
    )
    importer_name = "hadith.mirror"
    importer_version = "1.0.0"

    def __init__(self, session, corpus_root="corpus"):
        super().__init__(session, corpus_root)
        self._http = httpx.Client(timeout=120.0, follow_redirects=True)

    # ------------------------------------------------------------------ #

    def execute(self) -> dict:
        stats: dict = {"pinned_commit": PINNED_COMMIT, "collections": {}}
        for key in COLLECTIONS:
            existing = (
                self.session.query(HadithCollection).filter_by(key=key).one_or_none()
            )
            if existing is not None:
                raise RuntimeError(
                    f"Collection '{key}' already imported (id={existing.id}). "
                    "Re-imports must be an explicit, reviewed operation."
                )
            stats["collections"][key] = self._import_collection(key)
        return stats

    # ------------------------------------------------------------------ #

    def _fetch_edition(self, key: str, prefix: str):
        edition = f"{prefix}-{key}"
        url = f"{CDN_BASE}/editions/{edition}.min.json"
        response = self._http.get(url)
        response.raise_for_status()
        artifact = self.archive_bytes(
            f"{ARCHIVE_BASE}/{edition}.min.json",
            response.content,
            endpoint=url,
            http_status=response.status_code,
        )
        return json.loads(response.content), artifact

    @staticmethod
    def _alignment_key(hadith: dict):
        ref = hadith.get("reference") or {}
        return (
            str(hadith.get("hadithnumber")),
            ref.get("book"),
            ref.get("hadith"),
        )

    def _import_collection(self, key: str) -> dict:
        editions: dict[str, tuple[list, object, dict]] = {}
        prefaces_skipped: dict[str, int] = {}
        for prefix, lang in LANGUAGES:
            payload, artifact = self._fetch_edition(key, prefix)
            # Entries numbered 0 are prefaces/front-matter, not hadith
            # (e.g. urd-muslim carries the translator's preface as entry 0).
            hadiths = [
                h for h in payload["hadiths"] if str(h.get("hadithnumber")) != "0"
            ]
            prefaces_skipped[lang] = len(payload["hadiths"]) - len(hadiths)
            editions[lang] = (hadiths, artifact, payload["metadata"])

        # --- alignment validation across the three editions ---------------
        ar_hadiths, ar_artifact, ar_meta = editions["ar"]
        ar_keys = [self._alignment_key(h) for h in ar_hadiths]
        for lang in ("ur", "en"):
            other_keys = [self._alignment_key(h) for h in editions[lang][0]]
            if other_keys != ar_keys:
                mismatches = sum(1 for a, b in zip(ar_keys, other_keys) if a != b)
                raise ValueError(
                    f"{key}: '{lang}' edition is NOT aligned with Arabic "
                    f"(length {len(other_keys)} vs {len(ar_keys)}, "
                    f"{mismatches} mismatched entries) - refusing to import."
                )

        collection = HadithCollection(
            key=key,
            name=ar_meta.get("name") or key,
            raw_artifact_id=ar_artifact.id,
        )
        self.session.add(collection)
        self.session.flush()

        # --- books (kutub): union of section numbers, names per language --
        books: dict[int, HadithBook] = {}
        names_by_lang = {
            lang: editions[lang][2].get("sections", {}) for lang in ("ar", "ur", "en")
        }
        section_numbers = sorted(
            {int(n) for sections in names_by_lang.values() for n in sections}
        )
        for number in section_numbers:
            book = HadithBook(
                collection_id=collection.id,
                number=number,
                name=names_by_lang["en"].get(str(number)) or None,
                name_arabic=names_by_lang["ar"].get(str(number)) or None,
                name_urdu=names_by_lang["ur"].get(str(number)) or None,
                raw_artifact_id=ar_artifact.id,
            )
            self.session.add(book)
            books[number] = book
        self.session.flush()

        # --- hadith entries + texts ---------------------------------------
        empty_counts = {"ar": 0, "ur": 0, "en": 0}
        inserted_texts = 0
        for position, ar_hadith in enumerate(ar_hadiths, start=1):
            ref = ar_hadith.get("reference") or {}
            book = books.get(ref.get("book"))
            grades = ar_hadith.get("grades") or None
            hadith = Hadith(
                collection_id=collection.id,
                book_id=book.id if book else None,
                position=position,
                hadith_number=str(ar_hadith.get("hadithnumber")),
                arabic_number=(
                    str(ar_hadith["arabicnumber"])
                    if "arabicnumber" in ar_hadith
                    else None
                ),
                hadith_in_book=ref.get("hadith"),
                grades=grades,
            )
            self.session.add(hadith)
            if position % BATCH_SIZE == 0:
                self.session.flush()

            for lang in ("ar", "ur", "en"):
                entry = editions[lang][0][position - 1]
                text = (entry.get("text") or "").strip()
                if not text:
                    empty_counts[lang] += 1
                    continue
                self.session.add(
                    HadithText(
                        hadith=hadith,
                        language_code=lang,
                        text=entry["text"],
                        raw_artifact_id=editions[lang][1].id,
                    )
                )
                inserted_texts += 1
        self.session.flush()

        return {
            "entries": len(ar_hadiths),
            "books": len(section_numbers),
            "texts_inserted": inserted_texts,
            "empty_texts_skipped": empty_counts,
            "preface_entries_skipped": prefaces_skipped,
        }


def _main() -> None:
    from app.db.session import SessionLocal

    with SessionLocal() as session:
        importer = HadithMirrorImporter(session)
        run = importer.run_import()
        print(f"Import run {run.id}: {run.status}")
        print(json.dumps(run.stats, indent=2))


if __name__ == "__main__":
    _main()
