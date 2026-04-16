# Step 01_03_04 -- Event Table Profiling

**Dataset:** sc2egset
**Date:** 2026-04-15
**Predecessor:** 01_03_03 (Table Utility Assessment)
**Invariants:** I3, I6, I9

---

## Tracker Events (62,003,411 rows)

### Event type distribution

| Event Type | Count | % |
|-----------|------:|---:|
| UnitBorn | 22,372,489 | 36.0827 |
| UnitDied | 16,053,834 | 25.8919 |
| UnitTypeChange | 10,999,108 | 17.7395 |
| PlayerStats | 4,558,736 | 7.3524 |
| UnitInit | 3,151,270 | 5.0824 |
| UnitDone | 3,018,764 | 4.8687 |
| UnitPositions | 941,249 | 1.5181 |
| Upgrade | 797,987 | 1.2870 |
| UnitOwnerChange | 65,157 | 0.1051 |
| PlayerSetup | 44,817 | 0.0723 |

### Per-replay density

| Statistic | Value |
|-----------|------:|
| n_replays | 22390 |
| mean | 2769.2 |
| median | 1920.5 |
| p05 | 587.45 |
| p25 | 1147.0 |
| p75 | 3207.75 |
| p95 | 7703.649999999998 |
| min | 140 |
| max | 66984 |

### Event type coverage per replay

| Event Type | Replays | Coverage % | Total Events | Mean/Replay |
|-----------|--------:|-----------:|-------------:|-----------:|
| UnitBorn | 22,390 | 100.00 | 22,372,489 | 999.2 |
| UnitDied | 22,361 | 99.87 | 16,053,834 | 717.9 |
| UnitTypeChange | 22,281 | 99.51 | 10,999,108 | 493.7 |
| PlayerStats | 22,390 | 100.00 | 4,558,736 | 203.6 |
| UnitInit | 22,366 | 99.89 | 3,151,270 | 140.9 |
| UnitDone | 22,358 | 99.86 | 3,018,764 | 135.0 |
| UnitPositions | 22,345 | 99.80 | 941,249 | 42.1 |
| Upgrade | 22,385 | 99.98 | 797,987 | 35.6 |
| UnitOwnerChange | 5,684 | 25.39 | 65,157 | 11.5 |
| PlayerSetup | 22,390 | 100.00 | 44,817 | 2.0 |

### PlayerStats periodicity

- Mode gap: 0 loops (50.5756% of observations)
- Distinct gap values: 162
- Total gap observations: 4,536,346

### UnitBorn unit-type diversity

- Total distinct unit types: 232

Top 20 unit types by frequency:

| Unit Type | Count |
|-----------|------:|
| Larva | 3,899,335 |
| InvisibleTargetDummy | 2,803,987 |
| Zergling | 2,507,484 |
| Drone | 1,388,903 |
| Probe | 1,073,446 |
| Marine | 996,359 |
| SCV | 946,222 |
| MineralField | 837,605 |
| MineralField750 | 833,228 |
| Roach | 533,518 |
| Broodling | 456,249 |
| LabMineralField | 374,202 |
| LabMineralField750 | 374,084 |
| Baneling | 367,239 |
| VespeneGeyser | 334,491 |
| BroodlingEscort | 321,477 |
| Overlord | 321,027 |
| AdeptPhaseShift | 216,826 |
| SpacePlatformGeyser | 211,174 |
| Hydralisk | 185,643 |

### event_data JSON keys by type

- **UnitBorn:** controlPlayerId, evtTypeName, id, loop, unitTagIndex, unitTagRecycle, unitTypeName, upkeepPlayerId, x, y
- **UnitDied:** evtTypeName, id, killerPlayerId, killerUnitTagIndex, killerUnitTagRecycle, loop, unitTagIndex, unitTagRecycle, x, y
- **UnitTypeChange:** evtTypeName, id, loop, unitTagIndex, unitTagRecycle, unitTypeName
- **PlayerStats:** evtTypeName, id, loop, playerId, stats
- **UnitInit:** controlPlayerId, evtTypeName, id, loop, unitTagIndex, unitTagRecycle, unitTypeName, upkeepPlayerId, x, y

---

## Game Events (608,618,823 rows)

### Event type distribution

| Event Type | Count | % |
|-----------|------:|---:|
| CameraUpdate | 387,507,855 | 63.6700 |
| ControlGroupUpdate | 69,227,281 | 11.3745 |
| CommandManagerState | 43,946,635 | 7.2207 |
| SelectionDelta | 40,855,099 | 6.7128 |
| Cmd | 31,201,304 | 5.1266 |
| CmdUpdateTargetPoint | 25,863,707 | 4.2496 |
| CmdUpdateTargetUnit | 8,348,208 | 1.3717 |
| CameraSave | 1,027,659 | 0.1689 |
| TriggerMouseMoved | 380,197 | 0.0625 |
| UserOptions | 131,738 | 0.0216 |
| GameUserLeave | 70,032 | 0.0115 |
| TriggerDialogControl | 52,072 | 0.0086 |
| UnitClick | 2,187 | 0.0004 |
| AchievementAwarded | 1,495 | 0.0002 |
| DecrementGameTimeRemaining | 1,493 | 0.0002 |
| TriggerPing | 1,416 | 0.0002 |
| CommandManagerReset | 238 | 0.0000 |
| HijackReplayGame | 122 | 0.0000 |
| GameUserJoin | 25 | 0.0000 |
| Alliance | 24 | 0.0000 |
| AddAbsoluteGameSpeed | 24 | 0.0000 |
| TriggerTransmissionComplete | 8 | 0.0000 |
| ResourceTrade | 4 | 0.0000 |

CameraUpdate dominance: 63.6700%
Non-CameraUpdate events: 221,110,968

### Per-replay density (10% BERNOULLI sample)

- Sample method: CTE-based 10% filename sample
- Replays sampled: 22383
- Mean events/replay (sampled): 27191.1
- Median events/replay (sampled): 21910.0

Note: BERNOULLI samples rows, so per-replay counts are deflated (~10% of true per-replay totals).

### event_data JSON keys by type

- **Cmd:** abil, cmdFlags, data, evtTypeName, id, loop, otherUnit, sequence, unitGroup, userid
- **SelectionDelta:** controlGroupId, delta, evtTypeName, id, loop, userid

---

## Message Events (52,167 rows)

### Event type distribution

| Event Type | Count | % |
|-----------|------:|---:|
| Chat | 51,412 | 98.5527 |
| Ping | 714 | 1.3687 |
| ReconnectNotify | 41 | 0.0786 |

Replay coverage: 22260 / 22390 (99.42%)

### event_data JSON keys by type

- **Chat:** evtTypeName, id, loop, recipient, string, userid
- **Ping:** evtTypeName, id, loop, point, recipient, userid
- **ReconnectNotify:** evtTypeName, id, loop, status, userid

---

## SQL Queries (I6)

### tracker_type_distribution
```sql
SELECT evtTypeName, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 4) AS pct
FROM tracker_events_raw
GROUP BY evtTypeName ORDER BY cnt DESC
```

### tracker_per_replay_density
```sql
SELECT filename, COUNT(*) AS n_events
FROM tracker_events_raw GROUP BY filename
```

### tracker_per_replay_by_type
```sql
SELECT evtTypeName,
       COUNT(DISTINCT filename) AS n_replays,
       ROUND(100.0 * COUNT(DISTINCT filename) / 22390, 2)
         AS replay_coverage_pct,
       COUNT(*) AS total_events,
       ROUND(1.0 * COUNT(*) / COUNT(DISTINCT filename), 1)
         AS mean_per_replay
FROM tracker_events_raw GROUP BY evtTypeName ORDER BY total_events DESC
```

### tracker_temporal_distribution
```sql
SELECT (loop / 1000) * 1000 AS loop_bucket, COUNT(*) AS cnt
FROM tracker_events_raw GROUP BY loop_bucket ORDER BY loop_bucket
```

### tracker_event_data_sample_UnitBorn
```sql
SELECT event_data FROM tracker_events_raw WHERE evtTypeName = 'UnitBorn' LIMIT 5
```

### tracker_event_data_sample_UnitDied
```sql
SELECT event_data FROM tracker_events_raw WHERE evtTypeName = 'UnitDied' LIMIT 5
```

### tracker_event_data_sample_UnitTypeChange
```sql
SELECT event_data FROM tracker_events_raw WHERE evtTypeName = 'UnitTypeChange' LIMIT 5
```

### tracker_event_data_sample_PlayerStats
```sql
SELECT event_data FROM tracker_events_raw WHERE evtTypeName = 'PlayerStats' LIMIT 5
```

### tracker_event_data_sample_UnitInit
```sql
SELECT event_data FROM tracker_events_raw WHERE evtTypeName = 'UnitInit' LIMIT 5
```

### playerstats_periodicity
```sql
WITH ps AS (
    SELECT filename, loop,
           loop - LAG(loop) OVER (
               PARTITION BY filename ORDER BY loop
           ) AS gap
    FROM tracker_events_raw
    WHERE evtTypeName = 'PlayerStats'
)
SELECT gap, COUNT(*) AS cnt
FROM ps WHERE gap IS NOT NULL
GROUP BY gap ORDER BY cnt DESC
```

### unitborn_unit_types
```sql
SELECT json_extract_string(event_data, '$.unitTypeName') AS unit_type,
       COUNT(*) AS cnt
FROM tracker_events_raw
WHERE evtTypeName = 'UnitBorn'
GROUP BY unit_type ORDER BY cnt DESC LIMIT 50
```

### unitborn_distinct_count
```sql
SELECT COUNT(DISTINCT
    json_extract_string(event_data, '$.unitTypeName')
) AS n_distinct
FROM tracker_events_raw
WHERE evtTypeName = 'UnitBorn'
```

### game_type_distribution
```sql
SELECT evtTypeName, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 4) AS pct
FROM game_events_raw GROUP BY evtTypeName ORDER BY cnt DESC
```

### game_per_replay_density_sample
```sql
SELECT filename, COUNT(*) AS n_events
FROM game_events_raw TABLESAMPLE BERNOULLI(10)
GROUP BY filename
```

### game_per_replay_density_fallback
```sql
WITH sample_files AS (
        SELECT DISTINCT filename FROM game_events_raw
        USING SAMPLE 10 PERCENT (bernoulli)
    )
    SELECT g.filename, COUNT(*) AS n_events
    FROM game_events_raw g
    INNER JOIN sample_files s ON g.filename = s.filename
    GROUP BY g.filename
```

### game_event_data_sample_Cmd
```sql
SELECT event_data FROM game_events_raw WHERE evtTypeName = 'Cmd' LIMIT 5
```

### game_event_data_sample_SelectionDelta
```sql
SELECT event_data FROM game_events_raw WHERE evtTypeName = 'SelectionDelta' LIMIT 5
```

### message_type_distribution
```sql
SELECT evtTypeName, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 4) AS pct
FROM message_events_raw GROUP BY evtTypeName ORDER BY cnt DESC
```

### message_replay_coverage
```sql
SELECT COUNT(DISTINCT filename) AS n_replays
FROM message_events_raw
```

### message_event_data_sample
```sql
SELECT evtTypeName, event_data
FROM message_events_raw LIMIT 10
```

### message_event_data_sample_Chat
```sql
SELECT event_data FROM message_events_raw WHERE evtTypeName = 'Chat' LIMIT 5
```

### message_event_data_sample_Ping
```sql
SELECT event_data FROM message_events_raw WHERE evtTypeName = 'Ping' LIMIT 5
```

### message_event_data_sample_ReconnectNotify
```sql
SELECT event_data FROM message_events_raw WHERE evtTypeName = 'ReconnectNotify' LIMIT 5
```

