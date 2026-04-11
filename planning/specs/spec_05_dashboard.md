---
task_id: "T05"
task_name: "Write scripts/session_audit.py"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG02"
file_scope:
  - "scripts/session_audit.py"
read_scope:
  - "session_audit.md"
  - "scripts/hooks/log-subagent.sh"
  - "scripts/hooks/log-bash.sh"
category: "C"
---

# Spec: Write scripts/session_audit.py

## Objective

Create a standalone dashboard script that reads session telemetry and PR data,
then prints a markdown report to stdout. Stdlib only — no pandas, no external
packages.

## Instructions

1. Read `session_audit.md` for the report structure to replicate.
2. Read the updated `scripts/hooks/log-subagent.sh` and `log-bash.sh` for log
   format and paths.

3. Create `scripts/session_audit.py` with:

   **CLI interface** (argparse):
   ```
   python scripts/session_audit.py                      # full report
   python scripts/session_audit.py --since 2026-04-09   # filter by date
   python scripts/session_audit.py --pr-range 90-108    # filter by PR range
   python scripts/session_audit.py --format csv          # tab-separated output
   python scripts/session_audit.py --verbose             # per-session detail
   ```

   **7 sections:**
   1. Daily token usage table (from session JSONLs)
   2. Daily efficiency: lines changed vs output tokens (JSONLs + gh API)
   3. Model usage breakdown (from JSONL `message.model`)
   4. Complete PR table (from gh API)
   5. Era analysis — hardcoded boundary at PR #107; eras: "pre-DAG" (#1–#106),
      "DAG impl" (#107), "post-DAG" (#108+)
   6. Subagent analysis (from `~/Projects/tp-claude-logs/agent-audit.log`)
   7. Per-session detail (`--verbose` only)

   **JSONL parsing:**
   - Path: `~/.claude/projects/-Users-tomaszpionka-Projects-rts-outcome-prediction/*.jsonl`
   - Deduplicate by `message.id` (access: `record["message"]["id"]`) — NOT
     `uuid` or `message.uuid`. The JSONL emits 3-4 records per API response
     with different record `uuid` values but the same `message.id`.
   - Only count records where `type == "assistant"` and `message.usage` exists
   - Token fields: `usage.input_tokens`, `usage.output_tokens`,
     `usage.cache_read_input_tokens`, `usage.cache_creation_input_tokens`
   - Model: `message.model`
   - Timestamp: `record.timestamp` (ISO 8601 with Z suffix)

   **Agent log parsing:**
   - Format: `[YYYY-MM-DD HH:MM:SS] EventType key=value ...`
   - Events: SessionOpen, SessionClose, SubagentStart, SubagentStop
   - Token fields on SubagentStop: `in=`, `out=`, `cache_read=`
   - Duration: diff between matching Start/Stop by `agent=` ID

   **`--format csv`:** Each section emits tab-separated table with header row.
   Sections separated by blank line + `# Section Name` comment.

   **Error handling:** `subprocess` calls (`gh`, `git`) must catch failures and
   print a warning section rather than crashing. The script must always produce
   valid output, even if degraded.

4. `git add scripts/session_audit.py`. Do NOT commit.

## Verification

- `python scripts/session_audit.py | grep -q "## Daily token usage"` succeeds
- `python scripts/session_audit.py | grep -q "## Model usage"` succeeds
- `python scripts/session_audit.py --since 2026-04-11 | grep -q "2026-04-11"` succeeds
- Script does not crash when `~/Projects/tp-claude-logs/agent-audit.log` is missing
- Script does not crash when `gh` is unavailable (prints warning section)
- No imports outside stdlib
