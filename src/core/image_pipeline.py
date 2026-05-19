"""
Image compression pipeline for JPG / PNG.

JPG: re-encoded with a quality knob (lossy but controllable).
PNG: re-saved with `optimize=True`. For large RGB PNGs, an optional
palette reduction is offered when the user asks for "Strong" mode.

The pipeline never silently changes file extensions and never converts
JPG <-> PNG, so the restored asset behaves like the original.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None  # type: ignore


QUALITY_PRESETS = {
    "High":     {"jpg_quality": 90, "png_optimize": True,  "png_palette": False},
    "Balanced": {"jpg_quality": 75, "png_optimize": True,  "png_palette": False},
    "Strong":   {"jpg_quality": 55, "png_optimize": True,  "png_palette": True},
}


@dataclass
class ImageCompressionStats:
    original_size: int
    compressed_size: int
    mode: str  # "jpg" or "png"
    preset: str


class ImagePipeline:
    """Re-encode JPG/PNG images at a chosen quality level."""

    def __init__(self, preset: str = "Balanced") -> None:
        if Image is None:
            raise RuntimeError("Pillow is required for image compression.")
        if preset not in QUALITY_PRESETS:
            raise ValueError(f"Unknown preset {preset!r}")
        self.preset = preset
        self.cfg = QUALITY_PRESETS[preset]

    def set_preset(self, preset: str) -> None:
        if preset not in QUALITY_PRESETS:
            raise ValueError(f"Unknown preset {preset!r}")
        self.preset = preset
        self.cfg = QUALITY_PRESETS[preset]

    # -----------------------------------------------------------------
    def compress_file(self, src: Path, dst: Path) -> ImageCompressionStats:
        ext = src.suffix.lower()
        original_size = src.stat().st_size
        dst.parent.mkdir(parents=True, exist_ok=True)

        if ext in (".jpg", ".jpeg"):
            with Image.open(src) as img:
                rgb = img.convert("RGB")
                rgb.save(
                    dst,
                    format="JPEG",
                    quality=int(self.cfg["jpg_quality"]),
                    optimize=True,
                    progressive=True,
                )
            mode = "jpg"
        elif ext == ".png":
            with Image.open(src) as img:
                out_img = img
                if self.cfg["png_palette"] and img.mode in ("RGB", "RGBA"):
                    try:
                        out_img = img.convert("P", palette=Image.ADAPTIVE, colors=256)
                    except Exception:
                        out_img = img
                out_img.save(
                    dst,
                    format="PNG",
                    optimize=bool(self.cfg["png_optimize"]),
                )
            mode = "png"
        else:
            raise ValueError(f"Unsupported image extension: {ext}")

        return ImageCompressionStats(
            original_size=original_size,
            compressed_size=dst.stat().st_size,
            mode=mode,
            preset=self.preset,
        )

    # Decompression for images is simply a copy — they are self-contained.
    @staticmethod
    def restore_file(src: Path, dst: Path) -> int:
        dst.parent.mkdir(parents=True, exist_ok=True)
        data = src.read_bytes()
        dst.write_bytes(data)
        return len(data)
