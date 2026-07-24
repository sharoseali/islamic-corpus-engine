"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useI18n } from "./providers";
import { api } from "@/lib/api";
import { isRtl, type Locale } from "@/i18n/config";
import { collectionName, surahOf, verseAnchor } from "@/lib/localize";
import type { SearchHit, SearchResponse } from "@/lib/types";
import { Container } from "./ui";
import { primaryBtn } from "./home-search";
import { CopyButton } from "./copy-button";

const TYPE_GROUPS: { key: string; types: string }[] = [
  { key: "all", types: "" },
  { key: "quran", types: "quran_verse,quran_translation" },
  { key: "hadith", types: "hadith_text" },
  { key: "tafsir", types: "tafsir_entry" },
];

function stripHtml(s: string) {
  return s.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
}

const AUTO_LABEL: Record<Locale, string> = {
  en: "Auto",
  ur: "خودکار",
  ar: "تلقائي",
  tr: "Otomatik",
};

const hasArabicScript = (s: string) => /[؀-ۿ]/.test(s);

// Intelligent language routing: pick which content languages to search from
// the query's script and the user's selected UI language. Arabic-script
// queries hit Arabic (and Urdu when the UI is Urdu); Latin queries hit the
// English content that bridges to the Arabic sources.
function targetLangs(query: string, mode: string, locale: Locale): string[] {
  if (mode !== "auto") return [mode];
  if (hasArabicScript(query)) {
    return locale === "ur" ? ["ar", "ur"] : ["ar"];
  }
  return locale === "ur" ? ["en", "ur"] : ["en"];
}

export function SearchView() {
  const { locale, dict } = useI18n();
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQ = searchParams.get("q") ?? "";

  const [q, setQ] = useState(initialQ);
  const [group, setGroup] = useState("all");
  const [langMode, setLangMode] = useState<string>("auto");
  const [data, setData] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const runSearch = useCallback(
    async (query: string, g: string, mode: string) => {
      const trimmed = query.trim();
      if (!trimmed) {
        setData(null);
        return;
      }
      setLoading(true);
      try {
        const types = TYPE_GROUPS.find((t) => t.key === g)?.types;
        const langs = targetLangs(trimmed, mode, locale);
        const responses = await Promise.all(
          langs.map((lang) =>
            api
              .search(trimmed, lang, { types: types || undefined, limit: 30 })
              .catch(() => null),
          ),
        );
        // Merge, dedup, and rank across languages.
        const seen = new Set<string>();
        const merged: SearchHit[] = [];
        for (const res of responses) {
          if (!res) continue;
          for (const hit of res.hits) {
            const key = `${hit.doc_type}:${hit.source_row_id}`;
            if (seen.has(key)) continue;
            seen.add(key);
            merged.push(hit);
          }
        }
        merged.sort((a, b) => b.score - a.score);
        setData({
          query: trimmed,
          language_code: langs.join("+"),
          total: merged.length,
          hits: merged.slice(0, 40),
        });
      } catch {
        setData({ query: trimmed, language_code: mode, total: 0, hits: [] });
      } finally {
        setLoading(false);
      }
    },
    [locale],
  );

  useEffect(() => {
    if (initialQ) runSearch(initialQ, group, langMode);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQ]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    router.replace(`/${locale}/search?q=${encodeURIComponent(q.trim())}`);
    runSearch(q, group, langMode);
  };

  const changeGroup = (g: string) => {
    setGroup(g);
    runSearch(q, g, langMode);
  };

  const changeLang = (mode: string) => {
    setLangMode(mode);
    runSearch(q, group, mode);
  };

  return (
    <Container narrow style={{ padding: "36px 20px 60px" }} >
      <form onSubmit={submit} style={{ display: "flex", gap: 8, marginBottom: 18 }}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={dict.search.placeholder}
          autoFocus
          style={{
            flex: 1,
            border: "1px solid var(--border-strong)",
            borderRadius: 12,
            padding: "13px 16px",
            fontSize: 16,
            background: "var(--surface)",
            color: "var(--text)",
            outline: "none",
            fontFamily: "inherit",
          }}
        />
        <button type="submit" style={primaryBtn}>
          {dict.search.button}
        </button>
      </form>

      {/* Filters */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 8,
          alignItems: "center",
          marginBottom: 24,
        }}
      >
        <div style={{ display: "flex", gap: 4 }}>
          {TYPE_GROUPS.map((t) => (
            <button
              key={t.key}
              onClick={() => changeGroup(t.key)}
              style={chip(group === t.key)}
            >
              {dict.search[t.key as keyof typeof dict.search] ?? t.key}
            </button>
          ))}
        </div>
        <div style={{ marginInlineStart: "auto", display: "flex", gap: 4 }}>
          <button onClick={() => changeLang("auto")} style={chip(langMode === "auto")}>
            {AUTO_LABEL[locale]}
          </button>
          {["ar", "ur", "en"].map((l) => (
            <button key={l} onClick={() => changeLang(l)} style={chip(langMode === l)}>
              {l.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <p style={{ color: "var(--text-muted)", textAlign: "center", padding: 40 }}>
          {dict.search.searching}
        </p>
      )}

      {!loading && !data && (
        <p style={{ color: "var(--text-faint)", textAlign: "center", padding: 40 }}>
          {dict.search.prompt}
        </p>
      )}

      {!loading && data && data.hits.length === 0 && (
        <p style={{ color: "var(--text-muted)", textAlign: "center", padding: 40 }}>
          {dict.search.no_results}
        </p>
      )}

      {!loading && data && data.hits.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }} className="fade-in">
          <p style={{ color: "var(--text-faint)", fontSize: 14, margin: "0 0 4px" }}>
            {data.total} · {dict.search.results_for} “{data.query}”
          </p>
          {data.hits.map((h, i) => (
            <ResultCard
              key={`${h.doc_type}-${h.source_row_id}-${i}`}
              hit={h}
              dict={dict}
              locale={locale}
            />
          ))}
        </div>
      )}
    </Container>
  );
}

function hrefFor(hit: SearchHit, locale: Locale): string {
  const vk = typeof hit.ref?.verse_key === "string" ? hit.ref.verse_key : "";
  if (hit.doc_type === "quran_verse" || hit.doc_type === "quran_translation") {
    return `/${locale}/quran/${surahOf(vk)}#${verseAnchor(vk)}`;
  }
  if (hit.doc_type === "tafsir_entry") {
    return `/${locale}/tafsir/${surahOf(vk)}#${verseAnchor(vk)}`;
  }
  // hadith
  const coll = String(hit.ref?.collection ?? "");
  const num = String(hit.ref?.hadith_number ?? "");
  return `/${locale}/hadith/${coll}/h/${encodeURIComponent(num)}`;
}

function localizedCitation(
  hit: SearchHit,
  locale: Locale,
  dict: ReturnType<typeof useI18n>["dict"],
): string {
  const vk = typeof hit.ref?.verse_key === "string" ? hit.ref.verse_key : "";
  if (hit.doc_type === "quran_verse" || hit.doc_type === "quran_translation") {
    return `${dict.search.quran} ${vk}`;
  }
  if (hit.doc_type === "tafsir_entry") {
    return `${dict.tafsir.title} - ${vk}`;
  }
  const coll = String(hit.ref?.collection ?? "");
  const num = String(hit.ref?.hadith_number ?? "");
  return `${collectionName(coll, locale)} - ${dict.hadith.number} ${num}`;
}

function ResultCard({
  hit,
  dict,
  locale,
}: {
  hit: SearchHit;
  dict: ReturnType<typeof useI18n>["dict"];
  locale: Locale;
}) {
  const rtl = isRtl(hit.language_code as "ar" | "ur");
  const isArabicScript = hit.language_code === "ar" || hit.language_code === "ur";
  return (
    <Link href={hrefFor(hit, locale)} className="card result-card" style={{ padding: "18px 20px", display: "block" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginBottom: 10,
          flexWrap: "wrap",
        }}
      >
        <span style={{ fontSize: 13.5, fontWeight: 700, color: "var(--accent)" }}>
          {localizedCitation(hit, locale, dict)}
        </span>
        <span style={badge(hit.doc_type)}>{labelFor(hit.doc_type, dict)}</span>
        <span
          style={{
            marginInlineStart: "auto",
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <span
            style={{
              fontSize: 11.5,
              color: hit.match === "fuzzy" ? "var(--gold)" : "var(--text-faint)",
              fontWeight: 600,
            }}
          >
            {hit.match === "fuzzy" ? dict.search.match_fuzzy : dict.search.match_exact}
          </span>
          <CopyButton
            text={stripHtml(hit.text)}
            reference={localizedCitation(hit, locale, dict)}
            font={hit.language_code === "ar" ? "arabic" : hit.language_code === "ur" ? "urdu" : "plain"}
            dir={rtl ? "rtl" : "ltr"}
            title={dict.common.view}
          />
        </span>
      </div>
      <p
        dir={rtl ? "rtl" : "ltr"}
        className={
          hit.language_code === "ar"
            ? "font-arabic"
            : hit.language_code === "ur"
            ? "font-urdu"
            : ""
        }
        style={{
          margin: 0,
          fontSize: hit.language_code === "ur" ? 20 : isArabicScript ? 19 : 15.5,
          lineHeight: hit.language_code === "ur" ? 2.1 : isArabicScript ? 2 : 1.7,
          color: "var(--text)",
        }}
      >
        {truncate(stripHtml(hit.text), 320)}
      </p>
      <div
        style={{
          marginTop: 12,
          fontSize: 12.5,
          fontWeight: 600,
          color: "var(--accent)",
        }}
      >
        {dict.common.view} →
      </div>
    </Link>
  );
}

function truncate(s: string, n: number) {
  return s.length > n ? s.slice(0, n) + "…" : s;
}

function labelFor(type: string, dict: ReturnType<typeof useI18n>["dict"]) {
  if (type.startsWith("quran")) return dict.search.quran;
  if (type === "hadith_text") return dict.search.hadith;
  return dict.search.tafsir;
}

function chip(active: boolean): React.CSSProperties {
  return {
    padding: "7px 14px",
    borderRadius: 999,
    fontSize: 14,
    fontWeight: 600,
    border: "1px solid " + (active ? "transparent" : "var(--border)"),
    background: active ? "var(--accent)" : "var(--surface)",
    color: active ? "#fff" : "var(--text-muted)",
    cursor: "pointer",
    fontFamily: "inherit",
  };
}

function badge(type: string): React.CSSProperties {
  const map: Record<string, [string, string]> = {
    quran_verse: ["var(--accent-soft)", "var(--accent)"],
    quran_translation: ["var(--accent-soft)", "var(--accent)"],
    hadith_text: ["var(--gold-soft)", "var(--gold)"],
    tafsir_entry: ["var(--surface-2)", "var(--text-muted)"],
  };
  const [bg, color] = map[type] ?? ["var(--surface-2)", "var(--text-muted)"];
  return {
    padding: "2px 9px",
    borderRadius: 999,
    fontSize: 11.5,
    fontWeight: 600,
    background: bg,
    color,
  };
}
