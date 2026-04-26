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

## Plan-manifest correction (T14 pre-dispatch)

**Date:** 2026-04-26

T14 scope correction (2026-04-26): before T14 execution, the plan was amended to include `claim_evidence_matrix.md` and `cleanup_flag_ledger.md` in T14 write scope, preserving the same audit-trail discipline used in T11–T13. This is a manifest correction, not a scientific scope expansion. The two files are already authorised globally in the master File Manifest (lines 1768 and 1771); the T14 per-task `**File scope:**` block was extended to surface them explicitly for the executor, and instructions 8–9 were added to T14 to make the chapter→registry propagation contract explicit.
