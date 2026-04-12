# .claude — Routing Index

## Agents

| File | Load trigger |
|---|---|
| `agents/executor.md` | Dispatched by orchestrator for any code/data execution task |
| `agents/planner.md` | Dispatched for planning sessions (Category A–F) |
| `agents/planner-science.md` | Dispatched for Category A (phase work) planning |
| `agents/reviewer.md` | Dispatched at review gates after each task group |
| `agents/reviewer-deep.md` | Dispatched for final review of standard DAGs |
| `agents/reviewer-adversarial.md` | Dispatched for final review of Category A / multi-job DAGs |
| `agents/writer-thesis.md` | Dispatched for Category F (thesis writing) tasks |
| `agents/lookup.md` | Dispatched for read-only fact-lookup sub-tasks |

## Rules

| File | Load trigger |
|---|---|
| `rules/python-code.md` | Auto-loaded on any `.py` file touch (Category B/C) |
| `rules/git-workflow.md` | Auto-loaded on PR/commit operations |
| `rules/thesis-writing.md` | Auto-loaded on `thesis/` file touch (Category F) |
| `rules/sql-data.md` | Auto-loaded on SQL or DuckDB work |

## Commands

| File | Load trigger |
|---|---|
| `commands/dag.md` | Invoked via `/dag` skill to generate `DAG.yaml` + specs |
| `commands/materialize_plan.md` | Invoked to materialize approved plan into DAG + specs |
| `commands/pr.md` | Invoked to create and submit a pull request |

## Cross-cutting Config

| File | Load trigger |
|---|---|
| `scientific-invariants.md` | Read before any Category A or D (data/feature) work |
| `ml-protocol.md` | Read before any model training or evaluation work |
| `dev-constraints.md` | Standing constraints; auto-enforced by executor |
| `settings.json` | Loaded by Claude Code at session start (model routing, permissions) |
| `settings.local.json` | Local overrides for settings.json; not committed |
| `thesis-formatting-rules.yaml` | Read by writer-thesis agent before any thesis output |
