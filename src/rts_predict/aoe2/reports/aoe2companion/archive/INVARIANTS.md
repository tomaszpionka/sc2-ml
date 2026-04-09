# INVARIANTS — aoe2companion

## I1. Schema stability

- raw_matches: STABLE
- raw_ratings: see 00_03_rating_schema_profile.md

Evidence: 00_02_match_schema_profile.md, 00_03_rating_schema_profile.md

## I2. Snapshot tables

- raw_leaderboard: T_snapshot = 2026-04-06T21:08:57.795793+00:00
- raw_profiles:    T_snapshot = 2026-04-06T21:09:07.822448+00:00

WARNING: these tables MUST NOT be joined to historical matches as if they
were time-varying. They reflect state at T_snapshot only. Any downstream
phase that joins them to a match must filter to matches occurring within
a documented epsilon of T_snapshot, or accept the join as approximate.

## I3. Sparse rating regime

- Boundary date: 2025-06-26
- File-size threshold: 1024 bytes
- Number of sparse files: 1791
- Date range: 2020-08-01..2025-06-26
- Source: 00_03_rating_schema_profile.md

## I4. Dtype strategy

- raw_ratings strategy: explicit
- Rationale: auto_detect inferred inconsistent types for columns: profile_id, games, rating, date, leaderboard_id, season, rating_diff. Explicit map derived from dense sample schema.
- Artifact: 00_03_dtype_decision.json

## I5. Row-count totals at T_ingestion

- T_ingestion: 2026-04-07T11:21:37.439190+00:00
- raw_matches:     277,099,059 rows across 2,073 files
- raw_ratings:     58,317,433 rows across 2,072 files (736 data-bearing, 1,336 zero-row sparse)
- raw_leaderboard: 2,381,227 rows
- raw_profiles:    3,609,686 rows

## I6. Reconciliation result

- Strength: DEGRADED
- Reason: manifest does not record per-file row counts; reconciliation
  limited to file-count match and zero-row rating file count.

## I7. Provenance

Every raw table has a `filename` column populated by `filename = true` on
the source read. Removing or aliasing this column in any downstream view
is forbidden.