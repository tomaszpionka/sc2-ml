# Step 01_03_01 -- Systematic Data Profiling: aoe2companion

**Phase:** 01 -- Data Exploration
**Pipeline Section:** 01_03 -- Systematic Data Profiling
**Dataset:** aoe2companion
**Predecessor:** 01_02_07 (Multivariate EDA)
**Invariants applied:** #3, #6, #7, #9
**Table:** matches_raw (277,099,059 rows, 55 columns)

## I3 Temporal Classification Table

| Column | I3 Classification | Null % | Cardinality | Uniqueness Ratio | Notes |
|--------|-------------------|--------|-------------|------------------|-------|
| matchId | IDENTIFIER | 0.0 | 61,799,126 | 0.22302178 |  |
| started | PRE_GAME | 0.0 | 52,689,164 | 0.19014559 |  |
| finished | POST_GAME | 0.0 | 55,139,738 | 0.19898926 |  |
| leaderboard | PRE_GAME | 0.0 | 22 | 0.00000008 | NEAR-CONSTANT (uniqueness_ratio=0.00000008 < 0.001) |
| name | IDENTIFIER | 0.01 | 2,308,187 | 0.00832983 |  |
| server | CONTEXT | 97.99 | 11 | 0.00000004 | NEAR-CONSTANT (uniqueness_ratio=0.00000004 < 0.001) |
| internalLeaderboardId | PRE_GAME | 0.48 | 122 | 0.00000044 | NEAR-CONSTANT (uniqueness_ratio=0.00000044 < 0.001) |
| privacy | CONTEXT | 0.0 | 3 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| mod | PRE_GAME | 0.0 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| map | PRE_GAME | 0.0 | 261 | 0.00000094 | NEAR-CONSTANT (uniqueness_ratio=0.00000094 < 0.001) |
| difficulty | PRE_GAME | 0.0 | 7 | 0.00000003 | NEAR-CONSTANT (uniqueness_ratio=0.00000003 < 0.001) |
| startingAge | PRE_GAME | 0.0 | 12 | 0.00000004 | NEAR-CONSTANT (uniqueness_ratio=0.00000004 < 0.001) |
| fullTechTree | PRE_GAME | 0.16 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| allowCheats | PRE_GAME | 0.15 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| empireWarsMode | PRE_GAME | 1.06 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| endingAge | PRE_GAME | 0.0 | 11 | 0.00000004 | NEAR-CONSTANT (uniqueness_ratio=0.00000004 < 0.001) |
| gameMode | PRE_GAME | 0.0 | 16 | 0.00000006 | NEAR-CONSTANT (uniqueness_ratio=0.00000006 < 0.001) |
| lockSpeed | PRE_GAME | 0.15 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| lockTeams | PRE_GAME | 0.15 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| mapSize | PRE_GAME | 0.0 | 14 | 0.00000005 | NEAR-CONSTANT (uniqueness_ratio=0.00000005 < 0.001) |
| population | PRE_GAME | 0.16 | 21 | 0.00000008 | NEAR-CONSTANT (uniqueness_ratio=0.00000008 < 0.001, IQR=0) |
| hideCivs | PRE_GAME | 49.3 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| recordGame | PRE_GAME | 0.15 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| regicideMode | PRE_GAME | 7.39 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| gameVariant | PRE_GAME | 0.0 | 3 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| resources | PRE_GAME | 0.0 | 9 | 0.00000003 | NEAR-CONSTANT (uniqueness_ratio=0.00000003 < 0.001) |
| sharedExploration | PRE_GAME | 0.15 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| speed | PRE_GAME | 0.0 | 5 | 0.00000002 | NEAR-CONSTANT (uniqueness_ratio=0.00000002 < 0.001) |
| speedFactor | PRE_GAME | 0.0 | 4 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001, IQR=0) |
| suddenDeathMode | PRE_GAME | 1.04 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| antiquityMode | PRE_GAME | 68.66 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| civilizationSet | PRE_GAME | 0.0 | 3 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| teamPositions | PRE_GAME | 0.15 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| teamTogether | PRE_GAME | 0.15 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| treatyLength | PRE_GAME | 0.09 | 30 | 0.00000011 | NEAR-CONSTANT (uniqueness_ratio=0.00000011 < 0.001, IQR=0) |
| turboMode | PRE_GAME | 0.15 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| victory | PRE_GAME | 0.0 | 6 | 0.00000002 | NEAR-CONSTANT (uniqueness_ratio=0.00000002 < 0.001) |
| revealMap | PRE_GAME | 0.0 | 4 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| scenario | PRE_GAME | 98.27 | 30,484 | 0.00011001 | NEAR-CONSTANT (uniqueness_ratio=0.00011001 < 0.001) |
| password | PRE_GAME | 82.9 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| modDataset | PRE_GAME | 99.72 | 955 | 0.00000345 | NEAR-CONSTANT (uniqueness_ratio=0.00000345 < 0.001) |
| profileId | IDENTIFIER | 0.0 | 3,387,273 | 0.01222405 |  |
| rating | AMBIGUOUS | 42.46 | 4,196 | 0.00001514 | NEAR-CONSTANT (uniqueness_ratio=0.00001514 < 0.001) |
| ratingDiff | POST_GAME | 42.46 | 353 | 0.00000127 | NEAR-CONSTANT (uniqueness_ratio=0.00000127 < 0.001) |
| color | PRE_GAME | 0.01 | 43 | 0.00000016 | NEAR-CONSTANT (uniqueness_ratio=0.00000016 < 0.001) |
| colorHex | PRE_GAME | 0.0 | 10 | 0.00000004 | NEAR-CONSTANT (uniqueness_ratio=0.00000004 < 0.001) |
| slot | PRE_GAME | 0.0 | 9 | 0.00000003 | NEAR-CONSTANT (uniqueness_ratio=0.00000003 < 0.001) |
| status | CONTEXT | 0.0 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| team | PRE_GAME | 4.9 | 31 | 0.00000011 | NEAR-CONSTANT (uniqueness_ratio=0.00000011 < 0.001) |
| won | TARGET | 4.69 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| country | CONTEXT | 12.6 | 222 | 0.00000080 | NEAR-CONSTANT (uniqueness_ratio=0.00000080 < 0.001) |
| shared | CONTEXT | 0.0 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| verified | CONTEXT | 0.0 | 2 | 0.00000001 | NEAR-CONSTANT (uniqueness_ratio=0.00000001 < 0.001) |
| civ | PRE_GAME | 0.0 | 68 | 0.00000025 | NEAR-CONSTANT (uniqueness_ratio=0.00000025 < 0.001) |
| filename | IDENTIFIER | 0.0 | 2,210 | 0.00000798 | NEAR-CONSTANT (uniqueness_ratio=0.00000798 < 0.001) |

## Dataset-Level Summary

- **Total rows:** 277,099,059
- **Total columns:** 55
- **Duplicates (matchId, profileId):** 3,589,428 groups (12,401,433 rows)
- **Memory footprint:** 20.99 GB total allocated / 10.96 GB used (whole DB, DuckDB 1.5.1 pragma_database_size)

### Class Balance (won)

| won | Count | Pct |
|-----|-------|-----|
| False | 132,150,323 | 47.69% |
| True | 131,963,175 | 47.62% |
| None | 12,985,561 | 4.69% |

## Critical Findings

- **Dead fields (0):** None
- **Constant columns (0):** None
- **Near-constant columns (50):** leaderboard, server, internalLeaderboardId, privacy, mod, map, difficulty, startingAge, fullTechTree, allowCheats, empireWarsMode, endingAge, gameMode, lockSpeed, lockTeams, mapSize, population, hideCivs, recordGame, regicideMode, gameVariant, resources, sharedExploration, speed, speedFactor, suddenDeathMode, antiquityMode, civilizationSet, teamPositions, teamTogether, treatyLength, turboMode, victory, revealMap, scenario, password, modDataset, rating, ratingDiff, color, colorHex, slot, status, team, won, country, shared, verified, civ, filename

### Near-constant threshold: uniqueness_ratio < 0.001 OR IQR == 0 (Manual 3.3, I7)

| Column | Cardinality | Uniqueness Ratio | IQR | Reasons | I3 |
|--------|-------------|------------------|-----|---------|-----|
| leaderboard | 22 | 0.00000008 | None | uniqueness_ratio=0.00000008 < 0.001 | PRE_GAME |
| server | 11 | 0.00000004 | None | uniqueness_ratio=0.00000004 < 0.001 | CONTEXT |
| internalLeaderboardId | 122 | 0.00000044 | 9.0 | uniqueness_ratio=0.00000044 < 0.001 | PRE_GAME |
| privacy | 3 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | CONTEXT |
| mod | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | PRE_GAME |
| map | 261 | 0.00000094 | None | uniqueness_ratio=0.00000094 < 0.001 | PRE_GAME |
| difficulty | 7 | 0.00000003 | None | uniqueness_ratio=0.00000003 < 0.001 | PRE_GAME |
| startingAge | 12 | 0.00000004 | None | uniqueness_ratio=0.00000004 < 0.001 | PRE_GAME |
| fullTechTree | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | PRE_GAME |
| allowCheats | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | PRE_GAME |
| empireWarsMode | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | PRE_GAME |
| endingAge | 11 | 0.00000004 | None | uniqueness_ratio=0.00000004 < 0.001 | PRE_GAME |
| gameMode | 16 | 0.00000006 | None | uniqueness_ratio=0.00000006 < 0.001 | PRE_GAME |
| lockSpeed | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | PRE_GAME |
| lockTeams | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | PRE_GAME |
| mapSize | 14 | 0.00000005 | None | uniqueness_ratio=0.00000005 < 0.001 | PRE_GAME |
| population | 21 | 0.00000008 | 0.0 | uniqueness_ratio=0.00000008 < 0.001, IQR=0 | PRE_GAME |
| hideCivs | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | PRE_GAME |
| recordGame | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | PRE_GAME |
| regicideMode | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | PRE_GAME |
| gameVariant | 3 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | PRE_GAME |
| resources | 9 | 0.00000003 | None | uniqueness_ratio=0.00000003 < 0.001 | PRE_GAME |
| sharedExploration | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | PRE_GAME |
| speed | 5 | 0.00000002 | None | uniqueness_ratio=0.00000002 < 0.001 | PRE_GAME |
| speedFactor | 4 | 0.00000001 | 0.0 | uniqueness_ratio=0.00000001 < 0.001, IQR=0 | PRE_GAME |
| suddenDeathMode | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | PRE_GAME |
| antiquityMode | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | PRE_GAME |
| civilizationSet | 3 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | PRE_GAME |
| teamPositions | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | PRE_GAME |
| teamTogether | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | PRE_GAME |
| treatyLength | 30 | 0.00000011 | 0.0 | uniqueness_ratio=0.00000011 < 0.001, IQR=0 | PRE_GAME |
| turboMode | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | PRE_GAME |
| victory | 6 | 0.00000002 | None | uniqueness_ratio=0.00000002 < 0.001 | PRE_GAME |
| revealMap | 4 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | PRE_GAME |
| scenario | 30484 | 0.00011001 | None | uniqueness_ratio=0.00011001 < 0.001 | PRE_GAME |
| password | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | PRE_GAME |
| modDataset | 955 | 0.00000345 | None | uniqueness_ratio=0.00000345 < 0.001 | PRE_GAME |
| rating | 4196 | 0.00001514 | 365.0 | uniqueness_ratio=0.00001514 < 0.001 | AMBIGUOUS |
| ratingDiff | 353 | 0.00000127 | 32.0 | uniqueness_ratio=0.00000127 < 0.001 | POST_GAME |
| color | 43 | 0.00000016 | 3.0 | uniqueness_ratio=0.00000016 < 0.001 | PRE_GAME |
| colorHex | 10 | 0.00000004 | None | uniqueness_ratio=0.00000004 < 0.001 | PRE_GAME |
| slot | 9 | 0.00000003 | 3.0 | uniqueness_ratio=0.00000003 < 0.001 | PRE_GAME |
| status | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | CONTEXT |
| team | 31 | 0.00000011 | 1.0 | uniqueness_ratio=0.00000011 < 0.001 | PRE_GAME |
| won | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | TARGET |
| country | 222 | 0.00000080 | None | uniqueness_ratio=0.00000080 < 0.001 | CONTEXT |
| shared | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | CONTEXT |
| verified | 2 | 0.00000001 | None | uniqueness_ratio=0.00000001 < 0.001 | CONTEXT |
| civ | 68 | 0.00000025 | None | uniqueness_ratio=0.00000025 < 0.001 | PRE_GAME |
| filename | 2210 | 0.00000798 | None | uniqueness_ratio=0.00000798 < 0.001 | IDENTIFIER |

## Rating Stratification

| Scope | N Rows | Rating NULL % | Rating Mean | Rating Std | Rating Median | RatingDiff Mean |
|-------|--------|---------------|-------------|------------|---------------|-----------------|
| full_table | 277,099,059 | 42.46% | 1120.23 | 290.01 | 1093.0 | -0.1905 |
| 1v1_ranked | 61,071,799 | 26.21% | 1091.65 | 346.84 | 1049.0 | -0.4691 |

## Skewness/Kurtosis (Exact, Full Table)

Computed via DuckDB native `SKEWNESS()` and `KURTOSIS()` aggregate functions
over all non-NULL rows per column (no sampling, no listwise deletion).
Kurtosis values are **excess kurtosis** (kurtosis - 3); normal = 0.

| Column | Skewness | Kurtosis (excess) | I3 |
|--------|----------|-------------------|-----|
| rating | 0.5662 | 1.6157 | AMBIGUOUS |
| ratingDiff | 0.1105 | 0.89 | POST_GAME |
| population | 3.7833 | 17.8371 | PRE_GAME |
| slot | 0.916 | -0.1918 | PRE_GAME |
| color | 1.6691 | 15.4799 | PRE_GAME |
| team | 3.8741 | 30.6175 | PRE_GAME |
| speedFactor | 0.6323 | 17.6757 | PRE_GAME |
| treatyLength | 9.309 | 103.0427 | PRE_GAME |
| internalLeaderboardId | 4.355 | 24.9976 | PRE_GAME |
| duration_min | 413.7976 | 366153.7148 | POST_GAME |

## Artifact Index

| # | Artifact | Filename | Description |
|---|----------|----------|-------------|
| 1 | Systematic Profile JSON | `01_03_01_systematic_profile.json` | Machine-readable profile with all metrics |
| 2 | Completeness Heatmap | `01_03_01_completeness_heatmap.png` | NULL rate per column, color-coded |
| 3 | QQ Plots | `01_03_01_qq_plot.png` | Normal reference QQ for 5 numeric columns |
| 4 | ECDF Plots | `01_03_01_ecdf_key_columns.png` | Empirical CDFs for rating, ratingDiff, duration_min |
| 5 | This Report | `01_03_01_systematic_profile.md` | Human-readable summary |

**Distribution methods applied:** Histograms (01_02_05), QQ plots, ECDFs. KDE omitted: histograms and QQ plots provide equivalent shape assessment for these distributions; KDE adds smoothing artifacts on discrete integer columns (rating) and bounded/near-constant distributions (population, speedFactor). QQ plots are the stronger diagnostic tool per Tukey (1977).

## SQL Queries (Invariant #6)

### zero_count_numeric

```sql
SELECT
    SUM(CASE WHEN rating = 0 THEN 1 ELSE 0 END) AS rating_zero_count,
    SUM(CASE WHEN ratingDiff = 0 THEN 1 ELSE 0 END) AS ratingDiff_zero_count,
    SUM(CASE WHEN population = 0 THEN 1 ELSE 0 END) AS population_zero_count,
    SUM(CASE WHEN slot = 0 THEN 1 ELSE 0 END) AS slot_zero_count,
    SUM(CASE WHEN color = 0 THEN 1 ELSE 0 END) AS color_zero_count,
    SUM(CASE WHEN team = 0 THEN 1 ELSE 0 END) AS team_zero_count,
    SUM(CASE WHEN speedFactor = 0 THEN 1 ELSE 0 END) AS speedFactor_zero_count,
    SUM(CASE WHEN treatyLength = 0 THEN 1 ELSE 0 END) AS treatyLength_zero_count,
    SUM(CASE WHEN internalLeaderboardId = 0 THEN 1 ELSE 0 END) AS internalLeaderboardId_zero_count
FROM matches_raw
```

### skewness_kurtosis

```sql
SELECT
    SKEWNESS(rating) AS rating_skew,       KURTOSIS(rating) AS rating_kurt,
    SKEWNESS(ratingDiff) AS ratingDiff_skew, KURTOSIS(ratingDiff) AS ratingDiff_kurt,
    SKEWNESS(population) AS population_skew, KURTOSIS(population) AS population_kurt,
    SKEWNESS(slot) AS slot_skew,            KURTOSIS(slot) AS slot_kurt,
    SKEWNESS(color) AS color_skew,          KURTOSIS(color) AS color_kurt,
    SKEWNESS(team) AS team_skew,            KURTOSIS(team) AS team_kurt,
    SKEWNESS(speedFactor) AS speedFactor_skew, KURTOSIS(speedFactor) AS speedFactor_kurt,
    SKEWNESS(treatyLength) AS treatyLength_skew, KURTOSIS(treatyLength) AS treatyLength_kurt,
    SKEWNESS(internalLeaderboardId) AS internalLeaderboardId_skew,
    KURTOSIS(internalLeaderboardId) AS internalLeaderboardId_kurt,
    SKEWNESS(EXTRACT(EPOCH FROM (finished - started)) / 60.0)
        FILTER (WHERE finished > started) AS duration_min_skew,
    KURTOSIS(EXTRACT(EPOCH FROM (finished - started)) / 60.0)
        FILTER (WHERE finished > started) AS duration_min_kurt
FROM matches_raw
```

### iqr_outlier_all

```sql
SELECT
    COUNT(*) FILTER (WHERE rating IS NOT NULL AND (rating < 386.5 OR rating > 1846.5)) AS rating_iqr_outliers,
    COUNT(*) FILTER (WHERE ratingDiff IS NOT NULL AND (ratingDiff < -64.0 OR ratingDiff > 64.0)) AS ratingDiff_iqr_outliers,
    COUNT(*) FILTER (WHERE slot IS NOT NULL AND (slot < -4.5 OR slot > 7.5)) AS slot_iqr_outliers,
    COUNT(*) FILTER (WHERE color IS NOT NULL AND (color < -2.5 OR color > 9.5)) AS color_iqr_outliers,
    COUNT(*) FILTER (WHERE team IS NOT NULL AND (team < -0.5 OR team > 3.5)) AS team_iqr_outliers,
    COUNT(*) FILTER (WHERE internalLeaderboardId IS NOT NULL AND (internalLeaderboardId < -13.5 OR internalLeaderboardId > 22.5)) AS internalLeaderboardId_iqr_outliers
FROM matches_raw
```

### topk_leaderboard

```sql
SELECT leaderboard AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE leaderboard IS NOT NULL
GROUP BY leaderboard
ORDER BY cnt DESC
LIMIT 5
```

### topk_civ

```sql
SELECT civ AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE civ IS NOT NULL
GROUP BY civ
ORDER BY cnt DESC
LIMIT 5
```

### topk_map

```sql
SELECT map AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE map IS NOT NULL
GROUP BY map
ORDER BY cnt DESC
LIMIT 5
```

### topk_gameMode

```sql
SELECT gameMode AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE gameMode IS NOT NULL
GROUP BY gameMode
ORDER BY cnt DESC
LIMIT 5
```

### topk_gameVariant

```sql
SELECT gameVariant AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE gameVariant IS NOT NULL
GROUP BY gameVariant
ORDER BY cnt DESC
LIMIT 5
```

### topk_speed

```sql
SELECT speed AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE speed IS NOT NULL
GROUP BY speed
ORDER BY cnt DESC
LIMIT 5
```

### topk_difficulty

```sql
SELECT difficulty AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE difficulty IS NOT NULL
GROUP BY difficulty
ORDER BY cnt DESC
LIMIT 5
```

### topk_startingAge

```sql
SELECT startingAge AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE startingAge IS NOT NULL
GROUP BY startingAge
ORDER BY cnt DESC
LIMIT 5
```

### topk_endingAge

```sql
SELECT endingAge AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE endingAge IS NOT NULL
GROUP BY endingAge
ORDER BY cnt DESC
LIMIT 5
```

### topk_mapSize

```sql
SELECT mapSize AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE mapSize IS NOT NULL
GROUP BY mapSize
ORDER BY cnt DESC
LIMIT 5
```

### topk_resources

```sql
SELECT resources AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE resources IS NOT NULL
GROUP BY resources
ORDER BY cnt DESC
LIMIT 5
```

### topk_victory

```sql
SELECT victory AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE victory IS NOT NULL
GROUP BY victory
ORDER BY cnt DESC
LIMIT 5
```

### topk_civilizationSet

```sql
SELECT civilizationSet AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE civilizationSet IS NOT NULL
GROUP BY civilizationSet
ORDER BY cnt DESC
LIMIT 5
```

### topk_revealMap

```sql
SELECT revealMap AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE revealMap IS NOT NULL
GROUP BY revealMap
ORDER BY cnt DESC
LIMIT 5
```

### topk_server

```sql
SELECT server AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE server IS NOT NULL
GROUP BY server
ORDER BY cnt DESC
LIMIT 5
```

### topk_privacy

```sql
SELECT privacy AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE privacy IS NOT NULL
GROUP BY privacy
ORDER BY cnt DESC
LIMIT 5
```

### topk_status

```sql
SELECT status AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE status IS NOT NULL
GROUP BY status
ORDER BY cnt DESC
LIMIT 5
```

### topk_country

```sql
SELECT country AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE country IS NOT NULL
GROUP BY country
ORDER BY cnt DESC
LIMIT 5
```

### topk_scenario

```sql
SELECT scenario AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE scenario IS NOT NULL
GROUP BY scenario
ORDER BY cnt DESC
LIMIT 5
```

### topk_modDataset

```sql
SELECT modDataset AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE modDataset IS NOT NULL
GROUP BY modDataset
ORDER BY cnt DESC
LIMIT 5
```

### topk_colorHex

```sql
SELECT colorHex AS value, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / 277099059, 2) AS pct
FROM matches_raw
WHERE colorHex IS NOT NULL
GROUP BY colorHex
ORDER BY cnt DESC
LIMIT 5
```

### duplicate_detection

```sql
SELECT matchId, profileId, COUNT(*) AS cnt
FROM matches_raw
GROUP BY matchId, profileId
HAVING COUNT(*) > 1
ORDER BY cnt DESC
LIMIT 20
```

### duplicate_totals

```sql
SELECT SUM(cnt) AS total_dup_rows, COUNT(*) AS dup_groups
FROM (
    SELECT matchId, profileId, COUNT(*) AS cnt
    FROM matches_raw
    GROUP BY matchId, profileId
    HAVING COUNT(*) > 1
)
```

### memory_footprint

```sql
SELECT
    total_blocks * block_size AS total_bytes,
    used_blocks * block_size AS used_bytes
FROM pragma_database_size()
```

### rating_stratified

```sql
SELECT
    'full_table' AS scope,
    COUNT(*) AS n_rows,
    SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) AS rating_null,
    ROUND(SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS rating_null_pct,
    ROUND(AVG(rating), 2) AS rating_mean,
    ROUND(STDDEV(rating), 2) AS rating_std,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rating) AS rating_median,
    SUM(CASE WHEN ratingDiff IS NULL THEN 1 ELSE 0 END) AS ratingdiff_null,
    ROUND(AVG(ratingDiff), 4) AS ratingdiff_mean
FROM matches_raw

UNION ALL

SELECT
    '1v1_ranked' AS scope,
    COUNT(*) AS n_rows,
    SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) AS rating_null,
    ROUND(SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS rating_null_pct,
    ROUND(AVG(rating), 2) AS rating_mean,
    ROUND(STDDEV(rating), 2) AS rating_std,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rating) AS rating_median,
    SUM(CASE WHEN ratingDiff IS NULL THEN 1 ELSE 0 END) AS ratingdiff_null,
    ROUND(AVG(ratingDiff), 4) AS ratingdiff_mean
FROM matches_raw
WHERE leaderboard IN ('rm_1v1', 'qp_rm_1v1')
```

### qq_ecdf_sample

```sql
SELECT
    rating,
    ratingDiff,
    EXTRACT(EPOCH FROM (finished - started)) / 60.0 AS duration_min,
    population,
    speedFactor
FROM (
    SELECT *
    FROM matches_raw
    TABLESAMPLE BERNOULLI(0.020000 PERCENT)
) sub
WHERE finished > started
```

## Data Sources

- `matches_raw` (277,099,059 rows) -- DuckDB table from 01_02_02
- Census JSON: `01_02_04_univariate_census.json`
- Bivariate findings: `01_02_06_bivariate_eda.md` (I3 classifications)
- Multivariate findings: `01_02_07_multivariate_analysis.md`
- Skewness/kurtosis: DuckDB native SKEWNESS()/KURTOSIS() -- exact, full table, 10 columns
- BERNOULLI sample: 0.02% (55,414 rows for QQ/ECDF visualization)
