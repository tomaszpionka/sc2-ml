---
task_id: "T06"
task_name: "Update reviewer-deep.md + reviewer-adversarial.md"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG02"
file_scope:
  - ".claude/agents/reviewer-deep.md"
  - ".claude/agents/reviewer-adversarial.md"
read_scope: []
category: "C"
---

# Spec: Update reviewer-deep.md + reviewer-adversarial.md

## Objective

Reviewers read the active dataset's log + root CROSS log.

## Instructions

1. reviewer-deep.md Required Reading item 7: "Read `reports/research_log.md`
   recent entries" → "Read the active dataset's `research_log.md` and
   `reports/research_log.md` (CROSS entries) — check for contradictions
   with prior findings in both"
2. reviewer-adversarial.md: same pattern for its research_log reference.

## Verification

- Both files reference dataset log + root CROSS log
- No bare `reports/research_log.md` as sole source for findings
