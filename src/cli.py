"""Command-line interface for WebZip Studio.

Usage:
    python -m src.cli compress  <input> [<input>...] -o <out_dir> [--preset Balanced]
    python -m src.cli decompress <package_dir> -o <restore_dir>
    python -m src.cli verify    <package_dir> <restore_dir>

Examples:
    python -m src.cli compress data/sample_webpage -o build/sample_pkg
    python -m src.cli decompress build/sample_pkg -o build/sample_restored
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from src.core.manager import CompressionManager, DecompressionManager
from src.core.integrity import sha256_file
from src.core.manifest import Manifest
from src.utils.formatting import format_duration, format_size


def _progress(i: int, t: int, name: str) -> None:
    bar = ("#" * int(40 * i / t)).ljust(40, ".") if t else "." * 40
    sys.stdout.write(f"\r[{bar}] {i}/{t} {name[:40]:40s}")
    sys.stdout.flush()
    if i == t:
        sys.stdout.write("\n")


def cmd_compress(args: argparse.Namespace) -> int:
    sources = [Path(p) for p in args.inputs]
    out = Path(args.output).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    mgr = CompressionManager(quality_preset=args.preset)
    result = mgr.compress_paths(
        sources,
        out,
        package_label=out.name,
        progress=_progress,
        incremental=args.incremental,
        make_archive=not args.no_archive,
    )

    totals = result.manifest.totals
    print(f"\nFiles      : {int(totals.get('file_count', 0))}")
    print(f"Original   : {format_size(totals.get('original_size', 0))}")
    print(f"Compressed : {format_size(totals.get('compressed_size', 0))}")
    print(f"Ratio      : {totals.get('ratio', 1.0):.3f}")
    print(f"Savings    : {totals.get('savings_pct', 0.0):.1f}%")
    cpu = result.metrics.totals().get('duration', 0.0)
    print(f"CPU time   : {format_duration(cpu)}")
    print(f"Output     : {result.output_dir}")
    if result.archive_path:
        print(f"Archive    : {result.archive_path}  ({format_size(result.archive_size)})")
    return 0


def cmd_decompress(args: argparse.Namespace) -> int:
    package = Path(args.package).expanduser()
    out = Path(args.output).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    manifest = DecompressionManager().decompress_package(
        package, out, progress=_progress
    )
    print(f"\nRestored {len(manifest.files)} file(s) to {out}")

    # Verify text round-trip
    ok = mismatch = missing = 0
    for entry in manifest.files:
        restored = out / entry.relative_path
        if entry.strategy == "text":
            if not restored.exists():
                missing += 1
            elif sha256_file(restored) == entry.sha256_original:
                ok += 1
            else:
                mismatch += 1
                print(f"MISMATCH: {entry.relative_path}")
    if ok or mismatch or missing:
        print(f"Text verification: {ok} match, {mismatch} mismatch, {missing} missing")
    return 0 if mismatch == 0 and missing == 0 else 2


def cmd_verify(args: argparse.Namespace) -> int:
    package = Path(args.package).expanduser()
    restored = Path(args.restored).expanduser()
    manifest = Manifest.read(package / "manifest.json")
    ok = mismatch = 0
    for entry in manifest.files:
        if entry.strategy != "text":
            continue
        path = restored / entry.relative_path
        if not path.exists():
            print(f"MISSING: {entry.relative_path}")
            mismatch += 1
            continue
        if sha256_file(path) != entry.sha256_original:
            print(f"MISMATCH: {entry.relative_path}")
            mismatch += 1
        else:
            ok += 1
    print(f"\n{ok} OK, {mismatch} bad")
    return 0 if mismatch == 0 else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="webzip",
        description="WebZip Studio command-line interface.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_c = sub.add_parser("compress", help="Compress files / folders")
    p_c.add_argument("inputs", nargs="+", help="Files or folders to compress")
    p_c.add_argument("-o", "--output", required=True, help="Output package folder")
    p_c.add_argument("--preset", default="Balanced",
                     choices=["High", "Balanced", "Strong"])
    p_c.add_argument("--incremental", action="store_true",
                     help="Skip files unchanged since the previous run")
    p_c.add_argument("--no-archive", action="store_true",
                     help="Do not produce the single-file .webzip archive")
    p_c.set_defaults(func=cmd_compress)

    p_d = sub.add_parser("decompress", help="Decompress a package or .webzip archive")
    p_d.add_argument("package", help="Package folder OR .webzip archive file")
    p_d.add_argument("-o", "--output", required=True, help="Restore folder")
    p_d.set_defaults(func=cmd_decompress)

    p_v = sub.add_parser("verify", help="Verify restored files match the manifest")
    p_v.add_argument("package", help="Package folder")
    p_v.add_argument("restored", help="Restore folder produced by `decompress`")
    p_v.set_defaults(func=cmd_verify)

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
