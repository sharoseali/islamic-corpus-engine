import { notFound } from "next/navigation";
import Link from "next/link";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { api } from "@/lib/api";
import { Container } from "@/components/ui";
import { QuranReader } from "@/components/quran-reader";

export default async function ChapterPage({
  params,
}: {
  params: Promise<{ locale: string; chapter: string }>;
}) {
  const { locale, chapter } = await params;
  if (!isLocale(locale)) notFound();
  const chapterId = Number(chapter);
  if (!Number.isInteger(chapterId) || chapterId < 1 || chapterId > 114) notFound();

  const dict = getDictionary(locale);
  const [meta, translations, tafsirs] = await Promise.all([
    api.getChapter(chapterId),
    api.listTranslations(),
    api.listTafsirs(),
  ]);

  return (
    <Container narrow className="fade-in" style={{ paddingBottom: 60 }}>
      <div style={{ margin: "28px 0 8px", display: "flex", alignItems: "center", gap: 12 }}>
        <Link
          href={`/${locale}/quran`}
          style={{ color: "var(--text-muted)", fontSize: 14 }}
        >
          ← {dict.quran.surahs}
        </Link>
      </div>
      <div style={{ textAlign: "center", margin: "8px 0 24px" }}>
        <div className="font-arabic" style={{ fontSize: 40, fontWeight: 700 }}>
          {meta.name_arabic}
        </div>
        {locale === "en" && (
          <div style={{ fontSize: 18, fontWeight: 600, marginTop: 2 }}>
            {meta.name_simple}
            {meta.translated_name ? (
              <span style={{ color: "var(--text-faint)", fontWeight: 400 }}>
                {" "}· {meta.translated_name}
              </span>
            ) : null}
          </div>
        )}
        <div style={{ color: "var(--text-faint)", fontSize: 13.5, marginTop: 4 }}>
          {meta.verses_count} {dict.quran.verses}
        </div>
      </div>

      <QuranReader
        chapterId={chapterId}
        translations={translations}
        tafsirs={tafsirs}
        bismillah={meta.bismillah_pre}
      />
    </Container>
  );
}
