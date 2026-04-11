---
task_id: "T03"
task_name: "Update hooks README"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope:
  - "scripts/hooks/README.md"
read_scope: []
category: "C"
---

# Spec: Update hooks README

## Objective

Update all path references and format examples in `scripts/hooks/README.md` to
reflect the new log locations.

## Instructions

1. Read `scripts/hooks/README.md`.

2. **log-bash.sh section:**
   - Change `~/.claude/bash-audit.log` to `~/Projects/tp-claude-logs/bash-audit.log`
     everywhere (description line and all "Useful commands" examples).
   - Update description to note it includes a `project=` field.
   - Update the format example to include `project=rts-outcome-prediction`.

3. **log-subagent.sh section:**
   - Change `/tmp/rts-agent-log.txt` to `~/Projects/tp-claude-logs/agent-audit.log`
     everywhere (description line and all "Useful commands" examples).
   - Update side files line to: `/tmp/tp-claude-logs/sessions-seen.txt`,
     `/tmp/tp-claude-logs/sessions-counts.txt`.
   - Change "cleared on reboot" to "persistent across reboots".
   - Update all format examples to include `project=rts-outcome-prediction`.

4. `git add scripts/hooks/README.md`. Do NOT commit.

## Verification

- `grep -c "tp-claude-logs" scripts/hooks/README.md` returns ≥10
- No remaining references to `/tmp/rts-agent-log.txt` or `~/.claude/bash-audit.log`
- Format examples show `project=` field
