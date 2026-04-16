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
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/matches_raw.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/players_raw.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/overviews_raw.yaml
critique_required: true
research_log_ref: null
---

# Plan: aoestats 01_03_03 -- Table Utility Assessment

## Scope

Empirical assessment of all 3 raw tables (matches_raw, players_raw,
overviews_raw) for prediction pipeline utility. Run diagnostic queries
to quantify column overlap, join integrity, ELO redundancy between
match-level and player-level ratings, overviews_raw content (including
all STRUCT arrays and the replay_summary_raw column), and produce
evidence-backed verdicts. All conclusions emerge from query results.

## Problem Statement

aoestats has a split architecture: match-level data in matches_raw (30.7M
rows) and player-level data in players_raw (107.6M rows). The target
variable (`winner`) is in players_raw, the temporal anchor
(`started_timestamp`) is in matches_raw. Both appear essential but this
must be formally demonstrated. overviews_raw (1 row) is a singleton
reference table whose utility is uncertain. Additionally,
replay_summary_raw is a massive VARCHAR JSON column in players_raw that
requires explicit assessment.

The 01_02_07 multivariate EDA found near-perfect ELO redundancy (rho > 0.98)
between avg_elo, team_0_elo, team_1_elo, and old_rating. This step
quantifies whether match-level ELOs are deterministically derived from
player-level ratings in 1v1 matches.

## Assumptions & unknowns

- **Assumption:** All 3 raw tables are loaded and queryable in DuckDB
  (verified by 01_02_02 completion).
- **Unknown:** Whether avg_elo is exactly (team_0_elo + team_1_elo) / 2
  or an approximation. Resolved by: T03 queries.
- **Unknown:** Whether replay_summary_raw contains useful structured data
  or is predominantly empty. Resolved by: T04 query.
- **Unknown:** Whether overviews_raw.patches provides useful patch-date
  mapping not available elsewhere. Resolved by: T04 queries.

## Literature context

No external literature required. This is an internal data characterization
step. I3 (temporal discipline) and I6 (reproducibility) are the governing
invariants.

## Execution Steps

### T01 -- Column overlap and exclusive contributions

**Objective:** Build the definitive column-by-table matrix showing which
columns are exclusive to each table and which are shared.

**Instructions:**
1. Create notebook `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_03_table_utility.py`.
2. DESCRIBE both matches_raw and players_raw. Compute set intersection and set difference of column names.
3. Confirm where `winner` exists (which table(s)).
4. Confirm where `started_timestamp` exists (which table(s)).
5. Confirm `game_id` is present in both tables (the shared join key).
6. Print formatted summary: exclusive columns per table, shared columns.

**Verification:**
- Column overlap matrix printed.
- game_id confirmed as join key.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_03_table_utility.py`
- `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_03_table_utility.ipynb`

**Read scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/matches_raw.yaml`
- `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/players_raw.yaml`

---

### T02 -- Join integrity and multiplicity

**Objective:** Profile the game_id join between matches_raw and players_raw.
Cross-validate against 01_03_01 and 01_03_02 findings.

**Instructions:**
1. **Orphan counts in both directions** (anti-join):
