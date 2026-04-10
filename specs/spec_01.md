# Spec 01: Branch Guard Hook + "Never Work on Master" Rule

**Category:** C — Chore
**Branch:** `chore/branch-guard-hook`
**Source:** `audit_plan.md` Changes A + D
**Depends on:** Nothing — can run first or in parallel with spec_02/spec_03

---

## Context

The #1 friction source across 116 sessions was Claude writing files while on
the master branch. `settings.json` denies `git commit` and `git push` but
does NOT prevent Write/Edit tool calls on master. This spec adds:
1. A CLAUDE.md Critical Rule making the prohibition explicit
2. A PreToolUse hook that blocks Write/Edit when on master/main

---

## Step 1: Add "never work on master" to CLAUDE.md Critical Rules

**File:** `CLAUDE.md`

**Edit:** Find the last `NEVER` bullet in the Critical Rules section and add
a new bullet after it.

```
old_string:
- **NEVER** skip the plan/execute two-session workflow for non-trivial work

new_string:
- **NEVER** skip the plan/execute two-session workflow for non-trivial work
- **NEVER** make file changes while on master — always work on a feature branch
```

**Verify:** `grep "NEVER.*master" CLAUDE.md` returns exactly 1 match.

---

## Step 2: Create the branch guard hook script

**File:** `scripts/hooks/guard-master-branch.sh` (NEW)

**Content:**
```bash
#!/usr/bin/env bash
set -euo pipefail

branch=$(git branch --show-current 2>/dev/null)
if [ "$branch" = "master" ] || [ "$branch" = "main" ]; then
  echo "BLOCKED: On $branch branch. Create a feature branch first." >&2
  exit 1
fi
```

**Post-write:** `chmod +x scripts/hooks/guard-master-branch.sh`

**Verify:** `ls -la scripts/hooks/guard-master-branch.sh` shows `-rwxr-xr-x`.

---

## Step 3: Register the hook in settings.json

**File:** `.claude/settings.json`

**Edit:** Add a second entry to the `PreToolUse` array. The existing entry is:
```json
"PreToolUse": [
  {
    "matcher": "Write|Edit",
    "hooks": [
      {
        "type": "command",
        "command": "./scripts/hooks/guard-write-path.sh"
      }
    ]
  }
]
```

Change to:
```json
"PreToolUse": [
  {
    "matcher": "Write|Edit",
    "hooks": [
      {
        "type": "command",
        "command": "./scripts/hooks/guard-write-path.sh"
      }
    ]
  },
  {
    "matcher": "Write|Edit",
    "hooks": [
      {
        "type": "command",
        "command": "./scripts/hooks/guard-master-branch.sh"
      }
    ]
  }
]
```

**Verify:** `jq '.hooks.PreToolUse | length' .claude/settings.json` returns `2`.

---

## Step 4: Run tests to confirm nothing breaks

```bash
source .venv/bin/activate && poetry run pytest tests/ -v --cov=rts_predict --cov-report=term-missing
source .venv/bin/activate && poetry run ruff check src/ tests/
source .venv/bin/activate && poetry run mypy src/rts_predict/
```

No code was changed — only config and a new hook script — so tests must still
pass at the same coverage level.

---

## Gate condition

- [ ] `grep "NEVER.*master" CLAUDE.md` matches exactly once
- [ ] `scripts/hooks/guard-master-branch.sh` exists and is executable
- [ ] `jq '.hooks.PreToolUse | length' .claude/settings.json` returns 2
- [ ] All tests pass, lint clean, mypy clean
