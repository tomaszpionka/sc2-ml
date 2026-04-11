# DAGs

Execution graphs for multi-agent orchestration.

## Files

| File | Lifecycle | Purpose |
|------|-----------|---------|
| `DAG.yaml` | Ephemeral | The single active execution graph |
| `DAG_STATUS.yaml` | Ephemeral (optional) | Execution state tracker |
| `README.md` | Permanent | This file |

## Format

See `docs/templates/dag_template.yaml` for the YAML schema.

A DAG consists of Jobs > Task Groups > Tasks:
- **Job:** Top-level container (usually one per DAG).
- **Task Group:** Ordered batch of tasks. Sequential between groups (via `depends_on`).
  A review gate runs automatically after each group completes.
- **Task:** Single agent invocation. Parallel within a group when `parallel_safe: true`
  and `file_scope` does not overlap.

## Commit strategy

One commit per task group, orchestrated by the parent session:
1. All tasks in the group complete.
2. Parent stages all changes.
3. Parent creates one commit for the group.
4. Review gate runs against the group's diff.

## Review gate defaults

- **Heavyweight groups** (any `.py`, `.ipynb`, SQL, or `src/`/`sandbox/` files):
  `reviewer-deep` (Opus)
- **Lightweight groups** (`.md`, `.yaml`, status files only):
  `reviewer` (Sonnet)
- **Final gate** (after all groups): `reviewer-adversarial` (Opus)

## Failure policy

All failures halt the DAG. The user decides next action in the session.
No automatic retries.
