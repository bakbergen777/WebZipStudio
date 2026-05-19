"""Formatting helpers used by the GUI and reports."""

from __future__ import annotations


def format_size(num_bytes: float) -> str:
    if num_bytes is None:
        return "-"
    n = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024.0:
            return f"{n:.2f} {unit}" if unit != "B" else f"{int(n)} {unit}"
        n /= 1024.0
    return f"{n:.2f} TB"


def format_duration(seconds: float) -> str:
    if seconds is None:
        return "-"
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.0f} µs"
    if seconds < 1:
        return f"{seconds * 1000:.1f} ms"
    if seconds < 60:
        return f"{seconds:.2f} s"
    minutes = seconds / 60
    return f"{minutes:.1f} min"


def format_bandwidth_seconds(seconds: float) -> str:
    if seconds < 1.0:
        return f"{seconds * 1000:.0f} ms"
    if seconds < 60:
        return f"{seconds:.2f} s"
    return f"{seconds / 60:.1f} min"


def pct(value: float, denom: float) -> float:
    return (value / denom * 100.0) if denom else 0.0
