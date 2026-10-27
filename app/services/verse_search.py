"""Verse-centric Quran search: "every ayah where this word occurs".

Arabic query words are first matched to the Quranic Arabic Corpus
morphology (quran.roots / lemmas / stems / words): a word typed as its root
letters (صبر) lists every ayah with any form of that root, and a word form
(الصابرين) lists every ayah with that lemma. Keyword hits on the Arabic text
and on the translations are then collapsed to ayat, so one ayah appears once
whether the word was found by root, in the Arabic or in the translation. Results come in mushaf order (surah, ayah) for
exhaustive word lists, or by relevance. Each item carries the Uthmani text
and the translation in the reader's language, taken verbatim from the
canonical tables.
"""

import re
import threading
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

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
from app.services.search import SearchService
from app.services.text_normalize import arabic_light_stem, normalize_arabic

_ARABIC_SCRIPT = re.compile(r"[\u0600-\u06FF]")
_ARTICLE_PREFIXES = ("وال", "بال", "كال", "فال", "لل", "ال")

# Keyword candidates gathered per language before collapsing to ayat.
_KEYWORD_CANDIDATES = 400
# Meaning-based extras: only strong matches, and only a few, so the exact
# word list stays the authority and the extras read as a supplement.
_SEMANTIC_CANDIDATES = 60
_SEMANTIC_MIN_SCORE = 0.80
_SEMANTIC_MAX_EXTRA = 25


@dataclass
class VerseHit:
    verse_key: str
    chapter_id: int
    verse_number: int
    chapter_name_simple: str
    chapter_name_arabic: str
    text_uthmani: str
    translation_text: str | None
    translation_resource: str | None
    translation_language: str | None
    # How the ayah matched: "root" / "form" (morphology), languages in which
    # the words matched ("ar", "ur", ...) and/or "semantic".
    matched_in: list[str] = field(default_factory=list)
    score: float = 0.0
    # 1-based corpus positions of the words matched by morphology.
    matched_words: list[int] = field(default_factory=list)


@dataclass
class VerseSearchResult:
    total: int  # distinct ayat matched by words
    semantic_extra: int  # ayat found only by meaning (hybrid)
    items: list[VerseHit]
    # One entry per query word resolved by morphology: word, kind
    # ("root" | "form"), label (ص ب ر or the lemma), verses, words.
    morphology: list[dict] = field(default_factory=list)
    # Ayah themes (QUL, English) whose title matches the query: theme,
    # chapter_id, chapter_name_simple, chapter_name_arabic, ayah_from, ayah_to.
    themes: list[dict] = field(default_factory=list)


_THEME_LIMIT = 8


def _matching_themes(session: Session, query: str) -> list[dict]:
    """Themes whose English title or keywords contain the query words."""
    if _ARABIC_SCRIPT.search(query) or len(query.strip()) < 3:
        return []
    doc = func.to_tsvector("english", AyahTheme.theme + " " + func.coalesce(AyahTheme.keywords, ""))
    rows = session.execute(
        select(AyahTheme, Chapter)
        .join(Chapter, Chapter.id == AyahTheme.chapter_id)
        .where(doc.op("@@")(func.plainto_tsquery("english", query)))
        .order_by(AyahTheme.chapter_id, AyahTheme.ayah_from, AyahTheme.id)
        .limit(_THEME_LIMIT * 3)
    ).all()
    # The published file repeats some rows; one entry per theme and range.
    out: list[dict] = []
    seen: set[tuple] = set()
    for t, c in rows:
        key = (c.id, t.ayah_from, t.ayah_to, t.theme.casefold())
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "theme": t.theme,
                "chapter_id": c.id,
                "chapter_name_simple": c.name_simple,
                "chapter_name_arabic": c.name_arabic,
                "ayah_from": t.ayah_from,
                "ayah_to": t.ayah_to,
            }
        )
        if len(out) >= _THEME_LIMIT:
            break
    return out


class _Morphology:
    """Lookup tables of the corpus morphology, loaded once per process.

    Keys are normalised like query words (text_normalize.normalize_arabic),
    so a word typed on an Urdu keyboard or without hamza still resolves.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.loaded = False
        self.roots: dict[str, list[int]] = {}
        self.lemmas: dict[str, list[int]] = {}
        self.stems: dict[str, list[int]] = {}
        self.form_lemmas: dict[str, set[int]] = {}
        self.form_stems: dict[str, set[int]] = {}
        self.labels: dict[tuple[str, int], str] = {}

    def load(self, session: Session) -> None:
        if self.loaded:
            return
        with self._lock:
            if self.loaded:
                return
            for rid, letters, spaced in session.execute(
                select(Root.id, Root.letters, Root.letters_spaced)
            ):
                self.roots.setdefault(normalize_arabic(letters), []).append(rid)
                self.labels[("root", rid)] = spaced
            for lid, text_, clean in session.execute(select(Lemma.id, Lemma.text, Lemma.text_clean)):
                for key in {normalize_arabic(text_), normalize_arabic(clean)}:
                    self.lemmas.setdefault(key, []).append(lid)
                self.labels[("lemma", lid)] = text_
            for sid, text_, clean in session.execute(select(Stem.id, Stem.text, Stem.text_clean)):
                for key in {normalize_arabic(text_), normalize_arabic(clean)}:
                    self.stems.setdefault(key, []).append(sid)
                self.labels[("stem", sid)] = text_
            for form, lemma_id, stem_id in session.execute(
                select(Word.text_normalized, Word.lemma_id, Word.stem_id)
            ):
                if lemma_id is not None:
                    self.form_lemmas.setdefault(form, set()).add(lemma_id)
                if stem_id is not None:
                    self.form_stems.setdefault(form, set()).add(stem_id)
            self.loaded = True

    def resolve(self, raw: str) -> dict | None:
        """What one query word names: a root, else a lemma, else a stem."""
        tok = normalize_arabic(raw).strip(".,!?؟،؛:\"'()[]")
        if len(tok) < 3:
            return None  # particles and pronouns: the keyword stage has them
        # Dictionary forms are tried as typed, without the article (الصلاة ->
        # صلاة) and as the light stem (الصابرين -> صابر).
        forms = [tok]
        for prefix in _ARTICLE_PREFIXES:
            if tok.startswith(prefix) and len(tok) - len(prefix) >= 3:
                forms.append(tok[len(prefix):])
                break
        stem = arabic_light_stem(tok)
        if stem not in forms and len(stem) >= 3:
            forms.append(stem)
        if tok in self.roots and len(tok) <= 4:
            ids = self.roots[tok]
            return {"word": raw, "kind": "root", "column": "root_id", "ids": ids, "label": self.labels[("root", ids[0])]}
        # A dictionary form (typed as such, or reached by the light stem:
        # الصابرين -> صابر, الصلاة -> صلاة) expands to its whole lemma. An
        # inflected form (قالوا, السماوات) expands only to its stem, i.e. the
        # same word with other attached particles, which is what someone
        # typing that form means. Only the whole token is matched against
        # word forms: a bare stem would hit unrelated inflections (الربا ->
        # ربا -> رَبًّا).
        for f in forms:
            ids = self.lemmas.get(f)
            if ids:
                return {"word": raw, "kind": "form", "column": "lemma_id", "ids": ids, "label": self.labels[("lemma", ids[0])]}
        ids = sorted(self.form_stems.get(tok, ()))
        if ids:
            return {"word": raw, "kind": "form", "column": "stem_id", "ids": ids, "label": self.labels[("stem", ids[0])]}
        for f in forms:
            ids = self.stems.get(f)
            if ids:
                return {"word": raw, "kind": "form", "column": "stem_id", "ids": ids, "label": self.labels[("stem", ids[0])]}
        ids = sorted(self.form_lemmas.get(tok, ()))
        if ids:
            return {"word": raw, "kind": "form", "column": "lemma_id", "ids": ids, "label": self.labels[("lemma", ids[0])]}
        return None


_MORPHOLOGY = _Morphology()


def _morphology_hits(session: Session, terms: list[dict]) -> dict[str, list[int]]:
    """Ayat containing a word for every term, with the matched positions."""
    per_term: list[dict[str, list[int]]] = []
    for term in terms:
        column = getattr(Word, term["column"])
        rows = session.execute(
            select(Verse.verse_key, Word.position)
            .join(Verse, Verse.id == Word.verse_id)
            .where(column.in_(term["ids"]))
        ).all()
        hits: dict[str, list[int]] = {}
        for verse_key, position in rows:
            hits.setdefault(verse_key, []).append(position)
        term["verses"] = len(hits)
        term["words"] = len(rows)
        per_term.append(hits)
    keys = set.intersection(*(set(h) for h in per_term)) if per_term else set()
    return {k: sorted({p for h in per_term for p in h.get(k, [])}) for k in keys}


def _sort_key(verse_key: str) -> tuple[int, int]:
    a, b = verse_key.split(":")
    return int(a), int(b)


def quran_verse_search(
    session: Session,
    query: str,
    language_codes: list[str],
    *,
    translation_language: str | None,
    order: str = "mushaf",
    offset: int = 0,
    limit: int = 50,
    mode: str = "hybrid",
) -> VerseSearchResult:
    svc = SearchService(session)
    found: dict[str, dict] = {}

    def add(verse_key: str, how: str, score: float) -> None:
        entry = found.setdefault(verse_key, {"matched_in": [], "score": 0.0, "positions": []})
        if how not in entry["matched_in"]:
            entry["matched_in"].append(how)
        entry["score"] = max(entry["score"], score)

    morphology: list[dict] = []
    if mode in ("keyword", "hybrid") and _ARABIC_SCRIPT.search(query):
        _MORPHOLOGY.load(session)
        terms = [t for t in (_MORPHOLOGY.resolve(w) for w in query.split()) if t]
        if terms:
            how = "root" if any(t["kind"] == "root" for t in terms) else "form"
            for vk, positions in _morphology_hits(session, terms).items():
                add(vk, how, 1.0)
                found[vk]["positions"] = positions
            morphology = [
                {k: t[k] for k in ("word", "kind", "label", "verses", "words")} for t in terms
            ]

    if mode in ("keyword", "hybrid"):
        for lang in language_codes:
            doc_types = ["quran_verse"] if lang == "ar" else ["quran_translation"]
            for rank, h in enumerate(
                svc.keyword_search(query, lang, doc_types=doc_types, limit=_KEYWORD_CANDIDATES)
            ):
                vk = h.ref.get("verse_key")
                if vk and h.match in ("fulltext", "partial"):
                    add(vk, lang, 1.0 / (1 + rank))
    word_total = len(found)

    if mode in ("semantic", "hybrid"):
        try:
            sem = svc.semantic_search(
                query, language_codes,
                doc_types=["quran_verse", "quran_translation"],
                limit=_SEMANTIC_CANDIDATES,
            )
        except Exception:  # semantic stage is optional
            session.rollback()
            sem = []
        extras = 0
        for rank, h in enumerate(sem):
            vk = h.ref.get("verse_key")
            if not vk or h.score < _SEMANTIC_MIN_SCORE:
                continue
            if vk not in found:
                if extras >= _SEMANTIC_MAX_EXTRA:
                    continue
                extras += 1
            add(vk, "semantic", 0.5 / (1 + rank))

    keys = list(found)
    if order == "relevance":
        keys.sort(key=lambda k: (-found[k]["score"], _sort_key(k)))
    else:
        # Exact word matches first, in mushaf order; meaning-only after.
        def is_extra(k: str) -> bool:
            return found[k]["matched_in"] == ["semantic"]

        keys.sort(key=lambda k: (is_extra(k), _sort_key(k)))
    page_keys = keys[offset : offset + limit]
    themes = _matching_themes(session, query) if mode in ("keyword", "hybrid") else []
    if not page_keys:
        return VerseSearchResult(
            total=word_total, semantic_extra=len(found) - word_total, items=[],
            morphology=morphology, themes=themes,
        )

    rows = session.execute(
        select(Verse, Chapter)
        .join(Chapter, Chapter.id == Verse.chapter_id)
        .where(Verse.verse_key.in_(page_keys))
    ).all()
    by_key = {v.verse_key: (v, c) for v, c in rows}

    translations: dict[int, tuple[str, str, str]] = {}
    if translation_language and translation_language != "ar":
        resource = session.scalars(
            select(TranslationResource)
            .where(TranslationResource.language_code == translation_language)
            .order_by(TranslationResource.id)
        ).first()
        if resource is not None:
            verse_ids = [v.id for v, _ in rows]
            for vt in session.scalars(
                select(VerseTranslation).where(
                    VerseTranslation.verse_id.in_(verse_ids),
                    VerseTranslation.resource_id == resource.id,
                )
            ):
                translations[vt.verse_id] = (vt.text, resource.name, resource.language_code)

    items: list[VerseHit] = []
    for k in page_keys:
        pair = by_key.get(k)
        if pair is None:
            continue
        v, c = pair
        tr = translations.get(v.id)
        items.append(
            VerseHit(
                verse_key=k,
                chapter_id=c.id,
                verse_number=v.verse_number,
                chapter_name_simple=c.name_simple,
                chapter_name_arabic=c.name_arabic,
                text_uthmani=v.text_uthmani,
                translation_text=tr[0] if tr else None,
                translation_resource=tr[1] if tr else None,
                translation_language=tr[2] if tr else None,
                matched_in=found[k]["matched_in"],
                score=found[k]["score"],
                matched_words=found[k]["positions"],
            )
        )
    return VerseSearchResult(
        total=word_total, semantic_extra=len(found) - word_total, items=items,
        morphology=morphology, themes=themes,
    )
