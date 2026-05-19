# Test Plan

The test suite lives under `tests/` and runs with `python tests/run_all.py` (no pytest dependency required).

## Functional tests

| ID | Module | Scenario | Expected |
| --- | --- | --- | --- |
| F-01 | `test_huffman.py::test_round_trip_simple` | Build/encode/decode an English-like alphabet | decoded list equals input |
| F-02 | `test_huffman.py::test_single_symbol` | All symbols identical | restored list is identical |
| F-03 | `test_huffman.py::test_bit_packing` | Pack and unpack bitstring | exact bit equivalence |
| F-04 | `test_lz77.py::test_round_trip_empty` | Empty bytes | empty tokens, empty restoration |
| F-05 | `test_lz77.py::test_round_trip_basic` | Repeated phrase | tokens decode back to original |
| F-06 | `test_lz77.py::test_round_trip_html_like` | Repeated `<div><span>` chunk | at least one back-reference, exact restore |
| F-07 | `test_text_pipeline.py::test_pipeline_round_trip` | Real HTML | restored bytes equal source |
| F-08 | `test_text_pipeline.py::test_pipeline_empty` | Empty bytes | empty output, no exception |
| F-09 | `test_text_pipeline.py::test_pipeline_large` | 200 × repeated JS function | restored bytes equal source |
| F-10 | `test_manager.py::test_round_trip_webpage` | Compress + decompress whole sample webpage folder | every text file's restored SHA-256 matches the manifest |
| F-11 | `test_manager.py::test_run_twice_for_incremental` | Run twice with `incremental=True` | every sample file is reported as `unchanged` on the second run |

## Performance tests (run manually for the report)

These were executed on `data/sample_large_case` and the numbers are stored in `reports/demo_run_v2/metrics.json`:

```
Files: 16
Original: 153.82 KB
Compressed: 74.78 KB     -> 51.4% savings
Custom: 74.78 KB in 97.7 ms
gzip:   43.17 KB in  2.0 ms
zip:    44.46 KB in  6.9 ms
text strategy: 12 files, 41.10 KB -> 18.25 KB (55.6%)
image strategy: 4 files, 112.71 KB -> 56.53 KB (49.8%)
```

## Stability tests

| Scenario | Coverage |
| --- | --- |
| Missing manifest | `DecompressionManager.decompress_package` raises `FileNotFoundError`; the GUI shows a red dialog. |
| Corrupt `.wzs` | `TextPipeline.decompress_bytes` raises on the magic-number mismatch. |
| Unsupported extension | The file is copied verbatim and tagged `"copy"`. |
| Empty input file | Handled at the algorithm layer. |
| Output folder already exists | `output_dir.mkdir(parents=True, exist_ok=True)` keeps the run idempotent. |
| Drag-and-drop a non-file URL | `FileTable.dropEvent` ignores non-local URLs. |

## How to extend the test suite

1. Add new test functions starting with `test_` to a file in `tests/`.
2. Either include the module in `tests/run_all.py`'s `modules` list or run with `pytest`.
3. Keep tests deterministic — avoid external network or wall-clock dependencies.
