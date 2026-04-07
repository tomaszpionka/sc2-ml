# Step 0.3 — Player Parquet Schema Profile (aoestats, sample-based)

**Stability:** DRIFTED

Total files: 171  
Sample positions: earliest, Q1, median, Q3, latest

## Type drift detected

Column names are stable across samples, but the following columns
have different types across time:

| Column | Types observed (oldest → newest) |
|--------|----------------------------------|
| feudal_age_uptime | DOUBLE → INTEGER |
| castle_age_uptime | DOUBLE → INTEGER |
| imperial_age_uptime | DOUBLE → INTEGER |
| profile_id | DOUBLE → BIGINT |
| opening | VARCHAR → INTEGER |

## SQL used

```sql
-- Sample: 2022-08-28_2022-09-03_players.parquet
DESCRIBE SELECT * FROM read_parquet('<path>/2022-08-28_2022-09-03_players.parquet', filename = true);
SELECT count(*) AS n_rows FROM read_parquet('<path>/2022-08-28_2022-09-03_players.parquet');

-- Sample: 2023-06-18_2023-06-24_players.parquet
DESCRIBE SELECT * FROM read_parquet('<path>/2023-06-18_2023-06-24_players.parquet', filename = true);
SELECT count(*) AS n_rows FROM read_parquet('<path>/2023-06-18_2023-06-24_players.parquet');

-- Sample: 2024-04-14_2024-04-20_players.parquet
DESCRIBE SELECT * FROM read_parquet('<path>/2024-04-14_2024-04-20_players.parquet', filename = true);
SELECT count(*) AS n_rows FROM read_parquet('<path>/2024-04-14_2024-04-20_players.parquet');

-- Sample: 2025-04-06_2025-04-12_players.parquet
DESCRIBE SELECT * FROM read_parquet('<path>/2025-04-06_2025-04-12_players.parquet', filename = true);
SELECT count(*) AS n_rows FROM read_parquet('<path>/2025-04-06_2025-04-12_players.parquet');

-- Sample: 2026-02-01_2026-02-07_players.parquet
DESCRIBE SELECT * FROM read_parquet('<path>/2026-02-01_2026-02-07_players.parquet', filename = true);
SELECT count(*) AS n_rows FROM read_parquet('<path>/2026-02-01_2026-02-07_players.parquet');

-- Union schema across all 171 files (metadata only)
DESCRIBE SELECT * FROM read_parquet(
    'src/rts_predict/aoe2/data/aoestats/raw/players/*_players.parquet',
    union_by_name = true,
    filename = true
);
```

## Per-sample schemas

### 2022-08-28_2022-09-03_players.parquet

Row count: 53556

| Column | Type |
|--------|------|
| winner | BOOLEAN |
| game_id | VARCHAR |
| team | BIGINT |
| feudal_age_uptime | DOUBLE |
| castle_age_uptime | DOUBLE |
| imperial_age_uptime | DOUBLE |
| old_rating | BIGINT |
| new_rating | BIGINT |
| match_rating_diff | DOUBLE |
| replay_summary_raw | VARCHAR |
| profile_id | DOUBLE |
| civ | VARCHAR |
| opening | VARCHAR |
| filename | VARCHAR |

### 2023-06-18_2023-06-24_players.parquet

Row count: 748635

| Column | Type |
|--------|------|
| winner | BOOLEAN |
| game_id | VARCHAR |
| team | BIGINT |
| feudal_age_uptime | DOUBLE |
| castle_age_uptime | DOUBLE |
| imperial_age_uptime | DOUBLE |
| old_rating | BIGINT |
| new_rating | BIGINT |
| match_rating_diff | DOUBLE |
| replay_summary_raw | VARCHAR |
| profile_id | BIGINT |
| civ | VARCHAR |
| opening | VARCHAR |
| filename | VARCHAR |

### 2024-04-14_2024-04-20_players.parquet

Row count: 824722

| Column | Type |
|--------|------|
| winner | BOOLEAN |
| game_id | VARCHAR |
| team | BIGINT |
| feudal_age_uptime | INTEGER |
| castle_age_uptime | INTEGER |
| imperial_age_uptime | INTEGER |
| old_rating | BIGINT |
| new_rating | BIGINT |
| match_rating_diff | DOUBLE |
| replay_summary_raw | VARCHAR |
| profile_id | BIGINT |
| civ | VARCHAR |
| opening | INTEGER |
| filename | VARCHAR |

### 2025-04-06_2025-04-12_players.parquet

Row count: 828607

| Column | Type |
|--------|------|
| winner | BOOLEAN |
| game_id | VARCHAR |
| team | BIGINT |
| feudal_age_uptime | INTEGER |
| castle_age_uptime | INTEGER |
| imperial_age_uptime | INTEGER |
| old_rating | BIGINT |
| new_rating | BIGINT |
| match_rating_diff | DOUBLE |
| replay_summary_raw | VARCHAR |
| profile_id | BIGINT |
| civ | VARCHAR |
| opening | INTEGER |
| filename | VARCHAR |

### 2026-02-01_2026-02-07_players.parquet

Row count: 417903

| Column | Type |
|--------|------|
| winner | BOOLEAN |
| game_id | VARCHAR |
| team | BIGINT |
| feudal_age_uptime | INTEGER |
| castle_age_uptime | INTEGER |
| imperial_age_uptime | INTEGER |
| old_rating | BIGINT |
| new_rating | BIGINT |
| match_rating_diff | DOUBLE |
| replay_summary_raw | VARCHAR |
| profile_id | BIGINT |
| civ | VARCHAR |
| opening | INTEGER |
| filename | VARCHAR |

## Union schema

| Column | Type |
|--------|------|
| winner | BOOLEAN |
| game_id | VARCHAR |
| team | BIGINT |
| feudal_age_uptime | DOUBLE |
| castle_age_uptime | DOUBLE |
| imperial_age_uptime | DOUBLE |
| old_rating | BIGINT |
| new_rating | BIGINT |
| match_rating_diff | DOUBLE |
| replay_summary_raw | VARCHAR |
| profile_id | DOUBLE |
| civ | VARCHAR |
| opening | VARCHAR |
| filename | VARCHAR |