"""Background worker threads so the GUI never freezes."""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import List

from PySide6.QtCore import QThread, Signal

from src.core.manager import (
    CompressionManager,
    DecompressionManager,
    CompressionResult,
)


class CompressWorker(QThread):
    progress = Signal(int, int, str)
    finished_ok = Signal(object)             # CompressionResult
    failed = Signal(str)

    def __init__(
        self,
        sources: List[Path],
        output_dir: Path,
        preset: str,
        package_label: str,
        incremental: bool,
        make_archive: bool = True,
    ) -> None:
        super().__init__()
        self.sources = list(sources)
        self.output_dir = Path(output_dir)
        self.preset = preset
        self.package_label = package_label
        self.incremental = incremental
        self.make_archive = make_archive

    def run(self) -> None:  # noqa: D401
        try:
            mgr = CompressionManager(quality_preset=self.preset)
            result = mgr.compress_paths(
                self.sources,
                self.output_dir,
                package_label=self.package_label,
                progress=lambda i, t, name: self.progress.emit(i, t, name),
                incremental=self.incremental,
                make_archive=self.make_archive,
            )
            self.finished_ok.emit(result)
        except Exception as exc:
            details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            self.failed.emit(f"{exc}\n\n{details}")


class DecompressWorker(QThread):
    progress = Signal(int, int, str)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, package_dir: Path, output_dir: Path) -> None:
        super().__init__()
        self.package_dir = Path(package_dir)
        self.output_dir = Path(output_dir)

    def run(self) -> None:
        try:
            mgr = DecompressionManager()
            manifest = mgr.decompress_package(
                self.package_dir,
                self.output_dir,
                progress=lambda i, t, name: self.progress.emit(i, t, name),
            )
            self.finished_ok.emit(manifest)
        except Exception as exc:
            details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            self.failed.emit(f"{exc}\n\n{details}")
