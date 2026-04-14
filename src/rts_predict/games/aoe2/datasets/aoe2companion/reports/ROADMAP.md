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
description: "Establish a complete filesystem-level census of the aoe2companion raw data. This grounds all subsequent steps in verified file counts, sizes, date ranges, and directory structure."
phase: "01 — Data Exploration"
pipeline_section: "01_01 — Data Acquisition & Source Inventory"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 1"
dataset: "aoe2companion"
question: "How many files exist in each subdirectory, what date range do they span, and are there any temporal gaps between the matched file series (matches vs ratings)?"
method: "Full census of the raw directory tree. Count files, measure sizes, group by subdirectory. Extract dates from filenames to establish the temporal range and identify gaps."
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
description: "Map the column-level structure of all four aoe2companion file types (Parquet matches, CSV ratings, singleton leaderboards and profiles). Determine whether schemas are consistent across the full temporal range."
phase: "01 — Data Exploration"
pipeline_section: "01_01 — Data Acquisition & Source Inventory"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 1"
dataset: "aoe2companion"
question: "What columns exist in each file type, what are their data types, and does the schema remain stable across the temporal range or evolve over time?"
method: "Full census of Parquet file metadata for matches (2,073 files) and CSV headers for ratings (2,072 files). Read singleton leaderboard and profile schemas. Compare within each subdirectory for consistency and report column catalogs, types, and consistency verdicts. No DuckDB type proposals — deferred to ingestion design."
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
description: "Determine whether aoe2companion's four file types (Parquet matches, CSV ratings, singleton leaderboards and profiles) can be loaded into DuckDB with correct type mappings, and surface any traps (binary column encoding, CSV type inference, file-count asymmetry) before committing to full ingestion."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "aoe2companion"
question: "What does the raw data look like before we commit to an ingestion strategy — are there type inference traps, binary column encoding issues, or NULL patterns that need handling?"
method: "Inspect Parquet binary column annotations to determine encoding strategy. Smoke-test temporally-stratified file samples into in-memory DuckDB. DESCRIBE schemas, preview rows, and assess NULL counts. Investigate the matches/ratings file-count asymmetry (2073 vs 2072). Produce a design artifact for the full-ingestion step."
stratification: "By subdirectory (matches, ratings, leaderboards, profiles)."
predecessors:
  - "01_01_01"
  - "01_01_02"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py"
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
    how_upheld: "All smoke-test SQL, type inspection, and DESCRIBE output in the notebook."
  - number: "7"
    how_upheld: "Binary column encoding strategy justified by in-notebook Parquet metadata inspection."
  - number: "9"
    how_upheld: "Conclusions limited to type mappings, row counts, and file-count reconciliation — no content profiling."
gate:
  artifact_check: "artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json and .md exist and are non-empty."
  continue_predicate: "Design artifact documents DuckDB types for all 4 table types AND smoke test passed AND type inference traps identified and mitigation proposed."
  halt_predicate: "DuckDB cannot read any Parquet or CSV files, OR smoke test reveals unresolvable type conflicts."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_02_02 — DuckDB Ingestion

```yaml
step_number: "01_02_02"
name: "DuckDB Ingestion"
description: "Materialise raw aoe2companion data into persistent DuckDB tables: matches_raw (2,073 daily Parquet), ratings_raw (2,072 daily CSV with dtype decision from 01_02_01), leaderboard_raw (singleton Parquet), profiles_raw (singleton Parquet). All tables carry filename provenance. filename column stores path relative to raw_dir (no absolute paths)."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "aoe2companion"
question: "Can we materialise all four raw tables with correct types and provenance, applying the dtype decision from 01_02_01?"
method: "Call ingestion module functions against the persistent DuckDB. Validate with DESCRIBE, row counts, NULL rates on key fields. Verify filename column exists in all tables."
stratification: "By table (matches_raw, ratings_raw, leaderboard_raw, profiles_raw)."
predecessors:
  - "01_02_01"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_02_duckdb_ingestion.py"
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
  continue_predicate: "All four DuckDB tables created with expected row counts. All tables have filename column. filename values are relative paths (no leading /)."
  halt_predicate: "Any table creation fails OR row count is zero."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

### Step 01_02_03 — Raw Schema DESCRIBE

```yaml
step_number: "01_02_03"
name: "Raw Schema DESCRIBE"
description: "Establish the definitive column-name and column-type snapshot for every aoe2companion raw source. Uses in-memory DuckDB with the same read parameters planned for 01_02_02 (binary_as_string=true, union_by_name=true, filename=true for Parquet; explicit dtypes for CSV) and LIMIT 0 to avoid loading any row data. Output feeds the data/db/schemas/raw/*.yaml source-of-truth files consumed by all downstream steps. When 01_02_02 has been executed, this step can instead connect read-only to the persistent DuckDB."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "aoe2companion"
question: "What are the exact column names and DuckDB types for each aoe2companion raw source — matches, ratings, leaderboards, profiles — as they will appear after ingestion?"
method: "Connect to in-memory DuckDB. DESCRIBE SELECT * FROM read_parquet/read_csv(...) LIMIT 0 for each of the four sources using the same read options as 01_02_02. Write JSON artifact. Populate data/db/schemas/raw/*.yaml schema files."
stratification: "By source (matches, ratings, leaderboards, profiles)."
predecessors:
  - "01_02_01"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_03_raw_schema_describe.py"
inputs:
  duckdb_tables: "none — in-memory DuckDB, reads files directly with LIMIT 0"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - "DuckDB 1.5.1 (pinned in pyproject.toml)"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_03_raw_schema_describe.json"
  schema_files:
    - "data/db/schemas/raw/matches_raw.yaml"
    - "data/db/schemas/raw/ratings_raw.yaml"
    - "data/db/schemas/raw/leaderboards_raw.yaml"
    - "data/db/schemas/raw/profiles_raw.yaml"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "All DESCRIBE SQL embedded in notebook; JSON artifact records exact schema seen."
  - number: "7"
    how_upheld: "Column types and nullability taken from DESCRIBE output, not assumed."
  - number: "9"
    how_upheld: "Read-only step — no DuckDB tables created, no files modified."
  - number: "10"
    how_upheld: "filename column confirmed present across all four sources."
gate:
  artifact_check: "artifacts/01_exploration/02_eda/01_02_03_raw_schema_describe.json exists and non-empty. data/db/schemas/raw/*.yaml files populated for all four tables."
  continue_predicate: "Column counts confirmed: matches=55, ratings=8, leaderboards=19, profiles=14."
  halt_predicate: "Any source cannot be read or DESCRIBE returns zero columns."
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
