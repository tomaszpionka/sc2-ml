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

**Cross-references:** This roadmap covers the SC2 leg of the thesis. The AoE2 leg will have a parallel roadmap. Both feed into the unified thesis structure in `THESIS_STRUCTURE.md`. The scientific invariants in `scientific-invariants.md` apply at all times.

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

Output: `reports/00_source_audit.json`

**0.2 — Validate the `tournament_name` extraction logic**

Before loading any data, write a standalone Python script that:
- Scans 10 random `.SC2Replay.json` paths from each of 5 different tournament directories
- Applies `split_part(filename, '/', -3)` (simulated in Python as `path.parts[-3]`)
- Compares the result to the known tournament directory name
- Reports whether the extraction is correct for all sampled paths

If it fails for any path, fix the extraction logic in `processing.py` before proceeding.

Output: `reports/00_tournament_name_validation.txt`

**0.3 — Design and document the canonical `replay_id`**

Write a specification (a short markdown file) that defines:
- `replay_id` = the MD5 hash portion of the filename (the 32-character hex prefix before `.SC2Replay.json`)
- How to extract it from Path A's `filename` column (regex or string split)
- How to extract it from Path B's `match_id` column (the path string)
- Confirm both extractions produce identical values for the same file

This spec will be referenced by all downstream join logic.

Output: `reports/00_replay_id_spec.md`

**0.4 — Run Path A ingestion on a single tournament**

Run `move_data_to_duck_db` on a single tournament directory (e.g. `2016_IEM_10_Taipei`) as a smoke test. Then:
- Run `DESCRIBE raw` and record all column names and types
- Run `SELECT COUNT(*) FROM raw` and compare to the file count on disk for that tournament
- Verify `filename`, `header`, `initData`, `details`, `metadata`, `ToonPlayerDescMap` are all present and non-null
- Extract `tournament_name` using the validated logic from 0.2
- Extract `replay_id` using the spec from 0.3
- Spot-check 3 rows manually against the source JSON files

Output: `reports/00_path_a_smoke_test.md`

**0.5 — Run Path A ingestion on the full corpus**

Run `move_data_to_duck_db` with `should_drop=True` on the full `REPLAYS_SOURCE_DIR`. Record:
- Total rows loaded into `raw`
- Time taken
- Any errors logged

Output: `reports/00_full_ingestion_log.txt` (the pipeline log)

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

Output: `reports/00_path_b_extraction_log.txt`

**0.8 — Validate the Path A / Path B join**

Write a query that joins `raw` (Path A) to `tracker_events_raw` (Path B) on the canonical `replay_id`. Verify:
- Every `replay_id` in `tracker_events_raw` exists in `raw`
- Every `replay_id` in `raw` that has `trackerEvents` (from the audit in 0.1) has a corresponding row in `tracker_events_raw`
- Report any orphan `replay_id` values in either direction

Output: `reports/00_join_validation.md`

**0.9 — Run `load_map_translations` and verify**

Run `load_map_translations()`. Then:
- Count rows in `map_translation`
- Count distinct `metadata->>'$.mapName'` values in `raw`
- Count how many map names from `raw` have no translation (null join)
- List the untranslated map names

Output: `reports/00_map_translation_coverage.csv`

### Artifacts

- `reports/00_source_audit.json`
- `reports/00_tournament_name_validation.txt`
- `reports/00_replay_id_spec.md`
- `reports/00_path_a_smoke_test.md`
- `reports/00_full_ingestion_log.txt`
- `reports/00_path_b_extraction_log.txt`
- `reports/00_join_validation.md`
- `reports/00_map_translation_coverage.csv`

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
 
Output: `reports/01_corpus_summary.json`
Output: `reports/01_player_count_anomalies.csv` (if any anomalies found)
Output: `reports/01_result_field_audit.md`
Output: `reports/01_duplicate_detection.md`
 
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
 
Output: `reports/01_parse_quality_by_tournament.csv`
Output: `reports/01_parse_quality_summary.md` (narrative: which tournaments have >20%
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
 
Output: `reports/01_duration_distribution.csv`
Output: `reports/01_duration_distribution_full.png`
Output: `reports/01_duration_distribution_short_tail.png`
 
**1.4 — APM and MMR audit (confirmation of Phase 0 findings)**
 
Phase 0 already established:
- APM: 97.5% non-zero overall; all 2016 zeros, near-complete from 2017+
- MMR: 83.6% zero; systematically missing (tournament/lobby replays)
 
This step produces the formal report with year-by-year and league-by-league
breakdowns, suitable for thesis citation. Use the exact queries from
`research_log.md` Phase 0 entry.
 
Write `reports/01_apm_mmr_audit.md` with:
- The full year-by-year APM table
- The full year-by-year MMR table
- The MMR-by-highestLeague table
- Conclusion: APM is usable from 2017+ (with 2016 imputation needed);
  MMR is NOT usable as a direct feature — player skill must be derived
  from match history (Elo, Glicko-2, or rolling win rate)
 
Output: `reports/01_apm_mmr_audit.md`
 
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
 
Output: `reports/01_patch_landscape.csv`
 
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
 
Output: `reports/01_event_type_inventory.csv` (corpus-wide)
Output: `reports/01_event_count_distribution.csv` (per-replay distribution stats)
Output: `reports/01_event_density_by_year.csv`
Output: `reports/01_event_density_by_tournament.csv`
 
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
 
Output: `reports/01_playerstats_sampling_check.csv`
 
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
 
Output: `reports/01_game_settings_audit.md`
Output: `reports/01_field_completeness_summary.csv`
Output: `reports/01_error_flags_audit.csv` (list of replays with any error flag = true)

### Artifacts
 
- `reports/01_corpus_summary.json`
- `reports/01_player_count_anomalies.csv` (if anomalies exist)
- `reports/01_result_field_audit.md`
- `reports/01_duplicate_detection.md`
- `reports/01_parse_quality_by_tournament.csv`
- `reports/01_parse_quality_summary.md`
- `reports/01_duration_distribution.csv`
- `reports/01_duration_distribution_full.png`
- `reports/01_duration_distribution_short_tail.png`
- `reports/01_apm_mmr_audit.md`
- `reports/01_patch_landscape.csv`
- `reports/01_event_type_inventory.csv`
- `reports/01_event_count_distribution.csv`
- `reports/01_event_density_by_year.csv`
- `reports/01_event_density_by_tournament.csv`
- `reports/01_playerstats_sampling_check.csv`
- `reports/01_game_settings_audit.md`
- `reports/01_field_completeness_summary.csv`
- `reports/01_error_flags_audit.csv`

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

Output: `reports/02_nickname_toon_mapping.csv`

**2.4 — Detect and classify multi-toon cases**

For each nickname with `n_toons > 1`, classify as:

- **Server switch (safe to merge):** Toons from different regions but overlapping date ranges. Same player, different server. Canonical identity = nickname.
- **Rename (requires investigation):** Toons from the same region but different time periods (one toon ends, another begins). Could be a player rename or coincidental nickname collision.
- **Ambiguous (flag):** Cannot be determined automatically. List manually.

Output: `reports/02_multi_toon_cases.csv` with a `classification` column
Output: `reports/02_ambiguous_nicknames.md` — manual review list

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

Output: `reports/02_player_coverage.md`
Output: `reports/02_games_per_player_histogram.png`
Output: `reports/02_top_players.csv`

**2.7 — Race consistency per player**

For each canonical player, compute:
- Primary race (mode of `race` across all appearances)
- Fraction of games played as each race
- Flag players with > 5% games not as their primary race (race switchers)

Output: `reports/02_player_race_consistency.csv`

### Artifacts

- DuckDB table: `player_appearances`
- DuckDB table: `canonical_players`
- `reports/02_nickname_toon_mapping.csv`
- `reports/02_multi_toon_cases.csv`
- `reports/02_ambiguous_nicknames.md`
- `reports/02_player_coverage.md`
- `reports/02_games_per_player_histogram.png`
- `reports/02_top_players.csv`
- `reports/02_player_race_consistency.csv`

### Gate

`canonical_players` table exists. Every toon in `player_appearances` is assigned a `player_canonical_id`. The ambiguous nickname list is reviewed — even if the decision is "flag as uncertain and keep." You can state precisely how many unique professionals are in the dataset and what the game count distribution looks like.

**Thesis mapping:** §4.2.2 — Player identity resolution

---

## Phase 3 — Games table construction and temporal structure

**Context:** The `matches_flat` view in `processing.py` already pairs players within the same game. However, it produces **two rows per game** (one per perspective — p1 vs p2, then p2 vs p1). This phase constructs the canonical `games` table (one row per unique match), establishes correct temporal ordering per player, and validates that the data supports the sliding-window prediction framing.

**Critical design decision — symmetric player ordering:** In the `games` table, players are assigned to slots `player_a` and `player_b` using lexicographic ordering of canonical nicknames (LEAST/GREATEST). This is an arbitrary but consistent convention. At prediction time, the model receives features for a **focal player** and an **opponent** — the same feature computation pipeline runs for both perspectives. Neither player slot is privileged (Scientific Invariant #8).

**Inputs:** `raw` table, `player_appearances`, `canonical_players`, `map_translation`.

### Steps

**3.1 — Run `create_ml_views` to build `flat_players` and `matches_flat`**

Run `create_ml_views(con)`. Then immediately validate the output:
- Count rows in `flat_players` (should be exactly 2× the number of valid 1v1 replays)
- Count rows in `matches_flat` — determine exact multiplicity and document it
- Count distinct `match_id` values in `matches_flat`
- Check for any `match_id` with unexpected row count — these are data anomalies

Document the actual multiplicity explicitly so there is no ambiguity when building features.

**3.2 — Build the canonical `games` table**

Create a DuckDB table `games` with **one row per unique replay**, collapsing the two-perspective structure:

```sql
CREATE TABLE games AS
SELECT
    match_id,
    replay_id,         -- MD5 hash
    tournament_dir,
    match_time,
    game_loops,
    -- Both time representations, clearly labelled
    ROUND(game_loops / 22.4 / 60.0, 2) AS duration_real_minutes,
    ROUND(game_loops / 16.0 / 60.0, 2) AS duration_game_minutes,
    map_name,
    map_size_x,
    map_size_y,
    data_build,
    game_version,
    -- Player A is always the lexicographically smaller name (consistent ordering)
    LEAST(p1_name, p2_name) AS player_a_name,
    GREATEST(p1_name, p2_name) AS player_b_name,
    -- Race assignment follows the same ordering
    CASE WHEN p1_name < p2_name THEN p1_race ELSE p2_race END AS player_a_race,
    CASE WHEN p1_name < p2_name THEN p2_race ELSE p1_race END AS player_b_race,
    -- Winner
    CASE
        WHEN p1_result = 'Win' AND p1_name < p2_name THEN p1_name
        WHEN p1_result = 'Win' AND p1_name > p2_name THEN p2_name
        ELSE -- p1 lost
            CASE WHEN p1_name < p2_name THEN p2_name ELSE p1_name END
    END AS winner_name
FROM matches_flat
WHERE p1_name < p2_name  -- deduplicate: take only one perspective
```

Join to `canonical_players` to add `player_a_canonical_id`, `player_b_canonical_id`, and `winner_canonical_id`.

**Do NOT add an `is_valid` flag here.** Duration thresholds are determined in Phase 6 based on empirical evidence from Phase 1. Premature filtering violates the data-driven analysis principle.

**3.3 — Tournament timeline**

For each `tournament_dir` in `games`:
- First and last `match_time`
- Duration in days
- Number of unique players
- Number of games
- Year extracted from first match time

Sort chronologically. Verify that the tournament directory name years align with the actual timestamps (e.g. `2016_IEM_10_Taipei` should have matches in early 2016).

Output: `reports/03_tournament_timeline.csv`

**3.4 — Per-player career sequence**

For each canonical player, using `games` joined to `canonical_players`:
- Sort all their games by `match_time`
- Assign `career_game_seq` (1 = first ever recorded game)
- Compute `days_since_prev_game` (null for first game)
- Flag gaps > 180 days (possible retirement or injury break)

Store as DuckDB table `player_career_sequence`.

**3.5 — Within-tournament game sequence per player**

For each (player, tournament) pair:
- Sort games within that tournament by `match_time`
- Assign `within_tournament_seq` (1 = first game in that tournament for that player)
- Compute `minutes_since_prev_game_in_tournament` (null for first game)
- Flag any within-tournament gap < 1 minute (timestamp collision risk)
- Flag any within-tournament gap > 24 hours (multi-day event — legitimate)

Store in `player_career_sequence` as additional columns.

Output: `reports/03_timestamp_collision_report.csv` — list any sub-1-minute within-player gaps

**3.6 — Sliding-window feasibility analysis**

This is the most important step in this phase. For each canonical player, enumerate all valid `(history_window, target_game)` pairs where:
- Target game = game N in the player's career sequence
- History window = games 1 through N-1 (all prior games)

For each player, count:
- Total number of games (potential prediction targets)
- Number of targets where prior career games < 3 (cold-start: very little history)
- Number of targets where prior career games >= 3 (usable)
- Number of targets where the player also has ≥ 1 prior game **within the same tournament** (within-tournament conditioning available)
- Number of targets where the player has **only pre-tournament history** (no within-tournament context)

Aggregate across all players. This tells you: how many total training examples exist, how many are cold-start, and how often within-tournament context is available.

Output: `reports/03_sliding_window_feasibility.csv` (per player)
Output: `reports/03_sliding_window_summary.md` (aggregate stats — total examples, cold-start fraction, within-tournament context availability)

**3.7 — Head-to-head history analysis**

For each canonical player pair (A, B) where A < B alphabetically:
- Total games played against each other
- Chronological order of those games
- Earliest and latest match date

This establishes whether head-to-head history is a viable feature (requires at least some pairs playing each other multiple times).

Output: `reports/03_head_to_head_coverage.csv`

### Artifacts

- DuckDB table: `games`
- DuckDB table: `player_career_sequence`
- `reports/03_tournament_timeline.csv`
- `reports/03_timestamp_collision_report.csv`
- `reports/03_sliding_window_feasibility.csv`
- `reports/03_sliding_window_summary.md`
- `reports/03_head_to_head_coverage.csv`

### Gate

`games` table exists with exactly one row per replay and `player_a_canonical_id`, `player_b_canonical_id`, `winner_canonical_id` populated. The sliding-window feasibility report exists and you can state: (a) total prediction examples available, (b) cold-start proportion, (c) how often within-tournament context is available.

**Thesis mapping:** §4.2, §4.4.1 — Temporal structure and prediction framing

---

## Phase 4 — In-game statistics extraction and profiling

**Context:** The `player_stats` view in `ingestion.py` already extracts the 39 `PlayerStats` economic fields from `tracker_events_raw`. But it has not been profiled — we do not yet know which fields carry signal, whether sampling is regular, or what the distributions look like. This phase also extracts unit and upgrade events. Nothing here is feature engineering — this is raw value profiling.

**Inputs:** `tracker_events_raw` table, `games` table, `player_appearances`.

### Steps

**4.1 — Validate the `player_stats` view**

The `player_stats` view filters `tracker_events_raw` to `event_type = 'PlayerStats'` and extracts 39 typed columns.

Validate:
- Total rows in `player_stats`
- Distinct `match_id` values — should match `games` count
- Rows per match per player — should be approximately `game_loops / 160` per player (one snapshot every ~160 loops ≈ 7.14 real-time seconds at Faster speed)
- Distribution of row counts per match (min, median, max, p5, p95)
- Null rate per column — any of the 39 fields that are systematically null are dead

Output: `reports/04_player_stats_validation.md`

**4.2 — Sampling regularity check**

For 200 randomly sampled games, check that `PlayerStats` events are sampled at regular `~160 loop` intervals:
- For each game and player, sort events by `game_loop` and compute `diff(game_loop)`
- Distribution of diffs — should cluster tightly at 160
- Flag any game where mean diff deviates > 20% from 160 (irregular sampling)
- Flag any game with gaps > 500 loops (missed snapshots)

Note: 160 loops ÷ 22.4 loops/s = 7.14 real-time seconds per snapshot.

Output: `reports/04_sampling_regularity.csv`

**4.3 — Null and zero inflation per field**

For all 39 `player_stats` fields across the full corpus, compute:
- Fraction of rows that are null
- Fraction of rows that are exactly 0
- Mean, std, p5, p25, p75, p95 for non-null non-zero values

Fields where > 95% of values are 0 across all games are dead features. Document them explicitly.

Output: `reports/04_field_inflation.csv`

**4.4 — Winner vs. loser separability analysis**

This is the key statistical analysis for feature selection.

Join `player_stats` to `games` to label each player's snapshots as winner or loser.

Select canonical timepoints using the real-time conversion table from the
Reference section above. The timepoints should reflect meaningful game stages:

| Timepoint name | Real-time | Game loops | Rationale |
|---|---|---|---|
| `early_game` | ~3 min | ~4,032 | Post-opening, pre-expansion |
| `mid_game_1` | ~7 min | ~9,408 | First significant economic divergence |
| `mid_game_2` | ~12 min | ~16,128 | Mid-game army composition set |
| `late_game` | ~20 min | ~26,880 | Late-game macro differences |
| `final` | last snapshot | varies | End-of-game state |

For each timepoint: find the closest `PlayerStats` snapshot (nearest `game_loop`).

For each surviving (non-dead) field, compute:
- Mean for winners, mean for losers
- Cohen's d = (mean_winner - mean_loser) / pooled_std
- Two-sided t-test p-value (Bonferroni-corrected for number of fields tested)

Sort by Cohen's d descending. Fields with |Cohen's d| < 0.1 at all timepoints are weak and should be deprioritised.

Output: `reports/04_winner_loser_separability.csv`
Output: `reports/04_separability_heatmap.png` — heatmap: fields × timepoints, colour = Cohen's d

**4.5 — Extract and profile `UnitBorn` and `UnitDied` events**

From `tracker_events_raw`, filter to `event_type IN ('UnitBorn', 'UnitDied')`.

For each event, extract from `event_data` JSON:
- `unit_type_name`
- `control_player_id`
- `killer_player_id` (for UnitDied only)
- `game_loop`
- x, y coordinates

Build a table `unit_events` in DuckDB.

Then build a unit type taxonomy CSV `data/unit_type_taxonomy.csv`:
- List all distinct `unit_type_name` values across a sample of 500 games
- Classify each as: `worker`, `army_ground`, `army_air`, `building`, `neutral_destructible`, `other`
- Note which race produces each unit type (source: Liquipedia unit pages)

This taxonomy is used in Phase 7 feature engineering.

Output: DuckDB table `unit_events`
Output: `data/unit_type_taxonomy.csv`
Output: `reports/04_unit_type_profile.csv` — counts of each unit type born/died across the sample

**4.6 — Extract and profile `Upgrade` events**

From `tracker_events_raw`, filter to `event_type = 'Upgrade'`. Extract `upgrade_type_name`, `player_id`, `game_loop` from `event_data`.

Build DuckDB table `upgrade_events`. Then compute:
- Top 50 most frequent upgrades overall
- Median `game_loop` timing for each upgrade (converted to real-time minutes)
- Per-race breakdown: which upgrades are exclusively Terran/Protoss/Zerg?

Output: DuckDB table `upgrade_events`
Output: `reports/04_upgrade_timings.csv`

**4.7 — Build order fingerprinting (exploratory)**

For each game and player, extract the first 10 non-worker, non-neutral `UnitBorn` events (ordered by `game_loop`) as the build order prefix.

Compute:
- 20 most common build order prefixes per matchup (ZvT, ZvP, TvP, ZvZ, TvT, PvP)
- This is not a feature yet — it establishes build order diversity and whether it's feasible to use build orders as features

Output: `reports/04_build_order_analysis.md`

### Artifacts

- `reports/04_player_stats_validation.md`
- `reports/04_sampling_regularity.csv`
- `reports/04_field_inflation.csv`
- `reports/04_winner_loser_separability.csv`
- `reports/04_separability_heatmap.png`
- DuckDB table: `unit_events`
- `data/unit_type_taxonomy.csv`
- `reports/04_unit_type_profile.csv`
- DuckDB table: `upgrade_events`
- `reports/04_upgrade_timings.csv`
- `reports/04_build_order_analysis.md`

### Gate

You have a ranked list of which of the 39 PlayerStats fields show the strongest winner/loser separation at which timepoints. You have a unit type taxonomy. You know which fields are dead (all zeros). These findings directly determine which features to engineer in Phase 7.

**Thesis mapping:** §4.3.2 — SC2-specific in-game features

---

## Phase 5 — Map, meta-game, and matchup analysis

**Context:** Win/loss prediction in SC2 is heavily confounded by race matchup (ZvT, TvP, etc.), map pool, and game version (balance patches). This phase quantifies those confounds so they can be handled correctly in the model — either as control features or by stratifying the evaluation.

**Inputs:** `games` table, `player_appearances`, `map_translation`.

### Steps

**5.1 — Map pool by year**

For each calendar year, list the distinct `map_name` values that appear in `games` and their game counts. SC2 map pools rotate each competitive season.

Output: `reports/05_map_pool_by_year.csv`

**5.2 — Win rate by map and matchup**

For each (map_name, player_a_race, player_b_race) combination where we use canonical matchup ordering (alphabetically smaller race first, e.g. PvT not TvP):
- Total games
- Win rate for the first-listed race
- 95% Wilson confidence interval

Filter to combinations with ≥ 20 games. Flag combinations where win rate is outside [0.40, 0.60].

Output: `reports/05_map_matchup_winrates.csv`

**5.3 — Overall matchup balance by patch era**

Group replays into broad patch eras using the `game_version` landscape from Phase 1. For each (matchup, era) pair:
- Game count
- Win rate for race A
- 95% Wilson confidence interval

This tells you whether patch version is a necessary control variable in the model.

Output: `reports/05_matchup_balance_by_era.csv`

**5.4 — Map size vs. game duration correlation**

Compute `map_area = map_size_x * map_size_y` for each game. Scatter plot and Pearson correlation between map_area and `duration_real_minutes`.

Output: `reports/05_map_size_duration_correlation.png`

**5.5 — Race representation by tournament type**

Some tournaments (WCS Korea, GSL) skew toward Korean pros and thus Terran/Zerg. Others (WCS Global) have more diverse representation. Compute race proportion per tournament.

Output: `reports/05_race_representation_by_tournament.csv`

**5.6 — Decision document: required control features**

Write a short decision document answering:
1. Is map identity a necessary model feature? (Yes/No + evidence from 5.2)
2. Is patch era a necessary model feature? (Yes/No + evidence from 5.3)
3. Is race matchup encoded in the model or evaluated stratified? (Decision + rationale)

Output: `reports/05_control_feature_decisions.md`

### Artifacts

- `reports/05_map_pool_by_year.csv`
- `reports/05_map_matchup_winrates.csv`
- `reports/05_matchup_balance_by_era.csv`
- `reports/05_map_size_duration_correlation.png`
- `reports/05_race_representation_by_tournament.csv`
- `reports/05_control_feature_decisions.md`

### Gate

`reports/05_control_feature_decisions.md` exists and contains explicit yes/no decisions with supporting evidence. These decisions are locked in before feature engineering begins.

**Thesis mapping:** §4.1.1 context (meta-game confounds), §4.3.1 (control features)

---

## Phase 6 — Data cleaning and valid game corpus

**Context:** Based on all findings from Phases 1–5, this phase applies explicit, documented cleaning rules to produce the clean game corpus. Every exclusion is logged with its reason. No data is deleted — all exclusions are implemented as filters (a `games_clean` view). This is a thesis-auditable step.

**Critical principle:** Every threshold must be justified by either (a) empirical evidence from earlier phases, or (b) a cited precedent from the literature. No magic numbers.

**Inputs:** All tables and reports from Phases 1–5.

### Steps

**6.1 — Write the cleaning rules document**

Before touching any data, write `reports/06_cleaning_rules.md`. Each rule must reference which Phase finding motivates it:

| Rule ID | Condition | Action | Motivation |
|---------|-----------|--------|------------|
| R1 | `duration_real_minutes < T_min` (threshold T_min derived from Phase 1.3 distribution) | exclude | Phase 1.3: short-game tail analysis. T_min should be chosen based on the observed distribution, annotated game-play landmarks, and precedent (Wu et al. 2017 used 7 min; Białecki et al. 2023 used 9 min). Document the exact choice and its justification. |
| R2 | No rows in `tracker_events_raw` for this `replay_id` | exclude | Phase 1.1: no event data, cannot compute in-game features |
| R3 | Player count per game ≠ 2 (after observer/caster exclusion) | exclude | Not a valid 1v1 game |
| R4 | Either player's `result` not in {Win, Loss} | exclude | No ground truth label |
| R5 | Race is not in {Terr, Prot, Zerg} (e.g. BW exhibition, Random) | exclude | Non-standard race |
| R6 | Tournament `event_coverage_pct < 20%` (from Phase 1.2) | flag whole tournament | Insufficient data quality |
| R7 | Player appears only with ambiguous identity (unresolved from Phase 2.4) | flag game | Degraded player identity confidence |

Add any additional rules discovered during exploration.

**6.2 — Apply rules and create `games_clean` view**

Create a DuckDB view (not a copy) `games_clean` that filters `games` using all rules. Add an `exclusion_reason` column to the base `games` table explaining why each excluded game was removed.

**6.3 — Cleaning impact report**

For each rule, report:
- Games excluded by this rule (and this rule alone — not already excluded by a higher-priority rule)
- Tournaments affected
- Players who lose the most games due to each rule

Output: `reports/06_cleaning_impact.md`

**6.4 — Final clean corpus statistics**

On `games_clean`:
- Total games
- Total unique players
- Total tournaments
- Date range
- Games per year
- Overall win rate (sanity check: should be exactly 0.500, since every game has one winner and one loser)
- Matchup distribution (ZvT, ZvP, TvP, ZvZ, TvT, PvP counts and percentages)

Output: `reports/06_clean_corpus_summary.md`

### Artifacts

- `reports/06_cleaning_rules.md`
- DuckDB view: `games_clean`
- `reports/06_cleaning_impact.md`
- `reports/06_clean_corpus_summary.md`

### Gate

`games_clean` view exists. Overall win rate is exactly 0.500. Cleaning impact is documented. Every exclusion has a documented rule ID with a traceable justification (Phase finding or literature reference).

**Thesis mapping:** §4.2.3 — Preprocessing and quality filtering

---

## Phase 7 — Feature engineering

**Context:** With the data exploration complete and the clean corpus established, feature engineering can begin. Features fall into two groups:

- **Group A — Pre-game features:** Available before the match starts — player history, opponent history, head-to-head, derived skill rating, map, matchup. These are the **common feature set** that can also be computed for AoE2 (using civilisation instead of race, Elo instead of derived Glicko, etc.). This is the primary model.
- **Group B — In-game snapshot features:** From `PlayerStats` at canonical timepoints. SC2-only (AoE2 has no equivalent). Secondary experiment.

Do not mix groups A and B in the same model without understanding the temporal position they represent.

**Symmetric player treatment (Scientific Invariant #8):** Every feature must be computed identically for both players. The model input for a given game is structured as (focal_player_features, opponent_features, context_features), where the same function produces features for both perspectives.

**Inputs:** `games_clean`, `player_career_sequence`, `player_stats` view, `unit_events`, `upgrade_events`, `canonical_players`, all reports from Phases 1–5.

### Steps

**7.1 — Define the feature groups formally**

Write `reports/07_feature_specification.md` before writing any feature code:

**Group A — Pre-game features (predict before the game begins)**

Per-player features (computed for both focal and opponent):
- Derived skill rating: Elo or Glicko-2, computed from the player's match history
  strictly before the target game (Scientific Invariant #3). Starting rating, K-factor
  or RD parameters should be documented and tuned.
  [Reference: Glickman 2001; EsportsBench shows Glicko-2 at 80.13% for SC2]
- Games played in last 30 days, last 90 days, last 365 days
- Overall career win rate (all prior games)
- Win rate in last 10 / 20 / 50 games (rolling window)
- Win rate vs. the specific opponent's race (all prior games vs. that race)
- Win rate on this specific map (historical)
- Head-to-head record against this specific opponent (all prior games)
- Within-tournament momentum: win/loss record in current tournament so far (games 1..M)
- Career summary: total career games, career span in days
- APM: mean APM from last 10 games (available from 2017+; imputed for 2016)

Context features (per-game, not per-player):
- Race matchup encoding (one-hot for the 6 matchup types)
- Map features: map_name (one-hot or hashed), map_size_x, map_size_y
- Patch era encoding (from Phase 5 decision)
- Rating differential: focal_rating - opponent_rating

**Group B — In-game snapshot features (SC2 only)**
- From `player_stats` at the canonical timepoints from Phase 4.4:
  all surviving non-dead fields with |Cohen's d| > 0.2
- Differential features: focal_player_stat - opponent_stat at each timepoint
- Note: both players' stats are computed from the same game state —
  neither perspective is privileged

**7.2 — Implement derived skill ratings**

Before computing other features, implement an Elo or Glicko-2 rating system
that processes the full `games_clean` corpus chronologically:

- For each game in chronological order, update both players' ratings
- The rating **before** the game is the feature value (strict temporal discipline)
- Store the full rating history as a table: `player_rating_history`
  (columns: player_canonical_id, game_id, rating_before, rating_after, ...)
- Validate: the implied prediction accuracy from ratings alone (P(higher-rated wins))
  should approximate the ~80% reported by EsportsBench for Glicko-2 on SC2

Output: DuckDB table `player_rating_history`
Output: `reports/07_rating_system_validation.md`

**7.3 — Implement Group A feature computation**

All Group A features must be computed with **strict temporal discipline**: for any target game at time T, only information from games where `match_time < T` may be used (Scientific Invariant #3).

Implement as a Python function `compute_pre_game_features(games_clean, player_career_sequence, player_rating_history, target_game_id, focal_player_id)` that returns a feature vector for a given target game and focal player. Then vectorise over all games in `games_clean`, computing features for **both** players in each game (two rows per game — one per perspective).

Key implementation constraint: use `player_career_sequence` with `career_game_seq < target_seq` filters — never a naïve `.shift()` on a DataFrame that could leak future information.

Output: `data/features_group_a.parquet` — two rows per game (one per player perspective)

**7.4 — Implement Group B feature computation (SC2-only experiment)**

For the in-game model variant, compute PlayerStats features at each canonical timepoint per game.

Apply the surviving fields list from Phase 4 (|Cohen's d| > 0.2). Compute differential columns (focal_player_stat - opponent_stat).

Output: `data/features_group_b.parquet`

**7.5 — Feature validation**

For the Group A features:
- Null rate per feature column — document and handle (impute with career-prior mean, or use 0 for cold-start players with no prior games)
- Distribution checks: any features with extreme skew should be documented; consider log-transform or clipping if needed
- **Temporal leakage check:** for a random sample of 20 target games, manually verify that no feature value for that game depends on any event at or after `match_time` of the target game. Print the feature values alongside the data that produced them.
- **Symmetry check:** verify that for a sample of games, swapping focal and opponent player produces the expected mirror of feature values (e.g., focal_win_rate for player A = opponent_win_rate when player B is focal)

Output: `reports/07_feature_validation.md`

**7.6 — Build the prediction target table**

Create the final ML-ready table combining features and labels:

| column | description |
|--------|-------------|
| `game_id` | the game being predicted |
| `focal_player_id` | the canonical player we are predicting for |
| `opponent_player_id` | the opponent |
| `focal_player_name` | for human readability |
| `opponent_player_name` | for human readability |
| `within_tournament_context_games` | prior games by focal player in this tournament |
| `career_prior_games` | total prior career games for focal player |
| [all Group A feature columns] | prefixed `focal_` and `opp_` for per-player features |
| `label` | 1 if focal player won, 0 if lost |
| `split` | train / val / test (assigned in Phase 8) |

**Note on class balance:** Since each game produces two rows (one per perspective), the overall label distribution is exactly 50/50 by construction. This is intentional and correct.

Output: `data/ml_dataset.parquet`

### Artifacts

- `reports/07_feature_specification.md`
- DuckDB table: `player_rating_history`
- `reports/07_rating_system_validation.md`
- `data/features_group_a.parquet`
- `data/features_group_b.parquet` (if implemented)
- `reports/07_feature_validation.md`
- `data/ml_dataset.parquet`

### Gate

`ml_dataset.parquet` exists. Temporal leakage check passed for sampled games. Symmetry check passed. Null rates documented and handled. Rating system validated. `reports/07_feature_specification.md` explicitly distinguishes Group A (pre-game) from Group B (in-game) features.

**Thesis mapping:** §4.3 — Feature engineering

---

## Phase 8 — Train/val/test split construction

**Context:** This is where the correct splitting strategy from the thesis design is implemented. The naïve global temporal split in `processing.py` is replaced with a per-player temporal split (Scientific Invariant #1).

**Inputs:** `data/ml_dataset.parquet`, `games_clean`, `player_career_sequence`.

### Steps

**8.1 — Implement the correct split strategy**

The split logic is:

- **Test set:** For each canonical player, their last tournament appearance. All games in that tournament where the player is the focal player go to test.
- **Validation set:** For each canonical player, their second-to-last tournament appearance (same logic).
- **Training set:** All remaining games.

Implementation notes:
- A game can appear in both player A's training and player B's test set (if they played at different points in their respective careers). This is correct behaviour — the split is per-player, not per-game (Scientific Invariant #1).
- Players with fewer than 3 tournament appearances cannot have separate train/val/test — flag them as cold-start and exclude from validation/test, keep in training only.

**8.2 — Validate the split**

For the new split:
- No player's test target is temporally before their training data
- No player's validation target is temporally before their training data
- Class balance (win rate) in train, val, test — should each be ~0.500 (guaranteed by symmetric two-row design)
- Distribution of `within_tournament_context_games` in test: how often does the model have 0, 1, 2, 3+ prior games in the target tournament?
- Size of each split: number of examples

Output: `reports/08_split_validation.md`

**8.3 — Baseline win rate by split**

For each split, compute win rate by matchup (ZvT, TvP, etc.). If any matchup in test has win rate significantly different from 0.5, it is a potential confound.

Output: `reports/08_split_matchup_balance.csv`

**8.4 — Compare to the naïve global split**

For reference, document what the old `create_temporal_split` would have produced vs. the new per-player split. Include: split sizes, matchup balance, cold-start proportion, within-tournament context availability.

This comparison goes into the thesis methodology section as justification for the new approach.

Output: `reports/08_split_comparison.md`

### Artifacts

- `data/ml_dataset.parquet` (updated with correct `split` column)
- `reports/08_split_validation.md`
- `reports/08_split_matchup_balance.csv`
- `reports/08_split_comparison.md`

### Gate

Split is validated. No temporal leakage. Class balance ~0.500 in each split. The split comparison document exists.

**Thesis mapping:** §4.4.1 — Train/validation/test split strategy

---

## Phase 9 — Baseline models and sanity checks

**Context:** Before training any serious model, establish baselines that any real model must beat. Also run sanity checks to confirm the dataset and features are not trivially broken.

**Inputs:** `data/ml_dataset.parquet` with correct split.

### Steps

**9.1 — Implement and evaluate baselines**

- **Random baseline:** Predicts win probability = 0.5 always. Accuracy = 50%.
- **Race-matchup baseline:** Predicts the historically more winning race for each matchup. Uses only training set matchup win rates.
- **Elo/Glicko-2 rating baseline:** Predicts the higher-rated player wins.
  This is the primary strength-of-schedule baseline.
  [Reference: EsportsBench reports 80.13% for Glicko-2 on Aligulac SC2 data]
- **Recent form baseline:** Predicts the player with the higher win rate in their last 10 career games wins.
- **Head-to-head baseline:** Predicts based on prior head-to-head record. Falls back to recent form if no prior H2H exists.

Evaluate each baseline on the test set: accuracy, log-loss, ROC-AUC, per-matchup accuracy, calibration (Brier score).

Output: `reports/09_baseline_results.md`

**9.2 — Sanity check: permutation test**

Shuffle the `label` column randomly (keeping all features intact). Train a logistic regression on shuffled labels. Confirm it achieves ~50% accuracy. This verifies the training pipeline is not broken.

**9.3 — Sanity check: perfect feature leakage test**

Create a "cheat" feature: the actual in-game outcome stat from the final `PlayerStats` snapshot (e.g. `mineralsCurrent` differential at game end). Train a model on this. It should achieve near-100% accuracy. This verifies that the pipeline can distinguish signal from noise and that the join between features and labels is correct.

Output: `reports/09_sanity_checks.md`

### Artifacts

- `reports/09_baseline_results.md`
- `reports/09_sanity_checks.md`

### Gate

At least one baseline beats random (otherwise the features contain no signal). The Glicko-2 baseline should be in the 75–82% range (consistent with EsportsBench). Permutation test achieves ~50%. Leakage test achieves near-100%. All sanity checks documented.

**Thesis mapping:** §5.1.1 — SC2 baselines and sanity validation

---

## Phase 10 — Model training and evaluation

**Context:** With clean features, a correct split, and validated baselines, train the primary models. Start simple and add complexity only if justified by validation performance.

**Inputs:** `data/ml_dataset.parquet`, baseline results from Phase 9.

### Steps

**10.1 — Logistic Regression (interpretable baseline)**

Train with Group A features, evaluate on val set. Record: accuracy, log-loss, ROC-AUC, per-matchup accuracy, calibration curve. Inspect top feature weights — do they make domain sense? (e.g., rating differential should be the strongest predictor)

**10.2 — Random Forest**

Train with Group A features, tune on val set. Record same metrics plus feature importances. This tests whether non-linear interactions improve over LR.

**10.3 — Gradient Boosted Trees (LightGBM or XGBoost)**

Train with Group A features, tune on val set (learning rate, depth, regularisation). Evaluate on test set only after hyperparameter selection is finalised. Record same metrics plus feature importances via SHAP.

**10.4 — Feature ablation study**

Train best-performing model with each feature group removed in turn:
- Without derived skill ratings (Elo/Glicko)
- Without within-tournament context features
- Without head-to-head history
- Without career-level stats (win rate, activity)
- Without control features (map, matchup)

Report accuracy drop for each ablation. This answers which feature groups matter most.

Output: `reports/10_ablation_results.md`

**10.5 — Per-matchup evaluation**

For the best model, evaluate separately on ZvT, ZvP, TvP, ZvZ, TvT, PvP subsets of the test set. Are some matchups harder to predict than others?

**10.6 — Cold-start analysis**

Stratify test set by `career_prior_games` (0–5, 6–20, 21–50, 51+). How does model accuracy vary with career history length? This directly addresses the cold-start problem (Research Question RQ4).

**10.7 — In-game prediction experiment (Group B features, SC2 only)**

Using Group B features (PlayerStats at canonical timepoints), train LightGBM at each timepoint. Plot accuracy as a function of real-time game elapsed. Compare to the pre-game model. This produces the "accuracy over time" curve common in the esports prediction literature.

[Reference: Hodge et al. 2021 showed 85% at 5 min for Dota 2; SC2 literature shows accuracy increasing monotonically with game time]

**10.8 — Optional: GNN experiment**

If time permits, implement the GNN model from the existing `sc2/gnn` code. Compare to the tabular models. The key thesis question is: does modelling the player interaction graph add anything beyond the tabular features?

Output: `reports/10_model_results.md`
Output: `reports/10_ablation_results.md`
Output: `reports/10_per_matchup_results.csv`
Output: `reports/10_cold_start_analysis.csv`
Output: `reports/10_ingame_accuracy_curve.png` (if 10.7 done)

### Artifacts

- `reports/10_model_results.md`
- `reports/10_ablation_results.md`
- `reports/10_per_matchup_results.csv`
- `reports/10_cold_start_analysis.csv`
- `reports/10_ingame_accuracy_curve.png`

### Gate

Best model accuracy > best baseline accuracy (otherwise the ML is not adding value). Ablation results document which features drive performance. Results are ready for the thesis Chapter 5.

**Thesis mapping:** §5.1.2–5.1.4 — SC2 experimental results

---

## Appendix — Artifact index

All reports land in `reports/`. All data files land in `data/`. Logs land in `logs/`.

```
reports/
  00_source_audit.json
  00_tournament_name_validation.txt
  00_replay_id_spec.md
  00_path_a_smoke_test.md
  00_full_ingestion_log.txt
  00_path_b_extraction_log.txt
  00_join_validation.md
  00_map_translation_coverage.csv
  01_corpus_summary.json
  01_parse_quality_by_tournament.csv
  01_parse_quality_summary.md
  01_duration_distribution.csv
  01_duration_distribution_full.png
  01_duration_distribution_short_tail.png
  01_apm_mmr_audit.md
  01_patch_landscape.csv
  01_event_type_inventory.csv
  02_nickname_toon_mapping.csv
  02_multi_toon_cases.csv
  02_ambiguous_nicknames.md
  02_player_coverage.md
  02_games_per_player_histogram.png
  02_top_players.csv
  02_player_race_consistency.csv
  03_tournament_timeline.csv
  03_timestamp_collision_report.csv
  03_sliding_window_feasibility.csv
  03_sliding_window_summary.md
  03_head_to_head_coverage.csv
  04_player_stats_validation.md
  04_sampling_regularity.csv
  04_field_inflation.csv
  04_winner_loser_separability.csv
  04_separability_heatmap.png
  04_unit_type_profile.csv
  04_upgrade_timings.csv
  04_build_order_analysis.md
  05_map_pool_by_year.csv
  05_map_matchup_winrates.csv
  05_matchup_balance_by_era.csv
  05_map_size_duration_correlation.png
  05_race_representation_by_tournament.csv
  05_control_feature_decisions.md
  06_cleaning_rules.md
  06_cleaning_impact.md
  06_clean_corpus_summary.md
  07_feature_specification.md
  07_rating_system_validation.md
  07_feature_validation.md
  08_split_validation.md
  08_split_matchup_balance.csv
  08_split_comparison.md
  09_baseline_results.md
  09_sanity_checks.md
  10_model_results.md
  10_ablation_results.md
  10_per_matchup_results.csv
  10_cold_start_analysis.csv
  10_ingame_accuracy_curve.png

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
