# SC2-ML Project Roadmap

> **Thesis:** "A comparative analysis of methods for predicting game results in real-time strategy games, based on the examples of StarCraft II and Age of Empires II."
>
> This document tracks progress from code infrastructure through to thesis-ready results. Each item is checkable — mark `[x]` when complete. Cross-reference with `CHANGELOG.md` for code-level detail and `reports/methodology.md` for the full experimental specification.
>
> <!-- Claude: update checkboxes and "Last updated" date as work completes -->
> **Last updated:** 2026-04-03

---

## 1. Research Questions → Implementation Mapping

| RQ | Question | Key Sections | Status |
|----|----------|-------------|--------|
| **RQ1** | Pre-match prediction ceiling & feature lift over Elo baseline | §4 Features, §6.1 Ablation, §6.2 Tuning, §6.3 Evaluate | Infrastructure built, not yet run on real data |
| **RQ2** | In-game crossover point (when does in-game beat pre-match?) | §3.2 Path B, §5.3 LSTM/TCN, §6.4 Early Prediction Curve | Extraction scaffolded, models not started |
| **RQ3** | Tournament-aware sequential prediction | §6.6 Sequential Eval | Not started |

---

## 2. Data Pipeline

### 2.1 Path A — Pre-match Metadata (feeds RQ1)

- [x] Raw JSON ingestion into DuckDB (`data/ingestion.py`)
- [x] `flat_players` view — one row per player per match, race normalization, map translation
- [x] `matches_flat` view — paired player perspectives (2 rows per match)
- [x] `game_version` column in views (for patch-based analysis)
- [x] `player_id` column in views
- [x] Map name translation table (1,488 localized → 215 canonical English names)
- [x] Series detection via 2-hour gap heuristic (`assign_series_ids()`)
- [x] Temporal train/val/test split 80/15/5 (`create_temporal_split()`)
- [x] `init` CLI subcommand for one-step database setup
- [x] 12 integration smoke tests covering full chain

### 2.2 Path B — In-game Time-series (feeds RQ2)

- [x] Multiprocessing extraction framework (`extract_raw_events_from_file()`, Parquet intermediate)
- [x] DuckDB loaders with `player_stats` view (39 stat columns) and `match_player_map` table
- [x] `PLAYER_STATS_FIELD_MAP` — 39 `scoreValue*` → snake_case mappings
- [x] Parquet-based intermediate storage for inspection/re-loading
- [ ] **Stage 1 full execution** — run extraction on all ~17,930 replays (one-time, ~hours)
- [ ] **`in_game_features` DuckDB table** — per-timestep derived features (resource differentials, army composition, action binning) as specified in methodology §2.4
- [ ] **Stage 3 tensor materialization** — `[N_matches, T_max, 2*F]` padded tensors with mask, ready for LSTM/TCN

---

## 3. Data & Model Sanity Validation

> **Purpose:** Before running expensive experiments, validate that the processed data, feature engineering, and temporal splits produce sensible results. A single red flag here (e.g., suspiciously high accuracy, degenerate features, target leakage) invalidates all downstream results.

### Execution Checklist (Phase 0 → Phase 1)

- [ ] Run `poetry run sc2ml sanity` → `reports/sanity_validation.md`
- [ ] All 25+ sanity checks PASS
- [ ] Fix any failures (known issues: bool race dummies, expanding-window leakage, feature count mismatch)
- [ ] Run `poetry run sc2ml ablation` → `reports/ablation_results.md`
- [ ] Run `poetry run sc2ml tune --trials 200`
- [ ] Run `poetry run sc2ml evaluate` → `reports/full_evaluation.md`

### 3.1 DuckDB View Sanity

- [ ] Row counts: `flat_players` ≈ 2 × unique matches, `matches_flat` ≈ 2 × unique matches
- [ ] NULL rate audit: no critical columns (match_time, player names, race, result) with >0% NULLs
- [ ] `match_time` range and distribution (expect 2016–present, no future dates, no clustering artifacts)
- [ ] Race distribution: 3 races only, no residual abbreviated names (`Terr`, `Prot`)
- [ ] Duplicate `match_id` check in `flat_players` (exactly 2 rows per match, no more)
- [ ] Series ID assignment coverage (what % of matches belong to a detected series?)

### 3.2 Temporal Split Integrity

- [ ] Target balance per split: train/val/test should each be ~50% win rate (due to dual perspective)
- [ ] No temporal leakage: `max(train.match_time) < min(val.match_time) < min(test.match_time)`
- [ ] Series containment: no series split across train/val or val/test boundaries
- [ ] Split size ratios close to 80/15/5

### 3.3 Feature Distribution Checks

- [ ] No constant or near-constant features (std ≈ 0) across training set
- [ ] No features with >50% NaN/zero (degenerate due to cold-start or missing data)
- [ ] Elo features: mean ≈ 1500, reasonable spread (std ~100–300), `elo_diff` centered near 0
- [ ] Historical features: check cold-start handling — first N matches per player should have sensible defaults, not NaN propagation
- [ ] Feature correlation matrix: no unexpected perfect correlations (would indicate redundancy or formula bugs)
- [ ] Feature count grows monotonically per group: A→14, A+B→37, A+B+C→45, A+B+C+D→62, all→66

### 3.4 Leakage & Baseline Smoke Tests

- [ ] **Majority class baseline ≈ 50%** (confirms balanced target from dual perspective)
- [ ] **Elo-only baseline meaningfully above 50%** (confirms Elo system is informative; expect ~58–62%)
- [ ] **LightGBM on all features ≈ 63–66%** (consistent with prior runs in `reports/archive/09_run.md`)
- [ ] **No matchup achieving >75% accuracy** (would suggest leakage or data issue)
- [ ] **No single feature with >0.3 correlation with target** after proper temporal ordering (sanity cap)
- [ ] Quick feature importance from LightGBM: top features should be Elo/winrate-related, not map/context features (domain sanity)
- [ ] Train vs. test accuracy gap <5% (if much larger → overfitting or distribution shift)

### 3.5 Known Issues to Verify/Fix

- [ ] Confirm `pd.get_dummies` race columns are int, not bool (flagged in research log)
- [ ] Confirm expanding-window aggregates exclude current match (no self-leakage)
- [ ] Confirm Elo computation deduplicates via `processed_matches` set on real data
- [ ] Verify Group D rolling windows handle players with sparse match histories gracefully

### 3.6 Test Coverage (see `reports/test_plan.md` for details)

- [x] Phase 1 — Trivial gaps in existing test files (~10 tests)
- [x] Phase 2 — New test files for 0%-coverage modules (~25 tests)
- [x] Phase 3 — Augmenting partially-covered modules (~25 tests)
- [x] Phase 4 — Subprocess-isolated LightGBM tests (~15 tests)
- [x] Phase 5 — CLI and ingestion orchestration (~25 tests)
- [ ] Target: 100% coverage (currently 83%)

---

## 4. Feature Engineering

### 4.1 Feature Groups (methodology §3.1)

- [x] **Group A — Elo**: dynamic K-factor, `elo_diff`, `expected_win_prob`
- [x] **Group B — Historical aggregates**: Bayesian-smoothed winrates, cumulative APM/SQ means, `hist_std_apm`, `hist_std_sq`
- [x] **Group C — Matchup & map**: race one-hot, spawn distance, map area, `hist_winrate_map_race_smooth`
- [x] **Group D — Form & momentum**: win/loss streaks, EMA stats, 7d/30d activity, H2H records
- [x] **Group E — Context**: patch version numeric, tournament match position, series game number
- [x] `build_features(df, groups=FeatureGroup.X)` composable API
- [x] `split_for_ml()` consuming series-aware temporal split
- [x] `FeatureGroup` enum + registry with lazy-loaded compute functions
- [x] Backward-compatible wrappers (`perform_feature_engineering`, `temporal_train_test_split`)
- [x] 73 feature tests, 99% coverage on `features/`

### 4.2 In-game Features (methodology §3.2) — for RQ2

- [ ] Per-timestep resource differentials (minerals, vespene, army value, worker count)
- [ ] Efficiency ratios (collection rate, spending efficiency)
- [ ] Army composition (accumulated UnitBorn − UnitDied per unit type)
- [ ] Unit diversity (Shannon entropy)
- [ ] Tech tier flags
- [ ] Action features (real-time APM, camera movement, control group switches)
- [ ] Per-feature z-score normalization (training stats only)

---

## 5. Models

### 5.1 Baselines (methodology §5.2)

- [x] `MajorityClassBaseline` — always predicts majority class
- [x] `EloOnlyBaseline` — `expected_win_prob > 0.5`
- [x] `EloLRBaseline` — Logistic Regression on `elo_diff` only
- [x] All implement `predict_proba` for probability-based metrics
- [x] 18 baseline tests

### 5.2 Pre-match Models (methodology §5.3 — RQ1)

- [x] Logistic Regression (with StandardScaler)
- [x] LightGBM
- [x] XGBoost
- [x] Random Forest (kept for comparison, not primary)
- [x] Gradient Boosting (kept for comparison, not primary)
- [x] `train_and_evaluate_models()` returns `(dict[str, Pipeline], list[ModelResults])`

### 5.3 In-game Models (methodology §5.4 — RQ2)

- [ ] **LSTM** — 2-layer bidirectional, attention pooling, MLP head
- [ ] **TCN** — dilated causal convolutions, global pooling, MLP head
- [ ] Training loop with early stopping on validation loss
- [ ] MPS acceleration (with CPU fallback for sparse ops)

### 5.4 Fusion Model (methodology §5.5 — RQ1+RQ2)

- [ ] **Dual-stream** — pre-match MLP + in-game LSTM/TCN → concatenation → MLP head

### 5.5 GNN (deprioritized — appendix only)

- [x] GATv2 edge classifier (`SC2EdgeClassifier`)
- [x] Training loop with early stopping
- [x] Node2Vec embedding pipeline
- [x] t-SNE visualization
- [x] 14 diagnostic tests confirming majority-class collapse root causes
- [ ] Fix `pos_weight` in BCE loss (identified by diagnostics)
- [ ] Fix edge feature scaler leak (fit on full dataset)

---

## 6. Experiments

### 6.1 Feature Group Ablation (methodology §7.1 — RQ1)

- [x] `run_feature_ablation()` implemented in `evaluation.py`
- [x] `sc2ml ablation` CLI subcommand
- [ ] **Run on real data**: LightGBM on {A}, {A,B}, ..., {A,B,C,D,E}
- [ ] Report marginal lift per group step
- [ ] Permutation importance on winning group combination
- [ ] SHAP beeswarm on best pre-match model

### 6.2 Hyperparameter Tuning (methodology §5.6 — RQ1)

- [x] `tune_lgbm_optuna()` — Bayesian, 200 trials
- [x] `tune_xgb_optuna()` — Bayesian, 200 trials
- [x] `tune_lr_grid()` — grid search over C + penalty
- [x] `ExpandingWindowCV` for temporal inner loop
- [x] `sc2ml tune` CLI subcommand
- [ ] **Run on real data**: tune top 2 models with Optuna
- [ ] Save best hyperparameters to config/report

### 6.3 Full Model Evaluation (methodology §9 — RQ1)

- [x] `evaluate_model()` — accuracy, AUC-ROC, Brier, log loss + 95% CIs
- [x] `compare_models()` — McNemar's + DeLong's tests
- [x] Per-matchup breakdown (6 matchup types)
- [x] Veterans-only metrics
- [x] Calibration curve data
- [x] `ExperimentReport` with `.to_json()` and `.to_markdown()`
- [x] `sc2ml evaluate` CLI subcommand
- [ ] **Run on real data**: full evaluation with all baselines + tuned models
- [ ] Generate thesis-ready comparison table with CIs and p-values
- [ ] Generate calibration curves for best model per category

### 6.4 Early Prediction Curve (methodology §6 — RQ2, key thesis contribution)

- [ ] Evaluate in-game models at relative checkpoints: 10%, 20%, ..., 100%
- [ ] Evaluate at absolute checkpoints: 2, 4, 6, 8, 10, 12, 15, 20 min
- [ ] Plot accuracy/AUC/Brier as curves over game progress
- [ ] Identify crossover point where in-game beats best pre-match model
- [ ] Report prediction stability (mean absolute change between consecutive timesteps)

### 6.5 Patch Drift Experiment (methodology §10 — robustness)

- [x] `run_patch_drift_experiment()` implemented in `evaluation.py`
- [ ] **Run**: train on older patches, test on newer patch block
- [ ] Report accuracy drop as function of patch distance
- [ ] Compare with standard mixed-patch model

### 6.6 Tournament-Aware Sequential Evaluation (methodology §4.4 — RQ3)

- [ ] Implement sequential prediction loop per tournament
- [ ] Incrementally update Elo/winrates/counts after each revealed match
- [ ] Compare static vs. adaptive feature updates
- [ ] Report per-tournament accuracy curves

### 6.7 Interpretability & Error Analysis (methodology §8)

- [x] `classify_error_subgroups()` — mirrors, upsets, close Elo, short/long games
- [x] `compute_shap_values()`, `plot_shap_beeswarm()`, `plot_shap_per_matchup()`
- [x] `shap_feature_importance_table()`
- [ ] **Run on real data**: error subgroup report for best model
- [ ] **Run on real data**: SHAP analysis (global + per-matchup)
- [ ] Time-segmented SHAP for in-game models (how importance shifts across game phases)

---

## 7. Thesis Deliverables (methodology §13)

> These are the concrete outputs the SC2 portion of the thesis must produce.

- [ ] **D1 — Feature importance ranking** with marginal lift per group (from §6.1 ablation)
- [ ] **D2 — Model comparison table** with accuracy, AUC-ROC, Brier, log loss, CIs, McNemar p-values (from §6.3)
- [ ] **D3 — Early prediction curve** — accuracy/AUC/Brier vs. game progress, relative + absolute time (from §6.4)
- [ ] **D4 — Calibration curves** for best model per category: pre-match, in-game, fusion (from §6.3)
- [ ] **D5 — SHAP analysis** — global beeswarm + per-matchup + time-segmented for in-game (from §6.7)
- [ ] **D6 — Error analysis** — where models fail: upsets, mirrors, patch transitions (from §6.7)
- [ ] **D7 — Tournament sequential results** — static vs. adaptive comparison (from §6.6)
- [ ] **D8 — Patch drift analysis** — temporal robustness quantification (from §6.5)

---

## 8. Suggested Execution Order

The dependencies between sections create a natural ordering:

```
Phase 0: Data & Model Sanity Validation (§3)
    ↓   must pass before any experiment is trustworthy
Phase 1: RQ1 — Pre-match prediction (P0 priority)
    §6.1 Feature ablation  →  §6.2 Tuning  →  §6.3 Full evaluation
    §6.7 SHAP + error analysis (on best pre-match model)
    §6.5 Patch drift
    → produces D1, D2, D4, D5, D6, D8
    ↓
Phase 2: RQ2 — In-game prediction (P1 priority)
    §2.2 Complete Path B extraction  →  §4.2 In-game features
    §5.3 LSTM + TCN  →  §6.4 Early prediction curve
    §5.4 Dual-stream fusion
    → produces D3, updates D2/D4/D5
    ↓
Phase 3: RQ3 — Tournament-aware (P2 priority)
    §6.6 Sequential evaluation
    → produces D7
```

**Phase 0 is blocking.** If sanity checks reveal issues (leakage, degenerate features, unexpected accuracy), fix before proceeding. Prior runs (`reports/archive/09_run.md`) showed ~63–65% accuracy — deviation from this range on the current codebase needs investigation.

---

## 9. Out of Scope / Appendix-Only

These items are documented in methodology but explicitly deprioritized:

- GNN models (GATv2 exists but has known majority-class collapse — appendix only)
- FT-Transformer on pre-match features (academic interest, not core)
- Transformer on in-game time-series (dataset too small, high risk of underperformance)
- Build order sequence model (novel but risky)
- AoE2 integration (separate phase, after SC2 is complete)
