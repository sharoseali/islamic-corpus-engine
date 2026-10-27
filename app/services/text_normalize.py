"""Deterministic text normalization for search indexing.

CRITICAL: these functions produce DERIVED data for the `search` schema only.
Canonical text in the quran/hadith/tafsir schemas is never modified
(Source Fidelity). Normalization is pure and deterministic - the same input
always yields the same output - so the search index is exactly regenerable.

Two layers:
  normalize()      -> one readable normalized string per text (trigram
                      matching, display of matches).
  search_tokens()  -> the expanded token list the tsvector is built from:
                      each word plus its spelling variants and light stem,
                      so one typed word finds its inflected forms.
  query_tsquery()  -> the matching tsquery for a user query.
"""

import re
import unicodedata

# --- Arabic ----------------------------------------------------------------

# Combining marks stripped for matching: tashkeel, Quranic annotation signs,
# honorific signs, and tatweel. The superscript (dagger) alef U+0670 is NOT
# in this set: in Uthmani script it stands for a real alef that modern
# spelling writes out (شيطان, كتاب, سماوات), so it is handled separately.
_AR_STRIP = re.compile(
    "["
    "ؐ-ؚ"  # honorifics / small signs
    "ً-ٟ"  # tashkeel
    "ۖ-ۭ"  # quranic annotation marks
    "ـ"         # tatweel
    "]"
)

# Urdu aerab share the range; Urdu also drops the superscript alef
# (تعالیٰ -> تعالی), which is how Urdu readers type it.
_UR_STRIP = re.compile(
    "["
    "ؐ-ؚ"
    "ً-ٟ"
    "ٰ"
    "ۖ-ۭ"
    "ـ"
    "]"
)

_DAGGER = "ٰ"

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
        # Urdu keyboard letter forms typed into an Arabic search
        "ی": "ي",
        "ے": "ي",
        "ک": "ك",
        "ہ": "ه",
        "ۃ": "ه",
        "ۀ": "ه",
    }
)

# Words whose dagger alef is NOT written in modern spelling. Keyed by the
# written-out form, valued by the usual spelling. Both forms are indexed.
_AR_DAGGER_EXCEPTIONS = {
    "ذالك": "ذلك",
    "ذالكم": "ذلكم",
    "ذالكما": "ذلكما",
    "هاذا": "هذا",
    "هاذه": "هذه",
    "هاذان": "هذان",
    "هاذين": "هذين",
    "هاتين": "هتين",
    "هاؤلاء": "هؤلاء",
    "هاكذا": "هكذا",
    "لاكن": "لكن",
    "لاكنا": "لكنا",
    "لاكنكم": "لكنكم",
    "لاكننا": "لكننا",
    "الرحمان": "الرحمن",
    "رحمان": "رحمن",
    "الاه": "اله",
    "الاها": "الها",
    "الاهين": "الهين",
    "الاهه": "الهه",
    "الاهتكم": "الهتكم",
    "اولائك": "اولئك",
    "اولائكم": "اولئكم",
    "طاها": "طه",
    "ياسين": "يس",
}

_NON_WORD = re.compile(r"[^\w]+", re.UNICODE)

# Light10-style stemming (Larkey et al.): one prefix, one suffix, never
# below three letters. Written against text already passed through the
# letter map, so ة appears as ه and ى as ي.
_AR_PREFIXES = ("وال", "بال", "كال", "فال", "لل", "ال", "و")
# Attached object/possessive pronouns are stripped first (شياطينهم ->
# شياطين), then one inflectional ending (-> شياط). Each pass keeps at least
# three letters.
_AR_PRONOUN_SUFFIXES = ("هما", "كما", "هم", "هن", "كم", "كن", "نا", "ها", "ك")
_AR_SUFFIXES = ("ان", "ات", "ون", "ين", "يه", "ه", "ي")


# Uthmani orthography that modern spelling writes differently. Applied while
# the marks are still present, because the marks decide the case:
# - a waw with no vowel before a dagger alef is a silent waw standing for
#   alef (ٱلصَّلَوٰةَ -> الصلاة, ٱلزَّكَوٰةَ, ٱلْحَيَوٰةِ, ٱلرِّبَوٰا۟ -> الربا), while a
#   waw carrying a vowel keeps its sound (ٱلسَّمَٰوَٰتِ -> السماوات);
# - alef maqsura + dagger alef + ta marbuta is written with alef
#   (ٱلتَّوْرَىٰةَ -> التوراة);
# - the lam of the article carrying a shadda is a doubled lam (ٱلَّيْلِ ->
#   الليل, ٱلَّـٰٓئِى -> اللائي), except in the relative pronouns الذي / الذين /
#   التي, which modern spelling writes with one lam. The alef wasla marks
#   the article, so a shadda on a lam elsewhere (ٱلضَّآلِّينَ) is untouched.
_UTHMANI_SILENT_WAW = re.compile("و" + _DAGGER + "(?:ا\u06df)?")
_UTHMANI_MAQSURA_ALEF = re.compile("ى" + _DAGGER + "ة")
_UTHMANI_DOUBLED_LAM = re.compile(
    "(?:^|(?<=[\u064b-\u0652]))ٱل([\u064b-\u0652]*\u0651[\u064b-\u0652]*)(?![ذت])"
)


def _uthmani_to_modern(word: str) -> str:
    word = _UTHMANI_SILENT_WAW.sub("ا", word)
    word = _UTHMANI_MAQSURA_ALEF.sub("اة", word)
    return _UTHMANI_DOUBLED_LAM.sub(r"ٱلل\1", word)


def _arabic_word_variants(word: str) -> list[str]:
    """Spelling variants of one Arabic word (marks already stripped).

    Returns the written-out form first, then the dagger-dropped form when
    the word carried a dagger alef and the two differ.
    """
    written = word.replace("ى" + _DAGGER, "ى").replace(_DAGGER, "ا")
    written = _NON_WORD.sub("", written.translate(_AR_LETTER_MAP))
    out = [_AR_DAGGER_EXCEPTIONS.get(written, written)]
    if _DAGGER in word:
        dropped = _NON_WORD.sub("", word.replace(_DAGGER, "").translate(_AR_LETTER_MAP))
        if dropped not in out:
            out.append(dropped)
        if written not in out:
            out.append(written)
    return [w for w in out if w]


def _arabic_words(text: str) -> list[list[str]]:
    text = unicodedata.normalize("NFC", text)
    words = (_AR_STRIP.sub("", _uthmani_to_modern(w)) for w in text.split())
    return [v for v in (_arabic_word_variants(w) for w in words) if v]


def normalize_arabic(text: str) -> str:
    """Strip diacritics and unify letter forms for matching."""
    return " ".join(v[0] for v in _arabic_words(text))


def arabic_light_stem(word: str) -> str:
    for p in _AR_PREFIXES:
        if word.startswith(p) and len(word) - len(p) >= 3:
            word = word[len(p):]
            break
    for s in _AR_PRONOUN_SUFFIXES:
        if word.endswith(s) and len(word) - len(s) >= 3:
            word = word[: -len(s)]
            break
    for s in _AR_SUFFIXES:
        if word.endswith(s) and len(word) - len(s) >= 3:
            word = word[: -len(s)]
            break
    return word


# --- Urdu ------------------------------------------------------------------

# Unify Arabic-script letter variants commonly mixed into Urdu digital text.
_UR_LETTER_MAP = str.maketrans(
    {
        "ي": "ی",  # Arabic yeh -> Farsi yeh
        "ك": "ک",  # Arabic kaf -> keheh
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ہ",
        "ۃ": "ہ",
        "ئ": "ی",
        "ء": "",
    }
)

# Common inflectional endings (پردے/پردوں -> پرد, کتابیں -> کتاب).
_UR_SUFFIXES = ("ئیں", "وں", "یں", "ات", "ے", "ہ", "ی")


def normalize_urdu(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = _UR_STRIP.sub("", text)
    text = text.translate(_UR_LETTER_MAP)
    return " ".join(text.split())


def urdu_light_stem(word: str) -> str:
    for s in _UR_SUFFIXES:
        if word.endswith(s) and len(word) - len(s) >= 3:
            return word[: -len(s)]
    return word


# --- English ---------------------------------------------------------------

_HTML_TAG = re.compile(r"<[^>]+>")


def normalize_english(text: str) -> str:
    """Strip markup (footnote markers etc.) and lowercase for matching."""
    text = _HTML_TAG.sub(" ", text)
    text = unicodedata.normalize("NFKC", text)
    return " ".join(text.lower().split())


# --- Turkish ---------------------------------------------------------------

# Python's lower() turns İ into "i" + combining dot; map the Turkish pair
# explicitly so İstanbul -> istanbul and ISLAM -> ıslam stay consistent.
_TR_CASE = str.maketrans({"İ": "i", "I": "ı"})


def normalize_turkish(text: str) -> str:
    text = _HTML_TAG.sub(" ", text)
    text = unicodedata.normalize("NFKC", text)
    return " ".join(text.translate(_TR_CASE).lower().split())


NORMALIZERS = {
    "ar": normalize_arabic,
    "ur": normalize_urdu,
    "en": normalize_english,
    "tr": normalize_turkish,
}

# Languages whose stemming PostgreSQL does itself (snowball configs).
PG_STEMMED = {"en": "english", "tr": "turkish"}


def normalize(text: str, language_code: str) -> str:
    return NORMALIZERS[language_code](text)


# --- Token expansion for the full-text index -------------------------------


def _word_groups(text: str, language_code: str) -> list[list[str]]:
    """Per word: its variant spellings and stems, deduplicated, in order."""
    groups: list[list[str]] = []
    if language_code == "ar":
        for variants in _arabic_words(text):
            seen: list[str] = []
            for v in variants:
                for form in (v, arabic_light_stem(v)):
                    if form and form not in seen:
                        seen.append(form)
            groups.append(seen)
    elif language_code == "ur":
        for w in normalize_urdu(text).split():
            w = _NON_WORD.sub("", w)
            if not w:
                continue
            stem = urdu_light_stem(w)
            groups.append([w] if stem == w else [w, stem])
    else:
        for w in normalize(text, language_code).split():
            w = _NON_WORD.sub("", w)
            if w:
                groups.append([w])
    return groups


def search_tokens(text: str, language_code: str) -> str:
    """Space-joined expanded tokens to feed to to_tsvector('simple')."""
    return " ".join(tok for group in _word_groups(text, language_code) for tok in group)


def ts_config(language_code: str) -> str:
    # English and Turkish stem via PostgreSQL's snowball configs; Arabic and
    # Urdu are expanded in Python and indexed with 'simple'.
    return PG_STEMMED.get(language_code, "simple")


def _lexeme(tok: str) -> str:
    return "'" + tok.replace("'", "''") + "'"


def query_tsquery(text: str, language_code: str) -> str | None:
    """tsquery string for to_tsquery(): every word must match in some form."""
    groups = _word_groups(text, language_code)
    if not groups:
        return None
    return " & ".join(
        "(" + " | ".join(_lexeme(t) for t in g) + ")" if len(g) > 1 else _lexeme(g[0])
        for g in groups
    )


def term_tsquery(term: str, language_code: str) -> str | None:
    """tsquery string matching any form of a single (already normalized) term."""
    groups = _word_groups(term, language_code)
    if not groups:
        return None
    forms: list[str] = []
    for g in groups:
        for t in g:
            if t not in forms:
                forms.append(t)
    return " | ".join(_lexeme(t) for t in forms)
