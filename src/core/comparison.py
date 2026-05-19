"""Compare custom compression with ZIP and gzip baselines."""

from __future__ import annotations

import gzip
import io
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable


@dataclass
class BaselineResult:
    name: str
    compressed_size: int
    duration_seconds: float


def gzip_size(data: bytes, level: int = 6) -> BaselineResult:
    start = time.perf_counter()
    out = gzip.compress(data, compresslevel=level)
    elapsed = time.perf_counter() - start
    return BaselineResult(name="gzip", compressed_size=len(out), duration_seconds=elapsed)


def zip_size_for_files(files: Iterable[Path]) -> BaselineResult:
    """Run files through ZIP_DEFLATED and return the resulting archive size."""
    start = time.perf_counter()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in files:
            zf.write(path, arcname=path.name)
    elapsed = time.perf_counter() - start
    return BaselineResult(name="zip", compressed_size=buf.tell(), duration_seconds=elapsed)


def compare_against_baselines(
    files: Iterable[Path],
    custom_total: int,
    custom_seconds: float,
) -> Dict[str, Dict[str, float]]:
    files = list(files)
    if not files:
        return {}
    # gzip is per-file; sum sizes for a fair total
    gzip_total = 0
    gzip_seconds = 0.0
    for f in files:
        result = gzip_size(f.read_bytes())
        gzip_total += result.compressed_size
        gzip_seconds += result.duration_seconds
    zip_result = zip_size_for_files(files)

    return {
        "custom": {
            "compressed_size": float(custom_total),
            "duration_seconds": float(custom_seconds),
        },
        "gzip": {
            "compressed_size": float(gzip_total),
            "duration_seconds": float(gzip_seconds),
        },
        "zip": {
            "compressed_size": float(zip_result.compressed_size),
            "duration_seconds": float(zip_result.duration_seconds),
        },
    }
