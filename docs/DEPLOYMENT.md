# Deploying Elaaj to a server

The server runs the same three parts as development, as Docker containers,
plus Caddy in front for HTTPS:

| Service | Image | Role |
|---|---|---|
| `db` | `pgvector/pgvector:pg16` | PostgreSQL with pgvector and pg_trgm. Internal only. |
| `api` | built from `Dockerfile` | FastAPI, CPU build of onnxruntime, ffmpeg for voice search. Internal only. |
| `web` | built from `frontend/Dockerfile` | Next.js (standalone output). Internal only. |
| `caddy` | `caddy:2-alpine` | The only published ports (80, 443). Automatic HTTPS for a domain. |

Caddy sends `/api/v1/*` to the API and everything else to the frontend. The
API's interactive docs and the database are not reachable from outside.
Everything is defined in `docker-compose.prod.yml`, `deploy/Caddyfile` and
`.env` (template: `deploy/env.production.example`).

The data is never recomputed on the server. A **release bundle** built on
the development PC carries the database (a `pg_dump` archive), the search
models, the Whisper model and the original corpus archives; the server
restores it in minutes. The embeddings alone would take 8 to 12 hours on a
CPU server.

## 1. Server requirements

- Linux with Docker Engine and Docker Compose v2 (Ubuntu 22.04 or 24.04 is
  the straightforward choice; the development PC runs the same containers).
- **RAM: 16 GB recommended, 8 GB minimum.** The API holds the embedding
  model (2.2 GB) and the reranker (2.2 GB full precision, 0.6 GB int8) in
  memory; PostgreSQL wants 2 GB of shared buffers plus file cache for the
  1.5 GB vector index. With 8 GB use `RERANK_CANDIDATES=0` or the int8
  reranker and `PG_SHARED_BUFFERS=1GB`.
- **Disk: 60 GB.** Database 4 GB, models 6 GB, images 3 GB, one bundle
  8 GB, logs and room to grow.
- **CPU: 4 cores minimum.** Search without the reranker takes about 0.1 s.
  The reranker (`BAAI/bge-reranker-v2-m3`) is the one expensive step on a
  CPU; measured on the development PC (20-core laptop, which is faster per
  core than most virtual servers), hybrid search end to end:

| CPU threads | Reranker | Candidates (`RERANK_CANDIDATES`) | Median | Slowest of 6 queries |
|---|---|---|---|---|
| 4 | none (0) | 0 | 0.10 s | 0.13 s |
| 4 | int8 | 12 | 3.1 s | 4.1 s |
| 4 | int8 | 24 | 7.4 s | 9.0 s |
| 4 | full precision | 12 | 6.4 s | 8.3 s |
| 4 | full precision | 24 | 16.6 s | 20.5 s |
| 8 | full precision | 8 | 4.0 s | 5.7 s |
| 8 | full precision | 12 | 6.6 s | 8.5 s |
| 8 | int8 | 24 | 7.5 s | 8.6 s |
| GPU (RTX 3050, fp16) | full precision | 24 | 0.4 s | |

  Doubling the threads did not shorten the reranker step, so count on
  about 0.5 s per candidate at full precision and 0.3 s at int8, whatever
  the core count. Full precision on the GPU and on the CPU give identical rankings. The
  int8 reranker changes about one result in seventeen in the top five, so
  it is not the project default. Options, in order of preference:

  1. **A server with an NVIDIA GPU** (any card with 4 GB or more): the
     reranker runs in 0.4 s. Install the NVIDIA container toolkit, build
     the API image with the CUDA 12 onnxruntime (see "GPU" in
     `docs/RUNNING.md`) and add `gpus: all` to the `api` service. Not
     tested here (the development PC has no container toolkit).
  2. **CPU only, full precision, 12 candidates** (the template's default):
     correct rankings, about 6 s per search on 4 cores.
  3. **CPU only, reranker off** (`RERANK_CANDIDATES=0`): 0.1 s searches,
     ordered by the fused keyword and semantic ranks alone.
  4. **CPU only, int8** (`RERANKER_MODEL=BAAI/bge-reranker-v2-m3-int8`,
     `RERANKER_MODEL_DIR=bge-reranker-v2-m3-int8`): about 3 s, slightly
     different rankings.

- A **domain name** pointed at the server (DNS A record) gives automatic
  HTTPS. Without one, `SITE_ADDRESS=:80` serves plain HTTP on the IP
  address; browsers then refuse the microphone (voice search needs HTTPS).

## 2. One-time server setup

```bash
# Docker (Ubuntu). Log out and in again after usermod.
sudo apt update && sudo apt install -y docker.io docker-compose-v2 git rsync
sudo usermod -aG docker "$USER"

# Checkout owned by the deploy user (the API container runs as uid 1000 and
# writes into corpus/; set APP_UID/APP_GID in .env if your user differs).
sudo mkdir -p /srv/elaaj && sudo chown "$USER" /srv/elaaj
git clone https://github.com/sharoseali/islamic-corpus-engine.git /srv/elaaj
cd /srv/elaaj
cp deploy/env.production.example .env
nano .env        # POSTGRES_PASSWORD, SITE_ADDRESS, memory and CPU settings

# Firewall: SSH, HTTP, HTTPS (443/udp is HTTP/3).
sudo ufw allow OpenSSH && sudo ufw allow 80,443/tcp && sudo ufw allow 443/udp && sudo ufw enable
```

## 3. First deployment

On the development PC (database running, models in `corpus/cache/models`):

```bash
scripts/release_bundle.sh                    # writes release/<date>/
rsync -avP release/<date>/ user@server:/srv/elaaj/release/<date>/
```

The bundle contains `db.dump` (PostgreSQL custom format, compressed),
`models.tar` (plain model directories), `whisper.tar`, `original.tar`,
`MANIFEST.txt` (git commit, migration head, embedding model) and
`SHA256SUMS`. `MODELS="e5-large-fp32 bge-reranker-v2-m3-fp32"` before the
command limits the models to what the server will use.

On the server:

```bash
cd /srv/elaaj
docker compose -f docker-compose.prod.yml build      # API and web images
scripts/release_restore.sh release/<date>            # verifies checksums, restores, starts
curl -s http://127.0.0.1/api/v1/health               # {"status":"ok","db":"ok",...}
```

The restore stops the API, loads the dump into the `db` container
(`RESTORE_JOBS=4` uses more cores for the index builds), unpacks the
models and archives into `corpus/`, starts the stack and runs
`alembic upgrade head` (a no-op unless the code has migrations newer than
the dump). Then open `https://<domain>/` (or `http://<ip>/`).

## 4. Updating the code

`.github/workflows/deploy.yml` deploys every push to `main` (and can be
started by hand from the Actions tab). It needs these repository secrets:

| Secret | Value |
|---|---|
| `SSH_HOST` | server address |
| `SSH_USER` | the deploy user (owns `/srv/elaaj`, member of `docker`) |
| `SSH_KEY` | a private key whose public half is in that user's `authorized_keys` |
| `SSH_PORT` | optional, default 22 |
| `DEPLOY_PATH` | optional, default `/srv/elaaj` |

Until `SSH_HOST` exists the job ends green without doing anything, so
merging to `main` before the server exists is safe. The job uses the
GitHub environment `production`; add a required reviewer to it for a
manual approval step before each deploy.

What the deploy does, and what to run by hand without it:

```bash
cd /srv/elaaj
git fetch --prune origin && git checkout main && git reset --hard origin/main
docker compose -f docker-compose.prod.yml build --pull
docker compose -f docker-compose.prod.yml up -d --remove-orphans
docker compose -f docker-compose.prod.yml exec -T api alembic upgrade head
```

The frontend's ISR cache lives inside the `web` container, so a new image
starts with a fresh cache (the "stale data across builds" gotcha of
development does not apply).

## 5. Updating the data

Content changes (new imports, rebuilt search index, new embeddings) are
made on the development PC, where the GPU builds embeddings in 2 hours,
then shipped as a new bundle and restored with `scripts/release_restore.sh`
(the restore replaces the whole database; the site is down for the minutes
the restore takes). Small importer runs can also be executed in place:

```bash
docker compose -f docker-compose.prod.yml exec api python -m app.pipelines.quran.themes
docker compose -f docker-compose.prod.yml exec api python -m app.services.search_indexer
```

They write their archives and manifests into the mounted `corpus/`
directory on the server, exactly as in development.

## 6. Operations

```bash
docker compose -f docker-compose.prod.yml ps                 # state and health
docker compose -f docker-compose.prod.yml logs -f api        # API log (also: web, caddy, db)
docker compose -f docker-compose.prod.yml restart api
docker stats --no-stream                                     # memory per container
# Backup of the server database (the content is also reproducible from a bundle):
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U ice_admin -d islamic_corpus -Fc > backup-$(date +%F).dump
```

- `GET /api/v1/health` answers 200 with `"db": "ok"` when the database
  responds and 503 otherwise; the compose health checks use it.
- `API_WORKERS` adds uvicorn processes; each loads its own models
  (about 4.5 GB each with the full-precision reranker), so raise it only
  on a large server.
- The Whisper model (voice search in browsers without a speech engine) is
  restored from the bundle into `corpus/cache/hf`; without it the API
  downloads it (about 480 MB) on the first voice request.
- Caddy stores its certificates in the `caddy_data` volume and renews
  them itself.

## 7. Security notes

- Only Caddy publishes ports. The database has no published port and the
  API is reachable only under `/api/v1`.
- Containers run as unprivileged users (`app`, `node`, `postgres`).
- `.env` holds the database password and is never committed. Rotate it by
  changing it in `.env` and re-creating the `db` container's user, or
  simply before the first restore.
- Voice search accepts uploads (25 MB cap in the Caddyfile) and spends CPU
  on them; if it is abused, add a rate limit at Caddy or set a firewall
  rule for `/api/v1/speech`.
