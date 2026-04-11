# aoe2companion Dataset Roadmap

**Game:** AoE2
**Dataset:** aoe2companion
**Canonical phase list:** `docs/PHASES.md`
**Methodology manuals:** `docs/INDEX.md`
**Step definition schema:** `docs/templates/step_template.yaml`

---

> **Role: PRIMARY.** This is the primary AoE2 dataset. It runs full
> Phases 01–07. See `src/rts_predict/aoe2/reports/ROADMAP.md` for the
> dataset strategy rationale.

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

**aoe2companion API** — community match history and rating dataset.
~277M matches, ~58M ratings, ~2.4M leaderboard entries, ~3.6M profiles across
4,147 files totalling ~9.3 GB. Downloaded 2026-04-06.

**Raw data is immutable. The API download will not be repeated.**
Acquisition provenance is recorded in
`src/rts_predict/aoe2/reports/aoe2companion/README.md`.

**4 raw tables:**

| Table | Rows | Nature |
|-------|------|--------|
| raw_matches | 277,099,059 | append-ordered historical records |
| raw_ratings | 58,317,433 | append-ordered historical records |
| raw_leaderboard | 2,381,227 | point-in-time snapshot (T_snapshot = 2026-04-06T21:08:57Z) |
| raw_profiles | 3,609,686 | point-in-time snapshot (T_snapshot = 2026-04-06T21:09:07Z) |

**WARNING — snapshot tables:** `raw_leaderboard` and `raw_profiles` MUST NOT be
joined to historical matches as if they were time-varying. They reflect state at
`T_snapshot` only and must be treated as static reference lookups.

**Sparse rating regime:** The rating history data is sparse before 2025-06-26.
Files dated 2020-08-01 through 2025-06-26 account for 1,791 of the 2,072 rating
files and contain fewer than 1,024 bytes each. Analyses that depend on rating
completeness must segment at this boundary date.

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
