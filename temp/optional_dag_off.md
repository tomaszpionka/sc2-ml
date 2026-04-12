# Disable DAG Machinery — Analysis

Parked 2026-04-12. Resume when ready.

## Files that need changes

### Core enforcement (CLAUDE.md)
- **`CLAUDE.md`** lines 15, 43-69 — Critical Rules bullet about reading DAG.yaml, entire "Plan / Execute Workflow" section with DAG dispatch rules, spec pointer dispatch, final review dispatch. This is the main enforcement point.

### Templates
- **`docs/templates/plan_template.md`** lines 155-248 — The `## Suggested Execution Graph` section with full YAML schema. Every plan is required to include this.
- **`docs/templates/planner_output_contract.md`** lines 74-99 — Requires every plan to have the Execution Graph, every task to have `spec_file`, `file_scope`, `parallel_safe`, `depends_on`. Also in the self-check at lines 122-132 and hard rules at 109-115.

### Agent definitions
- **`.claude/agents/planner-science.md`** line 56 — "DAG requirement: Every plan MUST include a Suggested Execution Graph section..."
- **`.claude/agents/planner.md`** line 35 — Same DAG requirement constraint.
- **`.claude/agents/executor.md`** lines 25-28, 92-99 — Two dispatch paths: spec-based (DAG) and planless. The spec path reads spec files, echoes task_id, etc.

### Slash commands
- **`.claude/commands/materialize_plan.md`** — Entire file is the materialization command (plan → specs + DAG.yaml). 154 lines.
- **`.claude/commands/dag.md`** — Entire file is the DAG executor command (read DAG → dispatch agents → review gates). 111 lines.

### Planning README
- **`planning/README.md`** lines 5-6, 17-19, 25-48 — Lifecycle steps 2 (materialization) and 3 (execution) are DAG-centric. The contents table references `specs/`, `dags/DAG.yaml`, `dags/DAG_STATUS.yaml`.

### Memory index
- **`MEMORY.md`** has two DAG-related entries:
  - `feedback_dag_materialization_gate.md` — "always materialize DAG.yaml + specs BEFORE execution"
  - `feedback_dag_review_gates.md` — "intermediate TG reviews disabled; one final review"
  - (Both files don't exist at the expected path — may have been deleted or relocated)

### Test file (probably leave alone)
- **`tests/infrastructure/test_check_planning_drift.py`** — references DAG/specs in some structural test

## Proposed changes

1. **CLAUDE.md**: Replace DAG dispatch rules with simple "Execution: follow plan steps; user directs task splitting ad-hoc." Keep plan/execute two-session workflow.
2. **Plan template**: Wrap the Execution Graph section in `<!-- SUSPENDED -->` comment for easy re-enable.
3. **Output contract**: Remove DAG columns from required-sections table, remove Execution Graph section, soften hard rules.
4. **Planner agents**: Delete the DAG requirement constraint line from both planner-science.md and planner.md.
5. **Executor agent**: Keep only the "dispatched without a spec file" path (read `current_plan.md`).
6. **`/materialize_plan` + `/dag`**: Add a `SUSPENDED` banner at top so they short-circuit with a message.
7. **Planning README**: Simplify lifecycle — plan → approve → execute (no materialization step).
8. **Memory**: Remove the two stale DAG memory entries from `MEMORY.md`.
