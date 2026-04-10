# Spec 03: Git Workflow Consolidation + README Cleanup + Memory Updates

**Category:** C — Chore
**Branch:** `chore/git-workflow-consolidation`
**Source:** `audit_plan.md` Changes C + G + memory E.3/E.4/E.5
**Depends on:** Nothing — can run in parallel with spec_01/spec_02

---

## Context

Three independent but related cleanup tasks:
1. Consolidate ephemeral git artifacts (commit message, PR body) into
   `.github/tmp/` — currently `commit_msg.txt` lives in `temp/` while
   `pr.txt` is already in `.github/tmp/`
2. Fix stale README.md sections (dead file links, snapshot status)
3. Update memory files that reference the old `temp/commit_msg.txt` path

---

## Step 1: Update git-workflow.md — add commit.txt pattern + absolute paths note

**File:** `.claude/rules/git-workflow.md`

**1a — Replace the bash code block in § PR Body Format (lines 42-61):**

```
old_string:
```bash
# 1. Write PR body to file (never inline heredoc — avoids shell quoting issues)
cat > .github/tmp/pr.txt << 'EOF'
## Summary

- <bullet>

## Test plan

- [x] <step>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF

# 2. Create PR using the file
gh pr create --title "<type(scope): description>" --body-file .github/tmp/pr.txt

# 3. Clean up after PR is created
rm .github/tmp/pr.txt
```

new_string:
Always use **absolute paths** when referencing ephemeral files — relative paths
break when the working directory changes mid-session.

```bash
# 1. Commit message — write via Write tool (never heredoc — breaks in zsh)
#    Then user runs: git commit -F .github/tmp/commit.txt
#    Path: .github/tmp/commit.txt

# 2. PR body — write via Write tool
cat > .github/tmp/pr.txt << 'EOF'
## Summary

- <bullet>

## Test plan

- [x] <step>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF

# 3. Create PR using the file
gh pr create --title "<type(scope): description>" --body-file .github/tmp/pr.txt

# 4. Clean up after PR is created
rm -f .github/tmp/pr.txt .github/tmp/commit.txt
```
```

---

## Step 2: Update README.md — Prior Drafts section

**File:** `README.md`

**Edit:** Replace the entire "Prior Drafts" section (lines 33-39). The three
files listed (`ROADMAP_v1.md`, `methodology_v1.md`, `sanity_validation.md`)
were deleted in v0.13.2 and the path `sc2/reports/archive/` does not exist.

```
old_string:
## Prior Drafts (reference only — not authoritative)

| Document | Status |
|----------|--------|
| `src/rts_predict/sc2/reports/archive/ROADMAP_v1.md` | Superseded — caused premature jump to modelling before data exploration |
| `src/rts_predict/sc2/reports/archive/methodology_v1.md` | Superseded — assumed feature decisions not yet validated by exploration |
| `src/rts_predict/sc2/reports/archive/sanity_validation.md` | Evidence log of known issues pre-restart |

new_string:
## Prior Work (reference only — not authoritative)

Superseded drafts and pre-restart artifacts are preserved in per-dataset
archive directories:

- `src/rts_predict/sc2/reports/sc2egset/archive/` — SC2EGSet prior exploration
- `src/rts_predict/aoe2/reports/aoe2companion/archive/` — AoE2 Companion prior work
- `src/rts_predict/aoe2/reports/aoestats/archive/` — AoE2 aoestats prior work

Each archive has a `_README.md` explaining what it contains and why it was
superseded.
```

---

## Step 3: Update README.md — Project State section

**File:** `README.md`

**Edit:** Replace the stale status snapshot (lines 41-47) with a pointer.

```
old_string:
## Project State

The SC2 pipeline has a working ingestion layer and draft feature/model code, but data
exploration (Phase 01 — see `docs/PHASES.md` and `src/rts_predict/sc2/reports/sc2egset/ROADMAP.md`) has not been completed.
All feature and model code is a draft to be audited and revised as exploration findings
arrive. Do not treat existing module outputs as validated results.

new_string:
## Project Status

Phase progress is tracked per dataset in `PHASE_STATUS.yaml` files — see
`docs/PHASES.md` for the canonical phase list and `ARCHITECTURE.md` for
the full source-of-truth hierarchy.
```

---

## Step 4: Update README.md — Quick Start section

**File:** `README.md`

**Edit:** Update commands to use venv activation (consistency with spec_02).

```
old_string:
## Quick Start
```bash
poetry install
poetry run sc2 --help
poetry run pytest tests/ -v --cov=rts_predict
```

new_string:
## Quick Start
```bash
source .venv/bin/activate && poetry install
source .venv/bin/activate && poetry run sc2 --help
source .venv/bin/activate && poetry run pytest tests/ -v --cov=rts_predict
```
```

---

## Step 5: Update memory — commit message path

**File:** `~/.claude/projects/-Users-tomaszpionka-Projects-rts-outcome-prediction/memory/feedback_git_commit_format.md`

Current content references `temp/commit_msg.txt`. Overwrite with:

```markdown
---
name: git commit format — write to file
description: always write commit message to .github/tmp/commit.txt and use `git commit -F .github/tmp/commit.txt` — heredocs break in zsh
type: feedback
---

Always write the commit message to `.github/tmp/commit.txt` first (using the Write tool), then tell the user to run:

```zsh
git commit -F .github/tmp/commit.txt
```

Never use heredoc forms (`<<'EOF'`) or `$'...'` quoting for commit messages — both fail interactively in zsh for this user.

**Why:** Heredoc `EOF` terminator must be at column 0 which breaks when copy-pasted with any indentation; `$'...'` is fragile for long messages. File-based approach is unambiguous and always works.

**How to apply:** Every time a commit is needed, write `.github/tmp/commit.txt` via Write tool, then provide `git commit -F .github/tmp/commit.txt`. The file lives in `.github/tmp/` alongside `pr.txt` — both are gitignored (except `.gitkeep`).
```

---

## Step 6: Update memory — PR body file (add absolute paths note)

**File:** `~/.claude/projects/-Users-tomaszpionka-Projects-rts-outcome-prediction/memory/feedback_pr_body_file.md`

Overwrite with:

```markdown
---
name: Write PR body to .github/tmp/pr.txt for review
description: Always write the suggested PR body to .github/tmp/pr.txt (absolute path) instead of inline in chat
type: feedback
---

Always write the PR body to `.github/tmp/pr.txt` (overwrite previous content) so the user can review it before running `gh pr create --body-file .github/tmp/pr.txt`.

Always use **absolute paths** when referencing this file in commands — relative paths break when the working directory changes mid-session.

**Why:** User prefers to review the PR body in the file rather than copy-pasting from chat output.

**How to apply:** Any time a PR body is drafted (wrap-up flow or otherwise), write it to `.github/tmp/pr.txt` and tell the user to review it there. The directory has a `.gitkeep` and `.github/tmp/*` is gitignored (except `.gitkeep`), so the file is safe to write and won't be committed.
```

---

## Step 7: Update MEMORY.md index — commit format entry

**File:** `~/.claude/projects/-Users-tomaszpionka-Projects-rts-outcome-prediction/memory/MEMORY.md`

```
old_string:
- [git commit format](feedback_git_commit_format.md) — write message to `temp/commit_msg.txt`, then `git commit -F temp/commit_msg.txt`; heredocs break in zsh

new_string:
- [git commit format](feedback_git_commit_format.md) — write message to `.github/tmp/commit.txt`, then `git commit -F .github/tmp/commit.txt`; heredocs break in zsh
```

---

## Step 8: Run tests to confirm nothing breaks

```bash
source .venv/bin/activate && poetry run pytest tests/ -v --cov=rts_predict --cov-report=term-missing
source .venv/bin/activate && poetry run ruff check src/ tests/
source .venv/bin/activate && poetry run mypy src/rts_predict/
```

No application code changed — only docs, config, and memory files.

---

## Gate condition

- [ ] `grep "absolute" .claude/rules/git-workflow.md` matches
- [ ] `grep "commit.txt" .claude/rules/git-workflow.md` matches
- [ ] README.md "Prior Work" section points to archive directories, not specific deleted files
- [ ] README.md "Project Status" section is a pointer to PHASE_STATUS.yaml, not a snapshot
- [ ] README.md Quick Start uses `source .venv/bin/activate &&` prefix
- [ ] Memory: `feedback_git_commit_format.md` references `.github/tmp/commit.txt`
- [ ] Memory: `feedback_pr_body_file.md` mentions absolute paths
- [ ] Memory: MEMORY.md index updated for commit format entry
- [ ] All tests pass, lint clean, mypy clean
