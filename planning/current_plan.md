---
category: A
branch: feat/aoestats-canonical-slot
date: 2026-04-19
planner_model: claude-opus-4-7
dataset: aoestats
phase: "02"
pipeline_section: null            # F1 is a Phase-02-unblocking backfill of a Phase-01 view; it is a dataset-local amendment, not a numbered pipeline section.
invariants_touched: [I3, I5, I7, I9]
source_artifacts:
  - planning/BACKLOG.md                                                                                               # lines 17-46 (F1 entry) + lines 51-58 (F1+W4 coupling)
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_05_i5_diagnosis.json
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_05_i5_diagnosis.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/risk_register_aoestats.csv
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoestats.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_history_minimal.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_1v1_clean.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03_minimal_history_view.json
  - sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_03_minimal_history_view.py
  - reports/specs/01_05_preregistration.md
  - reports/research_log.md
  - thesis/chapters/04_data_and_methodology.md                                                                        # §4.4.6 flag definition
critique_required: true
research_log_ref: src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md#2026-04-19-backlog-f1-canonical-slot
---

## Scope

Add a `canonical_slot VARCHAR` derived column to the aoestats `matches_history_minimal` VIEW (and **only** that VIEW — `matches_1v1_clean` upstream gets a schema-note amendment but **no new column**, because `p0/p1` are already the skill-orthogonal slot identities at 1-row-per-match grain; see Assumption A2). `canonical_slot` neutralises the upstream API ordering artefact (W3 ARTEFACT_EDGE, 01_04_05) so that Phase 02 per-slot feature engineering can proceed without the 52.27% base-rate confound. Bundled with the coupled W4 documentation delta: INVARIANTS.md §5 I5 transitions PARTIAL → HOLDS conditional on the UNION-ALL + `canonical_slot` pair being invariant-verified. Spec §14 amendment v1.0.5 → v1.1.0 registers the schema surface change. Work is Cat A on thesis-critical path (§4.4.6 flag operational closure).

## Problem Statement

**Current state.** aoestats Phase 01 closed READY_CONDITIONAL (2026-04-19, PR #183). The single BLOCKER is AO-R01 `SLOT_ASYMMETRY`: `matches_history_minimal` currently emits 2 player-rows per match via UNION-ALL but carries no column that labels each row with a **skill-orthogonal slot identity**. The upstream `team` field in `matches_1v1_clean` is an API-assigned ordering where `team=1` is the higher-ELO player in 80.3% of matches (mean ELO advantage +11.9 pts; ELO audit in `01_04_05_i5_diagnosis.json:316-323`). Without a canonical slot column, any per-slot feature in Phase 02 (p0_civ × old_rating interactions, per-slot PSI, per-slot faction win rate, etc.) carries the W3 artefact and is thesis-defended as `[PRE-canonical_slot]` only — a methodology convention flagged in §4.4.6 awaiting operational closure.

**Derivation: hash of `match_id`, skill-orthogonal by construction.**
`canonical_slot` is assigned per focal-player row in `matches_history_minimal` via:
```
canonical_slot = CASE WHEN (hash(match_id) + focal_team) % 2 = 0 THEN 'slot_A' ELSE 'slot_B' END
```
The slot label depends **only on `match_id`** (a stable per-match identifier that does NOT encode any player property) and `focal_team` (the pivoting index in the 2-row-per-match UNION-ALL; either 0 or 1). For each match, `hash(match_id) % 2` produces a coin-flip; that coin-flip combined with the focal/opponent pivot distributes slot labels so each match has exactly one `slot_A` row and one `slot_B` row, and across matches the assignment is uniform by construction of the hash function.

**Why this works:** no player attribute (profile_id, old_rating, account age, skill) enters the derivation. The hash is of the MATCH identifier, not of any player-ordering signal. This is the same pattern used by `01_04_05_i5_diagnosis.json:17` which cites `hash(game_id) % 2` as the null-reference random-slot benchmark precisely because it is skill-orthogonal by construction.

**Alternatives rejected pre-user-decision:**
- **`old_rating`-ordered** (skill-ordered) — skill-coupled by construction; does not neutralise the W3 artefact, just makes it explicit. Methodologically sound only if the intent is "slot label = skill signal" (distinct purpose from canonical_slot).
- **`profile_id`-ordered** (lower-ID-first) — 01_04_05 Q4 explicitly rejects: `lower_id_first_win_rate = 0.5066 (+0.66pp)` is a non-trivial skill-correlated edge in what was supposed to be a null-reference control. Account age correlates with skill (early-adopter effect → lower IDs have longer histories + more match experience). Upstream artifact verdict: "Profile_id ordering must NOT be used as a slot-neutralizing technique" (`01_04_05_i5_diagnosis.md:94-98`). The directional point is that profile_id is skill-correlated; magnitude comparison to the team=1 artefact (+2.27pp) is not the load-bearing argument.
- **Hash on sorted `(min, max)` profile_id tuple** — inherits the same skill correlation; the sort is on a player-property magnitude. Not skill-orthogonal.

**Why now.** Phase 02 execution cannot begin in full scope (only GO-NARROW is unblocked) until this column lands. The `[PRE-canonical_slot]` flag is referenced 7+ times across §4.4.6, spec §9/§11, INVARIANTS §5, risk register AO-R01, research_log, and the Phase 06 interface CSV `notes` column. F1 is the single structural PR that discharges all of them.

**Coupling.** Reviewer-adversarial 2026-04-19 surfaced that F1 alone adds the column but leaves INVARIANTS §5 I5 row as PARTIAL with a trailing "W4 schema amendment" caveat. The flip to HOLDS requires the invariant text to be re-written to cite the UNION-ALL + `canonical_slot` pair as the combined I5-compliance mechanism. Spec §14 must register the amendment with a `spec_version` bump. Both edits co-locate cleanly in a single PR.

## Assumptions & unknowns

- **Assumption A1 (derivation — user-selected 2026-04-20).** Use **hash-on-`match_id`** derivation: `canonical_slot = CASE WHEN (hash(match_id) + focal_team) % 2 = 0 THEN 'slot_A' ELSE 'slot_B' END`. Justification follows from the **mathematical structure of the derivation, not from any empirical claim about `match_id`'s content.** Given: (a) `hash(match_id)` depends only on the value `match_id`; (b) both rows of any single match share the same `match_id` value (by the UNION-ALL pivot over a 1-row-per-match clean source); (c) therefore `hash(match_id)` takes an identical value for both rows of a given match. The binary splitter `(hash + focal_team) % 2` with `focal_team ∈ {0, 1}` then distributes the two rows into complementary slot labels (0 and 1 mod 2 differ by 1). The per-match distinct-slot property is **independent of `match_id`'s semantic content**: even if `match_id` encoded player identity, both rows of a match would receive the same hash, and the `focal_team` pivot alone would determine the complementary assignment. Skill-orthogonality across matches follows from the hash function's avalanche property applied to per-match varying inputs — no empirical claim about `match_id`'s origin or monotonicity is required. This is the same reasoning pattern `01_04_05_i5_diagnosis.json:17` uses for its null-reference `hash(game_id) % 2`. Falsifier: the orthogonality argument would fail only if both rows of a single match received *different* `match_id` values — structurally impossible under the current VIEW which JOINs on a single `match_id` per row in `matches_1v1_clean`.
- **Assumption A2 (scope of schema change).** `matches_1v1_clean` upstream does **not** gain a new `canonical_slot` column. Rationale: at 1-row-per-match grain, `p0_profile_id` and `p1_profile_id` already identify the two players orthogonally; `canonical_slot` is only meaningful at 2-row-per-match (focal vs. opponent) grain, which is the `matches_history_minimal` grain. `matches_1v1_clean.yaml` receives a descriptive note amendment in its `invariants` block explaining that the canonical-slot derivation is materialised downstream; no new column.
- **Assumption A3 (VIEW is read-only projection, I9 preserved).** The existing view is created via `CREATE OR REPLACE VIEW matches_history_minimal AS ...` (see `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_03_minimal_history_view.py:146-191`). Adding a deterministic CASE expression computed from the existing p0/p1 halves is a pure projection — no raw mutation, I9 holds.
- **Assumption A4 (row count neutrality).** `matches_history_minimal` remains at 35,629,894 rows (17,814,947 matches × 2). Adding a column changes schema width (9 → 10), not cardinality; we assert row count before and after.
- **Assumption A5 (F1+W4 bundled in one PR).** Propose bundling F1+W4 because (a) the flip-predicate in `modeling_readiness_aoestats.md:20` explicitly couples them, (b) executor is autonomous while user sleeps — a single gate condition minimises review ping-pong, (c) W4's operational content is purely documentation (INVARIANTS.md §5 row + spec §14 + `matches_1v1_clean.yaml` invariants note), so it does not expand code-change surface.
- **U1 (derivation choice) — RESOLVED 2026-04-20.** User selected hash-on-`match_id`. Profile_id-ordered and old_rating-ordered alternatives both rejected (see Problem Statement "Alternatives rejected" block). T01 carries only the hash-based DDL.
- **Unknown U2 (downstream notebook impact).** Whether any existing 01_05 notebook that reads `matches_history_minimal` would be silently affected by the new column. Review in T06 confirms all 01_05 notebooks `SELECT` specific columns (never `SELECT *` that would break); expected blast radius: zero existing notebooks need re-run.
- **Unknown U3 (W4 wording authority).** Whether the new §5 I5 row should say "HOLDS" outright or "HOLDS (subject to UNION-ALL + canonical_slot derivation)". Plan proposes the latter conditional phrasing because it preserves the evidence trail. Reviewer-adversarial may insist on stronger wording.

## Literature context

No new bibkeys required. F1 is a schema-level derived-column addition — it operationalises a methodology convention already defended in §4.4.6, which cites:
- W3 verdict artefact (`01_04_05_i5_diagnosis.json`) — primary evidence.
- I5 scientific invariant (`.claude/scientific-invariants.md` §5, "Symmetric player treatment").
- Spec §11 aoestats patch-anchored reference + W3 binding (`reports/specs/01_05_preregistration.md`).

The hash-on-`match_id` derivation directly adopts the "deterministic random tie-breaking on a match-level identifier" pattern that 01_04_05 itself uses as its null-reference benchmark. `01_04_05_i5_diagnosis.json:17` computes `hash(game_id) % 2` as the ground-truth skill-orthogonal random slot against which the API `team` field is compared and rejected as a W3 artefact. The canonical_slot derivation operationalises the same null-reference pattern as the production slot label for Phase 02 consumption.

## Execution Steps

Tasks are ordered to cleanly separate (a) the code change (notebook + schema YAMLs) from (b) the documentation amendments (INVARIANTS, spec §14, risk register, research_log, BACKLOG). Each task is executor-atomic.

---

### T01 — Author `01_04_03b_canonical_slot_amendment.py` sandbox notebook

**Objective.** Add a `canonical_slot VARCHAR` derived column to the existing `matches_history_minimal` VIEW via `CREATE OR REPLACE VIEW` (DDL re-emission in an amendment notebook). Produce validation artifact JSON. The notebook is the single source-of-truth for the DDL diff; it is paired with the existing `01_04_03_minimal_history_view.py` as a successor amendment (pattern mirrors PR #155's `01_04_02` duration-augmentation addendum style).

**Instructions.**
1. **Pre-validation.** Activate venv; open read-only `get_notebook_db("aoe2", "aoestats")`; `DESCRIBE matches_history_minimal` and assert current 9-column schema matches `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_history_minimal.yaml` (sanity check against schema drift).
2. **Derivation: hash-on-`match_id` (user-selected 2026-04-20, U1 RESOLVED).**
   ```sql
   -- In p0_half (focal_team = 0):
   CASE WHEN (hash(m.match_id) + 0) % 2 = 0 THEN 'slot_A' ELSE 'slot_B' END AS canonical_slot,
   -- In p1_half (focal_team = 1):
   CASE WHEN (hash(m.match_id) + 1) % 2 = 0 THEN 'slot_A' ELSE 'slot_B' END AS canonical_slot,
   ```
   **Hash function.** Use DuckDB's built-in `hash()` function (stable 64-bit hash). Apply to `m.match_id` (VARCHAR) directly; DuckDB handles string hashing natively. Output is a positive 64-bit integer; `% 2` yields 0 or 1.
   **Distinct-slot property.** For any given `match_id`, `hash(match_id)` is fixed. The two rows have `focal_team = 0` and `focal_team = 1` respectively, so `(hash + 0) % 2` and `(hash + 1) % 2` are always different — one is 0 and the other is 1. Hence the two rows always receive distinct slot labels.
   **Orthogonality proof (structural, not empirical).** `hash(match_id)` depends only on the value `match_id`. Both rows of any single match receive the same `match_id` (the VIEW's UNION-ALL pivot rebuilds from a 1-row-per-match source on `matches_1v1_clean.game_id` PK), so both rows receive the same hash. The binary splitter `(hash + focal_team) % 2` with `focal_team ∈ {0, 1}` distributes them into complementary slots: `0 % 2 ≠ 1 % 2` by binary arithmetic. The per-match distinct-slot property is **independent of `match_id`'s content** — even if `match_id` encoded player identity, both rows receive the same value so the `focal_team` pivot alone determines the complementary assignment. Skill-orthogonality across matches follows from the hash function's avalanche property. No empirical claim about `match_id`'s origin (vendor-provided, monotonic, UUID, etc.) is required for this argument.
3. **Pre-amendment baseline re-verification (guards against stale-baseline drift, Pass 2 fix).** BEFORE recreating the VIEW, re-run the existing `01_04_03` validation SQL queries (row_count, distinct_match_ids, symmetry_violations, slot_bias, duration stats — SQL verbatim is cached in `01_04_03_minimal_history_view.json` under `sql_queries`) on the **current live DuckDB state** and compare to the cached JSON values. If any differ: abort with "baseline drift — re-baseline required" and escalate to planner (baseline drift would mean the DB has been re-ingested or re-materialised since 2026-04-18 and the cached BEFORE snapshot is unreliable). If all match: proceed. Document the pre-amendment verification outcome inline in the T01 JSON artifact under `baseline_reverification: {status: 'PASS' | 'DRIFT', 2026-04-18 cached values, 2026-04-20 live values}`.
4. **Emit amended DDL.** Rebuild `CREATE_MATCHES_HISTORY_MINIMAL_SQL` constant with the chosen CASE expression inserted between the `won` column and the `duration_seconds` column in both `p0_half` and `p1_half`. Place `canonical_slot` at column position 7 (after `won`, before `duration_seconds`) to keep the 9-column cross-dataset contract visually anchored and `dataset_tag` last.
5. **Execute DDL.** `con.execute(CREATE_MATCHES_HISTORY_MINIMAL_SQL)`. Verify via `DESCRIBE matches_history_minimal` that column count = 10 and ordering is `[match_id, started_at, player_id, opponent_id, faction, opponent_faction, won, canonical_slot, duration_seconds, dataset_tag]`.
6. **Assertions (I6-compliant, SQL verbatim in JSON artifact).**
   - `row_count_preserved`: `SELECT COUNT(*) FROM matches_history_minimal` returns exactly 35,629,894.
   - `canonical_slot_binary_cardinality`: `SELECT DISTINCT canonical_slot FROM matches_history_minimal ORDER BY 1` returns exactly `['slot_A', 'slot_B']` (two values, no NULL, no empty string).
   - `canonical_slot_symmetry`: for every match_id, the two rows have **distinct** canonical_slot values: `SELECT COUNT(*) FROM (SELECT match_id FROM matches_history_minimal GROUP BY match_id HAVING COUNT(DISTINCT canonical_slot) != 2) v` returns exactly 0. This follows from the distinct-slot property (step 2); assertion is confirmatory, not a magic-number gate.
   - `canonical_slot_balance` (sanity check, not a gate): `SELECT canonical_slot, COUNT(*) FROM matches_history_minimal GROUP BY canonical_slot` returns two rows each with count ≈ 17,814,947 (within ~0.1% of 50/50 by central-limit expectation for 17.8M hash samples). Report values; no threshold assertion — the balance is a property of the hash function, not a claim to defend.
   - `canonical_slot_null_count`: `SELECT COUNT(*) FROM matches_history_minimal WHERE canonical_slot IS NULL` returns 0 (A1). For A2, may be non-zero for tied matches; documented in the JSON.
   - `canonical_slot_win_rate` (report-only, not a gate): `SELECT canonical_slot, AVG(CAST(won AS INT)) AS wr, COUNT(*) AS n FROM matches_history_minimal GROUP BY canonical_slot`. Expected: both rates very close to 0.5 by the orthogonality-by-construction argument — any residual deviation is a property of `match_id` (not of the derivation). Report the values in the JSON artifact as evidence; do NOT gate on a magic-number threshold. Skill-orthogonality of `canonical_slot` is established by the derivation's structure, not by this statistic.
   - `canonical_slot_I9_invariance_check`: existing columns (match_id, started_at, player_id, opponent_id, faction, opponent_faction, won, duration_seconds, dataset_tag) all produce identical counts and AVG/MIN/MAX before vs after the amendment. BEFORE snapshot sourced from the pre-amendment re-verification in step 3 (not from the stale cached `01_04_03_minimal_history_view.json`). This guards against the baseline-drift failure mode flagged by Pass 2 reviewer-adversarial.
7. **Emit JSON artifact** at `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.json` with: `{step: "01_04_03b", dataset: "aoestats", derivation_choice: "hash_on_match_id", hash_function: "duckdb_builtin_hash_64bit", ddl_sql_verbatim: <...>, assertions: {row_count_preserved: true, cardinality_binary: true, per_match_distinct: true, balance_wr: {slot_A: <value>, slot_B: <value>}}, generated_date: "2026-04-20", predecessor_artifact: ".../01_04_03_minimal_history_view.json"}` plus every SQL verbatim with SHA-256 query hashes (mirrors the `01_04_05_i5_diagnosis.json` query_shas pattern).
8. **Emit companion Markdown artifact** at `.../01_04_03b_canonical_slot_amendment.md` with narrative interpretation: (a) derivation choice + rationale (hash-on-match_id; skill-orthogonal by construction; profile_id and old_rating alternatives rejected with 01_04_05 Q4 citation for profile_id rejection), (b) ARTEFACT_EDGE → canonical_slot mapping, (c) downstream Phase 02 usage pattern, (d) cross-link to §4.4.6 flag closure.

**Verification.**
- Notebook runs end-to-end with no exceptions.
- Pre-amendment baseline re-verification (step 3) PASSes.
- All 7 assertions in step 6 pass.
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.json` exists with `assertions.all_passed: true`.
- `DESCRIBE matches_history_minimal` shows 10 columns in declared order.

**File scope (notebook writes).**
- `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.py`
- `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.ipynb`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.json`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.md`

**Read scope.**
- `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_03_minimal_history_view.py` (DDL source pattern)
- `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_history_minimal.yaml` (current 9-col spec)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03_minimal_history_view.json` (BEFORE baseline for I9 check)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_05_i5_diagnosis.json` (Q4 skill-orthogonality evidence)

---

### T02 — Update `matches_history_minimal.yaml` schema YAML (9 → 10 columns)

**Objective.** Synchronise the schema-source-of-truth YAML with the amended view. Insert a `canonical_slot` column entry and bump `schema_version`.

**Instructions.**
1. Set `schema_version: "10-col (AMENDMENT: canonical_slot added 2026-04-19)"`.
2. Update `describe_artifact` to `.../01_04_03b_canonical_slot_amendment.json`.
3. Update `generated_date: '2026-04-19'`.
4. In the `columns` array, insert a new entry **between `won` (index 6) and `duration_seconds` (index 7)**:
   ```yaml
   - name: canonical_slot
     type: VARCHAR
     nullable: false   # hash-on-match_id derivation produces a value for every row
     description: |
       Skill-orthogonal slot identity derived from hash of match_id. Resolves the W3
       ARTEFACT_EDGE upstream API ordering artefact (01_04_05): the team column in
       matches_1v1_clean assigns team=1 to the higher-ELO player in 80.3% of matches
       (mean +11.9 ELO). canonical_slot replaces team as the I5-compliant slot label
       for per-slot feature engineering in Phase 02.
       Derivation: CASE WHEN (hash(match_id) + focal_team) % 2 = 0 THEN 'slot_A'
       ELSE 'slot_B' END. Skill-orthogonal by structural construction: both rows of
       any match receive the same hash(match_id) value (UNION-ALL of a
       1-row-per-match source); the binary splitter (hash + focal_team) % 2 with
       focal_team ∈ {0,1} distributes them into complementary slots. Independent of
       match_id's semantic content — no empirical claim about its origin required.
       See 01_04_03b artifact for DDL + assertions.
     notes: |
       PRE_GAME. Derived slot identity for Phase 02 per-slot features. NOT the
       upstream API team label. Every match has exactly one 'slot_A' row and one
       'slot_B' row. Cardinality: exactly 2 values. NULL count: 0.
   ```
5. In the `invariants` array, update I5 row to cite the canonical_slot-based I5 compliance:
   ```yaml
   - id: I5
     description: |
       Player-row symmetry (I5-analog) + deterministic skill-orthogonal slot labelling.
       Every match_id has exactly 2 rows with distinct canonical_slot values.
       duration_seconds identical in both rows. aoestats-specific SLOT-BIAS gate:
       AVG(won::INT) == 0.5 exactly. canonical_slot skill-orthogonality is established
       by construction (hash depends only on match_id, independent of any player
       property); per-slot win rate balance near 0.5 is reported as confirmatory
       evidence in 01_04_03b, not as a magic-number gate.
   ```

**Verification.**
- YAML parses (`python -c "import yaml; yaml.safe_load(open(...))"`).
- `schema_version` reflects 10-col.
- `canonical_slot` entry exists at index 7.

**File scope.**
- `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_history_minimal.yaml`

**Read scope.**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.json` (T01 output)

---

### T03 — Amend `matches_1v1_clean.yaml` invariants note (no new column)

**Objective.** Discharge the W3 `schema_amendment_required` hook documented at `01_04_05_i5_diagnosis.json:356-358` at the `matches_1v1_clean` level, via a descriptive note in the YAML `invariants` I5 entry. No new column is added (per Assumption A2).

**Instructions.**
1. Update the `invariants[I5]` description in `matches_1v1_clean.yaml` (currently at line 208-211) to append:
   ```
   W3 ARTEFACT_EDGE (01_04_05): `team` column reflects upstream API ordering
   (invite-first / matchmaking-API assignment), NOT game-mechanical slot identity.
   Team=1 has higher ELO in 80.3% of matches. Phase 02 feature engineering MUST NOT
   use `team` as input; the downstream `matches_history_minimal.canonical_slot`
   column (hash-on-match_id; skill-orthogonal by construction) is the
   I5-compliant slot label. See `.../01_04_03b_canonical_slot_amendment.json`
   and INVARIANTS.md §5 I5 row.
   ```
2. Do **not** add a `canonical_slot` column to `matches_1v1_clean.yaml` — the derivation is a 2-row-per-match concept that only makes sense at the `matches_history_minimal` grain.

**Verification.**
- YAML parses.
- `grep canonical_slot matches_1v1_clean.yaml` returns the I5 note reference only (no column entry).

**File scope.**
- `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_1v1_clean.yaml`

**Read scope.**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_05_i5_diagnosis.json` (§phase_02_interface.amendment_description:356-358)

---

### T04 — Flip INVARIANTS.md §5 I5 row PARTIAL → HOLDS (W4 coupling)

**Objective.** Rewrite the aoestats INVARIANTS.md §5 I5 row to reflect that the UNION-ALL + canonical_slot pair fully discharges I5 compliance. This is the W4 operational payload.

**Instructions.**
1. Open `src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md` at line 129 (the current I5 row).
2. Replace the current I5 row (`| I5 | PARTIAL — asymmetry characterised, see §4 finding from 01_04_05 | ... W4 coupling ... |`) with:
   ```
   | I5 | HOLDS (post-2026-04-20 canonical_slot amendment) | Upstream `matches_raw` slot asymmetry `team1_wins ≈ 52.27%` diagnosed as ARTEFACT_EDGE (01_04_05): API assigns team=1 to higher-ELO player in 80.3% of games. UNION-ALL pivot in `matches_history_minimal` produces `won_rate = 0.5` exactly; canonical_slot column (hash-on-match_id, 01_04_03b) provides skill-orthogonal slot labelling by construction — the hash depends only on `match_id` (a stable per-match identifier independent of player properties). `team` field MUST NOT be used as a Phase 02 feature; canonical_slot is the I5-compliant slot label. Spec §14 v1.1.0 registers this amendment. |
   ```
3. In §4 (Per-dataset empirical findings), append a brief addendum to the 01_04_05 finding paragraph (after line 94) noting the 2026-04-20 amendment:
   ```
   **Amendment (2026-04-20 — BACKLOG F1 + W4).** The `canonical_slot VARCHAR`
   column is added to `matches_history_minimal` via hash-on-match_id derivation
   (`CASE WHEN (hash(match_id) + focal_team) % 2 = 0 THEN 'slot_A' ELSE 'slot_B' END`).
   Skill-orthogonal by structural construction: both rows of any match share the
   same match_id (UNION-ALL of a 1-row-per-match source), hence the same
   hash(match_id); the binary splitter with focal_team ∈ {0,1} pivot distributes
   them into complementary slots. The argument is independent of match_id's
   semantic content — no empirical claim about its origin is required.
   Profile_id-ordered and old_rating-ordered alternatives were both explicitly
   rejected (profile_id correlates with account age per Q4 of this same artifact;
   old_rating is skill-coupled by construction). I5 transitions PARTIAL → HOLDS
   in §5. Artifact: `01_04_03b_canonical_slot_amendment.{json,md}`.
   ```

**Verification.**
- `grep "I5" INVARIANTS.md` returns the new HOLDS row; no remaining PARTIAL reference for I5.
- `grep "canonical_slot" INVARIANTS.md` returns the new §4 addendum + §5 row reference.

**File scope.**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md`

**Read scope.**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.json` (T01 output)

---

### T05 — Spec §14 amendment v1.0.5 → v1.1.0

**Objective.** Register the schema surface change in the cross-dataset pre-registration spec's amendment log with a minor version bump.

**Instructions.**
1. In `reports/specs/01_05_preregistration.md` frontmatter, change `spec_version: "1.0.5"` → `spec_version: "1.1.0"`.
2. In §14 Amendment log (line 501+), append a new amendment entry at the end of the code block (before the closing triple-backtick):
   ```
   v1.1.0 — 2026-04-19 — aoestats matches_history_minimal schema surface amendment:
                          +1 column (canonical_slot VARCHAR). Discharges W3 follow-up
                          (spec v1.0.1 §14) and BACKLOG F1 + W4 coupling flagged in
                          01_06 decision gate.

                          Reason: W3 ARTEFACT_EDGE verdict (01_04_05, commit ab23ab1d)
                          established that upstream `team` is an API-ordering artefact,
                          not a game-mechanical slot identity. Until this amendment,
                          aoestats emitted [PRE-canonical_slot] flags on per-slot
                          01_05 outputs and Phase 02 was GO-NARROW (aggregate features
                          only). This amendment adds the canonical slot label needed
                          to expand Phase 02 scope to full (per-slot) features.

                          Derivation (hash-on-match_id; skill-orthogonal by
                          construction):
                            canonical_slot = CASE
                              WHEN (hash(match_id) + focal_team) % 2 = 0
                              THEN 'slot_A' ELSE 'slot_B' END

                          Orthogonality (structural, not empirical): `hash(match_id)`
                          depends only on the value match_id. Both rows of any
                          match share the same match_id (UNION-ALL of a
                          1-row-per-match source), hence the same hash. The binary
                          splitter `(hash + focal_team) % 2` with focal_team ∈ {0,1}
                          distributes them into complementary slots — independently
                          of match_id's semantic content. The argument requires no
                          empirical claim about match_id's origin or structure; even
                          if match_id encoded player identity, within-match
                          distinct slots would still hold by the focal_team pivot
                          alone. Profile_id-ordered and old_rating-ordered
                          alternatives were both explicitly rejected (01_04_05 Q4
                          showed profile_id-ordering IS skill-correlated via
                          account-age proxy; old_rating is skill-coupled by
                          construction).

                          Scope — one schema-level change + three documentation deltas:
                          - src/rts_predict/games/aoe2/datasets/aoestats/data/db/
                            schemas/views/matches_history_minimal.yaml: 9 → 10
                            columns (canonical_slot inserted at position 7).
                          - INVARIANTS.md §5 I5 row: PARTIAL → HOLDS.
                          - matches_1v1_clean.yaml invariants[I5]: W3 note appended
                            (no new column; p0/p1 already-disjoint at 1-row-per-match
                            grain).
                          - Spec §9/§11 [PRE-canonical_slot] flag: remains defined
                            as a historical marker for pre-amendment 01_05 artifacts;
                            post-amendment outputs will no longer need the flag.

                          Spec parameter groups (Q1–Q9) unchanged.

                          Source: BACKLOG F1 plan (planning/current_plan.md
                          2026-04-19), artifact `src/rts_predict/games/aoe2/datasets/
                          aoestats/reports/artifacts/01_exploration/04_cleaning/
                          01_04_03b_canonical_slot_amendment.json`.

                          Note: §9 Query 4 (aoestats-only canonical_slot readiness
                          query) now returns a non-empty result; [PRE-canonical_slot]
                          flag protocol transitions from ACTIVE to HISTORICAL. Any
                          future 01_05 re-run on aoestats data will emit per-slot
                          outputs WITHOUT the flag.
   ```
3. No changes to §1 (9-column contract description) or §§2-13 parameter groups. The 9-column cross-dataset contract in §1 is unchanged for sc2egset and aoe2companion; aoestats is declared to carry an additional local column. Add a sentence to §1 (after the cross-dataset note at line 67-71):
   ```
   Post-v1.1.0 note (aoestats-local): aoestats `matches_history_minimal` extends
   the 9-column contract with a local 10th column `canonical_slot VARCHAR`
   (hash-on-match_id; skill-orthogonal slot label). Sibling datasets (sc2egset,
   aoe2companion) retain the 9-column contract. Cross-dataset UNION ALL must
   project the 9 shared columns only. See §14 v1.1.0.
   ```

**Verification.**
- `grep spec_version reports/specs/01_05_preregistration.md` returns `1.1.0`.
- §14 contains the new v1.1.0 entry.
- §1 contains the aoestats-local extension note.

**File scope.**
- `reports/specs/01_05_preregistration.md`

**Read scope.**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.json` (T01 output)

---

### T06 — Downstream notebook safety audit (no re-runs)

**Objective.** Confirm that adding a column to `matches_history_minimal` does not silently break any existing aoestats 01_05 notebook. This is a read-only audit — no notebook re-run.

**Instructions.**
1. Grep all aoestats notebooks (01_05 + 01_06) for references to `matches_history_minimal`:
   ```
   grep -rn "matches_history_minimal" \
     sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/ \
     sandbox/aoe2/aoestats/01_exploration/06_decision_gates/
   ```
   Expected: every reference uses explicit `SELECT <col1, col2, ...>` / `DESCRIBE` / schema-YAML read — no `SELECT *` that would implicitly pull the new column. The 06_decision_gates scope was added post-Pass-2 review; known safe (schema-YAML reads, not SQL).
2. If any notebook uses `SELECT * FROM matches_history_minimal`, flag in the audit log as a follow-up and escalate to plan revision (add a T06a notebook re-run task). Expected finding: zero `SELECT *` patterns (the project's sandbox rule in `sandbox/README.md` and the explicit per-column SELECT pattern observed in `01_04_03_minimal_history_view.py:158-190` suggest none exist).
3. Similarly grep `src/rts_predict/games/aoe2/datasets/aoestats/` for `matches_history_minimal` references in the production code path; expected zero (Phase 02 has not started).
4. Produce a short audit note appended to the T01 markdown artifact (`01_04_03b_canonical_slot_amendment.md`) with the grep output counts and the zero-impact conclusion.

**Verification.**
- Grep produces expected zero `SELECT *` patterns.
- Audit note appended.

**File scope.**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.md` (append-only update)

**Read scope.**
- `sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/*.py`
- `sandbox/aoe2/aoestats/01_exploration/06_decision_gates/*.py`
- `src/rts_predict/games/aoe2/datasets/aoestats/*.py`

---

### T07 — Risk register + modeling readiness update (AO-R01 flip + verdict upgrade)

**Objective.** Flip AO-R01 from OPEN to RESOLVED in the aoestats risk register, and update `modeling_readiness_aoestats.md` verdict from READY_CONDITIONAL to READY_WITH_DECLARED_RESIDUALS.

**Instructions.**
1. In `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/risk_register_aoestats.csv` at the AO-R01 row (line 2):
   - Change `mitigation_status` from `OPEN (BACKLOG F1)` to `RESOLVED (2026-04-19, BACKLOG F1+W4; see 01_04_03b artifact)`.
   - Change `severity` from `BLOCKER` to `RESOLVED` (per the legend in `risk_register_aoestats.md` — verify the allowed values; if "RESOLVED" is not a severity, use the mitigation_status field only and leave severity as historical BLOCKER with a `RESOLVED` suffix note).
   - Do NOT delete the row — keep it for audit trail.
2. In `modeling_readiness_aoestats.md`:
   - §1 Verdict: `READY_CONDITIONAL` → `READY_WITH_DECLARED_RESIDUALS`.
   - §2 Flip-Predicate: annotate as `SATISFIED (2026-04-19): BACKLOG F1 landed; W4 operational content (INVARIANTS §5 I5 PARTIAL → HOLDS) bundled in same PR.`
   - §3 BLOCKER List: change heading to `**0 BLOCKERS (AO-R01 resolved 2026-04-19)**`; keep AO-R01 entry as a historical record with RESOLVED note.
   - §5 Phase 02 Go/No-Go: `GO-NARROW` → `GO-FULL (per-slot features permitted via canonical_slot; see matches_history_minimal.yaml 10-col schema)`.
3. In the corresponding markdown risk register (`risk_register_aoestats.md`), mirror the AO-R01 status update.

**Verification.**
- `grep RESOLVED risk_register_aoestats.csv` shows AO-R01 resolved.
- `grep READY modeling_readiness_aoestats.md` shows READY_WITH_DECLARED_RESIDUALS.

**File scope.**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/risk_register_aoestats.csv`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/risk_register_aoestats.md`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoestats.md`

**Read scope.**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.json` (T01 output)

---

### T08 — Update aoestats research_log.md + CROSS research_log.md

**Objective.** Write the canonical research_log entry for the F1+W4 amendment in the dataset-local log, and a CROSS entry linking to it.

**Instructions.**
1. Prepend to `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md` (reverse-chronological order; new entry goes above the 2026-04-19 01_06 entry at line 11):
   ```markdown
   ## 2026-04-20 — [BACKLOG F1 + W4 / Phase 02 unblocker] canonical_slot column amendment

   **Branch:** `feat/aoestats-canonical-slot`
   **Category:** A (Phase work, aoestats)
   **Scope:** Add `canonical_slot VARCHAR` to `matches_history_minimal` (hash-on-match_id; skill-orthogonal by construction); flip INVARIANTS.md §5 I5 PARTIAL → HOLDS; bump spec v1.0.5 → v1.1.0; resolve AO-R01 BLOCKER.

   ### Key findings
   - Derivation: hash-on-match_id `CASE WHEN (hash(match_id) + focal_team) % 2 = 0 THEN 'slot_A' ELSE 'slot_B' END`.
   - Skill-orthogonal by construction: the hash depends only on `match_id`, a stable per-match identifier independent of player properties. No empirical threshold test needed — orthogonality follows from the derivation's structure.
   - Profile_id-ordered and old_rating-ordered alternatives were both explicitly rejected (01_04_05 Q4 showed profile_id-ordering IS skill-correlated via account-age proxy; old_rating is skill-coupled by construction).
   - Row count preserved: 35,629,894 rows (10 columns; was 9).
   - Assertions all pass (row_count_preserved, binary_cardinality, per_match_distinct, balance_wr reported as evidence).

   ### Invariants touched
   - I3: no change.
   - I5: PARTIAL → HOLDS (post-amendment; W4 discharged).
   - I7: canonical_slot derivation formula cited inline + in 01_04_03b artifact.
   - I9: pure projection; BEFORE/AFTER existing-column stats unchanged.

   ### Artifact paths
   - `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.json`
   - `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.md`
   - `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_history_minimal.yaml` (10-col schema)

   ### Thesis mapping
   - §4.4.6 flag closure (pending Pass-2 revision; see REVIEW_QUEUE).
   ```
2. Prepend to `reports/research_log.md` (CROSS log) at line 20 (above the existing 2026-04-19 Phase 01 / 01_06 entry):
   ```markdown
   ## [CROSS] 2026-04-20 — [BACKLOG F1 + W4 / aoestats] canonical_slot amendment: schema surface +1 column, spec v1.0.5 → v1.1.0

   **Source:** aoestats research_log.md 2026-04-20 F1+W4 entry.

   Single-dataset amendment (aoestats only); sibling datasets (sc2egset, aoe2companion) unchanged. Adds `canonical_slot VARCHAR` to `matches_history_minimal` via hash-on-match_id derivation (skill-orthogonal by structural construction — both rows of any match share the same match_id hence the same hash; the binary splitter with focal_team pivot distributes them into complementary slots; argument independent of match_id's semantic content). Flips INVARIANTS.md §5 I5 PARTIAL → HOLDS and the 01_06 decision gate from READY_CONDITIONAL to READY_WITH_DECLARED_RESIDUALS. Spec §14 bumps to v1.1.0. Cross-dataset UNION ALL (if ever needed) must project the 9 shared columns only — aoestats extends locally. [PRE-canonical_slot] flag protocol in spec §9 transitions from ACTIVE to HISTORICAL.

   **Phase 02 implication:** GO-NARROW → GO-FULL for aoestats. Per-slot features (canonical_slot-conditioned old_rating, civ, faction stratifiers) now invariant-safe.
   ```

**Verification.**
- Both logs updated with new entries.
- Entries link to 01_04_03b artifact.

**File scope.**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md`
- `reports/research_log.md`

**Read scope.**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.json` (T01 output)

---

### T09 — Remove BACKLOG F1 entry + thesis §4.4.6 flag resolution footnote

**Objective.** Close the BACKLOG loop: remove the F1 entry (it is resolved), and leave the F4+ entries intact. Add a thesis §4.4.6 footnote pointing to the F1 resolution (substantive §4.4.6 revision deferred to Pass-2 as a separate Cat F session — see Out of scope).

**Instructions.**
1. In `planning/BACKLOG.md`, delete the F1 entry (lines 17-58 in current file; the entire block between `### F1 — aoestats...` and the next `---` or `### F4 —` header). Do not renumber remaining items (F4, F5, F6 already merged; preserve their numbering for provenance).
2. In `thesis/chapters/04_data_and_methodology.md` §4.4.6 (line ~399, the closure paragraph about "Zamknięcie flagi wymaga wykonania amendmentu Phase 02"), append a footnote-style `[REVIEW: post-F1 resolved]` marker with a parenthetical: `— amendment operationalny wykonany w PR #TBD (branch feat/aoestats-canonical-slot, 2026-04-19); INVARIANTS.md §5 I5 transitioned PARTIAL → HOLDS; spec v1.1.0 §14. Substantive §4.4.6 rewrite (flag z ACTIVE na HISTORICAL + referencje do 10-col schema) deferred do Pass-2 jako osobna Cat F session` — do NOT rewrite the Polish section prose; that is a separate Cat F thesis revision to be triaged via WRITING_STATUS.md.
3. In `thesis/chapters/REVIEW_QUEUE.md`, add a Pending entry:
   ```
   | §4.4.6 | Post-F1 revision | DRAFTED | Pass-2: rewrite §4.4.6 closure paragraph to reflect canonical_slot amendment landed in PR #TBD (2026-04-19). Update Tabela references, flip flag from ACTIVE to HISTORICAL, cite 01_04_03b artifact. Estimated effort: 1 Cat F session. |
   ```

**Verification.**
- `grep F1 planning/BACKLOG.md` returns zero matches.
- `grep 01_04_03b thesis/chapters/04_data_and_methodology.md` returns the new footnote.
- REVIEW_QUEUE.md carries the Pending §4.4.6 revision item.

**File scope.**
- `planning/BACKLOG.md`
- `thesis/chapters/04_data_and_methodology.md`
- `thesis/chapters/REVIEW_QUEUE.md`

**Read scope.**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.json` (T01 output)

---

### T10 — CHANGELOG + version bump

**Objective.** Register this PR in `CHANGELOG.md` under `[Unreleased]` and bump `pyproject.toml` version per git-workflow convention (minor bump for `feat/`: 3.28.1 → 3.29.0).

**Instructions.**
1. In `CHANGELOG.md` `[Unreleased]` section, populate:
   ```markdown
   ### Added

   - aoestats `canonical_slot VARCHAR` column in `matches_history_minimal` (hash-on-match_id; skill-orthogonal by construction). Resolves BACKLOG F1. Artifact: `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.{json,md}`.

   ### Changed

   - INVARIANTS.md §5 I5 row: PARTIAL → HOLDS (W4 operational content).
   - `reports/specs/01_05_preregistration.md` bumped v1.0.5 → v1.1.0 (§14 amendment log; aoestats `matches_history_minimal` 9 → 10 columns; cross-dataset UNION ALL contract projects 9 shared columns only).
   - `modeling_readiness_aoestats.md` verdict: READY_CONDITIONAL → READY_WITH_DECLARED_RESIDUALS. Phase 02 scope: GO-NARROW → GO-FULL.
   - `risk_register_aoestats.csv` AO-R01 mitigation_status: OPEN → RESOLVED.

   ### Fixed

   - `[PRE-canonical_slot]` flag protocol transitioned ACTIVE → HISTORICAL (operational closure of §4.4.6 flag; substantive thesis rewrite deferred to Pass-2 per REVIEW_QUEUE).

   ### Removed

   - `planning/BACKLOG.md` F1 entry (resolved).
   ```
2. After user approves and PR is merge-ready, bump `pyproject.toml` `version = "3.28.1"` → `version = "3.29.0"` and move `[Unreleased]` → `[3.29.0] — YYYY-MM-DD (PR #N: feat/aoestats-canonical-slot)` per git-workflow rule. This step is executed by the wrap-up flow, not in this plan's executor body — flag it as "to be performed at PR wrap-up" in the executor instructions.

**Verification.**
- `[Unreleased]` section populated with four headings.
- Version bump deferred to wrap-up.

**File scope.**
- `CHANGELOG.md`
- `pyproject.toml` (at wrap-up only)

**Read scope.**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.json` (T01 output)

---

## File Manifest

| File | Action |
|------|--------|
| `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.py` | Create |
| `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.ipynb` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.json` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.md` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_history_minimal.yaml` | Update |
| `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_1v1_clean.yaml` | Update |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md` | Update |
| `reports/specs/01_05_preregistration.md` | Update |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/risk_register_aoestats.csv` | Update |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/risk_register_aoestats.md` | Update |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoestats.md` | Update |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md` | Update |
| `reports/research_log.md` | Update |
| `planning/BACKLOG.md` | Update (delete F1 entry) |
| `thesis/chapters/04_data_and_methodology.md` | Update (footnote only) |
| `thesis/chapters/REVIEW_QUEUE.md` | Update |
| `CHANGELOG.md` | Update |
| `pyproject.toml` | Update (at wrap-up only; version bump 3.28.1 → 3.29.0) |

## Gate Condition

All of the following must hold for the plan to be considered complete:

1. **Notebook execution success.** `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.py` runs end-to-end with zero exceptions, baseline re-verification (T01 step 3) PASSes, and all 7 assertions in T01 step 6 return TRUE. Both `.py` and `.ipynb` committed.
2. **Row count preservation.** `SELECT COUNT(*) FROM matches_history_minimal` returns exactly **35,629,894** (identical to pre-amendment baseline). Assertion verified in `01_04_03b_canonical_slot_amendment.json` under `assertions.row_count_preserved: true`.
3. **Schema width transition.** `DESCRIBE matches_history_minimal` returns **10 columns** in the order `[match_id, started_at, player_id, opponent_id, faction, opponent_faction, won, canonical_slot, duration_seconds, dataset_tag]`. Verified in both the notebook and `matches_history_minimal.yaml` (`schema_version: 10-col`).
4. **canonical_slot well-formedness.** Distinct values set is exactly `{'slot_A', 'slot_B'}` with zero NULLs; every match_id has exactly one row with each slot value. Skill-orthogonality is established by construction (hash depends only on match_id, independent of player properties), not by a magic-number win-rate threshold. The balance statistic (per-slot win rate ≈ 0.5) is reported as confirmatory evidence, not gated.
5. **Spec version bump.** `reports/specs/01_05_preregistration.md` frontmatter `spec_version: "1.1.0"` and §14 contains the v1.1.0 amendment block.
6. **INVARIANTS transition.** `INVARIANTS.md` §5 I5 row shows `HOLDS` (no remaining PARTIAL status for I5). §4 has the 2026-04-19 addendum.
7. **Risk register + readiness update.** `risk_register_aoestats.csv` AO-R01 `mitigation_status = RESOLVED`. `modeling_readiness_aoestats.md` §1 verdict = `READY_WITH_DECLARED_RESIDUALS`; §5 = `GO-FULL`.
8. **Downstream notebook zero-impact audit.** T06 audit note appended to `01_04_03b_canonical_slot_amendment.md` confirms zero `SELECT *` patterns in existing 01_05 or production aoestats code.
9. **Research log updates.** aoestats `research_log.md` and CROSS `research_log.md` both carry the 2026-04-19 F1+W4 entry.
10. **BACKLOG F1 closure.** `grep '### F1' planning/BACKLOG.md` returns zero matches.
11. **Thesis §4.4.6 footnote + REVIEW_QUEUE.** `thesis/chapters/04_data_and_methodology.md` §4.4.6 carries the post-F1-resolved footnote; `REVIEW_QUEUE.md` carries the Pending substantive-rewrite item.
12. **CHANGELOG.** `[Unreleased]` populated with Added/Changed/Fixed/Removed entries.
13. **Tests pass.** `source .venv/bin/activate && poetry run pytest tests/ -v` passes (no new tests required — schema changes are verified by notebook assertions, not pytest; but existing tests must not regress).
14. **Pre-commit hooks pass.** `ruff` and `mypy` clean on any touched `.py` files.

## Out of scope

- **Substantive thesis §4.4.6 rewrite.** The operational footnote is added in T09, but re-writing the Polish section prose to (a) update the ACTIVE → HISTORICAL flag narrative, (b) revise Tabela cross-references, (c) revise the `planning/BACKLOG.md F1` citation is a Cat F thesis session, not Cat A. Triaged via REVIEW_QUEUE.md.
- **Phase 02 feature engineering.** Adding `canonical_slot` unblocks per-slot features but does not implement them. Phase 02 feature engineering (per-slot civ × canonical_slot stratifiers, per-slot old_rating interactions, etc.) is a separate Cat A session at Phase 02.
- **01_05 notebook re-run.** The existing 01_05_02 PSI, 01_05_06 leakage audit, and 01_05_08 Phase 06 interface notebooks are NOT re-run. Their `[PRE-canonical_slot]` flag references become historical markers of the pre-amendment state and remain in place for audit provenance. A future PR may re-run them as `01_05_Nb` amendments if needed for Phase 02 handoff; not in this plan.
- **Sibling dataset amendments.** sc2egset and aoe2companion retain the 9-column contract unchanged. Their `[POP:*]` tags and 9-column schemas are unaffected.
- **Phase 06 interface CSV re-emission.** `phase06_interface_aoestats.csv` was populated in F6 (PR #180) with 30 `[PRE-canonical_slot]` tags on per-slot rows. That artifact is not regenerated here — the flag becomes a historical marker per spec §14 v1.1.0.
- **Alternative derivation exploration.** The candidates considered and their outcomes: **hash-on-match_id SELECTED** (2026-04-20; structural-argument skill-orthogonality; stable under re-ingest contingent on match_id stability, which holds for aoestats vendor-provided game_id per `01_04_03_minimal_history_view.py:146-191`). Rejected alternatives: profile_id-ordered (01_04_05 Q4 disqualification — account-age correlates with skill), old_rating-ordered (skill-coupled by construction), hash on sorted (min, max) profile_id tuple (still player-property-dependent), lexicographic civilization name (target-leaky — civ correlates with outcome), team_0_elo-based (re-introduces W3 artefact).
- **W4 as a standalone entry.** There is no separate BACKLOG `W4` entry in `planning/BACKLOG.md`; W4 is the reviewer-adversarial label for "the schema-amendment workstream to flip I5 PARTIAL → HOLDS". Its operational payload is the INVARIANTS.md §5 row + spec §14 entries in T04/T05. No standalone W4 PR is proposed; it is bundled per Assumption A5.
- **PR open/push.** Per git-workflow rule, PR creation, push, and version bump (T10 final step) are executed at wrap-up by the user after execution + review pass, not by the executor inline.

## Open questions

- **Q1 — Derivation choice (RESOLVED 2026-04-20 by user).** Hash-on-`match_id` selected. Profile_id-ordered rejected (Q4 of 01_04_05 explicitly rejects profile_id as slot-neutralizing technique; account-age correlates with skill). Old_rating-ordered rejected (skill-coupled by construction; would recreate the bias it aimed to neutralize). Hash-on-match_id is skill-orthogonal by construction — the hash depends only on match_id, a stable per-match identifier independent of player properties.
- **Q2 — Sibling dataset mirror (W4 scope extension).** Should sc2egset and aoe2companion also grow a `canonical_slot` column for cross-dataset feature parity? Current analysis: NO — sc2egset's UNION ALL is already slot-orthogonal (no W3-analog artefact surfaced), and aoe2companion's equivalent audit was not flagged in 01_04_05. Resolves by: **deferral to Phase 02 planning session** if cross-dataset feature-parity symmetry becomes a binding concern.
- **Q3 — INVARIANTS §5 I5 wording — "HOLDS" vs "HOLDS (conditional on UNION-ALL + canonical_slot pair)".** Plan proposes the conditional phrasing. Resolves by: **reviewer-adversarial verdict**.
- **Q4 — Phase 02 mandatory-use rule.** Should INVARIANTS.md add an I5-sub-rule that Phase 02 MUST consume `canonical_slot` (not raw `team` or `p0/p1`) for aoestats per-slot features? Recommended: yes, but defer to Phase 02 planning session. Resolves by: **Phase 02 planning session**.

---

## Critique instruction for parent session

For Category A, adversarial critique is required before execution. Dispatch reviewer-adversarial to produce `planning/current_plan.critique.md` against this plan once the parent writes it to `planning/current_plan.md`. Key review vectors the reviewer should probe:

1. **Derivation choice defence (Q1 RESOLVED 2026-04-20).** Hash-on-match_id selected; skill-orthogonal by structural construction — both rows of any match share the same match_id hence the same hash, and the focal_team pivot distributes them into complementary slots (independent of match_id's semantic content). Profile_id-ordered was explicitly rejected because 01_04_05 Q4 showed `lower_id_first_win_rate = 0.5066 (+0.66pp)` is a non-trivial skill-correlated edge — account-age correlates with skill via early-adopter effect, so profile_id-ordering is not skill-orthogonal regardless of whether the magnitude of this edge is larger or smaller than the team=1 artefact (+2.27pp). Old_rating-ordered was rejected as skill-coupled by construction. Hash-on-match_id sidesteps both defects: no player attribute enters the derivation.
2. **W4 scope.** Plan claims W4 is pure documentation (INVARIANTS + spec). Reviewer should verify there is no lurking code change needed — e.g., do any existing Phase-06-interface-CSV emitters need to be re-run to drop the `[PRE-canonical_slot]` flag? Plan defers this; reviewer verify deferral is justified.
3. **Row-count preservation for I9.** T01 asserts `BEFORE_STATS` vs `AFTER_STATS` via the `01_04_03_minimal_history_view.json` baseline. But that baseline was computed 2026-04-18; the underlying DuckDB may have been re-ingested since. Reviewer: verify the baseline is still bit-identical to current DB state, or propose a re-baselining step.
4. **Fallback completeness.** Q1 resolved 2026-04-20 to hash-on-match_id; profile_id-ordered and old_rating-ordered alternatives both rejected in Problem Statement. Any future reopening of Q1 would require a new planning cycle, not a runtime override — T01 hardcodes the hash-based DDL.
5. **Thesis §4.4.6 footnote scope.** Plan plants a `[REVIEW: post-F1 resolved]` footnote without rewriting the section prose. Reviewer verify this is acceptable as a closure marker or demand inline section revision.

---

## Notes for parent / user

**For the parent (Claude as orchestrator):** This plan is ready to be written to `planning/current_plan.md` without further clarification. Dispatch reviewer-adversarial next; reviewer's critique goes to `planning/current_plan.critique.md`. After critique pass (up to 3 adversarial rounds per symmetric-rigor rule), dispatch executor to run T01 through T10.

**For the user at wake-up:** One decision point remains before execution dispatch:
1. ~~**Q1 derivation choice** — RESOLVED 2026-04-20 by user selection: hash-on-match_id. Profile_id-ordered and old_rating-ordered alternatives both rejected in plan body; no further decision needed.~~
2. **Execution dispatch** (required): approve executor invocation against `planning/current_plan.md` with task range T01–T10. Context at wake-up: plan went through 3 pre-execution adversarial rounds (REDESIGN → REVISE → REVISE) + 1 surgical Pass 4 (line-level fixes for cosmetic defects Pass 3 surfaced). Methodology core sound; scope unchanged.

Files consulted during planning (absolute paths):
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/planning/BACKLOG.md`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_05_i5_diagnosis.json`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_05_i5_diagnosis.md`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/risk_register_aoestats.csv`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoestats.md`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_history_minimal.yaml`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_1v1_clean.yaml`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03_minimal_history_view.json`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_03_minimal_history_view.py`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/reports/specs/01_05_preregistration.md`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/reports/research_log.md`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/thesis/chapters/04_data_and_methodology.md`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/.claude/scientific-invariants.md`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/docs/templates/plan_template.md`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/docs/templates/planner_output_contract.md`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoestats/reports/PHASE_STATUS.yaml`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/CHANGELOG.md`
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/pyproject.toml`
