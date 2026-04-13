# Step 01_02_02 -- DuckDB Ingestion: sc2egset


## Tables created


| Table | Rows |
|-------|------|
| replays_meta_raw | 22,390 |
| replay_players_raw | 44,817 |
| map_aliases_raw | 104,160 |

## Ingestion strategy


Three-stream extraction (see 01_02_01 design artifact):
- **replays_meta_raw**: DuckDB table, one row per replay. Metadata as
  STRUCT columns, ToonPlayerDescMap as VARCHAR (JSON text blob).
  Event arrays excluded. filename stores relative path from raw_dir.
- **replay_players_raw**: DuckDB table, normalised from ToonPlayerDescMap.
  One row per (replay, player) with all player fields extracted.
  filename stores relative path from raw_dir.
- **map_aliases_raw**: DuckDB table, all tournament mapping files with
  tournament provenance column. filename stores relative path from raw_dir.
- **Events**: Parquet extraction (optional, SSD-dependent, deferred).

## NULL rates


### replays_meta_raw


```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(details) AS details_null,
    COUNT(*) - COUNT(header) AS header_null,
    COUNT(*) - COUNT(initData) AS initData_null,
    COUNT(*) - COUNT(metadata) AS metadata_null,
    COUNT(*) - COUNT(ToonPlayerDescMap) AS tpdm_null,
    COUNT(*) - COUNT(filename) AS filename_null
FROM replays_meta_raw
```


|   total_rows |   details_null |   header_null |   initData_null |   metadata_null |   tpdm_null |   filename_null |
|-------------:|---------------:|--------------:|----------------:|----------------:|------------:|----------------:|
|        22390 |              0 |             0 |               0 |               0 |           0 |               0 |

### replay_players_raw


```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(toon_id) AS toon_id_null,
    COUNT(*) - COUNT(nickname) AS nickname_null,
    COUNT(*) - COUNT(MMR) AS MMR_null,
    COUNT(*) - COUNT(race) AS race_null,
    COUNT(*) - COUNT(result) AS result_null,
    COUNT(*) - COUNT(APM) AS APM_null,
    COUNT(*) - COUNT(filename) AS filename_null
FROM replay_players_raw
```


|   total_rows |   toon_id_null |   nickname_null |   MMR_null |   race_null |   result_null |   APM_null |   filename_null |
|-------------:|---------------:|----------------:|-----------:|------------:|--------------:|-----------:|----------------:|
|        44817 |              0 |               0 |          0 |           0 |             0 |          0 |               0 |

### map_aliases_raw


```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(tournament) AS tournament_null,
    COUNT(*) - COUNT(foreign_name) AS foreign_name_null,
    COUNT(*) - COUNT(english_name) AS english_name_null,
    COUNT(DISTINCT tournament) AS distinct_tournaments
FROM map_aliases_raw
```


|   total_rows |   tournament_null |   foreign_name_null |   english_name_null |   distinct_tournaments |
|-------------:|------------------:|--------------------:|--------------------:|-----------------------:|
|       104160 |                 0 |                   0 |                   0 |                     70 |

## ToonPlayerDescMap type verification


```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'replays_meta_raw' AND column_name = 'ToonPlayerDescMap'
```


| column_name       | data_type   |
|:------------------|:------------|
| ToonPlayerDescMap | VARCHAR     |

## Cross-table integrity


### Players -> Meta


```sql
SELECT
    COUNT(DISTINCT rp.filename) AS player_files,
    COUNT(DISTINCT rm.filename) AS meta_files,
    COUNT(DISTINCT rp.filename)
        - COUNT(DISTINCT CASE WHEN rm.filename IS NOT NULL
                              THEN rp.filename END) AS orphan_player_files
FROM replay_players_raw rp
LEFT JOIN replays_meta_raw rm ON rp.filename = rm.filename
```


|   player_files |   meta_files |   orphan_player_files |
|---------------:|-------------:|----------------------:|
|          22390 |        22390 |                     0 |

### Meta -> Players (reverse)


```sql
SELECT
    COUNT(DISTINCT rm.filename) AS meta_files,
    COUNT(DISTINCT rm.filename)
        - COUNT(DISTINCT CASE WHEN rp.filename IS NOT NULL
                              THEN rm.filename END) AS orphan_meta_files
FROM replays_meta_raw rm
LEFT JOIN replay_players_raw rp ON rm.filename = rp.filename
```


|   meta_files |   orphan_meta_files |
|-------------:|--------------------:|
|        22390 |                   0 |

## Player count per replay


```sql
SELECT players_per_replay, COUNT(*) AS replay_count
FROM (
    SELECT filename, COUNT(*) AS players_per_replay
    FROM replay_players_raw
    GROUP BY filename
)
GROUP BY players_per_replay
ORDER BY players_per_replay
```


|   players_per_replay |   replay_count |
|---------------------:|---------------:|
|                    1 |              3 |
|                    2 |          22379 |
|                    4 |              2 |
|                    6 |              1 |
|                    8 |              3 |
|                    9 |              2 |

## map_aliases_raw dedup profile


```sql
SELECT
    COUNT(DISTINCT foreign_name) AS unique_foreign,
    COUNT(DISTINCT english_name) AS unique_english,
    COUNT(DISTINCT tournament) AS unique_tournaments,
    COUNT(*) AS total_rows
FROM map_aliases_raw
```


|   unique_foreign |   unique_english |   unique_tournaments |   total_rows |
|-----------------:|-----------------:|---------------------:|-------------:|
|             1488 |              215 |                   70 |       104160 |