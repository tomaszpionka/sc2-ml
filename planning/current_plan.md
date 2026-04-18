---
category: A
date: 2026-04-18
branch: feat/01-04-04-identity-resolution
phase: "01"
pipeline_section: "01_04"
step: "01_04_04"
datasets: [sc2egset, aoestats, aoe2companion]
game: mixed
title: "01_04_04 Identity Resolution — 3-dataset exploration"
manual_reference: "docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md §4 + §5"
invariants_touched: [I2, I3, I6, I7, I8, I9]
predecessors: ["01_04_01", "01_04_02 + 2026-04-18 duration ADDENDUM (PR #155)", "01_04_03 9-col (PR #154)"]
plans_merged_from:
  - sc2egset planner a13b6543780c5c13b (5 tasks, 5 DS-SC2-IDENTITY decisions, 8 SQL queries, 3 PNGs)
  - aoestats planner a17b1b9e235934e7a (3 tasks — intra-dataset, civ-fingerprint JSD, cross-dataset preview)
  - aoe2companion planner a78278bf0361e934c (8 tasks, 6 JSON blocks, ATTACH-based cross-dataset preview)
---

# 01_04_04 Identity Resolution — 3-dataset exploration

## Problem Statement

Phase 02+ rating-system backtesting groups matches by a per-player primary key. The right key differs per dataset and is not yet empirically characterized:

- **sc2egset:** `toon_id` is region-scoped per Battle.net model (account → region → realm → toon). A physical player active on multiple regions has N distinct toon_ids. Using `toon_id` alone would split multi-region players into N cold-start Elo entities; using `LOWER(nickname)` alone would merge common-handle collisions ("Player", "SC2", "Default"). Neither is documented at this corpus.
- **aoestats:** Unique structural constraint — **no nickname column exists in any raw table**. `profile_id` (BIGINT) is the only identity signal. Invariant #2 (lowercased nickname as canonical) is natively unmeetable; either bridge to aoe2companion OR use a behavioral fingerprint (civ usage pattern, rating trajectory).
- **aoe2companion:** Has `profileId` + `name` + `country`. Quantify profileId↔name stability (rename history), name↔profileId collisions (common handles), and cross-table join integrity (`matches_raw` vs `profiles_raw` vs `ratings_raw`).

Cross-dataset question: do aoestats `profile_id` (DOUBLE→BIGINT) and aoe2companion `profileId` (INTEGER) share a namespace (e.g., both from aoe2insights.com API)? If yes, aoe2companion's `name` column could serve as I2 canonical nickname for aoestats via join. Empirical feasibility check only; full cross-dataset mapping deferred.

## Scope

**Exploration only** — produces census + decision-recommendation artifacts per dataset. No new VIEWs, no raw-table modifications, no schema YAML changes.

Each dataset gets its own 01_04_04 notebook + JSON + MD + optional CSVs/PNGs. Findings route to Phase 02 planner as `DS-*-IDENTITY-*` decision ledgers.

**In scope:**
- Per-dataset identity cardinality + NULL + sentinel audit
- Per-dataset structural uniqueness (multi-region for sc2; rename-history for aoec; stability-proxy for aoestats)
- Cross-dataset feasibility preview (aoestats ↔ aoec; small-sample ≤ 1,000 matches)
- Routing decisions to Phase 02

**Out of scope:**
- Canonical identity VIEW creation (Phase 02 deliverable per I2 — feature-engineering time, not cleaning time)
- Full cross-dataset identity mapping (separate CROSS PR if feasibility warrants)
- Upstream YAML modifications (I9)
- Thesis §4.2.2 [REVIEW] marker closure (Category F follow-up after evidence lands)

## Literature Context

- **Fellegi, I. P. & Sunter, A. B. (1969).** *A theory for record linkage.* JASA 64(328). Probabilistic-match framework — motivates agreement-pattern tabulation (nickname × region × temporal window) in sc2egset Class A/B/C classification + aoec match pairs. Already in bibliography.
- **Christen, P. (2012).** *Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution, and Duplicate Detection.* Springer. Four-stage pipeline (blocking → comparison → classification → evaluation) maps onto cross-dataset feasibility approach. Already in bibliography.
- **Winkler, W. E. (2006).** *Overview of Record Linkage and Current Research Directions.* US Census Bureau. EM algorithm for m/u probability estimation without ground truth — applicable if follow-up CROSS PR proceeds.
- **Hahn, Siqueira Ruela, & Rebelo Moreira (2020).** *Identifying Players in StarCraft via Behavioural Fingerprinting.* IEEE CoG. RTS behavioral-fingerprint stability — motivates aoestats civ-fingerprint JSD approach in absence of nickname.
- Manual `01_DATA_EXPLORATION_MANUAL.md` §4 (cleaning census) + §5 (panel-EDA feed-forward).

## Assumptions & Unknowns

**Shared:**
- **A1:** 86,400s threshold irrelevant here (duration-only). Identity thresholds are per-dataset empirical.
- **A2:** DuckDB 1.5.1 cross-DB `ATTACH ... (READ_ONLY)` works for aoestats ↔ aoec feasibility joins (empirically tested by aoec planner).
- **A3:** STEP_STATUS 01_04_04 is a NEW step. Per derivation chain: 01_04 auto-flips `complete → in_progress` when 01_04_04 added as `not_started`; restores to `complete` on gate pass. PHASE_STATUS 01 unchanged (01_05/01_06 still `not_started`).

**sc2egset-specific:**
- Sentinel `-1` claim (user-supplied) UNVERIFIED for sc2egset — univariate census (01_02_04) reports `zero_count=0` for toon_id in replay_players_raw. **Probe, don't assume.**
- 6 region values + 9 realm values (vs Battle.net canonical 5×2) — `Unknown` (~12.83%) is a data-quality concern; some tournaments predate full metadata capture.

**aoestats-specific:**
- NO nickname column — confirmed via planner inspection of `players_raw.yaml` (14 cols; no name/display/nickname field).
- `-1` sentinel claim (user-supplied) UNVERIFIED for aoestats. `01_02_04` reports `zero_count=0` in players_raw. Empirically confirm during T01.
- 13.95% `replay_summary_raw` non-empty — probe JSON parseability for hidden name extraction (feasibility probe only).

**aoec-specific:**
- `profileId = -1` confirmed as AI / anonymized (12.95M AI rows + 19.23k status='player' per 01_03_02).
- `profiles_raw` is 45.0% coverage of rm_1v1 match players (per 01_03_03 finding) — cannot be primary identity source; fall back to per-row matches_raw identity.

**Cross-dataset:**
- Window choice for feasibility: intersect aoestats (2022-08-29..2026-02-06) × aoec (2020-08-01..2026-04-04) = 2022-08-29..2026-02-06. Pick most recent complete week common to both: 2026-01-25..2026-01-31 (conservative choice before aoestats end date).
- Cross-dataset heuristic: 60s temporal window + civ-set equality + 50-ELO rating proximity. Weak blocker by design (Christen Ch. 4); reports evidence not adjudication.

## Execution Steps

### T01 — Register 01_04_04 step in all 3 datasets + revert PIPELINE_SECTION_STATUS 01_04 to in_progress

For each dataset:
1. Append `### Step 01_04_04 — Identity Resolution` block to `reports/ROADMAP.md` (after existing 01_04_03 block).
2. Add `01_04_04: {name: "Identity Resolution", pipeline_section: "01_04", status: not_started}` to `STEP_STATUS.yaml`.
3. Flip `PIPELINE_SECTION_STATUS.yaml` `01_04.status: complete → in_progress` (derivation-chain consistency).

PHASE_STATUS.yaml: unchanged.

Parent-level (not in any dataset's scope) — add to `reports/research_log.md` a CROSS stub entry for 01_04_04 + branch setup note.

### T02 — Per-dataset notebooks (3 parallel executors)

Each dataset's executor produces:
- `sandbox/<game>/<dataset>/01_exploration/04_cleaning/01_04_04_identity_resolution.py` + `.ipynb`
- `src/rts_predict/games/<game>/datasets/<dataset>/reports/artifacts/01_exploration/04_cleaning/01_04_04_identity_resolution.{json,md}`
- Dataset-specific supplementary artifacts (CSVs for sc2egset; PNGs for sc2egset; nothing additional for aoestats/aoec)

**sc2egset (5 tasks, see sibling planner output for full detail):**
- **Cell A** I0 sanity (row-count checks)
- **Cell B** single-key census (K1..K5: toon_id, (region,realm,toon_id), LOWER(nickname), (LOWER(nickname),region), (LOWER(nickname),region,realm))
- **Cell C** toon_id cross-region audit (Battle.net scoping test)
- **Cell D** nickname cross-region audit (multi-account evidence)
- **Cell E** temporal-overlap classification (Fellegi-Sunter agreement pattern: Class A=overlap, B=disjoint, C=degenerate)
- **Cell F** within-region handle-collision audit (common-handle evidence)
- **Cell G** userID refutation cross-check
- **Cell H** region/realm sanity (Unknown bucket)
- **Cell I** robustness on matches_flat_clean (±1% delta tolerance)
- **Cell J** 3 PNG plots (key cardinality bars, toon region heatmap, nickname cross-region stacked)
- **Cell K** DS-SC2-IDENTITY-01..05 decision ledger
- **Cell L** JSON + MD writers (Invariant I6: all SQL verbatim)

Expected numbers: `n_distinct(toon_id) / n_distinct(LOWER(nickname)) ≈ 2.26` (from 01_02_04 baseline; ±0.05 tolerance).

**aoestats (3 tasks):**
- **T01 intra-dataset:** sentinel/NULL audit across 4 columns × 3 tables; per-profile activity distribution; duplicate census (489 anchor ±10); rating-trajectory monotonicity probe (10k reservoir sample, seed 20260418); replay_summary_raw JSON-parseability feasibility probe
- **T02 civ-fingerprint JSD:** within-profile (first-half vs second-half) JSD distribution + 10,000-random-pair cross-profile control; literature thresholds 0.10/0.30/0.50; 10-profile concrete-example table
- **T03 cross-dataset preview:** 1,000-match reservoir sample from 2026-01-25..2026-01-31 window; 60s temporal block + civ-set + 50-ELO; report agreement rate + 95% bootstrap CI + verdict (A=strong, B=weak, C=infeasible)

**aoe2companion (8 tasks, most detailed):**
- **T01** cardinality baseline (3 tables: matches_raw, ratings_raw, profiles_raw)
- **T02** name-history-per-profileId profile (rename detection, binned 2-name / 3-5 / 6+)
- **T03** name→profileId collision (alias detection)
- **T04** join integrity across 3 raw tables (set-difference audit)
- **T05** (profileId, country) temporal stability
- **T06** cross-dataset feasibility via ATTACH READ_ONLY to aoestats DB; 2026-01-25..2026-01-31 window
- **T07** compose MD + JSON + synthesis (OBS-N → IMPL-N → ACTION-N)
- **T08** ROADMAP + research_log + STEP_STATUS update

### T03 — Close status + research_log (parent + 3 parallel updates)

For each dataset:
1. Update `STEP_STATUS.yaml` 01_04_04 → complete (completed_at date).
2. Restore `PIPELINE_SECTION_STATUS.yaml` 01_04 → complete.
3. Prepend dated research_log entry with findings + per-dataset DS-IDENTITY-* decisions.

Parent-level:
- Update `reports/research_log.md` with CROSS synthesis entry reconciling cross-dataset feasibility verdict (aoestats T03 ↔ aoec T06 must agree; if disagree, flag for adversarial review).

### T04 — CHANGELOG + version bump (parent)

3.15.0 → 3.16.0 (minor bump for new phase-step content).

## File Manifest

Per dataset (× 3):
- `sandbox/<game>/<dataset>/01_exploration/04_cleaning/01_04_04_identity_resolution.py` + `.ipynb` (NEW)
- `reports/artifacts/01_exploration/04_cleaning/01_04_04_identity_resolution.{json,md}` (NEW)
- `reports/ROADMAP.md` (append 01_04_04 block)
- `reports/STEP_STATUS.yaml` (add 01_04_04)
- `reports/PIPELINE_SECTION_STATUS.yaml` (01_04: in_progress → complete roundtrip)
- `reports/research_log.md` (prepend entry)

Dataset-specific:
- sc2egset: 2 CSVs (cross_region_nicknames, within_region_handle_collisions) + 3 PNGs under `artifacts/.../plots/`

Parent:
- `planning/current_plan.md` (this file; committed on branch at plan step)
- `reports/research_log.md` (CROSS entry)
- `CHANGELOG.md` ([3.16.0] entry)
- `pyproject.toml` (3.15.0 → 3.16.0)

**NOT touched (I9):**
- All 3 datasets' raw `*.yaml` under `data/db/schemas/raw/`
- All 3 datasets' view `*.yaml` under `data/db/schemas/views/`
- No new DuckDB VIEWs or TABLEs

## Gate Condition

Per dataset (all HALTING):

1. Artifact JSON + MD exist and parse; all SQL verbatim in `sql_queries` block (I6).
2. Decisions ledger populated (sc2egset: 5 DS-SC2-IDENTITY-*; aoestats: 3+ DS-AOESTATS-IDENTITY-*; aoec: 5+ DS-AOEC-IDENTITY-*).
3. Verdict/recommendation explicitly stated in MD "Synthesis" section.
4. I9 empty diff on all upstream YAMLs (verified by `git diff --stat master..HEAD`).
5. `ruff check` + `mypy` + jupytext drift checks pass on notebook.

Cross-dataset gate:
6. aoestats T03 and aoec T06 feasibility verdicts agree (both A / both B / both C). If disagree, HALT and dispatch adversarial — methodology asymmetry.
7. Parent research_log CROSS entry ties the 3 dataset findings together.

## Open Questions

Resolved at planning integration:
- **Q-cross-dataset-window:** Use 2026-01-25..2026-01-31 (most recent complete week in aoestats×aoec coverage intersection).
- **Q-threshold-consistency:** aoestats civ-fingerprint thresholds 0.10/0.30/0.50 documented as literature-anchored; flag in MD for per-game calibration if needed.
- **Q-step-status-pattern:** All 3 datasets revert 01_04 → in_progress at T01, restore at T03 (derivation-chain rule + 01_04_02/03 ADDENDUM precedent).
- **Q-verdict-rubric:** Both aoestats T03 and aoec T06 use same verdict framework: A=strong (>50% overlap), B=partial (10-50%), C=disjoint (<10%).

Deferred:
- Whether a canonical `player_identity_canonical` VIEW should ship in Phase 01 (before 01_05) or wait for Phase 02 — defer until sc2egset T02 Cell D evidence lands.
- Whether Phase 02 will ratify cross-dataset CROSS PR vs keep datasets isolated — defer until T06/T03 verdicts converge.
- Thesis §4.2.2 [REVIEW] marker closure — Category F follow-up.

## Adversarial instruction

Category A plan. Single pre-exec adversarial round (per user "less ceremony" directive). Reviewer-adversarial focuses on cross-plan consistency (decision rubric agreement, scope-boundary discipline between the 3 datasets, cross-dataset feasibility methodology convergence). Skip multi-round unless BLOCKERs fire.

Execution dispatches 3 parallel executors (one per dataset) after adversarial APPROVE.
