---
task_id: "T04"
task_name: "Filesystem mv raw data + verify"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope: []
read_scope: []
category: "B"
---

# Spec: Filesystem mv raw data + verify

## Objective

Move the actual (gitignored) data files to the new directory structure using
filesystem `mv`. This is a pure filesystem operation — git does not track these
files. After the move, verify data is accessible at new paths, gitignore is
still effective, and then delete the old (now empty) directory trees.

## Instructions

1. **SC2 data** (rezipped tournament dirs — safe to move):
   ```bash
   mv src/rts_predict/sc2/data/sc2egset/raw/* \
      src/rts_predict/games/sc2/datasets/sc2egset/data/raw/ 2>/dev/null || true
   mv src/rts_predict/sc2/data/sc2egset/staging/in_game_events/* \
      src/rts_predict/games/sc2/datasets/sc2egset/data/staging/in_game_events/ 2>/dev/null || true
   mv src/rts_predict/sc2/data/sc2egset/db/* \
      src/rts_predict/games/sc2/datasets/sc2egset/data/db/ 2>/dev/null || true
   mv src/rts_predict/sc2/data/sc2egset/tmp/* \
      src/rts_predict/games/sc2/datasets/sc2egset/data/tmp/ 2>/dev/null || true
   ```

2. **AoE2 companion data** (~9.2GB parquet):
   ```bash
   mv src/rts_predict/aoe2/data/aoe2companion/raw/matches/* \
      src/rts_predict/games/aoe2/datasets/aoe2companion/data/raw/matches/ 2>/dev/null || true
   mv src/rts_predict/aoe2/data/aoe2companion/raw/ratings/* \
      src/rts_predict/games/aoe2/datasets/aoe2companion/data/raw/ratings/ 2>/dev/null || true
   mv src/rts_predict/aoe2/data/aoe2companion/raw/leaderboards/* \
      src/rts_predict/games/aoe2/datasets/aoe2companion/data/raw/leaderboards/ 2>/dev/null || true
   mv src/rts_predict/aoe2/data/aoe2companion/raw/profiles/* \
      src/rts_predict/games/aoe2/datasets/aoe2companion/data/raw/profiles/ 2>/dev/null || true
   mv src/rts_predict/aoe2/data/aoe2companion/db/* \
      src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/ 2>/dev/null || true
   mv src/rts_predict/aoe2/data/aoe2companion/api/* \
      src/rts_predict/games/aoe2/datasets/aoe2companion/api/ 2>/dev/null || true
   ```

3. **AoE2 stats data** (~3.7GB parquet):
   ```bash
   mv src/rts_predict/aoe2/data/aoestats/raw/matches/* \
      src/rts_predict/games/aoe2/datasets/aoestats/data/raw/matches/ 2>/dev/null || true
   mv src/rts_predict/aoe2/data/aoestats/raw/players/* \
      src/rts_predict/games/aoe2/datasets/aoestats/data/raw/players/ 2>/dev/null || true
   mv src/rts_predict/aoe2/data/aoestats/raw/overview/* \
      src/rts_predict/games/aoe2/datasets/aoestats/data/raw/overview/ 2>/dev/null || true
   mv src/rts_predict/aoe2/data/aoestats/db/* \
      src/rts_predict/games/aoe2/datasets/aoestats/data/db/ 2>/dev/null || true
   ```

4. **SC2 logs**:
   ```bash
   mv src/rts_predict/sc2/logs src/rts_predict/games/sc2/logs 2>/dev/null || true
   ```

5. **Verify data is accessible at new paths**:
   ```bash
   ls src/rts_predict/games/sc2/datasets/sc2egset/data/raw/ | head -5
   ls src/rts_predict/games/aoe2/datasets/aoe2companion/data/raw/matches/ | head -3
   ls src/rts_predict/games/aoe2/datasets/aoestats/data/raw/matches/ | head -3
   ```

6. **Verify gitignore still effective** — `git status` must show NO new untracked data files.

7. **Delete old empty directory trees**:
   ```bash
   rm -rf src/rts_predict/sc2/
   rm -rf src/rts_predict/aoe2/
   ```

## Verification

- All 3 datasets' data accessible at new paths (step 5 output non-empty)
- `git status` shows no untracked data files
- `src/rts_predict/sc2/` directory does not exist
- `src/rts_predict/aoe2/` directory does not exist

## Context

- SC2 data (~214GB) has been rezipped as a safety precaution before this refactor.
- AoE2 data is parquet (~13GB total) — safe to `mv`.
- The `2>/dev/null || true` pattern handles cases where source dirs are empty (no-op).
- This task depends on T02 and T03 having completed `git mv` of tracked files first.
