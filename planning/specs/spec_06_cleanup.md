---
task_id: "T06"
task_name: "Delete static reports, update CHANGELOG"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG03"
file_scope:
  - "CHANGELOG.md"
  - "session_audit.md"
  - "session_audit_plan.md"
read_scope: []
category: "C"
---

# Spec: Delete static reports, update CHANGELOG

## Objective

Remove the one-off static reports from the repo root and update CHANGELOG.

## Instructions

1. Delete `session_audit.md` (generated artifact, now produced on demand by
   `scripts/session_audit.py`).

2. Delete `session_audit_plan.md` (consumed into `planning/current_plan.md`).

3. Read `CHANGELOG.md`. Under `[Unreleased]`, add:

   **Added:**
   - `scripts/session_audit.py` — on-demand session audit dashboard (token usage,
     PR efficiency, subagent analysis)

   **Changed:**
   - `scripts/hooks/log-subagent.sh`: audit log moved to
     `~/Projects/tp-claude-logs/agent-audit.log`, ephemeral state to
     `/tmp/tp-claude-logs/`, added `project=` field
   - `scripts/hooks/log-bash.sh`: audit log moved from `~/.claude/bash-audit.log`
     to `~/Projects/tp-claude-logs/bash-audit.log`, added `project=` field

   **Removed:**
   - `session_audit.md` (replaced by `scripts/session_audit.py`)
   - 10 orphaned spec files from PR #108 (`planning/specs/spec_01` through `spec_10`)

4. `git add CHANGELOG.md` and `git rm session_audit.md session_audit_plan.md`.
   Do NOT commit.

## Verification

- `session_audit.md` does not exist at repo root
- `session_audit_plan.md` does not exist at repo root
- CHANGELOG `[Unreleased]` has Added, Changed, and Removed entries
