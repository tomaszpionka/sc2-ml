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
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Step 01_03_01 -- Systematic Data Profiling: aoestats
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_03 -- Systematic Data Profiling
# **Dataset:** aoestats
# **Question:** What is the comprehensive column-level and dataset-level
# statistical profile for matches_raw and players_raw?
# **Invariants applied:**
# - #3 (temporal discipline -- every column annotated with temporal class)
# - #6 (reproducibility -- all SQL stored verbatim in markdown artifact)
# - #7 (no magic numbers -- all thresholds from census JSON; sample size justified)
# - #9 (step scope: profiling only -- no cleaning or feature decisions)
# **Predecessor:** 01_02_07 (Multivariate EDA -- complete, artifacts on disk)
# **Step scope:** Systematic profiling only. Critical findings flagged for
# 01_04, not acted upon.
# **ROADMAP reference:** `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` Step 01_03_01
# **Commit:** 64b322b
# **Date:** 2026-04-16
# **ROADMAP ref:** 01_03_01

# %%
import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir, setup_notebook_logging

matplotlib.use("Agg")
logger = setup_notebook_logging(__name__)

# %%
db = get_notebook_db("aoe2", "aoestats")

# %%
reports_dir = get_reports_dir("aoe2", "aoestats")
profiling_dir = reports_dir / "artifacts" / "01_exploration" / "03_profiling"
profiling_dir.mkdir(parents=True, exist_ok=True)

census_path = reports_dir / "artifacts" / "01_exploration" / "02_eda" / "01_02_04_univariate_census.json"
with open(census_path) as f:
    census = json.load(f)

bivariate_path = reports_dir / "artifacts" / "01_exploration" / "02_eda" / "01_02_06_bivariate_eda.json"
with open(bivariate_path) as f:
    bivariate = json.load(f)

# %%
required_census_keys = [
    "matches_null_census", "players_null_census",
    "numeric_stats_matches", "numeric_stats_players",
    "elo_sentinel_counts", "skew_kurtosis_matches", "skew_kurtosis_players",
    "outlier_counts_matches", "outlier_counts_players",
    "categorical_matches", "categorical_players",
    "winner_distribution", "duplicate_check_matches",
]
for k in required_census_keys:
    assert k in census, f"Missing census key: {k}"

assert bivariate["match_rating_diff_leakage"]["leakage_status"] == "PRE_GAME", (
    "match_rating_diff leakage must be resolved as PRE_GAME before profiling"
)
print("All required keys present. match_rating_diff = PRE_GAME (confirmed).")

# %%
sql_queries = {}
profile = {
    "step": "01_03_01",
    "dataset": "aoestats",
}

# I7: All constants from census -- no magic numbers
ELO_SENTINEL = -1  # census["elo_negative_distinct_values"] == [-1.0]
MATCHES_TOTAL = census["matches_null_census"]["total_rows"]  # 30,690,651
PLAYERS_TOTAL = census["players_null_census"]["total_rows"]  # 107,627,584
# I7: 50K RESERVOIR sample for QQ/ECDF -- SE of quantile estimate negligible
# at N=50K. For the median: SE(median) ~ sigma / (2*sqrt(N)*f(median)).
# At N=50K, SE ~ sigma/447, well below any substantive threshold.
SAMPLE_SIZE = 50_000

# I7: Near-constant detection cardinality cap. A column is near-constant only
# if (uniqueness_ratio < 0.001 AND cardinality <= NEAR_CONSTANT_CARDINALITY_CAP)
# OR (numeric IQR == 0). Cardinality cap of 5 prevents flagging low-cardinality
# but information-bearing categoricals (e.g. civ=50 values, winner=2 values at
# 30M rows). Threshold derived from constant-column boundary (cardinality=1)
# plus buffer; Manual Section 3.3.
NEAR_CONSTANT_CARDINALITY_CAP = 5

print(f"ELO_SENTINEL = {ELO_SENTINEL}")
print(f"MATCHES_TOTAL = {MATCHES_TOTAL:,}")
print(f"PLAYERS_TOTAL = {PLAYERS_TOTAL:,}")
print(f"SAMPLE_SIZE = {SAMPLE_SIZE:,}")
print(f"NEAR_CONSTANT_CARDINALITY_CAP = {NEAR_CONSTANT_CARDINALITY_CAP}")

# %%
# I3: Temporal class for every column, derived from 01_02_04/01_02_06 findings.
# match_rating_diff confirmed PRE_GAME in 01_02_06 (Pearson r=0.054 vs
# new_rating - old_rating).
TEMPORAL_CLASS = {
    # matches_raw columns
    "map": "CONTEXT",
    "started_timestamp": "CONTEXT",
    "duration": "POST-GAME",
    "irl_duration": "POST-GAME",
    "game_id": "IDENTIFIER",
    "avg_elo": "PRE-GAME",  # Classified PRE-GAME by convention (team-level ELO mean).
                              # No formal leakage test in 01_02_06; deferred to 01_04.
                              # If derived from new_rating, reclassify to POST-GAME.
    "num_players": "CONTEXT",
    "team_0_elo": "PRE-GAME",
    "team_1_elo": "PRE-GAME",
    "replay_enhanced": "CONTEXT",
    "leaderboard": "CONTEXT",
    "mirror": "POST-GAME",
    "patch": "CONTEXT",
    "raw_match_type": "CONTEXT",
    "game_type": "CONTEXT",
    "game_speed": "CONTEXT",
    "starting_age": "CONTEXT",
    "filename": "IDENTIFIER",
    # players_raw columns
    "winner": "TARGET",
    "team": "CONTEXT",
    "feudal_age_uptime": "IN-GAME",
    "castle_age_uptime": "IN-GAME",
    "imperial_age_uptime": "IN-GAME",
    "old_rating": "PRE-GAME",
    "new_rating": "POST-GAME",
    "match_rating_diff": "PRE-GAME",
    "replay_summary_raw": "CONTEXT",
    "profile_id": "IDENTIFIER",
    "civ": "PRE-GAME",
    "opening": "IN-GAME",
}
print(f"Temporal class lookup: {len(TEMPORAL_CLASS)} columns classified")

# %% [markdown]
# ## Section 3.1a -- Column-Level Profile: matches_raw

# %%
sql_matches_numeric_profile = """
WITH base AS (
    SELECT
        COUNT(*)                                          AS total_rows,
        -- duration (BIGINT nanoseconds -> seconds)
        COUNT(duration)                                   AS duration_nonnull,
        COUNT(*) - COUNT(duration)                        AS duration_null,
        COUNT(*) FILTER (WHERE duration = 0)              AS duration_zero,
        COUNT(DISTINCT duration)                          AS duration_distinct,
        AVG(duration / 1e9)                               AS duration_mean,
        STDDEV_SAMP(duration / 1e9)                       AS duration_std,
        MIN(duration / 1e9)                               AS duration_min,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY duration / 1e9) AS duration_p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY duration / 1e9) AS duration_p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration / 1e9) AS duration_p50,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY duration / 1e9) AS duration_p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration / 1e9) AS duration_p95,
        MAX(duration / 1e9)                               AS duration_max,
        SKEWNESS(duration / 1e9)                          AS duration_skew,
        KURTOSIS(duration / 1e9)                          AS duration_kurt,
        -- irl_duration
        COUNT(irl_duration)                               AS irl_duration_nonnull,
        COUNT(*) - COUNT(irl_duration)                    AS irl_duration_null,
        COUNT(*) FILTER (WHERE irl_duration = 0)          AS irl_duration_zero,
        COUNT(DISTINCT irl_duration)                      AS irl_duration_distinct,
        AVG(irl_duration / 1e9)                           AS irl_duration_mean,
        STDDEV_SAMP(irl_duration / 1e9)                   AS irl_duration_std,
        MIN(irl_duration / 1e9)                           AS irl_duration_min,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY irl_duration / 1e9) AS irl_duration_p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY irl_duration / 1e9) AS irl_duration_p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY irl_duration / 1e9) AS irl_duration_p50,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY irl_duration / 1e9) AS irl_duration_p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY irl_duration / 1e9) AS irl_duration_p95,
        MAX(irl_duration / 1e9)                           AS irl_duration_max,
        SKEWNESS(irl_duration / 1e9)                      AS irl_duration_skew,
        KURTOSIS(irl_duration / 1e9)                      AS irl_duration_kurt,
        -- avg_elo
        COUNT(avg_elo)                                    AS avg_elo_nonnull,
        COUNT(*) - COUNT(avg_elo)                         AS avg_elo_null,
        COUNT(*) FILTER (WHERE avg_elo = 0)               AS avg_elo_zero,
        COUNT(DISTINCT avg_elo)                           AS avg_elo_distinct,
        AVG(avg_elo)                                      AS avg_elo_mean,
        STDDEV_SAMP(avg_elo)                              AS avg_elo_std,
        MIN(avg_elo)                                      AS avg_elo_min,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY avg_elo) AS avg_elo_p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY avg_elo) AS avg_elo_p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY avg_elo) AS avg_elo_p50,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY avg_elo) AS avg_elo_p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY avg_elo) AS avg_elo_p95,
        MAX(avg_elo)                                      AS avg_elo_max,
        SKEWNESS(avg_elo)                                 AS avg_elo_skew,
        KURTOSIS(avg_elo)                                 AS avg_elo_kurt,
        -- team_0_elo (ALL rows, including sentinel -1)
        COUNT(team_0_elo)                                 AS team_0_elo_nonnull,
        COUNT(*) - COUNT(team_0_elo)                      AS team_0_elo_null,
        COUNT(*) FILTER (WHERE team_0_elo = 0)            AS team_0_elo_zero,
        COUNT(DISTINCT team_0_elo)                        AS team_0_elo_distinct,
        AVG(team_0_elo)                                   AS team_0_elo_mean,
        STDDEV_SAMP(team_0_elo)                           AS team_0_elo_std,
        MIN(team_0_elo)                                   AS team_0_elo_min,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY team_0_elo) AS team_0_elo_p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY team_0_elo) AS team_0_elo_p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY team_0_elo) AS team_0_elo_p50,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY team_0_elo) AS team_0_elo_p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY team_0_elo) AS team_0_elo_p95,
        MAX(team_0_elo)                                   AS team_0_elo_max,
        SKEWNESS(team_0_elo)                              AS team_0_elo_skew,
        KURTOSIS(team_0_elo)                              AS team_0_elo_kurt,
        -- team_1_elo (ALL rows, including sentinel -1)
        COUNT(team_1_elo)                                 AS team_1_elo_nonnull,
        COUNT(*) - COUNT(team_1_elo)                      AS team_1_elo_null,
        COUNT(*) FILTER (WHERE team_1_elo = 0)            AS team_1_elo_zero,
        COUNT(DISTINCT team_1_elo)                        AS team_1_elo_distinct,
        AVG(team_1_elo)                                   AS team_1_elo_mean,
        STDDEV_SAMP(team_1_elo)                           AS team_1_elo_std,
        MIN(team_1_elo)                                   AS team_1_elo_min,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY team_1_elo) AS team_1_elo_p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY team_1_elo) AS team_1_elo_p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY team_1_elo) AS team_1_elo_p50,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY team_1_elo) AS team_1_elo_p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY team_1_elo) AS team_1_elo_p95,
        MAX(team_1_elo)                                   AS team_1_elo_max,
        SKEWNESS(team_1_elo)                              AS team_1_elo_skew,
        KURTOSIS(team_1_elo)                              AS team_1_elo_kurt,
        -- raw_match_type
        COUNT(raw_match_type)                             AS raw_match_type_nonnull,
        COUNT(*) - COUNT(raw_match_type)                  AS raw_match_type_null,
        COUNT(*) FILTER (WHERE raw_match_type = 0)        AS raw_match_type_zero,
        COUNT(DISTINCT raw_match_type)                    AS raw_match_type_distinct,
        AVG(raw_match_type)                               AS raw_match_type_mean,
        STDDEV_SAMP(raw_match_type)                       AS raw_match_type_std,
        MIN(raw_match_type)                               AS raw_match_type_min,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY raw_match_type) AS raw_match_type_p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY raw_match_type) AS raw_match_type_p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY raw_match_type) AS raw_match_type_p50,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY raw_match_type) AS raw_match_type_p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY raw_match_type) AS raw_match_type_p95,
        MAX(raw_match_type)                               AS raw_match_type_max,
        SKEWNESS(raw_match_type)                          AS raw_match_type_skew,
        KURTOSIS(raw_match_type)                          AS raw_match_type_kurt,
        -- patch
        COUNT(patch)                                      AS patch_nonnull,
        COUNT(*) - COUNT(patch)                           AS patch_null,
        COUNT(*) FILTER (WHERE patch = 0)                 AS patch_zero,
        COUNT(DISTINCT patch)                             AS patch_distinct,
        AVG(patch)                                        AS patch_mean,
        STDDEV_SAMP(patch)                                AS patch_std,
        MIN(patch)                                        AS patch_min,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY patch) AS patch_p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY patch) AS patch_p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY patch) AS patch_p50,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY patch) AS patch_p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY patch) AS patch_p95,
        MAX(patch)                                        AS patch_max,
        SKEWNESS(patch)                                   AS patch_skew,
        KURTOSIS(patch)                                   AS patch_kurt,
        -- num_players
        COUNT(num_players)                                AS num_players_nonnull,
        COUNT(*) - COUNT(num_players)                     AS num_players_null,
        COUNT(*) FILTER (WHERE num_players = 0)           AS num_players_zero,
        COUNT(DISTINCT num_players)                       AS num_players_distinct,
        AVG(num_players)                                  AS num_players_mean,
        STDDEV_SAMP(num_players)                          AS num_players_std,
        MIN(num_players)                                  AS num_players_min,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY num_players) AS num_players_p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY num_players) AS num_players_p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY num_players) AS num_players_p50,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY num_players) AS num_players_p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY num_players) AS num_players_p95,
        MAX(num_players)                                  AS num_players_max,
        SKEWNESS(num_players)                             AS num_players_skew,
        KURTOSIS(num_players)                             AS num_players_kurt
    FROM matches_raw
)
SELECT * FROM base
"""
sql_queries["matches_numeric_profile"] = sql_matches_numeric_profile

# %%
row = db.fetch_df(sql_matches_numeric_profile).iloc[0]
matches_numeric_cols = [
    "duration", "irl_duration", "avg_elo", "team_0_elo", "team_1_elo",
    "raw_match_type", "patch", "num_players",
]
matches_column_profiles = {}
for col in matches_numeric_cols:
    nonnull = int(row[f"{col}_nonnull"])
    null_ct = int(row[f"{col}_null"])
    total = nonnull + null_ct
    p25 = float(row[f"{col}_p25"]) if row[f"{col}_p25"] is not None else 0.0
    p75 = float(row[f"{col}_p75"]) if row[f"{col}_p75"] is not None else 0.0
    iqr = p75 - p25
    matches_column_profiles[col] = {
        "table": "matches_raw",
        "temporal_class": TEMPORAL_CLASS[col],
        "dtype": "numeric",
        "null_count": null_ct,
        "null_pct": round(null_ct / total * 100, 4) if total > 0 else 0,
        "zero_count": int(row[f"{col}_zero"]),
        "zero_pct": round(int(row[f"{col}_zero"]) / total * 100, 4) if total > 0 else 0,
        "cardinality": int(row[f"{col}_distinct"]),
        "uniqueness_ratio": round(int(row[f"{col}_distinct"]) / total, 6) if total > 0 else 0,
        "mean": round(float(row[f"{col}_mean"]), 4) if row[f"{col}_mean"] is not None else None,
        "std": round(float(row[f"{col}_std"]), 4) if row[f"{col}_std"] is not None else None,
        "min": round(float(row[f"{col}_min"]), 4) if row[f"{col}_min"] is not None else None,
        "p05": round(float(row[f"{col}_p05"]), 4) if row[f"{col}_p05"] is not None else None,
        "p25": round(p25, 4),
        "p50": round(float(row[f"{col}_p50"]), 4) if row[f"{col}_p50"] is not None else None,
        "p75": round(p75, 4),
        "p95": round(float(row[f"{col}_p95"]), 4) if row[f"{col}_p95"] is not None else None,
        "max": round(float(row[f"{col}_max"]), 4) if row[f"{col}_max"] is not None else None,
        "skewness": round(float(row[f"{col}_skew"]), 4) if row[f"{col}_skew"] is not None else None,
        "kurtosis": round(float(row[f"{col}_kurt"]), 4) if row[f"{col}_kurt"] is not None else None,
        "iqr": round(iqr, 4),
    }
    print(f"  {col}: null={null_ct}, distinct={matches_column_profiles[col]['cardinality']}")

# %%
sql_matches_iqr_outliers = """
SELECT
    COUNT(*) FILTER (WHERE duration/1e9 < {dur_lo} OR duration/1e9 > {dur_hi})   AS duration_outliers,
    COUNT(*) FILTER (WHERE irl_duration/1e9 < {irl_lo} OR irl_duration/1e9 > {irl_hi}) AS irl_duration_outliers,
    COUNT(*) FILTER (WHERE avg_elo < {ae_lo} OR avg_elo > {ae_hi})               AS avg_elo_outliers,
    COUNT(*) FILTER (WHERE team_0_elo != -1 AND (team_0_elo < {t0_lo} OR team_0_elo > {t0_hi})) AS team_0_elo_outliers,
    COUNT(*) FILTER (WHERE team_1_elo != -1 AND (team_1_elo < {t1_lo} OR team_1_elo > {t1_hi})) AS team_1_elo_outliers,
    COUNT(*) FILTER (WHERE raw_match_type IS NOT NULL AND (raw_match_type < {rmt_lo} OR raw_match_type > {rmt_hi})) AS raw_match_type_outliers,
    COUNT(*) FILTER (WHERE patch < {p_lo} OR patch > {p_hi})                      AS patch_outliers,
    COUNT(*) FILTER (WHERE num_players < {np_lo} OR num_players > {np_hi})        AS num_players_outliers
FROM matches_raw
"""
# Compute fences from profile p25/p75
fences = {}
for col in matches_numeric_cols:
    p = matches_column_profiles[col]
    iqr = p["iqr"]
    fences[col] = (p["p25"] - 1.5 * iqr, p["p75"] + 1.5 * iqr)

sql_formatted = sql_matches_iqr_outliers.format(
    dur_lo=fences["duration"][0], dur_hi=fences["duration"][1],
    irl_lo=fences["irl_duration"][0], irl_hi=fences["irl_duration"][1],
    ae_lo=fences["avg_elo"][0], ae_hi=fences["avg_elo"][1],
    t0_lo=fences["team_0_elo"][0], t0_hi=fences["team_0_elo"][1],
    t1_lo=fences["team_1_elo"][0], t1_hi=fences["team_1_elo"][1],
    rmt_lo=fences["raw_match_type"][0], rmt_hi=fences["raw_match_type"][1],
    p_lo=fences["patch"][0], p_hi=fences["patch"][1],
    np_lo=fences["num_players"][0], np_hi=fences["num_players"][1],
)
sql_queries["matches_iqr_outliers"] = sql_formatted
outlier_row = db.fetch_df(sql_formatted).iloc[0]
for col in matches_numeric_cols:
    ct = int(outlier_row[f"{col}_outliers"])
    total = matches_column_profiles[col]["null_count"] + int(row[f"{col}_nonnull"])
    matches_column_profiles[col]["iqr_outlier_count"] = ct
    matches_column_profiles[col]["iqr_outlier_pct"] = round(ct / total * 100, 4) if total > 0 else 0
    matches_column_profiles[col]["iqr_lower_fence"] = round(fences[col][0], 4)
    matches_column_profiles[col]["iqr_upper_fence"] = round(fences[col][1], 4)
    print(f"  {col}: {ct:,} outliers ({matches_column_profiles[col]['iqr_outlier_pct']}%)")

# %%
# B1 fix: Use a CTE pre-filter instead of PERCENTILE_CONT WITHIN GROUP FILTER,
# which has uncertain DuckDB support for ordered-set aggregates. All aggregates
# (PERCENTILE_CONT, AVG, STDDEV_SAMP, SKEWNESS, KURTOSIS) run on the
# pre-filtered CTE for consistency.
sql_elo_no_sentinel = f"""
WITH elo_filtered AS (
    SELECT *
    FROM matches_raw
    WHERE team_0_elo != {ELO_SENTINEL} AND team_1_elo != {ELO_SENTINEL}
)
SELECT
    -- team_0_elo excluding sentinel -1 (via CTE pre-filter)
    COUNT(team_0_elo)                                                         AS t0_nonnull,
    AVG(team_0_elo)                                                           AS t0_mean,
    STDDEV_SAMP(team_0_elo)                                                   AS t0_std,
    MIN(team_0_elo)                                                           AS t0_min,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY team_0_elo)                  AS t0_p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY team_0_elo)                  AS t0_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY team_0_elo)                  AS t0_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY team_0_elo)                  AS t0_p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY team_0_elo)                  AS t0_p95,
    MAX(team_0_elo)                                                           AS t0_max,
    SKEWNESS(team_0_elo)                                                      AS t0_skew,
    KURTOSIS(team_0_elo)                                                      AS t0_kurt,
    -- team_1_elo excluding sentinel -1 (via CTE pre-filter)
    COUNT(team_1_elo)                                                         AS t1_nonnull,
    AVG(team_1_elo)                                                           AS t1_mean,
    STDDEV_SAMP(team_1_elo)                                                   AS t1_std,
    MIN(team_1_elo)                                                           AS t1_min,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY team_1_elo)                  AS t1_p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY team_1_elo)                  AS t1_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY team_1_elo)                  AS t1_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY team_1_elo)                  AS t1_p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY team_1_elo)                  AS t1_p95,
    MAX(team_1_elo)                                                           AS t1_max,
    SKEWNESS(team_1_elo)                                                      AS t1_skew,
    KURTOSIS(team_1_elo)                                                      AS t1_kurt
FROM elo_filtered
"""
sql_queries["elo_no_sentinel"] = sql_elo_no_sentinel
elo_ns = db.fetch_df(sql_elo_no_sentinel).iloc[0]
for prefix, col in [("t0", "team_0_elo"), ("t1", "team_1_elo")]:
    matches_column_profiles[col]["stats_excluding_sentinel"] = {
        "n_nonnull": int(elo_ns[f"{prefix}_nonnull"]),
        "mean": round(float(elo_ns[f"{prefix}_mean"]), 4),
        "std": round(float(elo_ns[f"{prefix}_std"]), 4),
        "min": round(float(elo_ns[f"{prefix}_min"]), 4),
        "p05": round(float(elo_ns[f"{prefix}_p05"]), 4),
        "p25": round(float(elo_ns[f"{prefix}_p25"]), 4),
        "p50": round(float(elo_ns[f"{prefix}_p50"]), 4),
        "p75": round(float(elo_ns[f"{prefix}_p75"]), 4),
        "p95": round(float(elo_ns[f"{prefix}_p95"]), 4),
        "max": round(float(elo_ns[f"{prefix}_max"]), 4),
        "skewness": round(float(elo_ns[f"{prefix}_skew"]), 4),
        "kurtosis": round(float(elo_ns[f"{prefix}_kurt"]), 4),
    }
print("ELO sentinel-excluded stats computed for team_0_elo and team_1_elo")

# %%
matches_categorical_cols = [
    "map", "leaderboard", "game_type", "game_speed", "starting_age",
    "replay_enhanced", "mirror", "game_id", "filename",
]
for col in matches_categorical_cols:
    sql_cat = f"""
    SELECT CAST({col} AS VARCHAR) AS val, COUNT(*) AS cnt
    FROM matches_raw
    WHERE {col} IS NOT NULL
    GROUP BY {col}
    ORDER BY cnt DESC
    LIMIT 5
    """
    sql_queries[f"matches_topk_{col}"] = sql_cat
    topk_df = db.fetch_df(sql_cat)

    sql_card = f"SELECT COUNT(DISTINCT {col}) AS card, COUNT(*) - COUNT({col}) AS null_ct, COUNT(*) AS total FROM matches_raw"
    card_row = db.fetch_df(sql_card).iloc[0]

    total = int(card_row["total"])
    null_ct = int(card_row["null_ct"])
    card = int(card_row["card"])
    matches_column_profiles[col] = {
        "table": "matches_raw",
        "temporal_class": TEMPORAL_CLASS[col],
        "dtype": "categorical",
        "null_count": null_ct,
        "null_pct": round(null_ct / total * 100, 4) if total > 0 else 0,
        "cardinality": card,
        "uniqueness_ratio": round(card / total, 6) if total > 0 else 0,
        "top_5": topk_df.to_dict(orient="records"),
    }
    print(f"  {col}: card={card}, null={null_ct}")

# BOOLEAN columns treated separately (already in census)
for col in ["replay_enhanced", "mirror"]:
    matches_column_profiles[col]["dtype"] = "boolean"

print(f"Total matches_raw column profiles (before timestamp): {len(matches_column_profiles)}")

# %%
sql_ts = """
SELECT
    COUNT(started_timestamp)              AS ts_nonnull,
    COUNT(*) - COUNT(started_timestamp)   AS ts_null,
    COUNT(DISTINCT started_timestamp)     AS ts_distinct,
    MIN(started_timestamp)                AS ts_min,
    MAX(started_timestamp)                AS ts_max
FROM matches_raw
"""
sql_queries["matches_started_timestamp"] = sql_ts
ts_row = db.fetch_df(sql_ts).iloc[0]
matches_column_profiles["started_timestamp"] = {
    "table": "matches_raw",
    "temporal_class": TEMPORAL_CLASS["started_timestamp"],
    "dtype": "timestamp",
    "null_count": int(ts_row["ts_null"]),
    "null_pct": round(int(ts_row["ts_null"]) / MATCHES_TOTAL * 100, 4),
    "cardinality": int(ts_row["ts_distinct"]),
    "uniqueness_ratio": round(int(ts_row["ts_distinct"]) / MATCHES_TOTAL, 6),
    "min": str(ts_row["ts_min"]),
    "max": str(ts_row["ts_max"]),
}
assert len(matches_column_profiles) == 18, f"Expected 18 columns, got {len(matches_column_profiles)}"
print(f"matches_raw column profiles complete: {len(matches_column_profiles)} columns")

# %% [markdown]
# ## Section 3.1b -- Column-Level Profile: players_raw

# %%
sql_players_numeric_profile = """
SELECT
    COUNT(*) AS total_rows,
    -- old_rating (BIGINT; zeros are legitimate, NOT sentinels)
    COUNT(old_rating)                                     AS old_rating_nonnull,
    COUNT(*) - COUNT(old_rating)                          AS old_rating_null,
    COUNT(*) FILTER (WHERE old_rating = 0)                AS old_rating_zero,
    COUNT(DISTINCT old_rating)                            AS old_rating_distinct,
    AVG(old_rating)                                       AS old_rating_mean,
    STDDEV_SAMP(old_rating)                               AS old_rating_std,
    MIN(old_rating)                                       AS old_rating_min,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY old_rating) AS old_rating_p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY old_rating) AS old_rating_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY old_rating) AS old_rating_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY old_rating) AS old_rating_p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY old_rating) AS old_rating_p95,
    MAX(old_rating)                                       AS old_rating_max,
    SKEWNESS(old_rating)                                  AS old_rating_skew,
    KURTOSIS(old_rating)                                  AS old_rating_kurt,
    -- new_rating
    COUNT(new_rating)                                     AS new_rating_nonnull,
    COUNT(*) - COUNT(new_rating)                          AS new_rating_null,
    COUNT(*) FILTER (WHERE new_rating = 0)                AS new_rating_zero,
    COUNT(DISTINCT new_rating)                            AS new_rating_distinct,
    AVG(new_rating)                                       AS new_rating_mean,
    STDDEV_SAMP(new_rating)                               AS new_rating_std,
    MIN(new_rating)                                       AS new_rating_min,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY new_rating) AS new_rating_p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY new_rating) AS new_rating_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY new_rating) AS new_rating_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY new_rating) AS new_rating_p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY new_rating) AS new_rating_p95,
    MAX(new_rating)                                       AS new_rating_max,
    SKEWNESS(new_rating)                                  AS new_rating_skew,
    KURTOSIS(new_rating)                                  AS new_rating_kurt,
    -- match_rating_diff
    COUNT(match_rating_diff)                              AS mrd_nonnull,
    COUNT(*) - COUNT(match_rating_diff)                   AS mrd_null,
    COUNT(*) FILTER (WHERE match_rating_diff = 0)         AS mrd_zero,
    COUNT(DISTINCT match_rating_diff)                     AS mrd_distinct,
    AVG(match_rating_diff)                                AS mrd_mean,
    STDDEV_SAMP(match_rating_diff)                        AS mrd_std,
    MIN(match_rating_diff)                                AS mrd_min,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY match_rating_diff) AS mrd_p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY match_rating_diff) AS mrd_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY match_rating_diff) AS mrd_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY match_rating_diff) AS mrd_p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY match_rating_diff) AS mrd_p95,
    MAX(match_rating_diff)                                AS mrd_max,
    SKEWNESS(match_rating_diff)                           AS mrd_skew,
    KURTOSIS(match_rating_diff)                           AS mrd_kurt,
    -- feudal_age_uptime
    COUNT(feudal_age_uptime)                              AS fau_nonnull,
    COUNT(*) - COUNT(feudal_age_uptime)                   AS fau_null,
    COUNT(*) FILTER (WHERE feudal_age_uptime = 0)         AS fau_zero,
    COUNT(DISTINCT feudal_age_uptime)                     AS fau_distinct,
    AVG(feudal_age_uptime)                                AS fau_mean,
    STDDEV_SAMP(feudal_age_uptime)                        AS fau_std,
    MIN(feudal_age_uptime)                                AS fau_min,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY feudal_age_uptime) AS fau_p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY feudal_age_uptime) AS fau_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY feudal_age_uptime) AS fau_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY feudal_age_uptime) AS fau_p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY feudal_age_uptime) AS fau_p95,
    MAX(feudal_age_uptime)                                AS fau_max,
    SKEWNESS(feudal_age_uptime)                           AS fau_skew,
    KURTOSIS(feudal_age_uptime)                           AS fau_kurt,
    -- castle_age_uptime
    COUNT(castle_age_uptime)                              AS cau_nonnull,
    COUNT(*) - COUNT(castle_age_uptime)                   AS cau_null,
    COUNT(*) FILTER (WHERE castle_age_uptime = 0)         AS cau_zero,
    COUNT(DISTINCT castle_age_uptime)                     AS cau_distinct,
    AVG(castle_age_uptime)                                AS cau_mean,
    STDDEV_SAMP(castle_age_uptime)                        AS cau_std,
    MIN(castle_age_uptime)                                AS cau_min,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY castle_age_uptime) AS cau_p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY castle_age_uptime) AS cau_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY castle_age_uptime) AS cau_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY castle_age_uptime) AS cau_p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY castle_age_uptime) AS cau_p95,
    MAX(castle_age_uptime)                                AS cau_max,
    SKEWNESS(castle_age_uptime)                           AS cau_skew,
    KURTOSIS(castle_age_uptime)                           AS cau_kurt,
    -- imperial_age_uptime
    COUNT(imperial_age_uptime)                            AS iau_nonnull,
    COUNT(*) - COUNT(imperial_age_uptime)                 AS iau_null,
    COUNT(*) FILTER (WHERE imperial_age_uptime = 0)       AS iau_zero,
    COUNT(DISTINCT imperial_age_uptime)                   AS iau_distinct,
    AVG(imperial_age_uptime)                              AS iau_mean,
    STDDEV_SAMP(imperial_age_uptime)                      AS iau_std,
    MIN(imperial_age_uptime)                              AS iau_min,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY imperial_age_uptime) AS iau_p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY imperial_age_uptime) AS iau_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY imperial_age_uptime) AS iau_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY imperial_age_uptime) AS iau_p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY imperial_age_uptime) AS iau_p95,
    MAX(imperial_age_uptime)                              AS iau_max,
    SKEWNESS(imperial_age_uptime)                         AS iau_skew,
    KURTOSIS(imperial_age_uptime)                         AS iau_kurt,
    -- profile_id
    COUNT(profile_id)                                     AS pid_nonnull,
    COUNT(*) - COUNT(profile_id)                          AS pid_null,
    COUNT(*) FILTER (WHERE profile_id = 0)                AS pid_zero,
    COUNT(DISTINCT profile_id)                            AS pid_distinct,
    AVG(profile_id)                                       AS pid_mean,
    MIN(profile_id)                                       AS pid_min,
    MAX(profile_id)                                       AS pid_max,
    -- team
    COUNT(team)                                           AS team_nonnull,
    COUNT(*) - COUNT(team)                                AS team_null,
    COUNT(DISTINCT team)                                  AS team_distinct
FROM players_raw
"""
sql_queries["players_numeric_profile"] = sql_players_numeric_profile

# %%
p_row = db.fetch_df(sql_players_numeric_profile).iloc[0]

# Map of (profile_col, prefix) for the six main numeric columns
players_numeric_map = [
    ("old_rating", "old_rating"),
    ("new_rating", "new_rating"),
    ("match_rating_diff", "mrd"),
    ("feudal_age_uptime", "fau"),
    ("castle_age_uptime", "cau"),
    ("imperial_age_uptime", "iau"),
]
players_column_profiles = {}
for col, pfx in players_numeric_map:
    nonnull = int(p_row[f"{pfx}_nonnull"])
    null_ct = int(p_row[f"{pfx}_null"])
    total = nonnull + null_ct
    p25_val = float(p_row[f"{pfx}_p25"]) if p_row[f"{pfx}_p25"] is not None else 0.0
    p75_val = float(p_row[f"{pfx}_p75"]) if p_row[f"{pfx}_p75"] is not None else 0.0
    iqr_val = p75_val - p25_val
    players_column_profiles[col] = {
        "table": "players_raw",
        "temporal_class": TEMPORAL_CLASS[col],
        "dtype": "numeric",
        "null_count": null_ct,
        "null_pct": round(null_ct / total * 100, 4) if total > 0 else 0,
        "zero_count": int(p_row[f"{pfx}_zero"]),
        "zero_pct": round(int(p_row[f"{pfx}_zero"]) / total * 100, 4) if total > 0 else 0,
        "cardinality": int(p_row[f"{pfx}_distinct"]),
        "uniqueness_ratio": round(int(p_row[f"{pfx}_distinct"]) / total, 6) if total > 0 else 0,
        "mean": round(float(p_row[f"{pfx}_mean"]), 4) if p_row[f"{pfx}_mean"] is not None else None,
        "std": round(float(p_row[f"{pfx}_std"]), 4) if p_row[f"{pfx}_std"] is not None else None,
        "min": round(float(p_row[f"{pfx}_min"]), 4) if p_row[f"{pfx}_min"] is not None else None,
        "p05": round(float(p_row[f"{pfx}_p05"]), 4) if p_row[f"{pfx}_p05"] is not None else None,
        "p25": round(p25_val, 4),
        "p50": round(float(p_row[f"{pfx}_p50"]), 4) if p_row[f"{pfx}_p50"] is not None else None,
        "p75": round(p75_val, 4),
        "p95": round(float(p_row[f"{pfx}_p95"]), 4) if p_row[f"{pfx}_p95"] is not None else None,
        "max": round(float(p_row[f"{pfx}_max"]), 4) if p_row[f"{pfx}_max"] is not None else None,
        "skewness": round(float(p_row[f"{pfx}_skew"]), 4) if p_row[f"{pfx}_skew"] is not None else None,
        "kurtosis": round(float(p_row[f"{pfx}_kurt"]), 4) if p_row[f"{pfx}_kurt"] is not None else None,
        "iqr": round(iqr_val, 4),
    }
    print(f"  {col}: null={null_ct}, distinct={players_column_profiles[col]['cardinality']}")

# profile_id: identifier, abbreviated stats
pid_nonnull = int(p_row["pid_nonnull"])
pid_null = int(p_row["pid_null"])
pid_total = pid_nonnull + pid_null
players_column_profiles["profile_id"] = {
    "table": "players_raw",
    "temporal_class": TEMPORAL_CLASS["profile_id"],
    "dtype": "numeric",
    "null_count": pid_null,
    "null_pct": round(pid_null / pid_total * 100, 4) if pid_total > 0 else 0,
    "zero_count": int(p_row["pid_zero"]),
    "cardinality": int(p_row["pid_distinct"]),
    "uniqueness_ratio": round(int(p_row["pid_distinct"]) / pid_total, 6) if pid_total > 0 else 0,
    "mean": round(float(p_row["pid_mean"]), 4) if p_row["pid_mean"] is not None else None,
    "min": round(float(p_row["pid_min"]), 4) if p_row["pid_min"] is not None else None,
    "max": round(float(p_row["pid_max"]), 4) if p_row["pid_max"] is not None else None,
    "iqr": None,
}

# team: low-cardinality numeric
team_nonnull = int(p_row["team_nonnull"])
team_null = int(p_row["team_null"])
team_total = team_nonnull + team_null
players_column_profiles["team"] = {
    "table": "players_raw",
    "temporal_class": TEMPORAL_CLASS["team"],
    "dtype": "categorical",
    "null_count": team_null,
    "null_pct": round(team_null / team_total * 100, 4) if team_total > 0 else 0,
    "cardinality": int(p_row["team_distinct"]),
    "uniqueness_ratio": round(int(p_row["team_distinct"]) / team_total, 6) if team_total > 0 else 0,
    "iqr": None,
}

print(f"  profile_id: null={pid_null}, distinct={int(p_row['pid_distinct'])}")
print(f"  team: null={team_null}, distinct={int(p_row['team_distinct'])}")

# %%
# IQR outlier counts for players_raw numeric columns
players_iqr_cols = ["old_rating", "new_rating", "match_rating_diff",
                    "feudal_age_uptime", "castle_age_uptime", "imperial_age_uptime"]
# Build fences dict for players
p_fences = {}
for col in players_iqr_cols:
    p_prof = players_column_profiles[col]
    if p_prof["p25"] is not None and p_prof["p75"] is not None:
        iqr_v = p_prof["iqr"]
        p_fences[col] = (p_prof["p25"] - 1.5 * iqr_v, p_prof["p75"] + 1.5 * iqr_v)
    else:
        p_fences[col] = (None, None)

sql_players_iqr_outliers = """
SELECT
    COUNT(*) FILTER (WHERE old_rating IS NOT NULL AND (old_rating < {or_lo} OR old_rating > {or_hi}))                         AS old_rating_outliers,
    COUNT(*) FILTER (WHERE new_rating IS NOT NULL AND (new_rating < {nr_lo} OR new_rating > {nr_hi}))                         AS new_rating_outliers,
    COUNT(*) FILTER (WHERE match_rating_diff IS NOT NULL AND (match_rating_diff < {mrd_lo} OR match_rating_diff > {mrd_hi}))   AS match_rating_diff_outliers,
    COUNT(*) FILTER (WHERE feudal_age_uptime IS NOT NULL AND (feudal_age_uptime < {fau_lo} OR feudal_age_uptime > {fau_hi}))   AS feudal_age_uptime_outliers,
    COUNT(*) FILTER (WHERE castle_age_uptime IS NOT NULL AND (castle_age_uptime < {cau_lo} OR castle_age_uptime > {cau_hi}))   AS castle_age_uptime_outliers,
    COUNT(*) FILTER (WHERE imperial_age_uptime IS NOT NULL AND (imperial_age_uptime < {iau_lo} OR imperial_age_uptime > {iau_hi})) AS imperial_age_uptime_outliers
FROM players_raw
"""
sql_p_iqr_formatted = sql_players_iqr_outliers.format(
    or_lo=p_fences["old_rating"][0], or_hi=p_fences["old_rating"][1],
    nr_lo=p_fences["new_rating"][0], nr_hi=p_fences["new_rating"][1],
    mrd_lo=p_fences["match_rating_diff"][0], mrd_hi=p_fences["match_rating_diff"][1],
    fau_lo=p_fences["feudal_age_uptime"][0] if p_fences["feudal_age_uptime"][0] is not None else 0,
    fau_hi=p_fences["feudal_age_uptime"][1] if p_fences["feudal_age_uptime"][1] is not None else 999,
    cau_lo=p_fences["castle_age_uptime"][0] if p_fences["castle_age_uptime"][0] is not None else 0,
    cau_hi=p_fences["castle_age_uptime"][1] if p_fences["castle_age_uptime"][1] is not None else 999,
    iau_lo=p_fences["imperial_age_uptime"][0] if p_fences["imperial_age_uptime"][0] is not None else 0,
    iau_hi=p_fences["imperial_age_uptime"][1] if p_fences["imperial_age_uptime"][1] is not None else 999,
)
sql_queries["players_iqr_outliers"] = sql_p_iqr_formatted
p_outlier_row = db.fetch_df(sql_p_iqr_formatted).iloc[0]
for col in players_iqr_cols:
    ct = int(p_outlier_row[f"{col}_outliers"])
    p_prof = players_column_profiles[col]
    total_col = p_prof["null_count"] + (PLAYERS_TOTAL - p_prof["null_count"])
    players_column_profiles[col]["iqr_outlier_count"] = ct
    players_column_profiles[col]["iqr_outlier_pct"] = round(ct / PLAYERS_TOTAL * 100, 4)
    players_column_profiles[col]["iqr_lower_fence"] = round(p_fences[col][0], 4) if p_fences[col][0] is not None else None
    players_column_profiles[col]["iqr_upper_fence"] = round(p_fences[col][1], 4) if p_fences[col][1] is not None else None
    print(f"  {col}: {ct:,} outliers ({players_column_profiles[col]['iqr_outlier_pct']}%)")

# %%
# Categorical players_raw columns: winner, game_id, civ, opening, replay_summary_raw, filename
players_cat_cols = ["game_id", "civ", "opening", "replay_summary_raw", "filename"]
for col in players_cat_cols:
    sql_p_cat = f"""
    SELECT CAST({col} AS VARCHAR) AS val, COUNT(*) AS cnt
    FROM players_raw
    WHERE {col} IS NOT NULL
    GROUP BY {col}
    ORDER BY cnt DESC
    LIMIT 5
    """
    sql_queries[f"players_topk_{col}"] = sql_p_cat
    topk_df_p = db.fetch_df(sql_p_cat)

    sql_p_card = f"SELECT COUNT(DISTINCT {col}) AS card, COUNT(*) - COUNT({col}) AS null_ct, COUNT(*) AS total FROM players_raw"
    card_row_p = db.fetch_df(sql_p_card).iloc[0]

    p_total = int(card_row_p["total"])
    p_null_ct = int(card_row_p["null_ct"])
    p_card = int(card_row_p["card"])
    players_column_profiles[col] = {
        "table": "players_raw",
        "temporal_class": TEMPORAL_CLASS[col],
        "dtype": "categorical",
        "null_count": p_null_ct,
        "null_pct": round(p_null_ct / p_total * 100, 4) if p_total > 0 else 0,
        "cardinality": p_card,
        "uniqueness_ratio": round(p_card / p_total, 6) if p_total > 0 else 0,
        "top_5": topk_df_p.to_dict(orient="records"),
    }
    print(f"  {col}: card={p_card}, null={p_null_ct}")

# winner: BOOLEAN
sql_winner_card = "SELECT COUNT(DISTINCT winner) AS card, COUNT(*) - COUNT(winner) AS null_ct, COUNT(*) AS total FROM players_raw"
w_card_row = db.fetch_df(sql_winner_card).iloc[0]
players_column_profiles["winner"] = {
    "table": "players_raw",
    "temporal_class": TEMPORAL_CLASS["winner"],
    "dtype": "boolean",
    "null_count": int(w_card_row["null_ct"]),
    "null_pct": round(int(w_card_row["null_ct"]) / int(w_card_row["total"]) * 100, 4),
    "cardinality": int(w_card_row["card"]),
    "uniqueness_ratio": round(int(w_card_row["card"]) / int(w_card_row["total"]), 6),
    "iqr": None,
}

# %%
sql_winner = """
SELECT winner::INTEGER AS winner_int, COUNT(*) AS cnt
FROM players_raw
GROUP BY winner::INTEGER
ORDER BY winner_int
"""
sql_queries["winner_class_balance"] = sql_winner
winner_df = db.fetch_df(sql_winner)
players_column_profiles["winner"]["class_balance"] = winner_df.to_dict(orient="records")
print(f"Winner class balance:\n{winner_df}")

assert len(players_column_profiles) == 14, f"Expected 14 player columns, got {len(players_column_profiles)}"
print(f"\nplayers_raw column profiles complete: {len(players_column_profiles)} columns")

# %% [markdown]
# ## Section 3.2 -- Dataset-Level Profile

# %%
sql_dup_matches = """
SELECT game_id, COUNT(*) AS cnt
FROM matches_raw
GROUP BY game_id
HAVING COUNT(*) > 1
ORDER BY cnt DESC
LIMIT 20
"""
sql_queries["duplicate_matches"] = sql_dup_matches
dup_matches = db.fetch_df(sql_dup_matches)
print(f"Duplicate game_ids in matches_raw: {len(dup_matches)} groups")

# %%
# B2 fix: Use census-aligned COALESCE string-concatenation methodology so
# results are comparable with 01_02_04 census (which found 489 duplicate rows).
# This handles the 1,185 NULL profile_id rows correctly.
sql_dup_players = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT CAST(game_id AS VARCHAR) || '_' || COALESCE(CAST(profile_id AS VARCHAR), '__NULL__')) AS distinct_pairs,
    COUNT(*) - COUNT(DISTINCT CAST(game_id AS VARCHAR) || '_' || COALESCE(CAST(profile_id AS VARCHAR), '__NULL__')) AS duplicate_rows
FROM players_raw
"""
sql_queries["duplicate_players"] = sql_dup_players
dup_players_row = db.fetch_df(sql_dup_players).iloc[0]
dup_players_total = int(dup_players_row["total_rows"])
dup_players_distinct = int(dup_players_row["distinct_pairs"])
dup_players_dups = int(dup_players_row["duplicate_rows"])
print(f"Players duplicate detection (census-aligned methodology):")
print(f"  total_rows: {dup_players_total:,}")
print(f"  distinct_pairs: {dup_players_distinct:,}")
print(f"  duplicate_rows: {dup_players_dups:,}")
print(f"  Census reference: 489 duplicate rows")

# %%
sql_linkage = """
SELECT
    (SELECT COUNT(*) FROM players_raw p
     WHERE NOT EXISTS (SELECT 1 FROM matches_raw m WHERE m.game_id = p.game_id))
    AS players_without_match,
    (SELECT COUNT(*) FROM matches_raw m
     WHERE NOT EXISTS (SELECT 1 FROM players_raw p WHERE p.game_id = m.game_id))
    AS matches_without_players
"""
sql_queries["match_linkage"] = sql_linkage
linkage_row = db.fetch_df(sql_linkage).iloc[0]
print(f"Players without match: {int(linkage_row['players_without_match']):,}")
print(f"Matches without players: {int(linkage_row['matches_without_players']):,}")

# %%
# Memory footprint from census (duckdb_table_info function not available)
footprint_matches_est = census.get("db_memory_footprint_bytes", None)
print(f"DB memory footprint from census: {footprint_matches_est:,} bytes" if footprint_matches_est else "N/A")

# %%
# Build completeness matrix: null_pct per column for heatmap
all_profiles = {}
all_profiles.update(matches_column_profiles)
all_profiles.update(players_column_profiles)

completeness_data = []
for col, p in sorted(all_profiles.items()):
    completeness_data.append({
        "column": col,
        "table": p["table"],
        "temporal_class": p["temporal_class"],
        "null_pct": p["null_pct"],
    })
completeness_df = pd.DataFrame(completeness_data)
print(completeness_df.to_string(index=False))

# %%
profile["dataset_level"] = {
    "matches_raw_rows": MATCHES_TOTAL,
    "players_raw_rows": PLAYERS_TOTAL,
    "matches_raw_columns": 18,
    "players_raw_columns": 14,
    "duplicate_matches_groups": len(dup_matches),
    "duplicate_matches_sample": dup_matches.head(5).to_dict(orient="records") if len(dup_matches) > 0 else [],
    "duplicate_players_total": dup_players_total,
    "duplicate_players_distinct_pairs": dup_players_distinct,
    "duplicate_players_rows": dup_players_dups,
    "duplicate_players_methodology": "COALESCE string-concatenation key (census-aligned)",
    "players_without_match": int(linkage_row["players_without_match"]),
    "matches_without_players": int(linkage_row["matches_without_players"]),
    "db_memory_footprint_bytes": footprint_matches_est,
    "winner_class_balance": players_column_profiles["winner"]["class_balance"],
}

# %% [markdown]
# ## Section 3.3 -- Critical Detection

# %%
# W1 fix: Near-constant detection uses a dual criterion with a cardinality
# guard to prevent false positives on low-cardinality but information-bearing
# categoricals.
critical_findings = {
    "dead_fields": [],       # null_pct == 100
    "constant_columns": [],  # cardinality == 1
    "near_constant": [],     # Near-constant: numeric IQR=0 OR
                              # (uniqueness_ratio < 0.001 AND cardinality <= 5).
                              # Cardinality cap of 5 prevents flagging low-cardinality
                              # but information-bearing categoricals (e.g. civ=50 values,
                              # winner=2 values at 30M rows). Manual Section 3.3 threshold;
                              # cardinality cap derived from constant-column boundary
                              # (cardinality=1) plus buffer.
}

for col, p in all_profiles.items():
    if p["null_pct"] == 100.0:
        critical_findings["dead_fields"].append(col)
    if p.get("cardinality", 0) == 1:
        critical_findings["constant_columns"].append({
            "column": col,
            "table": p["table"],
            "value": p.get("top_5", [{}])[0].get("val", "N/A") if "top_5" in p else "N/A",
        })
    # Near-constant: (uniqueness_ratio < 0.001 AND cardinality <= NEAR_CONSTANT_CARDINALITY_CAP
    #                  AND null_pct < 100.0)
    # OR (IQR == 0 AND null_pct < 100.0) for numeric columns with no spread
    is_near_constant = False
    if (p.get("uniqueness_ratio", 1.0) < 0.001
            and p.get("cardinality", 0) <= NEAR_CONSTANT_CARDINALITY_CAP
            and p.get("cardinality", 0) > 1
            and p["null_pct"] < 100.0):
        is_near_constant = True
    if (p.get("iqr", None) is not None
            and p["iqr"] == 0
            and p["null_pct"] < 100.0):
        is_near_constant = True
    if is_near_constant:
        critical_findings["near_constant"].append({
            "column": col,
            "table": p["table"],
            "cardinality": p.get("cardinality", "N/A"),
            "uniqueness_ratio": p.get("uniqueness_ratio", "N/A"),
            "iqr": p.get("iqr", "N/A"),
        })

profile["critical_findings"] = critical_findings

print(f"Dead fields: {critical_findings['dead_fields']}")
print(f"Constant columns: {[c['column'] for c in critical_findings['constant_columns']]}")
print(f"Near-constant: {[c['column'] for c in critical_findings['near_constant']]}")

# %% [markdown]
# ## Section 3.4a -- Completeness Heatmap

# %%
fig, (ax_m, ax_p) = plt.subplots(1, 2, figsize=(16, 6),
                                  gridspec_kw={"width_ratios": [18, 14]})

# matches_raw columns
m_cols = [(col, p["null_pct"]) for col, p in matches_column_profiles.items()]
m_cols.sort(key=lambda x: x[1], reverse=True)
m_names = [f"{c[0]}  {TEMPORAL_CLASS.get(c[0], '')}" for c in m_cols]
m_vals = np.array([[c[1] for c in m_cols]])

im_m = ax_m.imshow(m_vals, cmap="YlOrRd", aspect="auto", vmin=0, vmax=100)
ax_m.set_xticks(range(len(m_names)))
ax_m.set_xticklabels(m_names, rotation=90, fontsize=8)
ax_m.set_yticks([])
ax_m.set_title("matches_raw NULL %", fontsize=11)
for i, v in enumerate(m_vals[0]):
    ax_m.text(i, 0, f"{v:.1f}", ha="center", va="center", fontsize=7,
              color="white" if v > 50 else "black")

# players_raw columns
p_cols = [(col, p["null_pct"]) for col, p in players_column_profiles.items()]
p_cols.sort(key=lambda x: x[1], reverse=True)
p_names = [f"{c[0]}  {TEMPORAL_CLASS.get(c[0], '')}" for c in p_cols]
p_vals = np.array([[c[1] for c in p_cols]])

im_p = ax_p.imshow(p_vals, cmap="YlOrRd", aspect="auto", vmin=0, vmax=100)
ax_p.set_xticks(range(len(p_names)))
ax_p.set_xticklabels(p_names, rotation=90, fontsize=8)
ax_p.set_yticks([])
ax_p.set_title("players_raw NULL %", fontsize=11)
for i, v in enumerate(p_vals[0]):
    ax_p.text(i, 0, f"{v:.1f}", ha="center", va="center", fontsize=7,
              color="white" if v > 50 else "black")

fig.colorbar(im_p, ax=[ax_m, ax_p], shrink=0.4, label="NULL %")
fig.suptitle("Completeness Heatmap -- aoestats (I3 temporal class annotated)", fontsize=12)
fig.tight_layout()
fig.savefig(profiling_dir / "01_03_01_completeness_heatmap.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_03_01_completeness_heatmap.png")

# %% [markdown]
# ## Section 3.4b -- QQ Plots (Normality Assessment)
#
# I7: RESERVOIR(50000) sample. SE of quantile estimates negligible at N=50K.

# %%
sql_qq_matches = f"""
SELECT
    duration / 1e9 AS duration_sec,
    avg_elo,
    team_0_elo,
    team_1_elo,
    num_players
FROM matches_raw
WHERE team_0_elo != {ELO_SENTINEL} AND team_1_elo != {ELO_SENTINEL}
USING SAMPLE RESERVOIR({SAMPLE_SIZE})
"""
sql_queries["qq_matches_sample"] = sql_qq_matches
df_qq_m = db.fetch_df(sql_qq_matches)
print(f"QQ matches sample: {len(df_qq_m)} rows")

# %%
qq_m_cols = ["duration_sec", "avg_elo", "team_0_elo", "team_1_elo"]
fig, axes = plt.subplots(1, len(qq_m_cols), figsize=(5 * len(qq_m_cols), 5))
for i, col in enumerate(qq_m_cols):
    vals = df_qq_m[col].dropna().values
    sp_stats.probplot(vals, dist="norm", plot=axes[i])
    tc_key = col.replace("_sec", "") if col == "duration_sec" else col
    tc_label = TEMPORAL_CLASS.get(tc_key, "N/A")
    axes[i].set_title(f"QQ: {col}\n({tc_label})", fontsize=10)
    axes[i].get_lines()[0].set_markersize(1)
fig.suptitle(f"QQ Plots -- matches_raw (N={len(df_qq_m):,}, RESERVOIR sample)", fontsize=12)
fig.tight_layout()
fig.savefig(profiling_dir / "01_03_01_qq_matches.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_03_01_qq_matches.png")

# %%
sql_qq_players = f"""
SELECT
    old_rating,
    new_rating,
    match_rating_diff,
    feudal_age_uptime,
    castle_age_uptime,
    imperial_age_uptime
FROM players_raw
WHERE match_rating_diff IS NOT NULL
USING SAMPLE RESERVOIR({SAMPLE_SIZE})
"""
sql_queries["qq_players_sample"] = sql_qq_players
df_qq_p = db.fetch_df(sql_qq_players)
print(f"QQ players sample: {len(df_qq_p)} rows")

# %%
# I7 note: feudal/castle/imperial_age_uptime effective N after dropna is ~13% of SAMPLE_SIZE
# (~6,500 rows) due to 87-91% NULL rate. SE of quantile estimates at N=6,500 remains
# sufficient for detecting non-normality (SE_median ~ sigma/sqrt(6500)), just with wider bands.
# W2 fix: Subplot titles show actual non-null N per panel.
qq_p_cols = ["old_rating", "new_rating", "match_rating_diff",
             "feudal_age_uptime", "castle_age_uptime", "imperial_age_uptime"]
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes_flat = axes.flatten()
for i, col in enumerate(qq_p_cols):
    vals = df_qq_p[col].dropna().values
    n_valid = len(vals)
    if n_valid > 100:
        sp_stats.probplot(vals, dist="norm", plot=axes_flat[i])
        axes_flat[i].set_title(f"QQ: {col} [N={n_valid:,}]\n({TEMPORAL_CLASS[col]})", fontsize=10)
        axes_flat[i].get_lines()[0].set_markersize(1)
    else:
        axes_flat[i].set_title(f"QQ: {col} [N={n_valid:,}]\n(insufficient non-null data)", fontsize=10)
fig.suptitle(f"QQ Plots -- players_raw (RESERVOIR sample, N_sampled={len(df_qq_p):,})", fontsize=12)
fig.tight_layout()
fig.savefig(profiling_dir / "01_03_01_qq_players.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_03_01_qq_players.png")

# %% [markdown]
# ## Section 3.4c -- Empirical CDF (Key Columns)
#
# I7: RESERVOIR(50000) sample. Columns selected as key pre-game predictors.

# %%
sql_ecdf = f"""
SELECT
    m.team_0_elo,
    m.team_1_elo,
    p.old_rating,
    p.match_rating_diff
FROM players_raw p
JOIN matches_raw m ON p.game_id = m.game_id
WHERE m.team_0_elo != {ELO_SENTINEL}
  AND m.team_1_elo != {ELO_SENTINEL}
  AND p.match_rating_diff IS NOT NULL
USING SAMPLE RESERVOIR({SAMPLE_SIZE})
"""
sql_queries["ecdf_sample"] = sql_ecdf
df_ecdf = db.fetch_df(sql_ecdf)
print(f"ECDF sample: {len(df_ecdf)} rows")

# %%
ecdf_cols = ["team_0_elo", "team_1_elo", "old_rating", "match_rating_diff"]
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes_flat = axes.flatten()
for i, col in enumerate(ecdf_cols):
    vals = np.sort(df_ecdf[col].dropna().values)
    ecdf_y = np.arange(1, len(vals) + 1) / len(vals)
    axes_flat[i].step(vals, ecdf_y, where="post", linewidth=1.0)
    axes_flat[i].set_xlabel(col, fontsize=10)
    axes_flat[i].set_ylabel("ECDF", fontsize=10)
    axes_flat[i].set_title(f"ECDF: {col}  ({TEMPORAL_CLASS[col]})", fontsize=10)
    axes_flat[i].grid(True, alpha=0.3)
    # Add p25/p50/p75 reference lines
    for q, ls in [(0.25, ":"), (0.50, "--"), (0.75, ":")]:
        axes_flat[i].axhline(y=q, color="gray", linestyle=ls, alpha=0.5)
fig.suptitle(f"Empirical CDF -- Key Pre-Game Columns (N={len(df_ecdf):,})", fontsize=12)
fig.tight_layout()
fig.savefig(profiling_dir / "01_03_01_ecdf_key_columns.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: 01_03_01_ecdf_key_columns.png")

# %% [markdown]
# ## Section 3.5 -- JSON Artifact

# %%
profile["column_profiles_matches"] = matches_column_profiles
profile["column_profiles_players"] = players_column_profiles
profile["completeness_matrix"] = completeness_data

json_path = profiling_dir / "01_03_01_systematic_profile.json"
with open(json_path, "w") as f:
    json.dump(profile, f, indent=2, default=str)
print(f"JSON artifact written: {json_path} ({json_path.stat().st_size:,} bytes)")

# %% [markdown]
# ## Section 3.6 -- Markdown Artifact

# %%
# W4 fix: Column header changed from "DuckDB Type" to "Profile Type" since
# the values are profile-level labels (numeric, categorical, boolean, timestamp),
# not actual DuckDB schema types.
md_lines = [
    "# Step 01_03_01 -- Systematic Data Profiling -- aoestats\n",
    f"**Generated:** 2026-04-16",
    f"**Dataset:** aoestats (matches_raw: {MATCHES_TOTAL:,} rows, 18 columns; "
    f"players_raw: {PLAYERS_TOTAL:,} rows, 14 columns)\n",
    "## I3 Temporal Classification Table\n",
    "| Column | Source Table | Profile Type | Temporal Class |",
    "|--------|-------------|--------------|---------------|",
]
# Sort by table then column
for col in sorted(all_profiles.keys(), key=lambda c: (all_profiles[c]["table"], c)):
    p = all_profiles[col]
    md_lines.append(f"| {col} | {p['table']} | {p['dtype']} | {p['temporal_class']} |")

md_lines.extend([
    "",
    "## Critical Findings\n",
    f"- **Dead fields (100% NULL):** {critical_findings['dead_fields'] or 'None'}",
    f"- **Constant columns (cardinality=1):** "
    + (", ".join(c["column"] for c in critical_findings["constant_columns"]) or "None"),
    f"- **Near-constant columns:** "
    + (", ".join(c["column"] for c in critical_findings["near_constant"]) or "None"),
    f"- **Near-constant detection criteria (I7):** uniqueness_ratio < 0.001 AND "
    f"cardinality <= {NEAR_CONSTANT_CARDINALITY_CAP}, OR numeric IQR == 0",
    "",
    "## Dataset-Level Summary\n",
    f"- Duplicate game_id groups in matches_raw: {len(dup_matches)}",
    f"- Duplicate rows in players_raw (census-aligned methodology): {dup_players_dups:,}",
    f"- Players without match in matches_raw: {int(linkage_row['players_without_match']):,}",
    f"- Matches without players in players_raw: {int(linkage_row['matches_without_players']):,}",
    f"- Winner class balance: {players_column_profiles['winner']['class_balance']}",
    "",
    "## Plot Index\n",
    "| # | Title | Filename | Description |",
    "|---|-------|----------|-------------|",
    "| 1 | Completeness Heatmap | `01_03_01_completeness_heatmap.png` | NULL % per column, I3 annotated |",
    "| 2 | QQ Plots (matches_raw) | `01_03_01_qq_matches.png` | duration, avg_elo, team_0/1_elo |",
    "| 3 | QQ Plots (players_raw) | `01_03_01_qq_players.png` | old/new_rating, match_rating_diff, age uptimes (N per panel in title) |",
    "| 4 | ECDF Key Columns | `01_03_01_ecdf_key_columns.png` | team_0/1_elo, old_rating, match_rating_diff |",
    "",
])

md_lines.append("## SQL Queries\n")
for name, sql in sql_queries.items():
    md_lines.append(f"### {name}\n")
    md_lines.append(f"```sql\n{sql.strip()}\n```\n")

md_path = profiling_dir / "01_03_01_systematic_profile.md"
md_path.write_text("\n".join(md_lines))
print(f"Markdown artifact written: {md_path} ({md_path.stat().st_size:,} bytes)")

# %% [markdown]
# ## Gate Verification

# %%
expected_artifacts = [
    ("01_03_01_systematic_profile.json", profiling_dir),
    ("01_03_01_completeness_heatmap.png", profiling_dir),
    ("01_03_01_qq_matches.png", profiling_dir),
    ("01_03_01_qq_players.png", profiling_dir),
    ("01_03_01_ecdf_key_columns.png", profiling_dir),
    ("01_03_01_systematic_profile.md", profiling_dir),
]
for name, parent in expected_artifacts:
    path = parent / name
    assert path.exists() and path.stat().st_size > 0, f"Missing or empty: {name}"
    print(f"OK: {name} ({path.stat().st_size:,} bytes)")

# Verify JSON structure
with open(profiling_dir / "01_03_01_systematic_profile.json") as f:
    j = json.load(f)
assert "critical_findings" in j, "JSON missing critical_findings key"
assert "column_profiles_matches" in j, "JSON missing column_profiles_matches"
assert "column_profiles_players" in j, "JSON missing column_profiles_players"
print("JSON structure validated: critical_findings, column_profiles present")

# Verify MD contains I3 table
md_text = (profiling_dir / "01_03_01_systematic_profile.md").read_text()
assert "Temporal Class" in md_text, "MD missing I3 classification table"
assert "Profile Type" in md_text, "MD should use 'Profile Type' header, not 'DuckDB Type'"
for sql_name in sql_queries:
    assert sql_name in md_text, f"SQL query '{sql_name}' not in markdown artifact"
print("Markdown validated: I3 table present, all SQL queries embedded (I6)")

print("\n=== GATE PASSED: 01_03_01 artifacts complete ===")

# %%
db.close()
