# syntax=docker/dockerfile:1
# Elaaj API (FastAPI) - CPU build.
#
# The corpus directory (models, original archives, manifests) is mounted at
# run time, see docker-compose.prod.yml. For a GPU host run the API outside
# Docker with the venv (docs/RUNNING.md, "GPU") or add the NVIDIA container
# toolkit and the CUDA 12 onnxruntime build; this image stays CPU-only.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ffmpeg decodes browser recordings for voice search.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
COPY scripts ./scripts

# Runs as an unprivileged user; the mounted corpus directory must be
# writable by it (importers write manifests, Whisper caches its model).
RUN groupadd -g 1000 app && useradd -m -u 1000 -g app app \
    && mkdir -p corpus && chown -R app:app /app
USER app

# Whisper (faster-whisper) model cache, inside the mounted corpus tree so it
# survives image rebuilds and can be pre-seeded from a release bundle.
ENV HF_HOME=/app/corpus/cache/hf

EXPOSE 8400
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port 8400 --workers ${API_WORKERS:-1} --proxy-headers --forwarded-allow-ips '*'"]
