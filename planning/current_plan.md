---
category: F
branch: thesis/audit-methodology-lineage-cleanup
date: 2026-04-26
planner_model: claude-opus-4-7
dataset: null
phase: null
pipeline_section: null
invariants_touched: [I1, I2, I3, I4, I5, I6, I7, I8, I9, I10]
source_artifacts:
  - planning/final_production_pr_plan.md
  - planning/current_plan.critique.md
  - CLAUDE.md
  - .claude/README.md
  - .claude/scientific-invariants.md
  - .claude/ml-protocol.md
  - .claude/rules/thesis-writing.md
  - .claude/rules/git-workflow.md
  - docs/agents/AGENT_MANUAL.md
  - docs/templates/planner_output_contract.md
  - docs/templates/plan_template.md
  - docs/TAXONOMY.md
  - docs/PHASES.md
  - docs/INDEX.md
  - thesis/THESIS_STRUCTURE.md
  - thesis/WRITING_STATUS.md
  - thesis/chapters/REVIEW_QUEUE.md
  - thesis/chapters/01_introduction.md
  - thesis/chapters/02_theoretical_background.md
  - thesis/chapters/03_related_work.md
  - thesis/chapters/04_data_and_methodology.md
  - thesis/references.bib
  - thesis/pass2_evidence/README.md
  - thesis/pass2_evidence/sec_4_1_crosswalk.md
  - thesis/pass2_evidence/sec_4_1_halt_log.md
  - thesis/pass2_evidence/sec_4_2_crosswalk.md
  - thesis/pass2_evidence/sec_4_2_halt_log.md
  - reports/research_log.md
  - reports/specs/01_05_preregistration.md
  - reports/specs/01_06_readiness_criteria.md
  - reports/specs/02_00_feature_input_contract.md
  - reports/specs/02_01_leakage_audit_protocol.md
  - reports/specs/README.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/PHASE_STATUS.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw
  - src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/PHASE_STATUS.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw
  - src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/INVARIANTS.md
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/PHASE_STATUS.yaml
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/views
  - sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_03_stratification.py
  - sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_01_data_dictionary.py
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_quality_report_aoe2companion.md
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoe2companion.md
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoe2companion.csv
  - sandbox/README.md
  - sandbox/jupytext.toml
  - sandbox/notebook_config.toml
critique_required: true
research_log_ref: reports/research_log.md#2026-04-26-thesis-audit-methodology-lineage-cleanup
---

# Plan: Thesis Audit Cleanup PR — Methodology, AoE2 Provenance, and Evidence Lineage Hardening

> **Revision note (v2, 2026-04-26):** This plan has been patched in
> response to `planning/current_plan.critique.md` (5 BLOCKERs, 5
> WARNINGs, 4 NOTEs). The patch log lives in
> `planning/current_plan.critique_resolution.md`. Master scope (one
> PR; branch `thesis/audit-methodology-lineage-cleanup`; ordering;
> Category F; 20 tasks; 12 guardrails) is preserved verbatim.

## Scope

This plan instantiates the consolidated, user-approved master plan at
`planning/final_production_pr_plan.md` as a single large pull request that
hardens (a) thesis scientific methodology, (b) AoE2 data provenance, and
(c) the ROADMAP → notebook → artifact → research_log → thesis evidence
lineage, after external scientific audit. Execution proceeds in the
mandatory order: lineage audit → AoE2 ladder/matchmaking provenance →
ROADMAP/notebook/artifact/log repair → cross-dataset comparability →
methodology and spec hardening (including imported Phase 02 readiness
items) → thesis rewrite of Chapters 1 through 4 → review gates → PR
summary. The PR is cross-dataset (sc2egset, aoestats, aoe2companion) and
cross-cutting; it does not advance any single Phase. Category is **F**
(thesis writing), with embedded Category A and D work performed only
through proper lineage discipline (ROADMAP first, then notebook,
artifact, log).

## Problem Statement

The thesis title is *"A comparative analysis of methods for predicting
game results in real-time strategy games, based on the examples of
StarCraft II and Age of Empires II."* External audit identified that the
current draft and supporting evidence chain risk overstating what the
data actually support. Seven concrete risk areas are surfaced in the
master plan's executive summary:

1. whether AoE2 data are truly *ranked ladder* records or more broadly
   public multiplayer / ladder / matchmaking-derived data;
2. whether `aoestats` and `aoe2companion` represent the same population;
3. whether `aoe2companion` combines ranked and quickplay-like 1v1 Random
   Map records (the `internalLeaderboardId` 6 vs 18 question, where
   on-disk evidence in
   `sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_03_stratification.py:23`
   already labels ID 18 as `qp_rm_1v1` (quickplay) — see T05 4.2 and
   Q2);
4. whether SC2 tournament/professional replay data can be compared
   directly with AoE2 public ladder/matchmaking data;
5. whether thesis claims trace cleanly to ROADMAP Steps, notebooks,
   generated artifacts, and research logs;
6. whether planned feature engineering and evaluation protocols prevent
   temporal leakage; and
7. whether the thesis uses cautious, evidence-bounded language about
   novelty, calibration, feature importance, and statistical inference.

The PR must therefore repair both prose and the underlying evidence
lineage. It must not "make the chapters sound better" while leaving
upstream artifacts stale, contradictions unresolved, or AoE2 source
semantics under-verified. Workflow leakage in thesis prose
(`Phase 01`, `PR #TBD`, `BACKLOG.md`, `grep`, `master`, `post-F1`) and
unsupported "ranked ladder" terminology must be removed. Chapters 1
through 4 must be rewritten only after the evidence chain has been
audited, regenerated where required, and recorded in research logs and
`STEP_STATUS.yaml`.

## Assumptions & unknowns

The 12 non-negotiable guardrails from `planning/final_production_pr_plan.md`
§4 are load-bearing assumptions for this plan; their full text is the
source of truth. Restated in concise form:

- **Assumption (G1):** No thesis claim is updated before its evidence
  chain (ROADMAP → notebook → artifact → research_log → STEP_STATUS) is
  verified intact, regenerated where stale, or explicitly weakened/flagged.
- **Assumption (G2):** ROADMAP changes precede notebook changes whenever
  a Step's question, method, input, output, gate, thesis mapping, or
  invariant changes.
- **Assumption (G3):** Notebook logic changes never proceed without (i)
  ROADMAP update, (ii) marking prior artifacts stale, (iii) regenerating
  declared outputs, (iv) updating the per-dataset `research_log.md`, (v)
  updating `STEP_STATUS.yaml` only after the log exists, (vi) updating
  downstream prose, specs, and review queues, and (vii) recording the
  dependency in `notebook_regeneration_manifest.md`.
- **Assumption (G4):** No file under `reports/<dataset>/artifacts/` is
  manually edited unless it is first proven and documented to be
  hand-maintained rather than generated. Otherwise the upstream
  ROADMAP Step and notebook/generator are updated and the artifact is
  regenerated.
- **Assumption (G5):** Raw data are immutable. Cleaning logic lives in
  code, notebooks, or pipeline; derived artifacts may be regenerated.
- **Assumption (G6):** No "ranked ladder" terminology is used unless
  evidence (source schema, filters, queue/mode labels, leaderboard
  fields, AI/player indicators, winner complementarity, source
  documentation) supports it for that specific source.
- **Assumption (G7):** Differences between SC2 and AoE2 results are
  framed as method/data/population differences across structurally
  different data regimes — not as a clean causal comparison of game
  mechanics.
- **Assumption (G8):** No temporal leakage. Every feature for a game at
  time `T` uses only information strictly before `T` (Invariant I3).
  Random splits, `create_temporal_split()` legacy assumptions, and
  `GLOBAL_TEST_SIZE` are forbidden.
- **Assumption (G9):** `[REVIEW:]`, `[UNVERIFIED:]`, `[NEEDS CITATION]`,
  and `[NEEDS JUSTIFICATION]` flags are removed only when evidence
  exists. Otherwise they are preserved, refined, or escalated.
- **Assumption (G10):** Grey literature (API docs, GitHub repos,
  community/forum pages) may support data-provenance claims but is not
  presented as peer-reviewed scientific evidence.
- **Assumption (G11):** Data-dictionary rows are identified by stable
  field/table names and semantic keys, never by CSV line numbers.
- **Assumption (G12):** Same-class contradictions in an artifact are
  resolved together in this PR via upstream regeneration or documented
  hand-maintained correction, unless a clearly separate methodological
  decision is required.

Additional load-bearing assumptions:

- **Assumption (B):** The branch name `thesis/audit-methodology-lineage-cleanup`
  is a user-explicit override of the conventional Category F prefix
  `docs/thesis-`. Recorded once here; do not raise again. Branch name is
  preserved verbatim. T01 verifies the prefix does not break CI/hooks/
  templates and records the chosen version-bump classification (see T01
  Instructions step 5 and WARNING-3 fix).
- **Assumption (C):** Hard rules from `CLAUDE.md` apply: read
  `.claude/scientific-invariants.md` before any data/feature/model work;
  read `PHASE_STATUS.yaml` before any Category A or F work; activate the
  venv before invoking poetry; never modify raw data; never begin a new
  phase before prior phase artifacts exist on disk.
- **Assumption (D):** Adversarial-review cap. This PR uses exactly 3
  adversarial cycles per the symmetric 3-round cap (project memory
  `feedback_adversarial_cap_execution.md`). T02 = Round 1 (plan
  critique, already produced); T10 = Round 2 (consolidated mid-PR gate
  covering T05 provenance, T10 risk register, and the methodology-
  affecting spec changes prepared for T15 and T16 sub-blocks 14A.2 /
  14A.3); T19 = Round 3 (final PR review). Spec amendment protocols
  (BLOCKER-2 fix) accept the consolidated T10 review as the
  reviewer-adversarial signoff required by §7 of each affected spec.
  No further adversarial dispatches are permitted within this PR; if
  T19 finds substantive new issues, the PR either accepts them as
  documented limitations or escalates to user for explicit
  cap-waiver signoff.

Unknowns (resolved during execution at the indicated task):

- **Unknown:** Which Steps actually require notebook regeneration vs.
  only re-interpretation of existing artifacts. Resolves at T03
  (dependency lineage audit) and T06 (regeneration decision). If T03
  declares more than 10 Steps stale across all three datasets
  combined, the executor halts and escalates per T03 Instructions
  step 6 (WARNING-1/6 fix).
- **Unknown:** Whether `aoe2companion` `internalLeaderboardId = 18` is
  accurately classified on disk as `qp_rm_1v1` (quickplay) — the
  on-disk evidence at
  `sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_03_stratification.py:23`
  and `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md:872`
  already labels ID 18 as `qp_rm_1v1`; the residual unknown is
  whether external aoe2companion / aoe2.net documentation overturns
  that label, and how the `1v1 ranked ladder` mis-label propagated
  from `data_quality_report_aoe2companion.md:29` into thesis Chapter
  4 §4.1.3 / §4.2.3. Resolves at T05 sub-step 4.2 with `@lookup`
  external verification (BLOCKER-1 fix).
- **Unknown:** Aggregation semantics of `aoestats` (third-party
  aggregator opacity) — to what extent the records are ranked-ladder
  derivatives vs broader public 1v1 Random Map. Resolves at T05 sub-
  step 4.1, anchored on existing on-disk evidence
  (`01_03_02_true_1v1_profile.md` Jaccard finding,
  `01_04_01_data_cleaning.md` R02 rule) and external source
  documentation via `@lookup`. If source documentation is silent,
  default to "source-specific aggregation with semantic opacity"
  (WARNING-4/9 fix).
- **Unknown:** Whether SC2 in-game telemetry features (derived from
  `tracker_events_raw`) are retained in the final thesis methodology.
  Gates whether T16 sub-step 14A.6 (optional retroactive Step
  `01_03_05` semantic validation) executes. Resolves at T15 (specs/ML
  protocol repair) or earlier by user decision.
- **Unknown:** Whether merge governance accepts the `thesis/...`
  branch-prefix deviation (already user-approved per (B); operational
  CI/hook/template impact is verified at T01 step 5).

## Literature context

The work scope is driven by an external scientific audit summarised in
`planning/final_production_pr_plan.md` §1 and §7. The literature
references that act as load-bearing verification targets for T14
(Chapter 3 cleanup) and T13 (Chapter 2 cleanup) include:

- Hodge2021 — Dota 2 prediction; details and result phrasing must be
  verified rather than overgeneralised to RTS.
- GarciaMendez2025 — verify authors, target game (CS:GO/streaming
  esports vs RTS), venue/status, accuracy claim.
- Khan2024 / SC-Phi2 — verify metadata and exact accuracy claims for
  StarCraft II.
- Bialecki2022 vs Bialecki2023 — relationship and SC2EGSet vs SC2ReSet
  dataset/tooling distinction.
- EsportsBench — verify version/cutoff consistency.
- Tarassoli — verify against phantom/misattribution risk identified in
  audit.
- Demšar 2006, Benavoli et al. 2017 — classifier-comparison framing
  (Friedman/Nemenyi/Wilcoxon, Bayesian signed-rank); avoid
  overcommitting to mean-rank machinery if assumptions/context are weak.
- Çetin Taş, Müngen, Elbert, Lin/NCT/intransitivity (if used) — AoE2
  literature verification.
- de Prado 2018 (Ch. 7), Arlot & Celisse 2010 — temporal-leakage and
  normalization-leakage citations for Chapter 4.

`[OPINION]` framing flag: Beyond cited references, the executive-summary
characterisation of "the main scientific risk" as one of overclaiming
populations and lineage rather than style is editorial/audit-driven and
not itself a peer-reviewed claim. The plan adopts it as the working
frame because the user-approved master plan adopts it; downstream
verification is performed in T03–T05 and T11–T14.

## Execution Steps

Each Stage from `planning/final_production_pr_plan.md` §6 is re-emitted
below as a Task. Stage numbering from the source is referenced in prose
only (the word "Stage" is forbidden as a work-unit name in this
repository per `docs/TAXONOMY.md`). Tasks are sequential T01 through
T20.

### T01 — Preflight and repo safety

**Objective:** Establish a clean, auditable starting point on the
declared branch before any audit, regeneration, or thesis editing
begins. Mirrors source `Stage 0`.

**Instructions:**
1. Confirm clean git state via `git status`. If unrelated uncommitted
   user changes exist, stop and document in
   `thesis/pass2_evidence/audit_cleanup_summary.md`.
2. Create branch `thesis/audit-methodology-lineage-cleanup` (verbatim;
   user-explicit override of the conventional `docs/thesis-*` prefix).
3. Record baseline in `thesis/pass2_evidence/audit_cleanup_summary.md`:
   current commit hash, changed/untracked files, available test
   commands, available notebook execution conventions, available
   jupytext/pairing conventions.
4. Do not overwrite user changes. Do not touch raw data
   (`src/**/data/*/raw/**` is deny-listed by repo permissions).
5. **Branch-prefix verification (WARNING-3/8 fix).** Verify that the
   `thesis/` branch prefix does not break: (a) `.github/workflows/*.yml`
   filters keyed on branch name; (b) `.pre-commit-config.yaml` rules;
   (c) `.github/pull_request_template.md` placeholder substitution;
   (d) `.claude/rules/git-workflow.md` version-bump classification
   (decide explicitly: minor or patch — the rule's table maps `docs/`
   to minor, `chore/` to patch; `thesis/` is not enumerated, so a
   choice must be recorded). Document all four findings AND the
   chosen version-bump classification in
   `thesis/pass2_evidence/audit_cleanup_summary.md` under "Branch-
   prefix operational verification".

**Verification:**
- `git rev-parse --abbrev-ref HEAD` returns `thesis/audit-methodology-lineage-cleanup`.
- `git status` is clean or every entry is documented in
  `audit_cleanup_summary.md`.
- The initial section of `thesis/pass2_evidence/audit_cleanup_summary.md`
  exists and contains the baseline record.
- The "Branch-prefix operational verification" sub-section in
  `audit_cleanup_summary.md` records findings (a)–(d) and the
  chosen version-bump classification.

**File scope:**
- `thesis/pass2_evidence/audit_cleanup_summary.md`

**Read scope:**
- (none from sibling tasks — this is the first task)
- `.github/workflows/` (read-only verification)
- `.pre-commit-config.yaml` (read-only)
- `.github/pull_request_template.md` (read-only)
- `.claude/rules/git-workflow.md` (read-only)

---

### T02 — Master-plan adversarial-critique gate (Round 1 of 3)

**Objective:** Record the explicit adversarial-critique checkpoint for
this plan (Category F requires it before execution begins). Mirrors
source `Stage 1`. This is **Round 1 of 3** adversarial cycles per
Assumption (D); the critique already exists at
`planning/current_plan.critique.md` and has been resolved into this
plan revision (v2). T02's role is to make the gate verifiable in
the PR.

**Instructions:**
1. Confirm `planning/current_plan.md` exists and conforms to
   `docs/templates/planner_output_contract.md`.
2. Confirm `planning/current_plan.critique.md` has been produced by
   `@reviewer-adversarial`, with at minimum an attack on (i) ROADMAP →
   notebook → artifact → research_log → thesis lineage preservation,
   (ii) AoE2 ranked-ladder/quickplay/matchmaking semantics handling
   before thesis rewrite, (iii) protection of generated artifacts from
   manual patching, (iv) treatment of methodology spec changes (no Cat
   C demotion), (v) temporal-leakage and stale-artifact risk control,
   and (vi) safe incorporation of the previous Pre-Phase-02 Readiness
   plan's items.
3. Confirm `planning/current_plan.critique_resolution.md` exists and
   records how every BLOCKER-1..5, WARNING-1..5, and NOTE-1..3 from
   the critique has been resolved into this plan revision (v2).
4. Resolve every BLOCKER finding in `planning/current_plan.md` before
   T03 begins, or convert it to a documented non-executable constraint
   in `thesis/pass2_evidence/audit_cleanup_summary.md`.
5. Reference the critique outcome from
   `thesis/pass2_evidence/audit_cleanup_summary.md` (section "Plan
   adversarial review").

**Verification:**
- `planning/current_plan.critique.md` exists.
- `planning/current_plan.critique_resolution.md` exists and
  enumerates each BLOCKER/WARNING/NOTE with patch status.
- No BLOCKER finding remains unaddressed; each is either resolved in
  the plan or recorded as a non-executable constraint in
  `audit_cleanup_summary.md`.

**File scope:**
- `thesis/pass2_evidence/audit_cleanup_summary.md`

**Read scope:**
- `planning/current_plan.md`
- `planning/current_plan.critique.md`
- `planning/current_plan.critique_resolution.md`
- `thesis/pass2_evidence/audit_cleanup_summary.md` (T01 baseline)

---

### T03 — Dependency lineage audit

**Objective:** Build the full dependency map from thesis claim to
upstream artifact before any notebook or thesis prose is touched.
Mirrors source `Stage 2`. This is the load-bearing audit that decides
which downstream work is needed.

**Instructions:**
1. Read `docs/TAXONOMY.md` and extract the repo's unit-of-work model:
   Phase, Pipeline Section, Step, sandbox notebook (paired `.py`/`.ipynb`),
   artifact, research log, thesis mapping.
2. Locate every relevant ROADMAP file:
   `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`,
   `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`,
   `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`.
3. Locate sandbox notebooks for SC2EGSet Phase 01 and later, aoestats
   Phase 01 and later, aoe2companion Phase 01 and later, and any
   cross-dataset comparison work.
4. For every empirical thesis claim in Chapters 1–4, map: thesis file
   and section, exact claim, table/paragraph location, claimed number
   or interpretation, artifact path, notebook path, ROADMAP Step,
   research_log entry, `STEP_STATUS.yaml` status, and overall status
   (intact / stale / missing / contradictory / prose-only).
5. Classify each planned edit as one of: thesis-only wording change,
   artifact interpretation change, notebook logic change, Step design
   change, or cross-dataset decision (per the regeneration-policy
   classes A–E in source §8).
6. **`claim_evidence_matrix.md` strategy decision (BLOCKER-4 fix —
   Option B SUPPLEMENT).** Examine the existing
   `thesis/pass2_evidence/{README.md, sec_4_1_crosswalk.md,
   sec_4_1_halt_log.md, sec_4_2_crosswalk.md, sec_4_2_halt_log.md}`.
   Adopt strategy B: `claim_evidence_matrix.md` is a global
   cross-chapter index covering Chapters 1–3 in detail and pointing
   at the existing Chapter 4 crosswalks
   (`sec_4_1_crosswalk.md` and `sec_4_2_crosswalk.md`) for Chapter 4
   specifics. The existing crosswalks remain frozen per
   `thesis/pass2_evidence/README.md`'s Pass-2-handoff convention; do
   NOT mutate them. If T11 finds new Chapter 4 numbers needing
   crosswalk entries beyond what the v1 crosswalks already cover,
   create `sec_4_1_v2_crosswalk.md` and/or `sec_4_2_v2_crosswalk.md`
   per the README versioning convention rather than editing the v1
   files. Record the strategy decision (Option B SUPPLEMENT) in
   `thesis/pass2_evidence/dependency_lineage_audit.md` under
   "Pass-2-evidence file relationships".
7. **Scope-explosion escape valve (WARNING-1/6 fix).** Once
   `dependency_lineage_audit.md` is complete, count the number of
   Steps classified as stale/missing/contradictory across all three
   datasets combined. If that count exceeds 10, HALT before any T06
   action and present the staleness inventory to the user in
   `audit_cleanup_summary.md` under "Scope-explosion escalation",
   together with a scope-split decision request: (a) continue
   one-large-PR strategy, (b) split into a lineage-audit-only PR
   plus downstream regeneration PR, or (c) defer specific Steps. Do
   not silently push through. Record the user decision (verbatim) in
   `audit_cleanup_summary.md` before any T06 work begins.

**Verification:**
- `thesis/pass2_evidence/dependency_lineage_audit.md` exists and
  contains a row for every empirical claim in Chapters 1–4 with
  lineage classification.
- `thesis/pass2_evidence/claim_evidence_matrix.md` first version
  exists and references `sec_4_1_crosswalk.md` and
  `sec_4_2_crosswalk.md` for Chapter 4 evidence (per Option B
  SUPPLEMENT decision).
- `thesis/pass2_evidence/notebook_regeneration_manifest.md` first
  version exists and lists every notebook that may need regeneration.
- No notebook edit, no thesis prose edit, and no artifact edit has
  occurred prior to this verification.
- If the staleness count exceeds 10 Steps, the user decision is
  recorded in `audit_cleanup_summary.md` and T06 has not started.

**File scope:**
- `thesis/pass2_evidence/dependency_lineage_audit.md`
- `thesis/pass2_evidence/claim_evidence_matrix.md`
- `thesis/pass2_evidence/notebook_regeneration_manifest.md`
- `thesis/pass2_evidence/audit_cleanup_summary.md` (Scope-explosion
  escalation sub-section, only if triggered)

**Read scope:**
- `thesis/chapters/01_introduction.md`
- `thesis/chapters/02_theoretical_background.md`
- `thesis/chapters/03_related_work.md`
- `thesis/chapters/04_data_and_methodology.md`
- `thesis/chapters/REVIEW_QUEUE.md`
- `thesis/THESIS_STRUCTURE.md`
- `thesis/WRITING_STATUS.md`
- `thesis/pass2_evidence/README.md` (Pass-2-handoff convention)
- `thesis/pass2_evidence/sec_4_1_crosswalk.md` (read-only; frozen)
- `thesis/pass2_evidence/sec_4_1_halt_log.md` (read-only; frozen)
- `thesis/pass2_evidence/sec_4_2_crosswalk.md` (read-only; frozen)
- `thesis/pass2_evidence/sec_4_2_halt_log.md` (read-only; frozen)
- All three `reports/ROADMAP.md`, `research_log.md`, and
  `STEP_STATUS.yaml` files (sc2egset, aoestats, aoe2companion).
- `reports/research_log.md`

---

### T04 — Flag ledger and thesis audit inventory

**Objective:** Produce a complete inventory of unresolved thesis flags
plus the external-audit issue list. Mirrors source `Stage 3`.

**Instructions:**
1. Search Chapters 1–4 for `[REVIEW:]`, `[UNVERIFIED:]`,
   `[NEEDS CITATION]`, `[NEEDS JUSTIFICATION]`, `[TODO]`, and internal
   workflow language (`Phase 01`, `PR #TBD`, `BACKLOG.md`, `grep`,
   `post-F1`, `master`).
2. Cross-check against `thesis/chapters/REVIEW_QUEUE.md`.
3. Record each finding in `thesis/pass2_evidence/cleanup_flag_ledger.md`
   with file, section, flag text, issue category, source needed,
   upstream artifact needed, proposed resolution, and status.
4. Add external-audit issues even when no in-text flag exists: AoE2
   ranked-ladder provenance; SC2 vs AoE2 cross-game comparability;
   SC2EGSet Zenodo/version distinction (SC2EGSet vs SC2ReSet);
   GarciaMendez2025 target game/details; Hodge2021 phrasing; AoE2
   civilization count over time; Demšar/Benavoli classifier-comparison
   framing; ICC overcentrality; ECE/calibration overclaiming; grey
   literature vs peer-reviewed literature distinction; workflow leakage
   in thesis prose.

**Verification:**
- `thesis/pass2_evidence/cleanup_flag_ledger.md` exists.
- Every existing in-text flag in Chapters 1–4 appears in the ledger.
- Every external-audit issue appears in the ledger.
- `REVIEW_QUEUE.md` discrepancies are listed.

**File scope:**
- `thesis/pass2_evidence/cleanup_flag_ledger.md`

**Read scope:**
- `thesis/chapters/01_introduction.md`
- `thesis/chapters/02_theoretical_background.md`
- `thesis/chapters/03_related_work.md`
- `thesis/chapters/04_data_and_methodology.md`
- `thesis/chapters/REVIEW_QUEUE.md`
- `thesis/pass2_evidence/dependency_lineage_audit.md`

---

### T05 — AoE2 ladder provenance audit

**Objective:** Decide what each AoE2 dataset can defensibly be called.
Mirrors source `Stage 4` (sub-blocks 4.1, 4.2, 4.3). Use
hypothesis/falsifier/gate structure for the core questions. Per
Assumption (D) and BLOCKER-5 fix, the per-task adversarial dispatch
is REMOVED — provenance-logic adversarial review is satisfied by the
consolidated mid-PR adversarial gate at T10 (Round 2 of 3).

**Instructions:**
1. **aoestats sub-audit (4.1).** Inspect schema, notebooks, artifacts,
   logs, and ROADMAP under
   `src/rts_predict/games/aoe2/datasets/aoestats/`. Identify population
   fields (`leaderboard`, map/mode, rating, player count, winner, AI
   filters, queue/match-type if present). **Start from existing
   on-disk evidence (WARNING-4/9 fix):**
   `01_03_02_true_1v1_profile.md` (Jaccard analysis, if it exists;
   reference `research_log.md:1077` for the 0.958755 finding) and
   `01_04_01_data_cleaning.md` R02 rule. Then verify against external
   aoestats source documentation via `@lookup`. If source documentation
   is silent on whether `random_map` is exclusively the ranked queue,
   classify aoestats as "source-specific aggregation with semantic
   opacity" (matches the lowest tier of the §6 Stage 4.3 terminology
   ladder) and weaken thesis terminology accordingly. Verify cleaning
   filters: true 1v1, resolved match, human players only, valid
   ratings, side/team/focal handling, schema-evolution exclusions.
   Identify residual risks: quickplay contamination, custom-lobby
   contamination, team-game contamination, missing/ambiguous queue
   metadata, upstream-aggregator limitations.
2. **aoe2companion sub-audit (4.2).** Inspect schema, notebooks,
   artifacts, logs, and ROADMAP under
   `src/rts_predict/games/aoe2/datasets/aoe2companion/`. Identify and
   document `internalLeaderboardId`, retained values, values 6 and 18
   if present, and mapping to `rm_1v1` / `qp_rm_1v1` / equivalent
   labels. **Start from the on-disk evidence already present
   (BLOCKER-1 fix):**
   `sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_03_stratification.py:23`
   labels `internalLeaderboardId=6 (rm_1v1) and =18 (qp_rm_1v1)`;
   `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md:872`
   lists `6/rm_1v1` (~54M) and `18/qp_rm_1v1` (~7M) as top values.
   Use `@lookup` (external verification) to either confirm or
   overturn the on-disk classification of ID 18 = `qp_rm_1v1` against
   external aoe2companion / aoe2.net documentation. **Fallback rule
   (BLOCKER-1 fix):** if external documentation is ambiguous or
   unavailable, default to treating ID 18 as quickplay/matchmaking-
   derived, NOT ranked ladder. Never default to "ranked ladder" on
   ambiguity. Decide whether combining 6 and 18 is methodologically
   defensible; choose between split, exclude quickplay, keep both
   with matchmaking/ladder-like label, or treat one source as
   robustness/control.
3. **Audit format (4.3).** Write
   `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md`
   containing: source-by-source summary, exact source fields,
   filters, retained population, excluded population, evidence
   strength, remaining uncertainty, recommended terminology (per the
   four-tier ladder in source §6 Stage 4.3), exact thesis sections
   requiring edits, and whether notebook regeneration is needed. The
   terminology ladder must explicitly map: **ID 18 alone (or
   `rm_1v1` + `qp_rm_1v1` combined) → "third-party 1v1 Random Map
   quickplay/matchmaking records (per `qp_rm_1v1` label found in
   stratification artifact 01_05_03)" unless external verification
   overturns the on-disk evidence** (BLOCKER-1 fix).
4. Classify every occurrence of "ranked ladder" in Chapters 1–4 as
   OK / revise / unsupported / source-specific. Treat aoestats and
   aoe2companion separately. Where uncertainty remains, weaken thesis
   wording and flag.
5. **Propagation trace (BLOCKER-1 fix).** Trace the propagation of
   the "Retain 1v1 ranked ladder only" mis-label from
   `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_quality_report_aoe2companion.md:29`
   into thesis Chapter 4 §4.1.3 / §4.2.3 (lines 177, 187, 255 of
   `thesis/chapters/04_data_and_methodology.md`) and into any other
   downstream artifact, prose, or research-log entry. Record every
   traced occurrence in the
   `aoe2_ladder_provenance_audit.md` under "Mis-label propagation
   trace" so that T11 can apply the corrected terminology verbatim
   to each location.
6. **Adversarial review deferred to T10 (BLOCKER-5 fix).** The
   per-task "Submit the audit to `@reviewer-adversarial`" instruction
   is REMOVED. The provenance-logic adversarial review is satisfied
   by the consolidated mid-PR adversarial gate at T10 (Round 2 of 3).
   Defer dispatch until T10. Within T05, document any provenance-
   logic concerns the executor wishes to surface to T10's gate in the
   audit's "Open questions for T10 review" section.

**Verification:**
- `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` exists.
- Every "ranked ladder" / "ladder" / "matchmaking" occurrence in
  Chapters 1–4 has a classification entry.
- aoestats and aoe2companion are described separately with separate
  recommended terminology.
- The audit's "Mis-label propagation trace" section enumerates the
  `data_quality_report_aoe2companion.md:29` → thesis §4.1.3 / §4.2.3
  → other downstream propagation paths.
- The fallback rule "default to quickplay/matchmaking on ambiguity,
  never default to ranked ladder" is recorded explicitly in the
  audit.
- The audit's "Open questions for T10 review" section enumerates any
  provenance-logic concerns deferred to T10's consolidated review.

**File scope:**
- `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md`

**Read scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml`
- `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/raw`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.md`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/INVARIANTS.md`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_quality_report_aoe2companion.md`
- `sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_03_stratification.py`
- `thesis/pass2_evidence/dependency_lineage_audit.md`
- `thesis/pass2_evidence/cleanup_flag_ledger.md`

---

### T06 — ROADMAP and notebook regeneration decision

**Objective:** Decide which Steps require regeneration and update
upstream ROADMAP definitions before any notebook edit. Mirrors source
`Stage 5`.

**Instructions:**
1. Using outputs from T03–T05, identify every Step whose question,
   filters, cleaning logic, output artifacts, thesis mapping, or
   invariant/gate has changed.
2. For each affected Step, update the relevant ROADMAP file before
   touching its notebook: record old vs new Step definition; update
   expected inputs/outputs; update gate criteria; update
   `thesis_mapping`; update `scientific_invariants_applied`.
3. **Stale-marking discipline (NOTE-1/11 fix).** If a notebook must be
   edited, declare current artifacts from that Step as stale by
   recording them in `notebook_regeneration_manifest.md` (the manifest
   is the authoritative source of staleness). Do NOT rename artifacts
   with `_STALE` suffixes — that breaks downstream cross-references in
   research logs and thesis prose. Downstream consumers must consult
   the manifest before citing any artifact.
4. If no notebook regeneration is needed, document the reason in
   `thesis/pass2_evidence/notebook_regeneration_manifest.md`.
5. **Halt-and-escalate enforcement (WARNING-1/6 fix).** If T03's
   scope-explosion escape valve fired (more than 10 Steps stale across
   the three datasets combined) and the user has not yet returned a
   scope-split decision recorded in
   `audit_cleanup_summary.md`, do not begin any T06 ROADMAP edit. T06
   begins only after the user resolves the scope question.

**Verification:**
- No notebook change has occurred without a corresponding ROADMAP
  change when Step semantics changed.
- Every stale artifact is identified in
  `notebook_regeneration_manifest.md` (no `_STALE` filename suffix
  has been used).
- Every regeneration target is declared in the manifest.
- If T03's escape valve fired, the user's scope-split decision is
  recorded in `audit_cleanup_summary.md` before any T06 edit.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` (conditional¹)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` (conditional¹)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` (conditional¹)
- `thesis/pass2_evidence/notebook_regeneration_manifest.md`

**Read scope:**
- `thesis/pass2_evidence/dependency_lineage_audit.md`
- `thesis/pass2_evidence/cleanup_flag_ledger.md`
- `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md`
- `thesis/pass2_evidence/audit_cleanup_summary.md` (for scope-split
  decision, if T03's escape valve fired)
- All three dataset ROADMAP files (read first, edit only where Step
  semantics changed).

---

### T07 — Notebook fixes and artifact regeneration

**Objective:** Regenerate only what the manifest declares stale, but
regenerate completely and reproducibly. Mirrors source `Stage 6`.

**Instructions:**
1. **Notebook execution command (WARNING-2/7 fix).** For each affected
   Step from T06: edit paired notebooks (`.py` + `.ipynb`) consistently;
   execute end-to-end using the standard repo command —
   `source .venv/bin/activate && poetry run jupyter nbconvert --to notebook --execute --inplace <path-to-notebook.ipynb>`
   — with the timeout from `sandbox/notebook_config.toml`
   `[execution] timeout_seconds` (default 600s if not present). If a
   notebook fails to execute end-to-end, halt and document the failure
   in `notebook_regeneration_manifest.md`; do not commit a notebook
   whose execution log shows errors. Regenerate all declared artifacts
   under
   `src/rts_predict/games/<game>/datasets/<dataset>/reports/artifacts/`;
   update schemas under `data/db/schemas/` if needed; update
   assertions/gates.
2. AoE2 priorities: 1v1 scope; ranked/quickplay/leaderboard semantics;
   human vs AI filtering; winner complementarity; rating missingness;
   side/team asymmetry; focal/opponent construction; schema evolution.
3. SC2 priorities: SC2EGSet version/source identity; true 1v1 decisive
   scope; MMR sentinel semantics; tournament/professional population;
   replay/in-game feature availability.
4. Add tests/assertions: no team games in 1v1 analytical view; no
   unresolved winners; complementarity of win/loss; no AI games when
   human-only is claimed; no post-game data in pre-game feature views;
   no same-match leakage in history features.
5. Do not modify raw data. Do not edit any artifact manually if it is
   generated; only regenerate via its upstream notebook.

**Verification:**
- `git diff` shows updated notebook pairs that match
  `notebook_regeneration_manifest.md` declarations.
- All regenerated artifacts under
  `src/rts_predict/games/<game>/datasets/<dataset>/reports/artifacts/`
  match the ROADMAP-declared outputs for their Step.
- No stale artifact is referenced by any downstream consumer.
- `@reviewer` (mechanical) approves each per-dataset block.
- **Manifest-bound rule (WARNING-5/10 + BLOCKER-3 fix; extended for
  BLOCKER-1 sub-check 6).** Every modified file under
  `sandbox/<game>/<dataset>/**` or
  `src/rts_predict/games/<game>/datasets/<dataset>/reports/artifacts/**`
  has a corresponding row in `notebook_regeneration_manifest.md`.
  Any file modified without a manifest row is a planner-contract
  Hard Rule violation (no executor task may touch a file absent from
  the manifest). The manifest is the authoritative bound on the
  wildcard manifest rows. This rule applies to all generated artifact
  paths under aoe2companion `06_decision_gates`, including but not
  limited to Step 01_06_01 (data dictionary) and Step 01_06_02 (data
  quality report) outputs.

**File scope:**
- `sandbox/sc2/sc2egset/**` (conditional² — see manifest)
- `sandbox/aoe2/aoestats/**` (conditional²)
- `sandbox/aoe2/aoe2companion/**` (conditional²)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/**` (conditional²)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/**` (conditional²)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/**` (conditional²)
- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/**` (conditional²)
- `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/**` (conditional²)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/**` (conditional²)

**Read scope:**
- `thesis/pass2_evidence/notebook_regeneration_manifest.md`
- All three dataset ROADMAP files (post-T06)
- `sandbox/README.md`
- `sandbox/jupytext.toml`
- `sandbox/notebook_config.toml`

---

### T08 — research_log and STEP_STATUS repair

**Objective:** Repair evidence logs after artifact regeneration or
interpretation changes. Mirrors source `Stage 7`.

**Instructions:**
1. For each regenerated or reinterpreted Step, update the per-dataset
   `research_log.md` with: Step ID; question; method; inputs;
   outputs/artifacts; exact generated artifact paths; key findings;
   validation/assertions; limitations; thesis mapping; decision; whether
   prior artifacts became stale.
2. Update `STEP_STATUS.yaml` only after the corresponding log entry is
   complete.
3. If the finding affects cross-dataset comparison, add an entry to
   the root `reports/research_log.md` (CROSS).
4. Do not invent or backfill log entries for Steps not actually
   touched in this PR.

**Verification:**
- Every regenerated artifact appears in a per-dataset
  `research_log.md` entry.
- Every thesis-relevant interpretation change has a log entry.
- `STEP_STATUS.yaml` agrees with logs and on-disk artifacts.
- Cross-dataset findings are recorded in `reports/research_log.md`.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` (conditional³)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md` (conditional³)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md` (conditional³)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` (conditional³)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml` (conditional³)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml` (conditional³)
- `reports/research_log.md` (cross-dataset CROSS entry; always
  updated to record the audit decision)

**Read scope:**
- `thesis/pass2_evidence/notebook_regeneration_manifest.md`
- All three dataset ROADMAP and STEP_STATUS files (post-T06/T07)
- Regenerated artifacts under each dataset's `reports/artifacts/`

---

### T09 — Cross-dataset comparability matrix

**Objective:** Define the exact valid comparison scope for the thesis.
Mirrors source `Stage 8`.

**Instructions:**
1. Build a matrix in
   `thesis/pass2_evidence/cross_dataset_comparability_matrix.md`
   comparing SC2EGSet, aoestats, and aoe2companion across: source type;
   population; sampling mechanism; time window; unit of observation;
   true 1v1 status; ranked/ladder/matchmaking status;
   professional vs public player population; pre-game features;
   in-game features; replay availability; rating availability;
   patch/version drift; map/civ/race encoding; cold-start behaviour;
   legal/licensing/source limitations; inference limitations.
2. For each comparison claim in Chapters 1–4, label as supported,
   supported with caveat, unsupported, or wording-change-required.
3. Define the thesis's final comparison frame, anchored to the
   master-plan §6 Stage 8 expected framing: SC2 as
   tournament/professional replay corpus with rich in-game telemetry;
   AoE2 as third-party public 1v1 Random Map ladder/matchmaking-derived
   records with primarily pre-game/history/rating/map/civilization
   features; observed differences are method/data/population
   differences, not pure game-mechanic differences.
4. Add a cross-dataset CROSS entry in `reports/research_log.md`
   recording this decision.

**Verification:**
- `thesis/pass2_evidence/cross_dataset_comparability_matrix.md` exists.
- Every Chapter 1–4 comparison claim is labelled.
- Final comparison frame is recorded.
- `reports/research_log.md` contains the CROSS entry.

**File scope:**
- `thesis/pass2_evidence/cross_dataset_comparability_matrix.md`
- `reports/research_log.md`

**Read scope:**
- `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md`
- `thesis/pass2_evidence/dependency_lineage_audit.md`
- `thesis/pass2_evidence/cleanup_flag_ledger.md`
- All three dataset `INVARIANTS.md` files
- `thesis/chapters/01_introduction.md`
- `thesis/chapters/04_data_and_methodology.md`

---

### T10 — Methodology risk register and consolidated mid-PR adversarial gate (Round 2 of 3)

**Objective:** Record remaining examiner-facing risks rather than
burying them, and execute the consolidated mid-PR adversarial review
that satisfies BLOCKER-2's spec §7 reviewer-adversarial signoff and
BLOCKER-5's adversarial-cap discipline. Mirrors source `Stage 9` plus
a consolidated review obligation imported from T05 / T15 / T16
14A.2 / 14A.3 per BLOCKER-5 fix.

**Instructions:**
1. Create `thesis/pass2_evidence/methodology_risk_register.md`
   covering all 17 risks enumerated in source §6 Stage 9: AoE2 ranked
   ladder terminology (record explicitly that the qp_rm_1v1
   mis-label propagation traced in T05 is the **concrete current
   state on master**, not a hypothetical risk — BLOCKER-1 fix);
   aoe2companion quickplay/ranked mixing; aoestats
   source-aggregation opacity; SC2 tournament vs AoE2 public ladder
   population; temporal leakage in history features; match/series
   grouping leakage; rating missingness and sentinel semantics;
   patch/version drift; civilization roster changes across AoE2 time
   window; feature importance interpreted causally; ECE/binning
   instability; overuse of ICC / variance partitioning; overstrong
   literature-gap claim; grey-literature overreliance; reproducibility
   of third-party API data; SC2 cross-region fragmentation
   sample-size collapse (record the empirically derived retention
   threshold from T16 14A.5 here once available — NOTE-2/12 fix);
   SC2 `tracker_events_raw` field-semantics uncertainty if in-game
   features are retained.
2. For each risk record: severity; likelihood; affected thesis
   sections; mitigation; remaining uncertainty; final wording
   recommendation.
3. **Add an 18th risk: PR scope risk (WARNING-1/6 fix).** "PR scope
   risk — 20 tasks across thesis, three datasets, four chapters, two
   LOCKED specs. If T03 dependency lineage audit declares more than
   10 Steps stale, escalate to user for a scope-split decision before
   T06 begins." Mark as resolved at T03 if the escalation occurred,
   or as deferred if the count remained at or below 10.
4. **Consolidated mid-PR adversarial gate (BLOCKER-5 + BLOCKER-2
   fix).** Once the risk register is drafted, dispatch
   `@reviewer-adversarial` ONCE in a consolidated review (Round 2 of
   3 per Assumption (D)) covering:
   (i) `aoe2_ladder_provenance_audit.md` from T05 — provenance
       logic, the `qp_rm_1v1` propagation trace, and the
       "default to quickplay/matchmaking on ambiguity" fallback;
   (ii) the risk register itself, including the qp_rm_1v1 mis-label
        as concrete current state (not hypothetical);
   (iii) the planned spec changes for T15 and T16 sub-blocks 14A.2 /
         14A.3 (the planner-science + reviewer-adversarial
         co-signoff required by §7 of CROSS-02-00 and CROSS-02-01
         per BLOCKER-2 fix is satisfied by this single review);
   (iv) the regeneration plan from T06 if material spec/methodology
        questions remain.
   Record the review outcome (verdict, BLOCKERs, WARNINGs, NOTEs,
   resolutions) in `thesis/pass2_evidence/audit_cleanup_summary.md`
   under "Mid-PR adversarial gate (T10, Round 2 of 3)". Resolve
   every BLOCKER before T11 begins. WARNINGs and NOTEs flow to the
   risk register.

**Verification:**
- `thesis/pass2_evidence/methodology_risk_register.md` exists and
  includes the 17 source risks plus the 18th PR scope risk.
- The qp_rm_1v1 mis-label is recorded in the register as the
  concrete current state, not a hypothetical risk.
- Every serious risk has either a mitigation or explicit
  limitation-wording recommendation.
- The consolidated mid-PR adversarial review (Round 2 of 3) has been
  dispatched and its outcome recorded in
  `audit_cleanup_summary.md` under "Mid-PR adversarial gate".
- No BLOCKER from the consolidated review remains unaddressed
  before T11 begins.

**File scope:**
- `thesis/pass2_evidence/methodology_risk_register.md`
- `thesis/pass2_evidence/audit_cleanup_summary.md` (mid-PR gate
  outcome)

**Read scope:**
- `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md`
- `thesis/pass2_evidence/cross_dataset_comparability_matrix.md`
- `thesis/pass2_evidence/cleanup_flag_ledger.md`
- All three dataset `INVARIANTS.md` files
- `reports/specs/02_00_feature_input_contract.md` (for §7 protocol
  context)
- `reports/specs/02_01_leakage_audit_protocol.md` (for §7 protocol
  context)
- T15 and T16 14A.2 / 14A.3 spec change drafts (read by the
  consolidated reviewer; surfaced as input to the gate)

---

### T11 — Chapter 4 methodology cleanup

**Objective:** Make Chapter 4 scientifically defensible and aligned
with regenerated artifacts. Mirrors source `Stage 10`.

**Instructions:**
1. Fix SC2EGSet source/version/citation: verify exact Zenodo record;
   distinguish SC2EGSet preprocessed dataset from SC2ReSet raw replay
   pack/tooling; update citation and license wording only if verified.
2. Fix AoE2 source descriptions: separate aoestats from aoe2companion;
   use source-specific terminology per
   `aoe2_ladder_provenance_audit.md`; explain third-party-aggregation
   limitations; avoid overclaiming official ranked ladder.
3. **Apply T05 terminology verbatim and remove qp_rm_1v1 mis-labels
   (BLOCKER-1 fix).** Remove or weaken every "ladder rankingowy 1v1"
   / "ranked ladder" wording in §4.1 / §4.2 / §4.3 / §4.4 that traces
   to the qp_rm_1v1 mis-label per the propagation trace recorded in
   `aoe2_ladder_provenance_audit.md`. Apply the T05 §6 Stage 4.3
   terminology ladder verbatim (in particular, the mapping for ID 18
   alone or `rm_1v1 + qp_rm_1v1` combined).
4. Repair §4.1 and §4.2: ensure every number traces to a current
   artifact; ensure cleaning rules align with regenerated artifacts;
   ensure tables cite current artifact source; remove
   workflow-internal language from prose.
5. **Versioned crosswalk handling (BLOCKER-4 fix).** If new numbers
   in Chapter 4 require crosswalk entries beyond what
   `sec_4_1_crosswalk.md` and `sec_4_2_crosswalk.md` already cover,
   create `sec_4_1_v2_crosswalk.md` and/or `sec_4_2_v2_crosswalk.md`
   per the `pass2_evidence/README.md` versioning convention. Do not
   mutate the v1 crosswalks. Update `claim_evidence_matrix.md` to
   reference any v2 crosswalks alongside v1.
6. Repair §4.3 and §4.4 if currently placeholders: do not fabricate
   completed experiments; if Phase 02/03/04 is incomplete, write
   defensible planned-methodology language or explicitly mark pending;
   include explicit temporal-leakage controls; include feature
   families only if implemented or planned with clear gates.
7. Evaluation methodology: Brier and log-loss as primary probabilistic
   metrics if consistent with final design; ECE only as auxiliary with
   binning caveat; reliability diagrams / calibration slope and
   intercept where supported; AUROC and accuracy as secondary.
8. Statistical comparisons: avoid overcommitting to Friedman/Nemenyi
   mean-rank machinery; prefer paired loss differences, repeated
   temporal windows, and block bootstrap if supported; if not
   implemented, describe as planned or flag.
9. ICC: reduce centrality; move to diagnostic/appendix framing if
   still needed; remove any universal claim that observed-scale ICC
   is simply a lower bound of latent-scale ICC unless exactly
   supported.
10. Update `claim_evidence_matrix.md` and `cleanup_flag_ledger.md` to
    reflect final Chapter 4 state.

**Verification:**
- `rg -n "ranked ladder|leaderboard='random_map'|qp_rm_1v1|rm_1v1"
  thesis/chapters/04_data_and_methodology.md` returns only
  occurrences justified by `aoe2_ladder_provenance_audit.md` and the
  T05 terminology ladder.
- No "ladder rankingowy 1v1" wording survives unless explicitly
  justified by external verification overturning the on-disk
  qp_rm_1v1 evidence.
- Every number in Chapter 4 maps to an artifact path recorded in
  `claim_evidence_matrix.md` or `sec_4_*_crosswalk.md` (v1 or v2).
- No source population in Chapter 4 is mislabeled.
- No placeholder is disguised as completed method.
- `REVIEW_QUEUE.md` is updated for Chapter 4.
- If v2 crosswalks were created, `claim_evidence_matrix.md`
  references them.

**File scope:**
- `thesis/chapters/04_data_and_methodology.md`
- `thesis/pass2_evidence/claim_evidence_matrix.md`
- `thesis/pass2_evidence/cleanup_flag_ledger.md`
- `thesis/chapters/REVIEW_QUEUE.md`
- `thesis/pass2_evidence/sec_4_1_v2_crosswalk.md` (conditional⁷ —
  only if T11 finds new Chapter 4 numbers requiring crosswalk
  entries beyond what v1 covers)
- `thesis/pass2_evidence/sec_4_2_v2_crosswalk.md` (conditional⁷)
- `thesis/pass2_evidence/README.md` (conditional⁷ — only if v2
  crosswalks are created or if new claim_evidence_matrix structure
  requires index updates)

**Read scope:**
- `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md`
- `thesis/pass2_evidence/cross_dataset_comparability_matrix.md`
- `thesis/pass2_evidence/methodology_risk_register.md`
- `thesis/pass2_evidence/dependency_lineage_audit.md`
- `thesis/pass2_evidence/sec_4_1_crosswalk.md` (read-only; frozen)
- `thesis/pass2_evidence/sec_4_2_crosswalk.md` (read-only; frozen)
- All three dataset regenerated artifacts under `reports/artifacts/`

---

### T12 — Chapter 1 introduction, RQ, scope cleanup

**Objective:** Make the thesis opening match the real study. Mirrors
source `Stage 11`.

**Instructions:**
1. Rewrite motivation to emphasize scientific/methodological value,
   not market-size hype.
2. Weaken unsupported commercial/esports market claims unless dated
   and sourced.
3. Correct or flag: Hodge2021 details; GarciaMendez2025 target game/
   authors/accuracy; betting-market transfer from traditional sport to
   esports; AoE2 "millions of active players" if unsupported; AoE2
   "50 civilizations" if temporal scope is wrong or untied to the
   observed data window.
4. Rewrite the research-gap statement conservatively — *"In the
   reviewed literature, I did not identify a peer-reviewed study that
   compares families of probabilistic prediction methods across
   StarCraft II and Age of Empires II under a unified protocol."*
5. Rewrite RQ1–RQ4 to align with actual datasets and methods;
   distinguish method comparison from pure game comparison;
   distinguish pre-game vs in-game prediction; keep cold-start RQ only
   if empirically supported, otherwise flag.
6. Rewrite scope/limitations: SC2 professional/tournament replay
   population; AoE2 public 1v1 Random Map ladder/matchmaking
   population (per T05/T09); not a causal study of game mechanics;
   not a fully symmetric comparison of data availability; not
   necessarily real-time AoE2 prediction if only pre-game data are
   available.
7. **Apply T05 terminology to Chapter 1 (BLOCKER-1 fix).** Remove or
   weaken every "ladder rankingowy 1v1" / "ranked ladder" wording in
   Chapter 1 that traces to the qp_rm_1v1 mis-label per T05's
   propagation trace, applying the T05 §6 Stage 4.3 terminology
   ladder verbatim.
8. Update `WRITING_STATUS.md` and `REVIEW_QUEUE.md`.

**Verification:**
- Title, RQs, data, and methods are coherent in
  `01_introduction.md`.
- No overstrong novelty claims survive.
- AoE2 population wording matches T05 audit terminology (no
  qp_rm_1v1 mis-label propagation survives in Chapter 1).
- `WRITING_STATUS.md` reflects the revision; `REVIEW_QUEUE.md`
  reflects updated flag status.

**File scope:**
- `thesis/chapters/01_introduction.md`
- `thesis/WRITING_STATUS.md`
- `thesis/chapters/REVIEW_QUEUE.md`

**Read scope:**
- `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md`
- `thesis/pass2_evidence/cross_dataset_comparability_matrix.md`
- `thesis/pass2_evidence/cleanup_flag_ledger.md`
- `thesis/chapters/04_data_and_methodology.md` (post-T11)

---

### T13 — Chapter 2 theoretical-background cleanup

**Objective:** Remove overclaims and align theory with actual planned
experiments. Mirrors source `Stage 12`.

**Instructions:**
1. RTS difficulty: keep relevant theory; avoid excessive RL/AlphaStar
   detail not used by the thesis; distinguish control/agent-playing
   difficulty from prediction difficulty.
2. SC2: correct MMR/per-race/ladder claims with official or
   source-backed evidence; avoid implying SC2EGSet is ladder data.
3. AoE2: correct civilization-count claims relative to the data
   window; avoid claiming exact official ranked-system internals
   unless sourced; distinguish visible Elo/rating from unknown
   official matchmaking internals.
4. Rating systems: Elo / Glicko / TrueSkill / Aligulac as conceptual
   baselines; no overclaiming about TrueSkill 2 RTS validation;
   grey literature labelled as such.
5. Classifier-comparison theory: fix Demšar/Benavoli framing;
   avoid making Nemenyi/mean-rank procedures central if not
   appropriate to N=2 cross-game setting.
6. Calibration: emphasize proper scoring rules; ECE limitations;
   reliability diagrams as diagnostic, not sole proof.
7. ICC: reduce centrality; make it optional/diagnostic unless core
   to results.
8. **Inherit T05/T11 terminology and check Chapter 2 for downstream
   propagation (BLOCKER-1 fix).** Where Chapter 2 references AoE2
   ranked-ladder semantics, weaken the wording wherever T05's
   terminology ladder requires (in particular, do not let SC2
   theoretical material implicitly endorse "ranked ladder" labelling
   for AoE2 sources). Apply the T05 mapping for ID 18 / `qp_rm_1v1`
   verbatim.
9. Update `references.bib` with verified entries; tag grey
   literature with `[REVIEW: grey-literature — <url>]` in chapter
   prose where unavoidable.

**Verification:**
- Chapter 2 supports the methodology without promising experiments
  not planned or implemented.
- Rating and ladder terminology in Chapter 2 matches T05 and T09.
- No qp_rm_1v1-derived "ranked ladder" wording survives in Chapter
  2 unless externally justified.
- No verified phantom citations remain.

**File scope:**
- `thesis/chapters/02_theoretical_background.md`
- `thesis/references.bib`
- `thesis/chapters/REVIEW_QUEUE.md`

**Read scope:**
- `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md`
- `thesis/pass2_evidence/cross_dataset_comparability_matrix.md`
- `thesis/chapters/04_data_and_methodology.md` (post-T11)
- `thesis/chapters/01_introduction.md` (post-T12)

---

### T14 — Chapter 3 related-work cleanup

**Objective:** Make related work accurate, conservative, and
citation-clean. Mirrors source `Stage 13`.

**Instructions:**
1. Verify and fix: Tarassoli phantom/misattribution issues; Khan2024
   / SC-Phi2 metadata and exact accuracy claims; EsportsBench
   version/cutoff consistency; Bialecki2022 vs Bialecki2023
   relationship; SC2EGSet dataset/tooling distinction;
   GarciaMendez2025 target game and article status; Hodge2021 result
   details.
2. AoE2 literature: verify Çetin Taş and Müngen; verify Elbert if
   used; verify Lin/NCT/intransitivity if used; distinguish
   peer-reviewed AoE2 prediction work from community analyses.
3. Research gap: state conservatively; do not claim exhaustive
   absence unless a documented systematic search protocol exists.
4. Reduce overly broad adjacent-domain review where it distracts
   from RTS/AoE2/SC2 focus.
5. Keep literature tied to: probabilistic win prediction;
   RTS/SC2/AoE2; rating baselines; calibration; cross-domain
   sports/esports prediction.
6. **Inherit T05/T11 terminology and check Chapter 3 for downstream
   propagation (BLOCKER-1 fix).** Where Chapter 3 surveys AoE2
   prediction literature, audit any "ranked ladder" descriptive
   wording. Apply T05's terminology ladder where the wording is
   referring to the thesis's own AoE2 sources (aoestats /
   aoe2companion). Do not retroactively rewrite cited authors'
   characterisations of *their* sources, but do flag any
   inadvertent framing where this thesis's qp_rm_1v1 mis-label
   bleeds into Chapter 3 prose.
7. Record verifications and outcomes in
   `thesis/pass2_evidence/literature_verification_log.md`.

**Verification:**
- No known phantom citations remain in `03_related_work.md`.
- Grey literature is not mislabeled; tagged with
  `[REVIEW: grey-literature — <url>]` where unavoidable.
- The literature-gap statement is defensible (matches T12 wording).
- `literature_verification_log.md` exists.
- No qp_rm_1v1-derived "ranked ladder" wording survives in Chapter
  3 unless externally justified or quoting cited authors.

**File scope:**
- `thesis/chapters/03_related_work.md`
- `thesis/references.bib`
- `thesis/pass2_evidence/literature_verification_log.md`
- `thesis/chapters/REVIEW_QUEUE.md`

**Read scope:**
- `thesis/pass2_evidence/cleanup_flag_ledger.md`
- `thesis/chapters/01_introduction.md` (post-T12)
- `thesis/chapters/02_theoretical_background.md` (post-T13)
- `thesis/chapters/04_data_and_methodology.md` (post-T11)

---

### T15 — Specs, leakage gates, and ML-protocol repair

**Objective:** Ensure future modelling cannot proceed under unsafe
assumptions. Mirrors source `Stage 14`. Per Assumption (D) and
BLOCKER-5 fix, the per-task adversarial dispatch is REMOVED — the
methodology-affecting spec changes prepared here are reviewed by the
consolidated mid-PR adversarial gate at T10 (Round 2 of 3).

**Instructions:**
1. Inspect existing specs under `reports/specs/`:
   `01_05_preregistration.md`, `01_06_readiness_criteria.md`,
   `02_00_feature_input_contract.md`, `02_01_leakage_audit_protocol.md`.
2. **Apply each spec's §7 amendment protocol (BLOCKER-2 fix).** For
   every spec body change, apply the §7 Spec Change Protocol of the
   affected spec:
   (i) classify the change as major (vN+1) or minor (vN.M+1) per the
       spec's own §7 rules — changes to audit dimensions
       (CROSS-02-01 §2), gate conditions (CROSS-02-01 §5), or
       column-grain commitments (CROSS-02-00 §2) are major bumps
       where the spec says so;
   (ii) bump the `version` field in the frontmatter;
   (iii) add an amendment-log entry recording date, author,
         motivation, and scope (in the spec's amendment-log table);
   (iv) obtain planner-science + reviewer-adversarial signoffs (the
        latter via the consolidated mid-PR adversarial gate at T10
        per BLOCKER-2 fix);
   (v) commit the version bump and amendment-log row in the same
       commit as the body change (per §7 of CROSS-02-00:
       "The `version` field in the frontmatter MUST be bumped in
       the same commit as the amendment").
   Update or create specs to cover: feature-generation temporal
   discipline (Invariant I3); train/validation/test splitting (per-
   player chronological hold-out per Invariant I1); per-player /
   per-time / cross-dataset constraints; no target leakage; no
   random split; source-specific AoE2 population labels (per T05);
   reproducibility seed = 42; stale-artifact detection.
3. If feature/model code exists, add or update tests/assertions.
4. If feature/model code does not yet exist, add gate conditions and
   explicit future requirements.
5. Update the methodology in Chapter 4 (already in T11 file scope)
   only to the level actually supported by these specs.
6. **Adversarial review deferred to T10 (BLOCKER-5 fix).** The
   per-task "Submit spec changes that affect methodology to
   `@reviewer-adversarial`" instruction is REMOVED. The methodology-
   affecting spec changes are reviewed by the consolidated mid-PR
   adversarial gate at T10 (Round 2 of 3). The §7 amendment
   protocol's planner-science + reviewer-adversarial co-signoff is
   satisfied by that single review (see Assumption (D) and BLOCKER-2
   fix).
7. Decide here whether SC2 in-game telemetry features are retained;
   this gates T16 sub-step 14A.6 execution.

**Verification:**
- No spec contradicts `.claude/ml-protocol.md`.
- No thesis methodology language describes unimplemented protections
  as completed fact.
- `@reviewer-deep` finds no BLOCKER on leakage discipline.
- **Spec frontmatter `version` field has been bumped (no LOCKED
  spec body has been modified while the frontmatter version remains
  stale).** Each affected spec's amendment log has a new row dated
  within this PR. Major-vs-minor classification is recorded in
  `audit_cleanup_summary.md` under "Spec amendment classifications".
- The consolidated mid-PR adversarial review at T10 has accepted the
  spec changes (recorded in `audit_cleanup_summary.md` under
  "Mid-PR adversarial gate").

**File scope:**
- `reports/specs/01_05_preregistration.md` (conditional⁴)
- `reports/specs/01_06_readiness_criteria.md` (conditional⁴)
- `reports/specs/02_00_feature_input_contract.md` (conditional⁴)
- `reports/specs/02_01_leakage_audit_protocol.md` (conditional⁴)
- `reports/specs/README.md` (conditional⁴ — index update if specs
  added or renamed)
- `thesis/pass2_evidence/audit_cleanup_summary.md` (Spec amendment
  classifications sub-section)

**Read scope:**
- `.claude/ml-protocol.md`
- `.claude/scientific-invariants.md`
- `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md`
- `thesis/pass2_evidence/methodology_risk_register.md`
- `thesis/chapters/04_data_and_methodology.md` (post-T11)
- `reports/specs/02_00_feature_input_contract.md` §7 (read for
  amendment protocol)
- `reports/specs/02_01_leakage_audit_protocol.md` §7 (read for
  amendment protocol)

---

### T16 — Phase 02 readiness hardening

**Objective:** Incorporate the safe parts of the previous Pre-Phase-02
Readiness plan under strict lineage discipline. Mirrors source
`Stage 14A` (sub-blocks 14A.1–14A.6). Manual edits to generated
artifacts are forbidden; same-class contradictions are resolved
upstream.

**Instructions:**
1. **Data-dictionary temporal-classification audit (14A.1).** Inspect
   aoe2companion data-dictionary rows for `rating`, `started`,
   `leaderboard`, `internalLeaderboardId`, and other pre-game/context
   fields. Identify rows by stable field/table names, never by CSV
   line numbers. **Generated-vs-hand-maintained discipline (BLOCKER-3
   fix).** The data dictionary IS generated by
   `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_01_data_dictionary.py:114`.
   If 14A.1 finds a temporal-classification contradiction, the
   affected files are enumerated in the File Manifest under
   conditional⁶; touching them requires updating
   `notebook_regeneration_manifest.md` to record the cause
   (`T16 14A.1 finding`). Apply T06/T07 discipline: update the
   upstream ROADMAP Step (Step 01_06_01); regenerate the CSV via the
   notebook; update research_log; update STEP_STATUS.yaml after the
   log entry exists. Fix all same-class temporal-classification
   contradictions in the same PR unless a separate methodological
   decision is required.

   **BLOCKER-1 sub-check 6 extension — data-quality-report propagation
   repair path.** This sub-step also covers the BLOCKER-1 propagation
   repair path for the generated aoe2companion data-quality report.
   If `data_quality_report_aoe2companion.md` contains the
   `1v1 ranked ladder` mis-label for the retained ID 6 + ID 18
   population (verified by T05 step 5 propagation trace), do not patch
   the artifact manually. Update Step 01_06_02 in ROADMAP if the Step
   wording, question, outputs, or thesis mapping changes; update the
   paired `01_06_02_data_quality_report` notebook/generator (.py and
   .ipynb); regenerate the artifact via the standard nbconvert command
   (T07 step 1); then update `research_log.md` and
   `STEP_STATUS.yaml`. The same conditional⁶ manifest discipline
   applies. Record the cause as `T05/Q2 BLOCKER-1 propagation` in
   `notebook_regeneration_manifest.md`. Manual patching of the
   generated artifact is forbidden (G3/G4).
2. **CROSS-02-01 leakage-audit protocol hardening (14A.2).** Bind the
   v1 enforcement mechanism in
   `reports/specs/02_01_leakage_audit_protocol.md`; prefer
   pattern-conformance review as v1 if AST/lineage tooling does not
   yet exist; defer AST/pre-commit/CI tooling to v2 only if
   explicitly documented. **§7 amendment protocol (BLOCKER-2 fix).**
   This change binds the v1 enforcement mechanism — per CROSS-02-01
   §7, "Any change to §2 audit dimensions or §5 gate condition
   constitutes a major version increment (vN+1)." A v1→v2 bump is
   therefore appropriate; record the bump explicitly. Apply the §7
   amendment protocol verbatim (classify; bump version field;
   amendment-log row; planner-science + reviewer-adversarial
   signoffs via T10's consolidated gate; same-commit discipline).
   The adversarial review for this spec change is satisfied by the
   consolidated mid-PR adversarial gate at T10 (BLOCKER-5 fix).
3. **CROSS-02-00 feature-input contract and cold-start hardening
   (14A.3).** Update `reports/specs/02_00_feature_input_contract.md`
   only after AoE2 source semantics are verified (T05). Make the
   cold-start / rating-sparsity protocol source-specific (sc2egset,
   aoestats, aoe2companion). Forbid: future-game rating imputation;
   global-fit imputation leakage; hard-coded 0/1500 priors without
   derivation; use of target/result/duration fields in pre-game
   features. Preserve null/missing flags where predictive and
   temporally valid. Do not bind pseudocount `m` before empirical
   derivation. **§7 amendment protocol (BLOCKER-2 fix).** Source-
   specific cold-start protocol additions likely affect §3/§4
   column-grain commitments and §5 gate conditions, so classify
   as **major (v3→v4)** per CROSS-02-00 §7. Apply the §7 amendment
   protocol verbatim (classify as major; bump version field
   v3→v4; amendment-log row; planner-science + reviewer-adversarial
   signoffs via T10's consolidated gate; same-commit discipline).
4. **DuckDB UTC requirement (14A.4).** Add a requirement that all
   rolling-window joins and TIMESTAMP/TIMESTAMPTZ comparisons run
   with DuckDB session timezone bound to UTC. Add tests/assertions
   or notebook checks where practical. Document naked-TIMESTAMP
   assumptions per dataset.
5. **SC2 cross-region fragmentation risk (14A.5).** Assess whether
   `is_cross_region_fragmented` safe-subset filtering collapses the
   SC2 sample. **Empirical threshold binding (NOTE-2/12 fix).** Bind
   the retention threshold empirically to the WP-3 /
   `is_cross_region_fragmented` retention finding (per
   `modeling_readiness_sc2egset.md` §5 if cited there, or the
   `01_05_*` cross-region analysis in sc2egset). Record the
   empirically derived threshold in
   `methodology_risk_register.md` (under the cross-region risk
   entry). If no threshold can be empirically justified within this
   PR, keep the issue in the risk register as a deferred decision
   rather than hard-coding a magic number (Invariant I7). If
   strict filtering is used, report retention and fold-level sample
   sizes.
6. **Optional SC2 `tracker_events_raw` semantic validation (14A.6).**
   Execute only if T15 retains SC2 in-game telemetry features. If
   retained: add retroactive Step `01_03_05` under sc2egset ROADMAP
   *before* creating/editing notebooks (T06 discipline); use
   hypothesis/falsifier/gate format for each validation; validate
   `gameSpeed` / loop-to-time conversion, player-ID mapping by event
   type, JSON-key completeness, `PlayerStats` periodicity anomaly,
   field semantics before any aggregate reconciliation, coordinate
   bounds only after coordinate units are understood, patch/schema
   stability if feasible; emit `.md` and `.json` artifacts; update
   sc2egset `research_log.md` and `STEP_STATUS.yaml` (T08
   discipline); update CROSS-02-00 derivation-pattern table (apply
   §7 amendment protocol per step 3 above); update Chapter 4 only
   after artifacts are regenerated and logged. If not retained:
   weaken thesis claims about validated tracker-events-derived
   features.
7. Cautions: do not assume final-tick `PlayerStats` minerals/vespene
   are cumulative totals; coordinate-bounds validation is descriptive
   until coordinate units are verified; do not use SC2 tracker
   validation as a substitute for AoE2 provenance.
8. Write `thesis/pass2_evidence/phase02_readiness_hardening.md`
   recording all decisions, deferred items, and spec deltas.

**Verification:**
- `thesis/pass2_evidence/phase02_readiness_hardening.md` exists.
- No generated artifact has been manually edited.
- All methodology-affecting spec changes have passed the
  consolidated mid-PR adversarial review at T10 (BLOCKER-5 fix); no
  per-task adversarial dispatch is performed in T16.
- AoE2 ranked/ladder terminology is governed by T05, not by
  generic cold-start specs.
- SC2 `tracker_events_raw` validation is either completed and
  logged, or thesis claims about validated tracker-derived features
  are weakened.
- **All affected spec frontmatter `version` fields are bumped;
  amendment logs have new dated rows; LOCKED-vs-modified state is
  consistent (no body changes against stale frontmatter).**
  Major-vs-minor classification (per each spec's §7) is recorded in
  `audit_cleanup_summary.md`.
- **Manifest-bound rule (BLOCKER-3 fix; extended for BLOCKER-1
  sub-check 6).** Every modified file under
  `sandbox/<game>/<dataset>/**` or
  `src/rts_predict/games/<game>/datasets/<dataset>/reports/artifacts/**`
  has a corresponding row in `notebook_regeneration_manifest.md`.
  In particular, if 14A.1 found the data dictionary contradicted,
  the conditional⁶ rows in the File Manifest are matched by manifest
  entries with cause `T16 14A.1 finding`. Equivalently, if T05/Q2
  found the generated `data_quality_report_aoe2companion.md`
  carries the `1v1 ranked ladder` mis-label propagated from the
  ID 6 + ID 18 population, the conditional⁶ rows for Step 01_06_02
  are matched by manifest entries with cause
  `T05/Q2 BLOCKER-1 propagation`. This manifest discipline applies
  to both Step 01_06_01 and Step 01_06_02 generated artifacts.
- The empirically derived `is_cross_region_fragmented` retention
  threshold (or its deferred-decision status) is recorded in
  `methodology_risk_register.md`.

**File scope:**
- `thesis/pass2_evidence/phase02_readiness_hardening.md`
- `reports/specs/02_00_feature_input_contract.md` (conditional⁴ —
  with §7 v3→v4 amendment per BLOCKER-2 fix)
- `reports/specs/02_01_leakage_audit_protocol.md` (conditional⁴ —
  with §7 v1→v2 amendment per BLOCKER-2 fix)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` (conditional⁵ — Step 01_03_05 insertion only if 14A.6 executes)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` (conditional⁵)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` (conditional⁵)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_05_*.md` (conditional⁵)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_05_*.json` (conditional⁵)
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_05_*.py` (conditional⁵)
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_05_*.ipynb` (conditional⁵)
- `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_01_data_dictionary.py` (conditional⁶ — only if 14A.1 finds a temporal-classification contradiction and the dictionary is confirmed generated)
- `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_01_data_dictionary.ipynb` (conditional⁶)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoe2companion.csv` (conditional⁶)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoe2companion.md` (conditional⁶)
- `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_02_data_quality_report.py` (conditional⁶ — only if T05/Q2 finds the generated data quality report carries the `1v1 ranked ladder` mis-label propagated from the ID 6 + ID 18 population; BLOCKER-1 sub-check 6 fix)
- `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_02_data_quality_report.ipynb` (conditional⁶)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_quality_report_aoe2companion.md` (conditional⁶)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` (conditional⁶ — under ⁶: Step 01_06_01 (data dictionary) and/or Step 01_06_02 (data quality report) rows only)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md` (conditional⁶ — under ⁶: Step 01_06_01 (data dictionary) and/or Step 01_06_02 (data quality report) entries only)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml` (conditional⁶ — under ⁶: Step 01_06_01 (data dictionary) and/or Step 01_06_02 (data quality report) rows only)
- `thesis/pass2_evidence/methodology_risk_register.md` (potentially
  updated for cross-region threshold and qp_rm_1v1 risk note)
- `thesis/pass2_evidence/dependency_lineage_audit.md` (potentially
  updated for 14A.1 status)
- `thesis/pass2_evidence/audit_cleanup_summary.md` (Spec amendment
  classifications sub-section)
- `thesis/pass2_evidence/notebook_regeneration_manifest.md`
  (conditional⁶ — manifest entry for `T16 14A.1 finding` cause and/or
  `T05/Q2 BLOCKER-1 propagation` cause)

**Read scope:**
- `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md`
- `thesis/pass2_evidence/cross_dataset_comparability_matrix.md`
- `thesis/pass2_evidence/methodology_risk_register.md`
- `reports/specs/02_00_feature_input_contract.md` (and its §7)
- `reports/specs/02_01_leakage_audit_protocol.md` (and its §7)
- `.claude/ml-protocol.md`
- `.claude/scientific-invariants.md`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_sc2egset.md`
  (for empirical retention threshold binding)
- `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_01_data_dictionary.py`
  (read-only inspection to confirm generated status)
- `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_02_data_quality_report.py`
  (read-only inspection to confirm generated status; BLOCKER-1 sub-check 6 fix)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_quality_report_aoe2companion.md`
  (read-only inspection to confirm presence of `1v1 ranked ladder` mis-label per T05 step 5 propagation trace)

---

### T17 — REVIEW_QUEUE and WRITING_STATUS synchronization

**Objective:** Make repo state internally consistent. Mirrors source
`Stage 15`.

**Instructions:**
1. Update `thesis/chapters/REVIEW_QUEUE.md` to reflect: resolved
   flags; preserved flags; new flags; Pass 2 status; evidence-artifact
   references.
2. Update `thesis/WRITING_STATUS.md` per the SKELETON / BLOCKED /
   DRAFTABLE / DRAFTED / REVISED / FINAL semantics in
   `.claude/rules/thesis-writing.md`.
3. Ensure no resolved issue remains pending and no unresolved issue
   is silently dropped.
4. Update `thesis/pass2_evidence/cleanup_flag_ledger.md` to match
   final chapter state.

**Verification:**
- `REVIEW_QUEUE.md` agrees with chapter files post-T11/T12/T13/T14.
- `WRITING_STATUS.md` agrees with actual readiness.
- `cleanup_flag_ledger.md` agrees with both.

**File scope:**
- `thesis/chapters/REVIEW_QUEUE.md`
- `thesis/WRITING_STATUS.md`
- `thesis/pass2_evidence/cleanup_flag_ledger.md`

**Read scope:**
- `thesis/chapters/01_introduction.md` (post-T12)
- `thesis/chapters/02_theoretical_background.md` (post-T13)
- `thesis/chapters/03_related_work.md` (post-T14)
- `thesis/chapters/04_data_and_methodology.md` (post-T11)
- `thesis/pass2_evidence/literature_verification_log.md`
- `thesis/pass2_evidence/methodology_risk_register.md`

---

### T18 — Final thesis consistency pass

**Objective:** Make Chapters 1–4 read as one coherent thesis draft.
Mirrors source `Stage 16`.

**Instructions:**
1. Search and fix inconsistent terminology across Chapters 1–4:
   ranked ladder; ladder; quickplay; matchmaking; public online
   matches; tournament; professional; replay corpus; telemetry;
   pre-game; in-game; historical features.
2. Remove internal workflow language from thesis prose: `Phase 01`,
   `PR #TBD`, `BACKLOG.md`, `grep`, internal invariant names unless
   deliberately explained, raw implementation debugging language —
   unless placed in a clearly marked reproducibility appendix.
3. Keep academic register; preserve necessary uncertainty flags;
   ensure title / RQ / method / data alignment.

**Verification:**
- `rg -n "Phase 01|PR #TBD|BACKLOG\.md|\bgrep\b|post-F1|\bbranch master\b|\bon master\b|\bmerged to master\b|\binto master\b" thesis/chapters/`
  returns no matches outside an explicitly labelled reproducibility
  appendix (regex tightened per NOTE-3/13 fix; avoids false
  positives on "master\'s thesis" / "master plan" / "Master\'s
  degree").
- Terminology audit returns consistent vocabulary across Chapters
  1–4.
- Remaining flags are deliberate and recorded in
  `cleanup_flag_ledger.md`.

**File scope:**
- `thesis/chapters/01_introduction.md`
- `thesis/chapters/02_theoretical_background.md`
- `thesis/chapters/03_related_work.md`
- `thesis/chapters/04_data_and_methodology.md`

**Read scope:**
- `thesis/pass2_evidence/cleanup_flag_ledger.md` (post-T17)
- `thesis/chapters/REVIEW_QUEUE.md` (post-T17)

---

### T19 — Full review gates (Round 3 of 3)

**Objective:** Run mechanical, deep, and adversarial review gates on
the entire PR before merge. Mirrors source `Stage 17`. This is
**Round 3 of 3** adversarial cycles per Assumption (D); it counts
toward the symmetric 3-round cap per project memory
`feedback_adversarial_cap_execution.md`. T02 (pre-execution) was
Round 1; T10 (mid-PR) was Round 2; T19 is Round 3. No further
adversarial dispatches are permitted within this PR.

**Instructions:**
1. Run mechanical checks (each line is a single command):
   - `git diff --stat`
   - `rg "\[REVIEW:|\[UNVERIFIED:|\[NEEDS CITATION|\[NEEDS JUSTIFICATION|\[TODO" thesis/chapters`
   - `rg "ranked ladder|ladder|quickplay|random_map|internalLeaderboardId|leaderboard" thesis/chapters thesis/pass2_evidence`
   - `rg "Phase 01|PR #TBD|BACKLOG\.md|\bgrep\b|post-F1|\bbranch master\b|\bon master\b|\bmerged to master\b|\binto master\b" thesis/chapters`
     (NOTE-3/13 fix: regex avoids false positives on "master\'s
     thesis" / "master plan" / "Master\'s degree"; targets only
     branch/workflow leakage uses of "master")
   - `rg "17829625|14963484|SC2EGSet|SC2ReSet" thesis/chapters thesis/references.bib`
   - `rg "50 cywilizacji|50 civilizations|45 cywilizacji|45 civilizations" thesis/chapters`
   - `rg "Demsar|Demšar|Nemenyi|Benavoli|Friedman" thesis/chapters`
   - `rg "ECE|Brier|log-loss|calibration|kalibr" thesis/chapters`
2. **Notebook validation (WARNING-2/7 fix).** Use the nbconvert
   command from T07 step 1
   (`source .venv/bin/activate && poetry run jupyter nbconvert --to notebook --execute --inplace <path-to-notebook.ipynb>`)
   for any notebook validation. Do not invent commands. Run only on
   notebooks the manifest declares regenerated.
3. Document the commands actually run in
   `thesis/pass2_evidence/reviewer_gate_report.md`.
4. Dispatch `@reviewer-deep` for lineage completeness, no stale
   artifacts used, ROADMAP/notebook/artifact/log/thesis consistency,
   no raw data mutation, no contradictory cross-chapter claims, no
   unsupported quantitative claims.
5. **Dispatch `@reviewer-adversarial` (Round 3 of 3, BLOCKER-5 fix)
   for** AoE2 ranked-ladder wording (verify no qp_rm_1v1 mis-label
   propagation survives); cross-game comparability; methodology
   overclaims; literature gap; leakage; evidence traceability; and
   examiner-style stress test. **No further adversarial dispatches
   are permitted within this PR.** If a finding from T19 requires
   substantial re-work, re-execution into a 4th round is NOT
   permitted; the PR must instead either (a) accept WARNINGs as
   documented limitations recorded in
   `methodology_risk_register.md` and `audit_cleanup_summary.md`,
   or (b) escalate to user for explicit cap-waiver signoff (record
   the waiver in `audit_cleanup_summary.md`).
6. Resolve every BLOCKER finding before T20. Record WARNINGs in the
   methodology risk register and audit cleanup summary.

**Verification:**
- `thesis/pass2_evidence/reviewer_gate_report.md` exists and lists
  all commands run with their outputs (or output summaries).
- The Round 3 of 3 dispatch is recorded; no Round 4 dispatch has
  occurred (cap respected per Assumption (D)).
- No BLOCKER finding remains.
- WARNINGs are documented in `methodology_risk_register.md` and
  `audit_cleanup_summary.md`.
- If a cap waiver was sought, the user signoff is recorded in
  `audit_cleanup_summary.md`.

**File scope:**
- `thesis/pass2_evidence/reviewer_gate_report.md`
- `thesis/pass2_evidence/methodology_risk_register.md` (potentially updated)
- `thesis/pass2_evidence/audit_cleanup_summary.md` (potentially updated)

**Read scope:**
- All thesis chapters (post-T18)
- All pass2_evidence files (post-T17)
- `reports/research_log.md` (post-T08/T09)

---

### T20 — Final PR summary and PR body draft

**Objective:** Make the PR reviewable by a human without
reconstructing context from chat. Mirrors source `Stage 18`.

**Instructions:**
1. Finalise `thesis/pass2_evidence/audit_cleanup_summary.md` with the
   14 mandatory sections from source §6 Stage 18: PR scope; files
   changed; notebooks changed; artifacts regenerated; ROADMAP Steps
   changed; research_log entries added/updated; thesis sections
   changed; claims weakened; claims corrected; claims still
   unresolved; remaining supervisor-facing risks; commands run;
   review agents run; known limitations.
2. Draft the PR body following the template in source §6 Stage 18
   (Summary, Major changes, Key decisions, Validation, Remaining
   risks). Per project memory, write the body to
   `.github/tmp/pr.txt` for user review and use `--body-file`. Delete
   `.github/tmp/pr.txt` after PR creation per project memory.
3. Do not run `gh pr create` — the user executes it; the executor
   only proposes the command.

**Verification:**
- `thesis/pass2_evidence/audit_cleanup_summary.md` contains all 14
  sections.
- `.github/tmp/pr.txt` exists with the drafted PR body and is
  proposed (not created) for user review.
- PR is reviewable end-to-end without chat context.

**File scope:**
- `thesis/pass2_evidence/audit_cleanup_summary.md`
- `.github/tmp/pr.txt` (ephemeral; deleted after PR created)

**Read scope:**
- All pass2_evidence files (post-T19)
- All thesis chapters (post-T18)
- All updated ROADMAP, research_log, STEP_STATUS files (post-T08)
- `reports/research_log.md` (post-T09)

---

## File Manifest

> **Action `Read-only (frozen)`** denotes files that exist on disk and
> are referenced by tasks but must not be mutated by any task in this
> PR per the `thesis/pass2_evidence/README.md` Pass-2-handoff
> convention. Listed for completeness so executors do not accidentally
> treat them as out-of-scope artifacts.

Footnotes:

- ¹ Conditional on T03/T04/T05 finding that a Step's question, method,
  inputs, outputs, gate, thesis mapping, or invariants/scientific
  invariants applied have changed (per source §4.2 / §6 Stage 5).
- ² Conditional on T06 declaring the Step's artifacts stale and
  requiring regeneration (per source §6 Stage 6 and §8 class C/D).
- ³ Conditional on T07 having regenerated artifacts or T05/T11–T14
  having reinterpreted existing artifacts in a thesis-relevant way
  (per source §6 Stage 7).
- ⁴ Conditional on T15 finding the spec needs to be created or
  updated (per source §6 Stage 14). The README is updated only if a
  spec is added or renamed. Per BLOCKER-2 fix, every body change to
  CROSS-02-00 / CROSS-02-01 carries a §7 amendment-log row and a
  frontmatter version bump in the same commit.
- ⁵ Conditional on T15 confirming SC2 in-game telemetry features are
  retained, gating T16 sub-step 14A.6 execution. If telemetry is
  dropped, no Step `01_03_05` is created and the row remains
  un-touched in this PR.
- ⁶ Conditional on T16 14A.1 finding generated data-dictionary
  contradictions or on T05/Q2 finding that the generated
  aoe2companion data-quality report carries the `1v1 ranked ladder`
  mis-label propagated from the ID 6 + ID 18 population. This
  condition covers both Step 01_06_01 `data_dictionary_aoe2companion`
  and Step 01_06_02 `data_quality_report_aoe2companion`. If either
  generated artifact is repaired, the corresponding ROADMAP Step,
  paired notebook, generated artifact, research_log entry, and
  STEP_STATUS row must be updated via ROADMAP → notebook → artifact
  → research_log → STEP_STATUS discipline. Manual patching of the
  generated artifacts is forbidden (G3/G4). The
  `notebook_regeneration_manifest.md` records the cause
  (`T16 14A.1 finding` for the data dictionary,
  `T05/Q2 BLOCKER-1 propagation` for the data quality report) for
  each modified file. Conditional⁶ rows may overlap with
  conditional¹/²/³ for the same files; the conditional set is a
  union of trigger conditions (BLOCKER-3 fix; BLOCKER-1 sub-check 6
  fix).
- ⁷ Conditional on T11 finding new Chapter 4 numbers requiring
  crosswalk entries beyond what `sec_4_1_crosswalk.md` and
  `sec_4_2_crosswalk.md` already cover. The
  `thesis/pass2_evidence/README.md` versioning convention requires
  versioned `sec_<id>_vN_<type>.md` files when handoff-frozen
  crosswalks need extension (BLOCKER-4 fix).

| File | Action |
|------|--------|
| `planning/current_plan.md` | Rewrite |
| `planning/current_plan.critique_resolution.md` | Create (records resolution of BLOCKER-1..5, WARNING-1..5, NOTE-1..3 against critique v1) |
| `thesis/pass2_evidence/audit_cleanup_summary.md` | Create |
| `thesis/pass2_evidence/dependency_lineage_audit.md` | Create |
| `thesis/pass2_evidence/cleanup_flag_ledger.md` | Create |
| `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` | Create |
| `thesis/pass2_evidence/cross_dataset_comparability_matrix.md` | Create |
| `thesis/pass2_evidence/claim_evidence_matrix.md` | Create |
| `thesis/pass2_evidence/notebook_regeneration_manifest.md` | Create |
| `thesis/pass2_evidence/literature_verification_log.md` | Create |
| `thesis/pass2_evidence/methodology_risk_register.md` | Create |
| `thesis/pass2_evidence/phase02_readiness_hardening.md` | Create |
| `thesis/pass2_evidence/reviewer_gate_report.md` | Create |
| `thesis/pass2_evidence/README.md` | Update (conditional⁷ — only if new evidence-file relationships are introduced; e.g. if v2 crosswalks are created or if new claim_evidence_matrix structure requires index updates) |
| `thesis/pass2_evidence/sec_4_1_crosswalk.md` | Read-only (frozen — Pass-2 handoff convention) |
| `thesis/pass2_evidence/sec_4_1_halt_log.md` | Read-only (frozen) |
| `thesis/pass2_evidence/sec_4_2_crosswalk.md` | Read-only (frozen) |
| `thesis/pass2_evidence/sec_4_2_halt_log.md` | Read-only (frozen) |
| `thesis/pass2_evidence/sec_4_1_v2_crosswalk.md` | Create (conditional⁷ — only if T11 finds new numbers requiring crosswalk entries) |
| `thesis/pass2_evidence/sec_4_2_v2_crosswalk.md` | Create (conditional⁷) |
| `thesis/chapters/01_introduction.md` | Update |
| `thesis/chapters/02_theoretical_background.md` | Update |
| `thesis/chapters/03_related_work.md` | Update |
| `thesis/chapters/04_data_and_methodology.md` | Update |
| `thesis/chapters/REVIEW_QUEUE.md` | Update |
| `thesis/WRITING_STATUS.md` | Update |
| `thesis/references.bib` | Update |
| `reports/research_log.md` | Update |
| `reports/specs/01_05_preregistration.md` | Update (conditional⁴) |
| `reports/specs/01_06_readiness_criteria.md` | Update (conditional⁴) |
| `reports/specs/02_00_feature_input_contract.md` | Update (conditional⁴ — §7 amendment, classify as major v3→v4 per BLOCKER-2 fix) |
| `reports/specs/02_01_leakage_audit_protocol.md` | Update (conditional⁴ — §7 amendment, classify as major v1→v2 per BLOCKER-2 fix) |
| `reports/specs/README.md` | Update (conditional⁴) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` | Update (conditional¹/⁵) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` | Update (conditional³/⁵) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` | Update (conditional³/⁵) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/**` | Update (conditional² — only files explicitly declared stale in `notebook_regeneration_manifest.md` after T06; manifest is the authoritative bound; bare wildcard does not authorize touching arbitrary files — WARNING-5/10 fix) |
| `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/**` | Update (conditional² — manifest-bound, see WARNING-5/10 wording above) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` | Update (conditional¹) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md` | Update (conditional³) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml` | Update (conditional³) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/**` | Update (conditional² — manifest-bound, see WARNING-5/10 wording above) |
| `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/**` | Update (conditional² — manifest-bound) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` | Update (conditional¹/⁶ — under ⁶: Step 01_06_01 (data dictionary) and/or Step 01_06_02 (data quality report) rows only) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md` | Update (conditional³/⁶ — under ⁶: Step 01_06_01 (data dictionary) and/or Step 01_06_02 (data quality report) entries only) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml` | Update (conditional³/⁶ — under ⁶: Step 01_06_01 (data dictionary) and/or Step 01_06_02 (data quality report) rows only) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/**` | Update (conditional² — manifest-bound, see WARNING-5/10 wording above) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoe2companion.csv` | Update (conditional⁶) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoe2companion.md` | Update (conditional⁶) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_quality_report_aoe2companion.md` | Update (conditional⁶ — Step 01_06_02 generated artifact; mis-label propagation repair path per T05/Q2 BLOCKER-1 sub-check 6) |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/**` | Update (conditional² — manifest-bound) |
| `sandbox/sc2/sc2egset/**` | Update (conditional² — only files explicitly declared stale in `notebook_regeneration_manifest.md` after T06; manifest is the authoritative bound; bare wildcard does not authorize touching arbitrary files — WARNING-5/10 fix) |
| `sandbox/aoe2/aoestats/**` | Update (conditional² — manifest-bound, see WARNING-5/10 wording above) |
| `sandbox/aoe2/aoe2companion/**` | Update (conditional² — manifest-bound, see WARNING-5/10 wording above) |
| `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_01_data_dictionary.py` | Update (conditional⁶) |
| `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_01_data_dictionary.ipynb` | Update (conditional⁶) |
| `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_02_data_quality_report.py` | Update (conditional⁶ — Step 01_06_02 generator; mis-label propagation repair path per T05/Q2 BLOCKER-1 sub-check 6) |
| `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_02_data_quality_report.ipynb` | Update (conditional⁶) |
| `.github/tmp/pr.txt` | Create (ephemeral; deleted after PR creation) |

## Gate Condition

Pulled from source §9 (Acceptance criteria for the whole PR), grouped
by sub-area. The PR merges only when every condition below holds.

### Evidence

- `thesis/pass2_evidence/dependency_lineage_audit.md` exists and maps
  thesis claims to upstream evidence.
- `thesis/pass2_evidence/cleanup_flag_ledger.md` exists and matches
  final chapter flags.
- `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` exists and
  supports final terminology, including the qp_rm_1v1 mis-label
  propagation trace and the "default to quickplay/matchmaking on
  ambiguity" fallback rule.
- `thesis/pass2_evidence/cross_dataset_comparability_matrix.md` exists
  and matches thesis framing.
- `thesis/pass2_evidence/claim_evidence_matrix.md` exists and is
  consistent with final Chapters 1–4 (and references
  `sec_4_1_crosswalk.md` / `sec_4_2_crosswalk.md` and any v2
  crosswalks per BLOCKER-4 fix).
- `thesis/pass2_evidence/notebook_regeneration_manifest.md` documents
  whether notebooks/artifacts were regenerated and is the
  authoritative bound on every wildcard manifest row.
- `thesis/pass2_evidence/literature_verification_log.md` exists.
- `thesis/pass2_evidence/methodology_risk_register.md` exists,
  records the 17 source risks plus the 18th PR scope risk, and
  records the empirically derived (or deferred) cross-region
  retention threshold.
- `thesis/pass2_evidence/phase02_readiness_hardening.md` exists if any
  imported readiness items are used.
- `thesis/pass2_evidence/reviewer_gate_report.md` exists.
- `thesis/pass2_evidence/audit_cleanup_summary.md` exists and records
  the mid-PR adversarial gate (T10, Round 2 of 3), the final
  adversarial gate (T19, Round 3 of 3), branch-prefix operational
  verification, spec amendment classifications, and (if applicable)
  the scope-explosion escalation outcome.
- `planning/current_plan.critique_resolution.md` exists and records
  resolution of every BLOCKER-1..5, WARNING-1..5, and NOTE-1..3 from
  the critique against this revision (v2).

### Thesis

- Chapters 1–4 no longer overclaim about ranked ladder, cross-game
  comparison, literature gap, calibration, feature importance,
  statistical testing, or ICC.
- No qp_rm_1v1-derived "ranked ladder" wording survives in any
  Chapter unless explicitly justified by external verification
  overturning the on-disk evidence (BLOCKER-1 fix).
- All remaining flags in Chapters 1–4 are intentional and recorded in
  `cleanup_flag_ledger.md`.
- `thesis/chapters/REVIEW_QUEUE.md` and `thesis/WRITING_STATUS.md`
  are synchronized.

### Data and provenance

- `aoestats` and `aoe2companion` are described separately throughout.
- SC2EGSet is described as a tournament/professional replay corpus,
  not ladder data.
- AoE2 source terminology is source-specific and evidence-bounded
  per `aoe2_ladder_provenance_audit.md`.
- No stale artifacts are cited from any thesis chapter or
  pass2_evidence file.

### Workflow

- ROADMAP changes precede notebook changes whenever Step semantics
  changed.
- Notebook changes regenerate artifacts via end-to-end execution
  using the standard nbconvert command (WARNING-2/7 fix).
- Regenerated artifacts are logged in per-dataset `research_log.md`.
- Logs map to thesis claims via `claim_evidence_matrix.md` (and
  `sec_4_*_crosswalk.md` / `sec_4_*_v2_crosswalk.md` for Chapter 4).
- `STEP_STATUS.yaml` agrees with the per-dataset logs in every
  affected dataset.
- Every modified file under `sandbox/<game>/<dataset>/**` or
  `src/rts_predict/games/<game>/datasets/<dataset>/reports/artifacts/**`
  has a corresponding row in `notebook_regeneration_manifest.md`
  (BLOCKER-3 + WARNING-5/10 fix).
- Raw data are untouched.

### Specs (BLOCKER-2 fix)

- Each affected spec's frontmatter `version` field is bumped per
  the spec's own §7 protocol (CROSS-02-00 v3→v4 if methodology-
  affecting; CROSS-02-01 v1→v2 if §2 audit-dimensions or §5 gate
  changed).
- Each affected spec's amendment log has a new dated row recording
  date, author, motivation, and scope.
- LOCKED-vs-modified state is consistent (no body change against
  stale frontmatter).
- Major-vs-minor classification is recorded in
  `audit_cleanup_summary.md` under "Spec amendment classifications".
- Planner-science + reviewer-adversarial co-signoff is satisfied by
  the consolidated mid-PR adversarial gate at T10.

### Review

- `@reviewer` mechanical checks completed.
- `@reviewer-deep` deep review completed.
- `@reviewer-adversarial` adversarial review completed in exactly
  3 rounds: T02 (plan critique), T10 (consolidated mid-PR gate),
  T19 (final PR review). No Round 4 dispatch occurred unless an
  explicit user cap-waiver signoff is recorded in
  `audit_cleanup_summary.md`.
- No unresolved BLOCKER.
- All WARNINGs are documented in
  `methodology_risk_register.md` and/or `audit_cleanup_summary.md`.

## Out of scope

Pulled from source §3 (Do-not-adopt list from the prior plan), with
the prior PR's deferred items.

- **Two-PR branching.** This PR is single. No "cleanup PR + validation
  PR" split. (See T03 step 7 escape valve: if scope explodes, the
  user may approve a split — but the *default* remains single PR.)
- **Manual edits to generated artifacts.** Prohibited (G4). All
  regeneration goes through the upstream notebook (including the
  generated data dictionary per BLOCKER-3 fix).
- **Cat-C classification of methodology spec changes.** Spec edits
  that affect methodology require the consolidated mid-PR
  reviewer-adversarial gate at T10 and are part of this Cat-F PR;
  they do not become a side Cat-C chore.
- **Line-number-based CSV edits.** Forbidden (G11).
- **Leaving same-class contradictions unresolved for scope discipline.**
  Forbidden (G12); resolve same-class contradictions in this PR.
- **Treating SC2 `tracker_events_raw` validation as a substitute for
  AoE2 ranked-ladder provenance.** AoE2 provenance is governed by T05;
  SC2 tracker validation is a separate optional T16 sub-step.
- **Phase 02 Step `02_01` kickoff.** The previous Pre-Phase-02
  Readiness plan's T03 is deferred. This PR does not begin Phase 02
  feature engineering — only readiness hardening.
- **Modifying raw data.** Always out of scope (G5; deny-listed by repo
  permissions).
- **Renaming the branch to `docs/thesis-*`.** The user explicitly
  approved the `thesis/audit-methodology-lineage-cleanup` branch name;
  do not rename. T01 step 5 verifies the prefix does not break
  CI/hooks/templates.
- **Producing the adversarial critique itself.** That is
  `@reviewer-adversarial`'s job, dispatched by the parent session;
  this plan only requests it.
- **Mutating the v1 Pass-2-evidence crosswalks.** Per
  `thesis/pass2_evidence/README.md`'s Pass-2-handoff convention,
  `sec_4_1_crosswalk.md` / `sec_4_1_halt_log.md` /
  `sec_4_2_crosswalk.md` / `sec_4_2_halt_log.md` are frozen. New
  Chapter 4 crosswalk needs go into `sec_4_*_v2_*.md` files (BLOCKER-4
  fix).
- **A 4th adversarial round.** Per Assumption (D), exactly 3 rounds
  (T02, T10, T19) are permitted. Round 4 requires explicit user
  cap-waiver signoff.

## Open questions

Each question names what resolves it and at which task.

- **Q1.** Which Steps require notebook regeneration vs only
  re-interpretation? — Resolves at T03 (dependency lineage audit)
  and T06 (regeneration decision). If T03 declares more than 10
  Steps stale across all three datasets, the executor halts and
  escalates per T03 step 7 (WARNING-1/6 fix).
- **Q2.** *(Rewritten per BLOCKER-1 fix.)* Confirm the on-disk
  classification of `aoe2companion` `internalLeaderboardId = 18` as
  `qp_rm_1v1` against external aoe2companion / aoe2.net / source
  documentation, and trace the propagation of the `1v1 ranked ladder`
  mis-label from the generated data quality report
  (`data_quality_report_aoe2companion.md`, currently identified around
  line 29) into thesis Chapter 4 §4.1.3 / §4.2.3 and any other
  downstream artifact or prose.

  The conservative default is:
  - `internalLeaderboardId = 6` / `rm_1v1` may be treated as the ranked
    1v1 Random Map candidate, subject to external/source verification;
  - `internalLeaderboardId = 18` / `qp_rm_1v1` is treated as
    quickplay / matchmaking-derived, not ranked ladder, unless external
    documentation explicitly overturns the on-disk evidence;
  - if external documentation is ambiguous or unavailable, default to
    quickplay/matchmaking terminology for ID 18 and never default to
    ranked ladder.

  Decide whether IDs 6 and 18 should be combined, split, or one of them
  excluded. If they remain combined, the combined `aoe2companion` corpus
  must not be described as simply "ranked ladder"; it must use
  source-specific wording such as "public 1v1 Random Map
  ranked/quickplay matchmaking records" or another wording justified by
  `aoe2_ladder_provenance_audit.md`.

  Resolves at T05 sub-step 4.2 with `@lookup` external verification and
  downstream propagation audit. If the mislabeled data quality report is
  generated, remediation must follow the ROADMAP → notebook → artifact →
  research_log → STEP_STATUS lineage discipline rather than manual patching.
- **Q3.** *(Rewritten per WARNING-4/9 fix.)* Confirm aoestats
  `leaderboard='random_map'` aggregation semantics by reading
  `01_03_02_true_1v1_profile.md` (Jaccard finding if present),
  `01_04_01_data_cleaning.md` (R02 rule if present), and the
  aoestats source documentation via `@lookup`. If source
  documentation is silent on whether `random_map` is exclusively the
  ranked queue, classify aoestats as "source-specific aggregation
  with semantic opacity" and weaken thesis terminology accordingly.
  — Resolves at T05 sub-step 4.1.
- **Q4.** Are SC2 in-game telemetry features (derived from
  `tracker_events_raw`) retained in the final thesis methodology? —
  Gates whether T16 sub-step 14A.6 (Step `01_03_05` semantic
  validation) executes. Resolves by user decision at or before T15.
- **Q5.** Does merge governance accept the
  `thesis/audit-methodology-lineage-cleanup` branch-prefix deviation
  from the conventional `docs/thesis-*` prefix? — Already
  user-approved (recorded once in Assumptions B); operational
  CI/hook/template impact is verified at T01 step 5 (WARNING-3/8
  fix).

---

For Category F, adversarial critique is required before execution. Round 1 (the plan critique at `planning/current_plan.critique.md`) has already been produced; this revision (v2) of `planning/current_plan.md` resolves all 5 BLOCKERs, 5 WARNINGs, and 4 NOTEs from that critique, with the resolution log at `planning/current_plan.critique_resolution.md`. Implementation begins only after the parent session confirms BLOCKERs are resolved (T02 verification). Subsequent adversarial rounds are: Round 2 — consolidated mid-PR gate at T10 (covers T05 provenance, T10 risk register, T15 + T16 14A.2 / 14A.3 spec changes); Round 3 — final PR adversarial review at T19. No further adversarial dispatches are permitted within this PR per the symmetric 3-round cap (Assumption (D)).
