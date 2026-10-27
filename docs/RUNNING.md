# Running Elaaj (v1.0.0)

The platform has three parts: PostgreSQL (Docker), the FastAPI backend and
the Next.js frontend. This guide is for a developer on any machine; the
commands assume a Python virtual environment is activated (its name does
not matter; on the original development PC it is called `qlib`).

## 0. First-time setup

Requirements: Docker with Compose v2, Python 3.12, Node.js 20 or newer,
`ffmpeg` (only for voice search), and for the GPU option an NVIDIA card.

```bash
git clone https://github.com/sharoseali/islamic-corpus-engine.git
cd islamic-corpus-engine
cp .env.example .env               # set POSTGRES_PASSWORD; see the comments
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
docker compose up -d               # PostgreSQL 16 on host port 5433
alembic upgrade head               # creates the schemas and tables
cd frontend && npm install && cd ..
```

### Getting the data

A fresh database is empty. There are two ways to fill it.

**From a release bundle** (minutes; this is what a server gets, see
`docs/DEPLOYMENT.md`). Ask the maintainer for the bundle directory, then:

```bash
docker cp <bundle>/db.dump ikc_postgres:/tmp/db.dump
docker exec ikc_postgres pg_restore -U ice_admin -d islamic_corpus \
  --no-owner --no-privileges --clean --if-exists --jobs=4 /tmp/db.dump
mkdir -p corpus/cache/models && tar -xf <bundle>/models.tar -C corpus/cache/models
tar -xf <bundle>/original.tar -C corpus
```

**From the sources** (hours; the Quran importer needs Quran Foundation API
credentials in `.env`, `QF_CLIENT_ID` and `QF_CLIENT_SECRET`):

```bash
python -m app.pipelines.quran.importer        # Quran text + translations (quran.com)
python -m app.pipelines.hadith.importer       # Sahih al-Bukhari, Sahih Muslim (pinned mirror)
python -m app.pipelines.tafsir.qul_importer   # Tafsir Ibn Kathir ar/ur/en (QUL)
python -m app.pipelines.quran.morphology      # roots/lemmas/stems (QUL files, see below)
python -m app.pipelines.quran.themes          # ayah themes (QUL file, see below)
python -m app.services.search_indexer         # keyword index + spelling vocabulary
python -m app.services.embedding_indexer      # embeddings: 2 h on a GPU, 8 to 12 h on CPU
```

Every importer archives the raw bytes under `corpus/original/` with
checksums and writes a manifest under `corpus/manifests/`; re-running one
is safe and idempotent.

## 1. Database

```bash
docker compose up -d          # PostgreSQL 16 on host port 5433
```

To rebuild the search index after new imports (keeps the embeddings):

```bash
python -m app.services.search_indexer
```

## 2. Backend API (FastAPI)

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8400
```

- Interactive API docs: http://127.0.0.1:8400/docs
- Health: http://127.0.0.1:8400/api/v1/health (checks the database)

## 3. Frontend (Next.js)

```bash
cd frontend
npm run dev          # development, http://localhost:3400
# or for production:
npm run build && npm run start
```

The frontend reads `NEXT_PUBLIC_API_BASE` from `frontend/.env.local`
(defaults to `http://127.0.0.1:8400/api/v1`).

The browser calls `/api/v1/...` on the frontend's own origin, and Next.js
forwards it to the backend (`rewrites` in `frontend/next.config.ts`). This is
what lets phones and other devices on the network use the site. No page is
prerendered at build time, so `npm run build` works without the API.

## Voice search (optional)

Chrome, Edge and Safari use their built-in speech engine. Other browsers
(Firefox, Brave) record the clip and send it to the backend, which
transcribes it offline with Whisper. The machine needs `ffmpeg`
(`sudo apt install ffmpeg`):

```bash
# Pre-download the model once (about 480 MB) so the first request is fast:
python -c "from app.services.speech import _get_model; _get_model()"
```

Set `WHISPER_MODEL` in `.env` (`small` by default; `medium` is more accurate
for Urdu but slower). Browsers allow the microphone only on `localhost` or
HTTPS, not on `http://192.168.x.x`.

## Quran morphology (roots, lemmas, stems)

Word-level morphology of the Quranic Arabic Corpus, as distributed by QUL
(qul.tarteel.ai, "Morphology", the three "Word by word" resources in SQLite:
Word root, Word lemma, Word stem). Download them while signed in and place
the archives unchanged in `corpus/original/qul/morphology/`, then:

```bash
python -m app.pipelines.quran.morphology
```

The importer archives the files with checksums (manifest under
`corpus/manifests/qul/`), aligns every word to `quran.verses.text_uthmani`
by position (pause marks are not words; 37:130 is one word written as two
tokens) and refuses any other disagreement. Stray entries at positions that
do not exist in the source file are skipped and listed in the run stats.
Verse search then answers Arabic words by root (صبر lists every form of
ص ب ر) or by dictionary form (الصابرين), with the matched words marked.

Ayah themes (QUL "Ayah theme", English, "Ayah by Ayah") go to
`corpus/original/qul/topics/ayah-themes.db.zip` and are imported with:

```bash
python -m app.pipelines.quran.themes
```

English queries on the Quran tab then also list matching themes as links
into the reader ("usury" -> Prohibition of usury, 2:275-276). The published
file repeats about half its rows; the import keeps them as published and
search returns each theme once.

## Semantic search (open source, offline)

Search is hybrid: keyword matching plus meaning-based retrieval over
embeddings stored in `search.chunks` (pgvector). The models are open source
and run locally; nothing is sent anywhere and nothing from a model is ever
shown to a user: they only choose and order our own stored passages.

- Embedding model: `intfloat/multilingual-e5-large` as plain ONNX files in
  `corpus/cache/models/<EMBEDDING_MODEL_DIR>/` (`model.onnx`, `tokenizer.json`
  and config files). Not committed (2.2 GB); the sha256 of every file in use
  is recorded in `search.embedding_state`. The release bundle carries it.
- Reranker: `BAAI/bge-reranker-v2-m3` via fastembed, in the same directory
  (plain dirs `bge-reranker-v2-m3-fp32`, `-fp16` for a GPU, `-int8`).
- Settings (`.env`): `EMBEDDING_MODEL_DIR` (default `e5-large-fp32`),
  `EMBEDDING_THREADS` (default 16), `RERANKER_MODEL`, `RERANKER_MODEL_DIR`,
  `RERANK_CANDIDATES` (how many candidates the reranker re-orders; 0 turns
  it off).

Build or resume the embeddings (safe to interrupt and re-run, it continues
where it stopped):

```bash
python -m app.services.embedding_indexer
```

Re-running the keyword indexer (`app.services.search_indexer`) keeps the
embeddings: documents are updated in place and only chunks of changed texts
are dropped. It also refreshes `search.vocabulary` (every index word per
language), which the spelling fallback matches misspelled query words
against ("shaytaan", "patiense", "seytan") in a few milliseconds. The API
takes `mode=keyword|semantic|hybrid` (default hybrid) and
`rerank=true|false` on `/api/v1/search`; without embeddings it falls back
to keyword results.

### GPU (optional)

The embedding model runs on a CUDA GPU when `onnxruntime-gpu` is installed
and `EMBEDDING_DEVICE` is `auto` (default) or `cuda`; otherwise it uses the
CPU. GPU vectors are computed in full 32-bit precision (TF32 off), so a build
started on the CPU can continue on the GPU and vice versa. Installing the
CUDA 12 build (the PyPI default is a CUDA 13 build and needs driver 580+):

```bash
pip uninstall -y onnxruntime fastembed
pip install onnxruntime-gpu==1.29.0 \
  --index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/
pip install fastembed-gpu
# CUDA libraries: either pip install them into the venv ...
pip install "nvidia-cuda-runtime-cu12~=12.0" "nvidia-cuda-nvrtc-cu12~=12.0" \
  "nvidia-cufft-cu12~=11.0" "nvidia-curand-cu12~=10.0" "nvidia-cudnn-cu12~=9.0"
# ... or point EMBEDDING_CUDA_LIB_DIR (.env) at an existing set, e.g. the
# "nvidia" package directory of another Python environment that has torch.
```

A 4 GB card holds one large model at a time. The split that measures best:
the index build on the GPU (`EMBEDDING_DEVICE=cuda` for that run), and at
query time the embedder on the CPU (one short query, about 100 ms) with the
full-precision reranker on the GPU:

```
EMBEDDING_DEVICE=cpu
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
RERANKER_MODEL_DIR=bge-reranker-v2-m3-fp16   # plain dir: tokenizer files + onnx/model.onnx
RERANKER_DEVICE=cuda
```

The fp16 reranker is the fp32 ONNX model converted with
`onnxruntime.transformers.float16.convert_float_to_float16(model,
keep_io_types=True, disable_shape_infer=True)`. Measured against fp32 on
the same candidates it gives identical rankings (score correlation
1.00000, max score difference 0.04 on a 10-unit scale) at half the time;
int8 was not adopted (rankings differ in about 1 of 17 top-5 slots).

Without a GPU the defaults apply (reranker on the CPU, several seconds per
query; measured times in `docs/DEPLOYMENT.md`). With `auto` a process that
finds the GPU busy falls back to the CPU and says so in its log.

## Languages & routes

UI is available in English, Urdu, Arabic, and Turkish. The URL carries the
locale: `/en`, `/ur`, `/ar`, `/tr`. Urdu and Arabic render right-to-left.
Content (translations, tafsir) is served in Arabic, Urdu, and English.
Turkish is a UI-only language: Turkish users read the Arabic source content
(hadith, tafsir) with a fully Turkish interface.

Surfaces:
- `/{locale}` - home + search
- `/{locale}/quran` -> `/{locale}/quran/{surah}` - aligned reader
- `/{locale}/hadith` -> `/{collection}` -> `/{book}` - hadith browser
- `/{locale}/tafsir` -> `/{surah}` - Tafsir Ibn Kathir reader
- `/{locale}/search` - unified search

## Production deployment

The server runs the same three parts as Docker containers behind Caddy
(automatic HTTPS), built from `Dockerfile`, `frontend/Dockerfile` and
`docker-compose.prod.yml`. The database and the models are shipped as a
release bundle (`scripts/release_bundle.sh`) so nothing is recomputed on
the server. Step by step: `docs/DEPLOYMENT.md`.
