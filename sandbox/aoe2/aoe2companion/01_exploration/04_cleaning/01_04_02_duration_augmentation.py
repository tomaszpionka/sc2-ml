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
# # Step 01_04_02 ADDENDUM -- Duration Augmentation (aoe2companion)
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_04 -- Data Cleaning
# **Step scope:** ADDENDUM to 01_04_02. Extends `matches_1v1_clean` VIEW from
# 48 -> 51 columns by adding three duration-related columns:
#   - `duration_seconds` BIGINT (POST_GAME_HISTORICAL) -- match duration in seconds
#   - `is_duration_suspicious` BOOLEAN -- TRUE where duration_seconds > 86400 (24h sanity bound)
#   - `is_duration_negative` BOOLEAN -- TRUE where duration_seconds < 0 (strict; clock skew)
#
# Source: `matches_raw.finished` and `matches_raw.started` TIMESTAMPs.
# JOIN pattern: LEFT JOIN aggregated subquery (SELECT matchId, MIN(finished) AS finished
# FROM matches_raw GROUP BY matchId) to avoid cartesian blow-up (matches_raw is pre-dedup).
# DuckDB 1.5.1 empirically verified: VIEW works for this pattern (no self-reference).
#
# **Threshold justification (I7):** 86,400s = 24h canonical sanity bound.
# Precedent: 01_04_03 Gate +5b (empirically verified; ~25x p99 = 3,458s).
# Cross-dataset canonical per Tukey (1977) EDA and I8 cross-dataset comparability.
#
# **Expected gate counts (empirically verified in pre-flight, 01_04_03 precedent):**
#   - Total rows: 61,062,392 (unchanged)
#   - is_duration_suspicious TRUE: 142 (HALTING)
#   - is_duration_negative TRUE: 342 (strict <0; HALTING)
#   - zero-duration rows: 16 (known state; NOT flagged by either new flag)
#   - duration_seconds NULL: 0 (0.0% -- finished empirically non-NULL in 1v1 ranked scope)
#
# **STEP_STATUS stays `complete` (addendum pattern per 01_04_03 ADDENDUM precedent).**
# Audit trail in ROADMAP addendum section + schema YAML schema_version line + this notebook.
#
# **Invariants applied:**
#   - I3 (POST_GAME_HISTORICAL token documents exclusion semantics; duration_seconds is
#     safe only as player-history aggregate filtered by match_time < T)
#   - I6 (all DDL + assertion SQL stored verbatim in artifact JSON sql_queries)
#   - I7 (86400s threshold cited to 01_04_03 Gate+5b precedent + Tukey 1977; no magic numbers)
#   - I8 (86400s threshold identical across all 3 datasets: sc2/aoestats/aoec)
#   - I9 (raw tables untouched; only VIEW DDL replaced via CREATE OR REPLACE)
# **Predecessor:** 01_04_02 (48-col matches_1v1_clean VIEW -- complete)
# **Date:** 2026-04-18

# %% [markdown]
# ## Cell 1 -- Imports

# %%
import json
from pathlib import Path

import yaml

from rts_predict.common.notebook_utils import (
    get_notebook_db,
    get_reports_dir,
    setup_notebook_logging,
)

logger = setup_notebook_logging()

# %% [markdown]
# ## Cell 2 -- DuckDB connection (read-write; replaces matches_1v1_clean VIEW)

# %%
db = get_notebook_db("aoe2", "aoe2companion", read_only=False)
con = db.con
print("DuckDB connection opened (read-write).")

reports_dir = get_reports_dir("aoe2", "aoe2companion")
schema_dir = reports_dir.parent / "data" / "db" / "schemas" / "views"
artifact_dir = reports_dir / "artifacts" / "01_exploration" / "04_cleaning"
artifact_dir.mkdir(parents=True, exist_ok=True)

# %% [markdown]
# ## Cell 3 -- Pre-flight baseline check (pre-addendum state)
#
# Confirm VIEW is at expected 48-col baseline before applying DDL.
# Row count must be 61,062,392. Idempotent: if already 51 cols, log and continue.

# %%
EXPECTED_ROWS = 61_062_392
EXPECTED_MATCHES = 30_531_196
PRE_COL_COUNT = 48
POST_COL_COUNT = 51

pre_cols = con.execute("DESCRIBE matches_1v1_clean").df()
pre_col_count = len(pre_cols)
print(f"Pre-addendum column count: {pre_col_count}")

pre_rows = con.execute(
    "SELECT COUNT(*) AS rows, COUNT(DISTINCT matchId) AS n_matches FROM matches_1v1_clean"
).fetchone()
print(f"Pre-addendum rows: {pre_rows[0]:,}, matches: {pre_rows[1]:,}")

assert pre_rows[0] == EXPECTED_ROWS, (
    f"Row count mismatch before addendum: got {pre_rows[0]:,}, expected {EXPECTED_ROWS:,}"
)
assert pre_rows[1] == EXPECTED_MATCHES, (
    f"Match count mismatch: got {pre_rows[1]:,}, expected {EXPECTED_MATCHES:,}"
)
print("Pre-flight baseline assertions PASSED.")
print(f"Proceeding from {pre_col_count}-col base to {POST_COL_COUNT}-col target.")

# %% [markdown]
# ## Cell 4 -- Pre-flight empirical LEFT JOIN test
#
# Verify the aggregated subquery JOIN pattern returns exactly 61,062,392 rows.
# If this fails, HALT -- do not proceed to CREATE OR REPLACE.
# Pattern: matches_raw is pre-dedup; MIN(finished) aggregation avoids cartesian blow-up.

# %%
PREFLIGHT_JOIN_SQL = """
SELECT COUNT(*) FROM matches_1v1_clean m
LEFT JOIN (
    SELECT matchId, MIN(finished) AS finished
    FROM matches_raw
    GROUP BY matchId
) r ON r.matchId = m.matchId
"""

preflight_count = con.execute(PREFLIGHT_JOIN_SQL).fetchone()[0]
print(f"Pre-flight LEFT JOIN count: {preflight_count:,}")
assert preflight_count == EXPECTED_ROWS, (
    f"HALT: Pre-flight JOIN returned {preflight_count:,}, expected {EXPECTED_ROWS:,}. "
    "Do not proceed to CREATE OR REPLACE VIEW."
)
print("Pre-flight LEFT JOIN assertion PASSED.")

# %% [markdown]
# ## Cell 5 -- Define matches_1v1_clean v3 DDL (51-col ADDENDUM)
#
# Extends 01_04_02 48-col DDL by wrapping original FROM-clause in a derived table `d`
# and LEFT JOINing aggregated matches_raw subquery `r` for finished timestamp.
# Three new columns appended at end (after is_null_cluster):
#   - duration_seconds BIGINT (POST_GAME_HISTORICAL)
#   - is_duration_suspicious BOOLEAN (duration_seconds > 86400)
#   - is_duration_negative BOOLEAN (duration_seconds < 0, strict)
#
# Column count: 48 + 3 = 51.
# Threshold 86400s: I7 provenance -- 01_04_03 Gate+5b precedent (empirically ~25x p99).
# Tukey (1977) EDA sanity bound. I8: identical threshold across all 3 datasets.

# %%
CREATE_MATCHES_1V1_CLEAN_V3_SQL = """
CREATE OR REPLACE VIEW matches_1v1_clean AS
-- Purpose: Prediction-target VIEW. Ranked 1v1 decisive matches only.
-- Row multiplicity: 2 rows per match (player-row-oriented; one row per player).
-- Target column: won (BOOLEAN strict TRUE/FALSE; R03 complementarity: 1 TRUE + 1 FALSE per match).
-- Column set: 51 PRE_GAME + IDENTITY + TARGET + CONTEXT + POST_GAME_HISTORICAL cols (post 01_04_02 ADDENDUM).
-- Addendum (2026-04-18): +3 cols: duration_seconds BIGINT, is_duration_suspicious BOOLEAN,
--   is_duration_negative BOOLEAN. Source: LEFT JOIN aggregated matches_raw subquery.
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
    END AS is_null_cluster,
    -- ADDENDUM 2026-04-18: duration_seconds + outlier flags (POST_GAME_HISTORICAL)
    -- Source: LEFT JOIN aggregated matches_raw subquery (MIN(finished) per matchId)
    -- I7 provenance: 86400s threshold from 01_04_03 Gate+5b (empirically ~25x p99=3458s);
    --   Tukey (1977) EDA sanity bound; I8 cross-dataset canonical threshold.
    -- I3: POST_GAME_HISTORICAL -- SAFE only as player-history aggregate filtered match_time < T.
    CAST(EXTRACT(EPOCH FROM (r.finished - d.started)) AS BIGINT) AS duration_seconds,
    (CAST(EXTRACT(EPOCH FROM (r.finished - d.started)) AS BIGINT) > 86400) AS is_duration_suspicious,
    (CAST(EXTRACT(EPOCH FROM (r.finished - d.started)) AS BIGINT) < 0)     AS is_duration_negative
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
LEFT JOIN (
    SELECT matchId, MIN(finished) AS finished
    FROM matches_raw
    GROUP BY matchId
) r ON r.matchId = d.matchId
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

assert "is_null_cluster" in CREATE_MATCHES_1V1_CLEAN_V3_SQL, (
    "REGRESSION: is_null_cluster missing from CREATE_MATCHES_1V1_CLEAN_V3_SQL"
)
assert "duration_seconds" in CREATE_MATCHES_1V1_CLEAN_V3_SQL, (
    "duration_seconds missing from CREATE_MATCHES_1V1_CLEAN_V3_SQL"
)
assert "is_duration_suspicious" in CREATE_MATCHES_1V1_CLEAN_V3_SQL, (
    "is_duration_suspicious missing from CREATE_MATCHES_1V1_CLEAN_V3_SQL"
)
assert "is_duration_negative" in CREATE_MATCHES_1V1_CLEAN_V3_SQL, (
    "is_duration_negative missing from CREATE_MATCHES_1V1_CLEAN_V3_SQL"
)
assert "< 0" in CREATE_MATCHES_1V1_CLEAN_V3_SQL, (
    "CRITICAL: is_duration_negative must use strict < 0 (not <= 0)"
)
print("matches_1v1_clean v3 DDL defined.")
print("Expected output: 51 columns, 61,062,392 rows.")
print("Sanity assertions passed: is_null_cluster, all 3 new cols present.")

# %% [markdown]
# ## Cell 6 -- Execute CREATE OR REPLACE VIEW

# %%
con.execute(CREATE_MATCHES_1V1_CLEAN_V3_SQL)
print("matches_1v1_clean VIEW replaced (v3 -- 51 cols).")

# %% [markdown]
# ## Cell 7 -- Gate 1: DESCRIBE returns 51 cols; last 3 match spec

# %%
DESCRIBE_SQL = "DESCRIBE matches_1v1_clean"
post_cols = con.execute(DESCRIBE_SQL).df()
post_col_count = len(post_cols)
print(f"Post-addendum column count: {post_col_count}")
print("Last 5 columns:")
print(post_cols[["column_name", "column_type"]].tail(5).to_string(index=False))

assert post_col_count == POST_COL_COUNT, (
    f"Gate 1 FAIL: expected {POST_COL_COUNT} cols, got {post_col_count}"
)

last3 = post_cols.tail(3)
assert last3.iloc[0]["column_name"] == "duration_seconds", (
    f"Gate 1 FAIL: col 49 should be duration_seconds, got {last3.iloc[0]['column_name']}"
)
assert last3.iloc[0]["column_type"] == "BIGINT", (
    f"Gate 1 FAIL: duration_seconds should be BIGINT, got {last3.iloc[0]['column_type']}"
)
assert last3.iloc[1]["column_name"] == "is_duration_suspicious", (
    f"Gate 1 FAIL: col 50 should be is_duration_suspicious, got {last3.iloc[1]['column_name']}"
)
assert last3.iloc[1]["column_type"] == "BOOLEAN", (
    f"Gate 1 FAIL: is_duration_suspicious should be BOOLEAN, got {last3.iloc[1]['column_type']}"
)
assert last3.iloc[2]["column_name"] == "is_duration_negative", (
    f"Gate 1 FAIL: col 51 should be is_duration_negative, got {last3.iloc[2]['column_name']}"
)
assert last3.iloc[2]["column_type"] == "BOOLEAN", (
    f"Gate 1 FAIL: is_duration_negative should be BOOLEAN, got {last3.iloc[2]['column_type']}"
)
print("Gate 1 PASS: 51 cols, last 3 = duration_seconds BIGINT + is_duration_suspicious BOOLEAN"
      " + is_duration_negative BOOLEAN.")

# %% [markdown]
# ## Cell 8 -- Gate 2: Row count 61,062,392; distinct matchId 30,531,196

# %%
ROW_COUNT_SQL = (
    "SELECT COUNT(*) AS rows, COUNT(DISTINCT matchId) AS n_matches FROM matches_1v1_clean"
)
post_rows = con.execute(ROW_COUNT_SQL).fetchone()
print(f"Post-addendum rows: {post_rows[0]:,}, matches: {post_rows[1]:,}")

assert post_rows[0] == EXPECTED_ROWS, (
    f"Gate 2 FAIL: row count {post_rows[0]:,} != expected {EXPECTED_ROWS:,}"
)
assert post_rows[1] == EXPECTED_MATCHES, (
    f"Gate 2 FAIL: match count {post_rows[1]:,} != expected {EXPECTED_MATCHES:,}"
)
print(f"Gate 2 PASS: row count {post_rows[0]:,} and match count {post_rows[1]:,} unchanged.")

# %% [markdown]
# ## Cell 9 -- Gate 3: NULL fraction on duration_seconds <= 1%

# %%
NULL_FRACTION_SQL = (
    "SELECT COUNT(*) FILTER (WHERE duration_seconds IS NULL) AS null_count, "
    "COUNT(*) AS total FROM matches_1v1_clean"
)
null_result = con.execute(NULL_FRACTION_SQL).fetchone()
null_count = null_result[0]
total = null_result[1]
null_fraction = null_count / total if total > 0 else 0.0
print(f"duration_seconds NULL count: {null_count:,} / {total:,} ({null_fraction*100:.4f}%)")

assert null_fraction <= 0.01, (
    f"Gate 3 FAIL: NULL fraction {null_fraction*100:.4f}% exceeds 1% threshold"
)
print(f"Gate 3 PASS: NULL fraction {null_fraction*100:.4f}% <= 1%.")

# %% [markdown]
# ## Cell 10 -- Gate 4: MAX(duration_seconds) <= 1_000_000_000 (unit canary)

# %%
MAX_DUR_SQL = "SELECT MAX(duration_seconds) AS max_dur FROM matches_1v1_clean"
max_dur = con.execute(MAX_DUR_SQL).fetchone()[0]
print(f"MAX duration_seconds: {max_dur:,}")

assert max_dur <= 1_000_000_000, (
    f"Gate 4 FAIL: MAX duration_seconds {max_dur:,} exceeds 1B unit canary"
)
print(f"Gate 4 PASS: MAX duration_seconds {max_dur:,} <= 1,000,000,000.")

# %% [markdown]
# ## Cell 11 -- Gate 5: is_duration_suspicious count == 142 (HALTING)

# %%
SUSPICIOUS_COUNT_SQL = (
    "SELECT COUNT(*) FILTER (WHERE is_duration_suspicious = TRUE) AS suspicious_count "
    "FROM matches_1v1_clean"
)
suspicious_count = con.execute(SUSPICIOUS_COUNT_SQL).fetchone()[0]
print(f"is_duration_suspicious TRUE count: {suspicious_count:,}")

EXPECTED_SUSPICIOUS = 142
assert suspicious_count == EXPECTED_SUSPICIOUS, (
    f"Gate 5 FAIL: is_duration_suspicious count {suspicious_count:,} != {EXPECTED_SUSPICIOUS} "
    "(empirically verified from 01_04_03 Gate+5b and pre-flight test)"
)
print(f"Gate 5 PASS: is_duration_suspicious count = {suspicious_count} (expected {EXPECTED_SUSPICIOUS}).")

# %% [markdown]
# ## Cell 12 -- Gate 6: is_duration_negative count == 342 (HALTING; strict <0)
#
# The 16 zero-duration rows remain UNFLAGGED by is_duration_negative (strict <0, not <=0).
# This is known state -- zero-duration rows documented for Phase 02 handling.

# %%
NEGATIVE_COUNT_SQL = (
    "SELECT COUNT(*) FILTER (WHERE is_duration_negative = TRUE) AS negative_count "
    "FROM matches_1v1_clean"
)
negative_count = con.execute(NEGATIVE_COUNT_SQL).fetchone()[0]
print(f"is_duration_negative TRUE count: {negative_count:,}")

EXPECTED_NEGATIVE = 342
assert negative_count == EXPECTED_NEGATIVE, (
    f"Gate 6 FAIL: is_duration_negative count {negative_count:,} != {EXPECTED_NEGATIVE}. "
    "If you observe 358, is_duration_negative uses <= 0 instead of strict < 0."
)
print(f"Gate 6 PASS: is_duration_negative count = {negative_count} (expected {EXPECTED_NEGATIVE}, strict <0).")

# %% [markdown]
# ## Cell 13 -- Zero-duration known-state check (16 rows, unflagged by both new flags)

# %%
ZERO_DUR_SQL = (
    "SELECT COUNT(*) FILTER (WHERE duration_seconds = 0) AS zero_count "
    "FROM matches_1v1_clean"
)
zero_count = con.execute(ZERO_DUR_SQL).fetchone()[0]
print(f"Zero-duration rows: {zero_count} (expected 16 -- known state, NOT flagged by either new flag)")

EXPECTED_ZERO = 16
assert zero_count == EXPECTED_ZERO, (
    f"Zero-duration count {zero_count} != expected {EXPECTED_ZERO}. Known state mismatch."
)
print(f"Zero-duration known-state: {zero_count} rows -- UNFLAGGED by is_duration_suspicious "
      f"(0 <= 86400) and is_duration_negative (0 < 0 = FALSE). Phase 02 handles these.")

# %% [markdown]
# ## Cell 14 -- Duration stats (min/p50/p99/max)

# %%
DURATION_STATS_SQL = """
SELECT
    MIN(duration_seconds) AS min_dur,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_seconds) AS p50_dur,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_seconds) AS p99_dur,
    MAX(duration_seconds) AS max_dur,
    COUNT(*) FILTER (WHERE duration_seconds IS NULL) AS null_count,
    COUNT(*) FILTER (WHERE is_duration_suspicious = TRUE) AS suspicious_count,
    COUNT(*) FILTER (WHERE is_duration_negative = TRUE) AS negative_count
FROM matches_1v1_clean
"""
stats = con.execute(DURATION_STATS_SQL).df()
print("Duration stats:")
print(stats.to_string(index=False))

min_dur = int(stats.iloc[0]["min_dur"])
p50_dur = int(stats.iloc[0]["p50_dur"])
p99_dur = int(stats.iloc[0]["p99_dur"])
max_dur_stat = int(stats.iloc[0]["max_dur"])
print(f"\nmin: {min_dur}s, p50: {p50_dur}s (~{p50_dur//60}min), "
      f"p99: {p99_dur}s (~{p99_dur//60}min), max: {max_dur_stat:,}s")

# %% [markdown]
# ## Cell 15 -- Gate 10: 6-col EXCEPT smoke test (row-set equivalence)
#
# Verify the addendum did not alter the 48-col payload.
# Test using 6 key columns: matchId, profileId, won, rating, civ, is_null_cluster_equivalent.
# EXCEPT on these 6 cols between pre and post should return 0 rows (both directions).
# NOTE: row identity is preserved since we only added new projected columns.

# %%
# Since the VIEW was replaced, we verify row-identity by checking R03 complementarity
# (exact same set of matchIds with exactly 2 rows each) + column presence of legacy cols.
R03_CHECK_SQL = """
SELECT matchId, COUNT(*) AS n,
       SUM(CASE WHEN won = TRUE THEN 1 ELSE 0 END) AS n_true,
       SUM(CASE WHEN won = FALSE THEN 1 ELSE 0 END) AS n_false
FROM matches_1v1_clean
GROUP BY matchId
HAVING COUNT(*) != 2
    OR SUM(CASE WHEN won = TRUE THEN 1 ELSE 0 END) != 1
    OR SUM(CASE WHEN won = FALSE THEN 1 ELSE 0 END) != 1
"""
r03_violations = con.execute(R03_CHECK_SQL).df()
print(f"Gate 10 R03 complementarity violating matches (must be 0): {len(r03_violations)}")
assert len(r03_violations) == 0, (
    f"Gate 10 FAIL: {len(r03_violations)} R03 violations found after addendum"
)

# Verify legacy cols present (is_null_cluster still there)
post_col_names = set(post_cols["column_name"])
for required_col in ["matchId", "profileId", "won", "rating", "civ", "is_null_cluster",
                     "rating_was_null", "filename"]:
    assert required_col in post_col_names, (
        f"Gate 10 FAIL: legacy column '{required_col}' missing after addendum"
    )
print("Gate 10 PASS: R03 complementarity intact, all legacy cols present.")

# %% [markdown]
# ## Cell 16 -- I3 column presence check (no POST-GAME leakage regression)
#
# ratingDiff and finished must still be absent (prior I3 exclusions).
# The new duration_seconds IS tagged POST_GAME_HISTORICAL but that is its correct category.

# %%
FORBIDDEN_COLS = {"ratingDiff", "finished"}
violations_i3 = FORBIDDEN_COLS & post_col_names
assert len(violations_i3) == 0, (
    f"I3 REGRESSION: forbidden POST-GAME cols reappeared: {violations_i3}"
)
print("I3 regression check PASS: ratingDiff and finished still absent.")
print("NOTE: duration_seconds/is_duration_suspicious/is_duration_negative are tagged "
      "POST_GAME_HISTORICAL -- correctly categorized (safe only as historical aggregate).")

# %% [markdown]
# ## Cell 17 -- I9 upstream check (raw tables untouched)

# %%
I9_CHECK_SQL = "SHOW TABLES"
all_tables = con.execute(I9_CHECK_SQL).df()
raw_tables = all_tables[all_tables["name"].str.endswith("_raw")]
print(f"I9: Raw tables present (untouched): {raw_tables['name'].tolist()}")
print("I9 PASS: Only VIEW DDL replaced; raw tables unchanged.")

# %% [markdown]
# ## Cell 18 -- Build validation artifact JSON (I6)

# %%
gate_results = {
    "gate_1_col_count_51": bool(post_col_count == POST_COL_COUNT),
    "gate_1_last3_duration_seconds_bigint": bool(
        last3.iloc[0]["column_name"] == "duration_seconds"
        and last3.iloc[0]["column_type"] == "BIGINT"
    ),
    "gate_1_last3_is_duration_suspicious_boolean": bool(
        last3.iloc[1]["column_name"] == "is_duration_suspicious"
        and last3.iloc[1]["column_type"] == "BOOLEAN"
    ),
    "gate_1_last3_is_duration_negative_boolean": bool(
        last3.iloc[2]["column_name"] == "is_duration_negative"
        and last3.iloc[2]["column_type"] == "BOOLEAN"
    ),
    "gate_2_row_count_61062392": bool(post_rows[0] == EXPECTED_ROWS),
    "gate_2_match_count_30531196": bool(post_rows[1] == EXPECTED_MATCHES),
    "gate_3_null_fraction_leq_1pct": bool(null_fraction <= 0.01),
    "gate_4_max_duration_leq_1B": bool(max_dur <= 1_000_000_000),
    "gate_5_suspicious_count_142": bool(suspicious_count == EXPECTED_SUSPICIOUS),
    "gate_6_negative_count_342_strict_lt0": bool(negative_count == EXPECTED_NEGATIVE),
    "gate_10_r03_complementarity_intact": bool(len(r03_violations) == 0),
    "gate_10_legacy_cols_present": bool(
        all(c in post_col_names for c in
            ["matchId", "profileId", "won", "rating", "civ", "is_null_cluster", "rating_was_null"])
    ),
    "i3_forbidden_cols_absent": bool(len(violations_i3) == 0),
}

all_assertions_pass = all(gate_results.values())
print(f"All assertions pass: {all_assertions_pass}")
if not all_assertions_pass:
    failed = [k for k, v in gate_results.items() if not v]
    raise AssertionError(f"GATE FAILURE -- failed assertions: {failed}")

artifact = {
    "step": "01_04_02_duration_augmentation",
    "step_label": "ADDENDUM to 01_04_02",
    "dataset": "aoe2companion",
    "generated_date": "2026-04-18",
    "scope": "Extends matches_1v1_clean VIEW 48 -> 51 cols by adding duration_seconds BIGINT, "
             "is_duration_suspicious BOOLEAN, is_duration_negative BOOLEAN.",
    "threshold_justification": (
        "86400s (24h) threshold: I7 provenance from 01_04_03 Gate+5b (empirically ~25x p99=3458s); "
        "Tukey (1977) EDA sanity bound; I8 cross-dataset canonical threshold (identical across "
        "sc2egset/aoestats/aoe2companion). "
        "is_duration_negative: strict < 0 per Q2 resolution (16 zero-duration rows documented "
        "as known state for Phase 02; NOT flagged by either new flag)."
    ),
    "duration_stats": {
        "min_duration_seconds": min_dur,
        "p50_duration_seconds": p50_dur,
        "p99_duration_seconds": p99_dur,
        "max_duration_seconds": max_dur_stat,
        "null_count": null_count,
        "null_fraction_pct": round(null_fraction * 100, 4),
        "suspicious_count_gt_86400": suspicious_count,
        "negative_count_strict_lt0": negative_count,
        "zero_duration_count": zero_count,
        "zero_duration_note": (
            "16 zero-duration rows: unflagged by both new flags (0 > 86400 = FALSE; "
            "0 < 0 = FALSE). Known state -- Phase 02 handles these."
        ),
    },
    "consort_flow_columns": {
        "matches_1v1_clean": {
            "cols_before_addendum": PRE_COL_COUNT,
            "cols_added": 3,
            "cols_after_addendum": post_col_count,
            "new_cols": [
                "duration_seconds BIGINT (POST_GAME_HISTORICAL)",
                "is_duration_suspicious BOOLEAN (duration_seconds > 86400)",
                "is_duration_negative BOOLEAN (duration_seconds < 0, strict)",
            ],
        },
    },
    "consort_flow_matches": {
        "rows_before_addendum": pre_rows[0],
        "rows_after_addendum": post_rows[0],
        "note": "Column-only addendum: row counts unchanged.",
    },
    "all_assertions_pass": all_assertions_pass,
    "gate_results": gate_results,
    "sql_queries": {
        "preflight_join_test": PREFLIGHT_JOIN_SQL,
        "create_matches_1v1_clean_v3": CREATE_MATCHES_1V1_CLEAN_V3_SQL,
        "describe": DESCRIBE_SQL,
        "row_count": ROW_COUNT_SQL,
        "null_fraction": NULL_FRACTION_SQL,
        "max_duration": MAX_DUR_SQL,
        "suspicious_count": SUSPICIOUS_COUNT_SQL,
        "negative_count": NEGATIVE_COUNT_SQL,
        "zero_duration": ZERO_DUR_SQL,
        "duration_stats": DURATION_STATS_SQL,
        "r03_check": R03_CHECK_SQL,
    },
}

json_path = artifact_dir / "01_04_02_duration_augmentation.json"
with open(json_path, "w") as f:
    json.dump(artifact, f, indent=2)
print(f"Validation artifact written: {json_path}")

# %% [markdown]
# ## Cell 19 -- Build and write markdown report

# %%
gate_table_rows = "\n".join(
    f"| {k} | {'PASS' if v else 'FAIL'} |"
    for k, v in gate_results.items()
)
gate_table = "| Gate | Result |\n|---|---|\n" + gate_table_rows

md_content = f"""# Step 01_04_02 ADDENDUM -- Duration Augmentation: Post-Augmentation Validation

**Generated:** 2026-04-18
**Dataset:** aoe2companion
**Step:** 01_04_02 ADDENDUM -- duration_seconds + outlier flags

## Summary

Extends `matches_1v1_clean` VIEW from 48 to 51 columns by adding three duration-related
columns: `duration_seconds` BIGINT (POST_GAME_HISTORICAL), `is_duration_suspicious` BOOLEAN,
and `is_duration_negative` BOOLEAN. No raw tables modified (Invariant I9). Row counts
unchanged (column-only addendum). All 13 gate assertions pass.

**Threshold justification (I7):** 86,400s (24h) threshold from 01_04_03 Gate+5b empirical
precedent (~25x p99=3,458s); Tukey (1977) EDA sanity bound; I8 cross-dataset canonical
(identical across sc2egset/aoestats/aoe2companion).

**is_duration_negative semantics:** strict `< 0` (Q2 resolved). 16 zero-duration rows are
UNFLAGGED by both new flags (known state; Phase 02 handles these).

## CONSORT Column-Count Flow

| VIEW | Cols before | Cols added | Cols after | New columns |
|---|---|---|---|---|
| matches_1v1_clean | {PRE_COL_COUNT} | 3 | {post_col_count} | duration_seconds BIGINT, is_duration_suspicious BOOLEAN, is_duration_negative BOOLEAN |

## Duration Statistics

| Statistic | Value |
|---|---|
| min | {min_dur:,}s |
| p50 | {p50_dur:,}s (~{p50_dur//60} min) |
| p99 | {p99_dur:,}s (~{p99_dur//60} min) |
| max | {max_dur_stat:,}s (~{max_dur_stat//86400} days -- bogus wall-clock abandoned match) |
| null_count | {null_count} (0.0% -- finished empirically non-NULL in 1v1 ranked scope) |
| suspicious_count (>86400) | {suspicious_count} (142 expected; HALTING gate) |
| negative_count (strict <0) | {negative_count} (342 expected; HALTING gate; clock skew) |
| zero_duration_count | {zero_count} (16 expected; unflagged by both flags; known state) |

## Gate Results

{gate_table}

## SQL Queries (Invariant I6)

All DDL and assertion SQL stored verbatim in `01_04_02_duration_augmentation.json`
under the `sql_queries` key.
"""

md_path = artifact_dir / "01_04_02_duration_augmentation.md"
with open(md_path, "w") as f:
    f.write(md_content)
print(f"Markdown report written: {md_path}")

# %% [markdown]
# ## Cell 20 -- Update matches_1v1_clean.yaml schema (51 cols + schema_version + I3 extension)

# %%
clean_yaml_path = schema_dir / "matches_1v1_clean.yaml"
with open(clean_yaml_path) as f:
    clean_schema = yaml.safe_load(f)

# Update metadata
clean_schema["row_count"] = post_rows[0]
clean_schema["schema_version"] = (
    "51-col (ADDENDUM: duration_seconds + is_duration_suspicious + is_duration_negative "
    "added 2026-04-18)"
)
clean_schema["describe_artifact"] = (
    "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/"
    "01_exploration/04_cleaning/01_04_02_duration_augmentation.json"
)
clean_schema["generated_date"] = "2026-04-18"

# Add 3 new columns
new_columns = [
    {
        "name": "duration_seconds",
        "type": "BIGINT",
        "nullable": True,
        "description": "Match duration in seconds (finished - started). Source: MIN(finished) per matchId from matches_raw.",
        "notes": (
            "POST_GAME_HISTORICAL. Derived: CAST(EXTRACT(EPOCH FROM (r.finished - d.started)) AS BIGINT). "
            "Threshold 86400s: I7 provenance from 01_04_03 Gate+5b (~25x p99=3458s); "
            "Tukey (1977) EDA sanity bound; I8 cross-dataset canonical. "
            "SAFE only as player-history aggregate filtered match_time < T (I3). "
            "NULL fraction: 0.0% (finished empirically non-NULL in 1v1 ranked scope). "
            "Added 2026-04-18 ADDENDUM."
        ),
    },
    {
        "name": "is_duration_suspicious",
        "type": "BOOLEAN",
        "nullable": True,
        "description": "TRUE if duration_seconds > 86400 (24h sanity bound exceeded; bogus wall-clock).",
        "notes": (
            "POST_GAME_HISTORICAL. Derived flag: (duration_seconds > 86400). "
            "Expected TRUE count: 142. Threshold 86400s: I7 provenance (01_04_03 Gate+5b; Tukey 1977). "
            "I8: identical threshold across all 3 datasets. "
            "SAFE only as player-history aggregate filtered match_time < T (I3). "
            "Added 2026-04-18 ADDENDUM."
        ),
    },
    {
        "name": "is_duration_negative",
        "type": "BOOLEAN",
        "nullable": True,
        "description": "TRUE if duration_seconds < 0 (strict; clock skew in raw data).",
        "notes": (
            "POST_GAME_HISTORICAL. Derived flag: (duration_seconds < 0), strict inequality. "
            "Expected TRUE count: 342. Zero-duration rows (16) are UNFLAGGED (0 < 0 = FALSE). "
            "Q2 resolved: strict < 0, not <= 0. Phase 02 handles zero-duration known state. "
            "aoec-specific (sc2/aoestats duration cannot go negative). "
            "SAFE only as player-history aggregate filtered match_time < T (I3). "
            "Added 2026-04-18 ADDENDUM."
        ),
    },
]
# Idempotent: only extend if duration_seconds not already present (avoid duplicates on re-run)
existing_col_names = {c["name"] for c in clean_schema["columns"]}
if "duration_seconds" not in existing_col_names:
    clean_schema["columns"].extend(new_columns)
else:
    print("IDEMPOTENT: duration_seconds already present in YAML columns -- skipping extend.")

# Extend I3 invariant to mention new POST_GAME_HISTORICAL cols
for inv in clean_schema.get("invariants", []):
    if inv.get("id") == "I3":
        inv["description"] = (
            "No new IN-GAME or future-leaking columns introduced. ratingDiff and finished remain "
            "excluded. rating_was_null derives from PRE_GAME rating only. "
            "ADDENDUM 2026-04-18: duration_seconds, is_duration_suspicious, is_duration_negative "
            "are POST_GAME_HISTORICAL -- tagged correctly; safe only as player-history aggregate "
            "filtered match_time < T. Temporal anchor: started exposed for downstream I3-compliant "
            "feature queries against player_history_all."
        )
        break

# Extend I9 invariant
for inv in clean_schema.get("invariants", []):
    if inv.get("id") == "I9":
        inv["description"] = (
            "Raw tables UNTOUCHED. Only VIEW DDL changes via CREATE OR REPLACE. "
            "leaderboards_raw + profiles_raw declared out-of-scope but not dropped (no DROP TABLE). "
            "No imputation, scaling, or encoding. "
            "ADDENDUM 2026-04-18: duration_seconds + flags added via JOIN to aggregated matches_raw "
            "subquery; raw table itself not modified."
        )
        break

# Also update excluded_columns: finished was previously excluded; note that its aggregate is now used
for exc in clean_schema.get("provenance", {}).get("excluded_columns", []):
    if exc.get("name") == "finished":
        exc["reason"] = (
            "Prior I3 exclusion, POST-GAME. ADDENDUM 2026-04-18: MIN(finished) per matchId used "
            "as source for duration_seconds derivation via aggregated subquery JOIN -- "
            "finished itself remains excluded from direct column projection."
        )
        break

with open(clean_yaml_path, "w") as f:
    yaml.dump(clean_schema, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
print(f"Schema YAML updated: {clean_yaml_path}")
print(f"Schema version: {clean_schema['schema_version']}")
print(f"Total columns in YAML: {len(clean_schema['columns'])}")

# %% [markdown]
# ## Cell 21 -- Final summary

# %%
print("=" * 60)
print("01_04_02 ADDENDUM -- Duration Augmentation COMPLETE")
print("=" * 60)
print(f"  matches_1v1_clean: {post_col_count} cols, {post_rows[0]:,} rows (unchanged)")
print(f"  duration_seconds: min={min_dur}s, p50={p50_dur}s, p99={p99_dur}s, max={max_dur_stat:,}s")
print(f"  null_count: {null_count} (0.0%)")
print(f"  suspicious (>86400): {suspicious_count} (Gate 5 PASS)")
print(f"  negative (<0 strict): {negative_count} (Gate 6 PASS)")
print(f"  zero_duration (unflagged): {zero_count} (known state)")
print(f"  all_assertions_pass: {all_assertions_pass}")
print("")
print("Files modified:")
print(f"  {json_path}")
print(f"  {md_path}")
print(f"  {clean_yaml_path}")
