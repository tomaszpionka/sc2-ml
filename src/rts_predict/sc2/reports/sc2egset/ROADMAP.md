# SC2EGSet Dataset Roadmap — Phases 0–2

**Scope:** Dataset-specific exploration, profiling, and player identity resolution
for the SC2EGSet v2.1.0 dataset.

**Game-level roadmap (Phases 3–10):** `../ROADMAP.md`

---

# SC2ML Thesis — Data Pipeline & Exploration Roadmap (v2)

**Goal:** Win/loss prediction in professional StarCraft II 1v1 matches using pre-game context and (optionally) in-game time-series data  
**Dataset:** SC2EGSet v2.1.0 — 70+ tournaments, ~22 000 replays, 2016–2024  
**Citation:** Białecki, A. et al. (2023). *SC2EGSet: StarCraft II Esport Replay and Game-state Dataset.* Scientific Data 10(1), 600. https://doi.org/10.1038/s41597-023-02510-7 — version 2.1.0 from Zenodo: https://zenodo.org/records/17829625  
**Stack:** DuckDB · Python · pandas · PyArrow · scikit-learn · PyTorch (later phases)  
**Rule:** Every phase ends with mandatory artifacts. Claude Code must not advance to the next phase until all artifacts exist and the gate condition is explicitly met. Each phase maps to a thesis chapter section (see `THESIS_STRUCTURE.md`).

---

## How to use this document

Hand Claude Code **one phase at a time**. Each phase specifies:

- **Context** — what the phase is about and why it comes here
- **Inputs** — what must already exist before starting
- **Steps** — discrete, ordered tasks to execute
- **Artifacts** — files that must be created before moving on
- **Gate** — the explicit condition that unlocks the next phase
- **Thesis mapping** — which thesis section this phase feeds

Do not skip phases. Do not let Claude Code jump to feature engineering before data exploration is complete.

**Cross-references:** This roadmap covers the SC2EGSet dataset leg (Phases 0–2). The game-level pipeline (Phases 3–10) is in `../ROADMAP.md`. The AoE2 leg will have a parallel roadmap. Both feed into the unified thesis structure in `THESIS_STRUCTURE.md`. The scientific invariants in `scientific-invariants.md` apply at all times.

---

## Reference: SC2 game loop timing

All duration conversions in this roadmap use the following formula, derived from
Blizzard's s2client-proto documentation, Vinyals et al. (2017, arXiv:1708.04782),
and Liquipedia's Game Speed article:

- The SC2 engine runs at **16 game loops per game-second** (Normal speed).
- All competitive play uses **Faster** speed with a **1.4× multiplier**.
- Therefore: **22.4 game loops = 1 real-time second** at competitive speed.
- Conversion: `real_time_seconds = game_loops / 22.4`
- Conversion: `real_time_minutes = game_loops / 22.4 / 60`
- The field `elapsedGameLoops` in replay metadata counts loops at the engine rate.

The older formula `game_loops / 16.0 / 60.0` produces **game-minutes** (internal
engine time), not real-time minutes. Both representations are valid but must be
clearly labelled. This roadmap uses **real-time minutes** unless explicitly noted.

| Landmark | Game loops | Real-time |
|----------|-----------|-----------|
| 1 minute | 1,344 | 60s |
| 3 minutes | 4,032 | 180s |
| 5 minutes | 6,720 | 300s |
| 7 minutes | 9,408 | 420s |
| 10 minutes | 13,440 | 600s |
| 20 minutes | 26,880 | 1200s |

---

## Phase 0 — Ingestion audit and raw table design ✅ COMPLETE

**Context:** An ingestion pipeline exists (`ingestion.py`). It has two paths: Path A loads slimmed JSON into a DuckDB `raw` table (header, initData, details, metadata, ToonPlayerDescMap); Path B extracts tracker/game events to Parquet. Before running anything, audit both paths for correctness, missing fields, and schema problems. Fix issues before any data is loaded.

**Critical known issues to verify and fix:**

1. **`tournament_dir` is missing from the raw table.** `move_data_to_duck_db` uses `filename` (the full filesystem path) but does not extract the parent tournament directory name (e.g. `2016_IEM_10_Taipei`) as a standalone column. The `flat_players` view in `processing.py` derives `tournament_name` via `split_part(filename, '/', -3)` — this is fragile and depends on the exact directory depth. It must be validated against real paths and potentially replaced with a more robust extraction.

2. **`slim_down_sc2_with_manifest` irreversibly destroys `trackerEvents`, `gameEvents`, and `messageEvents` from the source JSON files.** This must NEVER be run with `dry_run=False` before Path B extraction is complete. Audit the manifest to determine if any files have already been stripped.

3. **`match_id` in Path B is the full relative path string**, e.g. `2016_IEM_10_Taipei/2016_IEM_10_Taipei_data/0e0b1a...SC2Replay.json`. In Path A it is the full absolute filesystem path from DuckDB's `filename` column. These two identifiers are different formats and must be reconciled into a single canonical `replay_id` (the MD5 hash prefix, e.g. `0e0b1a550447f0b0a616e48224b31bd9`) before any join between Path A and Path B tables is possible.

4. **`APM` and `MMR` in `ToonPlayerDescMap` are likely all zeros** across the full corpus (confirmed in sample file). Verify this before building any feature that references these fields.

5. **`create_temporal_split` in `processing.py` uses a naïve global time-based split** — it assigns whole tournaments to train/val/test by chronological order of earliest match. This is a reasonable starting point for ingestion validation, but it does NOT implement the correct per-player sliding-window framing discussed in the thesis design. It will need to be replaced in Phase 6.

**Inputs:** Source JSON files on disk at `REPLAYS_SOURCE_DIR`. Existing `ingestion.py`, `processing.py`, `cli.py`.

### Steps

**0.1 — Audit source file availability**

Run `audit_raw_data_availability()` from `ingestion.py`. Record:
- Total `.SC2Replay.json` files on disk
- Files with `trackerEvents` present (`has_tracker`)
- Files with `gameEvents` present (`has_game`)
- Files with both present (`has_both`)
- Files already stripped (`stripped`)

If `stripped > 0`, stop. Do not proceed until it is confirmed which files were stripped and whether the original data can be recovered from the SC2EGSet ZIPs.

Output: `00_01_source_audit.json`

**0.2 — Validate the `tournament_name` extraction logic**

Before loading any data, write a standalone Python script that:
- Scans 10 random `.SC2Replay.json` paths from each of 5 different tournament directories
- Applies `split_part(filename, '/', -3)` (simulated in Python as `path.parts[-3]`)
- Compares the result to the known tournament directory name
- Reports whether the extraction is correct for all sampled paths

If it fails for any path, fix the extraction logic in `processing.py` before proceeding.

Output: `00_02_tournament_name_validation.txt`

**0.3 — Design and document the canonical `replay_id`**

Write a specification (a short markdown file) that defines:
- `replay_id` = the MD5 hash portion of the filename (the 32-character hex prefix before `.SC2Replay.json`)
- How to extract it from Path A's `filename` column (regex or string split)
- How to extract it from Path B's `match_id` column (the path string)
- Confirm both extractions produce identical values for the same file

This spec will be referenced by all downstream join logic.

Output: `00_03_replay_id_spec.md`

**0.4 — Run Path A ingestion on a single tournament**

Run `move_data_to_duck_db` on a single tournament directory (e.g. `2016_IEM_10_Taipei`) as a smoke test. Then:
- Run `DESCRIBE raw` and record all column names and types
- Run `SELECT COUNT(*) FROM raw` and compare to the file count on disk for that tournament
- Verify `filename`, `header`, `initData`, `details`, `metadata`, `ToonPlayerDescMap` are all present and non-null
- Extract `tournament_name` using the validated logic from 0.2
- Extract `replay_id` using the spec from 0.3
- Spot-check 3 rows manually against the source JSON files

Output: `00_04_path_a_smoke_test.md`

**0.5 — Run Path A ingestion on the full corpus**

Run `move_data_to_duck_db` with `should_drop=True` on the full `REPLAYS_SOURCE_DIR`. Record:
- Total rows loaded into `raw`
- Time taken
- Any errors logged

Output: `00_05_full_ingestion_log.txt` (the pipeline log)

**0.6 — Add `tournament_dir` and `replay_id` as persistent columns**

After ingestion, add two derived columns to the `raw` table (or create a `raw_enriched` view that all downstream queries use):
- `tournament_dir` — extracted from `filename` using the validated logic
- `replay_id` — the MD5 hash extracted from `filename`

These two columns are the primary keys for all downstream work. Never rely on the raw `filename` string again after this point.

**0.7 — Run Path B extraction**

Run `run_in_game_extraction()` on the full corpus. This is the slow step (multiprocessing over ~17 930 files). Record:
- Total files extracted
- Total skipped (no `trackerEvents`)
- Number of Parquet batch files written
- Time taken

Then run `load_in_game_data_to_duckdb()` to load Parquet into DuckDB.

Output: `00_07_path_b_extraction_log.txt`

**0.8 — Validate the Path A / Path B join**

Write a query that joins `raw` (Path A) to `tracker_events_raw` (Path B) on the canonical `replay_id`. Verify:
- Every `replay_id` in `tracker_events_raw` exists in `raw`
- Every `replay_id` in `raw` that has `trackerEvents` (from the audit in 0.1) has a corresponding row in `tracker_events_raw`
- Report any orphan `replay_id` values in either direction

Output: `00_08_join_validation.md`

**0.9 — Run `load_map_translations` and verify**

Run `load_map_translations()`. Then:
- Count rows in `map_translation`
- Count distinct `metadata->>'$.mapName'` values in `raw`
- Count how many map names from `raw` have no translation (null join)
- List the untranslated map names

Output: `00_09_map_translation_coverage.csv`

### Artifacts

- `00_01_source_audit.json`
- `00_02_tournament_name_validation.txt`
- `00_03_replay_id_spec.md`
- `00_04_path_a_smoke_test.md`
- `00_05_full_ingestion_log.txt`
- `00_07_path_b_extraction_log.txt`
- `00_08_join_validation.md`
- `00_09_map_translation_coverage.csv`

### Gate

- `raw` table exists with correct row count
- `tracker_events_raw` table exists and joins cleanly to `raw` via `replay_id`
- `tournament_dir` and `replay_id` are reliably extractable from all rows
- Zero stripped source files (or a documented recovery plan)
- `APM`/`MMR` zero-rate verified

**Status:** All gate conditions met (see `research_log.md`, entry 2026-04-03).

**Summary of results:**
- 22,390 source files, 0 stripped
- `raw` table: 22,390 rows
- `tracker_events_raw`: 62M rows, joins cleanly (0 orphans)
- `game_events_raw`: 609M rows
- `match_player_map`: 44,815 rows
- `raw_enriched` view with `tournament_dir` and `replay_id`
- 188 maps, 100% translation coverage
- APM: 97.5% non-zero (usable from 2017+; all 2016 = zero)
- MMR: 83.6% zero (systematically missing, unusable as direct feature)

**Thesis mapping:** Appendix A — Data acquisition and preprocessing infrastructure

---

## Phase 1 — Corpus inventory and parse quality
 
**Context:** Before exploring any values, establish the total scope and health of the dataset. This phase is read-only — no cleaning decisions are made yet, only observations recorded. The output of this phase is the factual foundation for the Data chapter of the thesis.
 
Phase 0 confirmed the plumbing works: tables load, joins have zero orphans, counts match. Phase 1 opens the box and looks *inside* the data values. Every finding here is an observation, not a decision — cleaning decisions are deferred to Phase 6.
 
**Inputs:** `raw` table, `tracker_events_raw` table, `game_events_raw` table, `match_player_map` table, `map_translation` table. All from Phase 0.
 
### Steps
 
**1.1 — Overall corpus counts and structural validation**
 
Write DuckDB queries producing:
 
**A) Basic corpus dimensions:**
- Total replays in `raw`
- Total tournaments (distinct `tournament_dir`)
- Date range: `MIN` and `MAX` of `(details->>'$.timeUTC')::TIMESTAMP`
- Replays with null `match_time`
- Replays with `tracker_events_raw` entries (`has_events`)
- Replays without any tracker events (`missing_events`)
 
**B) Player count per replay:**
Phase 0 found `match_player_map` has 44,815 rows for 22,390 replays — a ratio
of ~2.003, which is approximately but not exactly 2 per game. Compute:
- Distribution of player count per replay (group `match_player_map` by `match_id`, count players)
- Count of replays with exactly 2 players (expected: the vast majority)
- Count of replays with 1 player (corrupted parse?)
- Count of replays with 3+ players (observers, casters, team games leaked into corpus?)
- List the anomalous replays (≠ 2 players) with their `replay_id` and `tournament_dir`
 
This directly feeds cleaning Rule R3 in Phase 6.
 
**C) Result field completeness:**
From `ToonPlayerDescMap`, extract the `result` field for every player slot. Compute:
- Distinct `result` values and their counts (expected: mostly "Win" and "Loss")
- Count of player slots with null result
- Count of player slots with values other than "Win" or "Loss" (e.g. "Undecided", empty string)
- Count of replays where neither player has result = "Win" (no winner determinable)
- Count of replays where both players have result = "Win" (data error)
 
This directly feeds cleaning Rule R4 in Phase 6.
 
**D) Duplicate replay detection:**
Tournament packs can overlap — the same replay might appear in two different
tournament directories. Check:
- Count of distinct `replay_id` values vs. total rows in `raw` — any difference means duplicates
- If duplicates exist: list them with both `tournament_dir` values
- Also check for near-duplicates: same (player_a_name, player_b_name, map_name) with
  `match_time` within 60 seconds but different `replay_id` — these might be the same
  game captured from different players' perspectives or re-uploaded
 
**Note on short games:** Do NOT apply any hardcoded duration filter at this stage.
Step 1.3 will produce the empirical duration distribution, from which a data-driven
threshold will be derived in Phase 6. Counting games below arbitrary cutoffs is
premature and introduces unjustified magic numbers.
 
Output: `01_01_corpus_summary.json`
Output: `01_01_player_count_anomalies.csv` (if any anomalies found)
Output: `01_01_result_field_audit.md`
Output: `01_01_duplicate_detection.md`
 
**1.2 — Per-tournament parse quality table**
 
For each tournament (grouped by `tournament_dir`), compute:
- `total_replays` — rows in `raw`
- `has_events` — count with at least one row in `tracker_events_raw`
- `missing_events` — count without any tracker events
- `null_timestamp` — count with null `match_time`
- `event_coverage_pct` — `has_events / total_replays * 100`
- `player_count_anomalies` — count of replays in that tournament with ≠ 2 players (from 1.1B)
- `result_anomalies` — count of replays with missing or invalid result fields (from 1.1C)
 
Cross-reference with `*_processed_failed.log` counts per tournament if accessible.
 
Sort by `event_coverage_pct` ascending — worst coverage first.
 
Output: `01_02_parse_quality_by_tournament.csv`
Output: `01_02_parse_quality_summary.md` (narrative: which tournaments have >20%
missing events, which have structural anomalies, which to potentially flag for exclusion)
 
**1.3 — Game duration distribution**
 
This step produces the empirical foundation for all duration-based decisions
in later phases. Both time representations must be computed and clearly labelled.
 
Convert `elapsedGameLoops` to both time scales:
- **Real-time minutes:** `elapsedGameLoops / 22.4 / 60.0` (Faster speed: 22.4 loops/s;
  see Reference section at top of roadmap)
- **Game-time minutes:** `elapsedGameLoops / 16.0 / 60.0` (engine-internal time;
  1.4× longer than real-time)
 
Report which conversion is used in all downstream artefacts.
 
Produce:
- Histogram data: bin edges and counts, binned at 1-minute real-time intervals from 0 to 60 minutes
- Summary statistics: mean, median, p1, p5, p10, p25, p75, p90, p95, p99 overall
- The same statistics grouped by year (extracted from `match_time`)
- **Left-tail focus:** a zoomed histogram of games under 10 real-time minutes,
  binned at 30-second intervals, to reveal the structure of the short-game tail.
  Annotate known SC2 game-play landmarks in the plot:
  - ~2 min: earliest possible worker rush resolution
  - ~3–5 min: typical cheese/cannon rush resolution (cite: Liquipedia Cheese article)
  - ~7 min: MSC dataset minimum threshold (Wu et al. 2017, arXiv:1710.03131)
  - ~9 min: SC2EGSet experimental minimum (Białecki et al. 2023, §4)
 
This histogram will be used in Phase 6 to choose a data-driven minimum duration
threshold. The threshold is NOT chosen here — only the distribution is observed.
 
Save histogram data as CSV and render as matplotlib PNGs (full range + zoomed).
 
Output: `01_03_duration_distribution.csv`
Output: `01_03_duration_distribution_full.png`
Output: `01_03_duration_distribution_short_tail.png`
 
**1.4 — APM and MMR audit (confirmation of Phase 0 findings)**
 
Phase 0 already established:
- APM: 97.5% non-zero overall; all 2016 zeros, near-complete from 2017+
- MMR: 83.6% zero; systematically missing (tournament/lobby replays)
 
This step produces the formal report with year-by-year and league-by-league
breakdowns, suitable for thesis citation. Use the exact queries from
`research_log.md` Phase 0 entry.
 
Write `01_04_apm_mmr_audit.md` with:
- The full year-by-year APM table
- The full year-by-year MMR table
- The MMR-by-highestLeague table
- Conclusion: APM is usable from 2017+ (with 2016 imputation needed);
  MMR is NOT usable as a direct feature — player skill must be derived
  from match history (Elo, Glicko-2, or rolling win rate)
 
Output: `01_04_apm_mmr_audit.md`
 
**1.5 — Game version and patch landscape**
 
From `raw`, extract `metadata->>'$.gameVersion'` and `metadata->>'$.dataBuild'`.
 
Produce a table with:
- Distinct `game_version` values
- Count of replays per version
- Date range (min/max `match_time`) per version
 
Group versions by year and identify broad patch eras. SC2 timeline reference:
- 2015-11: Legacy of the Void launch (patch 3.0)
- 2016-11: Patch 3.8 (design revamp)
- 2017-11: Patch 4.0 (free-to-play transition)
- 2019-11: Patch 4.11 (major balance update)
- 2020-10: Final major balance patch
- 2021+: Maintenance mode (no major balance changes)
 
These eras may serve as a control feature (Phase 5 decision).
 
Output: `01_05_patch_landscape.csv`
 
**1.6 — Tracker event type inventory (stratified)**
 
This step goes beyond a corpus-wide summary. A single average can mask temporal
or tournament-level variation that would affect downstream feature extraction.
 
**A) Corpus-wide summary:**
From `tracker_events_raw`, count rows by `event_type` across the full corpus:
- `PlayerStats` — economy time series (expected: most frequent)
- `UnitBorn` — unit production
- `UnitDied` — combat losses
- `UnitInit` / `UnitDone` — units under construction
- `Upgrade` — tech research
- `PlayerSetup` — player identity confirmation
- Any other event types present (list them — there may be types not anticipated)
 
Compute: total rows per type, average count per replay, median count per replay.
 
**B) Per-replay event count distribution:**
For each event type, compute the distribution of counts per replay:
- min, p5, p25, median, p75, p95, max
- Flag replays with zero events of a given type (e.g., a replay with zero
  `PlayerStats` events is effectively unusable for in-game features)
- Count of replays with zero `PlayerStats` events — these should be a tiny
  minority; if they are not, something is wrong with the extraction
 
**C) By-year stratification:**
For each (year, event_type) pair:
- Average count per replay
- Median count per replay
- This reveals whether older SC2 versions or parser versions produce different
  event densities. If `PlayerStats` snapshots per game changed across versions,
  Phase 4 needs to account for it.
 
**D) By-tournament stratification (summary level):**
For each tournament, compute:
- Average `PlayerStats` events per replay
- Average `UnitBorn` events per replay
- Flag any tournament where the average deviates > 2 standard deviations from
  the corpus-wide mean — these may have data quality issues not visible in the
  binary presence/absence check of Step 1.2
 
Output: `01_06_event_type_inventory.csv` (corpus-wide)
Output: `01_06_event_count_distribution.csv` (per-replay distribution stats)
Output: `01_06_event_density_by_year.csv`
Output: `01_06_event_density_by_tournament.csv`
 
**1.7 — Lightweight PlayerStats sampling regularity check**
 
Phase 4 (Step 4.2) will do a full 200-game deep dive into sampling regularity.
This step does a lighter version across years to establish whether the ~160-loop
sampling interval assumption holds corpus-wide, or whether certain eras behave
differently. This informs whether Phase 4 needs to treat years separately.
 
For a stratified sample of 10 games per year (2016–2024, ~90 games total):
- For each game and player, sort `PlayerStats` events by `game_loop`
- Compute `diff(game_loop)` between consecutive snapshots
- Report: mean diff, std diff, min diff, max diff per game
- Aggregate by year: is the mean interval consistent at ~160 loops across all years?
- Flag any year where the mean interval deviates > 20% from 160
 
If all years are consistent (~160 ± 20%), note this and move on. If any year
diverges, document which year and by how much — Phase 4 will investigate further.
 
Output: `01_07_playerstats_sampling_check.csv`
 
**1.8 — Game settings and replay field completeness audit**
 
The replay JSON contains numerous fields beyond those already profiled in Steps
1.1–1.7. Several of these are critical assumptions that the entire pipeline
depends on but has never verified (e.g. game speed = Faster). Others are
potential features or cleaning criteria that would be missed entirely without
a systematic field audit.
 
This step profiles every non-event field in the replay JSON, grouped by
criticality. All results must include the literal SQL that produced them
(Scientific Invariant #8).
 
**A) Game speed verification (CRITICAL):**
 
Every duration conversion in this roadmap assumes Faster speed (22.4 loops/sec).
This assumption has never been verified against the actual data.
 
```sql
-- From initData
SELECT
    initData->'$.gameDescription'->>'$.gameSpeed' AS init_game_speed,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1
ORDER BY 2 DESC;
 
-- From details (cross-check)
SELECT
    details->>'$.gameSpeed' AS details_game_speed,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1
ORDER BY 2 DESC;
```
 
Expected: 100% "Faster" for tournament replays. If ANY game is not Faster,
it must be flagged — duration conversion, PlayerStats timing, and all
Phase 4 timepoints are wrong for that game. If non-Faster games exist,
add a cleaning rule in Phase 6.
 
Also verify consistency between the two fields:
```sql
SELECT
    initData->'$.gameDescription'->>'$.gameSpeed' AS init_speed,
    details->>'$.gameSpeed' AS details_speed,
    COUNT(*) AS n
FROM raw
WHERE init_speed != details_speed
```
 
**B) Handicap check (CRITICAL):**
 
A handicap value ≠ 100 means a player's units start with reduced HP.
These are not competitive games and must be excluded.
 
```sql
SELECT
    (entry.value->>'$.handicap')::INTEGER AS handicap,
    COUNT(*) AS n_player_slots
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1
ORDER BY 1;
```
 
Expected: 100% at handicap = 100. Any deviation → cleaning rule.
 
**C) Error flags audit (CRITICAL):**
 
The SC2EGSet pre-processing pipeline sets error flags when event extraction
fails. A game with `trackerEvtsErr = true` may have corrupted or incomplete
tracker events — features built from its PlayerStats snapshots would be
unreliable.
 
```sql
SELECT
    "gameEventsErr",
    "messageEventsErr",
    "trackerEvtsErr",
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1, 2, 3
ORDER BY 4 DESC;
```
 
For any replays with `trackerEvtsErr = true`:
- Count them
- Check whether they also have rows in `tracker_events_raw` (they might have
  partial data, which is worse than no data — partial data silently produces
  wrong features)
- List their `replay_id` and `tournament_dir`
- Recommend exclusion in Phase 6 cleaning rules
 
**D) Victory/defeat and game mode settings (CRITICAL):**
 
```sql
SELECT
    initData->'$.gameDescription'->'$.gameOptions'->>'$.noVictoryOrDefeat' AS no_victory,
    initData->'$.gameDescription'->'$.gameOptions'->>'$.competitive' AS competitive,
    initData->'$.gameDescription'->'$.gameOptions'->>'$.cooperative' AS cooperative,
    initData->'$.gameDescription'->'$.gameOptions'->>'$.practice' AS practice,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1, 2, 3, 4
ORDER BY 5 DESC;
```
 
Expected for tournament replays: noVictoryOrDefeat = false, competitive = false
(custom lobby, not ranked), cooperative = false, practice = false.
Any deviation must be investigated.
 
**E) Random race detection (IMPORTANT):**
 
```sql
SELECT
    (entry.value->>'$.selectedRace') AS selected_race,
    (entry.value->>'$.race') AS assigned_race,
    COUNT(*) AS n_player_slots
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1, 2
ORDER BY 3 DESC;
```
 
If `selectedRace` is empty or null for all slots, it may not be populated
in this dataset version. If it contains "Random" for some slots, those
players were assigned a random race — their `race` field shows the
assignment, not their preference. This affects:
- Phase 2 race consistency analysis (a Random player looks like a race switcher)
- Phase 7 race-specific win rate features (unreliable for Random players)
 
**F) SQ (Spending Quotient) and supplyCappedPercent profiling (IMPORTANT):**
 
These are per-game efficiency metrics computed from the replay, not from
the player profile (unlike MMR). They may be more reliably available
than MMR.
 
```sql
-- SQ distribution
SELECT
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'$.SQ')::INTEGER = 0
              OR (entry.value->>'$.SQ') IS NULL THEN 1 ELSE 0 END) AS sq_zero_or_null,
    ROUND(AVG((entry.value->>'$.SQ')::FLOAT), 1) AS mean_sq,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY (entry.value->>'$.SQ')::FLOAT) AS median_sq
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry;
 
-- SQ by year
SELECT
    EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'$.SQ')::INTEGER = 0
              OR (entry.value->>'$.SQ') IS NULL THEN 1 ELSE 0 END) AS sq_zero_or_null,
    ROUND(AVG(CASE WHEN (entry.value->>'$.SQ')::INTEGER > 0
              THEN (entry.value->>'$.SQ')::FLOAT END), 1) AS mean_sq_nonzero
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1 ORDER BY 1;
 
-- supplyCappedPercent distribution (same structure)
SELECT
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'$.supplyCappedPercent')::INTEGER = 0
              OR (entry.value->>'$.supplyCappedPercent') IS NULL THEN 1 ELSE 0 END) AS scp_zero_or_null,
    ROUND(AVG((entry.value->>'$.supplyCappedPercent')::FLOAT), 1) AS mean_scp,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY (entry.value->>'$.supplyCappedPercent')::FLOAT) AS median_scp
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry;
```
 
If SQ and supplyCappedPercent are reliably non-zero, they are candidate
features for Phase 7. If they show the same systematic missingness as
MMR, document them as dead fields.
 
**G) Map and lobby metadata profiling (MINOR):**
 
```sql
-- maxPlayers distribution (should be mostly 2 or 4 for 1v1 maps)
SELECT
    (initData->'$.gameDescription'->>'$.maxPlayers')::INTEGER AS max_players,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1
ORDER BY 1;
 
-- isBlizzardMap
SELECT
    initData->'$.gameDescription'->>'$.isBlizzardMap' AS is_blizzard,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1;
 
-- fog of war (should be 0 = standard)
SELECT
    (initData->'$.gameDescription'->'$.gameOptions'->>'$.fog')::INTEGER AS fog,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1;
 
-- randomRaces (should be false)
SELECT
    initData->'$.gameDescription'->'$.gameOptions'->>'$.randomRaces' AS random_races,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1;
 
-- observers count
SELECT
    (initData->'$.gameDescription'->'$.gameOptions'->>'$.observers')::INTEGER AS observers,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1;
```
 
**H) Version consistency check (MINOR):**
 
```sql
-- header.version vs metadata.gameVersion
SELECT
    header->>'$.version' AS header_version,
    metadata->>'$.gameVersion' AS meta_version,
    COUNT(*) AS n
FROM raw
WHERE header_version != meta_version;
```
 
Expected: 0 mismatches.
 
**I) Field completeness summary:**
 
Produce a single table summarising every JSON field's null/zero rate across
the corpus. This becomes the definitive reference for which fields are
usable and which are dead.
 
| Field path | Total slots | Non-null & non-zero | % available | Usable? |
|---|---|---|---|---|
| APM | 44,817 | 43,685 | 97.5% | Yes (2017+) |
| MMR | 44,817 | 7,328 | 16.4% | No |
| SQ | 44,817 | ? | ? | ? |
| supplyCappedPercent | 44,817 | ? | ? | ? |
| handicap | 44,817 | ? | ? | ? |
| ... | | | | |
 
Output: `01_game_settings_audit.md`
Output: `01_field_completeness_summary.csv`
Output: `01_error_flags_audit.csv` (list of replays with any error flag = true)

### Artifacts
 
- `01_01_corpus_summary.json`
- `01_01_player_count_anomalies.csv` (if anomalies exist)
- `01_01_result_field_audit.md`
- `01_01_duplicate_detection.md`
- `01_02_parse_quality_by_tournament.csv`
- `01_02_parse_quality_summary.md`
- `01_03_duration_distribution.csv`
- `01_03_duration_distribution_full.png`
- `01_03_duration_distribution_short_tail.png`
- `01_04_apm_mmr_audit.md`
- `01_05_patch_landscape.csv`
- `01_06_event_type_inventory.csv`
- `01_06_event_count_distribution.csv`
- `01_06_event_density_by_year.csv`
- `01_06_event_density_by_tournament.csv`
- `01_07_playerstats_sampling_check.csv`
- `01_game_settings_audit.md`
- `01_field_completeness_summary.csv`
- `01_error_flags_audit.csv`

### Gate
 
You can state precisely:
- (a) How many replays are in the corpus and how many are structurally valid
  (exactly 2 players, both with Win/Loss result, no duplicates)
- (b) Which tournaments have critical event data and which have structural anomalies
- (c) The full game duration distribution including percentiles and the short-game
  tail structure — but NO threshold has been chosen yet
- (d) APM is usable from 2017+, MMR is not usable
- (e) Tracker event density is consistent (or not) across years and tournaments
- (f) PlayerStats sampling interval is stable (or not) across years
- (g) Game speed is confirmed as Faster for all replays (or non-Faster games are
  documented and flagged for exclusion)
- (h) No replays have handicap ≠ 100 (or those that do are documented)
- (i) Tracker event error flag rate is known and error-flagged replays are documented
- (j) SQ and supplyCappedPercent availability is profiled (usable or not)

No cleaning has been applied. All observations are documented with the exact
queries that produced them (Scientific Invariant #8).
 
**Thesis mapping:** §4.1.1 — SC2EGSet description (corpus composition and quality)

---

## Phase 2 — Player universe and identity resolution

**Context:** SC2 player identity is fragmented. A player's "toon" (e.g. `3-S2-1-4842177`) is unique only per Battle.net server. Korean pros playing on EU or NA servers for international tournaments get different toons. The player's **lowercase nickname** is the practical canonical identifier (Scientific Invariant #2), but it has edge cases: shared nicknames, renames mid-career, encoding inconsistencies.

This phase builds the canonical player table that all downstream feature engineering depends on. Both players in every game must be treated symmetrically — the same identity resolution, the same feature computation pipeline (Scientific Invariant #8).

**Inputs:** `raw` table with `ToonPlayerDescMap` JSON column.

### Steps

**2.1 — Extract the player appearances table**

The `ToonPlayerDescMap` field is a JSON object keyed by toon string. For each replay and each toon entry, produce one row:

```
replay_id | tournament_dir | match_time | toon | nickname | player_id_in_game |
race | result | region | realm | sq | supply_capped_pct |
highest_league | is_in_clan | clan_tag | apm | mmr
```

Note: `player_id_in_game` is the `playerID` field (1 or 2 — the in-game slot), not a canonical player identifier. Do not confuse these.

`nickname` must be lowercased at extraction time (consistent with `flat_players` LOWER transform and Scientific Invariant #2).

Store as DuckDB table `player_appearances`. This is the foundation for all player-level analysis.

**2.2 — Parse toon components**

The toon format is `{realm_prefix}-S2-{region_id}-{account_id}`. For example, `3-S2-1-4842177` splits into:
- `toon_realm_prefix` = 3
- `toon_region` = 1
- `toon_account_id` = 4842177

Known region codes: 1 = Americas, 2 = Europe, 3 = Korea. Add a `region_name` column based on this mapping.

Add these parsed columns to `player_appearances`.

**2.3 — Build nickname → toon mapping**

Query:
```sql
SELECT
    nickname,
    COUNT(DISTINCT toon) AS n_toons,
    COUNT(DISTINCT toon_region) AS n_regions,
    LIST(DISTINCT toon) AS toon_list,
    LIST(DISTINCT region_name) AS regions_played,
    MIN(match_time) AS first_appearance,
    MAX(match_time) AS last_appearance,
    COUNT(DISTINCT replay_id) AS total_games
FROM player_appearances
GROUP BY nickname
ORDER BY n_toons DESC
```

Save full output. Inspect all rows where `n_toons > 1`. These are the server-switch cases. The expectation is that top Korean pros (sOs, ByuN, Maru, Serral, etc.) will appear with toons from Korea and one other region.

Output: `02_nickname_toon_mapping.csv`

**2.4 — Detect and classify multi-toon cases**

For each nickname with `n_toons > 1`, classify as:

- **Server switch (safe to merge):** Toons from different regions but overlapping date ranges. Same player, different server. Canonical identity = nickname.
- **Rename (requires investigation):** Toons from the same region but different time periods (one toon ends, another begins). Could be a player rename or coincidental nickname collision.
- **Ambiguous (flag):** Cannot be determined automatically. List manually.

Output: `02_multi_toon_cases.csv` with a `classification` column
Output: `02_ambiguous_nicknames.md` — manual review list

**2.5 — Build `canonical_players` table**

Create a DuckDB table with one row per unique professional player:

| column | description |
|--------|-------------|
| `player_canonical_id` | integer surrogate key (auto-increment) |
| `canonical_nickname` | lowercase nickname (Scientific Invariant #2) |
| `known_toons` | list of all associated toons |
| `primary_region` | most frequent `region_name` across appearances |
| `career_first_game` | earliest `match_time` |
| `career_last_game` | latest `match_time` |
| `career_span_days` | days between first and last game |
| `total_game_appearances` | total rows in `player_appearances` |

Add `player_canonical_id` as a foreign key back to `player_appearances`.

**2.6 — Player coverage analysis**

Using `canonical_players` and `player_appearances`:

- Total unique canonical players
- Histogram of games per player (bin at 10-game intervals)
- Players with fewer than 10 career games — list them (cold-start risk)
- Players with fewer than 3 tournaments — list them
- Top 30 players by total game count
- Gini coefficient of the games-per-player distribution (quantify inequality)

Output: `02_player_coverage.md`
Output: `02_games_per_player_histogram.png`
Output: `02_top_players.csv`

**2.7 — Race consistency per player**

For each canonical player, compute:
- Primary race (mode of `race` across all appearances)
- Fraction of games played as each race
- Flag players with > 5% games not as their primary race (race switchers)

Output: `02_player_race_consistency.csv`

### Artifacts

- DuckDB table: `player_appearances`
- DuckDB table: `canonical_players`
- `02_nickname_toon_mapping.csv`
- `02_multi_toon_cases.csv`
- `02_ambiguous_nicknames.md`
- `02_player_coverage.md`
- `02_games_per_player_histogram.png`
- `02_top_players.csv`
- `02_player_race_consistency.csv`

### Gate

`canonical_players` table exists. Every toon in `player_appearances` is assigned a `player_canonical_id`. The ambiguous nickname list is reviewed — even if the decision is "flag as uncertain and keep." You can state precisely how many unique professionals are in the dataset and what the game count distribution looks like.

**Thesis mapping:** §4.2.2 — Player identity resolution

---

## Appendix — Artifact index

All Phase 0–2 reports land in this directory (`sc2egset/`). All data files land in `data/`. Logs land in `logs/`.

```
sc2egset/
  00_01_source_audit.json
  00_02_tournament_name_validation.txt
  00_03_replay_id_spec.md
  00_04_path_a_smoke_test.md
  00_05_full_ingestion_log.txt
  00_07_path_b_extraction_log.txt
  00_08_join_validation.md
  00_09_map_translation_coverage.csv
  01_01_corpus_summary.json
  01_01_player_count_anomalies.csv
  01_01_result_field_audit.md
  01_01_duplicate_detection.md
  01_02_parse_quality_by_tournament.csv
  01_02_parse_quality_summary.md
  01_03_duration_distribution.csv
  01_03_duration_distribution_full.png
  01_03_duration_distribution_short_tail.png
  01_04_apm_mmr_audit.md
  01_05_patch_landscape.csv
  01_06_event_type_inventory.csv
  01_06_event_count_distribution.csv
  01_06_event_density_by_year.csv
  01_06_event_density_by_tournament.csv
  01_07_playerstats_sampling_check.csv
  01_game_settings_audit.md
  01_field_completeness_summary.csv
  01_error_flags_audit.csv
  02_nickname_toon_mapping.csv
  02_multi_toon_cases.csv
  02_ambiguous_nicknames.md
  02_player_coverage.md
  02_games_per_player_histogram.png
  02_top_players.csv
  02_player_race_consistency.csv

data/
  unit_type_taxonomy.csv
  features_group_a.parquet
  features_group_b.parquet
  ml_dataset.parquet
```

---

## Appendix — Known dead code in existing scripts

The following functions exist in `ingestion.py` but should **not** be called during this pipeline:

- `slim_down_sc2_with_manifest(dry_run=False)` — irreversibly destroys source JSON files. Do not call unless you have confirmed that Path B extraction is fully complete and all Parquet files are safely written. Even then, consider whether you want to preserve the originals.

The following function in `processing.py` is superseded by Phase 8:

- `create_temporal_split()` — the naïve tournament-level chronological split. Useful for a quick ingestion smoke test but must not be used as the final train/val/test split for any thesis experiment.

The following in `cli.py` runs the old pipeline end-to-end including the wrong split:

- `run_pipeline()` — do not use until Phase 8 is complete and the split column in `ml_dataset.parquet` is correct.

---

## Appendix — Key references

| Short cite | Full reference | Used for |
|---|---|---|
| Białecki et al. 2023 | Białecki, A. et al. SC2EGSet: SC2 Esport Replay and Game-state Dataset. *Scientific Data* 10(1), 600. | Dataset |
| Vinyals et al. 2017 | Vinyals, O. et al. StarCraft II: A New Challenge for RL. *arXiv:1708.04782*. | Game loop timing, SC2LE |
| Wu et al. 2017 | Wu, H. et al. MSC: A Dataset for Macro-Management in SC2. *arXiv:1710.03131*. | Duration threshold (7 min), GRU baseline |
| Baek & Kim 2022 | Baek, J. & Kim, J. 3D-CNNs for SC2 prediction. *PLOS ONE*. | 90% accuracy benchmark |
| Khan et al. 2021 | Khan, A. et al. Transformers on SC2 MSC. *IEEE ICMLA*. | Transformer baseline |
| Glickman 2001 | Glickman, M. The Glicko-2 System. | Rating system |
| Thorrez 2024 | Thorrez, L. EsportsBench. | Glicko-2 at 80.13% for SC2 |
| Demšar 2006 | Demšar, J. Statistical Comparisons of Classifiers. *JMLR* 7. | Cross-game statistical comparison |
| Hodge et al. 2021 | Hodge, V. et al. Dota 2 Win Prediction. *IEEE Trans. Games*. | In-game accuracy curve precedent |
| Liquipedia | Game Speed article, Cheese strategies | Game loop conversion, short game landmarks |
| s2client-proto | Blizzard/s2client-proto protocol.md | 22.4 loops/s at Faster speed |
