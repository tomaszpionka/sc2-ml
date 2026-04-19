# Planning Backlog

Deferred follow-ups from merged PRs. A session picks ONE item, then fleshes it
out into `current_plan.md` (see `planning/README.md` §Lifecycle) and works
through the standard plan/execute/review loop.

This file is the queue — not an active plan. It holds no executable detail
beyond scoping; the full plan is produced at the moment a session claims the
item.

---

## Origin: PR #160 (feat/pre-01-05-cleanup) + PR #159 (chore/post-pr-158-hygiene)

Opened 2026-04-18.

### F1 — aoestats `canonical_slot` column (Phase 02 unblocker)

- **Category:** A (phase work, aoestats)
- **Branch:** `feat/aoestats-canonical-slot`
- **Invariants touched:** I3, I5, I7, I9
- **Predecessors:** PR #160 W3 verdict `ARTEFACT_EDGE` (commit `ab23ab1d`;
  `reports/specs/01_05_preregistration.md` §14 amendment v1.0.1)
- Thesis-side provenance: PR-3 of DEFEND-IN-THESIS sequence (§4.4.6 flag
  definition + §4.1.2.1 footnote at 52,27% sentence; PR #TBD).
- **Spec amendment trigger:** bumps spec to v1.1.0.

**Scope.** Add a `canonical_slot VARCHAR` derived column to aoestats
`matches_history_minimal` (and upstream `matches_1v1_clean` if needed) to
neutralise the upstream API skill-correlated slot assignment identified by W3.
Phase 02 features then consume `canonical_slot` instead of raw `team`.

**Decision to make during planning.** Whether `canonical_slot` derives from
`old_rating` (skill-ordered) or `profile_id` (identity-ordered,
skill-orthogonal). Artifact JSON §Phase 02 interface at
`src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_05_i5_diagnosis.json`
names both.

**Acceptance.** Schema YAML updated; derivation SQL documented; aoestats
`INVARIANTS.md` §5 `I5` row transitions PARTIAL → HOLDS (or equivalent);
spec §14 amended + `spec_version` bumped; no row-count regression on existing
views.

**Why priority 1.** Unblocks aoestats 01_05 from emitting
`[PRE-canonical_slot]`-tagged outputs and unblocks aoestats Phase 02 entirely.

**01_06 cross-reference (2026-04-19).** Phase 01 Decision Gate (01_06) registered F1 as the
BLOCKER flip-predicate for aoestats READY_CONDITIONAL verdict. Evidence artifact:
`src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoestats.md`.

**F1+W4 coupling (surfaced by reviewer-adversarial 2026-04-19).** F1 alone does NOT flip
aoestats verdict from READY_CONDITIONAL to READY_WITH_DECLARED_RESIDUALS. F1 resolves the
schema gap (adds `canonical_slot`), but INVARIANTS.md §5 I5 row remains PARTIAL until W4
(schema amendment to transition I5 PARTIAL → HOLDS) is also completed. The flip-predicate
is: "BACKLOG F1 (`canonical_slot` resolved in schema) AND W4 (INVARIANTS.md §5 I5 PARTIAL →
HOLDS via schema amendment)." If F1 lands without W4, aoestats Phase 02 expands to include
per-slot features technically, but the invariant state remains undocumented. Both F1 and W4
must land in the same PR or consecutive PRs before the verdict upgrade is valid.

---

### F4 — Narrative-drift checker (chore)

- **Category:** C (chore)
- **Branch:** `chore/narrative-drift-checker`
- **Predecessors:** PR #160 W2 critique A3 (deferred as scope creep).

**Scope.** Implement `scripts/verify_narrative_numbers.py`:
- Parse numeric tokens (≥ 4 significant digits) from every `research_log.md`.
- For tokens under a section header matching `[Phase NN / Step XX_YY_ZZ]`,
  grep the corresponding artifact JSON for the same value.
- Fail on research-log numbers absent from the step's artifact; allow
  documented exceptions via `# drift-allow: <justification>` inline marker.

Install as opt-in pre-commit hook (`git config hooks.checknarrativedrift true`)
and CI lint job on PRs touching `research_log.md`.

**Scope boundary.** Regex extraction must skip dates (`2026-04-18`), seed IDs
(`20260418`), row counts (`683,790`), percentages.

**Acceptance.** Script < 200 LOC; ruff + mypy clean; unit tests cover clean
case, drift detection, exception handling; CI job + pre-commit hook
documented in `.claude/rules/git-workflow.md`.

**Why priority 4.** Defence-in-depth against the class of defect W2
reconciled, but not blocking current work. Can interleave as a low-friction
chore.

---

## Claiming an item

1. Delete the item's entry from this backlog in the same PR that authors
   its `current_plan.md`, so the two artifacts are transactionally
   consistent.
2. Write the full plan into `current_plan.md` (must conform to
   `docs/templates/plan_template.md` — the `planning-drift` pre-commit
   hook enforces the template).
3. For Category A/F: dispatch `reviewer-adversarial` to produce
   `current_plan.critique.md` before execution.
4. For Category C: skip the adversarial gate; `planner` + executor is
   sufficient.
5. Execute, merge, purge per `planning/README.md` §Purge protocol.
