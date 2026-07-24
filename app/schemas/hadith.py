"""Hadith API response schemas."""

from pydantic import BaseModel


class HadithCollectionOut(BaseModel):
    id: int
    key: str
    name: str
    name_arabic: str | None
    hadith_count: int
    book_count: int


class HadithBookOut(BaseModel):
    id: int
    number: int
    name: str | None
    name_arabic: str | None
    name_urdu: str | None
    hadith_count: int


class HadithTextOut(BaseModel):
    language_code: str
    text: str


class HadithListItemOut(BaseModel):
    id: int
    hadith_number: str
    arabic_number: str | None
    book_number: int | None
    book_name: str | None
    grades: list | None
    texts: list[HadithTextOut] = []


class HadithDetailOut(HadithListItemOut):
    collection_key: str
    collection_name: str
