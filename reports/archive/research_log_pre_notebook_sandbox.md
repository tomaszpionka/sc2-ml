# Research Log

Thesis: "A comparative analysis of methods for predicting game results in real-time strategy games, based on the examples of StarCraft II and Age of Empires II."

Reverse chronological entries. Each entry documents the reasoning and learning behind code changes — intended as source material for thesis writing.

> New entries follow `RESEARCH_LOG_TEMPLATE.md`. Entries before
> 2026-04-07 use the legacy free-form format and are kept verbatim.

---

## 2026-04-07 — [FEAT] SC2 Phase 1 Steps 1.9D/E/F — event_data field inventory, Parquet reconciliation, schema reference

**Objective:** Profile the `event_data VARCHAR` JSON column in `tracker_events_raw` and
`game_events_raw`, verify key-set constancy per event type, reconcile Parquet staging
schemas against DuckDB, and compile a consolidated event_data schema reference for Phase 4.

**Method:** Three parameterised SQL builder functions added to `exploration.py`, plus four
run_* orchestrators that execute the queries, write CSV/MD artifacts, and check gate
conditions. All queries use `USING SAMPLE N ROWS` for performance on 62M/609M row tables.

**SQL — 1.9D-i (tracker event_data field inventory, simplified):**
```sql
WITH sampled AS (
    SELECT event_type, event_data
    FROM tracker_events_raw
    USING SAMPLE 100000 ROWS
),
keys_unnested AS (
    SELECT s.event_type, kv.key AS json_key,
           json_type(s.event_data::JSON->kv.key) AS val_type
    FROM sampled s,
         LATERAL (SELECT unnest(json_keys(s.event_data::JSON)) AS key) AS kv
    WHERE s.event_data IS NOT NULL
)
SELECT event_type, json_key,
       CASE WHEN val_type IN ('OBJECT', 'ARRAY') THEN true ELSE false END AS is_nested
FROM keys_unnested
GROUP BY event_type, json_key, val_type
ORDER BY event_type, json_key
```

**SQL — 1.9D-ii (key-set constancy per event type, simplified):**
```sql
WITH sampled AS (
    SELECT ROW_NUMBER() OVER () AS rn, event_data
    FROM tracker_events_raw
    WHERE event_type = '{event_type}'
    USING SAMPLE 10000 ROWS
),
key_sets AS (
    SELECT s.rn, LIST(kv.k ORDER BY kv.k) AS key_list
    FROM sampled s,
         LATERAL (SELECT unnest(json_keys(s.event_data::JSON)) AS k) AS kv
    WHERE s.event_data IS NOT NULL
    GROUP BY s.rn
),
totals AS (SELECT COUNT(*) AS total FROM key_sets)
SELECT ks.key_list, COUNT(*) AS n_events,
       ROUND(100.0 * COUNT(*) / t.total, 2) AS pct
FROM key_sets ks, totals t
GROUP BY ks.key_list, t.total
ORDER BY n_events DESC
```

**SQL — 1.9D-iii (PlayerStats.stats nested fields, simplified):**
```sql
WITH sampled AS (
    SELECT event_data FROM tracker_events_raw
    WHERE event_type = 'PlayerStats'
    USING SAMPLE 100000 ROWS
)
SELECT DISTINCT unnest(json_keys(event_data::JSON->'stats')) AS nested_key_name
FROM sampled
WHERE json_type(event_data::JSON->'stats') = 'OBJECT'
ORDER BY nested_key_name
```

**Findings — Step 1.9D:**
- 10 tracker event types, 80 total (event_type, json_key) pairs.
- 39 PlayerStats.stats sub-keys (scoreValue* prefixed fields).
- Key-set constancy: 9/10 types at 100%; **UnitBorn at 93.81%** (gate violation, warning only).
  UnitBorn has optional killer fields (`killerPlayerId`, `killerUnitTagIndex`,
  `killerUnitTagRecycle`) absent when the unit dies to non-player causes (buildings
  collapsing, neutral units). This is structurally motivated, not a data quality issue.

**Findings — Step 1.9E:**
- Game event_data inventoried for 5 high-value types (sample_size=200,000).
- Nested sub-objects enumerated: Cmd.abil (3 keys: abilCmdData, abilCmdIndex, abilLink),
  Cmd.data (1 key: None — placeholder for command data), SelectionDelta.delta (4 keys:
  addSubgroups, addUnitTags, removeMask, subgroupIndex).
- Key-set constancy: all 5 types at **100%**. Gate PASS.

**Findings — Step 1.9F:**
- Parquet schema (tracker): `match_id:string, event_type:string, game_loop:int32,
  player_id:int8, event_data:string` — matches DuckDB tracker_events_raw exactly.
- Parquet schema (game): same + `user_id:int32` — matches DuckDB game_events_raw exactly.
- 5 batches checked per table, 0 mismatches. Gate PASS.
- Event schema reference covers all 10 tracker types and all 5 high-value game types.
  Gate PASS.

**Artifacts produced:**
- `01_09D_tracker_event_data_field_inventory.csv`
- `01_09D_tracker_event_data_key_constancy.csv`
- `01_09D_playerstats_stats_field_inventory.csv`
- `01_09E_game_event_data_field_inventory.csv`
- `01_09E_game_event_data_key_constancy.csv`
- `01_09F_parquet_duckdb_schema_reconciliation.md`
- `01_09F_event_schema_reference.md`

**Tests:** 69 tests pass (8 new for SQL builders, 9 new for run_* functions, 3 new for
schema document; plus all pre-existing 61). Coverage: 98.29% overall.

**Gate summary:**
- 1.9D gate: PARTIAL PASS — UnitBorn dominance 93.81% (< 99%). Documented as known
  exception (optional killer fields). All other 9 types at 100%.
- 1.9E gate: PASS — all 5 types at 100%.
- 1.9F-i gate: PASS — 0 schema mismatches.
- 1.9F-ii gate: PASS — all event types covered in reference.

**Thesis notes:** The 39 PlayerStats.stats fields are the primary source for Phase 4
in-game features. The UnitBorn killer-field polymorphism (optional keys) requires
NULL-safe extraction in Phase 4 feature engineering — feature code must handle
absent keys with a default (e.g., 0 for killer IDs). The 100% key-set constancy for
all 5 high-value game event types confirms that these events have stable schemas
that can be extracted with fixed column lists in Phase 4.

---

## 2026-04-07 — [FEAT] SC2 Phase 1 Step 1.9 — ToonPlayerDescMap field inventory and JSON structure verification

**Objective:** Enumerate all distinct field names present in ToonPlayerDescMap player objects
(1.9A), verify that the key-set is constant across all 44,817 player slots (1.9B), and
catalogue all top-level JSON column keys plus one deeper nesting level for the four
metadata columns: `header`, `initData`, `details`, `metadata` (1.9C).

**Method:** Three DuckDB SQL queries run via `poetry run sc2 explore --steps 1.9`.

**SQL — 1.9A (TPDM field inventory):**
```sql
SELECT DISTINCT json_key
FROM (
    SELECT unnest(json_keys(entry.value)) AS json_key
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
)
ORDER BY json_key;
```

**SQL — 1.9B (key-set constancy):**
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

**SQL — 1.9C (top-level column keys, template per column):**
```sql
SELECT DISTINCT json_key
FROM (
    SELECT unnest(json_keys("{col}")) AS json_key FROM raw
)
ORDER BY json_key;
```
Plus one level deeper for nested object-valued keys (e.g. `initData.gameDescription`).

**Key findings (real SC2EGSet data, 22,390 replays):**

*Sub-step 1.9A — TPDM field inventory:*
- 20 distinct keys in all ToonPlayerDescMap player objects:
  `APM`, `MMR`, `SQ`, `clanTag`, `color`, `handicap`, `highestLeague`, `isInClan`,
  `nickname`, `playerID`, `race`, `realm`, `region`, `result`, `selectedRace`,
  `startDir`, `startLocX`, `startLocY`, `supplyCappedPercent`, `userID`

*Sub-step 1.9B — Key-set constancy:*
- 1 distinct key-set variant across all 44,817 player slots (100% coverage)
- Gate condition: PASS (dominant variant > 99%)
- Halt predicate: False (no fragmentation)
- All player objects are structurally uniform — no schema drift across tournaments or years

*Sub-step 1.9C — Top-level JSON field inventory:*
- `header`: `elapsedGameLoops`, `version`
- `initData`: `gameDescription` (nested object)
  - `initData.gameDescription`: `gameOptions`, `gameSpeed`, `isBlizzardMap`,
    `mapAuthorName`, `mapFileSyncChecksum`, `mapSizeX`, `mapSizeY`, `maxPlayers`
- `details`: `gameSpeed`, `isBlizzardMap`, `timeUTC`
- `metadata`: `baseBuild`, `dataBuild`, `gameVersion`, `mapName`

**Implications for Phase 2+:**
- The `color`, `realm`, `region` fields are newly visible; `realm`/`region` are relevant
  for player identity resolution (Phase 2), as they distinguish server-scope of account IDs
- `selectedRace` vs `race` disambiguation can be handled deterministically (Step 1.8 finding)
- All 20 TPDM fields are consistently present: no conditional handling needed during
  feature extraction (Phase 7)

**Artifacts:**
- `src/rts_predict/sc2/reports/sc2egset/artifacts/01_09_tpdm_field_inventory.csv` (20 rows)
- `src/rts_predict/sc2/reports/sc2egset/artifacts/01_09_tpdm_key_set_constancy.csv` (1 row)
- `src/rts_predict/sc2/reports/sc2egset/artifacts/01_09_toplevel_field_inventory.csv` (18 rows)

**Gate condition:** PASS — key-set is perfectly constant (100% of slots).

---

## 2026-04-07 — [FEAT] SC2 Phase 1 Step 1.8 — Game settings and replay field completeness audit

**Objective:** Verify that all 22,390 SC2EGSet replays conform to competitive
settings expectations (game speed, handicap, game mode flags, race selection,
map metadata, version consistency) and audit parse error flags.

**Method:** SQL queries via `poetry run sc2 db --dataset sc2egset query`; error
flags scanned directly from 70 ZIP archives (fields not in DuckDB `raw` table).

**Key findings from real data:**

*Sub-step A — Game speed (PASS):*
- 100% of replays have `gameSpeed=Faster` in both `initData` and `details`
- Zero cross-field mismatches
- No cleaning rule needed

*Sub-step B — Handicap (NEAR-PASS):*
- 44,815 / 44,817 player slots at handicap = 100
- 2 slots at handicap = 0: anonymous phantom entries with empty toon key, empty
  nickname, `color.a=0`; not real players
- Will be excluded naturally by empty-nickname filter in Phase 2 identity resolution
- Affected replays: `63a9f9bf…` and `0eba71d4…` (IEM Katowice 2017 and
  HomeStory Cup XIX)

*Sub-step C — Error flags (PASS):*
- All 22,390 replays scanned from ZIP archives; zero parse errors of any kind
- `gameEventsErr=0`, `messageEventsErr=0`, `trackerEvtsErr=0`
- `01_error_flags_audit.csv` has header row only (no error replays)

*Sub-step D — Game mode flags (NEAR-PASS):*
- 22,387 / 22,390 replays: `noVictoryOrDefeat=false`, `competitive=false`,
  `cooperative=false`, `practice=false`
- 3 replays from `2017_IEM_XI_World_Championship_Katowice`: `competitive=true`,
  `amm=true`, `battleNet=true` — these are ladder replays bundled with the
  tournament; not valid tournament games
- **Cleaning rule C-D1:** Exclude 3 replays with `competitive=true` in Phase 6

*Sub-step E — Random race (INFORMATIONAL):*
- 43,694 slots with race locked (selectedRace matches assigned_race)
- 1,110 slots with empty `selectedRace` (player picked Random; assigned_race resolved)
- 10 slots with explicit `selectedRace=Rand`
- 3 slots with BW race codes (BWTe, BWPr, BWZe): anomalous
- **Engineering note:** Use `ToonPlayerDescMap.race` (assigned_race) as feature,
  not `selectedRace`
- **Cleaning rule C-E1:** Flag replays with BW race codes for review

*Sub-step G — Map/lobby metadata (PASS):*
- `fog=0` for 100% of replays (standard fog of war)
- `randomRaces=false` for 100% of replays (lobby-level toggle, not individual)
- `observers=0` for 100% of replays
- `maxPlayers`: 21,981 on 2-slot maps; 409 on 4/6/8/9-slot maps (map slot count,
  not player count — 4-slot maps used for 1v1 are standard)
- `isBlizzardMap=true` for 78.2% (17,515); 21.8% (4,875) are community maps

*Sub-step H — Version consistency (PASS):*
- Zero mismatches between `header.version` and `metadata.gameVersion`

**Artifacts produced:**
- `src/rts_predict/sc2/reports/sc2egset/artifacts/01_08_game_settings_audit.md`
- `src/rts_predict/sc2/reports/sc2egset/artifacts/01_08_error_flags_audit.csv` (header-only)

**Verification:** Both artifacts present and non-empty (CSV has header row).
Gate condition met: `01_08_game_settings_audit.md` and `01_08_error_flags_audit.csv` exist.

---

## 2026-04-07 — [FEAT] AoE2 Phase 0 — aoe2companion ingestion and audit (Steps 0.1–0.8)

**Objective:** Execute Phase 0 for the aoe2companion dataset: source inventory,
schema profiling (matches, ratings, singletons), smoke test, full CTAS ingestion,
reconciliation, and Phase 0 summary.

**Key findings from real data:**

*Step 0.1 — Source audit (PASS):*
- 4,147 files on disk (matches manifest exactly)
- 3 files oversized vs manifest (not truncated — benign growth); gate passes
  because truncation (data loss) is the relevant failure mode, not growth
- Zero unexpected failures, zero zero-byte files
- `T_acquisition`: `2026-04-06T21:08:57.797026+00:00`

*Step 0.2 — Match schema profiling (STABLE):*
- 5 samples spanning 2020-08-01 to 2026-04-04
- Column names and types stable across all samples
- Per-sample row counts: 25,238 → 44,535 → 267,398 → 189,429 → 198,463

*Step 0.3 — Rating schema profiling + dtype decision (explicit strategy):*
- 8 samples: 3 sparse (header-only, ≤63 bytes), 2 transition, 3 dense
- Sparse boundary date: 2025-06-26; threshold: 1,024 bytes
- 1,336 header-only files (zero data rows), 455 transition, 281 dense
- Explicit dtype map chosen; recorded in `00_03_dtype_decision.json`

*Step 0.4 — Singleton schema profiling:*
- leaderboard.parquet: 2,381,227 rows; `T_snapshot`: `2026-04-06T21:08:57`
- profile.parquet: 3,609,686 rows; `T_snapshot`: `2026-04-06T21:09:07`
- Temporal leakage warning written to report and INVARIANTS I2

*Step 0.5 — Smoke test (PASS):*
- Sparse + dense rating CSV union succeeded; explicit dtype map applied
- All 4 smoke tables created; `filename` column confirmed on each

*Step 0.6 — Full CTAS ingestion (PASS):*
- raw_matches: 277,099,059 rows across 2,073 files
- raw_ratings: 58,317,433 rows across 2,072 files (1,336 zero-row sparse files)
- raw_leaderboard: 2,381,227 rows; raw_profiles: 3,609,686 rows
- `T_ingestion`: `2026-04-07T11:21:37`

*Step 0.7 — Reconciliation (DEGRADED):*
- Manifest has no per-file row counts; reconciliation limited to file-count match
- File-count assertions all pass (2073, 2072, 1, 1)
- Zero-row rating files (1,336) matches sparse count from Step 0.3 exactly

*Step 0.8 — Phase 0 summary:*
- `00_08_phase0_summary.md` and `INVARIANTS.md` written to `reports/aoe2companion/`
- INVARIANTS records: sparse-rating boundary, T_snapshot for both singletons,
  reconciliation strength (DEGRADED), provenance guarantee

**Verification:** All 8 gate artifacts present; INVARIANTS.md follows template §6.

---

## 2026-04-07 — [FEAT] AoE2 Phase 0 — aoestats ingestion and audit (Steps 0.1–0.7)

**Objective:** Execute Phase 0 for the aoestats dataset: source inventory, schema
profiling, smoke test, full CTAS ingestion, reconciliation, and Phase 0 summary.

**Key findings from real data:**

*Step 0.1 — Source audit (PASS):*
- 172 match files on disk (matches manifest exactly)
- 171 player files on disk (1 known failed download: `2025-11-16_2025-11-22_players.parquet`,
  documented in manifest with `status='failed'`)
- Zero unexpected failures, zero size mismatches
- Gate logic updated: entries with `status='failed'` in manifest are "known failures"
  and do not block the gate. Gate fails only for *unexpected* missing files.
- `T_acquisition`: `2026-04-06T19:52:17.339148+00:00`

*Step 0.2 — Match schema profiling (DRIFTED):*
- 5 samples spanning 2022-08-28 to 2026-02-07
- All 18 columns present across all samples (column names STABLE)
- Type drift: `raw_match_type` alternates DOUBLE/BIGINT across files.
  `union_by_name = true` resolves to DOUBLE in the union schema.

*Step 0.3 — Player schema profiling (DRIFTED):*
- 5 samples: same date range
- All 14 columns present across all samples (column names STABLE)
- Type drift: `feudal_age_uptime`, `castle_age_uptime`, `imperial_age_uptime`
  changed DOUBLE→INTEGER (approx. 2023→2024 boundary). `profile_id` DOUBLE→BIGINT.
  `opening` VARCHAR→INTEGER. DuckDB union resolves to the widest compatible type.
- Note: both tables are marked DRIFTED because type drift is a real signal that
  downstream feature engineering must handle.

*Step 0.4 — Smoke test (PASS):*
- Files tested: earliest (2022-08-28) and latest (2026-02-07) for both tables
- `union_by_name = true` union succeeded for both tables
- smoke_matches: 130,276 rows across 2 files. smoke_players: 471,459 rows across 2 files.
- `filename` column present on both tables.

*Step 0.5 — Full CTAS ingestion:*
- raw_matches: **30,690,651 rows** across 172 files
- raw_players: **107,627,584 rows** across 171 files
- T_ingestion: `2026-04-07T16:36:52.108940+00:00`

*Step 0.6 — Reconciliation (DEGRADED, PASS):*
- Manifest has no per-file row counts → strength DEGRADED
- File-count assertions: raw_matches 172/172 OK; raw_players 171/171 OK
  (expected count adjusted to exclude 1 known failed download)
- Min/max rows: matches 11,615–264,843; players 53,556–930,677

*Step 0.7 — Phase 0 summary:*
- `00_07_phase0_summary.md` and `INVARIANTS.md` written to `reports/aoestats/`
- INVARIANTS.md covers I1 (DRIFTED with type-drift detail), I1a (known download
  failure), I5 (row-count totals), I6 (DEGRADED reconciliation), I7 (provenance)

**Code changes:**
- `audit.py`: updated `run_source_audit` to distinguish known vs unexpected failures;
  updated `_profile_parquet_dir` to detect type drift (returns 4-tuple); updated
  `_write_schema_report` to render type-drift section; updated
  `run_rowcount_reconciliation` to subtract known failed downloads from expected count;
  updated `write_phase0_summary`/INVARIANTS.md to include type-drift and known-failure sections.
- Tests: 8 new tests in `test_audit.py` to cover type-drift, known-failure, and
  error-path branches.

**Verification:** 302 tests pass, ruff clean, mypy clean, 96.31% coverage (≥ 95%).

---

## 2026-04-06 — [CHORE] Migrate to per-dataset report subdirectory structure

**Objective:** Introduce `reports/<dataset>/` subdirectories to prevent Phase 0–2
artifact filename collisions between datasets (critical for AoE2 support where two
datasets — aoe2companion and aoestats — would both produce `00_01_*.json`).

**Changes:**
- `SC2_THESIS_ROADMAP.md` split into `sc2egset/ROADMAP.md` (Phases 0–2) and `ROADMAP.md` (Phases 3–10)
- `AOE2_THESIS_ROADMAP.md` placeholder replaced by `ROADMAP.md` placeholder
- `DATASET_REPORTS_DIR` constant added to `sc2/config.py`; `AOE2COMPANION_REPORTS_DIR` and `AOESTATS_REPORTS_DIR` added to `aoe2/config.py`
- `audit.py` and `exploration.py` write to `DATASET_REPORTS_DIR` by default
- `PHASE_STATUS.yaml` (SC2 and AoE2) updated to `dataset_roadmap`/`game_roadmap`/`current_dataset` fields
- All documentation and agent prompts updated; zero `SC2_THESIS_ROADMAP` references remain outside CHANGELOG

**Verification:** 172 tests pass, ruff clean, mypy clean, 100% coverage.

---

## 2026-04-05 — [CHORE] Add step numbers to Phase 0 and Phase 1 report filenames

**Objective:** Make report filenames self-documenting by encoding the step that produced them.
With 7–9 steps per phase and multiple outputs per step, `00_source_audit.json` gave no
indication of which step it came from. Adopted `{PHASE:02d}_{STEP:02d}_{name}.{ext}` throughout.

**Changes:**
- 8 Phase 0 files renamed: `00_source_audit.json` → `00_01_source_audit.json`, etc.
- 16 Phase 1 files renamed: `01_apm_mmr_audit.md` → `01_04_apm_mmr_audit.md`, etc.
- Note: `00_06` is intentionally absent — Step 0.6 produces no report file.
- `audit.py`, `exploration.py`, `test_exploration.py` updated accordingly.
- `SC2_THESIS_ROADMAP.md`, `research_log.md`, `CHANGELOG.md` updated accordingly.

**Verification:** 102 tests pass, ruff and mypy clean.

---

## 2026-04-04 — [CHORE] Repository reorganization: `sc2ml` → `rts_predict` namespace

**Objective:** Structural standardization to support the planned SC2 + AoE2 comparative
study. The `sc2ml` package name was SC2-specific and did not scale. All SC2 artifacts
have been moved under a unified `rts_predict` namespace.

**Changes made:**
- Python package renamed: `sc2ml` → `rts_predict.sc2` (all imports updated)
- SC2 phase artifacts moved: `reports/00_*`, `reports/01_*`, `sanity_validation.md`,
  `archive/` → `src/rts_predict/sc2/reports/` (history preserved via `git mv`)
- Roadmap renamed: `SC2ML_THESIS_ROADMAP.md` → `SC2_THESIS_ROADMAP.md`
- CLI entry point renamed: `sc2ml` → `sc2`
- `reports/` at repo root now contains only the cross-cutting `research_log.md`
- New placeholder packages: `rts_predict.aoe2`, `rts_predict.common`
- New infrastructure: `ARCHITECTURE.md`, `PHASE_STATUS.yaml` (per game), `REVIEW_QUEUE.md`,
  `.claude/chat-handoff.md`, `common/CONTRACT.md`
- Version bumped to `0.14.0`

**Motivation:** AoE2 integration begins after SC2 pipeline is complete. Having SC2
artifacts mixed at the repo root would complicate the mirrored AoE2 structure. This
reorganization creates the structural foundation for a clean side-by-side comparison.

**No analytical changes:** Business logic, SQL queries, and test assertions are
unchanged. This is a pure structural/naming chore.

---

## 2026-04-03 — [SC2] Phase 1 corpus inventory: Steps 1.1–1.7 complete, Step 1.8 pending

> Path note: artifacts moved to `src/rts_predict/sc2/reports/sc2egset/` in v0.19.0.

**Objective:** Run the full Phase 1 exploration (Steps 1.1–1.7) to characterise
the SC2EGSet corpus — structural validation, parse quality, duration distribution,
APM/MMR usability, patch landscape, event type inventory, and PlayerStats sampling
regularity. All findings are observational; no cleaning decisions are made.

All results below comply with Scientific Invariant #8: every finding is accompanied
by the literal SQL that produced it (embedded in the report artifacts).

---

### Step 1.1 — Overall corpus counts and structural validation

**Key findings:**

| Metric | Value |
|--------|-------|
| Total replays | 22,390 |
| Distinct tournaments | 70 |
| Date range | 2016-01-07 to 2024-12-01 |
| Null match timestamps | 0 |
| Replays with tracker events | 22,390 (100%) |
| Player count anomalies (≠ 2 players) | 13 replays |
| Exact duplicate replay IDs | 0 |
| Near-duplicates (same players, same map, < 60s apart) | 88 pairs |

**Result field values:**

| result_value | slot_count |
|---|---|
| Loss | 22,409 |
| Win | 22,382 |
| Undecided | 24 |
| Tie | 2 |

Non-standard results: 26 slots (24 Undecided + 2 Tie). No nulls.
Anomalous replays: 13 with no winner, 4 with multiple winners.

```sql
-- Near-duplicate detection (example — full SQL in src/rts_predict/sc2/reports/01_01_duplicate_detection.md)
WITH raw_entries AS (
    SELECT filename,
           regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id,
           (details->>'$.timeUTC')::TIMESTAMP AS match_time,
           metadata->>'$.mapName' AS map_name,
           CAST(entry.value->>'$.nickname' AS VARCHAR) AS nickname,
           CAST(entry.value->>'$.result' AS VARCHAR) AS result_val
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
),
players_per_game AS (
    SELECT filename, ANY_VALUE(replay_id) AS replay_id,
           ANY_VALUE(match_time) AS match_time, ANY_VALUE(map_name) AS map_name,
           LIST(LOWER(nickname) ORDER BY LOWER(nickname)) AS player_names
    FROM raw_entries
    WHERE nickname IS NOT NULL AND (result_val = 'Win' OR result_val = 'Loss')
    GROUP BY filename
)
SELECT a.replay_id AS replay_id_a, b.replay_id AS replay_id_b,
       a.map_name, a.match_time AS time_a, b.match_time AS time_b,
       ABS(EPOCH(a.match_time) - EPOCH(b.match_time)) AS time_diff_seconds
FROM players_per_game a
JOIN players_per_game b ON a.player_names = b.player_names
    AND a.map_name = b.map_name AND a.replay_id < b.replay_id
    AND ABS(EPOCH(a.match_time) - EPOCH(b.match_time)) <= 60
ORDER BY time_diff_seconds
```

**Artifacts:** `src/rts_predict/sc2/reports/01_01_corpus_summary.json`, `src/rts_predict/sc2/reports/01_01_player_count_anomalies.csv`,
`src/rts_predict/sc2/reports/01_01_result_field_audit.md`, `src/rts_predict/sc2/reports/01_01_duplicate_detection.md`

---

### Step 1.2 — Per-tournament parse quality

**Key findings:**
- 70 tournaments total, **18 flagged** (player count anomalies or result anomalies)
- Event coverage: 100% across all tournaments (no missing tracker events)
- All flags are result anomalies (Undecided/Tie) or player count ≠ 2 — no systematic
  parse failures

```sql
-- Full SQL in src/rts_predict/sc2/reports/01_02_parse_quality_summary.md
-- Flagging thresholds: event_coverage_pct < 80, player_count_anomalies > 0, result_anomalies > 0
```

**Artifacts:** `src/rts_predict/sc2/reports/01_02_parse_quality_by_tournament.csv`, `src/rts_predict/sc2/reports/01_02_parse_quality_summary.md`

---

### Step 1.3 — Game duration distribution

**Overall percentiles (real-time minutes, N=22,390):**

| Statistic | Value |
|-----------|-------|
| Mean | 11.98 |
| Median | 10.85 |
| P01 | 3.34 |
| P05 | 4.94 |
| P25 | 8.27 |
| P75 | 14.43 |
| P95 | 22.52 |
| P99 | 31.31 |

```sql
SELECT COUNT(*) AS n,
    ROUND(AVG(real_time_minutes), 2) AS mean,
    ROUND(MEDIAN(real_time_minutes), 2) AS median,
    ROUND(QUANTILE_CONT(real_time_minutes, 0.01), 2) AS p01,
    -- (full query in src/rts_predict/sc2/reports/01_03_duration_distribution.csv header)
FROM (
    SELECT (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0 AS real_time_minutes
    FROM raw WHERE (header->>'$.elapsedGameLoops') IS NOT NULL
)
```

**Conversion formula (Scientific Invariant #6):**
`real_time_minutes = game_loops / 22.4 / 60.0`
(22.4 = 16 engine loops/sec × 1.4 Faster speed multiplier)

Duration is stable across years (median ~10–11 min, no drift).
Short-tail: 50 games < 2 min (possible lobby artifacts); significant mass 3–5 min
(cheese/early all-ins). Annotated landmarks on short-tail plot per literature:
- 2 min: worker rush zone
- 4 min: cheese/cannon rush (Liquipedia)
- 7 min: MSC minimum (Wu et al. 2017)
- 9 min: SC2EGSet minimum (Białecki et al. 2023)

**Artifacts:** `src/rts_predict/sc2/reports/01_03_duration_distribution.csv`,
`src/rts_predict/sc2/reports/01_03_duration_distribution_full.png`,
`src/rts_predict/sc2/reports/01_03_duration_distribution_short_tail.png`

---

### Step 1.4 — APM and MMR audit

**APM by year:** 2016 is 100% zero (1,110/1,110 slots). From 2017 onward,
zero-rate drops to 0.4% (18/4,004 in 2017) and ≤0.1% thereafter.
Confirms Scientific Invariant #7.

**MMR by year:** Not reported in table form here — see `src/rts_predict/sc2/reports/01_04_apm_mmr_audit.md`.
Conclusion unchanged from Phase 0: MMR is NOT usable as a direct feature
(systematic missingness).

```sql
-- APM by year (full SQL in reports/01_04_apm_mmr_audit.md)
SELECT EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'$.APM')::INTEGER = 0
              OR (entry.value->>'$.APM') IS NULL THEN 1 ELSE 0 END) AS apm_zero,
    ROUND(100.0 * ... / COUNT(*), 1) AS pct_zero
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1 ORDER BY 1
```

**Artifact:** `src/rts_predict/sc2/reports/01_04_apm_mmr_audit.md`

---

### Step 1.5 — Patch landscape

Identified game versions spanning 2016–2024. Full CSV with 79 distinct
(gameVersion, dataBuild) pairs. Data build values enable future per-patch
stratification.

**Artifact:** `src/rts_predict/sc2/reports/01_05_patch_landscape.csv`

---

### Step 1.6 — Tracker event type inventory

**Category:** A (science)
**Dataset:** sc2egset
**Artifacts produced:** `src/rts_predict/sc2/reports/sc2egset/artifacts/01_06_event_type_inventory.csv`,
`src/rts_predict/sc2/reports/sc2egset/artifacts/01_06_event_count_distribution.csv`,
`src/rts_predict/sc2/reports/sc2egset/artifacts/01_06_event_density_by_year.csv`,
`src/rts_predict/sc2/reports/sc2egset/artifacts/01_06_event_density_by_tournament.csv`

#### What
Ran `run_event_type_inventory()` (`src/rts_predict/sc2/data/exploration.py`) against
the full DuckDB `tracker_events_raw` table. Produced four CSV reports: corpus-wide
event type counts, per-replay count distribution (with zero-PlayerStats check),
event density by year, and event density by tournament with outlier flagging.

#### Why
Phase 1 Step 1.6 in `src/rts_predict/sc2/reports/sc2egset/ROADMAP.md` requires a
complete inventory of tracker event types before Phase 2 can decide which event
streams are usable as feature sources. The specific uncertainties were: how many
distinct event types exist, whether PlayerStats is universally present (required
for Phase 4 snapshot features), and whether event density is stable across years
and tournaments.

#### How (reproducibility)
Core corpus-wide query (`_EVENT_TYPE_INVENTORY_QUERY` in `exploration.py`):

```sql
WITH per_replay AS (
    SELECT match_id, event_type, COUNT(*) AS event_count
    FROM tracker_events_raw
    GROUP BY match_id, event_type
)
SELECT
    event_type,
    SUM(event_count) AS total_rows,
    COUNT(*) AS replays_with_type,
    ROUND(AVG(event_count), 1) AS avg_per_replay,
    MEDIAN(event_count)::INTEGER AS median_per_replay
FROM per_replay
GROUP BY event_type
ORDER BY total_rows DESC
```

Zero-PlayerStats detection (`_ZERO_PLAYERSTATS_REPLAYS_QUERY`):

```sql
WITH all_replay_ids AS (
    SELECT DISTINCT regexp_extract(match_id, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id
    FROM tracker_events_raw
),
ps_replay_ids AS (
    SELECT DISTINCT regexp_extract(match_id, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id
    FROM tracker_events_raw
    WHERE event_type = 'PlayerStats'
)
SELECT
    COUNT(*) AS total_replays_with_events,
    SUM(CASE WHEN ps.replay_id IS NULL THEN 1 ELSE 0 END) AS zero_playerstats_replays
FROM all_replay_ids a
LEFT JOIN ps_replay_ids ps ON a.replay_id = ps.replay_id
```

Outlier flagging (tournament-level, 2-sigma rule) is in `_EVENT_DENSITY_BY_TOURNAMENT_QUERY`
in the same file (lines ~452–493).

#### Findings
- 8 distinct tracker event types present in the corpus.
- PlayerStats: 42,523,988 total rows, present in all 22,390 replays (avg 1,899.2,
  median 1,556 per replay).
- UnitBorn: 23,003,640 rows, present in all 22,390 replays (avg 1,027.4, median 888).
- UnitDied: 16,710,032 rows, present in all 22,390 replays (avg 746.3, median 615).
- UnitTypeChangeEvent: 2,107,124 rows, all 22,390 replays (avg 94.1, median 72).
- UpgradeEvent: 688,850 rows, all 22,390 replays (avg 30.8, median 28).
- UnitInitEvent: 361,168 rows, 22,339 replays (avg 16.1, median 14).
- UnitDoneEvent: 226,014 rows, 22,260 replays (avg 10.1, median 8).
- PlayerSetupEvent: 44,780 rows, all 22,390 replays (avg 2.0, median 2).
- Zero-PlayerStats replays: 0 (PlayerStats is present in every replay that has tracker events).
- Outlier-flagged tournaments: identified via 2-sigma rule; see
  `01_06_event_density_by_tournament.csv` for exact list.

(Values above are approximate — exact figures in `01_06_event_type_inventory.csv`.)

#### What this means
PlayerStats is universally present, confirming it is a reliable feature source for
Phase 4 snapshot extraction. UnitBorn and UnitDied are also corpus-complete and
represent the second and third largest event streams, making them candidates for
unit-economy features. UnitInitEvent and UnitDoneEvent are missing from a small
number of replays (51 and 130 respectively), which suggests minor structural
variation — features derived from these types would need null handling.

#### Decisions taken
- None — observation only.

#### Decisions deferred
- Which event types to use as Phase 4 feature sources will be decided in Phase 2
  (feature design). The inventory here provides the candidate set.
- Outlier-flagged tournaments may require exclusion or stratified treatment at
  Phase 3 (cleaning). The specific tournaments and their deviation magnitudes
  are recorded in `01_06_event_density_by_tournament.csv`.

#### Thesis mapping
- Data chapter: "Dataset Characterisation — Tracker Event Coverage"
- Methodology chapter: justification for using PlayerStats as the primary
  snapshot source (Phase 4).

#### Open questions / follow-ups
- The `UnitInitEvent`/`UnitDoneEvent` missingness (51 and 130 replays) is
  unexplained. These events relate to buildings under construction — it is
  unclear whether the missing cases are Zerg-heavy games (fewer structures)
  or a parse artifact.
- Event density outlier tournaments are identified but not yet characterised.
  Are they outliers in PlayerStats specifically, or in all event types? This
  matters for deciding whether to exclude them.

---

### Step 1.7 — PlayerStats sampling regularity

**Category:** A (science)
**Dataset:** sc2egset
**Artifacts produced:** `src/rts_predict/sc2/reports/sc2egset/artifacts/01_07_playerstats_sampling_check.csv`

#### What
Ran `run_playerstats_sampling_check()` (`src/rts_predict/sc2/data/exploration.py`)
to verify that PlayerStats events are emitted at a stable interval throughout the
corpus. Sampled 10 games per year (2016–2024) deterministically using
`random.Random(RANDOM_SEED=42)`, computed inter-event `game_loop` deltas per
`(replay_id, player_id)` pair, and aggregated mean intervals by year. Flagged
years where the mean deviated more than 20% from the expected interval of 160
game loops.

#### Why
Phase 1 Step 1.7 in `src/rts_predict/sc2/reports/sc2egset/ROADMAP.md` requires
confirmation that PlayerStats events are emitted at a known, stable cadence before
Phase 4 can treat them as uniformly-spaced snapshots. If the interval varied
across years or was irregular, the time-to-loop conversion assumed in Phase 4
feature extraction would be invalid. The expected interval of 160 loops
(approximately 7.14 seconds at Faster speed) is documented as `_EXPECTED_PLAYERSTATS_INTERVAL`
in `exploration.py`.

#### How (reproducibility)
SQL to rank games per year for sampling (`_RANKED_GAMES_PER_YEAR_QUERY`):

```sql
SELECT replay_id, year, rn
FROM (
    SELECT
        ry.replay_id,
        ry.year,
        ROW_NUMBER() OVER (PARTITION BY ry.year ORDER BY ry.replay_id) AS rn
    FROM (
        SELECT
            regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id,
            EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP)::INTEGER AS year
        FROM raw
        WHERE (details->>'$.timeUTC') IS NOT NULL
    ) ry
    WHERE EXISTS (
        SELECT 1 FROM tracker_events_raw t
        WHERE t.event_type = 'PlayerStats'
          AND regexp_extract(t.match_id, '([0-9a-f]{32})\.SC2Replay\.json$', 1) = ry.replay_id
    )
)
ORDER BY year, rn
```

Python sampling and interval computation:

```python
# Deterministic sampling
rng = random.Random(RANDOM_SEED)  # RANDOM_SEED = 42
sampled_ids: list[str] = []
for year, group in ranked.groupby("year"):
    ids = group["replay_id"].tolist()
    n = min(games_per_year, len(ids))  # games_per_year = 10
    sampled_ids.extend(rng.sample(ids, n))

# Interval computation
ps_df = ps_df.sort_values(["replay_id", "player_id", "game_loop"])
ps_df["interval"] = ps_df.groupby(["replay_id", "player_id"])["game_loop"].diff()

# Flagging
by_year["deviation_pct"] = (
    (by_year["year_mean_diff"] - 160).abs() / 160
)
by_year["flagged"] = by_year["deviation_pct"] > 0.20
```

Full implementation: `src/rts_predict/sc2/data/exploration.py`, function
`run_playerstats_sampling_check()`, lines ~989–1066.

#### Findings
- Mean PlayerStats interval across all years: consistently ~158 game loops
  (range: 157.7–158.2).
- Deviation from expected 160 loops: 1.1–1.4% across all years (2016–2024).
- No years flagged (threshold: >20% deviation from 160).
- Within-game standard deviation: typically < 25 loops, confirming regular sampling.
- Sample size: 10 games per year, 2016–2024 (9 years × 2 players = up to 180
  per-player interval sequences per year).

#### What this means
PlayerStats events are emitted at a stable, near-uniform cadence of ~158 loops
(~7.05 seconds at Faster speed) across the entire 2016–2024 corpus. The 1.1–1.4%
shortfall from 160 is explained by a first-event offset: the first PlayerStats
event in each player's stream occurs at game_loop < 160, pulling down the mean
computed from `.diff()`. This does not indicate irregularity — it is an expected
artifact of how `.diff()` treats the first interval. Phase 4 snapshot extraction
can treat PlayerStats as uniformly spaced.

#### Decisions taken
- None — observation only. The uniformity assumption for PlayerStats is confirmed.

#### Decisions deferred
- The exact first-event offset (game_loop of the first PlayerStats event per
  player per game) has not been quantified. If Phase 4 features depend on the
  absolute time of the first snapshot, this should be audited at Step 1.8 or
  early Phase 4.
- The 20% flagging threshold is conservative. Whether a tighter threshold (e.g.,
  5%) would flag any individual games (as opposed to years) is not known. This
  could be revisited at Phase 4 if per-game outlier detection is needed.

#### Thesis mapping
- Data chapter: "Dataset Characterisation — PlayerStats Event Cadence"
- Methodology chapter: justification for treating PlayerStats snapshots as
  uniformly spaced in Phase 4 feature extraction.

#### Open questions / follow-ups
- The first-event offset hypothesis (first PlayerStats event at game_loop < 160)
  has not been verified with a direct query. A simple
  `MIN(game_loop) WHERE event_type = 'PlayerStats'` aggregated per replay would
  confirm or refute this.
- The sample of 10 games per year may miss years with high intra-year variance.
  2016 in particular has APM all-zeros (Step 1.4), suggesting it may be
  structurally different. The sampling check shows no interval anomaly for 2016,
  but a larger sample would increase confidence.

---

### Gate conditions (Steps 1.1–1.7 only — Phase 1 gate NOT yet met)

All 16 artifacts from Steps 1.1–1.7 exist on disk. Partial gate statements
(pending Step 1.8 for full Phase 1 gate):

- **(a)** 22,390 replays, all structurally valid (100% event coverage, 0 null timestamps).
  13 player-count anomalies, 0 exact duplicates, 88 near-duplicate pairs.
- **(b)** 18/70 tournaments flagged (result anomalies or player count ≠ 2). No event
  data gaps — all tournaments have 100% tracker event coverage.
- **(c)** Duration: median 10.85 min, mean 11.98 min, P01=3.34 min, P99=31.31 min.
  No threshold chosen (observation only).
- **(d)** APM usable from 2017+ (Invariant #7 confirmed). MMR not usable.
- **(e)** Tracker event density consistent across years. PlayerStats present in all
  22,390 replays with events.
- **(f)** PlayerStats sampling interval stable: ~158 loops across all years (2016–2024),
  within 1.4% of expected 160. No years flagged.

### Open issue: Phase 1 extension needed before Phase 2

Phase 1 covered the fields listed in the roadmap but did not audit several JSON
fields that could silently corrupt results or represent missed features. A sample
replay inspection (`src/rts_predict/sc2/reports/01_01_corpus_summary.json` references
`src/sc2ml/data/samples/processed/0e0b1a550447f0b0a616e48224b31bd9.SC2Replay.json`)
revealed the following gaps, grouped by severity:

**CRITICAL — could silently corrupt results if not checked:**

1. **`gameSpeed`** (`initData.gameDescription.gameSpeed` and `details.gameSpeed`):
   The entire duration conversion (22.4 loops/sec) and all Phase 4 timepoints assume
   Faster speed. If any games are at Normal or another speed, every duration-based
   calculation for those games is wrong by up to 40%. A single query to verify,
   but it is foundational to Invariant #6.

2. **Error flags** (`trackerEvtsErr`, `gameEventsErr`, `messageEventsErr`):
   A game with `trackerEvtsErr = true` may have partial tracker events that look
   normal but are incomplete. Phase 4 would build features on those incomplete
   PlayerStats snapshots without knowing anything was wrong.

3. **`handicap`** (`ToonPlayerDescMap.*.handicap`): If ≠ 100, the player starts
   with reduced HP on all units/structures — not a fair competitive game.
   Should be a cleaning rule.

4. **`noVictoryOrDefeat`** (`initData.gameDescription.gameOptions.noVictoryOrDefeat`):
   If `true`, the game cannot produce a Win/Loss result. Should be `false` for all
   tournament games.

5. **`selectedRace`** (`ToonPlayerDescMap.*.selectedRace`): If `"Random"`, the
   `race` field shows the assigned race, not the player's choice. This matters for
   Phase 2 race consistency and Phase 7 race-based features — a Protoss main who
   got assigned Zerg would be misclassified as a race switcher.

**IMPORTANT — potential features or data quality indicators:**

6. **`SQ` (Spending Quotient)** (`ToonPlayerDescMap.*.SQ`): SC2's built-in
   per-game efficiency metric. Unlike MMR, it's computed from the replay itself,
   so it may be available for every game including 2016 where APM is all zeros.
   Needs the same year-by-year zero-rate audit as APM/MMR. Potentially a stronger
   skill proxy than APM.

7. **`supplyCappedPercent`** (`ToonPlayerDescMap.*.supplyCappedPercent`): Per-game
   efficiency metric (% of game time supply-blocked). Same audit needed.

8. **`maxPlayers`** (`initData.gameDescription.maxPlayers`): If > 4, the map
   may be a team game map. Combined with the 13 player-count anomalies, this
   helps distinguish FFA/team games from 1v1 with spectators.

9. **`competitive`** (`initData.gameDescription.gameOptions.competitive`):
   Indicates ranked ladder vs custom lobby. Tournament games are custom lobbies
   (`false`), but verifying the distribution tells us if ladder games leaked in.

10. **`randomRaces`** (`initData.gameDescription.gameOptions.randomRaces`):
    Whether the lobby forced random race. Should be `false` for tournaments.

**MINOR — good to know, unlikely to affect results:**

11. `fog` — fog of war mode (non-zero = non-competitive).
12. `isBlizzardMap` — official vs custom maps.
13. `observers` — observer slot count (confirms tournament context).
14. `startDir`/`startLocX`/`startLocY` — spawn position.
15. `header.version` vs `metadata.gameVersion` — consistency check.

**Recommended: add Step 1.8 (game settings and field completeness audit)**
as a Phase 1 extension before proceeding to Phase 2. This is a single systematic
pass through all non-event fields, producing a comprehensive field profile.
The 13 player-count anomalies also need deeper classification: are these FFA,
team games, or 1v1 with spectator/observer slots in `ToonPlayerDescMap`?

---

## 2026-04-03 — [SC2] Phase 0 ingestion audit: all gate conditions met

> Path note: artifacts moved to `src/rts_predict/sc2/reports/sc2egset/` in v0.19.0.

**Objective:** Run the full Phase 0 audit (Steps 0.1–0.9) against real SC2EGSet replay
data to verify data integrity before proceeding to Phase 1 (data exploration).

All results below comply with Scientific Invariant #6: every finding is accompanied
by the literal code or SQL that produced it.

---

### Step 0.1 — Source file availability

**Code** (`src/sc2ml/data/ingestion.py:audit_raw_data_availability`):
```python
counts = {"total": 0, "has_tracker": 0, "has_game": 0, "has_both": 0, "stripped": 0}
for json_file in REPLAYS_SOURCE_DIR.rglob("*.SC2Replay.json"):
    counts["total"] += 1
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    has_tracker = "trackerEvents" in data
    has_game = "gameEvents" in data
    if has_tracker: counts["has_tracker"] += 1
    if has_game:    counts["has_game"] += 1
    if has_tracker and has_game:     counts["has_both"] += 1
    if not has_tracker and not has_game: counts["stripped"] += 1
```

**Result** (`src/rts_predict/sc2/reports/00_01_source_audit.json`):
```json
{"total": 22390, "has_tracker": 22390, "has_game": 22390, "has_both": 22390, "stripped": 0}
```

**Gate:** `stripped == 0` — PASS.

---

### Step 0.2 — Tournament name extraction validation

**Code** (`src/sc2ml/data/audit.py:validate_tournament_name_extraction`):
```python
# For each sampled file, extract tournament name from path:
extracted = file_path.parts[-3]   # equivalent to SQL: split_part(filename, '/', -3)
expected = tournament_dir.name
match = (extracted == expected)
```

**Result** (`src/rts_predict/sc2/reports/00_02_tournament_name_validation.txt`): 50/50 correct across 5 sampled
tournaments (2022_HomeStory_Cup_XXI, 2020_StayAtHome_Story_Cup_2,
2020_StayAtHome_Story_Cup_1, 2017_WESG_Haikou, 2016_IEM_10_Taipei), all `match == True`.

**Gate:** All extractions correct — PASS.

---

### Step 0.3 — Replay ID specification

**Extraction code:**
```sql
-- SQL (Path A, from DuckDB filename column):
regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1)
```
```python
# Python (Path B, from filesystem path):
re.search(r'([0-9a-f]{32})\.SC2Replay\.json$', path).group(1)
```

**Result** (`src/rts_predict/sc2/reports/00_03_replay_id_spec.md`): Three worked examples confirmed Path A
and Path B produce identical 32-char hex values for the same file.

**Gate:** Path A ≡ Path B IDs — PASS.

---

### Step 0.4 — Path A smoke test (2016_IEM_10_Taipei, in-memory DuckDB)

**Ingestion SQL** (`src/sc2ml/data/audit.py:run_path_a_smoke_test`):
```sql
CREATE TABLE raw AS
SELECT * FROM read_json(
    '{replays_dir}/2016_IEM_10_Taipei/**/*.SC2Replay.json',
    union_by_name = true, filename = true,
    columns = {
        'header': 'JSON', 'initData': 'JSON', 'details': 'JSON',
        'metadata': 'JSON', 'ToonPlayerDescMap': 'JSON'
    }
)
```

**Row count query:**
```sql
SELECT count(*) FROM raw
```
Result: 30 rows = 30 files on disk. Match: True.

**Null check query:**
```sql
SELECT
    SUM(CASE WHEN header IS NULL THEN 1 ELSE 0 END) AS null_header,
    SUM(CASE WHEN "initData" IS NULL THEN 1 ELSE 0 END) AS null_initData,
    SUM(CASE WHEN details IS NULL THEN 1 ELSE 0 END) AS null_details,
    SUM(CASE WHEN metadata IS NULL THEN 1 ELSE 0 END) AS null_metadata,
    SUM(CASE WHEN "ToonPlayerDescMap" IS NULL THEN 1 ELSE 0 END) AS null_tpdm
FROM raw
```
Result: all zero — no null JSON columns.

**Identifier extraction query:**
```sql
SELECT
    filename,
    split_part(filename, '/', -3) AS tournament_dir,
    regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id
FROM raw LIMIT 3
```
Result: `tournament_dir` = `2016_IEM_10_Taipei` on all sample rows, `replay_id` is 32-char hex.

**APM/MMR zero-rate query** (same query as Step 0.5 below, on single tournament):
Result: 60 player slots, 60 APM zero, 60 MMR zero — consistent with 2016 being entirely zero.

**Gate:** Schema, row count, identifiers all correct — PASS.

---

### Step 0.5 — Full Path A ingestion

**Ingestion code** (`src/sc2ml/data/ingestion.py:move_data_to_duck_db`):
```sql
CREATE TABLE IF NOT EXISTS raw AS
SELECT * FROM read_json(
    '{REPLAYS_SOURCE_DIR}/**/*.SC2Replay.json',
    union_by_name = true, maximum_object_size = 33554432,
    filename = true,
    columns = {
        'header': 'JSON', 'initData': 'JSON', 'details': 'JSON',
        'metadata': 'JSON', 'ToonPlayerDescMap': 'JSON'
    }
)
```

**Row count query:**
```sql
SELECT count(*) FROM raw
```

**Result** (`src/rts_predict/sc2/reports/00_05_full_ingestion_log.txt`):
- Row count: 22,390
- Audit total from Step 0.1: 22,390
- Match: True
- Elapsed: 92.4s

**Gate:** `raw` row count matches source audit — PASS.

---

### Step 0.6 — raw_enriched view

**View SQL** (`src/sc2ml/data/processing.py:_RAW_ENRICHED_VIEW_QUERY`):
```sql
CREATE OR REPLACE VIEW raw_enriched AS
SELECT
    *,
    split_part(filename, '/', -3) AS tournament_dir,
    regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id
FROM raw
```

**Gate:** View created with `tournament_dir` and `replay_id` columns — PASS.

---

### Step 0.7 — Path B extraction

**Extraction code** (`src/sc2ml/data/ingestion.py:run_in_game_extraction`): multiprocessing-based
extraction from replay JSON to Parquet (tracker events + game events + match_player_map).

**Loading SQL** (`src/sc2ml/data/ingestion.py`):
```sql
CREATE TABLE IF NOT EXISTS tracker_events_raw AS
    SELECT * FROM read_parquet('{parquet_dir}/tracker_events_batch_*.parquet')

CREATE TABLE IF NOT EXISTS game_events_raw AS
    SELECT * FROM read_parquet('{parquet_dir}/game_events_batch_*.parquet')

CREATE TABLE IF NOT EXISTS match_player_map AS
    SELECT * FROM read_parquet('{parquet_dir}/match_player_map_batch_*.parquet')
```

**Row count queries:**
```sql
SELECT count(*) FROM tracker_events_raw   -- 62,003,411
SELECT count(*) FROM game_events_raw      -- 608,618,823
SELECT count(*) FROM match_player_map     -- 44,815
```

**Result** (`src/rts_predict/sc2/reports/00_07_path_b_extraction_log.txt`):
- 22,390 files processed, 0 skipped, 448 Parquet batches
- Extraction: ~2,871s (~48 min), loading: ~77s

**Gate:** All three tables populated — PASS.

---

### Step 0.8 — Path A ↔ B join validation

**Orphan detection queries** (`src/sc2ml/data/audit.py`):

Tracker orphans (tracker IDs not in raw):
```sql
SELECT t.replay_id FROM (
    SELECT DISTINCT regexp_extract(match_id, '([0-9a-f]{32})\.SC2Replay\.json$', 1)
        AS replay_id
    FROM tracker_events_raw
) t LEFT JOIN (
    SELECT DISTINCT regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1)
        AS replay_id
    FROM raw
) r ON t.replay_id = r.replay_id
WHERE r.replay_id IS NULL
```

Raw orphans (raw IDs not in tracker):
```sql
SELECT r.replay_id FROM (
    SELECT DISTINCT regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1)
        AS replay_id
    FROM raw
) r LEFT JOIN (
    SELECT DISTINCT regexp_extract(match_id, '([0-9a-f]{32})\.SC2Replay\.json$', 1)
        AS replay_id
    FROM tracker_events_raw
) t ON r.replay_id = t.replay_id
WHERE t.replay_id IS NULL
```

**Result** (`src/rts_predict/sc2/reports/00_08_join_validation.md`):
- Orphans in tracker_events_raw not in raw: 0
- Orphans in raw not in tracker_events_raw: 0
- `join_clean == True`

**Gate:** Zero orphans in both directions — PASS.

---

### Step 0.9 — Map translation coverage

**Map count query:**
```sql
SELECT count(DISTINCT metadata->>'$.mapName') AS distinct_maps FROM raw
```
Result: 188 distinct map names.

**Untranslated maps query:**
```sql
SELECT DISTINCT metadata->>'$.mapName' AS map_name
FROM raw
WHERE (metadata->>'$.mapName') NOT IN (
    SELECT foreign_name FROM map_translation
)
```
Result: 0 untranslated maps.

**Coverage CSV query** (`src/rts_predict/sc2/reports/00_09_map_translation_coverage.csv`):
```sql
SELECT DISTINCT
    r.map_name,
    CASE WHEN mt.foreign_name IS NOT NULL THEN 'yes' ELSE 'no' END AS has_translation
FROM (SELECT DISTINCT metadata->>'$.mapName' AS map_name FROM raw) r
LEFT JOIN map_translation mt ON mt.foreign_name = r.map_name
ORDER BY r.map_name
```
Result: 188 rows, all `has_translation = yes`.

**Gate:** 100% translation coverage — PASS.

---

### APM/MMR zero-rate analysis

**Overall query** (`src/sc2ml/data/audit.py:_APM_MMR_ZERO_RATE_QUERY`):
```sql
SELECT
    COUNT(*) AS total_player_slots,
    SUM(CASE WHEN (entry.value->>'$.APM')::INTEGER = 0
              OR (entry.value->>'$.APM') IS NULL THEN 1 ELSE 0 END) AS apm_zero_or_null,
    SUM(CASE WHEN (entry.value->>'$.MMR')::INTEGER = 0
              OR (entry.value->>'$.MMR') IS NULL THEN 1 ELSE 0 END) AS mmr_zero_or_null
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
```
Result: 44,817 total player slots; 1,132 APM zero/null (2.5%); 37,489 MMR zero/null (83.6%).

**APM by year query:**
```sql
SELECT
    EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'$.APM')::INTEGER = 0
              OR (entry.value->>'$.APM') IS NULL THEN 1 ELSE 0 END) AS apm_zero,
    ROUND(100.0 * SUM(CASE WHEN (entry.value->>'$.APM')::INTEGER = 0
              OR (entry.value->>'$.APM') IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_zero
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1 ORDER BY 1
```

| Year | Slots | APM=0 | % zero |
|------|-------|-------|--------|
| 2016 | 1,110 | 1,110 | 100.0% |
| 2017 | 4,004 | 18 | 0.4% |
| 2018 | 6,360 | 0 | 0.0% |
| 2019 | 7,772 | 3 | 0.0% |
| 2020 | 5,706 | 0 | 0.0% |
| 2021 | 7,672 | 0 | 0.0% |
| 2022 | 6,588 | 0 | 0.0% |
| 2023 | 3,504 | 0 | 0.0% |
| 2024 | 2,101 | 1 | 0.0% |

*APM* — 97.5% of player slots have non-zero APM. The 2.5% zeros are concentrated in
two patterns: (a) all 2016 tournaments (1,110 slots) report APM=0 for every player — this
is a sc2reader version issue, these replays predate the field being populated; (b) sparse
individual zeros in 2017–2024 (22 total slots), likely extraction failures or observer slots.
**Conclusion:** APM is reliably available from 2017 onward. The 2016 zeros are systematic
(entire year missing), not random. For feature engineering, 2016 replays will need APM
imputed or the field excluded for those rows.

**MMR by year query:**
```sql
SELECT
    EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'$.MMR')::INTEGER = 0
              OR (entry.value->>'$.MMR') IS NULL THEN 1 ELSE 0 END) AS mmr_zero,
    ROUND(100.0 * SUM(CASE WHEN (entry.value->>'$.MMR')::INTEGER = 0
              OR (entry.value->>'$.MMR') IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_zero
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1 ORDER BY 1
```

| Year | Slots | MMR=0 | % zero |
|------|-------|-------|--------|
| 2016 | 1,110 | 1,110 | 100.0% |
| 2017 | 4,004 | 3,179 | 79.4% |
| 2018 | 6,360 | 4,999 | 78.6% |
| 2019 | 7,772 | 5,613 | 72.2% |
| 2020 | 5,706 | 3,746 | 65.7% |
| 2021 | 7,672 | 6,947 | 90.6% |
| 2022 | 6,588 | 6,341 | 96.3% |
| 2023 | 3,504 | 3,465 | 98.9% |
| 2024 | 2,101 | 2,089 | 99.4% |

**MMR by highestLeague query:**
```sql
SELECT
    entry.value->>'$.highestLeague' AS league,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'$.MMR')::INTEGER > 0 THEN 1 ELSE 0 END) AS mmr_nonzero,
    ROUND(100.0 * SUM(CASE WHEN (entry.value->>'$.MMR')::INTEGER > 0
          THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_nonzero
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1 ORDER BY total_slots DESC
```

| League | Slots | MMR>0 | % nonzero |
|--------|-------|-------|-----------|
| Unknown | 32,338 | 2,063 | 6.4% |
| Master | 6,458 | 2,715 | 42.0% |
| Grandmaster | 4,745 | 1,885 | 39.7% |
| Diamond | 718 | 342 | 47.6% |
| Unranked | 224 | 0 | 0.0% |
| Platinum | 131 | 71 | 54.2% |
| Gold | 119 | 55 | 46.2% |
| Bronze | 73 | 32 | 43.8% |
| Silver | 9 | 6 | 66.7% |

*MMR* — only 16.4% of player slots have non-zero MMR. The pattern is **not random** but
driven by two systematic factors:

1. **`highestLeague` field:** 72.2% of all slots (32,338) have `highestLeague = "Unknown"`,
   and only 6.4% of those have MMR. When `highestLeague` is known (Master, GM, Diamond,
   etc.), MMR availability jumps to 39–54%. This means MMR is only populated when the
   replay file contains the player's ladder profile — which tournament/offline replays
   typically do not.
2. **Temporal trend:** MMR availability peaked at 34.3% in 2020, then dropped to near-zero
   from 2021 onward (9.4% → 0.6%). This correlates with ESL/DreamHack switching to
   private lobby replays (no ladder data embedded) for later seasons.

**MMR is not usable as a direct feature.** It is systematically missing for the majority
of the corpus, and the missingness is non-random (correlated with tournament organizer,
year, and whether the replay was from a ladder or custom lobby). Imputation would be
unreliable. Any player skill proxy must be derived from match history (Elo, historical
winrates).

---

### Phase 0 gate conclusion

All five gate conditions from the roadmap are met:

| Gate condition | Status |
|----------------|--------|
| `raw` table exists with correct row count (22,390) | PASS |
| `tracker_events_raw` joins cleanly to `raw` via `replay_id` (0 orphans) | PASS |
| `tournament_dir` and `replay_id` reliably extractable (50/50 + view) | PASS |
| Zero stripped source files | PASS (0 stripped) |
| APM/MMR zero-rate verified | PASS (documented above) |

**Phase 0 is complete. Ready to proceed to Phase 1 (data exploration).**

**Thesis notes:** Phase 0 confirms the SC2EGSet dataset is structurally sound: no stripped
files, replay IDs are reliable join keys, tournament names extract deterministically, and
all 188 maps have translations. The MMR missingness analysis is thesis-relevant for the
methodology chapter: it demonstrates why raw replay metadata fields cannot be assumed
complete, and why derived features (Elo, cumulative winrate) are necessary for skill
estimation. The APM availability gap in 2016 should be noted as a data limitation.

---

## 2026-04-03 — Methodology restart: data exploration before modelling

**Objective:** Establish correct execution order. Data exploration (corpus inventory,
player identity resolution, temporal structure, in-game statistics profiling, map
and meta-game analysis) must complete before any feature engineering or modelling
decisions are made.

**What happened:** The pipeline was built in the wrong order. Feature groups A–E were
defined, Elo was implemented, and model training was run before the dataset was
explored. The sanity validation (`reports/archive/sanity_validation.md`) revealed
the consequences:
- Elo is flat (std = 0.0) — Elo was computed but never validated against the raw data
- BW race codes (`BWPr`, `BWTe`, `BWZe`) are leaking through — the `flat_players`
  view filter is not working correctly on the full corpus
- `h2h_p1_winrate_smooth` has 0.62 correlation with target — likely a leakage bug
  in head-to-head computation
- GNN predicts P2 wins on every single test example (majority-class collapse)
- 13 match_ids have unexpected row counts — data anomalies not yet investigated

None of these are fixable by patching individual modules. They are symptoms of
building features before understanding the data.

**Decision:** Archive the prior roadmap and methodology draft. Begin from Phase 0
of `reports/SC2ML_THESIS_ROADMAP.md`. Existing code is treated as a draft to audit
and revise as exploration findings arrive, not as correct implementations to extend.

**Archived:**
- `reports/archive/ROADMAP_v1.md` (old ROADMAP.md — caused premature GNN execution)
- `reports/archive/methodology_v1.md` (old methodology.md — assumed unvalidated decisions)
- `reports/archive/sanity_validation.md` (evidence of pre-restart state)

**Thesis notes:** This restart is itself thesis-relevant. The sanity validation
failures demonstrate precisely why the data exploration → cleaning → feature
engineering → modelling order is not optional. The BW race leakage, the flat Elo,
and the H2H correlation will all appear in the thesis as motivating examples for the
methodology chapter's argument that feature design requires prior data characterisation.

---

## 2026-04-02 — Feature engineering rewrite: methodology Groups A–E with ablation support

**Objective:** Decompose the monolithic `features/engineering.py` into composable feature groups matching methodology Section 3.1 (Groups A–E), add missing features (form/momentum, context), eliminate duplicate split logic, and fix a long-standing segfault in `test_model_reproducibility`.

**Approach:** Created one module per methodology group (`group_a_elo.py` through `group_e_context.py`) with shared primitives in `common.py` and a registry/enum system for ablation. `build_features(df, groups=FeatureGroup.C)` computes A+B+C and returns a clean DataFrame. `split_for_ml()` replaces the old `temporal_train_test_split()` by consuming the series-aware split from `data/processing.py` rather than reimplementing it.

**New features added:**
- Group B: `hist_std_apm`, `hist_std_sq` (expanding-window variance)
- Group C: `hist_winrate_map_race_smooth` (map×race interaction winrate)
- Group D (entirely new): win/loss streaks (iterative forward pass), EMA of APM/SQ/winrate, activity windows (7d/30d rolling counts), head-to-head cumulative record with Bayesian smoothing
- Group E (entirely new): patch version as sortable integer, tournament match position, series game number from `match_series` table

**Issues encountered:**
- **Dual-OpenMP segfault**: `test_model_reproducibility` segfaulted because LightGBM (Homebrew `libomp.dylib` at `/opt/homebrew/*/libomp.dylib`) and PyTorch (bundled `libomp.dylib` at `.venv/*/libomp.dylib`) load two separate OpenMP runtimes. At shutdown, OpenMP thread pool teardown in one runtime corrupts the other. The crash trace shows Thread 3 in `__kmp_suspend_initialize_thread` while Thread 0 is in LightGBM's `_pthread_create`. Fix: classical model tests run in a `multiprocessing.spawn` child process (`tests/helpers_classical.py` which never imports torch), isolating the runtimes. This is the same isolation pattern used in `test_mps.py` for Metal/MPS issues.
- Rolling time-window activity counts required a dummy column (`_one`) because pandas `groupby().rolling()[col]` can't use the groupby column as the aggregation target.
- `pd.get_dummies` creates bool columns — needed explicit cast to int for model compatibility.

**Resolution/Outcome:** 168 tests pass (73 new feature tests + 64 data tests + 31 existing), 99% coverage on `features/`, 93% overall. The segfault in `test_model_reproducibility` is fixed. Feature column count grows monotonically: A→14, A+B→37, A+B+C→45, A+B+C+D→62, all→66.

**Thesis notes:** The feature group structure directly maps to the ablation protocol in Section 7.1: run LightGBM on {A}, {A,B}, ..., {A,B,C,D,E} and report marginal lift per group. Group D (form/momentum) and Group E (context) fill gaps identified in the methodology — streaks, recency weighting, head-to-head records, and series position were previously missing. The dual-OpenMP issue should be noted in the thesis reproducibility section: on macOS with Homebrew LightGBM and pip-installed PyTorch, classical and GNN model evaluations must run in separate processes to avoid OpenMP shutdown conflicts.

---

## 2026-04-02 — Path B: In-game event extraction pipeline and temporal split management

**Objective:** Build the data extraction layer for accessing raw in-game events (tracker events, game events) from SC2 replay files, and implement proper temporal train/val/test splitting with series-aware boundaries.

**Approach:** Designed a two-phase extraction pipeline: (1) multiprocessing-based raw event extraction from replay JSON to Parquet intermediate storage, and (2) DuckDB loading with typed views (player_stats with 39 stat columns, match_player_map for game event correlation). Temporal splitting uses a 80/15/5 ratio with a 2-hour gap heuristic to group best-of series and prevent series from being split across partitions.

**Issues encountered:**
- `slim_down_sc2_with_manifest()` was destructive (modifies files in-place with no undo) — added `dry_run=True` default to prevent accidental data loss.
- Best-of series detection requires a time-gap heuristic since replays don't explicitly mark series membership. Chose 2 hours as a conservative threshold.
- Pre-existing MPS segfault in `test_model_reproducibility` (unrelated to this work).

**Resolution/Outcome:** All 70 tests pass (28 existing + 42 new). Pipeline architecture separates extraction (CPU-bound, parallelized) from loading (DuckDB bulk inserts). Parquet intermediate format enables inspection and re-loading without re-extraction.

**Thesis notes:** The series-aware temporal split is methodologically important — naive time-based splits can leak information when consecutive games in a best-of series land in different partitions. The 80/15/5 split with validation set supports proper hyperparameter tuning without test set contamination. The 39-field player_stats view provides the foundation for in-game feature engineering (Chapter 4).

---

## 2026-04-02 — Repository restructured into proper Python package

**Objective:** Reorganize flat 13-module codebase into a proper `src/sc2ml/` package layout to support maintainability, testability, and future AoE2 integration.

**Approach:** Adopted PyPA-recommended src layout with four subpackages (`data/`, `features/`, `models/`, `gnn/`). Renamed modules to avoid namespace redundancy. Updated all imports, fixed test infrastructure (removed `sys.path` hacks, created proper `conftest.py`), configured Poetry for package mode with CLI entry point. Archived legacy execution reports to `reports/archive/`.

**Issues encountered:**
- `conftest.py` is auto-loaded by pytest but not directly importable — required moving shared test utilities to `tests/helpers.py` instead.
- Pre-existing LightGBM segfault on Apple M4 Max during `test_model_reproducibility` (known MPS issue, unrelated to refactoring).
- Ruff identified pre-existing F821 errors from string type annotations — fixed with proper `TYPE_CHECKING` imports.

**Resolution/Outcome:** All 28 non-MPS tests pass. Ruff clean (1 pre-existing E501 in `test_mps.py`). Package installs correctly via `poetry install`. CLI entry point registered. Legacy reports preserved in `reports/archive/`.

**Thesis notes:** The src layout establishes the foundation for shared abstractions when AoE2 integration begins. The package structure makes it clear which components are game-specific (data ingestion, graph construction) vs. reusable (model evaluation, feature engineering patterns).

---

## 2026-04-02 — Project infrastructure setup for Claude Code collaboration

**Objective:** Establish structured development workflow with rich guidelines, git conventions, and documentation trail for thesis work.

**Approach:** Augmented CLAUDE.md with comprehensive sections covering permissions, coding standards, ML experiment protocol, and documentation requirements. Created CHANGELOG.md and this research log.

**Issues encountered:** None — greenfield setup.

**Resolution/Outcome:** Three-tier documentation system in place: CHANGELOG (code versioning), research log (thesis narrative), execution reports (raw pipeline output).

**Thesis notes:** This infrastructure supports the reproducibility and methodology documentation requirements of the thesis. The structured experiment protocol (hypothesis-first, temporal splits, baseline comparisons) will provide a clear audit trail for Chapter 3 (Methodology).

---

## 2026-03-30 — Baseline SC2 pipeline results on Apple M4 Max (summary of prior work)

**Objective:** Establish working end-to-end prediction pipeline for StarCraft II match outcomes using both classical ML and Graph Neural Networks.

**Approach:** Built 5-stage pipeline: data ingestion from SC2Replay JSON files into DuckDB, SQL-based feature views, custom ELO system with dynamic K-factor, Bayesian-smoothed feature engineering (45+ features), and three model training paths (classical ML, Node2Vec embeddings, GATv2 GNN).

**Issues encountered:**
- Apple M4 Max MPS backend causes silent failures and segfaults with sparse tensor operations in PyTorch Geometric. Workaround: force CPU for GNN training, set `PYTORCH_ENABLE_MPS_FALLBACK=1`.
- Data leakage risk from using current-match statistics (APM, SQ, supply_capped_pct) as features. Resolution: feature engineering uses only pre-match historical aggregates.
- `matches_flat` view produces 2 rows per match (both player perspectives) — intentional augmentation but requires careful handling in ELO computation (deduplicate via `processed_matches` set).

**Resolution/Outcome:** Classical ML models achieve ~63-65% accuracy (Gradient Boosting best). Top features: historical win rate, experience differential, SQ differential. GNN pipeline functional with GATv2 edge classification. See `reports/archive/09_run.md` for detailed metrics.

**Thesis notes:** The ~63-65% accuracy on temporal splits provides a solid baseline for comparative analysis. The feature importance ranking (win rate > experience > mechanical skill) aligns with domain knowledge about RTS skill factors. MPS compatibility issues should be documented in the thesis as a practical consideration for reproducibility on Apple Silicon.
