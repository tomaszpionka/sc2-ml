---
task_id: "T11"
task_name: "Update templates + research docs"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG03"
file_scope:
  - "docs/templates/research_log_template.yaml"
  - "docs/templates/step_template.yaml"
  - "docs/templates/research_log_entry_template.yaml"
  - "docs/templates/plan_template.md"
  - "docs/research/RESEARCH_LOG.md"
  - "docs/research/RESEARCH_LOG_ENTRY.md"
read_scope: []
category: "C"
---

# Spec: Update templates + research docs

## Objective

Update research log templates and specification docs to describe the
per-dataset structure.

## Instructions

1. `docs/templates/research_log_template.yaml`: add note that per-dataset
   logs follow this schema; root log is index-only with CROSS entries.
2. `docs/templates/step_template.yaml`: research_log_entry pointer →
   dataset's log.
3. `docs/templates/research_log_entry_template.yaml`: note that entries
   live in per-dataset logs.
4. `docs/templates/plan_template.md`: `research_log_ref` → clarify points
   to dataset's log.
5. `docs/research/RESEARCH_LOG.md`: update to describe new structure
   (index at root, per-dataset logs, CROSS entries).
6. `docs/research/RESEARCH_LOG_ENTRY.md`: update to reference per-dataset
   logs as the destination for entries.

## Verification

- All 6 files describe per-dataset structure
- No references directing dataset-specific entries to root log
