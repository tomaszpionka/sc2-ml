# Parquet↔DuckDB Schema Reconciliation (Step 1.9F-i)

## tracker_events_raw

Batches checked: 5

**Parquet schema:**

- `match_id:string`
- `event_type:string`
- `game_loop:int32`
- `player_id:int8`
- `event_data:string`

**DuckDB schema:**

- `match_id:VARCHAR`
- `event_type:VARCHAR`
- `game_loop:INTEGER`
- `player_id:TINYINT`
- `event_data:VARCHAR`

**No mismatches — schemas are consistent.**

## game_events_raw

Batches checked: 5

**Parquet schema:**

- `match_id:string`
- `event_type:string`
- `game_loop:int32`
- `user_id:int32`
- `player_id:int8`
- `event_data:string`

**DuckDB schema:**

- `match_id:VARCHAR`
- `event_type:VARCHAR`
- `game_loop:INTEGER`
- `user_id:INTEGER`
- `player_id:TINYINT`
- `event_data:VARCHAR`

**No mismatches — schemas are consistent.**

## Gate: PASS

Total mismatches across both tables: 0
