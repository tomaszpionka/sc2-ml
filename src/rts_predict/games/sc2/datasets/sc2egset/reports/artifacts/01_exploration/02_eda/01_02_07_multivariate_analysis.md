# Step 01_02_07 -- Multivariate EDA

**Dataset:** sc2egset
**Total rows:** 44,817
**Win/Loss rows:** 44,791
**Excluded:** Undecided (24), Tie (2)

## PCA Decision

**Standard PCA was skipped.** The sc2egset pre-game numeric feature space contains exactly 1 column (`mmr`). With p=1, PCA is trivially PC1 = 100% variance explained. The scree plot is uninformative and the biplot collapses to a line (Jolliffe 2002, Section 2.2).

**Alternative chosen:** MMR distribution faceted by `selectedRace` x `highestLeague` -- showing the joint structure of all 3 pre-game features (1 numeric, 2 categorical) in a single figure.

**Option rejected:** Including IN-GAME features (APM, SQ, supplyCappedPercent) in PCA with I3 annotation was considered but rejected. The dominant PCs would be driven by the APM-SQ in-game correlation (~0.40-0.34 rho per 01_02_06), making the result uninterpretable for Phase 02 pre-game feature engineering.

## Column Classification

| Column | I3 Classification | Notes |
|--------|-------------------|-------|
| MMR | PRE-GAME | 83.65% zero sentinel; non-zero used for rated analysis |
| APM | IN-GAME (Inv. #3) | Not available at prediction time |
| SQ | IN-GAME (Inv. #3) | Not available at prediction time; 2 INT32_MIN sentinels |
| supplyCappedPercent | IN-GAME (Inv. #3) | Not available at prediction time |
| handicap | DEAD (excluded) | Effectively constant -- 2 non-100 rows |

## Plot Index

| # | Title | Filename | Key Finding |
|---|-------|----------|-------------|
| 1 | Cluster-Ordered Spearman Heatmap (two-panel) | 01_02_07_spearman_heatmap_all.png | APM-SQ correlation block visible; MMR decorrelated from in-game features in all-rows panel, moderately correlated in rated panel |
| 2 | Pre-Game Multivariate Faceted View | 01_02_07_pregame_multivariate_faceted.png | MMR distribution varies across league tiers; race shows minimal effect on MMR distribution within leagues |

## Spearman Matrices

### All rows (SQ sentinel excluded, N=44,789)

| | MMR | supplyCappedPercent | APM | SQ |
|---|---|---|---|---|
| MMR | 1.0000 | 0.0121 | -0.0131 | -0.0092 |
| supplyCappedPercent | 0.0121 | 1.0000 | -0.0023 | -0.1246 |
| APM | -0.0131 | -0.0023 | 1.0000 | 0.4049 |
| SQ | -0.0092 | -0.1246 | 0.4049 | 1.0000 |

### Rated players (MMR > 0, SQ sentinel excluded, N=7,159)

| | supplyCappedPercent | MMR | APM | SQ |
|---|---|---|---|---|
| supplyCappedPercent | 1.0000 | -0.0118 | -0.0263 | -0.1611 |
| MMR | -0.0118 | 1.0000 | 0.2061 | 0.1593 |
| APM | -0.0263 | 0.2061 | 1.0000 | 0.3445 |
| SQ | -0.1611 | 0.1593 | 0.3445 | 1.0000 |

## SQL Queries

### spearman_all
```sql
SELECT
    MMR,
    APM,
    SQ,
    supplyCappedPercent
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
    supplyCappedPercent
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND SQ > -2147483648
  AND MMR > 0
  -- I7: mmr > 0 filter excludes zero-sentinel rows (83.65% of data,
  --     census: MMR_zero = 37489)
```

### pregame_faceted
```sql
SELECT
    MMR,
    selectedRace,
    highestLeague,
    result
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND MMR > 0
  AND selectedRace IN ('Prot', 'Zerg', 'Terr')
  -- I7: exclude empty-string (1110 rows), Rand (10), BW* (3) per census
  -- I7: MMR > 0 excludes zero-sentinel (37489 rows, 83.65%)
```

## Data Sources

- `replay_players_raw` (44,817 rows, 25 columns)
- `01_02_04_univariate_census.json` (sentinel thresholds, result distribution)
- `01_02_06_bivariate_eda.json` (prior Spearman matrices with result_binary for comparison)

## Invariants Applied

- **I3:** Axis labels annotated with I3 classification on Spearman heatmap. Pre-game faceted plot uses only pre-game features.
- **I6:** All SQL queries reproduced in SQL Queries section above.
- **I7:** All thresholds data-derived from census JSON at runtime.
- **I9:** Multivariate visualization only; no new feature computation.
