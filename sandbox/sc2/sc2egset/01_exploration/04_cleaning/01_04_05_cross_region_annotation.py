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
# # Step 01_04_05 — Cross-Region Fragmentation Phase 01 Annotation
#
# **Phase:** 01 — Data Exploration
# **Pipeline Section:** 01_04 — Data Cleaning
# **Dataset:** sc2egset
# **Step scope:** Adds `is_cross_region_fragmented` BOOLEAN column to the
# `player_history_all` VIEW via DDL amendment. Flag TRUE iff a row's `toon_id`
# belongs to the set of cross-region toon_ids (toons whose LOWER(nickname)
# appears in 2+ regions in `replay_players_raw`).
#
# **Motivation:** WP-3 (01_05_10) empirically FAILed the "accepted bias" framing —
# at window=30, median rolling-window undercount = 16.0 games, p95 = 29.0 games.
# User directive 2026-04-21 requires a Phase 01 01_04 annotation so Phase 02
# consumers can operationalize the accepted-bias framing without re-deriving the
# cross-region set per query.
#
# **Invariants applied:**
#   - I6 (SQL stored verbatim in artifact)
#   - I7 (toon_id and nickname counts derived at runtime — no magic numbers)
#   - I9 (non-destructive: raw tables untouched; only VIEW replaced)
#
# **Predecessor:** 01_04_02 (player_history_all v2 — 37 cols), 01_05_10 (WP-3 FAIL)
# **Date:** 2026-04-21
# **ROADMAP ref:** 01_04_05

# %% [markdown]
# ## Cell 1 — Imports

# %%
import json
from pathlib import Path

import pandas as pd

from rts_predict.common.notebook_utils import (
    get_notebook_db,
    get_reports_dir,
    setup_notebook_logging,
)

logger = setup_notebook_logging()

# %% [markdown]
# ## Cell 2 — DuckDB Connection (writable — replaces VIEW)
#
# This notebook creates a replacement VIEW. A writable connection is required.
# WARNING: Close all read-only notebook connections to this DB before running.

# %%
db = get_notebook_db("sc2", "sc2egset", read_only=False)
con = db.con
print("DuckDB connection opened (read-write).")

# %% [markdown]
# ## Cell 3 — WP-3 Motivation: Empirical FAIL numbers
#
# The cross-region fragmentation bias was quantified by step 01_05_10.
# INVARIANTS.md §2 accepted-bias paragraph records:
#   - 246 cross-region nicknames (~12% of sc2egset players)
#   - At window=30: median undercount=16.0 games, p95=29.0 games (FAIL vs ≤1/≤5 thresholds)
#   - MMR-fragmentation Spearman ρ bootstrap 95% CI upper=0.291 (FAIL vs <0.20 threshold)
# This step operationalizes mitigation candidate (2): adding a BOOLEAN annotation flag
# to player_history_all so Phase 02 can apply the accepted-bias framing without
# re-deriving the cross-region set.

# %%
reports_dir = get_reports_dir("sc2", "sc2egset")
wp3_path = (
    reports_dir / "artifacts" / "01_exploration" / "05_temporal_panel_eda"
    / "cross_region_history_impact_sc2egset.json"
)

with open(wp3_path) as f:
    wp3 = json.load(f)

print(f"WP-3 artifact loaded: {wp3_path.name}")
print(f"  n_cross_region_nicknames: {wp3.get('n_cross_region_nicknames', 'N/A')}")
print(f"  median_rolling30_undercount: {wp3.get('median_rolling30_undercount', 'N/A')}")
print(f"  p95_rolling30_undercount: {wp3.get('p95_rolling30_undercount', 'N/A')}")
print(f"  bootstrap_CI_upper_rho: {wp3.get('bootstrap_CI_upper_rho', 'N/A')}")
print(f"  verdict: {wp3.get('verdict', 'N/A')}")

# %% [markdown]
# ## Cell 4 — Cross-Region Set Construction: Counts (hypothesis + falsifier)
#
# Hypothesis: nickname_count = 246 (as in INVARIANTS.md §2).
# Falsifier: any deviation → halt (zero-tolerance per WP-3/WP-4 precedent).
#
# SQL (I6):
# ```sql
# WITH cross_region_nicknames AS (
#     SELECT LOWER(nickname) AS nick_lower
#     FROM replay_players_raw
#     GROUP BY LOWER(nickname)
#     HAVING COUNT(DISTINCT region) > 1
# )
# SELECT COUNT(*) FROM cross_region_nicknames;
# ```

# %%
nickname_count = con.execute("""
    SELECT COUNT(*) AS nickname_count
    FROM (
        SELECT LOWER(nickname) AS nick_lower
        FROM replay_players_raw
        GROUP BY LOWER(nickname)
        HAVING COUNT(DISTINCT region) > 1
    ) sub
""").fetchone()[0]

toon_id_count = con.execute("""
    SELECT COUNT(DISTINCT toon_id) AS toon_id_count
    FROM replay_players_raw
    WHERE LOWER(nickname) IN (
        SELECT LOWER(nickname)
        FROM replay_players_raw
        GROUP BY LOWER(nickname)
        HAVING COUNT(DISTINCT region) > 1
    )
""").fetchone()[0]

print(f"nickname_count: {nickname_count}")
print(f"toon_id_count: {toon_id_count}")

# Zero-tolerance drift check (WP-3/WP-4 precedent)
INVARIANTS_NICKNAME_COUNT = 246
assert nickname_count == INVARIANTS_NICKNAME_COUNT, (
    f"HALT: nickname_count drift detected! "
    f"INVARIANTS.md §2 says {INVARIANTS_NICKNAME_COUNT}, got {nickname_count}. "
    f"Supersede INVARIANTS.md §2 authoritatively before proceeding."
)
print(f"nickname_count drift check PASSED ({nickname_count} == {INVARIANTS_NICKNAME_COUNT})")

# %% [markdown]
# ## Cell 5 — Handle-Length Breakdown of Flagged Toons
#
# Report distribution by LENGTH(nickname) bucket {< 5, 5-7, ≥ 8} for Phase 02 context.
# WP-3 §6 rare-handle subsample (length ≥ 8, n=96 nicknames) confirmed genuine
# fragmentation — bias is not solely a short-handle-collision artifact.
#
# This breakdown informs the blanket-flag conservatism argument (no length filter):
# false positives are bounded by the lt_5 count (short-handle toons more likely
# to be collision artifacts than genuine cross-region players).

# %%
breakdown_df = con.execute("""
    WITH cross_region_toons AS (
        SELECT DISTINCT toon_id
        FROM replay_players_raw
        WHERE LOWER(nickname) IN (
            SELECT LOWER(nickname)
            FROM replay_players_raw
            GROUP BY LOWER(nickname)
            HAVING COUNT(DISTINCT region) > 1
        )
    ),
    toon_min_nick_len AS (
        SELECT rp.toon_id, MIN(LENGTH(rp.nickname)) AS min_nick_len
        FROM replay_players_raw rp
        JOIN cross_region_toons crt ON rp.toon_id = crt.toon_id
        GROUP BY rp.toon_id
    )
    SELECT
        SUM(CASE WHEN min_nick_len < 5 THEN 1 ELSE 0 END) AS lt_5,
        SUM(CASE WHEN min_nick_len >= 5 AND min_nick_len <= 7 THEN 1 ELSE 0 END) AS len_5_to_7,
        SUM(CASE WHEN min_nick_len >= 8 THEN 1 ELSE 0 END) AS ge_8,
        COUNT(*) AS total_toons
    FROM toon_min_nick_len
""").df()

print("Handle-length breakdown (per distinct flagged toon_id, using min nickname length):")
print(breakdown_df.to_string(index=False))
lt_5 = int(breakdown_df["lt_5"].iloc[0])
len_5_to_7 = int(breakdown_df["len_5_to_7"].iloc[0])
ge_8 = int(breakdown_df["ge_8"].iloc[0])
total_toons = int(breakdown_df["total_toons"].iloc[0])
print(f"\n  lt_5: {lt_5}, 5_to_7: {len_5_to_7}, ge_8: {ge_8}, total: {total_toons}")
assert total_toons == toon_id_count, f"total_toons {total_toons} != toon_id_count {toon_id_count}"

# %% [markdown]
# ## Cell 6 — Current VIEW DDL (before amendment)
#
# Verbatim from 01_04_02_data_cleaning_execution.py (v2, 37 cols).
# Source: `FROM matches_flat mf WHERE mf.replay_id IS NOT NULL`

# %%
CURRENT_PLAYER_HISTORY_ALL_DDL = """
CREATE OR REPLACE VIEW player_history_all AS
-- Purpose: Player feature history VIEW. All replays (no 1v1/decisive filter).
-- Row multiplicity: 1 row per player per replay (44817 rows, 22390 replays).
-- Column set: 37 columns including IN_GAME_HISTORICAL metrics (APM, SQ, etc.)
-- valid for prior-match historical aggregation only (temporal discipline I3).
-- Changes from v1 (01_04_01): 16 cols dropped, 2 cols added, APM NULLIF applied.
SELECT
    -- Identity (6 cols)
    mf.replay_id,
    mf.filename,
    mf.toon_id,
    mf.nickname,
    mf.playerID,
    mf.userID,

    -- Target and decisive flag (2 cols per DS-SC2-04)
    mf.result,
    (mf.result IN ('Win', 'Loss')) AS is_decisive_result,

    -- Pre-game player features
    CASE WHEN mf.MMR = 0 THEN TRUE ELSE FALSE END AS is_mmr_missing,
    mf.race,
    CASE WHEN mf.selectedRace = '' THEN 'Random'
         ELSE mf.selectedRace END AS selectedRace,
    mf.region,
    mf.realm,
    mf.isInClan,

    -- In-game metrics
    NULLIF(mf.APM, 0) AS APM,
    (mf.APM = 0) AS is_apm_unparseable,
    CASE WHEN mf.SQ = -2147483648 THEN NULL ELSE mf.SQ END AS SQ,
    mf.supplyCappedPercent,
    mf.header_elapsedGameLoops,

    -- Pre-game spatial
    mf.startDir,
    mf.startLocX,
    mf.startLocY,

    -- Map metadata
    mf.metadata_mapName,
    CASE WHEN mf.gd_mapSizeX = 0 THEN NULL ELSE mf.gd_mapSizeX END AS gd_mapSizeX,
    CASE WHEN mf.gd_mapSizeY = 0 THEN NULL ELSE mf.gd_mapSizeY END AS gd_mapSizeY,
    mf.gd_maxPlayers,
    mf.details_isBlizzardMap,
    mf.gd_mapAuthorName,
    mf.gd_mapFileSyncChecksum,

    -- Temporal anchor
    mf.details_timeUTC,

    -- Version context
    mf.header_version,
    mf.metadata_baseBuild,
    mf.metadata_dataBuild,
    mf.metadata_gameVersion,

    -- Game options (variable cardinality only; 12 constants DROPPED per DS-SC2-08)
    mf.go_amm,
    mf.go_clientDebugFlags,
    mf.go_competitive

FROM matches_flat mf
WHERE mf.replay_id IS NOT NULL;
"""

pre_cols = con.execute("DESCRIBE player_history_all").df()
print(f"Current player_history_all column count: {len(pre_cols)}")
assert len(pre_cols) == 37, f"Expected 37 cols pre-amendment, got {len(pre_cols)}"
print("Pre-amendment column count assertion PASSED (37 cols).")

# %% [markdown]
# ## Cell 7 — Amended VIEW DDL (adds is_cross_region_fragmented as 38th column)
#
# BLOCKER-2 fix: uses actual source alias `mf` (from matches_flat mf).
# Prepends WITH cross_region_toons AS (...) CTE.
# Appends `(mf.toon_id IN (SELECT toon_id FROM cross_region_toons)) AS is_cross_region_fragmented`
# as the 38th projected column.
# Preserves existing FROM/WHERE exactly.
#
# SQL (I6 — stored verbatim):

# %%
AMENDED_PLAYER_HISTORY_ALL_DDL = """
CREATE OR REPLACE VIEW player_history_all AS
WITH cross_region_toons AS (
    SELECT DISTINCT toon_id
    FROM replay_players_raw
    WHERE LOWER(nickname) IN (
        SELECT LOWER(nickname)
        FROM replay_players_raw
        GROUP BY LOWER(nickname)
        HAVING COUNT(DISTINCT region) > 1
    )
)
-- Purpose: Player feature history VIEW. All replays (no 1v1/decisive filter).
-- Row multiplicity: 1 row per player per replay (44817 rows, 22390 replays).
-- Column set: 38 columns (37 from 01_04_02 + is_cross_region_fragmented from 01_04_05).
-- is_cross_region_fragmented: TRUE iff toon_id in cross-region set (01_04_05).
SELECT
    -- Identity (6 cols)
    mf.replay_id,
    mf.filename,
    mf.toon_id,
    mf.nickname,
    mf.playerID,
    mf.userID,

    -- Target and decisive flag (2 cols per DS-SC2-04)
    mf.result,
    (mf.result IN ('Win', 'Loss')) AS is_decisive_result,

    -- Pre-game player features
    CASE WHEN mf.MMR = 0 THEN TRUE ELSE FALSE END AS is_mmr_missing,
    mf.race,
    CASE WHEN mf.selectedRace = '' THEN 'Random'
         ELSE mf.selectedRace END AS selectedRace,
    mf.region,
    mf.realm,
    mf.isInClan,

    -- In-game metrics
    NULLIF(mf.APM, 0) AS APM,
    (mf.APM = 0) AS is_apm_unparseable,
    CASE WHEN mf.SQ = -2147483648 THEN NULL ELSE mf.SQ END AS SQ,
    mf.supplyCappedPercent,
    mf.header_elapsedGameLoops,

    -- Pre-game spatial
    mf.startDir,
    mf.startLocX,
    mf.startLocY,

    -- Map metadata
    mf.metadata_mapName,
    CASE WHEN mf.gd_mapSizeX = 0 THEN NULL ELSE mf.gd_mapSizeX END AS gd_mapSizeX,
    CASE WHEN mf.gd_mapSizeY = 0 THEN NULL ELSE mf.gd_mapSizeY END AS gd_mapSizeY,
    mf.gd_maxPlayers,
    mf.details_isBlizzardMap,
    mf.gd_mapAuthorName,
    mf.gd_mapFileSyncChecksum,

    -- Temporal anchor
    mf.details_timeUTC,

    -- Version context
    mf.header_version,
    mf.metadata_baseBuild,
    mf.metadata_dataBuild,
    mf.metadata_gameVersion,

    -- Game options (variable cardinality only; 12 constants DROPPED per DS-SC2-08)
    mf.go_amm,
    mf.go_clientDebugFlags,
    mf.go_competitive,

    -- Cross-region fragmentation annotation (01_04_05, 2026-04-21)
    (mf.toon_id IN (SELECT toon_id FROM cross_region_toons)) AS is_cross_region_fragmented

FROM matches_flat mf
WHERE mf.replay_id IS NOT NULL;
"""

print("Amended DDL defined (38 cols: 37 existing + is_cross_region_fragmented).")

# %% [markdown]
# ## Cell 8 — Execute DDL Amendment

# %%
con.execute(AMENDED_PLAYER_HISTORY_ALL_DDL)
print("player_history_all VIEW replaced (v3 — 38 cols).")

post_cols = con.execute("DESCRIBE player_history_all").df()
print(f"Post-amendment column count: {len(post_cols)}")
assert len(post_cols) == 38, f"Expected 38 cols post-amendment, got {len(post_cols)}"

post_row_count = con.execute("SELECT COUNT(*) FROM player_history_all").fetchone()[0]
print(f"Post-amendment row count: {post_row_count}")
assert post_row_count == 44817, f"Expected 44817 rows, got {post_row_count}"

print("Post-amendment assertions PASSED (38 cols, 44817 rows).")

# %% [markdown]
# ## Cell 9 — Verification: Flag Distribution

# %%
flag_dist_df = con.execute("""
    SELECT is_cross_region_fragmented, COUNT(*) AS cnt
    FROM player_history_all
    GROUP BY 1
    ORDER BY 1
""").df()

print("Flag distribution:")
print(flag_dist_df.to_string(index=False))

rows_flagged_false = int(flag_dist_df.loc[flag_dist_df["is_cross_region_fragmented"] == False, "cnt"].iloc[0])
rows_flagged_true = int(flag_dist_df.loc[flag_dist_df["is_cross_region_fragmented"] == True, "cnt"].iloc[0])
print(f"\n  rows_flagged_true: {rows_flagged_true}")
print(f"  rows_flagged_false: {rows_flagged_false}")
assert rows_flagged_true + rows_flagged_false == 44817, "Row count invariance broken"

# %% [markdown]
# ## Cell 10 — Verification: No NULL in BOOLEAN Column + Distinct Flagged Toons

# %%
null_count = con.execute("""
    SELECT COUNT(*) FROM player_history_all WHERE is_cross_region_fragmented IS NULL
""").fetchone()[0]
print(f"NULL count in is_cross_region_fragmented: {null_count}")
assert null_count == 0, f"BOOLEAN column has {null_count} NULLs — unexpected"
print("No NULL assertion PASSED.")

flagged_toons_distinct = con.execute("""
    SELECT COUNT(DISTINCT toon_id)
    FROM player_history_all
    WHERE is_cross_region_fragmented = TRUE
""").fetchone()[0]
print(f"Distinct flagged toon_ids in player_history_all: {flagged_toons_distinct}")
assert flagged_toons_distinct == toon_id_count, (
    f"flagged_toons_distinct {flagged_toons_distinct} != toon_id_count {toon_id_count}"
)
print(f"flagged_toons_distinct == toon_id_count ({toon_id_count}) PASSED.")

# %% [markdown]
# ## Cell 11 — Summary

# %%
print("=== 01_04_05 Summary ===")
print(f"  nickname_count: {nickname_count}")
print(f"  toon_id_count: {toon_id_count}")
print(f"  handle_length_breakdown: lt_5={lt_5}, 5_to_7={len_5_to_7}, ge_8={ge_8}")
print(f"  rows_flagged_true: {rows_flagged_true}")
print(f"  rows_flagged_false: {rows_flagged_false}")
print(f"  total_rows: {rows_flagged_true + rows_flagged_false}")
print(f"  null_count: {null_count}")
print(f"  flagged_toons_distinct: {flagged_toons_distinct}")
print(f"  column_count_pre: 37, column_count_post: 38")

# %% [markdown]
# ## Cell 12 — Artifact Export

# %%
artifacts_dir = (
    reports_dir / "artifacts" / "01_exploration" / "04_cleaning"
)
artifacts_dir.mkdir(parents=True, exist_ok=True)

artifact = {
    "step": "01_04_05",
    "view_amended": "player_history_all",
    "view_source_alias": "matches_flat mf",
    "column_added": "is_cross_region_fragmented",
    "column_type": "BOOLEAN",
    "row_count_pre": 44817,
    "row_count_post": post_row_count,
    "column_count_yaml_pre": 37,
    "column_count_yaml_post": 38,
    "column_count_spec_pre_locked": 36,
    "column_count_spec_drift_reconciled": True,
    "nickname_count": nickname_count,
    "toon_id_count": toon_id_count,
    "rows_flagged_true": rows_flagged_true,
    "rows_flagged_false": rows_flagged_false,
    "flagged_toons_distinct": flagged_toons_distinct,
    "handle_length_breakdown": {
        "lt_5": lt_5,
        "5_to_7": len_5_to_7,
        "ge_8": ge_8,
    },
    "conservatism_argument": (
        "The flag is blanket (no handle-length filter) by design. "
        "Rationale: length-filtered flags (e.g., length >= 8 per WP-3 rare-handle subsample) "
        "could miss genuine cross-region players with short handles. "
        "False-positive rate bounded by the lt_5 count (636 toons with min nickname length < 5): "
        "these short-handle toons are more likely handle-collision artifacts than genuine "
        "same-player fragmentation. Phase 02 may subset to length >= 8 via an additional JOIN "
        "for strict sensitivity analysis; the blanket flag is the conservative default. "
        "Trade-off: under-flagging misses real bias; over-flagging dilutes sensitivity signal. "
        "Plan chooses over-flagging as the safer Phase-02-informing default."
    ),
    "audit_date": "2026-04-21",
}

json_path = artifacts_dir / "01_04_05_cross_region_annotation.json"
with open(json_path, "w") as f:
    json.dump(artifact, f, indent=2)
print(f"JSON artifact written: {json_path}")

# Verify JSON roundtrip
with open(json_path) as f:
    loaded = json.load(f)
assert loaded["flagged_toons_distinct"] == loaded["toon_id_count"], "JSON integrity check failed"
assert loaded["row_count_pre"] == loaded["row_count_post"], "Row count invariance in JSON"
print("JSON integrity checks PASSED.")

db.close()
print("DuckDB connection closed.")
