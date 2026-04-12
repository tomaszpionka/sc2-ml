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
  A review gate MAY run after a group completes, if configured (opt-in).
- **Task:** Single agent invocation. Parallel within a group when `parallel_safe: true`
  and `file_scope` does not overlap.

## Commit strategy

One commit per task group, orchestrated by the parent session:
1. All tasks in the group complete.
2. Parent stages all changes.
3. Parent creates one commit for the group.
4. Review gate runs against the group's diff.

## Review gates

Review gates are opt-in per task group. Add one only at cascade risk
boundaries where a bad result would contaminate downstream work. The
DAG-level `final_review` is the standard quality gate.

Final reviewer by category:
- **Cat A/F** (science + thesis): `reviewer-adversarial`
- **Cat B/C/D/E** (all other): `reviewer` (Sonnet)

## Model assignment

Specify a `model` field on each task to control which model tier is used:

- **`"haiku"`** — ONLY when ALL of these hold:
  1. All content is provided verbatim in the spec (no synthesis)
  2. No judgment calls (no "decide if X is interpretive")
  3. No negative constraints ("don't use words like...")
  4. No artifact reading + prose writing
  5. No code changes
- **`"sonnet"`** — DEFAULT for most executor tasks
- **`"opus"`** — when task requires:
  1. Multi-file reasoning across >5 files
  2. Novel methodology decisions
  3. Complex constraint satisfaction (thesis chapters)

Omit `model` to inherit from the parent session.

## Spec consolidation

Combine tasks into fewer specs when they share `read_scope` or operate
on the same logical pattern (e.g., 3 datasets). One executor with a
bigger spec is cheaper than three executors that each re-read the same
files. Use parameterized dataset tables for multi-dataset work.

## Failure policy

All failures halt the DAG. The user decides next action in the session.
No automatic retries.
