---
category: D
branch: fix/aoestats-old-rating-pregame-closure
date: 2026-04-21
planner_model: claude-opus-4-7
dataset: aoestats
phase: "01"
pipeline_section: 01_04
invariants_touched: [I3, I6, I7]
source_artifacts:
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_1v1_clean.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/players_raw.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/matches_raw.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md
  - reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md
  - thesis/chapters/04_data_and_methodology.md
  - .claude/scientific-invariants.md
critique_required: true
research_log_ref: src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md#2026-04-21-old-rating-pregame-closure
---

# Plan: WP-4 — aoestats `old_rating` PRE-GAME empirical closure (REVISED 2026-04-21 post Mode A)

## Scope

Close the `old_rating` PRE-GAME deferral flag in `INVARIANTS.md §3` with empirical evidence via a **leaderboard-partitioned** consecutive-match temporal consistency test. Closes aoestats WARNING 2 per `phase01_audit_summary_2026-04-21.md §3`.

**Primary test scope:** single leaderboard `random_map` (the canonical 1v1 ladder per aoestats convention; largest-n stratum; most thesis-relevant since RQ3 compares RM 1v1 predictions). Per-leaderboard stratification runs over all leaderboards as a sensitivity / generalization check; overall verdict requires pooled + every-leaderboard + every-time-gap-bucket thresholds simultaneously.

Scope: one new notebook step at `01_04_06` + MD + JSON + INVARIANTS §3 update + research_log entry + version/CHANGELOG. 8 git-diff-scope files.

**Post-Mode-A revision summary (2026-04-21):** Mode A surfaced 2 BLOCKERs + 5 WARNINGs + 3 NOTEs. All 8 revisions applied within symmetric 1-revision cap:
- **BLOCKER 1:** LAG() partition scope corrected to `(profile_id, leaderboard)` with explicit `players_raw JOIN matches_raw USING (game_id)`; primary scope = `leaderboard = 'random_map'`; per-leaderboard stratification for sensitivity.
- **BLOCKER 2:** `CAST(profile_id AS BIGINT)` added in Setup per DS-AOESTATS-IDENTITY-04.
- **WARNING 3:** 0.95 agreement threshold argued decision-theoretically: disagreement rate > 5% would mean ≥ 5% of `old_rating` values are potentially POST-GAME contaminated, exceeding DS-AOESTATS-02's ~0.03% cleaning-loss tolerance by 2 orders of magnitude; the 5% ceiling is the threshold at which the classification becomes materially unsound.
- **WARNING 4:** redundant `CI_95_lower ≥ 0.90` dropped (trivially satisfied at n ~ 10M⁺); replaced with disagreement-magnitude gate: `max(|old_rating[t+1] − new_rating[t]|) < 50 rating units` tests for rounding errors / seasonal drift beyond the hypothesis's tolerance.
- **WARNING 5:** T02 Analysis §1 measures tie-rate + handles the 489 duplicate `(game_id, profile_id)` rows explicitly before dropping anything.
- **WARNING 6:** T02 Verdict cell specifies stratification-conflict rule: PASS iff (a) pooled gate passes AND (b) every leaderboard stratum passes at ≥ 0.90 (relaxed for sub-strata) AND (c) every time-gap-bucket passes at ≥ 0.90.
- **WARNING 7:** Gate Condition adds catastrophic-fail HALT: `agreement_rate < 0.80` → executor halts; user decision required.
- **NOTE 8:** T01 verifies `thesis/chapters/04_data_and_methodology.md §4.2.3` current content explicitly; T05 drops the unverified conditional.

Symmetric 1-revision cap consumed.

## Problem Statement

`INVARIANTS.md §3 line 76` states: "`old_rating` is PRE-GAME by schema inference: Classified PRE-GAME based on column semantics (pre-match rating). Formal bivariate temporal leakage test deferred to Phase 02." This is structural inference via the `matches_1v1_clean.yaml:excluded_columns` block (which excludes `new_rating`/`p*_new_rating` as POST-GAME), but not a direct empirical test.

The deferred empirical test: for consecutive matches t, t+1 of the same `profile_id` **on the same leaderboard** (critical: AoE2 ratings are per-leaderboard independent systems), `players_raw.old_rating[t+1]` should equal `players_raw.new_rating[t]`. High agreement confirms API honors the convention and `old_rating` IS the pre-match state; failure indicates either API semantics differ, ratings are reset/recomputed between matches for unrelated reasons, or the convention does not hold.

`old_rating` is the primary AoE2 rating feature across the thesis. An examiner asking "how do you know `old_rating` at match t isn't the rating AFTER match t?" currently has only a structural answer (VIEW exclusion); this step produces the conclusive empirical answer or surfaces a disconfirming finding.

## Assumptions & unknowns

- **Assumption (ratings are per-leaderboard, not global):** AoE2 ranked ladders are independent rating systems. The empirical test MUST partition by `(profile_id, leaderboard)`. A naive global `ORDER BY started_timestamp` across leaderboards yields cross-leaderboard pairs whose disagreement is a feature of independent rating systems, not an API convention violation.
- **Assumption (`new_rating` exists in `players_raw`):** T01 verifies; halts if absent.
- **Assumption (temporal anchor is `started_timestamp` TIMESTAMPTZ):** per `02_00_feature_input_contract.md §3.2` aoestats row.
- **Assumption (`profile_id` is DOUBLE in `players_raw`):** per INVARIANTS §1; DS-AOESTATS-IDENTITY-04 requires `CAST(. AS BIGINT)` before identity-keyed joins.
- **Assumption (integer ratings allow exact equality test):** Elo ratings in aoestats are stored as BIGINT; exact integer equality is well-defined. If storage is float, the test adopts a ±0.5 tolerance per match.
- **Unknown (tie-rate on `started_timestamp`):** measured in T02 §1; informs filter safety.
- **Unknown (the agreement rates themselves):** pooled + per-leaderboard + per-time-gap-bucket. Hypothesis: all ≥ thresholds. Falsifier: any threshold violated.
- **Unknown (outcome of FAIL path):** 3 follow-up candidates listed in §Open questions; decision deferred.

## Literature context

- `.claude/scientific-invariants.md` I3 (temporal; the test enforces strict-prior via LAG), I6 (SQL verbatim), I7 (thresholds must be argued or cited).
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md §3` line 76 — the deferral flag being closed.
- `reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md §3` — aoestats WARNING 2.
- `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_1v1_clean.yaml:excluded_columns` — structural evidence.
- DS-AOESTATS-02 (NULLIF cleaning-loss tolerance ~0.03%) + DS-AOESTATS-IDENTITY-04 (profile_id CAST) — aoestats-specific decision records; grounding for threshold argument.

## Execution Steps

### T01 — Verify raw-schema + thesis context

**Objective:** Before running the empirical test: (a) confirm `old_rating`, `new_rating`, `started_timestamp`, `profile_id`, `game_id` exist in the expected raw tables; (b) confirm `leaderboard` is in `matches_raw`; (c) verify `thesis/chapters/04_data_and_methodology.md §4.2.3` current language around `old_rating` PRE-GAME classification so T05's thesis-mapping note is grounded in fact.

**Instructions:**
1. Read `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/players_raw.yaml` — confirm presence of: `old_rating`, `new_rating`, `started_timestamp` (TIMESTAMPTZ), `profile_id` (DOUBLE), `game_id`.
2. Read `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw/matches_raw.yaml` — confirm presence of: `leaderboard`, `game_id`.
3. Read `thesis/chapters/04_data_and_methodology.md §4.2.3` — record the current statements about `old_rating` PRE-GAME classification. T05's research_log entry will reference (or not) §4.2.3 based on what is actually there.
4. If ANY schema column is missing, HALT and report. If §4.2.3 doesn't invoke `old_rating` at all, T05's thesis-mapping note drops the conditional — no thesis Pass-2 item required.

**Verification:**
- Executor notes confirm all columns exist.
- §4.2.3 content quoted in notes for T05 reference.

**File scope:** None (read-only).
**Read scope:** yaml schemas + `thesis/chapters/04_data_and_methodology.md`.

---

### T02 — Write sandbox notebook `01_04_06_old_rating_temporal_audit.py`

**Objective:** Leaderboard-partitioned consecutive-match temporal consistency test with all methodology revisions applied.

**Instructions:**
1. Create `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_06_old_rating_temporal_audit.py` (jupytext auto-pairs `.ipynb`).
2. Notebook structure:
   - **Header cell:** step description, hypothesis, falsifier, I6 discipline note. (No 01_05 spec-binding line — this is 01_04 scope; hook glob is `05_temporal_panel_eda/*.py` only, confirmed.)
   - **Hypothesis block (post-Mode-A revision):**
     - "H0: On `leaderboard = 'random_map'` (primary), for consecutive matches t, t+1 of the same `profile_id` ordered by `started_timestamp`, `players_raw.old_rating[t+1] == players_raw.new_rating[t]` at `agreement_rate ≥ 0.95` AND `max(|old_rating[t+1] − new_rating[t]|) < 50 rating units`. Per-leaderboard strata pass at ≥ 0.90. Per-time-gap-bucket strata pass at ≥ 0.90."
     - Falsifier: any gate fails → FAIL. Catastrophic fail: `agreement_rate < 0.80` → HALT, escalate to user.
     - Threshold argument (I7): 5% disagreement ceiling exceeds DS-AOESTATS-02's ~0.03% NULLIF cleaning-loss tolerance by 2 orders of magnitude. Disagreement below 5% is below the dataset's established classification-error tolerance; above 5% means the PRE-GAME classification is materially unsound. The 50-rating-unit disagreement magnitude is chosen as the approximate scale of typical Elo swings per game (Elo K=20–40); larger gaps indicate systematic drift beyond per-match Elo updates.
   - **Setup cell:**
     - DuckDB connection.
     - Schema validation: assert `players_raw` has all required columns; assert `matches_raw` has `leaderboard` + `game_id`.
     - **CAST discipline per DS-AOESTATS-IDENTITY-04:** define `profile_id_i64 := CAST(profile_id AS BIGINT)` in the CTE before any partition-key use.
   - **Analysis §1 — Tie-rate + duplicate-row pre-flight:**
     - SQL: count ties on `(profile_id_i64, leaderboard, started_timestamp)`; count rows per `(game_id, profile_id)` (expected 489 duplicates per INVARIANTS §1; verify).
     - Report tie rate. If > 1%, flag in output and revise filter strategy (halt or relax).
     - Document duplicate-handling: use `DISTINCT (game_id, profile_id_i64)` in the CTE to collapse the 489 duplicates to 1 row each.
   - **Analysis §2 — Pair construction (leaderboard-partitioned):**
     - CTE: `players_raw JOIN matches_raw USING (game_id)` to expose `leaderboard`.
     - Window: `LAG(new_rating) OVER (PARTITION BY profile_id_i64, leaderboard ORDER BY started_timestamp, game_id)` AS `prev_new_rating`; also LAG `started_timestamp` as `prev_started_timestamp`.
     - Filter: drop rows where `prev_new_rating IS NULL` (first match of each (player, leaderboard) sequence); drop rows in tied `started_timestamp` pairs if tie rate < 1% or use `(started_timestamp, game_id)` ordering otherwise.
     - Output pair count overall + per leaderboard.
     - **Scope:** primary test runs on `leaderboard = 'random_map'` subset. Per-leaderboard stratification returns separate agreement rates for each distinct leaderboard.
   - **Analysis §3 — Agreement + disagreement-magnitude:**
     - Compute: `agreed := (old_rating == prev_new_rating)` per pair; `disagreement_abs := ABS(old_rating - prev_new_rating)` per pair.
     - Aggregate primary scope (`random_map`): `agreement_rate`, `max_disagreement`, `median_disagreement_among_disagreeing_pairs`.
     - 95% Wilson binomial CI on agreement_rate (DuckDB computed or Python `scipy.stats.binomtest.proportion_ci`).
   - **Analysis §4 — Stratification (per leaderboard + per time-gap bucket):**
     - Per leaderboard: `agreement_rate` + pair count per distinct leaderboard.
     - Per time-gap bucket: `time_gap := started_timestamp - prev_started_timestamp`; bucket into `{<1d, 1-7d, 7-30d, >30d}`; compute `agreement_rate` per bucket.
     - Stratification-conflict resolution: overall PASS requires ALL strata ≥ 0.90.
   - **Verdict cell (post-Mode-A stratification-conflict rule):**
     - PASS iff ALL: (a) primary scope `agreement_rate ≥ 0.95` AND `max_disagreement < 50`; (b) every leaderboard stratum `agreement_rate ≥ 0.90`; (c) every time-gap-bucket `agreement_rate ≥ 0.90`.
     - MARGINAL if ONLY the `≥ 0.95` primary threshold is violated but all other gates pass; i.e., primary rate ∈ [0.90, 0.95).
     - FAIL otherwise.
     - CATASTROPHIC_HALT if primary `agreement_rate < 0.80`: print HALT notice; do NOT export artifacts; user escalation required.
   - **Artifact export cell:** write JSON + MD (skipped if CATASTROPHIC_HALT).
3. Iterate per `feedback_notebook_iterative_testing.md`.
4. Use `print()` for exploratory output; `logger` for terse diagnostics.

**Verification:**
- Notebook runs end-to-end.
- Verdict cell shows PASS/MARGINAL/FAIL/CATASTROPHIC_HALT with per-gate breakdown.
- JSON + MD produced (unless CATASTROPHIC_HALT).
- CAST discipline applied explicitly.
- Tie-rate + duplicate-rows counted.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_06_old_rating_temporal_audit.py` (Create)
- `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_06_old_rating_temporal_audit.ipynb` (Create)

**Read scope:** `players_raw`, `matches_raw` VIEWs; `INVARIANTS.md §3`.

---

### T03 — Write artifact MD + JSON

**Objective:** Persist analysis outputs (skipped if CATASTROPHIC_HALT from T02).

**Instructions:**
1. Write `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_06_old_rating_temporal_audit.md`:
   - **§1 Scope and method** — hypothesis + 3-gate falsifier + HALT threshold.
   - **§2 SQL verbatim (I6)** — all SQL blocks including CAST discipline + leaderboard-partitioned LAG + stratification.
   - **§3 Results** — primary scope agreement + max disagreement + Wilson CI + per-leaderboard table + per-time-gap-bucket table.
   - **§4 Verdict** — PASS/MARGINAL/FAIL per 3-gate breakdown.
   - **§5 Interpretation** — verdict-conditional prose:
     - PASS: "API honors the old/new-rating convention on `random_map` (primary) with consistent behavior across all leaderboards. Structural evidence (`matches_1v1_clean.yaml:excluded_columns`) + empirical evidence (this step) close the §3 deferral flag."
     - MARGINAL: primary scope ∈ [0.90, 0.95) — retain PRE-GAME classification but with explicit caveat; thesis §4.2.3 should hedge.
     - FAIL: explicit disagreement pattern + 3 follow-up candidates recorded.
2. Write `01_04_06_old_rating_temporal_audit.json`:
   - Fields: `n_pairs_primary_scope` (int), `n_pairs_total_all_leaderboards` (int), `agreement_rate_primary` (float), `max_disagreement_primary` (int — rating units), `wilson_ci_95_low` (float), `wilson_ci_95_high` (float), `per_leaderboard_agreement` (dict — `{leaderboard: agreement_rate}`), `per_time_gap_agreement` (dict — `{bucket: agreement_rate}`), `tie_rate` (float), `duplicate_rows_collapsed` (int), `verdict` (string — "PASS" | "MARGINAL" | "FAIL" | "CATASTROPHIC_HALT"), `hypothesis_thresholds` (object — `{agreement_primary_min: 0.95, max_disagreement_max: 50, stratum_min: 0.90, catastrophic_halt_min: 0.80}`), `threshold_rationale` (string — "DS-AOESTATS-02 2-order-of-magnitude factor over 0.03% NULLIF tolerance; 50 rating unit approximate Elo K=40 scale"), `ci_method` ("wilson"), `audit_date` (ISO).

**Verification:** both files exist; MD §2 has SQL verbatim; JSON parses; §5 matches verdict.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_06_old_rating_temporal_audit.md` (Create)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_06_old_rating_temporal_audit.json` (Create)

**Read scope:** T02 output.

---

### T04 — Update `INVARIANTS.md §3`

**Objective:** Replace the deferral with structural + empirical evidence (or hedge per FAIL).

**Instructions:**
1. Edit `INVARIANTS.md` line 76.
2. PASS replacement: "**`old_rating` is PRE-GAME (structural + empirical evidence):** Classified PRE-GAME. **Structural evidence:** `matches_1v1_clean.yaml:excluded_columns` excludes `new_rating`/`p*_new_rating` as POST-GAME. **Empirical evidence (01_04_06, 2026-04-21):** on `leaderboard='random_map'` primary scope, consecutive-match test confirms `players_raw.old_rating[t+1] == players_raw.new_rating[t]` at rate `<AGREEMENT>` (Wilson 95% CI [`<CI_LOW>`, `<CI_HIGH>`], n=`<N_PAIRS>` pairs; max disagreement `<MAX_DIS>` rating units). Per-leaderboard stratification: all leaderboards ≥ `<MIN_STRATUM>`. Per-time-gap: all buckets ≥ `<MIN_BUCKET>`. Deferred-test flag closed. (01_03_01 + 01_04_06)"
3. MARGINAL: retain language + explicit caveat sentence + Pass-2 §4.2.3 hedge target.
4. FAIL: retain the "classification is structurally PRE-GAME but empirically uncertain" hedge + name the 3 follow-up candidates.
5. Fill placeholders from T03 JSON.

**Verification:**
- `grep "01_04_06"` returns new citation.
- "deferred to Phase 02" language removed (PASS path) or converted to closure narrative (MARGINAL/FAIL).
- No `<PLACEHOLDER>` strings.

**File scope:** `INVARIANTS.md` (Update).
**Read scope:** T03 JSON.

---

### T05 — Append research_log entry

**Objective:** Document step.

**Instructions:**
1. Prepend entry to `research_log.md`.
2. Sub-sections: Date, Category (D), Dataset (aoestats), Step scope, Artifacts produced, What, Why, How (notebook + SQL + I6 + CAST discipline + leaderboard-partition), Findings (primary agreement + stratification + tie rate + duplicate handling), Decisions taken (verdict), Decisions deferred (FAIL path 3 candidates, if applicable), Thesis mapping (only if T01 confirmed §4.2.3 invokes `old_rating` PRE-GAME; otherwise drop), Open questions.

**Verification:** entry present; sub-sections populated; no unverified conditional on §4.2.3.

**File scope:** `research_log.md` (Update).
**Read scope:** T03 artifacts + T01 §4.2.3 notes.

---

### T06 — Version bump + CHANGELOG

**Objective:** Version 3.41.0 → 3.41.1 (patch, fix).

**Instructions:**
1. `pyproject.toml`: `version = "3.41.0"` → `version = "3.41.1"`.
2. `CHANGELOG.md`: move `[Unreleased]` aside; add `[3.41.1] — 2026-04-21 (PR #TBD: fix/aoestats-old-rating-pregame-closure)`:
   - `### Fixed`: aoestats `old_rating` PRE-GAME classification empirical closure via 01_04_06 leaderboard-partitioned consecutive-match test (primary scope `random_map`, stratification across all leaderboards + time-gap buckets). CAST discipline per DS-AOESTATS-IDENTITY-04. Threshold argument per DS-AOESTATS-02 tolerance. `INVARIANTS.md §3` "deferred to Phase 02" flag closed. Closes aoestats WARNING 2 from `phase01_audit_summary_2026-04-21.md §3`.
3. Reset `[Unreleased]`.

**Verification:** pyproject 3.41.1; CHANGELOG populated.

**File scope:** `pyproject.toml`, `CHANGELOG.md`.

---

## File Manifest

| File | Action |
|------|--------|
| `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_06_old_rating_temporal_audit.py` | Create |
| `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_06_old_rating_temporal_audit.ipynb` | Create (jupytext) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_06_old_rating_temporal_audit.md` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_06_old_rating_temporal_audit.json` | Create |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md` | Update |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md` | Update |
| `pyproject.toml` | Update |
| `CHANGELOG.md` | Update |
| `planning/current_plan.md` | (this plan; tracked separately) |
| `planning/current_plan.critique.md` | (Mode A) |

8 git-diff-scope files (4 new + 4 modified) + 2 planning meta.

## Gate Condition

- Notebook runs end-to-end; verdict PASS/MARGINAL/FAIL explicit. CATASTROPHIC_HALT prevents artifact export and requires user decision.
- MD + JSON with all prescribed fields; no `<PLACEHOLDER>` strings.
- INVARIANTS.md §3 updated per verdict branch.
- research_log.md entry complete.
- pyproject 3.41.1; CHANGELOG [3.41.1] populated.
- **3-gate PASS (argued per I7):**
  - `agreement_rate_primary ≥ 0.95` (random_map scope): 2 orders of magnitude above DS-AOESTATS-02's 0.03% NULLIF cleaning-loss tolerance.
  - `max_disagreement_primary < 50` rating units: Elo K=40 per-match scale; larger disagreements indicate systematic drift beyond expected per-match updates.
  - Every leaderboard stratum AND every time-gap bucket ≥ 0.90 (relaxed for sub-strata to accommodate smaller n).
- **CATASTROPHIC_HALT:** `agreement_rate_primary < 0.80` → executor HALTs; PR does not proceed; user decision required (likely WP-4 redesign).
- `git diff --stat` touches exactly 8 files + planning meta.

## Out of scope

- Phase 02 rating-feature-engineering — Phase 02 planner-science.
- Analogous tests for sc2egset / aoe2companion — different I2 / rating semantics.
- Thesis §4.2.3 prose update — Pass-2; this plan produces evidence only.
- VIEW schema changes or `excluded_columns` modifications.
- Demotion of `old_rating` if FAIL — decision recorded only; execution deferred.
- Full literature review of Elo update semantics — we cite DS-AOESTATS internal records only.

## Open questions

- **Q1 (resolved):** Thresholds — 0.95 primary + 0.90 strata + 50-unit max + 0.80 HALT. Arguments recorded.
- **Q2 (deferred to verdict):** FAIL follow-up candidates — retain with caveat, demote to CONDITIONAL_PRE_GAME, filter investigation. Decision tree: agreement ∈ [0.90, 0.95) → caveat; [0.80, 0.90) → demote; <0.80 → HALT (already in Gate Condition).
- **Q3 (resolved):** Leaderboard scope — primary `random_map`, stratification across all leaderboards.
- **Q4 (deferred to T02):** Exact tie-rate on `(profile_id, leaderboard, started_timestamp)` — measured in §1.
- **Q5 (deferred to T01):** §4.2.3 thesis content verification — T01 reads; T05 drops conditional if §4.2.3 doesn't invoke `old_rating` PRE-GAME.

## Dispatch sequence

1. This plan written at `planning/current_plan.md` on branch `fix/aoestats-old-rating-pregame-closure`.
2. `reviewer-adversarial` Mode A invoked 2026-04-21 — verdict REVISE with 2 BLOCKERs + 5 WARNINGs + 3 NOTEs. **Revision round applied 2026-04-21:** all 8 findings addressed (leaderboard partition + CAST discipline + decision-theoretic threshold + disagreement-magnitude gate + tie-rate measurement + stratification-conflict rule + HALT threshold + thesis §4.2.3 verification). Critique preserved at `planning/current_plan.critique.md`. Symmetric 1-revision cap consumed.
3. Executor dispatched with T01–T06.
4. `reviewer-deep` post-execution review (Cat D default per CLAUDE.md).
5. Pre-commit (ruff/mypy N/A; planning-drift passes; jupytext sync fires).
6. Commit + PR + merge.
7. Post-merge: next plan (WP-5) overwrites.
