"""Hadith models (schema: hadith).

Designed around sunnah.com's structure (collection -> book/kitab -> hadith)
so the official sunnah.com API import can slot in without schema changes.
Interim data comes from a pinned mirror; every row carries provenance and
nothing is invented - numbers and texts are stored exactly as served.

Numbering notes:
- `hadith_number`  - the source's primary number (Bukhari: canonical
  Fath al-Bari 1–7563; Muslim: sequential entry number). Stored as text
  because variants like "402.2" exist.
- `arabic_number`  - the source's secondary/canonical Arabic numbering
  (Muslim: Abd al-Baqi base number with variant decimals). Nullable.
- `position`       - 1-based order of the entry in the source file; the
  guaranteed-unique key within a collection.
"""

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import SCHEMA_HADITH, SCHEMA_METADATA, Base


class HadithCollection(Base):
    """A hadith book/collection (e.g. Sahih al-Bukhari)."""

    __tablename__ = "collections"
    __table_args__ = {"schema": SCHEMA_HADITH}

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), unique=True)  # "bukhari"
    name: Mapped[str] = mapped_column(String(255))  # as served by source
    name_arabic: Mapped[str | None] = mapped_column(String(255))
    author: Mapped[str | None] = mapped_column(String(255))
    author_arabic: Mapped[str | None] = mapped_column(String(255))
    raw_artifact_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA_METADATA}.raw_artifacts.id")
    )

    books: Mapped[list["HadithBook"]] = relationship(back_populates="collection")
    hadiths: Mapped[list["Hadith"]] = relationship(back_populates="collection")


class HadithBook(Base):
    """A book (kitab) within a collection, e.g. 'The Book of Faith'."""

    __tablename__ = "books"
    __table_args__ = (
        UniqueConstraint("collection_id", "number", name="collection_book_number"),
        {"schema": SCHEMA_HADITH},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    collection_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey(f"{SCHEMA_HADITH}.collections.id")
    )
    number: Mapped[int] = mapped_column(SmallInteger)  # 0 = introduction
    name: Mapped[str | None] = mapped_column(String(512))  # English, as served
    name_arabic: Mapped[str | None] = mapped_column(String(512))
    name_urdu: Mapped[str | None] = mapped_column(String(512))
    raw_artifact_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA_METADATA}.raw_artifacts.id")
    )

    collection: Mapped[HadithCollection] = relationship(back_populates="books")
    hadiths: Mapped[list["Hadith"]] = relationship(back_populates="book")


class Hadith(Base):
    """One hadith entry (structure only - texts live in hadith_texts)."""

    __tablename__ = "hadiths"
    __table_args__ = (
        UniqueConstraint("collection_id", "position", name="collection_position"),
        {"schema": SCHEMA_HADITH},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    collection_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey(f"{SCHEMA_HADITH}.collections.id")
    )
    book_id: Mapped[int | None] = mapped_column(
        ForeignKey(f"{SCHEMA_HADITH}.books.id"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)  # 1-based order in source
    hadith_number: Mapped[str] = mapped_column(String(16), index=True)
    arabic_number: Mapped[str | None] = mapped_column(String(16), index=True)
    hadith_in_book: Mapped[int | None] = mapped_column(Integer)
    grades: Mapped[list | None] = mapped_column(JSONB)  # source gradings, verbatim

    collection: Mapped[HadithCollection] = relationship(back_populates="hadiths")
    book: Mapped[HadithBook | None] = relationship(back_populates="hadiths")
    texts: Mapped[list["HadithText"]] = relationship(back_populates="hadith")


class HadithText(Base):
    """The text of one hadith in one language, verbatim from the source."""

    __tablename__ = "hadith_texts"
    __table_args__ = (
        UniqueConstraint("hadith_id", "language_code", name="hadith_language"),
        {"schema": SCHEMA_HADITH},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    hadith_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA_HADITH}.hadiths.id")
    )
    language_code: Mapped[str] = mapped_column(String(8))  # "ar", "ur", "en"
    text: Mapped[str] = mapped_column(Text)
    raw_artifact_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA_METADATA}.raw_artifacts.id")
    )

    hadith: Mapped[Hadith] = relationship(back_populates="texts")
