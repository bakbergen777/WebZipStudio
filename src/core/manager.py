"""Compression and decompression orchestration.

Public API:
    CompressionManager(quality_preset="Balanced").compress_paths(paths, output_dir)
    DecompressionManager().decompress_package(package_dir, output_dir)
"""

from __future__ import annotations

import shutil
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Set

from src.core.archive import archive_package, open_archive, is_webzip_archive, ArchiveResult
from src.core.image_pipeline import ImagePipeline
from src.core.incremental import IncrementalCache
from src.core.integrity import sha256_bytes, sha256_file
from src.core.manifest import FileEntry, Manifest
from src.core.metrics import FileMetric, MetricsCollector
from src.core.strategy import StrategySelector
from src.core.text_pipeline import TextPipeline


ProgressCallback = Callable[[int, int, str], None]


@dataclass
class CompressionResult:
    output_dir: Path
    manifest: Manifest
    metrics: MetricsCollector
    text_visualizer_data: Dict[str, object] = field(default_factory=dict)
    incremental_summary: Dict[str, List[str]] = field(default_factory=dict)
    archive_path: Optional[Path] = None
    archive_size: int = 0


class CompressionManager:
    """Orchestrate text + image compression and produce a package."""

    def __init__(
        self,
        quality_preset: str = "Balanced",
        text_pipeline: Optional[TextPipeline] = None,
        image_pipeline: Optional[ImagePipeline] = None,
        selector: Optional[StrategySelector] = None,
    ) -> None:
        self.text = text_pipeline or TextPipeline()
        self.image = image_pipeline or ImagePipeline(preset=quality_preset)
        self.selector = selector or StrategySelector()

    # -----------------------------------------------------------------
    def compress_paths(
        self,
        sources: Iterable[Path],
        output_dir: Path,
        package_label: str = "",
        progress: Optional[ProgressCallback] = None,
        incremental: bool = False,
        base_dir: Optional[Path] = None,
        make_archive: bool = True,
        archive_path: Optional[Path] = None,
    ) -> CompressionResult:
        sources = [Path(p) for p in sources]
        files = self._expand_files(sources)
        if base_dir is None:
            base_dir = self._infer_base_dir(files)

        output_dir = Path(output_dir)
        compressed_dir = output_dir / "compressed"
        reports_dir = output_dir / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        compressed_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Incremental cache lookup
        cache_path = output_dir / "incremental_cache.json"
        previous_cache = IncrementalCache.read(cache_path) if incremental else IncrementalCache()
        current_hashes: Dict[str, str] = {}
        for f in files:
            rel = f.relative_to(base_dir).as_posix()
            current_hashes[rel] = sha256_file(f)
        unchanged, recompressed, added, removed = previous_cache.diff(current_hashes)
        skip_set: Set[str] = unchanged if incremental else set()

        manifest = Manifest(package_label=package_label or base_dir.name)
        metrics = MetricsCollector()
        # Queue the work — uses a basic FIFO queue (deque)
        work_queue = deque(files)

        # Visualizer data captured from the first sizable text file
        viz_data: Dict[str, object] = {}

        total = len(files)
        index = 0
        while work_queue:
            src = work_queue.popleft()
            index += 1
            relative = src.relative_to(base_dir).as_posix()
            if progress:
                progress(index, total, relative)

            strategy = self.selector.for_path(src)

            if relative in skip_set and incremental:
                # Reuse previous output if it still exists
                prior = self._find_previous_entry(previous_cache, relative)
                if prior is not None and (output_dir / prior).exists():
                    continue

            if strategy == "text":
                self._compress_text(src, base_dir, compressed_dir, manifest, metrics)
                if not viz_data and src.stat().st_size > 256:
                    viz_data = self._capture_viz(src)
            elif strategy == "image":
                self._compress_image(src, base_dir, compressed_dir, manifest, metrics)
            else:
                self._copy_as_is(src, base_dir, compressed_dir, manifest, metrics)

        metrics.finish()
        manifest.recompute_totals()
        manifest.write(output_dir / "manifest.json")

        # Update incremental cache
        IncrementalCache(hashes=current_hashes).write(cache_path)

        # Bundle the package into a single shareable archive
        archive_result: Optional[ArchiveResult] = None
        if make_archive:
            try:
                archive_result = archive_package(output_dir, archive_path)
            except Exception:
                archive_result = None

        return CompressionResult(
            output_dir=output_dir,
            manifest=manifest,
            metrics=metrics,
            text_visualizer_data=viz_data,
            incremental_summary={
                "unchanged": sorted(unchanged),
                "recompressed": sorted(recompressed),
                "added": sorted(added),
                "removed": sorted(removed),
            },
            archive_path=archive_result.archive_path if archive_result else None,
            archive_size=archive_result.archive_size if archive_result else 0,
        )

    # -----------------------------------------------------------------
    def _compress_text(
        self,
        src: Path,
        base_dir: Path,
        compressed_dir: Path,
        manifest: Manifest,
        metrics: MetricsCollector,
    ) -> None:
        rel = src.relative_to(base_dir)
        out_path = compressed_dir / (rel.as_posix() + ".wzs")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        original = src.read_bytes()
        original_hash = sha256_bytes(original)

        start = time.perf_counter()
        blob, _stats = self.text.compress_bytes(original)
        out_path.write_bytes(blob)
        elapsed = time.perf_counter() - start

        compressed_hash = sha256_bytes(blob)

        manifest.add(
            FileEntry(
                relative_path=rel.as_posix(),
                output_path=str(out_path.relative_to(compressed_dir.parent).as_posix()),
                strategy="text",
                original_size=len(original),
                compressed_size=len(blob),
                sha256_original=original_hash,
                sha256_compressed=compressed_hash,
            )
        )
        metrics.add(
            FileMetric(
                name=rel.as_posix(),
                strategy="text",
                original_size=len(original),
                compressed_size=len(blob),
                duration_seconds=elapsed,
            )
        )

    def _compress_image(
        self,
        src: Path,
        base_dir: Path,
        compressed_dir: Path,
        manifest: Manifest,
        metrics: MetricsCollector,
    ) -> None:
        rel = src.relative_to(base_dir)
        out_path = compressed_dir / rel
        start = time.perf_counter()
        stats = self.image.compress_file(src, out_path)
        elapsed = time.perf_counter() - start

        manifest.add(
            FileEntry(
                relative_path=rel.as_posix(),
                output_path=str(out_path.relative_to(compressed_dir.parent).as_posix()),
                strategy="image",
                original_size=stats.original_size,
                compressed_size=stats.compressed_size,
                sha256_original=sha256_file(src),
                sha256_compressed=sha256_file(out_path),
                image_preset=stats.preset,
                image_mode=stats.mode,
            )
        )
        metrics.add(
            FileMetric(
                name=rel.as_posix(),
                strategy="image",
                original_size=stats.original_size,
                compressed_size=stats.compressed_size,
                duration_seconds=elapsed,
                note=f"{stats.mode}/{stats.preset}",
            )
        )

    def _copy_as_is(
        self,
        src: Path,
        base_dir: Path,
        compressed_dir: Path,
        manifest: Manifest,
        metrics: MetricsCollector,
    ) -> None:
        rel = src.relative_to(base_dir)
        out_path = compressed_dir / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        start = time.perf_counter()
        shutil.copyfile(src, out_path)
        elapsed = time.perf_counter() - start
        size = out_path.stat().st_size

        manifest.add(
            FileEntry(
                relative_path=rel.as_posix(),
                output_path=str(out_path.relative_to(compressed_dir.parent).as_posix()),
                strategy="copy",
                original_size=size,
                compressed_size=size,
                sha256_original=sha256_file(src),
                sha256_compressed=sha256_file(out_path),
                note="unsupported extension; copied verbatim",
            )
        )
        metrics.add(
            FileMetric(
                name=rel.as_posix(),
                strategy="copy",
                original_size=size,
                compressed_size=size,
                duration_seconds=elapsed,
                note="copied",
            )
        )

    # -----------------------------------------------------------------
    def _capture_viz(self, src: Path) -> Dict[str, object]:
        """Return visualizer data for a representative text file."""
        data = src.read_bytes()
        _, stats = self.text.compress_bytes(data)
        return {
            "source_file": src.name,
            "original_size": stats.original_size,
            "compressed_size": stats.compressed_size,
            "token_count": stats.token_count,
            "unique_symbols": stats.unique_symbols,
            "huffman_codes": stats.huffman_codes,
            "top_tokens": stats.top_tokens,
            "sample_matches": stats.sample_matches,
        }

    # -----------------------------------------------------------------
    @staticmethod
    def _expand_files(paths: Iterable[Path]) -> List[Path]:
        # Set used here to deduplicate while keeping deterministic order
        out: List[Path] = []
        seen: Set[str] = set()
        for p in paths:
            p = Path(p).resolve()
            if p.is_dir():
                for child in sorted(p.rglob("*")):
                    if child.is_file():
                        rp = child.resolve()
                        key = str(rp)
                        if key not in seen:
                            seen.add(key)
                            out.append(rp)
            elif p.is_file():
                key = str(p)
                if key not in seen:
                    seen.add(key)
                    out.append(p)
        return out

    @staticmethod
    def _infer_base_dir(files: List[Path]) -> Path:
        if not files:
            return Path(".")
        if len(files) == 1:
            return files[0].parent
        try:
            common = Path(__import__("os").path.commonpath([str(f.resolve()) for f in files]))
            return common
        except ValueError:
            return files[0].parent

    @staticmethod
    def _find_previous_entry(cache: IncrementalCache, relative: str) -> Optional[str]:
        return relative if relative in cache.hashes else None


# ---------------------------------------------------------------------
class DecompressionManager:
    """Restore a package produced by CompressionManager."""

    def __init__(self, text_pipeline: Optional[TextPipeline] = None) -> None:
        self.text = text_pipeline or TextPipeline()

    def decompress_package(
        self,
        package: Path,
        output_dir: Path,
        progress: Optional[ProgressCallback] = None,
    ) -> Manifest:
        """Decompress a package folder OR a .webzip archive file."""
        package = Path(package)
        if package.is_file() and is_webzip_archive(package):
            with open_archive(package) as extracted:
                return self._decompress_folder(extracted, Path(output_dir), progress)
        return self._decompress_folder(package, Path(output_dir), progress)

    def _decompress_folder(
        self,
        package_dir: Path,
        output_dir: Path,
        progress: Optional[ProgressCallback] = None,
    ) -> Manifest:
        output_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = package_dir / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"manifest.json not found at {manifest_path}")
        manifest = Manifest.read(manifest_path)

        total = len(manifest.files)
        for index, entry in enumerate(manifest.files, start=1):
            if progress:
                progress(index, total, entry.relative_path)

            src = package_dir / entry.output_path
            dst = output_dir / entry.relative_path
            dst.parent.mkdir(parents=True, exist_ok=True)

            if entry.strategy == "text":
                self.text.decompress_file(src, dst)
            elif entry.strategy in ("image", "copy"):
                shutil.copyfile(src, dst)
            else:
                shutil.copyfile(src, dst)

        return manifest
