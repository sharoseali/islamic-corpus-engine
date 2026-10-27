export type Chapter = {
  id: number;
  name_arabic: string;
  name_simple: string;
  name_complex: string;
  translated_name: string | null;
  revelation_place: "makkah" | "madinah";
  revelation_order: number;
  verses_count: number;
  bismillah_pre: boolean;
};

export type Translation = {
  resource_id: number;
  language_code: string;
  resource_name: string;
  text: string;
};

export type TafsirEntry = {
  edition_id: number;
  language_code: string;
  edition_name: string;
  text: string;
};

export type VerseDetail = {
  id: number;
  verse_key: string;
  verse_number: number;
  text_uthmani: string;
  juz_number: number;
  page_number: number | null;
  translations: Translation[];
  tafsir: TafsirEntry[];
};

export type HadithCollection = {
  id: number;
  key: string;
  name: string;
  name_arabic: string | null;
  hadith_count: number;
  book_count: number;
};

export type HadithBook = {
  id: number;
  number: number;
  name: string | null;
  name_arabic: string | null;
  name_urdu: string | null;
  hadith_count: number;
};

export type HadithText = { language_code: string; text: string };

export type HadithListItem = {
  id: number;
  hadith_number: string;
  arabic_number: string | null;
  book_number: number | null;
  book_name: string | null;
  grades: unknown[] | null;
  texts: HadithText[];
};

export type HadithDetail = HadithListItem & {
  collection_key: string;
  collection_name: string;
};

export type SearchHit = {
  doc_type: "quran_verse" | "quran_translation" | "hadith_text" | "tafsir_entry";
  language_code: string;
  collection_key: string;
  citation: string;
  source_row_id: number;
  text: string;
  score: number;
  match: "fulltext" | "partial" | "fuzzy" | "semantic";
  ref: Record<string, unknown>;
  snippet?: string | null;
  snippet_start?: number | null;
  snippet_end?: number | null;
};

export type SearchResponse = {
  query: string;
  language_code: string;
  mode?: string;
  offset?: number;
  total: number;
  counts?: { quran?: number; hadith?: number; tafsir?: number };
  hits: SearchHit[];
};

export type VerseHit = {
  verse_key: string;
  chapter_id: number;
  verse_number: number;
  chapter_name_simple: string;
  chapter_name_arabic: string;
  text_uthmani: string;
  translation_text: string | null;
  translation_resource: string | null;
  translation_language: string | null;
  matched_in: string[];
  score: number;
  matched_words: number[];
};

export type MorphologyTerm = {
  word: string;
  kind: "root" | "form";
  label: string;
  verses: number;
  words: number;
};

export type AyahThemeHit = {
  theme: string;
  chapter_id: number;
  chapter_name_simple: string;
  chapter_name_arabic: string;
  ayah_from: number;
  ayah_to: number;
};

export type QuranSearchResponse = {
  query: string;
  languages: string[];
  order: string;
  offset: number;
  total: number;
  semantic_extra: number;
  morphology: MorphologyTerm[];
  themes: AyahThemeHit[];
  items: VerseHit[];
};

export type ResourceInfo = {
  id: number;
  language_code: string;
  name: string;
  author_name?: string | null;
  slug?: string | null;
};
