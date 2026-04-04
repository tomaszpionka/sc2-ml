# Chore: Remove Pre-Roadmap Legacy Code

## Context

The repository contains feature engineering, GNN, classical ML, and analysis modules
written before proper data exploration was done. These modules violate scientific
invariants (e.g. temporal leakage via `.shift()` patterns), rely on split logic
the roadmap explicitly supersedes, and risk polluting execution sessions when Claude
reads them as "established convention". A single clean-cut removal commit — preceded
by a git tag — makes every removed file trivially recoverable via `git show` while
eliminating the contamination risk entirely.

**Category C — chore/maintenance**

---

## Branch

`chore/remove-pre-roadmap-legacy-code`

---

## Pre-commit step (before any file changes)

```bash
git tag pre-roadmap-cleanup
```

This creates a named reference point. Any removed function can be recovered with
`git show pre-roadmap-cleanup:src/sc2ml/features/group_a_elo.py` etc.

---

## What NOT to touch

- `src/sc2ml/data/ingestion.py` — Phase 0, active
- `src/sc2ml/data/processing.py` — **partially kept** (see edits below)
- `src/sc2ml/data/audit.py` — Phase 0 audit, active
- `src/sc2ml/data/exploration.py` — Phase 1, active
- `src/sc2ml/data/schemas.py` — active
- `src/sc2ml/data/samples/` — reference replays, keep
- `src/sc2ml/data/tests/` — **partially kept** (see edits below)
- `src/sc2ml/cli.py` — **partially kept** (see edits below)
- `src/sc2ml/config.py` — **partially kept** (see edits below)
- `src/sc2ml/tests/test_cli.py` — **partially kept** (see edits below)
- `src/sc2ml/__init__.py`, `src/sc2ml/config.py` — keep
- `tests/conftest.py`, `tests/helpers.py`, `tests/__init__.py`, `tests/test_mps.py` — keep
- `src/aoe2/.gitkeep` — keep
- `reports/` — keep all artifacts

---

## Step 1 — Delete entire directories

```
src/sc2ml/features/          (groups A-E, registry, compat, common, all tests — 20+ files)
src/sc2ml/gnn/               (model, pipeline, trainer, embedder, visualizer, tests — 8 files)
src/sc2ml/models/            (classical, baselines, evaluation, tuning, reporting, tests — 15 files)
src/sc2ml/analysis/          (error_analysis, shap_analysis, tests — 5 files)
tests/integration/           (test_integration, test_ablation, test_graph_construction,
                               test_gnn_diagnostics, test_model_reproducibility — 5 files)
```

```bash
git rm -r src/sc2ml/features/ src/sc2ml/gnn/ src/sc2ml/models/ src/sc2ml/analysis/ tests/integration/
```

---

## Step 2 — Delete individual files

```
src/sc2ml/data/cv.py                          (ExpandingWindowCV — future phase, not Phase 0-1)
src/sc2ml/data/tests/test_cv.py               (tests for above)
src/sc2ml/validation.py                       (sanity checks that depend on features/splits)
src/sc2ml/tests/test_sanity_validation.py     (tests for validation.py)
src/sc2ml/tests/helpers_sanity.py             (helpers for sanity tests)
src/sc2ml/logs/sc2_pipeline.log               (stale log from old pipeline runs)
```

```bash
git rm src/sc2ml/data/cv.py \
       src/sc2ml/data/tests/test_cv.py \
       src/sc2ml/validation.py \
       src/sc2ml/tests/test_sanity_validation.py \
       src/sc2ml/tests/helpers_sanity.py \
       src/sc2ml/logs/sc2_pipeline.log \
       processing_manifest.json
```

---

## Step 3 — Edit `src/sc2ml/data/ingestion.py`

Remove the deprecated `slim_down_sc2_with_manifest()` function (lines ~111–195).

Remove its import from config:
```python
MANIFEST_PATH,  # remove this line
```
Keep all other imports and functions in `ingestion.py` (`move_data_to_duck_db`,
`load_map_translations`, Path B event extraction, `_load_manifest`, `_save_manifest`, etc.)

Also edit `src/sc2ml/data/tests/test_ingestion.py`:
- Remove `slim_down_sc2_with_manifest` from the import block
- Remove all test classes/functions that test `slim_down_sc2_with_manifest`
  (they reference `MANIFEST_PATH` and test the deprecated trimming behaviour)

---

## Step 4 — Edit `src/sc2ml/cli.py`

### Imports to remove
```python
from sc2ml.features import build_features, split_for_ml
from sc2ml.gnn.embedder import append_embeddings_to_df, train_and_get_embeddings
from sc2ml.gnn.pipeline import build_starcraft_graph
from sc2ml.gnn.trainer import train_and_evaluate_gnn
from sc2ml.gnn.visualizer import visualize_gnn_space
from sc2ml.models.classical import train_and_evaluate_models
```

Also remove from the `processing` import: `create_temporal_split`, `validate_data_split_sql`, `validate_temporal_split`

Remove top-level import `import pandas as pd` (no longer needed after removing run_pipeline).

### Module-level constants to remove
```python
MODELS_TO_RUN = [...]
EVALUATE_PER_PATCH = False
GLOBAL_TEST_SIZE = 0.05
```

### Functions to remove entirely
- `run_pipeline()`
- `_load_data_and_features()`
- `_run_ablation_command()`
- `_run_tune_command()`
- `_run_evaluate_command()`
- `_run_sanity_command()`

### `init_database()` — remove two lines
```python
create_temporal_split(con)    # remove
validate_temporal_split(con)  # remove
```

### `main()` argparse — remove subcommands: `run`, `ablation`, `tune`, `evaluate`, `sanity`
Keep only: `init`, `audit`, `explore`

### `main()` dispatch — remove elif branches for removed subcommands

---

## Step 5 — Edit `src/sc2ml/data/processing.py`

### Config imports to remove
```python
from sc2ml.config import SERIES_GAP_SECONDS, TEST_RATIO, TRAIN_RATIO, VAL_RATIO
```
Replace with:
```python
from sc2ml.config import SERIES_GAP_SECONDS
```

### SQL constants to remove (used only by the three removed functions)
- `_CHRONOLOGICAL_SPLIT_QUERY`
- `_MATCH_SPLIT_CREATE_QUERY`
- `_SPLIT_STATS_QUERY`
- `_SPLIT_BOUNDARIES_QUERY`
- `_TOURNAMENT_CONTAINMENT_QUERY`
- `_SERIES_INTEGRITY_QUERY`
- `_YEAR_DIST_PER_SPLIT_QUERY`

### Functions to remove
- `create_temporal_split()`
- `validate_temporal_split()`
- `validate_data_split_sql()`

**Keep** `_MATCHES_WITH_SPLIT_QUERY`, `_MATCHES_WITHOUT_SPLIT_QUERY`, `_YEAR_DISTRIBUTION_QUERY`,
`_TOURNAMENT_GROUPING_QUERY` — still used by `get_matches_dataframe` and `assign_series_ids`.

---

## Step 6 — Edit `src/sc2ml/data/tests/test_processing.py`

Remove the import of `create_temporal_split`, `validate_temporal_split` from the import block.

Remove all test classes/functions that test the three removed functions:
- Any class/function testing `create_temporal_split`
- Any class/function testing `validate_temporal_split`
- Any class/function testing `validate_data_split_sql`

Keep all tests for: `create_raw_enriched_view`, `create_ml_views`, `get_matches_dataframe`, `assign_series_ids`.

---

## Step 7 — Edit `src/sc2ml/tests/test_cli.py`

Remove all test cases that reference removed subcommands or removed functions:
- Tests for `run_pipeline`
- Tests for `_run_ablation_command`
- Tests for `_run_tune_command`
- Tests for `_run_evaluate_command`
- Tests for `_run_sanity_command`
- Any helper fixtures that exist solely for the above

Keep tests for: `init_database`, `_run_audit_command`, `_run_explore_command`, `main()` routing for kept subcommands.

---

## Step 8 — Edit `src/sc2ml/config.py`

Remove orphaned constants no longer referenced anywhere after cleanup:
- `MANIFEST_PATH` — was used in `slim_down_sc2_with_manifest()` (removed)
- `PATCH_MIN_MATCHES` — was used in `run_pipeline()` (removed)
- `VETERAN_MIN_GAMES` — was used in `_run_evaluate_command()` (removed)
- `EXPANDING_CV_N_SPLITS` — was used in `cv.py` (deleted)
- `EXPANDING_CV_MIN_TRAIN_FRAC` — was used in `cv.py` (deleted)
- `TEST_RATIO`, `TRAIN_RATIO`, `VAL_RATIO` — were used in `create_temporal_split` (removed) and `validation.py` (deleted)

---

## Step 9 — Commit

```bash
git add -u   # stages deletions and modifications
git commit -m "chore: remove pre-roadmap legacy code (recoverable via git history)"
```

The commit message signals to future readers (and Claude Code) that this was intentional
cleanup, not accidental loss. The `pre-roadmap-cleanup` tag and git history make every
deleted file trivially retrievable.

---

## Verification

After the commit:

```bash
poetry run pytest tests/ src/ -v --cov=sc2ml --cov-report=term-missing
poetry run ruff check src/ tests/
poetry run mypy src/
```

All three must pass clean. The surviving test surface covers:
- `data/tests/test_audit.py`
- `data/tests/test_data_validation.py`
- `data/tests/test_exploration.py`
- `data/tests/test_ingestion.py`
- `data/tests/test_processing.py` (trimmed)
- `tests/test_cli.py` (trimmed)
- `tests/test_mps.py`

No features, no models, no GNN — the only importable code is the Phase 0-1 data pipeline.

---

## Scope confirmation

This PR does NOT touch:
- Any `reports/` artifacts from Phase 0 or Phase 1
- `src/sc2ml/data/ingestion.py`, `audit.py`, `exploration.py`, `schemas.py`
- `src/sc2ml/data/samples/`
- `src/aoe2/.gitkeep`
- `CHANGELOG.md`, `pyproject.toml`, `thesis/`
- `.claude/` reference files
