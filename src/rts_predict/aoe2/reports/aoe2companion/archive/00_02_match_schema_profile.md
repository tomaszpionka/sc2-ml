# Step 0.2 — Match Parquet Schema Profile (sample-based)

**Stability:** STABLE

Total match files: 2073  
Sample positions: earliest, Q1, median, Q3, latest

## SQL used

```sql
-- Sample: match-2020-08-01.parquet
DESCRIBE SELECT * FROM read_parquet('/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/matches/match-2020-08-01.parquet', filename = true);
SELECT count(*) AS n_rows FROM read_parquet('/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/matches/match-2020-08-01.parquet');

-- Sample: match-2022-01-01.parquet
DESCRIBE SELECT * FROM read_parquet('/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/matches/match-2022-01-01.parquet', filename = true);
SELECT count(*) AS n_rows FROM read_parquet('/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/matches/match-2022-01-01.parquet');

-- Sample: match-2023-06-03.parquet
DESCRIBE SELECT * FROM read_parquet('/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/matches/match-2023-06-03.parquet', filename = true);
SELECT count(*) AS n_rows FROM read_parquet('/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/matches/match-2023-06-03.parquet');

-- Sample: match-2024-11-02.parquet
DESCRIBE SELECT * FROM read_parquet('/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/matches/match-2024-11-02.parquet', filename = true);
SELECT count(*) AS n_rows FROM read_parquet('/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/matches/match-2024-11-02.parquet');

-- Sample: match-2026-04-04.parquet
DESCRIBE SELECT * FROM read_parquet('/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/matches/match-2026-04-04.parquet', filename = true);
SELECT count(*) AS n_rows FROM read_parquet('/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/matches/match-2026-04-04.parquet');

-- Union schema across all 2073 files (metadata only, no data scan)
DESCRIBE SELECT * FROM read_parquet(
    '/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/matches/match-*.parquet',
    union_by_name = true,
    filename = true
);
```

## Per-sample schemas

### match-2020-08-01.parquet

Row count: 25238

| Column | Type |
|--------|------|
| matchId | INTEGER |
| started | TIMESTAMP |
| finished | TIMESTAMP |
| leaderboard | BLOB |
| name | BLOB |
| server | BLOB |
| internalLeaderboardId | INTEGER |
| privacy | BLOB |
| mod | BOOLEAN |
| map | BLOB |
| difficulty | BLOB |
| startingAge | BLOB |
| fullTechTree | BOOLEAN |
| allowCheats | BOOLEAN |
| empireWarsMode | BOOLEAN |
| endingAge | BLOB |
| gameMode | BLOB |
| lockSpeed | BOOLEAN |
| lockTeams | BOOLEAN |
| mapSize | BLOB |
| population | INTEGER |
| hideCivs | BOOLEAN |
| recordGame | BOOLEAN |
| regicideMode | BOOLEAN |
| gameVariant | BLOB |
| resources | BLOB |
| sharedExploration | BOOLEAN |
| speed | BLOB |
| speedFactor | FLOAT |
| suddenDeathMode | BOOLEAN |
| antiquityMode | BOOLEAN |
| civilizationSet | BLOB |
| teamPositions | BOOLEAN |
| teamTogether | BOOLEAN |
| treatyLength | INTEGER |
| turboMode | BOOLEAN |
| victory | BLOB |
| revealMap | BLOB |
| scenario | BLOB |
| password | BOOLEAN |
| modDataset | BLOB |
| profileId | INTEGER |
| rating | INTEGER |
| ratingDiff | INTEGER |
| color | INTEGER |
| colorHex | BLOB |
| slot | INTEGER |
| status | BLOB |
| team | INTEGER |
| won | BOOLEAN |
| country | BLOB |
| shared | BOOLEAN |
| verified | BOOLEAN |
| civ | BLOB |
| filename | VARCHAR |

### match-2022-01-01.parquet

Row count: 44535

| Column | Type |
|--------|------|
| matchId | INTEGER |
| started | TIMESTAMP |
| finished | TIMESTAMP |
| leaderboard | BLOB |
| name | BLOB |
| server | BLOB |
| internalLeaderboardId | INTEGER |
| privacy | BLOB |
| mod | BOOLEAN |
| map | BLOB |
| difficulty | BLOB |
| startingAge | BLOB |
| fullTechTree | BOOLEAN |
| allowCheats | BOOLEAN |
| empireWarsMode | BOOLEAN |
| endingAge | BLOB |
| gameMode | BLOB |
| lockSpeed | BOOLEAN |
| lockTeams | BOOLEAN |
| mapSize | BLOB |
| population | INTEGER |
| hideCivs | BOOLEAN |
| recordGame | BOOLEAN |
| regicideMode | BOOLEAN |
| gameVariant | BLOB |
| resources | BLOB |
| sharedExploration | BOOLEAN |
| speed | BLOB |
| speedFactor | FLOAT |
| suddenDeathMode | BOOLEAN |
| antiquityMode | BOOLEAN |
| civilizationSet | BLOB |
| teamPositions | BOOLEAN |
| teamTogether | BOOLEAN |
| treatyLength | INTEGER |
| turboMode | BOOLEAN |
| victory | BLOB |
| revealMap | BLOB |
| scenario | BLOB |
| password | BOOLEAN |
| modDataset | BLOB |
| profileId | INTEGER |
| rating | INTEGER |
| ratingDiff | INTEGER |
| color | INTEGER |
| colorHex | BLOB |
| slot | INTEGER |
| status | BLOB |
| team | INTEGER |
| won | BOOLEAN |
| country | BLOB |
| shared | BOOLEAN |
| verified | BOOLEAN |
| civ | BLOB |
| filename | VARCHAR |

### match-2023-06-03.parquet

Row count: 267398

| Column | Type |
|--------|------|
| matchId | INTEGER |
| started | TIMESTAMP |
| finished | TIMESTAMP |
| leaderboard | BLOB |
| name | BLOB |
| server | BLOB |
| internalLeaderboardId | INTEGER |
| privacy | BLOB |
| mod | BOOLEAN |
| map | BLOB |
| difficulty | BLOB |
| startingAge | BLOB |
| fullTechTree | BOOLEAN |
| allowCheats | BOOLEAN |
| empireWarsMode | BOOLEAN |
| endingAge | BLOB |
| gameMode | BLOB |
| lockSpeed | BOOLEAN |
| lockTeams | BOOLEAN |
| mapSize | BLOB |
| population | INTEGER |
| hideCivs | BOOLEAN |
| recordGame | BOOLEAN |
| regicideMode | BOOLEAN |
| gameVariant | BLOB |
| resources | BLOB |
| sharedExploration | BOOLEAN |
| speed | BLOB |
| speedFactor | FLOAT |
| suddenDeathMode | BOOLEAN |
| antiquityMode | BOOLEAN |
| civilizationSet | BLOB |
| teamPositions | BOOLEAN |
| teamTogether | BOOLEAN |
| treatyLength | INTEGER |
| turboMode | BOOLEAN |
| victory | BLOB |
| revealMap | BLOB |
| scenario | BLOB |
| password | BOOLEAN |
| modDataset | BLOB |
| profileId | INTEGER |
| rating | INTEGER |
| ratingDiff | INTEGER |
| color | INTEGER |
| colorHex | BLOB |
| slot | INTEGER |
| status | BLOB |
| team | INTEGER |
| won | BOOLEAN |
| country | BLOB |
| shared | BOOLEAN |
| verified | BOOLEAN |
| civ | BLOB |
| filename | VARCHAR |

### match-2024-11-02.parquet

Row count: 189429

| Column | Type |
|--------|------|
| matchId | INTEGER |
| started | TIMESTAMP |
| finished | TIMESTAMP |
| leaderboard | BLOB |
| name | BLOB |
| server | BLOB |
| internalLeaderboardId | INTEGER |
| privacy | BLOB |
| mod | BOOLEAN |
| map | BLOB |
| difficulty | BLOB |
| startingAge | BLOB |
| fullTechTree | BOOLEAN |
| allowCheats | BOOLEAN |
| empireWarsMode | BOOLEAN |
| endingAge | BLOB |
| gameMode | BLOB |
| lockSpeed | BOOLEAN |
| lockTeams | BOOLEAN |
| mapSize | BLOB |
| population | INTEGER |
| hideCivs | BOOLEAN |
| recordGame | BOOLEAN |
| regicideMode | BOOLEAN |
| gameVariant | BLOB |
| resources | BLOB |
| sharedExploration | BOOLEAN |
| speed | BLOB |
| speedFactor | FLOAT |
| suddenDeathMode | BOOLEAN |
| antiquityMode | BOOLEAN |
| civilizationSet | BLOB |
| teamPositions | BOOLEAN |
| teamTogether | BOOLEAN |
| treatyLength | INTEGER |
| turboMode | BOOLEAN |
| victory | BLOB |
| revealMap | BLOB |
| scenario | BLOB |
| password | BOOLEAN |
| modDataset | BLOB |
| profileId | INTEGER |
| rating | INTEGER |
| ratingDiff | INTEGER |
| color | INTEGER |
| colorHex | BLOB |
| slot | INTEGER |
| status | BLOB |
| team | INTEGER |
| won | BOOLEAN |
| country | BLOB |
| shared | BOOLEAN |
| verified | BOOLEAN |
| civ | BLOB |
| filename | VARCHAR |

### match-2026-04-04.parquet

Row count: 198463

| Column | Type |
|--------|------|
| matchId | INTEGER |
| started | TIMESTAMP |
| finished | TIMESTAMP |
| leaderboard | BLOB |
| name | BLOB |
| server | BLOB |
| internalLeaderboardId | INTEGER |
| privacy | BLOB |
| mod | BOOLEAN |
| map | BLOB |
| difficulty | BLOB |
| startingAge | BLOB |
| fullTechTree | BOOLEAN |
| allowCheats | BOOLEAN |
| empireWarsMode | BOOLEAN |
| endingAge | BLOB |
| gameMode | BLOB |
| lockSpeed | BOOLEAN |
| lockTeams | BOOLEAN |
| mapSize | BLOB |
| population | INTEGER |
| hideCivs | BOOLEAN |
| recordGame | BOOLEAN |
| regicideMode | BOOLEAN |
| gameVariant | BLOB |
| resources | BLOB |
| sharedExploration | BOOLEAN |
| speed | BLOB |
| speedFactor | FLOAT |
| suddenDeathMode | BOOLEAN |
| antiquityMode | BOOLEAN |
| civilizationSet | BLOB |
| teamPositions | BOOLEAN |
| teamTogether | BOOLEAN |
| treatyLength | INTEGER |
| turboMode | BOOLEAN |
| victory | BLOB |
| revealMap | BLOB |
| scenario | BLOB |
| password | BOOLEAN |
| modDataset | BLOB |
| profileId | INTEGER |
| rating | INTEGER |
| ratingDiff | INTEGER |
| color | INTEGER |
| colorHex | BLOB |
| slot | INTEGER |
| status | BLOB |
| team | INTEGER |
| won | BOOLEAN |
| country | BLOB |
| shared | BOOLEAN |
| verified | BOOLEAN |
| civ | BLOB |
| filename | VARCHAR |

## Union schema (all match files)

| Column | Type |
|--------|------|
| matchId | INTEGER |
| started | TIMESTAMP |
| finished | TIMESTAMP |
| leaderboard | BLOB |
| name | BLOB |
| server | BLOB |
| internalLeaderboardId | INTEGER |
| privacy | BLOB |
| mod | BOOLEAN |
| map | BLOB |
| difficulty | BLOB |
| startingAge | BLOB |
| fullTechTree | BOOLEAN |
| allowCheats | BOOLEAN |
| empireWarsMode | BOOLEAN |
| endingAge | BLOB |
| gameMode | BLOB |
| lockSpeed | BOOLEAN |
| lockTeams | BOOLEAN |
| mapSize | BLOB |
| population | INTEGER |
| hideCivs | BOOLEAN |
| recordGame | BOOLEAN |
| regicideMode | BOOLEAN |
| gameVariant | BLOB |
| resources | BLOB |
| sharedExploration | BOOLEAN |
| speed | BLOB |
| speedFactor | FLOAT |
| suddenDeathMode | BOOLEAN |
| antiquityMode | BOOLEAN |
| civilizationSet | BLOB |
| teamPositions | BOOLEAN |
| teamTogether | BOOLEAN |
| treatyLength | INTEGER |
| turboMode | BOOLEAN |
| victory | BLOB |
| revealMap | BLOB |
| scenario | BLOB |
| password | BOOLEAN |
| modDataset | BLOB |
| profileId | INTEGER |
| rating | INTEGER |
| ratingDiff | INTEGER |
| color | INTEGER |
| colorHex | BLOB |
| slot | INTEGER |
| status | BLOB |
| team | INTEGER |
| won | BOOLEAN |
| country | BLOB |
| shared | BOOLEAN |
| verified | BOOLEAN |
| civ | BLOB |
| filename | VARCHAR |