# 01_03_03 Table Utility Assessment — aoe2companion

**Step:** 01_03_03 | **Dataset:** aoe2companion | **Date:** 2026-04-16

## Summary

| Table | Is time series | I3 classification | Pipeline use |
|---|---|---|---|
| `matches_raw` | Yes | USABLE | PRIMARY feature source |
| `ratings_raw` | Yes (no rm_1v1 data) | CONDITIONALLY USABLE | Unranked lb=0 only |
| `leaderboards_raw` | No (single snapshot) | NOT USABLE for temporal features | Static metadata only |
| `profiles_raw` | No (no timestamps) | NOT USABLE for temporal features | Static metadata only |

---

## T01 — leaderboards_raw characterization

- **Rows:** 2,381,227 across 1 source file
- **Distinct players:** 1,863,297 across 16 leaderboards
- **updatedAt range:** 2023-08-23 22:05:17.362000 to 2026-04-06 00:12:39.518000
- **lastMatchTime range:** 2022-09-06 18:47:29 to 2026-04-06 00:12:25

**avg_entries_per_player = 1.0 for all major leaderboards.** This confirms
leaderboards_raw is a single snapshot per player, not a time series.

**rm_1v1 coverage:** 242,054 players in leaderboards_raw vs 538,280 in matches_raw (45.0% overlap).

**I3 verdict:** NOT USABLE for temporal feature derivation.
Using leaderboards_raw.rating as a feature for game at time T would use
the April 2026 snapshot rating, violating I3 for all T before that date.

```sql
-- SQL: leaderboards_raw snapshot check

SELECT
    leaderboard,
    COUNT(*) AS n_rows,
    COUNT(DISTINCT profileId) AS n_players,
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT profileId), 3) AS avg_entries_per_player,
    COUNT(DISTINCT DATE_TRUNC('day', updatedAt)) AS n_distinct_updatedAt_days
FROM leaderboards_raw
WHERE leaderboard IN ('rm_1v1', 'rm_team', 'unranked')
GROUP BY leaderboard
ORDER BY leaderboard

```

---

## T01 — profiles_raw characterization

- **Rows:** 3,609,686 (1 row per profileId, 1 source file)
- **Distinct profileIds:** 3,609,686
- **TIMESTAMP columns:** 0 (no temporal dimension)
- **steamId non-null:** 3,607,835 (99.9%)
- **clan non-null:** 3,609,683 (100.0%)
- **country non-null:** 2,005,595 (55.6%)

**Coverage:** 100% of matches_raw profileIds (excl. -1) appear in profiles_raw.

**I3 verdict:** NOT USABLE for temporal features (no timestamps).
May be used as a static metadata lookup for steamId and clan.

---

## T02 — matches_raw.rating disambiguation

**Method:** Cross-reference matches_raw.rating against ratings_raw per-game
entries for the unranked leaderboard (lb=0, the only leaderboard with
temporal overlap in both tables).

For a focal player (profileId=3299155, 2,291+ matches),
for each match, find the ratings_raw entry with `date <= started` (nearest
entry at or before match start).

**Results:**

| Hypothesis | Test | Match rate |
|---|---|---|
| PRE-GAME: match_rating == rating_before | nearest rating before started | **99.8%** |
| POST-GAME direct: match_rating == rating_after | nearest rating after finished | 78.8% |
| POST-GAME derived: match_rating + ratingDiff == rating_after | derived | 79.2% |

**VERDICT: matches_raw.rating is the PRE-GAME rating** (99.8% exact match).
The ~2% mismatch cases are attributable to gaps in ratings_raw coverage
(games played by the player that were not captured in ratings_raw).

**Implication for I3:** matches_raw.rating can be used directly as a
pre-game rating feature without transformation. It is safe to use
`rating` from game T-1 (i.e., from matches with `started < T`) as a
feature for prediction of game T.

```sql
-- SQL: PRE-GAME hypothesis test

WITH player_matches AS (
    SELECT matchId, profileId, started, finished,
           rating AS match_rating, ratingDiff AS match_rd
    FROM matches_raw
    WHERE profileId = 3299155
      AND internalLeaderboardId = 0
      AND rating IS NOT NULL
      AND ratingDiff IS NOT NULL
),
nearest_before AS (
    SELECT
        m.matchId, m.profileId, m.started, m.match_rating, m.match_rd,
        MAX(r.date) AS nearest_before_date,
        MAX_BY(r.rating, r.date) AS rating_before
    FROM player_matches m
    JOIN ratings_raw r
        ON r.profile_id = m.profileId
       AND r.leaderboard_id = 0
       AND r.date <= m.started
    GROUP BY m.matchId, m.profileId, m.started, m.match_rating, m.match_rd
)
SELECT
    COUNT(*) AS n_matches_with_prior_rating,
    COUNT(CASE WHEN match_rating = rating_before THEN 1 END) AS n_exact_pre_match,
    ROUND(
        100.0 * COUNT(CASE WHEN match_rating = rating_before THEN 1 END) / COUNT(*), 1
    ) AS pct_exact_pre_match,
    APPROX_QUANTILE(ABS(match_rating - rating_before), 0.5) AS median_abs_diff,
    MAX(ABS(match_rating - rating_before)) AS max_abs_diff
FROM nearest_before

```

---

## Artifacts

- `01_03_03_table_utility_assessment.json` — full results with all SQL queries
