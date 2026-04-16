---
category: A
branch: feat/census-pass3
date: 2026-04-16
planner_model: claude-opus-4-6
dataset: aoestats
phase: "01"
pipeline_section: "01_03 -- Systematic Data Profiling"
step: "01_03_02"
invariants_touched: [6, 7, 9]
source_artifacts:
  - "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
  - "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json"
  - "src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/matches_raw.yaml"
  - "src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/players_raw.yaml"
critique_required: true
research_log_ref: "src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md"
---

# Plan: aoestats Step 01_03_02 -- True 1v1 Match Identification

## Scope

**Phase/Step:** 01 / 01_03_02
**Branch:** feat/census-pass3
**Action:** CREATE (step does not yet exist in ROADMAP)
**Predecessor:** 01_03_01 (Systematic Data Profiling -- complete, artifacts on disk)

Determine which matches in the aoestats dataset are genuine 1v1 matches --
exactly 2 active players -- regardless of the `leaderboard` game-mode label.
This step produces a player-count-based profile of all matches, compares the
results against the `leaderboard`-based filter, and documents discrepancies.
The output informs downstream 01_04 cleaning decisions about which matches
to retain for the 1v1 prediction task.

## Problem Statement

The aoestats dataset contains matches across multiple game modes: `random_map`
(58.5%), `team_random_map` (37.5%), `co_random_map` (2.0%), and
`co_team_random_map` (1.9%). The thesis predicts outcomes for 1v1 matches. The
`leaderboard = 'random_map'` value labels the ranked 1v1 ladder, but a
game-mode label is not a structural guarantee that a match has exactly 2 active
players. This step answers four questions:

**Q1: What columns in players_raw distinguish active (playing) players from
non-playing rows?** The schema YAML shows players_raw has 14 columns: winner,
game_id, team, feudal/castle/imperial_age_uptime, old_rating, new_rating,
match_rating_diff, replay_summary_raw, profile_id, civ, opening, filename.
There is NO `slot`, `is_observer`, `status`, or `type` column. The `team`
column has cardinality 2 (values 0 and 1, ~50/50 split), so there is no
"spectator team" value. The `winner` column is BOOLEAN, never NULL (0% NULL
rate). The `civ` column is VARCHAR, never NULL (0% NULL rate, cardinality 50).
The `profile_id` column is DOUBLE with 1,185 NULLs (0.0011%). Given the absence
of explicit observer/spectator markers, every row in players_raw represents an
active player. The "active player" definition for this dataset is therefore:
**every row in players_raw is an active player row**. This is a schema-level
fact, not an assumption -- the schema provides no mechanism to represent
non-active participants.

**Q2: How does `num_players` in matches_raw relate to the actual player count?**
The census already establishes that `num_players` and actual player-row counts
diverge: `num_players_distribution` reports `num_players=2: 18,586,063` matches,
while `players_per_match` reports `player_count=2: 18,438,769` matches --
a difference of 147,294 matches. The 01_03_01 linkage integrity check
identified 212,890 orphaned matches (game_ids in matches_raw with zero player
rows). This step quantifies the structural breakdown of that discrepancy:
specifically, what `num_players` values the orphaned matches have, and
whether any non-orphaned matches also show a mismatch between `num_players`
and actual player-row count.

**Q3: What is the true count of 1v1 matches?** Using the player-count method
(COUNT of players_raw rows per game_id = 2), determine the exact number of
genuine 1v1 matches.

**Q4: How does the true 1v1 count compare to the leaderboard-based filter?**
Compare the player-count-derived 1v1 set against `leaderboard = 'random_map'`
(the ranked 1v1 ladder). Identify: (a) ranked 1v1 matches with not exactly 2
players (corrupt/malformed), (b) non-ranked matches that are genuine 1v1
(unranked, co-op 1v1, etc.), (c) the overlap.

## Assumptions & Unknowns

- **Assumption (schema-grounded):** Every row in players_raw represents an
  active player. The schema has no observer/spectator marker columns. This is
  verified by the 01_01_02 schema discovery and 01_02_03 raw schema DESCRIBE
  artifacts. If a future step reveals that some player rows are inactive
  (e.g., via `replay_summary_raw` parsing), this assumption must be revisited.

- **Assumption (census-grounded):** `num_players` in matches_raw is an
  integer field with values 1-8, zero NULLs. From the 01_02_04 univariate
  census: num_players distribution shows 60.56% of matches have
  num_players=2.

- **Assumption (01_03_01-grounded):** `matches_without_players = 212,890` from
  the systematic profile linkage integrity check. These matches will appear in
  `num_players`-based counts but NOT in player-count-based counts.

- **Unknown: Does `num_players` always equal the count of player rows?** This
  is Q2's core question. Possible mismatches include: (a) the 212,890
  orphaned matches (no player rows), (b) the missing-week file gap
  (2025-11-16 to 2025-11-22 has matches but no player data, per the
  01_01_01 file inventory), (c) edge cases with duplicate player rows (489
  identified in 01_03_01).

- **Unknown: Are there `leaderboard = 'random_map'` matches with not exactly
  2 player rows?** If so, this indicates either data corruption or lobby
  irregularities in the ranked 1v1 ladder.

- **Unknown: Is `profile_id IS NULL` correlated with non-1v1 matches?** The
  1,185 NULL profile_id rows may cluster in certain match types.

## Literature Context

The distinction between game-mode labels and structural player counts is a
data quality concern specific to community-sourced game datasets. Kowalczyk
et al. (2024, SC2EGSet) note similar issues where replay metadata labels do
not guarantee structural properties. For AoE2 specifically, the aoestats.io
data pipeline is community-maintained and processes match records from the
AoE2 API, where lobby configuration can differ from actual player
participation.

The 01_DATA_EXPLORATION_MANUAL.md, Section 3 (Systematic Data Profiling)
prescribes cross-reference validation between related fields -- in this case,
`num_players` vs actual player row counts, and `leaderboard` vs structural
1v1 identification.

## Execution Steps

### T01 -- ROADMAP Patch

**Objective:** Insert the Step 01_03_02 definition into ROADMAP.md so that
the step is registered before execution begins.

**Instructions:**
1. Open `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`.
2. Insert the following YAML block after the 01_03_01 block (before the
   `---` separator preceding Phase 02), under a new section header
   `### Step 01_03_02 -- True 1v1 Match Identification`:

```yaml
step_number: "01_03_02"
name: "True 1v1 Match Identification"
description: "Cross-reference matches_raw.num_players against actual player row counts from players_raw to identify genuine 1v1 matches (exactly 2 active players). Compare against leaderboard-based filtering. Document discrepancies, orphaned matches, and edge cases. Profiling only -- no cleaning decisions."
phase: "01 -- Data Exploration"
pipeline_section: "01_03 -- Systematic Data Profiling"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 3"
dataset: "aoestats"
question: "Which matches are genuine 1v1 (exactly 2 active players), how does num_players relate to actual player counts, and how does the true 1v1 set compare to leaderboard='random_map'?"
method: "JOIN matches_raw with aggregated players_raw player counts per game_id. Cross-tabulate num_players vs actual_player_count. Compute leaderboard-vs-player-count overlap."
stratification: "By num_players value. By leaderboard value. By match type (true 1v1 vs label 1v1)."
predecessors:
  - "01_03_01"
notebook_path: "sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_02_true_1v1_identification.py"
inputs:
  duckdb_tables:
    - "matches_raw"
    - "players_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
    - "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json"
  external_references:
    - ".claude/scientific-invariants.md"
    - "docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md, Section 3"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json"
  plots:
    - "artifacts/01_exploration/03_profiling/01_03_02_match_type_breakdown.png"
  report: "artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "No magic numbers. All row counts, NULL rates, and thresholds from census JSON or systematic profile JSON. The 'active player' definition is schema-derived, not a magic number."
  - number: "9"
    how_upheld: "Profiling only. No cleaning decisions, no feature engineering, no model fitting. Findings are documented for 01_04, not acted upon."
gate:
  artifact_check: "All 3 artifact files exist under reports/artifacts/01_exploration/03_profiling/ and are non-empty."
  continue_predicate: "JSON contains keys: true_1v1_count, ranked_1v1_count, overlap, num_players_vs_actual_crosstab. MD contains comparison table. PNG file exists."
  halt_predicate: "Any SQL query fails or any artifact is missing or empty."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data"
  - "Chapter 4 -- Data and Methodology > 4.2 Pre-processing"
research_log_entry: "Required on completion."
```

**Verification:**
- The ROADMAP.md contains a `step_number: "01_03_02"` block.
- The block appears after 01_03_01 and before the Phase 02 placeholder.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`

---

### T02 -- Notebook Setup

**Objective:** Create the jupytext-paired notebook with header, imports, DuckDB
connection, census/profile JSON load, validation, and accumulator dicts.

**Instructions:**
1. The profiling directory already exists from 01_03_01:
   `sandbox/aoe2/aoestats/01_exploration/03_profiling/`.
2. The artifact directory already exists:
   `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/03_profiling/`.
3. Create the notebook file:
   `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`.

**Cell 1 -- markdown header:**
```markdown
# Step 01_03_02 -- True 1v1 Match Identification: aoestats

**Phase:** 01 -- Data Exploration
**Pipeline Section:** 01_03 -- Systematic Data Profiling
**Dataset:** aoestats
**Question:** Which matches are genuine 1v1 (exactly 2 active players),
how does num_players relate to actual player counts, and how does the
true 1v1 set compare to leaderboard='random_map'?
**Invariants applied:**
- #6 (reproducibility -- all SQL stored verbatim in markdown artifact)
- #7 (no magic numbers -- all thresholds from census/profile JSON)
- #9 (step scope: profiling only -- no cleaning or feature decisions)
**Predecessor:** 01_03_01 (Systematic Data Profiling -- complete)
**Step scope:** Identification and counting only. No filtering, cleaning,
or subsetting decisions.
```

**Cell 2 -- imports:**
```python
import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir, setup_notebook_logging

matplotlib.use("Agg")
logger = setup_notebook_logging(__name__)
```

**Cell 3 -- DuckDB connection:**
```python
db = get_notebook_db("aoe2", "aoestats")
```

**Cell 4 -- paths and artifact directory setup:**
```python
reports_dir = get_reports_dir("aoe2", "aoestats")
profiling_dir = reports_dir / "artifacts" / "01_exploration" / "03_profiling"
profiling_dir.mkdir(parents=True, exist_ok=True)

census_path = reports_dir / "artifacts" / "01_exploration" / "02_eda" / "01_02_04_univariate_census.json"
with open(census_path) as f:
    census = json.load(f)

profile_path = profiling_dir / "01_03_01_systematic_profile.json"
with open(profile_path) as f:
    profile_01_03_01 = json.load(f)
```

**Cell 5 -- validation:**
```python
# Validate census keys needed for this step
assert "num_players_distribution" in census, "Missing census key: num_players_distribution"
assert "categorical_matches" in census, "Missing census key: categorical_matches"
assert "leaderboard" in census["categorical_matches"], "Missing census key: categorical_matches.leaderboard"
assert "players_per_match" in census and len(census["players_per_match"]) > 0, (
    "Missing or empty census key 'players_per_match' -- "
    "re-run 01_02_04 census before proceeding"
)

# Validate profile keys
assert "dataset_level" in profile_01_03_01, "Missing profile key: dataset_level"
assert "matches_without_players" in profile_01_03_01["dataset_level"], (
    "Missing profile key: dataset_level.matches_without_players"
)

# I7: Extract constants from prior artifacts -- no magic numbers
MATCHES_TOTAL = profile_01_03_01["dataset_level"]["matches_raw_rows"]
PLAYERS_TOTAL = profile_01_03_01["dataset_level"]["players_raw_rows"]
MATCHES_WITHOUT_PLAYERS = profile_01_03_01["dataset_level"]["matches_without_players"]

# I7: num_players distribution from census
NUM_PLAYERS_DIST = {
    int(entry["num_players"]): int(entry["row_count"])
    for entry in census["num_players_distribution"]
}
# Census-derived: num_players=2 count
NUM_PLAYERS_2_CENSUS = NUM_PLAYERS_DIST.get(2, 0)

# I7: leaderboard distribution from census
LEADERBOARD_DIST = {
    entry["leaderboard"]: int(entry["cnt"])
    for entry in census["categorical_matches"]["leaderboard"]["top_values"]
}
RANKED_1V1_CENSUS = LEADERBOARD_DIST.get("random_map", 0)

print(f"MATCHES_TOTAL = {MATCHES_TOTAL:,}")
print(f"PLAYERS_TOTAL = {PLAYERS_TOTAL:,}")
print(f"MATCHES_WITHOUT_PLAYERS = {MATCHES_WITHOUT_PLAYERS:,}")
print(f"NUM_PLAYERS_2_CENSUS = {NUM_PLAYERS_2_CENSUS:,}")
print(f"RANKED_1V1_CENSUS = {RANKED_1V1_CENSUS:,}")
print(f"NUM_PLAYERS_DIST = {NUM_PLAYERS_DIST}")
```

**Cell 6 -- accumulators:**
```python
sql_queries = {}
result = {
    "step": "01_03_02",
    "dataset": "aoestats",
    "constants_source": {
        "MATCHES_TOTAL": {"value": MATCHES_TOTAL, "source": "01_03_01_systematic_profile.json > dataset_level.matches_raw_rows"},
        "PLAYERS_TOTAL": {"value": PLAYERS_TOTAL, "source": "01_03_01_systematic_profile.json > dataset_level.players_raw_rows"},
        "MATCHES_WITHOUT_PLAYERS": {"value": MATCHES_WITHOUT_PLAYERS, "source": "01_03_01_systematic_profile.json > dataset_level.matches_without_players"},
        "NUM_PLAYERS_2_CENSUS": {"value": NUM_PLAYERS_2_CENSUS, "source": "01_02_04_univariate_census.json > num_players_distribution[num_players=2].row_count"},
        "RANKED_1V1_CENSUS": {"value": RANKED_1V1_CENSUS, "source": "01_02_04_univariate_census.json > categorical_matches.leaderboard.top_values[random_map].cnt"},
    },
}
```

**Verification:**
- Notebook runs through T02 cells without error.
- Census and profile keys validated.
- All runtime constants sourced from prior artifacts, no magic numbers.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T03 -- Q1: Active Player Definition

**Objective:** Document the schema-based evidence that every row in players_raw
is an active player. Produce a diagnostic query that examines NULL patterns on
key columns to rule out hidden observer/spectator rows.

**Cell 7 -- markdown section:**
```markdown
## Q1: Active Player Definition

The players_raw schema has 14 columns. There is no slot, is_observer, status,
or type column. The team column has cardinality 2 (values 0 and 1). Every row
has a non-NULL winner (BOOLEAN), non-NULL civ (VARCHAR), and non-NULL team.
profile_id has 1,185 NULLs (0.0011%).

**Conclusion:** Every row in players_raw represents an active player. There
is no schema-level mechanism to represent spectators or observers.
```

**Cell 8 -- diagnostic: NULL pattern cross-tab for players_raw key columns:**
```python
sql_active_player_diagnostic = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE winner IS NULL)     AS winner_null,
    COUNT(*) FILTER (WHERE civ IS NULL)        AS civ_null,
    COUNT(*) FILTER (WHERE team IS NULL)        AS team_null,
    COUNT(*) FILTER (WHERE profile_id IS NULL)  AS profile_id_null,
    COUNT(*) FILTER (WHERE game_id IS NULL)     AS game_id_null,
    -- Check if there are any rows where ALL of winner, civ, team are NULL
    -- (would suggest empty/observer slots)
    COUNT(*) FILTER (
        WHERE winner IS NULL AND civ IS NULL AND team IS NULL
    ) AS all_key_null,
    -- Check team value range
    MIN(team) AS team_min,
    MAX(team) AS team_max,
    COUNT(DISTINCT team) AS team_distinct
FROM players_raw
"""
sql_queries["active_player_diagnostic"] = sql_active_player_diagnostic
diag_df = db.fetch_df(sql_active_player_diagnostic)
print(diag_df.T.to_string())

result["q1_active_player_diagnostic"] = {
    "total_rows": int(diag_df["total_rows"].iloc[0]),
    "winner_null": int(diag_df["winner_null"].iloc[0]),
    "civ_null": int(diag_df["civ_null"].iloc[0]),
    "team_null": int(diag_df["team_null"].iloc[0]),
    "profile_id_null": int(diag_df["profile_id_null"].iloc[0]),
    "game_id_null": int(diag_df["game_id_null"].iloc[0]),
    "all_key_null": int(diag_df["all_key_null"].iloc[0]),
    "team_min": int(diag_df["team_min"].iloc[0]),
    "team_max": int(diag_df["team_max"].iloc[0]),
    "team_distinct": int(diag_df["team_distinct"].iloc[0]),
}
result["q1_conclusion"] = (
    "Every row in players_raw is an active player. "
    "No observer/spectator marker columns exist. "
    "winner is never NULL, civ is never NULL, team has values {0, 1} only."
)
print(f"\nQ1 conclusion: {result['q1_conclusion']}")
```

**Verification:**
- winner_null = 0, civ_null = 0, team_null = 0, all_key_null = 0.
- team_min = 0, team_max = 1, team_distinct = 2.
- These match the census values established in 01_02_04.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T04 -- Q2: num_players vs Actual Player Count Cross-Reference

**Objective:** Join matches_raw with player counts from players_raw to determine
whether `num_players` accurately reflects the number of player rows per match.
Identify mismatches.

**Cell 9 -- markdown section:**
```markdown
## Q2: num_players vs Actual Player Count

Cross-reference matches_raw.num_players against COUNT(players_raw rows) per
game_id. The 01_03_01 linkage check found 212,890 matches with no player
rows. These will show as actual_count=0 in the cross-tabulation.
```

**Cell 10 -- cross-reference query:**
```python
sql_num_players_vs_actual = """
WITH player_counts AS (
    SELECT
        game_id,
        COUNT(*) AS actual_player_count
    FROM players_raw
    GROUP BY game_id
)
SELECT
    m.num_players,
    COALESCE(pc.actual_player_count, 0) AS actual_player_count,
    COUNT(*) AS match_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 4) AS pct
FROM matches_raw m
LEFT JOIN player_counts pc ON m.game_id = pc.game_id
GROUP BY m.num_players, COALESCE(pc.actual_player_count, 0)
ORDER BY m.num_players, actual_player_count
"""
sql_queries["num_players_vs_actual"] = sql_num_players_vs_actual
cross_df = db.fetch_df(sql_num_players_vs_actual)
print(cross_df.to_string(index=False))

# Store as list of dicts for JSON
result["q2_num_players_vs_actual_crosstab"] = cross_df.to_dict(orient="records")

# Compute alignment summary
total_matches = cross_df["match_count"].sum()
aligned = cross_df.loc[
    cross_df["num_players"] == cross_df["actual_player_count"],
    "match_count"
].sum()
mismatched = total_matches - aligned

result["q2_alignment_summary"] = {
    "total_matches": int(total_matches),
    "aligned_count": int(aligned),
    "aligned_pct": round(aligned / total_matches * 100, 4),
    "mismatched_count": int(mismatched),
    "mismatched_pct": round(mismatched / total_matches * 100, 4),
}
print(f"\nAlignment: {aligned:,} / {total_matches:,} ({result['q2_alignment_summary']['aligned_pct']}%)")
print(f"Mismatched: {mismatched:,} ({result['q2_alignment_summary']['mismatched_pct']}%)")
```

**Cell 11 -- mismatch breakdown:**
```python
# Separate the mismatches into categories
orphaned = cross_df.loc[cross_df["actual_player_count"] == 0, "match_count"].sum()
np_ne_actual = cross_df.loc[
    (cross_df["num_players"] != cross_df["actual_player_count"])
    & (cross_df["actual_player_count"] > 0),
    "match_count"
].sum()

result["q2_mismatch_breakdown"] = {
    "orphaned_matches_no_players": int(orphaned),
    "num_players_ne_actual_with_players": int(np_ne_actual),
}
print(f"Orphaned (actual=0): {orphaned:,}")
print(f"num_players != actual (actual>0): {np_ne_actual:,}")

# Validate orphaned count against 01_03_01
assert abs(int(orphaned) - MATCHES_WITHOUT_PLAYERS) <= 1, (
    f"Orphaned count {orphaned} does not match 01_03_01 linkage integrity "
    f"({MATCHES_WITHOUT_PLAYERS}). Investigate."
)
print(f"\nOrphaned count validated against 01_03_01: {MATCHES_WITHOUT_PLAYERS:,}")
```

**Cell 12 -- W2 cross-validation against census players_per_match:**
```python
# Compute actual player counts per game_id (non-orphaned matches only)
sql_player_counts = """
SELECT
    actual_player_count,
    COUNT(*) AS num_matches
FROM (
    SELECT game_id, COUNT(*) AS actual_player_count
    FROM players_raw
    GROUP BY game_id
) sub
GROUP BY actual_player_count
ORDER BY actual_player_count
"""
sql_queries["player_counts_distribution"] = sql_player_counts
df_player_counts = db.fetch_df(sql_player_counts)
print(df_player_counts.to_string(index=False))

# W2 fix: Cross-validate against census players_per_match
census_count_2 = next(
    (entry["count"] for entry in census["players_per_match"] if entry["player_count"] == 2),
    None
)
assert census_count_2 is not None, "Census missing player_count=2 entry"
recomputed_2 = int(df_player_counts[df_player_counts["actual_player_count"] == 2]["num_matches"].iloc[0])
delta_pct = abs(recomputed_2 - census_count_2) / census_count_2 * 100
assert delta_pct <= 1.0, (
    f"player_count=2 mismatch exceeds 1%: "
    f"census={census_count_2:,}, recomputed={recomputed_2:,}, delta={delta_pct:.3f}%"
)
print(f"Cross-validation PASSED: census={census_count_2:,}, recomputed={recomputed_2:,} "
      f"(delta={recomputed_2 - census_count_2:+,}, {delta_pct:.3f}%)")
```

**Verification:**
- Cross-tabulation produces rows showing `num_players` vs `actual_player_count`.
- Orphaned match count matches 01_03_01 value (212,890).
- Alignment summary is recorded in result dict.
- Cross-validation of `player_count=2` against census passes within 1%.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T05 -- Q3: True 1v1 Count (Player-Count Method)

**Objective:** Count matches with exactly 2 player rows (the structural
definition of a 1v1 match). Break down by leaderboard to see which game
modes contribute genuine 1v1 matches.

**Cell 12 -- markdown section:**
```markdown
## Q3: True 1v1 Count (Player-Count Method)

A "true 1v1" match is one with exactly 2 rows in players_raw for that
game_id. This is a structural criterion, independent of the leaderboard
label.
```

**Cell 13 -- true 1v1 count:**
```python
sql_true_1v1_count = """
WITH player_counts AS (
    SELECT
        game_id,
        COUNT(*) AS actual_player_count
    FROM players_raw
    GROUP BY game_id
    HAVING COUNT(*) = 2
)
SELECT COUNT(*) AS true_1v1_count
FROM player_counts
"""
sql_queries["true_1v1_count"] = sql_true_1v1_count
true_1v1_df = db.fetch_df(sql_true_1v1_count)
true_1v1_count = int(true_1v1_df["true_1v1_count"].iloc[0])
result["true_1v1_count"] = true_1v1_count
print(f"True 1v1 matches (exactly 2 player rows): {true_1v1_count:,}")
```

**Cell 13b -- B1 diagnostic: duplicate-row impact on 1v1 classification:**
```python
# B1 diagnostic: quantify how many game_ids might be misclassified due to
# the 489 duplicate player rows identified in 01_03_01.
# A game_id with 2 DISTINCT players but COUNT(*) = 3 would be excluded by
# the raw-count criterion. This query counts such cases.
duplicate_impact_sql = """
WITH raw_counts AS (
    SELECT game_id, COUNT(*) AS raw_count
    FROM players_raw
    GROUP BY game_id
),
distinct_counts AS (
    SELECT game_id, COUNT(DISTINCT profile_id) AS distinct_profiles
    FROM players_raw
    GROUP BY game_id
)
SELECT
    COUNT(*) FILTER (WHERE rc.raw_count = 2) AS matches_exactly_2_raw,
    COUNT(*) FILTER (WHERE dc.distinct_profiles = 2) AS matches_exactly_2_distinct,
    COUNT(*) FILTER (WHERE rc.raw_count != 2 AND dc.distinct_profiles = 2)
        AS recovered_by_dedup,
    COUNT(*) FILTER (WHERE rc.raw_count = 3 AND dc.distinct_profiles = 2)
        AS misclassified_count_3_but_2_distinct
FROM raw_counts rc
JOIN distinct_counts dc ON rc.game_id = dc.game_id
"""
sql_queries["duplicate_impact"] = duplicate_impact_sql
print("Duplicate impact diagnostic...")
df_dup_impact = db.fetch_df(duplicate_impact_sql).iloc[0]
print(f"  Matches with exactly 2 raw rows: {int(df_dup_impact['matches_exactly_2_raw']):,}")
print(f"  Matches with exactly 2 distinct profiles: {int(df_dup_impact['matches_exactly_2_distinct']):,}")
print(f"  Recovered by dedup (raw!=2 but distinct=2): {int(df_dup_impact['recovered_by_dedup']):,}")
print(f"  Specifically count=3 but 2 distinct (most likely dup case): "
      f"{int(df_dup_impact['misclassified_count_3_but_2_distinct']):,}")
duplicate_impact = df_dup_impact.to_dict()
result["duplicate_impact"] = duplicate_impact
```

**Cell 14 -- true 1v1 by leaderboard:**
```python
sql_true_1v1_by_leaderboard = """
WITH player_counts AS (
    SELECT
        game_id,
        COUNT(*) AS actual_player_count
    FROM players_raw
    GROUP BY game_id
    HAVING COUNT(*) = 2
)
SELECT
    m.leaderboard,
    COUNT(*) AS match_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 4) AS pct_of_true_1v1
FROM matches_raw m
INNER JOIN player_counts pc ON m.game_id = pc.game_id
GROUP BY m.leaderboard
ORDER BY match_count DESC
"""
sql_queries["true_1v1_by_leaderboard"] = sql_true_1v1_by_leaderboard
true_1v1_lb_df = db.fetch_df(sql_true_1v1_by_leaderboard)
print(true_1v1_lb_df.to_string(index=False))
result["true_1v1_by_leaderboard"] = true_1v1_lb_df.to_dict(orient="records")
```

**Cell 15 -- true 1v1 by num_players to check alignment:**
```python
sql_true_1v1_by_num_players = """
WITH player_counts AS (
    SELECT
        game_id,
        COUNT(*) AS actual_player_count
    FROM players_raw
    GROUP BY game_id
    HAVING COUNT(*) = 2
)
SELECT
    m.num_players,
    COUNT(*) AS match_count
FROM matches_raw m
INNER JOIN player_counts pc ON m.game_id = pc.game_id
GROUP BY m.num_players
ORDER BY m.num_players
"""
sql_queries["true_1v1_by_num_players"] = sql_true_1v1_by_num_players
true_1v1_np_df = db.fetch_df(sql_true_1v1_by_num_players)
print(true_1v1_np_df.to_string(index=False))
result["true_1v1_by_num_players"] = true_1v1_np_df.to_dict(orient="records")
```

**Verification:**
- true_1v1_count is a single integer > 0.
- Leaderboard breakdown sums to true_1v1_count.
- num_players breakdown reveals whether true 1v1 matches always have num_players=2.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T06 -- Q4: Comparison -- True 1v1 vs Ranked 1v1 (Leaderboard Filter)

**Objective:** Compute the set-level comparison between true 1v1 (player count
= 2) and ranked 1v1 (leaderboard = 'random_map'). Identify overlap,
ranked-only, and true-only subsets.

**Cell 16 -- markdown section:**
```markdown
## Q4: True 1v1 vs Ranked 1v1 (Leaderboard Filter)

Compare two sets:
- **Set A (True 1v1):** game_ids with exactly 2 player rows
- **Set B (Ranked 1v1):** game_ids with leaderboard = 'random_map'

Report: |A AND B|, |A NOT B|, |B NOT A|, |A|, |B|.
```

**Cell 17 -- set comparison query:**
```python
sql_set_comparison = """
WITH player_counts AS (
    SELECT
        game_id,
        COUNT(*) AS actual_player_count
    FROM players_raw
    GROUP BY game_id
),
classified AS (
    SELECT
        m.game_id,
        m.leaderboard,
        m.num_players,
        COALESCE(pc.actual_player_count, 0) AS actual_player_count,
        (COALESCE(pc.actual_player_count, 0) = 2)    AS is_true_1v1,
        (m.leaderboard = 'random_map')                AS is_ranked_1v1
    FROM matches_raw m
    LEFT JOIN player_counts pc ON m.game_id = pc.game_id
)
SELECT
    COUNT(*) AS total_matches,
    COUNT(*) FILTER (WHERE is_true_1v1)                               AS true_1v1,
    COUNT(*) FILTER (WHERE is_ranked_1v1)                             AS ranked_1v1,
    COUNT(*) FILTER (WHERE is_true_1v1 AND is_ranked_1v1)             AS overlap_both,
    COUNT(*) FILTER (WHERE is_true_1v1 AND NOT is_ranked_1v1)         AS true_only,
    COUNT(*) FILTER (WHERE NOT is_true_1v1 AND is_ranked_1v1)         AS ranked_only,
    COUNT(*) FILTER (WHERE NOT is_true_1v1 AND NOT is_ranked_1v1)     AS neither
FROM classified
"""
sql_queries["set_comparison"] = sql_set_comparison
set_df = db.fetch_df(sql_set_comparison)
print(set_df.T.to_string())

result["q4_set_comparison"] = {
    "total_matches": int(set_df["total_matches"].iloc[0]),
    "true_1v1": int(set_df["true_1v1"].iloc[0]),
    "ranked_1v1": int(set_df["ranked_1v1"].iloc[0]),
    "overlap_both": int(set_df["overlap_both"].iloc[0]),
    "true_only": int(set_df["true_only"].iloc[0]),
    "ranked_only": int(set_df["ranked_only"].iloc[0]),
    "neither": int(set_df["neither"].iloc[0]),
}

# Derived overlap metrics
overlap = result["q4_set_comparison"]["overlap_both"]
true_1v1_total = result["q4_set_comparison"]["true_1v1"]
ranked_total = result["q4_set_comparison"]["ranked_1v1"]
result["q4_overlap_metrics"] = {
    "jaccard_index": round(overlap / (true_1v1_total + ranked_total - overlap), 6) if (true_1v1_total + ranked_total - overlap) > 0 else 0,
    "overlap_pct_of_true": round(overlap / true_1v1_total * 100, 4) if true_1v1_total > 0 else 0,
    "overlap_pct_of_ranked": round(overlap / ranked_total * 100, 4) if ranked_total > 0 else 0,
}
print(f"\nJaccard index: {result['q4_overlap_metrics']['jaccard_index']}")
print(f"Overlap as % of true 1v1: {result['q4_overlap_metrics']['overlap_pct_of_true']}%")
print(f"Overlap as % of ranked 1v1: {result['q4_overlap_metrics']['overlap_pct_of_ranked']}%")
```

**Cell 18 -- ranked_only breakdown (ranked 1v1 with != 2 players):**
```python
sql_ranked_not_true_1v1 = """
WITH player_counts AS (
    SELECT
        game_id,
        COUNT(*) AS actual_player_count
    FROM players_raw
    GROUP BY game_id
)
SELECT
    m.num_players,
    COALESCE(pc.actual_player_count, 0) AS actual_player_count,
    COUNT(*) AS match_count
FROM matches_raw m
LEFT JOIN player_counts pc ON m.game_id = pc.game_id
WHERE m.leaderboard = 'random_map'
  AND COALESCE(pc.actual_player_count, 0) != 2
GROUP BY m.num_players, COALESCE(pc.actual_player_count, 0)
ORDER BY match_count DESC
"""
sql_queries["ranked_not_true_1v1"] = sql_ranked_not_true_1v1
ranked_not_df = db.fetch_df(sql_ranked_not_true_1v1)
print("Ranked 1v1 (leaderboard='random_map') with != 2 player rows:")
print(ranked_not_df.to_string(index=False))
result["q4_ranked_not_true_1v1"] = ranked_not_df.to_dict(orient="records")
```

**Cell 19 -- true_only breakdown (true 1v1 with non-random_map leaderboard):**
```python
sql_true_not_ranked = """
WITH player_counts AS (
    SELECT
        game_id,
        COUNT(*) AS actual_player_count
    FROM players_raw
    GROUP BY game_id
    HAVING COUNT(*) = 2
)
SELECT
    m.leaderboard,
    COUNT(*) AS match_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 4) AS pct
FROM matches_raw m
INNER JOIN player_counts pc ON m.game_id = pc.game_id
WHERE m.leaderboard != 'random_map'
GROUP BY m.leaderboard
ORDER BY match_count DESC
"""
sql_queries["true_not_ranked"] = sql_true_not_ranked
true_not_df = db.fetch_df(sql_true_not_ranked)
print("True 1v1 (2 player rows) with leaderboard != 'random_map':")
print(true_not_df.to_string(index=False))
result["q4_true_not_ranked"] = true_not_df.to_dict(orient="records")
```

**Verification:**
- Set comparison values sum correctly: overlap + true_only + ranked_only + neither = total_matches.
- true_1v1 = overlap + true_only.
- ranked_1v1 = overlap + ranked_only.
- All stored in result dict.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T07 -- profile_id NULL Analysis in Context of 1v1

**Objective:** Check whether the 1,185 NULL profile_id rows cluster in
specific match types. This is an edge-case investigation for Q1.

**Cell 20 -- markdown section:**
```markdown
## Edge Case: profile_id NULL Distribution by Match Type
```

**Cell 21 -- profile_id NULL by leaderboard and player count:**
```python
sql_null_profile_by_type = """
WITH player_counts AS (
    SELECT
        game_id,
        COUNT(*) AS actual_player_count
    FROM players_raw
    GROUP BY game_id
)
SELECT
    m.leaderboard,
    COALESCE(pc.actual_player_count, 0) AS actual_player_count,
    COUNT(*) AS null_profile_rows
FROM players_raw p
INNER JOIN matches_raw m ON p.game_id = m.game_id
LEFT JOIN player_counts pc ON p.game_id = pc.game_id
WHERE p.profile_id IS NULL
GROUP BY m.leaderboard, COALESCE(pc.actual_player_count, 0)
ORDER BY null_profile_rows DESC
"""
sql_queries["null_profile_by_type"] = sql_null_profile_by_type
null_prof_df = db.fetch_df(sql_null_profile_by_type)
print("NULL profile_id rows by leaderboard and player count:")
print(null_prof_df.to_string(index=False))
result["null_profile_id_by_type"] = null_prof_df.to_dict(orient="records")
```

**Verification:**
- Query runs without error. NULL profile_id distribution documented.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T08 -- Summary Statistics and Synthesis

**Objective:** Compute derived summary statistics and document the
cross-reference findings.

**Cell 22 -- markdown section:**
```markdown
## Summary and Synthesis
```

**Cell 23 -- summary computation:**
```python
# Consolidate key counts into a summary dict
# Use existing result values -- no new queries needed
sc = result["q4_set_comparison"]

result["summary"] = {
    "total_matches_in_dataset": MATCHES_TOTAL,
    "matches_with_player_data": MATCHES_TOTAL - MATCHES_WITHOUT_PLAYERS,
    "matches_without_player_data": MATCHES_WITHOUT_PLAYERS,
    "true_1v1_count": result["true_1v1_count"],
    "ranked_1v1_count": sc["ranked_1v1"],
    "overlap": sc["overlap_both"],
    "true_1v1_pct_of_all": round(result["true_1v1_count"] / MATCHES_TOTAL * 100, 4),
    "ranked_1v1_pct_of_all": round(sc["ranked_1v1"] / MATCHES_TOTAL * 100, 4),
    "profiling_notes": (
        f"Player-count method (actual_player_count=2) and leaderboard proxy "
        f"(leaderboard='random_map') overlap analysis complete. "
        f"Orphaned game_ids (no player rows): see cross_table_linkage from 01_03_01. "
        f"Duplicate impact bounded by duplicate_impact diagnostic above."
    ),
}

for k, v in result["summary"].items():
    if isinstance(v, (int, float)):
        print(f"  {k}: {v:,}" if isinstance(v, int) else f"  {k}: {v}")
    else:
        print(f"  {k}: {v}")
```

**Verification:**
- Summary dict contains all required keys.
- Percentages computed correctly.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T09 -- Visualization: Match-Type Breakdown Bar Chart

**Objective:** Produce a stacked/grouped bar chart showing the match-type
breakdown: true 1v1 vs ranked 1v1 vs overlap vs neither.

**Cell 24 -- bar chart:**
```python
# Bar chart: Venn-style breakdown
categories = ["Overlap\n(True AND Ranked)", "True 1v1 Only", "Ranked 1v1 Only", "Neither"]
values = [
    sc["overlap_both"],
    sc["true_only"],
    sc["ranked_only"],
    sc["neither"],
]
colors = ["#2ecc71", "#3498db", "#e67e22", "#95a5a6"]

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(categories, values, color=colors, edgecolor="black", linewidth=0.5)

# Add count labels on bars
for bar, val in zip(bars, values):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + MATCHES_TOTAL * 0.005,
        f"{val:,.0f}\n({val / MATCHES_TOTAL * 100:.1f}%)",
        ha="center", va="bottom", fontsize=9,
    )

ax.set_ylabel("Number of Matches")
ax.set_title(
    "aoestats: True 1v1 vs Ranked 1v1 (leaderboard='random_map') Comparison\n"
    f"Total matches: {MATCHES_TOTAL:,}",
    fontsize=11,
)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))

plt.tight_layout()
chart_path = profiling_dir / "01_03_02_match_type_breakdown.png"
fig.savefig(chart_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {chart_path}")
```

**Verification:**
- PNG file exists and is non-empty.
- Chart shows 4 categories with count labels.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T10 -- JSON Artifact

**Objective:** Write the complete result dict to the JSON artifact.

**Cell 25 -- write JSON:**
```python
# Add SQL queries to result for reproducibility (I6)
result["sql_queries"] = sql_queries

json_path = profiling_dir / "01_03_02_true_1v1_profile.json"
with open(json_path, "w") as f:
    json.dump(result, f, indent=2, default=str)
print(f"Saved: {json_path} ({json_path.stat().st_size:,} bytes)")

# Gate validation: required keys
for key in ["true_1v1_count", "ranked_1v1_count", "overlap",
            "q2_num_players_vs_actual_crosstab", "profiling_notes", "duplicate_impact"]:
    # ranked_1v1_count and overlap are nested under different keys
    if key == "ranked_1v1_count":
        assert result["q4_set_comparison"]["ranked_1v1"] > 0, f"Missing/zero: {key}"
    elif key == "overlap":
        assert "overlap_both" in result["q4_set_comparison"], f"Missing: {key}"
    elif key == "profiling_notes":
        assert "profiling_notes" in result["summary"], f"Missing summary key: {key}"
    elif key == "duplicate_impact":
        assert "duplicate_impact" in result, f"Missing key: {key}"
    else:
        assert key in result, f"Missing key: {key}"
print("Gate validation: all required JSON keys present.")
```

**Verification:**
- JSON file exists and is non-empty.
- Contains keys: true_1v1_count, q4_set_comparison (with ranked_1v1 and overlap_both),
  q2_num_players_vs_actual_crosstab, summary (with profiling_notes), duplicate_impact.
- SQL queries embedded verbatim (I6).

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

**Read scope:**
- All prior cells in the same notebook.

---

### T11 -- Markdown Report

**Objective:** Write the markdown report with comparison tables and all
SQL queries (I6).

**Cell 26 -- write markdown:**
```python
md_lines = [
    "# Step 01_03_02 -- True 1v1 Match Identification: aoestats",
    "",
    f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}",
    f"**Dataset:** aoestats",
    f"**Invariants:** #6 (SQL verbatim), #7 (no magic numbers), #9 (profiling only)",
    "",
    "## Summary",
    "",
    f"| Metric | Count | % of Total |",
    f"|--------|-------|------------|",
    f"| Total matches | {MATCHES_TOTAL:,} | 100.0% |",
    f"| Matches with player data | {MATCHES_TOTAL - MATCHES_WITHOUT_PLAYERS:,} | {(MATCHES_TOTAL - MATCHES_WITHOUT_PLAYERS) / MATCHES_TOTAL * 100:.2f}% |",
    f"| Matches without player data | {MATCHES_WITHOUT_PLAYERS:,} | {MATCHES_WITHOUT_PLAYERS / MATCHES_TOTAL * 100:.2f}% |",
    f"| **True 1v1** (2 player rows) | **{result['true_1v1_count']:,}** | **{result['summary']['true_1v1_pct_of_all']}%** |",
    f"| Ranked 1v1 (leaderboard='random_map') | {sc['ranked_1v1']:,} | {result['summary']['ranked_1v1_pct_of_all']}% |",
    "",
    "## Q1: Active Player Definition",
    "",
    "Every row in players_raw is an active player. The schema has no observer/",
    "spectator marker columns. winner is never NULL, civ is never NULL, team",
    "has values {0, 1} only. profile_id has 1,185 NULLs (0.0011%).",
    "",
    "## Q2: num_players vs Actual Player Count",
    "",
    "### Cross-tabulation",
    "",
]

# Add cross-tab table
cross_records = result["q2_num_players_vs_actual_crosstab"]
md_lines.append("| num_players | actual_player_count | match_count | pct |")
md_lines.append("|-------------|--------------------:|------------:|----:|")
for r in cross_records:
    md_lines.append(
        f"| {r['num_players']} | {r['actual_player_count']} "
        f"| {int(r['match_count']):,} | {r['pct']}% |"
    )

align = result["q2_alignment_summary"]
md_lines.extend([
    "",
    f"**Alignment:** {align['aligned_count']:,} / {align['total_matches']:,} "
    f"({align['aligned_pct']}%) of matches have num_players == actual player count.",
    f"**Mismatched:** {align['mismatched_count']:,} ({align['mismatched_pct']}%).",
    "",
    "## Q3: True 1v1 Count",
    "",
    f"**True 1v1 matches (exactly 2 player rows): {result['true_1v1_count']:,}**",
    "",
    "### By leaderboard",
    "",
    "| leaderboard | match_count | pct_of_true_1v1 |",
    "|-------------|------------:|----------------:|",
])
for r in result["true_1v1_by_leaderboard"]:
    md_lines.append(
        f"| {r['leaderboard']} | {int(r['match_count']):,} | {r['pct_of_true_1v1']}% |"
    )

md_lines.extend([
    "",
    "## Q4: True 1v1 vs Ranked 1v1 Comparison",
    "",
    "| Set | Count |",
    "|-----|------:|",
    f"| True 1v1 (A) | {sc['true_1v1']:,} |",
    f"| Ranked 1v1 (B) | {sc['ranked_1v1']:,} |",
    f"| A AND B (overlap) | {sc['overlap_both']:,} |",
    f"| A NOT B (true only) | {sc['true_only']:,} |",
    f"| B NOT A (ranked only) | {sc['ranked_only']:,} |",
    f"| Neither | {sc['neither']:,} |",
    "",
    f"**Jaccard index:** {result['q4_overlap_metrics']['jaccard_index']}",
    f"**Overlap as % of true 1v1:** {result['q4_overlap_metrics']['overlap_pct_of_true']}%",
    f"**Overlap as % of ranked 1v1:** {result['q4_overlap_metrics']['overlap_pct_of_ranked']}%",
    "",
    "### Ranked 1v1 with != 2 player rows (anomalies)",
    "",
])
if result["q4_ranked_not_true_1v1"]:
    md_lines.append("| num_players | actual_player_count | match_count |")
    md_lines.append("|-------------|--------------------:|------------:|")
    for r in result["q4_ranked_not_true_1v1"]:
        md_lines.append(
            f"| {r['num_players']} | {r['actual_player_count']} | {int(r['match_count']):,} |"
        )
else:
    md_lines.append("*No anomalies found.*")

md_lines.extend([
    "",
    "### True 1v1 from non-random_map leaderboards",
    "",
])
if result["q4_true_not_ranked"]:
    md_lines.append("| leaderboard | match_count | pct |")
    md_lines.append("|-------------|------------:|----:|")
    for r in result["q4_true_not_ranked"]:
        md_lines.append(
            f"| {r['leaderboard']} | {int(r['match_count']):,} | {r['pct']}% |"
        )
else:
    md_lines.append("*All true 1v1 matches are from random_map.*")

md_lines.extend([
    "",
    "## Visualization",
    "",
    "![Match type breakdown](01_03_02_match_type_breakdown.png)",
    "",
    "## SQL Queries (I6)",
    "",
])
for name, sql in sql_queries.items():
    md_lines.append(f"### {name}")
    md_lines.append("```sql")
    md_lines.append(sql.strip())
    md_lines.append("```")
    md_lines.append("")

md_path = profiling_dir / "01_03_02_true_1v1_profile.md"
md_path.write_text("\n".join(md_lines))
print(f"Saved: {md_path} ({md_path.stat().st_size:,} bytes)")
```

**Verification:**
- MD file exists and is non-empty.
- Contains comparison table (Q4 set comparison).
- Contains all SQL queries (I6).
- Contains link to PNG chart.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

**Read scope:**
- All prior cells in the same notebook.

---

### T12 -- Execute Notebook

**Objective:** Run the complete notebook end-to-end to produce all artifacts.

**Instructions:**
1. Run: `source .venv/bin/activate && poetry run jupytext --to notebook sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`
2. Run: `source .venv/bin/activate && poetry run jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=600 sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_02_true_1v1_identification.ipynb --output 01_03_02_true_1v1_identification.ipynb`
3. Verify all three artifact files exist and are non-empty:
   - `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json`
   - `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.md`
   - `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/03_profiling/01_03_02_match_type_breakdown.png`

**Verification:**
- All 3 artifact files exist and are non-empty.
- JSON contains keys: true_1v1_count, q4_set_comparison, q2_num_players_vs_actual_crosstab.
- MD contains comparison table.
- Notebook cell outputs show no errors.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_02_true_1v1_identification.ipynb` (generated by jupytext)

---

### T13 -- Status Updates

**Objective:** Update STEP_STATUS.yaml and research_log.md with step
completion.

**Instructions:**
1. Add step entry to `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml`:
```yaml
  "01_03_02":
    name: "True 1v1 Match Identification"
    pipeline_section: "01_03"
    status: complete
    completed_at: "<today's date>"
```
2. Add a research log entry to
   `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md`
   documenting:
   - Step number and name
   - Artifacts produced (3 files)
   - Key findings: true 1v1 count, ranked 1v1 count, overlap, the
     num_players vs actual alignment result, orphaned match count,
     Q1 conclusion (all player rows are active), any anomalies found
   - The recommended 1v1 definition for downstream use

**Verification:**
- STEP_STATUS.yaml contains `01_03_02: complete`.
- Research log contains an entry for `01_03_02`.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md`

---

## File Manifest

| File | Action |
|------|--------|
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` | Update (T01) |
| `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_02_true_1v1_identification.py` | Create (T02--T11) |
| `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_02_true_1v1_identification.ipynb` | Create (T12, generated by jupytext) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json` | Create (T10) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.md` | Create (T11) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/03_profiling/01_03_02_match_type_breakdown.png` | Create (T09) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml` | Update (T13) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md` | Update (T13) |

## Gate Condition

- All 3 artifact files exist under `reports/artifacts/01_exploration/03_profiling/` and are non-empty.
- `01_03_02_true_1v1_profile.json` contains keys: `true_1v1_count`,
  `q4_set_comparison` (with sub-keys `ranked_1v1`, `overlap_both`),
  `q2_num_players_vs_actual_crosstab`, `summary` (with sub-key `profiling_notes`),
  `duplicate_impact`, `sql_queries`.
- `01_03_02_true_1v1_profile.md` contains: Summary table, Q2 cross-tabulation
  table, Q4 set comparison table, SQL queries section.
- `01_03_02_match_type_breakdown.png` is a non-empty PNG file.
- Notebook executes end-to-end without errors.
- STEP_STATUS.yaml shows `01_03_02: complete`.
- All set comparison counts are internally consistent:
  overlap + true_only + ranked_only + neither = total_matches.

## Out of Scope

- **Cleaning decisions.** This step identifies and counts 1v1 matches. It does
  not drop non-1v1 matches, create a filtered view, or define the final
  analytical sample. Those decisions belong to 01_04 (Data Cleaning).
- **Feature engineering.** No derived features. No ELO difference computation.
- **Model fitting.** Profiling only (I9).
- **Cross-game comparison.** The SC2EGSet dataset has a different structure
  (replay files, not match records). Cross-game 1v1 identification comparison
  is deferred to Phase 06.
- **replay_summary_raw parsing.** The replay_summary_raw column (VARCHAR,
  cardinality 13,983,149) may contain embedded player metadata. Parsing it
  to identify observers is out of scope for this step; if needed, it would
  be a separate 01_03 step.
- **Duplicate player row resolution.** The 489 duplicate rows (from 01_03_01)
  are documented but not resolved here. Deduplication belongs to 01_04.

## Open Questions

- **OQ1: num_players reliability.** The cross-reference in T04 will reveal
  whether `num_players` always matches actual player count. If the alignment
  is near-perfect (excluding the 212,890 orphaned matches), `num_players` is
  a reliable proxy. If significant mismatches exist, the player-count method
  is the only trustworthy definition.

- **OQ2: Edge cases with odd num_players values.** The census shows
  num_players=1 (39 matches), num_players=3 (350), num_players=5 (327),
  num_players=7 (651). These odd values may indicate disconnected players,
  AI fill-ins, or data artifacts. T04's cross-reference will clarify whether
  these matches have matching odd player row counts.

- **OQ3: 212,890 orphaned matches.** These matches_raw rows have no
  corresponding players_raw rows. Likely caused by the missing-week gap
  (2025-11-16 to 2025-11-22) and possibly other data pipeline failures.
  The exact composition (by leaderboard, by num_players) will be visible in
  the cross-tabulation.

---

**Critique gate:** For Category A, adversarial critique is required before
execution begins. Dispatch reviewer-adversarial to produce
`planning/plan_aoestats_01_03_02.critique.md`.
```
