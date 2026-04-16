# Research Log

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

This log contains CROSS-dataset entries only. Dataset-specific findings
live in per-dataset logs — one per game/dataset combination.

| Dataset | Log | Last entry |
|---------|-----|------------|
| sc2 / sc2egset | [sc2egset research log](../src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md) | 2026-04-16 (01_04_00) |
| aoe2 / aoe2companion | [aoe2companion research log](../src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md) | 2026-04-16 (01_04_00) |
| aoe2 / aoestats | [aoestats research log](../src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md) | 2026-04-16 (01_04_00) |

---

## [CROSS] 2026-04-16 — [Phase 01 / Step 01_04_00] Canonical long skeleton normalization

Schema: 10 columns (match_id, started_timestamp, side, player_id,
chosen_civ_or_race, outcome_raw, rating_pre_raw, map_id_raw, patch_raw, leaderboard_raw)

All three datasets now expose a structurally identical long skeleton VIEW (`matches_long_raw`).
Downstream cleaning in all datasets operates against this common 10-column contract.

  - **aoe2companion:** 277,099,059 rows (lossless from matches_raw).
    Full dataset: side=0 449 rows win_pct=4.45% (source encoding artifact; team=0 is not a 1v1 side).
    side=1 win_pct=49.58%.
    1v1 scoped (leaderboard_raw IN (6, 18)): side=0 29,921,254 rows win_pct=47.18%;
    side=1 29,920,914 rows win_pct=52.81%. ~5pp slot asymmetry documented, deferred to Phase 02.
    leaderboard_raw = internalLeaderboardId (INTEGER); 1v1 values: 6 (rm_1v1), 18 (qp_rm_1v1).
    patch_raw = NULL (no patch column in source).

  - **aoestats:** 107,626,399 rows (lossless via independent anchor: 107,627,584 - 1,185 null_profile - 0 orphans).
    side 0 win_pct = 48.97% (53,813,160 rows).
    side 1 win_pct = 51.03% (53,813,239 rows).
    1v1 scoped (leaderboard_raw = 'random_map'): side 0 win_pct = 47.73%, side 1 win_pct = 52.27%.
    Known asymmetry from 01_04_01 confirmed.
    leaderboard_raw = leaderboard (VARCHAR); 1v1 value: 'random_map'.

  - **sc2egset:** 44,817 rows (lossless JOIN count).
    side 0 win_pct = 51.96% (22,390 rows, 13 null outcome).
    side 1 win_pct = 47.97% (22,387 rows, 13 null outcome).
    Mild asymmetry (3.99pp deviation, below 10pp alert threshold). Documented, not corrected.
    leaderboard_raw = NULL (tournament data, no matchmaking ladder).
    started_timestamp type = VARCHAR (details.timeUTC); type unification deferred to Phase 02.

> **Phase migration note (2026-04-09):** This log was reset as part of the
> Phase 01-07 migration. Prior entries were removed in v2.0.0 (archive
> cleanup); historical context is preserved in git history.
> All new entries use the Phase XX / Step XX_YY_ZZ format per docs/PHASES.md.

---

## CROSS-Dataset Entries

---

## 2026-04-15 -- [CROSS] [Phase 01 / Step 01_03_04] In-game event data asymmetry

**Datasets affected:** sc2egset (has event data), aoe2companion and aoestats (no equivalent)

SC2EGSet provides three in-game event streams: tracker_events_raw (62M rows,
10 types), game_events_raw (608M rows, 23 types), message_events_raw (52K rows,
3 types). Deep profiling confirms PlayerStats fires at a 160-loop periodic
interval (per player), UnitBorn spans 232 distinct unit types, and Cmd/SelectionDelta
carry structured action data.

Neither AoE2 dataset has in-game event logs. This asymmetry is the controlled
experimental variable for Invariant #8: "Do the same methods work equally well
with and without in-game data?" Pre-game feature sets can be compared directly;
SC2 additionally enables in-game feature comparison.

---

## 2026-04-14 -- [Phase 01 / Step 01_02_02] Invariant I10 fix: inline filename relativization

**Datasets affected:** aoe2companion, aoestats (sc2egset was already correct)

### What

Both AoE2 dataset ingestion modules (`ingestion.py`) were storing absolute file paths in the `filename` provenance column, violating Invariant I10. The fix was applied to all CTAS and INSERT queries by replacing `SELECT *` with `SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)`, where `prefix_len = len(str(raw_dir)) + 2`.

### Why this approach

The original fix used a post-load `UPDATE SET filename = substr(filename, prefix_len)`. This caused `OutOfMemoryException` on aoestats `players_raw` (107.6M rows) and would have done the same on aoe2companion `matches_raw` (277M rows). Moving the transformation inline into the SELECT means DuckDB writes relative paths on the first pass — no second pass over the full table.

sc2egset already handled this correctly via explicit `substr(filename, {prefix_len}) AS filename` in its column list (it cannot use `SELECT *` due to its custom schema).

### Protocol decision (applies to all future datasets)

**Never use a post-load UPDATE to relativize filenames.** Always use `SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)` inline in the CTAS/INSERT query. This is the canonical I10 implementation for AoE2 ingestion going forward.

### Additional fix: aoestats OOM (file-level batching)

aoestats `load_matches_raw` and `load_players_raw` now load in file-level batches (default `batch_size=10`): `CREATE TABLE ... AS SELECT` for the first batch, `INSERT INTO ... BY NAME SELECT` for subsequent batches. This mirrors the per-tournament batching sc2egset uses for `replays_meta_raw`. Peak RSS stays manageable regardless of total file count.

### Additional fix: aoestats table rename

aoestats tables were renamed from `raw_matches`/`raw_players`/`raw_overviews` → `matches_raw`/`players_raw`/`overviews_raw` to align with the `*_raw` suffix convention used across all datasets.

### References

- aoestats ingestion: `src/rts_predict/games/aoe2/datasets/aoestats/ingestion.py`
- aoe2companion ingestion: `src/rts_predict/games/aoe2/datasets/aoe2companion/ingestion.py`
- Per-dataset entries: aoestats 01_02_02, aoe2companion 01_02_02
