"""
LZ77-style sliding window compression.

Data structures used:
    - Sliding window (bounded list of recent bytes)
    - Hash map for fast match lookup (3-byte prefix -> list of positions)
    - List for the produced token stream

Token format:
    Triple (offset, length, next_byte). When `length == 0`, the token represents
    a literal byte (no back-reference).

Time complexity:
    - Encoding: O(n * average_chain_length); kept fast by capping chain length
      and clearing stale positions outside the sliding window.
    - Decoding: O(n).

Space complexity: O(window_size + n_tokens).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class LZ77Token:
    offset: int
    length: int
    next_byte: int  # 0..255; -1 used as a sentinel "no extra byte"

    def as_tuple(self) -> Tuple[int, int, int]:
        return (self.offset, self.length, self.next_byte)


class LZ77Compressor:
    """Tokenize input bytes into a list of LZ77 triples."""

    def __init__(
        self,
        window_size: int = 4096,
        lookahead_size: int = 18,
        min_match: int = 3,
        max_chain: int = 64,
    ) -> None:
        self.window_size = window_size
        self.lookahead_size = lookahead_size
        self.min_match = min_match
        self.max_chain = max_chain

    def compress(self, data: bytes) -> List[LZ77Token]:
        tokens: List[LZ77Token] = []
        n = len(data)
        if n == 0:
            return tokens

        # Hash map: 3-byte prefix -> list of positions (most recent first)
        prefix_index: dict = {}
        i = 0
        while i < n:
            # Look for the longest match that starts at position i
            best_offset = 0
            best_length = 0

            if i + self.min_match <= n:
                key = data[i:i + self.min_match]
                positions = prefix_index.get(key, [])
                # Walk recent positions, bounded by max_chain for speed
                checked = 0
                window_start = max(0, i - self.window_size)
                for pos in positions:
                    if pos < window_start:
                        break
                    if checked >= self.max_chain:
                        break
                    checked += 1

                    # Extend match
                    length = 0
                    max_length = min(self.lookahead_size, n - i)
                    while (
                        length < max_length
                        and data[pos + length] == data[i + length]
                    ):
                        length += 1

                    if length > best_length:
                        best_length = length
                        best_offset = i - pos
                        if length >= self.lookahead_size:
                            break

            if best_length >= self.min_match:
                next_byte_pos = i + best_length
                next_byte = data[next_byte_pos] if next_byte_pos < n else -1
                tokens.append(LZ77Token(best_offset, best_length, next_byte))

                # Insert all overlapping prefixes into the index for future matches
                for k in range(i, min(i + best_length + 1, n - self.min_match + 1)):
                    self._insert_prefix(prefix_index, data, k)

                step = best_length + (1 if next_byte != -1 else 0)
                i += step
            else:
                # Literal: length=0, next_byte=current
                tokens.append(LZ77Token(0, 0, data[i]))
                if i <= n - self.min_match:
                    self._insert_prefix(prefix_index, data, i)
                i += 1

            # Periodic prune of stale positions to keep chains short
            if (i & 0xFFF) == 0:
                self._prune_index(prefix_index, max(0, i - self.window_size))

        return tokens

    @staticmethod
    def _insert_prefix(index: dict, data: bytes, position: int) -> None:
        if position + 3 > len(data):
            return
        key = data[position:position + 3]
        bucket = index.get(key)
        if bucket is None:
            bucket = []
            index[key] = bucket
        bucket.insert(0, position)
        # Hard cap bucket size so a pathological repeated trigram does not blow up
        if len(bucket) > 256:
            del bucket[256:]

    @staticmethod
    def _prune_index(index: dict, lower_bound: int) -> None:
        for key, bucket in list(index.items()):
            kept = [p for p in bucket if p >= lower_bound]
            if kept:
                index[key] = kept
            else:
                del index[key]


class LZ77Decompressor:
    """Reverse a list of LZ77 tokens back into the original bytes."""

    def decompress(self, tokens: List[LZ77Token]) -> bytes:
        out = bytearray()
        for tok in tokens:
            if tok.length == 0:
                if tok.next_byte != -1:
                    out.append(tok.next_byte)
                continue
            start = len(out) - tok.offset
            if start < 0:
                raise ValueError("Corrupt LZ77 stream: offset out of range")
            for k in range(tok.length):
                out.append(out[start + k])
            if tok.next_byte != -1:
                out.append(tok.next_byte)
        return bytes(out)


# ---------------------------------------------------------------------
# Helpers for tokens <-> serializable form
# ---------------------------------------------------------------------
def tokens_to_symbol_stream(tokens: List[LZ77Token]) -> List[Tuple[int, int, int]]:
    return [t.as_tuple() for t in tokens]


def symbol_stream_to_tokens(stream) -> List[LZ77Token]:
    return [LZ77Token(int(o), int(l), int(b)) for (o, l, b) in stream]
