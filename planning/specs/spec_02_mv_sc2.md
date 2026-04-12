---
task_id: "T02"
task_name: "git mv SC2 tracked files"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope:
  - "src/rts_predict/games/sc2/"
read_scope: []
category: "B"
---

# Spec: git mv SC2 tracked files

## Objective

Move all git-tracked SC2 files from `src/rts_predict/sc2/` to the new
`src/rts_predict/games/sc2/` structure using `git mv` so git preserves history.
Raw data files (gitignored) are NOT moved here — that is T04.

## Instructions

1. Create target directories:
   ```bash
   mkdir -p src/rts_predict/games/sc2/datasets/sc2egset/data/{raw,staging/in_game_events,db,tmp}
   mkdir -p src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition
   ```

2. `git mv` game-level files:
   ```bash
   git mv src/rts_predict/sc2/cli.py src/rts_predict/games/sc2/cli.py
   git mv src/rts_predict/sc2/config.py src/rts_predict/games/sc2/config.py
   git mv src/rts_predict/sc2/__init__.py src/rts_predict/games/sc2/__init__.py
   git mv src/rts_predict/sc2/data/processing.py src/rts_predict/games/sc2/processing.py
   ```

3. `git mv` data README and .gitkeeps:
   ```bash
   git mv src/rts_predict/sc2/data/sc2egset/raw/README.md \
          src/rts_predict/games/sc2/datasets/sc2egset/data/raw/README.md
   git mv src/rts_predict/sc2/data/sc2egset/staging/README.md \
          src/rts_predict/games/sc2/datasets/sc2egset/data/staging/README.md
   ```
   Move all `.gitkeep` files to their corresponding new locations (raw, staging, db, tmp).

4. `git mv` entire reports tree:
   ```bash
   git mv src/rts_predict/sc2/reports/sc2egset/PHASE_STATUS.yaml \
          src/rts_predict/games/sc2/datasets/sc2egset/reports/PHASE_STATUS.yaml
   git mv src/rts_predict/sc2/reports/sc2egset/STEP_STATUS.yaml \
          src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml
   git mv src/rts_predict/sc2/reports/sc2egset/ROADMAP.md \
          src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md
   git mv src/rts_predict/sc2/reports/sc2egset/research_log.md \
          src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md
   ```
   Move any other files in `sc2/reports/sc2egset/` (including `artifacts/` subdirs).

5. Create new `__init__.py` package markers (these are new files, not git mv):
   ```
   src/rts_predict/games/__init__.py
   src/rts_predict/games/sc2/datasets/__init__.py
   src/rts_predict/games/sc2/datasets/sc2egset/__init__.py
   ```

6. Delete old stale `__init__.py` (no longer needed as a package marker at data level):
   ```bash
   git rm src/rts_predict/sc2/data/__init__.py
   ```
   Also git rm any other empty `__init__.py` files left in the old sc2 tree.

7. Do NOT move raw data files — they are gitignored and remain on disk at old paths.
   The filesystem move happens in T04.

## Verification

- `git status` shows renames, no deletions of data files
- `ls src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` exists
- Old `src/rts_predict/sc2/` dir has no remaining tracked files
  (`git ls-files src/rts_predict/sc2/` returns empty)
