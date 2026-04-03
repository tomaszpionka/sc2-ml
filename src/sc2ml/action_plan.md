# Plan: Run Phase 0 Sanity Validation on Real Data

## Context
All infrastructure is built (66 features, 5 models, 3 baselines, 25 sanity checks, 328 tests) but **nothing has been run on real data** (44,520 matches in `~/duckdb_work/test_sc2.duckdb`). The ROADMAP explicitly marks Phase 0 as blocking — no experiments are trustworthy until data sanity is confirmed.

## Step 1: Run `sc2ml sanity` on real data
- **Command:** `poetry run sc2ml sanity`
- **What it does:** Connects to real DuckDB, builds features (all groups), creates temporal split, runs 25 checks across 5 sections (§3.1-3.5)
- **Output:** `reports/sanity_validation.md`
- **Key file:** [validation.py](src/sc2ml/validation.py) — `run_full_sanity()` orchestrator

### Likely failure modes to handle:
1. **Race dummies as bool** (§3.5) — `pd.get_dummies` returns bool by default in newer pandas; fix in `group_c_matchup.py` with `dtype=int`
2. **Expanding window self-leakage** (§3.5) — verify `shift(1)` or equivalent in Group B/D computations
3. **Feature count mismatch** (§3.3) — expected A→14, A+B→37, etc.; may differ if columns changed
4. **Elo distribution off** (§3.3) — mean should be ~1500, std ~100-300
5. **Split ratio drift** — series-aware snapping may shift ratios away from 80/15/5
6. **DuckDB connection issues** — path is `~/duckdb_work/test_sc2.duckdb`, needs to exist

## Step 2: Fix any sanity failures
- Triage each failure by severity (blocking vs. cosmetic)
- Fix code in feature groups or processing as needed
- Re-run sanity until all 25 checks pass

## Step 3: Run feature ablation (Phase 1 begins)
- **Command:** `poetry run sc2ml ablation`
- **Output:** `reports/ablation_results.md`
- Measures marginal lift per feature group with LightGBM defaults

## Step 4: Hyperparameter tuning
- **Command:** `poetry run sc2ml tune --trials 200`
- Tunes top 2 models (LightGBM, XGBoost) via Optuna with expanding-window CV

## Step 5: Full evaluation
- **Command:** `poetry run sc2ml evaluate`
- **Output:** `reports/full_evaluation.md`
- All baselines + tuned models, bootstrap CIs, McNemar/DeLong, per-matchup breakdown

## Verification
- `reports/sanity_validation.md` exists with all 25 checks PASS
- `reports/ablation_results.md` shows monotonic accuracy lift A→E
- `reports/full_evaluation.md` shows accuracy in ~63-66% range (consistent with prior runs)
- No check shows accuracy >75% for any matchup (would indicate leakage)

## Critical files
- [src/sc2ml/validation.py](src/sc2ml/validation.py) — 25 sanity checks
- [src/sc2ml/cli.py](src/sc2ml/cli.py) — CLI subcommands (sanity, ablation, tune, evaluate)
- [src/sc2ml/features/group_a_elo.py](src/sc2ml/features/group_a_elo.py) through `group_e_context.py`
- [src/sc2ml/models/evaluation.py](src/sc2ml/models/evaluation.py) — metrics, CIs, statistical tests
- [src/sc2ml/config.py](src/sc2ml/config.py) — DB_FILE path, split ratios
