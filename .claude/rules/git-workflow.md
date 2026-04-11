---
paths:
  - "CHANGELOG.md"
  - "pyproject.toml"
  - "_current_plan.md"
---

# Git Workflow

## Branches
`feat/` `fix/` `refactor/` `docs/` `test/` `chore/` — conventional prefixes.
Commits: `type(scope): short description`. Atomic — one logical unit per commit.

## PR Creation Flow (on "wrap up")

1. Run checks (skip if no .py files in diff):
   a. ruff and mypy are enforced by pre-commit hook — they run on every commit. No manual run needed at PR time unless diagnosing a specific error.
   b. `source .venv/bin/activate && poetry run pytest tests/ -v --cov --cov-report=term-missing | tee coverage.txt`
      (`--cov` without a path uses `[tool.coverage.run] source` from `pyproject.toml`,
      which is `src/rts_predict` — covers all game and common packages)
   c. Read and analyze `coverage.txt` — identify uncovered lines in project code
   d. Add tests / fix code until coverage is at least 95% (`fail_under = 95` enforced in
      `[tool.coverage.report]` of `pyproject.toml`; threshold must not be lowered)
   e. Re-run step b to verify, then delete `coverage.txt`
2. Version: minor for feat/refactor/docs, patch for fix/test/chore
3. Bump `version` in `pyproject.toml` (SINGLE source — NO `__init__.py`)
4. Move `[Unreleased]` → `[X.Y.Z] — YYYY-MM-DD (PR #N: branch)`
5. Leave `[Unreleased]` empty with Added/Changed/Fixed/Removed headers
6. Commit: `chore(release): bump version to X.Y.Z`
7. Propose push + PR commands for user to execute

### PR Body Format

The PR body **must follow the template** in `.github/pull_request_template.md`:

- `## Summary` — 1–5 bullets describing what changed and why
- `## Motivation` — include only when the reason is non-obvious from the summary; omit otherwise
- `## Test plan` — concrete, checkable steps: commands run, artifacts verified, regressions checked
- Footer line: `🤖 Generated with [Claude Code](https://claude.com/claude-code)`

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

## End-of-Session Checklist (non-PR)
1. Tests pass with coverage
2. Ruff and mypy clean
3. CHANGELOG.md updated under `[Unreleased]`
4. research_log.md updated (mandatory for Category A)
5. Proposed commit messages for uncommitted work
6. Summary of ready-to-merge vs in-progress
