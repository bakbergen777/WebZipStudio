"""
Huffman coding implementation.

Data structures used:
    - Hash map (dict) for frequency counting and code lookup
    - Min-heap (priority queue) for tree construction
    - Binary tree (HuffmanNode) for code generation

Time complexity:
    - Frequency counting: O(n)
    - Tree construction: O(k log k), k = unique symbols
    - Encoding: O(n)
    - Decoding: O(n)
Space complexity:
    - O(k) for tree, table, and code book
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple


@dataclass(order=True)
class HuffmanNode:
    """A node of the Huffman binary tree.

    Comparable by (frequency, tiebreaker) so it can live in a min-heap.
    """

    frequency: int
    tiebreaker: int = field(compare=True)
    symbol: Optional[Any] = field(default=None, compare=False)
    left: Optional["HuffmanNode"] = field(default=None, compare=False)
    right: Optional["HuffmanNode"] = field(default=None, compare=False)

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


class HuffmanCoder:
    """Encode and decode symbol streams using Huffman coding.

    The class works on a generic symbol alphabet (any hashable token)
    so it can be reused for raw bytes or for the LZ77 token stream.
    """

    def __init__(self) -> None:
        self.root: Optional[HuffmanNode] = None
        self.codes: Dict[Any, str] = {}
        self.frequencies: Dict[Any, int] = {}

    # ---------------------------------------------------------------
    # Tree construction
    # ---------------------------------------------------------------
    def build(self, symbols: Iterable[Any]) -> None:
        """Build frequency table, tree, and code book from a symbol iterable."""
        self.frequencies = self._count_frequencies(symbols)
        self.root = self._build_tree(self.frequencies)
        self.codes = self._build_codes(self.root)

    def build_from_frequencies(self, frequencies: Dict[Any, int]) -> None:
        self.frequencies = dict(frequencies)
        self.root = self._build_tree(self.frequencies)
        self.codes = self._build_codes(self.root)

    @staticmethod
    def _count_frequencies(symbols: Iterable[Any]) -> Dict[Any, int]:
        # Hash map / dictionary use #1: frequency table
        table: Dict[Any, int] = {}
        for symbol in symbols:
            table[symbol] = table.get(symbol, 0) + 1
        return table

    @staticmethod
    def _build_tree(frequencies: Dict[Any, int]) -> Optional[HuffmanNode]:
        if not frequencies:
            return None

        # Min-heap / priority queue use: pick two least-frequent nodes
        heap: List[HuffmanNode] = []
        counter = 0
        for symbol, freq in frequencies.items():
            heapq.heappush(heap, HuffmanNode(freq, counter, symbol=symbol))
            counter += 1

        # Special case: single unique symbol — make a degenerate tree
        if len(heap) == 1:
            only = heapq.heappop(heap)
            parent = HuffmanNode(only.frequency, counter, left=only, right=None)
            return parent

        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            merged = HuffmanNode(
                frequency=left.frequency + right.frequency,
                tiebreaker=counter,
                left=left,
                right=right,
            )
            counter += 1
            heapq.heappush(heap, merged)

        return heap[0]

    @staticmethod
    def _build_codes(root: Optional[HuffmanNode]) -> Dict[Any, str]:
        codes: Dict[Any, str] = {}
        if root is None:
            return codes
        if root.is_leaf:
            # Single-symbol corner case
            codes[root.symbol] = "0"
            return codes

        # DFS over the binary tree to build the code book
        stack: List[Tuple[HuffmanNode, str]] = [(root, "")]
        while stack:
            node, path = stack.pop()
            if node.is_leaf:
                codes[node.symbol] = path or "0"
                continue
            if node.left is not None:
                stack.append((node.left, path + "0"))
            if node.right is not None:
                stack.append((node.right, path + "1"))
        return codes

    # ---------------------------------------------------------------
    # Encode / decode
    # ---------------------------------------------------------------
    def encode(self, symbols: Iterable[Any]) -> str:
        """Return the bitstring encoding of `symbols`."""
        symbols = list(symbols)
        if not symbols:
            return ""
        if not self.codes:
            raise RuntimeError("HuffmanCoder.build() must be called before encode().")
        out: List[str] = []
        for symbol in symbols:
            out.append(self.codes[symbol])
        return "".join(out)

    def decode(self, bitstring: str, length: int) -> List[Any]:
        """Decode a bitstring into a list of `length` symbols."""
        if length == 0:
            return []
        if self.root is None:
            raise RuntimeError("HuffmanCoder has no tree to decode against.")
        result: List[Any] = []
        node = self.root
        # Single-symbol degenerate tree
        if node.is_leaf:
            return [node.symbol] * length

        for bit in bitstring:
            node = node.left if bit == "0" else node.right
            if node is None:
                raise ValueError("Corrupt Huffman bitstream.")
            if node.is_leaf:
                result.append(node.symbol)
                node = self.root
                if len(result) == length:
                    break
        return result

    # ---------------------------------------------------------------
    # Helpers used by visualizer + manifest
    # ---------------------------------------------------------------
    def code_table(self) -> Dict[Any, str]:
        return dict(self.codes)

    def tree_to_dict(self) -> Optional[dict]:
        """Return a JSON-friendly representation of the Huffman tree."""
        if self.root is None:
            return None

        def walk(node: HuffmanNode) -> dict:
            if node.is_leaf:
                return {"leaf": True, "symbol": node.symbol, "freq": node.frequency}
            return {
                "leaf": False,
                "freq": node.frequency,
                "left": walk(node.left) if node.left is not None else None,
                "right": walk(node.right) if node.right is not None else None,
            }

        return walk(self.root)


# ---------------------------------------------------------------------
# Bit packing helpers
# ---------------------------------------------------------------------
def bitstring_to_bytes(bitstring: str) -> Tuple[bytes, int]:
    """Pack a bitstring into bytes; return (data, padding_bits)."""
    if not bitstring:
        return b"", 0
    padding = (8 - len(bitstring) % 8) % 8
    if padding:
        bitstring = bitstring + ("0" * padding)
    out = bytearray(len(bitstring) // 8)
    for i in range(0, len(bitstring), 8):
        out[i // 8] = int(bitstring[i:i + 8], 2)
    return bytes(out), padding


def bytes_to_bitstring(data: bytes, padding: int) -> str:
    if not data:
        return ""
    bits = "".join(f"{b:08b}" for b in data)
    if padding:
        bits = bits[:-padding] if padding < len(bits) else ""
    return bits
