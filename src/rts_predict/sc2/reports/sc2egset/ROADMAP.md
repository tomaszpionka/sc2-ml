# SC2EGSet Dataset Roadmap

**Game:** SC2
**Dataset:** sc2egset
**Canonical phase list:** `docs/PHASES.md`
**Methodology manuals:** `docs/INDEX.md`
**Step definition schema:** `docs/templates/step_template.yaml`

---

## How to use this document

This file decomposes Phases into Pipeline Sections and Steps for the sc2egset
dataset. The canonical Phase definitions and Pipeline Section enumerations live
in `docs/PHASES.md`. This ROADMAP does not invent Phases or Pipeline Sections;
it only decomposes them into Steps.

Only the currently-active Phase has fully defined Steps. Future Phases are
listed as placeholders with their Pipeline Section outline from `docs/PHASES.md`.
Steps are defined when the preceding Phase completes its gate.

Steps are numbered `XX_YY_ZZ` where `XX` = Phase, `YY` = Pipeline Section,
`ZZ` = Step within that Pipeline Section.

---

## Source data

**SC2EGSet v2.1.0** — StarCraft II Esport Replay and Game-state Dataset.
~22,000 competitive 1v1 replays from 70+ tournaments covering 2016–2024.

Citation: Białecki, A. et al. (2023). *SC2EGSet: StarCraft II Esport Replay
and Game-state Dataset.* Scientific Data 10(1), 600.
https://doi.org/10.1038/s41597-023-02510-7 — version 2.1.0 from Zenodo:
https://zenodo.org/records/17829625

**Game loop timing:** The SC2 engine runs at 16 game loops per game-second
(Normal speed). All competitive play uses Faster speed (1.4× multiplier),
giving **22.4 game loops = 1 real-time second**. Use `game_loops / 22.4 / 60`
for real-time minutes. The older formula `game_loops / 16.0 / 60` produces
game-minutes (internal engine time) — both are valid but must be clearly
labelled. All artifacts in this ROADMAP use real-time minutes unless
explicitly noted.

---

## Phase 01 — Data Exploration

### 01_01 — Data Acquisition & Source Inventory

| Step | Description | Notebook | Artifacts | Gate condition |
|------|-------------|----------|-----------|----------------|
| 01_01_01 | Raw JSON audit and DuckDB ingestion. Audit `raw/` tournament subdirs; sample one JSON file per tournament via `json_utils.py` to explore top-level keys; ingest root-level scalar keys into the `raw` DuckDB table and save nested keys (`header`, `initData`, `details`, `metadata`, `ToonPlayerDescMap`) as JSON columns. Calls `ingestion.move_data_to_duck_db()` and `ingestion.ingest_map_alias_files()`. Validates row count, schema, `tournament_dir` extraction, and `replay_id` (MD5 hash prefix). | `sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_raw_json_ingestion.py` | `01_01_01_source_audit.json`, `01_01_01_source_audit.md` | `raw` table exists; row count matches file count on disk; `tournament_dir` and `replay_id` extractable from all rows; zero stripped source files |
| 01_01_02 | In-game event extraction to Parquet and DuckDB. Calls `ingestion.run_in_game_extraction()` to extract tracker events and game events from raw JSON into Parquet batches; calls `ingestion.load_in_game_data_to_duckdb()` to load Parquet into `tracker_events_raw` and `game_events_raw` DuckDB tables. Records file count, row count, and extraction errors. | `sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_02_in_game_extraction.py` | `01_01_02_extraction_log.json`, `01_01_02_extraction_log.md` | `tracker_events_raw` and `game_events_raw` exist; row counts recorded; extraction errors logged |
| 01_01_03 | Path A / Path B join validation on `replay_id`. Joins `raw` (Path A) to `tracker_events_raw` (Path B) on canonical `replay_id`. Reports count of orphan `replay_id` values in either direction. Verifies every `replay_id` with tracker events in Path A has a corresponding entry in Path B. | `sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_03_join_validation.py` | `01_01_03_join_validation.md` | Zero orphan `replay_id` values in either direction; join is clean |

### 01_02 — Exploratory Data Analysis (Tukey-style)

| Step | Description | Notebook | Artifacts | Gate condition |
|------|-------------|----------|-----------|----------------|
| 01_02_01 | Corpus summary. Calls `exploration.run_corpus_summary()`. Reports total replays, total tournaments, date range, replays with/without tracker events, player-count distribution per replay (flags anomalies where count ≠ 2), and result field completeness (`Win`/`Loss`/other). Includes duplicate replay detection (same `replay_id` in multiple tournament dirs). | `sandbox/sc2/sc2egset/01_exploration/01_eda/01_02_01_corpus_summary.py` | `01_02_01_corpus_summary.json`, `01_02_01_corpus_summary.md` | Corpus dimensions recorded; player-count anomalies and result anomalies enumerated; duplicate `replay_id` count recorded |
| 01_02_02 | Per-tournament parse quality. Calls `exploration.run_parse_quality_by_tournament()`. For each tournament: total replays, has-events count, missing-events count, null-timestamp count, event-coverage percentage, player-count anomalies, result anomalies. Sorted by event coverage ascending (worst first). | `sandbox/sc2/sc2egset/01_exploration/01_eda/01_02_02_parse_quality.py` | `01_02_02_parse_quality_by_tournament.csv`, `01_02_02_parse_quality_summary.md` | Per-tournament quality table written; tournaments with >20% missing events identified |
| 01_02_03 | Game duration distribution. Calls `exploration.run_duration_distribution()`. Computes `elapsedGameLoops / 22.4 / 60` (real-time minutes) and `elapsedGameLoops / 16.0 / 60` (game-time minutes). Produces histogram (1-minute bins, 0–60 min), left-tail zoom (30-second bins, 0–10 min), and summary statistics (mean, median, p1, p5, p10, p25, p75, p90, p95, p99) overall and by year. No duration threshold applied — observation only. | `sandbox/sc2/sc2egset/01_exploration/01_eda/01_02_03_duration_distribution.py` | `01_02_03_duration_distribution.csv`, `01_02_03_duration_full.png`, `01_02_03_duration_short_tail.png` | Distribution data and plots written; no threshold decision made |
| 01_02_04 | APM and MMR audit. Calls `exploration.run_apm_mmr_audit()`. Produces year-by-year and league-by-league breakdown of APM non-zero rate and MMR non-zero rate. Documents usability findings: APM usable from 2017+; MMR systematically missing (tournament/lobby replays). Conclusion stated in artifact. | `sandbox/sc2/sc2egset/01_exploration/01_eda/01_02_04_apm_mmr_audit.py` | `01_02_04_apm_mmr_audit.md` | Year-by-year APM and MMR tables written; usability conclusion documented |
| 01_02_05 | Patch landscape. Calls `exploration.run_patch_landscape()`. Extracts `metadata->>'$.gameVersion'` and `metadata->>'$.dataBuild'` from `raw`. Produces a table of distinct game versions with replay count and date range. Groups by year and identifies broad patch eras (LotV launch 2015-11, patch 3.8 2016-11, patch 4.0 2017-11, patch 4.11 2019-11, final balance 2020-10, maintenance 2021+). | `sandbox/sc2/sc2egset/01_exploration/01_eda/01_02_05_patch_landscape.py` | `01_02_05_patch_landscape.csv`, `01_02_05_patch_landscape.md` | Version table and era grouping written |

### 01_03 — Systematic Data Profiling

| Step | Description | Notebook | Artifacts | Gate condition |
|------|-------------|----------|-----------|----------------|
| 01_03_01 | Tracker event type inventory. Calls `exploration.run_event_type_inventory()`. Corpus-wide and per-replay distribution for all event types in `tracker_events_raw` (`PlayerStats`, `UnitBorn`, `UnitDied`, `UnitInit`, `UnitDone`, `Upgrade`, `PlayerSetup`, and any others present). Reports total rows per type, average and median per replay, and count of replays with zero events of each type. Stratified by tournament and by year. | `sandbox/sc2/sc2egset/01_exploration/01_profiling/01_03_01_event_type_inventory.py` | `01_03_01_event_type_inventory.csv`, `01_03_01_event_type_inventory.md` | Event type table written; replays with zero `PlayerStats` events counted |
| 01_03_02 | `PlayerStats` event sampling and field check. Calls `exploration.run_playerstats_sampling_check()`. Samples `PlayerStats` events across tournaments and years; enumerates all fields present in the `event_data` JSON blob; checks field completeness and consistency across the corpus. Identifies fields that are always null or always constant (candidates for dropping). | `sandbox/sc2/sc2egset/01_exploration/01_profiling/01_03_02_playerstats_sampling.py` | `01_03_02_playerstats_sampling.md` | `PlayerStats` field list recorded; always-null and always-constant fields identified |
| 01_03_03 | Game settings audit. Profiles game-settings fields extracted from `initData` and `details` JSON columns: `isBlizzard`, `gameMode`, `speed`, `mapName`, `expansion`, race fields. Reports distinct values, frequencies, and missing-value rates per field stratified by tournament and year. Documents which combinations correspond to competitive 1v1. | `sandbox/sc2/sc2egset/01_exploration/01_profiling/01_03_03_game_settings_audit.py` | `01_03_03_game_settings_audit.csv`, `01_03_03_game_settings_audit.md` | Settings field frequencies written; competitive-1v1 filter criteria documented |
| 01_03_04 | Top-level field inventory. Calls `exploration.run_toplevel_field_inventory()`. Profiles all scalar columns in `raw` (non-JSON columns) plus top-level keys extracted from each JSON column (`header`, `initData`, `details`, `metadata`, `ToonPlayerDescMap`). Reports null rates, distinct counts, and data types for every field. | `sandbox/sc2/sc2egset/01_exploration/01_profiling/01_03_04_field_inventory.py` | `01_03_04_field_inventory.csv`, `01_03_04_field_inventory.md` | Full field inventory with null rates and distinct counts written |
| 01_03_05 | `event_data` JSON inventory for tracker and game events. Calls `exploration.build_event_data_field_inventory_query()` and `exploration.build_event_data_key_constancy_query()` to profile the `event_data` JSON blob within `tracker_events_raw` and `game_events_raw`. Reports which keys are present per event type, their null rates, and whether key sets are constant across the corpus. Calls `exploration.run_tracker_event_data_inventory()` and `exploration.run_game_event_data_inventory()`. | `sandbox/sc2/sc2egset/01_exploration/01_profiling/01_03_05_event_data_inventory.py` | `01_03_05_tracker_event_data_inventory.csv`, `01_03_05_game_event_data_inventory.csv`, `01_03_05_event_data_inventory.md` | Key inventory per event type written; key-set constancy checked |
| 01_03_06 | Parquet / DuckDB schema reconciliation. Calls `exploration.run_parquet_duckdb_reconciliation()`. Compares the schema of Parquet batch files on disk to the schema of `tracker_events_raw` and `game_events_raw` in DuckDB. Reports any type mismatches, column-name mismatches, or missing columns. Confirms that `load_in_game_data_to_duckdb()` reproduces the Parquet schema exactly. | `sandbox/sc2/sc2egset/01_exploration/01_profiling/01_03_06_parquet_duckdb_reconciliation.py` | `01_03_06_parquet_duckdb_reconciliation.md` | Schema match confirmed (or mismatches documented); `verify_parquet_duckdb_schema_consistency()` called |
| 01_03_07 | `ToonPlayerDescMap` (TPDM) field inventory. Calls `exploration.run_tpdm_field_inventory()` and `exploration.run_tpdm_key_set_constancy()`. Profiles all keys within the `ToonPlayerDescMap` JSON column: `result`, `APM`, `MMR`, `highestLeague`, `clanTag`, `name`, and any others. Reports key-set constancy (does every row have the same keys?) and null/zero rates per key, stratified by tournament and year. | `sandbox/sc2/sc2egset/01_exploration/01_profiling/01_03_07_tpdm_profiling.py` | `01_03_07_tpdm_profiling.csv`, `01_03_07_tpdm_profiling.md` | TPDM key set and null/zero rates written; key-set constancy recorded |

### 01_04 — Data Cleaning

| Step | Description | Notebook | Artifacts | Gate condition |
|------|-------------|----------|-----------|----------------|
| 01_04_01 | Cleaning rule inventory. Documents candidate cleaning rules derived from Phase 01 profiling findings — does not apply them. Each candidate rule is assigned an identifier (R1, R2, ...), a trigger condition, the affected rows, and the decision rationale. Rules cover: duration threshold selection (informed by 01_02_03 distribution), player-count filter (R: keep only games with exactly 2 players), result completeness filter (R: keep only games with one `Win` and one `Loss`), duplicate removal strategy, event-coverage threshold (R: minimum `PlayerStats` events per replay), game-settings filter (R: competitive 1v1 only). Rules are observations, not code. | `sandbox/sc2/sc2egset/01_exploration/01_cleaning/01_04_01_cleaning_rule_inventory.py` | `01_04_01_cleaning_rule_inventory.md` | Cleaning rule inventory written with one row per candidate rule; no rules applied to data |

### 01_05 — Temporal & Panel EDA

| Step | Description | Notebook | Artifacts | Gate condition |
|------|-------------|----------|-----------|----------------|
| 01_05_01 | Temporal coverage and panel structure. Computes replay count by year and by tournament, cumulative coverage over time, and player re-appearance frequency (how many replays feature the same player across different tournaments). Identifies the panel structure: are players repeated across time? Reports the distribution of per-player game counts to assess whether player history is dense enough for sliding-window features. Documents the earliest and latest match timestamps per player. | `sandbox/sc2/sc2egset/01_exploration/01_temporal/01_05_01_temporal_coverage.py` | `01_05_01_temporal_coverage.csv`, `01_05_01_temporal_coverage.md` | Temporal coverage table and panel structure summary written |

### 01_06 — Decision Gates

| Step | Description | Notebook | Artifacts | Gate condition |
|------|-------------|----------|-----------|----------------|
| 01_06_01 | Epistemic-readiness deliverables. Assembles four deliverables required to pass the Phase 01 gate: (1) Dataset characterisation — corpus scope, parse quality, key distributional findings from 01_02 and 01_03. (2) Temporal structure memo — panel depth, player re-appearance rates, sliding-window feasibility from 01_05_01. (3) Feature feasibility register — for each candidate feature class (APM, MMR, race, map, patch era, game-settings flags), states whether the field is available and usable given findings from 01_02–01_04. (4) `INVARIANTS.md` — creates `src/rts_predict/sc2/reports/sc2egset/INVARIANTS.md` documenting verifiable dataset invariants (game loop formula, canonical `replay_id` definition, APM/MMR usability boundaries, competitive-1v1 filter criteria). | `sandbox/sc2/sc2egset/01_exploration/01_gates/01_06_01_decision_gates.py` | `01_06_01_dataset_characterisation.md`, `01_06_01_temporal_structure_memo.md`, `01_06_01_feature_feasibility_register.md`, `INVARIANTS.md` (written to dataset reports root, not artifacts/) | All four deliverables exist on disk; `INVARIANTS.md` written at `src/rts_predict/sc2/reports/sc2egset/INVARIANTS.md` |

### Phase 01 gate

All of the following must hold before Phase 02 Steps are defined:

- `raw`, `tracker_events_raw`, and `game_events_raw` tables exist with recorded row counts
- Join between Path A and Path B has zero orphan `replay_id` values (01_01_03)
- Duration distribution artifact exists with no threshold decision hardcoded (01_02_03)
- APM/MMR usability documented with year-by-year evidence (01_02_04)
- Cleaning rule inventory written (candidate rules, not applied) (01_04_01)
- Temporal coverage and panel structure documented (01_05_01)
- `INVARIANTS.md` written at `src/rts_predict/sc2/reports/sc2egset/INVARIANTS.md` (01_06_01)
- `PHASE_STATUS.yaml` updated to reflect Phase 01 complete

---

## Phase 02 — Feature Engineering (placeholder)

Pipeline Sections per `docs/PHASES.md`:

- `02_01` — Pre-Game vs In-Game Boundary
- `02_02` — Symmetry & Difference Features
- `02_03` — Temporal Features, Windows, Decay, Cold Starts
- `02_04` — Feature Quality Assessment
- `02_05` — Categorical Encoding & Interactions
- `02_06` — Feature Selection
- `02_07` — Rating Systems & Domain Features
- `02_08` — Feature Documentation & Catalog

Steps to be defined when Phase 01 gate is met.

---

## Phase 03 — Splitting & Baselines (placeholder)

Pipeline Sections per `docs/PHASES.md`:

- `03_01` — Temporal Splitting Strategies
- `03_02` — Purge & Embargo
- `03_03` — Grouped Splits for Panel Data
- `03_04` — Nested Cross-Validation
- `03_05` — Split Validation
- `03_06` — Baseline Definitions
- `03_07` — Elo & Domain-Specific Baselines
- `03_08` — Shared Evaluation Protocol
- `03_09` — Statistical-Comparison Protocol

Steps to be defined when Phase 02 gate is met.

---

## Phase 04 — Model Training (placeholder)

Pipeline Sections per `docs/PHASES.md`:

- `04_01` — Training Pipelines (sklearn Pipeline + ColumnTransformer)
- `04_02` — GNN Training
- `04_03` — Loss Functions
- `04_04` — Early Stopping
- `04_05` — Learning Rate Scheduling
- `04_06` — Hyperparameter Tuning
- `04_07` — Nested Temporal Cross-Validation
- `04_08` — Reproducibility

Steps to be defined when Phase 03 gate is met.

---

## Phase 05 — Evaluation & Analysis (placeholder)

Pipeline Sections per `docs/PHASES.md`:

- `05_01` — Evaluation Metrics (threshold, probabilistic, ROC/PR, calibration, sharpness)
- `05_02` — Statistical Comparison of Classifiers
- `05_03` — Error Analysis
- `05_04` — Ablation Studies & Sensitivity Analysis

Steps to be defined when Phase 04 gate is met.

---

## Phase 06 — Cross-Domain Transfer (placeholder)

Pipeline Sections per `docs/PHASES.md`:

- `06_01` — Transfer Learning Taxonomy
- `06_02` — Ben-David's Bound & Transfer Feasibility
- `06_03` — Distribution Shift Between Domains
- `06_04` — Shared Feature Space Construction
- `06_05` — Negative Transfer
- `06_06` — Three-Tier Experimental Design
- `06_07` — Transfer Evaluation & Reporting
- `06_08` — Honest Claims With Two Domains
- `06_09` — Component Transferability Analysis

Steps to be defined when Phase 05 gate is met.

---

## Phase 07 — Thesis Writing Wrap-up (gate marker)

Per `docs/PHASES.md`, Phase 07 is a gate marker with no Pipeline Sections.
This dataset's Phase 07 gate is met when all thesis sections fed by this
dataset have reached FINAL status in `thesis/WRITING_STATUS.md`.
