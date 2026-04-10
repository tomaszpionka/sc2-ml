# Specs — Parallel Execution Guide

## Choosing a strategy

| Situation | Use |
|-----------|-----|
| Specs touch completely different files | Strategy A (shared branch) |
| Specs overlap in distinct sections of same file | Strategy A (low risk) |
| Specs heavily overlap or touch same lines | Strategy B (worktree) |
| Unsure about overlap | Strategy B (safe default) |

## Strategy A: Shared branch

```bash
# 1. Parent creates the shared branch
git checkout -b chore/my-feature

# 2. Spawn executors (no isolation)
Agent({
  subagent_type: "executor",
  prompt: "Execute specs/spec_01.md. Do NOT create branches or commit."
})
Agent({
  subagent_type: "executor",
  prompt: "Execute specs/spec_02.md. Do NOT create branches or commit."
})

# 3. Parent reviews, stages, commits
```

## Strategy B: Worktree isolation

```bash
# 1. Spawn executors with isolation (each gets its own worktree + branch)
Agent({
  subagent_type: "executor",
  isolation: "worktree",
  prompt: "Execute specs/spec_01.md. Do NOT commit or push."
})
Agent({
  subagent_type: "executor",
  isolation: "worktree",
  prompt: "Execute specs/spec_02.md. Do NOT commit or push."
})

# 2. Each returns its worktree path and branch name
# 3. Parent merges branches:
git merge <worktree-branch-1>
git merge <worktree-branch-2>
# 4. Resolve any conflicts, commit
```

## File ownership map (specs 01-03)

| File | spec_01 | spec_02 | spec_03 | Conflict? |
|------|---------|---------|---------|-----------|
| `CLAUDE.md` | line 13 (Critical Rules) | lines 10, 29-34 | — | YES — different sections |
| `.claude/settings.json` | hooks.PreToolUse | permissions.allow | — | YES — different keys |
| `.claude/rules/python-code.md` | — | lines 9-11 | — | No |
| `.claude/rules/git-workflow.md` | — | lines 17-19 | PR Body section | YES — different sections |
| `.claude/agents/executor.md` | — | lines 33-71 | — | No |
| `.claude/agents/reviewer.md` | — | lines 22-37 | — | No |
| `scripts/hooks/guard-master-branch.sh` | NEW | — | — | No |
| `scripts/hooks/lint-on-edit.sh` | — | line 9 | — | No |
| `README.md` | — | — | lines 14-47 | No |
| Memory files | — | 3 files | 3 files | No overlap |

## Recommended order for specs 01-03

**Option A — Strategy A, partial parallel:**
1. spec_01 alone (touches CLAUDE.md + settings.json)
2. spec_02 + spec_03 in parallel (overlapping files are in distinct sections)

**Option B — Strategy B, full parallel:**
All three with `isolation: "worktree"`. Merge back in order: spec_01, spec_02, spec_03.
Conflicts on CLAUDE.md and settings.json will be in different sections — git
should auto-resolve.
