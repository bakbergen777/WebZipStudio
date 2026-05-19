"""Core orchestration package for WebZip Studio."""

from .manager import CompressionManager, DecompressionManager, CompressionResult
from .manifest import Manifest, FileEntry
from .metrics import MetricsCollector, FileMetric
from .strategy import StrategySelector, EXTENSION_STRATEGY
from .integrity import sha256_bytes, sha256_file, files_match
from .transfer import estimate, BANDWIDTHS_BPS, TransferEstimate
from .comparison import compare_against_baselines, gzip_size, zip_size_for_files
from .incremental import IncrementalCache
from .text_pipeline import TextPipeline, TextCompressionStats
from .image_pipeline import ImagePipeline, ImageCompressionStats, QUALITY_PRESETS
from .archive import archive_package, open_archive, is_webzip_archive, ArchiveResult

__all__ = [
    "CompressionManager",
    "DecompressionManager",
    "CompressionResult",
    "Manifest",
    "FileEntry",
    "MetricsCollector",
    "FileMetric",
    "StrategySelector",
    "EXTENSION_STRATEGY",
    "sha256_bytes",
    "sha256_file",
    "files_match",
    "estimate",
    "BANDWIDTHS_BPS",
    "TransferEstimate",
    "compare_against_baselines",
    "gzip_size",
    "zip_size_for_files",
    "IncrementalCache",
    "TextPipeline",
    "TextCompressionStats",
    "ImagePipeline",
    "ImageCompressionStats",
    "QUALITY_PRESETS",
]
