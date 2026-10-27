"""Search service.

Three-stage retrieval over search.documents:
  1. Ranked full-text search (PostgreSQL tsvector + ts_rank); every word
     must match.
  2. If that yields too few hits, a relaxed keyword stage for questions
     written in natural language: question and filler words are dropped and
     passages are ranked by how many of the remaining key terms they contain.
  3. A spelling fallback matches misspelled words against the index
     vocabulary (pg_trgm) when the word stages find almost nothing.

Hybrid mode adds a semantic stage: the query is embedded with the same
open-source model used to build search.chunks and the nearest passages are
retrieved by cosine distance (pgvector HNSW). Keyword and semantic lists are
fused with reciprocal rank fusion, identical tafsir texts for adjacent ayat
are merged into one hit, and the top candidates are re-ordered by a
cross-encoder reranker. Every hit is still an exact stored passage with its
source; the models only choose and order.

Queries are normalized with the SAME functions used to build the index, so
a query written with or without diacritics matches identically. Every result
carries its citation and canonical pointer, from which the full provenance
chain (raw artifact -> import run -> source) can be resolved.
"""

import hashlib
import logging
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services import embeddings

from app.services.text_normalize import PG_STEMMED, normalize, query_tsquery, term_tsquery, ts_config

# Question and filler words dropped by the relaxed stage, plus words so
# common in the corpus ("Quran", "Allah") that they carry no signal. Lists
# are normalized with the index normalizer so spelling variants line up.
_STOPWORDS_RAW = {
    "ur": """
        میں سے کے کی کا کو نے پر تک اور یا بھی ہی تو کہ جو جس جن جب
        ہے ہیں تھا تھی تھے ہو ہوں ہوتا ہوتی ہوتے ہوا ہوئے گا گی گے
        کیا کیوں کیسے کب کہاں کون کونسا کونسی کتنا کتنی کس کسی
        لیے لئے متعلق بارے بارہ طرح والا والی والے ایک یہ وہ ان اس
        ہم آپ مجھے ہمیں بتائیں بتایئے بتاؤ چاہیے چاہئے کرنا کرنی کریں
        کرتے کرتا کرتی کر رہا رہی رہے سکتا سکتی سکتے دیں دے
        قرآن مجید کریم حدیث تفسیر شریف پاک اللہ تعالی
    """,
    "ar": """
        في من الى إلى على عن مع ما ماذا لماذا كيف هل متى اين أين
        الذي التي الذين هو هي هم ان أن إن او أو و ثم قد لا لم لن
        كان كانت يكون عند بعد قبل كل بين حول هذا هذه ذلك تلك
        القران القرآن الكريم الحديث التفسير الله تعالى
    """,
    "tr": """
        ve veya ile için gibi de da mi mı mu mü ne neden nasıl hangi kim nerede
        bir bu şu o bu ben sen biz siz onlar hakkında üzerine göre ise ki
        var yok olan olarak dir dır dur dür midir mıdır nedir
        kuran kur'an kerim hadis tefsir allah
    """,
    "en": """
        a an the of in on at to for from by with about into is are was
        were be been being do does did what which who whom whose why
        how when where can could should would will shall may might must
        i me my we our you your he she it they them his her its their
        this that these those and or not no as if so than then there
        tell please regarding concerning according say says said
        quran holy hadith tafsir allah
    """,
}
_STOPWORDS = {
    lang: {normalize(w, lang) for w in words.split()} for lang, words in _STOPWORDS_RAW.items()
}

log = logging.getLogger(__name__)

# Spelling fallback runs only when fewer hits than this were found, and
# offers at most this many index words per query word.
_FUZZY_BELOW = 5
_SPELLING_OPTIONS = 3

# Semantic stage: candidate chunks fetched per query and HNSW search width.
# e5 vectors sit close together (cosine 0.80 to 0.88 across a result list),
# so the index needs a wide search: with m=32/ef_construction=256, width 400
# measured recall@20 0.985 at 17 ms; 200 gave 0.885.
_SEMANTIC_CHUNKS = 120
_HNSW_EF_SEARCH = 400
# Reciprocal rank fusion constant (Cormack et al.).
_RRF_K = 60
# How many fused candidates the reranker re-orders: RERANK_CANDIDATES
# (0 turns the reranker off, for servers without a GPU).
# Keyword hits longer than this get a passage-sized snippet.
_SNIPPET_CHARS = 1200

# Relaxed matching caps the number of terms it OR-s together.
_MAX_RELAXED_TERMS = 8

# ts_rank normalization flag 1: divide by 1 + log(length), so a focused
# passage outranks a very long one that merely mentions every word.
_RANK_NORM = 1


def _key_terms(normalized: str, language_code: str) -> list[str]:
    """Content words of a query, in order, without stopwords or repeats."""
    stop = _STOPWORDS.get(language_code, set())
    terms: list[str] = []
    for word in normalized.split():
        word = word.strip(".,!?؟۔،:;\"'()[]")
        if len(word) > 1 and word not in stop and word not in terms:
            terms.append(word)
    return terms[:_MAX_RELAXED_TERMS]


@dataclass
class SearchHit:
    doc_type: str
    language_code: str
    collection_key: str
    citation: str
    source_row_id: int
    text_display: str
    score: float
    match: str  # "fulltext" | "partial" | "fuzzy" | "semantic"
    ref: dict = field(default_factory=dict)
    # Passage-sized excerpt of text_display that best matches the query,
    # with its character span inside text_display (for highlighting).
    snippet: str | None = None
    snippet_start: int | None = None
    snippet_end: int | None = None

    @property
    def key(self) -> tuple[str, int, str]:
        return (self.doc_type, self.source_row_id, self.language_code)


class SearchService:
    def __init__(self, session: Session):
        self.session = session

    def search(
        self,
        query: str,
        language_codes: str | list[str],
        *,
        doc_types: list[str] | None = None,
        collection_keys: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
        mode: str = "hybrid",
        rerank: bool = True,
    ) -> list[SearchHit]:
        """Keyword, semantic or hybrid search over one or more content
        languages. Hybrid falls back to keyword results when the semantic
        stage is unavailable (no model, no embeddings yet).

        Paging is done over the fused ranking: `offset + limit` candidates
        are gathered and the page is sliced from them.
        """
        langs = [language_codes] if isinstance(language_codes, str) else list(language_codes)
        want = offset + limit
        keyword: list[SearchHit] = []
        semantic: list[SearchHit] = []
        if mode in ("keyword", "hybrid"):
            per_lang = [
                self.keyword_search(
                    query, lang, doc_types=doc_types,
                    collection_keys=collection_keys, limit=want,
                )
                for lang in langs
            ]
            keyword = self._interleave(per_lang)
        if mode in ("semantic", "hybrid"):
            try:
                semantic = self.semantic_search(
                    query, langs, doc_types=doc_types,
                    collection_keys=collection_keys, limit=want,
                )
            except embeddings.SemanticUnavailable as exc:
                log.warning("semantic search unavailable: %s", exc)
            except Exception:  # never let the semantic stage break search
                log.exception("semantic search failed")
                self.session.rollback()

        if not semantic:
            return self._merge_duplicates(keyword)[offset:want]
        fused = self._fuse(keyword, semantic) if keyword else semantic
        fused = self._merge_duplicates(fused)
        if rerank and len(fused) > 1:
            fused = self._rerank(query, fused)
        return fused[offset:want]

    @staticmethod
    def _interleave(lists: list[list[SearchHit]]) -> list[SearchHit]:
        """Round-robin merge of per-language keyword rankings (scores from
        different languages are not comparable, ranks are)."""
        out: list[SearchHit] = []
        for i in range(max((len(x) for x in lists), default=0)):
            for lst in lists:
                if i < len(lst):
                    out.append(lst[i])
        return out

    def match_counts(self, query: str, language_codes: list[str]) -> dict[str, int]:
        """Exact-match counts per result group for the tabs: distinct ayat,
        distinct hadith, distinct tafsir passages, across the languages."""
        clauses: list[str] = []
        params: dict = {}
        for i, lang in enumerate(language_codes):
            tsq, value = self._tsquery(query, lang)
            if tsq is None:
                continue
            tsq = tsq.replace(":q", f":q{i}")
            params[f"q{i}"] = value
            params[f"lang{i}"] = lang
            clauses.append(f"(language_code = :lang{i} AND tsv @@ {tsq})")
        if not clauses:
            return {"quran": 0, "hadith": 0, "tafsir": 0}
        rows = self.session.execute(
            text(
                f"""
                SELECT CASE WHEN doc_type IN ('quran_verse','quran_translation') THEN 'quran'
                            WHEN doc_type = 'hadith_text' THEN 'hadith'
                            ELSE 'tafsir' END AS grp,
                       COUNT(DISTINCT CASE
                            WHEN doc_type IN ('quran_verse','quran_translation') THEN ref->>'verse_key'
                            WHEN doc_type = 'hadith_text' THEN collection_key || ':' || (ref->>'hadith_number')
                            ELSE language_code || ':' || md5(text_display) END) AS n
                FROM search.documents
                WHERE {" OR ".join(clauses)}
                GROUP BY grp
                """
            ),
            params,
        )
        counts = {"quran": 0, "hadith": 0, "tafsir": 0}
        for grp, n in rows:
            counts[grp] = int(n)
        return counts

    def _tsquery(self, query: str, language_code: str) -> tuple[str | None, str | None]:
        """(SQL fragment using :q, parameter value) for the language."""
        normalized = normalize(query, language_code)
        if not normalized:
            return None, None
        config = ts_config(language_code)
        if language_code in PG_STEMMED:
            return f"websearch_to_tsquery('{config}', :q)", normalized
        value = query_tsquery(query, language_code)
        return (f"to_tsquery('{config}', :q)", value) if value else (None, None)

    # -- semantic stage -----------------------------------------------------

    def semantic_search(
        self,
        query: str,
        language_codes: str | list[str],
        *,
        doc_types: list[str] | None = None,
        collection_keys: list[str] | None = None,
        limit: int = 20,
    ) -> list[SearchHit]:
        """Nearest stored passages by meaning; best chunk per document."""
        langs = [language_codes] if isinstance(language_codes, str) else list(language_codes)
        qvec = embeddings.embed_query(query)
        filters = ["c.language_code = ANY(:langs)"]
        params: dict = {
            "langs": langs,
            "qvec": "[" + ",".join(f"{x:.6f}" for x in qvec.tolist()) + "]",
            "k": max(_SEMANTIC_CHUNKS, limit * 4),
        }
        if doc_types:
            filters.append("c.doc_type = ANY(:doc_types)")
            params["doc_types"] = doc_types
        if collection_keys:
            filters.append("c.collection_key = ANY(:colls)")
            params["colls"] = collection_keys
        where = " AND ".join(filters)
        # Iterative scan keeps recall when filters discard most neighbours.
        self.session.execute(text(f"SET LOCAL hnsw.ef_search = {_HNSW_EF_SEARCH}"))
        self.session.execute(text("SET LOCAL hnsw.iterative_scan = 'relaxed_order'"))
        rows = self.session.execute(
            text(
                f"""
                SELECT d.doc_type, d.language_code, d.collection_key, d.citation,
                       d.source_row_id, d.text_display, d.ref,
                       c.text AS chunk_text, c.char_start, c.char_end,
                       1 - (c.embedding <=> CAST(:qvec AS vector)) AS score
                FROM search.chunks c
                JOIN search.documents d ON d.id = c.document_id
                WHERE {where}
                ORDER BY c.embedding <=> CAST(:qvec AS vector)
                LIMIT :k
                """
            ),
            params,
        )
        hits: list[SearchHit] = []
        seen: set[tuple] = set()
        for r in rows:
            h = self._to_hit(r, "semantic")
            if h.key in seen:
                continue  # a better chunk of this document was already taken
            seen.add(h.key)
            h.snippet = r.chunk_text
            h.snippet_start, h.snippet_end = r.char_start, r.char_end
            hits.append(h)
            if len(hits) >= limit * 2:
                break
        return hits

    # -- fusion, grouping, reranking ---------------------------------------

    @staticmethod
    def _fuse(keyword: list[SearchHit], semantic: list[SearchHit]) -> list[SearchHit]:
        """Reciprocal rank fusion of the two ranked lists."""
        scores: dict[tuple, float] = {}
        best: dict[tuple, SearchHit] = {}
        for ranked in (keyword, semantic):
            for rank, h in enumerate(ranked):
                scores[h.key] = scores.get(h.key, 0.0) + 1.0 / (_RRF_K + rank + 1)
                prev = best.get(h.key)
                if prev is None:
                    best[h.key] = h
                elif prev.snippet is None and h.snippet is not None:
                    # Keep the keyword label, borrow the semantic passage.
                    prev.snippet, prev.snippet_start, prev.snippet_end = (
                        h.snippet, h.snippet_start, h.snippet_end,
                    )
        out = sorted(best.values(), key=lambda h: -scores[h.key])
        for h in out:
            h.score = scores[h.key]
        return out

    @staticmethod
    def _merge_duplicates(hits: list[SearchHit]) -> list[SearchHit]:
        """Ibn Kathir repeats one commentary for each ayah of a group; show it
        once, citing the range (ref.verse_keys lists every ayah)."""
        groups: dict[tuple, SearchHit] = {}
        order: list[tuple] = []
        for h in hits:
            if h.doc_type != "tafsir_entry":
                key = ("solo", h.key)
            else:
                digest = hashlib.md5(h.text_display.encode("utf-8")).hexdigest()
                key = ("tafsir", h.language_code, h.collection_key, digest)
            if key in groups:
                g = groups[key]
                vk = h.ref.get("verse_key")
                if vk and vk not in g.ref.setdefault("verse_keys", [g.ref.get("verse_key")]):
                    g.ref["verse_keys"].append(vk)
                continue
            groups[key] = h
            order.append(key)
        out = [groups[k] for k in order]
        for h in out:
            keys = h.ref.get("verse_keys")
            if keys and len(keys) > 1:
                keys.sort(key=lambda k: tuple(int(x) for x in k.split(":")))
                first, last = keys[0], keys[-1]
                last_part = last.split(":")[1] if first.split(":")[0] == last.split(":")[0] else last
                h.citation = h.citation.replace(h.ref["verse_key"], f"{first}-{last_part}")
        return out

    def _rerank(self, query: str, hits: list[SearchHit]) -> list[SearchHit]:
        depth = get_settings().RERANK_CANDIDATES
        if depth <= 0:
            return hits
        top, rest = hits[:depth], hits[depth:]
        passages = [self._passage_for(h) for h in top]
        try:
            scores = embeddings.rerank(query, passages)
        except embeddings.SemanticUnavailable:
            return hits
        for h, sc in zip(top, scores):
            h.score = sc
        top.sort(key=lambda h: -h.score)
        return top + rest

    @staticmethod
    def _passage_for(hit: SearchHit) -> str:
        if hit.snippet:
            return hit.snippet
        from app.services.embedding_indexer import clean_for_embedding

        return clean_for_embedding(hit.text_display[:_SNIPPET_CHARS])

    # -- keyword stages -------------------------------------------------------

    def keyword_search(
        self,
        query: str,
        language_code: str,
        *,
        doc_types: list[str] | None = None,
        collection_keys: list[str] | None = None,
        limit: int = 20,
        fuzzy_threshold: float = 0.4,
    ) -> list[SearchHit]:
        normalized = normalize(query, language_code)
        if not normalized:
            return []
        config = ts_config(language_code)
        # English and Turkish use PostgreSQL's parser and stemmer; Arabic and
        # Urdu use the Python expansion (spelling variants + light stems).
        if language_code in PG_STEMMED:
            tsq = f"websearch_to_tsquery('{config}', :q)"
            tsq_param = normalized
        else:
            tsq = f"to_tsquery('{config}', :q)"
            tsq_param = query_tsquery(query, language_code)
            if not tsq_param:
                return []

        filters = ["language_code = :lang"]
        params: dict = {"lang": language_code, "q": tsq_param, "limit": limit}
        if doc_types:
            filters.append("doc_type = ANY(:doc_types)")
            params["doc_types"] = doc_types
        if collection_keys:
            filters.append("collection_key = ANY(:colls)")
            params["colls"] = collection_keys
        where = " AND ".join(filters)

        hits = self._fulltext(where, params, tsq)
        seen = {(h.doc_type, h.source_row_id) for h in hits}

        # Only worth running when dropping filler words changed the query.
        terms = _key_terms(normalized, language_code)
        if len(hits) < limit and terms and terms != normalized.split():
            for h in self._relaxed(where, params, language_code, terms):
                if (h.doc_type, h.source_row_id) not in seen:
                    seen.add((h.doc_type, h.source_row_id))
                    hits.append(h)
                    if len(hits) >= limit:
                        break

        # Spelling help only when the word stages found almost nothing.
        if len(hits) < _FUZZY_BELOW:
            for h in self._spelling(where, params, language_code, normalized, fuzzy_threshold):
                if (h.doc_type, h.source_row_id) not in seen:
                    hits.append(h)
                    if len(hits) >= limit:
                        break
        return hits[:limit]

    # -- stages -----------------------------------------------------------

    def _fulltext(self, where: str, params: dict, tsq: str) -> list[SearchHit]:
        sql = text(
            f"""
            SELECT doc_type, language_code, collection_key, citation,
                   source_row_id, text_display, ref,
                   ts_rank(tsv, {tsq}, {_RANK_NORM}) AS score
            FROM search.documents
            WHERE {where}
              AND tsv @@ {tsq}
            ORDER BY score DESC
            LIMIT :limit
            """
        )
        return [self._to_hit(r, "fulltext") for r in self.session.execute(sql, params)]

    def _relaxed(
        self, where: str, params: dict, language_code: str, terms: list[str]
    ) -> list[SearchHit]:
        """Passages containing at least half of the key terms, most first."""
        config = ts_config(language_code)
        if language_code in PG_STEMMED:
            term_params = {f"t{i}": t for i, t in enumerate(terms)}
            tq = [f"plainto_tsquery('{config}', :t{i})" for i in range(len(terms))]
        else:
            term_params = {f"t{i}": term_tsquery(t, language_code) or "''" for i, t in enumerate(terms)}
            tq = [f"to_tsquery('{config}', :t{i})" for i in range(len(terms))]
        matched = " + ".join(f"(tsv @@ {q})::int" for q in tq)
        any_term = " || ".join(tq)
        sql = text(
            f"""
            SELECT * FROM (
                SELECT doc_type, language_code, collection_key, citation,
                       source_row_id, text_display, ref,
                       ({matched}) AS matched,
                       ts_rank(tsv, {any_term}, {_RANK_NORM}) AS score
                FROM search.documents
                WHERE {where}
                  AND tsv @@ ({any_term})
            ) candidates
            WHERE matched >= :min_matched
            ORDER BY matched DESC, score DESC
            LIMIT :limit
            """
        )
        min_matched = max(1, (len(terms) + 1) // 2)
        rows = self.session.execute(sql, {**params, **term_params, "min_matched": min_matched})
        return [self._to_hit(r, "partial") for r in rows]

    def _spelling(
        self, where: str, params: dict, language_code: str, normalized: str, threshold: float
    ) -> list[SearchHit]:
        """Hits for the closest-spelled index words of a short query.

        Misspellings are matched against search.vocabulary (every lexeme of
        the keyword index, trigram-indexed), not against document texts, so
        this costs milliseconds. Each query word becomes an OR of its closest
        lexemes and the words are AND-ed, as in the strict stage.
        """
        words = _key_terms(normalized, language_code)
        if not 1 <= len(words) <= 3:
            return []
        rows = self.session.execute(
            text(
                """
                SELECT q.word, v.lexeme
                FROM unnest(CAST(:words AS text[])) AS q(word)
                JOIN search.vocabulary v
                  ON v.language_code = :lang
                 AND v.lexeme % q.word
                 AND similarity(v.lexeme, q.word) >= :thresh
                ORDER BY q.word, similarity(v.lexeme, q.word) DESC, v.ndoc DESC
                """
            ),
            {"words": words, "lang": language_code, "thresh": threshold},
        )
        options: dict[str, list[str]] = {}
        for word, lexeme in rows:
            found = options.setdefault(word, [])
            if len(found) < _SPELLING_OPTIONS and lexeme not in found:
                found.append(lexeme)
        if len(options) < len(words):
            return []  # a word with nothing close: no sensible suggestion

        def quoted(lexeme: str) -> str:
            return "'" + lexeme.replace("'", "''") + "'"

        tsq = " & ".join("(" + " | ".join(quoted(l) for l in options[w]) + ")" for w in words)
        # The lexemes are final index tokens, so 'simple' keeps them as they are.
        hits = self._fulltext(where, {**params, "q": tsq}, "to_tsquery('simple', :q)")
        for h in hits:
            h.match = "fuzzy"
        return hits

    @staticmethod
    def _to_hit(row, match: str) -> SearchHit:
        return SearchHit(
            doc_type=row.doc_type,
            language_code=row.language_code,
            collection_key=row.collection_key,
            citation=row.citation,
            source_row_id=row.source_row_id,
            text_display=row.text_display,
            score=float(row.score),
            match=match,
            ref=row.ref or {},
        )
