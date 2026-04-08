# Phase 0 / Step 0.9 — Post-Rebuild Verification Report

**Date:** 2026-04-08  
**Branch:** feat/phase0-map-alias-ingestion

---

## 1. Summary

Phase 0 was rebuilt after replacing the silent-merge `map_translation` table with the row-per-file `raw_map_alias_files` table and removing ML view construction from `init_database`. The database now contains six raw tables only: `raw`, `raw_map_alias_files`, `tracker_events_raw`, `game_events_raw`, `match_player_map`, and `player_stats`.

- `raw` row count: 22390 (expected 22390)
- `raw_map_alias_files` row count: 70
- `tracker_events_raw` row count: 62003411
- `game_events_raw` row count: 608618823
- `match_player_map` row count: 44815
- `player_stats` row count: 4558736
- Distinct tournament dirs (alias table): 70
- Distinct tournament dirs (raw table): 70
- Distinct SHA1 versions: 2
- One-file-per-dir invariant (V3 == V5): True
- raw row count matches expected: True

---

## 2. Schema (PRAGMA table_info)

### raw_map_alias_files

```
 cid           name      type  notnull dflt_value    pk
   0 tournament_dir   VARCHAR     True       None False
   1      file_path   VARCHAR     True       None False
   2      byte_sha1   VARCHAR     True       None False
   3        n_bytes    BIGINT     True       None False
   4       raw_json   VARCHAR     True       None False
   5    ingested_at TIMESTAMP     True       None False
```

### tracker_events_raw

```
 cid       name    type  notnull dflt_value    pk
   0   match_id VARCHAR    False       None False
   1 event_type VARCHAR    False       None False
   2  game_loop INTEGER    False       None False
   3  player_id TINYINT    False       None False
   4 event_data VARCHAR    False       None False
```

### game_events_raw

```
 cid       name    type  notnull dflt_value    pk
   0   match_id VARCHAR    False       None False
   1 event_type VARCHAR    False       None False
   2  game_loop INTEGER    False       None False
   3    user_id INTEGER    False       None False
   4  player_id TINYINT    False       None False
   5 event_data VARCHAR    False       None False
```

### match_player_map

```
 cid             name    type  notnull dflt_value    pk
   0         match_id VARCHAR    False       None False
   1        player_id TINYINT    False       None False
   2          user_id INTEGER    False       None False
   3         nickname VARCHAR    False       None False
   4             race VARCHAR    False       None False
   5 total_game_loops INTEGER    False       None False
```

### player_stats

```
 cid                                 name    type  notnull dflt_value    pk
   0                             match_id VARCHAR    False       None False
   1                            game_loop INTEGER    False       None False
   2                            player_id TINYINT    False       None False
   3                            food_made   FLOAT    False       None False
   4                            food_used   FLOAT    False       None False
   5             minerals_collection_rate   FLOAT    False       None False
   6                     minerals_current   FLOAT    False       None False
   7          minerals_friendly_fire_army   FLOAT    False       None False
   8       minerals_friendly_fire_economy   FLOAT    False       None False
   9    minerals_friendly_fire_technology   FLOAT    False       None False
  10                 minerals_killed_army   FLOAT    False       None False
  11              minerals_killed_economy   FLOAT    False       None False
  12           minerals_killed_technology   FLOAT    False       None False
  13                   minerals_lost_army   FLOAT    False       None False
  14                minerals_lost_economy   FLOAT    False       None False
  15             minerals_lost_technology   FLOAT    False       None False
  16          minerals_used_active_forces   FLOAT    False       None False
  17           minerals_used_current_army   FLOAT    False       None False
  18        minerals_used_current_economy   FLOAT    False       None False
  19     minerals_used_current_technology   FLOAT    False       None False
  20       minerals_used_in_progress_army   FLOAT    False       None False
  21    minerals_used_in_progress_economy   FLOAT    False       None False
  22 minerals_used_in_progress_technology   FLOAT    False       None False
  23              vespene_collection_rate   FLOAT    False       None False
  24                      vespene_current   FLOAT    False       None False
  25           vespene_friendly_fire_army   FLOAT    False       None False
  26        vespene_friendly_fire_economy   FLOAT    False       None False
  27     vespene_friendly_fire_technology   FLOAT    False       None False
  28                  vespene_killed_army   FLOAT    False       None False
  29               vespene_killed_economy   FLOAT    False       None False
  30            vespene_killed_technology   FLOAT    False       None False
  31                    vespene_lost_army   FLOAT    False       None False
  32                 vespene_lost_economy   FLOAT    False       None False
  33              vespene_lost_technology   FLOAT    False       None False
  34           vespene_used_active_forces   FLOAT    False       None False
  35            vespene_used_current_army   FLOAT    False       None False
  36         vespene_used_current_economy   FLOAT    False       None False
  37      vespene_used_current_technology   FLOAT    False       None False
  38        vespene_used_in_progress_army   FLOAT    False       None False
  39     vespene_used_in_progress_economy   FLOAT    False       None False
  40  vespene_used_in_progress_technology   FLOAT    False       None False
  41                 workers_active_count   FLOAT    False       None False
```

---

## 3. Row Counts

| Table | Row count |
|-------|-----------|
| `raw` (V9) | 22390 |
| `raw_map_alias_files` (V3) | 70 |
| `tracker_events_raw` (V11) | 62003411 |
| `game_events_raw` (V12) | 608618823 |
| `match_player_map` (V13) | 44815 |
| `player_stats` (V14) | 4558736 |

**raw_map_alias_files file-size statistics:**

```
 min_bytes  max_bytes  avg_bytes  median_bytes
     61199      61206    61203.2       61206.0
```

**Distinct SHA1 versions (V4):** 2
**Distinct alias tournament dirs (V5):** 70

---

## 4. Version Distribution

```
                               byte_sha1  n_dirs
462d1337c5e2d9003e84ae07c63561612b03c40c      42
e1537d016c5cb4b66b9e21fc874b9b207c7e78c1      28
```

---

## 5. One-File-Per-Dir Invariant

V3 (n_rows) = 70, V5 (n_dirs) = 70
Invariant holds: **True**

---

## 6. Replay Table Parity

V9 (n_replays) = 22390, expected = 22390
Match: **True**

---

## 7. Tournament Dir Cross-Check

V5 (alias n_dirs) = 70, V10 (raw n_dirs) = 70
Match: **True**

---

## 8. Sample Rows

```
        tournament_dir                                byte_sha1  n_bytes  json_len
    2016_IEM_10_Taipei 462d1337c5e2d9003e84ae07c63561612b03c40c    61206     54310
  2016_IEM_11_Shanghai 462d1337c5e2d9003e84ae07c63561612b03c40c    61206     54310
       2016_WCS_Winter e1537d016c5cb4b66b9e21fc874b9b207c7e78c1    61199     54303
 2017_HomeStory_Cup_XV e1537d016c5cb4b66b9e21fc874b9b207c7e78c1    61199     54303
2017_HomeStory_Cup_XVI e1537d016c5cb4b66b9e21fc874b9b207c7e78c1    61199     54303
```

---

## 9. Appendix — SQL for Each Cell

**V1:**
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'main'
ORDER BY table_name
```

**V2:**
```sql
PRAGMA table_info('raw_map_alias_files')
```

**V3:**
```sql
SELECT COUNT(*) AS n_rows FROM raw_map_alias_files
```

**V4:**
```sql
SELECT COUNT(DISTINCT byte_sha1) AS n_versions FROM raw_map_alias_files
```

**V5:**
```sql
SELECT COUNT(DISTINCT tournament_dir) AS n_dirs FROM raw_map_alias_files
```

**V6:**
```sql
SELECT
    MIN(n_bytes)    AS min_bytes,
    MAX(n_bytes)    AS max_bytes,
    AVG(n_bytes)    AS avg_bytes,
    MEDIAN(n_bytes) AS median_bytes
FROM raw_map_alias_files
```

**V7:**
```sql
SELECT byte_sha1, COUNT(*) AS n_dirs
FROM raw_map_alias_files
GROUP BY byte_sha1
ORDER BY n_dirs DESC
```

**V8:**
```sql
SELECT
    tournament_dir,
    byte_sha1,
    n_bytes,
    LENGTH(raw_json) AS json_len
FROM raw_map_alias_files
LIMIT 5
```

**V9:**
```sql
SELECT COUNT(*) AS n_replays FROM raw
```

**V10:**
```sql
SELECT COUNT(DISTINCT split_part(filename, '/', -3)) AS n_dirs
FROM raw
```

**V11:**
```sql
SELECT COUNT(*) AS n_tracker_events FROM tracker_events_raw
```

**V12:**
```sql
SELECT COUNT(*) AS n_game_events FROM game_events_raw
```

**V13:**
```sql
SELECT COUNT(*) AS n_match_player_map FROM match_player_map
```

**V14:**
```sql
SELECT COUNT(*) AS n_player_stats FROM player_stats
```