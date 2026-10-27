#!/usr/bin/env bash
# Restore a release bundle into the production stack (docker-compose.prod.yml).
# Run on the server from the repository root, after .env is in place:
#
#   scripts/release_restore.sh /path/to/bundle
#
# Replaces the database contents (the stack's API is stopped meanwhile),
# unpacks the models and the original corpus archives, then starts
# everything and applies any migrations newer than the dump.
set -euo pipefail

BUNDLE=${1:?usage: release_restore.sh <bundle-dir>}
BUNDLE=$(cd "$BUNDLE" && pwd)
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
# COMPOSE_ARGS: extra docker compose flags (local tests: --env-file, -f override).
COMPOSE=(docker compose -f docker-compose.prod.yml ${COMPOSE_ARGS:-})
RESTORE_JOBS=${RESTORE_JOBS:-2}

POSTGRES_DB=$(grep -E '^POSTGRES_DB=' .env | cut -d= -f2- || true)
POSTGRES_USER=$(grep -E '^POSTGRES_USER=' .env | cut -d= -f2- || true)
POSTGRES_DB=${POSTGRES_DB:-islamic_corpus}
POSTGRES_USER=${POSTGRES_USER:-ice_admin}

echo "[1/5] verify checksums"
(cd "$BUNDLE" && sha256sum -c SHA256SUMS)
cat "$BUNDLE/MANIFEST.txt"

echo "[2/5] models and corpus archives"
mkdir -p corpus/cache/models corpus/cache/hf
tar -xf "$BUNDLE/models.tar" -C corpus/cache/models
[ -f "$BUNDLE/whisper.tar" ] && tar -xf "$BUNDLE/whisper.tar" -C corpus/cache/hf
tar -xf "$BUNDLE/original.tar" -C corpus

echo "[3/5] database"
"${COMPOSE[@]}" stop api web >/dev/null 2>&1 || true
"${COMPOSE[@]}" up -d db
until "${COMPOSE[@]}" exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; do sleep 2; done
"${COMPOSE[@]}" cp "$BUNDLE/db.dump" db:/tmp/db.dump
# --clean drops what the dump is about to create, so a re-restore over an
# older copy works too; on an empty database it is a no-op.
"${COMPOSE[@]}" exec -T db pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  --no-owner --no-privileges --clean --if-exists --exit-on-error \
  --jobs="$RESTORE_JOBS" /tmp/db.dump
"${COMPOSE[@]}" exec -T db rm -f /tmp/db.dump
"${COMPOSE[@]}" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "ANALYZE"

echo "[4/5] start the stack"
"${COMPOSE[@]}" up -d

echo "[5/5] migrations newer than the dump (normally none)"
"${COMPOSE[@]}" exec -T api alembic upgrade head

"${COMPOSE[@]}" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select 'verses='||(select count(*) from quran.verses)||' hadiths='||(select count(*) from hadith.hadiths)||' chunks='||(select count(*) from search.chunks)"
echo "restore complete"
