---
task_id: "T10"
task_name: "Update TAXONOMY.md + PHASES.md + STEPS.md"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG03"
file_scope:
  - "docs/TAXONOMY.md"
  - "docs/PHASES.md"
  - "docs/ml_experiment_phases/PHASES.md"
  - "docs/ml_experiment_phases/STEPS.md"
read_scope: []
category: "C"
---

# Spec: Update TAXONOMY.md + PHASES.md + STEPS.md

## Objective

Update phase/step references to per-dataset logs.

## Instructions

1. docs/TAXONOMY.md: "one entry in `reports/research_log.md`" → "one entry
   in the dataset's `research_log.md`"
2. docs/PHASES.md: Phase 07 exit gate → "per-dataset `research_log.md`
   entries are current and thesis-citable"; cross-dataset coordination →
   "tracked in `reports/research_log.md` CROSS entries"
3. docs/ml_experiment_phases/PHASES.md: same as docs/PHASES.md.
4. docs/ml_experiment_phases/STEPS.md: step output → "dataset's
   `research_log.md`"

## Verification

- All 4 files reference per-dataset logs for findings
- CROSS coordination references root `reports/research_log.md`
