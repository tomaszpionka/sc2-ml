# Planning

Operational orchestration directory for the plan/execute two-session workflow.

## Contents

| Path | Lifecycle | Purpose |
|------|-----------|---------|
| `README.md` | Permanent | This file |
| `INDEX.md` | Permanent (reset after merge) | Active plan pointer + agent routing |
| `BACKLOG.md` | Permanent (append/claim) | Deferred follow-ups from merged PRs; a session claims one item → fleshes it into `current_plan.md` |
| `current_plan.md` | Ephemeral | The authoritative plan for the active PR |
| `current_plan.critique.md` | Ephemeral | Adversarial critique (Cat A/F mandatory; B/D conditional) |
| `current_plan.critique_resolution.md` | Ephemeral | Critique-resolution companion / plan-review resolution log (Cat A/F when critique present) |

## Lifecycle

1. **Planning session:** Planner produces plan in chat. Parent writes to
   `current_plan.md` (conforms to `docs/templates/plan_template.md`).
   For Category A/F (and optionally B/D when `file_scope` touches game src),
   reviewer-adversarial reads `current_plan.md` and produces
   `current_plan.critique.md`. User approves.
2. **Execution:** Parent dispatches executor(s) with `planning/current_plan.md`
   as the pointer and which task(s) (T01, T02, …) to execute.
   Executor reads the plan directly — no intermediate spec files.
3. **Final review:** Dispatcher passes `planning/current_plan.md` path + diff
   base ref. Reviewer reads the plan and diff themselves.
   Reviewer by category: reviewer-adversarial (Cat A/F); reviewer-deep (Cat B/D);
   reviewer (Cat C/E).
4. **PR wrap-up:** `current_plan.md` and `current_plan.critique.md` are
   committed on the feature branch as provenance.
5. **After merge:** Purge protocol runs (see below).

## Purge protocol (after PR merge)

On the first session after merge to master, commit once as
`chore(planning): purge artifacts from merged PR #N`:

1. Replace `current_plan.md` with `<!-- No active plan -->`
2. Delete `current_plan.critique.md` and `current_plan.critique_resolution.md` (if present)
3. Reset `INDEX.md` to its template state

## Source-of-truth

`current_plan.md` is authoritative. The plan defines intent and execution
instructions. Executors read it directly.

See `ARCHITECTURE.md` tier 8 for the full hierarchy.
