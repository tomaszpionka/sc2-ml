# aoestats Dataset Roadmap

**Game:** AoE2
**Dataset:** aoestats
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

This file decomposes Phases into Pipeline Sections and Steps for the aoestats
dataset. The canonical Phase definitions and Pipeline Section enumerations live
in `docs/PHASES.md`. This ROADMAP does not invent Phases or Pipeline Sections;
it only decomposes them into Steps.

Steps are defined in a planning session before Phase work begins.

Steps are numbered `XX_YY_ZZ` where `XX` = Phase, `YY` = Pipeline Section,
`ZZ` = Step within that Pipeline Section.

---

## Source data

**aoestats.io weekly DB dumps** — community match and player statistics dataset.
Downloaded 2026-04-06. File counts and date ranges are from
Step 01_01_01 (file inventory).

| Subdirectory | Files (.parquet / .json) | Size (MB) |
|---|---|---|
| `matches/` | 172 | 610.55 |
| `players/` | 171 | 3162.86 |
| `overview/` | 1 | 0.02 |

**Total:** 344 data files (excluding 3 `.gitkeep` dotfiles and 2 root files),
3773.61 MB. Filename-derived date range: 2022-08-28 to 2026-02-07.

**Raw data is immutable. The weekly dump download will not be repeated.**
Acquisition provenance is recorded in
`src/rts_predict/games/aoe2/datasets/aoestats/reports/README.md`.

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
description: "Walk the aoestats raw directory, count files, measure sizes, group by subdirectory."
phase: "01 — Data Exploration"
pipeline_section: "01_01 — Data Acquisition & Source Inventory"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 1"
dataset: "aoestats"
question: "What files exist on disk, how many are there, and how are they organized?"
method: "Call inventory_directory() on the raw directory. Report totals, per-subdirectory breakdown, extension distribution. Extract weekly date ranges from filenames using regex. Compare paired directories (matches vs players) for count and date-range alignment."
stratification: "By subdirectory (matches, players, overview)."
predecessors: "none — independent"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py"
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
description: "Read Parquet metadata from aoestats matches and players files. Read overview.json structure. Check schema consistency across the temporal range and compare matches/players schemas for structural overlap."
phase: "01 — Data Exploration"
pipeline_section: "01_01 — Data Acquisition & Source Inventory"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 1"
dataset: "aoestats"
question: "What columns exist in each file type, what are their data types, is the schema consistent across the temporal range, and do matches and players share structurally overlapping columns?"
method: "Full census: pyarrow.parquet.read_schema() on all 172 matches + 171 players files (metadata-only). discover_json_schema() on overview.json (1 file). Compare schemas within each subdirectory for consistency. Cross-compare matches and players column names for structural overlap (raw string comparison). Report column catalogs, Arrow types, consistency verdicts, and column name overlap. No DuckDB type proposals."
stratification: "By subdirectory. Full census within each."
predecessors:
  - "01_01_01"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_02_schema_discovery.py"
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
reproducibility: "Parquet schemas via pyarrow.parquet.read_schema() (full census on all files). JSON schema via discover_json_schema() (census, 1 file). Code and output in the paired notebook per Invariant #6."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "Schema profiles produced by code in the notebook, saved alongside the report."
  - number: "7"
    how_upheld: "Full census for Parquet (metadata-only, zero cost) and JSON (1 file). Census eliminates sample-size justification requirement."
  - number: "9"
    how_upheld: "Conclusions limited to column-level structural observations. Cross-subdirectory comparison is structural (column name overlap as raw string comparison), not content-level. No DuckDB type proposals."
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
description: "Load aoestats Parquet files into DuckDB with union_by_name=true. Pre-ingestion variant column census determines the actual type distribution of the 7 variant columns identified by 01_01_02 across all source files. Smoke test confirms DuckDB auto-promotion handles each variant pattern correctly. Load overview.json as reference table. Document missing-week asymmetry (171 vs 172 files)."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "aoestats"
question: "What are the actual type distributions of the 7 variant columns across all source files, can DuckDB union_by_name handle them correctly via auto-promotion (preserving native types rather than forcing VARCHAR), and do post-ingestion NULL patterns for presence/absence columns match the file-level census?"
method: "PRE-INGESTION VARIANT CENSUS: Run pyarrow.parquet.read_schema on ALL 172 matches + 171 players files. For each of the 7 variant columns identified by 01_01_02, record the type distribution across files (e.g., how many files have int64 vs double for a given column, how many have null-typed columns). This census is the authoritative source for variant column patterns — its results determine the ingestion strategy and provide the baseline for post-ingestion NULL verification. Smoke test and pre-ingestion functions live in pre_ingestion.py. SMOKE TEST: ingest 3-5 files from each subdirectory (earliest, middle, latest) into temp tables with union_by_name=true and filename=true. Verify DESCRIBE: variant columns have correct promoted types (not VARCHAR), duration/irl_duration are INTERVAL, column counts correct (matches_raw: 17+1 filename=18, players_raw: 13+1=14). FULL INGESTION: CREATE TABLE matches_raw AS ...; CREATE TABLE players_raw AS ...; CREATE TABLE overviews_raw AS SELECT * FROM read_json_auto('raw/overview/overview.json', filename=true) — produces table with filename provenance column. POST-INGESTION: DESCRIBE ALL 3 tables. Verify duration/irl_duration → INTERVAL, test EXTRACT(EPOCH FROM duration) for reasonable values. For each variant column: SELECT COUNT(*) FILTER (WHERE col IS NULL) — NULL counts must correspond to file-level absence pattern from census. Note on profile_id: if promoted to DOUBLE from mixed int64/double sources, player IDs as float64 may cause join precision issues for IDs > 2^53; flag for EDA investigation, do not alter at bronze layer. Investigate missing-week asymmetry (171 players vs 172 matches files)."
stratification: "By subdirectory (matches, players, overview)."
predecessors:
  - "01_01_01"
  - "01_01_02"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/01_eda/01_02_01_duckdb_ingestion.py"
inputs:
  duckdb_tables:
    - "matches_raw"
    - "players_raw"
    - "overviews_raw"
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
reproducibility: "Pre-ingestion pyarrow census code and DuckDB SQL in the notebook. Variant column type distributions established by full pyarrow census in the notebook. NULL counts verified against file-level absence pattern from same census. All code and output paired per Invariant #6. DuckDB version 1.5.1 noted."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "DDL, ingestion SQL, census code, DESCRIBE output, and NULL counts in the notebook."
  - number: "7"
    how_upheld: "No type-forcing thresholds — DuckDB auto-promotion is deterministic. Variant column type distributions from full pyarrow census (not sampled)."
  - number: "9"
    how_upheld: "Conclusions limited to: tables created, types assigned (including auto-promotion results), row counts, NULL patterns matching file-level census. profile_id precision flag is structural, not semantic."
gate:
  artifact_check: "artifacts/01_exploration/01_eda/01_02_01_duckdb_ingestion.json and .md exist and are non-empty."
  continue_predicate: "DuckDB tables exist with non-zero row counts AND full DESCRIBE output recorded for all 3 tables AND variant columns have expected promoted types (raw_match_type: DOUBLE, started_timestamp: TIMESTAMP, profile_id: DOUBLE, opening: VARCHAR, age uptimes: DOUBLE) AND duration/irl_duration are INTERVAL AND NULL counts for presence/absence columns match file census AND smoke test passed."
  halt_predicate: "DuckDB cannot read Parquet files with union_by_name, OR smoke test shows unexpected types (e.g., variant column auto-widened to VARCHAR when numeric promotion was expected), OR overviews_raw fails to parse from overview.json."
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
