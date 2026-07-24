import type { Locale } from "@/i18n/config";
import type { Chapter, HadithBook } from "./types";

// Localized collection titles (DB stores English + Arabic only).
export const COLLECTION_NAMES: Record<string, Record<Locale, string>> = {
  bukhari: {
    en: "Sahih al-Bukhari",
    ur: "صحیح بخاری",
    ar: "صحيح البخاري",
    tr: "Sahih-i Buhari",
  },
  muslim: {
    en: "Sahih Muslim",
    ur: "صحیح مسلم",
    ar: "صحيح مسلم",
    tr: "Sahih-i Müslim",
  },
};

export function collectionName(key: string, locale: Locale): string {
  return COLLECTION_NAMES[key]?.[locale] ?? key;
}

// Quran surah name: English transliteration for `en`, Arabic script otherwise.
export function chapterName(ch: Chapter, locale: Locale): string {
  return locale === "en" ? ch.name_simple : ch.name_arabic;
}

// Hadith kitab name: English for `en`, Arabic (now enriched) otherwise.
export function bookName(b: HadithBook, locale: Locale): string {
  if (locale === "en") return b.name ?? b.name_arabic ?? "";
  return b.name_arabic ?? b.name ?? "";
}

export function surahOf(verseKey: string): string {
  return verseKey.split(":")[0];
}

export function verseAnchor(verseKey: string): string {
  return `ayah-${verseKey.replace(":", "_")}`;
}
