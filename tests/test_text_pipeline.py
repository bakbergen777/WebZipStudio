"""End-to-end pipeline tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.text_pipeline import TextPipeline


SAMPLE_HTML = b"""<!DOCTYPE html>
<html><head><title>Demo</title></head>
<body>
  <h1>Hello world</h1>
  <p>The quick brown fox jumps over the lazy dog.</p>
  <p>The quick brown fox jumps over the lazy dog.</p>
  <p>The quick brown fox jumps over the lazy dog.</p>
</body></html>"""


def test_pipeline_round_trip():
    p = TextPipeline()
    blob, stats = p.compress_bytes(SAMPLE_HTML)
    assert blob[:4] == b"WZS1"
    restored = p.decompress_bytes(blob)
    assert restored == SAMPLE_HTML
    # For tiny inputs the JSON header dominates; correctness is the priority.
    assert stats.original_size == len(SAMPLE_HTML)


def test_pipeline_empty():
    p = TextPipeline()
    blob, _ = p.compress_bytes(b"")
    assert p.decompress_bytes(blob) == b""


def test_pipeline_large():
    p = TextPipeline()
    big = (b"function feature(args) { return args.map(function (x) { return x * 2; }); }\n" * 200)
    blob, _ = p.compress_bytes(big)
    assert p.decompress_bytes(blob) == big


if __name__ == "__main__":
    test_pipeline_round_trip()
    test_pipeline_empty()
    test_pipeline_large()
    print("Text pipeline OK")
