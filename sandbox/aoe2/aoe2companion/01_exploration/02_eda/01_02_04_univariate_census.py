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
# # Step 01_02_04 -- Univariate Census & Target Variable EDA: aoe2companion
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_02 -- EDA
# **Dataset:** aoe2companion
# **Question:** What are the NULL rates, cardinality, value distributions, and
# descriptive statistics for all columns across all four raw tables? What is the
# target variable (`won`) distribution and class balance?
# **Invariants applied:** #6 (reproducibility -- SQL inlined in artifact),
# #7 (no magic numbers), #8 (cross-game comparability), #9 (step scope: query)
# **Step scope:** query
# **Type:** Read-only -- no DuckDB writes, no new tables, no schema changes

# %% [markdown]
# ## 0. Imports and DB connection

# %%
import json
import os
from pathlib import Path

import pandas as pd

from rts_predict.common.notebook_utils import (
    get_notebook_db,
    get_reports_dir,
    setup_notebook_logging,
)

logger = setup_notebook_logging()

# %%
db = get_notebook_db("aoe2", "aoe2companion")
con = db.con
print("Connected to aoe2companion DuckDB (read-only)")

# %%
# T07: Memory footprint -- record DuckDB file size as a dataset-level metric
# Note: DB_FILE is not defined in this notebook's scope; use db._dataset.db_file
# (where db = get_notebook_db("aoe2", "aoe2companion")).
db_size_bytes = os.path.getsize(str(db._dataset.db_file))
print(f"DuckDB file size: {db_size_bytes:,} bytes ({db_size_bytes / (1024**3):.2f} GB)")

# %%
reports_dir = get_reports_dir("aoe2", "aoe2companion")
artifacts_dir = reports_dir / "artifacts" / "01_exploration" / "02_eda"
artifacts_dir.mkdir(parents=True, exist_ok=True)
print(f"Artifacts dir: {artifacts_dir}")

# %%
# Collector for JSON artifact
findings: dict = {}
findings["db_memory_footprint_bytes"] = db_size_bytes

# %% [markdown]
# ## A. Full NULL census of matches_raw (all 55 columns)
#
# Use SUMMARIZE as primary single-pass approach, then tidy the output.

# %%
print("Running SUMMARIZE on matches_raw (single pass over 277M rows)...")
summarize_df = con.execute("SUMMARIZE matches_raw").df()
print(f"SUMMARIZE returned {len(summarize_df)} rows (one per column)")

# %%
# Extract NULL census from SUMMARIZE output
# null_percentage is already float64 (e.g. 4.69 for 4.69%)
null_census_matches = summarize_df[["column_name", "count", "null_percentage"]].copy()
null_census_matches = null_census_matches.rename(
    columns={"count": "non_null_count"}
)

# %%
# Get total row count and cardinality per column via SUMMARIZE approx_unique
total_rows = con.execute(
    "SELECT COUNT(*) AS n FROM matches_raw"
).fetchone()[0]
print(f"Total rows in matches_raw: {total_rows:,}")

# %%
# Build tidy NULL census DataFrame
null_census_matches["total_rows"] = total_rows
null_census_matches["null_count"] = (
    (null_census_matches["null_percentage"] / 100.0 * total_rows)
    .round(0)
    .astype(int)
)
null_census_matches["null_pct"] = null_census_matches["null_percentage"]

# %%
# Get exact cardinality from SUMMARIZE approx_unique column
null_census_matches["approx_cardinality"] = summarize_df["approx_unique"].astype(int)
print("\n=== matches_raw NULL census (all 55 columns) ===")
print(
    null_census_matches[
        ["column_name", "total_rows", "null_count", "null_pct", "approx_cardinality"]
    ].to_string(index=False)
)

# %%
findings["matches_raw_null_census"] = (
    null_census_matches[
        ["column_name", "total_rows", "null_count", "null_pct", "approx_cardinality"]
    ]
    .to_dict(orient="records")
)
findings["matches_raw_total_rows"] = int(total_rows)

# %% [markdown]
# **SQL used:**
# ```sql
# SUMMARIZE matches_raw
# SELECT COUNT(*) AS n FROM matches_raw
# ```

# %% [markdown]
# ## A2. Empty-string investigation for VARCHAR columns
#
# Investigate whether `difficulty`, `colorHex`, `startingAge`, `endingAge`,
# `civilizationSet` (0 NULLs per SUMMARIZE) contain empty strings instead of NULLs.
# Also confirm `scenario` and `modDataset` (high-NULL VARCHARs) have genuine NULLs.
# `password` is BOOLEAN — empty-string hypothesis does not apply.

# %%
empty_string_cols = [
    "difficulty", "colorHex", "startingAge", "endingAge", "civilizationSet",
    "scenario", "modDataset"  # high-NULL VARCHARs -- confirm genuine NULLs
]
empty_string_results = []
for col in empty_string_cols:
    sql = f"""
    SELECT
        '{col}' AS column_name,
        COUNT(*) FILTER (WHERE "{col}" IS NULL)                                AS null_count,
        COUNT(*) FILTER (WHERE "{col}" = '')                                   AS empty_string_count,
        COUNT(*) FILTER (WHERE "{col}" IS NOT NULL AND "{col}" != '')          AS non_empty_count,
        COUNT(*)                                                               AS total_rows
    FROM matches_raw
    """
    row = con.execute(sql).df().iloc[0]
    empty_string_results.append(row.to_dict())
    print(
        f"{col}: NULL={int(row['null_count']):,}  "
        f"EMPTY={int(row['empty_string_count']):,}  "
        f"NON_EMPTY={int(row['non_empty_count']):,}"
    )

findings["empty_string_investigation"] = empty_string_results

# %%
# Verify: for each column the three counts sum to total_rows
for entry in empty_string_results:
    triple_sum = int(entry["null_count"]) + int(entry["empty_string_count"]) + int(entry["non_empty_count"])
    assert triple_sum == int(entry["total_rows"]), (
        f"Triple sum mismatch for {entry['column_name']}: {triple_sum} != {int(entry['total_rows'])}"
    )
print("All triple sums match total_rows.")

# %% [markdown]
# ## B. Target variable analysis (`won`)

# %%
won_dist_sql = """
SELECT
    won,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM matches_raw
GROUP BY won
ORDER BY cnt DESC
"""
print("Running won distribution query...")
won_dist_df = con.execute(won_dist_sql).df()
print("\n=== won value distribution ===")
print(won_dist_df.to_string(index=False))
findings["won_distribution"] = won_dist_df.to_dict(orient="records")

# %%
# Patch won null_count with exact value from GROUP BY (SUMMARIZE is approximate)
null_rows = won_dist_df.loc[won_dist_df["won"].isna()]
assert len(null_rows) == 1, f"Expected exactly 1 NULL won group, got {len(null_rows)}"
won_null_exact = int(null_rows["cnt"].iloc[0])
won_idx = null_census_matches.index[null_census_matches["column_name"] == "won"]
null_census_matches.loc[won_idx, "null_count"] = won_null_exact
null_census_matches.loc[won_idx, "null_pct"] = round(
    100.0 * won_null_exact / total_rows, 2
)
print(f"Patched won null_count: {won_null_exact:,} (exact from GROUP BY)")

# Re-emit matches_raw_null_census with corrected won value
findings["matches_raw_null_census"] = (
    null_census_matches[
        ["column_name", "total_rows", "null_count", "null_pct", "approx_cardinality"]
    ]
    .to_dict(orient="records")
)

findings["exact_won_null_note"] = {
    "column": "won",
    "summarize_derived_null_count": 12995946,
    "group_by_exact_null_count": won_null_exact,
    "discrepancy": 12995946 - won_null_exact,
    "resolution": "GROUP BY count is authoritative for the prediction target.",
    "approximation_note": (
        "SUMMARIZE approximate counts are used for all columns except 'won', "
        "where the exact GROUP BY value is authoritative for the prediction target."
    )
}

# %%
won_by_lb_sql = """
SELECT
    leaderboard,
    won,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(PARTITION BY leaderboard), 2) AS pct
FROM matches_raw
GROUP BY leaderboard, won
ORDER BY leaderboard, won
"""
print("Running won distribution stratified by leaderboard...")
won_by_lb_df = con.execute(won_by_lb_sql).df()
print("\n=== won distribution by leaderboard ===")
print(won_by_lb_df.to_string(index=False))
findings["won_by_leaderboard"] = won_by_lb_df.to_dict(orient="records")

# %%
# Intra-match won consistency check (2-row matches)
consistency_sql = """
WITH match_pairs AS (
    SELECT
        matchId,
        COUNT(*) AS n_rows,
        COUNT(*) FILTER (WHERE won = TRUE) AS won_true,
        COUNT(*) FILTER (WHERE won = FALSE) AS won_false,
        COUNT(*) - COUNT(won) AS won_null
    FROM matches_raw
    GROUP BY matchId
    HAVING COUNT(*) = 2
)
SELECT
    COUNT(*) AS total_2row_matches,
    COUNT(*) FILTER (WHERE won_true = 1 AND won_false = 1)
        AS consistent_complement,
    COUNT(*) FILTER (WHERE won_null = 2) AS both_null,
    COUNT(*) FILTER (WHERE won_true = 1 AND won_null = 1)
        AS one_true_one_null,
    COUNT(*) FILTER (WHERE won_false = 1 AND won_null = 1)
        AS one_false_one_null,
    COUNT(*) FILTER (WHERE won_true = 2) AS both_true,
    COUNT(*) FILTER (WHERE won_false = 2) AS both_false,
    COUNT(*) FILTER (WHERE won_true = 0 AND won_false = 0
        AND won_null < 2) AS other_inconsistent
FROM match_pairs
"""
print("Running intra-match won consistency check...")
consistency_df = con.execute(consistency_sql).df()
print("\n=== Intra-match won consistency (2-row matches) ===")
print(consistency_df.to_string(index=False))

# %%
findings["won_consistency_2row"] = consistency_df.to_dict(orient="records")

# %%
# Verification: won distribution (deferred to 01_02_05 for plotting)
print("=== won distribution (feeds bar chart in 01_02_05) ===")
print(won_dist_df.to_string(index=False))

# %% [markdown]
# ## C. Match structure by leaderboard

# %%
match_struct_sql = """
SELECT
    leaderboard,
    COUNT(DISTINCT matchId) AS distinct_matches,
    COUNT(*) AS total_rows,
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT matchId), 2) AS avg_rows_per_match
FROM matches_raw
GROUP BY leaderboard
ORDER BY total_rows DESC
"""
print("Running match structure by leaderboard query...")
match_struct_df = con.execute(match_struct_sql).df()
print("\n=== Match structure by leaderboard ===")
print(match_struct_df.to_string(index=False))
findings["match_structure_by_leaderboard"] = match_struct_df.to_dict(orient="records")

# %% [markdown]
# ## D. Categorical field profiles

# %%
# Columns with full top-k value listing
cat_topk_cols = [
    "leaderboard", "civ", "map", "gameMode", "speed", "victory",
    "server", "country", "status", "difficulty", "startingAge",
    "endingAge", "gameVariant", "resources", "revealMap", "mapSize",
    "civilizationSet", "privacy", "scenario", "modDataset",
]

# %%
# Loop over categorical columns -- top 30 values each
cat_profiles: dict = {}
for col in cat_topk_cols:
    sql = f"""
    SELECT
        "{col}" AS value,
        COUNT(*) AS cnt,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
    FROM matches_raw
    GROUP BY "{col}"
    ORDER BY cnt DESC
    LIMIT 30
    """
    df = con.execute(sql).df()
    cat_profiles[col] = df.to_dict(orient="records")
    n_distinct = con.execute(
        f'SELECT COUNT(DISTINCT "{col}") FROM matches_raw'
    ).fetchone()[0]
    n_null = con.execute(
        f'SELECT COUNT(*) - COUNT("{col}") FROM matches_raw'
    ).fetchone()[0]
    print(f"\n--- {col} (cardinality={n_distinct}, nulls={n_null:,}) ---")
    print(df.head(15).to_string(index=False))

# %%
findings["categorical_profiles"] = cat_profiles

# %%
# name: cardinality only (millions of distinct values)
name_sql = """
SELECT
    COUNT(DISTINCT name) AS distinct_names,
    COUNT(*) - COUNT(name) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(name)) / COUNT(*), 2) AS null_pct
FROM matches_raw
"""
print("Running name cardinality query...")
name_df = con.execute(name_sql).df()
print("\n--- name (cardinality only) ---")
print(name_df.to_string(index=False))
findings["name_cardinality"] = name_df.to_dict(orient="records")

# %%
# colorHex: cardinality and NULL rate only
colorhex_sql = """
SELECT
    COUNT(DISTINCT "colorHex") AS distinct_values,
    COUNT(*) - COUNT("colorHex") AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT("colorHex")) / COUNT(*), 2) AS null_pct
FROM matches_raw
"""
colorhex_df = con.execute(colorhex_sql).df()
print("\n--- colorHex (cardinality only) ---")
print(colorhex_df.to_string(index=False))
findings["colorHex_cardinality"] = colorhex_df.to_dict(orient="records")

# %%
# Verification: categorical top-k profiles (deferred to 01_02_05 for plotting)
print("=== leaderboard, civ, map top-k (feeds bar charts in 01_02_05) ===")
for col in ["leaderboard", "civ", "map"]:
    print(f"\n--- {col} ---")
    print(pd.DataFrame(cat_profiles[col]).head(20).to_string(index=False))

# %% [markdown]
# ## E. Boolean field census

# %%
bool_cols = [
    "mod", "fullTechTree", "allowCheats", "empireWarsMode", "lockSpeed",
    "lockTeams", "hideCivs", "recordGame", "regicideMode",
    "sharedExploration", "suddenDeathMode", "antiquityMode",
    "teamPositions", "teamTogether", "turboMode", "password",
    "shared", "verified",
]

# %%
bool_records = []
for col in bool_cols:
    sql = f"""
    SELECT
        '{col}' AS column_name,
        COUNT(*) FILTER (WHERE "{col}" = TRUE) AS true_count,
        COUNT(*) FILTER (WHERE "{col}" = FALSE) AS false_count,
        COUNT(*) - COUNT("{col}") AS null_count
    FROM matches_raw
    """
    row = con.execute(sql).df().iloc[0]
    bool_records.append(row.to_dict())
    print(
        f"{col}: TRUE={int(row['true_count']):,}  "
        f"FALSE={int(row['false_count']):,}  "
        f"NULL={int(row['null_count']):,}"
    )

# %%
bool_census_df = pd.DataFrame(bool_records)
print("\n=== Boolean field census ===")
print(bool_census_df.to_string(index=False))
findings["boolean_census"] = bool_census_df.to_dict(orient="records")

# %% [markdown]
# ## F. Numeric descriptive statistics

# %% [markdown]
# ### F.1 matches_raw numerics

# %%
matches_numeric_cols = [
    "rating", "ratingDiff", "population", "slot", "color",
    "team", "speedFactor", "treatyLength", "internalLeaderboardId",
]

# %%
matches_numeric_stats = []
for col in matches_numeric_cols:
    sql = f"""
    SELECT
        '{col}' AS column_name,
        MIN("{col}") AS min_val,
        MAX("{col}") AS max_val,
        ROUND(AVG("{col}"), 2) AS mean_val,
        ROUND(MEDIAN("{col}"), 2) AS median_val,
        ROUND(STDDEV("{col}"), 2) AS stddev_val,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY "{col}") AS p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY "{col}") AS p25,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY "{col}") AS p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY "{col}") AS p95
    FROM matches_raw
    WHERE "{col}" IS NOT NULL
    """
    row = con.execute(sql).df().iloc[0]
    matches_numeric_stats.append(row.to_dict())
    print(f"\n--- {col} ---")
    print(row.to_string())

# %%
findings["matches_raw_numeric_stats"] = matches_numeric_stats

# %% [markdown]
# ### F.2 ratings_raw numerics

# %%
ratings_numeric_cols = [
    "rating", "games", "rating_diff", "leaderboard_id", "season",
]

# %%
ratings_numeric_stats = []
for col in ratings_numeric_cols:
    sql = f"""
    SELECT
        '{col}' AS column_name,
        MIN("{col}") AS min_val,
        MAX("{col}") AS max_val,
        ROUND(AVG("{col}"), 2) AS mean_val,
        ROUND(MEDIAN("{col}"), 2) AS median_val,
        ROUND(STDDEV("{col}"), 2) AS stddev_val,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY "{col}") AS p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY "{col}") AS p25,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY "{col}") AS p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY "{col}") AS p95
    FROM ratings_raw
    WHERE "{col}" IS NOT NULL
    """
    row = con.execute(sql).df().iloc[0]
    ratings_numeric_stats.append(row.to_dict())
    print(f"\n--- ratings_raw.{col} ---")
    print(row.to_string())

# %%
findings["ratings_raw_numeric_stats"] = ratings_numeric_stats

# %% [markdown]
# ### F.3 leaderboards_raw numerics

# %%
lb_numeric_cols = [
    "rank", "rating", "wins", "losses", "games",
    "streak", "drops", "rankCountry", "season", "rankLevel",
]

# %%
lb_numeric_stats = []
for col in lb_numeric_cols:
    sql = f"""
    SELECT
        '{col}' AS column_name,
        MIN("{col}") AS min_val,
        MAX("{col}") AS max_val,
        ROUND(AVG("{col}"), 2) AS mean_val,
        ROUND(MEDIAN("{col}"), 2) AS median_val,
        ROUND(STDDEV("{col}"), 2) AS stddev_val,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY "{col}") AS p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY "{col}") AS p25,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY "{col}") AS p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY "{col}") AS p95
    FROM leaderboards_raw
    WHERE "{col}" IS NOT NULL
    """
    row = con.execute(sql).df().iloc[0]
    lb_numeric_stats.append(row.to_dict())
    print(f"\n--- leaderboards_raw.{col} ---")
    print(row.to_string())

# %%
findings["leaderboards_raw_numeric_stats"] = lb_numeric_stats

# %% [markdown]
# ## F2. Zero counts for numeric columns
#
# EDA Manual Section 3.1: compute zero counts for all numeric columns.
# `profiles_raw` excluded -- its only numeric column (`profileId`) is an identifier;
# zero counts on identifiers are semantically meaningless.

# %%
matches_zero_cols = [
    "rating", "ratingDiff", "population", "slot", "color",
    "team", "speedFactor", "treatyLength", "internalLeaderboardId",
]
matches_zero_counts = []
for col in matches_zero_cols:
    sql = f"""
    SELECT
        '{col}' AS column_name,
        COUNT(*) FILTER (WHERE "{col}" = 0)                                                  AS zero_count,
        COUNT(*) FILTER (WHERE "{col}" IS NOT NULL)                                          AS non_null_count,
        ROUND(100.0 * COUNT(*) FILTER (WHERE "{col}" = 0)
            / NULLIF(COUNT(*) FILTER (WHERE "{col}" IS NOT NULL), 0), 2)                    AS zero_pct_of_non_null
    FROM matches_raw
    """
    row = con.execute(sql).df().iloc[0]
    matches_zero_counts.append(row.to_dict())
    print(f"matches_raw.{col}: zero_count={int(row['zero_count']):,}")
findings["matches_raw_zero_counts"] = matches_zero_counts

# %%
ratings_zero_cols = ["rating", "games", "rating_diff", "leaderboard_id", "season"]
ratings_zero_counts = []
for col in ratings_zero_cols:
    sql = f"""
    SELECT
        '{col}' AS column_name,
        COUNT(*) FILTER (WHERE "{col}" = 0)                                                  AS zero_count,
        COUNT(*) FILTER (WHERE "{col}" IS NOT NULL)                                          AS non_null_count,
        ROUND(100.0 * COUNT(*) FILTER (WHERE "{col}" = 0)
            / NULLIF(COUNT(*) FILTER (WHERE "{col}" IS NOT NULL), 0), 2)                    AS zero_pct_of_non_null
    FROM ratings_raw
    """
    row = con.execute(sql).df().iloc[0]
    ratings_zero_counts.append(row.to_dict())
    print(f"ratings_raw.{col}: zero_count={int(row['zero_count']):,}")
findings["ratings_raw_zero_counts"] = ratings_zero_counts

# %%
lb_zero_cols = [
    "rank", "rating", "wins", "losses", "games",
    "streak", "drops", "rankCountry", "season", "rankLevel"
]
lb_zero_counts = []
for col in lb_zero_cols:
    sql = f"""
    SELECT
        '{col}' AS column_name,
        COUNT(*) FILTER (WHERE "{col}" = 0)                                                  AS zero_count,
        COUNT(*) FILTER (WHERE "{col}" IS NOT NULL)                                          AS non_null_count,
        ROUND(100.0 * COUNT(*) FILTER (WHERE "{col}" = 0)
            / NULLIF(COUNT(*) FILTER (WHERE "{col}" IS NOT NULL), 0), 2)                    AS zero_pct_of_non_null
    FROM leaderboards_raw
    """
    row = con.execute(sql).df().iloc[0]
    lb_zero_counts.append(row.to_dict())
    print(f"leaderboards_raw.{col}: zero_count={int(row['zero_count']):,}")
findings["leaderboards_raw_zero_counts"] = lb_zero_counts

# %% [markdown]
# ## F1b. Skewness and Kurtosis
#
# EDA Manual Section 3.1 requires skewness and kurtosis for all numeric columns.

# %%
# T02: Skewness and kurtosis for matches_raw numeric columns
matches_skew_kurtosis_cols = [
    "rating", "ratingDiff", "population", "slot", "color",
    "team", "speedFactor", "treatyLength", "internalLeaderboardId",
]
matches_skew_kurtosis = []
for col in matches_skew_kurtosis_cols:
    sql = f"""
    SELECT
        '{col}' AS column_name,
        ROUND(SKEWNESS("{col}"), 4) AS skewness,
        ROUND(KURTOSIS("{col}"), 4) AS kurtosis
    FROM matches_raw
    WHERE "{col}" IS NOT NULL
    """
    row = con.execute(sql).df().iloc[0]
    matches_skew_kurtosis.append(row.to_dict())
    print(f"matches_raw.{col}: skewness={row['skewness']}, kurtosis={row['kurtosis']}")
findings["matches_raw_skew_kurtosis"] = matches_skew_kurtosis
print("\n=== matches_raw skewness/kurtosis ===")
print(pd.DataFrame(matches_skew_kurtosis).to_string(index=False))

# %%
# T02: Skewness and kurtosis for ratings_raw numeric columns (5 cols)
ratings_skew_kurtosis_cols = ["leaderboard_id", "season", "rating", "games", "rating_diff"]
ratings_skew_kurtosis = []
for col in ratings_skew_kurtosis_cols:
    sql = f"""
    SELECT
        '{col}' AS column_name,
        ROUND(SKEWNESS("{col}"), 4) AS skewness,
        ROUND(KURTOSIS("{col}"), 4) AS kurtosis
    FROM ratings_raw
    WHERE "{col}" IS NOT NULL
    """
    row = con.execute(sql).df().iloc[0]
    ratings_skew_kurtosis.append(row.to_dict())
    print(f"ratings_raw.{col}: skewness={row['skewness']}, kurtosis={row['kurtosis']}")
findings["ratings_raw_skew_kurtosis"] = ratings_skew_kurtosis
print("\n=== ratings_raw skewness/kurtosis ===")
print(pd.DataFrame(ratings_skew_kurtosis).to_string(index=False))

# %%
# T02: Skewness and kurtosis for leaderboards_raw numeric columns
lb_skew_kurtosis_cols = [
    "rank", "rating", "wins", "losses", "games",
    "streak", "drops", "rankCountry", "season", "rankLevel",
]
lb_skew_kurtosis = []
for col in lb_skew_kurtosis_cols:
    sql = f"""
    SELECT
        '{col}' AS column_name,
        ROUND(SKEWNESS("{col}"), 4) AS skewness,
        ROUND(KURTOSIS("{col}"), 4) AS kurtosis
    FROM leaderboards_raw
    WHERE "{col}" IS NOT NULL
    """
    row = con.execute(sql).df().iloc[0]
    lb_skew_kurtosis.append(row.to_dict())
    print(f"leaderboards_raw.{col}: skewness={row['skewness']}, kurtosis={row['kurtosis']}")
findings["leaderboards_raw_skew_kurtosis"] = lb_skew_kurtosis
print("\n=== leaderboards_raw skewness/kurtosis ===")
print(pd.DataFrame(lb_skew_kurtosis).to_string(index=False))

# %% [markdown]
# ### F.4 Histograms and boxplots

# %%
# Fetch histogram data for key columns via DuckDB histogram bins
# matches_raw.rating
rating_hist_sql = """
SELECT
    (FLOOR(rating / 100) * 100)::INTEGER AS bin,
    COUNT(*) AS cnt
FROM matches_raw
WHERE rating IS NOT NULL
GROUP BY bin
ORDER BY bin
"""
rating_hist_df = con.execute(rating_hist_sql).df()

# %%
# matches_raw.ratingDiff
ratingdiff_hist_sql = """
SELECT
    (FLOOR("ratingDiff" / 10) * 10)::INTEGER AS bin,
    COUNT(*) AS cnt
FROM matches_raw
WHERE "ratingDiff" IS NOT NULL
GROUP BY bin
ORDER BY bin
"""
ratingdiff_hist_df = con.execute(ratingdiff_hist_sql).df()

# %%
# ratings_raw.rating
ratings_rating_hist_sql = """
SELECT
    (FLOOR(rating / 100) * 100)::INTEGER AS bin,
    COUNT(*) AS cnt
FROM ratings_raw
WHERE rating IS NOT NULL
GROUP BY bin
ORDER BY bin
"""
ratings_rating_hist_df = con.execute(ratings_rating_hist_sql).df()

# %%
# leaderboards_raw.rating
lb_rating_hist_sql = """
SELECT
    (FLOOR(rating / 100) * 100)::INTEGER AS bin,
    COUNT(*) AS cnt
FROM leaderboards_raw
WHERE rating IS NOT NULL
GROUP BY bin
ORDER BY bin
"""
lb_rating_hist_df = con.execute(lb_rating_hist_sql).df()

# %%
# Verification: rating histograms (deferred to 01_02_05 for plotting)
print("=== matches_raw.rating histogram bins (feeds histogram in 01_02_05) ===")
print(rating_hist_df.to_string(index=False))
print("\n=== matches_raw.ratingDiff histogram bins (feeds histogram in 01_02_05) ===")
print(ratingdiff_hist_df.to_string(index=False))
print("\n=== ratings_raw.rating histogram bins (feeds histogram in 01_02_05) ===")
print(ratings_rating_hist_df.to_string(index=False))
print("\n=== leaderboards_raw.rating histogram bins (feeds histogram in 01_02_05) ===")
print(lb_rating_hist_df.to_string(index=False))

# %%
# Verification: boxplot percentile data for rating and ratingDiff (deferred to 01_02_05)
boxplot_data = []
boxplot_labels = []
for stats_list, prefix in [
    (matches_numeric_stats, "m."),
    (ratings_numeric_stats, "r."),
    (lb_numeric_stats, "lb."),
]:
    for s in stats_list:
        if s["column_name"] in ("rating", "ratingDiff"):
            boxplot_labels.append(f"{prefix}{s['column_name']}")
            boxplot_data.append(s)

print("=== Numeric boxplot data (p05/p25/p50/p75/p95) -- feeds boxplot in 01_02_05 ===")
boxplot_summary_df = pd.DataFrame([
    {
        "label": label,
        "p05": s["p05"],
        "p25": s["p25"],
        "median": s["median_val"],
        "p75": s["p75"],
        "p95": s["p95"],
    }
    for label, s in zip(boxplot_labels, boxplot_data)
])
print(boxplot_summary_df.to_string(index=False))

# %% [markdown]
# ## G. Temporal range

# %%
temporal_range_sql = """
SELECT
    MIN(started) AS earliest_match,
    MAX(started) AS latest_match,
    MIN(finished) AS earliest_finish,
    MAX(finished) AS latest_finish,
    COUNT(DISTINCT CAST(started AS DATE)) AS distinct_match_dates
FROM matches_raw
"""
print("Running temporal range query...")
temporal_df = con.execute(temporal_range_sql).df()
print("\n=== Temporal range (matches_raw) ===")
print(temporal_df.to_string(index=False))
findings["temporal_range_matches"] = temporal_df.to_dict(orient="records")

# %%
ratings_temporal_sql = """
SELECT
    MIN(date) AS earliest_rating,
    MAX(date) AS latest_rating,
    COUNT(DISTINCT CAST(date AS DATE)) AS distinct_rating_dates
FROM ratings_raw
"""
ratings_temporal_df = con.execute(ratings_temporal_sql).df()
print("\n=== Temporal range (ratings_raw) ===")
print(ratings_temporal_df.to_string(index=False))
findings["temporal_range_ratings"] = ratings_temporal_df.to_dict(orient="records")

# %%
duration_sql = """
SELECT
    ROUND(AVG(EXTRACT(EPOCH FROM (finished - started))), 2) AS avg_duration_secs,
    ROUND(MEDIAN(EXTRACT(EPOCH FROM (finished - started))), 2)
        AS median_duration_secs,
    MIN(EXTRACT(EPOCH FROM (finished - started))) AS min_duration_secs,
    MAX(EXTRACT(EPOCH FROM (finished - started))) AS max_duration_secs,
    PERCENTILE_CONT(0.05) WITHIN GROUP
        (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p05_secs,
    PERCENTILE_CONT(0.95) WITHIN GROUP
        (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p95_secs
FROM matches_raw
WHERE finished > started
"""
print("Running match duration distribution query...")
duration_df = con.execute(duration_sql).df()
print("\n=== Match duration distribution (seconds) ===")
print(duration_df.to_string(index=False))
findings["match_duration_stats"] = duration_df.to_dict(orient="records")

# %%
# Excluded rows count
excluded_sql = """
SELECT
    COUNT(*) FILTER (WHERE finished IS NULL OR started IS NULL)
        AS null_timestamp_count,
    COUNT(*) FILTER (WHERE finished IS NOT NULL AND started IS NOT NULL
        AND finished <= started)
        AS non_positive_duration_count
FROM matches_raw
"""
excluded_df = con.execute(excluded_sql).df()
print("\n=== Excluded from duration calculation ===")
print(excluded_df.to_string(index=False))
findings["duration_excluded_rows"] = excluded_df.to_dict(orient="records")

# %%
# Time-series: monthly match counts
monthly_sql = """
SELECT
    DATE_TRUNC('month', started) AS month,
    COUNT(DISTINCT matchId) AS distinct_matches,
    COUNT(*) AS total_rows
FROM matches_raw
WHERE started IS NOT NULL
GROUP BY month
ORDER BY month
"""
monthly_df = con.execute(monthly_sql).df()
print(f"\nMonthly buckets: {len(monthly_df)} months")

# %%
# Verification: monthly match counts (deferred to 01_02_05 for line chart)
print("=== Monthly match counts (feeds line chart in 01_02_05) ===")
print(monthly_df.to_string(index=False))

# %% [markdown]
# ## H. Auxiliary table NULL census

# %% [markdown]
# ### H.1 leaderboards_raw (19 columns)

# %%
print("Running SUMMARIZE on leaderboards_raw...")
lb_summarize = con.execute("SUMMARIZE leaderboards_raw").df()
lb_total = con.execute(
    "SELECT COUNT(*) FROM leaderboards_raw"
).fetchone()[0]
print(f"leaderboards_raw total rows: {lb_total:,}")

# %%
lb_null_census = lb_summarize[["column_name", "null_percentage"]].copy()
lb_null_census["total_rows"] = lb_total
lb_null_census["null_count"] = (
    (lb_null_census["null_percentage"] / 100.0 * lb_total).round(0).astype(int)
)
lb_null_census["null_pct"] = lb_null_census["null_percentage"]
lb_null_census["approx_cardinality"] = lb_summarize["approx_unique"].astype(int)

print("\n=== leaderboards_raw NULL census (all 19 columns) ===")
print(
    lb_null_census[
        ["column_name", "total_rows", "null_count", "null_pct", "approx_cardinality"]
    ].to_string(index=False)
)

# %%
findings["leaderboards_raw_null_census"] = (
    lb_null_census[
        ["column_name", "total_rows", "null_count", "null_pct", "approx_cardinality"]
    ].to_dict(orient="records")
)
findings["leaderboards_raw_total_rows"] = int(lb_total)

# %% [markdown]
# ### H.2 profiles_raw (14 columns)

# %%
print("Running SUMMARIZE on profiles_raw...")
pr_summarize = con.execute("SUMMARIZE profiles_raw").df()
pr_total = con.execute(
    "SELECT COUNT(*) FROM profiles_raw"
).fetchone()[0]
print(f"profiles_raw total rows: {pr_total:,}")

# %%
pr_null_census = pr_summarize[["column_name", "null_percentage"]].copy()
pr_null_census["total_rows"] = pr_total
pr_null_census["null_count"] = (
    (pr_null_census["null_percentage"] / 100.0 * pr_total).round(0).astype(int)
)
pr_null_census["null_pct"] = pr_null_census["null_percentage"]
pr_null_census["approx_cardinality"] = pr_summarize["approx_unique"].astype(int)

print("\n=== profiles_raw NULL census (all 14 columns) ===")
print(
    pr_null_census[
        ["column_name", "total_rows", "null_count", "null_pct", "approx_cardinality"]
    ].to_string(index=False)
)

# %%
findings["profiles_raw_null_census"] = (
    pr_null_census[
        ["column_name", "total_rows", "null_count", "null_pct", "approx_cardinality"]
    ].to_dict(orient="records")
)
findings["profiles_raw_total_rows"] = int(pr_total)

# %% [markdown]
# ### H.3 ratings_raw (8 columns)

# %%
print("Running SUMMARIZE on ratings_raw...")
rt_summarize = con.execute("SUMMARIZE ratings_raw").df()
rt_total = con.execute(
    "SELECT COUNT(*) FROM ratings_raw"
).fetchone()[0]
print(f"ratings_raw total rows: {rt_total:,}")

# %%
rt_null_census = rt_summarize[["column_name", "null_percentage"]].copy()
rt_null_census["total_rows"] = rt_total
rt_null_census["null_count"] = (
    (rt_null_census["null_percentage"] / 100.0 * rt_total).round(0).astype(int)
)
rt_null_census["null_pct"] = rt_null_census["null_percentage"]
rt_null_census["approx_cardinality"] = rt_summarize["approx_unique"].astype(int)

print("\n=== ratings_raw NULL census (all 8 columns) ===")
print(
    rt_null_census[
        ["column_name", "total_rows", "null_count", "null_pct", "approx_cardinality"]
    ].to_string(index=False)
)

# %%
findings["ratings_raw_null_census"] = (
    rt_null_census[
        ["column_name", "total_rows", "null_count", "null_pct", "approx_cardinality"]
    ].to_dict(orient="records")
)
findings["ratings_raw_total_rows"] = int(rt_total)

# %% [markdown]
# ### H.1b leaderboards_raw categorical, boolean, and temporal
#
# T03: leaderboards_raw categorical (leaderboard, country), boolean (active),
# and temporal (lastMatchTime, updatedAt) profiling.

# %%
# T03: leaderboard VARCHAR -- all values (low cardinality)
lb_leaderboard_sql = """
SELECT
    leaderboard AS value,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM leaderboards_raw
GROUP BY leaderboard
ORDER BY cnt DESC
"""
lb_leaderboard_df = con.execute(lb_leaderboard_sql).df()
print("=== leaderboards_raw.leaderboard distribution ===")
print(lb_leaderboard_df.to_string(index=False))

# %%
# T03: country VARCHAR -- top 30 + NULL count
lb_country_sql = """
SELECT country AS value, COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM leaderboards_raw GROUP BY country ORDER BY cnt DESC LIMIT 30
"""
lb_country_df = con.execute(lb_country_sql).df()
lb_country_null_count = con.execute(
    "SELECT COUNT(*) - COUNT(country) FROM leaderboards_raw"
).fetchone()[0]
print(f"\n=== leaderboards_raw.country top 30 (null_count={lb_country_null_count:,}) ===")
print(lb_country_df.to_string(index=False))

# %%
# T03: boolean census for active
lb_boolean_sql = """
SELECT 'active' AS column_name,
    COUNT(*) FILTER (WHERE active = TRUE) AS true_count,
    COUNT(*) FILTER (WHERE active = FALSE) AS false_count,
    COUNT(*) - COUNT(active) AS null_count,
    COUNT(*) AS total_rows,
    ROUND(100.0 * COUNT(*) FILTER (WHERE active = TRUE) / COUNT(*), 2) AS true_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE active = FALSE) / COUNT(*), 2) AS false_pct,
    ROUND(100.0 * (COUNT(*) - COUNT(active)) / COUNT(*), 2) AS null_pct
FROM leaderboards_raw
"""
lb_boolean_df = con.execute(lb_boolean_sql).df()
print("\n=== leaderboards_raw boolean census (active) ===")
print(lb_boolean_df.to_string(index=False))

# %%
# T03: temporal range for lastMatchTime and updatedAt
lb_temporal_sql = """
SELECT
    'lastMatchTime' AS column_name,
    MIN("lastMatchTime") AS min_val,
    MAX("lastMatchTime") AS max_val
FROM leaderboards_raw
UNION ALL
SELECT
    'updatedAt' AS column_name,
    MIN("updatedAt") AS min_val,
    MAX("updatedAt") AS max_val
FROM leaderboards_raw
"""
lb_temporal_df = con.execute(lb_temporal_sql).df()
print("\n=== leaderboards_raw temporal ranges ===")
print(lb_temporal_df.to_string(index=False))

# %%
# T03: ratings_raw leaderboard_id distribution
rt_lb_id_sql = """
SELECT leaderboard_id AS value, COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM ratings_raw GROUP BY leaderboard_id ORDER BY cnt DESC
"""
rt_lb_id_df = con.execute(rt_lb_id_sql).df()
print("\n=== ratings_raw.leaderboard_id distribution ===")
print(rt_lb_id_df.to_string(index=False))

# %%
findings["leaderboards_raw_categorical"] = {
    "leaderboard": lb_leaderboard_df.to_dict(orient="records"),
    "country": {
        "top_30": lb_country_df.to_dict(orient="records"),
        "null_count": int(lb_country_null_count),
    },
}
findings["leaderboards_raw_boolean"] = lb_boolean_df.to_dict(orient="records")
findings["leaderboards_raw_temporal"] = lb_temporal_df.to_dict(orient="records")
findings["ratings_raw_leaderboard_id_distribution"] = rt_lb_id_df.to_dict(orient="records")

# %% [markdown]
# ### H.2b profiles_raw categorical
#
# T04: categorical profiling for profiles_raw country and clan columns.
# Note: 7 dead columns (sharedHistory, twitchChannel, youtubeChannel,
# youtubeChannelName, discordId, discordName, discordInvitation) are documented
# in constant_fields (see Section I).

# %%
# T04: country VARCHAR -- top 30 + NULL count and NULL pct
pr_country_sql = """
SELECT country AS value, COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM profiles_raw GROUP BY country ORDER BY cnt DESC LIMIT 30
"""
pr_country_df = con.execute(pr_country_sql).df()
pr_country_null_count = con.execute(
    "SELECT COUNT(*) - COUNT(country) FROM profiles_raw"
).fetchone()[0]
pr_country_null_pct = round(100.0 * pr_country_null_count / pr_total, 2)
print(f"=== profiles_raw.country top 30 (null_count={pr_country_null_count:,}, null_pct={pr_country_null_pct}%) ===")
print(pr_country_df.to_string(index=False))

# %%
# T04: clan VARCHAR -- top 30 + cardinality + null count
pr_clan_sql = """
SELECT clan AS value, COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM profiles_raw GROUP BY clan ORDER BY cnt DESC LIMIT 30
"""
pr_clan_df = con.execute(pr_clan_sql).df()
pr_clan_cardinality = con.execute(
    "SELECT COUNT(DISTINCT clan) FROM profiles_raw"
).fetchone()[0]
pr_clan_null_count = con.execute(
    "SELECT COUNT(*) - COUNT(clan) FROM profiles_raw"
).fetchone()[0]
print(f"\n=== profiles_raw.clan top 30 (cardinality={pr_clan_cardinality:,}, null_count={pr_clan_null_count:,}) ===")
print(pr_clan_df.to_string(index=False))

# %%
findings["profiles_raw_categorical"] = {
    "country": {
        "top_30": pr_country_df.to_dict(orient="records"),
        "null_count": int(pr_country_null_count),
        "null_pct": pr_country_null_pct,
    },
    "clan": {
        "top_30": pr_clan_df.to_dict(orient="records"),
        "cardinality": int(pr_clan_cardinality),
        "null_count": int(pr_clan_null_count),
    },
}

# %% [markdown]
# ## I2. Duplicate row detection
#
# T05: Check for duplicate composite keys in matches_raw and ratings_raw.

# %%
# T05: matches_raw -- duplicate (matchId, profileId) pairs
dup_matches_sql = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT CAST("matchId" AS VARCHAR) || '|' || CAST("profileId" AS VARCHAR))
        AS distinct_pairs,
    COUNT(*) - COUNT(DISTINCT CAST("matchId" AS VARCHAR) || '|' || CAST("profileId" AS VARCHAR))
        AS duplicate_rows
FROM matches_raw
"""
dup_matches_df = con.execute(dup_matches_sql).df()
print("=== matches_raw duplicate check (matchId, profileId) ===")
print(dup_matches_df.to_string(index=False))

# %%
# T05: ratings_raw -- duplicate (profile_id, leaderboard_id, date) triples
dup_ratings_sql = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT CAST(profile_id AS VARCHAR) || '|'
        || CAST(leaderboard_id AS VARCHAR) || '|'
        || CAST(date AS VARCHAR))
        AS distinct_triples,
    COUNT(*) - COUNT(DISTINCT CAST(profile_id AS VARCHAR) || '|'
        || CAST(leaderboard_id AS VARCHAR) || '|'
        || CAST(date AS VARCHAR))
        AS duplicate_rows
FROM ratings_raw
"""
dup_ratings_df = con.execute(dup_ratings_sql).df()
print("\n=== ratings_raw duplicate check (profile_id, leaderboard_id, date) ===")
print(dup_ratings_df.to_string(index=False))

# %%
findings["matches_raw_duplicate_check"] = dup_matches_df.to_dict(orient="records")
findings["ratings_raw_duplicate_check"] = dup_ratings_df.to_dict(orient="records")

# %% [markdown]
# ## I3. NULL co-occurrence for 0.15%-0.16% clusters
#
# T06: Two distinct NULL clusters in matches_raw:
# - Cluster A (8 cols, null_count=415,649): allowCheats, lockSpeed, lockTeams,
#   recordGame, sharedExploration, teamPositions, teamTogether, turboMode
# - Cluster B (2 cols, null_count=443,358): fullTechTree, population
# Note: fullTechTree and population have a different null count from the 8-column
# cluster -- these are two separate clusters.

# %%
# T06: Cluster A -- are all 8 columns simultaneously NULL?
null_cooc_a_sql = """
SELECT
    COUNT(*) AS all_eight_null_simultaneously,
    (SELECT COUNT(*) FROM matches_raw WHERE "allowCheats" IS NULL)
        AS allowCheats_null_count
FROM matches_raw
WHERE "allowCheats" IS NULL
    AND "lockSpeed" IS NULL AND "lockTeams" IS NULL
    AND "recordGame" IS NULL AND "sharedExploration" IS NULL
    AND "teamPositions" IS NULL AND "teamTogether" IS NULL
    AND "turboMode" IS NULL
"""
null_cooc_a_df = con.execute(null_cooc_a_sql).df()
print("=== Cluster A NULL co-occurrence (8 columns) ===")
print(null_cooc_a_df.to_string(index=False))

# %%
# T06: Cluster B -- are fullTechTree and population simultaneously NULL?
null_cooc_b_sql = """
SELECT
    COUNT(*) AS both_null,
    (SELECT COUNT(*) FROM matches_raw WHERE "fullTechTree" IS NULL)
        AS fullTechTree_null_count,
    (SELECT COUNT(*) FROM matches_raw WHERE population IS NULL)
        AS population_null_count
FROM matches_raw
WHERE "fullTechTree" IS NULL AND population IS NULL
"""
null_cooc_b_df = con.execute(null_cooc_b_sql).df()
print("\n=== Cluster B NULL co-occurrence (fullTechTree, population) ===")
print(null_cooc_b_df.to_string(index=False))

# %%
# T06: Cross-cluster overlap -- are Cluster A NULLs a subset of Cluster B NULLs?
null_cooc_cross_sql = """
SELECT
    COUNT(*) FILTER (WHERE "allowCheats" IS NULL AND "fullTechTree" IS NULL)
        AS both_clusters_null,
    COUNT(*) FILTER (WHERE "allowCheats" IS NULL AND "fullTechTree" IS NOT NULL)
        AS cluster_a_only_null,
    COUNT(*) FILTER (WHERE "allowCheats" IS NOT NULL AND "fullTechTree" IS NULL)
        AS cluster_b_only_null
FROM matches_raw
"""
null_cooc_cross_df = con.execute(null_cooc_cross_sql).df()
print("\n=== Cross-cluster overlap (Cluster A vs Cluster B) ===")
print(null_cooc_cross_df.to_string(index=False))

# %%
findings["matches_raw_null_cooccurrence"] = {
    "cluster_a_eight_cols": null_cooc_a_df.to_dict(orient="records"),
    "cluster_b_fulltree_population": null_cooc_b_df.to_dict(orient="records"),
    "cross_cluster_overlap": null_cooc_cross_df.to_dict(orient="records"),
}

# %% [markdown]
# ## Post-game field annotations (Invariant #3)
#
# Columns that encode match outcome -- using these as prediction features would
# be temporal leakage.

# %%
findings["post_game_fields"] = [
    {
        "table": "matches_raw",
        "column": "ratingDiff",
        "type": "INTEGER",
        "reason": (
            "Rating change resulting from match outcome. Using this to predict "
            "the match it encodes would be temporal leakage (Invariant #3)."
        )
    },
    {
        "table": "ratings_raw",
        "column": "rating_diff",
        "type": "BIGINT",
        "reason": (
            "Rating change resulting from match outcome. Semantically identical "
            "to matches_raw.ratingDiff. Using this to predict the match it "
            "encodes would be temporal leakage (Invariant #3)."
        )
    },
    {
        "table": "matches_raw",
        "column": "won",
        "type": "BOOLEAN",
        "reason": "Prediction target. Post-game by definition."
    },
    {
        "table": "matches_raw",
        "column": "finished",
        "type": "TIMESTAMP",
        "reason": "Match end timestamp. Known only after match completes."
    },
]
print("Post-game field annotations recorded.")

# %% [markdown]
# ## Field Classification (preliminary)
#
# Preliminary pre-game/post-game classification for all 55 matches_raw columns.
# Formal boundary deferred to Phase 02 (Feature Engineering).

# %%
field_classification = {
    "table": "matches_raw",
    "classification_status": "preliminary",
    "formal_boundary_deferred_to": "Phase 02 (Feature Engineering)",
    "classification_notes": {
        "pre_game": "Known before match starts. Usable as prediction features without temporal leakage.",
        "post_game": "Known only after match ends. Using as feature is temporal leakage (Invariant #3).",
        "ambiguous_pre_or_post": "Temporal status unknown; requires Phase 02 investigation before use.",
        "identifier": "Player/match identity columns. Not features.",
        "target": "Prediction target. Never a feature.",
        "context": "Player-level metadata with unclear temporal availability; not match settings and not match outcomes.",
    },
    "fields": [
        # Identifiers
        {"column": "matchId",              "temporal_class": "identifier",            "notes": "Match identifier"},
        {"column": "profileId",            "temporal_class": "identifier",            "notes": "Player identifier"},
        {"column": "name",                 "temporal_class": "identifier",            "notes": "Player name"},
        {"column": "filename",             "temporal_class": "identifier",            "notes": "Source file provenance (I10)"},
        # Target
        {"column": "won",                  "temporal_class": "target",               "notes": "Prediction target"},
        # Post-game
        {"column": "ratingDiff",           "temporal_class": "post_game",            "notes": "Rating change from match outcome (Invariant #3)"},
        {"column": "finished",             "temporal_class": "post_game",            "notes": "Match end timestamp"},
        # Ambiguous -- needs Phase 02 investigation
        {"column": "rating",               "temporal_class": "ambiguous_pre_or_post", "notes": "Could be pre-match or post-match snapshot -- identical 42.46% NULL rate suggests co-occurrence with ratingDiff (unverified; needs row-level check)"},
        # Pre-game (match settings)
        {"column": "started",              "temporal_class": "pre_game",             "notes": "Match start timestamp"},
        {"column": "leaderboard",          "temporal_class": "pre_game",             "notes": "Ranked queue / game mode"},
        {"column": "internalLeaderboardId","temporal_class": "pre_game",             "notes": "Numeric leaderboard ID"},
        {"column": "map",                  "temporal_class": "pre_game",             "notes": "Map selection"},
        {"column": "mapSize",              "temporal_class": "pre_game",             "notes": "Map size setting"},
        {"column": "civ",                  "temporal_class": "pre_game",             "notes": "Civilization selection"},
        {"column": "gameMode",             "temporal_class": "pre_game",             "notes": "Game mode"},
        {"column": "gameVariant",          "temporal_class": "pre_game",             "notes": "Game variant"},
        {"column": "speed",                "temporal_class": "pre_game",             "notes": "Game speed setting"},
        {"column": "speedFactor",          "temporal_class": "pre_game",             "notes": "Speed multiplier"},
        {"column": "population",           "temporal_class": "pre_game",             "notes": "Population cap"},
        {"column": "resources",            "temporal_class": "pre_game",             "notes": "Resource setting"},
        {"column": "startingAge",          "temporal_class": "pre_game",             "notes": "Starting age setting"},
        {"column": "endingAge",            "temporal_class": "pre_game",             "notes": "Ending age setting"},
        {"column": "victory",              "temporal_class": "pre_game",             "notes": "Victory condition"},
        {"column": "difficulty",           "temporal_class": "pre_game",             "notes": "AI difficulty setting"},
        {"column": "civilizationSet",      "temporal_class": "pre_game",             "notes": "Civ set restriction"},
        {"column": "revealMap",            "temporal_class": "pre_game",             "notes": "Map visibility setting"},
        {"column": "treatyLength",         "temporal_class": "pre_game",             "notes": "Treaty length setting"},
        {"column": "mod",                  "temporal_class": "pre_game",             "notes": "Mod enabled flag"},
        {"column": "fullTechTree",         "temporal_class": "pre_game",             "notes": "Full tech tree toggle"},
        {"column": "allowCheats",          "temporal_class": "pre_game",             "notes": "Cheats toggle"},
        {"column": "empireWarsMode",       "temporal_class": "pre_game",             "notes": "Empire Wars toggle"},
        {"column": "lockSpeed",            "temporal_class": "pre_game",             "notes": "Lock speed toggle"},
        {"column": "lockTeams",            "temporal_class": "pre_game",             "notes": "Lock teams toggle"},
        {"column": "hideCivs",             "temporal_class": "pre_game",             "notes": "Hide civs toggle"},
        {"column": "recordGame",           "temporal_class": "pre_game",             "notes": "Record game toggle"},
        {"column": "regicideMode",         "temporal_class": "pre_game",             "notes": "Regicide toggle"},
        {"column": "sharedExploration",    "temporal_class": "pre_game",             "notes": "Shared exploration toggle"},
        {"column": "suddenDeathMode",      "temporal_class": "pre_game",             "notes": "Sudden death toggle"},
        {"column": "antiquityMode",        "temporal_class": "pre_game",             "notes": "Antiquity mode toggle"},
        {"column": "teamPositions",        "temporal_class": "pre_game",             "notes": "Team positions toggle"},
        {"column": "teamTogether",         "temporal_class": "pre_game",             "notes": "Team together toggle"},
        {"column": "turboMode",            "temporal_class": "pre_game",             "notes": "Turbo mode toggle"},
        {"column": "color",                "temporal_class": "pre_game",             "notes": "Player color slot"},
        {"column": "colorHex",             "temporal_class": "pre_game",             "notes": "Player color hex code"},
        {"column": "slot",                 "temporal_class": "pre_game",             "notes": "Player slot number"},
        {"column": "team",                 "temporal_class": "pre_game",             "notes": "Team assignment"},
        {"column": "password",             "temporal_class": "pre_game",             "notes": "Password-protected match (BOOLEAN, 82.9% NULL)"},
        {"column": "scenario",             "temporal_class": "pre_game",             "notes": "Scenario name (98.27% NULL)"},
        {"column": "modDataset",           "temporal_class": "pre_game",             "notes": "Mod dataset name (99.72% NULL)"},
        # Context
        {"column": "server",               "temporal_class": "context",              "notes": "Server (97.99% NULL)"},
        {"column": "privacy",              "temporal_class": "context",              "notes": "Player privacy setting"},
        {"column": "status",               "temporal_class": "context",              "notes": "Player status"},
        {"column": "country",              "temporal_class": "context",              "notes": "Player country"},
        {"column": "shared",               "temporal_class": "context",              "notes": "Shared flag"},
        {"column": "verified",             "temporal_class": "context",              "notes": "Verified flag"},
    ]
}
findings["field_classification"] = field_classification
print(f"Field classification: {len(field_classification['fields'])} columns annotated")
assert len(field_classification["fields"]) == 55, (
    f"Expected 55 fields, got {len(field_classification['fields'])}"
)

# %% [markdown]
# ## I. Dead/constant/near-constant field detection
#
# - Cardinality = 1: constant (dead field)
# - Uniqueness ratio < 0.001: near-constant
# - Uniqueness ratio = COUNT(DISTINCT col) / COUNT(*) where denominator
#   includes NULLs (note: NULL deflation in denominator)

# %%
# T01: Combine census data from all four tables, including null_pct for dead-field fix
all_census = []
for table_name, census_df, total in [
    ("matches_raw", null_census_matches, total_rows),
    ("leaderboards_raw", lb_null_census, lb_total),
    ("profiles_raw", pr_null_census, pr_total),
    ("ratings_raw", rt_null_census, rt_total),
]:
    subset = census_df[["column_name", "approx_cardinality", "null_pct"]].copy()
    subset["table"] = table_name
    subset["total_rows"] = total
    subset["uniqueness_ratio"] = subset["approx_cardinality"] / total
    all_census.append(subset)
all_census_df = pd.concat(all_census, ignore_index=True)

# %%
# T01: Dead-field detection uses (approx_cardinality <= 1) OR (null_pct >= 100.0)
# The OR condition catches profiles_raw columns that are 100% NULL but have phantom
# HyperLogLog cardinalities > 1 due to approximation error (Flajolet et al. 2007).
constant_fields = all_census_df[
    (all_census_df["approx_cardinality"] <= 1) | (all_census_df["null_pct"] >= 100.0)
]

print(f"Dead fields detected: {len(constant_fields)}")
for _, row in constant_fields.iterrows():
    print(
        f"  {row['table']}.{row['column_name']} "
        f"(approx_cardinality={row['approx_cardinality']}, null_pct={row['null_pct']})"
    )

# %%
# T01: Assert the 7 profiles_raw dead columns are detected
expected_dead_profiles = {
    "sharedHistory", "twitchChannel", "youtubeChannel",
    "youtubeChannelName", "discordId", "discordName", "discordInvitation"
}
actual_dead_profiles = set(
    constant_fields.loc[constant_fields["table"] == "profiles_raw", "column_name"]
)
missing = expected_dead_profiles - actual_dead_profiles
assert not missing, f"BLOCKER: Dead profiles_raw columns missing: {missing}"
print(f"BLOCKER assertion passed: all 7 profiles_raw dead columns detected.")

# %%
# T08: Near-constant detection split into two buckets
# [I7] Empirical threshold: max clearly categorical cardinality is ~68 (civ);
# next meaningful categorical is map (~261) which falls above 100.
# Threshold of 100 cleanly separates low-cardinality semantically meaningful
# categoricals (leaderboard=22, civ=68) from map (261) and continuous columns.
# At N=277M rows, uniqueness_ratio < 0.001 flags all columns with < 277,000
# distinct values -- including semantically important categoricals.
NEAR_CONSTANT_CARDINALITY_THRESHOLD = 100  # empirical: max categorical=68 (civ), min ratio-flagged=261 (map)

# Bucket 1: genuinely low-cardinality (< 100 distinct values, not constant/dead)
near_constant_low_card = all_census_df[
    (all_census_df["uniqueness_ratio"] < 0.001)
    & (all_census_df["approx_cardinality"] > 1)
    & (all_census_df["approx_cardinality"] < NEAR_CONSTANT_CARDINALITY_THRESHOLD)
    & (all_census_df["null_pct"] < 100.0)
]
# Bucket 2: moderate-cardinality columns flagged only by ratio (NOT near-constant)
near_constant_ratio_flagged = all_census_df[
    (all_census_df["uniqueness_ratio"] < 0.001)
    & (all_census_df["approx_cardinality"] >= NEAR_CONSTANT_CARDINALITY_THRESHOLD)
]

print(f"\n=== Near-constant Bucket 1: low-cardinality (cardinality < {NEAR_CONSTANT_CARDINALITY_THRESHOLD}) ===")
if len(near_constant_low_card) > 0:
    print(near_constant_low_card.to_string(index=False))
else:
    print("None found.")

print(f"\n=== Near-constant Bucket 2: ratio-flagged only (cardinality >= {NEAR_CONSTANT_CARDINALITY_THRESHOLD}) ===")
print("(These include semantically important categoricals like map=261; NOT true near-constants.)")
if len(near_constant_ratio_flagged) > 0:
    print(near_constant_ratio_flagged.to_string(index=False))
else:
    print("None found.")

# %%
findings["constant_fields"] = constant_fields.to_dict(orient="records")
findings["near_constant_low_cardinality"] = near_constant_low_card.to_dict(orient="records")
findings["near_constant_ratio_flagged"] = near_constant_ratio_flagged.to_dict(orient="records")

# %% [markdown]
# ## J. Write artifacts
#
# Write JSON and markdown artifacts with all findings and SQL.

# %%
# Serialization helper -- convert non-serializable types
json_str = json.dumps(findings, indent=2, default=str)
json_path = artifacts_dir / "01_02_04_univariate_census.json"
Path(json_path).write_text(json_str)
print(f"JSON artifact saved: {json_path}")
print(f"JSON size: {len(json_str):,} bytes")

# %%
md_lines = [
    "# Step 01_02_04 -- Univariate Census & Target Variable EDA",
    "",
    "**Dataset:** aoe2companion",
    "**Date:** 2026-04-14",
    "",
    "All SQL queries that produced reported results are inlined below (Invariant #6).",
    "",
    "---",
    "",
    "## A. Full NULL census of matches_raw",
    "",
    "```sql",
    "SUMMARIZE matches_raw",
    "SELECT COUNT(*) AS n FROM matches_raw",
    "```",
    "",
    "## A2. Empty-string investigation for VARCHAR columns",
    "",
    "Investigates whether `difficulty`, `colorHex`, `startingAge`, `endingAge`, `civilizationSet`",
    "(0 NULLs per SUMMARIZE) contain empty strings. Also confirms genuine NULLs for `scenario`",
    "and `modDataset`. `password` (BOOLEAN) is excluded -- empty-string hypothesis does not apply.",
    "",
    "```sql",
    "-- Per column (col in empty_string_cols):",
    "SELECT",
    "    '{col}' AS column_name,",
    "    COUNT(*) FILTER (WHERE \"{col}\" IS NULL)                                AS null_count,",
    "    COUNT(*) FILTER (WHERE \"{col}\" = '')                                   AS empty_string_count,",
    "    COUNT(*) FILTER (WHERE \"{col}\" IS NOT NULL AND \"{col}\" != '')          AS non_empty_count,",
    "    COUNT(*)                                                               AS total_rows",
    "FROM matches_raw",
    "```",
    "",
    "## B. Target variable (won)",
    "",
    "### won NULL count: exact GROUP BY vs SUMMARIZE approximation",
    "",
    "SUMMARIZE uses HyperLogLog approximation. The exact NULL count is taken from",
    "the GROUP BY distribution query and patched into `matches_raw_null_census`.",
    "",
    "### Overall distribution",
    "```sql",
    won_dist_sql.strip(),
    "```",
    "",
    "### Stratified by leaderboard",
    "```sql",
    won_by_lb_sql.strip(),
    "```",
    "",
    "### Intra-match consistency check (2-row matches)",
    "```sql",
    consistency_sql.strip(),
    "```",
    "",
    "## C. Match structure by leaderboard",
    "",
    "```sql",
    match_struct_sql.strip(),
    "```",
    "",
    "## D. Categorical field profiles",
    "",
    "```sql",
    '-- Per column (col in categorical list):',
    'SELECT',
    '    "{col}" AS value,',
    '    COUNT(*) AS cnt,',
    '    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct',
    'FROM matches_raw',
    'GROUP BY "{col}"',
    'ORDER BY cnt DESC',
    'LIMIT 30',
    "```",
    "",
    "### name (cardinality only)",
    "```sql",
    name_sql.strip(),
    "```",
    "",
    "### colorHex (cardinality only)",
    "```sql",
    colorhex_sql.strip(),
    "```",
    "",
]

# %%
md_lines += [
    "## E. Boolean field census",
    "",
    "```sql",
    "-- Per boolean column:",
    "SELECT",
    "    '{col}' AS column_name,",
    '    COUNT(*) FILTER (WHERE "{col}" = TRUE) AS true_count,',
    '    COUNT(*) FILTER (WHERE "{col}" = FALSE) AS false_count,',
    '    COUNT(*) - COUNT("{col}") AS null_count',
    "FROM matches_raw",
    "```",
    "",
    "## F. Numeric descriptive statistics",
    "",
    "```sql",
    "-- Per numeric column (matches_raw, ratings_raw, leaderboards_raw):",
    "SELECT",
    "    '{col}' AS column_name,",
    '    MIN("{col}") AS min_val,',
    '    MAX("{col}") AS max_val,',
    '    ROUND(AVG("{col}"), 2) AS mean_val,',
    '    ROUND(MEDIAN("{col}"), 2) AS median_val,',
    '    ROUND(STDDEV("{col}"), 2) AS stddev_val,',
    "    PERCENTILE_CONT(0.05) WITHIN GROUP"
    ' (ORDER BY "{col}") AS p05,',
    "    PERCENTILE_CONT(0.25) WITHIN GROUP"
    ' (ORDER BY "{col}") AS p25,',
    "    PERCENTILE_CONT(0.75) WITHIN GROUP"
    ' (ORDER BY "{col}") AS p75,',
    "    PERCENTILE_CONT(0.95) WITHIN GROUP"
    ' (ORDER BY "{col}") AS p95',
    "FROM <table>",
    'WHERE "{col}" IS NOT NULL',
    "```",
    "",
    "## F2. Zero counts for numeric columns",
    "",
    "`profiles_raw` excluded -- its only numeric column (`profileId`) is an identifier.",
    "",
    "```sql",
    "-- Per column (col in numeric zero cols list, table in matches_raw / ratings_raw / leaderboards_raw):",
    "SELECT",
    "    '{col}' AS column_name,",
    "    COUNT(*) FILTER (WHERE \"{col}\" = 0)                                                  AS zero_count,",
    "    COUNT(*) FILTER (WHERE \"{col}\" IS NOT NULL)                                          AS non_null_count,",
    "    ROUND(100.0 * COUNT(*) FILTER (WHERE \"{col}\" = 0)",
    "        / NULLIF(COUNT(*) FILTER (WHERE \"{col}\" IS NOT NULL), 0), 2)                    AS zero_pct_of_non_null",
    "FROM <table>",
    "```",
    "",
    "## F1b. Skewness and Kurtosis (EDA Manual Section 3.1)",
    "",
    "```sql",
    "-- Per numeric column (col in numeric cols list, table in matches_raw / ratings_raw / leaderboards_raw):",
    "SELECT",
    "    '{col}' AS column_name,",
    '    ROUND(SKEWNESS("{col}"), 4) AS skewness,',
    '    ROUND(KURTOSIS("{col}"), 4) AS kurtosis',
    "FROM <table>",
    'WHERE "{col}" IS NOT NULL',
    "```",
    "",
    "matches_raw numeric columns (9): rating, ratingDiff, population, slot, color,",
    "    team, speedFactor, treatyLength, internalLeaderboardId",
    "ratings_raw numeric columns (5): leaderboard_id, season, rating, games, rating_diff",
    "leaderboards_raw numeric columns (10): rank, rating, wins, losses, games,",
    "    streak, drops, rankCountry, season, rankLevel",
    "",
    "## G. Temporal range",
    "",
    "### matches_raw temporal range",
    "```sql",
    temporal_range_sql.strip(),
    "```",
    "",
    "### ratings_raw temporal range",
    "```sql",
    ratings_temporal_sql.strip(),
    "```",
    "",
    "### Match duration distribution",
    "```sql",
    duration_sql.strip(),
    "```",
    "",
    "### Excluded rows",
    "```sql",
    excluded_sql.strip(),
    "```",
    "",
    "### Monthly match counts",
    "```sql",
    monthly_sql.strip(),
    "```",
    "",
]

# %%
md_lines += [
    "## H. Auxiliary table NULL census",
    "",
    "```sql",
    "SUMMARIZE leaderboards_raw",
    "SUMMARIZE profiles_raw",
    "SUMMARIZE ratings_raw",
    "SELECT COUNT(*) FROM leaderboards_raw",
    "SELECT COUNT(*) FROM profiles_raw",
    "SELECT COUNT(*) FROM ratings_raw",
    "```",
    "",
    "### H.1b leaderboards_raw categorical, boolean, and temporal",
    "",
    "#### leaderboard VARCHAR (all values)",
    "```sql",
    lb_leaderboard_sql.strip(),
    "```",
    "",
    "#### country VARCHAR (top 30)",
    "```sql",
    lb_country_sql.strip(),
    "```",
    "",
    "#### active BOOLEAN census",
    "```sql",
    lb_boolean_sql.strip(),
    "```",
    "",
    "#### lastMatchTime and updatedAt temporal ranges",
    "```sql",
    lb_temporal_sql.strip(),
    "```",
    "",
    "#### ratings_raw leaderboard_id distribution",
    "```sql",
    rt_lb_id_sql.strip(),
    "```",
    "",
    "### H.2b profiles_raw categorical",
    "",
    "Note: 7 dead columns documented in constant_fields (sharedHistory, twitchChannel,",
    "youtubeChannel, youtubeChannelName, discordId, discordName, discordInvitation).",
    "",
    "#### country VARCHAR (top 30)",
    "```sql",
    pr_country_sql.strip(),
    "```",
    "",
    "#### clan VARCHAR (top 30)",
    "```sql",
    pr_clan_sql.strip(),
    "```",
    "",
    "## I. Dead/constant/near-constant field detection",
    "",
    "### I.1 Dead fields (BLOCKER fix)",
    "",
    "Detection uses (approx_cardinality <= 1) OR (null_pct >= 100.0) -- the OR condition",
    "catches profiles_raw columns that are 100% NULL but have phantom HyperLogLog",
    "cardinalities > 1 due to approximation error (Flajolet et al. 2007).",
    "",
    "### I.2 Near-constant fields (two-bucket split, EDA Manual Section 3.3)",
    "",
    "**Threshold:** NEAR_CONSTANT_CARDINALITY_THRESHOLD = 100",
    "**Rationale (I7):** max clearly categorical cardinality is ~68 (civ); next meaningful",
    "categorical is map (~261). At N=277M rows, uniqueness_ratio < 0.001 flags all columns",
    "with < 277,000 distinct values -- including semantically important categoricals.",
    "",
    "- **Bucket 1 (near_constant_low_cardinality):** uniqueness_ratio < 0.001 AND",
    "  approx_cardinality in [2, 100) AND null_pct < 100 -- genuinely low-cardinality",
    "- **Bucket 2 (near_constant_ratio_flagged):** uniqueness_ratio < 0.001 AND",
    "  approx_cardinality >= 100 -- ratio-flagged but NOT true near-constants",
    "  (includes map=261, which is semantically important)",
    "",
    "### I2. Duplicate row detection",
    "",
    "#### matches_raw (matchId, profileId) pairs",
    "```sql",
    dup_matches_sql.strip(),
    "```",
    "",
    "#### ratings_raw (profile_id, leaderboard_id, date) triples",
    "```sql",
    dup_ratings_sql.strip(),
    "```",
    "",
    "### I3. NULL co-occurrence for 0.15%-0.16% clusters",
    "",
    "Two distinct NULL clusters:",
    "- **Cluster A** (8 cols, null_count=415,649): allowCheats, lockSpeed, lockTeams,",
    "  recordGame, sharedExploration, teamPositions, teamTogether, turboMode",
    "- **Cluster B** (2 cols, null_count=443,358): fullTechTree, population",
    "",
    "#### Cluster A co-occurrence",
    "```sql",
    null_cooc_a_sql.strip(),
    "```",
    "",
    "#### Cluster B co-occurrence",
    "```sql",
    null_cooc_b_sql.strip(),
    "```",
    "",
    "#### Cross-cluster overlap",
    "```sql",
    null_cooc_cross_sql.strip(),
    "```",
    "",
    "### T07. Memory footprint",
    "",
    "DuckDB file size recorded via `os.path.getsize(str(db._dataset.db_file))`.",
    "",
    "## Post-game field annotations (Invariant #3)",
    "",
    "Columns encoding match outcome -- temporal leakage risk if used as features.",
    "",
    "| table | column | type | reason |",
    "|-------|--------|------|--------|",
] + [
    f"| {f['table']} | {f['column']} | {f['type']} | {f['reason']} |"
    for f in findings["post_game_fields"]
] + [
    "",
    "## Field Classification (preliminary)",
    "",
    f"Table: matches_raw | Status: preliminary | Columns annotated: {len(findings['field_classification']['fields'])}",
    "",
    "Formal boundary deferred to Phase 02 (Feature Engineering).",
    "",
    "| column | temporal_class | notes |",
    "|--------|---------------|-------|",
] + [
    f"| {f['column']} | {f['temporal_class']} | {f['notes']} |"
    for f in findings["field_classification"]["fields"]
] + [
    "",
    "---",
    "",
    "*Generated by notebook "
    "01_02_04_univariate_census.py*",
]

md_text = "\n".join(md_lines)
md_path = artifacts_dir / "01_02_04_univariate_census.md"
Path(md_path).write_text(md_text)
print(f"Markdown artifact saved: {md_path}")

# %%
# Close DB connection
db.close()
print("Done. All artifacts written.")
