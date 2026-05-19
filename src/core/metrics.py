"""Metric collection helpers used by analytics."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class FileMetric:
    name: str
    strategy: str
    original_size: int
    compressed_size: int
    duration_seconds: float
    note: str = ""

    @property
    def ratio(self) -> float:
        return (self.compressed_size / self.original_size) if self.original_size else 1.0

    @property
    def savings_pct(self) -> float:
        return (1.0 - self.ratio) * 100.0


@dataclass
class MetricsCollector:
    items: List[FileMetric] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    ended_at: float = 0.0

    def add(self, metric: FileMetric) -> None:
        self.items.append(metric)

    def finish(self) -> None:
        self.ended_at = time.time()

    # -----------------------------------------------------------------
    def totals(self) -> Dict[str, float]:
        original = sum(i.original_size for i in self.items)
        compressed = sum(i.compressed_size for i in self.items)
        duration = sum(i.duration_seconds for i in self.items)
        ratio = (compressed / original) if original else 1.0
        return {
            "original_size": original,
            "compressed_size": compressed,
            "duration": duration,
            "wall_clock": (self.ended_at or time.time()) - self.started_at,
            "ratio": ratio,
            "savings_pct": (1.0 - ratio) * 100.0,
            "file_count": len(self.items),
        }

    def by_strategy(self) -> Dict[str, Dict[str, float]]:
        groups: Dict[str, List[FileMetric]] = {}
        for item in self.items:
            groups.setdefault(item.strategy, []).append(item)
        out: Dict[str, Dict[str, float]] = {}
        for key, lst in groups.items():
            original = sum(i.original_size for i in lst)
            compressed = sum(i.compressed_size for i in lst)
            ratio = (compressed / original) if original else 1.0
            out[key] = {
                "original": original,
                "compressed": compressed,
                "ratio": ratio,
                "savings_pct": (1.0 - ratio) * 100.0,
                "count": len(lst),
            }
        return out
