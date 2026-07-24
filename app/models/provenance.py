"""Provenance models (schema: metadata).

Every piece of content in the platform traces back through this chain:

    content row  ->  RawArtifact (exact bytes + SHA-256)
                 ->  ImportRun   (when, by which importer, outcome)
                 ->  Source      (who served it, under what license)

Nothing enters the corpus without passing through these tables.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import SCHEMA_METADATA, Base


class Source(Base):
    """An authenticated upstream source (e.g. quran.com, sunnah.com)."""

    __tablename__ = "sources"
    __table_args__ = {"schema": SCHEMA_METADATA}

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True)  # "quran_foundation"
    name: Mapped[str] = mapped_column(String(255))
    base_url: Mapped[str] = mapped_column(String(255))
    license: Mapped[str | None] = mapped_column(Text)
    attribution: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    import_runs: Mapped[list["ImportRun"]] = relationship(back_populates="source")


class ImportRun(Base):
    """One execution of an importer against a source."""

    __tablename__ = "import_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'succeeded', 'failed')", name="status_valid"
        ),
        {"schema": SCHEMA_METADATA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA_METADATA}.sources.id")
    )
    importer: Mapped[str] = mapped_column(String(128))  # e.g. "quran.chapters"
    importer_version: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="running")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stats: Mapped[dict | None] = mapped_column(JSONB)  # counts, durations, etc.
    notes: Mapped[str | None] = mapped_column(Text)

    source: Mapped[Source] = relationship(back_populates="import_runs")
    artifacts: Mapped[list["RawArtifact"]] = relationship(back_populates="import_run")


class RawArtifact(Base):
    """A single raw file archived under corpus/original/ - write-once."""

    __tablename__ = "raw_artifacts"
    __table_args__ = (
        UniqueConstraint("relative_path", "sha256", name="path_sha"),
        CheckConstraint("char_length(sha256) = 64", name="sha256_length"),
        {"schema": SCHEMA_METADATA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    import_run_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA_METADATA}.import_runs.id"), index=True
    )
    relative_path: Mapped[str] = mapped_column(String(512))  # under corpus/
    sha256: Mapped[str] = mapped_column(String(64))
    byte_size: Mapped[int] = mapped_column(BigInteger)
    endpoint: Mapped[str] = mapped_column(String(512))  # URL path fetched
    request_params: Mapped[dict | None] = mapped_column(JSONB)
    http_status: Mapped[int] = mapped_column(SmallInteger)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    import_run: Mapped[ImportRun] = relationship(back_populates="artifacts")
