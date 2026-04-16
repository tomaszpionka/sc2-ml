# Step 01_02_07 -- Multivariate EDA -- aoestats

**Generated:** 2026-04-15
**Dataset:** aoestats (matches_raw: 30,690,651 rows; players_raw: 107,627,584 rows)
**Predecessor:** 01_02_06 (Bivariate EDA)

## Column Classification

| Column | Source Table | Temporal Class | In PCA? | In Heatmap? |
|--------|-------------|---------------|---------|-------------|
| old_rating | players_raw | PRE-GAME | Yes | Yes |
| match_rating_diff | players_raw | PRE-GAME (confirmed 01_02_06) | Yes | Yes |
| avg_elo | matches_raw | PRE-GAME | Yes | Yes |
| team_0_elo | matches_raw | PRE-GAME | Yes | Yes |
| team_1_elo | matches_raw | PRE-GAME | Yes | Yes |
| new_rating | players_raw | POST-GAME | No | Yes (annotated*) |
| duration_sec | matches_raw | POST-GAME | No | Yes (annotated*) |
| feudal_age_uptime | players_raw | IN-GAME (87% NULL) | No | Yes (annotated*) |
| castle_age_uptime | players_raw | IN-GAME (88% NULL) | No | Yes (annotated*) |
| imperial_age_uptime | players_raw | IN-GAME (91% NULL) | No | Yes (annotated*) |

**Note:** cross-table JOIN produces multiple player rows per match. Match-level columns (avg_elo, team_0_elo, team_1_elo, duration_sec) are repeated across players within the same game. Correlations between match-level columns in this heatmap reflect this duplication; per-table correlations from 01_02_06 are the authoritative within-table values.

## Plot Index

| # | Title | Filename | Temporal Annotation |
|---|-------|----------|---------------------|
| 1 | Spearman heatmap (all numeric, cross-table) | `01_02_07_spearman_heatmap_all.png` | Mixed -- POST-GAME* and IN-GAME* annotated on axis |
| 2 | PCA scree plot (pre-game features only) | `01_02_07_pca_scree.png` | N/A (pre-game features only) |
| 3 | PCA biplot (PC1 vs PC2, winner-coloured) | `01_02_07_pca_biplot.png` | N/A (pre-game features only) |

## PCA Summary

Features: old_rating, match_rating_diff, avg_elo, team_0_elo, team_1_elo
Sample size: 20,000

**Note:** PC1 variance concentration is expected given the near-perfect collinearity of avg_elo, team_0_elo, and team_1_elo (pairwise rho > 0.98 per 01_02_06 Spearman matrix). PC1 dominance reflects ELO feature redundancy, not a latent factor. Retention decisions deferred to Phase 02.

| Component | Variance Explained | Cumulative |
|-----------|-------------------|------------|
| PC1 | 0.7923 | 0.7923 |
| PC2 | 0.2014 | 0.9936 |
| PC3 | 0.0034 | 0.9971 |
| PC4 | 0.0029 | 1.0000 |
| PC5 | 0.0000 | 1.0000 |

## SQL Queries

### spearman_cross_table_sample

```sql
SELECT
    p.old_rating,
    p.new_rating,
    p.match_rating_diff,
    p.feudal_age_uptime,
    p.castle_age_uptime,
    p.imperial_age_uptime,
    m.avg_elo,
    m.team_0_elo,
    m.team_1_elo,
    (m.duration / 1e9) AS duration_sec
FROM players_raw p
JOIN matches_raw m ON p.game_id = m.game_id
WHERE p.old_rating >= 0
  AND m.team_0_elo != -1
  AND m.team_1_elo != -1
USING SAMPLE RESERVOIR(20000)
```

### pca_cross_table_sample

```sql
SELECT
    p.old_rating,
    p.match_rating_diff,
    p.winner,
    m.avg_elo,
    m.team_0_elo,
    m.team_1_elo
FROM players_raw p
JOIN matches_raw m ON p.game_id = m.game_id
WHERE p.old_rating >= 0
  AND p.match_rating_diff IS NOT NULL
  AND m.team_0_elo != -1
  AND m.team_1_elo != -1
USING SAMPLE RESERVOIR(20000)
```

## Data Sources

- `matches_raw` (30,690,651 rows, 18 columns)
- `players_raw` (107,627,584 rows, 14 columns)
- Census artifact: `01_02_04_univariate_census.json`
- Bivariate artifact: `01_02_06_bivariate_eda.json`