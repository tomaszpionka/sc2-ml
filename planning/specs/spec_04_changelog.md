---
task_id: "T04"
task_name: "Update CHANGELOG for follow-up fixes"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG02"
file_scope:
  - "CHANGELOG.md"
read_scope: []
category: "C"
---

# Spec: Update CHANGELOG for follow-up fixes

## Objective

Add entries to the `[Unreleased]` section documenting the follow-up fixes
from TG01.

## Instructions

1. Read `CHANGELOG.md`.
2. Under `[Unreleased]`, add entries for:
   - **Added:** `test_main_integration_clean`, `test_main_integration_errors`,
     `test_absolute_spec_file_path`, `test_legacy_heuristic_false_positive`
     tests for planning drift hook
   - **Changed:** aoe2 README — added 4 per-dataset report/artifact path
     constants
   - **Changed:** `docs/TAXONOMY.md` — added Strategy A/B parallel execution
     definitions; `docs/agents/AGENT_MANUAL.md` and `planning/README.md`
     updated with formal terms
   - **Fixed:** `check_planning_drift.py` — absolute spec_file path handling
     in orphan detection

## Verification

1. `[Unreleased]` section has entries covering all 3 workstreams.
2. No duplication with existing entries.
