---
task_id: "T05"
task_name: "Update CLAUDE.md + executor.md"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG02"
file_scope:
  - "CLAUDE.md"
  - ".claude/agents/executor.md"
read_scope: []
category: "C"
---

# Spec: Update CLAUDE.md + executor.md

## Objective

Update orchestrator and executor research_log references to per-dataset pattern.

## Instructions

1. CLAUDE.md: change "update `reports/research_log.md`" → "update the
   active dataset's `research_log.md`"
2. executor.md Category A rule (~line 70): change "Update `reports/research_log.md`
   after each step" → "Update the active dataset's `research_log.md` after each step"
3. executor.md notebook workflow (~line 102): change "Update `reports/research_log.md`
   with a new entry" → "Update the active dataset's `research_log.md` with a new entry"
4. executor.md: add rule: "If a finding has cross-game implications
   (Invariant #8), also add a [CROSS] entry to `reports/research_log.md`"

## Verification

- No bare `reports/research_log.md` as destination for dataset-specific entries
  in either file (CROSS context references are fine)
- executor.md has the Invariant #8 cross-game implication rule
