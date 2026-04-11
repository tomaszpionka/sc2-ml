# Claude Code Hooks

Four hooks are wired up in `.claude/settings.json`. Each section below describes what the hook does, where it writes, and useful commands for querying its output.

---

## log-bash.sh

**Event:** `PreToolUse` — matcher: `Bash`  
**Fires:** before every Bash command, from any agent (root, executor, planner, lookup, …)  
**Log:** `~/Projects/tp-claude-logs/bash-audit.log` — persistent across reboots, global to all projects; includes a `project=` field per entry

**Format:**
```
[2026-04-11 14:23:01] session=abc123 agent=xyz456 type=executor project=rts-outcome-prediction
  desc: Check line/byte counts of template files
  cmd:  for f in /path/a /path/b; do echo "=== $f ==="; wc -lc "$f"; done
---
```

> Commands blocked by the deny list never reach `PreToolUse` and will not appear here.

**Useful commands:**

```bash
# Live tail
tail -f ~/Projects/tp-claude-logs/bash-audit.log

# All commands from one session
grep -A3 "session=SESSION_ID" ~/Projects/tp-claude-logs/bash-audit.log

# All commands run by a specific agent type
grep -A3 "type=executor" ~/Projects/tp-claude-logs/bash-audit.log

# All git commands across all sessions
grep "cmd:.*git " ~/Projects/tp-claude-logs/bash-audit.log

# All destructive-looking commands (rm, drop, truncate)
grep -i "cmd:.*\(rm \|DROP\|TRUNCATE\)" ~/Projects/tp-claude-logs/bash-audit.log

# Count commands per agent type
grep "^\[" ~/Projects/tp-claude-logs/bash-audit.log | grep -oP 'type=\K\S+' | sort | uniq -c | sort -rn

# Count commands per session
grep "^\[" ~/Projects/tp-claude-logs/bash-audit.log | grep -oP 'session=\K\S+' | sort | uniq -c | sort -rn

# Commands run on a specific date
grep "^\[2026-04-11" ~/Projects/tp-claude-logs/bash-audit.log

# Commands whose description matches a keyword
grep -A2 "desc:.*split" ~/Projects/tp-claude-logs/bash-audit.log

# Show full records that contain a keyword anywhere (header + desc + cmd)
awk '/keyword/{found=1} found{print; if(/^---/){found=0}}' ~/Projects/tp-claude-logs/bash-audit.log

# Count total commands logged
grep -c "^---" ~/Projects/tp-claude-logs/bash-audit.log
```

---

## log-subagent.sh

**Events:** `SubagentStart` and `SubagentStop`  
**Fires:** when any sub-agent is spawned or completes  
**Log:** `~/Projects/tp-claude-logs/agent-audit.log` — persistent across reboots  
**Side files:** `/tmp/tp-claude-logs/sessions-seen.txt`, `/tmp/tp-claude-logs/sessions-counts.txt`

**Format:**
```
[2026-04-11 14:20:00] SessionOpen   session=abc123 orchestrator=claude-sonnet-4-6 project=rts-outcome-prediction
[2026-04-11 14:20:01] SubagentStart session=abc123 agent=xyz type=executor model=claude-sonnet-4-6 project=rts-outcome-prediction
[2026-04-11 14:20:45] SubagentStop  session=abc123 agent=xyz type=executor model=claude-sonnet-4-6 in=12400 out=870 cache_read=9100 project=rts-outcome-prediction
[2026-04-11 14:20:45] SessionClose  session=abc123 total_agents=1 project=rts-outcome-prediction
```

**Useful commands:**

```bash
# Live tail
tail -f ~/Projects/tp-claude-logs/agent-audit.log

# Full timeline for one session
grep "session=SESSION_ID" ~/Projects/tp-claude-logs/agent-audit.log

# All sessions opened today
grep "SessionOpen" ~/Projects/tp-claude-logs/agent-audit.log

# All agent types spawned and how many times
grep "SubagentStart" ~/Projects/tp-claude-logs/agent-audit.log | grep -oP 'type=\K\S+' | sort | uniq -c | sort -rn

# Token usage per agent (SubagentStop lines only)
grep "SubagentStop" ~/Projects/tp-claude-logs/agent-audit.log | grep -v "tokens=unavailable"

# Total output tokens across all stopped agents
grep "SubagentStop" ~/Projects/tp-claude-logs/agent-audit.log \
  | grep -oP 'out=\K[0-9]+' | awk '{s+=$1} END {print "total_out_tokens:", s}'

# Total cache_read tokens (cost savings indicator)
grep "SubagentStop" ~/Projects/tp-claude-logs/agent-audit.log \
  | grep -oP 'cache_read=\K[0-9]+' | awk '{s+=$1} END {print "total_cache_read:", s}'

# Sessions where agents were started but never stopped (hung/crashed agents)
comm -23 \
  <(grep "SubagentStart" ~/Projects/tp-claude-logs/agent-audit.log | grep -oP 'agent=\K\S+' | sort) \
  <(grep "SubagentStop"  ~/Projects/tp-claude-logs/agent-audit.log | grep -oP 'agent=\K\S+' | sort)

# Count agents per session
grep "SubagentStop" ~/Projects/tp-claude-logs/agent-audit.log \
  | grep -oP 'session=\K\S+' | sort | uniq -c | sort -rn

# Sessions that spawned a planner-science agent
grep "SubagentStart" ~/Projects/tp-claude-logs/agent-audit.log | grep "type=planner-science"
```

---

## guard-write-path.sh

**Event:** `PreToolUse` — matcher: `Write|Edit`  
**Fires:** before every file write or edit  
**Output:** exit codes and JSON responses — no persistent log file

**Behavior:**
- Path inside repo → silently allow (exit 0)
- Path inside `$HOME` but outside repo → return `{"permissionDecision": "ask"}` (prompt user)
- Path outside `$HOME` → block with error message (exit 2)

**Useful commands:**

```bash
# There is no log file; surface guard blocks from the Claude Code session transcript instead.
# If you want to audit past blocks, add logging to the script itself, e.g.:
#   echo "[$(date '+%Y-%m-%d %H:%M:%S')] BLOCKED path=$ABS_PATH" >> ~/.claude/write-guard.log

# Check which paths were resolved as outside-repo during a session (requires added logging)
# grep "BLOCKED\|ASK" ~/.claude/write-guard.log

# Verify the repo root the guard is resolving to
git rev-parse --show-toplevel

# Dry-run: check whether a given path would pass the guard
ABS=$(realpath /some/path)
REPO=$(git rev-parse --show-toplevel)
[[ "$ABS" == "$REPO"* ]] && echo "ALLOW" || echo "ASK/BLOCK"
```

---

## lint-on-edit.sh

**Event:** `PostToolUse` — matcher: `Edit|Write`  
**Fires:** after every file edit or write  
**Output:** `ruff` lint output printed inline — no persistent log file

**Behavior:** if the edited file ends in `.py`, runs `ruff check <file> --no-fix` from the repo root and prints up to 10 lines of output. Non-Python files are silently skipped.

**Useful commands:**

```bash
# Run lint manually on a file (same command the hook uses)
source .venv/bin/activate && poetry run ruff check src/rts_predict/sc2/features.py --no-fix

# Run lint across the whole src tree
source .venv/bin/activate && poetry run ruff check src/ --no-fix

# Run lint and auto-fix (hook intentionally does not do this)
source .venv/bin/activate && poetry run ruff check src/ --fix

# Check which rules are active
source .venv/bin/activate && poetry run ruff rule --all | head -40

# Show all lint errors with line context
source .venv/bin/activate && poetry run ruff check src/ --no-fix --show-source

# Count lint violations per file
source .venv/bin/activate && poetry run ruff check src/ --no-fix --output-format=json \
  | jq 'group_by(.filename) | map({file: .[0].filename, count: length}) | sort_by(-.count)[]'
```
