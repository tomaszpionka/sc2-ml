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
# # Step 01_03_01 -- Systematic Data Profiling
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_03 -- Systematic Data Profiling
# **Dataset:** sc2egset
# **Question:** What is the full column-level and dataset-level quality
# profile of all sc2egset raw tables?
# **Invariants applied:** #3 (I3 temporal classification on every column),
# #6 (all SQL stored verbatim), #7 (all thresholds data-derived or cited),
# #9 (profiling only, no new feature computation)
# **Predecessor:** 01_02_05 (Univariate EDA Visualizations -- complete)
# **Type:** Read-only -- no DuckDB writes
#
# **Commit:** feat/census-pass3
# **Date:** 2026-04-16
# **ROADMAP ref:** 01_03_01

# %% [markdown]
# ## Cell 1 -- Imports

# %%
import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from rts_predict.common.notebook_utils import (
    get_notebook_db,
    get_reports_dir,
    setup_notebook_logging,
)

matplotlib.use("Agg")
logger = setup_notebook_logging()

# %% [markdown]
# ## Cell 2 -- DuckDB Connection

# %%
conn = get_notebook_db("sc2", "sc2egset")
print("DuckDB connection opened (read-only).")

# %% [markdown]
# ## Cell 3 -- Census Load and Runtime Constants (Invariant #7)

# %%
reports_dir = get_reports_dir("sc2", "sc2egset")
census_json_path = (
    reports_dir / "artifacts" / "01_exploration" / "02_eda"
    / "01_02_04_univariate_census.json"
)
with open(census_json_path) as f:
    census = json.load(f)

# --- Runtime constants from census (Invariant #7) ---
RP_TOTAL_ROWS = census["null_census"]["replay_players_raw"]["total_rows"]
print(f"replay_players_raw total rows: {RP_TOTAL_ROWS}")

RM_TOTAL_ROWS = census["null_census"]["replays_meta_raw_filename"]["total_rows"]
print(f"replays_meta_raw total rows: {RM_TOTAL_ROWS}")

MMR_ZERO_COUNT = census["zero_counts"]["replay_players_raw"]["MMR_zero"]
MMR_ZERO_PCT = round(100.0 * MMR_ZERO_COUNT / RP_TOTAL_ROWS, 2)
print(f"MMR zero sentinel: {MMR_ZERO_COUNT} rows ({MMR_ZERO_PCT}%)")

SQ_SENTINEL_COUNT = census["zero_counts"]["replay_players_raw"]["SQ_sentinel"]
INT32_MIN = int(np.iinfo(np.int32).min)
print(f"SQ sentinel (INT32_MIN={INT32_MIN}): {SQ_SENTINEL_COUNT} rows")

APM_ZERO_COUNT = census["zero_counts"]["replay_players_raw"]["APM_zero"]
APM_ZERO_PCT = round(100.0 * APM_ZERO_COUNT / RP_TOTAL_ROWS, 4)
print(f"APM zero sentinel: {APM_ZERO_COUNT} rows ({APM_ZERO_PCT}%)")

HANDICAP_ZERO_COUNT = census["zero_counts"]["replay_players_raw"]["handicap_zero"]
HANDICAP_ZERO_PCT = round(100.0 * HANDICAP_ZERO_COUNT / RP_TOTAL_ROWS, 4)
print(f"handicap zero sentinel: {HANDICAP_ZERO_COUNT} rows ({HANDICAP_ZERO_PCT}%)")

result_dist = {r["result"]: r["cnt"] for r in census["result_distribution"]}
N_WIN = result_dist["Win"]
N_LOSS = result_dist["Loss"]
N_UNDECIDED = result_dist.get("Undecided", 0)
N_TIE = result_dist.get("Tie", 0)
N_WINLOSS = N_WIN + N_LOSS
print(f"Win/Loss rows: {N_WINLOSS} (excluding {N_UNDECIDED} Undecided, {N_TIE} Tie)")

# I3 temporal classification from census field_classification.
# NOTE: elapsed_game_loops is classified as 'in_game' in the census JSON,
# but was retroactively reclassified as POST-GAME on 2026-04-15.
# This notebook overrides that classification for elapsed_game_loops.
FIELD_CLASSIFICATION = census["field_classification"]
print("Field classification keys:", list(FIELD_CLASSIFICATION.keys()))

# Output directories
artifact_dir = (
    reports_dir / "artifacts" / "01_exploration" / "03_profiling"
)
artifact_dir.mkdir(parents=True, exist_ok=True)
plots_dir = artifact_dir / "plots"
plots_dir.mkdir(parents=True, exist_ok=True)
print(f"Artifact dir: {artifact_dir}")
print(f"Plots dir: {plots_dir}")

# %% [markdown]
# ## Cell 4 -- SQL Queries Dict (Invariant #6)

# %%
# All SQL queries that produce reported results are stored here verbatim (I6).
sql_queries: dict = {}

# %% [markdown]
# ## Cell 5 -- replay_players_raw Numeric Profile

# %%
sql_queries["rp_numeric_profile"] = f"""
WITH base AS (
    SELECT *
    FROM replay_players_raw
)
SELECT
    'MMR' AS column_name,
    COUNT(*) AS n_rows,
    COUNT(*) - COUNT(MMR) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(MMR)) / COUNT(*), 4) AS null_pct,
    SUM(CASE WHEN MMR = 0 THEN 1 ELSE 0 END) AS zero_count,
    ROUND(100.0 * SUM(CASE WHEN MMR = 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS zero_pct,
    COUNT(DISTINCT MMR) AS cardinality,
    ROUND(COUNT(DISTINCT MMR)::DOUBLE / COUNT(*), 6) AS uniqueness_ratio,
    MIN(MMR) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY MMR) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY MMR) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY MMR) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY MMR) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY MMR) AS p95,
    MAX(MMR) AS max_val,
    ROUND(AVG(MMR), 4) AS mean_val,
    ROUND(STDDEV(MMR), 4) AS std_val,
    ROUND(SKEWNESS(MMR), 4) AS skewness,
    ROUND(KURTOSIS(MMR), 4) AS kurtosis
FROM base

UNION ALL

SELECT
    'MMR_rated_only' AS column_name,
    SUM(CASE WHEN MMR > 0 THEN 1 ELSE 0 END) AS n_rows,
    0 AS null_count,
    0.0 AS null_pct,
    0 AS zero_count,
    0.0 AS zero_pct,
    COUNT(DISTINCT CASE WHEN MMR > 0 THEN MMR END) AS cardinality,
    ROUND(COUNT(DISTINCT CASE WHEN MMR > 0 THEN MMR END)::DOUBLE
          / NULLIF(SUM(CASE WHEN MMR > 0 THEN 1 ELSE 0 END), 0), 6) AS uniqueness_ratio,
    MIN(CASE WHEN MMR > 0 THEN MMR END) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY MMR) FILTER (WHERE MMR > 0) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY MMR) FILTER (WHERE MMR > 0) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY MMR) FILTER (WHERE MMR > 0) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY MMR) FILTER (WHERE MMR > 0) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY MMR) FILTER (WHERE MMR > 0) AS p95,
    MAX(CASE WHEN MMR > 0 THEN MMR END) AS max_val,
    ROUND(AVG(CASE WHEN MMR > 0 THEN MMR END), 4) AS mean_val,
    ROUND(STDDEV(CASE WHEN MMR > 0 THEN MMR END), 4) AS std_val,
    ROUND(SKEWNESS(MMR) FILTER (WHERE MMR > 0), 4) AS skewness,
    ROUND(KURTOSIS(MMR) FILTER (WHERE MMR > 0), 4) AS kurtosis
FROM base

UNION ALL

SELECT
    'APM' AS column_name,
    COUNT(*) AS n_rows,
    COUNT(*) - COUNT(APM) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(APM)) / COUNT(*), 4) AS null_pct,
    SUM(CASE WHEN APM = 0 THEN 1 ELSE 0 END) AS zero_count,
    ROUND(100.0 * SUM(CASE WHEN APM = 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS zero_pct,
    COUNT(DISTINCT APM) AS cardinality,
    ROUND(COUNT(DISTINCT APM)::DOUBLE / COUNT(*), 6) AS uniqueness_ratio,
    MIN(APM) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY APM) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY APM) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY APM) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY APM) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY APM) AS p95,
    MAX(APM) AS max_val,
    ROUND(AVG(APM), 4) AS mean_val,
    ROUND(STDDEV(APM), 4) AS std_val,
    ROUND(SKEWNESS(APM), 4) AS skewness,
    ROUND(KURTOSIS(APM), 4) AS kurtosis
FROM base

UNION ALL

SELECT
    'SQ' AS column_name,
    COUNT(*) AS n_rows,
    COUNT(*) - COUNT(SQ) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(SQ)) / COUNT(*), 4) AS null_pct,
    SUM(CASE WHEN SQ = 0 THEN 1 ELSE 0 END) AS zero_count,
    ROUND(100.0 * SUM(CASE WHEN SQ = 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS zero_pct,
    COUNT(DISTINCT SQ) AS cardinality,
    ROUND(COUNT(DISTINCT SQ)::DOUBLE / COUNT(*), 6) AS uniqueness_ratio,
    MIN(SQ) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY SQ) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY SQ) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY SQ) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY SQ) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY SQ) AS p95,
    MAX(SQ) AS max_val,
    ROUND(AVG(SQ), 4) AS mean_val,
    ROUND(STDDEV(SQ), 4) AS std_val,
    ROUND(SKEWNESS(SQ), 4) AS skewness,
    ROUND(KURTOSIS(SQ), 4) AS kurtosis
FROM base

UNION ALL

SELECT
    'SQ_no_sentinel' AS column_name,
    SUM(CASE WHEN SQ > {INT32_MIN} THEN 1 ELSE 0 END) AS n_rows,
    0 AS null_count,
    0.0 AS null_pct,
    SUM(CASE WHEN SQ = 0 AND SQ > {INT32_MIN} THEN 1 ELSE 0 END) AS zero_count,
    0.0 AS zero_pct,
    COUNT(DISTINCT CASE WHEN SQ > {INT32_MIN} THEN SQ END) AS cardinality,
    ROUND(COUNT(DISTINCT CASE WHEN SQ > {INT32_MIN} THEN SQ END)::DOUBLE
          / NULLIF(SUM(CASE WHEN SQ > {INT32_MIN} THEN 1 ELSE 0 END), 0), 6) AS uniqueness_ratio,
    MIN(CASE WHEN SQ > {INT32_MIN} THEN SQ END) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > {INT32_MIN}) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > {INT32_MIN}) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > {INT32_MIN}) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > {INT32_MIN}) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > {INT32_MIN}) AS p95,
    MAX(CASE WHEN SQ > {INT32_MIN} THEN SQ END) AS max_val,
    ROUND(AVG(CASE WHEN SQ > {INT32_MIN} THEN SQ END), 4) AS mean_val,
    ROUND(STDDEV(CASE WHEN SQ > {INT32_MIN} THEN SQ END), 4) AS std_val,
    ROUND(SKEWNESS(SQ) FILTER (WHERE SQ > {INT32_MIN}), 4) AS skewness,
    ROUND(KURTOSIS(SQ) FILTER (WHERE SQ > {INT32_MIN}), 4) AS kurtosis
FROM base

UNION ALL

SELECT
    'supplyCappedPercent' AS column_name,
    COUNT(*) AS n_rows,
    COUNT(*) - COUNT(supplyCappedPercent) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(supplyCappedPercent)) / COUNT(*), 4) AS null_pct,
    SUM(CASE WHEN supplyCappedPercent = 0 THEN 1 ELSE 0 END) AS zero_count,
    ROUND(100.0 * SUM(CASE WHEN supplyCappedPercent = 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS zero_pct,
    COUNT(DISTINCT supplyCappedPercent) AS cardinality,
    ROUND(COUNT(DISTINCT supplyCappedPercent)::DOUBLE / COUNT(*), 6) AS uniqueness_ratio,
    MIN(supplyCappedPercent) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY supplyCappedPercent) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY supplyCappedPercent) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY supplyCappedPercent) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY supplyCappedPercent) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY supplyCappedPercent) AS p95,
    MAX(supplyCappedPercent) AS max_val,
    ROUND(AVG(supplyCappedPercent), 4) AS mean_val,
    ROUND(STDDEV(supplyCappedPercent), 4) AS std_val,
    ROUND(SKEWNESS(supplyCappedPercent), 4) AS skewness,
    ROUND(KURTOSIS(supplyCappedPercent), 4) AS kurtosis
FROM base

UNION ALL

SELECT
    'handicap' AS column_name,
    COUNT(*) AS n_rows,
    COUNT(*) - COUNT(handicap) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(handicap)) / COUNT(*), 4) AS null_pct,
    SUM(CASE WHEN handicap = 0 THEN 1 ELSE 0 END) AS zero_count,
    ROUND(100.0 * SUM(CASE WHEN handicap = 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS zero_pct,
    COUNT(DISTINCT handicap) AS cardinality,
    ROUND(COUNT(DISTINCT handicap)::DOUBLE / COUNT(*), 6) AS uniqueness_ratio,
    MIN(handicap) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY handicap) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY handicap) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY handicap) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY handicap) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY handicap) AS p95,
    MAX(handicap) AS max_val,
    ROUND(AVG(handicap), 4) AS mean_val,
    ROUND(STDDEV(handicap), 4) AS std_val,
    ROUND(SKEWNESS(handicap), 4) AS skewness,
    ROUND(KURTOSIS(handicap), 4) AS kurtosis
FROM base
"""

df_rp_numeric = conn.fetch_df(sql_queries["rp_numeric_profile"])
print(f"Numeric profile rows: {len(df_rp_numeric)}")
print(df_rp_numeric[["column_name", "n_rows", "null_pct", "zero_pct",
                       "cardinality", "mean_val", "skewness"]].to_string())

# %% [markdown]
# ## Cell 6 -- replay_players_raw Null/Cardinality Profile (All Columns)

# %%
# W-02: UNPIVOT fallback is included in sql_queries dict.
# Try UNPIVOT first; if it fails due to mixed-type coercion, use the UNION ALL fallback.
sql_queries["rp_null_cardinality"] = """
SELECT
    column_name,
    COUNT(*) - COUNT(col_val) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(col_val)) / COUNT(*), 4) AS null_pct,
    COUNT(DISTINCT col_val) AS cardinality,
    ROUND(COUNT(DISTINCT col_val)::DOUBLE / COUNT(*), 6) AS uniqueness_ratio
FROM (
    UNPIVOT replay_players_raw
    ON COLUMNS(*)
    INTO NAME column_name VALUE col_val
)
GROUP BY column_name
ORDER BY column_name
"""

# W-02: Fallback SQL if UNPIVOT fails due to mixed-type coercion issues.
# Per-column UNION ALL is more explicit and matches the census approach.
sql_queries["rp_null_cardinality_fallback"] = """
SELECT 'filename' AS col, COUNT(*) AS total, COUNT(filename) AS non_null,
       COUNT(DISTINCT filename) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'toon_id', COUNT(*), COUNT(toon_id), COUNT(DISTINCT toon_id) FROM replay_players_raw
UNION ALL
SELECT 'nickname', COUNT(*), COUNT(nickname), COUNT(DISTINCT nickname) FROM replay_players_raw
UNION ALL
SELECT 'playerID', COUNT(*), COUNT(playerID), COUNT(DISTINCT playerID) FROM replay_players_raw
UNION ALL
SELECT 'userID', COUNT(*), COUNT(userID), COUNT(DISTINCT userID) FROM replay_players_raw
UNION ALL
SELECT 'isInClan', COUNT(*), COUNT(isInClan), COUNT(DISTINCT isInClan) FROM replay_players_raw
UNION ALL
SELECT 'clanTag', COUNT(*), COUNT(clanTag), COUNT(DISTINCT clanTag) FROM replay_players_raw
UNION ALL
SELECT 'MMR', COUNT(*), COUNT(MMR), COUNT(DISTINCT MMR) FROM replay_players_raw
UNION ALL
SELECT 'race', COUNT(*), COUNT(race), COUNT(DISTINCT race) FROM replay_players_raw
UNION ALL
SELECT 'selectedRace', COUNT(*), COUNT(selectedRace),
       COUNT(DISTINCT selectedRace) FROM replay_players_raw
UNION ALL
SELECT 'handicap', COUNT(*), COUNT(handicap), COUNT(DISTINCT handicap) FROM replay_players_raw
UNION ALL
SELECT 'region', COUNT(*), COUNT(region), COUNT(DISTINCT region) FROM replay_players_raw
UNION ALL
SELECT 'realm', COUNT(*), COUNT(realm), COUNT(DISTINCT realm) FROM replay_players_raw
UNION ALL
SELECT 'highestLeague', COUNT(*), COUNT(highestLeague),
       COUNT(DISTINCT highestLeague) FROM replay_players_raw
UNION ALL
SELECT 'result', COUNT(*), COUNT(result), COUNT(DISTINCT result) FROM replay_players_raw
UNION ALL
SELECT 'APM', COUNT(*), COUNT(APM), COUNT(DISTINCT APM) FROM replay_players_raw
UNION ALL
SELECT 'SQ', COUNT(*), COUNT(SQ), COUNT(DISTINCT SQ) FROM replay_players_raw
UNION ALL
SELECT 'supplyCappedPercent', COUNT(*), COUNT(supplyCappedPercent),
       COUNT(DISTINCT supplyCappedPercent) FROM replay_players_raw
UNION ALL
SELECT 'startDir', COUNT(*), COUNT(startDir), COUNT(DISTINCT startDir) FROM replay_players_raw
UNION ALL
SELECT 'startLocX', COUNT(*), COUNT(startLocX), COUNT(DISTINCT startLocX) FROM replay_players_raw
UNION ALL
SELECT 'startLocY', COUNT(*), COUNT(startLocY), COUNT(DISTINCT startLocY) FROM replay_players_raw
UNION ALL
SELECT 'color_a', COUNT(*), COUNT(color_a), COUNT(DISTINCT color_a) FROM replay_players_raw
UNION ALL
SELECT 'color_b', COUNT(*), COUNT(color_b), COUNT(DISTINCT color_b) FROM replay_players_raw
UNION ALL
SELECT 'color_g', COUNT(*), COUNT(color_g), COUNT(DISTINCT color_g) FROM replay_players_raw
UNION ALL
SELECT 'color_r', COUNT(*), COUNT(color_r), COUNT(DISTINCT color_r) FROM replay_players_raw
"""

try:
    df_rp_null_card = conn.fetch_df(sql_queries["rp_null_cardinality"])
    print(f"UNPIVOT succeeded: {len(df_rp_null_card)} columns profiled")
except Exception as e:
    print(f"UNPIVOT failed ({e}), using UNION ALL fallback.")
    df_rp_null_card_fb = conn.fetch_df(sql_queries["rp_null_cardinality_fallback"])
    # Normalize fallback to same schema
    df_rp_null_card = pd.DataFrame({
        "column_name": df_rp_null_card_fb["col"],
        "null_count": df_rp_null_card_fb["total"] - df_rp_null_card_fb["non_null"],
        "null_pct": round(
            100.0 * (df_rp_null_card_fb["total"] - df_rp_null_card_fb["non_null"])
            / df_rp_null_card_fb["total"], 4
        ),
        "cardinality": df_rp_null_card_fb["cardinality"],
        "uniqueness_ratio": round(
            df_rp_null_card_fb["cardinality"] / df_rp_null_card_fb["total"], 6
        ),
    })
    print(f"Fallback succeeded: {len(df_rp_null_card)} columns profiled")

print(df_rp_null_card.to_string())

# %% [markdown]
# ## Cell 7 -- replay_players_raw Categorical Top-k (k=5)

# %%
CATEGORICAL_COLS_RP = [
    "result", "race", "selectedRace", "highestLeague",
    "region", "realm", "isInClan", "clanTag",
]

sql_queries["rp_topk"] = {}
df_rp_topk: dict = {}
for col in CATEGORICAL_COLS_RP:
    sql_queries["rp_topk"][col] = f"""
    SELECT
        CAST({col} AS VARCHAR) AS value,
        COUNT(*) AS cnt,
        ROUND(100.0 * COUNT(*) / {RP_TOTAL_ROWS}, 4) AS pct
    FROM replay_players_raw
    GROUP BY {col}
    ORDER BY cnt DESC
    LIMIT 5
    """
    df_rp_topk[col] = conn.fetch_df(sql_queries["rp_topk"][col])
    print(f"\nTop-5 for {col}:")
    print(df_rp_topk[col].to_string())

# %% [markdown]
# ## Cell 8 -- replay_players_raw IQR Outlier Counts

# %%
sql_queries["rp_iqr_outliers"] = f"""
WITH stats AS (
    SELECT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY MMR) AS mmr_q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY MMR) AS mmr_q3,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY APM) AS apm_q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY APM) AS apm_q3,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > {INT32_MIN}) AS sq_q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > {INT32_MIN}) AS sq_q3,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY supplyCappedPercent) AS sc_q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY supplyCappedPercent) AS sc_q3
    FROM replay_players_raw
)
SELECT
    SUM(CASE WHEN MMR < (s.mmr_q1 - 1.5 * (s.mmr_q3 - s.mmr_q1))
              OR MMR > (s.mmr_q3 + 1.5 * (s.mmr_q3 - s.mmr_q1))
         THEN 1 ELSE 0 END) AS mmr_iqr_outliers,
    SUM(CASE WHEN APM < (s.apm_q1 - 1.5 * (s.apm_q3 - s.apm_q1))
              OR APM > (s.apm_q3 + 1.5 * (s.apm_q3 - s.apm_q1))
         THEN 1 ELSE 0 END) AS apm_iqr_outliers,
    SUM(CASE WHEN SQ > {INT32_MIN}
              AND (SQ < (s.sq_q1 - 1.5 * (s.sq_q3 - s.sq_q1))
                   OR SQ > (s.sq_q3 + 1.5 * (s.sq_q3 - s.sq_q1)))
         THEN 1 ELSE 0 END) AS sq_iqr_outliers,
    SUM(CASE WHEN supplyCappedPercent < (s.sc_q1 - 1.5 * (s.sc_q3 - s.sc_q1))
              OR supplyCappedPercent > (s.sc_q3 + 1.5 * (s.sc_q3 - s.sc_q1))
         THEN 1 ELSE 0 END) AS sc_iqr_outliers
FROM replay_players_raw, stats s
"""

# W-03 fix: IQR for MMR-all is degenerate (Q1=Q3=0 -> IQR=0 -> every MMR>0 is an "outlier").
# The rated-only variant provides a meaningful IQR outlier count.
# IQR fence at 1.5*IQR per Tukey (1977) -- I7 compliance.
sql_queries["rp_iqr_outliers_mmr_rated"] = """
WITH rated AS (SELECT MMR FROM replay_players_raw WHERE MMR > 0),
     fences AS (
       SELECT
         PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY MMR) AS p25,
         PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY MMR) AS p75
       FROM rated
     ),
     fences_scalar AS (
       SELECT p25, p75, p75 - p25 AS iqr,
              p25 - 1.5 * (p75 - p25) AS lower_fence,
              p75 + 1.5 * (p75 - p25) AS upper_fence
       FROM fences
     )
SELECT
  f.p25, f.p75, f.iqr,
  COUNT(*) FILTER (WHERE r.MMR < f.lower_fence OR r.MMR > f.upper_fence)
      AS mmr_iqr_outliers_rated
FROM rated r CROSS JOIN fences_scalar f
GROUP BY f.p25, f.p75, f.iqr
"""

df_rp_iqr = conn.fetch_df(sql_queries["rp_iqr_outliers"])
df_rp_iqr_mmr_rated = conn.fetch_df(sql_queries["rp_iqr_outliers_mmr_rated"])
print("IQR outlier counts (all rows):")
print(df_rp_iqr.to_string())
print("\nMMR IQR outliers (rated-only, MMR>0):")
print(df_rp_iqr_mmr_rated.to_string())
print("\nNote: MMR IQR outlier count for all rows is degenerate (IQR=0 since Q1=Q3=0).")
print("Every MMR>0 row (rated players) is flagged as 'outlier' in the all-rows count.")

# %% [markdown]
# ## Cell 9 -- replays_meta_raw STRUCT-Flat Profile

# %%
sql_queries["rm_struct_profile"] = """
SELECT
    COUNT(*) AS n_rows,
    -- elapsed_game_loops (POST-GAME, reclassified 2026-04-15)
    COUNT(*) - COUNT(header.elapsedGameLoops) AS elapsed_game_loops_null,
    COUNT(DISTINCT header.elapsedGameLoops) AS elapsed_game_loops_cardinality,
    MIN(header.elapsedGameLoops) AS elapsed_game_loops_min,
    MAX(header.elapsedGameLoops) AS elapsed_game_loops_max,
    ROUND(AVG(header.elapsedGameLoops), 4) AS elapsed_game_loops_mean,
    ROUND(STDDEV(header.elapsedGameLoops), 4) AS elapsed_game_loops_std,
    ROUND(SKEWNESS(header.elapsedGameLoops), 4) AS elapsed_game_loops_skew,
    ROUND(KURTOSIS(header.elapsedGameLoops), 4) AS elapsed_game_loops_kurt,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY header.elapsedGameLoops)
        AS elapsed_game_loops_p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY header.elapsedGameLoops)
        AS elapsed_game_loops_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY header.elapsedGameLoops)
        AS elapsed_game_loops_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY header.elapsedGameLoops)
        AS elapsed_game_loops_p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY header.elapsedGameLoops)
        AS elapsed_game_loops_p95,
    -- map_name
    COUNT(*) - COUNT(metadata.mapName) AS map_name_null,
    COUNT(DISTINCT metadata.mapName) AS map_name_cardinality,
    -- max_players
    COUNT(*) - COUNT(initData.gameDescription.maxPlayers) AS max_players_null,
    COUNT(DISTINCT initData.gameDescription.maxPlayers) AS max_players_cardinality,
    -- game_speed (CONSTANT expected)
    COUNT(DISTINCT details.gameSpeed) AS game_speed_cardinality,
    -- game_speed_init (CONSTANT expected)
    COUNT(DISTINCT initData.gameDescription.gameSpeed) AS game_speed_init_cardinality,
    -- map_size
    COUNT(DISTINCT initData.gameDescription.mapSizeX) AS map_size_x_cardinality,
    COUNT(DISTINCT initData.gameDescription.mapSizeY) AS map_size_y_cardinality,
    -- error booleans (CONSTANT expected: all FALSE)
    COUNT(DISTINCT gameEventsErr) AS gameEventsErr_cardinality,
    COUNT(DISTINCT messageEventsErr) AS messageEventsErr_cardinality,
    COUNT(DISTINCT trackerEvtsErr) AS trackerEvtsErr_cardinality,
    -- version / build
    COUNT(DISTINCT metadata.gameVersion) AS game_version_meta_cardinality,
    COUNT(DISTINCT header."version") AS game_version_header_cardinality,
    COUNT(DISTINCT metadata.baseBuild) AS base_build_cardinality,
    COUNT(DISTINCT metadata.dataBuild) AS data_build_cardinality,
    -- blizzard map flags
    COUNT(DISTINCT details.isBlizzardMap) AS is_blizzard_map_cardinality,
    COUNT(DISTINCT initData.gameDescription.isBlizzardMap) AS is_blizzard_map_init_cardinality,
    -- time_utc
    COUNT(*) - COUNT(details.timeUTC) AS time_utc_null,
    COUNT(DISTINCT details.timeUTC) AS time_utc_cardinality
FROM replays_meta_raw
"""

df_rm = conn.fetch_df(sql_queries["rm_struct_profile"])
print(f"replays_meta_raw struct-flat profile rows: {len(df_rm)}")
print(df_rm.T.to_string())

# %% [markdown]
# ## Cell 10 -- replays_meta_raw IQR Outliers for elapsed_game_loops

# %%
sql_queries["rm_egl_iqr_outliers"] = """
WITH stats AS (
    SELECT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY header.elapsedGameLoops) AS q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY header.elapsedGameLoops) AS q3
    FROM replays_meta_raw
)
SELECT
    q1,
    q3,
    q3 - q1 AS iqr,
    q1 - 1.5 * (q3 - q1) AS lower_fence,
    q3 + 1.5 * (q3 - q1) AS upper_fence,
    SUM(CASE WHEN header.elapsedGameLoops < (s.q1 - 1.5 * (s.q3 - s.q1))
              OR header.elapsedGameLoops > (s.q3 + 1.5 * (s.q3 - s.q1))
         THEN 1 ELSE 0 END) AS iqr_outlier_count
FROM replays_meta_raw, stats s
GROUP BY q1, q3
"""

df_rm_egl_iqr = conn.fetch_df(sql_queries["rm_egl_iqr_outliers"])
print("elapsed_game_loops IQR outliers:")
print(df_rm_egl_iqr.to_string())

# %% [markdown]
# ## Cell 11 -- map_aliases_raw Profile

# %%
sql_queries["ma_profile"] = """
SELECT
    COUNT(*) AS n_rows,
    COUNT(*) - COUNT(tournament) AS tournament_null,
    COUNT(*) - COUNT(foreign_name) AS foreign_name_null,
    COUNT(*) - COUNT(english_name) AS english_name_null,
    COUNT(*) - COUNT(filename) AS filename_null,
    COUNT(DISTINCT tournament) AS tournament_cardinality,
    COUNT(DISTINCT foreign_name) AS foreign_name_cardinality,
    COUNT(DISTINCT english_name) AS english_name_cardinality,
    COUNT(DISTINCT filename) AS filename_cardinality
FROM map_aliases_raw
"""

sql_queries["ma_topk_tournament"] = """
SELECT
    tournament,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM map_aliases_raw), 4) AS pct
FROM map_aliases_raw
GROUP BY tournament
ORDER BY cnt DESC
LIMIT 5
"""

df_ma = conn.fetch_df(sql_queries["ma_profile"])
df_ma_topk = conn.fetch_df(sql_queries["ma_topk_tournament"])
print("map_aliases_raw profile:")
print(df_ma.T.to_string())
print("\nTop-5 tournaments:")
print(df_ma_topk.to_string())

# %% [markdown]
# ## Cell 12 -- Dataset-Level: Row Counts

# %%
sql_queries["row_counts"] = """
SELECT 'replay_players_raw' AS table_name, COUNT(*) AS n_rows FROM replay_players_raw
UNION ALL
SELECT 'replays_meta_raw', COUNT(*) FROM replays_meta_raw
UNION ALL
SELECT 'map_aliases_raw', COUNT(*) FROM map_aliases_raw
"""

df_row_counts = conn.fetch_df(sql_queries["row_counts"])
print("Row counts per table:")
print(df_row_counts.to_string())

# %% [markdown]
# ## Cell 13 -- Dataset-Level: Duplicate Detection

# %%
# W-04: (filename, playerID) matches census 01_02_04 methodology.
# filename encodes the replay hash (maps to replayId); playerID is the per-replay slot index.
# toon_id is global Battle.net ID and is NOT the per-replay duplicate detection key.
sql_queries["rp_duplicates"] = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT (filename, playerID)) AS distinct_pairs,
    COUNT(*) - COUNT(DISTINCT (filename, playerID)) AS duplicate_rows
FROM replay_players_raw
-- W-04: (filename, playerID) = natural key.
-- filename contains the replay hash; playerID is per-replay slot index (0/1).
-- toon_id is global Battle.net ID; not the correct duplication detection key here.
"""

df_dupes = conn.fetch_df(sql_queries["rp_duplicates"])
print("Duplicate detection (replayId, playerID):")
print(df_dupes.to_string())

# %% [markdown]
# ## Cell 14 -- Dataset-Level: Class Balance

# %%
sql_queries["class_balance"] = """
SELECT
    result,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS pct
FROM replay_players_raw
GROUP BY result
ORDER BY cnt DESC
"""

df_class_balance = conn.fetch_df(sql_queries["class_balance"])
print("Class balance:")
print(df_class_balance.to_string())

# %% [markdown]
# ## Cell 15 -- Dataset-Level: Cross-Table Linkage

# %%
sql_queries["cross_table_linkage"] = """
WITH rp_replays AS (
    SELECT DISTINCT
        regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id
    FROM replay_players_raw
),
rm_replays AS (
    SELECT DISTINCT
        regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id
    FROM replays_meta_raw
)
SELECT
    (SELECT COUNT(*) FROM rp_replays) AS rp_distinct_replays,
    (SELECT COUNT(*) FROM rm_replays) AS rm_distinct_replays,
    (SELECT COUNT(*) FROM rp_replays
     WHERE replay_id NOT IN (SELECT replay_id FROM rm_replays)) AS rp_orphans,
    (SELECT COUNT(*) FROM rm_replays
     WHERE replay_id NOT IN (SELECT replay_id FROM rp_replays)) AS rm_orphans
"""

df_linkage = conn.fetch_df(sql_queries["cross_table_linkage"])
print("Cross-table linkage (replayId via regex):")
print(df_linkage.to_string())

# %% [markdown]
# ## Cell 16 -- Dataset-Level: Memory Footprint

# %%
sql_queries["memory_footprint"] = """
SELECT
    database_name,
    table_name,
    estimated_size,
    column_count,
    index_count
FROM duckdb_tables()
WHERE table_name IN ('replay_players_raw', 'replays_meta_raw', 'map_aliases_raw')
ORDER BY table_name
"""

df_memory = conn.fetch_df(sql_queries["memory_footprint"])
print("Memory footprint (estimated):")
print(df_memory.to_string())

# %% [markdown]
# ## Cell 17 -- Build All Profiles

# %%
# Assemble column profiles from T03 results
rp_numeric_cols = df_rp_numeric.set_index("column_name").to_dict(orient="index")
rp_null_card_cols = df_rp_null_card.set_index("column_name").to_dict(orient="index")

# Merge numeric stats into null/card where columns overlap
all_profiles: dict = {}
for col, stats_row in rp_null_card_cols.items():
    all_profiles[col] = {
        "null_count": int(stats_row.get("null_count", 0)),
        "null_pct": float(stats_row.get("null_pct", 0.0)),
        "cardinality": int(stats_row.get("cardinality", 0)),
        "uniqueness_ratio": float(stats_row.get("uniqueness_ratio", 0.0)),
        "numeric": col in rp_numeric_cols,
    }
    if col in rp_numeric_cols:
        nr = rp_numeric_cols[col]
        all_profiles[col].update({
            "min_val": nr.get("min_val"),
            "max_val": nr.get("max_val"),
            "mean_val": nr.get("mean_val"),
            "std_val": nr.get("std_val"),
            "skewness": nr.get("skewness"),
            "kurtosis": nr.get("kurtosis"),
            "p25": nr.get("p25"),
            "p75": nr.get("p75"),
            "iqr": float(nr.get("p75", 0) - nr.get("p25", 0))
            if nr.get("p75") is not None and nr.get("p25") is not None else None,
        })

# Also add replays_meta_raw struct-flat fields
rm_row = df_rm.iloc[0]
rm_struct_fields = {
    "elapsed_game_loops": {
        "null_pct": float(rm_row.get("elapsed_game_loops_null", 0)),
        "cardinality": int(rm_row.get("elapsed_game_loops_cardinality", 0)),
        "uniqueness_ratio": float(rm_row.get("elapsed_game_loops_cardinality", 0))
            / float(rm_row.get("n_rows", 1)),
        "numeric": True,
        "iqr": float(
            df_rm_egl_iqr.iloc[0]["q3"] - df_rm_egl_iqr.iloc[0]["q1"]
        ) if len(df_rm_egl_iqr) > 0 else 0.0,
    },
    "game_speed": {
        "null_pct": 0.0,
        "cardinality": int(rm_row.get("game_speed_cardinality", 0)),
        "uniqueness_ratio": float(rm_row.get("game_speed_cardinality", 0))
            / float(rm_row.get("n_rows", 1)),
        "numeric": False,
    },
    "game_speed_init": {
        "null_pct": 0.0,
        "cardinality": int(rm_row.get("game_speed_init_cardinality", 0)),
        "uniqueness_ratio": float(rm_row.get("game_speed_init_cardinality", 0))
            / float(rm_row.get("n_rows", 1)),
        "numeric": False,
    },
    "gameEventsErr": {
        "null_pct": 0.0,
        "cardinality": int(rm_row.get("gameEventsErr_cardinality", 0)),
        "uniqueness_ratio": float(rm_row.get("gameEventsErr_cardinality", 0))
            / float(rm_row.get("n_rows", 1)),
        "numeric": False,
    },
    "messageEventsErr": {
        "null_pct": 0.0,
        "cardinality": int(rm_row.get("messageEventsErr_cardinality", 0)),
        "uniqueness_ratio": float(rm_row.get("messageEventsErr_cardinality", 0))
            / float(rm_row.get("n_rows", 1)),
        "numeric": False,
    },
    "trackerEvtsErr": {
        "null_pct": 0.0,
        "cardinality": int(rm_row.get("trackerEvtsErr_cardinality", 0)),
        "uniqueness_ratio": float(rm_row.get("trackerEvtsErr_cardinality", 0))
            / float(rm_row.get("n_rows", 1)),
        "numeric": False,
    },
    "map_name": {
        "null_pct": 0.0,
        "cardinality": int(rm_row.get("map_name_cardinality", 0)),
        "uniqueness_ratio": float(rm_row.get("map_name_cardinality", 0))
            / float(rm_row.get("n_rows", 1)),
        "numeric": False,
    },
    "max_players": {
        "null_pct": 0.0,
        "cardinality": int(rm_row.get("max_players_cardinality", 0)),
        "uniqueness_ratio": float(rm_row.get("max_players_cardinality", 0))
            / float(rm_row.get("n_rows", 1)),
        "numeric": True,
        "iqr": 0.0,
    },
    "map_size_x": {
        "null_pct": 0.0,
        "cardinality": int(rm_row.get("map_size_x_cardinality", 0)),
        "uniqueness_ratio": float(rm_row.get("map_size_x_cardinality", 0))
            / float(rm_row.get("n_rows", 1)),
        "numeric": True,
        "iqr": 0.0,
    },
    "map_size_y": {
        "null_pct": 0.0,
        "cardinality": int(rm_row.get("map_size_y_cardinality", 0)),
        "uniqueness_ratio": float(rm_row.get("map_size_y_cardinality", 0))
            / float(rm_row.get("n_rows", 1)),
        "numeric": True,
        "iqr": 0.0,
    },
    "is_blizzard_map": {
        "null_pct": 0.0,
        "cardinality": int(rm_row.get("is_blizzard_map_cardinality", 0)),
        "uniqueness_ratio": float(rm_row.get("is_blizzard_map_cardinality", 0))
            / float(rm_row.get("n_rows", 1)),
        "numeric": False,
    },
    "is_blizzard_map_init": {
        "null_pct": 0.0,
        "cardinality": int(rm_row.get("is_blizzard_map_init_cardinality", 0)),
        "uniqueness_ratio": float(rm_row.get("is_blizzard_map_init_cardinality", 0))
            / float(rm_row.get("n_rows", 1)),
        "numeric": False,
    },
}

print(f"all_profiles has {len(all_profiles)} columns from replay_players_raw")
print(f"rm_struct_fields has {len(rm_struct_fields)} struct-flat fields")

# %% [markdown]
# ## Cell 18 -- Critical Field Detection

# %%
# W-01: list below is illustrative. Detection must scan ALL profiles programmatically.
# Census flagged 20 near-constant columns across replay_players_raw and
# replays_meta_raw struct-flat. This code collects them dynamically from profiles.

critical_findings: dict = {
    "dead_fields": [],
    "constant_columns": [],
    "near_constant": [],
    "sentinel_columns": [],
}

# Dead fields: null_pct == 100%
for col, p in all_profiles.items():
    if p.get("null_pct", 0) == 100.0:
        critical_findings["dead_fields"].append(col)

# Constant columns from replays_meta_raw struct-flat (cardinality == 1)
# These come from struct fields; check rm_struct_fields
for col, p in rm_struct_fields.items():
    if p.get("cardinality", 99) == 1:
        critical_findings["constant_columns"].append(col)

# Also check all_profiles for cardinality == 1
for col, p in all_profiles.items():
    if p.get("cardinality", 99) == 1:
        if col not in critical_findings["constant_columns"]:
            critical_findings["constant_columns"].append(col)

# Near-constant: uniqueness_ratio < 0.001 OR IQR == 0 (for numeric columns)
# W-01: programmatic scan of ALL profiles
near_constant_rp = [
    col for col, p in all_profiles.items()
    if (p.get("uniqueness_ratio", 1.0) < 0.001
        and p.get("cardinality", 99) <= 20
        and p.get("null_pct", 100) < 100)
    or (p.get("numeric") and p.get("iqr") is not None
        and p.get("iqr", 1) == 0 and p.get("null_pct", 100) < 100)
]
near_constant_rm = [
    col for col, p in rm_struct_fields.items()
    if (p.get("uniqueness_ratio", 1.0) < 0.001
        and p.get("cardinality", 99) <= 20
        and p.get("null_pct", 100) < 100)
    or (p.get("numeric") and p.get("iqr") is not None
        and p.get("iqr", 1) == 0 and p.get("null_pct", 100) < 100)
]
critical_findings["near_constant"] = list(
    set(near_constant_rp + near_constant_rm)
    - set(critical_findings["constant_columns"])
)

# Sentinel columns
critical_findings["sentinel_columns"] = [
    {
        "column": "MMR",
        "table": "replay_players_raw",
        "sentinel_value": 0,
        "sentinel_count": MMR_ZERO_COUNT,
        "sentinel_pct": MMR_ZERO_PCT,
        "interpretation": "MMR=0 means unrated player",
    },
    {
        "column": "SQ",
        "table": "replay_players_raw",
        "sentinel_value": INT32_MIN,
        "sentinel_count": SQ_SENTINEL_COUNT,
        "sentinel_pct": round(100.0 * SQ_SENTINEL_COUNT / RP_TOTAL_ROWS, 4),
        "interpretation": "INT32_MIN sentinel for missing SQ value",
    },
]

print("Critical findings:")
print(f"  dead_fields: {critical_findings['dead_fields']}")
print(f"  constant_columns ({len(critical_findings['constant_columns'])}): "
      f"{critical_findings['constant_columns']}")
print(f"  near_constant ({len(critical_findings['near_constant'])}): "
      f"{critical_findings['near_constant']}")
print(f"  sentinel_columns: {[s['column'] for s in critical_findings['sentinel_columns']]}")

assert len(critical_findings["constant_columns"]) == 5, (
    f"Expected 5 constant columns, got {len(critical_findings['constant_columns'])}: "
    f"{critical_findings['constant_columns']}"
)
print("\nAssertion PASSED: exactly 5 constant columns.")

# %% [markdown]
# ## Cell 18b -- Extended Sentinel Analysis (R08)

# %%
# --- R08: 5 additional sentinel patterns beyond MMR=0 and SQ=INT32_MIN ---

# 1. MMR < 0 (negative MMR values)
sql_queries["sentinel_mmr_negative"] = f"""
SELECT
    COUNT(*) AS mmr_negative_count,
    MIN(MMR) AS mmr_min_negative,
    MAX(MMR) AS mmr_max_negative,
    ROUND(100.0 * COUNT(*) / {RP_TOTAL_ROWS}, 4) AS mmr_negative_pct
FROM replay_players_raw
WHERE MMR < 0
"""
df_mmr_neg = conn.fetch_df(sql_queries["sentinel_mmr_negative"])
MMR_NEGATIVE_COUNT = int(df_mmr_neg.iloc[0]["mmr_negative_count"])
MMR_NEGATIVE_PCT = float(df_mmr_neg.iloc[0]["mmr_negative_pct"])
MMR_MIN_NEGATIVE = int(df_mmr_neg.iloc[0]["mmr_min_negative"]) if MMR_NEGATIVE_COUNT > 0 else None
MMR_MAX_NEGATIVE = int(df_mmr_neg.iloc[0]["mmr_max_negative"]) if MMR_NEGATIVE_COUNT > 0 else None
print(f"MMR negative: {MMR_NEGATIVE_COUNT} rows ({MMR_NEGATIVE_PCT}%)")
if MMR_NEGATIVE_COUNT > 0:
    print(f"  range: [{MMR_MIN_NEGATIVE}, {MMR_MAX_NEGATIVE}]")

# 2. map_size = 0 (from replays_meta_raw -- uses RM_TOTAL_ROWS)
sql_queries["sentinel_map_size_zero"] = """
SELECT COUNT(*) AS map_size_zero_count
FROM replays_meta_raw
WHERE initData.gameDescription.mapSizeX = 0
  AND initData.gameDescription.mapSizeY = 0
"""
df_map_size_zero = conn.fetch_df(sql_queries["sentinel_map_size_zero"])
MAP_SIZE_ZERO_COUNT = int(df_map_size_zero.iloc[0]["map_size_zero_count"])
MAP_SIZE_ZERO_PCT = round(100.0 * MAP_SIZE_ZERO_COUNT / RM_TOTAL_ROWS, 4)
print(f"map_size zero (replays_meta_raw): {MAP_SIZE_ZERO_COUNT} rows ({MAP_SIZE_ZERO_PCT}%)")

# 3. selectedRace = '' (empty string)
sql_queries["sentinel_selectedrace_empty"] = """
SELECT COUNT(*) AS selected_race_empty_count
FROM replay_players_raw
WHERE selectedRace = ''
"""
df_race_empty = conn.fetch_df(sql_queries["sentinel_selectedrace_empty"])
SELECTED_RACE_EMPTY_COUNT = int(df_race_empty.iloc[0]["selected_race_empty_count"])
SELECTED_RACE_EMPTY_PCT = round(100.0 * SELECTED_RACE_EMPTY_COUNT / RP_TOTAL_ROWS, 4)
print(f"selectedRace empty: {SELECTED_RACE_EMPTY_COUNT} rows ({SELECTED_RACE_EMPTY_PCT}%)")

# Extend critical_findings["sentinel_columns"] with 5 new entries
critical_findings["sentinel_columns"].extend([
    {
        "column": "APM",
        "table": "replay_players_raw",
        "sentinel_value": 0,
        "sentinel_count": APM_ZERO_COUNT,
        "sentinel_pct": APM_ZERO_PCT,
        "interpretation": "APM=0 may indicate observer or disconnect",
    },
    {
        "column": "MMR",
        "table": "replay_players_raw",
        "sentinel_value": "negative",
        "sentinel_count": MMR_NEGATIVE_COUNT,
        "sentinel_pct": MMR_NEGATIVE_PCT,
        "interpretation": "Negative MMR values — anomalous sentinel",
    },
    {
        "column": "map_size",
        "table": "replays_meta_raw",
        "sentinel_value": 0,
        "sentinel_count": MAP_SIZE_ZERO_COUNT,
        "sentinel_pct": MAP_SIZE_ZERO_PCT,
        "interpretation": "mapSizeX=0 AND mapSizeY=0 — missing or default map size",
    },
    {
        "column": "handicap",
        "table": "replay_players_raw",
        "sentinel_value": 0,
        "sentinel_count": HANDICAP_ZERO_COUNT,
        "sentinel_pct": HANDICAP_ZERO_PCT,
        "interpretation": "handicap=0 — standard/no handicap applied",
    },
    {
        "column": "selectedRace",
        "table": "replay_players_raw",
        "sentinel_value": "",
        "sentinel_count": SELECTED_RACE_EMPTY_COUNT,
        "sentinel_pct": SELECTED_RACE_EMPTY_PCT,
        "interpretation": "Empty selectedRace string — race not specified",
    },
])

print(f"\nsentinel_columns count: {len(critical_findings['sentinel_columns'])}")
for s in critical_findings["sentinel_columns"]:
    print(f"  {s['column']}: {s['sentinel_count']:,} ({s['sentinel_pct']}%)")

# %% [markdown]
# ## Cell 18c -- Temporal Coverage (R09)

# %%
# --- R09: Temporal coverage (date range, gaps) ---

sql_queries["temporal_coverage"] = """
SELECT
    MIN(details.timeUTC) AS time_utc_min,
    MAX(details.timeUTC) AS time_utc_max,
    COUNT(DISTINCT strftime(TRY_CAST(details.timeUTC AS TIMESTAMP), '%Y-%m'))
        AS distinct_months
FROM replays_meta_raw
WHERE details.timeUTC IS NOT NULL
"""

df_temporal = conn.fetch_df(sql_queries["temporal_coverage"])
TIME_UTC_MIN = str(df_temporal.iloc[0]["time_utc_min"])
TIME_UTC_MAX = str(df_temporal.iloc[0]["time_utc_max"])
DISTINCT_MONTH_COUNT = int(df_temporal.iloc[0]["distinct_months"])
print(f"Temporal range: {TIME_UTC_MIN} to {TIME_UTC_MAX}")
print(f"Distinct months: {DISTINCT_MONTH_COUNT}")

# TRY_CAST verification (Critique fix T02.2)
sql_queries["temporal_trycast_verification"] = """
SELECT COUNT(DISTINCT details.timeUTC) AS raw_distinct
FROM replays_meta_raw
WHERE details.timeUTC IS NOT NULL
"""
df_trycast_verify = conn.fetch_df(sql_queries["temporal_trycast_verification"])
RAW_DISTINCT_TIMESTAMPS = int(df_trycast_verify.iloc[0]["raw_distinct"])
assert DISTINCT_MONTH_COUNT > 0, "No parseable timestamps found"
print(f"TRY_CAST verification: {RAW_DISTINCT_TIMESTAMPS} distinct raw values -> "
      f"{DISTINCT_MONTH_COUNT} distinct months")

# Temporal month gaps (Critique fix T02.1: Python fallback for generate_series)
sql_queries["temporal_month_gaps"] = """
WITH parsed AS (
    SELECT strftime(TRY_CAST(details.timeUTC AS TIMESTAMP), '%Y-%m') AS ym
    FROM replays_meta_raw
    WHERE details.timeUTC IS NOT NULL
),
observed AS (
    SELECT DISTINCT ym FROM parsed WHERE ym IS NOT NULL
),
date_range AS (
    SELECT MIN(ym) AS min_ym, MAX(ym) AS max_ym FROM observed
),
all_months AS (
    SELECT strftime(
        (SELECT TRY_CAST(min_ym || '-01' AS DATE) FROM date_range)
        + INTERVAL (i) MONTH,
        '%Y-%m'
    ) AS ym
    FROM generate_series(0,
        (SELECT DATEDIFF('month',
            TRY_CAST(min_ym || '-01' AS DATE),
            TRY_CAST(max_ym || '-01' AS DATE))
         FROM date_range)
    ) AS t(i)
)
SELECT am.ym AS gap_month
FROM all_months am
LEFT JOIN observed o ON am.ym = o.ym
WHERE o.ym IS NULL
ORDER BY am.ym
"""

try:
    df_gaps = conn.fetch_df(sql_queries["temporal_month_gaps"])
    GAP_MONTHS = df_gaps["gap_month"].tolist()
    print(f"SQL gap detection succeeded: {len(GAP_MONTHS)} gap months")
except Exception as e:
    print(f"SQL gap detection failed ({e}), using Python fallback.")
    # Python fallback (Critique fix T02.1)
    observed_months_df = conn.fetch_df(
        "SELECT DISTINCT strftime(TRY_CAST(details.timeUTC AS TIMESTAMP), '%Y-%m') AS ym "
        "FROM replays_meta_raw WHERE details.timeUTC IS NOT NULL "
        "AND TRY_CAST(details.timeUTC AS TIMESTAMP) IS NOT NULL ORDER BY ym"
    )
    sql_queries["temporal_month_gaps_note"] = (
        "Python fallback used for gap detection (generate_series CTE failed). "
        "See temporal_month_gaps for original SQL."
    )
    observed_set = set(observed_months_df["ym"].dropna())
    min_ym, max_ym = min(observed_set), max(observed_set)
    all_months_set = set(
        pd.date_range(min_ym + "-01", max_ym + "-01", freq="MS").strftime("%Y-%m")
    )
    GAP_MONTHS = sorted(all_months_set - observed_set)
    print(f"Python fallback: {len(GAP_MONTHS)} gap months")

if GAP_MONTHS:
    print(f"Gap months: {GAP_MONTHS}")
else:
    print("No calendar-month gaps found in the temporal range.")

# %% [markdown]
# ## Cell 18d -- startLocX/startLocY Type Verification (R13)

# %%
# --- R13: startLocX/startLocY verification ---
sql_queries["startloc_verification"] = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(startLocX) AS startLocX_null,
    COUNT(*) - COUNT(startLocY) AS startLocY_null,
    SUM(CASE WHEN startLocX < 0 THEN 1 ELSE 0 END) AS startLocX_negative,
    SUM(CASE WHEN startLocY < 0 THEN 1 ELSE 0 END) AS startLocY_negative,
    MIN(startLocX) AS startLocX_min,
    MAX(startLocX) AS startLocX_max,
    MIN(startLocY) AS startLocY_min,
    MAX(startLocY) AS startLocY_max,
    COUNT(DISTINCT startLocX) AS startLocX_cardinality,
    COUNT(DISTINCT startLocY) AS startLocY_cardinality
FROM replay_players_raw
"""

df_startloc = conn.fetch_df(sql_queries["startloc_verification"])
STARTLOCX_NULL = int(df_startloc.iloc[0]["startLocX_null"])
STARTLOCY_NULL = int(df_startloc.iloc[0]["startLocY_null"])
assert STARTLOCX_NULL == 0, f"startLocX has {STARTLOCX_NULL} NULLs"
assert STARTLOCY_NULL == 0, f"startLocY has {STARTLOCY_NULL} NULLs"
print("startLocX/startLocY verification:")
print(df_startloc.T.to_string())
print("\nAssertion PASSED: zero NULLs for startLocX and startLocY.")

# %% [markdown]
# ## Cell 19 -- Completeness Heatmap (T07)

# %%
# Build completeness DataFrame: table, column_name, effective_missing_pct
heatmap_rows = []

# replay_players_raw columns
rp_effective_missing = {
    "MMR": MMR_ZERO_PCT,
    "SQ": round(100.0 * SQ_SENTINEL_COUNT / RP_TOTAL_ROWS, 4),
}
for col, p in all_profiles.items():
    heatmap_rows.append({
        "table": "replay_players_raw",
        "column": col,
        "null_pct": float(p.get("null_pct", 0.0)),
        "effective_missing_pct": rp_effective_missing.get(
            col, float(p.get("null_pct", 0.0))
        ),
    })

# replays_meta_raw struct-flat columns
for col, p in rm_struct_fields.items():
    heatmap_rows.append({
        "table": "replays_meta_raw",
        "column": col,
        "null_pct": float(p.get("null_pct", 0.0)),
        "effective_missing_pct": float(p.get("null_pct", 0.0)),
    })

# map_aliases_raw columns
ma_row = df_ma.iloc[0]
for col in ["tournament", "foreign_name", "english_name", "filename"]:
    null_col = f"{col}_null"
    null_count = int(ma_row.get(null_col, 0))
    null_pct_val = round(100.0 * null_count / int(ma_row["n_rows"]), 4)
    heatmap_rows.append({
        "table": "map_aliases_raw",
        "column": col,
        "null_pct": null_pct_val,
        "effective_missing_pct": null_pct_val,
    })

df_heatmap = pd.DataFrame(heatmap_rows)
print(f"Heatmap DataFrame: {len(df_heatmap)} rows")
print(df_heatmap[df_heatmap["effective_missing_pct"] > 0])

# Build pivot for heatmap: rows = (table, column), value = effective_missing_pct
tables_order = ["replay_players_raw", "replays_meta_raw", "map_aliases_raw"]
fig_h, ax_h = plt.subplots(figsize=(28, 12))

y_labels = []
y_vals = []
colors = []

cmap = plt.get_cmap("YlOrRd")
for _, row in df_heatmap.iterrows():
    y_labels.append(f"{row['table'][:6]}../{row['column']}")
    y_vals.append(row["effective_missing_pct"])

# Use a horizontal bar chart as heatmap substitute (1D per column)
# Group by table with separators
fig_h2, axes_h = plt.subplots(3, 1, figsize=(28, 14))
for ax_i, tbl in enumerate(tables_order):
    tbl_df = df_heatmap[df_heatmap["table"] == tbl].copy()
    tbl_df = tbl_df.sort_values("effective_missing_pct", ascending=False)
    bars = axes_h[ax_i].bar(
        range(len(tbl_df)), tbl_df["effective_missing_pct"], color="steelblue"
    )
    # Highlight MMR
    for idx_b, (_, row_b) in enumerate(tbl_df.iterrows()):
        val = row_b["effective_missing_pct"]
        if val > 0:
            bars[idx_b].set_color(cmap(min(1.0, val / 100.0)))
    axes_h[ax_i].set_xticks(range(len(tbl_df)))
    axes_h[ax_i].set_xticklabels(tbl_df["column"].tolist(), rotation=45, ha="right",
                                  fontsize=8)
    axes_h[ax_i].set_ylabel("Effective Missing %")
    axes_h[ax_i].set_title(f"Table: {tbl}")
    axes_h[ax_i].set_ylim(0, 100)

fig_h2.suptitle(
    "Step 01_03_01 -- Data Completeness (Physical NULL + Sentinel Missingness)\n"
    "Physical NULL rate is 0% for all columns. "
    "Sentinel-based effective missingness: MMR=0 (83.65%), SQ=INT32_MIN (0.004%).",
    fontsize=11,
    y=1.01,
)
plt.tight_layout()

heatmap_path = plots_dir / "01_03_01_completeness_heatmap.png"
fig_h2.savefig(str(heatmap_path), bbox_inches="tight", dpi=120)
plt.close(fig_h2)
print(f"Saved: {heatmap_path}")

# %% [markdown]
# ## Cell 20 -- QQ Plots (T08)

# %%
# B-01 fix: split QQ data into two queries to avoid MMR sentinel filter
# polluting APM/SQ/supplyCappedPercent distributions.

sql_queries["qq_mmr"] = """
SELECT MMR
FROM replay_players_raw
WHERE result IN ('Win', 'Loss') AND MMR > 0
-- I7: MMR > 0 excludes unrated sentinel (83.65% of rows). Rated-only QQ.
"""

sql_queries["qq_ingame"] = f"""
SELECT APM, SQ, supplyCappedPercent
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND SQ > {INT32_MIN}
-- I7: SQ > INT32_MIN excludes 2 sentinel rows. APM/supplyCappedPercent unfiltered.
"""

sql_queries["qq_egl_data"] = """
SELECT header.elapsedGameLoops AS elapsed_game_loops
FROM replays_meta_raw
"""

df_qq_mmr = conn.fetch_df(sql_queries["qq_mmr"])
df_qq_ingame = conn.fetch_df(sql_queries["qq_ingame"])
df_qq_egl = conn.fetch_df(sql_queries["qq_egl_data"])

print(f"QQ MMR (rated-only): {len(df_qq_mmr):,} rows")
print(f"QQ ingame (Win/Loss, SQ sentinel excluded): {len(df_qq_ingame):,} rows")
print(f"QQ elapsed_game_loops: {len(df_qq_egl):,} rows")

# Build 5-panel QQ figure
fig_qq, axes_qq = plt.subplots(1, 5, figsize=(25, 5))

qq_data = [
    (
        df_qq_mmr["MMR"].dropna().values,
        f"MMR [PRE-GAME, rated only, N={len(df_qq_mmr):,}]",
    ),
    (
        df_qq_ingame["APM"].dropna().values,
        f"APM [IN-GAME, N={df_qq_ingame['APM'].count():,}]",
    ),
    (
        df_qq_ingame["SQ"].dropna().values,
        f"SQ [IN-GAME, sentinel excluded, N={df_qq_ingame['SQ'].dropna().count():,}]",
    ),
    (
        df_qq_ingame["supplyCappedPercent"].dropna().values,
        f"supplyCappedPercent [IN-GAME, N={df_qq_ingame['supplyCappedPercent'].count():,}]",
    ),
    (
        df_qq_egl["elapsed_game_loops"].dropna().values,
        f"elapsed_game_loops [POST-GAME, N={df_qq_egl['elapsed_game_loops'].count():,}]",
    ),
]

for ax_qq, (vals, title) in zip(axes_qq, qq_data):
    if len(vals) > 0:
        (osm, osr), (slope, intercept, r) = stats.probplot(vals, dist="norm")
        ax_qq.scatter(osm, osr, alpha=0.3, s=1, rasterized=True)
        ax_qq.plot(osm, slope * np.array(osm) + intercept, "r-", linewidth=1)
    ax_qq.set_title(title, fontsize=7, wrap=True)
    ax_qq.set_xlabel("Theoretical quantiles", fontsize=7)
    ax_qq.set_ylabel("Sample quantiles", fontsize=7)
    ax_qq.tick_params(labelsize=6)

fig_qq.suptitle(
    "Step 01_03_01 -- Normal QQ Plots for Key Numeric Columns\n"
    "(Invariants #3, #7 applied; B-01 fix: MMR uses rated-only query)",
    fontsize=10,
)
plt.tight_layout()

qq_path = plots_dir / "01_03_01_qq_plots.png"
fig_qq.savefig(str(qq_path), bbox_inches="tight", dpi=120)
plt.close(fig_qq)
print(f"Saved: {qq_path}")

# %% [markdown]
# ## Cell 21 -- ECDF Plots (T09)

# %%
# Reuse data fetched in T08
fig_ecdf, axes_ecdf = plt.subplots(1, 3, figsize=(18, 5))

ecdf_data = [
    (
        df_qq_mmr["MMR"].dropna().values,
        "MMR [PRE-GAME, rated only, MMR > 0]",
        "MMR",
    ),
    (
        df_qq_ingame["APM"].dropna().values,
        "APM [IN-GAME (Inv. #3)]",
        "APM",
    ),
    (
        df_qq_ingame["SQ"].dropna().values,
        "SQ [IN-GAME (Inv. #3), sentinel excluded]",
        "SQ",
    ),
]

for ax_e, (vals, title, xlabel) in zip(axes_ecdf, ecdf_data):
    if len(vals) > 0:
        sorted_vals = np.sort(vals)
        ecdf_y = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
        ax_e.step(sorted_vals, ecdf_y, where="post", linewidth=1)
    ax_e.set_title(title, fontsize=9)
    ax_e.set_xlabel(xlabel, fontsize=8)
    ax_e.set_ylabel("ECDF", fontsize=8)
    ax_e.set_ylim(0, 1)
    ax_e.tick_params(labelsize=7)

fig_ecdf.suptitle(
    "Step 01_03_01 -- Empirical CDF for Key Numeric Columns",
    fontsize=11,
)
plt.tight_layout()

ecdf_path = plots_dir / "01_03_01_ecdf_key_columns.png"
fig_ecdf.savefig(str(ecdf_path), bbox_inches="tight", dpi=120)
plt.close(fig_ecdf)
print(f"Saved: {ecdf_path}")

# %% [markdown]
# ## Cell 22 -- Build JSON Artifact (T10)

# %%
# Helper to convert numpy types to Python native for JSON serialization
def _to_native(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_native(x) for x in obj]
    return obj


# Build column profiles dict from df_rp_null_card and df_rp_numeric
rp_col_profiles: dict = {}
for col, p in all_profiles.items():
    rp_col_profiles[col] = _to_native(p)

# replays_meta_raw struct-flat profiles
rm_col_profiles: dict = _to_native(rm_struct_fields)

# map_aliases_raw profiles
ma_row_d = df_ma.iloc[0].to_dict()
ma_col_profiles = {
    "tournament": {
        "null_count": int(ma_row_d.get("tournament_null", 0)),
        "cardinality": int(ma_row_d.get("tournament_cardinality", 0)),
    },
    "foreign_name": {
        "null_count": int(ma_row_d.get("foreign_name_null", 0)),
        "cardinality": int(ma_row_d.get("foreign_name_cardinality", 0)),
    },
    "english_name": {
        "null_count": int(ma_row_d.get("english_name_null", 0)),
        "cardinality": int(ma_row_d.get("english_name_cardinality", 0)),
    },
    "filename": {
        "null_count": int(ma_row_d.get("filename_null", 0)),
        "cardinality": int(ma_row_d.get("filename_cardinality", 0)),
    },
}

# IQR outliers
iqr_row = df_rp_iqr.iloc[0].to_dict()
iqr_mmr_rated_row = df_rp_iqr_mmr_rated.iloc[0].to_dict()
iqr_egl_row = df_rm_egl_iqr.iloc[0].to_dict() if len(df_rm_egl_iqr) > 0 else {}

# Categorical top-k as simple list of dicts
rp_topk_json = {
    col: df_rp_topk[col].to_dict(orient="records")
    for col in CATEGORICAL_COLS_RP
}

# Dataset level
dupes_row = df_dupes.iloc[0].to_dict()
linkage_row = df_linkage.iloc[0].to_dict()
class_bal = df_class_balance.to_dict(orient="records")
mem_rows = df_memory.to_dict(orient="records")
row_count_rows = df_row_counts.to_dict(orient="records")

# sql_queries: convert nested dicts for JSON serialization
sql_queries_json: dict = {}
for k, v in sql_queries.items():
    if isinstance(v, dict):
        sql_queries_json[k] = v  # nested (rp_topk)
    else:
        sql_queries_json[k] = v

profile_json = {
    "step": "01_03_01",
    "dataset": "sc2egset",
    "tables": {
        "replay_players_raw": {
            "n_rows": RP_TOTAL_ROWS,
            "n_cols": 25,
            "column_profiles": rp_col_profiles,
            "iqr_outliers": {
                "all_rows": {
                    "mmr_iqr_outliers": _to_native(iqr_row.get("mmr_iqr_outliers")),
                    "apm_iqr_outliers": _to_native(iqr_row.get("apm_iqr_outliers")),
                    "sq_iqr_outliers": _to_native(iqr_row.get("sq_iqr_outliers")),
                    "sc_iqr_outliers": _to_native(iqr_row.get("sc_iqr_outliers")),
                },
                "MMR": {
                    "iqr_outliers_all": _to_native(iqr_row.get("mmr_iqr_outliers")),
                    "iqr_outliers_rated_only": _to_native(
                        iqr_mmr_rated_row.get("mmr_iqr_outliers_rated")
                    ),
                    "mmr_p25_rated": _to_native(iqr_mmr_rated_row.get("p25")),
                    "mmr_p75_rated": _to_native(iqr_mmr_rated_row.get("p75")),
                    "mmr_iqr_rated": _to_native(iqr_mmr_rated_row.get("iqr")),
                    "note": (
                        "MMR IQR outlier count for all rows is degenerate (IQR=0 since "
                        "Q1=Q3=0); rated-only (MMR>0) IQR outlier count is also reported."
                    ),
                },
            },
            "topk_categorical": rp_topk_json,
        },
        "replays_meta_raw": {
            "n_rows": RM_TOTAL_ROWS,
            "n_top_level_cols": 9,
            "n_struct_flat_fields": 17,
            "struct_field_profiles": rm_col_profiles,
            "elapsed_game_loops_iqr": {
                "q1": _to_native(iqr_egl_row.get("q1")),
                "q3": _to_native(iqr_egl_row.get("q3")),
                "iqr": _to_native(iqr_egl_row.get("iqr")),
                "lower_fence": _to_native(iqr_egl_row.get("lower_fence")),
                "upper_fence": _to_native(iqr_egl_row.get("upper_fence")),
                "iqr_outlier_count": _to_native(iqr_egl_row.get("iqr_outlier_count")),
                "classification": "POST-GAME (reclassified 2026-04-15)",
            },
        },
        "map_aliases_raw": {
            "n_rows": int(ma_row_d.get("n_rows", 0)),
            "n_cols": 4,
            "column_profiles": ma_col_profiles,
        },
    },
    "dataset_level": {
        "row_counts": row_count_rows,
        "duplicate_check": {
            "total_rows": _to_native(dupes_row.get("total_rows")),
            "distinct_pairs": _to_native(dupes_row.get("distinct_pairs")),
            "duplicate_rows": _to_native(dupes_row.get("duplicate_rows")),
            "key": "(filename, playerID)",
        },
        "class_balance": class_bal,
        "cross_table_linkage": {
            "rp_distinct_replays": _to_native(linkage_row.get("rp_distinct_replays")),
            "rm_distinct_replays": _to_native(linkage_row.get("rm_distinct_replays")),
            "rp_orphans": _to_native(linkage_row.get("rp_orphans")),
            "rm_orphans": _to_native(linkage_row.get("rm_orphans")),
        },
        "memory_footprint": _to_native(mem_rows),
        "temporal_coverage": {
            "time_utc_min": TIME_UTC_MIN,
            "time_utc_max": TIME_UTC_MAX,
            "distinct_months": DISTINCT_MONTH_COUNT,
            "gap_months": GAP_MONTHS,
        },
        "startloc_verification": {
            "startLocX_null": STARTLOCX_NULL,
            "startLocY_null": STARTLOCY_NULL,
            "startLocX_min": int(df_startloc.iloc[0]["startLocX_min"]),
            "startLocX_max": int(df_startloc.iloc[0]["startLocX_max"]),
            "startLocY_min": int(df_startloc.iloc[0]["startLocY_min"]),
            "startLocY_max": int(df_startloc.iloc[0]["startLocY_max"]),
            "startLocX_cardinality": int(df_startloc.iloc[0]["startLocX_cardinality"]),
            "startLocY_cardinality": int(df_startloc.iloc[0]["startLocY_cardinality"]),
        },
    },
    "critical_findings": critical_findings,
    "field_classification": FIELD_CLASSIFICATION,
    "elapsed_game_loops_reclassification": (
        "elapsed_game_loops classified POST-GAME, consistent with "
        "the census artifact (01_02_04) which also records it under "
        "'post_game' in the I3 classification."
    ),
    "sql_queries": sql_queries_json,
    "sentinel_summary": {
        "MMR": {
            "sentinel_value": 0,
            "count": MMR_ZERO_COUNT,
            "pct": MMR_ZERO_PCT,
            "interpretation": "MMR=0 means unrated player",
        },
        "SQ": {
            "sentinel_value": INT32_MIN,
            "count": SQ_SENTINEL_COUNT,
            "pct": round(100.0 * SQ_SENTINEL_COUNT / RP_TOTAL_ROWS, 4),
            "interpretation": "INT32_MIN sentinel for missing SQ value",
        },
        "APM": {
            "sentinel_value": 0,
            "count": APM_ZERO_COUNT,
            "pct": APM_ZERO_PCT,
            "interpretation": "APM=0 may indicate observer or disconnect",
        },
        "MMR_negative": {
            "sentinel_value": "negative",
            "count": MMR_NEGATIVE_COUNT,
            "pct": MMR_NEGATIVE_PCT,
            "interpretation": "Negative MMR values — anomalous sentinel",
        },
        "map_size": {
            "sentinel_value": 0,
            "count": MAP_SIZE_ZERO_COUNT,
            "pct": MAP_SIZE_ZERO_PCT,
            "table": "replays_meta_raw",
            "interpretation": "mapSizeX=0 AND mapSizeY=0 — missing or default map size",
        },
        "handicap": {
            "sentinel_value": 0,
            "count": HANDICAP_ZERO_COUNT,
            "pct": HANDICAP_ZERO_PCT,
            "interpretation": "handicap=0 — standard/no handicap applied",
        },
        "selectedRace": {
            "sentinel_value": "",
            "count": SELECTED_RACE_EMPTY_COUNT,
            "pct": SELECTED_RACE_EMPTY_PCT,
            "interpretation": "Empty selectedRace string — race not specified",
        },
    },
}

json_path = artifact_dir / "01_03_01_systematic_profile.json"
with open(json_path, "w") as jf:
    json.dump(profile_json, jf, indent=2, default=str)
print(f"Saved: {json_path}")

# %% [markdown]
# ## Cell 23 -- Markdown Artifact (T11)

# %%
# Build I3 classification table
def _build_i3_table(field_class: dict) -> str:
    lines = []
    lines.append("| Table | Column | I3 Classification |")
    lines.append("|-------|--------|-------------------|")
    rp_fc = field_class.get("replay_players_raw", {})
    for cls_key, cols in rp_fc.items():
        for col in cols:
            lines.append(f"| replay_players_raw | {col} | {cls_key.upper()} |")
    rm_fc = field_class.get("replays_meta_raw_struct_flat", {})
    for cls_key, cols in rm_fc.items():
        for col in cols:
            # Override elapsed_game_loops classification
            display_cls = cls_key.upper()
            if col == "elapsed_game_loops":
                display_cls = "POST-GAME (reclassified 2026-04-15)"
            lines.append(f"| replays_meta_raw | {col} | {display_cls} |")
    # map_aliases_raw: not in census field_classification; add manually
    for col in ["tournament", "foreign_name", "english_name", "filename"]:
        lines.append(f"| map_aliases_raw | {col} | IDENTIFIER/REFERENCE |")
    return "\n".join(lines)


# Build SQL section
def _build_sql_section(sqls: dict) -> str:
    lines = ["## SQL Queries (Invariant #6 — verbatim)"]
    for name, sql in sqls.items():
        if isinstance(sql, dict):
            lines.append(f"\n### {name} (per-column queries)")
            for sub_name, sub_sql in sql.items():
                lines.append(f"\n#### {name}['{sub_name}']")
                lines.append("```sql")
                lines.append(sub_sql.strip())
                lines.append("```")
        else:
            lines.append(f"\n### {name}")
            lines.append("```sql")
            lines.append(sql.strip())
            lines.append("```")
    return "\n".join(lines)


i3_table = _build_i3_table(FIELD_CLASSIFICATION)
sql_section = _build_sql_section(sql_queries_json)

# Numeric profile summary table
numeric_summary_lines = [
    "| column | n_rows | null_pct | zero_pct | cardinality | mean | std | skewness | kurtosis |",
    "|--------|--------|----------|----------|-------------|------|-----|----------|----------|",
]
for _, row_n in df_rp_numeric.iterrows():
    numeric_summary_lines.append(
        f"| {row_n['column_name']} | {row_n['n_rows']:,} | {row_n['null_pct']:.4f} | "
        f"{row_n['zero_pct']:.4f} | {row_n['cardinality']:,} | "
        f"{row_n['mean_val']:.2f} | {row_n['std_val']:.2f} | "
        f"{row_n['skewness']:.4f} | {row_n['kurtosis']:.4f} |"
    )
numeric_summary_str = "\n".join(numeric_summary_lines)

# Categorical top-k section
cat_topk_lines = []
for col_t in CATEGORICAL_COLS_RP:
    cat_topk_lines.append(f"\n#### {col_t}")
    cat_topk_lines.append("| value | count | pct |")
    cat_topk_lines.append("|-------|-------|-----|")
    for _, row_t in df_rp_topk[col_t].iterrows():
        cat_topk_lines.append(
            f"| {row_t['value']} | {row_t['cnt']:,} | {row_t['pct']:.4f}% |"
        )
cat_topk_str = "\n".join(cat_topk_lines)

# IQR outlier section
iqr_row_d = df_rp_iqr.iloc[0].to_dict()
mmr_rated_d = df_rp_iqr_mmr_rated.iloc[0].to_dict()

md_content = f"""# Step 01_03_01 -- Systematic Data Profiling
## sc2egset Dataset

**Phase:** 01 -- Data Exploration
**Pipeline Section:** 01_03 -- Systematic Data Profiling
**Predecessor:** 01_02_05
**Date:** 2026-04-16
**Invariants applied:** #3 (temporal classification), #6 (SQL verbatim), #7 (cited thresholds), #9 (no feature computation)

---

## Temporal Classification (Invariant #3)

> Note: `elapsed_game_loops` classified **POST-GAME**, consistent with the census artifact (01_02_04) which also records it under `post_game` in the I3 classification.

{i3_table}

---

## Table Summaries

| Table | Rows | Columns | Duplicates |
|-------|------|---------|------------|
| replay_players_raw | {RP_TOTAL_ROWS:,} | 25 | 0 (on filename, playerID) |
| replays_meta_raw | {RM_TOTAL_ROWS:,} | 9 top-level + 17 struct-flat | N/A |
| map_aliases_raw | {int(ma_row_d.get('n_rows', 0)):,} | 4 | N/A |

---

## Column-Level Profile: replay_players_raw Numeric Columns

{numeric_summary_str}

### MMR IQR Outlier Note (W-03)

**MMR IQR outlier count for all rows is degenerate (IQR=0 since Q1=Q3=0):**
- All-rows IQR outlier count: {int(iqr_row_d.get('mmr_iqr_outliers', 0)):,}
  (equals the number of rated players — every MMR>0 row is flagged)
- **Rated-only (MMR>0) IQR outlier count: {int(mmr_rated_d.get('mmr_iqr_outliers_rated', 0)):,}**
  (computed on the {int(RP_TOTAL_ROWS - MMR_ZERO_COUNT):,} rated rows only)
- Rated IQR: P25={float(mmr_rated_d.get('p25', 0)):.1f}, P75={float(mmr_rated_d.get('p75', 0)):.1f},
  IQR={float(mmr_rated_d.get('iqr', 0)):.1f}

IQR fence at 1.5*IQR per Tukey (1977) — Invariant #7.

---

## Categorical Top-5 Profiles
{cat_topk_str}

---

## Critical Findings

### Dead Fields (null_pct == 100%)
{critical_findings['dead_fields'] if critical_findings['dead_fields'] else "None (0% NULL rate across all tables confirmed by 01_02_04 census)."}

### Constant Columns (cardinality == 1)
{chr(10).join(f"- `{c}`" for c in critical_findings['constant_columns'])}

These 5 columns must be dropped before feature engineering (Phase 02).

### Near-Constant Columns (uniqueness_ratio < 0.001 OR IQR == 0)
{chr(10).join(f"- `{c}`" for c in sorted(critical_findings['near_constant']))}

### Sentinel Columns
| Column | Table | Sentinel Value | Count | Pct | Interpretation |
|--------|-------|---------------|-------|-----|---------------|
| MMR | replay_players_raw | 0 | {MMR_ZERO_COUNT:,} | {MMR_ZERO_PCT:.2f}% | Unrated player |
| SQ | replay_players_raw | INT32_MIN ({INT32_MIN}) | {SQ_SENTINEL_COUNT} | {round(100.0*SQ_SENTINEL_COUNT/RP_TOTAL_ROWS, 4):.4f}% | Missing SQ value |
| APM | replay_players_raw | 0 | {APM_ZERO_COUNT:,} | {APM_ZERO_PCT:.4f}% | Observer or disconnect |
| MMR (negative) | replay_players_raw | negative | {MMR_NEGATIVE_COUNT:,} | {MMR_NEGATIVE_PCT:.4f}% | Anomalous sentinel |
| map_size* | replays_meta_raw | 0 | {MAP_SIZE_ZERO_COUNT:,} | {MAP_SIZE_ZERO_PCT:.4f}% | Missing/default map size |
| handicap | replay_players_raw | 0 | {HANDICAP_ZERO_COUNT:,} | {HANDICAP_ZERO_PCT:.4f}% | Standard/no handicap |
| selectedRace | replay_players_raw | (empty) | {SELECTED_RACE_EMPTY_COUNT:,} | {SELECTED_RACE_EMPTY_PCT:.4f}% | Race not specified |

\\* map_size uses replays_meta_raw (N={RM_TOTAL_ROWS:,}); all others use replay_players_raw (N={RP_TOTAL_ROWS:,})

---

## Temporal Coverage

| Metric | Value |
|--------|-------|
| Earliest timestamp | {TIME_UTC_MIN} |
| Latest timestamp | {TIME_UTC_MAX} |
| Distinct calendar months | {DISTINCT_MONTH_COUNT} |
| Calendar-month gaps | {len(GAP_MONTHS)} ({', '.join(GAP_MONTHS) if GAP_MONTHS else 'none'}) |

---

## startLocX/startLocY Verification

| Metric | startLocX | startLocY |
|--------|-----------|-----------|
| NULLs | {STARTLOCX_NULL} | {STARTLOCY_NULL} |
| Min | {int(df_startloc.iloc[0]['startLocX_min'])} | {int(df_startloc.iloc[0]['startLocY_min'])} |
| Max | {int(df_startloc.iloc[0]['startLocX_max'])} | {int(df_startloc.iloc[0]['startLocY_max'])} |
| Cardinality | {int(df_startloc.iloc[0]['startLocX_cardinality'])} | {int(df_startloc.iloc[0]['startLocY_cardinality'])} |

Both columns are INTEGER with zero NULLs, confirmed by schema YAML and runtime verification.

---

## Cross-Table Linkage

| Metric | Value |
|--------|-------|
| rp_distinct_replays | {int(linkage_row.get('rp_distinct_replays', 0)):,} |
| rm_distinct_replays | {int(linkage_row.get('rm_distinct_replays', 0)):,} |
| rp_orphans | {int(linkage_row.get('rp_orphans', 0))} |
| rm_orphans | {int(linkage_row.get('rm_orphans', 0))} |

---

## Class Balance

| result | count | pct |
|--------|-------|-----|
{chr(10).join(f"| {r['result']} | {r['cnt']:,} | {r['pct']:.4f}% |" for r in class_bal)}

---

## Plot Index

| File | Description |
|------|-------------|
| `plots/01_03_01_completeness_heatmap.png` | Effective missingness per column per table. MMR=83.65% sentinel missingness dominates. |
| `plots/01_03_01_qq_plots.png` | Normal QQ plots for MMR (rated), APM, SQ (no sentinel), supplyCappedPercent, elapsed_game_loops (POST-GAME). |
| `plots/01_03_01_ecdf_key_columns.png` | ECDF for MMR (rated), APM, SQ (no sentinel). |

**Distribution methods applied:** Histograms (01_02_05), QQ plots, ECDFs. KDE omitted: histograms and QQ plots provide equivalent shape assessment for these distributions; KDE adds smoothing artifacts on discrete integer columns (MMR, APM, SQ) and bounded distributions (supplyCappedPercent). QQ plots are the stronger diagnostic tool per Tukey (1977).

---

{sql_section}

---

## Invariants Applied

- **#3 (Temporal discipline):** Every column classified. `elapsed_game_loops` annotated POST-GAME (reclassified 2026-04-15).
- **#6 (Reproducibility):** All SQL stored verbatim in `sql_queries` dict and in this artifact.
- **#7 (No magic numbers):** IQR fence = 1.5 * IQR per Tukey (1977). All sentinel thresholds from census JSON.
- **#9 (Step scope):** Profiling only. No cleaning, no feature engineering.

---

## Phase 02 Implications

- **Drop:** 5 constant columns (`game_speed`, `game_speed_init`, `gameEventsErr`, `messageEventsErr`, `trackerEvtsErr`).
- **Sentinel handling:** MMR=0 (83.65% unrated) and SQ=INT32_MIN (2 rows) require explicit handling.
- **Near-constant columns:** Review whether near-constant columns carry any predictive signal.
- **elapsed_game_loops:** POST-GAME feature — cannot be used in pre-game prediction context.
"""

md_path = artifact_dir / "01_03_01_systematic_profile.md"
md_path.write_text(md_content, encoding="utf-8")
print(f"Saved: {md_path}")

# %% [markdown]
# ## Cell 24 -- Gate Verification and Connection Close (T12)

# %%
json_path_chk = artifact_dir / "01_03_01_systematic_profile.json"
md_path_chk = artifact_dir / "01_03_01_systematic_profile.md"
heatmap_path_chk = plots_dir / "01_03_01_completeness_heatmap.png"
qq_path_chk = plots_dir / "01_03_01_qq_plots.png"
ecdf_path_chk = plots_dir / "01_03_01_ecdf_key_columns.png"

for p in [json_path_chk, md_path_chk, heatmap_path_chk, qq_path_chk, ecdf_path_chk]:
    assert p.exists(), f"Missing artifact: {p}"
    assert p.stat().st_size > 0, f"Empty artifact: {p}"
    print(f"  OK: {p.name} ({p.stat().st_size:,} bytes)")

# Gate check: JSON contains critical_findings
with open(json_path_chk) as f_chk:
    profile_chk = json.load(f_chk)

assert "critical_findings" in profile_chk, "JSON missing critical_findings key"
assert len(profile_chk["critical_findings"]["constant_columns"]) == 5, (
    f"Expected 5 constant columns, got "
    f"{len(profile_chk['critical_findings']['constant_columns'])}: "
    f"{profile_chk['critical_findings']['constant_columns']}"
)

# Gate check: MD contains I3 classification table
md_text_chk = md_path_chk.read_text()
assert "I3" in md_text_chk or "Temporal Classification" in md_text_chk, (
    "MD missing I3 classification table"
)

# Gate check: MMR rated-only IQR exists in JSON (W-03)
assert "iqr_outliers_rated_only" in str(profile_chk), (
    "JSON missing MMR rated-only IQR outlier count"
)

# Gate check: R08 -- sentinel_summary has 7 keys
assert len(profile_chk["sentinel_summary"]) == 7, (
    f"Expected 7 sentinel_summary entries, got {len(profile_chk['sentinel_summary'])}"
)

# Gate check: R09 -- temporal_coverage exists
assert "temporal_coverage" in profile_chk.get("dataset_level", {}), (
    "JSON missing temporal_coverage key"
)

# Gate check: R13 -- startloc_verification exists
assert "startloc_verification" in profile_chk.get("dataset_level", {}), (
    "JSON missing startloc_verification key"
)

# Gate check: R08 -- sentinel_columns has 7 entries
assert len(profile_chk["critical_findings"]["sentinel_columns"]) == 7, (
    f"Expected 7 sentinel_columns, got "
    f"{len(profile_chk['critical_findings']['sentinel_columns'])}"
)

print("\nAll 01_03_01 gate checks PASSED.")

conn.close()
print("DuckDB connection closed. Done.")
