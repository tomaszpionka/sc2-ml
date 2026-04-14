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
# # Step 01_02_04 -- Univariate Census & Target Variable EDA: aoestats
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_02 -- EDA
# **Dataset:** aoestats
# **Question:** What are the univariate distributions, NULL rates, and value
# profiles for every column in `matches_raw` (18 cols) and `players_raw`
# (14 cols)? What is the target variable class balance? What fraction is 1v1?
# **Invariants applied:** #3 (temporal -- new_rating leakage note), #6
# (reproducibility -- SQL inlined in artifact), #7 (no magic numbers),
# #8 (cross-game -- target encoding documented), #9 (step scope: query)
# **Step scope:** query
# **Type:** Read-only -- no DuckDB writes, no new tables, no schema changes

# %%
import json
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import pandas as pd

from rts_predict.common.notebook_utils import get_reports_dir, setup_notebook_logging
from rts_predict.games.aoe2.config import AOESTATS_DB_FILE

logger = setup_notebook_logging()
logger.info("DB_FILE: %s", AOESTATS_DB_FILE)

# %%
con = duckdb.connect(str(AOESTATS_DB_FILE), read_only=True)
print(f"Connected (read-only): {AOESTATS_DB_FILE}")

# %%
artifacts_dir = (
    get_reports_dir("aoe2", "aoestats")
    / "artifacts" / "01_exploration" / "02_eda"
)
artifacts_dir.mkdir(parents=True, exist_ok=True)
plots_dir = artifacts_dir
print(f"Artifacts dir: {artifacts_dir}")

# %%
findings: dict = {}
sql_queries: dict = {}

# %% [markdown]
# ## T07: DuckDB memory footprint
#
# On-disk size of the DuckDB database file (EDA Manual Section 3.2).

# %%
import os
db_size_bytes = os.path.getsize(str(AOESTATS_DB_FILE))
print(f"DuckDB file size: {db_size_bytes:,} bytes ({db_size_bytes / 1e9:.2f} GB)")
findings["db_memory_footprint_bytes"] = db_size_bytes

# %% [markdown]
# ## Section A: Full NULL census of matches_raw
#
# All 18 columns -- count and percentage computed in SQL (Invariant #6).

# %%
MATCHES_NULL_SQL = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(map) AS map_null,
    ROUND(100.0 * (COUNT(*) - COUNT(map)) / COUNT(*), 2) AS map_null_pct,
    COUNT(*) - COUNT(started_timestamp) AS started_timestamp_null,
    ROUND(100.0 * (COUNT(*) - COUNT(started_timestamp)) / COUNT(*), 2) AS started_timestamp_null_pct,
    COUNT(*) - COUNT(duration) AS duration_null,
    ROUND(100.0 * (COUNT(*) - COUNT(duration)) / COUNT(*), 2) AS duration_null_pct,
    COUNT(*) - COUNT(irl_duration) AS irl_duration_null,
    ROUND(100.0 * (COUNT(*) - COUNT(irl_duration)) / COUNT(*), 2) AS irl_duration_null_pct,
    COUNT(*) - COUNT(game_id) AS game_id_null,
    ROUND(100.0 * (COUNT(*) - COUNT(game_id)) / COUNT(*), 2) AS game_id_null_pct,
    COUNT(*) - COUNT(avg_elo) AS avg_elo_null,
    ROUND(100.0 * (COUNT(*) - COUNT(avg_elo)) / COUNT(*), 2) AS avg_elo_null_pct,
    COUNT(*) - COUNT(num_players) AS num_players_null,
    ROUND(100.0 * (COUNT(*) - COUNT(num_players)) / COUNT(*), 2) AS num_players_null_pct,
    COUNT(*) - COUNT(team_0_elo) AS team_0_elo_null,
    ROUND(100.0 * (COUNT(*) - COUNT(team_0_elo)) / COUNT(*), 2) AS team_0_elo_null_pct,
    COUNT(*) - COUNT(team_1_elo) AS team_1_elo_null,
    ROUND(100.0 * (COUNT(*) - COUNT(team_1_elo)) / COUNT(*), 2) AS team_1_elo_null_pct,
    COUNT(*) - COUNT(replay_enhanced) AS replay_enhanced_null,
    ROUND(100.0 * (COUNT(*) - COUNT(replay_enhanced)) / COUNT(*), 2) AS replay_enhanced_null_pct,
    COUNT(*) - COUNT(leaderboard) AS leaderboard_null,
    ROUND(100.0 * (COUNT(*) - COUNT(leaderboard)) / COUNT(*), 2) AS leaderboard_null_pct,
    COUNT(*) - COUNT(mirror) AS mirror_null,
    ROUND(100.0 * (COUNT(*) - COUNT(mirror)) / COUNT(*), 2) AS mirror_null_pct,
    COUNT(*) - COUNT(patch) AS patch_null,
    ROUND(100.0 * (COUNT(*) - COUNT(patch)) / COUNT(*), 2) AS patch_null_pct,
    COUNT(*) - COUNT(raw_match_type) AS raw_match_type_null,
    ROUND(100.0 * (COUNT(*) - COUNT(raw_match_type)) / COUNT(*), 2) AS raw_match_type_null_pct,
    COUNT(*) - COUNT(game_type) AS game_type_null,
    ROUND(100.0 * (COUNT(*) - COUNT(game_type)) / COUNT(*), 2) AS game_type_null_pct,
    COUNT(*) - COUNT(game_speed) AS game_speed_null,
    ROUND(100.0 * (COUNT(*) - COUNT(game_speed)) / COUNT(*), 2) AS game_speed_null_pct,
    COUNT(*) - COUNT(starting_age) AS starting_age_null,
    ROUND(100.0 * (COUNT(*) - COUNT(starting_age)) / COUNT(*), 2) AS starting_age_null_pct,
    COUNT(*) - COUNT(filename) AS filename_null,
    ROUND(100.0 * (COUNT(*) - COUNT(filename)) / COUNT(*), 2) AS filename_null_pct
FROM matches_raw
"""
sql_queries["matches_null_census"] = MATCHES_NULL_SQL

# %%
raw_m = con.execute(MATCHES_NULL_SQL).df()
total_matches = int(raw_m["total_rows"].iloc[0])
print(f"matches_raw total rows: {total_matches:,}")

# %%
MATCHES_COLS = [
    "map", "started_timestamp", "duration", "irl_duration", "game_id",
    "avg_elo", "num_players", "team_0_elo", "team_1_elo",
    "replay_enhanced", "leaderboard", "mirror", "patch",
    "raw_match_type", "game_type", "game_speed", "starting_age",
    "filename",
]

rows = []
for col in MATCHES_COLS:
    null_count = int(raw_m[f"{col}_null"].iloc[0])
    null_pct = float(raw_m[f"{col}_null_pct"].iloc[0])
    rows.append({"column": col, "null_count": null_count, "null_pct": null_pct})

matches_null_df = pd.DataFrame(rows)
print(matches_null_df.to_string(index=False))

# %%
findings["matches_null_census"] = {
    "total_rows": total_matches,
    "columns": rows,
}

# %% [markdown]
# ## Section B: Full NULL census of players_raw
#
# All 14 columns -- count and percentage computed in SQL (Invariant #6).

# %%
PLAYERS_NULL_SQL = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(winner) AS winner_null,
    ROUND(100.0 * (COUNT(*) - COUNT(winner)) / COUNT(*), 2) AS winner_null_pct,
    COUNT(*) - COUNT(game_id) AS game_id_null,
    ROUND(100.0 * (COUNT(*) - COUNT(game_id)) / COUNT(*), 2) AS game_id_null_pct,
    COUNT(*) - COUNT(team) AS team_null,
    ROUND(100.0 * (COUNT(*) - COUNT(team)) / COUNT(*), 2) AS team_null_pct,
    COUNT(*) - COUNT(feudal_age_uptime) AS feudal_age_uptime_null,
    ROUND(100.0 * (COUNT(*) - COUNT(feudal_age_uptime)) / COUNT(*), 2) AS feudal_age_uptime_null_pct,
    COUNT(*) - COUNT(castle_age_uptime) AS castle_age_uptime_null,
    ROUND(100.0 * (COUNT(*) - COUNT(castle_age_uptime)) / COUNT(*), 2) AS castle_age_uptime_null_pct,
    COUNT(*) - COUNT(imperial_age_uptime) AS imperial_age_uptime_null,
    ROUND(100.0 * (COUNT(*) - COUNT(imperial_age_uptime)) / COUNT(*), 2) AS imperial_age_uptime_null_pct,
    COUNT(*) - COUNT(old_rating) AS old_rating_null,
    ROUND(100.0 * (COUNT(*) - COUNT(old_rating)) / COUNT(*), 2) AS old_rating_null_pct,
    COUNT(*) - COUNT(new_rating) AS new_rating_null,
    ROUND(100.0 * (COUNT(*) - COUNT(new_rating)) / COUNT(*), 2) AS new_rating_null_pct,
    COUNT(*) - COUNT(match_rating_diff) AS match_rating_diff_null,
    ROUND(100.0 * (COUNT(*) - COUNT(match_rating_diff)) / COUNT(*), 2) AS match_rating_diff_null_pct,
    COUNT(*) - COUNT(replay_summary_raw) AS replay_summary_raw_null,
    ROUND(100.0 * (COUNT(*) - COUNT(replay_summary_raw)) / COUNT(*), 2) AS replay_summary_raw_null_pct,
    COUNT(*) - COUNT(profile_id) AS profile_id_null,
    ROUND(100.0 * (COUNT(*) - COUNT(profile_id)) / COUNT(*), 2) AS profile_id_null_pct,
    COUNT(*) - COUNT(civ) AS civ_null,
    ROUND(100.0 * (COUNT(*) - COUNT(civ)) / COUNT(*), 2) AS civ_null_pct,
    COUNT(*) - COUNT(opening) AS opening_null,
    ROUND(100.0 * (COUNT(*) - COUNT(opening)) / COUNT(*), 2) AS opening_null_pct,
    COUNT(*) - COUNT(filename) AS filename_null,
    ROUND(100.0 * (COUNT(*) - COUNT(filename)) / COUNT(*), 2) AS filename_null_pct
FROM players_raw
"""
sql_queries["players_null_census"] = PLAYERS_NULL_SQL

# %%
raw_p = con.execute(PLAYERS_NULL_SQL).df()
total_players = int(raw_p["total_rows"].iloc[0])
print(f"players_raw total rows: {total_players:,}")

# %%
PLAYERS_COLS = [
    "winner", "game_id", "team", "feudal_age_uptime",
    "castle_age_uptime", "imperial_age_uptime", "old_rating",
    "new_rating", "match_rating_diff", "replay_summary_raw",
    "profile_id", "civ", "opening", "filename",
]

rows_p = []
for col in PLAYERS_COLS:
    null_count = int(raw_p[f"{col}_null"].iloc[0])
    null_pct = float(raw_p[f"{col}_null_pct"].iloc[0])
    rows_p.append({"column": col, "null_count": null_count, "null_pct": null_pct})

players_null_df = pd.DataFrame(rows_p)
print(players_null_df.to_string(index=False))

# %%
findings["players_null_census"] = {
    "total_rows": total_players,
    "columns": rows_p,
}

# %% [markdown]
# ## Section B.2: NULL Co-occurrence Analysis
#
# Test whether the four high-NULL columns co-occur in their NULL/non-NULL patterns.
# Hypothesis: they co-occur with replay_enhanced=FALSE.

# %%
NULL_COOCCURRENCE_SQL = """
SELECT
    COUNT(*) FILTER (WHERE feudal_age_uptime IS NULL
        AND castle_age_uptime IS NULL
        AND imperial_age_uptime IS NULL
        AND opening IS NULL) AS all_four_null,
    COUNT(*) FILTER (WHERE feudal_age_uptime IS NOT NULL
        OR castle_age_uptime IS NOT NULL
        OR imperial_age_uptime IS NOT NULL
        OR opening IS NOT NULL) AS at_least_one_not_null,
    COUNT(*) AS total_rows
FROM players_raw
"""
sql_queries["players_raw_null_cooccurrence"] = NULL_COOCCURRENCE_SQL
cooccur_df = con.execute(NULL_COOCCURRENCE_SQL).df()
print("players_raw NULL co-occurrence:")
print(cooccur_df.to_string(index=False))
findings["players_raw_null_cooccurrence"] = {
    k: int(v) for k, v in cooccur_df.iloc[0].to_dict().items()
}

# %% [markdown]
# ## Section C: Target variable (winner) distribution
#
# The prediction target is `winner` (BOOLEAN: TRUE/FALSE/NULL).
# Unlike sc2egset's `result` (VARCHAR), this is a three-state column.
#
# **Note:** 1v1-restricted winner distribution is deferred pending
# `num_players` semantics analysis (Section D).

# %%
WINNER_SQL = """
SELECT
    winner,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM players_raw
GROUP BY winner
ORDER BY cnt DESC
"""
sql_queries["winner_distribution"] = WINNER_SQL

# %%
winner_df = con.execute(WINNER_SQL).df()
print(winner_df.to_string(index=False))

# %%
findings["winner_distribution"] = winner_df.to_dict(orient="records")

# %%
print("Data feeding winner bar chart:")
print(winner_df.to_string(index=False))

# %%
labels = winner_df["winner"].astype(str).tolist()
counts = winner_df["cnt"].tolist()

fig, ax = plt.subplots(figsize=(6, 4))
bars = ax.bar(labels, counts, color=["#2ecc71", "#e74c3c", "#95a5a6"])
ax.set_xlabel("winner value")
ax.set_ylabel("Count")
ax.set_title("Target Variable (winner) Distribution -- players_raw")
for bar, c in zip(bars, counts):
    ax.text(
        bar.get_x() + bar.get_width() / 2, bar.get_height(),
        f"{c:,.0f}", ha="center", va="bottom", fontsize=9,
    )
plt.tight_layout()
plt.savefig(plots_dir / "01_02_04_winner_distribution.png", dpi=150)
plt.show()
plt.close()

# %% [markdown]
# ## Section D: Player-count distribution (thesis scope gate)
#
# The thesis focuses on 1v1 prediction. `num_players` determines scope.

# %%
NUM_PLAYERS_SQL = """
SELECT
    num_players,
    COUNT(*) AS row_count,
    COUNT(DISTINCT game_id) AS distinct_match_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct,
    ROUND(
        100.0 * COUNT(DISTINCT game_id)
        / SUM(COUNT(DISTINCT game_id)) OVER(), 2
    ) AS distinct_match_pct
FROM matches_raw
GROUP BY num_players
ORDER BY num_players
"""
sql_queries["num_players_distribution"] = NUM_PLAYERS_SQL

# %%
num_players_df = con.execute(NUM_PLAYERS_SQL).df()
print(num_players_df.to_string(index=False))

# %%
findings["num_players_distribution"] = num_players_df.to_dict(orient="records")

# %% [markdown]
# ## Section E: Categorical field profiles
#
# Loop-based cells for all categoricals listed in the plan.
# Bar charts for top-k value frequencies.

# %% [markdown]
# ### E.1 matches_raw categoricals

# %%
MATCHES_CATEGORICALS = [
    ("matches_raw", "map", 20),
    ("matches_raw", "leaderboard", 50),
    ("matches_raw", "game_type", 50),
    ("matches_raw", "game_speed", 50),
    ("matches_raw", "starting_age", 50),
    ("matches_raw", "replay_enhanced", 10),
    ("matches_raw", "mirror", 10),
    ("matches_raw", "patch", 50),
    ("matches_raw", "raw_match_type", 50),
]

cat_profiles_matches: dict = {}

# %%
for table, col, topk in MATCHES_CATEGORICALS:
    sql = f"""
SELECT {col}, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM {table}
GROUP BY {col}
ORDER BY cnt DESC
LIMIT {topk}
"""
    df = con.execute(sql).df()
    cardinality_sql = f"SELECT COUNT(DISTINCT {col}) AS card FROM {table}"
    card = int(con.execute(cardinality_sql).df()["card"].iloc[0])
    cat_profiles_matches[col] = {
        "cardinality": card,
        "top_values": df.to_dict(orient="records"),
    }
    sql_queries[f"cat_{table}_{col}"] = sql.strip()
    print(f"\n=== {table}.{col} (cardinality={card}) ===")
    print(df.to_string(index=False))

# %%
findings["categorical_matches"] = cat_profiles_matches

# %% [markdown]
# ### E.2 players_raw categoricals

# %%
PLAYERS_CATEGORICALS = [
    ("players_raw", "civ", 50),
    ("players_raw", "opening", 30),
    ("players_raw", "team", 20),
    ("players_raw", "replay_summary_raw", 20),
]

cat_profiles_players: dict = {}

# %%
for table, col, topk in PLAYERS_CATEGORICALS:
    sql = f"""
SELECT {col}, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM {table}
GROUP BY {col}
ORDER BY cnt DESC
LIMIT {topk}
"""
    df = con.execute(sql).df()
    cardinality_sql = f"SELECT COUNT(DISTINCT {col}) AS card FROM {table}"
    card = int(con.execute(cardinality_sql).df()["card"].iloc[0])
    cat_profiles_players[col] = {
        "cardinality": card,
        "top_values": df.to_dict(orient="records"),
    }
    sql_queries[f"cat_{table}_{col}"] = sql.strip()
    print(f"\n=== {table}.{col} (cardinality={card}) ===")
    print(df.to_string(index=False))

# %%
findings["categorical_players"] = cat_profiles_players

# %% [markdown]
# ### E.3 opening non-NULL distribution
#
# The opening column is 86% NULL. Profile only the non-NULL subset.

# %%
OPENING_NONNULL_SQL = """
SELECT
    opening,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct_of_nonnull
FROM players_raw
WHERE opening IS NOT NULL
GROUP BY opening
ORDER BY cnt DESC
"""
sql_queries["opening_nonnull_distribution"] = OPENING_NONNULL_SQL
opening_nn_df = con.execute(OPENING_NONNULL_SQL).df()
print(f"opening non-NULL rows: {opening_nn_df['cnt'].sum():,}")
print(opening_nn_df.to_string(index=False))
findings["opening_nonnull_distribution"] = {
    "total_nonnull": int(opening_nn_df["cnt"].sum()),
    "values": opening_nn_df.to_dict(orient="records"),
}

# %% [markdown]
# ### E.5 Categorical bar charts
#
# Multi-panel bar charts for the most informative categoricals.

# %%
cat_plot_cols_m = [
    ("matches_raw", "map", 15),
    ("matches_raw", "leaderboard", 20),
    ("matches_raw", "game_type", 20),
    ("matches_raw", "game_speed", 10),
    ("matches_raw", "starting_age", 10),
]

# %%
print("Data feeding matches_raw categorical bar charts:")
for table, col, topk in cat_plot_cols_m:
    vals = cat_profiles_matches[col]["top_values"][:topk]
    print(f"\n  {table}.{col} (top {topk} of {len(cat_profiles_matches[col]['top_values'])}):")
    print(f"  {pd.DataFrame(vals).to_string(index=False)}")

fig, axes = plt.subplots(len(cat_plot_cols_m), 1, figsize=(10, 4 * len(cat_plot_cols_m)))
for ax, (table, col, topk) in zip(axes, cat_plot_cols_m):
    vals = cat_profiles_matches[col]["top_values"][:topk]
    labels_c = [str(v[col]) for v in vals]
    counts_c = [v["cnt"] for v in vals]
    ax.barh(labels_c[::-1], counts_c[::-1])
    ax.set_title(f"{table}.{col} (top {topk})")
    ax.set_xlabel("Count")

plt.tight_layout()
plt.savefig(plots_dir / "01_02_04_categorical_bars_matches.png", dpi=150)
plt.show()
plt.close()

# %%
cat_plot_cols_p = [
    ("players_raw", "civ", 20),
    ("players_raw", "opening", 15),
    ("players_raw", "team", 10),
]

# %%
print("Data feeding players_raw categorical bar charts:")
for table, col, topk in cat_plot_cols_p:
    vals = cat_profiles_players[col]["top_values"][:topk]
    print(f"\n  {table}.{col} (top {topk} of {len(cat_profiles_players[col]['top_values'])}):")
    print(f"  {pd.DataFrame(vals).to_string(index=False)}")

fig, axes = plt.subplots(len(cat_plot_cols_p), 1, figsize=(10, 4 * len(cat_plot_cols_p)))
for ax, (table, col, topk) in zip(axes, cat_plot_cols_p):
    vals = cat_profiles_players[col]["top_values"][:topk]
    labels_c = [str(v[col]) for v in vals]
    counts_c = [v["cnt"] for v in vals]
    ax.barh(labels_c[::-1], counts_c[::-1])
    ax.set_title(f"{table}.{col} (top {topk})")
    ax.set_xlabel("Count")

plt.tight_layout()
plt.savefig(plots_dir / "01_02_04_categorical_bars_players.png", dpi=150)
plt.show()
plt.close()

# %% [markdown]
# ## Section F: Numeric descriptive statistics
#
# DuckDB-side aggregation for all numeric columns.
# Duration columns divided by 1e9 for seconds.
# For high-NULL columns (age uptimes), note limited non-NULL sample.

# %% [markdown]
# ### F.1 matches_raw numerics

# %%
MATCHES_NUMERIC_DEFS = [
    ("matches_raw", "duration / 1e9", "duration_sec"),
    ("matches_raw", "irl_duration / 1e9", "irl_duration_sec"),
    ("matches_raw", "avg_elo", "avg_elo"),
    ("matches_raw", "team_0_elo", "team_0_elo"),
    ("matches_raw", "team_1_elo", "team_1_elo"),
    ("matches_raw", "raw_match_type", "raw_match_type"),
    ("matches_raw", "patch", "patch"),
]

numeric_stats_matches: list = []

# %%
for table, expr, label in MATCHES_NUMERIC_DEFS:
    sql = f"""
SELECT
    COUNT({expr}) AS n_nonnull,
    COUNT(*) - COUNT({expr}) AS n_null,
    SUM(CASE WHEN {expr} = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN({expr}) AS min_val,
    MAX({expr}) AS max_val,
    ROUND(AVG({expr}), 2) AS mean_val,
    ROUND(MEDIAN({expr}), 2) AS median_val,
    ROUND(STDDEV({expr}), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY {expr}), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {expr}), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY {expr}), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {expr}), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY {expr}), 2) AS p95
FROM {table}
"""
    df = con.execute(sql).df()
    rec = df.iloc[0].to_dict()
    rec = {k: float(v) if pd.notna(v) else None for k, v in rec.items()}
    rec["label"] = label
    numeric_stats_matches.append(rec)
    sql_queries[f"numeric_{table}_{label}"] = sql.strip()
    print(f"\n=== {label} ({table}) ===")
    print(df.to_string(index=False))

# %%
findings["numeric_stats_matches"] = numeric_stats_matches

# %% [markdown]
# ### F.2 players_raw numerics

# %%
PLAYERS_NUMERIC_DEFS = [
    ("players_raw", "old_rating", "old_rating"),
    ("players_raw", "new_rating", "new_rating"),
    ("players_raw", "match_rating_diff", "match_rating_diff"),
    ("players_raw", "feudal_age_uptime", "feudal_age_uptime"),
    ("players_raw", "castle_age_uptime", "castle_age_uptime"),
    ("players_raw", "imperial_age_uptime", "imperial_age_uptime"),
]

numeric_stats_players: list = []

# %%
for table, expr, label in PLAYERS_NUMERIC_DEFS:
    sql = f"""
SELECT
    COUNT({expr}) AS n_nonnull,
    COUNT(*) - COUNT({expr}) AS n_null,
    SUM(CASE WHEN {expr} = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN({expr}) AS min_val,
    MAX({expr}) AS max_val,
    ROUND(AVG({expr}), 2) AS mean_val,
    ROUND(MEDIAN({expr}), 2) AS median_val,
    ROUND(STDDEV({expr}), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY {expr}), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {expr}), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY {expr}), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {expr}), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY {expr}), 2) AS p95
FROM {table}
"""
    df = con.execute(sql).df()
    rec = df.iloc[0].to_dict()
    rec = {k: float(v) if pd.notna(v) else None for k, v in rec.items()}
    rec["label"] = label
    numeric_stats_players.append(rec)
    sql_queries[f"numeric_{table}_{label}"] = sql.strip()
    print(f"\n=== {label} ({table}) ===")
    print(df.to_string(index=False))

# %%
findings["numeric_stats_players"] = numeric_stats_players

# %% [markdown]
# ### F.8 Skewness and Kurtosis
#
# EDA Manual Section 3.1 requires distribution shape (skewness, kurtosis) for
# all numeric columns. For high-NULL columns, stats are computed on non-NULL subset only.

# %%
skew_kurt_matches = []
for table, expr, label in MATCHES_NUMERIC_DEFS:
    sql = f"""
SELECT
    ROUND(SKEWNESS({expr}), 4) AS skewness,
    ROUND(KURTOSIS({expr}), 4) AS kurtosis,
    COUNT({expr}) AS n_nonnull
FROM {table}
"""
    df = con.execute(sql).df()
    rec = df.iloc[0].to_dict()
    rec = {k: float(v) if pd.notna(v) else None for k, v in rec.items()}
    rec["label"] = label
    n_null_for_label = next(
        s for s in numeric_stats_matches if s["label"] == label
    )["n_null"]
    if n_null_for_label and n_null_for_label > 0:
        rec["note"] = (
            f"Computed on {int(rec['n_nonnull']):,} non-NULL values only; "
            f"{int(n_null_for_label):,} NULLs excluded"
        )
    skew_kurt_matches.append(rec)
    sql_queries[f"skew_kurt_matches_{label}"] = sql.strip()
    print(f"{label}: skewness={rec['skewness']}, kurtosis={rec['kurtosis']}")

# %%
skew_kurt_players = []
for table, expr, label in PLAYERS_NUMERIC_DEFS:
    sql = f"""
SELECT
    ROUND(SKEWNESS({expr}), 4) AS skewness,
    ROUND(KURTOSIS({expr}), 4) AS kurtosis,
    COUNT({expr}) AS n_nonnull
FROM {table}
"""
    df = con.execute(sql).df()
    rec = df.iloc[0].to_dict()
    rec = {k: float(v) if pd.notna(v) else None for k, v in rec.items()}
    rec["label"] = label
    n_null_for_label = next(
        s for s in numeric_stats_players if s["label"] == label
    )["n_null"]
    if n_null_for_label and n_null_for_label > 0:
        rec["note"] = (
            f"Computed on {int(rec['n_nonnull']):,} non-NULL values only; "
            f"{int(n_null_for_label):,} NULLs excluded"
        )
    skew_kurt_players.append(rec)
    sql_queries[f"skew_kurt_players_{label}"] = sql.strip()
    print(f"{label}: skewness={rec['skewness']}, kurtosis={rec['kurtosis']}")

# %%
findings["skew_kurtosis_matches"] = skew_kurt_matches
findings["skew_kurtosis_players"] = skew_kurt_players

# %% [markdown]
# ### F.3 profile_id min/max (ID safety gate)
#
# profile_id is DOUBLE -- confirm max < 2^53 to avoid precision loss.

# %%
PROFILE_ID_SQL = """
SELECT
    COUNT(profile_id) AS n_nonnull,
    COUNT(*) - COUNT(profile_id) AS n_null,
    MIN(profile_id) AS min_val,
    MAX(profile_id) AS max_val
FROM players_raw
"""
sql_queries["profile_id_range"] = PROFILE_ID_SQL

# %%
pid_df = con.execute(PROFILE_ID_SQL).df()
print(pid_df.to_string(index=False))
max_pid = float(pid_df["max_val"].iloc[0])
print(f"Max profile_id: {max_pid:,.0f}  |  2^53 = {2**53:,}")
print(f"Below 2^53 safety threshold: {max_pid < 2**53}")

# %%
findings["profile_id_range"] = {
    "n_nonnull": int(pid_df["n_nonnull"].iloc[0]),
    "n_null": int(pid_df["n_null"].iloc[0]),
    "min_val": float(pid_df["min_val"].iloc[0]),
    "max_val": max_pid,
    "below_2_53": max_pid < 2**53,
}

# %% [markdown]
# ### F.4 Numeric histograms (DuckDB-side binning)
#
# For 107.6M-row tables: bin in SQL, plot in matplotlib.

# %%
HIST_DEFS_MATCHES = [
    ("matches_raw", "duration / 1e9", "duration_sec", 60),
    ("matches_raw", "irl_duration / 1e9", "irl_duration_sec", 60),
    ("matches_raw", "avg_elo", "avg_elo", 50),
]

hist_data: dict = {}

for table, expr, label, bin_width in HIST_DEFS_MATCHES:
    sql = f"""
SELECT
    FLOOR({expr} / {bin_width}) * {bin_width} AS bin,
    COUNT(*) AS cnt
FROM {table}
WHERE {expr} IS NOT NULL
GROUP BY bin
ORDER BY bin
"""
    df = con.execute(sql).df()
    hist_data[label] = df
    sql_queries[f"hist_{label}"] = sql.strip()

# %%
print("Data feeding matches numeric histograms:")
for table, expr, label, _ in HIST_DEFS_MATCHES:
    df = hist_data[label]
    print(f"\n  {label}: {len(df)} bins, first 5:")
    print(f"  {df.head(5).to_string(index=False)}")
    print(f"  ...last 5:")
    print(f"  {df.tail(5).to_string(index=False)}")

# %%
fig, axes = plt.subplots(1, 3, figsize=(16, 4))
for ax, (label, df) in zip(axes, hist_data.items()):
    ax.bar(df["bin"], df["cnt"], width=df["bin"].diff().median() * 0.9)
    ax.set_title(label)
    ax.set_xlabel(label)
    ax.set_ylabel("Count")

plt.tight_layout()
plt.savefig(plots_dir / "01_02_04_duration_histogram.png", dpi=150)
plt.show()
plt.close()

# %%
HIST_DEFS_PLAYERS = [
    ("players_raw", "old_rating", "old_rating", 50),
    ("players_raw", "new_rating", "new_rating", 50),
    ("players_raw", "match_rating_diff", "match_rating_diff", 5),
    ("players_raw", "feudal_age_uptime", "feudal_age_uptime", 10),
    ("players_raw", "castle_age_uptime", "castle_age_uptime", 10),
    ("players_raw", "imperial_age_uptime", "imperial_age_uptime", 10),
]

for table, expr, label, bin_width in HIST_DEFS_PLAYERS:
    sql = f"""
SELECT
    FLOOR({expr} / {bin_width}) * {bin_width} AS bin,
    COUNT(*) AS cnt
FROM {table}
WHERE {expr} IS NOT NULL
GROUP BY bin
ORDER BY bin
"""
    df = con.execute(sql).df()
    hist_data[label] = df
    sql_queries[f"hist_{label}"] = sql.strip()

# %%
print("Data feeding players numeric histograms:")
for table, expr, label, _ in HIST_DEFS_PLAYERS:
    df = hist_data[label]
    print(f"\n  {label}: {len(df)} bins, first 5:")
    print(f"  {df.head(5).to_string(index=False)}")
    print(f"  ...last 5:")
    print(f"  {df.tail(5).to_string(index=False)}")

# %%
player_hist_labels = [
    "old_rating", "new_rating", "match_rating_diff",
    "feudal_age_uptime", "castle_age_uptime", "imperial_age_uptime",
]

fig, axes = plt.subplots(2, 3, figsize=(16, 8))
for ax, label in zip(axes.flat, player_hist_labels):
    df = hist_data[label]
    bw = df["bin"].diff().median()
    if pd.isna(bw) or bw == 0:
        bw = 1
    ax.bar(df["bin"], df["cnt"], width=float(bw) * 0.9)
    ax.set_title(label)
    ax.set_xlabel(label)
    ax.set_ylabel("Count")

plt.tight_layout()
plt.savefig(plots_dir / "01_02_04_numeric_histograms.png", dpi=150)
plt.show()
plt.close()

# %% [markdown]
# ### F.5 Numeric boxplots (from precomputed percentiles)
#
# Use already-computed percentile data for boxplot rendering.

# %%
all_numeric_stats = {
    s["label"]: s
    for s in numeric_stats_matches + numeric_stats_players
}
box_cols = [
    "duration_sec", "irl_duration_sec", "avg_elo",
    "old_rating", "new_rating", "match_rating_diff",
    "feudal_age_uptime", "castle_age_uptime", "imperial_age_uptime",
]

# %%
print("Data feeding numeric boxplots (precomputed percentiles):")
for col in box_cols:
    s = all_numeric_stats[col]
    print(
        f"  {col}: p05={s['p05']}, p25={s['p25']}, p50={s['p50']}, "
        f"p75={s['p75']}, p95={s['p95']}"
    )

# %%
fig, axes = plt.subplots(3, 3, figsize=(16, 12))
for ax, col in zip(axes.flat, box_cols):
    s = all_numeric_stats[col]
    if s["p25"] is None or s["p75"] is None:
        ax.set_title(f"{col} (no data)")
        continue
    bp_data = {
        "med": s["p50"],
        "q1": s["p25"],
        "q3": s["p75"],
        "whislo": s["p05"],
        "whishi": s["p95"],
    }
    ax.bxp([bp_data], showfliers=False)
    ax.set_title(col)
    ax.set_ylabel("Value")

plt.tight_layout()
plt.savefig(plots_dir / "01_02_04_numeric_boxplots.png", dpi=150)
plt.show()
plt.close()

# %% [markdown]
# ### F.6 IQR-based outlier counts
#
# Outlier detection per EDA Manual Section 3.1.
# IQR = p75 - p25. Lower fence = p25 - 1.5 * IQR. Upper fence = p75 + 1.5 * IQR.
# Factor 1.5 is Tukey's standard (Tukey 1977, Exploratory Data Analysis, p. 44). [I7]

# %%
def compute_iqr_outliers(con, table, expr, label, p25, p75):
    iqr = p75 - p25
    if iqr == 0:
        return {"label": label, "outlier_low": 0, "outlier_high": 0,
                "outlier_total": 0, "outlier_pct": 0.0,
                "denominator": "pct_of_non_null_values",
                "lower_fence": p25, "upper_fence": p75,
                "note": "IQR=0; fence-based detection not meaningful"}
    lower_fence = p25 - 1.5 * iqr
    upper_fence = p75 + 1.5 * iqr
    sql = f"""
    SELECT
        COUNT(*) FILTER (WHERE {expr} < {lower_fence}) AS outlier_low,
        COUNT(*) FILTER (WHERE {expr} > {upper_fence}) AS outlier_high,
        COUNT(*) FILTER (WHERE {expr} IS NOT NULL)     AS n_nonnull
    FROM {table}
    """
    row = con.execute(sql).df().iloc[0]
    total = int(row["outlier_low"]) + int(row["outlier_high"])
    nonnull = int(row["n_nonnull"])
    return {
        "label": label,
        "outlier_low": int(row["outlier_low"]),
        "outlier_high": int(row["outlier_high"]),
        "outlier_total": total,
        "outlier_pct": round(100.0 * total / nonnull, 2) if nonnull > 0 else 0.0,
        "denominator": "pct_of_non_null_values",
        "lower_fence": round(lower_fence, 2),
        "upper_fence": round(upper_fence, 2),
    }

outlier_counts_matches = []
for table, expr, label in MATCHES_NUMERIC_DEFS:
    stats = next(s for s in numeric_stats_matches if s["label"] == label)
    result = compute_iqr_outliers(con, table, expr, label, stats["p25"], stats["p75"])
    outlier_counts_matches.append(result)
    print(f"{label}: {result['outlier_total']:,} outliers ({result['outlier_pct']}%)")

outlier_counts_players = []
for table, expr, label in PLAYERS_NUMERIC_DEFS:
    stats = next(s for s in numeric_stats_players if s["label"] == label)
    result = compute_iqr_outliers(con, table, expr, label, stats["p25"], stats["p75"])
    outlier_counts_players.append(result)
    print(f"{label}: {result['outlier_total']:,} outliers ({result['outlier_pct']}%)")

findings["outlier_counts_matches"] = outlier_counts_matches
findings["outlier_counts_players"] = outlier_counts_players
findings["outlier_counts_note"] = (
    "outlier_pct is percentage of non-NULL values, not percentage of all rows. "
    "For high-NULL columns (e.g., feudal_age_uptime at 87% NULL), these differ "
    "substantially. See 'denominator' field in each entry."
)

# %% [markdown]
# ### F.7 Sentinel value detection: team ELO fields
#
# `team_0_elo` and `team_1_elo` show min=-1.0. Negative ELO is likely
# a sentinel for "unranked/unknown". Quantify and enumerate.

# %%
sql_elo_sentinel = """
SELECT
    COUNT(*) FILTER (WHERE team_0_elo < 0)   AS team_0_elo_neg,
    COUNT(*) FILTER (WHERE team_1_elo < 0)   AS team_1_elo_neg,
    COUNT(*)                                  AS total_rows
FROM matches_raw
"""
sql_queries["elo_sentinel_counts"] = sql_elo_sentinel.strip()
elo_sentinel_row = con.execute(sql_elo_sentinel).df().iloc[0]

sql_elo_neg_distinct = """
SELECT DISTINCT team_0_elo AS elo_val FROM matches_raw WHERE team_0_elo < 0
UNION
SELECT DISTINCT team_1_elo AS elo_val FROM matches_raw WHERE team_1_elo < 0
ORDER BY elo_val
"""
sql_queries["elo_neg_distinct_values"] = sql_elo_neg_distinct.strip()
elo_neg_distinct = con.execute(sql_elo_neg_distinct).df()

findings["elo_sentinel_counts"] = {
    "team_0_elo_negative": int(elo_sentinel_row["team_0_elo_neg"]),
    "team_1_elo_negative": int(elo_sentinel_row["team_1_elo_neg"]),
    "total_rows": int(elo_sentinel_row["total_rows"]),
    "team_0_pct": round(100.0 * int(elo_sentinel_row["team_0_elo_neg"]) / int(elo_sentinel_row["total_rows"]), 2),
    "team_1_pct": round(100.0 * int(elo_sentinel_row["team_1_elo_neg"]) / int(elo_sentinel_row["total_rows"]), 2),
}
findings["elo_negative_distinct_values"] = elo_neg_distinct["elo_val"].tolist()
print("ELO sentinel:", findings["elo_sentinel_counts"])
print("Distinct negative ELO values:", findings["elo_negative_distinct_values"])

# %% [markdown]
# ### F.9 ELO sentinel-excluded descriptive stats
#
# Parallel stats for team_0_elo and team_1_elo excluding the -1.0 sentinel.
# ELO=0 rows (4,824 for team_0_elo, 192 for team_1_elo) are NOT excluded --
# only the -1.0 sentinel (unranked marker) is excluded. ELO=0 may be valid.

# %%
for elo_col in ["team_0_elo", "team_1_elo"]:
    sql = f"""
SELECT
    COUNT({elo_col}) AS n_nonnull,
    COUNT(*) - COUNT({elo_col}) AS n_null,
    SUM(CASE WHEN {elo_col} = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN({elo_col}) AS min_val,
    MAX({elo_col}) AS max_val,
    ROUND(AVG({elo_col}), 2) AS mean_val,
    ROUND(MEDIAN({elo_col}), 2) AS median_val,
    ROUND(STDDEV({elo_col}), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY {elo_col}), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {elo_col}), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY {elo_col}), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {elo_col}), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY {elo_col}), 2) AS p95
FROM matches_raw
WHERE {elo_col} != -1.0
-- Note: ELO=0 rows (4,824 for team_0_elo, 192 for team_1_elo) are NOT excluded here;
-- only the -1.0 sentinel (unranked marker) is excluded. ELO=0 may represent valid
-- entries and requires separate investigation if needed.
"""
    df = con.execute(sql).df()
    rec = df.iloc[0].to_dict()
    rec = {k: float(v) if pd.notna(v) else None for k, v in rec.items()}
    findings[f"{elo_col}_stats_no_sentinel"] = rec
    sql_queries[f"numeric_matches_{elo_col}_no_sentinel"] = sql.strip()
    print(f"\n=== {elo_col} (sentinel -1.0 excluded) ===")
    print(df.to_string(index=False))

# %% [markdown]
# ## Section G: Temporal range
#
# `started_timestamp` is TIMESTAMP WITH TIME ZONE (native DuckDB).
# Cross-validate against 01_01_01 filename-derived range.

# %%
TEMPORAL_SQL = """
SELECT
    MIN(started_timestamp) AS earliest,
    MAX(started_timestamp) AS latest,
    COUNT(DISTINCT DATE_TRUNC('month', started_timestamp)) AS distinct_months,
    COUNT(DISTINCT DATE_TRUNC('week', started_timestamp)) AS distinct_weeks
FROM matches_raw
"""
sql_queries["temporal_range"] = TEMPORAL_SQL

# %%
temporal_df = con.execute(TEMPORAL_SQL).df()
print(temporal_df.to_string(index=False))

# %%
findings["temporal_range"] = {
    "earliest": str(temporal_df["earliest"].iloc[0]),
    "latest": str(temporal_df["latest"].iloc[0]),
    "distinct_months": int(temporal_df["distinct_months"].iloc[0]),
    "distinct_weeks": int(temporal_df["distinct_weeks"].iloc[0]),
}

# %%
MONTHLY_SQL = """
SELECT
    DATE_TRUNC('month', started_timestamp) AS month,
    COUNT(*) AS match_count
FROM matches_raw
WHERE started_timestamp IS NOT NULL
GROUP BY month
ORDER BY month
"""
sql_queries["monthly_match_counts"] = MONTHLY_SQL

# %%
monthly_df = con.execute(MONTHLY_SQL).df()
print(f"Monthly data: {len(monthly_df)} months")
print(monthly_df.head(10).to_string(index=False))

# %%
print(f"Monthly match counts: {len(monthly_df)} months")
print(monthly_df.to_string(index=False))

# %%
fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(monthly_df["month"], monthly_df["match_count"], marker="o", markersize=3)
ax.set_xlabel("Month")
ax.set_ylabel("Match Count")
ax.set_title("Match Count Over Time (Monthly) -- matches_raw")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(plots_dir / "01_02_04_match_count_over_time.png", dpi=150)
plt.show()
plt.close()

# %% [markdown]
# ## Section H: game_id join integrity
#
# Orphan detection between tables and players-per-match distribution.

# %%
ORPHAN_SQL = """
SELECT
    'players_without_match' AS check_name,
    COUNT(DISTINCT p.game_id) AS cnt
FROM players_raw p
LEFT JOIN matches_raw m ON p.game_id = m.game_id
WHERE m.game_id IS NULL
UNION ALL
SELECT
    'matches_without_players' AS check_name,
    COUNT(DISTINCT m.game_id) AS cnt
FROM matches_raw m
LEFT JOIN players_raw p ON m.game_id = p.game_id
WHERE p.game_id IS NULL
"""
sql_queries["orphan_detection"] = ORPHAN_SQL

# %%
orphan_df = con.execute(ORPHAN_SQL).df()
print(orphan_df.to_string(index=False))

# %%
findings["join_integrity_orphans"] = orphan_df.to_dict(orient="records")

# %%
PPM_SQL = """
SELECT
    player_count,
    COUNT(*) AS match_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM (
    SELECT game_id, COUNT(*) AS player_count
    FROM players_raw
    GROUP BY game_id
)
GROUP BY player_count
ORDER BY player_count
"""
sql_queries["players_per_match"] = PPM_SQL

# %%
ppm_df = con.execute(PPM_SQL).df()
print(ppm_df.to_string(index=False))

# %%
findings["players_per_match"] = ppm_df.to_dict(orient="records")

# %% [markdown]
# ## Section H.2: Duplicate Row Detection
#
# EDA Manual Section 3.2 requires duplicate row count and percentage.
# matches_raw: duplicates by game_id.
# players_raw: duplicates by (game_id, profile_id) composite.
# COALESCE used for profile_id because it has 1,185 NULLs in players_raw;
# NULL || anything = NULL in SQL, which would silently exclude those rows.

# %%
DUPE_MATCHES_SQL = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT CAST(game_id AS VARCHAR)) AS distinct_game_ids,
    COUNT(*) - COUNT(DISTINCT CAST(game_id AS VARCHAR)) AS duplicate_rows
FROM matches_raw
"""
sql_queries["duplicate_check_matches"] = DUPE_MATCHES_SQL
dupe_m = con.execute(DUPE_MATCHES_SQL).df()
print("matches_raw duplicate check:")
print(dupe_m.to_string(index=False))
findings["duplicate_check_matches"] = {k: int(v) for k, v in dupe_m.iloc[0].to_dict().items()}

# %%
DUPE_PLAYERS_SQL = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT CAST(game_id AS VARCHAR) || '_' || COALESCE(CAST(profile_id AS VARCHAR), '__NULL__'))
        AS distinct_game_player_pairs,
    COUNT(*) - COUNT(DISTINCT CAST(game_id AS VARCHAR) || '_' || COALESCE(CAST(profile_id AS VARCHAR), '__NULL__'))
        AS duplicate_rows
FROM players_raw
"""
sql_queries["duplicate_check_players"] = DUPE_PLAYERS_SQL
dupe_p = con.execute(DUPE_PLAYERS_SQL).df()
print("players_raw duplicate check:")
print(dupe_p.to_string(index=False))
findings["duplicate_check_players"] = {k: int(v) for k, v in dupe_p.iloc[0].to_dict().items()}

# %% [markdown]
# ## Section I: Dead/constant/near-constant field detection
#
# Uniqueness ratio for all columns. Flag cardinality = 1 (constant)
# or uniqueness ratio < 0.001 (near-constant, EDA Manual Section 3.3).
# NULL deflation note: for flagged columns with >50% NULL,
# also report non-NULL uniqueness ratio.

# %%
MATCHES_COLS_ALL = [
    "map", "started_timestamp", "duration", "irl_duration", "game_id",
    "avg_elo", "num_players", "team_0_elo", "team_1_elo",
    "replay_enhanced", "leaderboard", "mirror", "patch",
    "raw_match_type", "game_type", "game_speed", "starting_age",
    "filename",
]

uniqueness_rows_m = []
for col in MATCHES_COLS_ALL:
    sql = f"""
SELECT
    '{col}' AS column_name,
    COUNT(DISTINCT {col}) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT({col}) AS nonnull_rows,
    ROUND(COUNT(DISTINCT {col})::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT {col})::DOUBLE / NULLIF(COUNT({col}), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM matches_raw
"""
    df = con.execute(sql).df()
    uniqueness_rows_m.append(df.iloc[0].to_dict())
    sql_queries[f"uniqueness_matches_{col}"] = sql.strip()

# %%
uniq_m_df = pd.DataFrame(uniqueness_rows_m)
print("matches_raw uniqueness:\n")
print(uniq_m_df.to_string(index=False))

# %%
PLAYERS_COLS_ALL = [
    "winner", "game_id", "team", "feudal_age_uptime",
    "castle_age_uptime", "imperial_age_uptime", "old_rating",
    "new_rating", "match_rating_diff", "replay_summary_raw",
    "profile_id", "civ", "opening", "filename",
]

uniqueness_rows_p = []
for col in PLAYERS_COLS_ALL:
    sql = f"""
SELECT
    '{col}' AS column_name,
    COUNT(DISTINCT {col}) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT({col}) AS nonnull_rows,
    ROUND(COUNT(DISTINCT {col})::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT {col})::DOUBLE / NULLIF(COUNT({col}), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM players_raw
"""
    df = con.execute(sql).df()
    uniqueness_rows_p.append(df.iloc[0].to_dict())
    sql_queries[f"uniqueness_players_{col}"] = sql.strip()

# %%
uniq_p_df = pd.DataFrame(uniqueness_rows_p)
print("players_raw uniqueness:\n")
print(uniq_p_df.to_string(index=False))

# %%
dead_constant = []
near_constant_low_cardinality = []
near_constant_ratio_flagged = []

# [I7] Empirical threshold: max categorical cardinality in this dataset is 93 (map);
# min continuous cardinality is 3,032 (old_rating). Threshold of 100 cleanly separates groups.
# (civ cardinality=50 is correctly included as categorical under this threshold.)
# Key names aligned with aoe2companion plan for cross-dataset comparability.
NEAR_CONSTANT_CARDINALITY_THRESHOLD = 100

for row in uniqueness_rows_m + uniqueness_rows_p:
    card = int(row["cardinality"])
    ratio = float(row["uniqueness_ratio"])
    if card == 1:
        dead_constant.append(row)
    elif card < NEAR_CONSTANT_CARDINALITY_THRESHOLD and ratio < 0.001:
        near_constant_low_cardinality.append(row)
    elif ratio < 0.001:
        near_constant_ratio_flagged.append(row)

print(f"\nDead/constant fields (cardinality=1): {len(dead_constant)}")
for r in dead_constant:
    print(f"  {r['column_name']}: cardinality={r['cardinality']}")

print(f"\nNear-constant low-cardinality (cardinality < {NEAR_CONSTANT_CARDINALITY_THRESHOLD} AND ratio < 0.001): {len(near_constant_low_cardinality)}")
for r in near_constant_low_cardinality:
    print(f"  {r['column_name']}: cardinality={r['cardinality']}, ratio={r['uniqueness_ratio']}")

print(f"\nRatio-flagged (cardinality >= {NEAR_CONSTANT_CARDINALITY_THRESHOLD}, ratio < 0.001 due to large N): {len(near_constant_ratio_flagged)}")
for r in near_constant_ratio_flagged:
    print(f"  {r['column_name']}: cardinality={r['cardinality']}, ratio={r['uniqueness_ratio']}")
    print(f"    -> NOT near-constant; ratio is low only because N={r['total_rows']:,}")

# %%
findings["uniqueness_matches"] = uniqueness_rows_m
findings["uniqueness_players"] = uniqueness_rows_p
findings["dead_constant_fields"] = dead_constant
findings["near_constant_low_cardinality"] = near_constant_low_cardinality
findings["near_constant_ratio_flagged"] = near_constant_ratio_flagged
findings["near_constant_detection_note"] = {
    "cardinality_threshold": NEAR_CONSTANT_CARDINALITY_THRESHOLD,
    "justification": (
        "EDA Manual Section 3.3 uses uniqueness_ratio < 0.001 as a starting point. "
        "On a 30M/107M row dataset, this ratio flags continuous numerics with "
        "thousands of distinct values. Threshold of 100 separates genuinely "
        "low-cardinality columns (max categorical: map at 93) from continuous numerics "
        "(min: old_rating at 3,032). Columns flagged only by ratio are documented "
        "as 'near_constant_ratio_flagged' and are NOT near-constant."
    ),
}

# %% [markdown]
# ## Section K: Field temporal classification
#
# Classify every column by availability at prediction time.
# Categories: identifier | pre_game | in_game | post_game | target | constant | meta | deferred
# Invariant #3: any field classified as post_game or target is excluded from
# pre-game feature engineering. Fields classified as 'deferred' require
# empirical verification before use.

# %%
field_classification = {
    "classification_status": "preliminary",
    "formal_boundary_deferred_to": "Phase 02 (Feature Engineering)",
    "fields": [
        # matches_raw (18 columns)
        {"table": "matches_raw", "column": "game_id",          "classification": "identifier", "rationale": "Join key"},
        {"table": "matches_raw", "column": "map",              "classification": "pre_game",   "rationale": "Known at match creation"},
        {"table": "matches_raw", "column": "started_timestamp","classification": "pre_game",   "rationale": "Match start time"},
        {"table": "matches_raw", "column": "num_players",      "classification": "pre_game",   "rationale": "Lobby size known at match start"},
        {"table": "matches_raw", "column": "avg_elo",          "classification": "pre_game",   "rationale": "Computed from pre-match ratings"},
        {"table": "matches_raw", "column": "team_0_elo",       "classification": "pre_game",   "rationale": "Team 0 pre-match rating; sentinel -1.0 = unranked"},
        {"table": "matches_raw", "column": "team_1_elo",       "classification": "pre_game",   "rationale": "Team 1 pre-match rating; sentinel -1.0 = unranked"},
        {"table": "matches_raw", "column": "leaderboard",      "classification": "pre_game",   "rationale": "Ladder type selected before match"},
        {"table": "matches_raw", "column": "game_type",        "classification": "constant",   "rationale": "Cardinality=1 across entire dataset"},
        {"table": "matches_raw", "column": "game_speed",       "classification": "constant",   "rationale": "Cardinality=1 across entire dataset"},
        {"table": "matches_raw", "column": "starting_age",     "classification": "pre_game",   "rationale": "Game setting at lobby; near-constant (cardinality=2: 'dark' 30,690,632 rows vs 'standard' 19 rows)"},
        {"table": "matches_raw", "column": "mirror",           "classification": "pre_game",   "rationale": "Derivable from civ selections at match start"},
        {"table": "matches_raw", "column": "patch",            "classification": "pre_game",   "rationale": "Game version known at match time"},
        {"table": "matches_raw", "column": "raw_match_type",   "classification": "pre_game",   "rationale": "Match type determined before match"},
        {"table": "matches_raw", "column": "replay_enhanced",  "classification": "meta",       "rationale": "Data quality/source flag"},
        {"table": "matches_raw", "column": "duration",         "classification": "post_game",  "rationale": "Only known after match ends"},
        {"table": "matches_raw", "column": "irl_duration",     "classification": "post_game",  "rationale": "Only known after match ends"},
        {"table": "matches_raw", "column": "filename",         "classification": "meta",       "rationale": "Provenance column (Invariant I10)"},
        # players_raw (14 columns)
        {"table": "players_raw", "column": "game_id",          "classification": "identifier", "rationale": "Join key"},
        {"table": "players_raw", "column": "profile_id",       "classification": "identifier", "rationale": "Player identifier"},
        {"table": "players_raw", "column": "winner",           "classification": "target",     "rationale": "Prediction target (Invariant #3)"},
        {"table": "players_raw", "column": "team",             "classification": "pre_game",   "rationale": "Team assignment known at match start"},
        {"table": "players_raw", "column": "civ",              "classification": "pre_game",   "rationale": "Civilization selected at match start"},
        {"table": "players_raw", "column": "old_rating",       "classification": "pre_game",   "rationale": "Player rating before match (authoritative pre-game signal)"},
        {"table": "players_raw", "column": "new_rating",       "classification": "post_game",  "rationale": "LEAKAGE -- player rating after match (Invariant #3 violation if used as feature)"},
        {"table": "players_raw", "column": "match_rating_diff","classification": "deferred",   "rationale": "Leakage status unknown -- could be (new_rating - old_rating) = post_game, or (player_elo - opponent_elo) = pre_game. Requires empirical test: SELECT COUNT(*) FROM players_raw WHERE ABS(match_rating_diff - (new_rating - old_rating)) < 0.01"},
        {"table": "players_raw", "column": "opening",          "classification": "in_game",    "rationale": "Opening strategy determined during gameplay"},
        {"table": "players_raw", "column": "feudal_age_uptime","classification": "in_game",    "rationale": "Time to Feudal Age, measured during gameplay; 87% NULL"},
        {"table": "players_raw", "column": "castle_age_uptime","classification": "in_game",    "rationale": "Time to Castle Age, measured during gameplay; 88% NULL"},
        {"table": "players_raw", "column": "imperial_age_uptime","classification": "in_game",  "rationale": "Time to Imperial Age, measured during gameplay; 91% NULL"},
        {"table": "players_raw", "column": "replay_summary_raw","classification": "in_game",   "rationale": "Replay data; available only after match via replay parsing"},
        {"table": "players_raw", "column": "filename",         "classification": "meta",       "rationale": "Provenance column (Invariant I10)"},
    ]
}
findings["field_classification"] = field_classification
findings["field_classification_summary"] = {
    cls: sum(1 for f in field_classification["fields"] if f["classification"] == cls)
    for cls in ["pre_game", "post_game", "in_game", "identifier", "target", "constant", "meta", "deferred"]
}
findings["field_classification_note"] = {
    "match_rating_diff_leakage_test_sql": (
        "SELECT COUNT(*) FROM players_raw "
        "WHERE ABS(match_rating_diff - (new_rating - old_rating)) < 0.01"
    ),
    "note": (
        "If result > 0, match_rating_diff encodes new_rating - old_rating = post_game "
        "(fatal leakage). If result == 0, may be pre_game differential. "
        "Run this test before Phase 02 feature engineering."
    ),
}
print("Field classification:", findings["field_classification_summary"])

# %% [markdown]
# ## T04: z-score outlier deferral note
#
# EDA Manual Section 3.1 lists z-scores as required. Deferred with documentation.

# %%
findings["z_score_outliers_deferred"] = {
    "reason": "Deferred to Pipeline Section 01_03",
    "note": (
        "z-score outliers require mean/stddev; for highly skewed distributions "
        "(duration, age uptimes), z-scores are less informative than IQR fences. "
        "Full z-score profiling deferred to 01_03."
    ),
}

# %% [markdown]
# ## Section J: Write JSON and markdown artifacts
#
# JSON with all findings. Markdown with all SQL verbatim (Invariant #6).

# %%
artifact_data = {
    "step": "01_02_04",
    "dataset": "aoestats",
    **findings,
}

json_path = artifacts_dir / "01_02_04_univariate_census.json"
json_path.write_text(json.dumps(artifact_data, indent=2, default=str))
print(f"JSON artifact written: {json_path}")

# %%
md_lines = [
    "# Step 01_02_04 -- Univariate Census & Target Variable EDA",
    "",
    "**Dataset:** aoestats",
    "**Tables:** matches_raw (18 cols), players_raw (14 cols)",
    "",
]

md_lines.append("## SQL Queries (Invariant #6)")
md_lines.append("")
for name, sql in sql_queries.items():
    md_lines.append(f"### {name}")
    md_lines.append("")
    md_lines.append("```sql")
    md_lines.append(sql.strip())
    md_lines.append("```")
    md_lines.append("")

md_lines.append("## Key Findings")
md_lines.append("")
md_lines.append(
    f"- matches_raw total rows: {findings['matches_null_census']['total_rows']:,}"
)
md_lines.append(
    f"- players_raw total rows: {findings['players_null_census']['total_rows']:,}"
)
md_lines.append("")
md_lines.append("### Winner Distribution")
for row in findings["winner_distribution"]:
    md_lines.append(f"- winner={row['winner']}: {row['cnt']:,} ({row['pct']}%)")
md_lines.append("")
md_lines.append("### num_players Distribution")
for row in findings["num_players_distribution"]:
    md_lines.append(
        f"- num_players={row['num_players']}: "
        f"rows={row['row_count']:,} ({row['pct']}%), "
        f"distinct_matches={row['distinct_match_count']:,} "
        f"({row['distinct_match_pct']}%)"
    )

md_path = artifacts_dir / "01_02_04_univariate_census.md"
md_path.write_text("\n".join(md_lines) + "\n")
print(f"Markdown artifact written: {md_path}")

# %%
con.close()
print("Done. Connection closed.")
