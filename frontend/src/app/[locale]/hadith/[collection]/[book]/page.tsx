import Link from "next/link";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { api, hadithLangsFor } from "@/lib/api";
import { bookName, collectionName } from "@/lib/localize";
import { Container } from "@/components/ui";
import { HadithCard } from "@/components/hadith-card";

export default async function HadithListPage({
  params,
}: {
  params: Promise<{ locale: string; collection: string; book: string }>;
}) {
  const { locale, collection, book } = await params;
  if (!isLocale(locale)) notFound();
  const dict = getDictionary(locale);
  const bookNumber = Number(book);

  const [collections, books, hadiths] = await Promise.all([
    api.listCollections(),
    api.listBooks(collection).catch(() => []),
    api.listHadiths(collection, bookNumber, hadithLangsFor(locale)).catch(() => null),
  ]);
  if (!hadiths) notFound();

  const meta = collections.find((c) => c.key === collection);
  const bookMeta = books.find((b) => b.number === bookNumber);
  const collName = collectionName(collection, locale);
  const displayBookName = bookMeta
    ? bookName(bookMeta, locale)
    : `${dict.hadith.book} ${bookNumber}`;
  const isArabicScript = locale === "ar" || locale === "ur";

  return (
    <Container narrow className="fade-in" style={{ paddingBottom: 60 }}>
      <div style={{ marginTop: 28 }}>
        <Link
          href={`/${locale}/hadith/${collection}`}
          style={{ color: "var(--text-muted)", fontSize: 14 }}
        >
          ← {collName}
        </Link>
      </div>
      <div style={{ margin: "12px 0 24px" }}>
        <h1
          className={isArabicScript ? "font-arabic" : ""}
          style={{ fontSize: 26, fontWeight: 700, margin: 0 }}
        >
          {displayBookName}
        </h1>
        {locale === "en" && bookMeta?.name_arabic && (
          <p dir="rtl" className="font-arabic" style={{ margin: "4px 0 0", fontSize: 22, color: "var(--text-muted)" }}>
            {bookMeta.name_arabic}
          </p>
        )}
        <p style={{ color: "var(--text-faint)", fontSize: 13.5, margin: "6px 0 0" }}>
          {collName} · {hadiths.length} {dict.hadith.hadiths}
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {hadiths.map((h) => (
          <HadithCard
            key={h.id}
            hadith={h}
            collectionName={collName}
            collectionKey={collection}
            dict={dict}
          />
        ))}
      </div>
    </Container>
  );
}
