"""
Text compression pipeline for HTML / CSS / JS.

Stages:
    1. Read source bytes (UTF-8 with safe fallback).
    2. Pass through LZ77 sliding-window compressor -> token stream.
    3. Build Huffman code over the LZ77 token alphabet.
    4. Pack the bitstream into a custom .wzs binary container.

Stages 1-3 are 100% lossless. Decompression reverses them in the
opposite order.

The container format (binary, little-endian):
    magic   : 4 bytes  = b"WZS1"
    header  : 4 bytes  = uint32 length of JSON header
    json    : N bytes  = UTF-8 JSON describing frequencies, padding, etc.
    body    : remaining bytes = packed Huffman bitstream
"""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from src.algorithms.huffman import (
    HuffmanCoder,
    bitstring_to_bytes,
    bytes_to_bitstring,
)
from src.algorithms.lz77 import (
    LZ77Compressor,
    LZ77Decompressor,
    LZ77Token,
    symbol_stream_to_tokens,
    tokens_to_symbol_stream,
)

MAGIC = b"WZS1"


@dataclass
class TextCompressionStats:
    original_size: int
    compressed_size: int
    token_count: int
    unique_symbols: int
    huffman_codes: Dict[str, str]
    top_tokens: List[Tuple[str, int]]
    sample_matches: List[Tuple[int, int, int]]


class TextPipeline:
    """Lossless text compression pipeline."""

    def __init__(
        self,
        window_size: int = 4096,
        lookahead_size: int = 18,
        min_match: int = 3,
        max_chain: int = 64,
    ) -> None:
        self.lz = LZ77Compressor(
            window_size=window_size,
            lookahead_size=lookahead_size,
            min_match=min_match,
            max_chain=max_chain,
        )
        self.lz_decoder = LZ77Decompressor()

    # -----------------------------------------------------------------
    # API: bytes -> bytes
    # -----------------------------------------------------------------
    def compress_bytes(self, data: bytes) -> Tuple[bytes, TextCompressionStats]:
        tokens = self.lz.compress(data)
        symbol_stream = tokens_to_symbol_stream(tokens)

        coder = HuffmanCoder()
        coder.build(symbol_stream)
        bitstring = coder.encode(symbol_stream)
        body, padding = bitstring_to_bytes(bitstring)

        # Frequencies are serialized as parallel lists for JSON-safety
        freq_keys = list(coder.frequencies.keys())
        freq_values = [coder.frequencies[k] for k in freq_keys]
        # Each key is a tuple (offset, length, next_byte). JSON has no tuple
        # so we store them as 3-element lists.
        header = {
            "v": 1,
            "n_tokens": len(symbol_stream),
            "padding": padding,
            "freq_keys": [list(k) for k in freq_keys],
            "freq_values": freq_values,
            "original_size": len(data),
        }
        header_json = json.dumps(header, separators=(",", ":")).encode("utf-8")

        out = bytearray()
        out += MAGIC
        out += struct.pack("<I", len(header_json))
        out += header_json
        out += body

        # Stats for analytics / visualizer
        # Top tokens by frequency for the visualizer tab
        tops = sorted(coder.frequencies.items(), key=lambda kv: -kv[1])[:20]
        top_tokens = [(self._format_token(k), v) for k, v in tops]
        # Sample LZ77 matches (skip pure literals)
        sample_matches: List[Tuple[int, int, int]] = []
        for tok in tokens:
            if tok.length > 0:
                sample_matches.append(tok.as_tuple())
                if len(sample_matches) >= 12:
                    break
        # Code book preview (string keys for display)
        codes_preview: Dict[str, str] = {}
        for sym, code in coder.codes.items():
            codes_preview[self._format_token(sym)] = code
            if len(codes_preview) >= 20:
                break

        stats = TextCompressionStats(
            original_size=len(data),
            compressed_size=len(out),
            token_count=len(tokens),
            unique_symbols=len(coder.frequencies),
            huffman_codes=codes_preview,
            top_tokens=top_tokens,
            sample_matches=sample_matches,
        )
        return bytes(out), stats

    def decompress_bytes(self, blob: bytes) -> bytes:
        if blob[:4] != MAGIC:
            raise ValueError("Not a WZS1 stream (magic mismatch).")
        header_size = struct.unpack("<I", blob[4:8])[0]
        header_json = blob[8:8 + header_size]
        body = blob[8 + header_size:]
        header = json.loads(header_json.decode("utf-8"))

        # Rebuild Huffman from frequencies
        freq_keys = [tuple(k) for k in header["freq_keys"]]
        freq_values = header["freq_values"]
        frequencies = dict(zip(freq_keys, freq_values))

        coder = HuffmanCoder()
        coder.build_from_frequencies(frequencies)

        bitstring = bytes_to_bitstring(body, header["padding"])
        symbols = coder.decode(bitstring, header["n_tokens"])
        tokens = symbol_stream_to_tokens(symbols)
        return self.lz_decoder.decompress(tokens)

    # -----------------------------------------------------------------
    # API: file -> file
    # -----------------------------------------------------------------
    def compress_file(self, src: Path, dst: Path) -> TextCompressionStats:
        data = src.read_bytes()
        out, stats = self.compress_bytes(data)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(out)
        return stats

    def decompress_file(self, src: Path, dst: Path) -> int:
        blob = src.read_bytes()
        data = self.decompress_bytes(blob)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        return len(data)

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------
    @staticmethod
    def _format_token(token) -> str:
        if isinstance(token, tuple) and len(token) == 3:
            offset, length, byte = token
            if length == 0:
                if byte == -1:
                    return "LIT(EOF)"
                ch = chr(byte) if 32 <= byte < 127 else f"\\x{byte:02x}"
                return f"LIT('{ch}')"
            return f"REF(off={offset},len={length},nxt={byte})"
        return str(token)
