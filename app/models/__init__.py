"""ORM models. Importing this package registers all tables on Base.metadata."""

from app.models.hadith import Hadith, HadithBook, HadithCollection, HadithText
from app.models.provenance import ImportRun, RawArtifact, Source
from app.models.quran import (
    AyahTheme,
    Chapter,
    Lemma,
    Root,
    Stem,
    TranslationResource,
    Verse,
    VerseTranslation,
    Word,
)
from app.models.search import SearchDocument, SearchIndexState, SearchVocabulary
from app.models.search_chunks import EmbeddingState, SearchChunk
from app.models.tafsir import TafsirEdition, TafsirEntry, TafsirWork

__all__ = [
    "Source",
    "ImportRun",
    "RawArtifact",
    "Chapter",
    "Verse",
    "Root",
    "Lemma",
    "Stem",
    "Word",
    "AyahTheme",
    "TranslationResource",
    "VerseTranslation",
    "HadithCollection",
    "HadithBook",
    "Hadith",
    "HadithText",
    "TafsirWork",
    "TafsirEdition",
    "TafsirEntry",
    "SearchDocument",
    "SearchIndexState",
    "SearchVocabulary",
    "SearchChunk",
    "EmbeddingState",
]
