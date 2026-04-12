---
task_id: "T02"
task_name: "AoE2 README: add per-dataset report/artifact paths"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope:
  - "src/rts_predict/aoe2/README.md"
read_scope:
  - "src/rts_predict/aoe2/config.py"
  - "src/rts_predict/sc2/README.md"
category: "C"
---

# Spec: AoE2 README — add per-dataset report/artifact paths

## Objective

Add the 4 missing per-dataset report and artifact path constants to the
aoe2 README paths table, matching the SC2 README pattern.

## Instructions

1. Read `src/rts_predict/aoe2/README.md` and `src/rts_predict/aoe2/config.py`.
2. Read `src/rts_predict/sc2/README.md` for the reference pattern.
3. Add these 4 rows to the aoe2 paths table (after the existing entries,
   grouped logically by dataset):

   | Constant | Path |
   |----------|------|
   | `AOE2COMPANION_REPORTS_DIR` | `src/rts_predict/aoe2/reports/aoe2companion/` |
   | `AOE2COMPANION_ARTIFACTS_DIR` | `src/rts_predict/aoe2/reports/aoe2companion/artifacts/` |
   | `AOESTATS_REPORTS_DIR` | `src/rts_predict/aoe2/reports/aoestats/` |
   | `AOESTATS_ARTIFACTS_DIR` | `src/rts_predict/aoe2/reports/aoestats/artifacts/` |

4. Do NOT add `RAW_*`, `TEMP_DIR`, or `MANIFEST` constants.

## Verification

1. All 4 constant names exist in `config.py` (grep to confirm).
2. Table has parity with SC2 README pattern (core paths for agent routing).
