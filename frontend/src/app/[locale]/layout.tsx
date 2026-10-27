import type { Metadata } from "next";
import {
  Inter,
  Amiri,
  Noto_Nastaliq_Urdu,
  Noto_Naskh_Arabic,
  Scheherazade_New,
  EB_Garamond,
} from "next/font/google";
import { notFound } from "next/navigation";
import "../globals.css";
import { DEFAULT_LOCALE, LOCALES, dir, isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { Providers } from "@/components/providers";
import { Header } from "@/components/header";
import { Footer } from "@/components/footer";
import { InlineScript } from "@/components/inline-script";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
// Scholarly display serif (Garamond) for Latin headings, like an academic press.
const garamond = EB_Garamond({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  style: ["normal", "italic"],
  variable: "--font-serif",
});
const amiri = Amiri({
  subsets: ["arabic"],
  weight: ["400", "700"],
  variable: "--font-amiri",
});
const nastaliq = Noto_Nastaliq_Urdu({
  subsets: ["arabic"],
  weight: ["400", "500", "700"],
  variable: "--font-nastaliq",
});
// Clean, highly readable Naskh for Arabic UI chrome fallback.
const naskh = Noto_Naskh_Arabic({
  subsets: ["arabic"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-naskh",
});
// Amiri-style classical Naskh with full Urdu coverage, for Urdu text.
const scheherazade = Scheherazade_New({
  subsets: ["arabic"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-scheherazade",
});

export const metadata: Metadata = {
  title: "Elaaj bi Dua - علاج بالدعاء",
  description:
    "An authenticated corpus of Quran, Hadith, and Tafsir with full provenance.",
};

export function generateStaticParams() {
  return LOCALES.map((locale) => ({ locale }));
}

const THEME_INIT = `(function(){try{var t=localStorage.getItem('elaaj-theme');if(!t){t=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';}document.documentElement.setAttribute('data-theme',t);}catch(e){}})();`;

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = getDictionary(locale);

  return (
    <html
      lang={locale}
      dir={dir(locale)}
      data-scroll-behavior="smooth"
      suppressHydrationWarning
      className={`${inter.variable} ${garamond.variable} ${amiri.variable} ${nastaliq.variable} ${naskh.variable} ${scheherazade.variable}`}
    >
      <head>
        <InlineScript html={THEME_INIT} />
      </head>
      <body>
        <Providers locale={locale} dict={dict}>
          <Header />
          <main>{children}</main>
          <Footer />
        </Providers>
      </body>
    </html>
  );
}

export const dynamicParams = false;
void DEFAULT_LOCALE;
