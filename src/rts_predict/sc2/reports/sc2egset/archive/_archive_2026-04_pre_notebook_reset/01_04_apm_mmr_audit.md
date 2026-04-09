# APM and MMR Audit

## APM zero-rate by year

### Query
```sql
SELECT
    EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'$.APM')::INTEGER = 0
              OR (entry.value->>'$.APM') IS NULL THEN 1 ELSE 0 END) AS apm_zero,
    ROUND(100.0 * SUM(CASE WHEN (entry.value->>'$.APM')::INTEGER = 0
              OR (entry.value->>'$.APM') IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_zero
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1 ORDER BY 1
```

### Results

|   year |   total_slots |   apm_zero |   pct_zero |
|-------:|--------------:|-----------:|-----------:|
|   2016 |          1110 |       1110 |      100   |
|   2017 |          4004 |         18 |        0.4 |
|   2018 |          6360 |          0 |        0   |
|   2019 |          7772 |          3 |        0   |
|   2020 |          5706 |          0 |        0   |
|   2021 |          7672 |          0 |        0   |
|   2022 |          6588 |          0 |        0   |
|   2023 |          3504 |          0 |        0   |
|   2024 |          2101 |          1 |        0   |

## MMR zero-rate by year

### Query
```sql
SELECT
    EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'$.MMR')::INTEGER = 0
              OR (entry.value->>'$.MMR') IS NULL THEN 1 ELSE 0 END) AS mmr_zero,
    ROUND(100.0 * SUM(CASE WHEN (entry.value->>'$.MMR')::INTEGER = 0
              OR (entry.value->>'$.MMR') IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_zero
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1 ORDER BY 1
```

### Results

|   year |   total_slots |   mmr_zero |   pct_zero |
|-------:|--------------:|-----------:|-----------:|
|   2016 |          1110 |       1110 |      100   |
|   2017 |          4004 |       3179 |       79.4 |
|   2018 |          6360 |       4999 |       78.6 |
|   2019 |          7772 |       5613 |       72.2 |
|   2020 |          5706 |       3746 |       65.7 |
|   2021 |          7672 |       6947 |       90.6 |
|   2022 |          6588 |       6341 |       96.3 |
|   2023 |          3504 |       3465 |       98.9 |
|   2024 |          2101 |       2089 |       99.4 |

## MMR availability by league

### Query
```sql
SELECT
    entry.value->>'$.highestLeague' AS league,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'$.MMR')::INTEGER > 0 THEN 1 ELSE 0 END) AS mmr_nonzero,
    ROUND(100.0 * SUM(CASE WHEN (entry.value->>'$.MMR')::INTEGER > 0
          THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_nonzero
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1 ORDER BY total_slots DESC
```

### Results

| league      |   total_slots |   mmr_nonzero |   pct_nonzero |
|:------------|--------------:|--------------:|--------------:|
| Unknown     |         32338 |          2063 |           6.4 |
| Master      |          6458 |          2715 |          42   |
| Grandmaster |          4745 |          1885 |          39.7 |
| Diamond     |           718 |           342 |          47.6 |
| Unranked    |           224 |             0 |           0   |
| Platinum    |           131 |            71 |          54.2 |
| Gold        |           119 |            55 |          46.2 |
| Bronze      |            73 |            32 |          43.8 |
| Silver      |             9 |             6 |          66.7 |
|             |             2 |             0 |           0   |

## Conclusions

- **APM**: Usable from 2017 onward (Scientific Invariant #7).
  2016 tournaments have systematic zero APM.
- **MMR**: NOT usable as a direct feature.
  Systematic missingness driven by tournament organiser, year,
  and highestLeague availability.
  Player skill must be derived from match history.
