# R2 Critique — Autonomous-mode decisions

R2 adversarial returned ESCALATE_TO_USER with 6 items. User is asleep per autonomous directive. Decisions applied by autonomous pilot:

## Decisions

### N1 (BLOCKER) — Option B: prose acknowledgment, NOT artifact repair
**Rationale:** Option A would modify a Phase 01 artifact after its completion was formally gated (PIPELINE_SECTION_STATUS 01_04 = complete, STEP_STATUS entries dated 2026-04-17). Post-hoc ledger rewriting to match thesis narrative is an I9-adjacent precedent that weakens research-pipeline discipline. Option B (prose acknowledgment) is more honest AND preserves artifact immutability. Add ~400 chars to T04 acknowledging the divergence in clear, non-apologetic language.

### N2 (WARNING) — ACCEPT: add both bib entries + Madley-Dowd rebuttal
**Rationale:** Jakobsen 2017 is a peer-reviewed anchor stronger than van Buuren 2018 prose for the 40% threshold. Madley-Dowd 2019 is a direct challenge to proportion-driven routing that an examiner will raise; pre-empting it strengthens defence. Add both to `references.bib`, cite Jakobsen 2017 for 40%, and insert a ~300-char rebuttal paragraph against Madley-Dowd explaining Phase-01-is-fold-agnostic constraint.

### N3 (WARNING) — ACCEPT: document §4.1 repair in commit/PR scope
**Rationale:** Branch is already `docs/thesis-4.2-session`; renaming post-hoc is churn. Surface §4.1 repair in T05 commit message + final PR body so diff reviewers aren't surprised.

### N4 (WARNING) — ACCEPT: raise T04 upper bound to 15k
**Rationale:** §4.1.2 consumed 22.5k for two datasets without typology. §4.2.3 at 15k upper for three datasets + typology + defence + I7 provenance + MMR-MAR + two tables is ~66% of §4.1.2 per-dataset density — still terse but feasible. Total revised budget 24.0-30.5k.

### N5 (NIT) — ACCEPT: explicit prose acknowledgment in Tabela 4.6 caption
**Rationale:** Moving row 5 to 4.6a would fragment the typology unnecessarily; FLAG_FOR_IMPUTATION is a canonical rule class even if it's invoked only in aoe2companion. Acknowledge in caption that the row is retained because the mechanism is canonical in the typology, not because multi-dataset invocation.

### N6 (NIT) — ACCEPT: add I4 to invariants_touched
**Rationale:** §4.2.3 discusses target-consistency filters and POST_GAME exclusions. I4 should be listed.

## Handoff

Planner-science R3 should produce plan_4_2_v3.md applying these 6 decisions. Expected output: change log at top + updated plan body. Then parent persists to `planning/current_plan.md` and proceeds to execution (T01-T06) without R3 plan-side adversarial, reserving adversarial budget for execution-side.
