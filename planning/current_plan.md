---
category: A
branch: feat/sc2egset-cross-region-history-impact
date: 2026-04-21
planner_model: claude-opus-4-7
dataset: sc2egset
phase: "01"
pipeline_section: 01_05
invariants_touched: [I2, I3, I6, I7]
source_artifacts:
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_04b_worldwide_identity.md
  - reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_history_all.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/matches_history_minimal.yaml
  - reports/specs/02_00_feature_input_contract.md
  - .claude/scientific-invariants.md
critique_required: true
research_log_ref: src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md#2026-04-21-cross-region-history-impact
---

# Plan: WP-3 — sc2egset cross-region history-fragmentation quantification (REVISED 2026-04-21 post Mode A)

## Scope

Quantify the empirical impact of the ~12% cross-region player fragmentation (accepted bias under I2 Branch iii, `INVARIANTS.md §2`) on **Phase 02 rolling-window history features**. Closes sc2egset WARNING 3 from the 2026-04-21 Phase 01 sign-off sweep (`phase01_audit_summary_2026-04-21.md §2`): "For the 12% of cross-region cases, by how many games is the history underestimated, and is this correlated with skill level?"

Scope is bounded: one new notebook step at `01_05_10` that executes per-(player, match) rolling-window undercount measurements on existing cleaned tables (no raw-data re-processing, no new VIEW creation), produces one MD + one JSON artifact, extends `INVARIANTS.md §2` with measured numbers + graded thesis-defensibility paragraphs, and logs the step in `research_log.md`. No code outside `sandbox/`, `reports/artifacts/`, and the two docs.

**Post-Mode-A revision summary (2026-04-21):** Mode A adversarial critique surfaced 3 BLOCKERs + 3 WARNINGs + 3 NOTEs. Revisions applied within symmetric 1-revision cap:
- **BLOCKER-1:** Primary measurement switched from static lifetime undercount to per-(cross-region player, match) rolling-window undercount at window=30 (primary) + sensitivity across {5, 10, 30, 100}. Lifetime aggregate retained as descriptive context only, explicitly framed as loose upper bound.
- **BLOCKER-2:** MMR correlation threshold raised from `|ρ| < 0.1` to `|ρ| < 0.2` with n≈200 power calculation verbatim in notebook; bootstrap 95% CI on ρ (n_bootstrap=1000) reported alongside point estimate for graded interpretation.
- **BLOCKER-3:** Gate Condition adds `p95_rolling30_undercount ≤ 5` alongside `median_rolling30_undercount ≤ 1`; PASS requires BOTH. K=5 argued as below the rolling-30 feature's √n=5.5 measurement noise.
- **WARNING-4:** Gate "Threshold derivation" rewritten: thresholds argued against rolling-feature noise floor (concrete reference), with sensitivity report across {5, 10, 30, 100} windows for robustness.
- **WARNING-5:** T01 drift tolerance removed; current count recorded authoritatively with INVARIANTS.md supersede if drift detected.
- **WARNING-6:** T03 §5 emits three pre-drafted paragraphs (clean PASS / marginal / FAIL) for Pass-2 thesis incorporation.
- **NOTE-7:** DuckDB `PERCENTILE_CONT` prescribed as percentile engine for all JSON percentile fields; pandas used only for Spearman + bootstrap.
- **NOTE-8:** "Rare-handle" subsample analysis added (nickname length ≥ 8) to control for within-region handle-collision confound per INVARIANTS.md §2 30.6% collision rate.
- **NOTE-9:** Dispatch sequence acknowledges 2-session execution budget (session 1: T01+T02 hypothesis iteration; session 2: T03–T07 wrap-up).

Symmetric 1-revision cap consumed.

## Problem Statement

`INVARIANTS.md §2` records ~12% cross-region duplication (246 case-sensitive nicknames spanning multiple regions). For these 246 players, Phase 02 rolling-window features (e.g., `rolling_win_rate_past_30_games`, `past_match_count`) computed per `player_id_worldwide` (Branch iii) split the player's prefix-history across region-specific keys.

**Refined post-Mode-A framing:** The relevant bias is NOT the lifetime undercount (a player with 100 lifetime games split 50/50 has a 50-game total difference, but at their 25th EU match their rolling feature is correctly over their first 24 EU games regardless of what happens later in NA). The relevant bias is **per-(player, match) rolling-window undercount**: at match T, player X's rolling-30 feature under `player_id_worldwide` sees at most 30 prior EU games; under a hypothetical nickname-unified key, it would see up to 30 prior games across all regions. The undercount is `min(30, unified_prior) − min(30, player_id_worldwide_prior)`, per match T.

Three open risks — each addressable by this step's measurements:

1. **Bias magnitude (per-match rolling-window):** at window=30, what is the median and p95 undercount across all (cross-region player, match) pairs? If the median is 0 and p95 is ≤ noise-floor, Phase 02 features are reliable. If p95 is materially large, 5% of cross-region (player, match) pairs produce biased rolling features.
2. **Bias direction (MMR correlation):** is the fragmentation ratio (max regional games / total nickname games, lifetime scope — this stays a lifetime quantity because MMR is per-player not per-match) correlated with skill? Correlation estimated with bootstrap 95% CI (n_bootstrap=1000) at raised threshold `|ρ| < 0.2` (powered test at n≈200).
3. **Handle-collision confound:** INVARIANTS.md §2 notes 30.6% within-region handle-collision rate. Some cross-region nicknames are DIFFERENT physical players (common handles like "Zerg"). Rare-handle subsample (length ≥ 8) controls for this confound.

Examiner-grade question from WARNING 3 is answered quantitatively. §5 thesis-implication paragraph is pre-drafted for three verdict branches (clean PASS / marginal / FAIL) to give the Pass-2 drafter a defensible rewriting base.

## Assumptions & unknowns

- **Assumption (246 cross-region nicknames is current):** T01 re-runs the identifying SQL and records the current count authoritatively; if drift is detected, INVARIANTS.md §2 is superseded in this PR (no arbitrary tolerance per I7).
- **Assumption (player_history_all is the right table):** per `02_00_feature_input_contract.md §3.2` (CROSS-02-00-v1), the sc2egset per-dataset anchor columns are `toon_id` + `details_timeUTC` VARCHAR. The rolling-window SQL uses `details_timeUTC` as the temporal anchor after canonical TIMESTAMP cast (matches_history_minimal exposes `started_at` TIMESTAMP which is `CAST(details_timeUTC AS TIMESTAMP)`; these agree per INVARIANTS.md §1 "Temporal range: started_at ... via TRY_CAST of details.timeUTC; zero TRY_CAST failures").
- **Assumption (MMR skill proxy):** `MMR` in `player_history_all` = 0 is sentinel "not reported" (83.65% rate per INVARIANTS.md §1). MMR > 0 defines the skill-stratifiable subset. Players with zero non-sentinel MMR across their matches are dropped from §4 MMR analysis but retained in §1–§3 rolling-window analyses.
- **Assumption (30-game primary window):** window=30 is the primary analysis; sensitivity report spans {5, 10, 30, 100}. Thirty is selected as reasonable-middle for Phase 02 rolling features (not as Phase 02 commitment); sensitivity across 4 windows makes the verdict robust to this choice.
- **Unknown (the measurements themselves):** 5 quantities produced empirically — `median_rolling30_undercount`, `p95_rolling30_undercount`, `fragmentation_ratio_median_lifetime`, `mmr_spearman_rho_point`, `mmr_spearman_rho_bootstrap_ci_upper`. No a-priori prediction. Sensitivity across windows adds 6 more quantities (median + p95 at 5/10/100).
- **Unknown (follow-up scope if FAIL):** recorded in research_log T06 only if verdict is FAIL; scope candidates enumerated in §Open questions.

## Literature context

Not applicable at thesis-citation level — internal empirical step. Reference materials:

- `.claude/scientific-invariants.md` I2 (identity branch discipline), I3 (temporal: rolling-window uses strict `<`), I6 (SQL verbatim in artifacts), I7 (no magic numbers; thresholds argued against rolling-feature noise floor).
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md §2` — the statement this step quantifies.
- `reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md §2 WARNING 3` — the audit finding closed by this step.
- `reports/specs/02_00_feature_input_contract.md §3.2` — per-dataset PH anchor + ID definitions used in the rolling-window SQL.
- Spearman rank correlation power: Hollander & Wolfe (1999) Table 11.2 — |ρ|=0.2 at n=200 gives ~80% power at α=0.05 two-sided; |ρ|=0.1 at n=200 gives ~30% power (cited in notebook for BLOCKER-2 resolution rationale).

## Execution Steps

### T01 — Confirm cross-region nickname count authoritatively

**Objective:** Re-run the INVARIANTS.md §2 cross-region nickname SQL on current `replay_players_raw`. Record the authoritative count (no ±tolerance — whatever the current count is becomes the baseline; INVARIANTS.md §2 is superseded by this PR if the 246 figure has drifted).

**Instructions:**
1. Open the notebook (T02 creates it).
2. Execute SQL verbatim from INVARIANTS.md §2 lines 40–47 (cross-region nickname detection).
3. Record current count. Compare to the claimed 246. If drift detected, flag prominently in the notebook output; T05 INVARIANTS.md update supersedes the 246 with the current count.
4. Save the cross-region-nicknames list to a DuckDB temp table or Python DataFrame for reuse in T02 downstream analyses.

**Verification:**
- Notebook cell output shows the SQL result.
- If count ≠ 246: INVARIANTS.md §2 update in T05 supersedes with current count + date.
- SQL stored verbatim per I6.

**File scope:** None (notebook prep).
**Read scope:** `replay_players_raw`, `INVARIANTS.md §2`.

---

### T02 — Write sandbox notebook (multi-session-aware; hypothesis-driven iteration)

**Objective:** Produce `sandbox/sc2/sc2egset/01_exploration/05_temporal_panel_eda/01_05_10_cross_region_history_impact.py` (jupytext-paired). The notebook covers 5 analysis sections + verdict + artifact export. **This task may span a full session of iterative SQL debugging per `feedback_notebook_iterative_testing.md`.**

**Instructions:**
1. Create the jupytext-paired notebook.
2. Notebook structure (human-readable section names; NO plan codes per `feedback_no_plan_codes_in_docs.md`):
   - **Header:** step description; I6 SQL-verbatim discipline note; 2-session budget note (this task + artifacts + logs).
   - **Hypothesis block (updated post-Mode A):**
     - H0: cross-region fragmentation produces negligible per-match rolling-window bias in Phase 02 features, i.e., `median_rolling30_undercount ≤ 1 game` AND `p95_rolling30_undercount ≤ 5 games` (below √30 ≈ 5.5 feature-noise floor) AND `|bootstrap_CI_upper(mmr_spearman_rho)| < 0.2` (powered falsifier at n≈200).
     - Falsifier: any of the three thresholds violated triggers FAIL verdict.
     - Rationale for K=5 (p95): the rolling-30 feature's own measurement noise at a fixed win-rate p is bounded by `√(p(1-p)/30) ≈ 0.09` relative, i.e., ~2.7 games at p=0.5; the √n=5.5 heuristic is conservatively liberal.
     - Rationale for |ρ|<0.2: at n=200 (~246 minus MMR filter), this threshold has ~80% power at α=0.05 two-sided per Hollander & Wolfe §11.2 tables.
   - **Setup:** DuckDB connection, schema validation.
   - **Analysis §1 — Cross-region nickname identification (T01 output):** Re-run the SQL from INVARIANTS.md §2. Print count + first 10 nicknames.
   - **Analysis §2 — Lifetime fragmentation ratio (descriptive context; NOT primary metric):** For each cross-region nickname, compute `fragmentation_ratio = max(games_per_region) / total_games` across all regions. Report distribution: median, p25, p75, p95. Label clearly as "lifetime aggregate — loose upper bound on Phase 02 bias; per-match rolling-window bias is the primary measurement in §3."
   - **Analysis §3 — PRIMARY: Per-(player, match) rolling-window undercount at window=30:**
     - For each match M of each cross-region player, compute:
       - `ph_prior_at_M`: number of prior games (strict `<` on `details_timeUTC`) of that `player_id_worldwide` in `player_history_all`.
       - `unified_prior_at_M`: number of prior games of that nickname (all regions combined) in `player_history_all`.
       - `rolling30_undercount_at_M = min(30, unified_prior_at_M) - min(30, ph_prior_at_M)`.
     - Aggregate across all (cross-region player, match) pairs:
       - `median_rolling30_undercount` via DuckDB `PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY rolling30_undercount_at_M)`.
       - `p95_rolling30_undercount` via DuckDB `PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY rolling30_undercount_at_M)`.
       - Distribution histogram for visual inspection.
   - **Analysis §4 — Sensitivity sweep across windows {5, 10, 30, 100}:** Rerun Analysis §3's undercount SQL with windows 5, 10, 100. Report `median_rolling<W>_undercount` + `p95_rolling<W>_undercount` for each W. Per-window sensitivity table in the MD artifact.
   - **Analysis §5 — MMR stratification (with bootstrap CI):**
     - Compute per-player median MMR from non-sentinel MMR values.
     - Compute per-player lifetime fragmentation ratio (from §2).
     - Spearman ρ point estimate between median-MMR and fragmentation-ratio, restricted to players with ≥1 non-sentinel MMR.
     - Bootstrap 95% CI (n_bootstrap=1000, per-player resample) on ρ using pandas + scipy.stats.bootstrap.
     - Include power-calculation commentary: at achieved n, what is the detectable |ρ| at α=0.05 two-sided 80% power?
   - **Analysis §6 — Rare-handle subsample (handle-collision control):** Re-run §3 (primary rolling-window metric at window=30) and §5 (MMR-Spearman) restricted to cross-region nicknames with `LENGTH(nickname) ≥ 8`. Report same fields; compare to full-sample. If rare-handle subsample significantly differs, the full-sample result is contaminated by within-region handle-collision (different physical players sharing a nickname).
   - **Verdict cell:**
     - Apply 3-threshold gate: PASS iff ALL of (a) `median_rolling30_undercount ≤ 1` AND (b) `p95_rolling30_undercount ≤ 5` AND (c) `|bootstrap_CI_upper(mmr_spearman_rho)| < 0.2`.
     - Between-PASS-and-FAIL: MARGINAL verdict if ≥1 threshold is violated but by < 50% (soft-border region).
     - Print verdict + per-threshold pass/fail table.
   - **Artifact export cell:** write JSON + MD to `reports/artifacts/01_exploration/05_temporal_panel_eda/`.
3. Iterate cell-by-cell per `feedback_notebook_iterative_testing.md` — state hypothesis + falsifier up front, read every output, revise if unexpected; do NOT rubber-stamp.
4. Use `print()` for exploratory output, `logger` only for terse SQL-completion diagnostics.

**Verification:**
- Notebook runs end-to-end with no errors.
- Verdict cell shows PASS / MARGINAL / FAIL explicitly with per-threshold breakdown.
- JSON artifact parseable; all prescribed fields populated.
- Power-calibration commentary present.
- Rare-handle subsample result compared to full sample in a table.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/05_temporal_panel_eda/01_05_10_cross_region_history_impact.py` (Create)
- `sandbox/sc2/sc2egset/01_exploration/05_temporal_panel_eda/01_05_10_cross_region_history_impact.ipynb` (Create; jupytext auto-pair)

**Read scope:**
- `replay_players_raw`, `player_history_all` VIEWs.
- `INVARIANTS.md §2`.

---

### T03 — Write artifact MD + JSON

**Objective:** Persist analysis outputs to canonical artifact location.

**Instructions:**
1. Write `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/cross_region_history_impact_sc2egset.md`:
   - **§1 Scope and method** — what this artifact measures; hypothesis + 3-threshold falsifier verbatim from T02.
   - **§2 SQL verbatim (I6)** — all SQL blocks (nickname detection, fragmentation-ratio, per-match rolling-window undercount, sensitivity-windows, MMR-Spearman, bootstrap CI, rare-handle subsample). DuckDB `PERCENTILE_CONT` explicitly cited for percentile computation.
   - **§3 Results** — per-analysis-section tables + narrative. Window=30 primary table + {5, 10, 100} sensitivity table.
   - **§4 Verdict** — PASS / MARGINAL / FAIL per the 3-threshold gate; per-threshold breakdown.
   - **§5 Thesis implication (three pre-drafted paragraphs):**
     - **Clean PASS paragraph** — "At window=30, median undercount is `<MEDIAN>` game(s) and p95 is `<P95>` game(s), both below the rolling-30 feature's √30 ≈ 5.5 measurement noise floor. Bootstrap 95% CI on the MMR-fragmentation Spearman ρ is `[<LOW>, <HIGH>]`, within the `|ρ|<0.2` detectable-at-80%-power range, so fragmentation is not materially correlated with skill. The I2 Branch (iii) accepted-bias framing is quantitatively defended — the 12% cross-region duplication produces Phase 02 rolling-feature bias indistinguishable from the feature's own measurement noise."
     - **MARGINAL paragraph** — "At window=30, some thresholds are close: `<break-down>`. The rolling-feature bias from cross-region fragmentation is at the edge of material, and Phase 02 implementations should flag cross-region players (`is_cross_region=TRUE` indicator) for sensitivity analysis; a full Cat D remediation PR is not required but is a defensible upgrade path."
     - **FAIL paragraph** — "At window=30, `<which thresholds>` are violated: `<numbers>`. Rolling-feature bias materially exceeds the feature's own noise floor and/or correlates with skill above the power-detectable threshold. The I2 Branch (iii) accepted-bias framing requires quantitative qualification in §4.2.2: either (a) Phase 02 must emit per-feature sensitivity analysis conditioned on `is_cross_region`, OR (b) the 294 Class A cross-region candidate pairs (INVARIANTS.md §2) must be manually curated and unified in a follow-up Cat D PR. A future revision to this file will record that decision."
   - **§6 Follow-up scope (FAIL only)** — Cat D candidates enumerated if applicable.
2. Write `cross_region_history_impact_sc2egset.json`:
   - Primary fields: `n_cross_region_nicknames` (int), `median_rolling30_undercount_games` (float), `p95_rolling30_undercount_games` (float), `fragmentation_ratio_median_lifetime` (float), `mmr_spearman_rho_point` (float or null), `mmr_spearman_rho_bootstrap_ci_low` (float or null), `mmr_spearman_rho_bootstrap_ci_high` (float or null), `n_bootstrap` (int = 1000), `n_players_with_mmr` (int).
   - Sensitivity fields: `sensitivity_windows` = dict `{5: {median: float, p95: float}, 10: {...}, 30: {...}, 100: {...}}`.
   - Rare-handle subsample fields: `rare_handle_subsample` = dict `{n_players: int, median_rolling30_undercount: float, p95_rolling30_undercount: float, mmr_rho_point: float or null, mmr_rho_ci_low: float or null, mmr_rho_ci_high: float or null}`.
   - Verdict + thresholds: `verdict` (string — "PASS" / "MARGINAL" / "FAIL"), `hypothesis_thresholds` (object = `{median_rolling30_max: 1, p95_rolling30_max: 5, mmr_rho_ci_upper_abs_max: 0.2, window_primary: 30, sensitivity_windows: [5, 10, 30, 100]}`), `audit_date` (ISO = "2026-04-21"), `percentile_engine: "duckdb_PERCENTILE_CONT"`, `bootstrap_engine: "scipy.stats.bootstrap + pandas"`.
3. Apply the correct thesis-paragraph template (§5) based on the verdict — only ONE of {clean PASS / MARGINAL / FAIL} goes in §5; the other two are dropped from the final MD (or kept as commented-out alternatives). Executor judgment.

**Verification:**
- Both files exist at canonical path.
- MD §2 contains ≥6 SQL blocks.
- JSON parses; all named fields present.
- §5 thesis paragraph matches verdict.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/cross_region_history_impact_sc2egset.md` (Create)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/cross_region_history_impact_sc2egset.json` (Create)

**Read scope:** T02 notebook output.

---

### T04 — Update `INVARIANTS.md §2` with measured numbers

**Objective:** Replace qualitative accepted-bias statement with quantitative version referencing the 01_05_10 artifact.

**Instructions:**
1. Edit `src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md §2`.
2. Locate "Tolerance and accepted bias" paragraph. Preserve the current sentence; append a new one citing the 01_05_10 measurements:
   - Template: "Empirical impact on Phase 02 rolling-window features (01_05_10, 2026-04-21): at window=30, median undercount is `<MEDIAN>` games, p95 is `<P95>`; sensitivity at windows {5, 10, 100} shows `<qualitative description>`. MMR-fragmentation Spearman ρ = `<RHO>` (bootstrap 95% CI [`<LOW>`, `<HIGH>`], n=`<N_MMR>`). Verdict: `<VERDICT>` against 3-threshold gate (median_rolling30 ≤ 1 AND p95_rolling30 ≤ 5 AND |bootstrap_CI_upper(ρ)| < 0.2). Rare-handle subsample (nickname length ≥ 8, n=`<N_RARE>`) `<consistent/divergent>` with full sample. See `reports/artifacts/01_exploration/05_temporal_panel_eda/cross_region_history_impact_sc2egset.md`."
3. Placeholders filled from T03 JSON; no literal `<PLACEHOLDER>` strings remain.
4. If T01 detected count drift (new count ≠ 246), also supersede the "246 case-sensitive nicknames" figure in §2 with the current count + date "(updated 2026-04-21)".

**Verification:**
- `grep "01_05_10" src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md` returns the new citation.
- No `<PLACEHOLDER>` strings.
- Existing qualitative paragraph preserved; quantitative sentence APPENDED.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md` (Update)

**Read scope:**
- `cross_region_history_impact_sc2egset.json` (T03).

---

### T05 — Append research_log entry

**Objective:** Document the step per per-dataset-log protocol with all sub-sections.

**Instructions:**
1. Prepend new entry to `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` at the top of the reverse-chronological narrative.
2. Entry structure:
   - Date header: `## 2026-04-21 — [Phase 01 / Step 01_05_10] Cross-region history-fragmentation quantification`
   - **Category:** A (science).
   - **Dataset:** sc2egset.
   - **Step scope:** Phase 02 rolling-feature impact quantification.
   - **Artifacts produced:** MD + JSON (T03 paths); notebook (T02 path).
   - **What:** Per-(cross-region player, match) rolling-window undercount at window=30 (primary) + sensitivity {5, 10, 100} + MMR-fragmentation Spearman ρ with bootstrap 95% CI + rare-handle subsample.
   - **Why:** Closes sc2egset WARNING 3 (`phase01_audit_summary_2026-04-21.md §2`); produces thesis-citation-grade quantification for §4.2.2 Pass-2.
   - **How (reproducibility):** notebook `01_05_10`; SQL verbatim (I6); DuckDB PERCENTILE_CONT percentile engine; scipy bootstrap.
   - **Findings:** pull from T03 JSON — median_rolling30, p95_rolling30, bootstrap CI bounds, sensitivity at 5/10/100, rare-handle subsample consistency flag.
   - **Decisions taken:** verdict (PASS / MARGINAL / FAIL).
   - **Decisions deferred:** if FAIL → follow-up Cat D scope named (manual-curation unification OR `is_cross_region` flag in Phase 02); if PASS / MARGINAL → none (or brief thresholds-to-re-check note if MARGINAL).
   - **Thesis mapping:** §4.2.2 quantitative caveat addition; the §5 pre-drafted paragraph (from T03 MD) is the Pass-2 base.
   - **Open questions / follow-ups:** verdict-conditional.

**Verification:**
- New entry present at top of research_log.md.
- All required sub-sections populated.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` (Update)

**Read scope:** T03 artifacts.

---

### T06 — Version bump + CHANGELOG

**Objective:** Version 3.40.0 → 3.41.0 (minor; Phase 01 empirical extension).

**Instructions:**
1. Edit `pyproject.toml`: `version = "3.40.0"` → `version = "3.41.0"`.
2. Edit `CHANGELOG.md`: move `[Unreleased]` contents aside; add `[3.41.0] — 2026-04-21 (PR #TBD: feat/sc2egset-cross-region-history-impact)`:
   - `### Added`: New Phase 01 step 01_05_10 — sc2egset cross-region history-fragmentation impact; notebook + MD + JSON; closes sc2egset WARNING 3. Per-(player, match) rolling-window undercount at window=30 + sensitivity {5, 10, 100} + MMR-fragmentation Spearman ρ with bootstrap 95% CI + rare-handle subsample control. 3-threshold gate (median_rolling30 ≤ 1 AND p95_rolling30 ≤ 5 AND |bootstrap_CI_upper(ρ)| < 0.2).
   - `### Changed`: INVARIANTS.md §2 extended with quantitative impact + three-verdict graded thesis paragraphs; research_log.md new 01_05_10 entry.
3. Reset `[Unreleased]` to empty.

**Verification:**
- `pyproject.toml` `version = "3.41.0"`.
- `CHANGELOG.md` `[3.41.0]` populated.

**File scope:**
- `pyproject.toml` (Update)
- `CHANGELOG.md` (Update)

**Read scope:** None.

---

## File Manifest

| File | Action |
|------|--------|
| `sandbox/sc2/sc2egset/01_exploration/05_temporal_panel_eda/01_05_10_cross_region_history_impact.py` | Create |
| `sandbox/sc2/sc2egset/01_exploration/05_temporal_panel_eda/01_05_10_cross_region_history_impact.ipynb` | Create (jupytext) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/cross_region_history_impact_sc2egset.md` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/cross_region_history_impact_sc2egset.json` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md` | Update |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` | Update |
| `pyproject.toml` | Update |
| `CHANGELOG.md` | Update |
| `planning/current_plan.md` | (this plan; tracked separately) |
| `planning/current_plan.critique.md` | (produced by Mode A) |

8 git-diff-scope files (4 new + 4 modified) + 2 planning meta.

## Gate Condition

- Notebook runs end-to-end; verdict cell explicit PASS / MARGINAL / FAIL with per-threshold breakdown.
- MD + JSON artifacts exist with all prescribed fields (primary + sensitivity-windows + rare-handle + verdict + thresholds + engines).
- MD §5 thesis-implication paragraph matches the verdict (one of three pre-drafted).
- INVARIANTS.md §2 extended with filled-in numeric values; no `<PLACEHOLDER>` strings.
- research_log.md new entry with all sub-sections.
- pyproject.toml 3.41.0; CHANGELOG [3.41.0] populated; [Unreleased] reset.
- **3-threshold gate (argued, not invented per I7):**
  - `median_rolling30_undercount_games ≤ 1`: argued because at median, the Phase 02 rolling-30 feature's win-rate estimate is unaffected by ≤1-game prefix difference (dominant-term analysis: win-rate shift from 1 game among 30 is ≤ 3.3% absolute, below the typical 5–10% Phase 02 feature-signal threshold for a predictive contribution).
  - `p95_rolling30_undercount_games ≤ 5`: argued because √30 ≈ 5.5 is the feature's own measurement noise at win-rate p=0.5; p95 undercount below this level is statistically indistinguishable from feature noise.
  - `|bootstrap_CI_upper(mmr_spearman_rho)| < 0.2`: argued as the minimum detectable |ρ| at n≈200 for 80% power at α=0.05 two-sided (Hollander & Wolfe 1999 §11.2); lower thresholds are underpowered and pass vacuously.
- **Sensitivity robustness:** if window=30 verdict is PASS but {5, 10, 100} sensitivity reveals a window where either threshold is violated by > 50%, MARGINAL verdict instead (documented in T02 verdict cell).
- `git diff --stat` touches exactly 8 git-diff-scope files + planning meta.

## Out of scope

- **Cat D mitigation PR for cross-region identity unification** (if verdict FAIL) — separate PR; WP-3 only produces measurement + verdict + §5 pre-drafted paragraph.
- **Thesis §4.2.2 prose update** — Pass-2 Chat workflow or separate docs PR; WP-3 prepares §5 graded paragraphs in MD as input but does NOT edit `thesis/chapters/`.
- **Changes to any VIEW or cleaning rule** — measurement-only; schema changes are separate PRs.
- **Analogous quantification for aoestats / aoe2companion** — their I2 branches differ (v and i); "cross-region fragmentation" concept specific to sc2egset Branch (iii). Separate WPs if required.
- **Modifications to `02_00_feature_input_contract.md` or `02_01_leakage_audit_protocol.md`** — LOCKED specs.
- **Phase 02 rolling-window size commitment** — window=30 is primary analysis choice, NOT Phase 02 commitment. Phase 02 planner-science picks windows at 02_07.
- **Power-analysis generalisation beyond Spearman** — power calc for Spearman only per BLOCKER-2 fix; no other statistical tests added.

## Open questions

- **Q1 (resolved in Gate Condition):** PASS/FAIL thresholds — median_rolling30 ≤ 1, p95_rolling30 ≤ 5, |bootstrap_CI_upper(ρ)| < 0.2. Arguments recorded.
- **Q2 (deferred to verdict):** Follow-up Cat D scope if FAIL. Candidates: (a) manual-curation unification of 294 Class A cross-region candidate pairs; (b) Phase 02 `is_cross_region_fragmented` flag column for sensitivity analysis; (c) revised I2 branch. Recorded in research_log T05 only if FAIL.
- **Q3:** MMR-censored-data correction — resolved: analyze only ≥1-non-sentinel-MMR subset.
- **Q4 (new post-Mode-A):** If rare-handle subsample (§6) diverges substantially from full sample, does that imply the 246 figure is materially contaminated? — Report both side-by-side in artifact MD; let the Pass-2 thesis decide the framing.

## Dispatch sequence

1. This plan written at `planning/current_plan.md` on branch `feat/sc2egset-cross-region-history-impact`.
2. `reviewer-adversarial` Mode A invoked 2026-04-21 — verdict REVISE with 3 BLOCKERs + 3 WARNINGs + 3 NOTEs. **Revision round applied 2026-04-21:** all 9 findings addressed (per-match rolling-window metric, power-calibrated ρ threshold, p95 gate, sensitivity sweep, drift tolerance removed, graded thesis paragraphs, percentile engine, rare-handle subsample, 2-session budget). Critique preserved at `planning/current_plan.critique.md`. Symmetric 1-revision cap consumed.
3. **Execution budget: 2 sessions.** Session 1: T01 + T02 (hypothesis-driven notebook iteration). Session 2: T03–T06 (artifacts + INVARIANTS + log + version). Cat A notebook iteration per `feedback_notebook_iterative_testing.md` expects revision cycles in T02.
4. Executor dispatched with T01–T06 (may complete in 1 or 2 sessions depending on SQL iteration).
5. `reviewer-adversarial` Mode C (post-draft, Cat A default). If REVISE: apply once within cap.
6. Pre-commit (ruff/mypy N/A; planning-drift passes; jupytext sync fires).
7. Commit + PR + merge.
8. Post-merge: next plan (WP-4 or WP-5) overwrites.
