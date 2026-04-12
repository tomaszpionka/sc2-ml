---
task_id: "T10"
task_name: "Write check_planning_drift.py + tests"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG03"
file_scope:
  - "scripts/hooks/check_planning_drift.py"
  - "tests/infrastructure/test_check_planning_drift.py"
read_scope:
  - "scripts/hooks/check_phases_drift.py"
category: "C"
---

# Spec: Write check_planning_drift.py + tests

## Objective

Create the pre-commit validation script for planning artifacts.

## Instructions

1. Create `scripts/hooks/check_planning_drift.py` (stdlib only, ~150 lines).
2. Validation logic when `planning/` files are staged:
   - `current_plan.md`: Parse YAML frontmatter (category, branch, date
     required). Check required sections (case-insensitive heading match):
     - Universal (all categories): `## Scope`, `## Execution Steps`,
       `## File Manifest`, `## Suggested Execution Graph`
     - Category A/F only: also `## Problem Statement`,
       `## Assumptions & unknowns`, `## Literature context`,
       `## Gate Condition`, `## Open questions`
     - Category B/D: `## Problem Statement` recommended but not enforced
     - Category C/E: `## Problem Statement` not enforced
     (Match section names from `docs/templates/plan_template.md`.)
     **Bootstrap tolerance:** If the plan has markdown-bold metadata instead
     of YAML frontmatter (legacy format), warn but do not block. Add a
     `# TODO: enforce strict YAML frontmatter after this PR` comment.
   - `specs/spec_*.md`: Parse YAML frontmatter (task_id, task_name, agent,
     dag_ref, group_id, file_scope, category). Check required sections:
     `## Objective`, `## Instructions`, `## Verification`. (`## Context`
     is optional — document this in the script docstring.)
   - `dags/DAG.yaml`: Valid YAML. Required fields: dag_id, plan_ref,
     category, branch, base_ref. Every task has spec_file, file_scope,
     depends_on. All spec_file refs resolve to files on disk.
   - Cross-file: every spec_file in DAG has a matching spec; every spec on
     disk is referenced in the DAG (no orphans).
3. Follow `check_phases_drift.py` pattern: regex extraction, clear error
   messages, exit 1 on failure, stdlib only.
4. Add tests: `tests/infrastructure/test_check_planning_drift.py` — test
   valid/invalid plan frontmatter, missing spec sections, broken DAG refs,
   legacy (non-YAML) plan frontmatter warns but passes.

## Verification

- Script catches missing sections in plans
- Script catches broken spec_file refs in DAGs
- Script catches orphaned spec files
- Tests pass

## Context

Note: `scripts/hooks/check_phases_drift.py` may have been deleted by T04
before this task runs. If so, read it from git history for the pattern
reference: `git show HEAD~1:scripts/hooks/check_phases_drift.py`
