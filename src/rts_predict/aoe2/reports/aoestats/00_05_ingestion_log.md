# Step 0.5 — Full CTAS Ingestion Log (aoestats)

**T_ingestion (start):** `2026-04-07T16:36:33.523683+00:00`  
**T_ingestion (end):** `2026-04-07T16:36:52.108940+00:00`

## SQL used

```sql
DROP TABLE IF EXISTS raw_matches;
CREATE TABLE raw_matches AS
SELECT * FROM read_parquet(
    'src/rts_predict/aoe2/data/aoestats/raw/matches/*_matches.parquet',
    union_by_name = true,
    filename = true
);

DROP TABLE IF EXISTS raw_players;
CREATE TABLE raw_players AS
SELECT * FROM read_parquet(
    'src/rts_predict/aoe2/data/aoestats/raw/players/*_players.parquet',
    union_by_name = true,
    filename = true
);
```

## Row counts

| Table | Row count |
|-------|-----------|
| raw_matches | 30,690,651 |
| raw_players | 107,627,584 |