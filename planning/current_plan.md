---
category: A
branch: feat/aoestats-old-rating-conditional-classification
date: 2026-04-21
planner_model: claude-opus-4-7
dataset: aoestats
phase: "01"
pipeline_section: 01_04
invariants_touched: [I3, I6, I7]
source_artifacts:
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_06_old_rating_temporal_audit.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.md
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/player_history_all.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md
  - reports/specs/02_00_feature_input_contract.md
  - reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md
  - .claude/scientific-invariants.md
  - docs/PHASES.md
critique_required: true
research_log_ref: src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md#2026-04-21-old-rating-conditional-classification
---

# Plan: WP-6 — aoestats `old_rating` Phase 01 conditional-classification annotation (REVISED 2026-04-21 post Mode A)

## Scope

Address the WP-4 FAIL finding **retroactively inside Phase 01** per user directive 2026-04-21 ("don't spill responsibilities of docs/PHASES.md between phases; address issues even retroactively"). Apply a Phase 01 cleaning-rule annotation that makes `old_rating` semantically usable downstream: add derived column `time_since_prior_match_days` to the `player_history_all` VIEW via DDL amendment (canonical_slot precedent pattern PR #185), demote `old_rating` to CONDITIONAL_PRE_GAME in `INVARIANTS.md §3` with an **empirically-selected threshold chosen from data** (not pre-specified), amend spec 02_00 v1 → v2 per §7 change protocol.

**Post-Mode-A revision summary (2026-04-21):** Mode A surfaced 2 BLOCKERs + 3 WARNINGs + 3 NOTEs. All 5 applicable revisions applied within symmetric 1-revision cap:
- **BLOCKER-1 (I7 threshold consistency):** The original 7-day cutoff was argued from 01_04_06 stratification but included the 1-7d bucket (0.859) which fails the WP-4 0.90 stratum gate. Fix: T02 now COMPUTES pooled `<Nd` agreement rate at N ∈ {1, 2, 3, 7} and PICKS the largest N where pooled rate ≥ 0.90; threshold is DATA-DRIVEN, not pre-specified.
- **BLOCKER-2 (cross-leaderboard evidence):** 01_04_06 stratified per-time-gap only on `random_map`. Fix: T02 now computes the full 4 × 4 leaderboard × time-gap stratification; if all 4 leaderboards clear 0.90 at the chosen N, the classification generalizes globally; otherwise the classification is SCOPED to `leaderboard = 'random_map' AND time_since_prior_match_days < N`.
- **WARNING-1:** Schema-versioning format switched from semver to canonical_slot descriptive-string precedent ("15-col (AMENDMENT: ...)").
- **WARNING-2:** T06 updates spec 02_00 §2.2 column count 14 → 15; sub-step added to update ROADMAP.md:1000 current-state reference. Historical research_log entries NOT touched.
- **WARNING-3:** INVARIANTS.md §3 + spec 02_00 §5.5 explicitly document NULL-first-match semantics (NULL → treat as PRE-GAME; no prior-match risk).

Symmetric 1-revision cap consumed.

Scope: 1 new Phase 01 step 01_04_07 (notebook + MD + JSON) + VIEW DDL amendment + YAML schema update + INVARIANTS.md §3 revision + spec 02_00 v2 amendment + research_log + ROADMAP line + version bump. 11 git-diff-scope files.

## Problem Statement

WP-4 (PR #201 / step 01_04_06) empirically falsified the unconditional PRE-GAME classification of `old_rating`:
- Primary `random_map` scope: agreement = 0.9210, max disagreement = 1,118 rating units; 3-gate verdict FAIL.
- Per-time-gap on `random_map`: <1d = 0.944; 1-7d = 0.859; 7-30d = 0.708; >30d = 0.634.
- Per-leaderboard pooled: random_map 0.921; team_random_map 0.860; co_random_map 0.855; co_team_random_map 0.787.
- Interpretive finding: aoestats.io API updates `old_rating` at seasonal/leaderboard boundaries independent of per-match results; across those boundaries, `old_rating[t+1] ≠ new_rating[t]` for mechanistic reasons.

Per docs/PHASES.md §Phase 01: Pipeline Section 01_04 (Data Cleaning) is where column classifications are decided. Fixing this at Phase 02 would spill the responsibility — Phase 02 would have to re-discover + build workarounds. Phase 01-level fix: add derived column, pick threshold from data, reclassify, amend spec.

The critical methodology question (caught by Mode A): which threshold N? The plan's ORIGINAL pre-specified choice of 7 days was internally inconsistent (included the 0.859 bucket below the 0.90 stratum gate). The REVISED approach: let the data pick N empirically by computing pooled agreement at candidate cutoffs and choosing the largest N that clears the 0.90 threshold. Also: 01_04_06's per-time-gap stratification was random_map-only; the revised plan computes per-leaderboard × per-time-gap 4×4 stratification before generalizing.

## Assumptions & unknowns

- **Assumption (VIEW DDL amendment pattern):** `player_history_all` is a real VIEW per `01_04_01_data_cleaning.md:165`; the canonical_slot precedent (01_04_03b) is the template.
- **Assumption (DuckDB LAG semantics stable):** LAG with per-leaderboard partition gives the correct temporal gap. First match per (profile_id, leaderboard) → LAG = NULL → gap = NULL by SQL three-valued logic.
- **Assumption (data-driven threshold choice is defensible):** Picking N from the pooled `<Nd` agreement curve is argued-from-data per I7 (not invented). The criterion (≥ 0.90) matches the WP-4 stratum gate.
- **Assumption (4×4 stratification is computationally feasible):** The `player_history_all` VIEW is 107.6M rows; a 4×4 stratification table requires one pass with conditional aggregation. DuckDB should handle this in O(minutes), not O(hours).
- **Unknown (chosen N value):** determined empirically in T02. Must be 1 ≤ N ≤ 7.
- **Unknown (scope decision):** global (all leaderboards) vs. random_map-only. Determined empirically in T02 from the 4×4 stratification.
- **Unknown (first-match rate):** unknown a priori; T03 JSON records it.

## Literature context

Not applicable — internal Phase 01 cleaning annotation. References:
- `.claude/scientific-invariants.md` I3 (temporal), I6 (SQL verbatim), I7 (threshold argued from data).
- `docs/PHASES.md §Phase 01` Pipeline Section 01_04 — Data Cleaning.
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_06_old_rating_temporal_audit.{md,json}` — WP-4 empirical evidence (random_map-scoped).
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.{md,json}` (PR #185) — DDL-amendment-as-annotation precedent.
- `reports/specs/02_00_feature_input_contract.md` §7 — change protocol for v1 → v2 major bump.

## Execution Steps

### T01 — Inspect current `player_history_all` DDL + downstream 14-col references

**Objective:** Capture current DDL; verify no materialized tables exist; inventory downstream "14 cols" references that need updating.

**Instructions:**
1. Read `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md` around line 165 — capture current `CREATE OR REPLACE VIEW player_history_all AS ...` verbatim.
2. Read `01_04_03b_canonical_slot_amendment.md` — study the DDL-amendment artifact structure (schema yaml, descriptive schema_version string, documentation pattern).
3. Read `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.json` — confirm `player_history_all` is VIEW (not materialized).
4. Grep for current-state "14 cols" / "14 columns" / "14-col" references in `aoestats/reports/ROADMAP.md` and `reports/specs/02_00_feature_input_contract.md` — catalog the lines that need updating (current-state, not historical research_log entries).
5. Identify any downstream VIEWs that SELECT from `player_history_all`.

**Verification:**
- Current DDL captured.
- Canonical_slot precedent pattern understood.
- List of "14 cols" references requiring update: at minimum ROADMAP.md:1000 + spec 02_00 §2.2.
- No unexpected materialized dependencies.

**File scope:** None (read-only).
**Read scope:** listed yaml + md artifacts.

---

### T02 — Write sandbox notebook `01_04_07_old_rating_conditional_annotation.py`

**Objective:** Amend `player_history_all` VIEW DDL + run the EMPIRICAL threshold-selection analysis (pooled `<Nd` agreement per candidate cutoff + 4×4 leaderboard × time-gap stratification).

**Instructions:**
1. Create `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_07_old_rating_conditional_annotation.py` (jupytext auto-pairs).
2. Notebook structure:
   - **Header cell:** step description; post-Mode-A framing.
   - **Motivation cell:** cite 01_04_06's per-time-gap random_map stratification + per-leaderboard pooled agreements. Acknowledge the Mode A catch: random_map-only stratification does not justify a global cutoff without 4×4 test.
   - **Threshold-selection cell (BLOCKER-1 fix):** For each candidate cutoff N ∈ {1, 2, 3, 7} (days), compute the pooled agreement rate across `random_map` PAIRS where `time_since_prior_match_days < N`. Produce a table: N, n_pairs_eligible, pooled_agreement. Choose `N*` = the LARGEST N such that pooled agreement ≥ 0.90. Record the chosen N* in executor output.
   - **4×4 stratification cell (BLOCKER-2 fix):** For each leaderboard ∈ {random_map, team_random_map, co_random_map, co_team_random_map} × each time-gap bucket ∈ {<1d, 1-7d, 7-30d, >30d}, compute n_pairs + agreement_rate. Also compute per-leaderboard agreement at `time_since_prior_match_days < N*` (the chosen cutoff). Determine SCOPE:
     - If all 4 leaderboards' agreement at `<N*` ≥ 0.90 → SCOPE = GLOBAL (all leaderboards).
     - Otherwise → SCOPE = `random_map` only.
     Record SCOPE in executor output.
   - **Current VIEW DDL** verbatim from T01 for reference.
   - **Amended VIEW DDL:** `CREATE OR REPLACE VIEW player_history_all AS` with new column:
     ```sql
     SELECT
       <existing columns>,
       CAST(
         (EXTRACT(EPOCH FROM (started_timestamp -
           LAG(started_timestamp) OVER (
             PARTITION BY CAST(profile_id AS BIGINT), leaderboard
             ORDER BY started_timestamp, game_id
           )
         )) / 86400.0) AS DOUBLE
       ) AS time_since_prior_match_days
     FROM <existing source>
     ```
     Same CAST discipline (DS-AOESTATS-IDENTITY-04) + same tie-breaker `game_id` as 01_04_06.
   - **Execution cell:** DROP + CREATE the VIEW; verify row count unchanged (107,626,399); `DESCRIBE player_history_all` to confirm new column.
   - **Verification cells:**
     - Spot-check 10+ (profile_id, leaderboard) sequences: positive time gaps for non-first, NULL for first.
     - **First-match NULL rate (WARNING-3):** compute `n_null / n_total` and report.
     - **Rating-reset correlation:** Pearson ρ between `time_since_prior_match_days` and `|old_rating - LAG(new_rating)|` (for rows where LAG(new_rating) is not NULL).
   - **Summary cell:** print chosen N*, chosen SCOPE, first-match NULL rate, correlation ρ, 4×4 stratification table.
   - **Artifact export cell:** write JSON + MD to `reports/artifacts/01_exploration/04_cleaning/`.

3. Human-readable section headers throughout; no plan codes.

**Verification:**
- Notebook runs end-to-end.
- Row count unchanged post-amendment.
- Column present in DESCRIBE.
- Chosen N* and SCOPE recorded in notebook output.
- 4×4 stratification table populated.
- First-match NULL rate reported.
- Correlation ρ reported.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_07_old_rating_conditional_annotation.py` (Create)
- `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_07_old_rating_conditional_annotation.ipynb` (Create; jupytext)

**Read scope:** `player_history_all`, `01_04_01_data_cleaning.md`, `01_04_06_*.md`.

---

### T03 — Write artifact MD + JSON

**Objective:** Canonical artifact; threshold-selection evidence front-and-center.

**Instructions:**
1. Write `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_07_old_rating_conditional_annotation.md`:
   - **§1 Scope and motivation** — WP-4 FAIL → Phase 01 annotation per docs/PHASES.md §Phase 01 01_04; post-Mode-A data-driven threshold selection.
   - **§2 DDL verbatim (I6)** — before + after VIEW DDL.
   - **§3 Column definition** — `time_since_prior_match_days` type, semantics, NULL behavior (first match per `(profile_id, leaderboard)` → NULL).
   - **§4 Threshold selection (BLOCKER-1 resolution)** — pooled-agreement-at-cutoff table for N ∈ {1, 2, 3, 7}; chosen `N* = <VALUE>` with explicit argument "the largest N where pooled agreement on `random_map` clears the 0.90 stratum gate per I7."
   - **§5 Scope selection (BLOCKER-2 resolution)** — 4×4 leaderboard × time-gap stratification table; per-leaderboard agreement at `< N*`; chosen SCOPE (GLOBAL or `random_map`-only) with explicit argument.
   - **§6 NULL-first-match handling (WARNING-3 resolution)** — explicit rule: NULL → treat as PRE-GAME (rationale: no prior match exists, so "cross-session reset" risk is zero for the initial `old_rating` value). First-match NULL rate reported.
   - **§7 Verification** — row count unchanged; correlation ρ.
   - **§8 Downstream impact** — list of updates: `player_history_all.yaml` schema version; INVARIANTS.md §3 CONDITIONAL classification with chosen N* + SCOPE; spec 02_00 v1 → v2.
2. Write `01_04_07_old_rating_conditional_annotation.json`:
   - Fields: `step` ("01_04_07"), `view_amended` ("player_history_all"), `column_added` ("time_since_prior_match_days"), `column_type` ("DOUBLE"), `row_count_pre` (int), `row_count_post` (int; must equal pre), `first_match_null_rate` (float), `threshold_candidates` (dict — `{1: {n_pairs, pooled_agreement}, 2: {...}, 3: {...}, 7: {...}}`), `chosen_threshold_days` (int — N*), `threshold_argument` (string — "largest N where pooled agreement on random_map ≥ 0.90"), `stratification_4x4` (nested dict — `{leaderboard: {time_gap_bucket: {n_pairs, agreement_rate}}}`), `per_leaderboard_at_chosen_threshold` (dict — `{leaderboard: agreement_rate}`), `chosen_scope` (string — "GLOBAL" or "random_map_only"), `scope_argument` (string), `correlation_with_rating_reset_magnitude` (float), `audit_date` (ISO = "2026-04-21").

**Verification:**
- Both files exist.
- §2 DDL verbatim.
- §4 table has 4 rows (N ∈ {1,2,3,7}); chosen N* highlighted.
- §5 table is 4×4 (4 leaderboards × 4 time-gap buckets); chosen SCOPE highlighted.
- §6 NULL rule stated explicitly.
- JSON parses; all fields present including both threshold candidates and 4×4 stratification.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_07_old_rating_conditional_annotation.md` (Create)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_07_old_rating_conditional_annotation.json` (Create)

**Read scope:** T02 notebook.

---

### T04 — Update `player_history_all.yaml` schema (descriptive-string versioning per WARNING-1)

**Objective:** Document the new column + schema_version in canonical_slot-precedent descriptive-string format.

**Instructions:**
1. Edit `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/player_history_all.yaml`.
2. ADD a `schema_version` field (new; matching canonical_slot pattern on matches_history_minimal.yaml): `schema_version: '15-col (AMENDMENT: time_since_prior_match_days added 2026-04-21 per 01_04_07)'`.
3. Append column entry:
   ```yaml
   - name: time_since_prior_match_days
     type: DOUBLE
     nullable: true
     description: Calendar days since this player's prior match on the same leaderboard (LAG window partitioned by CAST(profile_id AS BIGINT), leaderboard; ordered by started_timestamp, game_id tie-breaker).
     notes: CONTEXT. NULL for first match per (profile_id, leaderboard) sequence. Used by INVARIANTS.md §3 CONDITIONAL_PRE_GAME classification of old_rating — PRE-GAME iff time_since_prior_match_days < N* OR time_since_prior_match_days IS NULL (chosen N* and scope per 01_04_07 artifact §4-§5). NULL is treated as PRE-GAME (no prior-match cross-session risk).
   ```
4. Preserve `step: '01_04_02'` as original provenance; schema_version string communicates the v1.0 → 15-col amendment.

**Verification:**
- `grep "schema_version" src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/player_history_all.yaml` returns the new field.
- `grep "time_since_prior_match_days" ...` returns the new column entry.
- Format matches canonical_slot precedent (descriptive string, not semver).

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/player_history_all.yaml` (Update)

---

### T05 — Update `INVARIANTS.md §3` — data-driven CONDITIONAL classification

**Objective:** Revise the `old_rating` bullet with EMPIRICALLY-SELECTED N* and SCOPE from T02 + explicit NULL handling.

**Instructions:**
1. Edit `src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md §3`.
2. Replace the current WP-4-era `old_rating` bullet (line ~76) with:

   "**`old_rating` CONDITIONAL_PRE_GAME classification:** Classified CONDITIONAL_PRE_GAME per Phase 01 01_04 classification discipline (docs/PHASES.md §Phase 01). **Condition:** `old_rating` is PRE-GAME iff (a) `<SCOPE_PREDICATE>` AND (b) `time_since_prior_match_days < <N*>` OR `time_since_prior_match_days IS NULL` (first match per leaderboard — no prior-match cross-session risk). `<SCOPE_PREDICATE>` is either `TRUE` (if SCOPE=GLOBAL) or `leaderboard = 'random_map'` (if SCOPE=random_map-only). `<N*>` is the empirically-selected threshold: the largest N ∈ {1, 2, 3, 7} days where pooled agreement on `random_map` clears the WP-4 0.90 stratum gate (01_04_07 §4). **Empirical grounding:** 01_04_06 (leaderboard-partitioned consecutive-match test) + 01_04_07 (threshold-selection + 4×4 leaderboard × time-gap stratification). **Structural supplement:** `matches_1v1_clean.yaml:excluded_columns` excludes `new_rating`/`p*_new_rating` as POST-GAME at the clean-view level. **Derived column anchor:** `time_since_prior_match_days` added to `player_history_all` VIEW (15-col schema per v1 amendment). **Phase 02 implications:** rolling features using `old_rating` should apply the condition as a filter or use dual feature paths (within-scope vs cross-session). (01_03_01 + 01_04_06 + 01_04_07)"

   Executor fills `<SCOPE_PREDICATE>` and `<N*>` from T03 JSON. No `<PLACEHOLDER>` strings remain.

3. Preserve surrounding §3 bullets.

**Verification:**
- `grep "CONDITIONAL_PRE_GAME" src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md` returns the new classification.
- No `<PLACEHOLDER>` literals in the file.
- Existing §3 bullets (Temporal anchor, Coverage, Inter-file temporal gaps, overviews_raw, Age uptimes, duration_seconds, Slot bias) preserved.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md` (Update)

**Read scope:** T03 JSON.

---

### T06 — Amend `reports/specs/02_00_feature_input_contract.md` v1 → v2

**Objective:** Spec amendment per §7 change protocol. Update column count + schema_version; add column row to §5.5; log amendment in §7.

**Instructions:**
1. Edit `reports/specs/02_00_feature_input_contract.md`.
2. Frontmatter: `spec_id: CROSS-02-00-v2`, `version: CROSS-02-00-v2`, `supersedes: CROSS-02-00-v1`, `date: 2026-04-21`.
3. **§2.2 aoestats `player_history_all`** (WARNING-2 resolution): update "Column count" from 14 → 15. Update "Schema version" row to match the new schema_version descriptive string (or reflect that one was introduced).
4. **§5.5 aoestats `player_history_all` classification table** — add row:
   `| time_since_prior_match_days | DOUBLE | CONTEXT | Calendar days since player's prior match on same leaderboard; NULL for first match per (profile_id, leaderboard). Phase 02 CONDITIONAL_PRE_GAME gate for old_rating via < N* condition (NULL treated as PRE-GAME per INVARIANTS.md §3). Added 01_04_07 (2026-04-21). |`
5. **§7 Spec change protocol** — add amendment log entry:
   "**2026-04-21 — CROSS-02-00-v1 → CROSS-02-00-v2.** aoestats §5.5 `player_history_all` adds `time_since_prior_match_days` (DOUBLE, CONTEXT) per WP-6 / 01_04_07. §2.2 column count 14 → 15; schema_version string introduced per canonical_slot precedent. Motivation: WP-4 empirical FAIL of unconditional `old_rating` PRE-GAME classification; Phase 01-level annotation per docs/PHASES.md §Phase 01 01_04 discipline. Major version bump per §7 (§2 column-count commitment change)."

**Verification:**
- `grep "CROSS-02-00-v2" reports/specs/02_00_feature_input_contract.md` returns new version.
- `grep "time_since_prior_match_days" ...` returns §5.5 row.
- §2.2 "Column count" reflects 15 for aoestats player_history_all.
- §7 amendment log has the 2026-04-21 entry.

**File scope:**
- `reports/specs/02_00_feature_input_contract.md` (Update)

---

### T07 — Update `ROADMAP.md` current-state 14-col reference (WARNING-2 part 2)

**Objective:** Refresh the dataset ROADMAP's current-state references to `player_history_all` column count (14 → 15). Historical research_log entries NOT touched.

**Instructions:**
1. Edit `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`.
2. Locate any current-state reference to `player_history_all` as "14 cols" / "14 columns" (e.g., around line 1000, 1053). For each reference that describes the CURRENT VIEW (not a historical derivation or a step's original output), update 14 → 15 with a parenthetical note "(post-01_04_07 amendment 2026-04-21)".
3. Do NOT modify references that describe a HISTORICAL step's output at time-of-step (those are historical records). Distinguish: "ROADMAP states the current VIEW is 14 cols" → update; "01_04_02 step produced a 14-col VIEW" → historical, preserve.

**Verification:**
- `grep "14 cols\|14 columns" src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` returns only historical references (or zero, if no such references exist).
- `grep "15 cols\|15-col" ROADMAP.md` returns the updated references.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` (Update)

---

### T08 — Append research_log entry

**Objective:** Document step per per-dataset protocol with threshold-selection + scope-selection findings.

**Instructions:**
1. Prepend new entry to `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md`.
2. Entry:
   - Date: `## 2026-04-21 — [Phase 01 / Step 01_04_07] old_rating CONDITIONAL_PRE_GAME Phase 01 annotation (data-driven threshold)`
   - **Category:** A.
   - **Dataset:** aoestats.
   - **Step scope:** WP-4 FAIL → Phase 01 01_04 annotation per docs/PHASES.md; post-Mode-A data-driven threshold + 4×4 scope selection.
   - **Artifacts produced:** T03 MD + JSON; T02 notebook.
   - **What:** Added `time_since_prior_match_days` DOUBLE column to `player_history_all` VIEW. Empirically selected threshold N* = `<N*>` days (from candidates {1, 2, 3, 7}). Empirically selected SCOPE = `<SCOPE>` (GLOBAL or random_map-only). Demoted `old_rating` to CONDITIONAL_PRE_GAME. Spec 02_00 v1 → v2 amendment.
   - **Why:** User directive 2026-04-21 requires Phase 01-level fix. Mode A caught unconditional threshold + cross-leaderboard generalization issues; revision applied empirical selection.
   - **How (reproducibility):** Notebook 01_04_07; DDL amendment verbatim per I6; per-leaderboard partition + game_id tie-breaker match 01_04_06.
   - **Findings:** Pooled `<Nd` agreement at candidates (table); chosen N*; 4×4 stratification; chosen SCOPE; first-match NULL rate; correlation ρ.
   - **Decisions taken:** CONDITIONAL_PRE_GAME classification with N* and SCOPE.
   - **Decisions deferred:** Phase 02 chooses how to USE the annotation.
   - **Thesis mapping:** §4.2.3 may reference CONDITIONAL_PRE_GAME + evidence chain (01_04_06 + 01_04_07). Pass-2 Chat.
   - **Open questions / follow-ups:** if SCOPE = random_map-only, whether to compute separate thresholds for other leaderboards in a future step (deferred).

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md` (Update)

---

### T09 — Version bump + CHANGELOG

**Objective:** Version 3.41.2 → 3.42.0 (minor, feat).

**Instructions:**
1. `pyproject.toml`: `3.41.2` → `3.42.0`.
2. `CHANGELOG.md`: move `[Unreleased]` aside; add `[3.42.0] — 2026-04-21 (PR #TBD: feat/aoestats-old-rating-conditional-classification)`:
   - `### Added`: New Phase 01 step 01_04_07 — aoestats `old_rating` CONDITIONAL_PRE_GAME annotation. `player_history_all` VIEW amended via DDL to add `time_since_prior_match_days` DOUBLE column (row count preserved at 107,626,399). Notebook + MD + JSON artifacts with data-driven threshold selection (N* ∈ {1, 2, 3, 7} days chosen empirically) + 4×4 leaderboard × time-gap stratification (SCOPE = GLOBAL or random_map-only, chosen empirically). Applies WP-4 FAIL finding as Phase 01 cleaning annotation per user directive 2026-04-21.
   - `### Changed`: `INVARIANTS.md §3` — `old_rating` demoted from PRE-GAME (WP-4 FAIL) to CONDITIONAL_PRE_GAME with empirically-selected N* + SCOPE + explicit NULL-first-match handling. `player_history_all.yaml` schema_version field introduced per canonical_slot descriptive-string precedent. `reports/specs/02_00_feature_input_contract.md` amended CROSS-02-00-v1 → CROSS-02-00-v2 per §7 (§2.2 column count 14 → 15; §5.5 adds column row; §7 amendment log). `aoestats/reports/ROADMAP.md` current-state 14-col references updated to 15-col.
3. Reset `[Unreleased]`.

**Verification:**
- `pyproject.toml` `version = "3.42.0"`.
- `CHANGELOG.md` `[3.42.0]` populated.

**File scope:**
- `pyproject.toml` (Update)
- `CHANGELOG.md` (Update)

---

## File Manifest

| File | Action |
|------|--------|
| `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_07_old_rating_conditional_annotation.py` | Create |
| `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_07_old_rating_conditional_annotation.ipynb` | Create (jupytext) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_07_old_rating_conditional_annotation.md` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_07_old_rating_conditional_annotation.json` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/player_history_all.yaml` | Update |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md` | Update |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` | Update |
| `reports/specs/02_00_feature_input_contract.md` | Update |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md` | Update |
| `pyproject.toml` | Update |
| `CHANGELOG.md` | Update |
| `planning/current_plan.md` | (this plan; tracked separately) |
| `planning/current_plan.critique.md` | (Mode A) |

11 git-diff-scope files (4 new + 7 modified) + 2 planning meta.

## Gate Condition

- Notebook 01_04_07 runs end-to-end; VIEW amendment succeeds; row count preserved.
- `time_since_prior_match_days` in DESCRIBE + in player_history_all.yaml.
- **Threshold selection (BLOCKER-1):** chosen N* is the largest N ∈ {1, 2, 3, 7} with pooled agreement on `random_map` ≥ 0.90; argument in T03 §4 + JSON `threshold_argument`.
- **Scope selection (BLOCKER-2):** 4×4 stratification computed; chosen SCOPE is either GLOBAL (all 4 leaderboards clear 0.90 at `<N*`) or `random_map`-only; argument in T03 §5 + JSON `scope_argument`.
- **NULL handling (WARNING-3):** INVARIANTS.md §3 + spec 02_00 §5.5 explicitly document NULL → PRE-GAME rule.
- **Schema versioning (WARNING-1):** descriptive-string format per canonical_slot precedent.
- **Column-count cascades (WARNING-2):** spec 02_00 §2.2 + ROADMAP.md updated 14 → 15.
- INVARIANTS.md §3 reclassified to CONDITIONAL_PRE_GAME with N* and SCOPE values filled (no `<PLACEHOLDER>`).
- Spec bumped v1 → v2; §7 amendment log entry present.
- Research log 01_04_07 entry complete.
- `pyproject.toml` 3.42.0; CHANGELOG `[3.42.0]` populated.
- All three `PHASE_STATUS.yaml` unchanged.
- `git diff --stat` touches exactly 11 git-diff-scope files + planning meta.
- **Phase responsibility discipline:** amendment in Phase 01 01_04 (Data Cleaning); classification in INVARIANTS.md §3 (Phase 01 documentation); spec §5.5 is cross-dataset Phase 01 output summary. No Phase 02 responsibilities spilled.

## Out of scope

- **Phase 02 usage decisions** — how Phase 02 filters/uses the column. Phase 02 planner-science decides.
- **`matches_history_minimal` propagation** — would break cross-dataset 9/10-col contract. Phase 02 consumes `player_history_all` directly.
- **sc2egset / aoe2companion analogous annotations** — WP-7 handles sc2egset; aoe2companion unaffected (different rating semantics).
- **Retroactive modification of 01_04_06 artifact** — WP-4 record preserved; 01_04_07 is subsequent.
- **Thesis §4.2.3 prose edits** — Pass-2 Chat.
- **Per-leaderboard-specific thresholds if SCOPE = random_map-only** — deferred to a future step; this plan scopes the classification honestly to what the data supports.

## Open questions

- **Q1 (resolved in T02):** Threshold N* — data-driven selection from {1, 2, 3, 7} days; chosen empirically in T02.
- **Q2 (resolved in T02):** Scope — data-driven from 4×4 stratification.
- **Q3 (resolved in T05 + T06):** NULL-first-match → PRE-GAME (no prior-match risk).
- **Q4 (deferred):** per-leaderboard-specific thresholds if SCOPE = random_map-only — future step.
- **Q5 (resolved):** Spec v1 → v2 major bump per §7 column-count commitment change.

## Dispatch sequence

1. This plan at `planning/current_plan.md` on branch `feat/aoestats-old-rating-conditional-classification`.
2. `reviewer-adversarial` Mode A invoked 2026-04-21 — verdict REVISE with 2 BLOCKERs + 3 WARNINGs + 3 NOTEs. **Revision round applied 2026-04-21:** all 5 findings addressed (data-driven threshold T02 cell + 4×4 stratification T02 cell; descriptive-string schema_version T04; spec §2.2 + ROADMAP updates T06/T07; explicit NULL rule T05). Critique preserved. Symmetric 1-revision cap consumed.
3. Executor dispatched with T01–T09.
4. `reviewer-adversarial` Mode C post-draft (Cat A default). If REVISE: apply once.
5. Pre-commit (ruff/mypy N/A; planning-drift passes; jupytext sync fires; no 01_05 binding — 01_04 scope).
6. Commit + PR + merge.
7. Post-merge: WP-7 (sc2egset cross-region Phase 01 annotation) overwrites plan.
