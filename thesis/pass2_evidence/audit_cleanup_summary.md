# Audit cleanup summary — thesis/audit-methodology-lineage-cleanup

## T01 — Preflight and repo safety baseline

### Branch state

- Branch: `thesis/audit-methodology-lineage-cleanup`
- HEAD commit: `3498ded2` — `docs(planning): instantiate thesis audit cleanup execution plan`
- Forked from: `master` @ `d0b2a8a6` — `Merge pull request #206 from tomaszpionka/chore/cross-research-log-refresh`
- Working tree: **clean** — `git status --short` returned empty output
- Date: 2026-04-26

### Repo conventions and commands

- **Test command:** `source .venv/bin/activate && poetry run pytest tests/ -v --cov=rts_predict --cov-report=term-missing`
  (coverage source is `src/rts_predict` as set in `pyproject.toml`; `fail_under = 95`)
- **Lint:** `source .venv/bin/activate && poetry run ruff check src/ tests/`
  (also fires automatically via pre-commit hook on every `git commit`)
- **Type check:** `source .venv/bin/activate && poetry run mypy src/rts_predict/`
  (also fires automatically via pre-commit hook on every `git commit`)
- **Notebook execution:** `jupyter nbconvert --to notebook --execute --inplace <notebook.ipynb>`
  Timeout: 600 seconds per fresh-kernel execution (from `sandbox/notebook_config.toml` `[execution] timeout_seconds = 600`)
- **Jupytext pairing:** Configuration lives at `sandbox/jupytext.toml` (per memory: NOT repo root).
  Format: `formats = "ipynb,py:percent"`. Volatile metadata stripped; only `kernelspec` and `jupytext` keys retained.
  Both `.ipynb` and `.py` must be staged together on every commit (author responsibility — jupytext pre-commit hook enforces content sync but not dual-staging).
- **Version single-source:** `pyproject.toml` only — no `__version__` in any `__init__.py`
  (per memory `feedback_version_tracking.md`)
- **Notebook cell cap:** 50 lines per cell (`sandbox/notebook_config.toml` `[cells] max_lines = 50`)
- **Report artifacts destination:** `src/rts_predict/<game>/reports/<dataset>/artifacts/` — always the `artifacts/` subdirectory; use `get_reports_dir("sc2", "sc2egset") / "artifacts"` from `rts_predict.common.notebook_utils`

### Branch-prefix operational verification (WARNING-3/8 fix)

#### (a) GitHub Actions workflows — `.github/workflows/*.yml`

**Status: N/A — directory absent.**

`ls .github/workflows/` returns `No such file or directory`. The `.github/workflows/` directory does not exist on either `master` or the current `thesis/` branch. There are no CI workflow YAML files that could contain branch-name filters. The `thesis/` prefix cannot break any workflow trigger.

#### (b) Pre-commit config — `.pre-commit-config.yaml`

**Status: CLEAR — no branch-name filters present.**

Inspected `.pre-commit-config.yaml` in full (91 lines). All hooks are triggered by:

- `files:` patterns matching staged file paths (`.py` extensions, `^planning/`, `STEP_STATUS`/`PIPELINE_SECTION_STATUS`/`PHASE_STATUS` YAML filenames, `^\.claude/rules/`, `^sandbox/.*\.(ipynb|py)$`, `^sandbox/.+/01_exploration/05_temporal_panel_eda/.+\.py$`)
- `types: [python]` for the mypy hook
- None of the hooks inspect the current branch name

The `thesis/` branch prefix has no effect on which pre-commit hooks fire or how they behave. All hooks verified clean.

#### (c) PR template — `.github/pull_request_template.md`

**Status: CLEAR — no branch-prefix placeholder substitution.**

The template (15 lines) contains only three sections: `## Summary`, `## Motivation`, and `## Test plan`, plus HTML comments and a footer. No `{{branch}}`, `%BRANCH%`, or any other branch-name placeholder is present. The template is static and the `thesis/` prefix cannot break any substitution. The PR body must be authored by the agent per the `git-workflow.md` format rules.

#### (d) Version-bump classification for `thesis/` prefix

**Chosen classification: MINOR**

Rationale: The `.claude/rules/git-workflow.md` version-bump table maps:

- `feat/`, `refactor/`, `docs/` → **minor**
- `fix/`, `test/`, `chore/` → **patch**

The `thesis/` prefix is not enumerated. The work on this branch is thesis chapter text, audit evidence documents, and supporting annotation — all documentation/writing artefacts with no code or data logic changes. This is closest in spirit and substance to `docs/`, which maps to **minor**. Recording: `thesis/` branches → **minor** version bump at PR wrap-up.

### Out-of-scope reminders for downstream tasks

- **T02 critique gate:** Already satisfied. `planning/current_plan.critique.md` and `planning/current_plan.critique_resolution.md` both exist on disk. BLOCKER-1 sub-check 6 was verified PASS by reviewer-adversarial round-1 follow-up. No re-verification needed in T02.
- **Raw data:** `src/**/data/*/raw/**` is deny-listed by repo permissions. No task in this branch touches raw data.
- **Existing pass2_evidence files:** The five frozen Pass-2-handoff files (`README.md`, `sec_4_1_crosswalk.md`, `sec_4_1_halt_log.md`, `sec_4_2_crosswalk.md`, `sec_4_2_halt_log.md`) must not be modified by any downstream task unless the task explicitly calls for it.
- **Planning files:** `planning/current_plan.md`, `planning/current_plan.critique.md`, `planning/current_plan.critique_resolution.md` must not be modified during execution.
- **Commit batching:** `audit_cleanup_summary.md` was left uncommitted at end of T01 per parent instruction. The parent will decide whether to batch the T01 commit with T02+ work.

## T02 — Plan adversarial review

**Date:** 2026-04-26

### Review cycle status

T02 constitutes **Round 1 of 3** adversarial cycles for this PR, per plan Assumption (D):
"T02 (plan critique gate), T10 (consolidated mid-PR adversarial gate), T19 (final PR adversarial gate) = 3 total; BLOCKER-5 resolution collapsed the original 5 per-task dispatches into this 3-round structure."

### Source documents

- Critique source: `planning/current_plan.critique.md`
- Resolution log: `planning/current_plan.critique_resolution.md`

### Findings count

| Type | Count |
|------|-------|
| BLOCKERs | 5 (BLOCKER-1 through BLOCKER-5) |
| WARNINGs | 5 (WARNING-1 through WARNING-5) |
| NOTEs | 4 (NOTE-1 through NOTE-4) |
| BLOCKER-1 sub-check 6 follow-up row | 1 |
| **Total rows** | **15** |

### Resolution status

- **BLOCKERs 1–5:** ALL RESOLVED in plan revision v2 (2026-04-26).
- **WARNINGs 1–5:** ALL RESOLVED in plan revision v2 (2026-04-26).
- **NOTEs 1–4:** ALL RESOLVED (NOTE-4 acknowledged as strength; no action required) in plan revision v2 (2026-04-26).
- **BLOCKER-1 sub-check 6:** RESOLVED in plan revision v3 (2026-04-26) — added Step 01_06_02 data-quality-report generator, artifact, ROADMAP, research_log, and STEP_STATUS entries to conditional⁶ manifest; extended conditional⁶ footnote and T16 14A.1 trigger to cover the generated data-quality-report repair path.

### Verification status

BLOCKER-1 sub-check 6 was verified **PASS** by reviewer-adversarial in two independent confirmation rounds (v3 follow-up). All other findings were verified PASS as part of the v2 patch acceptance by reviewer-adversarial in Round 1.

### Six attack dimensions — location in critique and plan response

| Dimension | Where attacked in critique | Plan response |
|-----------|---------------------------|---------------|
| (i) ROADMAP→notebook→artifact→research_log→thesis lineage | BLOCKER-3 (lines 51–71): manifest gap between T16 14A.1 findings and the generated data-dictionary lineage chain | Added conditional⁶ footnote with explicit manifest rows for all six data-dictionary / Step 01_06_01 files; T07/T16 HARD VERIFICATION RULE added |
| (ii) AoE2 ranked-ladder / quickplay / matchmaking semantics | BLOCKER-1 (lines 12–30): on-disk `qp_rm_1v1` label contradicts "ranked ladder" framing in Q2, `data_quality_report_aoe2companion.md`, and Chapters 4.1.3/4.2.3 | Q2 rewritten to confirm on-disk evidence; T05 4.2 adds fallback "default to quickplay/matchmaking on ambiguity"; T05 4.3 terminology ladder explicitly maps ID 18 / `qp_rm_1v1` |
| (iii) Generated-artifact protection | BLOCKER-3 (lines 56–60): T16 14A.1 names a generated notebook as work-output but manifest had no path from the finding to authorised file touch; Strengths §2 (lines 201–202) confirms G4 correctly reflected in T07 step 5 | Conditional⁶ manifest rows; manifest-bound HARD VERIFICATION RULE; sub-check 6 extended conditional⁶ to cover data-quality-report generator |
| (iv) Methodology spec change handling (no Cat-C demotion) | BLOCKER-2 (lines 33–47): LOCKED specs CROSS-02-00 v3 and CROSS-02-01 v1 have §7 amendment protocol not invoked by T15/T16 | T15/T16 instructions insert §7 protocol invocation (version bump, amendment-log row, planner-science + reviewer-adversarial co-signoff, same-commit discipline); Gate Condition Specs section added |
| (v) Temporal-leakage and stale-artifact risk | WARNING-2 (lines 127–140): no standard notebook-execution command leaves regenerated artifacts unaudited; NOTE-1 (lines 181–183): stale marking mechanism unspecified, risking artifact renaming that breaks cross-references | T07 step 1 cites explicit nbconvert command + 600 s timeout; NOTE-1 fix: stale marking lives in `notebook_regeneration_manifest.md` only — filenames never mutated |
| (vi) Safe incorporation of prior Pre-Phase-02 Readiness plan items | Strengths §5 (lines 206–207): unsafe items from prior plan enumerated in Out-of-scope; WARNING-5 (lines 167–177): wildcard manifest rows too coarse for "no executor task may touch a file absent from the manifest" | Wildcard rows tightened with explicit "manifest is the authoritative bound" wording; T07 HARD VERIFICATION RULE added; Out-of-scope retains prohibition on items from prior plan not sanctioned for this PR |

---

## Mid-PR adversarial gate (T10, Round 2 of 3)

**Date:** 2026-04-26
**Source critique:** consolidated review by `@reviewer-adversarial` (Round 2 of 3).
**Inputs reviewed:** `aoe2_ladder_provenance_audit.md` (T05); `notebook_regeneration_manifest.md` (T06/T07/T08 lifecycle); regenerated `data_quality_report_aoe2companion.md` (T07 + T08 follow-up); `cross_dataset_comparability_matrix.md` (T09 + grain-disambiguation patch); `methodology_risk_register.md` (T10 Stage 1 — 23 risks); `cleanup_flag_ledger.md` (T04 with re-routed task assignments); `reports/research_log.md` lines 17–39 (T09 CROSS entry).
**Branch HEAD at review:** `64e08553` + uncommitted T10 risk register on working tree.

### Verdict

**READY-FOR-T11-WITH-REVISIONS** — Round 2 consumed; cap not exceeded; T11 may proceed only after the two BLOCKERs below are resolved.

### Per-dimension verdicts

| Attack dimension | Verdict | Source dimension |
|------------------|---------|------------------|
| 1. T05 AoE2 provenance strength | SOUND (with 2 WARNINGs on shorthand echoes and aoestats artifact asymmetry) | T05 |
| 2. T07/T08 generated-artifact repair completeness | SOUND (zero remnants confirmed; lifecycle discipline correctly enforced) | T07/T08 |
| 3. T09 cross-dataset framing | SOUND (5-axis bounded-comparability statement adequate) | T09 |
| 4. T09 grain-disambiguation sufficiency | AT RISK (2 WARNINGs on grain visual differentiator + rows-per-match annotation) | T09 |
| 5. Methodology risk register completeness | AT RISK — **BLOCKER-A**: 3 missing examiner-facing risks | T10 |
| 6. Should any Chapter 4 rewrite remain blocked? | ADEQUATE-WITH-CAVEAT — **BLOCKER-B**: RISK-08 routing inconsistency | T10 |
| 7. Spec-related risk routing to T15/T16 | SOUND (no spec-mutation concerns require T15/T16 before T11; BLOCKER-2 §7 reviewer-adversarial co-signoff satisfied by this gate) | T15/T16 |
| 8. 3-round adversarial cap respect | SOUND (Round 2 collapses T05 / T15 / T16 14A.2 / 14A.3 / T06 dispatches symmetrically; cap NOT exceeded) | BLOCKER-5 fix |

### BLOCKERs (must resolve before T11 begins)

1. **BLOCKER-A — three missing examiner-facing risks in `methodology_risk_register.md`:**
   - **RISK-24 (proposed):** Focal/opponent slot asymmetry across three table shapes (SC2EGSet 2-row-per-match; aoestats 1-row-per-match with `p0_*`/`p1_*` columns; aoe2companion 2-row-per-match) — symmetric feature construction must be operationalized identically; Phase 02 contract must guarantee this. **Severity:** major. **Blocking-before-T11:** YES (T11 §4.2 / §4.2.3 prose). Routing: T11 -> T16.
   - **RISK-25 (proposed):** AoE2 civ-pair feature-engineering cardinality (1,225 ordered pairs) — Chapter 1 RQ3 hypothesis must hedge feature-space-cardinality claim against cold-start sparseness. **Severity:** minor. **Blocking-before-T11:** NO. Routing: T12 -> T16.
   - **RISK-26 (proposed):** SC2 Random-race semantics — focal race for Random-pickers is `Random` at pre-game time, not the eventual race; affects 555 replays. **Severity:** minor. **Blocking-before-T11:** conditional (yes if T11 §4.1.1 / §4.2.3 enumerates race feature engineering; no otherwise). Routing: T11 (conditional).
   **Required action:** add three risk register entries; rerun a brief sanity check; record the addition.

2. **BLOCKER-B — RISK-08 routing inconsistency in `methodology_risk_register.md`:**
   RISK-08 is severity=blocker but `Blocking-before-T11=NO` with rationale that it gates Phase 02 implementation, NOT Chapter 4 prose. This is contradicted by RISK-08's own "Affected thesis sections" list which includes §4.2.3 line 303 (workflow-leakage at `.claude/scientific-invariants.md:86`) and routing line "T16 (Phase 02 feature implementation guard) -> T11 (prose repair for §4.2.3 workflow-leakage)". Either the §4.2.3 prose work is in T11 scope (so blocking=YES) or it should be removed from RISK-08 and routed elsewhere (T18 workflow-leakage cleanup) so RISK-08 stays cleanly Phase-02-only.
   **Required action:** pick one of (a) flip blocking-before-T11=YES; or (b) move §4.2.3 prose repair out of RISK-08 wording recommendation and route separately. Document the decision.

### WARNINGs (optional mitigations within T11 instructions)

1. **WARNING-1** (Dimension 1): T11 read scope must include explicit instruction not to echo `aoe2companion INVARIANTS.md §2` shorthand `rm_1v1 analytical scope` without the `(ID 6 + ID 18)` qualifier.
2. **WARNING-2** (Dimension 1): aoestats `data_quality_report_aoestats.md` R02 "Restrict to ranked 1v1 ladder" remains uncorrected; T11 must apply prose hedge per `aoe2_ladder_provenance_audit.md` §8 step 4. Optionally raise as a separate risk register entry.
3. **WARNING-3** (Dimension 4): Matrix Population row uses bold for post-cleaning numbers but not for `leaderboard_raw` activity counts — T11 must label every count cell with explicit grain when transcribing into Tabela 4.4a/b/4.5.
4. **WARNING-4** (Dimension 4): Matrix Unit-of-observation row reports SC2EGSet "(44,418 rows)" and aoe2companion "(61,062,392 rows)" but aoestats has no parenthetical (1-row-per-match). T11 must annotate rows-per-match explicitly when placing these counts in adjacent table cells.

### NOTEs

1. **NOTE-1** (Dimension 2): `STEP_STATUS.yaml` schema has no `notes` field; T08 used a YAML comment workaround following Step 01_05_09 precedent. Acceptable but non-machine-readable. Tracked for T17 if a schema bump is later considered.
2. **NOTE-2** (Dimension 3): Bounded-comparability statement for §6.3 is correctly deferred (RISK-06 covers this). Track via WRITING_STATUS.md so the §6.3 obligation does not get lost when Chapter 6 begins.

### Cap accounting

- **Round 1 (plan critique gate):** consumed (2026-04-26, `current_plan.critique.md`).
- **Round 2 (consolidated mid-PR gate):** consumed (this section). Collapses T05 / T15 / T16 14A.2 / T16 14A.3 / T10 risk register / T06 regen plan dispatches per BLOCKER-5 fix. Symmetric and within scope.
- **Round 3 (final PR gate):** reserved for T19.
- **Cap exceedance:** NO.

### T11 readiness gate

**T11 is BLOCKED until BLOCKER-A and BLOCKER-B are resolved.** WARNINGs may be addressed within T11 dispatch instructions; NOTEs flow to T17 / WRITING_STATUS.md tracking. No items are routed to T15 / T16 before T11 begins.

### BLOCKER resolution status (post-2026-04-26 patch)

| BLOCKER | Action taken | File(s) changed | Verification routed to |
|---------|-------------|-----------------|------------------------|
| BLOCKER-A — three missing examiner-facing risks | RISK-24 (focal/opponent slot asymmetry across three dataset table shapes; severity major; blocking-before-T11 YES; routing T11 → T16); RISK-25 (AoE2 civ-pair feature-engineering cardinality; severity minor; blocking-before-T11 NO; routing T12 → T16); RISK-26 (SC2 Random race semantics; severity minor; blocking-before-T11 YES with conditional note — register schema supports yes/no only and the conditional clause is captured inline; routing T11 → T16) added to `methodology_risk_register.md` after RISK-23. Summary tables (severity, blocking, task routing, one-line severity) updated to reflect total count 23 → 26. T11 dispatch warnings subsection added to carry the four Round 2 WARNINGs into the T11 dispatch instructions. | `methodology_risk_register.md` | targeted blocker-resolution check (BLOCKER-A sub-check) before T11 dispatch |
| BLOCKER-B — RISK-08 routing inconsistency | RISK-08 `Blocking before Chapter 4 rewrite` flipped from `no` to `yes`. `Downstream task responsible` rewritten to make T11 the primary owner of the §4.2.3 prose repair (workflow-leakage F-072 academic-language replacement of `.claude/scientific-invariants.md:86`) with T16 owning the Phase 02 implementation guard. Explicit clause added: "T18 may perform final cleanup but must not be the first stage to notice or own §4.2.3 prose work." Summary "Counts by blocking-before-T11" updated (blocking 6 → 9 includes RISK-08 / RISK-24 / RISK-26; non-blocking 17 → 17 because RISK-25 added as non-blocking offsets RISK-08 transition). | `methodology_risk_register.md` | targeted blocker-resolution check (BLOCKER-B sub-check) before T11 dispatch |

**Round 2 status:** consumed. The 2026-04-26 patch is a targeted resolution of Round 2 BLOCKERs; it does NOT consume a new adversarial round. The 3-round symmetric cap remains respected (Round 1 plan critique = consumed; Round 2 mid-PR gate = consumed; Round 3 final PR gate = reserved for T19).

**T11 readiness:** still **BLOCKED** until a targeted blocker-resolution check (analogous to the BLOCKER-1 sub-check 6 follow-up earlier in this PR) returns PASS for both BLOCKER-A (RISK-24/25/26 well-grounded and routed correctly) and BLOCKER-B (RISK-08 routing internally consistent, prose ownership unambiguous). After PASS, T11 dispatch may proceed with the four WARNINGs carried into its instructions and NOTEs tracked separately.

---

## T19 — Final review gates (Round 3 of 3, 2026-04-27)

T19 ran the final review gates after T18. Mechanical checks passed clean (35 files / 18 commits, 64 physical chapter flags preserved, 0 workflow leakage in chapter prose, 0 stale-ranked-ladder claims, 560/560 pytest passing, 22 spec-version refs all current/historical, manifest 0 stale / 0 pending). Detailed gate report: `thesis/pass2_evidence/reviewer_gate_report.md`.

**Both reviewers converged on PASS-WITH-NOTES.** 0 BLOCKERs. 3 WARNINGs + 9 NOTEs total.

### WARNINGs requiring T20 attention

| ID | File / Section | Required action |
|---|---|---|
| WARNING-1 | `thesis/chapters/04_data_and_methodology.md:206` | Replace "populację ladderową (AoE2)" with "publiczne populacje 1v1 Random Map (AoE2)" or analogous wording from §4.1.2.0 line 79 |
| WARNING-2 | Ch 4 §4.3.2 placeholder or §4.4 stub | Add GATE-14A6 acknowledgement hedge so examiner reading Ch 4 sees the deferral |
| WARNING-3 | Ch 4 §4.4.5 ~line 388 | T20 PR body highlights ICC argument analogical-use of [Gelman2007] §11–12 |

### Spec amendment classifications (T15 reviewer-deep recommendation routed to T20)

The T15 reviewer-deep non-blocker recommendation to record borderline patch-vs-minor classification calls in this audit summary is now active for T20:

- **CROSS-02-00 v3 → v3.0.1 (T15)**: classified PATCH per `02_00_feature_input_contract.md` §7. Borderline against minor: §3.3 UTC discipline added a *binding requirement* (`SET TimeZone = 'UTC'`), which could be argued to be a §5-equivalent gate addition. PATCH classification stands because: (a) no §2 column-grain commitment changed; (b) no §4 encoding rule changed; (c) no §5 gate condition added/removed at the spec-protocol level — the requirement is a §3 discipline note, not a §5 gate. T10 Round 2 consolidated signoff covers this per Assumption (D) and BLOCKER-2 resolution.
- **CROSS-02-01 v1 → v1.0.1 (T15)**: classified PATCH per `02_01_leakage_audit_protocol.md` §7. Borderline against minor: §4 stale-artifact discipline added an authoritative-reference invariant (`notebook_regeneration_manifest.md` is the stale/current authority), which could be argued to be a §2-equivalent audit-dimension addition. PATCH classification stands because: (a) no §2 audit dimension was added; (b) no §3 schema field changed; (c) no §5 gate condition changed; (d) §4 enforcement is convention-based per §5 ("no CI check, pre-commit hook, or gate script"). The §3 JSON-schema literal `"CROSS-02-01-v1"` is intentionally retained at the patch increment per §192 stability convention (patches do NOT change artifact-schema literal values, because doing so would invalidate `confirmed_intact` lineage of pre-existing audit artifacts produced under the original v1 schema).

### Adversarial cap accounting

- Round 1 (plan critique) — consumed 2026-04-26
- Round 2 (T10 mid-PR gate, including the BLOCKER-A/B resolution patch) — consumed 2026-04-26
- Round 3 (T19 final PR gate) — consumed 2026-04-27

3 of 3 rounds consumed; symmetric cap respected. No further reviewer-adversarial dispatch on this PR.

**T20 readiness:** YES — CONDITIONAL on (a) WARNING-1 + WARNING-2 mechanical fixes (Ch 4 wording residue + GATE-14A6 visibility) and (b) T20 PR body enumeration of flag priority classes, GATE-14A6 status, §6.3 deferral, §4.4.6 redactional routing, §4.4.5 ICC analogical-use, and the spec amendment classifications recorded above.

### Post-T19 warning-resolution micro-pass

**Date:** 2026-05-04

A narrow T18-style mechanical consistency micro-pass was executed before T20 PR-body draft to clear the two T19 Chapter 4 mechanical warnings (WARNING-1 and WARNING-2). The micro-pass touched only `thesis/chapters/04_data_and_methodology.md` plus the two T19 report files (`reviewer_gate_report.md` and this summary). No notebooks, generated artifacts, ROADMAPs, research_logs, STEP_STATUS files, specs, schemas, references.bib, raw data, REVIEW_QUEUE.md, or WRITING_STATUS.md were touched.

- **WARNING-1 — RESOLVED.** §4.1.3 closing rationale (Chapter 4 line 206) now reads `na publiczne populacje 1v1 Random Map (AoE2) i odwrotnie` instead of `na populację ladderową (AoE2) i odwrotnie`. The replacement mirrors the conservative wording already established at §4.1.2.0 line 79 and matches the Tier-4 / mixed-mode framing used throughout §4.1.3 / §4.1.4 / Tabela 4.4a / Tabela 4.5.
- **WARNING-2 — RESOLVED.** §4.3.2 (`SC2-specific in-game features`) now contains a visible-prose paragraph headed `**Status walidacji semantycznej strumienia tracker_events_raw.**` that acknowledges the existence of the SC2 `tracker_events_raw` stream, the non-execution of dedicated semantic validation Step 01_03_05 in the current iteration, the open status of GATE-14A6, and the methodological consequence that `tracker_events_raw`-derived features are not yet treated as a fully validated model input. The hedge intentionally does not imply the validation has been completed.
- **WARNING-3 — REMAINS T20 PR-body documentation only.** No Chapter 4 edit was performed for WARNING-3; §4.4.5 ICC argument continues to use [Gelman2007] §11–12 analogically with the supporting `[REVIEW]` flag at line 208 acknowledging the analogical use. T20 PR body must mention that §4.4.5 uses the ICC argument analogically with [Gelman2007] §11–12, not as a direct empirical proof.
- **Adversarial cap unchanged.** No new reviewer-adversarial round was invoked. Round 3 (T19) remains consumed and continues to be the final adversarial round on this PR.
- **Validation results.** All five mechanical re-checks in `reviewer_gate_report.md` §7 returned the expected outcomes: WARNING-1 wording residue gone (only the line-212 negated `„ranked ladder"` mention remains); GATE-14A6 hedge visible in §4.3.2; chapter-prose workflow-leakage zero; physical chapter flag count preserved at 64 (Ch 1: 7, Ch 2: 15, Ch 3: 14, Ch 4: 28); manifest current `Status:` rows show zero `flagged_stale` and zero `regenerated_pending_log`.

---

## Plan-manifest correction (T14 pre-dispatch)

**Date:** 2026-04-26

T14 scope correction (2026-04-26): before T14 execution, the plan was amended to include `claim_evidence_matrix.md` and `cleanup_flag_ledger.md` in T14 write scope, preserving the same audit-trail discipline used in T11–T13. This is a manifest correction, not a scientific scope expansion. The two files are already authorised globally in the master File Manifest (lines 1768 and 1771); the T14 per-task `**File scope:**` block was extended to surface them explicitly for the executor, and instructions 8–9 were added to T14 to make the chapter→registry propagation contract explicit.

---

## T20 — Final PR summary

**Date:** 2026-05-04
**Branch HEAD at T20:** `c3d1b70d` (T19 final review gate + warning fixes)
**Base:** `master @ d0b2a8a6` (PR #206)
**Adversarial cap:** 3 of 3 rounds consumed (Round 1 plan critique 2026-04-26; Round 2 T10 mid-PR 2026-04-26; Round 3 T19 final 2026-04-27). No further reviewer-adversarial dispatch on this PR.

### 1. PR scope

This PR hardens the thesis methodology and evidence lineage after external scientific audit. It focuses on AoE2 data provenance, cross-dataset comparability, thesis claim discipline, and the ROADMAP → notebook → artifact → research_log → STEP_STATUS → thesis lineage chain. The PR adds 11 new Pass-2 evidence files under `thesis/pass2_evidence/`, repairs two generated `aoe2companion` artifacts via the canonical lineage, edits Chapters 1–4 prose to remove unqualified ranked-ladder claims and to install the Tier 4 / mixed-mode framing, patches two LOCKED specs (CROSS-02-00 v3→v3.0.1 and CROSS-02-01 v1→v1.0.1) and synchronises `WRITING_STATUS.md`, `REVIEW_QUEUE.md`, and `references.bib`. Total scope: 36 files changed, 19 commits, +7954 / −498 lines (per `git diff --stat master...HEAD` at HEAD `c3d1b70d`).

### 2. Files changed

Thesis prose (Chapters 1–4) and meta files:

- `thesis/chapters/01_introduction.md` (+14 lines net) — §1.1 / §1.2 / §1.3 / §1.4 four-confound + Tier 4 + mixed-mode wording (T12, T18).
- `thesis/chapters/02_theoretical_background.md` (+18 lines net) — §2.1 / §2.2 / §2.3 / §2.5 framing alignment (T13, T18).
- `thesis/chapters/03_related_work.md` (+40 lines net) — §3.4 / §3.5 bounded-gap framing + EsportsBench v9.0 / 2026-03-31 update + Elbert2025EC residualization correction (T14).
- `thesis/chapters/04_data_and_methodology.md` (+167 lines net) — §4.1.2 / §4.1.3 / §4.1.4 / §4.2.3 / §4.3.2 / §4.4.4 / §4.4.5 / §4.4.6 (T11, T18, T19 micro-pass).
- `thesis/chapters/REVIEW_QUEUE.md` (+30 lines net) — Pass-2 routing + GATE-14A6 pending item (T17).
- `thesis/WRITING_STATUS.md` (+20 lines net) — DRAFTED → REVISED transitions for §1.3 / §1.4 / §2.1 / §2.2 / §2.3 / §2.5 / §3.4 + Chapter 4 §4.4 GATE-14A6 note (T17).
- `thesis/references.bib` (+12 lines net) — bibliography fixes anchored by T14.

Pass-2 evidence (new files):

- `thesis/pass2_evidence/README.md` (new)
- `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` (new) — T05
- `thesis/pass2_evidence/audit_cleanup_summary.md` (this file) — T01–T20
- `thesis/pass2_evidence/claim_evidence_matrix.md` (new) — T03
- `thesis/pass2_evidence/cleanup_flag_ledger.md` (new) — T04, T17
- `thesis/pass2_evidence/cross_dataset_comparability_matrix.md` (new) — T09
- `thesis/pass2_evidence/dependency_lineage_audit.md` (new) — T03
- `thesis/pass2_evidence/literature_verification_log.md` (new) — T14
- `thesis/pass2_evidence/methodology_risk_register.md` (new) — T10, post-Round-2 patch
- `thesis/pass2_evidence/notebook_regeneration_manifest.md` (new) — T03, T07, T08
- `thesis/pass2_evidence/phase02_readiness_hardening.md` (new) — T16
- `thesis/pass2_evidence/reviewer_gate_report.md` (new) — T19, post-T19 micro-pass

Generator code, regenerated artifacts, ROADMAP, STEP_STATUS, research_log:

- `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_01_data_dictionary.{py,ipynb}` — T16 14A.1 `classify()` whole-word fix.
- `sandbox/aoe2/aoe2companion/01_exploration/06_decision_gates/01_06_02_data_quality_report.{py,ipynb}` — T07 R01 mixed-mode wording fix.
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` — Step 01_06_01 description + `gate.continue_predicate` extension (T16).
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/STEP_STATUS.yaml` — YAML comments appended to Step 01_06_01 (T16) and Step 01_06_02 (T08).
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoe2companion.{csv,md}` — regenerated by T16 (PRE_GAME 38→39, METADATA 16→17, TARGET 5→3).
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_quality_report_aoe2companion.md` — regenerated by T07 (R01 mixed-mode wording).
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md` — T08 Step 01_06_02 entry; T16 Step 01_06_01 entry.
- `reports/research_log.md` — cross-dataset entry (T09 row 17–39, T15 spec amendment notes).
- `reports/specs/02_00_feature_input_contract.md` — T15 v3→v3.0.1 patch (§3.3 UTC + §5.4 SC2 in-game telemetry retention).
- `reports/specs/02_01_leakage_audit_protocol.md` — T15 v1→v1.0.1 patch (§4 stale-artifact discipline + §8 sibling-spec ref bump).

Planning artefacts (working files not part of the scientific lineage):

- `planning/current_plan.md`, `planning/current_plan.critique.md`, `planning/current_plan.critique_resolution.md`, `planning/final_production_pr_plan.md`.

### 3. Notebooks changed

Two aoe2companion Phase 01 decision-gate notebooks were modified, both via the canonical `.py` + `.ipynb` jupytext-paired path:

| Notebook | Step | Change | Triggering task |
|----------|------|--------|-----------------|
| `01_06_01_data_dictionary.{py,ipynb}` | 01_06_01 | `classify()` fixed from substring `"TARGET" in n` to whole-word `re.search(r'\bTARGET\b', n)` to stop the I3-guard note `"started < target_match.started"` from triggering false-positive TARGET classification | T16 14A.1 |
| `01_06_02_data_quality_report.{py,ipynb}` | 01_06_02 | R01 description literal rewritten from `Retain 1v1 ranked ladder only` to mixed-mode wording (`rm_1v1` ID 6 + `qp_rm_1v1` ID 18 scope); generator shorthand `(rm/ew scope)` and `(rm+ew scope)` clarified to explicit `(ID 6 rm_1v1 + ID 18 qp_rm_1v1 scope)` | T07 + T08 |

Both notebooks were re-executed end-to-end via `nbconvert --to notebook --execute --inplace` with the 600 s timeout from `sandbox/notebook_config.toml`. No other notebooks were modified or re-executed in this PR.

### 4. Artifacts regenerated

| Artifact | Step | Regeneration outcome |
|----------|------|---------------------|
| `data_dictionary_aoe2companion.csv` | 01_06_01 | PRE_GAME 38→39 (`rating`/`player_history_all` reclassified from TARGET to PRE_GAME); METADATA 16→17 (`started`/`player_history_all` reclassified from TARGET to METADATA); TARGET 5→3 (only the three `won` columns remain — the correct outcome) |
| `data_dictionary_aoe2companion.md` | 01_06_01 | regenerated count summary alongside CSV (T16 14A.1 lineage closed) |
| `data_quality_report_aoe2companion.md` | 01_06_02 | R01 row reads the corrected mixed-mode wording; no `ranked ladder only` / `rm/ew` / `rm+ew` / `rankingowy ladder` remnants (T07 generator fix → T08 lineage closure) |

`notebook_regeneration_manifest.md` summary at PR HEAD: 85 `confirmed_intact` + 7 `not_yet_assessed` + 0 `flagged_stale` + 0 `regenerated_pending_log` = 92 rows. Both regenerated Steps are recorded as `confirmed_intact`. No raw data was touched (`git diff master...HEAD -- "**/data/raw/**"` is empty).

### 5. ROADMAP Steps changed

Only the aoe2companion ROADMAP was touched, and only for Step 01_06_01:

- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/ROADMAP.md` — Step 01_06_01 description amended to record the `classify()` whole-word matching requirement; `gate.continue_predicate` extended with: *"No PRE_GAME column (per YAML notes or CROSS-02-00 §5.6) is classified as TARGET in the CSV."* (T16 14A.1).

No other ROADMAP file (sc2egset, aoestats, or any other aoe2 dataset) was modified. Step 01_06_02 ROADMAP wording was inspected by T06 and confirmed not to carry the mis-label, so no edit was required.

### 6. research_log entries added/updated

| File | New entries | Triggering task |
|------|-------------|-----------------|
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md` | 2026-04-27 — `[Phase 01 / Step 01_06_01]` Data Dictionary temporal-classification repair (T16 14A.1) | T16 |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md` | 2026-04-26 — `[Phase 01 / Step 01_06_02]` Data Quality Report regeneration entry (T08), including the post-T08 R01 mixed-mode wording note | T07 + T08 |
| `reports/research_log.md` | 2026-04-26 — CROSS T09 cross-dataset comparability entry; 2026-04-26/2026-04-27 — CROSS T15 spec-amendment §7 protocol invocations for CROSS-02-00 v3→v3.0.1 and CROSS-02-01 v1→v1.0.1 | T09, T15 |

No sc2egset or aoestats `research_log.md` was modified by this PR (the cross-cutting changes were captured in the dataset-agnostic `reports/research_log.md`).

### 7. Thesis sections changed

| Chapter | Section | Change | Task |
|---------|---------|--------|------|
| 1 | §1.1 | Bounded research-gap rewording, RISK-16 hedge; [REVIEW] flag for T14 / Pass-2 verification of GarciaMendez2025 + F-036 author candidates | T12 |
| 1 | §1.2 | Civ-count `do 50` hedging | T12 |
| 1 | §1.3 | RQ3 hypothesis four-confound disclaimer; civ-pair feature-space cardinality hedge | T12 |
| 1 | §1.4 | "Charakter porównania krzyżowego" four-confound paragraph; Tier 4 / mixed-mode wording for both AoE2 corpora | T12 |
| 2 | §2.1 | Structural cleanup of cross-game framing | T13 |
| 2 | §2.2.3 | Tier 4 / mixed-mode framing + data-regime asymmetry statement | T13 |
| 2 | §2.3.2 / §2.5.4 | DLC-chronology hedge + civ-pair (do 1 225) cardinality hedge | T13 |
| 2 | §2.6.2 | ECE explicitly framed as descriptive calibration diagnostic, NOT proper scoring rule (RISK-14) | T13 |
| 3 | §3.4.1 / §3.4.3 / §3.4.4 | Bounded-gap framing; Elbert2025EC residualization correction; F-035 closed | T14 |
| 3 | §3.5 (Luki 1–3) | EsportsBench v9.0 / 2026-03-31 update; F-037 closed; F-036 + F-038 retained for Pass-2 | T14 |
| 4 | §4.1.2.0 | Mixed-mode wording for both AoE2 corpora (CX-12) | T11 |
| 4 | §4.1.3 (Tabela 4.4a / 4.4b) | Tier 4 + mixed-mode + grain-labelled population rows; "publiczne populacje 1v1 Random Map (AoE2)" replacement at line 206 (T19 WARNING-1 micro-pass) | T11 + T19 |
| 4 | §4.1.4 | New `[POP:rm_1v1_and_qp_rm_1v1]` / `[POP:1v1_random_map]` operational tags; four-confound dataset-conditional framing | T11 |
| 4 | §4.2.3 | Workflow-leakage F-072 academic-language replacement; invariant codes I3/I4/I7/I8/I9 rephrased as named scientific principles | T11 |
| 4 | §4.3.2 | New visible-prose hedge `Status walidacji semantycznej strumienia tracker_events_raw` (T19 WARNING-2 micro-pass; GATE-14A6 acknowledgement) | T19 |
| 4 | §4.4.4 | ECE descriptive-diagnostic framing; within-game statistical protocol catalog framing | T11 |
| 4 | §4.4.5 | ICC observed-scale framing weakened to "konserwatywne (potencjalnie dolne) oszacowanie"; ICC reframed as diagnostyka uzupełniająca; [Gelman2007] §11–12 used analogically (T19 WARNING-3 PR-body documentation only) | T11 |
| 4 | §4.4.6 | Post-F1 closure paragraph rewritten; substantive ACTIVE → HISTORICAL narrative routed to Pass-2 redactional session | T11 |

### 8. Claims weakened

- ECE → "descriptive calibration diagnostic" rather than proper scoring rule, both in §2.6.2 and §4.4.4 (RISK-14).
- ICC → "konserwatywne (potencjalnie dolne) oszacowanie" of latent-scale ICC under logit link, in §4.4.5 (RISK-15).
- AoE2 civ count → uniformly hedged "do 50" with explicit roster-instability note across §1.1 / §1.2 / §1.3 / §1.4 / §2.3.2 / §2.5.4 / §4.1.2 / §4.1.3 (RISK-12).
- Civ-pair count → uniformly hedged "do 1 225" with "przy założeniu stałego rosteru" qualifier (RISK-25).
- aoestats → never described as "ranked ladder" in chapter prose; always Tier 4 with explicit "queue semantics unverified" hedge (RISK-04).
- aoe2companion combined ID 6 + ID 18 → never described as "ranked ladder" in chapter prose; always mixed-mode (RISK-02).
- §1.1 coaching-tools sentence + §1.4 disclaimer → SHAP / feature-importance interpretation framed as correlational, not causal (RISK-13).
- §6.3 bounded-comparability statement → deferred to Phase 03/04 with audit trail (RISK-06; F-080 partly-resolved cross-chapter; tracked via WRITING_STATUS.md so the §6.3 obligation does not get lost when Chapter 6 is drafted).
- §4.4.6 → ACTIVE → HISTORICAL substantive narrative rewrite routed to Pass-2 redactional session; the chapter-prose layer is post-F1-aware (PR #185 confirmed merged on master) and carries no `PR #TBD` or `BACKLOG.md F1/F6` workflow leakage (T05 F-098 reclassification).

### 9. Claims corrected

- Step 01_06_02 R01 description: `Retain 1v1 ranked ladder only` → mixed-mode wording (`rm_1v1` ID 6 + `qp_rm_1v1` ID 18); upstream notebook + generator + artifact + research_log + STEP_STATUS lineage closed via T07 + T08 (commit `9581b053`).
- Step 01_06_01 data dictionary: `rating`/`player_history_all` row corrected from TARGET to PRE_GAME; `started`/`player_history_all` row corrected from TARGET to METADATA; root cause was `classify()` substring-matching `"TARGET" in n` on the I3-guard note `"started < target_match.started"`. Fixed via `re.search(r'\bTARGET\b', n)` (T16 14A.1, commit `61128d51`).
- Chapter 4 §4.1.3 line 206: `populację ladderową (AoE2)` → `publiczne populacje 1v1 Random Map (AoE2)` (T19 WARNING-1 micro-pass, commit `c3d1b70d`).
- Chapter 4 §4.3.2: GATE-14A6 / `tracker_events_raw` / Step 01_03_05 deferral now visible to a Chapter-4 reader as a dedicated paragraph (T19 WARNING-2 micro-pass).
- Chapter 3 §3.5 EsportsBench version label: v8.0 / 2025-12-31 → v9.0 / 2026-03-31 with explicit accessed-date hedge (T14, F-091 / F-092 closure).
- Chapter 3 §3.5 Luka 2: Elbert2025EC attribution method corrected from `SHAP` to `linear-FE residualization` (T14, F-037 closed).
- Chapter 3 §3.4.4: Elbert2025EC `aoe2insights.com` data-source attribution verified (T14, F-035 closed).
- Chapter 3 §3.5 Luka 3: AoE2 confirmed NOT in EsportsBench v9.0 (verified 2026-04-26).
- Chapter 4 §4.2.3: workflow-leakage `.claude/scientific-invariants.md:86` reference replaced with academic register "zasada prowenancji liczb" (RISK-08 / F-072).
- AoE2 ranked-ladder terminology unified across all four chapters per the four-tier ladder in `aoe2_ladder_provenance_audit.md` §4.3 (Tier 1 not applicable; Tier 2 = aoe2companion ID 6; Tier 3 = aoe2companion ID 18; Tier 4 = aoestats).

### 10. Claims still unresolved

64 physical chapter flags remain open by design and are routed through `cleanup_flag_ledger.md` to Pass-2 / future phases. The unresolved set falls into four priority classes:

| Priority class | Count | Examples (ledger IDs) | Routing |
|---|---:|---|---|
| Manual library lookup (Pass-2 manual; not WebSearchable) | 1 | F-036 (Brookhouse & Buckley 2025; Caldeira et al. 2025; Alhumaid & Tur 2025; Ferraz et al. 2025 — five WebSearch query formulations on 2026-04-26 returned no record) | Pass-2 manual lookup before final defense |
| Pass-2 literature verification (PDF read or peer-reviewed source check) | ≈ 30 | F-009 / F-019 / F-025 / F-038 (Thorrez2024 EsportsBench Table 2; PDF binary stream not text-extractable); F-020 / F-056 / F-085 (Demsar2006 §3.1.3 vs §3.2 PDF read); F-026 (Yang2017Dota split-method); F-029 / F-030 (CetinTas2023 86% + NB-vs-DT methodology); F-058 (Nakagawa2017 §2.2 + Browne2005 lower-bound directionality); F-060 / F-062 (sc2egset ICC CI delta-method); F-061 (Gelman2007 §11–12 small-cohort identification — also tied to T19 WARNING-3) | Pass 2 in Claude Chat |
| Methodology gates (open hard gates pinning future-PR work) | ≈ 4 | GATE-14A6 / F-102 / RISK-21 (SC2 `tracker_events_raw` semantic validation Step 01_03_05 not yet executed); RISK-08 (Phase 02 leakage guard — pre-emptive); RISK-23 historical residue note (Chapter 4 must not regress to pre-`9581b053` wording); RISK-20 (cross-region fragmentation retention %) | Phase 02 / Phase 03 future PRs |
| Future Phase 03/04/results-dependent (defer until empirical data exist) | ≈ 29 | F-003 / F-004 / F-008 / F-015 / F-016 / F-017 / F-021 / F-040 / F-046 / F-053 / F-057 / F-064 / F-065 (post-Phase-04 verification of method hierarchy, RQ wording, candidate within-game statistical protocol selection, §6.3 bounded-comparability statement, §4.4.6 ACTIVE → HISTORICAL substantive rewrite, Phase-02 SHAP analysis hedge, Phase-02 cross-region retention threshold, etc.) | Phase 03 / Phase 04 / results PRs |

By chapter the 64 flags split as: Chapter 1: 7; Chapter 2: 15; Chapter 3: 14 (= 13 [REVIEW] + 1 [NEEDS CITATION]); Chapter 4: 28 (= 27 [REVIEW] + 1 [UNVERIFIED]). All flags are accounted for in `cleanup_flag_ledger.md` rows F-001 through F-101 plus F-102 (GATE-14A6, T17). No unregistered flags exist in the chapter prose.

### 11. Remaining supervisor-facing risks

Carried forward beyond this PR (per `methodology_risk_register.md` + `reviewer_gate_report.md` NOTEs):

- **RISK-21 / GATE-14A6 (open).** SC2 `tracker_events_raw` semantic validation Step 01_03_05 has not been executed. Until it does, Chapter 4 §4.4 in-game features cannot be drafted past placeholder, and §4.3.2 carries a visible hedge so an examiner sees the deferral. Closure is Phase 02 readiness work, not in this PR.
- **RISK-20 (deferred).** SC2 cross-region fragmentation strict-filter retention percentage is not quantified in any Phase 01 artifact; per Invariant I7 the threshold must not be hard-coded in thesis prose until Phase 02 measures it. The empirical FAIL verdict at W=30 (median undercount 16.0 games, p95 29.0) is citable.
- **RISK-23 (mitigated; requires regression discipline).** Step 01_06_02 generated artifact mis-label was repaired by commit `9581b053`; Chapter 4 (T11) must not regress to pre-repair wording in subsequent edits. The current prose explicitly sources wording from the corrected artifact.
- **§6.3 bounded-comparability statement.** Deferred to Phase 03/04 (Chapter 6 BLOCKED status; F-080 partly-resolved cross-chapter); tracked via WRITING_STATUS.md so the obligation surfaces when Chapter 6 is drafted. T09 cross-dataset comparability matrix is the source-of-truth for the five-axis framing that §6.3 must adopt.
- **F-036 — 4 author candidates (Brookhouse & Buckley, Caldeira et al., Alhumaid & Tur, Ferraz et al.).** Two WebSearch passes (2026-04-20 + 2026-04-26) returned no matching publication. Pass-2 manual library lookup (Google Scholar, IEEE Xplore, ACM DL, library catalogue) required before final defense.
- **§4.4.5 ICC argument [Gelman2007] §11–12 (T19 WARNING-3).** Used analogically for one-way random-effects ANOVA on binary outcomes, not as a direct empirical proof. PR body must state this explicitly so a reader does not over-read the 744-cohort identifiability argument.
- **§4.4.6 ACTIVE → HISTORICAL substantive narrative rewrite.** Routed to a Pass-2 redactional session; the T11 cleanup closed the workflow-leakage layer (`PR #TBD`, `BACKLOG.md F1/F6` removed) but did not perform the substantive narrative redaction.
- **`data_dictionary_aoe2companion.md` templated date.** Generator hard-codes `Date: 2026-04-19` as a literal; the 2026-04-27 regeneration date is captured in research_log + STEP_STATUS comment + manifest detail record (lineage closed). Generator harmonisation routes to Phase 02 prep, not T20.
- **Chapter 1 §1.2 ECE register-drift (NOTE-1 deep).** §1.2 line 19 frames ECE at the head of the operational frame without flagging the descriptive-diagnostic distinction made in §2.6.2 / §4.4.4. Predates this PR; routes to a future Chapter 1 cleanup.

### 12. Commands run

The following commands were executed during the PR, in addition to standard `git` operations and code-editor file reads:

- `source .venv/bin/activate && poetry run pytest tests/ -q` — ran at T19 final gate; 560 passed, 7 statsmodels convergence warnings (not test failures); see `reviewer_gate_report.md` §1 row 11.
- `source .venv/bin/activate && poetry run jupyter nbconvert --to notebook --execute --inplace <notebook.ipynb>` — used by T07 (Step 01_06_02 regeneration) and T16 14A.1 (Step 01_06_01 regeneration); 600 s timeout per `sandbox/notebook_config.toml`.
- `git diff master...HEAD -- "**/data/raw/**"` — confirmed empty output (no raw data modified) at T19.
- `git diff --stat master...HEAD` — confirmed PR scope at T19 (35 files / 18 commits / +7683/-497 then) and at T20 (36 files / 19 commits / +7954/-498 after the T19 micro-pass commit).
- Repeated `rg` mechanical checks for: `populację ladderową|ladderową \(AoE2\)|ranked ladder|ranked-only|ranked ladder only` in Chapter 4; `GATE-14A6|tracker_events_raw|Step 01_03_05|walidacji semantycznej|semantic validation` in Chapter 4; `Phase 01|T[0-9]{2} audyt|PR #TBD|BACKLOG\.md|\bgrep\b|post-F1|branch master|on master|merged to master` across `thesis/chapters/`; physical flag count `\[REVIEW:|\[UNVERIFIED:|\[NEEDS CITATION|\[NEEDS JUSTIFICATION|\[TODO`; manifest active `Status: flagged_stale|regenerated_pending_log` rows.
- pre-commit hooks (ruff, mypy, planning artifact validation, status chain consistency Tier 7, .claude/rules trigger glob, 01_05 notebook spec-binding, jupytext) ran on every commit; see `git log` for the recent commits — all passed when present.

### 13. Review agents run

- **reviewer-adversarial Round 1 (plan critique gate, T02)** — consumed 2026-04-26; produced `planning/current_plan.critique.md` + `planning/current_plan.critique_resolution.md`. 5 BLOCKERs + 5 WARNINGs + 4 NOTEs; all resolved in plan revision v2 + v3.
- **reviewer-adversarial Round 2 (T10 mid-PR consolidated gate)** — consumed 2026-04-26; produced 2 BLOCKERs (RISK-24/25/26 missing + RISK-08 routing) + 4 WARNINGs + 2 NOTEs; both BLOCKERs resolved in 2026-04-26 patch (no new round consumed).
- **reviewer-deep (T19 deep-review)** — verdict `PASS-WITH-NOTES`; 0 BLOCKERs; 0 WARNINGs; 3 informational NOTEs; see `reviewer_gate_report.md` §2.
- **reviewer-adversarial Round 3 (T19 final PR gate)** — consumed 2026-04-27; verdict `PASS-WITH-NOTES`; 0 BLOCKERs; 3 WARNINGs (now 2 resolved by post-T19 micro-pass; WARNING-3 carried to PR body); 6 NOTEs; see `reviewer_gate_report.md` §3.

3 of 3 adversarial rounds consumed; symmetric cap respected. No further reviewer-adversarial dispatch on this PR; future adversarial work must defer to a follow-up PR addressing GATE-14A6 / Step 01_03_05 / Phase 02 readiness.

### 14. Known limitations

- **PDF binary-stream limitation.** Two PDFs critical to Pass-2 verification (Demsar 2006; Thorrez2024 EsportsBench preprint Table 2) returned binary FlateDecode content not extractable via WebFetch. The exact §-location of the N≥5 / N≥10 thresholds in Demsar and the exact Aligulac-on-Aligulac calibration row in Thorrez2024 Table 2 remain Pass-2 manual-PDF-read items (F-020 / F-056 / F-085 / F-009 / F-019 / F-025 / F-038).
- **F-036 four author-candidate citations.** Two independent WebSearch passes did not surface any of the four candidates; Pass-2 manual library lookup is required.
- **External AoE2 leaderboard API documentation unavailable as of 2026-04-26.** All 8 probed endpoints (aoe2.net, aoe2companion.com REST, SiegeEngineers/aoe2companion GitHub source files) returned HTTP 404 or web-app redirects; the aoe2companion ID 18 = `qp_rm_1v1` classification rests on the on-disk label and the T05 fallback rule. A future re-emergence of the API could overturn or confirm the classification.
- **GATE-14A6 unresolved.** SC2 `tracker_events_raw` semantic validation (Step 01_03_05) was not executed in this PR; thesis methodology must not claim validated `tracker_events`-derived features until Step 01_03_05 lands.
- **§6.3 bounded-comparability statement.** Cannot be drafted in this PR (Chapter 6 BLOCKED on Phase 03/04). Tracked via WRITING_STATUS.md.
- **Spec patch-vs-minor classification calls (T15) — borderline.**
  - **CROSS-02-00 v3 → v3.0.1 (T15) — PATCH.** Classification borderline against minor: §3.3 UTC discipline added a *binding requirement* (`SET TimeZone = 'UTC'`), arguably a §5-equivalent gate addition. PATCH stands because: (a) no §2 column-grain commitment changed; (b) no §4 encoding rule changed; (c) no §5 gate condition added/removed at the spec-protocol level — the requirement is a §3 discipline note, not a §5 gate. T10 Round 2 consolidated signoff covers this per Assumption (D) and BLOCKER-2 resolution. Reviewer-deep accepted the borderline patch classification.
  - **CROSS-02-01 v1 → v1.0.1 (T15) — PATCH.** Classification borderline against minor: §4 stale-artifact discipline added an authoritative-reference invariant (`notebook_regeneration_manifest.md` is the stale/current authority), arguably a §2-equivalent audit-dimension addition. PATCH stands because: (a) no §2 audit dimension was added; (b) no §3 schema field changed; (c) no §5 gate condition changed; (d) §4 enforcement is convention-based per §5 ("no CI check, pre-commit hook, or gate script"). The §3 JSON-schema literal `"CROSS-02-01-v1"` is intentionally retained at the patch increment per §192 stability convention (patches do NOT change artifact-schema literal values, because doing so would invalidate `confirmed_intact` lineage of pre-existing audit artifacts produced under the original v1 schema). Reviewer-deep accepted the borderline patch classification.
- **64 physical chapter flags preserved.** All 64 are intentionally retained per Pass-2 dependency; each has a routed Pass-2 verification item, future-Phase dependency, or deferred-to-follow-up routing in `cleanup_flag_ledger.md`. No flag is "stuck"; all have an owner.

### AoE2 provenance outcome (recap)

- **aoestats** = Tier 4 — source-specific aggregation with semantic opacity; queue type (ranked vs quickplay vs custom lobby) cannot be verified from available external documentation; thesis prose must NOT call this population "ranked ladder" without explicit qualification.
- **aoe2companion ID 6 (`rm_1v1`)** = Tier 2 — ranked candidate; on-disk label consistent; external API unavailable.
- **aoe2companion ID 18 (`qp_rm_1v1`)** = Tier 3 — quickplay/matchmaking-derived per on-disk classification + T05 fallback rule.
- **aoe2companion combined ID 6 + ID 18** = mixed-mode population; thesis prose must NOT call this combined scope simply "ranked ladder" — always explicit qualification of the ID 18 quickplay/matchmaking component.

### T19 warning resolution (recap)

- **WARNING-1** — RESOLVED in post-T19 micro-pass (commit `c3d1b70d`).
- **WARNING-2** — RESOLVED in post-T19 micro-pass (commit `c3d1b70d`).
- **WARNING-3** — REMAINS T20 PR-body documentation requirement only (Gelman2007 §11–12 used analogically in §4.4.5, not as direct empirical proof).
