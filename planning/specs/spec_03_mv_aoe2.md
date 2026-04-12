---
task_id: "T03"
task_name: "git mv AoE2 tracked files"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope:
  - "src/rts_predict/games/aoe2/"
read_scope: []
category: "B"
---

# Spec: git mv AoE2 tracked files

## Objective

Move all git-tracked AoE2 files from `src/rts_predict/aoe2/` to the new
`src/rts_predict/games/aoe2/` structure using `git mv`. Covers both datasets:
aoe2companion and aoestats. Raw data files (gitignored) are NOT moved here —
that is T04.

## Instructions

1. Create target directories:
   ```bash
   mkdir -p src/rts_predict/games/aoe2/datasets/aoe2companion/data/{raw/{matches,leaderboards,profiles,ratings},db}
   mkdir -p src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition
   mkdir -p src/rts_predict/games/aoe2/datasets/aoestats/data/{raw/{matches,players,overview},db}
   mkdir -p src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition
   ```

2. `git mv` game-level files:
   ```bash
   git mv src/rts_predict/aoe2/cli.py src/rts_predict/games/aoe2/cli.py
   git mv src/rts_predict/aoe2/config.py src/rts_predict/games/aoe2/config.py
   git mv src/rts_predict/aoe2/__init__.py src/rts_predict/games/aoe2/__init__.py
   ```

3. For each dataset (`aoe2companion`, `aoestats`):
   a. `git mv` Python modules to `datasets/<dataset>/` (sibling to data/, not inside it):
      - `acquisition.py`, `ingestion.py`, `types.py` (if present)
      - `__init__.py`
   b. `git mv` api/ `.gitkeep` to `datasets/<dataset>/api/.gitkeep`
   c. `git mv` raw/ `README.md` + `.gitkeep`s to `datasets/<dataset>/data/raw/`
      (including subdirectory `.gitkeep`s for matches/, leaderboards/, etc.)
   d. `git mv` db/ `.gitkeep` to `datasets/<dataset>/data/db/.gitkeep`
   e. `git mv` tmp/ `.gitkeep` to `datasets/<dataset>/data/tmp/.gitkeep` (if exists)
   f. `git mv` entire reports tree to `datasets/<dataset>/reports/`:
      - `PHASE_STATUS.yaml`, `STEP_STATUS.yaml`, `ROADMAP.md`, `research_log.md`
      - Any `artifacts/` subdirs

4. Create new `__init__.py` package markers:
   ```
   src/rts_predict/games/aoe2/datasets/__init__.py
   src/rts_predict/games/aoe2/datasets/aoe2companion/__init__.py   (if not already git mv'd)
   src/rts_predict/games/aoe2/datasets/aoestats/__init__.py        (if not already git mv'd)
   ```

5. Delete old stale `__init__.py` files:
   ```bash
   git rm src/rts_predict/aoe2/data/__init__.py
   ```
   Also git rm any other empty `__init__.py` files left in the old aoe2 tree.

6. Do NOT move raw data files — they are gitignored and remain on disk at old paths.
   The filesystem move happens in T04.

## Verification

- `git status` shows renames, no deletions of data files
- Both `acquisition.py` files accessible at new paths:
  - `ls src/rts_predict/games/aoe2/datasets/aoe2companion/acquisition.py`
  - `ls src/rts_predict/games/aoe2/datasets/aoestats/acquisition.py`
- Old `src/rts_predict/aoe2/` dir has no remaining tracked files
  (`git ls-files src/rts_predict/aoe2/` returns empty)
