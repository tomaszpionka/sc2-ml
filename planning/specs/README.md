# Specs Directory

Task specs for the active plan in `planning/current_plan.md`. Each spec is a
self-contained brief for one executor agent — it reads only its spec file, not
the full plan.

## Rules

1. **Specs always start from `spec_01`.** Numbering is per-plan, not cumulative
   across plans. Every new materialization starts at 01.
2. **Old specs are purged before new ones are created.** The first step of
   materialization deletes all `spec_*.md` files (keeps this README). Old specs
   belong to the prior plan and must not persist.
3. **One spec per DAG task.** The `spec_NN` number matches the `task_id` (T01 →
   spec_01, T02 → spec_02, etc.) in `planning/dags/DAG.yaml`.
4. **Specs are derived, not invented.** Content is extracted from
   `planning/current_plan.md`. If a spec diverges from the plan, the plan wins.

## Lifecycle

1. **Purge** — delete all `spec_*.md` from prior plan
2. **Materialize** — create new specs from approved plan (committed with DAG)
3. **Consume** — executors read their assigned spec during execution
4. **Purge** — after PR merges, purge protocol removes all specs again

## Naming Convention

`spec_NN_<short_name>.md` — numbered sequentially from 01, matching `task_id`
in `planning/dags/DAG.yaml`.

## Format

YAML frontmatter (`task_id`, `file_scope`, `read_scope`, `depends_on`) followed
by markdown instructions and verification checklist. See
`docs/templates/spec_template.md` for the schema.

## Current Specs

See `planning/dags/DAG.yaml` for the authoritative task-to-spec mapping.
