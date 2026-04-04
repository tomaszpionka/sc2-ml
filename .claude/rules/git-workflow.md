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

1. Run checks: pytest, ruff, mypy (skip if no .py staged)
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

```bash
gh pr create --title "<type(scope): description>" --body "$(cat <<'EOF'
## Summary

- <bullet>

## Test plan

- [x] <step>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

## End-of-Session Checklist (non-PR)
1. Tests pass with coverage
2. Ruff and mypy clean
3. CHANGELOG.md updated under `[Unreleased]`
4. research_log.md updated (mandatory for Category A)
5. Proposed commit messages for uncommitted work
6. Summary of ready-to-merge vs in-progress
