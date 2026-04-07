# INVARIANTS — aoestats

## I1. Schema stability

- raw_matches: DRIFTED
- raw_players: DRIFTED

Type drift in raw_matches (column names stable, types changed):

- `raw_match_type`: DOUBLE → BIGINT

Type drift in raw_players (column names stable, types changed):

- `feudal_age_uptime`: DOUBLE → INTEGER
- `castle_age_uptime`: DOUBLE → INTEGER
- `imperial_age_uptime`: DOUBLE → INTEGER
- `profile_id`: DOUBLE → BIGINT
- `opening`: VARCHAR → INTEGER
  DuckDB `union_by_name = true` resolves drift to the widest compatible type.

Evidence: 00_02_match_schema_profile.md, 00_03_player_schema_profile.md

## I1a. Known download failures

One player file failed during acquisition (documented in manifest with
status='failed'). This is a known gap, not a silent corruption.

- `2025-11-16_2025-11-22_players.parquet`: missing_from_disk

## I5. Row-count totals at T_ingestion

- T_ingestion: 2026-04-07T16:36:52.108940+00:00
- raw_matches: 30,690,651 rows across 172 files
- raw_players: 107,627,584 rows across 171 files

## I6. Reconciliation result

- Strength: DEGRADED
- Reason: manifest does not record per-file row counts; reconciliation
  limited to file-count match.
- Additional: raw_players contains 171 files (1 known failed download).
- Note: 1 entries had status='failed' in manifest: 2025-11-16_2025-11-22_players.parquet — excluded from expected file count.

## I7. Provenance

Every raw table has a `filename` column populated by `filename = true` on
the source read. Removing or aliasing this column in any downstream view
is forbidden.