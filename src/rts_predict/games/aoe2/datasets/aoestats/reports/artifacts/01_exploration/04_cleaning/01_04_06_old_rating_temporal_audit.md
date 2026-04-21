# Audit: old_rating PRE-GAME Temporal Consistency (Step 01_04_06)

**Dataset:** aoestats
**Date:** 2026-04-21
**Verdict:** FAIL

---

## §1 Scope and Method

**Hypothesis:** On `leaderboard = 'random_map'` (primary), for consecutive matches t, t+1
of the same `profile_id` ordered by `(started_timestamp, game_id)` within the same leaderboard,
`players_raw.old_rating[t+1] == players_raw.new_rating[t]` at `agreement_rate >= 0.95`
AND `max(|old_rating[t+1] - new_rating[t]|) < 50` rating units.
Per-leaderboard strata pass at >= 0.90. Per-time-gap-bucket strata pass at >= 0.90.

**3-gate falsifier:**
- Gate (a): primary scope `agreement_rate >= 0.95` AND `max_disagreement < 50`
- Gate (b): every leaderboard stratum `agreement_rate >= 0.90`
- Gate (c): every time-gap-bucket `agreement_rate >= 0.90`
- CATASTROPHIC_HALT: `agreement_rate < 0.80`

**Threshold rationale (I7):**
- 0.95 primary threshold: DS-AOESTATS-02 documents NULLIF cleaning-loss of ~0.03% for
  `old_rating=0` sentinel rows. Agreement rate below 0.95 (>5% disagreement) would exceed
  this tolerance by 2 orders of magnitude, making the PRE-GAME classification materially
  unsound.
- 50-unit magnitude threshold: Elo K-factor for aoestats is approximately 20-40 rating points
  per match. Disagreements > 50 units indicate systematic drift beyond normal Elo updates.
- 0.90 stratum threshold: relaxed for sub-strata to accommodate smaller n and
  leaderboard-specific factors (co-op modes, team ladders have different population sizes).

**CAST discipline (DS-AOESTATS-IDENTITY-04):** `profile_id` stored as DOUBLE; all values
below 2^53, so `CAST(profile_id AS BIGINT)` is lossless. Defined as `profile_id_i64` in all CTEs.

**LAG partition (BLOCKER 1 fix):** AoE2 ratings are per-leaderboard independent systems.
Window: `PARTITION BY (profile_id_i64, leaderboard) ORDER BY (started_timestamp, game_id)`.

---

## §2 SQL Verbatim (I6)

### Tie-rate pre-flight

```sql

WITH base AS (
  SELECT
    CAST(p.profile_id AS BIGINT) AS profile_id_i64,
    m.leaderboard,
    m.started_timestamp
  FROM players_raw p
  JOIN matches_raw m USING (game_id)
  WHERE p.profile_id IS NOT NULL
    AND p.old_rating IS NOT NULL
    AND p.new_rating IS NOT NULL
),
tie_check AS (
  SELECT profile_id_i64, leaderboard, started_timestamp, COUNT(*) AS cnt
  FROM base
  GROUP BY profile_id_i64, leaderboard, started_timestamp
)
SELECT
  COUNT(*)                                       AS total_groups,
  COUNT(*) FILTER (WHERE cnt > 1)                AS tied_groups,
  ROUND(
    COUNT(*) FILTER (WHERE cnt > 1) * 100.0 / COUNT(*),
    6
  )                                              AS tie_rate_pct
FROM tie_check

```

### Duplicate-row pre-flight

```sql

SELECT
  COUNT(*) FILTER (WHERE cnt > 1)      AS dup_groups,
  COALESCE(
    SUM(cnt) FILTER (WHERE cnt > 1) - COUNT(*) FILTER (WHERE cnt > 1),
    0
  )                                    AS extra_rows
FROM (
  SELECT game_id, CAST(profile_id AS BIGINT) AS profile_id_i64, COUNT(*) AS cnt
  FROM players_raw
  WHERE profile_id IS NOT NULL
  GROUP BY game_id, CAST(profile_id AS BIGINT)
)

```

### Pair construction and per-leaderboard agreement

```sql

WITH deduped AS (
  SELECT DISTINCT
    CAST(p.profile_id AS BIGINT) AS profile_id_i64,
    m.leaderboard,
    m.started_timestamp,
    m.game_id,
    p.old_rating,
    p.new_rating
  FROM players_raw p
  JOIN matches_raw m USING (game_id)
  WHERE p.profile_id IS NOT NULL
    AND p.old_rating IS NOT NULL
    AND p.new_rating IS NOT NULL
),
with_lag AS (
  SELECT
    profile_id_i64,
    leaderboard,
    started_timestamp,
    game_id,
    old_rating,
    new_rating,
    LAG(new_rating) OVER (
      PARTITION BY profile_id_i64, leaderboard
      ORDER BY started_timestamp, game_id
    ) AS prev_new_rating,
    LAG(started_timestamp) OVER (
      PARTITION BY profile_id_i64, leaderboard
      ORDER BY started_timestamp, game_id
    ) AS prev_started_timestamp
  FROM deduped
),
pairs AS (
  SELECT *
  FROM with_lag
  WHERE prev_new_rating IS NOT NULL
)
SELECT
  leaderboard,
  COUNT(*)                                              AS n_pairs,
  AVG(CASE WHEN old_rating = prev_new_rating THEN 1.0 ELSE 0.0 END)
                                                        AS agreement_rate,
  MAX(ABS(old_rating - prev_new_rating))                AS max_disagreement
FROM pairs
GROUP BY leaderboard
ORDER BY n_pairs DESC

```

### Primary scope agreement and disagreement magnitude

```sql

WITH deduped AS (
  SELECT DISTINCT
    CAST(p.profile_id AS BIGINT) AS profile_id_i64,
    m.leaderboard,
    m.started_timestamp,
    m.game_id,
    p.old_rating,
    p.new_rating
  FROM players_raw p
  JOIN matches_raw m USING (game_id)
  WHERE p.profile_id IS NOT NULL
    AND p.old_rating IS NOT NULL
    AND p.new_rating IS NOT NULL
),
with_lag AS (
  SELECT
    profile_id_i64,
    leaderboard,
    started_timestamp,
    game_id,
    old_rating,
    new_rating,
    LAG(new_rating) OVER (
      PARTITION BY profile_id_i64, leaderboard
      ORDER BY started_timestamp, game_id
    ) AS prev_new_rating,
    LAG(started_timestamp) OVER (
      PARTITION BY profile_id_i64, leaderboard
      ORDER BY started_timestamp, game_id
    ) AS prev_started_timestamp
  FROM deduped
),
pairs AS (
  SELECT *,
    CASE WHEN old_rating = prev_new_rating THEN 1 ELSE 0 END AS agreed,
    ABS(old_rating - prev_new_rating)                         AS disagreement_abs
  FROM with_lag
  WHERE prev_new_rating IS NOT NULL
    AND leaderboard = 'random_map'
)
SELECT
  COUNT(*)                                                          AS n_pairs,
  SUM(agreed)                                                       AS n_agreed,
  AVG(agreed::DOUBLE)                                               AS agreement_rate,
  MAX(disagreement_abs)                                             AS max_disagreement,
  MEDIAN(CASE WHEN agreed = 0 THEN disagreement_abs ELSE NULL END)  AS median_dis_disagreeing
FROM pairs

```

### Per-time-gap-bucket stratification

```sql

WITH deduped AS (
  SELECT DISTINCT
    CAST(p.profile_id AS BIGINT) AS profile_id_i64,
    m.leaderboard,
    m.started_timestamp,
    m.game_id,
    p.old_rating,
    p.new_rating
  FROM players_raw p
  JOIN matches_raw m USING (game_id)
  WHERE p.profile_id IS NOT NULL
    AND p.old_rating IS NOT NULL
    AND p.new_rating IS NOT NULL
    AND m.leaderboard = 'random_map'
),
with_lag AS (
  SELECT
    profile_id_i64,
    leaderboard,
    started_timestamp,
    game_id,
    old_rating,
    new_rating,
    LAG(new_rating) OVER (
      PARTITION BY profile_id_i64, leaderboard
      ORDER BY started_timestamp, game_id
    ) AS prev_new_rating,
    LAG(started_timestamp) OVER (
      PARTITION BY profile_id_i64, leaderboard
      ORDER BY started_timestamp, game_id
    ) AS prev_started_timestamp
  FROM deduped
),
pairs AS (
  SELECT *,
    CASE WHEN old_rating = prev_new_rating THEN 1 ELSE 0 END AS agreed,
    EPOCH(started_timestamp - prev_started_timestamp) / 86400.0 AS gap_days
  FROM with_lag
  WHERE prev_new_rating IS NOT NULL
),
bucketed AS (
  SELECT
    CASE
      WHEN gap_days < 1   THEN '<1d'
      WHEN gap_days < 7   THEN '1-7d'
      WHEN gap_days < 30  THEN '7-30d'
      ELSE                     '>30d'
    END AS time_gap_bucket,
    agreed
  FROM pairs
)
SELECT
  time_gap_bucket,
  COUNT(*)           AS n_pairs,
  AVG(agreed::DOUBLE) AS agreement_rate
FROM bucketed
GROUP BY time_gap_bucket
ORDER BY MIN(
  CASE time_gap_bucket
    WHEN '<1d'   THEN 0
    WHEN '1-7d'  THEN 1
    WHEN '7-30d' THEN 2
    ELSE              3
  END
)

```

---

## §3 Results

**Pre-flight:**
- Tie rate: 0.000000% (0 tied groups / 107,626,399 total) — well below 1% threshold
- Duplicate (game_id, profile_id_i64) extra rows: 0 — DISTINCT applied

**Primary scope (random_map):**
| Metric | Value |
|--------|-------|
| n_pairs | 35,275,197 |
| agreement_rate | 0.920968 |
| max_disagreement | 1118 rating units |
| median_disagreement (disagreeing only) | 16.0 |
| Wilson CI 95% low | 0.920879 |
| Wilson CI 95% high | 0.921057 |
| Total pairs (all leaderboards) | 106,700,317 |

**Per-leaderboard agreement:**
| Leaderboard | n_pairs | agreement_rate | Gate (b) |
|-------------|---------|----------------|----------|
| team_random_map | 67,428,909 | 0.8601 | FAIL |
| random_map | 35,275,197 | 0.9210 | PASS |
| co_team_random_map | 2,783,734 | 0.7867 | FAIL |
| co_random_map | 1,212,477 | 0.8552 | FAIL |

**Per-time-gap-bucket (random_map):**
| Bucket | n_pairs | agreement_rate | Gate (c) |
|--------|---------|----------------|----------|
| <1d | 29,021,397 | 0.9440 | PASS |
| 1-7d | 4,661,976 | 0.8590 | FAIL |
| 7-30d | 1,057,793 | 0.7076 | FAIL |
| >30d | 534,031 | 0.6345 | FAIL |

---

## §4 Verdict

| Gate | Criterion | Value | Status |
|------|-----------|-------|--------|
| (a) rate | primary agreement_rate >= 0.95 | 0.9210 | FAIL |
| (a) magnitude | max_disagreement < 50 units | 1118 | FAIL |
| (b) strata | all leaderboards >= 0.90 | failures: ['team_random_map', 'co_team_random_map', 'co_random_map'] | FAIL |
| (c) time-gap | all time-gap buckets >= 0.90 | failures: ['1-7d', '7-30d', '>30d'] | FAIL |

**Overall verdict: FAIL**

---

## §5 Interpretation

Gates failed: gate(a)-rate=False, gate(a)-magnitude=False, gate(b)=False, gate(c)=False. The PRE-GAME classification is structurally supported (VIEW exclusion of `new_rating`) but empirically uncertain. Disagreement concentrates in longer-gap pairs (1-7d: 0.859, 7-30d: 0.708, >30d: 0.634), consistent with rating resets or seasonal updates. Short-gap (<1d) agreement 0.9440 confirms the convention holds for dense play. Three follow-up candidates: (1) retain with caveat if primary is deemed acceptable for thesis purposes; (2) demote to CONDITIONAL_PRE_GAME pending investigation of reset mechanisms; (3) filter disagreeing pairs in Phase 02 feature engineering.
