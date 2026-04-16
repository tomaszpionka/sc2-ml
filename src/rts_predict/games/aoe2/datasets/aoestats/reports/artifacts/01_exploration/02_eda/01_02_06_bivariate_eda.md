# Step 01_02_06 -- Bivariate EDA -- aoestats

**Generated:** 2026-04-15
**Dataset:** aoestats (matches_raw: 30,690,651 rows; players_raw: 107,627,584 rows)
**Predecessor:** 01_02_05 (Univariate Visualizations)

## Leakage Resolution: match_rating_diff

**Status: PRE_GAME**

match_rating_diff does NOT correlate with new_rating - old_rating (Pearson r=0.0541). Likely a pre-game feature.

- Pearson r: 0.054070
- OLS slope: 0.017226
- OLS intercept: -0.311041
- R-squared: 0.002924
- Exact match (tolerance 0.01): 712,331 / 107,620,495 (0.66%)

## Plot Index

| # | Title | Filename | Temporal Annotation |
|---|-------|----------|---------------------|
| 1 | match_rating_diff_leakage_scatter | `01_02_06_match_rating_diff_leakage_scatter.png` | LEAKAGE STATUS: PRE_GAME (Inv. #3) |
| 2 | old_rating_by_winner | `01_02_06_old_rating_by_winner.png` | N/A (pre-game) |
| 3 | elo_by_winner | `01_02_06_elo_by_winner.png` | N/A (pre-game) |
| 4 | duration_by_winner | `01_02_06_duration_by_winner.png` | POST-GAME (Inv. #3) |
| 5 | numeric_by_winner | `01_02_06_numeric_by_winner.png` | N/A (pre-game features) |
| 6 | opening_winrate | `01_02_06_opening_winrate.png` | IN-GAME (Inv. #3) |
| 7 | age_uptime_by_winner | `01_02_06_age_uptime_by_winner.png` | IN-GAME (Inv. #3) |
| 8 | spearman_correlation | `01_02_06_spearman_correlation.png` | Mixed -- includes post-game columns |

## Statistical Tests -- Exploratory Discrimination

> PRE-GAME features. Effect sizes measure discriminative power at prediction time. Exploratory only (Tukey-style EDA). No multiple comparison correction applied.

### old_rating_by_winner
- **Temporal status:** PRE-GAME
- **Mann-Whitney U:** 3,174,601,597,960
- **p-value:** 1.7691e-207
- **Rank-biserial r (Wendt 1972):** -0.0159
- **n(winner):** 2,498,214 | **n(loser):** 2,501,786
- **Median(winner):** 1070.00 | **Median(loser):** 1063.00
- **Note:** RESERVOIR(5_000_000); SE(r)=0.00045

### match_rating_diff_by_winner
- **Temporal status:** PRE-GAME (confirmed in T03 leakage test)
- **Mann-Whitney U:** 3,762,711,920,606
- **p-value:** 0.0000e+00
- **Rank-biserial r (Wendt 1972):** -0.2041
- **n(winner):** 2,500,163 | **n(loser):** 2,499,835
- **Median(winner):** 4.00 | **Median(loser):** -4.00
- **Note:** RESERVOIR(5_000_000); SE(r)=0.00045


## SQL Queries

### leakage_exact_match_count

```sql
SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN ABS(match_rating_diff - (new_rating - old_rating)) < 0.01
        THEN 1 ELSE 0 END) AS exact_match_count,
    ROUND(100.0 * SUM(CASE WHEN ABS(match_rating_diff - (new_rating - old_rating)) < 0.01
        THEN 1 ELSE 0 END) / COUNT(*), 4) AS exact_match_pct
FROM players_raw
WHERE match_rating_diff IS NOT NULL
  AND old_rating > 0
  AND new_rating > 0
```

### leakage_scatter_sample

```sql
SELECT
    match_rating_diff,
    CAST(new_rating - old_rating AS DOUBLE) AS rating_delta
FROM players_raw
WHERE match_rating_diff IS NOT NULL
  AND old_rating > 0
  AND new_rating > 0
USING SAMPLE RESERVOIR(200000)
```

### match_rating_diff_raw_by_winner

```sql
SELECT winner, match_rating_diff
FROM players_raw
WHERE match_rating_diff IS NOT NULL
  AND winner IS NOT NULL
USING SAMPLE RESERVOIR(5000000)
```

### old_rating_by_winner_buckets

```sql
SELECT
    winner,
    FLOOR(old_rating / 25) * 25 AS bin,
    COUNT(*) AS cnt
FROM players_raw
WHERE old_rating > 0
GROUP BY winner, bin
ORDER BY winner, bin
```

### old_rating_by_winner_stats

```sql
SELECT
    winner,
    COUNT(*) AS n,
    ROUND(AVG(old_rating), 2) AS mean_val,
    ROUND(MEDIAN(old_rating), 2) AS median_val,
    ROUND(STDDEV(old_rating), 2) AS stddev_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY old_rating) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY old_rating) AS p75
FROM players_raw
WHERE old_rating > 0
GROUP BY winner
ORDER BY winner
```

### old_rating_raw_by_winner

```sql
SELECT winner, old_rating
FROM players_raw
WHERE old_rating >= 0
  AND winner IS NOT NULL
USING SAMPLE RESERVOIR(5000000)
```

### elo_diff_by_winning_team

```sql
WITH match_winner AS (
    SELECT
        game_id,
        MAX(CASE WHEN winner = true THEN team END) AS winning_team
    FROM players_raw
    GROUP BY game_id
)
SELECT
    mw.winning_team,
    FLOOR((m.team_0_elo - m.team_1_elo) / 10) * 10 AS elo_diff_bin,
    COUNT(*) AS cnt
FROM matches_raw m
JOIN match_winner mw ON m.game_id = mw.game_id
WHERE m.team_0_elo > 0
  AND m.team_1_elo > 0
GROUP BY mw.winning_team, elo_diff_bin
ORDER BY mw.winning_team, elo_diff_bin
```

### elo_by_winning_team_stats

```sql
WITH match_winner AS (
    SELECT
        game_id,
        MAX(CASE WHEN winner = true THEN team END) AS winning_team
    FROM players_raw
    GROUP BY game_id
)
SELECT
    mw.winning_team,
    ROUND(AVG(m.team_0_elo), 2) AS mean_t0_elo,
    ROUND(AVG(m.team_1_elo), 2) AS mean_t1_elo,
    ROUND(AVG(m.avg_elo), 2) AS mean_avg_elo,
    ROUND(AVG(m.team_0_elo - m.team_1_elo), 2) AS mean_elo_diff,
    COUNT(*) AS n
FROM matches_raw m
JOIN match_winner mw ON m.game_id = mw.game_id
WHERE m.team_0_elo > 0
  AND m.team_1_elo > 0
GROUP BY mw.winning_team
ORDER BY mw.winning_team
```

### duration_by_winner_buckets

```sql
WITH match_winner AS (
    SELECT
        game_id,
        MAX(CASE WHEN winner = true THEN team END) AS winning_team
    FROM players_raw
    GROUP BY game_id
)
SELECT
    mw.winning_team,
    FLOOR((m.duration / 1e9) / 60) AS dur_min_bin,
    COUNT(*) AS cnt
FROM matches_raw m
JOIN match_winner mw ON m.game_id = mw.game_id
WHERE m.duration > 0
  AND (m.duration / 1e9) <= 4714.1
GROUP BY mw.winning_team, dur_min_bin
ORDER BY mw.winning_team, dur_min_bin
```

### duration_by_winner_stats

```sql
WITH match_winner AS (
    SELECT
        game_id,
        MAX(CASE WHEN winner = true THEN team END) AS winning_team
    FROM players_raw
    GROUP BY game_id
)
SELECT
    mw.winning_team,
    ROUND(AVG(m.duration / 1e9), 2) AS mean_dur_sec,
    ROUND(MEDIAN(m.duration / 1e9), 2) AS median_dur_sec,
    COUNT(*) AS n
FROM matches_raw m
JOIN match_winner mw ON m.game_id = mw.game_id
WHERE m.duration > 0
GROUP BY mw.winning_team
ORDER BY mw.winning_team
```

### numeric_pregame_by_winner_stats

```sql
SELECT
    'old_rating' AS feature,
    winner,
    COUNT(*) AS n,
    ROUND(AVG(old_rating), 2) AS mean_val,
    ROUND(MEDIAN(old_rating), 2) AS median_val,
    ROUND(STDDEV(old_rating), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY old_rating) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY old_rating) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY old_rating) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY old_rating) AS p95
FROM players_raw
WHERE old_rating > 0
GROUP BY winner
ORDER BY winner
```

### match_elo_by_winner_stats

```sql
WITH match_winner AS (
    SELECT game_id,
        MAX(CASE WHEN winner = true THEN team END) AS winning_team
    FROM players_raw
    GROUP BY game_id
)
SELECT
    feature,
    winning_team AS winner_team,
    COUNT(*) AS n,
    ROUND(AVG(val), 2) AS mean_val,
    ROUND(MEDIAN(val), 2) AS median_val,
    ROUND(STDDEV(val), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY val) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY val) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY val) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY val) AS p95
FROM (
    SELECT mw.winning_team, 'avg_elo' AS feature, m.avg_elo AS val
    FROM matches_raw m JOIN match_winner mw ON m.game_id = mw.game_id
    WHERE m.avg_elo > 0
    UNION ALL
    SELECT mw.winning_team, 'team_0_elo', m.team_0_elo
    FROM matches_raw m JOIN match_winner mw ON m.game_id = mw.game_id
    WHERE m.team_0_elo > 0
    UNION ALL
    SELECT mw.winning_team, 'team_1_elo', m.team_1_elo
    FROM matches_raw m JOIN match_winner mw ON m.game_id = mw.game_id
    WHERE m.team_1_elo > 0
) sub
GROUP BY feature, winning_team
ORDER BY feature, winning_team
```

### opening_winrate

```sql
SELECT
    opening,
    COUNT(*) AS total_games,
    SUM(CASE WHEN winner = true THEN 1 ELSE 0 END) AS wins,
    ROUND(100.0 * SUM(CASE WHEN winner = true THEN 1 ELSE 0 END) / COUNT(*), 2) AS win_pct
FROM players_raw
WHERE opening IS NOT NULL
GROUP BY opening
ORDER BY total_games DESC
LIMIT 20
```

### age_uptime_by_winner_stats

```sql
SELECT
    feature,
    winner,
    COUNT(*) AS n,
    ROUND(AVG(val), 2) AS mean_val,
    ROUND(MEDIAN(val), 2) AS median_val,
    ROUND(STDDEV(val), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY val) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY val) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY val) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY val) AS p95
FROM (
    SELECT 'feudal_age_uptime' AS feature, winner, feudal_age_uptime AS val
    FROM players_raw WHERE feudal_age_uptime IS NOT NULL
    UNION ALL
    SELECT 'castle_age_uptime', winner, castle_age_uptime
    FROM players_raw WHERE castle_age_uptime IS NOT NULL
    UNION ALL
    SELECT 'imperial_age_uptime', winner, imperial_age_uptime
    FROM players_raw WHERE imperial_age_uptime IS NOT NULL
) sub
GROUP BY feature, winner
ORDER BY feature, winner
```

### spearman_sample_players

```sql
SELECT
    old_rating,
    new_rating,
    match_rating_diff,
    feudal_age_uptime,
    castle_age_uptime,
    imperial_age_uptime
FROM players_raw
WHERE old_rating > 0
  AND match_rating_diff IS NOT NULL
USING SAMPLE RESERVOIR(500000)
```

### spearman_sample_matches

```sql
SELECT
    avg_elo,
    team_0_elo,
    team_1_elo,
    (duration / 1e9) AS duration_sec,
    (irl_duration / 1e9) AS irl_duration_sec
FROM matches_raw
WHERE avg_elo > 0
  AND team_0_elo > 0
  AND team_1_elo > 0
USING SAMPLE RESERVOIR(500000)
```

## Data Sources

- `matches_raw` (30,690,651 rows, 18 columns)
- `players_raw` (107,627,584 rows, 14 columns)
- Census artifact: `01_02_04_univariate_census.json`