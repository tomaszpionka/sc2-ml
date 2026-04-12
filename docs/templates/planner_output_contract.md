# Planner output contract

You are a planner agent. Your job is to **describe**, not execute.
Empirical investigation during planning is prohibited.

This contract applies to all planner agents (e.g., planner-science, any
general-purpose Claude session acting in a planning role). Agent identity
does not change the output schema.

## Required output

Every planning invocation MUST produce ONE file:

1. `planning/current_plan.md` — conforms to `docs/templates/plan_template.md`

The critique (`planning/current_plan.critique.md`) is NOT the planner's
responsibility. After producing the plan, instruct the parent session:

> "For Category A or F, adversarial critique is required before
> materialization. Dispatch reviewer-adversarial to produce
> `planning/current_plan.critique.md`."

For Category B, C, D, and E, no critique instruction is needed unless the
category-specific rule below requires one.

## Conditional requirements by category

`category` is a required frontmatter field in `planning/current_plan.md`.
Use the table below to determine which plan sections are required and whether
a critique must be requested.

| Category | Plan sections required | Critique required? |
|----------|-----------------------|-------------------|
| A | Scope, Problem Statement, Assumptions & unknowns, Literature context, Execution Steps, File Manifest, Gate Condition, Out of scope, Open questions, Suggested Execution Graph | yes — instruct parent to dispatch reviewer-adversarial, all sections |
| B | Scope, Execution Steps, File Manifest, Suggested Execution Graph, Out of scope | yes — instruct parent to dispatch reviewer-adversarial; invariants + weaknesses sections only |
| C | Scope, Execution Steps, File Manifest, Suggested Execution Graph | no |
| D | Scope, Execution Steps, File Manifest, Suggested Execution Graph, Out of scope | yes if `file_scope` touches `src/rts_predict/games/<game>/` — instruct parent to dispatch reviewer-adversarial |
| E | Scope, Execution Steps, File Manifest, Suggested Execution Graph | no |
| F | Scope, Problem Statement, Assumptions & unknowns, Literature context, Execution Steps, File Manifest, Gate Condition, Out of scope, Open questions, Suggested Execution Graph | yes — instruct parent to dispatch reviewer-adversarial, all sections |

For Category C and E, produce only `current_plan.md`. Do not mention the
critique at all.

## Execution Steps structure

Each task in the Execution Steps section uses this rigid structure (matching
`docs/templates/plan_template.md`). The executor extracts each block into a
spec file with minimal interpretation.

```
### TNN — <task name>

**Objective:** <1–3 sentences describing what this task achieves and why.>

**Instructions:**
1. <Numbered step — concrete, unambiguous action>
2. <Next step>

**Verification:**
- <Command or observable condition that confirms success>

**File scope:** <Files this task WRITES — maps to `file_scope` in spec YAML>
- `path/to/file.py`

**Read scope:** <Files this task READS that are outputs of sibling tasks — maps to `read_scope` in spec YAML>
- `path/to/other_task_output.py`
```

Tasks are numbered sequentially: T01, T02, T03, … Every task number (TNN)
must appear exactly once in the Execution Steps and exactly once in the
Suggested Execution Graph.

## Suggested Execution Graph

Every plan must include a `Suggested Execution Graph` section containing a
fenced YAML block that conforms to `docs/templates/dag_template.yaml`.

Minimum requirements for each task entry in the graph:

- `task_id` — matches a TNN in Execution Steps
- `spec_file` — `planning/specs/spec_NN_<slug>.md`
- `file_scope` — list of files the task writes
- `parallel_safe` — `true` only if `file_scope` does not overlap any sibling task
- `depends_on` — list of task IDs this task blocks on, or `[]`

## Forbidden terms

The following words MUST NOT be used as load-bearing work-unit names
(per `docs/TAXONOMY.md`):

- Stage
- Experiment (formal work unit)
- Milestone
- Workstream, Track, Initiative, Epic
- Component (work unit)
- Section (unqualified — use "Pipeline Section", "thesis section", or "manual section")

The word **"task"** is NOT forbidden. Use it freely to refer to Tasks (T01,
T02, …) in the DAG.

## Hard rules

- `category` must be one of A, B, C, D, E, F.
- `branch` must use the prefix matching the category convention (see `docs/TAXONOMY.md`).
- `source_artifacts` must be non-empty for Category A and F — planning without
  inputs is speculation.
- `invariants_touched` must be populated for Category A and F; use `[]` for
  B–E unless data or model code is touched.
- Every task in the DAG must have `spec_file`, `file_scope`, `parallel_safe`,
  and `depends_on`.
- Every TNN in Execution Steps must map to a task in the Suggested Execution
  Graph, and vice versa.
- The File Manifest must list every file that any task creates, rewrites,
  updates, or deletes. No file may be touched by an executor task if it is
  absent from the manifest.
- If you cannot fill Execution Steps with concrete, unambiguous actions, STOP
  and tell the user what additional information is needed before planning can
  proceed.

## Self-check before returning

Before emitting `planning/current_plan.md`, verify:

- [ ] `category` is one of A–F (not a scope label)
- [ ] Suggested Execution Graph uses `jobs > task_groups > tasks` hierarchy
- [ ] Every task has `spec_file`, `file_scope`, `parallel_safe`, `depends_on`
- [ ] Every TNN in Execution Steps appears in the graph, and vice versa
- [ ] File Manifest is complete — every touched file is listed
- [ ] No forbidden taxonomy terms used as work-unit names
- [ ] `invariants_touched` populated for Category A/F
- [ ] For Category A/F: critique instruction included at end of plan

If any check fails, fix before returning. Do not ask the user to fix it.
