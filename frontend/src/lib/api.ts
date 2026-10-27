import type {
  Chapter,
  HadithBook,
  HadithCollection,
  HadithDetail,
  HadithListItem,
  QuranSearchResponse,
  ResourceInfo,
  SearchResponse,
  VerseDetail,
} from "./types";

// On the server, call the backend directly. In the browser, use the
// same-origin /api/v1 path that next.config.ts rewrites to the backend, so
// the site also works from phones and other devices on the network.
export const API_BASE =
  typeof window === "undefined"
    ? (process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8400/api/v1")
    : "/api/v1";

async function get<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...opts,
    headers: { Accept: "application/json", ...(opts?.headers ?? {}) },
    // Content rarely changes; cache for a day, revalidate in background.
    next: { revalidate: 86400 },
  });
  if (!res.ok) {
    throw new Error(`API ${res.status} for ${path}`);
  }
  return res.json() as Promise<T>;
}

// Content is available in Arabic, Urdu, English. Turkish is a UI-only
// language: Turkish users see Arabic content (the original sources).
export const CONTENT_LANG_FALLBACK: Record<string, string> = {
  en: "en",
  ur: "ur",
  ar: "ar",
  tr: "ar",
};

// Which hadith text languages to display for a given UI locale.
export function hadithLangsFor(locale: string): string {
  if (locale === "tr" || locale === "ar") return "ar";
  if (locale === "ur") return "ar,ur";
  return "ar,en";
}

export const api = {
  listChapters: () => get<Chapter[]>("/quran/chapters"),
  getChapter: (id: number) => get<Chapter>(`/quran/chapters/${id}`),
  getChapterVerses: (
    id: number,
    translationIds: number[],
    tafsirIds: number[],
    range?: { from: number; to: number },
  ) => {
    const params = new URLSearchParams();
    if (translationIds.length) params.set("translations", translationIds.join(","));
    if (tafsirIds.length) params.set("tafsir", tafsirIds.join(","));
    if (range) {
      params.set("from_ayah", String(range.from));
      params.set("to_ayah", String(range.to));
    }
    const qs = params.toString();
    return get<VerseDetail[]>(
      `/quran/chapters/${id}/verses${qs ? `?${qs}` : ""}`,
    );
  },
  listTranslations: () => get<ResourceInfo[]>("/quran/resources/translations"),
  listTafsirs: () => get<ResourceInfo[]>("/quran/resources/tafsirs"),

  listCollections: () => get<HadithCollection[]>("/hadith/collections"),
  listBooks: (key: string) => get<HadithBook[]>(`/hadith/collections/${key}/books`),
  listHadiths: (key: string, book: number, langs: string) =>
    get<HadithListItem[]>(
      `/hadith/collections/${key}/books/${book}/hadiths?langs=${langs}`,
    ),
  getHadith: (key: string, number: string, langs: string) =>
    get<HadithDetail>(
      `/hadith/collections/${key}/hadiths/${encodeURIComponent(number)}?langs=${langs}`,
    ),

  search: (
    q: string,
    langs: string | string[],
    opts?: {
      types?: string;
      collections?: string;
      limit?: number;
      offset?: number;
      mode?: "keyword" | "semantic" | "hybrid";
      rerank?: boolean;
      withCounts?: boolean;
    },
  ) => {
    const params = new URLSearchParams({ q, langs: Array.isArray(langs) ? langs.join(",") : langs });
    if (opts?.types) params.set("types", opts.types);
    if (opts?.collections) params.set("collections", opts.collections);
    if (opts?.limit) params.set("limit", String(opts.limit));
    if (opts?.offset) params.set("offset", String(opts.offset));
    if (opts?.mode) params.set("mode", opts.mode);
    if (opts?.rerank === false) params.set("rerank", "false");
    if (opts?.withCounts) params.set("with_counts", "true");
    return get<SearchResponse>(`/search?${params.toString()}`, {
      next: { revalidate: 0 },
    });
  },

  // Verse-centric Quran search: every ayah where the words occur.
  searchQuran: (
    q: string,
    langs: string[],
    opts?: {
      translation?: string;
      order?: "mushaf" | "relevance";
      limit?: number;
      offset?: number;
      mode?: "keyword" | "semantic" | "hybrid";
    },
  ) => {
    const params = new URLSearchParams({ q, langs: langs.join(",") });
    if (opts?.translation) params.set("translation", opts.translation);
    if (opts?.order) params.set("order", opts.order);
    if (opts?.limit) params.set("limit", String(opts.limit));
    if (opts?.offset) params.set("offset", String(opts.offset));
    if (opts?.mode) params.set("mode", opts.mode);
    return get<QuranSearchResponse>(`/search/quran?${params.toString()}`, {
      next: { revalidate: 0 },
    });
  },
};
