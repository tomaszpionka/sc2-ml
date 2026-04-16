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
# # Step 01_03_03 -- Table Utility Assessment: aoestats
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_03 -- Systematic Data Profiling
# **Dataset:** aoestats
# **Question:** Which tables are essential for the prediction pipeline, which
# are redundant, and which are supplementary? Specifically:
# - Column overlap between matches_raw and players_raw
# - Join integrity and multiplicity between matches_raw and players_raw
# - ELO redundancy: is matches_raw.avg_elo derivable from players_raw.old_rating?
# - overviews_raw content (all STRUCT arrays) and replay_summary_raw utility
# - Evidence-backed per-table verdict
# **Invariants applied:**
# - #3 (temporal discipline -- ELO fields annotated with temporal class)
# - #6 (reproducibility -- all SQL stored verbatim in artifact)
# - #7 (no magic numbers -- all constants from prior artifacts)
# - #9 (step scope: utility assessment only -- no cleaning decisions)
# **Predecessor:** 01_03_02 (True 1v1 Match Identification -- complete)
# **Step scope:** Empirical assessment only. Verdicts derive from query results.
# No pipeline design decisions.
# **ROADMAP reference:** `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`
# **Date:** 2026-04-15

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
plots_dir = profiling_dir / "plots"
plots_dir.mkdir(parents=True, exist_ok=True)

# Load prior artifacts
profile_01_03_01_path = profiling_dir / "01_03_01_systematic_profile.json"
with open(profile_01_03_01_path) as f:
    profile_01_03_01 = json.load(f)

profile_01_03_02_path = profiling_dir / "01_03_02_true_1v1_profile.json"
with open(profile_01_03_02_path) as f:
    profile_01_03_02 = json.load(f)

census_path = reports_dir / "artifacts" / "01_exploration" / "02_eda" / "01_02_04_univariate_census.json"
with open(census_path) as f:
    census = json.load(f)

# I7: Extract constants from prior artifacts -- no magic numbers
MATCHES_TOTAL = profile_01_03_01["dataset_level"]["matches_raw_rows"]
PLAYERS_TOTAL = profile_01_03_01["dataset_level"]["players_raw_rows"]
MATCHES_WITHOUT_PLAYERS = profile_01_03_01["dataset_level"]["matches_without_players"]
TRUE_1V1_COUNT = profile_01_03_02["true_1v1_count"]

print(f"MATCHES_TOTAL            = {MATCHES_TOTAL:,}")
print(f"PLAYERS_TOTAL            = {PLAYERS_TOTAL:,}")
print(f"MATCHES_WITHOUT_PLAYERS  = {MATCHES_WITHOUT_PLAYERS:,}")
print(f"TRUE_1V1_COUNT           = {TRUE_1V1_COUNT:,}")

# %%
sql_queries = {}
result = {
    "step": "01_03_03",
    "dataset": "aoestats",
    "constants_source": {
        "MATCHES_TOTAL": {
            "value": MATCHES_TOTAL,
            "source": "01_03_01_systematic_profile.json > dataset_level.matches_raw_rows",
        },
        "PLAYERS_TOTAL": {
            "value": PLAYERS_TOTAL,
            "source": "01_03_01_systematic_profile.json > dataset_level.players_raw_rows",
        },
        "MATCHES_WITHOUT_PLAYERS": {
            "value": MATCHES_WITHOUT_PLAYERS,
            "source": "01_03_01_systematic_profile.json > dataset_level.matches_without_players",
        },
        "TRUE_1V1_COUNT": {
            "value": TRUE_1V1_COUNT,
            "source": "01_03_02_true_1v1_profile.json > true_1v1_count",
        },
    },
}

# %% [markdown]
# ## T01: Column Overlap and Exclusive Contributions
#
# DESCRIBE both matches_raw and players_raw. Compute set intersection and
# set difference of column names. Confirm join key (game_id) is in both.
# Confirm where winner and started_timestamp live.

# %%
sql_describe_matches = "DESCRIBE matches_raw"
sql_describe_players = "DESCRIBE players_raw"
sql_queries["describe_matches"] = sql_describe_matches
sql_queries["describe_players"] = sql_describe_players

df_matches_schema = db.fetch_df(sql_describe_matches)
df_players_schema = db.fetch_df(sql_describe_players)

print("=== matches_raw schema ===")
print(df_matches_schema[["column_name", "column_type", "null"]].to_string(index=False))
print(f"\nTotal columns: {len(df_matches_schema)}")

print("\n=== players_raw schema ===")
print(df_players_schema[["column_name", "column_type", "null"]].to_string(index=False))
print(f"\nTotal columns: {len(df_players_schema)}")

# %%
matches_cols = set(df_matches_schema["column_name"].tolist())
players_cols = set(df_players_schema["column_name"].tolist())

shared_cols = matches_cols & players_cols
matches_only = matches_cols - players_cols
players_only = players_cols - matches_cols

print("=== Column Overlap Matrix ===")
print(f"\nShared columns ({len(shared_cols)}): {sorted(shared_cols)}")
print(f"\nmatches_raw exclusive ({len(matches_only)}): {sorted(matches_only)}")
print(f"\nplayers_raw exclusive ({len(players_only)}): {sorted(players_only)}")

# Confirm key columns
assert "game_id" in matches_cols, "game_id NOT in matches_raw -- join key missing!"
assert "game_id" in players_cols, "game_id NOT in players_raw -- join key missing!"
assert "winner" in players_cols, "winner NOT in players_raw!"
assert "winner" not in matches_cols, "winner unexpectedly in matches_raw!"
assert "started_timestamp" in matches_cols, "started_timestamp NOT in matches_raw!"
assert "started_timestamp" not in players_cols, "started_timestamp unexpectedly in players_raw!"

print("\n[CONFIRMED] game_id is the join key (present in both tables)")
print("[CONFIRMED] winner is EXCLUSIVE to players_raw")
print("[CONFIRMED] started_timestamp is EXCLUSIVE to matches_raw")

result["t01_column_overlap"] = {
    "matches_raw_column_count": len(matches_cols),
    "players_raw_column_count": len(players_cols),
    "shared_columns": sorted(shared_cols),
    "matches_raw_exclusive": sorted(matches_only),
    "players_raw_exclusive": sorted(players_only),
    "game_id_in_matches": "game_id" in matches_cols,
    "game_id_in_players": "game_id" in players_cols,
    "winner_table": "players_raw",
    "winner_in_matches": "winner" in matches_cols,
    "started_timestamp_table": "matches_raw",
    "started_timestamp_in_players": "started_timestamp" in players_cols,
}

# %% [markdown]
# ## T02: Join Integrity and Multiplicity
#
# Profile the game_id join between matches_raw and players_raw.
# - Anti-join in both directions (orphan counts)
# - Players-per-match distribution for joined matches
# - game_id cardinality in both tables
# - Multiplicity: matches have exactly 1 row per game_id; players have 2-8+

# %%
# T02-A: Orphan matches (game_id in matches_raw but not in players_raw)
sql_orphan_matches = """
SELECT COUNT(*) AS orphan_matches
FROM matches_raw m
WHERE NOT EXISTS (
    SELECT 1 FROM players_raw p WHERE p.game_id = m.game_id
)
"""
sql_queries["orphan_matches"] = sql_orphan_matches
orphan_matches_df = db.fetch_df(sql_orphan_matches)
orphan_matches = int(orphan_matches_df["orphan_matches"].iloc[0])
print(f"Orphan matches (in matches_raw but no players): {orphan_matches:,}")

# Cross-validate against 01_03_01
assert abs(orphan_matches - MATCHES_WITHOUT_PLAYERS) <= 1, (
    f"Orphan matches {orphan_matches} != 01_03_01 value {MATCHES_WITHOUT_PLAYERS}"
)
print(f"[VALIDATED] Matches 01_03_01 MATCHES_WITHOUT_PLAYERS = {MATCHES_WITHOUT_PLAYERS:,}")

# %%
# T02-B: Orphan players (game_id in players_raw but not in matches_raw)
sql_orphan_players = """
SELECT COUNT(DISTINCT game_id) AS orphan_player_game_ids,
       COUNT(*) AS orphan_player_rows
FROM players_raw p
WHERE NOT EXISTS (
    SELECT 1 FROM matches_raw m WHERE m.game_id = p.game_id
)
"""
sql_queries["orphan_players"] = sql_orphan_players
orphan_players_df = db.fetch_df(sql_orphan_players)
orphan_player_game_ids = int(orphan_players_df["orphan_player_game_ids"].iloc[0])
orphan_player_rows = int(orphan_players_df["orphan_player_rows"].iloc[0])
print(f"Orphan players (game_id in players_raw, not in matches_raw):")
print(f"  Distinct game_ids: {orphan_player_game_ids:,}")
print(f"  Player rows:       {orphan_player_rows:,}")

# %%
# T02-C: game_id cardinality in both tables
sql_game_id_cardinality = """
SELECT
    (SELECT COUNT(DISTINCT game_id) FROM matches_raw) AS matches_distinct_game_ids,
    (SELECT COUNT(*) FROM matches_raw)                AS matches_total_rows,
    (SELECT COUNT(DISTINCT game_id) FROM players_raw) AS players_distinct_game_ids,
    (SELECT COUNT(*) FROM players_raw)                AS players_total_rows
"""
sql_queries["game_id_cardinality"] = sql_game_id_cardinality
cardinality_df = db.fetch_df(sql_game_id_cardinality)
print(cardinality_df.T.to_string())

matches_distinct = int(cardinality_df["matches_distinct_game_ids"].iloc[0])
matches_total = int(cardinality_df["matches_total_rows"].iloc[0])
players_distinct = int(cardinality_df["players_distinct_game_ids"].iloc[0])
players_total = int(cardinality_df["players_total_rows"].iloc[0])

matches_uniqueness_pct = 100.0 * matches_distinct / matches_total
print(f"\nmatches_raw: {matches_distinct:,} distinct / {matches_total:,} total "
      f"= {matches_uniqueness_pct:.4f}% unique")
print(f"players_raw: {players_distinct:,} distinct game_ids / {players_total:,} total rows "
      f"= avg {players_total / players_distinct:.2f} player rows per game_id")

# %%
# T02-D: Multiplicity distribution (players per game_id)
sql_multiplicity = """
SELECT
    player_count,
    COUNT(*) AS num_games,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 4) AS pct_of_all_games
FROM (
    SELECT game_id, COUNT(*) AS player_count
    FROM players_raw
    GROUP BY game_id
) sub
GROUP BY player_count
ORDER BY player_count
"""
sql_queries["multiplicity_distribution"] = sql_multiplicity
mult_df = db.fetch_df(sql_multiplicity)
print("\nMultiplicity distribution (players per game_id in players_raw):")
print(mult_df.to_string(index=False))

# %%
# T02-E: matches_raw uniqueness per game_id (confirm 1:1)
sql_match_duplicates = """
SELECT
    MAX(cnt) AS max_count_per_game_id,
    COUNT(*) FILTER (WHERE cnt > 1) AS game_ids_with_duplicates,
    SUM(cnt) FILTER (WHERE cnt > 1) AS duplicate_rows
FROM (
    SELECT game_id, COUNT(*) AS cnt
    FROM matches_raw
    GROUP BY game_id
) sub
"""
sql_queries["match_duplicates"] = sql_match_duplicates
match_dup_df = db.fetch_df(sql_match_duplicates)
print("\nmatches_raw duplicate check:")
print(match_dup_df.T.to_string())

result["t02_join_integrity"] = {
    "orphan_matches_in_matches_not_players": orphan_matches,
    "orphan_player_game_ids_not_in_matches": orphan_player_game_ids,
    "orphan_player_rows_not_in_matches": orphan_player_rows,
    "matches_distinct_game_ids": matches_distinct,
    "matches_total_rows": matches_total,
    "matches_uniqueness_pct": round(matches_uniqueness_pct, 4),
    "players_distinct_game_ids": players_distinct,
    "players_total_rows": players_total,
    "players_avg_rows_per_game_id": round(players_total / players_distinct, 4),
    "multiplicity_distribution": mult_df.to_dict(orient="records"),
    "matches_max_count_per_game_id": int(match_dup_df["max_count_per_game_id"].iloc[0]),
    "matches_game_ids_with_duplicates": int(match_dup_df["game_ids_with_duplicates"].iloc[0]),
}

# %% [markdown]
# ## T03: ELO Redundancy Assessment
#
# The 01_02_07 multivariate EDA found near-perfect ELO redundancy (rho > 0.98)
# between avg_elo (matches_raw), team_0_elo (matches_raw), team_1_elo
# (matches_raw), and old_rating (players_raw).
#
# This step quantifies:
# 1. Whether avg_elo == (team_0_elo + team_1_elo) / 2 exactly (deterministic
#    derivation within matches_raw).
# 2. Whether avg_elo is derivable from the mean of old_rating across players
#    in 1v1 matches (i.e., whether match-level ELOs are redundant given
#    player-level ratings).
# 3. Spearman correlation on a 100K RESERVOIR sample.
#
# Temporal annotation:
# - old_rating = rating BEFORE the match (pre-game feature, temporally clean per I3)
# - new_rating = rating AFTER the match (target-leaking feature -- must not be used)
# - avg_elo, team_0_elo, team_1_elo = match-level aggregates (pre-game per API context)

# %%
# T03-A: Check avg_elo = (team_0_elo + team_1_elo) / 2 within matches_raw
sql_elo_formula_check = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE avg_elo IS NULL OR team_0_elo IS NULL OR team_1_elo IS NULL)
        AS any_null,
    COUNT(*) FILTER (
        WHERE avg_elo IS NOT NULL
          AND team_0_elo IS NOT NULL
          AND team_1_elo IS NOT NULL
          AND ABS(avg_elo - (team_0_elo + team_1_elo) / 2.0) < 0.001
    ) AS exact_match_count,
    COUNT(*) FILTER (
        WHERE avg_elo IS NOT NULL
          AND team_0_elo IS NOT NULL
          AND team_1_elo IS NOT NULL
          AND ABS(avg_elo - (team_0_elo + team_1_elo) / 2.0) >= 0.001
    ) AS inexact_match_count,
    MAX(
        CASE
            WHEN avg_elo IS NOT NULL AND team_0_elo IS NOT NULL AND team_1_elo IS NOT NULL
            THEN ABS(avg_elo - (team_0_elo + team_1_elo) / 2.0)
        END
    ) AS max_abs_deviation
FROM matches_raw
"""
sql_queries["elo_formula_check"] = sql_elo_formula_check
elo_formula_df = db.fetch_df(sql_elo_formula_check)
print("T03-A: avg_elo == (team_0_elo + team_1_elo) / 2 check:")
print(elo_formula_df.T.to_string())

total_elo_rows = int(elo_formula_df["total_rows"].iloc[0])
any_null_elo = int(elo_formula_df["any_null"].iloc[0])
exact_match = int(elo_formula_df["exact_match_count"].iloc[0])
inexact_match = int(elo_formula_df["inexact_match_count"].iloc[0])
max_dev = float(elo_formula_df["max_abs_deviation"].iloc[0]) if elo_formula_df["max_abs_deviation"].iloc[0] is not None else None

non_null_rows = total_elo_rows - any_null_elo
exact_pct = 100.0 * exact_match / non_null_rows if non_null_rows > 0 else 0.0
print(f"\nNon-NULL ELO rows: {non_null_rows:,}")
print(f"Exact matches: {exact_match:,} ({exact_pct:.4f}%)")
print(f"Inexact: {inexact_match:,}")
print(f"Max deviation: {max_dev}")

# %%
# T03-B: Derive avg_elo from players_raw.old_rating in 1v1 matches
# For a 1v1 match: avg_elo_derived = AVG(old_rating) across 2 players
# Compare this against matches_raw.avg_elo
sql_elo_derivation_check = """
WITH true_1v1 AS (
    SELECT game_id
    FROM players_raw
    GROUP BY game_id
    HAVING COUNT(*) = 2
),
player_avg_elo AS (
    SELECT p.game_id,
           AVG(CAST(p.old_rating AS DOUBLE)) AS derived_avg_elo
    FROM players_raw p
    INNER JOIN true_1v1 t ON p.game_id = t.game_id
    WHERE p.old_rating IS NOT NULL
    GROUP BY p.game_id
    HAVING COUNT(*) = 2
)
SELECT
    COUNT(*) AS joined_count,
    COUNT(*) FILTER (WHERE m.avg_elo IS NOT NULL) AS both_non_null,
    COUNT(*) FILTER (
        WHERE m.avg_elo IS NOT NULL
          AND ABS(m.avg_elo - pa.derived_avg_elo) < 0.5
    ) AS within_half_elo,
    COUNT(*) FILTER (
        WHERE m.avg_elo IS NOT NULL
          AND ABS(m.avg_elo - pa.derived_avg_elo) < 1.0
    ) AS within_one_elo,
    AVG(ABS(m.avg_elo - pa.derived_avg_elo)) FILTER (WHERE m.avg_elo IS NOT NULL)
        AS mean_abs_deviation,
    MAX(ABS(m.avg_elo - pa.derived_avg_elo)) FILTER (WHERE m.avg_elo IS NOT NULL)
        AS max_abs_deviation,
    PERCENTILE_CONT(0.5) WITHIN GROUP (
        ORDER BY ABS(m.avg_elo - pa.derived_avg_elo)
    ) FILTER (WHERE m.avg_elo IS NOT NULL) AS median_abs_deviation
FROM player_avg_elo pa
INNER JOIN matches_raw m ON m.game_id = pa.game_id
"""
sql_queries["elo_derivation_check"] = sql_elo_derivation_check
print("\nT03-B: Deriving avg_elo from players_raw.old_rating in 1v1 matches...")
elo_deriv_df = db.fetch_df(sql_elo_derivation_check)
print(elo_deriv_df.T.to_string())

joined_count = int(elo_deriv_df["joined_count"].iloc[0])
both_non_null = int(elo_deriv_df["both_non_null"].iloc[0])
within_half = int(elo_deriv_df["within_half_elo"].iloc[0])
within_one = int(elo_deriv_df["within_one_elo"].iloc[0])
mean_dev = float(elo_deriv_df["mean_abs_deviation"].iloc[0]) if elo_deriv_df["mean_abs_deviation"].iloc[0] is not None else None
max_dev_cross = float(elo_deriv_df["max_abs_deviation"].iloc[0]) if elo_deriv_df["max_abs_deviation"].iloc[0] is not None else None
median_dev = float(elo_deriv_df["median_abs_deviation"].iloc[0]) if elo_deriv_df["median_abs_deviation"].iloc[0] is not None else None

pct_within_half = 100.0 * within_half / both_non_null if both_non_null > 0 else 0.0
pct_within_one = 100.0 * within_one / both_non_null if both_non_null > 0 else 0.0
print(f"\nJoined 1v1 matches: {joined_count:,}")
print(f"Both ELOs non-null: {both_non_null:,}")
print(f"Within 0.5 ELO: {within_half:,} ({pct_within_half:.2f}%)")
print(f"Within 1.0 ELO: {within_one:,} ({pct_within_one:.2f}%)")
print(f"Mean abs deviation: {mean_dev}")
print(f"Median abs deviation: {median_dev}")
print(f"Max abs deviation: {max_dev_cross}")

# %%
# T03-C: Spearman correlation on 100K RESERVOIR sample
# Compare avg_elo (matches) with derived_avg_elo from players_raw.old_rating
sql_spearman_sample = """
WITH true_1v1 AS (
    SELECT game_id
    FROM players_raw
    GROUP BY game_id
    HAVING COUNT(*) = 2
),
player_avg AS (
    SELECT p.game_id,
           AVG(CAST(p.old_rating AS DOUBLE)) AS player_avg_old_rating
    FROM players_raw p
    INNER JOIN true_1v1 t ON p.game_id = t.game_id
    WHERE p.old_rating IS NOT NULL
    GROUP BY p.game_id
    HAVING COUNT(*) = 2
),
joined AS (
    SELECT
        m.avg_elo,
        pa.player_avg_old_rating,
        m.team_0_elo,
        m.team_1_elo
    FROM player_avg pa
    INNER JOIN matches_raw m ON m.game_id = pa.game_id
    WHERE m.avg_elo IS NOT NULL
      AND m.team_0_elo IS NOT NULL
      AND m.team_1_elo IS NOT NULL
)
SELECT *
FROM joined
USING SAMPLE RESERVOIR(100000)
"""
sql_queries["spearman_sample"] = sql_spearman_sample
print("\nT03-C: Drawing 100K RESERVOIR sample for Spearman correlation...")
sample_df = db.fetch_df(sql_spearman_sample)
print(f"Sample size: {len(sample_df):,}")

# Compute Spearman correlations
rho_avg_vs_player, pval_avg_vs_player = sp_stats.spearmanr(
    sample_df["avg_elo"].dropna(),
    sample_df["player_avg_old_rating"].dropna()
)
rho_t0_vs_player, pval_t0_vs_player = sp_stats.spearmanr(
    sample_df["team_0_elo"].dropna(),
    sample_df["player_avg_old_rating"].dropna()
)
rho_t1_vs_player, _ = sp_stats.spearmanr(
    sample_df["team_1_elo"].dropna(),
    sample_df["player_avg_old_rating"].dropna()
)
rho_t0_t1, _ = sp_stats.spearmanr(
    sample_df["team_0_elo"].dropna(),
    sample_df["team_1_elo"].dropna()
)

print(f"\nSpearman rho (avg_elo vs player_avg_old_rating): {rho_avg_vs_player:.6f}  p={pval_avg_vs_player:.2e}")
print(f"Spearman rho (team_0_elo vs player_avg_old_rating): {rho_t0_vs_player:.6f}")
print(f"Spearman rho (team_1_elo vs player_avg_old_rating): {rho_t1_vs_player:.6f}")
print(f"Spearman rho (team_0_elo vs team_1_elo): {rho_t0_t1:.6f}")

result["t03_elo_redundancy"] = {
    "avg_elo_formula_check": {
        "total_rows": total_elo_rows,
        "any_null_elo": any_null_elo,
        "non_null_rows": non_null_rows,
        "exact_match_count": exact_match,
        "exact_match_pct": round(exact_pct, 4),
        "inexact_match_count": inexact_match,
        "max_abs_deviation": max_dev,
    },
    "avg_elo_derivation_from_players": {
        "joined_1v1_count": joined_count,
        "both_non_null": both_non_null,
        "within_half_elo_count": within_half,
        "within_half_elo_pct": round(pct_within_half, 4),
        "within_one_elo_count": within_one,
        "within_one_elo_pct": round(pct_within_one, 4),
        "mean_abs_deviation": mean_dev,
        "median_abs_deviation": median_dev,
        "max_abs_deviation": max_dev_cross,
    },
    "spearman_sample_size": len(sample_df),
    "spearman_rho_avg_elo_vs_player_avg_old_rating": round(float(rho_avg_vs_player), 6),
    "spearman_pval_avg_elo_vs_player_avg_old_rating": float(pval_avg_vs_player),
    "spearman_rho_team0_elo_vs_player_avg_old_rating": round(float(rho_t0_vs_player), 6),
    "spearman_rho_team1_elo_vs_player_avg_old_rating": round(float(rho_t1_vs_player), 6),
    "spearman_rho_team0_elo_vs_team1_elo": round(float(rho_t0_t1), 6),
    "temporal_annotation": {
        "old_rating": "pre-game (temporal class: safe -- I3 compliant)",
        "new_rating": "post-game (temporal class: LEAKING -- must not be used as feature)",
        "avg_elo": "match-level pre-game aggregate (temporal class: safe if sourced from pre-game API snapshot)",
        "team_0_elo": "match-level pre-game aggregate",
        "team_1_elo": "match-level pre-game aggregate",
    },
}

# %% [markdown]
# ## T04: overviews_raw Content and replay_summary_raw Assessment
#
# overviews_raw is a singleton table (1 row) with nested STRUCT arrays.
# UNNEST all struct arrays: civs, openings, patches, groupings, changelog,
# tournament_stages.
#
# replay_summary_raw is a VARCHAR JSON column in players_raw. Assess:
# - What fraction are empty ('{}')?
# - Sample non-empty values.

# %%
# T04-A: overviews_raw basic structure
sql_overviews_basic = "SELECT * EXCLUDE (civs, openings, patches, groupings, changelog, tournament_stages) FROM overviews_raw"
sql_queries["overviews_basic"] = sql_overviews_basic
overviews_basic_df = db.fetch_df(sql_overviews_basic)
print("=== overviews_raw basic columns (excluding STRUCT arrays) ===")
print(overviews_basic_df.T.to_string())

# %%
# T04-B: UNNEST civs array
sql_civs = """
SELECT
    unnested.name AS civ_name,
    unnested.value AS match_count
FROM (
    SELECT UNNEST(civs) AS unnested
    FROM overviews_raw
)
ORDER BY match_count DESC
LIMIT 20
"""
sql_queries["overviews_civs"] = sql_civs
civs_df = db.fetch_df(sql_civs)
print(f"\n=== overviews_raw.civs (top 20 of {len(db.fetch_df('SELECT UNNEST(civs) FROM overviews_raw'))} civs) ===")
print(civs_df.to_string(index=False))

# %%
# T04-C: UNNEST openings array
sql_openings = """
SELECT
    unnested.name AS opening_name,
    unnested.value AS match_count
FROM (
    SELECT UNNEST(openings) AS unnested
    FROM overviews_raw
)
ORDER BY match_count DESC
LIMIT 20
"""
sql_queries["overviews_openings"] = sql_openings
openings_df = db.fetch_df(sql_openings)
print(f"\n=== overviews_raw.openings (top 20) ===")
print(openings_df.to_string(index=False))

# %%
# T04-D: UNNEST patches array
sql_patches = """
SELECT
    unnested.number AS patch_number,
    unnested.label AS patch_label,
    unnested.release_date AS release_date,
    unnested.published AS published,
    unnested.total_games AS total_games
FROM (
    SELECT UNNEST(patches) AS unnested
    FROM overviews_raw
)
ORDER BY release_date DESC NULLS LAST
"""
sql_queries["overviews_patches"] = sql_patches
patches_df = db.fetch_df(sql_patches)
print(f"\n=== overviews_raw.patches ({len(patches_df)} patches) ===")
print(patches_df.to_string(index=False))

# %%
# T04-E: UNNEST groupings array (ELO groupings)
sql_groupings = """
SELECT
    unnested.name AS group_name,
    unnested.label AS group_label
FROM (
    SELECT UNNEST(groupings) AS unnested
    FROM overviews_raw
)
ORDER BY group_name
"""
sql_queries["overviews_groupings"] = sql_groupings
groupings_df = db.fetch_df(sql_groupings)
print(f"\n=== overviews_raw.groupings ({len(groupings_df)} groups) ===")
print(groupings_df.to_string(index=False))

# %%
# T04-F: UNNEST changelog array
sql_changelog = """
SELECT
    unnested.change_time AS change_time,
    unnested.version AS version,
    ARRAY_LENGTH(unnested.changes) AS num_changes
FROM (
    SELECT UNNEST(changelog) AS unnested
    FROM overviews_raw
)
ORDER BY change_time DESC NULLS LAST
LIMIT 20
"""
sql_queries["overviews_changelog"] = sql_changelog
changelog_df = db.fetch_df(sql_changelog)
print(f"\n=== overviews_raw.changelog (latest 20 entries) ===")
print(changelog_df.to_string(index=False))

# %%
# T04-G: tournament_stages
sql_tournament_stages = """
SELECT UNNEST(tournament_stages) AS stage
FROM overviews_raw
"""
sql_queries["overviews_tournament_stages"] = sql_tournament_stages
stages_df = db.fetch_df(sql_tournament_stages)
print(f"\n=== overviews_raw.tournament_stages ({len(stages_df)} stages) ===")
print(stages_df.to_string(index=False))

# %%
# T04-H: replay_summary_raw assessment in players_raw
sql_replay_summary_stats = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE replay_summary_raw IS NULL) AS null_count,
    COUNT(*) FILTER (WHERE replay_summary_raw = '{}') AS empty_object_count,
    COUNT(*) FILTER (WHERE TRIM(replay_summary_raw) = '') AS empty_string_count,
    COUNT(*) FILTER (
        WHERE replay_summary_raw IS NOT NULL
          AND replay_summary_raw != '{}'
          AND TRIM(replay_summary_raw) != ''
    ) AS non_empty_count,
    MIN(LENGTH(replay_summary_raw)) AS min_length,
    MAX(LENGTH(replay_summary_raw)) AS max_length,
    APPROX_COUNT_DISTINCT(replay_summary_raw) AS approx_distinct_values
FROM players_raw
"""
sql_queries["replay_summary_stats"] = sql_replay_summary_stats
print("\nT04-H: replay_summary_raw assessment...")
replay_stats_df = db.fetch_df(sql_replay_summary_stats)
print(replay_stats_df.T.to_string())

total_replay = int(replay_stats_df["total_rows"].iloc[0])
null_replay = int(replay_stats_df["null_count"].iloc[0])
empty_obj_replay = int(replay_stats_df["empty_object_count"].iloc[0])
empty_str_replay = int(replay_stats_df["empty_string_count"].iloc[0])
non_empty_replay = int(replay_stats_df["non_empty_count"].iloc[0])
max_len_replay = int(replay_stats_df["max_length"].iloc[0]) if replay_stats_df["max_length"].iloc[0] is not None else 0

empty_total = null_replay + empty_obj_replay + empty_str_replay
empty_pct = 100.0 * empty_total / total_replay
non_empty_pct = 100.0 * non_empty_replay / total_replay

print(f"\nTotal player rows: {total_replay:,}")
print(f"NULL: {null_replay:,}")
print(f"Empty object '{{}}': {empty_obj_replay:,}")
print(f"Empty string: {empty_str_replay:,}")
print(f"Combined empty: {empty_total:,} ({empty_pct:.2f}%)")
print(f"Non-empty: {non_empty_replay:,} ({non_empty_pct:.2f}%)")
print(f"Max length: {max_len_replay:,} chars")

# %%
# T04-I: Sample non-empty replay_summary_raw values
if non_empty_replay > 0:
    sql_replay_sample = """
    SELECT
        game_id,
        LENGTH(replay_summary_raw) AS len,
        LEFT(replay_summary_raw, 300) AS preview
    FROM players_raw
    WHERE replay_summary_raw IS NOT NULL
      AND replay_summary_raw != '{}'
      AND TRIM(replay_summary_raw) != ''
    USING SAMPLE RESERVOIR(5)
    ORDER BY len DESC
    """
    sql_queries["replay_summary_sample"] = sql_replay_sample
    replay_sample_df = db.fetch_df(sql_replay_sample)
    print("\nSample non-empty replay_summary_raw values:")
    for _, row in replay_sample_df.iterrows():
        print(f"  game_id={row['game_id']} len={row['len']}")
        print(f"  preview: {row['preview'][:200]}")
        print()
    replay_sample_preview = replay_sample_df[["game_id", "len", "preview"]].to_dict(orient="records")
else:
    replay_sample_preview = []
    print("No non-empty replay_summary_raw values found -- skipping sample.")

result["t04_overviews_and_replay"] = {
    "overviews_raw": {
        "row_count": 1,
        "last_updated": str(overviews_basic_df["last_updated"].iloc[0]) if "last_updated" in overviews_basic_df.columns else None,
        "total_match_count": int(overviews_basic_df["total_match_count"].iloc[0]) if "total_match_count" in overviews_basic_df.columns else None,
        "civs_count": len(db.fetch_df("SELECT UNNEST(civs) FROM overviews_raw")),
        "openings_count": len(openings_df),
        "patches_count": len(patches_df),
        "patches_date_range": {
            "min": str(patches_df["release_date"].min()) if len(patches_df) > 0 and "release_date" in patches_df.columns else None,
            "max": str(patches_df["release_date"].max()) if len(patches_df) > 0 and "release_date" in patches_df.columns else None,
        },
        "groupings_count": len(groupings_df),
        "changelog_entries": len(db.fetch_df(sql_changelog.replace("LIMIT 20", ""))),
        "tournament_stages_count": len(stages_df),
        "tournament_stages": stages_df["stage"].tolist() if len(stages_df) > 0 else [],
    },
    "replay_summary_raw": {
        "total_rows": total_replay,
        "null_count": null_replay,
        "empty_object_count": empty_obj_replay,
        "empty_string_count": empty_str_replay,
        "combined_empty_count": empty_total,
        "combined_empty_pct": round(empty_pct, 4),
        "non_empty_count": non_empty_replay,
        "non_empty_pct": round(non_empty_pct, 4),
        "max_length_chars": max_len_replay,
        "sample_non_empty": replay_sample_preview,
    },
}

# %% [markdown]
# ## T05: Table Utility Verdicts
#
# Evidence-backed per-table verdict derived from T01-T04 findings.

# %%
# Derive verdicts from query results (not assumed)
elo_avg_exact_pct = result["t03_elo_redundancy"]["avg_elo_formula_check"]["exact_match_pct"]
elo_cross_within_half_pct = result["t03_elo_redundancy"]["avg_elo_derivation_from_players"]["within_half_elo_pct"]
spearman_rho = result["t03_elo_redundancy"]["spearman_rho_avg_elo_vs_player_avg_old_rating"]
replay_non_empty_pct = result["t04_overviews_and_replay"]["replay_summary_raw"]["non_empty_pct"]

print("=== T05: Evidence-Backed Table Utility Verdicts ===\n")

# matches_raw verdict
print("--- matches_raw ---")
print(f"  UNIQUE contribution: started_timestamp (temporal anchor), duration, irl_duration,")
print(f"  map, leaderboard, patch, mirror, replay_enhanced, game_type, game_speed,")
print(f"  starting_age, raw_match_type")
print(f"  ELO columns (avg_elo, team_0_elo, team_1_elo): Spearman rho={spearman_rho:.4f} with")
print(f"  player avg old_rating. avg_elo = (team_0 + team_1)/2 holds at {elo_avg_exact_pct:.2f}% of non-NULL rows.")
print(f"  avg_elo cross-table derivable within 0.5: {elo_cross_within_half_pct:.2f}%")
print(f"  VERDICT: ESSENTIAL -- provides started_timestamp (I3 temporal anchor) and")
print(f"  match-level context features not available in players_raw.")

# players_raw verdict
print("\n--- players_raw ---")
print(f"  UNIQUE contribution: winner (target variable), old_rating (pre-game ELO),")
print(f"  new_rating (post-game ELO -- LEAKING), civ, opening, team,")
print(f"  age uptimes (feudal/castle/imperial), profile_id, match_rating_diff")
print(f"  VERDICT: ESSENTIAL -- contains winner (target) and player-level features.")
print(f"  new_rating must be EXCLUDED from all feature sets (temporal leakage per I3).")

# overviews_raw verdict
patches_count = result["t04_overviews_and_replay"]["overviews_raw"]["patches_count"]
civs_count = result["t04_overviews_and_replay"]["overviews_raw"]["civs_count"]
print(f"\n--- overviews_raw ---")
print(f"  Structure: {patches_count} patches (with release dates), {civs_count} civs,")
print(f"  {result['t04_overviews_and_replay']['overviews_raw']['openings_count']} openings,")
print(f"  {result['t04_overviews_and_replay']['overviews_raw']['groupings_count']} ELO groupings")
print(f"  Patches provide: patch_number -> release_date mapping (not elsewhere in raw tables)")
print(f"  matches_raw.patch column can be JOIN-enriched with this date mapping")
print(f"  VERDICT: SUPPLEMENTARY REFERENCE -- singleton lookup table for patch metadata.")
print(f"  No prediction-critical features, but patches array provides patch->date mapping")
print(f"  useful for temporal stratification by game version.")

# replay_summary_raw verdict
print(f"\n--- replay_summary_raw (column in players_raw) ---")
print(f"  Non-empty: {non_empty_replay:,} / {total_replay:,} ({replay_non_empty_pct:.2f}%)")
if replay_non_empty_pct < 5.0:
    replay_verdict = "LOW UTILITY -- predominantly empty; not viable as a feature source at current fill rate."
elif replay_non_empty_pct < 50.0:
    replay_verdict = "PARTIAL UTILITY -- significant non-empty fraction; content warrants further investigation."
else:
    replay_verdict = "HIGH UTILITY -- majority non-empty; content requires detailed parsing assessment."
print(f"  VERDICT: {replay_verdict}")

result["t05_verdicts"] = {
    "matches_raw": {
        "verdict": "ESSENTIAL",
        "rationale": (
            f"Provides started_timestamp (sole temporal anchor -- I3 critical), "
            f"map, leaderboard, patch, duration, mirror, and other match-level context. "
            f"ELO columns (avg_elo, team_0/1_elo) have Spearman rho={spearman_rho:.4f} "
            f"with player old_rating (near-perfect redundancy), so match-level ELOs are "
            f"derivable from players_raw but not vice versa for started_timestamp."
        ),
        "unique_columns": sorted(matches_only),
        "elo_derivable_from_players": elo_cross_within_half_pct > 95.0,
        "elo_cross_within_half_pct": round(elo_cross_within_half_pct, 4),
        "spearman_rho_elo_match_vs_player": spearman_rho,
    },
    "players_raw": {
        "verdict": "ESSENTIAL",
        "rationale": (
            "Contains winner (prediction target -- no alternative), old_rating "
            "(pre-game player ELO -- I3 safe), civ, opening, age uptimes, team. "
            "new_rating is LEAKING (post-game) and must be excluded from features."
        ),
        "unique_columns": sorted(players_only),
        "new_rating_leaks": True,
        "new_rating_note": "post-game ELO -- temporal leakage per I3 -- must not be used as feature",
    },
    "overviews_raw": {
        "verdict": "SUPPLEMENTARY REFERENCE",
        "rationale": (
            f"Singleton lookup. Provides {patches_count}-entry patch->release_date mapping "
            f"not available elsewhere. Can enrich matches_raw.patch column. "
            f"No direct prediction-critical columns."
        ),
        "patches_count": patches_count,
        "provides_patch_date_mapping": True,
    },
    "replay_summary_raw": {
        "verdict": replay_verdict,
        "non_empty_pct": round(replay_non_empty_pct, 4),
        "rationale": (
            f"{non_empty_pct:.2f}% non-empty rows ({non_empty_replay:,} / {total_replay:,}). "
            f"Max content length: {max_len_replay:,} chars."
        ),
    },
}

print("\n=== Summary ===")
for tbl, v in result["t05_verdicts"].items():
    print(f"  {tbl}: {v['verdict']}")

# %% [markdown]
# ## T06: Save Artifacts

# %%
result["sql_queries"] = sql_queries

output_json = profiling_dir / "01_03_03_table_utility.json"
with open(output_json, "w") as f:
    json.dump(result, f, indent=2, default=str)
print(f"JSON artifact saved: {output_json}")

# %%
# T06-B: Markdown report with embedded SQL (Invariant #6)
md_lines = [
    "# Step 01_03_03 -- Table Utility Assessment: aoestats",
    "",
    "**Date:** 2026-04-15  ",
    "**Dataset:** aoestats  ",
    "**Pipeline Section:** 01_03 -- Systematic Data Profiling  ",
    "",
    "## Scope",
    "",
    "Empirical assessment of all 3 raw tables (matches_raw, players_raw, overviews_raw)",
    "for prediction pipeline utility. Column overlap, join integrity, ELO redundancy,",
    "overviews_raw STRUCT content, and replay_summary_raw fill rate.",
    "",
    "## T01: Column Overlap",
    "",
    f"- matches_raw: {result['t01_column_overlap']['matches_raw_column_count']} columns",
    f"- players_raw: {result['t01_column_overlap']['players_raw_column_count']} columns",
    f"- Shared columns ({len(result['t01_column_overlap']['shared_columns'])}): "
    + ", ".join(f"`{c}`" for c in result['t01_column_overlap']['shared_columns']),
    f"- matches_raw exclusive ({len(result['t01_column_overlap']['matches_raw_exclusive'])}): "
    + ", ".join(f"`{c}`" for c in result['t01_column_overlap']['matches_raw_exclusive']),
    f"- players_raw exclusive ({len(result['t01_column_overlap']['players_raw_exclusive'])}): "
    + ", ".join(f"`{c}`" for c in result['t01_column_overlap']['players_raw_exclusive']),
    "",
    "**Confirmed:** `game_id` is the join key (present in both tables).  ",
    "**Confirmed:** `winner` is exclusive to `players_raw`.  ",
    "**Confirmed:** `started_timestamp` is exclusive to `matches_raw`.  ",
    "",
    "```sql",
    sql_queries["describe_matches"],
    "-- (also for players_raw)",
    "```",
    "",
    "## T02: Join Integrity",
    "",
    f"- Orphan matches (no players): {result['t02_join_integrity']['orphan_matches_in_matches_not_players']:,}",
    f"  (validated against 01_03_01 MATCHES_WITHOUT_PLAYERS = {MATCHES_WITHOUT_PLAYERS:,})",
    f"- Orphan player game_ids (no match): {result['t02_join_integrity']['orphan_player_game_ids_not_in_matches']:,}",
    f"- matches_raw: {result['t02_join_integrity']['matches_distinct_game_ids']:,} distinct game_ids in"
    f" {result['t02_join_integrity']['matches_total_rows']:,} rows"
    f" ({result['t02_join_integrity']['matches_uniqueness_pct']:.4f}% unique)",
    f"- players_raw: {result['t02_join_integrity']['players_distinct_game_ids']:,} distinct game_ids,"
    f" avg {result['t02_join_integrity']['players_avg_rows_per_game_id']:.2f} rows/game_id",
    "",
    "```sql",
    sql_queries["orphan_matches"],
    "```",
    "",
    "```sql",
    sql_queries["orphan_players"],
    "```",
    "",
    "## T03: ELO Redundancy",
    "",
    f"- avg_elo = (team_0_elo + team_1_elo) / 2: "
    f"{result['t03_elo_redundancy']['avg_elo_formula_check']['exact_match_pct']:.4f}% exact match",
    f"- avg_elo derivable from players old_rating (1v1 matches, within 0.5 ELO): "
    f"{result['t03_elo_redundancy']['avg_elo_derivation_from_players']['within_half_elo_pct']:.4f}%",
    f"- Spearman rho (avg_elo vs player_avg_old_rating, n=100K): "
    f"{result['t03_elo_redundancy']['spearman_rho_avg_elo_vs_player_avg_old_rating']:.6f}",
    "",
    "**Temporal annotation:**",
    "- `old_rating`: pre-game rating -- temporally safe (I3 compliant)",
    "- `new_rating`: post-game rating -- **LEAKING** -- must not be used as a feature",
    "",
    "```sql",
    sql_queries["elo_formula_check"],
    "```",
    "",
    "```sql",
    sql_queries["elo_derivation_check"],
    "```",
    "",
    "```sql",
    sql_queries["spearman_sample"],
    "```",
    "",
    "## T04: overviews_raw and replay_summary_raw",
    "",
    f"- overviews_raw: 1 row (singleton reference)",
    f"  - {result['t04_overviews_and_replay']['overviews_raw']['patches_count']} patches"
    f" (release_date range: {result['t04_overviews_and_replay']['overviews_raw']['patches_date_range']['min']}"
    f" to {result['t04_overviews_and_replay']['overviews_raw']['patches_date_range']['max']})",
    f"  - {result['t04_overviews_and_replay']['overviews_raw']['civs_count']} civs, "
    f"{result['t04_overviews_and_replay']['overviews_raw']['openings_count']} openings, "
    f"{result['t04_overviews_and_replay']['overviews_raw']['groupings_count']} ELO groupings",
    f"  - tournament_stages: {result['t04_overviews_and_replay']['overviews_raw']['tournament_stages']}",
    "",
    f"- replay_summary_raw (players_raw column):",
    f"  - Non-empty: {result['t04_overviews_and_replay']['replay_summary_raw']['non_empty_pct']:.4f}%"
    f" ({result['t04_overviews_and_replay']['replay_summary_raw']['non_empty_count']:,} rows)",
    f"  - Empty ('{{}}' or NULL): {result['t04_overviews_and_replay']['replay_summary_raw']['combined_empty_pct']:.4f}%",
    f"  - Max content length: {result['t04_overviews_and_replay']['replay_summary_raw']['max_length_chars']:,} chars",
    "",
    "```sql",
    sql_queries["replay_summary_stats"],
    "```",
    "",
    "## T05: Verdicts",
    "",
]
for tbl, v in result["t05_verdicts"].items():
    md_lines.append(f"### {tbl}")
    md_lines.append(f"**Verdict:** {v['verdict']}  ")
    md_lines.append(f"**Rationale:** {v['rationale']}")
    md_lines.append("")

md_lines += [
    "## Artifact",
    "",
    f"`01_03_03_table_utility.json` -- JSON with all query results, SQL, and verdicts.",
    "",
]

output_md = profiling_dir / "01_03_03_table_utility.md"
with open(output_md, "w") as f:
    f.write("\n".join(md_lines))
print(f"Markdown artifact saved: {output_md}")

print("\n=== Step 01_03_03 complete ===")
print(f"JSON: {output_json}")
print(f"MD:   {output_md}")
