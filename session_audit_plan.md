# Plan: Session Audit Dashboard

**Category:** C (chore)
**Branch:** `chore/session-audit-dashboard`
**Priority:** Low — utility tooling, no science or thesis dependency

---

## Problem

`session_audit.md` was generated manually by a one-off analysis. The data
sources are machine-readable and stable enough to produce this report on demand,
but one source (`/tmp/rts-agent-log.txt`) is volatile and lost on reboot.

## Data Sources

| Source | What it contains | Persistent? |
|--------|-----------------|-------------|
| `~/.claude/projects/-Users-tomaszpionka-Projects-rts-outcome-prediction/*.jsonl` | Per-session orchestrator tokens (input, output, cache_read, cache_create, model) keyed by message UUID | Yes (149 files as of Apr 11) |
| `/tmp/rts-agent-log.txt` | Subagent start/stop with type, model, per-agent tokens, durations | **No — lost on reboot** |
| `gh pr list --state merged --json number,title,headRefName,mergedAt,additions,deletions` | PR metadata | Yes (API) |
| `git log` | Commit history, branch mapping | Yes |

## Steps

### S1. Make subagent log persistent

Change `scripts/hooks/log-subagent.sh` line 4:
```bash
# Before
LOG="/tmp/rts-agent-log.txt"
# After
LOG="$HOME/.claude/agent-audit.log"
```

Also update the two sibling state files (`rts-sessions-seen.txt`,
`rts-sessions-counts.txt`) to the same directory. Add
`~/.claude/agent-audit.log` to `.gitignore` if not already covered.

Migrate any existing `/tmp/rts-agent-log.txt` content:
```bash
cat /tmp/rts-agent-log.txt >> ~/.claude/agent-audit.log 2>/dev/null
```

### S2. Create the dashboard script

File: `scripts/session_audit.py`

A standalone Python script (not a notebook — no jupytext pairing needed, no
sandbox contract). Reads the three data sources and prints the same report
structure as `session_audit.md` to stdout as markdown.

**Dependencies:** Only stdlib (`json`, `glob`, `datetime`, `collections`,
`subprocess` for `gh` and `git` calls). No pandas, no external packages.

**CLI interface:**
```
python scripts/session_audit.py                    # full report
python scripts/session_audit.py --since 2026-04-09 # filter by date
python scripts/session_audit.py --pr-range 90-108  # filter by PR range
python scripts/session_audit.py --format md         # default: markdown
python scripts/session_audit.py --format csv        # for spreadsheet import
```

**Sections to generate:**
1. Daily token usage table (from session JSONLs)
2. Daily efficiency: lines changed vs output tokens (JSONL + gh API)
3. Model usage breakdown (from JSONL `message.model` field)
4. Full PR table (from gh API)
5. Era analysis (configurable era boundaries)
6. Subagent analysis (from agent-audit.log, if available)
7. Per-session detail (optional `--verbose` flag)

**JSONL parsing notes:**
- Deduplicate by `message.uuid` — the JSONL contains streaming duplicates
- Only count records where `type == "assistant"` and `message.usage` exists
- Token fields: `usage.input_tokens`, `usage.output_tokens`,
  `usage.cache_read_input_tokens`, `usage.cache_creation_input_tokens`
- Model: `message.model`
- Timestamp: `record.timestamp` (ISO 8601 with Z suffix)

**Agent log parsing notes:**
- Format: `[YYYY-MM-DD HH:MM:SS] EventType key=value key=value ...`
- Events: `SessionOpen`, `SessionClose`, `SubagentStart`, `SubagentStop`
- Token fields on `SubagentStop`: `in=`, `out=`, `cache_read=`
- Duration: diff between matching `SubagentStart` and `SubagentStop` by `agent=` ID

### S3. Wire as a convenience command (optional)

Add to `pyproject.toml` scripts section:
```toml
audit = "scripts.session_audit:main"
```

Or just document: `python scripts/session_audit.py > session_audit.md`

### S4. Delete the static report

Remove `session_audit.md` from repo root — it's now generated on demand.
Add a note in the script docstring pointing to where the report can be
regenerated.

---

## Files

| File | Action |
|------|--------|
| `scripts/hooks/log-subagent.sh` | Change LOG path to `~/.claude/agent-audit.log` |
| `scripts/session_audit.py` | New — dashboard generator |
| `session_audit.md` | Delete (generated artifact) |
| `.gitignore` | Add `session_audit.md` if keeping as generated output |

## Gate Condition

- `python scripts/session_audit.py` produces valid markdown with all 7 sections
- `--since` and `--pr-range` filters work correctly
- Subagent log persists across simulated reboot (path is `~/.claude/`)
- No new dependencies added to pyproject.toml
