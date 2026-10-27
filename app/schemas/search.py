"""Search API response schemas."""

from pydantic import BaseModel


class SearchHitOut(BaseModel):
    doc_type: str
    language_code: str
    collection_key: str
    citation: str
    source_row_id: int
    text: str
    score: float
    match: str
    ref: dict = {}
    snippet: str | None = None
    snippet_start: int | None = None
    snippet_end: int | None = None


class SearchResponseOut(BaseModel):
    query: str
    language_code: str
    mode: str = "hybrid"
    offset: int = 0
    total: int
    # Exact word-match counts per group (distinct ayat / hadith / passages).
    counts: dict[str, int] = {}
    hits: list[SearchHitOut] = []


class VerseHitOut(BaseModel):
    verse_key: str
    chapter_id: int
    verse_number: int
    chapter_name_simple: str
    chapter_name_arabic: str
    text_uthmani: str
    translation_text: str | None = None
    translation_resource: str | None = None
    translation_language: str | None = None
    matched_in: list[str] = []
    score: float = 0.0
    matched_words: list[int] = []


class MorphologyTermOut(BaseModel):
    word: str
    kind: str  # "root" | "form"
    label: str  # root letters (ص ب ر) or the lemma
    verses: int
    words: int


class ThemeOut(BaseModel):
    theme: str
    chapter_id: int
    chapter_name_simple: str
    chapter_name_arabic: str
    ayah_from: int
    ayah_to: int


class QuranSearchOut(BaseModel):
    query: str
    languages: list[str]
    order: str
    offset: int
    total: int
    semantic_extra: int = 0
    morphology: list[MorphologyTermOut] = []
    themes: list[ThemeOut] = []
    items: list[VerseHitOut] = []
