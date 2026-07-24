"""Search endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.search import SearchHitOut, SearchResponseOut
from app.services.search import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponseOut)
def search(
    q: str = Query(..., min_length=1, description="Search query"),
    lang: str = Query("en", pattern="^(ar|ur|en)$"),
    types: str | None = Query(None, description="comma-separated doc_types"),
    collections: str | None = Query(None, description="comma-separated collections"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> SearchResponseOut:
    doc_types = types.split(",") if types else None
    collection_keys = collections.split(",") if collections else None
    hits = SearchService(db).search(
        q, lang, doc_types=doc_types, collection_keys=collection_keys, limit=limit
    )
    return SearchResponseOut(
        query=q,
        language_code=lang,
        total=len(hits),
        hits=[
            SearchHitOut(
                doc_type=h.doc_type,
                language_code=h.language_code,
                collection_key=h.collection_key,
                citation=h.citation,
                source_row_id=h.source_row_id,
                text=h.text_display,
                score=h.score,
                match=h.match,
                ref=h.ref,
            )
            for h in hits
        ],
    )
