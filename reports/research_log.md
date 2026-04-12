# Research Log

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

This log contains CROSS-dataset entries only. Dataset-specific findings
live in per-dataset logs — one per game/dataset combination.

| Dataset | Log | Last entry |
|---------|-----|------------|
| sc2 / sc2egset | [sc2egset research log](../src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md) | 2026-04-12 (01_01_02) |
| aoe2 / aoe2companion | [aoe2companion research log](../src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md) | 2026-04-12 (01_01_02) |
| aoe2 / aoestats | [aoestats research log](../src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md) | 2026-04-12 (01_01_02) |

> **Phase migration note (2026-04-09):** This log was reset as part of the
> Phase 01-07 migration. Prior entries were removed in v2.0.0 (archive
> cleanup); historical context is preserved in git history.
> All new entries use the Phase XX / Step XX_YY_ZZ format per docs/PHASES.md.

---

## CROSS-Dataset Entries

## 2026-04-12 — [CROSS / Phase 01 / Step 01_01_02] Schema Discovery Structural Summary

**Category:** A (science)
**Datasets:** sc2egset, aoe2companion, aoestats

Structural comparison across all 3 datasets following Step 01_01_02 completion.

**File formats per dataset:**

| Dataset | File types |
|---------|-----------|
| sc2egset | JSON only |
| aoe2companion | Parquet, CSV |
| aoestats | Parquet, JSON |

**Column counts per file type:**

| Dataset | File type | Subdirectory | Columns |
|---------|-----------|-------------|---------|
| sc2egset | JSON | TOURNAMENT_data | 11 root keys |
| aoe2companion | Parquet | matches/ | 54 |
| aoe2companion | CSV | ratings/ | 7 |
| aoe2companion | Parquet | leaderboards/ | 18 |
| aoe2companion | Parquet | profiles/ | 13 |
| aoestats | Parquet | matches/ | 17 |
| aoestats | Parquet | players/ | 13 |
| aoestats | JSON | overview/ | 8 root keys |

**Nesting depth per file type:**

| Dataset | File type | Nesting depth |
|---------|-----------|---------------|
| sc2egset | JSON | 5 |
| aoe2companion | Parquet | 0 (flat) |
| aoe2companion | CSV | 0 (flat) |
| aoestats | Parquet | 0 (flat) |
| aoestats | JSON | 1 |

**Column name overlap across datasets (raw string comparison):**

Exact column name matches across all file types (literal string equality only):

- `sc2egset` (11 root keys) vs `aoe2companion` (all file types): 0 shared column names
- `sc2egset` (11 root keys) vs `aoestats` (all file types): 0 shared column names
- `aoe2companion` (all file types) vs `aoestats` (all file types): 5 shared column names — `civ`, `leaderboard`, `map`, `profile_id`, `team`

Per-subdirectory breakdown:
- `aoe2companion/matches/` vs `aoestats/matches/`: 2 shared — `leaderboard`, `map`
- `aoe2companion/matches/` vs `aoestats/players/`: 2 shared — `civ`, `team`
- `aoe2companion/ratings/` vs `aoestats/players/`: 1 shared — `profile_id`

Per-dataset entries:
- [sc2egset](../src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md)
- [aoe2companion](../src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md)
- [aoestats](../src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md)

---

## 2026-04-12 — [CROSS / Phase 01 / Step 01_01_01] File Inventory Summary

**Category:** A (phase work — rerun)
**Datasets:** sc2egset, aoe2companion, aoestats

Step 01_01_01 file inventory rerun completed for all 3 datasets.
Context leaks stripped, research log entries rewritten from artifacts.
ROADMAP source data sections, raw/README.md, and reports/README.md
repopulated strictly from 01_01_01 artifacts per Invariant #9.
Per-dataset findings in each dataset's research_log.md.

Per-dataset entries:
- [sc2egset](../src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md)
- [aoe2companion](../src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md)
- [aoestats](../src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md)
