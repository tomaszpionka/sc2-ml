# Step 01_02_06 -- Bivariate EDA: aoe2companion

**Phase:** 01 -- Data Exploration
**Pipeline Section:** 01_02 -- Exploratory Data Analysis
**Dataset:** aoe2companion
**Predecessor:** 01_02_05 (Univariate Census Visualizations)
**Invariants applied:** #3, #6, #7, #9

## Temporal Leakage Resolution

### ratingDiff (Q1 -- RESOLVED: POST-GAME)

ratingDiff is definitively post-game. Winners have positive mean ratingDiff,
losers have negative mean ratingDiff, in every leaderboard without exception.
This column MUST be excluded from all pre-game feature sets.

### rating (Q2 -- RESULT PENDING)

The rating classification depends on the observed mean difference between
won=True and won=False groups. See the plot annotation for the quantitative
result. Final classification will be written here post-execution.

## Plot Index

| # | Title | Filename | Question | Temporal Annotation |
|---|-------|----------|----------|---------------------|
| 1 | ratingDiff by Outcome (Q1) | `01_02_06_ratingdiff_by_won.png` | Q1 -- I3 resolution | POST-GAME (Inv. #3) |
| 2 | Rating by Outcome (Q2) | `01_02_06_rating_by_won.png` | Q2 -- ambiguity test | AMBIGUOUS -- see findings |
| 3 | Rating vs ratingDiff Scatter (Q3) | `01_02_06_rating_vs_ratingdiff.png` | Q3 -- structural relationship | rating: AMBIGUOUS | ratingDiff: POST-GAME |
| 4 | Duration by Outcome (Q4) | `01_02_06_duration_by_won.png` | Q4 -- duration predictiveness | N/A (match descriptor) |
| 5 | Numeric Features by Outcome (Q5) | `01_02_06_numeric_by_won.png` | Q5 -- feature-outcome overview | Per-panel labels |
| 6 | Spearman Correlation Matrix (Q6) | `01_02_06_spearman_correlation.png` | Q6 -- inter-feature correlation | N/A |
| 7 | ratingDiff by Leaderboard (Q7) | `01_02_06_ratingdiff_by_leaderboard.png` | Q7 -- leakage universality | POST-GAME (Inv. #3) |
| 8 | ratingDiff by Outcome per LB (Q7) | `01_02_06_ratingdiff_by_won_by_leaderboard.png` | Q7 -- leakage universality | POST-GAME (Inv. #3) |

## Statistical Tests -- Leakage Diagnostics

> Tests on POST-GAME columns measure **leakage magnitude**, not prediction power. A large effect size here confirms the column must be excluded from all feature sets.

### ratingdiff_by_won
- **Temporal status:** POST-GAME (confirmed leakage -- Inv. #3)
- **Mann-Whitney U:** 507,748,821,116,568
- **p-value:** 0.0000e+00
- **Rank-biserial r (Wendt 1972):** -1.0000
- **n(won=True):** 22,532,474 | **n(won=False):** 22,534,093
- **Median(won=True):** 16.00 | **Median(won=False):** -16.00


## Statistical Tests -- Exploratory Discrimination

> Tests on PRE-GAME / AMBIGUOUS columns measure **discriminative power** at prediction time. These findings generate hypotheses for Phase 02 and Phase 03 (no confirmatory claims; no multiple comparison correction).

### rating_by_won
- **Temporal status:** AMBIGUOUS (Inv. #3 -- temporal status unresolved)
- **Mann-Whitney U:** 255,984,614,523,364
- **p-value:** 0.0000e+00
- **Rank-biserial r (Wendt 1972):** -0.0086
- **n(won=True):** 22,531,103 | **n(won=False):** 22,528,795
- **Median(won=True):** 1051.00 | **Median(won=False):** 1047.00


## SQL Queries (Invariant #6)

### ratingdiff_percentiles_by_won

```sql
SELECT
    won,
    COUNT(*) AS n,
    AVG(ratingDiff) AS mean_val,
    MEDIAN(ratingDiff) AS median_val,
    STDDEV(ratingDiff) AS std_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY ratingDiff) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ratingDiff) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ratingDiff) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY ratingDiff) AS p95,
    MIN(ratingDiff) AS min_val,
    MAX(ratingDiff) AS max_val
FROM matches_raw
WHERE won IS NOT NULL
  AND ratingDiff IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won
ORDER BY won
```

### ratingdiff_hist_by_won

```sql
SELECT
    won,
    ratingDiff AS val,
    COUNT(*) AS cnt
FROM matches_raw
WHERE won IS NOT NULL
  AND ratingDiff IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won, ratingDiff
ORDER BY won, ratingDiff
```

### ratingdiff_raw_by_won

```sql
SELECT won, ratingDiff
FROM matches_raw
WHERE won IS NOT NULL
  AND ratingDiff IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
```

### rating_percentiles_by_won

```sql
SELECT
    won,
    COUNT(*) AS n,
    AVG(rating) AS mean_val,
    MEDIAN(rating) AS median_val,
    STDDEV(rating) AS std_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY rating) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY rating) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY rating) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY rating) AS p95
FROM matches_raw
WHERE won IS NOT NULL
  AND rating IS NOT NULL
  AND rating > 0
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won
ORDER BY won
```

### rating_hist_by_won

```sql
SELECT
    won,
    FLOOR(rating / 25) * 25 AS bin,
    COUNT(*) AS cnt
FROM matches_raw
WHERE won IS NOT NULL
  AND rating IS NOT NULL
  AND rating > 0
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won, bin
ORDER BY won, bin
```

### rating_raw_by_won

```sql
SELECT won, rating
FROM matches_raw
WHERE won IS NOT NULL
  AND rating IS NOT NULL
  AND rating > 0
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
```

### rating_vs_ratingdiff_scatter

```sql
SELECT
    rating,
    ratingDiff,
    won
FROM (
    SELECT *
    FROM matches_raw
    TABLESAMPLE BERNOULLI(0.036088 PERCENT)
) sub
WHERE won IS NOT NULL
  AND rating IS NOT NULL
  AND ratingDiff IS NOT NULL
  AND rating > 0
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
```

### duration_percentiles_by_won

```sql
SELECT
    won,
    COUNT(*) AS n,
    AVG(EXTRACT(EPOCH FROM (finished - started))) AS mean_secs,
    MEDIAN(EXTRACT(EPOCH FROM (finished - started))) AS median_secs,
    STDDEV(EXTRACT(EPOCH FROM (finished - started))) AS std_secs,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p95
FROM matches_raw
WHERE won IS NOT NULL
  AND finished > started
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won
ORDER BY won
```

### duration_hist_by_won

```sql
SELECT
    won,
    FLOOR(EXTRACT(EPOCH FROM (finished - started)) / 60) AS bin_min,
    COUNT(*) AS cnt
FROM matches_raw
WHERE won IS NOT NULL
  AND finished > started
  AND EXTRACT(EPOCH FROM (finished - started)) <= 3789.0
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won, bin_min
ORDER BY won, bin_min
```

### numeric_features_by_won

```sql
SELECT
    won,
    'rating' AS feature,
    AVG(rating) AS mean_val,
    MEDIAN(rating) AS median_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY rating) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY rating) AS p75,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY rating) AS p05,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY rating) AS p95
FROM matches_raw
WHERE won IS NOT NULL AND rating IS NOT NULL AND rating > 0
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won

UNION ALL

SELECT
    won,
    'ratingDiff' AS feature,
    AVG(ratingDiff) AS mean_val,
    MEDIAN(ratingDiff) AS median_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ratingDiff) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ratingDiff) AS p75,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY ratingDiff) AS p05,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY ratingDiff) AS p95
FROM matches_raw
WHERE won IS NOT NULL AND ratingDiff IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won

UNION ALL

SELECT
    won,
    'duration_min' AS feature,
    AVG(EXTRACT(EPOCH FROM (finished - started)) / 60) AS mean_val,
    MEDIAN(EXTRACT(EPOCH FROM (finished - started)) / 60) AS median_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started)) / 60) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started)) / 60) AS p75,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started)) / 60) AS p05,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started)) / 60) AS p95
FROM matches_raw
WHERE won IS NOT NULL AND finished > started
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
GROUP BY won

ORDER BY feature, won
```

### correlation_sample

```sql
SELECT
    rating,
    ratingDiff,
    EXTRACT(EPOCH FROM (finished - started)) / 60.0 AS duration_min,
    population,
    speedFactor,
    treatyLength
FROM (
    SELECT *
    FROM matches_raw
    TABLESAMPLE BERNOULLI(0.036088 PERCENT)
) sub
WHERE rating IS NOT NULL
  AND rating > 0
  AND ratingDiff IS NOT NULL
  AND finished > started
  AND population IS NOT NULL
  AND treatyLength IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
```

### ratingdiff_stats_by_leaderboard

```sql
SELECT
    leaderboard,
    COUNT(*) AS n,
    AVG(ratingDiff) AS mean_val,
    MEDIAN(ratingDiff) AS median_val,
    STDDEV(ratingDiff) AS std_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ratingDiff) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ratingDiff) AS p75
FROM matches_raw
WHERE ratingDiff IS NOT NULL
GROUP BY leaderboard
ORDER BY n DESC
```

### ratingdiff_by_won_by_leaderboard

```sql
SELECT
    leaderboard,
    won,
    COUNT(*) AS n,
    AVG(ratingDiff) AS mean_val,
    MEDIAN(ratingDiff) AS median_val
FROM matches_raw
WHERE won IS NOT NULL
  AND ratingDiff IS NOT NULL
GROUP BY leaderboard, won
ORDER BY leaderboard, won
```

## Interpretation Notes

### Near-constant columns in correlation matrix

**speedFactor** (stddev=0.09, 4 distinct values) and **treatyLength**
(96.56% zero in full dataset) may be near-constant in the rm_1v1 filtered
subset. Their Spearman coefficients should be interpreted with caution --
near-constant variables produce unstable or near-zero rho regardless of
true association. These columns are included for completeness but should
not be relied upon for Phase 02 feature selection without further analysis.

## Data Sources

- `matches_raw` (277,099,059 rows) -- DuckDB table from 01_02_02
- Census JSON: `01_02_04_univariate_census.json` (50 keys)
- Sample fraction: 0.036088% (BERNOULLI, targeting 100,000 rows)
