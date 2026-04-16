# Step 01_03_03 -- Table Utility Assessment
## sc2egset Dataset

**Phase:** 01 -- Data Exploration
**Pipeline Section:** 01_03 -- Systematic Data Profiling
**Predecessor:** 01_03_02
**Date:** 2026-04-16
**Invariants applied:** #3, #6, #9

---

## Join Key Verification

Join key: `replay_id` derived via:
```sql
regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id
```

| Metric | Value |
|--------|-------|
| rp distinct replay_ids | 22,390 |
| rm distinct replay_ids | 22,390 |
| Matched (intersection) | 22,390 |
| rp orphans | 0 |
| rm orphans | 0 |

---

## Struct Leaf Field Enumeration

replays_meta_raw contains **31 struct leaf fields** (confirmed 31 by assertion).

### Field inventory

| Path | Leaf Fields |
|------|-------------|
| `details.*` | gameSpeed, isBlizzardMap, timeUTC |
| `header.*` | elapsedGameLoops, version |
| `initData.gameDescription.gameOptions.*` | advancedSharedControl, amm, battleNet, clientDebugFlags, competitive, cooperative, fog, heroDuplicatesAllowed, lockTeams, noVictoryOrDefeat, observers, practice, randomRaces, teamsTogether, userDifficulty |
| `initData.gameDescription.*` | gameSpeed, isBlizzardMap, mapAuthorName, mapFileSyncChecksum, mapSizeX, mapSizeY, maxPlayers |
| `metadata.*` | baseBuild, dataBuild, gameVersion, mapName |

---

## Map Name Utility (T02)

- Distinct map names in `metadata.mapName`: 188
- Null count: 0
- In foreign_name column of map_aliases_raw: 188
- In english_name column of map_aliases_raw: 188
- In neither: 0
- Alias pairs with foreign==english: 14.4%

---

## Event View Temporal Characterization (T03)

- `game_events_raw`: 608,618,823 rows (from schema YAML; COUNT would timeout)
- `tracker_events_raw`: 62,003,411 rows (live COUNT)
- `message_events_raw`: 52,167 rows (live COUNT)

Tracker events min loop: **0**
Tracker events max loop: 109,287

Loop=0 events in both game_events_raw and tracker_events_raw include initialization
events (PlayerSetup, UnitBorn). These are game-initialization artifacts, not pre-game
information. All events are **IN_GAME** per Invariant #3.

---

## Table Utility Verdicts

| Table/View | Verdict | I3 Classification |
|------------|---------|-------------------|
| `replay_players_raw` | **ESSENTIAL** | PRE_GAME features; IN_GAME metrics; TARGET (result) |
| `replays_meta_raw` | **ESSENTIAL** | PRE_GAME (timestamp, game_version, map_name, map_size, maxPlayers); POST_GAME (header.elapsedGameLoops); CONSTANT (game_speed, gameOptions flags mostly constant) |
| `map_aliases_raw` | _UTILITY_CONDITIONAL_ | PRE_GAME (map translation lookup, no temporal info) |
| `game_events_raw` | _IN_GAME_ONLY_ | IN_GAME (loop >= 0, game-time events only) |
| `tracker_events_raw` | _IN_GAME_ONLY_ | IN_GAME (loop >= 0, game initialization + game-time state) |
| `message_events_raw` | _LOW_UTILITY_ | IN_GAME (chat/ping messages during match) |

---

## SQL Queries (Invariant #6)

### `describe_replay_players_raw`

```sql
DESCRIBE replay_players_raw
```

### `describe_replays_meta_raw`

```sql
DESCRIBE replays_meta_raw
```

### `struct_leaf_census`

```sql
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
```

### `struct_leaf_null_cardinality`

```sql
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
```

### `go_flag_distributions`

```sql
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
```

### `join_verification_replay_id`

```sql
WITH rp_distinct AS (
    SELECT DISTINCT
        regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id
    FROM replay_players_raw
    WHERE regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) != ''
),
rm_distinct AS (
    SELECT DISTINCT
        regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id
    FROM replays_meta_raw
    WHERE regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) != ''
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
```

### `replay_id_sample`

```sql
SELECT
    filename,
    regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id
FROM replays_meta_raw
LIMIT 10
```

### `empty_replay_id_check`

```sql
SELECT COUNT(*) AS empty_count
FROM replays_meta_raw
WHERE regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) = ''
```

### `meta_map_name_sample`

```sql
SELECT
    metadata.mapName AS map_name,
    COUNT(*) AS replay_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS pct
FROM replays_meta_raw
GROUP BY map_name
ORDER BY replay_count DESC
LIMIT 30
```

### `map_aliases_raw_overview`

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT tournament) AS distinct_tournaments,
    COUNT(DISTINCT foreign_name) AS distinct_foreign_names,
    COUNT(DISTINCT english_name) AS distinct_english_names,
    COUNT(DISTINCT filename) AS distinct_files
FROM map_aliases_raw
```

### `map_aliases_sample`

```sql
SELECT foreign_name, english_name
FROM map_aliases_raw
WHERE tournament = (SELECT MIN(tournament) FROM map_aliases_raw)
ORDER BY foreign_name
LIMIT 30
```

### `map_name_vs_aliases_cross`

```sql
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
```

### `alias_identity_check`

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE foreign_name = english_name) AS identity_count,
    COUNT(*) FILTER (WHERE foreign_name != english_name) AS translated_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE foreign_name = english_name) / COUNT(*),
        2
    ) AS identity_pct
FROM (SELECT DISTINCT foreign_name, english_name FROM map_aliases_raw)
```

### `map_name_null_check`

```sql
SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN metadata.mapName IS NULL THEN 1 ELSE 0 END) AS null_count,
    COUNT(DISTINCT metadata.mapName) AS distinct_map_names
FROM replays_meta_raw
```

### `game_events_loop0_types`

```sql
SELECT
    evtTypeName,
    COUNT(*) AS cnt
FROM game_events_raw
WHERE loop = 0
GROUP BY evtTypeName
ORDER BY cnt DESC
```

### `game_events_min_loop_sample`

```sql
SELECT
    MIN(loop) AS global_min_loop,
    MAX(loop) AS global_max_loop,
    COUNT(DISTINCT evtTypeName) AS distinct_event_types
FROM game_events_raw
WHERE loop <= 10
```

### `tracker_events_loop0_types`

```sql
SELECT
    evtTypeName,
    COUNT(*) AS cnt
FROM tracker_events_raw
WHERE loop = 0
GROUP BY evtTypeName
ORDER BY cnt DESC
```

### `tracker_events_type_distribution`

```sql
SELECT
    evtTypeName,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS pct
FROM tracker_events_raw
GROUP BY evtTypeName
ORDER BY cnt DESC
```

### `tracker_events_loop_range`

```sql
SELECT
    MIN(loop) AS min_loop,
    MAX(loop) AS max_loop,
    COUNT(DISTINCT filename) AS distinct_replays
FROM tracker_events_raw
```

### `message_events_overview`

```sql
SELECT
    evtTypeName,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS pct
FROM message_events_raw
GROUP BY evtTypeName
ORDER BY cnt DESC
```

### `message_events_coverage`

```sql
SELECT
    COUNT(DISTINCT filename) AS distinct_replays_in_events,
    COUNT(*) AS total_rows,
    MIN(loop) AS min_loop,
    MAX(loop) AS max_loop
FROM message_events_raw
```

### `message_events_sample`

```sql
SELECT
    evtTypeName,
    loop,
    event_data
FROM message_events_raw
ORDER BY loop
LIMIT 10
```

### `meta_version_distribution`

```sql
SELECT
    metadata.gameVersion AS game_version,
    COUNT(*) AS replay_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS pct
FROM replays_meta_raw
GROUP BY game_version
ORDER BY replay_count DESC
LIMIT 20
```

### `timestamp_distribution`

```sql
SELECT
    EXTRACT(YEAR FROM TRY_CAST(details.timeUTC AS TIMESTAMP)) AS year,
    COUNT(*) AS replay_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS pct,
    MIN(details.timeUTC) AS sample_min,
    MAX(details.timeUTC) AS sample_max
FROM replays_meta_raw
GROUP BY year
ORDER BY year
```
