---
task_id: "T02"
task_name: "Update log-bash.sh — path + project field"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope:
  - "scripts/hooks/log-bash.sh"
read_scope: []
category: "C"
---

# Spec: Update log-bash.sh — path + project field

## Objective

Move the bash audit log from `~/.claude/bash-audit.log` to
`~/Projects/tp-claude-logs/bash-audit.log`. Add a `project=` field.

## Instructions

1. Read `scripts/hooks/log-bash.sh`.

2. Replace line 8 (`LOG="$HOME/.claude/bash-audit.log"`) with:
   ```bash
   LOGDIR="$HOME/Projects/tp-claude-logs"
   mkdir -p "$LOGDIR"
   LOG="$LOGDIR/bash-audit.log"
   ```

3. After the existing variable extractions (after the `DESC=` line, ~line 17),
   add:
   ```bash
   PROJECT="$(basename "$(git rev-parse --show-toplevel 2>/dev/null || echo unknown)")"
   ```

4. Replace the record block (lines 22–28) with:
   ```bash
   {
     printf '[%s] session=%s agent=%s type=%s project=%s\n' \
       "$TIMESTAMP" "$SESSION" "$AGENT" "$AGENT_TYPE" "$PROJECT"
     [[ -n "$DESC" ]] && printf '  desc: %s\n' "$DESC"
     printf '  cmd:  %s\n' "$CMD_ONELINE"
     printf -- '---\n'
   } >> "$LOG"
   ```

5. Update the header comment (line 5) from `~/.claude/bash-audit.log` to
   `~/Projects/tp-claude-logs/bash-audit.log`.

6. `git add scripts/hooks/log-bash.sh`. Do NOT commit.

## Verification

- `grep "tp-claude-logs" scripts/hooks/log-bash.sh` matches the LOGDIR line
- `grep "project=" scripts/hooks/log-bash.sh` matches the printf line
- No remaining references to `~/.claude/bash-audit.log`
