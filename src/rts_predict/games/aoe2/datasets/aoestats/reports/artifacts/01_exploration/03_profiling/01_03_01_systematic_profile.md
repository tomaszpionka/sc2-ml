# Step 01_03_01 -- Systematic Data Profiling -- aoestats

**Generated:** 2026-04-16
**Dataset:** aoestats (matches_raw: 30,690,651 rows, 18 columns; players_raw: 107,627,584 rows, 14 columns)

## I3 Temporal Classification Table

| Column | Source Table | Profile Type | Temporal Class |
|--------|-------------|--------------|---------------|
| avg_elo | matches_raw | numeric | PRE-GAME |
| duration | matches_raw | numeric | POST-GAME |
| filename | matches_raw | categorical | IDENTIFIER |
| game_id | matches_raw | categorical | IDENTIFIER |
| game_speed | matches_raw | categorical | CONTEXT |
| game_type | matches_raw | categorical | CONTEXT |
| irl_duration | matches_raw | numeric | POST-GAME |
| leaderboard | matches_raw | categorical | CONTEXT |
| map | matches_raw | categorical | CONTEXT |
| mirror | matches_raw | boolean | POST-GAME |
| num_players | matches_raw | numeric | CONTEXT |
| patch | matches_raw | numeric | CONTEXT |
| raw_match_type | matches_raw | numeric | CONTEXT |
| replay_enhanced | matches_raw | boolean | CONTEXT |
| started_timestamp | matches_raw | timestamp | CONTEXT |
| starting_age | matches_raw | categorical | CONTEXT |
| team_0_elo | matches_raw | numeric | PRE-GAME |
| team_1_elo | matches_raw | numeric | PRE-GAME |
| castle_age_uptime | players_raw | numeric | IN-GAME |
| civ | players_raw | categorical | PRE-GAME |
| feudal_age_uptime | players_raw | numeric | IN-GAME |
| filename | players_raw | categorical | IDENTIFIER |
| game_id | players_raw | categorical | IDENTIFIER |
| imperial_age_uptime | players_raw | numeric | IN-GAME |
| match_rating_diff | players_raw | numeric | PRE-GAME |
| new_rating | players_raw | numeric | POST-GAME |
| old_rating | players_raw | numeric | PRE-GAME |
| opening | players_raw | categorical | IN-GAME |
| profile_id | players_raw | numeric | IDENTIFIER |
| replay_summary_raw | players_raw | categorical | CONTEXT |
| team | players_raw | categorical | CONTEXT |
| winner | players_raw | boolean | TARGET |

## Critical Findings

- **Dead fields (100% NULL):** None
- **Constant columns (cardinality=1):** game_type, game_speed
- **Near-constant columns:** leaderboard, starting_age, replay_enhanced, mirror, team, winner
- **Near-constant detection criteria (I7):** uniqueness_ratio < 0.001 AND cardinality <= 5, OR numeric IQR == 0

## Dataset-Level Summary

- Duplicate game_id groups in matches_raw: 0
- Duplicate rows in players_raw (census-aligned methodology): 489
- Players without match in matches_raw: 0
- Matches without players in players_raw: 212,890
- Winner class balance: [{'winner_int': 0, 'cnt': 53816397}, {'winner_int': 1, 'cnt': 53811187}]

## Plot Index

| # | Title | Filename | Description |
|---|-------|----------|-------------|
| 1 | Completeness Heatmap | `plots/01_03_01_completeness_heatmap.png` | NULL % per column, I3 annotated |
| 2 | QQ Plots (matches_raw) | `plots/01_03_01_qq_matches.png` | duration, avg_elo, team_0/1_elo |
| 3 | QQ Plots (players_raw) | `plots/01_03_01_qq_players.png` | old/new_rating, match_rating_diff, age uptimes (N per panel in title) |
| 4 | ECDF Key Columns | `plots/01_03_01_ecdf_key_columns.png` | team_0/1_elo, old_rating, match_rating_diff |

## SQL Queries

### matches_numeric_profile

```sql
WITH base AS (
    SELECT
        COUNT(*)                                          AS total_rows,
        -- duration (BIGINT nanoseconds -> seconds)
        COUNT(duration)                                   AS duration_nonnull,
        COUNT(*) - COUNT(duration)                        AS duration_null,
        COUNT(*) FILTER (WHERE duration = 0)              AS duration_zero,
        COUNT(DISTINCT duration)                          AS duration_distinct,
        AVG(duration / 1e9)                               AS duration_mean,
        STDDEV_SAMP(duration / 1e9)                       AS duration_std,
        MIN(duration / 1e9)                               AS duration_min,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY duration / 1e9) AS duration_p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY duration / 1e9) AS duration_p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration / 1e9) AS duration_p50,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY duration / 1e9) AS duration_p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration / 1e9) AS duration_p95,
        MAX(duration / 1e9)                               AS duration_max,
        SKEWNESS(duration / 1e9)                          AS duration_skew,
        KURTOSIS(duration / 1e9)                          AS duration_kurt,
        -- irl_duration
        COUNT(irl_duration)                               AS irl_duration_nonnull,
        COUNT(*) - COUNT(irl_duration)                    AS irl_duration_null,
        COUNT(*) FILTER (WHERE irl_duration = 0)          AS irl_duration_zero,
        COUNT(DISTINCT irl_duration)                      AS irl_duration_distinct,
        AVG(irl_duration / 1e9)                           AS irl_duration_mean,
        STDDEV_SAMP(irl_duration / 1e9)                   AS irl_duration_std,
        MIN(irl_duration / 1e9)                           AS irl_duration_min,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY irl_duration / 1e9) AS irl_duration_p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY irl_duration / 1e9) AS irl_duration_p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY irl_duration / 1e9) AS irl_duration_p50,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY irl_duration / 1e9) AS irl_duration_p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY irl_duration / 1e9) AS irl_duration_p95,
        MAX(irl_duration / 1e9)                           AS irl_duration_max,
        SKEWNESS(irl_duration / 1e9)                      AS irl_duration_skew,
        KURTOSIS(irl_duration / 1e9)                      AS irl_duration_kurt,
        -- avg_elo
        COUNT(avg_elo)                                    AS avg_elo_nonnull,
        COUNT(*) - COUNT(avg_elo)                         AS avg_elo_null,
        COUNT(*) FILTER (WHERE avg_elo = 0)               AS avg_elo_zero,
        COUNT(DISTINCT avg_elo)                           AS avg_elo_distinct,
        AVG(avg_elo)                                      AS avg_elo_mean,
        STDDEV_SAMP(avg_elo)                              AS avg_elo_std,
        MIN(avg_elo)                                      AS avg_elo_min,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY avg_elo) AS avg_elo_p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY avg_elo) AS avg_elo_p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY avg_elo) AS avg_elo_p50,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY avg_elo) AS avg_elo_p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY avg_elo) AS avg_elo_p95,
        MAX(avg_elo)                                      AS avg_elo_max,
        SKEWNESS(avg_elo)                                 AS avg_elo_skew,
        KURTOSIS(avg_elo)                                 AS avg_elo_kurt,
        -- team_0_elo (ALL rows, including sentinel -1)
        COUNT(team_0_elo)                                 AS team_0_elo_nonnull,
        COUNT(*) - COUNT(team_0_elo)                      AS team_0_elo_null,
        COUNT(*) FILTER (WHERE team_0_elo = 0)            AS team_0_elo_zero,
        COUNT(DISTINCT team_0_elo)                        AS team_0_elo_distinct,
        AVG(team_0_elo)                                   AS team_0_elo_mean,
        STDDEV_SAMP(team_0_elo)                           AS team_0_elo_std,
        MIN(team_0_elo)                                   AS team_0_elo_min,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY team_0_elo) AS team_0_elo_p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY team_0_elo) AS team_0_elo_p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY team_0_elo) AS team_0_elo_p50,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY team_0_elo) AS team_0_elo_p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY team_0_elo) AS team_0_elo_p95,
        MAX(team_0_elo)                                   AS team_0_elo_max,
        SKEWNESS(team_0_elo)                              AS team_0_elo_skew,
        KURTOSIS(team_0_elo)                              AS team_0_elo_kurt,
        -- team_1_elo (ALL rows, including sentinel -1)
        COUNT(team_1_elo)                                 AS team_1_elo_nonnull,
        COUNT(*) - COUNT(team_1_elo)                      AS team_1_elo_null,
        COUNT(*) FILTER (WHERE team_1_elo = 0)            AS team_1_elo_zero,
        COUNT(DISTINCT team_1_elo)                        AS team_1_elo_distinct,
        AVG(team_1_elo)                                   AS team_1_elo_mean,
        STDDEV_SAMP(team_1_elo)                           AS team_1_elo_std,
        MIN(team_1_elo)                                   AS team_1_elo_min,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY team_1_elo) AS team_1_elo_p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY team_1_elo) AS team_1_elo_p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY team_1_elo) AS team_1_elo_p50,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY team_1_elo) AS team_1_elo_p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY team_1_elo) AS team_1_elo_p95,
        MAX(team_1_elo)                                   AS team_1_elo_max,
        SKEWNESS(team_1_elo)                              AS team_1_elo_skew,
        KURTOSIS(team_1_elo)                              AS team_1_elo_kurt,
        -- raw_match_type
        COUNT(raw_match_type)                             AS raw_match_type_nonnull,
        COUNT(*) - COUNT(raw_match_type)                  AS raw_match_type_null,
        COUNT(*) FILTER (WHERE raw_match_type = 0)        AS raw_match_type_zero,
        COUNT(DISTINCT raw_match_type)                    AS raw_match_type_distinct,
        AVG(raw_match_type)                               AS raw_match_type_mean,
        STDDEV_SAMP(raw_match_type)                       AS raw_match_type_std,
        MIN(raw_match_type)                               AS raw_match_type_min,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY raw_match_type) AS raw_match_type_p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY raw_match_type) AS raw_match_type_p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY raw_match_type) AS raw_match_type_p50,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY raw_match_type) AS raw_match_type_p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY raw_match_type) AS raw_match_type_p95,
        MAX(raw_match_type)                               AS raw_match_type_max,
        SKEWNESS(raw_match_type)                          AS raw_match_type_skew,
        KURTOSIS(raw_match_type)                          AS raw_match_type_kurt,
        -- patch
        COUNT(patch)                                      AS patch_nonnull,
        COUNT(*) - COUNT(patch)                           AS patch_null,
        COUNT(*) FILTER (WHERE patch = 0)                 AS patch_zero,
        COUNT(DISTINCT patch)                             AS patch_distinct,
        AVG(patch)                                        AS patch_mean,
        STDDEV_SAMP(patch)                                AS patch_std,
        MIN(patch)                                        AS patch_min,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY patch) AS patch_p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY patch) AS patch_p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY patch) AS patch_p50,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY patch) AS patch_p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY patch) AS patch_p95,
        MAX(patch)                                        AS patch_max,
        SKEWNESS(patch)                                   AS patch_skew,
        KURTOSIS(patch)                                   AS patch_kurt,
        -- num_players
        COUNT(num_players)                                AS num_players_nonnull,
        COUNT(*) - COUNT(num_players)                     AS num_players_null,
        COUNT(*) FILTER (WHERE num_players = 0)           AS num_players_zero,
        COUNT(DISTINCT num_players)                       AS num_players_distinct,
        AVG(num_players)                                  AS num_players_mean,
        STDDEV_SAMP(num_players)                          AS num_players_std,
        MIN(num_players)                                  AS num_players_min,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY num_players) AS num_players_p05,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY num_players) AS num_players_p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY num_players) AS num_players_p50,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY num_players) AS num_players_p75,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY num_players) AS num_players_p95,
        MAX(num_players)                                  AS num_players_max,
        SKEWNESS(num_players)                             AS num_players_skew,
        KURTOSIS(num_players)                             AS num_players_kurt
    FROM matches_raw
)
SELECT * FROM base
```

### matches_iqr_outliers

```sql
SELECT
    COUNT(*) FILTER (WHERE duration/1e9 < -379.0999999999999 OR duration/1e9 > 5496.1)   AS duration_outliers,
    COUNT(*) FILTER (WHERE irl_duration/1e9 < -223.0 OR irl_duration/1e9 > 3233.0) AS irl_duration_outliers,
    COUNT(*) FILTER (WHERE avg_elo < 325.5 OR avg_elo > 1821.5)               AS avg_elo_outliers,
    COUNT(*) FILTER (WHERE team_0_elo != -1 AND (team_0_elo < 316.75 OR team_0_elo > 1822.75)) AS team_0_elo_outliers,
    COUNT(*) FILTER (WHERE team_1_elo != -1 AND (team_1_elo < 330.25 OR team_1_elo > 1824.25)) AS team_1_elo_outliers,
    COUNT(*) FILTER (WHERE raw_match_type IS NOT NULL AND (raw_match_type < 3.0 OR raw_match_type > 11.0)) AS raw_match_type_outliers,
    COUNT(*) FILTER (WHERE patch < 19600.0 OR patch > 215336.0)                      AS patch_outliers,
    COUNT(*) FILTER (WHERE num_players < -1.0 OR num_players > 7.0)        AS num_players_outliers
FROM matches_raw
```

### elo_no_sentinel

```sql
WITH elo_filtered AS (
    SELECT *
    FROM matches_raw
    WHERE team_0_elo != -1 AND team_1_elo != -1
)
SELECT
    -- team_0_elo excluding sentinel -1 (via CTE pre-filter)
    COUNT(team_0_elo)                                                         AS t0_nonnull,
    AVG(team_0_elo)                                                           AS t0_mean,
    STDDEV_SAMP(team_0_elo)                                                   AS t0_std,
    MIN(team_0_elo)                                                           AS t0_min,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY team_0_elo)                  AS t0_p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY team_0_elo)                  AS t0_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY team_0_elo)                  AS t0_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY team_0_elo)                  AS t0_p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY team_0_elo)                  AS t0_p95,
    MAX(team_0_elo)                                                           AS t0_max,
    SKEWNESS(team_0_elo)                                                      AS t0_skew,
    KURTOSIS(team_0_elo)                                                      AS t0_kurt,
    -- team_1_elo excluding sentinel -1 (via CTE pre-filter)
    COUNT(team_1_elo)                                                         AS t1_nonnull,
    AVG(team_1_elo)                                                           AS t1_mean,
    STDDEV_SAMP(team_1_elo)                                                   AS t1_std,
    MIN(team_1_elo)                                                           AS t1_min,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY team_1_elo)                  AS t1_p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY team_1_elo)                  AS t1_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY team_1_elo)                  AS t1_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY team_1_elo)                  AS t1_p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY team_1_elo)                  AS t1_p95,
    MAX(team_1_elo)                                                           AS t1_max,
    SKEWNESS(team_1_elo)                                                      AS t1_skew,
    KURTOSIS(team_1_elo)                                                      AS t1_kurt
FROM elo_filtered
```

### matches_topk_map

```sql
SELECT CAST(map AS VARCHAR) AS val, COUNT(*) AS cnt
    FROM matches_raw
    WHERE map IS NOT NULL
    GROUP BY map
    ORDER BY cnt DESC
    LIMIT 5
```

### matches_topk_leaderboard

```sql
SELECT CAST(leaderboard AS VARCHAR) AS val, COUNT(*) AS cnt
    FROM matches_raw
    WHERE leaderboard IS NOT NULL
    GROUP BY leaderboard
    ORDER BY cnt DESC
    LIMIT 5
```

### matches_topk_game_type

```sql
SELECT CAST(game_type AS VARCHAR) AS val, COUNT(*) AS cnt
    FROM matches_raw
    WHERE game_type IS NOT NULL
    GROUP BY game_type
    ORDER BY cnt DESC
    LIMIT 5
```

### matches_topk_game_speed

```sql
SELECT CAST(game_speed AS VARCHAR) AS val, COUNT(*) AS cnt
    FROM matches_raw
    WHERE game_speed IS NOT NULL
    GROUP BY game_speed
    ORDER BY cnt DESC
    LIMIT 5
```

### matches_topk_starting_age

```sql
SELECT CAST(starting_age AS VARCHAR) AS val, COUNT(*) AS cnt
    FROM matches_raw
    WHERE starting_age IS NOT NULL
    GROUP BY starting_age
    ORDER BY cnt DESC
    LIMIT 5
```

### matches_topk_replay_enhanced

```sql
SELECT CAST(replay_enhanced AS VARCHAR) AS val, COUNT(*) AS cnt
    FROM matches_raw
    WHERE replay_enhanced IS NOT NULL
    GROUP BY replay_enhanced
    ORDER BY cnt DESC
    LIMIT 5
```

### matches_topk_mirror

```sql
SELECT CAST(mirror AS VARCHAR) AS val, COUNT(*) AS cnt
    FROM matches_raw
    WHERE mirror IS NOT NULL
    GROUP BY mirror
    ORDER BY cnt DESC
    LIMIT 5
```

### matches_topk_game_id

```sql
SELECT CAST(game_id AS VARCHAR) AS val, COUNT(*) AS cnt
    FROM matches_raw
    WHERE game_id IS NOT NULL
    GROUP BY game_id
    ORDER BY cnt DESC
    LIMIT 5
```

### matches_topk_filename

```sql
SELECT CAST(filename AS VARCHAR) AS val, COUNT(*) AS cnt
    FROM matches_raw
    WHERE filename IS NOT NULL
    GROUP BY filename
    ORDER BY cnt DESC
    LIMIT 5
```

### matches_started_timestamp

```sql
SELECT
    COUNT(started_timestamp)              AS ts_nonnull,
    COUNT(*) - COUNT(started_timestamp)   AS ts_null,
    COUNT(DISTINCT started_timestamp)     AS ts_distinct,
    MIN(started_timestamp)                AS ts_min,
    MAX(started_timestamp)                AS ts_max
FROM matches_raw
```

### players_numeric_profile

```sql
SELECT
    COUNT(*) AS total_rows,
    -- old_rating (BIGINT; zeros are legitimate, NOT sentinels)
    COUNT(old_rating)                                     AS old_rating_nonnull,
    COUNT(*) - COUNT(old_rating)                          AS old_rating_null,
    COUNT(*) FILTER (WHERE old_rating = 0)                AS old_rating_zero,
    COUNT(DISTINCT old_rating)                            AS old_rating_distinct,
    AVG(old_rating)                                       AS old_rating_mean,
    STDDEV_SAMP(old_rating)                               AS old_rating_std,
    MIN(old_rating)                                       AS old_rating_min,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY old_rating) AS old_rating_p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY old_rating) AS old_rating_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY old_rating) AS old_rating_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY old_rating) AS old_rating_p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY old_rating) AS old_rating_p95,
    MAX(old_rating)                                       AS old_rating_max,
    SKEWNESS(old_rating)                                  AS old_rating_skew,
    KURTOSIS(old_rating)                                  AS old_rating_kurt,
    -- new_rating
    COUNT(new_rating)                                     AS new_rating_nonnull,
    COUNT(*) - COUNT(new_rating)                          AS new_rating_null,
    COUNT(*) FILTER (WHERE new_rating = 0)                AS new_rating_zero,
    COUNT(DISTINCT new_rating)                            AS new_rating_distinct,
    AVG(new_rating)                                       AS new_rating_mean,
    STDDEV_SAMP(new_rating)                               AS new_rating_std,
    MIN(new_rating)                                       AS new_rating_min,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY new_rating) AS new_rating_p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY new_rating) AS new_rating_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY new_rating) AS new_rating_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY new_rating) AS new_rating_p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY new_rating) AS new_rating_p95,
    MAX(new_rating)                                       AS new_rating_max,
    SKEWNESS(new_rating)                                  AS new_rating_skew,
    KURTOSIS(new_rating)                                  AS new_rating_kurt,
    -- match_rating_diff
    COUNT(match_rating_diff)                              AS mrd_nonnull,
    COUNT(*) - COUNT(match_rating_diff)                   AS mrd_null,
    COUNT(*) FILTER (WHERE match_rating_diff = 0)         AS mrd_zero,
    COUNT(DISTINCT match_rating_diff)                     AS mrd_distinct,
    AVG(match_rating_diff)                                AS mrd_mean,
    STDDEV_SAMP(match_rating_diff)                        AS mrd_std,
    MIN(match_rating_diff)                                AS mrd_min,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY match_rating_diff) AS mrd_p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY match_rating_diff) AS mrd_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY match_rating_diff) AS mrd_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY match_rating_diff) AS mrd_p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY match_rating_diff) AS mrd_p95,
    MAX(match_rating_diff)                                AS mrd_max,
    SKEWNESS(match_rating_diff)                           AS mrd_skew,
    KURTOSIS(match_rating_diff)                           AS mrd_kurt,
    -- feudal_age_uptime
    COUNT(feudal_age_uptime)                              AS fau_nonnull,
    COUNT(*) - COUNT(feudal_age_uptime)                   AS fau_null,
    COUNT(*) FILTER (WHERE feudal_age_uptime = 0)         AS fau_zero,
    COUNT(DISTINCT feudal_age_uptime)                     AS fau_distinct,
    AVG(feudal_age_uptime)                                AS fau_mean,
    STDDEV_SAMP(feudal_age_uptime)                        AS fau_std,
    MIN(feudal_age_uptime)                                AS fau_min,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY feudal_age_uptime) AS fau_p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY feudal_age_uptime) AS fau_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY feudal_age_uptime) AS fau_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY feudal_age_uptime) AS fau_p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY feudal_age_uptime) AS fau_p95,
    MAX(feudal_age_uptime)                                AS fau_max,
    SKEWNESS(feudal_age_uptime)                           AS fau_skew,
    KURTOSIS(feudal_age_uptime)                           AS fau_kurt,
    -- castle_age_uptime
    COUNT(castle_age_uptime)                              AS cau_nonnull,
    COUNT(*) - COUNT(castle_age_uptime)                   AS cau_null,
    COUNT(*) FILTER (WHERE castle_age_uptime = 0)         AS cau_zero,
    COUNT(DISTINCT castle_age_uptime)                     AS cau_distinct,
    AVG(castle_age_uptime)                                AS cau_mean,
    STDDEV_SAMP(castle_age_uptime)                        AS cau_std,
    MIN(castle_age_uptime)                                AS cau_min,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY castle_age_uptime) AS cau_p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY castle_age_uptime) AS cau_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY castle_age_uptime) AS cau_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY castle_age_uptime) AS cau_p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY castle_age_uptime) AS cau_p95,
    MAX(castle_age_uptime)                                AS cau_max,
    SKEWNESS(castle_age_uptime)                           AS cau_skew,
    KURTOSIS(castle_age_uptime)                           AS cau_kurt,
    -- imperial_age_uptime
    COUNT(imperial_age_uptime)                            AS iau_nonnull,
    COUNT(*) - COUNT(imperial_age_uptime)                 AS iau_null,
    COUNT(*) FILTER (WHERE imperial_age_uptime = 0)       AS iau_zero,
    COUNT(DISTINCT imperial_age_uptime)                   AS iau_distinct,
    AVG(imperial_age_uptime)                              AS iau_mean,
    STDDEV_SAMP(imperial_age_uptime)                      AS iau_std,
    MIN(imperial_age_uptime)                              AS iau_min,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY imperial_age_uptime) AS iau_p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY imperial_age_uptime) AS iau_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY imperial_age_uptime) AS iau_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY imperial_age_uptime) AS iau_p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY imperial_age_uptime) AS iau_p95,
    MAX(imperial_age_uptime)                              AS iau_max,
    SKEWNESS(imperial_age_uptime)                         AS iau_skew,
    KURTOSIS(imperial_age_uptime)                         AS iau_kurt,
    -- profile_id
    COUNT(profile_id)                                     AS pid_nonnull,
    COUNT(*) - COUNT(profile_id)                          AS pid_null,
    COUNT(*) FILTER (WHERE profile_id = 0)                AS pid_zero,
    COUNT(DISTINCT profile_id)                            AS pid_distinct,
    AVG(profile_id)                                       AS pid_mean,
    MIN(profile_id)                                       AS pid_min,
    MAX(profile_id)                                       AS pid_max,
    -- team
    COUNT(team)                                           AS team_nonnull,
    COUNT(*) - COUNT(team)                                AS team_null,
    COUNT(DISTINCT team)                                  AS team_distinct
FROM players_raw
```

### players_iqr_outliers

```sql
SELECT
    COUNT(*) FILTER (WHERE old_rating IS NOT NULL AND (old_rating < 355.5 OR old_rating > 1807.5))                         AS old_rating_outliers,
    COUNT(*) FILTER (WHERE new_rating IS NOT NULL AND (new_rating < 353.0 OR new_rating > 1809.0))                         AS new_rating_outliers,
    COUNT(*) FILTER (WHERE match_rating_diff IS NOT NULL AND (match_rating_diff < -68.0 OR match_rating_diff > 68.0))   AS match_rating_diff_outliers,
    COUNT(*) FILTER (WHERE feudal_age_uptime IS NOT NULL AND (feudal_age_uptime < 367.219 OR feudal_age_uptime > 1018.675))   AS feudal_age_uptime_outliers,
    COUNT(*) FILTER (WHERE castle_age_uptime IS NOT NULL AND (castle_age_uptime < 533.124 OR castle_age_uptime > 1963.876))   AS castle_age_uptime_outliers,
    COUNT(*) FILTER (WHERE imperial_age_uptime IS NOT NULL AND (imperial_age_uptime < 1221.087 OR imperial_age_uptime > 3207.9429999999998)) AS imperial_age_uptime_outliers
FROM players_raw
```

### players_topk_game_id

```sql
SELECT CAST(game_id AS VARCHAR) AS val, COUNT(*) AS cnt
    FROM players_raw
    WHERE game_id IS NOT NULL
    GROUP BY game_id
    ORDER BY cnt DESC
    LIMIT 5
```

### players_topk_civ

```sql
SELECT CAST(civ AS VARCHAR) AS val, COUNT(*) AS cnt
    FROM players_raw
    WHERE civ IS NOT NULL
    GROUP BY civ
    ORDER BY cnt DESC
    LIMIT 5
```

### players_topk_opening

```sql
SELECT CAST(opening AS VARCHAR) AS val, COUNT(*) AS cnt
    FROM players_raw
    WHERE opening IS NOT NULL
    GROUP BY opening
    ORDER BY cnt DESC
    LIMIT 5
```

### players_topk_replay_summary_raw

```sql
SELECT CAST(replay_summary_raw AS VARCHAR) AS val, COUNT(*) AS cnt
    FROM players_raw
    WHERE replay_summary_raw IS NOT NULL
    GROUP BY replay_summary_raw
    ORDER BY cnt DESC
    LIMIT 5
```

### players_topk_filename

```sql
SELECT CAST(filename AS VARCHAR) AS val, COUNT(*) AS cnt
    FROM players_raw
    WHERE filename IS NOT NULL
    GROUP BY filename
    ORDER BY cnt DESC
    LIMIT 5
```

### winner_class_balance

```sql
SELECT winner::INTEGER AS winner_int, COUNT(*) AS cnt
FROM players_raw
GROUP BY winner::INTEGER
ORDER BY winner_int
```

### duplicate_matches

```sql
SELECT game_id, COUNT(*) AS cnt
FROM matches_raw
GROUP BY game_id
HAVING COUNT(*) > 1
ORDER BY cnt DESC
LIMIT 20
```

### duplicate_players

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT CAST(game_id AS VARCHAR) || '_' || COALESCE(CAST(profile_id AS VARCHAR), '__NULL__')) AS distinct_pairs,
    COUNT(*) - COUNT(DISTINCT CAST(game_id AS VARCHAR) || '_' || COALESCE(CAST(profile_id AS VARCHAR), '__NULL__')) AS duplicate_rows
FROM players_raw
```

### match_linkage

```sql
SELECT
    (SELECT COUNT(*) FROM players_raw p
     WHERE NOT EXISTS (SELECT 1 FROM matches_raw m WHERE m.game_id = p.game_id))
    AS players_without_match,
    (SELECT COUNT(*) FROM matches_raw m
     WHERE NOT EXISTS (SELECT 1 FROM players_raw p WHERE p.game_id = m.game_id))
    AS matches_without_players
```

### qq_matches_sample

```sql
SELECT
    duration / 1e9 AS duration_sec,
    avg_elo,
    team_0_elo,
    team_1_elo,
    num_players
FROM matches_raw
WHERE team_0_elo != -1 AND team_1_elo != -1
USING SAMPLE RESERVOIR(50000)
```

### qq_players_sample

```sql
SELECT
    old_rating,
    new_rating,
    match_rating_diff,
    feudal_age_uptime,
    castle_age_uptime,
    imperial_age_uptime
FROM players_raw
WHERE match_rating_diff IS NOT NULL
USING SAMPLE RESERVOIR(50000)
```

### ecdf_sample

```sql
SELECT
    m.team_0_elo,
    m.team_1_elo,
    p.old_rating,
    p.match_rating_diff
FROM players_raw p
JOIN matches_raw m ON p.game_id = m.game_id
WHERE m.team_0_elo != -1
  AND m.team_1_elo != -1
  AND p.match_rating_diff IS NOT NULL
USING SAMPLE RESERVOIR(50000)
```
