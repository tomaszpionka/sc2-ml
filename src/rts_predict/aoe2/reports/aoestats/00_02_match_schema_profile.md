# Step 0.2 — Match Parquet Schema Profile (aoestats, sample-based)

**Stability:** DRIFTED

Total files: 172  
Sample positions: earliest, Q1, median, Q3, latest

## Type drift detected

Column names are stable across samples, but the following columns
have different types across time:

| Column | Types observed (oldest → newest) |
|--------|----------------------------------|
| raw_match_type | DOUBLE → BIGINT |

## SQL used

```sql
-- Sample: 2022-08-28_2022-09-03_matches.parquet
DESCRIBE SELECT * FROM read_parquet('<path>/2022-08-28_2022-09-03_matches.parquet', filename = true);
SELECT count(*) AS n_rows FROM read_parquet('<path>/2022-08-28_2022-09-03_matches.parquet');

-- Sample: 2023-06-25_2023-07-01_matches.parquet
DESCRIBE SELECT * FROM read_parquet('<path>/2023-06-25_2023-07-01_matches.parquet', filename = true);
SELECT count(*) AS n_rows FROM read_parquet('<path>/2023-06-25_2023-07-01_matches.parquet');

-- Sample: 2024-04-21_2024-04-27_matches.parquet
DESCRIBE SELECT * FROM read_parquet('<path>/2024-04-21_2024-04-27_matches.parquet', filename = true);
SELECT count(*) AS n_rows FROM read_parquet('<path>/2024-04-21_2024-04-27_matches.parquet');

-- Sample: 2025-04-13_2025-04-19_matches.parquet
DESCRIBE SELECT * FROM read_parquet('<path>/2025-04-13_2025-04-19_matches.parquet', filename = true);
SELECT count(*) AS n_rows FROM read_parquet('<path>/2025-04-13_2025-04-19_matches.parquet');

-- Sample: 2026-02-01_2026-02-07_matches.parquet
DESCRIBE SELECT * FROM read_parquet('<path>/2026-02-01_2026-02-07_matches.parquet', filename = true);
SELECT count(*) AS n_rows FROM read_parquet('<path>/2026-02-01_2026-02-07_matches.parquet');

-- Union schema across all 172 files (metadata only)
DESCRIBE SELECT * FROM read_parquet(
    'src/rts_predict/aoe2/data/aoestats/raw/matches/*_matches.parquet',
    union_by_name = true,
    filename = true
);
```

## Per-sample schemas

### 2022-08-28_2022-09-03_matches.parquet

Row count: 11615

| Column | Type |
|--------|------|
| map | VARCHAR |
| started_timestamp | TIMESTAMP WITH TIME ZONE |
| duration | BIGINT |
| irl_duration | BIGINT |
| game_id | VARCHAR |
| avg_elo | DOUBLE |
| num_players | BIGINT |
| team_0_elo | DOUBLE |
| team_1_elo | DOUBLE |
| replay_enhanced | BOOLEAN |
| leaderboard | VARCHAR |
| mirror | BOOLEAN |
| patch | BIGINT |
| raw_match_type | DOUBLE |
| game_type | VARCHAR |
| game_speed | VARCHAR |
| starting_age | VARCHAR |
| filename | VARCHAR |

### 2023-06-25_2023-07-01_matches.parquet

Row count: 217711

| Column | Type |
|--------|------|
| map | VARCHAR |
| started_timestamp | TIMESTAMP WITH TIME ZONE |
| duration | BIGINT |
| irl_duration | BIGINT |
| game_id | VARCHAR |
| avg_elo | DOUBLE |
| num_players | BIGINT |
| team_0_elo | DOUBLE |
| team_1_elo | DOUBLE |
| replay_enhanced | BOOLEAN |
| leaderboard | VARCHAR |
| mirror | BOOLEAN |
| patch | BIGINT |
| raw_match_type | BIGINT |
| game_type | VARCHAR |
| game_speed | VARCHAR |
| starting_age | VARCHAR |
| filename | VARCHAR |

### 2024-04-21_2024-04-27_matches.parquet

Row count: 240980

| Column | Type |
|--------|------|
| map | VARCHAR |
| started_timestamp | TIMESTAMP WITH TIME ZONE |
| duration | BIGINT |
| irl_duration | BIGINT |
| game_id | VARCHAR |
| avg_elo | DOUBLE |
| num_players | BIGINT |
| team_0_elo | DOUBLE |
| team_1_elo | DOUBLE |
| replay_enhanced | BOOLEAN |
| leaderboard | VARCHAR |
| mirror | BOOLEAN |
| patch | BIGINT |
| raw_match_type | DOUBLE |
| game_type | VARCHAR |
| game_speed | VARCHAR |
| starting_age | VARCHAR |
| filename | VARCHAR |

### 2025-04-13_2025-04-19_matches.parquet

Row count: 224416

| Column | Type |
|--------|------|
| map | VARCHAR |
| started_timestamp | TIMESTAMP WITH TIME ZONE |
| duration | BIGINT |
| irl_duration | BIGINT |
| game_id | VARCHAR |
| avg_elo | DOUBLE |
| num_players | BIGINT |
| team_0_elo | DOUBLE |
| team_1_elo | DOUBLE |
| replay_enhanced | BOOLEAN |
| leaderboard | VARCHAR |
| mirror | BOOLEAN |
| patch | BIGINT |
| raw_match_type | BIGINT |
| game_type | VARCHAR |
| game_speed | VARCHAR |
| starting_age | VARCHAR |
| filename | VARCHAR |

### 2026-02-01_2026-02-07_matches.parquet

Row count: 118661

| Column | Type |
|--------|------|
| map | VARCHAR |
| started_timestamp | TIMESTAMP WITH TIME ZONE |
| duration | BIGINT |
| irl_duration | BIGINT |
| game_id | VARCHAR |
| avg_elo | DOUBLE |
| num_players | BIGINT |
| team_0_elo | DOUBLE |
| team_1_elo | DOUBLE |
| replay_enhanced | BOOLEAN |
| leaderboard | VARCHAR |
| mirror | BOOLEAN |
| patch | BIGINT |
| raw_match_type | BIGINT |
| game_type | VARCHAR |
| game_speed | VARCHAR |
| starting_age | VARCHAR |
| filename | VARCHAR |

## Union schema

| Column | Type |
|--------|------|
| map | VARCHAR |
| started_timestamp | TIMESTAMP WITH TIME ZONE |
| duration | BIGINT |
| irl_duration | BIGINT |
| game_id | VARCHAR |
| avg_elo | DOUBLE |
| num_players | BIGINT |
| team_0_elo | DOUBLE |
| team_1_elo | DOUBLE |
| replay_enhanced | BOOLEAN |
| leaderboard | VARCHAR |
| mirror | BOOLEAN |
| patch | BIGINT |
| raw_match_type | DOUBLE |
| game_type | VARCHAR |
| game_speed | VARCHAR |
| starting_age | VARCHAR |
| filename | VARCHAR |