# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Conventional Commits](https://www.conventionalcommits.org/).

Each feature branch merges as a semver bump. The `[Unreleased]` section
tracks only changes on the current working branch that have not yet been
merged to `master`.

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

## [0.16.0] — 2026-04-04 (PR #30: refactor/mypy-and-test-cleanup)

### Added
- `tests/test_mps.py` rewritten as proper pytest: 5 test functions with `@pytest.mark.mps`, `skipif` guard, and session cleanup fixture (replaces standalone script)
- `mps` pytest marker registered in `pyproject.toml`

### Changed
- Fixed 37 mypy type errors across 8 files: `fetchone()` None guards on all DuckDB queries, `Generator` return types on yielding fixtures, explicit `rows` annotation in conftest

### Removed
- `tests/helpers.py` — unused `make_matches_df()` / `make_series_df()` (never imported)

## [0.15.1] — 2026-04-04 (PR: pending, chore/archive-cleanup)

### Removed
- 16 archive files (run logs 01-09, ROADMAP_v1, methodology_v1, data_analysis_notes, gnn_collapse_log, sanity_validation, research_log, gnn_space_map) replaced by single `ARCHIVE_SUMMARY.md`

## [0.15.0] — 2026-04-04 (PR: pending, docs/claude-config-restructure)

### Changed
- `CLAUDE.md` rewritten to 80 lines (from 277) — project identity, critical rules, and session workflow only; all detailed guidance moved to path-scoped rules
- `.claude/project-architecture.md` → `.claude/dev-constraints.md` — stripped ARCHITECTURE.md duplication, kept only non-obvious constraints (module ordering, legacy warnings, platform notes, external data paths)
- `.claude/ml-protocol.md` — added phase-activation guard (Phase 9+)
- `ARCHITECTURE.md` — updated 3 references from deleted files to new `.claude/rules/thesis-writing.md`

### Added
- `.claude/rules/python-code.md` — merged coding-standards + testing-standards + python-workflow (loads on `**/*.py` touch)
- `.claude/rules/thesis-writing.md` — merged thesis-writing + chat-handoff (loads on `thesis/**/*` touch)
- `.claude/rules/sql-data.md` — extracted SQL/data constraints from project-architecture (loads on `*/data/**/*.py` touch)
- `.claude/rules/git-workflow.md` — moved from `.claude/git-workflow.md` with PR template instructions preserved (loads on CHANGELOG/pyproject touch)

### Removed
- `.claude/coding-standards.md` — absorbed into `rules/python-code.md`
- `.claude/testing-standards.md` — absorbed into `rules/python-code.md`
- `.claude/python-workflow.md` — absorbed into `rules/python-code.md`
- `.claude/thesis-writing.md` — absorbed into `rules/thesis-writing.md`
- `.claude/chat-handoff.md` — absorbed into `rules/thesis-writing.md`
- `.claude/git-workflow.md` — absorbed into `rules/git-workflow.md`
- `.claude/aoe2-plan.md` — placeholder content, no longer needed
- `.claude/project-architecture.md` — replaced by `dev-constraints.md`

**Impact:** Always-loaded context reduced from 1,416 → 287 lines (−80%), 63,658 → 14,364 chars (−77%), 11 → 4 files (−64%). All content preserved in on-demand path-scoped rules.

## [0.14.3] — 2026-04-04 (PR: pending, chore/slim-pr-template)

### Changed
- `.github/pull_request_template.md` — stripped to three sections (Summary, optional Motivation, Test plan) and Claude Code footer; removed type/scope checkboxes, changes table, ML experiment, data integrity and documentation checklists, and commit messages block
- `.claude/git-workflow.md` Step 7 — PR body guidance now explicitly references the template structure and provides a `gh pr create` heredoc example

## [0.14.2] — 2026-04-04 (PR: pending, chore/sc2-data-compression-scripts)

### Added
- `src/rts_predict/sc2/data/sc2_rezip_data.sh` — re-zips each `*_data/` tournament
  directory back into a `*_data.zip` archive. Idempotent: skips tournaments where the
  zip already exists. Critical for local storage: 22 390 individual JSON files (~209 GB
  uncompressed) cause sustained Spotlight indexing and Defender real-time scanning on
  every file access, generating unnecessary IO load. Re-zipping compresses to ~12 GB
  and makes archives opaque to indexers. If data is ever moved to object storage
  (S3/GCS) this step is unnecessary as cloud storage is not subject to local IO overhead.
- `src/rts_predict/sc2/data/sc2_remove_data_dirs.sh` — removes `*_data/` source
  directories after re-zipping. Three guards required before any delete: (1) matching
  `.zip` exists, (2) zip is non-zero bytes, (3) real JSON file count in zip (excluding
  `._*` ditto resource-fork stubs) equals count in directory. Must be run after
  `sc2_rezip_data.sh` reports zero failures.
- `src/rts_predict/sc2/data/sc2_validate_map_name_mappings.sh` — validates that
  `map_foreign_to_english_mapping.json` is byte-identical across all tournament
  directories.

## [0.14.1] — 2026-04-04 (PR: pending, chore/repo-reorganization)

> Note: Entries before v0.14.0 reference the old `sc2ml` package name and
> root-level `reports/` paths. See the repo reorganization in v0.14.0.

### Added
- **Step 2.5**: `src/rts_predict/sc2/PHASE_STATUS.yaml` — machine-readable SC2 phase progress
- **Step 2.5**: `src/rts_predict/aoe2/PHASE_STATUS.yaml` — AoE2 placeholder
- **Step 2.6**: `src/rts_predict/common/CONTRACT.md` — shared vs game-specific boundary rules
- **Step 2.6**: `src/rts_predict/common/__init__.py`, `src/rts_predict/aoe2/__init__.py` — placeholder modules
- **Step 2.7**: `thesis/chapters/REVIEW_QUEUE.md` — Pass 1 → Pass 2 thesis handoff tracker
- **Step 2.7**: `.claude/chat-handoff.md` — Claude Code → Claude Chat handoff protocol

### Changed
- **Step 1**: Moved Python package `src/sc2ml/` → `src/rts_predict/sc2/` via `git mv` (history preserved)
- **Step 1**: Moved `src/aoe2/` → `src/rts_predict/aoe2/` via `git mv`
- **Step 1**: Created `src/rts_predict/__init__.py` (namespace package docstring; `__version__` lives in `pyproject.toml` only per step 9 fixup)
- **Step 1**: Created `src/rts_predict/common/` placeholder directory
- **Step 2**: Moved SC2 phase artifacts (`reports/00_*`, `reports/01_*`, `sanity_validation.md`, `archive/`) → `src/rts_predict/sc2/reports/` via `git mv`
- **Step 2**: Renamed `SC2ML_THESIS_ROADMAP.md` → `SC2_THESIS_ROADMAP.md` during move
- **Step 2**: `reports/` now contains only cross-cutting `research_log.md`
- **Step 3**: Gitignored runtime artifacts (model `.joblib`/`.pt` files, logs, manifest) manually migrated from root `models/`, `logs/` → `src/rts_predict/sc2/models/`, `src/rts_predict/sc2/logs/`
- **Step 4**: Centralized `GAME_DIR`, `ROOT_DIR`, `REPORTS_DIR` in `config.py`; removed duplicate `REPORTS_DIR` definitions from `audit.py` and `exploration.py`
- **Step 5**: Renamed all `sc2ml` imports to `rts_predict.sc2` across all Python source and test files
- **Step 6**: `pyproject.toml` — package renamed to `rts_predict`, CLI entry point renamed from `sc2ml` to `sc2`, coverage source updated to `src/rts_predict`, version bumped to `0.14.0`
- **Step 7**: `.gitignore` — artifact patterns updated to game-scoped `src/rts_predict/*/` wildcards
- **Step 8**: All `.claude/*.md` documentation — paths, commands, and references updated to `rts_predict` namespace
- **Step 9**: `CLAUDE.md` — major rewrite; all paths, commands, layout, and progress tracking updated
- **Step 10**: `README.md` — commands, roadmap reference, `ARCHITECTURE.md` mention
- **Step 11**: `CHANGELOG.md` — this entry
- **Step 12**: `reports/research_log.md` — reorganization entry, `[SC2]` tags, path updates
- **Step 13**: `thesis/THESIS_STRUCTURE.md` — `SC2ML` → `SC2`, `reports/` path references updated
- **Step 14**: Removed empty legacy root directories `src/sc2ml/` and `src/aoe2/` (emptied by `git mv` in Step 1)
- **Step 15**: `poetry.lock` regenerated after package rename; `poetry install` verified clean install
- **Step 16**: `ARCHITECTURE.md` — new repo-root document describing package layout, game contract, version management, and thesis writing workflow
- **Step 17**: `test_ingestion.py` — replaced backslash line continuation in `with` statements with parenthesized form

## [0.13.3] — 2026-04-04 (PR: pending, chore/rename-repo-rts-outcome-prediction)

### Changed
- Renamed repository from `sc2-ml` to `rts-outcome-prediction` for game-agnostic naming

## [0.13.2] — 2026-04-04 (PR: pending, chore/remove-pre-roadmap-legacy-code)

### Removed
- Deleted `src/sc2ml/features/`, `src/sc2ml/gnn/`, `src/sc2ml/models/`, `src/sc2ml/analysis/` — pre-roadmap feature engineering, GNN, classical ML, and analysis modules (recoverable via git history; tagged `pre-roadmap-cleanup`)
- Deleted `tests/integration/` — integration tests for the removed modules
- Deleted `src/sc2ml/data/cv.py`, `src/sc2ml/validation.py`, and their associated test/helper files
- Deleted stale `src/sc2ml/logs/sc2_pipeline.log` and `processing_manifest.json`

### Changed
- `src/sc2ml/cli.py`: stripped to Phase 0–1 subcommands only (`init`, `audit`, `explore`); removed `run`, `ablation`, `tune`, `evaluate`, `sanity` subcommands and all associated pipeline functions
- `src/sc2ml/data/processing.py`: removed `create_temporal_split`, `validate_temporal_split`, `validate_data_split_sql` and their SQL constants
- `src/sc2ml/data/ingestion.py`: removed deprecated `slim_down_sc2_with_manifest`
- `src/sc2ml/config.py`: removed orphaned constants (`MANIFEST_PATH`, `TRAIN_RATIO`, `VAL_RATIO`, `TEST_RATIO`, `VETERAN_MIN_GAMES`, `PATCH_MIN_MATCHES`, `EXPANDING_CV_N_SPLITS`, `EXPANDING_CV_MIN_TRAIN_FRAC`)

## [0.13.1] — 2026-04-04 (PR: pending, chore/housekeeping-workflow-and-roadmap)

### Changed
- **Workflow guard**: skip pytest/ruff/mypy on commits with no `.py` files staged
- **mypy scope**: broadened from `src/sc2ml/` to `src/` to cover future packages
- **Roadmap Phase 0**: restored full plan content (context, known issues, steps 0.1–0.9, artifacts, gate) above the "Status: complete" line
- **Roadmap Phase 1**: expanded context paragraph (references Phase 0 findings, adds `game_events_raw` and `match_player_map` as inputs); step 1.1 split into sub-sections A and B

### Added
- `src/aoe2/.gitkeep` — placeholder directory reserves the package slot for future AoE2 integration

## [0.13.0] — 2026-04-04 (PR: pending, feature/phase-1-corpus-inventory)

### Added
- **Phase 1 corpus exploration** (`src/sc2ml/data/exploration.py`): 7-step exploration
  pipeline (Steps 1.1–1.7) producing 16 report artifacts — corpus summary, parse quality,
  duration distribution with plots, APM/MMR audit, patch landscape, event type inventory,
  and PlayerStats sampling regularity check
- **Exploration tests** (`src/sc2ml/data/tests/test_exploration.py`): 23 tests with
  synthetic DuckDB fixtures covering all steps and orchestrator (98% coverage)
- **CLI `explore` subcommand**: `sc2ml explore [--steps 1.1 1.3]` for selective step execution
- **tabulate dependency**: Required for DataFrame-to-markdown in report generation

### Changed

### Fixed

### Removed

## [0.12.0] — 2026-04-03 (PR: pending, docs/thesis-infrastructure-invariants-v2)

### Added
- **Thesis directory structure** (`thesis/`): chapter skeletons (01–07), `THESIS_STRUCTURE.md` (section-to-phase mapping, ~300 lines), `WRITING_STATUS.md` (per-section status tracker), `references.bib` (~20 BibTeX entries), `figures/` and `tables/` directories
- **Thesis writing workflow** (`.claude/thesis-writing.md`): two-pass review process, critical review checklist (6 mandatory checks), inline flag system (`[REVIEW:]`, `[NEEDS CITATION]`, etc.), section-to-phase drafting schedule
- **Category F — Thesis writing** in `CLAUDE.md`: new work category with planning template, trigger words, progress tracking integration
- **Scientific invariants 7–10** (`.claude/scientific-invariants.md`): data field status with empirical backing (APM 97.5% usable 2017+, MMR 83.6% unusable), magic number ban, cross-game comparability protocol
- **SC2 game loop timing reference** (`reports/SC2ML_THESIS_ROADMAP.md`): 22.4 loops/sec derivation with landmarks table, citations (Blizzard s2client-proto, Vinyals et al. 2017)
- **Data utility script** (`src/sc2ml/data/sc2_nested_zip_remove.sh`): removes nested `_data.zip` files from SC2 replay directories
- **Reports archive stub** (`reports/archive/research_log.md`)

### Changed
- **Scientific invariants restructured** (`.claude/scientific-invariants.md`): reorganized from 6 to 10 numbered invariants with thematic sections (identity, temporal, symmetric, domain, data fields, reproducibility, cross-game)
- **Roadmap v2** (`reports/SC2ML_THESIS_ROADMAP.md`): Phase 0 marked complete with empirical gate results (22,390 replays, 62M tracker rows, 609M game event rows, 188 maps); Phase 1 expanded with empirical duration distribution emphasis and new steps (1.5 version landscape, 1.6 tracker event inventory); all phases now include explicit thesis section mapping
- **CLAUDE.md**: added Category F workflow, thesis writing trigger words, post-phase-gate thesis check in progress tracking, thesis writing references in project status

## [0.11.0] — 2026-04-03 (PR: pending, docs/invariant-6-research-log)

### Added
- **Scientific invariant #6** (`.claude/scientific-invariants.md`): all analytical results must be reported alongside the literal SQL/Python code that produced them
- Phase 0 audit artifacts (Steps 0.1–0.9): all 8 report files in `reports/00_*`

### Changed
- **Research log Phase 0 entry rewritten** (`reports/research_log.md`): every finding now includes the exact SQL query or Python code per invariant #6; APM/MMR analysis expanded with per-year and per-league breakdown tables; map count corrected from 189 → 188
- `ingestion.py` glob patterns unified to `*.SC2Replay.json` (was `*/data/*.SC2Replay.json` in `audit_raw_data_availability`, `slim_down_sc2_with_manifest`, `_collect_pending_files`)

## [0.10.0] — 2026-04-03 (PR: pending, feat/phase-0-ingestion-audit)

### Added
- **Phase 0 ingestion audit module** (`src/sc2ml/data/audit.py`): 9 audit functions mapping to roadmap steps 0.1–0.9 — source file audit, tournament name validation, replay_id spec, Path A smoke test (in-memory DuckDB), full Path A ingestion, Path B extraction, Path A↔B join validation, map translation coverage
- **`raw_enriched` view** in `processing.py`: adds `tournament_dir` and `replay_id` computed columns to `raw` table via `CREATE OR REPLACE VIEW`; `flat_players` now reads from `raw_enriched` instead of `raw`
- **`create_raw_enriched_view()`** function in `processing.py`, called during `init_database` pipeline
- **`audit` CLI subcommand**: `poetry run python -m sc2ml.cli audit [--steps 0.1 0.2 ...]` runs Phase 0 audit steps against real data
- **`run_phase_0_audit()` orchestrator** accepting optional step list for selective execution
- 14 new tests: `test_audit.py` (10 tests covering all public audit functions), `TestCreateRawEnrichedView` in `test_processing.py` (4 tests)

### Changed
- `_FLAT_PLAYERS_VIEW_QUERY` now reads from `raw_enriched` instead of `raw`; `tournament_name` derived from `tournament_dir` column instead of inline `split_part()`
- `init_database()` in `cli.py` now calls `create_raw_enriched_view(con)` between `move_data_to_duck_db` and `load_map_translations`
- `conftest.py` synthetic filenames updated to use 32-char hex prefixes (`SYNTHETIC_REPLAY_IDS`) matching real replay naming; APM/MMR set to 0 (dead fields)
- Integration test fixtures and sanity validation fixtures updated to call `create_raw_enriched_view` before `create_ml_views`

## [0.9.0] — 2026-04-03 (PR: pending, refactor/data-schemas-sql-extraction)

### Changed
- **`schemas.py` extracted** (`src/sc2ml/data/schemas.py`): `PLAYER_STATS_FIELD_MAP`, `TRACKER_SCHEMA`, `GAME_EVENT_SCHEMA`, `METADATA_SCHEMA` moved out of `ingestion.py`; re-exported from `ingestion` for backward compatibility
- **SQL queries extracted in `processing.py`**: all inline SQL moved to module-level `_QUERY` constants (`FLAT_PLAYERS_VIEW_QUERY`, `MATCHES_FLAT_VIEW_QUERY`, `MATCHES_WITH_SPLIT_QUERY`, `MATCHES_WITHOUT_SPLIT_QUERY`, `YEAR_DISTRIBUTION_QUERY`, `CHRONOLOGICAL_SPLIT_QUERY`, `SERIES_ASSIGNMENT_QUERY`, `SERIES_OTHER_PERSPECTIVE_QUERY`, `TOURNAMENT_GROUPING_QUERY`, `MATCH_SPLIT_CREATE_QUERY`, `SPLIT_STATS_QUERY`, `SPLIT_BOUNDARIES_QUERY`, `TOURNAMENT_CONTAINMENT_QUERY`, `SERIES_INTEGRITY_QUERY`, `YEAR_DIST_PER_SPLIT_QUERY`); parameterized f-string in `get_matches_dataframe` converted to `?` binding
- **SQL queries extracted in `ingestion.py`**: `DUCKDB_SET_QUERIES`, `RAW_TABLE_CREATE_QUERY`, `TRACKER_EVENTS_TABLE_QUERY`, `PLAYER_STATS_VIEW_QUERY`, `GAME_EVENTS_TABLE_QUERY`, `MATCH_PLAYER_MAP_TABLE_QUERY` extracted to module-level constants; `PLAYER_STATS_VIEW_QUERY` built once at module level via `_build_player_stats_view_query()`
- **`slim_down_sc2_with_manifest` deprecated** in `ingestion.py` and `samples/process_sample.py`: `DeprecationWarning` added, docstrings updated with `.. deprecated::` directive pointing to `run_in_game_extraction()`
- **`cv.py` docstrings** converted from NumPy style to Google style per coding standards
- **`data/__init__.py`**: `schemas` added to submodules docstring

## [0.8.0] — 2026-04-03 (PR: pending, chore/consolidate-base)

### Added
- **Evaluation infrastructure** (`models/evaluation.py`): `compute_metrics` (accuracy, AUC-ROC, Brier, log loss), `bootstrap_ci` (95% CI via 1000 bootstrap iterations), `calibration_curve_data`, `mcnemar_test` (exact binomial + chi-squared), `delong_test` (fast DeLong AUC comparison), `evaluate_model` (full eval with CIs + per-matchup + veterans), `compare_models` (pairwise statistical tests), `run_permutation_importance`
- **Baseline classifiers** (`models/baselines.py`): `MajorityClassBaseline`, `EloOnlyBaseline`, `EloLRBaseline` — all with `predict_proba` for probability-based metrics
- **Feature ablation runner** (`evaluation.py:run_feature_ablation`): trains LightGBM per group subset (A, A+B, ..., A+B+C+D+E), reports marginal lift per step
- **Expanding-window temporal CV** (`data/cv.py`): `ExpandingWindowCV` with series-aware boundary snapping, sklearn `BaseCrossValidator` compatible
- **Optuna tuning** (`models/tuning.py`): `tune_lgbm_optuna`, `tune_xgb_optuna` (Bayesian optimization, 200 trials), `tune_lr_grid` (grid search over C + penalty)
- **SHAP analysis** (`analysis/shap_analysis.py`): `compute_shap_values` (TreeExplainer/LinearExplainer), `plot_shap_beeswarm`, `plot_shap_per_matchup` (6 matchup types), `shap_feature_importance_table`
- **Error analysis** (`analysis/error_analysis.py`): `classify_error_subgroups` (mirrors, upsets, close Elo, short/long games), `error_subgroup_report`
- **Patch drift experiment** (`evaluation.py:run_patch_drift_experiment`): train on old patches, test on new, per-patch accuracy breakdown
- **Reporting** (`models/reporting.py`): `ExperimentReport` with `.to_json()` and `.to_markdown()` for thesis-ready reports
- **CLI subcommands**: `sc2ml ablation`, `sc2ml tune`, `sc2ml evaluate`
- `matchup_type` column preserved through feature engineering for per-matchup analysis
- `p1_race`/`p2_race` added to `_METADATA_COLUMNS` for safe ablation without Group C
- Config constants: `BOOTSTRAP_N_ITER`, `BOOTSTRAP_CI_LEVEL`, `CALIBRATION_N_BINS`, `RESULTS_DIR`, `EXPANDING_CV_N_SPLITS`, `EXPANDING_CV_MIN_TRAIN_FRAC`, `OPTUNA_N_TRIALS_LGBM`, `OPTUNA_N_TRIALS_XGB`, `LR_GRID_C`, `LR_GRID_PENALTY`
- `@pytest.mark.slow` marker registered in `pyproject.toml`
- `optuna` and `shap` dependencies
- 75 new tests: `test_evaluation.py` (22), `test_baselines.py` (18), `test_cv.py` (13), `test_ablation.py` (6), `test_analysis/test_error_analysis.py` (9), `test_analysis/test_shap_analysis.py` (7)
- **Phase 0 sanity validation** (`validation.py`): 28 automated checks across 5 sections — DuckDB view sanity (§3.1), temporal split integrity (§3.2), feature distribution checks (§3.3), leakage & baseline smoke tests (§3.4), known issues verification (§3.5)
- `SanityCheck`/`SanityReport` result containers with `.summary` property
- `run_full_sanity()` aggregator running all Phase 0 checks
- `sc2ml sanity` CLI subcommand for real-data validation (writes `reports/sanity_validation.md`)
- `@pytest.mark.sanity` marker registered in `pyproject.toml`
- 29 new tests in `test_sanity_validation.py` (25 passing, 4 skipped on synthetic data)
- **Scientific invariants** (`.claude/scientific-invariants.md`): thesis methodology constraints read-before-any-work
- **Thesis roadmap** (`reports/SC2ML_THESIS_ROADMAP.md`): authoritative phase-by-phase execution plan
- **Co-located tests**: all package tests moved next to source (`src/sc2ml/*/tests/`)
- `tests/integration/` directory for cross-package integration tests
- Data samples: `SC2EGSet_datasheet.pdf`, `README.md`, shell extraction scripts

### Changed
- `train_and_evaluate_models()` now returns `(dict[str, Pipeline], list[ModelResults])` instead of just pipelines
- `classical.py` refactored: model definitions extracted to `_build_model_pipelines()`, evaluation delegated to `evaluation.py`
- `.claude/` configuration files rewritten: `project-architecture.md`, `ml-protocol.md`, `testing-standards.md`, `git-workflow.md`, `coding-standards.md`
- `CLAUDE.md` restructured with scientific invariants mandate, progress tracking, end-of-session checklist
- `README.md` rewritten with project overview and documentation index

### Removed
- Duplicate root-level tests (`tests/test_*.py`) — replaced by co-located versions under `src/`
- Superseded reports: `reports/ROADMAP.md`, `reports/methodology.md`, `reports/test_plan.md`
- Root-level test helpers (`tests/helpers_*.py`)

### Known Issues
- 16 test errors + 1 failure in `test_processing.py` temporal split tests — fixture missing `flat_players` table; will be rewritten in Phase 0
- 1 GNN prediction quality test failure — expected, GNN is deprioritized
- 41 mypy errors — pre-existing `fetchone()` return type issues in DuckDB code

## [0.7.0] — 2026-04-03 (docs/data-pipeline-integrity)

### Documentation Refactoring
- **Unified documentation structure**: eliminated redundancy across 12+ markdown files. One authoritative source per topic.
- Moved `src/sc2ml/methodology.md` → `reports/methodology.md` (thesis specification doesn't belong in Python source tree)
- Moved `test_plan.md` → `reports/test_plan.md` (planning doc, not a root-level file)
- Archived `src/sc2ml/data/plan.md` → `reports/archive/data_analysis_notes.md` (superseded by methodology.md)
- Deleted `src/sc2ml/action_plan.md` — execution checklist folded into ROADMAP.md
- **ROADMAP.md** is now the single progress tracker: added Phase 0→1 execution checklist with exact CLI commands, §3.6 test coverage tracking, fixed cross-references
- **`.claude/project-architecture.md`** rewritten: fixed 6+ factual errors (deleted modules referenced as current, wrong feature count 45→66, outdated tuning description, GNN not marked as deprioritized)
- **CLAUDE.md** updated: added mandatory "Progress Tracking" section, added `reports/methodology.md`, `reports/ROADMAP.md`, `reports/test_plan.md` to guidelines table, added git-workflow reference to end-of-session checklist
- **README.md** replaced: was empty, now has project overview with documentation index

### Critical Bug Fixes (discovered during Phase 0 sanity validation)

#### Elo System — All Ratings Were 1500.0 (Complete Failure)
- **Root cause:** `group_a_elo.py` used a two-pass algorithm where Phase 1 recorded every player's Elo *before* Phase 2 updated anything. Result: all pre-match Elo values were the initialization constant (1500.0), producing zero variance and a useless Elo baseline (48.8% accuracy — worse than random).
- **Fix:** Merged into a single chronological pass — snapshot pre-match Elo, then update immediately, processing each unique match_id once via dedup guard. Elo now actually reflects player skill trajectories.
- **Impact:** All Elo-derived features (`p1_pre_match_elo`, `p2_pre_match_elo`, `elo_diff`, `expected_win_prob`) were non-functional across all prior pipeline runs. Historical run results in `reports/archive/` were achieved *without any Elo signal*.

#### H2H Feature Self-Leakage
- **Root cause:** `_compute_h2h()` in `group_d_form.py` used `expanding_sum` grouped by a canonical player pair key. In the dual-perspective layout (2 rows per match), the second row's expanding window included the first row's target value — which is the same match's result from the other perspective.
- **Fix:** H2H features now computed on deduplicated matches (one row per match_id) using a canonical-perspective target, then mapped back to both rows. Canonical ordering via `p1_name < p2_name`.
- **Impact:** `h2h_p1_winrate_smooth` had 0.62 correlation with target (detected by sanity check §3.4). This would have inflated model accuracy via leakage.

#### Temporal Split — Tournament Boundary Violations
- **Root cause:** `create_temporal_split()` split at series-level boundaries, but multiple tournaments can overlap chronologically (e.g., IEM Katowice 2024 qualifiers ran Dec 2023–Feb 2024, overlapping with ESL Winter Finals Dec 15–18). Result: 3 tournaments were split across train/val or val/test, creating temporal leakage and violating the principle that tournament context should not leak between splits.
- **Fix:** Split now operates at **tournament-level boundaries**. All matches from the same tournament (identified by source directory name during ingestion) are guaranteed to be in the same split. Series containment follows automatically since all series are within a tournament.
- **Impact:** Train/Val and Val/Test boundaries now have clean gaps (23 days and 3.5 months respectively). Previously had overlaps of 10 minutes and 2 months.
- **Observations from real data:** 66 tournaments spanning 2016–2024, 22,390 replays ingested (up from 22,103). Final split: train=17,991 (80.4%), val=3,520 (15.7%), test=858 (3.8%).

#### Data Quality — Team Games and Brood War Replays
- **Root cause:** `flat_players` view included non-1v1 matches (team games with 4-9 players) and Brood War exhibition replays (races: BWPr, BWTe, BWZe). These produced matches with !=2 rows, corrupting the dual-perspective assumption.
- **Fix:** Added two filters to `flat_players` view: (1) exclude BW races (`race NOT LIKE 'BW%'`), (2) restrict to 1v1 matches via subquery (`HAVING COUNT(*) = 2` on Win/Loss players per match). Affected: 13 team game replays (HSC XVI, TSL5, EWC) + 1 BW exhibition match.

### Other Changes
- Removed `series_length_so_far` feature — perfectly correlated with `series_game_number` (literally `game_number - 1`), provided zero additional information
- `validate_temporal_split()` now checks tournament containment in addition to series containment
- LightGBM sanity checks run in subprocess isolation when PyTorch is loaded (avoids dual-OpenMP segfault on macOS)
- `check_elo_baseline` threshold relaxed for small synthetic datasets (10 test rows with random data can't reliably beat 50%)
- Synthetic test fixtures updated to use chronological tournament assignment (20 tournaments, 5 matches each) instead of random assignment, required by tournament-level splitting

### Phase 0 Sanity Results (first run on real data — 16/25 passed)
Initial sanity run identified all the bugs above. Key observations:
- **22,390 replays** ingested across 66 tournaments (2016-2024)
- **1,044 unique players** in the dataset
- Target balance: ~50% (confirmed by dual-perspective layout)
- Historical features have no NaN (cold-start handling works)
- No series spans multiple splits
- Race dummies are int (not bool) — previously flagged issue was already fixed
- Expanding-window aggregates correctly exclude current match
- Feature count: 75 columns from 5 groups (slightly above the 66 expected — needs audit)
- **Next session:** proper source data analysis before running experiments

## [0.6.0] — 2026-04-02 (PR #7: test/gnn-diagnostics)

### Added
- **GNN diagnostic test suite** (`tests/test_gnn_diagnostics.py`): 14 tests across 6 groups confirming GATv2 majority-class collapse root causes — no `pos_weight` in BCE loss, edge feature scaler leak (fit on full dataset), hard 0.5 threshold
- `@pytest.mark.gnn` marker registered in `pyproject.toml` (skip with `-m "not gnn"`)
- `setup_logging()` now called in `run_pipeline()` for reliable file logging when invoked outside `main()`

## [0.5.0] — 2026-04-02 (PR #6: fix/pipeline-coherence)

### Added
- `init_database()` function and CLI `init` subcommand for one-step database setup from raw replays
- CLI argparse with `init [--force]` and `run` subcommands (backward-compatible: bare invocation still runs pipeline)
- `game_version` column in `flat_players` and `matches_flat` SQL views (from `metadata.gameVersion`)
- 12 integration smoke tests (`tests/test_integration.py`) verifying the full chain: ingestion → processing → features → model training
- Race normalization and game version parsing tests in data and feature test suites

### Fixed
- **Race name mismatch**: SQL view now normalizes abbreviated race names (`Terr`→`Terran`, `Prot`→`Protoss`) so one-hot columns match GNN visualizer and test expectations
- **Validation set discarded**: `train_and_evaluate_models()` now accepts optional `X_val`/`y_val`; XGBoost and LightGBM use it for early stopping; val accuracy reported for all models
- **Patch version always zero on real data**: Group E now uses `game_version` (`"3.1.1.39948"`) for `patch_version_numeric` instead of plain `data_build` (`"39948"`)
- **Compat fallback crash**: `cli.py` fallback path now drops string columns via `select_dtypes(include='number')` before passing to sklearn
- **t-SNE `n_iter` deprecation**: Updated to `max_iter` for scikit-learn 1.6+

### Changed
- `cli.py` refactored: pipeline logic extracted to `run_pipeline()`, `init_database()` added, imports now include ingestion/processing functions

## [0.4.0] — 2026-04-01 (PR #5: refactor/feature-groups-ablation)

### Added
- **Feature groups A–E** implementing methodology Section 3.1 for incremental ablation:
  - Group A (`group_a_elo.py`): Dynamic K-factor Elo ratings (refactored from `elo.py`)
  - Group B (`group_b_historical.py`): Historical aggregates + new variance features (`hist_std_apm`, `hist_std_sq`)
  - Group C (`group_c_matchup.py`): Race encoding, spawn distance, map area + new map×race interaction winrate
  - Group D (`group_d_form.py`): **New** — win/loss streaks, EMA stats, activity windows (7d/30d), head-to-head records
  - Group E (`group_e_context.py`): **New** — patch version numeric, tournament match position, series game number
- `build_features(df, groups=FeatureGroup.C)` API for composable group selection and ablation
- `split_for_ml()` consuming the series-aware 80/15/5 split from `data/processing.py`
- `FeatureGroup` enum and `get_groups()` for ablation protocol (methodology Section 7.1)
- Feature group registry (`registry.py`) with lazy-loaded compute functions
- Backward-compatible wrappers in `compat.py` (`perform_feature_engineering`, `temporal_train_test_split`)
- Config constants: `EMA_ALPHA`, `ACTIVITY_WINDOW_SHORT`, `ACTIVITY_WINDOW_LONG`, `H2H_BAYESIAN_C`
- 73 new tests in `tests/test_features/` covering all groups, common primitives, registry, ablation, and compat
- `tests/helpers.py`: `make_series_df()` for Group E testing; deterministic win streaks for Player_0
- `tests/helpers_classical.py`: isolated worker for classical model reproducibility (no torch import)
- `pytest-cov` and `coverage` dev dependencies
- **Path B in-game event extraction pipeline** in `ingestion.py`: `audit_raw_data_availability()`, `extract_raw_events_from_file()`, `save_raw_events_to_parquet()`, `run_in_game_extraction()`, DuckDB loaders with `player_stats` view and `match_player_map` table
- `PLAYER_STATS_FIELD_MAP` — 39 `scoreValue*` → snake_case field mappings for tracker events
- Temporal split management in `processing.py`: `assign_series_ids()`, `create_temporal_split()`, `validate_temporal_split()`
- `player_id` column added to `flat_players` and `matches_flat` SQL views
- `get_matches_dataframe()` now accepts optional `split` parameter for filtered queries
- Config constants: `IN_GAME_DB_PATH`, `IN_GAME_PARQUET_DIR`, `IN_GAME_MANIFEST_PATH`, `IN_GAME_WORKERS`, `IN_GAME_BATCH_SIZE`, `TRAIN_RATIO`, `VAL_RATIO`, `TEST_RATIO`, `SERIES_GAP_SECONDS`
- `pyarrow` dependency for Parquet-based event storage
- 42 new tests in `src/sc2ml/data/tests/` covering ingestion and processing pipelines
- Data pipeline documentation: `src/sc2ml/data/README.md`, methodology notes

### Changed
- `cli.py` now uses `build_features()` + `split_for_ml()` instead of monolithic `perform_feature_engineering()` + `temporal_train_test_split()`
- `temporal_train_test_split()` now emits `DeprecationWarning` (use `split_for_ml()` instead)
- Test imports updated: `from sc2ml.features import ...` replaces `from sc2ml.features.engineering import ...`
- `slim_down_sc2_with_manifest()` now defaults to `dry_run=True` for safety

### Fixed
- **Dual-OpenMP segfault on macOS (LightGBM + PyTorch)**: LightGBM ships Homebrew `libomp.dylib`, PyTorch bundles its own `libomp.dylib`. Loading both in the same process causes a segfault at shutdown during OpenMP thread pool teardown. Fix: classical model reproducibility tests now run in a `multiprocessing.spawn` child process via `helpers_classical.py` (which never imports torch), fully isolating the two runtimes. GNN test adds `gc.collect()` + `torch.mps.empty_cache()` cleanup per `test_mps.py` pattern.

### Removed
- `features/elo.py` and `features/engineering.py` (replaced by group modules + compat wrappers)

## [0.3.0] — 2026-03-31 (PR #4: refactor/break-down-claude-md)

### Added
- `.claude/` sub-files: `python-workflow.md`, `testing-standards.md`, `coding-standards.md`, `git-workflow.md`, `ml-protocol.md`, `project-architecture.md`

## [0.2.0] — 2026-03-30 (PR #3: refactor/package-structure)

### Changed
- **Reorganized into `src/sc2ml/` package** with four subpackages: `data/`, `features/`, `models/`, `gnn/` — proper Python src layout replacing flat root-level modules
- Renamed modules to avoid namespace redundancy (e.g. `data_ingestion.py` → `sc2ml.data.ingestion`)
- Updated `pyproject.toml` to src layout (`packages = [{include = "sc2ml", from = "src"}]`)
- Replaced hardcoded `ROOT_PROJECTS_DIR` path with `Path(__file__)` derivation in `config.py`
- Moved logging setup from module-level side effect to `setup_logging()` function in `cli.py`
- Fixed duplicate `perform_feature_engineering()` call in pipeline orchestrator
- Replaced string type annotations with proper `TYPE_CHECKING` imports in GNN modules
- Archived legacy run reports (`01_run.md`–`09_run.md`) to `reports/archive/`
- Translated all Polish comments and log strings to English across all 13 Python modules
- Added type hints to all function signatures (parameters and return types) in all modules
- Extracted 60+ magic numbers into named constants in `config.py`

### Added
- `src/sc2ml/__init__.py` with package version `0.2.0`
- `[project.scripts]` entry point: `sc2ml = "sc2ml.cli:main"`
- `tests/conftest.py` for pytest configuration
- `tests/helpers.py` for shared test utilities (replaces `tests/fixtures.py`)
- `[tool.pytest.ini_options]` in `pyproject.toml`
- `pyproject.toml` with Poetry dependency management
- `config.py` with all centralized constants
- `tests/` directory with test suite (data validation, feature engineering, graph construction, model reproducibility)
- CLAUDE.md, CHANGELOG.md, and research log

### Removed
- Root-level `__init__.py` (incorrect — root is not a package)
- `tests/fixtures.py` (absorbed into `tests/helpers.py`)
- `sys.path.insert()` hack from all test files
- Unused imports in `cli.py` (data ingestion functions not called in current pipeline)
- Dead commented-out legacy `main()` function block (~100 lines)

### Fixed
- Test fixture now drops non-numeric columns (e.g. `data_build`) before passing to sklearn
- Ruff import sorting and unused import warnings resolved across all modules

## [0.1.0] — 2026-03-30 (Baseline)

### Added
- SC2 data ingestion pipeline with manifest tracking (`data_ingestion.py`)
- DuckDB-based data processing with SQL views (`data_processing.py`)
- Feature engineering with 45+ features and Bayesian smoothing (`ml_pipeline.py`)
- Custom ELO rating system with dynamic K-factor (`elo_system.py`)
- Classical ML baselines: Logistic Regression, Random Forest, Gradient Boosting, XGBoost, LightGBM (`model_training.py`)
- Random Forest hyperparameter tuning via RandomizedSearchCV (`hyperparameter_tuning.py`)
- GATv2-based Graph Neural Network for edge classification (`gnn_model.py`, `gnn_pipeline.py`, `gnn_trainer.py`)
- Node2Vec embedding pipeline (`node2vec_embedder.py`)
- t-SNE visualization of GNN embeddings (`gnn_visualizer.py`)
- Pipeline orchestrator with configurable model selection (`main.py`)
- Execution reports documenting 9 pipeline runs (`reports/`)
