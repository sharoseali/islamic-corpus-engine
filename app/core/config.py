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
