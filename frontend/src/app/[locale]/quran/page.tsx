import Link from "next/link";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { api } from "@/lib/api";
import { Container, PageTitle, Badge } from "@/components/ui";
import { ScopedSearch } from "@/components/scoped-search";

export default async function QuranIndex({
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
      <PageTitle title={dict.quran.title} subtitle={dict.tagline} />
      <ScopedSearch scope="quran" />
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: 12,
          paddingBottom: 20,
        }}
      >
        {chapters.map((c) => (
          <Link
            key={c.id}
            href={`/${locale}/quran/${c.id}`}
            className="card"
            style={{ padding: "16px 18px", display: "flex", alignItems: "center", gap: 14 }}
          >
            <div
              style={{
                width: 40,
                height: 40,
                flexShrink: 0,
                borderRadius: 10,
                background: "var(--accent-soft)",
                color: "var(--accent)",
                display: "grid",
                placeItems: "center",
                fontWeight: 700,
                fontSize: 15,
              }}
            >
              {c.id}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                <span style={{ fontWeight: 700, fontSize: 15.5 }}>{c.name_simple}</span>
                <span className="font-arabic" style={{ fontSize: 20, color: "var(--text)" }}>
                  {c.name_arabic}
                </span>
              </div>
              <div style={{ display: "flex", gap: 6, marginTop: 5, alignItems: "center" }}>
                <Badge tone={c.revelation_place === "makkah" ? "gold" : "accent"}>
                  {c.revelation_place === "makkah"
                    ? dict.quran.revelation_makkah
                    : dict.quran.revelation_madinah}
                </Badge>
                <span style={{ fontSize: 12.5, color: "var(--text-faint)" }}>
                  {c.verses_count} {dict.quran.verses}
                </span>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </Container>
  );
}
