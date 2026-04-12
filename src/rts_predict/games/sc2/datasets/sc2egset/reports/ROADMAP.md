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
description: "Walk the sc2egset raw directory, count files, measure sizes, group by subdirectory."
phase: "01 — Data Exploration"
pipeline_section: "01_01 — Data Acquisition & Source Inventory"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 1"
dataset: "sc2egset"
question: "What files exist on disk, how many are there, and how are they organized?"
method: "Call inventory_directory() on the raw directory and on each tournament's _data/ subdirectory. The sc2egset layout is two-level: raw/TOURNAMENT/TOURNAMENT_data/*.SC2Replay.json. Report tournament-level metadata counts, per-_data/ replay counts, total replay files, total size, and summary statistics (min/max/median replays per tournament). Flag tournaments with missing _data/ dirs."
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
  - "Chapter 4 — Data and Methodology > 4.1.1 SC2EGSet (StarCraft II)"
research_log_entry: "Required on completion."
```

### Step 01_01_02 — Schema Discovery

```yaml
step_number: "01_01_02"
name: "Schema Discovery"
description: "Sample sc2egset JSON files across all 70 directories. Discover root-level keys, nested keypaths, data types, and schema consistency across eras."
phase: "01 — Data Exploration"
pipeline_section: "01_01 — Data Acquisition & Source Inventory"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 1"
dataset: "sc2egset"
question: "What is the internal structure of the SC2EGSet JSON files, and is this structure consistent across all 70 directories?"
method: "Select 1 file from each of the 70 _data/ subdirectories (first alphabetically) for root-level schema via discover_json_schema(). Select 3 files from each directory for full keypath enumeration via get_json_keypaths(). Compare schemas across directories to detect era-dependent variation. Report root-level key catalog, full keypath tree, observed types, and consistency verdict. No DuckDB type proposals (deferred to ingestion design)."
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
reproducibility: "All schema profiles produced by discover_json_schema() and get_json_keypaths() from rts_predict.common.json_utils. File selection is deterministic (first N alphabetically per directory). Code and output in the paired notebook per Invariant #6."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "Schema profiles produced by code in the notebook, saved alongside the report."
  - number: "7"
    how_upheld: "Sample size (1 per directory for root schema, 3 for keypaths) justified by temporal stratification in the report."
  - number: "9"
    how_upheld: "Conclusions limited to structural observations. No row counts, value distributions, or semantic interpretation."
gate:
  artifact_check: "artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json and .md exist and are non-empty."
  continue_predicate: "Schema artifacts exist and report a consistency verdict for all 70 directories."
  halt_predicate: "More than 30% of sampled files fail to parse."
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
