---
task_id: "T04"
task_name: "Migrate old logs — stage, prepend, cleanup"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope: []
read_scope: []
category: "C"
depends_on: ["T01", "T02"]
---

# Spec: Migrate old logs — stage, prepend, cleanup

## Objective

Move existing log data from old locations into the new
`~/Projects/tp-claude-logs/` directory, preserving chronological order. Old
data must appear BEFORE (on top of) any new entries that landed after the hooks
were updated.

## Instructions

1. Ensure `~/Projects/tp-claude-logs/` exists (the updated hooks create it, but
   be defensive):
   ```bash
   mkdir -p ~/Projects/tp-claude-logs
   ```

2. **Stage old logs with `_old` suffix:**
   ```bash
   cp /tmp/rts-agent-log.txt ~/Projects/tp-claude-logs/agent-audit_old.log 2>/dev/null || true
   cp ~/.claude/bash-audit.log ~/Projects/tp-claude-logs/bash-audit_old.log 2>/dev/null || true
   ```

3. **Prepend old data into the live logs** (old on top, new below):
   ```bash
   # agent-audit
   if [ -f ~/Projects/tp-claude-logs/agent-audit_old.log ]; then
     cat ~/Projects/tp-claude-logs/agent-audit_old.log \
         ~/Projects/tp-claude-logs/agent-audit.log 2>/dev/null \
         > ~/Projects/tp-claude-logs/agent-audit_merged.log \
       && mv ~/Projects/tp-claude-logs/agent-audit_merged.log \
             ~/Projects/tp-claude-logs/agent-audit.log
   fi

   # bash-audit
   if [ -f ~/Projects/tp-claude-logs/bash-audit_old.log ]; then
     cat ~/Projects/tp-claude-logs/bash-audit_old.log \
         ~/Projects/tp-claude-logs/bash-audit.log 2>/dev/null \
         > ~/Projects/tp-claude-logs/bash-audit_merged.log \
       && mv ~/Projects/tp-claude-logs/bash-audit_merged.log \
             ~/Projects/tp-claude-logs/bash-audit.log
   fi
   ```

   Edge case: if the live log does not yet exist (no hook has fired), `cat`
   copies the old file as-is. This is correct.

4. **Clean up staging files:**
   ```bash
   rm -f ~/Projects/tp-claude-logs/agent-audit_old.log
   rm -f ~/Projects/tp-claude-logs/bash-audit_old.log
   ```

5. **Verify chronological order:**
   ```bash
   head -1 ~/Projects/tp-claude-logs/agent-audit.log
   tail -1 ~/Projects/tp-claude-logs/agent-audit.log
   ```
   First line should be older than last line.

6. Nothing to `git add` — this task modifies files outside the repo.

## Verification

- `~/Projects/tp-claude-logs/agent-audit.log` exists and is non-empty
- `~/Projects/tp-claude-logs/bash-audit.log` exists and is non-empty
- No `*_old.log` or `*_merged.log` staging files remain
- First line of agent-audit.log is from Apr 11 or earlier (old data)
- No remaining data in `/tmp/rts-agent-log.txt` that is absent from the new log
