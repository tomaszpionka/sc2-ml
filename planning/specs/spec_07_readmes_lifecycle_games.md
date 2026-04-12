---
task_id: "T07"
task_name: "Create lifecycle + game READMEs"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG02"
file_scope:
  - "docs/ml_experiment_lifecycle/README.md"
  - "src/rts_predict/sc2/README.md"
  - "src/rts_predict/aoe2/README.md"
read_scope: []
category: "C"
---

# Spec: Create lifecycle + game READMEs

## Objective

Add routing READMEs for methodology manuals and game packages.

## Instructions

1. `docs/ml_experiment_lifecycle/README.md`: Note 6 manuals, one per Phase.
   Read order by Phase number. Each manual is self-contained.
2. `src/rts_predict/sc2/README.md`: CLI, config, data, reports paths.
   Dataset table with ROADMAP link and status.
3. `src/rts_predict/aoe2/README.md`: Same pattern. Note operational status
   (data acquisition functional, features/models not yet implemented).

## Verification

- All 3 files exist with routing tables
