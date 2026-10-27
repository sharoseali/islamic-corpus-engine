"""Islamic Knowledge Core - FastAPI application.

Serves the authenticated corpus (Quran, Hadith, Tafsir) and search to the
scholar-facing frontend. Read-only over the canonical data.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import hadith, quran, search, speech
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Islamic Knowledge Core API",
    version="1.0.0",
    description="Authenticated Quran, Hadith, and Tafsir corpus with search.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3400",
        "http://127.0.0.1:3400",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api/v1")
app.include_router(quran.router, prefix="/api/v1")
app.include_router(hadith.router, prefix="/api/v1")
app.include_router(speech.router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "app": settings.APP_NAME, "version": "1.0.0"}


@app.get("/api/v1/languages", tags=["meta"])
def languages() -> dict:
    return {
        "ui": ["en", "ur", "ar", "tr"],
        "rtl": ["ur", "ar"],
        "content": ["ar", "ur", "en"],
    }
