# Defense Q&A

A short rehearsal sheet for the project defense.

### Q: Why did you pick LZ77 + Huffman?
A: They cover both of the major compression families in the course material — LZ77 is a dictionary scheme that uses a sliding window plus a hash-map prefix index, Huffman is an entropy coder built on a min-heap and a binary tree. Combining them gives us measurable savings on text and exercises five different data structures in one pipeline.

### Q: Which data structures are visible in the implementation?
A:
- Hash map: LZ77 prefix index, Huffman frequency table, extension-to-strategy map, incremental cache.
- Min-heap: Huffman tree construction (Python's `heapq`).
- Binary tree: Huffman code tree.
- Sliding window: LZ77 lookback buffer (bounded length).
- Queue: `collections.deque` used by `CompressionManager` to walk files.
- Set: dedup of file paths and incremental change detection.
- List/array: token streams, per-file metric tables.

### Q: Is text compression really lossless?
A: Yes. We verify it: every text file's pre-compression SHA-256 is recorded in the manifest, and the GUI's Decompress tab shows MATCH/MISMATCH after restoration. The test `test_round_trip_webpage` enforces this end-to-end.

### Q: Why is image compression lossy?
A: The user-facing knob is the quality preset (High / Balanced / Strong). JPEG is intrinsically lossy because of the DCT quantization step, and PNG palette reduction also changes pixels. We never silently swap formats and we expose the trade-off in the Compress tab.

### Q: How do you compare with ZIP and gzip?
A: After every batch we feed the same files through `gzip.compress(level=6)` and `ZipFile(compression=ZIP_DEFLATED)`. The Analytics tab shows the three numbers side by side. gzip almost always wins on raw ratio because it ships with pre-baked Huffman tables and a more aggressive LZ77 implementation; the goal of our system is academic clarity, not beating Deflate.

### Q: What is incremental compression?
A: After every run we write `incremental_cache.json` with each file's SHA-256. On the next run with the Incremental box ticked we skip files whose hash has not changed. The Incremental tab shows four buckets: UNCHANGED, RECOMPRESSED, ADDED, REMOVED.

### Q: How does the `.wzs` container work?
A: Magic `"WZS1"`, then `uint32` header length, then a JSON header listing the LZ77 token frequencies and the bit padding, then the packed Huffman bitstream. The decoder rebuilds the exact same Huffman tree from the frequencies, so we never have to ship the codes themselves.

### Q: What is the worst-case time complexity?
A: LZ77 dominates. Naive LZ77 is O(n · w · ℓ) but we cap the chain length at 64, so it is effectively O(n) in practice. Huffman is O(k log k), where `k` is the alphabet size. Decompression is strictly O(n).

### Q: How big is the alphabet for Huffman?
A: It is the set of unique LZ77 triples that appear in the input. In `sample_large_case` it stays in the low-thousands per file.

### Q: What happens on a tiny file?
A: The JSON header dominates; the compressed file may be larger than the input. We document this in `docs/COMPLEXITY_ANALYSIS.md`. gzip avoids this by shipping precomputed trees, which is a deliberate engineering trade we did not adopt.

### Q: Why a custom container instead of zlib?
A: Because the academic goal is to *show* the data structures. zlib would hide them. We still respect the format on disk: a magic word, a versioned header, deterministic decoding.

### Q: Why PySide6?
A: It is the official Qt for Python binding, has a mature `QThread` implementation, and works on Windows, macOS, and Linux without extra packaging. The GUI never freezes during compression because the work happens in a `QThread` subclass.

### Q: How do you handle very large batches?
A: The manager iterates files in a `deque`, so we never load every payload at once. Per-file metrics are appended to a list as work finishes.

### Q: How would you extend this to real webpages?
A: Tokenization could become language-aware (HTML tag table, CSS keyword table, JS keyword table) which would shrink the alphabet — `docs/SYSTEM_DESIGN.md` calls this out as a known follow-up. A second improvement is moving the Huffman frequency table to a shared dictionary across the whole batch.
