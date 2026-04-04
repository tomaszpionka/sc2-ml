---
paths:
  - "src/rts_predict/*/data/**/*.py"
---

# SQL & Data Pipeline Constraints

## Replay ID (canonical join key)
```sql
regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id
```
- Path A: extract from `filename`; Path B: extract from `match_id`
- ALL downstream tables use `replay_id` as FK to `raw`
- NEVER join on `filename` or `match_id` directly

## Tournament Identity
```sql
split_part(filename, '/', -3) AS tournament_dir
```
Validated Phase 0 Step 0.2 (50/50). Must be persistent column on `raw`.

## View Design
- Every view: comment block with purpose + row multiplicity
- Use `replay_id` as join key, `canonical_nickname` as player identifier
- `matches_flat` = TWO rows per game — always `COUNT(DISTINCT replay_id)`
- Create views ONLY after dependent tables are validated

## Temporal Discipline (mirrors Invariant #3)
- Features for game at time T use ONLY `match_time < T`
- NEVER `.shift()` on unsorted data
- Filter by sequence number or timestamp, NEVER by row position

## Data Handling
- NEVER silently drop rows — log count and reason
- Assert shapes and dtypes after every major transformation
- Use `pd.Categorical` for known-cardinality columns (race, matchup, result)
- When reading large files: specify `dtype` and `usecols` upfront
