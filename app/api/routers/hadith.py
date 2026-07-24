"""Hadith endpoints: collections, books, hadith listing + detail."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.hadith import Hadith, HadithBook, HadithCollection, HadithText
from app.schemas.hadith import (
    HadithBookOut,
    HadithCollectionOut,
    HadithDetailOut,
    HadithListItemOut,
    HadithTextOut,
)

router = APIRouter(prefix="/hadith", tags=["hadith"])


@router.get("/collections", response_model=list[HadithCollectionOut])
def list_collections(db: Session = Depends(get_db)) -> list[HadithCollectionOut]:
    collections = db.scalars(
        select(HadithCollection).order_by(HadithCollection.id)
    ).all()
    out = []
    for c in collections:
        hadith_count = db.scalar(
            select(func.count(Hadith.id)).where(Hadith.collection_id == c.id)
        )
        book_count = db.scalar(
            select(func.count(HadithBook.id)).where(HadithBook.collection_id == c.id)
        )
        out.append(
            HadithCollectionOut(
                id=c.id,
                key=c.key,
                name=c.name,
                name_arabic=c.name_arabic,
                hadith_count=hadith_count or 0,
                book_count=book_count or 0,
            )
        )
    return out


@router.get("/collections/{key}/books", response_model=list[HadithBookOut])
def list_books(key: str, db: Session = Depends(get_db)) -> list[HadithBookOut]:
    collection = db.scalar(select(HadithCollection).where(HadithCollection.key == key))
    if collection is None:
        raise HTTPException(404, "Collection not found")
    books = db.scalars(
        select(HadithBook)
        .where(HadithBook.collection_id == collection.id)
        .order_by(HadithBook.number)
    ).all()
    out = []
    for b in books:
        count = db.scalar(
            select(func.count(Hadith.id)).where(Hadith.book_id == b.id)
        )
        out.append(
            HadithBookOut(
                id=b.id,
                number=b.number,
                name=b.name,
                name_arabic=b.name_arabic,
                name_urdu=b.name_urdu,
                hadith_count=count or 0,
            )
        )
    return out


@router.get(
    "/collections/{key}/books/{book_number}/hadiths",
    response_model=list[HadithListItemOut],
)
def list_hadiths_in_book(
    key: str,
    book_number: int,
    langs: str = Query("ar,ur,en"),
    db: Session = Depends(get_db),
) -> list[HadithListItemOut]:
    collection = db.scalar(select(HadithCollection).where(HadithCollection.key == key))
    if collection is None:
        raise HTTPException(404, "Collection not found")
    book = db.scalar(
        select(HadithBook).where(
            HadithBook.collection_id == collection.id,
            HadithBook.number == book_number,
        )
    )
    if book is None:
        raise HTTPException(404, "Book not found")

    wanted_langs = [x.strip() for x in langs.split(",") if x.strip()]
    hadiths = db.scalars(
        select(Hadith).where(Hadith.book_id == book.id).order_by(Hadith.position)
    ).all()
    return [_hadith_item(db, h, book, wanted_langs) for h in hadiths]


@router.get(
    "/collections/{key}/hadiths/{number}", response_model=HadithDetailOut
)
def get_hadith(
    key: str,
    number: str,
    langs: str = Query("ar,ur,en"),
    db: Session = Depends(get_db),
) -> HadithDetailOut:
    collection = db.scalar(select(HadithCollection).where(HadithCollection.key == key))
    if collection is None:
        raise HTTPException(404, "Collection not found")
    hadith = db.scalar(
        select(Hadith).where(
            Hadith.collection_id == collection.id, Hadith.hadith_number == number
        )
    )
    if hadith is None:
        raise HTTPException(404, "Hadith not found")
    book = db.get(HadithBook, hadith.book_id) if hadith.book_id else None
    wanted = [x.strip() for x in langs.split(",") if x.strip()]
    item = _hadith_item(db, hadith, book, wanted)
    return HadithDetailOut(
        **item.model_dump(),
        collection_key=collection.key,
        collection_name=collection.name,
    )


def _hadith_item(
    db: Session, hadith: Hadith, book: HadithBook | None, langs: list[str]
) -> HadithListItemOut:
    texts = db.scalars(
        select(HadithText).where(
            HadithText.hadith_id == hadith.id,
            HadithText.language_code.in_(langs),
        )
    ).all()
    order = {lang: i for i, lang in enumerate(langs)}
    texts_sorted = sorted(texts, key=lambda t: order.get(t.language_code, 99))
    return HadithListItemOut(
        id=hadith.id,
        hadith_number=hadith.hadith_number,
        arabic_number=hadith.arabic_number,
        book_number=book.number if book else None,
        book_name=book.name if book else None,
        grades=hadith.grades,
        texts=[
            HadithTextOut(language_code=t.language_code, text=t.text)
            for t in texts_sorted
        ],
    )
