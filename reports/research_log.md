# Research Log

Thesis: "A comparative analysis of methods for predicting game results in real-time strategy games, based on the examples of StarCraft II and Age of Empires II."

Reverse chronological entries. Each entry documents the reasoning and learning behind code changes — intended as source material for thesis writing.

---

## 2026-04-03 — Methodology restart: data exploration before modelling

**Objective:** Establish correct execution order. Data exploration (corpus inventory,
player identity resolution, temporal structure, in-game statistics profiling, map
and meta-game analysis) must complete before any feature engineering or modelling
decisions are made.

**What happened:** The pipeline was built in the wrong order. Feature groups A–E were
defined, Elo was implemented, and model training was run before the dataset was
explored. The sanity validation (`reports/archive/sanity_validation.md`) revealed
the consequences:
- Elo is flat (std = 0.0) — Elo was computed but never validated against the raw data
- BW race codes (`BWPr`, `BWTe`, `BWZe`) are leaking through — the `flat_players`
  view filter is not working correctly on the full corpus
- `h2h_p1_winrate_smooth` has 0.62 correlation with target — likely a leakage bug
  in head-to-head computation
- GNN predicts P2 wins on every single test example (majority-class collapse)
- 13 match_ids have unexpected row counts — data anomalies not yet investigated

None of these are fixable by patching individual modules. They are symptoms of
building features before understanding the data.

**Decision:** Archive the prior roadmap and methodology draft. Begin from Phase 0
of `reports/SC2ML_THESIS_ROADMAP.md`. Existing code is treated as a draft to audit
and revise as exploration findings arrive, not as correct implementations to extend.

**Archived:**
- `reports/archive/ROADMAP_v1.md` (old ROADMAP.md — caused premature GNN execution)
- `reports/archive/methodology_v1.md` (old methodology.md — assumed unvalidated decisions)
- `reports/archive/sanity_validation.md` (evidence of pre-restart state)

**Thesis notes:** This restart is itself thesis-relevant. The sanity validation
failures demonstrate precisely why the data exploration → cleaning → feature
engineering → modelling order is not optional. The BW race leakage, the flat Elo,
and the H2H correlation will all appear in the thesis as motivating examples for the
methodology chapter's argument that feature design requires prior data characterisation.

---

## 2026-04-02 — Feature engineering rewrite: methodology Groups A–E with ablation support

**Objective:** Decompose the monolithic `features/engineering.py` into composable feature groups matching methodology Section 3.1 (Groups A–E), add missing features (form/momentum, context), eliminate duplicate split logic, and fix a long-standing segfault in `test_model_reproducibility`.

**Approach:** Created one module per methodology group (`group_a_elo.py` through `group_e_context.py`) with shared primitives in `common.py` and a registry/enum system for ablation. `build_features(df, groups=FeatureGroup.C)` computes A+B+C and returns a clean DataFrame. `split_for_ml()` replaces the old `temporal_train_test_split()` by consuming the series-aware split from `data/processing.py` rather than reimplementing it.

**New features added:**
- Group B: `hist_std_apm`, `hist_std_sq` (expanding-window variance)
- Group C: `hist_winrate_map_race_smooth` (map×race interaction winrate)
- Group D (entirely new): win/loss streaks (iterative forward pass), EMA of APM/SQ/winrate, activity windows (7d/30d rolling counts), head-to-head cumulative record with Bayesian smoothing
- Group E (entirely new): patch version as sortable integer, tournament match position, series game number from `match_series` table

**Issues encountered:**
- **Dual-OpenMP segfault**: `test_model_reproducibility` segfaulted because LightGBM (Homebrew `libomp.dylib` at `/opt/homebrew/*/libomp.dylib`) and PyTorch (bundled `libomp.dylib` at `.venv/*/libomp.dylib`) load two separate OpenMP runtimes. At shutdown, OpenMP thread pool teardown in one runtime corrupts the other. The crash trace shows Thread 3 in `__kmp_suspend_initialize_thread` while Thread 0 is in LightGBM's `_pthread_create`. Fix: classical model tests run in a `multiprocessing.spawn` child process (`tests/helpers_classical.py` which never imports torch), isolating the runtimes. This is the same isolation pattern used in `test_mps.py` for Metal/MPS issues.
- Rolling time-window activity counts required a dummy column (`_one`) because pandas `groupby().rolling()[col]` can't use the groupby column as the aggregation target.
- `pd.get_dummies` creates bool columns — needed explicit cast to int for model compatibility.

**Resolution/Outcome:** 168 tests pass (73 new feature tests + 64 data tests + 31 existing), 99% coverage on `features/`, 93% overall. The segfault in `test_model_reproducibility` is fixed. Feature column count grows monotonically: A→14, A+B→37, A+B+C→45, A+B+C+D→62, all→66.

**Thesis notes:** The feature group structure directly maps to the ablation protocol in Section 7.1: run LightGBM on {A}, {A,B}, ..., {A,B,C,D,E} and report marginal lift per group. Group D (form/momentum) and Group E (context) fill gaps identified in the methodology — streaks, recency weighting, head-to-head records, and series position were previously missing. The dual-OpenMP issue should be noted in the thesis reproducibility section: on macOS with Homebrew LightGBM and pip-installed PyTorch, classical and GNN model evaluations must run in separate processes to avoid OpenMP shutdown conflicts.

---

## 2026-04-02 — Path B: In-game event extraction pipeline and temporal split management

**Objective:** Build the data extraction layer for accessing raw in-game events (tracker events, game events) from SC2 replay files, and implement proper temporal train/val/test splitting with series-aware boundaries.

**Approach:** Designed a two-phase extraction pipeline: (1) multiprocessing-based raw event extraction from replay JSON to Parquet intermediate storage, and (2) DuckDB loading with typed views (player_stats with 39 stat columns, match_player_map for game event correlation). Temporal splitting uses a 80/15/5 ratio with a 2-hour gap heuristic to group best-of series and prevent series from being split across partitions.

**Issues encountered:**
- `slim_down_sc2_with_manifest()` was destructive (modifies files in-place with no undo) — added `dry_run=True` default to prevent accidental data loss.
- Best-of series detection requires a time-gap heuristic since replays don't explicitly mark series membership. Chose 2 hours as a conservative threshold.
- Pre-existing MPS segfault in `test_model_reproducibility` (unrelated to this work).

**Resolution/Outcome:** All 70 tests pass (28 existing + 42 new). Pipeline architecture separates extraction (CPU-bound, parallelized) from loading (DuckDB bulk inserts). Parquet intermediate format enables inspection and re-loading without re-extraction.

**Thesis notes:** The series-aware temporal split is methodologically important — naive time-based splits can leak information when consecutive games in a best-of series land in different partitions. The 80/15/5 split with validation set supports proper hyperparameter tuning without test set contamination. The 39-field player_stats view provides the foundation for in-game feature engineering (Chapter 4).

---

## 2026-04-02 — Repository restructured into proper Python package

**Objective:** Reorganize flat 13-module codebase into a proper `src/sc2ml/` package layout to support maintainability, testability, and future AoE2 integration.

**Approach:** Adopted PyPA-recommended src layout with four subpackages (`data/`, `features/`, `models/`, `gnn/`). Renamed modules to avoid namespace redundancy. Updated all imports, fixed test infrastructure (removed `sys.path` hacks, created proper `conftest.py`), configured Poetry for package mode with CLI entry point. Archived legacy execution reports to `reports/archive/`.

**Issues encountered:**
- `conftest.py` is auto-loaded by pytest but not directly importable — required moving shared test utilities to `tests/helpers.py` instead.
- Pre-existing LightGBM segfault on Apple M4 Max during `test_model_reproducibility` (known MPS issue, unrelated to refactoring).
- Ruff identified pre-existing F821 errors from string type annotations — fixed with proper `TYPE_CHECKING` imports.

**Resolution/Outcome:** All 28 non-MPS tests pass. Ruff clean (1 pre-existing E501 in `test_mps.py`). Package installs correctly via `poetry install`. CLI entry point registered. Legacy reports preserved in `reports/archive/`.

**Thesis notes:** The src layout establishes the foundation for shared abstractions when AoE2 integration begins. The package structure makes it clear which components are game-specific (data ingestion, graph construction) vs. reusable (model evaluation, feature engineering patterns).

---

## 2026-04-02 — Project infrastructure setup for Claude Code collaboration

**Objective:** Establish structured development workflow with rich guidelines, git conventions, and documentation trail for thesis work.

**Approach:** Augmented CLAUDE.md with comprehensive sections covering permissions, coding standards, ML experiment protocol, and documentation requirements. Created CHANGELOG.md and this research log.

**Issues encountered:** None — greenfield setup.

**Resolution/Outcome:** Three-tier documentation system in place: CHANGELOG (code versioning), research log (thesis narrative), execution reports (raw pipeline output).

**Thesis notes:** This infrastructure supports the reproducibility and methodology documentation requirements of the thesis. The structured experiment protocol (hypothesis-first, temporal splits, baseline comparisons) will provide a clear audit trail for Chapter 3 (Methodology).

---

## 2026-03-30 — Baseline SC2 pipeline results on Apple M4 Max (summary of prior work)

**Objective:** Establish working end-to-end prediction pipeline for StarCraft II match outcomes using both classical ML and Graph Neural Networks.

**Approach:** Built 5-stage pipeline: data ingestion from SC2Replay JSON files into DuckDB, SQL-based feature views, custom ELO system with dynamic K-factor, Bayesian-smoothed feature engineering (45+ features), and three model training paths (classical ML, Node2Vec embeddings, GATv2 GNN).

**Issues encountered:**
- Apple M4 Max MPS backend causes silent failures and segfaults with sparse tensor operations in PyTorch Geometric. Workaround: force CPU for GNN training, set `PYTORCH_ENABLE_MPS_FALLBACK=1`.
- Data leakage risk from using current-match statistics (APM, SQ, supply_capped_pct) as features. Resolution: feature engineering uses only pre-match historical aggregates.
- `matches_flat` view produces 2 rows per match (both player perspectives) — intentional augmentation but requires careful handling in ELO computation (deduplicate via `processed_matches` set).

**Resolution/Outcome:** Classical ML models achieve ~63-65% accuracy (Gradient Boosting best). Top features: historical win rate, experience differential, SQ differential. GNN pipeline functional with GATv2 edge classification. See `reports/archive/09_run.md` for detailed metrics.

**Thesis notes:** The ~63-65% accuracy on temporal splits provides a solid baseline for comparative analysis. The feature importance ranking (win rate > experience > mechanical skill) aligns with domain knowledge about RTS skill factors. MPS compatibility issues should be documented in the thesis as a practical consideration for reproducibility on Apple Silicon.
