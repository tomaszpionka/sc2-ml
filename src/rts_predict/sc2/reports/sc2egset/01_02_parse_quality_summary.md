# Parse Quality Summary

## Query
```sql
WITH tournament_raw AS (
    SELECT
        split_part(filename, '/', -3) AS tournament_dir,
        regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id,
        (details->>'$.timeUTC')::TIMESTAMP AS match_time,
        filename
    FROM raw
),
tracker_ids AS (
    SELECT DISTINCT regexp_extract(match_id, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id
    FROM tracker_events_raw
),
player_counts AS (
    SELECT
        regexp_extract(match_id, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id,
        COUNT(*) AS player_count
    FROM match_player_map
    GROUP BY 1
),
result_extracted AS (
    SELECT
        regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id,
        entry.value->>'$.result' AS result_val
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
),
result_check AS (
    SELECT
        replay_id,
        SUM(CASE WHEN result_val = 'Win' THEN 1 ELSE 0 END) AS win_count,
        SUM(
            CASE WHEN result_val IS NULL
                      OR (result_val != 'Win' AND result_val != 'Loss')
                 THEN 1 ELSE 0 END
        ) AS bad_results
    FROM result_extracted
    GROUP BY 1
)
SELECT
    tr.tournament_dir,
    COUNT(*) AS total_replays,
    SUM(CASE WHEN t.replay_id IS NOT NULL THEN 1 ELSE 0 END) AS has_events,
    SUM(CASE WHEN t.replay_id IS NULL THEN 1 ELSE 0 END) AS missing_events,
    SUM(CASE WHEN tr.match_time IS NULL THEN 1 ELSE 0 END) AS null_timestamp,
    ROUND(100.0 * SUM(CASE WHEN t.replay_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1)
        AS event_coverage_pct,
    SUM(CASE WHEN pc.player_count IS NULL OR pc.player_count != 2 THEN 1 ELSE 0 END)
        AS player_count_anomalies,
    SUM(CASE WHEN rc.win_count != 1 OR rc.bad_results > 0 THEN 1 ELSE 0 END)
        AS result_anomalies
FROM tournament_raw tr
LEFT JOIN tracker_ids t ON tr.replay_id = t.replay_id
LEFT JOIN player_counts pc ON pc.replay_id = tr.replay_id
LEFT JOIN result_check rc ON rc.replay_id = tr.replay_id
GROUP BY tr.tournament_dir
ORDER BY event_coverage_pct ASC
```

## Summary: 70 tournaments total, 18 flagged

Flagging thresholds:
- event_coverage_pct < 80%
- player_count_anomalies > 0
- result_anomalies > 0

## Flagged tournaments

| tournament_dir                             |   total_replays |   has_events |   missing_events |   null_timestamp |   event_coverage_pct |   player_count_anomalies |   result_anomalies |
|:-------------------------------------------|----------------:|-------------:|-----------------:|-----------------:|---------------------:|-------------------------:|-------------------:|
| 2021_Cheeseadelphia_Winter_Championship    |              73 |           73 |                0 |                0 |                  100 |                        0 |                  1 |
| 2022_Dreamhack_SC2_Masters_Last_Chance2021 |             355 |          355 |                0 |                0 |                  100 |                        0 |                  1 |
| 2024_03_ESL_SC2_Masters_Spring_Finals      |             264 |          264 |                0 |                0 |                  100 |                        2 |                  1 |
| 2018_WCS_Leipzig                           |             420 |          420 |                0 |                0 |                  100 |                        0 |                  1 |
| 2019_IEM_Katowice                          |             440 |          440 |                0 |                0 |                  100 |                        0 |                  1 |
| 2018_HomeStory_Cup_XVII                    |             343 |          343 |                0 |                0 |                  100 |                        0 |                  1 |
| 2020_Dreamhack_SC2_Masters_Fall            |             799 |          799 |                0 |                0 |                  100 |                        0 |                  1 |
| 2018_IEM_Katowice                          |             444 |          444 |                0 |                0 |                  100 |                        0 |                  1 |
| 2017_HomeStory_Cup_XVI                     |             249 |          249 |                0 |                0 |                  100 |                        2 |                  1 |
| 2018_WCS_Valencia                          |             410 |          410 |                0 |                0 |                  100 |                        0 |                  1 |
| 2019_HomeStory_Cup_XIX                     |             330 |          330 |                0 |                0 |                  100 |                        1 |                  1 |
| 2022_Dreamhack_SC2_Masters_Valencia        |            1094 |         1094 |                0 |                0 |                  100 |                        0 |                  1 |
| 2020_TSL5                                  |             185 |          185 |                0 |                0 |                  100 |                        4 |                  2 |
| 2017_IEM_XI_World_Championship_Katowice    |             409 |          409 |                0 |                0 |                  100 |                        3 |                  0 |
| 2024_05_EWC                                |             154 |          154 |                0 |                0 |                  100 |                        1 |                  0 |
| 2017_WESG_Barcelona                        |             135 |          135 |                0 |                0 |                  100 |                        0 |                  1 |
| 2020_Dreamhack_SC2_Masters_Summer          |             783 |          783 |                0 |                0 |                  100 |                        0 |                  1 |
| 2021_ASUS_ROG_Fall                         |              78 |           78 |                0 |                0 |                  100 |                        0 |                  1 |
