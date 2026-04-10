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
