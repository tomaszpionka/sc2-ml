# Step 0.4 — Smoke Test (aoestats)

**Gate: PASS**

Files tested (matches): `2022-08-28_2022-09-03_matches.parquet`, `2026-02-01_2026-02-07_matches.parquet`  
Files tested (players): `2022-08-28_2022-09-03_players.parquet`, `2026-02-01_2026-02-07_players.parquet`

## SQL used (in-memory DuckDB)

```sql
CREATE TABLE smoke_matches AS
SELECT * FROM read_parquet(
    ['src/rts_predict/aoe2/data/aoestats/raw/matches/2022-08-28_2022-09-03_matches.parquet', 'src/rts_predict/aoe2/data/aoestats/raw/matches/2026-02-01_2026-02-07_matches.parquet'],
    union_by_name = true,
    filename = true
);

CREATE TABLE smoke_players AS
SELECT * FROM read_parquet(
    ['src/rts_predict/aoe2/data/aoestats/raw/players/2022-08-28_2022-09-03_players.parquet', 'src/rts_predict/aoe2/data/aoestats/raw/players/2026-02-01_2026-02-07_players.parquet'],
    union_by_name = true,
    filename = true
);

-- Verification
SELECT count(*) AS rows, count(DISTINCT filename) AS files FROM smoke_matches;  -- expect files = 2
SELECT count(*) AS rows, count(DISTINCT filename) AS files FROM smoke_players;  -- expect files = 2
```

## Results

| Table | Rows | Files | filename col | Status |
|-------|------|-------|-------------|--------|
| smoke_matches | 130276 | 2 | True | OK |
| smoke_players | 471459 | 2 | True | OK |