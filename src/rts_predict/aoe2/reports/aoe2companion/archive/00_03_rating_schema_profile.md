# Step 0.3 — Rating CSV Schema Profile and Dtype Decision

**Sparse/dense boundary date:** `2025-06-26`  
**File-size threshold for sparsity:** 1024 bytes (1 KB)

## File-size distribution

| Category | Count | Size criterion |
|----------|-------|---------------|
| Header-only (sparse) | 1336 | == 63 bytes |
| Transition | 455 | 64 – 999 bytes |
| Dense | 281 | >= 1 KB |

**Threshold derivation:** Header-only files are exactly 63 bytes
(the CSV header string `profile_id,games,rating,date,leaderboard_id,rating_diff,season`
plus newline with no data rows). The 1 KB threshold is conservative,
ensuring no transitional files are misclassified as dense.

## SQL used

```sql
-- Sample: rating-2020-08-01.csv
DESCRIBE SELECT * FROM read_csv('src/rts_predict/aoe2/data/aoe2companion/raw/ratings/rating-2020-08-01.csv', auto_detect = true);

-- Sample: rating-2021-10-20.csv
DESCRIBE SELECT * FROM read_csv('src/rts_predict/aoe2/data/aoe2companion/raw/ratings/rating-2021-10-20.csv', auto_detect = true);

-- Sample: rating-2023-04-22.csv
DESCRIBE SELECT * FROM read_csv('src/rts_predict/aoe2/data/aoe2companion/raw/ratings/rating-2023-04-22.csv', auto_detect = true);

-- Sample: rating-2022-09-10.csv
DESCRIBE SELECT * FROM read_csv('src/rts_predict/aoe2/data/aoe2companion/raw/ratings/rating-2022-09-10.csv', auto_detect = true);

-- Sample: rating-2024-01-15.csv
DESCRIBE SELECT * FROM read_csv('src/rts_predict/aoe2/data/aoe2companion/raw/ratings/rating-2024-01-15.csv', auto_detect = true);

-- Sample: rating-2025-06-27.csv
DESCRIBE SELECT * FROM read_csv('src/rts_predict/aoe2/data/aoe2companion/raw/ratings/rating-2025-06-27.csv', auto_detect = true);

-- Sample: rating-2025-09-29.csv
DESCRIBE SELECT * FROM read_csv('src/rts_predict/aoe2/data/aoe2companion/raw/ratings/rating-2025-09-29.csv', auto_detect = true);

-- Sample: rating-2025-12-31.csv
DESCRIBE SELECT * FROM read_csv('src/rts_predict/aoe2/data/aoe2companion/raw/ratings/rating-2025-12-31.csv', auto_detect = true);

-- Union schema across all 2072 CSV files (header read only)
DESCRIBE SELECT * FROM read_csv(
    'src/rts_predict/aoe2/data/aoe2companion/raw/ratings/rating-*.csv',
    union_by_name = true,
    auto_detect = true,
    filename = true
);
```

## Per-sample schemas

### rating-2020-08-01.csv (header-only, 63 bytes)

| Column | Type |
|--------|------|
| profile_id | VARCHAR |
| games | VARCHAR |
| rating | VARCHAR |
| date | VARCHAR |
| leaderboard_id | VARCHAR |
| rating_diff | VARCHAR |
| season | VARCHAR |

### rating-2021-10-20.csv (header-only, 63 bytes)

| Column | Type |
|--------|------|
| profile_id | VARCHAR |
| games | VARCHAR |
| rating | VARCHAR |
| date | VARCHAR |
| leaderboard_id | VARCHAR |
| rating_diff | VARCHAR |
| season | VARCHAR |

### rating-2023-04-22.csv (header-only, 63 bytes)

| Column | Type |
|--------|------|
| profile_id | VARCHAR |
| games | VARCHAR |
| rating | VARCHAR |
| date | VARCHAR |
| leaderboard_id | VARCHAR |
| rating_diff | VARCHAR |
| season | VARCHAR |

### rating-2022-09-10.csv (transition, 147 bytes)

| Column | Type |
|--------|------|
| profile_id | BIGINT |
| games | BIGINT |
| rating | BIGINT |
| date | TIMESTAMP |
| leaderboard_id | BIGINT |
| rating_diff | VARCHAR |
| season | BIGINT |

### rating-2024-01-15.csv (transition, 427 bytes)

| Column | Type |
|--------|------|
| profile_id | BIGINT |
| games | BIGINT |
| rating | BIGINT |
| date | TIMESTAMP |
| leaderboard_id | BIGINT |
| rating_diff | BIGINT |
| season | BIGINT |

### rating-2025-06-27.csv (dense, 8114431 bytes)

| Column | Type |
|--------|------|
| profile_id | BIGINT |
| games | BIGINT |
| rating | BIGINT |
| date | TIMESTAMP |
| leaderboard_id | BIGINT |
| rating_diff | BIGINT |
| season | BIGINT |

### rating-2025-09-29.csv (dense, 10701095 bytes)

| Column | Type |
|--------|------|
| profile_id | BIGINT |
| games | BIGINT |
| rating | BIGINT |
| date | TIMESTAMP |
| leaderboard_id | BIGINT |
| rating_diff | BIGINT |
| season | BIGINT |

### rating-2025-12-31.csv (dense, 10614705 bytes)

| Column | Type |
|--------|------|
| profile_id | BIGINT |
| games | BIGINT |
| rating | BIGINT |
| date | TIMESTAMP |
| leaderboard_id | BIGINT |
| rating_diff | BIGINT |
| season | BIGINT |

## Union schema (all rating CSVs)

| Column | Type |
|--------|------|
| profile_id | BIGINT |
| games | BIGINT |
| rating | BIGINT |
| date | TIMESTAMP |
| leaderboard_id | BIGINT |
| rating_diff | BIGINT |
| season | BIGINT |
| filename | VARCHAR |

## Dtype decision

**Strategy:** `explicit`  
**Rationale:** auto_detect inferred inconsistent types for columns: profile_id, games, rating, date, leaderboard_id, season, rating_diff. Explicit map derived from dense sample schema.

Artifact: `00_03_dtype_decision.json`