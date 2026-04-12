# Research Log — AoE2 / aoe2companion

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

AoE2 / aoe2companion findings. Reverse chronological.

---

## 2026-04-12 — [Phase 01 / Step 01_01_02] Schema discovery of aoe2companion raw files

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** content
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.md`

### What

Applied full census schema discovery across all 4 file types in the aoe2companion dataset. `discover_parquet_schemas()` was run on all 2,073 `matches/` Parquet files (metadata-only read). `discover_csv_schema(sample_rows=50)` was run on all 2,072 `ratings/` CSV files (header + 50 rows per file). `discover_parquet_schema()` was run on the singleton `leaderboard.parquet` and `profile.parquet` files. Schema consistency was checked within each subdirectory.

### Why

Step 01_01_02 establishes column-level structure of all raw files before any DuckDB ingestion design. Per Invariant #9, this step is limited to structure — not row counts, distributions, or semantic interpretation. Full census is used because `pyarrow.parquet.read_schema()` is metadata-only (sub-second per file) and `pd.read_csv(nrows=50)` reads only header + 50 rows.

### How (reproducibility)

```python
from rts_predict.common.parquet_utils import discover_parquet_schema, discover_parquet_schemas, discover_csv_schema

# matches/: full census Parquet
matches_result = discover_parquet_schemas(matches_parquet_files)

# ratings/: full census CSV (header + 50 rows each)
ratings_schemas = [discover_csv_schema(fp, sample_rows=50) for fp in ratings_csv_files]

# Singletons
leaderboard_schema = discover_parquet_schema(leaderboard_file)
profile_schema = discover_parquet_schema(profile_file)
```

Full derivation: `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_02_schema_discovery.ipynb`

### Findings

**matches/ (Parquet):**
- Total columns: 54
- Files checked: 2,073 of 2,073
- Schema consistency: True — all 2,073 files share identical schema
- Arrow types present: `int32`, `timestamp[ms, tz=UTC]`, `binary`, `bool`, `float`

**ratings/ (CSV):**
- Total columns: 7
- Column names: `profile_id`, `games`, `rating`, `date`, `leaderboard_id`, `rating_diff`, `season`
- Files checked: 2,072 of 2,072
- Schema consistency: True — all 2,072 files share identical schema
- Inferred types: all 7 columns inferred as `object` from 50-row sample

**leaderboards/leaderboard.parquet (singleton):**
- Total columns: 18
- Arrow types present: `int32`, `binary`, `timestamp[ms, tz=UTC]`, `bool`

**profiles/profile.parquet (singleton):**
- Total columns: 13
- Arrow types present: `int32`, `binary`, `bool`

### Decisions taken

- None — observation only.

### Decisions deferred

- CSV type inference yielded `object` for all 7 ratings columns (pandas default for heterogeneous or string-typed columns with 50-row sample). Concrete type assignment deferred to DuckDB ingestion step.
- DuckDB type proposals for all file types deferred to ingestion design.
- Whether `binary` Arrow type in Parquet files represents encoded strings or byte arrays requires content-level inspection (Step 01_03).

### Thesis mapping

- Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data: column schemas for matches, ratings, leaderboards, and profiles.

### Open questions / follow-ups

- The `ratings/` CSV columns are all inferred as `object` from 50-row sampling; whether the actual types are numeric or string across the full population requires Step 01_03 profiling.
- The `binary` type for many `matches/` Parquet columns (e.g., `name`, `server`, `map`, `civ`) may indicate variable-length byte encoding; actual encoding must be established at content-level inspection.
- The `won` column is present in `matches/` (not in ratings); its relationship to outcome labeling must be established in Step 01_02/01_03.

---

## 2026-04-12 — [Phase 01 / Step 01_01_01] File inventory of aoe2companion raw directory

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** filesystem
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md`

### What

Walked the aoe2companion raw directory (`src/rts_predict/games/aoe2/datasets/aoe2companion/data/raw`) using `inventory_directory()`, which performs a pure filesystem glob and stat walk (no file reads). Counted files, measured byte sizes, listed extensions, extracted dates from filenames using the regex `(\d{4}-\d{2}-\d{2})`, and identified gaps between consecutive dated filenames. Results written to JSON and Markdown artifacts.

### Why

Step 01_01_01 establishes the filesystem baseline for all downstream exploration steps. Per Manual 01_DATA_EXPLORATION and Invariant #6, all analytical results must be reported alongside the code that produced them. Per Invariant #9, conclusions at this step are limited to what is observable from the filesystem (filenames, sizes, counts, date patterns in names).

### How (reproducibility)

```python
from rts_predict.common.inventory import inventory_directory
from rts_predict.common.filename_patterns import summarize_filename_patterns
import re
from datetime import date

result = inventory_directory(RAW_DIR)

DATE_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})")
# For each subdirectory: extract dates from file stems, sort, find gaps > 1 day.

all_files = result.files_at_root + [f for sd in result.subdirs for f in sd.files]
patterns = summarize_filename_patterns(all_files)
```

Full derivation: `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.ipynb`

### Findings

- Raw directory: `src/rts_predict/games/aoe2/datasets/aoe2companion/data/raw`
- Total files: 4153
- Total size: 9387.80 MB (9,843,818,592 bytes)
- Subdirectory count: 4 (`leaderboards/`, `matches/`, `profiles/`, `ratings/`)
- Files at root level (not in any subdirectory): 2

**Per-subdirectory breakdown:**

| Subdirectory | Files | Size (MB) | Extensions |
|---|---|---|---|
| `leaderboards/` | 2 | 83.32 | `.gitkeep`: 1, `.parquet`: 1 |
| `matches/` | 2074 | 6621.52 | `.gitkeep`: 1, `.parquet`: 2073 |
| `profiles/` | 2 | 161.84 | `.gitkeep`: 1, `.parquet`: 1 |
| `ratings/` | 2073 | 2519.59 | `.gitkeep`: 1, `.csv`: 2072 |

**Date range analysis (extracted from filenames):**

- `matches/`: 2073 files with dates, 2020-08-01 to 2026-04-04, no gaps
- `ratings/`: 2072 files with dates, 2020-08-01 to 2026-04-04, 1 gap (2025-07-10 → 2025-07-12, 2 days)
- `leaderboards/`: no date pattern in filenames
- `profiles/`: no date pattern in filenames

**Filename patterns (whole-tree):**

| Pattern | Count |
|---|---|
| `match-{date}.parquet` | 2073 |
| `rating-{date}.csv` | 2072 |
| `.gitkeep` | 4 |
| `README.md` | 1 |
| `_download_manifest.json` | 1 |
| `leaderboard.parquet` | 1 |
| `profile.parquet` | 1 |

### Decisions taken

- None — observation only.

### Decisions deferred

- Whether the 2-day gap in `ratings/` (2025-07-10 → 2025-07-12) is consequential for the analysis must be assessed in a later step that reads file content.
- Interpretation of `_download_manifest.json`, `leaderboard.parquet`, and `profile.parquet` semantics deferred to Step 01_01_02 (content profiling).
- Relationship between file count in `matches/` (2073) and `ratings/` (2072) cannot be determined at filesystem scope.

### Thesis mapping

- Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data

### Open questions / follow-ups

- `leaderboards/` and `profiles/` each hold exactly 1 `.parquet` file with no date pattern; their schema and update cadence are unknown at this step.
- `matches/` has 2073 dated `.parquet` files naming pattern `match-{date}.parquet`; `ratings/` has 2072 `rating-{date}.csv` files — the one-file count difference warrants investigation in Step 01_01_02.
- The 2-day gap in `ratings/` (2025-07-10 → 2025-07-12) is the only gap found; its cause cannot be determined from filenames alone.

---
