# Spec 04: Custom /pr Skill

**Category:** C — Chore
**Branch:** `chore/pr-skill`
**Source:** `temp/audit_plan.md` §3 Feature 1, §10 Follow-up
**Depends on:** spec_02 (venv activation convention) and spec_03 (git-workflow
consolidation) should be merged first so that the skill references the correct
command prefixes and ephemeral file paths. If running before those specs,
adjust `source .venv/bin/activate &&` prefixes and `.github/tmp/` paths
accordingly.

---

## Context

The PR wrap-up workflow (`.claude/rules/git-workflow.md` § PR Creation Flow)
is a 7-step process that Claude must execute on every "wrap up" request. Today,
the user must either spell out the steps or rely on Claude reading the rule
file and following it correctly. A custom skill turns this into a single
`/pr` command that expands the full workflow as a prompt.

Claude Code custom skills live in `.claude/commands/` as markdown files. The
filename (minus `.md`) becomes the slash command. The file content is injected
as a system prompt when the user types the command. `$ARGUMENTS` is replaced
with any text the user types after the command name.

---

## Step 1: Create the commands directory

**Action:** Create the directory `.claude/commands/`.

```bash
mkdir -p .claude/commands
```

**Verify:** `ls -d .claude/commands` succeeds.

---

## Step 2: Create the /pr skill file

**File:** `.claude/commands/pr.md` (NEW FILE)

**Content:**

```markdown
# PR Wrap-Up

Complete the full PR creation workflow for the current branch.

## Arguments

If the user provided arguments: `$ARGUMENTS`
Use them as additional context (e.g., target base branch, PR title hint).

## Pre-flight

1. Run `git branch --show-current` to confirm you are NOT on master/main.
   If on master/main, STOP and tell the user to create a feature branch first.
2. Run `git log --oneline master..HEAD` to see all commits on this branch.
3. Run `git diff --stat master..HEAD` to see files changed vs the base branch.

## Step 1: Run checks

If the diff contains `.py` files, run all three checks. If no `.py` files
were changed, skip to Step 2.

a. `source .venv/bin/activate && poetry run ruff check src/ tests/`
b. `source .venv/bin/activate && poetry run mypy src/rts_predict/`
c. `source .venv/bin/activate && poetry run pytest tests/ -v --cov --cov-report=term-missing | tee coverage.txt`

After step c, read `coverage.txt` and verify coverage meets the 95% threshold
(`fail_under = 95` in `pyproject.toml`). If coverage is below 95%, report the
uncovered lines and STOP — do not proceed until coverage is fixed.

After confirming coverage passes, delete `coverage.txt`.

If any check fails, report the failure and STOP. Do not proceed until all
checks pass.

## Step 2: Version bump

Determine the version bump type from the branch prefix:
- `feat/`, `refactor/`, `docs/` → minor bump
- `fix/`, `test/`, `chore/` → patch bump

Read the current version from `pyproject.toml`. Propose the new version to
the user. Do NOT bump until the user confirms.

After confirmation, update `version` in `pyproject.toml` (the SINGLE source
of truth — no `__version__` in any `__init__.py`).

## Step 3: Update CHANGELOG.md

Move the `[Unreleased]` section contents to a new version heading:
`[X.Y.Z] — YYYY-MM-DD (PR #N: branch-name)`

Leave `[Unreleased]` empty with the standard headers:
Added, Changed, Fixed, Removed.

## Step 4: Release commit

Write the commit message to `.github/tmp/commit.txt`:
```
chore(release): bump version to X.Y.Z
```

Tell the user to run:
```
git add -A && git commit -F .github/tmp/commit.txt
```

Wait for the user to confirm the commit succeeded before proceeding.

## Step 5: Write PR body

Analyze the full diff (`git diff master..HEAD`) and commit log to draft a PR
body following the template in `.github/pull_request_template.md`:

- `## Summary` — 1-5 bullets describing what changed and why
- `## Motivation` — include only when the reason is non-obvious; omit otherwise
- `## Test plan` — concrete steps: commands run, artifacts verified, regressions checked
- Footer: `🤖 Generated with [Claude Code](https://claude.com/claude-code)`

Write the PR body to `.github/tmp/pr.txt` using the Write tool.
Tell the user: "PR body written to `.github/tmp/pr.txt` — please review it."

## Step 6: Propose PR creation

After the user confirms the PR body is acceptable, propose the command:

```
git push -u origin $(git branch --show-current) && gh pr create --title "<type(scope): description>" --body-file .github/tmp/pr.txt
```

Replace `<type(scope): description>` with an appropriate title based on the
branch prefix and changes (keep under 70 characters).

The user executes this command — do NOT run git push or gh pr create yourself.

## Step 7: Clean up

After the user confirms the PR was created, delete the ephemeral files:

```
rm -f .github/tmp/pr.txt .github/tmp/commit.txt
```

Report the PR URL if visible in the gh output.

## Rules

- NEVER run `git push`, `git commit`, or `gh pr create` yourself — propose
  commands for the user to execute.
- ALWAYS use absolute paths for ephemeral files.
- ALWAYS use `source .venv/bin/activate &&` before poetry commands.
- If `_current_plan.md` exists, check whether it should be deleted or kept
  for the PR description context.
```

**Verify:** `cat .claude/commands/pr.md | head -1` returns `# PR Wrap-Up`.

---

## Step 3: Document the skill in AGENT_MANUAL.md

**File:** `docs/agents/AGENT_MANUAL.md`

**Edit:** Add a new section between the "Hooks" section and "When to Use
`/model` vs Agents". Find and replace:

```
old_string:
---

## When to Use `/model` vs Agents

new_string:
## Custom Skills (Slash Commands)

Skills live in `.claude/commands/` as markdown files. The filename becomes
the slash command. Type the command and Claude expands the file as a prompt.

| Command | File | What it does |
|---------|------|--------------|
| `/pr` | `.claude/commands/pr.md` | Full PR wrap-up: checks, version bump, CHANGELOG, PR body, cleanup |

### `/pr` — PR Wrap-Up

Type `/pr` when you are ready to create a pull request. Optionally add
arguments (e.g., `/pr target main` or `/pr skip-checks`) as context hints.

The skill walks through the complete PR Creation Flow from
`.claude/rules/git-workflow.md`:
1. Pre-flight (branch check, commit log, diff summary)
2. Lint + mypy + pytest with coverage gate
3. Version bump proposal (user confirms)
4. CHANGELOG update
5. Release commit (user executes)
6. PR body written to `.github/tmp/pr.txt` (user reviews)
7. PR creation command proposed (user executes)
8. Ephemeral file cleanup

**Key safety property:** Claude never runs `git push`, `git commit`, or
`gh pr create` — it proposes commands for the user to execute.

**Planned follow-up:** `/execute-plan` — a skill to execute steps from
`_current_plan.md` or a `specs/spec_NN.md` file without spelling out the
full instruction each time.

---

## When to Use `/model` vs Agents
```

**Verify:** `grep "/pr" docs/agents/AGENT_MANUAL.md` returns matches in the
new "Custom Skills" section.

---

## Step 4: Run tests to confirm nothing breaks

```bash
source .venv/bin/activate && poetry run pytest tests/ -v --cov=rts_predict --cov-report=term-missing
source .venv/bin/activate && poetry run ruff check src/ tests/
source .venv/bin/activate && poetry run mypy src/rts_predict/
```

No application code changed — only a new markdown file and documentation.
Tests must still pass at the same coverage level.

---

## Gate condition

- [ ] `.claude/commands/` directory exists
- [ ] `.claude/commands/pr.md` exists and starts with `# PR Wrap-Up`
- [ ] `grep "source .venv" .claude/commands/pr.md` matches (venv prefix used)
- [ ] `grep "NEVER run.*git push" .claude/commands/pr.md` matches (safety rule present)
- [ ] `grep ".github/tmp/pr.txt" .claude/commands/pr.md` matches (correct ephemeral path)
- [ ] `grep "Custom Skills" docs/agents/AGENT_MANUAL.md` matches
- [ ] `grep "/pr" docs/agents/AGENT_MANUAL.md` matches in the new section
- [ ] `grep "execute-plan" docs/agents/AGENT_MANUAL.md` matches (follow-up noted)
- [ ] All tests pass, lint clean, mypy clean
