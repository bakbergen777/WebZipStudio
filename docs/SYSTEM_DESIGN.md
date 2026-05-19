# System Design

## Overview

WebZip Studio is a desktop tool that compresses webpage resource files (HTML, CSS, JS, JPG, PNG) using a layered pipeline. Text resources are compressed losslessly with a custom LZ77 + Huffman pipeline. Image resources are compressed with Pillow at a user-chosen quality. A package manifest stores per-file metadata so decompression is deterministic and verifiable.

## Module map

| Module | Responsibility | Key data structures |
| --- | --- | --- |
| `algorithms/huffman.py` | Build frequency table, Huffman tree, encode/decode bitstrings | hash map, min-heap, binary tree |
| `algorithms/lz77.py` | Sliding-window matcher and decoder | bounded list (window), hash map (3-byte prefix index), list of tokens |
| `core/text_pipeline.py` | Wraps LZ77 + Huffman, produces `.wzs` container | dict (header) |
| `core/image_pipeline.py` | JPEG/PNG re-encoding with quality presets | dict |
| `core/strategy.py` | Maps file extension → strategy | hash map |
| `core/manifest.py` | Package manifest read/write | dataclasses + dict |
| `core/metrics.py` | Per-file timing and ratio collection | list of dataclasses |
| `core/comparison.py` | gzip/ZIP baselines | list (file enumeration) |
| `core/transfer.py` | 4G/5G/WiFi simulation | dict |
| `core/integrity.py` | SHA-256 helpers | n/a |
| `core/incremental.py` | Hash-cache for incremental runs | dict + set |
| `core/manager.py` | Orchestrates compression and decompression | queue (`deque`) |
| `gui/*` | PySide6 main window + five tabs | Qt widgets |
| `utils/formatting.py` | Human-readable size/time formatters | n/a |

## Data flow — compression

```
            +-----------------+
 user files | StrategySelector|---- "text" -----> TextPipeline ------+
            +-----------------+                                       |
                  |                                                    v
                  +---- "image" ---> ImagePipeline ---------+   .wzs file
                                                            |        +
                                                            v        |
                                                    compressed/      |
                                                    image.jpg/png    |
                                                            |        |
                                                            +--+-----+
                                                               |
                                                               v
                                                       Manifest.json
                                                       MetricsCollector
                                                       IncrementalCache
                                                       reports/metrics.json
```

## Data flow — decompression

```
package_dir/manifest.json -> DecompressionManager
  for each entry:
    if strategy == "text":
        TextPipeline.decompress_file(.wzs -> original)
    if strategy in ("image", "copy"):
        copy file
  -> verification table in GUI compares restored hash to manifest hash
```

## Package format

```
package_dir/
  manifest.json           # version, totals, per-file entries, hashes
  incremental_cache.json  # SHA-256 cache for the next run
  compressed/
    <relative path>.wzs   # text files: custom LZ77+Huffman container
    <relative path>       # image files: re-encoded JPG or PNG
  reports/
    metrics.json          # per-file metrics from the last run
```

## `.wzs` container layout

```
offset 0   : 4 bytes  = magic "WZS1"
offset 4   : 4 bytes  = uint32 (header length, little-endian)
offset 8   : N bytes  = JSON header
                          {
                            "v": 1,
                            "n_tokens": <int>,
                            "padding": <int>,
                            "freq_keys":  [[off,len,nxt], ...],
                            "freq_values":[<int>, ...],
                            "original_size": <int>
                          }
offset 8+N : ...      = packed Huffman bitstream
```

The header lists the LZ77 token frequencies so the decoder can rebuild the same Huffman tree without sending the codes themselves.

## Algorithm rationale

| Choice | Why |
| --- | --- |
| LZ77 + Huffman for text | Demonstrates dictionary-based and entropy-based compression in one pipeline. Gives us a hash map (prefix index), heap (Huffman build), and binary tree (Huffman codes) — directly maps to course objectives. |
| Pillow for images | Lossy image compression is a separate, well-understood field. Re-implementing JPEG would not add academic value. The user-facing knob is the quality preset. |
| Custom `.wzs` container | Lets us carry per-file frequency tables without external dependencies, while keeping the format trivially inspectable in the report. |
| ZIP and gzip baselines | gzip uses Deflate (LZ77 + Huffman). Comparing against it makes the trade-off honest. |
| Incremental SHA-256 cache | Avoids reprocessing unchanged files in repeated runs. |

## Threading model

The GUI runs Qt's event loop on the main thread. Compression and decompression run on `QThread` subclasses (`CompressWorker`, `DecompressWorker`) and emit signals back to the GUI. The progress bar, status label, and file table update from those signals — the UI never freezes.

## Error handling

- Manifest missing or corrupted → user-facing dialog, no partial restore.
- Unsupported extension → file is copied verbatim and tagged `"copy"` in the manifest, never silently dropped.
- Empty input → handled at the algorithm layer (`Huffman.decode` and the LZ77 loop both return empty).
- Decoder integrity failure → `MISMATCH` row in the verification table.
