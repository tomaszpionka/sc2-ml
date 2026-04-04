# Project Architecture

## Purpose of This Document

This document describes how the project **should be structured** as it is built
correctly from the data exploration outward. It is not a catalogue of existing
modules — existing code was written before proper data exploration and must be
treated as a draft to audit and revise, not as a correct implementation to extend.

When any existing module conflicts with guidance in this document or with
`.claude/scientific-invariants.md`, the guidance takes precedence over the code.

---

## Package Layout (`src/rts_predict/`)

See `ARCHITECTURE.md` at the repo root for the canonical structural guide and
the game extension protocol. This section gives the ordering constraints and
legacy code warnings needed for daily development.

### Intended structure
```
src/rts_predict/
├── __init__.py              # __version__ = "X.Y.Z" — single version location
├── sc2/                     # StarCraft II game package
│   ├── __init__.py          # game docstring only — NO __version__
│   ├── cli.py               # pipeline orchestrator and CLI subcommands
│   ├── config.py            # GAME_DIR, ROOT_DIR, REPORTS_DIR, path constants
│   ├── PHASE_STATUS.yaml    # machine-readable phase progress (read at session start)
│   ├── data/
│   │   ├── ingestion.py     # replay JSON → DuckDB raw table (Path A + Path B)
│   │   ├── processing.py    # SQL views: flat_players, matches_flat
│   │   ├── exploration.py   # data exploration functions, one per roadmap step
│   │   └── tests/
│   ├── features/
│   │   ├── __init__.py      # build_features() composable API
│   │   └── tests/
│   ├── models/
│   │   ├── baselines.py     # rule-based baselines (matchup win rate, recent form, H2H)
│   │   ├── classical.py     # LR, LightGBM, XGBoost training and evaluation
│   │   └── tests/
│   ├── analysis/
│   │   └── tests/
│   ├── gnn/                 # deprioritized — appendix only
│   ├── reports/             # SC2-specific phase artifacts (tracked in git)
│   │   └── SC2_THESIS_ROADMAP.md
│   ├── models/              # SC2 model artifacts (gitignored)
│   ├── logs/                # SC2 pipeline logs (gitignored)
│   └── tests/               # package-root tests (cli, validation)
├── aoe2/                    # AoE2 game package (placeholder)
│   ├── __init__.py
│   └── PHASE_STATUS.yaml
└── common/                  # Shared evaluation framework (future)
    ├── __init__.py
    └── CONTRACT.md
```

### Ordering constraint

Modules must only be written after the phase that justifies them is complete:

| Module | May be written after |
|--------|---------------------|
| `sc2/data/exploration.py` | Phase 0 gate (ingestion validated) |
| `sc2/data/processing.py` views | Phase 2 gate (canonical_players exists) |
| `sc2/features/` | Phase 7 (feature spec document exists) |
| `sc2/models/baselines.py` | Phase 9 |
| `sc2/models/classical.py` | Phase 9 gate (baselines evaluated) |
| `sc2/gnn/` | Phase 10, only if time permits |

---

## External Data Paths (from `config.py`)

- `~/duckdb_work/test_sc2.duckdb` — main DuckDB database
- `~/duckdb_work/tmp/` — DuckDB temp directory
- `~/Downloads/SC2_Replays/` — raw SC2Replay JSON files (read-only — never modify)

Source JSON files at `~/Downloads/SC2_Replays/` must never be modified during
exploration or ingestion work. See the ingestion warning below.

---

## Data Pipeline: Two Independent Paths

The ingestion pipeline has two paths that are independent and must run in a
specific order. Understanding this is required before touching any ingestion code.

### Path A — Pre-match metadata (header, players, map, game version)

`move_data_to_duck_db()` reads the top-level JSON fields from each replay file
and loads them into the DuckDB `raw` table. The `raw` table stores these fields
as JSON blobs: `header`, `initData`, `details`, `metadata`, `ToonPlayerDescMap`.

The `raw` table is the single source of truth for all pre-match information.

### Path B — In-game events (tracker events, game events)

`run_in_game_extraction()` reads the `trackerEvents` and `gameEvents` arrays from
each replay file using multiprocessing and writes them to Parquet files. These are
then loaded into DuckDB as `tracker_events_raw` and `game_events_raw`.

`tracker_events_raw` is the source of all in-game time-series data (`PlayerStats`,
`UnitBorn`, `UnitDied`, `Upgrade`, etc.).

### Ordering and the destructive slimming function

> ⛔ `slim_down_sc2_with_manifest(dry_run=False)` permanently deletes `trackerEvents`,
> `gameEvents`, and `messageEvents` from every source JSON file on disk. It must
> NEVER be called until Path B extraction is fully complete and all Parquet files
> are verified. The default `dry_run=True` is safe. Calling it prematurely destroys
> data that cannot be recovered without re-downloading the SC2EGSet ZIPs.

Correct execution order:
1. Run `audit_raw_data_availability()` — verify no files are already stripped
2. Run Path B: `run_in_game_extraction()` → `load_in_game_data_to_duckdb()`
3. Verify Parquet output is complete
4. Run Path A: `move_data_to_duck_db()`
5. Only then consider `slim_down_sc2_with_manifest()` — and only if disk space
   requires it, with the originals backed up

---

## Identifier Design: `replay_id` vs `match_id`

**Path A and Path B use different string formats to refer to the same replay file.
Joining them on raw strings will silently produce wrong results or zero matches.**

| Source | Column | Format |
|--------|--------|--------|
| Path A `raw` table | `filename` | Absolute path: `/Users/.../SC2_Replays/2016_IEM_10_Taipei/.../0e0b1a55...SC2Replay.json` |
| Path B `tracker_events_raw` | `match_id` | Relative path: `2016_IEM_10_Taipei/.../0e0b1a55...SC2Replay.json` |

The canonical `replay_id` is the 32-character MD5 hex prefix of the filename:
`0e0b1a550447f0b0a616e48224b31bd9`. Extract it identically from both sides before
joining:
```sql
-- From Path A filename column:
regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id

-- From Path B match_id column:
regexp_extract(match_id, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id
```

All downstream tables (`games`, `player_appearances`, `player_career_sequence`,
`player_stats_ts`, `unit_events`, `upgrade_events`) must use `replay_id` as their
join key to `raw`. Never join on `filename` or `match_id` directly.

---

## Tournament Identity: `tournament_dir`

The tournament a replay belongs to is encoded only in the filesystem path, not in any JSON field. The directory structure is:
```
~/Downloads/SC2_Replays/
2016_IEM_10_Taipei/
2016_IEM_10_Taipei_data/
0e0b1a55...SC2Replay.json
```

`tournament_dir` = `2016_IEM_10_Taipei` is extracted from `filename` using
`split_part(filename, '/', -3)`. This logic depends on the directory depth being
exactly as shown above. Validate it in Phase 0, Step 0.2 before relying on it.

`tournament_dir` must be added as a persistent column to the `raw` table (or to a
`raw_enriched` view) immediately after ingestion. It is the only tournament foreign
key available anywhere in the pipeline.

---

## SQL View Design Principles

Views are documentation as well as queries. Each view must:

- Have a comment block explaining its purpose and the multiplicity of its rows
- Use `replay_id` (not `filename` or `match_id`) as the join key to `raw`
- Use `canonical_nickname` (not raw toon strings) as the player identifier
- Be created only after the tables it depends on are validated

**Multiplicity to be aware of:**

`matches_flat` produces two rows per unique game (one per player perspective). This
is intentional. Any aggregation or deduplication must account for this. When counting
unique games, always `COUNT(DISTINCT replay_id)` or filter to `WHERE p1_name < p2_name`.

---

## Feature Engineering Principles

Feature code may not be written until `src/rts_predict/sc2/reports/07_feature_specification.md` exists
(produced in Phase 7 of the roadmap). That document defines which features are in
Group A (pre-game) and Group B (in-game) and which fields are confirmed dead.

All feature functions must:
- Accept a `target_game_id` and compute values using only events with
  `match_time < target_game.match_time`
- Use `player_canonical_id` as the player key, never raw toon or raw nickname
- Be testable for temporal leakage in isolation (see `.claude/testing-standards.md`)

The feature count and group composition are **unknown until data exploration is
complete**. Do not assume the legacy feature count of 66 across 5 groups is correct.
It was derived from code written without data exploration and may not reflect the
actual fields that carry signal in this dataset.

---

## Legacy Code: What Exists and What to Do With It

The repository contains modules written before proper data exploration. They may
contain incorrect assumptions, wrong split logic, or features derived from dead fields.

**Treat all of the following as drafts that require verification before use:**

| Module | Known issue |
|--------|-------------|
| `sc2/data/processing.py` → `create_temporal_split()` | Wrong split strategy. Superseded by Phase 8 per-player leave-last-tournament-out. Do not use for any thesis experiment. |
| `sc2/cli.py` → `run_pipeline()` | Calls the wrong split. Do not use until Phase 8 is complete. |
| `sc2/features/group_*.py` | Built without winner/loser separability analysis. Field selection unvalidated. Treat as a starting point, not ground truth. |
| `sc2/gnn/` | Known majority-class collapse. Deprioritized to appendix. Do not invest time until Phases 1–9 are complete. |
| `sc2/config.py` → `GLOBAL_TEST_SIZE` | Part of the old naive split. Not valid for thesis evaluation. |

**What this means in practice:** When the roadmap asks you to build a feature or a
view, write it from scratch guided by the roadmap specification and the exploration
findings. Check whether a legacy module covers the same ground. If it does, audit it
against the specification — do not extend it blindly.

---

## Directories

- `reports/` — cross-cutting research artifacts: `research_log.md` (tagged `[SC2]`/`[AoE2]`/`[CROSS]`)
- `src/rts_predict/sc2/reports/` — SC2-specific phase artifacts: roadmap, exploration outputs
- `src/rts_predict/sc2/reports/SC2_THESIS_ROADMAP.md` — authoritative SC2 execution plan
- `src/rts_predict/sc2/reports/archive/` — legacy pipeline execution logs (reference only)
- `src/rts_predict/sc2/logs/` — pipeline log file (`sc2_pipeline.log`, gitignored)
- `src/rts_predict/sc2/models/` — serialised model artifacts (written only in Phase 10, gitignored)
- `ARCHITECTURE.md` — canonical package layout, game extension guide (repo root)

---

## Known Platform Notes

- DuckDB configured for 24GB RAM, 4 threads (tuned for Apple M4 Max)
- LightGBM and PyTorch load conflicting OpenMP runtimes on macOS — classical model
  tests must run in subprocess isolation (`multiprocessing.spawn`)
- GNN training forces CPU explicitly due to MPS sparse tensor issues
- `PYTORCH_ENABLE_MPS_FALLBACK=1` is set in `~/.zshrc`