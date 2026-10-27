"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useI18n } from "./providers";
import { api } from "@/lib/api";
import { verseAnchor } from "@/lib/localize";
import { highlightHtml, highlightLang } from "@/lib/highlight";
import type { Chapter, ResourceInfo, VerseDetail } from "@/lib/types";
import { CopyButton } from "./copy-button";
import { ElaajLoader } from "./elaaj-loader";

const stripHtml = (s: string) =>
  s.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();

// Ayat per reading page. Ibn Kathir comments on groups of ayat; a page
// never cuts a group, so it may run a few ayat longer.
const PAGE_SIZE = 10;
const LOOKAHEAD = 6;

// Which Ibn Kathir edition to open by default for each UI language.
const DEFAULT_TAFSIR: Record<string, number> = { en: 35, ur: 30, ar: 22, tr: 22 };

// Endonym for each edition's language, used on the switch (same in every UI).
const LANG_ENDONYM: Record<string, string> = {
  ar: "العربية",
  ur: "اردو",
  en: "English",
};

// Component-local strings (author + source are the verified attribution).
const T: Record<
  string,
  { read_in: string; work: string; author: string; source: string; original: string; translation: string }
> = {
  en: {
    read_in: "Read in",
    work: "Tafsir Ibn Kathir",
    author: "Ḥāfiẓ Ibn Kathir (Ismāʿīl ibn Kathīr al-Dimashqī, 701-774 AH)",
    source: "Source: Quranic Universal Library (Tarteel)",
    original: "Original Arabic text",
    translation: "Translation as distributed by the source",
  },
  ur: {
    read_in: "پڑھیں",
    work: "تفسیرِ ابنِ کثیر",
    author: "الحافظ ابنِ کثیر (اسماعیل بن کثیر الدمشقی، ۷۰۱ - ۷۷۴ھ)",
    source: "ماخذ: قرآنک یونیورسل لائبریری (ترتیل)",
    original: "اصل عربی متن",
    translation: "ترجمہ، بعینہٖ ماخذ کے مطابق",
  },
  ar: {
    read_in: "اقرأ بـ",
    work: "تفسير ابن كثير",
    author: "الحافظ ابن كثير (إسماعيل بن كثير الدمشقي، ٧٠١ - ٧٧٤ هـ)",
    source: "المصدر: المكتبة القرآنية الجامعة (ترتيل)",
    original: "النص العربي الأصلي",
    translation: "الترجمة كما وردت من المصدر",
  },
  tr: {
    read_in: "Şu dilde oku",
    work: "Tefsir İbn Kesir",
    author: "Hafız İbn Kesir (İsmail ibn Kesir ed-Dımaşki, 701-774 H)",
    source: "Kaynak: Quranic Universal Library (Tarteel)",
    original: "Özgün Arapça metin",
    translation: "Kaynaktan aktarıldığı biçimiyle çeviri",
  },
};

type Group = { fromKey: string; toKey: string; fromNum: number; toNum: number; arabic: string[]; html: string };

function fill(template: string, vars: Record<string, string | number>) {
  return template.replace(/\{(\w+)\}/g, (_, k) => String(vars[k] ?? ""));
}

export function TafsirReader({
  meta,
  tafsirs,
  initialAyah,
  highlightQuery,
}: {
  meta: Chapter;
  tafsirs: ResourceInfo[];
  initialAyah?: number;
  highlightQuery?: string;
}) {
  const { locale, dict } = useI18n();
  const t = T[locale] ?? T.en;
  const total = meta.verses_count;
  const clamp = (n: number) => Math.min(Math.max(1, Math.floor(n) || 1), total);

  const [tafsirId, setTafsirId] = useState(DEFAULT_TAFSIR[locale] ?? 35);
  const [start, setStart] = useState(() => clamp(initialAyah ?? 1));
  const [verses, setVerses] = useState<VerseDetail[] | null>(null);
  const [hl, setHl] = useState<string | undefined>(highlightQuery);
  const [jump, setJump] = useState("");
  const [showTop, setShowTop] = useState(false);
  const targetRef = useRef<number | null>(initialAyah ?? null);

  // A link may carry the ayah in the hash (#ayah-2_36) instead of ?ayah=.
  useEffect(() => {
    const m = /ayah-(\d+)_(\d+)/.exec(window.location.hash);
    if (m && !initialAyah) {
      const n = clamp(Number(m[2]));
      targetRef.current = n;
      setStart(n);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    let cancelled = false;
    setVerses(null);
    api
      .getChapterVerses(meta.id, [], [tafsirId], { from: start, to: Math.min(total, start + PAGE_SIZE + LOOKAHEAD - 1) })
      .then((rows) => {
        if (!cancelled) setVerses(rows);
      })
      .catch(() => {
        if (!cancelled) setVerses([]);
      });
    const url = new URL(window.location.href);
    url.searchParams.set("ayah", String(start));
    window.history.replaceState(null, "", url.toString());
    return () => {
      cancelled = true;
    };
  }, [meta.id, tafsirId, start, total]);

  const lang = useMemo(
    () => tafsirs.find((x) => x.id === tafsirId)?.language_code ?? "en",
    [tafsirs, tafsirId],
  );
  const rtl = lang === "ar" || lang === "ur";
  const hlLang = hl ? highlightLang(hl, lang) : null;

  const order = ["ar", "ur", "en"];
  const editions = useMemo(
    () => [...tafsirs].sort((a, b) => order.indexOf(a.language_code) - order.indexOf(b.language_code)),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [tafsirs],
  );

  // Group consecutive ayat sharing one commentary, then cut the page at the
  // first group boundary after PAGE_SIZE ayat.
  const { groups, pageEnd } = useMemo(() => {
    if (!verses) return { groups: null as Group[] | null, pageEnd: start };
    const all: Group[] = [];
    for (const v of verses) {
      const html = v.tafsir[0]?.text ?? "";
      const last = all[all.length - 1];
      if (last && last.html === html) {
        last.toKey = v.verse_key;
        last.toNum = v.verse_number;
        last.arabic.push(v.text_uthmani);
      } else {
        all.push({ fromKey: v.verse_key, toKey: v.verse_key, fromNum: v.verse_number, toNum: v.verse_number, arabic: [v.text_uthmani], html });
      }
    }
    const page: Group[] = [];
    let end = start - 1;
    for (const g of all) {
      if (page.length && end - start + 1 >= PAGE_SIZE) break;
      page.push(g);
      end = g.toNum;
    }
    return { groups: page, pageEnd: end };
  }, [verses, start]);

  // Scroll to the requested ayah once its page has rendered.
  useEffect(() => {
    if (!groups || targetRef.current === null) return;
    const n = targetRef.current;
    const g = groups.find((x) => n >= x.fromNum && n <= x.toNum);
    const el = g ? document.getElementById(verseAnchor(g.fromKey)) : null;
    if (el) {
      el.scrollIntoView({ block: "start", behavior: "smooth" });
      el.classList.add("is-target");
      targetRef.current = null;
    }
  }, [groups]);

  useEffect(() => {
    const onScroll = () => setShowTop(window.scrollY > 600);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const goTo = useCallback(
    (n: number) => {
      const c = clamp(n);
      targetRef.current = c;
      setStart(c);
      document.getElementById("tafsir-top")?.scrollIntoView({ block: "start", behavior: "smooth" });
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [total],
  );
  const hasPrev = start > 1;
  const hasNext = pageEnd < total;
  const progress = Math.round((pageEnd / total) * 100);

  const nav = (
    <div className="reader-nav">
      <button type="button" className="reader-nav__btn" onClick={() => goTo(start - PAGE_SIZE)} disabled={!hasPrev}>
        {dict.reader.previous}
      </button>
      <span className="reader-nav__range">{fill(dict.reader.ayat_range, { from: start, to: pageEnd, total })}</span>
      <form
        className="reader-nav__jump"
        onSubmit={(e) => {
          e.preventDefault();
          if (jump) goTo(Number(jump));
        }}
      >
        <label>
          <span className="sr-only">{dict.reader.jump_to_ayah}</span>
          <input
            type="number"
            min={1}
            max={total}
            value={jump}
            onChange={(e) => setJump(e.target.value)}
            placeholder={dict.reader.jump_to_ayah}
            inputMode="numeric"
          />
        </label>
        <button type="submit" className="reader-nav__btn">{dict.reader.go}</button>
      </form>
      <button type="button" className="reader-nav__btn reader-nav__btn--primary" onClick={() => goTo(pageEnd + 1)} disabled={!hasNext}>
        {dict.reader.next}
      </button>
    </div>
  );

  return (
    <div id="tafsir-top">
      {/* Surah heading + verified attribution */}
      <header className="tafsir-header">
        <div className="font-arabic tafsir-surah-ar">{meta.name_arabic}</div>
        {locale !== "ar" && <div className="tafsir-surah-name">{meta.name_simple}</div>}
        <div className="tafsir-attribution">
          <span className="tafsir-attr-work">{t.work}</span>
          <span className="tafsir-attr-dot" aria-hidden>·</span>
          <span className="tafsir-attr-author">{t.author}</span>
        </div>
        <div className="tafsir-attr-source">{t.source}</div>
      </header>

      {/* Reading language switch (Arabic original, Urdu, English) */}
      <div className="tafsir-switch">
        <span className="tafsir-switch-label">{t.read_in}:</span>
        {editions.map((e) => (
          <button
            key={e.id}
            type="button"
            onClick={() => setTafsirId(e.id)}
            className={"tafsir-switch-btn" + (e.id === tafsirId ? " is-active" : "")}
            lang={e.language_code}
          >
            {LANG_ENDONYM[e.language_code] ?? e.language_code}
          </button>
        ))}
        <span className="tafsir-switch-note">{lang === "ar" ? t.original : t.translation}</span>
      </div>

      {/* Sticky position bar: range, paging, jump, progress */}
      <div className="reader-bar">
        {nav}
        <div className="reader-progress" aria-hidden>
          <span style={{ width: `${progress}%` }} />
        </div>
      </div>

      {hl && (
        <div className="reader-hl-note">
          <span>{fill(dict.reader.highlighted_from_search, { q: hl })}</span>
          <button type="button" className="chip" onClick={() => setHl(undefined)}>✕</button>
        </div>
      )}

      {!verses && <ElaajLoader />}

      {groups && (
        <article className="tafsir-book" dir={rtl ? "rtl" : "ltr"}>
          {groups.map((g) => {
            const chap = g.fromKey.split(":")[0];
            const label = g.fromNum === g.toNum ? `${chap}:${g.fromNum}` : `${chap}:${g.fromNum}-${g.toNum}`;
            const html = hlLang ? highlightHtml(g.html, hl, hlLang) : g.html;
            return (
              <section key={g.fromKey} id={verseAnchor(g.fromKey)} className="tafsir-section">
                <div className="tafsir-ayah">
                  <span className="tafsir-ayah-key">{label}</span>
                  <span className="tafsir-ayah-ar font-arabic" dir="rtl">
                    {g.arabic.join(" ۝ ")}
                  </span>
                  <span className="tafsir-ayah-copy">
                    <CopyButton
                      text={stripHtml(g.html)}
                      reference={`${t.work} ${label}`}
                      font={lang === "ur" ? "urdu" : lang === "ar" ? "arabic" : "plain"}
                      dir={rtl ? "rtl" : "ltr"}
                      title={label}
                    />
                  </span>
                </div>
                <div
                  dir={rtl ? "rtl" : "ltr"}
                  className={(lang === "ur" ? "font-urdu " : lang === "ar" ? "font-arabic " : "") + "rich-text tafsir-prose"}
                  dangerouslySetInnerHTML={{ __html: html }}
                />
              </section>
            );
          })}
        </article>
      )}

      {groups && <div className="reader-bar reader-bar--bottom">{nav}</div>}

      <button
        type="button"
        className={`back-to-top${showTop ? " is-visible" : ""}`}
        onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        aria-label={dict.reader.back_to_top}
        title={dict.reader.back_to_top}
      >
        ↑
      </button>
    </div>
  );
}
