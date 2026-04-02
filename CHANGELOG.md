# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Conventional Commits](https://www.conventionalcommits.org/).

Each feature branch merges as a semver bump. The `[Unreleased]` section
tracks only changes on the current working branch that have not yet been
merged to `master`.

## [Unreleased]

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

### Changed
- `train_and_evaluate_models()` now returns `(dict[str, Pipeline], list[ModelResults])` instead of just pipelines
- `classical.py` refactored: model definitions extracted to `_build_model_pipelines()`, evaluation delegated to `evaluation.py`

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
