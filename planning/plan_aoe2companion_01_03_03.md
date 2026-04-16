---
category: A
branch: feat/table-utility-assessment
date: 2026-04-16
planner_model: claude-opus-4-6
dataset: aoe2companion
phase: "01"
pipeline_section: "01_03 -- Systematic Data Profiling"
invariants_touched: [I3, I6, I7, I9]
source_artifacts:
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/matches_raw.yaml
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/ratings_raw.yaml
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/leaderboards_raw.yaml
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/profiles_raw.yaml
critique_required: true
research_log_ref: null
---

# Plan: aoe2companion 01_03_03 -- Table Utility Assessment

## Scope

Empirical assessment of all 4 raw tables (matches_raw, ratings_raw,
leaderboards_raw, profiles_raw) for prediction pipeline utility. Run
diagnostic queries to determine: which tables carry temporal data suitable
for pre-game feature derivation under I3, which are stale snapshots, and
how matches_raw.rating relates to ratings_raw.rating. All verdicts emerge
from the query results, not from assumptions.

## Problem Statement

aoe2companion has 4 raw tables. Two appear to be time series (matches_raw,
ratings_raw) and two appear to be singleton snapshots (leaderboards_raw,
profiles_raw), but this characterization has not been formally verified.
The matches_raw.rating column has been classified AMBIGUOUS since 01_02_04
because it is unclear whether it represents the pre-game or post-game
rating. This step runs empirical queries to answer these open questions
and produce evidence-backed table utility verdicts.

## Assumptions & unknowns

- **Assumption:** All 4 raw tables are loaded and queryable in DuckDB
  (verified by 01_02_02 completion).
- **Unknown:** Whether matches_raw.rating is pre-game or post-game.
  Resolved by T02 cross-reference with ratings_raw.
- **Unknown:** Whether leaderboards_raw has any temporal dimension that
  could support pre-game attribution. Resolved by T01 queries.
- **Unknown:** Whether profiles_raw columns contribute information not
  already available in matches_raw. Resolved by T01 queries.

## Literature context

No external literature required. This is an internal data characterization
step. I3 (temporal discipline) and I6 (reproducibility) are the governing
invariants.

## Execution Steps

### T01 -- Investigate leaderboards_raw and profiles_raw

**Objective:** Run diagnostic queries on the two singleton-candidate tables
to characterize their temporal properties, coverage, redundancy with
matches_raw, and I3 classification.

**Instructions:**

1. Create notebook `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_03_table_utility_assessment.py`.

2. **leaderboards_raw -- source file count:**
