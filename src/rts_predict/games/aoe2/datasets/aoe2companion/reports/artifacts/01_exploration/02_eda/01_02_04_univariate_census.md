# Step 01_02_04 -- Univariate Census & Target Variable EDA

**Dataset:** aoe2companion
**Date:** 2026-04-14

All SQL queries that produced reported results are inlined below (Invariant #6).

---

## A. Full NULL census of matches_raw

```sql
SUMMARIZE matches_raw
SELECT COUNT(*) AS n FROM matches_raw
```

## A2. Empty-string investigation for VARCHAR columns

Investigates whether `difficulty`, `colorHex`, `startingAge`, `endingAge`, `civilizationSet`
(0 NULLs per SUMMARIZE) contain empty strings. Also confirms genuine NULLs for `scenario`
and `modDataset`. `password` (BOOLEAN) is excluded -- empty-string hypothesis does not apply.

```sql
-- Per column (col in empty_string_cols):
SELECT
    '{col}' AS column_name,
    COUNT(*) FILTER (WHERE "{col}" IS NULL)                                AS null_count,
    COUNT(*) FILTER (WHERE "{col}" = '')                                   AS empty_string_count,
    COUNT(*) FILTER (WHERE "{col}" IS NOT NULL AND "{col}" != '')          AS non_empty_count,
    COUNT(*)                                                               AS total_rows
FROM matches_raw
```

## B. Target variable (won)

### won NULL count: exact GROUP BY vs SUMMARIZE approximation

SUMMARIZE uses HyperLogLog approximation. The exact NULL count is taken from
the GROUP BY distribution query and patched into `matches_raw_null_census`.

### Overall distribution
```sql
SELECT
    won,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM matches_raw
GROUP BY won
ORDER BY cnt DESC
```

### Stratified by leaderboard
```sql
SELECT
    leaderboard,
    won,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(PARTITION BY leaderboard), 2) AS pct
FROM matches_raw
GROUP BY leaderboard, won
ORDER BY leaderboard, won
```

### Intra-match consistency check (2-row matches)
```sql
WITH match_pairs AS (
    SELECT
        matchId,
        COUNT(*) AS n_rows,
        COUNT(*) FILTER (WHERE won = TRUE) AS won_true,
        COUNT(*) FILTER (WHERE won = FALSE) AS won_false,
        COUNT(*) - COUNT(won) AS won_null
    FROM matches_raw
    GROUP BY matchId
    HAVING COUNT(*) = 2
)
SELECT
    COUNT(*) AS total_2row_matches,
    COUNT(*) FILTER (WHERE won_true = 1 AND won_false = 1)
        AS consistent_complement,
    COUNT(*) FILTER (WHERE won_null = 2) AS both_null,
    COUNT(*) FILTER (WHERE won_true = 1 AND won_null = 1)
        AS one_true_one_null,
    COUNT(*) FILTER (WHERE won_false = 1 AND won_null = 1)
        AS one_false_one_null,
    COUNT(*) FILTER (WHERE won_true = 2) AS both_true,
    COUNT(*) FILTER (WHERE won_false = 2) AS both_false,
    COUNT(*) FILTER (WHERE won_true = 0 AND won_false = 0
        AND won_null < 2) AS other_inconsistent
FROM match_pairs
```

## C. Match structure by leaderboard

```sql
SELECT
    leaderboard,
    COUNT(DISTINCT matchId) AS distinct_matches,
    COUNT(*) AS total_rows,
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT matchId), 2) AS avg_rows_per_match
FROM matches_raw
GROUP BY leaderboard
ORDER BY total_rows DESC
```

## D. Categorical field profiles

```sql
-- Per column (col in categorical list):
SELECT
    "{col}" AS value,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM matches_raw
GROUP BY "{col}"
ORDER BY cnt DESC
LIMIT 30
```

### name (cardinality only)
```sql
SELECT
    COUNT(DISTINCT name) AS distinct_names,
    COUNT(*) - COUNT(name) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(name)) / COUNT(*), 2) AS null_pct
FROM matches_raw
```

### colorHex (cardinality only)
```sql
SELECT
    COUNT(DISTINCT "colorHex") AS distinct_values,
    COUNT(*) - COUNT("colorHex") AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT("colorHex")) / COUNT(*), 2) AS null_pct
FROM matches_raw
```

## E. Boolean field census

```sql
-- Per boolean column:
SELECT
    '{col}' AS column_name,
    COUNT(*) FILTER (WHERE "{col}" = TRUE) AS true_count,
    COUNT(*) FILTER (WHERE "{col}" = FALSE) AS false_count,
    COUNT(*) - COUNT("{col}") AS null_count
FROM matches_raw
```

## F. Numeric descriptive statistics

```sql
-- Per numeric column (matches_raw, ratings_raw, leaderboards_raw):
SELECT
    '{col}' AS column_name,
    MIN("{col}") AS min_val,
    MAX("{col}") AS max_val,
    ROUND(AVG("{col}"), 2) AS mean_val,
    ROUND(MEDIAN("{col}"), 2) AS median_val,
    ROUND(STDDEV("{col}"), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY "{col}") AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY "{col}") AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY "{col}") AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY "{col}") AS p95
FROM <table>
WHERE "{col}" IS NOT NULL
```

## F2. Zero counts for numeric columns

`profiles_raw` excluded -- its only numeric column (`profileId`) is an identifier.

```sql
-- Per column (col in numeric zero cols list, table in matches_raw / ratings_raw / leaderboards_raw):
SELECT
    '{col}' AS column_name,
    COUNT(*) FILTER (WHERE "{col}" = 0)                                                  AS zero_count,
    COUNT(*) FILTER (WHERE "{col}" IS NOT NULL)                                          AS non_null_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE "{col}" = 0)
        / NULLIF(COUNT(*) FILTER (WHERE "{col}" IS NOT NULL), 0), 2)                    AS zero_pct_of_non_null
FROM <table>
```

## F1b. Skewness and Kurtosis (EDA Manual Section 3.1)

```sql
-- Per numeric column (col in numeric cols list, table in matches_raw / ratings_raw / leaderboards_raw):
SELECT
    '{col}' AS column_name,
    ROUND(SKEWNESS("{col}"), 4) AS skewness,
    ROUND(KURTOSIS("{col}"), 4) AS kurtosis
FROM <table>
WHERE "{col}" IS NOT NULL
```

matches_raw numeric columns (9): rating, ratingDiff, population, slot, color,
    team, speedFactor, treatyLength, internalLeaderboardId
ratings_raw numeric columns (5): leaderboard_id, season, rating, games, rating_diff
leaderboards_raw numeric columns (10): rank, rating, wins, losses, games,
    streak, drops, rankCountry, season, rankLevel

## G. Temporal range

### matches_raw temporal range
```sql
SELECT
    MIN(started) AS earliest_match,
    MAX(started) AS latest_match,
    MIN(finished) AS earliest_finish,
    MAX(finished) AS latest_finish,
    COUNT(DISTINCT CAST(started AS DATE)) AS distinct_match_dates
FROM matches_raw
```

### ratings_raw temporal range
```sql
SELECT
    MIN(date) AS earliest_rating,
    MAX(date) AS latest_rating,
    COUNT(DISTINCT CAST(date AS DATE)) AS distinct_rating_dates
FROM ratings_raw
```

### Match duration distribution
```sql
SELECT
    ROUND(AVG(EXTRACT(EPOCH FROM (finished - started))), 2) AS avg_duration_secs,
    ROUND(MEDIAN(EXTRACT(EPOCH FROM (finished - started))), 2)
        AS median_duration_secs,
    MIN(EXTRACT(EPOCH FROM (finished - started))) AS min_duration_secs,
    MAX(EXTRACT(EPOCH FROM (finished - started))) AS max_duration_secs,
    PERCENTILE_CONT(0.05) WITHIN GROUP
        (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p05_secs,
    PERCENTILE_CONT(0.95) WITHIN GROUP
        (ORDER BY EXTRACT(EPOCH FROM (finished - started))) AS p95_secs
FROM matches_raw
WHERE finished > started
```

### Excluded rows
```sql
SELECT
    COUNT(*) FILTER (WHERE finished IS NULL OR started IS NULL)
        AS null_timestamp_count,
    COUNT(*) FILTER (WHERE finished IS NOT NULL AND started IS NOT NULL
        AND finished <= started)
        AS non_positive_duration_count
FROM matches_raw
```

### Monthly match counts
```sql
SELECT
    DATE_TRUNC('month', started) AS month,
    COUNT(DISTINCT matchId) AS distinct_matches,
    COUNT(*) AS total_rows
FROM matches_raw
WHERE started IS NOT NULL
GROUP BY month
ORDER BY month
```

## H. Auxiliary table NULL census

```sql
SUMMARIZE leaderboards_raw
SUMMARIZE profiles_raw
SUMMARIZE ratings_raw
SELECT COUNT(*) FROM leaderboards_raw
SELECT COUNT(*) FROM profiles_raw
SELECT COUNT(*) FROM ratings_raw
```

### H.1b leaderboards_raw categorical, boolean, and temporal

#### leaderboard VARCHAR (all values)
```sql
SELECT
    leaderboard AS value,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM leaderboards_raw
GROUP BY leaderboard
ORDER BY cnt DESC
```

#### country VARCHAR (top 30)
```sql
SELECT country AS value, COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM leaderboards_raw GROUP BY country ORDER BY cnt DESC LIMIT 30
```

#### active BOOLEAN census
```sql
SELECT 'active' AS column_name,
    COUNT(*) FILTER (WHERE active = TRUE) AS true_count,
    COUNT(*) FILTER (WHERE active = FALSE) AS false_count,
    COUNT(*) - COUNT(active) AS null_count,
    COUNT(*) AS total_rows,
    ROUND(100.0 * COUNT(*) FILTER (WHERE active = TRUE) / COUNT(*), 2) AS true_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE active = FALSE) / COUNT(*), 2) AS false_pct,
    ROUND(100.0 * (COUNT(*) - COUNT(active)) / COUNT(*), 2) AS null_pct
FROM leaderboards_raw
```

#### lastMatchTime and updatedAt temporal ranges
```sql
SELECT
    'lastMatchTime' AS column_name,
    MIN("lastMatchTime") AS min_val,
    MAX("lastMatchTime") AS max_val
FROM leaderboards_raw
UNION ALL
SELECT
    'updatedAt' AS column_name,
    MIN("updatedAt") AS min_val,
    MAX("updatedAt") AS max_val
FROM leaderboards_raw
```

#### ratings_raw leaderboard_id distribution
```sql
SELECT leaderboard_id AS value, COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM ratings_raw GROUP BY leaderboard_id ORDER BY cnt DESC
```

### H.2b profiles_raw categorical

Note: 7 dead columns documented in constant_fields (sharedHistory, twitchChannel,
youtubeChannel, youtubeChannelName, discordId, discordName, discordInvitation).

#### country VARCHAR (top 30)
```sql
SELECT country AS value, COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM profiles_raw GROUP BY country ORDER BY cnt DESC LIMIT 30
```

#### clan VARCHAR (top 30)
```sql
SELECT clan AS value, COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM profiles_raw GROUP BY clan ORDER BY cnt DESC LIMIT 30
```

## I. Dead/constant/near-constant field detection

### I.1 Dead fields (BLOCKER fix)

Detection uses (approx_cardinality <= 1) OR (null_pct >= 100.0) -- the OR condition
catches profiles_raw columns that are 100% NULL but have phantom HyperLogLog
cardinalities > 1 due to approximation error (Flajolet et al. 2007).

### I.2 Near-constant fields (two-bucket split, EDA Manual Section 3.3)

**Threshold:** NEAR_CONSTANT_CARDINALITY_THRESHOLD = 100
**Rationale (I7):** max clearly categorical cardinality is ~68 (civ); next meaningful
categorical is map (~261). At N=277M rows, uniqueness_ratio < 0.001 flags all columns
with < 277,000 distinct values -- including semantically important categoricals.

- **Bucket 1 (near_constant_low_cardinality):** uniqueness_ratio < 0.001 AND
  approx_cardinality in [2, 100) AND null_pct < 100 -- genuinely low-cardinality
- **Bucket 2 (near_constant_ratio_flagged):** uniqueness_ratio < 0.001 AND
  approx_cardinality >= 100 -- ratio-flagged but NOT true near-constants
  (includes map=261, which is semantically important)

### I2. Duplicate row detection

#### matches_raw (matchId, profileId) pairs
```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT CAST("matchId" AS VARCHAR) || '|' || CAST("profileId" AS VARCHAR))
        AS distinct_pairs,
    COUNT(*) - COUNT(DISTINCT CAST("matchId" AS VARCHAR) || '|' || CAST("profileId" AS VARCHAR))
        AS duplicate_rows
FROM matches_raw
```

#### ratings_raw (profile_id, leaderboard_id, date) triples
```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT CAST(profile_id AS VARCHAR) || '|'
        || CAST(leaderboard_id AS VARCHAR) || '|'
        || CAST(date AS VARCHAR))
        AS distinct_triples,
    COUNT(*) - COUNT(DISTINCT CAST(profile_id AS VARCHAR) || '|'
        || CAST(leaderboard_id AS VARCHAR) || '|'
        || CAST(date AS VARCHAR))
        AS duplicate_rows
FROM ratings_raw
```

### I3. NULL co-occurrence for 0.15%-0.16% clusters

Two distinct NULL clusters:
- **Cluster A** (8 cols, null_count=415,649): allowCheats, lockSpeed, lockTeams,
  recordGame, sharedExploration, teamPositions, teamTogether, turboMode
- **Cluster B** (2 cols, null_count=443,358): fullTechTree, population

#### Cluster A co-occurrence
```sql
SELECT
    COUNT(*) AS all_eight_null_simultaneously,
    (SELECT COUNT(*) FROM matches_raw WHERE "allowCheats" IS NULL)
        AS allowCheats_null_count
FROM matches_raw
WHERE "allowCheats" IS NULL
    AND "lockSpeed" IS NULL AND "lockTeams" IS NULL
    AND "recordGame" IS NULL AND "sharedExploration" IS NULL
    AND "teamPositions" IS NULL AND "teamTogether" IS NULL
    AND "turboMode" IS NULL
```

#### Cluster B co-occurrence
```sql
SELECT
    COUNT(*) AS both_null,
    (SELECT COUNT(*) FROM matches_raw WHERE "fullTechTree" IS NULL)
        AS fullTechTree_null_count,
    (SELECT COUNT(*) FROM matches_raw WHERE population IS NULL)
        AS population_null_count
FROM matches_raw
WHERE "fullTechTree" IS NULL AND population IS NULL
```

#### Cross-cluster overlap
```sql
SELECT
    COUNT(*) FILTER (WHERE "allowCheats" IS NULL AND "fullTechTree" IS NULL)
        AS both_clusters_null,
    COUNT(*) FILTER (WHERE "allowCheats" IS NULL AND "fullTechTree" IS NOT NULL)
        AS cluster_a_only_null,
    COUNT(*) FILTER (WHERE "allowCheats" IS NOT NULL AND "fullTechTree" IS NULL)
        AS cluster_b_only_null
FROM matches_raw
```

### T07. Memory footprint

DuckDB file size recorded via `os.path.getsize(str(db._dataset.db_file))`.

## Post-game field annotations (Invariant #3)

Columns encoding match outcome -- temporal leakage risk if used as features.

| table | column | type | reason |
|-------|--------|------|--------|
| matches_raw | ratingDiff | INTEGER | Rating change resulting from match outcome. Using this to predict the match it encodes would be temporal leakage (Invariant #3). |
| ratings_raw | rating_diff | BIGINT | Rating change resulting from match outcome. Semantically identical to matches_raw.ratingDiff. Using this to predict the match it encodes would be temporal leakage (Invariant #3). |
| matches_raw | won | BOOLEAN | Prediction target. Post-game by definition. |
| matches_raw | finished | TIMESTAMP | Match end timestamp. Known only after match completes. |

## Field Classification (preliminary)

Table: matches_raw | Status: preliminary | Columns annotated: 55

Formal boundary deferred to Phase 02 (Feature Engineering).

| column | temporal_class | notes |
|--------|---------------|-------|
| matchId | identifier | Match identifier |
| profileId | identifier | Player identifier |
| name | identifier | Player name |
| filename | identifier | Source file provenance (I10) |
| won | target | Prediction target |
| ratingDiff | post_game | Rating change from match outcome (Invariant #3) |
| finished | post_game | Match end timestamp |
| rating | ambiguous_pre_or_post | Could be pre-match or post-match snapshot -- identical 42.46% NULL rate suggests co-occurrence with ratingDiff (unverified; needs row-level check) |
| started | pre_game | Match start timestamp |
| leaderboard | pre_game | Ranked queue / game mode |
| internalLeaderboardId | pre_game | Numeric leaderboard ID |
| map | pre_game | Map selection |
| mapSize | pre_game | Map size setting |
| civ | pre_game | Civilization selection |
| gameMode | pre_game | Game mode |
| gameVariant | pre_game | Game variant |
| speed | pre_game | Game speed setting |
| speedFactor | pre_game | Speed multiplier |
| population | pre_game | Population cap |
| resources | pre_game | Resource setting |
| startingAge | pre_game | Starting age setting |
| endingAge | pre_game | Ending age setting |
| victory | pre_game | Victory condition |
| difficulty | pre_game | AI difficulty setting |
| civilizationSet | pre_game | Civ set restriction |
| revealMap | pre_game | Map visibility setting |
| treatyLength | pre_game | Treaty length setting |
| mod | pre_game | Mod enabled flag |
| fullTechTree | pre_game | Full tech tree toggle |
| allowCheats | pre_game | Cheats toggle |
| empireWarsMode | pre_game | Empire Wars toggle |
| lockSpeed | pre_game | Lock speed toggle |
| lockTeams | pre_game | Lock teams toggle |
| hideCivs | pre_game | Hide civs toggle |
| recordGame | pre_game | Record game toggle |
| regicideMode | pre_game | Regicide toggle |
| sharedExploration | pre_game | Shared exploration toggle |
| suddenDeathMode | pre_game | Sudden death toggle |
| antiquityMode | pre_game | Antiquity mode toggle |
| teamPositions | pre_game | Team positions toggle |
| teamTogether | pre_game | Team together toggle |
| turboMode | pre_game | Turbo mode toggle |
| color | pre_game | Player color slot |
| colorHex | pre_game | Player color hex code |
| slot | pre_game | Player slot number |
| team | pre_game | Team assignment |
| password | pre_game | Password-protected match (BOOLEAN, 82.9% NULL) |
| scenario | pre_game | Scenario name (98.27% NULL) |
| modDataset | pre_game | Mod dataset name (99.72% NULL) |
| server | context | Server (97.99% NULL) |
| privacy | context | Player privacy setting |
| status | context | Player status |
| country | context | Player country |
| shared | context | Shared flag |
| verified | context | Verified flag |

---

*Generated by notebook 01_02_04_univariate_census.py*