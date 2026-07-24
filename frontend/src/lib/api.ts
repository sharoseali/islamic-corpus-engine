import type {
  Chapter,
  HadithBook,
  HadithCollection,
  HadithDetail,
  HadithListItem,
  ResourceInfo,
  SearchResponse,
  VerseDetail,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000/api/v1";

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
  ) => {
    const params = new URLSearchParams();
    if (translationIds.length) params.set("translations", translationIds.join(","));
    if (tafsirIds.length) params.set("tafsir", tafsirIds.join(","));
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
    lang: string,
    opts?: { types?: string; collections?: string; limit?: number },
  ) => {
    const params = new URLSearchParams({ q, lang });
    if (opts?.types) params.set("types", opts.types);
    if (opts?.collections) params.set("collections", opts.collections);
    if (opts?.limit) params.set("limit", String(opts.limit));
    return get<SearchResponse>(`/search?${params.toString()}`, {
      next: { revalidate: 0 },
    });
  },
};
