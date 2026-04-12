---
task_id: "T06"
task_name: "Rewrite config.py path constants"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG02"
file_scope:
  - "src/rts_predict/games/sc2/config.py"
  - "src/rts_predict/games/aoe2/config.py"
read_scope: []
category: "B"
---

# Spec: Rewrite config.py path constants

## Objective

Rewrite both config files with correct `__file__`-relative path derivation
for the new `games/<game>/` directory depth. The root is now 4 levels up from
each config file (was 3 levels in the old structure).

## Instructions

1. **`src/rts_predict/games/sc2/config.py`** — replace path constants section with:
   ```python
   GAME_DIR = Path(__file__).resolve().parent           # games/sc2/
   ROOT_DIR = GAME_DIR.parent.parent.parent.parent      # 4 levels to repo root
   DATASETS_DIR = GAME_DIR / "datasets"
   DATASET_DIR = DATASETS_DIR / "sc2egset"
   DATA_DIR = DATASET_DIR / "data"
   REPORTS_DIR = DATASET_DIR / "reports"
   DATASET_ARTIFACTS_DIR = REPORTS_DIR / "artifacts"
   DB_FILE = DATA_DIR / "db" / "db.duckdb"
   DUCKDB_TEMP_DIR = DATA_DIR / "tmp"
   REPLAYS_SOURCE_DIR = DATA_DIR / "raw"
   IN_GAME_PARQUET_DIR = DATA_DIR / "staging" / "in_game_events"
   IN_GAME_MANIFEST_PATH = DATA_DIR / "staging" / "in_game_processing_manifest.json"
   MODELS_DIR = GAME_DIR / "models"
   ```
   Remove `DATASET_REPORTS_DIR` if present (redundant — `REPORTS_DIR` is already per-dataset).

2. **`src/rts_predict/games/aoe2/config.py`** — read the existing file first, then
   rebase all path constants from the old `data/` prefix to `datasets/<dataset>/data/`:
   ```python
   GAME_DIR = Path(__file__).resolve().parent
   ROOT_DIR = GAME_DIR.parent.parent.parent.parent
   DATASETS_DIR = GAME_DIR / "datasets"
   AOE2COMPANION_DIR = DATASETS_DIR / "aoe2companion"
   AOE2COMPANION_DATA_DIR = AOE2COMPANION_DIR / "data"
   AOE2COMPANION_RAW_DIR = AOE2COMPANION_DATA_DIR / "raw"
   AOE2COMPANION_RAW_MATCHES_DIR = AOE2COMPANION_RAW_DIR / "matches"
   AOE2COMPANION_RAW_LEADERBOARDS_DIR = AOE2COMPANION_RAW_DIR / "leaderboards"
   AOE2COMPANION_RAW_PROFILES_DIR = AOE2COMPANION_RAW_DIR / "profiles"
   AOE2COMPANION_RAW_RATINGS_DIR = AOE2COMPANION_RAW_DIR / "ratings"
   AOE2COMPANION_DB_FILE = AOE2COMPANION_DATA_DIR / "db" / "db.duckdb"
   AOE2COMPANION_TMP_DIR = AOE2COMPANION_DATA_DIR / "tmp"
   AOE2COMPANION_API_DIR = AOE2COMPANION_DIR / "api"
   AOE2COMPANION_REPORTS_DIR = AOE2COMPANION_DIR / "reports"
   AOE2COMPANION_ARTIFACTS_DIR = AOE2COMPANION_REPORTS_DIR / "artifacts"
   AOESTATS_DIR = DATASETS_DIR / "aoestats"
   AOESTATS_DATA_DIR = AOESTATS_DIR / "data"
   AOESTATS_RAW_DIR = AOESTATS_DATA_DIR / "raw"
   # ... mirror the same pattern for all aoestats constants
   AOESTATS_REPORTS_DIR = AOESTATS_DIR / "reports"
   AOESTATS_ARTIFACTS_DIR = AOESTATS_REPORTS_DIR / "artifacts"
   ```
   Remove game-level `DATA_DIR` and `REPORTS_DIR` (no longer meaningful at game level).

3. Verify imports resolve:
   ```bash
   source .venv/bin/activate && poetry run python -c \
     "from rts_predict.games.sc2.config import REPLAYS_SOURCE_DIR; print(REPLAYS_SOURCE_DIR)"
   source .venv/bin/activate && poetry run python -c \
     "from rts_predict.games.aoe2.config import AOE2COMPANION_RAW_MATCHES_DIR; print(AOE2COMPANION_RAW_MATCHES_DIR)"
   ```

## Verification

- Both Python one-liners above execute without ImportError
- `source .venv/bin/activate && poetry run sc2 --help` does not crash
- `source .venv/bin/activate && poetry run aoe2 --help` does not crash
- All path constants resolve to paths under `src/rts_predict/games/`

## Context

- Read the existing config files before rewriting — they may have additional constants
  not listed above (especially aoe2/config.py which has ~22 constants).
- Do NOT remove any constant names that are referenced by other modules yet —
  T07 handles import updates. Ensure backward-name-compatibility until T07 lands.
