"""Shared API dependencies."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import SessionLocal

# Languages the platform serves (UI + content)
SUPPORTED_LANGUAGES = ("en", "ur", "ar", "tr")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
