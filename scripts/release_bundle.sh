#!/usr/bin/env bash
# Build a release bundle for a server: the database as a pg_dump archive,
# the search models, the Whisper model and the original corpus archives.
# Nothing is recomputed on the server (the embeddings alone take hours).
#
#   scripts/release_bundle.sh [output-dir]      # default release/<date>
#
# Environment: DB_CONTAINER (default ikc_postgres), MODELS (space-separated
# model directories under corpus/cache/models to include).
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
OUT=${1:-release/$(date +%Y%m%d-%H%M)}
DB_CONTAINER=${DB_CONTAINER:-ikc_postgres}
MODELS=${MODELS:-"e5-large-fp32 bge-reranker-v2-m3-fp32 bge-reranker-v2-m3-int8 bge-reranker-v2-m3-fp16"}
HF_HUB=${HF_HUB:-$HOME/.cache/huggingface/hub}

# Database name and user from .env (never the password: pg_dump runs inside
# the container as the database superuser).
POSTGRES_DB=$(grep -E '^POSTGRES_DB=' .env | cut -d= -f2- || true)
POSTGRES_USER=$(grep -E '^POSTGRES_USER=' .env | cut -d= -f2- || true)
POSTGRES_DB=${POSTGRES_DB:-islamic_corpus}
POSTGRES_USER=${POSTGRES_USER:-ice_admin}

mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
echo "bundle: $OUT"

echo "[1/5] database dump ($POSTGRES_DB from $DB_CONTAINER)"
docker exec "$DB_CONTAINER" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  --format=custom --compress=6 --no-owner --no-privileges > "$OUT/db.dump"

echo "[2/5] search models"
present=()
for m in $MODELS; do
  if [ -d "corpus/cache/models/$m" ]; then present+=("$m"); else echo "  skip $m (not present)"; fi
done
tar -C corpus/cache/models -cf "$OUT/models.tar" "${present[@]}"

echo "[3/5] whisper model"
if ls -d "$HF_HUB"/models--Systran--faster-whisper-* >/dev/null 2>&1; then
  # -h follows the cache's symlinks so the copy is self-contained.
  tar -C "$(dirname "$HF_HUB")" -chf "$OUT/whisper.tar" \
    $(cd "$(dirname "$HF_HUB")" && ls -d hub/models--Systran--faster-whisper-*)
else
  echo "  none cached; the server downloads it on first use"
fi

echo "[4/5] original corpus archives"
tar -C corpus -cf "$OUT/original.tar" original

echo "[5/5] manifest and checksums"
{
  echo "created=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "git_commit=$(git rev-parse HEAD 2>/dev/null || echo unknown)"
  echo "alembic_head=$(docker exec "$DB_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc 'select version_num from alembic_version')"
  echo "embedding_state=$(docker exec "$DB_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc 'select model_name||'"'"' chunks='"'"'||chunk_count from search.embedding_state' 2>/dev/null | head -1)"
  echo "models=${present[*]}"
} > "$OUT/MANIFEST.txt"
(cd "$OUT" && sha256sum db.dump models.tar original.tar $(ls whisper.tar 2>/dev/null) MANIFEST.txt > SHA256SUMS)

du -sh "$OUT"/*
echo "done: $OUT"
