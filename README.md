# Elaaj bi Dua · علاج بالدعاء

**Healing through supplication, grounded in authentic sources.**

Elaaj bi Dua is a non-commercial Islamic knowledge platform. Its long-term
purpose is to help scholars (ulama) and seekers find the remedies and duas
that the Quran and the Sunnah teach for the difficulties and illnesses people
face, drawn only from authenticated primary sources and always shown with a
full reference back to the origin.

That end goal depends on one foundation above all others: a corpus that is
authentic to the letter. Before any analysis, recommendation, or "cure"
feature can be trusted, the underlying text of the Quran, the Hadith, and the
Tafsir must be preserved exactly as transmitted, with verifiable provenance.
Building that trustworthy corpus is the first step, and it is the part that is
complete today.

## Authenticity principles

Every part of the system is held to four rules:

1. **Source fidelity.** Original text is stored exactly as published by the
   source. It is never edited, "corrected", or normalized in place.
2. **Complete provenance.** Every verse, hadith, and commentary records the
   source it came from, the exact bytes fetched, a SHA-256 checksum, and when
   it was imported. Any datum can be traced back to its origin.
3. **Deterministic imports.** Re-running an importer on the same source
   produces the same result. Changed upstream content is flagged for review,
   never applied silently.
4. **Separation of concerns.** Original corpus data, derived search data, and
   application data are kept apart. Search and display are rebuilt from the
   canonical text; they never become the source of truth.

## What is built so far

The authentic corpus and the platform to read and search it are in place.

**Corpus (stored verbatim, checksummed, with full provenance):**

- **The Quran**, all 114 surahs and 6,236 ayat in the Uthmani script, from the
  Quran Foundation API (quran.com), with English (Saheeh International) and
  Urdu (Fatah Muhammad Jalandhari) translations aligned ayah by ayah.
- **Sahih al-Bukhari** and **Sahih Muslim**, complete, in Arabic (with full
  chains of narration), Urdu, and English, organized by book (kitab).
- **Tafsir Ibn Kathir**, complete for all 6,236 ayat, in Arabic, Urdu, and
  English, from the Quranic Universal Library (QUL).

**Platform:**

- A PostgreSQL database with domain schemas (quran, hadith, tafsir, search,
  metadata) and a provenance chain on every record.
- A search engine over the whole corpus: ranked full-text search with a
  fuzzy fallback for typos, in Arabic, Urdu, and English, diacritic-insensitive.
- A read-only JSON API (FastAPI) serving the corpus and search.
- A multilingual reading interface (Next.js) in English, Urdu, Arabic, and
  Turkish, with right-to-left support, light and dark themes tuned for long
  reading sessions, and scholarly typography.

## What you can do

Open the app and you can:

- **Read the Quran** surah by surah, with the Arabic ayah, the translation,
  and Tafsir Ibn Kathir shown together and switchable by language.
- **Study Hadith**, browsing Sahih al-Bukhari and Sahih Muslim from collection
  to book (kitab) to individual hadith, each with its Arabic chain of
  narration, translation, reference number, and an authenticity mark.
- **Read Tafsir Ibn Kathir** for any ayah in Arabic, Urdu, or English.
- **Search across everything** in one place. The search understands the
  language of your query: an Arabic-script query finds Arabic (and Urdu)
  content, and results carry a precise reference and link straight to the
  ayah, hadith, or tafsir passage they come from.
- **Copy any passage** with one click. The copy keeps the original script and
  font and appends the source reference, so it can be pasted and shared with
  the citation intact.
- **Choose your language and theme.** The interface is available in English,
  Urdu, Arabic, and Turkish, and opens in Urdu by default. Turkish is a
  UI-only language: the interface is Turkish while the content is shown in
  Arabic, its original source language.

## Architecture

- **Database:** PostgreSQL 16 (run via Docker), with pgvector and pg_trgm.
- **Backend:** Python, SQLAlchemy, Alembic migrations, FastAPI.
- **Frontend:** Next.js (App Router) with TypeScript.
- **Importers:** deterministic pipelines that fetch from a source, checksum
  and archive the raw response, and load it with full provenance.

## Running the platform

See [docs/RUNNING.md](docs/RUNNING.md) for step-by-step instructions to start
the database, the API, and the web interface.

## Roadmap

The corpus foundation is deliberately conservative and correct first. From
here the plan is to widen the sources and then deepen the analysis.

1. **Complete the six canonical collections (Sihah Sittah).** Add Sunan Abi
   Dawud, Jami at-Tirmidhi, Sunan an-Nasa'i, and Sunan Ibn Majah, with their
   gradings, once official access (sunnah.com) is available. The database and
   interface are already designed to receive them.
2. **Add further authenticated works** from recognized scholars, including
   additional tafsir and hadith collections, each held to the same provenance
   and fidelity rules.
3. **Deepen the content analysis.** With a broad, trustworthy corpus in place,
   build the tools that help scholars locate the duas, sunan, and remedies
   taught for a given problem, linking each recommendation back to its exact
   authentic source and grading. This is where the platform's healing purpose
   is realized, on a base that can be trusted.

## Sources and attribution

- Quran text, translations, and tafsir routing: Quran Foundation / quran.com.
- Tafsir Ibn Kathir (complete, three languages): Quranic Universal Library
  (QUL) by Tarteel AI.
- Sahih al-Bukhari and Sahih Muslim: interim mirror pending official
  sunnah.com access, stored with provenance and slated for verification
  against the official source.

All texts are presented with attribution and are stored unmodified. This
project is strictly non-commercial.
