"""Bundle a package folder into a single shareable archive file.

The output is a standard ZIP archive (so any unzip tool can open it)
written with the `.webzip` extension to make the project's identity
clear. The archive contains:

    package_label/
        manifest.json
        incremental_cache.json
        compressed/...
        reports/...

Because the archive is a normal ZIP, decompression first unzips the
archive into a temporary folder, then runs the regular
DecompressionManager over the extracted package.
"""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


WEBZIP_SUFFIX = ".webzip"


@dataclass
class ArchiveResult:
    archive_path: Path
    archive_size: int


def archive_package(package_dir: Path, archive_path: Path | None = None,
                    *, compression: int = zipfile.ZIP_DEFLATED) -> ArchiveResult:
    """Pack `package_dir` into a single .webzip archive.

    `archive_path` defaults to `<package_dir>.webzip` next to the folder.
    """
    package_dir = Path(package_dir).resolve()
    if not package_dir.exists():
        raise FileNotFoundError(f"Package folder does not exist: {package_dir}")

    if archive_path is None:
        archive_path = package_dir.with_suffix(WEBZIP_SUFFIX)
    else:
        archive_path = Path(archive_path)

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if archive_path.exists():
        archive_path.unlink()

    base_name = package_dir.name
    with zipfile.ZipFile(archive_path, "w", compression=compression, compresslevel=6) as zf:
        for path in sorted(package_dir.rglob("*")):
            if not path.is_file():
                continue
            arcname = Path(base_name) / path.relative_to(package_dir)
            zf.write(path, arcname=str(arcname.as_posix()))

    return ArchiveResult(archive_path=archive_path,
                         archive_size=archive_path.stat().st_size)


@contextmanager
def open_archive(archive_path: Path) -> Iterator[Path]:
    """Yield the path to the package folder inside `archive_path`.

    The archive is extracted into a temporary directory; the caller gets
    the path of the *first* (and normally only) top-level folder. The
    temporary directory is cleaned up when the context exits.
    """
    archive_path = Path(archive_path)
    if not archive_path.exists():
        raise FileNotFoundError(archive_path)

    tmp = Path(tempfile.mkdtemp(prefix="webzip_extract_"))
    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(tmp)
        # Find the first directory entry — the manifest.json sits inside it
        candidates = [c for c in tmp.iterdir() if c.is_dir()]
        if not candidates:
            # Manifest might be at root of the archive
            yield tmp
        else:
            yield candidates[0]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def is_webzip_archive(path: Path) -> bool:
    path = Path(path)
    if not path.is_file():
        return False
    if path.suffix.lower() in (WEBZIP_SUFFIX, ".zip"):
        return zipfile.is_zipfile(path)
    return False
