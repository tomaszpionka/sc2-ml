# Step 01_01_02 — Schema Discovery: aoe2companion

**Phase:** 01 — Data Exploration  
**Pipeline Section:** 01_01 — Data Acquisition & Source Inventory  
**Dataset:** aoe2companion  
**Invariants applied:** #6, #7, #9  

## Sampling methodology

Full census for all file types.

| File type | Subdirectory | Files in dataset | Files checked | Method |
|-----------|-------------|-----------------|--------------|--------|
| Parquet | `matches/` | 2073 | 2073 | metadata-only (pyarrow.parquet.read_schema) |
| CSV | `ratings/` | 2072 | 2072 | header + 50 rows (pd.read_csv) |
| Parquet | `leaderboards/` | 1 | 1 | metadata-only |
| Parquet | `profiles/` | 1 | 1 | metadata-only |

## matches/ schema (Parquet)

**Total columns:** 54  
**Schema consistency:** True  

| Column | Type | Nullable |
|--------|------|----------|
| `matchId` | int32 | False |
| `started` | timestamp[ms, tz=UTC] | False |
| `finished` | timestamp[ms, tz=UTC] | False |
| `leaderboard` | binary | True |
| `name` | binary | True |
| `server` | binary | True |
| `internalLeaderboardId` | int32 | True |
| `privacy` | binary | True |
| `mod` | bool | True |
| `map` | binary | True |
| `difficulty` | binary | True |
| `startingAge` | binary | True |
| `fullTechTree` | bool | True |
| `allowCheats` | bool | True |
| `empireWarsMode` | bool | True |
| `endingAge` | binary | True |
| `gameMode` | binary | True |
| `lockSpeed` | bool | True |
| `lockTeams` | bool | True |
| `mapSize` | binary | True |
| `population` | int32 | True |
| `hideCivs` | bool | True |
| `recordGame` | bool | True |
| `regicideMode` | bool | True |
| `gameVariant` | binary | True |
| `resources` | binary | True |
| `sharedExploration` | bool | True |
| `speed` | binary | True |
| `speedFactor` | float | True |
| `suddenDeathMode` | bool | True |
| `antiquityMode` | bool | True |
| `civilizationSet` | binary | True |
| `teamPositions` | bool | True |
| `teamTogether` | bool | True |
| `treatyLength` | int32 | True |
| `turboMode` | bool | True |
| `victory` | binary | True |
| `revealMap` | binary | True |
| `scenario` | binary | True |
| `password` | bool | True |
| `modDataset` | binary | True |
| `profileId` | int32 | True |
| `rating` | int32 | True |
| `ratingDiff` | int32 | True |
| `color` | int32 | True |
| `colorHex` | binary | True |
| `slot` | int32 | True |
| `status` | binary | True |
| `team` | int32 | True |
| `won` | bool | True |
| `country` | binary | True |
| `shared` | bool | True |
| `verified` | bool | True |
| `civ` | binary | True |

## ratings/ schema (CSV)

**Total columns:** 7  
**Schema consistency:** True  

| Column | Type | Nullable |
|--------|------|----------|
| `profile_id` | object | False |
| `games` | object | False |
| `rating` | object | False |
| `date` | object | False |
| `leaderboard_id` | object | False |
| `rating_diff` | object | False |
| `season` | object | False |

## leaderboards/ schema (Parquet singleton)

**Total columns:** 18  

| Column | Type | Nullable |
|--------|------|----------|
| `leaderboard` | binary | False |
| `profileId` | int32 | False |
| `name` | binary | False |
| `rank` | int32 | True |
| `rating` | int32 | True |
| `lastMatchTime` | timestamp[ms, tz=UTC] | True |
| `drops` | int32 | True |
| `losses` | int32 | True |
| `streak` | int32 | True |
| `wins` | int32 | True |
| `games` | int32 | True |
| `updatedAt` | timestamp[ms, tz=UTC] | True |
| `rankCountry` | int32 | True |
| `active` | bool | True |
| `season` | int32 | True |
| `rankLevel` | int32 | True |
| `steamId` | binary | True |
| `country` | binary | True |

## profiles/ schema (Parquet singleton)

**Total columns:** 13  

| Column | Type | Nullable |
|--------|------|----------|
| `profileId` | int32 | False |
| `steamId` | binary | True |
| `name` | binary | True |
| `clan` | binary | True |
| `country` | binary | True |
| `avatarhash` | binary | True |
| `sharedHistory` | bool | True |
| `twitchChannel` | binary | True |
| `youtubeChannel` | binary | True |
| `youtubeChannelName` | binary | True |
| `discordId` | binary | True |
| `discordName` | binary | True |
| `discordInvitation` | binary | True |

## Notes

- No DuckDB type proposals in this step (deferred to ingestion design).
- Step scope: `content` (file headers/schemas).
