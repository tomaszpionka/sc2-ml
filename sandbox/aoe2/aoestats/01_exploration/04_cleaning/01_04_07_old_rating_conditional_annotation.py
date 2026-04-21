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
# # Step 01_04_07 — old_rating CONDITIONAL_PRE_GAME Phase 01 Annotation
#
# **Phase:** 01 — Data Exploration
# **Pipeline Section:** 01_04 — Data Cleaning
# **Step:** 01_04_07
# **Dataset:** aoestats
# **Predecessors:** 01_04_01–01_04_06
# **Invariants touched:** I3, I6, I7
#
# **Purpose:** Apply a Phase 01 cleaning-rule annotation that makes `old_rating`
# semantically usable downstream. Adds derived column `time_since_prior_match_days`
# to `player_history_all` VIEW via DDL amendment (following the canonical_slot
# precedent pattern from 01_04_03b). Selects the CONDITIONAL_PRE_GAME threshold
# empirically from data using pooled agreement rates on `random_map`.
#
# **Post-Mode-A framing:** The original WP-6 plan pre-specified a 7-day cutoff,
# but Mode A identified this as inconsistent: the 1-7d bucket (0.859) fails the
# 0.90 stratum gate used in WP-4. The revised approach computes pooled `<N days`
# agreement for N ∈ {1, 2, 3, 7} and picks the LARGEST N with pooled agreement
# >= 0.90 on `random_map`. Additionally, a 4×4 leaderboard × time-gap
# stratification determines whether the classification can generalize globally
# or is limited to `random_map` only.
#
# **CAST discipline (DS-AOESTATS-IDENTITY-04):** `profile_id` is stored as DOUBLE;
# `CAST(profile_id AS BIGINT)` is lossless (all values < 2^53). LAG partition key
# uses CAST. Tie-breaker: `game_id` (same as 01_04_06).
#
# **Date:** 2026-04-21

# %% [markdown]
# ## Motivation
#
# Step 01_04_06 (WP-4) empirically falsified the unconditional PRE-GAME
# classification of `old_rating`. Key findings:
#
# **Per-time-gap on random_map (from 01_04_06):**
# | Bucket | n_pairs | agreement_rate |
# |--------|---------|----------------|
# | <1d    | 29,021,397 | 0.9440 |
# | 1-7d   | 4,661,976  | 0.8590 |
# | 7-30d  | 1,057,793  | 0.7076 |
# | >30d   | 534,031    | 0.6345 |
#
# **Per-leaderboard pooled (from 01_04_06):**
# | Leaderboard | agreement_rate |
# |-------------|----------------|
# | random_map        | 0.9210 |
# | team_random_map   | 0.8601 |
# | co_random_map     | 0.8552 |
# | co_team_random_map | 0.7867 |
#
# **Interpretation:** aoestats.io API updates `old_rating` at seasonal/leaderboard
# boundaries independent of per-match results. Across those boundaries,
# `old_rating[t+1] != new_rating[t]` for mechanistic reasons (rating resets,
# seasonal updates). Agreement is high for dense play (<1d gap) but degrades
# with longer gaps.
#
# **Mode A catch:** The original 7-day cutoff included the 1-7d bucket (0.859),
# which fails the 0.90 stratum gate. Additionally, the 01_04_06 per-time-gap
# stratification was random_map-only — it does not justify a GLOBAL cutoff
# without verifying all 4 leaderboards at the chosen N.
#
# **This step:** Computes pooled `<N days` agreement on random_map for N ∈ {1,2,3,7},
# picks N* = largest N with pooled agreement >= 0.90, then verifies the 4×4
# leaderboard × time-gap stratification to determine SCOPE.

# %% [markdown]
# ## Cell 1 — Imports

# %%
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

from rts_predict.common.notebook_utils import (
    get_notebook_db,
    get_reports_dir,
    setup_notebook_logging,
)

logger = setup_notebook_logging()
print("Imports complete.")

# %% [markdown]
# ## Cell 2 — DuckDB Connection
#
# Read-write required: this step amends the `player_history_all` VIEW via DDL.

# %%
db = get_notebook_db("aoe2", "aoestats", read_only=False)
con = db.con
duckdb_version = con.execute("SELECT version()").fetchone()[0]
print(f"DuckDB connected (read-write). Version: {duckdb_version}")

# %% [markdown]
# ## Cell 3 — Reports Directory + Artifact Paths

# %%
reports_dir = get_reports_dir("aoe2", "aoestats")
artifacts_dir = reports_dir / "artifacts" / "01_exploration" / "04_cleaning"
artifacts_dir.mkdir(parents=True, exist_ok=True)
json_path = artifacts_dir / "01_04_07_old_rating_conditional_annotation.json"
md_path = artifacts_dir / "01_04_07_old_rating_conditional_annotation.md"
print(f"Artifacts target: {artifacts_dir}")

# %% [markdown]
# ## Cell 4 — Baseline Row Count (Pre-Amendment)
#
# Record row count before DDL amendment; must be 107,626,399.

# %%
row_count_pre = con.execute("SELECT COUNT(*) FROM player_history_all").fetchone()[0]
print(f"Row count pre-amendment: {row_count_pre:,}")
assert row_count_pre == 107_626_399, (
    f"Unexpected pre-amendment row count: {row_count_pre:,} (expected 107,626,399)"
)
print("Pre-amendment row count VERIFIED: 107,626,399")

# %% [markdown]
# ## Threshold Selection — BLOCKER-1 Fix
#
# **Hypothesis (I7):** The CONDITIONAL_PRE_GAME threshold should be the LARGEST
# N ∈ {1, 2, 3, 7} days such that the pooled agreement rate on `random_map` for
# pairs with `time_since_prior_match_days < N` clears the WP-4 0.90 stratum gate.
#
# **Falsifier:** If no N in {1, 2, 3, 7} clears 0.90, the analysis halts and
# escalates. If only N=1 clears, SCOPE is automatically constrained to `<1d`
# (very tight). The largest N that passes is chosen to maximize coverage.
#
# For each N, the pooled agreement on random_map is computed as:
# AVG(old_rating == prev_new_rating) for pairs where gap_days < N.
# (This uses the existing `prev_new_rating` LAG pattern from 01_04_06.)

# %%
SQL_THRESHOLD_SELECTION = """
WITH deduped AS (
  SELECT DISTINCT
    CAST(p.profile_id AS BIGINT) AS profile_id_i64,
    m.leaderboard,
    m.started_timestamp,
    m.game_id,
    p.old_rating,
    p.new_rating
  FROM players_raw p
  JOIN matches_raw m USING (game_id)
  WHERE p.profile_id IS NOT NULL
    AND p.old_rating IS NOT NULL
    AND p.new_rating IS NOT NULL
    AND m.leaderboard = 'random_map'
),
with_lag AS (
  SELECT
    profile_id_i64,
    leaderboard,
    started_timestamp,
    game_id,
    old_rating,
    new_rating,
    LAG(new_rating) OVER (
      PARTITION BY profile_id_i64, leaderboard
      ORDER BY started_timestamp, game_id
    ) AS prev_new_rating,
    LAG(started_timestamp) OVER (
      PARTITION BY profile_id_i64, leaderboard
      ORDER BY started_timestamp, game_id
    ) AS prev_started_timestamp
  FROM deduped
),
pairs AS (
  SELECT *,
    CASE WHEN old_rating = prev_new_rating THEN 1 ELSE 0 END AS agreed,
    EXTRACT(EPOCH FROM (started_timestamp - prev_started_timestamp)) / 86400.0 AS gap_days
  FROM with_lag
  WHERE prev_new_rating IS NOT NULL
)
SELECT
  candidate_n,
  COUNT(*)                               AS n_pairs_eligible,
  AVG(agreed::DOUBLE)                    AS pooled_agreement
FROM pairs
CROSS JOIN (VALUES (1), (2), (3), (7)) AS candidates(candidate_n)
WHERE gap_days < candidate_n
GROUP BY candidate_n
ORDER BY candidate_n
"""

threshold_df = con.execute(SQL_THRESHOLD_SELECTION).df()
print("Threshold selection table (pooled <N days agreement on random_map):")
print(threshold_df.to_string(index=False))

# %% [markdown]
# ### Choose N*
#
# N* = largest N in {1, 2, 3, 7} where pooled_agreement >= 0.90.

# %%
THRESHOLD_GATE = 0.90
candidates_passing = threshold_df[threshold_df["pooled_agreement"] >= THRESHOLD_GATE]

if candidates_passing.empty:
    raise RuntimeError(
        "No candidate N in {1, 2, 3, 7} clears the 0.90 stratum gate on random_map. "
        "Halting — escalate to user before proceeding."
    )

N_STAR = int(candidates_passing["candidate_n"].max())
n_pairs_at_N_star = int(
    threshold_df.loc[threshold_df["candidate_n"] == N_STAR, "n_pairs_eligible"].iloc[0]
)
pooled_agreement_at_N_star = float(
    threshold_df.loc[threshold_df["candidate_n"] == N_STAR, "pooled_agreement"].iloc[0]
)

print(f"\nChosen N* = {N_STAR} days")
print(f"  Pooled agreement at <{N_STAR}d: {pooled_agreement_at_N_star:.6f}")
print(f"  n_pairs eligible: {n_pairs_at_N_star:,}")
print(f"  Argument: largest N in {{1,2,3,7}} where pooled agreement on random_map >= 0.90")

threshold_candidates = {}
for _, row in threshold_df.iterrows():
    threshold_candidates[int(row["candidate_n"])] = {
        "n_pairs_eligible": int(row["n_pairs_eligible"]),
        "pooled_agreement": round(float(row["pooled_agreement"]), 6),
    }

# %% [markdown]
# ## 4×4 Leaderboard × Time-Gap Stratification — BLOCKER-2 Fix
#
# **Hypothesis:** If all 4 leaderboards' agreement at `<N*` days clears 0.90,
# the CONDITIONAL_PRE_GAME classification generalizes globally (all leaderboards).
# Otherwise, it is scoped to `random_map` only.
#
# The full 4×4 table (4 leaderboards × 4 time-gap buckets) provides evidence for
# both the per-leaderboard rate at `<N*` and the behavior across time-gap buckets.

# %%
SQL_4X4_STRATIFICATION = f"""
WITH deduped AS (
  SELECT DISTINCT
    CAST(p.profile_id AS BIGINT) AS profile_id_i64,
    m.leaderboard,
    m.started_timestamp,
    m.game_id,
    p.old_rating,
    p.new_rating
  FROM players_raw p
  JOIN matches_raw m USING (game_id)
  WHERE p.profile_id IS NOT NULL
    AND p.old_rating IS NOT NULL
    AND p.new_rating IS NOT NULL
    AND m.leaderboard IN (
      'random_map', 'team_random_map', 'co_random_map', 'co_team_random_map'
    )
),
with_lag AS (
  SELECT
    profile_id_i64,
    leaderboard,
    started_timestamp,
    game_id,
    old_rating,
    new_rating,
    LAG(new_rating) OVER (
      PARTITION BY profile_id_i64, leaderboard
      ORDER BY started_timestamp, game_id
    ) AS prev_new_rating,
    LAG(started_timestamp) OVER (
      PARTITION BY profile_id_i64, leaderboard
      ORDER BY started_timestamp, game_id
    ) AS prev_started_timestamp
  FROM deduped
),
pairs AS (
  SELECT *,
    CASE WHEN old_rating = prev_new_rating THEN 1 ELSE 0 END AS agreed,
    EXTRACT(EPOCH FROM (started_timestamp - prev_started_timestamp)) / 86400.0 AS gap_days
  FROM with_lag
  WHERE prev_new_rating IS NOT NULL
),
bucketed AS (
  SELECT
    leaderboard,
    CASE
      WHEN gap_days < 1   THEN '<1d'
      WHEN gap_days < 7   THEN '1-7d'
      WHEN gap_days < 30  THEN '7-30d'
      ELSE                     '>30d'
    END AS time_gap_bucket,
    agreed
  FROM pairs
)
SELECT
  leaderboard,
  time_gap_bucket,
  COUNT(*)            AS n_pairs,
  AVG(agreed::DOUBLE) AS agreement_rate
FROM bucketed
GROUP BY leaderboard, time_gap_bucket
ORDER BY leaderboard, MIN(
  CASE time_gap_bucket
    WHEN '<1d'   THEN 0
    WHEN '1-7d'  THEN 1
    WHEN '7-30d' THEN 2
    ELSE              3
  END
)
"""

strat_df = con.execute(SQL_4X4_STRATIFICATION).df()
print("4×4 Leaderboard × Time-Gap Stratification:")
print(strat_df.to_string(index=False))

# %% [markdown]
# ### Per-leaderboard agreement at < N* days

# %%
SQL_PER_LB_AT_N_STAR = f"""
WITH deduped AS (
  SELECT DISTINCT
    CAST(p.profile_id AS BIGINT) AS profile_id_i64,
    m.leaderboard,
    m.started_timestamp,
    m.game_id,
    p.old_rating,
    p.new_rating
  FROM players_raw p
  JOIN matches_raw m USING (game_id)
  WHERE p.profile_id IS NOT NULL
    AND p.old_rating IS NOT NULL
    AND p.new_rating IS NOT NULL
    AND m.leaderboard IN (
      'random_map', 'team_random_map', 'co_random_map', 'co_team_random_map'
    )
),
with_lag AS (
  SELECT
    profile_id_i64,
    leaderboard,
    started_timestamp,
    game_id,
    old_rating,
    new_rating,
    LAG(new_rating) OVER (
      PARTITION BY profile_id_i64, leaderboard
      ORDER BY started_timestamp, game_id
    ) AS prev_new_rating,
    LAG(started_timestamp) OVER (
      PARTITION BY profile_id_i64, leaderboard
      ORDER BY started_timestamp, game_id
    ) AS prev_started_timestamp
  FROM deduped
),
pairs AS (
  SELECT *,
    CASE WHEN old_rating = prev_new_rating THEN 1 ELSE 0 END AS agreed,
    EXTRACT(EPOCH FROM (started_timestamp - prev_started_timestamp)) / 86400.0 AS gap_days
  FROM with_lag
  WHERE prev_new_rating IS NOT NULL
    AND gap_days < {N_STAR}
)
SELECT
  leaderboard,
  COUNT(*)            AS n_pairs_at_cutoff,
  AVG(agreed::DOUBLE) AS agreement_at_cutoff
FROM pairs
GROUP BY leaderboard
ORDER BY leaderboard
"""

lb_at_N_star_df = con.execute(SQL_PER_LB_AT_N_STAR).df()
print(f"Per-leaderboard agreement at <{N_STAR}d:")
print(lb_at_N_star_df.to_string(index=False))

# %% [markdown]
# ### Determine SCOPE

# %%
per_lb_at_cutoff = {
    row["leaderboard"]: float(row["agreement_at_cutoff"])
    for _, row in lb_at_N_star_df.iterrows()
}

all_leaderboards = ["random_map", "team_random_map", "co_random_map", "co_team_random_map"]
lb_failures_at_N_star = {
    lb: rate for lb, rate in per_lb_at_cutoff.items() if rate < THRESHOLD_GATE
}

if len(lb_failures_at_N_star) == 0:
    SCOPE = "GLOBAL"
    scope_predicate = "TRUE"
    scope_argument = (
        f"All 4 leaderboards clear 0.90 at <{N_STAR}d cutoff. "
        "CONDITIONAL_PRE_GAME classification applies globally."
    )
else:
    SCOPE = "random_map_only"
    scope_predicate = "leaderboard = 'random_map'"
    scope_argument = (
        f"Not all leaderboards clear 0.90 at <{N_STAR}d cutoff. "
        f"Failures: {lb_failures_at_N_star}. "
        "CONDITIONAL_PRE_GAME classification scoped to random_map only."
    )

print(f"\nChosen SCOPE: {SCOPE}")
print(f"  Scope predicate: {scope_predicate}")
print(f"  Argument: {scope_argument}")
print(f"  Leaderboard failures at <{N_STAR}d: {lb_failures_at_N_star}")

# %% [markdown]
# ## Current VIEW DDL (for reference — from 01_04_01 artifact)
#
# Captured verbatim below before amendment. The VIEW currently has 14 columns.

# %%
CURRENT_DDL = """CREATE OR REPLACE VIEW player_history_all AS
WITH player_counts AS (
    SELECT game_id, COUNT(*) AS player_count
    FROM players_raw
    GROUP BY game_id
)
SELECT
    CAST(p.profile_id AS BIGINT) AS profile_id,
    p.game_id,
    m.started_timestamp,
    m.leaderboard,
    m.map,
    m.patch,
    pc.player_count,
    m.mirror,
    m.replay_enhanced,
    p.civ,
    p.team,
    NULLIF(p.old_rating, 0) AS old_rating,
    p.old_rating = 0        AS is_unrated,
    p.winner
FROM players_raw p
INNER JOIN matches_raw m ON p.game_id = m.game_id
INNER JOIN player_counts pc ON p.game_id = pc.game_id
WHERE p.profile_id IS NOT NULL
  AND m.started_timestamp IS NOT NULL"""

print("Current VIEW DDL (14 columns) recorded.")
print("Adding time_since_prior_match_days as column 15...")

# %% [markdown]
# ## Amended VIEW DDL — Adding time_since_prior_match_days
#
# The new column uses a LAG window function:
# - Partition: CAST(profile_id AS BIGINT), leaderboard (per-leaderboard rating systems)
# - Order: started_timestamp, game_id (tie-breaker matches 01_04_06)
# - CAST discipline: profile_id is DOUBLE; CAST to BIGINT is lossless (all < 2^53)
# - NULL semantics: first match per (profile_id, leaderboard) → LAG = NULL → gap = NULL

# %%
AMENDED_DDL = """CREATE OR REPLACE VIEW player_history_all AS
WITH player_counts AS (
    SELECT game_id, COUNT(*) AS player_count
    FROM players_raw
    GROUP BY game_id
),
lag_base AS (
    SELECT
        CAST(p.profile_id AS BIGINT) AS profile_id,
        p.game_id,
        m.started_timestamp,
        m.leaderboard,
        m.map,
        m.patch,
        pc.player_count,
        m.mirror,
        m.replay_enhanced,
        p.civ,
        p.team,
        NULLIF(p.old_rating, 0) AS old_rating,
        p.old_rating = 0        AS is_unrated,
        p.winner,
        LAG(m.started_timestamp) OVER (
            PARTITION BY CAST(p.profile_id AS BIGINT), m.leaderboard
            ORDER BY m.started_timestamp, m.game_id
        ) AS prev_started_timestamp
    FROM players_raw p
    INNER JOIN matches_raw m ON p.game_id = m.game_id
    INNER JOIN player_counts pc ON p.game_id = pc.game_id
    WHERE p.profile_id IS NOT NULL
      AND m.started_timestamp IS NOT NULL
)
SELECT
    profile_id,
    game_id,
    started_timestamp,
    leaderboard,
    map,
    patch,
    player_count,
    mirror,
    replay_enhanced,
    civ,
    team,
    old_rating,
    is_unrated,
    winner,
    CAST(
        EXTRACT(EPOCH FROM (started_timestamp - prev_started_timestamp)) / 86400.0
        AS DOUBLE
    ) AS time_since_prior_match_days
FROM lag_base"""

print("Amended DDL ready (15 columns).")

# %% [markdown]
# ## Execute VIEW Amendment
#
# DROP + CREATE the VIEW. Verify row count unchanged. Confirm new column in DESCRIBE.

# %%
con.execute("DROP VIEW IF EXISTS player_history_all")
con.execute(AMENDED_DDL)
print("VIEW player_history_all amended.")

# %% [markdown]
# ## Verification — Row Count Post-Amendment

# %%
row_count_post = con.execute("SELECT COUNT(*) FROM player_history_all").fetchone()[0]
print(f"Row count post-amendment: {row_count_post:,}")
assert row_count_post == row_count_pre, (
    f"Row count changed: pre={row_count_pre:,} post={row_count_post:,}"
)
print(f"Row count PRESERVED: {row_count_post:,}")

# %% [markdown]
# ## Verification — DESCRIBE (Confirm New Column)

# %%
describe_df = con.execute("DESCRIBE player_history_all").df()
print("DESCRIBE player_history_all:")
print(describe_df.to_string(index=False))
col_names = list(describe_df["column_name"])
assert "time_since_prior_match_days" in col_names, (
    "time_since_prior_match_days not found in DESCRIBE output"
)
assert len(col_names) == 15, f"Expected 15 columns, got {len(col_names)}: {col_names}"
print(f"\nColumn count: {len(col_names)} (expected 15) — VERIFIED")
print("time_since_prior_match_days present — VERIFIED")

# %% [markdown]
# ## Spot-Check: 10 (profile_id, leaderboard) Sequences
#
# For 10 players, verify positive gaps for non-first matches and NULL for first.

# %%
SQL_SPOT_CHECK = """
SELECT
    profile_id,
    leaderboard,
    started_timestamp,
    game_id,
    old_rating,
    time_since_prior_match_days,
    ROW_NUMBER() OVER (
        PARTITION BY profile_id, leaderboard
        ORDER BY started_timestamp, game_id
    ) AS seq_within_lb
FROM player_history_all
WHERE profile_id IN (
    SELECT profile_id
    FROM player_history_all
    WHERE leaderboard = 'random_map'
    GROUP BY profile_id
    HAVING COUNT(*) >= 5
    ORDER BY profile_id
    LIMIT 10
)
AND leaderboard = 'random_map'
ORDER BY profile_id, started_timestamp, game_id
LIMIT 50
"""

spot_df = con.execute(SQL_SPOT_CHECK).df()
print("Spot-check (10 players, random_map, first 50 rows):")
print(spot_df.to_string(index=False))

# Verify: first in sequence (seq=1) should have NULL gap
first_match_rows = spot_df[spot_df["seq_within_lb"] == 1]
null_first_count = first_match_rows["time_since_prior_match_days"].isna().sum()
print(f"\nFirst-in-sequence rows (seq=1): {len(first_match_rows)}")
print(f"  NULLs in time_since_prior_match_days: {null_first_count}")
assert null_first_count == len(first_match_rows), (
    f"Expected all first-match rows to have NULL gap; got {null_first_count}/{len(first_match_rows)}"
)
print("  All first-match rows have NULL gap — VERIFIED")

# Verify: non-first rows should have positive gaps
non_first_rows = spot_df[spot_df["seq_within_lb"] > 1].dropna(
    subset=["time_since_prior_match_days"]
)
negative_gaps = (non_first_rows["time_since_prior_match_days"] < 0).sum()
assert negative_gaps == 0, f"Found {negative_gaps} negative gap values"
print(f"  Non-first rows: {len(non_first_rows)} — all have non-negative gaps — VERIFIED")

# %% [markdown]
# ## First-Match NULL Rate (WARNING-3)
#
# Compute the fraction of rows where `time_since_prior_match_days IS NULL`.
# These are first-match rows per (profile_id, leaderboard). Per INVARIANTS.md §3
# + spec 02_00 §5.5: NULL → PRE-GAME (no prior-match cross-session risk).

# %%
SQL_NULL_RATE = """
SELECT
    COUNT(*)                                                          AS n_total,
    COUNT(*) FILTER (WHERE time_since_prior_match_days IS NULL)       AS n_null,
    COUNT(*) FILTER (WHERE time_since_prior_match_days IS NOT NULL)   AS n_non_null,
    AVG(CASE WHEN time_since_prior_match_days IS NULL THEN 1.0 ELSE 0.0 END)
                                                                      AS null_rate
FROM player_history_all
"""

null_result = con.execute(SQL_NULL_RATE).fetchone()
n_total, n_null, n_non_null, null_rate = null_result
null_rate = float(null_rate)

print(f"First-match NULL rate analysis:")
print(f"  n_total:    {n_total:,}")
print(f"  n_null:     {n_null:,}")
print(f"  n_non_null: {n_non_null:,}")
print(f"  null_rate:  {null_rate:.6f} ({null_rate:.2%})")
print()
print("NULL semantics: time_since_prior_match_days IS NULL → first match per")
print("(profile_id, leaderboard). No prior-match cross-session risk.")
print("Per INVARIANTS.md §3: NULL treated as PRE-GAME for the CONDITIONAL_PRE_GAME gate.")

# %% [markdown]
# ## Rating-Reset Correlation (ρ)
#
# Pearson correlation between `time_since_prior_match_days` and
# `|old_rating - LAG(new_rating)|` (disagreement magnitude) for rows where
# the prior new_rating is available. Positive ρ confirms that longer gaps
# correlate with larger rating disagreements (consistent with seasonal resets).

# %%
SQL_CORRELATION = """
WITH deduped AS (
  SELECT DISTINCT
    CAST(p.profile_id AS BIGINT) AS profile_id_i64,
    m.leaderboard,
    m.started_timestamp,
    m.game_id,
    p.old_rating,
    p.new_rating
  FROM players_raw p
  JOIN matches_raw m USING (game_id)
  WHERE p.profile_id IS NOT NULL
    AND p.old_rating IS NOT NULL
    AND p.new_rating IS NOT NULL
    AND m.leaderboard = 'random_map'
),
with_lag AS (
  SELECT
    profile_id_i64,
    leaderboard,
    started_timestamp,
    game_id,
    old_rating,
    new_rating,
    LAG(new_rating) OVER (
      PARTITION BY profile_id_i64, leaderboard
      ORDER BY started_timestamp, game_id
    ) AS prev_new_rating,
    LAG(started_timestamp) OVER (
      PARTITION BY profile_id_i64, leaderboard
      ORDER BY started_timestamp, game_id
    ) AS prev_started_timestamp
  FROM deduped
),
pairs AS (
  SELECT
    ABS(old_rating - prev_new_rating)                                   AS disagreement_abs,
    EXTRACT(EPOCH FROM (started_timestamp - prev_started_timestamp)) / 86400.0
                                                                        AS gap_days
  FROM with_lag
  WHERE prev_new_rating IS NOT NULL
    AND EXTRACT(EPOCH FROM (started_timestamp - prev_started_timestamp)) IS NOT NULL
)
SELECT gap_days, disagreement_abs
FROM pairs
WHERE gap_days IS NOT NULL
  AND disagreement_abs IS NOT NULL
USING SAMPLE 500000 ROWS (reservoir, 42)
"""

corr_df = con.execute(SQL_CORRELATION).df()
print(f"Correlation sample: {len(corr_df):,} pairs")

rho, pvalue = pearsonr(corr_df["gap_days"], corr_df["disagreement_abs"])
rho = float(rho)
print(f"Pearson ρ (gap_days vs |disagreement|): {rho:.6f}")
print(f"p-value: {pvalue:.2e}")
print()
if rho > 0:
    print(f"Positive ρ = {rho:.4f}: longer gaps correlate with larger rating disagreements.")
    print("Consistent with seasonal/boundary rating resets hypothesis.")
else:
    print(f"Unexpected ρ = {rho:.4f}.")

# %% [markdown]
# ## Summary

# %%
print("=" * 60)
print("SUMMARY — Step 01_04_07")
print("=" * 60)
print(f"N* (chosen threshold):       {N_STAR} days")
print(f"Pooled agreement at <{N_STAR}d:  {pooled_agreement_at_N_star:.6f}")
print(f"SCOPE:                        {SCOPE}")
print(f"Scope predicate:              {scope_predicate}")
print(f"First-match NULL rate:        {null_rate:.6f} ({null_rate:.2%})")
print(f"Pearson ρ:                    {rho:.6f}")
print(f"Row count pre:                {row_count_pre:,}")
print(f"Row count post:               {row_count_post:,}")
print(f"Row count preserved:          {row_count_pre == row_count_post}")
print()
print("Threshold candidates:")
for n, vals in threshold_candidates.items():
    passing = "PASS" if vals["pooled_agreement"] >= THRESHOLD_GATE else "FAIL"
    chosen = " <-- N*" if n == N_STAR else ""
    print(f"  N={n}d: n_pairs={vals['n_pairs_eligible']:,}  agreement={vals['pooled_agreement']:.6f}  [{passing}]{chosen}")
print()
print(f"Scope argument: {scope_argument}")

# %% [markdown]
# ## Artifact Export

# %%
# Build 4x4 stratification dict
stratification_4x4 = {}
for _, row in strat_df.iterrows():
    lb = row["leaderboard"]
    bucket = row["time_gap_bucket"]
    if lb not in stratification_4x4:
        stratification_4x4[lb] = {}
    stratification_4x4[lb][bucket] = {
        "n_pairs": int(row["n_pairs"]),
        "agreement_rate": round(float(row["agreement_rate"]), 6),
    }

# Build per-leaderboard at chosen threshold dict
per_lb_at_chosen = {
    lb: round(rate, 6) for lb, rate in per_lb_at_cutoff.items()
}

artifact_json = {
    "step": "01_04_07",
    "view_amended": "player_history_all",
    "column_added": "time_since_prior_match_days",
    "column_type": "DOUBLE",
    "row_count_pre": int(row_count_pre),
    "row_count_post": int(row_count_post),
    "first_match_null_rate": round(null_rate, 6),
    "threshold_candidates": {
        str(n): {
            "n_pairs_eligible": vals["n_pairs_eligible"],
            "pooled_agreement": vals["pooled_agreement"],
        }
        for n, vals in threshold_candidates.items()
    },
    "chosen_threshold_days": N_STAR,
    "threshold_argument": (
        f"largest N in {{1,2,3,7}} where pooled agreement on random_map >= 0.90; "
        f"chosen N*={N_STAR} with pooled agreement {pooled_agreement_at_N_star:.6f}"
    ),
    "stratification_4x4": stratification_4x4,
    "per_leaderboard_at_chosen_threshold": per_lb_at_chosen,
    "chosen_scope": SCOPE,
    "scope_argument": scope_argument,
    "correlation_with_rating_reset_magnitude": round(rho, 6),
    "audit_date": "2026-04-21",
    "current_ddl": CURRENT_DDL,
    "amended_ddl": AMENDED_DDL,
}

json_path.write_text(json.dumps(artifact_json, indent=2))
print(f"JSON artifact written: {json_path}")

# %% [markdown]
# ## MD Artifact
#
# Full report written to artifacts directory. See Cell below.

# %%
# Build threshold table rows
threshold_table_rows = "\n".join(
    f"| {n} | {vals['n_pairs_eligible']:,} | {vals['pooled_agreement']:.6f} | "
    f"{'PASS' if vals['pooled_agreement'] >= THRESHOLD_GATE else 'FAIL'} | "
    f"{'**N\\* = ' + str(n) + '**' if n == N_STAR else ''} |"
    for n, vals in threshold_candidates.items()
)

# Build 4x4 table rows (pivot: leaderboard × time_gap_bucket)
leaderboards_order = [
    "random_map", "team_random_map", "co_random_map", "co_team_random_map"
]
buckets_order = ["<1d", "1-7d", "7-30d", ">30d"]

strat_pivot_rows = []
for lb in leaderboards_order:
    row_cells = [lb]
    for bucket in buckets_order:
        if lb in stratification_4x4 and bucket in stratification_4x4[lb]:
            d = stratification_4x4[lb][bucket]
            row_cells.append(f"{d['n_pairs']:,} / {d['agreement_rate']:.4f}")
        else:
            row_cells.append("N/A")
    strat_pivot_rows.append("| " + " | ".join(row_cells) + " |")
strat_4x4_table = "\n".join(strat_pivot_rows)

# Build per-lb at N* table
lb_at_N_star_rows = "\n".join(
    f"| {row['leaderboard']} | {row['n_pairs_at_cutoff']:,} | {row['agreement_at_cutoff']:.6f} | "
    f"{'PASS' if row['agreement_at_cutoff'] >= THRESHOLD_GATE else 'FAIL'} |"
    for _, row in lb_at_N_star_df.iterrows()
)

md_content = f"""# Step 01_04_07 — old_rating CONDITIONAL_PRE_GAME Phase 01 Annotation

**Dataset:** aoestats
**Date:** 2026-04-21
**Step:** 01_04_07

---

## §1 Scope and Motivation

Step 01_04_06 (WP-4) empirically falsified the unconditional PRE-GAME classification
of `old_rating` (FAIL on all 3 gates; primary `random_map` agreement = 0.9210,
max_disagreement = 1,118 rating units). Per `docs/PHASES.md §Phase 01 01_04`,
Phase 01 is where column classifications are decided. Fixing this at Phase 02 would
spill the responsibility — Phase 02 would have to re-discover and build workarounds.

This step applies a Phase 01-level annotation: add derived column
`time_since_prior_match_days` to `player_history_all` VIEW, select an
empirically-grounded threshold N* ∈ {{1, 2, 3, 7}} days, determine SCOPE
(GLOBAL or `random_map`-only) from the 4×4 leaderboard × time-gap stratification,
and demote `old_rating` to CONDITIONAL_PRE_GAME in INVARIANTS.md §3.

**Post-Mode-A framing:** Mode A identified that the original 7-day pre-specified
cutoff was internally inconsistent (included the 1-7d bucket at 0.859, below the
0.90 stratum gate). The revised approach selects N* data-driven from
{{{', '.join(str(n) for n in [1, 2, 3, 7])}}} days. Mode A also identified that
01_04_06's per-time-gap stratification was random_map-only and could not justify
a global cutoff without the 4×4 leaderboard test.

---

## §2 DDL Verbatim (I6)

### Before Amendment (14 columns)

```sql
{CURRENT_DDL}
```

### After Amendment (15 columns)

```sql
{AMENDED_DDL}
```

---

## §3 Column Definition: time_since_prior_match_days

| Field | Value |
|-------|-------|
| Type | DOUBLE |
| Nullable | true |
| Source | LAG window: `PARTITION BY CAST(profile_id AS BIGINT), leaderboard ORDER BY started_timestamp, game_id` |
| NULL semantics | First match per `(profile_id, leaderboard)` — LAG returns NULL → gap = NULL |
| CAST discipline | `CAST(profile_id AS BIGINT)` (DS-AOESTATS-IDENTITY-04; lossless per 01_04_01) |
| Tie-breaker | `game_id` (matches 01_04_06 ordering) |

**NULL-first-match rule:** `time_since_prior_match_days IS NULL` means this is
the player's first recorded match on this leaderboard. No prior-match cross-session
risk exists for the initial `old_rating` value. NULL is therefore treated as
PRE-GAME for the CONDITIONAL_PRE_GAME gate. See §6 for full rule statement.

---

## §4 Threshold Selection — BLOCKER-1 Resolution

**Method:** For each candidate N ∈ {{1, 2, 3, 7}} days, compute pooled agreement
rate (`AVG(old_rating = prev_new_rating)`) on `random_map` for pairs where
`time_since_prior_match_days < N`. Choose N* = largest N with pooled agreement >= 0.90
(matching the WP-4 stratum gate per I7 — no magic numbers).

| N (days) | n_pairs_eligible | pooled_agreement | Gate (>=0.90) | Chosen |
|----------|-----------------|------------------|---------------|--------|
{threshold_table_rows}

**Chosen N* = {N_STAR} days.** Argument: largest N in {{1, 2, 3, 7}} where pooled
agreement on `random_map` clears the WP-4 0.90 stratum gate (I7 — threshold argued
from data, not pre-specified).

---

## §5 Scope Selection — BLOCKER-2 Resolution

**Method:** 4×4 leaderboard × time-gap stratification. If all 4 leaderboards
clear 0.90 at `<N*` days, SCOPE = GLOBAL. Otherwise SCOPE = `random_map`-only.

### Full 4×4 table (n_pairs / agreement_rate per cell)

| Leaderboard | <1d | 1-7d | 7-30d | >30d |
|-------------|-----|------|-------|------|
{strat_4x4_table}

### Per-leaderboard agreement at <{N_STAR}d

| Leaderboard | n_pairs | agreement_at_cutoff | Gate (>=0.90) |
|-------------|---------|---------------------|---------------|
{lb_at_N_star_rows}

**Chosen SCOPE: {SCOPE}.**
Scope predicate: `{scope_predicate}`.
Argument: {scope_argument}

---

## §6 NULL-First-Match Handling — WARNING-3 Resolution

**Explicit rule:** `time_since_prior_match_days IS NULL` indicates this is the
player's first recorded match on this leaderboard (no prior match exists in the
dataset). The "cross-session rating reset" risk is ZERO for this `old_rating`
value because there is no prior match after which a reset could have occurred.
Therefore: `time_since_prior_match_days IS NULL` → treat as PRE-GAME.

**Phase 02 condition:** `old_rating` is PRE-GAME iff
`({scope_predicate}) AND (time_since_prior_match_days < {N_STAR} OR time_since_prior_match_days IS NULL)`.

**First-match NULL rate:** {null_rate:.6f} ({null_rate:.2%} of all `player_history_all` rows).

---

## §7 Verification

| Check | Value | Status |
|-------|-------|--------|
| Row count pre-amendment | {row_count_pre:,} | — |
| Row count post-amendment | {row_count_post:,} | {"PRESERVED" if row_count_pre == row_count_post else "CHANGED"} |
| Column count | 15 | VERIFIED |
| `time_since_prior_match_days` in DESCRIBE | present | VERIFIED |
| First-match rows: all NULL gaps | {null_first_count}/{len(first_match_rows)} | VERIFIED |
| Non-first rows: no negative gaps | 0 | VERIFIED |
| Pearson ρ (gap vs disagreement) | {rho:.6f} | reported |

---

## §8 Downstream Impact

The following files require updating as a result of this amendment:

1. `player_history_all.yaml` — schema_version field (descriptive-string per canonical_slot precedent);
   new column entry for `time_since_prior_match_days`.
2. `INVARIANTS.md §3` — `old_rating` reclassified from PRE-GAME (WP-4 FAIL) to
   CONDITIONAL_PRE_GAME with N*={N_STAR}, SCOPE={SCOPE}, explicit NULL rule.
3. `reports/specs/02_00_feature_input_contract.md` — v1 → v2 per §7 change protocol;
   §2.2 column count 14 → 15; §5.5 adds `time_since_prior_match_days` row.
4. `ROADMAP.md` — current-state `player_history_all` 14-col references updated to 15-col.
"""

md_path.write_text(md_content)
print(f"MD artifact written: {md_path}")
print("\nStep 01_04_07 complete.")
