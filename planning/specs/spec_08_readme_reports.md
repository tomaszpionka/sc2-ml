---
task_id: "T08"
task_name: "Create reports/README.md"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG02"
file_scope:
  - "reports/README.md"
read_scope: []
category: "C"
---

# Spec: Create reports/README.md

## Objective

Add routing README for reports directory reflecting the per-dataset
structure from the research log split.

## Instructions

1. `reports/README.md`: Describe root as index + CROSS entries only.
   Per-dataset reports at `src/rts_predict/<game>/reports/<dataset>/`.
   Link to research_log_template.yaml.

## Verification

- File exists
- Describes the post-split structure (index + CROSS at root, per-dataset logs)
