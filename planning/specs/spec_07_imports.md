---
task_id: "T07"
task_name: "Update imports + pyproject + notebooks + scripts"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG02"
file_scope:
  - "pyproject.toml"
  - "src/rts_predict/common/notebook_utils.py"
  - "scripts/sc2egset/"
  - "sandbox/"
read_scope: []
category: "B"
---

# Spec: Update imports + pyproject + notebooks + scripts

## Objective

Fix every Python import statement, entry point, string reference, shell script
path, and sandbox notebook import to reflect the new `rts_predict.games.*` namespace.

## Instructions

1. **All `.py` files** — systematic string replacement (grep first to confirm scope,
   then apply):
   - `rts_predict.sc2.` → `rts_predict.games.sc2.`
   - `rts_predict.aoe2.` → `rts_predict.games.aoe2.`
   - `rts_predict.aoe2.data.aoe2companion.` → `rts_predict.games.aoe2.datasets.aoe2companion.`
   - `rts_predict.aoe2.data.aoestats.` → `rts_predict.games.aoe2.datasets.aoestats.`
   - `rts_predict.sc2.data.processing` → `rts_predict.games.sc2.processing`
   - String refs in tests (mock patch paths): apply same replacements

2. **`src/rts_predict/common/notebook_utils.py` line ~26**:
   Change `"rts_predict.{game}.config"` → `"rts_predict.games.{game}.config"`

3. **`pyproject.toml`**:
   - Entry points:
     ```toml
     sc2 = "rts_predict.games.sc2.cli:main"
     aoe2 = "rts_predict.games.aoe2.cli:main"
     ```
   - Mirror drift exemptions: update the 3 path references to match new structure.

4. **Sandbox notebooks** (jupytext `.py` paired files — 3 files):
   - Update all import statements in `.py` files
   - Run `source .venv/bin/activate && jupytext --sync <file>.py` on each to
     update the `.ipynb` pair

5. **Shell scripts** in `scripts/sc2egset/` (6 files) — update hardcoded paths:
   ```
   $REPO_ROOT/src/rts_predict/sc2/data/sc2egset/raw
   → $REPO_ROOT/src/rts_predict/games/sc2/datasets/sc2egset/data/raw
   ```
   Apply the same pattern for any other sc2egset paths in those scripts.

6. **Run full check suite**:
   ```bash
   source .venv/bin/activate && poetry run pytest tests/ -v
   source .venv/bin/activate && poetry run ruff check src/ tests/
   source .venv/bin/activate && poetry run mypy src/rts_predict/
   source .venv/bin/activate && poetry run python scripts/check_mirror_drift.py
   ```

## Verification

- `pytest` passes (all tests)
- `ruff check` clean
- `mypy` clean
- `check_mirror_drift.py` exits 0
- `source .venv/bin/activate && poetry run sc2 --help` works
- `source .venv/bin/activate && poetry run aoe2 --help` works
- `grep -rn "rts_predict\.sc2\|rts_predict\.aoe2" --include="*.py" . | grep -v .venv`
  returns zero matches

## Context

- This task depends on T06 (config.py rewritten) — run only after T06 is complete.
- Sandbox notebooks are jupytext-paired. The `.toml` config lives at `sandbox/jupytext.toml`.
  Always sync `.py` → `.ipynb`, never edit `.ipynb` directly.
- The mirror drift script checks that `src/` and `tests/` structures remain in sync.
  It may need path updates itself — read it before running.
