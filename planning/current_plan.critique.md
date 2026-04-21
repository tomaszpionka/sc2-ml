# Adversarial Review — Plan (Mode A) — WP-2

**Plan:** `planning/current_plan.md` (WP-2 — Mandatory Pre-Training Leakage Audit Protocol Spec)
**Branch:** `docs/phase02-leakage-audit-protocol`
**Base:** `master` @ `5682acfb` (post PR #198; version 3.39.0)
**Date:** 2026-04-21
**Reviewer:** reviewer-adversarial, Mode A (pre-execution)

## Lens summary

| Lens | Verdict |
|---|---|
| Temporal discipline | SOUND — spec is about preventing I3 violations; does not itself introduce any |
| Statistical methodology | N/A — docs-only spec; no statistical tests invoked |
| Feature engineering | N/A — spec prescribes audit protocol, not feature construction |
| Thesis defensibility | ADEQUATE — gate mechanism is non-binding without tooling; examiners can ask |
| Cross-game comparability | AT RISK — aoestats Phase 01 audit is Markdown, not JSON; plan's template-inheritance claim is false for one of three datasets |

## BLOCKER / WARNING / NOTE findings

1. **[BLOCKER] Assumption 2 is factually wrong for aoestats.** Plan's Assumptions section claims all three Phase 01 leakage-audit JSON artifacts carry `future_leak_count`, `post_game_token_violations`, `reference_window_assertion`. The aoestats Phase 01 audit at `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_06_temporal_leakage_audit_v1.md` is a **Markdown file, NOT JSON**; its structure uses freeform section headers (Q7.1, Q7.2, Q7.3, Q7.4) rather than key-value fields. sc2egset + aoe2companion audits ARE JSON and do carry the three fields. T01 instruction 4 asks the executor to tabulate a "shared field matrix across 3 Phase 01 artifacts" — the true intersection is empty because the aoestats MD contributes zero JSON field names. The plan must acknowledge the format asymmetry and define semantic equivalences (e.g., Q7.1 → `future_leak_count`, Q7.2 → `post_game_token_violations`, Q7.3 → `reference_window_assertion`).

2. **[BLOCKER] "sc2egset WARNING 2 from 2026-04-21 Phase 01 sign-off audits" has no on-disk referent.** The plan cites the finding code "WARNING 2" but no artifact in the repo carries that designation. The sc2egset modeling-readiness doc uses risk IDs SC-R01 through SC-R07; the cross-dataset rollup enumerates dimensions D1–D6; `pass2_status.md` tracks F5.x/F6.x Pass-2 findings, not W-x Phase 01 audit findings. The actual source is the reviewer-adversarial agent output from earlier this session (agent af5c57132779f1103) which was summarized in chat but NOT committed as an artifact. Invariant I9 requires traceability to existing artifacts. An examiner asking "show me the sc2egset WARNING 2 you claim to close" finds nothing. Fix: commit a Phase 01 audit summary artifact consolidating the 3 dataset sign-off verdicts + their WARNING/NOTE enumerations as the durable on-disk referent for WP-2, WP-3, WP-4, WP-5.

3. **[WARNING] T02 verification grep count will produce a false "FAIL".** Verification step says "`grep 'CROSS-02-01-v1'` returns exactly ONE match (frontmatter)." But T02 instructions also embed `CROSS-02-01-v1` in §1 prose (cites WP-1 sibling), §3 schema field description, and possibly §8. The grep will return several matches even on a correctly-executed spec. Fix: frontmatter-scope the assertion, e.g., `grep '^spec_id: CROSS-02-01-v1'`.

4. **[WARNING] §5 gate condition is advisory without CI tooling.** T02 instruction 6 + Gate Condition prescribe: "verdict = PASS required for 02_01 exit; missing audit OR verdict != PASS blocks the Pipeline Section." No pre-commit hook, CI script, or tooling in `scripts/` or `.github/workflows/` reads the JSON and fails commits if `verdict != "PASS"`. The gate is documented but not enforced. Examiner-grade weakness: "You say this is binding — what prevents bypassing it?" Fix: either (a) schedule a follow-up task adding a CI/pre-commit guard (separate PR, noted in §Out of scope or §Open questions), or (b) explicitly acknowledge in §5 that v1 enforcement is "by convention + mandatory adversarial review, not by automated tooling," with §7 future-amendment target to add tooling enforcement.

5. **[NOTE] `spec_id`/`version` field collapse is cosmetic but creates a two-field redundancy.** T02 instruction 1 prescribes `spec_id: CROSS-02-01-v1`, `version: CROSS-02-01-v1` (identical). WP-1's spec (`02_00_feature_input_contract.md`) has the same collapse. If both fields permanently carry the same value, one is dead weight. The §7 version pattern `CROSS-02-01-vN.M.K` implies full replacement, keeping the two synchronized and therefore redundant. Examiner question risk: "What is the semantic difference between `spec_id` and `version`?" Not blocking; worth flagging for future spec-versioning-convention amendment that standardizes across WP-1 + WP-2.

6. **[NOTE] §2.2 POST-GAME lineage resolution defers to "SQL AST walk or Python docstring".** The plan names two lineage-resolution mechanisms without selecting one. For cascading SQL views (this pipeline's pattern), no existing AST-walk tool exists in `scripts/`; for Python notebook code, docstring tracing requires conventions not yet defined. Plan explicitly declares implementation out of scope (Phase 02 planner-science decides). But if Phase 02 picks "manual checklist" as the implementation, §2.2's lineage audit is unenforceable for deep VIEW cascades. The spec should note this limitation so Phase 02 planner-science cannot miss it.

## Verdict

**REVISE BEFORE EXECUTION.** BLOCKER 1 (aoestats format asymmetry) and BLOCKER 2 (traceability gap) must be addressed before execution. BLOCKER 2 in particular affects all four remaining WPs (WP-2, WP-3, WP-4, WP-5) — they all cite 2026-04-21 audit findings without a committed on-disk source.

## If REVISE: required revisions (enumerated list)

1. **Fix Assumption 2** — plan Assumptions section: correct the claim that all three Phase 01 audits are JSON. Acknowledge that aoestats is Markdown. T01 instruction 4 must instruct executor to handle format asymmetry with explicit field equivalences (Q7.x ↔ JSON field names).

2. **Add T05 (new task)** — Create Phase 01 audit summary artifact at `reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md` consolidating the 3 dataset sign-off verdicts (sc2egset, aoestats, aoe2companion) with their WARNING/NOTE enumerations. This artifact becomes the durable on-disk referent for WP-2 (closes WARNING 2) and future WP-3/WP-4/WP-5 (close other findings). File manifest becomes 6 git-diff-scope files (was 5). Renumber existing T04 → T06.

3. **Fix T02 verification grep** — change the criterion from `grep "CROSS-02-01-v1"` returning "exactly ONE match" to a frontmatter-scoped assertion like `grep "^spec_id: CROSS-02-01-v1"` returning one match.

4. **Acknowledge gate non-enforcement in spec §5** — T02 instruction 6 should also instruct the spec to note that v1 enforcement is "by convention + mandatory adversarial review, not by automated tooling," with §7 prescribing tooling enforcement as a future amendment target (follow-up PR to add CI/pre-commit guard).

(NOTEs 5 and 6 are optional; NOTE 5 can be addressed in a future spec-versioning-convention chore that standardizes both WP-1 and WP-2 frontmatter; NOTE 6 can be addressed by adding one sentence to spec §2.2 acknowledging the implementation-dependency limitation.)
