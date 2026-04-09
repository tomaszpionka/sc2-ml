# aoestats Dataset Roadmap

**Game:** AoE2
**Dataset:** aoestats
**Canonical phase list:** `docs/PHASES.md`
**Methodology manuals:** `docs/INDEX.md`
**Step definition schema:** `docs/templates/step_template.yaml`

---

## How to use this document

This file decomposes Phases into Pipeline Sections and Steps for the aoestats
dataset. The canonical Phase definitions and Pipeline Section enumerations live
in `docs/PHASES.md`. This ROADMAP does not invent Phases or Pipeline Sections;
it only decomposes them into Steps.

Only the currently-active Phase has fully defined Steps. Future Phases are
listed as placeholders with their Pipeline Section outline from `docs/PHASES.md`.
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

### 01_01 — Data Acquisition & Source Inventory

| Step | Description | Notebook | Artifacts | Gate condition |
|------|-------------|----------|-----------|----------------|
| 01_01_01 | Ingest existing raw Parquet into DuckDB. Calls `ingestion.load_all_raw_tables()` to read the two raw file sets (match parquets, player parquets) into DuckDB tables `raw_matches` and `raw_players`. Validates row counts against README.md provenance record (~30.7M matches, ~107.6M players). Documents the known missing file `2025-11-16_2025-11-22_players.parquet`: confirms 172 match files and 171 player files are loaded (not 172). Records schema, file counts, and ingestion timestamps. No data is downloaded; all source files already exist on disk. | `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_raw_ingestion.py` | `01_01_01_raw_ingestion.json`, `01_01_01_raw_ingestion.md` | Both tables exist in DuckDB; row counts match README.md within 0.1%; known missing file documented; schema written; zero ingestion errors |
| 01_01_02 | Schema export and dtype audit. Exports the DuckDB schema for both raw tables to YAML. Verifies that type drift from `union_by_name = true` resolved to the canonical types documented in README.md (raw_match_type BIGINT; feudal/castle/imperial_age_uptime INTEGER; profile_id BIGINT; opening INTEGER). Confirms the `filename` provenance column is present in every table. | `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_02_schema_export.py` | `01_01_02_schema_export.yaml`, `01_01_02_schema_export.md` | Schema YAML written for both tables; all drifted columns resolved to canonical types confirmed; `filename` column confirmed in every table |

### 01_02 — Exploratory Data Analysis (Tukey-style)

| Step | Description | Notebook | Artifacts | Gate condition |
|------|-------------|----------|-----------|----------------|
| 01_02_01 | Corpus summary. Reports total matches, unique players, date range, and result-field completeness in `raw_matches`. Counts distinct leaderboard IDs, civilisations, and map types. Identifies missing-result rate and any rows where winner is null or ambiguous. Stratified by year and by leaderboard type. | `sandbox/aoe2/aoestats/01_exploration/01_eda/01_02_01_corpus_summary.py` | `01_02_01_corpus_summary.json`, `01_02_01_corpus_summary.md` | Corpus dimensions recorded; result-field completeness documented; stratified counts written |
| 01_02_02 | Player EDA. Analyses `raw_players` distribution by leaderboard, year, and player. Reports rating range, median, and null rates for player-level rating fields. Identifies cold-start problem: fraction of matches where no pre-match player data is available for one or both players. Acknowledges the known missing week (`2025-11-16_2025-11-22`) and quantifies whether matches in that week are still present via `raw_matches`. | `sandbox/aoe2/aoestats/01_exploration/01_eda/01_02_02_player_eda.py` | `01_02_02_player_eda.csv`, `01_02_02_player_eda.md` | Player distribution table written; cold-start fraction quantified; missing-week impact on raw_players coverage documented |
| 01_02_03 | Match settings distribution. Profiles `raw_matches` game-settings fields: map type, civilisation picks, team size, ranked vs. unranked, game speed, and leaderboard ID. Reports distinct-value frequencies and missing rates per field stratified by year. Documents which combinations correspond to ranked 1v1 (the primary analysis target). | `sandbox/aoe2/aoestats/01_exploration/01_eda/01_02_03_match_settings.py` | `01_02_03_match_settings.csv`, `01_02_03_match_settings.md` | Settings field frequencies written; ranked-1v1 filter criteria documented |

### 01_03 — Systematic Data Profiling

| Step | Description | Notebook | Artifacts | Gate condition |
|------|-------------|----------|-----------|----------------|
| 01_03_01 | raw_matches column profiling. Profiles all columns in `raw_matches`: null rates, distinct counts, data types, value distributions for key fields (winner, leaderboard_id, map_type, num_players, game_speed, started, finished, raw_match_type). Reports any rows with impossible values (e.g., finished < started, num_players outside expected range). Verifies that `raw_match_type` resolved to BIGINT (schema drift confirmation). Stratified by year and leaderboard type. | `sandbox/aoe2/aoestats/01_exploration/01_profiling/01_03_01_matches_profiling.py` | `01_03_01_matches_profiling.csv`, `01_03_01_matches_profiling.md` | Full column inventory with null rates and distinct counts written; impossible-value rows counted; raw_match_type BIGINT confirmed |
| 01_03_02 | raw_players column profiling. Profiles all columns in `raw_players`: null rates, distinct counts, and distributions for key fields including the five schema-drifted columns (feudal_age_uptime, castle_age_uptime, imperial_age_uptime, profile_id, opening). Verifies all drifted columns resolved to canonical types. Documents 171-file coverage and identifies which match dates lack a corresponding player file (the known missing week). Reports fraction of (player, match) combinations with null uptime values. | `sandbox/aoe2/aoestats/01_exploration/01_profiling/01_03_02_players_profiling.py` | `01_03_02_players_profiling.csv`, `01_03_02_players_profiling.md` | Column inventory written; all five drifted columns resolved to canonical types confirmed; missing-week coverage gap documented and quantified |

### 01_04 — Data Cleaning

| Step | Description | Notebook | Artifacts | Gate condition |
|------|-------------|----------|-----------|----------------|
| 01_04_01 | Cleaning rule inventory. Documents candidate cleaning rules derived from Phase 01 profiling findings — does not apply them. Each candidate rule is assigned an identifier (R1, R2, ...), a trigger condition, the affected rows, and the decision rationale. Rules cover: result-completeness filter (keep only matches with an unambiguous winner), team-size filter (keep only 1v1), ranked filter (keep only ranked matches), duration plausibility filter (remove matches with finished ≤ started or impossibly short durations), duplicate match removal, and the known data gap treatment (document the missing `2025-11-16_2025-11-22_players.parquet` week and its impact on player-level feature availability). Rules are observations, not code. | `sandbox/aoe2/aoestats/01_exploration/01_cleaning/01_04_01_cleaning_rule_inventory.py` | `01_04_01_cleaning_rule_inventory.md` | Cleaning rule inventory written with one row per candidate rule; known missing-file gap treatment documented; no rules applied to data |

### 01_05 — Temporal & Panel EDA

| Step | Description | Notebook | Artifacts | Gate condition |
|------|-------------|----------|-----------|----------------|
| 01_05_01 | Temporal coverage and panel structure. Computes match count by year and by month. Reports player re-appearance frequency: how many players have more than N matches (for N = 5, 10, 50, 100). Assesses panel depth for sliding-window feature feasibility. Documents earliest and latest match timestamps per leaderboard type. Highlights the missing week (`2025-11-16_2025-11-22`) as a temporal gap in player coverage and quantifies its effect on contiguous player histories. | `sandbox/aoe2/aoestats/01_exploration/01_temporal/01_05_01_temporal_coverage.py` | `01_05_01_temporal_coverage.csv`, `01_05_01_temporal_coverage.md` | Temporal coverage table and panel structure summary written; missing-week temporal gap effect on player histories quantified |

### 01_06 — Decision Gates

| Step | Description | Notebook | Artifacts | Gate condition |
|------|-------------|----------|-----------|----------------|
| 01_06_01 | Epistemic-readiness deliverables. Assembles four deliverables required to pass the Phase 01 gate: (1) Dataset characterisation — corpus scope, match settings, key distributional findings from 01_02 and 01_03. (2) Temporal structure memo — panel depth, player re-appearance rates, sliding-window feasibility, missing-week impact from 01_05_01. (3) Feature feasibility register — for each candidate feature class (pre-match player stats, age uptime, civilisation pick, map type, leaderboard era, game-speed flag, historical win rate), states whether the field is available and usable given findings from 01_02–01_04. (4) `INVARIANTS.md` — creates `src/rts_predict/aoe2/reports/aoestats/INVARIANTS.md` documenting verifiable dataset invariants (known missing file, schema drift canonical types, canonical ranked-1v1 filter criteria, `filename` provenance column rule). | `sandbox/aoe2/aoestats/01_exploration/01_gates/01_06_01_decision_gates.py` | `01_06_01_dataset_characterisation.md`, `01_06_01_temporal_structure_memo.md`, `01_06_01_feature_feasibility_register.md`, `INVARIANTS.md` (written to dataset reports root, not artifacts/) | All four deliverables exist on disk; `INVARIANTS.md` written at `src/rts_predict/aoe2/reports/aoestats/INVARIANTS.md` |

### Phase 01 gate

All of the following must hold before Phase 02 Steps are defined:

- `raw_matches` and `raw_players` tables exist in DuckDB with row counts matching README.md provenance within 0.1% (01_01_01)
- Known missing file `2025-11-16_2025-11-22_players.parquet` documented; 171 player files confirmed (01_01_01)
- Schema YAML written and all drifted column types confirmed against canonical types (01_01_02)
- Result-field completeness and ranked-1v1 filter criteria documented (01_02_01, 01_02_03)
- Cold-start fraction and missing-week coverage impact quantified (01_02_02)
- Schema drift canonical types verified for both tables in profiling (01_03_01, 01_03_02)
- Cleaning rule inventory written (candidate rules, not applied); known data gap treatment documented (01_04_01)
- Temporal coverage and panel structure documented; missing-week gap effect quantified (01_05_01)
- `INVARIANTS.md` written at `src/rts_predict/aoe2/reports/aoestats/INVARIANTS.md` (01_06_01)
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
