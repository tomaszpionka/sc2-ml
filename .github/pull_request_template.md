## Summary

<!-- 1-3 bullets describing what this branch does and why -->
-
-

## Type

<!-- Check all that apply -->
- [ ] `feat` — new functionality
- [ ] `fix` — bug fix
- [ ] `refactor` — code restructuring (no functional change)
- [ ] `test` — adding or improving tests
- [ ] `docs` — documentation only
- [ ] `chore` — maintenance, dependencies, config

## Scope

<!-- Which pipeline area(s) does this touch? -->
- [ ] Data ingestion (`data_ingestion.py`)
- [ ] SQL processing / views (`data_processing.py`)
- [ ] Feature engineering (`ml_pipeline.py`)
- [ ] ELO system (`elo_system.py`)
- [ ] Classical ML models (`model_training.py`, `hyperparameter_tuning.py`)
- [ ] GNN pipeline (`gnn_model.py`, `gnn_pipeline.py`, `gnn_trainer.py`)
- [ ] Node2Vec / embeddings (`node2vec_embedder.py`)
- [ ] Visualization (`gnn_visualizer.py`)
- [ ] Configuration / infrastructure (`config.py`, `main.py`)
- [ ] AoE2 pipeline
- [ ] Other: <!-- describe -->

## Changes

<!-- Brief list of files modified and what changed -->
| File | Change |
|------|--------|
|  |  |

## ML Experiment (if applicable)

<!-- Fill in if this PR contains model/feature changes -->

**Hypothesis:** <!-- What change was made and why it should help -->

**Baseline (before):** <!-- Accuracy / metrics from reports/XX_run.md reference -->

**Result (after):** <!-- New metrics; attach or reference reports/XX_run.md -->

**Run report:** `reports/XX_run.md`

## Data Integrity Checklist

- [ ] No current-match stats used as features (APM, SQ, supply_capped_pct, game_loops)
- [ ] Temporal split preserved — no random shuffling before feature engineering
- [ ] Random seed 42 used for all stochastic operations
- [ ] Data shapes and null counts validated at affected pipeline stages

## Documentation Checklist

- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] `reports/research_log.md` updated (required if experiment / methodology / issues involved)
- [ ] Tests added or updated in `tests/` for new logic
- [ ] Docstrings / comments updated for changed functions

## Commit Messages

<!-- List the Conventional Commits messages included in this PR -->
```
type(scope): description
```
