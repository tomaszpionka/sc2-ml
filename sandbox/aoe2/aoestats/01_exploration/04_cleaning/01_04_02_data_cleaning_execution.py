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
# # Step 01_04_02 -- Data Cleaning Execution (Act on DS-AOESTATS-01..08)
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_04 -- Data Cleaning
# **Dataset:** aoestats
# **Step scope:** Applies the 8 cleaning decisions (DS-AOESTATS-01..08) surfaced by 01_04_01
# missingness audit. Modifies VIEW DDL for matches_1v1_clean and player_history_all
# (no raw table changes per Invariant I9). Reports CONSORT-style column-count flow +
# subgroup impact + post-cleaning invariant re-validation.
# **Invariants applied:**
#   - I3 (temporal discipline: PRE_GAME only in matches_1v1_clean)
#   - I5 (1-row-per-match in matches_1v1_clean; p0/p1 columns symmetric NULLIF applied)
#   - I6 (all SQL stored verbatim in artifact)
#   - I7 (all thresholds data-derived from 01_04_01 ledger at runtime)
#   - I9 (non-destructive: raw tables untouched; only VIEWs replaced)
#   - I10 (no filename derivation changes; satisfied upstream)
# **Predecessor:** 01_04_01 (Missingness Audit -- complete)
# **Date:** 2026-04-17
# **ROADMAP ref:** 01_04_02

# %% [markdown]
# ## Cell 1 -- Imports

# %%
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from rts_predict.common.notebook_utils import (
    get_notebook_db,
    get_reports_dir,
    setup_notebook_logging,
)

logger = setup_notebook_logging()

# %% [markdown]
# ## Cell 2 -- DuckDB Connection (writable -- replaces VIEWs)
#
# This notebook creates two replacement VIEWs. A writable connection is required.
# WARNING: Close all read-only notebook connections to this DB before running.

# %%
db = get_notebook_db("aoe2", "aoestats", read_only=False)
con = db.con
print("DuckDB connection opened (read-write).")

# %% [markdown]
# ## Cell 3 -- Load 01_04_01 ledger (empirical evidence base)
#
# All per-DS resolution rationale traces to specific rows in this ledger.
# Thresholds and sentinel counts are read from the ledger at runtime (Invariant I7 -- no magic numbers).

# %%
reports_dir = get_reports_dir("aoe2", "aoestats")
ledger_path = (
    reports_dir / "artifacts" / "01_exploration" / "04_cleaning"
    / "01_04_01_missingness_ledger.csv"
)
ledger = pd.read_csv(ledger_path)
print(f"Ledger loaded: {len(ledger)} rows x {len(ledger.columns)} cols")
print(f"Columns: {list(ledger.columns)}")

ds_cols = [
    "view", "column", "n_null", "n_sentinel", "pct_missing_total",
    "n_distinct", "mechanism", "recommendation",
]
print("\nAll ledger rows (DS-AOESTATS scope):")
print(ledger[[c for c in ds_cols if c in ledger.columns]].to_string(index=False))

# Extract empirical sentinel counts at runtime per I7
def ledger_val(view_name, col_name, field):
    rows = ledger.loc[
        (ledger["view"] == view_name) & (ledger["column"] == col_name), field
    ]
    if len(rows) == 0:
        raise KeyError(f"Ledger row not found: view={view_name!r}, column={col_name!r}")
    return rows.values[0]

# DS-AOESTATS-02 sentinel counts
expected_p0_unrated = int(ledger_val("matches_1v1_clean", "p0_old_rating", "n_sentinel"))
expected_p1_unrated = int(ledger_val("matches_1v1_clean", "p1_old_rating", "n_sentinel"))
# DS-AOESTATS-03 sentinel counts
expected_avg_elo_sentinel = int(ledger_val("matches_1v1_clean", "avg_elo", "n_sentinel"))
# DS-AOESTATS-02 player_history_all sentinel counts
expected_unrated = int(ledger_val("player_history_all", "old_rating", "n_sentinel"))

print(f"\nRuntime empirical sentinel counts (I7 verification):")
print(f"  p0_old_rating sentinel (=0) in matches_1v1_clean: {expected_p0_unrated}")
print(f"  p1_old_rating sentinel (=0) in matches_1v1_clean: {expected_p1_unrated}")
print(f"  avg_elo sentinel (=0) in matches_1v1_clean: {expected_avg_elo_sentinel}")
print(f"  old_rating sentinel (=0) in player_history_all: {expected_unrated}")

# %% [markdown]
# ## Cell 4 -- Per-DS resolution log (documentation)
#
# DS-AOESTATS-01..08 decisions locked by user. No SQL execution here.

# %%
p0_rate = ledger_val("matches_1v1_clean", "p0_old_rating", "pct_missing_total")
p1_rate = ledger_val("matches_1v1_clean", "p1_old_rating", "pct_missing_total")
avg_elo_rate = ledger_val("matches_1v1_clean", "avg_elo", "pct_missing_total")
old_rating_rate = ledger_val("player_history_all", "old_rating", "pct_missing_total")

ds_resolutions = [
    {
        "id": "DS-AOESTATS-01",
        "column": "team_0_elo, team_1_elo",
        "views": "matches_1v1_clean",
        "ledger_rate": "0.00% (n_sentinel=0; sentinel=-1 absent in this scope)",
        "recommendation": "RETAIN_AS_IS",
        "decision": "NO-OP (RETAIN_AS_IS). F1 override: sentinel=-1 absent in 1v1 ranked scope.",
        "ddl_effect": "None",
    },
    {
        "id": "DS-AOESTATS-02",
        "column": "p0_old_rating, p1_old_rating (matches_1v1_clean); old_rating (player_history_all)",
        "views": "both",
        "ledger_rate": (
            f"{p0_rate:.4f}% p0 / {p1_rate:.4f}% p1 (matches_1v1_clean); "
            f"{old_rating_rate:.4f}% (player_history_all)"
        ),
        "recommendation": "CONVERT_SENTINEL_TO_NULL (non-binding; carries_semantic_content=True)",
        "decision": (
            "NULLIF(old_rating, 0) + ADD is_unrated flag in both VIEWs. "
            "mirrors sc2egset DS-SC2-10 pattern."
        ),
        "ddl_effect": (
            "matches_1v1_clean: NULLIF(p0_old_rating,0), NULLIF(p1_old_rating,0), "
            "+p0_is_unrated BOOLEAN, +p1_is_unrated BOOLEAN. "
            "player_history_all: NULLIF(old_rating,0), +is_unrated BOOLEAN."
        ),
    },
    {
        "id": "DS-AOESTATS-03",
        "column": "avg_elo",
        "views": "matches_1v1_clean",
        "ledger_rate": f"{avg_elo_rate:.4f}% (n_sentinel={expected_avg_elo_sentinel})",
        "recommendation": "CONVERT_SENTINEL_TO_NULL (non-binding; carries_semantic_content=True)",
        "decision": "NULLIF(avg_elo, 0) AS avg_elo. No companion flag (p0/p1_is_unrated covers semantic).",
        "ddl_effect": "matches_1v1_clean: NULLIF(avg_elo,0) AS avg_elo.",
    },
    {
        "id": "DS-AOESTATS-04",
        "column": "raw_match_type",
        "views": "matches_1v1_clean",
        "ledger_rate": "0.0396% NULL (n_null=7,055); n_distinct=1 in non-NULL scope",
        "recommendation": "RETAIN_AS_IS (original ledger, rate < 5% MCAR boundary)",
        "decision": (
            "DROP_COLUMN override (NOTE-1 critique fix): n_distinct=1 in non-NULL scope "
            "overrides RETAIN_AS_IS. Column is informationally redundant with upstream "
            "leaderboard + player_count filters."
        ),
        "ddl_effect": "matches_1v1_clean: raw_match_type removed from SELECT.",
    },
    {
        "id": "DS-AOESTATS-05",
        "column": "team1_wins",
        "views": "matches_1v1_clean",
        "ledger_rate": "0.00% (n_null=0; BOOLEAN strict 0/1)",
        "recommendation": "RETAIN_AS_IS / mechanism=N/A",
        "decision": "NO-OP (RETAIN_AS_IS). F1 override: zero NULLs; decisive by upstream filter.",
        "ddl_effect": "None",
    },
    {
        "id": "DS-AOESTATS-06",
        "column": "winner",
        "views": "player_history_all",
        "ledger_rate": "0.00% (n_null=0)",
        "recommendation": "RETAIN_AS_IS / mechanism=N/A",
        "decision": "NO-OP (RETAIN_AS_IS). Zero NULLs confirmed.",
        "ddl_effect": "None",
    },
    {
        "id": "DS-AOESTATS-07",
        "column": "overviews_raw (table)",
        "views": "N/A (not used by any VIEW)",
        "ledger_rate": "N/A (out of analytical scope)",
        "recommendation": "N/A",
        "decision": "FORMALLY DECLARED OUT-OF-ANALYTICAL-SCOPE in cleaning registry. No DDL change.",
        "ddl_effect": "None (registry-only resolution).",
    },
    {
        "id": "DS-AOESTATS-08",
        "column": "leaderboard, num_players",
        "views": "matches_1v1_clean (constants); player_history_all (RETAINED -- NOT constants there)",
        "ledger_rate": "n_distinct=1 in matches_1v1_clean scope for both columns",
        "recommendation": "DROP_COLUMN",
        "decision": "DROP leaderboard + num_players from matches_1v1_clean only. RETAIN in player_history_all.",
        "ddl_effect": "matches_1v1_clean: leaderboard and num_players removed from SELECT.",
    },
]
print("DS-AOESTATS-01..08 resolutions:")
for r in ds_resolutions:
    print(f"  {r['id']} ({r['column']}): {r['decision']}")

# %% [markdown]
# ## Cell 5 -- Pre-cleaning column counts (CONSORT before)
#
# Capture the current column state before applying DDL. On a fresh DB (01_04_01 state),
# this returns 21 / 13. If this notebook has already been run, the VIEWs are at 20 / 14
# (idempotent). Either way we record the pre-DDL state and note it in the CONSORT flow.

# %%
pre_clean_cols = con.execute("DESCRIBE matches_1v1_clean").df()
pre_hist_cols = con.execute("DESCRIBE player_history_all").df()

print(f"Current matches_1v1_clean columns: {len(pre_clean_cols)}")
print(f"Current player_history_all columns: {len(pre_hist_cols)}")

# Reference counts from 01_04_01 (the authoritative starting state)
COLS_BEFORE_CLEAN = 21
COLS_BEFORE_HIST = 13
print(f"01_04_01 reference: matches_1v1_clean={COLS_BEFORE_CLEAN}, player_history_all={COLS_BEFORE_HIST}")
print("Pre-cleaning column count reference recorded.")

# %% [markdown]
# ## Cell 6 -- Pre-cleaning row counts (CONSORT before)
#
# Row counts are invariant across 01_04_02 (column-only step). Asserting here
# against the known canonical values from 01_04_01.

# %%
pre_clean_rows = con.execute(
    "SELECT COUNT(*) AS rows, COUNT(DISTINCT game_id) AS game_ids FROM matches_1v1_clean"
).fetchone()
pre_hist_rows = con.execute(
    "SELECT COUNT(*) AS rows FROM player_history_all"
).fetchone()

print(f"matches_1v1_clean: rows={pre_clean_rows[0]}, game_ids={pre_clean_rows[1]}")
print(f"player_history_all: rows={pre_hist_rows[0]}")

# Row counts must match canonical 01_04_01 values (unchanged by column-only step)
assert pre_clean_rows[0] == 17814947, f"Expected 17814947 rows, got {pre_clean_rows[0]}"
assert pre_clean_rows[1] == 17814947, f"Expected 17814947 game_ids, got {pre_clean_rows[1]}"
assert pre_hist_rows[0] == 107626399, f"Expected 107626399 rows, got {pre_hist_rows[0]}"
print("Row count assertions passed (canonical 01_04_01 values confirmed).")

# %% [markdown]
# ## Cell 7 -- Define matches_1v1_clean v2 DDL
#
# Changes from current 21-column DDL (01_04_01 state):
# - DROP 3: leaderboard (DS-AOESTATS-08), num_players (DS-AOESTATS-08), raw_match_type (DS-AOESTATS-04)
# - MODIFY 3: avg_elo NULLIF (DS-AOESTATS-03), p0_old_rating NULLIF (DS-AOESTATS-02),
#             p1_old_rating NULLIF (DS-AOESTATS-02)
# - ADD 2: p0_is_unrated BOOLEAN (DS-AOESTATS-02), p1_is_unrated BOOLEAN (DS-AOESTATS-02)
# Net: 21 - 3 + 2 = 20 columns.

# %%
CREATE_MATCHES_1V1_CLEAN_V2_SQL = """
CREATE OR REPLACE VIEW matches_1v1_clean AS
-- Purpose: Prediction-target VIEW. Ranked 1v1 decisive matches only.
-- Row multiplicity: 1 row per match (NOT 2-per-match like sc2egset matches_flat_clean).
-- Target column: team1_wins (BOOLEAN; 0/1 strict -- no Undecided/Tie analog in aoestats).
-- Column set: 20 PRE_GAME + IDENTITY + TARGET columns (post 01_04_02).
-- All cleaning decisions (DS-AOESTATS-01..08) documented in 01_04_02_post_cleaning_validation.json.
WITH ranked_1v1 AS (
    SELECT m.game_id
    FROM matches_raw m
    INNER JOIN (
        SELECT game_id
        FROM players_raw
        GROUP BY game_id
        HAVING COUNT(*) = 2 AND COUNT(DISTINCT team) = 2
    ) pc ON m.game_id = pc.game_id
    WHERE m.leaderboard = 'random_map'
),
p0 AS (SELECT * FROM players_raw WHERE team = 0),
p1 AS (SELECT * FROM players_raw WHERE team = 1)
SELECT
    -- IDENTITY
    m.game_id,
    m.started_timestamp,

    -- DS-AOESTATS-08: leaderboard DROPPED (constant n_distinct=1 in this scope)
    m.map,
    m.mirror,
    -- DS-AOESTATS-08: num_players DROPPED (constant n_distinct=1 in this scope)
    m.patch,
    -- DS-AOESTATS-04: raw_match_type DROPPED (n_distinct=1 in non-NULL filtered scope; redundant with upstream filter)
    m.replay_enhanced,

    -- ELO (DS-AOESTATS-03: avg_elo NULLIF applied)
    NULLIF(m.avg_elo, 0) AS avg_elo,
    -- DS-AOESTATS-01: team_0_elo / team_1_elo RETAIN_AS_IS (sentinel=-1 absent in this scope per F1 override)
    m.team_0_elo,
    m.team_1_elo,

    -- Player 0 (DS-AOESTATS-02: NULLIF + is_unrated indicator)
    CAST(p0.profile_id AS BIGINT) AS p0_profile_id,
    p0.civ AS p0_civ,
    NULLIF(p0.old_rating, 0) AS p0_old_rating,
    (p0.old_rating = 0) AS p0_is_unrated,
    p0.winner AS p0_winner,

    -- Player 1 (DS-AOESTATS-02: symmetric NULLIF + is_unrated)
    CAST(p1.profile_id AS BIGINT) AS p1_profile_id,
    p1.civ AS p1_civ,
    NULLIF(p1.old_rating, 0) AS p1_old_rating,
    (p1.old_rating = 0) AS p1_is_unrated,
    p1.winner AS p1_winner,

    -- TARGET (DS-AOESTATS-05: RETAIN_AS_IS, F1 override)
    -- WARNING (I5): p0=team=0, p1=team=1. team=1 wins ~52.27% (slot asymmetry from 01_04_01).
    -- Phase 02 feature engineering MUST randomise focal/opponent assignment before training.
    p1.winner AS team1_wins
FROM ranked_1v1 r
INNER JOIN matches_raw m ON m.game_id = r.game_id
INNER JOIN p0 ON p0.game_id = r.game_id
INNER JOIN p1 ON p1.game_id = r.game_id
WHERE p0.winner != p1.winner;
"""

print("matches_1v1_clean v2 DDL defined.")
print("Expected output: 20 columns, 17,814,947 rows.")

# %% [markdown]
# ## Cell 8 -- Replace matches_1v1_clean VIEW

# %%
con.execute(CREATE_MATCHES_1V1_CLEAN_V2_SQL)
print("matches_1v1_clean VIEW replaced (v2).")

# %% [markdown]
# ## Cell 9 -- Define player_history_all v2 DDL
#
# Changes from current 13-column DDL (01_04_01 state):
# - MODIFY 1: old_rating -> NULLIF(old_rating, 0) per DS-AOESTATS-02
# - ADD 1: is_unrated BOOLEAN per DS-AOESTATS-02
# Net: 13 + 1 = 14 columns.
# NOTE: leaderboard and player_count are RETAINED here (not constants in this wider scope).

# %%
CREATE_PLAYER_HISTORY_ALL_V2_SQL = """
CREATE OR REPLACE VIEW player_history_all AS
-- Purpose: Player feature history VIEW. ALL game types and ALL leaderboards.
-- Row multiplicity: 1 row per player per match (107,626,399 rows pre/post).
-- Column set: 14 columns (was 13; +1 is_unrated indicator from DS-AOESTATS-02).
-- Changes from 01_04_01: old_rating NULLIF; +is_unrated; leaderboard/player_count RETAINED
--   (only constant in matches_1v1_clean, not here).
WITH player_counts AS (
    SELECT game_id, COUNT(*) AS player_count
    FROM players_raw
    GROUP BY game_id
)
SELECT
    -- IDENTITY
    CAST(p.profile_id AS BIGINT) AS profile_id,
    p.game_id,
    m.started_timestamp,

    -- CONTEXT (NOT constant in player_history_all -- covers all leaderboards/team-sizes)
    m.leaderboard,
    m.map,
    m.patch,
    pc.player_count,
    m.mirror,
    m.replay_enhanced,
    p.civ,
    p.team,

    -- PRE_GAME rating (DS-AOESTATS-02: NULLIF + is_unrated indicator)
    NULLIF(p.old_rating, 0) AS old_rating,
    (p.old_rating = 0) AS is_unrated,

    -- TARGET (DS-AOESTATS-06: RETAIN_AS_IS, F1 override)
    p.winner
FROM players_raw p
INNER JOIN matches_raw m ON p.game_id = m.game_id
INNER JOIN player_counts pc ON p.game_id = pc.game_id
WHERE p.profile_id IS NOT NULL
  AND m.started_timestamp IS NOT NULL;
"""

print("player_history_all v2 DDL defined.")
print("Expected output: 14 columns, 107,626,399 rows.")

# %% [markdown]
# ## Cell 10 -- Replace player_history_all VIEW

# %%
con.execute(CREATE_PLAYER_HISTORY_ALL_V2_SQL)
print("player_history_all VIEW replaced (v2).")

# %% [markdown]
# ## Cell 11 -- Post-cleaning column counts (CONSORT after)

# %%
post_clean_cols = con.execute("DESCRIBE matches_1v1_clean").df()
post_hist_cols = con.execute("DESCRIBE player_history_all").df()

print(f"Post-cleaning matches_1v1_clean columns: {len(post_clean_cols)}")
print(f"matches_1v1_clean column names: {post_clean_cols['column_name'].tolist()}")
print()
print(f"Post-cleaning player_history_all columns: {len(post_hist_cols)}")
print(f"player_history_all column names: {post_hist_cols['column_name'].tolist()}")

assert len(post_clean_cols) == 20, (
    f"Expected 20 columns in matches_1v1_clean, got {len(post_clean_cols)}"
)
assert len(post_hist_cols) == 14, (
    f"Expected 14 columns in player_history_all, got {len(post_hist_cols)}"
)
print("\nPost-cleaning column count assertions PASSED (20 / 14).")

# %% [markdown]
# ## Cell 12 -- Forbidden-column assertions (Section 3.3a -- newly dropped in 01_04_02)

# %%
clean_col_names = set(post_clean_cols["column_name"])
hist_col_names = set(post_hist_cols["column_name"])

# 3.3a: Newly dropped in 01_04_02 -- assert absent from matches_1v1_clean
forbidden_clean_new = {
    "leaderboard",      # DS-AOESTATS-08
    "num_players",      # DS-AOESTATS-08
    "raw_match_type",   # DS-AOESTATS-04
}
violations_clean_new = forbidden_clean_new & clean_col_names
assert len(violations_clean_new) == 0, (
    f"Newly-dropped columns still present in matches_1v1_clean: {violations_clean_new}"
)
print(f"3.3a matches_1v1_clean: all 3 newly-dropped columns absent. PASSED.")

# 3.3b: Pre-existing I3 exclusions (POST-GAME + IN-GAME) -- still absent
forbidden_clean_prior = {
    # POST-GAME (I3 violations removed in prior PRs)
    "new_rating",
    "p0_new_rating",
    "p1_new_rating",
    "duration",
    "irl_duration",
    "match_rating_diff",
    "p0_match_rating_diff",
    "p1_match_rating_diff",
    # IN-GAME (I3 violations removed in prior PRs)
    "p0_opening",
    "p1_opening",
    "p0_feudal_age_uptime",
    "p1_feudal_age_uptime",
    "p0_castle_age_uptime",
    "p1_castle_age_uptime",
    "p0_imperial_age_uptime",
    "p1_imperial_age_uptime",
    # Constant/near-dead from 01_04_01
    "game_type",
    "game_speed",
    "starting_age",
}
violations_clean_prior = forbidden_clean_prior & clean_col_names
assert len(violations_clean_prior) == 0, (
    f"Prior-excluded columns reappeared in matches_1v1_clean: {violations_clean_prior}"
)
print(f"3.3b matches_1v1_clean: all prior-excluded columns still absent. PASSED.")

# 3.3c: player_history_all RETAINED columns -- assert PRESENT (not dropped)
required_hist_present = {"leaderboard", "player_count"}
missing_hist_present = required_hist_present - hist_col_names
assert len(missing_hist_present) == 0, (
    f"Expected columns missing from player_history_all: {missing_hist_present}"
)
print(f"3.3c player_history_all: leaderboard + player_count still present. PASSED.")

# %% [markdown]
# ## Cell 13 -- New-column assertions (Section 3.4)
#
# Asserts p0_is_unrated, p1_is_unrated, team1_wins are BOOLEAN in matches_1v1_clean;
# is_unrated is BOOLEAN in player_history_all. 4 assertions total.

# %%
BOOLEAN_TYPE_SQL = """
SELECT column_name, data_type
FROM information_schema.columns
WHERE (table_name = 'matches_1v1_clean' AND column_name IN ('p0_is_unrated', 'p1_is_unrated', 'team1_wins'))
   OR (table_name = 'player_history_all' AND column_name = 'is_unrated')
ORDER BY table_name, column_name
"""
r_bool = con.execute(BOOLEAN_TYPE_SQL).df()
print("BOOLEAN type assertion results:")
print(r_bool.to_string(index=False))

assert len(r_bool) == 4, f"Expected 4 BOOLEAN rows, got {len(r_bool)}"
for _, row in r_bool.iterrows():
    assert row["data_type"] == "BOOLEAN", (
        f"{row['column_name']} should be BOOLEAN, got {row['data_type']}"
    )
print("All 4 new/asserted BOOLEAN columns confirmed. PASSED.")

# Verify by column_name lookup from DESCRIBE output for p0_is_unrated, p1_is_unrated
assert "p0_is_unrated" in clean_col_names, "p0_is_unrated missing from matches_1v1_clean"
assert "p1_is_unrated" in clean_col_names, "p1_is_unrated missing from matches_1v1_clean"
assert "is_unrated" in hist_col_names, "is_unrated missing from player_history_all"
print("New-column presence assertions PASSED.")

# %% [markdown]
# ## Cell 14 -- Zero-NULL identity assertions (Section 3.1)

# %%
ZERO_NULL_CLEAN_SQL = """
SELECT
    COUNT(*) FILTER (WHERE game_id IS NULL) AS null_game_id,
    COUNT(*) FILTER (WHERE started_timestamp IS NULL) AS null_started_timestamp,
    COUNT(*) FILTER (WHERE p0_profile_id IS NULL) AS null_p0_profile_id,
    COUNT(*) FILTER (WHERE p1_profile_id IS NULL) AS null_p1_profile_id,
    COUNT(*) FILTER (WHERE p0_winner IS NULL) AS null_p0_winner,
    COUNT(*) FILTER (WHERE p1_winner IS NULL) AS null_p1_winner,
    COUNT(*) FILTER (WHERE team1_wins IS NULL) AS null_team1_wins
FROM matches_1v1_clean
"""
r_null_clean = con.execute(ZERO_NULL_CLEAN_SQL).fetchone()
print(
    f"matches_1v1_clean zero-NULL check: "
    f"game_id={r_null_clean[0]}, started_timestamp={r_null_clean[1]}, "
    f"p0_profile_id={r_null_clean[2]}, p1_profile_id={r_null_clean[3]}, "
    f"p0_winner={r_null_clean[4]}, p1_winner={r_null_clean[5]}, "
    f"team1_wins={r_null_clean[6]}"
)
for i, name in enumerate(["game_id", "started_timestamp", "p0_profile_id", "p1_profile_id",
                           "p0_winner", "p1_winner", "team1_wins"]):
    assert r_null_clean[i] == 0, f"{name} has NULLs in matches_1v1_clean: {r_null_clean[i]}"
print("matches_1v1_clean zero-NULL identity assertions PASSED.")

ZERO_NULL_HIST_SQL = """
SELECT
    COUNT(*) FILTER (WHERE profile_id IS NULL) AS null_profile_id,
    COUNT(*) FILTER (WHERE game_id IS NULL) AS null_game_id,
    COUNT(*) FILTER (WHERE started_timestamp IS NULL) AS null_started_timestamp,
    COUNT(*) FILTER (WHERE winner IS NULL) AS null_winner
FROM player_history_all
"""
r_null_hist = con.execute(ZERO_NULL_HIST_SQL).fetchone()
print(
    f"player_history_all zero-NULL check: "
    f"profile_id={r_null_hist[0]}, game_id={r_null_hist[1]}, "
    f"started_timestamp={r_null_hist[2]}, winner={r_null_hist[3]}"
)
for i, name in enumerate(["profile_id", "game_id", "started_timestamp", "winner"]):
    assert r_null_hist[i] == 0, f"{name} has NULLs in player_history_all: {r_null_hist[i]}"
print("player_history_all zero-NULL identity assertions PASSED.")

# %% [markdown]
# ## Cell 15 -- Target consistency assertion (Section 3.2, aoestats analog)
#
# Aoestats matches_1v1_clean is 1-row-per-match (NOT 2-per-replay like sc2egset).
# Assertions: (a) no duplicate game_id; (b) p0_winner XOR p1_winner consistency;
# (c) team1_wins = p1_winner internal consistency.

# %%
DUP_MATCH_SQL = """
SELECT COUNT(*) AS dup_match_count
FROM (
    SELECT game_id, COUNT(*) AS n
    FROM matches_1v1_clean
    GROUP BY game_id
    HAVING n > 1
) d
"""
r_dup = con.execute(DUP_MATCH_SQL).fetchone()
print(f"Duplicate game_id count (must be 0): {r_dup[0]}")
assert r_dup[0] == 0, f"Duplicate game_ids in matches_1v1_clean: {r_dup[0]}"
print("No-duplicate game_id assertion PASSED.")

TARGET_CONSISTENCY_SQL = """
SELECT
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE p0_winner = TRUE AND p1_winner = FALSE) AS p0_wins,
    COUNT(*) FILTER (WHERE p0_winner = FALSE AND p1_winner = TRUE) AS p1_wins,
    COUNT(*) FILTER (WHERE p0_winner = p1_winner) AS inconsistent,
    COUNT(*) FILTER (WHERE team1_wins != p1_winner) AS team1_wins_inconsistent
FROM matches_1v1_clean
"""
r_tgt = con.execute(TARGET_CONSISTENCY_SQL).fetchone()
total, p0_wins, p1_wins, inconsistent, team1_wins_inconsistent = r_tgt
print(
    f"Target consistency: total={total}, p0_wins={p0_wins}, p1_wins={p1_wins}, "
    f"inconsistent={inconsistent}, team1_wins_inconsistent={team1_wins_inconsistent}"
)
assert inconsistent == 0, f"p0_winner=p1_winner rows (must be 0): {inconsistent}"
assert team1_wins_inconsistent == 0, (
    f"team1_wins != p1_winner rows (must be 0): {team1_wins_inconsistent}"
)
assert p0_wins + p1_wins == total, (
    f"p0_wins ({p0_wins}) + p1_wins ({p1_wins}) != total ({total})"
)
print("Target consistency assertions PASSED (aoestats analog of I5).")

# %% [markdown]
# ## Cell 16 -- No-new-NULLs assertion (Section 3.5)
#
# For each KEPT column in either VIEW that had n_null=0 per 01_04_01 ledger,
# assert n_null still = 0. Documented exceptions (new NULLs expected from NULLIF):
# - matches_1v1_clean: avg_elo, p0_old_rating, p1_old_rating
# - player_history_all: old_rating

# %%
# NULLIF columns -- new NULLs expected; skip in no-new-NULLs check
nullif_cols_clean = {"avg_elo", "p0_old_rating", "p1_old_rating"}
nullif_cols_hist = {"old_rating"}
# New indicator columns (not in ledger; skip)
new_cols_clean = {"p0_is_unrated", "p1_is_unrated"}
new_cols_hist = {"is_unrated"}

kept_zero_null_cols_clean = []
for col in post_clean_cols["column_name"].tolist():
    if col in nullif_cols_clean or col in new_cols_clean:
        continue
    ledger_row = ledger[
        (ledger["view"] == "matches_1v1_clean") & (ledger["column"] == col)
    ]
    if len(ledger_row) > 0 and ledger_row["n_null"].values[0] == 0:
        kept_zero_null_cols_clean.append(col)

if kept_zero_null_cols_clean:
    null_checks_clean = " + ".join(
        [f"COUNT(*) FILTER (WHERE \"{c}\" IS NULL)" for c in kept_zero_null_cols_clean]
    )
    r_no_new_clean = con.execute(
        f"SELECT {null_checks_clean} AS total_nulls FROM matches_1v1_clean"
    ).fetchone()
    print(
        f"No-new-NULLs check on {len(kept_zero_null_cols_clean)} zero-null cols "
        f"in matches_1v1_clean: total_nulls={r_no_new_clean[0]}"
    )
    assert r_no_new_clean[0] == 0, (
        f"New NULLs introduced in matches_1v1_clean: {r_no_new_clean[0]}"
    )
print("No-new-NULLs assertion for matches_1v1_clean PASSED.")

kept_zero_null_cols_hist = []
for col in post_hist_cols["column_name"].tolist():
    if col in nullif_cols_hist or col in new_cols_hist:
        continue
    ledger_row = ledger[
        (ledger["view"] == "player_history_all") & (ledger["column"] == col)
    ]
    if len(ledger_row) > 0 and ledger_row["n_null"].values[0] == 0:
        kept_zero_null_cols_hist.append(col)

if kept_zero_null_cols_hist:
    null_checks_hist = " + ".join(
        [f"COUNT(*) FILTER (WHERE \"{c}\" IS NULL)" for c in kept_zero_null_cols_hist]
    )
    r_no_new_hist = con.execute(
        f"SELECT {null_checks_hist} AS total_nulls FROM player_history_all"
    ).fetchone()
    print(
        f"No-new-NULLs check on {len(kept_zero_null_cols_hist)} zero-null cols "
        f"in player_history_all: total_nulls={r_no_new_hist[0]}"
    )
    assert r_no_new_hist[0] == 0, (
        f"New NULLs introduced in player_history_all: {r_no_new_hist[0]}"
    )
print("No-new-NULLs assertion for player_history_all (excluding old_rating) PASSED.")

# %% [markdown]
# ## Cell 17 -- NULLIF effect + is_unrated consistency assertions (Section 3.6)
#
# Expected counts loaded from ledger at runtime per Invariant I7. No hardcoded literals.

# %%
NULLIF_CLEAN_SQL = """
SELECT
    COUNT(*) FILTER (WHERE p0_old_rating IS NULL) AS p0_or_null_after,
    COUNT(*) FILTER (WHERE p0_is_unrated = TRUE) AS p0_unrated_flag,
    COUNT(*) FILTER (WHERE p0_is_unrated = FALSE AND p0_old_rating IS NULL) AS p0_inconsistent,
    COUNT(*) FILTER (WHERE p1_old_rating IS NULL) AS p1_or_null_after,
    COUNT(*) FILTER (WHERE p1_is_unrated = TRUE) AS p1_unrated_flag,
    COUNT(*) FILTER (WHERE p1_is_unrated = FALSE AND p1_old_rating IS NULL) AS p1_inconsistent,
    COUNT(*) FILTER (WHERE avg_elo IS NULL) AS avg_elo_null_after
FROM matches_1v1_clean
"""
r_nullif_clean = con.execute(NULLIF_CLEAN_SQL).fetchone()
p0_or_null, p0_flag, p0_inc, p1_or_null, p1_flag, p1_inc, avg_elo_null = r_nullif_clean
print(
    f"matches_1v1_clean NULLIF effect:\n"
    f"  p0_old_rating IS NULL: {p0_or_null} (expected ~{expected_p0_unrated} from ledger)\n"
    f"  p0_is_unrated=TRUE:    {p0_flag} (expected ~{expected_p0_unrated})\n"
    f"  p0_inconsistent:       {p0_inc} (expected 0)\n"
    f"  p1_old_rating IS NULL: {p1_or_null} (expected ~{expected_p1_unrated} from ledger)\n"
    f"  p1_is_unrated=TRUE:    {p1_flag} (expected ~{expected_p1_unrated})\n"
    f"  p1_inconsistent:       {p1_inc} (expected 0)\n"
    f"  avg_elo IS NULL:       {avg_elo_null} (expected ~{expected_avg_elo_sentinel} from ledger)"
)

# NULLIF counts must match ledger-derived expected values within +-1 row (I7)
assert abs(p0_or_null - expected_p0_unrated) <= 1, (
    f"p0_old_rating NULL count {p0_or_null} diverges from ledger {expected_p0_unrated} by >1"
)
assert abs(p0_flag - expected_p0_unrated) <= 1, (
    f"p0_is_unrated flag count {p0_flag} diverges from ledger {expected_p0_unrated} by >1"
)
assert p0_inc == 0, f"p0 inconsistency: {p0_inc} rows where is_unrated=FALSE but old_rating IS NULL"
assert abs(p1_or_null - expected_p1_unrated) <= 1, (
    f"p1_old_rating NULL count {p1_or_null} diverges from ledger {expected_p1_unrated} by >1"
)
assert abs(p1_flag - expected_p1_unrated) <= 1, (
    f"p1_is_unrated flag count {p1_flag} diverges from ledger {expected_p1_unrated} by >1"
)
assert p1_inc == 0, f"p1 inconsistency: {p1_inc} rows where is_unrated=FALSE but old_rating IS NULL"
assert abs(avg_elo_null - expected_avg_elo_sentinel) <= 1, (
    f"avg_elo NULL count {avg_elo_null} diverges from ledger {expected_avg_elo_sentinel} by >1"
)
print("matches_1v1_clean NULLIF effect assertions PASSED.")

NULLIF_HIST_SQL = """
SELECT
    COUNT(*) FILTER (WHERE old_rating IS NULL) AS or_null_after,
    COUNT(*) FILTER (WHERE is_unrated = TRUE) AS unrated_flag,
    COUNT(*) FILTER (WHERE is_unrated = FALSE AND old_rating IS NULL) AS inconsistent
FROM player_history_all
"""
r_nullif_hist = con.execute(NULLIF_HIST_SQL).fetchone()
or_null, unrated_flag, inconsistent_hist = r_nullif_hist
print(
    f"player_history_all NULLIF effect:\n"
    f"  old_rating IS NULL: {or_null} (expected ~{expected_unrated} from ledger)\n"
    f"  is_unrated=TRUE:    {unrated_flag} (expected ~{expected_unrated})\n"
    f"  inconsistent:       {inconsistent_hist} (expected 0)"
)
assert abs(or_null - expected_unrated) <= 1, (
    f"old_rating NULL count {or_null} diverges from ledger {expected_unrated} by >1"
)
assert abs(unrated_flag - expected_unrated) <= 1, (
    f"is_unrated flag count {unrated_flag} diverges from ledger {expected_unrated} by >1"
)
assert inconsistent_hist == 0, (
    f"Inconsistency in player_history_all: {inconsistent_hist} rows where "
    f"is_unrated=FALSE but old_rating IS NULL"
)
print("player_history_all NULLIF effect assertions PASSED.")

# %% [markdown]
# ## Cell 18 -- Post-cleaning row counts (CONSORT after)

# %%
post_clean_rows = con.execute(
    "SELECT COUNT(*) AS rows, COUNT(DISTINCT game_id) AS game_ids FROM matches_1v1_clean"
).fetchone()
post_hist_rows = con.execute(
    "SELECT COUNT(*) AS rows FROM player_history_all"
).fetchone()

print(f"Post-cleaning matches_1v1_clean: rows={post_clean_rows[0]}, game_ids={post_clean_rows[1]}")
print(f"Post-cleaning player_history_all: rows={post_hist_rows[0]}")

# Row counts must be unchanged (column-only cleaning step)
assert post_clean_rows[0] == pre_clean_rows[0], (
    f"Row count changed in matches_1v1_clean: {pre_clean_rows[0]} -> {post_clean_rows[0]}"
)
assert post_clean_rows[1] == pre_clean_rows[1], (
    f"game_id count changed in matches_1v1_clean: {pre_clean_rows[1]} -> {post_clean_rows[1]}"
)
assert post_hist_rows[0] == pre_hist_rows[0], (
    f"Row count changed in player_history_all: {pre_hist_rows[0]} -> {post_hist_rows[0]}"
)
print("CONSORT after: row counts unchanged (column-only cleaning). PASSED.")

# %% [markdown]
# ## Cell 19 -- Subgroup impact summary (Section 3.9, Jeanselme et al. 2024)
#
# Counts loaded from actual VIEW data at runtime per I7.

# %%
total_clean = post_clean_rows[0]
total_hist = post_hist_rows[0]

subgroup_impact = [
    {
        "affected_column": "leaderboard (dropped from matches_1v1_clean)",
        "source_decision": "DS-AOESTATS-08",
        "subgroup_most_affected": "Constant in scope -- none affected",
        "impact": f"Information neutral (n_distinct=1 in {total_clean:,} rows); no subgroup differentially affected",
    },
    {
        "affected_column": "num_players (dropped from matches_1v1_clean)",
        "source_decision": "DS-AOESTATS-08",
        "subgroup_most_affected": "Constant in scope -- none affected",
        "impact": f"Information neutral (n_distinct=1 in {total_clean:,} rows); no subgroup differentially affected",
    },
    {
        "affected_column": "raw_match_type (dropped from matches_1v1_clean)",
        "source_decision": "DS-AOESTATS-04",
        "subgroup_most_affected": "n_distinct=1 in non-NULL filtered scope",
        "impact": f"Information neutral; 7,055 NULL rows remain in VIEW (MCAR <5% boundary per Schafer & Graham 2002)",
    },
    {
        "affected_column": "p0_old_rating NULLIF + p0_is_unrated",
        "source_decision": "DS-AOESTATS-02",
        "subgroup_most_affected": f"Unrated-team0 players ({p0_or_null} of {total_clean:,} = {p0_or_null/total_clean*100:.4f}%)",
        "impact": "Sentinel->NULL converts 0-rating to missing-rating; p0_is_unrated flag preserves rated/unrated signal",
    },
    {
        "affected_column": "p1_old_rating NULLIF + p1_is_unrated",
        "source_decision": "DS-AOESTATS-02",
        "subgroup_most_affected": f"Unrated-team1 players ({p1_or_null} of {total_clean:,} = {p1_or_null/total_clean*100:.4f}%)",
        "impact": "Same as p0 -- symmetric NULLIF+flag applied",
    },
    {
        "affected_column": "old_rating NULLIF + is_unrated (player_history_all)",
        "source_decision": "DS-AOESTATS-02",
        "subgroup_most_affected": f"Unrated-player rows ({or_null} of {total_hist:,} = {or_null/total_hist*100:.4f}%)",
        "impact": "Sentinel->NULL; is_unrated flag preserves signal for Phase 02 win-rate denominator selection",
    },
    {
        "affected_column": "avg_elo NULLIF",
        "source_decision": "DS-AOESTATS-03",
        "subgroup_most_affected": f"Matches with >=1 unrated player ({avg_elo_null} of {total_clean:,} = {avg_elo_null/total_clean*100:.4f}%)",
        "impact": "Sentinel->NULL eliminates 0-skew in ELO averaging operations; p0/p1_is_unrated already capture the subgroup",
    },
]
print("Subgroup impact summary:")
for sg in subgroup_impact:
    print(f"  {sg['affected_column']} ({sg['source_decision']}): {sg['impact']}")

# %% [markdown]
# ## Cell 20 -- Cleaning registry (Section 3.10)

# %%
cleaning_registry_new = [
    {
        "rule_id": "drop_matches_1v1_clean_constants",
        "condition": "n_distinct=1 in matches_1v1_clean scope",
        "action": "DROP leaderboard and num_players from matches_1v1_clean",
        "justification": (
            "DS-AOESTATS-08: ledger constants-detection (n_distinct=1 across 17,814,947 rows); "
            "zero information content. Mirror of sc2egset DS-SC2-08 pattern."
        ),
        "impact": "-2 cols matches_1v1_clean",
    },
    {
        "rule_id": "drop_raw_match_type_redundant",
        "condition": "n_distinct=1 in non-NULL filtered scope of matches_1v1_clean",
        "action": "DROP raw_match_type from matches_1v1_clean",
        "justification": (
            "DS-AOESTATS-04: NOTE-1 critique fix -- constants-detection overrides RETAIN_AS_IS; "
            "redundant with upstream leaderboard='random_map' + COUNT(*)=2 filters; "
            "7,055 NULLs are MCAR but contribute zero signal beyond what upstream filter encodes."
        ),
        "impact": "-1 col matches_1v1_clean",
    },
    {
        "rule_id": "nullif_old_rating_indicator",
        "condition": "old_rating = 0 in either VIEW",
        "action": "NULLIF(old_rating, 0) + ADD is_unrated BOOLEAN flag in both VIEWs",
        "justification": (
            "DS-AOESTATS-02: low-rate sentinel with semantic content; "
            "NULLIF makes IS NULL semantics consistent for Phase 02 imputation; "
            "is_unrated flag preserves missingness-as-signal (sklearn MissingIndicator pattern)."
        ),
        "impact": (
            "matches_1v1_clean: 0 dropped / +2 (p0_is_unrated, p1_is_unrated) / 2 modified; "
            "player_history_all: 0 dropped / +1 (is_unrated) / 1 modified"
        ),
    },
    {
        "rule_id": "nullif_avg_elo",
        "condition": "avg_elo = 0 in matches_1v1_clean",
        "action": "NULLIF(avg_elo, 0) AS avg_elo",
        "justification": (
            "DS-AOESTATS-03: lowest sentinel rate (0.0007%); NULLIF makes column safe for "
            "Phase 02 averaging operations without 0-sentinel skewing means. "
            "p0_is_unrated/p1_is_unrated already convey the unrated subgroup membership."
        ),
        "impact": "1 modified col, 0 added",
    },
    {
        "rule_id": "declare_overviews_oos",
        "condition": "Always (documentation)",
        "action": "OVERVIEWS_RAW formally declared out-of-analytical-scope in this registry",
        "justification": (
            "DS-AOESTATS-07: singleton metadata table (1 row), not used by any VIEW. "
            "Registry declaration prevents inadvertent feature-source use in Phase 02+."
        ),
        "impact": "None (registry-only resolution)",
    },
]
print(f"Cleaning registry: {len(cleaning_registry_new)} new rules added in 01_04_02.")
for r in cleaning_registry_new:
    print(f"  {r['rule_id']}: {r['action']}")

# %% [markdown]
# ## Cell 21 -- Build and write artifact JSON (Section 3.10 / I6)

# %%
artifact_dir = reports_dir / "artifacts" / "01_exploration" / "04_cleaning"
artifact_dir.mkdir(parents=True, exist_ok=True)

validation_artifact = {
    "step": "01_04_02",
    "dataset": "aoestats",
    "generated_date": "2026-04-17",
    "cleaning_registry": cleaning_registry_new,
    "consort_flow_columns": {
        "matches_1v1_clean": {
            "cols_before": COLS_BEFORE_CLEAN,
            "cols_dropped": 3,
            "cols_added": 2,
            "cols_modified": 3,
            "cols_after": len(post_clean_cols),
        },
        "player_history_all": {
            "cols_before": COLS_BEFORE_HIST,
            "cols_dropped": 0,
            "cols_added": 1,
            "cols_modified": 1,
            "cols_after": len(post_hist_cols),
        },
    },
    "consort_flow_matches": {
        "matches_1v1_clean": {
            "game_ids_before_01_04_02": pre_clean_rows[1],
            "rows_before_01_04_02": pre_clean_rows[0],
            "game_ids_after_01_04_02": post_clean_rows[1],
            "rows_after_01_04_02": post_clean_rows[0],
            "note": "Column-only cleaning step: row counts unchanged.",
        },
        "player_history_all": {
            "rows_before_01_04_02": pre_hist_rows[0],
            "rows_after_01_04_02": post_hist_rows[0],
            "note": "Column-only cleaning step: row counts unchanged.",
        },
    },
    "subgroup_impact": subgroup_impact,
    "validation_assertions": {
        # Column counts
        "col_count_clean_20": bool(len(post_clean_cols) == 20),
        "col_count_hist_14": bool(len(post_hist_cols) == 14),
        # Zero-NULL identity (matches_1v1_clean)
        "zero_null_game_id_clean": bool(r_null_clean[0] == 0),
        "zero_null_started_timestamp_clean": bool(r_null_clean[1] == 0),
        "zero_null_p0_profile_id_clean": bool(r_null_clean[2] == 0),
        "zero_null_p1_profile_id_clean": bool(r_null_clean[3] == 0),
        "zero_null_p0_winner_clean": bool(r_null_clean[4] == 0),
        "zero_null_p1_winner_clean": bool(r_null_clean[5] == 0),
        "zero_null_team1_wins_clean": bool(r_null_clean[6] == 0),
        # Zero-NULL identity (player_history_all)
        "zero_null_profile_id_hist": bool(r_null_hist[0] == 0),
        "zero_null_game_id_hist": bool(r_null_hist[1] == 0),
        "zero_null_started_timestamp_hist": bool(r_null_hist[2] == 0),
        "zero_null_winner_hist": bool(r_null_hist[3] == 0),
        # Target consistency (aoestats analog of I5)
        "no_duplicate_game_id": bool(r_dup[0] == 0),
        "no_inconsistent_winner_rows": bool(inconsistent == 0),
        "team1_wins_equals_p1_winner": bool(team1_wins_inconsistent == 0),
        # Forbidden columns absent
        "forbidden_newly_dropped_absent_clean": bool(len(violations_clean_new) == 0),
        "forbidden_prior_i3_absent_clean": bool(len(violations_clean_prior) == 0),
        # New columns present + BOOLEAN type
        "new_col_p0_is_unrated_present": bool("p0_is_unrated" in clean_col_names),
        "new_col_p1_is_unrated_present": bool("p1_is_unrated" in clean_col_names),
        "new_col_is_unrated_hist_present": bool("is_unrated" in hist_col_names),
        "new_cols_boolean_type": bool(
            all(r_bool["data_type"] == "BOOLEAN")
        ),
        # NULLIF effect counts (within +-1 row of ledger)
        "p0_nullif_count_matches_ledger": bool(abs(p0_or_null - expected_p0_unrated) <= 1),
        "p0_is_unrated_consistency": bool(p0_inc == 0),
        "p1_nullif_count_matches_ledger": bool(abs(p1_or_null - expected_p1_unrated) <= 1),
        "p1_is_unrated_consistency": bool(p1_inc == 0),
        "avg_elo_nullif_count_matches_ledger": bool(abs(avg_elo_null - expected_avg_elo_sentinel) <= 1),
        "hist_nullif_count_matches_ledger": bool(abs(or_null - expected_unrated) <= 1),
        "hist_is_unrated_consistency": bool(inconsistent_hist == 0),
        # Row counts unchanged
        "row_count_clean_unchanged": bool(post_clean_rows[0] == pre_clean_rows[0]),
        "row_count_hist_unchanged": bool(post_hist_rows[0] == pre_hist_rows[0]),
        # leaderboard + player_count retained in player_history_all
        "hist_leaderboard_retained": bool("leaderboard" in hist_col_names),
        "hist_player_count_retained": bool("player_count" in hist_col_names),
    },
    "sql_queries": {
        "create_matches_1v1_clean_v2": CREATE_MATCHES_1V1_CLEAN_V2_SQL,
        "create_player_history_all_v2": CREATE_PLAYER_HISTORY_ALL_V2_SQL,
        "zero_null_clean": ZERO_NULL_CLEAN_SQL,
        "zero_null_hist": ZERO_NULL_HIST_SQL,
        "dup_match": DUP_MATCH_SQL,
        "target_consistency": TARGET_CONSISTENCY_SQL,
        "nullif_clean": NULLIF_CLEAN_SQL,
        "nullif_hist": NULLIF_HIST_SQL,
        "boolean_type_check": BOOLEAN_TYPE_SQL,
    },
    "decisions_resolved": ds_resolutions,
    "ledger_derived_expected_values": {
        "expected_p0_unrated": expected_p0_unrated,
        "expected_p1_unrated": expected_p1_unrated,
        "expected_avg_elo_sentinel": expected_avg_elo_sentinel,
        "expected_unrated": expected_unrated,
    },
}

# Verify all assertions pass before writing
all_pass = all(validation_artifact["validation_assertions"].values())
validation_artifact["all_assertions_pass"] = all_pass
print(f"All assertions pass: {all_pass}")
if not all_pass:
    failed = [k for k, v in validation_artifact["validation_assertions"].items() if not v]
    raise AssertionError(f"GATE FAILURE -- failed assertions: {failed}")

json_path = artifact_dir / "01_04_02_post_cleaning_validation.json"
with open(json_path, "w") as f:
    json.dump(validation_artifact, f, indent=2)
print(f"Artifact written: {json_path}")

# %% [markdown]
# ## Cell 22 -- Build and write markdown report

# %%
consort_col_table = (
    "| VIEW | Cols before | Cols dropped | Cols added | Cols modified | Cols after |\n"
    "|---|---|---|---|---|---|\n"
    f"| matches_1v1_clean | 21 | 3 | 2 | 3 (avg_elo, p0_old_rating, p1_old_rating NULLIF) | 20 |\n"
    f"| player_history_all | 13 | 0 | 1 | 1 (old_rating NULLIF) | 14 |"
)

consort_row_table = (
    "| Stage | matches_1v1_clean rows | matches_1v1_clean game_ids | player_history_all rows |\n"
    "|---|---|---|---|\n"
    f"| Before 01_04_02 (post 01_04_01) | 17,814,947 | 17,814,947 | 107,626,399 |\n"
    f"| After 01_04_02 column-only changes | 17,814,947 | 17,814,947 | 107,626,399 |"
)

registry_table_rows = "\n".join(
    f"| {r['rule_id']} | {r['condition']} | {r['action']} | {r['justification']} | {r['impact']} |"
    for r in cleaning_registry_new
)
registry_table = (
    "| Rule ID | Condition | Action | Justification | Impact |\n"
    "|---|---|---|---|---|\n"
    + registry_table_rows
)

subgroup_table_rows = "\n".join(
    f"| {sg['affected_column']} | {sg['source_decision']} | {sg['subgroup_most_affected']} | {sg['impact']} |"
    for sg in subgroup_impact
)
subgroup_table = (
    "| Affected column | Source decision | Subgroup most affected | Impact |\n"
    "|---|---|---|---|\n"
    + subgroup_table_rows
)

assertion_rows = "\n".join(
    f"| {k} | {'PASS' if v else 'FAIL'} |"
    for k, v in validation_artifact["validation_assertions"].items()
)
assertion_table = "| Assertion | Status |\n|---|---|\n" + assertion_rows

ds_table_rows = "\n".join(
    f"| {r['id']} | {r['column']} | {r['decision']} |"
    for r in ds_resolutions
)
ds_table = (
    "| DS ID | Column | Decision |\n"
    "|---|---|---|\n"
    + ds_table_rows
)

md_content = f"""# Step 01_04_02 -- Data Cleaning Execution: Post-Cleaning Validation

**Generated:** 2026-04-17
**Dataset:** aoestats
**Step:** 01_04_02 -- Act on DS-AOESTATS-01..08

## Summary

Step 01_04_02 applies all 8 cleaning decisions (DS-AOESTATS-01..08) surfaced by the
01_04_01 missingness audit. Both VIEWs are replaced via CREATE OR REPLACE DDL.
No raw tables are modified (Invariant I9). Row counts are unchanged (column-only
cleaning step). All validation assertions pass.

**Final column counts:** matches_1v1_clean 21 -> 20 (drop 3, add 2, modify 3);
player_history_all 13 -> 14 (drop 0, add 1, modify 1).

## Per-DS Resolutions

{ds_table}

## Cleaning Registry (new rules in 01_04_02)

{registry_table}

## CONSORT Column-Count Flow

{consort_col_table}

## CONSORT Match-Count Flow (column-only -- no row changes)

{consort_row_table}

## Subgroup Impact (Jeanselme et al. 2024)

{subgroup_table}

## Validation Results

{assertion_table}

## SQL Queries (Invariant I6)

All DDL and assertion SQL is stored verbatim in `01_04_02_post_cleaning_validation.json`
under the `sql_queries` key. Ledger-derived expected values are stored under
`ledger_derived_expected_values`.
"""

md_path = artifact_dir / "01_04_02_post_cleaning_validation.md"
with open(md_path, "w") as f:
    f.write(md_content)
print(f"Markdown report written: {md_path}")

# %% [markdown]
# ## Cell 23 -- Update player_history_all schema YAML
#
# KEEP existing prose-format notes vocabulary (Q3 locked decision).
# Do NOT migrate to sc2egset single-token vocabulary.
# Changes: bump step -> 01_04_02; add is_unrated column; modify old_rating description;
# update invariants block.

# %%
# schema_dir derived from reports_dir (avoids __file__ unavailability in notebooks)
# reports_dir is: src/rts_predict/games/aoe2/datasets/aoestats/reports
# schema_dir is:  src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views
schema_dir = reports_dir.parent / "data" / "db" / "schemas" / "views"
pha_yaml_path = schema_dir / "player_history_all.yaml"

# Prose-format notes per Q3 locked decision (keep existing aoestats vocabulary)
HIST_COL_NOTES = {
    "profile_id": (
        "IDENTITY. CAST from DOUBLE -- safe per T01 (max=24,853,897 < 2^53). Use as player FK.",
        "Player account identifier, cast from DOUBLE to BIGINT (R01).",
    ),
    "game_id": (
        "IDENTITY. Join key to matches_raw.",
        "Match identifier, shared with matches_raw.",
    ),
    "started_timestamp": (
        "CONTEXT. I3: Downstream feature queries MUST add\n"
        "WHERE ph.started_timestamp < target_match.started_timestamp.\n"
        "Rows with NULL started_timestamp excluded by VIEW predicate.",
        "Match start time (UTC-aware). Temporal anchor for I3 enforcement.",
    ),
    "leaderboard": (
        "CONTEXT. No leaderboard restriction -- all game types included for full-history feature computation.",
        "Ladder or game-type identifier (e.g., random_map, team_random_map, co_random_map).",
    ),
    "map": (
        "PRE_GAME (selected before match starts).",
        "Map name for the match.",
    ),
    "patch": (
        "CONTEXT. Temporal stratification variable.",
        "Game patch number at match time.",
    ),
    "player_count": (
        "CONTEXT. Computed via COUNT(*) GROUP BY game_id. Includes 1v1 (2), team (4, 6, 8), and edge cases.",
        "Total number of player rows for this game_id in players_raw.",
    ),
    "mirror": (
        "PRE_GAME descriptive. From matches_raw.",
        "Whether both players played the same civilization.",
    ),
    "replay_enhanced": (
        "CONTEXT. From matches_raw.",
        "Whether the match record was enhanced via replay parsing.",
    ),
    "civ": (
        "PRE_GAME. Key feature for faction proficiency computation in Phase 02.",
        "Civilization chosen by this player for this match.",
    ),
    "team": (
        "CONTEXT. Retained for player-row orientation. No wide-format pivot in this VIEW.",
        "Team identifier (0 or 1 for 1v1 matches; higher for team games).",
    ),
    "old_rating": (
        "PRE_GAME. I3-safe: recorded before match. Key feature for Phase 02. "
        "Sentinel=0 (unrated player) converted to NULL via NULLIF in 01_04_02 (DS-AOESTATS-02); "
        "see is_unrated companion flag for missingness-as-signal preservation.",
        "Player ELO rating before the match started. NULL if player was unrated (old_rating=0 sentinel).",
    ),
    "is_unrated": (
        "PRE_GAME. Indicator flag for unrated players (old_rating=0 sentinel). "
        "Derives from PRE_GAME old_rating; safe as feature without temporal filter. "
        "New in 01_04_02.",
        "TRUE if this player was unrated (old_rating=0 before NULLIF). Preserves missingness-as-signal.",
    ),
    "winner": (
        "TARGET. Used as prediction label in matches_1v1_clean (via p0_winner/p1_winner). "
        "Retained here for win-rate feature computation across all game types.",
        "Whether this player won the match.",
    ),
}

describe_hist_final = con.execute("DESCRIBE player_history_all").df()

columns_yaml_hist = []
for _, row in describe_hist_final.iterrows():
    col_name = row["column_name"]
    col_type = row["column_type"]
    nullable_str = row.get("null", "YES")
    nullable = nullable_str == "YES"
    if col_name in HIST_COL_NOTES:
        notes_val, desc_val = HIST_COL_NOTES[col_name]
    else:
        notes_val = f"CONTEXT. {col_name}."
        desc_val = f"{col_name}."
    columns_yaml_hist.append({
        "name": col_name,
        "type": col_type,
        "nullable": nullable,
        "description": desc_val,
        "notes": notes_val,
    })

invariants_block_hist = [
    {
        "id": "I3",
        "description": (
            "new_rating and match_rating_diff (POST-GAME) excluded. Temporal anchor "
            "(started_timestamp) exposed for downstream WHERE ph.started_timestamp < "
            "target_match.started_timestamp. old_rating is PRE_GAME-safe (rating before match)."
        ),
    },
    {
        "id": "I5",
        "description": (
            "Player-row-oriented (one row per player per match). No wide-format pivoting. "
            "profile_id is the identity key. No player-slot asymmetry risk in this VIEW."
        ),
    },
    {
        "id": "I6",
        "description": "VIEW DDL stored verbatim in 01_04_02_post_cleaning_validation.json sql_queries.",
    },
    {
        "id": "I9",
        "description": (
            "No features computed. VIEW is a JOIN projection of players_raw x matches_raw. "
            "01_04_02 modifies the column SET (old_rating NULLIF; +is_unrated indicator), "
            "never the underlying raw tables. No imputation, scaling, or encoding."
        ),
    },
    {
        "id": "I10",
        "description": (
            "No filename derivation changes. The aoestats raw tables already satisfy I10 "
            "from 01_02_02 ingestion."
        ),
    },
]

pha_yaml_content = {
    "table": "player_history_all",
    "dataset": "aoestats",
    "game": "aoe2",
    "object_type": "view",
    "step": "01_04_02",
    "row_count": int(post_hist_rows[0]),
    "describe_artifact": (
        "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/"
        "04_cleaning/01_04_02_post_cleaning_validation.json"
    ),
    "generated_date": "2026-04-17",
    "columns": columns_yaml_hist,
    "provenance": {
        "source_tables": ["players_raw", "matches_raw"],
        "filter": "profile_id IS NOT NULL; started_timestamp IS NOT NULL",
        "scope": (
            "All leaderboards and game types (no leaderboard restriction). "
            "Prediction scope != feature scope."
        ),
        "created_by": "sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py",
        "excluded_columns": [
            {"name": "new_rating", "reason": "POST-GAME; I3 violation (R06)"},
            {"name": "game_type", "reason": "Constant (cardinality=1); R04"},
            {"name": "game_speed", "reason": "Constant (cardinality=1); R04"},
            {"name": "starting_age", "reason": "Near-dead (99.99994% single value); R05"},
            {"name": "opening", "reason": "IN-GAME; 86-91% NULL; feature-inclusion deferred to Phase 02 (I9)"},
            {"name": "feudal_age_uptime", "reason": "IN-GAME; 86-91% NULL; feature-inclusion deferred to Phase 02 (I9)"},
            {"name": "castle_age_uptime", "reason": "IN-GAME; 86-91% NULL; feature-inclusion deferred to Phase 02 (I9)"},
            {"name": "imperial_age_uptime", "reason": "IN-GAME; 86-91% NULL; feature-inclusion deferred to Phase 02 (I9)"},
            {"name": "replay_summary_raw", "reason": "PARTIAL UTILITY; deferred to Phase 02"},
            {"name": "filename", "reason": "Provenance only; not needed in analytical VIEW"},
            {"name": "duration", "reason": "POST-GAME (match length known only after completion)"},
            {"name": "irl_duration", "reason": "POST-GAME (wall-clock duration known only after completion)"},
            {"name": "match_rating_diff", "reason": "POST-GAME (I3 violation); ELO delta from this match (new_rating - old_rating). Removed in 01_04_01 I3 fix."},
        ],
    },
    "invariants": invariants_block_hist,
}

with open(pha_yaml_path, "w") as f:
    yaml.dump(pha_yaml_content, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
print(f"player_history_all.yaml updated: {pha_yaml_path}")
print(f"  Columns: {len(columns_yaml_hist)}")

# %% [markdown]
# ## Cell 24 -- Create matches_1v1_clean schema YAML (NEW)
#
# Mirror player_history_all.yaml flat-list shape with prose-format notes vocabulary.
# 20 column entries with type, nullable, description, prose notes.
# Includes invariants block (I3/I5/I6/I9/I10).

# %%
mvc_yaml_path = schema_dir / "matches_1v1_clean.yaml"

CLEAN_COL_NOTES = {
    "game_id": (
        "IDENTITY. Primary key; 1-row-per-match invariant (asserted in 01_04_02).",
        "Match identifier, shared with matches_raw. Join key.",
    ),
    "started_timestamp": (
        "CONTEXT. I3: Downstream feature queries MUST filter player_history_all by "
        "ph.started_timestamp < this value.",
        "Match start time (UTC-aware). Temporal anchor for I3 enforcement.",
    ),
    "map": (
        "PRE_GAME. Selected before match starts. 77 distinct maps in 1v1 ranked scope.",
        "Map name for the match.",
    ),
    "mirror": (
        "PRE_GAME. From matches_raw. TRUE if both players chose the same civilization.",
        "Whether both players played the same civilization.",
    ),
    "patch": (
        "CONTEXT. Temporal stratification variable. 19 distinct patches in scope.",
        "Game patch number at match time.",
    ),
    "replay_enhanced": (
        "CONTEXT. From matches_raw.",
        "Whether the match record was enhanced via replay parsing.",
    ),
    "avg_elo": (
        "PRE_GAME. Average of team_0_elo and team_1_elo. "
        "Sentinel=0 converted to NULL via NULLIF in 01_04_02 (DS-AOESTATS-03). "
        "~118 rows affected.",
        "Average ELO of both players. NULL if either player was unrated (avg_elo=0 sentinel).",
    ),
    "team_0_elo": (
        "PRE_GAME. Team 0 aggregate ELO. Sentinel=-1 absent in 1v1 ranked scope (DS-AOESTATS-01; F1 override).",
        "Team 0 ELO rating before the match.",
    ),
    "team_1_elo": (
        "PRE_GAME. Team 1 aggregate ELO. Sentinel=-1 absent in 1v1 ranked scope (DS-AOESTATS-01; F1 override).",
        "Team 1 ELO rating before the match.",
    ),
    "p0_profile_id": (
        "IDENTITY. Player 0 account identifier (team=0). CAST from DOUBLE to BIGINT.",
        "Player 0 profile identifier.",
    ),
    "p0_civ": (
        "PRE_GAME. Player 0 civilization choice. 50 distinct civilizations in scope.",
        "Civilization chosen by player 0.",
    ),
    "p0_old_rating": (
        "PRE_GAME. Player 0 ELO before the match. "
        "Sentinel=0 converted to NULL via NULLIF in 01_04_02 (DS-AOESTATS-02). "
        "~4,730 rows affected. See p0_is_unrated for missingness-as-signal flag.",
        "Player 0 ELO rating before the match. NULL if player was unrated (sentinel=0).",
    ),
    "p0_is_unrated": (
        "PRE_GAME. Indicator flag for unrated players (old_rating=0 sentinel). "
        "Derives from PRE_GAME p0_old_rating; safe as feature without temporal filter. "
        "New in 01_04_02.",
        "TRUE if player 0 was unrated (p0_old_rating=0 before NULLIF). BOOLEAN.",
    ),
    "p0_winner": (
        "POST_GAME_HISTORICAL. Whether player 0 (team=0) won. Zero NULLs (F1 override). "
        "Used internally for target derivation; NOT a direct feature for game T.",
        "Whether player 0 won the match.",
    ),
    "p1_profile_id": (
        "IDENTITY. Player 1 account identifier (team=1). CAST from DOUBLE to BIGINT.",
        "Player 1 profile identifier.",
    ),
    "p1_civ": (
        "PRE_GAME. Player 1 civilization choice. 50 distinct civilizations in scope.",
        "Civilization chosen by player 1.",
    ),
    "p1_old_rating": (
        "PRE_GAME. Player 1 ELO before the match. "
        "Sentinel=0 converted to NULL via NULLIF in 01_04_02 (DS-AOESTATS-02). "
        "~188 rows affected. See p1_is_unrated for missingness-as-signal flag.",
        "Player 1 ELO rating before the match. NULL if player was unrated (sentinel=0).",
    ),
    "p1_is_unrated": (
        "PRE_GAME. Indicator flag for unrated players (old_rating=0 sentinel). "
        "Derives from PRE_GAME p1_old_rating; safe as feature without temporal filter. "
        "New in 01_04_02.",
        "TRUE if player 1 was unrated (p1_old_rating=0 before NULLIF). BOOLEAN.",
    ),
    "p1_winner": (
        "POST_GAME_HISTORICAL. Whether player 1 (team=1) won. Zero NULLs (F1 override). "
        "Used internally for target derivation; NOT a direct feature for game T.",
        "Whether player 1 won the match.",
    ),
    "team1_wins": (
        "TARGET. Primary prediction label. Derived as p1.winner AS team1_wins. "
        "BOOLEAN strict 0/1 -- no Undecided/Tie analog in aoestats (CRITICAL ASYMMETRY). "
        "WARNING (I5): team=1 wins ~52.27% of matches (slot asymmetry). "
        "Phase 02 MUST randomise focal/opponent assignment before training.",
        "TRUE if team 1 (player 1) won the match. Prediction target.",
    ),
}

describe_clean_final = con.execute("DESCRIBE matches_1v1_clean").df()

columns_yaml_clean = []
for _, row in describe_clean_final.iterrows():
    col_name = row["column_name"]
    col_type = row["column_type"]
    nullable_str = row.get("null", "YES")
    nullable = nullable_str == "YES"
    if col_name in CLEAN_COL_NOTES:
        notes_val, desc_val = CLEAN_COL_NOTES[col_name]
    else:
        notes_val = f"CONTEXT. {col_name}."
        desc_val = f"{col_name}."
    columns_yaml_clean.append({
        "name": col_name,
        "type": col_type,
        "nullable": nullable,
        "description": desc_val,
        "notes": notes_val,
    })

invariants_block_clean = [
    {
        "id": "I3",
        "description": (
            "All columns are PRE_GAME, IDENTITY, or TARGET. No IN-GAME or POST-GAME columns present "
            "(post-game columns removed in prior PRs; in-game columns never included). "
            "p0_winner / p1_winner are POST_GAME_HISTORICAL but used only for target derivation "
            "(team1_wins = p1.winner) within this VIEW; they are not direct feature inputs for game T. "
            "Temporal anchor: started_timestamp exposed for downstream I3-compliant feature queries "
            "against player_history_all."
        ),
    },
    {
        "id": "I5",
        "description": (
            "1-row-per-match invariant (asserted in 01_04_02). NOT 2-rows-per-replay like sc2egset. "
            "p0/p1 columns are symmetric (NULLIF + is_unrated applied identically to both slots). "
            "Phase 02 MUST randomise focal/opponent assignment before training to avoid slot asymmetry "
            "(team=1 wins ~52.27% per 01_04_01 audit)."
        ),
    },
    {
        "id": "I6",
        "description": "VIEW DDL stored verbatim in 01_04_02_post_cleaning_validation.json sql_queries.",
    },
    {
        "id": "I9",
        "description": (
            "No features computed. VIEW is a JOIN projection of matches_raw x players_raw "
            "with column drops (DS-AOESTATS-04/08) and NULLIF transformations (DS-AOESTATS-02/03). "
            "No imputation, scaling, or encoding. Phase 02 owns those transforms."
        ),
    },
    {
        "id": "I10",
        "description": (
            "No filename derivation changes. The aoestats raw tables already satisfy I10 "
            "from 01_02_02 ingestion."
        ),
    },
]

mvc_yaml_content = {
    "table": "matches_1v1_clean",
    "dataset": "aoestats",
    "game": "aoe2",
    "object_type": "view",
    "step": "01_04_02",
    "row_count": int(post_clean_rows[0]),
    "describe_artifact": (
        "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/"
        "04_cleaning/01_04_02_post_cleaning_validation.json"
    ),
    "generated_date": "2026-04-17",
    "columns": columns_yaml_clean,
    "provenance": {
        "source_tables": ["matches_raw", "players_raw"],
        "filter": (
            "Ranked 1v1 decisive matches only: leaderboard='random_map'; "
            "COUNT(DISTINCT players_raw.team)=2; COUNT(players_raw rows per game_id)=2; "
            "p0.winner != p1.winner (decisive -- no ties)."
        ),
        "scope": "Ranked 1v1 decisive matches only. Prediction scope only (not full feature history).",
        "row_multiplicity": "1 row per match (NOT 2-per-match like sc2egset).",
        "created_by": "sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py",
        "excluded_columns": [
            {"name": "leaderboard", "reason": "Constant (n_distinct=1) in 1v1 ranked scope; DS-AOESTATS-08"},
            {"name": "num_players", "reason": "Constant (n_distinct=1) in 1v1 ranked scope; DS-AOESTATS-08"},
            {"name": "raw_match_type", "reason": "n_distinct=1 in non-NULL scope; redundant with upstream filter; DS-AOESTATS-04"},
            {"name": "new_rating", "reason": "POST-GAME; I3 violation"},
            {"name": "p0_new_rating", "reason": "POST-GAME; I3 violation"},
            {"name": "p1_new_rating", "reason": "POST-GAME; I3 violation"},
            {"name": "duration", "reason": "POST-GAME; I3 violation"},
            {"name": "irl_duration", "reason": "POST-GAME; I3 violation"},
            {"name": "match_rating_diff", "reason": "POST-GAME; I3 violation"},
            {"name": "p0_match_rating_diff", "reason": "POST-GAME; I3 violation"},
            {"name": "p1_match_rating_diff", "reason": "POST-GAME; I3 violation"},
            {"name": "p0_opening", "reason": "IN-GAME; I3 violation"},
            {"name": "p1_opening", "reason": "IN-GAME; I3 violation"},
            {"name": "p0_feudal_age_uptime", "reason": "IN-GAME; I3 violation"},
            {"name": "p1_feudal_age_uptime", "reason": "IN-GAME; I3 violation"},
            {"name": "p0_castle_age_uptime", "reason": "IN-GAME; I3 violation"},
            {"name": "p1_castle_age_uptime", "reason": "IN-GAME; I3 violation"},
            {"name": "p0_imperial_age_uptime", "reason": "IN-GAME; I3 violation"},
            {"name": "p1_imperial_age_uptime", "reason": "IN-GAME; I3 violation"},
            {"name": "game_type", "reason": "Constant (cardinality=1) in scope"},
            {"name": "game_speed", "reason": "Constant (cardinality=1) in scope"},
            {"name": "starting_age", "reason": "Near-dead (99.99994% single value) in scope"},
        ],
    },
    "invariants": invariants_block_clean,
}

with open(mvc_yaml_path, "w") as f:
    yaml.dump(mvc_yaml_content, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
print(f"matches_1v1_clean.yaml created: {mvc_yaml_path}")
print(f"  Columns: {len(columns_yaml_clean)}")

# %% [markdown]
# ## Cell 25 -- Close DuckDB connection + final summary

# %%
db.close()
print("DuckDB connection closed.")

print("\n=== STEP 01_04_02 FINAL SUMMARY ===")
print(f"Dataset: aoestats")
print(f"Generated date: 2026-04-17")
print()
print("CONSORT Column-Count Flow:")
print(f"  matches_1v1_clean:  21 -> 20 cols (drop 3, add 2, modify 3)")
print(f"  player_history_all: 13 -> 14 cols (drop 0, add 1, modify 1)")
print()
print("CONSORT Row-Count Flow (column-only -- no row changes):")
print(f"  matches_1v1_clean:  17,814,947 rows (unchanged)")
print(f"  player_history_all: 107,626,399 rows (unchanged)")
print()
print("NULLIF effect counts (ledger-derived, I7):")
print(f"  p0_old_rating -> NULL: {p0_or_null} (expected ~{expected_p0_unrated})")
print(f"  p1_old_rating -> NULL: {p1_or_null} (expected ~{expected_p1_unrated})")
print(f"  avg_elo -> NULL:       {avg_elo_null} (expected ~{expected_avg_elo_sentinel})")
print(f"  old_rating -> NULL:    {or_null} (expected ~{expected_unrated})")
print()
print("All assertions pass:", all_pass)
print()
print("Artifacts written:")
print(f"  {json_path}")
print(f"  {md_path}")
print(f"  {pha_yaml_path} (UPDATED)")
print(f"  {mvc_yaml_path} (NEW)")
print()
print("PENDING (parent completes after review):")
print("  - STEP_STATUS.yaml: add 01_04_02: complete")
print("  - PIPELINE_SECTION_STATUS.yaml: bump 01_04 in_progress -> complete")
print("  - ROADMAP.md: append 01_04_02 step block")
print("  - research_log.md: append 2026-04-17 [01_04_02] entry")
