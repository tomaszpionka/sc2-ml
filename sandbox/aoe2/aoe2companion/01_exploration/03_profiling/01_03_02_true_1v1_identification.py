# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     notebook_metadata_filter: kernelspec,jupytext
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: .venv
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Step 01_03_02 -- True 1v1 Match Identification: aoe2companion
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

# %% Cell 2 -- imports
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

# %% Cell 3 -- DuckDB connection (read-only)
db = get_notebook_db("aoe2", "aoe2companion")
con = db.con
# Reduce memory pressure for large aggregations on this machine (22.3 GiB RAM)
con.execute("SET preserve_insertion_order=false")
con.execute("SET threads=2")
print("Connected via get_notebook_db: aoe2 / aoe2companion")

# %% Cell 4 -- load prior artifacts and path setup
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

# %% Cell 5 -- verify prerequisite keys from census
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

# %% Cell 6 -- initialize sql_queries dict
sql_queries = {}

print(f"Total rows: {total_rows:,}")

# %% Cell 7 -- rows-per-match distribution (all rows, exact)
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

# %% Cell 8 -- rows-per-match distribution by status (human vs AI)
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

# %% Cell 9 -- census profileId=-1
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

# %% Cell 10 -- leaderboards profileId = -1 rows in 1v1
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

# %% Cell 11 -- true 1v1 criteria funnel (separate queries to avoid OOM)
# Define 1v1 criteria levels:
# Level 1: matchId has exactly 2 total rows
# Level 2: matchId has exactly 2 rows AND both have status='player'
# Level 3: Level 2 AND both have won IS NOT NULL
# Level 4: Level 3 AND won values are complementary (one true, one false)
# Level 5: Level 4 AND both have distinct profileId (profileId != -1)
# Level 6: Level 5 AND both have team IS NOT NULL AND 2 distinct teams
#
# NOTE: The combined CTE with COUNT(DISTINCT) aggregates causes OOM on this
# machine (22.3 GiB). Using separate HAVING-based queries (no intermediate
# materialisation of complex aggregates) reduces peak memory usage.

# L1+L2+L3+L4: count only with simpler non-DISTINCT aggregates
criteria_funnel_sql_a = """
WITH match_stats AS (
    SELECT
        matchId,
        COUNT(*) AS total_rows,
        COUNT(*) FILTER (WHERE status = 'player') AS human_rows,
        COUNT(*) FILTER (WHERE won IS NOT NULL) AS won_nonnull,
        COUNT(*) FILTER (WHERE won = true) AS won_true,
        COUNT(*) FILTER (WHERE won = false) AS won_false
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
                     AND won_true = 1 AND won_false = 1) AS L4_complementary_won
FROM match_stats
"""
sql_queries["criteria_funnel_a"] = criteria_funnel_sql_a
print("Computing criteria funnel L1-L4 (no DISTINCT aggregates)...")
df_fa = con.execute(criteria_funnel_sql_a).fetchdf().iloc[0]
total_matches_val = int(df_fa["total_matches"])
l1_val = int(df_fa["L1_exactly_2_rows"])
l2_val = int(df_fa["L2_2_humans"])
l3_val = int(df_fa["L3_2_humans_won_known"])
l4_val = int(df_fa["L4_complementary_won"])
print(f"  total: {total_matches_val:,}, L1: {l1_val:,}, L2: {l2_val:,}, L3: {l3_val:,}, L4: {l4_val:,}")

# L5: add COUNT(DISTINCT profileId) filter -- use HAVING-based query on pre-filtered set
criteria_funnel_sql_b = """
SELECT COUNT(*) AS L5_distinct_profiles
FROM (
    SELECT matchId
    FROM matches_raw
    GROUP BY matchId
    HAVING COUNT(*) = 2
       AND COUNT(*) FILTER (WHERE status = 'player') = 2
       AND COUNT(*) FILTER (WHERE won = true) = 1
       AND COUNT(*) FILTER (WHERE won = false) = 1
       AND COUNT(DISTINCT profileId) FILTER (WHERE profileId != -1) = 2
)
"""
sql_queries["criteria_funnel_b"] = criteria_funnel_sql_b
print("Computing criteria funnel L5 (distinct profiles)...")
l5_val = int(con.execute(criteria_funnel_sql_b).fetchdf().iloc[0]["L5_distinct_profiles"])
print(f"  L5: {l5_val:,}")

# L6: L4 criteria + MIN(team) IS NOT NULL AND MIN(team) != MAX(team)
# Equivalent to COUNT(DISTINCT team) FILTER (WHERE team IS NOT NULL) = 2
# but avoids double COUNT(DISTINCT) which causes OOM.
# For a 2-row match: MIN(team) != MAX(team) with MIN(team) IS NOT NULL
# is equivalent to 2 distinct non-null team values.
criteria_funnel_sql_c = """
SELECT COUNT(*) AS L6_distinct_teams
FROM (
    SELECT matchId,
           MIN(team) AS min_team,
           MAX(team) AS max_team
    FROM matches_raw
    GROUP BY matchId
    HAVING COUNT(*) = 2
       AND COUNT(*) FILTER (WHERE status = 'player') = 2
       AND COUNT(*) FILTER (WHERE won = true) = 1
       AND COUNT(*) FILTER (WHERE won = false) = 1
       AND MIN(profileId) > -1
       AND MIN(profileId) != MAX(profileId)
)
WHERE min_team IS NOT NULL AND min_team != max_team
"""
sql_queries["criteria_funnel_c"] = criteria_funnel_sql_c
print("Computing criteria funnel L6 (distinct teams, MIN/MAX approach)...")
l6_val = int(con.execute(criteria_funnel_sql_c).fetchdf().iloc[0]["L6_distinct_teams"])
print(f"  L6: {l6_val:,}")

# Combine the three part-queries into a single documented SQL for I6
criteria_funnel_sql = (
    "-- Part A (L1-L4, no DISTINCT aggregates):\n" + criteria_funnel_sql_a
    + "\n-- Part B (L5, HAVING COUNT(DISTINCT profileId)):\n" + criteria_funnel_sql_b
    + "\n-- Part C (L6, HAVING COUNT(DISTINCT team)):\n" + criteria_funnel_sql_c
)
sql_queries["criteria_funnel"] = criteria_funnel_sql

funnel_levels = {
    "total_matches": total_matches_val,
    "L1_exactly_2_rows": l1_val,
    "L2_2_human_players": l2_val,
    "L3_2_humans_won_known": l3_val,
    "L4_complementary_won": l4_val,
    "L5_distinct_profiles": l5_val,
    "L6_distinct_teams": l6_val,
}

print(f"\n1v1 Criteria Funnel:")
for level, count in funnel_levels.items():
    pct = count * 100.0 / funnel_levels["total_matches"]
    print(f"  {level}: {count:,} ({pct:.2f}%)")

# %% Cell 11b -- W3 fix: deduplicated funnel (COUNT DISTINCT human profiles)
# W3 fix: Parallel funnel using HAVING with COUNT(DISTINCT profileId) on
# status='player' rows, to quantify matchIds recoverable by deduplication.
# The 12.4M duplicate rows (from 01_03_01) mean some matchIds may have
# COUNT(*) > 2 but only 2 distinct human profileIds.
# MEMORY NOTE: COUNT(DISTINCT) in HAVING causes OOM on this machine when
# combined with other HAVING clauses. Strategy: one COUNT(DISTINCT) per query
# at a time, evaluated as HAVING on raw table (no CTE materialisation).

# L1-dedup: exactly 2 distinct human profiles (ignores won and team)
criteria_funnel_dedup_sql_l1 = """
SELECT COUNT(*) AS L1_dedup_2_human_profiles
FROM (
    SELECT matchId
    FROM matches_raw
    WHERE profileId != -1 AND status = 'player'
    GROUP BY matchId
    HAVING COUNT(DISTINCT profileId) = 2
)
"""
sql_queries["criteria_funnel_dedup_l1"] = criteria_funnel_dedup_sql_l1
print("Computing dedup funnel L1...")
dedup_l1 = int(con.execute(criteria_funnel_dedup_sql_l1).fetchdf().iloc[0]["L1_dedup_2_human_profiles"])
print(f"  L1_dedup: {dedup_l1:,}")

# L2-dedup: 2 distinct human profiles + at least 2 non-null won values
# Use HAVING COUNT(*) FILTER on original table joined back by matchId
criteria_funnel_dedup_sql_l2 = """
SELECT COUNT(*) AS L2_dedup_won_known
FROM (
    SELECT matchId
    FROM matches_raw
    WHERE profileId != -1 AND status = 'player'
    GROUP BY matchId
    HAVING COUNT(DISTINCT profileId) = 2
) h
JOIN (
    SELECT matchId
    FROM matches_raw
    GROUP BY matchId
    HAVING COUNT(*) FILTER (WHERE won IS NOT NULL) >= 2
) w USING (matchId)
"""
sql_queries["criteria_funnel_dedup_l2"] = criteria_funnel_dedup_sql_l2
print("Computing dedup funnel L2...")
dedup_l2 = int(con.execute(criteria_funnel_dedup_sql_l2).fetchdf().iloc[0]["L2_dedup_won_known"])
print(f"  L2_dedup: {dedup_l2:,}")

# L3-dedup: 2 distinct human profiles + complementary won
criteria_funnel_dedup_sql_l3 = """
SELECT COUNT(*) AS L3_dedup_complementary_won
FROM (
    SELECT matchId
    FROM matches_raw
    WHERE profileId != -1 AND status = 'player'
    GROUP BY matchId
    HAVING COUNT(DISTINCT profileId) = 2
) h
JOIN (
    SELECT matchId
    FROM matches_raw
    GROUP BY matchId
    HAVING COUNT(*) FILTER (WHERE won = true) >= 1
       AND COUNT(*) FILTER (WHERE won = false) >= 1
) w USING (matchId)
"""
sql_queries["criteria_funnel_dedup_l3"] = criteria_funnel_dedup_sql_l3
print("Computing dedup funnel L3...")
dedup_l3 = int(con.execute(criteria_funnel_dedup_sql_l3).fetchdf().iloc[0]["L3_dedup_complementary_won"])
print(f"  L3_dedup: {dedup_l3:,}")

# L4-dedup: L3 + 2 distinct non-(-1) profileIds (already implied by L1)
# Since our L1 already filters profileId != -1, L4 = L3 for the dedup path
# Confirm explicitly:
criteria_funnel_dedup_sql_l4 = "-- L4_dedup = L3_dedup (profileId != -1 already enforced in L1 filter)"
sql_queries["criteria_funnel_dedup_l4"] = criteria_funnel_dedup_sql_l4
dedup_l4 = dedup_l3  # implied by the L1 WHERE profileId != -1 filter
print(f"  L4_dedup: {dedup_l4:,} (= L3_dedup, profileId filter already in L1)")

# L5-dedup: L3 + 2 distinct non-null teams (use MIN/MAX trick to avoid double DISTINCT)
criteria_funnel_dedup_sql_l5 = """
SELECT COUNT(*) AS L5_dedup_distinct_teams
FROM (
    SELECT matchId
    FROM matches_raw
    WHERE profileId != -1 AND status = 'player'
    GROUP BY matchId
    HAVING COUNT(DISTINCT profileId) = 2
) h
JOIN (
    SELECT matchId,
           MIN(team) AS min_team,
           MAX(team) AS max_team
    FROM matches_raw
    GROUP BY matchId
    HAVING COUNT(*) FILTER (WHERE won = true) >= 1
       AND COUNT(*) FILTER (WHERE won = false) >= 1
) w USING (matchId)
WHERE w.min_team IS NOT NULL AND w.min_team != w.max_team
"""
sql_queries["criteria_funnel_dedup_l5"] = criteria_funnel_dedup_sql_l5
print("Computing dedup funnel L5...")
dedup_l5 = int(con.execute(criteria_funnel_dedup_sql_l5).fetchdf().iloc[0]["L5_dedup_distinct_teams"])
print(f"  L5_dedup: {dedup_l5:,}")

criteria_funnel_dedup_sql = (
    "-- Dedup L1 (2 distinct human profiles):\n" + criteria_funnel_dedup_sql_l1
    + "\n-- Dedup L2 (+ won_nonnull >= 2):\n" + criteria_funnel_dedup_sql_l2
    + "\n-- Dedup L3 (+ complementary won):\n" + criteria_funnel_dedup_sql_l3
    + "\n-- Dedup L4 (= L3, profileId filter in L1):\n" + criteria_funnel_dedup_sql_l4
    + "\n-- Dedup L5 (+ distinct teams):\n" + criteria_funnel_dedup_sql_l5
)
sql_queries["criteria_funnel_dedup"] = criteria_funnel_dedup_sql

funnel_levels_dedup = {
    "total_matches": total_matches_val,
    "L1_dedup_2_human_profiles": dedup_l1,
    "L2_dedup_won_known": dedup_l2,
    "L3_dedup_complementary_won": dedup_l3,
    "L4_dedup_distinct_profiles": dedup_l4,
    "L5_dedup_distinct_teams": dedup_l5,
}
print(f"\n1v1 Criteria Funnel (DEDUP):")
for level, count in funnel_levels_dedup.items():
    pct = count * 100.0 / funnel_levels_dedup["total_matches"]
    print(f"  {level}: {count:,} ({pct:.2f}%)")

# Delta at L1: matchIds recovered by deduplication
dedup_delta_l1 = funnel_levels_dedup["L1_dedup_2_human_profiles"] - funnel_levels["L1_exactly_2_rows"]
print(f"\nDedup delta at L1: {dedup_delta_l1:+,} matchIds recovered")
dedup_delta = {"L1_delta": dedup_delta_l1, "note": "Positive = matchIds recovered by dedup"}

# %% Cell 12 -- characterize the drop at each funnel level
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

# %% Cell 12b -- B1 fix (a): leaderboard cardinality per matchId diagnostic
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

# %% Cell 13 -- leaderboard overlap with true 1v1
# Use L4 (complementary won, 2 humans) as the structural 1v1 criterion.
# Avoids ARRAY_AGG and CARDINALITY (MAP-only in this DuckDB version);
# uses COUNT(DISTINCT leaderboard) and MIN(leaderboard) for single-leaderboard
# category assignment. Multi-leaderboard matchIds (where n_leaderboards > 1)
# are grouped as 'multi_leaderboard'. For single-leaderboard matchIds, we
# use MIN(leaderboard) = the only leaderboard value.
leaderboard_overlap_sql = """
WITH match_stats AS (
    SELECT matchId,
           COUNT(*) AS total_rows,
           COUNT(*) FILTER (WHERE status = 'player') AS human_rows,
           COUNT(*) FILTER (WHERE won = true) AS won_true,
           COUNT(*) FILTER (WHERE won = false) AS won_false,
           COUNT(DISTINCT leaderboard) AS n_leaderboards,
           MIN(leaderboard) AS min_leaderboard
    FROM matches_raw
    GROUP BY matchId
),
classified AS (
    SELECT *,
           (total_rows = 2 AND human_rows = 2
            AND won_true = 1 AND won_false = 1) AS is_structural_1v1,
           CASE
               WHEN n_leaderboards > 1 THEN 'multi_leaderboard'
               WHEN min_leaderboard = 'rm_1v1' THEN 'rm_1v1_only'
               WHEN min_leaderboard = 'qp_rm_1v1' THEN 'qp_rm_1v1_only'
               ELSE min_leaderboard
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

# %% Cell 14 -- proxy vs structural confusion matrix
# 2x2 confusion matrix: proxy_1v1 (leaderboard rm_1v1/qp_rm_1v1) vs structural_1v1
# Uses COUNT(DISTINCT leaderboard) and MIN(leaderboard) to categorize matchIds.
confusion_sql = """
WITH match_stats AS (
    SELECT matchId,
           COUNT(*) AS total_rows,
           COUNT(*) FILTER (WHERE status = 'player') AS human_rows,
           COUNT(*) FILTER (WHERE won = true) AS won_true,
           COUNT(*) FILTER (WHERE won = false) AS won_false,
           COUNT(DISTINCT leaderboard) AS n_leaderboards,
           MIN(leaderboard) AS min_leaderboard,
           MAX(leaderboard) AS max_leaderboard
    FROM matches_raw
    GROUP BY matchId
),
classified AS (
    SELECT *,
           (total_rows = 2 AND human_rows = 2
            AND won_true = 1 AND won_false = 1) AS is_structural_1v1,
           CASE
               WHEN n_leaderboards > 1 THEN 'multi_leaderboard'
               WHEN min_leaderboard IN ('rm_1v1', 'qp_rm_1v1') THEN 'rm_1v1_only'
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

# %% Cell 15 -- all-1v1-leaderboards overlap (expanded proxy)
# Expand to all leaderboards with avg_rows_per_match = 2.0 from census.
# Uses COUNT(DISTINCT leaderboard) and MIN(leaderboard) to categorize matchIds.
all_1v1_leaderboards_sql = """
WITH match_stats AS (
    SELECT matchId,
           COUNT(*) AS total_rows,
           COUNT(*) FILTER (WHERE status = 'player') AS human_rows,
           COUNT(*) FILTER (WHERE won = true) AS won_true,
           COUNT(*) FILTER (WHERE won = false) AS won_false,
           COUNT(DISTINCT leaderboard) AS n_leaderboards,
           MIN(leaderboard) AS min_leaderboard
    FROM matches_raw
    GROUP BY matchId
),
classified AS (
    SELECT *,
           (total_rows = 2 AND human_rows = 2
            AND won_true = 1 AND won_false = 1) AS is_structural_1v1,
           CASE
               WHEN n_leaderboards > 1 THEN 'multi_leaderboard'
               WHEN min_leaderboard IN (
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

# %% Cell 16 -- won complement analysis for 2-human matches
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

# %% Cell 17 -- team analysis for structural 1v1 matches
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

# %% Cell 18 -- assemble and write JSON
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

# %% Cell 19 -- generate markdown report
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
        f"| {entry['leaderboard_category']} | {entry['total_matches']:,} | "
        f"{entry['structural_1v1']:,} | {entry['pct_structural_1v1']} |"
    )
md_lines.append(f"\n```sql\n{sql_queries['leaderboard_structural_1v1_overlap']}\n```\n")

md_lines.append("### 6b. Proxy vs structural confusion matrix (rm_1v1 + qp_rm_1v1)\n")
md_lines.append("| Leaderboard Category | Structural 1v1 | Matches |")
md_lines.append("|---|---|---|")
for entry in confusion_matrix:
    md_lines.append(
        f"| {entry['leaderboard_category']} | {entry['is_structural_1v1']} | "
        f"{entry['n_matches']:,} |"
    )
md_lines.append(f"\n```sql\n{sql_queries['proxy_vs_structural_confusion']}\n```\n")

md_lines.append("### 6c. Expanded proxy (all 1v1 leaderboards) vs structural\n")
md_lines.append("| Leaderboard Category | Structural 1v1 | Matches |")
md_lines.append("|---|---|---|")
for entry in expanded_proxy_confusion:
    md_lines.append(
        f"| {entry['leaderboard_category']} | {entry['is_structural_1v1']} | "
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
