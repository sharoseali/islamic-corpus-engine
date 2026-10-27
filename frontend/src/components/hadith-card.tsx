"use client";

import type { HadithListItem } from "@/lib/types";
import type { Dictionary } from "@/i18n/dictionaries";
import { CopyButton } from "./copy-button";
import { highlightLang, highlightText } from "@/lib/highlight";

const LANG_LABEL: Record<string, string> = { ar: "العربية", ur: "اردو", en: "English" };

const SAHIHAYN = new Set(["bukhari", "muslim"]);

export function HadithCard({
  hadith,
  collectionName,
  collectionKey,
  dict,
  highlight,
}: {
  hadith: HadithListItem;
  collectionName: string;
  collectionKey: string;
  dict: Dictionary;
  // Query to highlight (set when arriving from a search result).
  highlight?: string;
}) {
  // Explicit gradings (present in future collections) take priority; for
  // the two Ṣaḥīḥ collections, authenticity is established by inclusion.
  const explicitGrades =
    Array.isArray(hadith.grades) && hadith.grades.length > 0
      ? hadith.grades
          .map((g) =>
            typeof g === "string"
              ? g
              : (g as { grade?: string; name?: string })?.grade ??
                (g as { name?: string })?.name,
          )
          .filter(Boolean)
      : [];
  const isSahih = SAHIHAYN.has(collectionKey);

  return (
    <div className="card" style={{ padding: "22px 24px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
        <span
          style={{
            fontSize: 13,
            fontWeight: 700,
            color: "var(--accent)",
            background: "var(--accent-soft)",
            borderRadius: 999,
            padding: "3px 12px",
          }}
        >
          {collectionName} {hadith.hadith_number}
        </span>
        {hadith.arabic_number && (
          <span style={{ fontSize: 12, color: "var(--text-faint)" }}>
            ({hadith.arabic_number})
          </span>
        )}
        <span style={{ marginInlineStart: "auto", display: "flex", gap: 6, alignItems: "center" }}>
          {explicitGrades.length > 0
            ? explicitGrades.map((g, i) => <GradeBadge key={i} label={String(g)} />)
            : isSahih && <GradeBadge label={dict.hadith.sahih} title={dict.hadith.sahih_note} authentic />}
          <CopyButton
            text={hadith.texts.map((t) => t.text).join("\n\n")}
            reference={`${collectionName} ${hadith.hadith_number}`}
            font="arabic"
            dir="rtl"
            title={dict.common.view}
          />
        </span>
      </div>

      {hadith.texts.map((t) => {
        const rtl = t.language_code === "ar" || t.language_code === "ur";
        const hlLang = highlight ? highlightLang(highlight, t.language_code) : null;
        return (
          <div key={t.language_code} style={{ marginBottom: 16 }}>
            <div
              style={{
                fontSize: 11.5,
                fontWeight: 700,
                letterSpacing: "0.04em",
                textTransform: "uppercase",
                color: "var(--text-faint)",
                marginBottom: 6,
              }}
            >
              {LANG_LABEL[t.language_code] ?? t.language_code}
            </div>
            <p
              dir={rtl ? "rtl" : "ltr"}
              className={
                t.language_code === "ar"
                  ? "font-arabic"
                  : t.language_code === "ur"
                  ? "font-urdu"
                  : ""
              }
              style={{
                margin: 0,
                fontSize:
                  t.language_code === "ar" ? 21 : t.language_code === "ur" ? 20 : 15.5,
                lineHeight:
                  t.language_code === "ar" ? 2.1 : t.language_code === "ur" ? 2.1 : 1.75,
                color: "var(--text)",
              }}
            >
              {hlLang ? highlightText(t.text, highlight, hlLang) : t.text}
            </p>
          </div>
        );
      })}

      <div style={{ borderTop: "1px solid var(--border)", paddingTop: 12, marginTop: 4 }}>
        <span style={{ fontSize: 12, color: "var(--text-faint)" }}>
          {dict.hadith.isnad_note}
        </span>
      </div>
    </div>
  );
}

function GradeBadge({
  label,
  title,
  authentic,
}: {
  label: string;
  title?: string;
  authentic?: boolean;
}) {
  return (
    <span
      title={title}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        fontSize: 12,
        fontWeight: 700,
        padding: "3px 11px",
        borderRadius: 999,
        background: authentic ? "var(--accent-soft)" : "var(--gold-soft)",
        color: authentic ? "var(--accent)" : "var(--gold)",
        border: `1px solid ${authentic ? "var(--accent)" : "var(--gold)"}`,
      }}
    >
      {authentic && <span aria-hidden>✓</span>}
      {label}
    </span>
  );
}
