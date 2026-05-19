"""Manifest for a compressed package.

The manifest is a JSON document stored alongside the compressed files.
It records:
    - the package format version
    - per-file metadata (size, strategy, hash, output path)
    - aggregate metrics
    - timestamps

It is used by the decompressor to know how to restore each file
and by the analytics tab to show summary statistics.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class FileEntry:
    relative_path: str          # path inside the source webpage
    output_path: str            # path inside the package (compressed/...)
    strategy: str               # "text" | "image" | "skip"
    original_size: int
    compressed_size: int
    sha256_original: str
    sha256_compressed: str
    image_preset: Optional[str] = None
    image_mode: Optional[str] = None
    note: Optional[str] = None


@dataclass
class Manifest:
    version: int = 1
    created_at: float = field(default_factory=time.time)
    package_label: str = ""
    files: List[FileEntry] = field(default_factory=list)
    totals: Dict[str, float] = field(default_factory=dict)

    def add(self, entry: FileEntry) -> None:
        self.files.append(entry)

    def recompute_totals(self) -> None:
        original = sum(f.original_size for f in self.files)
        compressed = sum(f.compressed_size for f in self.files)
        ratio = (compressed / original) if original else 1.0
        self.totals = {
            "original_size": original,
            "compressed_size": compressed,
            "savings_bytes": max(0, original - compressed),
            "ratio": ratio,
            "savings_pct": (1.0 - ratio) * 100.0,
            "file_count": len(self.files),
        }

    # -----------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "created_at": self.created_at,
            "package_label": self.package_label,
            "files": [asdict(f) for f in self.files],
            "totals": self.totals,
        }

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def read(cls, path: Path) -> "Manifest":
        raw = json.loads(path.read_text(encoding="utf-8"))
        m = cls(
            version=raw.get("version", 1),
            created_at=raw.get("created_at", 0.0),
            package_label=raw.get("package_label", ""),
            files=[FileEntry(**f) for f in raw.get("files", [])],
            totals=raw.get("totals", {}),
        )
        return m
