"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useI18n } from "./providers";
import { SearchField } from "./search-field";

export function HomeSearch() {
  const { locale } = useI18n();
  const router = useRouter();
  const [q, setQ] = useState("");

  const submit = () => {
    if (q.trim()) {
      router.push(`/${locale}/search?q=${encodeURIComponent(q.trim())}`);
    }
  };

  return <SearchField value={q} onChange={setQ} onSubmit={submit} variant="hero" />;
}
