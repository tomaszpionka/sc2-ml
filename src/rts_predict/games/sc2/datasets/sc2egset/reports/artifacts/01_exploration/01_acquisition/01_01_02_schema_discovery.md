# Step 01_01_02 — Schema Discovery: sc2egset

**Phase:** 01 — Data Exploration  
**Pipeline Section:** 01_01 — Data Acquisition & Source Inventory  
**Dataset:** sc2egset  
**Invariants applied:** #6, #7, #9  

## Sampling methodology

| Parameter | Value |
|-----------|-------|
| Strategy | systematic temporal stratification (1 file/dir for root schema, 3 files/dir for keypaths) |
| Directories | 70 |
| Files selected (root schema) | 70 |
| Files selected (keypaths) | 210 |
| Total files in dataset | 22390 |

File selection is deterministic: first N files alphabetically per `_data/` directory.

## Root-level key catalog (JSON schema)

| Key | Observed types | Nullable | Frequency / Total |
|-----|----------------|----------|-------------------|
| `ToonPlayerDescMap` | dict | False | 70 / 70 |
| `details` | dict | False | 70 / 70 |
| `gameEvents` | list | False | 70 / 70 |
| `gameEventsErr` | bool | False | 70 / 70 |
| `header` | dict | False | 70 / 70 |
| `initData` | dict | False | 70 / 70 |
| `messageEvents` | list | False | 70 / 70 |
| `messageEventsErr` | bool | False | 70 / 70 |
| `metadata` | dict | False | 70 / 70 |
| `trackerEvents` | list | False | 70 / 70 |
| `trackerEvtsErr` | bool | False | 70 / 70 |

## Full keypath tree

Total unique keypaths: 7350

```
ToonPlayerDescMap.1-S2-1-10010469.APM
ToonPlayerDescMap.1-S2-1-10010469.MMR
ToonPlayerDescMap.1-S2-1-10010469.SQ
ToonPlayerDescMap.1-S2-1-10010469.clanTag
ToonPlayerDescMap.1-S2-1-10010469.color.a
ToonPlayerDescMap.1-S2-1-10010469.color.b
ToonPlayerDescMap.1-S2-1-10010469.color.g
ToonPlayerDescMap.1-S2-1-10010469.color.r
ToonPlayerDescMap.1-S2-1-10010469.handicap
ToonPlayerDescMap.1-S2-1-10010469.highestLeague
ToonPlayerDescMap.1-S2-1-10010469.isInClan
ToonPlayerDescMap.1-S2-1-10010469.nickname
ToonPlayerDescMap.1-S2-1-10010469.playerID
ToonPlayerDescMap.1-S2-1-10010469.race
ToonPlayerDescMap.1-S2-1-10010469.realm
ToonPlayerDescMap.1-S2-1-10010469.region
ToonPlayerDescMap.1-S2-1-10010469.result
ToonPlayerDescMap.1-S2-1-10010469.selectedRace
ToonPlayerDescMap.1-S2-1-10010469.startDir
ToonPlayerDescMap.1-S2-1-10010469.startLocX
ToonPlayerDescMap.1-S2-1-10010469.startLocY
ToonPlayerDescMap.1-S2-1-10010469.supplyCappedPercent
ToonPlayerDescMap.1-S2-1-10010469.userID
ToonPlayerDescMap.1-S2-1-10313976.APM
ToonPlayerDescMap.1-S2-1-10313976.MMR
ToonPlayerDescMap.1-S2-1-10313976.SQ
ToonPlayerDescMap.1-S2-1-10313976.clanTag
ToonPlayerDescMap.1-S2-1-10313976.color.a
ToonPlayerDescMap.1-S2-1-10313976.color.b
ToonPlayerDescMap.1-S2-1-10313976.color.g
ToonPlayerDescMap.1-S2-1-10313976.color.r
ToonPlayerDescMap.1-S2-1-10313976.handicap
ToonPlayerDescMap.1-S2-1-10313976.highestLeague
ToonPlayerDescMap.1-S2-1-10313976.isInClan
ToonPlayerDescMap.1-S2-1-10313976.nickname
ToonPlayerDescMap.1-S2-1-10313976.playerID
ToonPlayerDescMap.1-S2-1-10313976.race
ToonPlayerDescMap.1-S2-1-10313976.realm
ToonPlayerDescMap.1-S2-1-10313976.region
ToonPlayerDescMap.1-S2-1-10313976.result
ToonPlayerDescMap.1-S2-1-10313976.selectedRace
ToonPlayerDescMap.1-S2-1-10313976.startDir
ToonPlayerDescMap.1-S2-1-10313976.startLocX
ToonPlayerDescMap.1-S2-1-10313976.startLocY
ToonPlayerDescMap.1-S2-1-10313976.supplyCappedPercent
ToonPlayerDescMap.1-S2-1-10313976.userID
ToonPlayerDescMap.1-S2-1-10313981.APM
ToonPlayerDescMap.1-S2-1-10313981.MMR
ToonPlayerDescMap.1-S2-1-10313981.SQ
ToonPlayerDescMap.1-S2-1-10313981.clanTag
ToonPlayerDescMap.1-S2-1-10313981.color.a
ToonPlayerDescMap.1-S2-1-10313981.color.b
ToonPlayerDescMap.1-S2-1-10313981.color.g
ToonPlayerDescMap.1-S2-1-10313981.color.r
ToonPlayerDescMap.1-S2-1-10313981.handicap
ToonPlayerDescMap.1-S2-1-10313981.highestLeague
ToonPlayerDescMap.1-S2-1-10313981.isInClan
ToonPlayerDescMap.1-S2-1-10313981.nickname
ToonPlayerDescMap.1-S2-1-10313981.playerID
ToonPlayerDescMap.1-S2-1-10313981.race
ToonPlayerDescMap.1-S2-1-10313981.realm
ToonPlayerDescMap.1-S2-1-10313981.region
ToonPlayerDescMap.1-S2-1-10313981.result
ToonPlayerDescMap.1-S2-1-10313981.selectedRace
ToonPlayerDescMap.1-S2-1-10313981.startDir
ToonPlayerDescMap.1-S2-1-10313981.startLocX
ToonPlayerDescMap.1-S2-1-10313981.startLocY
ToonPlayerDescMap.1-S2-1-10313981.supplyCappedPercent
ToonPlayerDescMap.1-S2-1-10313981.userID
ToonPlayerDescMap.1-S2-1-10314005.APM
ToonPlayerDescMap.1-S2-1-10314005.MMR
ToonPlayerDescMap.1-S2-1-10314005.SQ
ToonPlayerDescMap.1-S2-1-10314005.clanTag
ToonPlayerDescMap.1-S2-1-10314005.color.a
ToonPlayerDescMap.1-S2-1-10314005.color.b
ToonPlayerDescMap.1-S2-1-10314005.color.g
ToonPlayerDescMap.1-S2-1-10314005.color.r
ToonPlayerDescMap.1-S2-1-10314005.handicap
ToonPlayerDescMap.1-S2-1-10314005.highestLeague
ToonPlayerDescMap.1-S2-1-10314005.isInClan
ToonPlayerDescMap.1-S2-1-10314005.nickname
ToonPlayerDescMap.1-S2-1-10314005.playerID
ToonPlayerDescMap.1-S2-1-10314005.race
ToonPlayerDescMap.1-S2-1-10314005.realm
ToonPlayerDescMap.1-S2-1-10314005.region
ToonPlayerDescMap.1-S2-1-10314005.result
ToonPlayerDescMap.1-S2-1-10314005.selectedRace
ToonPlayerDescMap.1-S2-1-10314005.startDir
ToonPlayerDescMap.1-S2-1-10314005.startLocX
ToonPlayerDescMap.1-S2-1-10314005.startLocY
ToonPlayerDescMap.1-S2-1-10314005.supplyCappedPercent
ToonPlayerDescMap.1-S2-1-10314005.userID
ToonPlayerDescMap.1-S2-1-10314033.APM
ToonPlayerDescMap.1-S2-1-10314033.MMR
ToonPlayerDescMap.1-S2-1-10314033.SQ
ToonPlayerDescMap.1-S2-1-10314033.clanTag
ToonPlayerDescMap.1-S2-1-10314033.color.a
ToonPlayerDescMap.1-S2-1-10314033.color.b
ToonPlayerDescMap.1-S2-1-10314033.color.g
ToonPlayerDescMap.1-S2-1-10314033.color.r
ToonPlayerDescMap.1-S2-1-10314033.handicap
ToonPlayerDescMap.1-S2-1-10314033.highestLeague
ToonPlayerDescMap.1-S2-1-10314033.isInClan
ToonPlayerDescMap.1-S2-1-10314033.nickname
ToonPlayerDescMap.1-S2-1-10314033.playerID
ToonPlayerDescMap.1-S2-1-10314033.race
ToonPlayerDescMap.1-S2-1-10314033.realm
ToonPlayerDescMap.1-S2-1-10314033.region
ToonPlayerDescMap.1-S2-1-10314033.result
ToonPlayerDescMap.1-S2-1-10314033.selectedRace
ToonPlayerDescMap.1-S2-1-10314033.startDir
ToonPlayerDescMap.1-S2-1-10314033.startLocX
ToonPlayerDescMap.1-S2-1-10314033.startLocY
ToonPlayerDescMap.1-S2-1-10314033.supplyCappedPercent
ToonPlayerDescMap.1-S2-1-10314033.userID
ToonPlayerDescMap.1-S2-1-10314125.APM
ToonPlayerDescMap.1-S2-1-10314125.MMR
ToonPlayerDescMap.1-S2-1-10314125.SQ
ToonPlayerDescMap.1-S2-1-10314125.clanTag
ToonPlayerDescMap.1-S2-1-10314125.color.a
ToonPlayerDescMap.1-S2-1-10314125.color.b
ToonPlayerDescMap.1-S2-1-10314125.color.g
ToonPlayerDescMap.1-S2-1-10314125.color.r
ToonPlayerDescMap.1-S2-1-10314125.handicap
ToonPlayerDescMap.1-S2-1-10314125.highestLeague
ToonPlayerDescMap.1-S2-1-10314125.isInClan
ToonPlayerDescMap.1-S2-1-10314125.nickname
ToonPlayerDescMap.1-S2-1-10314125.playerID
ToonPlayerDescMap.1-S2-1-10314125.race
ToonPlayerDescMap.1-S2-1-10314125.realm
ToonPlayerDescMap.1-S2-1-10314125.region
ToonPlayerDescMap.1-S2-1-10314125.result
ToonPlayerDescMap.1-S2-1-10314125.selectedRace
ToonPlayerDescMap.1-S2-1-10314125.startDir
ToonPlayerDescMap.1-S2-1-10314125.startLocX
ToonPlayerDescMap.1-S2-1-10314125.startLocY
ToonPlayerDescMap.1-S2-1-10314125.supplyCappedPercent
ToonPlayerDescMap.1-S2-1-10314125.userID
ToonPlayerDescMap.1-S2-1-10314292.APM
ToonPlayerDescMap.1-S2-1-10314292.MMR
ToonPlayerDescMap.1-S2-1-10314292.SQ
ToonPlayerDescMap.1-S2-1-10314292.clanTag
ToonPlayerDescMap.1-S2-1-10314292.color.a
ToonPlayerDescMap.1-S2-1-10314292.color.b
ToonPlayerDescMap.1-S2-1-10314292.color.g
ToonPlayerDescMap.1-S2-1-10314292.color.r
ToonPlayerDescMap.1-S2-1-10314292.handicap
ToonPlayerDescMap.1-S2-1-10314292.highestLeague
ToonPlayerDescMap.1-S2-1-10314292.isInClan
ToonPlayerDescMap.1-S2-1-10314292.nickname
ToonPlayerDescMap.1-S2-1-10314292.playerID
ToonPlayerDescMap.1-S2-1-10314292.race
ToonPlayerDescMap.1-S2-1-10314292.realm
ToonPlayerDescMap.1-S2-1-10314292.region
ToonPlayerDescMap.1-S2-1-10314292.result
ToonPlayerDescMap.1-S2-1-10314292.selectedRace
ToonPlayerDescMap.1-S2-1-10314292.startDir
ToonPlayerDescMap.1-S2-1-10314292.startLocX
ToonPlayerDescMap.1-S2-1-10314292.startLocY
ToonPlayerDescMap.1-S2-1-10314292.supplyCappedPercent
ToonPlayerDescMap.1-S2-1-10314292.userID
ToonPlayerDescMap.1-S2-1-10463737.APM
ToonPlayerDescMap.1-S2-1-10463737.MMR
ToonPlayerDescMap.1-S2-1-10463737.SQ
ToonPlayerDescMap.1-S2-1-10463737.clanTag
ToonPlayerDescMap.1-S2-1-10463737.color.a
ToonPlayerDescMap.1-S2-1-10463737.color.b
ToonPlayerDescMap.1-S2-1-10463737.color.g
ToonPlayerDescMap.1-S2-1-10463737.color.r
ToonPlayerDescMap.1-S2-1-10463737.handicap
ToonPlayerDescMap.1-S2-1-10463737.highestLeague
ToonPlayerDescMap.1-S2-1-10463737.isInClan
ToonPlayerDescMap.1-S2-1-10463737.nickname
ToonPlayerDescMap.1-S2-1-10463737.playerID
ToonPlayerDescMap.1-S2-1-10463737.race
ToonPlayerDescMap.1-S2-1-10463737.realm
ToonPlayerDescMap.1-S2-1-10463737.region
ToonPlayerDescMap.1-S2-1-10463737.result
ToonPlayerDescMap.1-S2-1-10463737.selectedRace
ToonPlayerDescMap.1-S2-1-10463737.startDir
ToonPlayerDescMap.1-S2-1-10463737.startLocX
ToonPlayerDescMap.1-S2-1-10463737.startLocY
ToonPlayerDescMap.1-S2-1-10463737.supplyCappedPercent
ToonPlayerDescMap.1-S2-1-10463737.userID
ToonPlayerDescMap.1-S2-1-10463877.APM
ToonPlayerDescMap.1-S2-1-10463877.MMR
ToonPlayerDescMap.1-S2-1-10463877.SQ
ToonPlayerDescMap.1-S2-1-10463877.clanTag
ToonPlayerDescMap.1-S2-1-10463877.color.a
ToonPlayerDescMap.1-S2-1-10463877.color.b
ToonPlayerDescMap.1-S2-1-10463877.color.g
ToonPlayerDescMap.1-S2-1-10463877.color.r
ToonPlayerDescMap.1-S2-1-10463877.handicap
ToonPlayerDescMap.1-S2-1-10463877.highestLeague
ToonPlayerDescMap.1-S2-1-10463877.isInClan
ToonPlayerDescMap.1-S2-1-10463877.nickname
ToonPlayerDescMap.1-S2-1-10463877.playerID
ToonPlayerDescMap.1-S2-1-10463877.race
ToonPlayerDescMap.1-S2-1-10463877.realm
ToonPlayerDescMap.1-S2-1-10463877.region
... (7150 more keypaths truncated)
```

## Schema consistency

**All 70 directories share the same root-level schema:** True

## Notes

- No DuckDB type proposals in this step (deferred to ingestion design).
- Sample values in the JSON artifact are for type-inference validation only.
- Step scope: `content` (file headers/schemas/sample root keys).
