# Research Log — AoE2 / aoe2companion

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

AoE2 / aoe2companion findings. Reverse chronological.

---

## 2026-04-09 — [Phase 01 / Step 01_01_01] File Inventory (aoe2companion)

**Category:** A (science)
**Dataset:** aoe2companion
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md`

### What
Ran `inventory_directory()` on the aoe2companion raw directory. Produced
per-subdirectory file counts, sizes, and extension distributions. Extracted
dates from filenames and checked for gaps.

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

**aoe2companion:** 4,154 total files across 4 subdirectories + 3 files at
root. Total size: 9,388.27 MB (~9.2 GB). Breakdown:
- `matches/`: 2,074 files (1 no-ext + 2,073 `.parquet`), 6,621.52 MB
- `ratings/`: 2,073 files (1 no-ext + 2,072 `.csv`), 2,519.59 MB
- `leaderboards/`: 2 files (1 no-ext + 1 `.parquet`), 83.32 MB (snapshot)
- `profiles/`: 2 files (1 no-ext + 1 `.parquet`), 161.84 MB (snapshot)
Date range for matches: 2020-08-01 to 2026-04-04, 2,073 daily files, no gaps.
Date range for ratings: 2020-08-01 to 2026-04-04, 2,072 daily files, 1 gap
(2025-07-10 to 2025-07-12, 2 days).

### What this means
The aoe2companion raw directory is non-empty and structurally sound. The
matches directory is daily and complete (no gaps). The ratings directory has
one 2-day gap in July 2025. Leaderboards and profiles are single snapshots.

### Decisions taken
None specific to aoe2companion at this step.

### Decisions deferred
- Ingestion strategy depends on what we find in schema discovery (01_01_02/03).

### Thesis mapping
- Chapter 4 — Data and Methodology > 4.1 Datasets

### Open questions / follow-ups
- The ratings 2-day gap (2025-07-10 to 2025-07-12) is minor but should be
  flagged in cleaning notes (Step 01_01_03 or Phase 02).
