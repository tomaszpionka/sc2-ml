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
# # Step 01_04_03 -- Minimal Cross-Dataset History View (aoestats)
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_04 -- Data Cleaning
# **Step:** 01_04_03
# **Dataset:** aoestats (sibling of sc2egset pattern-establisher PR #152)
# **Predecessor:** 01_04_02 (Data Cleaning Execution -- complete)
# **Step scope:** Create `matches_history_minimal` VIEW -- 8-column player-row-grain
# view of `matches_1v1_clean` (2 rows per 1v1 match via UNION ALL pivot). Canonical
# TIMESTAMP temporal dtype via CAST from TIMESTAMPTZ AT TIME ZONE 'UTC'. Per-dataset
# polymorphic faction vocabulary (full civ names ~50 distinct). Cross-dataset-harmonized
# substrate for Phase 02+ rating-system backtesting. Pure projection (I9).
# **Invariants applied:**
#   - I3 (TIMESTAMP cast from TIMESTAMPTZ enables chronologically faithful ordering)
#   - I5-analog (player-row symmetry, NULL-safe assertion via IS DISTINCT FROM;
#     aoestats-specific slot-bias gate: AVG(won::INT) == 0.5 exactly)
#   - I6 (DDL + every assertion SQL stored verbatim in validation JSON artifact)
#   - I7 (game_id is VARCHAR passthrough -- no fixed-length magic literal needed)
#   - I8 (8-column cross-dataset contract; per-dataset-polymorphic faction vocabulary)
#   - I9 (pure non-destructive projection; no upstream modification)
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
# Pre-execution constraint: no parallel CLI writes during T02.

# %%
db = get_notebook_db("aoe2", "aoestats", read_only=False)
con = db.con
print("DuckDB connection opened (read-write).")

# %% [markdown]
# ## Cell 4 -- Source-view sanity check
#
# DESCRIBE matches_1v1_clean; assert 20 cols + presence of required columns.
# Verifies the expected schema from matches_1v1_clean.yaml (01_04_02 artifact).
# aoestats has 1-row-per-match grain; UNION ALL pivot produces 2-rows-per-match.

# %%
describe_src = con.execute("DESCRIBE matches_1v1_clean").fetchall()
src_col_names = [row[0] for row in describe_src]
print(f"matches_1v1_clean column count: {len(src_col_names)}")
print(f"Columns: {src_col_names}")

# Assert 20 columns
assert len(src_col_names) == 20, (
    f"Expected 20 columns in matches_1v1_clean, got {len(src_col_names)}"
)

# Assert required columns are present
required_cols = [
    "game_id", "started_timestamp",
    "p0_profile_id", "p0_civ", "p0_winner",
    "p1_profile_id", "p1_civ", "p1_winner",
    "team1_wins",
]
for col in required_cols:
    assert col in src_col_names, (
        f"Required column '{col}' missing from matches_1v1_clean"
    )

print("Source-view sanity check PASSED: 20 cols + all required columns present.")

# %% [markdown]
# ## Cell 5 -- Define DDL constant
#
# CREATE OR REPLACE VIEW DDL verbatim from plan spec (UNION ALL pivot from
# 1-row-per-match to 2-rows-per-match). Stored as constant for I6 verbatim
# embedding in JSON artifact.
# Key casts:
#   - game_id: VARCHAR passthrough (no CAST needed; I7 -- no fixed-length magic literal)
#   - started_timestamp: TIMESTAMPTZ -> TIMESTAMP via AT TIME ZONE 'UTC' (I3)
#   - p{0,1}_profile_id: BIGINT -> VARCHAR (CAST)
#   - p{0,1}_civ: VARCHAR passthrough (faction)
#   - p{0,1}_winner: BOOLEAN passthrough (won)

# %%
CREATE_MATCHES_HISTORY_MINIMAL_SQL = """\
CREATE OR REPLACE VIEW matches_history_minimal AS
-- aoestats sibling of sc2egset.matches_history_minimal (PR #152 pattern).
-- Input: matches_1v1_clean (1 row/match, p0/p1 cols). UNION ALL -> 2 rows/match.
-- Invariants: I3 (TIMESTAMP cast from TIMESTAMPTZ), I5-analog (NULL-safe symmetry +
--   slot-bias gate), I6 (SQL verbatim in JSON), I7 (prefix cites game_id VARCHAR),
--   I8 (cross-dataset 8-col contract), I9 (no upstream modification).
WITH p0_half AS (
    SELECT
        'aoestats::' || m.game_id                                     AS match_id,
        CAST(m.started_timestamp AT TIME ZONE 'UTC' AS TIMESTAMP)     AS started_at,
        CAST(m.p0_profile_id AS VARCHAR)                              AS player_id,
        CAST(m.p1_profile_id AS VARCHAR)                              AS opponent_id,
        m.p0_civ                                                      AS faction,
        m.p1_civ                                                      AS opponent_faction,
        m.p0_winner                                                   AS won,
        'aoestats'                                                    AS dataset_tag
    FROM matches_1v1_clean m
),
p1_half AS (
    SELECT
        'aoestats::' || m.game_id                                     AS match_id,
        CAST(m.started_timestamp AT TIME ZONE 'UTC' AS TIMESTAMP)     AS started_at,
        CAST(m.p1_profile_id AS VARCHAR)                              AS player_id,
        CAST(m.p0_profile_id AS VARCHAR)                              AS opponent_id,
        m.p1_civ                                                      AS faction,
        m.p0_civ                                                      AS opponent_faction,
        m.p1_winner                                                   AS won,
        'aoestats'                                                    AS dataset_tag
    FROM matches_1v1_clean m
)
SELECT * FROM p0_half
UNION ALL
SELECT * FROM p1_half
ORDER BY started_at, match_id, player_id\
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
# DESCRIBE matches_history_minimal; assert 8 columns + exact dtypes per spec.
# Expected: [VARCHAR, TIMESTAMP, VARCHAR, VARCHAR, VARCHAR, VARCHAR, BOOLEAN, VARCHAR]
# for columns [match_id, started_at, player_id, opponent_id, faction,
#              opponent_faction, won, dataset_tag].

# %%
describe_view = con.execute("DESCRIBE matches_history_minimal").fetchall()
view_col_names = [row[0] for row in describe_view]
view_col_types = [str(row[1]) for row in describe_view]

print(f"matches_history_minimal column count: {len(view_col_names)}")
for name, dtype in zip(view_col_names, view_col_types):
    print(f"  {name}: {dtype}")

# Assert 8 columns
assert len(view_col_names) == 8, (
    f"Expected 8 columns, got {len(view_col_names)}: {view_col_names}"
)

# Assert column names in order
expected_col_names = [
    "match_id", "started_at", "player_id", "opponent_id",
    "faction", "opponent_faction", "won", "dataset_tag",
]
assert view_col_names == expected_col_names, (
    f"Column name mismatch:\n  expected: {expected_col_names}\n  got:      {view_col_names}"
)

# Assert dtypes in order
expected_dtypes = [
    "VARCHAR", "TIMESTAMP", "VARCHAR", "VARCHAR",
    "VARCHAR", "VARCHAR", "BOOLEAN", "VARCHAR",
]
assert view_col_types == expected_dtypes, (
    f"Dtype mismatch:\n  expected: {expected_dtypes}\n  got:      {view_col_types}"
)

print("Schema shape validation PASSED: 8 cols + dtypes match spec.")

# %% [markdown]
# ## Cell 8 -- Row-count validation
#
# Gate: total_rows=35,629,894; distinct_match_ids=17,814,947; src_rows=17,814,947;
# matches_with_not_2_rows=0.
# aoestats: 17,814,947 source matches x 2 (UNION ALL pivot) = 35,629,894 rows.

# %%
ROW_COUNT_CHECK_SQL = """\
SELECT
    (SELECT COUNT(*) FROM matches_history_minimal)                  AS total_rows,
    (SELECT COUNT(DISTINCT match_id) FROM matches_history_minimal)  AS distinct_match_ids,
    (SELECT COUNT(*) FROM matches_1v1_clean)                        AS src_rows,
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
total_rows, distinct_match_ids, src_rows, matches_with_2_rows, matches_with_not_2_rows = rc

print(f"total_rows:              {total_rows}")
print(f"distinct_match_ids:      {distinct_match_ids}")
print(f"src_rows:                {src_rows}")
print(f"matches_with_2_rows:     {matches_with_2_rows}")
print(f"matches_with_not_2_rows: {matches_with_not_2_rows}")

assert total_rows == 35_629_894, f"Expected total_rows=35629894, got {total_rows}"
assert distinct_match_ids == 17_814_947, f"Expected distinct_match_ids=17814947, got {distinct_match_ids}"
assert src_rows == 17_814_947, f"Expected src_rows=17814947, got {src_rows}"
assert matches_with_not_2_rows == 0, f"Expected matches_with_not_2_rows=0, got {matches_with_not_2_rows}"

print("Row-count validation PASSED.")

# %% [markdown]
# ## Cell 9 -- Symmetry (I5-analog, NULL-safe)
#
# Gate: symmetry_violations=0. Uses IS DISTINCT FROM for NULL-safe comparison.
# UNION ALL pivot guarantees exact symmetry: p0_half player_id == p1_half opponent_id
# and vice versa, and won values are complementary.

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
        b.player_id         AS b_pid,
        b.opponent_id       AS b_oid,
        b.won               AS b_won,
        b.faction           AS b_fac,
        b.opponent_faction  AS b_ofac
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
   OR a_ofac IS DISTINCT FROM b_fac\
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
# Gate: null_faction / null_opponent_faction all 0 (A5: p{0,1}_civ empirically zero-NULL
#   in 1v1 ranked scope; gate enforces at runtime).
# null_started_at: report only.

# %%
ZERO_NULL_SQL = """\
SELECT
    COUNT(*) FILTER (WHERE match_id          IS NULL) AS null_match_id,
    COUNT(*) FILTER (WHERE started_at        IS NULL) AS null_started_at,
    COUNT(*) FILTER (WHERE player_id         IS NULL) AS null_player_id,
    COUNT(*) FILTER (WHERE opponent_id       IS NULL) AS null_opponent_id,
    COUNT(*) FILTER (WHERE won               IS NULL) AS null_won,
    COUNT(*) FILTER (WHERE dataset_tag       IS NULL) AS null_dataset_tag,
    COUNT(*) FILTER (WHERE faction           IS NULL) AS null_faction,
    COUNT(*) FILTER (WHERE opponent_faction  IS NULL) AS null_opponent_faction
FROM matches_history_minimal\
"""

null_row = con.execute(ZERO_NULL_SQL).fetchone()
(
    null_match_id, null_started_at, null_player_id, null_opponent_id,
    null_won, null_dataset_tag, null_faction, null_opponent_faction
) = null_row

print(f"null_match_id:          {null_match_id}")
print(f"null_started_at:        {null_started_at}  (report only)")
print(f"null_player_id:         {null_player_id}")
print(f"null_opponent_id:       {null_opponent_id}")
print(f"null_won:               {null_won}")
print(f"null_dataset_tag:       {null_dataset_tag}")
print(f"null_faction:           {null_faction}")
print(f"null_opponent_faction:  {null_opponent_faction}")

assert null_match_id == 0, f"null_match_id={null_match_id} (expected 0)"
assert null_player_id == 0, f"null_player_id={null_player_id} (expected 0)"
assert null_opponent_id == 0, f"null_opponent_id={null_opponent_id} (expected 0)"
assert null_won == 0, f"null_won={null_won} (expected 0)"
assert null_dataset_tag == 0, f"null_dataset_tag={null_dataset_tag} (expected 0)"
assert null_faction == 0, f"null_faction={null_faction} (expected 0)"
assert null_opponent_faction == 0, f"null_opponent_faction={null_opponent_faction} (expected 0)"

print("Zero-NULL validation PASSED for all 7 gated columns.")

# %% [markdown]
# ## Cell 11 -- match_id prefix verification
#
# Gate: prefix_violations=0.
# aoestats: game_id is VARCHAR (opaque -- no fixed length, no numeric regex).
# Prefix check: LIKE 'aoestats::%' AND non-empty tail after '::'.
# I7 provenance: game_id is VARCHAR passthrough per matches_1v1_clean.yaml.

# %%
PREFIX_CHECK_SQL = """\
-- game_id is VARCHAR (opaque primary key from aoestats API -- no fixed length).
-- No numeric-tail regex (unlike aoec INTEGER matchId) -- game_id may be any string.
-- Provenance: src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/
--             matches_1v1_clean.yaml column game_id type: VARCHAR (I7).
SELECT COUNT(*) AS prefix_violations
FROM matches_history_minimal
WHERE match_id NOT LIKE 'aoestats::%'
   OR regexp_extract(match_id, '::(.+)$', 1) = ''\
"""

prefix_row = con.execute(PREFIX_CHECK_SQL).fetchone()
prefix_violations = prefix_row[0]
print(f"prefix_violations: {prefix_violations}")

assert prefix_violations == 0, f"prefix_violations={prefix_violations} (expected 0)"

print("Prefix check PASSED.")

# %% [markdown]
# ## Cell 12 -- dataset_tag constant
#
# Gate: n_distinct_tags=1, the_tag='aoestats'.

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
assert the_tag == "aoestats", f"the_tag={the_tag!r} (expected 'aoestats')"

print("dataset_tag constant PASSED.")

# %% [markdown]
# ## Cell 13 -- Faction vocabulary (exploratory, no hard gate)
#
# Documents per-dataset polymorphism (I8). aoestats empirically ships full civ names
# (Mongols, Franks, etc. -- ~50 distinct values). NOT 4-char stems like sc2egset.
# No hard assertion -- exploratory per plan spec.

# %%
FACTION_VOCAB_SQL = """\
SELECT faction, COUNT(*) AS n
FROM matches_history_minimal
GROUP BY faction
ORDER BY n DESC\
"""

faction_rows = con.execute(FACTION_VOCAB_SQL).fetchall()
print("Faction vocabulary (per-dataset polymorphic, aoestats full civ names):")
for faction, n in faction_rows:
    print(f"  {faction!r}: {n}")

faction_vocab = {row[0]: row[1] for row in faction_rows}
print(f"\nTotal faction vocab size: {len(faction_vocab)} distinct values")
print("NOTE: aoestats faction vocabulary is full civilization names (Mongols, Franks, etc.).")
print("      Consumers MUST NOT treat faction as cross-dataset categorical without game-conditional encoding.")

# %% [markdown]
# ## Cell 14 -- Temporal sanity (I3)
#
# Report min/max started_at, null count, distinct count.
# TIMESTAMP ordering is chronologically faithful (CAST from TIMESTAMPTZ ensures this).

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
print(f"null_started_at:     {null_started_at_ts}  (CAST failures; expected 0)")
print(f"distinct_started_at: {distinct_started_at}")

# %% [markdown]
# ## Cell 14a -- SLOT-BIAS gate (aoestats-specific, I5-NEW)
#
# Gate: AVG(won::INT) == 0.5 exactly (tolerance 1e-9).
# Empirical rationale (A3 from plan): UNION ALL erases slot bias at output level.
# p0 slot wins ~47.73% (slot0_rate); p1 slot wins ~52.27% (slot1_rate).
# But every match contributes exactly 1 won=TRUE + 1 won=FALSE regardless of slot,
# so overall_won_rate = 0.5 exactly.
# This gate documents the UNION-erases-slot-bias property and serves as a
# regression guard for future DDL changes.

# %%
SLOT_BIAS_GATE_SQL = """\
SELECT
    AVG(won::INT)                                          AS overall_won_rate,
    AVG(won::INT) FILTER (WHERE player_id < opponent_id)  AS slot0_rate,
    AVG(won::INT) FILTER (WHERE player_id > opponent_id)  AS slot1_rate
FROM matches_history_minimal\
"""

bias_row = con.execute(SLOT_BIAS_GATE_SQL).fetchone()
overall_won_rate, slot0_rate, slot1_rate = bias_row
print(f"overall_won_rate: {overall_won_rate}")
print(f"slot0_rate:       {slot0_rate}  (informational -- p0_half rows)")
print(f"slot1_rate:       {slot1_rate}  (informational -- p1_half rows)")

assert abs(overall_won_rate - 0.5) < 1e-9, (
    f"SLOT-BIAS GATE FAILED: overall_won_rate={overall_won_rate} (expected 0.5 exactly)"
)

print("SLOT-BIAS gate PASSED: AVG(won::INT) == 0.5 exactly.")

# %% [markdown]
# ## Cell 15 -- game_id format sanity (informational)
#
# aoestats game_id is an opaque VARCHAR -- no fixed length, no numeric constraint.
# This cell reports the length distribution for documentation purposes only (no gate).
# I7 provenance: game_id is VARCHAR per matches_1v1_clean.yaml.

# %%
GAME_ID_FORMAT_SQL = """\
SELECT
    MIN(length(regexp_extract(match_id, '::(.+)$', 1))) AS min_tail_len,
    MAX(length(regexp_extract(match_id, '::(.+)$', 1))) AS max_tail_len,
    COUNT(DISTINCT regexp_extract(match_id, '::(.+)$', 1)) AS distinct_game_ids
FROM matches_history_minimal\
"""

fmt_row = con.execute(GAME_ID_FORMAT_SQL).fetchone()
min_tail_len, max_tail_len, distinct_game_ids = fmt_row
print(f"game_id tail min length:    {min_tail_len}")
print(f"game_id tail max length:    {max_tail_len}")
print(f"distinct game_ids:          {distinct_game_ids}  (expect == distinct_match_ids / 1)")
print("NOTE: game_id is opaque VARCHAR; no fixed-length gate applied (I7 provenance).")

# %% [markdown]
# ## Cell 16 -- Build validation JSON + assert all_assertions_pass
#
# Captures: step metadata, row_counts, assertion_results, sql_queries (verbatim I6),
# describe_table_rows (DESCRIBE output for nullable-flag reproducibility).

# %%
reports_dir = get_reports_dir("aoe2", "aoestats")
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
    "src_col_count_20": len(describe_src) == 20,
    "required_src_cols_present": all(c in src_col_names for c in required_cols),
    "col_count_8": len(view_col_names) == 8,
    "col_names_match": view_col_names == expected_col_names,
    "col_dtypes_match": view_col_types == expected_dtypes,
    "total_rows_35629894": total_rows == 35_629_894,
    "distinct_match_ids_17814947": distinct_match_ids == 17_814_947,
    "src_rows_17814947": src_rows == 17_814_947,
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
    "dataset_tag_aoestats": the_tag == "aoestats",
    "slot_bias_overall_05": abs(overall_won_rate - 0.5) < 1e-9,
}

all_assertions_pass = all(assertion_results.values())

validation = {
    "step": "01_04_03",
    "dataset": "aoestats",
    "game": "aoe2",
    "generated_date": str(date.today()),
    "view": "matches_history_minimal",
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
        "null_dataset_tag": null_dataset_tag,
        "null_faction": null_faction,
        "null_opponent_faction": null_opponent_faction,
    },
    "symmetry_violations": symmetry_violations,
    "prefix_violations": prefix_violations,
    "dataset_tag_distinct": n_distinct_tags,
    "dataset_tag_value": the_tag,
    "slot_bias": {
        "overall_won_rate": overall_won_rate,
        "slot0_rate": slot0_rate,
        "slot1_rate": slot1_rate,
        "gate_tolerance": 1e-9,
        "note": (
            "UNION ALL erases slot bias at output level: every match contributes "
            "1 won=TRUE + 1 won=FALSE. Upstream slot asymmetry (team=1 wins ~52.27%) "
            "is preserved at slot level but cancelled at aggregate level."
        ),
    },
    "temporal_sanity": {
        "min_started_at": str(min_started_at),
        "max_started_at": str(max_started_at),
        "null_started_at": null_started_at_ts,
        "distinct_started_at": distinct_started_at,
    },
    "game_id_format": {
        "min_tail_len": min_tail_len,
        "max_tail_len": max_tail_len,
        "distinct_game_ids": distinct_game_ids,
        "note": "game_id is opaque VARCHAR; no fixed-length gate (I7 provenance).",
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
        "PREFIX_CHECK_SQL": PREFIX_CHECK_SQL,
        "DATASET_TAG_CHECK_SQL": DATASET_TAG_CHECK_SQL,
        "SLOT_BIAS_GATE_SQL": SLOT_BIAS_GATE_SQL,
        "FACTION_VOCAB_SQL": FACTION_VOCAB_SQL,
        "TEMPORAL_SANITY_SQL": TEMPORAL_SANITY_SQL,
        "GAME_ID_FORMAT_SQL": GAME_ID_FORMAT_SQL,
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
    f"| `{faction}` | {n} |" for faction, n in faction_rows
)

md_content = f"""# Step 01_04_03 -- Minimal Cross-Dataset History View (aoestats)

**Generated:** {date.today()}
**Dataset:** aoestats
**Game:** AoE2
**Step:** 01_04_03
**Predecessor:** 01_04_02 (Data Cleaning Execution)

## Summary

Created `matches_history_minimal` VIEW -- 8-column player-row-grain view of
`matches_1v1_clean` (2 rows per 1v1 match via UNION ALL pivot). Canonical TIMESTAMP
temporal dtype (via CAST from TIMESTAMPTZ AT TIME ZONE 'UTC'). Per-dataset-polymorphic
faction vocabulary (full AoE2 civ names, ~50 distinct). Cross-dataset-harmonized
substrate for Phase 02+ rating-system backtesting. Pure non-destructive projection (I9).

aoestats-specific: UNION ALL erases slot bias -- overall_won_rate = 0.5 exactly
(upstream slot asymmetry team=1 wins ~52.27% preserved at slot level only).

## Schema (8 columns)

| column | dtype | semantics |
|---|---|---|
| `match_id` | VARCHAR | `'aoestats::'` + game_id (VARCHAR passthrough; opaque, variable length) |
| `started_at` | TIMESTAMP | CAST(started_timestamp AT TIME ZONE 'UTC' AS TIMESTAMP); canonical cross-dataset type |
| `player_id` | VARCHAR | CAST(p{{0,1}}_profile_id AS VARCHAR); focal player |
| `opponent_id` | VARCHAR | Opposing player |
| `faction` | VARCHAR | Full civ name (Mongols, Franks, etc.). PER-DATASET POLYMORPHIC |
| `opponent_faction` | VARCHAR | Opposing civ (same vocabulary as faction) |
| `won` | BOOLEAN | Focal player's outcome (complementary between the 2 rows) |
| `dataset_tag` | VARCHAR | Constant `'aoestats'` |

## Row-count flow

| metric | value |
|---|---|
| Source matches_1v1_clean rows (1/match) | {src_rows} |
| matches_history_minimal total rows (2/match) | {total_rows} |
| distinct match_ids | {distinct_match_ids} |
| matches with exactly 2 rows | {matches_with_2_rows} |
| matches with NOT 2 rows | {matches_with_not_2_rows} |

## Slot-bias gate (aoestats-specific)

| metric | value |
|---|---|
| overall_won_rate (GATE: == 0.5) | {overall_won_rate} |
| slot0_rate (informational) | {slot0_rate} |
| slot1_rate (informational) | {slot1_rate} |

UNION ALL erases slot bias: every match contributes 1 won=TRUE + 1 won=FALSE.

## Faction vocabulary (per-dataset polymorphic, top rows shown in full table)

| faction | count |
|---|---|
{faction_table_rows}

NOTE: aoestats faction vocabulary is full AoE2 civilization names.
Consumers MUST NOT treat faction as a single categorical feature across
datasets without game-conditional encoding.

## Temporal sanity (I3)

| metric | value |
|---|---|
| min_started_at | {min_started_at} |
| max_started_at | {max_started_at} |
| null_started_at (CAST failures) | {null_started_at_ts} |
| distinct_started_at | {distinct_started_at} |

## NULL counts

| column | null count | gate |
|---|---|---|
| match_id | {null_match_id} | 0 (GATE) |
| started_at | {null_started_at} | report only |
| player_id | {null_player_id} | 0 (GATE) |
| opponent_id | {null_opponent_id} | 0 (GATE) |
| won | {null_won} | 0 (GATE) |
| dataset_tag | {null_dataset_tag} | 0 (GATE) |
| faction | {null_faction} | 0 (GATE) |
| opponent_faction | {null_opponent_faction} | 0 (GATE) |

## Gate verdict

| check | result |
|---|---|
| Row count 35,629,894 = 2 x 17,814,947 | {'PASS' if total_rows == 35_629_894 and distinct_match_ids == 17_814_947 else 'FAIL'} |
| Column count 8 | {'PASS' if len(view_col_names) == 8 else 'FAIL'} |
| started_at dtype TIMESTAMP | {'PASS' if 'TIMESTAMP' in view_col_types[1] else 'FAIL'} |
| I5-analog NULL-safe symmetry violations = 0 | {'PASS' if symmetry_violations == 0 else 'FAIL'} |
| match_id prefix violations = 0 | {'PASS' if prefix_violations == 0 else 'FAIL'} |
| dataset_tag distinct count = 1 | {'PASS' if n_distinct_tags == 1 else 'FAIL'} |
| Zero NULLs in 7 gated columns | {'PASS' if null_match_id == null_player_id == null_opponent_id == null_won == null_dataset_tag == null_faction == null_opponent_faction == 0 else 'FAIL'} |
| SLOT-BIAS: AVG(won::INT) == 0.5 (tolerance 1e-9) | {'PASS' if abs(overall_won_rate - 0.5) < 1e-9 else 'FAIL'} |
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
# Nullable flags sourced from DESCRIBE result.
# DuckDB DESCRIBE 6-tuple contract: (column_name, column_type, null, key, default, extra).
# Index 2 is the null flag: 'YES' -> nullable=True, 'NO' -> nullable=False.
# Concrete Python booleans written -- no '<from DESCRIBE>' string literals.

# %%
schema_dir = reports_dir.parent / "data" / "db" / "schemas" / "views"
schema_dir.mkdir(parents=True, exist_ok=True)

yaml_path = schema_dir / "matches_history_minimal.yaml"

# Translate DESCRIBE nullable flags to concrete Python booleans
describe_rows_for_yaml = con.execute("DESCRIBE matches_history_minimal").fetchall()
nullable_map = {row[0]: (row[2] == "YES") for row in describe_rows_for_yaml}

schema = {
    "table": "matches_history_minimal",
    "dataset": "aoestats",
    "game": "aoe2",
    "object_type": "view",
    "step": "01_04_03",
    "row_count": total_rows,
    "describe_artifact": (
        "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts"
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
                "For aoestats: 'aoestats::<game_id>' where game_id is an opaque VARCHAR "
                "(variable length, no fixed-length constraint). Prefix guarantees UNION ALL "
                "uniqueness across sibling datasets. Provenance: game_id is VARCHAR per "
                "src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/"
                "matches_1v1_clean.yaml (I7 -- no numeric regex applied)."
            ),
            "notes": "IDENTITY. Prefix applied in this VIEW only; upstream game_id unchanged (I9).",
        },
        {
            "name": "started_at",
            "type": "TIMESTAMP",
            "nullable": nullable_map["started_at"],
            "description": (
                "Match start time. TIMESTAMP (no TZ) via "
                "CAST(started_timestamp AT TIME ZONE 'UTC' AS TIMESTAMP). "
                "Upstream matches_1v1_clean.started_timestamp is TIMESTAMP WITH TIME ZONE "
                "(TIMESTAMPTZ); the AT TIME ZONE 'UTC' + CAST yields a naive UTC TIMESTAMP "
                "consistent with the canonical cross-dataset dtype. Canonical cross-dataset "
                "dtype: sc2egset uses TRY_CAST from VARCHAR; aoestats uses explicit TZ cast; "
                "aoe2companion passes through TIMESTAMP directly."
            ),
            "notes": (
                "CONTEXT. Temporal anchor for Phase 02 rating-update loops. "
                "Chronologically faithful (TIMESTAMP ordering; upstream TIMESTAMPTZ preserved semantics)."
            ),
        },
        {
            "name": "player_id",
            "type": "VARCHAR",
            "nullable": nullable_map["player_id"],
            "description": (
                "Focal player identifier. aoestats: CAST(p{0,1}_profile_id AS VARCHAR) "
                "(upstream BIGINT). Identifies the AoE2 profile for this player-row."
            ),
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
                "Focal player's faction. **Per-dataset polymorphic vocabulary** "
                "(cross-dataset column name + dtype only -- values differ in ontology). "
                "sc2egset: 4-char race stems Prot/Terr/Zerg. "
                "aoestats: full civilization names (Mongols, Franks, etc. -- ~50 distinct). "
                "aoe2companion: full civilization names. "
                "CONSUMERS MUST NOT treat faction as a single categorical feature across "
                "datasets without game-conditional encoding (e.g., WHERE dataset_tag = 'aoestats' "
                "before GROUP BY faction)."
            ),
            "notes": "PRE_GAME. Full civilization name from p{0,1}_civ. Polymorphic I8 contract -- see description.",
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
                "complementary `won` values (exactly one TRUE, one FALSE). "
                "UNION ALL erases upstream slot asymmetry (team=1 wins ~52.27% upstream): "
                "overall AVG(won::INT) == 0.5 exactly (slot-bias gate verified in 01_04_03)."
            ),
            "notes": (
                "TARGET. Direct projection of p{0,1}_winner from matches_1v1_clean. "
                "Prediction label for downstream experiments."
            ),
        },
        {
            "name": "dataset_tag",
            "type": "VARCHAR",
            "nullable": False,
            "description": (
                "Dataset discriminator for UNION ALL across sibling datasets. "
                "Constant 'aoestats' in this VIEW."
            ),
            "notes": "IDENTITY. Matches the prefix before '::' in match_id.",
        },
    ],
    "provenance": {
        "source_tables": ["matches_1v1_clean"],
        "join_key": (
            "UNION ALL pivot: p0_half uses (game_id, p0_profile_id as player_id, "
            "p1_profile_id as opponent_id, p0_civ, p0_winner); "
            "p1_half mirrors the assignment."
        ),
        "filter": (
            "Inherited from matches_1v1_clean: ranked 1v1 decisive (leaderboard=random_map, "
            "2 players, p0_winner != p1_winner). 17,814,947 source matches."
        ),
        "scope": (
            "17,814,947 matches x 2 rows = 35,629,894 player-rows. "
            "Cross-dataset harmonization substrate for Phase 02+ rating backtesting."
        ),
        "created_by": (
            "sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_03_minimal_history_view.py"
        ),
    },
    "invariants": [
        {
            "id": "I3",
            "description": (
                "TIMESTAMP-typed temporal anchor enables chronologically faithful ordering. "
                "Upstream started_timestamp is TIMESTAMPTZ; CAST(... AT TIME ZONE 'UTC' AS TIMESTAMP) "
                "yields a naive UTC TIMESTAMP. Phase 02 consumers use started_at as the "
                "strict-less-than anchor for match_time < T feature computation."
            ),
        },
        {
            "id": "I5",
            "description": (
                "Player-row symmetry (I5-analog). Every match_id has exactly 2 rows. "
                "(player_id, opponent_id) appears once in each direction. The two `won` "
                "values are complementary. faction and opponent_faction are mirror images. "
                "Assertion SQL uses IS DISTINCT FROM for NULL-safe comparison. "
                "aoestats-specific SLOT-BIAS gate: AVG(won::INT) == 0.5 exactly (tolerance 1e-9) -- "
                "UNION ALL erases upstream slot asymmetry (team=1 wins ~52.27% in source)."
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
                "game_id is VARCHAR (opaque API key; no fixed-length magic literal). "
                "Provenance: matches_1v1_clean.yaml column game_id type: VARCHAR. "
                "PREFIX_CHECK_SQL uses LIKE 'aoestats::%' + non-empty tail regex only "
                "(no numeric constraint, unlike aoe2companion INTEGER matchId)."
            ),
        },
        {
            "id": "I8",
            "description": (
                "Cross-dataset comparability: 8-column names + dtypes are the cross-dataset "
                "contract. Canonical temporal dtype = TIMESTAMP (no TZ). Faction vocabulary "
                "is per-dataset-polymorphic -- column name and dtype cross-dataset, values "
                "per-dataset ontology. aoestats uses full civ names; sc2egset uses 4-char "
                "race stems. match_id prefixed 'aoestats::'."
            ),
        },
        {
            "id": "I9",
            "description": (
                "Pure non-destructive projection. No raw table modified. matches_1v1_clean "
                "unchanged. Only matches_history_minimal VIEW created via CREATE OR REPLACE. "
                "Input (matches_1v1_clean) read-only."
            ),
        },
    ],
    "provenance_categories_note": (
        "This view inherits provenance categories from matches_1v1_clean. Per-column "
        "'notes' field uses the single-token vocabulary (IDENTITY, CONTEXT, PRE_GAME, "
        "TARGET) established in 01_04_02."
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

print("\n=== FINAL SUMMARY: Step 01_04_03 (aoestats) ===")
print(f"VIEW created:          matches_history_minimal")
print(f"Rows:                  {total_rows} ({distinct_match_ids} matches x 2)")
print(f"Schema:                {len(view_col_names)} cols, started_at dtype: {view_col_types[1]}")
print(f"Symmetry violations:   {symmetry_violations}")
print(f"Prefix violations:     {prefix_violations}")
print(f"dataset_tag distinct:  {n_distinct_tags}")
print(f"overall_won_rate:      {overall_won_rate}  (SLOT-BIAS gate; expected 0.5 exactly)")
print(f"slot0_rate:            {slot0_rate}  (informational)")
print(f"slot1_rate:            {slot1_rate}  (informational)")
print(f"Faction vocab size:    {len(faction_vocab)} distinct civs")
print(f"All assertions pass:   {all_assertions_pass}")
print(f"\nArtifacts:")
print(f"  {json_path}")
print(f"  {md_path}")
print(f"  {yaml_path}")
