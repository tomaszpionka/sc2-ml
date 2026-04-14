# Step 01_02_03 -- Raw Schema DESCRIBE

**Dataset:** aoe2companion
**Sources:** matches, ratings, leaderboards, profiles

All SQL queries that produced reported results are inlined below (Invariant #6).
Schema obtained via in-memory DuckDB with `LIMIT 0` (no row data loaded).

---

## matches (55 columns)

```sql
DESCRIBE SELECT * FROM read_parquet(
    '<matches_glob>',
    binary_as_string=true, union_by_name=true, filename=true
) LIMIT 0
```

| column_name | column_type | null | key | default | extra |
|---|---|---|---|---|---|
| matchId | INTEGER | YES | None | None | None |
| started | TIMESTAMP | YES | None | None | None |
| finished | TIMESTAMP | YES | None | None | None |
| leaderboard | VARCHAR | YES | None | None | None |
| name | VARCHAR | YES | None | None | None |
| server | VARCHAR | YES | None | None | None |
| internalLeaderboardId | INTEGER | YES | None | None | None |
| privacy | VARCHAR | YES | None | None | None |
| mod | BOOLEAN | YES | None | None | None |
| map | VARCHAR | YES | None | None | None |
| difficulty | VARCHAR | YES | None | None | None |
| startingAge | VARCHAR | YES | None | None | None |
| fullTechTree | BOOLEAN | YES | None | None | None |
| allowCheats | BOOLEAN | YES | None | None | None |
| empireWarsMode | BOOLEAN | YES | None | None | None |
| endingAge | VARCHAR | YES | None | None | None |
| gameMode | VARCHAR | YES | None | None | None |
| lockSpeed | BOOLEAN | YES | None | None | None |
| lockTeams | BOOLEAN | YES | None | None | None |
| mapSize | VARCHAR | YES | None | None | None |
| population | INTEGER | YES | None | None | None |
| hideCivs | BOOLEAN | YES | None | None | None |
| recordGame | BOOLEAN | YES | None | None | None |
| regicideMode | BOOLEAN | YES | None | None | None |
| gameVariant | VARCHAR | YES | None | None | None |
| resources | VARCHAR | YES | None | None | None |
| sharedExploration | BOOLEAN | YES | None | None | None |
| speed | VARCHAR | YES | None | None | None |
| speedFactor | FLOAT | YES | None | None | None |
| suddenDeathMode | BOOLEAN | YES | None | None | None |
| antiquityMode | BOOLEAN | YES | None | None | None |
| civilizationSet | VARCHAR | YES | None | None | None |
| teamPositions | BOOLEAN | YES | None | None | None |
| teamTogether | BOOLEAN | YES | None | None | None |
| treatyLength | INTEGER | YES | None | None | None |
| turboMode | BOOLEAN | YES | None | None | None |
| victory | VARCHAR | YES | None | None | None |
| revealMap | VARCHAR | YES | None | None | None |
| scenario | VARCHAR | YES | None | None | None |
| password | BOOLEAN | YES | None | None | None |
| modDataset | VARCHAR | YES | None | None | None |
| profileId | INTEGER | YES | None | None | None |
| rating | INTEGER | YES | None | None | None |
| ratingDiff | INTEGER | YES | None | None | None |
| color | INTEGER | YES | None | None | None |
| colorHex | VARCHAR | YES | None | None | None |
| slot | INTEGER | YES | None | None | None |
| status | VARCHAR | YES | None | None | None |
| team | INTEGER | YES | None | None | None |
| won | BOOLEAN | YES | None | None | None |
| country | VARCHAR | YES | None | None | None |
| shared | BOOLEAN | YES | None | None | None |
| verified | BOOLEAN | YES | None | None | None |
| civ | VARCHAR | YES | None | None | None |
| filename | VARCHAR | YES | None | None | None |

## ratings (8 columns)

```sql
DESCRIBE SELECT * FROM read_csv(
    '<ratings_glob>',
    union_by_name=true, filename=true,
    dtypes={profile_id: BIGINT, games: BIGINT, rating: BIGINT,
            date: TIMESTAMP, leaderboard_id: BIGINT,
            rating_diff: BIGINT, season: BIGINT}
) LIMIT 0
```

| column_name | column_type | null | key | default | extra |
|---|---|---|---|---|---|
| profile_id | BIGINT | YES | None | None | None |
| games | BIGINT | YES | None | None | None |
| rating | BIGINT | YES | None | None | None |
| date | TIMESTAMP | YES | None | None | None |
| leaderboard_id | BIGINT | YES | None | None | None |
| rating_diff | BIGINT | YES | None | None | None |
| season | BIGINT | YES | None | None | None |
| filename | VARCHAR | YES | None | None | None |

## leaderboards (19 columns)

```sql
DESCRIBE SELECT * FROM read_parquet(
    '<leaderboard_file>',
    binary_as_string=true, filename=true
) LIMIT 0
```

| column_name | column_type | null | key | default | extra |
|---|---|---|---|---|---|
| leaderboard | VARCHAR | YES | None | None | None |
| profileId | INTEGER | YES | None | None | None |
| name | VARCHAR | YES | None | None | None |
| rank | INTEGER | YES | None | None | None |
| rating | INTEGER | YES | None | None | None |
| lastMatchTime | TIMESTAMP | YES | None | None | None |
| drops | INTEGER | YES | None | None | None |
| losses | INTEGER | YES | None | None | None |
| streak | INTEGER | YES | None | None | None |
| wins | INTEGER | YES | None | None | None |
| games | INTEGER | YES | None | None | None |
| updatedAt | TIMESTAMP | YES | None | None | None |
| rankCountry | INTEGER | YES | None | None | None |
| active | BOOLEAN | YES | None | None | None |
| season | INTEGER | YES | None | None | None |
| rankLevel | INTEGER | YES | None | None | None |
| steamId | VARCHAR | YES | None | None | None |
| country | VARCHAR | YES | None | None | None |
| filename | VARCHAR | YES | None | None | None |

## profiles (14 columns)

```sql
DESCRIBE SELECT * FROM read_parquet(
    '<profile_file>',
    binary_as_string=true, filename=true
) LIMIT 0
```

| column_name | column_type | null | key | default | extra |
|---|---|---|---|---|---|
| profileId | INTEGER | YES | None | None | None |
| steamId | VARCHAR | YES | None | None | None |
| name | VARCHAR | YES | None | None | None |
| clan | VARCHAR | YES | None | None | None |
| country | VARCHAR | YES | None | None | None |
| avatarhash | VARCHAR | YES | None | None | None |
| sharedHistory | BOOLEAN | YES | None | None | None |
| twitchChannel | VARCHAR | YES | None | None | None |
| youtubeChannel | VARCHAR | YES | None | None | None |
| youtubeChannelName | VARCHAR | YES | None | None | None |
| discordId | VARCHAR | YES | None | None | None |
| discordName | VARCHAR | YES | None | None | None |
| discordInvitation | VARCHAR | YES | None | None | None |
| filename | VARCHAR | YES | None | None | None |

---

*Generated by notebook 01_02_03_raw_schema_describe.py*
