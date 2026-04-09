# Step 0.5 — Smoke Test

**Gate: PASS**

Dtype strategy applied: `explicit`  
Sparse file used: `rating-2022-09-10.csv` (147 bytes)  
Dense file used: `rating-2025-06-27.csv` (8114431 bytes)

## SQL used (in-memory DuckDB)

```sql
CREATE TABLE smoke_matches AS
SELECT * FROM read_parquet(
    '/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/matches/match-2023-06-03.parquet',
    filename = true
);

CREATE TABLE smoke_ratings AS
SELECT * FROM read_csv(
    ['/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/ratings/rating-2022-09-10.csv', '/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/ratings/rating-2025-06-27.csv'],
    union_by_name = true,
    dtypes = {'profile_id': 'BIGINT', 'games': 'BIGINT', 'rating': 'BIGINT', 'date': 'TIMESTAMP', 'leaderboard_id': 'BIGINT', 'rating_diff': 'BIGINT', 'season': 'BIGINT'},
    filename = true
);

CREATE TABLE smoke_leaderboard AS SELECT * FROM read_parquet('/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/leaderboards/leaderboard.parquet', filename = true);
CREATE TABLE smoke_profiles AS SELECT * FROM read_parquet('/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/aoe2/data/aoe2companion/raw/profiles/profile.parquet', filename = true);

-- Verification queries
SELECT count(*) AS rows FROM smoke_matches;
SELECT count(*) AS rows, count(DISTINCT filename) AS files FROM smoke_ratings;  -- expect files = 2
SELECT count(*) AS rows FROM smoke_leaderboard;
SELECT count(*) AS rows FROM smoke_profiles;
```

## Results

| Table | Rows | Files | filename col | Status |
|-------|------|-------|-------------|--------|
| smoke_matches | 267398 | N/A | True | OK |
| smoke_ratings | 179140 | 2 | True | OK |
| smoke_leaderboard | 2381227 | N/A | True | OK |
| smoke_profiles | 3609686 | N/A | True | OK |