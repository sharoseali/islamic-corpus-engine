export const LOCALES = ["en", "ur", "ar", "tr"] as const;
export type Locale = (typeof LOCALES)[number];

export const DEFAULT_LOCALE: Locale = "ur";
export const RTL_LOCALES: Locale[] = ["ur", "ar"];

export function isRtl(locale: Locale): boolean {
  return RTL_LOCALES.includes(locale);
}

export function dir(locale: Locale): "rtl" | "ltr" {
  return isRtl(locale) ? "rtl" : "ltr";
}

export const LOCALE_NAMES: Record<Locale, string> = {
  en: "English",
  ur: "اردو",
  ar: "العربية",
  tr: "Türkçe",
};

export function isLocale(value: string): value is Locale {
  return (LOCALES as readonly string[]).includes(value);
}
