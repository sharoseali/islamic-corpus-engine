"use client";

import { useI18n } from "./providers";

export function Footer() {
  const { locale, dict } = useI18n();
  const isArabicScript = locale === "ar" || locale === "ur";

  return (
    <footer
      style={{
        borderTop: "1px solid var(--border)",
        padding: "16px 20px",
        background: "var(--bg-elevated)",
        textAlign: "center",
      }}
    >
      <p
        style={{
          margin: 0,
          maxWidth: 760,
          marginInline: "auto",
          fontSize: isArabicScript ? 14 : 13,
          lineHeight: isArabicScript ? 1.9 : 1.6,
          color: "var(--text-muted)",
        }}
      >
        {dict.home.authenticity_desc}
      </p>
    </footer>
  );
}
