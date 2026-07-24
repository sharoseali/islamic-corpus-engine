import Link from "next/link";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { api } from "@/lib/api";
import { collectionName } from "@/lib/localize";
import { Container, PageTitle, Badge } from "@/components/ui";

export default async function HadithIndex({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const dict = getDictionary(locale);
  const collections = await api.listCollections();

  return (
    <Container className="fade-in">
      <PageTitle title={dict.hadith.title} subtitle={dict.tagline} />
      <div style={{ display: "grid", gap: 14, gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", paddingBottom: 20 }}>
        {collections.map((c) => (
          <Link
            key={c.id}
            href={`/${locale}/hadith/${c.key}`}
            className="card"
            style={{ padding: "24px 26px", display: "block" }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <h3
                className={locale === "ar" || locale === "ur" ? "font-arabic" : ""}
                style={{ fontSize: 20, fontWeight: 700, margin: 0 }}
              >
                {collectionName(c.key, locale)}
              </h3>
              <span aria-hidden style={{ fontSize: 26 }}>☾</span>
            </div>
            <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
              <Badge tone="accent">{c.hadith_count.toLocaleString()} {dict.hadith.hadiths}</Badge>
              <Badge tone="neutral">{c.book_count} {dict.hadith.books}</Badge>
            </div>
          </Link>
        ))}
      </div>
    </Container>
  );
}
