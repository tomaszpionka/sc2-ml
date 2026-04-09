# Step 0.4 — Singleton Schema Profile (Leaderboard and Profiles)

WARNING: Both tables are point-in-time snapshots. They MUST NOT be
joined to historical matches as if they were time-varying.

## SQL used

```sql
DESCRIBE SELECT * FROM read_parquet('src/rts_predict/aoe2/data/aoe2companion/raw/leaderboards/leaderboard.parquet', filename = true);
SELECT count(*) AS n_rows FROM read_parquet('src/rts_predict/aoe2/data/aoe2companion/raw/leaderboards/leaderboard.parquet');

DESCRIBE SELECT * FROM read_parquet('src/rts_predict/aoe2/data/aoe2companion/raw/profiles/profile.parquet', filename = true);
SELECT count(*) AS n_rows FROM read_parquet('src/rts_predict/aoe2/data/aoe2companion/raw/profiles/profile.parquet');
```

## leaderboard.parquet

**T_snapshot:** `2026-04-06T21:08:57.795793+00:00`  
**Row count:** 2381227

| Column | Type |
|--------|------|
| leaderboard | BLOB |
| profileId | INTEGER |
| name | BLOB |
| rank | INTEGER |
| rating | INTEGER |
| lastMatchTime | TIMESTAMP |
| drops | INTEGER |
| losses | INTEGER |
| streak | INTEGER |
| wins | INTEGER |
| games | INTEGER |
| updatedAt | TIMESTAMP |
| rankCountry | INTEGER |
| active | BOOLEAN |
| season | INTEGER |
| rankLevel | INTEGER |
| steamId | BLOB |
| country | BLOB |
| filename | VARCHAR |

## profile.parquet

**T_snapshot:** `2026-04-06T21:09:07.822448+00:00`  
**Row count:** 3609686

| Column | Type |
|--------|------|
| profileId | INTEGER |
| steamId | BLOB |
| name | BLOB |
| clan | BLOB |
| country | BLOB |
| avatarhash | BLOB |
| sharedHistory | BOOLEAN |
| twitchChannel | BLOB |
| youtubeChannel | BLOB |
| youtubeChannelName | BLOB |
| discordId | BLOB |
| discordName | BLOB |
| discordInvitation | BLOB |
| filename | VARCHAR |