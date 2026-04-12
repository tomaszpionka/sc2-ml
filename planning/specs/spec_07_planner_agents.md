---
task_id: "T07"
task_name: "Update planner-science.md + ml-protocol.md"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG02"
file_scope:
  - ".claude/agents/planner-science.md"
  - ".claude/ml-protocol.md"
read_scope: []
category: "C"
---

# Spec: Update planner-science.md + ml-protocol.md

## Objective

Planner checks root CROSS log + sibling dataset logs for cross-dataset
coordination.

## Instructions

1. planner-science.md: "check `reports/research_log.md` for sibling
   decisions" → "check `reports/research_log.md` (CROSS entries) for
   cross-game decisions, and sibling dataset research logs if coordinating
   across datasets"
2. ml-protocol.md: update any `reports/research_log.md` references to
   per-dataset pattern.

## Verification

- Both files reference the new structure
- No bare `reports/research_log.md` as destination for dataset-specific entries
