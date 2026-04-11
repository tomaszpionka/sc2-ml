# aoestats Dataset Roadmap

**Game:** AoE2
**Dataset:** aoestats
**Canonical phase list:** `docs/PHASES.md`
**Methodology manuals:** `docs/INDEX.md`
**Step definition schema:** `docs/templates/step_template.yaml`

---

> **Role: SUPPLEMENTARY VALIDATION.** This dataset runs full Phase 01,
> then a lightweight Phase 02–05 replication pass. It does not run
> Phase 06. See `src/rts_predict/aoe2/reports/ROADMAP.md` for the
> dataset strategy rationale.

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

**aoestats.io weekly dumps** — community match and player statistics dataset.
~30.7M matches, ~107.6M players across 343 files on disk (172 match parquets +
171 player parquets). Downloaded 2026-04-06.

**Raw data is immutable. The weekly dump download will not be repeated.**
Acquisition provenance is recorded in
`src/rts_predict/aoe2/reports/aoestats/README.md`.

**2 raw tables:**

| Table | Rows | Files |
|-------|------|-------|
| raw_matches | 30,690,651 | 172 |
| raw_players | 107,627,584 | 171 |

**WARNING — known data gap:** `2025-11-16_2025-11-22_players.parquet` is missing
from disk. This is a documented download failure recorded in the manifest with
`status='failed'`. It is not silent corruption. The raw_players table therefore
contains 171 files instead of 172. All Steps that depend on raw_players MUST
acknowledge this gap.

**WARNING — schema drift:** Type drift was resolved by DuckDB
`union_by_name = true` (widest compatible type wins). Known drifted columns:

- `raw_matches.raw_match_type`: DOUBLE → BIGINT
- `raw_players.feudal_age_uptime`: DOUBLE → INTEGER
- `raw_players.castle_age_uptime`: DOUBLE → INTEGER
- `raw_players.imperial_age_uptime`: DOUBLE → INTEGER
- `raw_players.profile_id`: DOUBLE → BIGINT
- `raw_players.opening`: VARCHAR → INTEGER

Profiling steps must verify that resolved types match the canonical types above.

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
