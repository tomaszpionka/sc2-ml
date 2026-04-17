# 01_04_01 Data Cleaning Artifact — aoe2companion

**Generated:** 2026-04-17  
**Step:** 01_04_01  
**Dataset:** aoe2companion  

## Cleaning Registry

| Rule | Name | Condition | Action | Impact |
|------|------|-----------|--------|--------|
| R00 | Feature history scope | Full matches_raw, all game types, excluding profileId=-1 and duplicates | Create VIEW player_history_all as feature computation source | ~264,132,745 rows in player_history_all |
| R01 | Scope restriction | internalLeaderboardId NOT IN (6, 18) OR internalLeaderboardId IS NULL | Exclude from prediction target VIEW; retain in player_history_all | 216,027,260 rows excluded from prediction target (~78.0% of total) |
| R02 | Deduplication | Duplicate (matchId, profileId) rows; also any profileId=-1 rows | Keep first occurrence per matchId x profileId (ORDER BY started); exclude profileId=-1 | Excess rows removed: 5; profileId=-1 rows removed: 1 |
| R03 | Won complementarity | 2-row match where won not complementary; also 1-row and 3+ row matches | Exclude entire match (both rows) | Matches excluded: 5,052 |
| R04 | NULL cluster flag | All 10 game-settings columns simultaneously NULL | FLAG only (is_null_cluster = TRUE) -- retained in matches_1v1_clean | 11,184 rows flagged |
| R05 | ratings_raw.games outlier cap | ratings_raw.games > 1,775,011,321 (p99.9, empirically computed) | Winsorize to p99.9 = 1,775,011,321 in ratings_clean VIEW | 78,923 rows with games > 1M capped |

## CONSORT Flow

| Stage | N rows | N matches | Description |
|-------|--------|-----------|-------------|
| S0_raw | 277,099,059 | 74788989 | All rows in matches_raw |
| S1_scope_restricted | 61,071,799 | 30536248 | R01: internalLeaderboardId IN (6, 18) |
| S2_deduplicated | 61,071,794 | 30536248 | R02: deduplicated by (matchId, profileId) ORDER BY started; profileId=-1 excluded |
| S3_valid_complementary | 61,062,392 | 30531196 | R03: 2-row matches with complementary won only |
| excluded_S0_to_S1 | 216,027,260 | — | Out-of-scope leaderboards |
| excluded_S1_to_S2 | 5 | — | Duplicates + profileId=-1 |
| excluded_S2_to_S3 | 9,402 | — | Non-complementary won + non-2-row matches |

## Post-Cleaning Validation

- **V1 Rating coverage:** 73.8%
- **V2 No POST-GAME leakage:** PASS
- **V3 No negative ratings:** PASS
- **V7 No anonymous rows:** PASS

### V4 Leaderboard Distribution (matches_1v1_clean)

| Leaderboard | internalLeaderboardId | N rows |
|-------------|----------------------|--------|
| rm_1v1 | 6 | 53,686,164 |
| qp_rm_1v1 | 18 | 7,376,228 |

### V8 Leaderboard Diversity (player_history_all)

| Leaderboard | N rows |
|-------------|--------|
| rm_team | 102,711,158 |
| unranked | 65,939,173 |
| rm_1v1 | 53,694,518 |
| qp_rm_team | 19,707,154 |
| qp_rm_1v1 | 7,377,276 |
| rm_team_console | 3,472,383 |
| ew_team | 3,356,610 |
| unknown | 3,131,983 |
| ew_1v1 | 1,943,971 |
| rm_1v1_console | 1,600,477 |
| ew_1v1_redbullwololo | 594,890 |
| dm_team | 193,400 |
| qp_br_ffa | 167,984 |
| dm_1v1 | 94,508 |
| qp_ew_1v1 | 49,477 |
| qp_ew_team | 44,716 |
| ror_team | 23,308 |
| ror_1v1 | 15,775 |
| ew_1v1_console | 7,522 |
| ew_team_console | 5,812 |
| ew_1v1_redbullwololo_console | 650 |

## NULL Audit

### matches_1v1_clean

Total rows: 61,062,392

| Column | NULL count | NULL % |
|--------|-----------|--------|
| matchId | 0 | 0.0% |
| started | 0 | 0.0% |
| leaderboard | 0 | 0.0% |
| name | 37 | 0.0001% |
| server | 59,469,814 | 97.3919% |
| internalLeaderboardId | 0 | 0.0% |
| privacy | 0 | 0.0% |
| mod | 0 | 0.0% |
| map | 0 | 0.0% |
| difficulty | 0 | 0.0% |
| startingAge | 0 | 0.0% |
| fullTechTree | 11,198 | 0.0183% |
| allowCheats | 11,196 | 0.0183% |
| empireWarsMode | 215,820 | 0.3534% |
| endingAge | 0 | 0.0% |
| gameMode | 0 | 0.0% |
| lockSpeed | 11,196 | 0.0183% |
| lockTeams | 11,186 | 0.0183% |
| mapSize | 0 | 0.0% |
| population | 11,198 | 0.0183% |
| hideCivs | 22,701,220 | 37.1771% |
| recordGame | 11,196 | 0.0183% |
| regicideMode | 1,862,388 | 3.05% |
| gameVariant | 0 | 0.0% |
| resources | 0 | 0.0% |
| sharedExploration | 11,186 | 0.0183% |
| speed | 0 | 0.0% |
| speedFactor | 0 | 0.0% |
| suddenDeathMode | 214,514 | 0.3513% |
| antiquityMode | 36,676,142 | 60.0634% |
| civilizationSet | 0 | 0.0% |
| teamPositions | 11,196 | 0.0183% |
| teamTogether | 11,196 | 0.0183% |
| treatyLength | 4,392 | 0.0072% |
| turboMode | 11,184 | 0.0183% |
| victory | 0 | 0.0% |
| revealMap | 0 | 0.0% |
| scenario | 61,062,388 | 100.0% |
| password | 47,367,192 | 77.5718% |
| modDataset | 61,062,392 | 100.0% |
| profileId | 0 | 0.0% |
| rating | 15,999,234 | 26.2015% |
| color | 1,591 | 0.0026% |
| colorHex | 0 | 0.0% |
| slot | 0 | 0.0% |
| status | 0 | 0.0% |
| team | 1,222,484 | 2.002% |
| won | 0 | 0.0% |
| country | 1,373,052 | 2.2486% |
| shared | 0 | 0.0% |
| verified | 0 | 0.0% |
| civ | 0 | 0.0% |
| filename | 0 | 0.0% |
| is_null_cluster | 0 | 0.0% |

Zero-NULL assertions: matchId, profileId, started, won -- all PASS

### player_history_all

Total rows: 264,132,745

| Column | NULL count | NULL % |
|--------|-----------|--------|
| matchId | 0 | 0.0% |
| profileId | 0 | 0.0% |
| name | 625 | 0.0002% |
| started | 0 | 0.0% |
| leaderboard | 0 | 0.0% |
| internalLeaderboardId | 1,209,089 | 0.4578% |
| map | 0 | 0.0% |
| civ | 0 | 0.0% |
| rating | 104,676,152 | 39.6301% |
| color | 7,089 | 0.0027% |
| slot | 0 | 0.0% |
| team | 13,270,235 | 5.0241% |
| startingAge | 0 | 0.0% |
| gameMode | 0 | 0.0% |
| speed | 0 | 0.0% |
| won | 19,251 | 0.0073% |
| country | 21,936,289 | 8.305% |
| status | 0 | 0.0% |
| verified | 0 | 0.0% |
| filename | 0 | 0.0% |

Zero-NULL assertions: matchId, profileId, started -- all PASS
Zero-NULL evidence: 01_02_04 census (matches_raw_null_census) confirms null_count=0 for matchId, profileId, started in matches_raw.
Nullable finding: won has 19,251 NULLs (0.0073%) -- documented, not asserted

## Missingness Ledger

> **Note on rates:** All triage rates derive from VIEWs (filtered scope), not raw tables.
> A column with 42% NULL in matches_raw can be ~26% NULL in matches_1v1_clean.
> The ledger is authoritative for downstream decisions because Phase 02 features
> are computed from the VIEWs.

### Missingness Ledger: matches_1v1_clean

Total rows: 61,062,392 | Columns: 54

| Column | Dtype | pct_missing_total | mechanism | recommendation |
|--------|-------|-------------------|-----------|----------------|
| matchId | INTEGER | 0.0 | N/A | RETAIN_AS_IS |
| started | TIMESTAMP | 0.0 | N/A | RETAIN_AS_IS |
| leaderboard | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| name | VARCHAR | 0.0001 | MCAR | RETAIN_AS_IS |
| server | VARCHAR | 97.3919 | MNAR | DROP_COLUMN |
| internalLeaderboardId | INTEGER | 0.0 | N/A | RETAIN_AS_IS |
| privacy | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| mod | BOOLEAN | 0.0 | N/A | DROP_COLUMN |
| map | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| difficulty | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| startingAge | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| fullTechTree | BOOLEAN | 0.0183 | MAR | RETAIN_AS_IS |
| allowCheats | BOOLEAN | 0.0183 | MAR | RETAIN_AS_IS |
| empireWarsMode | BOOLEAN | 0.3534 | MAR | RETAIN_AS_IS |
| endingAge | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| gameMode | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| lockSpeed | BOOLEAN | 0.0183 | MAR | RETAIN_AS_IS |
| lockTeams | BOOLEAN | 0.0183 | MAR | RETAIN_AS_IS |
| mapSize | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| population | INTEGER | 0.0183 | MAR | RETAIN_AS_IS |
| hideCivs | BOOLEAN | 37.1771 | MAR | FLAG_FOR_IMPUTATION |
| recordGame | BOOLEAN | 0.0183 | MAR | RETAIN_AS_IS |
| regicideMode | BOOLEAN | 3.05 | MAR | RETAIN_AS_IS |
| gameVariant | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| resources | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| sharedExploration | BOOLEAN | 0.0183 | MAR | RETAIN_AS_IS |
| speed | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| speedFactor | FLOAT | 0.0 | N/A | RETAIN_AS_IS |
| suddenDeathMode | BOOLEAN | 0.3513 | MAR | RETAIN_AS_IS |
| antiquityMode | BOOLEAN | 60.0634 | MAR | DROP_COLUMN |
| civilizationSet | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| teamPositions | BOOLEAN | 0.0183 | MAR | RETAIN_AS_IS |
| teamTogether | BOOLEAN | 0.0183 | MAR | RETAIN_AS_IS |
| treatyLength | INTEGER | 0.0072 | MAR | RETAIN_AS_IS |
| turboMode | BOOLEAN | 0.0183 | MAR | RETAIN_AS_IS |
| victory | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| revealMap | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| scenario | VARCHAR | 100.0 | MAR | DROP_COLUMN |
| password | BOOLEAN | 77.5718 | MAR | DROP_COLUMN |
| modDataset | VARCHAR | 100.0 | MAR | DROP_COLUMN |
| profileId | INTEGER | 0.0 | N/A | RETAIN_AS_IS |
| rating | INTEGER | 26.2015 | MAR | FLAG_FOR_IMPUTATION |
| color | INTEGER | 0.0026 | MCAR | RETAIN_AS_IS |
| colorHex | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| slot | INTEGER | 0.0 | N/A | RETAIN_AS_IS |
| status | VARCHAR | 0.0 | N/A | DROP_COLUMN |
| team | INTEGER | 2.002 | MAR | RETAIN_AS_IS |
| won | BOOLEAN | 0.0 | N/A | RETAIN_AS_IS |
| country | VARCHAR | 2.2486 | MAR | RETAIN_AS_IS |
| shared | BOOLEAN | 0.0 | N/A | RETAIN_AS_IS |
| verified | BOOLEAN | 0.0 | N/A | RETAIN_AS_IS |
| civ | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| filename | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| is_null_cluster | BOOLEAN | 0.0 | N/A | RETAIN_AS_IS |

### Missingness Ledger: player_history_all

Total rows: 264,132,745 | Columns: 20

| Column | Dtype | pct_missing_total | mechanism | recommendation |
|--------|-------|-------------------|-----------|----------------|
| matchId | INTEGER | 0.0 | N/A | RETAIN_AS_IS |
| profileId | INTEGER | 0.0 | N/A | RETAIN_AS_IS |
| name | VARCHAR | 0.0002 | MCAR | RETAIN_AS_IS |
| started | TIMESTAMP | 0.0 | N/A | RETAIN_AS_IS |
| leaderboard | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| internalLeaderboardId | INTEGER | 0.4578 | MAR | RETAIN_AS_IS |
| map | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| civ | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| rating | INTEGER | 39.6301 | MAR | FLAG_FOR_IMPUTATION |
| color | INTEGER | 0.0027 | MCAR | RETAIN_AS_IS |
| slot | INTEGER | 0.0 | N/A | RETAIN_AS_IS |
| team | INTEGER | 5.0241 | MAR | FLAG_FOR_IMPUTATION |
| startingAge | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| gameMode | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| speed | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |
| won | BOOLEAN | 0.0073 | MAR | EXCLUDE_TARGET_NULL_ROWS |
| country | VARCHAR | 8.305 | MAR | FLAG_FOR_IMPUTATION |
| status | VARCHAR | 0.0 | N/A | DROP_COLUMN |
| verified | BOOLEAN | 0.0 | N/A | RETAIN_AS_IS |
| filename | VARCHAR | 0.0 | N/A | RETAIN_AS_IS |

## Decisions surfaced for downstream cleaning (01_04_02+)

### DS-AOEC-01
**Column(s):** server (97.39% in matches_1v1_clean / ~98% in raw matches_raw), scenario (100.00% / ~98.3%), modDataset (100.00% / ~99.7%), password (77.57% via 40-80% MAR-non-primary path / ~82.9% raw)

**Question:** All four -> DROP_COLUMN at 01_04_02+ (per Rule S4). 'scenario' and 'modDataset' are 100% NULL in cleaned scope (every row is NULL -- drop is unambiguous). 'password' falls below the 80% boundary in the cleaned scope and is routed through the 40-80% non-primary cost-benefit path; intent (drop) is the same. Note: VIEW rates differ from raw rates due to the matches_1v1_clean ranked-1v1 filter -- see the plan's note_on_rates for the principle.

### DS-AOEC-02
**Column(s):** antiquityMode (60.06% in matches_1v1_clean / ~68.66% in raw -- falls in 40-80% non-primary band -> DROP_COLUMN), hideCivs (37.18% in matches_1v1_clean / ~49.30% in raw -- now falls in 5-40% band -> FLAG_FOR_IMPUTATION, NOT DROP_COLUMN as raw-rate framing implied)

**Question:** Phase 02 decides if the imputed-with-indicator hideCivs is predictive; if not, drop in 01_04_02+. The recommendation drift between raw-rate (~49% suggesting drop) and VIEW-rate (37% suggesting flag) is a direct consequence of the matches_1v1_clean filter narrowing the scope; the audit reports VIEW-rate as authoritative.

### DS-AOEC-03
**Column(s):** mod, map, difficulty, startingAge, fullTechTree, allowCheats, empireWarsMode, endingAge, gameMode, lockSpeed, lockTeams, mapSize, population, recordGame, regicideMode, gameVariant, resources, sharedExploration, speed, speedFactor, suddenDeathMode, civilizationSet, teamPositions, teamTogether, treatyLength, turboMode, victory, revealMap

**Question:** Low-NULL game settings group. Each gets individual 01_02_04-grounded justification. Downstream disposition is RETAIN_AS_IS / FLAG_FOR_IMPUTATION per rate.

### DS-AOEC-04
**Column(s):** rating in matches_1v1_clean (~26% NULL in 1v1 scope per VIEW)

**Question:** Primary feature exception per Rule S4. Phase 02 imputation strategy (median-within-leaderboard + add_indicator) must be specified before Phase 02 begins.

### DS-AOEC-05
**Column(s):** country (~12.6% in raw, lower in 1v1 VIEW)

**Question:** Phase 02 -- 'Unknown' category encoding or add_indicator.

### DS-AOEC-06
**Column(s):** won in matches_1v1_clean

**Question:** 0 NULLs (R03 guarantees) -- per F1 zero-missingness override, ledger reports RETAIN_AS_IS / mechanism=N/A. Target-override post-step does NOT fire.

### DS-AOEC-07
**Column(s):** won in player_history_all (~5%)

**Question:** MAR; per the target-override post-step, recommendation becomes EXCLUDE_TARGET_NULL_ROWS. Feature computation must skip NULL-target rows.

### DS-AOEC-08
**Column(s):** leaderboards_raw, profiles_raw

**Question:** NOT_USABLE per 01_03_03; profiles_raw has 7 dead columns (100% NULL). Formally declare out-of-analytical-scope at 01_04_02+ -- these tables do not enter any VIEW and do not need triage.


## SQL Queries

### T01_scope_restriction

```sql
-- Scope restriction -- count rows before/after
SELECT
    'total' AS scope,
    COUNT(*) AS n_rows,
    COUNT(DISTINCT matchId) AS n_matches
FROM matches_raw

UNION ALL

SELECT
    'in_scope_1v1' AS scope,
    COUNT(*) AS n_rows,
    COUNT(DISTINCT matchId) AS n_matches
FROM matches_raw
WHERE internalLeaderboardId IN (6, 18)

UNION ALL

SELECT
    'out_of_scope' AS scope,
    COUNT(*) AS n_rows,
    COUNT(DISTINCT matchId) AS n_matches
FROM matches_raw
WHERE internalLeaderboardId NOT IN (6, 18)
   OR internalLeaderboardId IS NULL;
```

### T02_dup_stratification

```sql
-- Duplicate stratification (in-scope only)
WITH in_scope AS (
    SELECT *
    FROM matches_raw
    WHERE internalLeaderboardId IN (6, 18)
),
dup_groups AS (
    SELECT matchId, profileId, COUNT(*) AS row_count
    FROM in_scope
    GROUP BY matchId, profileId
    HAVING COUNT(*) > 1
)
SELECT
    CASE WHEN d.profileId = -1 THEN 'profileId_minus1' ELSE 'real_profileId' END AS stratum,
    COUNT(*) AS n_dup_groups,
    SUM(d.row_count) AS total_dup_rows,
    SUM(d.row_count) - COUNT(*) AS excess_rows
FROM dup_groups d
GROUP BY
    CASE WHEN d.profileId = -1 THEN 'profileId_minus1' ELSE 'real_profileId' END;
```

### T02_minus1_investigation

```sql
-- profileId=-1 investigation in 1v1 scope
SELECT
    COUNT(*) AS total_minus1_rows,
    COUNT(DISTINCT matchId) AS n_matches_with_minus1
FROM matches_raw
WHERE internalLeaderboardId IN (6, 18)
  AND profileId = -1;
```

### T03_won_consistency

```sql
-- Won consistency check (in-scope, 2-row matches only)
WITH in_scope_dedup AS (
    SELECT * EXCLUDE (rn)
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY matchId, profileId
                   ORDER BY started
               ) AS rn
        FROM matches_raw
        WHERE internalLeaderboardId IN (6, 18)
          AND profileId != -1
    ) sub
    WHERE rn = 1
),
match_pairs AS (
    SELECT
        matchId,
        COUNT(*) AS n_rows,
        COUNT(*) FILTER (WHERE won = TRUE) AS n_won_true,
        COUNT(*) FILTER (WHERE won = FALSE) AS n_won_false,
        COUNT(*) FILTER (WHERE won IS NULL) AS n_won_null
    FROM in_scope_dedup
    GROUP BY matchId
    HAVING COUNT(*) = 2
)
SELECT
    CASE
        WHEN n_won_true = 1 AND n_won_false = 1 THEN 'complementary'
        WHEN n_won_true = 2 THEN 'both_true'
        WHEN n_won_false = 2 THEN 'both_false'
        WHEN n_won_null > 0 THEN 'has_null'
        ELSE 'other'
    END AS won_pattern,
    COUNT(*) AS n_matches,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM match_pairs
GROUP BY won_pattern
ORDER BY n_matches DESC;
```

### T03_match_sizes

```sql
-- Non-2-row match counts in scope after dedup
WITH in_scope_dedup AS (
    SELECT * EXCLUDE (rn)
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY matchId, profileId
                   ORDER BY started
               ) AS rn
        FROM matches_raw
        WHERE internalLeaderboardId IN (6, 18)
          AND profileId != -1
    ) sub
    WHERE rn = 1
),
match_sizes AS (
    SELECT matchId, COUNT(*) AS n_rows FROM in_scope_dedup GROUP BY matchId
)
SELECT
    CASE WHEN n_rows = 1 THEN '1_row'
         WHEN n_rows = 2 THEN '2_rows'
         ELSE '3_plus_rows' END AS size_bucket,
    COUNT(*) AS n_matches,
    SUM(n_rows) AS total_rows
FROM match_sizes
GROUP BY size_bucket
ORDER BY size_bucket;
```

### T04_null_cluster

```sql
-- NULL cluster temporal stratification (in-scope)
WITH in_scope AS (
    SELECT * FROM matches_raw WHERE internalLeaderboardId IN (6, 18)
),
null_cluster AS (
    SELECT
        matchId, started,
        CASE
            WHEN allowCheats IS NULL AND lockSpeed IS NULL AND lockTeams IS NULL
             AND recordGame IS NULL AND sharedExploration IS NULL
             AND teamPositions IS NULL AND teamTogether IS NULL
             AND turboMode IS NULL AND fullTechTree IS NULL AND population IS NULL
            THEN TRUE ELSE FALSE
        END AS is_null_cluster
    FROM in_scope
)
SELECT is_null_cluster, COUNT(*) AS n_rows,
       MIN(started) AS min_date, MAX(started) AS max_date,
       COUNT(DISTINCT DATE_TRUNC('month', started)) AS n_months
FROM null_cluster
GROUP BY is_null_cluster;
```

### T04_null_monthly

```sql
-- Monthly breakdown: monthly temporal stratification of NULL cluster
WITH in_scope AS (
    SELECT * FROM matches_raw WHERE internalLeaderboardId IN (6, 18)
),
null_cluster AS (
    SELECT
        started,
        CASE
            WHEN allowCheats IS NULL AND lockSpeed IS NULL AND lockTeams IS NULL
             AND recordGame IS NULL AND sharedExploration IS NULL
             AND teamPositions IS NULL AND teamTogether IS NULL
             AND turboMode IS NULL AND fullTechTree IS NULL AND population IS NULL
            THEN TRUE ELSE FALSE
        END AS is_null_cluster
    FROM in_scope
)
SELECT
    DATE_TRUNC('month', started) AS month,
    COUNT(*) FILTER (WHERE is_null_cluster) AS null_cluster_rows,
    COUNT(*) FILTER (WHERE NOT is_null_cluster) AS normal_rows,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_null_cluster) / COUNT(*), 2) AS null_pct
FROM null_cluster
GROUP BY DATE_TRUNC('month', started)
ORDER BY month;
```

### T04_null_survival

```sql
-- NULL cluster survival after scope restriction, deduplication, and consistency filtering
WITH in_scope_dedup AS (
    SELECT * EXCLUDE (rn)
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY matchId, profileId ORDER BY started) AS rn
        FROM matches_raw
        WHERE internalLeaderboardId IN (6, 18) AND profileId != -1
    ) sub
    WHERE rn = 1
),
valid_matches AS (
    SELECT matchId FROM in_scope_dedup
    GROUP BY matchId
    HAVING COUNT(*) = 2
       AND COUNT(*) FILTER (WHERE won = TRUE) = 1
       AND COUNT(*) FILTER (WHERE won = FALSE) = 1
)
SELECT
    CASE
        WHEN d.allowCheats IS NULL AND d.lockSpeed IS NULL AND d.lockTeams IS NULL
         AND d.recordGame IS NULL AND d.sharedExploration IS NULL
         AND d.teamPositions IS NULL AND d.teamTogether IS NULL
         AND d.turboMode IS NULL AND d.fullTechTree IS NULL AND d.population IS NULL
        THEN 'null_cluster' ELSE 'normal'
    END AS cluster_status,
    COUNT(*) AS n_rows,
    COUNT(DISTINCT d.matchId) AS n_matches
FROM in_scope_dedup d
INNER JOIN valid_matches v ON d.matchId = v.matchId
GROUP BY cluster_status;
```

### T05_outlier_analysis

```sql
SELECT
    COUNT(*) AS total_rows,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY games) AS p99,
    PERCENTILE_CONT(0.999) WITHIN GROUP (ORDER BY games) AS p999,
    PERCENTILE_CONT(0.9999) WITHIN GROUP (ORDER BY games) AS p9999,
    MAX(games) AS max_val,
    COUNT(*) FILTER (WHERE games > 50000) AS n_above_50k,
    COUNT(*) FILTER (WHERE games > 100000) AS n_above_100k,
    COUNT(*) FILTER (WHERE games > 1000000) AS n_above_1M
FROM ratings_raw;
```

### T05_ratings_clean_view

```sql
CREATE OR REPLACE VIEW ratings_clean AS
SELECT
    profile_id, LEAST(games, 1775011321) AS games,
    rating, date, leaderboard_id, rating_diff, season, filename
FROM ratings_raw;
```

### T06_player_history_all_view

```sql
CREATE OR REPLACE VIEW player_history_all AS
WITH deduped AS (
    SELECT * EXCLUDE (rn)
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY matchId, profileId
                   ORDER BY started
               ) AS rn
        FROM matches_raw
        WHERE profileId != -1
    ) sub
    WHERE rn = 1
)
SELECT
    matchId,
    profileId,
    name,
    started,
    leaderboard,
    internalLeaderboardId,
    map,
    civ,
    rating,
    color,
    slot,
    team,
    startingAge,
    gameMode,
    speed,
    won,
    country,
    status,
    verified,
    filename
FROM deduped;
```

### T07_matches_1v1_clean_view

```sql
CREATE OR REPLACE VIEW matches_1v1_clean AS
SELECT
    d.matchId,
    d.started,
    d.leaderboard,
    d.name,
    d.server,
    d.internalLeaderboardId,
    d.privacy,
    d.mod,
    d.map,
    d.difficulty,
    d.startingAge,
    d.fullTechTree,
    d.allowCheats,
    d.empireWarsMode,
    d.endingAge,
    d.gameMode,
    d.lockSpeed,
    d.lockTeams,
    d.mapSize,
    d.population,
    d.hideCivs,
    d.recordGame,
    d.regicideMode,
    d.gameVariant,
    d.resources,
    d.sharedExploration,
    d.speed,
    d.speedFactor,
    d.suddenDeathMode,
    d.antiquityMode,
    d.civilizationSet,
    d.teamPositions,
    d.teamTogether,
    d.treatyLength,
    d.turboMode,
    d.victory,
    d.revealMap,
    d.scenario,
    d.password,
    d.modDataset,
    d.profileId,
    d.rating,
    d.color,
    d.colorHex,
    d.slot,
    d.status,
    d.team,
    d.won,
    d.country,
    d.shared,
    d.verified,
    d.civ,
    d.filename,
    CASE
        WHEN d.allowCheats IS NULL AND d.lockSpeed IS NULL AND d.lockTeams IS NULL
         AND d.recordGame IS NULL AND d.sharedExploration IS NULL
         AND d.teamPositions IS NULL AND d.teamTogether IS NULL
         AND d.turboMode IS NULL AND d.fullTechTree IS NULL AND d.population IS NULL
        THEN TRUE ELSE FALSE
    END AS is_null_cluster
FROM (
    SELECT * EXCLUDE (rn)
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY matchId, profileId
                   ORDER BY started
               ) AS rn
        FROM matches_raw
        WHERE internalLeaderboardId IN (6, 18)
          AND profileId != -1
    ) raw_rn
    WHERE rn = 1
) d
WHERE d.matchId IN (
    SELECT matchId
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY matchId, profileId
                   ORDER BY started
               ) AS rn
        FROM matches_raw
        WHERE internalLeaderboardId IN (6, 18)
          AND profileId != -1
    ) sub
    WHERE rn = 1
    GROUP BY matchId
    HAVING COUNT(*) = 2
       AND COUNT(*) FILTER (WHERE won = TRUE) = 1
       AND COUNT(*) FILTER (WHERE won = FALSE) = 1
);
```

### null_audit_matches_cols

```sql
WITH col_list AS (
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'matches_1v1_clean'
    ORDER BY ordinal_position
)
SELECT * FROM col_list;
```

### null_audit_hist_cols

```sql
WITH col_list AS (
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'player_history_all'
    ORDER BY ordinal_position
)
SELECT * FROM col_list;
```

### null_audit_per_column_template

```sql
SELECT COUNT(*) FILTER (WHERE "{column_name}" IS NULL) AS null_count FROM {view_name}
```

### missingness_sentinel_template

```sql
SELECT COUNT(*) FILTER (WHERE "{col}" {predicate}) FROM {view_name}
```

### missingness_constants_template

```sql
SELECT COUNT(DISTINCT "{col}") FROM {view_name}
```
