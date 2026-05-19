# WebZip Studio — Webpage Compression System

Final project for the **Data Structure and its Algorithms** course.

| Member | Student ID |
| --- | --- |
| Bakbergen Amir | 202469990559 |
| Bakbergen Alen | 202469990562 |
| Huang Liu Diego David | 202469990549 |

## Purpose

WebZip Studio compresses the resource files of a webpage (HTML, CSS, JS, JPG, PNG) using a custom layered pipeline that is anchored in classic data structures:

- **Hash maps** for frequency tables and the LZ77 prefix index
- **Min-heap (priority queue)** to build the Huffman tree
- **Binary tree** to derive Huffman codes
- **Sliding window** for LZ77 matches
- **Queue** for batch processing
- **Sets** for deduplication and incremental change detection

For text resources the round trip is **lossless** and verified by SHA-256. For images the user picks a quality preset (High / Balanced / Strong) and the system uses Pillow to re-encode.

## Features

- Auto-detected strategy per file extension
- Single file, multiple files, or whole-folder compression
- Custom `.wzs` container for text (LZ77 + Huffman + JSON header)
- Quality-controlled JPEG/PNG re-encoding
- Decompression with SHA-256 integrity check
- Batch ZIP/gzip comparison
- 4G / 5G / WiFi transfer-time simulation
- Algorithm visualizer (top tokens, Huffman code book, LZ77 matches)
- Incremental compression that only reprocesses changed files

## Demo numbers (from `data/sample_large_case`)

```
Files: 16
Original: 153.82 KB
Compressed: 74.78 KB     -> 51.4% savings, ratio 0.486
Custom: 74.78 KB in 97.7 ms
gzip:   43.17 KB in  2.0 ms
zip:    44.46 KB in  6.9 ms
text strategy: 12 files, 41.10 KB -> 18.25 KB (55.6% savings)
image strategy: 4 files, 112.71 KB -> 56.53 KB (49.8% savings)
```

The numbers above are recomputed every run and saved to `reports/demo_run_v2/metrics.json`.

## How to run

### Desktop GUI

```bash
pip install -r requirements.txt
python main.py
```

The application opens a five-tab desktop window: **Compress**, **Decompress**, **Analytics**, **Visualizer**, **Incremental**. The Compress tab is laid out as four numbered steps (1. add files → 2. pick output folder → 3. choose quality → 4. click *Compress now*). `Ctrl+Enter` triggers compression.

### Command line (also works without a display server)

```bash
# Compress a folder — produces build/sample_pkg/  AND  build/sample_pkg.webzip
python -m src.cli compress data/sample_webpage -o build/sample_pkg --preset Balanced

# Decompress directly from the single-file archive
python -m src.cli decompress build/sample_pkg.webzip -o build/sample_restored

# (Or from the package folder — both work)
python -m src.cli decompress build/sample_pkg -o build/sample_restored

# Re-verify a previously restored package
python -m src.cli verify build/sample_pkg build/sample_restored
```

The CLI prints a progress bar, the compression ratio, the path of the resulting `.webzip` archive, and how many text files matched their original SHA-256 hash.

## Output formats

Every compression run produces two artefacts:

1. A **package folder** that contains `manifest.json`, `incremental_cache.json`, the `compressed/` files, and the per-run metrics under `reports/`. This folder is fully inspectable with any text editor or hex viewer.
2. A **single-file `.webzip` archive** of that folder, ready to email or upload. Internally it is a standard ZIP (compression level 6), so any unzip tool can open it. Decompression accepts either the folder or the archive interchangeably.

## How to test

```bash
python tests/run_all.py
```

The test runner exercises Huffman, LZ77, the text pipeline, and the end-to-end manager including the integrity verification path.

## Project layout

```
WebZipStudio/
  main.py                 # GUI entry point
  requirements.txt
  src/
    algorithms/           # Huffman + LZ77
    core/                 # pipelines, manifest, metrics, comparison, transfer
    gui/                  # PySide6 window + tabs
    utils/                # formatting helpers
    models/
  data/
    sample_webpage/       # tiny demo (HTML, CSS, JS, JPG, PNG)
    sample_large_case/    # 16-file batch used for the metrics in this README
  reports/                # populated by demo runs
  docs/                   # design + complexity + Q&A documents
  tests/                  # unit + integration tests
  assets/                 # charts used by report and slides
```

## Documentation map

- `docs/SYSTEM_DESIGN.md` — architecture, modules, data flow
- `docs/COMPLEXITY_ANALYSIS.md` — time/space complexity per algorithm
- `docs/TEST_PLAN.md` — test strategy
- `docs/DEFENSE_QA.md` — likely defense questions and answers
- `docs/REPORT_HELP.md` — mapping to the official report sections

## Algorithms in one paragraph

Text files are tokenized as raw bytes and run through an LZ77 sliding-window encoder that emits `(offset, length, next_byte)` triples. The resulting symbol stream is fed to a Huffman coder built on a min-heap, which produces a prefix code book. The bitstream is packed into a `.wzs` file with a small JSON header that records the symbol frequencies needed for decoding. Decompression reverses the process exactly. Image files use Pillow with quality presets so the user explicitly trades image fidelity for size.

## Limitations

- The custom text pipeline competes against gzip/zip on small batches; gzip is highly tuned and uses Deflate. The point of this project is to expose the data structures, not to beat Deflate. The comparison panel makes this trade-off visible.
- Image compression is lossy by design; we never silently swap formats.
- The single-file `.wzs` header carries the frequency table, so very tiny inputs may grow slightly. This is documented in `docs/COMPLEXITY_ANALYSIS.md`.
