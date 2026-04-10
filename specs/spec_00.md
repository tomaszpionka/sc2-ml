# Spec 00: Parallel Executor Convention

**Category:** C — Chore
**Branch:** N/A — this spec modifies agent definitions, not application code
**Execute on:** whatever branch is active when you run this (e.g. `chore/parallel-executor-setup`)

---

## Context

The project needs a convention for running multiple executor subagents in
parallel. Two mechanisms exist:

### Strategy A: Shared branch (no isolation)
Parent creates a branch, spawns executors that all edit the same working tree.
Simple, no merge step, but requires that specs touch non-overlapping files.

### Strategy B: Worktree isolation
Parent spawns executors with `isolation: "worktree"`. Each gets a temporary
git worktree at `.claude/worktrees/<name>/` with its own branch based on HEAD.
Full file isolation — no conflict possible. After completion, each worktree's
changes must be merged back (auto-cleaned if no changes were made).

### When to use which

| Situation | Strategy | Why |
|-----------|----------|-----|
| Specs touch completely different files | A (shared) | No merge overhead |
| Specs overlap on a few files in distinct sections | A (shared) | Edit tool's unique-match makes collisions unlikely |
| Specs heavily overlap or touch same lines | B (worktree) | Isolation prevents corruption |
| Complex Phase work across modules | B (worktree) | Safety worth the merge cost |
| Config/docs chores with known file map | A (shared) | Simpler, faster |

---

## Step 1: Add parallel execution rules to executor.md

**File:** `.claude/agents/executor.md`

**Edit:** Add a new section after `## Constraints` (after line 36):

```
old_string:
## Test placement rules

new_string:
## Parallel execution rules
When spawned as one of multiple parallel executors:
- Do NOT run `git checkout`, `git branch`, or any branch-modifying command.
- Do NOT run `git add` or `git commit` — the parent session handles staging.
- If your spec file says "Branch: ..." — that is for the parent session's
  reference, not for you to create.
- If you need to edit a file that another parallel executor might also touch,
  complete your edit and report the conflict risk in your summary.

When spawned with `isolation: "worktree"`:
- You are in an isolated git worktree with your own branch.
- Edit files freely — no conflict with other agents.
- Do NOT run `git push`. The parent session merges your worktree branch.

## Test placement rules
```

---

## Step 2: Add orchestration instructions to CLAUDE.md

**File:** `CLAUDE.md`

**Edit:** Add a new section after `## Phase Work Execution (Sandbox Notebooks)`:

```
old_string:
## Agent Architecture

new_string:
## Parallel Executor Orchestration

Two strategies for running executor subagents in parallel:

**Strategy A — Shared branch** (for non-overlapping file edits):
1. Parent creates the branch before spawning any executor
2. Parent provides each executor with its spec file path
3. Executors do NOT create branches, checkout, add, or commit
4. Parent stages and commits after all executors complete
5. Never assign parallel executors specs that edit the same file

**Strategy B — Worktree isolation** (for overlapping or complex edits):
1. Parent spawns executors with `isolation: "worktree"`
2. Each executor gets an isolated worktree with its own branch
3. Executors edit freely — no conflict possible
4. Parent merges each worktree branch back after completion

Use Strategy A for config/docs chores with known file maps. Use Strategy B
for Phase work or any situation where file overlap is hard to predict.

## Agent Architecture
```

---

## Step 3: Create the specs README with parallel execution guide

**File:** `specs/README.md` (NEW)

```markdown
# Specs — Parallel Execution Guide

## Choosing a strategy

| Situation | Use |
|-----------|-----|
| Specs touch completely different files | Strategy A (shared branch) |
| Specs overlap in distinct sections of same file | Strategy A (low risk) |
| Specs heavily overlap or touch same lines | Strategy B (worktree) |
| Unsure about overlap | Strategy B (safe default) |

## Strategy A: Shared branch

```
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

```
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
```

---

## Step 4: Update AGENT_MANUAL.md

**File:** `docs/agents/AGENT_MANUAL.md`

**4a — Add branch guard to § Hooks (after line 284):**

```
old_string:
### PreToolUse: Write Guard (before every Write/Edit)
Checks the target path. Inside repo = silent. Outside repo in home = asks you.
Outside home = blocked. Protects your system from accidental writes.

new_string:
### PreToolUse: Write Guard (before every Write/Edit)
Checks the target path. Inside repo = silent. Outside repo in home = asks you.
Outside home = blocked. Protects your system from accidental writes.

### PreToolUse: Branch Guard (before every Write/Edit)
Blocks all Write/Edit calls when on master or main branch. Forces you to
create a feature branch first. Prevents the #1 historical friction source:
accidentally editing files on master.
```

**4b — Add Layer 4 to § Permission Model (after line 249):**

```
old_string:
**Result:** Normal work flows without any permission prompts. Dangerous
operations are blocked. Edge cases ask you first.

new_string:
### Layer 4: Branch guard hook (catches edits on master)
- Write/Edit on a feature branch → allowed silently
- Write/Edit on master or main → blocked with error message

**Result:** Normal work flows without any permission prompts. Dangerous
operations are blocked. Edge cases ask you first.
```

**4c — Add Workflow E after Workflow D (after line 224):**

```
old_string:
---

## Permission Model

new_string:
### Workflow E: Parallel Spec Execution

When a plan has been split into independent spec files (`specs/spec_NN.md`):

```
Step 1:  [parent creates branch OR uses worktree isolation]
Step 2:  [parent spawns executor(s) — one per spec]
         @executor execute specs/spec_01.md
         @executor execute specs/spec_02.md   ← parallel if safe
Step 3:  [shared branch: parent reviews all changes]
         [worktree: parent merges each worktree branch]
Step 4:  @reviewer review changes
Step 5:  [parent stages, commits, wraps up PR]
```

**Two strategies:**
- **Shared branch:** Executors edit the same working tree. Requires
  non-overlapping file ownership. See `specs/README.md` for file maps.
- **Worktree isolation:** Each executor gets `isolation: "worktree"`.
  Full file isolation, but requires merging branches afterwards.

---

## Permission Model
```

**4d — Update § Future: Autonomous Long Sessions (line ~310):**

```
old_string:
- Uses `isolation: worktree` for safe parallel work

new_string:
- Uses `isolation: worktree` for safe parallel work on separate branches, or
  shared-branch parallel execution for specs that touch non-overlapping files
  (see Workflow E above)
```

**4e — Update `poetry run` in § Reading database schemas (line 161):**

```
old_string:
poetry run sc2 export-schemas --db <db_path> --out <schemas_dir>

new_string:
source .venv/bin/activate && poetry run sc2 export-schemas --db <db_path> --out <schemas_dir>
```

---

## Step 5: Run tests to confirm nothing breaks

```bash
source .venv/bin/activate && poetry run pytest tests/ -v --cov=rts_predict --cov-report=term-missing
source .venv/bin/activate && poetry run ruff check src/ tests/
source .venv/bin/activate && poetry run mypy src/rts_predict/
```

---

## Gate condition

- [ ] `grep "Parallel execution rules" .claude/agents/executor.md` matches
- [ ] `grep "isolation.*worktree" .claude/agents/executor.md` matches
- [ ] `grep "Parallel Executor Orchestration" CLAUDE.md` matches
- [ ] `grep "Strategy B.*Worktree" CLAUDE.md` matches
- [ ] `specs/README.md` exists with both strategies documented
- [ ] `grep "Branch Guard" docs/agents/AGENT_MANUAL.md` matches
- [ ] `grep "Workflow E" docs/agents/AGENT_MANUAL.md` matches
- [ ] `grep "source .venv" docs/agents/AGENT_MANUAL.md` matches
- [ ] All tests pass, lint clean, mypy clean
