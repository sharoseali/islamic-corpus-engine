import Link from "next/link";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { Container } from "@/components/ui";
import { HomeSearch } from "@/components/home-search";
import {
  BookMark,
  ChainMark,
  GirihBand,
  GirihField,
  MihrabArch,
  PagesMark,
  SideArch,
  StarMark,
} from "@/components/ornament";
import { Ticker } from "@/components/ticker";
import { notFound } from "next/navigation";

export default async function HomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const dict = getDictionary(locale);
  const isArabicScript = locale === "ar" || locale === "ur";

  const cards = [
    {
      href: `/${locale}/quran`,
      title: dict.home.card_quran,
      desc: dict.home.card_quran_desc,
      icon: <BookMark size={30} />,
    },
    {
      href: `/${locale}/hadith`,
      title: dict.home.card_hadith,
      desc: dict.home.card_hadith_desc,
      icon: <ChainMark size={30} />,
    },
    {
      href: `/${locale}/tafsir`,
      title: dict.home.card_tafsir,
      desc: dict.home.card_tafsir_desc,
      icon: <PagesMark size={30} />,
    },
  ];

  return (
    <div className="fade-in home">
      {/* One continuous girih field behind the whole page, down to the footer */}
      <GirihField className="page-girih" patternId="girih-page" />
      {/* Manuscript hero: mosque facade (central mihrab + flanking arches) */}
      <section className="hero">
        <div className="hero-sides" aria-hidden>
          <div className="hero-side hero-side-left">
            <SideArch />
          </div>
          <div className="hero-side hero-side-right">
            <SideArch />
          </div>
        </div>
        <div className="hero-frame">
          <MihrabArch />
          <div className="hero-content">
          <div style={{ marginBottom: 12 }}>
            <StarMark size={38} />
          </div>
          <div className="hero-name">
            <span className="font-serif hero-name-en">Elaaj bi Dua</span>
            <span className="hero-name-dot" aria-hidden>
              ·
            </span>
            <span className="font-arabic hero-name-ar" dir="rtl">
              علاج بالدعاء
            </span>
          </div>
          <div className="hero-rule" aria-hidden />
          <h1
            style={{
              fontSize: isArabicScript ? 33 : 44,
              fontWeight: isArabicScript ? 700 : 500,
              margin: "0 auto 14px",
              maxWidth: 500,
              lineHeight: isArabicScript ? 1.8 : 1.15,
            }}
          >
            {dict.home.hero_title}
          </h1>
          <p
            style={{
              fontSize: 16.5,
              color: "var(--text-muted)",
              maxWidth: 500,
              margin: "0 auto 24px",
              lineHeight: isArabicScript ? 1.95 : 1.65,
            }}
          >
            {dict.home.hero_sub}
          </p>
          <HomeSearch />
          </div>
        </div>
        <div className="hero-band" aria-hidden>
          <GirihBand height={30} opacity={0.5} />
        </div>
      </section>

      {/* Feature ticker */}
      <Ticker items={dict.home.ticker} />

      {/* Cards sit on the continuous girih backdrop */}
      <section className="cards-section">
        <Container style={{ maxWidth: 1100, position: "relative", zIndex: 1 }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: 18,
            }}
          >
            {cards.map((c) => (
              <Link key={c.href} href={c.href} className="card manuscript-card" style={cardStyle}>
                <span className="card-corner card-corner-tl" aria-hidden />
                <span className="card-corner card-corner-br" aria-hidden />
                <div style={{ marginBottom: 16 }}>{c.icon}</div>
                <h3 style={{ fontSize: 20, fontWeight: 600, margin: "0 0 6px" }}>
                  {c.title}
                </h3>
                <p style={{ color: "var(--text-muted)", margin: 0, fontSize: 15, lineHeight: 1.6 }}>
                  {c.desc}
                </p>
              </Link>
            ))}
          </div>
        </Container>
      </section>
    </div>
  );
}

const cardStyle: React.CSSProperties = {
  padding: "28px 26px",
  display: "block",
  transition: "transform 0.18s, box-shadow 0.18s, border-color 0.18s",
};
