"""Estimate webpage transfer time over different network types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


# Network bandwidth assumptions (bits per second).
# These are configurable on purpose so the academic report can defend the
# numbers used for the simulation.
BANDWIDTHS_BPS: Dict[str, float] = {
    "4G":   12_000_000,    # 12 Mbps
    "5G":   100_000_000,   # 100 Mbps
    "WiFi": 50_000_000,    # 50 Mbps
}


@dataclass
class TransferEstimate:
    network: str
    seconds_before: float
    seconds_after: float

    @property
    def speedup(self) -> float:
        if self.seconds_after <= 0:
            return float("inf")
        return self.seconds_before / self.seconds_after


def estimate(original_bytes: int, compressed_bytes: int) -> Dict[str, TransferEstimate]:
    out: Dict[str, TransferEstimate] = {}
    for network, bps in BANDWIDTHS_BPS.items():
        before = (original_bytes * 8) / bps if bps > 0 else 0.0
        after = (compressed_bytes * 8) / bps if bps > 0 else 0.0
        out[network] = TransferEstimate(network, before, after)
    return out
