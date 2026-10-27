"""Application configuration.

All settings are loaded from environment variables (and the project-root
`.env` file in development). This module is the single source of truth for
configuration - Alembic and the application both read from here.
"""

from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    APP_NAME: str = "Islamic Knowledge Core"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"
    # Browser origins allowed to call the API directly (comma-separated).
    # The production site calls the API through its own origin (the
    # frontend forwards /api/v1), so this only matters for development.
    CORS_ORIGINS: str = "http://localhost:3400,http://127.0.0.1:3400"

    # --- PostgreSQL ---
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5433
    POSTGRES_DB: str = "islamic_corpus"
    POSTGRES_USER: str = "ice_admin"
    POSTGRES_PASSWORD: str

    # --- Corpus ---
    CORPUS_ROOT: str = "corpus"

    # --- Quran Foundation API (quran.com) ---
    QF_CLIENT_ID: str = ""
    QF_CLIENT_SECRET: str = ""
    QF_OAUTH_BASE: str = "https://oauth2.quran.foundation"
    QF_API_BASE: str = "https://apis.quran.foundation"

    # --- sunnah.com API ---
    SUNNAH_API_KEY: str = ""
    SUNNAH_API_BASE: str = "https://api.sunnah.com/v1"

    # --- Speech-to-text (voice search, offline Whisper) ---
    # Model size: tiny, base, small, medium, large-v3. Larger is more
    # accurate for Urdu/Arabic but slower on CPU.
    WHISPER_MODEL: str = "small"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    # --- Semantic search (open-source embedding + reranker, CPU, offline) ---
    # Models are downloaded once into EMBEDDING_CACHE_DIR and pinned by
    # checksum in search.embedding_state. e5 models need the "query: " and
    # "passage: " prefixes, added by app.services.embeddings.
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-large"
    # Plain directory under EMBEDDING_CACHE_DIR holding model.onnx + tokenizer.
    EMBEDDING_MODEL_DIR: str = "e5-large-fp32"
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3-int8"
    # "cpu" (default; the int8 reranker only runs its quantised layers on
    # the CPU anyway) or "cuda" for a full-precision reranker on a GPU with
    # room beside the embedding model.
    RERANKER_DEVICE: str = "cpu"
    # Optional plain directory under EMBEDDING_CACHE_DIR holding the reranker
    # (tokenizer files + onnx/model.onnx); empty: fastembed's own cache.
    RERANKER_MODEL_DIR: str = ""
    EMBEDDING_CACHE_DIR: str = "corpus/cache/models"
    EMBEDDING_THREADS: int = 16  # onnxruntime intra-op threads
    # How many fused candidates the reranker re-orders per query. The time
    # grows with this number; 0 turns the reranker off (CPU-only servers).
    RERANK_CANDIDATES: int = 24
    # "auto": use the GPU when onnxruntime-gpu and a CUDA device are present
    # (full precision, no TF32), otherwise the CPU. "cuda" requires the GPU,
    # "cpu" never touches it.
    EMBEDDING_DEVICE: str = "auto"
    # Directory laid out like pip's "nvidia" namespace package (cublas/lib,
    # cudnn/lib, ...) to load the CUDA libraries from, e.g. those of another
    # Python environment on the same machine. Empty: use this environment's
    # own nvidia-*-cu12 packages.
    EMBEDDING_CUDA_LIB_DIR: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """SQLAlchemy connection URL (psycopg v3 driver)."""
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_HOST,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
