"""Enrich hadith book (kitab) Arabic names.

Our interim hadith source (fawazahmed0) carries only English section names.
Arabic kitab titles are sourced from AhmedBaset/hadith-json (same sunnah.com
lineage), matched by book number and cross-checked on the English name.
Collection Arabic names are set to their well-known titles.

This only fills the display-name column; it does not touch hadith text or
provenance. When the official sunnah.com API import lands, it supersedes this.
"""

import json
import urllib.request

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.hadith import HadithBook, HadithCollection

SOURCES = {
    "bukhari": "https://raw.githubusercontent.com/AhmedBaset/hadith-json/main/db/by_book/the_9_books/bukhari.json",
    "muslim": "https://raw.githubusercontent.com/AhmedBaset/hadith-json/main/db/by_book/the_9_books/muslim.json",
}
COLLECTION_ARABIC = {"bukhari": "صحيح البخاري", "muslim": "صحيح مسلم"}


def _fetch(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.loads(r.read())


def main() -> None:
    with SessionLocal() as s:
        for key, url in SOURCES.items():
            coll = s.scalar(select(HadithCollection).where(HadithCollection.key == key))
            if coll is None:
                print(f"skip {key}: not imported")
                continue
            coll.name_arabic = COLLECTION_ARABIC[key]

            data = _fetch(url)
            by_id = {int(c["id"]): c["arabic"] for c in data["chapters"]}

            books = s.scalars(
                select(HadithBook).where(HadithBook.collection_id == coll.id)
            ).all()
            updated = 0
            for b in books:
                arabic = by_id.get(b.number)
                if arabic:
                    b.name_arabic = arabic
                    updated += 1
            print(f"{key}: set collection Arabic name + {updated} book Arabic names")
        s.commit()


if __name__ == "__main__":
    main()
