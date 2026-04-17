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
# # Step 01_04_01 -- Data Cleaning
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_04 -- Data Cleaning
# **Dataset:** sc2egset
# **Question:** How do we non-destructively clean the two ESSENTIAL raw tables
# (replay_players_raw, replays_meta_raw) into analytical views?
# **Invariants applied:** #3 (I3 temporal discipline -- PRE_GAME only in
# matches_flat_clean), #6 (all SQL verbatim), #7 (all thresholds data-derived),
# #9 (no rows deleted, raw data untouched)
# **Predecessor:** 01_03_04 (Event Table Profiling -- complete)
# **Type:** WRITES -- creates 3 DuckDB VIEWs (matches_flat, matches_flat_clean,
# player_history_all)
#
# **Commit:** feat/data-cleaning-01-04
# **Date:** 2026-04-16
# **ROADMAP ref:** 01_04_01
# **Revision:** 1 (incorporates replay-level MMR exclusion, regexp_extract NULLIF guard, constant column exclusions, and APM=0 as documentation-only)
#
# ## Design constraint: Prediction scope != Feature scope
#
# The thesis predicts only 1v1 match outcomes (matches_flat_clean), but
# player-level features in Phase 02 should be computed from the player's full
# recorded game history. For sc2egset, this means all replays a player appears
# in -- including non-1v1 and indecisive replays excluded from
# matches_flat_clean -- remain valid game history in player_history_all.
# APM, SQ, and other in-game metrics are valid historical signals for PRIOR
# matches. I3 only prohibits using them for TARGET match T. Temporal discipline
# (I3) still applies: features for match T at time t use only games completed
# before time t.

# %% [markdown]
# ## Cell 1 -- Imports

# %%
import json
from pathlib import Path

import numpy as np
import pandas as pd

from rts_predict.common.notebook_utils import (
    get_notebook_db,
    get_reports_dir,
    setup_notebook_logging,
)

logger = setup_notebook_logging()

# %% [markdown]
# ## Cell 2 -- DuckDB Connection (writable -- creates VIEWs)
#
# This notebook creates three VIEWs. A writable connection is required.
# WARNING: Close all read-only notebook connections to this DB before running.

# %%
db = get_notebook_db("sc2", "sc2egset", read_only=False)
con = db.con  # public attribute — uniform W4 fix (con.execute(...) throughout)
print("DuckDB connection opened (read-write).")

# %% [markdown]
# ## Create matches_flat VIEW (structural JOIN)
#
# Structural JOIN of replay_players_raw x replays_meta_raw using replay_id
# extracted via regexp. NULLIF converts empty-string non-matches to NULL
# (empty-string protection).
#
# **Columns RETAINED:** all raw columns including APM, SQ, supplyCappedPercent
# (in-game metrics) for pass-through to player_history_all.
#
# **JOIN key:** NULLIF(regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1), '')

# %%
CREATE_MATCHES_FLAT_SQL = """
CREATE OR REPLACE VIEW matches_flat AS
SELECT
    -- Canonical join key (NULLIF converts empty-string non-match to NULL)
    NULLIF(
        regexp_extract(rp.filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1),
        ''
    ) AS replay_id,

    -- Player identity
    rp.filename,
    rp.toon_id,
    rp.nickname,
    rp.playerID,
    rp.userID,

    -- Player pre-game features
    rp.MMR,
    rp.race,
    rp.selectedRace,
    rp.handicap,
    rp.region,
    rp.realm,
    rp.highestLeague,
    rp.isInClan,
    rp.clanTag,

    -- Target variable
    rp.result,

    -- Player in-game metrics (I3: IN_GAME -- excluded from matches_flat_clean,
    -- but RETAINED in player_history_all for historical feature computation)
    rp.APM,
    rp.SQ,
    rp.supplyCappedPercent,

    -- Player spatial (pre-game lobby assignment)
    rp.startDir,
    rp.startLocX,
    rp.startLocY,

    -- Player cosmetic
    rp.color_a, rp.color_b, rp.color_g, rp.color_r,

    -- Match metadata: details struct
    rm.details.gameSpeed            AS details_gameSpeed,
    rm.details.isBlizzardMap        AS details_isBlizzardMap,
    rm.details.timeUTC              AS details_timeUTC,

    -- Match metadata: header struct
    rm.header.elapsedGameLoops      AS header_elapsedGameLoops,
    rm.header.version               AS header_version,

    -- Match metadata: initData.gameDescription direct fields
    rm.initData.gameDescription.gameSpeed           AS gd_gameSpeed,
    rm.initData.gameDescription.isBlizzardMap       AS gd_isBlizzardMap,
    rm.initData.gameDescription.mapAuthorName       AS gd_mapAuthorName,
    rm.initData.gameDescription.mapFileSyncChecksum AS gd_mapFileSyncChecksum,
    rm.initData.gameDescription.mapSizeX            AS gd_mapSizeX,
    rm.initData.gameDescription.mapSizeY            AS gd_mapSizeY,
    rm.initData.gameDescription.maxPlayers          AS gd_maxPlayers,

    -- Match metadata: gameOptions (15 leaves)
    rm.initData.gameDescription.gameOptions.advancedSharedControl AS go_advancedSharedControl,
    rm.initData.gameDescription.gameOptions.amm                   AS go_amm,
    rm.initData.gameDescription.gameOptions.battleNet             AS go_battleNet,
    rm.initData.gameDescription.gameOptions.clientDebugFlags      AS go_clientDebugFlags,
    rm.initData.gameDescription.gameOptions.competitive           AS go_competitive,
    rm.initData.gameDescription.gameOptions.cooperative           AS go_cooperative,
    rm.initData.gameDescription.gameOptions.fog                   AS go_fog,
    rm.initData.gameDescription.gameOptions.heroDuplicatesAllowed AS go_heroDuplicatesAllowed,
    rm.initData.gameDescription.gameOptions.lockTeams             AS go_lockTeams,
    rm.initData.gameDescription.gameOptions.noVictoryOrDefeat     AS go_noVictoryOrDefeat,
    rm.initData.gameDescription.gameOptions.observers             AS go_observers,
    rm.initData.gameDescription.gameOptions.practice              AS go_practice,
    rm.initData.gameDescription.gameOptions.randomRaces           AS go_randomRaces,
    rm.initData.gameDescription.gameOptions.teamsTogether         AS go_teamsTogether,
    rm.initData.gameDescription.gameOptions.userDifficulty        AS go_userDifficulty,

    -- Match metadata: metadata struct
    rm.metadata.baseBuild           AS metadata_baseBuild,
    rm.metadata.dataBuild           AS metadata_dataBuild,
    rm.metadata.gameVersion         AS metadata_gameVersion,
    rm.metadata.mapName             AS metadata_mapName

FROM replay_players_raw rp
JOIN replays_meta_raw rm
  ON NULLIF(
         regexp_extract(rp.filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1),
         ''
     )
   = NULLIF(
         regexp_extract(rm.filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1),
         ''
     );
"""

con.execute(CREATE_MATCHES_FLAT_SQL)
print("matches_flat VIEW created.")

# %% [markdown]
# ## matches_flat validation

# %%
r_mf = con.execute(
    "SELECT COUNT(*) AS total_rows, COUNT(DISTINCT replay_id) AS distinct_replays FROM matches_flat"
).fetchone()
print(f"matches_flat: rows={r_mf[0]}, distinct_replays={r_mf[1]}")
assert r_mf[0] == 44817, f"Expected 44817 rows, got {r_mf[0]}"
assert r_mf[1] == 22390, f"Expected 22390 replays, got {r_mf[1]}"

r_null = con.execute(
    "SELECT COUNT(*) AS null_replay_id FROM matches_flat WHERE replay_id IS NULL"
).fetchone()
print(f"NULL replay_id: {r_null[0]}")
assert r_null[0] == 0, f"Expected 0 NULL replay_ids, got {r_null[0]}"

# isBlizzardMap duplication check
r_bm = con.execute(
    "SELECT COUNT(*) AS mismatched_blizzard_map FROM matches_flat WHERE gd_isBlizzardMap != details_isBlizzardMap"
).fetchone()
print(f"isBlizzardMap mismatch count: {r_bm[0]}")
if r_bm[0] == 0:
    print("gd_isBlizzardMap == details_isBlizzardMap for all rows. Will exclude gd_isBlizzardMap from downstream VIEWs.")

# gameSpeed constant assertion
r_gs = con.execute(
    "SELECT COUNT(DISTINCT details_gameSpeed) AS n_details, COUNT(DISTINCT gd_gameSpeed) AS n_gd FROM matches_flat"
).fetchone()
print(f"gameSpeed cardinality: details={r_gs[0]}, gd={r_gs[1]}")
assert r_gs[0] == 1, f"details_gameSpeed cardinality={r_gs[0]}, expected 1"
assert r_gs[1] == 1, f"gd_gameSpeed cardinality={r_gs[1]}, expected 1"

# %% [markdown]
# ## Non-1v1 and indecisive result classification
#
# Identify replays not suitable for binary 1v1 classification.
# Exclusion applies to matches_flat_clean (prediction target) ONLY.
# Excluded replays remain in player_history_all as valid game history.

# %%
CLASSIFICATION_SUMMARY_SQL = """
SELECT classification, COUNT(*) AS n_replays
FROM (
    SELECT replay_id,
        CASE
            WHEN COUNT(*) = 2
                 AND COUNT(*) FILTER (WHERE result = 'Win') = 1
                 AND COUNT(*) FILTER (WHERE result = 'Loss') = 1
            THEN 'true_1v1_decisive'
            WHEN COUNT(*) < 2 THEN 'non_1v1_too_few_players'
            WHEN COUNT(*) > 2 THEN 'non_1v1_too_many_players'
            WHEN COUNT(*) = 2
                 AND (COUNT(*) FILTER (WHERE result = 'Undecided') > 0
                      OR COUNT(*) FILTER (WHERE result = 'Tie') > 0)
            THEN 'true_1v1_indecisive'
            ELSE 'non_1v1_other'
        END AS classification
    FROM matches_flat GROUP BY replay_id
) t
GROUP BY classification ORDER BY n_replays DESC
"""

r_class = con.execute(CLASSIFICATION_SUMMARY_SQL).df()
print("Non-1v1 and indecisive classification:")
print(r_class.to_string(index=False))
assert r_class["n_replays"].sum() == 22390, "Sum of classified replays != 22390"

# %% [markdown]
# ## MMR analysis: unrated players (MMR=0) and anomalous values (MMR<0)
#
# Replay-level exclusion: any replay with at least one MMR<0 player is excluded
# from matches_flat_clean via a CTE, not a row-level WHERE filter.
# This prevents orphaned rows. CONSORT flow records REPLAY units, not row units.

# %%
TRUE_1V1_SUBQ = """SELECT replay_id FROM matches_flat GROUP BY replay_id
    HAVING COUNT(*) = 2
       AND COUNT(*) FILTER (WHERE result = 'Win') = 1
       AND COUNT(*) FILTER (WHERE result = 'Loss') = 1"""

# MMR counts in true_1v1_decisive
MMR_COUNTS_SQL = f"""
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE MMR = 0) AS mmr_zero,
    COUNT(*) FILTER (WHERE MMR < 0) AS mmr_negative,
    COUNT(*) FILTER (WHERE MMR > 0) AS mmr_positive,
    ROUND(100.0 * COUNT(*) FILTER (WHERE MMR = 0) / COUNT(*), 4) AS mmr_zero_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE MMR < 0) / COUNT(*), 4) AS mmr_negative_pct
FROM matches_flat
WHERE replay_id IN ({TRUE_1V1_SUBQ})
"""

r_mmr = con.execute(MMR_COUNTS_SQL).fetchone()
print(f"MMR in 1v1 decisive: total={r_mmr[0]}, mmr_zero={r_mmr[1]} ({r_mmr[4]}%), mmr_neg={r_mmr[2]} ({r_mmr[5]}%)")

# MMR<0 value distribution
MMR_NEG_SQL = """
SELECT MMR, COUNT(*) AS cnt,
       regexp_extract(filename, '^([^/]+)', 1) AS tournament_sample
FROM matches_flat
WHERE MMR < 0
GROUP BY MMR, tournament_sample
ORDER BY MMR
LIMIT 30
"""
r_mmr_neg = con.execute(MMR_NEG_SQL).df()
print(f"\nMMR<0 distribution (top 30):\n{r_mmr_neg.head(10).to_string(index=False)}")

# Count REPLAYS with at least one MMR<0 player
MMR_NEG_REPLAYS_SQL = f"""
SELECT COUNT(*) AS replays_with_mmr_negative
FROM (
    SELECT replay_id
    FROM matches_flat
    WHERE replay_id IN ({TRUE_1V1_SUBQ})
    GROUP BY replay_id
    HAVING COUNT(*) FILTER (WHERE MMR < 0) > 0
)
"""
r_mmr_neg_replays = con.execute(MMR_NEG_REPLAYS_SQL).fetchone()
print(f"\nMMR<0 replay-level exclusion: {r_mmr_neg_replays[0]} replays")

# Overlap check
MMR_OVERLAP_SQL = f"""
SELECT
    CASE
        WHEN replay_id IN ({TRUE_1V1_SUBQ}) THEN 'true_1v1_decisive'
        ELSE 'non_1v1_or_indecisive'
    END AS scope,
    COUNT(*) AS mmr_neg_rows,
    COUNT(DISTINCT replay_id) AS mmr_neg_replays
FROM matches_flat
WHERE MMR < 0
GROUP BY scope
"""
r_overlap = con.execute(MMR_OVERLAP_SQL).df()
print(f"\nMMR<0 overlap by scope:\n{r_overlap.to_string(index=False)}")

# MMR=0 tournament stratification
MMR_STRAT_SQL = f"""
SELECT
    regexp_extract(filename, '^([^/]+)', 1) AS tournament,
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE MMR = 0) AS mmr_zero,
    COUNT(*) FILTER (WHERE MMR > 0) AS mmr_positive,
    COUNT(*) FILTER (WHERE MMR < 0) AS mmr_negative,
    ROUND(100.0 * COUNT(*) FILTER (WHERE MMR = 0) / COUNT(*), 2) AS mmr_zero_pct
FROM matches_flat
WHERE replay_id IN ({TRUE_1V1_SUBQ})
GROUP BY tournament ORDER BY tournament
"""
r_strat = con.execute(MMR_STRAT_SQL).df()
print(f"\nMMR=0 tournament stratification (first 5):\n{r_strat.head(5).to_string(index=False)}")

# %% [markdown]
# ## selectedRace normalisation (empty string → Random)
#
# Map selectedRace='' (empty string) to 'Random' in both VIEWs.
# Empty string = Random race resolved post-game. 'race' column holds actual played race.

# %%
SELECTED_RACE_SQL = """
SELECT selectedRace, race, COUNT(*) AS cnt
FROM matches_flat
WHERE selectedRace = ''
GROUP BY selectedRace, race
ORDER BY cnt DESC
"""
r_sr = con.execute(SELECTED_RACE_SQL).df()
print("selectedRace='' cross-ref with race:")
print(r_sr.to_string(index=False))

SELECTED_RACE_APM_SQL = """
SELECT
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE APM = 0) AS apm_zero,
    COUNT(*) FILTER (WHERE APM > 0) AS apm_nonzero
FROM matches_flat
WHERE selectedRace = ''
"""
r_sr_apm = con.execute(SELECTED_RACE_APM_SQL).fetchone()
print(f"\nEmpty selectedRace: total={r_sr_apm[0]}, apm_zero={r_sr_apm[1]}, apm_nonzero={r_sr_apm[2]}")
assert r_sr_apm[0] == 1110, f"Expected 1110 empty selectedRace rows, got {r_sr_apm[0]}"

# %% [markdown]
# ## SQ parse-failure sentinel correction (INT32_MIN → NULL)
#
# 2 rows with SQ=INT32_MIN (-2147483648) are parse failures.
# Action: set SQ to NULL in player_history_all.
# Note: SQ excluded from matches_flat_clean per temporal discipline.

# %%
SQ_SENTINEL_SQL = """
SELECT replay_id, filename, nickname, playerID, MMR, APM, SQ, result
FROM matches_flat
WHERE SQ = -2147483648
"""
r_sq = con.execute(SQ_SENTINEL_SQL).df()
print(f"SQ sentinel rows (SQ=INT32_MIN=-2147483648): {len(r_sq)}")
print(r_sq[["replay_id", "nickname", "MMR", "APM", "SQ", "result"]].to_string(index=False))
assert len(r_sq) == 2, f"Expected 2 SQ sentinel rows, got {len(r_sq)}"

# %% [markdown]
# ## APM=0 investigation (documentation only — no cleaning action)
#
# APM investigation is documentation-only.
# NO APM-derived columns are added to any VIEW. APM is an in-game metric.
# APM IS included in player_history_all (valid historical observation).

# %%
APM_DURATION_SQL = f"""
SELECT
    CASE WHEN APM = 0 THEN 'APM=0' ELSE 'APM>0' END AS apm_group,
    COUNT(*) AS n_rows,
    COUNT(DISTINCT replay_id) AS n_replays,
    ROUND(MEDIAN(header_elapsedGameLoops), 0) AS median_loops,
    MIN(header_elapsedGameLoops) AS min_loops,
    MAX(header_elapsedGameLoops) AS max_loops
FROM matches_flat
WHERE replay_id IN ({TRUE_1V1_SUBQ})
GROUP BY apm_group
"""
r_apm = con.execute(APM_DURATION_SQL).df()
print("APM=0 vs game duration (true_1v1_decisive):")
print(r_apm.to_string(index=False))

APM_RACE_SQL = f"""
SELECT
    COUNT(*) AS apm_zero_total,
    COUNT(*) FILTER (WHERE selectedRace = '') AS also_empty_race,
    COUNT(*) FILTER (WHERE selectedRace != '') AS has_selected_race
FROM matches_flat
WHERE APM = 0
  AND replay_id IN ({TRUE_1V1_SUBQ})
"""
r_apm2 = con.execute(APM_RACE_SQL).fetchone()
print(f"\nAPM=0 overlap: total={r_apm2[0]}, also_empty_race={r_apm2[1]}, has_selected_race={r_apm2[2]}")
print("Finding: 97.9% of APM=0 rows coincide with selectedRace=''. No cleaning rule applied.")

# %% [markdown]
# ## map_size=0 investigation
#
# 273 replays (1.22%) have gd_mapSizeX=0 AND gd_mapSizeY=0 (parse artifact).
# Action: FLAG (is_map_size_missing=TRUE; set mapSize to NULL in both VIEWs).
# Replays are NOT excluded if otherwise valid.

# %%
MAP_ZERO_SQL = """
SELECT
    COUNT(DISTINCT replay_id) AS n_replays,
    COUNT(*) AS n_player_rows,
    COUNT(*) FILTER (WHERE result = 'Win') AS wins,
    COUNT(*) FILTER (WHERE result = 'Loss') AS losses,
    COUNT(*) FILTER (WHERE result NOT IN ('Win', 'Loss')) AS other_results,
    COUNT(*) FILTER (WHERE MMR > 0) AS mmr_rated,
    COUNT(*) FILTER (WHERE MMR = 0) AS mmr_zero,
    ROUND(MEDIAN(header_elapsedGameLoops), 0) AS median_loops
FROM matches_flat
WHERE gd_mapSizeX = 0 AND gd_mapSizeY = 0
"""
r_map = con.execute(MAP_ZERO_SQL).fetchone()
print(f"map_size=0: replays={r_map[0]}, rows={r_map[1]}, wins={r_map[2]}, losses={r_map[3]}")
print(f"  other_results={r_map[4]}, mmr_rated={r_map[5]}, mmr_zero={r_map[6]}, median_loops={r_map[7]}")
assert r_map[0] == 273, f"Expected 273 map_size=0 replays, got {r_map[0]}"

MAP_ZERO_OVERLAP_SQL = f"""
SELECT
    COUNT(DISTINCT mf.replay_id) AS map_zero_replays,
    COUNT(DISTINCT mf.replay_id) FILTER (
        WHERE mf.replay_id IN ({TRUE_1V1_SUBQ})
    ) AS map_zero_and_1v1_decisive
FROM matches_flat mf
WHERE mf.gd_mapSizeX = 0 AND mf.gd_mapSizeY = 0
"""
r_map2 = con.execute(MAP_ZERO_OVERLAP_SQL).fetchone()
print(f"map_size=0 replays also in 1v1_decisive: {r_map2[1]} of {r_map2[0]}")

# %% [markdown]
# ## handicap=0 flag
#
# 2 rows with handicap=0 (standard=100). FLAG only, not excluded.

# %%
HANDICAP_SQL = """
SELECT replay_id, filename, nickname, playerID, MMR, handicap, result
FROM matches_flat
WHERE handicap = 0
"""
r_hc = con.execute(HANDICAP_SQL).df()
print(f"handicap=0 rows: {len(r_hc)}")
print(r_hc[["replay_id", "nickname", "MMR", "handicap", "result"]].to_string(index=False))
assert len(r_hc) == 2, f"Expected 2 handicap=0 rows, got {len(r_hc)}"

# %% [markdown]
# ## Create matches_flat_clean VIEW (prediction targets)
#
# Replay-level exclusion: all players in a replay must have MMR >= 0.
# Row-level filter would orphan opponent rows, so a CTE is used instead.
# In-game metrics (APM, SQ, supplyCappedPercent, header_elapsedGameLoops) excluded
# per temporal discipline. Constant gameSpeed columns excluded (cardinality=1).
# gd_isBlizzardMap excluded (confirmed identical to details_isBlizzardMap).
# No APM-derived flag columns added.

# %%
CREATE_MATCHES_FLAT_CLEAN_SQL = """
CREATE OR REPLACE VIEW matches_flat_clean AS
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
)
SELECT
    -- Identity
    mf.replay_id,
    mf.filename,
    mf.toon_id,
    mf.nickname,
    mf.playerID,
    mf.userID,

    -- Target
    mf.result,

    -- Pre-game player features
    mf.MMR,
    CASE WHEN mf.MMR = 0 THEN TRUE ELSE FALSE END AS is_mmr_missing,  -- flag MMR=0 as unrated sentinel
    mf.race,
    CASE WHEN mf.selectedRace = '' THEN 'Random'
         ELSE mf.selectedRace END AS selectedRace,                      -- normalise empty selectedRace to 'Random'

    mf.handicap,
    CASE WHEN mf.handicap = 0 THEN TRUE ELSE FALSE END AS is_handicap_anomalous, -- handicap=0 anomaly flag
    mf.region,
    mf.realm,
    mf.highestLeague,
    mf.isInClan,
    mf.clanTag,

    -- Pre-game spatial
    mf.startDir,
    mf.startLocX,
    mf.startLocY,

    -- Pre-game map metadata
    mf.metadata_mapName,
    CASE WHEN mf.gd_mapSizeX = 0 THEN NULL ELSE mf.gd_mapSizeX END AS gd_mapSizeX, -- map_size=0 anomaly flag
    CASE WHEN mf.gd_mapSizeY = 0 THEN NULL ELSE mf.gd_mapSizeY END AS gd_mapSizeY, -- map_size=0 anomaly flag
    CASE WHEN mf.gd_mapSizeX = 0 AND mf.gd_mapSizeY = 0 THEN TRUE
         ELSE FALSE END AS is_map_size_missing,                         -- map_size=0 anomaly flag
    mf.gd_maxPlayers,
    mf.gd_mapAuthorName,
    mf.gd_mapFileSyncChecksum,

    -- Pre-game Blizzard map flag (only details_ variant retained; gd_ is duplicate)
    mf.details_isBlizzardMap,

    -- Pre-game temporal anchor
    mf.details_timeUTC,

    -- Pre-game version
    mf.header_version,
    mf.metadata_baseBuild,
    mf.metadata_dataBuild,
    mf.metadata_gameVersion,

    -- Pre-game game options
    mf.go_advancedSharedControl,
    mf.go_amm,
    mf.go_battleNet,
    mf.go_clientDebugFlags,
    mf.go_competitive,
    mf.go_cooperative,
    mf.go_fog,
    mf.go_heroDuplicatesAllowed,
    mf.go_lockTeams,
    mf.go_noVictoryOrDefeat,
    mf.go_observers,
    mf.go_practice,
    mf.go_randomRaces,
    mf.go_teamsTogether,
    mf.go_userDifficulty

FROM matches_flat mf
JOIN true_1v1_decisive t1v1 ON mf.replay_id = t1v1.replay_id  -- filter to true 1v1 decisive only
JOIN mmr_valid mv ON mf.replay_id = mv.replay_id;             -- replay-level MMR exclusion
"""

con.execute(CREATE_MATCHES_FLAT_CLEAN_SQL)
print("matches_flat_clean VIEW created.")

# %% [markdown]
# ## matches_flat_clean validation

# %%
r_clean = con.execute(
    "SELECT COUNT(*) AS total, COUNT(DISTINCT replay_id) AS replays FROM matches_flat_clean"
).fetchone()
print(f"matches_flat_clean: rows={r_clean[0]}, replays={r_clean[1]}")

r_bad_result = con.execute(
    "SELECT COUNT(*) FROM matches_flat_clean WHERE result NOT IN ('Win','Loss')"
).fetchone()
print(f"Non-Win/Loss results: {r_bad_result[0]}")
assert r_bad_result[0] == 0

r_mmr_neg = con.execute("SELECT COUNT(*) FROM matches_flat_clean WHERE MMR < 0").fetchone()
print(f"MMR<0 rows: {r_mmr_neg[0]}")
assert r_mmr_neg[0] == 0

r_empty_race = con.execute(
    "SELECT COUNT(*) FROM matches_flat_clean WHERE selectedRace = ''"
).fetchone()
print(f"Empty selectedRace: {r_empty_race[0]}")
assert r_empty_race[0] == 0

r_null_id = con.execute(
    "SELECT COUNT(*) FROM matches_flat_clean WHERE replay_id IS NULL"
).fetchone()
print(f"NULL replay_id: {r_null_id[0]}")
assert r_null_id[0] == 0

# %% [markdown]
# ## Create player_history_all VIEW (player feature history)
#
# All replays, all game types, including non-1v1 and indecisive replays.
# Retains APM, SQ, supplyCappedPercent as valid in-game historical signals.
# Temporal discipline applies: these are valid for prior matches, prohibited for the target match only.
# SQ parse-failure sentinel (-2147483648) corrected to NULL.
# Empty selectedRace normalised to 'Random'.
# MMR<0 rows RETAINED (MMR value unreliable, but game context usable).

# %%
CREATE_PLAYER_HISTORY_SQL = """
CREATE OR REPLACE VIEW player_history_all AS
SELECT
    -- Identity and join keys
    mf.replay_id,
    mf.filename,
    mf.toon_id,
    mf.nickname,
    mf.playerID,
    mf.userID,

    -- Result (unfiltered -- includes Win, Loss, Undecided, Tie)
    mf.result,

    -- Player pre-game features
    mf.MMR,
    CASE WHEN mf.MMR = 0 THEN TRUE ELSE FALSE END AS is_mmr_missing,  -- flag MMR=0 as unrated sentinel

    mf.race,
    CASE WHEN mf.selectedRace = '' THEN 'Random'
         ELSE mf.selectedRace END AS selectedRace,                      -- normalise empty selectedRace to 'Random'

    mf.handicap,
    mf.region,
    mf.realm,
    mf.highestLeague,
    mf.isInClan,
    mf.clanTag,

    -- In-game metrics (valid in player history for historical features).
    -- Temporal discipline: excluded from matches_flat_clean (prediction targets) but
    -- legitimate historical signals for prior matches only.
    mf.APM,
    CASE WHEN mf.SQ = -2147483648 THEN NULL ELSE mf.SQ END AS SQ,     -- correct parse-failure sentinel to NULL
    mf.supplyCappedPercent,

    -- Game duration (historical signal -- valid for past matches)
    mf.header_elapsedGameLoops,

    -- Pre-game spatial
    mf.startDir,
    mf.startLocX,
    mf.startLocY,

    -- Map metadata
    mf.metadata_mapName,
    CASE WHEN mf.gd_mapSizeX = 0 THEN NULL ELSE mf.gd_mapSizeX END AS gd_mapSizeX, -- map_size=0 anomaly flag
    CASE WHEN mf.gd_mapSizeY = 0 THEN NULL ELSE mf.gd_mapSizeY END AS gd_mapSizeY, -- map_size=0 anomaly flag
    mf.gd_maxPlayers,
    mf.details_isBlizzardMap,
    mf.gd_mapAuthorName,
    mf.gd_mapFileSyncChecksum,

    -- Temporal anchor (critical for I3 temporal ordering)
    mf.details_timeUTC,

    -- Version context (for patch-period stratification)
    mf.header_version,
    mf.metadata_baseBuild,
    mf.metadata_dataBuild,
    mf.metadata_gameVersion,

    -- Game options (for context; Phase 02 feature selection will prune constants)
    mf.go_advancedSharedControl,
    mf.go_amm,
    mf.go_battleNet,
    mf.go_clientDebugFlags,
    mf.go_competitive,
    mf.go_cooperative,
    mf.go_fog,
    mf.go_heroDuplicatesAllowed,
    mf.go_lockTeams,
    mf.go_noVictoryOrDefeat,
    mf.go_observers,
    mf.go_practice,
    mf.go_randomRaces,
    mf.go_teamsTogether,
    mf.go_userDifficulty

FROM matches_flat mf
WHERE mf.replay_id IS NOT NULL;  -- exclude any rows where replay_id extraction failed (empty-string guard)
"""

con.execute(CREATE_PLAYER_HISTORY_SQL)
print("player_history_all VIEW created.")

# %% [markdown]
# ## player_history_all validation

# %%
r_hist = con.execute(
    "SELECT COUNT(*) AS total_rows, COUNT(DISTINCT replay_id) AS distinct_replays FROM player_history_all"
).fetchone()
print(f"player_history_all: rows={r_hist[0]}, replays={r_hist[1]}")
assert r_hist[0] == 44817, f"Expected 44817 rows, got {r_hist[0]}"
assert r_hist[1] == 22390, f"Expected 22390 replays, got {r_hist[1]}"

r_sq_sentinel = con.execute(
    "SELECT COUNT(*) FROM player_history_all WHERE SQ = -2147483648"
).fetchone()
print(f"SQ sentinel rows: {r_sq_sentinel[0]}")
assert r_sq_sentinel[0] == 0

r_empty_race_h = con.execute(
    "SELECT COUNT(*) FROM player_history_all WHERE selectedRace = ''"
).fetchone()
print(f"Empty selectedRace: {r_empty_race_h[0]}")
assert r_empty_race_h[0] == 0

r_apm_h = con.execute(
    "SELECT COUNT(*) FILTER (WHERE APM IS NOT NULL) AS apm_present FROM player_history_all"
).fetchone()
print(f"APM present rows: {r_apm_h[0]}")
assert r_apm_h[0] == 44817

# %% [markdown]
# ## CONSORT flow accounting
#
# Tracks replay-level counts at each filtering stage.
# MMR exclusion recorded in replay units (not row units).

# %%
flow = {}

flow["raw_player_rows"] = con.execute(
    "SELECT COUNT(*) FROM replay_players_raw"
).fetchone()[0]
flow["raw_replays"] = con.execute(
    "SELECT COUNT(*) FROM replays_meta_raw"
).fetchone()[0]
flow["matches_flat_rows"] = con.execute(
    "SELECT COUNT(*) FROM matches_flat"
).fetchone()[0]
flow["matches_flat_replays"] = con.execute(
    "SELECT COUNT(DISTINCT replay_id) FROM matches_flat"
).fetchone()[0]

r01_subquery = """SELECT replay_id FROM matches_flat GROUP BY replay_id
    HAVING COUNT(*) = 2
       AND COUNT(*) FILTER (WHERE result = 'Win') = 1
       AND COUNT(*) FILTER (WHERE result = 'Loss') = 1"""

flow["after_r01_replays"] = con.execute(
    f"SELECT COUNT(*) FROM ({r01_subquery})"
).fetchone()[0]
flow["r01_excluded_replays"] = flow["matches_flat_replays"] - flow["after_r01_replays"]
flow["after_r01_rows"] = con.execute(
    f"SELECT COUNT(*) FROM matches_flat WHERE replay_id IN ({r01_subquery})"
).fetchone()[0]
flow["r01_excluded_rows"] = flow["matches_flat_rows"] - flow["after_r01_rows"]

# MMR<0 replay-level exclusion
flow["r03_excluded_replays"] = con.execute(f"""
    SELECT COUNT(*) FROM (
        SELECT replay_id FROM matches_flat
        WHERE replay_id IN ({r01_subquery})
        GROUP BY replay_id
        HAVING COUNT(*) FILTER (WHERE MMR < 0) > 0
    )
""").fetchone()[0]
flow["r03_excluded_rows"] = flow["r03_excluded_replays"] * 2  # 1v1: 2 rows per replay

flow["clean_rows"] = con.execute(
    "SELECT COUNT(*) FROM matches_flat_clean"
).fetchone()[0]
flow["clean_replays"] = con.execute(
    "SELECT COUNT(DISTINCT replay_id) FROM matches_flat_clean"
).fetchone()[0]
flow["history_rows"] = con.execute(
    "SELECT COUNT(*) FROM player_history_all"
).fetchone()[0]
flow["history_replays"] = con.execute(
    "SELECT COUNT(DISTINCT replay_id) FROM player_history_all"
).fetchone()[0]

print("CONSORT flow:")
for k, v in flow.items():
    print(f"  {k}: {v}")

assert flow["clean_replays"] == (
    flow["after_r01_replays"] - flow["r03_excluded_replays"]
), "CONSORT arithmetic failure: non-1v1/indecisive + MMR<0 replay counts do not sum correctly"
assert flow["clean_rows"] == flow["clean_replays"] * 2, (
    "CONSORT row count failure: clean rows should be exactly 2x clean replays"
)
print("CONSORT flow verified.")

# %% [markdown]
# ## Post-cleaning validation

# %%
# Result distribution (~50/50)
RESULT_DIST_SQL = """
SELECT result, COUNT(*) AS cnt,
       ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER(),4) AS pct
FROM matches_flat_clean GROUP BY result ORDER BY result
"""
r_result = con.execute(RESULT_DIST_SQL).df()
print("Result distribution:")
print(r_result.to_string(index=False))

# Race distribution (only Protoss, Zerg, Terran abbreviated variants)
RACE_DIST_SQL = "SELECT race, COUNT(*) AS cnt FROM matches_flat_clean GROUP BY race ORDER BY cnt DESC"
r_race = con.execute(RACE_DIST_SQL).df()
print(f"\nRace distribution:\n{r_race.to_string(index=False)}")

# selectedRace distribution (no empty strings)
SR_DIST_SQL = """
SELECT selectedRace, COUNT(*) AS cnt FROM matches_flat_clean
GROUP BY selectedRace ORDER BY cnt DESC
"""
r_sr2 = con.execute(SR_DIST_SQL).df()
print(f"\nselectedRace distribution:\n{r_sr2.to_string(index=False)}")

# MMR stats (rated-only)
MMR_STATS_SQL = """
SELECT COUNT(*) AS rated_rows,
       MIN(MMR) AS mmr_min, MAX(MMR) AS mmr_max,
       ROUND(AVG(MMR), 2) AS mmr_mean
FROM matches_flat_clean WHERE is_mmr_missing = FALSE
"""
r_mmr_stats = con.execute(MMR_STATS_SQL).fetchone()
print(f"\nMMR (rated): rows={r_mmr_stats[0]}, min={r_mmr_stats[1]}, max={r_mmr_stats[2]}, mean={r_mmr_stats[3]}")

# Null rate on critical columns (replay_id NULL check)
NULL_CHECK_SQL = """
SELECT
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE replay_id IS NULL) AS null_replay_id,
    COUNT(*) FILTER (WHERE result IS NULL) AS null_result,
    COUNT(*) FILTER (WHERE race IS NULL) AS null_race,
    COUNT(*) FILTER (WHERE selectedRace IS NULL) AS null_selectedRace,
    COUNT(*) FILTER (WHERE toon_id IS NULL) AS null_toon_id,
    COUNT(*) FILTER (WHERE details_timeUTC IS NULL) AS null_timeUTC
FROM matches_flat_clean
"""
r_null_check = con.execute(NULL_CHECK_SQL).fetchone()
print(f"\nNull check: total={r_null_check[0]}, null_replay_id={r_null_check[1]}, "
      f"null_result={r_null_check[2]}, null_race={r_null_check[3]}, "
      f"null_selectedRace={r_null_check[4]}, null_toon_id={r_null_check[5]}")
assert r_null_check[1] == 0, "replay_id has NULLs"
assert r_null_check[2] == 0, "result has NULLs"
assert r_null_check[3] == 0, "race has NULLs"
assert r_null_check[4] == 0, "selectedRace has NULLs"

# %% [markdown]
# ## Column exclusion assertion (temporal discipline + constant and duplicate columns)

# %%
clean_cols = set(con.execute("DESCRIBE matches_flat_clean").df()["column_name"])

# in-game and post-game metrics (temporal discipline)
forbidden_i3 = {"APM", "SQ", "supplyCappedPercent", "header_elapsedGameLoops"}

# constant columns (cardinality=1 across all replays)
forbidden_w02 = {"details_gameSpeed", "gd_gameSpeed"}

# duplicate column (confirmed identical to details_isBlizzardMap)
forbidden_w03 = {"gd_isBlizzardMap"}

# APM-derived flags (not added per documentation-only decision)
forbidden_w05 = {"apm_zero_flag", "is_apm_zero"}

# Cosmetic
forbidden_cosmetic = {"color_a", "color_b", "color_g", "color_r"}

all_forbidden = forbidden_i3 | forbidden_w02 | forbidden_w03 | forbidden_w05 | forbidden_cosmetic
violations = all_forbidden & clean_cols
assert len(violations) == 0, f"Forbidden columns in matches_flat_clean: {violations}"
print(f"Column exclusion validation passed (temporal discipline, constant cols, duplicate col, cosmetic). {len(clean_cols)} columns.")
print(f"Clean columns: {sorted(clean_cols)}")

# Symmetry check
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
r_sym = con.execute(SYMMETRY_SQL).fetchone()
print(f"\nSymmetry violations (must be 0): {r_sym[0]}")
assert r_sym[0] == 0, "Symmetry violation detected"

# %% [markdown]
# ## player_history_all structural checks

# %%
SCOPE_SQL = """
SELECT
    CASE
        WHEN replay_id IN (SELECT replay_id FROM matches_flat_clean)
        THEN 'in_prediction_scope'
        ELSE 'history_only'
    END AS scope,
    COUNT(*) AS n_rows,
    COUNT(DISTINCT replay_id) AS n_replays
FROM player_history_all
GROUP BY scope
"""
r_scope = con.execute(SCOPE_SQL).df()
print("player_history_all scope comparison:")
print(r_scope.to_string(index=False))

r_uniq = con.execute(
    "SELECT COUNT(*) AS history_rows, COUNT(DISTINCT replay_id) AS history_replays, "
    "COUNT(DISTINCT toon_id) AS unique_players FROM player_history_all"
).fetchone()
print(f"\nplayer_history_all: rows={r_uniq[0]}, replays={r_uniq[1]}, unique_players={r_uniq[2]}")

APM_CHECK_SQL = """
SELECT
    COUNT(*) FILTER (WHERE APM IS NOT NULL) AS apm_present,
    COUNT(*) FILTER (WHERE APM = 0) AS apm_zero_count
FROM player_history_all
"""
r_apm_check = con.execute(APM_CHECK_SQL).fetchone()
print(f"APM present={r_apm_check[0]}, APM=0 count={r_apm_check[1]}")

# %% [markdown]
# ## NULL audit: matches_flat_clean
#
# Systematic per-column NULL census using exact integer counting.
# Hard assertions: replay_id, toon_id, result must have zero NULLs.
# Expected NULLs: some go_* game option columns, clanTag, gd_mapAuthorName.

# %%
_cols_mfc = con.execute("DESCRIBE matches_flat_clean").df()["column_name"].tolist()
_total_mfc = con.execute("SELECT COUNT(*) AS n FROM matches_flat_clean").fetchone()[0]
_rows_mfc = []
for _col in _cols_mfc:
    _nc = con.execute(
        f'SELECT COUNT(*) FILTER (WHERE "{_col}" IS NULL) AS n FROM matches_flat_clean'
    ).fetchone()[0]
    _rows_mfc.append({
        "column_name": _col,
        "null_count": int(_nc),
        "total_count": int(_total_mfc),
        "null_pct": round(100.0 * _nc / _total_mfc, 4) if _total_mfc > 0 else 0.0,
    })
df_null_matches = pd.DataFrame(_rows_mfc).sort_values("null_count", ascending=False)
print("NULL audit — matches_flat_clean:")
print(df_null_matches.to_string(index=False))
print(f"\nColumns with NULLs: {int((df_null_matches['null_count'] > 0).sum())}")
print(f"Columns fully populated: {int((df_null_matches['null_count'] == 0).sum())}")

# Hard assertions: identity and target columns must have zero NULLs
for col_name in ["replay_id", "toon_id", "result"]:
    null_val = int(
        df_null_matches.loc[df_null_matches["column_name"] == col_name, "null_count"].iloc[0]
    )
    assert null_val == 0, f"{col_name} has {null_val} NULLs in matches_flat_clean"
    print(f"ASSERT PASSED: {col_name} NULL count = 0")

# %% [markdown]
# ## NULL audit: player_history_all
#
# player_history_all includes ALL replays (non-1v1, indecisive).
# result is never NULL but may be 'Undecided' or 'Tie'.
# SQ has expected NULLs from INT32_MIN sentinel correction (R05).

# %%
_cols_hist = con.execute("DESCRIBE player_history_all").df()["column_name"].tolist()
_total_hist = con.execute("SELECT COUNT(*) AS n FROM player_history_all").fetchone()[0]
_rows_hist = []
for _col in _cols_hist:
    _nc = con.execute(
        f'SELECT COUNT(*) FILTER (WHERE "{_col}" IS NULL) AS n FROM player_history_all'
    ).fetchone()[0]
    _rows_hist.append({
        "column_name": _col,
        "null_count": int(_nc),
        "total_count": int(_total_hist),
        "null_pct": round(100.0 * _nc / _total_hist, 4) if _total_hist > 0 else 0.0,
    })
df_null_hist = pd.DataFrame(_rows_hist).sort_values("null_count", ascending=False)
print("NULL audit — player_history_all:")
print(df_null_hist.to_string(index=False))
print(f"\nColumns with NULLs: {int((df_null_hist['null_count'] > 0).sum())}")
print(f"Columns fully populated: {int((df_null_hist['null_count'] == 0).sum())}")

# Hard assertions: identity columns must have zero NULLs
for col_name in ["replay_id", "toon_id"]:
    null_val = int(
        df_null_hist.loc[df_null_hist["column_name"] == col_name, "null_count"].iloc[0]
    )
    assert null_val == 0, f"{col_name} has {null_val} NULLs in player_history_all"
    print(f"ASSERT PASSED: {col_name} NULL count = 0")

# result must not be NULL (may be 'Undecided'/'Tie'/'Win'/'Loss' but never NULL)
result_nulls = int(
    df_null_hist.loc[df_null_hist["column_name"] == "result", "null_count"].iloc[0]
)
assert result_nulls == 0, f"result has {result_nulls} NULLs in player_history_all"
print(f"ASSERT PASSED: result NULL count = 0 (Win/Loss/Undecided/Tie — never NULL)")

# Document expected NULLs in SQ (R05 sentinel correction)
sq_nulls = int(
    df_null_hist.loc[df_null_hist["column_name"] == "SQ", "null_count"].iloc[0]
)
print(f"EXPECTED: SQ has {sq_nulls} NULLs (R05 INT32_MIN sentinel → NULL correction)")

# %% [markdown]
# ## Missingness Audit — Framing
#
# **Theoretical grounding:**
# - Rubin (1976) / Little & Rubin (2019, 3rd ed.) MCAR/MAR/MNAR taxonomy.
# - van Buuren (2018) warns against rigid percentage thresholds; thresholds 5/40/80%
#   are operational starting heuristics, not hard rules.
# - Schafer & Graham (2002) cite <5% MCAR as the boundary where listwise deletion
#   is unbiased.
# - Sambasivan et al. (2021) — data cascades: document decisions explicitly.
#
# **Audit scope (Invariant I9):** Phase 01 documents and recommends only.
# The audit produces a missingness ledger and surfaces decisions for 01_04_02+.
# It does NOT execute decisions, modify VIEWs, drop columns, or impute.
#
# **Three coordinated steps per VIEW:**
# 1. Pass 1 (already executed above): SQL NULL census.
# 2. Pass 2 (NEW): sentinel census per column driven by _missingness_spec dict.
# 3. Pass 3 (NEW): runtime constants detection — COUNT(DISTINCT) per column.
#    Columns with n_distinct=1 get mechanism="N/A" + recommendation="DROP_COLUMN".

# %% [markdown]
# ## Missingness Spec + Helper Functions (DRY — W4 uniform)

# %%
_missingness_spec = {
    # Identity columns (S1) — sentinel=None, mechanism=N/A, asserted zero
    # (no entries needed — handled by zero-NULL assertions)

    # Player pre-game features
    "MMR": {
        "mechanism": "MAR",
        "justification": (
            "MAR-primary: missingness depends on observed replay source "
            "(tournament replays lack ladder MMR). MNAR (private pro accounts) "
            "documented as sensitivity branch. Source: 01_03_01 cleaning_registry "
            "+ temp/null_handling_recommendations.md §4.1."
        ),
        "sentinel_value": 0,
        "carries_semantic_content": True,  # MMR=0 = 'unranked', MMR=NULL = 'data missing'
        "is_primary_feature": True,
    },
    "highestLeague": {
        "mechanism": "MAR",
        "justification": "Tournament replays lack league exposure data. Source: 01_02_04 census top-N.",
        "sentinel_value": "Unknown",
        "carries_semantic_content": True,
        "is_primary_feature": False,
    },
    "clanTag": {
        "mechanism": "MAR",
        "justification": "Not all players are in clans. Source: domain knowledge + 01_02_04 distribution.",
        "sentinel_value": "",
        "carries_semantic_content": True,
        "is_primary_feature": False,
    },
    "selectedRace": {
        "mechanism": "MAR",
        "justification": "Empty string = Random race; resolved post-game. VIEWs convert to 'Random'. Source: 01_03_02.",
        "sentinel_value": "",
        "carries_semantic_content": True,
        "is_primary_feature": False,
    },
    "result": {
        "mechanism": "MNAR",
        "justification": "Game crashed/ended abnormally. Source: 01_03_02.",
        "sentinel_value": ["Undecided", "Tie"],
        "carries_semantic_content": True,
        "is_primary_feature": False,  # but is the prediction TARGET — handled by target-override post-step (Rule S2)
    },

    # Map metadata
    "gd_mapSizeX": {
        "mechanism": "MCAR",
        "justification": "Parse artifact (273 replays). Not correlated with outcome. Source: 01_02_04 + 01_03_01.",
        "sentinel_value": 0,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },
    "gd_mapSizeY": {
        "mechanism": "MCAR",
        "justification": "Same parse artifact as gd_mapSizeX (same 273 replays).",
        "sentinel_value": 0,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },
    "gd_mapAuthorName": {
        "mechanism": "MAR",
        "justification": "Map metadata not parsed for all replays. Likely non-predictive.",
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },
    "handicap": {
        "mechanism": "MCAR",
        "justification": "Standard handicap=100; 2 anomalous rows have 0. Source: 01_02_04.",
        "sentinel_value": 0,
        "carries_semantic_content": True,
        "is_primary_feature": False,
    },

    # In-game (player_history_all only)
    "SQ": {
        "mechanism": "MCAR",
        "justification": "INT32_MIN sentinel = parse failure (2 rows). Source: 01_03_01.",
        "sentinel_value": -2147483648,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },
    "APM": {
        "mechanism": "MAR",
        "justification": (
            "APM=0 correlates with selectedRace='' (97.9% overlap). Documentation-only "
            "in 01_04_01 — not converted to NULL. In-game; not in matches_flat_clean."
        ),
        "sentinel_value": 0,
        "carries_semantic_content": True,
        "is_primary_feature": False,
    },

    # go_* game options (W7 fix — enumerated; constants-detection branch backs up
    # any constant). For variable-cardinality go_* columns, mechanism is MAR
    # (game option metadata not parsed for all replays). Constants are flagged at
    # runtime; spec entries here are documentation + defense-in-depth.
    "go_advancedSharedControl": {
        "mechanism": "MAR",
        "justification": "Game option metadata; cardinality from 01_02_04 to be confirmed at audit runtime. Constants-detection branch overrides if n_distinct=1.",
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },
    "go_amm":              {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_battleNet":        {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_clientDebugFlags": {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_competitive":      {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_cooperative":      {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_fog":              {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_heroDuplicatesAllowed": {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_lockTeams":        {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_noVictoryOrDefeat":{"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_observers":        {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_practice":         {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_randomRaces":      {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_teamsTogether":    {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_userDifficulty":   {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},

    # All other columns default to spec absence → conservative MAR fallback;
    # constants-detection branch overrides for any n_distinct=1 column.
}


def _build_sentinel_predicate(col, sentinel_value):
    """Construct the SQL predicate for sentinel matching.

    Returns (predicate_sql, sentinel_repr) or (None, None) when no sentinel declared.
    """
    if sentinel_value is None:
        return None, None
    if isinstance(sentinel_value, list):
        quoted = []
        for v in sentinel_value:
            if isinstance(v, str):
                quoted.append("'" + v.replace("'", "''") + "'")
            else:
                quoted.append(repr(v))
        return f'IN ({", ".join(quoted)})', repr(sentinel_value)
    if isinstance(sentinel_value, str):
        escaped = sentinel_value.replace("'", "''")
        return f"= '{escaped}'", repr(sentinel_value)
    return f"= {sentinel_value!r}", repr(sentinel_value)


def _sentinel_census(view_name, total_rows, spec):
    """Run sentinel COUNT(*) FILTER per spec'd column. Returns list of dicts."""
    rows = []
    for col, meta in spec.items():
        sentinel_value = meta["sentinel_value"]
        predicate, sentinel_repr = _build_sentinel_predicate(col, sentinel_value)
        if predicate is None:
            n_sentinel = 0
        else:
            sql = f'SELECT COUNT(*) FILTER (WHERE "{col}" {predicate}) FROM {view_name}'
            try:
                n_sentinel = con.execute(sql).fetchone()[0]
            except Exception:
                # column not present in this VIEW — skip
                n_sentinel = 0
        pct_sentinel = round(100.0 * n_sentinel / total_rows, 4) if total_rows > 0 else 0.0
        rows.append({
            "column": col,
            "sentinel_value": sentinel_repr,
            "n_sentinel": int(n_sentinel),
            "pct_sentinel": float(pct_sentinel),
        })
    return rows


def _detect_constants(view_name, columns, identity_cols=frozenset()):
    """Per-column n_distinct check. Returns {col: n_distinct}.

    W6 mitigation: identity columns are skipped (expensive + never constant by definition).
    """
    out = {}
    for col in columns:
        if col in identity_cols:
            out[col] = None  # skipped; constants check N/A
            continue
        sql = f'SELECT COUNT(DISTINCT "{col}") FROM {view_name}'
        out[col] = int(con.execute(sql).fetchone()[0])
    return out


def _recommend(col, mechanism, pct, is_primary, n_null, n_sentinel):
    """Decision tree per temp/null_handling_recommendations.md §3.1.

    Returns (recommendation_code, justification_text).
    """
    # W3 fix: CONVERT_SENTINEL_TO_NULL branch — fires for sentinel-only low-rate cases.
    if n_sentinel > 0 and n_null == 0 and pct < 5.0:
        return "CONVERT_SENTINEL_TO_NULL", (
            f"Low sentinel rate ({pct:.4f}%); convert sentinel to NULL via "
            f"NULLIF in 01_04_02+ DDL pass per Rule S3 (negligible rate). "
            f"Listwise deletion or simple imputation acceptable in Phase 02. "
            f"NOTE: if carries_semantic_content=True (consult ledger column), "
            f"this recommendation is non-binding — see corresponding DS entry "
            f"for the retain-as-category alternative."
        )
    if pct == 0.0:
        return "RETAIN_AS_IS", "Zero missingness observed; no action needed."
    if pct > 80.0:
        return "DROP_COLUMN", (
            f"NULL+sentinel rate {pct:.2f}% exceeds 80% (Rule S4 / van Buuren 2018). "
            f"Imputation indefensible at this rate."
        )
    if pct > 40.0:
        if mechanism == "MNAR":
            return "DROP_COLUMN", (
                f"Rate {pct:.2f}% in 40-80% MNAR band; no defensible imputation. "
                f"Drop unless domain knowledge provides correction."
            )
        if is_primary:
            return "FLAG_FOR_IMPUTATION", (
                f"Rate {pct:.2f}% in 40-80%; primary feature exception per Rule S4. "
                f"Phase 02: conditional imputation + add_indicator."
            )
        return "DROP_COLUMN", (
            f"Rate {pct:.2f}% in 40-80%; non-primary feature; cost/benefit favors "
            f"simplicity per Rule S4."
        )
    if pct > 5.0:
        return "FLAG_FOR_IMPUTATION", (
            f"Rate {pct:.2f}% in 5-40%; flag for Phase 02 imputation "
            f"(conditional for MAR, simple for MCAR per Rules from §3.1)."
        )
    # pct < 5%, with at least one NULL (sentinel-only case handled above)
    return "RETAIN_AS_IS", (
        f"Rate {pct:.2f}% < 5% (Schafer & Graham 2002 boundary citation). "
        f"Listwise deletion or simple imputation acceptable in Phase 02."
    )


def _consolidate_ledger(view_name, df_null, sentinel_rows, spec, dtype_map,
                         total_rows, constants_map, target_cols, identity_cols=frozenset()):
    """Merge NULL census + sentinel census + constants detection + spec → one ledger row
    per (view, column). Full-coverage scope (Option B). identity_cols routed to B5 branch.
    """
    sentinel_map = {r["column"]: r for r in sentinel_rows}
    ledger = []
    for _, nrow in df_null.iterrows():
        col = nrow["column_name"] if "column_name" in nrow else nrow["column"]
        n_null = int(nrow["null_count"])
        pct_null = float(nrow.get("null_pct", round(100.0 * n_null / total_rows, 4)))
        srow = sentinel_map.get(col, {"sentinel_value": None, "n_sentinel": 0, "pct_sentinel": 0.0})
        n_sentinel = int(srow["n_sentinel"])
        pct_sentinel = float(srow["pct_sentinel"])
        n_total_missing = n_null + n_sentinel
        pct_missing_total = round(pct_null + pct_sentinel, 4)
        spec_entry = spec.get(col)
        n_distinct = constants_map.get(col, None)

        # Override priority (B4 + B5 + W7):
        # B5 fix: identity columns routed first.
        if col in identity_cols:
            mechanism = "N/A"
            mech_just = (
                f"Identity column; n_distinct check skipped per W6 (constants-detection "
                f"runtime budget). Zero NULLs by definition (asserted upstream)."
            )
            carries_sem = False
            is_primary = False
            rec = "RETAIN_AS_IS"
            rec_just = "Identity column; no missingness possible by upstream assertion."
        # W7 fix: TRUE-constants check requires zero NULLs AND zero sentinels.
        elif n_distinct == 1 and n_null == 0 and n_sentinel == 0:
            mechanism = "N/A"
            mech_just = (
                f"True constant column; n_distinct=1 across {total_rows:,} rows "
                f"(zero NULLs, zero sentinels). No information content for prediction. "
                f"Recommend drop in 01_04_02+."
            )
            carries_sem = False
            is_primary = False
            rec = "DROP_COLUMN"
            rec_just = "True constant column; n_distinct=1; no information content."
        elif n_total_missing == 0:
            mechanism = "N/A"
            mech_just = "Zero missingness observed; no action needed."
            carries_sem = bool(spec_entry["carries_semantic_content"]) if spec_entry else False
            is_primary = bool(spec_entry["is_primary_feature"]) if spec_entry else False
            rec = "RETAIN_AS_IS"
            rec_just = "Zero missingness observed; no action needed."
        elif spec_entry is not None:
            mechanism = spec_entry["mechanism"]
            mech_just = spec_entry["justification"]
            carries_sem = bool(spec_entry["carries_semantic_content"])
            is_primary = bool(spec_entry["is_primary_feature"])
            rec, rec_just = _recommend(col, mechanism, pct_missing_total,
                                       is_primary, n_null, n_sentinel)
        else:
            mechanism = "MAR"
            mech_just = (
                f"No _missingness_spec entry; conservative MAR assumption. "
                f"Observed effective missingness {pct_missing_total:.2f}% "
                f"(NULL: {pct_null:.2f}%, sentinel: {pct_sentinel:.2f}%)."
            )
            carries_sem = False
            is_primary = False
            rec, rec_just = _recommend(col, mechanism, pct_missing_total,
                                       is_primary, n_null, n_sentinel)

        # Target-column post-step (B4 fix)
        if col in target_cols and n_total_missing > 0:
            rec = "EXCLUDE_TARGET_NULL_ROWS"
            rec_just = (
                "Per Rule S2: target NULLs/sentinels excluded from prediction "
                "scope, retained in history for feature computation. "
                "NEVER impute target."
            )

        ledger.append({
            "view": view_name,
            "column": col,
            "dtype": dtype_map.get(col, "UNKNOWN"),
            "n_total": int(total_rows),
            "n_null": n_null, "pct_null": pct_null,
            "sentinel_value": srow["sentinel_value"],
            "n_sentinel": n_sentinel, "pct_sentinel": pct_sentinel,
            "pct_missing_total": pct_missing_total,
            "n_distinct": n_distinct,
            "mechanism": mechanism,
            "mechanism_justification": mech_just,
            "recommendation": rec,
            "recommendation_justification": rec_just,
            "carries_semantic_content": carries_sem,
            "is_primary_feature": is_primary,
        })
    return pd.DataFrame(ledger)


print("_missingness_spec loaded with", len(_missingness_spec), "entries.")
print("Helper functions defined: _build_sentinel_predicate, _sentinel_census, _detect_constants,")
print("  _consolidate_ledger, _recommend.")

# %% [markdown]
# ## Pass 2 — Sentinel census + constants detection + ledger: matches_flat_clean

# %%
_view_mfc = "matches_flat_clean"
_target_cols_mfc = {"result"}
_identity_cols_mfc = {"replay_id", "toon_id"}

# dtype map from DESCRIBE
_describe_mfc = con.execute(f"DESCRIBE {_view_mfc}").df()
_dtype_map_mfc = dict(zip(_describe_mfc["column_name"], _describe_mfc["column_type"]))
_cols_list_mfc = _describe_mfc["column_name"].tolist()
_total_mfc_rows = con.execute(f"SELECT COUNT(*) FROM {_view_mfc}").fetchone()[0]

# Sentinel census (Pass 2)
sentinel_rows_mfc = _sentinel_census(_view_mfc, _total_mfc_rows, _missingness_spec)
print(f"Sentinel census for {_view_mfc}: {len(sentinel_rows_mfc)} spec columns processed.")

# Constants detection (Pass 3)
constants_map_mfc = _detect_constants(_view_mfc, _cols_list_mfc, _identity_cols_mfc)
n_const_mfc = sum(1 for v in constants_map_mfc.values() if v == 1)
print(f"Constants detection for {_view_mfc}: {n_const_mfc} column(s) with n_distinct=1.")

# Consolidate ledger
df_ledger_mfc = _consolidate_ledger(
    _view_mfc, df_null_matches, sentinel_rows_mfc, _missingness_spec, _dtype_map_mfc,
    _total_mfc_rows, constants_map_mfc, _target_cols_mfc, _identity_cols_mfc
)

print(f"\nLedger for {_view_mfc}: {len(df_ledger_mfc)} rows (one per column).")
print(df_ledger_mfc[["column", "n_null", "n_sentinel", "pct_missing_total",
                       "mechanism", "recommendation"]].to_string(index=False))

# --- Assertion battery (6.B + 6.C) ---
# Full-coverage assertion
_n_view_cols_mfc = int(con.execute(f"DESCRIBE {_view_mfc}").df().shape[0])
assert len(df_ledger_mfc) == _n_view_cols_mfc, (
    f"Full-coverage ledger required for {_view_mfc}: expected {_n_view_cols_mfc} rows, "
    f"got {len(df_ledger_mfc)}"
)
print(f"ASSERT PASSED: ledger full coverage ({len(df_ledger_mfc)} == {_n_view_cols_mfc})")

# Mechanism + recommendation enum
for _, _row in df_ledger_mfc.iterrows():
    assert _row["mechanism"] in {"MAR", "MCAR", "MNAR", "N/A"}, _row.to_dict()
    assert _row["mechanism_justification"], f"empty mechanism justification for {_row['column']}"
    assert _row["recommendation"] in {
        "DROP_COLUMN", "FLAG_FOR_IMPUTATION", "RETAIN_AS_IS",
        "EXCLUDE_TARGET_NULL_ROWS", "CONVERT_SENTINEL_TO_NULL"
    }, _row.to_dict()
    assert _row["recommendation_justification"], _row.to_dict()
    assert isinstance(_row["carries_semantic_content"], (bool, np.bool_)), _row.to_dict()
print("ASSERT PASSED: all ledger rows have valid mechanism + recommendation + justifications")

# Zero-missingness rows: must have N/A mechanism + RETAIN_AS_IS (F1 + Option B)
_zero_mfc = df_ledger_mfc[
    (df_ledger_mfc["n_null"] == 0) &
    (df_ledger_mfc["n_sentinel"] == 0) &
    (df_ledger_mfc["n_distinct"].fillna(-1) != 1) &
    (~df_ledger_mfc["column"].isin(_target_cols_mfc)) &
    (~df_ledger_mfc["column"].isin(_identity_cols_mfc))
]
assert (_zero_mfc["mechanism"] == "N/A").all(), "non-target zero-missingness rows must have mechanism=N/A"
assert (_zero_mfc["recommendation"] == "RETAIN_AS_IS").all(), "non-target zero-missingness rows must be RETAIN_AS_IS"
print("ASSERT PASSED: zero-missingness non-target rows → mechanism=N/A, recommendation=RETAIN_AS_IS")

# True constants
_const_mfc = df_ledger_mfc[
    (df_ledger_mfc["n_distinct"].fillna(-1) == 1) &
    (df_ledger_mfc["n_null"] == 0) &
    (df_ledger_mfc["n_sentinel"] == 0)
]
assert (_const_mfc["mechanism"] == "N/A").all(), "true constant rows must have mechanism=N/A"
assert (_const_mfc["recommendation"] == "DROP_COLUMN").all(), "true constant rows must be DROP_COLUMN"
print(f"ASSERT PASSED: {len(_const_mfc)} true constant column(s) → mechanism=N/A, recommendation=DROP_COLUMN")

# Identity columns (B5 fix)
_ident_mfc = df_ledger_mfc[df_ledger_mfc["column"].isin(_identity_cols_mfc)]
assert (_ident_mfc["mechanism"] == "N/A").all(), "identity columns must have mechanism=N/A"
assert (_ident_mfc["recommendation"] == "RETAIN_AS_IS").all(), "identity columns must be RETAIN_AS_IS"
print("ASSERT PASSED: identity columns → mechanism=N/A, recommendation=RETAIN_AS_IS")

# Target typo guard (W7)
_missing_targets_mfc = set(_target_cols_mfc) - set(df_ledger_mfc["column"].values)
assert not _missing_targets_mfc, f"target column(s) named but missing from VIEW: {_missing_targets_mfc}"
print("ASSERT PASSED: target column(s) present in ledger")

# Target-column override (B4)
_targets_with_missing_mfc = df_ledger_mfc[
    (df_ledger_mfc["column"].isin(_target_cols_mfc)) &
    ((df_ledger_mfc["n_null"] > 0) | (df_ledger_mfc["n_sentinel"] > 0))
]
assert (_targets_with_missing_mfc["recommendation"] == "EXCLUDE_TARGET_NULL_ROWS").all(), (
    "Target columns with semantic missingness must be EXCLUDE_TARGET_NULL_ROWS (B4)"
)
print("ASSERT PASSED: target-column override (B4) consistent")

# 6.C sc2egset-specific: MMR sentinel > 0 in matches_flat_clean
_mmr_row_mfc = df_ledger_mfc[df_ledger_mfc["column"] == "MMR"]
if len(_mmr_row_mfc) > 0:
    assert _mmr_row_mfc.iloc[0]["n_sentinel"] > 0, "MMR sentinel count should be > 0 in matches_flat_clean"
    assert _mmr_row_mfc.iloc[0]["recommendation"] == "DROP_COLUMN", (
        f"MMR at >80% sentinel rate should be DROP_COLUMN; got {_mmr_row_mfc.iloc[0]['recommendation']}"
    )
    print(f"ASSERT PASSED: MMR n_sentinel={_mmr_row_mfc.iloc[0]['n_sentinel']}, recommendation=DROP_COLUMN")

# 6.C: gd_mapSizeX/Y n_sentinel=0 (VIEW converts 0 to NULL)
for _mc in ["gd_mapSizeX", "gd_mapSizeY"]:
    _mr = df_ledger_mfc[df_ledger_mfc["column"] == _mc]
    if len(_mr) > 0:
        assert _mr.iloc[0]["n_sentinel"] == 0, (
            f"{_mc} sentinel should be 0 (VIEW converts to NULL); got {_mr.iloc[0]['n_sentinel']}"
        )
        print(f"ASSERT PASSED: {_mc} n_sentinel=0 (VIEW converted to NULL)")

# 6.C: result in matches_flat_clean — F1 zero-missingness → RETAIN_AS_IS, mechanism=N/A
_result_row_mfc = df_ledger_mfc[df_ledger_mfc["column"] == "result"]
if len(_result_row_mfc) > 0:
    assert _result_row_mfc.iloc[0]["n_total_missing"] if "n_total_missing" in _result_row_mfc.columns else (
        _result_row_mfc.iloc[0]["n_null"] + _result_row_mfc.iloc[0]["n_sentinel"]
    ) == 0 or _result_row_mfc.iloc[0]["recommendation"] in {"RETAIN_AS_IS", "EXCLUDE_TARGET_NULL_ROWS"}, (
        "result in matches_flat_clean should be RETAIN_AS_IS (0 NULLs, F1 override) or EXCLUDE_TARGET_NULL_ROWS"
    )
    print(f"ASSERT PASSED: result recommendation={_result_row_mfc.iloc[0]['recommendation']} (matches_flat_clean)")

# 6.C: W7 verification — go_* constants
_go_constants_mfc = df_ledger_mfc[
    df_ledger_mfc["column"].str.startswith("go_") &
    (df_ledger_mfc["n_distinct"].fillna(-1) == 1)
]
if len(_go_constants_mfc) > 0:
    assert (_go_constants_mfc["recommendation"] == "DROP_COLUMN").all(), (
        f"go_* constants must all be DROP_COLUMN: {_go_constants_mfc[['column', 'recommendation']].to_dict()}"
    )
    print(f"ASSERT PASSED (W7): {len(_go_constants_mfc)} go_* column(s) detected as constants → DROP_COLUMN")
else:
    print("INFO (W7): no go_* columns detected as constants in matches_flat_clean")

print(f"\nmatches_flat_clean ledger complete: {len(df_ledger_mfc)} rows.")

# %% [markdown]
# ## Pass 2 — Sentinel census + constants detection + ledger: player_history_all

# %%
_view_hist = "player_history_all"
_target_cols_hist = {"result"}
_identity_cols_hist = {"replay_id", "toon_id"}

_describe_hist = con.execute(f"DESCRIBE {_view_hist}").df()
_dtype_map_hist = dict(zip(_describe_hist["column_name"], _describe_hist["column_type"]))
_cols_list_hist = _describe_hist["column_name"].tolist()
_total_hist_rows = con.execute(f"SELECT COUNT(*) FROM {_view_hist}").fetchone()[0]

# Sentinel census (Pass 2)
sentinel_rows_hist = _sentinel_census(_view_hist, _total_hist_rows, _missingness_spec)
print(f"Sentinel census for {_view_hist}: {len(sentinel_rows_hist)} spec columns processed.")

# Constants detection (Pass 3)
constants_map_hist = _detect_constants(_view_hist, _cols_list_hist, _identity_cols_hist)
n_const_hist = sum(1 for v in constants_map_hist.values() if v == 1)
print(f"Constants detection for {_view_hist}: {n_const_hist} column(s) with n_distinct=1.")

# Consolidate ledger
df_ledger_hist = _consolidate_ledger(
    _view_hist, df_null_hist, sentinel_rows_hist, _missingness_spec, _dtype_map_hist,
    _total_hist_rows, constants_map_hist, _target_cols_hist, _identity_cols_hist
)

print(f"\nLedger for {_view_hist}: {len(df_ledger_hist)} rows (one per column).")
print(df_ledger_hist[["column", "n_null", "n_sentinel", "pct_missing_total",
                        "mechanism", "recommendation"]].to_string(index=False))

# --- Assertion battery (6.B + 6.C) ---
_n_view_cols_hist = int(con.execute(f"DESCRIBE {_view_hist}").df().shape[0])
assert len(df_ledger_hist) == _n_view_cols_hist, (
    f"Full-coverage ledger required for {_view_hist}: expected {_n_view_cols_hist} rows, "
    f"got {len(df_ledger_hist)}"
)
print(f"ASSERT PASSED: ledger full coverage ({len(df_ledger_hist)} == {_n_view_cols_hist})")

for _, _row in df_ledger_hist.iterrows():
    assert _row["mechanism"] in {"MAR", "MCAR", "MNAR", "N/A"}, _row.to_dict()
    assert _row["mechanism_justification"], f"empty mechanism justification for {_row['column']}"
    assert _row["recommendation"] in {
        "DROP_COLUMN", "FLAG_FOR_IMPUTATION", "RETAIN_AS_IS",
        "EXCLUDE_TARGET_NULL_ROWS", "CONVERT_SENTINEL_TO_NULL"
    }, _row.to_dict()
    assert _row["recommendation_justification"], _row.to_dict()
    assert isinstance(_row["carries_semantic_content"], (bool, np.bool_)), _row.to_dict()
print("ASSERT PASSED: all ledger rows have valid mechanism + recommendation + justifications")

_zero_hist = df_ledger_hist[
    (df_ledger_hist["n_null"] == 0) &
    (df_ledger_hist["n_sentinel"] == 0) &
    (df_ledger_hist["n_distinct"].fillna(-1) != 1) &
    (~df_ledger_hist["column"].isin(_target_cols_hist)) &
    (~df_ledger_hist["column"].isin(_identity_cols_hist))
]
assert (_zero_hist["mechanism"] == "N/A").all(), "non-target zero-missingness rows must have mechanism=N/A"
assert (_zero_hist["recommendation"] == "RETAIN_AS_IS").all(), "non-target zero-missingness rows must be RETAIN_AS_IS"
print("ASSERT PASSED: zero-missingness non-target rows → mechanism=N/A, recommendation=RETAIN_AS_IS")

_const_hist = df_ledger_hist[
    (df_ledger_hist["n_distinct"].fillna(-1) == 1) &
    (df_ledger_hist["n_null"] == 0) &
    (df_ledger_hist["n_sentinel"] == 0)
]
assert (_const_hist["mechanism"] == "N/A").all(), "true constant rows must have mechanism=N/A"
assert (_const_hist["recommendation"] == "DROP_COLUMN").all(), "true constant rows must be DROP_COLUMN"
print(f"ASSERT PASSED: {len(_const_hist)} true constant column(s) → mechanism=N/A, recommendation=DROP_COLUMN")

_ident_hist = df_ledger_hist[df_ledger_hist["column"].isin(_identity_cols_hist)]
assert (_ident_hist["mechanism"] == "N/A").all(), "identity columns must have mechanism=N/A"
assert (_ident_hist["recommendation"] == "RETAIN_AS_IS").all(), "identity columns must be RETAIN_AS_IS"
print("ASSERT PASSED: identity columns → mechanism=N/A, recommendation=RETAIN_AS_IS")

_missing_targets_hist = set(_target_cols_hist) - set(df_ledger_hist["column"].values)
assert not _missing_targets_hist, f"target column(s) named but missing from VIEW: {_missing_targets_hist}"
print("ASSERT PASSED: target column(s) present in ledger")

_targets_with_missing_hist = df_ledger_hist[
    (df_ledger_hist["column"].isin(_target_cols_hist)) &
    ((df_ledger_hist["n_null"] > 0) | (df_ledger_hist["n_sentinel"] > 0))
]
assert (_targets_with_missing_hist["recommendation"] == "EXCLUDE_TARGET_NULL_ROWS").all(), (
    "Target columns with semantic missingness must be EXCLUDE_TARGET_NULL_ROWS (B4)"
)
print("ASSERT PASSED: target-column override (B4) consistent")

# 6.C sc2egset-specific for player_history_all:
# clanTag sentinel should have high pct
_clantag_row = df_ledger_hist[df_ledger_hist["column"] == "clanTag"]
if len(_clantag_row) > 0:
    print(f"INFO: clanTag n_sentinel={_clantag_row.iloc[0]['n_sentinel']}, "
          f"pct_sentinel={_clantag_row.iloc[0]['pct_sentinel']}%")

# MMR sentinel in player_history_all
_mmr_row_hist = df_ledger_hist[df_ledger_hist["column"] == "MMR"]
if len(_mmr_row_hist) > 0:
    assert _mmr_row_hist.iloc[0]["n_sentinel"] > 0, "MMR sentinel count should be > 0 in player_history_all"
    print(f"ASSERT PASSED: MMR n_sentinel={_mmr_row_hist.iloc[0]['n_sentinel']} in player_history_all")

# result in player_history_all: Undecided/Tie → EXCLUDE_TARGET_NULL_ROWS
_result_row_hist = df_ledger_hist[df_ledger_hist["column"] == "result"]
if len(_result_row_hist) > 0:
    _r_sentinel = _result_row_hist.iloc[0]["n_sentinel"]
    if _r_sentinel > 0:
        assert _result_row_hist.iloc[0]["recommendation"] == "EXCLUDE_TARGET_NULL_ROWS", (
            f"result in player_history_all with sentinels should be EXCLUDE_TARGET_NULL_ROWS; "
            f"got {_result_row_hist.iloc[0]['recommendation']}"
        )
        print(f"ASSERT PASSED: result n_sentinel={_r_sentinel} → EXCLUDE_TARGET_NULL_ROWS")
    else:
        print(f"INFO: result n_sentinel=0 in player_history_all (no Undecided/Tie rows found in sentinel census)")

# W7 for player_history_all
_go_constants_hist = df_ledger_hist[
    df_ledger_hist["column"].str.startswith("go_") &
    (df_ledger_hist["n_distinct"].fillna(-1) == 1)
]
if len(_go_constants_hist) > 0:
    assert (_go_constants_hist["recommendation"] == "DROP_COLUMN").all()
    print(f"ASSERT PASSED (W7): {len(_go_constants_hist)} go_* column(s) detected as constants in {_view_hist} → DROP_COLUMN")
else:
    print("INFO (W7): no go_* columns detected as constants in player_history_all")

print(f"\nplayer_history_all ledger complete: {len(df_ledger_hist)} rows.")

# %% [markdown]
# ## Decisions Surfaced for Downstream Cleaning (01_04_02+)
#
# DS-SC2-01 through DS-SC2-10 are open questions surfaced by this audit.
# They are NOT decisions — they are inputs for 01_04_02+ to resolve.

# %%
print("""
DS-SC2-01 — MMR (sentinel=0, ~83.66%):
  Q: Convert MMR=0 to NULL and drop from matches_flat_clean (Rule S4 / >80%),
     OR retain MMR=0 as explicit 'unranked' categorical encoding + is_mmr_missing,
     OR run analysis on rated subset only as sensitivity arm?
  Mechanism: MAR-primary (tournament replays); MNAR (private pro accounts) as sensitivity branch.

DS-SC2-02 — highestLeague (sentinel='Unknown', ~72.16%):
  Q: Drop entirely (Rule S4 / >50% non-primary), OR retain 'Unknown' as its own category?

DS-SC2-03 — clanTag (sentinel='', ~74%):
  Q: Drop (likely non-predictive at this rate), OR retain as derived is_in_clan boolean only?

DS-SC2-04 — result in player_history_all (Undecided/Tie sentinel):
  Q: How should NULL-target rows in player_history_all be handled when computing player
     history features (drop / mark as DRAW / retain with NaN target)?

DS-SC2-05 — selectedRace (sentinel='', ~2.48%):
  Already converted to 'Random' in VIEWs; audit confirms zero residual empty-string occurrences.

DS-SC2-06 — gd_mapSizeX / gd_mapSizeY (sentinel=0, ~1.22%):
  VIEWs already CASE-WHEN to NULL; audit confirms ledger reports converted NULLs, not original sentinel.

DS-SC2-07 — gd_mapAuthorName:
  Q: Drop on grounds of being a non-predictive metadata field even before missingness considered?

DS-SC2-08 — go_* constants surfaced by runtime constants-detection:
  Q: Confirm which exact go_* columns are constant in each VIEW and drop in 01_04_02+?

DS-SC2-09 — handicap (sentinel=0, ~0.0045% — 2 anomalous rows):
  Q: NULLIF the 2 anomalous rows + listwise deletion (Rule S3 / negligible rate),
     OR retain 0 as explicit is_anomalous_handicap flag?
  Note: carries_semantic_content=True; CONVERT_SENTINEL_TO_NULL recommendation is non-binding.

DS-SC2-10 — APM in player_history_all (sentinel=0, ~2.53%; 97.9% overlap with selectedRace=''):
  Q: Convert APM=0 to NULL via NULLIF in 01_04_02+ (per audit recommendation),
     OR retain APM=0 as categorical encoding for 'extremely short / unparseable game'?
  Note: carries_semantic_content=True; recommendation is non-binding.
""")

# %% [markdown]
# ## Produce artifacts (JSON)

# %%
reports_dir = get_reports_dir("sc2", "sc2egset")
artifact_dir = reports_dir / "artifacts" / "01_exploration" / "04_cleaning"
artifact_dir.mkdir(parents=True, exist_ok=True)

artifact = {
    "step": "01_04_01",
    "dataset": "sc2egset",
    "revision": 1,
    "revision_basis": "Replay-level MMR exclusion, regexp_extract NULLIF guard, constant column exclusions, and APM=0 as documentation-only.",
    "cleaning_registry": [
        {
            "rule_id": "non_1v1_indecisive_exclusion",
            "condition": "Replay is not true_1v1_decisive (player_count != 2 OR result not Win+Loss)",
            "action": "EXCLUDE from matches_flat_clean; RETAIN in player_history_all",
            "justification": "Binary classification target requires 2 players with 1 Win + 1 Loss. Non-1v1 and indecisive replays are valid game history. Source: 01_03_02.",
            "impact": f"{flow['r01_excluded_replays']} replays excluded from prediction scope, retained in history"
        },
        {
            "rule_id": "unrated_player_flag",
            "condition": "MMR = 0",
            "action": "FLAG (is_mmr_missing = TRUE)",
            "justification": "MNAR -- professional players on private accounts. 83.66%. Source: 01_03_01.",
            "impact": "37,422 rows in true_1v1_decisive scope"
        },
        {
            "rule_id": "anomalous_mmr_exclusion",
            "condition": "ANY player in replay has MMR < 0 (replay-level exclusion)",
            "action": "EXCLUDE entire replay from matches_flat_clean; RETAIN in player_history_all (MMR<0 treated as unreliable)",
            "justification": "Impossible in SC2 matchmaking. Replay-level exclusion prevents orphaned rows. Source: 01_03_01.",
            "impact": f"{flow['r03_excluded_replays']} replays excluded from prediction scope"
        },
        {
            "rule_id": "random_race_normalisation",
            "condition": "selectedRace = '' (empty string)",
            "action": "NORMALISE to 'Random' in both VIEWs",
            "justification": "Empty string = Random race selection resolved post-game. Source: 01_03_02.",
            "impact": "1,110 rows (2.48%)"
        },
        {
            "rule_id": "sq_sentinel_correction",
            "condition": "SQ = -2147483648 (INT32_MIN)",
            "action": "SQ -> NULL. SQ excluded from matches_flat_clean per temporal discipline; correction applies in player_history_all.",
            "justification": "Parse-failure sentinel. Source: 01_03_01.",
            "impact": "2 rows (0.0045%)"
        },
        {
            "rule_id": "map_size_missing_flag",
            "condition": "gd_mapSizeX = 0 AND gd_mapSizeY = 0",
            "action": "FLAG (mapSize -> NULL; is_map_size_missing = TRUE in both VIEWs)",
            "justification": "Parse artifact; 0 is not a valid SC2 map dimension. Source: 01_02_04, 01_03_01.",
            "impact": f"{r_map[0]} replays (~{r_map[1]} rows)"
        },
        {
            "rule_id": "handicap_anomaly_flag",
            "condition": "handicap = 0",
            "action": "FLAG (is_handicap_anomalous = TRUE)",
            "justification": "Standard handicap = 100. Source: 01_02_04.",
            "impact": "2 rows (0.0045%)"
        }
    ],
    "consort_flow": {
        "raw_player_rows": flow["raw_player_rows"],
        "raw_replays": flow["raw_replays"],
        "matches_flat_rows": flow["matches_flat_rows"],
        "matches_flat_replays": flow["matches_flat_replays"],
        "after_r01_replays": flow["after_r01_replays"],
        "r01_excluded_replays": flow["r01_excluded_replays"],
        "r01_excluded_rows": flow["r01_excluded_rows"],
        "r03_excluded_replays": flow["r03_excluded_replays"],
        "r03_excluded_rows": flow["r03_excluded_rows"],
        "clean_rows": flow["clean_rows"],
        "clean_replays": flow["clean_replays"],
        "history_rows": flow["history_rows"],
        "history_replays": flow["history_replays"]
    },
    "validation": {
        "matches_flat_rows": flow["matches_flat_rows"],
        "matches_flat_replays": flow["matches_flat_replays"],
        "null_replay_id": 0,
        "isBlizzardMap_mismatch": 0,
        "details_gameSpeed_cardinality": 1,
        "gd_gameSpeed_cardinality": 1,
        "clean_rows": flow["clean_rows"],
        "clean_replays": flow["clean_replays"],
        "non_win_loss_results_clean": 0,
        "mmr_negative_clean": 0,
        "empty_selected_race_clean": 0,
        "null_replay_id_clean": 0,
        "symmetry_violations": 0,
        "history_rows": flow["history_rows"],
        "history_replays": flow["history_replays"],
        "sq_sentinel_history": 0,
        "empty_selected_race_history": 0,
        "apm_present_history": 44817,
        "i3_column_exclusion_passed": True,
        "consort_arithmetic_verified": True
    },
    "views_created": ["matches_flat", "matches_flat_clean", "player_history_all"],
    "design_constraint": {
        "prediction_scope": "matches_flat_clean -- 1v1 decisive results only, PRE-GAME features, MMR<0 replays excluded",
        "feature_history_scope": "player_history_all -- all replays, all game types, including in-game metrics (APM, SQ)",
        "rationale": "Player features computed from full game history; prediction targets restricted to 1v1 decisive. I3 applies at target match level only."
    },
    "i3_compliance": {
        "matches_flat_clean_excluded": [
            "APM", "SQ", "supplyCappedPercent", "header_elapsedGameLoops",
            "details_gameSpeed", "gd_gameSpeed", "gd_isBlizzardMap",
            "color_a", "color_b", "color_g", "color_r"
        ],
        "player_history_all_includes_ingame": [
            "APM", "SQ", "supplyCappedPercent", "header_elapsedGameLoops"
        ],
        "rationale": "I3 prohibits in-game metrics for TARGET match T. For prior matches in player_history_all, they are valid historical signals."
    },
    "design_changes": {
        "replay_level_mmr_exclusion": "MMR exclusion changed from row-level WHERE to replay-level CTE (mmr_valid). 157 replays excluded.",
        "constant_column_exclusions": "details_gameSpeed and gd_gameSpeed excluded from both matches_flat_clean and player_history_all (constant across all replays)",
        "duplicate_column_exclusion": "gd_isBlizzardMap excluded from downstream VIEWs; verified identical to details_isBlizzardMap (mismatch=0)",
        "regexp_extract_null_guard": "NULLIF wrapper applied in matches_flat VIEW definition; null_replay_id=0 confirmed",
        "apm_documentation_only": "No APM-derived columns in any VIEW; APM=0 investigation is documentation-only"
    },
    "sql_queries": {
        "CREATE_MATCHES_FLAT": CREATE_MATCHES_FLAT_SQL,
        "CREATE_MATCHES_FLAT_CLEAN": CREATE_MATCHES_FLAT_CLEAN_SQL,
        "CREATE_PLAYER_HISTORY_ALL": CREATE_PLAYER_HISTORY_SQL,
        "CLASSIFICATION_SUMMARY": CLASSIFICATION_SUMMARY_SQL,
        "MMR_COUNTS": MMR_COUNTS_SQL,
        "MMR_NEG_REPLAYS": MMR_NEG_REPLAYS_SQL,
        "MMR_NEG_DISTRIBUTION": MMR_NEG_SQL,
        "MMR_OVERLAP": MMR_OVERLAP_SQL,
        "MMR_STRATIFICATION": MMR_STRAT_SQL,
        "SELECTED_RACE_CROSSREF": SELECTED_RACE_SQL,
        "SELECTED_RACE_APM": SELECTED_RACE_APM_SQL,
        "SQ_SENTINEL": SQ_SENTINEL_SQL,
        "APM_DURATION": APM_DURATION_SQL,
        "APM_RACE_OVERLAP": APM_RACE_SQL,
        "MAP_ZERO_PROFILE": MAP_ZERO_SQL,
        "MAP_ZERO_OVERLAP": MAP_ZERO_OVERLAP_SQL,
        "HANDICAP_ZERO": HANDICAP_SQL,
        "RESULT_DISTRIBUTION": RESULT_DIST_SQL,
        "RACE_DISTRIBUTION": RACE_DIST_SQL,
        "SELECTED_RACE_DISTRIBUTION": SR_DIST_SQL,
        "MMR_STATS": MMR_STATS_SQL,
        "NULL_CHECK": NULL_CHECK_SQL,
        "SYMMETRY_CHECK": SYMMETRY_SQL,
        "SCOPE_COMPARISON": SCOPE_SQL
    }
}

# NULL audit integration (T02/T03 results)
artifact["null_audit"] = {
    "matches_flat_clean": {
        "total_rows": int(df_null_matches["total_count"].iloc[0]) if len(df_null_matches) > 0 else 0,
        "columns_audited": len(df_null_matches),
        "columns_with_nulls": int((df_null_matches["null_count"] > 0).sum()),
        "columns_fully_populated": int((df_null_matches["null_count"] == 0).sum()),
        "per_column": df_null_matches[
            ["column_name", "null_count", "total_count", "null_pct"]
        ].to_dict(orient="records"),
        "zero_null_assertions_passed": {
            "replay_id": True,
            "toon_id": True,
            "result": True,
        },
    },
    "player_history_all": {
        "total_rows": int(df_null_hist["total_count"].iloc[0]) if len(df_null_hist) > 0 else 0,
        "columns_audited": len(df_null_hist),
        "columns_with_nulls": int((df_null_hist["null_count"] > 0).sum()),
        "columns_fully_populated": int((df_null_hist["null_count"] == 0).sum()),
        "per_column": df_null_hist[
            ["column_name", "null_count", "total_count", "null_pct"]
        ].to_dict(orient="records"),
        "zero_null_assertions_passed": {
            "replay_id": True,
            "toon_id": True,
            "result": True,
        },
        "expected_null_findings": {
            "SQ": f"R05 sentinel correction (INT32_MIN -> NULL). Found {sq_nulls} NULLs.",
        },
    },
}
artifact["sql_queries"]["null_audit_method"] = (
    "Per-column NULL census via: "
    "COUNT(*) FILTER (WHERE \"<col>\" IS NULL) for each column from DESCRIBE <view>"
)

# --- Missingness audit block (additive — Deliverable 5.D) ---
_ds_surfaced = [
    {"id": "DS-SC2-01", "column": "MMR (sentinel=0, ~83.66%)",
     "observed_pct_missing_total": float(df_ledger_mfc[df_ledger_mfc["column"] == "MMR"]["pct_missing_total"].iloc[0]) if len(df_ledger_mfc[df_ledger_mfc["column"] == "MMR"]) > 0 else None,
     "question": "Convert MMR=0 to NULL and drop the column from matches_flat_clean (per Rule S4 / >80%), OR retain MMR=0 as an explicit 'unranked' categorical encoding alongside is_mmr_missing, OR run the analysis on the rated subset only as a sensitivity arm?"},
    {"id": "DS-SC2-02", "column": "highestLeague (sentinel='Unknown', ~72.16%)",
     "observed_pct_missing_total": float(df_ledger_mfc[df_ledger_mfc["column"] == "highestLeague"]["pct_missing_total"].iloc[0]) if len(df_ledger_mfc[df_ledger_mfc["column"] == "highestLeague"]) > 0 else None,
     "question": "Drop the column entirely (Rule S4 / >50% non-primary), OR retain 'Unknown' as its own category (Phase 02 decides if predictive)?"},
    {"id": "DS-SC2-03", "column": "clanTag (sentinel='', ~74%)",
     "observed_pct_missing_total": None,
     "question": "Drop the column (likely non-predictive at this rate), OR retain as a derived is_in_clan boolean only?"},
    {"id": "DS-SC2-04", "column": "result in player_history_all (Undecided/Tie sentinel)",
     "observed_pct_missing_total": float(df_ledger_hist[df_ledger_hist["column"] == "result"]["pct_missing_total"].iloc[0]) if len(df_ledger_hist[df_ledger_hist["column"] == "result"]) > 0 else None,
     "question": "How should NULL-target rows in player_history_all be handled when computing player history features (e.g., expanding-window win-rate)? Drop these rows, mark as DRAW, or retain with NaN target?"},
    {"id": "DS-SC2-05", "column": "selectedRace (sentinel='', ~2.48%)",
     "observed_pct_missing_total": 0.0,
     "question": "Already converted to 'Random' in VIEWs (PR predecessor); audit confirms zero residual empty-string occurrences in the cleaned VIEWs."},
    {"id": "DS-SC2-06", "column": "gd_mapSizeX / gd_mapSizeY (sentinel=0, ~1.22%)",
     "observed_pct_missing_total": None,
     "question": "VIEWs already CASE-WHEN to NULL (PR predecessor); audit confirms ledger reports the converted NULLs, not the original sentinel."},
    {"id": "DS-SC2-07", "column": "gd_mapAuthorName",
     "observed_pct_missing_total": float(df_ledger_mfc[df_ledger_mfc["column"] == "gd_mapAuthorName"]["pct_missing_total"].iloc[0]) if len(df_ledger_mfc[df_ledger_mfc["column"] == "gd_mapAuthorName"]) > 0 else None,
     "question": "Drop column on grounds of being a non-predictive metadata field even before missingness considered? Decision deferred to 01_04_02+."},
    {"id": "DS-SC2-08", "column": "go_* constants surfaced by runtime constants-detection",
     "observed_pct_missing_total": None,
     "question": "Confirm the runtime constants-detection branch reports n_distinct=1 for the go_* columns flagged in 01_03_03. Drop these per Rule S4 / N/A-mechanism in 01_04_02+?"},
    {"id": "DS-SC2-09", "column": "handicap (sentinel=0, ~0.0045% — 2 anomalous rows)",
     "observed_pct_missing_total": float(df_ledger_mfc[df_ledger_mfc["column"] == "handicap"]["pct_missing_total"].iloc[0]) if len(df_ledger_mfc[df_ledger_mfc["column"] == "handicap"]) > 0 else None,
     "question": "NULLIF the 2 anomalous handicap=0 rows + listwise deletion per Rule S3 (negligible rate), OR retain 0 as an explicit is_anomalous_handicap flag? NOTE: carries_semantic_content=True; CONVERT_SENTINEL_TO_NULL recommendation is non-binding."},
    {"id": "DS-SC2-10", "column": "APM in player_history_all (sentinel=0, ~2.53%; 97.9% overlap with selectedRace='')",
     "observed_pct_missing_total": float(df_ledger_hist[df_ledger_hist["column"] == "APM"]["pct_missing_total"].iloc[0]) if len(df_ledger_hist[df_ledger_hist["column"] == "APM"]) > 0 else None,
     "question": "Convert APM=0 to NULL via NULLIF in 01_04_02+ (per audit recommendation) OR retain APM=0 as a categorical encoding for 'extremely short / unparseable game'? NOTE: carries_semantic_content=True; recommendation is non-binding."},
]

artifact["missingness_audit"] = {
    "framework": {
        "source_doc": "temp/null_handling_recommendations.md",
        "rules_applied": ["S1", "S2", "S3", "S4", "S5", "S6"],
        "mechanism_taxonomy": "Rubin (1976); Little & Rubin (2019, 3rd ed.)",
        "phase_boundary": "Phase 01 documents (I9). Phase 02 transforms.",
        "thresholds": {
            "low_rate_pct": 5.0,
            "mid_rate_pct": 40.0,
            "high_rate_pct": 80.0,
            "threshold_source": (
                "Operational starting heuristics from temp/null_handling_recommendations.md §1.2; "
                "<5% MCAR boundary citation: Schafer & Graham 2002; "
                "warning against rigid global thresholds: van Buuren 2018"
            ),
        },
        "override_priority": [
            "1. Constants detection (n_distinct == 1) → mechanism=N/A, recommendation=DROP_COLUMN",
            "2. F1 zero-missingness (n_total_missing == 0) → mechanism=N/A, recommendation=RETAIN_AS_IS",
            "3. _recommend() per spec/fallback (incl. CONVERT_SENTINEL_TO_NULL for sentinel-only low-rate cases)",
            "4. Target-column post-step (col in target_cols AND n_total_missing > 0) → recommendation=EXCLUDE_TARGET_NULL_ROWS",
        ],
        "per_view_target_cols": {
            "matches_flat_clean": list(_target_cols_mfc),
            "player_history_all": list(_target_cols_hist),
        },
    },
    "missingness_spec": _missingness_spec,
    "views": {
        "matches_flat_clean": {
            "total_rows": _total_mfc_rows,
            "columns_audited": len(df_ledger_mfc),
            "ledger": df_ledger_mfc.to_dict(orient="records"),
        },
        "player_history_all": {
            "total_rows": _total_hist_rows,
            "columns_audited": len(df_ledger_hist),
            "ledger": df_ledger_hist.to_dict(orient="records"),
        },
    },
    "decisions_surfaced": _ds_surfaced,
}

# Assertions on artifact before write (6.B)
assert len(artifact["missingness_audit"]["decisions_surfaced"]) >= 1
assert all("question" in d and d["question"] for d in artifact["missingness_audit"]["decisions_surfaced"])
print("ASSERT PASSED: missingness_audit decisions_surfaced non-empty and complete")

json_path = artifact_dir / "01_04_01_data_cleaning.json"
with open(json_path, "w") as f:
    json.dump(artifact, f, indent=2, default=str)
print(f"JSON artifact written: {json_path}")

# %% [markdown]
# ## Write Missingness Ledger CSV + JSON (Deliverable 5.B / 5.C)

# %%
# Concatenate both VIEW ledgers
df_ledger_all = pd.concat([df_ledger_mfc, df_ledger_hist], ignore_index=True)
print(f"Combined ledger: {len(df_ledger_all)} rows ({len(df_ledger_mfc)} mfc + {len(df_ledger_hist)} hist)")

# Assertions: CSV column set exactly matches Deliverable 5.B (17 columns)
_expected_cols = {
    "view", "column", "dtype",
    "n_total", "n_null", "pct_null",
    "sentinel_value", "n_sentinel", "pct_sentinel",
    "pct_missing_total",
    "n_distinct",
    "mechanism", "mechanism_justification",
    "recommendation", "recommendation_justification",
    "carries_semantic_content",
    "is_primary_feature",
}
_actual_cols = set(df_ledger_all.columns)
assert _actual_cols == _expected_cols, (
    f"Ledger CSV column mismatch.\nExpected: {sorted(_expected_cols)}\nActual: {sorted(_actual_cols)}"
)
print(f"ASSERT PASSED: ledger has exactly 17 columns matching Deliverable 5.B")

# Write CSV
ledger_csv_path = artifact_dir / "01_04_01_missingness_ledger.csv"
df_ledger_all.to_csv(ledger_csv_path, index=False)
print(f"Ledger CSV written: {ledger_csv_path}")

# Write JSON (Deliverable 5.C schema)
ledger_json_path = artifact_dir / "01_04_01_missingness_ledger.json"
ledger_json = {
    "step": "01_04_01",
    "dataset": "sc2egset",
    "generated_date": "2026-04-17",
    "framework": artifact["missingness_audit"]["framework"],
    "missingness_spec": _missingness_spec,
    "ledger": df_ledger_all.to_dict(orient="records"),
    "decisions_surfaced": _ds_surfaced,
}
with open(ledger_json_path, "w") as f:
    json.dump(ledger_json, f, indent=2, default=str)
print(f"Ledger JSON written: {ledger_json_path}")

# File existence assertions (6.B)
assert ledger_csv_path.exists(), f"Ledger CSV not found: {ledger_csv_path}"
assert ledger_json_path.exists(), f"Ledger JSON not found: {ledger_json_path}"
print("ASSERT PASSED: both ledger files exist")

# %% [markdown]
# ## Write MD artifact

# %%
md_content = f"""# Step 01_04_01 -- Data Cleaning

**Dataset:** sc2egset
**Date:** 2026-04-16
**Revision:** 1 (incorporates replay-level MMR exclusion, regexp_extract NULLIF guard, constant column exclusions, and APM=0 as documentation-only)
**Invariants:** I3, I6, I7, I9

---

## Summary

Applied non-destructive cleaning to two ESSENTIAL raw tables (replay_players_raw,
replays_meta_raw) and created three DuckDB VIEWs:

1. **`matches_flat`** -- structural JOIN, all rows, no filters
2. **`matches_flat_clean`** -- prediction target VIEW: 1v1 decisive, PRE-GAME only
3. **`player_history_all`** -- player feature history: all replays, IN_GAME metrics retained

## Design Constraint: Prediction Scope != Feature Scope

Prediction targets (matches_flat_clean) are restricted to 1v1 decisive replays
with pre-game features only (I3). Player history features (Phase 02) use
player_history_all which includes all replays including non-1v1 and in-game
metrics for PRIOR matches. I3 prohibits in-game metrics only at TARGET match T.

## CONSORT Flow (REPLAY units)

| Stage | Replays | Rows |
|-------|---------|------|
| Raw (replays_meta_raw) | {flow['raw_replays']:,} | -- |
| Raw (replay_players_raw) | -- | {flow['raw_player_rows']:,} |
| matches_flat (JOIN) | {flow['matches_flat_replays']:,} | {flow['matches_flat_rows']:,} |
| After 1v1 decisive filter | {flow['after_r01_replays']:,} | {flow['after_r01_rows']:,} |
| Excluded (non-1v1 + indecisive) | -{flow['r01_excluded_replays']:,} | -{flow['r01_excluded_rows']:,} |
| After MMR<0 replay-level exclusion | {flow['clean_replays']:,} | {flow['clean_rows']:,} |
| Excluded (any MMR<0 player) | -{flow['r03_excluded_replays']:,} | -{flow['r03_excluded_rows']:,} |
| **matches_flat_clean (final)** | **{flow['clean_replays']:,}** | **{flow['clean_rows']:,}** |
| player_history_all (all replays) | {flow['history_replays']:,} | {flow['history_rows']:,} |

MMR<0 exclusion is replay-level: if any player in a replay has MMR<0, the entire
replay is excluded from prediction scope. Row-level filtering would orphan the
opponent's row, breaking the 2-per-replay invariant.

## Cleaning Registry

| Rule | Condition | Action | Impact |
|------|-----------|--------|--------|
| Exclusion: non-1v1 or indecisive | Not true_1v1_decisive | EXCLUDE from clean; RETAIN in history | {flow['r01_excluded_replays']} replays |
| Flag: unrated player | MMR = 0 | FLAG (is_mmr_missing=TRUE) | 37,422 rows (83.66%) |
| Exclusion: anomalous MMR | ANY player MMR<0 (replay-level) | EXCLUDE replay from clean; RETAIN in history | {flow['r03_excluded_replays']} replays |
| Normalise: random race | selectedRace = '' | NORMALISE to 'Random' | 1,110 rows (2.48%) |
| Correct: SQ sentinel | SQ = INT32_MIN | SQ -> NULL | 2 rows (0.0045%) |
| Flag: map size missing | mapSizeX=0 AND mapSizeY=0 | FLAG + NULL | 273 replays |
| Flag: handicap anomalous | handicap = 0 | FLAG (is_handicap_anomalous=TRUE) | 2 rows (0.0045%) |

Note: APM=0 is NOT a cleaning rule. APM=0 investigation is documentation-only.
APM is excluded from matches_flat_clean (temporal discipline) and retained in
player_history_all as a valid historical observation.

## Columns Excluded from matches_flat_clean

- APM, SQ, supplyCappedPercent, header_elapsedGameLoops (in-game metrics — temporal discipline)
- details_gameSpeed, gd_gameSpeed (constant across all replays, cardinality=1)
- gd_isBlizzardMap (duplicate of details_isBlizzardMap — zero mismatches confirmed)
- color_a, color_b, color_g, color_r (cosmetic)

## Columns Retained in player_history_all (in-game historical signals)

- APM -- actions per minute (in-game metric, valid for prior match history)
- SQ -- spending quotient (parse-failure sentinel INT32_MIN corrected to NULL)
- supplyCappedPercent -- % game time supply-blocked
- header_elapsedGameLoops -- game duration

## Validation Results

- matches_flat: {flow['matches_flat_rows']:,} rows, {flow['matches_flat_replays']:,} replays, 0 NULL replay_ids
- isBlizzardMap mismatch: 0 (gd_isBlizzardMap identical to details_isBlizzardMap)
- gameSpeed cardinality: 1 (both details_gameSpeed and gd_gameSpeed)
- matches_flat_clean: {flow['clean_rows']:,} rows, {flow['clean_replays']:,} replays
- Result distribution: 50.0% Win / 50.0% Loss (perfect symmetry)
- Symmetry violations: 0 (every replay has exactly 1 Win + 1 Loss row)
- Column exclusion assertion (temporal discipline + constant/duplicate cols): PASSED
- player_history_all: {flow['history_rows']:,} rows, {flow['history_replays']:,} replays
- SQ sentinel in player_history_all: 0
- CONSORT arithmetic verified

## Changes from Initial Design

- Replay-level MMR exclusion via CTE (mmr_valid) -- {flow['r03_excluded_replays']} replays excluded
- details_gameSpeed, gd_gameSpeed excluded (verified constant across all replays)
- gd_isBlizzardMap excluded (verified identical to details_isBlizzardMap, mismatch=0)
- NULLIF wrapper applied to regexp_extract in matches_flat JOIN (null_replay_id=0 confirmed)
- No APM-derived columns added to any VIEW

## NULL Audit

### matches_flat_clean

| Metric | Value |
|--------|-------|
| Total rows | {int(df_null_matches['total_count'].iloc[0]):,} |
| Columns audited | {len(df_null_matches)} |
| Columns with NULLs | {int((df_null_matches['null_count'] > 0).sum())} |
| Columns fully populated | {int((df_null_matches['null_count'] == 0).sum())} |

Zero-NULL assertions passed: replay_id, toon_id, result.

### player_history_all

| Metric | Value |
|--------|-------|
| Total rows | {int(df_null_hist['total_count'].iloc[0]):,} |
| Columns audited | {len(df_null_hist)} |
| Columns with NULLs | {int((df_null_hist['null_count'] > 0).sum())} |
| Columns fully populated | {int((df_null_hist['null_count'] == 0).sum())} |

Zero-NULL assertions passed: replay_id, toon_id, result.
Expected NULLs: SQ (R05 sentinel correction — {sq_nulls} rows).

## Missingness Ledger

Full-coverage ledger (Option B): one row per column per VIEW. Zero-missingness columns
tagged mechanism=N/A / recommendation=RETAIN_AS_IS. Constant columns tagged mechanism=N/A /
recommendation=DROP_COLUMN. Target columns with missingness tagged EXCLUDE_TARGET_NULL_ROWS.

Framework: Rubin (1976) / Little & Rubin (2019) MCAR/MAR/MNAR taxonomy.
Thresholds (5/40/80%) are operational starting heuristics — van Buuren (2018) warns
against rigid global thresholds.

### Missingness Ledger — matches_flat_clean

{df_ledger_mfc[['column', 'dtype', 'n_null', 'n_sentinel', 'pct_missing_total', 'mechanism', 'recommendation']].to_markdown(index=False)}

**Columns: {len(df_ledger_mfc)} | With missingness: {int((df_ledger_mfc['pct_missing_total'] > 0).sum())} | Constants (DROP_COLUMN): {int((df_ledger_mfc['recommendation'] == 'DROP_COLUMN').sum())}**

### Missingness Ledger — player_history_all

{df_ledger_hist[['column', 'dtype', 'n_null', 'n_sentinel', 'pct_missing_total', 'mechanism', 'recommendation']].to_markdown(index=False)}

**Columns: {len(df_ledger_hist)} | With missingness: {int((df_ledger_hist['pct_missing_total'] > 0).sum())} | Constants (DROP_COLUMN): {int((df_ledger_hist['recommendation'] == 'DROP_COLUMN').sum())}**

## Decisions Surfaced for Downstream Cleaning (01_04_02+)

The following open questions are surfaced by this audit for 01_04_02+ to resolve.
The audit RECOMMENDS but does NOT decide or execute. All rates below are from the VIEWs
(filtered scope); raw-table rates differ.

| ID | Column | Observed pct_missing_total | Question |
|----|--------|---------------------------|----------|
| DS-SC2-01 | MMR (sentinel=0) | ~83.66% | Convert MMR=0 to NULL + drop (Rule S4 >80%), OR retain as 'unranked' encoding + is_mmr_missing, OR rated-subset sensitivity arm? |
| DS-SC2-02 | highestLeague (sentinel='Unknown') | ~72.16% | Drop entirely, OR retain 'Unknown' as its own category? |
| DS-SC2-03 | clanTag (sentinel='') | ~74% | Drop (non-predictive at this rate), OR retain as is_in_clan boolean? |
| DS-SC2-04 | result in player_history_all (Undecided/Tie) | runtime | How to handle NULL-target rows in player_history_all for win-rate feature computation? |
| DS-SC2-05 | selectedRace (sentinel='') | 0% in VIEWs | Already normalised to 'Random' in VIEWs; audit confirms zero residual. |
| DS-SC2-06 | gd_mapSizeX / gd_mapSizeY (sentinel=0) | n_sentinel=0 in VIEWs | VIEWs CASE-WHEN to NULL; audit confirms ledger reports converted NULLs. |
| DS-SC2-07 | gd_mapAuthorName | runtime | Drop as non-predictive metadata? |
| DS-SC2-08 | go_* constants | runtime | Confirm which go_* are constant in each VIEW; drop in 01_04_02+? |
| DS-SC2-09 | handicap (sentinel=0, 2 rows) | ~0.0045% | NULLIF + listwise deletion (Rule S3), OR retain is_anomalous_handicap flag? (carries_semantic_content=True) |
| DS-SC2-10 | APM (sentinel=0, ~2.53%) | ~2.53% in hist | Convert to NULL via NULLIF, OR retain as encoding for 'unparseable game'? (carries_semantic_content=True) |

Ledger artifacts: `artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv` (CSV)
and `artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.json` (JSON).
"""

md_path = artifact_dir / "01_04_01_data_cleaning.md"
with open(md_path, "w") as f:
    f.write(md_content)
print(f"MD artifact written: {md_path}")

# %% [markdown]
# ## Write schema YAML for player_history_all

# %%
describe_df = con.execute("DESCRIBE player_history_all").df()

schema_yaml_lines = [
    "table: player_history_all",
    "dataset: sc2egset",
    "game: sc2",
    "object_type: view",
    'step: "01_04_01"',
    f"row_count: {flow['history_rows']}",
    "describe_artifact: src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json",
    "generated_date: '2026-04-16'",
    "columns:",
]

# Column annotations
col_notes = {
    "replay_id": ("VARCHAR", "Canonical join key extracted via regexp. NULLIF empty-string guard applied.", "IDENTITY"),
    "filename": ("VARCHAR", "Replay file path relative to raw_dir. Invariant I10.", "IDENTITY"),
    "toon_id": ("VARCHAR", "Battle.net toon/account identifier. Player identity key.", "IDENTITY"),
    "nickname": ("VARCHAR", "Player nickname.", "IDENTITY"),
    "playerID": ("INTEGER", "In-game player id.", "IDENTITY"),
    "userID": ("BIGINT", "User id.", "IDENTITY"),
    "result": ("VARCHAR", "Game result (Win, Loss, Undecided, Tie). Unfiltered in history.", "TARGET"),
    "MMR": ("INTEGER", "Matchmaking rating. 0=unrated sentinel (83.66% MNAR).", "PRE_GAME"),
    "is_mmr_missing": ("BOOLEAN", "TRUE if MMR=0 (unrated professional). MNAR.", "PRE_GAME"),
    "race": ("VARCHAR", "Actual race played (Protoss, Zerg, Terran abbreviated).", "PRE_GAME"),
    "selectedRace": ("VARCHAR", "Selected race. Empty string normalised to 'Random'.", "PRE_GAME"),
    "handicap": ("INTEGER", "Handicap percentage (100=standard). 2 anomalous rows have 0.", "PRE_GAME"),
    "region": ("VARCHAR", "Battle.net region label.", "PRE_GAME"),
    "realm": ("VARCHAR", "Realm label.", "PRE_GAME"),
    "highestLeague": ("VARCHAR", "Highest known league. Mostly Unknown in esports replays.", "PRE_GAME"),
    "isInClan": ("BOOLEAN", "Whether the player is in a clan.", "PRE_GAME"),
    "clanTag": ("VARCHAR", "Clan tag.", "PRE_GAME"),
    "APM": ("INTEGER", "Actions per minute (in-game metric). IN_GAME_HISTORICAL: valid for prior matches only. Excluded from matches_flat_clean (I3).", "IN_GAME_HISTORICAL"),
    "SQ": ("INTEGER", "Spending Quotient. Parse-failure sentinel INT32_MIN corrected to NULL. IN_GAME_HISTORICAL.", "IN_GAME_HISTORICAL"),
    "supplyCappedPercent": ("INTEGER", "% game time supply-capped. IN_GAME_HISTORICAL.", "IN_GAME_HISTORICAL"),
    "header_elapsedGameLoops": ("BIGINT", "Game duration in loops. IN_GAME_HISTORICAL (post-game observable).", "IN_GAME_HISTORICAL"),
    "startDir": ("INTEGER", "Starting direction code (lobby assignment).", "PRE_GAME"),
    "startLocX": ("INTEGER", "Starting x location on map.", "PRE_GAME"),
    "startLocY": ("INTEGER", "Starting y location on map.", "PRE_GAME"),
    "metadata_mapName": ("VARCHAR", "Human-readable map name.", "PRE_GAME"),
    "gd_mapSizeX": ("BIGINT", "Map width (0 corrected to NULL; parse artifact).", "PRE_GAME"),
    "gd_mapSizeY": ("BIGINT", "Map height (0 corrected to NULL; parse artifact).", "PRE_GAME"),
    "gd_maxPlayers": ("BIGINT", "Max players in game description.", "PRE_GAME"),
    "details_isBlizzardMap": ("BOOLEAN", "Blizzard-authored map flag (from details struct). Preferred over gd_isBlizzardMap (confirmed identical, duplicate dropped).", "PRE_GAME"),
    "gd_mapAuthorName": ("VARCHAR", "Map author name.", "PRE_GAME"),
    "gd_mapFileSyncChecksum": ("BIGINT", "Map file sync checksum.", "PRE_GAME"),
    "details_timeUTC": ("VARCHAR", "UTC timestamp of game. Temporal anchor for I3 ordering.", "CONTEXT"),
    "header_version": ("VARCHAR", "SC2 version string.", "CONTEXT"),
    "metadata_baseBuild": ("VARCHAR", "Base build string.", "CONTEXT"),
    "metadata_dataBuild": ("VARCHAR", "Data build string.", "CONTEXT"),
    "metadata_gameVersion": ("VARCHAR", "Game version.", "CONTEXT"),
    "go_advancedSharedControl": ("BOOLEAN", "Game option: advanced shared control.", "CONTEXT"),
    "go_amm": ("BOOLEAN", "Game option: automated match making.", "CONTEXT"),
    "go_battleNet": ("BOOLEAN", "Game option: Battle.net game.", "CONTEXT"),
    "go_clientDebugFlags": ("BIGINT", "Game option: client debug flags.", "CONTEXT"),
    "go_competitive": ("BOOLEAN", "Game option: competitive mode.", "CONTEXT"),
    "go_cooperative": ("BOOLEAN", "Game option: cooperative mode.", "CONTEXT"),
    "go_fog": ("BIGINT", "Game option: fog of war setting.", "CONTEXT"),
    "go_heroDuplicatesAllowed": ("BOOLEAN", "Game option: hero duplicates allowed.", "CONTEXT"),
    "go_lockTeams": ("BOOLEAN", "Game option: teams locked.", "CONTEXT"),
    "go_noVictoryOrDefeat": ("BOOLEAN", "Game option: no victory or defeat.", "CONTEXT"),
    "go_observers": ("BIGINT", "Game option: observers allowed.", "CONTEXT"),
    "go_practice": ("BOOLEAN", "Game option: practice mode.", "CONTEXT"),
    "go_randomRaces": ("BOOLEAN", "Game option: random races.", "CONTEXT"),
    "go_teamsTogether": ("BOOLEAN", "Game option: teams together.", "CONTEXT"),
    "go_userDifficulty": ("BIGINT", "Game option: user difficulty.", "CONTEXT"),
    # max_players_check removed: alias dropped in PR #138
}

for _, row in describe_df.iterrows():
    col = row["column_name"]
    ctype = row["column_type"]
    nullable = row["null"] == "YES"
    desc, notes = col_notes.get(col, ("", "PRE_GAME"))[1], col_notes.get(col, ("", "PRE_GAME"))[2]
    schema_yaml_lines.append(f"- name: {col}")
    schema_yaml_lines.append(f"  type: {ctype}")
    schema_yaml_lines.append(f"  nullable: {nullable}")
    schema_yaml_lines.append(f"  description: {desc}")
    schema_yaml_lines.append(f"  notes: {notes}")

schema_yaml_lines += [
    "provenance:",
    "  source_tables: [replay_players_raw, replays_meta_raw]",
    "  join_key: \"NULLIF(regexp_extract(filename, '([0-9a-f]{32})\\\\.SC2Replay\\\\.json', 1), '') AS replay_id\"",
    "  filter: \"replay_id IS NOT NULL (empty-string guard); MMR<0 retained with flag; SQ=INT32_MIN -> NULL (parse-failure sentinel correction)\"",
    "  scope: \"All replays (no 1v1/decisive filter). Includes non-1v1 and indecisive replays excluded from matches_flat_clean.\"",
    "  created_by: sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_01_data_cleaning.py",
    "invariants:",
    "  - id: I3",
    '    description: "APM, SQ, supplyCappedPercent, header_elapsedGameLoops are IN_GAME',
    '      and excluded from matches_flat_clean. They are RETAINED here as valid',
    '      historical signals for prior matches only (I3 applies to target match T,',
    '      not to historical records)."',
    "  - id: I6",
    '    description: "VIEW DDL stored verbatim in 01_04_01_data_cleaning.json sql_queries."',
    "  - id: I9",
    '    description: "No features computed. VIEW is a JOIN projection of replay_players_raw',
    '      x replays_meta_raw with minimal quality corrections."',
]

schema_yaml_content = "\n".join(schema_yaml_lines) + "\n"

schema_dir = reports_dir.parent / "data" / "db" / "schemas" / "views"
schema_dir.mkdir(parents=True, exist_ok=True)
schema_path = schema_dir / "player_history_all.yaml"
with open(schema_path, "w") as f:
    f.write(schema_yaml_content)
print(f"Schema YAML written: {schema_path}")

# %% [markdown]
# ## Close connection

# %%
db.close()
print("DuckDB connection closed.")
print("\nAll cleaning tasks complete.")
print(f"  matches_flat: {flow['matches_flat_rows']:,} rows / {flow['matches_flat_replays']:,} replays")
print(f"  matches_flat_clean: {flow['clean_rows']:,} rows / {flow['clean_replays']:,} replays")
print(f"  player_history_all: {flow['history_rows']:,} rows / {flow['history_replays']:,} replays")
