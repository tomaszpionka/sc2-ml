---
category: C
branch: chore/raw-schema-docs
date: 2026-04-14
planner_model: claude-sonnet-4-6
critique_required: false
---

# Plan: Raw table schema YAML documentation

## Scope

Create YAML schema documentation files for every `*_raw` DuckDB table (and
view) across all three datasets. These are static documentation artefacts —
not runtime code — describing column names, DuckDB types, provenance, and
applicable invariants.

**Target path:** `src/rts_predict/games/<game>/datasets/<dataset>/data/db/schemas/raw/`

No existing schema templates or `schemas/raw/` directories exist. All paths
must be created. Column types are sourced from `parquet_schema()` live queries
and ingestion module DDL (ground truth), not from prior documentation.

---

## YAML template

One file per table. Filename = `<table_name>.yaml`.

```yaml
# Schema: <table_name>
# Dataset: <dataset> | Game: <game>
# Generated: YYYY-MM-DD | Source step: <step>

table: <table_name>
dataset: <dataset>
game: <game>
object_type: table   # or: view
step: <step>         # pipeline step that creates this object
row_count: <N>       # from artifact; 0 if not yet materialised

columns:
  - name: <col>
    type: <DUCKDB_TYPE>   # DuckDB runtime type (after read options applied)
    nullable: true|false
    description: "<one line>"
    notes: "<optional: pre/post-game, invariant ref, known quirk>"

provenance:
  source_files_pattern: "<glob relative to dataset root>"
  duckdb_read_function: read_parquet | read_csv | read_json_auto
  duckdb_read_options:
    union_by_name: true
    filename: true
    binary_as_string: true   # include only if applicable
  ingestion_module: "src/rts_predict/games/<game>/datasets/<dataset>/ingestion.py"
  ingestion_function: <function_name>
  notes: "<optional: memory notes, batch strategy, etc.>"

invariants:
  - id: I7
    description: "Provenance: filename column present and never dropped."
  - id: I10
    description: "Relative filename: no absolute paths in filename column."
```

---

## T01 — sc2egset (6 files: 3 tables + 3 views)

**Dir:** `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/`

### `replays_meta_raw.yaml`

```yaml
table: replays_meta_raw
dataset: sc2egset
game: sc2
object_type: table
step: 01_02_02
row_count: 22390

columns:
  - name: filename
    type: VARCHAR
    nullable: false
    description: Replay file path relative to raw_dir (substr-stripped during ingestion).
    notes: "Invariant I10."
  - name: details
    type: "STRUCT(gameSpeed VARCHAR, isBlizzardMap BOOLEAN, timeUTC VARCHAR)"
    nullable: true
    description: Game details struct — speed, map origin, UTC timestamp.
  - name: header
    type: "STRUCT(elapsedGameLoops BIGINT, version VARCHAR)"
    nullable: true
    description: Replay header — elapsed loops and protocol version.
  - name: initData
    type: "STRUCT(gameDescription STRUCT(gameOptions STRUCT(...), gameSpeed VARCHAR, isBlizzardMap BOOLEAN, mapAuthorName VARCHAR, mapFileSyncChecksum BIGINT, mapSizeX BIGINT, mapSizeY BIGINT, maxPlayers BIGINT))"
    nullable: true
    description: Game initialisation data — options, map metadata, player limits.
  - name: metadata
    type: "STRUCT(baseBuild VARCHAR, dataBuild VARCHAR, gameVersion VARCHAR, mapName VARCHAR)"
    nullable: true
    description: Build versions and map name.
  - name: ToonPlayerDescMap
    type: VARCHAR
    nullable: true
    description: JSON text blob of player descriptions keyed by toon ID. Stored as VARCHAR because keys are dynamic per-replay toon IDs that cannot be unioned as STRUCTs.
  - name: gameEventsErr
    type: BOOLEAN
    nullable: true
    description: Whether game event extraction encountered errors.
  - name: messageEventsErr
    type: BOOLEAN
    nullable: true
    description: Whether message event extraction encountered errors.
  - name: trackerEvtsErr
    type: BOOLEAN
    nullable: true
    description: Whether tracker event extraction encountered errors.

provenance:
  source_files_pattern: "data/raw/<tournament>/<tournament>_data/*.SC2Replay.json"
  duckdb_read_function: read_json_auto
  duckdb_read_options:
    union_by_name: true
    filename: true
    maximum_object_size: 167772160
  ingestion_module: "src/rts_predict/games/sc2/datasets/sc2egset/ingestion.py"
  ingestion_function: load_replays_meta_raw
  notes: >
    Loaded per-tournament (70 batches) to avoid OOM. Single CTAS over
    22,390 files peaks at 22 GB RSS. Per-tournament batching stays under 3 GB.

invariants:
  - id: I7
    description: "Provenance: filename column present and never dropped."
  - id: I10
    description: "Relative filename: no absolute paths in filename column."
```

### `replay_players_raw.yaml`

```yaml
table: replay_players_raw
dataset: sc2egset
game: sc2
object_type: table
step: 01_02_02
row_count: 44817

columns:
  - name: filename
    type: VARCHAR
    nullable: false
    description: Replay file path relative to raw_dir.
    notes: "Invariant I10."
  - name: toon_id
    type: VARCHAR
    nullable: false
    description: "Player toon ID (MAP key from ToonPlayerDescMap, e.g. '3-S2-1-4842177')."
    notes: Pre-game feature.
  - name: nickname
    type: VARCHAR
    nullable: true
    description: Player in-game nickname.
    notes: Pre-game feature.
  - name: playerID
    type: INTEGER
    nullable: true
    description: Player slot ID within the replay (1 or 2 for standard 1v1).
  - name: userID
    type: BIGINT
    nullable: true
    description: Blizzard user ID.
  - name: isInClan
    type: BOOLEAN
    nullable: true
    description: Whether the player belongs to a clan.
  - name: clanTag
    type: VARCHAR
    nullable: true
    description: Clan tag string, null if not in a clan.
  - name: MMR
    type: INTEGER
    nullable: true
    description: Matchmaking Rating at game time.
    notes: Pre-game feature.
  - name: race
    type: VARCHAR
    nullable: true
    description: "Actual race played (after random resolution). Values: Terran, Protoss, Zerg."
  - name: selectedRace
    type: VARCHAR
    nullable: true
    description: Race selected in lobby (may be 'Random').
    notes: Pre-game feature.
  - name: handicap
    type: INTEGER
    nullable: true
    description: Handicap percentage (100 = no handicap).
    notes: Pre-game feature.
  - name: region
    type: VARCHAR
    nullable: true
    description: "Battle.net region (US, EU, KR, etc.)."
    notes: Pre-game feature.
  - name: realm
    type: VARCHAR
    nullable: true
    description: Battle.net realm within region.
    notes: Pre-game feature.
  - name: highestLeague
    type: VARCHAR
    nullable: true
    description: "Highest league (e.g. Grandmaster, Master, Diamond)."
    notes: Pre-game feature.
  - name: result
    type: VARCHAR
    nullable: true
    description: "Match result for this player (Win, Loss)."
    notes: Post-game. Prediction target.
  - name: APM
    type: INTEGER
    nullable: true
    description: Actions Per Minute over the full game.
    notes: Post-game feature.
  - name: SQ
    type: INTEGER
    nullable: true
    description: Spending Quotient — resource efficiency metric.
    notes: Post-game feature.
  - name: supplyCappedPercent
    type: INTEGER
    nullable: true
    description: Percentage of game time spent supply-capped.
    notes: Post-game feature.
  - name: startDir
    type: INTEGER
    nullable: true
    description: Starting direction on the map (compass encoding).
  - name: startLocX
    type: INTEGER
    nullable: true
    description: Starting location X coordinate.
  - name: startLocY
    type: INTEGER
    nullable: true
    description: Starting location Y coordinate.
  - name: color_a
    type: INTEGER
    nullable: true
    description: Player colour alpha channel.
  - name: color_b
    type: INTEGER
    nullable: true
    description: Player colour blue channel.
  - name: color_g
    type: INTEGER
    nullable: true
    description: Player colour green channel.
  - name: color_r
    type: INTEGER
    nullable: true
    description: Player colour red channel.

provenance:
  source_files_pattern: "data/raw/<tournament>/<tournament>_data/*.SC2Replay.json"
  extraction_method: >
    Python-side extraction from ToonPlayerDescMap JSON blobs in replays_meta_raw.
    Rows batch-inserted via executemany().
  ingestion_module: "src/rts_predict/games/sc2/datasets/sc2egset/ingestion.py"
  ingestion_function: load_replay_players_raw

invariants:
  - id: I7
    description: "Provenance: filename column present."
  - id: I10
    description: "Relative filename: no absolute paths."
```

### `map_aliases_raw.yaml`

```yaml
table: map_aliases_raw
dataset: sc2egset
game: sc2
object_type: table
step: 01_02_02
row_count: 104160

columns:
  - name: tournament
    type: VARCHAR
    nullable: false
    description: Tournament directory name (provenance for which tournament this entry belongs to).
  - name: foreign_name
    type: VARCHAR
    nullable: false
    description: Map name in the original (non-English) language.
  - name: english_name
    type: VARCHAR
    nullable: false
    description: Canonical English map name.
  - name: filename
    type: VARCHAR
    nullable: false
    description: Path to the mapping JSON file, relative to raw_dir.
    notes: "Invariant I10."

provenance:
  source_files_pattern: "data/raw/<tournament>/map_foreign_to_english_mapping.json"
  extraction_method: >
    Python-side extraction. Each of 70 tournament mapping JSONs expanded to
    (tournament, foreign_name, english_name, filename) tuples and batch-inserted.
    All 70 files are identical (1,488 keys each); all loaded for provenance.
  ingestion_module: "src/rts_predict/games/sc2/datasets/sc2egset/ingestion.py"
  ingestion_function: load_map_aliases_raw

invariants:
  - id: I7
    description: "Provenance: filename column present."
  - id: I10
    description: "Relative filename: no absolute paths."
```

### `game_events_raw.yaml`

```yaml
table: game_events_raw
dataset: sc2egset
game: sc2
object_type: view
step: 01_02_02
row_count: 608618823

columns:
  - name: filename
    type: VARCHAR
    nullable: false
    description: Replay file path relative to raw_dir.
    notes: "Invariant I10."
  - name: loop
    type: BIGINT
    nullable: false
    description: Game tick at which this event occurred.
  - name: evtTypeName
    type: VARCHAR
    nullable: false
    description: >
      Event type name. Top types: CameraUpdate (387M, 63.7%), ControlGroupUpdate
      (69M), CommandManagerState (44M), SelectionDelta (41M), Cmd (31M).
  - name: event_data
    type: VARCHAR
    nullable: false
    description: Full event payload serialised as JSON VARCHAR.

provenance:
  source_files_pattern: "data/db/events/gameEvents/batch_*.parquet"
  duckdb_read_function: read_parquet
  notes: >
    View, not table — Parquet files are authoritative; no data duplicated in DuckDB.
    Events extracted by extract_events_to_parquet() as zstd-compressed Parquet batches.
  ingestion_module: "src/rts_predict/games/sc2/datasets/sc2egset/ingestion.py"
  ingestion_function: load_event_views

invariants:
  - id: I7
    description: "Provenance: filename column present."
  - id: I10
    description: "Relative filename: no absolute paths."
```

### `tracker_events_raw.yaml`

```yaml
table: tracker_events_raw
dataset: sc2egset
game: sc2
object_type: view
step: 01_02_02
row_count: 62003411

columns:
  - name: filename
    type: VARCHAR
    nullable: false
    description: Replay file path relative to raw_dir.
    notes: "Invariant I10."
  - name: loop
    type: BIGINT
    nullable: false
    description: Game tick at which this event occurred.
  - name: evtTypeName
    type: VARCHAR
    nullable: false
    description: >
      Event type name. Top types: UnitBorn (22M), UnitDied (16M),
      UnitTypeChange (11M), PlayerStats (4.6M).
  - name: event_data
    type: VARCHAR
    nullable: false
    description: Full event payload serialised as JSON VARCHAR.

provenance:
  source_files_pattern: "data/db/events/trackerEvents/batch_*.parquet"
  duckdb_read_function: read_parquet
  notes: Same extraction pipeline as game_events_raw.
  ingestion_module: "src/rts_predict/games/sc2/datasets/sc2egset/ingestion.py"
  ingestion_function: load_event_views

invariants:
  - id: I7
    description: "Provenance: filename column present."
  - id: I10
    description: "Relative filename: no absolute paths."
```

### `message_events_raw.yaml`

```yaml
table: message_events_raw
dataset: sc2egset
game: sc2
object_type: view
step: 01_02_02
row_count: 52167

columns:
  - name: filename
    type: VARCHAR
    nullable: false
    description: Replay file path relative to raw_dir.
    notes: "Invariant I10. Present in 22,260 of 22,390 replays (130 replays have no message events)."
  - name: loop
    type: BIGINT
    nullable: false
    description: Game tick at which this event occurred.
  - name: evtTypeName
    type: VARCHAR
    nullable: false
    description: "Event type name. Values: Chat (51,412), Ping (714), ReconnectNotify (41)."
  - name: event_data
    type: VARCHAR
    nullable: false
    description: Full event payload serialised as JSON VARCHAR.

provenance:
  source_files_pattern: "data/db/events/messageEvents/batch_*.parquet"
  duckdb_read_function: read_parquet
  notes: Same extraction pipeline as game_events_raw.
  ingestion_module: "src/rts_predict/games/sc2/datasets/sc2egset/ingestion.py"
  ingestion_function: load_event_views

invariants:
  - id: I7
    description: "Provenance: filename column present."
  - id: I10
    description: "Relative filename: no absolute paths."
```

**Verification T01:**
- `find src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/ -name "*.yaml" | wc -l` → 6
- Column counts: replays_meta_raw=9, replay_players_raw=25, map_aliases_raw=4, event views=4 each

---

## T02 — aoe2companion (4 files)

**Dir:** `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/`

Note: `matches_raw` not yet materialised to DuckDB (01_02_02 not yet executed).
`row_count` for matches/ratings/leaderboards/profiles set to 0 pending execution.
Column types sourced from `parquet_schema()` on actual raw files + `binary_as_string=true`
promotion (BYTE_ARRAY → VARCHAR).

### `matches_raw.yaml`

```yaml
table: matches_raw
dataset: aoe2companion
game: aoe2
object_type: table
step: 01_02_02
row_count: 0   # pending 01_02_02 execution; pre-ingestion query count: 277,099,059 rows

columns:
  # --- match identity ---
  - name: matchId
    type: INTEGER
    nullable: false
    description: Unique match identifier. Join key across tables.
    notes: "0 NULLs confirmed in 01_02_01."
  - name: started
    type: BIGINT
    nullable: true
    description: Match start Unix timestamp (seconds).
  - name: finished
    type: BIGINT
    nullable: true
    description: Match end Unix timestamp (seconds).
  # --- match configuration (VARCHAR after binary_as_string=true) ---
  - name: leaderboard
    type: VARCHAR
    nullable: true
    description: Leaderboard identifier (e.g. ranked 1v1, ranked team).
  - name: map
    type: VARCHAR
    nullable: true
    description: Map name.
  - name: server
    type: VARCHAR
    nullable: true
    description: Server/datacenter where the match was played.
  - name: privacy
    type: VARCHAR
    nullable: true
    description: Match privacy setting.
  - name: difficulty
    type: VARCHAR
    nullable: true
    description: Difficulty setting (relevant for scenarios).
  - name: startingAge
    type: VARCHAR
    nullable: true
    description: Starting age setting.
  - name: endingAge
    type: VARCHAR
    nullable: true
    description: Ending age cap setting.
  - name: gameMode
    type: VARCHAR
    nullable: true
    description: Game mode label.
  - name: mapSize
    type: VARCHAR
    nullable: true
    description: Map size category.
  - name: gameVariant
    type: VARCHAR
    nullable: true
    description: Game variant label.
  - name: resources
    type: VARCHAR
    nullable: true
    description: Starting resources setting.
  - name: speed
    type: VARCHAR
    nullable: true
    description: Game speed setting.
  - name: civilizationSet
    type: VARCHAR
    nullable: true
    description: Civilisation set restriction.
  - name: victory
    type: VARCHAR
    nullable: true
    description: Victory condition.
  - name: revealMap
    type: VARCHAR
    nullable: true
    description: Map reveal setting.
  - name: scenario
    type: VARCHAR
    nullable: true
    description: Scenario name, if applicable.
  - name: modDataset
    type: VARCHAR
    nullable: true
    description: Mod dataset identifier.
  - name: colorHex
    type: VARCHAR
    nullable: true
    description: Player colour as hex string.
  - name: status
    type: VARCHAR
    nullable: true
    description: Match status (e.g. finished, in-progress).
  - name: country
    type: VARCHAR
    nullable: true
    description: Player country code.
  - name: civ
    type: VARCHAR
    nullable: true
    description: Civilisation played.
  # --- match flags (BOOLEAN) ---
  - name: mod
    type: BOOLEAN
    nullable: true
    description: Whether a mod was active.
  - name: fullTechTree
    type: BOOLEAN
    nullable: true
    description: Full tech tree enabled.
  - name: allowCheats
    type: BOOLEAN
    nullable: true
    description: Cheats allowed.
  - name: empireWarsMode
    type: BOOLEAN
    nullable: true
    description: Empire Wars mode active.
  - name: lockSpeed
    type: BOOLEAN
    nullable: true
    description: Speed lock enabled.
  - name: lockTeams
    type: BOOLEAN
    nullable: true
    description: Team lock enabled.
  - name: hideCivs
    type: BOOLEAN
    nullable: true
    description: Civilisations hidden from opponents.
  - name: recordGame
    type: BOOLEAN
    nullable: true
    description: Game recording enabled.
  - name: regicideMode
    type: BOOLEAN
    nullable: true
    description: Regicide mode active.
  - name: sharedExploration
    type: BOOLEAN
    nullable: true
    description: Shared exploration enabled.
  - name: suddenDeathMode
    type: BOOLEAN
    nullable: true
    description: Sudden death mode active.
  - name: antiquityMode
    type: BOOLEAN
    nullable: true
    description: Antiquity mode active.
  - name: teamPositions
    type: BOOLEAN
    nullable: true
    description: Fixed team positions.
  - name: teamTogether
    type: BOOLEAN
    nullable: true
    description: Team together spawn setting.
  - name: turboMode
    type: BOOLEAN
    nullable: true
    description: Turbo mode active.
  - name: password
    type: BOOLEAN
    nullable: true
    description: Password-protected lobby.
  - name: shared
    type: BOOLEAN
    nullable: true
    description: Match shared on aoe2companion.
  - name: verified
    type: BOOLEAN
    nullable: true
    description: Match verified flag.
  # --- numeric match/player attributes ---
  - name: internalLeaderboardId
    type: INTEGER
    nullable: true
    description: Internal leaderboard numeric ID. Use alongside leaderboard VARCHAR.
  - name: population
    type: INTEGER
    nullable: true
    description: Population cap setting.
  - name: treatyLength
    type: INTEGER
    nullable: true
    description: Treaty length in minutes (0 = no treaty).
  - name: profileId
    type: INTEGER
    nullable: true
    description: Player profile ID. Join key to leaderboards_raw and profiles_raw.
    notes: "INT32 in Parquet. 0 NULLs confirmed in 01_02_01."
  - name: rating
    type: INTEGER
    nullable: true
    description: Player rating at match time.
    notes: Pre-game feature.
  - name: ratingDiff
    type: INTEGER
    nullable: true
    description: Rating change from this match.
    notes: Post-game feature.
  - name: color
    type: INTEGER
    nullable: true
    description: Player colour index.
  - name: slot
    type: INTEGER
    nullable: true
    description: Player slot number in the lobby.
  - name: team
    type: INTEGER
    nullable: true
    description: Team number this player belongs to.
  - name: speedFactor
    type: FLOAT
    nullable: true
    description: Game speed multiplier.
  # --- prediction target ---
  - name: won
    type: BOOLEAN
    nullable: true
    description: Whether this player won the match.
    notes: >
      Prediction target. 12,985,561 NULLs (4.69% of rows) — genuine API
      recording gaps, not type promotion artefacts (H1 rejected, H2 confirmed
      in 01_02_01 won-NULL root-cause investigation 2026-04-14). Spans entire
      5.7-year corpus.
  # --- provenance ---
  - name: filename
    type: VARCHAR
    nullable: false
    description: Match Parquet file path relative to raw_dir.
    notes: "Invariant I10."

provenance:
  source_files_pattern: "data/raw/matches/match-YYYY-MM-DD.parquet"
  duckdb_read_function: read_parquet
  duckdb_read_options:
    union_by_name: true
    filename: true
    binary_as_string: true
  ingestion_module: "src/rts_predict/games/aoe2/datasets/aoe2companion/ingestion.py"
  ingestion_function: load_matches_raw
  notes: >
    54 source columns (22 unannotated BYTE_ARRAY columns resolved to VARCHAR
    via binary_as_string=true). 2,073 daily files spanning 2020-08-01 to
    2026-04-04. avg_rows_per_match=3.71 indicates team-game data beyond 1v1.

invariants:
  - id: I7
    description: "Provenance: filename column present."
  - id: I10
    description: "Relative filename: no absolute paths."
```

### `ratings_raw.yaml`

```yaml
table: ratings_raw
dataset: aoe2companion
game: aoe2
object_type: table
step: 01_02_02
row_count: 0   # pending 01_02_02 execution

columns:
  - name: profile_id
    type: BIGINT
    nullable: false
    description: Player profile ID. Join key to matches_raw.profileId.
    notes: "Explicit type required — read_csv_auto infers VARCHAR at scale."
  - name: games
    type: BIGINT
    nullable: true
    description: Cumulative games played at this rating snapshot.
  - name: rating
    type: BIGINT
    nullable: true
    description: Player Elo rating at this date.
    notes: Pre-game feature for temporal rating lookups.
  - name: date
    type: TIMESTAMP
    nullable: true
    description: Date of the rating snapshot.
    notes: "Explicit type required. Temporal key for pre-game feature joins."
  - name: leaderboard_id
    type: BIGINT
    nullable: true
    description: Leaderboard numeric ID this rating belongs to.
  - name: rating_diff
    type: BIGINT
    nullable: true
    description: Rating change since previous snapshot.
  - name: season
    type: BIGINT
    nullable: true
    description: Season number.
  - name: filename
    type: VARCHAR
    nullable: false
    description: Rating CSV file path relative to raw_dir.
    notes: "Invariant I10."

provenance:
  source_files_pattern: "data/raw/ratings/rating-YYYY-MM-DD.csv"
  duckdb_read_function: read_csv
  duckdb_read_options:
    union_by_name: true
    filename: true
    dtypes: "{profile_id: BIGINT, games: BIGINT, rating: BIGINT, date: TIMESTAMP, leaderboard_id: BIGINT, rating_diff: BIGINT, season: BIGINT}"
  ingestion_module: "src/rts_predict/games/aoe2/datasets/aoe2companion/ingestion.py"
  ingestion_function: load_ratings_raw
  notes: >
    2,072 daily CSV files. read_csv_auto infers all 7 columns as VARCHAR
    at scale — explicit dtypes required. Missing file: rating-2025-07-11.csv.

invariants:
  - id: I7
    description: "Provenance: filename column present."
  - id: I10
    description: "Relative filename: no absolute paths."
```

### `leaderboards_raw.yaml`

```yaml
table: leaderboards_raw
dataset: aoe2companion
game: aoe2
object_type: table
step: 01_02_02
row_count: 0   # pending 01_02_02 execution; 01_01_01 inventory: 83 MB singleton

columns:
  - name: leaderboard
    type: VARCHAR
    nullable: true
    description: Leaderboard name/identifier (BYTE_ARRAY → VARCHAR via binary_as_string=true).
  - name: profileId
    type: INTEGER
    nullable: true
    description: Player profile ID. Join key to matches_raw.profileId.
  - name: name
    type: VARCHAR
    nullable: true
    description: Player display name.
  - name: rank
    type: INTEGER
    nullable: true
    description: Player rank on this leaderboard.
  - name: rating
    type: INTEGER
    nullable: true
    description: Player rating on this leaderboard.
  - name: lastMatchTime
    type: BIGINT
    nullable: true
    description: Unix timestamp of last match.
  - name: drops
    type: INTEGER
    nullable: true
    description: Number of drops (disconnects) recorded.
  - name: losses
    type: INTEGER
    nullable: true
    description: Total losses.
  - name: streak
    type: INTEGER
    nullable: true
    description: Current win streak (negative = losing streak).
  - name: wins
    type: INTEGER
    nullable: true
    description: Total wins.
  - name: games
    type: INTEGER
    nullable: true
    description: Total games played.
  - name: updatedAt
    type: BIGINT
    nullable: true
    description: Unix timestamp of last leaderboard entry update.
  - name: rankCountry
    type: INTEGER
    nullable: true
    description: Player rank within their country.
  - name: active
    type: BOOLEAN
    nullable: true
    description: Whether the player is currently active on this leaderboard.
  - name: season
    type: INTEGER
    nullable: true
    description: Season number for this entry.
  - name: rankLevel
    type: INTEGER
    nullable: true
    description: Rank level (numeric tier).
  - name: steamId
    type: VARCHAR
    nullable: true
    description: Player Steam ID (BYTE_ARRAY → VARCHAR via binary_as_string=true).
  - name: country
    type: VARCHAR
    nullable: true
    description: Player country code.
  - name: filename
    type: VARCHAR
    nullable: false
    description: Singleton leaderboard Parquet file path relative to raw_dir.
    notes: "Invariant I10."

provenance:
  source_files_pattern: "data/raw/leaderboards/leaderboard.parquet"
  duckdb_read_function: read_parquet
  duckdb_read_options:
    filename: true
    binary_as_string: true
  ingestion_module: "src/rts_predict/games/aoe2/datasets/aoe2companion/ingestion.py"
  ingestion_function: load_leaderboards_raw

invariants:
  - id: I7
    description: "Provenance: filename column present."
  - id: I10
    description: "Relative filename: no absolute paths."
```

### `profiles_raw.yaml`

```yaml
table: profiles_raw
dataset: aoe2companion
game: aoe2
object_type: table
step: 01_02_02
row_count: 0   # pending 01_02_02 execution; 01_01_01 inventory: 162 MB singleton

columns:
  - name: profileId
    type: INTEGER
    nullable: true
    description: Player profile ID. Primary key. Join key to matches_raw and leaderboards_raw.
  - name: steamId
    type: VARCHAR
    nullable: true
    description: Player Steam ID.
  - name: name
    type: VARCHAR
    nullable: true
    description: Player display name.
  - name: clan
    type: VARCHAR
    nullable: true
    description: Clan tag or name.
  - name: country
    type: VARCHAR
    nullable: true
    description: Player country code.
  - name: avatarhash
    type: VARCHAR
    nullable: true
    description: Avatar image hash.
  - name: sharedHistory
    type: BOOLEAN
    nullable: true
    description: Whether the player shares match history publicly.
  - name: twitchChannel
    type: VARCHAR
    nullable: true
    description: Twitch channel URL or name.
  - name: youtubeChannel
    type: VARCHAR
    nullable: true
    description: YouTube channel URL.
  - name: youtubeChannelName
    type: VARCHAR
    nullable: true
    description: YouTube channel display name.
  - name: discordId
    type: VARCHAR
    nullable: true
    description: Discord user ID.
  - name: discordName
    type: VARCHAR
    nullable: true
    description: Discord username.
  - name: discordInvitation
    type: VARCHAR
    nullable: true
    description: Discord server invitation link.
  - name: filename
    type: VARCHAR
    nullable: false
    description: Singleton profile Parquet file path relative to raw_dir.
    notes: "Invariant I10."

provenance:
  source_files_pattern: "data/raw/profiles/profile.parquet"
  duckdb_read_function: read_parquet
  duckdb_read_options:
    filename: true
    binary_as_string: true
  ingestion_module: "src/rts_predict/games/aoe2/datasets/aoe2companion/ingestion.py"
  ingestion_function: load_profiles_raw

invariants:
  - id: I7
    description: "Provenance: filename column present."
  - id: I10
    description: "Relative filename: no absolute paths."
```

**Verification T02:**
- `find src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/ -name "*.yaml" | wc -l` → 4
- Column counts: matches_raw=55, ratings_raw=8, leaderboards_raw=19, profiles_raw=14

---

## T03 — aoestats (3 files)

**Dir:** `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/`

Column types sourced from the 01_02_01 artifact DESCRIBE output (tables were
materialised as part of 01_02_01 for this dataset). Note: `profile_id` is
DOUBLE due to mixed int64/double source files — flagged in artifact.

### `matches_raw.yaml`

```yaml
table: matches_raw
dataset: aoestats
game: aoe2
object_type: table
step: 01_02_01
row_count: 30690651

columns:
  - name: map
    type: VARCHAR
    nullable: true
    description: Map name.
  - name: started_timestamp
    type: TIMESTAMP WITH TIME ZONE
    nullable: true
    description: Match start timestamp.
    notes: >
      Promoted from mixed us/ns precision Parquet types (68 files timestamp[us],
      104 files timestamp[ns]) via union_by_name. Both resolve to TIMESTAMP WITH
      TIME ZONE in DuckDB.
  - name: duration
    type: BIGINT
    nullable: true
    description: Match duration in nanoseconds (Arrow duration[ns] → BIGINT).
    notes: "Divide by 1e9 for seconds. NOT INTERVAL — DuckDB 1.5.1 maps duration[ns] to BIGINT."
  - name: irl_duration
    type: BIGINT
    nullable: true
    description: Real-world match duration in nanoseconds.
    notes: Same BIGINT nanoseconds caveat as duration.
  - name: game_id
    type: VARCHAR
    nullable: true
    description: Unique match identifier. Join key to players_raw.
  - name: avg_elo
    type: DOUBLE
    nullable: true
    description: Average Elo rating of all players in the match.
    notes: Pre-game feature.
  - name: num_players
    type: BIGINT
    nullable: true
    description: Number of players in the match.
  - name: team_0_elo
    type: DOUBLE
    nullable: true
    description: Average Elo of team 0.
    notes: Pre-game feature.
  - name: team_1_elo
    type: DOUBLE
    nullable: true
    description: Average Elo of team 1.
    notes: Pre-game feature.
  - name: replay_enhanced
    type: BOOLEAN
    nullable: true
    description: Whether the match has replay data attached.
  - name: leaderboard
    type: VARCHAR
    nullable: true
    description: Leaderboard identifier.
  - name: mirror
    type: BOOLEAN
    nullable: true
    description: Whether both players chose the same civilisation.
  - name: patch
    type: BIGINT
    nullable: true
    description: Game patch number at match time.
  - name: raw_match_type
    type: DOUBLE
    nullable: true
    description: Raw match type numeric code.
    notes: >
      Promoted from mixed int64 (106 files) / double (66 files) via
      union_by_name. No NULLs introduced by promotion.
  - name: game_type
    type: VARCHAR
    nullable: true
    description: Game type label.
  - name: game_speed
    type: VARCHAR
    nullable: true
    description: Game speed setting.
  - name: starting_age
    type: VARCHAR
    nullable: true
    description: Starting age setting.
  - name: filename
    type: VARCHAR
    nullable: true
    description: Weekly match Parquet file path relative to raw_dir.
    notes: "Invariant I10."

provenance:
  source_files_pattern: "data/raw/matches/*.parquet"
  duckdb_read_function: read_parquet
  duckdb_read_options:
    union_by_name: true
    filename: true
  ingestion_module: "src/rts_predict/games/aoe2/datasets/aoestats/ingestion.py"
  ingestion_function: load_matches_raw
  notes: >
    172 weekly files. Two variant columns with mixed Parquet types across
    files — handled by union_by_name type promotion. No NULLs introduced.

invariants:
  - id: I7
    description: "Provenance: filename column present."
  - id: I10
    description: "Relative filename: no absolute paths."
```

### `players_raw.yaml`

```yaml
table: players_raw
dataset: aoestats
game: aoe2
object_type: table
step: 01_02_01
row_count: 107627584

columns:
  - name: winner
    type: BOOLEAN
    nullable: true
    description: Whether this player won the match.
    notes: Prediction target. NULL rate not yet quantified for aoestats.
  - name: game_id
    type: VARCHAR
    nullable: true
    description: Match identifier. Join key to matches_raw.
  - name: team
    type: BIGINT
    nullable: true
    description: Team number this player belongs to.
  - name: feudal_age_uptime
    type: DOUBLE
    nullable: true
    description: Time to reach Feudal Age in seconds.
    notes: >
      93,726,448 NULLs (87% of rows) — either games that ended before Feudal
      Age or schema gap in 89 of 171 player files (null-typed → DOUBLE with
      NULL fill via union_by_name).
  - name: castle_age_uptime
    type: DOUBLE
    nullable: true
    description: Time to reach Castle Age in seconds.
    notes: 94,641,831 NULLs (88% of rows) — same cause as feudal_age_uptime.
  - name: imperial_age_uptime
    type: DOUBLE
    nullable: true
    description: Time to reach Imperial Age in seconds.
    notes: 98,468,904 NULLs (91% of rows) — same cause as feudal_age_uptime.
  - name: old_rating
    type: BIGINT
    nullable: true
    description: Player Elo rating before this match.
    notes: Pre-game feature.
  - name: new_rating
    type: BIGINT
    nullable: true
    description: Player Elo rating after this match.
    notes: Post-game feature.
  - name: match_rating_diff
    type: DOUBLE
    nullable: true
    description: Rating change from this match.
    notes: Post-game feature.
  - name: replay_summary_raw
    type: VARCHAR
    nullable: true
    description: Raw replay summary JSON string (contents TBD — investigate in 01_03).
  - name: profile_id
    type: DOUBLE
    nullable: true
    description: Player profile ID.
    notes: >
      FLAGGED: DOUBLE due to mixed int64 (135 files) / double (36 files)
      source types. Precision loss risk for IDs > 2^53. 1,185 NULLs.
      Cast to BIGINT deferred to cleaning step 01_04.
  - name: civ
    type: VARCHAR
    nullable: true
    description: Civilisation played.
    notes: Pre-game feature.
  - name: opening
    type: VARCHAR
    nullable: true
    description: Opening strategy label.
    notes: >
      92,616,290 NULLs (86% of rows) — null-typed in 89 of 171 player files.
      May represent a schema change around mid-dataset.
  - name: filename
    type: VARCHAR
    nullable: true
    description: Weekly player Parquet file path relative to raw_dir.
    notes: "Invariant I10."

provenance:
  source_files_pattern: "data/raw/players/*.parquet"
  duckdb_read_function: read_parquet
  duckdb_read_options:
    union_by_name: true
    filename: true
  ingestion_module: "src/rts_predict/games/aoe2/datasets/aoestats/ingestion.py"
  ingestion_function: load_players_raw
  notes: >
    171 weekly files. Five variant columns — profile_id, age uptimes, and
    opening all have mixed types. Missing week: 2025-11-16_2025-11-22 has
    matches but no player data.

invariants:
  - id: I7
    description: "Provenance: filename column present."
  - id: I10
    description: "Relative filename: no absolute paths."
```

### `overviews_raw.yaml`

```yaml
table: overviews_raw
dataset: aoestats
game: aoe2
object_type: table
step: 01_02_01
row_count: 1

columns:
  - name: last_updated
    type: VARCHAR
    nullable: true
    description: Timestamp string of last overview update.
  - name: total_match_count
    type: BIGINT
    nullable: true
    description: Total match count across the full dataset.
  - name: civs
    type: "STRUCT(\"name\" VARCHAR, \"value\" BIGINT)[]"
    nullable: true
    description: Civilisation play-rate distribution array.
  - name: openings
    type: "STRUCT(\"name\" VARCHAR, \"value\" BIGINT)[]"
    nullable: true
    description: Opening strategy play-rate distribution array.
  - name: patches
    type: "STRUCT(number BIGINT, \"label\" VARCHAR, release_date DATE, published BOOLEAN, url VARCHAR, description VARCHAR, total_games HUGEINT)[]"
    nullable: true
    description: Patch history array with game counts per patch.
  - name: groupings
    type: "STRUCT(\"name\" VARCHAR, \"label\" VARCHAR, elo_groupings STRUCT(\"label\" VARCHAR, \"name\" VARCHAR)[])[]"
    nullable: true
    description: Elo grouping definitions.
  - name: changelog
    type: "STRUCT(change_time TIMESTAMP, changes VARCHAR[], \"version\" VARCHAR)[]"
    nullable: true
    description: Dataset changelog entries.
  - name: tournament_stages
    type: "VARCHAR[]"
    nullable: true
    description: Tournament stage labels.
  - name: filename
    type: VARCHAR
    nullable: true
    description: Singleton overview JSON file path relative to raw_dir.
    notes: "Invariant I10."

provenance:
  source_files_pattern: "data/raw/overview/overview.json"
  duckdb_read_function: read_json_auto
  duckdb_read_options:
    filename: true
  ingestion_module: "src/rts_predict/games/aoe2/datasets/aoestats/ingestion.py"
  ingestion_function: load_overviews_raw
  notes: Singleton file (1 row). Contains nested STRUCT arrays for civ/opening distributions.

invariants:
  - id: I7
    description: "Provenance: filename column present."
  - id: I10
    description: "Relative filename: no absolute paths."
```

**Verification T03:**
- `find src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/ -name "*.yaml" | wc -l` → 3
- Column counts: matches_raw=18, players_raw=14, overviews_raw=9

---

## File manifest

| File | Action |
|------|--------|
| `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replays_meta_raw.yaml` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replay_players_raw.yaml` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/map_aliases_raw.yaml` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/game_events_raw.yaml` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/tracker_events_raw.yaml` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/message_events_raw.yaml` | Create |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/matches_raw.yaml` | Create |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/ratings_raw.yaml` | Create |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/leaderboards_raw.yaml` | Create |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/profiles_raw.yaml` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/matches_raw.yaml` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/players_raw.yaml` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/overviews_raw.yaml` | Create |

Total: 13 new YAML files across 3 datasets.

---

## Gate condition

1. All 13 YAML files exist on disk under their respective `schemas/raw/` directories
2. Each YAML file is valid YAML (`python3 -c "import yaml; yaml.safe_load(open('<path>'))"` succeeds)
3. Column counts match artifacts:
   - sc2egset: replays_meta_raw=9, replay_players_raw=25, map_aliases_raw=4, event views=4 each
   - aoe2companion: matches_raw=55, ratings_raw=8, leaderboards_raw=19, profiles_raw=14
   - aoestats: matches_raw=18, players_raw=14, overviews_raw=9
4. No Python source files modified (documentation only)
5. No test files created or modified

---

## Out of scope

- Silver/gold layer schema documentation (Steps 01_03+)
- YAML validation tooling or schema registry
- Runtime loading of these YAMLs by any Python module
- `aoe2companion/matches_raw` `row_count` population (pending 01_02_02 execution)
