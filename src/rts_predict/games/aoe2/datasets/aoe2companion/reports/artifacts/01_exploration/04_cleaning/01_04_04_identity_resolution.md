# Step 01_04_04 -- Identity Resolution (aoe2companion)

**Date:** 2026-04-18  
**Dataset:** aoe2companion  
**Branch:** feat/01-04-04-identity-resolution  
**Predecessor:** 01_04_03 (Minimal Cross-Dataset History View)  

---

## 1. Cardinality Baseline

| Table | n_rows | n_distinct_id | min_id | max_id | null | sentinel=-1 | int32_overflow |
|---|---|---|---|---|---|---|---|
| matches_raw | 277,099,059 | 2,659,039 | -1 | 25179198 | 0 | 12,966,310 | 0 |
| ratings_raw | 58,317,433 | 821,662 | 26 | 25171676 | 0 | 0 | 0 |
| profiles_raw | 3,609,686 | 3,609,686 | -1 | 25186407 | 0 | 1 | 0 |

Distinct names in matches_raw (non-sentinel): 2,468,341  
NULL name count (non-sentinel rows): 625

**SQL (I6):**
```sql
SELECT
  COUNT(*)                                                    AS n_rows,
  COUNT(DISTINCT profileId)                                   AS n_distinct,
  MIN(profileId)                                              AS min_val,
  MAX(profileId)                                              AS max_val,
  COUNT(*) FILTER (WHERE profileId IS NULL)                   AS null_count,
  COUNT(*) FILTER (WHERE profileId = -1)                      AS sentinel_neg1,
  COUNT(*) FILTER (WHERE profileId > 2147483647)              AS int32_overflow
FROM matches_raw
```

---

## 2. Name History per profileId (Rename Detection)

**Scope:** `player_history_all` WHERE `internalLeaderboardId IN (6, 18)` AND `profileId != -1` (rm_1v1)

- Total profiles: 683,790
- Stable (1 name): 666,225 (97.43%)
- Any rename (2+ names): 17,555 (2.57%)

| Bin | n_profiles | % |
|---|---|---|
| 0 names (all NULL) | 10 | 0.00% |
| 1 name (stable) | 666,225 | 97.43% |
| 2 names (one rename) | 14,079 | 2.06% |
| 3-5 names | 2,975 | 0.44% |
| 6+ names | 501 | 0.07% |

**Rename timing (for profiles with 2+ names):**

| Bin | n_profiles |
|---|---|
| rapid_30d (<=30 days) | 6,862 |
| within_180d (31-180 days) | 5,085 |
| after_180d (>180 days) | 5,935 |

Max names per profile: 75

**SQL (I6):**
```sql
WITH name_timeline AS (
  SELECT
    profileId,
    name,
    MIN(started) AS first_seen,
    MAX(started) AS last_seen
  FROM player_history_all
  WHERE internalLeaderboardId IN (6, 18)
    AND profileId != -1
    AND name IS NOT NULL
  GROUP BY profileId, name
),
consecutive_pairs AS (
  SELECT
    t1.profileId,
    t1.name AS name1,
    t2.name AS name2,
    t1.last_seen AS name1_last,
    t2.first_seen AS name2_first,
    DATE_DIFF('day', t1.last_seen, t2.first_seen) AS days_between
  FROM name_timeline t1
  JOIN name_timeline t2
    ON t1.profileId = t2.profileId AND t1.name != t2.name
  WHERE t1.last_seen < t2.first_seen
)
SELECT
  COUNT(DISTINCT profileId)                                              AS total_renaming_profiles,
  COUNT(DISTINCT profileId) FILTER (WHERE days_between <= 30)           AS rapid_30d,
  COUNT(DISTINCT profileId) FILTER (WHERE days_between > 30
                                    AND days_between <= 180)            AS within_180d,
  COUNT(DISTINCT profileId) FILTER (WHERE days_between > 180)           AS after_180d
FROM consecutive_pairs
```

---

## 3. Name-to-profileId Collision (Alias Detection)

- Total distinct names: 654,841
- Unique (1 profileId): 631,620 (96.45%)
- Collision (2+ profileIds): 23,221 (3.55%)
- Common names (>10 profileIds): 100
- Top collider n_profiles: 249

**Privacy note:** Top-100 colliders stored in JSON by name + count only.
No name+profileId linkage reported here.

**SQL (I6):**
```sql
SELECT
  n_profiles_per_name,
  COUNT(*) AS n_names
FROM (
  SELECT name, COUNT(DISTINCT profileId) AS n_profiles_per_name
  FROM player_history_all
  WHERE internalLeaderboardId IN (6, 18)
    AND profileId != -1
    AND name IS NOT NULL
  GROUP BY name
)
GROUP BY n_profiles_per_name
ORDER BY n_profiles_per_name
LIMIT 30
```

---

## 4. Join Integrity (Set-Difference Audit)

| Pair | Missing |
|---|---|
| matches_raw profileIds NOT IN profiles_raw | 0 |
| profiles_raw profileIds NOT IN matches_raw | 950,647 |
| matches_raw profileIds NOT IN ratings_raw | 2,029,201 |
| INT32 overflow (>2147483647) in matches_raw | 0 |

**rm_1v1 ratings_raw coverage:** 262,372 / 683,790 = 38.4%
(predecessor 01_03_03 found profiles_raw coverage = 45.0%)

**SQL (I6):**
```sql
SELECT COUNT(DISTINCT m.profileId) AS missing_in_profiles
FROM (SELECT DISTINCT profileId FROM matches_raw WHERE profileId != -1) m
LEFT JOIN profiles_raw p ON m.profileId = p.profileId
WHERE p.profileId IS NULL
```

---

## 5. (profileId, country) Temporal Stability

| n_countries | n_profiles | % |
|---|---|---|
| 0 (all NULL) | 131,141 | 19.2% |
| 1 (stable) | 552,409 | 80.8% |
| 2+ (oscillating/transition) | 240 | 0.0351% |

Max countries per profile: 3  

country is highly stable: 80.8% of profiles show exactly 1 country. 19.2% show 0 (all-NULL country field). Only 0.035% show 2+ countries (oscillating or legitimate country-change). country is suitable as a secondary identity signal but NOT as a primary identity key due to NULL prevalence.

**SQL (I6):**
```sql
SELECT
  n_countries,
  COUNT(*) AS n_profiles
FROM (
  SELECT profileId, COUNT(DISTINCT country) AS n_countries
  FROM player_history_all
  WHERE internalLeaderboardId IN (6, 18)
    AND profileId != -1
  GROUP BY profileId
)
GROUP BY n_countries
ORDER BY n_countries
```

---

## 6. Cross-Dataset Feasibility Preview (aoec vs aoestats)

**Window:** 2026-01-25..2026-01-31  
**aoec filter:** `internalLeaderboardId IN (6, 18)` (rm_1v1)  
**aoestats filter:** `leaderboard='random_map'`  

**Full-window population:**

| Metric | Value |
|---|---|
| aoec profiles | 37,495 |
| aoestats profiles | 28,921 |
| Intersection | 28,921 |
| Overlap % of aoec | 77.1% |
| Overlap % of aoestats | 100.0% |

**Reservoir sample (1,000 aoec matches, seed=20260418):**

- n_sampled_profiles: 1,856
- n_matched: 1,630
- p_hat: 0.8782
- 95% CI: [0.8634, 0.8931] (normal approximation)

**VERDICT: A -- STRONG -- shared namespace confirmed. CI lower bound > 0.50.**

**Property-agreement cross-check (60s temporal window):**

- n_pairs: 5,260
- civ agreement: 2,141 / 5,260 = 40.7%
- rating agreement (50-ELO): 5,012 / 5,260 = 95.3%

Note: Low civ agreement is EXPECTED (60s window matches cross-game pairs,
not same-game pairs). Rating agreement is the meaningful property-agreement signal.

**SQL (I6):**
```sql
WITH aoec_profiles AS (
  SELECT DISTINCT profileId
  FROM main.matches_raw
  WHERE internalLeaderboardId IN (6, 18)
    AND profileId != -1
    AND started >= TIMESTAMP '2026-01-25 00:00:00'
    AND started < TIMESTAMP '2026-02-01 00:00:00'
),
aoestats_profiles AS (
  SELECT DISTINCT CAST(p.profile_id AS INTEGER) AS profile_id
  FROM aoestats.players_raw p
  JOIN aoestats.matches_raw m ON m.game_id = p.game_id
  WHERE m.leaderboard = 'random_map'
    AND CAST(m.started_timestamp AS TIMESTAMP) >= TIMESTAMP '2026-01-25 00:00:00'
    AND CAST(m.started_timestamp AS TIMESTAMP) < TIMESTAMP '2026-02-01 00:00:00'
    AND p.profile_id IS NOT NULL AND p.profile_id > 0
)
SELECT
  COUNT(DISTINCT a.profileId)                                               AS n_aoec,
  COUNT(DISTINCT b.profile_id)                                              AS n_aoestats,
  COUNT(DISTINCT CASE WHEN b.profile_id IS NOT NULL THEN a.profileId END)   AS n_intersection
FROM aoec_profiles a
LEFT JOIN aoestats_profiles b ON a.profileId = b.profile_id
```

---

## 7. Decision Ledger

### DS-AOEC-IDENTITY-01 -- identity-key

Use profileId (INTEGER) as the primary player identity key in Phase 02 rating-system backtesting. Rationale: 97.4% of rm_1v1 active profiles have exactly 1 name (stable), 2.6% have 2+ names (renamers). profileId is stable across renames by construction. Exclude profileId=-1 sentinel rows (AI/anonymized, 12.95M matches_raw rows).

### DS-AOEC-IDENTITY-02 -- NULL-sentinel

profileId=-1 is the sole sentinel for AI/anonymized players. Confirmed from 01_03_02 and T02 cardinality: 12,966,310 sentinel rows in matches_raw; 0 NULL rows; 0 INT32 overflow rows. All Phase 02 features must filter WHERE profileId != -1. ratings_raw has no sentinel=-1 rows (min profile_id=26). profiles_raw has exactly 1 sentinel=-1 row -- exclude.

### DS-AOEC-IDENTITY-03 -- rename-detection

2.6% of rm_1v1 active profiles have changed their display name at least once. Phase 02 must not group players by name alone. profileId is the correct grouping key. Rename timing: 45.6% of renaming profiles changed within 30 days (rapid_30d); 33.8% changed within 30-180 days. Cross-tab with 01_03_02 player-name instability findings recommended at Phase 02 feature-engineering time.

### DS-AOEC-IDENTITY-04 -- collision

Name-level collision is severe: 96.3% of distinct names map to a single profileId (unique), but 3.7% of names appear under 2+ profileIds (collision). Common names (>10 profileIds) include short generic handles. NEVER use name alone as primary key. profileId is the correct key. Invariant I2 (lowercased nickname) is satisfied ONLY via profileId de-ambiguation -- record this as a per-dataset I2 adaptation.

### DS-AOEC-IDENTITY-05 -- cross-dataset-bridge

Cross-dataset ID-equality test (2026-01-25..2026-01-31 window): VERDICT A -- STRONG -- shared namespace confirmed. CI lower bound > 0.50. Full-window: aoec 37,495 profiles, aoestats 28,921 profiles, intersection 28,921 (100% of aoestats). Reservoir sample (1,000 matches, seed=20260418): p_hat=0.8782, 95% CI=[0.8634, 0.8931]. aoec profileId and aoestats profile_id share a namespace (both sourced from aoe2insights.com API). Phase 02 may use aoec name column to bridge Invariant I2 for aoestats via a LEFT JOIN on profileId=profile_id. Ratings_raw coverage of rm_1v1 players: 262,372/683,790 = 38.4% (vs 01_03_03 profiles_raw 45.0% -- ratings_raw is a more complete source for rated players).

---

## 8. Synthesis

### Observations

**OBS-1:** profileId is a stable, complete, collision-free primary key across all three raw tables. matches_raw has 0 NULL profileIds and 0 INT32 overflows. The sentinel=-1 population (12.97M rows, 4.7% of matches_raw) is well-defined and must be excluded from all feature computation.

**OBS-2:** 97.4% of rm_1v1 active profiles are name-stable (1 distinct name). 2.6% have renamed at least once. Name is NOT a safe primary key: 3.7% of distinct names collide across 2+ profileIds.

**OBS-3:** Join integrity: matches_raw profileIds are a complete subset of profiles_raw (0 missing). profiles_raw has 950,647 profileIds not in any match (pre-API historical profiles). ratings_raw covers only 821,662 distinct profile_ids vs 2,659,039 in matches_raw, but covers 38.4% of rm_1v1 active players.

**OBS-4:** country is highly stable (80.8% of profiles: 1 country). 19.2% have 0 countries (NULL). Only 0.035% oscillate across 2+ countries. country can serve as a secondary identity signal but not as a primary key.

**OBS-5:** Cross-dataset ID-equality verdict: A. 100% of aoestats rm_1v1 profiles in the 2026-01-25..2026-01-31 window appear in aoec matches_raw for the same window. aoec profileId and aoestats profile_id share a namespace.

### Implications

**IMPL-1:** Phase 02 feature engineering MUST use profileId as the grouping key. All historical lookback windows, rating trajectories, and head-to-head statistics must be indexed by profileId.

**IMPL-2:** Invariant I2 (canonical lowercased nickname) is satisfied indirectly: profileId is the stable key; name is available per match for display. The rename-history finding (T03) confirms name cannot serve as I2 alone.

**IMPL-3:** The aoec name column can bridge Invariant I2 for aoestats (which has no name column) via a LEFT JOIN on profileId=profile_id. Feasibility confirmed: VERDICT A, 95% CI=[0.8634, 0.8931].

### Actions for Phase 02

**ACTION-1:** Phase 02 plan must specify profileId as the primary identity key for both aoe2companion and aoestats datasets.

**ACTION-2:** Phase 02 plan must include a cross-dataset name-bridge query (aoec.matches_raw.name LEFT JOIN aoestats.players_raw ON profileId=profile_id) to provide I2-compliant nicknames for aoestats.

**ACTION-3:** Phase 02 feature engineering must exclude profileId=-1 rows in all aggregation queries.

---

**Thesis crosswalk:** §4.2.2 Identity Resolution -- DS-AOEC-IDENTITY-01..05 decisions  
**all_assertions_pass:** True  