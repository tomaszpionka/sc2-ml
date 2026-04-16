# Step 01_02_05 -- Univariate Visualizations: aoestats

**Phase:** 01 -- Data Exploration
**Pipeline Section:** 01_02 -- Exploratory Data Analysis (Tukey-style)
**Dataset:** aoestats
**Invariants applied:** #6 (SQL reproducibility), #7 (no magic numbers), #9 (step scope: visualization only)
**Predecessor artifact:** `01_02_04_univariate_census.json`

## Plot Index

| # | File | Description | Temporal Annotation |
|---|------|-------------|---------------------|
| 1 | `01_02_05_winner_distribution.png` | Winner distribution 2-bar (players_raw) | N/A |
| 2 | `01_02_05_num_players_distribution.png` | Match size distribution bar (matches_raw) | N/A |
| 3 | `01_02_05_map_top20.png` | Top-20 maps horizontal barh (matches_raw) | N/A |
| 4 | `01_02_05_civ_top20.png` | Top-20 civilizations horizontal barh (players_raw) | N/A |
| 5 | `01_02_05_leaderboard_distribution.png` | Leaderboard distribution bar (matches_raw) | N/A |
| 6 | `01_02_05_duration_histogram.png` | Duration dual-panel: body (p95 clip) + full range (log) | POST-GAME (Inv. #3) |
| 7 | `01_02_05_elo_distributions.png` | ELO 1x3 panel: avg_elo, team_0_elo, team_1_elo (sentinel excluded) | N/A |
| 8 | `01_02_05_old_rating_histogram.png` | Pre-game rating (old_rating) histogram (players_raw) | N/A |
| 9 | `01_02_05_match_rating_diff_histogram.png` | match_rating_diff histogram clipped [-200,+200] (players_raw) | LEAKAGE UNRESOLVED (Inv. #3) |
| 10 | `01_02_05_age_uptime_histograms.png` | Age uptime 1x3 panel: feudal/castle/imperial (non-NULL only) | IN-GAME (Inv. #3) |
| 11 | `01_02_05_opening_nonnull.png` | Opening strategy bar (non-NULL only, players_raw) | IN-GAME (Inv. #3) |
| 12 | `01_02_05_iqr_outlier_summary.png` | IQR outlier rates barh (all numeric columns) | N/A |
| 13 | `01_02_05_null_rate_bar.png` | NULL rate barh for all columns (4-tier severity) | N/A |
| 14 | `01_02_05_schema_change_boundary.png` | Weekly NULL rate for high-NULL columns (schema change boundary) | IN-GAME (Inv. #3) |
| 15 | `01_02_05_monthly_match_count.png` | Monthly match volume line chart (matches_raw) | N/A |

## SQL Queries (Invariant #6)

All SQL queries that produce plotted data appear verbatim below.

### `hist_duration_body`

```sql
SELECT
    FLOOR((duration / 1e9) / 60) AS bin_min,
    COUNT(*) AS cnt
FROM matches_raw
WHERE duration > 0
  AND (duration / 1e9) <= 4714.1
GROUP BY bin_min
ORDER BY bin_min
```

### `hist_duration_full_log`

```sql
SELECT
    FLOOR(LOG10(GREATEST(duration / 1e9, 1))) AS log_bin,
    COUNT(*) AS cnt
FROM matches_raw
WHERE duration > 0
GROUP BY log_bin
ORDER BY log_bin
```

### `hist_elo_3panel`

```sql
-- avg_elo (exclude zero sentinels for consistency with team panels):
SELECT FLOOR(avg_elo / 25) * 25 AS bin, COUNT(*) AS cnt
FROM matches_raw WHERE avg_elo > 0
GROUP BY bin ORDER BY bin;

-- team_0_elo (exclude sentinel -1 and zero):
SELECT FLOOR(team_0_elo / 25) * 25 AS bin, COUNT(*) AS cnt
FROM matches_raw WHERE team_0_elo > 0
GROUP BY bin ORDER BY bin;

-- team_1_elo (exclude sentinel -1 and zero):
SELECT FLOOR(team_1_elo / 25) * 25 AS bin, COUNT(*) AS cnt
FROM matches_raw WHERE team_1_elo > 0
GROUP BY bin ORDER BY bin
```

### `hist_old_rating`

```sql
SELECT FLOOR(old_rating / 25) * 25 AS bin, COUNT(*) AS cnt
FROM players_raw WHERE old_rating > 0
GROUP BY bin ORDER BY bin
```

### `hist_match_rating_diff`

```sql
SELECT
    FLOOR(match_rating_diff / 5) * 5 AS bin,
    COUNT(*) AS cnt
FROM players_raw
WHERE match_rating_diff IS NOT NULL
  AND match_rating_diff BETWEEN -200 AND 200
GROUP BY bin ORDER BY bin
```

### `hist_age_uptimes`

```sql
-- feudal_age_uptime:
SELECT FLOOR(feudal_age_uptime / 10) * 10 AS bin, COUNT(*) AS cnt
FROM players_raw WHERE feudal_age_uptime IS NOT NULL
GROUP BY bin ORDER BY bin;

-- castle_age_uptime:
SELECT FLOOR(castle_age_uptime / 20) * 20 AS bin, COUNT(*) AS cnt
FROM players_raw WHERE castle_age_uptime IS NOT NULL
GROUP BY bin ORDER BY bin;

-- imperial_age_uptime:
SELECT FLOOR(imperial_age_uptime / 30) * 30 AS bin, COUNT(*) AS cnt
FROM players_raw WHERE imperial_age_uptime IS NOT NULL
GROUP BY bin ORDER BY bin
```

### `weekly_null_rate_high_null_cols`

```sql
SELECT
    CAST(SUBSTR(filename, 9, 10) AS DATE) AS week_start,
    COUNT(*) AS total_rows,
    ROUND(100.0 * (COUNT(*) - COUNT("feudal_age_uptime")) / COUNT(*), 2) AS feudal_age_uptime_null_pct,
    ROUND(100.0 * (COUNT(*) - COUNT("castle_age_uptime")) / COUNT(*), 2) AS castle_age_uptime_null_pct,
    ROUND(100.0 * (COUNT(*) - COUNT("imperial_age_uptime")) / COUNT(*), 2) AS imperial_age_uptime_null_pct,
    ROUND(100.0 * (COUNT(*) - COUNT("opening")) / COUNT(*), 2) AS opening_null_pct
FROM players_raw
GROUP BY week_start
ORDER BY week_start
```

### `monthly_match_counts`

```sql
SELECT
    DATE_TRUNC('month', started_timestamp) AS month,
    COUNT(*) AS match_count
FROM matches_raw
WHERE started_timestamp IS NOT NULL
GROUP BY month
ORDER BY month
```

## Data Sources

- `matches_raw`: 30,690,651 rows
- `players_raw`: 107,627,584 rows
- Census artifact: `01_02_04_univariate_census.json`
