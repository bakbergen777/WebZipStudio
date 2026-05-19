"""Tests for the compression manager (end to end)."""
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.manager import CompressionManager, DecompressionManager
from src.core.integrity import sha256_file


def test_round_trip_webpage():
    sample = Path(__file__).resolve().parents[1] / "data" / "sample_webpage"
    assert sample.exists(), f"Sample data missing: {sample}"

    with tempfile.TemporaryDirectory() as tmp:
        package_dir = Path(tmp) / "pkg"
        restore_dir = Path(tmp) / "restored"

        manager = CompressionManager(quality_preset="Balanced")
        result = manager.compress_paths([sample], package_dir, package_label="sample")
        assert result.manifest.totals["file_count"] >= 4

        # Restore
        DecompressionManager().decompress_package(package_dir, restore_dir)

        # Verify text files match exactly
        for entry in result.manifest.files:
            if entry.strategy == "text":
                restored = restore_dir / entry.relative_path
                assert restored.exists()
                assert sha256_file(restored) == entry.sha256_original


def test_run_twice_for_incremental():
    sample = Path(__file__).resolve().parents[1] / "data" / "sample_webpage"
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out"
        manager = CompressionManager(quality_preset="Balanced")
        manager.compress_paths([sample], out, incremental=True)
        result2 = manager.compress_paths([sample], out, incremental=True)
        # All sample files should be detected as unchanged on the second run
        assert len(result2.incremental_summary["unchanged"]) >= 4


if __name__ == "__main__":
    test_round_trip_webpage()
    test_run_twice_for_incremental()
    print("Manager OK")
