#!/usr/bin/env bash
set -euo pipefail

LOG="/tmp/rts-agent-log.txt"
INPUT=$(cat)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# --- Robust per-field extraction (avoids @tsv field-shift anomaly) ---
EVENT=$(echo "$INPUT"      | jq -r '.hook_event_name       // "unknown"')
SESSION=$(echo "$INPUT"    | jq -r '.session_id            // "unknown"')
AGENT=$(echo "$INPUT"      | jq -r '.agent_id              // "unknown"')
AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type            // "unknown"')
TRANSCRIPT=$(echo "$INPUT" | jq -r '.agent_transcript_path // "none"')

# --- Model lookup from agent_type ---
case "$AGENT_TYPE" in
  planner-science)  MODEL="claude-opus-4-6"           ;;
  executor)         MODEL="claude-sonnet-4-6"         ;;
  planner)          MODEL="claude-sonnet-4-6"         ;;
  reviewer)         MODEL="claude-sonnet-4-6"         ;;
  lookup)           MODEL="claude-haiku-4-5-20251001" ;;
  *)                MODEL="claude-sonnet-4-6"         ;;
esac

# --- SessionOpen: emit once per session on first SubagentStart ---
SESSIONS_SEEN="/tmp/rts-sessions-seen.txt"
touch "$SESSIONS_SEEN"
if [[ "$EVENT" == "SubagentStart" ]]; then
  if ! grep -qF "$SESSION" "$SESSIONS_SEEN"; then
    echo "$SESSION" >> "$SESSIONS_SEEN"
    echo "[$TIMESTAMP] SessionOpen   session=$SESSION orchestrator=$MODEL" >> "$LOG"
  fi
fi

# --- SessionClose: track started/stopped counts per session ---
COUNTS_FILE="/tmp/rts-sessions-counts.txt"
LOCK_DIR="/tmp/rts-sessions-counts.lock"
touch "$COUNTS_FILE"

# Portable atomic lock via mkdir (works on macOS without flock)
LOCK_WAIT=0
until mkdir "$LOCK_DIR" 2>/dev/null; do
  sleep 0.1
  LOCK_WAIT=$(( LOCK_WAIT + 1 ))
  [[ $LOCK_WAIT -ge 20 ]] && break
done

LINE=$(grep -F "$SESSION" "$COUNTS_FILE" 2>/dev/null || printf '%s\t0\t0' "$SESSION")
STARTED=$(echo "$LINE" | cut -f2)
STOPPED=$(echo "$LINE" | cut -f3)

[[ "$EVENT" == "SubagentStart" ]] && STARTED=$(( STARTED + 1 ))
[[ "$EVENT" == "SubagentStop"  ]] && STOPPED=$(( STOPPED + 1 ))

{ grep -vF "$SESSION" "$COUNTS_FILE" 2>/dev/null || true
  printf '%s\t%s\t%s\n' "$SESSION" "$STARTED" "$STOPPED"
} > "${COUNTS_FILE}.tmp" && mv "${COUNTS_FILE}.tmp" "$COUNTS_FILE"

rmdir "$LOCK_DIR" 2>/dev/null || true

# --- Token aggregation from transcript JSONL (SubagentStop only) ---
IN_TOKENS="unavailable"
OUT_TOKENS="unavailable"
CACHE_READ="unavailable"

if [[ "$EVENT" == "SubagentStop" && "$TRANSCRIPT" != "none" && -f "$TRANSCRIPT" ]]; then
  USAGE=$(jq -s '{
    in:  ([.[].message.usage.input_tokens                // 0] | add // 0),
    out: ([.[].message.usage.output_tokens               // 0] | add // 0),
    cr:  ([.[].message.usage.cache_read_input_tokens     // 0] | add // 0)
  }' "$TRANSCRIPT" 2>/dev/null) || USAGE='{"in":0,"out":0,"cr":0}'
  IN_TOKENS=$(echo "$USAGE"  | jq -r '.in')
  OUT_TOKENS=$(echo "$USAGE" | jq -r '.out')
  CACHE_READ=$(echo "$USAGE" | jq -r '.cr')
fi

# --- Emit log line ---
if [[ "$EVENT" == "SubagentStart" ]]; then
  echo "[$TIMESTAMP] SubagentStart session=$SESSION agent=$AGENT type=$AGENT_TYPE model=$MODEL" >> "$LOG"
elif [[ "$EVENT" == "SubagentStop" ]]; then
  if [[ "$IN_TOKENS" == "unavailable" ]]; then
    echo "[$TIMESTAMP] SubagentStop  session=$SESSION agent=$AGENT type=$AGENT_TYPE model=$MODEL tokens=unavailable" >> "$LOG"
  else
    echo "[$TIMESTAMP] SubagentStop  session=$SESSION agent=$AGENT type=$AGENT_TYPE model=$MODEL in=$IN_TOKENS out=$OUT_TOKENS cache_read=$CACHE_READ" >> "$LOG"
  fi
fi

# --- SessionClose: emit after stop count reaches start count ---
if [[ "$EVENT" == "SubagentStop" && "$STARTED" -gt 0 && "$STOPPED" -ge "$STARTED" ]]; then
  echo "[$TIMESTAMP] SessionClose  session=$SESSION total_agents=$STARTED" >> "$LOG"
fi
