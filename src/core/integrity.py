"""SHA-256 helpers for file integrity verification."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path, chunk: int = 65_536) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def files_match(a: Path, b: Path) -> bool:
    return sha256_file(a) == sha256_file(b)


def hash_many(paths: Iterable[Path]) -> dict:
    return {str(p): sha256_file(p) for p in paths}
