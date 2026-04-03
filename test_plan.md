# Test Coverage Augmentation Plan: 53% → 100%

## Context

Current test coverage is 53% (1050 of 2247 statements missed). The thesis project needs high coverage to validate the data pipeline, feature engineering, and model evaluation code before running real experiments (Phase 0 blocking). The main gap is that orchestration modules (CLI, classical models, tuning, reporting) and several analysis modules have 0% coverage.

**Key constraint:** LightGBM and PyTorch load conflicting OpenMP runtimes on macOS. Tests using LightGBM must run in subprocess isolation (`multiprocessing.get_context("spawn")`) when torch has been imported in the same pytest session. This pattern is already established in `tests/helpers_classical.py`.

---

## Phase 1 — Trivial gaps in existing test files (~10 tests)

These are 1-3 test additions to files that already have fixtures.

### 1.1 `features/__init__.py` (96% → 100%, line 96)
- **File:** `tests/test_features/test_build_features.py`
- **Add:** `test_build_features_casts_bool_to_int` — verify no bool-dtype columns in output

### 1.2 `features/group_e_context.py` (88% → 100%, lines 53-56, 64)
- **File:** `tests/test_features/test_group_e.py`
- **Add:** `test_context_uses_game_version_column` — DataFrame with `game_version` but no `data_build`, verify `patch_version_numeric` uses game_version
- **Add:** `test_context_no_tournament_name_fallback` — DataFrame without `tournament_name`, verify `tournament_match_position = 0`

### 1.3 `data/cv.py` (98% → 100%, line 118)
- **File:** `tests/test_cv.py`
- **Add:** `test_expanding_window_skips_degenerate_fold` — high `min_train_frac` with few splits → fewer folds yielded than `n_splits`

### 1.4 `analysis/error_analysis.py` (98% → 100%, line 161)
- **File:** `tests/test_analysis/test_error_analysis.py`
- **Add:** `test_error_subgroup_report_single_class_auc_nan` — subgroup where all y_true are same class → `auc_roc` is NaN

### 1.5 `gnn/trainer.py` (96% → 100%, lines 108-109, 143)
- **File:** `tests/test_gnn_diagnostics.py` or new `tests/test_gnn_trainer.py`
- **Add:** `test_early_stopping_triggers` — mock or use tiny graph with `GNN_PATIENCE=1` so training stops early
- **Add:** `test_empty_veterans_mask_warning` — `veteran_mask` all-False for test edges → warning logged

---

## Phase 2 — New test files for 0%-coverage pure modules (~25 tests)

### 2.1 `models/reporting.py` (0% → 100%)
- **New file:** `tests/test_models/__init__.py` + `tests/test_models/test_reporting.py`
- **Fixtures:** Mock `ModelResults` instances (with numpy arrays for y_true/y_pred/y_prob, per_matchup dict, veterans dict), mock comparison DataFrame, mock ablation results list, mock patch drift dict
- **No subprocess needed**
- **Tests (~14):**
  - `test_to_json_creates_file` — verify JSON file written at path
  - `test_to_json_default_path` — verify RESULTS_DIR used
  - `test_to_json_model_results_structure` — "models" key has name/accuracy/auc_roc
  - `test_to_json_comparisons_serialized` — comparisons DataFrame → JSON
  - `test_to_json_ablation_results` — "ablation" key excludes model_result
  - `test_to_json_patch_drift_with_model_results` — ModelResults in patch_drift serialized
  - `test_to_json_patch_drift_with_dict` — plain dict preserved
  - `test_to_markdown_creates_file` — verify .md file written
  - `test_to_markdown_model_comparison_table` — headers present
  - `test_to_markdown_statistical_comparisons` — pairwise rows
  - `test_to_markdown_ablation_section` — ablation table rendered
  - `test_to_markdown_per_matchup_breakdown` — matchup table present
  - `test_to_markdown_error_analysis` — error subgroup rows
  - `test_to_markdown_patch_drift` — patch drift block

### 2.2 `gnn/embedder.py` (0% → 100%)
- **New file:** `tests/test_gnn_embedder.py`
- **Fixtures:** Minimal PyG Data (5 nodes, ~10 edges), player_to_id dict
- **Mark:** `@pytest.mark.gnn`
- **Tests (~7):**
  - `test_train_returns_dict` — returns dict
  - `test_embeddings_correct_dim` — values have NODE2VEC_EMBEDDING_DIM length
  - `test_all_players_present` — all players in output
  - `test_isolated_node_zero_vector` — disconnected node gets zeros
  - `test_append_creates_columns` — p1_emb_0, p2_emb_0 etc.
  - `test_append_preserves_rows` — row count unchanged
  - `test_append_unknown_player_zeros` — missing player gets zero vector

### 2.3 `gnn/visualizer.py` (0% → 100%)
- **New file:** `tests/test_gnn_visualizer.py`
- **Fixtures:** Mock SC2EdgeClassifier (MagicMock with .conv1/.conv2 returning tensors), PyG Data with x/edge_index, features_df with race columns
- **Mark:** `@pytest.mark.gnn`
- **Tests (~4):**
  - `test_visualize_creates_png` — verify PNG at output_path
  - `test_visualize_with_top_player_annotation` — include "serral" in player_to_id
  - `test_visualize_all_races` — one player per race
  - `test_visualize_no_crash_on_empty_race` — race with 0 players

---

## Phase 3 — Augmenting partially-covered modules (~25 tests)

### 3.1 `models/evaluation.py` (58% → ~90%, in-process portions)
- **File:** `tests/test_evaluation.py`
- **Tests (~10):**
  - `test_delong_scalar_covariance` — m=1 positive sample triggers ndim==0 path
  - `test_evaluate_model_1d_prob` — mock model returning 1D predict_proba
  - `test_evaluate_model_bootstrap_ci` — compute_ci=True, verify CI tuples
  - `test_evaluate_model_veterans_metrics` — pass veterans_mask with True values
  - `test_evaluate_model_veterans_empty` — all-False mask → empty dict
  - `test_evaluate_all_models` — 2 fitted models → list + DataFrame
  - `test_evaluate_all_models_comparison_count` — n*(n-1)/2 rows
  - `test_run_permutation_importance` — fitted LR + test data → DataFrame
  - `test_run_permutation_importance_sorted` — descending by mean
  - `test_compare_models_single` — 1 model → empty comparisons

### 3.2 `analysis/shap_analysis.py` (55% → 100%)
- **File:** `tests/test_analysis/test_shap_analysis.py`
- **Tests (~6):**
  - `test_compute_shap_no_subsampling` — max_samples > len(X_test)
  - `test_compute_shap_kernel_explainer_fallback` — Pipeline with unknown classifier type
  - `test_plot_beeswarm_creates_file` — mock shap.Explanation, verify PNG
  - `test_plot_beeswarm_custom_title` — custom title doesn't crash
  - `test_plot_per_matchup_creates_files` — 2 matchup types → 2 PNGs
  - `test_plot_per_matchup_skips_small` — matchup with <10 samples skipped

### 3.3 `validation.py` (73% → 100%, failure paths)
- **File:** `tests/test_sanity_validation.py`
- **New DuckDB fixtures** with deliberately broken data
- **Tests (~8):**
  - `test_check_null_rate_finds_nulls` — NULL match_time rows
  - `test_check_match_time_range_too_early` — year < 2010
  - `test_check_match_time_range_future` — year > 2027
  - `test_check_race_distribution_unexpected` — "Random" race
  - `test_check_duplicate_match_ids_bad` — 3 rows per match_id
  - `test_check_target_balance_skewed` — 90% win rate
  - `test_check_split_ratios_off` — 50/25/25 ratios
  - `test_sanity_report_summary` — verify SanityReport.summary formatting

### 3.4 `data/processing.py` (56% → 100%)
- **File:** `src/sc2ml/data/tests/test_processing.py`
- **Tests (~5):**
  - `test_get_matches_no_split_table_warns` — no match_split table + split arg → warning
  - `test_validate_data_split_sql_runs` — verify no crash on synthetic matches_flat
  - `test_validate_data_split_sql_logs_distribution` — year distribution logged
  - `test_validate_temporal_split_logs_boundaries` — split boundary info logged
  - `test_validate_temporal_split_series_check` — series integrity reported

---

## Phase 4 — Subprocess-isolated LightGBM tests (~15 tests)

### 4.1 `models/classical.py` (0% → 100%)
- **New files:** `tests/test_models/test_classical.py` + `tests/helpers_classical_unit.py`
- **Subprocess worker** in `helpers_classical_unit.py`: creates 50-row synthetic DataFrame, calls `_build_model_pipelines()` and `train_and_evaluate_models()`
- **Tests (~6):**
  - `test_build_pipelines_returns_five` — 5 keys in dict
  - `test_pipeline_step_names` — scaler + classifier in each
  - `test_train_evaluate_returns_tuple` — (dict, list)
  - `test_all_models_valid_accuracy` — 0 ≤ acc ≤ 1
  - `test_with_val_set` — X_val/y_val → early stopping
  - `test_with_matchup_col` — per_matchup populated

### 4.2 `models/tuning.py` (0% → 100%)
- **New files:** `tests/test_models/test_tuning.py` + `tests/helpers_tuning.py`
- **Subprocess worker** in `helpers_tuning.py`: 30-row DataFrame, ExpandingWindowCV(n_splits=2), n_trials=2
- **Tests (~5):**
  - `test_tune_random_forest` — returns fitted estimator
  - `test_tune_lgbm_optuna` — returns Pipeline, n_trials=2
  - `test_tune_xgb_optuna` — returns Pipeline, n_trials=2
  - `test_tune_lr_grid` — returns Pipeline
  - (all via subprocess, mark `@pytest.mark.slow`)

### 4.3 `models/evaluation.py` subprocess portions (→ 100%)
- **New file:** `tests/helpers_evaluation.py`
- **Tests (~3):**
  - `test_run_feature_ablation_subprocess` — 5 ablation steps returned
  - `test_run_patch_drift_subprocess` — old→new and mixed results
  - `test_run_patch_drift_no_column_raises` — ValueError when no patch column

---

## Phase 5 — CLI and ingestion orchestration (~25 tests)

### 5.1 `cli.py` (0% → 100%)
- **New file:** `tests/test_cli.py`
- **Strategy:** Mock all downstream modules with `unittest.mock.patch`
- **No subprocess needed** (all calls mocked)
- **Tests (~18):**
  - `test_setup_logging` — creates handlers
  - `test_init_database_calls_steps` — 6 functions called in order
  - `test_init_database_should_drop` — forwarded correctly
  - `test_main_init` — argparse routes to init_database
  - `test_main_init_force` — --force flag
  - `test_main_run` — routes to run_pipeline
  - `test_main_ablation` — routes to _run_ablation_command
  - `test_main_tune` — routes to _run_tune_command
  - `test_main_tune_custom_trials` — --trials 50
  - `test_main_evaluate` — routes to _run_evaluate_command
  - `test_main_sanity` — routes to _run_sanity_command
  - `test_main_default` — no subcommand → run_pipeline
  - `test_run_pipeline_classic` — MODELS_TO_RUN=["CLASSIC"]
  - `test_run_pipeline_gnn` — GNN path
  - `test_run_pipeline_per_patch` — EVALUATE_PER_PATCH=True
  - `test_load_data_with_series` — series table exists
  - `test_load_data_without_series` — no series table
  - `test_run_pipeline_exception` — exception → logger.error

### 5.2 `data/ingestion.py` remaining (0% → 100%)
- **File:** `src/sc2ml/data/tests/test_ingestion.py`
- **Tests (~7):**
  - `test_audit_raw_data_empty_dir` — empty dir → zero counts
  - `test_audit_raw_data_mixed` — files with/without events
  - `test_load_map_translations_with_files` — creates table
  - `test_load_map_translations_no_files` — warning logged
  - `test_collect_pending_files_filters_done` — manifest filtering
  - `test_run_in_game_extraction_mock_pool` — mock Pool, verify batches
  - `test_run_in_game_extraction_empty_pending` — early return

---

## New files to create

| File | Purpose |
|------|---------|
| `tests/test_models/__init__.py` | Package init |
| `tests/test_models/test_reporting.py` | ExperimentReport tests |
| `tests/test_models/test_classical.py` | Classical model pipeline tests |
| `tests/test_models/test_tuning.py` | Hyperparameter tuning tests |
| `tests/test_gnn_embedder.py` | Node2Vec embedder tests |
| `tests/test_gnn_visualizer.py` | t-SNE visualizer tests |
| `tests/test_cli.py` | CLI orchestration tests |
| `tests/helpers_classical_unit.py` | Subprocess worker for classical.py |
| `tests/helpers_tuning.py` | Subprocess worker for tuning.py |
| `tests/helpers_evaluation.py` | Subprocess worker for evaluation.py |

## Existing files to augment

| File | Tests to add |
|------|-------------|
| `tests/test_features/test_build_features.py` | 1 |
| `tests/test_features/test_group_e.py` | 2 |
| `tests/test_cv.py` | 1 |
| `tests/test_analysis/test_error_analysis.py` | 1 |
| `tests/test_analysis/test_shap_analysis.py` | 6 |
| `tests/test_evaluation.py` | 13 |
| `tests/test_sanity_validation.py` | 8 |
| `tests/test_gnn_diagnostics.py` | 2 |
| `src/sc2ml/data/tests/test_processing.py` | 5 |
| `src/sc2ml/data/tests/test_ingestion.py` | 7 |

## Verification

After each phase, run:
```bash
poetry run pytest tests/ -m "not slow" --ignore=tests/test_mps.py --cov=sc2ml --cov-report=term-missing
```

At the end, run the full suite including slow tests:
```bash
poetry run pytest tests/ --ignore=tests/test_mps.py --cov=sc2ml --cov-report=term-missing
```

Target: 0 missing lines in all modules.
