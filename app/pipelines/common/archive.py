"""Write-once corpus archive.

Files under corpus/original/ are the byte-perfect record of what a source
served us. They are written exactly once: content is staged in corpus/temp/,
checksummed, then atomically moved into place. Re-storing identical bytes is
a no-op; re-storing *different* bytes for the same path raises - differences
must be reviewed by a human, never silently applied (Source Fidelity).
"""

import hashlib
import os
import uuid
from dataclasses import dataclass
from pathlib import Path


class ArtifactIntegrityError(Exception):
    """Raised when new content differs from what is already archived."""


@dataclass(frozen=True)
class StoredFile:
    relative_path: str  # relative to corpus/original/
    sha256: str
    byte_size: int
    already_existed: bool


class CorpusArchive:
    def __init__(self, corpus_root: Path):
        self.root = Path(corpus_root)
        self.original = self.root / "original"
        self.temp = self.root / "temp"
        self.manifests = self.root / "manifests"

    def store(self, relative_path: str, content: bytes) -> StoredFile:
        """Archive `content` at original/<relative_path>, write-once."""
        sha256 = hashlib.sha256(content).hexdigest()
        dest = self.original / relative_path

        if dest.exists():
            existing_sha = hashlib.sha256(dest.read_bytes()).hexdigest()
            if existing_sha == sha256:
                return StoredFile(relative_path, sha256, len(content), True)
            raise ArtifactIntegrityError(
                f"{relative_path}: archived sha256 {existing_sha[:12]}… differs "
                f"from newly fetched {sha256[:12]}… - refusing to overwrite. "
                "Review the difference and import as a new run if legitimate."
            )

        self.temp.mkdir(parents=True, exist_ok=True)
        staging = self.temp / f"{uuid.uuid4().hex}.part"
        try:
            with open(staging, "wb") as fh:
                fh.write(content)
                fh.flush()
                os.fsync(fh.fileno())
            dest.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staging, dest)  # atomic within the same filesystem
        finally:
            staging.unlink(missing_ok=True)

        return StoredFile(relative_path, sha256, len(content), False)

    def verify(self, relative_path: str, expected_sha256: str) -> bool:
        """Re-checksum an archived file against its recorded hash."""
        dest = self.original / relative_path
        if not dest.exists():
            return False
        return hashlib.sha256(dest.read_bytes()).hexdigest() == expected_sha256
