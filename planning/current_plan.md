# Category C Plan: Session Audit Dashboard

**Category:** C (chore)
**Branch:** `chore/session-audit-dashboard`
**Date:** 2026-04-11
**Priority:** Low — utility tooling, no science or thesis dependency

---

## Scope

Create an on-demand session audit dashboard (`scripts/session_audit.py`) and
consolidate log file placement. Move persistent audit logs into
`~/Projects/tp-claude-logs/` (macOS-canonical user app data)
and ephemeral state into `/tmp/tp-claude-logs/`. Clears all custom files out of
`~/.claude/` (tool-managed).

---

## Design Decision: Log File Placement

### Rejected: `~/.claude/` (any path)

A reviewer audit found that `~/.claude/` is tool-managed by Claude Code — it
contains `backups/`, `sessions/`, `telemetry/`, `tasks/`, `plans/`, and other
directories created/managed by the CLI process. Custom files placed here are
co-tenants with no lease. Risks:

- **Namespace collision:** A future Claude Code release could add its own
  `logs/`, `agent-audit.log`, or `bash-audit.log` and silently overwrite or
  corrupt custom files.
- **No project isolation:** A global log mixes telemetry from all repos.
- **Existing precedent is wrong:** `~/.claude/bash-audit.log` (from
  `log-bash.sh`) has the same problems — it should be migrated, not replicated.

### Rejected: `.claude/logs/` (project-local)

Good isolation, but `.claude/` in the repo is also partly read by Claude Code's
project-settings mechanism. A future CLI release that scans `.claude/` for new
subdirectories could conflict. Also requires `.gitignore` entry.

### Rejected: `/tmp/tp-claude-logs/`

Safe namespace (sticky bit, user-owned), but `/tmp/` is cleared on every reboot
by macOS `launchd`. Subagent telemetry would be lost — defeating the purpose of
moving away from the current volatile `/tmp/rts-agent-log.txt`.

### Adopted: `~/Projects/tp-claude-logs/`

User-managed directory alongside project repos. Simple, visible, persistent.

| Property | Value |
|----------|-------|
| Base dir | `~/Projects/tp-claude-logs/` |
| Agent audit | `~/Projects/tp-claude-logs/agent-audit.log` |
| Bash audit | `~/Projects/tp-claude-logs/bash-audit.log` |
| Session state | `/tmp/tp-claude-logs/sessions-seen.txt` |
| Session counts | `/tmp/tp-claude-logs/sessions-counts.txt` |
| Lock dir | `/tmp/tp-claude-logs/sessions-counts.lock` |
| Persistence | **Yes** — survives reboots, only lost if manually deleted |
| CLI conflict | None — fully outside `~/.claude/` and repo tree |
| Git | Not inside any repo — nothing to ignore |

Session state files (`sessions-seen.txt`, `sessions-counts.txt`, lock dir)
remain in `/tmp/tp-claude-logs/` — they are intentionally per-boot ephemeral
state (tracking which sessions have emitted `SessionOpen`), not audit data.

**Migration — sequencing matters for chronological integrity:**

Once the hooks are updated (S1a, S1b), new log entries start landing in the new
directory immediately. The old data must be injected *before* (on top of) the
live entries, not appended after them, or the timeline breaks.

**Step 1 — Stage old logs into the new dir with `_old` suffix:**
```bash
cp /tmp/rts-agent-log.txt ~/Projects/tp-claude-logs/agent-audit_old.log 2>/dev/null
cp ~/.claude/bash-audit.log ~/Projects/tp-claude-logs/bash-audit_old.log 2>/dev/null
```

**Step 2 — Prepend old data into the live logs (old on top, new below):**
```bash
# agent-audit: old entries (pre-migration) + new entries (post-migration)
cat ~/Projects/tp-claude-logs/agent-audit_old.log \
    ~/Projects/tp-claude-logs/agent-audit.log \
    > ~/Projects/tp-claude-logs/agent-audit_merged.log \
  && mv ~/Projects/tp-claude-logs/agent-audit_merged.log \
        ~/Projects/tp-claude-logs/agent-audit.log

# bash-audit: same pattern
cat ~/Projects/tp-claude-logs/bash-audit_old.log \
    ~/Projects/tp-claude-logs/bash-audit.log \
    > ~/Projects/tp-claude-logs/bash-audit_merged.log \
  && mv ~/Projects/tp-claude-logs/bash-audit_merged.log \
        ~/Projects/tp-claude-logs/bash-audit.log
```

**Step 3 — Clean up staging files:**
```bash
rm ~/Projects/tp-claude-logs/agent-audit_old.log
rm ~/Projects/tp-claude-logs/bash-audit_old.log
```

**Timing:** This migration runs AFTER TG01 hooks are committed and active, as a
separate migration task (T04 in TG01). It is NOT parallel-safe with the hooks —
depends on T01 and T02 completing first. A brief window exists where the live
log has only post-migration entries; after the prepend, the full timeline is
restored.

**Edge case:** If the live log does not yet exist when prepend runs (no hook has
fired yet), the `cat` simply copies the old file as-is. This is correct.

---

## Data Sources for the Dashboard

| Source | Contents | Persistent? |
|--------|----------|-------------|
| `~/.claude/projects/<project>/*.jsonl` | Per-session orchestrator tokens (input, output, cache_read, cache_create, model) keyed by message UUID | Yes (Claude-managed) |
| `~/Projects/tp-claude-logs/agent-audit.log` | Subagent start/stop with type, model, per-agent tokens, durations | Yes |
| `~/Projects/tp-claude-logs/bash-audit.log` | Per-command audit trail | Yes |
| `gh pr list --state merged --json ...` | PR metadata (additions, deletions, mergedAt) | Yes (API) |
| `git log` | Commit history | Yes |

---

## Execution Steps

### S1. Consolidate hook logs into `~/Projects/tp-claude-logs/`

Audit logs (persistent) go to `~/Projects/tp-claude-logs/`.
Ephemeral per-boot state files go to `/tmp/tp-claude-logs/`.

**S1a — Update `scripts/hooks/log-subagent.sh`**

Current state:
- `LOG="/tmp/rts-agent-log.txt"` (line 4)
- `SESSIONS_SEEN="/tmp/rts-sessions-seen.txt"` (line 29)
- `COUNTS_FILE="/tmp/rts-sessions-counts.txt"` (line 39)
- `LOCK_DIR="/tmp/rts-sessions-counts.lock"` (line 40)

Change to:
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

Add `project=` field to every log line (SessionOpen, SubagentStart,
SubagentStop, SessionClose) for future cross-project filtering:
```bash
PROJECT="$(basename "$(git rev-parse --show-toplevel 2>/dev/null || echo unknown)")"
```

Append `project=$PROJECT` to each `echo "[$TIMESTAMP] ..."` line.

**S1b — Update `scripts/hooks/log-bash.sh`**

Current state:
- `LOG="$HOME/.claude/bash-audit.log"` (line 8)

Change to:
```bash
LOGDIR="$HOME/Projects/tp-claude-logs"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/bash-audit.log"
```

Add `project=` field to the log record block (line 23). Show the full
replacement for the record block (lines 22–28):
```bash
PROJECT="$(basename "$(git rev-parse --show-toplevel 2>/dev/null || echo unknown)")"
{
  printf '[%s] session=%s agent=%s type=%s project=%s\n' \
    "$TIMESTAMP" "$SESSION" "$AGENT" "$AGENT_TYPE" "$PROJECT"
  [[ -n "$DESC" ]] && printf '  desc: %s\n' "$DESC"
  printf '  cmd:  %s\n' "$CMD_ONELINE"
  printf -- '---\n'
} >> "$LOG"
```

**S1c — Update `scripts/hooks/README.md`**

Update all log file path references from `/tmp/rts-agent-log.txt` and
`~/.claude/bash-audit.log` to `/tmp/tp-claude-logs/` paths. Document the
volatility trade-off and the manual migration command.

### S2. Create the dashboard script

**File:** `scripts/session_audit.py`

Standalone Python script. Reads the data sources and prints the report as
markdown to stdout. **No external dependencies** — stdlib only (`json`, `glob`,
`datetime`, `collections`, `subprocess`, `argparse`).

**CLI interface:**
```
python scripts/session_audit.py                      # full report
python scripts/session_audit.py --since 2026-04-09   # filter by date
python scripts/session_audit.py --pr-range 90-108    # filter by PR range
python scripts/session_audit.py --format csv          # for spreadsheet import
python scripts/session_audit.py --verbose             # per-session detail
```

**Sections to generate:**
1. Daily token usage table (from session JSONLs)
2. Daily efficiency: lines changed vs output tokens (JSONLs + gh API)
3. Model usage breakdown (from JSONL `message.model` field)
4. Complete PR table (from gh API)
5. Era analysis — hardcoded boundary at PR #107 (DAG introduction); eras:
   "pre-DAG" (#1–#106), "DAG impl" (#107), "post-DAG" (#108+). Future: accept
   `--era-boundary` flag to override
6. Subagent analysis (from `~/Projects/tp-claude-logs/agent-audit.log`, graceful
   fallback if file missing — print "no subagent data available")
7. Per-session detail (with `--verbose`)

**`--format csv` behaviour:** Each section emits a tab-separated table with a
header row. Sections are separated by a blank line and a `# Section Name`
comment line. Designed for spreadsheet paste, not programmatic parsing.

**Error handling:** All `subprocess` calls (`gh`, `git`) must catch failures and
print a warning section (e.g., `## PR table\n\n_gh CLI unavailable — skipping_`)
rather than crashing. The dashboard must always produce valid output, even if
degraded.

**JSONL parsing notes:**
- Deduplicate by `message.id` (access: `record["message"]["id"]`, format:
  `msg_01DPxX...`) — the JSONL emits 3-4 records per API response with different
  record-level `uuid` values but the same `message.id`. Using the wrong key
  (`uuid` or `message.uuid`) would produce 3-4x token inflation
- Only count records where `type == "assistant"` and `message.usage` exists
- Token fields: `usage.input_tokens`, `usage.output_tokens`,
  `usage.cache_read_input_tokens`, `usage.cache_creation_input_tokens`
- Model: `message.model`
- Timestamp: `record.timestamp` (ISO 8601 with Z suffix)

**Agent log parsing notes:**
- Format: `[YYYY-MM-DD HH:MM:SS] EventType key=value key=value ...`
- Events: `SessionOpen`, `SessionClose`, `SubagentStart`, `SubagentStop`
- Token fields on `SubagentStop`: `in=`, `out=`, `cache_read=`
- Duration: diff between matching Start/Stop by `agent=` ID
- New field: `project=` for filtering

### S3. Clean up

- Delete `session_audit.md` from repo root (now generated on demand)
- Delete `session_audit_plan.md` from repo root (consumed into this plan)

---

## File Manifest

| File | Action |
|------|--------|
| `scripts/hooks/log-subagent.sh` | Audit log → `~/Projects/tp-claude-logs/`, state → `/tmp/tp-claude-logs/`, add `project=` |
| `scripts/hooks/log-bash.sh` | Move `~/.claude/bash-audit.log` → `~/Projects/tp-claude-logs/`, add `project=` |
| `scripts/hooks/README.md` | Update path references, document persistence model |
| `scripts/session_audit.py` | New — dashboard generator |
| `session_audit.md` | Delete (generated artifact) |
| `session_audit_plan.md` | Delete (consumed into plan) |

---

## Gate Condition

- `python scripts/session_audit.py` produces valid markdown with all 7 sections
- `--since` and `--pr-range` filters produce correct subsets
- `~/Projects/tp-claude-logs/agent-audit.log` is written by the subagent hook
- `~/Projects/tp-claude-logs/bash-audit.log` is written by the bash hook
- Both logs include `project=rts-outcome-prediction` field
- No new writes to `~/.claude/bash-audit.log` or `/tmp/rts-agent-log.txt`
- Session state files (`sessions-seen.txt`, `sessions-counts.txt`, lock dir)
  are under `/tmp/tp-claude-logs/` not scattered in `/tmp/`
- No new dependencies added to pyproject.toml
- Dashboard degrades gracefully when agent log is empty (e.g., first run after migration)
- Dashboard degrades gracefully when `gh` CLI is unavailable (prints warning, does not crash)
- `python scripts/session_audit.py | grep -q "## Daily token usage"` succeeds
- `python scripts/session_audit.py | grep -q "## Model usage"` succeeds

---

## Suggested Execution Graph

```yaml
dag_id: "dag_session_audit_dashboard"
spec_ref: "planning/current_plan.md"
category: "C"
branch: "chore/session-audit-dashboard"
base_ref: "master"
default_isolation: "shared_branch"

jobs:
  - job_id: "J01"
    name: "Session audit dashboard"

    task_groups:
      - group_id: "TG01"
        name: "Consolidate hook logs"
        depends_on: []
        review_gate:
          agent: "reviewer"
          scope: "diff"
          on_blocker: "halt"
        tasks:
          - task_id: "T01"
            name: "Update log-subagent.sh — paths + project field"
            agent: "executor"
            file_scope:
              - "scripts/hooks/log-subagent.sh"
            parallel_safe: true
            depends_on: []
          - task_id: "T02"
            name: "Update log-bash.sh — path + project field"
            agent: "executor"
            file_scope:
              - "scripts/hooks/log-bash.sh"
            parallel_safe: true
            depends_on: []
          - task_id: "T03"
            name: "Update hooks README"
            agent: "executor"
            file_scope:
              - "scripts/hooks/README.md"
            parallel_safe: true
            depends_on: []

      - group_id: "TG02"
        name: "Create dashboard script"
        depends_on: ["TG01"]
        review_gate:
          agent: "reviewer"
          scope: "diff"
          on_blocker: "halt"
        tasks:
          - task_id: "T04"
            name: "Write scripts/session_audit.py"
            agent: "executor"
            file_scope:
              - "scripts/session_audit.py"
            read_scope:
              - "session_audit.md"
              - "scripts/hooks/log-subagent.sh"
              - "scripts/hooks/log-bash.sh"
            parallel_safe: false
            depends_on: []

      - group_id: "TG03"
        name: "Cleanup + CHANGELOG"
        depends_on: ["TG02"]
        review_gate:
          agent: "reviewer"
          scope: "cumulative"
          on_blocker: "halt"
        tasks:
          - task_id: "T05"
            name: "Delete static reports, update CHANGELOG"
            agent: "executor"
            file_scope:
              - "CHANGELOG.md"
              - "session_audit.md"
              - "session_audit_plan.md"
            parallel_safe: false
            depends_on: []

final_review:
  agent: "reviewer-deep"
  scope: "all"
  base_ref: "master"
  on_blocker: "halt"

failure_policy:
  on_failure: "halt"
```
