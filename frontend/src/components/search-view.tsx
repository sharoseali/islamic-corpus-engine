"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { SearchField } from "./search-field";
import { ElaajLoader } from "./elaaj-loader";
import { useI18n } from "./providers";
import { api } from "@/lib/api";
import { isRtl, type Locale } from "@/i18n/config";
import { collectionName, surahOf, verseAnchor } from "@/lib/localize";
import { highlightLang, highlightText, highlightPositions } from "@/lib/highlight";
import type { Chapter, QuranSearchResponse, SearchHit, SearchResponse, VerseHit } from "@/lib/types";
import { Container } from "./ui";
import { CopyButton } from "./copy-button";

type Scope = "all" | "quran" | "hadith" | "tafsir";
type Dict = ReturnType<typeof useI18n>["dict"];

const SCOPES: Scope[] = ["all", "quran", "hadith", "tafsir"];
const TYPES: Record<Scope, string | undefined> = {
  all: undefined,
  quran: "quran_verse,quran_translation",
  hadith: "hadith_text",
  tafsir: "tafsir_entry",
};
const PAGE = 20;
const QURAN_PAGE = 50;
// Collections whose every hadith is graded sahih by the compiler.
const SAHIH_COLLECTIONS = new Set(["bukhari", "muslim"]);

const AUTO_LABEL: Record<Locale, string> = { en: "Auto", ur: "خودکار", ar: "تلقائي", tr: "Otomatik" };
const LANG_CHIPS = ["ar", "ur", "en", "tr"];

const stripHtml = (s: string) => s.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
const hasArabicScript = (s: string) => /[؀-ۿ]/.test(s);

// Which content languages to search: the query's script decides between
// Arabic-script and Latin content; the UI language adds its own content.
function targetLangs(query: string, mode: string, locale: Locale): string[] {
  if (mode !== "auto") return [mode];
  if (hasArabicScript(query)) return locale === "ur" ? ["ar", "ur"] : ["ar"];
  if (locale === "tr") return ["tr", "en"];
  return ["en"];
}

function isScope(v: string | null): v is Scope {
  return !!v && (SCOPES as string[]).includes(v);
}

export function SearchView() {
  const { locale, dict } = useI18n();
  const router = useRouter();
  const params = useSearchParams();
  const initialQ = params.get("q") ?? "";
  const initialScope: Scope = isScope(params.get("scope")) ? (params.get("scope") as Scope) : "all";

  const [q, setQ] = useState(initialQ);
  const [scope, setScope] = useState<Scope>(initialScope);
  const [langMode, setLangMode] = useState("auto");
  const [order, setOrder] = useState<"mushaf" | "relevance">("mushaf");
  const [counts, setCounts] = useState<SearchResponse["counts"] | null>(null);
  const [hits, setHits] = useState<SearchHit[] | null>(null);
  const [verses, setVerses] = useState<QuranSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [exhausted, setExhausted] = useState(false);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [activeQuery, setActiveQuery] = useState(initialQ);
  const requestId = useRef(0);

  useEffect(() => {
    api.listChapters().then(setChapters).catch(() => undefined);
  }, []);
  const chapterById = useMemo(() => new Map(chapters.map((c) => [c.id, c])), [chapters]);

  const translationLang = locale === "ar" ? undefined : locale;

  const run = useCallback(
    async (query: string, sc: Scope, mode: string, ord: "mushaf" | "relevance", offset: number) => {
      const trimmed = query.trim();
      const id = ++requestId.current;
      if (!trimmed) {
        setHits(null);
        setVerses(null);
        setCounts(null);
        return;
      }
      offset === 0 ? setLoading(true) : setLoadingMore(true);
      const langs = targetLangs(trimmed, mode, locale);
      try {
        if (sc === "quran") {
          const [res, countRes] = await Promise.all([
            api.searchQuran(trimmed, langs, { translation: translationLang, order: ord, limit: QURAN_PAGE, offset }),
            offset === 0
              ? api.search(trimmed, langs, { limit: 1, mode: "keyword", rerank: false, withCounts: true }).catch(() => null)
              : Promise.resolve(null),
          ]);
          if (id !== requestId.current) return;
          setVerses((prev) => (offset === 0 || !prev ? res : { ...res, items: [...prev.items, ...res.items] }));
          setExhausted(res.items.length < QURAN_PAGE);
          if (countRes) setCounts({ ...countRes.counts, quran: res.total });
          setHits(null);
        } else {
          const res = await api.search(trimmed, langs, {
            types: TYPES[sc],
            limit: PAGE,
            offset,
            withCounts: offset === 0,
          });
          if (id !== requestId.current) return;
          setHits((prev) => (offset === 0 || !prev ? res.hits : [...prev, ...res.hits]));
          setExhausted(res.hits.length < PAGE);
          if (offset === 0 && res.counts) setCounts(res.counts);
          setVerses(null);
        }
        setActiveQuery(trimmed);
      } catch {
        if (id !== requestId.current) return;
        if (offset === 0) {
          setHits([]);
          setVerses(null);
        }
      } finally {
        if (id === requestId.current) {
          setLoading(false);
          setLoadingMore(false);
        }
      }
    },
    [locale, translationLang],
  );

  useEffect(() => {
    if (initialQ) run(initialQ, initialScope, "auto", "mushaf", 0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQ]);

  const syncUrl = (query: string, sc: Scope) => {
    const sp = new URLSearchParams({ q: query.trim() });
    if (sc !== "all") sp.set("scope", sc);
    router.replace(`/${locale}/search?${sp.toString()}`);
  };

  const submit = () => {
    syncUrl(q, scope);
    run(q, scope, langMode, order, 0);
  };
  const changeScope = (sc: Scope) => {
    setScope(sc);
    syncUrl(q, sc);
    run(q, sc, langMode, order, 0);
  };
  const changeLang = (mode: string) => {
    setLangMode(mode);
    run(q, scope, mode, order, 0);
  };
  const changeOrder = (ord: "mushaf" | "relevance") => {
    setOrder(ord);
    run(q, scope, langMode, ord, 0);
  };
  const loadMore = () => {
    const offset = scope === "quran" ? (verses?.items.length ?? 0) : (hits?.length ?? 0);
    run(q, scope, langMode, order, offset);
  };

  const countFor = (sc: Scope): number | null => {
    if (!counts || sc === "all") return null;
    const n = counts[sc];
    return typeof n === "number" ? n : null;
  };

  const hasResults = scope === "quran" ? (verses?.items.length ?? 0) > 0 : (hits?.length ?? 0) > 0;
  const searched = scope === "quran" ? verses !== null : hits !== null;

  return (
    <Container narrow style={{ padding: "36px 20px 60px" }}>
      <SearchField value={q} onChange={setQ} onSubmit={submit} variant="page" autoFocus />

      {/* Scope tabs with exact-match counts */}
      <div className="scope-tabs" role="tablist">
        {SCOPES.map((sc) => {
          const n = countFor(sc);
          return (
            <button
              key={sc}
              role="tab"
              aria-selected={scope === sc}
              onClick={() => changeScope(sc)}
              className={`scope-tab${scope === sc ? " is-active" : ""}`}
            >
              {sc === "all" ? dict.search.all : dict.search[sc]}
              {n !== null && <span className="scope-count">{n.toLocaleString()}</span>}
            </button>
          );
        })}
        <div className="lang-chips">
          <button onClick={() => changeLang("auto")} className={`chip${langMode === "auto" ? " is-active" : ""}`}>
            {AUTO_LABEL[locale]}
          </button>
          {LANG_CHIPS.map((l) => (
            <button key={l} onClick={() => changeLang(l)} className={`chip${langMode === l ? " is-active" : ""}`}>
              {l.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {loading && <ElaajLoader label={dict.search.searching} />}

      {!loading && !searched && (
        <p style={{ color: "var(--text-faint)", textAlign: "center", padding: 40 }}>{dict.search.prompt}</p>
      )}

      {!loading && searched && !hasResults && (
        <p style={{ color: "var(--text-muted)", textAlign: "center", padding: 40 }}>{dict.search.no_results}</p>
      )}

      {!loading && scope === "quran" && verses && verses.items.length > 0 && (
        <QuranResults
          data={verses}
          query={activeQuery}
          order={order}
          onOrder={changeOrder}
          dict={dict}
          locale={locale}
        />
      )}

      {!loading && scope !== "quran" && hits && hits.length > 0 && (
        <div className="results-list fade-in">
          <p className="results-meta">
            {dict.search.results_for} “{activeQuery}”
          </p>
          {hits.map((h, i) => (
            <ResultCard
              key={`${h.doc_type}-${h.source_row_id}-${h.language_code}-${i}`}
              hit={h}
              query={activeQuery}
              dict={dict}
              locale={locale}
              chapter={chapterById.get(Number(String(h.ref?.verse_key ?? "").split(":")[0]))}
            />
          ))}
        </div>
      )}

      {!loading && searched && hasResults && (
        <div className="load-more">
          {exhausted ? (
            <span className="load-more__end">{dict.results.no_more}</span>
          ) : (
            <button className="load-more__btn" onClick={loadMore} disabled={loadingMore}>
              {loadingMore ? dict.common.loading : dict.results.load_more}
            </button>
          )}
        </div>
      )}
    </Container>
  );
}

// ---------------------------------------------------------------- Quran ---

function QuranResults({
  data,
  query,
  order,
  onOrder,
  dict,
  locale,
}: {
  data: QuranSearchResponse;
  query: string;
  order: "mushaf" | "relevance";
  onOrder: (o: "mushaf" | "relevance") => void;
  dict: Dict;
  locale: Locale;
}) {
  // Group consecutive ayat of one surah under a heading (mushaf order
  // gives contiguous groups; relevance order shows the surah on each ayah).
  // In mushaf order the server lists exact word matches first and the
  // meaning-only extras after them; a divider separates the two.
  const groups: { chapter: VerseHit; items: VerseHit[]; extra: boolean }[] = [];
  for (const v of data.items) {
    const extra = v.matched_in.length === 1 && v.matched_in[0] === "semantic";
    const last = groups[groups.length - 1];
    if (order === "mushaf" && last && last.chapter.chapter_id === v.chapter_id && last.extra === extra) last.items.push(v);
    else groups.push({ chapter: v, items: [v], extra });
  }
  const firstExtra = order === "mushaf" ? groups.findIndex((g) => g.extra) : -1;
  const arLang = highlightLang(query, "ar");
  return (
    <div className="fade-in">
      <div className="results-bar">
        <span className="results-meta">
          <strong>{data.total.toLocaleString()}</strong> {dict.results.ayat_count} · {dict.results.exact_word_matches}
          {data.semantic_extra > 0 && (
            <>
              {" "}
              · +{data.semantic_extra} {dict.results.by_meaning_extra}
            </>
          )}
        </span>
        <span className="order-toggle">
          <button className={`chip${order === "mushaf" ? " is-active" : ""}`} onClick={() => onOrder("mushaf")}>
            {dict.results.order_mushaf}
          </button>
          <button className={`chip${order === "relevance" ? " is-active" : ""}`} onClick={() => onOrder("relevance")}>
            {dict.results.order_relevance}
          </button>
        </span>
      </div>

      {data.morphology && data.morphology.length > 0 && (
        <div className="morph-chips">
          {data.morphology.map((m) => (
            <span key={m.word} className="morph-chip">
              <span className="morph-chip__kind">{m.kind === "root" ? dict.results.root : dict.results.word_form}</span>
              <span className="morph-chip__label font-arabic" dir="rtl" lang="ar">
                {m.label}
              </span>
              <span className="morph-chip__meta">
                {m.words.toLocaleString()} {dict.results.words_count} · {m.verses.toLocaleString()} {dict.results.ayat_count}
              </span>
            </span>
          ))}
        </div>
      )}

      {data.themes && data.themes.length > 0 && (
        <div className="theme-list">
          <span className="theme-list__title">{dict.results.topics}</span>
          {data.themes.map((t) => (
            <Link
              key={`${t.chapter_id}:${t.ayah_from}`}
              href={`/${locale}/quran/${t.chapter_id}#${verseAnchor(`${t.chapter_id}:${t.ayah_from}`)}`}
              className="theme-chip"
            >
              <span className="theme-chip__ref">
                {t.chapter_name_simple} {t.chapter_id}:{t.ayah_from}
                {t.ayah_to > t.ayah_from ? `-${t.ayah_to}` : ""}
              </span>
              <span className="theme-chip__text">{t.theme}</span>
            </Link>
          ))}
        </div>
      )}

      {groups.map((g, gi) => (
        <section key={`${g.chapter.chapter_id}-${g.items[0].verse_key}`} className="surah-group">
          {gi === firstExtra && (
            <h2 className="extras-divider">
              <span>{dict.results.by_meaning_extra}</span>
            </h2>
          )}
          {order === "mushaf" && (
            <h3 className="surah-group__title">
              <span className="surah-group__num">{g.chapter.chapter_id}</span>
              <span className="font-arabic surah-group__ar" dir="rtl">
                {g.chapter.chapter_name_arabic}
              </span>
              {locale !== "ar" && <span className="surah-group__en">{g.chapter.chapter_name_simple}</span>}
              <span className="surah-group__count">{g.items.length}</span>
            </h3>
          )}
          {g.items.map((v) => {
            const trLang = v.translation_language ? highlightLang(query, v.translation_language) : null;
            return (
              <article key={v.verse_key} className="verse-row">
                <div className="verse-row__head">
                  <Link href={`/${locale}/quran/${v.chapter_id}#${verseAnchor(v.verse_key)}`} className="verse-key">
                    {order === "relevance" ? `${v.chapter_name_arabic} · ` : ""}
                    {v.verse_key}
                  </Link>
                  <span className="verse-row__flags">
                    {v.matched_in.includes("root") && <span className="flag flag--root">{dict.results.by_root}</span>}
                    {v.matched_in.includes("form") && <span className="flag flag--root">{dict.results.by_word_form}</span>}
                    {v.matched_in.includes("ar") && <span className="flag">{dict.results.matched_in_arabic}</span>}
                    {v.matched_in.some((m) => !["ar", "semantic", "root", "form"].includes(m)) && (
                      <span className="flag">{dict.results.matched_in_translation}</span>
                    )}
                    {v.matched_in.length === 1 && v.matched_in[0] === "semantic" && (
                      <span className="flag flag--gold">{dict.results.by_meaning}</span>
                    )}
                  </span>
                  <CopyButton
                    text={v.text_uthmani + (v.translation_text ? "\n" + stripHtml(v.translation_text) : "")}
                    reference={`${dict.search.quran} ${v.verse_key}`}
                    font="arabic"
                    dir="rtl"
                    title={v.verse_key}
                  />
                </div>
                <p className="verse-row__ar font-arabic" dir="rtl" lang="ar">
                  {v.matched_words && v.matched_words.length > 0
                    ? highlightPositions(v.text_uthmani, v.matched_words, v.verse_key)
                    : arLang
                      ? highlightText(v.text_uthmani, query, "ar")
                      : v.text_uthmani}
                </p>
                {v.translation_text && (
                  <p
                    className={`verse-row__tr${v.translation_language === "ur" ? " font-urdu" : ""}`}
                    dir={v.translation_language === "ur" ? "rtl" : "ltr"}
                    lang={v.translation_language ?? undefined}
                  >
                    {trLang
                      ? highlightText(stripHtml(v.translation_text), query, trLang)
                      : stripHtml(v.translation_text)}
                  </p>
                )}
                <div className="verse-row__actions">
                  <Link href={`/${locale}/quran/${v.chapter_id}#${verseAnchor(v.verse_key)}`}>{dict.results.open_reader}</Link>
                  <Link
                    href={`/${locale}/tafsir/${v.chapter_id}?ayah=${v.verse_number}&hl=${encodeURIComponent(query)}#${verseAnchor(v.verse_key)}`}
                  >
                    {dict.results.open_tafsir}
                  </Link>
                </div>
              </article>
            );
          })}
        </section>
      ))}
    </div>
  );
}

// ------------------------------------------------------- Hadith / Tafsir ---

function hrefFor(hit: SearchHit, locale: Locale, query: string): string {
  const vk = typeof hit.ref?.verse_key === "string" ? hit.ref.verse_key : "";
  const hl = `hl=${encodeURIComponent(query)}`;
  if (hit.doc_type === "quran_verse" || hit.doc_type === "quran_translation") {
    return `/${locale}/quran/${surahOf(vk)}?${hl}#${verseAnchor(vk)}`;
  }
  if (hit.doc_type === "tafsir_entry") {
    const ayah = vk.split(":")[1];
    return `/${locale}/tafsir/${surahOf(vk)}?ayah=${ayah}&${hl}#${verseAnchor(vk)}`;
  }
  const coll = String(hit.ref?.collection ?? "");
  const num = String(hit.ref?.hadith_number ?? "");
  return `/${locale}/hadith/${coll}/h/${encodeURIComponent(num)}?${hl}`;
}

function citationFor(hit: SearchHit, locale: Locale, dict: Dict, chapter?: Chapter): string {
  const vk = typeof hit.ref?.verse_key === "string" ? hit.ref.verse_key : "";
  const keys = Array.isArray(hit.ref?.verse_keys) ? (hit.ref.verse_keys as string[]) : null;
  const range =
    keys && keys.length > 1 ? `${keys[0]}-${keys[keys.length - 1].split(":")[1]}` : vk;
  const surah = chapter ? (locale === "en" ? chapter.name_simple : chapter.name_arabic) : "";
  if (hit.doc_type === "quran_verse" || hit.doc_type === "quran_translation") {
    return `${dict.search.quran} ${vk}${surah ? ` · ${surah}` : ""}`;
  }
  if (hit.doc_type === "tafsir_entry") {
    return `${dict.tafsir.title} ${range}${surah ? ` · ${surah}` : ""}`;
  }
  const coll = String(hit.ref?.collection ?? "");
  const num = String(hit.ref?.hadith_number ?? "");
  return `${collectionName(coll, locale)} · ${dict.hadith.number} ${num}`;
}

function ResultCard({
  hit,
  query,
  dict,
  locale,
  chapter,
}: {
  hit: SearchHit;
  query: string;
  dict: Dict;
  locale: Locale;
  chapter?: Chapter;
}) {
  const rtl = isRtl(hit.language_code as "ar" | "ur");
  const isArabicScript = hit.language_code === "ar" || hit.language_code === "ur";
  const hl = highlightLang(query, hit.language_code);
  const body = stripHtml(hit.snippet ?? hit.text);
  const shown = body.length > 420 ? body.slice(0, 420) + "…" : body;
  const citation = citationFor(hit, locale, dict, chapter);
  return (
    <Link href={hrefFor(hit, locale, query)} className="card result-card">
      <div className="result-card__head">
        <span className="result-card__cite">{citation}</span>
        <span className={`badge badge--${hit.doc_type}`}>{labelFor(hit.doc_type, dict)}</span>
        {hit.doc_type === "hadith_text" && SAHIH_COLLECTIONS.has(hit.collection_key) && (
          <span className="badge badge--sahih">{dict.results.sahih_collection}</span>
        )}
        <span className="result-card__tools">
          <span className={`match-label${hit.match === "fulltext" ? "" : " match-label--soft"}`}>
            {hit.match === "fuzzy"
              ? dict.search.match_fuzzy
              : hit.match === "partial"
                ? dict.search.match_partial
                : hit.match === "semantic"
                  ? dict.search.match_semantic
                  : dict.search.match_exact}
          </span>
          <CopyButton
            text={stripHtml(hit.text)}
            reference={citation}
            font={hit.language_code === "ar" ? "arabic" : hit.language_code === "ur" ? "urdu" : "plain"}
            dir={rtl ? "rtl" : "ltr"}
            title={dict.common.view}
          />
        </span>
      </div>
      <p
        dir={rtl ? "rtl" : "ltr"}
        lang={hit.language_code}
        className={`result-card__body${hit.language_code === "ar" ? " font-arabic" : hit.language_code === "ur" ? " font-urdu" : ""}`}
        style={{
          fontSize: hit.language_code === "ur" ? 20 : isArabicScript ? 19 : 15.5,
          lineHeight: hit.language_code === "ur" ? 2.1 : isArabicScript ? 2 : 1.7,
        }}
      >
        {hl ? highlightText(shown, query, hl) : shown}
      </p>
      <div className="result-card__more">{dict.common.view} →</div>
    </Link>
  );
}

function labelFor(type: string, dict: Dict) {
  if (type.startsWith("quran")) return dict.search.quran;
  if (type === "hadith_text") return dict.search.hadith;
  return dict.search.tafsir;
}
