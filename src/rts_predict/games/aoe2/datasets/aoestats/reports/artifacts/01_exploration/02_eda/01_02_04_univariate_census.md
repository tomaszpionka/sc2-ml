# Step 01_02_04 -- Univariate Census & Target Variable EDA

**Dataset:** aoestats
**Tables:** matches_raw (18 cols), players_raw (14 cols)

## SQL Queries (Invariant #6)

### matches_null_census

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(map) AS map_null,
    ROUND(100.0 * (COUNT(*) - COUNT(map)) / COUNT(*), 2) AS map_null_pct,
    COUNT(*) - COUNT(started_timestamp) AS started_timestamp_null,
    ROUND(100.0 * (COUNT(*) - COUNT(started_timestamp)) / COUNT(*), 2) AS started_timestamp_null_pct,
    COUNT(*) - COUNT(duration) AS duration_null,
    ROUND(100.0 * (COUNT(*) - COUNT(duration)) / COUNT(*), 2) AS duration_null_pct,
    COUNT(*) - COUNT(irl_duration) AS irl_duration_null,
    ROUND(100.0 * (COUNT(*) - COUNT(irl_duration)) / COUNT(*), 2) AS irl_duration_null_pct,
    COUNT(*) - COUNT(game_id) AS game_id_null,
    ROUND(100.0 * (COUNT(*) - COUNT(game_id)) / COUNT(*), 2) AS game_id_null_pct,
    COUNT(*) - COUNT(avg_elo) AS avg_elo_null,
    ROUND(100.0 * (COUNT(*) - COUNT(avg_elo)) / COUNT(*), 2) AS avg_elo_null_pct,
    COUNT(*) - COUNT(num_players) AS num_players_null,
    ROUND(100.0 * (COUNT(*) - COUNT(num_players)) / COUNT(*), 2) AS num_players_null_pct,
    COUNT(*) - COUNT(team_0_elo) AS team_0_elo_null,
    ROUND(100.0 * (COUNT(*) - COUNT(team_0_elo)) / COUNT(*), 2) AS team_0_elo_null_pct,
    COUNT(*) - COUNT(team_1_elo) AS team_1_elo_null,
    ROUND(100.0 * (COUNT(*) - COUNT(team_1_elo)) / COUNT(*), 2) AS team_1_elo_null_pct,
    COUNT(*) - COUNT(replay_enhanced) AS replay_enhanced_null,
    ROUND(100.0 * (COUNT(*) - COUNT(replay_enhanced)) / COUNT(*), 2) AS replay_enhanced_null_pct,
    COUNT(*) - COUNT(leaderboard) AS leaderboard_null,
    ROUND(100.0 * (COUNT(*) - COUNT(leaderboard)) / COUNT(*), 2) AS leaderboard_null_pct,
    COUNT(*) - COUNT(mirror) AS mirror_null,
    ROUND(100.0 * (COUNT(*) - COUNT(mirror)) / COUNT(*), 2) AS mirror_null_pct,
    COUNT(*) - COUNT(patch) AS patch_null,
    ROUND(100.0 * (COUNT(*) - COUNT(patch)) / COUNT(*), 2) AS patch_null_pct,
    COUNT(*) - COUNT(raw_match_type) AS raw_match_type_null,
    ROUND(100.0 * (COUNT(*) - COUNT(raw_match_type)) / COUNT(*), 2) AS raw_match_type_null_pct,
    COUNT(*) - COUNT(game_type) AS game_type_null,
    ROUND(100.0 * (COUNT(*) - COUNT(game_type)) / COUNT(*), 2) AS game_type_null_pct,
    COUNT(*) - COUNT(game_speed) AS game_speed_null,
    ROUND(100.0 * (COUNT(*) - COUNT(game_speed)) / COUNT(*), 2) AS game_speed_null_pct,
    COUNT(*) - COUNT(starting_age) AS starting_age_null,
    ROUND(100.0 * (COUNT(*) - COUNT(starting_age)) / COUNT(*), 2) AS starting_age_null_pct,
    COUNT(*) - COUNT(filename) AS filename_null,
    ROUND(100.0 * (COUNT(*) - COUNT(filename)) / COUNT(*), 2) AS filename_null_pct
FROM matches_raw
```

### players_null_census

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(winner) AS winner_null,
    ROUND(100.0 * (COUNT(*) - COUNT(winner)) / COUNT(*), 2) AS winner_null_pct,
    COUNT(*) - COUNT(game_id) AS game_id_null,
    ROUND(100.0 * (COUNT(*) - COUNT(game_id)) / COUNT(*), 2) AS game_id_null_pct,
    COUNT(*) - COUNT(team) AS team_null,
    ROUND(100.0 * (COUNT(*) - COUNT(team)) / COUNT(*), 2) AS team_null_pct,
    COUNT(*) - COUNT(feudal_age_uptime) AS feudal_age_uptime_null,
    ROUND(100.0 * (COUNT(*) - COUNT(feudal_age_uptime)) / COUNT(*), 2) AS feudal_age_uptime_null_pct,
    COUNT(*) - COUNT(castle_age_uptime) AS castle_age_uptime_null,
    ROUND(100.0 * (COUNT(*) - COUNT(castle_age_uptime)) / COUNT(*), 2) AS castle_age_uptime_null_pct,
    COUNT(*) - COUNT(imperial_age_uptime) AS imperial_age_uptime_null,
    ROUND(100.0 * (COUNT(*) - COUNT(imperial_age_uptime)) / COUNT(*), 2) AS imperial_age_uptime_null_pct,
    COUNT(*) - COUNT(old_rating) AS old_rating_null,
    ROUND(100.0 * (COUNT(*) - COUNT(old_rating)) / COUNT(*), 2) AS old_rating_null_pct,
    COUNT(*) - COUNT(new_rating) AS new_rating_null,
    ROUND(100.0 * (COUNT(*) - COUNT(new_rating)) / COUNT(*), 2) AS new_rating_null_pct,
    COUNT(*) - COUNT(match_rating_diff) AS match_rating_diff_null,
    ROUND(100.0 * (COUNT(*) - COUNT(match_rating_diff)) / COUNT(*), 2) AS match_rating_diff_null_pct,
    COUNT(*) - COUNT(replay_summary_raw) AS replay_summary_raw_null,
    ROUND(100.0 * (COUNT(*) - COUNT(replay_summary_raw)) / COUNT(*), 2) AS replay_summary_raw_null_pct,
    COUNT(*) - COUNT(profile_id) AS profile_id_null,
    ROUND(100.0 * (COUNT(*) - COUNT(profile_id)) / COUNT(*), 2) AS profile_id_null_pct,
    COUNT(*) - COUNT(civ) AS civ_null,
    ROUND(100.0 * (COUNT(*) - COUNT(civ)) / COUNT(*), 2) AS civ_null_pct,
    COUNT(*) - COUNT(opening) AS opening_null,
    ROUND(100.0 * (COUNT(*) - COUNT(opening)) / COUNT(*), 2) AS opening_null_pct,
    COUNT(*) - COUNT(filename) AS filename_null,
    ROUND(100.0 * (COUNT(*) - COUNT(filename)) / COUNT(*), 2) AS filename_null_pct
FROM players_raw
```

### players_raw_null_cooccurrence

```sql
SELECT
    COUNT(*) FILTER (WHERE feudal_age_uptime IS NULL
        AND castle_age_uptime IS NULL
        AND imperial_age_uptime IS NULL
        AND opening IS NULL) AS all_four_null,
    COUNT(*) FILTER (WHERE feudal_age_uptime IS NOT NULL
        OR castle_age_uptime IS NOT NULL
        OR imperial_age_uptime IS NOT NULL
        OR opening IS NOT NULL) AS at_least_one_not_null,
    COUNT(*) AS total_rows
FROM players_raw
```

### winner_distribution

```sql
SELECT
    winner,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM players_raw
GROUP BY winner
ORDER BY cnt DESC
```

### num_players_distribution

```sql
SELECT
    num_players,
    COUNT(*) AS row_count,
    COUNT(DISTINCT game_id) AS distinct_match_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct,
    ROUND(
        100.0 * COUNT(DISTINCT game_id)
        / SUM(COUNT(DISTINCT game_id)) OVER(), 2
    ) AS distinct_match_pct
FROM matches_raw
GROUP BY num_players
ORDER BY num_players
```

### cat_matches_raw_map

```sql
SELECT map, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM matches_raw
GROUP BY map
ORDER BY cnt DESC
LIMIT 20
```

### cat_matches_raw_leaderboard

```sql
SELECT leaderboard, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM matches_raw
GROUP BY leaderboard
ORDER BY cnt DESC
LIMIT 50
```

### cat_matches_raw_game_type

```sql
SELECT game_type, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM matches_raw
GROUP BY game_type
ORDER BY cnt DESC
LIMIT 50
```

### cat_matches_raw_game_speed

```sql
SELECT game_speed, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM matches_raw
GROUP BY game_speed
ORDER BY cnt DESC
LIMIT 50
```

### cat_matches_raw_starting_age

```sql
SELECT starting_age, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM matches_raw
GROUP BY starting_age
ORDER BY cnt DESC
LIMIT 50
```

### cat_matches_raw_replay_enhanced

```sql
SELECT replay_enhanced, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM matches_raw
GROUP BY replay_enhanced
ORDER BY cnt DESC
LIMIT 10
```

### cat_matches_raw_mirror

```sql
SELECT mirror, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM matches_raw
GROUP BY mirror
ORDER BY cnt DESC
LIMIT 10
```

### cat_matches_raw_patch

```sql
SELECT patch, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM matches_raw
GROUP BY patch
ORDER BY cnt DESC
LIMIT 50
```

### cat_matches_raw_raw_match_type

```sql
SELECT raw_match_type, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM matches_raw
GROUP BY raw_match_type
ORDER BY cnt DESC
LIMIT 50
```

### cat_players_raw_civ

```sql
SELECT civ, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM players_raw
GROUP BY civ
ORDER BY cnt DESC
LIMIT 50
```

### cat_players_raw_opening

```sql
SELECT opening, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM players_raw
GROUP BY opening
ORDER BY cnt DESC
LIMIT 30
```

### cat_players_raw_team

```sql
SELECT team, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM players_raw
GROUP BY team
ORDER BY cnt DESC
LIMIT 20
```

### cat_players_raw_replay_summary_raw

```sql
SELECT replay_summary_raw, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM players_raw
GROUP BY replay_summary_raw
ORDER BY cnt DESC
LIMIT 20
```

### opening_nonnull_distribution

```sql
SELECT
    opening,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct_of_nonnull
FROM players_raw
WHERE opening IS NOT NULL
GROUP BY opening
ORDER BY cnt DESC
```

### numeric_matches_raw_duration_sec

```sql
SELECT
    COUNT(duration / 1e9) AS n_nonnull,
    COUNT(*) - COUNT(duration / 1e9) AS n_null,
    SUM(CASE WHEN duration / 1e9 = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN(duration / 1e9) AS min_val,
    MAX(duration / 1e9) AS max_val,
    ROUND(AVG(duration / 1e9), 2) AS mean_val,
    ROUND(MEDIAN(duration / 1e9), 2) AS median_val,
    ROUND(STDDEV(duration / 1e9), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY duration / 1e9), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY duration / 1e9), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration / 1e9), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY duration / 1e9), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration / 1e9), 2) AS p95
FROM matches_raw
```

### numeric_matches_raw_irl_duration_sec

```sql
SELECT
    COUNT(irl_duration / 1e9) AS n_nonnull,
    COUNT(*) - COUNT(irl_duration / 1e9) AS n_null,
    SUM(CASE WHEN irl_duration / 1e9 = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN(irl_duration / 1e9) AS min_val,
    MAX(irl_duration / 1e9) AS max_val,
    ROUND(AVG(irl_duration / 1e9), 2) AS mean_val,
    ROUND(MEDIAN(irl_duration / 1e9), 2) AS median_val,
    ROUND(STDDEV(irl_duration / 1e9), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY irl_duration / 1e9), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY irl_duration / 1e9), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY irl_duration / 1e9), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY irl_duration / 1e9), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY irl_duration / 1e9), 2) AS p95
FROM matches_raw
```

### numeric_matches_raw_avg_elo

```sql
SELECT
    COUNT(avg_elo) AS n_nonnull,
    COUNT(*) - COUNT(avg_elo) AS n_null,
    SUM(CASE WHEN avg_elo = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN(avg_elo) AS min_val,
    MAX(avg_elo) AS max_val,
    ROUND(AVG(avg_elo), 2) AS mean_val,
    ROUND(MEDIAN(avg_elo), 2) AS median_val,
    ROUND(STDDEV(avg_elo), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY avg_elo), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY avg_elo), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY avg_elo), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY avg_elo), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY avg_elo), 2) AS p95
FROM matches_raw
```

### numeric_matches_raw_team_0_elo

```sql
SELECT
    COUNT(team_0_elo) AS n_nonnull,
    COUNT(*) - COUNT(team_0_elo) AS n_null,
    SUM(CASE WHEN team_0_elo = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN(team_0_elo) AS min_val,
    MAX(team_0_elo) AS max_val,
    ROUND(AVG(team_0_elo), 2) AS mean_val,
    ROUND(MEDIAN(team_0_elo), 2) AS median_val,
    ROUND(STDDEV(team_0_elo), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY team_0_elo), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY team_0_elo), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY team_0_elo), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY team_0_elo), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY team_0_elo), 2) AS p95
FROM matches_raw
```

### numeric_matches_raw_team_1_elo

```sql
SELECT
    COUNT(team_1_elo) AS n_nonnull,
    COUNT(*) - COUNT(team_1_elo) AS n_null,
    SUM(CASE WHEN team_1_elo = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN(team_1_elo) AS min_val,
    MAX(team_1_elo) AS max_val,
    ROUND(AVG(team_1_elo), 2) AS mean_val,
    ROUND(MEDIAN(team_1_elo), 2) AS median_val,
    ROUND(STDDEV(team_1_elo), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY team_1_elo), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY team_1_elo), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY team_1_elo), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY team_1_elo), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY team_1_elo), 2) AS p95
FROM matches_raw
```

### numeric_matches_raw_raw_match_type

```sql
SELECT
    COUNT(raw_match_type) AS n_nonnull,
    COUNT(*) - COUNT(raw_match_type) AS n_null,
    SUM(CASE WHEN raw_match_type = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN(raw_match_type) AS min_val,
    MAX(raw_match_type) AS max_val,
    ROUND(AVG(raw_match_type), 2) AS mean_val,
    ROUND(MEDIAN(raw_match_type), 2) AS median_val,
    ROUND(STDDEV(raw_match_type), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY raw_match_type), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY raw_match_type), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY raw_match_type), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY raw_match_type), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY raw_match_type), 2) AS p95
FROM matches_raw
```

### numeric_matches_raw_patch

```sql
SELECT
    COUNT(patch) AS n_nonnull,
    COUNT(*) - COUNT(patch) AS n_null,
    SUM(CASE WHEN patch = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN(patch) AS min_val,
    MAX(patch) AS max_val,
    ROUND(AVG(patch), 2) AS mean_val,
    ROUND(MEDIAN(patch), 2) AS median_val,
    ROUND(STDDEV(patch), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY patch), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY patch), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY patch), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY patch), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY patch), 2) AS p95
FROM matches_raw
```

### numeric_players_raw_old_rating

```sql
SELECT
    COUNT(old_rating) AS n_nonnull,
    COUNT(*) - COUNT(old_rating) AS n_null,
    SUM(CASE WHEN old_rating = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN(old_rating) AS min_val,
    MAX(old_rating) AS max_val,
    ROUND(AVG(old_rating), 2) AS mean_val,
    ROUND(MEDIAN(old_rating), 2) AS median_val,
    ROUND(STDDEV(old_rating), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY old_rating), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY old_rating), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY old_rating), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY old_rating), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY old_rating), 2) AS p95
FROM players_raw
```

### numeric_players_raw_new_rating

```sql
SELECT
    COUNT(new_rating) AS n_nonnull,
    COUNT(*) - COUNT(new_rating) AS n_null,
    SUM(CASE WHEN new_rating = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN(new_rating) AS min_val,
    MAX(new_rating) AS max_val,
    ROUND(AVG(new_rating), 2) AS mean_val,
    ROUND(MEDIAN(new_rating), 2) AS median_val,
    ROUND(STDDEV(new_rating), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY new_rating), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY new_rating), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY new_rating), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY new_rating), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY new_rating), 2) AS p95
FROM players_raw
```

### numeric_players_raw_match_rating_diff

```sql
SELECT
    COUNT(match_rating_diff) AS n_nonnull,
    COUNT(*) - COUNT(match_rating_diff) AS n_null,
    SUM(CASE WHEN match_rating_diff = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN(match_rating_diff) AS min_val,
    MAX(match_rating_diff) AS max_val,
    ROUND(AVG(match_rating_diff), 2) AS mean_val,
    ROUND(MEDIAN(match_rating_diff), 2) AS median_val,
    ROUND(STDDEV(match_rating_diff), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY match_rating_diff), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY match_rating_diff), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY match_rating_diff), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY match_rating_diff), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY match_rating_diff), 2) AS p95
FROM players_raw
```

### numeric_players_raw_feudal_age_uptime

```sql
SELECT
    COUNT(feudal_age_uptime) AS n_nonnull,
    COUNT(*) - COUNT(feudal_age_uptime) AS n_null,
    SUM(CASE WHEN feudal_age_uptime = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN(feudal_age_uptime) AS min_val,
    MAX(feudal_age_uptime) AS max_val,
    ROUND(AVG(feudal_age_uptime), 2) AS mean_val,
    ROUND(MEDIAN(feudal_age_uptime), 2) AS median_val,
    ROUND(STDDEV(feudal_age_uptime), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY feudal_age_uptime), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY feudal_age_uptime), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY feudal_age_uptime), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY feudal_age_uptime), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY feudal_age_uptime), 2) AS p95
FROM players_raw
```

### numeric_players_raw_castle_age_uptime

```sql
SELECT
    COUNT(castle_age_uptime) AS n_nonnull,
    COUNT(*) - COUNT(castle_age_uptime) AS n_null,
    SUM(CASE WHEN castle_age_uptime = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN(castle_age_uptime) AS min_val,
    MAX(castle_age_uptime) AS max_val,
    ROUND(AVG(castle_age_uptime), 2) AS mean_val,
    ROUND(MEDIAN(castle_age_uptime), 2) AS median_val,
    ROUND(STDDEV(castle_age_uptime), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY castle_age_uptime), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY castle_age_uptime), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY castle_age_uptime), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY castle_age_uptime), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY castle_age_uptime), 2) AS p95
FROM players_raw
```

### numeric_players_raw_imperial_age_uptime

```sql
SELECT
    COUNT(imperial_age_uptime) AS n_nonnull,
    COUNT(*) - COUNT(imperial_age_uptime) AS n_null,
    SUM(CASE WHEN imperial_age_uptime = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN(imperial_age_uptime) AS min_val,
    MAX(imperial_age_uptime) AS max_val,
    ROUND(AVG(imperial_age_uptime), 2) AS mean_val,
    ROUND(MEDIAN(imperial_age_uptime), 2) AS median_val,
    ROUND(STDDEV(imperial_age_uptime), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY imperial_age_uptime), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY imperial_age_uptime), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY imperial_age_uptime), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY imperial_age_uptime), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY imperial_age_uptime), 2) AS p95
FROM players_raw
```

### skew_kurt_matches_duration_sec

```sql
SELECT
    ROUND(SKEWNESS(duration / 1e9), 4) AS skewness,
    ROUND(KURTOSIS(duration / 1e9), 4) AS kurtosis,
    COUNT(duration / 1e9) AS n_nonnull
FROM matches_raw
```

### skew_kurt_matches_irl_duration_sec

```sql
SELECT
    ROUND(SKEWNESS(irl_duration / 1e9), 4) AS skewness,
    ROUND(KURTOSIS(irl_duration / 1e9), 4) AS kurtosis,
    COUNT(irl_duration / 1e9) AS n_nonnull
FROM matches_raw
```

### skew_kurt_matches_avg_elo

```sql
SELECT
    ROUND(SKEWNESS(avg_elo), 4) AS skewness,
    ROUND(KURTOSIS(avg_elo), 4) AS kurtosis,
    COUNT(avg_elo) AS n_nonnull
FROM matches_raw
```

### skew_kurt_matches_team_0_elo

```sql
SELECT
    ROUND(SKEWNESS(team_0_elo), 4) AS skewness,
    ROUND(KURTOSIS(team_0_elo), 4) AS kurtosis,
    COUNT(team_0_elo) AS n_nonnull
FROM matches_raw
```

### skew_kurt_matches_team_1_elo

```sql
SELECT
    ROUND(SKEWNESS(team_1_elo), 4) AS skewness,
    ROUND(KURTOSIS(team_1_elo), 4) AS kurtosis,
    COUNT(team_1_elo) AS n_nonnull
FROM matches_raw
```

### skew_kurt_matches_raw_match_type

```sql
SELECT
    ROUND(SKEWNESS(raw_match_type), 4) AS skewness,
    ROUND(KURTOSIS(raw_match_type), 4) AS kurtosis,
    COUNT(raw_match_type) AS n_nonnull
FROM matches_raw
```

### skew_kurt_matches_patch

```sql
SELECT
    ROUND(SKEWNESS(patch), 4) AS skewness,
    ROUND(KURTOSIS(patch), 4) AS kurtosis,
    COUNT(patch) AS n_nonnull
FROM matches_raw
```

### skew_kurt_players_old_rating

```sql
SELECT
    ROUND(SKEWNESS(old_rating), 4) AS skewness,
    ROUND(KURTOSIS(old_rating), 4) AS kurtosis,
    COUNT(old_rating) AS n_nonnull
FROM players_raw
```

### skew_kurt_players_new_rating

```sql
SELECT
    ROUND(SKEWNESS(new_rating), 4) AS skewness,
    ROUND(KURTOSIS(new_rating), 4) AS kurtosis,
    COUNT(new_rating) AS n_nonnull
FROM players_raw
```

### skew_kurt_players_match_rating_diff

```sql
SELECT
    ROUND(SKEWNESS(match_rating_diff), 4) AS skewness,
    ROUND(KURTOSIS(match_rating_diff), 4) AS kurtosis,
    COUNT(match_rating_diff) AS n_nonnull
FROM players_raw
```

### skew_kurt_players_feudal_age_uptime

```sql
SELECT
    ROUND(SKEWNESS(feudal_age_uptime), 4) AS skewness,
    ROUND(KURTOSIS(feudal_age_uptime), 4) AS kurtosis,
    COUNT(feudal_age_uptime) AS n_nonnull
FROM players_raw
```

### skew_kurt_players_castle_age_uptime

```sql
SELECT
    ROUND(SKEWNESS(castle_age_uptime), 4) AS skewness,
    ROUND(KURTOSIS(castle_age_uptime), 4) AS kurtosis,
    COUNT(castle_age_uptime) AS n_nonnull
FROM players_raw
```

### skew_kurt_players_imperial_age_uptime

```sql
SELECT
    ROUND(SKEWNESS(imperial_age_uptime), 4) AS skewness,
    ROUND(KURTOSIS(imperial_age_uptime), 4) AS kurtosis,
    COUNT(imperial_age_uptime) AS n_nonnull
FROM players_raw
```

### profile_id_range

```sql
SELECT
    COUNT(profile_id) AS n_nonnull,
    COUNT(*) - COUNT(profile_id) AS n_null,
    MIN(profile_id) AS min_val,
    MAX(profile_id) AS max_val
FROM players_raw
```

### hist_duration_sec

```sql
SELECT
    FLOOR(duration / 1e9 / 60) * 60 AS bin,
    COUNT(*) AS cnt
FROM matches_raw
WHERE duration / 1e9 IS NOT NULL
GROUP BY bin
ORDER BY bin
```

### hist_irl_duration_sec

```sql
SELECT
    FLOOR(irl_duration / 1e9 / 60) * 60 AS bin,
    COUNT(*) AS cnt
FROM matches_raw
WHERE irl_duration / 1e9 IS NOT NULL
GROUP BY bin
ORDER BY bin
```

### hist_avg_elo

```sql
SELECT
    FLOOR(avg_elo / 50) * 50 AS bin,
    COUNT(*) AS cnt
FROM matches_raw
WHERE avg_elo IS NOT NULL
GROUP BY bin
ORDER BY bin
```

### hist_old_rating

```sql
SELECT
    FLOOR(old_rating / 50) * 50 AS bin,
    COUNT(*) AS cnt
FROM players_raw
WHERE old_rating IS NOT NULL
GROUP BY bin
ORDER BY bin
```

### hist_new_rating

```sql
SELECT
    FLOOR(new_rating / 50) * 50 AS bin,
    COUNT(*) AS cnt
FROM players_raw
WHERE new_rating IS NOT NULL
GROUP BY bin
ORDER BY bin
```

### hist_match_rating_diff

```sql
SELECT
    FLOOR(match_rating_diff / 5) * 5 AS bin,
    COUNT(*) AS cnt
FROM players_raw
WHERE match_rating_diff IS NOT NULL
GROUP BY bin
ORDER BY bin
```

### hist_feudal_age_uptime

```sql
SELECT
    FLOOR(feudal_age_uptime / 10) * 10 AS bin,
    COUNT(*) AS cnt
FROM players_raw
WHERE feudal_age_uptime IS NOT NULL
GROUP BY bin
ORDER BY bin
```

### hist_castle_age_uptime

```sql
SELECT
    FLOOR(castle_age_uptime / 10) * 10 AS bin,
    COUNT(*) AS cnt
FROM players_raw
WHERE castle_age_uptime IS NOT NULL
GROUP BY bin
ORDER BY bin
```

### hist_imperial_age_uptime

```sql
SELECT
    FLOOR(imperial_age_uptime / 10) * 10 AS bin,
    COUNT(*) AS cnt
FROM players_raw
WHERE imperial_age_uptime IS NOT NULL
GROUP BY bin
ORDER BY bin
```

### elo_sentinel_counts

```sql
SELECT
    COUNT(*) FILTER (WHERE team_0_elo < 0)   AS team_0_elo_neg,
    COUNT(*) FILTER (WHERE team_1_elo < 0)   AS team_1_elo_neg,
    COUNT(*)                                  AS total_rows
FROM matches_raw
```

### elo_neg_distinct_values

```sql
SELECT DISTINCT team_0_elo AS elo_val FROM matches_raw WHERE team_0_elo < 0
UNION
SELECT DISTINCT team_1_elo AS elo_val FROM matches_raw WHERE team_1_elo < 0
ORDER BY elo_val
```

### numeric_matches_team_0_elo_no_sentinel

```sql
SELECT
    COUNT(team_0_elo) AS n_nonnull,
    COUNT(*) - COUNT(team_0_elo) AS n_null,
    SUM(CASE WHEN team_0_elo = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN(team_0_elo) AS min_val,
    MAX(team_0_elo) AS max_val,
    ROUND(AVG(team_0_elo), 2) AS mean_val,
    ROUND(MEDIAN(team_0_elo), 2) AS median_val,
    ROUND(STDDEV(team_0_elo), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY team_0_elo), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY team_0_elo), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY team_0_elo), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY team_0_elo), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY team_0_elo), 2) AS p95
FROM matches_raw
WHERE team_0_elo != -1.0
-- Note: ELO=0 rows (4,824 for team_0_elo, 192 for team_1_elo) are NOT excluded here;
-- only the -1.0 sentinel (unranked marker) is excluded. ELO=0 may represent valid
-- entries and requires separate investigation if needed.
```

### numeric_matches_team_1_elo_no_sentinel

```sql
SELECT
    COUNT(team_1_elo) AS n_nonnull,
    COUNT(*) - COUNT(team_1_elo) AS n_null,
    SUM(CASE WHEN team_1_elo = 0 THEN 1 ELSE 0 END) AS n_zero,
    MIN(team_1_elo) AS min_val,
    MAX(team_1_elo) AS max_val,
    ROUND(AVG(team_1_elo), 2) AS mean_val,
    ROUND(MEDIAN(team_1_elo), 2) AS median_val,
    ROUND(STDDEV(team_1_elo), 2) AS stddev_val,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY team_1_elo), 2) AS p05,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY team_1_elo), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY team_1_elo), 2) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY team_1_elo), 2) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY team_1_elo), 2) AS p95
FROM matches_raw
WHERE team_1_elo != -1.0
-- Note: ELO=0 rows (4,824 for team_0_elo, 192 for team_1_elo) are NOT excluded here;
-- only the -1.0 sentinel (unranked marker) is excluded. ELO=0 may represent valid
-- entries and requires separate investigation if needed.
```

### temporal_range

```sql
SELECT
    MIN(started_timestamp) AS earliest,
    MAX(started_timestamp) AS latest,
    COUNT(DISTINCT DATE_TRUNC('month', started_timestamp)) AS distinct_months,
    COUNT(DISTINCT DATE_TRUNC('week', started_timestamp)) AS distinct_weeks
FROM matches_raw
```

### monthly_match_counts

```sql
SELECT
    DATE_TRUNC('month', started_timestamp) AS month,
    COUNT(*) AS match_count
FROM matches_raw
WHERE started_timestamp IS NOT NULL
GROUP BY month
ORDER BY month
```

### orphan_detection

```sql
SELECT
    'players_without_match' AS check_name,
    COUNT(DISTINCT p.game_id) AS cnt
FROM players_raw p
LEFT JOIN matches_raw m ON p.game_id = m.game_id
WHERE m.game_id IS NULL
UNION ALL
SELECT
    'matches_without_players' AS check_name,
    COUNT(DISTINCT m.game_id) AS cnt
FROM matches_raw m
LEFT JOIN players_raw p ON m.game_id = p.game_id
WHERE p.game_id IS NULL
```

### players_per_match

```sql
SELECT
    player_count,
    COUNT(*) AS match_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM (
    SELECT game_id, COUNT(*) AS player_count
    FROM players_raw
    GROUP BY game_id
)
GROUP BY player_count
ORDER BY player_count
```

### duplicate_check_matches

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT CAST(game_id AS VARCHAR)) AS distinct_game_ids,
    COUNT(*) - COUNT(DISTINCT CAST(game_id AS VARCHAR)) AS duplicate_rows
FROM matches_raw
```

### duplicate_check_players

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT CAST(game_id AS VARCHAR) || '_' || COALESCE(CAST(profile_id AS VARCHAR), '__NULL__'))
        AS distinct_game_player_pairs,
    COUNT(*) - COUNT(DISTINCT CAST(game_id AS VARCHAR) || '_' || COALESCE(CAST(profile_id AS VARCHAR), '__NULL__'))
        AS duplicate_rows
FROM players_raw
```

### uniqueness_matches_map

```sql
SELECT
    'map' AS column_name,
    COUNT(DISTINCT map) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(map) AS nonnull_rows,
    ROUND(COUNT(DISTINCT map)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT map)::DOUBLE / NULLIF(COUNT(map), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM matches_raw
```

### uniqueness_matches_started_timestamp

```sql
SELECT
    'started_timestamp' AS column_name,
    COUNT(DISTINCT started_timestamp) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(started_timestamp) AS nonnull_rows,
    ROUND(COUNT(DISTINCT started_timestamp)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT started_timestamp)::DOUBLE / NULLIF(COUNT(started_timestamp), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM matches_raw
```

### uniqueness_matches_duration

```sql
SELECT
    'duration' AS column_name,
    COUNT(DISTINCT duration) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(duration) AS nonnull_rows,
    ROUND(COUNT(DISTINCT duration)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT duration)::DOUBLE / NULLIF(COUNT(duration), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM matches_raw
```

### uniqueness_matches_irl_duration

```sql
SELECT
    'irl_duration' AS column_name,
    COUNT(DISTINCT irl_duration) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(irl_duration) AS nonnull_rows,
    ROUND(COUNT(DISTINCT irl_duration)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT irl_duration)::DOUBLE / NULLIF(COUNT(irl_duration), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM matches_raw
```

### uniqueness_matches_game_id

```sql
SELECT
    'game_id' AS column_name,
    COUNT(DISTINCT game_id) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(game_id) AS nonnull_rows,
    ROUND(COUNT(DISTINCT game_id)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT game_id)::DOUBLE / NULLIF(COUNT(game_id), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM matches_raw
```

### uniqueness_matches_avg_elo

```sql
SELECT
    'avg_elo' AS column_name,
    COUNT(DISTINCT avg_elo) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(avg_elo) AS nonnull_rows,
    ROUND(COUNT(DISTINCT avg_elo)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT avg_elo)::DOUBLE / NULLIF(COUNT(avg_elo), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM matches_raw
```

### uniqueness_matches_num_players

```sql
SELECT
    'num_players' AS column_name,
    COUNT(DISTINCT num_players) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(num_players) AS nonnull_rows,
    ROUND(COUNT(DISTINCT num_players)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT num_players)::DOUBLE / NULLIF(COUNT(num_players), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM matches_raw
```

### uniqueness_matches_team_0_elo

```sql
SELECT
    'team_0_elo' AS column_name,
    COUNT(DISTINCT team_0_elo) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(team_0_elo) AS nonnull_rows,
    ROUND(COUNT(DISTINCT team_0_elo)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT team_0_elo)::DOUBLE / NULLIF(COUNT(team_0_elo), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM matches_raw
```

### uniqueness_matches_team_1_elo

```sql
SELECT
    'team_1_elo' AS column_name,
    COUNT(DISTINCT team_1_elo) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(team_1_elo) AS nonnull_rows,
    ROUND(COUNT(DISTINCT team_1_elo)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT team_1_elo)::DOUBLE / NULLIF(COUNT(team_1_elo), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM matches_raw
```

### uniqueness_matches_replay_enhanced

```sql
SELECT
    'replay_enhanced' AS column_name,
    COUNT(DISTINCT replay_enhanced) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(replay_enhanced) AS nonnull_rows,
    ROUND(COUNT(DISTINCT replay_enhanced)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT replay_enhanced)::DOUBLE / NULLIF(COUNT(replay_enhanced), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM matches_raw
```

### uniqueness_matches_leaderboard

```sql
SELECT
    'leaderboard' AS column_name,
    COUNT(DISTINCT leaderboard) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(leaderboard) AS nonnull_rows,
    ROUND(COUNT(DISTINCT leaderboard)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT leaderboard)::DOUBLE / NULLIF(COUNT(leaderboard), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM matches_raw
```

### uniqueness_matches_mirror

```sql
SELECT
    'mirror' AS column_name,
    COUNT(DISTINCT mirror) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(mirror) AS nonnull_rows,
    ROUND(COUNT(DISTINCT mirror)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT mirror)::DOUBLE / NULLIF(COUNT(mirror), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM matches_raw
```

### uniqueness_matches_patch

```sql
SELECT
    'patch' AS column_name,
    COUNT(DISTINCT patch) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(patch) AS nonnull_rows,
    ROUND(COUNT(DISTINCT patch)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT patch)::DOUBLE / NULLIF(COUNT(patch), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM matches_raw
```

### uniqueness_matches_raw_match_type

```sql
SELECT
    'raw_match_type' AS column_name,
    COUNT(DISTINCT raw_match_type) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(raw_match_type) AS nonnull_rows,
    ROUND(COUNT(DISTINCT raw_match_type)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT raw_match_type)::DOUBLE / NULLIF(COUNT(raw_match_type), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM matches_raw
```

### uniqueness_matches_game_type

```sql
SELECT
    'game_type' AS column_name,
    COUNT(DISTINCT game_type) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(game_type) AS nonnull_rows,
    ROUND(COUNT(DISTINCT game_type)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT game_type)::DOUBLE / NULLIF(COUNT(game_type), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM matches_raw
```

### uniqueness_matches_game_speed

```sql
SELECT
    'game_speed' AS column_name,
    COUNT(DISTINCT game_speed) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(game_speed) AS nonnull_rows,
    ROUND(COUNT(DISTINCT game_speed)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT game_speed)::DOUBLE / NULLIF(COUNT(game_speed), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM matches_raw
```

### uniqueness_matches_starting_age

```sql
SELECT
    'starting_age' AS column_name,
    COUNT(DISTINCT starting_age) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(starting_age) AS nonnull_rows,
    ROUND(COUNT(DISTINCT starting_age)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT starting_age)::DOUBLE / NULLIF(COUNT(starting_age), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM matches_raw
```

### uniqueness_matches_filename

```sql
SELECT
    'filename' AS column_name,
    COUNT(DISTINCT filename) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(filename) AS nonnull_rows,
    ROUND(COUNT(DISTINCT filename)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT filename)::DOUBLE / NULLIF(COUNT(filename), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM matches_raw
```

### uniqueness_players_winner

```sql
SELECT
    'winner' AS column_name,
    COUNT(DISTINCT winner) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(winner) AS nonnull_rows,
    ROUND(COUNT(DISTINCT winner)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT winner)::DOUBLE / NULLIF(COUNT(winner), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM players_raw
```

### uniqueness_players_game_id

```sql
SELECT
    'game_id' AS column_name,
    COUNT(DISTINCT game_id) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(game_id) AS nonnull_rows,
    ROUND(COUNT(DISTINCT game_id)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT game_id)::DOUBLE / NULLIF(COUNT(game_id), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM players_raw
```

### uniqueness_players_team

```sql
SELECT
    'team' AS column_name,
    COUNT(DISTINCT team) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(team) AS nonnull_rows,
    ROUND(COUNT(DISTINCT team)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT team)::DOUBLE / NULLIF(COUNT(team), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM players_raw
```

### uniqueness_players_feudal_age_uptime

```sql
SELECT
    'feudal_age_uptime' AS column_name,
    COUNT(DISTINCT feudal_age_uptime) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(feudal_age_uptime) AS nonnull_rows,
    ROUND(COUNT(DISTINCT feudal_age_uptime)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT feudal_age_uptime)::DOUBLE / NULLIF(COUNT(feudal_age_uptime), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM players_raw
```

### uniqueness_players_castle_age_uptime

```sql
SELECT
    'castle_age_uptime' AS column_name,
    COUNT(DISTINCT castle_age_uptime) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(castle_age_uptime) AS nonnull_rows,
    ROUND(COUNT(DISTINCT castle_age_uptime)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT castle_age_uptime)::DOUBLE / NULLIF(COUNT(castle_age_uptime), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM players_raw
```

### uniqueness_players_imperial_age_uptime

```sql
SELECT
    'imperial_age_uptime' AS column_name,
    COUNT(DISTINCT imperial_age_uptime) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(imperial_age_uptime) AS nonnull_rows,
    ROUND(COUNT(DISTINCT imperial_age_uptime)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT imperial_age_uptime)::DOUBLE / NULLIF(COUNT(imperial_age_uptime), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM players_raw
```

### uniqueness_players_old_rating

```sql
SELECT
    'old_rating' AS column_name,
    COUNT(DISTINCT old_rating) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(old_rating) AS nonnull_rows,
    ROUND(COUNT(DISTINCT old_rating)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT old_rating)::DOUBLE / NULLIF(COUNT(old_rating), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM players_raw
```

### uniqueness_players_new_rating

```sql
SELECT
    'new_rating' AS column_name,
    COUNT(DISTINCT new_rating) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(new_rating) AS nonnull_rows,
    ROUND(COUNT(DISTINCT new_rating)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT new_rating)::DOUBLE / NULLIF(COUNT(new_rating), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM players_raw
```

### uniqueness_players_match_rating_diff

```sql
SELECT
    'match_rating_diff' AS column_name,
    COUNT(DISTINCT match_rating_diff) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(match_rating_diff) AS nonnull_rows,
    ROUND(COUNT(DISTINCT match_rating_diff)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT match_rating_diff)::DOUBLE / NULLIF(COUNT(match_rating_diff), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM players_raw
```

### uniqueness_players_replay_summary_raw

```sql
SELECT
    'replay_summary_raw' AS column_name,
    COUNT(DISTINCT replay_summary_raw) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(replay_summary_raw) AS nonnull_rows,
    ROUND(COUNT(DISTINCT replay_summary_raw)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT replay_summary_raw)::DOUBLE / NULLIF(COUNT(replay_summary_raw), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM players_raw
```

### uniqueness_players_profile_id

```sql
SELECT
    'profile_id' AS column_name,
    COUNT(DISTINCT profile_id) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(profile_id) AS nonnull_rows,
    ROUND(COUNT(DISTINCT profile_id)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT profile_id)::DOUBLE / NULLIF(COUNT(profile_id), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM players_raw
```

### uniqueness_players_civ

```sql
SELECT
    'civ' AS column_name,
    COUNT(DISTINCT civ) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(civ) AS nonnull_rows,
    ROUND(COUNT(DISTINCT civ)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT civ)::DOUBLE / NULLIF(COUNT(civ), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM players_raw
```

### uniqueness_players_opening

```sql
SELECT
    'opening' AS column_name,
    COUNT(DISTINCT opening) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(opening) AS nonnull_rows,
    ROUND(COUNT(DISTINCT opening)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT opening)::DOUBLE / NULLIF(COUNT(opening), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM players_raw
```

### uniqueness_players_filename

```sql
SELECT
    'filename' AS column_name,
    COUNT(DISTINCT filename) AS cardinality,
    COUNT(*) AS total_rows,
    COUNT(filename) AS nonnull_rows,
    ROUND(COUNT(DISTINCT filename)::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio,
    ROUND(COUNT(DISTINCT filename)::DOUBLE / NULLIF(COUNT(filename), 0)::DOUBLE, 6) AS nonnull_uniqueness_ratio
FROM players_raw
```

## Key Findings

- matches_raw total rows: 30,690,651
- players_raw total rows: 107,627,584

### Winner Distribution
- winner=False: 53,816,397 (50.0%)
- winner=True: 53,811,187 (50.0%)

### num_players Distribution
- num_players=1: rows=39 (0.0%), distinct_matches=39 (0.0%)
- num_players=2: rows=18,586,063 (60.56%), distinct_matches=18,586,063 (60.56%)
- num_players=3: rows=350 (0.0%), distinct_matches=350 (0.0%)
- num_players=4: rows=5,057,269 (16.48%), distinct_matches=5,057,269 (16.48%)
- num_players=5: rows=327 (0.0%), distinct_matches=327 (0.0%)
- num_players=6: rows=2,736,203 (8.92%), distinct_matches=2,736,203 (8.92%)
- num_players=7: rows=651 (0.0%), distinct_matches=651 (0.0%)
- num_players=8: rows=4,309,749 (14.04%), distinct_matches=4,309,749 (14.04%)
