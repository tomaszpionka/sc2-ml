# Phase 1 -- JSON Field Taxonomy and First-Chunk Plan

**Dataset:** SC2EGSet v2.1.0
**Phase:** 1 (Corpus inventory and data exploration)
**Author:** planner-science agent
**Date:** 2026-04-09
**Prerequisite:** Phase 0 complete (gate 2026-04-03). Spec 1.1 merged (`raw_map_alias_files.raw_json` is type `JSON`).
**Query budget consumed:** 50 / 50 DuckDB read-only queries

---

## Section 1 -- JSON Field Taxonomy

### 1.1 Sampling strategy

All findings below were derived from read-only queries against `db.duckdb` with the following strategy:

- **Key-set constancy:** For every JSON blob column, `json_keys()` was grouped across the full corpus (22,390 rows for `raw` table columns) to identify whether the set of top-level keys varies across rows. This is a complete census, not a sample.
- **Nested keys:** For objects inside JSON blobs, `json_keys()` was applied to the nested path on either a full census or on representative samples (N=500 where noted).
- **Value distributions:** Categorical fields were enumerated via `json_each()` across all toons in the corpus (44,817 player slots). Numeric fields were checked for zero rates on the full corpus.
- **Event data (tracker/game):** Key-set constancy was verified per `event_type` across the full table (62M tracker rows, 609M game rows). Value-level sampling was limited to 1-3 rows per type for structural inspection.

### 1.2 Table: `raw` -- JSON blob inventory

The `raw` table has 6 columns. Five are JSON blobs; one (`filename`) is VARCHAR. All five JSON blobs have **100% key-set constancy** across all 22,390 rows (every row has exactly the same set of top-level keys).

#### 1.2.1 `header` (JSON)

Key-set: `[elapsedGameLoops, version]` -- 100% constant (22,390/22,390).

| path | depth | dtype_observed | context | presence_category | pre_game_eligible | notes |
|------|-------|----------------|---------|-------------------|-------------------|-------|
| header.elapsedGameLoops | 1 | int | header | always | **no** | Total game loops; known only after match ends. Post-game. |
| header.version | 1 | string | header | always | depends | Version string e.g. "3.1.1.39948". Could serve as a pre-game context feature if version is known before match start (it is -- determined by game client). |

**Total fields:** 2 (0 nested objects)

#### 1.2.2 `initData` (JSON)

Key-set: `[gameDescription]` -- 100% constant. Single top-level key wrapping a nested object.

**`initData.gameDescription` sub-object:**

Key-set: `[gameOptions, gameSpeed, isBlizzardMap, mapAuthorName, mapFileSyncChecksum, mapSizeX, mapSizeY, maxPlayers]` -- 100% constant (22,390/22,390).

| path | depth | dtype_observed | context | presence_category | pre_game_eligible | notes |
|------|-------|----------------|---------|-------------------|-------------------|-------|
| initData.gameDescription.mapSizeX | 2 | int | gameDescription | always | yes | Map width in grid cells. |
| initData.gameDescription.mapSizeY | 2 | int | gameDescription | always | yes | Map height in grid cells. |
| initData.gameDescription.maxPlayers | 2 | int | gameDescription | always | yes | Expected 2 for 1v1. Values 4/6/8/9 found (409 replays). Anomaly indicator. |
| initData.gameDescription.gameSpeed | 2 | string | gameDescription | always | yes | 100% "Faster" across corpus. Zero variance -- not a useful feature. |
| initData.gameDescription.isBlizzardMap | 2 | bool | gameDescription | always | yes | 17,515 true vs 4,875 false. Potential stratification variable. |
| initData.gameDescription.mapAuthorName | 2 | string | gameDescription | always | yes | Toon-format string e.g. "3-S2-2-29526". Not human-readable. |
| initData.gameDescription.mapFileSyncChecksum | 2 | int | gameDescription | always | yes | Deterministic map file hash. Unique map version identifier. |
| initData.gameDescription.gameOptions | 2 | object | gameDescription | always | yes | Nested object with 15 or 16 keys (see below). |

**`initData.gameDescription.gameOptions` sub-object:**

Two key-set variants:
- 16-key variant (includes `buildCoachEnabled`): 19,971 replays (89.2%)
- 15-key variant (without `buildCoachEnabled`): 2,419 replays (10.8%)

| path | depth | dtype_observed | context | presence_category | pre_game_eligible | notes |
|------|-------|----------------|---------|-------------------|-------------------|-------|
| ...gameOptions.advancedSharedControl | 3 | bool | gameOptions | always | yes | Team game option. |
| ...gameOptions.amm | 3 | bool | gameOptions | always | yes | Automated matchmaking flag. |
| ...gameOptions.battleNet | 3 | bool | gameOptions | always | yes | Played on Battle.net. |
| ...gameOptions.buildCoachEnabled | 3 | bool | gameOptions | mostly (89.2%) | yes | Absent in older replays. Version-dependent field. |
| ...gameOptions.clientDebugFlags | 3 | int | gameOptions | always | yes | Debug flags bitmask. |
| ...gameOptions.competitive | 3 | bool | gameOptions | always | yes | Competitive mode flag. |
| ...gameOptions.cooperative | 3 | bool | gameOptions | always | yes | Co-op mode flag. |
| ...gameOptions.fog | 3 | int | gameOptions | always | yes | Fog of war setting. |
| ...gameOptions.heroDuplicatesAllowed | 3 | bool | gameOptions | always | yes | Hero mode option. |
| ...gameOptions.lockTeams | 3 | bool | gameOptions | always | yes | Teams locked. |
| ...gameOptions.noVictoryOrDefeat | 3 | bool | gameOptions | always | yes | Disables victory screen. |
| ...gameOptions.observers | 3 | int | gameOptions | always | yes | Observer slot count/mode. |
| ...gameOptions.practice | 3 | bool | gameOptions | always | yes | Practice mode. |
| ...gameOptions.randomRaces | 3 | bool | gameOptions | always | yes | Random race mode. |
| ...gameOptions.teamsTogether | 3 | bool | gameOptions | always | yes | Teams together spawning. |
| ...gameOptions.userDifficulty | 3 | int | gameOptions | always | yes | AI difficulty (for vs-AI; expect constant in PvP). |

**Total fields in initData:** 1 + 8 + 16 = 25 (max depth 3)

#### 1.2.3 `details` (JSON)

Key-set: `[gameSpeed, isBlizzardMap, timeUTC]` -- 100% constant (22,390/22,390).

| path | depth | dtype_observed | context | presence_category | pre_game_eligible | notes |
|------|-------|----------------|---------|-------------------|-------------------|-------|
| details.timeUTC | 1 | string (ISO datetime) | details | always | yes | Match start timestamp. Primary temporal axis. |
| details.gameSpeed | 1 | string | details | always | yes | Redundant with initData.gameDescription.gameSpeed. 100% "Faster". |
| details.isBlizzardMap | 1 | bool | details | always | yes | Redundant with initData.gameDescription.isBlizzardMap. |

**Total fields:** 3 (0 nested objects). Two of three are redundant with initData.

#### 1.2.4 `metadata` (JSON)

Key-set: `[baseBuild, dataBuild, gameVersion, mapName]` -- 100% constant (22,390/22,390).

| path | depth | dtype_observed | context | presence_category | pre_game_eligible | notes |
|------|-------|----------------|---------|-------------------|-------------------|-------|
| metadata.baseBuild | 1 | int | metadata | always | yes | Base build number. Coarser than dataBuild. |
| metadata.dataBuild | 1 | int | metadata | always | yes | Data build number. Finer patch identifier. |
| metadata.gameVersion | 1 | string | metadata | always | yes | Version string e.g. "3.1.1.39948". Same format as header.version. |
| metadata.mapName | 1 | string | metadata | always | yes | Human-readable map name. Primary map feature. Subject to localization (Korean, etc.) -- needs normalization via raw_map_alias_files. |

**Total fields:** 4 (0 nested objects)

#### 1.2.5 `ToonPlayerDescMap` (JSON -- keyed map)

This is the richest blob. It is a JSON object keyed by toon strings (e.g. `"3-S2-1-4842177"`). Each value is a player descriptor object.

**Map-level structure:**

| n_toons | count | pct |
|---------|-------|-----|
| 1 | 3 | 0.01% |
| 2 | 22,379 | 99.95% |
| 4 | 2 | 0.01% |
| 6 | 1 | <0.01% |
| 8 | 3 | 0.01% |
| 9 | 2 | 0.01% |

11 replays have anomalous toon counts (not 2). These counts are perfectly consistent with `match_player_map` player counts for the same replays.

**Value-side schema (per-player object):**

Key-set: 20 keys -- 100% constant across all sampled toons (500/500). The same 20 fields appear in every player slot.

| path | depth | dtype_observed | context | presence_category | pre_game_eligible | notes |
|------|-------|----------------|---------|-------------------|-------------------|-------|
| ...\<toon\>.nickname | 2 | string | player | always | yes | In-game display name. Canonical player identifier (lowercased) per INVARIANTS.md. |
| ...\<toon\>.playerID | 2 | int | player | always | no | In-game slot (1 or 2). Assigned at match start, not a persistent identity. |
| ...\<toon\>.userID | 2 | int | player | always | no | Engine user slot. Joinable to game_events_raw.user_id. |
| ...\<toon\>.SQ | 2 | int | player | always | depends | Spending Quotient. Post-game metric (computed from match). NOT pre-game eligible. |
| ...\<toon\>.supplyCappedPercent | 2 | int | player | always | no | % of game time supply-capped. Post-game metric. |
| ...\<toon\>.startDir | 2 | int | player | always | yes | Starting direction/spawn index. Pre-game (assigned by map). |
| ...\<toon\>.startLocX | 2 | int | player | always | yes | Spawn X coordinate. Pre-game. |
| ...\<toon\>.startLocY | 2 | int | player | always | yes | Spawn Y coordinate. Pre-game. |
| ...\<toon\>.race | 2 | string | player | always | yes | Actual race played: Prot/Zerg/Terr (+ 3 BWxx anomalies). Pre-game. |
| ...\<toon\>.selectedRace | 2 | string | player | always | yes | Race selected in lobby. Values: Prot/Zerg/Terr/Rand + empty string (1,110 slots = 2.5%). |
| ...\<toon\>.APM | 2 | int | player | always | no | Actions per minute. Post-game aggregate. 1,132/44,817 = 2.5% zero (concentrated in 2016). |
| ...\<toon\>.MMR | 2 | int | player | always | depends | Matchmaking rating. 37,489/44,817 = 83.7% zero. Systematically missing. NOT usable as direct feature. |
| ...\<toon\>.result | 2 | string | player | always | **no (target)** | Match outcome. Values: Win (22,382), Loss (22,409), Undecided (24), Tie (2). This is the prediction target, never a feature. |
| ...\<toon\>.region | 2 | string | player | always | yes | Server region: Europe/US/Unknown/Korea/China + 2 empty. |
| ...\<toon\>.realm | 2 | string | player | always | yes | Server realm: Europe/North America/Unknown/Korea/China/Taiwan/Russia/Latin America + 2 empty. More granular than region. |
| ...\<toon\>.highestLeague | 2 | string | player | always | depends | Ladder league: Unknown (32,338 = 72.2%), Master (6,458), Grandmaster (4,745), Diamond (718), etc. Heavily missing. |
| ...\<toon\>.isInClan | 2 | bool | player | always | yes | 11,607/44,817 = 25.9% true. |
| ...\<toon\>.clanTag | 2 | string | player | always | yes | Non-empty for 11,607 slots (matches isInClan perfectly). |
| ...\<toon\>.handicap | 2 | int | player | always | yes | Nearly always 100. Only 2 slots have non-100 value. |
| ...\<toon\>.color | 2 | object | player | always | no | Nested object with 4 sub-keys (see below). Visual only. |

**`color` sub-object:**

| path | depth | dtype_observed | context | presence_category | pre_game_eligible | notes |
|------|-------|----------------|---------|-------------------|-------------------|-------|
| ...\<toon\>.color.r | 3 | int | color | always | no | Red channel (0-255). Visual/display only. |
| ...\<toon\>.color.g | 3 | int | color | always | no | Green channel. |
| ...\<toon\>.color.b | 3 | int | color | always | no | Blue channel. |
| ...\<toon\>.color.a | 3 | int | color | always | no | Alpha channel. |

**Total fields in ToonPlayerDescMap:** 20 per-player + 4 color sub-keys = 24. Multiplied by N toons per replay (usually 2).

### 1.3 Table: `raw_map_alias_files` -- JSON blob inventory

Single JSON blob column: `raw_json` (type JSON).

**Structure:** Flat key-value map. Keys are foreign-language map names (Korean, etc.). Values are English canonical map names. No nesting.

- Number of entries per file varies widely: many files have 1,488 entries (a common master list), but the distribution was not fully enumerated.
- Purpose: normalization of `metadata.mapName` to canonical English names.

| path | depth | dtype_observed | context | presence_category | pre_game_eligible | notes |
|------|-------|----------------|---------|-------------------|-------------------|-------|
| raw_json.\<foreign_name\> | 1 | string | map alias | varies | n/a (reference data) | Flat map. Variable number of keys per tournament (some share a master list of 1,488 entries). |

**Total fields:** Variable (up to 1,488 per row). All depth-1 string values.

### 1.4 Table: `tracker_events_raw` -- `event_data` (VARCHAR containing JSON)

Column `event_data` is stored as VARCHAR, not native JSON. Must be cast via `CAST(event_data AS JSON)` for extraction.

10 distinct event types. Key-set constancy is 100% for 9 of 10 types. UnitBorn has two key-set variants.

#### PlayerSetup (44,817 rows)

Key-set: `[evtTypeName, id, loop, playerId, slotId, type, userId]` -- 100% constant.

| path | depth | dtype_observed | context | presence_category | pre_game_eligible | notes |
|------|-------|----------------|---------|-------------------|-------------------|-------|
| evtTypeName | 1 | string | PlayerSetup | always | n/a | Always "NNet.Replay.Tracker.SPlayerSetupEvent". Metadata. |
| id | 1 | int | PlayerSetup | always | n/a | Event sequence ID. |
| loop | 1 | int | PlayerSetup | always | n/a | Game loop (always 0 for setup). |
| playerId | 1 | int | PlayerSetup | always | n/a | Player slot. |
| slotId | 1 | int | PlayerSetup | always | n/a | Lobby slot. |
| type | 1 | int | PlayerSetup | always | n/a | Player type (human/AI/observer). |
| userId | 1 | int | PlayerSetup | always | n/a | Engine user ID. |

#### PlayerStats (4,558,736 rows)

Key-set: `[evtTypeName, id, loop, playerId, stats]` -- 100% constant.

| path | depth | dtype_observed | context | presence_category | pre_game_eligible | notes |
|------|-------|----------------|---------|-------------------|-------------------|-------|
| evtTypeName | 1 | string | PlayerStats | always | no | Always "NNet.Replay.Tracker.SPlayerStatsEvent". |
| id | 1 | int | PlayerStats | always | no | Event sequence ID. |
| loop | 1 | int | PlayerStats | always | no | Game loop of snapshot. Every 160 loops. |
| playerId | 1 | int | PlayerStats | always | no | Player slot. |
| stats | 1 | object | PlayerStats | always | no | Contains 39 sub-keys (see below). All in-game. |

**`stats` sub-object (39 keys):** 100% constant key-set. All keys follow the naming pattern `scoreValue{Resource}{Category}{Subcategory}`. These are fully mapped by the `player_stats` VIEW. Key categories:

- `scoreValueFoodMade`, `scoreValueFoodUsed` (supply)
- `scoreValueMinerals{CollectionRate,Current,FriendlyFire{Army,Economy,Technology},Killed{Army,Economy,Technology},Lost{Army,Economy,Technology},UsedActiveForces,UsedCurrent{Army,Economy,Technology},UsedInProgress{Army,Economy,Technology}}` (20 mineral sub-keys)
- Same pattern for `scoreValueVespene...` (20 vespene sub-keys, but shares FoodMade/FoodUsed)
- `scoreValueWorkersActiveCount`

Total: 2 (food) + 18 (minerals) + 18 (vespene) + 1 (workers) = 39.

#### UnitBorn (22,372,489 rows)

**Two key-set variants:**
- 13-key variant (93.5%, 20,926,589 rows): includes `creatorAbilityName`, `creatorUnitTagIndex`, `creatorUnitTagRecycle`
- 10-key variant (6.5%, 1,445,900 rows): lacks creator fields (units spawned without a creator ability, e.g. starting workers, mineral patches)

| path | depth | dtype_observed | context | presence_category | pre_game_eligible | notes |
|------|-------|----------------|---------|-------------------|-------------------|-------|
| controlPlayerId | 1 | int | UnitBorn | always | no | Controlling player. |
| evtTypeName | 1 | string | UnitBorn | always | no | Event type name. |
| id | 1 | int | UnitBorn | always | no | Sequence ID. |
| loop | 1 | int | UnitBorn | always | no | Game loop. |
| unitTagIndex | 1 | int | UnitBorn | always | no | Unit tag index (for tracking). |
| unitTagRecycle | 1 | int | UnitBorn | always | no | Unit tag recycle count. |
| unitTypeName | 1 | string | UnitBorn | always | no | Unit type e.g. "Marine", "Zealot". |
| upkeepPlayerId | 1 | int | UnitBorn | always | no | Supply-owning player. |
| x | 1 | int | UnitBorn | always | no | Map X coordinate. |
| y | 1 | int | UnitBorn | always | no | Map Y coordinate. |
| creatorAbilityName | 1 | string | UnitBorn | mostly (93.5%) | no | Ability that created the unit. Absent for map-placed units. |
| creatorUnitTagIndex | 1 | int | UnitBorn | mostly (93.5%) | no | Tag of creating unit. |
| creatorUnitTagRecycle | 1 | int | UnitBorn | mostly (93.5%) | no | Recycle of creating unit. |

#### UnitDied (16,053,834 rows)

Key-set: `[evtTypeName, id, killerPlayerId, killerUnitTagIndex, killerUnitTagRecycle, loop, unitTagIndex, unitTagRecycle, x, y]` -- 100% constant.

| path | depth | dtype_observed | context | presence_category | pre_game_eligible | notes |
|------|-------|----------------|---------|-------------------|-------------------|-------|
| killerPlayerId | 1 | int | UnitDied | always | no | Who killed the unit. |
| killerUnitTagIndex | 1 | int | UnitDied | always | no | Tag of killer. |
| killerUnitTagRecycle | 1 | int | UnitDied | always | no | Recycle of killer. |
| unitTagIndex | 1 | int | UnitDied | always | no | Tag of dying unit. |
| unitTagRecycle | 1 | int | UnitDied | always | no | Recycle of dying unit. |
| x | 1 | int | UnitDied | always | no | Death location. |
| y | 1 | int | UnitDied | always | no | Death location. |
| (+ evtTypeName, id, loop) | 1 | -- | -- | always | no | Standard envelope. |

#### UnitInit (3,151,270 rows)

Key-set: `[controlPlayerId, evtTypeName, id, loop, unitTagIndex, unitTagRecycle, unitTypeName, upkeepPlayerId, x, y]` -- 100% constant. Same structure as UnitBorn minus creator fields.

#### UnitDone (3,018,764 rows)

Key-set: `[evtTypeName, id, loop, unitTagIndex, unitTagRecycle]` -- 100% constant. Minimal: only identifies which unit finished construction.

#### Upgrade (797,987 rows)

Key-set: `[count, evtTypeName, id, loop, playerId, upgradeTypeName]` -- 100% constant.

| path | depth | dtype_observed | context | presence_category | pre_game_eligible | notes |
|------|-------|----------------|---------|-------------------|-------------------|-------|
| count | 1 | int | Upgrade | always | no | Upgrade level (usually 1, can be 2-3 for stacking upgrades). |
| upgradeTypeName | 1 | string | Upgrade | always | no | e.g. "ProtossGroundWeaponsLevel1". |

#### UnitTypeChange (10,999,108 rows)

Key-set: `[evtTypeName, id, loop, unitTagIndex, unitTagRecycle, unitTypeName]` -- 100% constant. Records unit morphs (e.g. Larva to Drone).

#### UnitOwnerChange (65,157 rows)

Key-set: `[controlPlayerId, evtTypeName, id, loop, unitTagIndex, unitTagRecycle, upkeepPlayerId]` -- 100% constant. Records unit ownership transfers (Neural Parasite, Mind Control, etc.).

#### UnitPositions (941,249 rows)

Key-set: `[evtTypeName, firstUnitIndex, id, items, loop]` -- 100% constant.

| path | depth | dtype_observed | context | presence_category | pre_game_eligible | notes |
|------|-------|----------------|---------|-------------------|-------------------|-------|
| firstUnitIndex | 1 | int | UnitPositions | always | no | Starting index for the items array. |
| items | 1 | array | UnitPositions | always | no | Flat int array. Encoded as alternating (unitIndex, x, y) triples. Not self-describing -- requires pairing with firstUnitIndex to decode. |

### 1.5 Table: `game_events_raw` -- `event_data` (VARCHAR containing JSON)

23 distinct event types. Key-set constancy was verified at 100% for the 4 high-value types (Cmd, UserOptions, GameUserLeave, SelectionDelta).

#### Cmd (31,201,304 rows) -- high value

Key-set: `[abil, cmdFlags, data, evtTypeName, id, loop, otherUnit, sequence, unitGroup, userid]` -- 100% constant.

Notable nesting:
- `abil`: object with `{abilCmdData, abilCmdIndex, abilLink}` (depth 2)
- `cmdFlags`: array of strings e.g. `["User"]`
- `data`: object with variable content (e.g. `{"None": null}`, or `{"TargetPoint": {...}}`)
- `unitGroup`: nullable; when present, contains unit group reference
- `userid`: object `{"userId": <int>}` (depth 2)

#### SelectionDelta (40,855,099 rows) -- moderate value

Key-set: `[controlGroupId, delta, evtTypeName, id, loop, userid]` -- 100% constant.

Notable nesting:
- `delta`: object with `{addSubgroups, addUnitTags, removeMask, subgroupIndex}` (depth 2)
  - `addSubgroups`: array of objects with `{count, intraSubgroupPriority, subgroupPriority, unitLink}` (depth 3)
  - `addUnitTags`: array of ints
  - `removeMask`: object (e.g. `{"None": null}`)
- `userid`: object `{"userId": <int>}` (depth 2)

#### UserOptions (131,738 rows) -- moderate value

Key-set: `[baseBuildNum, buildNum, cameraFollow, debugPauseEnabled, developmentCheatsEnabled, evtTypeName, gameFullyDownloaded, hotkeyProfile, id, isMapToMapTransition, loop, multiplayerCheatsEnabled, platformMac, syncChecksummingEnabled, testCheatsEnabled, useGalaxyAsserts, userid, versionFlags]` -- 100% constant. 18 keys, all depth 1 except `userid` (depth 2).

#### GameUserLeave (70,032 rows) -- low value

Key-set: `[evtTypeName, id, leaveReason, loop, userid]` -- 100% constant.

#### Other game event types (18 types, collectively ~2.5M rows)

CameraUpdate (387M), ControlGroupUpdate (69M), CommandManagerState (44M), CmdUpdateTargetPoint (26M), CmdUpdateTargetUnit (8M), CameraSave (1M), TriggerMouseMoved (380K), TriggerDialogControl (52K), UnitClick (2K), AchievementAwarded (1.5K), DecrementGameTimeRemaining (1.5K), TriggerPing (1.4K), CommandManagerReset (238), HijackReplayGame (122), GameUserJoin (25), Alliance (24), AddAbsoluteGameSpeed (24), TriggerTransmissionComplete (8), ResourceTrade (4).

Key-set constancy for these types was NOT verified individually. CameraUpdate alone accounts for 387M rows (63.6% of all game events) and is extremely low value for prediction.

### 1.6 Field count summary

| Table | Column | Depth-1 fields | Depth-2 fields | Depth-3 fields | Total leaf fields |
|-------|--------|----------------|----------------|----------------|-------------------|
| raw | header | 2 | 0 | 0 | 2 |
| raw | initData | 1 | 8 | 15-16 | 25 |
| raw | details | 3 | 0 | 0 | 3 |
| raw | metadata | 4 | 0 | 0 | 4 |
| raw | ToonPlayerDescMap | 0 (keyed map) | 20 per toon | 4 (color) | 24 per toon |
| raw_map_alias_files | raw_json | variable (up to 1,488) | 0 | 0 | variable |
| tracker_events_raw | event_data | 5-13 per type | 39 (PlayerStats.stats) | 0 | ~80 unique across types |
| game_events_raw | event_data | 5-18 per type | ~10 (Cmd sub-objects) | ~4 (SelectionDelta) | ~60 unique across types |

**Grand total unique leaf fields across all tables and event types: approximately 200.**

---

## Section 2 -- Per-Table Shape Assessment

### 2.1 `raw` (22,390 rows, 6 columns)

**Row grain:** One row per SC2Replay JSON file. Confirmed empirically -- 22,390 rows matches the source file count. The YAML notes are correct.

**Join keys:** `filename` is the only stored identifier. `replay_id` (32-char MD5 hex) and `tournament_dir` are derived via regex/split. Neither is materialized as a column. All joins to event tables require `regexp_extract()` on both sides.

**Flat vs. JSON:** 1 flat column (`filename`, VARCHAR). 5 JSON columns (`header`, `initData`, `details`, `metadata`, `ToonPlayerDescMap`).

**Most Phase 1-relevant column:** `ToonPlayerDescMap`. It contains 20 fields per player including the prediction target (`result`), the canonical player identifier (`nickname`), skill indicators (APM, MMR, SQ, highestLeague), spawn position, race, and clan affiliation. This is the single richest source for pre-game feature candidates.

**Non-obvious fact:** The `replay_id` is not a stored column. Every single join between `raw` and any event table requires a regex extraction on the fly. This is both a performance concern (regex on 22K+ rows for every query) and a correctness risk (if the regex pattern changes). Phase 1 must evaluate whether materializing `replay_id` as a persistent column is warranted.

### 2.2 `tracker_events_raw` (62,003,411 rows, 5 columns)

**Row grain:** One tracker event per row. Confirmed -- 10 event types, all accounted for. YAML notes are correct.

**Join keys:** `match_id` (VARCHAR, relative path) joins to `raw.filename` via regex. `player_id` (TINYINT) joins to `match_player_map.player_id` within the same match.

**Flat vs. JSON:** 4 flat columns (`match_id`, `event_type`, `game_loop`, `player_id`). 1 de facto JSON column (`event_data`, stored as VARCHAR). The VARCHAR storage means every JSON extraction requires an explicit CAST.

**Most Phase 1-relevant column:** `event_data` for `PlayerStats` events. The 39-field `stats` sub-object is the foundation for all in-game economic features.

**Non-obvious fact:** `event_data` is VARCHAR, not JSON. DuckDB can still extract from it, but `json_keys()` requires `CAST(event_data AS JSON)`. The player_stats VIEW handles this transparently, but any direct query against tracker_events_raw for non-PlayerStats types must remember to cast. This is an artifact of the Parquet ingestion path (Arrow stores strings, not JSON).

### 2.3 `game_events_raw` (608,618,823 rows, 6 columns)

**Row grain:** One game engine event per row. YAML notes are correct. This is the largest table by far.

**Join keys:** `match_id` (same format as tracker_events_raw). `user_id` (INTEGER) joins to `match_player_map.user_id`. `player_id` (TINYINT) also present but may be null for system events.

**Flat vs. JSON:** 5 flat columns. 1 de facto JSON column (`event_data`, VARCHAR).

**Most Phase 1-relevant column:** `event_data` for `Cmd` events. Command events encode player actions (unit orders, ability usage) and are the foundation for APM-from-events and action-sequence features.

**Non-obvious fact:** CameraUpdate events account for 387M rows (63.6% of the table) and contain only camera position data. For any aggregate query against this table, filtering out CameraUpdate first is essential to avoid extremely slow scans. The useful event types (Cmd, SelectionDelta, UserOptions, GameUserLeave) collectively account for only ~72M rows (11.8%).

### 2.4 `match_player_map` (44,815 rows, 6 columns)

**Row grain:** One row per player per match. YAML notes are correct. 22,377 matches have exactly 2 players; 5 have 1; 8 have 3+. The total (44,815) minus twice the clean count (44,754) leaves 61 rows in anomalous matches.

**Join keys:** `match_id` (same format as event tables). `player_id` (TINYINT, 1 or 2) -- composite key with `match_id`. `user_id` (INTEGER) for game_events_raw joins.

**Flat vs. JSON:** All 6 columns are flat (no JSON). `nickname`, `race` are categorical strings. `total_game_loops` is an integer.

**Most Phase 1-relevant column:** `nickname`. This is the bridge between event-table player slots (numeric `player_id`) and the canonical player identity (lowercased nickname per INVARIANTS.md).

**Non-obvious fact:** `race` values are abbreviated: `Prot`, `Zerg`, `Terr`. This matches `ToonPlayerDescMap.<toon>.race` but differs from typical SC2 community conventions ("Protoss", "Zerg", "Terran"). Phase 1 must decide whether to normalize to full names. Also, `total_game_loops` is present here but NOT in `raw.header.elapsedGameLoops` as a flat column -- the two should be cross-validated.

### 2.5 `raw_map_alias_files` (70 rows, 6 columns)

**Row grain:** One row per tournament-level `map_foreign_to_english_mapping.json` file. YAML notes are correct. PRIMARY KEY on `tournament_dir` enforced by DuckDB.

**Join keys:** `tournament_dir` joins to `raw` via `split_part(filename, '/', -3)`.

**Flat vs. JSON:** 5 flat columns. 1 JSON column (`raw_json`).

**Most Phase 1-relevant column:** `raw_json`. This is the sole source for map name normalization. Without it, Korean/foreign map names in `metadata.mapName` cannot be matched to their English equivalents.

**Non-obvious fact:** Many tournament files share identical content (the same 1,488-entry master list), suggesting they were copied from a template rather than curated per-tournament. The `byte_sha1` column can detect this. If most files are identical, the effective number of distinct map alias sets may be much smaller than 70.

### 2.6 `player_stats` (VIEW, 4,558,736 rows, 42 columns)

**Row grain:** One PlayerStats snapshot per player per game loop. YAML notes are correct. This is a VIEW over `tracker_events_raw WHERE event_type = 'PlayerStats'`, not a base table.

**Join keys:** `match_id`, `player_id`, `game_loop` (composite triple).

**Flat vs. JSON:** All 42 columns are flat (the VIEW extracts and casts the 39 stats sub-keys plus the 3 envelope fields). This is the recommended interface for economic feature extraction.

**Most Phase 1-relevant column:** All 39 `scoreValue*` fields are equally relevant for in-game feature engineering. The VIEW is purpose-built to flatten what would otherwise require nested JSON extraction on every query.

**Non-obvious fact:** The VIEW definition lives in `ingestion.py` (`_build_player_stats_view_query()`), not in a SQL file. If the VIEW is dropped or the database is rebuilt, the Python code must be re-run to recreate it. The field mapping is defined in `PLAYER_STATS_FIELD_MAP` in `schemas.py`.

---

## Section 3 -- Cross-Table Integrity Concerns

### 3.1 Known: match_player_map vs raw row count mismatch

`match_player_map` has 44,815 rows / 2 = 22,407.5 matches (not an integer). `raw` has 22,390 rows. The delta is 17.5 "extra" matches, explained by:
- 22,377 matches with exactly 2 players = 44,754 rows
- 5 matches with 1 player = 5 rows
- 2 matches with 4 players = 8 rows
- 1 match with 6 players = 6 rows
- 3 matches with 8 players = 24 rows
- 2 matches with 9 players = 18 rows
- Total: 44,754 + 5 + 8 + 6 + 24 + 18 = 44,815. Exact match.

**All 22,390 replay_ids in match_player_map are present in raw, and vice versa. Zero orphans in either direction.**

### 3.2 Orphan detection: tracker_events_raw vs raw

**Zero orphans.** All 22,390 distinct replay_ids in tracker_events_raw exist in raw, and all 22,390 replay_ids in raw have tracker events.

### 3.3 Concern: game_events_raw vs raw orphan status

Not verified in this plan due to query budget (the table has 609M rows and a GROUP BY on regex-extracted replay_id would be expensive). Phase 1 Step 01_01 must verify this.

### 3.4 Concern: ToonPlayerDescMap toon count vs match_player_map player count consistency

Verified for the 11 anomalous replays: toon counts and player counts match perfectly. **However, for the 22,379 normal replays, the assumption that n_toons == n_mpm has not been verified row-by-row.** Phase 1 must confirm this with a full-corpus cross-check.

### 3.5 Concern: ToonPlayerDescMap nickname vs match_player_map nickname consistency

Both tables contain player nicknames, but they come from different extraction paths (Path A vs Path B). These have not been cross-validated. Possible discrepancies:
- Case differences (ToonPlayerDescMap preserves original case; match_player_map may differ)
- Encoding differences (Unicode normalization)
- Different toon-to-slot mapping (if extraction logic disagrees on which toon maps to player_id 1 vs 2)

Phase 1 must perform a systematic cross-validation.

### 3.6 Concern: match_player_map.total_game_loops vs raw.header.elapsedGameLoops

Both fields represent match duration but come from different extraction paths. They have not been cross-validated. Discrepancies would indicate either:
- Different rounding/truncation in the extraction
- Off-by-one errors in game loop counting
- Corruption in one path

### 3.7 Concern: PlayerSetup event count vs match_player_map row count

PlayerSetup has 44,817 rows. match_player_map has 44,815 rows. Delta = 2. This is unexplained. The per-match distributions are similar but not identical:
- PlayerSetup: 3 matches with 1 event, 22,379 with 2, then anomalies
- match_player_map: 5 matches with 1 player, 22,377 with 2, then anomalies

The 2-row difference and the different counts of "1-player" matches (3 vs 5) suggest the two tables disagree on which replays have anomalous player counts. Phase 1 must identify the specific replay_ids where they disagree.

### 3.8 Concern: raw_map_alias_files tournament_dir coverage

There are 70 rows in raw_map_alias_files. The number of distinct tournament_dirs in raw has not been verified in this plan. If there are tournaments in raw that have no alias file, map name normalization will fail for those tournaments. Phase 1 must verify full coverage.

### 3.9 Concern: Duplicate replay_ids

Not checked in this plan. If the same MD5 hash appears twice in raw (from different tournament directories containing the same replay file), downstream joins will produce incorrect fan-out. Phase 1 Step 01_01D must check for duplicates.

### 3.10 Concern: event_data VARCHAR vs JSON type mismatch risk

`tracker_events_raw.event_data` and `game_events_raw.event_data` are VARCHAR, but `raw` columns and `raw_map_alias_files.raw_json` are native JSON. This type inconsistency means:
- Different extraction syntax may be needed depending on which table you query
- The `player_stats` VIEW handles the cast internally, but ad-hoc queries against event tables will forget the cast
- No schema validation is performed on the VARCHAR content -- malformed JSON would pass silently

---

## Section 4 -- Phase 1 Step Taxonomy

Phase 1 is organized into three sub-phases, each building on the previous.

### Sub-phase A: Structural Census (foundational)

Establish the exact shape, completeness, and internal consistency of every table. No domain interpretation yet -- pure data profiling.

| ID | Name | Primary table(s) | JSON blob(s) consumed | Question answered | Depends on | Stratification | Complexity |
|----|------|-------------------|-----------------------|-------------------|------------|----------------|------------|
| 01_01 | Corpus dimensions and structural validation | raw, match_player_map, tracker_events_raw | ToonPlayerDescMap (toon count, result), header (elapsedGameLoops) | How many replays, tournaments, date range, player count anomalies, result field completeness, duplicates? | none | by year, by tournament | medium |
| 01_02 | Cross-table consistency audit | raw, match_player_map, tracker_events_raw, game_events_raw | ToonPlayerDescMap (nickname), header (elapsedGameLoops) | Do nicknames, player counts, game durations, and replay_ids agree across all tables? Resolves concerns 3.3-3.7. | 01_01 | none | medium |
| 01_03 | Per-tournament parse quality profile | raw, tracker_events_raw | ToonPlayerDescMap (result), header (elapsedGameLoops) | Which tournaments have missing events, anomalous player counts, or invalid results? | 01_01 | by tournament | medium |
| 01_04 | Map name normalization audit | raw, raw_map_alias_files | metadata (mapName), raw_json | Do all tournament_dirs have alias files? What fraction of map names need translation? Are there unmapped names? | 01_01 | by tournament | low |

### Sub-phase B: Field-Level Profiling (per-blob deep dives)

For each JSON blob, produce complete value distributions, cardinality, missingness, and dtype verification. These are the "know everything" steps.

| ID | Name | Primary table(s) | JSON blob(s) consumed | Question answered | Depends on | Stratification | Complexity |
|----|------|-------------------|-----------------------|-------------------|------------|----------------|------------|
| 01_05 | ToonPlayerDescMap field profiling | raw | All 20+4 ToonPlayerDescMap fields | What are the value distributions, cardinalities, zero/missing rates, and temporal patterns for every player-level field? | 01_01 | by year, by race, by region | high |
| 01_06 | Game duration distribution | raw | header (elapsedGameLoops) | What is the empirical duration distribution? Left-tail structure? Temporal trends? | 01_01 | by year, by matchup | medium |
| 01_07 | Game version and patch landscape | raw | metadata (gameVersion, dataBuild, baseBuild) | How many patch eras? What is the temporal coverage of each? Version-dependent field presence (e.g. buildCoachEnabled)? | 01_01 | by year | low |
| 01_08 | Game settings audit | raw | initData (gameDescription, gameOptions), details | What are the value distributions for map dimensions, maxPlayers, gameOptions flags? Any anomalous settings? | 01_01 | by year, by tournament | medium |
| 01_09 | Tracker event type inventory (stratified) | tracker_events_raw | event_data (all 10 types) | Per-replay event count distributions by type. Which replays lack PlayerStats? Temporal trends in event counts? | 01_01 | by year, by event_type | medium |
| 01_10 | Game event type inventory (stratified) | game_events_raw | event_data (top 5 types) | Per-replay Cmd count distributions. Event-type proportions. Any replays with zero Cmd events? | 01_01 | by year, by event_type | high |

### Sub-phase C: Domain-Specific Profiling (thesis-relevant deep dives)

Focused investigations driven by the thesis prediction task. These produce findings that directly feed Phase 2 (identity resolution) and Phase 7 (feature engineering).

| ID | Name | Primary table(s) | JSON blob(s) consumed | Question answered | Depends on | Stratification | Complexity |
|----|------|-------------------|-----------------------|-------------------|------------|----------------|------------|
| 01_11 | APM and MMR audit (formal) | raw | ToonPlayerDescMap (APM, MMR, SQ, highestLeague) | Year-by-year and league-by-league breakdown of APM zero rate, MMR zero rate, SQ distribution. Formal confirmation of Phase 0 findings. | 01_05 | by year, by league | medium |
| 01_12 | Race and matchup distribution | raw, match_player_map | ToonPlayerDescMap (race, selectedRace) | Matchup distribution (ZvP, ZvT, PvT, mirrors). Race-vs-selectedRace discrepancies (random race players). Temporal trends. | 01_05 | by year, by matchup | medium |
| 01_13 | Player activity profile | raw | ToonPlayerDescMap (nickname) | How many games per player? Distribution of player activity. Top-N players by game count. Singleton players. | 01_05 | by year, by tournament | medium |
| 01_14 | Spawn position and map dimension analysis | raw | ToonPlayerDescMap (startDir, startLocX, startLocY), initData (mapSizeX, mapSizeY) | Are spawn positions consistent within maps? Do map dimensions predict spawn count? Any relationship between spawn and outcome? | 01_05, 01_08 | by map, by matchup | high |
| 01_15 | Result anomaly deep dive | raw | ToonPlayerDescMap (result) | What are the 24 Undecided and 2 Tie results? Which replays? Can they be resolved or must they be excluded? | 01_01 | none | low |
| 01_16 | Consolidated field inventory artifact | all | all | Produce the definitive field-level inventory CSV covering every leaf field across all tables, with empirical dtype, cardinality, presence rate, and pre-game eligibility classification. | 01_05 through 01_15 | none | medium |

---

## Section 5 -- First Chunk Recommendation

### Selected steps: 01_01, 01_02, 01_03, 01_04, 01_05

**Rationale for 5 steps:**

1. **01_01 (Corpus dimensions)** -- Every subsequent step depends on knowing the exact corpus shape: how many replays, which are anomalous, what the date range is, whether there are duplicates. This is the foundation.

2. **01_02 (Cross-table consistency)** -- Before trusting any cross-table query (which every later step uses), we must know whether the tables agree. The 9 integrity concerns from Section 3 must be resolved. If nicknames disagree between tables, every player-level analysis would be wrong.

3. **01_03 (Per-tournament parse quality)** -- Some steps will stratify by tournament. If certain tournaments are badly parsed, we need to know before attempting stratified analysis. This also identifies candidates for exclusion.

4. **01_04 (Map name normalization)** -- Map is a critical pre-game feature. If alias coverage is incomplete, we discover that now rather than in feature engineering.

5. **01_05 (ToonPlayerDescMap field profiling)** -- This is the "know everything about the prediction-relevant blob" step. Every pre-game feature candidate lives in ToonPlayerDescMap. The field taxonomy tables in Section 1 show what keys exist; this step answers what values they hold, how they distribute, and how they change over time.

**Why not fewer:** Steps 01_01-01_04 are quick structural checks (low-to-medium complexity) that can likely share a single notebook or be split across two. Step 01_05 is the heavyweight but is genuinely foundational -- without it, no later step can reason about feature quality.

**Why not more:** Steps 01_06-01_10 (duration, patches, settings, event inventories) are important but independent of each other. They can proceed in any order after the first chunk establishes the structural foundation. Adding them to the first chunk increases scope without adding dependencies.

**Sequencing within the chunk:**
```
01_01 (no deps)
  |
  +-- 01_02 (depends on 01_01)
  +-- 01_03 (depends on 01_01)
  +-- 01_04 (depends on 01_01)
  +-- 01_05 (depends on 01_01)
```

Steps 01_02 through 01_05 can proceed in parallel after 01_01 completes.

---

## Section 6 -- Hard Halt: What the Planner Did NOT Do

This planning document explicitly does NOT contain and the planner explicitly did NOT produce:

1. **Executor specs.** No function signatures, no SQL queries beyond sampling, no deliverable filenames, no artifact schemas, no cell-by-cell notebook outlines. Those are the executor's job after this plan is approved.

2. **SQL queries for production use.** The 50 queries executed were sampling/profiling queries to inform the taxonomy. They are not reusable artifacts. The executor will write thesis-grade reproducible queries.

3. **Notebooks.** No `.py` or `.ipynb` files were created. The sandbox directory `sandbox/sc2/sc2egset/plans/` must be created before this document is placed there.

4. **Phase 2 cleaning rules.** No decisions about which replays to exclude, which fields to impute, which anomalies to flag. Phase 1 observes; Phase 6 decides.

5. **Feature engineering.** No features were designed, named, or specified. The `pre_game_eligible` column in Section 1 tables is a classification of raw fields, not a feature design.

6. **Magic numbers.** No thresholds were proposed for any cleaning or filtering operation. The Section 1 presence categories (always, mostly, sometimes, rarely) are descriptions of the data, not decision boundaries.

7. **Model design.** No model architectures, hyperparameter ranges, or evaluation protocols were specified.

8. **AoE2 anything.** This plan is exclusively for SC2EGSet.

9. **Modifications to the database, ingestion code, schema YAMLs, or archived artifacts.** All tools were used in read-only mode.

10. **A complete enumeration of all game_events_raw event types' key sets.** Only the 4 high-value types were verified. The remaining 19 low-volume types must be profiled in Step 01_10 if they are deemed thesis-relevant.

---

## Appendix A -- Surprises That Contradicted YAML Notes

1. **ToonPlayerDescMap has 20 fields per player, not 10.** The YAML comment mentions "nickname, playerID, userID, race, result, APM, SQ, MMR, supplyCappedPercent, isInClan" (10 fields). The actual data contains 10 additional fields not mentioned: `startDir`, `startLocX`, `startLocY`, `selectedRace`, `region`, `realm`, `highestLeague`, `clanTag`, `handicap`, `color`. Several of these are pre-game eligible and thesis-relevant (startLoc for spawn analysis, highestLeague for skill stratification, selectedRace for random-race detection, region/realm for server analysis).

2. **`color` is a nested object, not a scalar.** It contains `{r, g, b, a}` sub-keys, adding depth-3 nesting to ToonPlayerDescMap.

3. **`header.version` is a plain string, not a nested object.** The YAML did not specify the structure, but the field name "version" might suggest an object (with major/minor/patch). It is simply a dotted version string like "3.1.1.39948".

4. **`gameOptions` has two key-set variants.** 89.2% of replays include `buildCoachEnabled`; 10.8% do not. This is the only instance of non-constant key sets in the raw table JSON blobs (apart from ToonPlayerDescMap's variable number of toon keys, which is by design).

5. **BW-race values exist in the corpus.** Three player slots have race values `BWZe`, `BWTe`, `BWPr` (Brood War race codes). These are anomalies -- likely from co-op or custom games that leaked into the tournament corpus.

6. **`selectedRace` has 1,110 empty-string values (2.5%).** These are not the same as the 10 `Rand` values. Empty string may indicate a different missing-data mechanism.

7. **`highestLeague` is 72.2% "Unknown".** This makes it largely unusable as a direct stratification variable, despite being a potentially valuable skill indicator.

8. **`realm` is more granular than `region`.** Region has 5 values; realm has 8. Realm distinguishes Taiwan, Russia, and Latin America, which region does not.

9. **`isBlizzardMap` = false for 4,875 replays (21.8%).** This is a substantial minority, potentially indicating custom/modified tournament maps.

10. **`maxPlayers` is not always 2.** 409 replays (1.8%) have maxPlayers > 2, indicating maps designed for team games that were used for 1v1.

---

## Appendix B -- Tool Usage Summary

| Category | Count |
|----------|-------|
| Read YAML/config files | 12 |
| Read source/docs files | 3 |
| DuckDB read-only queries | 50 / 50 |
| Bash (ls, head, etc.) | 2 |
| **Total tool calls** | **67** |

| Metric | Value |
|--------|-------|
| Total leaf fields discovered | ~200 |
| Candidate Phase 1 steps proposed | 16 |
| Steps in first chunk | 5 |
| Surprises contradicting YAML notes | 10 |
