# Step 01_03_03 -- Table Utility Assessment: aoestats

**Date:** 2026-04-15  
**Dataset:** aoestats  
**Pipeline Section:** 01_03 -- Systematic Data Profiling  

## Scope

Empirical assessment of all 3 raw tables (matches_raw, players_raw, overviews_raw)
for prediction pipeline utility. Column overlap, join integrity, ELO redundancy,
overviews_raw STRUCT content, and replay_summary_raw fill rate.

## T01: Column Overlap

- matches_raw: 18 columns
- players_raw: 14 columns
- Shared columns (2): `filename`, `game_id`
- matches_raw exclusive (16): `avg_elo`, `duration`, `game_speed`, `game_type`, `irl_duration`, `leaderboard`, `map`, `mirror`, `num_players`, `patch`, `raw_match_type`, `replay_enhanced`, `started_timestamp`, `starting_age`, `team_0_elo`, `team_1_elo`
- players_raw exclusive (12): `castle_age_uptime`, `civ`, `feudal_age_uptime`, `imperial_age_uptime`, `match_rating_diff`, `new_rating`, `old_rating`, `opening`, `profile_id`, `replay_summary_raw`, `team`, `winner`

**Confirmed:** `game_id` is the join key (present in both tables).  
**Confirmed:** `winner` is exclusive to `players_raw`.  
**Confirmed:** `started_timestamp` is exclusive to `matches_raw`.  

```sql
DESCRIBE matches_raw
-- (also for players_raw)
```

## T02: Join Integrity

- Orphan matches (no players): 212,890
  (validated against 01_03_01 MATCHES_WITHOUT_PLAYERS = 212,890)
- Orphan player game_ids (no match): 0
- matches_raw: 30,690,651 distinct game_ids in 30,690,651 rows (100.0000% unique)
- players_raw: 30,477,761 distinct game_ids, avg 3.53 rows/game_id

```sql

SELECT COUNT(*) AS orphan_matches
FROM matches_raw m
WHERE NOT EXISTS (
    SELECT 1 FROM players_raw p WHERE p.game_id = m.game_id
)

```

```sql

SELECT COUNT(DISTINCT game_id) AS orphan_player_game_ids,
       COUNT(*) AS orphan_player_rows
FROM players_raw p
WHERE NOT EXISTS (
    SELECT 1 FROM matches_raw m WHERE m.game_id = p.game_id
)

```

## T03: ELO Redundancy

- avg_elo = (team_0_elo + team_1_elo) / 2: 99.9955% exact match
- avg_elo derivable from players old_rating (1v1 matches, within 0.5 ELO): 100.0000%
- Spearman rho (avg_elo vs player_avg_old_rating, n=100K): 1.000000

**Temporal annotation:**
- `old_rating`: pre-game rating -- temporally safe (I3 compliant)
- `new_rating`: post-game rating -- **LEAKING** -- must not be used as a feature

```sql

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE avg_elo IS NULL OR team_0_elo IS NULL OR team_1_elo IS NULL)
        AS any_null,
    COUNT(*) FILTER (
        WHERE avg_elo IS NOT NULL
          AND team_0_elo IS NOT NULL
          AND team_1_elo IS NOT NULL
          AND ABS(avg_elo - (team_0_elo + team_1_elo) / 2.0) < 0.001
    ) AS exact_match_count,
    COUNT(*) FILTER (
        WHERE avg_elo IS NOT NULL
          AND team_0_elo IS NOT NULL
          AND team_1_elo IS NOT NULL
          AND ABS(avg_elo - (team_0_elo + team_1_elo) / 2.0) >= 0.001
    ) AS inexact_match_count,
    MAX(
        CASE
            WHEN avg_elo IS NOT NULL AND team_0_elo IS NOT NULL AND team_1_elo IS NOT NULL
            THEN ABS(avg_elo - (team_0_elo + team_1_elo) / 2.0)
        END
    ) AS max_abs_deviation
FROM matches_raw

```

```sql

WITH true_1v1 AS (
    SELECT game_id
    FROM players_raw
    GROUP BY game_id
    HAVING COUNT(*) = 2
),
player_avg_elo AS (
    SELECT p.game_id,
           AVG(CAST(p.old_rating AS DOUBLE)) AS derived_avg_elo
    FROM players_raw p
    INNER JOIN true_1v1 t ON p.game_id = t.game_id
    WHERE p.old_rating IS NOT NULL
    GROUP BY p.game_id
    HAVING COUNT(*) = 2
)
SELECT
    COUNT(*) AS joined_count,
    COUNT(*) FILTER (WHERE m.avg_elo IS NOT NULL) AS both_non_null,
    COUNT(*) FILTER (
        WHERE m.avg_elo IS NOT NULL
          AND ABS(m.avg_elo - pa.derived_avg_elo) < 0.5
    ) AS within_half_elo,
    COUNT(*) FILTER (
        WHERE m.avg_elo IS NOT NULL
          AND ABS(m.avg_elo - pa.derived_avg_elo) < 1.0
    ) AS within_one_elo,
    AVG(ABS(m.avg_elo - pa.derived_avg_elo)) FILTER (WHERE m.avg_elo IS NOT NULL)
        AS mean_abs_deviation,
    MAX(ABS(m.avg_elo - pa.derived_avg_elo)) FILTER (WHERE m.avg_elo IS NOT NULL)
        AS max_abs_deviation,
    PERCENTILE_CONT(0.5) WITHIN GROUP (
        ORDER BY ABS(m.avg_elo - pa.derived_avg_elo)
    ) FILTER (WHERE m.avg_elo IS NOT NULL) AS median_abs_deviation
FROM player_avg_elo pa
INNER JOIN matches_raw m ON m.game_id = pa.game_id

```

```sql

WITH true_1v1 AS (
    SELECT game_id
    FROM players_raw
    GROUP BY game_id
    HAVING COUNT(*) = 2
),
player_avg AS (
    SELECT p.game_id,
           AVG(CAST(p.old_rating AS DOUBLE)) AS player_avg_old_rating
    FROM players_raw p
    INNER JOIN true_1v1 t ON p.game_id = t.game_id
    WHERE p.old_rating IS NOT NULL
    GROUP BY p.game_id
    HAVING COUNT(*) = 2
),
joined AS (
    SELECT
        m.avg_elo,
        pa.player_avg_old_rating,
        m.team_0_elo,
        m.team_1_elo
    FROM player_avg pa
    INNER JOIN matches_raw m ON m.game_id = pa.game_id
    WHERE m.avg_elo IS NOT NULL
      AND m.team_0_elo IS NOT NULL
      AND m.team_1_elo IS NOT NULL
)
SELECT *
FROM joined
USING SAMPLE RESERVOIR(100000)

```

## T04: overviews_raw and replay_summary_raw

- overviews_raw: 1 row (singleton reference)
  - 19 patches (release_date range: 2022-08-29 00:00:00 to 2025-12-02 00:00:00)
  - 50 civs, 10 openings, 4 ELO groupings
  - tournament_stages: ['all', 'qualifiers', 'main_event']

- replay_summary_raw (players_raw column):
  - Non-empty: 13.9474% (15,011,294 rows)
  - Empty ('{}' or NULL): 86.0526%
  - Max content length: 7,484 chars

```sql

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE replay_summary_raw IS NULL) AS null_count,
    COUNT(*) FILTER (WHERE replay_summary_raw = '{}') AS empty_object_count,
    COUNT(*) FILTER (WHERE TRIM(replay_summary_raw) = '') AS empty_string_count,
    COUNT(*) FILTER (
        WHERE replay_summary_raw IS NOT NULL
          AND replay_summary_raw != '{}'
          AND TRIM(replay_summary_raw) != ''
    ) AS non_empty_count,
    MIN(LENGTH(replay_summary_raw)) AS min_length,
    MAX(LENGTH(replay_summary_raw)) AS max_length,
    APPROX_COUNT_DISTINCT(replay_summary_raw) AS approx_distinct_values
FROM players_raw

```

## T05: Verdicts

### matches_raw
**Verdict:** ESSENTIAL  
**Rationale:** Provides started_timestamp (sole temporal anchor -- I3 critical), map, leaderboard, patch, duration, mirror, and other match-level context. ELO columns (avg_elo, team_0/1_elo) have Spearman rho=1.0000 with player old_rating (near-perfect redundancy), so match-level ELOs are derivable from players_raw but not vice versa for started_timestamp.

### players_raw
**Verdict:** ESSENTIAL  
**Rationale:** Contains winner (prediction target -- no alternative), old_rating (pre-game player ELO -- I3 safe), civ, opening, age uptimes, team. new_rating is LEAKING (post-game) and must be excluded from features.

### overviews_raw
**Verdict:** SUPPLEMENTARY REFERENCE  
**Rationale:** Singleton lookup. Provides 19-entry patch->release_date mapping not available elsewhere. Can enrich matches_raw.patch column. No direct prediction-critical columns.

### replay_summary_raw
**Verdict:** PARTIAL UTILITY -- significant non-empty fraction; content warrants further investigation.  
**Rationale:** 13.95% non-empty rows (15,011,294 / 107,627,584). Max content length: 7,484 chars.

## Artifact

`01_03_03_table_utility.json` -- JSON with all query results, SQL, and verdicts.
