"""File content hashing for artifact deduplication."""

from __future__ import annotations

import hashlib
from pathlib import Path

CHUNK_SIZE = 65536


def sha256_file(path: Path) -> str:
    """Return hex SHA-256 digest of file contents."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()
