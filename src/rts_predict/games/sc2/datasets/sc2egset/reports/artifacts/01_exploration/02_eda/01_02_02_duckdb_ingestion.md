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
- **game_events_raw / tracker_events_raw / message_events_raw**: DuckDB
  views over per-type Parquet subdirectories. Single-pass extraction;
  columns: filename (relative, I10), loop, evtTypeName, event_data.

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

## Event extraction


| Event type | Rows extracted | DuckDB view |
|------------|---------------|-------------|
| gameEvents | 608,618,823 | game_events_raw |
| trackerEvents | 62,003,411 | tracker_events_raw |
| messageEvents | 52,167 | message_events_raw |

## game_events_raw health checks


### NULL rates


```sql
SELECT
    COUNT(*)                       AS total_rows,
    COUNT(*) - COUNT(filename)     AS filename_null,
    COUNT(*) - COUNT(loop)         AS loop_null,
    COUNT(*) - COUNT(evtTypeName)  AS evtTypeName_null,
    COUNT(*) - COUNT(event_data)   AS event_data_null
FROM game_events_raw
```


|   total_rows |   filename_null |   loop_null |   evtTypeName_null |   event_data_null |
|-------------:|----------------:|------------:|-------------------:|------------------:|
|    608618823 |               0 |           0 |                  0 |                 0 |

### Filename coverage


```sql
SELECT
    COUNT(DISTINCT e.filename)  AS event_files,
    COUNT(DISTINCT rm.filename) AS meta_files,
    COUNT(DISTINCT e.filename)
        - COUNT(DISTINCT CASE WHEN rm.filename IS NOT NULL
                              THEN e.filename END) AS orphan_event_files
FROM game_events_raw e
LEFT JOIN replays_meta_raw rm ON e.filename = rm.filename
```


|   event_files |   meta_files |   orphan_event_files |
|--------------:|-------------:|---------------------:|
|         22390 |        22390 |                    0 |

### Top-10 evtTypeName


```sql
SELECT evtTypeName, COUNT(*) AS event_count
FROM game_events_raw
GROUP BY evtTypeName
ORDER BY event_count DESC
LIMIT 10
```


| evtTypeName          |   event_count |
|:---------------------|--------------:|
| CameraUpdate         |     387507855 |
| ControlGroupUpdate   |      69227281 |
| CommandManagerState  |      43946635 |
| SelectionDelta       |      40855099 |
| Cmd                  |      31201304 |
| CmdUpdateTargetPoint |      25863707 |
| CmdUpdateTargetUnit  |       8348208 |
| CameraSave           |       1027659 |
| TriggerMouseMoved    |        380197 |
| UserOptions          |        131738 |

## tracker_events_raw health checks


### NULL rates


```sql
SELECT
    COUNT(*)                       AS total_rows,
    COUNT(*) - COUNT(filename)     AS filename_null,
    COUNT(*) - COUNT(loop)         AS loop_null,
    COUNT(*) - COUNT(evtTypeName)  AS evtTypeName_null,
    COUNT(*) - COUNT(event_data)   AS event_data_null
FROM tracker_events_raw
```


|   total_rows |   filename_null |   loop_null |   evtTypeName_null |   event_data_null |
|-------------:|----------------:|------------:|-------------------:|------------------:|
|     62003411 |               0 |           0 |                  0 |                 0 |

### Filename coverage


```sql
SELECT
    COUNT(DISTINCT e.filename)  AS event_files,
    COUNT(DISTINCT rm.filename) AS meta_files,
    COUNT(DISTINCT e.filename)
        - COUNT(DISTINCT CASE WHEN rm.filename IS NOT NULL
                              THEN e.filename END) AS orphan_event_files
FROM tracker_events_raw e
LEFT JOIN replays_meta_raw rm ON e.filename = rm.filename
```


|   event_files |   meta_files |   orphan_event_files |
|--------------:|-------------:|---------------------:|
|         22390 |        22390 |                    0 |

### Top-10 evtTypeName


```sql
SELECT evtTypeName, COUNT(*) AS event_count
FROM tracker_events_raw
GROUP BY evtTypeName
ORDER BY event_count DESC
LIMIT 10
```


| evtTypeName     |   event_count |
|:----------------|--------------:|
| UnitBorn        |      22372489 |
| UnitDied        |      16053834 |
| UnitTypeChange  |      10999108 |
| PlayerStats     |       4558736 |
| UnitInit        |       3151270 |
| UnitDone        |       3018764 |
| UnitPositions   |        941249 |
| Upgrade         |        797987 |
| UnitOwnerChange |         65157 |
| PlayerSetup     |         44817 |

## message_events_raw health checks


### NULL rates


```sql
SELECT
    COUNT(*)                       AS total_rows,
    COUNT(*) - COUNT(filename)     AS filename_null,
    COUNT(*) - COUNT(loop)         AS loop_null,
    COUNT(*) - COUNT(evtTypeName)  AS evtTypeName_null,
    COUNT(*) - COUNT(event_data)   AS event_data_null
FROM message_events_raw
```


|   total_rows |   filename_null |   loop_null |   evtTypeName_null |   event_data_null |
|-------------:|----------------:|------------:|-------------------:|------------------:|
|        52167 |               0 |           0 |                  0 |                 0 |

### Filename coverage


```sql
SELECT
    COUNT(DISTINCT e.filename)  AS event_files,
    COUNT(DISTINCT rm.filename) AS meta_files,
    COUNT(DISTINCT e.filename)
        - COUNT(DISTINCT CASE WHEN rm.filename IS NOT NULL
                              THEN e.filename END) AS orphan_event_files
FROM message_events_raw e
LEFT JOIN replays_meta_raw rm ON e.filename = rm.filename
```


|   event_files |   meta_files |   orphan_event_files |
|--------------:|-------------:|---------------------:|
|         22260 |        22260 |                    0 |

### Top-10 evtTypeName


```sql
SELECT evtTypeName, COUNT(*) AS event_count
FROM message_events_raw
GROUP BY evtTypeName
ORDER BY event_count DESC
LIMIT 10
```


| evtTypeName     |   event_count |
|:----------------|--------------:|
| Chat            |         51412 |
| Ping            |           714 |
| ReconnectNotify |            41 |