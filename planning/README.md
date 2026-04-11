# Planning

Operational orchestration directory for the plan/execute two-session workflow.

All planning artifacts live here. For terminology (Spec, DAG, Job, Task Group,
Task), see [`docs/TAXONOMY.md`](../docs/TAXONOMY.md).

## Contents

| Path | Lifecycle | Purpose |
|------|-----------|---------|
| `INDEX.md` | Permanent (reset after merge) | Agent routing table — which agent reads what |
| `README.md` | Permanent | This file |
| `current_plan.md` | Ephemeral | The authoritative Spec for the active PR |
| `specs/README.md` | Permanent | Parallel execution guide (Strategy A/B) |
| `specs/spec_*.md` | Ephemeral | Individual task specs, one per DAG task |
| `dags/README.md` | Permanent | DAG format documentation |
| `dags/DAG.yaml` | Ephemeral | The single active execution graph |
| `dags/DAG_STATUS.yaml` | Ephemeral (optional) | Execution state tracker |

## Lifecycle

1. **Planning session:** Planner produces plan in chat. Parent writes to
   `current_plan.md`. Adversarial reviewer reviews. User approves.
2. **Execution session (first action):** Parent materializes `dags/DAG.yaml`
   and `specs/spec_*.md` from the approved plan. Updates `INDEX.md`.
3. **During execution:** Parent dispatches agents per `DAG.yaml`. Updates
   `DAG_STATUS.yaml` (if used). Commits per task group.
4. **PR wrap-up:** All planning artifacts committed on the feature branch.
5. **After merge:** Purge protocol runs (see below).

## Purge protocol (after PR merge)

On the first session after merge to master, stage all of the following
together and commit once as `chore(planning): purge artifacts from merged PR #N`:

1. Replace `current_plan.md` with `<!-- No active plan -->`
2. Replace `dags/DAG.yaml` with `# No active DAG`
3. Delete `dags/DAG_STATUS.yaml` (if present)
4. Delete all `specs/spec_*.md` files
5. Reset `INDEX.md` to its template state (remove spec links, keep structure)

## Source-of-truth

Within this directory, precedence is:

1. `current_plan.md` — authoritative. The plan defines intent.
2. `dags/DAG.yaml` — derived. Execution order. If it diverges, the plan wins.
3. `specs/spec_*.md` — derived. Task-level extracts. If they diverge, the plan wins.

See `ARCHITECTURE.md` tier 8a/8b for the full hierarchy.
