---
category: A
branch: feat/table-utility-assessment
date: 2026-04-16
planner_model: claude-opus-4-6
dataset: aoestats
phase: "01"
pipeline_section: "01_03 -- Systematic Data Profiling"
invariants_touched: [I3, I6, I7, I8, I9]
source_artifacts:
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/matches_raw.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/players_raw.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/overviews_raw.yaml
critique_required: true
research_log_ref: null
---

# Plan: aoestats 01_03_03 -- Table Utility Assessment

## Scope

Systematically evaluate all 3 raw tables (matches_raw, players_raw,
overviews_raw) for prediction pipeline utility. Produce per-table verdicts,
quantify ELO redundancy between match-level and player-level ratings,
inspect overviews_raw content, and define the recommended join SQL.

## Problem Statement

aoestats has a split architecture: match-level data in matches_raw (30.7M
rows) and player-level data in players_raw (107.6M rows). The target
variable (`winner`) is in players_raw, the temporal anchor
(`started_timestamp`) is in matches_raw. Both are essential — but this must
be formally demonstrated. overviews_raw (1 row) is a singleton reference
table whose utility is uncertain.

The 01_02_07 multivariate EDA found near-perfect ELO redundancy (rho > 0.98)
between avg_elo, team_0_elo, team_1_elo, and old_rating. This step
quantifies whether match-level ELOs are deterministically derived from
player-level ratings in 1v1 matches.

## Execution Steps

### T01 -- Column overlap and exclusive contributions

**Objective:** Build the definitive column-by-table matrix showing which
columns are exclusive to each table.

**Instructions:**
1. DESCRIBE both tables. Compute set intersection and difference.
2. Confirm `winner` exists ONLY in players_raw.
3. Confirm `started_timestamp` exists ONLY in matches_raw.
4. Confirm `game_id` is the shared join key.
5. Print formatted summary: exclusive columns per table, shared columns.

---

### T02 -- Join integrity and multiplicity

**Objective:** Profile the game_id join. Cross-validate against 01_03_01/02.

**Instructions:**
1. Orphan counts in both directions (anti-join).
   Cross-check: matches_without_players = 212,890 (from 01_03_01).
2. Multiplicity distribution (player count per game_id).
3. True 1v1 count (actual_player_count = 2). Cross-check 01_03_02.

---

### T03 -- ELO redundancy quantification

**Objective:** Determine whether match-level ELOs are deterministically
derived from player-level old_rating in 1v1 matches.

**Instructions:**
1. Sample 100K 1v1 rows via RESERVOIR join.
2. Spearman correlation matrix: avg_elo, team_0_elo, team_1_elo, old_rating.
3. Residual analysis: `old_rating - team_0_elo` for team=0 players,
   `old_rating - team_1_elo` for team=1 players. Report mean/std.
4. If residual std ≈ 0 → match-level ELOs are derived, not independent.
5. Recommendation: retain only old_rating for 1v1 (the others add no
   information and introduce multicollinearity).

---

### T04 -- overviews_raw content inspection

**Objective:** Enumerate STRUCT array contents, check redundancy with
players_raw, assess patch date utility.

**Instructions:**
1. Read the single row. Print `last_updated`, `total_match_count`.
2. UNNEST `civs` array. Compare against `SELECT DISTINCT civ FROM players_raw`.
3. UNNEST `openings` array. Compare against `SELECT DISTINCT opening FROM players_raw`.
4. UNNEST `patches` array. Print all 19 with `release_date`.
   Assess: useful for `patch_age_at_match_time` feature in Phase 02?
5. UNNEST `groupings`. Determine if aoestats.io's own bins or game-defined.
6. Inspect `changelog` — confirm it's site changelog, not game changelog.
7. Per-component verdict: {name, redundant_with, verdict, reasoning}.

---

### T05 -- Verdicts, column retention, and recommended join SQL

**Objective:** Synthesize T01-T04 into formal verdicts and artifacts.

**Instructions:**
1. Assign verdicts:
   - matches_raw: KEEP (temporal anchor, match context)
   - players_raw: KEEP (target, player identity, pre-game rating)
   - overviews_raw: DROP (civs/openings redundant, patches extractable if needed)
2. Column retention list with I3 class for every column.
3. Recommended 1v1 join SQL:
   ```sql
   SELECT m.game_id, m.started_timestamp, m.map, m.leaderboard,
          m.num_players, m.patch, m.avg_elo, m.team_0_elo, m.team_1_elo,
          p.profile_id, p.team, p.civ, p.old_rating,
          p.match_rating_diff, p.winner
   FROM matches_raw m
   JOIN players_raw p ON m.game_id = p.game_id
   WHERE m.num_players = 2
   ```
4. Expected row count for 1v1 join.
5. Write JSON and MD artifacts.

---

### T06 -- ROADMAP and status updates

Add 01_03_03 to ROADMAP.md, STEP_STATUS.yaml, research_log.md.

---

## File Manifest

| File | Action |
|------|--------|
| `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_03_table_utility.py` | Create |
| `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_03_table_utility.ipynb` | Create |
| `src/.../aoestats/reports/artifacts/.../01_03_03_table_utility.json` | Create |
| `src/.../aoestats/reports/artifacts/.../01_03_03_table_utility.md` | Create |
| `src/.../aoestats/reports/ROADMAP.md` | Update |
| `src/.../aoestats/reports/STEP_STATUS.yaml` | Update |
| `src/.../aoestats/reports/research_log.md` | Update |

## Gate Condition

- JSON artifact with verdicts for all 3 tables
- `pipeline_scope` == `["matches_raw", "players_raw"]`
- `excluded_tables` == `["overviews_raw"]`
- ELO redundancy section with Spearman matrix and residual stats
- Recommended join SQL in artifact
- All SQL queries in `sql_queries` dict (I6)
- Notebook executes without error
- STEP_STATUS shows 01_03_03 complete

## Out of scope

- Cleaning decisions (01_04)
- Feature engineering (Phase 02)
- ELO column drop execution (01_04 decision)
- overviews_raw patch extraction (Phase 02 if needed)
