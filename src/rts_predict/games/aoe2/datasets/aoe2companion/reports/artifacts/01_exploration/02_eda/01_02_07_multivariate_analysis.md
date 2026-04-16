# Step 01_02_07 -- Multivariate EDA: aoe2companion

**Phase:** 01 -- Data Exploration
**Pipeline Section:** 01_02 -- Exploratory Data Analysis
**Dataset:** aoe2companion
**Predecessor:** 01_02_06 (Bivariate EDA)
**Invariants applied:** #3, #6, #7, #9

## Feature Classification Table (I3)

| Column | I3 Classification | In Heatmap | In PCA | PCA Exclusion Reason |
|--------|-------------------|------------|--------|---------------------|
| rating | AMBIGUOUS | Yes | No | AMBIGUOUS -- deferred to Phase 02 |
| ratingDiff | POST-GAME | Yes | No | POST-GAME (I3) |
| duration_min | POST-GAME | Yes | No | POST-GAME (I3) |
| population | PRE-GAME | Yes | No | p25==p75==200.0 |
| speedFactor | PRE-GAME | Yes | No | p25==p75==1.7000000476837158 |
| treatyLength | PRE-GAME | Yes | No | p25==p75==0.0 |
| internalLeaderboardId | PRE-GAME | Yes | No | nominal categorical (122 distinct IDs) -- excluded from PCA, retained in heatmap |
| slot | NOT-A-FEATURE | No | No | UI/positional index |
| color | NOT-A-FEATURE | No | No | UI/positional index |
| team | NOT-A-FEATURE | No | No | UI/positional index |

## Plot Index

| # | Title | Filename | Question | Feature Scope |
|---|-------|----------|----------|---------------|
| 1 | Spearman Cluster-Ordered Heatmap | `01_02_07_spearman_heatmap_all.png` | Feature redundancy clusters | All -- I3-labelled axes |
| 2 | Degenerate PCA Fallback | `01_02_07_pca_biplot.png` | Feature scatter (PCA degenerate) | PRE-GAME only |

## SQL Queries (Invariant #6)

### spearman_sample_all

```sql
SELECT
    rating,
    ratingDiff,
    EXTRACT(EPOCH FROM (finished - started)) / 60.0 AS duration_min,
    population,
    speedFactor,
    treatyLength,
    internalLeaderboardId
FROM (
    SELECT
        rating,
        ratingDiff,
        finished,
        started,
        population,
        speedFactor,
        treatyLength,
        internalLeaderboardId,
        leaderboard
    FROM matches_raw
    TABLESAMPLE BERNOULLI(0.036088 PERCENT)
) sub
WHERE rating IS NOT NULL
  AND rating > 0
  AND ratingDiff IS NOT NULL
  AND finished > started
  AND population IS NOT NULL
  AND treatyLength IS NOT NULL
  AND internalLeaderboardId IS NOT NULL
  AND leaderboard IN ('rm_1v1', 'qp_rm_1v1')
```

## PCA Degeneracy Note

PCA is degenerate for aoe2companion: only 0 pre-game numeric features survive after excluding POST-GAME (ratingDiff, duration), AMBIGUOUS (rating), NOT-A-FEATURE (slot, color, team), and near-constant columns (population, speedFactor, treatyLength). This confirms that aoe2companion's pre-game feature space is effectively low-dimensional for raw numeric columns. Phase 02 must engineer features from temporal history (win rates, Elo trajectories, civ matchup stats) to build a useful feature set.

## Interpretation Notes

### Near-constant columns
speedFactor (stddev=0.09, 4 distinct values) and treatyLength (96.56% zero) are near-constant in 1v1 ranked play. Their Spearman coefficients should be interpreted with caution.

### Pre-game feature poverty
aoe2companion matches_raw has very few genuinely numeric pre-game features. Phase 02 must engineer features from temporal match history (rolling win rates, Elo trajectories, head-to-head stats, civ matchup statistics) to build a useful prediction feature set.

## Data Sources

- `matches_raw` (277,099,059 rows) -- DuckDB table from 01_02_02
- Census JSON: `01_02_04_univariate_census.json` (50 keys)
- Bivariate findings: `01_02_06_bivariate_eda.md` (I3 classifications)
- Sample fraction: 0.036088% (BERNOULLI, targeting 100,000 rows)
