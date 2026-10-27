import Link from "next/link";
import { notFound } from "next/navigation";
import { isLocale, type Locale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { api, hadithLangsFor } from "@/lib/api";
import { collectionName } from "@/lib/localize";
import { Container } from "@/components/ui";
import { HadithCard } from "@/components/hadith-card";

export default async function HadithPermalink({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string; collection: string; number: string }>;
  searchParams: Promise<{ hl?: string }>;
}) {
  const { locale, collection, number } = await params;
  const { hl } = await searchParams;
  if (!isLocale(locale)) notFound();

  const hadith = await api
    .getHadith(collection, number, hadithLangsFor(locale))
    .catch(() => null);
  if (!hadith) notFound();

  const dict = getDictionary(locale);
  const collName = collectionName(collection, locale as Locale);

  return (
    <Container narrow className="fade-in" style={{ paddingBottom: 60 }}>
      <div style={{ marginTop: 28, display: "flex", gap: 14, flexWrap: "wrap" }}>
        <Link href={`/${locale}/hadith`} style={{ color: "var(--text-muted)", fontSize: 14 }}>
          ← {dict.hadith.title}
        </Link>
        <Link
          href={`/${locale}/hadith/${collection}`}
          style={{ color: "var(--text-muted)", fontSize: 14 }}
        >
          {collName}
        </Link>
        {hadith.book_number != null && (
          <Link
            href={`/${locale}/hadith/${collection}/${hadith.book_number}`}
            style={{ color: "var(--text-muted)", fontSize: 14 }}
          >
            {dict.hadith.book} {hadith.book_number}
          </Link>
        )}
      </div>

      <div style={{ margin: "16px 0 22px" }}>
        <h1 style={{ fontSize: 26, fontWeight: 700, margin: 0 }}>
          {collName} - {dict.hadith.number} {hadith.hadith_number}
        </h1>
      </div>

      <HadithCard
        hadith={hadith}
        collectionName={collName}
        collectionKey={collection}
        dict={dict}
        highlight={hl || undefined}
      />
    </Container>
  );
}
