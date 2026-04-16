---
category: A
branch: feat/sc2egset-01-03-04-event-profiling
date: 2026-04-16
planner_model: claude-opus-4-6
dataset: sc2egset
phase: "01"
pipeline_section: "01_03 -- Systematic Data Profiling"
invariants_touched: [I3, I6, I9]
source_artifacts:
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_03_table_utility.json
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/game_events_raw.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/tracker_events_raw.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/message_events_raw.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md
critique_required: true
research_log_ref: null
---

# Plan: sc2egset 01_03_04 -- Event Table Profiling

## Scope

Deep structural profiling of the three event views (tracker_events_raw 62M rows,
game_events_raw 608M rows, message_events_raw 52K rows). These are unique to
sc2egset -- neither AoE2 dataset has in-game event logs. The thesis may include
an in-game prediction comparison per Invariant #8. This step profiles event
structure to enable informed Phase 02 scope decisions. No features extracted,
no tables created (I9).

## Problem Statement

01_03_03 classified all event views as IN_GAME_ONLY but deferred deep profiling.
Current knowledge gaps: (a) event type distributions only partially known from
the census top-5/bottom-5, (b) per-replay event density unknown, (c) event_data
JSON schema never sampled per event type, (d) PlayerStats periodicity unknown
(fixed interval or variable?), (e) UnitBorn unit-type diversity unknown. Without
this, Phase 02 in-game feature design is impossible.

## Assumptions & unknowns

- **Assumption:** Event views remain stable since 01_02_03 (no schema changes).
- **Assumption:** [Critique fix: performance baseline] Census GROUP BY
  evtTypeName on game_events_raw completed in 0.9s. Similar aggregation queries
  will complete in seconds, not minutes.
- **Unknown:** PlayerStats periodicity -- resolves by: T01 analysis.
- **Unknown:** UnitBorn unit-type diversity -- resolves by: T01 query.

## Literature context

SC2EGSet (Bialecki et al. 2023) documents three event streams from s2protocol.
[Critique fix: naming convention] The dataset uses SHORT event type names
(`UnitBorn`, `PlayerStats`, `CameraUpdate`) not NNet-prefixed names. JSON field
names also use short form (`unitTypeName` not `m_unitTypeName`). Confirmed from
01_02_04 census artifact.

## Hardware: Mac Pro M4 Max, 36GB RAM, 14 CPUs

## Execution Steps

### T01 -- Tracker Events Deep Profile (PRIMARY, 62M rows)

**Instructions:**

1. [Critique fix: ROADMAP entry FIRST] Amend ROADMAP.md to add 01_03_04 step
   definition BEFORE any notebook execution.

2. Create notebook `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_04_event_profiling.py`.

3. Event type distribution (all 10 types, SHORT names):
   ```sql
   SELECT evtTypeName, COUNT(*) AS cnt,
          ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 4) AS pct
   FROM tracker_events_raw
   GROUP BY evtTypeName ORDER BY cnt DESC
   ```

4. Per-replay event density:
   ```sql
   SELECT filename, COUNT(*) AS n_events
   FROM tracker_events_raw GROUP BY filename
   ```
   Then Python stats (mean, median, p05, p25, p75, p95, min, max).

5. Per-replay by type (replay coverage per event type):
   ```sql
   SELECT evtTypeName,
          COUNT(DISTINCT filename) AS n_replays,
          ROUND(100.0 * COUNT(DISTINCT filename) / 22390, 2) AS replay_coverage_pct,
          COUNT(*) AS total_events,
          ROUND(1.0 * COUNT(*) / COUNT(DISTINCT filename), 1) AS mean_per_replay
   FROM tracker_events_raw GROUP BY evtTypeName ORDER BY total_events DESC
   ```

6. Temporal distribution (1000-loop buckets):
   ```sql
   SELECT (loop / 1000) * 1000 AS loop_bucket, COUNT(*) AS cnt
   FROM tracker_events_raw GROUP BY loop_bucket ORDER BY loop_bucket
   ```

7. event_data schema sampling: top 5 types by count, LIMIT 5 rows each.
   Parse JSON keys in Python.

8. PlayerStats periodicity:
   ```sql
   SELECT filename, loop,
          loop - LAG(loop) OVER (PARTITION BY filename ORDER BY loop) AS gap
   FROM tracker_events_raw
   WHERE evtTypeName = 'PlayerStats'
   ```
   Then Python: gap stats (min, max, mean, median, n_distinct_gaps, mode).

9. [Critique fix: field name] UnitBorn unit-type diversity using `unitTypeName`:
   ```sql
   SELECT json_extract_string(event_data, '$.unitTypeName') AS unit_type,
          COUNT(*) AS cnt
   FROM tracker_events_raw
   WHERE evtTypeName = 'UnitBorn'
   GROUP BY unit_type ORDER BY cnt DESC LIMIT 50
   ```

---

### T02 -- Game Events Moderate Profile (SECONDARY, 608M rows)

**Instructions:**

1. Event type distribution (all 23 types, SHORT names):
   [Critique fix: performance] Census ran this in 0.9s. Expect <2s.
   ```sql
   SELECT evtTypeName, COUNT(*) AS cnt,
          ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 4) AS pct
   FROM game_events_raw GROUP BY evtTypeName ORDER BY cnt DESC
   ```

2. CameraUpdate dominance and non-CameraUpdate breakdown from step 1 results.

3. [Critique fix: TABLESAMPLE method] Per-replay density (10% BERNOULLI):
   ```sql
   SELECT filename, COUNT(*) AS n_events
   FROM game_events_raw TABLESAMPLE BERNOULLI(10)
   GROUP BY filename
   ```
   Caveat: BERNOULLI samples rows, so per-replay counts are deflated.

4. event_data sampling: `Cmd` and `SelectionDelta`, LIMIT 5 each, parse keys.

---

### T03 -- Message Events Light Profile (52K rows)

1. Event type distribution (3 types: `Chat`, `Ping`, third).
2. Coverage: `COUNT(DISTINCT filename)` -- confirm ~22,260.
3. event_data sample: 10 rows, parse JSON keys.

---

### T04 -- Artifact Generation

1. JSON: `01_03_04_event_profiling.json` (all three view profiles + sql_queries)
2. MD: `01_03_04_event_profiling.md` (summary tables, key findings)
3. Update STEP_STATUS.yaml (01_03_04 = complete)
4. Update research_log.md

---

## Gate Condition

- JSON artifact exists with keys for all three event views
- [Critique fix: exact counts] tracker = 62,003,411; game = 608,618,823 (exact); message = 52,167
- PlayerStats periodicity analysis non-empty
- [Critique fix: diversity threshold] UnitBorn: at least 20 distinct unit types
  (SC2 has 3 races with 15+ units each; <20 indicates parsing error)
- event_data JSON key sets for 5+ tracker types, 2+ game types
- All SQL in `sql_queries` dict (I6)
- STEP_STATUS shows 01_03_04 complete
- ROADMAP.md contains 01_03_04 step definition

## Performance estimates

[Critique fix: revised using actual census timings]

| Query | Rows | Expected | Evidence |
|-------|------|----------|----------|
| Tracker type distribution | 62M | <1s | Census: 0.1s |
| Tracker per-replay density | 62M | <1s | Census: 0.33s |
| PlayerStats periodicity | ~4.6M | <5s | Window on subset |
| UnitBorn unit types | ~22M | <30s | json_extract + GROUP BY |
| Game type distribution | 608M | <2s | Census: 0.9s |
| Game per-replay (10% sample) | ~60M | <10s | Sampling + GROUP BY |
| Message queries | 52K | <0.1s | Census: <0.03s |
| **Total** | | **<1 min** | |

## Out of scope

- Feature extraction (Phase 02)
- Full event_data parsing at scale
- Cleaning decisions (01_04)
- New DuckDB tables/views
- Visualizations

## Critique fix summary

| Fix | Severity | Description |
|-----|----------|-------------|
| ROADMAP entry | BLOCKER | Added as FIRST action of T01, not deferred to T04 |
| Event naming | WARNING | All SQL uses SHORT names (UnitBorn not NNet.Replay.Tracker.SUnitBornEvent) |
| json_extract field | WARNING | Uses $.unitTypeName (not m_unitTypeName) |
| TABLESAMPLE method | WARNING | Specifies BERNOULLI explicitly |
| Performance table | WARNING | Revised using census 01_02_04 actual timings |
| Gate: exact counts | NOTE | game_events_raw requires exact 608,618,823 |
| Gate: UnitBorn threshold | NOTE | Raised from 3 to 20 distinct types |
