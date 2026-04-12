---
task_id: "T13"
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

Document the research log decentralization.

## Instructions

1. Under `[Unreleased]`, add:
   - Added: 3 per-dataset `research_log.md` files (sc2egset, aoe2companion,
     aoestats) with migrated Step 01_01_01 findings
   - Changed: `reports/research_log.md` rewritten as index + CROSS entries
   - Changed: ~25 files updated to reference per-dataset logs instead of
     unified log

## Verification

- CHANGELOG has entries under `[Unreleased]`
- All 3 actions (Added, Changed x2) present
