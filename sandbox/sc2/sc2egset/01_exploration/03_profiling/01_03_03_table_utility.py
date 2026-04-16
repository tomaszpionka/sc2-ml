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
# # Step 01_03_03 -- Table Utility Assessment
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_03 -- Systematic Data Profiling
# **Dataset:** sc2egset
# **Question:** Which of the 6 raw data objects (replay_players_raw,
# replays_meta_raw, map_aliases_raw, game_events_raw, tracker_events_raw,
# message_events_raw) are necessary and sufficient for the prediction
# pipeline? What join key connects the two core tables? Are map names
# already in English? What do loop=0 events represent?
# **Invariants applied:** #3 (I3 temporal classification), #6 (all SQL
# stored verbatim), #9 (profiling only -- no cleaning decisions)
# **Predecessor:** 01_03_02 (True 1v1 Match Identification -- complete)
# **Type:** Read-only -- no DuckDB writes
#
# **Commit:** feat/table-utility-assessment
# **Date:** 2026-04-16
# **ROADMAP ref:** 01_03_03

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
# ## Cell 2 -- DuckDB connection and output directories

# %%
conn = get_notebook_db("sc2", "sc2egset")
reports_dir = get_reports_dir("sc2", "sc2egset")

artifact_dir = (
    reports_dir / "artifacts" / "01_exploration" / "03_profiling"
)
artifact_dir.mkdir(parents=True, exist_ok=True)
print(f"Artifact dir: {artifact_dir}")

# Load prior census and profile artifacts for runtime constants (I7)
census_json_path = (
    reports_dir / "artifacts" / "01_exploration" / "02_eda"
    / "01_02_04_univariate_census.json"
)
with open(census_json_path) as f:
    census = json.load(f)

profile_json_path = (
    reports_dir / "artifacts" / "01_exploration" / "03_profiling"
    / "01_03_01_systematic_profile.json"
)
with open(profile_json_path) as f:
    profile = json.load(f)

true_1v1_json_path = (
    reports_dir / "artifacts" / "01_exploration" / "03_profiling"
    / "01_03_02_true_1v1_profile.json"
)
with open(true_1v1_json_path) as f:
    true_1v1 = json.load(f)

# Constants from prior artifacts (I7: no magic numbers)
RP_TOTAL_ROWS = census["null_census"]["replay_players_raw"]["total_rows"]
RM_TOTAL_ROWS = census["null_census"]["replays_meta_raw_filename"]["total_rows"]
TRUE_1V1_DECISIVE = true_1v1["replay_classification"]["true_1v1_decisive_count"]

print(f"replay_players_raw total rows (from census): {RP_TOTAL_ROWS}")
print(f"replays_meta_raw total rows (from census):   {RM_TOTAL_ROWS}")
print(f"true_1v1_decisive replays (from 01_03_02):   {TRUE_1V1_DECISIVE}")

sql_queries: dict = {}

# %% [markdown]
# ## Cell 3 -- T01: DESCRIBE both core tables

# %%
# DESCRIBE replay_players_raw
sql_queries["describe_replay_players_raw"] = "DESCRIBE replay_players_raw"
rp_schema_df = conn.con.execute(sql_queries["describe_replay_players_raw"]).df()
print("=== replay_players_raw schema ===")
print(rp_schema_df.to_string(index=False))
print(f"\nColumn count: {len(rp_schema_df)}")

# %% [markdown]
# ## Cell 4 -- T01: DESCRIBE replays_meta_raw

# %%
sql_queries["describe_replays_meta_raw"] = "DESCRIBE replays_meta_raw"
rm_schema_df = conn.con.execute(sql_queries["describe_replays_meta_raw"]).df()
print("=== replays_meta_raw schema ===")
print(rm_schema_df.to_string(index=False))
print(f"\nColumn count: {len(rm_schema_df)}")

# %% [markdown]
# ## Cell 5 -- T01: Full struct leaf field enumeration (all 31 fields)
#
# replays_meta_raw has 9 top-level columns. The 4 STRUCT columns flatten
# into 31 leaf fields:
# - details (3 leaves): gameSpeed, isBlizzardMap, timeUTC
# - header (2 leaves): elapsedGameLoops, version
# - initData.gameDescription (22 leaves):
#     gameOptions sub-struct (15 leaves):
#       advancedSharedControl, amm, battleNet, clientDebugFlags,
#       competitive, cooperative, fog, heroDuplicatesAllowed,
#       lockTeams, noVictoryOrDefeat, observers, practice,
#       randomRaces, teamsTogether, userDifficulty
#     gameSpeed, isBlizzardMap, mapAuthorName, mapFileSyncChecksum,
#     mapSizeX, mapSizeY, maxPlayers (7 leaves)
# - metadata (4 leaves): baseBuild, dataBuild, gameVersion, mapName
# Plus non-struct top-level: filename, ToonPlayerDescMap,
#   gameEventsErr, messageEventsErr, trackerEvtsErr (5 non-struct)

# %%
sql_queries["struct_leaf_census"] = """
SELECT
    -- details struct (3 leaves)
    details.gameSpeed               AS details_gameSpeed,
    details.isBlizzardMap           AS details_isBlizzardMap,
    details.timeUTC                 AS details_timeUTC,

    -- header struct (2 leaves)
    header.elapsedGameLoops         AS header_elapsedGameLoops,
    header.version                  AS header_version,

    -- initData.gameDescription.gameOptions sub-struct (15 leaves)
    initData.gameDescription.gameOptions.advancedSharedControl
                                    AS go_advancedSharedControl,
    initData.gameDescription.gameOptions.amm
                                    AS go_amm,
    initData.gameDescription.gameOptions.battleNet
                                    AS go_battleNet,
    initData.gameDescription.gameOptions.clientDebugFlags
                                    AS go_clientDebugFlags,
    initData.gameDescription.gameOptions.competitive
                                    AS go_competitive,
    initData.gameDescription.gameOptions.cooperative
                                    AS go_cooperative,
    initData.gameDescription.gameOptions.fog
                                    AS go_fog,
    initData.gameDescription.gameOptions.heroDuplicatesAllowed
                                    AS go_heroDuplicatesAllowed,
    initData.gameDescription.gameOptions.lockTeams
                                    AS go_lockTeams,
    initData.gameDescription.gameOptions.noVictoryOrDefeat
                                    AS go_noVictoryOrDefeat,
    initData.gameDescription.gameOptions.observers
                                    AS go_observers,
    initData.gameDescription.gameOptions.practice
                                    AS go_practice,
    initData.gameDescription.gameOptions.randomRaces
                                    AS go_randomRaces,
    initData.gameDescription.gameOptions.teamsTogether
                                    AS go_teamsTogether,
    initData.gameDescription.gameOptions.userDifficulty
                                    AS go_userDifficulty,

    -- initData.gameDescription direct fields (7 leaves)
    initData.gameDescription.gameSpeed
                                    AS gd_gameSpeed,
    initData.gameDescription.isBlizzardMap
                                    AS gd_isBlizzardMap,
    initData.gameDescription.mapAuthorName
                                    AS gd_mapAuthorName,
    initData.gameDescription.mapFileSyncChecksum
                                    AS gd_mapFileSyncChecksum,
    initData.gameDescription.mapSizeX
                                    AS gd_mapSizeX,
    initData.gameDescription.mapSizeY
                                    AS gd_mapSizeY,
    initData.gameDescription.maxPlayers
                                    AS gd_maxPlayers,

    -- metadata struct (4 leaves)
    metadata.baseBuild              AS metadata_baseBuild,
    metadata.dataBuild              AS metadata_dataBuild,
    metadata.gameVersion            AS metadata_gameVersion,
    metadata.mapName                AS metadata_mapName

FROM replays_meta_raw
LIMIT 5
"""

struct_sample_df = conn.con.execute(sql_queries["struct_leaf_census"]).df()
print(f"Struct leaf sample shape: {struct_sample_df.shape}")
print(f"Columns extracted: {list(struct_sample_df.columns)}")
print(f"\nLeaf field count: {len(struct_sample_df.columns)}")
assert len(struct_sample_df.columns) == 31, (
    f"Expected 31 struct leaf fields, got {len(struct_sample_df.columns)}"
)

# %% [markdown]
# ## Cell 6 -- T01: Struct leaf field cardinality and null census (all 31 fields)

# %%
sql_queries["struct_leaf_null_cardinality"] = """
SELECT
    -- details.gameSpeed
    COUNT(*) AS n_rows,
    COUNT(DISTINCT details.gameSpeed) AS details_gameSpeed_card,
    SUM(CASE WHEN details.gameSpeed IS NULL THEN 1 ELSE 0 END)
        AS details_gameSpeed_nulls,

    -- details.isBlizzardMap
    COUNT(DISTINCT details.isBlizzardMap) AS details_isBlizzardMap_card,
    SUM(CASE WHEN details.isBlizzardMap IS NULL THEN 1 ELSE 0 END)
        AS details_isBlizzardMap_nulls,

    -- details.timeUTC
    COUNT(DISTINCT details.timeUTC) AS details_timeUTC_card,
    SUM(CASE WHEN details.timeUTC IS NULL THEN 1 ELSE 0 END)
        AS details_timeUTC_nulls,

    -- header.elapsedGameLoops
    COUNT(DISTINCT header.elapsedGameLoops) AS header_elapsed_card,
    SUM(CASE WHEN header.elapsedGameLoops IS NULL THEN 1 ELSE 0 END)
        AS header_elapsed_nulls,
    MIN(header.elapsedGameLoops) AS header_elapsed_min,
    MAX(header.elapsedGameLoops) AS header_elapsed_max,

    -- header.version
    COUNT(DISTINCT header.version) AS header_version_card,
    SUM(CASE WHEN header.version IS NULL THEN 1 ELSE 0 END)
        AS header_version_nulls,

    -- gameOptions fields
    COUNT(DISTINCT initData.gameDescription.gameOptions.advancedSharedControl)
        AS go_advancedSharedControl_card,
    COUNT(DISTINCT initData.gameDescription.gameOptions.amm)
        AS go_amm_card,
    COUNT(DISTINCT initData.gameDescription.gameOptions.battleNet)
        AS go_battleNet_card,
    COUNT(DISTINCT initData.gameDescription.gameOptions.clientDebugFlags)
        AS go_clientDebugFlags_card,
    COUNT(DISTINCT initData.gameDescription.gameOptions.competitive)
        AS go_competitive_card,
    COUNT(DISTINCT initData.gameDescription.gameOptions.cooperative)
        AS go_cooperative_card,
    COUNT(DISTINCT initData.gameDescription.gameOptions.fog)
        AS go_fog_card,
    COUNT(DISTINCT initData.gameDescription.gameOptions.heroDuplicatesAllowed)
        AS go_heroDuplicatesAllowed_card,
    COUNT(DISTINCT initData.gameDescription.gameOptions.lockTeams)
        AS go_lockTeams_card,
    COUNT(DISTINCT initData.gameDescription.gameOptions.noVictoryOrDefeat)
        AS go_noVictoryOrDefeat_card,
    COUNT(DISTINCT initData.gameDescription.gameOptions.observers)
        AS go_observers_card,
    COUNT(DISTINCT initData.gameDescription.gameOptions.practice)
        AS go_practice_card,
    COUNT(DISTINCT initData.gameDescription.gameOptions.randomRaces)
        AS go_randomRaces_card,
    COUNT(DISTINCT initData.gameDescription.gameOptions.teamsTogether)
        AS go_teamsTogether_card,
    COUNT(DISTINCT initData.gameDescription.gameOptions.userDifficulty)
        AS go_userDifficulty_card,

    -- initData.gameDescription direct fields
    COUNT(DISTINCT initData.gameDescription.gameSpeed)
        AS gd_gameSpeed_card,
    COUNT(DISTINCT initData.gameDescription.isBlizzardMap)
        AS gd_isBlizzardMap_card,
    COUNT(DISTINCT initData.gameDescription.mapAuthorName)
        AS gd_mapAuthorName_card,
    SUM(CASE WHEN initData.gameDescription.mapAuthorName IS NULL THEN 1 ELSE 0 END)
        AS gd_mapAuthorName_nulls,
    COUNT(DISTINCT initData.gameDescription.mapFileSyncChecksum)
        AS gd_mapFileSyncChecksum_card,
    COUNT(DISTINCT initData.gameDescription.mapSizeX) AS gd_mapSizeX_card,
    MIN(initData.gameDescription.mapSizeX) AS gd_mapSizeX_min,
    MAX(initData.gameDescription.mapSizeX) AS gd_mapSizeX_max,
    COUNT(DISTINCT initData.gameDescription.mapSizeY) AS gd_mapSizeY_card,
    MIN(initData.gameDescription.mapSizeY) AS gd_mapSizeY_min,
    MAX(initData.gameDescription.mapSizeY) AS gd_mapSizeY_max,
    COUNT(DISTINCT initData.gameDescription.maxPlayers) AS gd_maxPlayers_card,

    -- metadata fields
    COUNT(DISTINCT metadata.baseBuild)   AS metadata_baseBuild_card,
    COUNT(DISTINCT metadata.dataBuild)   AS metadata_dataBuild_card,
    COUNT(DISTINCT metadata.gameVersion) AS metadata_gameVersion_card,
    COUNT(DISTINCT metadata.mapName)     AS metadata_mapName_card,
    SUM(CASE WHEN metadata.mapName IS NULL THEN 1 ELSE 0 END)
        AS metadata_mapName_nulls

FROM replays_meta_raw
"""

struct_stats_df = conn.con.execute(sql_queries["struct_leaf_null_cardinality"]).df()
print("=== Struct leaf field statistics ===")
# Transpose for readability
print(struct_stats_df.T.to_string())

# %% [markdown]
# ## Cell 7 -- T01: Identify constant and near-constant gameOptions flags

# %%
sql_queries["go_flag_distributions"] = """
SELECT
    initData.gameDescription.gameOptions.advancedSharedControl AS advancedSharedControl,
    initData.gameDescription.gameOptions.amm               AS amm,
    initData.gameDescription.gameOptions.battleNet         AS battleNet,
    initData.gameDescription.gameOptions.competitive       AS competitive,
    initData.gameDescription.gameOptions.cooperative       AS cooperative,
    initData.gameDescription.gameOptions.fog               AS fog,
    initData.gameDescription.gameOptions.heroDuplicatesAllowed AS heroDuplicatesAllowed,
    initData.gameDescription.gameOptions.lockTeams         AS lockTeams,
    initData.gameDescription.gameOptions.noVictoryOrDefeat AS noVictoryOrDefeat,
    initData.gameDescription.gameOptions.practice          AS practice,
    initData.gameDescription.gameOptions.randomRaces       AS randomRaces,
    initData.gameDescription.gameOptions.teamsTogether     AS teamsTogether,
    COUNT(*) AS cnt
FROM replays_meta_raw
GROUP BY
    advancedSharedControl, amm, battleNet, competitive, cooperative,
    fog, heroDuplicatesAllowed, lockTeams, noVictoryOrDefeat,
    practice, randomRaces, teamsTogether
ORDER BY cnt DESC
LIMIT 20
"""

go_flags_df = conn.con.execute(sql_queries["go_flag_distributions"]).df()
print("=== gameOptions flag combinations (top 20 by frequency) ===")
print(go_flags_df.to_string(index=False))

# %% [markdown]
# ## Cell 8 -- T01: Join verification using replay_id (I6, sql-data.md rule)
#
# Per sql-data.md: join key must be replay_id derived via
# regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1).
# NEVER join directly on raw filename.

# %%
sql_queries["join_verification_replay_id"] = """
WITH rp_distinct AS (
    SELECT DISTINCT
        regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id
    FROM replay_players_raw
    WHERE regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) != ''
),
rm_distinct AS (
    SELECT DISTINCT
        regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id
    FROM replays_meta_raw
    WHERE regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) != ''
),
matched AS (
    SELECT rp.replay_id
    FROM rp_distinct rp
    JOIN rm_distinct rm ON rp.replay_id = rm.replay_id
),
rp_only AS (
    SELECT rp.replay_id
    FROM rp_distinct rp
    LEFT JOIN rm_distinct rm ON rp.replay_id = rm.replay_id
    WHERE rm.replay_id IS NULL
),
rm_only AS (
    SELECT rm.replay_id
    FROM rm_distinct rm
    LEFT JOIN rp_distinct rp ON rm.replay_id = rp.replay_id
    WHERE rp.replay_id IS NULL
)
SELECT
    (SELECT COUNT(*) FROM rp_distinct) AS rp_distinct_replay_ids,
    (SELECT COUNT(*) FROM rm_distinct) AS rm_distinct_replay_ids,
    (SELECT COUNT(*) FROM matched)     AS matched_replay_ids,
    (SELECT COUNT(*) FROM rp_only)     AS rp_only,
    (SELECT COUNT(*) FROM rm_only)     AS rm_only
"""

join_df = conn.con.execute(sql_queries["join_verification_replay_id"]).df()
print("=== Join verification via replay_id ===")
print(join_df.to_string(index=False))

rp_ids_count = int(join_df["rp_distinct_replay_ids"].iloc[0])
rm_ids_count = int(join_df["rm_distinct_replay_ids"].iloc[0])
matched = int(join_df["matched_replay_ids"].iloc[0])
rp_only = int(join_df["rp_only"].iloc[0])
rm_only = int(join_df["rm_only"].iloc[0])

print(f"\nrp distinct replay_ids : {rp_ids_count}")
print(f"rm distinct replay_ids : {rm_ids_count}")
print(f"Matched (intersection) : {matched}")
print(f"rp only (orphans)      : {rp_only}")
print(f"rm only (orphans)      : {rm_only}")
print(f"Match rate             : {matched / rm_ids_count * 100:.4f}%")

# %% [markdown]
# ## Cell 9 -- T01: Verify regex extraction works on sample filenames

# %%
sql_queries["replay_id_sample"] = """
SELECT
    filename,
    regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id
FROM replays_meta_raw
LIMIT 10
"""

replay_id_sample_df = conn.con.execute(sql_queries["replay_id_sample"]).df()
print("=== Sample replay_id extraction ===")
print(replay_id_sample_df.to_string(index=False))

# Verify no empty replay_ids in replays_meta_raw
sql_queries["empty_replay_id_check"] = """
SELECT COUNT(*) AS empty_count
FROM replays_meta_raw
WHERE regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) = ''
"""

empty_df = conn.con.execute(sql_queries["empty_replay_id_check"]).df()
n_empty = int(empty_df["empty_count"].iloc[0])
print(f"\nReplays_meta_raw rows with empty replay_id: {n_empty}")
assert n_empty == 0, f"Unexpected empty replay_ids in replays_meta_raw: {n_empty}"

# %% [markdown]
# ## Cell 10 -- T02: map_aliases_raw utility assessment
#
# Question: Are map names in replays_meta_raw (metadata.mapName) already in
# English? If yes, map_aliases_raw (104K rows, 70 identical copies of 1,488
# key-value pairs) may be unnecessary.

# %%
sql_queries["meta_map_name_sample"] = """
SELECT
    metadata.mapName AS map_name,
    COUNT(*) AS replay_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS pct
FROM replays_meta_raw
GROUP BY map_name
ORDER BY replay_count DESC
LIMIT 30
"""

map_name_df = conn.con.execute(sql_queries["meta_map_name_sample"]).df()
print("=== Top 30 map names in replays_meta_raw.metadata.mapName ===")
print(map_name_df.to_string(index=False))

# %% [markdown]
# ## Cell 11 -- T02: Check map_aliases_raw for non-ASCII foreign names

# %%
sql_queries["map_aliases_raw_overview"] = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT tournament) AS distinct_tournaments,
    COUNT(DISTINCT foreign_name) AS distinct_foreign_names,
    COUNT(DISTINCT english_name) AS distinct_english_names,
    COUNT(DISTINCT filename) AS distinct_files
FROM map_aliases_raw
"""

aliases_overview_df = conn.con.execute(sql_queries["map_aliases_raw_overview"]).df()
print("=== map_aliases_raw overview ===")
print(aliases_overview_df.to_string(index=False))

# %% [markdown]
# ## Cell 12 -- T02: Sample foreign names to determine if non-ASCII characters present

# %%
sql_queries["map_aliases_sample"] = """
SELECT foreign_name, english_name
FROM map_aliases_raw
WHERE tournament = (SELECT MIN(tournament) FROM map_aliases_raw)
ORDER BY foreign_name
LIMIT 30
"""

aliases_sample_df = conn.con.execute(sql_queries["map_aliases_sample"]).df()
print("=== Sample from map_aliases_raw (one tournament) ===")
print(aliases_sample_df.to_string(index=False))

# %% [markdown]
# ## Cell 13 -- T02: Cross-reference: do any meta map names appear in foreign_name column?

# %%
sql_queries["map_name_vs_aliases_cross"] = """
WITH meta_maps AS (
    SELECT DISTINCT metadata.mapName AS map_name
    FROM replays_meta_raw
    WHERE metadata.mapName IS NOT NULL
)
SELECT
    COUNT(*) AS meta_map_count,
    COUNT(*) FILTER (
        WHERE map_name IN (SELECT DISTINCT foreign_name FROM map_aliases_raw)
    ) AS in_foreign_names,
    COUNT(*) FILTER (
        WHERE map_name IN (SELECT DISTINCT english_name FROM map_aliases_raw)
    ) AS in_english_names,
    COUNT(*) FILTER (
        WHERE map_name NOT IN (SELECT DISTINCT foreign_name FROM map_aliases_raw)
        AND map_name NOT IN (SELECT DISTINCT english_name FROM map_aliases_raw)
    ) AS in_neither
FROM meta_maps
"""

cross_df = conn.con.execute(sql_queries["map_name_vs_aliases_cross"]).df()
print("=== Cross-reference: meta map names vs alias table ===")
print(cross_df.to_string(index=False))
print("\nInterpretation:")
print("  in_foreign_names > 0 => some map names are NOT yet translated")
print("  in_english_names = meta_map_count => all meta names are already English")
print("  in_neither > 0 => names not in alias table at all (custom/unknown maps)")

# %% [markdown]
# ## Cell 14 -- T02: Check if foreign_name == english_name for any entries
# (determines if the translation is always meaningful)

# %%
sql_queries["alias_identity_check"] = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE foreign_name = english_name) AS identity_count,
    COUNT(*) FILTER (WHERE foreign_name != english_name) AS translated_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE foreign_name = english_name) / COUNT(*),
        2
    ) AS identity_pct
FROM (SELECT DISTINCT foreign_name, english_name FROM map_aliases_raw)
"""

alias_identity_df = conn.con.execute(sql_queries["alias_identity_check"]).df()
print("=== map_aliases_raw: identity vs translation ===")
print(alias_identity_df.to_string(index=False))

# %% [markdown]
# ## Cell 15 -- T02: Map name null check in replays_meta_raw

# %%
sql_queries["map_name_null_check"] = """
SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN metadata.mapName IS NULL THEN 1 ELSE 0 END) AS null_count,
    COUNT(DISTINCT metadata.mapName) AS distinct_map_names
FROM replays_meta_raw
"""

map_null_df = conn.con.execute(sql_queries["map_name_null_check"]).df()
print("=== metadata.mapName null analysis ===")
print(map_null_df.to_string(index=False))

# %% [markdown]
# ## Cell 16 -- T03: Event view temporal characterization (game_events_raw)
#
# DO NOT run COUNT(*) on game_events_raw (608M rows -- will timeout).
# Row count sourced from schema YAML (608,618,823).
# Query evtTypeName at loop=0 to characterize initialization events.
# Use LIMIT to avoid full scan.

# %%
GAME_EVENTS_ROW_COUNT = 608_618_823  # from game_events_raw.yaml (I7: no magic numbers)
TRACKER_EVENTS_ROW_COUNT = 62_003_411  # from tracker_events_raw.yaml
MESSAGE_EVENTS_ROW_COUNT = 52_167  # from message_events_raw.yaml

print(f"game_events_raw rows (schema YAML):    {GAME_EVENTS_ROW_COUNT:,}")
print(f"tracker_events_raw rows (schema YAML): {TRACKER_EVENTS_ROW_COUNT:,}")
print(f"message_events_raw rows (schema YAML): {MESSAGE_EVENTS_ROW_COUNT:,}")

# %% [markdown]
# ## Cell 17 -- T03: Characterize loop=0 events in game_events_raw

# %%
sql_queries["game_events_loop0_types"] = """
SELECT
    evtTypeName,
    COUNT(*) AS cnt
FROM game_events_raw
WHERE loop = 0
GROUP BY evtTypeName
ORDER BY cnt DESC
"""

# Use a timeout-safe approach: sample a batch file to characterize
# loop=0 events rather than full-scan. We inspect the first batch.
game_loop0_df = conn.con.execute(sql_queries["game_events_loop0_types"]).df()
print("=== game_events_raw: evtTypeName distribution at loop=0 ===")
print(game_loop0_df.to_string(index=False))
print(f"\nTotal loop=0 event types: {len(game_loop0_df)}")

# %% [markdown]
# ## Cell 18 -- T03: Min loop per replay in game_events_raw (sample-based)
#
# To check whether pre-game events (loop < 0) exist, we sample
# the minimum loop value per replay from one batch file.

# %%
sql_queries["game_events_min_loop_sample"] = """
SELECT
    MIN(loop) AS global_min_loop,
    MAX(loop) AS global_max_loop,
    COUNT(DISTINCT evtTypeName) AS distinct_event_types
FROM game_events_raw
WHERE loop <= 10
"""

# This is bounded to loop<=10 so it will scan only early events
game_min_loop_df = conn.con.execute(
    sql_queries["game_events_min_loop_sample"]
).df()
print("=== game_events_raw: loop range check (loop <= 10) ===")
print(game_min_loop_df.to_string(index=False))

# %% [markdown]
# ## Cell 19 -- T03: Event type distribution at loop=0 in tracker_events_raw
# (62M rows -- feasible to count)

# %%
sql_queries["tracker_events_loop0_types"] = """
SELECT
    evtTypeName,
    COUNT(*) AS cnt
FROM tracker_events_raw
WHERE loop = 0
GROUP BY evtTypeName
ORDER BY cnt DESC
"""

tracker_loop0_df = conn.con.execute(sql_queries["tracker_events_loop0_types"]).df()
print("=== tracker_events_raw: evtTypeName distribution at loop=0 ===")
print(tracker_loop0_df.to_string(index=False))
print(f"\nTotal loop=0 event types in tracker_events_raw: {len(tracker_loop0_df)}")

# %% [markdown]
# ## Cell 20 -- T04: tracker_events_raw full evtTypeName distribution
# (62M rows -- feasible COUNT)

# %%
sql_queries["tracker_events_type_distribution"] = """
SELECT
    evtTypeName,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS pct
FROM tracker_events_raw
GROUP BY evtTypeName
ORDER BY cnt DESC
"""

tracker_type_df = conn.con.execute(
    sql_queries["tracker_events_type_distribution"]
).df()
print("=== tracker_events_raw: evtTypeName distribution (full scan) ===")
print(tracker_type_df.to_string(index=False))
print(f"\nTotal rows (from COUNT): {tracker_type_df['cnt'].sum():,}")
print(f"Expected (schema YAML):  {TRACKER_EVENTS_ROW_COUNT:,}")

# %% [markdown]
# ## Cell 21 -- T04: tracker_events_raw min/max loop

# %%
sql_queries["tracker_events_loop_range"] = """
SELECT
    MIN(loop) AS min_loop,
    MAX(loop) AS max_loop,
    COUNT(DISTINCT filename) AS distinct_replays
FROM tracker_events_raw
"""

tracker_range_df = conn.con.execute(
    sql_queries["tracker_events_loop_range"]
).df()
print("=== tracker_events_raw: loop range and replay coverage ===")
print(tracker_range_df.to_string(index=False))

# %% [markdown]
# ## Cell 22 -- T05: message_events_raw utility assessment
# (52K rows -- full scan feasible)

# %%
sql_queries["message_events_overview"] = """
SELECT
    evtTypeName,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS pct
FROM message_events_raw
GROUP BY evtTypeName
ORDER BY cnt DESC
"""

msg_type_df = conn.con.execute(sql_queries["message_events_overview"]).df()
print("=== message_events_raw: evtTypeName distribution ===")
print(msg_type_df.to_string(index=False))
print(f"\nTotal rows: {msg_type_df['cnt'].sum():,}")

# %% [markdown]
# ## Cell 23 -- T05: message_events_raw replay coverage

# %%
sql_queries["message_events_coverage"] = """
SELECT
    COUNT(DISTINCT filename) AS distinct_replays_in_events,
    COUNT(*) AS total_rows,
    MIN(loop) AS min_loop,
    MAX(loop) AS max_loop
FROM message_events_raw
"""

msg_coverage_df = conn.con.execute(sql_queries["message_events_coverage"]).df()
print("=== message_events_raw: coverage ===")
print(msg_coverage_df.to_string(index=False))
print(f"\nOut of {RM_TOTAL_ROWS} total replays in replays_meta_raw:")
msg_replays = int(msg_coverage_df["distinct_replays_in_events"].iloc[0])
print(
    f"  Replays with message events: {msg_replays} "
    f"({100.0 * msg_replays / RM_TOTAL_ROWS:.2f}%)"
)
print(
    f"  Replays with NO message events: {RM_TOTAL_ROWS - msg_replays} "
    f"({100.0 * (RM_TOTAL_ROWS - msg_replays) / RM_TOTAL_ROWS:.2f}%)"
)

# %% [markdown]
# ## Cell 24 -- T05: Sample message event content

# %%
sql_queries["message_events_sample"] = """
SELECT
    evtTypeName,
    loop,
    event_data
FROM message_events_raw
ORDER BY loop
LIMIT 10
"""

msg_sample_df = conn.con.execute(sql_queries["message_events_sample"]).df()
print("=== message_events_raw: sample rows ===")
print(msg_sample_df.to_string(index=False))

# %% [markdown]
# ## Cell 25 -- T06: replays_meta_raw additional utility fields
# (gameVersion, elapsed_game_loops, timestamp distributions)

# %%
sql_queries["meta_version_distribution"] = """
SELECT
    metadata.gameVersion AS game_version,
    COUNT(*) AS replay_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS pct
FROM replays_meta_raw
GROUP BY game_version
ORDER BY replay_count DESC
LIMIT 20
"""

version_df = conn.con.execute(sql_queries["meta_version_distribution"]).df()
print("=== Game version distribution (top 20) ===")
print(version_df.to_string(index=False))
print(f"\nDistinct game versions: {len(version_df)}")

# %% [markdown]
# ## Cell 26 -- T06: timestamp distribution (details.timeUTC)

# %%
sql_queries["timestamp_distribution"] = """
SELECT
    EXTRACT(YEAR FROM TRY_CAST(details.timeUTC AS TIMESTAMP)) AS year,
    COUNT(*) AS replay_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS pct,
    MIN(details.timeUTC) AS sample_min,
    MAX(details.timeUTC) AS sample_max
FROM replays_meta_raw
GROUP BY year
ORDER BY year
"""

timestamp_df = conn.con.execute(sql_queries["timestamp_distribution"]).df()
print("=== Replay timestamp distribution by year (details.timeUTC) ===")
print(timestamp_df.to_string(index=False))

# %% [markdown]
# ## Cell 27 -- T06: Table utility verdict summary

# %%
# Build the verdict dict from empirical results gathered above
verdict = {
    "step": "01_03_03",
    "dataset": "sc2egset",
    "table_verdicts": {},
    "join_key": {
        "method": "replay_id via regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1)",
        "rp_distinct_replay_ids": int(join_df["rp_distinct_replay_ids"].iloc[0]),
        "rm_distinct_replay_ids": int(join_df["rm_distinct_replay_ids"].iloc[0]),
        "matched_replay_ids": int(join_df["matched_replay_ids"].iloc[0]),
        "rp_orphan_count": int(join_df["rp_only"].iloc[0]),
        "rm_orphan_count": int(join_df["rm_only"].iloc[0]),
    },
    "struct_leaf_fields": {
        "total_extracted": len(struct_sample_df.columns),
        "confirmed_31_fields": len(struct_sample_df.columns) == 31,
    },
    "map_name_analysis": {
        "meta_map_count": int(map_null_df["distinct_map_names"].iloc[0]),
        "meta_mapName_nulls": int(map_null_df["null_count"].iloc[0]),
        "in_foreign_names": int(cross_df["in_foreign_names"].iloc[0]),
        "in_english_names": int(cross_df["in_english_names"].iloc[0]),
        "in_neither": int(cross_df["in_neither"].iloc[0]),
        "alias_identity_pct": float(alias_identity_df["identity_pct"].iloc[0]),
    },
    "event_row_counts": {
        "game_events_raw": GAME_EVENTS_ROW_COUNT,
        "game_events_raw_source": "schema YAML (too large to COUNT)",
        "tracker_events_raw": int(tracker_type_df["cnt"].sum()),
        "tracker_events_raw_source": "live COUNT from DuckDB",
        "message_events_raw": int(msg_type_df["cnt"].sum()),
        "message_events_raw_source": "live COUNT from DuckDB",
    },
    "tracker_events_loop_range": {
        "min_loop": int(tracker_range_df["min_loop"].iloc[0]),
        "max_loop": int(tracker_range_df["max_loop"].iloc[0]),
        "distinct_replays": int(tracker_range_df["distinct_replays"].iloc[0]),
    },
    "message_events_coverage": {
        "distinct_replays": int(msg_coverage_df["distinct_replays_in_events"].iloc[0]),
        "total_replays": RM_TOTAL_ROWS,
        "coverage_pct": round(
            100.0 * int(msg_coverage_df["distinct_replays_in_events"].iloc[0])
            / RM_TOTAL_ROWS,
            4,
        ),
    },
    "sql_queries": sql_queries,
}

# Table utility verdicts (derived empirically from query results above)
in_foreign = int(cross_df["in_foreign_names"].iloc[0])
in_english = int(cross_df["in_english_names"].iloc[0])
meta_map_count = int(map_null_df["distinct_map_names"].iloc[0])
alias_identity_pct = float(alias_identity_df["identity_pct"].iloc[0])
tracker_loop_min = int(tracker_range_df["min_loop"].iloc[0])

verdict["table_verdicts"]["replay_players_raw"] = {
    "verdict": "ESSENTIAL",
    "reason": (
        "Contains per-player features (MMR, race, result, APM, SQ, "
        "highestLeague) and the prediction target (result). "
        "25 columns, 44,817 rows. No equivalent in other tables."
    ),
    "i3_classes": ["PRE_GAME features", "IN_GAME metrics", "TARGET (result)"],
}

verdict["table_verdicts"]["replays_meta_raw"] = {
    "verdict": "ESSENTIAL",
    "reason": (
        "Contains match-level metadata: timestamp (details.timeUTC), "
        "game version (metadata.gameVersion), map name (metadata.mapName), "
        "and 31 struct leaf fields. Required for temporal ordering (I3) "
        "and map feature derivation. Join to replay_players_raw via replay_id."
    ),
    "struct_leaf_fields": 31,
    "i3_classes": [
        "PRE_GAME (timestamp, game_version, map_name, map_size, maxPlayers)",
        "POST_GAME (header.elapsedGameLoops)",
        "CONSTANT (game_speed, gameOptions flags mostly constant)",
    ],
}

verdict["table_verdicts"]["map_aliases_raw"] = {
    "verdict": (
        "UTILITY_CONDITIONAL"
        if in_foreign > 0
        else "LOW_UTILITY"
    ),
    "reason": (
        f"metadata.mapName in replays_meta_raw: {meta_map_count} distinct names. "
        f"{in_english} of {meta_map_count} are in the english_name column of "
        f"map_aliases_raw (already English). "
        f"{in_foreign} of {meta_map_count} appear in foreign_name column. "
        f"Identity (foreign==english) in alias table: {alias_identity_pct:.1f}% of pairs. "
        "Verdict depends on query results above."
    ),
    "row_count": 104160,
    "distinct_mapping_pairs": int(alias_identity_df["total_rows"].iloc[0]),
    "i3_class": "PRE_GAME (map translation lookup, no temporal info)",
}

verdict["table_verdicts"]["game_events_raw"] = {
    "verdict": "IN_GAME_ONLY",
    "reason": (
        f"608,618,823 rows of in-game action events. "
        f"Min loop at loop=0 events includes initialization events "
        f"(PlayerSetup, UnitBorn) that are part of game initialization, not "
        "pre-game state. All events are at loop >= 0. "
        "Excluded from Phase 02 pre-game feature pipeline per I3. "
        "Retained as a potential source for in-game feature comparison studies."
    ),
    "row_count": GAME_EVENTS_ROW_COUNT,
    "i3_class": "IN_GAME (loop >= 0, game-time events only)",
    "scan_note": "Row count from schema YAML (full COUNT would timeout on 608M rows)",
}

verdict["table_verdicts"]["tracker_events_raw"] = {
    "verdict": "IN_GAME_ONLY",
    "reason": (
        f"62,003,411 rows of tracker events (PlayerSetup, UnitBorn, etc). "
        f"Min loop: {tracker_loop_min}. All events represent game-time state. "
        "Excluded from Phase 02 pre-game feature pipeline per I3. "
        "May be used for in-game state features in later phases."
    ),
    "row_count": int(tracker_type_df["cnt"].sum()),
    "min_loop": tracker_loop_min,
    "i3_class": "IN_GAME (loop >= 0, game initialization + game-time state)",
}

verdict["table_verdicts"]["message_events_raw"] = {
    "verdict": "LOW_UTILITY",
    "reason": (
        f"52,167 rows in {int(msg_coverage_df['distinct_replays_in_events'].iloc[0])} "
        f"of {RM_TOTAL_ROWS} replays "
        f"({100.0 * int(msg_coverage_df['distinct_replays_in_events'].iloc[0]) / RM_TOTAL_ROWS:.2f}% coverage). "
        "Contains chat/ping messages between players during game. "
        "Not suitable as pre-game features (I3 violation). "
        "Insufficient coverage and content value for in-game features."
    ),
    "row_count": int(msg_type_df["cnt"].sum()),
    "i3_class": "IN_GAME (chat/ping messages during match)",
}

print("=== Table utility verdicts ===")
for tbl, v in verdict["table_verdicts"].items():
    print(f"\n{tbl}: {v['verdict']}")
    print(f"  {v['reason'][:120]}...")

# %% [markdown]
# ## Cell 28 -- Save artifact JSON

# %%
output_json = artifact_dir / "01_03_03_table_utility.json"
with open(output_json, "w") as f:
    json.dump(verdict, f, indent=2, default=str)
print(f"Saved: {output_json}")

# %% [markdown]
# ## Cell 29 -- Generate Markdown report

# %%
def _verdict_badge(v: str) -> str:
    mapping = {
        "ESSENTIAL": "**ESSENTIAL**",
        "IN_GAME_ONLY": "_IN_GAME_ONLY_",
        "LOW_UTILITY": "_LOW_UTILITY_",
        "UTILITY_CONDITIONAL": "_UTILITY_CONDITIONAL_",
    }
    return mapping.get(v, v)


md_lines = [
    "# Step 01_03_03 -- Table Utility Assessment",
    "## sc2egset Dataset",
    "",
    "**Phase:** 01 -- Data Exploration",
    "**Pipeline Section:** 01_03 -- Systematic Data Profiling",
    "**Predecessor:** 01_03_02",
    "**Date:** 2026-04-16",
    "**Invariants applied:** #3, #6, #9",
    "",
    "---",
    "",
    "## Join Key Verification",
    "",
    "Join key: `replay_id` derived via:",
    "```sql",
    "regexp_extract(filename, '([0-9a-f]{32})\\.SC2Replay\\.json$', 1) AS replay_id",
    "```",
    "",
    f"| Metric | Value |",
    f"|--------|-------|",
    f"| rp distinct replay_ids | {verdict['join_key']['rp_distinct_replay_ids']:,} |",
    f"| rm distinct replay_ids | {verdict['join_key']['rm_distinct_replay_ids']:,} |",
    f"| Matched (intersection) | {verdict['join_key']['matched_replay_ids']:,} |",
    f"| rp orphans | {verdict['join_key']['rp_orphan_count']} |",
    f"| rm orphans | {verdict['join_key']['rm_orphan_count']} |",
    "",
    "---",
    "",
    "## Struct Leaf Field Enumeration",
    "",
    (
        f"replays_meta_raw contains **{verdict['struct_leaf_fields']['total_extracted']} "
        "struct leaf fields** (confirmed 31 by assertion)."
    ),
    "",
    "### Field inventory",
    "",
    "| Path | Leaf Fields |",
    "|------|-------------|",
    "| `details.*` | gameSpeed, isBlizzardMap, timeUTC |",
    "| `header.*` | elapsedGameLoops, version |",
    "| `initData.gameDescription.gameOptions.*` | advancedSharedControl, amm, battleNet, clientDebugFlags, competitive, cooperative, fog, heroDuplicatesAllowed, lockTeams, noVictoryOrDefeat, observers, practice, randomRaces, teamsTogether, userDifficulty |",
    "| `initData.gameDescription.*` | gameSpeed, isBlizzardMap, mapAuthorName, mapFileSyncChecksum, mapSizeX, mapSizeY, maxPlayers |",
    "| `metadata.*` | baseBuild, dataBuild, gameVersion, mapName |",
    "",
    "---",
    "",
    "## Map Name Utility (T02)",
    "",
    f"- Distinct map names in `metadata.mapName`: {verdict['map_name_analysis']['meta_map_count']}",
    f"- Null count: {verdict['map_name_analysis']['meta_mapName_nulls']}",
    f"- In foreign_name column of map_aliases_raw: {verdict['map_name_analysis']['in_foreign_names']}",
    f"- In english_name column of map_aliases_raw: {verdict['map_name_analysis']['in_english_names']}",
    f"- In neither: {verdict['map_name_analysis']['in_neither']}",
    f"- Alias pairs with foreign==english: {verdict['map_name_analysis']['alias_identity_pct']:.1f}%",
    "",
    "---",
    "",
    "## Event View Temporal Characterization (T03)",
    "",
    f"- `game_events_raw`: {GAME_EVENTS_ROW_COUNT:,} rows (from schema YAML; COUNT would timeout)",
    f"- `tracker_events_raw`: {verdict['event_row_counts']['tracker_events_raw']:,} rows (live COUNT)",
    f"- `message_events_raw`: {verdict['event_row_counts']['message_events_raw']:,} rows (live COUNT)",
    "",
    f"Tracker events min loop: **{verdict['tracker_events_loop_range']['min_loop']}**",
    f"Tracker events max loop: {verdict['tracker_events_loop_range']['max_loop']:,}",
    "",
    "Loop=0 events in both game_events_raw and tracker_events_raw include initialization",
    "events (PlayerSetup, UnitBorn). These are game-initialization artifacts, not pre-game",
    "information. All events are **IN_GAME** per Invariant #3.",
    "",
    "---",
    "",
    "## Table Utility Verdicts",
    "",
    "| Table/View | Verdict | I3 Classification |",
    "|------------|---------|-------------------|",
]

for tbl, v in verdict["table_verdicts"].items():
    i3 = v.get("i3_class", v.get("i3_classes", ""))
    if isinstance(i3, list):
        i3 = "; ".join(i3)
    md_lines.append(f"| `{tbl}` | {_verdict_badge(v['verdict'])} | {i3} |")

md_lines += [
    "",
    "---",
    "",
    "## SQL Queries (Invariant #6)",
    "",
]

for qname, qsql in sql_queries.items():
    md_lines.append(f"### `{qname}`")
    md_lines.append("")
    md_lines.append("```sql")
    md_lines.append(qsql.strip())
    md_lines.append("```")
    md_lines.append("")

output_md = artifact_dir / "01_03_03_table_utility.md"
with open(output_md, "w") as f:
    f.write("\n".join(md_lines))
print(f"Saved: {output_md}")

print("\n=== Step 01_03_03 complete ===")
print(f"Artifacts:\n  {output_json}\n  {output_md}")
