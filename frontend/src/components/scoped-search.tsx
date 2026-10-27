"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useI18n } from "./providers";
import { SearchField } from "./search-field";

// Search bar on the Quran, Hadith and Tafsir pages: searches only that
// scope and opens the results page on the matching tab.
export function ScopedSearch({ scope }: { scope: "quran" | "hadith" | "tafsir" }) {
  const { locale, dict } = useI18n();
  const router = useRouter();
  const [q, setQ] = useState("");
  const placeholder = {
    quran: dict.results.search_in_quran,
    hadith: dict.results.search_in_hadith,
    tafsir: dict.results.search_in_tafsir,
  }[scope];

  const submit = () => {
    if (q.trim()) {
      router.push(`/${locale}/search?q=${encodeURIComponent(q.trim())}&scope=${scope}`);
    }
  };

  return (
    <div className="scoped-search">
      <SearchField value={q} onChange={setQ} onSubmit={submit} variant="page" placeholder={placeholder} />
    </div>
  );
}
