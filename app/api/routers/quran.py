"""Quran endpoints: chapters, verses, aligned translations + tafsir."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.quran import (
    Chapter,
    TranslationResource,
    Verse,
    VerseTranslation,
)
from app.models.tafsir import TafsirEdition, TafsirEntry
from app.schemas.quran import (
    ChapterOut,
    TafsirEntryOut,
    TranslationOut,
    VerseDetailOut,
)

router = APIRouter(prefix="/quran", tags=["quran"])


@router.get("/chapters", response_model=list[ChapterOut])
def list_chapters(db: Session = Depends(get_db)) -> list[ChapterOut]:
    chapters = db.scalars(select(Chapter).order_by(Chapter.id)).all()
    return [ChapterOut.model_validate(c, from_attributes=True) for c in chapters]


@router.get("/chapters/{chapter_id}", response_model=ChapterOut)
def get_chapter(chapter_id: int, db: Session = Depends(get_db)) -> ChapterOut:
    chapter = db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(404, "Chapter not found")
    return ChapterOut.model_validate(chapter, from_attributes=True)


@router.get("/chapters/{chapter_id}/verses", response_model=list[VerseDetailOut])
def get_chapter_verses(
    chapter_id: int,
    translations: str | None = Query(
        None, description="comma-separated translation resource ids"
    ),
    tafsir: str | None = Query(
        None, description="comma-separated tafsir edition ids"
    ),
    db: Session = Depends(get_db),
) -> list[VerseDetailOut]:
    if db.get(Chapter, chapter_id) is None:
        raise HTTPException(404, "Chapter not found")

    verses = db.scalars(
        select(Verse).where(Verse.chapter_id == chapter_id).order_by(Verse.verse_number)
    ).all()
    verse_ids = [v.id for v in verses]

    translation_ids = _parse_ids(translations)
    tafsir_ids = _parse_ids(tafsir)

    tr_by_verse: dict[int, list[TranslationOut]] = {}
    if translation_ids and verse_ids:
        rows = db.execute(
            select(VerseTranslation, TranslationResource)
            .join(
                TranslationResource,
                TranslationResource.id == VerseTranslation.resource_id,
            )
            .where(
                VerseTranslation.verse_id.in_(verse_ids),
                VerseTranslation.resource_id.in_(translation_ids),
            )
        )
        for vt, res in rows:
            tr_by_verse.setdefault(vt.verse_id, []).append(
                TranslationOut(
                    resource_id=res.id,
                    language_code=res.language_code,
                    resource_name=res.name,
                    text=vt.text,
                )
            )

    tf_by_verse: dict[int, list[TafsirEntryOut]] = {}
    if tafsir_ids and verse_ids:
        rows = db.execute(
            select(TafsirEntry, TafsirEdition)
            .join(TafsirEdition, TafsirEdition.id == TafsirEntry.edition_id)
            .where(
                TafsirEntry.verse_id.in_(verse_ids),
                TafsirEntry.edition_id.in_(tafsir_ids),
            )
        )
        for entry, edition in rows:
            tf_by_verse.setdefault(entry.verse_id, []).append(
                TafsirEntryOut(
                    edition_id=edition.id,
                    language_code=edition.language_code,
                    edition_name=edition.name,
                    text=entry.text,
                )
            )

    result = []
    for v in verses:
        detail = VerseDetailOut(
            id=v.id,
            verse_key=v.verse_key,
            verse_number=v.verse_number,
            text_uthmani=v.text_uthmani,
            juz_number=v.juz_number,
            page_number=v.page_number,
            translations=tr_by_verse.get(v.id, []),
            tafsir=tf_by_verse.get(v.id, []),
        )
        result.append(detail)
    return result


@router.get("/resources/translations")
def list_translation_resources(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(TranslationResource).order_by(TranslationResource.id)).all()
    return [
        {
            "id": r.id,
            "language_code": r.language_code,
            "name": r.name,
            "author_name": r.author_name,
        }
        for r in rows
    ]


@router.get("/resources/tafsirs")
def list_tafsir_editions(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(TafsirEdition).order_by(TafsirEdition.id)).all()
    return [
        {
            "id": e.id,
            "language_code": e.language_code,
            "name": e.name,
            "slug": e.slug,
        }
        for e in rows
    ]


def _parse_ids(raw: str | None) -> list[int]:
    if not raw:
        return []
    out = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            out.append(int(part))
    return out
