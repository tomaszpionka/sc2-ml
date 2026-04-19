---
category: A
branch: feat/phase01-decision-gates-01-06
date: 2026-04-19
planner_model: claude-opus-4-7
dataset: null
phase: "01"
pipeline_section: "01_06 — Decision Gates"
invariants_touched: [I1, I2, I3, I5, I6, I7, I8, I9]
source_artifacts:
  - docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md
  - docs/PHASES.md
  - docs/TAXONOMY.md
  - docs/templates/plan_template.md
  - reports/specs/01_05_preregistration.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/INVARIANTS.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/decision_gate_sc2egset.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_09_gate_memo.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md
  - reports/research_log.md
  - planning/BACKLOG.md
  - thesis/WRITING_STATUS.md
  - .claude/scientific-invariants.md
critique_required: true
research_log_ref: null
---

# Plan: Phase 01 Decision Gates (01_06) — close Phase 01 across three datasets

## Scope

Close **Phase 01 (Data Exploration)** for all three datasets by executing
**Pipeline Section 01_06 — Decision Gates** per
`docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md` §6 for
sc2egset, aoestats, and aoe2companion in a single bundled PR. Produces
the four Manual §6.1 deliverables (data dictionary, data quality report,
risk register, modeling-readiness decision) per dataset plus one
cross-dataset rollup memo that resolves the PRIMARY / SUPPLEMENTARY
VALIDATION role assignment along **five enumerated dimensions**
(sample-scale / skill-signal / temporal-coverage / identity-rigor /
patch-resolution, plus in-game-events for sc2egset). Advances each
dataset's `STEP_STATUS → PIPELINE_SECTION_STATUS → PHASE_STATUS`
derivation chain (`01_06` → complete, Phase 01 → complete). Resolves
the existing `[01_06 deferred]` flags in thesis §4.1 / §4.1.3 / §4.1.4
Notes cells by updating their status to note 01_06 closure (no new
§4.3 row is created; §4.3 is not a section in the current
WRITING_STATUS.md layout).

Retroactively adds the missing `01_05_09` gate-memo Step to **both
sc2egset and aoe2companion** ROADMAPs so all three datasets carry
symmetric 01_05 exit artifacts (aoestats already has it). For sc2egset,
01_05_09 wraps the existing `decision_gate_sc2egset.md` artifact on disk
and is added as a retroactively-`complete` step. For aoe2companion,
01_05_09 requires authoring a new memo and is executed as a new step.

Authors a narrow spec `reports/specs/01_06_readiness_criteria.md`
locking the four-deliverable schema, the verdict taxonomy, and the
role-assignment criteria.

Purges six orphan pre-execution artifacts under `.github/tmp/01_05/`
inline.

## Problem Statement

Phase 01 is `in_progress` across all three datasets. Pipeline Sections
01_01–01_05 are `complete`; 01_06 is `not_started` in all three
`PIPELINE_SECTION_STATUS.yaml` files. The three ROADMAPs list `01_06 —
Decision Gates` as a pipeline section but contain no step decomposition
— the ROADMAP tails say "Steps to be defined when Phase 01 gate is
met." This is inverted: 01_06 **is** the Phase 01 gate mechanism, so
the dataset cannot reach the "gate met" state without 01_06 existing as
concrete steps.

Two datasets have partial precursor artifacts that must be distinguished
from the 01_06 deliverables; one is missing even the partial artifact's
owning Step:

- **sc2egset** has `decision_gate_sc2egset.md` on disk at
  `artifacts/01_exploration/05_temporal_panel_eda/` but **no
  `01_05_09` Step in its ROADMAP owns it** (sc2egset's 01_05 Step
  decomposition stops at 01_05_08). This is a retroactive-symmetry
  gap equivalent to aoe2companion's missing memo; this plan fixes
  both.
- **aoestats** has both `01_05_09` Step in ROADMAP and
  `01_05_09_gate_memo.md` artifact on disk — the only fully-symmetric
  dataset.
- **aoe2companion** has neither Step nor artifact. This plan
  retroactively adds both.

None of the three covers the Manual §6.1 four-deliverable set, which
spans Phase 01 in its entirety (01_01 schema → 01_02 EDA → 01_03
profiling → 01_04 cleaning → 01_05 temporal/panel). So 01_06 is
substantively new consolidation work.

aoestats and aoe2companion ROADMAPs declare *"Role: TO BE DETERMINED.
Role assignment (PRIMARY vs SUPPLEMENTARY VALIDATION) will be formalized
at the Phase 01 Decision Gate (01_06) based on comparative data quality
findings."* sc2egset's ROADMAP was authored without this flag; this plan
adds the equivalent block to sc2egset as part of T02 (so all three
ROADMAPs carry the flag for the rollup to resolve).

Role assignment is **six-dimensional with D4 split into D4a/D4b**
(plus a seventh item that is NOT a role dimension — D6, the
controlled-asymmetry flag). A dataset can be PRIMARY on one dimension
and SUPPLEMENTARY on another. The cross-dataset rollup (T08) populates
the following matrix from T05/T06/T07 empirical artifacts:

| Dimension | sc2egset | aoestats | aoe2companion |
|---|---|---|---|
| D1 Sample-scale (ML training volume) | SUPPLEMENTARY | SUPPLEMENTARY | **PRIMARY** |
| D2 Skill-signal (observed-scale ICC, F1+F2 passed) | **PRIMARY** | SUPPLEMENTARY | SUPPLEMENTARY |
| D3 Temporal coverage (months continuous, density floor) | SUPPLEMENTARY | SUPPLEMENTARY | **PRIMARY** |
| D4a Identity rename-stability (Branch (i)) | SUPPLEMENTARY (Branch iii) | SUPPLEMENTARY (Branch v) | **PRIMARY** (Branch i) |
| D4b Identity within-scope rigor (rates < 15%) | **co-PRIMARY** (12%/30.6% — within-region) | SUPPLEMENTARY (Branch v, unmeasurable) | **co-PRIMARY** (2.57%/3.55%) |
| D5 Patch resolution (patch metadata) | SUPPLEMENTARY | **PRIMARY** | SUPPLEMENTARY |
| D6 (asymmetry flag, NOT a role dimension) | flag present | N/A | N/A |

**Note on D6:** per Pass 2 reviewer-adversarial, D6 is included in the
matrix for I8 asymmetry transparency only; it is NOT counted toward
sc2egset's PRIMARY-role weight in downstream discussion. Role-tally
for Phase 02 kickoff uses only D1–D5 + D4a/D4b.

This resolves the Pass 2 reviewer-adversarial concerns:
- **ICC-0.003 question:** aoe2companion is PRIMARY on D1/D3 and
  co-PRIMARY on D4 but **SUPPLEMENTARY on D2 skill-signal** (its ICC
  0.003 fails filter F1 at the 0.01 threshold AND fails filter F2 as
  FALSIFIED). sc2egset takes PRIMARY on D2 (ICC 0.046, INCONCLUSIVE
  passes F2).
- **D4 conflation:** split into D4a (rename-stability, where
  aoe2companion's Branch (i) wins outright) and D4b (within-scope
  rigor, where sc2egset's Branch (iii) with documented within-region
  rates and aoe2companion's Branch (i) both qualify with rates < 15%,
  but sc2egset is the only within-region candidate; aoe2companion is
  rename-stable PRIMARY; co-PRIMARY is thus preserved but now on
  orthogonal sub-dimensions).
- **D6 inflation:** D6 labelled flag-only, not role-bearing.

Why now: thesis §4.1 Notes cell (line 64 of `thesis/WRITING_STATUS.md`)
carries an explicit flag "sections 01_05 (Temporal & Panel EDA), 01_06
(Decision Gates) deferred — flagged where claims await them". §4.1.3
and §4.1.4 Notes cells carry analogous 01_06-deferred residuals. These
flags land on 01_06 closure; T12 resolves them in-row. BACKLOG F1
(aoestats `canonical_slot`) is a Phase 02 unblocker that 01_06 must
formally register as a READY_CONDITIONAL predicate without resolving
it. Further delay keeps §4.4.1–3 and all of Chapters 5–6 blocked on
Phase 02–04.

## Assumptions & unknowns

- **Assumption:** The Manual 01 §6.1 four-deliverable taxonomy (data
  dictionary, data quality report, risk register, modeling-readiness
  decision) is the authoritative gate structure. No project-local
  redefinition.
- **Assumption:** Existing 01_05 exit memos (`decision_gate_sc2egset.md`,
  `01_05_09_gate_memo.md`) are inputs to 01_06, not substitutes. The
  01_06 per-dataset readiness memo incorporates them by reference and
  extends their scope to all of 01_01–01_05.
- **Assumption:** 01_06 consumes prior artifacts only; does not re-run
  analyses, re-query DuckDB, or reprocess data (per Invariant I9 —
  step conclusions derive only from prior steps' artifacts on disk).
  Notebook cells may re-execute cached DuckDB reads for reproducibility
  assertions but must not introduce new findings beyond consolidation.
- **Assumption:** Bundled-PR approach (1 PR × 3 datasets) is correct
  given the cross-dataset rollup's role-assignment obligation. User
  confirmed 2026-04-19.
- **Assumption:** Four-notebook-per-dataset model (one per §6.1
  deliverable) is preferred over a combined notebook, for traceability.
  User confirmed 2026-04-19.
- **Assumption:** Executor runs notebooks iteratively with per-notebook
  verification (hypothesis + falsifier up front, every output read,
  revise if rejected) per
  `.claude/rules/thesis-writing.md`-equivalent discipline for data
  notebooks — see T05–T07 execution instructions.
- **Assumption:** PRIMARY / SUPPLEMENTARY VALIDATION role assignment
  (sc2egset PRIMARY in-game / aoe2companion PRIMARY population-scale /
  aoestats SUPPLEMENTARY) is user-approved 2026-04-19. The cross-rollup
  memo must still justify it from evidence, not assert by fiat.
- **Assumption:** Anticipated verdicts (sc2egset READY_FULL;
  aoestats READY_CONDITIONAL predicate = BACKLOG F1;
  aoe2companion READY_FULL) are predictions only; executor verifies
  against actual 01_01–01_05 artifacts and may revise.
- **Unknown:** Whether any dataset's INVARIANTS.md §5 will flip a
  PARTIAL row as a direct consequence of 01_06 consolidation. Expected
  zero transitions; T10 is a no-op placeholder if so.

## Literature context

Methodology-internal. No new bibtex entries.

- **Manual 01 §6 "Decision Gates"** — the four required deliverables
  and the "one-page summary from memory" heuristic.
- **[CRISP-ML(Q)]** — phase-transition quality gates concept (cited
  Manual §6.2). Applied here: 01→02 gate requires documented
  assessment + confirmed absence of leakage.
- **[Gebru2021Datasheets]** — motivates the data-dictionary
  deliverable's scope beyond schema (collection, biases, licensing).
- **[Kapoor2023Reforms]** — 8-module reporting standard; Module 2
  (Data Quality) and Module 3 (Data Preprocessing) map to §6.1
  deliverables 2 and 4 respectively.
- **[Davis2024SportsAnalytics]** — cited at Manual §5.2; relevant for
  sports-specific risk-register entries (patch heterogeneity,
  survivorship, nested dependencies).

These sources are already cited in the project's methodology tree;
01_06 artifacts reference them by key, no new entries added.

## Execution Steps

> **Pre-execution (parent responsibility):** Parent dispatches
> `reviewer-adversarial` to produce
> `planning/current_plan.critique.md` before any executor begins T01.
> This file is not created by any of T01–T14; it is a prerequisite
> artifact owned by the parent/reviewer-adversarial agent. If
> `planning/current_plan.critique.md` is absent when T01 dispatch
> begins, executor halts and reports to parent before proceeding.

### T01 — Author spec `01_06_readiness_criteria.md`

**Objective:** Lock the four-deliverable schema, the verdict taxonomy,
and the role-assignment criteria so 01_06 executions are deterministic
and cross-dataset comparable.

**Instructions:**
1. Read Manual 01 §6 in full.
2. Read `reports/specs/01_05_preregistration.md` for the spec template
   precedent (frontmatter, amendment log, binding mechanism).
3. Author `reports/specs/01_06_readiness_criteria.md` with sections:
   - §1 Four-deliverable schema (column sets for
     data_dictionary.csv, data_quality_report.md, risk_register.csv,
     modeling_readiness.md).
   - §2 Verdict taxonomy (**four tiers**, not three):
     - **READY_FULL** — no BLOCKER in risk register; no HIGH/MEDIUM
       defence-in-thesis residuals open; Phase 02 proceeds
       unconditionally.
     - **READY_WITH_DECLARED_RESIDUALS** — no BLOCKER; ≥1 HIGH/MEDIUM
       defence-in-thesis residual documented with explicit Chapter 4
       anchor. Phase 02 proceeds unconditionally; residuals are
       landed in the thesis text rather than fixed pre-Phase-02.
     - **READY_CONDITIONAL** — has BLOCKER but mitigation path exists
       and is registered in BACKLOG; Phase 02 may proceed on narrower
       scope OR after BACKLOG item resolves — decision named
       explicitly.
     - **NOT_READY** — unresolvable BLOCKER; return to Pipeline
       Section X with specific remediation instruction.
     Each verdict must specify its **flip-predicate**: the exact
     condition under which the verdict would transition to a less-
     restricted state. For READY_FULL and NOT_READY, the predicate is
     trivial (N/A and "address the unresolvable BLOCKER" respectively).
   - §3 Role-assignment criteria — **six dimensions** enumerated
     explicitly; a dataset can be PRIMARY on one dimension and
     SUPPLEMENTARY on another. For each dimension, the spec names the
     comparable metric + decision rule + falsifier:
     - **D1 Sample-scale** — metric: total cleaned Phase-02-ready rows
       (from data_quality_report.md CONSORT final stage). Decision:
       PRIMARY if dataset's count ≥ 10× the second-largest;
       SUPPLEMENTARY otherwise. Falsifier: if another dataset exceeds
       10× the current PRIMARY within Phase 02 refreshes, role flips.
     - **D2 Skill-signal** — metric: observed-scale ICC with CI on the
       pre-game reference window (from 01_05 ICC artifacts). Decision
       requires **two filters passed in conjunction**:
       - **Filter F1 (quantitative):** ICC point estimate ≥ 0.01.
         **Justification:** 0.01 is the conventional ICC
         ignorable-variance floor (Koo & Li 2016 JCM §3.1; Cicchetti
         1994); below this, between-player variance is
         indistinguishable from rounding error in typical skill-
         estimation studies. Threshold cited, not invented.
       - **Filter F2 (qualitative):** verdict field in the
         **dataset's INVARIANTS.md §5 row** for the ICC-relevant
         invariant (I8 cross-game comparability) does NOT read
         `FALSIFIED`. INVARIANTS.md §5 is the canonical, uniform
         verdict source across all three datasets; it uses the token
         set `{HOLDS, PARTIAL, FALSIFIED, DEVIATES}` consistently.
         The per-dataset ICC JSON artifacts use inconsistent
         schemas (sc2egset `verdict`, aoestats `falsifier_verdict`,
         aoe2companion prose `verdict` value) and are **not** the
         canonical source; they are cited in T05/T06/T07 as evidence
         but the F2 filter reads from INVARIANTS.md §5 only.
         `HOLDS`/`PARTIAL` verdicts pass F2; `FALSIFIED`/`DEVIATES`
         fail.
       PRIMARY requires passing BOTH F1 and F2 AND being the largest
       point-estimate ICC among F2-passing candidates. SUPPLEMENTARY
       otherwise. Falsifier: if a SUPPLEMENTARY dataset's ICC later
       rises above the PRIMARY's at equal CI width AND its
       INVARIANTS.md §5 verdict transitions out of FALSIFIED, role
       flips.
     - **D3 Temporal coverage** — metric: months of **continuous**
       cleaned-data availability, where "continuous" is defined by
       SQL pattern: `SELECT COUNT(DISTINCT DATE_TRUNC('month',
       started)) FROM <cleaned_table> WHERE month has ≥ N cleaned
       rows`.
       **Density floor N = 100 rows/month justification:** derived
       from binomial SE bound — at N=100 observations per month, the
       standard error of any within-month proportion estimate is
       ≤ 5% (SE = √(p(1-p)/N) ≤ √(0.25/100) = 0.05 at p=0.5). 100 is
       the project-set minimum for within-month rate stability at
       SE ≤ 5%. Threshold is derived, not invented. If an executor
       in T08 needs a different density floor per-dataset, they
       invoke spec amendment (T01 §4 forbids mid-execution amendment;
       halt + report to parent).
       Decision: PRIMARY if month-count ≥ 2× the median across
       candidates at this density floor. Comparable on D3 only among
       datasets with the same density floor applied. Falsifier: if
       another dataset later exceeds the PRIMARY's density-filtered
       month-count.
     - **D4a Identity rename-stability** — metric: Branch assignment
       per `.claude/scientific-invariants.md` I2 extended procedure.
       Decision: PRIMARY if Branch (i) (API-namespace ID,
       provider-level rename-stable); SUPPLEMENTARY if Branch (ii/iii)
       (scoped or handle-based with documented migration risk) or
       Branch (v) (structurally-forced).
     - **D4b Identity within-scope rigor** — metric: measured
       collision rate and migration rate for the chosen identity key
       within its declared scope (per dataset's INVARIANTS.md §2).
       Decision: PRIMARY if both rates are < 15% AND documented with
       SQL; SUPPLEMENTARY if Branch (v) structurally-forced (rates
       unmeasurable within dataset) or if either rate ≥ 15%.
     - **D5 Patch resolution** — metric: presence of patch-id or
       equivalent binding column. Decision: PRIMARY if a patch
       identifier is present and usable for cohort slicing;
       SUPPLEMENTARY otherwise.
     - **D6 Controlled-asymmetry flag (I8 controlled variable)** —
       NOT a cross-dataset comparability dimension. Metric: presence
       of game-internal event-timeline data (SC2 replays carry this;
       neither AoE2 corpus does). This is an **asymmetry flag**
       documenting the thesis's Invariant #8 controlled variable, not
       a role dimension. sc2egset carries the flag; AoE2 datasets are
       N/A. D6 is listed in the T08 §2 matrix for transparency but
       **DOES NOT count toward PRIMARY-role weight** in T08 §5 Phase
       02 kickoff discussion. Cross-dataset role tally is restricted
       to D1–D5 + D4a/b (D4 contributes 2 sub-dimensions).
     Each of D1–D6 must name its "comparable yes/no" predicate: under
     what conditions cross-dataset comparison on this dimension is
     permitted (e.g., D2 skill-signal comparison requires both
     datasets to have pre-game reference windows of comparable
     duration).
   - §4 Binding: spec cited by SHA in each 01_06 notebook's docstring.
     **This plan locks the spec at v1.0 and forbids mid-execution
     amendments.** If an executor finds a defect in §1/§2/§3 during
     T05–T08, they halt and report to parent; parent opens a
     follow-up PR to amend the spec, NOT this PR. This contrasts with
     the `01_05_preregistration.md` practice (five amendments during
     01_05 execution); 01_06 deliberately chooses a locked-spec
     posture to prevent adversarial-review churn.
   - §5 Amendment log (initial v1.0 entry dated 2026-04-19).

**Verification:**
- File exists at `reports/specs/01_06_readiness_criteria.md`.
- §1–§5 populated.
- §1 column sets enumerated explicitly (no "etc.").
- §2 four verdicts (READY_FULL / READY_WITH_DECLARED_RESIDUALS /
  READY_CONDITIONAL / NOT_READY) each with flip-predicate.
- §3 six dimensions (D1–D6) each with metric + decision rule + falsifier.
- §4 spec-lock posture stated explicitly ("forbids mid-execution
  amendments").

**File scope:**
- `reports/specs/01_06_readiness_criteria.md` (Create)

**Read scope:**
- `docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md` §6
- `reports/specs/01_05_preregistration.md` (template precedent)

---

### T02 — sc2egset ROADMAP: insert Role block + retroactive 01_05_09 + 01_06 step YAMLs + STEP_STATUS entries

**Objective:** (a) insert a "Role: TO BE DETERMINED" block into
sc2egset's ROADMAP (which currently lacks it, unlike aoestats +
aoe2companion); (b) retroactively add `01_05_09` Step wrapping the
existing `decision_gate_sc2egset.md` artifact (as `complete` from the
outset, since the artifact already exists on disk); (c) decompose
sc2egset's 01_06 pipeline section into four concrete Steps.

**Atomicity note:** all three operations land in this single task. The
STEP_STATUS.yaml write at the end of T02 is **atomic**: the five new
entries (01_05_09 complete + four 01_06 not_started) are written in
one file-write, so PIPELINE_SECTION_STATUS.yaml's derivation rule is
never observed in an intermediate state mid-task.

**Instructions:**
1. Read sc2egset ROADMAP.md in full. Locate header metadata block
   (before first `## Phase 01` section). Identify the exact insertion
   point for the Role block (match aoestats line 12 and aoe2companion
   line 12 layouts for parity).
2. **Insert new Role block** at that position with verbatim content:
   ```
   > **Role: TO BE DETERMINED.** Role assignment (PRIMARY vs
   > SUPPLEMENTARY VALIDATION, per dimension D1–D6 in
   > `reports/specs/01_06_readiness_criteria.md` §3) will be
   > formalized at the Phase 01 Decision Gate (01_06) based on
   > comparative data quality findings.
   ```
   This is a **create** operation, not an update (sc2egset's ROADMAP
   never carried this flag).
3. **Rename the existing artifact for naming parity** with aoestats'
   `01_05_09_gate_memo.md` convention: `git mv
   src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/decision_gate_sc2egset.md
   src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_09_gate_memo.md`.
   This closes the retroactive-symmetry naming divergence flagged by
   Pass 2 reviewer-adversarial.
4. Locate the 01_05 step YAML list (01_05_01..01_05_08). Retroactively
   append Step YAML 01_05_09 with: `step_number: 01_05_09`, `name:
   "01_05 exit memo (retroactive)"`, `description: "Consolidate 01_05
   findings into a single exit memo for Phase 01 gate consumption.
   Artifact authored 2026-04-18 (pre-01_06) and retroactively bound
   to this Step in 01_06 ROADMAP refresh."`, `notebook_path: null`
   (artifact is pre-existing, not notebook-produced), `outputs:
   src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_09_gate_memo.md`,
   `completed_at: "2026-04-18"` (date of the original artifact, NOT
   T02 execution date), `gate: "memo exists on disk; covers
   01_05_01..01_05_08 findings"`.
5. Append four 01_06 Step YAMLs (01_06_01 through 01_06_04) with
   `step_number`, `name`, `description`, `notebook_path`, `inputs`,
   `outputs`, `gate`, `thesis_mapping`, `research_log_entry` populated
   per the 01_05 template, referencing
   `reports/specs/01_06_readiness_criteria.md` v1.0 SHA in each
   step's notebook_path docstring expectation.
6. **Atomically update STEP_STATUS.yaml**: append one `complete`
   entry for 01_05_09 (retroactive, with comment noting the
   retroactivity and `completed_at: 2026-04-18`) and four
   `not_started` entries for 01_06_01..04.

**Verification:**
- ROADMAP carries the Role block at the same relative position as
  aoestats and aoe2companion ROADMAPs.
- ROADMAP 01_05 list now ends at 01_05_09 (was 01_05_08).
- ROADMAP 01_06 section lists four step YAMLs; all YAML parses via
  `python -c "import yaml; ..."`.
- STEP_STATUS has five new entries: 01_05_09 = `complete` (retroactive
  with comment), 01_06_01..04 = `not_started`.
- PIPELINE_SECTION_STATUS.yaml for sc2egset shows `01_05: complete`
  unchanged (since 01_05_09 is added at `complete`, derivation holds).

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/decision_gate_sc2egset.md` → `01_05_09_gate_memo.md` (git mv; rename)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` (Update — Role block creation + 01_05_09 Step + four 01_06 Steps)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` (Update — 5 new entries, atomic write)

**Read scope:**
- `reports/specs/01_06_readiness_criteria.md` (T01 output)
- sc2egset ROADMAP.md (current state, find insertion points)
- aoestats + aoe2companion ROADMAPs line 12 (layout precedent for Role block)
- sc2egset 01_05 step YAMLs (template reference)
- `decision_gate_sc2egset.md` (pre-rename: verify artifact exists for 01_05_09 binding)

---

### T03 — aoestats ROADMAP: 01_06 step YAMLs + STEP_STATUS entries + Role block update

**Objective:** Decompose aoestats' 01_06 pipeline section into four
concrete Steps. aoestats already has `01_05_09_gate_memo.md` and a
matching Step YAML, so no retroactive 01_05 work is required here.

**Atomicity note:** four `not_started` 01_06 entries written in one
file-write; PIPELINE_SECTION_STATUS.yaml untouched until T09.

**Instructions:**
1. Read aoestats ROADMAP.md; locate 01_06 placeholder.
2. Append four Step YAMLs 01_06_01..01_06_04, same shape as T02,
   referencing spec v1.0 SHA.
3. Update ROADMAP top-of-file role declaration. Existing "Role: TO BE
   DETERMINED" block at aoestats line 12 is **updated** (not created)
   to:
   ```
   Role: PRIMARY on patch-resolution (D5, patch_id binding);
   SUPPLEMENTARY on sample-scale (D1), temporal-coverage (D3), and
   identity-rigor (D4, Branch (v) structurally-forced); SUPPLEMENTARY
   on skill-signal (D2, ICC 0.027 pending BACKLOG F1 canonical_slot
   resolution); N/A on in-game events (D6). Assigned at 01_06 per
   cross_dataset_phase01_rollup.md. Rationale: patch-anchored,
   BACKLOG F1 canonical_slot pending, Branch (v) structurally-forced.
   ```
4. **Atomically update STEP_STATUS.yaml**: append four `not_started`
   entries for 01_06_01..04.

**Verification:**
- ROADMAP 01_06 section lists four step YAMLs; YAML parses.
- STEP_STATUS has four new `not_started` entries.
- Role block at line 12 flipped from TBD to dimension-specific
  assignment.
- PIPELINE_SECTION_STATUS.yaml unchanged by this task.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` (Update)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml` (Update — 4 new entries)

**Read scope:**
- `reports/specs/01_06_readiness_criteria.md`
- aoestats ROADMAP.md (line 12 for Role block update)
- aoestats 01_05 step YAMLs (template)

---

### T04 — aoe2companion ROADMAP: retroactive 01_05_09 (as `not_started`) + 01_06 step YAMLs + STEP_STATUS entries

**Objective:** Same ROADMAP update pattern as T02 (sc2egset) and T03
(aoestats), but aoe2companion's retroactive 01_05_09 **is net-new work**
(no pre-existing artifact on disk), so the Step is added as
`not_started` in T04 and completed by T07.

**Atomicity note for PIPELINE_SECTION_STATUS derivation chain
(honest-state posture, Pass 2 fix):** appending a `not_started`
01_05_09 Step to aoe2companion's STEP_STATUS forces aoe2companion
01_05 to derive back from `complete` to `in_progress`. Rather than
leave `PIPELINE_SECTION_STATUS.yaml` lying against its own stated
rule, T04 **explicitly re-derives and writes** the honest state:

1. T04 writes 01_05_09 as `not_started` at the STEP_STATUS level AND
   updates `PIPELINE_SECTION_STATUS.yaml` to `01_05: in_progress`
   (correctly derived from the new STEP_STATUS contents).
2. T07 checkpoint 1 authors the 01_05_09 memo, flips STEP_STATUS
   01_05_09 to `complete`, AND re-derives `PIPELINE_SECTION_STATUS`
   to `01_05: complete` (all 9 steps now complete).
3. T07 checkpoints 2–5 execute 01_06_01..04.
4. T09 handles only the final PHASE_STATUS refresh plus any 01_06
   PIPELINE_SECTION_STATUS transition.

This way each intermediate commit is self-consistent. The T04–T07
window is documented mid-PR state (01_05 = `in_progress`) rather than
an implicit falsehood.

**Instructions:**
1. Read aoe2companion ROADMAP.md; locate 01_05 step YAML list tail
   (currently ends at 01_05_08) + 01_06 placeholder.
2. Retroactively append `01_05_09` Step YAML: `step_number: 01_05_09`,
   `name: "01_05 exit memo"`, `description: "Consolidate 01_05 findings
   into a single exit memo for Phase 01 gate consumption. Authored in
   T07 as part of the 01_06 bundled PR (retroactive Step addition)."`,
   `notebook_path: sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_09_gate_memo.py`,
   `outputs: src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_09_gate_memo.md`,
   `gate: "memo exists; cites all 01_05 artifacts by path"`.
3. Append four 01_06 Step YAMLs (01_06_01..01_06_04), same shape as
   T02/T03, referencing spec v1.0 SHA.
4. Update ROADMAP top-of-file role declaration. Existing "Role: TO BE
   DETERMINED" block at aoe2companion line 12 is **updated** (not
   created) to:
   ```
   Role: PRIMARY for sample-scale (D1) and temporal-coverage (D3)
   dimensions; co-PRIMARY for identity-rigor (D4); SUPPLEMENTARY on
   skill-signal (D2, ICC FALSIFIED 0.003), patch-resolution (D5), and
   N/A on in-game events (D6). Assigned at 01_06 per
   reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md.
   Rationale: 30.5M matches, rename-stable profileId at 2.57% / 3.55%
   (reconciled 2026-04-19). Skill-signal SUPPLEMENTARY status deferred
   to sc2egset primary.
   ```
5. **Atomically update STEP_STATUS.yaml**: append 1 `not_started` entry
   for 01_05_09 (with comment `# retroactive; memo authored in T07
   checkpoint 1`) and 4 `not_started` entries for 01_06_01..04.
6. **Update PIPELINE_SECTION_STATUS.yaml** to reflect the re-derived
   state: set `01_05: in_progress` (since 01_05_09 is now a
   not-started step). The derivation rule at line 3 of the yaml is
   now honestly satisfied. T07 checkpoint 1 will restore
   `01_05: complete` after the memo lands.

**Verification:**
- ROADMAP has both `01_05_09` and `01_06_01..01_06_04` step YAMLs.
- STEP_STATUS has five new entries, all `not_started`.
- 01_05_09 entry carries the `# retroactive; memo authored in T07
  checkpoint 1` comment.
- Role block at line 12 flipped from TBD to the dimension-specific
  assignment above.
- PIPELINE_SECTION_STATUS.yaml shows `01_05: in_progress` (honestly
  re-derived from STEP_STATUS containing 01_05_09 not_started).
  T07 checkpoint 1 will restore `01_05: complete` atomically after
  the memo lands.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` (Update)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml` (Update — 5 new entries)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/PIPELINE_SECTION_STATUS.yaml` (Update — 01_05 complete → in_progress)

**Read scope:**
- `reports/specs/01_06_readiness_criteria.md`
- aoe2companion ROADMAP.md (line 12 for Role block update)
- aoe2companion research_log.md (for 01_05 findings to memo in T07)

---

### T05 — sc2egset 01_06 execution (4 notebooks + artifacts, iterative)

**Objective:** Execute sc2egset's four 01_06 notebooks in strict
sequence with per-notebook verification. Produce the four §6.1
deliverables.

**Execution mode (user-directed 2026-04-19):** Notebooks are executed
iteratively, NOT in parallel. Per `.claude/rules` notebook discipline:

1. State the hypothesis + falsifier at the top of each notebook cell.
2. Run the cell.
3. Read every output line.
4. Compare against the stated hypothesis.
5. If rejected: revise the cell (or the upstream artifact if the
   revision surfaces an error) and re-run. Never rubber-stamp after one
   run.
6. Only after the notebook's gate is met does the executor move to the
   next notebook.

Order: 01_06_01 (data dictionary) → 01_06_02 (data quality report) →
01_06_03 (risk register) → 01_06_04 (modeling readiness). 01_06_04
consumes outputs from 01_06_01..03, so the sequence is load-bearing.

**Instructions (per notebook):**

**01_06_01 — Data Dictionary**
1. Hypothesis: every column consumed downstream in Phase 02 (i.e.,
   appearing in `matches_1v1_clean`, `matches_history_minimal`, or
   Phase 02 feature spec) can be categorised as PRE_GAME,
   POST_GAME_HISTORICAL, or TARGET under Invariant I3.
2. Falsifier: any column that resists categorisation, or any
   categorisation that contradicts I3 (POST_GAME column consumed as
   feature).
3. Notebook: enumerate columns from the schema YAMLs; assign
   `temporal_classification` per I3; build the dictionary CSV.
4. Outputs:
   - `reports/artifacts/01_exploration/06_decision_gates/data_dictionary_sc2egset.csv`
     (columns: `column_name`, `dtype`, `semantics`, `valid_range`,
     `nullability`, `units`, `temporal_classification`,
     `provenance_step`, `invariant_notes`)
   - `reports/artifacts/01_exploration/06_decision_gates/data_dictionary_sc2egset.md`
     (human-readable companion with grouping by table + narrative on
     the temporal classification)
5. Gate: every Phase-02 feature-candidate column has a row; no column
   categorised as POST_GAME is consumed by any feature (I3 check).

**01_06_02 — Data Quality Report**
1. Hypothesis: the CONSORT-style flow from raw → `matches_1v1_clean`
   accounts for every dropped row category (null, sentinel, outlier,
   duplicate) with a named cleaning rule.
2. Falsifier: any "unexplained" row count delta between stages; any
   cleaning rule whose effect is untraceable to a config or registry
   entry.
3. Notebook: consolidate 01_02_04 null/sentinel reports, 01_03
   profiling artifacts, 01_04_01 missingness ledger, 01_04_02 cleaning
   registry into a CONSORT flow. Trace each R0N rule back to its
   `*_cleaning.yaml` row.
4. Output:
   `reports/artifacts/01_exploration/06_decision_gates/data_quality_report_sc2egset.md`
   with CONSORT flow (text ASCII acceptable), rule registry, route-
   decision table (5% / 5–40% / ≥40% per column).
5. Gate: CONSORT flow balanced (sum of drops = raw − clean); rule
   registry fully traceable.

**01_06_03 — Risk Register**
1. Hypothesis: every INVARIANTS.md §5 PARTIAL/VIOLATED row, every
   BACKLOG F* item registered as affecting sc2egset, and every 01_05
   adversarial-audit residual produces a row in the risk register with
   severity, evidence path, Phase 02 implication, and thesis-defence
   reference.
2. Falsifier: any known issue missing from the register; any register
   row missing its evidence artifact path.
3. Notebook: enumerate from INVARIANTS.md §5, BACKLOG.md (filter
   sc2egset), 01_05 artifacts (leakage audit, ICC, PSI, survivorship).
4. Outputs:
   - `reports/artifacts/01_exploration/06_decision_gates/risk_register_sc2egset.csv`
     (columns: `risk_id`, `category`, `description`,
     `evidence_artifact`, `severity`, `phase02_implication`,
     `thesis_defence_reference`, `mitigation_status`)
   - `reports/artifacts/01_exploration/06_decision_gates/risk_register_sc2egset.md`
     (human-readable companion)
5. Gate: every INVARIANTS.md §5 non-HOLDS row has a corresponding
   risk_id; severity BLOCKER rows (if any) map to BACKLOG items.

**01_06_04 — Modeling Readiness**
1. Hypothesis: sc2egset passes Phase 01 gate as **READY_WITH_DECLARED_
   RESIDUALS** — no BLOCKER in risk register, but 5+ HIGH/MEDIUM
   defence-in-thesis residuals (uncohort-filtered PSI B2 fix, ICC
   INCONCLUSIVE 0.046, tournament-only population scope, I8 PARTIAL
   schema-divergence, 2023-Q3 duration drift |d|=0.544) documented
   with Chapter 4 anchors.
2. Falsifier: any BLOCKER row surfaces in 01_06_03 (would downgrade
   to READY_CONDITIONAL or NOT_READY), or zero HIGH/MEDIUM residuals
   (would upgrade to READY_FULL).
3. Notebook: consume 01_06_01 + 01_06_02 + 01_06_03 artifacts; produce
   the verdict memo per spec §2 (four-tier taxonomy).
4. Output:
   `reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_sc2egset.md`
   — verdict, flip-predicate (if non-FULL), list of BLOCKER risk_ids
   (if any), list of HIGH/MEDIUM residuals with Chapter 4 anchor,
   explicit go/no-go for Phase 02 kickoff.
5. Gate: verdict stated verbatim from spec §2 taxonomy; flip-predicate
   named explicitly for non-FULL verdicts; each HIGH/MEDIUM residual
   has a Chapter 4 defence anchor.

**Verification (task-level):** all four artifacts present; modeling-
readiness verdict consistent with risk-register BLOCKER set.

**Pause/resume checkpoint (user-directed 2026-04-19):** after each of
the four notebooks completes, executor pauses and reports the
hypothesis-falsifier outcome to parent before proceeding to the next
notebook. If any notebook's hypothesis is rejected, executor halts
entirely and reports; do not proceed with a failed hypothesis.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/06_decision_gates/01_06_01_data_dictionary.py` (Create)
- `sandbox/sc2/sc2egset/01_exploration/06_decision_gates/01_06_02_data_quality_report.py` (Create)
- `sandbox/sc2/sc2egset/01_exploration/06_decision_gates/01_06_03_risk_register.py` (Create)
- `sandbox/sc2/sc2egset/01_exploration/06_decision_gates/01_06_04_modeling_readiness.py` (Create)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/06_decision_gates/data_dictionary_sc2egset.{csv,md}` (Create)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/06_decision_gates/data_quality_report_sc2egset.md` (Create)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/06_decision_gates/risk_register_sc2egset.{csv,md}` (Create)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_sc2egset.md` (Create)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` (Update — four entries flipped to `complete`)

**Read scope:**
- `reports/specs/01_06_readiness_criteria.md`
- sc2egset INVARIANTS.md, ROADMAP.md, STEP_STATUS.yaml
- sc2egset 01_01..01_05 artifacts (all)
- sc2egset research_log.md
- `decision_gate_sc2egset.md` (01_05 exit memo)
- `planning/BACKLOG.md` (for sc2egset-flagged items, if any)

---

### T06 — aoestats 01_06 execution (4 notebooks + artifacts, iterative)

**Objective:** Same as T05 for aoestats. Anticipated verdict is
READY_CONDITIONAL with BACKLOG F1 (`canonical_slot`) as the
flip-predicate — execution verifies against actual artifacts.

**Execution mode:** iterative per T05 specification.

**Instructions:** analogous to T05, with aoestats-specific content:

- **01_06_01 data dictionary:** must flag `team=0/team=1` columns in
  `matches_1v1_clean` as "per-slot, affected by `[PRE-canonical_slot]`
  flag pending BACKLOG F1 resolution" in `invariant_notes`.
- **01_06_02 data quality report:** CONSORT flow must include the 28
  corrupt-duration matches dropped in rm_1v1; cleaning rule registry
  must reference `cleaning.yaml` R01..R0N with `leaderboard =
  'random_map'` scope anchor.
- **01_06_03 risk register:** BLOCKER row for aoestats
  `canonical_slot`-pending team=1 skill bias (W3 ARTEFACT_EDGE);
  category SLOT_ASYMMETRY; phase02_implication "per-slot features
  forbidden until F1 lands; aggregate / UNION-ALL-symmetric features
  permitted"; mitigation_status `OPEN (BACKLOG F1)`.
- **01_06_04 modeling readiness:** verdict **READY_CONDITIONAL**;
  flip-predicate "BACKLOG F1 `canonical_slot` resolved AND
  INVARIANTS.md §5 I5 row transitions PARTIAL → HOLDS". Per
  reviewer-adversarial finding: aoestats INVARIANTS.md §5 line 129
  notes I5 requires W4 (schema amendment, distinct workstream from
  F1). Plan flip-predicate must state this coupling explicitly:
  "aoestats READY_CONDITIONAL → READY_WITH_DECLARED_RESIDUALS requires
  BOTH F1 resolution AND W4 schema amendment; if F1 lands without W4,
  verdict remains READY_CONDITIONAL with narrower aggregate-features
  scope". Explicit scope statement: "Phase 02 may proceed on aggregate
  / UNION-ALL-symmetric features; per-slot features deferred until F1
  + W4 both land".

**Pause/resume checkpoint:** same four-notebook checkpoint discipline as
T05.

**File scope:**
- `sandbox/aoe2/aoestats/01_exploration/06_decision_gates/01_06_01_data_dictionary.py` (Create)
- `sandbox/aoe2/aoestats/01_exploration/06_decision_gates/01_06_02_data_quality_report.py` (Create)
- `sandbox/aoe2/aoestats/01_exploration/06_decision_gates/01_06_03_risk_register.py` (Create)
- `sandbox/aoe2/aoestats/01_exploration/06_decision_gates/01_06_04_modeling_readiness.py` (Create)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoestats.{csv,md}` (Create)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/data_quality_report_aoestats.md` (Create)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/risk_register_aoestats.{csv,md}` (Create)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoestats.md` (Create)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml` (Update — 4 entries flipped to `complete`)

**Read scope:**
- `reports/specs/01_06_readiness_criteria.md`
- aoestats INVARIANTS.md, ROADMAP.md, STEP_STATUS.yaml
- aoestats 01_01..01_05 artifacts (including 01_04_05 I5 diagnosis and
  01_05_09 gate memo)
- aoestats research_log.md
- `planning/BACKLOG.md` (F1 in full)

---

### T07 — aoe2companion 01_05_09 retroactive memo + 01_06 execution (5 notebooks total, iterative)

**Objective:** Produce the retroactive `01_05_09_gate_memo.md` for
aoe2companion (fills the symmetry gap identified in T04), then execute
the four 01_06 notebooks. Anticipated verdict is READY_FULL.

**Execution mode:** iterative per T05 specification. Order:
`01_05_09` (retroactive) → `01_06_01` → `01_06_02` → `01_06_03` →
`01_06_04`.

**Instructions:**

**01_05_09 — 01_05 exit memo (retroactive)**
1. Hypothesis: aoe2companion's 01_05 findings can be consolidated into
   a single exit memo matching the format of sc2egset's
   `decision_gate_sc2egset.md` and aoestats' `01_05_09_gate_memo.md`.
2. Falsifier: any 01_05 finding that resists summarisation or
   contradicts the W-verdicts recorded in spec v1.0.5 §11.
3. Notebook: consolidate 01_05_01..01_05_08 findings (ICC verdict,
   PSI audit, leakage audit, temporal drift, survivorship, 01_05_05
   sensitivity) into a standard exit memo format.
4. Output:
   `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_09_gate_memo.md`
5. Gate: memo format matches sibling datasets' exit memos; cites each
   01_05 artifact by path.

Then 01_06_01..01_06_04 analogous to T05/T06 with aoe2companion-specific
content:

- **01_06_01 data dictionary:** flag identity-rate reconciliation
  (2026-04-19: 2.57% / 3.55% rm_1v1 scope) in `invariant_notes` for
  `profileId` column; note Branch (i) API-namespace identifier.
- **01_06_02 data quality report:** CONSORT flow must include the
  2.25% country NULL retention (MissingIndicator route, MAR primary /
  MNAR sensitivity per §4.2.3); rating=0 / ratings_raw empty for lb=6
  noted but scope-boundary, not a risk.
- **01_06_03 risk register:** LOW RESOLVED for identity-rate
  reconciliation; HIGH for ICC FALSIFIED 0.003 at §4.4.5 (defence, not
  blocker); no BLOCKERs expected.
- **01_06_04 modeling readiness:** verdict **READY_WITH_DECLARED_
  RESIDUALS** (not READY_FULL — ICC FALSIFIED 0.003 at reference
  window is a HIGH skill-signal residual with §4.4.5 defence anchor;
  I2 PARTIAL at 2.57% rename rate is a defence item with §4.2.2
  anchor; 342 duration clock-skew rows retained is a MEDIUM residual).
  No BLOCKER; Phase 02 proceeds unconditionally; residuals landed in
  thesis. Flip-predicate N/A.

**Pause/resume checkpoint:** same four-notebook checkpoint discipline
as T05, plus an additional checkpoint after 01_05_09 memo completes
and before 01_06_01 begins (total: 5 checkpoints for this task).

**Checkpoint 1 (01_05_09 memo) atomicity:** when the 01_05_09 memo
lands, executor MUST in the same task step: (a) flip STEP_STATUS
01_05_09 to `complete`, (b) re-derive and write
`PIPELINE_SECTION_STATUS.yaml` `01_05: complete` (restoring the
honest state that T04 temporarily set to `in_progress`). **Commit
atomicity:** both writes (memo + STEP_STATUS + PIPELINE_SECTION_STATUS)
are a single git commit. Executor does NOT commit the memo and the
YAML writes separately. Only after the atomic commit lands does the
executor pause for parent check-in. Do not split across two commits.

**File scope:**
- `sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_09_gate_memo.py` (Create)
- `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_01_data_dictionary.py` (Create)
- `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_02_data_quality_report.py` (Create)
- `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_03_risk_register.py` (Create)
- `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_04_modeling_readiness.py` (Create)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_09_gate_memo.md` (Create)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoe2companion.{csv,md}` (Create)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_quality_report_aoe2companion.md` (Create)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/risk_register_aoe2companion.{csv,md}` (Create)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoe2companion.md` (Create)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml` (Update — 01_05_09 + four 01_06 entries flipped to `complete`)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/PIPELINE_SECTION_STATUS.yaml` (Update — checkpoint 1 restores 01_05: complete)

**Read scope:**
- `reports/specs/01_06_readiness_criteria.md`
- aoe2companion INVARIANTS.md, ROADMAP.md, STEP_STATUS.yaml
- aoe2companion 01_01..01_05 artifacts
- aoe2companion research_log.md (especially 2026-04-19 identity-rate
  reconciliation entry)

---

### T08 — Cross-dataset rollup memo (dimension-matrix form)

**Objective:** Produce one cross-dataset artifact resolving the PRIMARY
/ SUPPLEMENTARY VALIDATION role assignment along six enumerated
dimensions (D1–D6 per spec §3), populated from T05/T06/T07 quantitative
artifacts, plus Phase 02 go/no-go per dataset.

**Instructions:**
1. Read the three `modeling_readiness_<dataset>.md` from T05–T07 plus
   the three `data_dictionary_<dataset>.csv` and
   `data_quality_report_<dataset>.md` for the per-dimension metrics.
2. Produce a rollup memo at
   `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md`
   containing:

   **§1 — Three-dataset verdict table** (one row per dataset).
   **The row values below are the plan's anticipated outcome;
   executor may override any cell based on actual 01_06 artifact
   findings in T05–T07, following spec §2 taxonomy. The template is
   illustrative, not binding.**

   | Dataset | Verdict (anticipated) | Flip-predicate | Phase 02 go/no-go |
   |---|---|---|---|
   | sc2egset | READY_WITH_DECLARED_RESIDUALS | N/A (residuals landed in thesis) | GO |
   | aoestats | READY_CONDITIONAL | F1 + W4 both resolved | GO-NARROW (aggregate features only; per-slot deferred until F1+W4) |
   | aoe2companion | READY_WITH_DECLARED_RESIDUALS | N/A | GO |

   **§2 — Dimension × dataset role matrix** (populated from T05–T07
   empirics; each cell carries the underlying metric value).
   **D4 split into D4a/D4b per Pass 2 revision; D6 is flag-only, not
   role-bearing:**

   | Dimension | sc2egset | aoestats | aoe2companion | Comparability |
   |---|---|---|---|---|
   | D1 Sample-scale (cleaned rows) | [from T05 CONSORT] | [from T06 CONSORT] | [from T07 CONSORT ~30.5M] | yes (all 3 counts derived from same schema shape) |
   | D2 Skill-signal (ICC point estimate + verdict) | [from sc2egset icc.json: 0.046 INCONCLUSIVE — passes F1+F2] | [from aoestats 01_05_05_icc_results.json: 0.027 — check F2] | [from aoe2companion 01_05_05_icc.json: 0.003 FALSIFIED — fails F1 AND F2] | yes (all 3 measured on pre-game reference windows) |
   | D3 Temporal coverage (months with ≥100 cleaned rows) | [from T05 data_dictionary, density-filtered SQL] | [from T06 data_dictionary] | [from T07 data_dictionary, ~60+ months] | yes once density floor applied uniformly |
   | D4a Identity rename-stability (Branch per I2) | Branch (iii) — SUPPLEMENTARY | Branch (v) — SUPPLEMENTARY | Branch (i) — **PRIMARY** | yes (all 3 follow I2 extended procedure) |
   | D4b Identity within-scope rigor (rates < 15%) | 12%/30.6% within-region — **co-PRIMARY** | Branch (v) unmeasurable — SUPPLEMENTARY | 2.57%/3.55% — **co-PRIMARY** | yes (rate thresholds applied uniformly; orthogonal to D4a) |
   | D5 Patch resolution | N/A (tournament) | patch_id binding — **PRIMARY** | N/A (no patch metadata) | no (aoestats is the only PRIMARY candidate) |
   | D6 Controlled-asymmetry flag (I8 variable, **NOT** role-bearing) | in-game events parseable | N/A | N/A | no (flag only; not counted toward PRIMARY-role tally) |

   **§3 — Role assignment with evidence citations** (for each cell
   labelled PRIMARY/SUPPLEMENTARY in the header matrix — §Problem
   Statement line ~94 — cite the metric value + artifact path that
   justifies the label. State the falsifier for each PRIMARY label
   referring back to spec §3 decision rule):
   - D1 PRIMARY aoe2companion — justify via sample-scale ratio
     aoe2companion:sc2egset ≥ 10× and aoe2companion:aoestats ≥ 10×;
     falsifier: if another dataset exceeds 10× the current PRIMARY.
   - D2 PRIMARY sc2egset — apply F1 (ICC ≥ 0.01) + F2 (verdict NOT
     FALSIFIED): sc2egset 0.046 INCONCLUSIVE passes both; aoestats
     0.027 check F2 per INVARIANTS.md §5 row; aoe2companion 0.003
     fails F1 AND F2. Falsifier: if a SUPPLEMENTARY dataset's ICC
     rises above sc2egset's AND its verdict transitions out of
     FALSIFIED/INCONCLUSIVE conflict.
   - D3 PRIMARY aoe2companion — month count ≥ 2× the median across
     candidates, SQL-defined with ≥ 100 cleaned rows/month density
     floor (uniformly applied); sc2egset tournament-sparse months
     below density floor are excluded; falsifier: if density-filtered
     SQL shows another dataset exceeds aoe2companion's count.
   - D4a PRIMARY aoe2companion — sole Branch (i) rename-stable
     dataset. sc2egset (Branch iii) and aoestats (Branch v) are
     SUPPLEMENTARY. Falsifier: if aoestats transitions to Branch (i)
     via BACKLOG F1, role flips to co-PRIMARY.
   - D4b co-PRIMARY sc2egset + aoe2companion — both have measured
     rates < 15% (sc2egset within-region; aoe2companion globally).
     aoestats Branch (v) structurally-forced cannot measure rates
     within dataset. This co-PRIMARY is **orthogonal to D4a** and
     compatible: sc2egset wins on within-region rigor;
     aoe2companion wins on rename-stability.
   - D5 PRIMARY aoestats — sole dataset with patch_id binding.
   - D6 asymmetry flag — NOT a role assignment; documented for I8
     transparency only.

   **§4 — Cross-dataset I8 compliance enumeration**. Concrete list of
   **which cross-checks are permitted** (e.g., "distribution of
   cleaned rows per month comparable sc2egset ↔ aoe2companion under
   D1+D3 pair") and **which are blocked** (e.g., "per-slot win rates
   across all three — BLOCKED pending aoestats F1+W4"). At least 6
   concrete cross-check items listed.

   **§5 — Phase 02 kickoff readiness**: explicit per-dataset
   declaration that Phase 02 planning can commence, with scope
   narrowing per §1's Phase 02 column.

**Verification:**
- File exists, §1–§5 all populated.
- §1 table has 3 rows with verdict + flip-predicate + GO/GO-NARROW.
- §2 dimension matrix has 3 datasets × 6 dimensions = 18 cells each
  with metric value (not just label).
- §3 cites six role-assignment decisions each with evidence + falsifier.
- §4 lists ≥6 cross-check items with permitted/blocked status.
- All metric values in §2 traceable to T05–T07 artifact paths.

**File scope:**
- `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md` (Create)

**Read scope:**
- three `modeling_readiness_<dataset>.md`, `data_dictionary_<dataset>.{csv,md}`,
  `data_quality_report_<dataset>.md`, `risk_register_<dataset>.{csv,md}` from T05–T07
- `reports/specs/01_06_readiness_criteria.md` §3 (role-assignment criteria D1–D6)
- relevant 01_05 ICC artifacts for the D2 skill-signal cells

---

### T09 — PIPELINE_SECTION_STATUS + PHASE_STATUS transitions (all 3 datasets)

**Objective:** Advance each dataset's pipeline-section and phase status
files to reflect Phase 01 completion.

**Instructions:**
1. For each dataset, update
   `reports/PIPELINE_SECTION_STATUS.yaml`: set `01_06` status to
   `complete` (aoe2companion also has `01_05_09` retroactively added —
   ensure that pipeline section remains `complete` since its step is
   now `complete` via T07).
2. For each dataset, update `reports/PHASE_STATUS.yaml`: set Phase 01
   status to `complete`.
3. Verify derivation chain: STEP_STATUS (all 01_06 steps complete) →
   PIPELINE_SECTION (01_06 complete) → PHASE (Phase 01 complete).

**Verification:**
- All 3 `PIPELINE_SECTION_STATUS.yaml` show `01_06: complete`.
- All 3 `PHASE_STATUS.yaml` show Phase 01 = `complete`.
- `python -c "import yaml; [yaml.safe_load(open(p)) for p in [list-of-six-files]]"` parses cleanly.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/PIPELINE_SECTION_STATUS.yaml` (Update)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/PHASE_STATUS.yaml` (Update)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/PIPELINE_SECTION_STATUS.yaml` (Update)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/PHASE_STATUS.yaml` (Update)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/PIPELINE_SECTION_STATUS.yaml` (Update)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/PHASE_STATUS.yaml` (Update)

**Read scope:**
- the three updated `STEP_STATUS.yaml` from T05–T07

---

### T10 — INVARIANTS.md §5 refresh (conditional; audit log always written)

**Objective:** If 01_06 surfaced any invariant-status transition (e.g.,
aoe2companion identity reconciliation might flip I2 from PARTIAL to
HOLDS), update the affected `INVARIANTS.md §5` row. Always write an
audit-log file documenting what was checked and what transitioned (or
didn't) so the task is observable in the PR diff even when no data
edits occur.

**Instructions:**
1. Read each dataset's `modeling_readiness` and `risk_register`
   artifacts for explicit invariant-status transition language.
2. For each dataset's INVARIANTS.md, update §5 rows only where 01_06
   artifacts explicitly ratify a transition.
3. Write `.github/tmp/01_06/t10_invariant_refresh.log` with per-dataset
   rows: `<dataset> | <invariant_id> | <status_before> | <status_after> | <evidence_artifact>`.
   At minimum one row per dataset × I1–I10 = 30 rows stating "no
   transition" where no edit was made.

**Verification:**
- For any INVARIANTS.md edit, row-level diff matches 01_06 finding.
- `.github/tmp/01_06/t10_invariant_refresh.log` exists with 30 rows
  (3 datasets × 10 invariants) documenting before/after status.

**File scope:**
- 0–3 of `{sc2egset, aoestats, aoe2companion}/reports/INVARIANTS.md` (Update, conditional)
- `.github/tmp/01_06/t10_invariant_refresh.log` (Create)

---

### T11 — Research log entries (3 per-dataset + 1 CROSS)

**Objective:** Record 01_06 execution and findings in each dataset's
research log plus one CROSS entry in the project-level log.

**Instructions:**
1. Append a dated entry to each dataset's `reports/research_log.md`
   with: category A, branch `feat/phase01-decision-gates-01-06`,
   scope (Phase 01 gate closure), key findings (verdict, BLOCKER
   count, risk register severity distribution), artifact paths,
   invariants touched, thesis mapping (§4.3 unblock).
2. Append a CROSS entry to `reports/research_log.md` with: cross-
   dataset rollup path, role-assignment decision, Phase 02 readiness
   declaration per dataset.

**Verification:**
- 4 entries dated 2026-04-19 (or today).
- Each per-dataset entry references 01_06_01..01_06_04 artifact
  paths explicitly.
- CROSS entry references the rollup path and all three
  `modeling_readiness_<dataset>.md`.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` (Update)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md` (Update)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md` (Update)
- `reports/research_log.md` (Update — CROSS entry)

---

### T12 — Thesis + planning state updates

**Objective:** Resolve the `01_06 deferred` flags currently sitting in
thesis §4.1 / §4.1.3 / §4.1.4 Notes cells (not a phantom §4.3 row — per
reviewer-adversarial BLOCKER 1, §4.3 does not exist in the current
WRITING_STATUS.md layout). Add a BACKLOG F1 cross-reference noting that
01_06 registered it as the READY_CONDITIONAL predicate for aoestats.

**Instructions:**
1. Read `thesis/WRITING_STATUS.md` lines 64–73 (Chapter 4 rows). The
   three rows that this task appends to are:
   - §4.1 (line 64) — row currently carries explicit 01_06 deferral
     language.
   - §4.1.3 (line 66) — row references reference-window asymmetry;
     01_06 adjudication is the plan's inference (not a verbatim quote).
   - §4.1.4 (line 67) — row carries population-scope framing; 01_06
     resolves via T08 rollup role matrix.
2. For each of the three rows, **append unconditionally** a
   `2026-04-19 (PR #TBD): 01_06 Phase 01 gate closed; see
   cross_dataset_phase01_rollup.md` clause to the Notes cell —
   regardless of whether the existing Notes text literally contains
   "01_06". Executor does not match-and-replace; they append. Do NOT
   flip the row-level status (DRAFTED stays DRAFTED — this is a Notes
   cell enrichment, not a status transition).
3. Update `thesis/WRITING_STATUS.md` "Last updated" header to
   `2026-04-19 (01_06 Phase 01 gate closure)`.
4. Update `planning/BACKLOG.md` F1 entry: add a cross-reference
   footnote noting that 01_06 registered F1 as the flip-predicate for
   aoestats READY_CONDITIONAL, with path to
   `modeling_readiness_aoestats.md`. Also note the F1+W4 coupling
   surfaced by reviewer-adversarial (F1 alone does not flip I5;
   requires W4 schema amendment).

**Verification:**
- Three §4.1.x rows carry 2026-04-19 Notes-cell append.
- None of the three rows has status changed (DRAFTED remains DRAFTED).
- "Last updated" header updated.
- BACKLOG F1 entry cites `modeling_readiness_aoestats.md` + notes
  F1+W4 coupling.
- No new `§4.3` row created.

**File scope:**
- `thesis/WRITING_STATUS.md` (Update — 3 row Notes + header)
- `planning/BACKLOG.md` (Update — F1 footnote + W4 coupling note)

---

### T13 — Inline cleanup: purge `.github/tmp/01_05/`

**Objective:** Remove six orphan pre-execution artifacts from the
landed 01_05 cycle.

**Instructions:**
1. Delete all files under `.github/tmp/01_05/`:
   - `plan_sc2egset.md`, `plan_sc2egset.critique.md`
   - `plan_aoestats.md`, `plan_aoestats.critique.md`
   - `plan_aoe2companion.md`, `plan_aoe2companion.critique.md`
2. Remove the `.github/tmp/01_05/` directory itself.

**Verification:**
- `ls .github/tmp/01_05/` returns "No such file or directory" or empty.

**File scope:**
- `.github/tmp/01_05/*` (Delete × 6)

---

### T14 — CHANGELOG entry + final verification

**Objective:** Document the PR in CHANGELOG and run final pre-commit
check.

**Instructions:**
1. Append `[Unreleased]` or new semver entry to `CHANGELOG.md`
   summarising Phase 01 closure (3 datasets), per-dataset verdicts,
   role assignment, thesis §4.3 unblock.
2. Run `source .venv/bin/activate && pre-commit run --all-files`.
3. If any hook fails, fix and re-stage.

**Verification:**
- CHANGELOG entry present.
- `pre-commit` clean.

**File scope:**
- `CHANGELOG.md` (Update)

**Read scope:**
- `.claude/rules/git-workflow.md` (version bump convention)

---

## File Manifest

| File | Action |
|------|--------|
| `reports/specs/01_06_readiness_criteria.md` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` | Update |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` | Update |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/PIPELINE_SECTION_STATUS.yaml` | Update |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/PHASE_STATUS.yaml` | Update |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md` | Update (conditional) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` | Update |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/06_decision_gates/data_dictionary_sc2egset.{csv,md}` | Create × 2 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/06_decision_gates/data_quality_report_sc2egset.md` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/06_decision_gates/risk_register_sc2egset.{csv,md}` | Create × 2 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_sc2egset.md` | Create |
| `sandbox/sc2/sc2egset/01_exploration/06_decision_gates/01_06_01_data_dictionary.py` | Create |
| `sandbox/sc2/sc2egset/01_exploration/06_decision_gates/01_06_02_data_quality_report.py` | Create |
| `sandbox/sc2/sc2egset/01_exploration/06_decision_gates/01_06_03_risk_register.py` | Create |
| `sandbox/sc2/sc2egset/01_exploration/06_decision_gates/01_06_04_modeling_readiness.py` | Create |
| *(same 11-file set for aoestats under `src/rts_predict/games/aoe2/datasets/aoestats/...` + `sandbox/aoe2/aoestats/...`)* | Create/Update |
| *(same 11-file set for aoe2companion, PLUS `01_05_09_gate_memo.{py,md}` retroactive)* | Create/Update |
| `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md` | Create |
| `reports/research_log.md` | Update |
| `thesis/WRITING_STATUS.md` | Update |
| `planning/BACKLOG.md` | Update |
| `CHANGELOG.md` | Update |
| `.github/tmp/01_05/*.md` | Delete × 6 |
| `planning/current_plan.md` | Update (provenance at PR wrap-up) |
| `planning/current_plan.critique.md` | Create (reviewer-adversarial, pre-execution) |

Approximate total: ~45 file touches (3 × ~11 per-dataset + 7 shared +
6 deletions + 2 retroactive aoe2companion memo).

## Gate Condition

- All three `PHASE_STATUS.yaml` files show Phase 01 = `complete`.
- All three `PIPELINE_SECTION_STATUS.yaml` files show 01_06 = `complete`.
- aoe2companion `PIPELINE_SECTION_STATUS.yaml` shows 01_05 still
  `complete` with 01_05_09 retroactively added as a `complete` step.
- Four §6.1 deliverables per dataset exist on disk × 3 datasets = 12
  artifacts present.
- Cross-dataset rollup exists at
  `reports/artifacts/01_exploration/06_decision_gates/cross_dataset_phase01_rollup.md`.
- Three per-dataset research_log entries + one CROSS entry dated
  2026-04-19 (or today).
- `thesis/WRITING_STATUS.md` §4.1 / §4.1.3 / §4.1.4 Notes cells carry
  `2026-04-19 (PR #TBD): 01_06 gate closed` append; no row-level status
  transitions.
- `planning/BACKLOG.md` F1 entry cites
  `modeling_readiness_aoestats.md` and notes the F1+W4 coupling.
- `.github/tmp/01_05/` directory empty or removed.
- CHANGELOG entry present.
- Pre-commit hooks clean.
- Adversarial review completed; `planning/current_plan.critique.md`
  present on disk (parent responsibility, pre-T01).
- PR opened.

## Out of scope

- **BACKLOG F1 — aoestats `canonical_slot`** — registered as
  READY_CONDITIONAL predicate in `modeling_readiness_aoestats.md`; not
  resolved here. Separate Cat A PR (`feat/aoestats-canonical-slot`)
  triggers a spec v1.1.0 bump.
- **BACKLOG F4 — narrative-drift checker** — unrelated Cat C chore.
- **Phase 02 step definitions in any ROADMAP.** Phase 02 placeholders
  in ROADMAP tails remain as-is.
- **Thesis §4.3 drafting** — only the status flip to DRAFTABLE. Actual
  prose drafting is a Category F PR that consumes 01_06 artifacts.
- **Thesis §4.4.1–3 and Chapters 5–6** — still BLOCKED on Phase
  02–04 artifacts; not touched here.
- **Cross-dataset spec amendments to `01_05_preregistration.md`.** The
  v1.0.5 spec is locked; 01_06 does not amend it.
- **Re-running any 01_01–01_05 analysis** or regenerating any Phase
  06 interface CSV.
- **New bibtex entries.** 01_06 leans on existing methodology sources
  only.

## Open questions

- **Q1:** Whether any dataset's INVARIANTS.md §5 PARTIAL row actually
  flips during 01_06 execution. Resolved at execution time (T10);
  expected no-op.
- **Q2:** Whether the cross-dataset rollup's role-assignment
  justification survives thesis supervisor review. Resolved at Pass 2
  (not part of this PR).
- **Q3:** Whether aoestats READY_CONDITIONAL verdict language needs
  supervisor sign-off before BACKLOG F1 is claimed. Resolved: no —
  01_06 registers the predicate; F1 is scheduled independently.
- **Q4:** Whether `[CRISP-ML(Q)]` needs a bibtex entry added to
  `thesis/references.bib` for §4.3 drafting. Resolved: deferred to
  §4.3 drafting PR; this PR does not touch `references.bib`.
