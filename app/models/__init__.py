"""ORM models. Importing this package registers all tables on Base.metadata."""

from app.models.hadith import Hadith, HadithBook, HadithCollection, HadithText
from app.models.provenance import ImportRun, RawArtifact, Source
from app.models.quran import Chapter, TranslationResource, Verse, VerseTranslation
from app.models.search import SearchDocument, SearchIndexState
from app.models.tafsir import TafsirEdition, TafsirEntry, TafsirWork

__all__ = [
    "Source",
    "ImportRun",
    "RawArtifact",
    "Chapter",
    "Verse",
    "TranslationResource",
    "VerseTranslation",
    "HadithCollection",
    "HadithBook",
    "Hadith",
    "HadithText",
    "TafsirWork",
    "TafsirEdition",
    "TafsirEntry",
]
