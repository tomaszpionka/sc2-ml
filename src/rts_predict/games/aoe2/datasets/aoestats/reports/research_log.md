# Research Log — AoE2 / aoestats

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

AoE2 / aoestats findings. Reverse chronological.

---

## 2026-04-09 — [Phase 01 / Step 01_01_01] File Inventory

**Category:** A (science)
**Dataset:** aoestats
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md`

### What
Ran `inventory_directory()` on the raw directory of the aoestats dataset.
Produced per-subdirectory file counts, sizes, and extension distributions.
Extracted dates from filenames and checked for gaps. Compared paired
matches/players directories.

### Why
Step 01_01_01 is the first step of Phase 01 Data Exploration. Before any
DuckDB ingestion can be designed, we need an authoritative inventory of
what files exist. Per Scientific Invariant 6, these counts must be produced
by auditable code.

### How (reproducibility)
The notebook calls `inventory_directory(RAW_DIR)` from
`rts_predict.common.inventory` and writes the result to JSON and Markdown
artifacts. The notebook is the reproducibility record.

### Findings

**aoestats:** 349 total files across 3 subdirectories + 2 files at root.
Total size: 3,773.43 MB (~3.7 GB). Breakdown:
- `matches/`: 173 files (1 no-ext + 172 `.parquet`), 610.55 MB
- `players/`: 172 files (1 no-ext + 171 `.parquet`), 3,162.86 MB
- `overview/`: 2 files (1 no-ext + 1 `.json`), 0.02 MB

Date range for both matches and players: 2022-08-28 to 2026-02-07.
matches: 172 weekly files, 3 gaps (43 days, 8 days, 8 days).
players: 171 weekly files (1 missing — documented download failure for
2025-11-16_2025-11-22), same 3 gaps plus an 8-day gap confirming the
missing file.
Paired comparison (matches vs players): count_match=False (172 vs 171),
date_range_match=True. The asymmetry is the known missing file.

### What this means
The aoestats raw directory is non-empty and structurally sound. The
asymmetry (172 match files vs 171 player files) is consistent with the
documented download failure already noted in the ROADMAP source data
section — this is not a new finding. The 43-day gap (2024-07-20 to
2024-09-01) in matches is significant and should be documented in
01_01_02 analysis.

### Decisions taken
None specific to aoestats at this step.

### Decisions deferred
- Ingestion strategy depends on what we find in schema discovery (01_01_02/03).

### Thesis mapping
- Chapter 4 — Data and Methodology > 4.1 Datasets

### Open questions / follow-ups
- The 43-day gap in matches (2024-07-20 to 2024-09-01) is significant
  and should be documented in 01_01_02 analysis.
