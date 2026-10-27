"""Search endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.search import (
    MorphologyTermOut,
    QuranSearchOut,
    SearchHitOut,
    SearchResponseOut,
    ThemeOut,
    VerseHitOut,
)
from app.services.search import SearchService
from app.services.verse_search import quran_verse_search

router = APIRouter(prefix="/search", tags=["search"])

_LANG_PATTERN = r"^(ar|ur|en|tr)(,(ar|ur|en|tr))*$"


def _langs(lang: str | None, langs: str | None) -> list[str]:
    raw = langs or lang or "en"
    out: list[str] = []
    for part in raw.split(","):
        part = part.strip()
        if part and part not in out:
            out.append(part)
    return out


@router.get("", response_model=SearchResponseOut)
def search(
    q: str = Query(..., min_length=1, description="Search query"),
    lang: str | None = Query(None, pattern="^(ar|ur|en|tr)$", description="single content language"),
    langs: str | None = Query(None, pattern=_LANG_PATTERN, description="comma-separated content languages"),
    types: str | None = Query(None, description="comma-separated doc_types"),
    collections: str | None = Query(None, description="comma-separated collections"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=1000),
    mode: str = Query("hybrid", pattern="^(keyword|semantic|hybrid)$"),
    rerank: bool = Query(True, description="re-order top candidates with the reranker"),
    with_counts: bool = Query(False, description="include per-group exact-match counts"),
    db: Session = Depends(get_db),
) -> SearchResponseOut:
    language_codes = _langs(lang, langs)
    doc_types = types.split(",") if types else None
    collection_keys = collections.split(",") if collections else None
    service = SearchService(db)
    hits = service.search(
        q, language_codes, doc_types=doc_types, collection_keys=collection_keys,
        limit=limit, offset=offset, mode=mode, rerank=rerank,
    )
    counts = service.match_counts(q, language_codes) if with_counts else {}
    return SearchResponseOut(
        query=q,
        language_code=",".join(language_codes),
        mode=mode,
        offset=offset,
        total=len(hits),
        counts=counts,
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
                snippet=h.snippet,
                snippet_start=h.snippet_start,
                snippet_end=h.snippet_end,
            )
            for h in hits
        ],
    )


@router.get("/quran", response_model=QuranSearchOut)
def search_quran(
    q: str = Query(..., min_length=1),
    langs: str = Query("ar", pattern=_LANG_PATTERN, description="languages to match words in"),
    translation: str | None = Query(None, pattern="^(ur|en|tr)$", description="translation language to display"),
    order: str = Query("mushaf", pattern="^(mushaf|relevance)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0, le=2000),
    mode: str = Query("hybrid", pattern="^(keyword|semantic|hybrid)$"),
    db: Session = Depends(get_db),
) -> QuranSearchOut:
    language_codes = _langs(None, langs)
    result = quran_verse_search(
        db, q, language_codes,
        translation_language=translation, order=order,
        offset=offset, limit=limit, mode=mode,
    )
    return QuranSearchOut(
        query=q,
        languages=language_codes,
        order=order,
        offset=offset,
        total=result.total,
        semantic_extra=result.semantic_extra,
        morphology=[MorphologyTermOut(**t) for t in result.morphology],
        themes=[ThemeOut(**t) for t in result.themes],
        items=[VerseHitOut(**vars(i)) for i in result.items],
    )
