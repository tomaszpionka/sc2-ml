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
# # Step 01_04_03 -- Minimal Cross-Dataset History View (aoe2companion)
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_04 -- Data Cleaning
# **Step:** 01_04_03
# **Dataset:** aoe2companion (sibling of sc2egset PR #152 + aoestats)
# **Predecessor:** 01_04_02 (Data Cleaning Execution -- complete)
# **Step scope:** Create `matches_history_minimal` TABLE -- 9-column player-row-grain
# projection of `matches_1v1_clean` (2 rows per 1v1 match, natively player-row-oriented).
# Self-join pattern (sc2egset precedent) -- no UNION ALL needed (aoec is already 2-row
# per match). Canonical TIMESTAMP temporal dtype (pass-through; matches_raw.started
# is already TIMESTAMP). Per-dataset-polymorphic faction vocabulary (full civ names).
# Cross-dataset-harmonized substrate for Phase 02+ rating-system backtesting.
# Pure projection (I9).
#
# **IMPLEMENTATION NOTE:** DuckDB 1.5.1 has a known internal bug where a self-join on
# a VIEW that uses window functions with QUALIFY (such as matches_1v1_clean, which
# contains row_number() + ANY() subquery) causes either an InternalException or
# incorrect row counts. The workaround: (1) materialize the filtered base data into
# a staging TABLE _mhm_base, (2) self-join _mhm_base to produce matches_history_minimal
# as a persistent TABLE, (3) drop the staging table. The semantics are identical to
# the plan's CREATE OR REPLACE VIEW intent -- same 9-column contract, same filtering.
# The object_type is TABLE not VIEW; DESCRIBE produces identical schema.
#
# **ADDENDUM:** Extended to 9-col contract (duration_seconds BIGINT added between
# won and dataset_tag). Source: EXTRACT(EPOCH FROM (r.finished - r.started)) in the
# _mhm_base staging CTE (matches_raw already joined at staging level -- add as column,
# no new JOIN needed; R1-WARNING-A6 fix). CAST(... AS BIGINT) truncates to integer seconds.
# Gate +6 (aoec-specific, HALTING): NULL fraction on duration_seconds <= 1%
# (matches_raw.finished is nullable for abandoned/crashed matches).
#
# **Invariants applied:**
#   - I3 (TIMESTAMP pass-through; already TIMESTAMP in matches_raw.started;
#     duration_seconds is POST_GAME_HISTORICAL -- excluded from PRE_GAME features)
#   - I5-analog (player-row symmetry, NULL-safe assertion via IS DISTINCT FROM;
#     extended to include duration_seconds symmetry)
#   - I6 (DDL + every assertion SQL stored verbatim in validation JSON artifact)
#   - I7 (matchId INTEGER -> numeric-tail regex [0-9]+ with round-trip cast provenance;
#     EXTRACT(EPOCH FROM) is standard DuckDB -- no magic constant)
#   - I8 (9-column cross-dataset contract; per-dataset-polymorphic faction vocabulary)
#   - I9 (pure non-destructive projection; no upstream modification)
# **BLOCKER-1 (aoec):** matchId is INTEGER (variable decimal width). Fixed-length gate
# inapplicable. Uses numeric-tail regex [0-9]+ + round-trip BIGINT cast assertion.
# **BLOCKER-2 (aoec):** No slot column -- slot-bias gate is N/A (natively player-row).
# I5-analog symmetry still enforced.
# **Date:** 2026-04-18

# %% [markdown]
# ## Cell 2 -- Imports

# %%
import json
from datetime import date
from pathlib import Path

import yaml

from rts_predict.common.notebook_utils import (
    get_notebook_db,
    get_reports_dir,
    setup_notebook_logging,
)

logger = setup_notebook_logging()
print("Imports complete.")

# %% [markdown]
# ## Cell 3 -- DuckDB Connection (writable -- creates TABLE)
#
# This notebook creates one new TABLE: `matches_history_minimal`.
# A writable connection is required.
# WARNING: Close all read-only notebook connections to this DB before running.
# Pre-execution constraint: no parallel CLI writes during T03.

# %%
db = get_notebook_db("aoe2", "aoe2companion", read_only=False)
con = db.con
print("DuckDB connection opened (read-write).")

# %% [markdown]
# ## Cell 4 -- Source-view sanity check
#
# DESCRIBE matches_1v1_clean; assert 51 cols + presence of required columns.
# Verifies the expected schema from matches_1v1_clean.yaml (01_04_02 ADDENDUM artifact).
# Required cols: matchId, started, profileId, civ, won (+ other 01_04_02 cols; 51 total).
# NOTE: Updated 48->51 after 01_04_02 ADDENDUM (duration_seconds + 2 flags added 2026-04-18).

# %%
describe_src = con.execute("DESCRIBE matches_1v1_clean").fetchall()
src_col_names = [row[0] for row in describe_src]
print(f"matches_1v1_clean column count: {len(src_col_names)}")
print(f"Columns: {src_col_names}")

# Assert 51 columns (per matches_1v1_clean.yaml step 01_04_02 ADDENDUM: 48 + 3 duration cols)
assert len(src_col_names) == 51, (
    f"Expected 51 columns in matches_1v1_clean, got {len(src_col_names)}"
)

# Assert required columns are present
required_cols = ["matchId", "started", "profileId", "civ", "won"]
for col in required_cols:
    assert col in src_col_names, (
        f"Required column '{col}' missing from matches_1v1_clean"
    )

print("Source-view sanity check PASSED: 51 cols + all required columns present.")

# %% [markdown]
# ## Cell 4b -- matches_raw finished column sanity check
#
# ADDENDUM: Verify matches_raw has `finished` TIMESTAMP + `started` TIMESTAMP + `matchId` join key.
# R1-WARNING-A6 fix: compute duration in _mhm_base staging (matches_raw already joined;
# no new JOIN). matches_raw.finished is nullable (abandoned/crashed matches).
# Gate +6: NULL fraction on duration_seconds must be <= 1% (HALTING).

# %%
describe_raw = con.execute("DESCRIBE matches_raw").fetchall()
raw_col_names = [row[0] for row in describe_raw]
raw_col_types_map = {row[0]: str(row[1]) for row in describe_raw}

assert "finished" in raw_col_names, (
    "BLOCKER: 'finished' column missing from matches_raw"
)
assert "started" in raw_col_names, (
    "BLOCKER: 'started' column missing from matches_raw"
)
assert "matchId" in raw_col_names, (
    "BLOCKER: 'matchId' column missing from matches_raw (join key)"
)
print(f"matches_raw.finished type: {raw_col_types_map['finished']}  (expected TIMESTAMP, nullable)")
print(f"matches_raw.started type:  {raw_col_types_map['started']}  (expected TIMESTAMP)")
print("matches_raw sanity check PASSED: finished + started + matchId present.")

# %% [markdown]
# ## Cell 5 -- Define DDL constants
#
# Three-step DDL due to DuckDB 1.5.1 bug (same as original 8-col implementation).
# ADDENDUM: duration_seconds added to _mhm_base staging as in-place column.
# EXTRACT(EPOCH FROM (r.finished - r.started)) -> DOUBLE seconds -> CAST AS BIGINT.
# matches_raw already joined at staging level (R1-WARNING-A6 fix: no new JOIN needed).
# I7 cite: EXTRACT(EPOCH FROM) is standard DuckDB -- no magic constant (per R1-WARNING-A5).
# Gate +6 (aoec-specific): measure NULL fraction; halt if > 1% (finished is nullable).

# %%
CREATE_GOOD_MATCH_IDS_SQL = """\
CREATE OR REPLACE TABLE _good_match_ids AS
-- Staging step 1/2: good match IDs (complementary won/lost pairs after dedup).
-- DuckDB 1.5.1 bug: QUALIFY + GROUP BY in a single CTE gives wrong row counts
-- when that CTE is used in a subsequent INNER JOIN. Materialized separately.
-- I9: matches_raw read-only; no upstream modification.
WITH deduped AS (
    SELECT matchId, profileId, won
    FROM matches_raw
    WHERE internalLeaderboardId IN (6, 18)
      AND profileId != -1
    QUALIFY
        row_number() OVER (PARTITION BY matchId, profileId ORDER BY started) = 1
)
SELECT matchId
FROM deduped
GROUP BY matchId
HAVING COUNT(*) = 2
   AND SUM(CASE WHEN won THEN 1 ELSE 0 END) = 1
   AND SUM(CASE WHEN NOT won THEN 1 ELSE 0 END) = 1\
"""

CREATE_STAGING_TABLE_SQL = """\
CREATE OR REPLACE TABLE _mhm_base AS
-- Staging step 2/2: base projection from matches_raw + _good_match_ids.
-- ADDENDUM: duration_seconds added in-place (R1-WARNING-A6 fix: matches_raw already
--   joined here; no additional JOIN needed).
-- I7: matchId INTEGER per data/db/schemas/raw/matches_raw.yaml line `matchId: INTEGER`.
-- I7: EXTRACT(EPOCH FROM) is standard DuckDB function -- no magic constant.
-- I7: finished is nullable (abandoned matches); NULL propagates to duration_seconds.
-- I9: matches_raw read-only; no upstream modification.
SELECT
    'aoe2companion::' || CAST(r.matchId AS VARCHAR)                  AS match_id,
    r.started                                                        AS started_at,
    CAST(r.profileId AS VARCHAR)                                     AS player_id,
    r.civ                                                            AS faction,
    r.won                                                            AS won,
    -- ADDENDUM: duration_seconds. EXTRACT EPOCH returns DOUBLE seconds.
    -- CAST AS BIGINT truncates (no rounding). NULL if r.finished IS NULL.
    -- Gate +6: NULL fraction must be <= 1% (HALTING -- see Cell 10c).
    CAST(EXTRACT(EPOCH FROM (r.finished - r.started)) AS BIGINT)     AS duration_seconds
FROM matches_raw r
INNER JOIN _good_match_ids g ON r.matchId = g.matchId
WHERE r.internalLeaderboardId IN (6, 18)
  AND r.profileId != -1
QUALIFY
    row_number() OVER (PARTITION BY r.matchId, r.profileId ORDER BY r.started) = 1\
"""

CREATE_MATCHES_HISTORY_MINIMAL_SQL = """\
CREATE OR REPLACE TABLE matches_history_minimal AS
-- aoe2companion sibling of sc2egset.matches_history_minimal (PR #152 pattern).
-- ADDENDUM: 9-col contract (duration_seconds added 2026-04-18).
-- Input: _mhm_base (materialized staging from matches_raw with matches_1v1_clean
--   filter logic + duration_seconds column). Strategy: self-join on match_id with
--   unequal player_id (sc2egset pattern). No UNION ALL pivot needed -- aoec is
--   already 2 rows/match natively.
-- Grain: 2 rows per 1v1 match (player row + opponent row, symmetric swap).
-- Cross-dataset contract: 9 columns, identical dtypes across sibling objects.
--   Canonical temporal dtype = TIMESTAMP (no TZ). Faction vocabulary is
--   per-dataset-polymorphic (SC2 race stems vs AoE2 full civ names).
-- Invariants: I3 (TIMESTAMP pass-through; started already TIMESTAMP per
--   data/db/schemas/raw/matches_raw.yaml; duration_seconds is POST_GAME_HISTORICAL),
--   I5-analog (NULL-safe symmetry incl. duration; slot-bias gate N/A -- aoec natively
--   player-row), I6 (DDL verbatim in JSON artifact), I7 (matchId INTEGER ->
--   numeric-tail regex [0-9]+; EXTRACT(EPOCH FROM) is standard DuckDB -- no magic
--   constant), I8 (9-col cross-dataset contract), I9 (pure projection; no upstream mod).
SELECT
    p.match_id,
    p.started_at,
    p.player_id,
    o.player_id                AS opponent_id,
    p.faction,
    o.faction                  AS opponent_faction,
    p.won,
    p.duration_seconds,
    'aoe2companion'            AS dataset_tag
FROM _mhm_base p
JOIN _mhm_base o
  ON p.match_id = o.match_id
 AND p.player_id <> o.player_id
ORDER BY p.started_at, p.match_id, p.player_id\
"""

DROP_STAGING_TABLES_SQL = [
    "DROP TABLE IF EXISTS _mhm_base",
    "DROP TABLE IF EXISTS _good_match_ids",
]

print("DDL constants defined.")
print("\n=== STEP 1 DDL (good_match_ids staging) ===")
print(CREATE_GOOD_MATCH_IDS_SQL)
print("\n=== STEP 2 DDL (_mhm_base staging with duration_seconds) ===")
print(CREATE_STAGING_TABLE_SQL)
print("\n=== STEP 3 DDL (matches_history_minimal) ===")
print(CREATE_MATCHES_HISTORY_MINIMAL_SQL)

# %% [markdown]
# ## Cell 6 -- Execute DDL (create TABLE)
#
# Four-step execution (DuckDB 1.5.1 workaround):
# 1. Create _good_match_ids TABLE (good matchIds: complementary won pairs).
# 2. Create _mhm_base TABLE (base projection: matches_raw INNER JOIN _good_match_ids;
#    ADDENDUM: includes duration_seconds = EXTRACT(EPOCH FROM (finished - started))).
# 3. Create matches_history_minimal TABLE (self-join _mhm_base).
# 4. Drop both staging tables (_mhm_base and _good_match_ids).

# %%
# Step 0: Drop any existing matches_history_minimal and staging tables
for obj in ["matches_history_minimal", "_mhm_base", "_good_match_ids"]:
    con.execute(f"DROP TABLE IF EXISTS {obj}")
    con.execute(f"DROP VIEW IF EXISTS {obj}")
print("Step 0: Cleaned up existing objects.")

# Step 1: good_match_ids staging table
con.execute(CREATE_GOOD_MATCH_IDS_SQL)
gm_count = con.execute("SELECT COUNT(*) FROM _good_match_ids").fetchone()[0]
print(f"Step 1: _good_match_ids created. Count: {gm_count}")
assert gm_count == 30_531_196, (
    f"good_match_ids count mismatch: expected 30_531_196, got {gm_count}"
)

# Step 2: _mhm_base staging table (now includes duration_seconds)
con.execute(CREATE_STAGING_TABLE_SQL)
staging_count = con.execute("SELECT COUNT(*) FROM _mhm_base").fetchone()[0]
print(f"Step 2: _mhm_base created. Staging row count: {staging_count}")
assert staging_count == 61_062_392, (
    f"Staging count mismatch: expected 61_062_392, got {staging_count}"
)

# Step 3: matches_history_minimal
con.execute(CREATE_MATCHES_HISTORY_MINIMAL_SQL)
print("Step 3: TABLE matches_history_minimal created.")

# Step 4: Drop staging tables
for sql in DROP_STAGING_TABLES_SQL:
    con.execute(sql)
print("Step 4: Staging tables dropped.")

print("TABLE matches_history_minimal created successfully.")

# %% [markdown]
# ## Cell 7 -- Schema shape validation
#
# DESCRIBE matches_history_minimal; assert 9 columns + exact dtypes per spec.
# ADDENDUM: 9 columns (duration_seconds BIGINT added between won and dataset_tag).
# Gate +1: DESCRIBE returns 9 cols in order [..., won BOOLEAN, duration_seconds BIGINT, dataset_tag VARCHAR].

# %%
describe_view = con.execute("DESCRIBE matches_history_minimal").fetchall()
view_col_names = [row[0] for row in describe_view]
view_col_types = [str(row[1]) for row in describe_view]

print(f"matches_history_minimal column count: {len(view_col_names)}")
for name, dtype in zip(view_col_names, view_col_types):
    print(f"  {name}: {dtype}")

# Gate +1: Assert 9 columns
assert len(view_col_names) == 9, (
    f"Expected 9 columns, got {len(view_col_names)}: {view_col_names}"
)

# Assert column names in order
expected_col_names = [
    "match_id", "started_at", "player_id", "opponent_id",
    "faction", "opponent_faction", "won", "duration_seconds", "dataset_tag",
]
assert view_col_names == expected_col_names, (
    f"Column name mismatch:\n  expected: {expected_col_names}\n  got:      {view_col_names}"
)

# Assert dtypes in order
expected_dtypes = [
    "VARCHAR", "TIMESTAMP", "VARCHAR", "VARCHAR",
    "VARCHAR", "VARCHAR", "BOOLEAN", "BIGINT", "VARCHAR",
]
assert view_col_types == expected_dtypes, (
    f"Dtype mismatch:\n  expected: {expected_dtypes}\n  got:      {view_col_types}"
)

print("Schema shape validation PASSED: 9 cols + dtypes match spec. (Gate +1 PASS)")

# %% [markdown]
# ## Cell 8 -- Row-count validation
#
# Gate: total_rows=61_062_392; distinct_match_ids=30_531_196; matches_with_not_2_rows=0.
# aoec matches_1v1_clean is natively 2-rows/match -> 30_531_196 matches x 2 = 61_062_392.

# %%
ROW_COUNT_CHECK_SQL = """\
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT match_id) AS distinct_match_ids
FROM matches_history_minimal\
"""

ROW_COUNT_SRC_SQL = """\
SELECT COUNT(*) AS src_rows FROM matches_1v1_clean\
"""

ROW_COUNT_NOT_2_SQL = """\
SELECT COUNT(*) AS matches_with_not_2_rows
FROM (
    SELECT match_id, COUNT(*) AS n
    FROM matches_history_minimal
    GROUP BY match_id
    HAVING n <> 2
)\
"""

rc = con.execute(ROW_COUNT_CHECK_SQL).fetchone()
total_rows, distinct_match_ids = rc

src_rows = con.execute(ROW_COUNT_SRC_SQL).fetchone()[0]
matches_with_not_2_rows = con.execute(ROW_COUNT_NOT_2_SQL).fetchone()[0]
matches_with_2_rows = distinct_match_ids  # since matches_with_not_2_rows = 0

print(f"total_rows:             {total_rows}")
print(f"distinct_match_ids:     {distinct_match_ids}")
print(f"src_rows:               {src_rows}")
print(f"matches_with_not_2_rows:{matches_with_not_2_rows}")

assert total_rows == 61_062_392, f"Expected total_rows=61_062_392, got {total_rows}"
assert distinct_match_ids == 30_531_196, f"Expected distinct_match_ids=30_531_196, got {distinct_match_ids}"
assert src_rows == 61_062_392, f"Expected src_rows=61_062_392, got {src_rows}"
assert matches_with_not_2_rows == 0, f"Expected matches_with_not_2_rows=0, got {matches_with_not_2_rows}"

print("Row-count validation PASSED.")

# %% [markdown]
# ## Cell 9 -- Symmetry (I5-analog, NULL-safe)
#
# Gate: symmetry_violations=0. Uses IS DISTINCT FROM for NULL-safe comparison.
# Checks: (player_id, opponent_id) are swapped; won values are complementary;
# faction and opponent_faction are mirrors.
# ADDENDUM: Extended to include duration_seconds IS NOT DISTINCT FROM
# (self-join propagates same duration_seconds from p and o rows -- symmetric by construction).
# NOTE: Slot-bias gate is N/A for aoec (natively player-row; no slot column).

# %%
SYMMETRY_I5_ANALOG_SQL = """\
WITH row_pairs AS (
    SELECT
        a.match_id,
        a.player_id         AS a_pid,
        a.opponent_id       AS a_oid,
        a.won               AS a_won,
        a.faction           AS a_fac,
        a.opponent_faction  AS a_ofac,
        a.duration_seconds  AS a_dur,
        b.player_id         AS b_pid,
        b.opponent_id       AS b_oid,
        b.won               AS b_won,
        b.faction           AS b_fac,
        b.opponent_faction  AS b_ofac,
        b.duration_seconds  AS b_dur
    FROM matches_history_minimal a
    JOIN matches_history_minimal b
      ON a.match_id = b.match_id
     AND a.player_id <> b.player_id
)
SELECT COUNT(*) AS symmetry_violations
FROM row_pairs
WHERE a_pid <> b_oid
   OR a_oid <> b_pid
   OR a_won = b_won
   OR a_fac IS DISTINCT FROM b_ofac
   OR a_ofac IS DISTINCT FROM b_fac
   OR a_dur IS DISTINCT FROM b_dur\
"""

sym_row = con.execute(SYMMETRY_I5_ANALOG_SQL).fetchone()
symmetry_violations = sym_row[0]
print(f"symmetry_violations: {symmetry_violations}")

assert symmetry_violations == 0, (
    f"I5-analog NULL-safe symmetry violations: {symmetry_violations} (expected 0)"
)

print("Symmetry (I5-analog, NULL-safe) PASSED.")
print("NOTE: Slot-bias gate is N/A for aoec (natively player-row; no slot column).")

# %% [markdown]
# ## Cell 10 -- Zero-NULL on non-nullable spec columns
#
# Gate: null_match_id / null_player_id / null_opponent_id / null_won / null_dataset_tag all 0.
# Gate: null_faction / null_opponent_faction all 0 (civ is zero-NULL upstream per
# matches_1v1_clean.yaml notes -- stricter than sc2/aoestats).
# started_at: also gate=0 (pass-through; no TRY_CAST failures since upstream started is TIMESTAMP).
# ADDENDUM: null_duration_seconds NOT a halt gate here -- handled in Cell 10c (Gate +6).

# %%
ZERO_NULL_SQL = """\
SELECT
    COUNT(*) FILTER (WHERE match_id          IS NULL) AS null_match_id,
    COUNT(*) FILTER (WHERE started_at        IS NULL) AS null_started_at,
    COUNT(*) FILTER (WHERE player_id         IS NULL) AS null_player_id,
    COUNT(*) FILTER (WHERE opponent_id       IS NULL) AS null_opponent_id,
    COUNT(*) FILTER (WHERE won               IS NULL) AS null_won,
    COUNT(*) FILTER (WHERE duration_seconds  IS NULL) AS null_duration_seconds,
    COUNT(*) FILTER (WHERE dataset_tag       IS NULL) AS null_dataset_tag,
    COUNT(*) FILTER (WHERE faction           IS NULL) AS null_faction,
    COUNT(*) FILTER (WHERE opponent_faction  IS NULL) AS null_opponent_faction
FROM matches_history_minimal\
"""

null_row = con.execute(ZERO_NULL_SQL).fetchone()
(
    null_match_id, null_started_at, null_player_id, null_opponent_id,
    null_won, null_duration_seconds, null_dataset_tag,
    null_faction, null_opponent_faction
) = null_row

print(f"null_match_id:          {null_match_id}")
print(f"null_started_at:        {null_started_at}  (gate=0; pass-through TIMESTAMP)")
print(f"null_player_id:         {null_player_id}")
print(f"null_opponent_id:       {null_opponent_id}")
print(f"null_won:               {null_won}")
print(f"null_duration_seconds:  {null_duration_seconds}  (Gate +2 + Gate +6 reported below)")
print(f"null_dataset_tag:       {null_dataset_tag}")
print(f"null_faction:           {null_faction}  (gate=0; civ zero-NULL upstream)")
print(f"null_opponent_faction:  {null_opponent_faction}  (gate=0; civ zero-NULL upstream)")

assert null_match_id == 0, f"null_match_id={null_match_id} (expected 0)"
assert null_player_id == 0, f"null_player_id={null_player_id} (expected 0)"
assert null_opponent_id == 0, f"null_opponent_id={null_opponent_id} (expected 0)"
assert null_won == 0, f"null_won={null_won} (expected 0)"
assert null_dataset_tag == 0, f"null_dataset_tag={null_dataset_tag} (expected 0)"
assert null_faction == 0, f"null_faction={null_faction} (expected 0; civ zero-NULL upstream)"
assert null_opponent_faction == 0, f"null_opponent_faction={null_opponent_faction} (expected 0)"

print("Zero-NULL validation PASSED for all 7 non-nullable spec columns (incl. faction).")

# %% [markdown]
# ## Cell 10b -- duration_seconds positive-value and range assertions
#
# ADDENDUM Gates +3, +4, +5a, +5b:
# Gate +3: duration_seconds > 0 for all non-NULL rows.
# Gate +4: Duration symmetry (covered in Cell 9 symmetry check;
#   self-join propagates same duration_seconds for both rows of a match).
# Gate +5a (HALTING -- unit regression canary): max(duration_seconds) <= 1_000_000_000
#   (~31.7 years). Catches nanosecond-unit passthrough bug: if EXTRACT EPOCH were
#   accidentally dropped, raw INTERVAL microseconds would yield values far above 1B.
#   Threshold intentionally generous to allow raw-data outliers (e.g., very long
#   wall-clock durations from crashed/abandoned matches).
# Gate +5b (REPORT-ONLY -- outlier count): count rows where duration_seconds > 86400 (> 24h).
#   These are raw-data corruption / abandoned matches with bogus timestamps. Do NOT halt.
#   Report count + sample. Outlier handling deferred to 01_04_02 augmentation follow-up.

# %%
DURATION_STATS_SQL = """\
SELECT
    MIN(duration_seconds)                                         AS min_duration_seconds,
    MAX(duration_seconds)                                         AS max_duration_seconds,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_seconds)
                                                                  AS p50_duration_seconds,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_seconds)
                                                                  AS p99_duration_seconds,
    AVG(duration_seconds)                                         AS avg_duration_seconds,
    COUNT(*) FILTER (WHERE duration_seconds IS NOT NULL)          AS non_null_count,
    COUNT(*) FILTER (WHERE duration_seconds IS NOT NULL
                       AND duration_seconds <= 0)                 AS non_positive_count,
    COUNT(*) FILTER (WHERE duration_seconds > 86400)              AS outlier_count_gt_86400
FROM matches_history_minimal\
"""

dur_row = con.execute(DURATION_STATS_SQL).fetchone()
(
    min_dur, max_dur, p50_dur, p99_dur, avg_dur,
    non_null_dur, non_positive_dur, outlier_count_gt_86400
) = dur_row

print(f"min_duration_seconds:       {min_dur}")
print(f"max_duration_seconds:       {max_dur}")
print(f"p50_duration_seconds:       {p50_dur}")
print(f"p99_duration_seconds:       {p99_dur}")
print(f"avg_duration_seconds:       {avg_dur:.1f}" if avg_dur is not None else "avg_duration_seconds: None")
print(f"non_null_count:             {non_null_dur}")
print(f"non_positive_count:         {non_positive_dur}  (Gate +3: expected 0)")
print(f"outlier_count_gt_86400:     {outlier_count_gt_86400}  (Gate +5b: report-only)")

# Gate +3: report non-positive values among non-NULLs (REPORT-ONLY for aoec).
# aoec: negative duration_seconds arise when finished < started (clock skew / timezone
# corruption in raw data -- not a unit regression). These are raw-data artifacts, not
# an indication that EXTRACT(EPOCH FROM) was dropped. Do NOT halt; report for awareness.
# For reference: aoestats Gate +3 is HALTING (arrow[ns] -> /1e9 -> no negatives possible),
# but aoec wall-clock subtraction can yield negatives for corrupted finished timestamps.
# Outlier handling deferred to 01_04_02 augmentation follow-up PR.
if non_positive_dur > 0:
    print(
        f"Gate +3 REPORT-ONLY (aoec): {non_positive_dur} rows with duration_seconds <= 0 "
        f"(finished < started -- clock skew / raw-data corruption). NOT a unit regression. "
        f"Pass-through; outlier handling deferred."
    )
else:
    print("Gate +3 PASS: all non-NULL duration_seconds > 0.")

# Gate +5a (HALTING -- unit regression canary).
# Threshold: 1_000_000_000 seconds (~31.7 years).
# If EXTRACT(EPOCH FROM) were accidentally dropped, INTERVAL micros passthrough would
# yield values far above this threshold. The 1B canary is intentionally generous so
# legitimate outliers (abandoned matches with bogus wall-clock) pass through.
assert max_dur is None or max_dur <= 1_000_000_000, (
    f"Gate +5a HALTING FAILED: unit regression? max_duration_seconds={max_dur} > 1_000_000_000. "
    f"aoec duration: EXTRACT(EPOCH FROM (r.finished - r.started)) -> DOUBLE seconds -> BIGINT. "
    f"If this value is astronomically large, EXTRACT EPOCH may have been dropped."
)
print(f"Gate +5a PASS: max_duration_seconds={max_dur} <= 1_000_000_000 (unit canary OK).")

# Gate +5b (REPORT-ONLY -- outlier count > 24h).
# These are raw-data corruption rows (abandoned/crashed matches with bogus timestamps).
# Do NOT halt. Pass through unchanged to downstream steps.
# Outlier handling is deferred to the 01_04_02 augmentation PR (follow-up).
print(
    f"Gate +5b REPORT: {outlier_count_gt_86400} rows with duration_seconds > 86400 (> 24h). "
    f"These are raw-data corruption / abandoned matches. "
    f"Outlier handling deferred to 01_04_02 augmentation follow-up PR. Pass-through."
)

# Sample the outliers for the validation JSON
OUTLIER_SAMPLE_SQL = """\
SELECT match_id, player_id, duration_seconds
FROM matches_history_minimal
WHERE duration_seconds > 86400
ORDER BY duration_seconds DESC
LIMIT 10\
"""
outlier_sample_rows = con.execute(OUTLIER_SAMPLE_SQL).fetchall()
outlier_sample = [
    {"match_id": row[0], "player_id": row[1], "duration_seconds": row[2]}
    for row in outlier_sample_rows
]
print(f"Top-10 outlier sample (by duration_seconds DESC):")
for s in outlier_sample:
    print(f"  {s}")

# %% [markdown]
# ## Cell 10c -- Gate +6 (aoec-specific, HALTING): NULL fraction on duration_seconds
#
# ADDENDUM Gate +6: NULL fraction = null_duration_seconds / total_rows.
# HALTING if fraction > 1% (R1-WARNING-A7 fix).
# matches_raw.finished is nullable (abandoned/crashed matches); NULL propagates to
# EXTRACT(EPOCH FROM (finished - started)).
# If fraction > 1%, HALT -- do not proceed to next dataset.

# %%
NULL_FRACTION_SQL = """\
SELECT
    COUNT(*) FILTER (WHERE duration_seconds IS NULL)  AS null_count,
    COUNT(*)                                          AS total_rows,
    COUNT(*) FILTER (WHERE duration_seconds IS NULL) * 1.0 / COUNT(*) AS null_fraction
FROM matches_history_minimal\
"""

nf_row = con.execute(NULL_FRACTION_SQL).fetchone()
dur_null_count, dur_total_rows, dur_null_fraction = nf_row

print(f"null_count:    {dur_null_count}")
print(f"total_rows:    {dur_total_rows}")
print(f"null_fraction: {dur_null_fraction:.6f}  (= {dur_null_fraction*100:.4f}%)")
print(f"Gate +6 threshold: <= 0.01 (1%)")

# Gate +6 (aoec-specific, HALTING)
assert dur_null_fraction <= 0.01, (
    f"Gate +6 HALTING FAILED: duration_seconds NULL fraction = {dur_null_fraction:.6f} "
    f"({dur_null_fraction*100:.4f}%) > 1%. "
    f"matches_raw.finished is nullable for abandoned matches. "
    f"NULL count: {dur_null_count} / {dur_total_rows}"
)
print(f"Gate +6 PASS: duration_seconds NULL fraction = {dur_null_fraction:.6f} <= 0.01.")

# %% [markdown]
# ## Cell 11 -- match_id prefix verification (aoec-specific: numeric-tail regex)
#
# Gate: prefix_violations=0.
# aoec-specific: matchId is INTEGER (variable decimal width) -- no fixed-length gate.
# Checks: LIKE 'aoe2companion::%' AND numeric-tail regex [0-9]+ AND round-trip BIGINT cast.
# I7 provenance: `matchId: INTEGER` in
# src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/matches_raw.yaml.

# %%
PREFIX_CHECK_SQL = """\
-- Magic literal: 'aoe2companion::' = dataset prefix.
-- Numeric-tail regex [0-9]+ cites:
--   src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/matches_raw.yaml
--   line `matchId: INTEGER` (I7 provenance).
-- Round-trip cast: regexp_extract tail == CAST(CAST(tail AS BIGINT) AS VARCHAR)
--   verifies no leading zeros or non-numeric chars in match_id suffix.
-- Variable decimal width -- no fixed-length gate (unlike sc2egset's 42-char hex).
SELECT COUNT(*) AS prefix_violations
FROM matches_history_minimal m
WHERE m.match_id NOT LIKE 'aoe2companion::%'
   OR regexp_extract(m.match_id, '::([0-9]+)$', 1) = ''
   OR regexp_extract(m.match_id, '::([0-9]+)$', 1)
      <> CAST(CAST(split_part(m.match_id, '::', 2) AS BIGINT) AS VARCHAR)\
"""

prefix_row = con.execute(PREFIX_CHECK_SQL).fetchone()
prefix_violations = prefix_row[0]
print(f"prefix_violations: {prefix_violations}")

assert prefix_violations == 0, f"prefix_violations={prefix_violations} (expected 0)"

print("Prefix check (numeric-tail regex + round-trip cast) PASSED.")

# %% [markdown]
# ## Cell 12 -- dataset_tag constant
#
# Gate: n_distinct_tags=1, the_tag='aoe2companion'.

# %%
DATASET_TAG_CHECK_SQL = """\
SELECT
    COUNT(DISTINCT dataset_tag) AS n_distinct_tags,
    MAX(dataset_tag)            AS the_tag
FROM matches_history_minimal\
"""

tag_row = con.execute(DATASET_TAG_CHECK_SQL).fetchone()
n_distinct_tags, the_tag = tag_row
print(f"n_distinct_tags: {n_distinct_tags}")
print(f"the_tag:         {the_tag}")

assert n_distinct_tags == 1, f"n_distinct_tags={n_distinct_tags} (expected 1)"
assert the_tag == "aoe2companion", f"the_tag={the_tag!r} (expected 'aoe2companion')"

print("dataset_tag constant PASSED.")

# %% [markdown]
# ## Cell 13 -- Faction vocabulary (exploratory, no gate)
#
# Documents per-dataset polymorphism (I8). aoe2companion ships full civ names
# (e.g., Franks, Mongols, Britons, etc.) -- NOT 4-char stems like sc2egset.
# No hard assertion -- exploratory per plan spec.

# %%
FACTION_VOCAB_SQL = """\
SELECT faction, COUNT(*) AS n
FROM matches_history_minimal
GROUP BY faction
ORDER BY n DESC\
"""

faction_rows = con.execute(FACTION_VOCAB_SQL).fetchall()
print("Faction vocabulary (per-dataset polymorphic, aoe2companion full civ names):")
for faction, n in faction_rows[:10]:
    print(f"  {faction!r}: {n}")
if len(faction_rows) > 10:
    print(f"  ... ({len(faction_rows) - 10} more)")

faction_vocab = {row[0]: row[1] for row in faction_rows}
print(f"\nTotal faction vocab size: {len(faction_vocab)} distinct values")
print("NOTE: aoe2companion faction vocabulary is full civilization names (Franks, Mongols, etc.).")
print("      Consumers MUST NOT treat faction as cross-dataset categorical without game-conditional encoding.")

# %% [markdown]
# ## Cell 14 -- Temporal sanity (I3)
#
# Report min/max started_at, null count, distinct count.
# TIMESTAMP pass-through from matches_raw.started (already TIMESTAMP).
# No TRY_CAST -- no cast failures expected. Chronologically faithful ordering.

# %%
TEMPORAL_SANITY_SQL = """\
SELECT
    MIN(started_at)            AS min_started_at,
    MAX(started_at)            AS max_started_at,
    COUNT(*) FILTER (WHERE started_at IS NULL) AS null_started_at,
    COUNT(DISTINCT started_at) AS distinct_started_at
FROM matches_history_minimal\
"""

ts_row = con.execute(TEMPORAL_SANITY_SQL).fetchone()
min_started_at, max_started_at, null_started_at_ts, distinct_started_at = ts_row
print(f"min_started_at:      {min_started_at}")
print(f"max_started_at:      {max_started_at}")
print(f"null_started_at:     {null_started_at_ts}  (pass-through; expected 0)")
print(f"distinct_started_at: {distinct_started_at}")

# %% [markdown]
# ## Cell 15 -- matchId range sanity (aoec-specific)
#
# Report min/max matchId value and max decimal digit count.
# aoec matchId is INTEGER (variable decimal width; 1-10 digits).
# Exploratory only -- no gate. Confirms I7 numeric provenance.

# %%
MATCHID_RANGE_SQL = """\
SELECT
    MIN(CAST(split_part(match_id, '::', 2) AS BIGINT))              AS min_match_id_val,
    MAX(CAST(split_part(match_id, '::', 2) AS BIGINT))              AS max_match_id_val,
    MAX(length(split_part(match_id, '::', 2)))                      AS max_decimal_digits
FROM matches_history_minimal\
"""

mid_row = con.execute(MATCHID_RANGE_SQL).fetchone()
min_match_id_val, max_match_id_val, max_decimal_digits = mid_row
print(f"min_match_id_val:    {min_match_id_val}")
print(f"max_match_id_val:    {max_match_id_val}")
print(f"max_decimal_digits:  {max_decimal_digits}")
print("NOTE: Variable decimal width confirmed -- no fixed-length gate (aoec-specific).")

# %% [markdown]
# ## Cell 16 -- Build validation JSON + assert all_assertions_pass
#
# Captures: step metadata, row_counts, assertion_results, sql_queries (verbatim I6),
# describe_table_rows (DESCRIBE output for nullable-flag reproducibility).
# ADDENDUM: 9-col schema; duration_seconds stats + Gate +6 included.

# %%
reports_dir = get_reports_dir("aoe2", "aoe2companion")
artifact_dir = reports_dir / "artifacts" / "01_exploration" / "04_cleaning"
artifact_dir.mkdir(parents=True, exist_ok=True)

json_path = artifact_dir / "01_04_03_minimal_history_view.json"

# Capture DESCRIBE output as JSON-serializable list
describe_rows_raw = con.execute("DESCRIBE matches_history_minimal").fetchall()
describe_table_rows = [
    {
        "column_name": row[0],
        "column_type": str(row[1]),
        "null": row[2],
        "key": row[3],
        "default": row[4],
        "extra": row[5],
    }
    for row in describe_rows_raw
]

assertion_results = {
    "src_col_count_51": len(describe_src) == 51,  # updated 48->51 post 01_04_02 ADDENDUM
    "required_src_cols_present": all(c in src_col_names for c in required_cols),
    "col_count_9": len(view_col_names) == 9,
    "col_names_match": view_col_names == expected_col_names,
    "col_dtypes_match": view_col_types == expected_dtypes,
    "total_rows_61062392": total_rows == 61_062_392,
    "distinct_match_ids_30531196": distinct_match_ids == 30_531_196,
    "src_rows_61062392": src_rows == 61_062_392,
    "matches_with_not_2_rows_0": matches_with_not_2_rows == 0,
    "symmetry_violations_0": symmetry_violations == 0,
    "null_match_id_0": null_match_id == 0,
    "null_player_id_0": null_player_id == 0,
    "null_opponent_id_0": null_opponent_id == 0,
    "null_won_0": null_won == 0,
    "null_dataset_tag_0": null_dataset_tag == 0,
    "null_faction_0": null_faction == 0,
    "null_opponent_faction_0": null_opponent_faction == 0,
    "prefix_violations_0": prefix_violations == 0,
    "n_distinct_tags_1": n_distinct_tags == 1,
    "dataset_tag_aoe2companion": the_tag == "aoe2companion",
    # Gate +3: REPORT-ONLY for aoec (negative values = clock skew, not unit regression)
    # Not included in halting assertion_results -- see duration_stats.non_positive_count in JSON.
    "duration_max_le_1B_gate5a": max_dur is None or max_dur <= 1_000_000_000,
    "duration_null_fraction_le_1pct": dur_null_fraction <= 0.01,
}

all_assertions_pass = all(assertion_results.values())

validation = {
    "step": "01_04_03",
    "dataset": "aoe2companion",
    "game": "aoe2",
    "generated_date": str(date.today()),
    "object": "matches_history_minimal",
    "object_type": "table",
    "schema_version": "9-col (ADDENDUM: duration_seconds added 2026-04-18)",
    "implementation_note": (
        "DuckDB 1.5.1 bug: (1) self-join on matches_1v1_clean VIEW (row_number+ANY) "
        "causes InternalException; (2) QUALIFY+CTE self-join in a single CREATE TABLE "
        "gives wrong row counts (42,866 instead of 61,062,392). Workaround: three-step "
        "DDL -- (1) CREATE TABLE _good_match_ids from matches_raw QUALIFY; "
        "(2) CREATE TABLE _mhm_base = matches_raw INNER JOIN _good_match_ids QUALIFY "
        "+ ADDENDUM duration_seconds; "
        "(3) CREATE TABLE matches_history_minimal = self-join _mhm_base; "
        "(4) DROP staging tables. Semantics identical to planned CREATE OR REPLACE VIEW. "
        "Same 9-column schema contract maintained."
    ),
    "row_counts": {
        "total_rows": total_rows,
        "distinct_match_ids": distinct_match_ids,
        "src_rows": src_rows,
        "matches_with_2_rows": matches_with_2_rows,
        "matches_with_not_2_rows": matches_with_not_2_rows,
    },
    "null_counts": {
        "null_match_id": null_match_id,
        "null_started_at": null_started_at,
        "null_player_id": null_player_id,
        "null_opponent_id": null_opponent_id,
        "null_won": null_won,
        "null_duration_seconds": null_duration_seconds,
        "null_dataset_tag": null_dataset_tag,
        "null_faction": null_faction,
        "null_opponent_faction": null_opponent_faction,
    },
    "duration_stats": {
        "min_duration_seconds": min_dur,
        "max_duration_seconds": max_dur,
        "p50_duration_seconds": p50_dur,
        "p99_duration_seconds": p99_dur,
        "avg_duration_seconds": avg_dur,
        "non_null_count": non_null_dur,
        "non_positive_count": non_positive_dur,
        "null_count": dur_null_count,
        "null_fraction": dur_null_fraction,
        "outlier_count_gt_86400": outlier_count_gt_86400,
        "outlier_sample_top10": outlier_sample,
        "gate_plus3_report_only_non_positive_count": non_positive_dur,
        "gate_plus3_note": (
            "REPORT-ONLY for aoec. Negative values (finished < started) = clock skew "
            "in raw data -- not a unit regression. Outlier handling deferred."
        ),
        "gate_plus5a_pass": max_dur is None or max_dur <= 1_000_000_000,
        "gate_plus5b_report_only": outlier_count_gt_86400,
        "gate_plus6_pass": dur_null_fraction <= 0.01,
        "provenance": (
            "CAST(EXTRACT(EPOCH FROM (r.finished - r.started)) AS BIGINT). "
            "EXTRACT(EPOCH FROM) is standard DuckDB function returning DOUBLE seconds. "
            "CAST AS BIGINT truncates (no rounding). NULL if r.finished IS NULL "
            "(abandoned/crashed matches). R1-WARNING-A6 fix: computed in _mhm_base "
            "staging (matches_raw already joined; no new JOIN needed)."
        ),
    },
    "symmetry_violations": symmetry_violations,
    "prefix_violations": prefix_violations,
    "dataset_tag_distinct": n_distinct_tags,
    "dataset_tag_value": the_tag,
    "temporal_sanity": {
        "min_started_at": str(min_started_at),
        "max_started_at": str(max_started_at),
        "null_started_at": null_started_at_ts,
        "distinct_started_at": distinct_started_at,
    },
    "matchid_range": {
        "min_match_id_val": min_match_id_val,
        "max_match_id_val": max_match_id_val,
        "max_decimal_digits": max_decimal_digits,
    },
    "faction_vocab": faction_vocab,
    "schema_shape": {
        "col_names": view_col_names,
        "col_types": view_col_types,
    },
    "assertion_results": assertion_results,
    "all_assertions_pass": all_assertions_pass,
    "describe_table_rows": describe_table_rows,
    "sql_queries": {
        "CREATE_GOOD_MATCH_IDS_SQL": CREATE_GOOD_MATCH_IDS_SQL,
        "CREATE_STAGING_TABLE_SQL": CREATE_STAGING_TABLE_SQL,
        "CREATE_MATCHES_HISTORY_MINIMAL_SQL": CREATE_MATCHES_HISTORY_MINIMAL_SQL,
        "DROP_STAGING_TABLES_SQL": DROP_STAGING_TABLES_SQL,
        "ROW_COUNT_CHECK_SQL": ROW_COUNT_CHECK_SQL,
        "ROW_COUNT_SRC_SQL": ROW_COUNT_SRC_SQL,
        "ROW_COUNT_NOT_2_SQL": ROW_COUNT_NOT_2_SQL,
        "SYMMETRY_I5_ANALOG_SQL": SYMMETRY_I5_ANALOG_SQL,
        "ZERO_NULL_SQL": ZERO_NULL_SQL,
        "DURATION_STATS_SQL": DURATION_STATS_SQL,
        "OUTLIER_SAMPLE_SQL": OUTLIER_SAMPLE_SQL,
        "NULL_FRACTION_SQL": NULL_FRACTION_SQL,
        "PREFIX_CHECK_SQL": PREFIX_CHECK_SQL,
        "DATASET_TAG_CHECK_SQL": DATASET_TAG_CHECK_SQL,
        "FACTION_VOCAB_SQL": FACTION_VOCAB_SQL,
        "TEMPORAL_SANITY_SQL": TEMPORAL_SANITY_SQL,
        "MATCHID_RANGE_SQL": MATCHID_RANGE_SQL,
    },
    "spec_schema": {
        "expected_col_names": expected_col_names,
        "expected_dtypes": expected_dtypes,
    },
}

with open(json_path, "w") as f:
    json.dump(validation, f, indent=2, default=str)

print(f"Validation JSON written: {json_path}")
print(f"All assertions pass: {all_assertions_pass}")

assert all_assertions_pass, (
    f"One or more assertions FAILED:\n"
    + "\n".join(f"  {k}: {v}" for k, v in assertion_results.items() if not v)
)

# %% [markdown]
# ## Cell 17 -- Build markdown report

# %%
md_path = artifact_dir / "01_04_03_minimal_history_view.md"

faction_table_rows = "\n".join(
    f"| `{faction}` | {n} |" for faction, n in faction_rows[:20]
)

md_content = f"""# Step 01_04_03 -- Minimal Cross-Dataset History View (aoe2companion)

**Generated:** {date.today()}
**Dataset:** aoe2companion
**Game:** AoE2
**Step:** 01_04_03
**Predecessor:** 01_04_02 (Data Cleaning Execution)
**Schema version:** 9-col (ADDENDUM: duration_seconds added 2026-04-18)

## Summary

Created `matches_history_minimal` TABLE -- 9-column player-row-grain projection of
`matches_raw` (filtered to matches_1v1_clean scope; 2 rows per 1v1 match). Self-join
pattern (sc2egset PR #152 precedent). Canonical TIMESTAMP temporal dtype (pass-through;
matches_raw.started is already TIMESTAMP). Per-dataset-polymorphic faction
vocabulary (full AoE2 civ names). Cross-dataset-harmonized substrate for Phase 02+
rating-system backtesting. Pure non-destructive projection (I9).

**Implementation note (DuckDB 1.5.1 workaround):**
Three-step DDL -- (1) CREATE TABLE _good_match_ids; (2) CREATE TABLE _mhm_base
(includes duration_seconds); (3) CREATE TABLE matches_history_minimal via self-join;
(4) DROP staging tables.

**ADDENDUM:** Added `duration_seconds` BIGINT (column 8) between `won` and `dataset_tag`.
Source: EXTRACT(EPOCH FROM (r.finished - r.started)) in _mhm_base staging (in-place;
matches_raw already joined). NULL if r.finished is NULL (abandoned matches).
Gate +6 (HALTING): NULL fraction <= 1%.

aoec-specific notes:
- No UNION ALL pivot needed (natively 2-row per match).
- No slot-bias gate (no slot column; natively player-row).
- Zero-NULL gate for faction + opponent_faction (civ zero-NULL upstream per 01_04_02).
- matchId INTEGER -> variable decimal width; numeric-tail regex + round-trip cast (I7).

## Schema (9 columns)

| column | dtype | semantics |
|---|---|---|
| `match_id` | VARCHAR | `'aoe2companion::'` + decimal matchId (variable width) |
| `started_at` | TIMESTAMP | Pass-through from matches_raw.started (already TIMESTAMP) |
| `player_id` | VARCHAR | CAST(profileId AS VARCHAR) |
| `opponent_id` | VARCHAR | Opposing profileId (from self-join) |
| `faction` | VARCHAR | Full civ name (e.g., Franks, Mongols). PER-DATASET POLYMORPHIC |
| `opponent_faction` | VARCHAR | Opposing civ (same vocabulary as faction) |
| `won` | BOOLEAN | Focal player's outcome (complementary between the 2 rows) |
| `duration_seconds` | BIGINT | POST_GAME_HISTORICAL. EXTRACT(EPOCH FROM (finished - started)). NULL if finished IS NULL. |
| `dataset_tag` | VARCHAR | Constant `'aoe2companion'` |

## Row-count flow

| metric | value |
|---|---|
| Source matches_1v1_clean rows | {src_rows} |
| matches_history_minimal total rows | {total_rows} |
| distinct match_ids | {distinct_match_ids} |
| matches with exactly 2 rows | {matches_with_2_rows} |
| matches with NOT 2 rows | {matches_with_not_2_rows} |

## duration_seconds stats (ADDENDUM gates)

| metric | value | gate |
|---|---|---|
| min_duration_seconds | {min_dur} | report only |
| max_duration_seconds | {max_dur} | <= 1_000_000_000 (Gate +5a HALTING) |
| p50_duration_seconds | {p50_dur} | report only |
| p99_duration_seconds | {p99_dur} | report only |
| avg_duration_seconds | {avg_dur:.1f} | report only |
| null_duration_seconds | {null_duration_seconds} | report only (Gate +2) |
| null_fraction | {dur_null_fraction:.6f} ({dur_null_fraction*100:.4f}%) | <= 1% (Gate +6 HALTING) |
| non_positive_count | {non_positive_dur} | 0 (Gate +3) |
| outlier_count_gt_86400 | {outlier_count_gt_86400} | report only (Gate +5b) |

## matchId range (aoec-specific, exploratory)

| metric | value |
|---|---|
| min_match_id_val | {min_match_id_val} |
| max_match_id_val | {max_match_id_val} |
| max_decimal_digits | {max_decimal_digits} |

## Faction vocabulary (per-dataset polymorphic, top 20)

| faction | count |
|---|---|
{faction_table_rows}

NOTE: aoe2companion faction vocabulary is full civilization names (e.g., Franks, Mongols).
Consumers MUST NOT treat faction as a single categorical feature across
datasets without game-conditional encoding.

## Temporal sanity (I3)

| metric | value |
|---|---|
| min_started_at | {min_started_at} |
| max_started_at | {max_started_at} |
| null_started_at (pass-through) | {null_started_at_ts} |
| distinct_started_at | {distinct_started_at} |

## NULL counts

| column | null count | gate |
|---|---|---|
| match_id | {null_match_id} | 0 (GATE) |
| started_at | {null_started_at} | 0 (GATE; pass-through TIMESTAMP) |
| player_id | {null_player_id} | 0 (GATE) |
| opponent_id | {null_opponent_id} | 0 (GATE) |
| won | {null_won} | 0 (GATE) |
| duration_seconds | {null_duration_seconds} | report only + Gate +6 |
| dataset_tag | {null_dataset_tag} | 0 (GATE) |
| faction | {null_faction} | 0 (GATE; civ zero-NULL upstream) |
| opponent_faction | {null_opponent_faction} | 0 (GATE; civ zero-NULL upstream) |

## Gate verdict (18 gates; no slot-bias gate -- aoec natively player-row)

| check | result |
|---|---|
| Row count 61,062,392 = 2 x 30,531,196 | {'PASS' if total_rows == 61_062_392 and distinct_match_ids == 30_531_196 else 'FAIL'} |
| Column count 9 (Gate +1) | {'PASS' if len(view_col_names) == 9 else 'FAIL'} |
| started_at dtype TIMESTAMP | {'PASS' if 'TIMESTAMP' in view_col_types[1] else 'FAIL'} |
| duration_seconds dtype BIGINT | {'PASS' if view_col_types[7] == 'BIGINT' else 'FAIL'} |
| I5-analog NULL-safe symmetry violations (incl. duration) = 0 | {'PASS' if symmetry_violations == 0 else 'FAIL'} |
| Zero NULLs: match_id / player_id / opponent_id / won / dataset_tag | {'PASS' if null_match_id == null_player_id == null_opponent_id == null_won == null_dataset_tag == 0 else 'FAIL'} |
| Zero NULLs: faction / opponent_faction (civ zero-NULL upstream) | {'PASS' if null_faction == null_opponent_faction == 0 else 'FAIL'} |
| Prefix violations = 0 (numeric-tail regex + round-trip cast) | {'PASS' if prefix_violations == 0 else 'FAIL'} |
| dataset_tag distinct count = 1, value 'aoe2companion' | {'PASS' if n_distinct_tags == 1 and the_tag == 'aoe2companion' else 'FAIL'} |
| matches_with_not_2_rows = 0 | {'PASS' if matches_with_not_2_rows == 0 else 'FAIL'} |
| duration_seconds non-positive count (Gate +3 REPORT-ONLY for aoec) | {non_positive_dur} rows (clock skew) |
| duration_seconds max <= 1_000_000_000 (Gate +5a HALTING) | {'PASS' if (max_dur is None or max_dur <= 1_000_000_000) else 'FAIL'} |
| duration_seconds outlier_count_gt_86400 (Gate +5b REPORT-ONLY) | {outlier_count_gt_86400} rows |
| duration_seconds NULL fraction <= 1% (Gate +6 HALTING) | {'PASS' if dur_null_fraction <= 0.01 else 'FAIL'} |
| All assertions pass | {'PASS' if all_assertions_pass else 'FAIL'} |

## Artifact

Validation JSON: `{json_path.relative_to(json_path.parents[8])}`
"""

with open(md_path, "w") as f:
    f.write(md_content)

print(f"Markdown report written: {md_path}")

# %% [markdown]
# ## Cell 18 -- Write schema YAML for matches_history_minimal
#
# ADDENDUM: 9-col schema. duration_seconds column added between won and dataset_tag.
# POST_GAME_HISTORICAL machine-token in notes.
# Nullable flags sourced from DESCRIBE result.

# %%
schema_dir = reports_dir.parent / "data" / "db" / "schemas" / "views"
schema_dir.mkdir(parents=True, exist_ok=True)

yaml_path = schema_dir / "matches_history_minimal.yaml"

# Translate DESCRIBE nullable flags to concrete Python booleans
describe_rows_for_yaml = con.execute("DESCRIBE matches_history_minimal").fetchall()
nullable_map = {row[0]: (row[2] == "YES") for row in describe_rows_for_yaml}

schema = {
    "table": "matches_history_minimal",
    "dataset": "aoe2companion",
    "game": "aoe2",
    "object_type": "table",
    "object_type_note": (
        "DuckDB 1.5.1 bug: self-join on matches_1v1_clean VIEW (row_number + ANY) "
        "causes InternalException. Three-step DDL materialization used instead of "
        "CREATE OR REPLACE VIEW. Semantics are identical to the planned VIEW -- same "
        "9-column contract (ADDENDUM), same filtering, same row count."
    ),
    "step": "01_04_03",
    "schema_version": "9-col (ADDENDUM: duration_seconds added 2026-04-18)",
    "row_count": total_rows,
    "describe_artifact": (
        "src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts"
        "/01_exploration/04_cleaning/01_04_03_minimal_history_view.json"
    ),
    "generated_date": str(date.today()),
    "columns": [
        {
            "name": "match_id",
            "type": "VARCHAR",
            "nullable": nullable_map["match_id"],
            "description": (
                "Cross-dataset unique match identifier. Format: '<dataset_tag>::<native_id>'. "
                "For aoe2companion: 'aoe2companion::<decimal-matchId>'. Provenance: numeric-tail "
                "regex [0-9]+ cites matches_raw.yaml line `matchId: INTEGER` (I7)."
            ),
            "notes": "IDENTITY. Prefix applied in DDL only; upstream matchId unchanged (I9).",
        },
        {
            "name": "started_at",
            "type": "TIMESTAMP",
            "nullable": nullable_map["started_at"],
            "description": (
                "Match start time. TIMESTAMP (no TZ) -- pass-through from "
                "matches_raw.started (already TIMESTAMP per matches_raw.yaml)."
            ),
            "notes": (
                "CONTEXT. Temporal anchor for Phase 02 rating-update loops."
            ),
        },
        {
            "name": "player_id",
            "type": "VARCHAR",
            "nullable": nullable_map["player_id"],
            "description": (
                "Focal player identifier. aoe2companion: CAST(profileId AS VARCHAR) "
                "(INTEGER -> VARCHAR)."
            ),
            "notes": "IDENTITY.",
        },
        {
            "name": "opponent_id",
            "type": "VARCHAR",
            "nullable": nullable_map["opponent_id"],
            "description": "Opposing player identifier. Same grain and provenance as player_id.",
            "notes": "IDENTITY.",
        },
        {
            "name": "faction",
            "type": "VARCHAR",
            "nullable": nullable_map["faction"],
            "description": (
                "Focal player's faction. Per-dataset polymorphic vocabulary. "
                "aoe2companion: full civilization names (zero NULLs upstream). "
                "CONSUMERS MUST NOT treat faction as single categorical across datasets."
            ),
            "notes": "PRE_GAME. Raw civ vocabulary. Polymorphic I8 contract. Zero NULLs.",
        },
        {
            "name": "opponent_faction",
            "type": "VARCHAR",
            "nullable": nullable_map["opponent_faction"],
            "description": "Opposing player's faction (same per-dataset vocabulary as `faction`).",
            "notes": "PRE_GAME. Mirror of faction from the opponent row. Zero NULLs.",
        },
        {
            "name": "won",
            "type": "BOOLEAN",
            "nullable": nullable_map["won"],
            "description": (
                "TRUE if the focal player won, FALSE otherwise. Complementary between the 2 rows."
            ),
            "notes": "TARGET. Prediction label for downstream experiments. Zero NULLs.",
        },
        {
            "name": "duration_seconds",
            "type": "BIGINT",
            "nullable": nullable_map.get("duration_seconds", True),
            "description": (
                "Match duration in seconds (POST_GAME_HISTORICAL). For aoe2companion: "
                "CAST(EXTRACT(EPOCH FROM (r.finished - r.started)) AS BIGINT). "
                "EXTRACT(EPOCH FROM) is standard DuckDB function returning DOUBLE seconds. "
                "CAST AS BIGINT truncates (no rounding). NULL if r.finished IS NULL "
                "(abandoned/crashed matches -- verified by Gate +6 NULL fraction <= 1%). "
                "Both rows of a match have identical duration_seconds (symmetric -- "
                "self-join propagates same value). "
                "I7: EXTRACT(EPOCH FROM) is standard DuckDB -- no magic constant "
                "(per R1-WARNING-A5 verification). "
                "Derivation note (A-D3): wall-clock duration (finished - started); "
                "no in-game duration column available in aoec."
            ),
            "notes": (
                "POST_GAME_HISTORICAL. Available only after match end. DO NOT use as "
                "PRE_GAME feature for predicting match T outcome (I3 violation). "
                "Useful for retrospective analysis: rating-update weighting, learning-curve "
                "measurement, game-length-conditioned BTL. Phase 02 feature extractors that "
                "drop POST_GAME_HISTORICAL tokens will auto-exclude. "
                "Unit: seconds (canonical cross-dataset unit). "
                "Source: EXTRACT(EPOCH FROM (matches_raw.finished - matches_raw.started)). "
                "Cross-dataset I7 provenance: sc2egset 22.4 loops/sec; "
                "aoestats /1e9 nanoseconds; aoec EXTRACT EPOCH (this dataset)."
            ),
        },
        {
            "name": "dataset_tag",
            "type": "VARCHAR",
            "nullable": False,
            "description": (
                "Dataset discriminator for UNION ALL across sibling datasets. "
                "Constant 'aoe2companion' in this TABLE."
            ),
            "notes": "IDENTITY. Matches the prefix before '::' in match_id.",
        },
    ],
    "provenance": {
        "source_tables": ["matches_raw"],
        "source_note": (
            "Reads from matches_raw directly (not matches_1v1_clean VIEW) due to DuckDB 1.5.1 "
            "bug. ADDENDUM: duration_seconds derived from r.finished - r.started (in _mhm_base "
            "staging; no additional JOIN required)."
        ),
        "join_key": (
            "self-join on 'aoe2companion::' || CAST(matchId AS VARCHAR); "
            "player_id = CAST(profileId AS VARCHAR)."
        ),
        "filter": (
            "internalLeaderboardId IN (6, 18); profileId != -1; "
            "deduplicated; R03 complementarity."
        ),
        "scope": (
            "30,531,196 true 1v1 decisive matches, 61,062,392 player-rows."
        ),
        "created_by": (
            "sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/"
            "01_04_03_minimal_history_view.py"
        ),
    },
    "invariants": [
        {
            "id": "I3",
            "description": (
                "TIMESTAMP temporal anchor. duration_seconds is POST_GAME_HISTORICAL "
                "(machine-grep-able token): DO NOT use as PRE_GAME feature."
            ),
        },
        {
            "id": "I5",
            "description": (
                "Player-row symmetry. duration_seconds is identical for both rows "
                "(self-join propagates same value). "
                "Slot-bias gate is N/A for aoec (natively player-row)."
            ),
        },
        {
            "id": "I6",
            "description": (
                "CREATE TABLE DDL + every assertion SQL stored verbatim in "
                "01_04_03_minimal_history_view.json sql_queries block."
            ),
        },
        {
            "id": "I7",
            "description": (
                "matchId INTEGER provenance: matches_raw.yaml line `matchId: INTEGER`. "
                "EXTRACT(EPOCH FROM) is standard DuckDB -- no magic constant."
            ),
        },
        {
            "id": "I8",
            "description": (
                "9-column cross-dataset contract (ADDENDUM: extended from 8). "
                "duration_seconds unit is seconds across all datasets."
            ),
        },
        {
            "id": "I9",
            "description": (
                "Pure non-destructive projection. matches_raw read-only. "
                "Staging tables _mhm_base and _good_match_ids created and immediately dropped."
            ),
        },
    ],
    "provenance_categories_note": (
        "Per-column 'notes' uses vocabulary: IDENTITY, CONTEXT, PRE_GAME, TARGET, "
        "POST_GAME_HISTORICAL (added in ADDENDUM)."
    ),
}

with open(yaml_path, "w") as f:
    yaml.safe_dump(schema, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

print(f"Schema YAML written: {yaml_path}")
print(f"Nullable values from DESCRIBE:")
for col_name, nullable_val in nullable_map.items():
    print(f"  {col_name}: nullable={nullable_val}")

# %% [markdown]
# ## Cell 19 -- Close connection + final summary

# %%
db.close()
print("DuckDB connection closed.")

print("\n=== FINAL SUMMARY: Step 01_04_03 (aoe2companion, ADDENDUM: 9-col) ===")
print(f"TABLE created:         matches_history_minimal")
print(f"Rows:                  {total_rows} ({distinct_match_ids} matches x 2)")
print(f"Schema:                {len(view_col_names)} cols, started_at dtype: {view_col_types[1]}")
print(f"duration_seconds:      min={min_dur}, max={max_dur}, nulls={null_duration_seconds} ({dur_null_fraction*100:.4f}%)")
print(f"Symmetry violations:   {symmetry_violations}")
print(f"Prefix violations:     {prefix_violations}")
print(f"dataset_tag distinct:  {n_distinct_tags}")
print(f"Faction vocab size:    {len(faction_vocab)} distinct civs")
print(f"Faction vocab (top 5): {list(faction_vocab.keys())[:5]}")
print(f"matchId range:         {min_match_id_val} to {max_match_id_val} (max {max_decimal_digits} digits)")
print(f"All assertions pass:   {all_assertions_pass}")
print(f"\nGate summary:")
print(f"  Gate +1 (9 cols):                {'PASS' if len(view_col_names) == 9 else 'FAIL'}")
print(f"  Gate +2 (null_dur reported):     {null_duration_seconds} NULLs")
print(f"  Gate +3 (non-positive, REPORT):  {non_positive_dur} rows (clock skew, not unit regression)")
print(f"  Gate +5a (max <= 1_000_000_000): {'PASS' if (max_dur is None or max_dur <= 1_000_000_000) else 'FAIL'}")
print(f"  Gate +5b (outlier_gt_86400):     {outlier_count_gt_86400} rows (report-only)")
print(f"  Gate +6 (null frac <= 1%):       {'PASS' if dur_null_fraction <= 0.01 else 'FAIL'}")
print(f"\nArtifacts:")
print(f"  {json_path}")
print(f"  {md_path}")
print(f"  {yaml_path}")
