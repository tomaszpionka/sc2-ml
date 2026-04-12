---
task_id: "T04"
task_name: "Delete phase derivatives + drift hook"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope:
  - "docs/ml_experiment_phases/PHASES.md"
  - "docs/ml_experiment_phases/PIPELINE_SECTIONS.md"
  - "docs/ml_experiment_phases/README.md"
  - "scripts/hooks/check_phases_drift.py"
  - ".pre-commit-config.yaml"
read_scope: []
category: "C"
---

# Spec: Delete phase derivatives + drift hook

## Objective

Eliminate drift between `docs/PHASES.md` (canonical, Tier 3) and its
derivatives in `docs/ml_experiment_phases/`. The derivatives are subsets
of canonical content with silent structural drift that the hook only
partially detects.

## Instructions

1. Delete `docs/ml_experiment_phases/PHASES.md` — derivative subset of
   `docs/PHASES.md`, adds no unique content.
2. Delete `docs/ml_experiment_phases/PIPELINE_SECTIONS.md` — derivative
   copy of Pipeline Section tables already in `docs/PHASES.md`.
3. Keep `docs/ml_experiment_phases/STEPS.md` — contains unique content
   (Step contract, schema, numbering convention) not found in
   `docs/PHASES.md`.
4. Delete `scripts/hooks/check_phases_drift.py` — no longer needed.
5. Remove the `phases-drift` hook entry from `.pre-commit-config.yaml`.
   (Only remove the phases-drift hook. Do not touch other hooks.)
6. Create `docs/ml_experiment_phases/README.md`:
   ```
   # ML Experiment Phases — Supplementary Reference

   Phase and Pipeline Section definitions live in `docs/PHASES.md` (Tier 3).
   This directory contains only `STEPS.md` (Step contract and schema).
   ```

## Verification

- `docs/ml_experiment_phases/PHASES.md` does not exist
- `docs/ml_experiment_phases/PIPELINE_SECTIONS.md` does not exist
- `docs/ml_experiment_phases/STEPS.md` exists (untouched)
- `scripts/hooks/check_phases_drift.py` does not exist
- `pre-commit run --all-files` passes (no missing hook)
- `docs/PHASES.md` unchanged (zero edits to the canonical source)
