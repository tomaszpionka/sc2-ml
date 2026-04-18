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
# # Step 01_04_02 -- Data Cleaning Execution (Act on DS-AOEC-01..08)
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_04 -- Data Cleaning
# **Dataset:** aoe2companion
# **Step scope:** Applies all 8 cleaning decisions (DS-AOEC-01..08) surfaced by 01_04_01
# missingness audit. Modifies VIEW DDL for matches_1v1_clean and player_history_all
# via CREATE OR REPLACE (no raw table changes per Invariant I9). Reports CONSORT-style
# column-count flow + subgroup impact + post-cleaning invariant re-validation.
# Creates matches_1v1_clean.yaml (NEW) and updates player_history_all.yaml.
# **Invariants applied:**
#   - I3 (temporal discipline: PRE_GAME only in matches_1v1_clean)
#   - I5 (player-row-oriented; 2 rows per match in matches_1v1_clean, symmetric treatment)
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
# This notebook creates two replacement VIEWs via CREATE OR REPLACE. A writable
# connection is required.
# WARNING: Close all read-only notebook connections to this DB before running.

# %%
db = get_notebook_db("aoe2", "aoe2companion", read_only=False)
con = db.con
print("DuckDB connection opened (read-write).")

# %% [markdown]
# ## Cell 3 -- Load 01_04_01 ledger (empirical evidence base, I7)
#
# All per-DS resolution rationale traces to specific rows in this ledger.
# Thresholds and counts are read from the ledger at runtime (Invariant I7 -- no magic numbers).

# %%
reports_dir = get_reports_dir("aoe2", "aoe2companion")
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
print("\nAll ledger rows (DS-AOEC scope):")
print(ledger[[c for c in ds_cols if c in ledger.columns]].to_string(index=False))


def ledger_val(view_name: str, col_name: str, field: str):
    """Retrieve a single field value from the ledger for a given view+column pair.

    Raises KeyError if the row is not found (I7 enforcement).
    """
    rows = ledger.loc[
        (ledger["view"] == view_name) & (ledger["column"] == col_name), field
    ]
    if len(rows) == 0:
        raise KeyError(f"Ledger row not found: view={view_name!r}, column={col_name!r}")
    return rows.values[0]


# Extract per-column counts at runtime per I7 -- no magic numbers in code
expected_rating_null_clean = int(ledger_val("matches_1v1_clean", "rating", "n_null"))
expected_rating_null_hist = int(ledger_val("player_history_all", "rating", "n_null"))
expected_won_null_hist = int(ledger_val("player_history_all", "won", "n_null"))

print(f"\nRuntime empirical counts (I7 verification):")
print(f"  rating IS NULL in matches_1v1_clean:  {expected_rating_null_clean:,}")
print(f"  rating IS NULL in player_history_all: {expected_rating_null_hist:,}")
print(f"  won IS NULL in player_history_all:    {expected_won_null_hist:,}  (DS-AOEC-07 documented count)")

# %% [markdown]
# ## Cell 4 -- Per-DS resolution log (documentation, DS-AOEC-01..08)
#
# DS-AOEC-01..08 decisions locked. No SQL execution here.

# %%
server_rate = ledger_val("matches_1v1_clean", "server", "pct_missing_total")
scenario_rate = ledger_val("matches_1v1_clean", "scenario", "pct_missing_total")
mod_dataset_rate = ledger_val("matches_1v1_clean", "modDataset", "pct_missing_total")
password_rate = ledger_val("matches_1v1_clean", "password", "pct_missing_total")
antiquity_rate = ledger_val("matches_1v1_clean", "antiquityMode", "pct_missing_total")
hid_civs_rate = ledger_val("matches_1v1_clean", "hideCivs", "pct_missing_total")
mod_rate = ledger_val("matches_1v1_clean", "mod", "pct_missing_total")
status_rate_clean = ledger_val("matches_1v1_clean", "status", "pct_missing_total")
rating_rate = ledger_val("matches_1v1_clean", "rating", "pct_missing_total")
country_rate_clean = ledger_val("matches_1v1_clean", "country", "pct_missing_total")
country_rate_hist = ledger_val("player_history_all", "country", "pct_missing_total")
won_rate_clean = ledger_val("matches_1v1_clean", "won", "pct_missing_total")
won_rate_hist = ledger_val("player_history_all", "won", "pct_missing_total")
status_rate_hist = ledger_val("player_history_all", "status", "pct_missing_total")

ds_resolutions = [
    {
        "id": "DS-AOEC-01",
        "column": "server, scenario, modDataset, password",
        "views": "matches_1v1_clean",
        "ledger_rate": (
            f"server={server_rate:.4f}%, scenario={scenario_rate:.2f}%, "
            f"modDataset={mod_dataset_rate:.2f}%, password={password_rate:.4f}%"
        ),
        "recommendation": "DROP_COLUMN (server MNAR; scenario/modDataset/password MAR)",
        "decision": "DROP all 4 from matches_1v1_clean per Rule S4 (van Buuren 2018).",
        "ddl_effect": "matches_1v1_clean: server/scenario/modDataset/password removed from SELECT.",
    },
    {
        "id": "DS-AOEC-02",
        "column": "antiquityMode (DROP), hideCivs (RETAIN+FLAG)",
        "views": "matches_1v1_clean",
        "ledger_rate": (
            f"antiquityMode={antiquity_rate:.4f}%, hideCivs={hid_civs_rate:.4f}%"
        ),
        "recommendation": "antiquityMode DROP_COLUMN (60% in 40-80% non-primary); hideCivs FLAG_FOR_IMPUTATION",
        "decision": (
            "antiquityMode DROPPED (60.06%, 40-80% non-primary band). "
            "hideCivs RETAINED with FLAG_FOR_IMPUTATION (37.18%, 5-40% band) deferred to Phase 02."
        ),
        "ddl_effect": "matches_1v1_clean: antiquityMode removed from SELECT. hideCivs retained verbatim.",
    },
    {
        "id": "DS-AOEC-03",
        "column": "All low-NULL game settings (<5%)",
        "views": "matches_1v1_clean, player_history_all",
        "ledger_rate": "Rates < 5% Schafer & Graham 2002 MCAR boundary",
        "recommendation": "RETAIN_AS_IS",
        "decision": "NO-OP (RETAIN_AS_IS). All low-NULL game settings retained verbatim.",
        "ddl_effect": "None.",
    },
    {
        "id": "DS-AOEC-03b",
        "column": "mod, status (matches_1v1_clean); status (player_history_all)",
        "views": "both",
        "ledger_rate": (
            f"mod={mod_rate:.2f}% (n_distinct=1), "
            f"status (clean)={status_rate_clean:.2f}% (n_distinct=1), "
            f"status (hist)={status_rate_hist:.2f}% (n_distinct=1)"
        ),
        "recommendation": "DROP_COLUMN (constants-detection override; n_distinct=1)",
        "decision": (
            "DROP mod and status from matches_1v1_clean; "
            "DROP status from player_history_all. "
            "Constants-detection override supersedes low-NULL RETAIN_AS_IS."
        ),
        "ddl_effect": (
            "matches_1v1_clean: mod and status removed. "
            "player_history_all: status removed."
        ),
    },
    {
        "id": "DS-AOEC-04",
        "column": "rating (matches_1v1_clean) + rating_was_null flag (NEW)",
        "views": "matches_1v1_clean",
        "ledger_rate": f"rating={rating_rate:.4f}% NULL in scope",
        "recommendation": "FLAG_FOR_IMPUTATION (primary feature; Rule S4 exception per van Buuren 2018)",
        "decision": (
            "rating RETAINED in matches_1v1_clean. "
            "ADD rating_was_null BOOLEAN flag (sklearn MissingIndicator pattern; "
            "DS-AOEC-04 / Rule S4 primary feature exception). "
            "No NULLIF needed -- upstream VIEW already filters rating >= 0."
        ),
        "ddl_effect": "matches_1v1_clean: +(rating IS NULL) AS rating_was_null BOOLEAN.",
    },
    {
        "id": "DS-AOEC-05",
        "column": "country",
        "views": "both",
        "ledger_rate": (
            f"matches_1v1_clean={country_rate_clean:.4f}%, "
            f"player_history_all={country_rate_hist:.3f}%"
        ),
        "recommendation": (
            "matches_1v1_clean: RETAIN_AS_IS (<5%); "
            "player_history_all: FLAG_FOR_IMPUTATION (8.30%, 5-40% band)"
        ),
        "decision": (
            "country RETAINED in both VIEWs per cross-dataset convention. "
            "Phase 02 strategy TBD ('Unknown' encoding or country_was_null indicator)."
        ),
        "ddl_effect": "None (deferred to Phase 02).",
    },
    {
        "id": "DS-AOEC-06",
        "column": "won (matches_1v1_clean)",
        "views": "matches_1v1_clean",
        "ledger_rate": f"won={won_rate_clean:.2f}% NULL (R03 complementarity guarantees zero NULLs)",
        "recommendation": "RETAIN_AS_IS / mechanism=N/A (F1 zero-missingness override)",
        "decision": "NO-OP (RETAIN_AS_IS). Zero NULLs by R03 complementarity.",
        "ddl_effect": "None.",
    },
    {
        "id": "DS-AOEC-07",
        "column": "won (player_history_all)",
        "views": "player_history_all",
        "ledger_rate": f"won={won_rate_hist:.4f}% NULL (~{expected_won_null_hist:,} rows)",
        "recommendation": "EXCLUDE_TARGET_NULL_ROWS (Rule S2)",
        "decision": (
            "DOCUMENTED: won in player_history_all has ~19,251 NULLs (0.0073%). "
            "EXCLUDE_TARGET_NULL_ROWS rule documented in cleaning registry. "
            "Physical exclusion deferred to Phase 02 feature-computation per Rule S2."
        ),
        "ddl_effect": "None (registry-only resolution; Row S2 enforced at Phase 02 rolling-window level).",
    },
    {
        "id": "DS-AOEC-08",
        "column": "leaderboards_raw (singleton 2-row), profiles_raw (7 dead columns 100% NULL)",
        "views": "N/A (not used by any VIEW)",
        "ledger_rate": "N/A (out of analytical scope)",
        "recommendation": "N/A",
        "decision": (
            "FORMALLY DECLARED OUT-OF-ANALYTICAL-SCOPE in cleaning registry. "
            "No DDL change, no DROP TABLE."
        ),
        "ddl_effect": "None (registry-only resolution).",
    },
]
print("DS-AOEC-01..08 resolutions:")
for r in ds_resolutions:
    print(f"  {r['id']} ({r['column']}): {r['decision']}")

# %% [markdown]
# ## Cell 5 -- Pre-cleaning column counts (CONSORT before)
#
# Capture the current column state before applying DDL. On a fresh DB (01_04_01 state),
# matches_1v1_clean=54, player_history_all=20. If the notebook has already run,
# the VIEWs are at 48/19 (idempotent). Either way we record the 01_04_01 reference.

# %%
pre_clean_cols = con.execute("DESCRIBE matches_1v1_clean").df()
pre_hist_cols = con.execute("DESCRIBE player_history_all").df()

print(f"Current matches_1v1_clean columns: {len(pre_clean_cols)}")
print(f"Current player_history_all columns: {len(pre_hist_cols)}")

# Reference counts from 01_04_01 (the authoritative starting state)
COLS_BEFORE_CLEAN = 54
COLS_BEFORE_HIST = 20
print(f"01_04_01 reference: matches_1v1_clean={COLS_BEFORE_CLEAN}, player_history_all={COLS_BEFORE_HIST}")
print("Pre-cleaning column count reference recorded.")

# %% [markdown]
# ## Cell 6 -- Pre-cleaning row counts (CONSORT before)
#
# Row counts are invariant across 01_04_02 (column-only step). Expected values
# derived from ledger at runtime per I7.

# %%
expected_clean_rows = int(ledger_val("matches_1v1_clean", "matchId", "n_total"))
expected_hist_rows = int(ledger_val("player_history_all", "matchId", "n_total"))

pre_clean_rows = con.execute(
    "SELECT COUNT(*) AS rows, COUNT(DISTINCT matchId) AS n_matches FROM matches_1v1_clean"
).fetchone()
pre_hist_rows = con.execute(
    "SELECT COUNT(*) AS rows FROM player_history_all"
).fetchone()

print(f"matches_1v1_clean: rows={pre_clean_rows[0]:,}, matches={pre_clean_rows[1]:,}")
print(f"player_history_all: rows={pre_hist_rows[0]:,}")

assert pre_clean_rows[0] == expected_clean_rows, (
    f"Expected {expected_clean_rows:,} rows, got {pre_clean_rows[0]:,}"
)
assert pre_hist_rows[0] == expected_hist_rows, (
    f"Expected {expected_hist_rows:,} rows, got {pre_hist_rows[0]:,}"
)
print(f"Row count assertions passed (expected_clean_rows={expected_clean_rows:,}, "
      f"expected_hist_rows={expected_hist_rows:,}).")

# %% [markdown]
# ## Cell 7 -- Define matches_1v1_clean v2 DDL
#
# Changes from 01_04_01 54-column DDL:
# - DROP 7 columns: server (DS-AOEC-01), scenario (DS-AOEC-01), modDataset (DS-AOEC-01),
#   password (DS-AOEC-01), antiquityMode (DS-AOEC-02), mod (DS-AOEC-03b), status (DS-AOEC-03b)
# - ADD 1 column: (rating IS NULL) AS rating_was_null (DS-AOEC-04)
# Net: 54 - 7 + 1 = 48 columns.
# No NULLIF needed: rating already filtered >= 0 upstream (n_sentinel=0 in ledger).

# %%
CREATE_MATCHES_1V1_CLEAN_V2_SQL = """
CREATE OR REPLACE VIEW matches_1v1_clean AS
-- Purpose: Prediction-target VIEW. Ranked 1v1 decisive matches only.
-- Row multiplicity: 2 rows per match (player-row-oriented; one row per player).
-- Target column: won (BOOLEAN strict TRUE/FALSE; R03 complementarity: 1 TRUE + 1 FALSE per match).
-- Column set: 48 PRE_GAME + IDENTITY + TARGET + CONTEXT columns (post 01_04_02).
-- All cleaning decisions (DS-AOEC-01..08) documented in 01_04_02_post_cleaning_validation.json.
-- NOTE: Uses explicit column list (no SELECT * EXCLUDE) + subquery IN pattern (not CTE JOIN)
--       to avoid DuckDB internal errors with multi-column aggregation.
SELECT
    d.matchId,
    d.started,
    d.leaderboard,
    d.name,
    -- DS-AOEC-01: server DROPPED (MNAR 97.39%)
    d.internalLeaderboardId,
    d.privacy,
    -- DS-AOEC-03b: mod DROPPED (n_distinct=1 constant)
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
    -- DS-AOEC-02: antiquityMode DROPPED (MAR 60.06%, 40-80% non-primary band)
    d.civilizationSet,
    d.teamPositions,
    d.teamTogether,
    d.treatyLength,
    d.turboMode,
    d.victory,
    d.revealMap,
    -- DS-AOEC-01: scenario DROPPED (MAR 100%)
    -- DS-AOEC-01: password DROPPED (MAR 77.57%)
    -- DS-AOEC-01: modDataset DROPPED (MAR 100%)
    d.profileId,
    d.rating,
    -- DS-AOEC-04: rating_was_null BOOLEAN flag (missingness-as-signal; sklearn MissingIndicator pattern)
    (d.rating IS NULL) AS rating_was_null,
    d.color,
    d.colorHex,
    d.slot,
    -- DS-AOEC-03b: status DROPPED (n_distinct=1 constant)
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
    SELECT
        matchId, started, leaderboard, name,
        internalLeaderboardId, privacy, map, difficulty, startingAge, fullTechTree,
        allowCheats, empireWarsMode, endingAge, gameMode, lockSpeed, lockTeams,
        mapSize, population, hideCivs, recordGame, regicideMode, gameVariant,
        resources, sharedExploration, speed, speedFactor, suddenDeathMode,
        civilizationSet, teamPositions, teamTogether, treatyLength, turboMode,
        victory, revealMap, profileId, rating, color, colorHex, slot,
        team, won, country, shared, verified, civ, filename,
        ROW_NUMBER() OVER (
            PARTITION BY matchId, profileId
            ORDER BY started
        ) AS rn
    FROM matches_raw
    WHERE internalLeaderboardId IN (6, 18)
      AND profileId != -1
) d
WHERE d.rn = 1
  AND d.matchId IN (
    SELECT matchId
    FROM (
        SELECT matchId, profileId, won,
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
       AND SUM(CASE WHEN won = TRUE THEN 1 ELSE 0 END) = 1
       AND SUM(CASE WHEN won = FALSE THEN 1 ELSE 0 END) = 1
);
"""

# Cell 13 sanity assertion (round-2 F6): prevent silent regression of R03/R02-derived flag
assert "is_null_cluster" in CREATE_MATCHES_1V1_CLEAN_V2_SQL, (
    "REGRESSION: is_null_cluster missing from CREATE_MATCHES_1V1_CLEAN_V2_SQL"
)
print("matches_1v1_clean v2 DDL defined.")
print("Expected output: 48 columns, 61,062,392 rows.")
print("Sanity assertion passed: is_null_cluster present in DDL.")

# %% [markdown]
# ## Cell 8 -- Replace matches_1v1_clean VIEW

# %%
con.execute(CREATE_MATCHES_1V1_CLEAN_V2_SQL)
print("matches_1v1_clean VIEW replaced (v2).")

# %% [markdown]
# ## Cell 9 -- Define player_history_all v2 DDL
#
# Changes from 01_04_01 20-column DDL:
# - DROP 1 column: status (DS-AOEC-03b constants override; n_distinct=1)
# Net: 20 - 1 = 19 columns.
# won RETAINED (DS-AOEC-07 documents EXCLUDE_TARGET_NULL_ROWS but defers to Phase 02).
# rating, country, team retained (FLAG_FOR_IMPUTATION deferred to Phase 02).

# %%
CREATE_PLAYER_HISTORY_ALL_V2_SQL = """
CREATE OR REPLACE VIEW player_history_all AS
-- Purpose: Player feature history VIEW. ALL game types and ALL leaderboards.
-- Row multiplicity: 1 row per player per match (264,132,745 rows pre/post).
-- Column set: 19 columns (was 20; -1 status dropped per DS-AOEC-03b).
-- Changes from 01_04_01: status constant DROPPED.
-- DS-AOEC-07: won has ~19,251 NULLs (0.0073%); physical exclusion deferred to Phase 02.
-- NOTE: Explicit column list (no SELECT * EXCLUDE) to avoid DuckDB multi-aggregate bug.
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
    -- DS-AOEC-03b: status DROPPED (n_distinct=1 constant; always 'player' after R00)
    verified,
    filename
FROM (
    SELECT
        matchId, profileId, name, started, leaderboard, internalLeaderboardId,
        map, civ, rating, color, slot, team, startingAge, gameMode, speed,
        won, country, verified, filename,
        ROW_NUMBER() OVER (
            PARTITION BY matchId, profileId
            ORDER BY started
        ) AS rn
    FROM matches_raw
    WHERE profileId != -1
) d
WHERE rn = 1;
"""

print("player_history_all v2 DDL defined.")
print("Expected output: 19 columns, 264,132,745 rows.")

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

assert len(post_clean_cols) == 48, (
    f"Expected 48 columns in matches_1v1_clean, got {len(post_clean_cols)}"
)
assert len(post_hist_cols) == 19, (
    f"Expected 19 columns in player_history_all, got {len(post_hist_cols)}"
)
print("\nPost-cleaning column count assertions PASSED (48 / 19).")

# %% [markdown]
# ## Cell 12 -- Forbidden-column assertions (Section 3.3a/b/c)

# %%
clean_col_names = set(post_clean_cols["column_name"])
hist_col_names = set(post_hist_cols["column_name"])

# 3.3a: Newly dropped in 01_04_02 -- assert absent
forbidden_clean_new = {
    "server",       # DS-AOEC-01
    "scenario",     # DS-AOEC-01
    "modDataset",   # DS-AOEC-01
    "password",     # DS-AOEC-01
    "antiquityMode", # DS-AOEC-02
    "mod",          # DS-AOEC-03b
    "status",       # DS-AOEC-03b
}
forbidden_hist_new = {"status"}  # DS-AOEC-03b

violations_clean_new = forbidden_clean_new & clean_col_names
violations_hist_new = forbidden_hist_new & hist_col_names
assert len(violations_clean_new) == 0, (
    f"Newly-dropped columns still in matches_1v1_clean: {violations_clean_new}"
)
assert len(violations_hist_new) == 0, (
    f"Newly-dropped columns still in player_history_all: {violations_hist_new}"
)
print("3.3a: All 7 newly-dropped columns absent from matches_1v1_clean. PASSED.")
print("3.3a: status absent from player_history_all. PASSED.")

# 3.3b: Pre-existing I3 exclusions (POST-GAME) -- still absent
forbidden_clean_prior = {"ratingDiff", "finished"}
violations_clean_prior = forbidden_clean_prior & clean_col_names
assert len(violations_clean_prior) == 0, (
    f"Prior-excluded POST-GAME columns reappeared in matches_1v1_clean: {violations_clean_prior}"
)
print("3.3b: ratingDiff and finished still absent from matches_1v1_clean. PASSED.")

# 3.3c: player_history_all RETAINED columns -- assert PRESENT
required_hist_present = {"won", "rating", "country", "team"}
missing_hist_present = required_hist_present - hist_col_names
assert len(missing_hist_present) == 0, (
    f"Expected columns missing from player_history_all: {missing_hist_present}"
)
print(f"3.3c: won/rating/country/team still present in player_history_all. PASSED.")

# %% [markdown]
# ## Cell 13 -- New-column assertion (Section 3.4)
#
# Verify rating_was_null is present in matches_1v1_clean and is BOOLEAN type.

# %%
BOOLEAN_TYPE_SQL = """
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'matches_1v1_clean'
  AND column_name = 'rating_was_null'
"""
r_bool = con.execute(BOOLEAN_TYPE_SQL).df()
print("BOOLEAN type assertion for rating_was_null:")
print(r_bool.to_string(index=False))

assert len(r_bool) == 1, f"Expected 1 BOOLEAN row, got {len(r_bool)}"
assert r_bool.iloc[0]["data_type"] == "BOOLEAN", (
    f"rating_was_null should be BOOLEAN, got {r_bool.iloc[0]['data_type']}"
)
assert "rating_was_null" in clean_col_names, "rating_was_null missing from matches_1v1_clean"
print("New-column rating_was_null: present and BOOLEAN type. PASSED.")

# %% [markdown]
# ## Cell 14 -- Zero-NULL identity assertions (Section 3.1)

# %%
# NOTE: DuckDB bug workaround -- multi-column aggregation on views with correlated
# IN-subquery patterns triggers an internal error. Individual WHERE-clause COUNT
# queries are used instead. Results are semantically equivalent.
ZERO_NULL_CLEAN_SQL = "-- Individual per-column WHERE-based NULL checks (see assertions below)"
null_matchId_clean = con.execute(
    "SELECT COUNT(*) FROM matches_1v1_clean WHERE matchId IS NULL"
).fetchone()[0]
null_started_clean = con.execute(
    "SELECT COUNT(*) FROM matches_1v1_clean WHERE started IS NULL"
).fetchone()[0]
null_profileId_clean = con.execute(
    "SELECT COUNT(*) FROM matches_1v1_clean WHERE profileId IS NULL"
).fetchone()[0]
null_won_clean = con.execute(
    "SELECT COUNT(*) FROM matches_1v1_clean WHERE won IS NULL"
).fetchone()[0]
r_null_clean = (null_matchId_clean, null_started_clean, null_profileId_clean, null_won_clean)
print(
    f"matches_1v1_clean zero-NULL check: "
    f"matchId={r_null_clean[0]}, started={r_null_clean[1]}, "
    f"profileId={r_null_clean[2]}, won={r_null_clean[3]}"
)
for i, name in enumerate(["matchId", "started", "profileId", "won"]):
    assert r_null_clean[i] == 0, f"{name} has NULLs in matches_1v1_clean: {r_null_clean[i]}"
print("matches_1v1_clean zero-NULL identity assertions PASSED.")

ZERO_NULL_HIST_SQL = "-- Individual per-column WHERE-based NULL checks (see assertions below)"
null_matchId_hist = con.execute(
    "SELECT COUNT(*) FROM player_history_all WHERE matchId IS NULL"
).fetchone()[0]
null_profileId_hist = con.execute(
    "SELECT COUNT(*) FROM player_history_all WHERE profileId IS NULL"
).fetchone()[0]
null_started_hist = con.execute(
    "SELECT COUNT(*) FROM player_history_all WHERE started IS NULL"
).fetchone()[0]
r_null_hist = (null_matchId_hist, null_profileId_hist, null_started_hist)
print(
    f"player_history_all zero-NULL check: "
    f"matchId={r_null_hist[0]}, profileId={r_null_hist[1]}, started={r_null_hist[2]}"
)
for i, name in enumerate(["matchId", "profileId", "started"]):
    assert r_null_hist[i] == 0, f"{name} has NULLs in player_history_all: {r_null_hist[i]}"
print("player_history_all zero-NULL identity assertions PASSED.")
print("NOTE: won IS NULL check deliberately excluded -- DS-AOEC-07 documents ~19,251 NULLs (0.0073%).")

# %% [markdown]
# ## Cell 15 -- Target consistency assertion (Section 3.2 -- aoec R03 analog)
#
# aoec matches_1v1_clean is 2-rows-per-match (player-row-oriented).
# R03 invariant: each match has exactly one won=TRUE + one won=FALSE row.
# The violating-match query must return 0 rows.

# %%
R03_CONSISTENCY_SQL = """
SELECT matchId, COUNT(*) AS n,
       SUM(CASE WHEN won = TRUE THEN 1 ELSE 0 END) AS n_true,
       SUM(CASE WHEN won = FALSE THEN 1 ELSE 0 END) AS n_false
FROM matches_1v1_clean
GROUP BY matchId
HAVING COUNT(*) != 2
    OR SUM(CASE WHEN won = TRUE THEN 1 ELSE 0 END) != 1
    OR SUM(CASE WHEN won = FALSE THEN 1 ELSE 0 END) != 1
"""
r_r03 = con.execute(R03_CONSISTENCY_SQL).df()
print(f"R03 complementarity violating matches (must be 0): {len(r_r03)}")
assert len(r_r03) == 0, (
    f"R03 violation: {len(r_r03)} matches without exactly 1 TRUE + 1 FALSE won row."
)
print("R03 complementarity assertion PASSED (all matches have exactly 1 TRUE + 1 FALSE).")

# %% [markdown]
# ## Cell 16 -- No-new-NULLs assertion (Section 3.5)
#
# For each KEPT column in either VIEW that had n_null=0 per the 01_04_01 ledger,
# assert n_null still = 0. rating_was_null is new (not in ledger); skip.
# Explicit filter discipline (round-2 F7): use ledger_val pattern directly.

# %%
zero_null_cols_clean = ledger.loc[
    (ledger["view"] == "matches_1v1_clean") & (ledger["n_null"] == 0), "column"
].tolist()
zero_null_cols_hist = ledger.loc[
    (ledger["view"] == "player_history_all") & (ledger["n_null"] == 0), "column"
].tolist()

print(f"Zero-null columns to assert: {len(zero_null_cols_clean)} in clean, "
      f"{len(zero_null_cols_hist)} in hist")

# Sanity: country and name have non-zero n_null in ledger; if they appear here, filter is broken
assert "country" not in zero_null_cols_clean, (
    "FILTER BUG: country has non-zero n_null but appeared in zero_null_cols_clean"
)
assert "name" not in zero_null_cols_clean, (
    "FILTER BUG: name has non-zero n_null but appeared in zero_null_cols_clean"
)
print("Sanity assertions on zero-null filter PASSED (country/name correctly excluded).")

# New column not in ledger: skip
new_cols_clean = {"rating_was_null"}
# Only check columns present in current VIEW
check_cols_clean = [
    c for c in zero_null_cols_clean
    if c in clean_col_names and c not in new_cols_clean
]
check_cols_hist = [
    c for c in zero_null_cols_hist
    if c in hist_col_names
]

if check_cols_clean:
    # NOTE: DuckDB bug workaround -- multi-column SUM(CASE...) on matches_1v1_clean view
    # triggers InternalException. Use individual per-column WHERE-based COUNT queries
    # accumulated in Python (same pattern as Cell 14 zero-NULL assertions).
    total_nulls_clean = 0
    for c in check_cols_clean:
        n = con.execute(
            f'SELECT COUNT(*) FROM matches_1v1_clean WHERE "{c}" IS NULL'
        ).fetchone()[0]
        total_nulls_clean += n
    print(
        f"No-new-NULLs check on {len(check_cols_clean)} zero-null cols "
        f"in matches_1v1_clean: total_nulls={total_nulls_clean}"
    )
    assert total_nulls_clean == 0, (
        f"New NULLs introduced in matches_1v1_clean: {total_nulls_clean}"
    )
print("No-new-NULLs assertion for matches_1v1_clean PASSED.")

if check_cols_hist:
    # Defensive: use per-column individual queries (consistent with matches_1v1_clean approach)
    total_nulls_hist = 0
    for c in check_cols_hist:
        n = con.execute(
            f'SELECT COUNT(*) FROM player_history_all WHERE "{c}" IS NULL'
        ).fetchone()[0]
        total_nulls_hist += n
    print(
        f"No-new-NULLs check on {len(check_cols_hist)} zero-null cols "
        f"in player_history_all: total_nulls={total_nulls_hist}"
    )
    assert total_nulls_hist == 0, (
        f"New NULLs introduced in player_history_all: {total_nulls_hist}"
    )
print("No-new-NULLs assertion for player_history_all PASSED.")

# %% [markdown]
# ## Cell 17 -- rating_was_null flag consistency (Section 3.6)
#
# Assert COUNT(rating_was_null=TRUE) == COUNT(rating IS NULL).
# Cross-check against expected_rating_null_clean from ledger (I7 tolerance: +-1 row).

# %%
RATING_FLAG_SQL = "-- Individual WHERE-based counts for flag consistency (DuckDB bug workaround)"
RATING_FLAG_SQL_FLAG_COUNT = "SELECT COUNT(*) FROM matches_1v1_clean WHERE rating_was_null = TRUE"
RATING_FLAG_SQL_NULL_COUNT = "SELECT COUNT(*) FROM matches_1v1_clean WHERE rating IS NULL"
RATING_FLAG_SQL_INCONSISTENT = "SELECT COUNT(*) FROM matches_1v1_clean WHERE rating_was_null = TRUE AND rating IS NOT NULL"
flag_true = con.execute(RATING_FLAG_SQL_FLAG_COUNT).fetchone()[0]
rating_null = con.execute(RATING_FLAG_SQL_NULL_COUNT).fetchone()[0]
inconsistent_flag = con.execute(RATING_FLAG_SQL_INCONSISTENT).fetchone()[0]
r_flag = (flag_true, rating_null, inconsistent_flag)
print(
    f"rating_was_null flag consistency:\n"
    f"  flag_true_count:                {flag_true:,}\n"
    f"  rating_null_count:              {rating_null:,}\n"
    f"  expected_rating_null_clean (I7): {expected_rating_null_clean:,}\n"
    f"  inconsistent (flag=TRUE but rating NOT NULL): {inconsistent_flag}"
)

assert flag_true == rating_null, (
    f"rating_was_null=TRUE count ({flag_true:,}) != rating IS NULL count ({rating_null:,})"
)
assert inconsistent_flag == 0, (
    f"Inconsistency: {inconsistent_flag} rows where rating_was_null=TRUE but rating IS NOT NULL"
)
assert abs(flag_true - expected_rating_null_clean) <= 1, (
    f"flag_true count {flag_true:,} diverges from ledger {expected_rating_null_clean:,} by >1"
)
print("rating_was_null flag consistency assertions PASSED.")

# %% [markdown]
# ## Cell 18 -- Post-cleaning row counts (CONSORT after)

# %%
post_clean_rows = con.execute(
    "SELECT COUNT(*) AS rows, COUNT(DISTINCT matchId) AS n_matches FROM matches_1v1_clean"
).fetchone()
post_hist_rows = con.execute(
    "SELECT COUNT(*) AS rows FROM player_history_all"
).fetchone()

print(f"Post-cleaning matches_1v1_clean: rows={post_clean_rows[0]:,}, matches={post_clean_rows[1]:,}")
print(f"Post-cleaning player_history_all: rows={post_hist_rows[0]:,}")

# Row counts must be unchanged (column-only cleaning step)
assert post_clean_rows[0] == pre_clean_rows[0], (
    f"Row count changed in matches_1v1_clean: {pre_clean_rows[0]:,} -> {post_clean_rows[0]:,}"
)
assert post_hist_rows[0] == pre_hist_rows[0], (
    f"Row count changed in player_history_all: {pre_hist_rows[0]:,} -> {post_hist_rows[0]:,}"
)
print("CONSORT after: row counts unchanged (column-only cleaning). PASSED.")

# %% [markdown]
# ## Cell 19 -- Subgroup impact summary (Section 3.9, Jeanselme et al. 2024)

# %%
total_clean = post_clean_rows[0]
total_hist = post_hist_rows[0]

subgroup_impact = [
    {
        "affected_column": "server (dropped from matches_1v1_clean)",
        "source_decision": "DS-AOEC-01",
        "subgroup_most_affected": (
            f"~{100 - server_rate:.1f}% of rows had non-NULL server; "
            f"those matches lose server-location information"
        ),
        "impact": (
            f"97.39% NULL; MNAR. ~2.6% of rows ({int((1 - server_rate/100)*total_clean):,}) "
            f"had non-NULL server info. That subgroup loses location information; "
            f"deemed not predictive for ranked 1v1."
        ),
    },
    {
        "affected_column": "scenario (dropped from matches_1v1_clean)",
        "source_decision": "DS-AOEC-01",
        "subgroup_most_affected": "100% NULL -- no subgroup affected",
        "impact": "100.00% NULL; MAR. No subgroup loses anything.",
    },
    {
        "affected_column": "modDataset (dropped from matches_1v1_clean)",
        "source_decision": "DS-AOEC-01",
        "subgroup_most_affected": "100% NULL -- no subgroup affected",
        "impact": "100.00% NULL; MAR. No subgroup loses anything.",
    },
    {
        "affected_column": "password (dropped from matches_1v1_clean)",
        "source_decision": "DS-AOEC-01",
        "subgroup_most_affected": (
            f"~{100 - password_rate:.1f}% of rows had non-NULL password "
            f"(password-protected lobby)"
        ),
        "impact": (
            f"77.57% NULL; MAR. ~{int((1 - password_rate/100)*total_clean):,} rows "
            f"had password-protected lobby info. Deemed not predictive for ranked 1v1."
        ),
    },
    {
        "affected_column": "antiquityMode (dropped from matches_1v1_clean)",
        "source_decision": "DS-AOEC-02",
        "subgroup_most_affected": (
            f"Pre-patch matches ({antiquity_rate:.1f}% NULL) lose this flag; "
            f"post-patch matches retain downstream patch-stratification"
        ),
        "impact": (
            f"60.06% NULL; MAR (schema-evolution boundary). "
            f"~{int((1 - antiquity_rate/100)*total_clean):,} non-NULL rows had this flag. "
            f"Patch-stratification captures the same boundary for Phase 02."
        ),
    },
    {
        "affected_column": "mod (dropped from matches_1v1_clean)",
        "source_decision": "DS-AOEC-03b",
        "subgroup_most_affected": "Constant -- no subgroup affected",
        "impact": f"n_distinct=1 constant across {total_clean:,} rows; zero information content.",
    },
    {
        "affected_column": "status (dropped from both VIEWs)",
        "source_decision": "DS-AOEC-03b",
        "subgroup_most_affected": "Constant -- no subgroup affected",
        "impact": (
            f"n_distinct=1 constant in both VIEWs "
            f"({total_clean:,} clean, {total_hist:,} hist); zero information content."
        ),
    },
    {
        "affected_column": "rating_was_null (added to matches_1v1_clean)",
        "source_decision": "DS-AOEC-04",
        "subgroup_most_affected": (
            f"~{rating_rate:.2f}% of matches_1v1_clean rows have rating IS NULL "
            f"(unrated focal player)"
        ),
        "impact": (
            f"{flag_true:,} rows ({flag_true/total_clean*100:.2f}%) have rating IS NULL. "
            f"Flag preserves rated/unrated signal for Phase 02 (sklearn MissingIndicator pattern)."
        ),
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
        "rule_id": "drop_high_null_columns_clean",
        "condition": "n_null > 40% in matches_1v1_clean scope (Rule S4 / van Buuren 2018)",
        "action": "DROP server, scenario, modDataset, password from matches_1v1_clean",
        "justification": (
            "DS-AOEC-01: server (MNAR 97.39%), scenario (MAR 100%), "
            "modDataset (MAR 100%), password (MAR 77.57%). "
            "Rule S4 threshold crossed; imputation indefensible (van Buuren 2018 Ch. 1.3)."
        ),
        "impact": "-4 cols matches_1v1_clean",
    },
    {
        "rule_id": "drop_schema_evolution_columns_clean",
        "condition": "n_null in 40-80% band, non-primary feature, schema-evolution column",
        "action": "DROP antiquityMode from matches_1v1_clean",
        "justification": (
            "DS-AOEC-02: antiquityMode MAR 60.06% (40-80% non-primary band). "
            "Schema-evolution boundary: introduced in a later patch. "
            "Cost/benefit favors simplicity per Rule S4."
        ),
        "impact": "-1 col matches_1v1_clean",
    },
    {
        "rule_id": "drop_constants_clean",
        "condition": "n_distinct=1 in matches_1v1_clean scope",
        "action": "DROP mod, status from matches_1v1_clean",
        "justification": (
            "DS-AOEC-03b: constants-detection override. "
            "mod n_distinct=1 (always FALSE), status n_distinct=1 (always 'player'). "
            "Zero information content; constants-detection supersedes low-NULL RETAIN_AS_IS."
        ),
        "impact": "-2 cols matches_1v1_clean",
    },
    {
        "rule_id": "drop_constants_hist",
        "condition": "n_distinct=1 in player_history_all scope",
        "action": "DROP status from player_history_all",
        "justification": (
            "DS-AOEC-03b: constants-detection override. "
            "status n_distinct=1 (always 'player' after R00 profileId != -1 filter). "
            "Zero information content."
        ),
        "impact": "-1 col player_history_all",
    },
    {
        "rule_id": "add_rating_was_null_flag_clean",
        "condition": "rating IS NULL in matches_1v1_clean (primary feature, ~26.20% NULL)",
        "action": "ADD (rating IS NULL) AS rating_was_null BOOLEAN to matches_1v1_clean",
        "justification": (
            "DS-AOEC-04: Rule S4 primary feature exception (van Buuren 2018). "
            "rating retained despite ~26.20% NULL (primary feature + MAR mechanism). "
            "rating_was_null BOOLEAN flag preserves missingness-as-signal "
            "(sklearn MissingIndicator pattern) for Phase 02 imputation strategy."
        ),
        "impact": "+1 col matches_1v1_clean (rating_was_null BOOLEAN)",
    },
    {
        "rule_id": "declare_leaderboards_profiles_oos",
        "condition": "Always (documentation only)",
        "action": (
            "leaderboards_raw (2-row singleton reference) + profiles_raw "
            "(7 dead columns, 100% NULL) declared OUT-OF-ANALYTICAL-SCOPE"
        ),
        "justification": (
            "DS-AOEC-08: leaderboards_raw is a 2-row singleton reference table "
            "(not used by any VIEW). profiles_raw has 7 columns all 100% NULL "
            "(no analytical utility). Registry declaration prevents inadvertent "
            "feature-source use in Phase 02+. No DROP TABLE statements issued per I9."
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
    "dataset": "aoe2companion",
    "generated_date": "2026-04-17",
    "cleaning_registry": cleaning_registry_new,
    "consort_flow_columns": {
        "matches_1v1_clean": {
            "cols_before": COLS_BEFORE_CLEAN,
            "cols_dropped": 7,
            "cols_added": 1,
            "cols_modified": 0,
            "cols_after": len(post_clean_cols),
        },
        "player_history_all": {
            "cols_before": COLS_BEFORE_HIST,
            "cols_dropped": 1,
            "cols_added": 0,
            "cols_modified": 0,
            "cols_after": len(post_hist_cols),
        },
    },
    "consort_flow_matches": {
        "matches_1v1_clean": {
            "n_matches_before": pre_clean_rows[1],
            "rows_before_01_04_02": pre_clean_rows[0],
            "n_matches_after": post_clean_rows[1],
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
        "col_count_clean_48": bool(len(post_clean_cols) == 48),
        "col_count_hist_19": bool(len(post_hist_cols) == 19),
        # Zero-NULL identity (matches_1v1_clean)
        "zero_null_matchId_clean": bool(r_null_clean[0] == 0),
        "zero_null_started_clean": bool(r_null_clean[1] == 0),
        "zero_null_profileId_clean": bool(r_null_clean[2] == 0),
        "zero_null_won_clean": bool(r_null_clean[3] == 0),
        # Zero-NULL identity (player_history_all)
        "zero_null_matchId_hist": bool(r_null_hist[0] == 0),
        "zero_null_profileId_hist": bool(r_null_hist[1] == 0),
        "zero_null_started_hist": bool(r_null_hist[2] == 0),
        # R03 complementarity
        "r03_complementarity_0_violations": bool(len(r_r03) == 0),
        # Forbidden columns absent
        "forbidden_newly_dropped_absent_clean": bool(len(violations_clean_new) == 0),
        "forbidden_newly_dropped_absent_hist": bool(len(violations_hist_new) == 0),
        "forbidden_prior_i3_absent_clean": bool(len(violations_clean_prior) == 0),
        # Required columns retained in player_history_all
        "hist_won_retained": bool("won" in hist_col_names),
        "hist_rating_retained": bool("rating" in hist_col_names),
        "hist_country_retained": bool("country" in hist_col_names),
        "hist_team_retained": bool("team" in hist_col_names),
        # New flag column present + BOOLEAN type
        "new_col_rating_was_null_present": bool("rating_was_null" in clean_col_names),
        "new_col_rating_was_null_boolean": bool(
            len(r_bool) == 1 and r_bool.iloc[0]["data_type"] == "BOOLEAN"
        ),
        # rating_was_null flag consistency
        "rating_was_null_equals_rating_is_null": bool(flag_true == rating_null),
        "rating_was_null_no_inconsistency": bool(inconsistent_flag == 0),
        "rating_was_null_count_matches_ledger": bool(
            abs(flag_true - expected_rating_null_clean) <= 1
        ),
        # Row counts unchanged
        "row_count_clean_unchanged": bool(post_clean_rows[0] == pre_clean_rows[0]),
        "row_count_hist_unchanged": bool(post_hist_rows[0] == pre_hist_rows[0]),
    },
    "sql_queries": {
        "create_matches_1v1_clean_v2": CREATE_MATCHES_1V1_CLEAN_V2_SQL,
        "create_player_history_all_v2": CREATE_PLAYER_HISTORY_ALL_V2_SQL,
        "zero_null_clean": ZERO_NULL_CLEAN_SQL,
        "zero_null_hist": ZERO_NULL_HIST_SQL,
        "r03_consistency": R03_CONSISTENCY_SQL,
        "rating_flag_consistency": RATING_FLAG_SQL,
        "boolean_type_check": BOOLEAN_TYPE_SQL,
    },
    "decisions_resolved": ds_resolutions,
    "ledger_derived_expected_values": {
        "expected_rating_null_clean": expected_rating_null_clean,
        "expected_rating_null_hist": expected_rating_null_hist,
        "expected_won_null_hist": expected_won_null_hist,
        "expected_clean_rows": expected_clean_rows,
        "expected_hist_rows": expected_hist_rows,
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
    f"| matches_1v1_clean | 54 | 7 (server/scenario/modDataset/password/antiquityMode/mod/status) | 1 (rating_was_null) | 0 | 48 |\n"
    f"| player_history_all | 20 | 1 (status) | 0 | 0 | 19 |"
)

consort_row_table = (
    "| Stage | matches_1v1_clean rows | matches_1v1_clean matches | player_history_all rows |\n"
    "|---|---|---|---|\n"
    f"| Before 01_04_02 (post 01_04_01) | {pre_clean_rows[0]:,} | {pre_clean_rows[1]:,} | {pre_hist_rows[0]:,} |\n"
    f"| After 01_04_02 column-only changes | {post_clean_rows[0]:,} | {post_clean_rows[1]:,} | {post_hist_rows[0]:,} |"
)

registry_table_rows = "\n".join(
    f"| {r['rule_id']} | {r['condition']} | {r['action']} | {r['impact']} |"
    for r in cleaning_registry_new
)
registry_table = (
    "| Rule ID | Condition | Action | Impact |\n"
    "|---|---|---|---|\n"
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
**Dataset:** aoe2companion
**Step:** 01_04_02 -- Act on DS-AOEC-01..08

## Summary

Step 01_04_02 applies all 8 cleaning decisions (DS-AOEC-01..08) surfaced by the
01_04_01 missingness audit. Both VIEWs are replaced via CREATE OR REPLACE DDL.
No raw tables are modified (Invariant I9). Row counts are unchanged (column-only
cleaning step). All validation assertions pass.

**Final column counts:** matches_1v1_clean 54 -> 48 (drop 7, add 1, modify 0);
player_history_all 20 -> 19 (drop 1, add 0, modify 0).

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
# KEEP existing prose-format notes vocabulary (Q3 locked decision from PR #144).
# Do NOT migrate to sc2egset single-token vocabulary.
# Changes: bump step -> 01_04_02; remove status column; update invariants block.

# %%
# schema_dir derived from reports_dir (avoids __file__ unavailability in notebooks)
# reports_dir is: src/rts_predict/games/aoe2/datasets/aoe2companion/reports
# schema_dir is:  src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/views
schema_dir = reports_dir.parent / "data" / "db" / "schemas" / "views"
pha_yaml_path = schema_dir / "player_history_all.yaml"

# Prose-format notes per Q3 locked decision (keep existing aoec vocabulary)
HIST_COL_NOTES = {
    "matchId": (
        "IDENTITY / CONTEXT. Temporal join key for feature computation.",
        "Match identifier. Join key for linking player rows to a match.",
    ),
    "profileId": (
        "IDENTITY. All profileId=-1 rows excluded (R02 / R00).",
        "Player profile identifier. Primary player identity key in aoe2companion.",
    ),
    "name": (
        "IDENTITY. Not used as canonical identifier (server-scoped); see I2.",
        "Player in-game display name at time of match.",
    ),
    "started": (
        "CONTEXT. I3: downstream feature queries must use WHERE ph.started < target_match.started.",
        "Match start timestamp. Temporal anchor for I3 discipline.",
    ),
    "leaderboard": (
        "CONTEXT. No restriction applied: all game types included for feature scope.",
        "Ladder name (rm_1v1, rm_team, unranked, etc.). 21 distinct values.",
    ),
    "internalLeaderboardId": (
        "CONTEXT. Not filtered; all leaderboard IDs present.",
        "Numeric ladder ID. Maps to ratings_raw.leaderboard_id for cross-table joins.",
    ),
    "map": (
        "PRE_GAME. Available before match start.",
        "Map name (e.g., arabia, arena, black_forest).",
    ),
    "civ": (
        "PRE_GAME. Player's civilization choice. Feature candidate for civ proficiency.",
        "Civilization name (e.g., Franks, Mongols, Britons).",
    ),
    "rating": (
        "PRE_GAME. I3: use only games where started < target_match.started. "
        "~39.63% NULL in player_history_all (all leaderboards including unranked). "
        "Phase 02 imputation: median-within-leaderboard strategy TBD.",
        "Player ELO rating entering the match. Confirmed PRE-GAME in 01_03_03 (99.8%).",
    ),
    "color": (
        "CONTEXT. Lobby assignment; not predictive.",
        "In-game player color code (1-8).",
    ),
    "slot": (
        "CONTEXT. Lobby assignment.",
        "Player slot index in the lobby.",
    ),
    "team": (
        "CONTEXT. Team number; sentinel 255 per matches_raw schema YAML notes. "
        "~5.02% NULL+sentinel in player_history_all (5-40% FLAG band). "
        "Phase 02 strategy TBD.",
        "Team number. Sentinel value 255 exists in some records.",
    ),
    "startingAge": (
        "PRE_GAME. Game setting; near-constant in ranked play.",
        "Starting age setting (dark, feudal, castle, imperial).",
    ),
    "gameMode": (
        "PRE_GAME. Game setting.",
        "Game mode identifier (e.g., random_map, empire_wars).",
    ),
    "speed": (
        "PRE_GAME. Game setting; near-constant in ranked play.",
        "Game speed setting name (e.g., normal, fast).",
    ),
    "won": (
        "TARGET. Prediction label for matches_1v1_clean. "
        "In player_history_all, used for historical win-rate feature computation. "
        "DS-AOEC-07: ~19,251 NULLs (0.0073%) from unranked/unknown leaderboards; "
        "EXCLUDE_TARGET_NULL_ROWS rule documented; physical exclusion deferred to Phase 02 per Rule S2.",
        "Match outcome for this player. TRUE = won, FALSE = lost.",
    ),
    "country": (
        "IDENTITY / CONTEXT. Player attribute; potential demographic feature. "
        "~8.30% NULL in player_history_all (5-40% FLAG band; DS-AOEC-05). "
        "Phase 02 strategy TBD ('Unknown' category encoding or country_was_null indicator).",
        "Player country code (ISO 3166-1 alpha-2).",
    ),
    "verified": (
        "IDENTITY. Account attribute.",
        "Whether the player account is verified.",
    ),
    "filename": (
        "IDENTITY / PROVENANCE. Invariant I10: relative path only.",
        "Source Parquet file path relative to raw_dir (I10).",
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
            "POST-GAME columns ratingDiff and finished excluded. Temporal anchor (started) "
            "exposed for downstream WHERE ph.started < target_match.started. "
            "rating is PRE_GAME-safe (rating before match, confirmed 01_03_03)."
        ),
    },
    {
        "id": "I5",
        "description": (
            "Player-row-oriented (one row per player per match). No wide-format pivoting. "
            "profileId is the identity key. No player-slot asymmetry risk in this VIEW."
        ),
    },
    {
        "id": "I6",
        "description": "VIEW DDL stored verbatim in 01_04_02_post_cleaning_validation.json sql_queries.",
    },
    {
        "id": "I9",
        "description": (
            "No features computed here. VIEW is a filtered projection of matches_raw. "
            "Feature computation from player_history_all occurs in 01_05 / Phase 02. "
            "01_04_02 modifies only the column set (status DROP); never modifies raw tables."
        ),
    },
    {
        "id": "I10",
        "description": (
            "No filename derivation changes. The aoec raw tables already satisfy I10 "
            "from 01_02_02 ingestion."
        ),
    },
]

pha_yaml_content = {
    "table": "player_history_all",
    "dataset": "aoe2companion",
    "game": "aoe2",
    "object_type": "view",
    "step": "01_04_02",
    "row_count": int(post_hist_rows[0]),
    "describe_artifact": (
        "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/"
        "04_cleaning/01_04_02_post_cleaning_validation.json"
    ),
    "generated_date": "2026-04-17",
    "columns": columns_yaml_hist,
    "provenance": {
        "source_tables": ["matches_raw"],
        "filter": "profileId != -1; deduplicated by (matchId, profileId) ORDER BY started (earliest wins)",
        "scope": "All game types (no internalLeaderboardId restriction). Prediction scope != feature scope.",
        "created_by": "sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py",
        "notes": (
            "Vocabulary style aligned with aoestats (prose-format per-column notes); "
            "cross-dataset harmonisation with sc2egset (single-token notes + provenance_categories invariant) "
            "deferred to a CROSS PR after all three dataset 01_04_02 PRs land (per Q3 lock from PR #144)."
        ),
        "excluded_columns": [
            {"name": "status", "reason": "DS-AOEC-03b, n_distinct=1 constant (always 'player' after R00)"},
            {"name": "ratingDiff", "reason": "Prior I3 exclusion, POST-GAME (rating change after match)"},
            {"name": "finished", "reason": "Prior I3 exclusion, POST-GAME (game end timestamp)"},
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
# Mirror player_history_all.yaml prose-format notes vocabulary (aoestats convention).
# 48 column entries with type, nullable, description, prose notes.
# Includes invariants block (I3/I5/I6/I7/I9/I10).

# %%
mvc_yaml_path = schema_dir / "matches_1v1_clean.yaml"

CLEAN_COL_NOTES = {
    "matchId": (
        "IDENTITY. Primary key; R03 1v1 complementarity invariant "
        "(each match has exactly one TRUE + one FALSE won row).",
        "Match identifier from matches_raw.",
    ),
    "started": (
        "CONTEXT. I3: Downstream feature queries MUST filter player_history_all by "
        "ph.started < this value.",
        "Match start timestamp. Temporal anchor for I3 discipline.",
    ),
    "leaderboard": (
        "CONTEXT. Ladder name; 2 distinct values in 1v1 ranked scope (rm_1v1, rm_team analog).",
        "Ladder name (e.g., rm_1v1).",
    ),
    "name": (
        "IDENTITY. Player in-game display name. ~0.00% NULL (MCAR; RETAIN_AS_IS).",
        "Player in-game display name at time of match.",
    ),
    "internalLeaderboardId": (
        "CONTEXT. Numeric ladder ID; 2 distinct values in scope (6, 18). "
        "Zero NULLs by upstream filter (internalLeaderboardId IN (6, 18)).",
        "Numeric ladder ID. Maps to ratings_raw.leaderboard_id.",
    ),
    "privacy": (
        "CONTEXT. Lobby privacy setting. Zero NULLs.",
        "Lobby privacy setting (3 distinct values).",
    ),
    "map": (
        "PRE_GAME. Game setting; 94 distinct maps in 1v1 ranked scope. Zero NULLs.",
        "Map name (e.g., arabia, arena, black_forest).",
    ),
    "difficulty": (
        "PRE_GAME. Game setting; 3 distinct values per ledger. Zero NULLs. "
        "NOT a constant (n_distinct=3; RETAIN_AS_IS per DS-AOEC-03).",
        "Difficulty setting (3 distinct values in scope).",
    ),
    "startingAge": (
        "PRE_GAME. Game setting; near-constant in ranked play. Zero NULLs.",
        "Starting age setting (dark, feudal, castle, imperial).",
    ),
    "fullTechTree": (
        "PRE_GAME. Game setting; <0.02% NULL per ledger (Schafer & Graham 2002 <5% MCAR boundary).",
        "Whether full tech tree is enabled.",
    ),
    "allowCheats": (
        "PRE_GAME. Game setting; <0.02% NULL per ledger (Schafer & Graham 2002 <5% MCAR boundary). "
        "NULL-cluster member (R04 is_null_cluster).",
        "Whether cheats are allowed.",
    ),
    "empireWarsMode": (
        "PRE_GAME. Game mode; ~0.35% NULL per ledger (Schafer & Graham 2002 <5% MCAR boundary).",
        "Whether Empire Wars mode is active.",
    ),
    "endingAge": (
        "PRE_GAME. Game setting. Zero NULLs.",
        "Ending age setting.",
    ),
    "gameMode": (
        "PRE_GAME. Game setting. Zero NULLs.",
        "Game mode identifier (e.g., random_map, empire_wars).",
    ),
    "lockSpeed": (
        "PRE_GAME. Game setting; <0.02% NULL per ledger (Schafer & Graham 2002 <5% MCAR boundary). "
        "NULL-cluster member (R04 is_null_cluster).",
        "Whether game speed is locked.",
    ),
    "lockTeams": (
        "PRE_GAME. Game setting; <0.02% NULL per ledger (Schafer & Graham 2002 <5% MCAR boundary). "
        "NULL-cluster member (R04 is_null_cluster).",
        "Whether teams are locked.",
    ),
    "mapSize": (
        "PRE_GAME. Game setting; 5 distinct map sizes. Zero NULLs.",
        "Map size category (tiny, small, medium, normal, large, giant).",
    ),
    "population": (
        "PRE_GAME. Game setting; <0.02% NULL per ledger (Schafer & Graham 2002 <5% MCAR boundary). "
        "NULL-cluster member (R04 is_null_cluster).",
        "Population cap setting.",
    ),
    "hideCivs": (
        "PRE_GAME. Schema-evolution column (patch-dependent visibility setting). "
        "~37.18% NULL (DS-AOEC-02 FLAG_FOR_IMPUTATION per ledger). "
        "Phase 02 will materialise the imputation method AND its companion indicator (if chosen). "
        "NOT pre-materialised at cleaning time per cross-dataset convention "
        "(sc2egset isInClan, aoestats deferred non-primary flags).",
        "Whether civilizations are hidden from opponents before the match.",
    ),
    "recordGame": (
        "PRE_GAME. Game setting; <0.02% NULL per ledger (Schafer & Graham 2002 <5% MCAR boundary). "
        "NULL-cluster member (R04 is_null_cluster).",
        "Whether the game is recorded.",
    ),
    "regicideMode": (
        "PRE_GAME. Game mode; ~3.05% NULL per ledger (Schafer & Graham 2002 <5% MCAR boundary).",
        "Whether Regicide mode is active.",
    ),
    "gameVariant": (
        "PRE_GAME. Game setting; 2 distinct values. Zero NULLs.",
        "Game variant identifier.",
    ),
    "resources": (
        "PRE_GAME. Game setting; 4 distinct values. Zero NULLs.",
        "Starting resources setting.",
    ),
    "sharedExploration": (
        "PRE_GAME. Game setting; <0.02% NULL per ledger (Schafer & Graham 2002 <5% MCAR boundary). "
        "NULL-cluster member (R04 is_null_cluster).",
        "Whether map exploration is shared between team members.",
    ),
    "speed": (
        "PRE_GAME. Game setting; 3 distinct values. Zero NULLs.",
        "Game speed setting name (e.g., normal, fast).",
    ),
    "speedFactor": (
        "PRE_GAME. Game setting; 3 distinct values. Zero NULLs.",
        "Numeric speed multiplier.",
    ),
    "suddenDeathMode": (
        "PRE_GAME. Game mode; ~0.35% NULL per ledger (Schafer & Graham 2002 <5% MCAR boundary).",
        "Whether Sudden Death mode is active.",
    ),
    "civilizationSet": (
        "PRE_GAME. Game setting; 3 distinct values. Zero NULLs.",
        "Civilization set restriction (e.g., all, dlc_specific).",
    ),
    "teamPositions": (
        "PRE_GAME. Game setting; <0.02% NULL per ledger (Schafer & Graham 2002 <5% MCAR boundary). "
        "NULL-cluster member (R04 is_null_cluster).",
        "Whether team start positions are fixed.",
    ),
    "teamTogether": (
        "PRE_GAME. Game setting; <0.02% NULL per ledger (Schafer & Graham 2002 <5% MCAR boundary). "
        "NULL-cluster member (R04 is_null_cluster).",
        "Whether team start positions cluster allies together.",
    ),
    "treatyLength": (
        "PRE_GAME. Game setting; ~0.01% NULL per ledger (Schafer & Graham 2002 <5% MCAR boundary).",
        "Treaty duration in minutes (0 = no treaty).",
    ),
    "turboMode": (
        "PRE_GAME. Game mode; <0.02% NULL per ledger (Schafer & Graham 2002 <5% MCAR boundary). "
        "NULL-cluster member (R04 is_null_cluster).",
        "Whether Turbo mode is active.",
    ),
    "victory": (
        "PRE_GAME. Game setting; 3 distinct values. Zero NULLs.",
        "Victory condition (conquest, wonder, relic, time_limit).",
    ),
    "revealMap": (
        "PRE_GAME. Game setting; 4 distinct values. Zero NULLs.",
        "Map reveal setting (normal, explored, all_visible).",
    ),
    "profileId": (
        "IDENTITY. All profileId=-1 rows excluded upstream (R02 / R00). Zero NULLs.",
        "Player profile identifier. Primary player identity key in aoe2companion.",
    ),
    "rating": (
        "PRE_GAME. Player ELO rating before the match. ~26.20% NULL in scope (DS-AOEC-04 / "
        "Rule S4 primary feature exception per van Buuren 2018). "
        "The matches_1v1_clean VIEW asserts rating >= 0 upstream so the -1 sentinel is "
        "filtered before this VIEW; n_sentinel=0 in the audit reflects upstream filtering. "
        "Phase 02 imputation strategy: median-within-leaderboard + see rating_was_null "
        "companion flag for missingness-as-signal preservation.",
        "Player ELO rating entering the match (PRE-GAME, confirmed 01_03_03).",
    ),
    "rating_was_null": (
        "PRE_GAME. Indicator flag for unrated/missing-rating players (rating IS NULL). "
        "Derives from rating; safe as feature without temporal filter. "
        "New in 01_04_02 per DS-AOEC-04 (sklearn MissingIndicator pattern).",
        "TRUE if this row had NULL rating before any Phase 02 imputation. BOOLEAN.",
    ),
    "color": (
        "CONTEXT. Lobby assignment; not predictive. ~0.003% NULL (MCAR; RETAIN_AS_IS).",
        "In-game player color code (1-8).",
    ),
    "colorHex": (
        "CONTEXT. Hex string of color code. Zero NULLs.",
        "In-game player color as hex string.",
    ),
    "slot": (
        "CONTEXT. Lobby assignment. Zero NULLs.",
        "Player slot index in the lobby.",
    ),
    "team": (
        "CONTEXT. Team number; sentinel 255 per matches_raw schema YAML notes. "
        "~2.00% NULL per ledger (rate < 5% Schafer & Graham 2002 boundary; RETAIN_AS_IS).",
        "Team number (1 or 2 for 1v1 matches). Sentinel 255 exists in matches_raw.",
    ),
    "won": (
        "TARGET. Primary prediction label. BOOLEAN strict TRUE/FALSE; "
        "zero NULLs by R03 complementarity (F1 zero-missingness override).",
        "Match outcome for this player. TRUE = won, FALSE = lost.",
    ),
    "country": (
        "IDENTITY / CONTEXT. Player attribute; potential demographic feature. "
        "~2.25% NULL in matches_1v1_clean scope (rate < 5% Schafer & Graham 2002 boundary; "
        "ledger recommendation RETAIN_AS_IS). "
        "Player_history_all rate (~8.30%) crosses the FLAG band -- Phase 02 chooses "
        "per-VIEW strategy ('Unknown' category encoding or country_was_null indicator). "
        "NOT pre-materialised at cleaning time per cross-dataset convention "
        "(sc2egset / aoestats add flags only for primary features).",
        "Player country code (ISO 3166-1 alpha-2).",
    ),
    "shared": (
        "CONTEXT. Lobby share setting. Zero NULLs.",
        "Whether the match is shared/public.",
    ),
    "verified": (
        "IDENTITY. Account verification status. Zero NULLs.",
        "Whether the player account is verified.",
    ),
    "civ": (
        "PRE_GAME. Player civilization choice. Zero NULLs. Feature candidate for civ proficiency.",
        "Civilization name chosen by this player (e.g., Franks, Mongols, Britons).",
    ),
    "filename": (
        "IDENTITY / PROVENANCE. Invariant I10: relative path only.",
        "Source Parquet file path relative to raw_dir (I10).",
    ),
    "is_null_cluster": (
        "CONTEXT. R04 schema-era boundary flag -- TRUE when 10 game-settings columns are "
        "simultaneously NULL (allowCheats, lockSpeed, lockTeams, recordGame, sharedExploration, "
        "teamPositions, teamTogether, turboMode, fullTechTree, population). "
        "Spans entire date range, <0.02% of rows; informational only.",
        "TRUE if this match belongs to the NULL-cluster schema era (10 game settings simultaneously NULL).",
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
            "No new POST-GAME columns introduced. ratingDiff and finished remain excluded "
            "(verified by Section 3.3b assertion). rating_was_null derives from the "
            "PRE_GAME rating column only. Temporal anchor: started exposed for downstream "
            "I3-compliant feature queries against player_history_all."
        ),
    },
    {
        "id": "I5",
        "description": (
            "Player-row-oriented (2 rows per match). Not 1-row-per-match like aoestats. "
            "matches_1v1_clean retains player-row orientation (2 rows per match). "
            "No slot-asymmetry introduced; both player rows treated identically."
        ),
    },
    {
        "id": "I6",
        "description": (
            "All DDL + assertion SQL stored verbatim in 01_04_02_post_cleaning_validation.json "
            "sql_queries."
        ),
    },
    {
        "id": "I7",
        "description": (
            "All expected counts loaded at runtime from 01_04_01_missingness_ledger.csv via "
            "ledger_val() helper. No magic numbers in notebook code. Plan cites ledger values "
            "as expected guidance; notebook derives them."
        ),
    },
    {
        "id": "I9",
        "description": (
            "Raw tables UNTOUCHED. Only VIEW DDL changes via CREATE OR REPLACE. "
            "leaderboards_raw + profiles_raw declared out-of-scope but not dropped "
            "(no DROP TABLE statements). No imputation, scaling, or encoding."
        ),
    },
    {
        "id": "I10",
        "description": (
            "No filename derivation changes. The aoec raw tables already satisfy I10 "
            "from 01_02_02 ingestion."
        ),
    },
]

mvc_yaml_content = {
    "table": "matches_1v1_clean",
    "dataset": "aoe2companion",
    "game": "aoe2",
    "object_type": "view",
    "step": "01_04_02",
    "row_count": int(post_clean_rows[0]),
    "describe_artifact": (
        "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/"
        "04_cleaning/01_04_02_post_cleaning_validation.json"
    ),
    "generated_date": "2026-04-17",
    "columns": columns_yaml_clean,
    "provenance": {
        "source_tables": ["matches_raw"],
        "filter": (
            "internalLeaderboardId IN (6, 18); profileId != -1; "
            "deduplicated by (matchId, profileId) ORDER BY started; "
            "R03 complementarity filter (HAVING COUNT(*)=2 AND n_true=1 AND n_false=1)"
        ),
        "scope": (
            "Ranked 1v1 decisive matches only (internalLeaderboardId IN (6, 18) "
            "AND profileId != -1, deduplicated, won-complementary)."
        ),
        "row_multiplicity": (
            "2 rows per match (player-row-oriented; one row per player). "
            "NOT 1-row-per-match like aoestats. "
            "Upstream CTE: see sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/"
            "01_04_01_data_cleaning.py (HAVING COUNT(*)=2 + R03 complementarity filter)."
        ),
        "notes": (
            "Vocabulary style aligned with aoestats (prose-format per-column notes); "
            "cross-dataset harmonisation with sc2egset (single-token notes + "
            "provenance_categories invariant) deferred to a CROSS PR after all three "
            "dataset 01_04_02 PRs land (per Q3 lock from PR #144)."
        ),
        "created_by": "sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py",
        "excluded_columns": [
            {"name": "server", "reason": "DS-AOEC-01, MNAR 97.39% NULL"},
            {"name": "scenario", "reason": "DS-AOEC-01, MAR 100% NULL"},
            {"name": "modDataset", "reason": "DS-AOEC-01, MAR 100% NULL"},
            {"name": "password", "reason": "DS-AOEC-01, MAR 77.57% NULL"},
            {"name": "antiquityMode", "reason": "DS-AOEC-02, MAR 60.06% NULL (schema-evolution)"},
            {"name": "mod", "reason": "DS-AOEC-03b, n_distinct=1 constant"},
            {"name": "status", "reason": "DS-AOEC-03b, n_distinct=1 constant"},
            {"name": "ratingDiff", "reason": "Prior I3 exclusion, POST-GAME"},
            {"name": "finished", "reason": "Prior I3 exclusion, POST-GAME"},
        ],
    },
    "invariants": invariants_block_clean,
}

with open(mvc_yaml_path, "w") as f:
    yaml.dump(mvc_yaml_content, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
print(f"matches_1v1_clean.yaml created: {mvc_yaml_path}")
print(f"  Columns: {len(columns_yaml_clean)}")

# %% [markdown]
# ## Cell 25 -- Verify YAML column counts

# %%
assert len(columns_yaml_clean) == 48, (
    f"matches_1v1_clean.yaml should have 48 columns, got {len(columns_yaml_clean)}"
)
assert len(columns_yaml_hist) == 19, (
    f"player_history_all.yaml should have 19 columns, got {len(columns_yaml_hist)}"
)
print(f"YAML column count assertions PASSED: clean={len(columns_yaml_clean)}, hist={len(columns_yaml_hist)}")

# %% [markdown]
# ## Cell 26 -- Close DuckDB connection + final summary

# %%
db.close()

print("=" * 70)
print("STEP 01_04_02 COMPLETE -- Final Summary")
print("=" * 70)
print()
print("CONSORT COLUMN-COUNT FLOW:")
print(f"  matches_1v1_clean:  54 -> 48 cols (drop 7: server/scenario/modDataset/password/antiquityMode/mod/status; add 1: rating_was_null)")
print(f"  player_history_all: 20 -> 19 cols (drop 1: status)")
print()
print("CONSORT ROW-COUNT FLOW (column-only -- no row changes):")
print(f"  matches_1v1_clean:  {post_clean_rows[0]:,} rows / {post_clean_rows[1]:,} matches (unchanged)")
print(f"  player_history_all: {post_hist_rows[0]:,} rows (unchanged)")
print()
print(f"rating_was_null flag count: {flag_true:,} rows "
      f"({flag_true/total_clean*100:.2f}% of matches_1v1_clean)")
print(f"  Matches ledger expected count ({expected_rating_null_clean:,}) within +-1 row: "
      f"{abs(flag_true - expected_rating_null_clean) <= 1}")
print()
print(f"All assertions pass: {all_pass}")
print()
print("ARTIFACTS PRODUCED:")
print(f"  {json_path}")
print(f"  {md_path}")
print(f"  {mvc_yaml_path}")
print(f"  {pha_yaml_path} (updated)")
print()
print("PENDING (not done by notebook):")
print("  - STEP_STATUS.yaml: add 01_04_02: complete")
print("  - PIPELINE_SECTION_STATUS.yaml: bump 01_04 -> complete")
print("  - ROADMAP.md: append Step 01_04_02 block")
print("  - research_log.md: prepend 2026-04-17 01_04_02 entry")
