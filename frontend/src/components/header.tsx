"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { useI18n, useTheme } from "./providers";
import { LOCALES, LOCALE_NAMES, type Locale } from "@/i18n/config";

export function Header() {
  const { locale, dict } = useI18n();
  const { theme, toggle } = useTheme();
  const pathname = usePathname();
  const router = useRouter();
  const [langOpen, setLangOpen] = useState(false);

  const nav = [
    { href: `/${locale}`, label: dict.nav.home, exact: true },
    { href: `/${locale}/quran`, label: dict.nav.quran },
    { href: `/${locale}/hadith`, label: dict.nav.hadith },
    { href: `/${locale}/tafsir`, label: dict.nav.tafsir },
    { href: `/${locale}/search`, label: dict.nav.search },
  ];

  const isActive = (href: string, exact?: boolean) =>
    exact ? pathname === href : pathname.startsWith(href);

  const switchLocale = (next: Locale) => {
    const rest = pathname.replace(new RegExp(`^/${locale}`), "");
    router.push(`/${next}${rest}`);
    setLangOpen(false);
  };

  return (
    <header
      style={{
        borderBottom: "1px solid var(--border)",
        background: "color-mix(in srgb, var(--bg-elevated) 92%, transparent)",
        backdropFilter: "blur(8px)",
        position: "sticky",
        top: 0,
        zIndex: 50,
      }}
    >
      <div
        style={{
          maxWidth: 1140,
          margin: "0 auto",
          padding: "0 20px",
          height: 64,
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        <Link
          href={`/${locale}`}
          style={{ display: "flex", alignItems: "center", gap: 10, marginInlineEnd: "auto" }}
        >
          <span
            aria-hidden
            style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              border: "1px solid var(--gold)",
              color: "var(--gold)",
              display: "grid",
              placeItems: "center",
              fontWeight: 700,
              fontSize: 19,
              fontFamily: "var(--font-arabic)",
            }}
          >
            ع
          </span>
          <span
            className={locale === "en" || locale === "tr" ? "font-serif" : ""}
            style={{ fontWeight: 600, fontSize: 20, letterSpacing: "0.01em" }}
          >
            {dict.app_name}
          </span>
        </Link>

        <nav style={{ display: "flex", alignItems: "center", gap: 2 }}>
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              style={{
                padding: "8px 13px",
                borderRadius: 9,
                fontSize: 15,
                fontWeight: 500,
                color: isActive(item.href, item.exact)
                  ? "var(--accent)"
                  : "var(--text-muted)",
                background: isActive(item.href, item.exact)
                  ? "var(--accent-soft)"
                  : "transparent",
                transition: "all 0.15s",
              }}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div style={{ display: "flex", alignItems: "center", gap: 6, marginInlineStart: 8 }}>
          <div style={{ position: "relative" }}>
            <button
              onClick={() => setLangOpen((v) => !v)}
              aria-label={dict.common.language}
              style={iconBtn}
            >
              <span style={{ fontSize: 14, fontWeight: 600 }}>
                {LOCALE_NAMES[locale]}
              </span>
              <span aria-hidden style={{ fontSize: 10, opacity: 0.6 }}>▼</span>
            </button>
            {langOpen && (
              <div
                style={{
                  position: "absolute",
                  insetInlineEnd: 0,
                  top: 46,
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                  borderRadius: 12,
                  boxShadow: "var(--shadow)",
                  overflow: "hidden",
                  minWidth: 140,
                }}
              >
                {LOCALES.map((l) => (
                  <button
                    key={l}
                    onClick={() => switchLocale(l)}
                    style={{
                      display: "block",
                      width: "100%",
                      textAlign: "start",
                      padding: "10px 14px",
                      fontSize: 15,
                      background: l === locale ? "var(--accent-soft)" : "transparent",
                      color: l === locale ? "var(--accent)" : "var(--text)",
                      border: "none",
                      cursor: "pointer",
                    }}
                  >
                    {LOCALE_NAMES[l]}
                  </button>
                ))}
              </div>
            )}
          </div>

          <button
            onClick={toggle}
            aria-label={theme === "light" ? dict.common.theme_dark : dict.common.theme_light}
            style={iconBtn}
          >
            {theme === "light" ? "🌙" : "☀️"}
          </button>
        </div>
      </div>
    </header>
  );
}

const iconBtn: React.CSSProperties = {
  height: 38,
  minWidth: 38,
  padding: "0 10px",
  borderRadius: 10,
  border: "1px solid var(--border)",
  background: "var(--surface)",
  color: "var(--text)",
  cursor: "pointer",
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  fontSize: 16,
};
