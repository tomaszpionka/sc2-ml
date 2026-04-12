---
task_id: "<T01, T02, etc.>"
task_name: "<descriptive name>"
agent: "<executor | reviewer | reviewer-deep | reviewer-adversarial | writer-thesis>"
model: "<haiku | sonnet | opus — optional, omit to inherit>"
dag_ref: "planning/dags/DAG.yaml"
group_id: "<TG01, TG02, etc.>"
file_scope:
  - "<files this task writes>"
read_scope:
  - "<files this task reads from other tasks>"
datasets: []  # Optional — for parameterized multi-dataset specs
category: "<A-F>"
---

# Spec: <task_name>

## Objective

<1-3 sentences: what this task accomplishes>

## Instructions

<Numbered steps for the agent to execute. Be specific about:
- Which files to create or modify
- Function signatures (for code tasks)
- SQL queries (for data tasks)
- Expected outputs>

## Verification

<How to verify this task completed correctly:
- Commands to run (pytest, ruff, mypy)
- Files that must exist
- Conditions that must hold>

## Context

<Any additional context the agent needs:
- Links to relevant docs or templates
- Dependencies from prior tasks
- Constraints from scientific invariants (if Category A)>
