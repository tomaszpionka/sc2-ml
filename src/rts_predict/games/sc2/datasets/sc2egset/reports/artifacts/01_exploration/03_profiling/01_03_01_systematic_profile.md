# Step 01_03_01 -- Systematic Data Profiling
## sc2egset Dataset

**Phase:** 01 -- Data Exploration
**Pipeline Section:** 01_03 -- Systematic Data Profiling
**Predecessor:** 01_02_05
**Date:** 2026-04-16
**Invariants applied:** #3 (temporal classification), #6 (SQL verbatim), #7 (cited thresholds), #9 (no feature computation)

---

## Temporal Classification (Invariant #3)

> Note: `elapsed_game_loops` was reclassified as **POST-GAME** on 2026-04-15.
> The census artifact (01_02_04) still shows it as `in_game`; this notebook records the corrected classification.

| Table | Column | I3 Classification |
|-------|--------|-------------------|
| replay_players_raw | filename | IDENTIFIER |
| replay_players_raw | toon_id | IDENTIFIER |
| replay_players_raw | nickname | IDENTIFIER |
| replay_players_raw | playerID | IDENTIFIER |
| replay_players_raw | userID | IDENTIFIER |
| replay_players_raw | MMR | PRE_GAME |
| replay_players_raw | race | PRE_GAME |
| replay_players_raw | selectedRace | PRE_GAME |
| replay_players_raw | handicap | PRE_GAME |
| replay_players_raw | region | PRE_GAME |
| replay_players_raw | realm | PRE_GAME |
| replay_players_raw | highestLeague | PRE_GAME |
| replay_players_raw | isInClan | PRE_GAME |
| replay_players_raw | clanTag | PRE_GAME |
| replay_players_raw | startDir | PRE_GAME |
| replay_players_raw | startLocX | PRE_GAME |
| replay_players_raw | startLocY | PRE_GAME |
| replay_players_raw | color_a | PRE_GAME |
| replay_players_raw | color_b | PRE_GAME |
| replay_players_raw | color_g | PRE_GAME |
| replay_players_raw | color_r | PRE_GAME |
| replay_players_raw | APM | IN_GAME |
| replay_players_raw | SQ | IN_GAME |
| replay_players_raw | supplyCappedPercent | IN_GAME |
| replay_players_raw | result | TARGET |
| replays_meta_raw | filename | IDENTIFIER |
| replays_meta_raw | time_utc | PRE_GAME |
| replays_meta_raw | game_version_header | PRE_GAME |
| replays_meta_raw | base_build | PRE_GAME |
| replays_meta_raw | data_build | PRE_GAME |
| replays_meta_raw | game_version_meta | PRE_GAME |
| replays_meta_raw | map_name | PRE_GAME |
| replays_meta_raw | max_players | PRE_GAME |
| replays_meta_raw | map_size_x | PRE_GAME |
| replays_meta_raw | map_size_y | PRE_GAME |
| replays_meta_raw | is_blizzard_map | PRE_GAME |
| replays_meta_raw | is_blizzard_map_init | PRE_GAME |
| replays_meta_raw | elapsed_game_loops | POST-GAME (reclassified 2026-04-15) |
| replays_meta_raw | game_speed | CONSTANT |
| replays_meta_raw | game_speed_init | CONSTANT |
| replays_meta_raw | gameEventsErr | CONSTANT |
| replays_meta_raw | messageEventsErr | CONSTANT |
| replays_meta_raw | trackerEvtsErr | CONSTANT |
| map_aliases_raw | tournament | IDENTIFIER/REFERENCE |
| map_aliases_raw | foreign_name | IDENTIFIER/REFERENCE |
| map_aliases_raw | english_name | IDENTIFIER/REFERENCE |
| map_aliases_raw | filename | IDENTIFIER/REFERENCE |

---

## Table Summaries

| Table | Rows | Columns | Duplicates |
|-------|------|---------|------------|
| replay_players_raw | 44,817 | 25 | 0 (on filename, playerID) |
| replays_meta_raw | 22,390 | 9 top-level + 17 struct-flat | N/A |
| map_aliases_raw | 104,160 | 4 | N/A |

---

## Column-Level Profile: replay_players_raw Numeric Columns

| column | n_rows | null_pct | zero_pct | cardinality | mean | std | skewness | kurtosis |
|--------|--------|----------|----------|-------------|------|-----|----------|----------|
| MMR | 44,817.0 | 0.0000 | 83.6491 | 1,031 | 738.71 | 3035.53 | -5.7590 | 77.8914 |
| MMR_rated_only | 7,169.0 | 0.0000 | 0.0000 | 1,029 | 5425.38 | 1481.12 | -0.7753 | -0.8569 |
| APM | 44,817.0 | 0.0000 | 2.5258 | 556 | 355.57 | 104.87 | -0.2024 | 3.6247 |
| SQ | 44,817.0 | 0.0000 | 0.0000 | 171 | -95711.06 | 14345597.84 | -149.6897 | 22405.9998 |
| SQ_no_sentinel | 44,815.0 | 0.0000 | 0.0000 | 170 | 122.38 | 18.91 | -0.3200 | 0.6632 |
| supplyCappedPercent | 44,817.0 | 0.0000 | 0.6649 | 51 | 7.24 | 4.71 | 2.2456 | 18.1756 |
| handicap | 44,817.0 | 0.0000 | 0.0045 | 2 | 100.00 | 0.67 | -149.6897 | 22405.9998 |

### MMR IQR Outlier Note (W-03)

**MMR IQR outlier count for all rows is degenerate (IQR=0 since Q1=Q3=0):**
- All-rows IQR outlier count: 7,328
  (equals the number of rated players — every MMR>0 row is flagged)
- **Rated-only (MMR>0) IQR outlier count: 0**
  (computed on the 7,328 rated rows only)
- Rated IQR: P25=4203.0, P75=6584.0,
  IQR=2381.0

IQR fence at 1.5*IQR per Tukey (1977) — Invariant #7.

---

## Categorical Top-5 Profiles

#### result
| value | count | pct |
|-------|-------|-----|
| Loss | 22,409 | 50.0011% |
| Win | 22,382 | 49.9409% |
| Undecided | 24 | 0.0536% |
| Tie | 2 | 0.0045% |

#### race
| value | count | pct |
|-------|-------|-----|
| Prot | 16,228 | 36.2095% |
| Zerg | 15,695 | 35.0202% |
| Terr | 12,891 | 28.7636% |
| BWPr | 1 | 0.0022% |
| BWZe | 1 | 0.0022% |

#### selectedRace
| value | count | pct |
|-------|-------|-----|
| Prot | 15,948 | 35.5847% |
| Zerg | 15,123 | 33.7439% |
| Terr | 12,623 | 28.1657% |
|  | 1,110 | 2.4767% |
| Rand | 10 | 0.0223% |

#### highestLeague
| value | count | pct |
|-------|-------|-----|
| Unknown | 32,338 | 72.1557% |
| Master | 6,458 | 14.4097% |
| Grandmaster | 4,745 | 10.5875% |
| Diamond | 718 | 1.6021% |
| Unranked | 224 | 0.4998% |

#### region
| value | count | pct |
|-------|-------|-----|
| Europe | 21,022 | 46.9063% |
| US | 12,699 | 28.3352% |
| Unknown | 5,748 | 12.8255% |
| Korea | 3,604 | 8.0416% |
| China | 1,742 | 3.8869% |

#### realm
| value | count | pct |
|-------|-------|-----|
| Europe | 20,777 | 46.3596% |
| North America | 12,490 | 27.8689% |
| Unknown | 5,748 | 12.8255% |
| Korea | 2,835 | 6.3257% |
| China | 1,742 | 3.8869% |

#### isInClan
| value | count | pct |
|-------|-------|-----|
| false | 33,210 | 74.1013% |
| true | 11,607 | 25.8987% |

#### clanTag
| value | count | pct |
|-------|-------|-----|
|  | 33,210 | 74.1013% |
| αX | 778 | 1.7359% |
| PSISTM | 532 | 1.1870% |
| mouz | 513 | 1.1447% |
| RBLN | 466 | 1.0398% |

---

## Critical Findings

### Dead Fields (null_pct == 100%)
None (0% NULL rate across all tables confirmed by 01_02_04 census).

### Constant Columns (cardinality == 1)
- `game_speed`
- `game_speed_init`
- `gameEventsErr`
- `messageEventsErr`
- `trackerEvtsErr`

These 5 columns must be dropped before feature engineering (Phase 02).

### Near-Constant Columns (uniqueness_ratio < 0.001 OR IQR == 0)
- `MMR`
- `color_a`
- `color_b`
- `color_g`
- `color_r`
- `handicap`
- `highestLeague`
- `isInClan`
- `is_blizzard_map`
- `is_blizzard_map_init`
- `map_size_x`
- `map_size_y`
- `max_players`
- `playerID`
- `race`
- `realm`
- `region`
- `result`
- `selectedRace`
- `startDir`
- `userID`

### Sentinel Columns
| Column | Table | Sentinel Value | Count | Pct | Interpretation |
|--------|-------|---------------|-------|-----|---------------|
| MMR | replay_players_raw | 0 | 37,489 | 83.65% | Unrated player |
| SQ | replay_players_raw | INT32_MIN (-2147483648) | 2 | 0.0045% | Missing SQ value |

---

## Cross-Table Linkage

| Metric | Value |
|--------|-------|
| rp_distinct_replays | 22,390 |
| rm_distinct_replays | 22,390 |
| rp_orphans | 0 |
| rm_orphans | 0 |

---

## Class Balance

| result | count | pct |
|--------|-------|-----|
| Loss | 22,409 | 50.0011% |
| Win | 22,382 | 49.9409% |
| Undecided | 24 | 0.0536% |
| Tie | 2 | 0.0045% |

---

## Plot Index

| File | Description |
|------|-------------|
| `01_03_01_completeness_heatmap.png` | Effective missingness per column per table. MMR=83.65% sentinel missingness dominates. |
| `01_03_01_qq_plots.png` | Normal QQ plots for MMR (rated), APM, SQ (no sentinel), supplyCappedPercent, elapsed_game_loops (POST-GAME). |
| `01_03_01_ecdf_key_columns.png` | ECDF for MMR (rated), APM, SQ (no sentinel). |

---

## SQL Queries (Invariant #6 — verbatim)

### rp_numeric_profile
```sql
WITH base AS (
    SELECT *
    FROM replay_players_raw
)
SELECT
    'MMR' AS column_name,
    COUNT(*) AS n_rows,
    COUNT(*) - COUNT(MMR) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(MMR)) / COUNT(*), 4) AS null_pct,
    SUM(CASE WHEN MMR = 0 THEN 1 ELSE 0 END) AS zero_count,
    ROUND(100.0 * SUM(CASE WHEN MMR = 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS zero_pct,
    COUNT(DISTINCT MMR) AS cardinality,
    ROUND(COUNT(DISTINCT MMR)::DOUBLE / COUNT(*), 6) AS uniqueness_ratio,
    MIN(MMR) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY MMR) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY MMR) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY MMR) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY MMR) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY MMR) AS p95,
    MAX(MMR) AS max_val,
    ROUND(AVG(MMR), 4) AS mean_val,
    ROUND(STDDEV(MMR), 4) AS std_val,
    ROUND(SKEWNESS(MMR), 4) AS skewness,
    ROUND(KURTOSIS(MMR), 4) AS kurtosis
FROM base

UNION ALL

SELECT
    'MMR_rated_only' AS column_name,
    SUM(CASE WHEN MMR > 0 THEN 1 ELSE 0 END) AS n_rows,
    0 AS null_count,
    0.0 AS null_pct,
    0 AS zero_count,
    0.0 AS zero_pct,
    COUNT(DISTINCT CASE WHEN MMR > 0 THEN MMR END) AS cardinality,
    ROUND(COUNT(DISTINCT CASE WHEN MMR > 0 THEN MMR END)::DOUBLE
          / NULLIF(SUM(CASE WHEN MMR > 0 THEN 1 ELSE 0 END), 0), 6) AS uniqueness_ratio,
    MIN(CASE WHEN MMR > 0 THEN MMR END) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY MMR) FILTER (WHERE MMR > 0) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY MMR) FILTER (WHERE MMR > 0) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY MMR) FILTER (WHERE MMR > 0) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY MMR) FILTER (WHERE MMR > 0) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY MMR) FILTER (WHERE MMR > 0) AS p95,
    MAX(CASE WHEN MMR > 0 THEN MMR END) AS max_val,
    ROUND(AVG(CASE WHEN MMR > 0 THEN MMR END), 4) AS mean_val,
    ROUND(STDDEV(CASE WHEN MMR > 0 THEN MMR END), 4) AS std_val,
    ROUND(SKEWNESS(MMR) FILTER (WHERE MMR > 0), 4) AS skewness,
    ROUND(KURTOSIS(MMR) FILTER (WHERE MMR > 0), 4) AS kurtosis
FROM base

UNION ALL

SELECT
    'APM' AS column_name,
    COUNT(*) AS n_rows,
    COUNT(*) - COUNT(APM) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(APM)) / COUNT(*), 4) AS null_pct,
    SUM(CASE WHEN APM = 0 THEN 1 ELSE 0 END) AS zero_count,
    ROUND(100.0 * SUM(CASE WHEN APM = 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS zero_pct,
    COUNT(DISTINCT APM) AS cardinality,
    ROUND(COUNT(DISTINCT APM)::DOUBLE / COUNT(*), 6) AS uniqueness_ratio,
    MIN(APM) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY APM) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY APM) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY APM) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY APM) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY APM) AS p95,
    MAX(APM) AS max_val,
    ROUND(AVG(APM), 4) AS mean_val,
    ROUND(STDDEV(APM), 4) AS std_val,
    ROUND(SKEWNESS(APM), 4) AS skewness,
    ROUND(KURTOSIS(APM), 4) AS kurtosis
FROM base

UNION ALL

SELECT
    'SQ' AS column_name,
    COUNT(*) AS n_rows,
    COUNT(*) - COUNT(SQ) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(SQ)) / COUNT(*), 4) AS null_pct,
    SUM(CASE WHEN SQ = 0 THEN 1 ELSE 0 END) AS zero_count,
    ROUND(100.0 * SUM(CASE WHEN SQ = 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS zero_pct,
    COUNT(DISTINCT SQ) AS cardinality,
    ROUND(COUNT(DISTINCT SQ)::DOUBLE / COUNT(*), 6) AS uniqueness_ratio,
    MIN(SQ) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY SQ) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY SQ) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY SQ) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY SQ) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY SQ) AS p95,
    MAX(SQ) AS max_val,
    ROUND(AVG(SQ), 4) AS mean_val,
    ROUND(STDDEV(SQ), 4) AS std_val,
    ROUND(SKEWNESS(SQ), 4) AS skewness,
    ROUND(KURTOSIS(SQ), 4) AS kurtosis
FROM base

UNION ALL

SELECT
    'SQ_no_sentinel' AS column_name,
    SUM(CASE WHEN SQ > -2147483648 THEN 1 ELSE 0 END) AS n_rows,
    0 AS null_count,
    0.0 AS null_pct,
    SUM(CASE WHEN SQ = 0 AND SQ > -2147483648 THEN 1 ELSE 0 END) AS zero_count,
    0.0 AS zero_pct,
    COUNT(DISTINCT CASE WHEN SQ > -2147483648 THEN SQ END) AS cardinality,
    ROUND(COUNT(DISTINCT CASE WHEN SQ > -2147483648 THEN SQ END)::DOUBLE
          / NULLIF(SUM(CASE WHEN SQ > -2147483648 THEN 1 ELSE 0 END), 0), 6) AS uniqueness_ratio,
    MIN(CASE WHEN SQ > -2147483648 THEN SQ END) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > -2147483648) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > -2147483648) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > -2147483648) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > -2147483648) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > -2147483648) AS p95,
    MAX(CASE WHEN SQ > -2147483648 THEN SQ END) AS max_val,
    ROUND(AVG(CASE WHEN SQ > -2147483648 THEN SQ END), 4) AS mean_val,
    ROUND(STDDEV(CASE WHEN SQ > -2147483648 THEN SQ END), 4) AS std_val,
    ROUND(SKEWNESS(SQ) FILTER (WHERE SQ > -2147483648), 4) AS skewness,
    ROUND(KURTOSIS(SQ) FILTER (WHERE SQ > -2147483648), 4) AS kurtosis
FROM base

UNION ALL

SELECT
    'supplyCappedPercent' AS column_name,
    COUNT(*) AS n_rows,
    COUNT(*) - COUNT(supplyCappedPercent) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(supplyCappedPercent)) / COUNT(*), 4) AS null_pct,
    SUM(CASE WHEN supplyCappedPercent = 0 THEN 1 ELSE 0 END) AS zero_count,
    ROUND(100.0 * SUM(CASE WHEN supplyCappedPercent = 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS zero_pct,
    COUNT(DISTINCT supplyCappedPercent) AS cardinality,
    ROUND(COUNT(DISTINCT supplyCappedPercent)::DOUBLE / COUNT(*), 6) AS uniqueness_ratio,
    MIN(supplyCappedPercent) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY supplyCappedPercent) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY supplyCappedPercent) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY supplyCappedPercent) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY supplyCappedPercent) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY supplyCappedPercent) AS p95,
    MAX(supplyCappedPercent) AS max_val,
    ROUND(AVG(supplyCappedPercent), 4) AS mean_val,
    ROUND(STDDEV(supplyCappedPercent), 4) AS std_val,
    ROUND(SKEWNESS(supplyCappedPercent), 4) AS skewness,
    ROUND(KURTOSIS(supplyCappedPercent), 4) AS kurtosis
FROM base

UNION ALL

SELECT
    'handicap' AS column_name,
    COUNT(*) AS n_rows,
    COUNT(*) - COUNT(handicap) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(handicap)) / COUNT(*), 4) AS null_pct,
    SUM(CASE WHEN handicap = 0 THEN 1 ELSE 0 END) AS zero_count,
    ROUND(100.0 * SUM(CASE WHEN handicap = 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS zero_pct,
    COUNT(DISTINCT handicap) AS cardinality,
    ROUND(COUNT(DISTINCT handicap)::DOUBLE / COUNT(*), 6) AS uniqueness_ratio,
    MIN(handicap) AS min_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY handicap) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY handicap) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY handicap) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY handicap) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY handicap) AS p95,
    MAX(handicap) AS max_val,
    ROUND(AVG(handicap), 4) AS mean_val,
    ROUND(STDDEV(handicap), 4) AS std_val,
    ROUND(SKEWNESS(handicap), 4) AS skewness,
    ROUND(KURTOSIS(handicap), 4) AS kurtosis
FROM base
```

### rp_null_cardinality
```sql
SELECT
    column_name,
    COUNT(*) - COUNT(col_val) AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT(col_val)) / COUNT(*), 4) AS null_pct,
    COUNT(DISTINCT col_val) AS cardinality,
    ROUND(COUNT(DISTINCT col_val)::DOUBLE / COUNT(*), 6) AS uniqueness_ratio
FROM (
    UNPIVOT replay_players_raw
    ON COLUMNS(*)
    INTO NAME column_name VALUE col_val
)
GROUP BY column_name
ORDER BY column_name
```

### rp_null_cardinality_fallback
```sql
SELECT 'filename' AS col, COUNT(*) AS total, COUNT(filename) AS non_null,
       COUNT(DISTINCT filename) AS cardinality FROM replay_players_raw
UNION ALL
SELECT 'toon_id', COUNT(*), COUNT(toon_id), COUNT(DISTINCT toon_id) FROM replay_players_raw
UNION ALL
SELECT 'nickname', COUNT(*), COUNT(nickname), COUNT(DISTINCT nickname) FROM replay_players_raw
UNION ALL
SELECT 'playerID', COUNT(*), COUNT(playerID), COUNT(DISTINCT playerID) FROM replay_players_raw
UNION ALL
SELECT 'userID', COUNT(*), COUNT(userID), COUNT(DISTINCT userID) FROM replay_players_raw
UNION ALL
SELECT 'isInClan', COUNT(*), COUNT(isInClan), COUNT(DISTINCT isInClan) FROM replay_players_raw
UNION ALL
SELECT 'clanTag', COUNT(*), COUNT(clanTag), COUNT(DISTINCT clanTag) FROM replay_players_raw
UNION ALL
SELECT 'MMR', COUNT(*), COUNT(MMR), COUNT(DISTINCT MMR) FROM replay_players_raw
UNION ALL
SELECT 'race', COUNT(*), COUNT(race), COUNT(DISTINCT race) FROM replay_players_raw
UNION ALL
SELECT 'selectedRace', COUNT(*), COUNT(selectedRace),
       COUNT(DISTINCT selectedRace) FROM replay_players_raw
UNION ALL
SELECT 'handicap', COUNT(*), COUNT(handicap), COUNT(DISTINCT handicap) FROM replay_players_raw
UNION ALL
SELECT 'region', COUNT(*), COUNT(region), COUNT(DISTINCT region) FROM replay_players_raw
UNION ALL
SELECT 'realm', COUNT(*), COUNT(realm), COUNT(DISTINCT realm) FROM replay_players_raw
UNION ALL
SELECT 'highestLeague', COUNT(*), COUNT(highestLeague),
       COUNT(DISTINCT highestLeague) FROM replay_players_raw
UNION ALL
SELECT 'result', COUNT(*), COUNT(result), COUNT(DISTINCT result) FROM replay_players_raw
UNION ALL
SELECT 'APM', COUNT(*), COUNT(APM), COUNT(DISTINCT APM) FROM replay_players_raw
UNION ALL
SELECT 'SQ', COUNT(*), COUNT(SQ), COUNT(DISTINCT SQ) FROM replay_players_raw
UNION ALL
SELECT 'supplyCappedPercent', COUNT(*), COUNT(supplyCappedPercent),
       COUNT(DISTINCT supplyCappedPercent) FROM replay_players_raw
UNION ALL
SELECT 'startDir', COUNT(*), COUNT(startDir), COUNT(DISTINCT startDir) FROM replay_players_raw
UNION ALL
SELECT 'startLocX', COUNT(*), COUNT(startLocX), COUNT(DISTINCT startLocX) FROM replay_players_raw
UNION ALL
SELECT 'startLocY', COUNT(*), COUNT(startLocY), COUNT(DISTINCT startLocY) FROM replay_players_raw
UNION ALL
SELECT 'color_a', COUNT(*), COUNT(color_a), COUNT(DISTINCT color_a) FROM replay_players_raw
UNION ALL
SELECT 'color_b', COUNT(*), COUNT(color_b), COUNT(DISTINCT color_b) FROM replay_players_raw
UNION ALL
SELECT 'color_g', COUNT(*), COUNT(color_g), COUNT(DISTINCT color_g) FROM replay_players_raw
UNION ALL
SELECT 'color_r', COUNT(*), COUNT(color_r), COUNT(DISTINCT color_r) FROM replay_players_raw
```

### rp_topk (per-column queries)

#### rp_topk['result']
```sql
SELECT
        CAST(result AS VARCHAR) AS value,
        COUNT(*) AS cnt,
        ROUND(100.0 * COUNT(*) / 44817, 4) AS pct
    FROM replay_players_raw
    GROUP BY result
    ORDER BY cnt DESC
    LIMIT 5
```

#### rp_topk['race']
```sql
SELECT
        CAST(race AS VARCHAR) AS value,
        COUNT(*) AS cnt,
        ROUND(100.0 * COUNT(*) / 44817, 4) AS pct
    FROM replay_players_raw
    GROUP BY race
    ORDER BY cnt DESC
    LIMIT 5
```

#### rp_topk['selectedRace']
```sql
SELECT
        CAST(selectedRace AS VARCHAR) AS value,
        COUNT(*) AS cnt,
        ROUND(100.0 * COUNT(*) / 44817, 4) AS pct
    FROM replay_players_raw
    GROUP BY selectedRace
    ORDER BY cnt DESC
    LIMIT 5
```

#### rp_topk['highestLeague']
```sql
SELECT
        CAST(highestLeague AS VARCHAR) AS value,
        COUNT(*) AS cnt,
        ROUND(100.0 * COUNT(*) / 44817, 4) AS pct
    FROM replay_players_raw
    GROUP BY highestLeague
    ORDER BY cnt DESC
    LIMIT 5
```

#### rp_topk['region']
```sql
SELECT
        CAST(region AS VARCHAR) AS value,
        COUNT(*) AS cnt,
        ROUND(100.0 * COUNT(*) / 44817, 4) AS pct
    FROM replay_players_raw
    GROUP BY region
    ORDER BY cnt DESC
    LIMIT 5
```

#### rp_topk['realm']
```sql
SELECT
        CAST(realm AS VARCHAR) AS value,
        COUNT(*) AS cnt,
        ROUND(100.0 * COUNT(*) / 44817, 4) AS pct
    FROM replay_players_raw
    GROUP BY realm
    ORDER BY cnt DESC
    LIMIT 5
```

#### rp_topk['isInClan']
```sql
SELECT
        CAST(isInClan AS VARCHAR) AS value,
        COUNT(*) AS cnt,
        ROUND(100.0 * COUNT(*) / 44817, 4) AS pct
    FROM replay_players_raw
    GROUP BY isInClan
    ORDER BY cnt DESC
    LIMIT 5
```

#### rp_topk['clanTag']
```sql
SELECT
        CAST(clanTag AS VARCHAR) AS value,
        COUNT(*) AS cnt,
        ROUND(100.0 * COUNT(*) / 44817, 4) AS pct
    FROM replay_players_raw
    GROUP BY clanTag
    ORDER BY cnt DESC
    LIMIT 5
```

### rp_iqr_outliers
```sql
WITH stats AS (
    SELECT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY MMR) AS mmr_q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY MMR) AS mmr_q3,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY APM) AS apm_q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY APM) AS apm_q3,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > -2147483648) AS sq_q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY SQ) FILTER (WHERE SQ > -2147483648) AS sq_q3,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY supplyCappedPercent) AS sc_q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY supplyCappedPercent) AS sc_q3
    FROM replay_players_raw
)
SELECT
    SUM(CASE WHEN MMR < (s.mmr_q1 - 1.5 * (s.mmr_q3 - s.mmr_q1))
              OR MMR > (s.mmr_q3 + 1.5 * (s.mmr_q3 - s.mmr_q1))
         THEN 1 ELSE 0 END) AS mmr_iqr_outliers,
    SUM(CASE WHEN APM < (s.apm_q1 - 1.5 * (s.apm_q3 - s.apm_q1))
              OR APM > (s.apm_q3 + 1.5 * (s.apm_q3 - s.apm_q1))
         THEN 1 ELSE 0 END) AS apm_iqr_outliers,
    SUM(CASE WHEN SQ > -2147483648
              AND (SQ < (s.sq_q1 - 1.5 * (s.sq_q3 - s.sq_q1))
                   OR SQ > (s.sq_q3 + 1.5 * (s.sq_q3 - s.sq_q1)))
         THEN 1 ELSE 0 END) AS sq_iqr_outliers,
    SUM(CASE WHEN supplyCappedPercent < (s.sc_q1 - 1.5 * (s.sc_q3 - s.sc_q1))
              OR supplyCappedPercent > (s.sc_q3 + 1.5 * (s.sc_q3 - s.sc_q1))
         THEN 1 ELSE 0 END) AS sc_iqr_outliers
FROM replay_players_raw, stats s
```

### rp_iqr_outliers_mmr_rated
```sql
WITH rated AS (SELECT MMR FROM replay_players_raw WHERE MMR > 0),
     fences AS (
       SELECT
         PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY MMR) AS p25,
         PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY MMR) AS p75
       FROM rated
     ),
     fences_scalar AS (
       SELECT p25, p75, p75 - p25 AS iqr,
              p25 - 1.5 * (p75 - p25) AS lower_fence,
              p75 + 1.5 * (p75 - p25) AS upper_fence
       FROM fences
     )
SELECT
  f.p25, f.p75, f.iqr,
  COUNT(*) FILTER (WHERE r.MMR < f.lower_fence OR r.MMR > f.upper_fence)
      AS mmr_iqr_outliers_rated
FROM rated r CROSS JOIN fences_scalar f
GROUP BY f.p25, f.p75, f.iqr
```

### rm_struct_profile
```sql
SELECT
    COUNT(*) AS n_rows,
    -- elapsed_game_loops (POST-GAME, reclassified 2026-04-15)
    COUNT(*) - COUNT(header.elapsedGameLoops) AS elapsed_game_loops_null,
    COUNT(DISTINCT header.elapsedGameLoops) AS elapsed_game_loops_cardinality,
    MIN(header.elapsedGameLoops) AS elapsed_game_loops_min,
    MAX(header.elapsedGameLoops) AS elapsed_game_loops_max,
    ROUND(AVG(header.elapsedGameLoops), 4) AS elapsed_game_loops_mean,
    ROUND(STDDEV(header.elapsedGameLoops), 4) AS elapsed_game_loops_std,
    ROUND(SKEWNESS(header.elapsedGameLoops), 4) AS elapsed_game_loops_skew,
    ROUND(KURTOSIS(header.elapsedGameLoops), 4) AS elapsed_game_loops_kurt,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY header.elapsedGameLoops)
        AS elapsed_game_loops_p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY header.elapsedGameLoops)
        AS elapsed_game_loops_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY header.elapsedGameLoops)
        AS elapsed_game_loops_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY header.elapsedGameLoops)
        AS elapsed_game_loops_p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY header.elapsedGameLoops)
        AS elapsed_game_loops_p95,
    -- map_name
    COUNT(*) - COUNT(metadata.mapName) AS map_name_null,
    COUNT(DISTINCT metadata.mapName) AS map_name_cardinality,
    -- max_players
    COUNT(*) - COUNT(initData.gameDescription.maxPlayers) AS max_players_null,
    COUNT(DISTINCT initData.gameDescription.maxPlayers) AS max_players_cardinality,
    -- game_speed (CONSTANT expected)
    COUNT(DISTINCT details.gameSpeed) AS game_speed_cardinality,
    -- game_speed_init (CONSTANT expected)
    COUNT(DISTINCT initData.gameDescription.gameSpeed) AS game_speed_init_cardinality,
    -- map_size
    COUNT(DISTINCT initData.gameDescription.mapSizeX) AS map_size_x_cardinality,
    COUNT(DISTINCT initData.gameDescription.mapSizeY) AS map_size_y_cardinality,
    -- error booleans (CONSTANT expected: all FALSE)
    COUNT(DISTINCT gameEventsErr) AS gameEventsErr_cardinality,
    COUNT(DISTINCT messageEventsErr) AS messageEventsErr_cardinality,
    COUNT(DISTINCT trackerEvtsErr) AS trackerEvtsErr_cardinality,
    -- version / build
    COUNT(DISTINCT metadata.gameVersion) AS game_version_meta_cardinality,
    COUNT(DISTINCT header."version") AS game_version_header_cardinality,
    COUNT(DISTINCT metadata.baseBuild) AS base_build_cardinality,
    COUNT(DISTINCT metadata.dataBuild) AS data_build_cardinality,
    -- blizzard map flags
    COUNT(DISTINCT details.isBlizzardMap) AS is_blizzard_map_cardinality,
    COUNT(DISTINCT initData.gameDescription.isBlizzardMap) AS is_blizzard_map_init_cardinality,
    -- time_utc
    COUNT(*) - COUNT(details.timeUTC) AS time_utc_null,
    COUNT(DISTINCT details.timeUTC) AS time_utc_cardinality
FROM replays_meta_raw
```

### rm_egl_iqr_outliers
```sql
WITH stats AS (
    SELECT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY header.elapsedGameLoops) AS q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY header.elapsedGameLoops) AS q3
    FROM replays_meta_raw
)
SELECT
    q1,
    q3,
    q3 - q1 AS iqr,
    q1 - 1.5 * (q3 - q1) AS lower_fence,
    q3 + 1.5 * (q3 - q1) AS upper_fence,
    SUM(CASE WHEN header.elapsedGameLoops < (s.q1 - 1.5 * (s.q3 - s.q1))
              OR header.elapsedGameLoops > (s.q3 + 1.5 * (s.q3 - s.q1))
         THEN 1 ELSE 0 END) AS iqr_outlier_count
FROM replays_meta_raw, stats s
GROUP BY q1, q3
```

### ma_profile
```sql
SELECT
    COUNT(*) AS n_rows,
    COUNT(*) - COUNT(tournament) AS tournament_null,
    COUNT(*) - COUNT(foreign_name) AS foreign_name_null,
    COUNT(*) - COUNT(english_name) AS english_name_null,
    COUNT(*) - COUNT(filename) AS filename_null,
    COUNT(DISTINCT tournament) AS tournament_cardinality,
    COUNT(DISTINCT foreign_name) AS foreign_name_cardinality,
    COUNT(DISTINCT english_name) AS english_name_cardinality,
    COUNT(DISTINCT filename) AS filename_cardinality
FROM map_aliases_raw
```

### ma_topk_tournament
```sql
SELECT
    tournament,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM map_aliases_raw), 4) AS pct
FROM map_aliases_raw
GROUP BY tournament
ORDER BY cnt DESC
LIMIT 5
```

### row_counts
```sql
SELECT 'replay_players_raw' AS table_name, COUNT(*) AS n_rows FROM replay_players_raw
UNION ALL
SELECT 'replays_meta_raw', COUNT(*) FROM replays_meta_raw
UNION ALL
SELECT 'map_aliases_raw', COUNT(*) FROM map_aliases_raw
```

### rp_duplicates
```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT (filename, playerID)) AS distinct_pairs,
    COUNT(*) - COUNT(DISTINCT (filename, playerID)) AS duplicate_rows
FROM replay_players_raw
-- W-04: (filename, playerID) = natural key.
-- filename contains the replay hash; playerID is per-replay slot index (0/1).
-- toon_id is global Battle.net ID; not the correct duplication detection key here.
```

### class_balance
```sql
SELECT
    result,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS pct
FROM replay_players_raw
GROUP BY result
ORDER BY cnt DESC
```

### cross_table_linkage
```sql
WITH rp_replays AS (
    SELECT DISTINCT
        regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id
    FROM replay_players_raw
),
rm_replays AS (
    SELECT DISTINCT
        regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id
    FROM replays_meta_raw
)
SELECT
    (SELECT COUNT(*) FROM rp_replays) AS rp_distinct_replays,
    (SELECT COUNT(*) FROM rm_replays) AS rm_distinct_replays,
    (SELECT COUNT(*) FROM rp_replays
     WHERE replay_id NOT IN (SELECT replay_id FROM rm_replays)) AS rp_orphans,
    (SELECT COUNT(*) FROM rm_replays
     WHERE replay_id NOT IN (SELECT replay_id FROM rp_replays)) AS rm_orphans
```

### memory_footprint
```sql
SELECT
    database_name,
    table_name,
    estimated_size,
    column_count,
    index_count
FROM duckdb_tables()
WHERE table_name IN ('replay_players_raw', 'replays_meta_raw', 'map_aliases_raw')
ORDER BY table_name
```

### qq_mmr
```sql
SELECT MMR
FROM replay_players_raw
WHERE result IN ('Win', 'Loss') AND MMR > 0
-- I7: MMR > 0 excludes unrated sentinel (83.65% of rows). Rated-only QQ.
```

### qq_ingame
```sql
SELECT APM, SQ, supplyCappedPercent
FROM replay_players_raw
WHERE result IN ('Win', 'Loss')
  AND SQ > -2147483648
-- I7: SQ > INT32_MIN excludes 2 sentinel rows. APM/supplyCappedPercent unfiltered.
```

### qq_egl_data
```sql
SELECT header.elapsedGameLoops AS elapsed_game_loops
FROM replays_meta_raw
```

---

## Invariants Applied

- **#3 (Temporal discipline):** Every column classified. `elapsed_game_loops` annotated POST-GAME (reclassified 2026-04-15).
- **#6 (Reproducibility):** All SQL stored verbatim in `sql_queries` dict and in this artifact.
- **#7 (No magic numbers):** IQR fence = 1.5 * IQR per Tukey (1977). All sentinel thresholds from census JSON.
- **#9 (Step scope):** Profiling only. No cleaning, no feature engineering.

---

## Phase 02 Implications

- **Drop:** 5 constant columns (`game_speed`, `game_speed_init`, `gameEventsErr`, `messageEventsErr`, `trackerEvtsErr`).
- **Sentinel handling:** MMR=0 (83.65% unrated) and SQ=INT32_MIN (2 rows) require explicit handling.
- **Near-constant columns:** Review whether near-constant columns carry any predictive signal.
- **elapsed_game_loops:** POST-GAME feature — cannot be used in pre-game prediction context.
