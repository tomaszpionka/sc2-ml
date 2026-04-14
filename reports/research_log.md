# Research Log

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

This log contains CROSS-dataset entries only. Dataset-specific findings
live in per-dataset logs — one per game/dataset combination.

| Dataset | Log | Last entry |
|---------|-----|------------|
| sc2 / sc2egset | [sc2egset research log](../src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md) | 2026-04-14 (01_02_03) |
| aoe2 / aoe2companion | [aoe2companion research log](../src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md) | 2026-04-14 (01_02_03) |
| aoe2 / aoestats | [aoestats research log](../src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md) | 2026-04-14 (01_02_03) |

> **Phase migration note (2026-04-09):** This log was reset as part of the
> Phase 01-07 migration. Prior entries were removed in v2.0.0 (archive
> cleanup); historical context is preserved in git history.
> All new entries use the Phase XX / Step XX_YY_ZZ format per docs/PHASES.md.

---

## CROSS-Dataset Entries

---

## 2026-04-14 — [Phase 01 / Step 01_02_02] Invariant I10 fix: inline filename relativization

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
