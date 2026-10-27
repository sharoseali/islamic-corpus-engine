"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useI18n } from "./providers";
import { highlightHtml, highlightLang, highlightText } from "@/lib/highlight";
import { api } from "@/lib/api";
import { verseAnchor } from "@/lib/localize";
import type { ResourceInfo, VerseDetail } from "@/lib/types";
import { CopyButton } from "./copy-button";
import { ElaajLoader } from "./elaaj-loader";

const stripHtml = (s: string) =>
  s.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();

// Sensible defaults per UI language. 0 = no translation (Arabic-only view
// for the Arabic locale). Turkish reads the Diyanet translation (id 77).
const DEFAULT_TRANSLATION: Record<string, number> = { en: 20, ur: 234, ar: 0, tr: 77 };
const DEFAULT_TAFSIR: Record<string, number> = { en: 35, ur: 30, ar: 22, tr: 22 };

export function QuranReader({
  chapterId,
  translations,
  tafsirs,
  bismillah,
  initialShowTafsir = false,
}: {
  chapterId: number;
  translations: ResourceInfo[];
  tafsirs: ResourceInfo[];
  bismillah: boolean;
  initialShowTafsir?: boolean;
}) {
  const { locale, dict } = useI18n();
  // Search results link here with ?hl=<query>: highlight the matched words.
  const hl = useSearchParams().get("hl") ?? "";
  const [translationId, setTranslationId] = useState(
    DEFAULT_TRANSLATION[locale] ?? 20,
  );
  const [tafsirId, setTafsirId] = useState(DEFAULT_TAFSIR[locale] ?? 35);
  const [showTafsir, setShowTafsir] = useState(initialShowTafsir);
  const [verses, setVerses] = useState<VerseDetail[] | null>(null);
  const [openVerse, setOpenVerse] = useState<number | null>(null);

  useEffect(() => {
    setVerses(null);
    const tafsirIds = showTafsir ? [tafsirId] : [];
    const translationIds = translationId > 0 ? [translationId] : [];
    api
      .getChapterVerses(chapterId, translationIds, tafsirIds)
      .then(setVerses)
      .catch(() => setVerses([]));
  }, [chapterId, translationId, tafsirId, showTafsir]);

  const tafsirLang = useMemo(
    () => tafsirs.find((t) => t.id === tafsirId)?.language_code ?? "en",
    [tafsirs, tafsirId],
  );

  // When arriving from a search link (…#ayah-2_255), scroll to that ayah,
  // highlight it, and open its tafsir.
  useEffect(() => {
    if (!verses || verses.length === 0) return;
    const hash = window.location.hash.replace(/^#/, "");
    if (!hash) return;
    const el = document.getElementById(hash);
    if (!el) return;
    const target = verses.find((v) => verseAnchor(v.verse_key) === hash);
    if (target && showTafsir) setOpenVerse(target.id);
    el.classList.add("ayah-target");
    el.scrollIntoView({ behavior: "smooth", block: "start" });
    const t = setTimeout(() => el.classList.remove("ayah-target"), 2600);
    return () => clearTimeout(t);
  }, [verses, showTafsir]);

  return (
    <div>
      {/* Controls */}
      <div
        className="card"
        style={{
          padding: "12px 14px",
          display: "flex",
          gap: 12,
          flexWrap: "wrap",
          alignItems: "center",
          marginBottom: 20,
          position: "sticky",
          top: 76,
          zIndex: 10,
        }}
      >
        <Select
          label={dict.quran.translation}
          value={translationId}
          onChange={setTranslationId}
          options={[
            { value: 0, label: "-" },
            ...translations.map((t) => ({
              value: t.id,
              label: `${t.name} (${t.language_code})`,
            })),
          ]}
        />
        <label style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 14, cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={showTafsir}
            onChange={(e) => setShowTafsir(e.target.checked)}
            style={{ accentColor: "var(--accent)", width: 16, height: 16 }}
          />
          {showTafsir ? dict.quran.hide_tafsir : dict.quran.show_tafsir}
        </label>
        {showTafsir && (
          <Select
            label={dict.quran.tafsir}
            value={tafsirId}
            onChange={setTafsirId}
            options={tafsirs.map((t) => ({
              value: t.id,
              label: `${t.name} (${t.language_code})`,
            }))}
          />
        )}
      </div>

      {bismillah && chapterId !== 1 && chapterId !== 9 && (
        <div
          className="font-arabic"
          style={{ textAlign: "center", fontSize: 28, margin: "8px 0 26px", color: "var(--text)" }}
        >
          بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ
        </div>
      )}

      {!verses && <ElaajLoader />}

      {verses?.map((v) => {
        const tafsirEntry = v.tafsir[0];
        return (
          <div
            key={v.id}
            id={verseAnchor(v.verse_key)}
            className="card"
            style={{ padding: "22px 24px", marginBottom: 16 }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginBottom: 14,
              }}
            >
              <span
                style={{
                  fontSize: 13,
                  fontWeight: 700,
                  color: "var(--accent)",
                  background: "var(--accent-soft)",
                  borderRadius: 999,
                  padding: "3px 11px",
                }}
              >
                {v.verse_key}
              </span>
              <span style={{ marginInlineStart: "auto" }}>
                <CopyButton
                  text={
                    v.text_uthmani +
                    (v.translations.length
                      ? "\n\n" + v.translations.map((t) => stripHtml(t.text)).join("\n")
                      : "")
                  }
                  reference={`${dict.quran.title} ${v.verse_key}`}
                  font="arabic"
                  dir="rtl"
                  title={dict.common.view}
                />
              </span>
            </div>

            {/* Arabic ayah */}
            <p dir="rtl" className="quran-text" style={{ margin: "0 0 16px", textAlign: "right" }}>
              {hl && highlightLang(hl, "ar") ? highlightText(v.text_uthmani, hl, "ar") : v.text_uthmani}
            </p>

            {/* Translation */}
            {v.translations.map((t) => {
              const rtl = t.language_code === "ur" || t.language_code === "ar";
              return (
                <p
                  key={t.resource_id}
                  dir={rtl ? "rtl" : "ltr"}
                  className={
                    t.language_code === "ur"
                      ? "font-urdu rich-text"
                      : "rich-text"
                  }
                  style={{
                    margin: "0 0 6px",
                    fontSize: t.language_code === "ur" ? 20 : rtl ? 18 : 16,
                    color:
                      t.language_code === "ur" ? "var(--text)" : "var(--text-muted)",
                    lineHeight: t.language_code === "ur" ? 2.1 : rtl ? 2.2 : 1.7,
                  }}
                  dangerouslySetInnerHTML={{
                    __html:
                      hl && highlightLang(hl, t.language_code)
                        ? highlightHtml(t.text, hl, highlightLang(hl, t.language_code) as string)
                        : t.text,
                  }}
                />
              );
            })}

            {/* Tafsir */}
            {showTafsir && tafsirEntry && (
              <div style={{ marginTop: 14 }}>
                <button
                  onClick={() => setOpenVerse(openVerse === v.id ? null : v.id)}
                  style={{
                    background: "transparent",
                    border: "1px solid var(--border)",
                    borderRadius: 9,
                    padding: "6px 12px",
                    fontSize: 13,
                    fontWeight: 600,
                    color: "var(--accent)",
                    cursor: "pointer",
                    fontFamily: "inherit",
                  }}
                >
                  {dict.quran.tafsir} - Ibn Kathir{" "}
                  {openVerse === v.id ? "▲" : "▼"}
                </button>
                {openVerse === v.id && (
                  <div className="fade-in" style={{ marginTop: 12, paddingTop: 14, borderTop: "1px solid var(--border)" }}>
                    <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 6 }}>
                      <CopyButton
                        text={stripHtml(tafsirEntry.text)}
                        reference={`${dict.tafsir.title} ${v.verse_key}`}
                        font={tafsirLang === "ur" ? "urdu" : tafsirLang === "ar" ? "arabic" : "plain"}
                        dir={tafsirLang === "ar" || tafsirLang === "ur" ? "rtl" : "ltr"}
                        title={dict.common.view}
                      />
                    </div>
                    <div
                      dir={tafsirLang === "ar" || tafsirLang === "ur" ? "rtl" : "ltr"}
                      className={
                        (tafsirLang === "ur" ? "font-urdu " : "") + "rich-text"
                      }
                      style={{
                        fontSize: tafsirLang === "ur" ? 19 : tafsirLang === "ar" ? 17 : 15,
                        color: "var(--text)",
                        lineHeight: tafsirLang === "ur" ? 2.1 : 1.85,
                      }}
                      dangerouslySetInnerHTML={{ __html: tafsirEntry.text }}
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  options: { value: number; label: string }[];
}) {
  return (
    <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 14 }}>
      <span style={{ color: "var(--text-faint)" }}>{label}:</span>
      <select
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: "6px 10px",
          background: "var(--surface)",
          color: "var(--text)",
          fontSize: 14,
          fontFamily: "inherit",
          cursor: "pointer",
          maxWidth: 220,
        }}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}
