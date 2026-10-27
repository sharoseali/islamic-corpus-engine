import { notFound } from "next/navigation";
import Link from "next/link";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { api } from "@/lib/api";
import { Container } from "@/components/ui";
import { TafsirReader } from "@/components/tafsir-reader";

export default async function TafsirChapterPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string; chapter: string }>;
  searchParams: Promise<{ ayah?: string; hl?: string }>;
}) {
  const { locale, chapter } = await params;
  const { ayah, hl } = await searchParams;
  if (!isLocale(locale)) notFound();
  const chapterId = Number(chapter);
  if (!Number.isInteger(chapterId) || chapterId < 1 || chapterId > 114) notFound();

  const dict = getDictionary(locale);
  const [meta, tafsirs] = await Promise.all([
    api.getChapter(chapterId),
    api.listTafsirs(),
  ]);

  return (
    <Container narrow className="fade-in" style={{ paddingBottom: 60 }}>
      <div style={{ margin: "28px 0 4px" }}>
        <Link href={`/${locale}/tafsir`} style={{ color: "var(--text-muted)", fontSize: 14 }}>
          ← {dict.tafsir.title}
        </Link>
      </div>

      <TafsirReader
        meta={meta}
        tafsirs={tafsirs}
        initialAyah={ayah && /^\d+$/.test(ayah) ? Number(ayah) : undefined}
        highlightQuery={hl || undefined}
      />
    </Container>
  );
}
