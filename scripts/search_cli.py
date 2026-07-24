"""Command-line search over the Islamic Knowledge Core corpus.

Usage:
    python -m scripts.search_cli "الرحمن الرحيم" --lang ar
    python -m scripts.search_cli "forgiveness" --lang en --types tafsir_entry
    python -m scripts.search_cli "نماز" --lang ur --collections bukhari,muslim
"""

import argparse
import re

from app.db.session import SessionLocal
from app.services.search import SearchService

_TAG = re.compile(r"<[^>]+>")


def _snippet(text: str, width: int = 160) -> str:
    clean = " ".join(_TAG.sub(" ", text).split())
    return clean if len(clean) <= width else clean[:width] + "…"


def main() -> None:
    parser = argparse.ArgumentParser(description="Search the corpus.")
    parser.add_argument("query")
    parser.add_argument("--lang", required=True, choices=["ar", "ur", "en"])
    parser.add_argument("--types", help="comma-separated doc_types")
    parser.add_argument("--collections", help="comma-separated collection keys")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    doc_types = args.types.split(",") if args.types else None
    collections = args.collections.split(",") if args.collections else None

    with SessionLocal() as session:
        hits = SearchService(session).search(
            args.query,
            args.lang,
            doc_types=doc_types,
            collection_keys=collections,
            limit=args.limit,
        )

    if not hits:
        print("No results.")
        return

    print(f'\n{len(hits)} result(s) for "{args.query}" [{args.lang}]\n')
    for i, h in enumerate(hits, 1):
        tag = "≈" if h.match == "fuzzy" else "•"
        print(f"{i:>2}. {tag} [{h.doc_type}] {h.citation}  (score {h.score:.3f})")
        print(f"      {_snippet(h.text_display)}")
    print()


if __name__ == "__main__":
    main()
