---
task_id: "T12"
task_name: "Update CHANGELOG"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG04"
file_scope:
  - "CHANGELOG.md"
read_scope: []
category: "C"
---

# Spec: Update CHANGELOG

## Objective

Document all workstreams: token economy, directory indexing, phase
consolidation, and template enforcement.

## Instructions

1. Under `[Unreleased]`, add:
   - Changed: CLAUDE.md trimmed (~16 lines removed, dispatch rules preserved)
   - Changed: ARCHITECTURE.md trimmed (~18 lines, pointers replace duplication)
   - Changed: executor.md trimmed (~40 lines, data layout + notebook workflow
     replaced with pointers)
   - Added: 8 directory README.md files (routing documents)
   - Added: `docs/INDEX.md` directory map — centralized routing hub
   - Added: `scripts/hooks/check_planning_drift.py` pre-commit hook for
     planning artifact validation
   - Added: `tests/infrastructure/test_check_planning_drift.py`
   - Removed: `docs/ml_experiment_phases/PHASES.md` (derivative of canonical
     `docs/PHASES.md`)
   - Removed: `docs/ml_experiment_phases/PIPELINE_SECTIONS.md` (derivative)
   - Removed: `scripts/hooks/check_phases_drift.py` (no longer needed)

## Verification

- CHANGELOG has entries under `[Unreleased]`
- All workstreams represented (token economy, indexing, consolidation, enforcement)
