# Specs Directory

Task specs for the active plan in `planning/current_plan.md`. Each spec is a
self-contained brief for one executor agent — it reads only its spec file, not
the full plan.

## Lifecycle

1. **Materialized** from the approved plan (DAG + specs committed together)
2. **Consumed** during execution (agents read their assigned spec)
3. **Purged** after the PR merges (specs are ephemeral per-branch artifacts)

## Naming Convention

`spec_NN_<short_name>.md` — numbered to match `task_id` in `planning/dags/DAG.yaml`.

## Format

YAML frontmatter (`task_id`, `file_scope`, `read_scope`, `depends_on`) followed
by markdown instructions and verification checklist. See
`docs/templates/spec_template.md` for the schema.

## Current Specs

See `planning/dags/DAG.yaml` for the authoritative task-to-spec mapping.
