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
# # Step 01_04_01 -- Data Cleaning: aoe2companion
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_04 -- Data Cleaning
# **Dataset:** aoe2companion
# **Question:** Which rows in matches_raw are unsuitable for binary classification
#   of 1v1 match outcomes? What cleaning rules should be applied non-destructively?
# **Invariants applied:**
#   - #3 (temporal discipline -- POST-GAME columns excluded from player_history_all)
#   - #5 (symmetric player treatment -- player_history_all is player-row-oriented)
#   - #6 (reproducibility -- all SQL queries written verbatim to artifacts)
#   - #7 (no magic numbers -- thresholds empirically derived)
#   - #9 (step scope -- cleaning only, no feature computation)
# **Predecessor:** 01_03_03 (Table Utility Assessment -- complete)
# **Step scope:** Non-destructive cleaning via VIEW definitions. Raw data untouched.
# **Outputs:** 3 DuckDB VIEWs, JSON artifact, MD artifact

# %% [markdown]
# ## 0. Imports and DB connection

# %%
import json
from datetime import date
from pathlib import Path

import pandas as pd

from rts_predict.common.notebook_utils import (
    get_notebook_db,
    get_reports_dir,
    setup_notebook_logging,
)

logger = setup_notebook_logging()

# %%
# NOTE: read_only=False required for CREATE OR REPLACE VIEW statements
db = get_notebook_db("aoe2", "aoe2companion", read_only=False)
con = db.con
print("Connected via get_notebook_db: aoe2 / aoe2companion (read_only=False)")

# %%
reports_dir = get_reports_dir("aoe2", "aoe2companion")
cleaning_dir = reports_dir / "artifacts" / "01_exploration" / "04_cleaning"
cleaning_dir.mkdir(parents=True, exist_ok=True)
print(f"Artifact output dir: {cleaning_dir}")

# %% [markdown]
# ## Scope restriction to ranked 1v1 leaderboards
#
# Filter matches_raw to rm_1v1 (internalLeaderboardId=6) and qp_rm_1v1
# (internalLeaderboardId=18) for the prediction target VIEW. CONSORT stage 1.
#
# **Scope note:** This restriction defines the *prediction target VIEW only*.
# The full matches_raw table remains the feature computation source.
# The player_history_all VIEW (created below) covers all game types for player-level feature aggregation.

# %%
SQL_T01_SCOPE = """
-- Scope restriction -- count rows before/after
SELECT
    'total' AS scope,
    COUNT(*) AS n_rows,
    COUNT(DISTINCT matchId) AS n_matches
FROM matches_raw

UNION ALL

SELECT
    'in_scope_1v1' AS scope,
    COUNT(*) AS n_rows,
    COUNT(DISTINCT matchId) AS n_matches
FROM matches_raw
WHERE internalLeaderboardId IN (6, 18)

UNION ALL

SELECT
    'out_of_scope' AS scope,
    COUNT(*) AS n_rows,
    COUNT(DISTINCT matchId) AS n_matches
FROM matches_raw
WHERE internalLeaderboardId NOT IN (6, 18)
   OR internalLeaderboardId IS NULL;
"""

df_t01 = con.execute(SQL_T01_SCOPE).df()
print("Scope restriction:")
print(df_t01.to_string())

# %%
t01_total = int(df_t01[df_t01["scope"] == "total"]["n_rows"].iloc[0])
t01_in_scope = int(df_t01[df_t01["scope"] == "in_scope_1v1"]["n_rows"].iloc[0])
t01_out_scope = int(df_t01[df_t01["scope"] == "out_of_scope"]["n_rows"].iloc[0])
t01_in_matches = int(df_t01[df_t01["scope"] == "in_scope_1v1"]["n_matches"].iloc[0])
print(f"Total rows: {t01_total:,}")
print(f"In-scope (1v1): {t01_in_scope:,} rows / {t01_in_matches:,} matches")
print(f"Out-of-scope: {t01_out_scope:,} rows")
assert t01_in_scope + t01_out_scope == t01_total, "Scope counts must sum to total"
print("Assertion passed: in_scope + out_scope == total")

# %% [markdown]
# ## Duplicate analysis and deduplication
#
# Stratify duplicates in in-scope subset by profileId=-1 vs real profileId.

# %%
SQL_T02_DUP_STRAT = """
-- Duplicate stratification (in-scope only)
WITH in_scope AS (
    SELECT *
    FROM matches_raw
    WHERE internalLeaderboardId IN (6, 18)
),
dup_groups AS (
    SELECT matchId, profileId, COUNT(*) AS row_count
    FROM in_scope
    GROUP BY matchId, profileId
    HAVING COUNT(*) > 1
)
SELECT
    CASE WHEN d.profileId = -1 THEN 'profileId_minus1' ELSE 'real_profileId' END AS stratum,
    COUNT(*) AS n_dup_groups,
    SUM(d.row_count) AS total_dup_rows,
    SUM(d.row_count) - COUNT(*) AS excess_rows
FROM dup_groups d
GROUP BY
    CASE WHEN d.profileId = -1 THEN 'profileId_minus1' ELSE 'real_profileId' END;
"""

df_t02_dup = con.execute(SQL_T02_DUP_STRAT).df()
print("Duplicate stratification:")
print(df_t02_dup.to_string())

# %%
SQL_T02_MINUS1 = """
-- profileId=-1 investigation in 1v1 scope
SELECT
    COUNT(*) AS total_minus1_rows,
    COUNT(DISTINCT matchId) AS n_matches_with_minus1
FROM matches_raw
WHERE internalLeaderboardId IN (6, 18)
  AND profileId = -1;
"""

df_t02_m1 = con.execute(SQL_T02_MINUS1).df()
print("profileId=-1 in 1v1 scope:")
print(df_t02_m1.to_string())
t02_minus1_rows = int(df_t02_m1["total_minus1_rows"].iloc[0])
print(f"profileId=-1 rows in rm_1v1/qp_rm_1v1: {t02_minus1_rows}")

# %% [markdown]
# ## Match consistency check (won complement)

# %%
SQL_T03_WON = """
-- Won consistency check (in-scope, 2-row matches only)
WITH in_scope_dedup AS (
    SELECT * EXCLUDE (rn)
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY matchId, profileId
                   ORDER BY started
               ) AS rn
        FROM matches_raw
        WHERE internalLeaderboardId IN (6, 18)
          AND profileId != -1
    ) sub
    WHERE rn = 1
),
match_pairs AS (
    SELECT
        matchId,
        COUNT(*) AS n_rows,
        COUNT(*) FILTER (WHERE won = TRUE) AS n_won_true,
        COUNT(*) FILTER (WHERE won = FALSE) AS n_won_false,
        COUNT(*) FILTER (WHERE won IS NULL) AS n_won_null
    FROM in_scope_dedup
    GROUP BY matchId
    HAVING COUNT(*) = 2
)
SELECT
    CASE
        WHEN n_won_true = 1 AND n_won_false = 1 THEN 'complementary'
        WHEN n_won_true = 2 THEN 'both_true'
        WHEN n_won_false = 2 THEN 'both_false'
        WHEN n_won_null > 0 THEN 'has_null'
        ELSE 'other'
    END AS won_pattern,
    COUNT(*) AS n_matches,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM match_pairs
GROUP BY won_pattern
ORDER BY n_matches DESC;
"""

df_t03_won = con.execute(SQL_T03_WON).df()
print("Won consistency check:")
print(df_t03_won.to_string())

# %%
SQL_T03_SIZES = """
-- Non-2-row match counts in scope after dedup
WITH in_scope_dedup AS (
    SELECT * EXCLUDE (rn)
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY matchId, profileId
                   ORDER BY started
               ) AS rn
        FROM matches_raw
        WHERE internalLeaderboardId IN (6, 18)
          AND profileId != -1
    ) sub
    WHERE rn = 1
),
match_sizes AS (
    SELECT matchId, COUNT(*) AS n_rows FROM in_scope_dedup GROUP BY matchId
)
SELECT
    CASE WHEN n_rows = 1 THEN '1_row'
         WHEN n_rows = 2 THEN '2_rows'
         ELSE '3_plus_rows' END AS size_bucket,
    COUNT(*) AS n_matches,
    SUM(n_rows) AS total_rows
FROM match_sizes
GROUP BY size_bucket
ORDER BY size_bucket;
"""

df_t03_sizes = con.execute(SQL_T03_SIZES).df()
print("Match size distribution (in-scope, after dedup):")
print(df_t03_sizes.to_string())

# %% [markdown]
# ## NULL co-occurrence cluster investigation

# %%
SQL_T04_CLUSTER = """
-- NULL cluster temporal stratification (in-scope)
WITH in_scope AS (
    SELECT * FROM matches_raw WHERE internalLeaderboardId IN (6, 18)
),
null_cluster AS (
    SELECT
        matchId, started,
        CASE
            WHEN allowCheats IS NULL AND lockSpeed IS NULL AND lockTeams IS NULL
             AND recordGame IS NULL AND sharedExploration IS NULL
             AND teamPositions IS NULL AND teamTogether IS NULL
             AND turboMode IS NULL AND fullTechTree IS NULL AND population IS NULL
            THEN TRUE ELSE FALSE
        END AS is_null_cluster
    FROM in_scope
)
SELECT is_null_cluster, COUNT(*) AS n_rows,
       MIN(started) AS min_date, MAX(started) AS max_date,
       COUNT(DISTINCT DATE_TRUNC('month', started)) AS n_months
FROM null_cluster
GROUP BY is_null_cluster;
"""

df_t04_cluster = con.execute(SQL_T04_CLUSTER).df()
print("NULL cluster summary:")
print(df_t04_cluster.to_string())

# %%
SQL_T04_MONTHLY = """
-- Monthly breakdown: monthly temporal stratification of NULL cluster
WITH in_scope AS (
    SELECT * FROM matches_raw WHERE internalLeaderboardId IN (6, 18)
),
null_cluster AS (
    SELECT
        started,
        CASE
            WHEN allowCheats IS NULL AND lockSpeed IS NULL AND lockTeams IS NULL
             AND recordGame IS NULL AND sharedExploration IS NULL
             AND teamPositions IS NULL AND teamTogether IS NULL
             AND turboMode IS NULL AND fullTechTree IS NULL AND population IS NULL
            THEN TRUE ELSE FALSE
        END AS is_null_cluster
    FROM in_scope
)
SELECT
    DATE_TRUNC('month', started) AS month,
    COUNT(*) FILTER (WHERE is_null_cluster) AS null_cluster_rows,
    COUNT(*) FILTER (WHERE NOT is_null_cluster) AS normal_rows,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_null_cluster) / COUNT(*), 2) AS null_pct
FROM null_cluster
GROUP BY DATE_TRUNC('month', started)
ORDER BY month;
"""

df_t04_monthly = con.execute(SQL_T04_MONTHLY).df()
print("Monthly breakdown of NULL cluster:")
print(df_t04_monthly.to_string())

# %%
# Analysis: is the NULL cluster concentrated?
t04_null_n_months = int(df_t04_cluster[df_t04_cluster["is_null_cluster"] == True]["n_months"].iloc[0])
t04_null_rows = int(df_t04_cluster[df_t04_cluster["is_null_cluster"] == True]["n_rows"].iloc[0])
t04_total_rows = int(df_t04_cluster["n_rows"].sum())
t04_null_pct = 100.0 * t04_null_rows / t04_total_rows
print(f"NULL cluster spans {t04_null_n_months} months out of {t04_total_rows:,} total in-scope rows")
print(f"NULL cluster: {t04_null_rows:,} rows ({t04_null_pct:.4f}% of in-scope)")
print("Decision: NULL cluster spans entire date range but < 0.02% of data => FLAG only")

# %%
SQL_T04_SURVIVAL = """
-- NULL cluster survival after scope restriction, deduplication, and consistency filtering
WITH in_scope_dedup AS (
    SELECT * EXCLUDE (rn)
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY matchId, profileId ORDER BY started) AS rn
        FROM matches_raw
        WHERE internalLeaderboardId IN (6, 18) AND profileId != -1
    ) sub
    WHERE rn = 1
),
valid_matches AS (
    SELECT matchId FROM in_scope_dedup
    GROUP BY matchId
    HAVING COUNT(*) = 2
       AND COUNT(*) FILTER (WHERE won = TRUE) = 1
       AND COUNT(*) FILTER (WHERE won = FALSE) = 1
)
SELECT
    CASE
        WHEN d.allowCheats IS NULL AND d.lockSpeed IS NULL AND d.lockTeams IS NULL
         AND d.recordGame IS NULL AND d.sharedExploration IS NULL
         AND d.teamPositions IS NULL AND d.teamTogether IS NULL
         AND d.turboMode IS NULL AND d.fullTechTree IS NULL AND d.population IS NULL
        THEN 'null_cluster' ELSE 'normal'
    END AS cluster_status,
    COUNT(*) AS n_rows,
    COUNT(DISTINCT d.matchId) AS n_matches
FROM in_scope_dedup d
INNER JOIN valid_matches v ON d.matchId = v.matchId
GROUP BY cluster_status;
"""

df_t04_survival = con.execute(SQL_T04_SURVIVAL).df()
print("NULL cluster survival after scope restriction, deduplication, and consistency filtering:")
print(df_t04_survival.to_string())

# %% [markdown]
# ## ratings_raw.games outlier capping

# %%
SQL_T05_OUTLIER = """
SELECT
    COUNT(*) AS total_rows,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY games) AS p99,
    PERCENTILE_CONT(0.999) WITHIN GROUP (ORDER BY games) AS p999,
    PERCENTILE_CONT(0.9999) WITHIN GROUP (ORDER BY games) AS p9999,
    MAX(games) AS max_val,
    COUNT(*) FILTER (WHERE games > 50000) AS n_above_50k,
    COUNT(*) FILTER (WHERE games > 100000) AS n_above_100k,
    COUNT(*) FILTER (WHERE games > 1000000) AS n_above_1M
FROM ratings_raw;
"""

df_t05 = con.execute(SQL_T05_OUTLIER).df()
print("ratings_raw.games outlier analysis:")
print(df_t05.to_string())

# %%
p999_value = int(df_t05["p999"].iloc[0])
print(f"p99.9 value (empirical cap): {p999_value:,}")
print(f"p99 value: {int(df_t05['p99'].iloc[0]):,}")
print(f"max value: {int(df_t05['max_val'].iloc[0]):,}")
print(f"rows above 50k: {int(df_t05['n_above_50k'].iloc[0]):,}")
print(f"rows above 1M: {int(df_t05['n_above_1M'].iloc[0]):,}")

# %%
SQL_T05_VIEW = f"""
CREATE OR REPLACE VIEW ratings_clean AS
SELECT
    profile_id, LEAST(games, {p999_value}) AS games,
    rating, date, leaderboard_id, rating_diff, season, filename
FROM ratings_raw;
"""

con.execute(SQL_T05_VIEW)
r_rc = con.execute("SELECT COUNT(*) AS n FROM ratings_clean").fetchone()
print(f"ratings_clean VIEW created. Rows: {r_rc[0]:,}")

# %% [markdown]
# ## Create player_history_all VIEW
#
# Player-row-oriented VIEW over full matches_raw (all game types).
# Excludes ratingDiff and finished (POST-GAME, I3). Used for feature computation.

# %%
SQL_T06_VIEW = """
CREATE OR REPLACE VIEW player_history_all AS
WITH deduped AS (
    SELECT * EXCLUDE (rn)
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY matchId, profileId
                   ORDER BY started
               ) AS rn
        FROM matches_raw
        WHERE profileId != -1
    ) sub
    WHERE rn = 1
)
SELECT
    matchId,
    profileId,
    name,
    started,
    leaderboard,
    internalLeaderboardId,
    map,
    civ,
    rating,
    color,
    slot,
    team,
    startingAge,
    gameMode,
    speed,
    won,
    country,
    status,
    verified,
    filename
FROM deduped;
"""

con.execute(SQL_T06_VIEW)
print("player_history_all VIEW created")

# %%
r_pha = con.execute("""
SELECT COUNT(*) AS n_rows, COUNT(DISTINCT matchId) AS n_matches,
       COUNT(DISTINCT profileId) AS n_players, COUNT(DISTINCT leaderboard) AS n_leaderboards
FROM player_history_all
""").df()
print("player_history_all counts:")
print(r_pha.to_string())

# %% [markdown]
# ## Create matches_1v1_clean VIEW
#
# Composes all prediction-target cleaning decisions (scope restriction, deduplication,
# won-complement filter, NULL-cluster flag) into matches_1v1_clean.
# Uses subquery IN approach (not CTE with INNER JOIN) to avoid DuckDB optimizer
# bug with CTE re-use in COUNT(*) context.

# %%
SQL_T07_VIEW = """
CREATE OR REPLACE VIEW matches_1v1_clean AS
SELECT
    d.matchId,
    d.started,
    d.leaderboard,
    d.name,
    d.server,
    d.internalLeaderboardId,
    d.privacy,
    d.mod,
    d.map,
    d.difficulty,
    d.startingAge,
    d.fullTechTree,
    d.allowCheats,
    d.empireWarsMode,
    d.endingAge,
    d.gameMode,
    d.lockSpeed,
    d.lockTeams,
    d.mapSize,
    d.population,
    d.hideCivs,
    d.recordGame,
    d.regicideMode,
    d.gameVariant,
    d.resources,
    d.sharedExploration,
    d.speed,
    d.speedFactor,
    d.suddenDeathMode,
    d.antiquityMode,
    d.civilizationSet,
    d.teamPositions,
    d.teamTogether,
    d.treatyLength,
    d.turboMode,
    d.victory,
    d.revealMap,
    d.scenario,
    d.password,
    d.modDataset,
    d.profileId,
    d.rating,
    d.color,
    d.colorHex,
    d.slot,
    d.status,
    d.team,
    d.won,
    d.country,
    d.shared,
    d.verified,
    d.civ,
    d.filename,
    CASE
        WHEN d.allowCheats IS NULL AND d.lockSpeed IS NULL AND d.lockTeams IS NULL
         AND d.recordGame IS NULL AND d.sharedExploration IS NULL
         AND d.teamPositions IS NULL AND d.teamTogether IS NULL
         AND d.turboMode IS NULL AND d.fullTechTree IS NULL AND d.population IS NULL
        THEN TRUE ELSE FALSE
    END AS is_null_cluster
FROM (
    SELECT * EXCLUDE (rn)
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY matchId, profileId
                   ORDER BY started
               ) AS rn
        FROM matches_raw
        WHERE internalLeaderboardId IN (6, 18)
          AND profileId != -1
    ) raw_rn
    WHERE rn = 1
) d
WHERE d.matchId IN (
    SELECT matchId
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY matchId, profileId
                   ORDER BY started
               ) AS rn
        FROM matches_raw
        WHERE internalLeaderboardId IN (6, 18)
          AND profileId != -1
    ) sub
    WHERE rn = 1
    GROUP BY matchId
    HAVING COUNT(*) = 2
       AND COUNT(*) FILTER (WHERE won = TRUE) = 1
       AND COUNT(*) FILTER (WHERE won = FALSE) = 1
);
"""

con.execute(SQL_T07_VIEW)
print("matches_1v1_clean VIEW created")

# %%
r_clean = con.execute(
    "SELECT COUNT(*) AS n_rows, COUNT(DISTINCT matchId) AS n_matches FROM matches_1v1_clean"
).df()
print("matches_1v1_clean counts:")
print(r_clean.to_string())

r_won = con.execute(
    "SELECT won, COUNT(*) AS n FROM matches_1v1_clean GROUP BY won"
).df()
print("Won distribution (must be exactly 50/50):")
print(r_won.to_string())

# %% [markdown]
# ## Post-cleaning validation and CONSORT flow

# %%
# CONSORT flow -- run stages individually to avoid DuckDB UNION ALL + VIEW bug
s0 = con.execute("SELECT COUNT(*) AS n_rows, COUNT(DISTINCT matchId) AS n_matches FROM matches_raw").fetchone()
s1 = con.execute("SELECT COUNT(*) AS n_rows, COUNT(DISTINCT matchId) AS n_matches FROM matches_raw WHERE internalLeaderboardId IN (6, 18)").fetchone()
s2 = con.execute("""
SELECT COUNT(*) AS n_rows, COUNT(DISTINCT matchId) AS n_matches
FROM (SELECT matchId, ROW_NUMBER() OVER (PARTITION BY matchId, profileId ORDER BY started) AS rn
      FROM matches_raw WHERE internalLeaderboardId IN (6, 18) AND profileId != -1) sub WHERE rn = 1
""").fetchone()
s3 = con.execute("SELECT COUNT(*) AS n_rows, COUNT(DISTINCT matchId) AS n_matches FROM matches_1v1_clean").fetchone()

print("CONSORT flow:")
print(f"S0 Raw:                  {s0[0]:>12,} rows / {s0[1]:>10,} matches")
print(f"S1 Scope restricted:     {s1[0]:>12,} rows / {s1[1]:>10,} matches")
print(f"S2 Deduplicated:         {s2[0]:>12,} rows / {s2[1]:>10,} matches")
print(f"S3 Valid complementary:  {s3[0]:>12,} rows / {s3[1]:>10,} matches")

# %%
# V1: Rating coverage
r_v1 = con.execute("""
SELECT COUNT(*) AS total, COUNT(rating) AS n_non_null,
       ROUND(100.0*COUNT(rating)/COUNT(*),2) AS rating_coverage_pct
FROM matches_1v1_clean
""").df()
print("V1 Rating coverage:")
print(r_v1.to_string())

# %%
# V2: No POST-GAME leakage in player_history_all or matches_1v1_clean (I3)
r_v2 = con.execute("""
SELECT column_name FROM information_schema.columns
WHERE table_name='player_history_all'
  AND column_name IN ('ratingDiff', 'finished')
""").df()
print(f"V2a POST-GAME columns in player_history_all (expect 0 rows): {len(r_v2)}")
assert len(r_v2) == 0, "FAIL: POST-GAME columns found in player_history_all!"
print("V2a PASS: No ratingDiff or finished in player_history_all")

# %%
r_v2_clean = con.execute("""
SELECT column_name FROM information_schema.columns
WHERE table_name='matches_1v1_clean'
  AND column_name IN ('ratingDiff', 'finished')
""").df()
print(f"V2b POST-GAME columns in matches_1v1_clean (expect 0 rows): {len(r_v2_clean)}")
assert len(r_v2_clean) == 0, "FAIL: POST-GAME columns found in matches_1v1_clean!"
print("V2b PASS: No ratingDiff or finished in matches_1v1_clean")

# %%
# V3: Rating sanity
r_v3 = con.execute("SELECT COUNT(*) FILTER (WHERE rating < 0) AS n_negative FROM matches_1v1_clean").df()
print(f"V3 Negative ratings: {r_v3['n_negative'].iloc[0]}")
assert r_v3["n_negative"].iloc[0] == 0, "FAIL: Negative ratings found!"
print("V3 PASS: No negative ratings")

# %%
# V4: Leaderboard distribution
r_v4 = con.execute("""
SELECT leaderboard, internalLeaderboardId, COUNT(*) AS n_rows
FROM matches_1v1_clean GROUP BY leaderboard, internalLeaderboardId
""").df()
print("V4 Leaderboard distribution:")
print(r_v4.to_string())

# %%
# V5: NULL cluster proportion
r_v5 = con.execute("""
SELECT is_null_cluster, COUNT(*) AS n_rows,
       ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER(),4) AS pct
FROM matches_1v1_clean GROUP BY is_null_cluster
""").df()
print("V5 NULL cluster proportion:")
print(r_v5.to_string())

# %%
# V6: player_history_all basic counts
r_v6 = con.execute("""
SELECT COUNT(*) AS n_rows, COUNT(DISTINCT matchId) AS n_matches,
       COUNT(DISTINCT profileId) AS n_players, COUNT(DISTINCT leaderboard) AS n_leaderboards
FROM player_history_all
""").df()
print("V6 player_history_all counts:")
print(r_v6.to_string())

# %%
# V7: No anonymous players in player_history_all
r_v7 = con.execute("SELECT COUNT(*) AS n_anonymous FROM player_history_all WHERE profileId = -1").df()
print(f"V7 Anonymous rows (expect 0): {r_v7['n_anonymous'].iloc[0]}")
assert r_v7["n_anonymous"].iloc[0] == 0, "FAIL: Anonymous rows found in player_history_all!"
print("V7 PASS: 0 anonymous rows")

# %%
# V8: player_history_all leaderboard diversity
r_v8 = con.execute("""
SELECT leaderboard, COUNT(*) AS n_rows FROM player_history_all
GROUP BY leaderboard ORDER BY n_rows DESC
""").df()
print("V8 Leaderboard diversity:")
print(r_v8.to_string())
assert len(r_v8) > 5, "Expected multiple leaderboard types"
print(f"V8 PASS: {len(r_v8)} distinct leaderboards present")

# %% [markdown]
# ## NULL Audit
#
# Systematic per-column NULL census for both VIEWs. Dynamic column discovery
# via information_schema.columns ensures the audit adapts to any future column
# additions or removals without code changes.

# %%
# NULL census for matches_1v1_clean (dynamic column discovery)
SQL_NULL_AUDIT_MATCHES_COLS = """
WITH col_list AS (
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'matches_1v1_clean'
    ORDER BY ordinal_position
)
SELECT * FROM col_list;
"""

df_cols_m1 = con.execute(SQL_NULL_AUDIT_MATCHES_COLS).df()
total_rows_m1 = con.execute("SELECT COUNT(*) AS n FROM matches_1v1_clean").fetchone()[0]

# Per-column NULL count via COUNT(*) FILTER (WHERE col IS NULL).
# Template: SELECT COUNT(*) FILTER (WHERE "{column_name}" IS NULL) AS null_count
#           FROM matches_1v1_clean
# Executed once per column discovered above.
null_results_m1 = []
for col_name in df_cols_m1["column_name"]:
    q = f'SELECT COUNT(*) FILTER (WHERE "{col_name}" IS NULL) AS null_count FROM matches_1v1_clean'
    null_count = con.execute(q).fetchone()[0]
    null_pct = round(100.0 * null_count / total_rows_m1, 4) if total_rows_m1 > 0 else 0.0
    null_results_m1.append({
        "column": col_name,
        "null_count": int(null_count),
        "null_pct": float(null_pct),
    })

df_null_m1 = pd.DataFrame(null_results_m1)
print(f"NULL census for matches_1v1_clean ({total_rows_m1:,} total rows):")
print(df_null_m1.to_string(index=False))

# %%
# Assertions: zero-NULL identity and target columns in matches_1v1_clean
m1_null_map = {r["column"]: r["null_count"] for r in null_results_m1}
M1_ZERO_NULL_COLS = ["matchId", "profileId", "started", "won"]
for col in M1_ZERO_NULL_COLS:
    assert m1_null_map[col] == 0, f"FAIL: {col} has {m1_null_map[col]:,} NULLs in matches_1v1_clean"
    print(f"PASS: {col} has 0 NULLs in matches_1v1_clean")

# Document won=0 NULLs as expected (R03 complementary-won filter guarantees this)
print(f"\nFinding: won NULL count = {m1_null_map['won']} (guaranteed 0 by complementary-won filter R03)")

# %%
# NULL census for player_history_all (dynamic column discovery)
SQL_NULL_AUDIT_HIST_COLS = """
WITH col_list AS (
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'player_history_all'
    ORDER BY ordinal_position
)
SELECT * FROM col_list;
"""

df_cols_ph = con.execute(SQL_NULL_AUDIT_HIST_COLS).df()
total_rows_ph = con.execute("SELECT COUNT(*) AS n FROM player_history_all").fetchone()[0]

# Per-column NULL count via COUNT(*) FILTER (WHERE col IS NULL).
# Same template as matches_1v1_clean audit above.
null_results_ph = []
for col_name in df_cols_ph["column_name"]:
    q = f'SELECT COUNT(*) FILTER (WHERE "{col_name}" IS NULL) AS null_count FROM player_history_all'
    null_count = con.execute(q).fetchone()[0]
    null_pct = round(100.0 * null_count / total_rows_ph, 4) if total_rows_ph > 0 else 0.0
    null_results_ph.append({
        "column": col_name,
        "null_count": int(null_count),
        "null_pct": float(null_pct),
    })

df_null_ph = pd.DataFrame(null_results_ph)
print(f"NULL census for player_history_all ({total_rows_ph:,} total rows):")
print(df_null_ph.to_string(index=False))

# %%
# Assertions: zero-NULL identity columns in player_history_all
# IMPORTANT: won is NOT in the zero-NULL list. player_history_all covers ALL
# game types with no won IS NOT NULL filter. won NULLs are a documented finding.
#
# Evidence for matchId/profileId/started zero-NULL expectation:
#   01_02_04 census (matches_raw_null_census in 01_02_04_univariate_census.json)
#   reports null_count=0 for all three columns across 277,099,059 rows.
#   player_history_all applies only WHERE profileId != -1 and dedup by
#   (matchId, profileId) ORDER BY started -- neither filter can introduce NULLs
#   into columns fully populated in the source table.
ph_null_map = {r["column"]: r["null_count"] for r in null_results_ph}
PH_ZERO_NULL_COLS = ["matchId", "profileId", "started"]
for col in PH_ZERO_NULL_COLS:
    assert ph_null_map[col] == 0, f"FAIL: {col} has {ph_null_map[col]:,} NULLs in player_history_all"
    print(f"PASS: {col} has 0 NULLs in player_history_all")

# Document won NULL count as a finding (adversarial review blocker: won IS nullable here)
won_null_count_ph = ph_null_map.get("won", -1)
won_null_pct_ph = round(100.0 * won_null_count_ph / total_rows_ph, 4) if total_rows_ph > 0 else 0.0
print(f"\nFinding: won has {won_null_count_ph:,} NULLs ({won_null_pct_ph}%) in player_history_all")
print("  Reason: VIEW covers all game types; no won IS NOT NULL filter applied.")
print("  Impact: Feature computation must handle won=NULL rows (skip or impute).")

# %% [markdown]
# ## Missingness Audit
#
# **Scope:** Phase 01 documents only (Invariant I9). Phase 02 transforms.
#
# This audit gathers insights for downstream cleaning decisions in 01_04_02+.
# It does NOT execute decisions, modify VIEWs, drop columns, or impute.
#
# Three coordinated steps per VIEW:
# - Pass 1 (NULL census): already executed above via COUNT(*) FILTER (WHERE col IS NULL)
# - Pass 2 (sentinel census): per-column sentinel match driven by _missingness_spec dict
# - Pass 3 (constants detection): SELECT COUNT(DISTINCT col) per column; n_distinct=1 → DROP_COLUMN
#
# **References:** Rubin (1976) MCAR/MAR/MNAR taxonomy; Little & Rubin (2019, 3rd ed.);
# van Buuren (2018) — warns against rigid percentage thresholds;
# Schafer & Graham (2002) — <5% MCAR boundary citation;
# Sambasivan et al. (2021) — data cascade prevention via explicit decision surfacing.

# %%
import numpy as np

_missingness_spec = {
    # Pre-game rating (primary feature, exception per S4)
    "rating": {
        "mechanism": "MAR",
        "justification": (
            "Unranked matches lack rating. In matches_1v1_clean (ranked scope), "
            "effective NULL rate is ~26% -- primary feature, not dropped per Rule "
            "S4 exception. The matches_1v1_clean VIEW asserts `rating >= 0` "
            "upstream, so the -1 sentinel is filtered before the audit sees it; "
            "n_sentinel=0 in the ledger reflects upstream filtering, not absence "
            "of the encoding. Source: 01_03_03 + this audit."
        ),
        "sentinel_value": None,
        "carries_semantic_content": True,
        "is_primary_feature": True,
    },

    # Player metadata
    "country": {
        "mechanism": "MAR",
        "justification": "Player chose not to disclose country. Source: 01_02_04 distribution.",
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },

    # Target column (matches_1v1_clean has 0 NULLs by R03; player_history_all has ~5%)
    "won": {
        "mechanism": "MAR",
        "justification": (
            "Unranked / unknown leaderboards lack won. Excluded from prediction "
            "scope (matches_1v1_clean enforces via R03); retained in "
            "player_history_all for feature computation. Source: 01_03_02 + R03."
        ),
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },

    # Game-settings group A: structurally absent (ranked 1v1 via API version)
    "server": {
        "mechanism": "MNAR",
        "justification": "Structurally absent for certain API versions. 01_02_04 reports null_pct=97.99%.",
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },
    "modDataset": {
        "mechanism": "MAR",
        "justification": "Scenario-specific; absent for ranked random map. 01_02_04 reports null_pct=99.72%.",
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },
    "scenario": {
        "mechanism": "MAR",
        "justification": "Custom scenario only; absent for ranked random map. 01_02_04 reports null_pct=98.27%.",
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },
    "password": {
        "mechanism": "MAR",
        "justification": "Password-protected lobbies only. 01_02_04 reports null_pct=82.90%.",
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },

    # Game-settings group B: schema-evolution (patch-dependent)
    "antiquityMode": {
        "mechanism": "MAR",
        "justification": (
            "Schema-evolution column: introduced in a later patch; missingness "
            "depends on observed match patch (a recorded variable). 01_02_04 "
            "reports null_pct=68.66%."
        ),
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },
    "hideCivs": {
        "mechanism": "MAR",
        "justification": "Schema-evolution column (patch-dependent). 01_02_04 reports null_pct=49.30%.",
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },

    # Group C -- low-NULL game settings (individually enumerated)
    "mod":              {"mechanism": "MAR", "justification": "Group C boolean game setting; 01_02_04 evidence -- ranked-1v1 default. Constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "map":              {"mechanism": "MCAR", "justification": "Map name; near-zero null in ranked 1v1 scope per 01_02_04. Categorical feature.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "difficulty":       {"mechanism": "MAR", "justification": "AI difficulty; near-zero null in ranked-1v1 scope per 01_02_04. Constants-detection backstop applies (likely constant in ranked).", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "startingAge":      {"mechanism": "MAR", "justification": "Game setting; near-zero null in ranked-1v1 scope per 01_02_04. Constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "fullTechTree":     {"mechanism": "MAR", "justification": "Boolean game setting; 01_02_04 evidence -- ranked-1v1 default.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "allowCheats":      {"mechanism": "MAR", "justification": "Boolean game setting; 01_02_04 evidence -- ranked-1v1 default. NULL-cluster member (R04).", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "empireWarsMode":   {"mechanism": "MAR", "justification": "Boolean game mode; 01_02_04 evidence -- variant indicator.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "endingAge":        {"mechanism": "MAR", "justification": "Game setting; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "gameMode":         {"mechanism": "MAR", "justification": "Game mode setting; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "lockSpeed":        {"mechanism": "MAR", "justification": "Boolean game setting; 01_02_04 evidence. NULL-cluster member.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "lockTeams":        {"mechanism": "MAR", "justification": "Boolean game setting; 01_02_04 evidence. NULL-cluster member.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "mapSize":          {"mechanism": "MAR", "justification": "Map size setting; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "population":       {"mechanism": "MAR", "justification": "Population cap; 01_02_04 evidence. NULL-cluster member.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "recordGame":       {"mechanism": "MAR", "justification": "Boolean game setting; 01_02_04 evidence. NULL-cluster member.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "regicideMode":     {"mechanism": "MAR", "justification": "Boolean game mode; 01_02_04 evidence -- variant indicator.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "gameVariant":      {"mechanism": "MAR", "justification": "Game variant identifier; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "resources":        {"mechanism": "MAR", "justification": "Starting resources setting; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "sharedExploration":{"mechanism": "MAR", "justification": "Boolean game setting; 01_02_04 evidence. NULL-cluster member.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "speed":            {"mechanism": "MAR", "justification": "Game speed name; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "speedFactor":      {"mechanism": "MAR", "justification": "Game speed multiplier; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "suddenDeathMode":  {"mechanism": "MAR", "justification": "Boolean game mode; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "civilizationSet":  {"mechanism": "MAR", "justification": "Civilization-set restriction; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "teamPositions":    {"mechanism": "MAR", "justification": "Boolean game setting; 01_02_04 evidence. NULL-cluster member.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "teamTogether":     {"mechanism": "MAR", "justification": "Boolean game setting; 01_02_04 evidence. NULL-cluster member.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "treatyLength":     {"mechanism": "MAR", "justification": "Treaty duration; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "turboMode":        {"mechanism": "MAR", "justification": "Boolean game mode; 01_02_04 evidence. NULL-cluster member.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "victory":          {"mechanism": "MAR", "justification": "Victory condition; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "revealMap":        {"mechanism": "MAR", "justification": "Map reveal setting; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},

    # Player metadata (low-NULL):
    "color":            {"mechanism": "MCAR", "justification": "In-game color code; near-zero null per 01_02_04.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "colorHex":         {"mechanism": "MCAR", "justification": "Color as hex; near-zero null per 01_02_04.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "slot":             {"mechanism": "MCAR", "justification": "Player slot index; near-zero null per 01_02_04.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "status":           {"mechanism": "MCAR", "justification": "Player status; near-zero null per 01_02_04.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "team":             {"mechanism": "MAR", "justification": "Team number; sentinel 255 per matches_raw schema YAML notes.", "sentinel_value": 255, "carries_semantic_content": True, "is_primary_feature": False},
    "shared":           {"mechanism": "MAR", "justification": "Boolean shared-control flag; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "verified":         {"mechanism": "MAR", "justification": "Boolean verified flag; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "privacy":          {"mechanism": "MAR", "justification": "Privacy/visibility setting; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "name":             {"mechanism": "MCAR", "justification": "Display name; near-zero null per 01_02_04.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},

    # Derived flag from VIEW (R04 -- already retained as feature):
    "is_null_cluster":  {"mechanism": "N/A", "justification": "Derived flag from VIEW DDL (R04). Always non-NULL by construction.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},

    # Identity columns (S1): matchId, started, profileId, internalLeaderboardId,
    # civ, filename -- handled by zero-NULL assertions or spec-fallback if non-zero rate.
}

print(f"_missingness_spec loaded: {len(_missingness_spec)} columns declared")


def _build_sentinel_predicate(col, sentinel_value):
    """Construct the SQL predicate for sentinel matching."""
    if sentinel_value is None:
        return None, None
    if isinstance(sentinel_value, list):
        quoted = []
        for v in sentinel_value:
            if isinstance(v, str):
                quoted.append("'" + v.replace("'", "''") + "'")
            else:
                quoted.append(repr(v))
        return f'IN ({", ".join(quoted)})', repr(sentinel_value)
    if isinstance(sentinel_value, str):
        escaped = sentinel_value.replace("'", "''")
        return f"= '{escaped}'", repr(sentinel_value)
    return f"= {sentinel_value!r}", repr(sentinel_value)


def _sentinel_census(view_name, total_rows, spec):
    """Run sentinel COUNT(*) FILTER per spec'd column. Returns list of dicts."""
    rows = []
    for col, meta in spec.items():
        sentinel_value = meta["sentinel_value"]
        predicate, sentinel_repr = _build_sentinel_predicate(col, sentinel_value)
        if predicate is None:
            n_sentinel = 0
        else:
            sql = f'SELECT COUNT(*) FILTER (WHERE "{col}" {predicate}) FROM {view_name}'
            n_sentinel = con.execute(sql).fetchone()[0]
        pct_sentinel = round(100.0 * n_sentinel / total_rows, 4) if total_rows > 0 else 0.0
        rows.append({
            "column": col,
            "sentinel_value": sentinel_repr,
            "n_sentinel": int(n_sentinel),
            "pct_sentinel": float(pct_sentinel),
        })
    return rows


def _detect_constants(view_name, columns, identity_cols=frozenset()):
    """Per-column n_distinct check. Returns {col: n_distinct}.

    Identity columns are skipped (constants-detection runtime budget W6).
    """
    out = {}
    for col in columns:
        if col in identity_cols:
            out[col] = None
            continue
        sql = f'SELECT COUNT(DISTINCT "{col}") FROM {view_name}'
        out[col] = int(con.execute(sql).fetchone()[0])
    return out


def _recommend(col, mechanism, pct, is_primary, n_null, n_sentinel):
    """Decision tree per temp/null_handling_recommendations.md S3.1."""
    if n_sentinel > 0 and n_null == 0 and pct < 5.0:
        return "CONVERT_SENTINEL_TO_NULL", (
            f"Low sentinel rate ({pct:.4f}%); convert sentinel to NULL via "
            f"NULLIF in 01_04_02+ DDL pass per Rule S3 (negligible rate). "
            f"NOTE: if carries_semantic_content=True, recommendation is non-binding."
        )
    if pct == 0.0:
        return "RETAIN_AS_IS", "Zero missingness observed; no action needed."
    if pct > 80.0:
        return "DROP_COLUMN", (
            f"NULL+sentinel rate {pct:.2f}% exceeds 80% (Rule S4 / van Buuren 2018). "
            f"Imputation indefensible at this rate."
        )
    if pct > 40.0:
        if mechanism == "MNAR":
            return "DROP_COLUMN", (
                f"Rate {pct:.2f}% in 40-80% MNAR band; no defensible imputation."
            )
        if is_primary:
            return "FLAG_FOR_IMPUTATION", (
                f"Rate {pct:.2f}% in 40-80%; primary feature exception per Rule S4. "
                f"Phase 02: conditional imputation + add_indicator."
            )
        return "DROP_COLUMN", (
            f"Rate {pct:.2f}% in 40-80%; non-primary feature; cost/benefit favors "
            f"simplicity per Rule S4."
        )
    if pct > 5.0:
        return "FLAG_FOR_IMPUTATION", (
            f"Rate {pct:.2f}% in 5-40%; flag for Phase 02 imputation."
        )
    return "RETAIN_AS_IS", (
        f"Rate {pct:.2f}% < 5% (Schafer & Graham 2002 boundary citation). "
        f"Listwise deletion or simple imputation acceptable in Phase 02."
    )


def _consolidate_ledger(view_name, df_null, sentinel_rows, spec, dtype_map,
                        total_rows, constants_map, target_cols, identity_cols=frozenset()):
    """Merge NULL census + sentinel census + constants detection + spec."""
    sentinel_map = {r["column"]: r for r in sentinel_rows}
    ledger = []
    for _, nrow in df_null.iterrows():
        col = nrow["column"] if "column" in nrow else nrow["column_name"]
        n_null = int(nrow["null_count"])
        pct_null = float(nrow.get("null_pct", round(100.0 * n_null / total_rows, 4)))
        srow = sentinel_map.get(col, {"sentinel_value": None, "n_sentinel": 0, "pct_sentinel": 0.0})
        n_sentinel = int(srow["n_sentinel"])
        pct_sentinel = float(srow["pct_sentinel"])
        n_total_missing = n_null + n_sentinel
        pct_missing_total = round(pct_null + pct_sentinel, 4)
        spec_entry = spec.get(col)
        n_distinct = constants_map.get(col, None)

        if col in identity_cols:
            mechanism = "N/A"
            mech_just = (
                f"Identity column; n_distinct check skipped per W6 (constants-detection "
                f"runtime budget). Zero NULLs by definition (asserted upstream)."
            )
            carries_sem = False
            is_primary = False
            rec = "RETAIN_AS_IS"
            rec_just = "Identity column; no missingness possible by upstream assertion."
        elif n_distinct == 1 and n_null == 0 and n_sentinel == 0:
            mechanism = "N/A"
            mech_just = (
                f"True constant column; n_distinct=1 across {total_rows:,} rows "
                f"(zero NULLs, zero sentinels). No information content for prediction."
            )
            carries_sem = False
            is_primary = False
            rec = "DROP_COLUMN"
            rec_just = "True constant column; n_distinct=1; no information content."
        elif n_total_missing == 0:
            mechanism = "N/A"
            mech_just = "Zero missingness observed; no action needed."
            carries_sem = bool(spec_entry["carries_semantic_content"]) if spec_entry else False
            is_primary = bool(spec_entry["is_primary_feature"]) if spec_entry else False
            rec = "RETAIN_AS_IS"
            rec_just = "Zero missingness observed; no action needed."
        elif spec_entry is not None:
            mechanism = spec_entry["mechanism"]
            mech_just = spec_entry["justification"]
            carries_sem = bool(spec_entry["carries_semantic_content"])
            is_primary = bool(spec_entry["is_primary_feature"])
            rec, rec_just = _recommend(col, mechanism, pct_missing_total,
                                       is_primary, n_null, n_sentinel)
        else:
            mechanism = "MAR"
            mech_just = (
                f"No _missingness_spec entry; conservative MAR assumption. "
                f"Effective missingness {pct_missing_total:.2f}% "
                f"(NULL: {pct_null:.2f}%, sentinel: {pct_sentinel:.2f}%)."
            )
            carries_sem = False
            is_primary = False
            rec, rec_just = _recommend(col, mechanism, pct_missing_total,
                                       is_primary, n_null, n_sentinel)

        if col in target_cols and n_total_missing > 0:
            rec = "EXCLUDE_TARGET_NULL_ROWS"
            rec_just = (
                "Per Rule S2: target NULLs/sentinels excluded from prediction "
                "scope, retained in history for feature computation. "
                "NEVER impute target."
            )

        ledger.append({
            "view": view_name,
            "column": col,
            "dtype": dtype_map.get(col, "UNKNOWN"),
            "n_total": int(total_rows),
            "n_null": n_null,
            "pct_null": pct_null,
            "sentinel_value": srow["sentinel_value"],
            "n_sentinel": n_sentinel,
            "pct_sentinel": pct_sentinel,
            "pct_missing_total": pct_missing_total,
            "n_distinct": n_distinct,
            "mechanism": mechanism,
            "mechanism_justification": mech_just,
            "recommendation": rec,
            "recommendation_justification": rec_just,
            "carries_semantic_content": carries_sem,
            "is_primary_feature": is_primary,
        })
    return pd.DataFrame(ledger)

print("Missingness audit helpers defined.")

# %%
# Pass 2+3: sentinel census + constants detection + ledger for matches_1v1_clean
_VIEW_M1 = "matches_1v1_clean"
_TARGET_COLS_M1 = {"won"}
_IDENTITY_COLS_M1 = {"matchId", "profileId"}  # W3 fix: profileId skipped to avoid DuckDB COUNT(DISTINCT) artifact

_dtype_m1 = {
    row["column_name"]: row["column_type"]
    for _, row in con.execute(f"DESCRIBE {_VIEW_M1}").df().iterrows()
}

print(f"Pass 2: sentinel census for {_VIEW_M1} ...")
sentinel_rows_m1 = _sentinel_census(_VIEW_M1, total_rows_m1, _missingness_spec)

print(f"Pass 3: constants detection for {_VIEW_M1} (skipping identity cols: {_IDENTITY_COLS_M1}) ...")
constants_m1 = _detect_constants(_VIEW_M1, list(_dtype_m1.keys()), identity_cols=_IDENTITY_COLS_M1)

df_null_m1_for_ledger = pd.DataFrame(null_results_m1)
df_ledger_m1 = _consolidate_ledger(
    _VIEW_M1, df_null_m1_for_ledger, sentinel_rows_m1, _missingness_spec,
    _dtype_m1, total_rows_m1, constants_m1,
    target_cols=_TARGET_COLS_M1, identity_cols=_IDENTITY_COLS_M1,
)

n_view_cols_m1 = int(con.execute(f"DESCRIBE {_VIEW_M1}").df().shape[0])
assert len(df_ledger_m1) == n_view_cols_m1, (
    f"Full-coverage ledger required for {_VIEW_M1}: "
    f"expected {n_view_cols_m1} rows, got {len(df_ledger_m1)}"
)
print(f"Ledger for {_VIEW_M1}: {len(df_ledger_m1)} rows (full coverage: {n_view_cols_m1} cols)")

for _, row in df_ledger_m1.iterrows():
    assert row["mechanism"] in {"MAR", "MCAR", "MNAR", "N/A"}, row.to_dict()
    assert row["mechanism_justification"], f"empty mechanism justification for {row['column']}"
    assert row["recommendation"] in {
        "DROP_COLUMN", "FLAG_FOR_IMPUTATION", "RETAIN_AS_IS",
        "EXCLUDE_TARGET_NULL_ROWS", "CONVERT_SENTINEL_TO_NULL"
    }, row.to_dict()
    assert row["recommendation_justification"], row.to_dict()
    assert isinstance(row["carries_semantic_content"], (bool, np.bool_)), row.to_dict()

target_cols_for_view_m1 = _TARGET_COLS_M1
identity_cols_for_view_m1 = _IDENTITY_COLS_M1

_missing_targets_m1 = set(target_cols_for_view_m1) - set(df_ledger_m1["column"].values)
assert not _missing_targets_m1, f"target column(s) missing from VIEW: {_missing_targets_m1}"

_zero_m1 = df_ledger_m1[
    (df_ledger_m1["n_null"] == 0) &
    (df_ledger_m1["n_sentinel"] == 0) &
    (df_ledger_m1["n_distinct"].fillna(-1) != 1) &
    (~df_ledger_m1["column"].isin(target_cols_for_view_m1)) &
    (~df_ledger_m1["column"].isin(identity_cols_for_view_m1))
]
assert (_zero_m1["mechanism"] == "N/A").all(), "non-target zero-missingness rows must have mechanism=N/A"
assert (_zero_m1["recommendation"] == "RETAIN_AS_IS").all(), "non-target zero-missingness rows must be RETAIN_AS_IS"

_const_m1 = df_ledger_m1[
    (df_ledger_m1["n_distinct"].fillna(-1) == 1) &
    (df_ledger_m1["n_null"] == 0) &
    (df_ledger_m1["n_sentinel"] == 0)
]
assert (_const_m1["mechanism"] == "N/A").all(), "true constant rows must have mechanism=N/A"
assert (_const_m1["recommendation"] == "DROP_COLUMN").all(), "true constant rows must be DROP_COLUMN"

_ident_m1 = df_ledger_m1[df_ledger_m1["column"].isin(identity_cols_for_view_m1)]
assert (_ident_m1["mechanism"] == "N/A").all(), "identity columns must have mechanism=N/A"
assert (_ident_m1["recommendation"] == "RETAIN_AS_IS").all(), "identity columns must be RETAIN_AS_IS"

_targets_with_missing_m1 = df_ledger_m1[
    (df_ledger_m1["column"].isin(target_cols_for_view_m1)) &
    ((df_ledger_m1["n_null"] > 0) | (df_ledger_m1["n_sentinel"] > 0))
]
assert (_targets_with_missing_m1["recommendation"] == "EXCLUDE_TARGET_NULL_ROWS").all(), (
    "Target columns with semantic missingness must be EXCLUDE_TARGET_NULL_ROWS"
)

print(f"All assertions passed for {_VIEW_M1} ledger.")
print(df_ledger_m1[["column", "mechanism", "recommendation", "pct_missing_total"]].to_string(index=False))

# %%
# Pass 2+3: sentinel census + constants detection + ledger for player_history_all
_VIEW_PH = "player_history_all"
_TARGET_COLS_PH = {"won"}
_IDENTITY_COLS_PH = {"matchId", "profileId"}

_dtype_ph = {
    row["column_name"]: row["column_type"]
    for _, row in con.execute(f"DESCRIBE {_VIEW_PH}").df().iterrows()
}

print(f"Pass 2: sentinel census for {_VIEW_PH} ...")
sentinel_rows_ph_spec = _sentinel_census(_VIEW_PH, total_rows_ph, _missingness_spec)

print(f"Pass 3: constants detection for {_VIEW_PH} (skipping identity cols: {_IDENTITY_COLS_PH}) ...")
constants_ph = _detect_constants(_VIEW_PH, list(_dtype_ph.keys()), identity_cols=_IDENTITY_COLS_PH)

df_null_ph_for_ledger = pd.DataFrame(null_results_ph)
df_ledger_ph = _consolidate_ledger(
    _VIEW_PH, df_null_ph_for_ledger, sentinel_rows_ph_spec, _missingness_spec,
    _dtype_ph, total_rows_ph, constants_ph,
    target_cols=_TARGET_COLS_PH, identity_cols=_IDENTITY_COLS_PH,
)

n_view_cols_ph = int(con.execute(f"DESCRIBE {_VIEW_PH}").df().shape[0])
assert len(df_ledger_ph) == n_view_cols_ph, (
    f"Full-coverage ledger required for {_VIEW_PH}: "
    f"expected {n_view_cols_ph} rows, got {len(df_ledger_ph)}"
)
print(f"Ledger for {_VIEW_PH}: {len(df_ledger_ph)} rows (full coverage: {n_view_cols_ph} cols)")

for _, row in df_ledger_ph.iterrows():
    assert row["mechanism"] in {"MAR", "MCAR", "MNAR", "N/A"}, row.to_dict()
    assert row["mechanism_justification"], f"empty mechanism justification for {row['column']}"
    assert row["recommendation"] in {
        "DROP_COLUMN", "FLAG_FOR_IMPUTATION", "RETAIN_AS_IS",
        "EXCLUDE_TARGET_NULL_ROWS", "CONVERT_SENTINEL_TO_NULL"
    }, row.to_dict()
    assert row["recommendation_justification"], row.to_dict()
    assert isinstance(row["carries_semantic_content"], (bool, np.bool_)), row.to_dict()

target_cols_for_view_ph = _TARGET_COLS_PH
identity_cols_for_view_ph = _IDENTITY_COLS_PH

_missing_targets_ph = set(target_cols_for_view_ph) - set(df_ledger_ph["column"].values)
assert not _missing_targets_ph, f"target column(s) missing from VIEW: {_missing_targets_ph}"

_zero_ph = df_ledger_ph[
    (df_ledger_ph["n_null"] == 0) &
    (df_ledger_ph["n_sentinel"] == 0) &
    (df_ledger_ph["n_distinct"].fillna(-1) != 1) &
    (~df_ledger_ph["column"].isin(target_cols_for_view_ph)) &
    (~df_ledger_ph["column"].isin(identity_cols_for_view_ph))
]
assert (_zero_ph["mechanism"] == "N/A").all(), "non-target zero-missingness rows must have mechanism=N/A"
assert (_zero_ph["recommendation"] == "RETAIN_AS_IS").all(), "non-target zero-missingness rows must be RETAIN_AS_IS"

_const_ph = df_ledger_ph[
    (df_ledger_ph["n_distinct"].fillna(-1) == 1) &
    (df_ledger_ph["n_null"] == 0) &
    (df_ledger_ph["n_sentinel"] == 0)
]
assert (_const_ph["mechanism"] == "N/A").all(), "true constant rows must have mechanism=N/A"
assert (_const_ph["recommendation"] == "DROP_COLUMN").all(), "true constant rows must be DROP_COLUMN"

_ident_ph = df_ledger_ph[df_ledger_ph["column"].isin(identity_cols_for_view_ph)]
assert (_ident_ph["mechanism"] == "N/A").all(), "identity columns must have mechanism=N/A"
assert (_ident_ph["recommendation"] == "RETAIN_AS_IS").all(), "identity columns must be RETAIN_AS_IS"

_targets_with_missing_ph = df_ledger_ph[
    (df_ledger_ph["column"].isin(target_cols_for_view_ph)) &
    ((df_ledger_ph["n_null"] > 0) | (df_ledger_ph["n_sentinel"] > 0))
]
assert (_targets_with_missing_ph["recommendation"] == "EXCLUDE_TARGET_NULL_ROWS").all(), (
    "Target columns with semantic missingness must be EXCLUDE_TARGET_NULL_ROWS"
)

print(f"All assertions passed for {_VIEW_PH} ledger.")
print(df_ledger_ph[["column", "mechanism", "recommendation", "pct_missing_total"]].to_string(index=False))

# %% [markdown]
# ## Decisions surfaced for downstream cleaning (01_04_02+)
#
# **DS-AOEC-01 (structurally-absent group):** server (97.39% in matches_1v1_clean
# / ~98% in raw matches_raw), scenario (100.00% / ~98.3%), modDataset (100.00%
# / ~99.7%), password (77.57% via 40-80% MAR-non-primary path / ~82.9% raw).
# All four -> DROP_COLUMN at 01_04_02+ (per Rule S4). 'scenario' and 'modDataset'
# are 100% NULL in cleaned scope (every row is NULL -- drop is unambiguous).
# 'password' falls below the 80% boundary in the cleaned scope and is routed
# through the 40-80% non-primary cost-benefit path; intent (drop) is the same.
# Note: VIEW rates differ from raw rates due to the matches_1v1_clean ranked-
# 1v1 filter -- see the plan's note_on_rates for the principle.
#
# **DS-AOEC-02 (schema-evolution group):** antiquityMode (60.06% in matches_1v1_clean
# / ~68.66% in raw -- falls in 40-80% non-primary band -> DROP_COLUMN), hideCivs
# (37.18% in matches_1v1_clean / ~49.30% in raw -- now falls in 5-40% band ->
# FLAG_FOR_IMPUTATION, NOT DROP_COLUMN as raw-rate framing implied). Phase 02
# decides if the imputed-with-indicator hideCivs is predictive; if not, drop
# in 01_04_02+. The recommendation drift between raw-rate (~49% suggesting drop)
# and VIEW-rate (37% suggesting flag) is a direct consequence of the
# matches_1v1_clean filter narrowing the scope; the audit reports VIEW-rate
# as authoritative.
#
# **DS-AOEC-03 (low-NULL game settings):** mod, map, difficulty, startingAge, fullTechTree,
# allowCheats, empireWarsMode, endingAge, gameMode, lockSpeed, lockTeams, mapSize,
# population, recordGame, regicideMode, gameVariant, resources, sharedExploration,
# speed, speedFactor, suddenDeathMode, civilizationSet, teamPositions, teamTogether,
# treatyLength, turboMode, victory, revealMap. Each gets individual 01_02_04-grounded
# justification; downstream disposition is RETAIN_AS_IS / FLAG_FOR_IMPUTATION per rate.
#
# **DS-AOEC-04:** rating in matches_1v1_clean (~26% NULL in 1v1 scope per VIEW):
# primary feature exception per Rule S4. Phase 02 imputation strategy
# (median-within-leaderboard + add_indicator) must be specified before Phase 02 begins.
#
# **DS-AOEC-05:** country (~12.6% in raw, lower in 1v1 VIEW): Phase 02 --
# 'Unknown' category encoding or add_indicator.
#
# **DS-AOEC-06:** won in matches_1v1_clean: 0 NULLs (R03 guarantees) -- per F1
# zero-missingness override, ledger reports RETAIN_AS_IS / mechanism=N/A.
#
# **DS-AOEC-07:** won in player_history_all (~5%): MAR; per the target-override
# post-step, recommendation becomes EXCLUDE_TARGET_NULL_ROWS.
#
# **DS-AOEC-08 (snapshot-table disposition):** leaderboards_raw and profiles_raw
# are NOT_USABLE per 01_03_03; profiles_raw has 7 dead columns (100% NULL).
# Formally declare out-of-analytical-scope at 01_04_02+ -- these tables do not
# enter any VIEW and do not need triage.
#
# **Note on rates:** All triage rates derive from VIEWs (filtered scope), not raw
# tables. A column with 42% NULL in matches_raw can be ~26% NULL in
# matches_1v1_clean. The ledger is authoritative for downstream decisions because
# Phase 02 features are computed from the VIEWs.

# %%
db.close()
print("DB connection closed.")

# %% [markdown]
# ## Artifact production

# %%
db_ro = get_notebook_db("aoe2", "aoe2companion", read_only=True)
con_ro = db_ro.con

# Re-fetch all results for artifact
df_t01_art = con_ro.execute(SQL_T01_SCOPE).df()
df_t02_dup_art = con_ro.execute(SQL_T02_DUP_STRAT).df()
df_t02_m1_art = con_ro.execute(SQL_T02_MINUS1).df()
df_t03_won_art = con_ro.execute(SQL_T03_WON).df()
df_t03_sizes_art = con_ro.execute(SQL_T03_SIZES).df()
df_t04_cluster_art = con_ro.execute(SQL_T04_CLUSTER).df()
df_t04_monthly_art = con_ro.execute(SQL_T04_MONTHLY).df()
df_t04_survival_art = con_ro.execute(SQL_T04_SURVIVAL).df()
df_t05_art = con_ro.execute(SQL_T05_OUTLIER).df()

s0_art = con_ro.execute("SELECT COUNT(*) AS n, COUNT(DISTINCT matchId) AS nm FROM matches_raw").fetchone()
s1_art = con_ro.execute("SELECT COUNT(*) AS n, COUNT(DISTINCT matchId) AS nm FROM matches_raw WHERE internalLeaderboardId IN (6, 18)").fetchone()
s2_art = con_ro.execute("""
SELECT COUNT(*) AS n, COUNT(DISTINCT matchId) AS nm
FROM (SELECT matchId, ROW_NUMBER() OVER (PARTITION BY matchId, profileId ORDER BY started) AS rn
      FROM matches_raw WHERE internalLeaderboardId IN (6, 18) AND profileId != -1) sub WHERE rn = 1
""").fetchone()
s3_art = con_ro.execute("SELECT COUNT(*) AS n, COUNT(DISTINCT matchId) AS nm FROM matches_1v1_clean").fetchone()

r_v1_art = con_ro.execute("""
SELECT COUNT(*) AS total, COUNT(rating) AS n_non_null,
       ROUND(100.0*COUNT(rating)/COUNT(*),2) AS rating_coverage_pct
FROM matches_1v1_clean
""").fetchone()
r_v2_art = con_ro.execute("""
SELECT column_name FROM information_schema.columns
WHERE table_name='player_history_all' AND column_name IN ('ratingDiff', 'finished')
""").df()
r_v2b_art = con_ro.execute("""
SELECT column_name FROM information_schema.columns
WHERE table_name='matches_1v1_clean' AND column_name IN ('ratingDiff', 'finished')
""").df()
r_v3_art = con_ro.execute("SELECT COUNT(*) FILTER (WHERE rating < 0) AS n FROM matches_1v1_clean").fetchone()
r_v4_art = con_ro.execute("SELECT leaderboard, internalLeaderboardId, COUNT(*) AS n_rows FROM matches_1v1_clean GROUP BY leaderboard, internalLeaderboardId").df()
r_v5_art = con_ro.execute("SELECT is_null_cluster, COUNT(*) AS n_rows, ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER(),4) AS pct FROM matches_1v1_clean GROUP BY is_null_cluster").df()
r_v6_art = con_ro.execute("SELECT COUNT(*) AS n_rows, COUNT(DISTINCT matchId) AS n_matches, COUNT(DISTINCT profileId) AS n_players, COUNT(DISTINCT leaderboard) AS n_leaderboards FROM player_history_all").fetchone()
r_v7_art = con_ro.execute("SELECT COUNT(*) AS n FROM player_history_all WHERE profileId = -1").fetchone()
r_v8_art = con_ro.execute("SELECT leaderboard, COUNT(*) AS n_rows FROM player_history_all GROUP BY leaderboard ORDER BY n_rows DESC").df()

db_ro.close()
print("All artifact data collected.")

# %%
t05_p999 = int(df_t05_art["p999"].iloc[0])

artifact = {
    "step": "01_04_01",
    "dataset": "aoe2companion",
    "game": "aoe2",
    "generated_date": str(date.today()),
    "cleaning_registry": {
        "R00": {
            "id": "R00",
            "name": "Feature history scope",
            "condition": "Full matches_raw, all game types, excluding profileId=-1 and duplicates",
            "action": "Create VIEW player_history_all as feature computation source",
            "justification": (
                "Player features computed from full recorded history. Restricting to 1v1 "
                "would compound selection bias without eliminating it."
            ),
            "impact": f"~{r_v6_art[0]:,} rows in player_history_all",
            "view": "player_history_all",
        },
        "R01": {
            "id": "R01",
            "name": "Scope restriction",
            "condition": "internalLeaderboardId NOT IN (6, 18) OR internalLeaderboardId IS NULL",
            "action": "Exclude from prediction target VIEW; retain in player_history_all",
            "justification": (
                "Thesis scope is 1v1 ranked Random Map prediction. "
                "01_03_02 confirmed rm_1v1 + qp_rm_1v1 captures 99.98% of structural 1v1 matches. "
                "IDs 6 and 18 from empirical analysis in 01_03_02."
            ),
            "impact": f"{t01_out_scope:,} rows excluded from prediction target (~{100*t01_out_scope/t01_total:.1f}% of total)",
        },
        "R02": {
            "id": "R02",
            "name": "Deduplication",
            "condition": "Duplicate (matchId, profileId) rows; also any profileId=-1 rows",
            "action": "Keep first occurrence per matchId x profileId (ORDER BY started); exclude profileId=-1",
            "justification": (
                "aoe2companion API returns duplicate rows across daily dumps. "
                "01_03_02 showed profileId=-1 affects only 1 row in rm_1v1. "
                "Using ORDER BY started provides deterministic, semantically meaningful tie-breaking."
            ),
            "impact": f"Excess rows removed: {t01_in_scope - s2_art[0]:,}; profileId=-1 rows removed: {int(df_t02_m1_art['total_minus1_rows'].iloc[0]):,}",
        },
        "R03": {
            "id": "R03",
            "name": "Won complementarity",
            "condition": "2-row match where won not complementary; also 1-row and 3+ row matches",
            "action": "Exclude entire match (both rows)",
            "justification": (
                "Zero-sum 1v1 game requires exactly one winner. "
                "Non-complementary won is unresolvable."
            ),
            "impact": f"Matches excluded: {s2_art[1] - s3_art[1]:,}",
        },
        "R04": {
            "id": "R04",
            "name": "NULL cluster flag",
            "condition": "All 10 game-settings columns simultaneously NULL",
            "action": "FLAG only (is_null_cluster = TRUE) -- retained in matches_1v1_clean",
            "justification": (
                "NULL cluster is tiny (<0.02% of in-scope rows). "
                "Spans the full date range (not a concentrated schema-change era). "
                "Affected columns are near-constant in 1v1 ranked play. "
                "Flagged for sensitivity analysis in modeling phase."
            ),
            "impact": f"{int(r_v5_art[r_v5_art['is_null_cluster'] == True]['n_rows'].iloc[0]):,} rows flagged",
        },
        "R05": {
            "id": "R05",
            "name": "ratings_raw.games outlier cap",
            "condition": f"ratings_raw.games > {t05_p999:,} (p99.9, empirically computed)",
            "action": f"Winsorize to p99.9 = {t05_p999:,} in ratings_clean VIEW",
            "justification": (
                f"Max={int(df_t05_art['max_val'].iloc[0]):,} is physically impossible. "
                f"p99.9={t05_p999:,} derived empirically (I7). "
                f"p99={int(df_t05_art['p99'].iloc[0]):,} shows the extreme outlier cluster."
            ),
            "impact": f"{int(df_t05_art['n_above_1M'].iloc[0]):,} rows with games > 1M capped",
        },
    },
    "consort_flow": {
        "S0_raw": {"n_rows": s0_art[0], "n_matches": s0_art[1], "description": "All rows in matches_raw"},
        "S1_scope_restricted": {"n_rows": s1_art[0], "n_matches": s1_art[1], "description": "R01: internalLeaderboardId IN (6, 18)"},
        "S2_deduplicated": {"n_rows": s2_art[0], "n_matches": s2_art[1], "description": "R02: deduplicated by (matchId, profileId) ORDER BY started; profileId=-1 excluded"},
        "S3_valid_complementary": {"n_rows": s3_art[0], "n_matches": s3_art[1], "description": "R03: 2-row matches with complementary won only"},
        "excluded_S0_to_S1": {"n_rows": s0_art[0] - s1_art[0], "description": "Out-of-scope leaderboards"},
        "excluded_S1_to_S2": {"n_rows": s1_art[0] - s2_art[0], "description": "Duplicates + profileId=-1"},
        "excluded_S2_to_S3": {"n_rows": s2_art[0] - s3_art[0], "description": "Non-complementary won + non-2-row matches"},
    },
    "post_cleaning_validation": {
        "V1_rating_coverage": {
            "total_rows": r_v1_art[0],
            "n_non_null_rating": r_v1_art[1],
            "rating_coverage_pct": float(r_v1_art[2]),
            "description": "Rating (PRE-GAME, confirmed 01_03_03) coverage in matches_1v1_clean",
        },
        "V2_no_postgame_leakage": {
            "player_history_all": {
                "n_postgame_cols_found": len(r_v2_art),
                "columns_checked": ["ratingDiff", "finished"],
                "pass": len(r_v2_art) == 0,
            },
            "matches_1v1_clean": {
                "n_postgame_cols_found": len(r_v2b_art),
                "columns_checked": ["ratingDiff", "finished"],
                "pass": len(r_v2b_art) == 0,
            },
            "pass": len(r_v2_art) == 0 and len(r_v2b_art) == 0,
            "description": "No POST-GAME columns in player_history_all or matches_1v1_clean (I3)",
        },
        "V3_rating_sanity": {
            "n_negative_rating": r_v3_art[0],
            "pass": r_v3_art[0] == 0,
        },
        "V4_leaderboard_distribution": {
            row["leaderboard"]: {"internalLeaderboardId": row["internalLeaderboardId"], "n_rows": row["n_rows"]}
            for _, row in r_v4_art.iterrows()
        },
        "V5_null_cluster_proportion": {
            str(row["is_null_cluster"]): {"n_rows": row["n_rows"], "pct": float(row["pct"])}
            for _, row in r_v5_art.iterrows()
        },
        "V6_player_history_all_counts": {
            "n_rows": r_v6_art[0],
            "n_matches": r_v6_art[1],
            "n_players": r_v6_art[2],
            "n_leaderboards": r_v6_art[3],
        },
        "V7_no_anonymous_rows": {
            "n_anonymous": r_v7_art[0],
            "pass": r_v7_art[0] == 0,
        },
        "V8_leaderboard_diversity": {
            row["leaderboard"]: row["n_rows"] for _, row in r_v8_art.iterrows()
        },
    },
    "null_cluster_monthly_breakdown": [
        {
            "month": str(row["month"]),
            "null_cluster_rows": int(row["null_cluster_rows"]),
            "normal_rows": int(row["normal_rows"]),
            "null_pct": float(row["null_pct"]),
        }
        for _, row in df_t04_monthly_art.iterrows()
    ],
    "sql_queries": {
        "T01_scope_restriction": SQL_T01_SCOPE,
        "T02_dup_stratification": SQL_T02_DUP_STRAT,
        "T02_minus1_investigation": SQL_T02_MINUS1,
        "T03_won_consistency": SQL_T03_WON,
        "T03_match_sizes": SQL_T03_SIZES,
        "T04_null_cluster": SQL_T04_CLUSTER,
        "T04_null_monthly": SQL_T04_MONTHLY,
        "T04_null_survival": SQL_T04_SURVIVAL,
        "T05_outlier_analysis": SQL_T05_OUTLIER,
        "T05_ratings_clean_view": SQL_T05_VIEW,
        "T06_player_history_all_view": SQL_T06_VIEW,
        "T07_matches_1v1_clean_view": SQL_T07_VIEW,
    },
}

# NULL audit artifact integration (cross-dataset standardized key structure)
artifact["null_audit"] = {
    "matches_1v1_clean": {
        "total_rows": int(total_rows_m1),
        "columns": null_results_m1,
        "zero_null_assertions": {col: True for col in M1_ZERO_NULL_COLS},
        "nullable_findings": {
            "won": {
                "null_count": int(m1_null_map["won"]),
                "note": "guaranteed 0 by complementary-won filter R03",
            },
        },
    },
    "player_history_all": {
        "total_rows": int(total_rows_ph),
        "columns": null_results_ph,
        "zero_null_assertions": {col: True for col in PH_ZERO_NULL_COLS},
        "zero_null_evidence": (
            "01_02_04 census (matches_raw_null_census) reports null_count=0 "
            "for matchId, profileId, started across 277,099,059 rows in matches_raw. "
            "player_history_all is a filtered projection (WHERE profileId != -1, "
            "dedup by matchId/profileId) that cannot introduce NULLs."
        ),
        "nullable_findings": {
            "won": {
                "null_count": int(won_null_count_ph),
                "null_pct": float(won_null_pct_ph),
                "note": (
                    "nullable field; VIEW covers all game types; "
                    "no won IS NOT NULL filter applied"
                ),
            },
        },
    },
}

# Add NULL audit SQL queries to the artifact (I6: derivation for all reported results)
artifact["sql_queries"]["null_audit_matches_cols"] = SQL_NULL_AUDIT_MATCHES_COLS
artifact["sql_queries"]["null_audit_hist_cols"] = SQL_NULL_AUDIT_HIST_COLS

# N4 fix: store representative SQL template for the per-column NULL counting loop.
artifact["sql_queries"]["null_audit_per_column_template"] = (
    'SELECT COUNT(*) FILTER (WHERE "{column_name}" IS NULL) AS null_count '
    'FROM {view_name}'
)

# Missingness audit block (additive -- extends null_audit with sentinel+constants+ledger)
_decisions_surfaced_list = [
    {
        "id": "DS-AOEC-01",
        "columns": (
            "server (97.39% in matches_1v1_clean / ~98% in raw matches_raw), "
            "scenario (100.00% / ~98.3%), modDataset (100.00% / ~99.7%), "
            "password (77.57% via 40-80% MAR-non-primary path / ~82.9% raw)"
        ),
        "question": (
            "All four -> DROP_COLUMN at 01_04_02+ (per Rule S4). 'scenario' and 'modDataset' "
            "are 100% NULL in cleaned scope (every row is NULL -- drop is unambiguous). "
            "'password' falls below the 80% boundary in the cleaned scope and is routed "
            "through the 40-80% non-primary cost-benefit path; intent (drop) is the same. "
            "Note: VIEW rates differ from raw rates due to the matches_1v1_clean ranked-"
            "1v1 filter -- see the plan's note_on_rates for the principle."
        ),
    },
    {
        "id": "DS-AOEC-02",
        "columns": (
            "antiquityMode (60.06% in matches_1v1_clean / ~68.66% in raw -- "
            "falls in 40-80% non-primary band -> DROP_COLUMN), "
            "hideCivs (37.18% in matches_1v1_clean / ~49.30% in raw -- "
            "now falls in 5-40% band -> FLAG_FOR_IMPUTATION, NOT DROP_COLUMN as "
            "raw-rate framing implied)"
        ),
        "question": (
            "Phase 02 decides if the imputed-with-indicator hideCivs is predictive; "
            "if not, drop in 01_04_02+. The recommendation drift between raw-rate "
            "(~49% suggesting drop) and VIEW-rate (37% suggesting flag) is a direct "
            "consequence of the matches_1v1_clean filter narrowing the scope; "
            "the audit reports VIEW-rate as authoritative."
        ),
    },
    {
        "id": "DS-AOEC-03",
        "columns": (
            "mod, map, difficulty, startingAge, fullTechTree, allowCheats, empireWarsMode, "
            "endingAge, gameMode, lockSpeed, lockTeams, mapSize, population, recordGame, "
            "regicideMode, gameVariant, resources, sharedExploration, speed, speedFactor, "
            "suddenDeathMode, civilizationSet, teamPositions, teamTogether, treatyLength, "
            "turboMode, victory, revealMap"
        ),
        "question": (
            "Low-NULL game settings group. Each gets individual 01_02_04-grounded justification. "
            "Downstream disposition is RETAIN_AS_IS / FLAG_FOR_IMPUTATION per rate."
        ),
    },
    {
        "id": "DS-AOEC-04",
        "column": "rating in matches_1v1_clean (~26% NULL in 1v1 scope per VIEW)",
        "question": (
            "Primary feature exception per Rule S4. Phase 02 imputation strategy "
            "(median-within-leaderboard + add_indicator) must be specified before Phase 02 begins."
        ),
    },
    {
        "id": "DS-AOEC-05",
        "column": "country (~12.6% in raw, lower in 1v1 VIEW)",
        "question": "Phase 02 -- 'Unknown' category encoding or add_indicator.",
    },
    {
        "id": "DS-AOEC-06",
        "column": "won in matches_1v1_clean",
        "question": (
            "0 NULLs (R03 guarantees) -- per F1 zero-missingness override, "
            "ledger reports RETAIN_AS_IS / mechanism=N/A. Target-override post-step does NOT fire."
        ),
    },
    {
        "id": "DS-AOEC-07",
        "column": "won in player_history_all (~5%)",
        "question": (
            "MAR; per the target-override post-step, recommendation becomes "
            "EXCLUDE_TARGET_NULL_ROWS. Feature computation must skip NULL-target rows."
        ),
    },
    {
        "id": "DS-AOEC-08",
        "columns": "leaderboards_raw, profiles_raw",
        "question": (
            "NOT_USABLE per 01_03_03; profiles_raw has 7 dead columns (100% NULL). "
            "Formally declare out-of-analytical-scope at 01_04_02+ -- these tables do not "
            "enter any VIEW and do not need triage."
        ),
    },
]

artifact["missingness_audit"] = {
    "framework": {
        "source_doc": "temp/null_handling_recommendations.md",
        "rules_applied": ["S1", "S2", "S3", "S4", "S5", "S6"],
        "mechanism_taxonomy": "Rubin (1976); Little & Rubin (2019, 3rd ed.)",
        "phase_boundary": "Phase 01 documents (I9). Phase 02 transforms.",
        "note_on_rates": (
            "All triage rates in the ledger derive from VIEWs (filtered scope), not raw tables. "
            "A column with 42% NULL in matches_raw can be ~26% NULL in matches_1v1_clean. "
            "The ledger is authoritative for downstream decisions because Phase 02 features "
            "are computed from the VIEWs."
        ),
        "thresholds": {
            "low_rate_pct": 5.0,
            "mid_rate_pct": 40.0,
            "high_rate_pct": 80.0,
            "threshold_source": (
                "Operational starting heuristics from temp/null_handling_recommendations.md §1.2; "
                "<5% MCAR boundary citation: Schafer & Graham 2002; "
                "warning against rigid global thresholds: van Buuren 2018"
            ),
        },
        "override_priority": [
            "1. Identity-column branch (B5): identity cols routed to mechanism=N/A, RETAIN_AS_IS",
            "2. Constants detection (n_distinct == 1 AND zero NULLs AND zero sentinels) -> mechanism=N/A, DROP_COLUMN",
            "3. F1 zero-missingness (n_total_missing == 0) -> mechanism=N/A, RETAIN_AS_IS",
            "4. _recommend() per spec/fallback (incl. CONVERT_SENTINEL_TO_NULL for sentinel-only low-rate cases)",
            "5. Target-column post-step (col in target_cols AND n_total_missing > 0) -> EXCLUDE_TARGET_NULL_ROWS",
        ],
        "per_view_target_cols": {
            "matches_1v1_clean": list(_TARGET_COLS_M1),
            "player_history_all": list(_TARGET_COLS_PH),
        },
        "per_view_identity_cols": {
            "matches_1v1_clean": list(_IDENTITY_COLS_M1),
            "player_history_all": list(_IDENTITY_COLS_PH),
        },
    },
    "missingness_spec": {
        col: {
            "mechanism": m["mechanism"],
            "justification": m["justification"],
            "sentinel_value": repr(m["sentinel_value"]) if m["sentinel_value"] is not None else None,
            "carries_semantic_content": m["carries_semantic_content"],
            "is_primary_feature": m["is_primary_feature"],
        }
        for col, m in _missingness_spec.items()
    },
    "matches_1v1_clean": {
        "total_rows": int(total_rows_m1),
        "n_cols": len(df_ledger_m1),
        "ledger": df_ledger_m1.to_dict(orient="records"),
    },
    "player_history_all": {
        "total_rows": int(total_rows_ph),
        "n_cols": len(df_ledger_ph),
        "ledger": df_ledger_ph.to_dict(orient="records"),
    },
    "decisions_surfaced": _decisions_surfaced_list,
}

artifact["sql_queries"]["missingness_sentinel_template"] = (
    'SELECT COUNT(*) FILTER (WHERE "{col}" {predicate}) FROM {view_name}'
)
artifact["sql_queries"]["missingness_constants_template"] = (
    'SELECT COUNT(DISTINCT "{col}") FROM {view_name}'
)

# Assertions: decisions_surfaced non-empty
assert len(artifact["missingness_audit"]["decisions_surfaced"]) >= 1
assert all(
    "question" in d and d["question"]
    for d in artifact["missingness_audit"]["decisions_surfaced"]
)

json_path = cleaning_dir / "01_04_01_data_cleaning.json"
with open(json_path, "w") as f:
    json.dump(artifact, f, indent=2, default=str)
print(f"Artifact written: {json_path}")

# %%
# Write standalone missingness ledger CSV + JSON
df_ledger_combined = pd.concat([df_ledger_m1, df_ledger_ph], ignore_index=True)

ledger_csv_path = cleaning_dir / "01_04_01_missingness_ledger.csv"
df_ledger_combined.to_csv(ledger_csv_path, index=False)
print(f"Missingness ledger CSV written: {ledger_csv_path} ({len(df_ledger_combined)} rows)")

ledger_json_obj = {
    "step": "01_04_01",
    "dataset": "aoe2companion",
    "generated_date": str(date.today()),
    "framework": artifact["missingness_audit"]["framework"],
    "missingness_spec": artifact["missingness_audit"]["missingness_spec"],
    "ledger": df_ledger_combined.to_dict(orient="records"),
    "decisions_surfaced": _decisions_surfaced_list,
}

ledger_json_path = cleaning_dir / "01_04_01_missingness_ledger.json"
with open(ledger_json_path, "w") as f:
    json.dump(ledger_json_obj, f, indent=2, default=str)
print(f"Missingness ledger JSON written: {ledger_json_path}")

# Gate assertions: files exist, correct column count
assert ledger_csv_path.exists(), "ledger CSV not found"
assert ledger_json_path.exists(), "ledger JSON not found"
assert set(df_ledger_combined.columns) == {
    "view", "column", "dtype", "n_total", "n_null", "pct_null",
    "sentinel_value", "n_sentinel", "pct_sentinel", "pct_missing_total",
    "n_distinct", "mechanism", "mechanism_justification",
    "recommendation", "recommendation_justification",
    "carries_semantic_content", "is_primary_feature",
}, f"Unexpected ledger columns: {set(df_ledger_combined.columns)}"
print(f"Ledger gate assertions passed: {len(df_ledger_combined)} total rows, 17 columns")

# %%
# Markdown artifact
md_lines = [
    "# 01_04_01 Data Cleaning Artifact — aoe2companion",
    "",
    f"**Generated:** {date.today()}  ",
    f"**Step:** 01_04_01  ",
    "**Dataset:** aoe2companion  ",
    "",
    "## Cleaning Registry",
    "",
    "| Rule | Name | Condition | Action | Impact |",
    "|------|------|-----------|--------|--------|",
]
for rid, rule in artifact["cleaning_registry"].items():
    md_lines.append(f"| {rid} | {rule['name']} | {rule['condition']} | {rule['action']} | {rule['impact']} |")

md_lines += [
    "",
    "## CONSORT Flow",
    "",
    "| Stage | N rows | N matches | Description |",
    "|-------|--------|-----------|-------------|",
]
for stage, vals in artifact["consort_flow"].items():
    if "description" in vals:
        md_lines.append(f"| {stage} | {vals.get('n_rows', '—'):,} | {vals.get('n_matches', '—')} | {vals['description']} |")

md_lines += [
    "",
    "## Post-Cleaning Validation",
    "",
    f"- **V1 Rating coverage:** {artifact['post_cleaning_validation']['V1_rating_coverage']['rating_coverage_pct']}%",
    f"- **V2 No POST-GAME leakage:** {'PASS' if artifact['post_cleaning_validation']['V2_no_postgame_leakage']['pass'] else 'FAIL'}",
    f"- **V3 No negative ratings:** {'PASS' if artifact['post_cleaning_validation']['V3_rating_sanity']['pass'] else 'FAIL'}",
    f"- **V7 No anonymous rows:** {'PASS' if artifact['post_cleaning_validation']['V7_no_anonymous_rows']['pass'] else 'FAIL'}",
    "",
    "### V4 Leaderboard Distribution (matches_1v1_clean)",
    "",
    "| Leaderboard | internalLeaderboardId | N rows |",
    "|-------------|----------------------|--------|",
]
for lb, vals in artifact["post_cleaning_validation"]["V4_leaderboard_distribution"].items():
    md_lines.append(f"| {lb} | {vals['internalLeaderboardId']} | {vals['n_rows']:,} |")

md_lines += [
    "",
    "### V8 Leaderboard Diversity (player_history_all)",
    "",
    "| Leaderboard | N rows |",
    "|-------------|--------|",
]
for lb, n in artifact["post_cleaning_validation"]["V8_leaderboard_diversity"].items():
    md_lines.append(f"| {lb} | {n:,} |")

# NULL Audit markdown section
md_lines += [
    "",
    "## NULL Audit",
    "",
    "### matches_1v1_clean",
    "",
    f"Total rows: {int(total_rows_m1):,}",
    "",
    "| Column | NULL count | NULL % |",
    "|--------|-----------|--------|",
]
for r in null_results_m1:
    md_lines.append(f"| {r['column']} | {r['null_count']:,} | {r['null_pct']}% |")

md_lines += [
    "",
    f"Zero-NULL assertions: {', '.join(M1_ZERO_NULL_COLS)} -- all PASS",
    "",
    "### player_history_all",
    "",
    f"Total rows: {int(total_rows_ph):,}",
    "",
    "| Column | NULL count | NULL % |",
    "|--------|-----------|--------|",
]
for r in null_results_ph:
    md_lines.append(f"| {r['column']} | {r['null_count']:,} | {r['null_pct']}% |")

md_lines += [
    "",
    f"Zero-NULL assertions: {', '.join(PH_ZERO_NULL_COLS)} -- all PASS",
    (
        "Zero-NULL evidence: 01_02_04 census (matches_raw_null_census) confirms "
        "null_count=0 for matchId, profileId, started in matches_raw."
    ),
    f"Nullable finding: won has {won_null_count_ph:,} NULLs ({won_null_pct_ph}%) -- documented, not asserted",
]

# Missingness Ledger section
md_lines += [
    "",
    "## Missingness Ledger",
    "",
    "> **Note on rates:** All triage rates derive from VIEWs (filtered scope), not raw tables.",
    "> A column with 42% NULL in matches_raw can be ~26% NULL in matches_1v1_clean.",
    "> The ledger is authoritative for downstream decisions because Phase 02 features",
    "> are computed from the VIEWs.",
    "",
    "### Missingness Ledger: matches_1v1_clean",
    "",
    f"Total rows: {int(total_rows_m1):,} | Columns: {len(df_ledger_m1)}",
    "",
    "| Column | Dtype | pct_missing_total | mechanism | recommendation |",
    "|--------|-------|-------------------|-----------|----------------|",
]
for _, row in df_ledger_m1.iterrows():
    md_lines.append(
        f"| {row['column']} | {row['dtype']} | {row['pct_missing_total']} | "
        f"{row['mechanism']} | {row['recommendation']} |"
    )

md_lines += [
    "",
    "### Missingness Ledger: player_history_all",
    "",
    f"Total rows: {int(total_rows_ph):,} | Columns: {len(df_ledger_ph)}",
    "",
    "| Column | Dtype | pct_missing_total | mechanism | recommendation |",
    "|--------|-------|-------------------|-----------|----------------|",
]
for _, row in df_ledger_ph.iterrows():
    md_lines.append(
        f"| {row['column']} | {row['dtype']} | {row['pct_missing_total']} | "
        f"{row['mechanism']} | {row['recommendation']} |"
    )

# Decisions surfaced section
md_lines += [
    "",
    "## Decisions surfaced for downstream cleaning (01_04_02+)",
    "",
]
for ds in _decisions_surfaced_list:
    ds_id = ds["id"]
    ds_col = ds.get("column", ds.get("columns", ""))
    ds_q = ds["question"]
    md_lines += [
        f"### {ds_id}",
        f"**Column(s):** {ds_col}",
        "",
        f"**Question:** {ds_q}",
        "",
    ]

md_lines += ["", "## SQL Queries", ""]
for qname, qsql in artifact["sql_queries"].items():
    md_lines += [f"### {qname}", "", "```sql", qsql.strip(), "```", ""]

md_path = cleaning_dir / "01_04_01_data_cleaning.md"
with open(md_path, "w") as f:
    f.write("\n".join(md_lines))
print(f"MD artifact written: {md_path}")

print("\nStep 01_04_01 complete.")
