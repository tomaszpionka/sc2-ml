---
category: A
branch: feat/table-utility-assessment
date: 2026-04-16
planner_model: claude-opus-4-6
dataset: sc2egset
phase: "01"
pipeline_section: "01_03 -- Systematic Data Profiling"
invariants_touched: [I3, I6, I8, I9]
source_artifacts:
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replay_players_raw.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replays_meta_raw.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/map_aliases_raw.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/game_events_raw.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/tracker_events_raw.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/message_events_raw.yaml
critique_required: true
research_log_ref: null
---

# Plan: sc2egset 01_03_03 -- Table Utility Assessment

## Scope

Empirical assessment of all 6 raw data objects (3 tables, 3 views) for
prediction pipeline utility. Run diagnostic queries to verify the join
relationship between replay_players_raw and replays_meta_raw, assess
map_aliases_raw utility, characterize event view temporal properties, and
enumerate all replays_meta_raw struct leaf fields. All verdicts emerge from
query results.

## Problem Statement

sc2egset has 6 data objects. Two tables (replay_players_raw,
replays_meta_raw) are clearly central but currently separate -- a joined
VIEW is needed. map_aliases_raw (104K rows) is a translation lookup whose
necessity depends on whether map names are already English. Three event
views (670M+ rows total) contain game-time action data whose temporal
properties relative to I3 need formal characterization.

This step produces the evidence needed to design the `matches_flat` VIEW
SQL and formally scope each data object for the pipeline.

## Assumptions & unknowns

- **Assumption:** All 6 data objects are loaded and queryable in DuckDB
  (verified by 01_02_02 completion).
- **Assumption:** The join key between replay_players_raw and
  replays_meta_raw is `replay_id` derived via
  `regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1)`,
  per the sql-data.md rule.
- **Unknown:** Whether map names in replays_meta_raw are already in
  English or require translation via map_aliases_raw. Resolved by: T02.
- **Unknown:** Whether event views contain any loop=0 events and what
  those events represent. Resolved by: T03.
- **Unknown:** Which of the 31 replays_meta_raw struct leaf fields are
  useful vs constant/redundant. Resolved by: T01.

## Literature context

No external literature required. This is an internal data characterization
step. I3 (temporal discipline) and I6 (reproducibility) are the governing
invariants. The SC2 replay format documentation (s2protocol) informs
struct field interpretation but no specific citation is needed at this
profiling level.

## Execution Steps

### T01 -- Core table cross-inventory and full struct enumeration

**Objective:** Unified column inventory of replay_players_raw (25 cols) and
replays_meta_raw (all struct leaf fields). Verify the join using replay_id.
Enumerate every struct leaf field with its empirical properties.

**Instructions:**

1. Create notebook `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_03_table_utility.py`.

2. DESCRIBE both tables. Print column lists.

3. **Join verification using replay_id:**
   [Critique fix: BLOCKER -- must use replay_id derived via regexp_extract,
   not raw filename.]
