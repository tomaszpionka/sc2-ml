---
task_id: "T01"
task_name: "Update log-subagent.sh — paths + project field"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG01"
file_scope:
  - "scripts/hooks/log-subagent.sh"
read_scope: []
category: "C"
---

# Spec: Update log-subagent.sh — paths + project field

## Objective

Move the audit log to `~/Projects/tp-claude-logs/` (persistent) and ephemeral
state files to `/tmp/tp-claude-logs/`. Add a `project=` field to every log line.

## Instructions

1. Read `scripts/hooks/log-subagent.sh`.

2. Replace the 4 scattered path assignments (lines 4, 29, 39, 40) with two
   directory groups:

   ```bash
   # Persistent audit log
   LOGDIR="$HOME/Projects/tp-claude-logs"
   mkdir -p "$LOGDIR"
   LOG="$LOGDIR/agent-audit.log"

   # Ephemeral per-boot state (intentionally in /tmp/)
   STATEDIR="/tmp/tp-claude-logs"
   mkdir -p "$STATEDIR"
   SESSIONS_SEEN="$STATEDIR/sessions-seen.txt"
   COUNTS_FILE="$STATEDIR/sessions-counts.txt"
   LOCK_DIR="$STATEDIR/sessions-counts.lock"
   ```

   Place the `LOGDIR`/`LOG` block at line 4 (replacing the old `LOG=` line).
   Place the `STATEDIR` block where `SESSIONS_SEEN` was first assigned (~line 29),
   replacing the 3 individual assignments scattered across lines 29, 39, 40.

3. After the existing variable extractions (after the `TRANSCRIPT=` line,
   ~line 13), add:
   ```bash
   PROJECT="$(basename "$(git rev-parse --show-toplevel 2>/dev/null || echo unknown)")"
   ```

4. Append `project=$PROJECT` to every `echo "[$TIMESTAMP] ..."` line:
   - SessionOpen (~line 34): `... orchestrator=$MODEL project=$PROJECT`
   - SubagentStart (~line 82): `... model=$MODEL project=$PROJECT`
   - SubagentStop lines (~lines 85, 87): `... project=$PROJECT` at end
   - SessionClose (~line 93): `... total_agents=$STARTED project=$PROJECT`

5. Do NOT change anything else — model lookup, token aggregation, lock logic.

6. Update the header comment (line 3) to reference the new log location.

7. `git add scripts/hooks/log-subagent.sh`. Do NOT commit.

## Verification

- `grep -c "tp-claude-logs" scripts/hooks/log-subagent.sh` returns ≥2
  (LOGDIR + STATEDIR)
- `grep -c "project=" scripts/hooks/log-subagent.sh` returns ≥4
  (SessionOpen + Start + Stop + Close)
- No remaining references to `/tmp/rts-agent-log.txt` or `/tmp/rts-sessions-`
