# Step 01_02_06 -- Bivariate EDA

**Dataset:** sc2egset
**Step:** 01_02_06
**Predecessor:** 01_02_05
**Total rows:** 44,817
**Win/Loss rows:** 44,791
**Excluded:** Undecided (24), Tie (2)

> **NOTE:** All statistical tests in this notebook are EXPLORATORY (Tukey-style EDA, 01_02 pipeline section). P-values are reported for descriptive comparison, not as confirmatory hypothesis tests. No multiple comparison correction is applied. Findings here generate hypotheses for Phase 02 feature engineering and Phase 03 model evaluation -- not causal claims.

## Plot Index

| # | Title | Filename | Test | Key Finding | Temporal Annotation |
|---|-------|----------|------|-------------|---------------------|
| 1 | MMR by Result (non-zero) | 01_02_06_mmr_by_result.png | Mann-Whitney U | See test_results | N/A |
| 2 | Race Win Rate (post-random-resolution) | 01_02_06_race_winrate.png | Chi-square | See test_results | N/A |
| 3 | APM by Result | 01_02_06_apm_by_result.png | Mann-Whitney U | See test_results | IN-GAME (Inv. #3) |
| 4 | SQ by Result | 01_02_06_sq_by_result.png | Mann-Whitney U | See test_results | IN-GAME (Inv. #3) |
| 5 | supplyCappedPercent by Result | 01_02_06_supplycapped_by_result.png | Mann-Whitney U | See test_results | IN-GAME (Inv. #3) |
| 6 | League Win Rate | 01_02_06_league_winrate.png | Descriptive | See plot | N/A |
| 7 | Clan Win Rate | 01_02_06_clan_winrate.png | Chi-square | See test_results | N/A |
| 8 | Numeric Features by Result | 01_02_06_numeric_by_result.png | Visual | Multi-panel overview (MMR non-zero) | Mixed (APM/SQ/supCap IN-GAME) |
| 9 | Spearman Correlation (all + rated subplots) | 01_02_06_spearman_correlation.png | Spearman rho | Two side-by-side matrices in JSON | Mixed (* = IN-GAME) |

## Statistical Tests Summary

### mmr_by_result
- **Test:** Mann-Whitney U
- **U statistic:** 7,285,394
- **Rank-biserial r:** -0.0902
- **p-value:** 2.4115e-11

### race_winrate_chi2
- **Test:** chi-square
- **Chi-square:** 39.8405
- **p-value:** 2.2322e-09

### apm_by_result
- **Test:** Mann-Whitney U
- **U statistic:** 275,580,382
- **Rank-biserial r:** -0.0989
- **p-value:** 1.9696e-73

### sq_by_result
- **Test:** Mann-Whitney U
- **U statistic:** 296,794,093
- **Rank-biserial r:** -0.1836
- **p-value:** 2.8084e-248

### supplycapped_by_result
- **Test:** Mann-Whitney U
- **U statistic:** 253,214,553
- **Rank-biserial r:** -0.0097
- **p-value:** 7.4099e-02

### clan_winrate_chi2
- **Test:** chi-square
- **Chi-square:** 7.7452
- **p-value:** 5.3857e-03

## SQL Queries

### mmr_by_result
```sql
SELECT MMR, result
FROM replay_players_raw
WHERE MMR != 0
  AND result IN ('Win', 'Loss')
```

### race_winrate
```sql
SELECT
    race,
    COUNT(*) AS total,
    SUM(CASE WHEN result = 'Win' THEN 1 ELSE 0 END) AS wins,
    ROUND(100.0 * SUM(CASE WHEN result = 'Win' THEN 1 ELSE 0 END) / COUNT(*), 2) AS win_pct
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND race IN ('Prot', 'Zerg', 'Terr')
GROUP BY race
ORDER BY race
```

### apm_by_result
```sql
SELECT APM, result
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
```

### sq_by_result
```sql
SELECT SQ, result
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND SQ > -2147483648
```

### supplycapped_by_result
```sql
SELECT supplyCappedPercent, result
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
```

### league_winrate
```sql
SELECT
    highestLeague,
    COUNT(*) AS total,
    SUM(CASE WHEN result = 'Win' THEN 1 ELSE 0 END) AS wins,
    ROUND(100.0 * SUM(CASE WHEN result = 'Win' THEN 1 ELSE 0 END) / COUNT(*), 2) AS win_pct
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
GROUP BY highestLeague
ORDER BY total DESC
```

### clan_winrate
```sql
SELECT
    isInClan,
    COUNT(*) AS total,
    SUM(CASE WHEN result = 'Win' THEN 1 ELSE 0 END) AS wins,
    ROUND(100.0 * SUM(CASE WHEN result = 'Win' THEN 1 ELSE 0 END) / COUNT(*), 2) AS win_pct
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
GROUP BY isInClan
ORDER BY isInClan
```

### numeric_by_result
```sql
SELECT MMR, APM, SQ, supplyCappedPercent, result
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
```

### spearman_all
```sql
SELECT
    MMR,
    APM,
    SQ,
    supplyCappedPercent,
    CASE WHEN result = 'Win' THEN 1 ELSE 0 END AS result_binary
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND SQ > -2147483648
```

### spearman_rated
```sql
SELECT
    MMR,
    APM,
    SQ,
    supplyCappedPercent,
    CASE WHEN result = 'Win' THEN 1 ELSE 0 END AS result_binary
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND SQ > -2147483648
  AND MMR > 0
  -- I7: mmr > 0 filter excludes zero-sentinel rows (83.65% of data, census:
  --     zero_counts.replay_players_raw.MMR_zero = 37489). Without this filter,
  --     the MMR-correlation row/column is dominated by the zero-spike and
  --     shows near-zero rho regardless of true association. Consistent with
  --     T03 violin which also filters mmr > 0.
```

## Data Sources

- `replay_players_raw` (44,817 rows, 25 columns)
- `01_02_04_univariate_census.json` (sentinel thresholds, result distribution)

## Invariants Applied

- **I3:** All three in-game columns carry IN-GAME annotation on every plot.
- **I6:** All SQL queries reproduced above.
- **I7:** All thresholds data-derived from census JSON at runtime.
- **I9:** Bivariate analysis only; no new feature computation.