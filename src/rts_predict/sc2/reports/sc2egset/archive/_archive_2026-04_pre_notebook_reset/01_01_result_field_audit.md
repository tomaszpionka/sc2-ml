# Result Field Audit

## Distinct result values

### Query
```sql
SELECT
    entry.value->>'$.result' AS result_value,
    COUNT(*) AS slot_count
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1
ORDER BY slot_count DESC
```

### Results

| result_value   |   slot_count |
|:---------------|-------------:|
| Loss           |        22409 |
| Win            |        22382 |
| Undecided      |           24 |
| Tie            |            2 |

## Null and non-standard results

### Query
```sql
WITH extracted AS (
    SELECT entry.value->>'$.result' AS result_val
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
)
SELECT
    SUM(CASE WHEN result_val IS NULL THEN 1 ELSE 0 END) AS null_results,
    SUM(CASE WHEN result_val IS NOT NULL
              AND result_val != 'Win'
              AND result_val != 'Loss' THEN 1 ELSE 0 END) AS non_standard_results
FROM extracted
```

### Results

|   null_results |   non_standard_results |
|---------------:|-----------------------:|
|              0 |                     26 |

## Anomalous replays (no winner or multiple winners)

### Query
```sql
WITH replay_results AS (
    SELECT
        filename,
        SUM(CASE WHEN entry.value->>'$.result' = 'Win' THEN 1 ELSE 0 END) AS win_count,
        SUM(CASE WHEN entry.value->>'$.result' = 'Loss' THEN 1 ELSE 0 END) AS loss_count
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
    GROUP BY filename
)
SELECT
    SUM(CASE WHEN win_count = 0 THEN 1 ELSE 0 END) AS no_winner_replays,
    SUM(CASE WHEN win_count >= 2 THEN 1 ELSE 0 END) AS multiple_winner_replays
FROM replay_results
```

### Results

|   no_winner_replays |   multiple_winner_replays |
|--------------------:|--------------------------:|
|                  13 |                         4 |
