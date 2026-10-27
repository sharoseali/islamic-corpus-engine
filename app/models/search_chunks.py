"""Semantic search models (schema: search).

DERIVED DATA ONLY, like search.documents. A chunk is a passage-sized piece
of one search document (a whole ayah, translation or short hadith; a long
hadith or tafsir entry split into pieces) together with its embedding
vector. Every chunk points back to its search document and canonical row,
so a hit resolves to the exact source passage with full provenance.

The embedding model is a measuring instrument, not a source: it reads our
stored text and produces numbers. Nothing from the model is ever shown.
EmbeddingState pins the exact model files (name, revision, checksums) so
the vectors are reproducible.
"""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import SCHEMA_SEARCH, Base

EMBEDDING_DIM = 1024


class SearchChunk(Base):
    """One embedded passage of a search document."""

    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="chunk_identity"),
        Index("ix_search_chunks_type_lang", "doc_type", "language_code"),
        Index(
            "ix_search_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 32, "ef_construction": 256},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        {"schema": SCHEMA_SEARCH},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA_SEARCH}.documents.id", ondelete="CASCADE")
    )
    chunk_index: Mapped[int] = mapped_column(SmallInteger)
    # Denormalized from the document for fast filtering without a join.
    doc_type: Mapped[str] = mapped_column(String(32))
    language_code: Mapped[str] = mapped_column(String(8))
    collection_key: Mapped[str] = mapped_column(String(64))
    # The exact passage that was embedded (display text, markup stripped).
    text: Mapped[str] = mapped_column(Text)
    # Character offsets of the passage inside documents.text_display.
    char_start: Mapped[int] = mapped_column(Integer)
    char_end: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))


class EmbeddingState(Base):
    """Which model produced the vectors currently in search.chunks."""

    __tablename__ = "embedding_state"
    __table_args__ = {"schema": SCHEMA_SEARCH}

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)  # always 1
    built_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    model_name: Mapped[str] = mapped_column(String(128))
    model_dim: Mapped[int] = mapped_column(Integer)
    # sha256 of every model file used, keyed by file name
    model_files: Mapped[dict] = mapped_column(JSONB)
    chunker_version: Mapped[str] = mapped_column(String(32))
    chunk_count: Mapped[int] = mapped_column(Integer)
    documents_indexed: Mapped[int] = mapped_column(Integer)
