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
| `current_plan.critique.md` | Ephemeral | Adversarial critique produced by reviewer-adversarial (Category A/B/F mandatory; D conditional on file_scope touching game src); not produced by the planner |
| `specs/README.md` | Permanent | Parallel execution guide (Strategy A/B) |
| `specs/spec_*.md` | Ephemeral | Individual task specs, one per DAG task |
| `dags/README.md` | Permanent | DAG format documentation |
| `dags/DAG.yaml` | Ephemeral | The single active execution graph |
| `dags/DAG_STATUS.yaml` | Ephemeral (optional) | Execution state tracker |

## Lifecycle

1. **Planning session:** Planner produces plan in chat. Parent writes to
   `current_plan.md`. Plan MUST include a Suggested Execution Graph.
   For Category A/F (and optionally B/D), after the plan is written and before
   materialization, reviewer-adversarial reads `current_plan.md` and produces
   `current_plan.critique.md`. User approves.
2. **Materialization (first action after approval):**
   a. **Purge old specs:** Delete all `specs/spec_*.md` files (keep `README.md`).
      Old specs belong to the prior plan — they must not persist into the new
      execution. Specs always start from `spec_01` on every plan.
   b. **Generate specs:** Extract one `specs/spec_NN_<name>.md` per DAG task
      from the approved plan. Specs are numbered sequentially starting at 01,
      matching `task_id` in the DAG. Content comes from the plan — specs are
      derived, not invented.
   c. **Generate DAG:** Write `dags/DAG.yaml`. Each task's `spec_file` field
      MUST point to the spec created in step (b). The DAG's `plan_ref` field
      points to `planning/current_plan.md` (provenance only — executors read
      specs, not the plan).
   d. **Update INDEX.md** with spec links.
   e. **Commit** all materialized artifacts together.
   **Execution MUST NOT begin until DAG + specs exist on disk — no exceptions,
   even for single-task plans.**
3. **Execution (only after materialization is committed):** Parent reads
   `dags/DAG.yaml` and dispatches agents per task group. Agents read their
   assigned spec file, not the full plan. Updates `DAG_STATUS.yaml` (if
   used). Commits per task group. Review gates after each group.
4. **PR wrap-up:** All planning artifacts committed on the feature branch.
5. **After merge:** Purge protocol runs (see below).

## Purge protocol (after PR merge)

On the first session after merge to master, stage all of the following
together and commit once as `chore(planning): purge artifacts from merged PR #N`:

1. Replace `current_plan.md` with `<!-- No active plan -->`
2. Replace `dags/DAG.yaml` with `# No active DAG`
3. Delete `dags/DAG_STATUS.yaml` (if present)
4. Delete all `specs/spec_*.md` files
5. Delete `current_plan.critique.md` (if present)
6. Reset `INDEX.md` to its template state (remove spec links, keep structure)

## Source-of-truth

Within this directory, precedence is:

1. `current_plan.md` — authoritative. The plan defines intent.
2. `dags/DAG.yaml` — derived. Execution order. If it diverges, the plan wins.
3. `specs/spec_*.md` — derived. Task-level extracts. If they diverge, the plan wins.

See `ARCHITECTURE.md` tier 8/8b for the full hierarchy.
