"""Search service.

Two-stage retrieval over search.documents:
  1. Ranked full-text search (PostgreSQL tsvector + ts_rank).
  2. If FTS yields too few hits, a fuzzy trigram fallback (pg_trgm
     similarity) catches misspellings and partial words.

Queries are normalized with the SAME functions used to build the index, so
a query written with or without diacritics matches identically. Every result
carries its citation and canonical pointer, from which the full provenance
chain (raw artifact -> import run -> source) can be resolved.
"""

from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.text_normalize import normalize

# language -> tsvector config used at index time
_TS_CONFIG = {"ar": "simple", "ur": "simple", "en": "english"}


@dataclass
class SearchHit:
    doc_type: str
    language_code: str
    collection_key: str
    citation: str
    source_row_id: int
    text_display: str
    score: float
    match: str  # "fulltext" | "fuzzy"
    ref: dict = field(default_factory=dict)


class SearchService:
    def __init__(self, session: Session):
        self.session = session

    def search(
        self,
        query: str,
        language_code: str,
        *,
        doc_types: list[str] | None = None,
        collection_keys: list[str] | None = None,
        limit: int = 20,
        fuzzy_threshold: float = 0.3,
    ) -> list[SearchHit]:
        normalized = normalize(query, language_code)
        if not normalized:
            return []
        config = _TS_CONFIG.get(language_code, "simple")

        filters = ["language_code = :lang"]
        params: dict = {"lang": language_code, "q": normalized, "limit": limit}
        if doc_types:
            filters.append("doc_type = ANY(:doc_types)")
            params["doc_types"] = doc_types
        if collection_keys:
            filters.append("collection_key = ANY(:colls)")
            params["colls"] = collection_keys
        where = " AND ".join(filters)

        hits = self._fulltext(where, params, config)
        if len(hits) < limit:
            seen = {(h.doc_type, h.source_row_id) for h in hits}
            params["thresh"] = fuzzy_threshold
            for h in self._fuzzy(where, params):
                if (h.doc_type, h.source_row_id) not in seen:
                    hits.append(h)
                    if len(hits) >= limit:
                        break
        return hits[:limit]

    # -- stages -----------------------------------------------------------

    def _fulltext(self, where: str, params: dict, config: str) -> list[SearchHit]:
        sql = text(
            f"""
            SELECT doc_type, language_code, collection_key, citation,
                   source_row_id, text_display, ref,
                   ts_rank(tsv, websearch_to_tsquery('{config}', :q)) AS score
            FROM search.documents
            WHERE {where}
              AND tsv @@ websearch_to_tsquery('{config}', :q)
            ORDER BY score DESC
            LIMIT :limit
            """
        )
        return [self._to_hit(r, "fulltext") for r in self.session.execute(sql, params)]

    def _fuzzy(self, where: str, params: dict) -> list[SearchHit]:
        sql = text(
            f"""
            SELECT doc_type, language_code, collection_key, citation,
                   source_row_id, text_display, ref,
                   similarity(text_normalized, :q) AS score
            FROM search.documents
            WHERE {where}
              AND text_normalized % :q
              AND similarity(text_normalized, :q) >= :thresh
            ORDER BY score DESC
            LIMIT :limit
            """
        )
        return [self._to_hit(r, "fuzzy") for r in self.session.execute(sql, params)]

    @staticmethod
    def _to_hit(row, match: str) -> SearchHit:
        return SearchHit(
            doc_type=row.doc_type,
            language_code=row.language_code,
            collection_key=row.collection_key,
            citation=row.citation,
            source_row_id=row.source_row_id,
            text_display=row.text_display,
            score=float(row.score),
            match=match,
            ref=row.ref or {},
        )
