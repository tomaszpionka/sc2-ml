# Production-ready plan: thesis audit cleanup PR

**Repository:** `tomaszpionka/rts-outcome-prediction`  
**PR title:** `thesis: harden scientific methodology, AoE2 data provenance, and thesis evidence lineage`  
**Branch:** `thesis/audit-methodology-lineage-cleanup`  
**Mode:** one large PR, executed in staged internal phases  
**Primary ordering:** `lineage audit → AoE2 ladder provenance → ROADMAP/notebook/artifact/log repair → thesis rewrite → review gates`

This document is the final consolidated production plan. It combines the broad scientific-audit cleanup plan with the useful parts of the later Claude-generated “Pre-Phase-02 Readiness” plan, while rejecting that plan’s unsafe parts: two-PR branching, manual edits to generated artifacts, methodology-affecting changes classified as mechanical cleanup, line-number-based CSV edits, and treating SC2 `tracker_events_raw` validation as a substitute for AoE2 provenance.

---

After Claude Code creates `planning/current_plan.md`, use:

```text
Now invoke @reviewer-adversarial to critique `planning/current_plan.md`.

The critique must specifically attack:
- whether the plan preserves ROADMAP → notebook → artifact → research_log → thesis lineage;
- whether AoE2 ranked ladder / quickplay / matchmaking semantics are handled before thesis rewrite;
- whether generated artifacts are protected from manual patching;
- whether spec changes are incorrectly treated as mechanical cleanup;
- whether temporal leakage and stale-artifact risks are controlled;
- whether the previous Claude-generated T01/T02 plan was incorporated safely without adopting its unsafe assumptions.

Do not begin implementation until all BLOCKERs are resolved or explicitly converted into documented non-executable constraints.
```

---

## 1. Executive summary

This PR hardens the thesis draft and the repository evidence chain after external scientific audit. The thesis title is:

> “A comparative analysis of methods for predicting game results in real-time strategy games, based on the examples of StarCraft II and Age of Empires II.”

The main scientific risk is not style. The main risk is that the thesis currently may overstate what the data support, especially around:

1. whether AoE2 data are truly **ranked ladder** data or more broadly public multiplayer / ladder / matchmaking-derived records;
2. whether `aoestats` and `aoe2companion` represent the same population;
3. whether `aoe2companion` combines ranked and quickplay-like 1v1 Random Map records;
4. whether SC2 tournament/professional replay data can be compared directly with AoE2 public ladder/matchmaking data;
5. whether thesis claims trace cleanly to ROADMAP Steps, notebooks, generated artifacts, and research logs;
6. whether planned feature engineering and evaluation protocols prevent temporal leakage;
7. whether the thesis uses cautious, evidence-bounded language about novelty, calibration, feature importance, and statistical inference.

The PR must therefore repair both prose and evidence lineage. It must not merely “make the chapters sound better.”

---

## 2. Agent routing

Use the repository’s existing agent system.

### Required routing

- `@planner-science`  
  Use first. It owns the master plan because this cleanup touches thesis methodology, data provenance, notebooks, generated artifacts, validation gates, and scientific claims.

- `@reviewer-adversarial`  
  Use immediately after `planning/current_plan.md` is created. It must challenge the plan before execution. Use again at the end for examiner-style critique.

- `@executor`  
  Use for implementation only after the plan has passed adversarial critique.

- `/model opus`  
  Use during implementation for methodology-heavy reasoning: AoE2 provenance, source semantics, thesis claims, temporal leakage, ROADMAP/notebook/artifact/log dependencies, and chapter rewrites.

- `@writer-thesis`  
  Use only after evidence artifacts are established. It may revise prose, but must not invent evidence or remove unresolved uncertainty.

- `@lookup`  
  Use for external verification of papers, official documentation, source/API semantics, bibliographic metadata, and current source details.

- `@reviewer`  
  Use for mechanical checks, file consistency, flag searches, and command/test summaries.

- `@reviewer-deep`  
  Use for final heavy review of lineage, artifacts, specs, invariants, and thesis consistency.

### Execution constraint

No implementation may begin until:

1. `planning/current_plan.md` exists;
2. `@reviewer-adversarial` has reviewed it;
3. all adversarial BLOCKERs have been fixed or explicitly documented as non-executable constraints.

---

## 3. Read-first list

Before planning or editing, read and cite internally in the plan as needed.

### Core process and invariant docs

- `CLAUDE.md`
- `.claude/README.md`
- `.claude/scientific-invariants.md`
- `.claude/ml-protocol.md`
- `.claude/rules/thesis-writing.md`
- `docs/agents/AGENT_MANUAL.md`
- `docs/templates/planner_output_contract.md`
- `docs/TAXONOMY.md`
- `docs/PHASES.md`
- `docs/INDEX.md`

### Research workflow and lineage docs

- every relevant `ROADMAP.md`, including dataset-specific ROADMAP files;
- `docs/research/ROADMAP.md`, if present;
- `docs/research/RESEARCH_LOG.md`, if present;
- root `reports/research_log.md`;
- all relevant per-dataset `research_log.md` files;
- all relevant `STEP_STATUS.yaml` and `PHASE_STATUS.yaml` files.

### Thesis files

- `thesis/THESIS_STRUCTURE.md`
- `thesis/WRITING_STATUS.md`
- `thesis/chapters/REVIEW_QUEUE.md`
- `thesis/chapters/01_introduction.md`
- `thesis/chapters/02_theoretical_background.md`
- `thesis/chapters/03_related_work.md`
- `thesis/chapters/04_data_and_methodology.md`
- `thesis/references.bib`

### AoE2 data/provenance

Read all relevant files under:

- `src/rts_predict/games/aoe2/datasets/aoestats/**`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/**`

Pay special attention to:

- `reports/INVARIANTS.md`
- `reports/research_log.md`
- `reports/ROADMAP.md`
- `reports/STEP_STATUS.yaml`
- `reports/artifacts/01_exploration/**`
- schemas under `data/db/schemas/**`
- sandbox notebooks and notebook pairs.

### SC2 data/provenance

Read all relevant files under:

- `src/rts_predict/games/sc2/datasets/sc2egset/**`

Pay special attention to:

- `reports/INVARIANTS.md`
- `reports/research_log.md`
- `reports/ROADMAP.md`
- `reports/STEP_STATUS.yaml`
- `reports/artifacts/01_exploration/**`
- schemas under `data/db/schemas/**`
- sandbox notebooks and notebook pairs.

### Cross-dataset specs/reports

- `reports/specs/**`
- root `reports/research_log.md`
- any cross-dataset comparison artifacts or decision-gate files.

### Previous Claude-generated plan

If the previous Claude-generated “Pre-Phase-02 Readiness — T01 Cleanup + T02 tracker_events Semantic Validation” plan is available in the repo or pasted by the user, read it as an input artifact only.

Useful parts to incorporate:

- hypothesis/falsifier/gate style for validation tasks;
- DuckDB UTC requirement for timestamp joins;
- cold-start and rating-sparsity protocol, after AoE2 source semantics are verified;
- leakage audit pattern-conformance binding;
- SC2 cross-region fragmentation risk;
- optional SC2 `tracker_events_raw` semantic validation.

Do not adopt:

- two-PR branching;
- manual edits to generated artifacts;
- classifying methodology-affecting spec changes as simple mechanical cleanup;
- line-number-based CSV edits;
- leaving same-class known artifact contradictions unresolved merely for scope discipline;
- treating SC2 tracker validation as a substitute for AoE2 ranked ladder provenance.

---

## 4. Non-negotiable guardrails

### 4.1 Evidence before prose

Do not update thesis claims before verifying the evidence chain.

A thesis empirical claim is valid only if this lineage is intact:

```text
ROADMAP Step
  -> sandbox notebook pair (.py + .ipynb, if paired)
  -> generated artifacts
  -> research_log.md entry
  -> STEP_STATUS.yaml / gate status
  -> thesis prose or table
  -> REVIEW_QUEUE / WRITING_STATUS state
```

If the chain is incomplete, stale, contradictory, or missing, the claim must be corrected, weakened, flagged, or removed.

### 4.2 ROADMAP is upstream of notebooks

If the Step question, method, input, output, gate, thesis mapping, or invariant changes, update the relevant ROADMAP before touching the notebook.

Do not let a notebook silently answer a different question than the Step declares.

### 4.3 No surgical notebook fixes

If notebook logic changes:

1. update the relevant ROADMAP Step first;
2. mark prior artifacts from that Step as stale;
3. regenerate all declared outputs;
4. update the relevant per-dataset `research_log.md`;
5. update `STEP_STATUS.yaml` only after the log exists;
6. update downstream thesis prose, tables, specs, and review queues;
7. record the dependency in `notebook_regeneration_manifest.md`.

### 4.4 No manual edits to generated artifacts

Do not manually edit files under `reports/artifacts/` unless you first prove and document that the file is hand-maintained rather than generated.

If generated, update the upstream ROADMAP Step and notebook/generator, then regenerate the artifact.

### 4.5 No raw data mutation

Never edit raw data. Cleaning logic belongs in code/notebooks/pipeline. Derived artifacts may be regenerated.

### 4.6 No unsupported “ranked ladder” terminology

Do not call AoE2 data “ranked ladder” merely because the games are multiplayer online.

For each AoE2 source, verify using actual source fields and filters:

- `leaderboard`;
- `internalLeaderboardId`;
- rating fields;
- queue/mode labels;
- match type;
- map type;
- player count;
- AI/player indicators;
- winner/complementarity checks;
- source documentation.

If evidence is insufficient, use cautious terminology.

### 4.7 No clean causal game-vs-game comparison

Do not imply that differences between SC2 and AoE2 results are purely game-mechanical.

Preferred framing:

> comparison of prediction methods across two RTS titles under structurally different data regimes.

Not:

> pure causal comparison of StarCraft II vs Age of Empires II as games.

### 4.8 No temporal leakage

All features for a game at time `T` must use only information strictly before `T`.

Disallow:

- target match result leakage;
- future match leakage;
- same-match leakage;
- same-series leakage unless explicitly handled;
- post-game duration/stat leakage into pre-game models;
- random split language;
- legacy `create_temporal_split()` assumptions;
- `GLOBAL_TEST_SIZE` random-style assumptions.

### 4.9 Do not hide uncertainty

Do not delete `[REVIEW:]`, `[UNVERIFIED:]`, `[NEEDS CITATION]`, or `[NEEDS JUSTIFICATION]` merely to make the draft look cleaner.

Resolve only when evidence exists. Otherwise preserve, refine, or escalate the flag.

### 4.10 Grey literature discipline

Source documentation, API pages, community tools, GitHub repos, and forum/community pages may support data-provenance claims, but must not be presented as peer-reviewed scientific evidence.

### 4.11 No line-number-based artifact edits

Do not rely on CSV line numbers such as “row 65” or “row 70” as stable edit targets. Identify data-dictionary rows by stable field/table names and semantic keys.

### 4.12 Same-class contradiction rule

If the same artifact contains additional contradictions of the same type as the one being fixed, resolve them in the same PR through upstream regeneration or documented hand-maintained correction, unless doing so requires a clearly separate methodological decision.

Do not knowingly leave same-class contradictions unresolved merely for scope discipline.

---

## 5. Required PR outputs

Create or update this folder:

```text
thesis/pass2_evidence/
```

Required evidence files:

1. `thesis/pass2_evidence/dependency_lineage_audit.md`
2. `thesis/pass2_evidence/cleanup_flag_ledger.md`
3. `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md`
4. `thesis/pass2_evidence/cross_dataset_comparability_matrix.md`
5. `thesis/pass2_evidence/claim_evidence_matrix.md`
6. `thesis/pass2_evidence/notebook_regeneration_manifest.md`
7. `thesis/pass2_evidence/literature_verification_log.md`
8. `thesis/pass2_evidence/methodology_risk_register.md`
9. `thesis/pass2_evidence/phase02_readiness_hardening.md`
10. `thesis/pass2_evidence/reviewer_gate_report.md`
11. `thesis/pass2_evidence/audit_cleanup_summary.md`

Required updated project files, if affected:

- `planning/current_plan.md`
- relevant `ROADMAP.md` files
- relevant sandbox notebook `.py` / `.ipynb` pairs
- regenerated artifacts under relevant `reports/artifacts/`
- relevant schemas and assertion outputs, if changed
- relevant per-dataset `research_log.md`
- root `reports/research_log.md` for cross-dataset decisions
- relevant `STEP_STATUS.yaml` / `PHASE_STATUS.yaml`, if status changes
- `reports/specs/**`, if methodology or gates change
- `thesis/chapters/01_introduction.md`
- `thesis/chapters/02_theoretical_background.md`
- `thesis/chapters/03_related_work.md`
- `thesis/chapters/04_data_and_methodology.md`
- `thesis/chapters/REVIEW_QUEUE.md`
- `thesis/WRITING_STATUS.md`
- `thesis/references.bib`

---

## 6. Production plan

### Stage 0 — Preflight and repo safety

**Agent:** `@executor`, after plan approval.

Tasks:

1. Confirm clean git state.
2. Create branch:

   ```text
   thesis/audit-methodology-lineage-cleanup
   ```

3. Record baseline:
   - current commit hash;
   - changed/untracked files;
   - available test commands;
   - available notebook execution conventions;
   - available jupytext/pairing conventions, if any.
4. Do not overwrite user changes.
5. If unrelated uncommitted user changes exist, stop and document.

Writes:

- initial section in `thesis/pass2_evidence/audit_cleanup_summary.md`.

Acceptance:

- clean or explicitly documented working tree;
- branch created;
- no raw data touched.

---

### Stage 1 — Master plan and adversarial critique

**Agents:** `@planner-science`, then `@reviewer-adversarial`.

Tasks:

1. Produce `planning/current_plan.md` following `docs/templates/planner_output_contract.md`.
2. Classify this PR as primarily Category F, with embedded Category A/D work where notebooks/artifacts/specs are affected.
3. Include:
   - File Manifest;
   - source_artifacts;
   - invariants_touched;
   - failure modes;
   - expected outputs;
   - rollback plan;
   - review gates.
4. Run adversarial critique.
5. Fix BLOCKERs in the plan before execution.

Acceptance:

- `planning/current_plan.md` exists and is specific;
- adversarial critique exists or is summarized;
- no unresolved BLOCKER before execution.

---

### Stage 2 — Dependency lineage audit

**Agent:** `@executor` with `/model opus`.

Objective:

Build the dependency map before touching notebooks or thesis prose.

Tasks:

1. Read `docs/TAXONOMY.md` and extract the repo’s unit-of-work model:
   - Phase;
   - Step;
   - notebook;
   - artifact;
   - research log;
   - thesis mapping.
2. Locate relevant ROADMAP files.
3. Locate sandbox notebooks related to:
   - SC2EGSet Phase 01 and later;
   - aoestats Phase 01 and later;
   - aoe2companion Phase 01 and later;
   - cross-dataset comparison, if present.
4. For every thesis claim in Chapters 1–4 that depends on empirical project artifacts, map:
   - thesis file and section;
   - exact claim;
   - table/paragraph location;
   - claimed number or interpretation;
   - artifact path;
   - notebook path;
   - ROADMAP Step;
   - research_log entry;
   - STEP_STATUS;
   - status: intact / stale / missing / contradictory / prose-only.
5. Classify each planned edit as:
   - thesis-only wording change;
   - artifact interpretation change;
   - notebook logic change;
   - Step design change;
   - cross-dataset decision.

Writes:

- `thesis/pass2_evidence/dependency_lineage_audit.md`
- first version of `thesis/pass2_evidence/claim_evidence_matrix.md`
- first version of `thesis/pass2_evidence/notebook_regeneration_manifest.md`

Acceptance:

- every planned empirical thesis edit has lineage classification;
- every notebook that may need regeneration is listed;
- no notebook edits begin before this stage is complete.

---

### Stage 3 — Flag ledger and thesis audit inventory

**Agent:** `@executor`.

Objective:

Build a complete inventory of unresolved thesis flags and external audit issues.

Tasks:

1. Search Chapters 1–4 for:
   - `[REVIEW:]`
   - `[UNVERIFIED:]`
   - `[NEEDS CITATION]`
   - `[NEEDS JUSTIFICATION]`
   - `[TODO]`
   - internal workflow language such as `Phase`, `PR #TBD`, `BACKLOG.md`, `grep`, `post-F1`, `master`.
2. Cross-check with `thesis/chapters/REVIEW_QUEUE.md`.
3. Create a ledger with:
   - file;
   - section;
   - flag text;
   - issue category;
   - source needed;
   - upstream artifact needed;
   - proposed resolution;
   - status.
4. Add external audit issues even if no in-text flag exists:
   - AoE2 ranked ladder provenance;
   - SC2 vs AoE2 cross-game comparability;
   - SC2EGSet Zenodo/version distinction;
   - GarciaMendez2025 target game/details;
   - Hodge2021 phrasing;
   - AoE2 civilization count over time;
   - Demšar/Benavoli classifier-comparison framing;
   - ICC overcentrality;
   - ECE/calibration overclaiming;
   - grey literature vs peer-reviewed literature distinction;
   - workflow leakage in thesis prose.

Writes:

- `thesis/pass2_evidence/cleanup_flag_ledger.md`

Acceptance:

- every existing flag appears in the ledger;
- every audit issue is represented;
- REVIEW_QUEUE discrepancies are listed.

---

### Stage 4 — AoE2 ladder provenance audit

**Agents:** `@executor` with `/model opus`, `@lookup` where needed, then `@reviewer-adversarial`.

Objective:

Decide what the AoE2 datasets can defensibly be called.

Use hypothesis/falsifier/gate structure for the core questions.

#### 4.1 aoestats

Tasks:

1. Inspect source schema, notebooks, artifacts, logs, and ROADMAP.
2. Identify fields used to define population:
   - `leaderboard`;
   - map/mode;
   - rating fields;
   - player count;
   - winner fields;
   - AI/player filters;
   - queue/match-type fields, if any.
3. Verify what `leaderboard='random_map'` means in aoestats.
4. Determine whether aoestats records represent:
   - ranked 1v1 Random Map ladder;
   - public Random Map ladder;
   - broader ranked multiplayer;
   - source-specific aggregation;
   - or something insufficiently documented.
5. Verify cleaning filters:
   - true 1v1;
   - resolved match;
   - human players only;
   - valid ratings;
   - side/team/focal-opponent handling;
   - schema-evolution exclusions.
6. Identify residual risk:
   - quickplay contamination;
   - custom lobby contamination;
   - team-game contamination;
   - missing/ambiguous queue metadata;
   - upstream aggregator limitations.

#### 4.2 aoe2companion

Tasks:

1. Inspect source schema, notebooks, artifacts, logs, and ROADMAP.
2. Identify and document:
   - `internalLeaderboardId`;
   - retained values;
   - values `6` and `18`, if present;
   - mapping to `rm_1v1`, `qp_rm_1v1`, or equivalent labels.
3. Verify whether ID `18` is ranked ladder, quickplay, or a distinct non-ranked/ladder-like population.
4. Determine whether combining IDs `6` and `18` is methodologically defensible.
5. Decide whether the thesis should:
   - split them;
   - exclude quickplay;
   - keep both but label as 1v1 Random Map matchmaking/ladder-like records;
   - or treat one source as robustness/control only.
6. Identify whether current thesis wording overclaims.

#### 4.3 Required audit format

Write:

- `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md`

It must contain:

- source-by-source summary;
- exact source fields;
- filters;
- retained population;
- excluded population;
- evidence strength;
- remaining uncertainty;
- recommended terminology;
- exact thesis sections requiring edits;
- whether notebook regeneration is needed.

Recommended terminology ladder:

- strong evidence: “publicly indexed 1v1 ranked Random Map ladder matches”;
- medium evidence: “publicly indexed 1v1 Random Map ladder/matchmaking records”;
- mixed source: “AoE2 public 1v1 Random Map records from third-party aggregators, including ranked-ladder and possibly quickplay/matchmaking-derived records depending on source”;
- insufficient evidence: “third-party AoE2 multiplayer match records filtered to 1v1 Random Map-like matches.”

Acceptance:

- every occurrence of “ranked ladder” in Chapters 1–4 is classified as OK / revise / unsupported / source-specific;
- aoestats and aoe2companion are treated separately;
- if uncertainty remains, thesis wording is weakened and flagged;
- adversarial review finds no BLOCKER in the provenance logic.

---

### Stage 5 — ROADMAP and notebook regeneration decision

**Agents:** `@planner-science`, then `@executor`.

Objective:

Decide which Steps require regeneration and repair upstream definitions first.

Tasks:

1. Using outputs from Stages 2–4, identify every Step whose:
   - question changed;
   - filters changed;
   - cleaning logic changed;
   - output artifacts changed;
   - thesis mapping changed;
   - invariant/gate changed.
2. For each affected Step:
   - update ROADMAP before notebook edits;
   - record old vs new Step definition;
   - update expected inputs/outputs;
   - update gate criteria;
   - update thesis_mapping;
   - update scientific_invariants_applied.
3. If a notebook must be edited:
   - mark current artifacts from that Step as stale;
   - do not silently reuse them.
4. If no notebook regeneration is needed:
   - explicitly document why in `notebook_regeneration_manifest.md`.

Writes:

- updated relevant ROADMAP files;
- updated `thesis/pass2_evidence/notebook_regeneration_manifest.md`.

Acceptance:

- no notebook changes without ROADMAP changes when Step semantics changed;
- every stale artifact is identified;
- every regeneration target is declared.

---

### Stage 6 — Notebook fixes and artifact regeneration

**Agent:** `@executor` with `/model opus`; `@reviewer` after each dataset block.

Objective:

Regenerate only what must be regenerated, but regenerate completely and reproducibly.

Tasks:

1. For each affected Step:
   - edit paired notebooks consistently;
   - execute end-to-end using project conventions;
   - regenerate all declared artifacts;
   - update schemas if needed;
   - update assertions/gates.
2. For AoE2, prioritize filters and artifacts relevant to:
   - 1v1 scope;
   - ranked/quickplay/leaderboard semantics;
   - human vs AI;
   - winner complementarity;
   - rating missingness;
   - side/team asymmetry;
   - focal/opponent construction;
   - schema evolution.
3. For SC2, prioritize artifacts relevant to:
   - SC2EGSet version/source identity;
   - true 1v1 decisive scope;
   - MMR sentinel semantics;
   - tournament/professional population;
   - replay/in-game feature availability.
4. Add tests/assertions where possible:
   - no team games in 1v1 analytical view;
   - no unresolved winners;
   - complementarity of win/loss;
   - no AI games if human-only claim is made;
   - no post-game data in pre-game feature views;
   - no same-match leakage in history features.
5. Do not modify raw data.

Writes:

- updated notebooks;
- regenerated artifacts;
- updated schemas/assertion outputs, if relevant.

Acceptance:

- all regenerated artifacts match ROADMAP outputs;
- no stale artifact is used downstream;
- notebook execution is documented;
- mechanical review passes for each dataset block.

---

### Stage 7 — research_log and STEP_STATUS repair

**Agent:** `@executor`.

Objective:

Repair evidence logs after artifact regeneration or interpretation changes.

Tasks:

1. For each regenerated or reinterpreted Step, update per-dataset `research_log.md`.
2. Each log entry must include:
   - Step ID;
   - question;
   - method;
   - inputs;
   - outputs/artifacts;
   - exact generated artifact paths;
   - key findings;
   - validation/assertions;
   - limitations;
   - thesis mapping;
   - decision;
   - whether prior artifacts became stale.
3. Update `STEP_STATUS.yaml` only after the corresponding log is complete.
4. If a finding affects cross-dataset comparison, update root `reports/research_log.md`.

Acceptance:

- every regenerated artifact appears in a research_log entry;
- every thesis-relevant interpretation has a log entry;
- STEP_STATUS agrees with logs and artifacts.

---

### Stage 8 — Cross-dataset comparability matrix

**Agents:** `@planner-science`, then `@executor` with `/model opus`.

Objective:

Define the exact valid comparison scope for the thesis.

Tasks:

1. Build a matrix comparing SC2EGSet, aoestats, and aoe2companion across:
   - source type;
   - population;
   - sampling mechanism;
   - time window;
   - unit of observation;
   - true 1v1 status;
   - ranked/ladder/matchmaking status;
   - professional vs public player population;
   - pre-game features;
   - in-game features;
   - replay availability;
   - rating availability;
   - patch/version drift;
   - map/civ/race encoding;
   - cold-start behavior;
   - legal/licensing/source limitations;
   - inference limitations.
2. For each comparison claim in Chapters 1–4, label:
   - supported;
   - supported with caveat;
   - unsupported;
   - thesis wording must change.
3. Define the thesis’s final comparison frame.

Expected final framing:

> The thesis compares prediction methods across two RTS titles under asymmetric data regimes: SC2 as a professional/tournament replay corpus with rich in-game telemetry, and AoE2 as third-party public 1v1 Random Map ladder/matchmaking-derived records with primarily pre-game/history/rating/map/civilization features. Observed differences are interpreted as method/data/population differences, not pure game-mechanic differences.

Writes:

- `thesis/pass2_evidence/cross_dataset_comparability_matrix.md`
- root `reports/research_log.md` entry if this is a cross-dataset decision.

Acceptance:

- matrix is explicit enough to support Chapter 1 and Chapter 4 rewrites;
- no later thesis prose violates the matrix.

---

### Stage 9 — Methodology risk register

**Agents:** `@reviewer-adversarial`, then `@executor`.

Objective:

Record remaining examiner-facing risks rather than burying them.

Create:

- `thesis/pass2_evidence/methodology_risk_register.md`

Risks to assess:

1. AoE2 ranked ladder terminology risk.
2. aoe2companion quickplay/ranked mixing risk.
3. aoestats source aggregation opacity.
4. SC2 tournament population vs AoE2 public ladder population.
5. Temporal leakage in history features.
6. Match/series grouping leakage.
7. Rating missingness and sentinel semantics.
8. Patch/version drift.
9. Civilization roster changes across AoE2 time window.
10. Feature importance interpreted causally.
11. ECE/binning instability.
12. Overuse of ICC / variance partitioning.
13. Overstrong literature-gap claim.
14. Grey literature overreliance.
15. Reproducibility of third-party API data.
16. SC2 cross-region fragmentation mitigation collapsing sample size.
17. SC2 `tracker_events_raw` field-semantics uncertainty if in-game features are retained.

For each risk:

- severity;
- likelihood;
- affected thesis sections;
- mitigation;
- remaining uncertainty;
- final wording recommendation.

Acceptance:

- every serious risk has mitigation or explicit limitation wording.

---

### Stage 10 — Chapter 4 methodology cleanup

**Agents:** `@writer-thesis` for prose only after evidence exists; `@executor` for file edits; `/model opus`.

Objective:

Make Chapter 4 scientifically defensible and aligned with artifacts.

Tasks:

1. Fix SC2EGSet source/version/citation issue:
   - verify correct Zenodo record and dataset/tooling distinction;
   - distinguish SC2EGSet preprocessed dataset from SC2ReSet raw replay pack/tooling if applicable;
   - update citation and license wording only if verified.
2. Fix AoE2 source descriptions:
   - separate aoestats from aoe2companion;
   - use source-specific terminology;
   - explain third-party aggregation limitations;
   - avoid overclaiming official ranked ladder unless supported.
3. Repair §4.1 and §4.2:
   - ensure every number traces to current artifacts;
   - ensure cleaning rules align with regenerated artifacts;
   - ensure tables cite current artifact source;
   - remove workflow-internal language from thesis prose.
4. Repair §4.3 and §4.4 if currently placeholders:
   - do not fabricate completed experiments;
   - if Phase 02/03/04 is not complete, write defensible planned-methodology language or mark as pending;
   - include explicit temporal leakage controls;
   - include feature families only if implemented or planned with clear gates.
5. Evaluation methodology:
   - Brier/log-loss as primary probabilistic metrics, if consistent with final design;
   - ECE only as auxiliary, with binning caveat;
   - reliability diagrams/calibration slope/intercept where supported;
   - AUROC/accuracy as secondary.
6. Statistical comparisons:
   - avoid overcommitting to Friedman/Nemenyi mean-rank machinery;
   - prefer paired loss differences, repeated temporal windows, and block bootstrap if supported;
   - if not implemented, describe as planned or flag.
7. ICC:
   - reduce centrality;
   - move to diagnostic/appendix framing if still needed;
   - remove any universal claim that observed-scale ICC is simply a lower bound of latent-scale ICC unless exactly supported.

Writes:

- `thesis/chapters/04_data_and_methodology.md`
- updates to `claim_evidence_matrix.md`
- updates to `cleanup_flag_ledger.md`

Acceptance:

- no number in Chapter 4 lacks artifact lineage;
- no source population is mislabeled;
- no placeholder is disguised as completed method;
- REVIEW_QUEUE is updated for Chapter 4.

---

### Stage 11 — Chapter 1 introduction/RQ/scope cleanup

**Agent:** `@writer-thesis` with `/model opus`.

Objective:

Make the thesis opening match the real study.

Tasks:

1. Rewrite motivation to emphasize scientific/methodological value, not market-size hype.
2. Weaken unsupported commercial/esports market claims unless dated and sourced.
3. Correct or flag:
   - Hodge2021 details;
   - GarciaMendez2025 target game/authors/accuracy;
   - betting-market transfer from traditional sport to esports;
   - AoE2 “millions of active players” if unsupported;
   - AoE2 “50 civilizations” if temporal scope is wrong or not tied to observed data window.
4. Rewrite research gap conservatively:

   ```text
   In the reviewed literature, I did not identify a peer-reviewed study that compares families of probabilistic prediction methods across StarCraft II and Age of Empires II under a unified protocol.
   ```

5. Rewrite RQs:
   - align RQ1–RQ4 with actual datasets and methods;
   - distinguish method comparison from pure game comparison;
   - distinguish pre-game vs in-game prediction;
   - keep cold-start if empirically supported, otherwise flag.
6. Rewrite scope/limitations:
   - SC2 professional/tournament replay population;
   - AoE2 public 1v1 Random Map ladder/matchmaking population, as supported by Stage 4;
   - not a causal study of game mechanics;
   - not a fully symmetric comparison of data availability;
   - not necessarily real-time AoE2 prediction if only pre-game data are available.

Writes:

- `thesis/chapters/01_introduction.md`
- updates to REVIEW_QUEUE / WRITING_STATUS.

Acceptance:

- title, RQs, data, and methods are coherent;
- no overstrong novelty claims;
- AoE2 population wording matches Stage 4.

---

### Stage 12 — Chapter 2 theoretical background cleanup

**Agents:** `@writer-thesis`, `@lookup` where needed.

Objective:

Remove overclaims and align theory with actual experiments.

Tasks:

1. RTS difficulty:
   - keep relevant theory;
   - avoid excessive RL/AlphaStar detail not used by thesis;
   - distinguish control/agent-playing difficulty from prediction difficulty.
2. SC2:
   - correct MMR/per-race/ladder claims with official or source-backed evidence;
   - avoid implying SC2EGSet is ladder data.
3. AoE2:
   - correct civilization-count claims relative to data window;
   - avoid claiming exact official ranked-system internals unless sourced;
   - distinguish visible Elo/rating from unknown official matchmaking internals.
4. Rating systems:
   - Elo/Glicko/TrueSkill/Aligulac as conceptual baselines;
   - no overclaiming about TrueSkill 2 RTS validation;
   - grey literature clearly labeled.
5. Classifier comparison theory:
   - fix Demšar/Benavoli framing;
   - avoid making Nemenyi/mean-rank procedures central if not appropriate.
6. Calibration:
   - emphasize proper scoring rules;
   - ECE limitations;
   - reliability diagrams as diagnostic, not sole proof.
7. ICC:
   - reduce centrality;
   - make it optional/diagnostic unless core to results.

Writes:

- `thesis/chapters/02_theoretical_background.md`
- `thesis/references.bib` if needed.

Acceptance:

- Chapter 2 supports methodology without promising experiments not planned or implemented;
- rating and ladder terminology matches Stage 4 and Stage 8.

---

### Stage 13 — Chapter 3 related work cleanup

**Agents:** `@writer-thesis`, `@lookup`, `@reviewer`.

Objective:

Make related work accurate, conservative, and citation-clean.

Tasks:

1. Verify and fix:
   - Tarassoli phantom/misattribution issues;
   - Khan2024 / SC-Phi2 metadata and exact accuracy claims;
   - EsportsBench version/cutoff consistency;
   - Bialecki2022 vs Bialecki2023 relationship;
   - SC2EGSet dataset/tooling distinction;
   - GarciaMendez2025 target game and article status;
   - Hodge2021 result details.
2. AoE2 literature:
   - verify Çetin Taş and Müngen;
   - verify Elbert if used;
   - verify Lin/NCT/intransitivity if used;
   - distinguish peer-reviewed AoE2 prediction work from community analyses.
3. Research gap:
   - state conservatively;
   - do not claim exhaustive absence unless systematic search protocol is documented.
4. Reduce overly broad adjacent-domain review if it distracts from RTS/AoE2/SC2.
5. Keep literature tied to:
   - probabilistic win prediction;
   - RTS/SC2/AoE2;
   - rating baselines;
   - calibration;
   - cross-domain sports/esports prediction.

Writes:

- `thesis/chapters/03_related_work.md`
- `thesis/references.bib`
- `thesis/pass2_evidence/literature_verification_log.md`

Acceptance:

- no known phantom citations;
- grey literature is not mislabeled;
- literature gap is defensible.

---

### Stage 14 — Specs, leakage gates, and ML protocol repair

**Agents:** `@planner-science`, then `@executor`, then `@reviewer-deep`.

Objective:

Ensure future modeling cannot proceed under unsafe assumptions.

Tasks:

1. Inspect existing specs under `reports/specs/**`.
2. Update or create specs for:
   - feature-generation temporal discipline;
   - train/validation/test splitting;
   - per-player/per-time/cross-dataset constraints;
   - no target leakage;
   - no random split;
   - source-specific AoE2 population labels;
   - reproducibility seed = 42;
   - stale artifact detection.
3. If feature/model code exists:
   - add or update tests/assertions.
4. If feature/model code does not yet exist:
   - add gate conditions and explicit future requirements.
5. Update thesis methodology only to the level actually supported.

Acceptance:

- no spec contradicts `.claude/ml-protocol.md`;
- no thesis methodology describes unimplemented protections as completed fact;
- reviewer-deep finds no BLOCKER on leakage discipline.

---

### Stage 14A — Phase 02 readiness hardening imported from the Claude plan

**Agents:** `@executor`, `@reviewer-adversarial` for methodology-affecting spec changes.

Objective:

Incorporate useful Phase-02-readiness findings from the previous Claude-generated plan, but only under strict lineage discipline. This stage must not manually patch generated artifacts.

#### 14A.1 Data dictionary temporal-classification audit

Tasks:

1. Inspect aoe2companion data dictionary rows related to:
   - `rating`;
   - `started`;
   - `leaderboard`;
   - `internalLeaderboardId`;
   - other pre-game/context fields.
2. Identify rows by stable field/table names, not CSV line numbers.
3. If the data dictionary is generated:
   - update the upstream ROADMAP Step and notebook/generator;
   - regenerate the CSV.
4. If it is hand-maintained:
   - document that status in `dependency_lineage_audit.md` before editing.
5. Fix all same-class temporal-classification contradictions in the same PR unless a separate methodological decision is required.
6. Do not leave known same-class contradictions merely for scope discipline.

#### 14A.2 CROSS-02-01 leakage audit protocol hardening

Tasks:

1. Bind the v1 enforcement mechanism for Phase 02.
2. Prefer pattern-conformance review as the v1 mechanism if AST/lineage tooling does not yet exist.
3. Defer AST/pre-commit/CI tooling to v2 only if explicitly documented.
4. Because this changes methodology, require `@reviewer-adversarial` review.

#### 14A.3 CROSS-02-00 feature input contract and cold-start hardening

Tasks:

1. Add or update cold-start and rating-sparsity handling only after AoE2 source semantics are verified.
2. The protocol must be source-specific:
   - sc2egset;
   - aoestats;
   - aoe2companion.
3. Forbid:
   - future-game rating imputation;
   - global fit imputation leakage;
   - hard-coded 0/1500 priors without derivation;
   - use of target/result/duration fields in pre-game features.
4. Preserve null/missing flags where predictive and temporally valid.
5. Do not bind pseudocount `m` before empirical derivation.

#### 14A.4 DuckDB UTC requirement

Tasks:

1. Add a requirement that all rolling-window joins and TIMESTAMP/TIMESTAMPTZ comparisons run with DuckDB session timezone bound to UTC.
2. Add tests/assertions or notebook checks where practical.
3. Document naked TIMESTAMP assumptions per dataset.

#### 14A.5 SC2 cross-region fragmentation risk

Tasks:

1. Assess whether `is_cross_region_fragmented` safe-subset filtering collapses the SC2 sample.
2. Prefer sensitivity indicator or dual feature paths if strict filtering destroys sample size.
3. If strict filtering is used, report retention and fold-level sample sizes.
4. Add this risk to `methodology_risk_register.md`.

#### 14A.6 Optional SC2 `tracker_events_raw` semantic validation

Execute this only if thesis methods/RQs retain SC2 in-game telemetry features.

Tasks:

1. Add retroactive Step `01_03_05` under sc2egset ROADMAP before creating/editing notebooks.
2. Use hypothesis/falsifier/gate format for each validation.
3. Validate:
   - gameSpeed / loop-to-time conversion;
   - player ID mapping by event type;
   - JSON key completeness;
   - PlayerStats periodicity anomaly;
   - field semantics before any aggregate reconciliation;
   - coordinate bounds only after coordinate units are understood;
   - patch/schema stability if feasible.
4. Emit `.md` and `.json` artifacts.
5. Update:
   - sc2egset `research_log.md`;
   - sc2egset `STEP_STATUS.yaml`;
   - CROSS-02-00 derivation-pattern table;
   - thesis Chapter 4 only after artifacts are regenerated and logged.
6. If validation is not executed, thesis must not claim validated use of tracker-events-derived features.

Important cautions:

- Do not assume final-tick `PlayerStats` minerals/vespene are cumulative totals. Inspect parser/source semantics first.
- Coordinate bounds validation is descriptive until coordinate units and map bounds semantics are verified.
- Do not use SC2 tracker validation as a substitute for AoE2 provenance.

Writes:

- `thesis/pass2_evidence/phase02_readiness_hardening.md`
- updated specs/artifacts/logs only if lineage requires it.

Acceptance:

- no generated artifact is manually edited;
- all spec changes pass adversarial review;
- AoE2 ranked/ladder terminology remains governed by Stage 4, not generic cold-start specs;
- SC2 tracker-events validation is either completed and logged or thesis claims are weakened.

---

### Stage 15 — Review queue and writing status synchronization

**Agents:** `@executor`, `@reviewer`.

Objective:

Make repo state internally consistent.

Tasks:

1. Update `thesis/chapters/REVIEW_QUEUE.md`:
   - resolved flags;
   - preserved flags;
   - new flags;
   - Pass 2 status;
   - evidence artifact references.
2. Update `thesis/WRITING_STATUS.md`.
3. Ensure no resolved issue remains pending.
4. Ensure no unresolved issue is silently dropped.
5. Update `cleanup_flag_ledger.md` to match final chapter state.

Acceptance:

- REVIEW_QUEUE agrees with chapter files;
- WRITING_STATUS agrees with actual readiness;
- flag ledger agrees with both.

---

### Stage 16 — Final thesis consistency pass

**Agents:** `@writer-thesis`, then `@reviewer`.

Objective:

Make Chapters 1–4 read as one coherent thesis draft.

Tasks:

1. Search and fix inconsistent terminology:
   - ranked ladder;
   - ladder;
   - quickplay;
   - matchmaking;
   - public online matches;
   - tournament;
   - professional;
   - replay corpus;
   - telemetry;
   - pre-game;
   - in-game;
   - historical features.
2. Remove internal workflow language from thesis prose:
   - `Phase 01`;
   - `PR #TBD`;
   - `BACKLOG.md`;
   - `grep`;
   - internal invariant names unless deliberately explained;
   - raw implementation debugging language.
3. Keep academic register.
4. Preserve necessary uncertainty flags.
5. Ensure title/RQ/method/data alignment.

Acceptance:

- supervisor can read Chapters 1–4 without seeing repo workflow leakage;
- remaining flags are deliberate, not accidental.

---

### Stage 17 — Full review gates

**Agents:** `@reviewer`, `@reviewer-deep`, `@reviewer-adversarial`.

Required mechanical checks:

```bash
git diff --stat
rg "\[REVIEW:|\[UNVERIFIED:|\[NEEDS CITATION|\[NEEDS JUSTIFICATION|\[TODO" thesis/chapters
rg "ranked ladder|ladder|quickplay|random_map|internalLeaderboardId|leaderboard" thesis/chapters thesis/pass2_evidence
rg "Phase 01|PR #TBD|BACKLOG.md|grep|post-F1|master" thesis/chapters
rg "17829625|14963484|SC2EGSet|SC2ReSet" thesis/chapters thesis/references.bib
rg "50 cywilizacji|50 civilizations|45 cywilizacji|45 civilizations" thesis/chapters
rg "Demsar|Demšar|Nemenyi|Benavoli|Friedman" thesis/chapters
rg "ECE|Brier|log-loss|calibration|kalibr" thesis/chapters
```

Project checks:

- run available tests if discoverable;
- run notebook validation if the project has a standard command;
- do not invent commands if no standard command exists;
- document commands actually run.

`@reviewer-deep` must verify:

- lineage completeness;
- no stale artifacts used;
- ROADMAP/notebook/artifact/log/thesis consistency;
- no raw data mutation;
- no contradictory claims across chapters;
- no unsupported quantitative claims.

`@reviewer-adversarial` must attack:

- AoE2 ranked ladder wording;
- cross-game comparability;
- methodology overclaims;
- literature gap;
- leakage;
- evidence traceability;
- whether an examiner could challenge the thesis.

Writes:

- `thesis/pass2_evidence/reviewer_gate_report.md`

Acceptance:

- no BLOCKER remains;
- WARNINGs are documented in risk register and cleanup summary;
- remaining unresolved issues are intentionally flagged.

---

### Stage 18 — Final PR summary

**Agent:** `@executor`.

Write:

- `thesis/pass2_evidence/audit_cleanup_summary.md`

Must include:

1. PR scope.
2. Files changed.
3. Notebooks changed.
4. Artifacts regenerated.
5. ROADMAP Steps changed.
6. research_log entries added/updated.
7. Thesis sections changed.
8. Claims weakened.
9. Claims corrected.
10. Claims still unresolved.
11. Remaining supervisor-facing risks.
12. Commands run.
13. Review agents run.
14. Known limitations.

Prepare PR body:

```markdown
## Summary

This PR hardens the thesis methodology and evidence lineage after external scientific audit. It focuses on AoE2 data provenance, cross-dataset comparability, thesis claim discipline, and ROADMAP→notebook→artifact→research_log→thesis consistency.

## Major changes

- Added dependency lineage audit.
- Added AoE2 ladder/matchmaking provenance audit.
- Updated affected ROADMAP Steps and regenerated artifacts where required.
- Repaired research_log / STEP_STATUS lineage.
- Rewrote thesis Chapters 1–4 to avoid unsupported claims.
- Added Phase 02 readiness hardening where relevant.
- Updated REVIEW_QUEUE and WRITING_STATUS.
- Added methodology risk register and final reviewer gate report.

## Key decisions

- SC2 and AoE2 are framed as different RTS data regimes, not a clean causal game-vs-game comparison.
- AoE2 source terminology is source-specific and evidence-bounded.
- “Ranked ladder” wording is used only where supported by source fields and filters.
- Remaining uncertainty is explicitly flagged.

## Validation

- [list commands run]
- reviewer
- reviewer-deep
- reviewer-adversarial

## Remaining risks

- [summarize from methodology_risk_register.md]
```

Acceptance:

- PR can be reviewed by a human without reconstructing context from chat.

---

## 7. Specific audit findings to address

### 7.1 AoE2 ranked ladder uncertainty

Problem:

The thesis risks implying that AoE2 data are “ranked ladder” merely because they are online multiplayer.

Required:

- verify aoestats and aoe2companion separately;
- do not conflate `random_map`, `rm_1v1`, and `qp_rm_1v1`;
- if quickplay appears, do not call it ranked;
- if source docs are ambiguous, weaken wording.

### 7.2 SC2 vs AoE2 comparability

Problem:

The thesis title suggests a comparative analysis between RTS games, but the data regimes differ.

Required:

- explicitly frame SC2 as tournament/professional replay telemetry;
- explicitly frame AoE2 as public 1v1 Random Map ladder/matchmaking third-party records, source permitting;
- avoid pure game-mechanic causal interpretation.

### 7.3 SC2EGSet source/citation issue

Required:

- verify exact dataset record;
- distinguish dataset vs tooling vs raw replay pack;
- correct Chapters 3/4 and references.

### 7.4 Overstrong literature gap

Required:

- use bounded search language;
- state what was reviewed;
- distinguish peer-reviewed literature from grey/community sources.

### 7.5 GarciaMendez2025 and Hodge2021

Required:

- verify GarciaMendez2025 authors, target game, venue/status, accuracy claim;
- frame it as CS:GO/streaming esports if that is correct, not direct RTS evidence;
- verify Hodge2021 details and do not overgeneralize from Dota 2.

### 7.6 AoE2 civilization count

Required:

- tie civilization count to observed data window or current game state;
- do not imply a constant number across all years if roster changed.

### 7.7 Calibration/evaluation

Required:

- proper scoring rules central;
- Brier/log-loss primary if consistent with method;
- ECE auxiliary and binning-dependent;
- reliability diagrams diagnostic;
- accuracy secondary.

### 7.8 Statistical comparison

Required:

- do not overuse Friedman/Nemenyi if assumptions/context are weak;
- prefer paired loss differences and block bootstrap if implemented or planned;
- if not implemented, do not present as completed.

### 7.9 ICC

Required:

- reduce centrality;
- frame as optional diagnostic if kept;
- avoid strong latent-vs-observed-scale claims without exact support.

### 7.10 Repo workflow leakage in thesis prose

Required:

Remove or rewrite internal workflow terms from thesis:

- `Phase 01`
- `PR #TBD`
- `BACKLOG.md`
- `grep`
- `master`
- `post-F1`
- internal issue labels

unless placed in a clearly marked reproducibility appendix.

### 7.11 Useful imported items from Claude’s plan

Add safely:

- DuckDB UTC requirement for timestamp joins;
- source-specific cold-start/rating sparsity protocol;
- leakage-audit pattern-conformance v1;
- SC2 cross-region fragmentation risk;
- optional SC2 `tracker_events_raw` semantic validation;
- hypothesis/falsifier/gate format for validation.

Reject:

- two-PR branching;
- manual artifact edits;
- Cat C classification for methodology-affecting changes;
- line-number edits;
- leaving same-class contradictions unresolved;
- assuming `PlayerStats` resource fields are cumulative without semantic verification.

---

## 8. Regeneration policy

### A. Thesis-only wording change

Allowed when:

- no number changes;
- no method changes;
- no filter/scope changes;
- no interpretation changes.

Required:

- update REVIEW_QUEUE/WRITING_STATUS if status changes.

### B. Artifact interpretation change

Allowed when:

- notebook output is unchanged;
- previous thesis interpretation was too strong/wrong.

Required:

- update thesis prose;
- update evidence note;
- update research_log if prior log wording becomes misleading.

### C. Notebook logic change

This invalidates downstream artifacts for that Step.

Required:

1. update ROADMAP Step;
2. edit notebook pair;
3. regenerate artifacts;
4. update research_log;
5. update STEP_STATUS;
6. update thesis;
7. update REVIEW_QUEUE/WRITING_STATUS.

### D. Step design change

Required:

- update ROADMAP before notebook;
- do not let notebook answer a different question than ROADMAP.

### E. Cross-dataset decision

Required:

- update root `reports/research_log.md`;
- update comparability matrix;
- update thesis limitations.

---

## 9. Acceptance criteria for the whole PR

The PR is complete only when all criteria are met.

### Evidence

- `dependency_lineage_audit.md` exists and maps thesis claims to upstream evidence.
- `cleanup_flag_ledger.md` exists and matches final chapter flags.
- `aoe2_ladder_provenance_audit.md` exists and supports final terminology.
- `cross_dataset_comparability_matrix.md` exists and matches thesis framing.
- `claim_evidence_matrix.md` exists and is consistent with final Chapters 1–4.
- `notebook_regeneration_manifest.md` documents whether notebooks/artifacts were regenerated.
- `literature_verification_log.md` exists.
- `methodology_risk_register.md` exists.
- `phase02_readiness_hardening.md` exists if any imported Claude-plan items are used.
- `reviewer_gate_report.md` exists.
- `audit_cleanup_summary.md` exists.

### Thesis

Chapters 1–4 no longer overclaim about:

- ranked ladder;
- cross-game comparison;
- literature gap;
- calibration;
- feature importance;
- statistical testing;
- ICC.

All remaining flags are intentional and recorded. REVIEW_QUEUE and WRITING_STATUS are synchronized.

### Data/provenance

- aoestats and aoe2companion are described separately.
- SC2EGSet is described as tournament/professional replay corpus, not ladder data.
- AoE2 source terminology is source-specific and evidence-bounded.
- No stale artifacts are cited.

### Workflow

- ROADMAP changes precede notebook changes.
- Notebook changes regenerate artifacts.
- Artifacts are logged.
- Logs map to thesis.
- STEP_STATUS agrees with logs.
- Raw data untouched.

### Review

- `@reviewer` completed.
- `@reviewer-deep` completed.
- `@reviewer-adversarial` completed.
- No unresolved BLOCKER.
- WARNINGs documented.

---

## 10. Final reminder to the agent

This PR is not successful if it merely makes the thesis prose smoother.

It is successful only if the evidence chain is repaired:

```text
ROADMAP.md
  -> sandbox notebooks
  -> generated artifacts
  -> research_log.md
  -> STEP_STATUS.yaml / gates
  -> thesis prose and tables
  -> REVIEW_QUEUE / WRITING_STATUS
```

The critical order must not be inverted:

```text
lineage audit
  -> AoE2 ladder provenance
  -> ROADMAP/notebook/artifact/log repair
  -> cross-dataset comparability
  -> methodology/spec hardening
  -> thesis rewrite
  -> review gates
```

If the agent starts by rewriting thesis prose, it is doing the work in the wrong order.
