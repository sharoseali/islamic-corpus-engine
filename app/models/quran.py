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


# -- Morphology (Quranic Arabic Corpus via QUL) -------------------------------
#
# Every word of the Quran with its root, lemma and stem, aligned by position
# to verses.text_uthmani. Scholarly reference data, imported from archived
# files like everything else; never edited here.


class Root(Base):
    """A root (usually three letters) shared by a family of words."""

    __tablename__ = "roots"
    __table_args__ = {"schema": SCHEMA_QURAN}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # QUL root id
    letters: Mapped[str] = mapped_column(String(8), index=True)  # "صبر"
    letters_spaced: Mapped[str] = mapped_column(String(16))  # "ص ب ر" as published
    buckwalter: Mapped[str | None] = mapped_column(String(16))
    words_count: Mapped[int | None] = mapped_column(Integer)
    uniq_words_count: Mapped[int | None] = mapped_column(Integer)
    raw_artifact_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA_METADATA}.raw_artifacts.id")
    )


class Lemma(Base):
    """Dictionary form of a word (vocalised, plus a bare-letter form)."""

    __tablename__ = "lemmas"
    __table_args__ = {"schema": SCHEMA_QURAN}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # QUL lemma id
    text: Mapped[str] = mapped_column(String(64))
    text_clean: Mapped[str] = mapped_column(String(64), index=True)
    raw_artifact_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA_METADATA}.raw_artifacts.id")
    )


class Stem(Base):
    """Word stem (the word without its attached particles and affixes)."""

    __tablename__ = "stems"
    __table_args__ = {"schema": SCHEMA_QURAN}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # QUL stem id
    text: Mapped[str] = mapped_column(String(64))
    text_clean: Mapped[str] = mapped_column(String(64), index=True)
    raw_artifact_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA_METADATA}.raw_artifacts.id")
    )


class Word(Base):
    """One word of the Uthmani text at its 1-based position in the verse."""

    __tablename__ = "words"
    __table_args__ = (
        UniqueConstraint("verse_id", "position", name="uq_word_position"),
        {"schema": SCHEMA_QURAN},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    verse_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA_QURAN}.verses.id"), index=True
    )
    position: Mapped[int] = mapped_column(SmallInteger)
    text_uthmani: Mapped[str] = mapped_column(Text)
    text_normalized: Mapped[str] = mapped_column(String(64), index=True)
    root_id: Mapped[int | None] = mapped_column(
        ForeignKey(f"{SCHEMA_QURAN}.roots.id"), index=True
    )
    lemma_id: Mapped[int | None] = mapped_column(
        ForeignKey(f"{SCHEMA_QURAN}.lemmas.id"), index=True
    )
    stem_id: Mapped[int | None] = mapped_column(
        ForeignKey(f"{SCHEMA_QURAN}.stems.id"), index=True
    )
    raw_artifact_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA_METADATA}.raw_artifacts.id")
    )

    verse: Mapped[Verse] = relationship()
    root: Mapped[Root | None] = relationship()
    lemma: Mapped[Lemma | None] = relationship()
    stem: Mapped[Stem | None] = relationship()


class AyahTheme(Base):
    """A theme or topic covering a range of ayat (QUL "Ayah theme", English).

    Reference data for browsing and for topic search; never shown as if it
    were part of the Quran text."""

    __tablename__ = "ayah_themes"
    __table_args__ = {"schema": SCHEMA_QURAN}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chapter_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA_QURAN}.chapters.id"), index=True
    )
    ayah_from: Mapped[int] = mapped_column(SmallInteger)
    ayah_to: Mapped[int] = mapped_column(SmallInteger)
    theme: Mapped[str] = mapped_column(Text)
    keywords: Mapped[str | None] = mapped_column(Text)
    total_ayahs: Mapped[int | None] = mapped_column(SmallInteger)
    raw_artifact_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA_METADATA}.raw_artifacts.id")
    )
