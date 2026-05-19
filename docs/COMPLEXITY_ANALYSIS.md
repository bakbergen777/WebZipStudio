# Complexity Analysis

Symbols used in this document:

- `n` = number of bytes in the input file
- `k` = number of unique LZ77 tokens (alphabet size after preprocessing)
- `w` = sliding window size (default 4096)
- `c` = max chain length explored per match attempt (default 64)
- `B` = number of files in a batch
- `N` = total bytes across all files in a batch

## Huffman coder

| Operation | Time | Space |
| --- | --- | --- |
| Frequency counting | O(n) | O(k) |
| Tree construction (heap-based) | O(k log k) | O(k) |
| Code-book derivation (DFS) | O(k) | O(k) |
| Encoding | O(n) | O(n) for the bitstring |
| Decoding | O(n) | O(n) |

The min-heap operations dominate the construction phase. With at most 256 raw byte values + LZ77 token combinations the alphabet is bounded, so the tree build is effectively O(1) compared to encoding.

## LZ77 compressor

The compressor maintains a hash-map prefix index `prefix[3-byte] -> list of positions`. For each position it walks the bucket but stops after `c` candidates and never crosses the window boundary.

| Operation | Time | Space |
| --- | --- | --- |
| Match search at one position | O(c · ℓ) where ℓ ≤ lookahead | bounded |
| Whole-input compression | O(n · c · ℓ) ≈ O(n) since c and ℓ are constants | O(w) for the window + O(n) for tokens |
| Decoding | O(n) | O(n) |

The naive LZ77 (no hash index) would be O(n · w · ℓ) — quadratic in `n` for moderately repetitive inputs. Our hashing makes the dictionary lookup amortized constant time, which is the same trick that powers gzip/Deflate.

## Text pipeline (LZ77 + Huffman + container)

| Stage | Time | Space |
| --- | --- | --- |
| LZ77 tokenization | O(n) | O(n) |
| Huffman tree | O(k log k) | O(k) |
| Encode | O(n) | O(n) |
| Container write | O(k + n) | O(k + n) |
| Decompression | O(n) | O(n) |

## Image pipeline

Re-encoding is delegated to Pillow.

- JPEG: time is dominated by the DCT step in libjpeg, roughly O(p) where `p` is the pixel count.
- PNG: time is dominated by Deflate, again O(p).

This is intentionally outside the scope of the data structures we own; the academic focus stays on the text pipeline.

## Whole-batch compression

| Stage | Time |
| --- | --- |
| Strategy lookup (hash map) | O(B) |
| Per-file processing | sum over files |
| Manifest write | O(B) |
| Incremental cache write | O(B) |

Total wall time scales linearly with the total input size and slightly super-linearly with the per-file constants.

## Space budgets observed in practice

Running on `data/sample_large_case` (16 files, 153.82 KB):

| Component | Approx. peak resident memory |
| --- | --- |
| LZ77 token buffer | ~2× source size |
| Huffman bitstring | ~ source size |
| Manifest | ~ a few KB |

## Trade-offs documented for the report

1. The `.wzs` header lists the symbol frequencies. For very tiny files the header dominates and the compressed file may be larger than the input. This is expected — gzip uses pre-baked Huffman trees for small inputs to avoid the same problem.
2. We bound the LZ77 chain length to `c = 64`. Increasing `c` improves the compression ratio but reduces speed; the comparison panel exposes the trade-off.
3. The image pipeline is lossy by design. Hashing checks therefore apply only to text restoration.
