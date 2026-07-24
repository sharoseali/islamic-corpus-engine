"""Quran API response schemas."""

from pydantic import BaseModel


class ChapterOut(BaseModel):
    id: int
    name_arabic: str
    name_simple: str
    name_complex: str
    translated_name: str | None
    revelation_place: str
    revelation_order: int
    verses_count: int
    bismillah_pre: bool


class TranslationOut(BaseModel):
    resource_id: int
    language_code: str
    resource_name: str
    text: str


class TafsirEntryOut(BaseModel):
    edition_id: int
    language_code: str
    edition_name: str
    text: str


class VerseOut(BaseModel):
    id: int
    verse_key: str
    verse_number: int
    text_uthmani: str
    juz_number: int
    page_number: int | None


class VerseDetailOut(VerseOut):
    translations: list[TranslationOut] = []
    tafsir: list[TafsirEntryOut] = []
