---
task_id: "T11"
task_name: "Wire pre-commit hook"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG03"
file_scope:
  - ".pre-commit-config.yaml"
read_scope: []
category: "C"
---

# Spec: Wire pre-commit hook

## Objective

Add the planning-drift hook to `.pre-commit-config.yaml`.

## Instructions

1. Add to `.pre-commit-config.yaml` (in the local hooks section):
   ```yaml
   - repo: local
     hooks:
       - id: planning-drift
         name: planning artifact validation
         language: system
         entry: python scripts/hooks/check_planning_drift.py
         files: ^planning/
         pass_filenames: false
   ```
2. Verify the `phases-drift` hook was already removed by T04. If it is
   still present, remove it now.
3. Test: stage a spec with missing `## Objective` section, verify the hook
   blocks the commit. Restore the spec after testing.

## Verification

- `pre-commit run planning-drift` passes on valid planning artifacts
- Blocks on invalid ones (missing sections, broken refs)
- `phases-drift` hook is absent from `.pre-commit-config.yaml`
