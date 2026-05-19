"""Unit tests for LZ77 compressor."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.algorithms.lz77 import LZ77Compressor, LZ77Decompressor


def test_round_trip_empty():
    comp = LZ77Compressor()
    decomp = LZ77Decompressor()
    assert decomp.decompress(comp.compress(b"")) == b""


def test_round_trip_basic():
    comp = LZ77Compressor()
    decomp = LZ77Decompressor()
    data = b"the quick brown fox jumps over the lazy dog. the the the the"
    tokens = comp.compress(data)
    assert decomp.decompress(tokens) == data


def test_round_trip_html_like():
    comp = LZ77Compressor()
    decomp = LZ77Decompressor()
    data = (b"<div class=\"x\"><span>hello</span></div>" * 32) + b"<p>foo</p>"
    tokens = comp.compress(data)
    assert decomp.decompress(tokens) == data
    # Some tokens should be back-references, otherwise we are not compressing
    assert any(t.length > 0 for t in tokens)


if __name__ == "__main__":
    test_round_trip_empty()
    test_round_trip_basic()
    test_round_trip_html_like()
    print("LZ77 OK")
