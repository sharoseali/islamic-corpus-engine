# Running Elaaj (v1.0.0)

The platform has three parts: PostgreSQL (Docker), the FastAPI backend, and
the Next.js frontend.

## 1. Database

```bash
docker compose up -d          # PostgreSQL 16 on host port 5433
```

Data is already imported (Quran, Bukhari, Muslim, Tafsir Ibn Kathir) and the
search index is built. To rebuild the search index after new imports:

```bash
qlib/bin/python -m app.services.search_indexer
```

## 2. Backend API (FastAPI)

```bash
qlib/bin/uvicorn app.main:app --host 127.0.0.1 --port 8400
```

- Interactive API docs: http://127.0.0.1:8400/docs
- Health: http://127.0.0.1:8400/api/v1/health

## 3. Frontend (Next.js)

```bash
cd frontend
npm install          # first time only
npm run dev          # development, http://localhost:3400
# or for production:
npm run build && npm run start
```

The frontend reads `NEXT_PUBLIC_API_BASE` from `frontend/.env.local`
(defaults to `http://127.0.0.1:8400/api/v1`).

## Languages & routes

UI is available in English, Urdu, Arabic, and Turkish. The URL carries the
locale: `/en`, `/ur`, `/ar`, `/tr`. Urdu and Arabic render right-to-left.
Content (translations, tafsir) is served in Arabic, Urdu, and English.
Turkish is a UI-only language: Turkish users read the Arabic source content
(hadith, tafsir) with a fully Turkish interface.

Surfaces:
- `/{locale}` - home + search
- `/{locale}/quran` → `/{locale}/quran/{surah}` - aligned reader
- `/{locale}/hadith` → `/{collection}` → `/{book}` - hadith browser
- `/{locale}/tafsir` → `/{surah}` - Tafsir Ibn Kathir reader
- `/{locale}/search` - unified search
