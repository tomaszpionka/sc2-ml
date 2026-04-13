# Research Log — AoE2 / aoe2companion

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

AoE2 / aoe2companion findings. Reverse chronological.

---

## 2026-04-13 — [Phase 01 / Step 01_02_01] DuckDB pre-ingestion investigation

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** query
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json`

### What

Ingested all four raw data sources into DuckDB (`matches_raw`, `ratings_raw`,
`leaderboards_raw`, `profiles_raw`) and validated column counts, types, and
null rates against 01_01_02 schema discovery findings.

### Why

Materialise the bronze layer for queryable exploration. Invariant #7 (type
fidelity) — verify DuckDB type inference matches Parquet/CSV source types.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py`

### Findings

- `matches_raw`: 277M rows, 55 columns (54 source + filename). `binary_as_string=true` resolved all 22 unannotated BYTE_ARRAY columns to VARCHAR
- `ratings_raw`: 58.3M rows, 8 columns. `read_csv_auto` inferred all 7 columns as VARCHAR at scale — required explicit `types=` parameter to get correct BIGINT/TIMESTAMP types
- `leaderboards_raw`: 2.38M rows, 19 columns (singleton Parquet)
- `profiles_raw`: 3.61M rows, 14 columns (singleton Parquet)
- Column counts match 01_01_02 expectations plus filename column in all tables
- `won` column: 12.99M NULLs out of 277M rows (4.7%) — matches without a recorded winner
- File count gap: 2,073 match files vs 2,072 rating files — `rating-2025-07-11.csv` is missing

### Decisions taken

- All Parquet reads use `binary_as_string=true` — Parquet files have unannotated BYTE_ARRAY columns that are actually UTF-8 strings
- CSV ratings use explicit type specification (never rely on `read_csv_auto` at scale for this dataset)
- Raw layer uses `SELECT *` with `filename=true` — no explicit DDL at this stage

### Decisions deferred

- Handling of 12.99M NULL `won` values — cleaning step decision
- Whether the missing rating file for 2025-07-11 is recoverable or should be documented as a gap
- Profile ID join strategy between matches and ratings (different column names: `profileId` vs `profile_id`)

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 match data ingestion, binary column handling, CSV type pitfall
- Chapter 4, §4.2.1 — Ingestion validation methodology

### Open questions / follow-ups

- What fraction of NULL `won` values are draws vs incomplete records?
- Does the `profileId`/`profile_id` naming inconsistency across tables indicate different source APIs?

---

## 2026-04-13 — [Phase 01 / Step 01_01_02] Schema discovery

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** content
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json`

### What

Full census of all 4,147 data files: Parquet metadata-only reads for matches,
leaderboards, and profiles; CSV header + 50-row samples for ratings.
Catalogued column names, physical types, and nullability.

### Why

Map the exact schema of each source before ingestion. Invariant #6 requires
knowing field names and types for reproducibility.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_02_schema_discovery.py`

### Findings

- Matches: 54 columns per Parquet file, consistent schema across all 2,073 daily files. 22 columns have unannotated BYTE_ARRAY physical type (no logical type annotation — Parquet files were written without UTF8 annotation)
- Ratings: 7 CSV columns (`profile_id`, `games`, `rating`, `date`, `leaderboard_id`, `rating_diff`, `season`), consistent across 2,072 files
- Leaderboards: 18 columns (singleton Parquet), 4 unannotated BYTE_ARRAY columns
- Profiles: 13 columns (singleton Parquet), 11 unannotated BYTE_ARRAY columns
- Schema is consistent within each file type — no variant columns detected

### Decisions taken

- Full census (not sampling) used because file counts are manageable (<4,200 files)
- BYTE_ARRAY without annotation flagged for `binary_as_string=true` at ingestion

### Decisions deferred

- Ingestion strategy deferred to 01_02_01

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset schema description

### Open questions / follow-ups

- Why do Parquet files lack UTF8 annotation on string columns? (upstream data source issue)

---

## 2026-04-13 — [Phase 01 / Step 01_01_01] File inventory

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** filesystem
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`

### What

Catalogued the aoe2companion raw data directory: 4 subdirectories (matches,
ratings, leaderboards, profiles), file counts, sizes, extensions, and
temporal coverage via filename date parsing.

### Why

Establish the data landscape. Invariant #9 — filesystem-level inventory before
content inspection.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.py`

### Findings

- 4,153 total files across 4 subdirectories, 9.2 GB total
- Matches: 2,073 daily Parquet files (6.6 GB), 2020-08-01 to 2026-04-04, no date gaps
- Ratings: 2,072 daily CSV files (2.5 GB), 2020-08-01 to 2026-04-04, no date gaps
- Leaderboards: 1 singleton Parquet (83 MB)
- Profiles: 1 singleton Parquet (162 MB)
- 1 file count gap: matches has 2,073 files, ratings has 2,072 (missing 2025-07-11)

### Decisions taken

- Temporal coverage spans ~5.7 years — sufficient for longitudinal analysis
- File count mismatch between matches and ratings noted for investigation

### Decisions deferred

- Internal file structure deferred to 01_01_02

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset description, temporal coverage, data volume

### Open questions / follow-ups

- None — straightforward inventory step
