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

json_path = cleaning_dir / "01_04_01_data_cleaning.json"
with open(json_path, "w") as f:
    json.dump(artifact, f, indent=2, default=str)
print(f"Artifact written: {json_path}")

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

md_lines += ["", "## SQL Queries", ""]
for qname, qsql in artifact["sql_queries"].items():
    md_lines += [f"### {qname}", "", "```sql", qsql.strip(), "```", ""]

md_path = cleaning_dir / "01_04_01_data_cleaning.md"
with open(md_path, "w") as f:
    f.write("\n".join(md_lines))
print(f"MD artifact written: {md_path}")

print("\nStep 01_04_01 complete.")
