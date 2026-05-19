"""Unit tests for Huffman coder."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.algorithms.huffman import HuffmanCoder, bitstring_to_bytes, bytes_to_bitstring


def test_round_trip_simple():
    coder = HuffmanCoder()
    symbols = list("the quick brown fox jumps over the lazy dog the the the")
    coder.build(symbols)
    bitstring = coder.encode(symbols)
    decoded = coder.decode(bitstring, len(symbols))
    assert decoded == symbols, "round trip mismatch"


def test_single_symbol():
    coder = HuffmanCoder()
    coder.build(["x"] * 12)
    bits = coder.encode(["x"] * 12)
    decoded = coder.decode(bits, 12)
    assert decoded == ["x"] * 12


def test_bit_packing():
    bits = "101011001110"
    blob, padding = bitstring_to_bytes(bits)
    assert bytes_to_bitstring(blob, padding) == bits


if __name__ == "__main__":
    test_round_trip_simple()
    test_single_symbol()
    test_bit_packing()
    print("Huffman OK")
