"""Tests for the .webzip archive flow."""
import sys
import tempfile
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.archive import archive_package, is_webzip_archive
from src.core.manager import CompressionManager, DecompressionManager
from src.core.integrity import sha256_file


def test_archive_round_trip_via_webzip():
    sample = Path(__file__).resolve().parents[1] / "data" / "sample_webpage"
    assert sample.exists(), f"Sample data missing: {sample}"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        package_dir = tmp_path / "pkg"
        restore_dir = tmp_path / "restored"

        manager = CompressionManager(quality_preset="Balanced")
        result = manager.compress_paths(
            [sample], package_dir, package_label="sample", make_archive=True
        )
        # Archive must exist and be a valid ZIP
        assert result.archive_path is not None
        assert result.archive_path.exists()
        assert is_webzip_archive(result.archive_path)
        assert zipfile.is_zipfile(result.archive_path)

        # Decompress directly from the .webzip archive
        manifest = DecompressionManager().decompress_package(result.archive_path, restore_dir)

        # Every text file restores to the exact original bytes
        for entry in manifest.files:
            if entry.strategy == "text":
                restored = restore_dir / entry.relative_path
                assert restored.exists()
                assert sha256_file(restored) == entry.sha256_original


def test_make_archive_disabled():
    sample = Path(__file__).resolve().parents[1] / "data" / "sample_webpage"
    with tempfile.TemporaryDirectory() as tmp:
        package_dir = Path(tmp) / "pkg"
        manager = CompressionManager(quality_preset="Balanced")
        result = manager.compress_paths(
            [sample], package_dir, package_label="no_arch", make_archive=False
        )
        assert result.archive_path is None
        assert result.archive_size == 0


if __name__ == "__main__":
    test_archive_round_trip_via_webzip()
    test_make_archive_disabled()
    print("Archive tests OK")
