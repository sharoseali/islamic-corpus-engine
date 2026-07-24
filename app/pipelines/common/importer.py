"""Importer base class.

Manages the full provenance lifecycle of an import:

    Source row  ->  ImportRun row  ->  RawArtifact row per fetched file
                                   ->  corpus/original/ file (write-once)
                                   ->  corpus/manifests/<source>/<run>.json

Subclasses implement `execute()` and use `archive_bytes()` for every payload
they fetch. Imports are deterministic and idempotent: identical content is
recognized (not duplicated), and changed upstream content raises instead of
silently overwriting.
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.provenance import ImportRun, RawArtifact, Source
from app.pipelines.common.archive import CorpusArchive


class BaseImporter(ABC):
    # Subclasses must define these
    source_key: str
    source_name: str
    source_base_url: str
    source_license: str | None = None
    source_attribution: str | None = None
    importer_name: str
    importer_version: str = "1.0.0"

    def __init__(self, session: Session, corpus_root: str | Path = "corpus"):
        self.session = session
        self.archive = CorpusArchive(Path(corpus_root))
        self.run: ImportRun | None = None
        self._manifest_entries: list[dict] = []

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def execute(self) -> dict:
        """Perform the import; return stats. Implemented by subclasses."""
        raise NotImplementedError

    def run_import(self) -> ImportRun:
        source = self._get_or_create_source()
        self.run = ImportRun(
            source=source,
            importer=self.importer_name,
            importer_version=self.importer_version,
            status="running",
        )
        self.session.add(self.run)
        self.session.flush()

        try:
            stats = self.execute()
        except Exception as exc:
            # All-or-nothing: discard every partial data change, then record
            # the failed run on its own in a fresh transaction.
            self.session.rollback()
            source = self._get_or_create_source()
            self.run = ImportRun(
                source=source,
                importer=self.importer_name,
                importer_version=self.importer_version,
                status="failed",
                finished_at=datetime.now(timezone.utc),
                notes=f"{type(exc).__name__}: {exc}"[:2000],
            )
            self.session.add(self.run)
            self.session.commit()
            self._write_manifest()
            raise

        self.run.status = "succeeded"
        self.run.stats = stats
        self.run.finished_at = datetime.now(timezone.utc)
        self.session.commit()
        self._write_manifest()
        return self.run

    # ------------------------------------------------------------------ #
    # Archiving
    # ------------------------------------------------------------------ #

    def archive_bytes(
        self,
        relative_path: str,
        content: bytes,
        *,
        endpoint: str,
        request_params: dict | None = None,
        http_status: int = 200,
    ) -> RawArtifact:
        """Archive raw bytes + record (or reuse) the RawArtifact row."""
        stored = self.archive.store(relative_path, content)

        artifact: RawArtifact | None = None
        if stored.already_existed:
            artifact = self.session.scalar(
                select(RawArtifact).where(
                    RawArtifact.relative_path == stored.relative_path,
                    RawArtifact.sha256 == stored.sha256,
                )
            )
        if artifact is None:
            artifact = RawArtifact(
                import_run_id=self.run.id,
                relative_path=stored.relative_path,
                sha256=stored.sha256,
                byte_size=stored.byte_size,
                endpoint=endpoint,
                request_params=request_params,
                http_status=http_status,
                fetched_at=datetime.now(timezone.utc),
            )
            self.session.add(artifact)
            self.session.flush()

        self._manifest_entries.append(
            {
                "relative_path": stored.relative_path,
                "sha256": stored.sha256,
                "byte_size": stored.byte_size,
                "endpoint": endpoint,
                "request_params": request_params,
                "http_status": http_status,
                "fetched_at": artifact.fetched_at.isoformat(),
                "reused_existing": stored.already_existed,
            }
        )
        return artifact

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _get_or_create_source(self) -> Source:
        source = self.session.scalar(
            select(Source).where(Source.key == self.source_key)
        )
        if source is None:
            source = Source(
                key=self.source_key,
                name=self.source_name,
                base_url=self.source_base_url,
                license=self.source_license,
                attribution=self.source_attribution,
            )
            self.session.add(source)
            self.session.flush()
        return source

    def _write_manifest(self) -> None:
        if self.run is None:
            return
        manifest = {
            "run_id": self.run.id,
            "source": self.source_key,
            "importer": self.importer_name,
            "importer_version": self.importer_version,
            "status": self.run.status,
            "started_at": self.run.started_at.isoformat()
            if self.run.started_at
            else None,
            "finished_at": self.run.finished_at.isoformat()
            if self.run.finished_at
            else None,
            "stats": self.run.stats,
            "artifacts": self._manifest_entries,
        }
        out_dir = self.archive.manifests / self.source_key
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"run_{self.run.id:06d}.json"
        out_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
