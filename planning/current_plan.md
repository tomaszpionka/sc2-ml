---
category: A
branch: phase01/sc2egset-tracker-events-semantic-validation
date: 2026-05-04
planner_model: claude-opus-4-7
dataset: sc2egset
phase: "01"
pipeline_section: "01_03 -- Systematic Data Profiling"
invariants_touched: [I3, I6, I7, I9, I10]
source_artifacts:
  - docs/TAXONOMY.md
  - docs/PHASES.md
  - .claude/scientific-invariants.md
  - .claude/ml-protocol.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/tracker_events_raw.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replay_players_raw.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replays_meta_raw.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_03_table_utility.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_04_event_profiling.md
  - thesis/pass2_evidence/phase02_readiness_hardening.md
  - thesis/pass2_evidence/methodology_risk_register.md
  - reports/specs/02_00_feature_input_contract.md
  - reports/specs/02_01_leakage_audit_protocol.md
critique_required: true
research_log_ref: src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md#2026-05-04-phase01-step-01_03_05-tracker-events-semantic-validation
---

# Plan: Phase 01 closure of GATE-14A6 — SC2EGSet `tracker_events_raw` semantic validation (Step 01_03_05)

## Scope

This plan creates and executes a single Phase 01 step (Step 01_03_05, NEW) that semantically validates the `tracker_events_raw` table of the SC2EGSet dataset. The work closes — or explicitly narrows — GATE-14A6, which currently blocks SC2 in-game telemetry features in the thesis (per `thesis/pass2_evidence/phase02_readiness_hardening.md` §14A.6 and RISK-21). The plan covers ROADMAP creation, notebook authoring, eight validation modules (V1–V8), artifact generation, lineage closure, and conditional updates to the Phase 02 readiness evidence file. It does NOT generate Phase 02 features, train models, edit thesis chapters, or touch AoE2 datasets.

## Problem Statement

The just-merged PR #207 (`thesis/audit-methodology-lineage-cleanup`) closed all in-text BLOCKERs but left **GATE-14A6** open as the deepest non-cosmetic risk surfaced by the external scientific audit. GATE-14A6 says: thesis methodology MUST NOT claim that SC2 `tracker_events`-derived in-game features have been semantically validated until Step 01_03_05 executes end-to-end and produces accepted `.md` + `.json` artifacts. Chapter 4 §4.3.2 currently carries a visible-prose hedge so an examiner sees the deferral. Without Step 01_03_05, Phase 02 cannot draft SC2 in-game features without parser-assumption risk, and one of the thesis's two primary RQ2 contributions (in-game-vs-pre-game ablation) cannot be defended.

This plan is the bounded closure of that gate. It does not over-promise: the gate may be **closed** (all planned tracker-derived feature families safe or caveated with no critical unknowns), **narrowed** (some safe family + enumerated blocked families), or **unable_to_decide** (which halts the PR to the user) — but every outcome is grounded in artifact evidence rather than parser assumptions.

## Assumptions & unknowns

- **Assumption:** The 10 tracker event types catalogued in 01_03_04 (UnitBorn 36.08%, UnitDied 25.89%, UnitTypeChange 17.74%, PlayerStats 7.35%, UnitInit, UnitDone, UnitPositions, Upgrade, UnitOwnerChange, PlayerSetup) are the complete authoritative list for sc2egset.
- **Assumption:** `details.gameSpeed` cardinality = 1 (`Faster`) per existing `INVARIANTS.md` §1; loop-to-seconds factor 22.4 lps. **Re-confirmed empirically in V1, never inherited.**
- **Assumption:** The repo-local `s2protocol` decoder definitions (or the public Blizzard/s2protocol GitHub source) is the authoritative reference for per-event-field semantics. The SC2EGSet datasheet PDF is **NOT** text-extractable in this environment (no `pdftotext` / `pdfminer.six` / `pypdf` in the active `.venv`); per Q1 decision below, **no new dependency will be added** in this PR. Any field that cannot be verified without datasheet PDF text is downgraded to `eligible_with_caveat` or `blocked_until_additional_validation`, never `eligible_for_phase02_now`.
- **Assumption:** sc2egset's anchor column is VARCHAR `details_timeUTC` (not TIMESTAMPTZ), so CROSS-02-00 §3.3 UTC discipline (`SET TimeZone = 'UTC'`) is **not strictly required** for the comparisons in this notebook, but is executed defensively per spec.
- **Unknown:** Whether `n_inverted` (impossible UnitBorn → UnitDied lifecycle ordering) is strictly 0 across the 22,390 sc2egset replays — resolved empirically in V5.
- **Unknown:** Whether coordinate fields (V6) are encoded in cell units, sub-cell units (×16 fixed-point), or some other convention — resolved by s2protocol cross-reference + descriptive empirical reporting; no "parser bug" claim without source support.
- **Unknown:** Per-event-type schema stability across `gameVersion` cohorts (V4) — resolved empirically with stratified sampling so rare event families are not declared absent solely due to under-sampling.

## Literature context

The relevant external references are the s2protocol decoder source (Blizzard, https://github.com/Blizzard/s2protocol) and the SC2EGSet datasheet [Bialecki2023, *Scientific Data* 10:600, DOI 10.1038/s41597-023-02510-7]. The Liquipedia community-grey reference for `22.4 loops/sec` already cited in Chapter 2 §2.2.4 is **secondary/contextual only** for this validation — V1 establishes the factor by s2protocol authority + empirical confirmation. No new bibliographic entries are added by this PR.

[OPINION] In the absence of a peer-reviewed citation for per-event-field cumulative-vs-instantaneous semantics for `PlayerStats.stats.*Current` keys, the s2protocol decoder source is the most authoritative reference available. If even s2protocol does not unambiguously establish cumulative semantics for a given field, that field is classified as `eligible_with_caveat` or `blocked_until_additional_validation` — never `eligible_for_phase02_now`.

## Execution Steps

### T01 — ROADMAP-first: add Step 01_03_05 stub

**Objective:** Per G2 generated-artifact discipline, the ROADMAP entry must exist before the notebook is created. Add a single YAML block describing Step 01_03_05 with a `gate.continue_predicate` that matches the GATE-14A6 closure criterion below.

**Instructions:**
1. Read the existing 01_03_04 YAML block (lines 658–727) to confirm the schema used by the 01_03 family.
2. Append a new Step 01_03_05 block after line 727 with: `step_number: "01_03_05"`; `name: "Tracker Events Semantic Validation"`; `phase: "01 -- Data Exploration"`; `pipeline_section: "01_03 -- Systematic Data Profiling"`; `dataset: "sc2egset"`; `predecessors: ["01_03_04"]`; `notebook_path: "sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.py"`; `inputs.duckdb_tables: [tracker_events_raw, replay_players_raw, replays_meta_raw]`; `outputs.report: "artifacts/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.md"`; `outputs.data_artifacts: [01_03_05_tracker_events_semantic_validation.json, tracker_events_feature_eligibility.csv]`; `scientific_invariants_applied: [I3, I6, I7, I9, I10]`; `thesis_mapping: ["Chapter 4 -- Data and Methodology > 4.3.2 SC2 in-game telemetry feature eligibility", "Phase 02 (Feature Engineering) — decides which tracker-derived feature families enter scope"]`.
3. The Step `question` field MUST be framed as semantic validation, NOT feature generation: *"For each tracker_events_raw event family, are the event-data field semantics, player-id mapping, cadence, coordinate units, and lifecycle semantics sufficiently understood to derive Phase 02 in-game-history features without parser-assumption risk? Which feature families are eligible_for_phase02_now, eligible_with_caveat, blocked_until_additional_validation, or not_applicable_to_pre_game?"*
4. The `gate.continue_predicate` MUST text-match the closure rule in §Gate Condition below. The `gate.halt_predicate` MUST cover: V1 fails to confirm a single canonical loop-to-seconds factor; V2 finds an event type whose semantically-player-attributed records cannot be mapped at all; V8 cannot produce verdicts due to evidence insufficiency.
5. Do NOT invent fields beyond the 01_03_04 schema. If 01_03_04 lacks a field needed here (e.g., `external_references`), include it only if `step_template.yaml` allows it.

**Verification:**
- `grep -n '01_03_05' src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` returns the new heading and YAML block.
- `python -c "import yaml,sys; yaml.safe_load(open('src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md').read().split('---')[-1])"` does NOT raise (or equivalent YAML lint over the appended block).
- No other ROADMAP lines change (`git diff --stat` shows only ROADMAP.md additions, zero deletions).

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`

**Read scope:**
- `docs/templates/step_template.yaml`
- `thesis/pass2_evidence/phase02_readiness_hardening.md` (§14A.6 verbatim text)

---

### T02 — Parser / s2protocol evidence assembly (read-only, no dependency add)

**Objective:** Establish what is and is not retrievable from authoritative sources before the validation notebook makes any semantic claim. Per **Q1 decision (path b)** and **Amendment 7**, this PR adds NO new Python dependency and does NOT modify `pyproject.toml` or `poetry.lock`. The output is a structured `EVIDENCE` dict that T03 transcribes into the notebook intro cell.

**Instructions:**
1. **No PDF text extraction.** Do not run `poetry add`. Do not edit `pyproject.toml` or `poetry.lock`. The SC2EGSet datasheet is recorded as a citation by section number only, never by extracted text.
2. **s2protocol cross-reference (read-only WebFetch).** For each of the 10 tracker event types (UnitBorn, UnitDied, UnitTypeChange, PlayerStats, UnitInit, UnitDone, UnitPositions, Upgrade, UnitOwnerChange, PlayerSetup), retrieve the relevant section from `https://github.com/Blizzard/s2protocol` (try `decoders.py` and the protocol-version files matching `replays_meta_raw.metadata.gameVersion` cardinality — the most recent protocols within the 2016–2024 corpus span are the relevant authority). Record per event type: which fields are documented; which field names match the JSON keys observed in 01_03_04 (`controlPlayerId`, `upkeepPlayerId`, `playerId`, `killerPlayerId`, etc.); whether `PlayerStats.stats.*Current` keys are documented as instantaneous or cumulative.
3. **Per validation module, declare evidence stance.** Build a Python dict (transcribed into T03 notebook):
   ```python
   EVIDENCE = {
       "V1_loops_per_second": {
           "primary_source": "<s2protocol path or 'datasheet §X (text not extracted)'>",
           "secondary_source": "Liquipedia (community-grey, contextual only)",
           "verdict_method": "empirical (cardinality of details.gameSpeed) + cited 22.4 lps from s2protocol",
           "datasheet_extractable": False,
       },
       # ... one entry per V1..V8
   }
   ```
4. **Auto-downgrade rule.** Per Q1: any module whose `primary_source` is the datasheet AND `datasheet_extractable: False` AND s2protocol does not cover the field unambiguously gets its candidate verdict downgraded automatically to `eligible_with_caveat` or `blocked_until_additional_validation` in T10. Document this rule in `EVIDENCE["_meta"]["auto_downgrade_rule"]`.

**Verification:**
- `EVIDENCE` is an 8-key dict (V1..V8) plus `_meta`; transcribed into T03's notebook intro cell.
- `pyproject.toml` and `poetry.lock` are not in `git diff`.
- WebFetch results for each event type recorded as a comment block in the notebook.

**File scope:**
- (none — T02 produces no on-disk file; output flows into T03)

**Read scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/tracker_events_raw.yaml`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_04_event_profiling.md`
- `thesis/pass2_evidence/phase02_readiness_hardening.md` §14A.6

---

### T03 — Notebook scaffold + V1 (game-loop / time semantics)

**Objective:** Build the jupytext-paired notebook (.py + .ipynb), insert intro cell with `EVIDENCE` from T02, and execute V1: empirically establish loops-per-second per `gameSpeed` value with **s2protocol as primary citation authority** (Q2 decision); Liquipedia retained as secondary/contextual only.

**Instructions:**
1. Create paired notebook under `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.{py,ipynb}` per `sandbox/jupytext.toml` (memory: lives at `sandbox/jupytext.toml`, not repo root). Cell cap 50 lines per `sandbox/notebook_config.toml`.
2. **Intro cells:** imports (`from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir`; `import duckdb, json, pathlib, csv, yaml`); UTC discipline (`con.execute("SET TimeZone = 'UTC'")` per CROSS-02-00 §3.3 — defensive); constants (`DATASET = "sc2egset"`, `ARTIFACTS_DIR = get_reports_dir("sc2", DATASET) / "artifacts" / "01_exploration" / "03_profiling"`); `EVIDENCE` dict from T02; `sql_queries = {}`; helper `def run_q(name, sql): sql_queries[name] = sql; return con.execute(sql).fetch_df()`.
3. **Hypothesis (V1) — printed at top of V1 section:** `details.gameSpeed` cardinality is 1 (`Faster`) across all 22,390 sc2egset replays AND there is exactly one canonical loop-to-seconds factor (22.4) for that gameSpeed. **Falsifier:** any second `gameSpeed` value, OR a per-replay deviation between `max(loop) / 22.4` and any external duration field by more than 10% on more than 0.1% of replays.
4. **V1.1 gameSpeed cardinality:** `SELECT details.gameSpeed AS game_speed, COUNT(*) AS n_replays FROM replays_meta_raw GROUP BY game_speed ORDER BY n_replays DESC;` Assert single row, `game_speed='Faster'`, `n_replays=22390`. Halt if not.
5. **V1.2 lps source:** Record `verdicts["V1"]["lps_source"]` = the s2protocol path or commit/version anchor. **Liquipedia is NOT the primary citation** (Q2). If s2protocol does not explicitly state 22.4 lps for "Faster", record `lps_source` as "empirical (replay max-loop / external duration field) corroborated by s2protocol gameSpeed enum"; do not silently fall back to Liquipedia.
6. **V1.3 empirical sanity check:** `WITH per_replay AS (SELECT m.filename, m.header.elapsedGameLoops AS final_loop, (SELECT MAX(t.loop) FROM tracker_events_raw t WHERE t.filename = m.filename) AS max_tracker_loop FROM replays_meta_raw m) SELECT COUNT(*) AS n_replays, COUNT(*) FILTER (WHERE max_tracker_loop > final_loop) AS tracker_after_end, COUNT(*) FILTER (WHERE max_tracker_loop < final_loop * 0.5) AS tracker_well_before_end, AVG(max_tracker_loop / NULLIF(final_loop, 0)) AS mean_tracker_to_end_ratio, AVG(final_loop / 22.4) AS mean_duration_seconds FROM per_replay;` If `tracker_after_end > 0` flag for V7 leakage discussion. If `mean_tracker_to_end_ratio < 0.95` on more than negligible fraction, downgrade V1 verdict.
7. **V1 verdict block:** `verdicts["V1"] = {"hypothesis": ..., "falsifier": ..., "result": "PASS"|"PASS_WITH_CAVEAT"|"FAIL", "lps_source": ..., "loop_to_seconds_table": [{"game_speed": "Faster", "lps": 22.4}], "evidence": {...numbers...}}`.

**Verification:**
- Notebook executes cleanly via `nbconvert --execute --inplace` within the 600s budget.
- `verdicts["V1"]["result"]` is non-null.
- `verdicts["V1"]["lps_source"]` does NOT name Liquipedia as primary.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.py`
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.ipynb`

**Read scope:**
- T02 EVIDENCE dict (in-memory, transcribed into the notebook)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md` (existing 22.4 lps reference)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_04_event_profiling.md`

---

### T04 — V2 (player-id mapping by event type)

**Objective:** Per each of the 10 event types, identify which JSON key inside `event_data` maps the event to one of the two analytical players in `replay_players_raw`. **Per Amendment 3:** the ≥99.5% mapping threshold applies ONLY to semantically player-attributed records. Neutral / global / playerless records (e.g., `playerId=16` neutral, `playerId=0` observer/world) are classified separately and NOT counted as mapping failures.

**Instructions:**
1. **Hypothesis:** PlayerStats uses `playerId`; UnitBorn / UnitInit / UnitDone use `controlPlayerId` (true owner) AND `upkeepPlayerId`; UnitDied uses `killerPlayerId` for attribution and `(unitTagIndex, unitTagRecycle)` join back through UnitBorn lineage for victim attribution; PlayerSetup defines slot identity. UnitOwnerChange / UnitTypeChange / UnitPositions / Upgrade — TBD empirically.
2. **Falsifier (per Amendment 3):** any event type whose declared player-attributed records have id-field values outside `{0, 1, 2, …, 16}` OR fail to join back to `replay_players_raw.playerID` with > 99.5% match rate **on the player-attributed slice** (rows where the id field is not in the documented neutral/global/playerless set).
3. **V2.1 enumerate id-bearing keys per event type** (5 not yet enumerated by 01_03_04: UnitDone, UnitTypeChange, UnitPositions, UnitOwnerChange, PlayerSetup, Upgrade): `WITH samples AS (SELECT evtTypeName, event_data, ROW_NUMBER() OVER (PARTITION BY evtTypeName ORDER BY loop) AS rn FROM tracker_events_raw WHERE evtTypeName IN (...)) SELECT evtTypeName, event_data FROM samples WHERE rn <= 3 ORDER BY evtTypeName, rn;` Record union of JSON keys per type.
4. **V2.2 distinct id-field-value histogram per event type:** see planner SQL; cap with `LIMIT 200` per type if necessary; record histograms.
5. **V2.3 join-back verification with neutral/global slicing.** For each candidate id field, partition rows into `player_attributed` vs `neutral_or_global` by value. Compute match rate ONLY on `player_attributed` slice:
   ```sql
   WITH ev AS (
     SELECT filename,
            json_extract_string(event_data, '$.controlPlayerId')::INT AS pid
     FROM tracker_events_raw WHERE evtTypeName = 'UnitBorn'
   ),
   classified AS (
     SELECT *, CASE WHEN pid IN (16, 0) THEN 'neutral_or_global' ELSE 'player_attributed' END AS slot_class
     FROM ev
   )
   SELECT
     slot_class,
     COUNT(*) AS n_events,
     COUNT(*) FILTER (WHERE rp.toon_id IS NOT NULL) AS n_matched,
     1.0 * COUNT(*) FILTER (WHERE rp.toon_id IS NOT NULL) / COUNT(*) AS match_rate
   FROM classified
   LEFT JOIN replay_players_raw rp ON rp.filename = classified.filename AND rp.playerID = classified.pid
   GROUP BY slot_class;
   ```
   The verdict mapping per event type is the field whose `player_attributed` slice has the highest match rate; ties rejected as ambiguous. The neutral/global slice is recorded separately under `verdicts["V2"]["neutral_handling"][event_type]`.
6. **V2 verdict.** Per-event mapping table inserted into `verdicts["V2"]["mappings"]` — fields: `event_type`, `chosen_id_field`, `match_rate_player_attributed`, `neutral_handling` (e.g., `{"16": "neutral", "0": "observer/global"}`), `confidence` (`high` ≥99.5% on player-attributed slice / `medium` 95–99.5% / `low` <95% or ambiguous).

**Verification:**
- Every event type has either a non-null mapping rule OR a documented `confidence: low` / `ambiguous` verdict that downgrades downstream V8 status.
- `verdicts["V2"]["neutral_handling"]` is a non-empty per-event-type dict where applicable.
- Match rate ≥99.5% threshold is computed on `player_attributed` slice only (Amendment 3).

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.{py,ipynb}` (append cells)

**Read scope:**
- T03 notebook so far
- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replay_players_raw.yaml`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_04_event_profiling.md`

---

### T05 — V3 (PlayerStats field semantics — strict cumulative classification per Q3)

**Objective:** Classify every key inside `PlayerStats.event_data.stats` as one of: `safe_snapshot` (instantaneous; sampleable at a snapshot loop), `safe_delta` (cumulative-by-construction OR derivable as such, monotonic non-decreasing within a replay), `unsafe_or_ambiguous` (cannot be classified without external authority). **Per Q3 decision (strict option a):** if cumulative semantics are not proven by s2protocol AND empirical monotonicity AND the auto-downgrade rule from T02, the corresponding cumulative-economy feature family is `blocked_until_additional_validation`. Snapshot features may still be `eligible_for_phase02_now` provided cadence + completeness + V2 player-mapping verdicts pass.

**Instructions:**
1. **Hypothesis:** `minerals*Current` / `vespene*Current` / `food_used` / `food_made` / `workers_active_count` / `army_count` etc. are instantaneous snapshots. Cumulative-style fields (e.g., `minerals_collection_rate` time-series totals) are NOT cumulative-as-final-tick — they may reset to 0 on game end / disconnect.
2. **Falsifier:** any field whose final-tick value contradicts the per-tick delta sum on more than negligible fraction of replays; OR any field whose s2protocol authority is silent AND whose empirical pattern is neither bounded-oscillation nor monotonic-non-decreasing.
3. **V3.1 enumerate stats keys:** `WITH s AS (SELECT json_extract(event_data, '$.stats') AS stats FROM tracker_events_raw WHERE evtTypeName = 'PlayerStats' LIMIT 1) SELECT json_keys(stats) FROM s;` Record full key list. Cross-reference each key to s2protocol authority captured in T02.
4. **V3.2 cadence audit (partitioned by `(filename, playerId)` to remove the two-players-at-same-loop artifact noted in `research_log.md` lines 992–994):**
   ```sql
   WITH ps AS (
     SELECT filename,
            json_extract_string(event_data, '$.playerId')::INT AS pid,
            loop,
            loop - LAG(loop) OVER (PARTITION BY filename, json_extract_string(event_data, '$.playerId') ORDER BY loop) AS gap
     FROM tracker_events_raw WHERE evtTypeName = 'PlayerStats'
   )
   SELECT gap, COUNT(*) AS n FROM ps WHERE gap IS NOT NULL GROUP BY gap ORDER BY n DESC LIMIT 20;
   ```
   Confirm dominant gap is 160 loops (~7.14s at 22.4 lps). If not, downgrade V3.
5. **V3.3 classify each field.** Per-replay-per-player range vs monotonicity check:
   ```sql
   WITH ps AS (
     SELECT filename, json_extract_string(event_data,'$.playerId')::INT AS pid, loop,
            json_extract_string(event_data,'$.stats.<KEY>')::DOUBLE AS v
     FROM tracker_events_raw WHERE evtTypeName = 'PlayerStats'
   ),
   monotonic_check AS (
     SELECT filename, pid,
            MIN(v) AS minv, MAX(v) AS maxv,
            COUNT(*) FILTER (WHERE v < LAG(v) OVER (PARTITION BY filename, pid ORDER BY loop)) AS n_decreases,
            COUNT(*) AS n_ticks
     FROM ps GROUP BY filename, pid
   )
   SELECT
     COUNT(*) AS n_player_replays,
     AVG(maxv - minv) AS mean_range,
     1.0 * SUM(n_decreases) / NULLIF(SUM(n_ticks), 0) AS frac_decreases
   FROM monotonic_check;
   ```
   Pattern detection: `safe_snapshot` ↔ value oscillates within bounded range AND `frac_decreases > 0`; `safe_delta` ↔ `frac_decreases ≈ 0` AND s2protocol confirms cumulative; `unsafe_or_ambiguous` ↔ neither pattern OR no source authority.
6. **V3 verdict per field:** Inserted into `verdicts["V3"]["field_classification"]` as list of dicts with `key`, `class`, `evidence`, `source`. Per Q3 strict rule: any field with `class: unsafe_or_ambiguous` AND used in a candidate cumulative-economy feature family forces that feature family to `blocked_until_additional_validation` in T10.

**Verification:**
- Every PlayerStats stats key has a classification (one of `safe_snapshot` / `safe_delta` / `unsafe_or_ambiguous`).
- Cadence query confirms a per-(replay, player) dominant gap of 160 loops within tolerance.
- No field is classified `safe_delta` without both empirical monotonicity AND s2protocol confirmation.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.{py,ipynb}` (append cells)

**Read scope:**
- T03/T04 notebook so far
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` (PlayerStats periodicity note, lines ~992–994)

---

### T06 — V4 (event-type coverage and schema stability across years / patches, with rare-family safeguard)

**Objective:** Establish whether each event type's coverage and JSON-key set is stable across the 2016–2024 corpus. Patch-level shifts (`gameVersion` changes) can introduce new fields or rename old ones; an unstable event family is at best `eligible_with_caveat`. **Per Amendment 6:** if 1% Bernoulli sampling is used, rare event families MUST NOT be declared absent/unstable solely because the sample under-represents them. Use per-event-type stratification where practical OR explicitly caveat rare-family verdicts.

**Instructions:**
1. **Hypothesis:** All 10 event types' top-level JSON keys are stable across `gameVersion`. **Falsifier:** any event type whose key-set differs by ≥ 2 keys between two `gameVersion` cohorts representing > 5% of the corpus each.
2. **V4.1 per-year coverage (full-table, NOT sampled):**
   ```sql
   SELECT EXTRACT(YEAR FROM TRY_CAST(rm.details.timeUTC AS TIMESTAMP)) AS year,
          te.evtTypeName,
          COUNT(DISTINCT te.filename) AS n_replays,
          COUNT(*) AS n_events
   FROM tracker_events_raw te JOIN replays_meta_raw rm USING (filename)
   GROUP BY year, te.evtTypeName ORDER BY year, te.evtTypeName;
   ```
3. **V4.2 per-`gameVersion` key-set diff with rare-family safeguard.** Two-pass approach:
   - **Pass A (cheap, 1% Bernoulli):** key-set per (evtTypeName, gameVersion) over `TABLESAMPLE BERNOULLI(1)`.
   - **Pass B (per-event-type stratified, up to 10K rows per (evtTypeName, gameVersion) cell):** for any event family whose Pass A sample has < 1000 events in any non-trivial gameVersion cohort, run a stratified resample using `ROW_NUMBER() OVER (PARTITION BY evtTypeName, gameVersion ORDER BY loop) AS rn` with `WHERE rn <= 10000`, to confirm the key-set diff finding holds at sample size that cannot be dismissed as under-coverage.
   - For event families where neither Pass A nor Pass B has ≥ 1000 events in the corpus (truly rare), record verdict as `coverage_too_sparse_for_stability_decision` rather than declaring instability.
4. **V4 verdict per event type:** `coverage_stable` (`true` / `false` / `too_sparse_to_decide`); `key_set_stable` (`true` / `false` / `too_sparse_to_decide`); `unstable_versions` list (or empty); `sample_strategy` (`pass_a_only` / `pass_b_stratified` / `full_table`).

**Verification:**
- All 10 event types have a coverage + key-set verdict (one of the three values).
- Per-year coverage table is non-empty.
- No event family is declared `unstable` based on a Pass A sample with < 1000 events without a Pass B confirmation.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.{py,ipynb}` (append cells)

**Read scope:**
- T03..T05 notebook so far

---

### T07 — V5 (unit-lifecycle event semantics)

**Objective:** For UnitBorn / UnitInit / UnitDone / UnitDied / UnitTypeChange / UpgradeComplete (where present per schema), determine whether counts-by-cutoff-loop are semantically safe. **Per Amendment 4:** surviving units without UnitDied are NOT failures. `n_inverted` = impossible lifecycle ordering contradictions only (UnitDied earlier than its UnitBorn). UnitBorn / UnitDied count features may be eligible for cutoff-based counts even when full lifecycle closure (every UnitBorn matched to a UnitDied) is incomplete because units can survive past game end.

**Instructions:**
1. **Hypothesis:** Each unit event records a deterministic state transition at its `loop` value AND `event_data` does not encode any future-dependent field.
2. **Falsifier:** any event whose `event_data` value depends on game-end state (e.g., a "final cause of death" requiring post-game resolution); OR `n_inverted > 0` in the lifecycle ordering audit.
3. **V5.1 cross-reference EVIDENCE["V5_*"]** from T02 — if s2protocol confirms each event is locally-deterministic at its loop, mark as `safe_snapshot_count`.
4. **V5.2 lifecycle ordering audit (Amendment 4 — survivors NOT failures):**
   ```sql
   WITH births AS (
     SELECT filename, json_extract_string(event_data,'$.unitTagIndex') AS uti,
            json_extract_string(event_data,'$.unitTagRecycle') AS utr, loop AS born_loop
     FROM tracker_events_raw WHERE evtTypeName = 'UnitBorn'
   ),
   deaths AS (
     SELECT filename, json_extract_string(event_data,'$.unitTagIndex') AS uti,
            json_extract_string(event_data,'$.unitTagRecycle') AS utr, loop AS died_loop
     FROM tracker_events_raw WHERE evtTypeName = 'UnitDied'
   ),
   joined AS (
     SELECT b.filename, b.uti, b.utr, b.born_loop, d.died_loop
     FROM births b LEFT JOIN deaths d
       ON b.filename = d.filename AND b.uti = d.uti AND b.utr = d.utr
   )
   SELECT
     COUNT(*) AS n_births,
     COUNT(*) FILTER (WHERE died_loop IS NOT NULL) AS n_births_with_death,
     COUNT(*) FILTER (WHERE died_loop IS NULL) AS n_survivors,            -- NOT a failure (Amendment 4)
     COUNT(*) FILTER (WHERE died_loop IS NOT NULL AND died_loop < born_loop) AS n_inverted  -- IS a failure
   FROM joined;
   ```
   `n_inverted` MUST be 0; `n_survivors` is reported descriptively.
5. **V5.3 cutoff-count semantic check.** For UnitBorn-by-cutoff and UnitDied-by-cutoff:
   ```sql
   SELECT te.evtTypeName, COUNT(*) FILTER (WHERE te.loop <= 6720) AS count_at_5min  -- 5 min × 60 s × 22.4 lps = 6720
   FROM tracker_events_raw te WHERE evtTypeName IN ('UnitBorn','UnitDied','UnitTypeChange','Upgrade')
   GROUP BY te.evtTypeName;
   ```
   Confirm cutoff-based counts are well-defined regardless of survivor status.
6. **V5 verdict per family:** Insert into `verdicts["V5"]` with `n_survivors_descriptive`, `n_inverted` (must be 0), `cutoff_count_safe` (boolean).

**Verification:**
- All lifecycle-event families have a verdict.
- `n_inverted = 0` for the UnitBorn → UnitDied pair.
- `n_survivors` reported descriptively, NOT classified as a failure.
- Cutoff-count safety verdict is `true` for at least UnitBorn and UnitDied.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.{py,ipynb}` (append cells)

**Read scope:**
- T03..T06 notebook so far

---

### T08 — V6 (coordinate semantics, descriptive only per Q4 + Amendment 5)

**Objective:** Test whether `event_data.x` / `event_data.y` for events that carry coordinates lie within `replays_meta_raw.initData.gameDescription.mapSizeX/mapSizeY` bounds. **Per Q4 (option c) + Amendment 5:** report descriptively only AND if out-of-bounds rate is non-trivial (> 1%), plant a follow-up `[REVIEW: investigate s2protocol coordinate-encoding for SC2 tracker events]` note in the artifact (NOT in chapter prose) for Phase-2 / Pass-2 follow-up. Coordinate validation is descriptive unless coordinate units, origin, AND map bounds are source-confirmed.

**Instructions:**
1. **Hypothesis:** Coordinates are integer cell units within `[0, mapSizeX-1] × [0, mapSizeY-1]`. **Falsifier:** any event family with > 1% out-of-bounds rate.
2. **Reporting style (Hard Constraint 9, restated as Amendment 5):** out-of-bounds rate is reported descriptively; do NOT call this a "parser bug" without source-supported evidence.
3. **V6.1 bounds extraction:** `SELECT filename, initData.gameDescription.mapSizeX AS msx, initData.gameDescription.mapSizeY AS msy FROM replays_meta_raw;`
4. **V6.2 in-bounds rate per coordinate-bearing event type** (UnitBorn, UnitDied, UnitInit, UnitPositions): see planner SQL.
5. **V6.3 source-confirmation check.** Per Amendment 5: if s2protocol does NOT explicitly state coordinate units (cell vs sub-cell vs fixed-point) AND origin (0,0 vs map-center vs other), V6 verdict cannot be `eligible_for_phase02_now` — at best `eligible_with_caveat` with the source-confirmation gap recorded.
6. **V6 verdict:** `in_bounds_rate` per event type (descriptive); `source_confirmed_units` (boolean); `source_confirmed_origin` (boolean); `verdict` per Amendment 5 rule. If `in_bounds_rate < 0.99` for any event family, append a follow-up note string `verdicts["V6"]["followup_note"] = "[REVIEW: investigate s2protocol coordinate-encoding for SC2 tracker events <event_type>; out-of-bounds rate <X>% observed 2026-05-04]"`. Note lives in the artifact only — NOT in `thesis/chapters/REVIEW_QUEUE.md` (per Q5).

**Verification:**
- V6 verdict block exists for every coordinate-bearing event family.
- `in_bounds_rate` reported per event type.
- Where `source_confirmed_units` or `source_confirmed_origin` is `false`, verdict is NOT `eligible_for_phase02_now`.
- Where `in_bounds_rate < 0.99`, a `followup_note` string is recorded in the artifact JSON.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.{py,ipynb}` (append cells)

**Read scope:**
- T03..T07 notebook so far
- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replays_meta_raw.yaml`

---

### T09 — V7 (leakage boundary; tracker_events NEVER pre-game per Amendment 2)

**Objective:** Make explicit that tracker events are NOT pre-game (Invariant I3, restated as Amendment 2) and codify the cutoff rule for in-game snapshots. Per **Amendment 2:** every candidate feature family must classify as one of three settings — `pre_game`, `in_game_snapshot`, `post_game_or_blocked` — and tracker-event-derived families MUST NEVER be classified as `pre_game`.

**Instructions:**
1. **Hypothesis:** All events have `loop ≥ 0`; loop-0 events are game-initialization (PlayerSetup, initial UnitBorn) and remain IN_GAME. The cutoff rule for an in-game-snapshot feature at a chosen cutoff loop `L` is `event.loop ≤ L` AND `event.loop < target_match.start_loop_in_player_history` IF cross-replay (Phase 02 enforces the cross-replay condition; this Step only validates the within-replay rule).
2. **Falsifier:** any tracker event with `loop < 0` OR any event whose loop post-dates the corresponding `header.elapsedGameLoops`.
3. **V7.1 boundary check:** `SELECT COUNT(*) FILTER (WHERE te.loop < 0) AS n_negative, COUNT(*) FILTER (WHERE te.loop > rm.header.elapsedGameLoops) AS n_after_end FROM tracker_events_raw te JOIN replays_meta_raw rm USING (filename);` Both must be 0.
4. **V7.2 per-feature-family eligibility under three prediction settings (Amendment 2).** For each candidate feature family enumerated in T10, record:
   - `pre_game`: ALWAYS `not_applicable_to_pre_game` (tracker events are not available before game start).
   - `in_game_snapshot` at `event.loop ≤ cutoff_loop`: provisional verdict driven by V1..V6 outcomes.
   - `post_game_or_blocked`: feature requires post-game state OR cumulative semantics that V3 could not confirm.
5. **V7 verdict.** Three-status block per family in `verdicts["V7"]["per_family"]`; `verdicts["V7"]["amendment_2_compliance"] = true` iff every tracker-derived family has `pre_game = not_applicable_to_pre_game`.

**Verification:**
- V7 boundary checks both 0.
- Per-family three-status table is non-empty.
- `amendment_2_compliance: true` — every tracker-derived family has `pre_game = not_applicable_to_pre_game`.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.{py,ipynb}` (append cells)

**Read scope:**
- T03..T08 notebook so far

---

### T10 — V8 (final feature eligibility decision; produce CSV with per-prediction-setting columns)

**Objective:** Aggregate V1..V7 into a four-status verdict per `(event_family, candidate_feature_family)` and write the machine-readable CSV. Per **Amendment 2**, the CSV has explicit per-prediction-setting columns. Per **Amendment 1**, the GATE-14A6 decision aggregates across ALL planned-Phase-02 SC2 in-game feature families, not just one PlayerStats snapshot.

**Instructions:**
1. **Decision rule (declared inline in notebook):**
   - `eligible_for_phase02_now` iff: V1 = PASS AND V2 mapping `confidence: high` (on player-attributed slice per Amendment 3) AND relevant V3/V4/V5/V6 verdicts PASS or PASS_WITH_CAVEAT AND V7 setting = `in_game_snapshot` AND auto-downgrade rule from T02 does NOT fire.
   - `eligible_with_caveat` iff: any of {V3, V4, V5, V6} is PASS_WITH_CAVEAT but no FAIL AND V2 mapping is at least `medium` AND V7 setting = `in_game_snapshot`.
   - `blocked_until_additional_validation` iff: any of {V3, V4, V5, V6} is FAIL OR V2 mapping is `low` confidence OR V7 setting requires `post_game_or_blocked` OR cumulative-economy semantics required AND V3 cumulative classification not proven (Q3 strict rule).
   - `not_applicable_to_pre_game` iff: V7 setting = `pre_game` (mechanically: every tracker-derived family carries this status under the `pre_game` column per Amendment 2).
2. **Candidate families to enumerate (non-exhaustive baseline; expand if additional Phase 02 SC2 in-game features are planned):**

   | event_family | candidate_feature_family | planned-for-Phase-02 |
   |---|---|---|
   | PlayerStats | `minerals_collection_rate_history_mean` | yes |
   | PlayerStats | `army_value_at_5min_snapshot` | yes |
   | PlayerStats | `supply_used_at_cutoff_snapshot` | yes |
   | PlayerStats | `food_used_max_history` | yes |
   | UnitBorn | `count_units_built_by_cutoff_loop` | yes |
   | UnitBorn | `time_to_first_expansion_loop` | yes |
   | UnitDied | `count_units_killed_by_cutoff_loop` | yes |
   | UnitDied | `count_units_lost_by_cutoff_loop` | yes |
   | UnitTypeChange | `morph_count_by_cutoff_loop` | yes |
   | Upgrade | `count_upgrades_by_cutoff_loop` | yes |
   | UnitOwnerChange | `mind_control_event_count` | optional |
   | UnitPositions | `army_centroid_at_cutoff_snapshot` | optional |
   | UnitInit/UnitDone | `building_construction_count_by_cutoff_loop` | yes |
   | PlayerSetup | `slot_identity_consistency` | yes |

3. **CSV columns (per Amendment 2):** `event_family, candidate_feature_family, planned_for_phase02, status_pre_game, status_in_game_snapshot, status_post_game_or_blocked, upstream_modules, evidence_source, confidence, blocking_reason_if_blocked`. The CSV is written by the notebook in T11; T10 only computes the verdicts in memory.
4. **GATE-14A6 decision aggregation (per Amendment 1).** After per-family verdicts are computed, set `verdicts["V8"]["gate_14a6_decision"]`:
   - `closed` iff: every row with `planned_for_phase02 = "yes"` has either `status_in_game_snapshot = eligible_for_phase02_now` OR `status_in_game_snapshot = eligible_with_caveat` AND there is no critical unknown (no `evidence_source = "datasheet (text not extracted)"` for any planned family AND no V3 cumulative-economy field unproven in a planned feature family).
   - `narrowed` iff: at least one row with `planned_for_phase02 = "yes"` has `status_in_game_snapshot = eligible_for_phase02_now` OR `eligible_with_caveat`, AND at least one other planned-yes row has `status_in_game_snapshot = blocked_until_additional_validation`, AND every blocked planned-yes row has a non-empty `blocking_reason_if_blocked`.
   - `unable_to_decide` iff: no defensible eligibility verdict can be assigned (e.g., V1 FAIL or V2 cannot map any event type or evidence insufficient across the board).
   - **Single PlayerStats snapshot eligible is NOT enough** to declare `closed` unless every planned-for-Phase-02 family is also eligible/caveated.

**Verification:**
- `verdicts["V8"]["per_family"]` is a list with one entry per row in the candidate table.
- Every tracker-derived row has `status_pre_game = not_applicable_to_pre_game`.
- `gate_14a6_decision` ∈ {`closed`, `narrowed`, `unable_to_decide`}.
- Decision rule applied per Amendment 1 — single eligible PlayerStats snapshot does NOT promote decision to `closed` if other planned families are blocked.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.{py,ipynb}` (append cells)

**Read scope:**
- T03..T09 notebook so far

---

### T11 — Artifact regeneration + research_log + STEP_STATUS / PIPELINE_SECTION_STATUS / PHASE_STATUS closure

**Objective:** Run a final clean regeneration from the synced .py to produce the .md / .json / .csv outputs from a fresh kernel; update `research_log.md`, `STEP_STATUS.yaml`, and (per Q6) `PIPELINE_SECTION_STATUS.yaml` + `PHASE_STATUS.yaml` if their schemas allow.

**Instructions:**
1. **Sync + execute:** `source .venv/bin/activate && poetry run jupytext --sync sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.py && poetry run jupyter nbconvert --to notebook --execute --inplace sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.ipynb --ExecutePreprocessor.timeout=600`
2. **Notebook writes:**
   - `01_03_05_tracker_events_semantic_validation.json` with top-level keys: `step`, `dataset`, `verdicts` (V1..V8), `sql_queries`, `gate_14a6_decision`.
   - `01_03_05_tracker_events_semantic_validation.md` — narrative + per-V section + reproduced SQL.
   - `tracker_events_feature_eligibility.csv` — T10 per-prediction-setting columns.
3. **research_log entry** (per `docs/templates/research_log_entry_template.yaml`): Date `2026-05-04`, Step `01_03_05`, sections What/Why/How/Findings/Decisions taken/Decisions deferred/Thesis mapping/Open questions. Findings: `gate_14a6_decision` value; per-V one-line summary; pointer to CSV.
4. **STEP_STATUS.yaml:** insert
   ```yaml
   "01_03_05":
     name: "Tracker Events Semantic Validation"
     pipeline_section: "01_03"
     status: complete    # iff continue_predicate met
     started_at: "2026-05-04"
     completed_at: "2026-05-04"
     artifact_file: "01_03_05_tracker_events_semantic_validation.py"
   ```
   If `continue_predicate` fires `unable_to_decide`, status = `in_progress` and the PR halts to user.
5. **PIPELINE_SECTION_STATUS.yaml** (Q6): if file exists with matching schema, update only the `01_03` row to reflect Step 01_03_05 status. Do NOT invent new fields.
6. **PHASE_STATUS.yaml** (Q6): if file exists with matching schema, set Phase 01 status to `in_progress` while Step is open, back to `complete` once Step gate passes. Do NOT invent new fields.

**Verification:**
- `git status` shows exactly the manifest files (no others).
- `python -c "import json; json.load(open('src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.json'))"` parses without error.
- CSV has > 0 rows; CSV header includes `status_pre_game`, `status_in_game_snapshot`, `status_post_game_or_blocked` columns (Amendment 2).
- research_log entry validates against the template.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.{py,ipynb}` (regenerate via nbconvert)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.md`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.json`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/tracker_events_feature_eligibility.csv`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/PIPELINE_SECTION_STATUS.yaml` (Q6 — only if file exists with matching schema)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/PHASE_STATUS.yaml` (Q6 — only if file exists with matching schema)

**Read scope:**
- T03..T10 notebook output
- `docs/templates/research_log_entry_template.yaml`
- `docs/templates/step_status_template.yaml`
- `docs/templates/pipeline_section_status_template.yaml`
- `docs/templates/phase_status_template.yaml`

---

### T12 — Manifest + (CONDITIONAL) phase02_readiness_hardening + RISK-21 update

**Objective:** Close the lineage. **Per Q5:** do NOT edit thesis chapters in this PR. The conditional updates ONLY fire if T11 produced an actionable verdict — never silently mark GATE-14A6 closed if validation was wholly partial. REVIEW_QUEUE / Chapter 4 prose updates are out of scope for this PR.

**Instructions:**
1. **`thesis/pass2_evidence/notebook_regeneration_manifest.md`** — append a row under "sc2egset — Phase 01 notebooks":
   - If `gate_14a6_decision = closed`: status `confirmed_intact`, cause "GATE-14A6 closed (Step 01_03_05)".
   - If `gate_14a6_decision = narrowed`: status `confirmed_intact`, cause "GATE-14A6 narrowed per V8 CSV (Step 01_03_05)".
   - If `gate_14a6_decision = unable_to_decide`: status `flagged_stale`, cause "unable_to_decide per V8 (Step 01_03_05)" — and the PR halts to user before completing T13.
2. **(CONDITIONAL) `thesis/pass2_evidence/phase02_readiness_hardening.md` §14A.6** — append a "Post-validation update (2026-05-04)" subsection IFF V8 produced an actionable verdict (`closed` or `narrowed`). The new subsection records: `gate_14a6_decision` value; per-feature-family status table extracted from CSV; updated permitted thesis framing — only narrowed where validation actually delivered a verdict. **Do NOT remove the original §14A.6 text** (historical record). For `narrowed`, the subsection must enumerate which feature families remain blocked.
3. **(CONDITIONAL) `thesis/pass2_evidence/methodology_risk_register.md` RISK-21** — update three cells iff T12 conditional update fires: `Mitigation already applied` ("Step 01_03_05 executed 2026-05-04; per-event-family semantic verdict recorded in `tracker_events_feature_eligibility.csv`"); `Residual uncertainty` (carry forward only `eligible_with_caveat` / `blocked_until_additional_validation` families); `Downstream task responsible` (route to Phase 02 implementers if any family is `eligible_for_phase02_now`). Severity stays `major`; status moves OPEN → CLOSED-WITH-CAVEAT iff at least one planned family is `eligible_for_phase02_now`; otherwise OPEN-NARROWED.
4. **No spec amendment.** CROSS-02-00 v3.0.1 §5.4 already names this gate by reference. No spec bump in scope.
5. **No thesis chapter edits (Q5 + Amendment 8).** `thesis/chapters/**` is OUT OF SCOPE. `thesis/chapters/REVIEW_QUEUE.md` and `thesis/WRITING_STATUS.md` are OUT OF SCOPE for this PR. If V8 = `narrowed`, the §4.3.2 hedge stays as is; the manifest + §14A.6 update + RISK-21 update is the full extent of post-validation propagation in this PR. Any chapter-prose follow-up belongs to a separate Category F thesis-sync task.

**Verification:**
- `git diff` on the three thesis pass2_evidence files matches exactly the conditional rules.
- `git diff thesis/chapters/` is empty.
- `git diff thesis/WRITING_STATUS.md` is empty.

**File scope:**
- `thesis/pass2_evidence/notebook_regeneration_manifest.md`
- `thesis/pass2_evidence/phase02_readiness_hardening.md` (CONDITIONAL — only if V8 actionable)
- `thesis/pass2_evidence/methodology_risk_register.md` (CONDITIONAL — only if V8 actionable)

**Read scope:**
- T11 output JSON + CSV

---

### T13 — PR wrap-up

**Objective:** Commit on the user-named branch, draft PR body, run pre-commit; do not merge.

**Instructions:**
1. **Branch & stage:** branch `phase01/sc2egset-tracker-events-semantic-validation` was created at plan-write time (parent session). Stage only files in the manifest.
2. **Pre-commit:** `git commit` triggers ruff + mypy + jupytext-pair check + status chain consistency. Do not skip with `--no-verify`. Fix any failures and create a NEW commit (never `--amend`).
3. **Commit message:** `feat(sc2egset): close GATE-14A6 — tracker_events semantic validation (Step 01_03_05)`. Body: 1–2 sentences on `gate_14a6_decision` value + co-author tag.
4. **PR body:** write to `.github/tmp/pr.txt` per memory `feedback_pr_body_file.md`; use `gh pr create --base master --head phase01/sc2egset-tracker-events-semantic-validation --body-file .github/tmp/pr.txt`; delete the temp file after PR creation per memory `feedback_pr_body_cleanup.md`.
5. **PR body content:** Summary (1–5 bullets describing what changed and why); Test plan (concrete checkable steps); footer `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
6. **Coverage / type / lint:** already covered by pre-commit; document the run in PR body.
7. **Do not merge.** PR is opened for user review.

**Verification:**
- `gh pr view --json url` returns a valid URL.
- `git status --short` returns no output (working tree clean).
- `.github/tmp/pr.txt` removed after PR creation.
- `pyproject.toml` and `poetry.lock` are not in `git diff master...HEAD` (Amendment 7).
- `thesis/chapters/**` is not in `git diff master...HEAD` (Amendment 8).

**File scope:**
- (no source files; commit + push + PR creation)

**Read scope:**
- All preceding task outputs

---

## File Manifest

Every file ANY executor task is permitted to touch. Files NOT in this list MUST NOT be modified.

| File | Action | Task |
|------|--------|------|
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` | Update — append Step 01_03_05 YAML block after line 727 | T01 |
| `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.py` | Create | T03–T10 |
| `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.ipynb` | Create (jupytext-paired); regenerate via nbconvert in T11 | T03–T11 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.md` | Create (notebook output) | T11 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_05_tracker_events_semantic_validation.json` | Create (notebook output) | T11 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/tracker_events_feature_eligibility.csv` | Create (notebook output, per-prediction-setting columns per Amendment 2) | T11 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` | Update — append 2026-05-04 Step 01_03_05 entry | T11 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` | Update — add `01_03_05` row | T11 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/PIPELINE_SECTION_STATUS.yaml` | Update — `01_03` row only if file exists with matching schema (Q6) | T11 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/PHASE_STATUS.yaml` | Update — Phase 01 status only if file exists with matching schema (Q6) | T11 |
| `thesis/pass2_evidence/notebook_regeneration_manifest.md` | Update — append Step 01_03_05 row | T12 |
| `thesis/pass2_evidence/phase02_readiness_hardening.md` | Update — CONDITIONAL §14A.6 post-validation subsection (only if V8 actionable) | T12 |
| `thesis/pass2_evidence/methodology_risk_register.md` | Update — CONDITIONAL RISK-21 cells (only if V8 actionable) | T12 |
| `planning/current_plan.md` | (this file) — written by parent on plan approval | parent |
| `planning/current_plan.critique.md` | Critique — written by reviewer-deep (per user override) | reviewer |

**INACTIVE / forbidden in this PR (Amendments 7 + 8):**

- `pyproject.toml` — **INACTIVE** per Q1 (path b) + Amendment 7. Do NOT add `pdfminer.six` or any new dependency. Activation requires explicit user override that supersedes Q1.
- `poetry.lock` — **INACTIVE** per Q1 + Amendment 7. Same activation rule as above.
- `thesis/chapters/**` — **FORBIDDEN** per Q5 + Amendment 8. No edits in this PR.
- `thesis/chapters/REVIEW_QUEUE.md` — **FORBIDDEN** per Q5 + Amendment 8. Coordinate-anomaly follow-up note (T08) lives in the artifact JSON only, not REVIEW_QUEUE.
- `thesis/WRITING_STATUS.md` — **FORBIDDEN** per Q5. No edits in this PR.
- `data/raw/**` — deny-listed (repo permissions).
- AoE2 datasets (`src/rts_predict/games/aoe2/**`) — out of scope.
- LOCKED specs (`reports/specs/02_00_*.md`, `reports/specs/02_01_*.md`) — no amendment in this PR.
- `01_03_04_event_profiling.{md,json}` — already `confirmed_intact`; no re-execution.
- `references.bib` — no bibliographic addition in this PR (Q2: s2protocol cited as URL/repo path; Liquipedia retained as secondary).

## Gate Condition

GATE-14A6 closure decision per **Amendment 1**:

- **`closed`** iff: every row in `tracker_events_feature_eligibility.csv` with `planned_for_phase02 = "yes"` has either `status_in_game_snapshot = eligible_for_phase02_now` OR `status_in_game_snapshot = eligible_with_caveat` AND there is no critical unknown (no `evidence_source = "datasheet (text not extracted)"` for any planned family AND no V3 cumulative-economy field unproven in a planned feature family). A single `PlayerStats` snapshot family eligible is NOT enough.
- **`narrowed`** iff: at least one row with `planned_for_phase02 = "yes"` has `status_in_game_snapshot = eligible_for_phase02_now` OR `eligible_with_caveat`, AND at least one other planned-yes row has `status_in_game_snapshot = blocked_until_additional_validation`, AND every blocked planned-yes row has a non-empty `blocking_reason_if_blocked`.
- **`unable_to_decide`** iff: no defensible eligibility verdict can be assigned. PR halts to user before T13 wrap-up.

Mechanical gate criteria (must hold for `closed` OR `narrowed`):

1. `01_03_05_tracker_events_semantic_validation.json` exists, parses, contains all 8 verdict blocks (V1..V8) plus `gate_14a6_decision`.
2. `tracker_events_feature_eligibility.csv` has > 0 rows; header includes `status_pre_game`, `status_in_game_snapshot`, `status_post_game_or_blocked` columns (Amendment 2).
3. Every tracker-derived row has `status_pre_game = not_applicable_to_pre_game` (Amendment 2 compliance).
4. `STEP_STATUS.yaml` `01_03_05` row exists with `status: complete` (or `in_progress` iff `unable_to_decide`).
5. Phase 01 returns to `complete` in `PHASE_STATUS.yaml` iff Step 01_03_05 status is `complete`.
6. `notebook_regeneration_manifest.md` has the new Step 01_03_05 row.
7. If gate is `closed` or `narrowed` → `phase02_readiness_hardening.md` §14A.6 has the post-validation subsection AND RISK-21 cells updated.
8. `git diff thesis/chapters/` is empty (Amendment 8).
9. `git diff pyproject.toml poetry.lock` is empty (Amendment 7).

## Out of scope

- Phase 02 feature generation (this PR is validation only).
- Model training, splitting, evaluation.
- Thesis chapter prose edits (`thesis/chapters/**`).
- `thesis/chapters/REVIEW_QUEUE.md` and `thesis/WRITING_STATUS.md` updates (Q5).
- AoE2 datasets (aoestats, aoe2companion).
- Spec amendments (CROSS-02-00 v3.0.1 and CROSS-02-01 v1.0.1 stay LOCKED).
- Raw-data mutation (`data/raw/**`).
- Re-execution of 01_03_04 (already `confirmed_intact`).
- New Python dependency addition (`pdfminer.six`, `pypdf`, etc.) — Q1 + Amendment 7 forbid edits to `pyproject.toml` / `poetry.lock`.
- Bibliographic addition to `references.bib` (s2protocol cited as URL/repo path; Liquipedia stays secondary).
- Chapter 4 §4.3.2 prose hedge update for `narrowed` outcome — deferred to a separate Category F thesis-sync task per Q5.

## Open questions

All six pre-execution open questions raised by the planner have been resolved by user decision and are recorded inline:

- **Q1 (datasheet text extraction)** — RESOLVED in `## Assumptions & unknowns`, T02 instructions, File Manifest INACTIVE list, and §Out of scope. Path (b): no PDF tooling, no dependency add, downgrade datasheet-only fields to `eligible_with_caveat` / `blocked_until_additional_validation`.
- **Q2 (loops-per-second citation authority)** — RESOLVED in `## Literature context` and T03 instructions. s2protocol is primary; Liquipedia is secondary/contextual only; no separate prose task.
- **Q3 (PlayerStats cumulative-classification severity)** — RESOLVED in T05 instructions and T10 decision rule. Strict (a): cumulative-economy features are `blocked_until_additional_validation` if cumulative semantics not proven; snapshot features may still be eligible if cadence + completeness + V2 mapping pass.
- **Q4 (coordinate parser-bug framing)** — RESOLVED in T08 instructions. Option (c): descriptive AND `[REVIEW]` follow-up note in the artifact JSON if out-of-bounds rate is non-trivial; no parser-bug claims without source support.
- **Q5 (`narrowed` vs `closed` thesis prose impact)** — RESOLVED in T12 instructions and File Manifest. Option (a): no thesis chapter edits in this PR; only Phase 02 readiness / manifest / risk evidence files in scope.
- **Q6 (`PIPELINE_SECTION_STATUS.yaml`)** — RESOLVED in T11 instructions and File Manifest. Yes — update alongside `STEP_STATUS.yaml` and `PHASE_STATUS.yaml` if these files exist with matching schema; do not invent new fields.

Additional execution-time questions (no user decision required pre-execution):

- Whether s2protocol explicitly states 22.4 lps for `gameSpeed='Faster'` — resolves at T02 by WebFetch; if unclear, V1 records `lps_source: "empirical (replay max-loop / external duration field) corroborated by s2protocol gameSpeed enum"`.
- Whether s2protocol decoder source file paths have changed between protocol versions — resolves at T02 by WebFetch and recorded in `EVIDENCE`.
- Whether any rare event family (V4 Pass A < 1000 events) requires Pass B stratification — resolves empirically at T06.

## User amendments to the planner output (recorded for traceability)

The planner's output was approved with 9 user amendments + the 6 Q decisions above. Amendment locations in this plan:

- **Amendment 1 (GATE-14A6 vocabulary)** — recorded in §Gate Condition; T10 decision-rule step 4.
- **Amendment 2 (per-prediction-setting eligibility columns; tracker_events NEVER pre-game)** — recorded in T09 (V7) instructions step 4 and verification; T10 instructions step 1 (`not_applicable_to_pre_game` rule) and step 3 (CSV columns); §Gate Condition mechanical criteria 2 + 3.
- **Amendment 3 (V2 player-mapping threshold scoped to player-attributed slice)** — recorded in T04 (V2) hypothesis, falsifier, and V2.3 query; T10 decision-rule.
- **Amendment 4 (V5 survivors NOT failures; `n_inverted` = ordering contradictions)** — recorded in T07 (V5) objective, V5.2 query, and verification.
- **Amendment 5 (V6 descriptive unless source-confirmed)** — recorded in T08 (V6) objective, V6.3 source-confirmation check, and V6 verdict structure.
- **Amendment 6 (V4 sampling — rare families safeguarded)** — recorded in T06 (V4) objective and V4.2 two-pass approach.
- **Amendment 7 (no `pyproject.toml` / `poetry.lock` edit)** — recorded in T02 instructions, T03 instructions, File Manifest INACTIVE list, §Out of scope, T13 verification, §Gate Condition mechanical criterion 9.
- **Amendment 8 (no thesis chapter edits)** — recorded in T08 (V6 follow-up note in artifact only), T12 instructions step 5, File Manifest INACTIVE list, §Out of scope, T13 verification, §Gate Condition mechanical criterion 8.
- **Amendment 9 (reviewer choreography — reviewer-deep, not reviewer-adversarial)** — recorded in §Reviewer routing — user override below; also in this plan's frontmatter `critique_required: true` is satisfied by reviewer-deep per the user override.

## Reviewer routing — user override

**Critique reviewer = `reviewer-deep`, NOT `reviewer-adversarial`** — explicit user override for this plan. Recorded in this section so the parent session does not auto-route to reviewer-adversarial despite Category A. The reviewer-deep critique is written to `planning/current_plan.critique.md`. Subsequent execution-side review (post-PR) returns to the standard Category A choreography.

T01 execution does NOT begin until reviewer-deep BLOCKERs (if any) are resolved by a follow-up plan revision.

Adversarial cap accounting: this is a fresh PR. Plan-side cap = 0/3 used (reviewer-deep used in lieu of adversarial Round 1 per user override). Execution-side cap = 0/3 used. Symmetric per memory `feedback_adversarial_cap_execution.md`.
