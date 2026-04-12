---
task_id: "T03"
task_name: "Strategy A/B: formalize in TAXONOMY.md + update pointers"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope:
  - "docs/TAXONOMY.md"
  - "docs/agents/AGENT_MANUAL.md"
  - "planning/README.md"
read_scope:
  - "docs/templates/dag_template.yaml"
category: "C"
---

# Spec: Strategy A/B — formalize in TAXONOMY.md + update pointers

## Objective

Add formal Strategy A (shared branch) and Strategy B (worktree isolation)
definitions to TAXONOMY.md. Update AGENT_MANUAL.md and planning/README.md
to use the formal terms and point to TAXONOMY.md.

## Instructions

1. Read `docs/TAXONOMY.md`, `docs/agents/AGENT_MANUAL.md`, and `planning/README.md`.

2. **TAXONOMY.md** — add a `### Parallel execution strategies` subsection
   under the existing operational terms area (after the DAG/Job/Task Group/Task
   definitions). Content:

   - **Strategy A (shared branch):** All parallel executors work on the same
     branch. Executors do NOT run `git add/commit` — the parent orchestrator
     stages and commits after each task group. Use when file scopes don't
     overlap. DAG field: `default_isolation: "shared_branch"`.
   - **Strategy B (worktree isolation):** Each executor runs in a temporary
     git worktree via `isolation: "worktree"`. Changes are merged back by
     the orchestrator. Use when file scopes overlap or executors need
     independent git state. DAG field: task-level `isolation: "worktree"`.

3. **AGENT_MANUAL.md** — find Workflow E (Parallel Spec Execution, around
   lines 310-315). Replace informal "Two strategies" phrasing with the
   formal **Strategy A** / **Strategy B** names. Add a pointer:
   `See docs/TAXONOMY.md for formal definitions.`

4. **planning/README.md** — find the existing reference to parallel execution
   (around line 16). Update to include: `See docs/TAXONOMY.md for
   Strategy A/B definitions.`

## Verification

1. `grep -rn "Strategy A" docs/ planning/` shows hits in TAXONOMY.md,
   AGENT_MANUAL.md, and planning/README.md.
2. `grep -rn "Strategy B" docs/ planning/` shows the same files.
3. No definition drift — TAXONOMY.md is the single source, others point to it.
