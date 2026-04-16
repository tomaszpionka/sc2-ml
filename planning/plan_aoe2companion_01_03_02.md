---
category: A
branch: feat/census-pass3
date: 2026-04-16
planner_model: claude-opus-4-6
dataset: aoe2companion
phase: "01"
pipeline_section: "01_03 -- Systematic Data Profiling"
invariants_touched: [3, 6, 7, 9]
critique_required: true
source_artifacts:
  - "reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
  - "reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json"
  - "data/db/db.duckdb (matches_raw)"
research_log_ref: "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md"
---

# Plan: aoe2companion Step 01_03_02 -- True 1v1 Match Identification

## Scope

**Phase/Step:** 01 / 01_03_02
**Branch:** feat/census-pass3
**Action:** CREATE (step 01_03_02 does not exist in ROADMAP.md; this plan defines it)
**Predecessor:** 01_03_01 (Systematic Data Profiling -- complete, artifacts on disk)

Identify the full population of genuine 1v1 matches in `matches_raw`
(277,099,059 rows) regardless of ranked or unranked status. This step
answers a precise structural question: which matchId values have exactly 2
active (human) player rows, exactly 2 distinct teams, and a complementary
won outcome? The result is a structured JSON artifact documenting the 1v1
population size, its overlap and divergence from the leaderboard-based proxy
(`leaderboard IN ('rm_1v1', 'qp_rm_1v1')`), and the distribution of
edge cases.

This step does NOT create any derived table, view, or cleaned subset. It
is a profiling step (I9) that produces observations and quantified
populations for the 01_04 cleaning rules to consume.

**Why this step matters:** Prior EDA (01_02_04 through 01_03_01) used
`leaderboard IN ('rm_1v1', 'qp_rm_1v1')` as a proxy for 1v1 matches,
capturing 61.1M rows (22.0%). However, this proxy conflates two assumptions:
(a) that every `rm_1v1`/`qp_rm_1v1` match is a true 2-player match, and
(b) that no 1v1 matches exist outside these leaderboards (e.g., `unranked`,
`ew_1v1`, `ror_1v1`, `dm_1v1`). Before 01_04 (cleaning) can define the
analytical cohort, both assumptions must be tested empirically.

## Problem Statement

### Schema-derived findings

The `matches_raw` table is a **player-match table**: each row represents one
player in one match. The match-level grouping key is `matchId` (INTEGER),
with cardinality 61,799,126 vs 277,099,059 total rows -- an average of
~4.48 rows per matchId across all leaderboards.

Key columns for 1v1 identification (from 01_03_01 systematic profile):

| Column | Type | Null % | Cardinality | Role |
|--------|------|--------|-------------|------|
| matchId | INTEGER | 0.0% | 61,799,126 | Match grouping key |
| profileId | INTEGER | 0.0% | 3,387,273 | Player identity; -1 = anonymous/AI |
| status | VARCHAR | 0.0% | 2 | 'player' (95.33%) vs 'ai' (4.67%) |
| team | INTEGER | 4.9% | 31 | Team assignment (1, 2, ..., 255) |
| won | BOOLEAN | 4.69% | 2 | Match outcome (true/false/NULL) |
| leaderboard | VARCHAR | 0.0% | 22 | Queue type (rm_1v1, unranked, ...) |
| slot | INTEGER | 0.0% | 9 | Player slot (0-7) |

### Existing match-structure evidence from 01_02_04

The census already computed `match_structure_by_leaderboard`, which confirms
that several leaderboards have avg_rows_per_match = 2.0:

| Leaderboard | Distinct Matches | Total Rows | Avg Rows/Match |
|-------------|-----------------|------------|----------------|
| rm_1v1 | 26,847,572 | 53,694,523 | 2.0 |
| qp_rm_1v1 | 3,688,676 | 7,377,276 | 2.0 |
| ew_1v1 | 972,000 | 1,943,971 | 2.0 |
| rm_1v1_console | 800,244 | 1,600,477 | 2.0 |
| ew_1v1_redbullwololo | 297,445 | 594,890 | 2.0 |
| dm_1v1 | 47,254 | 94,508 | 2.0 |
| qp_ew_1v1 | 24,739 | 49,477 | 2.0 |
| ror_1v1 | 7,888 | 15,775 | 2.0 |
| ew_1v1_console | 3,761 | 7,522 | 2.0 |
| ew_1v1_redbullwololo_console | 325 | 650 | 2.0 |
| unranked | 18,783,620 | 78,254,732 | 4.17 |

The 1v1 leaderboards show perfect avg=2.0, but the `unranked` leaderboard
averages 4.17 -- meaning it mixes 1v1 and team games. Some matchIds under
`unranked` will have exactly 2 rows and should be identified.

### Duplicate complication

01_03_01 found 3,589,428 (matchId, profileId) duplicate groups containing
12,401,433 rows. Sample duplicates show profileId = -1 (anonymous/AI). True
1v1 identification must account for these duplicates -- either by counting
distinct profileId per matchId or by deduplicating first. This step profiles
both approaches.

### Four questions this step answers

**Q1:** How many matchIds have exactly 2 rows in matches_raw? How does this
compare to exactly 2 *distinct* profileIds, exactly 2 rows with `status = 'player'`,
and exactly 2 rows with `status = 'player'` AND `won IS NOT NULL`?

**Q2:** What is the `COUNT(*) GROUP BY matchId` distribution across all
matches? (i.e., histogram of 1-row, 2-row, 3-row, ..., 8-row matches)

**Q3:** Among the ~30.5M 1v1-leaderboard matches (rm_1v1 + qp_rm_1v1),
are there any that do NOT have exactly 2 player rows? Conversely, among
non-1v1 leaderboards, how many matchIds DO have exactly 2 player rows?

**Q4:** For true 1v1 matches (exactly 2 player rows), what is the won-
complement consistency? (Both players have won values, exactly one true and
one false.) What fraction have NULL won (no decisive outcome)?

## Assumptions & Unknowns

- **Assumption:** `matchId` is the correct match-level grouping key. The census
  shows 61.8M distinct values, and the 01_02_04 `match_structure_by_leaderboard`
  analysis already grouped by matchId to compute avg_rows_per_match. This is
  confirmed behavior.
- **Assumption:** `status = 'player'` identifies human participants. AI opponents
  (`status = 'ai'`, 4.67% of rows) should be excluded from "active player" counts
  for 1v1 identification, since the thesis prediction task is human vs human.
- **Assumption:** `profileId = -1` represents anonymous or placeholder entries.
  01_03_01 duplicates show these as the most common duplicate source. They
  interact with the `status` column -- need to verify whether profileId = -1
  rows are exclusively `status = 'ai'` or also appear for `status = 'player'`.
- **Unknown:** Exact overlap between "leaderboard is 1v1" and "matchId has
  exactly 2 player rows". The census avg_rows_per_match = 2.0 for 1v1 leaderboards
  is encouraging but not proof that every individual match is 2-row. This step
  measures the exact match.
- **Unknown:** How many `unranked` matchIds have exactly 2 player rows. The
  unranked leaderboard has 18.8M distinct matches; some fraction will be 1v1.
- **Unknown:** How many matches have exactly 2 rows but one or both have
  `won IS NULL` (no decisive outcome). This affects the usable prediction
  target population.
- **Unknown:** Whether `team` values are consistent within true 1v1 matches
  (team 1 vs team 2) or have anomalies (same team, NULL team, team > 2).

## Literature Context

True 1v1 identification in community match datasets is a standard data
cleaning prerequisite in RTS prediction literature. Elo-based prediction
models (Herbrich et al. 2006, Glickman 1999) assume a clean 1v1 population.
The aoe2companion dataset is community-sourced, meaning it includes AI
games, team games, and spectator/placeholder rows alongside genuine 1v1
human matches. Failing to isolate the 1v1 population before feature
engineering would produce training data contaminated with team dynamics
and AI opponent patterns.

The approach -- grouping by match key, counting active participants, and
cross-validating with leaderboard metadata -- follows the data profiling
methodology of CRISP-DM Phase 2 (Chapman et al. 2000) and the Data
Exploration Manual Section 3 (structural integrity checks).

## Execution Steps

### T01 -- ROADMAP and STEP_STATUS Patch

**Objective:** Register step 01_03_02 in ROADMAP.md and STEP_STATUS.yaml.

**Instructions:**
1. Open `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`.
2. Insert the following Step 01_03_02 YAML block after the Step 01_03_01 block.
   Wrap it in a `### Step 01_03_02` heading.

```yaml
step_number: "01_03_02"
name: "True 1v1 Match Identification"
description: "Identify the full population of genuine 1v1 matches in matches_raw regardless of leaderboard. Profile the matchId grouping structure: rows-per-match distribution, true 1v1 criteria (exactly 2 human players, complementary won outcome), overlap with leaderboard-based 1v1 proxy, and edge cases (AI rows, NULL won, duplicate profileId=-1). Read-only profiling -- no tables or views created."
phase: "01 -- Data Exploration"
pipeline_section: "01_03 -- Systematic Data Profiling"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 3"
dataset: "aoe2companion"
question: "Among all 61.8M distinct matchIds, which ones are genuine 1v1 matches (exactly 2 human players)? How does this set compare to the leaderboard-based 1v1 proxy? What edge cases exist?"
method: "DuckDB aggregate queries over matches_raw. GROUP BY matchId with HAVING-based structural criteria. Cross-tabulation with leaderboard. Won complement analysis. All SQL verbatim in artifact (I6)."
stratification: "Full table for aggregate counts. Leaderboard-stratified for overlap analysis."
predecessors:
  - "01_03_01"
notebook_path: "sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_02_true_1v1_identification.py"
inputs:
  duckdb_tables:
    - "matches_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
    - "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json"
  report: "artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.md"
gate:
  artifact_check: "01_03_02_true_1v1_profile.json and .md exist and are non-empty."
  continue_predicate: "JSON contains rows_per_match_distribution, true_1v1_criteria, leaderboard_overlap, and won_complement_analysis keys."
  halt_predicate: "DuckDB queries fail on matches_raw."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "All SQL queries written verbatim to JSON and MD artifacts."
  - number: "7"
    how_upheld: "1v1 criteria (exactly 2 human player rows) derived empirically from match structure, not assumed. Thresholds from census data."
  - number: "9"
    how_upheld: "Read-only profiling. No tables created. No cleaning decisions made. Findings feed 01_04."
  - number: "3"
    how_upheld: "No temporal features computed. Only structural grouping analysis."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data"
research_log_entry: "Required on completion."
```

3. Open `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml`.
4. Add entry:
```yaml
  "01_03_02":
    name: "True 1v1 Match Identification"
    pipeline_section: "01_03"
    status: not_started
```

**Verification:**
- ROADMAP.md contains Step 01_03_02 YAML block after 01_03_01.
- STEP_STATUS.yaml contains `01_03_02` entry with `status: not_started`.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml`

---

### T02 -- Create Notebook Skeleton

**Objective:** Create the 1v1 identification notebook with imports, DuckDB
connection (read-only), prior artifact loads, path constants, and sql_queries
dict.

**Instructions:**
1. Create `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`
   with jupytext percent-format header (same kernel metadata as 01_03_01).

**Cell 1 -- markdown header:**
```
# Step 01_03_02 -- True 1v1 Match Identification: aoe2companion
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_03 -- Systematic Data Profiling
# **Dataset:** aoe2companion
# **Question:** Among all 61.8M distinct matchIds, which ones are genuine
#   1v1 matches (exactly 2 human players)? How does this set compare to
#   the leaderboard-based 1v1 proxy? What edge cases exist?
# **Invariants applied:**
#   - #6 (reproducibility -- all SQL queries written verbatim to artifacts)
#   - #7 (no magic numbers -- criteria derived from census data)
#   - #9 (step scope -- profiling only, no cleaning decisions)
#   - #3 (temporal discipline -- no temporal features computed)
# **Predecessor:** 01_03_01 (Systematic Data Profiling)
# **Step scope:** Structural profiling. Read-only. No DuckDB writes.
# **Outputs:** JSON profile, MD report
```

**Cell 2 -- imports:**
```python
import json
from pathlib import Path

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from rts_predict.common.notebook_utils import (
    get_notebook_db,
    get_reports_dir,
    setup_notebook_logging,
)

logger = setup_notebook_logging()
matplotlib.use("Agg")
```

**Cell 3 -- DuckDB connection (read-only):**
```python
db = get_notebook_db("aoe2", "aoe2companion")
con = db.con
print("Connected via get_notebook_db: aoe2 / aoe2companion")
```

**Cell 4 -- load prior artifacts and path setup:**
```python
reports_dir = get_reports_dir("aoe2", "aoe2companion")
census_path = reports_dir / "artifacts" / "01_exploration" / "02_eda" / "01_02_04_univariate_census.json"
profile_path = reports_dir / "artifacts" / "01_exploration" / "03_profiling" / "01_03_01_systematic_profile.json"
output_dir = reports_dir / "artifacts" / "01_exploration" / "03_profiling"
output_dir.mkdir(parents=True, exist_ok=True)

with open(census_path) as f:
    census = json.load(f)
with open(profile_path) as f:
    profile = json.load(f)

total_rows = census["matches_raw_total_rows"]
print(f"Census loaded: total_rows = {total_rows:,}")
print(f"Profile loaded: {profile['total_columns']} columns profiled")
```

**Cell 5 -- verify prerequisite keys from census:**
```python
required_keys = [
    "matches_raw_total_rows",
    "match_structure_by_leaderboard",
    "won_consistency_2row",
    "won_distribution",
]
for k in required_keys:
    assert k in census, f"Missing census key: {k}"
print(f"All {len(required_keys)} required census keys present")

# Print census match_structure_by_leaderboard summary
for entry in census["match_structure_by_leaderboard"]:
    print(f"  {entry['leaderboard']}: {entry['distinct_matches']:,} matches, "
          f"avg {entry['avg_rows_per_match']:.2f} rows/match")
```

**Cell 6 -- initialize sql_queries dict:**
```python
sql_queries = {}

print(f"Total rows: {total_rows:,}")
```

**Verification:**
- Notebook imports and runs through setup without error.
- Census and profile JSONs load successfully.
- All 4 required census keys present.
- `match_structure_by_leaderboard` summary prints correctly.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T03 -- Rows-Per-Match Distribution (Q2)

**Objective:** Compute the full distribution of how many rows each matchId
has (1-row, 2-row, 3-row, ..., N-row). This is the foundation for all
subsequent 1v1 identification queries.

**Cell 7 -- rows-per-match distribution (all rows, exact):**
```python
rows_per_match_sql = """
SELECT
    rows_per_match,
    COUNT(*) AS n_matches,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_matches,
    SUM(rows_per_match) AS total_rows_in_group
FROM (
    SELECT matchId, COUNT(*) AS rows_per_match
    FROM matches_raw
    GROUP BY matchId
)
GROUP BY rows_per_match
ORDER BY rows_per_match
"""
sql_queries["rows_per_match_distribution"] = rows_per_match_sql
print("Computing rows-per-match distribution (full table, exact)...")
df_rpm = con.execute(rows_per_match_sql).fetchdf()
print(f"\nRows-per-match distribution:")
for _, row in df_rpm.iterrows():
    print(f"  {int(row['rows_per_match'])} rows/match: "
          f"{int(row['n_matches']):,} matches ({row['pct_matches']}%), "
          f"{int(row['total_rows_in_group']):,} total rows")

total_matches = int(df_rpm['n_matches'].sum())
two_row_matches = int(df_rpm.loc[df_rpm['rows_per_match'] == 2, 'n_matches'].sum())
print(f"\nTotal distinct matchIds: {total_matches:,}")
print(f"matchIds with exactly 2 rows: {two_row_matches:,} "
      f"({two_row_matches * 100 / total_matches:.2f}%)")

rows_per_match_distribution = df_rpm.to_dict(orient="records")
```

**Cell 8 -- rows-per-match distribution by status (human vs AI):**
```python
# Count distinct status values per matchId to understand human-vs-AI composition
human_rows_per_match_sql = """
SELECT
    human_players,
    COUNT(*) AS n_matches,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_matches
FROM (
    SELECT matchId,
           COUNT(*) FILTER (WHERE status = 'player') AS human_players,
           COUNT(*) FILTER (WHERE status = 'ai') AS ai_players,
           COUNT(*) AS total_players
    FROM matches_raw
    GROUP BY matchId
)
GROUP BY human_players
ORDER BY human_players
"""
sql_queries["human_rows_per_match_distribution"] = human_rows_per_match_sql
print("Computing human-player-count per match (full table, exact)...")
df_hpm = con.execute(human_rows_per_match_sql).fetchdf()
print(f"\nHuman players per match:")
for _, row in df_hpm.iterrows():
    print(f"  {int(row['human_players'])} human players: "
          f"{int(row['n_matches']):,} matches ({row['pct_matches']}%)")

human_rows_per_match = df_hpm.to_dict(orient="records")
```

**Verification:**
- Distribution sums to ~61.8M total matches (census matchId cardinality).
- 2-row matches are the largest group for 1v1 leaderboards.
- Human player count distribution produced.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T04 -- ProfileId = -1 Investigation

**Objective:** Profile the profileId = -1 population. Are these exclusively
`status = 'ai'`, or do some appear with `status = 'player'`? This informs
whether profileId = -1 can be used as an AI indicator and how it interacts
with the duplicate problem found in 01_03_01.

**Cell 9 -- profileId = -1 census:**
```python
profileId_minus1_sql = """
SELECT
    status,
    COUNT(*) AS n_rows,
    COUNT(DISTINCT matchId) AS n_matches,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM matches_raw), 2) AS pct_all_rows
FROM matches_raw
WHERE profileId = -1
GROUP BY status
ORDER BY n_rows DESC
"""
sql_queries["profileId_minus1_by_status"] = profileId_minus1_sql
print("Profiling profileId = -1 rows...")
df_pid_m1 = con.execute(profileId_minus1_sql).fetchdf()
print(f"\nprofileId = -1 by status:")
for _, row in df_pid_m1.iterrows():
    print(f"  status={row['status']}: {int(row['n_rows']):,} rows "
          f"({row['pct_all_rows']}%), {int(row['n_matches']):,} distinct matches")

profileid_minus1_profile = df_pid_m1.to_dict(orient="records")
```

**Cell 10 -- profileId = -1 rows in 1v1 leaderboards:**
```python
pid_m1_1v1_sql = """
SELECT
    leaderboard,
    COUNT(*) AS n_rows,
    COUNT(DISTINCT matchId) AS n_matches
FROM matches_raw
WHERE profileId = -1
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1', 'ew_1v1', 'dm_1v1',
                       'rm_1v1_console', 'ew_1v1_console', 'ew_1v1_redbullwololo',
                       'ew_1v1_redbullwololo_console', 'qp_ew_1v1', 'ror_1v1')
GROUP BY leaderboard
ORDER BY n_rows DESC
"""
sql_queries["profileId_minus1_in_1v1_leaderboards"] = pid_m1_1v1_sql
print("ProfileId = -1 in 1v1 leaderboards...")
df_pid_1v1 = con.execute(pid_m1_1v1_sql).fetchdf()
if len(df_pid_1v1) == 0:
    print("  No profileId = -1 rows in any 1v1 leaderboard.")
else:
    for _, row in df_pid_1v1.iterrows():
        print(f"  {row['leaderboard']}: {int(row['n_rows']):,} rows, "
              f"{int(row['n_matches']):,} matches")

profileid_minus1_1v1 = df_pid_1v1.to_dict(orient="records")
```

**Verification:**
- profileId = -1 population quantified by status.
- Determined whether profileId = -1 appears in 1v1 leaderboards.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T05 -- True 1v1 Criteria Definition and Counting

**Objective:** Define and apply increasingly strict criteria for "true 1v1"
and count the population at each level. This creates a funnel from the
broadest definition to the strictest.

**Cell 11 -- true 1v1 criteria funnel (single CTE query):**
```python
# Define 1v1 criteria levels:
# Level 1: matchId has exactly 2 total rows
# Level 2: matchId has exactly 2 rows AND both have status='player'
# Level 3: Level 2 AND both have won IS NOT NULL
# Level 4: Level 3 AND won values are complementary (one true, one false)
# Level 5: Level 4 AND both have distinct profileId (profileId != -1)
# Level 6: Level 5 AND both have team IS NOT NULL AND 2 distinct teams

criteria_funnel_sql = """
WITH match_stats AS (
    SELECT
        matchId,
        COUNT(*) AS total_rows,
        COUNT(*) FILTER (WHERE status = 'player') AS human_rows,
        COUNT(*) FILTER (WHERE status = 'ai') AS ai_rows,
        COUNT(*) FILTER (WHERE won IS NOT NULL) AS won_nonnull,
        COUNT(*) FILTER (WHERE won = true) AS won_true,
        COUNT(*) FILTER (WHERE won = false) AS won_false,
        COUNT(DISTINCT profileId) AS distinct_profiles,
        COUNT(DISTINCT profileId) FILTER (WHERE profileId != -1) AS distinct_real_profiles,
        COUNT(DISTINCT team) FILTER (WHERE team IS NOT NULL) AS distinct_teams,
        MIN(profileId) AS min_profileId
    FROM matches_raw
    GROUP BY matchId
)
SELECT
    COUNT(*) AS total_matches,
    COUNT(*) FILTER (WHERE total_rows = 2) AS L1_exactly_2_rows,
    COUNT(*) FILTER (WHERE total_rows = 2 AND human_rows = 2) AS L2_2_humans,
    COUNT(*) FILTER (WHERE total_rows = 2 AND human_rows = 2
                     AND won_nonnull = 2) AS L3_2_humans_won_known,
    COUNT(*) FILTER (WHERE total_rows = 2 AND human_rows = 2
                     AND won_true = 1 AND won_false = 1) AS L4_complementary_won,
    COUNT(*) FILTER (WHERE total_rows = 2 AND human_rows = 2
                     AND won_true = 1 AND won_false = 1
                     AND distinct_real_profiles = 2) AS L5_distinct_profiles,
    COUNT(*) FILTER (WHERE total_rows = 2 AND human_rows = 2
                     AND won_true = 1 AND won_false = 1
                     AND distinct_real_profiles = 2
                     AND distinct_teams = 2) AS L6_distinct_teams
FROM match_stats
"""
sql_queries["criteria_funnel"] = criteria_funnel_sql
print("Computing true 1v1 criteria funnel (single scan over match_stats CTE)...")
df_funnel = con.execute(criteria_funnel_sql).fetchdf().iloc[0]

funnel_levels = {
    "total_matches": int(df_funnel["total_matches"]),
    "L1_exactly_2_rows": int(df_funnel["L1_exactly_2_rows"]),
    "L2_2_human_players": int(df_funnel["L2_2_humans"]),
    "L3_2_humans_won_known": int(df_funnel["L3_2_humans_won_known"]),
    "L4_complementary_won": int(df_funnel["L4_complementary_won"]),
    "L5_distinct_profiles": int(df_funnel["L5_distinct_profiles"]),
    "L6_distinct_teams": int(df_funnel["L6_distinct_teams"]),
}

print(f"\n1v1 Criteria Funnel:")
for level, count in funnel_levels.items():
    pct = count * 100.0 / funnel_levels["total_matches"]
    print(f"  {level}: {count:,} ({pct:.2f}%)")
```

**Cell 11b -- W3 fix: deduplicated funnel (COUNT DISTINCT profileId):**
```python
# W3 fix: Parallel funnel using COUNT(DISTINCT profileId) FILTER (WHERE status='player')
# to quantify matchIds recoverable by deduplication. The 12.4M duplicate rows
# (from 01_03_01) mean some matchIds may have COUNT(*) > 2 but only 2 distinct
# human profileIds.
criteria_funnel_dedup_sql = """
WITH match_stats AS (
    SELECT
        matchId,
        COUNT(*) AS total_rows,
        COUNT(DISTINCT profileId) FILTER (WHERE status = 'player') AS distinct_human_profiles,
        COUNT(DISTINCT profileId) FILTER (WHERE profileId != -1) AS distinct_real_profiles,
        COUNT(*) FILTER (WHERE won IS NOT NULL) AS won_nonnull,
        COUNT(*) FILTER (WHERE won = true) AS won_true,
        COUNT(*) FILTER (WHERE won = false) AS won_false,
        COUNT(DISTINCT team) FILTER (WHERE team IS NOT NULL) AS distinct_teams
    FROM matches_raw
    GROUP BY matchId
)
SELECT
    COUNT(*) AS total_matches,
    COUNT(*) FILTER (WHERE distinct_human_profiles = 2) AS L1_dedup_2_human_profiles,
    COUNT(*) FILTER (WHERE distinct_human_profiles = 2
                     AND won_nonnull >= 2) AS L2_dedup_won_known,
    COUNT(*) FILTER (WHERE distinct_human_profiles = 2
                     AND won_true >= 1 AND won_false >= 1) AS L3_dedup_complementary_won,
    COUNT(*) FILTER (WHERE distinct_human_profiles = 2
                     AND won_true >= 1 AND won_false >= 1
                     AND distinct_real_profiles = 2) AS L4_dedup_distinct_profiles,
    COUNT(*) FILTER (WHERE distinct_human_profiles = 2
                     AND won_true >= 1 AND won_false >= 1
                     AND distinct_real_profiles = 2
                     AND distinct_teams = 2) AS L5_dedup_distinct_teams
FROM match_stats
"""
sql_queries["criteria_funnel_dedup"] = criteria_funnel_dedup_sql
print("Computing true 1v1 criteria funnel -- DEDUPLICATED...")
df_funnel_dedup = con.execute(criteria_funnel_dedup_sql).fetchdf().iloc[0]

funnel_levels_dedup = {
    "total_matches": int(df_funnel_dedup["total_matches"]),
    "L1_dedup_2_human_profiles": int(df_funnel_dedup["L1_dedup_2_human_profiles"]),
    "L2_dedup_won_known": int(df_funnel_dedup["L2_dedup_won_known"]),
    "L3_dedup_complementary_won": int(df_funnel_dedup["L3_dedup_complementary_won"]),
    "L4_dedup_distinct_profiles": int(df_funnel_dedup["L4_dedup_distinct_profiles"]),
    "L5_dedup_distinct_teams": int(df_funnel_dedup["L5_dedup_distinct_teams"]),
}
print(f"\n1v1 Criteria Funnel (DEDUP):")
for level, count in funnel_levels_dedup.items():
    pct = count * 100.0 / funnel_levels_dedup["total_matches"]
    print(f"  {level}: {count:,} ({pct:.2f}%)")

# Delta at L1: matchIds recovered by deduplication
dedup_delta_l1 = funnel_levels_dedup["L1_dedup_2_human_profiles"] - funnel_levels["L1_exactly_2_rows"]
print(f"\nDedup delta at L1: {dedup_delta_l1:+,} matchIds recovered")
dedup_delta = {"L1_delta": dedup_delta_l1, "note": "Positive = matchIds recovered by dedup"}
```

**Cell 12 -- characterize the drop at each funnel level:**
```python
# Compute row-level diagnostics for matches that FAIL each subsequent criterion
# Matches with 2 rows but NOT 2 humans (human+AI 1v1?)
hybrid_1v1_sql = """
WITH match_stats AS (
    SELECT matchId,
           COUNT(*) AS total_rows,
           COUNT(*) FILTER (WHERE status = 'player') AS human_rows,
           COUNT(*) FILTER (WHERE status = 'ai') AS ai_rows
    FROM matches_raw
    GROUP BY matchId
    HAVING COUNT(*) = 2
)
SELECT
    human_rows, ai_rows,
    COUNT(*) AS n_matches
FROM match_stats
GROUP BY human_rows, ai_rows
ORDER BY n_matches DESC
"""
sql_queries["hybrid_1v1_composition"] = hybrid_1v1_sql
print("2-row matches by human/AI composition:")
df_hybrid = con.execute(hybrid_1v1_sql).fetchdf()
for _, row in df_hybrid.iterrows():
    print(f"  humans={int(row['human_rows'])}, ai={int(row['ai_rows'])}: "
          f"{int(row['n_matches']):,} matches")

hybrid_1v1_composition = df_hybrid.to_dict(orient="records")
```

**Verification:**
- Funnel produces monotonically decreasing counts from L1 to L6.
- Total matches matches census matchId cardinality (~61.8M).
- Drop between levels quantified and diagnosed.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T06 -- Leaderboard Overlap Analysis (Q3)

**Objective:** Cross-tabulate the true 1v1 criteria (L4 or L5 -- final
recommended level) with the leaderboard column. Measure: how many
leaderboard=rm_1v1/qp_rm_1v1 matches are NOT true 1v1? How many true 1v1
exist in `unranked` or other non-1v1 leaderboards?

**Cell 12b -- B1 fix (a): leaderboard cardinality per matchId diagnostic:**
```python
# B1 fix (a): Leaderboard cardinality per matchId diagnostic.
# The 01_02_04 census proves sum(per-leaderboard distinct matchIds) = 74.8M > 61.8M total,
# meaning ~13M matchIds appear under 2+ leaderboard values. Quantify this before any
# leaderboard-based aggregation.
leaderboard_cardinality_sql = """
SELECT n_leaderboards, COUNT(*) AS n_matches
FROM (
    SELECT matchId, COUNT(DISTINCT leaderboard) AS n_leaderboards
    FROM matches_raw
    GROUP BY matchId
)
GROUP BY n_leaderboards
ORDER BY n_leaderboards
"""
sql_queries["leaderboard_cardinality_per_match"] = leaderboard_cardinality_sql
print("Leaderboard cardinality per matchId...")
df_lb_card = con.execute(leaderboard_cardinality_sql).fetchdf()
for _, row in df_lb_card.iterrows():
    print(f"  {int(row['n_leaderboards'])} leaderboard(s): {int(row['n_matches']):,} matchIds")
leaderboard_cardinality_per_match = df_lb_card.to_dict(orient="records")
```

**Cell 13 -- leaderboard overlap with true 1v1:**
```python
# Use L4 (complementary won, 2 humans) as the structural 1v1 criterion.
# L5/L6 can be applied on top if needed.
leaderboard_overlap_sql = """
WITH match_stats AS (
    SELECT matchId,
           COUNT(*) AS total_rows,
           COUNT(*) FILTER (WHERE status = 'player') AS human_rows,
           COUNT(*) FILTER (WHERE won = true) AS won_true,
           COUNT(*) FILTER (WHERE won = false) AS won_false,
           COUNT(DISTINCT profileId) FILTER (WHERE profileId != -1) AS distinct_real_profiles,
           ARRAY_AGG(DISTINCT leaderboard ORDER BY leaderboard) AS leaderboard_arr,
           CARDINALITY(ARRAY_AGG(DISTINCT leaderboard ORDER BY leaderboard)) AS n_leaderboards
    FROM matches_raw
    GROUP BY matchId
),
classified AS (
    SELECT *,
           (total_rows = 2 AND human_rows = 2
            AND won_true = 1 AND won_false = 1) AS is_structural_1v1,
           CASE
               WHEN n_leaderboards > 1 THEN 'multi_leaderboard'
               WHEN leaderboard_arr[1] = 'rm_1v1' THEN 'rm_1v1_only'
               WHEN leaderboard_arr[1] = 'qp_rm_1v1' THEN 'qp_rm_1v1_only'
               ELSE leaderboard_arr[1]
           END AS leaderboard_category
    FROM match_stats
)
SELECT
    leaderboard_category,
    COUNT(*) AS total_matches,
    COUNT(*) FILTER (WHERE is_structural_1v1) AS structural_1v1,
    COUNT(*) FILTER (WHERE NOT is_structural_1v1) AS not_structural_1v1,
    ROUND(COUNT(*) FILTER (WHERE is_structural_1v1) * 100.0 / COUNT(*), 2) AS pct_structural_1v1
FROM classified
GROUP BY leaderboard_category
ORDER BY total_matches DESC
"""
sql_queries["leaderboard_structural_1v1_overlap"] = leaderboard_overlap_sql
print("Leaderboard overlap with structural 1v1 criterion (L4)...")
df_lb_overlap = con.execute(leaderboard_overlap_sql).fetchdf()
print(f"\nLeaderboard x structural 1v1:")
for _, row in df_lb_overlap.iterrows():
    print(f"  {row['leaderboard_category']}: {int(row['total_matches']):,} total, "
          f"{int(row['structural_1v1']):,} structural 1v1 ({row['pct_structural_1v1']}%)")

leaderboard_overlap = df_lb_overlap.to_dict(orient="records")
```

**Cell 14 -- proxy vs structural confusion matrix:**
```python
# 2x2 confusion matrix: proxy_1v1 (leaderboard rm_1v1/qp_rm_1v1) vs structural_1v1
confusion_sql = """
WITH match_stats AS (
    SELECT matchId,
           COUNT(*) AS total_rows,
           COUNT(*) FILTER (WHERE status = 'player') AS human_rows,
           COUNT(*) FILTER (WHERE won = true) AS won_true,
           COUNT(*) FILTER (WHERE won = false) AS won_false,
           ARRAY_AGG(DISTINCT leaderboard ORDER BY leaderboard) AS leaderboard_arr,
           CARDINALITY(ARRAY_AGG(DISTINCT leaderboard ORDER BY leaderboard)) AS n_leaderboards
    FROM matches_raw
    GROUP BY matchId
),
classified AS (
    SELECT *,
           (total_rows = 2 AND human_rows = 2
            AND won_true = 1 AND won_false = 1) AS is_structural_1v1,
           CASE
               WHEN n_leaderboards > 1 THEN 'multi_leaderboard'
               WHEN leaderboard_arr[1] IN ('rm_1v1', 'qp_rm_1v1') THEN 'rm_1v1_only'
               ELSE 'non_rm_1v1_only'
           END AS leaderboard_category
    FROM match_stats
)
SELECT
    leaderboard_category,
    is_structural_1v1,
    COUNT(*) AS n_matches
FROM classified
GROUP BY leaderboard_category, is_structural_1v1
ORDER BY leaderboard_category, is_structural_1v1
"""
sql_queries["proxy_vs_structural_confusion"] = confusion_sql
print("Proxy vs structural 1v1 confusion matrix...")
df_conf = con.execute(confusion_sql).fetchdf()
for _, row in df_conf.iterrows():
    print(f"  leaderboard_category={row['leaderboard_category']}, structural_1v1={row['is_structural_1v1']}: "
          f"{int(row['n_matches']):,}")

confusion_matrix = df_conf.to_dict(orient="records")
```

**Cell 15 -- all-1v1-leaderboards overlap (expanded proxy):**
```python
# Expand to all leaderboards with avg_rows_per_match = 2.0 from census
all_1v1_leaderboards_sql = """
WITH match_stats AS (
    SELECT matchId,
           COUNT(*) AS total_rows,
           COUNT(*) FILTER (WHERE status = 'player') AS human_rows,
           COUNT(*) FILTER (WHERE won = true) AS won_true,
           COUNT(*) FILTER (WHERE won = false) AS won_false,
           ARRAY_AGG(DISTINCT leaderboard ORDER BY leaderboard) AS leaderboard_arr,
           CARDINALITY(ARRAY_AGG(DISTINCT leaderboard ORDER BY leaderboard)) AS n_leaderboards
    FROM matches_raw
    GROUP BY matchId
),
classified AS (
    SELECT *,
           (total_rows = 2 AND human_rows = 2
            AND won_true = 1 AND won_false = 1) AS is_structural_1v1,
           CASE
               WHEN n_leaderboards > 1 THEN 'multi_leaderboard'
               WHEN leaderboard_arr[1] IN (
                   'rm_1v1', 'qp_rm_1v1', 'ew_1v1', 'dm_1v1',
                   'rm_1v1_console', 'ew_1v1_console', 'ew_1v1_redbullwololo',
                   'ew_1v1_redbullwololo_console', 'qp_ew_1v1', 'ror_1v1'
               ) THEN 'any_1v1_leaderboard_only'
               ELSE 'non_1v1_leaderboard_only'
           END AS leaderboard_category
    FROM match_stats
)
SELECT
    leaderboard_category,
    is_structural_1v1,
    COUNT(*) AS n_matches
FROM classified
GROUP BY leaderboard_category, is_structural_1v1
ORDER BY leaderboard_category, is_structural_1v1
"""
sql_queries["expanded_proxy_vs_structural"] = all_1v1_leaderboards_sql
print("All-1v1-leaderboards vs structural 1v1:")
df_exp = con.execute(all_1v1_leaderboards_sql).fetchdf()
for _, row in df_exp.iterrows():
    print(f"  leaderboard_category={row['leaderboard_category']}, structural_1v1={row['is_structural_1v1']}: "
          f"{int(row['n_matches']):,}")

expanded_proxy_confusion = df_exp.to_dict(orient="records")
```

**Verification:**
- Confusion matrix cells sum to total matches (~61.8M).
- `unranked` leaderboard yields a non-zero structural 1v1 count.
- Expanded proxy captures more 1v1 leaderboards (ew_1v1, dm_1v1, etc.).

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T07 -- Won Complement and Edge Case Analysis (Q4)

**Objective:** For the matches passing the structural 1v1 criterion, profile
the won outcome complement (both non-NULL and complementary? Both NULL?
One NULL?) and characterize the team column values.

**Cell 16 -- won complement analysis for 2-human matches:**
```python
won_complement_sql = """
WITH match_stats AS (
    SELECT matchId,
           COUNT(*) AS total_rows,
           COUNT(*) FILTER (WHERE status = 'player') AS human_rows,
           COUNT(*) FILTER (WHERE won IS NULL) AS won_null_count,
           COUNT(*) FILTER (WHERE won = true) AS won_true,
           COUNT(*) FILTER (WHERE won = false) AS won_false
    FROM matches_raw
    GROUP BY matchId
    HAVING COUNT(*) = 2 AND COUNT(*) FILTER (WHERE status = 'player') = 2
)
SELECT
    CASE
        WHEN won_true = 1 AND won_false = 1 THEN 'complementary'
        WHEN won_true = 2 THEN 'both_true'
        WHEN won_false = 2 THEN 'both_false'
        WHEN won_null_count = 2 THEN 'both_null'
        WHEN won_null_count = 1 AND won_true = 1 THEN 'one_true_one_null'
        WHEN won_null_count = 1 AND won_false = 1 THEN 'one_false_one_null'
        ELSE 'other'
    END AS won_pattern,
    COUNT(*) AS n_matches,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
FROM match_stats
GROUP BY 1
ORDER BY n_matches DESC
"""
sql_queries["won_complement_2human"] = won_complement_sql
print("Won complement analysis for 2-row, 2-human matches:")
df_won = con.execute(won_complement_sql).fetchdf()
for _, row in df_won.iterrows():
    print(f"  {row['won_pattern']}: {int(row['n_matches']):,} ({row['pct']}%)")

won_complement_analysis = df_won.to_dict(orient="records")
```

**Cell 17 -- team analysis for structural 1v1 matches:**
```python
team_analysis_sql = """
WITH match_stats AS (
    SELECT matchId,
           COUNT(*) AS total_rows,
           COUNT(*) FILTER (WHERE status = 'player') AS human_rows,
           COUNT(*) FILTER (WHERE won = true) AS won_true,
           COUNT(*) FILTER (WHERE won = false) AS won_false,
           COUNT(DISTINCT team) FILTER (WHERE team IS NOT NULL) AS distinct_teams,
           COUNT(*) FILTER (WHERE team IS NULL) AS team_null_count,
           MIN(team) AS min_team,
           MAX(team) AS max_team
    FROM matches_raw
    GROUP BY matchId
    HAVING COUNT(*) = 2
       AND COUNT(*) FILTER (WHERE status = 'player') = 2
       AND COUNT(*) FILTER (WHERE won = true) = 1
       AND COUNT(*) FILTER (WHERE won = false) = 1
)
SELECT
    CASE
        WHEN team_null_count = 2 THEN 'both_null'
        WHEN team_null_count = 1 THEN 'one_null'
        WHEN distinct_teams = 2 AND min_team = 1 AND max_team = 2 THEN 'standard_1v2'
        WHEN distinct_teams = 2 THEN 'two_teams_nonstandard'
        WHEN distinct_teams = 1 THEN 'same_team'
        ELSE 'other'
    END AS team_pattern,
    COUNT(*) AS n_matches,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
FROM match_stats
GROUP BY 1
ORDER BY n_matches DESC
"""
sql_queries["team_analysis_structural_1v1"] = team_analysis_sql
print("Team analysis for structural 1v1 matches (L4):")
df_team = con.execute(team_analysis_sql).fetchdf()
for _, row in df_team.iterrows():
    print(f"  {row['team_pattern']}: {int(row['n_matches']):,} ({row['pct']}%)")

team_analysis = df_team.to_dict(orient="records")
```

**Verification:**
- Won complement shows majority as `complementary` (expected for valid 1v1).
- Team patterns characterize anomalies.
- Matches failing complementary won criterion quantified.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T08 -- JSON Artifact Assembly and Write

**Objective:** Assemble all findings into a structured JSON artifact at the
canonical output path.

**Cell 18 -- assemble and write JSON:**
```python
artifact = {
    "step": "01_03_02",
    "dataset": "aoe2companion",
    "table": "matches_raw",
    "total_rows": total_rows,
    "total_distinct_matchIds": funnel_levels["total_matches"],
    "rows_per_match_distribution": rows_per_match_distribution,
    "human_rows_per_match_distribution": human_rows_per_match,
    "profileId_minus1_profile": profileid_minus1_profile,
    "profileId_minus1_in_1v1_leaderboards": profileid_minus1_1v1,
    "true_1v1_criteria_funnel_raw": funnel_levels,
    "true_1v1_criteria_funnel_dedup": funnel_levels_dedup,
    "dedup_delta": dedup_delta,
    "hybrid_1v1_composition": hybrid_1v1_composition,
    "leaderboard_cardinality_per_match": leaderboard_cardinality_per_match,
    "leaderboard_overlap": leaderboard_overlap,
    "proxy_vs_structural_confusion_matrix": confusion_matrix,
    "expanded_proxy_confusion_matrix": expanded_proxy_confusion,
    "won_complement_analysis": won_complement_analysis,
    "team_analysis": team_analysis,
    "sql_queries": sql_queries,
}

json_path = output_dir / "01_03_02_true_1v1_profile.json"
with open(json_path, "w") as f:
    json.dump(artifact, f, indent=2, default=str)
print(f"JSON artifact written: {json_path}")
print(f"  Keys: {list(artifact.keys())}")
```

**Verification:**
- JSON file exists at expected path and is non-empty.
- All required keys present: `rows_per_match_distribution`, `true_1v1_criteria_funnel_raw`,
  `true_1v1_criteria_funnel_dedup`, `dedup_delta`, `leaderboard_cardinality_per_match`,
  `leaderboard_overlap`, `won_complement_analysis`.
- `sql_queries` key contains all SQL strings.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T09 -- Markdown Report

**Objective:** Write a human-readable markdown report summarizing all
findings with SQL queries inline (I6).

**Cell 19 -- generate markdown report:**
```python
md_lines = []
md_lines.append("# Step 01_03_02 -- True 1v1 Match Identification: aoe2companion\n")
md_lines.append(f"**Generated by:** `01_03_02_true_1v1_identification.py`\n")
md_lines.append(f"**Table:** matches_raw ({total_rows:,} rows, "
                f"{funnel_levels['total_matches']:,} distinct matchIds)\n")
md_lines.append("**Invariants:** #6 (all SQL verbatim), #7 (criteria from data), "
                "#9 (profiling only)\n")

md_lines.append("\n## 1. Rows-Per-Match Distribution\n")
md_lines.append("| Rows/Match | Matches | % | Total Rows |")
md_lines.append("|---|---|---|---|")
for entry in rows_per_match_distribution:
    md_lines.append(
        f"| {entry['rows_per_match']} | {entry['n_matches']:,} | "
        f"{entry['pct_matches']} | {entry['total_rows_in_group']:,} |"
    )
md_lines.append(f"\n```sql\n{sql_queries['rows_per_match_distribution']}\n```\n")

md_lines.append("\n## 2. Human Players Per Match\n")
md_lines.append("| Human Players | Matches | % |")
md_lines.append("|---|---|---|")
for entry in human_rows_per_match:
    md_lines.append(
        f"| {entry['human_players']} | {entry['n_matches']:,} | {entry['pct_matches']} |"
    )
md_lines.append(f"\n```sql\n{sql_queries['human_rows_per_match_distribution']}\n```\n")

md_lines.append("\n## 3. ProfileId = -1 Investigation\n")
md_lines.append("| Status | Rows | % All Rows | Distinct Matches |")
md_lines.append("|---|---|---|---|")
for entry in profileid_minus1_profile:
    md_lines.append(
        f"| {entry['status']} | {entry['n_rows']:,} | {entry['pct_all_rows']} | "
        f"{entry['n_matches']:,} |"
    )
md_lines.append(f"\n```sql\n{sql_queries['profileId_minus1_by_status']}\n```\n")

md_lines.append("\n## 4. True 1v1 Criteria Funnel\n")
md_lines.append("| Level | Criterion | Matches | % All |")
md_lines.append("|---|---|---|---|")
level_descriptions = {
    "total_matches": "All distinct matchIds",
    "L1_exactly_2_rows": "Exactly 2 rows",
    "L2_2_human_players": "L1 + both status='player'",
    "L3_2_humans_won_known": "L2 + both won IS NOT NULL",
    "L4_complementary_won": "L3 + one won=true, one won=false",
    "L5_distinct_profiles": "L4 + 2 distinct profileId (excl -1)",
    "L6_distinct_teams": "L5 + 2 distinct teams",
}
for key, desc in level_descriptions.items():
    count = funnel_levels[key]
    pct = count * 100.0 / funnel_levels["total_matches"]
    md_lines.append(f"| {key} | {desc} | {count:,} | {pct:.2f}% |")
md_lines.append(f"\n```sql\n{sql_queries['criteria_funnel']}\n```\n")

md_lines.append("\n## 5. 2-Row Match Human/AI Composition\n")
md_lines.append("| Humans | AI | Matches |")
md_lines.append("|---|---|---|")
for entry in hybrid_1v1_composition:
    md_lines.append(
        f"| {entry['human_rows']} | {entry['ai_rows']} | {entry['n_matches']:,} |"
    )
md_lines.append(f"\n```sql\n{sql_queries['hybrid_1v1_composition']}\n```\n")

md_lines.append("\n## 6. Leaderboard Overlap\n")
md_lines.append("### 6a. Per-leaderboard structural 1v1 rate\n")
md_lines.append("| Leaderboard | Total | Structural 1v1 | % |")
md_lines.append("|---|---|---|---|")
for entry in leaderboard_overlap:
    md_lines.append(
        f"| {entry['leaderboard']} | {entry['total_matches']:,} | "
        f"{entry['structural_1v1']:,} | {entry['pct_structural_1v1']} |"
    )
md_lines.append(f"\n```sql\n{sql_queries['leaderboard_structural_1v1_overlap']}\n```\n")

md_lines.append("### 6b. Proxy vs structural confusion matrix (rm_1v1 + qp_rm_1v1)\n")
md_lines.append("| Proxy 1v1 | Structural 1v1 | Matches |")
md_lines.append("|---|---|---|")
for entry in confusion_matrix:
    md_lines.append(
        f"| {entry['is_proxy_1v1']} | {entry['is_structural_1v1']} | "
        f"{entry['n_matches']:,} |"
    )
md_lines.append(f"\n```sql\n{sql_queries['proxy_vs_structural_confusion']}\n```\n")

md_lines.append("### 6c. Expanded proxy (all 1v1 leaderboards) vs structural\n")
md_lines.append("| Any 1v1 LB | Structural 1v1 | Matches |")
md_lines.append("|---|---|---|")
for entry in expanded_proxy_confusion:
    md_lines.append(
        f"| {entry['is_any_1v1_leaderboard']} | {entry['is_structural_1v1']} | "
        f"{entry['n_matches']:,} |"
    )
md_lines.append(f"\n```sql\n{sql_queries['expanded_proxy_vs_structural']}\n```\n")

md_lines.append("\n## 7. Won Complement Analysis (2-Human Matches)\n")
md_lines.append("| Pattern | Matches | % |")
md_lines.append("|---|---|---|")
for entry in won_complement_analysis:
    md_lines.append(
        f"| {entry['won_pattern']} | {entry['n_matches']:,} | {entry['pct']} |"
    )
md_lines.append(f"\n```sql\n{sql_queries['won_complement_2human']}\n```\n")

md_lines.append("\n## 8. Team Analysis (Structural 1v1)\n")
md_lines.append("| Pattern | Matches | % |")
md_lines.append("|---|---|---|")
for entry in team_analysis:
    md_lines.append(
        f"| {entry['team_pattern']} | {entry['n_matches']:,} | {entry['pct']} |"
    )
md_lines.append(f"\n```sql\n{sql_queries['team_analysis_structural_1v1']}\n```\n")

md_lines.append("\n## 9. Thesis Implications\n")
md_lines.append(
    "This step documents observations only. Implications for "
    "the analytical cohort definition are noted here for 01_04 consumption:\n\n"
    "- **Observation 1:** [Rows-per-match distribution] -> [cohort size] -> 01_04\n"
    "- **Observation 2:** [Proxy vs structural overlap] -> [leaderboard filter adequacy] -> 01_04\n"
    "- **Observation 3:** [Won complement anomalies] -> [target variable cleaning] -> 01_04\n"
    "- **Observation 4:** [Team anomalies] -> [additional filter criteria] -> 01_04\n"
    "- **Observation 5:** [ProfileId = -1 in 1v1] -> [identity resolution scope] -> 01_04\n"
    "\nFinal cohort definition decisions belong to Step 01_04_XX, not this step (I9).\n"
)

md_path = output_dir / "01_03_02_true_1v1_profile.md"
with open(md_path, "w") as f:
    f.write("\n".join(md_lines))
print(f"Markdown report written: {md_path}")
print(f"  {len(md_lines)} lines")
```

**Verification:**
- Markdown file exists at expected path and is non-empty.
- All 9 sections present.
- All SQL queries embedded inline (I6).
- Section 9 (Thesis Implications) notes observations without cleaning decisions (I9).

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T10 -- Notebook Execution and Validation

**Objective:** Execute the notebook end-to-end and validate all artifacts.

**Instructions:**
1. Run the notebook via:
   `source .venv/bin/activate && poetry run python sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`
2. Verify both artifact files exist and are non-empty.
3. Validate JSON structure: check for required keys
   (`rows_per_match_distribution`, `true_1v1_criteria_funnel_raw`,
   `true_1v1_criteria_funnel_dedup`, `dedup_delta`,
   `leaderboard_cardinality_per_match`, `leaderboard_overlap`,
   `won_complement_analysis`, `sql_queries`).
4. Verify `true_1v1_criteria_funnel_raw` is monotonically decreasing: L1 >= L2 >= L3 >= L4 >= L5 >= L6.
5. Verify confusion matrix cells sum to total_matches.

**Verification:**
- `ls -la src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/03_profiling/01_03_02_*`
- Both files exist, non-zero size.
- `source .venv/bin/activate && poetry run python -c "import json; d=json.load(open('src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json')); print(list(d.keys()))"`

**File scope:**
- (no new files -- validation only)

**Read scope:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.md`

---

### T11 -- STEP_STATUS Update and Research Log Entry

**Objective:** Mark step complete in STEP_STATUS.yaml and add a research
log entry summarizing findings.

**Instructions:**
1. Update `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml`:
   Set `01_03_02` status to `complete` and `completed_at` to the execution date.
2. Add a research log entry at the top of
   `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md`
   with the following structure:
   - Date, Phase/Step, Category A
   - Artifacts produced (2 files)
   - Summary of findings: funnel counts, proxy vs structural overlap, edge cases
   - Thesis implications (observations for 01_04, not decisions)

**Verification:**
- STEP_STATUS.yaml shows `01_03_02: status: complete`.
- Research log has entry for 01_03_02 at the top.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md`

---

## File Manifest

| File | Action | Task |
|------|--------|------|
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` | Update | T01 |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml` | Update | T01, T11 |
| `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_02_true_1v1_identification.py` | Create | T02--T09 |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json` | Create | T08 |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.md` | Create | T09 |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md` | Update | T11 |

## Gate Condition

All of the following must hold:

1. Both artifact files exist under `reports/artifacts/01_exploration/03_profiling/` and are non-empty:
   - `01_03_02_true_1v1_profile.json`
   - `01_03_02_true_1v1_profile.md`
2. JSON contains required keys: `rows_per_match_distribution`, `true_1v1_criteria_funnel_raw`, `true_1v1_criteria_funnel_dedup`, `dedup_delta`, `leaderboard_cardinality_per_match`, `leaderboard_overlap`, `proxy_vs_structural_confusion_matrix`, `won_complement_analysis`, `team_analysis`, `sql_queries`.
3. `true_1v1_criteria_funnel_raw` is monotonically decreasing from L1 to L6.
4. Confusion matrix cells sum to `total_distinct_matchIds`.
5. All SQL queries are present in the `sql_queries` key (I6).
6. MD report contains all 9 sections with inline SQL.
7. Notebook executes end-to-end without error.
8. STEP_STATUS.yaml shows `01_03_02: status: complete`.
9. research_log.md has entry for 01_03_02.
10. No SQL uses `ANY_VALUE(leaderboard)` -- all leaderboard aggregations use `ARRAY_AGG(DISTINCT leaderboard ORDER BY leaderboard)`.

## Out of Scope

- **Defining the analytical cohort.** This step identifies populations; 01_04 (cleaning) decides which population to use.
- **Creating derived tables or views.** Read-only profiling (I9). The 1v1 filter query can be reused by 01_04 but no table is created here.
- **Rating join with ratings_raw.** Deferred to 01_04. This step profiles match structure, not rating completeness.
- **Cross-dataset comparison with aoestats 1v1 identification.** Deferred to 01_06 Decision Gate.
- **Feature engineering.** No features created. No temporal features computed.
- **Data cleaning or row exclusion.** Observations only.

## Open Questions

- **What fraction of `unranked` matches are true 1v1?** Computed at execution. The `unranked` leaderboard has 18.8M matches with avg 4.17 rows/match -- a nontrivial subset will have exactly 2 human rows.
- **Are profileId = -1 rows exclusively `status = 'ai'`?** If some profileId = -1 rows have `status = 'player'`, this affects the L5 (distinct_real_profiles) criterion. Resolved by T04.
- **Do all 1v1-leaderboard matches pass the structural 1v1 criterion?** The census avg_rows_per_match = 2.0 suggests yes, but edge cases (duplicate ingestion, partial records) may exist. Resolved by T06.
- **How large is the "hidden 1v1" population in non-1v1 leaderboards?** This is the key thesis-relevant question -- it determines whether the leaderboard proxy underestimates the usable data.
```

---

For Category A, adversarial critique is required before execution. Dispatch reviewer-adversarial to produce `planning/plan_aoe2companion_01_03_02.critique.md`.

---

**Key files referenced:**

- `/Users/tomaszpionka/Projects/rts-outcome-prediction/.claude/scientific-invariants.md` -- 10 invariants; I3, I6, I7, I9 most relevant
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json` -- match_structure_by_leaderboard, won_consistency_2row (establishes matchId as grouping key and avg_rows_per_match)
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json` -- column profiles for matchId (card 61.8M), profileId (card 3.4M, -1 in duplicates), status (player 95.3%, ai 4.7%), team (4.9% NULL, card 31), won (4.69% NULL), slot (card 9)
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` -- step 01_03_02 to be added
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml` -- 01_03_01 complete, 01_03_02 not yet registered
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/planning/plan_aoe2companion_01_03_01.md` -- format reference for task structure
