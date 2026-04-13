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
description: "Establish a complete filesystem-level census of the aoestats raw data. This grounds all subsequent steps in verified file counts, sizes, date ranges, and directory structure — including alignment between paired directories (matches vs players)."
phase: "01 — Data Exploration"
pipeline_section: "01_01 — Data Acquisition & Source Inventory"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 1"
dataset: "aoestats"
question: "How many files exist in each subdirectory, what weekly date range do they span, and are the matches and players file series temporally aligned?"
method: "Full census of the raw directory tree. Count files, measure sizes, group by subdirectory. Extract weekly dates from filenames and compare paired directories for count and date-range alignment."
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
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "Inventory counts produced by code in the notebook, saved alongside the report."
  - number: "7"
    how_upheld: "Full census — no sampling or thresholds."
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
description: "Map the column-level structure of all three aoestats file types (Parquet matches, Parquet players, JSON overview). Determine whether schemas are consistent across the weekly temporal range and whether matches and players share structurally overlapping columns."
phase: "01 — Data Exploration"
pipeline_section: "01_01 — Data Acquisition & Source Inventory"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 1"
dataset: "aoestats"
question: "What columns exist in each file type, what are their data types, does the schema remain stable across the weekly temporal range, and do matches and players share overlapping column names?"
method: "Full census of Parquet file metadata for matches (172 files) and players (171 files). Read overview.json structure. Compare schemas within each subdirectory for consistency and cross-compare matches/players for structural overlap. Report column catalogs, types, and consistency verdicts. No DuckDB type proposals — deferred to ingestion design."
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
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "Schema profiles produced by code in the notebook, saved alongside the report."
  - number: "7"
    how_upheld: "Full census — no sampling or thresholds."
  - number: "9"
    how_upheld: "Conclusions limited to column-level structural observations — no value distributions or DuckDB type proposals."
gate:
  artifact_check: "artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json and .md exist and are non-empty."
  continue_predicate: "Schema artifacts exist and report a consistency verdict for all subdirectories."
  halt_predicate: "Any Parquet file fails to open."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_02_01 — DuckDB Pre-Ingestion

```yaml
step_number: "01_02_01"
name: "DuckDB Pre-Ingestion"
description: "Determine how aoestats's variant-typed columns (7 columns whose Parquet type differs across weekly files) behave under DuckDB type promotion, and whether NULL patterns in the ingested tables match the file-level column presence/absence census."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "aoestats"
question: "What does the raw data look like before we commit to an ingestion strategy — are there type promotion traps for variant columns, interval-type handling issues, or NULL patterns that need handling?"
method: "Full census of Parquet metadata across all weekly files to establish per-column type distributions for the 7 variant columns. Smoke-test temporally-stratified file samples into in-memory DuckDB. DESCRIBE schemas, verify type promotions and interval handling, and cross-check NULL counts against file-level column presence. Investigate the matches/players file-count asymmetry (172 vs 171). Produce a design artifact for the full-ingestion step."
stratification: "By subdirectory (matches, players, overview)."
predecessors:
  - "01_01_01"
  - "01_01_02"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py"
inputs:
  duckdb_tables:
    - "none — investigation uses temporary in-memory DB"
  prior_artifacts:
    - "artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json"
    - "artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - "DuckDB 1.5.1 (pinned in pyproject.toml)"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json"
  report: "artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "All census code, smoke-test SQL, DESCRIBE output, and NULL counts in the notebook."
  - number: "7"
    how_upheld: "Variant column type distributions from full Parquet metadata census."
  - number: "9"
    how_upheld: "Conclusions limited to type mappings, NULL patterns, and file-count reconciliation — no content profiling."
gate:
  artifact_check: "artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json and .md exist and are non-empty."
  continue_predicate: "Design artifact documents DuckDB types for all 3 table types AND variant columns have expected promoted types AND NULL patterns match file-level census AND smoke test passed."
  halt_predicate: "DuckDB cannot read Parquet files with union_by_name, OR smoke test reveals unresolvable type conflicts."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_02_02 — DuckDB Ingestion

```yaml
step_number: "01_02_02"
name: "DuckDB Ingestion"
description: "Materialise raw aoestats data into persistent DuckDB tables: matches_raw (172 weekly Parquet with union_by_name), players_raw (171 weekly Parquet with union_by_name), overviews_raw (singleton overview.json). All tables carry filename provenance. filename column stores path relative to raw_dir (no absolute paths)."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "aoestats"
question: "Can we materialise all three raw tables with correct type promotions for variant columns and provenance?"
method: "Call ingestion module functions against the persistent DuckDB. Validate with DESCRIBE, row counts, NULL rates on key fields. Verify filename column exists in all tables and variant columns have expected promoted types."
stratification: "By table (matches_raw, players_raw, overviews_raw)."
predecessors:
  - "01_02_01"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/02_eda/01_02_02_duckdb_ingestion.py"
inputs:
  duckdb_tables:
    - "none — creates tables"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - "DuckDB 1.5.1 (pinned in pyproject.toml)"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.json"
  report: "artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "All ingestion SQL in the module, validation SQL in the notebook."
  - number: "7"
    how_upheld: "All tables carry filename provenance column."
  - number: "9"
    how_upheld: "Conclusions limited to ingestion success, row counts, column types, and NULL rates."
  - number: "10"
    how_upheld: "filename column in all tables stores path relative to raw_dir; no absolute paths."
gate:
  artifact_check: "artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.json and .md exist and are non-empty."
  continue_predicate: "All three DuckDB tables created with expected row counts. All tables have filename column. filename values are relative paths (no leading /)."
  halt_predicate: "Any table creation fails OR row count is zero."
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
