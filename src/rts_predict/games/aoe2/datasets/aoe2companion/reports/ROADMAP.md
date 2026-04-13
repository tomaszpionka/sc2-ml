# aoe2companion Dataset Roadmap

**Game:** AoE2
**Dataset:** aoe2companion
**Canonical phase list:** `docs/PHASES.md`
**Methodology manuals:** `docs/INDEX.md`
**Step definition schema:** `docs/templates/step_template.yaml`
**Research log:** `research_log.md` (sibling file — per-dataset reverse-chronological narrative)

---

> **Role: TO BE DETERMINED.** Role assignment (PRIMARY vs SUPPLEMENTARY
> VALIDATION) will be formalized at the Phase 01 Decision Gate (01_06) based
> on comparative data quality findings. Until then, this dataset runs all
> Phases at full scope per `docs/PHASES.md`.

## How to use this document

This file decomposes Phases into Pipeline Sections and Steps for the aoe2companion
dataset. The canonical Phase definitions and Pipeline Section enumerations live
in `docs/PHASES.md`. This ROADMAP does not invent Phases or Pipeline Sections;
it only decomposes them into Steps.

Steps are defined in a planning session before Phase work begins.

Steps are numbered `XX_YY_ZZ` where `XX` = Phase, `YY` = Pipeline Section,
`ZZ` = Step within that Pipeline Section.

---

## Source data

**aoe2companion CDN dump** — community match history and rating dataset.
Downloaded 2026-04-06. File counts and date ranges are from
Step 01_01_01 (file inventory).

| Subdirectory | Files | Size (MB) | Extensions |
|---|---|---|---|
| `leaderboards/` | 2 | 83.32 | `.parquet`: 1, `.gitkeep`: 1 |
| `matches/` | 2074 | 6621.52 | `.parquet`: 2073, `.gitkeep`: 1 |
| `profiles/` | 2 | 161.84 | `.parquet`: 1, `.gitkeep`: 1 |
| `ratings/` | 2073 | 2519.59 | `.csv`: 2072, `.gitkeep`: 1 |

**Total files:** 4153 (including root-level `README.md` and `_download_manifest.json`)
**Total size:** 9387.80 MB

**Raw data is immutable. The API download will not be repeated.**
Acquisition provenance is recorded in
`src/rts_predict/games/aoe2/datasets/aoe2companion/reports/README.md`.

Row counts, schema, and column-level characteristics will be established
by Phase 01 Steps 01_01_02 (schema discovery) and 01_03 (systematic profiling).

---

## Phase 01 — Data Exploration

Pipeline Sections per `docs/PHASES.md`:

- `01_01` — Data Acquisition & Source Inventory
- `01_02` — Exploratory Data Analysis (Tukey-style)
- `01_03` — Systematic Data Profiling
- `01_04` — Data Cleaning
- `01_05` — Temporal & Panel EDA
- `01_06` — Decision Gates

### Step 01_01_01 — File Inventory

```yaml
step_number: "01_01_01"
name: "File Inventory"
description: "Walk the aoe2companion raw directory, count files, measure sizes, group by subdirectory."
phase: "01 — Data Exploration"
pipeline_section: "01_01 — Data Acquisition & Source Inventory"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 1"
dataset: "aoe2companion"
question: "What files exist on disk, how many are there, and how are they organized?"
method: "Call inventory_directory() on the raw directory. Report totals, per-subdirectory breakdown, extension distribution. Extract dates from filenames using regex and report date range and gaps per subdirectory."
stratification: "By subdirectory (matches, ratings, leaderboards, profiles)."
predecessors: "none — independent"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.py"
inputs:
  duckdb_tables: "none — reads filesystem only"
  external_references:
    - ".claude/scientific-invariants.md"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"
  report: "artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md"
reproducibility: "All counts produced by inventory_directory() from rts_predict.common.inventory. Code and output are in the paired notebook."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "Inventory counts are produced by code in the notebook, saved alongside the report."
  - number: "7"
    how_upheld: "No thresholds used — pure counting."
gate:
  artifact_check: "artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json and .md exist and are non-empty."
  continue_predicate: "Inventory artifacts exist on disk."
  halt_predicate: "Raw directory does not exist or is empty."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_01_02 — Schema Discovery

```yaml
step_number: "01_01_02"
name: "Schema Discovery"
description: "Read Parquet metadata and CSV headers from aoe2companion raw files. Discover column schemas for matches, ratings, leaderboards, and profiles. Check schema consistency across the temporal range."
phase: "01 — Data Exploration"
pipeline_section: "01_01 — Data Acquisition & Source Inventory"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 1"
dataset: "aoe2companion"
question: "What columns exist in each file type, what are their data types, and is the schema consistent across the temporal range?"
method: "Full census: pyarrow.parquet.read_schema() on all 2,073 files in matches/ (metadata-only, sub-second). Full census: pd.read_csv(nrows=50) on all 2,072 files in ratings/ (header + 50 rows for type inference). Read schema from singleton leaderboard.parquet and profile.parquet. Compare schemas within each subdirectory for consistency. Report column catalogs, Arrow/inferred types, and consistency verdicts. No DuckDB type proposals."
stratification: "By subdirectory. Full census within each — no sampling needed for Parquet metadata or CSV headers."
predecessors:
  - "01_01_01"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_02_schema_discovery.py"
inputs:
  duckdb_tables: "none — reads raw file metadata directly"
  prior_artifacts:
    - "artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - "docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md, Section 1"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json"
  report: "artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.md"
reproducibility: "Parquet schemas via pyarrow.parquet.read_schema() (full census on all files). CSV schemas via pd.read_csv(nrows=50) (full census, 50 rows per file for type inference — sufficient to detect type variation without full content read). Code and output in the paired notebook per Invariant #6."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "Schema profiles produced by code in the notebook, saved alongside the report."
  - number: "7"
    how_upheld: "Full census for Parquet (metadata-only, zero cost) and CSV (header + 50 rows). Census eliminates sample-size justification requirement."
  - number: "9"
    how_upheld: "Conclusions limited to column-level structural observations. No row counts or value distributions. No DuckDB type proposals."
gate:
  artifact_check: "artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json and .md exist and are non-empty."
  continue_predicate: "Schema artifacts exist and report a consistency verdict for all subdirectories."
  halt_predicate: "Any Parquet file fails to open."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_02_01 — DuckDB Ingestion

```yaml
step_number: "01_02_01"
name: "DuckDB Ingestion"
description: "Load aoe2companion Parquet and CSV files into DuckDB tables. Inspect pyarrow logical types for binary columns across all 3 Parquet subdirectories to determine whether binary_as_string=true is required. Validate CSV type inference for ratings. Verify row and column counts. Investigate matches/ratings file count gap (2073/2072)."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "aoe2companion"
question: "Can all aoe2companion files be loaded into DuckDB tables with correct type mappings, are binary columns unannotated BYTE_ARRAY requiring binary_as_string=true, are CSV types inferred correctly for ratings, do row counts align with file inventory, and what explains the 2073/2072 file count gap?"
method: "PYARROW INSPECTION: Run pyarrow.parquet.ParquetFile.schema on sample files from each subdirectory (matches, leaderboards, profiles) to determine binary column annotation status (parquet_logical, converted_type). If unannotated BYTE_ARRAY, binary_as_string=true is required; if annotated STRING/UTF8, DuckDB handles natively. Record per-subdirectory binary column counts and annotation status. Smoke test and pre-ingestion functions live in pre_ingestion.py. SMOKE TEST: ingest 3-5 Parquet files from matches/ (earliest, middle, latest by date) + 3-5 CSV from ratings/ into temp tables with binary_as_string=true (if justified by pyarrow inspection). Verify DESCRIBE: binary columns are VARCHAR (not BLOB), CSV-inferred types are reasonable (profile_id numeric, date parsed). Cross-check column schemas across smoke-test files to assess cross-file consistency. FULL INGESTION: CREATE TABLE matches_raw AS ...; CREATE TABLE ratings_raw AS ...; CREATE TABLE leaderboards_raw/profiles_raw from singletons with binary_as_string=true and filename=true (every raw table carries filename for provenance). POST-INGESTION: DESCRIBE all 4 tables — record full DuckDB-assigned types. GATE for ratings_raw: profile_id must be INTEGER/BIGINT, date must be DATE/TIMESTAMP, games/rating/rating_diff must be INTEGER — if any is VARCHAR, re-ingest with explicit types=. Row counts per table. Column count verification (matches_raw: 54+1 filename=55, ratings_raw: 7+1=8, leaderboards_raw: 18+1=19, profiles_raw: 13+1=14). NULL count for won. Investigate 2073/2072 file gap (identify which date(s) have matches but no ratings, or vice versa)."
stratification: "By subdirectory (matches, ratings, leaderboards, profiles)."
predecessors:
  - "01_01_01"
  - "01_01_02"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/01_eda/01_02_01_duckdb_ingestion.py"
inputs:
  duckdb_tables:
    - "matches_raw"
    - "ratings_raw"
    - "leaderboards_raw"
    - "profiles_raw"
  prior_artifacts:
    - "artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"
    - "artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - "DuckDB 1.5.1 (pinned in pyproject.toml)"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/01_eda/01_02_01_duckdb_ingestion.json"
  report: "artifacts/01_exploration/01_eda/01_02_01_duckdb_ingestion.md"
reproducibility: "DuckDB SQL in the notebook. Parquet logical type inspection via pyarrow.parquet.ParquetFile.schema on sample files to determine binary column annotation status. Row counts verified against 01_01_01 file counts. Smoke test and pre-ingestion functions in pre_ingestion.py. All code and output paired per Invariant #6. DuckDB version 1.5.1 noted."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "DDL, ingestion SQL, DESCRIBE output, and row counts in the notebook."
  - number: "7"
    how_upheld: "binary_as_string=true justified by in-notebook pyarrow logical type inspection. File counts from 01_01_01 used as verification baseline."
  - number: "9"
    how_upheld: "Conclusions limited to: tables created, types assigned, row counts, file-count reconciliation. Binary column justification cites Parquet metadata (structural), not content."
gate:
  artifact_check: "artifacts/01_exploration/01_eda/01_02_01_duckdb_ingestion.json and .md exist and are non-empty."
  continue_predicate: "DuckDB tables (matches_raw, ratings_raw, leaderboards_raw, profiles_raw) exist with non-zero row counts AND full DESCRIBE output recorded for all 4 tables AND ratings_raw DESCRIBE shows profile_id as INTEGER/BIGINT, date as DATE/TIMESTAMP, and games/rating/rating_diff as INTEGER (not VARCHAR) AND smoke test passed before full ingestion."
  halt_predicate: "DuckDB cannot read any Parquet or CSV files, OR smoke test shows binary columns as BLOB (not VARCHAR), OR ratings_raw type gate fails after re-ingestion attempt."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

---

## Phase 02 — Feature Engineering (placeholder)

Pipeline Sections: see `docs/PHASES.md`.
Steps to be defined when Phase 01 gate is met.

---

## Phase 03 — Splitting & Baselines (placeholder)

Pipeline Sections: see `docs/PHASES.md`.
Steps to be defined when Phase 02 gate is met.

---

## Phase 04 — Model Training (placeholder)

Pipeline Sections: see `docs/PHASES.md`.
Steps to be defined when Phase 03 gate is met.

---

## Phase 05 — Evaluation & Analysis (placeholder)

Pipeline Sections: see `docs/PHASES.md`.
Steps to be defined when Phase 04 gate is met.

---

## Phase 06 — Cross-Domain Transfer (placeholder)

Pipeline Sections: see `docs/PHASES.md`.
Steps to be defined when Phase 05 gate is met.

---

## Phase 07 — Thesis Writing Wrap-up (gate marker)

Per `docs/PHASES.md`, Phase 07 is a gate marker with no Pipeline Sections.
This dataset's Phase 07 gate is met when all thesis sections fed by this
dataset have reached FINAL status in `thesis/WRITING_STATUS.md`.
