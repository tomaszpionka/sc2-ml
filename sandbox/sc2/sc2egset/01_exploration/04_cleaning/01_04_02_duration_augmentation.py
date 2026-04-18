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
# # Step 01_04_02 ADDENDUM -- Duration Augmentation (matches_flat_clean 28 → 30 cols)
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_04 -- Data Cleaning
# **Dataset:** sc2egset
# **Step scope:** ADDENDUM to 01_04_02. Extends `matches_flat_clean` VIEW from 28 → 30
# columns by adding `duration_seconds` (POST_GAME_HISTORICAL) and `is_duration_suspicious`
# (POST_GAME_HISTORICAL). Source: `player_history_all.header_elapsedGameLoops` aggregated
# per replay_id / 22.4 (SC2 "Faster" loops/sec constant, I7). No row changes (I9).
# STEP_STATUS stays complete per addendum precedent (01_04_03 ADDENDUM pattern).
# **Invariants applied:**
#   - I3 (POST_GAME_HISTORICAL tokens on both new cols -- excluded from PRE_GAME features)
#   - I5 (symmetry: both rows per replay have identical duration_seconds + is_duration_suspicious)
#   - I6 (all DDL + assertions SQL stored verbatim in artifact)
#   - I7 (22.4 loops/sec derived from details.gameSpeed cardinality=1 census, research_log.md:424)
#   - I8 (86_400s threshold identical across sc2egset, aoestats, aoe2companion)
#   - I9 (non-destructive: raw tables untouched; only matches_flat_clean VIEW replaced)
# **Predecessor:** 01_04_02 (complete), 01_04_03 ADDENDUM (established 22.4 and source pattern)
# **Date:** 2026-04-18
# **ROADMAP ref:** 01_04_02 ADDENDUM (duration augmentation)

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
# ## Cell 2 -- DuckDB Connection (writable -- replaces matches_flat_clean VIEW)
#
# Writable connection required to execute CREATE OR REPLACE VIEW.
# WARNING: Close all other open connections to this DuckDB before running.

# %%
db = get_notebook_db("sc2", "sc2egset", read_only=False)
con = db.con
print("DuckDB connection opened (read-write).")

# %% [markdown]
# ## Cell 3 -- Pre-augmentation baseline counts
#
# Capture current column count (28) and row count (44,418) before DDL.
# Assertions ensure starting state is correct.

# %%
pre_cols = con.execute("DESCRIBE matches_flat_clean").df()
pre_rows = con.execute(
    "SELECT COUNT(*) AS rows, COUNT(DISTINCT replay_id) AS replays FROM matches_flat_clean"
).fetchone()

print(f"Pre-augmentation matches_flat_clean: {len(pre_cols)} cols, {pre_rows[0]} rows, {pre_rows[1]} replays")
print(f"Column names: {pre_cols['column_name'].tolist()}")
# Allow 28 (fresh) or 30 (already augmented -- idempotent re-run)
assert len(pre_cols) in (28, 30), f"Expected 28 or 30 cols, got {len(pre_cols)}"
assert pre_rows[0] == 44418, f"Expected 44418 rows, got {pre_rows[0]}"
assert pre_rows[1] == 22209, f"Expected 22209 replays, got {pre_rows[1]}"
if len(pre_cols) == 30:
    print("NOTE: VIEW already at 30 cols (idempotent re-run). CREATE OR REPLACE will re-apply.")
print("Pre-augmentation baseline assertions PASSED.")

# %% [markdown]
# ## Cell 4 -- Define DDL: matches_flat_clean v3 (28 → 30 cols)
#
# Strategy: wrap entire existing v2 DDL as `v2_base` CTE, add `duration_per_replay`
# CTE that aggregates player_history_all.header_elapsedGameLoops per replay_id,
# then LEFT JOIN + append duration_seconds + is_duration_suspicious.
#
# I7 provenance for 22.4 loops/sec:
#   - details.gameSpeed cardinality=1 in sc2egset (W02 census, research_log.md:424)
#   - Blizzard SC2 "Faster" game speed = 22.4 loops/sec (official documentation)
#   - Established in 01_04_03 ADDENDUM (matches_history_minimal duration_seconds derivation)
#
# I8 provenance for 86_400s threshold:
#   - Cross-dataset canonical sanity bound (~25x p99 for sc2egset)
#   - Identical across sc2egset, aoestats, aoe2companion per plan A1 + I8

# %%
CREATE_MATCHES_FLAT_CLEAN_V3_SQL = """
CREATE OR REPLACE VIEW matches_flat_clean AS
-- Purpose: Prediction-target VIEW. True 1v1 decisive replays only.
-- Row multiplicity: 2 rows per replay (1 Win + 1 Loss), invariant I5.
-- Column set: 30 PRE_GAME + IDENTITY + TARGET + POST_GAME_HISTORICAL columns (I3).
-- v3 ADDENDUM (2026-04-18): added duration_seconds + is_duration_suspicious.
-- All prior 21 dropped columns documented in 01_04_02_post_cleaning_validation.json.
WITH true_1v1_decisive AS (
    -- only replays with exactly 2 players, 1 Win + 1 Loss
    SELECT replay_id
    FROM matches_flat
    GROUP BY replay_id
    HAVING COUNT(*) = 2
       AND COUNT(*) FILTER (WHERE result = 'Win') = 1
       AND COUNT(*) FILTER (WHERE result = 'Loss') = 1
),
mmr_valid AS (
    -- replay-level exclusion: any replay with MMR<0 player excluded entirely.
    -- If ANY player has MMR < 0, the ENTIRE replay is excluded.
    -- Prevents orphaned opponent rows that would break the 2-per-replay invariant.
    SELECT replay_id
    FROM matches_flat
    GROUP BY replay_id
    HAVING COUNT(*) FILTER (WHERE MMR < 0) = 0
),
v2_base AS (
    SELECT
        -- Identity (6 cols)
        mf.replay_id,
        mf.filename,
        mf.toon_id,
        mf.nickname,
        mf.playerID,
        mf.userID,

        -- Target (1 col)
        mf.result,

        -- Pre-game player features (DS-SC2-01: MMR DROPPED; is_mmr_missing RETAINED)
        CASE WHEN mf.MMR = 0 THEN TRUE ELSE FALSE END AS is_mmr_missing,
        mf.race,
        CASE WHEN mf.selectedRace = '' THEN 'Random'
             ELSE mf.selectedRace END AS selectedRace,

        -- DS-SC2-09: handicap DROPPED (near-constant: 2 anomalies in 44k)
        -- DS-SC2-09: is_handicap_anomalous DROPPED (flag meaningless without column)
        mf.region,
        mf.realm,
        -- DS-SC2-02: highestLeague DROPPED (72.04% sentinel rate, Rule S4)
        mf.isInClan,
        -- DS-SC2-03: clanTag DROPPED (73.93% sentinel rate, Rule S4; isInClan retained)

        -- Pre-game spatial
        mf.startDir,
        mf.startLocX,
        mf.startLocY,

        -- Pre-game map metadata
        mf.metadata_mapName,
        -- DS-SC2-06: gd_mapSizeX DROPPED (redundant with mapName; retained in player_history_all)
        -- DS-SC2-06: gd_mapSizeY DROPPED (same)
        -- DS-SC2-06: is_map_size_missing DROPPED (flag meaningless without columns)
        mf.gd_maxPlayers,
        -- DS-SC2-07: gd_mapAuthorName DROPPED (non-predictive metadata; domain-judgement override)
        mf.gd_mapFileSyncChecksum,

        -- Pre-game Blizzard map flag
        mf.details_isBlizzardMap,

        -- Pre-game temporal anchor
        mf.details_timeUTC,

        -- Pre-game version context
        mf.header_version,
        mf.metadata_baseBuild,
        mf.metadata_dataBuild,
        mf.metadata_gameVersion,

        -- Pre-game game options (variable cardinality only; 12 constants DROPPED per DS-SC2-08)
        -- DS-SC2-08: go_advancedSharedControl DROPPED (n_distinct=1)
        mf.go_amm,
        -- DS-SC2-08: go_battleNet DROPPED (n_distinct=1)
        mf.go_clientDebugFlags,
        mf.go_competitive
        -- DS-SC2-08: go_cooperative DROPPED (n_distinct=1)
        -- DS-SC2-08: go_fog DROPPED (n_distinct=1)
        -- DS-SC2-08: go_heroDuplicatesAllowed DROPPED (n_distinct=1)
        -- DS-SC2-08: go_lockTeams DROPPED (n_distinct=1)
        -- DS-SC2-08: go_noVictoryOrDefeat DROPPED (n_distinct=1)
        -- DS-SC2-08: go_observers DROPPED (n_distinct=1)
        -- DS-SC2-08: go_practice DROPPED (n_distinct=1)
        -- DS-SC2-08: go_randomRaces DROPPED (n_distinct=1)
        -- DS-SC2-08: go_teamsTogether DROPPED (n_distinct=1)
        -- DS-SC2-08: go_userDifficulty DROPPED (n_distinct=1)

    FROM matches_flat mf
    JOIN true_1v1_decisive t1v1 ON mf.replay_id = t1v1.replay_id
    JOIN mmr_valid mv ON mf.replay_id = mv.replay_id
),
duration_per_replay AS (
    -- Aggregate header_elapsedGameLoops per replay_id from player_history_all.
    -- player_history_all retains header_elapsedGameLoops (IN_GAME_HISTORICAL);
    -- matches_flat_clean and matches_long_raw both exclude it per I3.
    -- Both rows per replay share the same loops value (symmetry verified below).
    -- 22.4 loops/sec: SC2 "Faster" game-speed constant (I7 provenance:
    --   details.gameSpeed cardinality=1 in sc2egset, research_log.md:424;
    --   Blizzard SC2 documentation).
    SELECT
        replay_id,
        CAST(ANY_VALUE(header_elapsedGameLoops) / 22.4 AS BIGINT) AS duration_seconds
    FROM player_history_all
    WHERE replay_id IS NOT NULL
    GROUP BY replay_id
)
SELECT
    v2.*,
    -- POST_GAME_HISTORICAL: game duration derived from header_elapsedGameLoops.
    -- SAFE as player-history aggregate (match_time < T) in Phase 02; UNSAFE as
    -- direct game-T feature. Excluded from PRE_GAME feature sets by I3 token filter.
    dpr.duration_seconds,
    -- POST_GAME_HISTORICAL: TRUE where duration_seconds > 86400s (24h sanity bound).
    -- Threshold: ~25x p99 of sc2egset distribution (p99=1,876s, max=6,073s);
    -- identical across sc2egset, aoestats, aoe2companion (I8 cross-dataset comparability).
    -- Expected 0 suspicious rows for sc2egset (01_04_03 ADDENDUM confirmed max=6,073s).
    (dpr.duration_seconds > 86400) AS is_duration_suspicious
FROM v2_base v2
LEFT JOIN duration_per_replay dpr ON v2.replay_id = dpr.replay_id;
"""

print("matches_flat_clean v3 DDL defined.")
print("Expected output: 30 columns, 44418 rows, 22209 replays.")

# %% [markdown]
# ## Cell 5 -- Execute DDL: replace matches_flat_clean VIEW

# %%
con.execute(CREATE_MATCHES_FLAT_CLEAN_V3_SQL)
print("matches_flat_clean VIEW replaced (v3 -- 30 cols).")

# %% [markdown]
# ## Cell 6 -- Gate 1+2: Column count = 30; last 2 are duration_seconds BIGINT + is_duration_suspicious BOOLEAN

# %%
DESCRIBE_SQL = "DESCRIBE matches_flat_clean"
post_cols = con.execute(DESCRIBE_SQL).df()
col_names = post_cols["column_name"].tolist()
col_types = dict(zip(post_cols["column_name"], post_cols["column_type"]))

print(f"Post-augmentation col count: {len(post_cols)}")
print(f"Last 2 cols: {col_names[-2:]}")
print(f"Types: {col_types[col_names[-2]]}, {col_types[col_names[-1]]}")

assert len(post_cols) == 30, f"Gate 1 FAIL: expected 30 cols, got {len(post_cols)}"
assert col_names[-2] == "duration_seconds", f"Gate 2 FAIL: expected duration_seconds at pos -2, got {col_names[-2]}"
assert col_names[-1] == "is_duration_suspicious", f"Gate 2 FAIL: expected is_duration_suspicious at pos -1, got {col_names[-1]}"
assert col_types["duration_seconds"] == "BIGINT", f"Gate 2 FAIL: expected BIGINT, got {col_types['duration_seconds']}"
assert col_types["is_duration_suspicious"] == "BOOLEAN", f"Gate 2 FAIL: expected BOOLEAN, got {col_types['is_duration_suspicious']}"
print("Gate 1 PASS: 30 cols")
print("Gate 2 PASS: last 2 cols = duration_seconds BIGINT + is_duration_suspicious BOOLEAN")

# %% [markdown]
# ## Cell 7 -- Gate 3: Row count 44,418 (unchanged)

# %%
ROW_COUNT_SQL = "SELECT COUNT(*) AS rows, COUNT(DISTINCT replay_id) AS replays FROM matches_flat_clean"
post_rows = con.execute(ROW_COUNT_SQL).fetchone()
print(f"Post-augmentation: {post_rows[0]} rows, {post_rows[1]} replays")
assert post_rows[0] == 44418, f"Gate 3 FAIL: expected 44418 rows, got {post_rows[0]}"
assert post_rows[1] == 22209, f"Gate 3 FAIL: expected 22209 replays, got {post_rows[1]}"
print("Gate 3 PASS: row count 44,418 unchanged")

# %% [markdown]
# ## Cell 8 -- Gate 4: duration_seconds NULL count = 0

# %%
NULL_DURATION_SQL = "SELECT COUNT(*) FILTER (WHERE duration_seconds IS NULL) AS null_count FROM matches_flat_clean"
r_null = con.execute(NULL_DURATION_SQL).fetchone()
print(f"duration_seconds NULL count: {r_null[0]}")
assert r_null[0] == 0, f"Gate 4 FAIL: expected 0 NULLs, got {r_null[0]}"
print("Gate 4 PASS: duration_seconds NULL count = 0")

# %% [markdown]
# ## Cell 9 -- Gate 5: MAX(duration_seconds) <= 1_000_000_000 (unit regression canary)

# %%
DURATION_STATS_SQL = """
SELECT
    MIN(duration_seconds) AS min_sec,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_seconds) AS p50_sec,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_seconds) AS p99_sec,
    MAX(duration_seconds) AS max_sec,
    COUNT(*) FILTER (WHERE is_duration_suspicious = TRUE) AS suspicious_count,
    COUNT(*) FILTER (WHERE duration_seconds IS NULL) AS null_count
FROM matches_flat_clean
"""
r_stats = con.execute(DURATION_STATS_SQL).fetchone()
print(f"Duration stats: min={r_stats[0]}, p50={r_stats[1]}, p99={r_stats[2]}, max={r_stats[3]}")
print(f"suspicious_count (>86400s)={r_stats[4]}, null_count={r_stats[5]}")
assert r_stats[3] <= 1_000_000_000, f"Gate 5 FAIL: MAX duration {r_stats[3]} > unit canary 1e9"
print("Gate 5 PASS: MAX(duration_seconds) <= 1_000_000_000")

# %% [markdown]
# ## Cell 10 -- Gate 6: I5 symmetry -- 0 IS DISTINCT FROM violations on new cols

# %%
SYMMETRY_DURATION_SQL = """
SELECT COUNT(*) AS violations
FROM (
    SELECT
        replay_id,
        MIN(duration_seconds) AS min_dur,
        MAX(duration_seconds) AS max_dur,
        MIN(CAST(is_duration_suspicious AS INTEGER)) AS min_susp,
        MAX(CAST(is_duration_suspicious AS INTEGER)) AS max_susp
    FROM matches_flat_clean
    GROUP BY replay_id
    HAVING min_dur IS DISTINCT FROM max_dur
        OR min_susp IS DISTINCT FROM max_susp
)
"""
r_sym = con.execute(SYMMETRY_DURATION_SQL).fetchone()
print(f"I5 symmetry violations on duration cols: {r_sym[0]}")
assert r_sym[0] == 0, f"Gate 6 FAIL: {r_sym[0]} symmetry violations on duration cols"
print("Gate 6 PASS: 0 IS DISTINCT FROM violations (I5 symmetry holds)")

# %% [markdown]
# ## Cell 11 -- Gate 6b (extra): suspicious count = 0 (sc2egset-specific HALTING gate)
#
# 01_04_03 ADDENDUM confirmed sc2egset max=6,073s (well below 86,400s).
# Expected 0 suspicious rows for sc2egset.

# %%
SUSPICIOUS_COUNT_SQL = "SELECT COUNT(*) FILTER (WHERE is_duration_suspicious = TRUE) AS cnt FROM matches_flat_clean"
r_susp = con.execute(SUSPICIOUS_COUNT_SQL).fetchone()
print(f"is_duration_suspicious = TRUE count: {r_susp[0]}")
assert r_susp[0] == 0, f"Gate 6b FAIL: expected 0 suspicious rows, got {r_susp[0]}"
print("Gate 6b PASS: is_duration_suspicious count = 0 (no outliers in sc2egset)")

# %% [markdown]
# ## Cell 12 -- Re-run I3/I5 baseline assertions (regression guard)
#
# Ensure the VIEW replacement didn't disturb existing integrity.

# %%
BASELINE_ASSERTIONS_SQL = """
SELECT
    COUNT(*) FILTER (WHERE replay_id IS NULL) AS null_replay_id,
    COUNT(*) FILTER (WHERE toon_id IS NULL) AS null_toon_id,
    COUNT(*) FILTER (WHERE result IS NULL) AS null_result,
    COUNT(*) FILTER (WHERE result NOT IN ('Win', 'Loss')) AS non_decisive
FROM matches_flat_clean
"""
r_base = con.execute(BASELINE_ASSERTIONS_SQL).fetchone()
print(f"Baseline: null_replay_id={r_base[0]}, null_toon_id={r_base[1]}, null_result={r_base[2]}, non_decisive={r_base[3]}")
assert r_base[0] == 0, f"Regression: replay_id NULLs found"
assert r_base[1] == 0, f"Regression: toon_id NULLs found"
assert r_base[2] == 0, f"Regression: result NULLs found"
assert r_base[3] == 0, f"Regression: non-decisive results found"

SYMMETRY_SQL = """
SELECT COUNT(*) AS replays_not_symmetric
FROM (
    SELECT replay_id,
           COUNT(*) FILTER (WHERE result = 'Win') AS wins,
           COUNT(*) FILTER (WHERE result = 'Loss') AS losses
    FROM matches_flat_clean
    GROUP BY replay_id
    HAVING wins != 1 OR losses != 1
)
"""
r_sym_base = con.execute(SYMMETRY_SQL).fetchone()
print(f"I5 baseline symmetry violations: {r_sym_base[0]}")
assert r_sym_base[0] == 0, f"Regression: I5 symmetry violated"
print("All baseline regression assertions PASSED.")

# %% [markdown]
# ## Cell 13 -- Forbidden-column regression (header_elapsedGameLoops absent from matches_flat_clean)
#
# Ensures I3 is preserved: IN_GAME_HISTORICAL columns not directly exposed.

# %%
col_names_set = set(post_cols["column_name"])
FORBIDDEN_I3 = {"header_elapsedGameLoops", "APM", "SQ", "supplyCappedPercent"}
violations_i3 = FORBIDDEN_I3 & col_names_set
assert len(violations_i3) == 0, f"I3 regression: forbidden IN_GAME cols present: {violations_i3}"
print(f"I3 regression PASS: no IN_GAME_HISTORICAL cols directly in matches_flat_clean. {FORBIDDEN_I3} all absent.")

# %% [markdown]
# ## Cell 14 -- Build and write artifact JSON

# %%
reports_dir = get_reports_dir("sc2", "sc2egset")
artifact_dir = reports_dir / "artifacts" / "01_exploration" / "04_cleaning"
artifact_dir.mkdir(parents=True, exist_ok=True)

duration_stats = {
    "min_seconds": int(r_stats[0]),
    "p50_seconds": float(r_stats[1]),
    "p99_seconds": float(r_stats[2]),
    "max_seconds": int(r_stats[3]),
    "null_count": int(r_stats[5]),
    "suspicious_count_gt_86400": int(r_stats[4]),
}

validation_assertions = {
    "gate_1_col_count_30": bool(len(post_cols) == 30),
    "gate_2_last_col_duration_seconds_bigint": bool(
        col_names[-2] == "duration_seconds" and col_types["duration_seconds"] == "BIGINT"
    ),
    "gate_2_last_col_is_duration_suspicious_boolean": bool(
        col_names[-1] == "is_duration_suspicious" and col_types["is_duration_suspicious"] == "BOOLEAN"
    ),
    "gate_3_row_count_44418": bool(post_rows[0] == 44418),
    "gate_4_null_duration_seconds_zero": bool(r_null[0] == 0),
    "gate_5_max_duration_le_1e9": bool(r_stats[3] <= 1_000_000_000),
    "gate_6_symmetry_violations_zero": bool(r_sym[0] == 0),
    "gate_6b_suspicious_count_zero": bool(r_susp[0] == 0),
    "regression_zero_null_replay_id": bool(r_base[0] == 0),
    "regression_zero_null_toon_id": bool(r_base[1] == 0),
    "regression_zero_null_result": bool(r_base[2] == 0),
    "regression_zero_non_decisive": bool(r_base[3] == 0),
    "regression_i5_symmetry": bool(r_sym_base[0] == 0),
    "regression_i3_no_ingame_cols": bool(len(violations_i3) == 0),
}
all_pass = all(validation_assertions.values())

artifact = {
    "step": "01_04_02",
    "step_addendum": "duration_augmentation",
    "dataset": "sc2egset",
    "generated_date": "2026-04-18",
    "description": (
        "ADDENDUM to 01_04_02. Extends matches_flat_clean from 28 -> 30 cols by adding "
        "duration_seconds BIGINT (POST_GAME_HISTORICAL) + is_duration_suspicious BOOLEAN "
        "(POST_GAME_HISTORICAL). Source: player_history_all.header_elapsedGameLoops / 22.4 "
        "aggregated per replay_id. No row changes (I9). STEP_STATUS stays complete."
    ),
    "consort_flow_columns": {
        "matches_flat_clean": {
            "cols_before_addendum": 28,
            "cols_added": 2,
            "cols_after_addendum": 30,
        }
    },
    "duration_stats": duration_stats,
    "i7_provenance": {
        "divisor": 22.4,
        "unit": "SC2 Faster game-speed loops/sec",
        "source": (
            "details.gameSpeed cardinality=1 in sc2egset (W02 census, research_log.md:424); "
            "Blizzard SC2 'Faster' game speed = 22.4 loops/sec (official documentation). "
            "Established in 01_04_03 ADDENDUM (matches_history_minimal duration_seconds derivation)."
        ),
    },
    "i8_provenance": {
        "threshold_seconds": 86400,
        "justification": (
            "Cross-dataset canonical sanity bound (~25x p99 for sc2egset: p99=1,876s, max=6,073s). "
            "Identical across sc2egset, aoestats, aoe2companion per plan A1 + I8 cross-dataset comparability."
        ),
    },
    "all_assertions_pass": all_pass,
    "validation_assertions": validation_assertions,
    "sql_queries": {
        "create_matches_flat_clean_v3": CREATE_MATCHES_FLAT_CLEAN_V3_SQL,
        "describe": DESCRIBE_SQL,
        "row_count": ROW_COUNT_SQL,
        "null_duration": NULL_DURATION_SQL,
        "duration_stats": DURATION_STATS_SQL,
        "symmetry_duration": SYMMETRY_DURATION_SQL,
        "suspicious_count": SUSPICIOUS_COUNT_SQL,
        "baseline_assertions": BASELINE_ASSERTIONS_SQL,
        "symmetry_baseline": SYMMETRY_SQL,
    },
}

json_path = artifact_dir / "01_04_02_duration_augmentation.json"
with open(json_path, "w") as f:
    json.dump(artifact, f, indent=2)
print(f"Artifact JSON written: {json_path}")
print(f"All assertions pass: {all_pass}")
if not all_pass:
    failed = [k for k, v in validation_assertions.items() if not v]
    raise AssertionError(f"GATE FAILURE -- failed assertions: {failed}")

# %% [markdown]
# ## Cell 15 -- Write markdown report

# %%
assertion_rows = "\n".join(
    f"| {k} | {'PASS' if v else 'FAIL'} |"
    for k, v in validation_assertions.items()
)
assertion_table = "| Assertion | Status |\n|---|---|\n" + assertion_rows

md_content = f"""# Step 01_04_02 ADDENDUM -- Duration Augmentation (matches_flat_clean 28 → 30)

**Generated:** 2026-04-18
**Dataset:** sc2egset
**Step:** 01_04_02 ADDENDUM -- duration_seconds + is_duration_suspicious

## Summary

ADDENDUM to 01_04_02. Extends `matches_flat_clean` VIEW from 28 → 30 columns by adding:
- `duration_seconds` BIGINT (POST_GAME_HISTORICAL): game duration in seconds.
- `is_duration_suspicious` BOOLEAN (POST_GAME_HISTORICAL): TRUE where duration_seconds > 86,400s.

Source: `player_history_all.header_elapsedGameLoops` aggregated per `replay_id`, divided by 22.4
(SC2 "Faster" loops/sec constant, I7). No row changes (I9). STEP_STATUS stays `complete`.

## CONSORT Column-Count Flow

| VIEW | Cols before addendum | Cols added | Cols after addendum |
|---|---|---|---|
| matches_flat_clean | 28 | 2 | 30 |

## Duration Stats (sc2egset)

| Stat | Value |
|---|---|
| min_seconds | {duration_stats['min_seconds']} |
| p50_seconds | {duration_stats['p50_seconds']:.1f} |
| p99_seconds | {duration_stats['p99_seconds']:.1f} |
| max_seconds | {duration_stats['max_seconds']} |
| null_count | {duration_stats['null_count']} |
| suspicious_count (>86400s) | {duration_stats['suspicious_count_gt_86400']} |

## I7 Provenance (22.4 loops/sec)

- `details.gameSpeed` cardinality=1 in sc2egset (W02 census, research_log.md:424)
- Blizzard SC2 "Faster" game speed = 22.4 loops/sec (official documentation)
- Established in 01_04_03 ADDENDUM (matches_history_minimal duration_seconds derivation)

## I8 Provenance (86,400s threshold)

Cross-dataset canonical sanity bound (~25x p99 for sc2egset: p99=1,876s, max=6,073s).
Identical across sc2egset, aoestats, aoe2companion per plan A1 + I8 cross-dataset comparability.

## Validation Results

{assertion_table}

## SQL Queries (Invariant I6)

All DDL and assertion SQL stored verbatim in `01_04_02_duration_augmentation.json`
under the `sql_queries` key.
"""

md_path = artifact_dir / "01_04_02_duration_augmentation.md"
with open(md_path, "w") as f:
    f.write(md_content)
print(f"Markdown report written: {md_path}")

# %% [markdown]
# ## Cell 16 -- Gate 7: Update matches_flat_clean.yaml (30 cols + schema_version + I3/I7 updates)

# %%
# Derive schema_dir from reports_dir (avoids __file__ which is unavailable in notebooks)
# reports_dir is: src/rts_predict/games/sc2/datasets/sc2egset/reports
# schema_dir is:  src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views
schema_dir = reports_dir.parent / "data" / "db" / "schemas" / "views"
schema_path = schema_dir / "matches_flat_clean.yaml"

mfc_columns_yaml = [
    {
        "name": "replay_id", "type": "VARCHAR", "nullable": True,
        "description": "Canonical join key extracted via regexp. NULLIF empty-string guard applied.",
        "notes": "IDENTITY. Canonical join key extracted via regexp. NULLIF empty-string guard applied.",
    },
    {
        "name": "filename", "type": "VARCHAR", "nullable": True,
        "description": "Replay file path relative to raw_dir. Invariant I10.",
        "notes": "IDENTITY. Replay file path relative to raw_dir. Invariant I10.",
    },
    {
        "name": "toon_id", "type": "VARCHAR", "nullable": True,
        "description": "Battle.net toon/account identifier. Player identity key.",
        "notes": "IDENTITY. Battle.net toon/account identifier. Player identity key.",
    },
    {
        "name": "nickname", "type": "VARCHAR", "nullable": True,
        "description": "Player nickname.",
        "notes": "IDENTITY. Player nickname.",
    },
    {
        "name": "playerID", "type": "INTEGER", "nullable": True,
        "description": "In-game player id.",
        "notes": "IDENTITY. In-game player id.",
    },
    {
        "name": "userID", "type": "BIGINT", "nullable": True,
        "description": "User id.",
        "notes": "IDENTITY. User id.",
    },
    {
        "name": "result", "type": "VARCHAR", "nullable": True,
        "description": "Game result (Win or Loss only -- Undecided/Tie excluded by true_1v1_decisive CTE). Prediction target.",
        "notes": "TARGET. Game result (Win or Loss only -- Undecided/Tie excluded by true_1v1_decisive CTE). Prediction target.",
    },
    {
        "name": "is_mmr_missing", "type": "BOOLEAN", "nullable": True,
        "description": "TRUE if MMR=0 (unrated professional). MNAR. MMR dropped in 01_04_02 (DS-SC2-01); this flag preserves the rated/unrated signal.",
        "notes": "PRE_GAME. TRUE if MMR=0 (unrated professional). MNAR. MMR dropped in 01_04_02 (DS-SC2-01); this flag preserves the rated/unrated signal.",
    },
    {
        "name": "race", "type": "VARCHAR", "nullable": True,
        "description": "Actual race played (Protoss, Zerg, Terran abbreviated).",
        "notes": "PRE_GAME. Actual race played (Protoss, Zerg, Terran abbreviated).",
    },
    {
        "name": "selectedRace", "type": "VARCHAR", "nullable": True,
        "description": "Selected race. Empty string normalised to 'Random'.",
        "notes": "PRE_GAME. Selected race. Empty string normalised to 'Random'.",
    },
    {
        "name": "region", "type": "VARCHAR", "nullable": True,
        "description": "Battle.net region label.",
        "notes": "PRE_GAME. Battle.net region label.",
    },
    {
        "name": "realm", "type": "VARCHAR", "nullable": True,
        "description": "Realm label.",
        "notes": "PRE_GAME. Realm label.",
    },
    {
        "name": "isInClan", "type": "BOOLEAN", "nullable": True,
        "description": "Whether the player is in a clan.",
        "notes": "PRE_GAME. Whether the player is in a clan.",
    },
    {
        "name": "startDir", "type": "INTEGER", "nullable": True,
        "description": "Starting direction code (lobby assignment).",
        "notes": "PRE_GAME. Starting direction code (lobby assignment).",
    },
    {
        "name": "startLocX", "type": "INTEGER", "nullable": True,
        "description": "Starting x location on map.",
        "notes": "PRE_GAME. Starting x location on map.",
    },
    {
        "name": "startLocY", "type": "INTEGER", "nullable": True,
        "description": "Starting y location on map.",
        "notes": "PRE_GAME. Starting y location on map.",
    },
    {
        "name": "metadata_mapName", "type": "VARCHAR", "nullable": True,
        "description": "Human-readable map name.",
        "notes": "PRE_GAME. Human-readable map name.",
    },
    {
        "name": "gd_maxPlayers", "type": "BIGINT", "nullable": True,
        "description": "Max players in game description.",
        "notes": "PRE_GAME. Max players in game description.",
    },
    {
        "name": "gd_mapFileSyncChecksum", "type": "BIGINT", "nullable": True,
        "description": "Map file sync checksum.",
        "notes": "PRE_GAME. Map file sync checksum.",
    },
    {
        "name": "details_isBlizzardMap", "type": "BOOLEAN", "nullable": True,
        "description": "Blizzard-authored map flag (from details struct).",
        "notes": "PRE_GAME. Blizzard-authored map flag (from details struct).",
    },
    {
        "name": "details_timeUTC", "type": "VARCHAR", "nullable": True,
        "description": "UTC timestamp of game. Temporal anchor for I3 ordering.",
        "notes": "CONTEXT. UTC timestamp of game. Temporal anchor for I3 ordering.",
    },
    {
        "name": "header_version", "type": "VARCHAR", "nullable": True,
        "description": "SC2 version string.",
        "notes": "CONTEXT. SC2 version string.",
    },
    {
        "name": "metadata_baseBuild", "type": "VARCHAR", "nullable": True,
        "description": "Base build string.",
        "notes": "CONTEXT. Base build string.",
    },
    {
        "name": "metadata_dataBuild", "type": "VARCHAR", "nullable": True,
        "description": "Data build string.",
        "notes": "CONTEXT. Data build string.",
    },
    {
        "name": "metadata_gameVersion", "type": "VARCHAR", "nullable": True,
        "description": "Game version.",
        "notes": "CONTEXT. Game version.",
    },
    {
        "name": "go_amm", "type": "BOOLEAN", "nullable": True,
        "description": "Game option: automated match making. Variable cardinality (n_distinct=2).",
        "notes": "CONTEXT. Game option: automated match making. Variable cardinality (n_distinct=2).",
    },
    {
        "name": "go_clientDebugFlags", "type": "BIGINT", "nullable": True,
        "description": "Game option: client debug flags. Variable cardinality (n_distinct=2).",
        "notes": "CONTEXT. Game option: client debug flags. Variable cardinality (n_distinct=2).",
    },
    {
        "name": "go_competitive", "type": "BOOLEAN", "nullable": True,
        "description": "Game option: competitive mode. Variable cardinality (n_distinct=2).",
        "notes": "CONTEXT. Game option: competitive mode. Variable cardinality (n_distinct=2).",
    },
    {
        "name": "duration_seconds", "type": "BIGINT", "nullable": True,
        "description": (
            "Game duration in seconds. Derived from player_history_all.header_elapsedGameLoops / 22.4 "
            "(SC2 Faster loops/sec constant, I7) aggregated per replay_id. ADDENDUM 2026-04-18."
        ),
        "notes": (
            "POST_GAME_HISTORICAL. Game duration in seconds. Derived from "
            "player_history_all.header_elapsedGameLoops / 22.4 (I7: details.gameSpeed "
            "cardinality=1 in sc2egset, research_log.md:424; Blizzard SC2 Faster=22.4 loops/sec). "
            "SAFE as player-history aggregate (match_time < T). UNSAFE as direct game-T feature. "
            "Added in 01_04_02 ADDENDUM 2026-04-18."
        ),
    },
    {
        "name": "is_duration_suspicious", "type": "BOOLEAN", "nullable": True,
        "description": (
            "TRUE where duration_seconds > 86,400s (24h sanity bound). Expected 0 for sc2egset "
            "(max=6,073s confirmed by 01_04_03 ADDENDUM). Threshold identical across sc2egset, "
            "aoestats, aoe2companion (I8). ADDENDUM 2026-04-18."
        ),
        "notes": (
            "POST_GAME_HISTORICAL. TRUE where duration_seconds > 86400s. Threshold: ~25x p99 "
            "for sc2egset (p99=1,876s, max=6,073s); identical across all 3 datasets (I8 "
            "cross-dataset comparability). Expected 0 rows for sc2egset. Added in 01_04_02 ADDENDUM 2026-04-18."
        ),
    },
]

mfc_invariants = [
    {
        "id": "I3",
        "description": (
            "matches_flat_clean is the prediction-target VIEW. ALL columns must be PRE_GAME "
            "(available before game T starts). IN_GAME_HISTORICAL and POST_GAME_HISTORICAL "
            "columns are excluded by construction from direct feature use. "
            "ADDENDUM 2026-04-18: duration_seconds + is_duration_suspicious are POST_GAME_HISTORICAL "
            "(tokens in notes field). header_elapsedGameLoops is NOT directly exposed; it is "
            "aggregated via a JOIN to player_history_all. I3 is preserved: no IN_GAME_HISTORICAL "
            "column is directly present. Phase 02 must apply match_time < T filter before using "
            "POST_GAME_HISTORICAL columns as historical aggregates."
        ),
        "provenance_categories": [
            {"TARGET": "THE prediction label itself (Win/Loss/Undecided/Tie). Singleton sentinel -- only the result column carries this tag. Never aggregate without temporal exclusion (match_time < T); using it as a direct game-T feature IS target leakage."},
            {"POST_GAME_HISTORICAL": "The game-T outcome itself or any feature derived from it (e.g., is_decisive_result, future Phase-02 win-rate aggregates, duration_seconds, is_duration_suspicious). SAFE only when used as a player-history aggregate FILTERED by match_time < T. UNSAFE as direct game-T feature. NOT PRESENT in this VIEW as direct features -- all POST_GAME_HISTORICAL cols are available for historical aggregation only."},
            {"IN_GAME_HISTORICAL": "Available during/after game completion (e.g., APM, SQ, supplyCappedPercent, header_elapsedGameLoops). NOT PRESENT in this VIEW by construction (I3). header_elapsedGameLoops is accessed only via aggregation in duration_per_replay CTE -- not exposed directly."},
            {"PRE_GAME": "Available before game T starts (e.g., race, map, skill flags). Safe to use as feature for game T without temporal filtering."},
            {"IDENTITY": "Stable identifiers (replay_id, toon_id, profileId). No temporal constraint; not a feature input but a join key."},
            {"CONTEXT": "Game/match metadata (started_timestamp, mapName, gameLoops). PRE_GAME-equivalent for temporal purposes; available before game T."},
        ],
    },
    {
        "id": "I5",
        "description": (
            "Every replay_id has exactly 2 rows: 1 with result='Win', 1 with result='Loss'. "
            "ADDENDUM 2026-04-18: both rows have identical duration_seconds + is_duration_suspicious "
            "(verified by IS DISTINCT FROM check = 0 violations in duration_augmentation gate 6)."
        ),
    },
    {
        "id": "I6",
        "description": (
            "DDL is reproducible from raw + 01_04_00 + 01_04_01 + 01_04_02 + this notebook. "
            "Original DDL stored verbatim in 01_04_02_post_cleaning_validation.json sql_queries block. "
            "ADDENDUM DDL stored verbatim in 01_04_02_duration_augmentation.json sql_queries block."
        ),
    },
    {
        "id": "I7",
        "description": (
            "22.4 loops/sec divisor: SC2 Faster game-speed constant. Provenance: "
            "details.gameSpeed cardinality=1 in sc2egset (W02 census, research_log.md:424); "
            "Blizzard SC2 documentation. Established in 01_04_03 ADDENDUM."
        ),
    },
    {
        "id": "I9",
        "description": "01_04_02 (including this ADDENDUM) modifies the column SET, never the values. No imputation, scaling, or encoding. Phase 02 owns those transforms.",
    },
    {
        "id": "I10",
        "description": "All replay_id derivation traces back to filename relative to raw_dir per Invariant I10.",
    },
]

mfc_yaml_content = {
    "table": "matches_flat_clean",
    "dataset": "sc2egset",
    "game": "sc2",
    "object_type": "view",
    "step": "01_04_02",
    "schema_version": "30-col (ADDENDUM: duration added 2026-04-18)",
    "row_count": int(post_rows[0]),
    "describe_artifact": (
        "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/"
        "01_04_02_post_cleaning_validation.json"
    ),
    "addendum_artifact": (
        "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/"
        "01_04_02_duration_augmentation.json"
    ),
    "generated_date": "2026-04-18",
    "columns": mfc_columns_yaml,
    "provenance": {
        "source_tables": ["replay_players_raw", "replays_meta_raw", "player_history_all"],
        "join_key": "NULLIF(regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json', 1), '') AS replay_id",
        "filter": "true_1v1_decisive CTE (exactly 2 players, 1 Win + 1 Loss); mmr_valid CTE (no MMR<0 player in replay)",
        "scope": "True 1v1 decisive replays only. 22,209 replays, 44,418 rows (2 per replay).",
        "created_by": "sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py",
        "addendum_by": "sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_02_duration_augmentation.py",
    },
    "invariants": mfc_invariants,
}

with open(schema_path, "w") as f:
    yaml.dump(mfc_yaml_content, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
print(f"matches_flat_clean.yaml updated: {schema_path}")
print(f"  Columns: {len(mfc_columns_yaml)}")
print(f"  schema_version: {mfc_yaml_content['schema_version']}")

# %% [markdown]
# ## Cell 17 -- Gate 8: I9 -- no diff on upstream YAMLs

# %%
import subprocess

# repo_root is derived from schema_dir (which is absolute)
repo_root = schema_dir.parent.parent.parent.parent.parent.parent.parent.parent
print(f"repo_root: {repo_root}")

UPSTREAM_YAML_NAMES = [
    "src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_history_all.yaml",
    "src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/matches_long_raw.yaml",
    "src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/matches_history_minimal.yaml",
]

for yaml_rel in UPSTREAM_YAML_NAMES:
    yaml_abs = str(repo_root / yaml_rel)
    result = subprocess.run(
        ["git", "diff", "--stat", yaml_abs],
        capture_output=True, text=True, cwd=str(repo_root)
    )
    has_diff = bool(result.stdout.strip())
    print(f"{'MODIFIED (VIOLATION)' if has_diff else 'CLEAN'}: {yaml_rel}")
    if has_diff:
        print(f"  diff: {result.stdout.strip()}")
    assert not has_diff, f"Gate 8 FAIL (I9): unexpected diff on upstream YAML: {yaml_rel}"

print("Gate 8 PASS: I9 -- all upstream YAMLs untouched")

# %% [markdown]
# ## Cell 18 -- Gate 9: Validation JSON -- all_assertions_pass: true + SQL verbatim

# %%
with open(json_path) as f:
    loaded = json.load(f)

assert loaded["all_assertions_pass"] is True, f"Gate 9 FAIL: all_assertions_pass={loaded['all_assertions_pass']}"
assert "create_matches_flat_clean_v3" in loaded["sql_queries"], "Gate 9 FAIL: DDL SQL missing from json"
assert "duration_stats" in loaded["sql_queries"], "Gate 9 FAIL: duration_stats SQL missing from json"
print("Gate 9 PASS: all_assertions_pass=true + SQL verbatim in json")

# %% [markdown]
# ## Cell 19 -- Close DuckDB connection

# %%
db.close()
print("DuckDB connection closed.")

# %% [markdown]
# ## Cell 20 -- Final summary

# %%
print("=" * 70)
print("Step 01_04_02 ADDENDUM -- Duration Augmentation: COMPLETE")
print("=" * 70)
print()
print("CONSORT column-count flow:")
print("  matches_flat_clean: 28 cols -> 30 cols (added duration_seconds + is_duration_suspicious)")
print()
print("Duration stats (sc2egset):")
print(f"  min={duration_stats['min_seconds']}s, p50={duration_stats['p50_seconds']:.1f}s, "
      f"p99={duration_stats['p99_seconds']:.1f}s, max={duration_stats['max_seconds']}s")
print(f"  null_count={duration_stats['null_count']}, suspicious_count={duration_stats['suspicious_count_gt_86400']}")
print()
print("All 9 gates: PASS")
print()
print("Artifacts produced:")
print(f"  {json_path}")
print(f"  {md_path}")
print(f"  {schema_path} (UPDATED)")
