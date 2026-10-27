import type { ReactNode } from "react";

// Match highlighting for search results and readers.
//
// Mirrors the normalisation and light stemming the backend indexes with
// (app/services/text_normalize.py): diacritics removed, letter forms
// unified, dagger alef written out, common prefixes and suffixes stripped.
// Keep the two in step, or highlighted words and matched words will differ.

const AR_MARKS = /[ؐ-ًؚ-ٟۖ-ۭـ]/g;
const UR_MARKS = /[ؐ-ًؚ-ٰٟۖ-ۭـ]/g;
const DAGGER = "ٰ";
const NON_WORD = /[^\p{L}\p{N}]+/gu;

const AR_LETTERS: Record<string, string> = {
  "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي", "ء": "",
  // Urdu keyboard letter forms typed into an Arabic search
  "ی": "ي", "ے": "ي", "ک": "ك", "ہ": "ه", "ۃ": "ه", "ۀ": "ه",
};
const UR_LETTERS: Record<string, string> = {
  "ي": "ی", "ك": "ک", "أ": "ا", "إ": "ا", "آ": "ا", "ة": "ہ", "ۃ": "ہ", "ئ": "ی", "ء": "",
};
const AR_DAGGER_EXCEPTIONS: Record<string, string> = {
  "ذالك": "ذلك", "ذالكم": "ذلكم", "هاذا": "هذا", "هاذه": "هذه", "هاؤلاء": "هؤلاء",
  "لاكن": "لكن", "الرحمان": "الرحمن", "رحمان": "رحمن", "الاه": "اله", "اولائك": "اولئك",
};

// Uthmani orthography written differently in modern spelling (mirror of the
// backend rules): silent waw before a dagger alef (ٱلصَّلَوٰةَ -> الصلاة), alef
// maqsura + dagger + ta marbuta (ٱلتَّوْرَىٰةَ -> التوراة), and the article's lam
// carrying a shadda (ٱلَّيْلِ -> الليل) except in الذي / الذين / التي.
const UTHMANI_RULES: [RegExp, string][] = [
  [/و\u0670(?:ا\u06DF)?/g, "ا"],
  [/ى\u0670ة/g, "اة"],
  [/(^|[\u064B-\u0652])ٱل([\u064B-\u0652]*\u0651[\u064B-\u0652]*)(?![ذت])/g, "$1ٱلل$2"],
];
const uthmaniToModern = (w: string) => UTHMANI_RULES.reduce((acc, [re, to]) => acc.replace(re, to), w);

const AR_PREFIXES = ["وال", "بال", "كال", "فال", "لل", "ال", "و"];
const AR_PRONOUNS = ["هما", "كما", "هم", "هن", "كم", "كن", "نا", "ها", "ك"];
const AR_SUFFIXES = ["ان", "ات", "ون", "ين", "يه", "ه", "ي"];
const UR_SUFFIXES = ["ئیں", "وں", "یں", "ات", "ے", "ہ", "ی"];

const mapLetters = (w: string, map: Record<string, string>) =>
  Array.from(w, (c) => (c in map ? map[c] : c)).join("");

function stripOne(word: string, list: string[], fromStart: boolean): string {
  for (const a of list) {
    if (fromStart ? word.startsWith(a) : word.endsWith(a)) {
      if (word.length - a.length >= 3) return fromStart ? word.slice(a.length) : word.slice(0, -a.length);
    }
  }
  return word;
}

export function arabicStem(w: string): string {
  w = stripOne(w, AR_PREFIXES, true);
  w = stripOne(w, AR_PRONOUNS, false);
  return stripOne(w, AR_SUFFIXES, false);
}

export function urduStem(w: string): string {
  return stripOne(w, UR_SUFFIXES, false);
}

/** All comparable forms (spelling variants and stems) of one word. */
export function wordForms(raw: string, lang: string): string[] {
  // Marks are handled per language first: the dagger alef is a mark but
  // stands for a letter in Arabic, so it must be converted before the
  // generic non-letter strip.
  const word = raw.normalize("NFC");
  if (!word) return [];
  if (lang === "ar") {
    const bare = uthmaniToModern(word).replace(AR_MARKS, "");
    const clean = (w: string) => mapLetters(w, AR_LETTERS).replace(NON_WORD, "");
    const written = clean(bare.replace(new RegExp("ى" + DAGGER, "g"), "ى").replace(new RegExp(DAGGER, "g"), "ا"));
    const forms = [AR_DAGGER_EXCEPTIONS[written] ?? written];
    if (bare.includes(DAGGER)) {
      const dropped = clean(bare.replace(new RegExp(DAGGER, "g"), ""));
      if (!forms.includes(dropped)) forms.push(dropped);
      if (!forms.includes(written)) forms.push(written);
    }
    for (const f of [...forms]) {
      const st = arabicStem(f);
      if (st && !forms.includes(st)) forms.push(st);
    }
    return forms.filter(Boolean);
  }
  if (lang === "ur") {
    const base = mapLetters(word.replace(UR_MARKS, ""), UR_LETTERS).replace(NON_WORD, "");
    if (!base) return [];
    const st = urduStem(base);
    return st === base ? [base] : [base, st];
  }
  const lower = (lang === "tr" ? word.replace(/İ/g, "i").replace(/I/g, "ı").toLowerCase() : word.toLowerCase()).replace(NON_WORD, "");
  return lower ? [lower] : [];
}

function queryForms(query: string, lang: string): string[][] {
  return query
    .split(/\s+/)
    .map((w) => wordForms(w, lang))
    .filter((f) => f.length > 0 && f[0].length >= 2);
}

function matches(displayForms: string[], qforms: string[][], lang: string): boolean {
  for (const group of qforms) {
    for (const q of group) {
      for (const d of displayForms) {
        if (d === q) return true;
        if (lang === "en" || lang === "tr") {
          if (q.length >= 3 && d.startsWith(q)) return true;
        } else if (q.length >= 3 && d.includes(q)) return true;
      }
    }
  }
  return false;
}

/** Highlight words of `text` that match the query; returns React nodes. */
export function highlightText(text: string, query: string | null | undefined, lang: string): ReactNode {
  if (!query || !query.trim()) return text;
  const qforms = queryForms(query, lang);
  if (!qforms.length) return text;
  const parts = text.split(/(\s+)/);
  let any = false;
  const nodes = parts.map((part, i) => {
    if (!part || /^\s+$/.test(part)) return part;
    if (matches(wordForms(part, lang), qforms, lang)) {
      any = true;
      return (
        <mark key={i} className="hl">
          {part}
        </mark>
      );
    }
    return part;
  });
  return any ? nodes : text;
}

/** Same for an HTML string: only text between tags is touched. */
export function highlightHtml(html: string, query: string | null | undefined, lang: string): string {
  if (!query || !query.trim()) return html;
  const qforms = queryForms(query, lang);
  if (!qforms.length) return html;
  return html
    .split(/(<[^>]+>)/)
    .map((seg) => {
      if (!seg || seg.startsWith("<")) return seg;
      return seg
        .split(/(\s+)/)
        .map((part) =>
          part && !/^\s+$/.test(part) && matches(wordForms(part, lang), qforms, lang)
            ? `<mark class="hl">${part}</mark>`
            : part,
        )
        .join("");
    })
    .join("");
}

/** Which language's rules to use for a query against text in `textLang`. */
export function highlightLang(query: string, textLang: string): string | null {
  const arabicScript = /[؀-ۿ]/.test(query);
  if (textLang === "ar" || textLang === "ur") return arabicScript ? textLang : null;
  return arabicScript ? null : textLang;
}

const ARABIC_LETTER = /[\u0621-\u064A\u0671-\u06D3\u06FA-\u06FF]/;
// quran.com writes 37:130 "إِلْ يَاسِينَ" as two tokens; the corpus counts one word.
const JOINED_TOKENS: Record<string, [number, number]> = { "37:130": [3, 4] };

/** Highlight the words at the given 1-based corpus positions of a verse.
 *  Pause marks and other signs between words are not counted. */
export function highlightPositions(text: string, positions: number[], verseKey: string): ReactNode {
  if (!positions.length) return text;
  const want = new Set(positions);
  const join = JOINED_TOKENS[verseKey];
  let next = 1;
  let joined = false;
  let any = false;
  const nodes = text.split(/(\s+)/).map((part, i) => {
    if (!part || /^\s+$/.test(part) || !ARABIC_LETTER.test(part)) return part;
    let pos: number;
    if (join && !joined && next === join[1]) {
      pos = join[0];
      joined = true;
    } else {
      pos = next;
      next += 1;
    }
    if (!want.has(pos)) return part;
    any = true;
    return (
      <mark key={i} className="hl">
        {part}
      </mark>
    );
  });
  return any ? nodes : text;
}
