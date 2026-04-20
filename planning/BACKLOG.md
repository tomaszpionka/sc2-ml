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
