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

Systematically evaluate all 6 raw data objects (3 tables, 3 views) for
prediction pipeline utility. Produce per-object KEEP/CONDITIONAL/DEFER
verdicts, design the `matches_flat` VIEW SQL, assess map_aliases_raw
redundancy, and formally scope event views out of the pre-game pipeline.

## Problem Statement

sc2egset has 6 data objects. Two tables (replay_players_raw,
replays_meta_raw) are clearly essential but currently separate — a joined
VIEW is needed. map_aliases_raw (104K rows) is a translation lookup whose
necessity depends on whether map names are already English. Three event
views (670M+ rows total) contain in-game action data that is by definition
unavailable at pre-game prediction time.

This step produces the `matches_flat` VIEW SQL and the formal pipeline
scope definition that 01_04 will consume.

## Execution Steps

### T01 -- Core table cross-inventory and join verification

**Objective:** Unified column inventory of replay_players_raw (25 cols) and
replays_meta_raw (9 top-level, 17 struct-flat fields). Verify 1:2 join.

**Instructions:**
1. DESCRIBE both tables.
2. Verify join cardinality: distinct filename count from replay_players_raw
   should equal replays_meta_raw row count (22,390). Zero orphans both ways.
3. Verify 1:2 relationship for true_1v1 replays.
4. Produce proposed `matches_flat` column list with I3 classifications from
   01_02_04 census `field_classification`. Exclude 5 constant columns and
   ToonPlayerDescMap.

---

### T02 -- map_aliases_raw utility assessment

**Objective:** Determine if map_aliases_raw is needed for map name normalization.

**Instructions:**
1. Query distinct `metadata.mapName` values from replays_meta_raw (188 expected).
2. Query distinct `english_name` and `foreign_name` from map_aliases_raw.
3. Cross-reference: how many replay map names appear in english_name? In foreign_name?
4. Inspect any unmatched map names.
5. Verdict: CONDITIONAL (not needed if map names already English) or KEEP.

---

### T03 -- Event views scope ruling

**Objective:** Formally rule event views OUT of the pre-game pipeline.

**Instructions:**
1. Confirm row counts (cite schema YAML if full COUNT is too slow).
2. Verify no pre-game events: `SELECT MIN(loop) FROM tracker_events_raw`.
   Loop > 0 means events begin after game start.
3. Formal I3 ruling: event data is in-game/post-game by definition.
4. Verdict: DEFER for all 3 views. They remain in DB for optional Phase 02
   in-game comparison work.

---

### T04 -- In-game feature potential survey (informational)

**Objective:** Enumerate tracker_events event types for Phase 02 planning.

**Instructions:**
1. `SELECT evtTypeName, COUNT(*) FROM tracker_events_raw GROUP BY evtTypeName ORDER BY COUNT(*) DESC`.
2. Annotate known feature-relevant types: UnitBorn (army), PlayerStats
   (economy), UnitDied (losses), Upgrade (tech).
3. Explicit note: informational only, no pipeline decision.

---

### T05 -- matches_flat VIEW SQL and artifact assembly

**Objective:** Produce the exact VIEW SQL and final artifacts.

**Instructions:**
1. Construct `matches_flat` VIEW SQL joining replay_players_raw with
   struct-extracted replays_meta_raw fields via filename.
2. Column retention list with I3 classifications.
3. Assemble JSON artifact:
   ```json
   {
     "tables": {
       "replay_players_raw": {"verdict": "KEEP", ...},
       "replays_meta_raw": {"verdict": "KEEP", ...},
       "map_aliases_raw": {"verdict": "CONDITIONAL", ...},
       "game_events_raw": {"verdict": "DEFER", ...},
       "tracker_events_raw": {"verdict": "DEFER", ...},
       "message_events_raw": {"verdict": "DEFER", ...}
     },
     "matches_flat_view_sql": "...",
     "pipeline_scope": ["replay_players_raw", "replays_meta_raw"],
     "deferred_tables": ["game_events_raw", "tracker_events_raw", "message_events_raw"],
     "sql_queries": { ... }
   }
   ```
4. Write JSON and MD artifacts.

---

### T06 -- ROADMAP and status updates

Add 01_03_03 to ROADMAP.md, STEP_STATUS.yaml, research_log.md.

---

## File Manifest

| File | Action |
|------|--------|
| `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_03_table_utility.py` | Create |
| `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_03_table_utility.ipynb` | Create |
| `src/.../sc2egset/reports/artifacts/.../01_03_03_table_utility.json` | Create |
| `src/.../sc2egset/reports/artifacts/.../01_03_03_table_utility.md` | Create |
| `src/.../sc2egset/reports/ROADMAP.md` | Update |
| `src/.../sc2egset/reports/STEP_STATUS.yaml` | Update |
| `src/.../sc2egset/reports/research_log.md` | Update |

## Gate Condition

- JSON artifact with verdicts for all 6 data objects
- `pipeline_scope` == `["replay_players_raw", "replays_meta_raw"]`
- `deferred_tables` contains all 3 event views
- `matches_flat_view_sql` is a non-empty string
- Column retention list with I3 class for every column
- All SQL queries in `sql_queries` dict (I6)
- Notebook executes without error
- STEP_STATUS shows 01_03_03 complete

## Out of scope

- VIEW creation in DuckDB (01_04 will execute the SQL)
- Event feature engineering (Phase 02)
- map_aliases_raw integration (Phase 02 if needed)
- Data cleaning decisions (01_04)
