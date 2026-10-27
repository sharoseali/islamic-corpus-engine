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

The browser calls `/api/v1/...` on the frontend's own origin, and Next.js
forwards it to the backend (`rewrites` in `frontend/next.config.ts`). This is
what lets phones and other devices on the network use the site.

## Voice search (optional)

Chrome, Edge and Safari use their built-in speech engine. Other browsers
(Firefox, Brave) record the clip and send it to the backend, which
transcribes it offline with Whisper. The server needs `ffmpeg` installed
(`sudo apt install ffmpeg`; it is already present on this machine):

```bash
qlib/bin/pip install -r requirements.txt   # installs faster-whisper
# Pre-download the model once (about 480 MB) so the first request is fast:
qlib/bin/python -c "from app.services.speech import _get_model; _get_model()"
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
qlib/bin/python -m app.pipelines.quran.morphology
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
qlib/bin/python -m app.pipelines.quran.themes
```

English queries on the Quran tab then also list matching themes as links
into the reader ("usury" -> Prohibition of usury, 2:275-276). The published
file repeats about half its rows; the import keeps them as published and
search returns each theme once.

## Semantic search (open source, offline)

Search is hybrid: keyword matching plus meaning-based retrieval over
embeddings stored in `search.chunks` (pgvector). The models are open source
and run on the CPU; nothing is sent anywhere and nothing from a model is ever
shown to a user: they only choose and order our own stored passages.

- Embedding model: `intfloat/multilingual-e5-large` as plain ONNX files in
  `corpus/cache/models/<EMBEDDING_MODEL_DIR>/` (`model.onnx`, `tokenizer.json`
  and config files). Not committed (2.2 GB); the sha256 of every file in use
  is recorded in `search.embedding_state`.
- Reranker: `BAAI/bge-reranker-v2-m3` via fastembed, cached in the same
  directory.
- Settings (`.env`): `EMBEDDING_MODEL_DIR` (default `e5-large-fp32`),
  `EMBEDDING_THREADS` (default 16), `RERANKER_MODEL`.

Build or resume the embeddings (several hours on CPU; safe to interrupt and
re-run, it continues where it stopped):

```bash
qlib/bin/python -m app.services.embedding_indexer
```

Re-running the keyword indexer (`app.services.search_indexer`) keeps the
embeddings: documents are updated in place and only chunks of changed texts
are dropped. It also refreshes `search.vocabulary` (every index word per
language), which the spelling fallback matches misspelled query words
against ("shaytaan", "patiense", "seytan") in a few milliseconds. The API takes `mode=keyword|semantic|hybrid` (default hybrid)
and `rerank=true|false` on `/api/v1/search`; without embeddings it falls
back to keyword results.

### GPU (optional)

The embedding model runs on a CUDA GPU when `onnxruntime-gpu` is installed
and `EMBEDDING_DEVICE` is `auto` (default) or `cuda`; otherwise it uses the
CPU. GPU vectors are computed in full 32-bit precision (TF32 off), so a build
started on the CPU can continue on the GPU and vice versa. Installing the
CUDA 12 build (the PyPI default is a CUDA 13 build and needs driver 580+):

```bash
qlib/bin/pip uninstall -y onnxruntime fastembed
qlib/bin/pip install onnxruntime-gpu==1.29.0 \
  --index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/
qlib/bin/pip install fastembed-gpu
# CUDA libraries: either pip install them into the venv ...
qlib/bin/pip install "nvidia-cuda-runtime-cu12~=12.0" "nvidia-cuda-nvrtc-cu12~=12.0" \
  "nvidia-cufft-cu12~=11.0" "nvidia-curand-cu12~=10.0" "nvidia-cudnn-cu12~=9.0"
# ... or point EMBEDDING_CUDA_LIB_DIR (.env) at an existing set, e.g. the
# "nvidia" package directory of another Python environment that has torch.
```

A 4 GB card holds one large model at a time. The split that measures best
here: the index build on the GPU (`EMBEDDING_DEVICE=cuda` for that run),
and at query time the embedder on the CPU (one short query, about 100 ms)
with the full-precision reranker on the GPU:

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

Without a GPU the defaults apply (int8 reranker on the CPU, several seconds
per query on long passages). With `auto` a process that finds the GPU busy
falls back to the CPU and says so in its log.

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
