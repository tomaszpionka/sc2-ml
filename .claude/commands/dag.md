# Execute DAG

Execute the DAG at `planning/dags/DAG.yaml` (or the path provided as argument).
This is the execution phase — the DAG and specs must already exist on disk.

## Arguments

If the user provided arguments: `$ARGUMENTS`
Use the first argument as the DAG file path (e.g., `/dag planning/dags/DAG_sc2.yaml`).
If no arguments, default to `planning/dags/DAG.yaml`.

## Pre-flight

1. Read the DAG file. If it does not exist or is empty, STOP.
2. Verify the branch matches `branch:` in the DAG. If not, WARN but proceed
   (the user may have intentionally switched).
3. For each task in the DAG, verify its `spec_file` exists on disk:
   ```bash
   grep "spec_file:" <dag_path> | awk '{print $2}' | tr -d '"' | while read f; do
     [ -f "$f" ] && echo "OK: $f" || echo "MISSING: $f"
   done
   ```
   If any are MISSING, STOP — materialization is incomplete.

## Execution protocol

### Step 1: Parse the DAG structure

From the DAG, extract:
- `jobs` — list of independent execution streams
- Within each job: `task_groups` in dependency order
- Within each group: `tasks` with `spec_file`, `agent`, `parallel_safe`, `depends_on`
- `review_gate` per group
- `final_review` configuration

### Step 2: Execute jobs

If the DAG has multiple jobs with no cross-job `depends_on`, dispatch them
in parallel (or sequentially — either is correct). If jobs have dependencies,
respect them.

For each job, execute task groups in dependency order:

#### For each task group:

1. **Dispatch tasks.**
   - Tasks with `parallel_safe: true` and no unmet `depends_on` within the
     group: dispatch in parallel.
   - Tasks with `parallel_safe: false` or unmet `depends_on`: dispatch
     sequentially after their dependencies complete.
   - **Dispatch prompt format** (pointer, NOT content):
     ```
     You are executing task {task_id} from DAG {dag_id}.
     Your spec is at: {spec_file}
     Read the spec FIRST. It is your contract. Execute exactly what it says.
     ```
     Do NOT add context, instructions, or summaries from the plan or spec.
     The spec is the sole source of truth — the executor reads it via tool call.

2. **Review gate.**
   After all tasks in the group complete, dispatch the review gate agent
   specified in `review_gate.agent` with:
   - Scope: `review_gate.scope` ("diff" = changes from this group only,
     "cumulative" = all changes since DAG start)
   - Base ref: `review_gate.base_ref` ("auto" = SHA before first task started)
   - If the reviewer returns a BLOCKER: HALT and report to the user.
     Do not proceed to the next task group.
   - If the reviewer returns APPROVE or non-blocking issues: proceed.

3. **Report group completion.** State which tasks completed, which gates
   passed, and any issues flagged.

### Step 3: Final review

After all jobs and task groups complete, dispatch the `final_review` agent
with:
- `plan_ref` path from the DAG (the reviewer reads it, not the orchestrator)
- All `spec_file` paths from the DAG (the reviewer reads them)
- `base_ref` for the diff
- Scope: "all" (full diff from base to HEAD)

The final reviewer checks plan-vs-reality alignment, spec compliance, and
scope drift. Report its verdict.

### Step 4: Report

Print a summary:
- DAG ID, branch, category
- Jobs executed: count
- Task groups completed: count
- Tasks completed: count
- Review gates: PASS/FAIL per group
- Final review: verdict
- Any blockers or issues

## Rules

- **Read ONLY the DAG file** for task structure. Do NOT read `current_plan.md`
  or spec files — executors read their own specs, reviewers read as needed.
- **Dispatch prompts are pointers.** The prompt contains the spec_file path
  and task_id. Nothing else. No objectives, no instructions, no verification
  criteria from the spec or plan.
- **Respect review gates.** A BLOCKER from a review gate halts execution.
  The user decides next action.
- **Do not modify files yourself.** The orchestrator dispatches agents — it
  does not write code, edit specs, or run tests directly. The executors and
  reviewers do the work.
- **Commit staging is the orchestrator's job.** After each task group (if on
  a shared branch), stage and commit the executor's changes. Executors on
  shared branches do not run `git add` or `git commit`.
