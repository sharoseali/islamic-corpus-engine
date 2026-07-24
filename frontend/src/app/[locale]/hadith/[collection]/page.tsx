import Link from "next/link";
import { notFound } from "next/navigation";
import { isLocale, isRtl } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { api } from "@/lib/api";
import { bookName, collectionName } from "@/lib/localize";
import { Container, PageTitle } from "@/components/ui";

export default async function BooksPage({
  params,
}: {
  params: Promise<{ locale: string; collection: string }>;
}) {
  const { locale, collection } = await params;
  if (!isLocale(locale)) notFound();
  const dict = getDictionary(locale);

  const [collections, books] = await Promise.all([
    api.listCollections(),
    api.listBooks(collection).catch(() => null),
  ]);
  if (!books) notFound();
  const meta = collections.find((c) => c.key === collection);
  void meta;
  const rtl = isRtl(locale);
  const isArabicScript = locale === "ar" || locale === "ur";

  return (
    <Container className="fade-in">
      <div style={{ marginTop: 28 }}>
        <Link href={`/${locale}/hadith`} style={{ color: "var(--text-muted)", fontSize: 14 }}>
          ← {dict.hadith.collections}
        </Link>
      </div>
      <PageTitle title={collectionName(collection, locale)} subtitle={`${dict.hadith.books}`} />
      <div style={{ display: "grid", gap: 10, paddingBottom: 20 }}>
        {books
          .filter((b) => b.hadith_count > 0)
          .map((b) => (
            <Link
              key={b.id}
              href={`/${locale}/hadith/${collection}/${b.number}`}
              className="card"
              style={{
                padding: "14px 18px",
                display: "flex",
                alignItems: "center",
                gap: 14,
              }}
            >
              <span
                style={{
                  minWidth: 34,
                  height: 34,
                  padding: "0 8px",
                  borderRadius: 9,
                  background: "var(--surface-2)",
                  color: "var(--text-muted)",
                  display: "grid",
                  placeItems: "center",
                  fontWeight: 700,
                  fontSize: 14,
                }}
              >
                {b.number}
              </span>
              <span
                className={isArabicScript ? "font-arabic" : ""}
                style={{ flex: 1, fontWeight: 600, fontSize: isArabicScript ? 18 : 15.5 }}
              >
                {bookName(b, locale)}
                {locale === "en" && b.name_arabic && (
                  <span
                    dir="rtl"
                    className="font-arabic"
                    style={{ display: "block", fontWeight: 400, color: "var(--text-faint)", fontSize: 17, marginTop: 2 }}
                  >
                    {b.name_arabic}
                  </span>
                )}
              </span>
              <span style={{ fontSize: 13, color: "var(--text-faint)", textAlign: rtl ? "left" : "right" }}>
                {b.hadith_count} {dict.hadith.hadiths}
              </span>
            </Link>
          ))}
      </div>
    </Container>
  );
}
