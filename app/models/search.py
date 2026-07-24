"""Search models (schema: search).

DERIVED DATA ONLY - everything here is regenerable from the canonical
schemas by the indexer. Each document points back to its canonical source
row, which carries the full provenance chain (raw artifact -> import run ->
source). Dropping and rebuilding this schema loses nothing.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import SCHEMA_SEARCH, Base


class SearchDocument(Base):
    """One searchable text unit (ayah, translation, hadith text, tafsir)."""

    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint(
            "doc_type", "source_row_id", "language_code", name="doc_identity"
        ),
        Index("ix_search_documents_tsv", "tsv", postgresql_using="gin"),
        Index(
            "ix_search_documents_trgm",
            "text_normalized",
            postgresql_using="gin",
            postgresql_ops={"text_normalized": "gin_trgm_ops"},
        ),
        Index("ix_search_documents_type_lang", "doc_type", "language_code"),
        {"schema": SCHEMA_SEARCH},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # 'quran_verse' | 'quran_translation' | 'hadith_text' | 'tafsir_entry'
    doc_type: Mapped[str] = mapped_column(String(32))
    language_code: Mapped[str] = mapped_column(String(8))
    # 'quran' | 'bukhari' | 'muslim' | 'ibn-kathir' | ...
    collection_key: Mapped[str] = mapped_column(String(64), index=True)
    # id of the canonical row (quran.verses.id, hadith.hadith_texts.id, ...)
    source_row_id: Mapped[int] = mapped_column(BigInteger)
    # human-readable reference, e.g. "Quran 2:255" / "Sahih al-Bukhari 5735"
    citation: Mapped[str] = mapped_column(String(255))
    # extra reference details for display/filtering (chapter, book, edition)
    ref: Mapped[dict | None] = mapped_column(JSONB)
    text_display: Mapped[str] = mapped_column(Text)
    text_normalized: Mapped[str] = mapped_column(Text)
    tsv: Mapped[str | None] = mapped_column(TSVECTOR)


class SearchIndexState(Base):
    """Fingerprint of the last index build - staleness is detectable."""

    __tablename__ = "index_state"
    __table_args__ = {"schema": SCHEMA_SEARCH}

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)  # always 1
    built_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    indexer_version: Mapped[str] = mapped_column(String(32))
    document_count: Mapped[int] = mapped_column(Integer)
    # counts of canonical rows at build time, per doc_type
    corpus_fingerprint: Mapped[dict] = mapped_column(JSONB)
