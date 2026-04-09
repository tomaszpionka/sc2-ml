# aoe2companion Dataset Roadmap

**Game:** AoE2
**Dataset:** aoe2companion
**Canonical phase list:** `docs/PHASES.md`
**Methodology manuals:** `docs/INDEX.md`
**Step definition schema:** `docs/templates/step_template.yaml`

---

## How to use this document

This file decomposes Phases into Pipeline Sections and Steps for the aoe2companion
dataset. The canonical Phase definitions and Pipeline Section enumerations live
in `docs/PHASES.md`. This ROADMAP does not invent Phases or Pipeline Sections;
it only decomposes them into Steps.

Only the currently-active Phase has fully defined Steps. Future Phases are
listed as placeholders with their Pipeline Section outline from `docs/PHASES.md`.
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

### 01_01 — Data Acquisition & Source Inventory

| Step | Description | Notebook | Artifacts | Gate condition |
|------|-------------|----------|-----------|----------------|
| 01_01_01 | Ingest existing raw Parquet/CSV into DuckDB. Calls `ingestion.load_all_raw_tables()` to read the four raw file sets (match parquets, rating CSVs, leaderboard parquet, profiles parquet) into DuckDB tables `raw_matches`, `raw_ratings`, `raw_leaderboard`, and `raw_profiles`. Validates row counts against README.md provenance record (~277M matches, ~58M ratings, ~2.4M leaderboard, ~3.6M profiles). Records schema, file counts, and ingestion timestamps. No data is downloaded; all source files already exist on disk. | `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_raw_ingestion.py` | `01_01_01_raw_ingestion.json`, `01_01_01_raw_ingestion.md` | All four tables exist in DuckDB; row counts match README.md within 0.1%; schema written; zero ingestion errors |
| 01_01_02 | Schema export and dtype audit. Exports the DuckDB schema for all four raw tables to YAML. Verifies that `raw_ratings` uses the explicit dtype map documented in the README.md archive (profile_id, games, rating, date, leaderboard_id, season, rating_diff were problematic under auto-detect). Confirms the `filename` provenance column is present in every table. | `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_02_schema_export.py` | `01_01_02_schema_export.yaml`, `01_01_02_schema_export.md` | Schema YAML written for all four tables; explicit dtype map confirmed for `raw_ratings`; `filename` column confirmed in every table |

### 01_02 — Exploratory Data Analysis (Tukey-style)

| Step | Description | Notebook | Artifacts | Gate condition |
|------|-------------|----------|-----------|----------------|
| 01_02_01 | Corpus summary. Reports total matches, unique players, date range, and result-field completeness in `raw_matches`. Counts distinct leaderboard IDs and civilisations. Identifies missing-result rate and any rows where winner is null or ambiguous. Stratified by year and by leaderboard type. | `sandbox/aoe2/aoe2companion/01_exploration/01_eda/01_02_01_corpus_summary.py` | `01_02_01_corpus_summary.json`, `01_02_01_corpus_summary.md` | Corpus dimensions recorded; result-field completeness documented; stratified counts written |
| 01_02_02 | Rating EDA. Analyses `raw_ratings` distribution by leaderboard, year, and player. Reports rating range, median, and null rates. Documents the sparse-regime boundary (2025-06-26): compares rating coverage before and after the boundary date. Plots rating count by month. Identifies cold-start problem: fraction of matches where no pre-match rating is available for one or both players. | `sandbox/aoe2/aoe2companion/01_exploration/01_eda/01_02_02_rating_eda.py` | `01_02_02_rating_eda.csv`, `01_02_02_rating_eda.md`, `01_02_02_rating_coverage_by_month.png` | Rating distribution table written; sparse-regime boundary documented; cold-start fraction quantified |
| 01_02_03 | Match settings distribution. Profiles `raw_matches` game-settings fields: map type, civilisation picks, team size, ranked vs. unranked, game speed, and leaderboard ID. Reports distinct-value frequencies and missing rates per field stratified by year. Documents which combinations correspond to ranked 1v1 (the primary analysis target). | `sandbox/aoe2/aoe2companion/01_exploration/01_eda/01_02_03_match_settings.py` | `01_02_03_match_settings.csv`, `01_02_03_match_settings.md` | Settings field frequencies written; ranked-1v1 filter criteria documented |

### 01_03 — Systematic Data Profiling

| Step | Description | Notebook | Artifacts | Gate condition |
|------|-------------|----------|-----------|----------------|
| 01_03_01 | raw_matches column profiling. Profiles all columns in `raw_matches`: null rates, distinct counts, data types, value distributions for key fields (winner, leaderboard_id, map_type, num_players, game_speed, started, finished). Reports any rows with impossible values (e.g., finished < started, num_players outside expected range). Stratified by year and leaderboard type. | `sandbox/aoe2/aoe2companion/01_exploration/01_profiling/01_03_01_matches_profiling.py` | `01_03_01_matches_profiling.csv`, `01_03_01_matches_profiling.md` | Full column inventory with null rates and distinct counts written; impossible-value rows counted |
| 01_03_02 | raw_ratings column profiling. Profiles all columns in `raw_ratings`: null rates, distinct counts, rating and games distribution by leaderboard and year. Reports fraction of (player, leaderboard) combinations with fewer than 5 rating records (unstable history). Documents temporal gaps in rating records per player. Stratified by leaderboard_id and by sparse-regime segment (pre/post 2025-06-26). | `sandbox/aoe2/aoe2companion/01_exploration/01_profiling/01_03_02_ratings_profiling.py` | `01_03_02_ratings_profiling.csv`, `01_03_02_ratings_profiling.md` | Column inventory written; unstable-history player fraction documented; temporal-gap analysis by sparse-regime segment written |
| 01_03_03 | Snapshot table profiling. Profiles `raw_leaderboard` and `raw_profiles`. Reports column inventory, null rates, and distinct counts for both tables. **Documents the snapshot limitation explicitly:** these tables cannot be used for temporal feature engineering; their T_snapshot timestamps are recorded. Notes which `raw_matches` player IDs are present vs. absent in `raw_profiles`. | `sandbox/aoe2/aoe2companion/01_exploration/01_profiling/01_03_03_snapshot_profiling.py` | `01_03_03_snapshot_profiling.csv`, `01_03_03_snapshot_profiling.md` | Snapshot column inventories written; T_snapshot values confirmed; match-to-profile join completeness rate recorded |

### 01_04 — Data Cleaning

| Step | Description | Notebook | Artifacts | Gate condition |
|------|-------------|----------|-----------|----------------|
| 01_04_01 | Cleaning rule inventory. Documents candidate cleaning rules derived from Phase 01 profiling findings — does not apply them. Each candidate rule is assigned an identifier (R1, R2, ...), a trigger condition, the affected rows, and the decision rationale. Rules cover: result-completeness filter (keep only matches with an unambiguous winner), team-size filter (keep only 1v1), ranked filter (keep only ranked matches), duration plausibility filter (remove matches with finished ≤ started or impossibly short durations), duplicate match removal, and rating-availability filter (document minimum rating-record requirement for feature computation, given sparse regime). Rules are observations, not code. | `sandbox/aoe2/aoe2companion/01_exploration/01_cleaning/01_04_01_cleaning_rule_inventory.py` | `01_04_01_cleaning_rule_inventory.md` | Cleaning rule inventory written with one row per candidate rule; no rules applied to data |

### 01_05 — Temporal & Panel EDA

| Step | Description | Notebook | Artifacts | Gate condition |
|------|-------------|----------|-----------|----------------|
| 01_05_01 | Temporal coverage and panel structure. Computes match count by year and by month. Reports player re-appearance frequency: how many players have more than N matches (for N = 5, 10, 50, 100). Assesses panel depth for sliding-window feature feasibility. Documents earliest and latest match timestamps per leaderboard type. Quantifies the proportion of matches falling in the sparse-rating regime (before 2025-06-26). | `sandbox/aoe2/aoe2companion/01_exploration/01_temporal/01_05_01_temporal_coverage.py` | `01_05_01_temporal_coverage.csv`, `01_05_01_temporal_coverage.md` | Temporal coverage table and panel structure summary written; sparse-regime proportion documented |

### 01_06 — Decision Gates

| Step | Description | Notebook | Artifacts | Gate condition |
|------|-------------|----------|-----------|----------------|
| 01_06_01 | Epistemic-readiness deliverables. Assembles four deliverables required to pass the Phase 01 gate: (1) Dataset characterisation — corpus scope, match settings, key distributional findings from 01_02 and 01_03. (2) Temporal structure memo — panel depth, player re-appearance rates, sliding-window feasibility, sparse-regime impact from 01_05_01. (3) Feature feasibility register — for each candidate feature class (pre-match rating, rating delta, civ pick, map type, leaderboard era, game-speed flag, historical win rate), states whether the field is available and usable given findings from 01_02–01_04. (4) `INVARIANTS.md` — creates `src/rts_predict/aoe2/reports/aoe2companion/INVARIANTS.md` documenting verifiable dataset invariants (snapshot table timestamps, sparse-regime boundary, canonical ranked-1v1 filter criteria, `filename` provenance column rule). | `sandbox/aoe2/aoe2companion/01_exploration/01_gates/01_06_01_decision_gates.py` | `01_06_01_dataset_characterisation.md`, `01_06_01_temporal_structure_memo.md`, `01_06_01_feature_feasibility_register.md`, `INVARIANTS.md` (written to dataset reports root, not artifacts/) | All four deliverables exist on disk; `INVARIANTS.md` written at `src/rts_predict/aoe2/reports/aoe2companion/INVARIANTS.md` |

### Phase 01 gate

All of the following must hold before Phase 02 Steps are defined:

- `raw_matches`, `raw_ratings`, `raw_leaderboard`, and `raw_profiles` tables exist in DuckDB with row counts matching README.md provenance within 0.1% (01_01_01)
- Schema YAML written and explicit dtype map for `raw_ratings` confirmed (01_01_02)
- Result-field completeness and ranked-1v1 filter criteria documented (01_02_01, 01_02_03)
- Sparse-regime boundary documented with cold-start fraction quantified (01_02_02)
- Snapshot table limitation explicitly documented; T_snapshot timestamps recorded (01_03_03)
- Cleaning rule inventory written (candidate rules, not applied) (01_04_01)
- Temporal coverage and panel structure documented; sparse-regime proportion quantified (01_05_01)
- `INVARIANTS.md` written at `src/rts_predict/aoe2/reports/aoe2companion/INVARIANTS.md` (01_06_01)
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
