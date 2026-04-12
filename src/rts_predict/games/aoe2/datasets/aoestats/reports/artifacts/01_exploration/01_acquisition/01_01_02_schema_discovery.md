# Step 01_01_02 — Schema Discovery: aoestats

**Phase:** 01 — Data Exploration  
**Pipeline Section:** 01_01 — Data Acquisition & Source Inventory  
**Dataset:** aoestats  
**Invariants applied:** #6, #7, #9  

## Sampling methodology

Full census for all file types.

| File type | Subdirectory | Files in dataset | Files checked | Method |
|-----------|-------------|-----------------|--------------|--------|
| Parquet | `matches/` | 172 | 172 | metadata-only (pyarrow.parquet.read_schema) |
| Parquet | `players/` | 171 | 171 | metadata-only (pyarrow.parquet.read_schema) |
| JSON | `overview/` | 1 | 1 | discover_json_schema (root keys) |

## matches/ schema (Parquet)

**Total columns:** 17  
**Schema consistency:** False  

| Column | Arrow type | Nullable |
|--------|-----------|----------|
| `map` | string | True |
| `started_timestamp` | timestamp[us, tz=UTC] | True |
| `duration` | duration[ns] | True |
| `irl_duration` | duration[ns] | True |
| `game_id` | string | True |
| `avg_elo` | double | True |
| `num_players` | int64 | True |
| `team_0_elo` | double | True |
| `team_1_elo` | double | True |
| `replay_enhanced` | bool | True |
| `leaderboard` | string | True |
| `mirror` | bool | True |
| `patch` | int64 | True |
| `raw_match_type` | double | True |
| `game_type` | string | True |
| `game_speed` | string | True |
| `starting_age` | string | True |

## players/ schema (Parquet)

**Total columns:** 13  
**Schema consistency:** False  

| Column | Arrow type | Nullable |
|--------|-----------|----------|
| `winner` | bool | True |
| `game_id` | string | True |
| `team` | int64 | True |
| `feudal_age_uptime` | double | True |
| `castle_age_uptime` | double | True |
| `imperial_age_uptime` | double | True |
| `old_rating` | int64 | True |
| `new_rating` | int64 | True |
| `match_rating_diff` | double | True |
| `replay_summary_raw` | string | True |
| `profile_id` | double | True |
| `civ` | string | True |
| `opening` | string | True |

## overview/ schema (JSON)

**Total root keys:** 8  

| Key | Observed types | Nullable | Frequency / Total |
|-----|----------------|----------|-------------------|
| `changelog` | list | False | 1 / 1 |
| `civs` | list | False | 1 / 1 |
| `groupings` | list | False | 1 / 1 |
| `last_updated` | str | False | 1 / 1 |
| `openings` | list | False | 1 / 1 |
| `patches` | list | False | 1 / 1 |
| `total_match_count` | int | False | 1 / 1 |
| `tournament_stages` | list | False | 1 / 1 |

## Cross-comparison: matches vs players column names

Comparison is raw string matching of column names only — no semantic interpretation.

| Metric | Count |
|--------|-------|
| Shared column names | 1 |
| matches-only column names | 16 |
| players-only column names | 12 |

**Shared column names:**

- `game_id`

**matches-only column names:**

- `avg_elo`
- `duration`
- `game_speed`
- `game_type`
- `irl_duration`
- `leaderboard`
- `map`
- `mirror`
- `num_players`
- `patch`
- `raw_match_type`
- `replay_enhanced`
- `started_timestamp`
- `starting_age`
- `team_0_elo`
- `team_1_elo`

**players-only column names:**

- `castle_age_uptime`
- `civ`
- `feudal_age_uptime`
- `imperial_age_uptime`
- `match_rating_diff`
- `new_rating`
- `old_rating`
- `opening`
- `profile_id`
- `replay_summary_raw`
- `team`
- `winner`

## Notes

- No DuckDB type proposals in this step (deferred to ingestion design).
- Step scope: `content` (file headers/schemas).
