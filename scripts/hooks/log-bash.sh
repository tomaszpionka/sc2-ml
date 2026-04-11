#!/usr/bin/env bash
# log-bash.sh — PreToolUse hook: log every Bash invocation for audit/observability.
# Fires before execution; always exits 0 so it never blocks the command.
#
# Log location: ~/.claude/bash-audit.log  (persistent across reboots, global to all projects)
# Format: structured text, one record per separator block, human- and grep-readable.

LOG="$HOME/.claude/bash-audit.log"

INPUT=$(cat)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

SESSION=$(   echo "$INPUT" | jq -r '.session_id             // "unknown"')
AGENT=$(     echo "$INPUT" | jq -r '.agent_id               // "unknown"')
AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type             // "root"')
CMD=$(       echo "$INPUT" | jq -r '.tool_input.command     // ""')
DESC=$(      echo "$INPUT" | jq -r '.tool_input.description // ""')

# Inline the command (replace literal newlines with ↵) for the single-line header.
CMD_ONELINE=$(printf '%s' "$CMD" | tr '\n' '↵')

{
  printf '[%s] session=%s agent=%s type=%s\n' \
    "$TIMESTAMP" "$SESSION" "$AGENT" "$AGENT_TYPE"
  [[ -n "$DESC" ]] && printf '  desc: %s\n' "$DESC"
  printf '  cmd:  %s\n' "$CMD_ONELINE"
  printf -- '---\n'
} >> "$LOG"

exit 0
