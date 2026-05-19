"""Incremental compression cache.

Stores per-file SHA-256 hashes from the previous compression run, so the
next run can skip files that have not changed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Set, Tuple


@dataclass
class IncrementalCache:
    """Mapping of relative path -> SHA-256 of the source file."""

    hashes: Dict[str, str] = field(default_factory=dict)

    def diff(self, current: Dict[str, str]) -> Tuple[Set[str], Set[str], Set[str], Set[str]]:
        """Return (unchanged, recompressed, added, removed)."""
        previous_paths = set(self.hashes.keys())
        current_paths = set(current.keys())

        added = current_paths - previous_paths
        removed = previous_paths - current_paths
        common = previous_paths & current_paths
        unchanged: Set[str] = set()
        recompressed: Set[str] = set()
        for path in common:
            if self.hashes[path] == current[path]:
                unchanged.add(path)
            else:
                recompressed.add(path)
        return unchanged, recompressed, added, removed

    # -----------------------------------------------------------------
    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def read(cls, path: Path) -> "IncrementalCache":
        if not path.exists():
            return cls()
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls(hashes=dict(raw.get("hashes", {})))
