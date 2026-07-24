import Link from "next/link";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { api } from "@/lib/api";
import { Container, PageTitle } from "@/components/ui";

export default async function TafsirIndex({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const dict = getDictionary(locale);
  const chapters = await api.listChapters();

  return (
    <Container className="fade-in">
      <PageTitle title={dict.tafsir.title} subtitle={dict.tafsir.intro} />
      <p style={{ color: "var(--text-faint)", marginTop: -18, marginBottom: 24, fontSize: 14 }}>
        {dict.tafsir.by_ibn_kathir} · {dict.tafsir.select_surah}
      </p>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(230px, 1fr))",
          gap: 10,
          paddingBottom: 20,
        }}
      >
        {chapters.map((c) => (
          <Link
            key={c.id}
            href={`/${locale}/tafsir/${c.id}`}
            className="card"
            style={{ padding: "13px 16px", display: "flex", alignItems: "center", gap: 12 }}
          >
            <span
              style={{
                minWidth: 32,
                height: 32,
                borderRadius: 8,
                background: "var(--surface-2)",
                color: "var(--text-muted)",
                display: "grid",
                placeItems: "center",
                fontWeight: 700,
                fontSize: 13,
              }}
            >
              {c.id}
            </span>
            <span style={{ flex: 1, fontWeight: 600, fontSize: 15 }}>{c.name_simple}</span>
            <span className="font-arabic" style={{ fontSize: 18 }}>
              {c.name_arabic}
            </span>
          </Link>
        ))}
      </div>
    </Container>
  );
}
