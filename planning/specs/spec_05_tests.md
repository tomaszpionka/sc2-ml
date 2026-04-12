---
task_id: "T05"
task_name: "Restructure test mirror"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope:
  - "tests/rts_predict/games/"
read_scope: []
category: "B"
---

# Spec: Restructure test mirror

## Objective

Mirror the src/ restructure in `tests/rts_predict/`. Move all SC2 and AoE2
test files to the new `games/<game>/datasets/<dataset>/` layout using `git mv`,
then delete colocated test dirs inside src/ (they are empty — only `__pycache__`).

## Instructions

1. Create target directories:
   ```bash
   mkdir -p tests/rts_predict/games/sc2/datasets/sc2egset
   mkdir -p tests/rts_predict/games/aoe2/datasets/aoe2companion
   mkdir -p tests/rts_predict/games/aoe2/datasets/aoestats
   ```

2. `git mv` SC2 test files:
   ```bash
   git mv tests/rts_predict/sc2/test_cli.py \
          tests/rts_predict/games/sc2/test_cli.py
   git mv tests/rts_predict/sc2/data/conftest.py \
          tests/rts_predict/games/sc2/datasets/sc2egset/conftest.py
   git mv tests/rts_predict/sc2/data/test_processing.py \
          tests/rts_predict/games/sc2/test_processing.py
   ```
   (Note: `processing.py` moved to game level in T02, so test lives at game level.)

3. `git mv` AoE2 test files:
   ```bash
   git mv tests/rts_predict/aoe2/test_cli.py \
          tests/rts_predict/games/aoe2/test_cli.py
   ```
   For each file in `tests/rts_predict/aoe2/data/aoe2companion/`:
   ```bash
   git mv tests/rts_predict/aoe2/data/aoe2companion/<file> \
          tests/rts_predict/games/aoe2/datasets/aoe2companion/<file>
   ```
   For each file in `tests/rts_predict/aoe2/data/aoestats/`:
   ```bash
   git mv tests/rts_predict/aoe2/data/aoestats/<file> \
          tests/rts_predict/games/aoe2/datasets/aoestats/<file>
   ```

4. Create `__init__.py` files at new levels as needed:
   ```
   tests/rts_predict/games/__init__.py
   tests/rts_predict/games/sc2/__init__.py
   tests/rts_predict/games/sc2/datasets/__init__.py
   tests/rts_predict/games/sc2/datasets/sc2egset/__init__.py
   tests/rts_predict/games/aoe2/__init__.py
   tests/rts_predict/games/aoe2/datasets/__init__.py
   tests/rts_predict/games/aoe2/datasets/aoe2companion/__init__.py
   tests/rts_predict/games/aoe2/datasets/aoestats/__init__.py
   ```

5. Delete colocated test dirs in src/ (contain only `__pycache__`, no test files):
   ```bash
   rm -rf src/rts_predict/sc2/data/tests/
   rm -rf src/rts_predict/aoe2/data/aoestats/tests/
   rm -rf src/rts_predict/common/tests/
   ```
   (These are the stale empty dirs identified in LATER.md.)

6. Delete old test dirs (now empty after git mv):
   ```bash
   rm -rf tests/rts_predict/sc2/
   rm -rf tests/rts_predict/aoe2/
   ```

## Verification

- `source .venv/bin/activate && poetry run pytest --collect-only` finds all tests at new paths
- No test directories inside `src/` (`find src/ -name "test_*.py" | wc -l` returns 0)
- Old `tests/rts_predict/sc2/` and `tests/rts_predict/aoe2/` do not exist

## Context

- This task depends on T02 and T03 (git mv of src/ files) but can run in parallel with T04.
- The colocated test dirs (`src/.../tests/`) are a policy violation documented in LATER.md
  ("no tests inside src/"). They are empty (only `__pycache__`) so deletion is safe.
