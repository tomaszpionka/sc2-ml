# SC2ML Thesis — Data Pipeline & Exploration Roadmap

**Goal:** Win/loss prediction in professional StarCraft II using game-state time-series data  
**Dataset:** SC2EGSet — 70+ tournaments, ~20 000 replays, 2016–2024  
**Stack:** DuckDB · Python · pandas · PyArrow · scikit-learn · PyTorch (later phases)  
**Rule:** Every phase ends with mandatory artifacts. Claude Code must not advance to the next phase until all artifacts exist and the gate condition is explicitly met. Each phase maps to a thesis chapter section.

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

---

## Phase 0 — Ingestion audit and raw table design

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

**Thesis mapping:** Appendix — Data acquisition and preprocessing infrastructure

---

## Phase 1 — Corpus inventory and parse quality

**Context:** Before exploring any values, establish the total scope and health of the dataset. This phase is read-only — no cleaning decisions are made yet, only observations recorded. The output of this phase is the factual foundation for the Data chapter of the thesis.

**Inputs:** `raw` table, `tracker_events_raw` table, `map_translation` table. All from Phase 0.

### Steps

**1.1 — Overall corpus counts**

Write a DuckDB query producing a single summary row:
- Total replays in `raw`
- Total tournaments (distinct `tournament_dir`)
- Date range: `MIN` and `MAX` of `(details->>'$.timeUTC')::TIMESTAMP`
- Replays with null `match_time`
- Replays with `elapsed_loops < 1120` (under ~70 real seconds — likely disconnect/surrender)
- Replays with `tracker_events_raw` entries (`has_events`)
- Replays without any tracker events (`missing_events`)

Output: `reports/01_corpus_summary.json`

**1.2 — Per-tournament parse quality table**

For each tournament (grouped by `tournament_dir`), compute:
- `total_replays` — rows in `raw`
- `has_events` — count with at least one row in `tracker_events_raw`
- `missing_events` — count without any tracker events
- `short_games` — count with `elapsed_loops < 1120`
- `null_timestamp` — count with null `match_time`
- `event_coverage_pct` — `has_events / total_replays * 100`

Cross-reference with `*_processed_failed.log` counts per tournament if accessible.

Sort by `event_coverage_pct` ascending — worst coverage first.

Output: `reports/01_parse_quality_by_tournament.csv`  
Output: `reports/01_parse_quality_summary.md` (narrative: which tournaments have >20% missing events, which to potentially exclude)

**1.3 — Game duration distribution**

Convert `elapsed_loops` to minutes: `elapsed_loops / 16.0 / 60.0`.

Produce:
- Histogram data: bin edges and counts, binned at 2-minute intervals from 0 to 60 minutes
- Summary statistics: mean, median, p5, p25, p75, p95 overall
- The same statistics grouped by year (extracted from `match_time`)

Save histogram data as CSV and render as a matplotlib PNG.

Output: `reports/01_duration_distribution.csv`  
Output: `reports/01_duration_distribution.png`

**1.4 — APM and MMR zero-rate verification**

From the `raw` table, extract `APM` and `MMR` from `ToonPlayerDescMap` for every player slot. Compute:
- Fraction of player slots where `APM = 0`
- Fraction of player slots where `MMR = 0`
- If APM zero-rate > 95%: document as unusable, add to known dead fields list
- If MMR zero-rate > 95%: same

Output: `reports/01_apm_mmr_audit.md`

**1.5 — Game version and patch landscape**

From `raw`, extract `metadata->>'$.gameVersion'` and `metadata->>'$.dataBuild'`.

Produce a table with:
- Distinct `game_version` values
- Count of replays per version
- Date range (min/max `match_time`) per version

Group versions by year and identify broad patch eras (e.g. 2016–2017 = Heart of the Swarm→early LotV era, etc.).

Output: `reports/01_patch_landscape.csv`

**1.6 — Tracker event type inventory**

From `tracker_events_raw`, count rows by `event_type` across the full corpus:
- `PlayerStats` — the economy time series
- `UnitBorn` — unit production
- `UnitDied` — combat losses
- `UnitInit` / `UnitDone` — units under construction
- `Upgrade` — tech research
- `PlayerSetup` — player identity confirmation
- Any other types present

Compute average counts per replay for each event type.

Output: `reports/01_event_type_inventory.csv`

### Artifacts

- `reports/01_corpus_summary.json`
- `reports/01_parse_quality_by_tournament.csv`
- `reports/01_parse_quality_summary.md`
- `reports/01_duration_distribution.csv`
- `reports/01_duration_distribution.png`
- `reports/01_apm_mmr_audit.md`
- `reports/01_patch_landscape.csv`
- `reports/01_event_type_inventory.csv`

### Gate

You can state precisely: (a) how many replays are in the corpus, (b) which tournaments have critical event data, (c) the game duration distribution including the short-game tail, (d) whether APM/MMR are usable features (almost certainly not). No cleaning has been applied yet.

**Thesis mapping:** Chapter 3 — Dataset, section: Corpus composition and quality

---

## Phase 2 — Player universe and identity resolution

**Context:** SC2 player identity is fragmented. A player's "toon" (e.g. `3-S2-1-4842177`) is unique only per Battle.net server. Korean pros playing on EU or NA servers for international tournaments get different toons. The player's **nickname** is the practical global identifier, but it has edge cases: shared nicknames, renames mid-career, encoding inconsistencies (the `flat_players` view already applies `LOWER()` — important to note). This phase builds the canonical player table that all downstream feature engineering depends on.

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
| `canonical_nickname` | lowercase nickname (consistent with `flat_players` LOWER transform) |
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

**Thesis mapping:** Chapter 3 — Dataset, section: Player identity and coverage

---

## Phase 3 — Games table construction and temporal structure

**Context:** The `matches_flat` view in `processing.py` already pairs players within the same game. However, it produces **two rows per game** (one per perspective — p1 vs p2, then p2 vs p1). This is intentional for some feature engineering approaches but must be clearly understood. This phase constructs the canonical `games` table (one row per unique match), establishes correct temporal ordering per player, and validates that the data supports the sliding-window prediction framing.

**Inputs:** `raw` table, `player_appearances`, `canonical_players`, `map_translation`.

### Steps

**3.1 — Run `create_ml_views` to build `flat_players` and `matches_flat`**

Run `create_ml_views(con)`. Then immediately validate the output:
- Count rows in `flat_players` (should be exactly 2× the number of valid 1v1 replays)
- Count rows in `matches_flat` (should be exactly 4× — two perspectives × two players — wait: re-read the JOIN. It joins p1 to p2 where `p1.player_name != p2.player_name`, producing 2 rows per match. Verify this.)
- Count distinct `match_id` values in `matches_flat`
- Check for any `match_id` with more or fewer than 2 rows — these are data anomalies

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
    ROUND(game_loops / 16.0 / 60.0, 2) AS game_duration_minutes,
    map_name,
    map_size_x,
    map_size_y,
    data_build,
    game_version,
    -- Player 1 is always the lexicographically smaller name (consistent ordering)
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
    END AS winner_name,
    -- is_valid: flag games meeting minimum quality criteria
    (game_loops >= 1120) AS is_valid
FROM matches_flat
WHERE p1_name < p2_name  -- deduplicate: take only one perspective
```

Join to `canonical_players` to add `player_a_canonical_id` and `player_b_canonical_id` and `winner_canonical_id`.

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
- The target game is the player's **last game within a given tournament** at some point in their career

For each player, count:
- Total number of valid prediction targets (last game per tournament appearance)
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

**Thesis mapping:** Chapter 3 — Dataset, section: Temporal structure and prediction framing

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
- Rows per match per player — should be approximately `elapsed_loops / 160` per player (one snapshot every ~160 loops)
- Distribution of row counts per match (min, median, max, p5, p95)
- Null rate per column — any of the 39 fields that are systematically null are dead

Output: `reports/04_player_stats_validation.md`

**4.2 — Sampling regularity check**

For 200 randomly sampled games, check that `PlayerStats` events are sampled at regular `~160 loop` intervals:
- For each game and player, sort events by `game_loop` and compute `diff(game_loop)`
- Distribution of diffs — should cluster tightly at 160
- Flag any game where mean diff deviates > 20% from 160 (irregular sampling)
- Flag any game with gaps > 500 loops (missed snapshots)

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

At three canonical timepoints — loop 1120 (~70s), loop 2240 (~140s), loop 4480 (~280s) — and at the final snapshot (last `game_loop` per game per player), compute for each of the surviving (non-dead) 39 fields:
- Mean for winners
- Mean for losers
- Cohen's d = (mean_winner - mean_loser) / pooled_std
- Two-sided t-test p-value (Bonferroni-corrected for 39 comparisons)

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
- Note which race produces each unit type

This taxonomy is used in Phase 5 feature engineering.

Output: DuckDB table `unit_events`  
Output: `data/unit_type_taxonomy.csv`  
Output: `reports/04_unit_type_profile.csv` — counts of each unit type born/died across the sample

**4.6 — Extract and profile `Upgrade` events**

From `tracker_events_raw`, filter to `event_type = 'Upgrade'`. Extract `upgrade_type_name`, `player_id`, `game_loop` from `event_data`.

Build DuckDB table `upgrade_events`. Then compute:
- Top 50 most frequent upgrades overall
- Median `game_loop` timing for each upgrade (converted to minutes)
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

You have a ranked list of which of the 39 PlayerStats fields show the strongest winner/loser separation at which timepoints. You have a unit type taxonomy. You know which fields are dead (all zeros). These findings directly determine which features to engineer in Phase 5.

**Thesis mapping:** Chapter 4 — Features, section: In-game economic and military indicators

---

## Phase 5 — Map, meta-game, and matchup analysis

**Context:** Win/loss prediction in SC2 is heavily confounded by race matchup (ZvT, TvP, etc.), map pool, and game version (balance patches). This phase quantifies those confounds so they can be handled correctly in the model — either as control features or by stratifying the evaluation.

**Inputs:** `games` table, `player_appearances`, `map_translation`.

### Steps

**5.1 — Map pool by year**

For each calendar year, list the distinct `map_name` values that appear in `games` and their game counts. SC2 map pools rotate each season.

Output: `reports/05_map_pool_by_year.csv`

**5.2 — Win rate by map and matchup**

For each (map_name, player_a_race, player_b_race) combination where player_a < player_b alphabetically (canonical matchup ordering):
- Total games
- Win rate for player_a's race
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

Compute `map_area = map_size_x * map_size_y` for each game. Scatter plot and Pearson correlation between map_area and `game_duration_minutes`.

Output: `reports/05_map_size_duration_correlation.png`

**5.5 — Race representation by tournament type**

Some tournaments (WCS Korea, IEM) skew toward Korean pros and thus Terran/Zerg. Others (WCS Global) have more Protoss. Compute race proportion per tournament.

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

**Thesis mapping:** Chapter 3 — Dataset, section: Meta-game confounds; Chapter 4 — Features, section: Control variables

---

## Phase 6 — Data cleaning and valid game corpus

**Context:** Based on all findings from Phases 1–5, this phase applies explicit, documented cleaning rules to produce the clean game corpus. Every exclusion is logged with its reason. No data is deleted — all exclusions are implemented as filters (a `is_valid` flag or a `games_clean` view). This is a thesis-auditable step.

**Inputs:** All tables and reports from Phases 1–5.

### Steps

**6.1 — Write the cleaning rules document**

Before touching any data, write `reports/06_cleaning_rules.md`. Each rule must reference which Phase finding motivates it:

| Rule ID | Condition | Action | Motivation |
|---------|-----------|--------|------------|
| R1 | `game_loops < 1120` | exclude | Phase 1.3: games < 70s are disconnects/surrenders |
| R2 | No rows in `tracker_events_raw` for this `replay_id` | exclude | Phase 1.1: no event data, cannot compute in-game features |
| R3 | Player count per game ≠ 2 (after observer/caster exclusion) | exclude | Phase 0.4: not a valid 1v1 game |
| R4 | Either player's `result` not in {Win, Loss} | exclude | no ground truth label |
| R5 | Race is `BW%` (Brood War exhibition) | exclude | Phase 0: `flat_players` view already filters this |
| R6 | Tournament `event_coverage_pct < 20%` (from Phase 1.2) | flag whole tournament | insufficient data quality |
| R7 | Player appears only with ambiguous identity (unresolved from Phase 2.4) | flag game | degraded player identity confidence |

Add any additional rules discovered during exploration.

**6.2 — Apply rules and create `games_clean` view**

Create a DuckDB view (not a copy) `games_clean` that filters `games` using all R1–R7 rules. Add an `exclusion_reason` column to the base `games` table explaining why each excluded game was removed.

**6.3 — Cleaning impact report**

For each rule, report:
- Games excluded by this rule (and this rule alone — not already excluded)
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
- Overall win rate (sanity check: should be 0.500 exactly, since every game has one winner)
- Matchup distribution (ZvT, ZvP, TvP, ZvZ, TvT, PvP counts and percentages)

Output: `reports/06_clean_corpus_summary.md`

### Artifacts

- `reports/06_cleaning_rules.md`
- DuckDB view: `games_clean`
- `reports/06_cleaning_impact.md`
- `reports/06_clean_corpus_summary.md`

### Gate

`games_clean` view exists. Overall win rate is exactly 0.500. Cleaning impact is documented. Every exclusion has a documented rule ID.

**Thesis mapping:** Chapter 3 — Dataset, section: Preprocessing and quality filtering

---

## Phase 7 — Feature engineering

**Context:** With the data exploration complete and the clean corpus established, feature engineering can begin. Features fall into three groups: (A) pre-game context features (available before the match starts — player history, opponent history, head-to-head); (B) in-game snapshot features (from `PlayerStats` at canonical timepoints — ONLY usable for in-game prediction, not pre-game); (C) control features (map, matchup, patch era — decided in Phase 5). Do not mix groups A and B in the same model without understanding the temporal position they represent.

**Inputs:** `games_clean`, `player_career_sequence`, `player_stats` view, `unit_events`, `upgrade_events`, `canonical_players`, all reports from Phases 1–5.

### Steps

**7.1 — Define the feature groups formally**

Write `reports/07_feature_specification.md` before writing any feature code:

**Group A — Pre-game features (predict before the game begins)**
- Player A and B: games played in last 30 days, last 90 days, last 1 year (career window)
- Player A and B: win rate in last N games (rolling window — use results from `player_career_sequence`)
- Player A and B: win rate vs. the specific opponent's race
- Player A and B: win rate on this map (historical)
- Player A and B: win rate in this tournament type (IEM vs. HomeStory etc.)
- Head-to-head record between A and B (all prior games)
- Within-tournament context: player's win/loss record so far in the current tournament (games 1 to M-1)
- Within-tournament context: opponent's win/loss record so far in the current tournament
- Career-level summary: total career games, career win rate, career span in days
- Race matchup encoding (one-hot or ordinal)
- Map features: map_name (one-hot or embedding), map_size_x, map_size_y
- Patch era encoding

**Group B — In-game snapshot features (predict during/after game — requires game to have started)**
- From `player_stats` at loop 1120, 2240, 4480: all surviving non-dead fields (from Phase 4 separability analysis, filtered to |Cohen's d| > 0.2 at any timepoint)
- Differential features: winner_stat - loser_stat at each timepoint (note: these are only computable for training, not inference without knowing who won)

**Note:** Group B features are only valid for a post-hoc or "in-game prediction" model variant. The primary thesis model should use only Group A features. Group B can be a comparison experiment.

**7.2 — Implement Group A feature computation**

All Group A features must be computed with **strict temporal discipline**: for any target game at time T, only information from games before time T (strictly `match_time < T`) may be used.

Implement as a Python function `compute_pre_game_features(games_clean, player_career_sequence, target_game_id)` that returns a feature vector for a given target game. Then vectorise over all prediction targets identified in Phase 3 (Step 3.6).

Key implementation constraint: use `player_career_sequence` with `career_game_seq < target_seq` filters — never a naïve `.shift()` on a DataFrame that could leak future information.

Output: `data/features_group_a.parquet` — one row per prediction target

**7.3 — Implement Group B feature computation (optional experiment)**

For the in-game model variant, compute PlayerStats features at each canonical timepoint per game.

Apply the surviving fields list from Phase 4 (|Cohen's d| > 0.2). Compute differential columns (player_a_stat - player_b_stat).

Output: `data/features_group_b.parquet`

**7.4 — Feature validation**

For the Group A features:
- Null rate per feature column — document and handle (impute with career-prior mean, or use 0 for cold-start players with no prior games)
- Distribution checks: any features with extreme skew (> 10 std from mean) should be log-transformed or clipped
- Temporal leakage check: for a sample of 20 target games, manually verify that no feature value for that game depends on any event at or after `match_time` of the target game

Output: `reports/07_feature_validation.md`

**7.5 — Build the prediction target table**

Create the final ML-ready table combining features and labels:

| column | description |
|--------|-------------|
| `target_game_id` | the game being predicted |
| `player_focal_id` | the canonical player we are predicting for |
| `player_opponent_id` | the opponent |
| `within_tournament_context_games` | how many prior games this player has in this tournament |
| `career_prior_games` | total prior career games for focal player |
| [all Group A feature columns] | |
| `label` | 1 if focal player won, 0 if lost |
| `split` | train / val / test (assigned in Phase 8) |

Output: `data/ml_dataset.parquet`

### Artifacts

- `reports/07_feature_specification.md`
- `data/features_group_a.parquet`
- `data/features_group_b.parquet` (if implemented)
- `reports/07_feature_validation.md`
- `data/ml_dataset.parquet`

### Gate

`ml_dataset.parquet` exists. Temporal leakage check passed for sampled games. Null rates documented and handled. `reports/07_feature_specification.md` explicitly distinguishes Group A (pre-game) from Group B (in-game) features.

**Thesis mapping:** Chapter 4 — Features

---

## Phase 8 — Train/val/test split construction

**Context:** This is where the correct splitting strategy from the thesis design is implemented. The naïve global temporal split in `processing.py` is replaced with a per-player leave-last-tournament-out strategy combined with within-tournament prediction framing. This is the most thesis-critical implementation step.

**Inputs:** `data/ml_dataset.parquet`, `games_clean`, `player_career_sequence`.

### Steps

**8.1 — Implement the correct split strategy**

The split logic is:

- **Test set:** For each canonical player, their last tournament appearance. The prediction target within that tournament is their last game (game M+1 given games 1 to M within that tournament). This is the prediction target from the sliding window.
- **Validation set:** For each canonical player, their second-to-last tournament appearance (same logic).
- **Training set:** All remaining games.

Implementation notes:
- A game can appear in both player A's training and player B's test set (if they played at different points in their respective careers). This is correct behaviour — the split is per-player, not per-game.
- Players with fewer than 3 tournament appearances cannot have separate train/val/test — flag them as cold-start and exclude from validation/test, keep in training only.

**8.2 — Validate the split**

For the new split:
- No player's test target is temporally before their training data
- No player's validation target is temporally before their training data
- Class balance (win rate) in train, val, test — should each be ~0.500
- Distribution of `within_tournament_context_games` in test: how often does the model have 0, 1, 2, 3+ prior games in the target tournament?
- Size of each split: number of examples

Output: `reports/08_split_validation.md`

**8.3 — Baseline win rate by split**

For each split, compute win rate by matchup (ZvT, TvP, etc.). If any matchup in test has win rate significantly different from 0.5, it is a potential confound in the test evaluation.

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

**Thesis mapping:** Chapter 4 — Methods, section: Experimental setup and evaluation protocol

---

## Phase 9 — Baseline models and sanity checks

**Context:** Before training any serious model, establish baselines that any real model must beat. Also run sanity checks to confirm the dataset and features are not trivially broken.

**Inputs:** `data/ml_dataset.parquet` with correct split.

### Steps

**9.1 — Implement and evaluate baselines**

- **Random baseline:** Predicts win probability = 0.5 always. Accuracy = 50%.
- **Race-matchup baseline:** Predicts the historically more winning race for each matchup. Uses only training set matchup win rates.
- **Recent form baseline:** Predicts the player with the higher win rate in their last 10 career games wins.
- **Head-to-head baseline:** Predicts based on prior head-to-head record. Falls back to recent form if no prior H2H exists.

Evaluate each baseline on the test set: accuracy, log-loss, ROC-AUC, per-matchup accuracy.

Output: `reports/09_baseline_results.md`

**9.2 — Sanity check: permutation test**

Shuffle the `label` column randomly (keeping all features intact). Train a logistic regression on shuffled labels. Confirm it achieves ~50% accuracy (no worse than random). This verifies the training pipeline is not broken.

**9.3 — Sanity check: perfect feature leakage test**

Create a "cheat" feature: the actual in-game outcome stat from the final `PlayerStats` snapshot (e.g. `minerals_killed_army` differential at game end). Train a model on this. It should achieve near-100% accuracy. This verifies that the pipeline can distinguish signal from noise and that the join between features and labels is correct.

Output: `reports/09_sanity_checks.md`

### Artifacts

- `reports/09_baseline_results.md`
- `reports/09_sanity_checks.md`

### Gate

At least one baseline beats random (otherwise the features contain no signal). Permutation test achieves ~50%. Leakage test achieves near-100%. All sanity checks documented.

**Thesis mapping:** Chapter 5 — Experiments, section: Baselines and sanity validation

---

## Phase 10 — Model training and evaluation

**Context:** With clean features, a correct split, and validated baselines, train the primary models. Start simple and add complexity only if justified by validation performance.

**Inputs:** `data/ml_dataset.parquet`, baseline results from Phase 9.

### Steps

**10.1 — Logistic Regression (interpretable baseline)**

Train with Group A features, evaluate on val set. Record: accuracy, log-loss, ROC-AUC, per-matchup accuracy, calibration curve. Inspect top feature weights — do they make domain sense?

**10.2 — Gradient Boosted Trees (LightGBM or XGBoost)**

Train with Group A features, tune on val set (learning rate, depth, regularisation). Evaluate on test set only after hyperparameter selection is finalised. Record same metrics plus feature importances.

**10.3 — Feature ablation study**

Train LightGBM with each feature group removed in turn:
- Without within-tournament context features
- Without head-to-head history
- Without career-level stats
- Without control features (map, matchup)

Report accuracy drop for each ablation. This answers which feature groups matter most.

Output: `reports/10_ablation_results.md`

**10.4 — Per-matchup evaluation**

For the best model, evaluate separately on ZvT, ZvP, TvP, ZvZ, TvT, PvP subsets of the test set. Are some matchups harder to predict than others?

**10.5 — Cold-start analysis**

Stratify test set by `career_prior_games` (0–5, 6–20, 21–50, 51+). How does model accuracy vary with career history length? This directly addresses the cold-start problem.

**10.6 — Optional: GNN experiment**

If time permits, implement the GNN model from the existing `sc2/gnn` code. Compare to the tabular models. The key thesis question is: does modelling the player interaction graph add anything beyond the tabular features?

Output: `reports/10_model_results.md`  
Output: `reports/10_ablation_results.md`  
Output: `reports/10_per_matchup_results.csv`  
Output: `reports/10_cold_start_analysis.csv`

### Artifacts

- `reports/10_model_results.md`
- `reports/10_ablation_results.md`
- `reports/10_per_matchup_results.csv`
- `reports/10_cold_start_analysis.csv`

### Gate

Best model accuracy > best baseline accuracy (otherwise the ML is not adding value). Ablation results document which features drive performance.

**Thesis mapping:** Chapter 5 — Experiments, sections: Primary results, Ablation study, Analysis

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
  01_duration_distribution.png
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
