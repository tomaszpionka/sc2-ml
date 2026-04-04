# SC2 Replay Data — Sample & Schema Reference

Sample SC2Replay JSON file and schema documentation for each stage of the ML pipeline.

**Sample match:** sOs (Protoss, Win) vs ByuN (Terran, Loss) — Central Protocol, 2016-02-01, Korean server.

## Directory Structure

```
samples/
├── raw/
│   ├── 0e0b1a55...SC2Replay.json              # Sample replay (raw)
│   └── map_foreign_to_english_mapping.json     # Map name translations (all languages → English)
├── processed/          # Slimmed files (heavy event arrays removed)
├── process_sample.py   # Script to generate processed/ from raw/
└── README.md           # This file
```

---

## Map Translation Reference (`map_foreign_to_english_mapping.json`)

Flat JSON dictionary mapping **1,488 localized SC2 map names** to **215 canonical English names**. SC2 replays store map names in the client's display language, so the same map appears under different names depending on server region.

**Structure:** `{ "foreign_name": "english_name", ... }`

```json
{
  "16 bits EC": "16-Bit LE",
  "16비트 - 래더": "16-Bit LE",
  "16位-天梯版": "16-Bit LE",
  "16 бит РВ": "16-Bit LE",
  "Abiogénesis EE": "Abiogenesis LE",
  "Achados e Perdidos LE": "Lost and Found LE"
}
```

**Language coverage:** English, Korean, Chinese (Simplified + Traditional), Russian, Spanish, French, German, Portuguese, Polish, Italian.

**Pipeline usage:** `load_map_translations()` in `ingestion.py` scans all `*map_foreign_to_english_mapping.json` files under the replays source directory, merges them into DuckDB's `map_translation` table. The `flat_players` view in `processing.py` LEFT JOINs this table to normalize `metadata.mapName` → canonical English name. This ensures map-based features (map area, spawn distance, future map-race winrate features) are computed over consistent map identities regardless of replay client language.

---

## Stage 1: Raw JSON (pre-ingestion)

Full replay file as exported by SC2Replay parser. ~3 MB per file.
Raw data is going to be available in Downloads dir under paths as:
```
~Downloads/SC2_Replays/2016_IEM_10_Taipei  > tree .           
.
├── 2016_IEM_10_Taipei_data
│   ├── 095724b86cbca0e6da2fb8baad0d7baf.SC2Replay.json
│   ├── 0e0b1a550447f0b0a616e48224b31bd9.SC2Replay.json
│   ├── 15ad08e3ed7fc167bf455dbe3f1f7d91.SC2Replay.json
│   ├── 1a9aeda55b1c48e503b94aca122f41a5.SC2Replay.json
│   ├── 278b7a0a0b2b8ca4594d45e5b0b0ceec.SC2Replay.json
│   ├── 3813bc1121bf0b258ea224918ff6f6f7.SC2Replay.json
│   ├── 407c8d1441b9d43ae3211b3b5b9664af.SC2Replay.json
│   ├── 421a88ce218e57005a8c78f1823c8cd3.SC2Replay.json
│   ├── 45add59eb97b5ac01eac21c3749ce037.SC2Replay.json
│   ├── 6f6b057793b1d01261c76f292cc32fea.SC2Replay.json
│   ├── 74a6039ae628fda57f94e4a7d47a0acc.SC2Replay.json
│   ├── 8a1f5c840fab9326ab8eaa20536fb75a.SC2Replay.json
│   ├── a042a7cbde4d7f08bcf4b64d35109d54.SC2Replay.json
│   ├── a09e8befe4e278e317a5a4df4b96a3f4.SC2Replay.json
│   ├── a0f9b25f7126689fd31b0e000a809d14.SC2Replay.json
│   ├── a1404d2d8439fe46753186703b35f7b7.SC2Replay.json
│   ├── a1f0f8d3104439f506cc69fcf7397995.SC2Replay.json
│   ├── a277238b2907ac76ba037bcfd2a1192c.SC2Replay.json
│   ├── b09eebe96e48bebc9b3a4a149f7fb173.SC2Replay.json
│   ├── b7d07c7ef535bde3ce276bb250e06db2.SC2Replay.json
│   ├── b9411b10de82684c5a2025078373153d.SC2Replay.json
│   ├── cd9e6768a888d1f56293f463c7a64da6.SC2Replay.json
│   ├── e2355cf005004a8a59280864effdbac5.SC2Replay.json
│   ├── e8eea04e40da2df5b57fa8ca2ce3f4ea.SC2Replay.json
│   ├── ea69286365b59bd476aa8b7c3dc004a2.SC2Replay.json
│   ├── f05c515d2c490bd18063310de9806ed9.SC2Replay.json
│   ├── f07816f9b5fb1463d96848f44ac1865e.SC2Replay.json
│   ├── f0c7ed2a887a2b9a6101055f330e3a31.SC2Replay.json
│   ├── f6cb6724220bce3b7b8f354246e83a52.SC2Replay.json
│   └── fd62e9cd965be24d61aaa75b7be04b81.SC2Replay.json
├── 2016_IEM_10_Taipei_data.zip
├── 2016_IEM_10_Taipei_main_log.log
├── 2016_IEM_10_Taipei_processed_failed.log
├── 2016_IEM_10_Taipei_processed_mapping.json
├── 2016_IEM_10_Taipei_summary.json
└── map_foreign_to_english_mapping.json

2 directories, 36 files
```

Each *.SC2Replay.json file is supposed to be a single match. The file prefix such as 2016_IEM_10_Taipei_data_fd62e9cd965be24d61aaa75b7be04b81 has to be preserved to serve as unique identifier.

| Key | Type | Description |
|-----|------|-------------|
| `header` | object | `{elapsedGameLoops: int, version: str}` |
| `initData` | object | Game setup: map description, game options, map dimensions |
| `details` | object | `{gameSpeed: str, isBlizzardMap: bool, timeUTC: str}` |
| `metadata` | object | `{baseBuild: str, dataBuild: str, gameVersion: str, mapName: str}` |
| `messageEvents` | array | In-game chat messages (1 event in sample) |
| **`gameEvents`** | **array** | **Player input events — commands, camera moves, selections (~9000 events). Stripped optionally.** |
| **`trackerEvents`** | **array** | **Game state events — unit births/deaths, player stats, upgrades (~500 events). Stripped optionally.** |
| `ToonPlayerDescMap` | object | Per-player stats keyed by Battle.net toon ID (see below) |
| `gameEventsErr` | bool | Whether gameEvents parsing had errors |
| `messageEventsErr` | bool | Whether messageEvents parsing had errors |
| `trackerEvtsErr` | bool | Whether trackerEvents parsing had errors |

### ToonPlayerDescMap entry (per player)

```json
{
  "nickname": "sOs",
  "playerID": 2,
  "userID": 5,
  "SQ": 85,
  "supplyCappedPercent": 6,
  "startDir": 1,
  "startLocX": 133,
  "startLocY": 154,
  "race": "Prot",
  "selectedRace": "",
  "APM": 0,
  "MMR": 0,
  "result": "Win",
  "region": "Korea",
  "realm": "Korea",
  "highestLeague": "Unranked",
  "isInClan": false,
  "clanTag": "",
  "handicap": 100,
  "color": {"a": 255, "b": 0, "g": 66, "r": 255}
}
```

### trackerEvents types (available in raw, stripped in processed)

| Event Type | Count (sample) | Description |
|------------|---------------|-------------|
| `PlayerSetup` | 2 | Player slot assignments |
| `PlayerStats` | 97 | Periodic resource/economy snapshots (minerals, vespene, food, workers) |
| `UnitBorn` | 262 | Unit/structure creation events |
| `UnitDied` | 66 | Unit/structure destruction events |
| `UnitInit` | 36 | Unit initialization (in-progress buildings) |
| `UnitDone` | 36 | Unit/structure completion |
| `UnitTypeChange` | 14 | Morphs (e.g. Larva -> Drone) |
| `UnitPositions` | 14 | Periodic unit position snapshots |
| `Upgrade` | 1 | Research completion |

> **Note:** trackerEvents contain time-series data (PlayerStats snapshots every ~160 game loops) that could be valuable for temporal models. Currently stripped by the pipeline but preserved in `raw/` for future use.

---

## Stage 2: Slimmed JSON (post `slim_down_sc2_with_manifest`)

Heavy event arrays removed. ~2 KB per file. Produced by `process_sample.py` or the main pipeline's `slim_down_sc2_with_manifest()`.

**Remaining keys:** `header`, `initData`, `details`, `metadata`, `ToonPlayerDescMap`, `gameEventsErr`, `messageEventsErr`, `trackerEvtsErr`

See Stage 1 table for types — only `messageEvents`, `gameEvents`, and `trackerEvents` are removed.

---

## Stage 3: `flat_players` DuckDB View

One row per player per match. Created by `create_ml_views()` in `processing.py`.

| Column | Type | Source |
|--------|------|--------|
| `match_id` | VARCHAR | `raw.filename` |
| `tournament_name` | VARCHAR | Extracted from filepath (3rd-to-last segment) |
| `match_time` | TIMESTAMP | `details.timeUTC` |
| `game_loops` | INTEGER | `header.elapsedGameLoops` |
| `map_size_x` | INTEGER | `initData.gameDescription.mapSizeX` |
| `map_size_y` | INTEGER | `initData.gameDescription.mapSizeY` |
| `data_build` | VARCHAR | `metadata.dataBuild` |
| `map_name` | VARCHAR | `metadata.mapName` (translated to English via `map_translation` table) |
| `player_name` | VARCHAR | `ToonPlayerDescMap[*].nickname` (lowercased) |
| `race` | VARCHAR | `ToonPlayerDescMap[*].race` (normalized: `Terran`, `Protoss`, `Zerg`) |
| `startLocX` | INTEGER | `ToonPlayerDescMap[*].startLocX` |
| `startLocY` | INTEGER | `ToonPlayerDescMap[*].startLocY` |
| `apm` | INTEGER | `ToonPlayerDescMap[*].APM` |
| `sq` | INTEGER | `ToonPlayerDescMap[*].SQ` (Spending Quotient) |
| `supply_capped_pct` | INTEGER | `ToonPlayerDescMap[*].supplyCappedPercent` |
| `is_in_clan` | BOOLEAN | `ToonPlayerDescMap[*].isInClan` |
| `result` | VARCHAR | `Win` or `Loss` only (casters/observers excluded) |

---

## Stage 4: `matches_flat` DuckDB View

Two rows per unique match (one per player perspective). Created by self-joining `flat_players` on `match_id`.

| Column Group | Columns |
|-------------|---------|
| **Match-level** | `match_id`, `match_time`, `tournament_name`, `game_loops`, `map_size_x`, `map_size_y`, `data_build`, `map_name` |
| **Player 1 (perspective)** | `p1_name`, `p1_race`, `p1_startLocX`, `p1_startLocY`, `p1_apm`, `p1_sq`, `p1_supply_capped_pct`, `p1_is_in_clan`, `p1_result` |
| **Player 2 (opponent)** | `p2_name`, `p2_race`, `p2_startLocX`, `p2_startLocY`, `p2_apm`, `p2_sq`, `p2_supply_capped_pct`, `p2_is_in_clan` |

> `p1_result` is the only result column — p2's result is always the inverse.

---

## Stage 5: Feature-Engineered DataFrame

Final ML-ready features after ELO computation (`elo.py`) and feature engineering (`engineering.py`). All features represent pre-match knowledge only — no leakage from current-match stats.

### ELO features (from `add_elo_features`)

| Feature | Description |
|---------|-------------|
| `p1_pre_match_elo` | Player 1's ELO before this match (starts at 1500) |
| `p2_pre_match_elo` | Player 2's ELO before this match |
| `elo_diff` | `p1_pre_match_elo - p2_pre_match_elo` |
| `expected_win_prob` | P1's expected win probability from ELO formula |

### Historical rolling features (from `perform_feature_engineering`)

| Feature | Description |
|---------|-------------|
| `p{1,2}_total_games_played` | Cumulative games before this match |
| `p{1,2}_hist_mean_apm` | Historical average APM |
| `p{1,2}_hist_mean_sq` | Historical average Spending Quotient |
| `p{1,2}_hist_mean_supply_block` | Historical average supply-capped percentage |
| `p{1,2}_hist_mean_game_length` | Historical average game length (game loops) |
| `p1_hist_winrate_smooth` | Bayesian-smoothed overall win rate (C=5.0, prior=0.5) |
| `p2_hist_winrate_smooth` | Same for player 2 |
| `p1_hist_winrate_as_race_smooth` | Win rate playing as their current race |
| `p1_hist_winrate_vs_race_smooth` | Win rate against opponent's current race |

### Difference features

| Feature | Description |
|---------|-------------|
| `diff_hist_apm` | `p1_hist_mean_apm - p2_hist_mean_apm` |
| `diff_hist_sq` | `p1_hist_mean_sq - p2_hist_mean_sq` |
| `diff_hist_supply_block` | `p1 - p2` historical supply block rate |
| `diff_hist_game_length` | `p1 - p2` preferred game length |
| `diff_experience` | `p1 - p2` total games played |

### Pre-match map features

| Feature | Description |
|---------|-------------|
| `spawn_distance` | Euclidean distance between spawn locations |
| `map_area` | `map_size_x * map_size_y` |

### One-hot encoded columns

Race columns are one-hot encoded via `pd.get_dummies`: `p1_race_Terr`, `p1_race_Prot`, `p1_race_Zerg`, `p2_race_Terr`, `p2_race_Prot`, `p2_race_Zerg` (exact columns depend on races present in data).

### Retained metadata (not used as ML features)

| Column | Purpose |
|--------|---------|
| `match_id` | Join key (dropped before training) |
| `match_time` | Temporal ordering (dropped before training) |
| `p1_name`, `p2_name` | Player identification for GNN (dropped before classical training) |
| `data_build` | Game patch version (kept for per-patch analysis) |
| `target` | Binary label: 1 = p1 wins, 0 = p1 loses (dropped from X, used as y) |

### Columns dropped for leakage prevention

These current-match stats are removed because they are not known before the match:

`p1_result`, `p1_startLocX`, `p1_startLocY`, `p2_startLocX`, `p2_startLocY`, `p1_apm`, `p2_apm`, `p1_sq`, `p2_sq`, `p1_supply_capped_pct`, `p2_supply_capped_pct`, `game_loops`, `p2_target_perspective`, `map_size_x`, `map_size_y`, `tournament_name`, `map_name`

> **Note:** `spawn_distance` and `map_area` are derived from dropped columns but computed before the drop. Start locations are known pre-match (map spawn points); raw coordinates are dropped because they are map-specific and non-generalizable.
