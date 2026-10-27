"""Islamic Knowledge Core - FastAPI application.

Serves the authenticated corpus (Quran, Hadith, Tafsir) and search to the
scholar-facing frontend. Read-only over the canonical data.
"""

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routers import hadith, quran, search, speech
from app.core.config import get_settings
from app.db.session import engine

settings = get_settings()

app = FastAPI(
    title="Islamic Knowledge Core API",
    version="1.0.0",
    description="Authenticated Quran, Hadith, and Tafsir corpus with search.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api/v1")
app.include_router(quran.router, prefix="/api/v1")
app.include_router(hadith.router, prefix="/api/v1")
app.include_router(speech.router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["meta"])
def health(response: Response) -> dict:
    """Liveness and readiness: 200 when the database answers, 503 otherwise."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db = "ok"
    except Exception:  # noqa: BLE001 - any failure means not ready
        db = "unavailable"
        response.status_code = 503
    return {
        "status": "ok" if db == "ok" else "degraded",
        "db": db,
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "env": settings.APP_ENV,
    }


@app.get("/api/v1/languages", tags=["meta"])
def languages() -> dict:
    return {
        "ui": ["en", "ur", "ar", "tr"],
        "rtl": ["ur", "ar"],
        "content": ["ar", "ur", "en"],
    }
