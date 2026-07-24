"""Tafsir models (schema: tafsir).

A classical work (e.g. Tafsir Ibn Kathir) exists once in `works`; each
language edition of it (Arabic original, Urdu, English abridged) is a row in
`editions`; the per-ayah commentary text lives in `entries`, keyed to the
canonical quran.verses row - which is what keeps ayah, translations, and
tafsir perfectly aligned across languages.
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import SCHEMA_METADATA, SCHEMA_QURAN, SCHEMA_TAFSIR, Base


class TafsirWork(Base):
    """A classical tafsir work, independent of language."""

    __tablename__ = "works"
    __table_args__ = {"schema": SCHEMA_TAFSIR}

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), unique=True)  # "ibn-kathir"
    name: Mapped[str] = mapped_column(String(255))  # Tafsir Ibn Kathir
    author_name: Mapped[str | None] = mapped_column(String(255))

    editions: Mapped[list["TafsirEdition"]] = relationship(back_populates="work")


class TafsirEdition(Base):
    """One language edition of a work, as offered by the source."""

    __tablename__ = "editions"
    __table_args__ = {"schema": SCHEMA_TAFSIR}

    # quran.com tafsir resource id (14 = ar Ibn Kathir, 160 = ur, 169 = en)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey(f"{SCHEMA_TAFSIR}.works.id")
    )
    language_code: Mapped[str] = mapped_column(String(8))
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str | None] = mapped_column(String(255))
    source_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey(f"{SCHEMA_METADATA}.sources.id")
    )

    work: Mapped[TafsirWork] = relationship(back_populates="editions")
    entries: Mapped[list["TafsirEntry"]] = relationship(back_populates="edition")


class TafsirEntry(Base):
    """Commentary on one ayah in one edition, verbatim from the source."""

    __tablename__ = "entries"
    __table_args__ = (
        UniqueConstraint("edition_id", "verse_id", name="edition_verse"),
        {"schema": SCHEMA_TAFSIR},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    edition_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA_TAFSIR}.editions.id")
    )
    verse_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA_QURAN}.verses.id"), index=True
    )
    source_entry_id: Mapped[int | None] = mapped_column(BigInteger)
    text: Mapped[str] = mapped_column(Text)
    raw_artifact_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA_METADATA}.raw_artifacts.id")
    )

    edition: Mapped[TafsirEdition] = relationship(back_populates="entries")
