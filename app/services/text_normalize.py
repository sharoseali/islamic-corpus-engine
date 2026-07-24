"""Deterministic text normalization for search indexing.

CRITICAL: these functions produce DERIVED data for the `search` schema only.
Canonical text in the quran/hadith/tafsir schemas is never modified
(Source Fidelity). Normalization is pure and deterministic - the same input
always yields the same output - so the search index is exactly regenerable.
"""

import re
import unicodedata

# --- Arabic ----------------------------------------------------------------

# Combining marks stripped for matching: tashkeel, superscript alef, Quranic
# annotation signs, honorific signs, and tatweel.
_AR_STRIP = re.compile(
    "["
    "ؐ-ؚ"  # honorifics / small signs
    "ً-ٟ"  # tashkeel
    "ٰ"         # superscript alef
    "ۖ-ۭ"  # quranic annotation marks
    "ـ"         # tatweel
    "]"
)

# Letter-form unification (search-side only)
_AR_LETTER_MAP = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",  # alef wasla (Quranic orthography)
        "ى": "ي",
        "ة": "ه",
        "ؤ": "و",
        "ئ": "ي",
        "ء": "",
    }
)


def normalize_arabic(text: str) -> str:
    """Strip diacritics and unify letter forms for matching."""
    text = unicodedata.normalize("NFC", text)
    text = _AR_STRIP.sub("", text)
    text = text.translate(_AR_LETTER_MAP)
    return " ".join(text.split())


# --- Urdu ------------------------------------------------------------------

# Urdu aerab are the same combining range; also unify Arabic-script letter
# variants commonly mixed into Urdu digital text.
_UR_LETTER_MAP = str.maketrans(
    {
        "ي": "ی",  # Arabic yeh -> Farsi yeh
        "ك": "ک",  # Arabic kaf -> keheh
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ہ",
        "ئ": "ی",
        "ء": "",
    }
)


def normalize_urdu(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = _AR_STRIP.sub("", text)
    text = text.translate(_UR_LETTER_MAP)
    return " ".join(text.split())


# --- English ---------------------------------------------------------------

_HTML_TAG = re.compile(r"<[^>]+>")


def normalize_english(text: str) -> str:
    """Strip markup (footnote markers etc.) and lowercase for matching."""
    text = _HTML_TAG.sub(" ", text)
    text = unicodedata.normalize("NFKC", text)
    return " ".join(text.lower().split())


NORMALIZERS = {
    "ar": normalize_arabic,
    "ur": normalize_urdu,
    "en": normalize_english,
}


def normalize(text: str, language_code: str) -> str:
    return NORMALIZERS[language_code](text)
