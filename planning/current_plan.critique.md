# Reviewer-Deep Critique — Phase 02 Feature-Engineering Readiness Plan

**Plan:** `planning/current_plan.md` (Category A; branch `phase02/feature-engineering-readiness`)
**Plan author:** gpt-5.5-pro
**Reviewer:** reviewer-deep (per the plan's T06 reviewer choreography; reviewer-adversarial deferred unless reviewer-deep raises an unresolved BLOCKER)
**Round:** 1 of 3 (plan-side)
**Date:** 2026-05-05
**Branch HEAD at review:** plan-stage; before T01 execution

---

## Verdict

**PASS-WITH-NOTES.** 0 unresolved BLOCKERs. 4 WARNINGs carried forward into T03–T06 execution. Implementation remains blocked beyond T01 until user review of the T01 checkpoint.

This critique is the plan-side reviewer-deep gate. Reviewer-deep is used in lieu of reviewer-adversarial per user override of the CLAUDE.md default Cat-A choreography (mirroring PR #207's pattern). The plan frontmatter `critique_required: true` is satisfied by this file. Reviewer-deep plan gate consumed; reviewer-adversarial not invoked; adversarial cap not consumed.

---

## Resolved blocker themes

The following themes were identified during reviewer-deep analysis of the Phase 02 plan and are resolved in the plan as written. They are recorded here for provenance; no plan revision is pending on any of them.

### Resolved blocker theme 1 — 02_03 must not supersede 02_01

CROSS-02-03 (the temporal feature audit protocol proposed by plan T04) MUST NOT supersede or replace CROSS-02-01-v1.0.1 (the pre-training leakage audit protocol). CROSS-02-03 is a **design-time / source-family protocol only**: it prescribes checks that fire during feature-family construction (e.g., `HISTORY_STRICT_LT_TARGET`, `INGAME_LOOP_CUTOFF`, `SOURCE_LABEL_STRATIFICATION`) but does NOT gate post-materialization pre-training audit. CROSS-02-01-v1.0.1 remains the binding pre-training leakage audit gate for Pipeline Sections 02_01 / 02_03 / 02_06 per its own §1 / §6.

**Resolution location in plan:**

- T04 instructions step 2 carries the non-supersession clause: "CROSS-02-01 remains the mandatory pre-training/materialization leakage audit. CROSS-02-03 adds feature-family design-time and source-specific temporal checks."
- T04 falsifier flags any text that says CROSS-02-03 replaces CROSS-02-01.
- T04 verification rg pattern `does not replace|CROSS-02-01 remains|event.loop <= cutoff_loop|ph.<anchor> < target.started_at|training fold` (positive match required) and `replaces CROSS-02-01|tracker-derived.*pre-game|full-dataset scaler` (negative match required).

### Resolved blocker theme 2 — T01 must state GATE-14A6 outcome = narrowed and full tracker scope is not closed

The T01 phase01_closeout_summary.md MUST state both:

- `GATE-14A6 outcome: narrowed`
- `full tracker scope is not closed`

These are required artifact-validation phrases per plan T01 instructions step 7. Without them, downstream Phase 02 sessions could collapse the narrowed / not-closed distinction into "validated tracker features" or "closed gate" — both factually wrong per the PR #208 outcome (`gate_14a6_decision = narrowed`; `planned_subset_ready_predicate_satisfied = true`; `full_tracker_scope_closed_predicate_satisfied = false`).

**Resolution location in plan:**

- T01 verification rg pattern `GATE-14A6 outcome: narrowed|full tracker scope is not closed|aoestats Tier 4|aoe2companion mixed-mode|tracker-derived features are never pre-game` (positive match required).
- T01 verification rg pattern `ranked ladder only|ranked-only|GATE-14A6.*closed` (negative match required).
- The negative pattern `GATE-14A6.*closed` is line-anchored; T01 phrasing must keep `GATE-14A6` and the literal substring `closed` on different physical lines. The required phrase `full tracker scope is not closed` is preserved in §1 status table row 2, in §3 second paragraph, and in §5 mandatory phrases list — none of those lines contain `GATE-14A6` on the same physical line.

### Resolved blocker theme 3 — tracker-derived SC2 features are never pre-game

SC2 `tracker_events`-derived features MUST NEVER carry `prediction_setting = pre_game`. Per Amendment 2 of PR #208 and Invariant I3, every row in `tracker_events_feature_eligibility.csv` carries `status_pre_game = not_applicable_to_pre_game`. CROSS-02-02 (the feature-engineering plan from plan T03) MUST reflect this; any tracker-derived family marked `pre_game` is a hard plan failure.

**Resolution location in plan:**

- T03 instructions step 7 imports the tracker CSV constraints verbatim (15 rows; 5 eligible_for_phase02_now + 7 eligible_with_caveat + 3 blocked).
- T03 falsifier explicitly flags "any SC2 tracker-derived family marked `pre_game`" as a blocker.
- T03 verification check blocks the literal `tracker-derived pre-game`.
- T01 mandatory phrase `tracker-derived features are never pre-game` is required.

---

## Warnings carried forward

These do not block T01 commit but must be honoured during T03 / T04 / T05 / T06 execution.

### Warning 1 — phase02 branch-prefix classification must be verified

The branch prefix `phase02/` is not enumerated in `.claude/rules/git-workflow.md` version-bump table (which lists `feat/`, `refactor/`, `docs/` → minor; `fix/`, `test/`, `chore/` → patch). Before any PR wrap-up commit:

- verify no GitHub workflow / pre-commit hook / `.claude/rules` glob rejects the `phase02/` prefix (covered by plan T00; operational result confirmed at session start: no `.github/workflows`, pre-commit hooks do not filter by branch, `.claude/rules` paths globs do not gate the prefix);
- decide and record the version-bump classification (minor vs patch) at PR wrap-up time.

### Warning 2 — no cold-start magic constants may be introduced without empirical derivation

CROSS-02-02 (plan T03) and CROSS-02-03 (plan T04) MUST NOT name a default cold-start threshold K, default pseudocount m, default smoothing strength, or default prior. Per Invariant I7, every numeric value MUST be data-derived from training-fold statistics or literature-cited and recorded in the per-dataset Phase 02 ROADMAP step that materializes it. Plan T03 §4.5 and plan T04 `COLD_START_GATE` audit family are the binding gates.

### Warning 3 — AoE2 terminology must preserve aoestats Tier 4 and aoe2companion mixed-mode labels

Across T01, T03, T04, T05, T06 outputs, AoE2 terminology MUST follow `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` §4.3 four-tier ladder. `aoestats` is Tier 4 (semantic opacity); `aoe2companion` combined `internalLeaderboardId IN (6, 18)` is mixed-mode (NOT a ranked-ladder umbrella). The plan's T05 cross-spec consistency pass enforces this through forbidden-term grep checks.

### Warning 4 — proposed Phase 02 ROADMAP steps are proposals, not executed dataset ROADMAP changes

CROSS-02-02 §6 (plan T03) lists proposed Phase 02 ROADMAP step IDs (e.g., 02_01_01 through 02_08_01). These are PROPOSALS only. Plan T03 instructions step 9 explicitly forbids dataset ROADMAP edits in this PR. Any future PR that converts a proposal into an executed ROADMAP step requires user approval and a separate commit.

---

## Notes

1. **Reviewer choreography deviation.** The plan's reviewer choreography routes plan-side critique to reviewer-deep instead of the CLAUDE.md default Cat-A reviewer-adversarial. This is a plan-internal user override; `critique_required: true` is satisfied by reviewer-deep per the same pattern PR #207 used. Reviewer-deep plan gate consumed; reviewer-adversarial not invoked; adversarial cap not consumed.

2. **File-manifest conservatism.** The plan's File Manifest is bounded to documentation/specification artifacts only. No notebooks, generated artifacts, raw data, locked specs, ROADMAPs, status YAMLs, research_logs (per-dataset), or thesis chapters are touched.

3. **Conditional CHANGELOG.md update.** Plan T06 marks the `CHANGELOG.md` update as conditional on current repository convention. Decision is deferred to T06 execution time; the no-op outcome must be documented in the PR body if the convention does not require an `[Unreleased]` entry for spec/rule-only changes.

---

## Reviewer status

- Reviewer-deep plan gate consumed (this file; verdict PASS-WITH-NOTES; 2026-05-05).
- Reviewer-adversarial not invoked.
- Adversarial cap not consumed.

The execution-side reviewer-deep gate (per plan T06) is reserved for PR wrap-up. Reviewer-adversarial dispatch at PR wrap-up is conditional on a reviewer-deep BLOCKER finding at that point and has not been invoked at the planning stage.

---

## Implementation gate

- T01 (`thesis/pass2_evidence/phase01_closeout_summary.md`): cleared for execution; artifact already present and validated against the T01 rg checks.
- T02 (`.claude/rules/data-analysis-lineage.md`): **BLOCKED until user review of the T01 checkpoint.**
- T03 (`reports/specs/02_02_feature_engineering_plan.md`): BLOCKED until user review.
- T04 (`reports/specs/02_03_temporal_feature_audit_protocol.md`): BLOCKED until user review.
- T05 (cross-spec consistency pass): BLOCKED until T01–T04 are committed.
- T06 (research_log update + reviewer-deep gate + conditional CHANGELOG): BLOCKED until T01–T05 are committed.

The iterative execution protocol per user direction is to commit and gate after each task at the user-review boundary.
