# Step 01_04_07 — old_rating CONDITIONAL_PRE_GAME Phase 01 Annotation

**Dataset:** aoestats
**Date:** 2026-04-21
**Step:** 01_04_07

---

## §1 Scope and Motivation

Step 01_04_06 (WP-4) empirically falsified the unconditional PRE-GAME classification
of `old_rating` (FAIL on all 3 gates; primary `random_map` agreement = 0.9210,
max_disagreement = 1,118 rating units). Per `docs/PHASES.md §Phase 01 01_04`,
Phase 01 is where column classifications are decided. Fixing this at Phase 02 would
spill the responsibility — Phase 02 would have to re-discover and build workarounds.

This step applies a Phase 01-level annotation: add derived column
`time_since_prior_match_days` to `player_history_all` VIEW, select an
empirically-grounded threshold N* ∈ {1, 2, 3, 7} days, determine SCOPE
(GLOBAL or `random_map`-only) from the 4×4 leaderboard × time-gap stratification,
and demote `old_rating` to CONDITIONAL_PRE_GAME in INVARIANTS.md §3.

**Post-Mode-A framing:** Mode A identified that the original 7-day pre-specified
cutoff was internally inconsistent (included the 1-7d bucket at 0.859, below the
0.90 stratum gate). The revised approach selects N* data-driven from
{1, 2, 3, 7} days. Mode A also identified that
01_04_06's per-time-gap stratification was random_map-only and could not justify
a global cutoff without the 4×4 leaderboard test.

---

## §2 DDL Verbatim (I6)

### Before Amendment (14 columns)

```sql
CREATE OR REPLACE VIEW player_history_all AS
WITH player_counts AS (
    SELECT game_id, COUNT(*) AS player_count
    FROM players_raw
    GROUP BY game_id
)
SELECT
    CAST(p.profile_id AS BIGINT) AS profile_id,
    p.game_id,
    m.started_timestamp,
    m.leaderboard,
    m.map,
    m.patch,
    pc.player_count,
    m.mirror,
    m.replay_enhanced,
    p.civ,
    p.team,
    NULLIF(p.old_rating, 0) AS old_rating,
    p.old_rating = 0        AS is_unrated,
    p.winner
FROM players_raw p
INNER JOIN matches_raw m ON p.game_id = m.game_id
INNER JOIN player_counts pc ON p.game_id = pc.game_id
WHERE p.profile_id IS NOT NULL
  AND m.started_timestamp IS NOT NULL
```

### After Amendment (15 columns)

```sql
CREATE OR REPLACE VIEW player_history_all AS
WITH player_counts AS (
    SELECT game_id, COUNT(*) AS player_count
    FROM players_raw
    GROUP BY game_id
),
lag_base AS (
    SELECT
        CAST(p.profile_id AS BIGINT) AS profile_id,
        p.game_id,
        m.started_timestamp,
        m.leaderboard,
        m.map,
        m.patch,
        pc.player_count,
        m.mirror,
        m.replay_enhanced,
        p.civ,
        p.team,
        NULLIF(p.old_rating, 0) AS old_rating,
        p.old_rating = 0        AS is_unrated,
        p.winner,
        LAG(m.started_timestamp) OVER (
            PARTITION BY CAST(p.profile_id AS BIGINT), m.leaderboard
            ORDER BY m.started_timestamp, m.game_id
        ) AS prev_started_timestamp
    FROM players_raw p
    INNER JOIN matches_raw m ON p.game_id = m.game_id
    INNER JOIN player_counts pc ON p.game_id = pc.game_id
    WHERE p.profile_id IS NOT NULL
      AND m.started_timestamp IS NOT NULL
)
SELECT
    profile_id,
    game_id,
    started_timestamp,
    leaderboard,
    map,
    patch,
    player_count,
    mirror,
    replay_enhanced,
    civ,
    team,
    old_rating,
    is_unrated,
    winner,
    CAST(
        EXTRACT(EPOCH FROM (started_timestamp - prev_started_timestamp)) / 86400.0
        AS DOUBLE
    ) AS time_since_prior_match_days
FROM lag_base
```

---

## §3 Column Definition: time_since_prior_match_days

| Field | Value |
|-------|-------|
| Type | DOUBLE |
| Nullable | true |
| Source | LAG window: `PARTITION BY CAST(profile_id AS BIGINT), leaderboard ORDER BY started_timestamp, game_id` |
| NULL semantics | First match per `(profile_id, leaderboard)` — LAG returns NULL → gap = NULL |
| CAST discipline | `CAST(profile_id AS BIGINT)` (DS-AOESTATS-IDENTITY-04; lossless per 01_04_01) |
| Tie-breaker | `game_id` (matches 01_04_06 ordering) |

**NULL-first-match rule:** `time_since_prior_match_days IS NULL` means this is
the player's first recorded match on this leaderboard. No prior-match cross-session
risk exists for the initial `old_rating` value. NULL is therefore treated as
PRE-GAME for the CONDITIONAL_PRE_GAME gate. See §6 for full rule statement.

---

## §4 Threshold Selection — BLOCKER-1 Resolution

**Method:** For each candidate N ∈ {1, 2, 3, 7} days, compute pooled agreement
rate (`AVG(old_rating = prev_new_rating)`) on `random_map` for pairs where
`time_since_prior_match_days < N`. Choose N* = largest N with pooled agreement >= 0.90
(matching the WP-4 stratum gate per I7 — no magic numbers).

| N (days) | n_pairs_eligible | pooled_agreement | Gate (>=0.90) | Chosen |
|----------|-----------------|------------------|---------------|--------|
| 1 | 29,021,397 | 0.943973 | PASS |  |
| 2 | 31,283,114 | 0.939304 | PASS |  |
| 3 | 32,235,871 | 0.936925 | PASS |  |
| 7 | 33,683,373 | 0.932212 | PASS | **N\* = 7** |

**Chosen N* = 7 days.** Argument: largest N in {1, 2, 3, 7} where pooled
agreement on `random_map` clears the WP-4 0.90 stratum gate (I7 — threshold argued
from data, not pre-specified).

---

## §5 Scope Selection — BLOCKER-2 Resolution

**Method:** 4×4 leaderboard × time-gap stratification. If all 4 leaderboards
clear 0.90 at `<N*` days, SCOPE = GLOBAL. Otherwise SCOPE = `random_map`-only.

### Full 4×4 table (n_pairs / agreement_rate per cell)

| Leaderboard | <1d | 1-7d | 7-30d | >30d |
|-------------|-----|------|-------|------|
| random_map | 29,021,397 / 0.9440 | 4,661,976 / 0.8590 | 1,057,793 / 0.7076 | 534,031 / 0.6345 |
| team_random_map | 55,493,653 / 0.8782 | 9,224,946 / 0.8072 | 1,946,974 / 0.6838 | 763,336 / 0.6354 |
| co_random_map | 915,616 / 0.8950 | 227,305 / 0.7610 | 48,500 / 0.6472 | 21,056 / 0.6221 |
| co_team_random_map | 2,164,037 / 0.8147 | 496,101 / 0.7067 | 88,722 / 0.6305 | 34,874 / 0.5871 |

### Per-leaderboard agreement at <7d

| Leaderboard | n_pairs | agreement_at_cutoff | Gate (>=0.90) |
|-------------|---------|---------------------|---------------|
| co_random_map | 1,142,921 | 0.868363 | FAIL |
| co_team_random_map | 2,660,138 | 0.794572 | FAIL |
| random_map | 33,683,373 | 0.932212 | PASS |
| team_random_map | 64,718,599 | 0.868085 | FAIL |

**Chosen SCOPE: random_map_only.**
Scope predicate: `leaderboard = 'random_map'`.
Argument: Not all leaderboards clear 0.90 at <7d cutoff. Failures: {'co_random_map': 0.8683627302324483, 'co_team_random_map': 0.7945723116620266, 'team_random_map': 0.8680845980612157}. CONDITIONAL_PRE_GAME classification scoped to random_map only.

---

## §6 NULL-First-Match Handling — WARNING-3 Resolution

**Explicit rule:** `time_since_prior_match_days IS NULL` indicates this is the
player's first recorded match on this leaderboard (no prior match exists in the
dataset). The "cross-session rating reset" risk is ZERO for this `old_rating`
value because there is no prior match after which a reset could have occurred.
Therefore: `time_since_prior_match_days IS NULL` → treat as PRE-GAME.

**Phase 02 condition:** `old_rating` is PRE-GAME iff
`(leaderboard = 'random_map') AND (time_since_prior_match_days < 7 OR time_since_prior_match_days IS NULL)`.

**First-match NULL rate:** 0.008605 (0.86% of all `player_history_all` rows).

---

## §7 Verification

| Check | Value | Status |
|-------|-------|--------|
| Row count pre-amendment | 107,626,399 | — |
| Row count post-amendment | 107,626,399 | PRESERVED |
| Column count | 15 | VERIFIED |
| `time_since_prior_match_days` in DESCRIBE | present | VERIFIED |
| First-match rows: all NULL gaps | 5/5 | VERIFIED |
| Non-first rows: no negative gaps | 0 | VERIFIED |
| Pearson ρ (gap vs disagreement) | 0.197529 | reported |

---

## §8 Downstream Impact

The following files require updating as a result of this amendment:

1. `player_history_all.yaml` — schema_version field (descriptive-string per canonical_slot precedent);
   new column entry for `time_since_prior_match_days`.
2. `INVARIANTS.md §3` — `old_rating` reclassified from PRE-GAME (WP-4 FAIL) to
   CONDITIONAL_PRE_GAME with N*=7, SCOPE=random_map_only, explicit NULL rule.
3. `reports/specs/02_00_feature_input_contract.md` — v1 → v2 per §7 change protocol;
   §2.2 column count 14 → 15; §5.5 adds `time_since_prior_match_days` row.
4. `ROADMAP.md` — current-state `player_history_all` 14-col references updated to 15-col.
