"""Choose a compression strategy based on file extension."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

# Hash map use case: extension -> strategy label
EXTENSION_STRATEGY: Dict[str, str] = {
    ".html": "text",
    ".htm":  "text",
    ".css":  "text",
    ".js":   "text",
    ".json": "text",
    ".txt":  "text",
    ".svg":  "text",
    ".jpg":  "image",
    ".jpeg": "image",
    ".png":  "image",
}


class StrategySelector:
    """Map a file path to a compression strategy."""

    def __init__(self, mapping: Dict[str, str] | None = None) -> None:
        self.mapping = dict(mapping or EXTENSION_STRATEGY)

    def for_path(self, path: Path) -> str:
        return self.mapping.get(path.suffix.lower(), "skip")
