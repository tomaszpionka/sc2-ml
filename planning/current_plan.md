---
category: A
branch: phase02/feature-engineering-readiness
date: 2026-05-05
planner_model: gpt-5.5-pro
dataset: null
phase: "02"
pipeline_section: "02_01 -- Pre-Game vs In-Game Boundary"
invariants_touched: [I3, I5, I6, I7, I8, I9, I10]
source_artifacts:
  - thesis/pass2_evidence/audit_cleanup_summary.md
  - thesis/pass2_evidence/phase02_readiness_hardening.md
  - thesis/pass2_evidence/methodology_risk_register.md
  - thesis/pass2_evidence/cross_dataset_comparability_matrix.md
  - thesis/pass2_evidence/aoe2_ladder_provenance_audit.md
  - thesis/pass2_evidence/notebook_regeneration_manifest.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/tracker_events_feature_eligibility.csv
  - reports/specs/02_00_feature_input_contract.md
  - reports/specs/02_01_leakage_audit_protocol.md
  - docs/PHASES.md
  - docs/TAXONOMY.md
  - docs/templates/plan_template.md
  - docs/templates/step_template.yaml
  - docs/ml_experiment_lifecycle/02_FEATURE_ENGINEERING_MANUAL.md
  - .claude/scientific-invariants.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/PHASE_STATUS.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/PHASE_STATUS.yaml
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/PHASE_STATUS.yaml
critique_required: true
research_log_ref: reports/research_log.md#2026-05-05-cross-phase02-feature-engineering-readiness-contracts
---

# Plan: Phase 02 feature-engineering readiness contracts after PR #207 and PR #208

## Scope

This plan prepares the next PR on branch `phase02/feature-engineering-readiness`. The PR is a documentation/specification readiness PR for Phase 02. It creates the Phase 01 closeout summary and two Phase 02 contract/protocol specs, plus a data-analysis lineage rule that prevents ROADMAP → notebook → artifact batching. It does **not** generate feature tables, create feature-generation notebooks, train models, edit thesis chapters, touch raw data, or modify generated artifacts.

The user-specified branch prefix `phase02/` intentionally differs from the Category-A `feat/` convention. T00 must verify that no hook, workflow, or repo validation depends on branch-prefix matching before implementation begins. If a validation tool rejects the prefix, halt and ask whether to switch to `feat/phase02-feature-engineering-readiness`.

## Problem Statement

PR #207 hardened thesis methodology, AoE2 provenance, evidence lineage, and stale-artifact discipline. PR #208 executed SC2EGSet Step `01_03_05` and produced the tracker-event eligibility contract. The current state is therefore suitable for Phase 02 planning, but not for direct feature materialization.

The risk to avoid is GIGO with nice lineage: a ROADMAP entry, notebook, artifacts, and research log can still be scientifically wrong if the notebook's assumptions, falsifiers, and sanity checks were never reviewed before artifact generation. Phase 02 must therefore begin with explicit feature-family boundaries, temporal rules, source-specific labels, grains, and leakage gates before any feature-generation notebook is authored.

This PR will convert the post-PR #207/#208 evidence into three thesis-/pipeline-facing documents:

1. `thesis/pass2_evidence/phase01_closeout_summary.md`
2. `reports/specs/02_02_feature_engineering_plan.md`
3. `reports/specs/02_03_temporal_feature_audit_protocol.md`

It will also add `.claude/rules/data-analysis-lineage.md` to encode the anti-GIGO workflow rule.

## Assumptions & unknowns

- **Assumption:** Phase 01 is complete for `sc2egset`, `aoestats`, and `aoe2companion`; Phase 02 is not started for all three datasets.
- **Assumption:** `reports/specs/02_00_feature_input_contract.md` and `reports/specs/02_01_leakage_audit_protocol.md` remain LOCKED and binding. New specs in this PR must not supersede or silently amend them.
- **Assumption:** `tracker_events_feature_eligibility.csv` is the authoritative contract for SC2 tracker-derived in-game snapshot source families.
- **Assumption:** No generated artifact is stale at PR start unless T00 finds a manifest contradiction.
- **Unknown:** Whether the repository permits branch prefix `phase02/`. T00 resolves this mechanically.
- **Unknown:** Whether Phase 02 should later materialize a tiny validation slice. This PR does not implement one; it can only define the approval gate for such a slice.
- **Unknown:** Specific cold-start thresholds and pseudocounts. These cannot be fixed in this PR; the specs must define derivation gates and validation requirements only.

## Literature context

The Phase 02 methodology comes from the repository-local Feature Engineering manual: temporal availability boundaries, symmetric pairwise representation, rolling-window feature discipline, leakage prevention, categorical-encoding controls, and feature catalog documentation. The source manuals and scientific invariants are binding; no new external literature is introduced by this planning PR.

[OPINION] The correct Phase 02 sequence is contract → reviewer-deep → ROADMAP stubs → tiny validated slice → artifact generation → research log/status closure. Directly generating model-ready feature tables from the current baseline is not defensible because it would conflate source-family eligibility with feature-value correctness.

## Execution Steps

### T00 — Preflight, branch-prefix safety, and read-only baseline

**Objective:** Confirm the branch, status chain, and no-stale-artifact baseline before any file is changed.

**Instructions:**
1. Start from `master` after PR #207 and PR #208 are merged.
2. Create branch `phase02/feature-engineering-readiness` exactly as user requested.
3. Verify `git status --short` is clean.
4. Verify no `.github/workflows` or pre-commit hook depends on the branch prefix. If branch-prefix validation exists and rejects `phase02/`, halt.
5. Read all files listed in `source_artifacts` frontmatter, especially the five Pass-2 evidence files, `tracker_events_feature_eligibility.csv`, specs `02_00` / `02_01`, and all dataset ROADMAP / research_log / STEP_STATUS / PHASE_STATUS files.
6. Record a local checklist in the PR body draft or T01 source notes; do not create a generated artifact.

**Sanity check:** Phase 01 complete and Phase 02 not_started for `sc2egset`, `aoestats`, and `aoe2companion`; Step `01_03_05` complete for `sc2egset`; manifest has no `flagged_stale` or `regenerated_pending_log` rows relevant to Phase 02 entry.

**Falsifier:** Any Phase 01 not complete, any Phase 02 already in_progress, any relevant manifest row `flagged_stale` / `regenerated_pending_log`, or any branch-prefix hook failure halts the PR before T01.

**Artifact validation:** N/A — no artifact is produced.

**Lineage:** T00 must cite the status files and manifest rows in the PR body or T01 notes.

**Verification:**
- `git status --short` is empty before edits.
- `grep -R "branch" .github .pre-commit-config.yaml .claude/rules 2>/dev/null` or equivalent finds no branch-prefix gate blocking `phase02/`.
- Phase-status files are read and their Phase 01 / Phase 02 statuses are transcribed into T01.

**File scope:**
- none

**Read scope:**
- all `source_artifacts` frontmatter files

---

### T01 — Create `phase01_closeout_summary.md`

**Objective:** Create a single closeout document that states what Phase 01 has closed for Phase 02 and what remains narrowed/deferred.

**Instructions:**
1. Create `thesis/pass2_evidence/phase01_closeout_summary.md`.
2. Include a top-level status table with rows:
   - `sc2egset` — Phase 01 complete; Phase 02 not_started; pre-game/history ready with declared residuals.
   - `sc2egset tracker-derived in-game snapshot` — initial planned subset ready with caveats; full tracker scope narrowed, not closed.
   - `aoestats` — Phase 01 complete; Phase 02 not_started; pre-game/history ready under Tier 4 semantic opacity wording.
   - `aoe2companion` — Phase 01 complete; Phase 02 not_started; pre-game/history ready under mixed-mode ID 6 + ID 18 wording.
3. Explicitly state that this closeout is not thesis chapter prose and does not update Chapter 4.
4. Explicitly state that AoE2 must not be called unqualified ranked ladder; use the source-specific labels from T05/T09.
5. Explicitly state the three SC2 tracker blocked families and that they remain outside initial Phase 02 scope.
6. Include an evidence-lineage table with columns: `claim`, `source_file`, `source_step_or_spec`, `current_verdict`, `phase02_consequence`.
7. Include a sanity/falsifier/validation/lineage subsection.

**Sanity check:** Every closeout claim has a source path; every dataset has Phase 01 complete and Phase 02 not_started status cited from the dataset status files.

**Falsifier:** Any sentence implying full SC2 tracker scope is `closed`, aoestats is simply ranked ladder, or aoe2companion ID 6 + ID 18 is ranked-only blocks the file.

**Artifact validation:** Markdown must contain these exact phrases: `GATE-14A6 outcome: narrowed`, `full tracker scope is not closed`, `aoestats Tier 4`, `aoe2companion mixed-mode`, `tracker-derived features are never pre-game`.

**Lineage:** Cite/point to PR #208 tracker artifacts, `phase02_readiness_hardening.md`, `aoe2_ladder_provenance_audit.md`, `cross_dataset_comparability_matrix.md`, `notebook_regeneration_manifest.md`, and all three PHASE_STATUS files.

**Verification:**
- `test -s thesis/pass2_evidence/phase01_closeout_summary.md`
- `rg "GATE-14A6 outcome: narrowed|full tracker scope is not closed|aoestats Tier 4|aoe2companion mixed-mode|tracker-derived features are never pre-game" thesis/pass2_evidence/phase01_closeout_summary.md`
- `! rg "ranked ladder only|ranked-only|GATE-14A6.*closed" thesis/pass2_evidence/phase01_closeout_summary.md`

**File scope:**
- `thesis/pass2_evidence/phase01_closeout_summary.md`

**Read scope:**
- T00 source files

---

### T02 — Add data-analysis lineage guardrail rule

**Objective:** Add a repo rule that prevents generated artifacts from being treated as evidence before assumptions, falsifiers, and sanity checks are reviewed.

**Instructions:**
1. Create `.claude/rules/data-analysis-lineage.md`.
2. Include the binding rule: `A generated artifact is not evidence unless the notebook's assumptions, falsifiers, and sanity checks were reviewed before artifact generation.`
3. Include the execution sequence:
   - ROADMAP stub only.
   - Notebook scaffold + one validation module.
   - Execute and report.
   - User/reviewer review.
   - Commit checkpoint.
   - Next validation module.
   - Generate artifacts only after validation modules pass.
   - Then research_log / STEP_STATUS / manifest.
   - Then reviewer-deep.
4. Include a halt rule: if a result is surprising or contradicts assumptions, halt before artifact generation.
5. Make the rule apply to empirical data analysis and feature-engineering steps; do not make it retroactively invalidate confirmed Phase 01 artifacts.

**Sanity check:** Rule is framed as a workflow guardrail, not as a claim about existing artifacts being invalid.

**Falsifier:** Any text that says ROADMAP, notebook, artifact, and next step may be batched in one empirical execution blocks the file.

**Artifact validation:** Markdown must include the exact binding rule sentence and the halt rule.

**Lineage:** Cite/point to `audit_cleanup_summary.md` stale-artifact discipline and `notebook_regeneration_manifest.md` status vocabulary.

**Verification:**
- `test -s .claude/rules/data-analysis-lineage.md`
- `rg "A generated artifact is not evidence" .claude/rules/data-analysis-lineage.md`
- `rg "halt before artifact generation" .claude/rules/data-analysis-lineage.md`

**File scope:**
- `.claude/rules/data-analysis-lineage.md`

**Read scope:**
- `thesis/pass2_evidence/audit_cleanup_summary.md`
- `thesis/pass2_evidence/notebook_regeneration_manifest.md`

---

### T03 — Create `reports/specs/02_02_feature_engineering_plan.md`

**Objective:** Define the Phase 02 feature-engineering contract: minimal feature families, prediction settings, source labels, feature grains, and proposed ROADMAP steps without implementing notebooks or feature tables.

**Instructions:**
1. Create `reports/specs/02_02_feature_engineering_plan.md` with frontmatter:
   - `spec_id: CROSS-02-02-v1`
   - `version: CROSS-02-02-v1`
   - `status: LOCKED`
   - `date: 2026-05-05`
   - `datasets_bound: [sc2egset, aoestats, aoe2companion]`
   - `sibling_specs: [CROSS-02-00-v3.0.1, CROSS-02-01-v1.0.1]`
   - `supersedes: null`
2. Add a non-supersession clause: this spec does not replace or amend `02_00` or `02_01`; it consumes them.
3. Define prediction settings:
   - `pre_game`
   - `history_pre_game`
   - `in_game_snapshot`
   - `blocked_or_deferred`
4. Define feature table grains:
   - source-family catalog grain: one row per `(dataset_tag, prediction_setting, source_family)`.
   - canonical candidate feature matrix grain: one row per `(dataset_tag, match_id, focal_player_id, opponent_id, prediction_setting)`.
   - in-game snapshot candidate grain: one row per `(dataset_tag, match_id, focal_player_id, opponent_id, cutoff_loop)`.
   - future final feature catalog grain: one row per materialized feature column, owned by `02_08`.
5. Define minimal feature families by dataset and prediction setting. Each row must include `dataset`, `source_label`, `prediction_setting`, `feature_family`, `source_table_or_artifact`, `grain`, `allowed_now`, `constraints`, and `downstream_section`.
6. Include at least these cross-dataset minimal families:
   - static matchup/context features: faction/race/civ, opponent faction, map when available, patch/era context when available.
   - rating or rating-proxy features: SC2 MMR missingness / future reconstructed rating, aoestats `old_rating` conditional pre-game, aoe2companion `rating` with NULL handling.
   - history features: prior match count, prior win rate, rolling/expanding form, time since prior match, map/faction proficiency, matchup history.
   - cold-start indicators and smoothed history features, with derivation gates only.
7. Include SC2 in-game snapshot families by importing `tracker_events_feature_eligibility.csv` constraints. The spec must list 5 eligible-now rows, 7 caveated rows, 3 blocked rows, and mark `slot_identity_consistency` as a sanity gate, not a model input.
8. Include AoE2 source-specific labels and stratification:
   - `aoestats`: Tier 4 semantic opacity; source label `leaderboard='random_map'`; not ranked-only.
   - `aoe2companion`: ID 6 `rm_1v1` ranked candidate; ID 18 `qp_rm_1v1` quickplay/matchmaking-derived; combined scope mixed-mode; stratify/sensitivity by `internalLeaderboardId`.
9. Include proposed Phase 02 ROADMAP steps as a proposal table only. Do not edit dataset ROADMAPs in this PR unless a later user approval explicitly changes scope.

**Sanity check:** Every feature-family row declares a grain and prediction setting.

**Falsifier:** Any SC2 tracker-derived family marked `pre_game`, any blocked tracker family marked `allowed_now = true`, any AoE2 row labelled unqualified ranked ladder, or any family lacking grain/prediction_setting blocks the spec.

**Artifact validation:** Frontmatter parses; required sections exist; all feature-family rows use controlled vocabularies; spec contains no notebook paths and no materialized feature-table paths except proposed future placeholders.

**Lineage:** Each row must reference one of: `02_00`, `02_01`, Phase 01 closeout summary, `tracker_events_feature_eligibility.csv`, AoE2 provenance audit, comparability matrix, or dataset status/artifact files.

**Verification:**
- `test -s reports/specs/02_02_feature_engineering_plan.md`
- `python - <<'PY'
from pathlib import Path
p=Path('reports/specs/02_02_feature_engineering_plan.md')
s=p.read_text()
required=['CROSS-02-02-v1','prediction_setting','feature table grains','tracker_events_feature_eligibility.csv','aoestats Tier 4','aoe2companion','mixed-mode','slot_identity_consistency']
missing=[x for x in required if x not in s]
assert not missing, missing
for banned in ['ranked ladder only','tracker-derived pre-game','full tracker scope closed']:
    assert banned not in s, banned
PY`

**File scope:**
- `reports/specs/02_02_feature_engineering_plan.md`

**Read scope:**
- T01 closeout summary
- T00 source files

---

### T04 — Create `reports/specs/02_03_temporal_feature_audit_protocol.md`

**Objective:** Define the temporal feature audit protocol for Phase 02 candidate feature construction. This protocol complements the locked CROSS-02-01 pre-training leakage audit; it does not replace it.

**Instructions:**
1. Create `reports/specs/02_03_temporal_feature_audit_protocol.md` with frontmatter:
   - `spec_id: CROSS-02-03-v1`
   - `version: CROSS-02-03-v1`
   - `status: LOCKED`
   - `date: 2026-05-05`
   - `datasets_bound: [sc2egset, aoestats, aoe2companion]`
   - `sibling_specs: [CROSS-02-00-v3.0.1, CROSS-02-01-v1.0.1, CROSS-02-02-v1]`
   - `supersedes: null`
2. Add a non-supersession clause: CROSS-02-01 remains the mandatory pre-training/materialization leakage audit. CROSS-02-03 adds feature-family design-time and source-specific temporal checks.
3. Define mandatory audit families:
   - `HISTORY_STRICT_LT_TARGET`: every `player_history_all` feature uses dataset-specific anchor and `ph.<anchor> < target.started_at`.
   - `INGAME_LOOP_CUTOFF`: every SC2 tracker snapshot uses `event.loop <= cutoff_loop`.
   - `NO_TARGET_OR_POSTGAME_DIRECT`: no target/post-game field is projected directly for target match.
   - `TRAIN_FOLD_ONLY_FIT`: scalers, imputers, encoders, and smoothing priors fit on training fold only.
   - `KFOLD_TARGET_ENCODING`: target encoding uses cross-fitting or is prohibited.
   - `SYMMETRIC_FOCAL_OPPONENT`: focal and opponent features computed by same function or same SQL pattern.
   - `SOURCE_LABEL_STRATIFICATION`: AoE2 source-specific labels and `internalLeaderboardId` stratification retained.
   - `SC2_TRACKER_ELIGIBILITY`: tracker CSV governs all in-game snapshot families.
   - `COLD_START_GATE`: no cold-start threshold or pseudocount without empirical derivation and training-fold fit scope.
   - `GENERATED_ARTIFACT_DISCIPLINE`: no artifact generation before assumptions/falsifiers/sanity checks are reviewed.
4. Define a future audit artifact schema for feature-generation PRs, but state that this PR emits no such audit artifact because no feature-generation notebook or table is created.
5. Define cold-start gates:
   - `n_prior_matches` and `is_cold_start` must be explicit features or masks.
   - global priors/smoothing values must be derived from training folds only.
   - first-match rows must not be dropped silently.
   - any threshold must be data-derived or literature-cited per I7.
6. Define a failure matrix: what observation halts a future feature-generation step.

**Sanity check:** CROSS-02-03 clearly distinguishes design-time checks from CROSS-02-01 post-materialization/pre-training checks.

**Falsifier:** Any statement that CROSS-02-03 replaces CROSS-02-01, allows feature training without CROSS-02-01 audit after materialization, or permits tracker-derived pre-game features blocks the spec.

**Artifact validation:** Frontmatter parses; every audit family has `scope`, `pass_condition`, `falsifier`, `evidence_required`, and `future_artifact_field`.

**Lineage:** Each audit family cites a source invariant/spec/artifact path and downstream Phase 02 section.

**Verification:**
- `test -s reports/specs/02_03_temporal_feature_audit_protocol.md`
- `rg "does not replace|CROSS-02-01 remains|event.loop <= cutoff_loop|ph.<anchor> < target.started_at|training fold" reports/specs/02_03_temporal_feature_audit_protocol.md`
- `! rg "replaces CROSS-02-01|tracker-derived.*pre-game|full-dataset scaler" reports/specs/02_03_temporal_feature_audit_protocol.md`

**File scope:**
- `reports/specs/02_03_temporal_feature_audit_protocol.md`

**Read scope:**
- T01 closeout summary
- T02 rule
- T03 feature-engineering plan
- `reports/specs/02_01_leakage_audit_protocol.md`

---

### T05 — Cross-spec consistency pass

**Objective:** Verify that new documents do not contradict locked specs, evidence files, or source-specific AoE2 / SC2 constraints.

**Instructions:**
1. Search new files for prohibited terms:
   - `ranked ladder only`
   - unqualified `ranked ladder` in AoE2 combined or aoestats context
   - `GATE-14A6 closed`
   - `full tracker scope closed`
   - `tracker-derived pre-game`
2. Verify every `tracker_events_feature_eligibility.csv` row is represented or explicitly routed in `02_02`.
3. Verify all feature-family rows include `grain` and `prediction_setting`.
4. Verify all leakage audit families include a falsifier.
5. Verify cold-start sections contain no fixed pseudocount or threshold unless explicitly marked future-derived.
6. Verify no notebooks, generated artifacts, raw data, or thesis chapters are touched.

**Sanity check:** `git diff --name-only` contains only the planned docs/rules/research-log files.

**Falsifier:** Any touched notebook, generated artifact, raw-data path, or thesis chapter halts before commit.

**Artifact validation:** Use markdown grep checks and, where possible, frontmatter parsing for the three new Markdown files.

**Lineage:** Validation results should be summarized in the final PR body and reviewer-deep notes.

**Verification:**
- `git diff --name-only` matches the File Manifest below.
- `rg` checks above pass.
- Optional: small Python script validates frontmatter and required section headings.

**File scope:**
- no new files; edits to T01-T04 docs only if validation finds a contradiction

**Read scope:**
- T01-T04 outputs
- all source artifacts

---

### T06 — Research-log / changelog closure and reviewer-deep gate

**Objective:** Close the documentation/spec PR with a cross-cutting research-log entry and reviewer-deep pass before implementation tasks are approved.

**Instructions:**
1. Add a reverse-chronological entry to `reports/research_log.md` for CROSS Phase 02 readiness contracts.
2. Update `CHANGELOG.md` only if current project convention requires an `[Unreleased]` entry for new specs/rules. If no convention requires it, leave unchanged and state so in the PR body.
3. Run reviewer-deep. Do not run reviewer-adversarial unless reviewer-deep raises an unresolved BLOCKER.
4. Reviewer-deep must explicitly evaluate:
   - no notebook or artifact generation occurred;
   - no thesis chapters were edited;
   - no generated artifacts were manually patched;
   - full SC2 tracker scope remains narrowed, not closed;
   - every feature family declares grain and prediction setting;
   - source-specific AoE2 labels are preserved;
   - CROSS-02-03 does not supersede CROSS-02-01;
   - cold-start thresholds are gates, not magic constants.

**Sanity check:** Reviewer-deep returns PASS or PASS-WITH-NOTES with 0 unresolved BLOCKERs.

**Falsifier:** Any reviewer-deep BLOCKER must be resolved in-doc before commit; if it changes scope beyond docs/specs/rules/log, halt for user approval.

**Artifact validation:** N/A — no generated artifacts.

**Lineage:** Root research-log entry lists all created docs/rules and states that no feature generation occurred.

**Verification:**
- `rg "phase02/feature-engineering-readiness|CROSS-02-02-v1|CROSS-02-03-v1" reports/research_log.md`
- reviewer-deep checklist attached to PR body or committed as `planning/current_plan.critique.md` if that repo pattern is being used for this PR.

**File scope:**
- `reports/research_log.md`
- `CHANGELOG.md` only if convention requires
- T01-T04 docs if reviewer-deep finds fixable issues

**Read scope:**
- all outputs from T01-T05

---

## File Manifest

| File | Action |
|------|--------|
| `planning/current_plan.md` | Rewrite with this plan |
| `thesis/pass2_evidence/phase01_closeout_summary.md` | Create |
| `.claude/rules/data-analysis-lineage.md` | Create |
| `reports/specs/02_02_feature_engineering_plan.md` | Create |
| `reports/specs/02_03_temporal_feature_audit_protocol.md` | Create |
| `reports/research_log.md` | Update |
| `CHANGELOG.md` | Conditional update only if project convention requires |

## Gate Condition

The PR is complete only if all of the following are true:

- `phase01_closeout_summary.md` exists and states: Phase 01 complete for all three datasets; Phase 02 not_started; SC2 pre-game/history ready; SC2 planned tracker in-game snapshot subset ready with caveats; full SC2 tracker scope narrowed/not closed; AoE2 pre-game/history ready under source-specific labels.
- `.claude/rules/data-analysis-lineage.md` exists and contains the exact generated-artifact guardrail.
- `02_02_feature_engineering_plan.md` exists and defines minimal feature families by dataset/prediction setting, source labels, feature grains, and proposed Phase 02 ROADMAP steps without editing dataset ROADMAPs.
- `02_03_temporal_feature_audit_protocol.md` exists and complements, but does not replace, `02_01_leakage_audit_protocol.md`.
- Every feature-family row declares grain and prediction setting.
- Every leakage/audit rule declares sanity check, falsifier, evidence requirement, and future artifact field.
- No feature-generation notebook, model-ready feature table, raw data, generated artifact, model-training code, or thesis chapter is touched.
- Reviewer-deep returns PASS or PASS-WITH-NOTES with 0 unresolved BLOCKERs.

## Out of scope

- Feature-generation notebooks.
- Tiny validation slice execution.
- Model-ready feature tables or DuckDB feature views.
- Train/test splits, encoders, scalers, models, baselines, or metrics.
- Thesis chapter prose edits.
- Raw data edits.
- Manual patching or regeneration of existing generated artifacts.
- Dataset ROADMAP edits, unless the user explicitly approves converting the proposal table into ROADMAP stubs in a later task.
- Closing full SC2 tracker scope; current PR must preserve `narrowed` outcome.

## Open questions

- Should the next implementation PR add dataset ROADMAP stubs immediately after this contract PR, or first create a non-executing feature-source catalog? Resolves by user decision after this PR.
- Should a tiny validation slice be permitted in the first implementation PR? Resolves by user decision; default is no.
- Should CROSS-02-03 eventually gain CI/pre-commit enforcement? Resolves after the first feature-generation PR proves the audit schema.
- Should `CHANGELOG.md` be updated for spec/rule-only changes? Resolves by checking current repository convention during T06.
