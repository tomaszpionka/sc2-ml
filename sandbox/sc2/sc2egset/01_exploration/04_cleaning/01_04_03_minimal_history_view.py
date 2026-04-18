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
# # Step 01_04_03 -- Minimal Cross-Dataset History View (sc2egset pattern-establisher)
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_04 -- Data Cleaning
# **Step:** 01_04_03
# **Dataset:** sc2egset (pattern-establisher; aoestats + aoe2companion follow in sibling PRs)
# **Predecessor:** 01_04_02 (Data Cleaning Execution -- complete)
# **Step scope:** Create `matches_history_minimal` VIEW -- 9-column player-row-grain
# projection of `matches_flat_clean` (2 rows per 1v1 match). Canonical TIMESTAMP
# temporal dtype. Per-dataset-polymorphic faction vocabulary. Cross-dataset-harmonized
# substrate for Phase 02+ rating-system backtesting. Pure projection (I9).
# **Invariants applied:**
#   - I3 (TIMESTAMP cast enables chronologically faithful ordering;
#     duration_seconds is POST_GAME_HISTORICAL -- excluded from PRE_GAME features)
#   - I5-analog (player-row symmetry, NULL-safe assertion via IS DISTINCT FROM;
#     extended to include duration_seconds symmetry)
#   - I6 (DDL + every assertion SQL stored verbatim in validation JSON artifact)
#   - I7 (magic literals 32/42 cite matches_long_raw.yaml join_key regex provenance;
#     22.4 loops/sec cites details.gameSpeed cardinality=1 from sc2egset W02 census)
#   - I8 (9-column cross-dataset contract; per-dataset-polymorphic faction vocabulary)
#   - I9 (pure non-destructive projection; no upstream modification)
# **ADDENDUM:** Extended to 9-col contract (duration_seconds BIGINT added between
# won and dataset_tag) per user directive 2026-04-18. Column 8 = duration_seconds
# POST_GAME_HISTORICAL; sourced from player_history_all.header_elapsedGameLoops
# (matches_long_raw and matches_flat_clean exclude it per I3). Aggregated per replay
# before join to avoid row multiplication (player_history_all has 2 rows per replay).
# 22.4 loops/sec: SC2 "Faster" game-speed constant (Liquipedia); details.gameSpeed
# cardinality=1 in sc2egset (W02 census, research_log.md:424).
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
# ## Cell 3 -- DuckDB Connection (writable -- creates VIEW)
#
# This notebook creates one new VIEW: `matches_history_minimal`.
# A writable connection is required.
# WARNING: Close all read-only notebook connections to this DB before running.
# Pre-execution constraint (R1-WARNING-7): no parallel CLI writes during T02.

# %%
db = get_notebook_db("sc2", "sc2egset", read_only=False)
con = db.con
print("DuckDB connection opened (read-write).")

# %% [markdown]
# ## Cell 4 -- Source-view sanity check
#
# DESCRIBE matches_flat_clean; assert 28 cols + presence of required columns.
# Verifies the expected schema from matches_flat_clean.yaml (01_04_02 artifact).

# %%
describe_src = con.execute("DESCRIBE matches_flat_clean").fetchall()
src_col_names = [row[0] for row in describe_src]
print(f"matches_flat_clean column count: {len(src_col_names)}")
print(f"Columns: {src_col_names}")

# Assert 30 columns (28 original + duration_seconds + is_duration_suspicious
# added by 01_04_02 ADDENDUM 2026-04-18; this notebook always runs after that ADDENDUM)
assert len(src_col_names) == 30, (
    f"Expected 30 columns in matches_flat_clean, got {len(src_col_names)}"
)

# Assert required columns are present
required_cols = ["replay_id", "toon_id", "race", "result", "details_timeUTC"]
for col in required_cols:
    assert col in src_col_names, (
        f"Required column '{col}' missing from matches_flat_clean"
    )

print("Source-view sanity check PASSED: 30 cols + all required columns present.")

# %% [markdown]
# ## Cell 4b -- player_history_all sanity check
#
# ADDENDUM: Verify player_history_all has header_elapsedGameLoops.
# This is the source for duration_seconds (matches_long_raw + matches_flat_clean
# exclude it per I3; player_history_all retains it at line 112 of its YAML schema).

# %%
describe_pha = con.execute("DESCRIBE player_history_all").fetchall()
pha_col_names = [row[0] for row in describe_pha]
print(f"player_history_all column count: {len(pha_col_names)}")

assert "header_elapsedGameLoops" in pha_col_names, (
    "BLOCKER: header_elapsedGameLoops missing from player_history_all"
)
assert "replay_id" in pha_col_names, (
    "BLOCKER: replay_id missing from player_history_all"
)

print("player_history_all sanity check PASSED: header_elapsedGameLoops + replay_id present.")

# %% [markdown]
# ## Cell 5 -- Define DDL constant
#
# CREATE OR REPLACE VIEW DDL (ADDENDUM: 9-col contract, duration_seconds added).
# duration_per_replay CTE aggregates header_elapsedGameLoops per replay_id before
# joining to avoid row multiplication (player_history_all has 2 rows per replay;
# value is constant per replay so ANY_VALUE is safe).
# I7 provenance for 22.4 loops/sec: details.gameSpeed cardinality=1 in sc2egset
# (W02 census, research_log.md:424) + Blizzard "Faster" constant (Liquipedia SC2 Game Speed).
# raw_match_id alias exists in base CTE (line 121 of original notebook).

# %%
CREATE_MATCHES_HISTORY_MINIMAL_SQL = """\
CREATE OR REPLACE VIEW matches_history_minimal AS
-- Purpose: Minimal cross-dataset-harmonized history view for rating-system
--   backtesting (Phase 02+ consumer).
-- Grain: 2 rows per 1v1 match (player row + opponent row, symmetric swap).
-- Cross-dataset contract: 9 columns, identical dtypes across sibling views.
--   Canonical temporal dtype = TIMESTAMP (no TZ). Faction vocabulary is
--   per-dataset-polymorphic (SC2 race stems vs AoE2 civ names).
-- Invariants: I3 (TIMESTAMP cast enables faithful chronological ordering;
--   duration_seconds is POST_GAME_HISTORICAL -- excluded from PRE_GAME features),
--   I5-analog (player-row symmetry, NULL-safe assertion; duration_seconds
--   symmetric between row pairs), I6 (DDL verbatim in JSON artifact),
--   I7 (magic numbers 32/42 cite matches_long_raw.yaml join_key regex
--   [0-9a-f]{32}; 22.4 loops/sec cites details.gameSpeed cardinality=1
--   from sc2egset W02 census, research_log.md:424 + Blizzard Faster constant),
--   I8 (UNION-compatible with sibling datasets via dataset_tag + prefixed
--   match_id + canonical 9-col dtypes), I9 (pure projection; no upstream mod).
WITH base AS (
    SELECT
        'sc2egset::' || mfc.replay_id              AS match_id,
        mfc.replay_id                              AS raw_match_id,
        TRY_CAST(mfc.details_timeUTC AS TIMESTAMP) AS started_at,
        mfc.toon_id                                AS player_id,
        mfc.race                                   AS faction,
        (mfc.result = 'Win')                       AS won
    FROM matches_flat_clean mfc
),
duration_per_replay AS (
    -- Aggregate header_elapsedGameLoops to 1 value per replay before join.
    -- player_history_all has 2 rows per replay; value is constant per replay.
    -- I7 provenance for 22.4 loops/sec: details.gameSpeed cardinality=1 in
    -- sc2egset (W02 census, research_log.md:424) + Blizzard Faster constant
    -- (Liquipedia SC2 Game Speed). matches_long_raw and matches_flat_clean
    -- exclude header_elapsedGameLoops per I3; player_history_all retains it.
    -- A-D1 caveat: assumes Faster speed (22.4 loops/sec) for all replays;
    -- non-Faster replays would underestimate duration. Accepted for thesis-level
    -- precision; flagged in schema YAML notes.
    SELECT
        replay_id,
        ANY_VALUE(header_elapsedGameLoops) AS game_loops
    FROM player_history_all
    GROUP BY replay_id
)
SELECT
    p.match_id,
    p.started_at,
    p.player_id,
    o.player_id                                    AS opponent_id,
    p.faction,
    o.faction                                      AS opponent_faction,
    p.won,
    CAST(dpr.game_loops / 22.4 AS BIGINT)          AS duration_seconds,
    'sc2egset'                                     AS dataset_tag
FROM base p
JOIN base o
  ON p.match_id = o.match_id
 AND p.player_id <> o.player_id
LEFT JOIN duration_per_replay dpr
  ON dpr.replay_id = p.raw_match_id
ORDER BY p.started_at, p.match_id, p.player_id\
"""

print("DDL constant defined.")
print(CREATE_MATCHES_HISTORY_MINIMAL_SQL)

# %% [markdown]
# ## Cell 6 -- Execute DDL (create VIEW)

# %%
con.execute(CREATE_MATCHES_HISTORY_MINIMAL_SQL)
print("VIEW matches_history_minimal created successfully.")

# %% [markdown]
# ## Cell 7 -- Schema shape validation
#
# DESCRIBE matches_history_minimal; assert 9 columns + exact dtypes per spec.
# ADDENDUM: 9 columns now (duration_seconds BIGINT added between won and dataset_tag).
# Expected: [VARCHAR, TIMESTAMP, VARCHAR, VARCHAR, VARCHAR, VARCHAR, BOOLEAN, BIGINT, VARCHAR]
# for columns [match_id, started_at, player_id, opponent_id, faction, opponent_faction,
#              won, duration_seconds, dataset_tag].
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
# Gate: total_rows=44418, distinct_match_ids=22209, src_rows=44418, matches_with_not_2_rows=0.

# %%
ROW_COUNT_CHECK_SQL = """\
SELECT
    (SELECT COUNT(*) FROM matches_history_minimal)                  AS total_rows,
    (SELECT COUNT(DISTINCT match_id) FROM matches_history_minimal)  AS distinct_match_ids,
    (SELECT COUNT(*) FROM matches_flat_clean)                       AS src_rows,
    (SELECT COUNT(DISTINCT replay_id) FROM matches_flat_clean)      AS src_replays,
    (SELECT COUNT(*) FROM (
        SELECT match_id, COUNT(*) AS n
        FROM matches_history_minimal
        GROUP BY match_id
        HAVING n = 2
     ))                                                             AS matches_with_2_rows,
    (SELECT COUNT(*) FROM (
        SELECT match_id, COUNT(*) AS n
        FROM matches_history_minimal
        GROUP BY match_id
        HAVING n <> 2
     ))                                                             AS matches_with_not_2_rows\
"""

rc = con.execute(ROW_COUNT_CHECK_SQL).fetchone()
total_rows, distinct_match_ids, src_rows, src_replays, matches_with_2_rows, matches_with_not_2_rows = rc

print(f"total_rows:             {total_rows}")
print(f"distinct_match_ids:     {distinct_match_ids}")
print(f"src_rows:               {src_rows}")
print(f"src_replays:            {src_replays}")
print(f"matches_with_2_rows:    {matches_with_2_rows}")
print(f"matches_with_not_2_rows:{matches_with_not_2_rows}")

assert total_rows == 44418, f"Expected total_rows=44418, got {total_rows}"
assert distinct_match_ids == 22209, f"Expected distinct_match_ids=22209, got {distinct_match_ids}"
assert src_rows == 44418, f"Expected src_rows=44418, got {src_rows}"
assert matches_with_not_2_rows == 0, f"Expected matches_with_not_2_rows=0, got {matches_with_not_2_rows}"

print("Row-count validation PASSED.")

# %% [markdown]
# ## Cell 9 -- Symmetry (I5-analog, NULL-safe)
#
# Gate: symmetry_violations=0. Uses IS DISTINCT FROM for NULL-safe comparison.
# ADDENDUM: Extended symmetry check includes duration_seconds IS NOT DISTINCT FROM
# (duration must be identical for both rows of a match -- POST_GAME_HISTORICAL symmetric).

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

# %% [markdown]
# ## Cell 10 -- Zero-NULL on non-nullable spec columns
#
# Gate: null_match_id / null_player_id / null_opponent_id / null_won / null_dataset_tag all 0.
# null_started_at: report only (TRY_CAST failure count; I7 -- not a gate threshold).
# ADDENDUM: null_duration_seconds reported (LEFT JOIN may produce NULLs for replays
# missing from player_history_all; expected=0 but report-only for sc2egset).

# %%
ZERO_NULL_SQL = """\
SELECT
    COUNT(*) FILTER (WHERE match_id     IS NULL) AS null_match_id,
    COUNT(*) FILTER (WHERE started_at   IS NULL) AS null_started_at,
    COUNT(*) FILTER (WHERE player_id    IS NULL) AS null_player_id,
    COUNT(*) FILTER (WHERE opponent_id  IS NULL) AS null_opponent_id,
    COUNT(*) FILTER (WHERE won          IS NULL) AS null_won,
    COUNT(*) FILTER (WHERE duration_seconds IS NULL) AS null_duration_seconds,
    COUNT(*) FILTER (WHERE dataset_tag  IS NULL) AS null_dataset_tag,
    COUNT(*) FILTER (WHERE faction          IS NULL) AS null_faction_info,
    COUNT(*) FILTER (WHERE opponent_faction IS NULL) AS null_opponent_faction_info
FROM matches_history_minimal\
"""

null_row = con.execute(ZERO_NULL_SQL).fetchone()
(
    null_match_id, null_started_at, null_player_id, null_opponent_id,
    null_won, null_duration_seconds, null_dataset_tag,
    null_faction_info, null_opponent_faction_info
) = null_row

print(f"null_match_id:             {null_match_id}")
print(f"null_started_at:           {null_started_at}  (report only -- TRY_CAST failures)")
print(f"null_player_id:            {null_player_id}")
print(f"null_opponent_id:          {null_opponent_id}")
print(f"null_won:                  {null_won}")
print(f"null_duration_seconds:     {null_duration_seconds}  (Gate +2)")
print(f"null_dataset_tag:          {null_dataset_tag}")
print(f"null_faction_info:         {null_faction_info}  (report only)")
print(f"null_opponent_faction_info:{null_opponent_faction_info}  (report only)")

assert null_match_id == 0, f"null_match_id={null_match_id} (expected 0)"
assert null_player_id == 0, f"null_player_id={null_player_id} (expected 0)"
assert null_opponent_id == 0, f"null_opponent_id={null_opponent_id} (expected 0)"
assert null_won == 0, f"null_won={null_won} (expected 0)"
assert null_dataset_tag == 0, f"null_dataset_tag={null_dataset_tag} (expected 0)"

print("Zero-NULL validation PASSED for all 5 non-nullable spec columns.")
print(f"duration_seconds NULLs: {null_duration_seconds}  (Gate +2 reported)")

# %% [markdown]
# ## Cell 10b -- duration_seconds positive-value and range assertions
#
# ADDENDUM Gates +3, +4, +5:
# Gate +3: duration_seconds > 0 for all non-NULL rows.
# Gate +4: Duration symmetry (covered in Cell 9 symmetry check).
# Gate +5 (HALTING): max(duration_seconds) <= 86400 (24 hours sanity bound).
#   Protects against nanosecond-unit regression: if max > 86400, unit is wrong.

# %%
DURATION_STATS_SQL = """\
SELECT
    MIN(duration_seconds)                                         AS min_duration_seconds,
    MAX(duration_seconds)                                         AS max_duration_seconds,
    AVG(duration_seconds)                                         AS avg_duration_seconds,
    COUNT(*) FILTER (WHERE duration_seconds IS NOT NULL)          AS non_null_count,
    COUNT(*) FILTER (WHERE duration_seconds IS NOT NULL
                       AND duration_seconds <= 0)                 AS non_positive_count
FROM matches_history_minimal\
"""

dur_row = con.execute(DURATION_STATS_SQL).fetchone()
min_dur, max_dur, avg_dur, non_null_dur, non_positive_dur = dur_row

print(f"min_duration_seconds: {min_dur}")
print(f"max_duration_seconds: {max_dur}")
print(f"avg_duration_seconds: {avg_dur:.1f}")
print(f"non_null_count:       {non_null_dur}")
print(f"non_positive_count:   {non_positive_dur}  (Gate +3: expected 0)")

# Gate +3: no non-positive values among non-NULLs
assert non_positive_dur == 0, (
    f"Gate +3 FAILED: {non_positive_dur} rows with duration_seconds <= 0"
)
print("Gate +3 PASS: all non-NULL duration_seconds > 0.")

# Gate +5 (HALTING): max <= 86400 (24 hours). Catches nanosecond-unit regression.
assert max_dur is None or max_dur <= 86400, (
    f"Gate +5 HALTING FAILED: max_duration_seconds={max_dur} > 86400 "
    f"(unit regression? expected seconds, got nanoseconds?)"
)
print(f"Gate +5 PASS: max_duration_seconds={max_dur} <= 86400.")

# %% [markdown]
# ## Cell 11 -- match_id prefix verification
#
# Gate: prefix_violations=0; length == 42.
# Magic literals 32 / 42 cite matches_long_raw.yaml join_key regex [0-9a-f]{32} (I7 provenance).

# %%
PREFIX_CHECK_SQL = """\
-- Magic literals: 'sc2egset::' = 10-char literal prefix (plan spec);
--                 32 = replay_id hex length from
--                      src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/matches_long_raw.yaml
--                      join_key regex [0-9a-f]{32} (I7 provenance).
-- Total length contract: 10 + 32 = 42.
SELECT COUNT(*) AS prefix_violations
FROM matches_history_minimal
WHERE match_id NOT LIKE 'sc2egset::%'
   OR length(match_id) <> length('sc2egset::') + 32
   OR regexp_extract(match_id, '::([0-9a-f]{32})$', 1) = ''\
"""

prefix_row = con.execute(PREFIX_CHECK_SQL).fetchone()
prefix_violations = prefix_row[0]
print(f"prefix_violations: {prefix_violations}")

assert prefix_violations == 0, f"prefix_violations={prefix_violations} (expected 0)"

print("Prefix uniqueness PASSED.")

# %% [markdown]
# ## Cell 12 -- dataset_tag constant
#
# Gate: n_distinct_tags=1, the_tag='sc2egset'.

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
assert the_tag == "sc2egset", f"the_tag={the_tag!r} (expected 'sc2egset')"

print("dataset_tag constant PASSED.")

# %% [markdown]
# ## Cell 13 -- Faction vocabulary (exploratory, no gate)
#
# Documents per-dataset polymorphism (I8). sc2egset empirically ships `Prot`/`Terr`/`Zerg`
# 4-char stems (NOT full 'Protoss'/'Terran'/'Zerg').
# Expected counts approx: 'Prot' ~16121, 'Zerg' ~15527, 'Terr' ~12770.
# No hard assertion -- exploratory per plan spec.

# %%
FACTION_VOCAB_SQL = """\
SELECT faction, COUNT(*) AS n
FROM matches_history_minimal
GROUP BY faction
ORDER BY n DESC\
"""

faction_rows = con.execute(FACTION_VOCAB_SQL).fetchall()
print("Faction vocabulary (per-dataset polymorphic, sc2egset 4-char stems):")
for faction, n in faction_rows:
    print(f"  {faction!r}: {n}")

faction_vocab = {row[0]: row[1] for row in faction_rows}
print(f"\nTotal faction vocab size: {len(faction_vocab)} distinct values")
print("NOTE: sc2egset faction vocabulary is 4-char race stems (Prot/Terr/Zerg).")
print("      Consumers MUST NOT treat faction as cross-dataset categorical without game-conditional encoding.")

# %% [markdown]
# ## Cell 14 -- Temporal sanity (I3)
#
# Report min/max started_at, null count, distinct count.
# TIMESTAMP ordering is chronologically faithful (unlike upstream VARCHAR lex ordering).

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
print(f"null_started_at:     {null_started_at_ts}  (TRY_CAST failures; expected 0)")
print(f"distinct_started_at: {distinct_started_at}")

# %% [markdown]
# ## Cell 15 -- Build validation JSON + assert all_assertions_pass
#
# Captures: step metadata, row_counts, assertion_results, sql_queries (verbatim I6),
# describe_table_rows (DESCRIBE output for nullable-flag reproducibility).
# ADDENDUM: 9-col schema; duration_seconds stats included.
# Note: DuckDB may return DuckDBPyType for column_type; stringify with str(x) per R3-NOTE-2.

# %%
reports_dir = get_reports_dir("sc2", "sc2egset")
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
    "src_col_count_30": len(describe_src) == 30,  # ADDENDUM 2026-04-18: 28+2 (duration_seconds + is_duration_suspicious)
    "required_src_cols_present": all(c in src_col_names for c in required_cols),
    "col_count_9": len(view_col_names) == 9,
    "col_names_match": view_col_names == expected_col_names,
    "col_dtypes_match": view_col_types == expected_dtypes,
    "total_rows_44418": total_rows == 44418,
    "distinct_match_ids_22209": distinct_match_ids == 22209,
    "src_rows_44418": src_rows == 44418,
    "matches_with_not_2_rows_0": matches_with_not_2_rows == 0,
    "symmetry_violations_0": symmetry_violations == 0,
    "null_match_id_0": null_match_id == 0,
    "null_player_id_0": null_player_id == 0,
    "null_opponent_id_0": null_opponent_id == 0,
    "null_won_0": null_won == 0,
    "null_dataset_tag_0": null_dataset_tag == 0,
    "prefix_violations_0": prefix_violations == 0,
    "n_distinct_tags_1": n_distinct_tags == 1,
    "dataset_tag_sc2egset": the_tag == "sc2egset",
    "duration_non_positive_0": non_positive_dur == 0,
    "duration_max_le_86400": max_dur is None or max_dur <= 86400,
}

all_assertions_pass = all(assertion_results.values())

validation = {
    "step": "01_04_03",
    "dataset": "sc2egset",
    "game": "sc2",
    "generated_date": str(date.today()),
    "view": "matches_history_minimal",
    "schema_version": "9-col (ADDENDUM: duration_seconds added 2026-04-18)",
    "row_counts": {
        "total_rows": total_rows,
        "distinct_match_ids": distinct_match_ids,
        "src_rows": src_rows,
        "src_replays": src_replays,
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
        "null_faction_info": null_faction_info,
        "null_opponent_faction_info": null_opponent_faction_info,
    },
    "duration_stats": {
        "min_duration_seconds": min_dur,
        "max_duration_seconds": max_dur,
        "avg_duration_seconds": avg_dur,
        "non_null_count": non_null_dur,
        "non_positive_count": non_positive_dur,
        "gate_plus3_pass": non_positive_dur == 0,
        "gate_plus5_pass": max_dur is None or max_dur <= 86400,
        "provenance": (
            "CAST(header_elapsedGameLoops / 22.4 AS BIGINT). "
            "22.4 loops/sec: SC2 Faster game-speed constant (Liquipedia). "
            "details.gameSpeed cardinality=1 in sc2egset (research_log.md:424). "
            "Source: player_history_all.header_elapsedGameLoops (aggregated per replay "
            "via ANY_VALUE to avoid row multiplication; player_history_all has 2 rows/replay)."
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
    "faction_vocab": faction_vocab,
    "schema_shape": {
        "col_names": view_col_names,
        "col_types": view_col_types,
    },
    "assertion_results": assertion_results,
    "all_assertions_pass": all_assertions_pass,
    "describe_table_rows": describe_table_rows,
    "sql_queries": {
        "CREATE_MATCHES_HISTORY_MINIMAL_SQL": CREATE_MATCHES_HISTORY_MINIMAL_SQL,
        "ROW_COUNT_CHECK_SQL": ROW_COUNT_CHECK_SQL,
        "SYMMETRY_I5_ANALOG_SQL": SYMMETRY_I5_ANALOG_SQL,
        "ZERO_NULL_SQL": ZERO_NULL_SQL,
        "DURATION_STATS_SQL": DURATION_STATS_SQL,
        "PREFIX_CHECK_SQL": PREFIX_CHECK_SQL,
        "DATASET_TAG_CHECK_SQL": DATASET_TAG_CHECK_SQL,
        "FACTION_VOCAB_SQL": FACTION_VOCAB_SQL,
        "TEMPORAL_SANITY_SQL": TEMPORAL_SANITY_SQL,
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
# ## Cell 16 -- Build markdown report

# %%
md_path = artifact_dir / "01_04_03_minimal_history_view.md"

faction_table_rows = "\n".join(
    f"| `{faction}` | {n} |" for faction, n in faction_rows
)

md_content = f"""# Step 01_04_03 -- Minimal Cross-Dataset History View

**Generated:** {date.today()}
**Dataset:** sc2egset
**Game:** SC2
**Step:** 01_04_03
**Predecessor:** 01_04_02 (Data Cleaning Execution)
**Schema version:** 9-col (ADDENDUM: duration_seconds added 2026-04-18)

## Summary

Created `matches_history_minimal` VIEW -- 9-column player-row-grain projection of
`matches_flat_clean` (2 rows per 1v1 match). Canonical TIMESTAMP temporal dtype
(via TRY_CAST of `details_timeUTC`). Per-dataset-polymorphic faction vocabulary.
Cross-dataset-harmonized substrate for Phase 02+ rating-system backtesting.
Pure non-destructive projection (I9).

ADDENDUM: Added `duration_seconds` BIGINT (column 8) between `won` and `dataset_tag`.
Source: `player_history_all.header_elapsedGameLoops / 22.4` (SC2 Faster loops/sec).
POST_GAME_HISTORICAL -- excluded from PRE_GAME features.

## Schema (9 columns)

| column | dtype | semantics |
|---|---|---|
| `match_id` | VARCHAR | `'sc2egset::'` + 32-char hex replay_id (length = 42) |
| `started_at` | TIMESTAMP | TRY_CAST of details_timeUTC; canonical cross-dataset type |
| `player_id` | VARCHAR | Battle.net toon_id |
| `opponent_id` | VARCHAR | Opposing toon_id |
| `faction` | VARCHAR | Raw race stems `Prot`/`Terr`/`Zerg` (4-char; NOT full names). PER-DATASET POLYMORPHIC |
| `opponent_faction` | VARCHAR | Opposing race (same vocabulary as faction) |
| `won` | BOOLEAN | Focal player's outcome (complementary between the 2 rows) |
| `duration_seconds` | BIGINT | POST_GAME_HISTORICAL. Duration in seconds = header_elapsedGameLoops / 22.4. 22.4 loops/sec: SC2 Faster constant (Liquipedia); details.gameSpeed cardinality=1 (research_log.md:424). |
| `dataset_tag` | VARCHAR | Constant `'sc2egset'` |

## Row-count flow

| metric | value |
|---|---|
| Source matches_flat_clean rows | {src_rows} |
| Source distinct replay_ids | {src_replays} |
| matches_history_minimal total rows | {total_rows} |
| distinct match_ids | {distinct_match_ids} |
| matches with exactly 2 rows | {matches_with_2_rows} |
| matches with NOT 2 rows | {matches_with_not_2_rows} |

## duration_seconds stats (ADDENDUM gates)

| metric | value | gate |
|---|---|---|
| min_duration_seconds | {min_dur} | report only |
| max_duration_seconds | {max_dur} | <= 86400 (Gate +5) |
| avg_duration_seconds | {avg_dur:.1f} | report only |
| non_null_count | {non_null_dur} | report only |
| null_duration_seconds | {null_duration_seconds} | report only (Gate +2) |
| non_positive_count | {non_positive_dur} | 0 (Gate +3) |

## Faction vocabulary (per-dataset polymorphic)

| faction | count |
|---|---|
{faction_table_rows}

NOTE: sc2egset faction vocabulary is 4-char race stems (Prot/Terr/Zerg).
Consumers MUST NOT treat faction as a single categorical feature across
datasets without game-conditional encoding.

## Temporal sanity (I3)

| metric | value |
|---|---|
| min_started_at | {min_started_at} |
| max_started_at | {max_started_at} |
| null_started_at (TRY_CAST failures) | {null_started_at_ts} |
| distinct_started_at | {distinct_started_at} |

## NULL counts

| column | null count | gate |
|---|---|---|
| match_id | {null_match_id} | 0 (GATE) |
| started_at | {null_started_at} | report only |
| player_id | {null_player_id} | 0 (GATE) |
| opponent_id | {null_opponent_id} | 0 (GATE) |
| won | {null_won} | 0 (GATE) |
| duration_seconds | {null_duration_seconds} | report only (Gate +2) |
| dataset_tag | {null_dataset_tag} | 0 (GATE) |
| faction | {null_faction_info} | report only |
| opponent_faction | {null_opponent_faction_info} | report only |

## Gate verdict

| check | result |
|---|---|
| Row count 44,418 = 2 x 22,209 | {'PASS' if total_rows == 44418 and distinct_match_ids == 22209 else 'FAIL'} |
| Column count 9 (Gate +1) | {'PASS' if len(view_col_names) == 9 else 'FAIL'} |
| started_at dtype TIMESTAMP | {'PASS' if 'TIMESTAMP' in view_col_types[1] else 'FAIL'} |
| duration_seconds dtype BIGINT | {'PASS' if view_col_types[7] == 'BIGINT' else 'FAIL'} |
| I5-analog NULL-safe symmetry violations (incl. duration) = 0 | {'PASS' if symmetry_violations == 0 else 'FAIL'} |
| match_id prefix violations = 0; length = 42 | {'PASS' if prefix_violations == 0 else 'FAIL'} |
| dataset_tag distinct count = 1 | {'PASS' if n_distinct_tags == 1 else 'FAIL'} |
| Zero NULLs in match_id / player_id / opponent_id / won / dataset_tag | {'PASS' if null_match_id == null_player_id == null_opponent_id == null_won == null_dataset_tag == 0 else 'FAIL'} |
| duration_seconds non-positive = 0 (Gate +3) | {'PASS' if non_positive_dur == 0 else 'FAIL'} |
| duration_seconds max <= 86400 (Gate +5 HALTING) | {'PASS' if (max_dur is None or max_dur <= 86400) else 'FAIL'} |
| All assertions pass | {'PASS' if all_assertions_pass else 'FAIL'} |

## Artifact

Validation JSON: `{json_path.relative_to(json_path.parents[8])}`
"""

with open(md_path, "w") as f:
    f.write(md_content)

print(f"Markdown report written: {md_path}")

# %% [markdown]
# ## Cell 17 -- Write schema YAML for matches_history_minimal
#
# ADDENDUM: 9-col schema. duration_seconds column added between won and dataset_tag.
# POST_GAME_HISTORICAL machine-token in notes (per I3 token vocabulary).
# I7 provenance for 22.4 constant cited in notes.

# %%
schema_dir = reports_dir.parent / "data" / "db" / "schemas" / "views"
schema_dir.mkdir(parents=True, exist_ok=True)

yaml_path = schema_dir / "matches_history_minimal.yaml"

# Translate DESCRIBE nullable flags to concrete Python booleans
describe_rows_for_yaml = con.execute("DESCRIBE matches_history_minimal").fetchall()
nullable_map = {row[0]: (row[2] == "YES") for row in describe_rows_for_yaml}

schema = {
    "table": "matches_history_minimal",
    "dataset": "sc2egset",
    "game": "sc2",
    "object_type": "view",
    "step": "01_04_03",
    "schema_version": "9-col (ADDENDUM: duration_seconds added 2026-04-18)",
    "row_count": total_rows,
    "describe_artifact": (
        "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts"
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
                "For sc2egset: 'sc2egset::<32-char-hex-replay_id>'. Prefix guarantees UNION ALL "
                "uniqueness across sibling datasets. Length contract = 42 chars (10 prefix + 32 hex) "
                "derived from src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/"
                "matches_long_raw.yaml join_key regex [0-9a-f]{32} (I7 provenance)."
            ),
            "notes": "IDENTITY. Prefix applied in this VIEW only; upstream replay_id unchanged (I9).",
        },
        {
            "name": "started_at",
            "type": "TIMESTAMP",
            "nullable": nullable_map["started_at"],
            "description": (
                "Match start time. TIMESTAMP (no TZ) via TRY_CAST(matches_flat_clean.details_timeUTC "
                "AS TIMESTAMP). Canonical cross-dataset dtype: sibling VIEWs (aoestats, aoe2companion) "
                "MUST emit TIMESTAMP (aoestats CAST from TIMESTAMPTZ AT TIME ZONE 'UTC'; aoe2companion "
                "pass-through). DuckDB TRY_CAST handles variable sub-second precision (7 observed "
                "length variants 22-28 chars in upstream VARCHAR)."
            ),
            "notes": (
                "CONTEXT. Temporal anchor for Phase 02 rating-update loops. "
                "Chronologically faithful (TIMESTAMP ordering, not lex)."
            ),
        },
        {
            "name": "player_id",
            "type": "VARCHAR",
            "nullable": nullable_map["player_id"],
            "description": "Focal player identifier. sc2egset: Battle.net toon_id.",
            "notes": (
                "IDENTITY. Per-dataset identifier; cross-dataset identity resolution "
                "is a future step (Phase 01_05+)."
            ),
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
                "Focal player's faction. Per-dataset polymorphic vocabulary (cross-dataset "
                "column name + dtype only -- values differ in ontology). sc2egset: 4-char race "
                "stems Prot/Terr/Zerg (empirically verified; NOT full 'Protoss'/'Terran'/'Zerg'). "
                "aoestats: full civilization names (Mongols, Franks, etc.). "
                "aoe2companion: full civilization names. "
                "CONSUMERS MUST NOT treat faction as a single categorical feature across "
                "datasets without game-conditional encoding (e.g., WHERE dataset_tag = 'sc2egset' "
                "before GROUP BY faction)."
            ),
            "notes": (
                "PRE_GAME. Raw vocabulary (race actually played, not selectedRace which includes "
                "'Random'). Polymorphic I8 contract -- see description."
            ),
        },
        {
            "name": "opponent_faction",
            "type": "VARCHAR",
            "nullable": nullable_map["opponent_faction"],
            "description": "Opposing player's faction (same per-dataset vocabulary as `faction`).",
            "notes": "PRE_GAME. Mirror of faction from the opponent row.",
        },
        {
            "name": "won",
            "type": "BOOLEAN",
            "nullable": nullable_map["won"],
            "description": (
                "TRUE if the focal player won, FALSE otherwise. The two rows of a match have "
                "complementary `won` values (exactly one TRUE, one FALSE)."
            ),
            "notes": (
                "TARGET. Direct projection of matches_flat_clean.result; prediction label "
                "for downstream experiments."
            ),
        },
        {
            "name": "duration_seconds",
            "type": "BIGINT",
            "nullable": nullable_map.get("duration_seconds", True),
            "description": (
                "Match duration in seconds (POST_GAME_HISTORICAL). For sc2egset: "
                "CAST(player_history_all.header_elapsedGameLoops / 22.4 AS BIGINT). "
                "Aggregated per replay via ANY_VALUE before joining (player_history_all has "
                "2 rows per replay; value is constant per replay). "
                "Both rows of a match have identical duration_seconds (symmetric). "
                "I7 provenance for 22.4 loops/sec: details.gameSpeed cardinality=1 in "
                "sc2egset (W02 census, research_log.md:424) + Blizzard 'Faster' constant "
                "(Liquipedia SC2 Game Speed). "
                "Calibration caveat (A-D1): assumes Faster speed for all replays; "
                "non-Faster replays would underestimate duration (~30% error). "
                "Accepted for thesis-level precision."
            ),
            "notes": (
                "POST_GAME_HISTORICAL. Available only after match end. DO NOT use as "
                "PRE_GAME feature for predicting match T outcome (I3 violation). "
                "Useful for retrospective analysis: rating-update weighting, learning-curve "
                "measurement, game-length-conditioned BTL. Phase 02 feature extractors that "
                "drop POST_GAME_HISTORICAL tokens will auto-exclude. "
                "Unit: seconds (canonical cross-dataset unit). "
                "Source: player_history_all.header_elapsedGameLoops / 22.4 (sc2egset-specific). "
                "Cross-dataset I7 provenance: sc2egset 22.4 loops/sec (this dataset); "
                "aoestats /1e9 nanoseconds via pre_ingestion.py:271; "
                "aoec EXTRACT EPOCH from matches_raw.started/finished."
            ),
        },
        {
            "name": "dataset_tag",
            "type": "VARCHAR",
            "nullable": False,
            "description": (
                "Dataset discriminator for UNION ALL across sibling datasets. "
                "Constant 'sc2egset' in this VIEW."
            ),
            "notes": "IDENTITY. Matches the prefix before '::' in match_id.",
        },
    ],
    "provenance": {
        "source_tables": ["matches_flat_clean", "player_history_all"],
        "join_key": (
            "self-join on matches_flat_clean via replay_id; player_id = toon_id; "
            "opponent_id from sibling row where mfc.toon_id <> opp.toon_id. "
            "LEFT JOIN to duration_per_replay (aggregated player_history_all) on replay_id."
        ),
        "filter": (
            "Inherited from matches_flat_clean: true_1v1_decisive (2 players, 1 Win + 1 Loss) "
            "+ mmr_valid."
        ),
        "scope": (
            "22,209 true 1v1 decisive replays, 44,418 player-rows. Cross-dataset harmonization "
            "substrate for Phase 02+ rating backtesting."
        ),
        "created_by": (
            "sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_03_minimal_history_view.py"
        ),
    },
    "invariants": [
        {
            "id": "I3",
            "description": (
                "TIMESTAMP-typed temporal anchor enables chronologically faithful ordering. "
                "duration_seconds is POST_GAME_HISTORICAL (machine-grep-able token in notes): "
                "DO NOT use as PRE_GAME feature for match T. Phase 02 feature extractors "
                "that drop POST_GAME_HISTORICAL tokens will auto-exclude this column."
            ),
        },
        {
            "id": "I5",
            "description": (
                "Player-row symmetry (I5-analog). Every match_id has exactly 2 rows. "
                "(player_id, opponent_id) appears once in each direction. The two `won` "
                "values are complementary. faction and opponent_faction are mirror images. "
                "duration_seconds is identical for both rows (symmetric LEFT JOIN). "
                "Assertion SQL uses IS DISTINCT FROM for NULL-safe comparison."
            ),
        },
        {
            "id": "I6",
            "description": (
                "CREATE OR REPLACE VIEW DDL + every assertion SQL stored verbatim in "
                "01_04_03_minimal_history_view.json sql_queries block. DESCRIBE result "
                "captured in validation JSON describe_table_rows for reproducibility "
                "of the nullable flags written to this YAML."
            ),
        },
        {
            "id": "I7",
            "description": (
                "Magic literals: PREFIX_CHECK_SQL `32` hex chars / `42` total length cite "
                "upstream data/db/schemas/views/matches_long_raw.yaml join_key regex "
                "[0-9a-f]{32}. duration_seconds constant 22.4 loops/sec cites: "
                "details.gameSpeed cardinality=1 in sc2egset (W02 census, research_log.md:424) "
                "+ Blizzard 'Faster' game-speed constant (Liquipedia SC2 Game Speed)."
            ),
        },
        {
            "id": "I8",
            "description": (
                "Cross-dataset comparability: 9-column names + dtypes are the cross-dataset "
                "contract (ADDENDUM: extended from 8 to 9 cols; duration_seconds BIGINT added). "
                "Canonical temporal dtype = TIMESTAMP (no TZ). Faction vocabulary is "
                "per-dataset-polymorphic. duration_seconds unit is seconds across all datasets "
                "(sc2egset /22.4 loops; aoestats /1e9 ns; aoec EXTRACT EPOCH)."
            ),
        },
        {
            "id": "I9",
            "description": (
                "Pure non-destructive projection. No raw table modified. matches_flat_clean "
                "unchanged. player_history_all is read-only (SELECT only). "
                "Only matches_history_minimal VIEW created via CREATE OR REPLACE."
            ),
        },
    ],
    "provenance_categories_note": (
        "This view inherits provenance categories from matches_flat_clean. Per-column "
        "'notes' field uses the single-token vocabulary (IDENTITY, CONTEXT, PRE_GAME, "
        "TARGET, POST_GAME_HISTORICAL) -- POST_GAME_HISTORICAL added in ADDENDUM."
    ),
}

with open(yaml_path, "w") as f:
    yaml.safe_dump(schema, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

print(f"Schema YAML written: {yaml_path}")
print(f"Nullable values from DESCRIBE:")
for col_name, nullable_val in nullable_map.items():
    print(f"  {col_name}: nullable={nullable_val}")

# %% [markdown]
# ## Cell 18 -- Close connection + final summary

# %%
db.close()
print("DuckDB connection closed.")

print("\n=== FINAL SUMMARY: Step 01_04_03 (sc2egset, ADDENDUM: 9-col) ===")
print(f"VIEW created:          matches_history_minimal")
print(f"Rows:                  {total_rows} ({distinct_match_ids} matches x 2)")
print(f"Schema:                {len(view_col_names)} cols, started_at dtype: {view_col_types[1]}")
print(f"duration_seconds:      min={min_dur}, max={max_dur}, avg={avg_dur:.1f}, nulls={null_duration_seconds}")
print(f"Symmetry violations:   {symmetry_violations}")
print(f"Prefix violations:     {prefix_violations}")
print(f"dataset_tag distinct:  {n_distinct_tags}")
print(f"Faction vocab:         {list(faction_vocab.keys())}")
print(f"All assertions pass:   {all_assertions_pass}")
print(f"\nGate summary:")
print(f"  Gate +1 (9 cols):           {'PASS' if len(view_col_names) == 9 else 'FAIL'}")
print(f"  Gate +2 (null_dur reported): {null_duration_seconds} NULLs")
print(f"  Gate +3 (dur > 0):          {'PASS' if non_positive_dur == 0 else 'FAIL'}")
print(f"  Gate +5 (max <= 86400):     {'PASS' if (max_dur is None or max_dur <= 86400) else 'FAIL'}")
print(f"\nArtifacts:")
print(f"  {json_path}")
print(f"  {md_path}")
print(f"  {yaml_path}")
