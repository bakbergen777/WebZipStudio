"""Algorithm package for WebZip Studio.

Modules
-------
huffman:
    Huffman coder/decoder built on a min-heap priority queue and a binary tree.
lz77:
    Sliding-window LZ77 compressor/decompressor with a hash-map prefix index.
"""

from .huffman import (
    HuffmanCoder,
    HuffmanNode,
    bitstring_to_bytes,
    bytes_to_bitstring,
)
from .lz77 import (
    LZ77Compressor,
    LZ77Decompressor,
    LZ77Token,
    tokens_to_symbol_stream,
    symbol_stream_to_tokens,
)

__all__ = [
    "HuffmanCoder",
    "HuffmanNode",
    "bitstring_to_bytes",
    "bytes_to_bitstring",
    "LZ77Compressor",
    "LZ77Decompressor",
    "LZ77Token",
    "tokens_to_symbol_stream",
    "symbol_stream_to_tokens",
]
