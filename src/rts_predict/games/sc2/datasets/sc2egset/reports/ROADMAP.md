# SC2EGSet Dataset Roadmap

**Game:** SC2
**Dataset:** sc2egset
**Canonical phase list:** `docs/PHASES.md`
**Methodology manuals:** `docs/INDEX.md`
**Step definition schema:** `docs/templates/step_template.yaml`
**Research log:** `research_log.md` (sibling file — per-dataset reverse-chronological narrative)

---

## How to use this document

This file decomposes Phases into Pipeline Sections and Steps for the sc2egset
dataset. The canonical Phase definitions and Pipeline Section enumerations live
in `docs/PHASES.md`. This ROADMAP does not invent Phases or Pipeline Sections;
it only decomposes them into Steps.

Steps are defined in a planning session before Phase work begins.

Steps are numbered `XX_YY_ZZ` where `XX` = Phase, `YY` = Pipeline Section,
`ZZ` = Step within that Pipeline Section.

---

## Source data

**SC2EGSet: StarCraft II Esport Replay and Game-state Dataset** — Zenodo v2.1.0.

Raw directory layout: `raw/TOURNAMENT/TOURNAMENT_data/*.SC2Replay.json`
(two-level: 70 tournament directories, each containing a `_data/` subdirectory
with `.SC2Replay.json` files and a `map_foreign_to_english_mapping.json` metadata
file at the tournament level).

File counts from 01_01_01 artifact:
- `.SC2Replay.json` files: 22,390
- Metadata files (`.zip`, `.log`, `.json` at tournament level): 431
- Files at root level: 3
- Total files scanned: 22,821
- Total `.SC2Replay.json` size: 214,060.62 MB

Directory name prefix range: `2016_` through `2024_` (70 directories).

Source: Białecki, A. et al. (2023). *SC2EGSet: StarCraft II Esport Replay
and Game-state Dataset.* Scientific Data 10(1), 600.
https://doi.org/10.1038/s41597-023-02510-7 — version 2.1.0 from Zenodo:
https://zenodo.org/records/17829625

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
description: "Establish a complete filesystem-level census of the sc2egset raw data. This grounds all subsequent steps in verified file counts, sizes, and directory structure."
phase: "01 — Data Exploration"
pipeline_section: "01_01 — Data Acquisition & Source Inventory"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 1"
dataset: "sc2egset"
question: "How many replay files exist, how large are they, and how are they distributed across the two-level tournament directory structure?"
method: "Full census of the raw directory tree. Count files, measure sizes, and group by tournament subdirectory. Report summary statistics (min/max/median replays per tournament) and flag structural anomalies (e.g., missing subdirectories)."
stratification: "By tournament directory (each tournament has its own _data/ subdir)."
predecessors: "none — independent"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.py"
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
  - "Chapter 4 — Data and Methodology > 4.1.1 SC2EGSet (StarCraft II)"
research_log_entry: "Required on completion."
```

### Step 01_01_02 — Schema Discovery

```yaml
step_number: "01_01_02"
name: "Schema Discovery"
description: "Map the internal structure of sc2egset JSON replay files — root-level keys, nested keypaths, data types — and determine whether the schema is consistent across all 70 tournament directories (spanning 2016-2024)."
phase: "01 — Data Exploration"
pipeline_section: "01_01 — Data Acquisition & Source Inventory"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 1"
dataset: "sc2egset"
question: "What is the internal structure of the replay JSON files, and does it remain stable across tournament eras or evolve over time?"
method: "Sample files from each of the 70 directories (deterministic selection, stratified by tournament). Enumerate root-level keys and full keypath trees. Compare schemas across directories to detect era-dependent variation and report a consistency verdict. No DuckDB type proposals — deferred to ingestion design."
stratification: "By directory (all 70 represented; temporal range 2016-2024)."
predecessors:
  - "01_01_01"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_02_schema_discovery.py"
inputs:
  duckdb_tables: "none — reads raw JSON files directly"
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
    how_upheld: "Sample size per directory justified by temporal stratification in the report."
  - number: "9"
    how_upheld: "Conclusions limited to structural observations — no value distributions or semantic interpretation."
gate:
  artifact_check: "artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json and .md exist and are non-empty."
  continue_predicate: "Schema artifacts exist and report a consistency verdict for all 70 directories."
  halt_predicate: "More than 30% of sampled files fail to parse."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.1 SC2EGSet (StarCraft II)"
research_log_entry: "Required on completion."
```

### Step 01_02_01 — DuckDB Pre-Ingestion Investigation

```yaml
step_number: "01_02_01"
name: "DuckDB Pre-Ingestion Investigation"
description: "Determine how sc2egset's deeply nested JSON (11 root keys, dynamic-key maps, 3 large event arrays) behaves when loaded into DuckDB, and decide on a table split strategy before committing to full ingestion."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "sc2egset"
question: "What does the raw data look like before we commit to an ingestion strategy — are there type inference traps, storage feasibility concerns for event arrays, or structural irregularities in the mapping files that need handling?"
method: "Smoke-test size-stratified file samples into in-memory DuckDB. DESCRIBE schemas, preview rows, and assess event array storage cost (extrapolated to full corpus). Test single-table vs split-table approaches on a mid-size tournament directory. Census all 70 tournament-level mapping files for schema consistency. Produce a design artifact with proposed DDL for a future full-ingestion step."
stratification: "By root key group (metadata vs events vs player desc map); by tournament directory for map alias files."
predecessors:
  - "01_01_01"
  - "01_01_02"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py"
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
    how_upheld: "All smoke-test SQL, storage measurements, and census code in the notebook."
  - number: "7"
    how_upheld: "File sample selection derived from 01_01_01 per-directory size data."
  - number: "9"
    how_upheld: "Conclusions limited to type mappings, storage estimates, and structural consistency — no content profiling."
gate:
  artifact_check: "artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json and .md exist and are non-empty."
  continue_predicate: "Design artifact documents: (1) read_json_auto behavior for all 11 root keys with DuckDB types, (2) proposed table split strategy with rationale, (3) event array storage estimate with SSD feasibility verdict, (4) full census of all 70 map_foreign_to_english_mapping.json files with cross-file consistency assessment and proposed DDL."
  halt_predicate: "read_json_auto cannot parse any sample file, OR batch ingestion of a single directory fails."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.1 SC2EGSet (StarCraft II)"
research_log_entry: "Required on completion."
```

### Step 01_02_02 — DuckDB Ingestion

```yaml
step_number: "01_02_02"
name: "DuckDB Ingestion"
description: "Materialise raw sc2egset data into persistent DuckDB tables using the three-stream strategy determined by 01_02_01. Stream 1 (replays_meta): one row per replay with metadata STRUCT columns and ToonPlayerDescMap as VARCHAR. Stream 2 (replay_players): normalised from ToonPlayerDescMap, one row per (replay, player). Stream 3 (events): optional Parquet extraction for gameEvents, trackerEvents, messageEvents. Also: map_aliases table from all 70 tournament mapping files."
phase: "01 — Data Exploration"
pipeline_section: "01_02 — Exploratory Data Analysis (Tukey-style)"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 2"
dataset: "sc2egset"
question: "Can we materialise the three-stream ingestion strategy into persistent tables and verify row counts, column types, and NULL rates?"
method: "Call ingestion module functions against the persistent DuckDB. Validate with DESCRIBE, row counts, NULL rates on key fields. Verify ToonPlayerDescMap is VARCHAR, event arrays are excluded from replays_meta, and map_aliases has tournament provenance."
stratification: "By table (replays_meta, replay_players, map_aliases)."
predecessors:
  - "01_02_01"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.py"
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
gate:
  artifact_check: "artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.json and .md exist and are non-empty."
  continue_predicate: "All three DuckDB tables created with expected row counts. ToonPlayerDescMap is VARCHAR. All tables have filename column."
  halt_predicate: "Any table creation fails OR row count is zero."
thesis_mapping:
  - "Chapter 4 — Data and Methodology > 4.1.1 SC2EGSet (StarCraft II)"
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
