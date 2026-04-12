# Materialize Plan

Convert an approved plan in `planning/current_plan.md` into executable
artifacts: spec files and a DAG. This is the gate between planning and
execution — nothing runs until this command completes.

## Arguments

If the user provided arguments: `$ARGUMENTS`
Use them as additional context (e.g., "skip INDEX update", "dry run").

## Why this is mechanical, not creative

`planning/current_plan.md` already contains the full task breakdown:
- **Execution Steps** section defines each task's objective, instructions,
  file scope, read scope, and verification criteria
- **Suggested Execution Graph** defines task IDs (T01, T02, ...), group IDs,
  dependency ordering, agents, and `spec_file` paths
- **File Manifest** lists every file touched

The plan IS the source of truth for spec numbering, naming, and content.
Materialization extracts each task's section from the plan into its own
spec file, then wires the DAG to reference those files. No invention, no
interpretation — if the plan says T01 is "Update log-subagent.sh" with
file_scope `scripts/hooks/log-subagent.sh`, that is exactly what spec_01
contains.

If the plan lacks a Suggested Execution Graph, or the graph lacks task
definitions with file scopes, the plan is incomplete — STOP and tell the
user the plan needs revision before materialization.

## Pre-flight

1. Run `git branch --show-current` to confirm you are NOT on master/main.
   If on master/main, STOP — materialization happens on the feature branch.
2. Read `planning/current_plan.md`. If it is empty or contains only a
   placeholder (`<!-- No active plan -->`), STOP — there is no plan to
   materialize.
3. Verify the plan contains a **Suggested Execution Graph** section with
   task_id, spec_file, file_scope, and depends_on for each task. If any
   of these are missing, STOP — the plan is incomplete.
4. Read the plan's frontmatter to extract `category` and
   `critique_required`. If `category` is A or F (or `critique_required`
   is true), verify `planning/current_plan.critique.md` exists and is
   non-empty. If missing, HALT with message: "Category A/F requires
   adversarial critique before materialization. Dispatch
   reviewer-adversarial to produce
   `planning/current_plan.critique.md` first."

## Step 1: Purge old specs

Delete all `planning/specs/spec_*.md` files. Keep `planning/specs/README.md`.

```bash
rm -f planning/specs/spec_*.md
```

If no old specs exist, this is a no-op. Report how many were deleted (may be 0).

## Step 2: Generate spec files from the plan

For each task in the plan's Suggested Execution Graph, extract its content
into a spec file. The plan already defines the `spec_file` path for each
task (planners are required to include these), so the naming is predetermined:
- Task T01 with `spec_file: "planning/specs/spec_01_log_subagent.md"` → create that file
- Task T02 with `spec_file: "planning/specs/spec_02_log_bash.md"` → create that file
- (and so on — the plan is the source of truth for naming)

**Each spec MUST follow `docs/templates/spec_template.md` as its schema.**
Read that template first. It defines the required structure:
- YAML frontmatter fields (task_id, task_name, agent, dag_ref, group_id,
  file_scope, read_scope, category) — values copied from the plan
- `## Objective` — extracted from the plan's Execution Steps
- `## Instructions` — extracted from the plan's Execution Steps
- `## Verification` — extracted from the plan's Execution Steps
- `## Context` (optional) — links to docs, dependencies, invariants

The template is the dataclass. Every spec is an instance of it.

**Rules:**
- Content is extracted from the plan, not invented
- Every spec MUST be self-contained. If the plan says "Same as TXX" or
  "Same pattern as spec_XX", inline the full instructions with substituted
  paths. Never produce a spec that references another spec.
- If the plan's Execution Steps section for a task lacks detail, copy what
  exists and flag it: "NOTE: plan underspecified — agent should read
  plan section for additional context"
- Do NOT add scope, files, or instructions that the plan does not define
- If the plan's Suggested Execution Graph includes a `model` field on a task,
  include it in the spec's YAML frontmatter.
- When the plan marks tasks for consolidation (shared read_scope, parameterized
  dataset table), produce one combined spec with all instructions inlined.

After generating all specs, verify:
```bash
ls -la planning/specs/spec_*.md
```

Report count and names.

## Step 3: Generate DAG

Write `planning/dags/DAG.yaml` from the plan's Suggested Execution Graph.
The graph already defines the structure — this step serialises it to YAML.

**Rules:**
- `plan_ref` at DAG level points to `planning/current_plan.md` (provenance)
- Each task's `spec_file` points to the spec created in Step 2
- All other fields (depends_on, parallel_safe, review_gate, etc.) are
  copied from the plan's Suggested Execution Graph

**Verification — every spec_file ref must resolve:**
```bash
grep "spec_file:" planning/dags/DAG.yaml | awk '{print $2}' | tr -d '"' | while read f; do
  [ -f "$f" ] && echo "OK: $f" || echo "MISSING: $f"
done
```

If any are MISSING, STOP and fix before proceeding.

## Step 4: Update INDEX.md

Read `planning/INDEX.md`. Add or update the spec links section so agents
can find their assigned specs.

## Step 5: Commit

Stage all materialized artifacts together:
```bash
git add planning/dags/DAG.yaml planning/specs/spec_*.md planning/INDEX.md
```

Write commit message to `.github/tmp/commit.txt`:
```
chore(planning): materialize DAG + N specs for <plan name>
```

Commit:
```bash
git commit -F .github/tmp/commit.txt
```

## Step 6: Report

Print a summary:
- Number of specs generated (must match task count in plan)
- DAG task count and group count
- All spec_file refs verified (OK / MISSING)
- Commit SHA

State: "Materialization complete. Ready for execution."

## Rules

- NEVER begin execution (dispatching agents, editing source files) during
  this command. Materialization is planning infrastructure only.
- NEVER skip the purge step. Old specs from prior plans must not persist.
- NEVER invent scope, files, or instructions beyond what the plan defines.
  The plan is the single source of truth for materialization.
- If the plan is ambiguous or incomplete, ask the user — do not guess.
