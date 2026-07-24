"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useI18n } from "./providers";

export function HomeSearch() {
  const { locale, dict } = useI18n();
  const router = useRouter();
  const [q, setQ] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (q.trim()) {
      router.push(`/${locale}/search?q=${encodeURIComponent(q.trim())}`);
    }
  };

  return (
    <form onSubmit={submit} style={{ maxWidth: 500, margin: "0 auto" }}>
      <div
        style={{
          display: "flex",
          gap: 8,
          background: "var(--surface)",
          border: "1px solid var(--border-strong)",
          borderRadius: 14,
          padding: 6,
          boxShadow: "var(--shadow)",
        }}
      >
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={dict.search.placeholder}
          aria-label={dict.search.button}
          style={{
            flex: 1,
            border: "none",
            outline: "none",
            background: "transparent",
            color: "var(--text)",
            fontSize: 16,
            padding: "10px 14px",
            fontFamily: "inherit",
          }}
        />
        <button type="submit" style={primaryBtn}>
          {dict.search.button}
        </button>
      </div>
    </form>
  );
}

export const primaryBtn: React.CSSProperties = {
  background: "var(--accent)",
  color: "#fff",
  border: "none",
  borderRadius: 10,
  padding: "10px 22px",
  fontSize: 15,
  fontWeight: 600,
  cursor: "pointer",
  fontFamily: "inherit",
};
