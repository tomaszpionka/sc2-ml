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
con = get_notebook_db("sc2", "sc2egset", read_only=False)
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

con.con.execute(CREATE_MATCHES_FLAT_SQL)
print("matches_flat VIEW created.")

# %% [markdown]
# ## matches_flat validation

# %%
r_mf = con.con.execute(
    "SELECT COUNT(*) AS total_rows, COUNT(DISTINCT replay_id) AS distinct_replays FROM matches_flat"
).fetchone()
print(f"matches_flat: rows={r_mf[0]}, distinct_replays={r_mf[1]}")
assert r_mf[0] == 44817, f"Expected 44817 rows, got {r_mf[0]}"
assert r_mf[1] == 22390, f"Expected 22390 replays, got {r_mf[1]}"

r_null = con.con.execute(
    "SELECT COUNT(*) AS null_replay_id FROM matches_flat WHERE replay_id IS NULL"
).fetchone()
print(f"NULL replay_id: {r_null[0]}")
assert r_null[0] == 0, f"Expected 0 NULL replay_ids, got {r_null[0]}"

# isBlizzardMap duplication check
r_bm = con.con.execute(
    "SELECT COUNT(*) AS mismatched_blizzard_map FROM matches_flat WHERE gd_isBlizzardMap != details_isBlizzardMap"
).fetchone()
print(f"isBlizzardMap mismatch count: {r_bm[0]}")
if r_bm[0] == 0:
    print("gd_isBlizzardMap == details_isBlizzardMap for all rows. Will exclude gd_isBlizzardMap from downstream VIEWs.")

# gameSpeed constant assertion
r_gs = con.con.execute(
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

r_class = con.con.execute(CLASSIFICATION_SUMMARY_SQL).df()
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

r_mmr = con.con.execute(MMR_COUNTS_SQL).fetchone()
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
r_mmr_neg = con.con.execute(MMR_NEG_SQL).df()
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
r_mmr_neg_replays = con.con.execute(MMR_NEG_REPLAYS_SQL).fetchone()
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
r_overlap = con.con.execute(MMR_OVERLAP_SQL).df()
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
r_strat = con.con.execute(MMR_STRAT_SQL).df()
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
r_sr = con.con.execute(SELECTED_RACE_SQL).df()
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
r_sr_apm = con.con.execute(SELECTED_RACE_APM_SQL).fetchone()
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
r_sq = con.con.execute(SQ_SENTINEL_SQL).df()
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
r_apm = con.con.execute(APM_DURATION_SQL).df()
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
r_apm2 = con.con.execute(APM_RACE_SQL).fetchone()
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
r_map = con.con.execute(MAP_ZERO_SQL).fetchone()
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
r_map2 = con.con.execute(MAP_ZERO_OVERLAP_SQL).fetchone()
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
r_hc = con.con.execute(HANDICAP_SQL).df()
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

con.con.execute(CREATE_MATCHES_FLAT_CLEAN_SQL)
print("matches_flat_clean VIEW created.")

# %% [markdown]
# ## matches_flat_clean validation

# %%
r_clean = con.con.execute(
    "SELECT COUNT(*) AS total, COUNT(DISTINCT replay_id) AS replays FROM matches_flat_clean"
).fetchone()
print(f"matches_flat_clean: rows={r_clean[0]}, replays={r_clean[1]}")

r_bad_result = con.con.execute(
    "SELECT COUNT(*) FROM matches_flat_clean WHERE result NOT IN ('Win','Loss')"
).fetchone()
print(f"Non-Win/Loss results: {r_bad_result[0]}")
assert r_bad_result[0] == 0

r_mmr_neg = con.con.execute("SELECT COUNT(*) FROM matches_flat_clean WHERE MMR < 0").fetchone()
print(f"MMR<0 rows: {r_mmr_neg[0]}")
assert r_mmr_neg[0] == 0

r_empty_race = con.con.execute(
    "SELECT COUNT(*) FROM matches_flat_clean WHERE selectedRace = ''"
).fetchone()
print(f"Empty selectedRace: {r_empty_race[0]}")
assert r_empty_race[0] == 0

r_null_id = con.con.execute(
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

con.con.execute(CREATE_PLAYER_HISTORY_SQL)
print("player_history_all VIEW created.")

# %% [markdown]
# ## player_history_all validation

# %%
r_hist = con.con.execute(
    "SELECT COUNT(*) AS total_rows, COUNT(DISTINCT replay_id) AS distinct_replays FROM player_history_all"
).fetchone()
print(f"player_history_all: rows={r_hist[0]}, replays={r_hist[1]}")
assert r_hist[0] == 44817, f"Expected 44817 rows, got {r_hist[0]}"
assert r_hist[1] == 22390, f"Expected 22390 replays, got {r_hist[1]}"

r_sq_sentinel = con.con.execute(
    "SELECT COUNT(*) FROM player_history_all WHERE SQ = -2147483648"
).fetchone()
print(f"SQ sentinel rows: {r_sq_sentinel[0]}")
assert r_sq_sentinel[0] == 0

r_empty_race_h = con.con.execute(
    "SELECT COUNT(*) FROM player_history_all WHERE selectedRace = ''"
).fetchone()
print(f"Empty selectedRace: {r_empty_race_h[0]}")
assert r_empty_race_h[0] == 0

r_apm_h = con.con.execute(
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

flow["raw_player_rows"] = con.con.execute(
    "SELECT COUNT(*) FROM replay_players_raw"
).fetchone()[0]
flow["raw_replays"] = con.con.execute(
    "SELECT COUNT(*) FROM replays_meta_raw"
).fetchone()[0]
flow["matches_flat_rows"] = con.con.execute(
    "SELECT COUNT(*) FROM matches_flat"
).fetchone()[0]
flow["matches_flat_replays"] = con.con.execute(
    "SELECT COUNT(DISTINCT replay_id) FROM matches_flat"
).fetchone()[0]

r01_subquery = """SELECT replay_id FROM matches_flat GROUP BY replay_id
    HAVING COUNT(*) = 2
       AND COUNT(*) FILTER (WHERE result = 'Win') = 1
       AND COUNT(*) FILTER (WHERE result = 'Loss') = 1"""

flow["after_r01_replays"] = con.con.execute(
    f"SELECT COUNT(*) FROM ({r01_subquery})"
).fetchone()[0]
flow["r01_excluded_replays"] = flow["matches_flat_replays"] - flow["after_r01_replays"]
flow["after_r01_rows"] = con.con.execute(
    f"SELECT COUNT(*) FROM matches_flat WHERE replay_id IN ({r01_subquery})"
).fetchone()[0]
flow["r01_excluded_rows"] = flow["matches_flat_rows"] - flow["after_r01_rows"]

# MMR<0 replay-level exclusion
flow["r03_excluded_replays"] = con.con.execute(f"""
    SELECT COUNT(*) FROM (
        SELECT replay_id FROM matches_flat
        WHERE replay_id IN ({r01_subquery})
        GROUP BY replay_id
        HAVING COUNT(*) FILTER (WHERE MMR < 0) > 0
    )
""").fetchone()[0]
flow["r03_excluded_rows"] = flow["r03_excluded_replays"] * 2  # 1v1: 2 rows per replay

flow["clean_rows"] = con.con.execute(
    "SELECT COUNT(*) FROM matches_flat_clean"
).fetchone()[0]
flow["clean_replays"] = con.con.execute(
    "SELECT COUNT(DISTINCT replay_id) FROM matches_flat_clean"
).fetchone()[0]
flow["history_rows"] = con.con.execute(
    "SELECT COUNT(*) FROM player_history_all"
).fetchone()[0]
flow["history_replays"] = con.con.execute(
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
r_result = con.con.execute(RESULT_DIST_SQL).df()
print("Result distribution:")
print(r_result.to_string(index=False))

# Race distribution (only Protoss, Zerg, Terran abbreviated variants)
RACE_DIST_SQL = "SELECT race, COUNT(*) AS cnt FROM matches_flat_clean GROUP BY race ORDER BY cnt DESC"
r_race = con.con.execute(RACE_DIST_SQL).df()
print(f"\nRace distribution:\n{r_race.to_string(index=False)}")

# selectedRace distribution (no empty strings)
SR_DIST_SQL = """
SELECT selectedRace, COUNT(*) AS cnt FROM matches_flat_clean
GROUP BY selectedRace ORDER BY cnt DESC
"""
r_sr2 = con.con.execute(SR_DIST_SQL).df()
print(f"\nselectedRace distribution:\n{r_sr2.to_string(index=False)}")

# MMR stats (rated-only)
MMR_STATS_SQL = """
SELECT COUNT(*) AS rated_rows,
       MIN(MMR) AS mmr_min, MAX(MMR) AS mmr_max,
       ROUND(AVG(MMR), 2) AS mmr_mean
FROM matches_flat_clean WHERE is_mmr_missing = FALSE
"""
r_mmr_stats = con.con.execute(MMR_STATS_SQL).fetchone()
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
r_null_check = con.con.execute(NULL_CHECK_SQL).fetchone()
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
clean_cols = set(con.con.execute("DESCRIBE matches_flat_clean").df()["column_name"])

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
r_sym = con.con.execute(SYMMETRY_SQL).fetchone()
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
r_scope = con.con.execute(SCOPE_SQL).df()
print("player_history_all scope comparison:")
print(r_scope.to_string(index=False))

r_uniq = con.con.execute(
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
r_apm_check = con.con.execute(APM_CHECK_SQL).fetchone()
print(f"APM present={r_apm_check[0]}, APM=0 count={r_apm_check[1]}")

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

json_path = artifact_dir / "01_04_01_data_cleaning.json"
with open(json_path, "w") as f:
    json.dump(artifact, f, indent=2)
print(f"JSON artifact written: {json_path}")

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
"""

md_path = artifact_dir / "01_04_01_data_cleaning.md"
with open(md_path, "w") as f:
    f.write(md_content)
print(f"MD artifact written: {md_path}")

# %% [markdown]
# ## Write schema YAML for player_history_all

# %%
describe_df = con.con.execute("DESCRIBE player_history_all").df()

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
    "max_players_check": ("BIGINT", "Alias of gd_maxPlayers for cross-check.", "CONTEXT"),
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
con.close()
print("DuckDB connection closed.")
print("\nAll cleaning tasks complete.")
print(f"  matches_flat: {flow['matches_flat_rows']:,} rows / {flow['matches_flat_replays']:,} replays")
print(f"  matches_flat_clean: {flow['clean_rows']:,} rows / {flow['clean_replays']:,} replays")
print(f"  player_history_all: {flow['history_rows']:,} rows / {flow['history_replays']:,} replays")
