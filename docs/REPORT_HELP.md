# Report Help

How the codebase maps to the seven sections required by the course final report.

## A. Background

Use the introduction in `README.md` and the rationale in `docs/SYSTEM_DESIGN.md`. Key talking points:

- Webpages keep getting heavier; mobile networks pay for the bytes.
- Generic compression tools (gzip, zip) are black boxes for a course on data structures.
- A custom layered system makes the data structures visible and defensible.

## B. System Requirement

Pull the supported file types and feature list from `README.md` (HTML, CSS, JS, JPG, PNG; auto-detection; lossless text; controllable images; metrics; comparison; transfer simulation; integrity verification; incremental mode; GUI). Cross-reference the assignment brief.

## C. System Design

Lift the diagrams and module table directly from `docs/SYSTEM_DESIGN.md`. The sub-sections to include:

1. Module map (table)
2. Compression flow diagram
3. Decompression flow diagram
4. `.wzs` container format
5. Algorithm rationale (why LZ77 + Huffman, why Pillow for images, why a custom container)
6. Threading model (QThread workers)

## D. Demonstration

The Compress / Decompress / Analytics / Visualizer / Incremental tabs each deserve a screenshot. Numbers to quote:

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

The auto-generated charts at `assets/chart_compare.png`, `assets/chart_strategy.png`, and `assets/chart_per_file.png` can be embedded directly.

## E. Conclusion

- Lossless text restoration is verified by SHA-256 on every text file.
- Custom pipeline lags gzip's raw ratio because gzip ships pre-baked Huffman tables; the takeaway is that the academic system is *legible* and *correct*, not optimized to the last byte.
- Future work: language-aware tokenization (HTML/CSS/JS keyword tables) and a single shared dictionary across the whole batch.

## F. Contribution Clarification

| Member | Owns | Evidence |
| --- | --- | --- |
| Bakbergen Amir (202469990559) | Project lead, core algorithms (Huffman + LZ77), text pipeline, manifest, tests | `src/algorithms/`, `src/core/text_pipeline.py`, `tests/` |
| Bakbergen Alen (202469990562) | GUI design and integration (PySide6 main window + five tabs), workers, analytics | `src/gui/`, `src/core/comparison.py`, `src/core/transfer.py` |
| Huang Liu Diego David (202469990549) | Image pipeline, sample data, benchmarking, charts and report assets | `src/core/image_pipeline.py`, `data/sample_*`, `assets/chart_*.png` |

## G. Individual Report

The three personal reports under `reports/` follow the same template:

1. Personal information
2. Sections owned in the project
3. Key data structures the member implemented or used
4. Hardest problem they solved
5. What they learned
6. What they would change next time
