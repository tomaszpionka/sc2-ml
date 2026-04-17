---
category: A
branch: fix/01-04-null-audit
date: 2026-04-17
planner_model: claude-opus-4-7
phase: "01"
pipeline_section: "01_04 — Data Cleaning"
dataset: cross-dataset (sc2egset, aoestats, aoe2companion)
invariants_touched: [I3, I6, I7, I8, I9]
critique_required: true
research_log_ref: src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md#2026-04-17-phase-01-step-01-04-01-part-b-missingness-audit-insight-gathering
source_artifacts:
  - temp/null_handling_recommendations.md
  - docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json
---

<!-- Consolidated plan for 01_04_01 Missingness Audit refactor (3 datasets) -->
<!-- v3-r2 APPROVED by reviewer-adversarial round 4 + reviewer-deep validation -->

# DECISIONS LOCKED (user, 2026-04-17)

The three open questions raised in the v1 plan have been answered by the user. The plan below already reflects them; this banner exists so executor and reviewer-adversarial see them immediately.

| # | Question | Decision | Rationale (user words) |
|---|----------|----------|-------------------------|
| Q1 | JSON-inline ledger vs standalone files | **Keep both** | (no caveat) |
| Q2 | `research_log.md` CROSS entry | **Per-dataset only**, no CROSS entry | "Easier to fix retro-actively with less friction." |
| Q3 | Ledger row scope | **Option B — full coverage** (every column gets a row; zero-missingness rows tagged `mechanism="N/A"`, `recommendation="RETAIN_AS_IS"`) | "Apply the solution which works better in terms of futureproofness — should be helpful for decision making and for me and claude to understand it." |

These decisions affect Deliverables 1 (ROADMAP YAML), 5 (ledger schema), 6 (assertions), and 7 (file manifest). See "Decisions locked (user, this round)" near the end of this file for the prose explanation.

---

# REVISION CHANGELOG (v1 → v2)

This v2 supersedes v1 in full. The four critique BLOCKERs and seven WARNINGs raised in `planning/current_plan.critique.md` have been resolved per user direction:

- **BLOCKER B1 (aoestats `winner` column references):** v2 references the actual matches_1v1_clean schema columns: target = `team1_wins` (BIGINT), source columns = `p0_winner`/`p1_winner` (zero-NULL booleans). The phantom `winner` column is removed from DS-AOESTATS-05, the spec dict comment, the per-VIEW target sets, and Deliverable 6.C. Verified against `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_01_data_cleaning.py` lines 274-298, 532-540.
- **BLOCKER B2 (aoestats old_rating sentinel range):** v2 sets `sentinel_value=0` for `p0_old_rating`/`p1_old_rating` and cites the ACTUAL ground-truth artifact for OLD_RATING (verified directly): `numeric_stats_players[label='old_rating'].min_val=0, n_zero=5937` (consistent with `players_raw_census.old_rating.zero_count=5937, zero_pct=0.0055`). The v3-r1 fix corrects a v2 crossed-figure error: the `min=-5, n_zero=5187` figures belong to `new_rating` (POST-GAME, excluded per I3), NOT to `old_rating`. DS-AOESTATS-02 is restated to surface only the in-scope question for old_rating's `0`-sentinel disposition.
- **BLOCKER B3 (aoe2companion future-step citation):** "+ 01_05 temporal panel evidence" is struck from `antiquityMode` and `hideCivs` justifications. The 01_02_04 census alone (verified: antiquityMode null_pct=68.66%, hideCivs null_pct=49.30%) grounds both entries.
- **BLOCKER B4 (override priority):** v2 introduces an explicit two-tier resolution: (a) F1 zero-missingness override fires whenever `n_total_missing == 0`, producing `RETAIN_AS_IS` / `mechanism="N/A"`; (b) the target-override post-step converts the recommendation to `EXCLUDE_TARGET_NULL_ROWS` if the column is in the per-VIEW target set AND `n_total_missing > 0`. Per-VIEW target sets are made explicit in Deliverable 3 and referenced from 6.B/6.C. Examples: sc2egset matches_flat_clean `result` (0 NULLs) → `RETAIN_AS_IS`; sc2egset player_history_all `result` (Undecided/Tie present) → `EXCLUDE_TARGET_NULL_ROWS`.
- **WARNING W1 (Davis 2024 citation):** retained in `methodology_citations` with explicit inline tag "(retained for future Phase 02/03 reference; not load-bearing in this audit step)".
- **WARNING W2 (aoe2companion Group C enumeration):** all ~33 game-settings columns now enumerated explicitly in `_missingness_spec` (Deliverable 2.C). Group C entries cite their actual 01_02_04 NULL rates with one-liner mechanism justifications. The runtime constants-detection branch (W7) backs up any spec-fallback case.
- **WARNING W3 (CONVERT_SENTINEL_TO_NULL recommendation):** new `_recommend()` branch added — fires when `n_sentinel > 0` AND `n_null == 0` AND `pct_sentinel < 5%`. Returns `CONVERT_SENTINEL_TO_NULL` with citation of Rule S3. Reflected in Deliverables 3, 5.B/5.C/5.D enum, 6.B assertion enum, and 6.C per-dataset assertions for `team_0_elo`/`team_1_elo`/SQ.
- **WARNING W4 (DB connection standardization):** unified to `con = db.con` then `con.execute(...)` across all three notebooks. sc2egset notebook normalization includes ALL 58 existing `con.con.execute(...)` calls plus the new audit cells. aoestats notebook changes the connection-acquisition cell from `con = db._con` (private attribute) to `con = db.con` (public attribute); existing `con.execute(...)` call sites stay unchanged. aoe2companion is already conformant. Documented in Deliverable 3 with rationale.
- **WARNING W5 (DS-SC2-04 restatement):** restated to surface a real downstream question against `player_history_all`: "How should NULL-target rows in player_history_all be handled when computing player history features (drop / mark as DRAW / retain with NaN target)?" The matches_flat_clean confirmation (1v1_decisive filter excludes ~0.06%) is moved to `key_findings_carried_forward` as a CONSORT-verification line rather than a downstream open question.
- **WARNING W6 (tautological assertion in 6.B):** the `n_nonzero_ledger >= max(n_nonzero_null_cols, n_sentinel_hits)` block is replaced with a single comment noting that coverage is guaranteed by the full-coverage assertion above.
- **WARNING W7 (go_* and other fallback MAR for constants):** TWO fixes applied: (a) `_consolidate_ledger` now runs `SELECT COUNT(DISTINCT "{col}") FROM {view_name}` for every column before spec lookup; if `n_distinct == 1`, mechanism becomes `"N/A"` and recommendation becomes `"DROP_COLUMN"` ("Constant column; n_distinct=1; no information content."). (b) The 15 sc2egset `go_*` columns are enumerated explicitly in `_missingness_spec` (Deliverable 2.A) with mechanism per evidence — variable cardinality go_* get justified MAR; constant go_* are flagged for the runtime constants-detection branch as a defense-in-depth check.
- **NOTE-1 (cross-game ledger comparability):** sentence added to Deliverable 5.B noting Phase 02's feature-category taxonomy will map dataset-specific column names ({MMR, team_0_elo, rating} → "pre-game skill rating") for cross-game analysis.
- **NOTE-2 (F2 verification):** Deliverable 7 gate condition includes an explicit grep step to confirm no leftover `col != "winner"` branch remains in legacy aoestats notebook code.
- **NOTE-3 (threshold language):** ROADMAP `scientific_invariants_applied` block reframed: thresholds 5/40/80% follow operational starting heuristics from §1.2, with Schafer & Graham 2002 cited for the <5% MCAR boundary and van Buuren 2018 cited for the warning against rigid global thresholds.
- **NOTE-4 (post-execution review):** Deliverable 7 closes with a directive to dispatch reviewer-deep against the produced ledgers before they are cited by Phase 02.

Empirical data spot-check during plan rewrite:
- aoestats `players_raw.old_rating`: min=0, max=3045, n_zero=5,937 — consistent across `numeric_stats_players[label='old_rating']` and `players_raw_census.old_rating` (verified directly during v3-r1 rewrite). The `min=-5, n_zero=5,187` figures belong to `new_rating` (POST-GAME, excluded by I3), not `old_rating`.
- aoestats `matches_raw.avg_elo`: min=0, max=2976.5, n_zero=121 — from `numeric_stats_matches[label='avg_elo']` (the `n_zero=4,824` figure belongs to `team_0_elo`, not `avg_elo`).
- aoestats `matches_raw.team_0_elo` and `team_1_elo`: min=-1; n_zero(team_0)=4824, n_zero(team_1)=192.
- aoe2companion `matches_raw.server` null_pct=97.99, `hideCivs` null_pct=49.30, `antiquityMode` null_pct=68.66, `modDataset` null_pct=99.72.
- sc2egset 15 `go_*` columns confirmed enumerated in matches_flat_clean DDL (lines 570-584 of the existing notebook).
- aoe2companion matches_1v1_clean DDL: 54 columns (53 from matches_raw + `is_null_cluster` derived).
- aoestats matches_1v1_clean DDL: 21 columns (no `winner`; target = `team1_wins`; source booleans = `p0_winner`, `p1_winner`).

---

# Plan — 01_04_01 Data Cleaning / Null Audit Refactor (3 datasets) — v2

**Category:** A | **Branch:** `fix/01-04-null-audit` (current) | **Critique gate required after approval.**

**Phase/Step refs:** Phase 01 / Pipeline Section 01_04 / Step 01_04_01 (per `docs/PHASES.md` and each dataset's ROADMAP).

**Scope reframe (the user's load-bearing decision):** 01_04_01 is an **insight-gathering audit**. It produces a missingness ledger and surfaces decisions for 01_04_02+. It does NOT execute decisions, modify VIEWs, drop columns, or impute. Two coordinated census passes (SQL NULL + sentinel) plus a runtime constants-detection step feed one consolidated ledger per VIEW per dataset.

**Cross-game design (Invariant I8/Rule S6):** Same `_missingness_spec` schema, same ledger schema, same recommendation logic, same artifact path layout, same DB connection idiom across all three datasets.

---

## Scope

Refactor 01_04_01 across 3 datasets (sc2egset, aoestats, aoe2companion) from a NULL-only audit to a Missingness Audit with two coordinated census passes (SQL NULL + sentinel) plus runtime constants detection, feeding a consolidated 17-column ledger per VIEW. The audit is **insight-gathering for downstream cleaning decisions in 01_04_02+, NOT decision-execution**. See the "Scope reframe" paragraph above and the per-dataset deliverables (1.A/1.B/1.C through 7) below for full detail.

## Problem Statement

Step 01_04_01 prior implementations covered SQL NULL counts only — missing the substantial sentinel-encoded missingness (`MMR=0` ~83% in sc2egset; `team_0_elo=-1` in aoestats; etc.) that drives Phase 02 imputation strategy. Audit needed to (a) close that gap with a sentinel-aware second pass, (b) preserve the audit's "recommend only" contract while surfacing alternatives via per-dataset `decisions_surfaced` blocks, and (c) standardize cross-dataset framework so Phase 02 can consume uniform ledger artifacts. Iteration history (v1 → v3-r2) and resolved BLOCKERs/WARNINGs are documented in the "REVISION CHANGELOG" near the top of this file.

## Assumptions & unknowns

- **Assumption:** the 01_02_04 census artifacts are the authoritative source for raw-table NULL/sentinel rates; VIEW rates differ and are computed at audit runtime.
- **Assumption:** the user's locked Q1/Q2/Q3 decisions (banner above) hold for the entire scope; no late re-litigation of full-coverage Option B vs compact alternative.
- **Assumption:** B6 deferral via DS entries (Option D, user-elected) is the appropriate semantic-content sentinel handling; downstream 01_04_02+ chooses between the surfaced alternatives without prejudice from the audit recommendation.
- **Unknown:** Phase 02 imputation strategy for primary features with high NULL rates — deferred to 01_04_02+ disposition step (resolves by 01_04_02+ planning round).
- **Unknown:** whether the constants `mod`, `difficulty`, `status`, `leaderboard`, `num_players` flagged DROP_COLUMN by W7 should also be surfaced in cross-dataset feature taxonomy — Phase 02 concern.

## Literature context

Methodology citations are recorded in each dataset's ROADMAP.md `methodology_citations` block (Deliverable 1.A/1.B/1.C). Sources include: Rubin 1976 (MCAR/MAR/MNAR taxonomy origin); Little & Rubin 2019 (3rd ed.); van Buuren 2018 (warning against rigid rate thresholds); Sambasivan et al. CHI 2021 (data cascades); Schafer & Graham 2002 (<5% MCAR boundary); Davis et al. 2024 (sports analytics protocols, retained for future Phase 02/03 reference); sklearn v1.8 MissingIndicator + HistGradientBoostingClassifier NaN handling; CRISP-DM cleaning report convention; Manual 01 §3 (Profiling) + §4 (Cleaning).

## Execution Steps

The plan organizes execution into 7 deliverables (sections below). Each dataset follows the same pattern; per-dataset specifics in 1.A/1.B/1.C, 2.A/2.B/2.C, 4.A/4.B/4.C, 6.C. Helpers in Deliverable 3 are DRY across datasets.

- **Deliverable 1** — Three updated ROADMAP entries (replaces existing 01_04_01 step blocks)
- **Deliverable 2** — `_missingness_spec` dict contents per dataset
- **Deliverable 3** — Sentinel census + constants detection + override priority (DRY helpers)
- **Deliverable 4** — Notebook structure (cells in order)
- **Deliverable 5** — Missingness ledger artifact schema and path
- **Deliverable 6** — Test/assertion list per notebook
- **Deliverable 7** — Branch + file list + gate condition

Status: COMPLETE — three executor agents executed in parallel on 2026-04-17; reviewer-deep validated; 3 BLOCKERs from reviewer-deep round addressed via follow-up surgical fixes (B1/B2/B3 in aoestats DS narratives) plus W1/W3/N1.

## File Manifest

See **Deliverable 7 — File manifest** below for the per-dataset file list (notebook .py + .ipynb, ROADMAP.md, artifacts CSV/JSON/MD, research_log.md additions). 26 files total across the three datasets plus this plan + critique.

## Gate Condition

See **Deliverable 7 — Gate condition (composite, all three datasets)** below for the 12 gate criteria. Status verified by all three executor agents at execution time and confirmed by reviewer-deep in `planning/current_plan.critique.md`.

## Open questions

The user resolved Q1/Q2/Q3 in the locked-decisions banner at the top of this document (resolves by: user decision, complete). Reviewer-adversarial rounds 1–4 raised and resolved 4+3+2+0 BLOCKERs (resolves by: planner-science / parent surgical edits per round). Reviewer-deep round identified 3 BLOCKERs + 5 WARNINGs + 3 NOTEs — all elected fixes (BLOCKERs + W1 + W3 + W5 + N1) applied (resolves by: post-execution executor agents). No open questions remain that block PR creation; remaining items (W2 inline JSON shape, W4 spec annotation, NOTE-2 password sanity check, NOTE-3 helper extraction) are tracked as follow-ups.

---

## Deliverable 1 — Three updated ROADMAP entries (full YAML text)

Each block replaces the existing `### Step 01_04_01 -- Data Cleaning` block. Description is rewritten to "insight-gathering for downstream cleaning decisions in 01_04_02+, NOT decision-execution." Predecessors and notebook paths preserved.

### 1.A — `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`

```yaml
step_number: "01_04_01"
name: "Data Cleaning — VIEW DDL + Missingness Audit (insight-gathering)"
description: >
  Two-part step with one execution pass.
  PART A (already executed in PRs #138/#139): non-destructive cleaning of
  replay_players_raw and replays_meta_raw via three DuckDB VIEWs (matches_flat,
  matches_flat_clean, player_history_all) — all DDL changes resolved in prior PRs.
  PART B (this revision): consolidated missingness audit over the analytical VIEWs
  (matches_flat_clean, player_history_all). Two coordinated census passes per VIEW —
  SQL NULL census plus sentinel census driven by per-column _missingness_spec — plus
  a runtime constants-detection check, feed one missingness ledger (CSV+JSON) per
  VIEW. The audit gathers insights for downstream cleaning decisions in 01_04_02+;
  it does NOT execute decisions, modify VIEWs, drop columns, or impute. Ends with
  an explicit "Decisions surfaced for downstream cleaning" section listing
  per-dataset open questions.
phase: "01 — Data Exploration"
pipeline_section: "01_04 — Data Cleaning"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Sections 3 (Profiling) and 4 (Cleaning)"
dataset: "sc2egset"
question: >
  What is the complete missingness picture (NULL + sentinel-encoded + constant
  columns) per analytical VIEW column, classified by mechanism (Rubin 1976
  MCAR/MAR/MNAR), and which open questions must downstream 01_04 steps resolve
  before Phase 02 imputation design?
method: >
  Three-step per-VIEW audit (matches_flat_clean, player_history_all):
  Step 1 (kept verbatim): SQL NULL census per column via
  COUNT(*) FILTER (WHERE col IS NULL) over the full VIEW.
  Step 2 (NEW): sentinel census per column driven by _missingness_spec dict
  (per-column override is preferred; auto-detection from prior census artifacts is
  the secondary fallback). Sentinel SQL per column matches the spec's declared
  sentinel value(s).
  Step 3 (NEW): runtime constants detection — SELECT COUNT(DISTINCT col) per VIEW
  column; columns with n_distinct=1 get mechanism="N/A" + recommendation="DROP_COLUMN".
  Per-row recommendation derived from pct_missing_total = pct_null + pct_sentinel
  via the decision tree in temp/null_handling_recommendations.md §3.1, applying
  Rules S1-S6, with two override layers: (a) F1 zero-missingness override and
  (b) target-column override per Rule S2. The notebook produces RECOMMENDATIONS
  only; downstream 01_04 steps decide and execute.
  Reads the empirical sentinel patterns from
  artifacts/01_exploration/02_eda/01_02_04_univariate_census.json — the audit
  consolidates prior findings; it does not re-derive them.
predecessors:
  - "01_03_04"
methodology_citations:
  - "Rubin, D.B. (1976). Inference and missing data. Biometrika, 63(3), 581-592. — MCAR/MAR/MNAR taxonomy."
  - "Little, R.J. & Rubin, D.B. (2019). Statistical Analysis with Missing Data, 3rd ed. Wiley. — Authoritative mechanism classification."
  - "van Buuren, S. (2018). Flexible Imputation of Missing Data, 2nd ed. CRC Press. — Warns against rigid percentage thresholds; threshold S4 used as starting heuristic only."
  - "Schafer, J.L. & Graham, J.W. (2002). Missing data: Our view of the state of the art. Psychological Methods, 7(2), 147-177. — Listwise deletion acceptable at <5% MCAR (boundary citation, not threshold derivation)."
  - "Sambasivan, N. et al. (2021). Everyone wants to do the model work, not the data work: Data Cascades in High-Stakes AI. CHI '21. — Rationale for surfacing decisions explicitly rather than deferring."
  - "Davis, J. et al. (2024). Methodology and Evaluation in Sports Analytics. Machine Learning, 113, 6977-7010. — Domain precedent for sports outcome data quality protocols (retained for future Phase 02/03 reference; not load-bearing in this audit step)."
  - "scikit-learn v1.8 documentation. Imputation of missing values; sklearn.impute.MissingIndicator. — Missingness-as-signal principle for Phase 02."
  - "Wirth, R. & Hipp, J. (2000). CRISP-DM: Towards a standard process model for data mining. — Cleaning report convention adopted in artifact format."
  - "Manual 01_DATA_EXPLORATION_MANUAL.md §3 (Profiling) and §4 (Cleaning) — pipeline phase boundary (Phase 01 documents, Phase 02 transforms)."
notebook_path: "sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_01_data_cleaning.py"
inputs:
  duckdb_tables:
    - "replay_players_raw (44,817 rows)"
    - "replays_meta_raw (22,390 rows)"
  duckdb_views:
    - "matches_flat (44,817 rows / 22,390 replays)"
    - "matches_flat_clean (44,418 rows / 22,209 replays)"
    - "player_history_all (44,817 rows / 22,390 replays)"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json (sentinel and zero-distribution evidence)"
    - "artifacts/01_exploration/03_profiling/* (column-level mechanism evidence — see prior steps)"
outputs:
  duckdb_views:
    - "matches_flat (unchanged)"
    - "matches_flat_clean (unchanged)"
    - "player_history_all (unchanged)"
  schema_yamls:
    - "data/db/schemas/views/player_history_all.yaml (unchanged from PR #138/#139)"
  data_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json (extended with missingness_audit block)"
    - "artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv (NEW — one row per (view, column); full-coverage Option B; zero-missingness columns tagged RETAIN_AS_IS / mechanism=N/A; constant columns tagged DROP_COLUMN / mechanism=N/A)"
    - "artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.json (NEW — same content, machine-readable)"
  report: "artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md (extended)"
reproducibility: >
  Code and output in the paired notebook. All SQL verbatim in JSON sql_queries.
  Audit re-runs deterministically from raw tables.
key_findings_carried_forward:
  - "157 replays excluded due to MMR<0 (PR predecessor — kept)"
  - "MMR=0 sentinel covers 83.66% of true_1v1_decisive rows (audit confirms)"
  - "highestLeague='Unknown' covers ~72% (audit confirms)"
  - "clanTag='' covers ~74% (audit confirms via sentinel pass)"
  - "matches_flat_clean's 1v1_decisive filter excludes ~0.06% Undecided/Tie rows from result (CONSORT verified each run; Rule S2 enforced upstream of the audit)"
decisions_surfaced:
  - id: "DS-SC2-01"
    column: "MMR (sentinel=0, ~83.66%)"
    question: >
      Convert MMR=0 to NULL and drop the column from matches_flat_clean
      (per Rule S4 / >80%), OR retain MMR=0 as an explicit `unranked` categorical
      encoding alongside `is_mmr_missing`, OR run the analysis on the rated subset
      only as a sensitivity arm (per Sambasivan 2021 cascade-prevention)?
    mechanism_note: >
      Resolve MMR mechanism contradiction: this plan classifies MMR=0 as
      MAR-primary (tournament replays without ladder MMR — missingness depends
      on observed replay source); MNAR (private pro accounts) is documented as a
      sensitivity branch. Source: 01_03_01 + 01_03_03 cleaning_registry rules.
  - id: "DS-SC2-02"
    column: "highestLeague (sentinel='Unknown', ~72.16%)"
    question: >
      Drop the column entirely (Rule S4 / >50% non-primary), OR retain 'Unknown'
      as its own category (Phase 02 decides if predictive)?
  - id: "DS-SC2-03"
    column: "clanTag (sentinel='', ~74%)"
    question: >
      Drop the column (likely non-predictive at this rate), OR retain as a derived
      `is_in_clan` boolean only?
  - id: "DS-SC2-04"
    column: "result in player_history_all (Undecided/Tie sentinel; non-zero rate in player_history_all)"
    question: >
      How should NULL-target rows in player_history_all be handled when computing
      player history features (e.g., expanding-window win-rate)? Drop these rows,
      mark them as a DRAW outcome category, or retain with NaN target value (so
      games-played counts include them but win-rate denominators exclude)?
  - id: "DS-SC2-05"
    column: "selectedRace (sentinel='', ~2.48%)"
    question: >
      Already converted to 'Random' in VIEWs (PR predecessor); the audit confirms
      zero residual empty-string occurrences in the cleaned VIEWs.
  - id: "DS-SC2-06"
    columns: "gd_mapSizeX / gd_mapSizeY (sentinel=0, ~1.22%)"
    question: >
      VIEWs already CASE-WHEN to NULL (PR predecessor); audit confirms ledger
      reports the converted NULLs, not the original sentinel.
  - id: "DS-SC2-07"
    column: "gd_mapAuthorName"
    question: >
      Drop column on grounds of being a non-predictive metadata field even before
      missingness considered? Decision deferred to 01_04_02+.
  - id: "DS-SC2-08"
    columns: "go_* constants surfaced by runtime constants-detection branch"
    question: >
      Confirm the runtime constants-detection branch reports n_distinct=1 for the
      go_* columns flagged in 01_03_03 (and which exact columns are identified as
      constant in matches_flat_clean vs player_history_all). Drop these per
      Rule S4 / N/A-mechanism in 01_04_02+?
  - id: "DS-SC2-09"
    column: "handicap (sentinel=0, ~0.0045% — 2 anomalous rows)"
    question: >
      NULLIF the 2 anomalous handicap=0 rows + listwise deletion per Rule S3
      (negligible rate), OR retain 0 as an explicit `is_anomalous_handicap` flag?
      B6 deferral note — same pattern as DS-AOESTATS-02: audit will recommend
      CONVERT_SENTINEL_TO_NULL via W3 branch; spec marks
      carries_semantic_content=True (0 is documented as "anomalous game"
      indicator, semantically meaningful); downstream chooses without prejudice
      from the ledger.
  - id: "DS-SC2-10"
    column: "APM in player_history_all (sentinel=0, ~2.53%; 97.9% overlap with selectedRace='')"
    question: >
      Convert APM=0 to NULL via NULLIF in 01_04_02+ (per audit recommendation)
      OR retain APM=0 as a categorical encoding for "extremely short / unparseable
      game"? B6 deferral note — audit will recommend CONVERT_SENTINEL_TO_NULL
      via W3 branch; spec marks carries_semantic_content=True (APM=0 documented
      as correlating with selectedRace='' — meaningful game-state signal);
      downstream chooses without prejudice from the ledger.
scientific_invariants_applied:
  - number: "3"
    how_upheld: >
      No new feature computation. No use of game T data. Audit is read-only over
      VIEWs whose I3 compliance was established in the predecessor PRs.
  - number: "6"
    how_upheld: >
      All three SQL templates (NULL census, sentinel census, constants detection)
      stored verbatim in JSON sql_queries. The per-column sentinel queries are
      reconstructible from the template + the _missingness_spec dict (also stored
      in the artifact).
  - number: "7"
    how_upheld: >
      Thresholds (5%/40%/80%) follow the operational starting heuristics in
      temp/null_handling_recommendations.md §1.2; cite Schafer & Graham 2002 for
      the <5% MCAR boundary and van Buuren 2018 for the warning against rigid
      global thresholds. Each threshold-driven recommendation surfaces as a
      downstream decision per §3.1; the audit recommends, the downstream step
      decides. Per-column mechanism justifications cite either a prior step's
      artifact (with path) or a sentinel-meaning interpretation explicitly grounded
      in domain context.
  - number: "9"
    how_upheld: >
      All facts derive from this step's SQL or from cited predecessor artifacts.
      No raw tables, no VIEWs, no schema YAMLs are modified. Audit is purely
      additive: extends artifact JSON, adds two new ledger files. No future-step
      citations.
gate:
  artifact_check: >
    JSON has "missingness_audit" block with two VIEW sub-blocks, each containing
    a "ledger" array (one row per column in the VIEW — full-coverage Option B) and the
    "_missingness_spec" used. The two new ledger files (CSV + JSON) exist at the
    paths above. MD has a "Missingness Ledger" section per VIEW + a final
    "Decisions surfaced for downstream cleaning (01_04_02+)" section reproducing
    DS-SC2-01..10 with current observed rates filled in.
  continue_predicate: >
    Every column in the VIEW appears in the ledger (full-coverage Option B).
    Every column with non-zero missingness has a _missingness_spec entry; zero-
    missingness rows carry mechanism=N/A, recommendation=RETAIN_AS_IS, and
    justification="Zero missingness observed; no action needed." regardless of
    spec. Constant columns (n_distinct=1) carry mechanism=N/A,
    recommendation=DROP_COLUMN with constants-detection justification.
    Every ledger row has non-empty mechanism_justification, recommendation,
    recommendation_justification, and explicit carries_semantic_content boolean.
    Existing zero-NULL assertions (replay_id, toon_id, result in both VIEWs) still
    pass. STEP_STATUS.yaml has 01_04_01: complete.
  halt_predicate: >
    Any column in the VIEW missing from the ledger (full-coverage violation);
    any column with non-zero missingness lacking a _missingness_spec entry; any
    ledger row missing mandatory fields; any zero-NULL identity assertion failure;
    any contradictory pairing of mechanism="N/A" with non-N/A justification.
research_log_entry: >
  Required on completion: list per-VIEW row counts in ledger, reference the
  artifact paths, summarise decisions surfaced for downstream resolution.
```

### 1.B — `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`

Same shape as 1.A, with these dataset-specific deltas:

- `description` references matches_1v1_clean and player_history_all only (no third VIEW).
- `inputs.duckdb_tables` cites matches_raw (30,690,651 rows) and players_raw (107,627,584 rows).
- `inputs.duckdb_views` cites matches_1v1_clean (17,814,947 rows) and player_history_all (107,626,399 rows).
- `outputs.data_artifacts` includes the same two new ledger files at the aoestats artifact path.
- `key_findings_carried_forward` keeps the existing aoestats findings (997 inconsistent winner rows excluded, schema-change boundary 2024-03-17, t1_win_pct 52.27%).
- `decisions_surfaced` block:
  - **DS-AOESTATS-01:** team_0_elo / team_1_elo sentinel=-1 (~0.0001%): per the new `CONVERT_SENTINEL_TO_NULL` recommendation branch, confirm NULLIF in 01_04_02+ DDL pass per Rule S3 (negligible rate). Listwise deletion or simple imputation acceptable in Phase 02.
  - **DS-AOESTATS-02:** p0_old_rating / p1_old_rating sentinel=0 (n_zero=5,937 in players_raw, ~0.0055%): NULLIF + listwise deletion (negligible rate) per Rule S3 in 01_04_02+ DDL pass, OR retain `0` as an explicit `unrated` categorical encoding alongside `is_unrated`? Source: `players_raw_census.old_rating.zero_count=5937` (consistent with `numeric_stats_players[label='old_rating'].n_zero=5937`). **B6 deferral note:** the audit will recommend `CONVERT_SENTINEL_TO_NULL` for these columns via the W3 branch (sentinel-only, low-rate). However, spec marks `carries_semantic_content=True` (`0` = "unrated" carries meaning). The audit's recommendation is **non-binding for semantic-content sentinels** — 01_04_02+ explicitly chooses one of the two arms above (NULLIF-and-drop OR retain-as-category) and the recommendation does not pre-empt that choice. The ledger row carries both the `recommendation` and the `carries_semantic_content=True` flag so the downstream step has both signals.
  - **DS-AOESTATS-03:** avg_elo n_zero=121 (~0.0004% across 30,690,651 matches_raw rows): listwise deletion is trivially defensible per Rule S3, OR investigate whether zero is genuine aggregate vs sentinel via 01_04_02+ join to underlying team_0_elo / team_1_elo? Source: `numeric_stats_matches[label='avg_elo'].n_zero=121`. Note: the `4,824` figure is `team_0_elo.n_zero`, NOT `avg_elo.n_zero`. **B6 deferral note:** same as DS-AOESTATS-02 — audit will recommend `CONVERT_SENTINEL_TO_NULL`; spec marks `carries_semantic_content=True`; downstream chooses between the alternatives without prejudice from the ledger.
  - **DS-AOESTATS-04:** raw_match_type 12,504 NULLs in matches_raw (~0.04% of 30,690,651): MCAR per Rule S3, listwise deletion candidate at 01_04_02+ — but column may be redundant given internalLeaderboardId already constrains scope. **Note:** the `12,504` figure is `matches_raw_census.raw_match_type.null_count`; the actual NULL count in matches_1v1_clean (filtered scope) will be different and is computed at audit runtime by Pass 1.
  - **DS-AOESTATS-05:** team1_wins (the prediction target, BIGINT) in matches_1v1_clean: 0 NULLs verified (driven by the upstream `WHERE p0.winner != p1.winner` exclusion). Per Option B + F1 zero-missingness override → ledger row reports `mechanism=N/A`, `recommendation=RETAIN_AS_IS`. Source columns p0_winner / p1_winner also report 0 NULLs (BOOLEAN, zero-NULL verified by census). The phantom `winner` column referenced in the v1 plan does NOT exist in matches_1v1_clean.
  - **DS-AOESTATS-06:** winner column in player_history_all: nullable findings already documented; downstream feature computation must skip NULL-target rows for win-rate features (deferred to Phase 02; 01_04_02+ confirms the documentation note).
  - **DS-AOESTATS-07:** overviews_raw is a singleton metadata table (1 row), not used by any VIEW — formally declare out-of-analytical-scope at 01_04_02+ disposition step.

### 1.C — `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`

Same shape, with these aoe2companion-specific deltas:

- `inputs.duckdb_views` cites matches_1v1_clean (54 columns: 53 from matches_raw + `is_null_cluster` derived) and player_history_all (and ratings_clean unchanged from PR predecessor).
- `key_findings_carried_forward` keeps R01–R05 + the NULL cluster MNAR finding.
- **`decisions_surfaced`:** explicit partitioning of all ~33 game-settings columns, each enumerated:
  - **DS-AOEC-01 (structurally-absent group):** server (~98% NULL), modDataset (~99.7%), scenario (~98.3%), password (~82.9%). Drop from analytical VIEWs at 01_04_02+ (per Rule S4 / >80% MNAR-or-MAR), OR retain as ranked-vs-custom partition flags?
  - **DS-AOEC-02 (schema-evolution group):** antiquityMode (~68.66% — verified from 01_02_04), hideCivs (~49.30% — verified). Drop OR retain as patch-era indicator features (Phase 02 decides if predictive)?
  - **DS-AOEC-03 (low-NULL game settings group, individually enumerated in spec — Deliverable 2.C):** the remaining ~27 settings columns (mod, map, difficulty, startingAge, fullTechTree, allowCheats, empireWarsMode, endingAge, gameMode, lockSpeed, lockTeams, mapSize, population, recordGame, regicideMode, gameVariant, resources, sharedExploration, speed, speedFactor, suddenDeathMode, civilizationSet, teamPositions, teamTogether, treatyLength, turboMode, victory, revealMap). Each gets an explicit per-column 01_02_04-grounded justification in the spec; downstream disposition is RETAIN_AS_IS / FLAG_FOR_IMPUTATION per the rate. Constants-detection branch (W7) backs up any column missing an individual spec entry.
  - **DS-AOEC-04:** rating in matches_1v1_clean (~26% NULL in 1v1 scope per VIEW): primary feature exception per Rule S4. Phase 02 imputation strategy (median-within-leaderboard + add_indicator) must be specified before Phase 02 begins.
  - **DS-AOEC-05:** country (~12.6% in raw, lower in 1v1 VIEW): Phase 02 — 'Unknown' category encoding or add_indicator.
  - **DS-AOEC-06:** won in matches_1v1_clean: 0 NULLs (R03 guarantees) — per F1 zero-missingness override, ledger reports RETAIN_AS_IS / mechanism=N/A. Per the target-override post-step, RETAIN_AS_IS stands (no override fires when rate is zero).
  - **DS-AOEC-07:** won in player_history_all (~5%): MAR; per the target-override post-step, recommendation becomes EXCLUDE_TARGET_NULL_ROWS.
  - **DS-AOEC-08 (snapshot-table disposition — W2 fix):** leaderboards_raw and profiles_raw are NOT_USABLE per 01_03_03; profiles_raw has 7 dead columns (100% NULL). Formally declare out-of-analytical-scope at 01_04_02+ — these tables do not enter any VIEW and do not need triage.
- **`note_on_rates`:** all triage rates in the ledger derive from VIEWs (filtered scope), not raw tables. A column with 42% NULL in matches_raw can be ~26% NULL in matches_1v1_clean. The ledger is authoritative for downstream decisions because Phase 02 features are computed from the VIEWs.

---

## Deliverable 2 — `_missingness_spec` dict contents per dataset

Schema (identical across datasets):

```python
{
  "<column>": {
    "mechanism": "MAR" | "MCAR" | "MNAR" | "N/A",
    "justification": "<text citing prior step finding>",
    "sentinel_value": <scalar | list | None>,    # None means SQL NULL is the only missingness encoding
    "carries_semantic_content": bool,            # True if sentinel meaning differs from "data missing"
    "is_primary_feature": bool                   # affects Rule S4 high-NULL handling
  }
}
```

The dict declares the spec; the audit treats `sentinel_value=None` as "NULL only," scalar as a single sentinel, and list as a set of sentinels. Constants detected at runtime override the spec to `mechanism="N/A"`, `recommendation="DROP_COLUMN"`.

### 2.A — sc2egset `_missingness_spec` (insert in notebook ahead of new audit cells)

Source for sentinel values: `01_02_04_univariate_census.json`, the existing notebook's documented findings (MMR=0, SQ=INT32_MIN, selectedRace='', map_size=0, handicap=0), and the `temp/null_handling_recommendations.md` table. The 15 `go_*` columns are now explicitly enumerated (W7 fix).

```python
_missingness_spec = {
    # Identity columns (S1) — sentinel=None, mechanism=N/A, asserted zero
    # (no entries needed — handled by zero-NULL assertions)

    # Player pre-game features
    "MMR": {
        "mechanism": "MAR",
        "justification": (
            "MAR-primary: missingness depends on observed replay source "
            "(tournament replays lack ladder MMR). MNAR (private pro accounts) "
            "documented as sensitivity branch. Source: 01_03_01 cleaning_registry "
            "+ temp/null_handling_recommendations.md §4.1."
        ),
        "sentinel_value": 0,
        "carries_semantic_content": True,  # MMR=0 = 'unranked', MMR=NULL = 'data missing'
        "is_primary_feature": True,
    },
    "highestLeague": {
        "mechanism": "MAR",
        "justification": "Tournament replays lack league exposure data. Source: 01_02_04 census top-N.",
        "sentinel_value": "Unknown",
        "carries_semantic_content": True,
        "is_primary_feature": False,
    },
    "clanTag": {
        "mechanism": "MAR",
        "justification": "Not all players are in clans. Source: domain knowledge + 01_02_04 distribution.",
        "sentinel_value": "",
        "carries_semantic_content": True,
        "is_primary_feature": False,
    },
    "selectedRace": {
        "mechanism": "MAR",
        "justification": "Empty string = Random race; resolved post-game. VIEWs convert to 'Random'. Source: 01_03_02.",
        "sentinel_value": "",
        "carries_semantic_content": True,
        "is_primary_feature": False,
    },
    "result": {
        "mechanism": "MNAR",
        "justification": "Game crashed/ended abnormally. Source: 01_03_02.",
        "sentinel_value": ["Undecided", "Tie"],
        "carries_semantic_content": True,
        "is_primary_feature": False,  # but is the prediction TARGET — handled by target-override post-step (Rule S2)
    },

    # Map metadata
    "gd_mapSizeX": {
        "mechanism": "MCAR",
        "justification": "Parse artifact (273 replays). Not correlated with outcome. Source: 01_02_04 + 01_03_01.",
        "sentinel_value": 0,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },
    "gd_mapSizeY": {
        "mechanism": "MCAR",
        "justification": "Same parse artifact as gd_mapSizeX (same 273 replays).",
        "sentinel_value": 0,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },
    "gd_mapAuthorName": {
        "mechanism": "MAR",
        "justification": "Map metadata not parsed for all replays. Likely non-predictive.",
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },
    "handicap": {
        "mechanism": "MCAR",
        "justification": "Standard handicap=100; 2 anomalous rows have 0. Source: 01_02_04.",
        "sentinel_value": 0,
        "carries_semantic_content": True,
        "is_primary_feature": False,
    },

    # In-game (player_history_all only)
    "SQ": {
        "mechanism": "MCAR",
        "justification": "INT32_MIN sentinel = parse failure (2 rows). Source: 01_03_01.",
        "sentinel_value": -2147483648,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },
    "APM": {
        "mechanism": "MAR",
        "justification": (
            "APM=0 correlates with selectedRace='' (97.9% overlap). Documentation-only "
            "in 01_04_01 — not converted to NULL. In-game; not in matches_flat_clean."
        ),
        "sentinel_value": 0,
        "carries_semantic_content": True,
        "is_primary_feature": False,
    },

    # go_* game options (W7 fix — enumerated; constants-detection branch backs up
    # any constant). For variable-cardinality go_* columns, mechanism is MAR
    # (game option metadata not parsed for all replays). Constants are flagged at
    # runtime; spec entries here are documentation + defense-in-depth.
    "go_advancedSharedControl": {
        "mechanism": "MAR",
        "justification": "Game option metadata; cardinality from 01_02_04 to be confirmed at audit runtime. Constants-detection branch overrides if n_distinct=1.",
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },
    "go_amm":              {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_battleNet":        {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_clientDebugFlags": {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_competitive":      {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_cooperative":      {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_fog":              {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_heroDuplicatesAllowed": {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_lockTeams":        {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_noVictoryOrDefeat":{"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_observers":        {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_practice":         {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_randomRaces":      {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_teamsTogether":    {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "go_userDifficulty":   {"mechanism": "MAR", "justification": "Game option metadata; constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},

    # All other columns default to spec absence → conservative MAR fallback;
    # constants-detection branch overrides for any n_distinct=1 column.
}
```

**Per-VIEW target sets (used by target-override post-step — B4 fix):**
- matches_flat_clean target = `{"result"}`
- player_history_all target = `{"result"}`

### 2.B — aoestats `_missingness_spec`

```python
_missingness_spec = {
    # Identity / target — handled by S1/S2 zero-NULL assertions; no spec entry

    # Pre-game ratings (sentinel-encoded missingness)
    # B2 fix: spec covers `0` (unrated sentinel); negative range surfaced as
    # DS-AOESTATS-02 (separate downstream investigation).
    "p0_old_rating": {
        "mechanism": "MAR",
        "justification": (
            "Pre-game rating; 0 is the unrated sentinel. "
            "01_02_04 numeric_stats_players[label='old_rating'] reports "
            "min_val=0, max_val=3045, n_zero=5,937; consistent with "
            "players_raw_census.old_rating.zero_count=5,937 (zero_pct=0.0055%). "
            "No negative values exist in old_rating (the negative range -5..-1 "
            "appears only in new_rating, which is POST-GAME and excluded per I3). "
            "Disposition surfaced as DS-AOESTATS-02."
        ),
        "sentinel_value": 0,
        "carries_semantic_content": True,
        "is_primary_feature": True,
    },
    "p1_old_rating": {
        "mechanism": "MAR",
        "justification": "Symmetric to p0_old_rating.",
        "sentinel_value": 0,
        "carries_semantic_content": True,
        "is_primary_feature": True,
    },
    "team_0_elo": {
        "mechanism": "MCAR",
        "justification": "ELO=-1 sentinel = isolated parse failures. 01_02_04 census min=-1, n_zero=4824.",
        "sentinel_value": -1,
        "carries_semantic_content": False,
        "is_primary_feature": True,
    },
    "team_1_elo": {
        "mechanism": "MCAR",
        "justification": "Symmetric to team_0_elo. 01_02_04 census min=-1, n_zero=192.",
        "sentinel_value": -1,
        "carries_semantic_content": False,
        "is_primary_feature": True,
    },
    "avg_elo": {
        "mechanism": "MAR",
        "justification": (
            "01_02_04 numeric_stats_matches[label='avg_elo'] reports min_val=0, "
            "max_val=2976.5, n_zero=121 (~0.0004% of 30,690,651 matches_raw rows). "
            "Disposition (genuine zero vs sentinel) deferred to 01_04_02+ join "
            "investigation (DS-AOESTATS-03). Note: the n_zero=4,824 figure cited "
            "in earlier drafts belongs to team_0_elo, NOT avg_elo."
        ),
        "sentinel_value": 0,
        "carries_semantic_content": True,
        "is_primary_feature": True,
    },

    # MCAR / low-rate columns
    "raw_match_type": {
        "mechanism": "MCAR",
        "justification": "matches_raw_census.raw_match_type.null_count=12,504 (~0.04% of matches_raw). Actual NULL count in matches_1v1_clean (filtered scope) computed at audit runtime by Pass 1; static figure here is raw-table reference. Source: 01_02_04 matches_raw_census.",
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },

    # NOTE: matches_1v1_clean has NO `winner` column. The actual columns are:
    #   - team1_wins (BIGINT, prediction target, 0 NULLs guaranteed by upstream
    #     `WHERE p0.winner != p1.winner`)
    #   - p0_winner, p1_winner (BOOLEAN source columns, 0 NULLs verified)
    # All three follow the F1 zero-missingness override under Option B → ledger
    # reports RETAIN_AS_IS / mechanism=N/A. The previous v1 spec comment that
    # mentioned `winner` is removed (B1 fix).
}
```

**Per-VIEW target sets (used by target-override post-step — B4 fix):**
- matches_1v1_clean target = `{"team1_wins"}` (the BIGINT prediction target)
- player_history_all target = `{"winner"}` (the BOOLEAN match-result column carried in player history)

(Note: `p0_winner` and `p1_winner` in matches_1v1_clean are source-of-truth booleans, not the prediction target; they are not in the target set.)

**Critique-v3 / v2 fixes baked in:**
- **B1 (winner column references):** removed; matches_1v1_clean has team1_wins (target) + p0_winner/p1_winner (source). All three covered by F1 zero-missingness override under Option B.
- **B2 (old_rating sentinel range):** spec covers `0` (the unrated sentinel) only — no negatives exist in old_rating. Cited 01_02_04 ground truth (verified): `numeric_stats_players[label='old_rating'].min_val=0, n_zero=5,937` (consistent with `players_raw_census.old_rating.zero_count=5,937`). The `min=-5, n_zero=5,187` figures cited in v2 belong to `new_rating` (POST-GAME, excluded per I3) and have been removed.
- **F1 (phantom NULL):** the audit code overrides justification to `"Zero missingness observed; no action needed."` whenever `n_total_missing == 0`.
- **F2 (winner forced to MAR):** removed in v3; verified absent — Deliverable 7 gate adds an explicit grep verification step (NOTE-2).
- **W1 (sentinel invisibility):** team_0_elo/team_1_elo, p0_old_rating/p1_old_rating, avg_elo all carry explicit sentinel_value entries.
- **W2 (raw_match_type):** explicitly MCAR, not N/A.
- **W3 (overviews_raw):** documented as out-of-scope in `decisions_surfaced` (DS-AOESTATS-07), not in `_missingness_spec`.

### 2.C — aoe2companion `_missingness_spec` (W2 fix — Group C enumerated)

```python
_missingness_spec = {
    # Pre-game rating (primary feature, exception per S4)
    "rating": {
        "mechanism": "MAR",
        "justification": (
            "Unranked matches lack rating. In matches_1v1_clean (ranked scope), "
            "effective NULL rate is ~26% — primary feature, not dropped per Rule "
            "S4 exception. The matches_1v1_clean VIEW asserts `rating >= 0` "
            "upstream, so the -1 sentinel is filtered before the audit sees it; "
            "n_sentinel=0 in the ledger reflects upstream filtering, not absence "
            "of the encoding. Source: 01_03_03 + this audit."
        ),
        "sentinel_value": None,
        "carries_semantic_content": True,
        "is_primary_feature": True,
    },

    # Player metadata
    "country": {
        "mechanism": "MAR",
        "justification": "Player chose not to disclose country. Source: 01_02_04 distribution.",
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },

    # Target column (matches_1v1_clean has 0 NULLs by R03; player_history_all has ~5%)
    "won": {
        "mechanism": "MAR",
        "justification": (
            "Unranked / unknown leaderboards lack won. Excluded from prediction "
            "scope (matches_1v1_clean enforces via R03); retained in "
            "player_history_all for feature computation. Source: 01_03_02 + R03."
        ),
        "sentinel_value": None,
        "carries_semantic_content": False,  # NEVER imputed (target — handled by target-override post-step)
        "is_primary_feature": False,
    },

    # Game-settings group A: structurally absent (ranked 1v1 via API version)
    "server": {
        "mechanism": "MNAR",
        "justification": "Structurally absent for certain API versions. 01_02_04 reports null_pct=97.99%.",
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },
    "modDataset": {
        "mechanism": "MAR",
        "justification": "Scenario-specific; absent for ranked random map. 01_02_04 reports null_pct=99.72%.",
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },
    "scenario": {
        "mechanism": "MAR",
        "justification": "Custom scenario only; absent for ranked random map. 01_02_04 reports null_pct=98.27%.",
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },
    "password": {
        "mechanism": "MAR",
        "justification": "Password-protected lobbies only. 01_02_04 reports null_pct=82.90%.",
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },

    # Game-settings group B: schema-evolution (patch-dependent) — B3 fix:
    # 01_02_04 evidence ALONE; no future-step references.
    "antiquityMode": {
        "mechanism": "MAR",
        "justification": (
            "Schema-evolution column: introduced in a later patch; missingness "
            "depends on observed match patch (a recorded variable). 01_02_04 "
            "reports null_pct=68.66%."
        ),
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },
    "hideCivs": {
        "mechanism": "MAR",
        "justification": "Schema-evolution column (patch-dependent). 01_02_04 reports null_pct=49.30%.",
        "sentinel_value": None,
        "carries_semantic_content": False,
        "is_primary_feature": False,
    },

    # Group C — low-NULL game settings (W2 fix: every column individually
    # enumerated). Each gets a one-liner justification grounded in 01_02_04.
    # Constants-detection branch (W7) overrides for any n_distinct=1 column.
    # Template: "Group C low-NULL game setting; 01_02_04 reports null_pct=<pct>%.
    # Mechanism MAR (legitimate ranked-1v1 absence) per 01_02_04 evidence."
    "mod":              {"mechanism": "MAR", "justification": "Group C boolean game setting; 01_02_04 evidence — ranked-1v1 default. Constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "map":              {"mechanism": "MCAR", "justification": "Map name; near-zero null in ranked 1v1 scope per 01_02_04. Categorical feature.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "difficulty":       {"mechanism": "MAR", "justification": "AI difficulty; near-zero null in ranked-1v1 scope per 01_02_04. Constants-detection backstop applies (likely constant in ranked).", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "startingAge":      {"mechanism": "MAR", "justification": "Game setting; near-zero null in ranked-1v1 scope per 01_02_04. Constants-detection backstop applies.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "fullTechTree":     {"mechanism": "MAR", "justification": "Boolean game setting; 01_02_04 evidence — ranked-1v1 default.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "allowCheats":      {"mechanism": "MAR", "justification": "Boolean game setting; 01_02_04 evidence — ranked-1v1 default. NULL-cluster member (R04).", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "empireWarsMode":   {"mechanism": "MAR", "justification": "Boolean game mode; 01_02_04 evidence — variant indicator.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "endingAge":        {"mechanism": "MAR", "justification": "Game setting; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "gameMode":         {"mechanism": "MAR", "justification": "Game mode setting; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "lockSpeed":        {"mechanism": "MAR", "justification": "Boolean game setting; 01_02_04 evidence. NULL-cluster member.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "lockTeams":        {"mechanism": "MAR", "justification": "Boolean game setting; 01_02_04 evidence. NULL-cluster member.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "mapSize":          {"mechanism": "MAR", "justification": "Map size setting; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "population":       {"mechanism": "MAR", "justification": "Population cap; 01_02_04 evidence. NULL-cluster member.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "recordGame":       {"mechanism": "MAR", "justification": "Boolean game setting; 01_02_04 evidence. NULL-cluster member.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "regicideMode":     {"mechanism": "MAR", "justification": "Boolean game mode; 01_02_04 evidence — variant indicator.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "gameVariant":      {"mechanism": "MAR", "justification": "Game variant identifier; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "resources":        {"mechanism": "MAR", "justification": "Starting resources setting; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "sharedExploration":{"mechanism": "MAR", "justification": "Boolean game setting; 01_02_04 evidence. NULL-cluster member.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "speed":            {"mechanism": "MAR", "justification": "Game speed name; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "speedFactor":      {"mechanism": "MAR", "justification": "Game speed multiplier; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "suddenDeathMode":  {"mechanism": "MAR", "justification": "Boolean game mode; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "civilizationSet":  {"mechanism": "MAR", "justification": "Civilization-set restriction; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "teamPositions":    {"mechanism": "MAR", "justification": "Boolean game setting; 01_02_04 evidence. NULL-cluster member.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "teamTogether":     {"mechanism": "MAR", "justification": "Boolean game setting; 01_02_04 evidence. NULL-cluster member.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "treatyLength":     {"mechanism": "MAR", "justification": "Treaty duration; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "turboMode":        {"mechanism": "MAR", "justification": "Boolean game mode; 01_02_04 evidence. NULL-cluster member.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "victory":          {"mechanism": "MAR", "justification": "Victory condition; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "revealMap":        {"mechanism": "MAR", "justification": "Map reveal setting; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},

    # Player metadata (low-NULL):
    "color":            {"mechanism": "MCAR", "justification": "In-game color code; near-zero null per 01_02_04.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "colorHex":         {"mechanism": "MCAR", "justification": "Color as hex; near-zero null per 01_02_04.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "slot":             {"mechanism": "MCAR", "justification": "Player slot index; near-zero null per 01_02_04.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "status":           {"mechanism": "MCAR", "justification": "Player status; near-zero null per 01_02_04.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "team":             {"mechanism": "MAR", "justification": "Team number; sentinel 255 per matches_raw schema YAML notes.", "sentinel_value": 255, "carries_semantic_content": True, "is_primary_feature": False},
    "shared":           {"mechanism": "MAR", "justification": "Boolean shared-control flag; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "verified":         {"mechanism": "MAR", "justification": "Boolean verified flag; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "privacy":          {"mechanism": "MAR", "justification": "Privacy/visibility setting; 01_02_04 evidence.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},
    "name":             {"mechanism": "MCAR", "justification": "Display name; near-zero null per 01_02_04.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},

    # Derived flag from VIEW (R04 — already retained as feature):
    "is_null_cluster":  {"mechanism": "N/A", "justification": "Derived flag from VIEW DDL (R04). Always non-NULL by construction.", "sentinel_value": None, "carries_semantic_content": False, "is_primary_feature": False},

    # Identity columns (S1, no spec entry needed): matchId, started, profileId,
    # internalLeaderboardId, civ, filename — handled by zero-NULL assertions or
    # spec-fallback if non-zero rate observed.
}
```

**Per-VIEW target sets (used by target-override post-step — B4 fix):**
- matches_1v1_clean target = `{"won"}`
- player_history_all target = `{"won"}`

**Critique-v3 / v2 fixes baked in:**
- **W1 (Group C enumeration):** all ~33 game-settings columns now individually enumerated with 01_02_04-grounded justifications.
- **B3 (no future-step citation):** "+ 01_05 temporal panel evidence" struck from `antiquityMode` and `hideCivs`. Both grounded in 01_02_04 alone (verified: 68.66% / 49.30%).

---

## Deliverable 3 — Sentinel census + constants detection + override priority (DRY across datasets)

Same SQL pattern across all three notebooks. The Python wrapper varies in the source dict name (`_missingness_spec`) but the loop is identical.

**Connection convention (W4 fix — UNIFORM across all three datasets):**
- All three notebooks use `con = db.con` (public attribute) at the connection-acquisition cell, then `con.execute(...)` at every call site.
- **sc2egset notebook normalization scope:** ALL 58 existing `con.con.execute(...)` calls in earlier cells are converted to `con.execute(...)`. The connection-acquisition cell is renamed two-step: `con = get_notebook_db("sc2", "sc2egset", read_only=False)` becomes `db = get_notebook_db("sc2", "sc2egset", read_only=False)` followed by `con = db.con` (see Deliverable 4.A cell 3 for explicit instruction).
- **aoestats notebook:** changes `con = db._con` (private attribute) to `con = db.con` (public attribute). Existing `con.execute(...)` call sites stay unchanged because the resulting `con` object exposes the same `.execute()` method.
- **aoe2companion notebook:** already uses `con = db.con` and `con.execute(...)`. No change needed.
- **Rationale:** public attribute is the stable API; private attribute is brittle (breaks on any wrapper refactor). Cross-game uniformity supports Invariant I8 / Rule S6.

```python
def _build_sentinel_predicate(col: str, sentinel_value):
    """Construct the SQL predicate for sentinel matching.

    Returns (predicate_sql, sentinel_repr) or (None, None) when no sentinel declared.
    """
    if sentinel_value is None:
        return None, None
    if isinstance(sentinel_value, list):
        quoted = []
        for v in sentinel_value:
            if isinstance(v, str):
                quoted.append("'" + v.replace("'", "''") + "'")
            else:
                quoted.append(repr(v))
        return f'IN ({", ".join(quoted)})', repr(sentinel_value)
    if isinstance(sentinel_value, str):
        escaped = sentinel_value.replace("'", "''")
        return f"= '{escaped}'", repr(sentinel_value)
    return f"= {sentinel_value!r}", repr(sentinel_value)


def _sentinel_census(view_name: str, total_rows: int, spec: dict) -> list[dict]:
    """Run sentinel COUNT(*) FILTER per spec'd column. Returns list of dicts."""
    rows = []
    for col, meta in spec.items():
        sentinel_value = meta["sentinel_value"]
        predicate, sentinel_repr = _build_sentinel_predicate(col, sentinel_value)
        if predicate is None:
            n_sentinel = 0
        else:
            sql = f'SELECT COUNT(*) FILTER (WHERE "{col}" {predicate}) FROM {view_name}'
            n_sentinel = con.execute(sql).fetchone()[0]   # uniform across datasets (W4 fix)
        pct_sentinel = round(100.0 * n_sentinel / total_rows, 4) if total_rows > 0 else 0.0
        rows.append({
            "column": col,
            "sentinel_value": sentinel_repr,
            "n_sentinel": int(n_sentinel),
            "pct_sentinel": float(pct_sentinel),
        })
    return rows


def _detect_constants(view_name: str, columns: list[str], identity_cols: set[str] = frozenset()) -> dict:
    """Per-column n_distinct check. Returns {col: n_distinct}.

    W6 mitigation: identity columns (e.g. replay_id, profile_id, game_id, matchId)
    are skipped (they are never constant by definition; COUNT(DISTINCT) on them is
    expensive on player_history_all-scale tables). For non-identity columns,
    APPROX_COUNT_DISTINCT could be substituted to reduce wall-clock at the cost of
    an O(1)-vs-exact tradeoff — exact is used here because the constants check
    requires exact equality with 1, and the runtime budget for the three datasets
    is acceptable (estimated ≤30 minutes per dataset for the full audit on
    player_history_all-scale tables).
    """
    out = {}
    for col in columns:
        if col in identity_cols:
            out[col] = None  # skipped; constants check N/A
            continue
        sql = f'SELECT COUNT(DISTINCT "{col}") FROM {view_name}'
        out[col] = int(con.execute(sql).fetchone()[0])
    return out
```

**W6 runtime budget (informational):** for aoestats player_history_all (~107.6M
rows × 13 cols), each `COUNT(DISTINCT col)` on a high-cardinality column may take
30-90s on a single machine. Worst-case audit runtime per dataset is ~30 minutes
when constants-detection is included. Identity columns are skipped via the
`identity_cols` parameter (sc2egset: `{replay_id, toon_id}`; aoestats:
`{game_id, profile_id}`; aoe2companion: `{matchId, profileId}`). Future: consider
swapping to `APPROX_COUNT_DISTINCT` for non-identity columns if the budget is
exceeded.

**Ledger consolidation pattern (DRY) — with B4 + W6 + W7 fixes:**

```python
def _consolidate_ledger(view_name: str, df_null: pd.DataFrame, sentinel_rows: list[dict],
                         spec: dict, dtype_map: dict, total_rows: int,
                         constants_map: dict, target_cols: set[str],
                         identity_cols: set[str] = frozenset()) -> pd.DataFrame:
    """Merge NULL census + sentinel census + constants detection + spec → one
    ledger row per (view, column). Full-coverage scope (Option B per user
    decision). identity_cols are routed to a dedicated branch (B5 fix) to
    avoid the n_distinct=None comparison instability."""
    sentinel_map = {r["column"]: r for r in sentinel_rows}
    ledger = []
    for _, nrow in df_null.iterrows():
        col = nrow["column_name"] if "column_name" in nrow else nrow["column"]
        n_null = int(nrow["null_count"])
        pct_null = float(nrow.get("null_pct", round(100.0 * n_null / total_rows, 4)))
        srow = sentinel_map.get(col, {"sentinel_value": None, "n_sentinel": 0, "pct_sentinel": 0.0})
        n_sentinel = int(srow["n_sentinel"])
        pct_sentinel = float(srow["pct_sentinel"])
        n_total_missing = n_null + n_sentinel
        pct_missing_total = round(pct_null + pct_sentinel, 4)
        spec_entry = spec.get(col)
        n_distinct = constants_map.get(col, None)

        # Override priority (B4 + B5 + W7):
        #   0. Identity-column branch (B5 fix): n_distinct skipped per W6 — route
        #      explicitly to mechanism=N/A, recommendation=RETAIN_AS_IS.
        #   1. Constants override (W7): n_distinct == 1 AND zero NULLs AND zero
        #      sentinels → DROP_COLUMN, mechanism=N/A
        #   2. F1 zero-missingness override: n_total_missing == 0 → RETAIN_AS_IS,
        #      mechanism=N/A
        #   3. Spec / fallback recommendation
        #   4. Target-column post-step (B4): if col in target_cols AND
        #      n_total_missing > 0, override recommendation to EXCLUDE_TARGET_NULL_ROWS

        # B5 fix: identity columns are routed first (W6 skipped n_distinct for them,
        # leaving n_distinct=None which would otherwise cause pandas dtype-dependent
        # NA propagation in the assertion battery).
        if col in identity_cols:
            mechanism = "N/A"
            mech_just = (
                f"Identity column; n_distinct check skipped per W6 (constants-detection "
                f"runtime budget). Zero NULLs by definition (asserted upstream)."
            )
            carries_sem = False
            is_primary = False
            rec = "RETAIN_AS_IS"
            rec_just = "Identity column; no missingness possible by upstream assertion."
        # W1 fix: TRUE-constants check requires zero NULLs AND zero sentinels.
        # SQL COUNT(DISTINCT) excludes NULLs, so a 99%-NULL column with 1% one
        # value would otherwise be misclassified as a "constant" — but it has
        # missingness signal usable as add_indicator. Tighter guard prevents
        # category errors against high-NULL near-constants like aoe2companion
        # `password` (82.9% NULL).
        # NOTE: chained `elif` — the identity branch above MUST short-circuit
        # the rest of the chain for identity columns (B5 fix).
        elif n_distinct == 1 and n_null == 0 and n_sentinel == 0:
            mechanism = "N/A"
            mech_just = (
                f"True constant column; n_distinct=1 across {total_rows:,} rows "
                f"(zero NULLs, zero sentinels). No information content for prediction. "
                f"Recommend drop in 01_04_02+."
            )
            carries_sem = False
            is_primary = False  # W8 fix
            rec = "DROP_COLUMN"
            rec_just = "True constant column; n_distinct=1; no information content."
        elif n_total_missing == 0:
            mechanism = "N/A"
            mech_just = "Zero missingness observed; no action needed."
            carries_sem = bool(spec_entry["carries_semantic_content"]) if spec_entry else False
            is_primary = bool(spec_entry["is_primary_feature"]) if spec_entry else False  # W8 fix
            rec = "RETAIN_AS_IS"
            rec_just = "Zero missingness observed; no action needed."
        elif spec_entry is not None:
            mechanism = spec_entry["mechanism"]
            mech_just = spec_entry["justification"]
            carries_sem = bool(spec_entry["carries_semantic_content"])
            is_primary = bool(spec_entry["is_primary_feature"])
            rec, rec_just = _recommend(col, mechanism, pct_missing_total,
                                       is_primary, n_null, n_sentinel)
        else:
            mechanism = "MAR"
            mech_just = (
                f"No _missingness_spec entry; conservative MAR assumption. "
                f"Observed effective missingness {pct_missing_total:.2f}% "
                f"(NULL: {pct_null:.2f}%, sentinel: {pct_sentinel:.2f}%)."
            )
            carries_sem = False
            is_primary = False
            rec, rec_just = _recommend(col, mechanism, pct_missing_total,
                                       is_primary, n_null, n_sentinel)

        # Target-column post-step (B4 fix): fires only when the column is in
        # the per-VIEW target set AND has semantic missingness. Otherwise the
        # F1 zero-missingness override (or earlier branches) wins.
        if col in target_cols and n_total_missing > 0:
            rec = "EXCLUDE_TARGET_NULL_ROWS"
            rec_just = (
                "Per Rule S2: target NULLs/sentinels excluded from prediction "
                "scope, retained in history for feature computation. "
                "NEVER impute target."
            )

        ledger.append({
            "view": view_name,
            "column": col,
            "dtype": dtype_map.get(col, "UNKNOWN"),
            "n_total": int(total_rows),
            "n_null": n_null, "pct_null": pct_null,
            "sentinel_value": srow["sentinel_value"],
            "n_sentinel": n_sentinel, "pct_sentinel": pct_sentinel,
            "pct_missing_total": pct_missing_total,
            "n_distinct": n_distinct,
            "mechanism": mechanism,
            "mechanism_justification": mech_just,
            "recommendation": rec,
            "recommendation_justification": rec_just,
            "carries_semantic_content": carries_sem,
            "is_primary_feature": is_primary,  # W8 fix: surfaced for downstream Phase 02 consumption
        })
    return pd.DataFrame(ledger)


def _recommend(col: str, mechanism: str, pct: float, is_primary: bool,
               n_null: int, n_sentinel: int) -> tuple[str, str]:
    """Decision tree per temp/null_handling_recommendations.md §3.1.
    Returns (recommendation_code, justification_text). Identity/target columns are
    handled by zero-NULL assertions and the target-override post-step,
    respectively."""
    # W3 fix: CONVERT_SENTINEL_TO_NULL branch — fires for sentinel-only,
    # low-rate cases (n_sentinel > 0 AND n_null == 0 AND pct < 5%).
    #
    # B6 deferral (Option D): this branch fires regardless of
    # carries_semantic_content. For columns where the spec marks
    # carries_semantic_content=True (e.g., aoestats p0_old_rating /
    # p1_old_rating / avg_elo, sc2egset handicap / APM), the recommendation
    # is NON-BINDING. The corresponding DS entries (DS-AOESTATS-02,
    # DS-AOESTATS-03, DS-SC2-09, DS-SC2-10) explicitly surface the
    # alternative arm (retain-as-category vs convert-and-drop) for 01_04_02+
    # to choose. The ledger row carries both `recommendation` and
    # `carries_semantic_content` so the downstream step has both signals.
    if n_sentinel > 0 and n_null == 0 and pct < 5.0:
        return "CONVERT_SENTINEL_TO_NULL", (
            f"Low sentinel rate ({pct:.4f}%); convert sentinel to NULL via "
            f"NULLIF in 01_04_02+ DDL pass per Rule S3 (negligible rate). "
            f"Listwise deletion or simple imputation acceptable in Phase 02. "
            f"NOTE: if carries_semantic_content=True (consult ledger column), "
            f"this recommendation is non-binding — see corresponding DS entry "
            f"for the retain-as-category alternative."
        )
    if pct == 0.0:
        return "RETAIN_AS_IS", "Zero missingness observed; no action needed."
    if pct > 80.0:
        return "DROP_COLUMN", (
            f"NULL+sentinel rate {pct:.2f}% exceeds 80% (Rule S4 / van Buuren 2018). "
            f"Imputation indefensible at this rate."
        )
    if pct > 40.0:
        if mechanism == "MNAR":
            return "DROP_COLUMN", (
                f"Rate {pct:.2f}% in 40-80% MNAR band; no defensible imputation. "
                f"Drop unless domain knowledge provides correction."
            )
        if is_primary:
            return "FLAG_FOR_IMPUTATION", (
                f"Rate {pct:.2f}% in 40-80%; primary feature exception per Rule S4. "
                f"Phase 02: conditional imputation + add_indicator."
            )
        return "DROP_COLUMN", (
            f"Rate {pct:.2f}% in 40-80%; non-primary feature; cost/benefit favors "
            f"simplicity per Rule S4."
        )
    if pct > 5.0:
        return "FLAG_FOR_IMPUTATION", (
            f"Rate {pct:.2f}% in 5-40%; flag for Phase 02 imputation "
            f"(conditional for MAR, simple for MCAR per Rules from §3.1)."
        )
    # pct < 5%, with at least one NULL (sentinel-only case handled above)
    return "RETAIN_AS_IS", (
        f"Rate {pct:.2f}% < 5% (Schafer & Graham 2002 boundary citation). "
        f"Listwise deletion or simple imputation acceptable in Phase 02."
    )
```

**Override priority summary (B4 + W7):**
1. **Constants detection (W7):** if `n_distinct == 1` → mechanism=N/A, recommendation=DROP_COLUMN.
2. **F1 zero-missingness:** if `n_total_missing == 0` → mechanism=N/A, recommendation=RETAIN_AS_IS.
3. **Spec / fallback recommendation** via `_recommend()` (which itself includes the W3 `CONVERT_SENTINEL_TO_NULL` branch as the first arm).
4. **Target-column post-step (B4):** if `col in target_cols AND n_total_missing > 0` → recommendation=EXCLUDE_TARGET_NULL_ROWS (overrides whatever step 3 produced).

**Per-VIEW target sets (passed to `_consolidate_ledger`):**
- sc2egset matches_flat_clean: `{"result"}` (always 0 NULLs after 1v1_decisive filter → F1 wins → RETAIN_AS_IS, target post-step does NOT fire)
- sc2egset player_history_all: `{"result"}` (Undecided/Tie present → spec → MNAR → 5-40% branch → FLAG_FOR_IMPUTATION → target post-step OVERRIDES → EXCLUDE_TARGET_NULL_ROWS)
- aoestats matches_1v1_clean: `{"team1_wins"}` (0 NULLs → F1 wins → RETAIN_AS_IS)
- aoestats player_history_all: `{"winner"}` (NULLs present → target post-step fires → EXCLUDE_TARGET_NULL_ROWS)
- aoe2companion matches_1v1_clean: `{"won"}` (0 NULLs by R03 → F1 wins → RETAIN_AS_IS)
- aoe2companion player_history_all: `{"won"}` (~5% NULL → target post-step fires → EXCLUDE_TARGET_NULL_ROWS)

**Special-case overrides (per dataset):**
- **sc2egset:** `gd_mapAuthorName` gets `DROP_COLUMN` regardless of rate per the explicit non-predictiveness override (already in v3 plan).

---

## Deliverable 4 — Notebook structure (cells in order)

Each notebook keeps all existing cells. The audit refactor is **additive** with the spec-driven sentinel pass + constants-detection pass slotted between the existing NULL census and the existing artifact-write cells. The same five-cell insertion pattern applies to all three notebooks; only the body differs. The W4 connection-style normalization is applied across ALL existing cells in sc2egset and the connection-acquisition cell in aoestats.

### 4.A — sc2egset notebook (`sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_01_data_cleaning.py`)

| # | Cell | Status | One-line description |
|---|------|--------|----------------------|
| 1 | Header markdown | existing-keep | Step header, invariants, scope. |
| 2 | Imports | existing-keep | Imports + logger setup. |
| 3 | DuckDB writable connection | existing-modify (W4 + W5) | **Two-step rename:** (1) rename the existing line `con = get_notebook_db("sc2", "sc2egset", read_only=False)` → `db = get_notebook_db("sc2", "sc2egset", read_only=False)`; (2) add new line immediately after: `con = db.con`. The variable `db` (wrapper) replaces `con` (was-wrapper-now-connection). All subsequent cells now use `con.execute(...)` (the raw DuckDB connection). DO NOT mechanically insert `con = db.con` after the existing `con = get_notebook_db(...)` — that would double-bind `con` and break later `con.con.execute(...)` calls. |
| 4–14 | matches_flat VIEW + validation + MMR/selectedRace/SQ/APM/map/handicap analysis | existing-modify (W4) | All `con.con.execute(...)` calls → `con.execute(...)`. |
| 15 | matches_flat_clean VIEW DDL | existing-modify (W4) | Same. |
| 16 | matches_flat_clean validation | existing-modify (W4) | Same. |
| 17 | player_history_all VIEW DDL | existing-modify (W4) | Same. |
| 18 | player_history_all validation | existing-modify (W4) | Same. |
| 19 | CONSORT flow | existing-modify (W4) | Same. |
| 20 | Post-cleaning validation | existing-modify (W4) | Same. |
| 21 | Column exclusion assertion | existing-modify (W4) | Same. |
| 22 | player_history_all structural checks | existing-modify (W4) | Same. |
| 23 | NULL audit: matches_flat_clean (Pass 1) | existing-modify (W4) | Same. |
| 24 | NULL audit: player_history_all (Pass 1) | existing-modify (W4) | Same. |
| 25 | **NEW: Markdown — Missingness Audit framing** | new-insert | Cites Rubin 1976, Little & Rubin 2019, van Buuren 2018, Sambasivan 2021, Schafer & Graham 2002 (boundary). States Phase 01 documents only (I9). States the audit feeds three coordinated steps (NULL census + sentinel census + constants detection). |
| 26 | **NEW: `_missingness_spec` dict + helpers** | new-insert | Defines spec (Deliverable 2.A), `_build_sentinel_predicate`, `_sentinel_census`, `_detect_constants`, `_consolidate_ledger`, `_recommend`. |
| 27 | **NEW: Pass 2 sentinel census + constants detection + ledger for matches_flat_clean** | new-insert | Calls `_sentinel_census(...)`, `_detect_constants(..., identity_cols={"replay_id", "toon_id"})`, `_consolidate_ledger(..., target_cols={"result"}, identity_cols={"replay_id", "toon_id"})`; stores `df_ledger_mfc`; prints summary. |
| 28 | **NEW: Pass 2 sentinel + constants + ledger for player_history_all** | new-insert | Same for player_history_all → `df_ledger_hist`, `target_cols={"result"}`, `identity_cols={"replay_id", "toon_id"}`. |
| 29 | **NEW: Decisions surfaced markdown** | new-insert | Reproduces DS-SC2-01..10 (DS-SC2-09 / DS-SC2-10 added per B6 deferral for handicap / APM). |
| 30 | Produce JSON artifact | existing-modify | Add `artifact["missingness_audit"]` block. |
| 31 | **NEW: Write missingness ledger CSV+JSON** | new-insert | Concatenate `df_ledger_mfc` + `df_ledger_hist`, write to `01_04_01_missingness_ledger.csv` and `.json`. |
| 32 | Write MD artifact | existing-modify | Add "Missingness Ledger" subsection per VIEW + "Decisions surfaced" closing section. |
| 33 | Write schema YAML for player_history_all | existing-keep | Untouched. |
| 34 | Close connection | existing-keep | Untouched. |

### 4.B — aoestats notebook (`sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_01_data_cleaning.py`)

Same pattern. The only existing-cell modification besides the W4 connection acquisition (line 51: `con = db._con` → `con = db.con`) is the artifact-write cell (which becomes additive).

| # | Cell | Status | Description |
|---|------|--------|-------------|
| ... connection cell (line ~51) | existing-modify (W4) | `con = db._con` → `con = db.con`. |
| ... T01–T08 + NULL census | existing-keep | All `con.execute(...)` calls already conformant. |
| ~37 | **NEW: Missingness audit framing markdown** | new-insert | Same framing as sc2egset cell 25. |
| ~38 | **NEW: `_missingness_spec` + helpers** | new-insert | Deliverable 2.B + DRY helpers. |
| ~39 | **NEW: Pass 2 sentinel + constants + ledger for matches_1v1_clean** | new-insert | `target_cols={"team1_wins"}`, `identity_cols={"game_id"}` → `df_ledger_m1`. |
| ~40 | **NEW: Pass 2 sentinel + constants + ledger for player_history_all** | new-insert | `target_cols={"winner"}`, `identity_cols={"game_id", "profile_id"}` → `df_ledger_ph`. |
| ~41 | **NEW: Decisions surfaced markdown** | new-insert | DS-AOESTATS-01..07. |
| ~42 | Artifact JSON | existing-modify | Add `artifact["missingness_audit"]` block. |
| ~43 | **NEW: Write ledger CSV+JSON** | new-insert | Same as sc2egset cell 31. |
| ~44 | Artifact MD | existing-modify | Add Missingness Ledger + Decisions sections. |
| ~45 | Final print | existing-keep | Untouched. |

### 4.C — aoe2companion notebook (`sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_01_data_cleaning.py`)

Same pattern. Connection-acquisition cell already conformant (`con = db.con`).

| # | Cell | Status | Description |
|---|------|--------|-------------|
| ... T01–T08, V1–V8, NULL census | existing-keep | All `con.execute(...)` calls already conformant. |
| ~33 | **NEW: Missingness audit framing markdown** | new-insert | Same pattern. |
| ~34 | **NEW: `_missingness_spec` + helpers** | new-insert | Deliverable 2.C. |
| ~35 | **NEW: Pass 2 sentinel + constants + ledger for matches_1v1_clean** | new-insert | `target_cols={"won"}`, `identity_cols={"matchId"}`. Place inside the `db` writable context (before `db.close()`). |
| ~36 | **NEW: Pass 2 sentinel + constants + ledger for player_history_all** | new-insert | `target_cols={"won"}`, `identity_cols={"matchId", "profileId"}`. |
| ~37 | **NEW: Decisions surfaced markdown** | new-insert | DS-AOEC-01..08. |
| ~38–end | Artifact rebuild + writes | existing-modify | Add `artifact["missingness_audit"]` block in the JSON build; add ledger CSV+JSON writes; add Missingness Ledger + Decisions + rate-disambiguation note to MD. |

---

## Deliverable 5 — Missingness ledger artifact schema and path

### 5.A — File paths

Per dataset, two new files:

```
src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv
src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.json

src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv
src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.json

src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv
src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.json
```

The existing `01_04_01_data_cleaning.json` continues to exist; the new `missingness_audit` block is added inside it AND the consolidated ledger is also emitted as standalone CSV+JSON.

### 5.B — CSV column list (identical across datasets)

```
view, column, dtype,
n_total, n_null, pct_null,
sentinel_value, n_sentinel, pct_sentinel,
pct_missing_total,
n_distinct,
mechanism, mechanism_justification,
recommendation, recommendation_justification,
carries_semantic_content,
is_primary_feature
```

17 columns (added `n_distinct` for the constants-detection branch and `is_primary_feature` per W8 fix — surfaced from spec for downstream Phase 02 consumption). **One row per (view, column) — full coverage (Option B per user decision).** Every column in each VIEW is represented. Columns with zero missingness are emitted with `mechanism = "N/A"`, `recommendation = "RETAIN_AS_IS"`. Constant columns are emitted with `mechanism = "N/A"`, `recommendation = "DROP_COLUMN"`. Identity columns (B5 fix) are emitted with `mechanism = "N/A"`, `recommendation = "RETAIN_AS_IS"`, `n_distinct = null` (skipped per W6 budget).

**Cross-dataset comparability note (NOTE-1):** Ledgers are not directly joinable across datasets due to dataset-specific column names — Phase 02 introduces a feature-category taxonomy that maps {MMR (sc2), team_0_elo (aoestats), rating (aoe2companion)} → 'pre-game skill rating' for cross-game analysis. The audit's per-dataset scope is appropriate for 01_04 cleaning decisions; cross-game alignment is a Phase 02 concern.

### 5.C — JSON shape

```json
{
  "step": "01_04_01",
  "dataset": "<sc2egset | aoestats | aoe2companion>",
  "generated_date": "<ISO date>",
  "framework": {
    "source_doc": "temp/null_handling_recommendations.md",
    "rules_applied": ["S1", "S2", "S3", "S4", "S5", "S6"],
    "mechanism_taxonomy": "Rubin (1976); Little & Rubin (2019, 3rd ed.)",
    "phase_boundary": "Phase 01 documents (I9). Phase 02 transforms.",
    "thresholds": {
      "low_rate_pct": 5.0,
      "mid_rate_pct": 40.0,
      "high_rate_pct": 80.0,
      "threshold_source": "Operational starting heuristics from temp/null_handling_recommendations.md §1.2; <5% MCAR boundary citation: Schafer & Graham 2002; warning against rigid global thresholds: van Buuren 2018"
    },
    "override_priority": [
      "1. Constants detection (n_distinct == 1) → mechanism=N/A, recommendation=DROP_COLUMN",
      "2. F1 zero-missingness (n_total_missing == 0) → mechanism=N/A, recommendation=RETAIN_AS_IS",
      "3. _recommend() per spec/fallback (incl. CONVERT_SENTINEL_TO_NULL for sentinel-only low-rate cases)",
      "4. Target-column post-step (col in target_cols AND n_total_missing > 0) → recommendation=EXCLUDE_TARGET_NULL_ROWS"
    ],
    "per_view_target_cols": {
      "<view_name>": ["<col>", "..."]
    }
  },
  "missingness_spec": { /* the _missingness_spec dict verbatim */ },
  "ledger": [
    {
      "view": "matches_flat_clean",
      "column": "MMR",
      "dtype": "INTEGER",
      "n_total": 44418,
      "n_null": 0,
      "pct_null": 0.0,
      "sentinel_value": "0",
      "n_sentinel": 37422,
      "pct_sentinel": 84.25,
      "pct_missing_total": 84.25,
      "n_distinct": 1234,
      "mechanism": "MAR",
      "mechanism_justification": "MAR-primary: missingness depends on observed replay source ...",
      "recommendation": "DROP_COLUMN",
      "recommendation_justification": "NULL+sentinel rate 84.25% exceeds 80% (Rule S4 / van Buuren 2018). Imputation indefensible at this rate.",
      "carries_semantic_content": true,
      "is_primary_feature": true
    }
    /* ... one row per column per VIEW (full coverage); zero-missingness rows
       tagged RETAIN_AS_IS / mechanism="N/A"; constant columns tagged
       DROP_COLUMN / mechanism="N/A" ... */
  ],
  "decisions_surfaced": [
    {
      "id": "DS-SC2-01",
      "column": "MMR",
      "observed_pct_missing_total": 84.25,
      "question": "Convert MMR=0 to NULL and drop the column from matches_flat_clean ..."
    }
  ]
}
```

### 5.D — Inline `missingness_audit` block in `01_04_01_data_cleaning.json` (additive)

Existing JSON already has `null_audit`. Add sibling key `missingness_audit` containing the same `framework` + `missingness_spec` + per-VIEW `ledger` arrays + `override_priority` + `per_view_target_cols`. The standalone ledger files are a convenience for downstream programmatic consumption.

The recommendation enum used in both `5.B` ledger and `5.C/5.D` JSON includes **all five values**:
- `DROP_COLUMN`
- `FLAG_FOR_IMPUTATION`
- `RETAIN_AS_IS`
- `EXCLUDE_TARGET_NULL_ROWS`
- `CONVERT_SENTINEL_TO_NULL` (W3 fix — new branch)

---

## Deliverable 6 — Test/assertion list per notebook

These are inline `assert` statements in the audit cells and in the artifact-write cells. Each notebook gets the same assertion battery (with dataset-specific identity/target column lists):

### 6.A — Pre-existing assertions (must continue to pass)

- **All notebooks:** zero-NULL identity assertions (replay_id/toon_id/result for sc2; game_id/started_timestamp/p0_profile_id/p1_profile_id/p0_winner/p1_winner for aoestats; matchId/profileId/started for aoe2companion). All currently pass; the refactor must not break them.
- **All notebooks:** existing CONSORT arithmetic, existing Vn validations.

### 6.B — New assertions (one battery per notebook, applied to each ledger)

```python
# Spec coverage: every ledger column has a non-empty mechanism justification
for _, row in df_ledger.iterrows():
    assert row["mechanism"] in {"MAR", "MCAR", "MNAR", "N/A"}, row.to_dict()
    assert row["mechanism_justification"], f"empty mechanism justification for {row['column']}"
    assert row["recommendation"] in {
        "DROP_COLUMN", "FLAG_FOR_IMPUTATION", "RETAIN_AS_IS",
        "EXCLUDE_TARGET_NULL_ROWS", "CONVERT_SENTINEL_TO_NULL"
    }, row.to_dict()
    assert row["recommendation_justification"], row.to_dict()
    assert isinstance(row["carries_semantic_content"], (bool, np.bool_)), row.to_dict()

# Spec dict completeness for sentinel-bearing columns
spec_cols_with_sentinel = {c for c, m in _missingness_spec.items() if m["sentinel_value"] is not None}
sentinel_row_cols = {r["column"] for r in sentinel_rows_mfc + sentinel_rows_hist}
missing_in_sentinel_pass = spec_cols_with_sentinel - sentinel_row_cols
allowed_absent = {<dataset-specific allowlist>}
assert missing_in_sentinel_pass <= allowed_absent, (
    f"Spec sentinel columns missing from sentinel pass: {missing_in_sentinel_pass - allowed_absent}"
)

# Per-VIEW context (B5 + B4 fix): identity_cols_for_view and target_cols_for_view
# must match the per-VIEW sets passed to _detect_constants() and
# _consolidate_ledger() in the audit cells (Deliverable 4.A/4.B/4.C). Defined per cell:
#   sc2egset matches_flat_clean:    target={"result"},     identity={"replay_id", "toon_id"}
#   sc2egset player_history_all:    target={"result"},     identity={"replay_id", "toon_id"}
#   aoestats matches_1v1_clean:     target={"team1_wins"}, identity={"game_id"}
#   aoestats player_history_all:    target={"winner"},     identity={"game_id", "profile_id"}
#   aoe2companion matches_1v1_clean: target={"won"},       identity={"matchId"}
#   aoe2companion player_history_all: target={"won"},      identity={"matchId", "profileId"}
# (these are bound in each audit cell before the assertion battery runs).

# Ledger full-coverage assertion (Option B): every column in the VIEW gets a row
n_view_cols = int(con.execute(f"DESCRIBE {view_name}").df().shape[0])  # uniform W4
assert len(df_ledger) == n_view_cols, (
    f"Full-coverage ledger required for {view_name}: expected {n_view_cols} rows, got {len(df_ledger)}"
)

# Zero-missingness rows must have N/A mechanism + RETAIN_AS_IS recommendation (F1 + Option B)
_zero = df_ledger[
    (df_ledger["n_null"] == 0) &
    (df_ledger["n_sentinel"] == 0) &
    (df_ledger["n_distinct"].fillna(-1) != 1) &  # B5 fix: handle None for skipped identity cols
    (~df_ledger["column"].isin(target_cols_for_view)) &  # exclude target overrides (B4)
    (~df_ledger["column"].isin(identity_cols_for_view))  # B5 fix: identity cols routed via own branch
]
assert (_zero["mechanism"] == "N/A").all(), "non-target zero-missingness rows must have mechanism=N/A"
assert (_zero["recommendation"] == "RETAIN_AS_IS").all(), "non-target zero-missingness rows must be RETAIN_AS_IS"

# True constants (n_distinct=1 AND no NULLs AND no sentinels) must be DROP_COLUMN / mechanism=N/A
# (W1 + W7 fix: high-NULL near-constants are NOT tagged here — they fall through to spec/F1)
_const = df_ledger[
    (df_ledger["n_distinct"].fillna(-1) == 1) &  # B5 defensive: identity cols have n_distinct=None
    (df_ledger["n_null"] == 0) &
    (df_ledger["n_sentinel"] == 0)
]
assert (_const["mechanism"] == "N/A").all(), "true constant rows must have mechanism=N/A"
assert (_const["recommendation"] == "DROP_COLUMN").all(), "true constant rows must be DROP_COLUMN"

# B5 fix: identity columns must have mechanism=N/A, recommendation=RETAIN_AS_IS
_ident = df_ledger[df_ledger["column"].isin(identity_cols_for_view)]
assert (_ident["mechanism"] == "N/A").all(), "identity columns must have mechanism=N/A"
assert (_ident["recommendation"] == "RETAIN_AS_IS").all(), "identity columns must be RETAIN_AS_IS"

# W7 fix: target columns named in target_cols_for_view must actually appear in the ledger
# (typo guard — otherwise a misspelled target name silently leaves the recommendation unchanged).
_missing_targets = set(target_cols_for_view) - set(df_ledger["column"].values)
assert not _missing_targets, f"target column(s) named but missing from VIEW: {_missing_targets}"

# Target-column override (B4): if col in target_cols AND n_total_missing > 0,
# recommendation must be EXCLUDE_TARGET_NULL_ROWS
_targets_with_missing = df_ledger[
    (df_ledger["column"].isin(target_cols_for_view)) &
    ((df_ledger["n_null"] > 0) | (df_ledger["n_sentinel"] > 0))
]
assert (_targets_with_missing["recommendation"] == "EXCLUDE_TARGET_NULL_ROWS").all(), (
    "Target columns with semantic missingness must be EXCLUDE_TARGET_NULL_ROWS (B4)"
)

# Coverage of non-zero rows is guaranteed by the full-coverage assertion above
# (every column → row). W6 fix: no separate redundant assertion.

# Sentinel-spec consistency: every row with non-None sentinel_value reports n_sentinel >= 0
for _, row in df_ledger.iterrows():
    if row["sentinel_value"] is not None and row["sentinel_value"] != "None":
        assert row["n_sentinel"] >= 0
        # If the VIEW has CASE-WHEN converted the sentinel to NULL, n_sentinel is 0;
        # this is informational, not a failure.

# Decisions-surfaced section is present and non-empty in the artifact
assert len(artifact["missingness_audit"]["decisions_surfaced"]) >= 1
assert all("question" in d and d["question"] for d in artifact["missingness_audit"]["decisions_surfaced"])

# Files exist after write
assert (artifact_dir / "01_04_01_missingness_ledger.csv").exists()
assert (artifact_dir / "01_04_01_missingness_ledger.json").exists()
```

### 6.C — Dataset-specific assertions

- **sc2egset:**
  - `MMR` ledger row (in matches_flat_clean): sentinel_value=0, n_sentinel > 0 (33,000-37,500 expected from prior census), recommendation=DROP_COLUMN.
  - `gd_mapSizeX`/`gd_mapSizeY`: n_sentinel=0 (the VIEW already converts to NULL).
  - `result` (in matches_flat_clean): per F1 zero-missingness override → recommendation=RETAIN_AS_IS, mechanism=N/A. Target-override post-step does NOT fire because n_total_missing=0.
  - `result` (in player_history_all): if Undecided/Tie present, recommendation=EXCLUDE_TARGET_NULL_ROWS via target-override post-step.
  - `clanTag`: sentinel_value="" with high pct.
  - **W7 verification:** the constants-detection branch must surface n_distinct=1 for the go_* columns flagged in 01_03_03 — assert that `df_ledger[(df_ledger["n_distinct"] == 1)]["recommendation"]` is uniformly `DROP_COLUMN`.
- **aoestats:**
  - `team1_wins` (in matches_1v1_clean): per F1 → recommendation=RETAIN_AS_IS, mechanism=N/A. **Crucially, no `winner` column is referenced** (B1 fix).
  - `p0_winner`, `p1_winner` (in matches_1v1_clean): both per F1 → recommendation=RETAIN_AS_IS, mechanism=N/A.
  - `team_0_elo`/`team_1_elo`: sentinel_value=-1 with low n_sentinel (consistent with 01_02_04 min=-1, n_zero_team_0=4824, n_zero_team_1=192). **W3 verification:** recommendation=CONVERT_SENTINEL_TO_NULL (sentinel-only low-rate branch).
  - `p0_old_rating`/`p1_old_rating`: sentinel_value=0; verify n_sentinel matches expected from 01_02_04.
  - `winner` (in player_history_all): recommendation=EXCLUDE_TARGET_NULL_ROWS via target-override post-step.
- **aoe2companion:**
  - `won` (in matches_1v1_clean): per F1 → recommendation=RETAIN_AS_IS, mechanism=N/A (R03 guarantees zero NULLs).
  - `won` (in player_history_all): recommendation=EXCLUDE_TARGET_NULL_ROWS via target-override post-step.
  - `rating` (in matches_1v1_clean): recommendation=FLAG_FOR_IMPUTATION (primary feature exception).
  - The structurally-absent group (server, modDataset, scenario, password): each gets recommendation=DROP_COLUMN (>80%).
  - `antiquityMode` (~68.66%) and `hideCivs` (~49.30%): per W2-fix Group B, mechanism=MAR; per the 40-80% non-primary rule → recommendation=DROP_COLUMN.

---

## Deliverable 7 — Branch + file list + gate condition

### Branch

`fix/01-04-null-audit` (current branch — already checked out; status confirms staged refactor work).

### File manifest

| File | Action |
|------|--------|
| `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_01_data_cleaning.py` | Update — (a) W4 normalization: ALL `con.con.execute(...)` → `con.execute(...)` plus add `con = db.con` cell; (b) insert spec + helpers + 2 ledger cells + decisions cell; (c) modify artifact-write cells. |
| `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_01_data_cleaning.ipynb` | Update — jupytext sync (`jupytext --sync` from the .py). |
| `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_01_data_cleaning.py` | Update — (a) W4 normalization: `con = db._con` → `con = db.con`; (b) insert audit cells. |
| `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_01_data_cleaning.ipynb` | Update — jupytext sync. |
| `sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_01_data_cleaning.py` | Update — (a) no W4 changes (already conformant); (b) insert audit cells. |
| `sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_01_data_cleaning.ipynb` | Update — jupytext sync. |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` | Update — replace 01_04_01 step block with Deliverable 1.A. |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` | Update — replace 01_04_01 step block with Deliverable 1.B. |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` | Update — replace 01_04_01 step block with Deliverable 1.C. |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json` | Re-generate (notebook re-run) — additive `missingness_audit` block. |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md` | Re-generate. |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv` | NEW — notebook produces. |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.json` | NEW — notebook produces. |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json` | Re-generate. |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md` | Re-generate. |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv` | NEW. |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.json` | NEW. |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json` | Re-generate. |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md` | Re-generate. |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv` | NEW. |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.json` | NEW. |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` | Append entry on completion (per CLAUDE.md "After Category A step"). |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md` | Append entry on completion. |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md` | Append entry on completion. |

**Files NOT touched (per scope discipline):**
- `STEP_STATUS.yaml` per dataset — already shows `01_04_01: complete` from PR #138/#139.
- Any DuckDB VIEW DDL.
- Any schema YAML.
- Any raw table or Parquet file.
- `temp/` files (planning artifacts only).

### Gate condition (composite, all three datasets)

Per dataset, the gate from each ROADMAP entry's `gate.continue_predicate` must hold (Deliverable 1). Composite cross-game gate:

1. All three notebooks execute end-to-end without assertion failure (existing assertions + new assertions in Deliverable 6).
2. All three `01_04_01_missingness_ledger.{csv,json}` files exist.
3. Each ledger has exactly N rows where N equals the column count of the underlying VIEW (full-coverage assertion per Option B).
4. Each ledger has CSV column set exactly matching Deliverable 5.B (17 columns including `n_distinct` and `is_primary_feature`).
5. Each `01_04_01_data_cleaning.json` has additive `missingness_audit` block with `framework`, `missingness_spec`, `ledger`, `decisions_surfaced`, `override_priority`, `per_view_target_cols` keys.
6. Each `01_04_01_data_cleaning.md` has a "Missingness Ledger" subsection per VIEW + a "Decisions surfaced for downstream cleaning (01_04_02+)" closing section reproducing the dataset's DS-* entries with current observed rates.
7. Pre-commit hooks (ruff, mypy) pass.
8. Unit tests still pass — `source .venv/bin/activate && poetry run pytest tests/ -v` (no test changes expected; the audit is read-only over VIEWs).
9. **Verification (NOTE-2):** `Grep -r 'col != "winner"' sandbox/aoe2/aoestats/01_exploration/04_cleaning/` returns no matches. (Confirms F2 fix is fully in place; legacy triage code was removed in v3.)
10. **Connection-style verification (W4):** `Grep -r 'con.con.execute' sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_01_data_cleaning.py` returns no matches; `Grep -r 'db._con' sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_01_data_cleaning.py` returns no matches.

**Post-execution review (NOTE-4):** dispatch a reviewer-deep second-pass review against the produced ledgers to validate mechanism justifications before they are cited by Phase 02. The reviewer should specifically verify: (a) every `mechanism="MAR"` row has a non-fallback justification grounded in 01_02_04 evidence; (b) every `recommendation="DROP_COLUMN"` row's rationale is consistent with its observed rate or constant status; (c) every `recommendation="EXCLUDE_TARGET_NULL_ROWS"` row genuinely corresponds to a target-VIEW column with semantic missingness (B4 enforcement).

---

## Out of scope (explicit non-goals — preserve discipline)

- Modifying any VIEW DDL (deferred to 01_04_02+).
- Dropping any column from the actual VIEW (deferred — the ledger only RECOMMENDS DROP_COLUMN).
- Imputing any column (deferred to Phase 02).
- Converting sentinels to NULL in VIEWs (deferred to 01_04_02+; the audit only documents and recommends, including via the new `CONVERT_SENTINEL_TO_NULL` recommendation).
- Formal MCAR statistical tests (Little 1988) — inappropriate at the step's read-only-audit scope; mechanism classification grounded in domain evidence per Rubin's framework is the established norm at this Phase per Manual 01 §4.
- Updating PHASE_STATUS or STEP_STATUS — step is already complete; this refactor is additive on the same step within the same Phase.
- aoestats `overviews_raw` triage — out-of-scope; documented as out-of-analytical-scope in `decisions_surfaced` only.
- aoe2companion `leaderboards_raw` / `profiles_raw` triage — out-of-scope; documented as out-of-analytical-scope in `decisions_surfaced` only.
- Cross-dataset ledger join keys — Phase 02 concern (NOTE-1).

## Decisions locked (user, this round)

The three open questions raised in v1 of this plan have been answered by the user; the plan above already reflects them:

1. **JSON-inline ledger vs standalone files** — **KEEP BOTH.** Inline `missingness_audit` block remains inside `01_04_01_data_cleaning.json`; standalone `01_04_01_missingness_ledger.{csv,json}` files are also emitted for downstream programmatic consumption. Size cost is acceptable; redundancy is intentional.
2. **`research_log.md` CROSS entry** — **PER-DATASET ONLY.** No CROSS entry in `reports/research_log.md`. Per-dataset entries in each dataset's `research_log.md` suffice.
3. **Ledger row scope** — **OPTION B (full coverage).** One row per (view, column) — every column in each VIEW is represented. Zero-missingness columns emit `mechanism="N/A"`, `recommendation="RETAIN_AS_IS"`. Constant columns emit `mechanism="N/A"`, `recommendation="DROP_COLUMN"`.

---

## Plan status (post-critique)

This plan is **v3-r2** and has been **APPROVED** by reviewer-adversarial round 4 (see `planning/current_plan.critique.md`). The critique gate is satisfied; executor sessions can be dispatched.

**Iteration history:**
- **v1:** initial planner-science draft → adversarial round 1: 4 BLOCKERs + 7 WARNINGs (REVISE)
- **v2:** planner-science revision addressing all v1 findings → adversarial round 2: 3 NEW BLOCKERs (B1/B2/B3 — empirically false figures and a fabricated section name) + 7 WARNINGs (REVISE)
- **v3-r1:** parent surgical edits (verified ground truth against `01_02_04_univariate_census.json`) → adversarial round 3: 2 NEW BLOCKERs (B5 identity-column n_distinct=None instability; B6 CONVERT_SENTINEL_TO_NULL ignores carries_semantic_content) + 1 WARNING (W8 ledger CSV missing is_primary_feature) (REVISE)
- **v3-r2:** parent surgical edits applying B5/W8 fixes + Option D B6 deferral (DS entries surface contradiction without changing recommendation logic) → adversarial round 4: APPROVE

**Empirical truthfulness:** every cited NULL rate, sentinel count, and column reference is cross-checked against `01_02_04_univariate_census.json` or the VIEW DDLs. Reviewer-adversarial round 4 verified the new DS-SC2-09 (handicap, 2/44,817=0.00446%) and DS-SC2-10 (APM, 1132/44,817=2.527%) claims directly against the census artifact.

**Post-execution review (NOTE-4):** dispatch `reviewer-deep` against the produced ledger artifacts before they are cited by Phase 02. This validates that the as-shipped ledger reflects the W3 docstring contract (CONVERT_SENTINEL_TO_NULL is non-binding for `carries_semantic_content=True` columns) and the per-dataset DS entries hold up against the actual data.

---

**v3-r1 transparency note:**

The earlier v2 transparency note documented a planner deviation from the user's B2 instruction. After v2-round-2 adversarial review (verdict: REVISE BEFORE EXECUTION) and direct artifact verification by the parent, the deviation was traced to a **crossed-figure error**: `numeric_stats_players` is a list of dicts indexed by `label`, and the planner conflated the `label='new_rating'` row's stats (`min=-5, n_zero=5187`) with `label='old_rating'`. The actual `label='old_rating'` row has `min_val=0, n_zero=5937`. v3-r1 corrects this: the spec, DS-AOESTATS-02, the changelog, and the empirical spot-check all cite `old_rating` ground truth only. No deviation from the user's B2 instruction remains.

A second crossed-figure error was caught in the same round: `avg_elo.n_zero` was reported as `4,824` (which is actually `team_0_elo.n_zero`); the correct value `n_zero=121` is now used in the spec and DS-AOESTATS-03. The fabricated section name `categorical_profiles` (which does not exist in the artifact) has been replaced with `players_raw_census` (the actual section storing `zero_count`/`zero_pct` per column).