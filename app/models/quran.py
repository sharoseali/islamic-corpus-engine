"""Canonical Quran models (schema: quran).

The Arabic text stored here is the Uthmani script exactly as served by
quran.com (Quran Foundation API) - never modified (Source Fidelity).
Every row carries a raw_artifact_id linking to the exact archived bytes
it was parsed from.
"""

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import SCHEMA_METADATA, SCHEMA_QURAN, Base


class Chapter(Base):
    """A surah (1–114)."""

    __tablename__ = "chapters"
    __table_args__ = (
        CheckConstraint("id BETWEEN 1 AND 114", name="id_range"),
        CheckConstraint(
            "revelation_place IN ('makkah', 'madinah')", name="revelation_place_valid"
        ),
        {"schema": SCHEMA_QURAN},
    )

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)  # surah number
    name_arabic: Mapped[str] = mapped_column(String(64))  # e.g. الفاتحة
    name_simple: Mapped[str] = mapped_column(String(64))  # e.g. Al-Fatihah
    name_complex: Mapped[str] = mapped_column(String(64))  # e.g. Al-Fātiĥah
    translated_name: Mapped[str | None] = mapped_column(String(128))  # The Opener
    revelation_place: Mapped[str] = mapped_column(String(16))
    revelation_order: Mapped[int] = mapped_column(SmallInteger)
    verses_count: Mapped[int] = mapped_column(SmallInteger)
    bismillah_pre: Mapped[bool] = mapped_column(Boolean)
    raw_artifact_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA_METADATA}.raw_artifacts.id")
    )

    verses: Mapped[list["Verse"]] = relationship(back_populates="chapter")


class Verse(Base):
    """An ayah, with Uthmani Arabic text exactly as served by the source."""

    __tablename__ = "verses"
    __table_args__ = (
        UniqueConstraint("chapter_id", "verse_number", name="chapter_verse"),
        CheckConstraint("verse_number >= 1", name="verse_number_positive"),
        {"schema": SCHEMA_QURAN},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # quran.com verse id
    chapter_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey(f"{SCHEMA_QURAN}.chapters.id")
    )
    verse_number: Mapped[int] = mapped_column(SmallInteger)
    verse_key: Mapped[str] = mapped_column(String(8), unique=True)  # "2:255"
    text_uthmani: Mapped[str] = mapped_column(Text)
    juz_number: Mapped[int] = mapped_column(SmallInteger)
    hizb_number: Mapped[int | None] = mapped_column(SmallInteger)
    rub_el_hizb_number: Mapped[int | None] = mapped_column(SmallInteger)
    ruku_number: Mapped[int | None] = mapped_column(SmallInteger)
    manzil_number: Mapped[int | None] = mapped_column(SmallInteger)
    sajdah_number: Mapped[int | None] = mapped_column(SmallInteger)
    page_number: Mapped[int | None] = mapped_column(SmallInteger)  # madani mushaf
    raw_artifact_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA_METADATA}.raw_artifacts.id")
    )

    chapter: Mapped[Chapter] = relationship(back_populates="verses")
    translations: Mapped[list["VerseTranslation"]] = relationship(
        back_populates="verse"
    )


class TranslationResource(Base):
    """A translation edition offered by the source (e.g. Saheeh International)."""

    __tablename__ = "translation_resources"
    __table_args__ = {"schema": SCHEMA_QURAN}

    # quran.com resource id, e.g. 131 = Saheeh International
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    language_code: Mapped[str] = mapped_column(String(8))  # "en", "ur"
    name: Mapped[str] = mapped_column(String(255))
    author_name: Mapped[str | None] = mapped_column(String(255))
    slug: Mapped[str | None] = mapped_column(String(255))
    source_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey(f"{SCHEMA_METADATA}.sources.id")
    )

    translations: Mapped[list["VerseTranslation"]] = relationship(
        back_populates="resource"
    )


class VerseTranslation(Base):
    """The translation of one ayah in one edition, verbatim from the source."""

    __tablename__ = "verse_translations"
    __table_args__ = (
        UniqueConstraint("verse_id", "resource_id", name="verse_resource"),
        {"schema": SCHEMA_QURAN},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    verse_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA_QURAN}.verses.id"))
    resource_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA_QURAN}.translation_resources.id"), index=True
    )
    text: Mapped[str] = mapped_column(Text)
    raw_artifact_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA_METADATA}.raw_artifacts.id")
    )

    verse: Mapped[Verse] = relationship(back_populates="translations")
    resource: Mapped[TranslationResource] = relationship(back_populates="translations")
