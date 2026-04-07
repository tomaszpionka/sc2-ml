# Step 0.6 — Full CTAS Ingestion Log

**T_ingestion (start):** `2026-04-07T11:20:09.775039+00:00`  
**T_ingestion (end):** `2026-04-07T11:21:37.439190+00:00`  
**Dtype strategy applied to raw_ratings:** `explicit`  
**Rationale:** auto_detect inferred inconsistent types for columns: profile_id, games, rating, date, leaderboard_id, season, rating_diff. Explicit map derived from dense sample schema.

## SQL used

```sql
DROP TABLE IF EXISTS raw_matches;
CREATE TABLE raw_matches AS
SELECT * FROM read_parquet(
    '/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/matches/match-*.parquet',
    union_by_name = true,
    filename = true
);

DROP TABLE IF EXISTS raw_ratings;
CREATE TABLE raw_ratings AS
SELECT * FROM read_csv(
    '/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/ratings/rating-*.csv',
    union_by_name = true,
    dtypes = {'profile_id': 'BIGINT', 'games': 'BIGINT', 'rating': 'BIGINT', 'date': 'TIMESTAMP', 'leaderboard_id': 'BIGINT', 'rating_diff': 'BIGINT', 'season': 'BIGINT'},
    filename = true
);

DROP TABLE IF EXISTS raw_leaderboard;
CREATE TABLE raw_leaderboard AS
SELECT * FROM read_parquet('/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/leaderboards/leaderboard.parquet', filename = true);

DROP TABLE IF EXISTS raw_profiles;
CREATE TABLE raw_profiles AS
SELECT * FROM read_parquet('/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/profiles/profile.parquet', filename = true);
```

## Row counts

| Table | Row count |
|-------|-----------|
| raw_matches | 277,099,059 |
| raw_ratings | 58,317,433 |
| raw_leaderboard | 2,381,227 |
| raw_profiles | 3,609,686 |