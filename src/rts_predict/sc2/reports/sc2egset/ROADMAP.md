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
 
Output: `01_08_game_settings_audit.md`
Output: `01_08_field_completeness_summary.csv` *(superseded — not produced; see note below)*
Output: `01_08_error_flags_audit.csv` (list of replays with any error flag = true)

**Note on Step 1.8 sub-steps F and I:** Sub-steps F (SQ/supplyCappedPercent profiling) and I (field completeness summary) are superseded by Step 1.10, which applies the §3.1 profiling battery uniformly to ALL ToonPlayerDescMap fields. Running 1.8F before Step 1.10 would profile SQ and supplyCappedPercent twice. Sub-steps A–E, G, H execute as originally defined. `01_08_field_completeness_summary.csv` is superseded by `01_10_tpdm_column_profile.csv` and `01_10_tpdm_field_status.csv`.

**1.9 — Systematic ToonPlayerDescMap field inventory and JSON structure verification**

Context: The ToonPlayerDescMap column is a JSON object keyed by toon string, where each value is a JSON object containing player-level metadata. Steps 1.4 and
1.8 profile selected fields (APM, MMR, SQ, supplyCappedPercent, handicap, race, selectedRace, result, highestLeague). However, the full set of keys in these
per-player objects has never been enumerated from the data itself. Manual 01 §3.1 requires column-level profiling for every extractable field, and constraint 9
requires verifying JSON structure constancy before profiling values. This step satisfies Manual 01 §1 (schema discovery) and §3.1 (column-level profiling
prerequisite). Feeds thesis §4.1.1 (SC2EGSet description).

Inputs: raw table.

Sub-steps:

**1.9A — Enumerate all distinct keys in ToonPlayerDescMap player objects**

```sql
SELECT DISTINCT json_key
FROM (
    SELECT unnest(json_keys(entry.value)) AS json_key
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
)
ORDER BY json_key;
```

```
poetry run sc2 db --dataset sc2egset query "SELECT DISTINCT json_key FROM (SELECT unnest(json_keys(entry.value)) AS json_key FROM raw, LATERAL json_each(\"ToonPlayerDescMap\") AS entry) ORDER BY json_key" --format table
```

**1.9B — Verify key-set constancy across all player slots**

```sql
WITH key_sets AS (
    SELECT
        filename,
        entry.key AS toon,
        LIST(k ORDER BY k) AS key_list
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry,
         LATERAL unnest(json_keys(entry.value)) AS t(k)
    GROUP BY filename, entry.key
)
SELECT key_list, COUNT(*) AS n_slots
FROM key_sets
GROUP BY key_list
ORDER BY n_slots DESC;
```

```
poetry run sc2 db --dataset sc2egset query "WITH key_sets AS (SELECT filename, entry.key AS toon, LIST(k ORDER BY k) AS key_list FROM raw, LATERAL json_each(\"ToonPlayerDescMap\") AS entry, LATERAL unnest(json_keys(entry.value)) AS t(k) GROUP BY filename, entry.key) SELECT key_list, COUNT(*) AS n_slots FROM key_sets GROUP BY key_list ORDER BY n_slots DESC" --format csv
```

**1.9C — Enumerate all distinct keys in top-level JSON columns (header, initData, details, metadata)**

For each of header, initData, details, metadata:

```sql
SELECT DISTINCT json_key
FROM (
    SELECT unnest(json_keys(header)) AS json_key FROM raw
)
ORDER BY json_key;
```

```
poetry run sc2 db --dataset sc2egset query "SELECT DISTINCT json_key FROM (SELECT unnest(json_keys(header)) AS json_key FROM raw) ORDER BY json_key" --format table
```

Repeat for initData, details, metadata. For nested objects (e.g., initData->'$.gameDescription'), recursively enumerate one level deeper.

Artifacts:
- `01_09_tpdm_field_inventory.csv`
- `01_09_tpdm_key_set_constancy.csv`
- `01_09_toplevel_field_inventory.csv`

Thesis mapping: §4.1.1 — SC2EGSet schema documentation

Gate condition:
- Artifact check: All three CSV files exist and are non-empty.
- Continue predicate: If the key-set is constant (one variant with 100% of slots) or nearly constant (dominant variant covers >99% of slots), continue to Step 1.10.
- Halt predicate: If more than 5 distinct key-set variants exist each covering >5% of slots, halt Phase 1 and escalate, because the assumption that all player slots have identical schema (which all downstream JSON path extraction depends on) would be violated.

[CROSS-GAME]

---

**1.9D — Tracker `event_data` field inventory**

Context: Steps 1.9A–C profiled ToonPlayerDescMap and top-level JSON columns. The
`tracker_events_raw` table (~62M rows, 10 distinct event types) stores per-event JSON
payloads in an `event_data VARCHAR` column. This step enumerates all JSON keys inside
those payloads, verifies key-set constancy, and inventories the PlayerStats.stats
nested sub-object (39 metric fields). Required before Phase 4 can extract per-event
feature columns.

Inputs: tracker_events_raw table.

Sub-steps:

**1.9D-i — Per-event-type JSON key inventory**

```python
from rts_predict.sc2.data.exploration import (
    build_event_data_field_inventory_query, run_tracker_event_data_inventory
)
# SQL query template (with USING SAMPLE 100000 ROWS):
sql = build_event_data_field_inventory_query('tracker_events_raw', sample_size=100_000)
```

Returns columns: event_type, json_key, is_nested.

**1.9D-ii — Key-set constancy per event type**

```python
from rts_predict.sc2.data.exploration import build_event_data_key_constancy_query
# For each event type et:
sql = build_event_data_key_constancy_query('tracker_events_raw', et, sample_size=10_000)
```

Returns columns: key_list, n_events, pct (sorted by n_events DESC).

**1.9D-iii — PlayerStats.stats nested field inventory**

```python
from rts_predict.sc2.data.exploration import build_nested_field_inventory_query
sql = build_nested_field_inventory_query(
    'tracker_events_raw', 'PlayerStats', 'stats', sample_size=100_000
)
```

Returns column: nested_key_name.

Artifacts:
- `01_09D_tracker_event_data_field_inventory.csv` (columns: event_type, json_key, is_nested)
- `01_09D_tracker_event_data_key_constancy.csv` (columns: event_type, key_list, n_events, pct)
- `01_09D_playerstats_stats_field_inventory.csv` (column: nested_key_name)

Findings (2026-04-07):
- 10 distinct tracker event types; 80 total (event_type, json_key) pairs.
- 39 PlayerStats.stats sub-keys found.
- Key-set constancy: 9/10 types at 100%; UnitBorn at 93.81% (warning, not halt) —
  UnitBorn has optional `killerPlayerId`, `killerUnitTagIndex`, `killerUnitTagRecycle`
  fields that are absent when the unit is not killed by another unit.

Gate condition:
- Artifact check: All three CSV files exist and are non-empty.
- Continue predicate: Each event type has a dominant key-set variant >99%. UnitBorn
  gate violation (93.81%) is documented as a known exception — optional killer fields
  are structurally motivated. Continue to 1.9E.
- Halt predicate: If any event type other than UnitBorn has dominant variant ≤95%.

---

**1.9E — Game `event_data` field inventory**

Context: The `game_events_raw` table (~609M rows, 23 distinct event types) also stores
JSON payloads in `event_data`. This step focuses on the 5 high-value event types that
will drive Phase 4 in-game features: Cmd, SelectionDelta, ControlGroupUpdate,
CmdUpdateTargetPoint, CmdUpdateTargetUnit.

Inputs: game_events_raw table.

Sub-steps:

**1.9E-i — Per-event-type JSON key inventory**

```python
sql = build_event_data_field_inventory_query('game_events_raw', sample_size=200_000)
```

**1.9E-ii — Nested sub-object enumerations**

```python
# For (Cmd, abil), (Cmd, data), (SelectionDelta, delta):
sql = build_nested_field_inventory_query('game_events_raw', et, nested_key, sample_size=200_000)
```

**1.9E-iii — Key-set constancy for 5 high-value types**

```python
for et in ('Cmd', 'SelectionDelta', 'ControlGroupUpdate',
           'CmdUpdateTargetPoint', 'CmdUpdateTargetUnit'):
    sql = build_event_data_key_constancy_query('game_events_raw', et, sample_size=10_000)
```

Artifacts:
- `01_09E_game_event_data_field_inventory.csv` (columns: event_type, json_key, is_nested)
- `01_09E_game_event_data_key_constancy.csv` (columns: event_type, key_list, n_events, pct)

Findings (2026-04-07):
- All 5 high-value types have dominant key-set variant = 100%. Gate PASS.
- Nested sub-objects: Cmd.abil (3 keys), Cmd.data (1 key), SelectionDelta.delta (4 keys).

Gate condition:
- Artifact check: Both CSV files exist and are non-empty.
- Continue predicate: All 5 types have dominant variant >95%.

---

**1.9F — Parquet↔DuckDB reconciliation + consolidated schema document**

Context: Validates that the Parquet staging files (produced by Path B extraction) have
schemas consistent with the DuckDB table definitions, and compiles a consolidated
event_data schema reference from 1.9D and 1.9E findings.

Inputs: Staging Parquet files in `staging/in_game_events/`, DuckDB db.duckdb, 1.9D/E CSVs.

Sub-steps:

**1.9F-i — Parquet↔DuckDB schema reconciliation**

```python
from rts_predict.sc2.data.exploration import run_parquet_duckdb_reconciliation
result = run_parquet_duckdb_reconciliation(output_dir=DATASET_REPORTS_DIR)
```

Checks column names (order-independent) for 5 randomly selected batches per table.

**1.9F-ii — Compile consolidated schema document**

```python
from rts_predict.sc2.data.exploration import run_event_schema_document
result = run_event_schema_document(output_dir=DATASET_REPORTS_DIR)
```

Artifacts:
- `01_09F_parquet_duckdb_schema_reconciliation.md`
- `01_09F_event_schema_reference.md`

Findings (2026-04-07):
- Tracker Parquet schema: match_id:string, event_type:string, game_loop:int32,
  player_id:int8, event_data:string — consistent with DuckDB (0 mismatches, 5 batches).
- Game Parquet schema: same + user_id:int32 — consistent with DuckDB (0 mismatches, 5 batches).
- Schema reference covers all 10 tracker types and all 5 high-value game types. Gate PASS.

Gate condition:
- Artifact check: Both MD files exist.
- Continue predicate: 0 schema mismatches across both tables; all event types covered in reference.

[CROSS-GAME]

---

**1.10 — Uniform column-level profiling of all ToonPlayerDescMap fields**

Context: Manual 01 §3.1 prescribes a standard profiling battery for every variable. Step 1.9 will have enumerated the complete field list. This step applies the
§3.1 battery uniformly to all fields (constraint 6: treat all fields symmetrically, no cherry-picking). Feeds thesis §4.1.1 (field descriptions) and §4.1.2 (data quality).

Inputs: raw table. Complete field list from Step 1.9.

Sub-steps:

**1.10A — Null/missing rate, zero rate, cardinality, distinct-value count**

For each field F from Step 1.9A (via a generated UNION ALL query):

```sql
SELECT
    '{field_name}' AS field_name,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'{json_path}') IS NULL THEN 1 ELSE 0 END) AS null_count,
    ROUND(100.0 * SUM(CASE WHEN (entry.value->>'{json_path}') IS NULL
        THEN 1 ELSE 0 END) / COUNT(*), 2) AS null_pct,
    SUM(CASE WHEN (entry.value->>'{json_path}') = '0'
        OR (entry.value->>'{json_path}') = '' THEN 1 ELSE 0 END) AS zero_or_empty_count,
    ROUND(100.0 * SUM(CASE WHEN (entry.value->>'{json_path}') = '0'
        OR (entry.value->>'{json_path}') = '' THEN 1 ELSE 0 END) / COUNT(*), 2) AS zero_or_empty_pct,
    COUNT(DISTINCT (entry.value->>'{json_path}')) AS distinct_count,
    ROUND(COUNT(DISTINCT (entry.value->>'{json_path}'))::DOUBLE / COUNT(*), 6) AS uniqueness_ratio
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry;
```

The full UNION ALL query is generated by build_tpdm_profiling_query(field_list: list[str]) -> str in exploration.py. CLI invocation:

```
poetry run sc2 db --dataset sc2egset query "<generated SQL>" --format csv
```

**1.10B — Distribution summary for numeric fields (min/max/mean/median/percentiles)**

For each field classified as numeric in 1.10A (distinct_count > 2, values parse as numbers):

```sql
SELECT
    '{field_name}' AS field_name,
    MIN(val) AS min_val, MAX(val) AS max_val,
    ROUND(AVG(val), 2) AS mean_val,
    ROUND(MEDIAN(val), 2) AS median_val,
    ROUND(STDDEV(val), 2) AS std_val,
    ROUND(QUANTILE_CONT(val, 0.01), 2) AS p01,
    ROUND(QUANTILE_CONT(val, 0.05), 2) AS p05,
    ROUND(QUANTILE_CONT(val, 0.25), 2) AS p25,
    ROUND(QUANTILE_CONT(val, 0.75), 2) AS p75,
    ROUND(QUANTILE_CONT(val, 0.95), 2) AS p95,
    ROUND(QUANTILE_CONT(val, 0.99), 2) AS p99,
    ROUND((QUANTILE_CONT(val, 0.75) - QUANTILE_CONT(val, 0.25)), 2) AS iqr
FROM (
    SELECT (entry.value->>'{json_path}')::DOUBLE AS val
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
    WHERE (entry.value->>'{json_path}') IS NOT NULL
      AND TRY_CAST((entry.value->>'{json_path}') AS DOUBLE) IS NOT NULL
)
WHERE val != 0;
```

**1.10C — Top-k frequent values for categorical/string fields**

For each field with distinct_count <= 100:

```sql
SELECT
    '{field_name}' AS field_name,
    (entry.value->>'{json_path}') AS value,
    COUNT(*) AS frequency,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 2
ORDER BY 3 DESC
LIMIT 20;
```

**1.10D — Dead / constant / near-constant detection (Manual 01 §3.3)**

Applied as a Python classification from 1.10A results:

```python
def classify_field_status(
    null_pct: float, distinct_count: int, uniqueness_ratio: float, total_slots: int
) -> str:
    """Classify field as dead, constant, near-constant, or active.

    Threshold source: Manual 01 §3.3 — "a uniqueness ratio below 0.001 is a
    reasonable starting point" for flagging near-constant columns.
    """
    if null_pct == 100.0:
        return "dead"
    if distinct_count == 1:
        return "constant"
    # Threshold: uniqueness_ratio < 0.001 (Manual 01 §3.3)
    if uniqueness_ratio < 0.001:
        return "near-constant"
    return "active"
```

**1.10E — Year-stratified zero/null rates for all fields (Manual 01 §7)**

```sql
SELECT
    EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year,
    '{field_name}' AS field_name,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'{json_path}') IS NULL
        OR (entry.value->>'{json_path}') = '0' THEN 1 ELSE 0 END) AS zero_or_null,
    ROUND(100.0 * SUM(CASE WHEN (entry.value->>'{json_path}') IS NULL
        OR (entry.value->>'{json_path}') = '0' THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_zero_or_null
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1, 2
ORDER BY 2, 1;
```

```
poetry run sc2 db --dataset sc2egset query "<generated UNION ALL SQL per field>" --format csv
```

Artifacts:
- `01_10_tpdm_column_profile.csv`
- `01_10_tpdm_numeric_distributions.csv`
- `01_10_tpdm_categorical_topk.csv`
- `01_10_tpdm_field_status.csv`
- `01_10_tpdm_availability_by_year.csv`

Thesis mapping: §4.1.1 — field descriptions; §4.1.2 — data quality summary

Gate condition:
- Artifact check: All five CSV files exist and are non-empty.
- Continue predicate: If every field from Step 1.9 has a complete profiling row in 01_10_tpdm_column_profile.csv, continue to Step 1.11.
- Halt predicate: Halt and escalate to user if the number of "active" fields (per the classify_field_status classification) is insufficient to construct any reasonable pre-game feature set. Specifically: halt if, after excluding fields classified as "dead" or "constant", fewer than 3 fields remain with classification PRE_GAME (as determined in the subsequent Step 1.11). The premise being tested is that ToonPlayerDescMap contains sufficient per-player metadata for pre-game feature construction. If this premise is violated, no downstream feature engineering is possible from this data source alone.

[CROSS-GAME]

---

**1.11 — Temporal leakage risk classification for all fields**

Context: Manual 01 §5 requires a temporal leakage risk audit for every field that may feed Phase 7 (feature engineering). Scientific Invariant 3 states that no
feature for game T may use information from game T or later, and that violations are "fatal to the thesis." Several ToonPlayerDescMap fields are computed from
the replay itself (post-game aggregates), not from the player's pre-game profile. This step classifies every field by temporal availability. Feeds thesis §3.3
(methodology — temporal discipline).

Inputs: Field inventory from Step 1.9. Field profiles from Step 1.10. SC2EGSet documentation (Bialecki et al. 2023). Blizzard s2client-proto documentation.

Sub-steps:

**1.11A — Classify each field by temporal availability**

Domain-knowledge annotation step. Each field receives one label:

- PRE_GAME: Value is known before the game starts and does not change during the game. Safe for pre-game features. Examples: race, selectedRace, nickname, highestLeague, MMR (the rating before the game).
- POST_GAME: Value is computed from in-game events after the game ends. Using this as a pre-game feature violates Invariant 3. Examples: APM, SQ, supplyCappedPercent, result.
- AMBIGUOUS: Cannot be definitively classified without further investigation. Document the specific uncertainty. AMBIGUOUS fields are conservatively excluded from pre-game features (safe_for_pre_game_features = False) and recorded in the risk register produced by Step 1.16.

```python
def classify_temporal_availability(field_name: str) -> dict:
    """Classify a ToonPlayerDescMap field by temporal availability.
    Returns dict with keys: field_name, classification, rationale,
    safe_for_pre_game_features, source_documentation.

    For AMBIGUOUS fields, safe_for_pre_game_features is always False
    and rationale is set to "ambiguous — conservatively excluded pending
    documentation."
    """
    ...
```

**1.11B — Verify POST_GAME classification empirically for APM and SQ**

APM–duration correlation (APM is a post-game aggregate per game clock, not a pre-game profile value):

```sql
SELECT
    ROUND(CORR(
        (entry.value->>'$.APM')::DOUBLE,
        (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0
    ), 4) AS apm_duration_correlation,
    COUNT(*) AS n
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
WHERE (entry.value->>'$.APM')::DOUBLE > 0;
```

```
poetry run sc2 db --dataset sc2egset query "SELECT ROUND(CORR((entry.value->>'$.APM')::DOUBLE, (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0), 4) AS apm_duration_correlation, COUNT(*) AS n FROM raw, LATERAL json_each(\"ToonPlayerDescMap\") AS entry WHERE (entry.value->>'$.APM')::DOUBLE > 0" --format table
```

SQ–duration correlation:

```sql
SELECT
    ROUND(CORR(
        (entry.value->>'$.SQ')::DOUBLE,
        (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0
    ), 4) AS sq_duration_correlation,
    COUNT(*) AS n
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
WHERE TRY_CAST((entry.value->>'$.SQ') AS DOUBLE) IS NOT NULL
  AND (entry.value->>'$.SQ')::DOUBLE > 0;
```

```
poetry run sc2 db --dataset sc2egset query "SELECT ROUND(CORR((entry.value->>'$.SQ')::DOUBLE, (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0), 4) AS sq_duration_correlation, COUNT(*) AS n FROM raw, LATERAL json_each(\"ToonPlayerDescMap\") AS entry WHERE TRY_CAST((entry.value->>'$.SQ') AS DOUBLE) IS NOT NULL AND (entry.value->>'$.SQ')::DOUBLE > 0" --format table
```

**1.11C — Document the classification in a structured table**

AMBIGUOUS fields are written to the output CSV with `safe_for_pre_game_features = False` and rationale marked `"ambiguous — conservatively excluded pending documentation."`.

Artifacts:
- `01_11_temporal_leakage_classification.csv` (field_name, classification [PRE_GAME/POST_GAME/AMBIGUOUS], rationale, safe_for_pre_game_features [true/false], source)
- `01_11_leakage_empirical_checks.md` (APM-duration and SQ-duration correlation results with the SQL that produced them)

Thesis mapping: §3.3 — temporal discipline methodology; §4.1.3 — temporal leakage risk audit

Gate condition:
- Artifact check: Both files exist and are non-empty.
- Continue predicate: If every field from Step 1.9 has a classification and all POST_GAME fields are clearly documented with rationale, continue to Step 1.12.
- Halt predicate: Continue if every AMBIGUOUS field can be conservatively excluded from pre-game features (i.e., classified safe_for_pre_game_features = False by default) and recorded in the risk register produced by Step 1.16. Halt and escalate only if a field is both AMBIGUOUS and so structurally central to Phase 3 feature engineering that conservative exclusion would block the construction of any reasonable pre-game feature set.

[CROSS-GAME]

---

**1.12 — Dataset-level class balance and feature completeness heatmap**

Context: Manual 01 §3.2 requires dataset-level profiling including class balance of the target variable and a feature completeness heatmap. Step 1.1 counted Win
(22,382) vs Loss (22,409) at the player-slot level, but the target variable for prediction is replay-level outcome. This step produces the correct replay-level
class balance and a visual heatmap of field completeness. Feeds thesis §4.1.2 (data quality).

Inputs: raw table. Field profiles from Step 1.10.

Sub-steps:

**1.12A — Replay-level class balance (after excluding structural anomalies)**

```sql
WITH valid_replays AS (
    SELECT
        filename,
        SUM(CASE WHEN entry.value->>'$.result' = 'Win' THEN 1 ELSE 0 END) AS win_count,
        SUM(CASE WHEN entry.value->>'$.result' = 'Loss' THEN 1 ELSE 0 END) AS loss_count,
        COUNT(*) AS player_count
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
    GROUP BY filename
)
SELECT
    SUM(CASE WHEN win_count = 1 AND loss_count = 1 AND player_count = 2
        THEN 1 ELSE 0 END) AS valid_1v1_replays,
    SUM(CASE WHEN win_count != 1 OR loss_count != 1 OR player_count != 2
        THEN 1 ELSE 0 END) AS excluded_replays,
    COUNT(*) AS total_replays
FROM valid_replays;
```

```
poetry run sc2 db --dataset sc2egset query "WITH valid_replays AS (SELECT filename, SUM(CASE WHEN entry.value->>'$.result' = 'Win' THEN 1 ELSE 0 END) AS win_count, SUM(CASE WHEN entry.value->>'$.result' = 'Loss' THEN 1 ELSE 0 END) AS loss_count, COUNT(*) AS player_count FROM raw, LATERAL json_each(\"ToonPlayerDescMap\") AS entry GROUP BY filename) SELECT SUM(CASE WHEN win_count = 1 AND loss_count = 1 AND player_count = 2 THEN 1 ELSE 0 END) AS valid_1v1_replays, SUM(CASE WHEN win_count != 1 OR loss_count != 1 OR player_count != 2 THEN 1 ELSE 0 END) AS excluded_replays, COUNT(*) AS total_replays FROM valid_replays" --format table
```

**1.12B — Class balance stratified by year and tournament**

```sql
SELECT
    EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year,
    split_part(filename, '/', -3) AS tournament_dir,
    COUNT(*) AS total_replays,
    SUM(CASE WHEN entry.value->>'$.result' = 'Win' THEN 1 ELSE 0 END) AS win_slots,
    SUM(CASE WHEN entry.value->>'$.result' = 'Loss' THEN 1 ELSE 0 END) AS loss_slots,
    SUM(CASE WHEN entry.value->>'$.result' NOT IN ('Win', 'Loss')
        OR entry.value->>'$.result' IS NULL THEN 1 ELSE 0 END) AS anomalous_slots
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1, 2
ORDER BY 1, 2;
```

```
poetry run sc2 db --dataset sc2egset query "<SQL above>" --format csv
```

**1.12C — Feature completeness heatmap (Python)**

```python
def plot_field_completeness_heatmap(
    profile_df: pd.DataFrame,
    output_path: Path,
) -> None:
    """Generate a heatmap of field availability rates across years.
    Args:
        profile_df: DataFrame from 01_10_tpdm_availability_by_year.csv
        output_path: Path for the output PNG
    """
    ...
```

Uses the year-stratified availability data from Step 1.10E to create a (field x year) heatmap where cell color represents the percentage of non-null, non-zero values.

Artifacts:
- `01_12_class_balance.csv`
- `01_12_class_balance_stratified.csv`
- `01_12_field_completeness_heatmap.png`

Thesis mapping: §4.1.2 — data quality; §4.1.1 — dataset summary statistics

Gate condition:
- Artifact check: All three files exist and are non-empty.
- Continue predicate: If valid_1v1_replays / total_replays > 0.999, continue to Step 1.13. (Threshold source: Step 1.1 established that 13 out of 22,390 replays are anomalous, yielding a 99.94% valid rate. The 99.9% threshold is derived from this empirical baseline — any significant drop below the established rate indicates a regression or a data-processing error introduced between Step 1.1 and Step 1.12.)
- Halt predicate: If valid_1v1_replays / total_replays drops to 0.999 or below, halt Phase 1 and escalate, because the valid replay rate would have degraded significantly relative to the 99.94% baseline established by Step 1.1, indicating that the assumption that SC2EGSet is predominantly a 1v1 tournament dataset (which the entire prediction task definition rests on) may be violated or that a processing error has been introduced.

[CROSS-GAME]

---

**1.13 — Bivariate analysis: race, matchup, and result**

Context: Manual 01 §4 requires bivariate and multivariate analysis. For the pre-game prediction task, the most important bivariate relationships are between
race/matchup and win rate, stratified by year and tournament to mitigate Simpson's paradox (Manual 01 §7). This step produces the cross-tabulations that Phase 7
matchup features will depend on. True multivariate stratification (e.g., race x map x era x result interaction) is deferred to Phase 2, where the player appearances table provides the structured player-game grain necessary for multi-factor analysis; Phase 1 operates on raw JSON and covers bivariate cases only. Feeds thesis §4.2 (exploratory analysis).

Inputs: raw table.

Sub-steps:

**1.13A — Race distribution (overall and by year)**

```sql
SELECT
    entry.value->>'$.race' AS race,
    COUNT(*) AS n_slots,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1
ORDER BY 2 DESC;
```

```
poetry run sc2 db --dataset sc2egset query "SELECT entry.value->>'$.race' AS race, COUNT(*) AS n_slots, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct FROM raw, LATERAL json_each(\"ToonPlayerDescMap\") AS entry GROUP BY 1 ORDER BY 2 DESC" --format table
```

Year-stratified:

```sql
SELECT
    EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year,
    entry.value->>'$.race' AS race,
    COUNT(*) AS n_slots,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY
        EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP)), 2) AS pct
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1, 2
ORDER BY 1, 3 DESC;
```

```
poetry run sc2 db --dataset sc2egset query "<SQL above>" --format csv
```

**1.13B — Matchup win rates (overall and by year)**

```sql
WITH game_pairs AS (
    SELECT
        filename,
        EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year,
        split_part(filename, '/', -3) AS tournament_dir,
        MAX(CASE WHEN entry.value->>'$.result' = 'Win'
            THEN entry.value->>'$.race' END) AS winner_race,
        MAX(CASE WHEN entry.value->>'$.result' = 'Loss'
            THEN entry.value->>'$.race' END) AS loser_race
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
    GROUP BY filename, 2, 3
    HAVING COUNT(*) = 2
       AND SUM(CASE WHEN entry.value->>'$.result' = 'Win' THEN 1 ELSE 0 END) = 1
       AND SUM(CASE WHEN entry.value->>'$.result' = 'Loss' THEN 1 ELSE 0 END) = 1
),
matchups AS (
    SELECT *,
        CASE WHEN winner_race <= loser_race
            THEN winner_race || 'v' || loser_race
            ELSE loser_race || 'v' || winner_race
        END AS matchup,
        CASE WHEN winner_race <= loser_race
            THEN winner_race ELSE loser_race
        END AS first_race
    FROM game_pairs
)
SELECT
    matchup, first_race,
    COUNT(*) AS total_games,
    SUM(CASE WHEN winner_race = first_race THEN 1 ELSE 0 END) AS first_race_wins,
    ROUND(100.0 * SUM(CASE WHEN winner_race = first_race THEN 1 ELSE 0 END) / COUNT(*), 1) AS first_race_win_pct
FROM matchups
GROUP BY 1, 2
ORDER BY 1;
```

```
poetry run sc2 db --dataset sc2egset query "<SQL above>" --format csv
```

Year-stratified version: add year to the GROUP BY and SELECT.

**1.13C — Race win rate by tournament tier (Simpson's-paradox check)**

Same as 1.13B with tournament_dir added to GROUP BY.

Artifacts:
- `01_13_race_distribution.csv`
- `01_13_matchup_win_rates.csv`
- `01_13_matchup_win_rates_by_year.csv`
- `01_13_matchup_win_rates_by_tournament.csv`

Thesis mapping: §4.2.1 — race and matchup analysis; §4.3 — balance meta-analysis

Gate condition:
- Artifact check: All four CSV files exist and are non-empty.
- Continue predicate: If all six matchups (TvZ, TvP, ZvP, TvT, ZvZ, PvP) have at least 100 games each and aggregate win rates are between 30% and 70%, continue to Step 1.14. (Threshold source: Agresti 2002, Categorical Data Analysis — 100 games minimum for stable proportion estimates; 30–70% range reflects competitive balance.)
- Halt predicate: If any matchup has fewer than 20 games total, halt Phase 1 and escalate, because matchup-stratified feature engineering in Phase 7 would be unreliable due to insufficient sample size per stratum.

[CROSS-GAME]

---

**1.14 — Correlation analysis of numeric ToonPlayerDescMap fields**

Context: Manual 01 §4 prescribes bivariate correlation analysis. For numeric fields in ToonPlayerDescMap (APM, SQ, supplyCappedPercent, MMR where available),
pairwise correlations reveal redundancy and potential multicollinearity before feature engineering. This step is observational — no feature selection decisions
are made. Feeds thesis §4.2 (exploratory analysis).

Inputs: raw table. Numeric field list from Step 1.10.

Sub-steps:

**1.14A — Extract numeric fields for Spearman correlation (Python)**

Spearman is preferred over Pearson because distributions are likely non-normal (Manual 01 §2.1: "Spearman for monotonic relationships"). DuckDB does not have a
built-in SPEARMAN_CORR, so data is extracted and computed in Python via scipy.stats.spearmanr.

```sql
SELECT
    (entry.value->>'$.APM')::DOUBLE AS apm,
    (entry.value->>'$.SQ')::DOUBLE AS sq,
    (entry.value->>'$.supplyCappedPercent')::DOUBLE AS supply_capped_pct,
    (entry.value->>'$.MMR')::DOUBLE AS mmr,
    (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0 AS duration_minutes,
    entry.value->>'$.race' AS race,
    entry.value->>'$.result' AS result,
    EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
WHERE (entry.value->>'$.APM')::DOUBLE > 0;
```

```
poetry run sc2 db --dataset sc2egset query "SELECT (entry.value->>'$.APM')::DOUBLE AS apm, (entry.value->>'$.SQ')::DOUBLE AS sq, (entry.value->>'$.supplyCappedPercent')::DOUBLE AS supply_capped_pct, (entry.value->>'$.MMR')::DOUBLE AS mmr, (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0 AS duration_minutes, entry.value->>'$.race' AS race, entry.value->>'$.result' AS result, EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year FROM raw, LATERAL json_each(\"ToonPlayerDescMap\") AS entry WHERE (entry.value->>'$.APM')::DOUBLE > 0" --format csv
```

**1.14B — Pairwise Spearman correlation matrix**

```python
def compute_spearman_matrix(
    df: pd.DataFrame,
    numeric_cols: list[str],
) -> pd.DataFrame:
    """Compute pairwise Spearman correlations with p-values.
    Returns DataFrame with columns: var1, var2, rho, p_value, n.
    Uses scipy.stats.spearmanr.
    """
    ...
```

**1.14C — Correlation stratified by race**

Same Spearman matrix computed separately for Terran, Protoss, and Zerg, to check whether aggregate correlations mask race-specific patterns.

**1.14D — Correlation heatmap (Python, matplotlib)**

```python
def plot_correlation_heatmap(
    corr_matrix: pd.DataFrame,
    output_path: Path,
    title: str,
) -> None:
    """Render annotated Spearman correlation heatmap."""
    ...
```

Artifacts:
- `01_14_spearman_correlations.csv`
- `01_14_spearman_by_race.csv`
- `01_14_correlation_heatmap.png`

Thesis mapping: §4.2.2 — bivariate analysis of pre-game metadata fields

Gate condition:
- Artifact check: All three files exist and are non-empty.
- Continue predicate: If the correlation matrix is computed for all available numeric field pairs, continue to Step 1.15.
- Halt predicate: If any pair of fields that would both be used as features shows |rho| > 0.95, halt Phase 1 and escalate, because near-perfect collinearity between planned features would make independent feature contribution uninterpretable and violate the thesis requirement for feature importance analysis. (Threshold source: Dormann et al. 2013, "Collinearity: a review of methods to deal with it" — 0.95 is the escalate level; values between 0.7 and 0.95 are noted but do not halt.)

[CROSS-GAME]

---

**1.15 — Distribution visualizations for numeric fields classified as active (QQ plots, KDE, ECDFs)**

Context: Manual 01 §3.4 prescribes histograms, KDE, QQ plots, and ECDFs as the standard distribution analysis toolkit. Step 1.3 produced histograms for game
duration only. This step extends visual distribution analysis to every field from Step 1.10 whose status is "active" (per the Step 1.10D classification) AND whose type is numeric (per the Step 1.10B distribution profiling). The exact field count is determined by Step 1.10's findings; the gate condition is one PNG triplet per qualifying field, no exceptions. Feeds thesis §4.2 (exploratory analysis) and Appendix B (supplementary figures).

Inputs: Numeric field data extracted in Step 1.14A. Field status from Step 1.10D.

Sub-steps:

**1.15A — Histograms + KDE, QQ plot, and ECDF per active numeric field**

```python
def plot_distribution_panel(
    series: pd.Series,
    field_name: str,
    output_dir: Path,
) -> None:
    """Generate histogram+KDE, QQ plot, and ECDF for a single numeric field.
    Produces three PNG files:
      {output_dir}/01_15_{field_name}_hist_kde.png
      {output_dir}/01_15_{field_name}_qq.png
      {output_dir}/01_15_{field_name}_ecdf.png
    """
    ...
```

For each field that is both "active" in Step 1.10D's classification AND numeric in Step 1.10B's distribution profiling:
- Histogram with KDE overlay (matplotlib + scipy.stats.gaussian_kde)
- QQ plot against normal distribution (scipy.stats.probplot) — the Manual calls this "the gold standard"
- ECDF (statsmodels ECDF or matplotlib step function)

**1.15B — Duration distribution by race**

```sql
SELECT
    entry.value->>'$.race' AS race,
    (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0 AS duration_minutes
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
WHERE entry.value->>'$.result' = 'Win';
```

```
poetry run sc2 db --dataset sc2egset query "SELECT entry.value->>'$.race' AS race, (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0 AS duration_minutes FROM raw, LATERAL json_each(\"ToonPlayerDescMap\") AS entry WHERE entry.value->>'$.result' = 'Win'" --format csv
```

Produces overlaid KDE plots by race.

Artifacts:
- One (hist_kde, qq, ecdf) PNG triplet per field that is both "active" (Step 1.10D) and numeric (Step 1.10B). The exact field list is determined at execution time by Step 1.10's findings.
- `01_15_duration_by_race_kde.png`

Thesis mapping: §4.2 — main exploratory figures; Appendix B — supplementary distribution plots

Gate condition:
- Artifact check: One (histogram+KDE, QQ, ECDF) PNG triplet exists for every field that Step 1.10D classifies as "active" AND Step 1.10B confirms as numeric. Zero exceptions. The expected fields include at minimum APM and duration; SQ, supplyCappedPercent, and any additional numeric active fields are included if Step 1.10 classifies them accordingly.
- Continue predicate: If all qualifying fields have complete visualization triplets, continue to Step 1.16.
- Halt predicate: If any active numeric field classified as PRE_GAME in Step 1.11 shows a QQ plot indicating a degenerate distribution (all values identical, or bimodal with >90% in one mode), halt Phase 1 and escalate, because a pre-game feature with degenerate distribution would have near-zero predictive value and its inclusion in the feature set must be reconsidered before Phase 7.

[CROSS-GAME]

---

**1.16 — Phase 1 consolidation: data dictionary, data quality report, risk register, modeling readiness decision**

Context: Manual 01 §6.1 requires four deliverables before proceeding to modeling phases. This step consolidates all findings from Steps 1.1 through 1.15 into
these four structured artifacts. No new analysis is performed — synthesis only. Feeds thesis §4.1 (dataset description), §3 (methodology), and the Phase 1 gate.

Inputs: All artifacts from Steps 1.1 through 1.15.

Sub-steps:

**Deliverable 1 of 4 — Data dictionary**

Filename: `01_16_data_dictionary.md` (under `src/rts_predict/sc2/reports/sc2egset/`)

Required sections:
1. Overview (one paragraph summarizing the SC2EGSet schema and this dictionary's scope)
2. Top-level columns table (one row per raw table column: filename, header, initData, details, metadata, ToonPlayerDescMap, error flags)
3. ToonPlayerDescMap fields table (one row per field from Step 1.9 inventory, with columns: field name, JSON path, data type, semantic meaning, null/zero rate from Step 1.10, temporal classification from Step 1.11, field status from Step 1.10D)
4. Top-level JSON sub-keys table (one row per sub-key discovered in Step 1.9C for header, initData, details, metadata)

Feeding artifacts: 01_09_tpdm_field_inventory.csv, 01_09_tpdm_key_set_constancy.csv, 01_09_toplevel_field_inventory.csv, 01_10_tpdm_column_profile.csv, 01_10_tpdm_field_status.csv, 01_11_temporal_leakage_classification.csv

Sign-off criterion: Every field enumerated in Step 1.9 (both ToonPlayerDescMap fields and top-level JSON sub-keys) appears in the dictionary with all required columns populated. No field has a blank data type, temporal classification, or field status cell.

```python
def compile_data_dictionary(
    field_inventory: pd.DataFrame,
    column_profiles: pd.DataFrame,
    temporal_classifications: pd.DataFrame,
) -> str:
    """Compile a data dictionary from Phase 1 profiling artifacts.
    Returns markdown string with one section per field containing:
    - Field name and JSON path
    - Data type (inferred from profiling)
    - Semantic meaning (from SC2EGSet documentation)
    - Valid range (from min/max in profiling)
    - Null/zero rate
    - Temporal classification (PRE_GAME / POST_GAME)
    - Field status (dead / constant / near-constant / active)
    - Notes and assumptions
    """
    ...
```

**Deliverable 2 of 4 — Data quality report**

Filename: `01_16_data_quality_report.md` (under `src/rts_predict/sc2/reports/sc2egset/`)

Required sections:
1. Executive summary (one paragraph with key quality metrics)
2. Missingness summary (per-field null rates, referencing 01_10_tpdm_column_profile.csv)
3. Duplicate inventory (exact and near-duplicate counts, referencing 01_01_duplicate_detection.md)
4. Structural anomaly inventory (13 anomalous replays from Step 1.1, error-flagged replays from Step 1.8)
5. Field status classification counts (dead / constant / near-constant / active breakdown, referencing 01_10_tpdm_field_status.csv)
6. Year-stratified completeness summary (referencing 01_10_tpdm_availability_by_year.csv and 01_12_field_completeness_heatmap.png)
7. Class balance confirmation (referencing 01_12_class_balance.csv)
8. Game settings verification results (referencing 01_08_game_settings_audit.md from Step 1.8)

Feeding artifacts: 01_01_corpus_summary.json, 01_01_duplicate_detection.md, 01_01_player_count_anomalies.csv, 01_04_apm_mmr_audit.md, 01_08_game_settings_audit.md, 01_08_error_flags_audit.csv, 01_10_tpdm_column_profile.csv, 01_10_tpdm_field_status.csv, 01_10_tpdm_availability_by_year.csv, 01_12_class_balance.csv, 01_12_field_completeness_heatmap.png

Sign-off criterion: Every section contains at least one quantified finding traceable to a named source artifact. No section is empty or contains only placeholder text.

**Deliverable 3 of 4 — Risk register**

Filename: `01_16_risk_register.md` (under `src/rts_predict/sc2/reports/sc2egset/`)

Required sections:
1. Overview (one paragraph explaining the register's purpose and severity scale)
2. Risk table (columns: Risk ID, Description, Severity [Critical/High/Medium/Low], Affected Phase, Mitigation, Source Step)
3. AMBIGUOUS fields appendix (one row per field classified as AMBIGUOUS in Step 1.11, with the conservative exclusion rationale from 01_11_temporal_leakage_classification.csv)

Feeding artifacts: 01_01_duplicate_detection.md (near-duplicate risk), 01_01_player_count_anomalies.csv (anomalous replay risk), 01_04_apm_mmr_audit.md (MMR missingness, APM 2016 risk), 01_11_temporal_leakage_classification.csv (temporal leakage risk, AMBIGUOUS field risk), 01_12_class_balance.csv (class balance risk if applicable), 01_08_error_flags_audit.csv (error flag risk)

Sign-off criterion: At minimum the following risks are documented: (1) temporal leakage from post-game fields (Source: Step 1.11), (2) MMR systematic missingness (Source: Step 1.4), (3) near-duplicate replay pairs (Source: Step 1.1), (4) every AMBIGUOUS field from Step 1.11. Every risk has all six table columns populated.

Seed entries:

| Risk ID | Description | Severity | Affected Phase | Mitigation | Source |
|---------|-------------|----------|----------------|------------|--------|
| R01 | Temporal leakage from post-game fields (APM, SQ, supplyCappedPercent) used as pre-game features | Critical | Phase 7 | Step 1.11 classification; Phase 7 must exclude POST_GAME fields | Step 1.11 |
| R02 | MMR systematic missingness (83.6% zero) | High | Phase 7 | Derive skill from match history (Elo/Glicko-2) | Step 1.4 |
| R03 | 88 near-duplicate replay pairs | Medium | Phase 6 | Deduplication in Phase 6 cleaning | Step 1.1 |
| R04 | 2016 APM all-zero (systematic, not MCAR) | Medium | Phase 7 | Exclude 2016 from APM features or impute | Step 1.4 |
| R05 | 13 replays with player_count != 2 | Low | Phase 6 | Exclusion rule in Phase 6 | Step 1.1 |

**Deliverable 4 of 4 — Modeling readiness decision**

Filename: `01_16_modeling_readiness.md` (under `src/rts_predict/sc2/reports/sc2egset/`)

Required sections:
1. Decision header (GO / NO-GO / CONDITIONAL GO)
2. Gate conditions checklist (explicit reference to each original gate condition (a)-(j) from the ROADMAP, stating whether met, with the artifact or finding that confirms it)
3. Risk assessment summary (reference each risk from the risk register and its mitigation status: mitigated, accepted, or unresolved)
4. Conditions for proceeding (if CONDITIONAL GO: list specific conditions that must be met before Phase 2)
5. Recommended Phase 2 priorities (based on risk register, what should Phase 2 focus on first)

Feeding artifacts: 01_16_data_dictionary.md, 01_16_data_quality_report.md, 01_16_risk_register.md (all three prior deliverables)

Sign-off criterion: The document contains an explicit GO / NO-GO / CONDITIONAL-GO decision. If GO or CONDITIONAL-GO, every original gate condition (a)-(j) is addressed with a pass/fail status and artifact reference. If CONDITIONAL-GO, at least one condition for proceeding is listed with a concrete resolution path. If NO-GO, the specific blocking finding is named.

Artifacts:
- `01_16_data_dictionary.md`
- `01_16_data_quality_report.md`
- `01_16_risk_register.md`
- `01_16_modeling_readiness.md`

Thesis mapping: §4.1 — dataset description; §4.1.2 — data quality; §3.3 — risk management; §4.1.4 — modeling readiness assessment

Gate condition:
- Artifact check: All four markdown files exist and are non-empty.
- Continue predicate: If 01_16_modeling_readiness.md contains a GO or CONDITIONAL GO decision, continue to Phase 2.
- Halt predicate: If 01_16_modeling_readiness.md contains a NO-GO decision, halt the pipeline and escalate, because the data has been assessed as unfit for the prediction task and no downstream phase can produce valid results.

[CROSS-GAME]

---

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
- `01_08_game_settings_audit.md`
- `01_08_field_completeness_summary.csv` *(superseded by Step 1.10 — not produced)*
- `01_08_error_flags_audit.csv`

### Gate

Phase 1 is complete when ALL of the following named artifacts exist under `src/rts_predict/sc2/reports/sc2egset/` and satisfy their stated quality criteria:

1. **Data Dictionary — `01_16_data_dictionary.md`**
   - Produced by: Step 1.16 (Deliverable 1 of 4)
   - Depends on: Steps 1.9, 1.10, 1.11
   - Quality criterion: Every field discovered in Step 1.9 has an entry. Every entry includes: field name, JSON path, data type, semantic meaning, valid range, null/zero rate, temporal classification, field status.

2. **Data Quality Report — `01_16_data_quality_report.md`**
   - Produced by: Step 1.16 (Deliverable 2 of 4)
   - Depends on: Steps 1.1, 1.2, 1.4, 1.8, 1.10, 1.12
   - Quality criterion: Report includes the following quantified sections: missingness summary (per-field null rates), duplicate inventory, structural anomaly inventory, field status classification counts, year-stratified completeness summary, error flag rates, game settings verification results. Every number traceable to a named artifact from an earlier step.

3. **Risk Register — `01_16_risk_register.md`**
   - Produced by: Step 1.16 (Deliverable 3 of 4)
   - Depends on: Steps 1.1, 1.4, 1.8, 1.11, 1.12, 1.13
   - Quality criterion: Every risk has an ID, description, severity, affected phase, mitigation strategy, and source step reference. At minimum: temporal leakage risk (Step 1.11), MMR missingness risk (Step 1.4), near-duplicate risk (Step 1.1), and all AMBIGUOUS fields from Step 1.11 must be documented.

4. **Modeling Readiness Decision — `01_16_modeling_readiness.md`**
   - Produced by: Step 1.16 (Deliverable 4 of 4)
   - Depends on: Steps 1.16 Deliverables 1–3 (all other deliverables)
   - Quality criterion: Contains an explicit GO / NO-GO / CONDITIONAL-GO decision with narrative justification referencing the risk register and data quality report. If CONDITIONAL-GO, lists the specific conditions.

**Prerequisite artifacts (Steps 1.1–1.15)**

| Step | Artifacts |
|------|-----------|
| 1.1 | 01_01_corpus_summary.json, 01_01_player_count_anomalies.csv, 01_01_result_field_audit.md, 01_01_duplicate_detection.md |
| 1.2 | 01_02_parse_quality_by_tournament.csv, 01_02_parse_quality_summary.md |
| 1.3 | 01_03_duration_distribution.csv, 01_03_duration_distribution_full.png, 01_03_duration_distribution_short_tail.png |
| 1.4 | 01_04_apm_mmr_audit.md |
| 1.5 | 01_05_patch_landscape.csv |
| 1.6 | 01_06_event_type_inventory.csv, 01_06_event_count_distribution.csv, 01_06_event_density_by_year.csv, 01_06_event_density_by_tournament.csv |
| 1.7 | 01_07_playerstats_sampling_check.csv |
| 1.8 | 01_08_game_settings_audit.md, 01_08_error_flags_audit.csv (note: 01_08_field_completeness_summary.csv superseded by Step 1.10 — not produced) |
| 1.9 | 01_09_tpdm_field_inventory.csv, 01_09_tpdm_key_set_constancy.csv, 01_09_toplevel_field_inventory.csv |
| 1.9D | 01_09D_tracker_event_data_field_inventory.csv, 01_09D_tracker_event_data_key_constancy.csv, 01_09D_playerstats_stats_field_inventory.csv |
| 1.9E | 01_09E_game_event_data_field_inventory.csv, 01_09E_game_event_data_key_constancy.csv |
| 1.9F | 01_09F_parquet_duckdb_schema_reconciliation.md, 01_09F_event_schema_reference.md |
| 1.10 | 01_10_tpdm_column_profile.csv, 01_10_tpdm_numeric_distributions.csv, 01_10_tpdm_categorical_topk.csv, 01_10_tpdm_field_status.csv, 01_10_tpdm_availability_by_year.csv |
| 1.11 | 01_11_temporal_leakage_classification.csv, 01_11_leakage_empirical_checks.md |
| 1.12 | 01_12_class_balance.csv, 01_12_class_balance_stratified.csv, 01_12_field_completeness_heatmap.png |
| 1.13 | 01_13_race_distribution.csv, 01_13_matchup_win_rates.csv, 01_13_matchup_win_rates_by_year.csv, 01_13_matchup_win_rates_by_tournament.csv |
| 1.14 | 01_14_spearman_correlations.csv, 01_14_spearman_by_race.csv, 01_14_correlation_heatmap.png |
| 1.15 | One (hist_kde, qq, ecdf) PNG triplet per field that Step 1.10D classifies as "active" AND Step 1.10B confirms as numeric. Zero exceptions. |

**Relationship to existing gate conditions (a)–(j)**

The existing conditions are subsumed, not replaced:
- (a)–(f): Factual statements derived from Steps 1.1–1.7 artifacts. Remain prerequisites.
- (g)–(j): Factual statements derived from Step 1.8 artifacts. Remain prerequisites.
- New gate adds: temporal leakage classification (Step 1.11), class balance confirmation (Step 1.12), bivariate analysis (Steps 1.13–1.14), distribution visualizations (Step 1.15), and the four §6.1 consolidation deliverables (Step 1.16).

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
  01_08_game_settings_audit.md
  01_08_field_completeness_summary.csv
  01_08_error_flags_audit.csv
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
