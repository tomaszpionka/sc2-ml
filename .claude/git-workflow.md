# Git Workflow & Session Management

## Feature Branches

Each work session maps to a feature branch. Claude proposes a branch name at session
start using conventional prefixes:

- `feat/` — new functionality (e.g. `feat/exploration-phase-1`)
- `fix/` — bug fixes (e.g. `fix/replay-id-extraction`)
- `refactor/` — code restructuring (e.g. `refactor/ingestion-schema`)
- `docs/` — documentation only (e.g. `docs/scientific-invariants`)
- `test/` — adding or improving tests (e.g. `test/temporal-leakage-checks`)
- `chore/` — maintenance tasks (e.g. `chore/superseded-code-cleanup`)

## Commit Messages

[Conventional Commits](https://www.conventionalcommits.org/) format:
```
type(scope): short description
Optional body with context.
```
Examples: `feat(exploration): add phase 1 corpus inventory`, `fix(ingestion): correct tournament_dir extraction depth`

## Atomic Commits

Each commit should be a single logical unit. Prefer multiple small commits over one
large one. Do not bundle unrelated changes.

## Wrapping Up: PR Creation Flow

When asked to wrap up changes into a PR, Claude must complete all of the following
steps autonomously in order before handing off:

### Step 1 — Verify all checks pass
Skip if there is no .py file in the staged files, otherwise:
```bash
poetry run pytest tests/ src/ -v --cov=rts_predict --cov-report=term-missing
poetry run ruff check src/ tests/
poetry run mypy src/
```

All three must be clean. Do not proceed if any fail.

### Step 2 — Determine the new version

Read the current version from `pyproject.toml` (`version = "X.Y.Z"`).

Apply semantic versioning:
- **Minor bump** (`X.Y.0 → X.Y+1.0`) for every feature branch (`feat/`) and most
  `refactor/` and `docs/` branches — i.e. any PR that adds capability or changes
  behaviour
- **Patch bump** (`X.Y.Z → X.Y.Z+1`) for `fix/`, `test/`, and `chore/` branches
  that correct existing behaviour without adding new capability
- **Major bump** (`X.0.0`) only when explicitly instructed

When in doubt between minor and patch, use minor. State the chosen version and
the reasoning in a single sentence before making any file changes.

### Step 3 — Update `pyproject.toml`

Replace the `version` field with the new version string. No other changes.

### Step 4 — Update `CHANGELOG.md`

Move the entire contents of the `[Unreleased]` section into a new versioned section
immediately below the `[Unreleased]` header. The new section header format is:
```
[X.Y.Z] — YYYY-MM-DD (PR #N: branch-name)
```
Use today's date. Use the branch name exactly as it appears in git. For the PR number:
if the remote already has a PR open, use that number; otherwise write `PR: pending`
and note that the number should be filled in after the PR is created on GitHub.

Leave the `[Unreleased]` section empty and ready for the next branch:
```markdown
## [Unreleased]

### Added

### Changed

### Fixed

### Removed
```

### Step 5 — Bump version in `pyproject.toml`

Update the `version` field in `pyproject.toml`. This is the **single** version
location — do not add `__version__` to any `__init__.py`.

### Step 6 — Commit the version bump
```
chore(release): bump version to X.Y.Z
```
This commit contains only the `pyproject.toml` and `CHANGELOG.md` changes. Nothing else.

### Step 7 — Propose the push and PR commands

Provide the exact commands for the user to review and execute (these require user
confirmation per the permissions in `CLAUDE.md`):
```bash
git push origin <branch-name>
```

Then the GitHub CLI command to open the PR:
```bash
gh pr create --title "<type>(scope): description" --body "<summary of changes>"
```

Or, if `gh` is not available, provide the GitHub URL to open the PR manually.

---

## End-of-Session Checklist (non-PR sessions)

For sessions that do not end in a PR, run before wrapping up:

1. All tests pass: `poetry run pytest tests/ src/ -v --cov=rts_predict --cov-report=term-missing`
2. Ruff clean: `poetry run ruff check src/ tests/`
3. Mypy clean: `poetry run mypy src/rts_predict/`
4. `CHANGELOG.md` updated — current work documented under `[Unreleased]`
5. `reports/research_log.md` updated if the session involved experimentation,
   methodology decisions, issues, or breakthroughs
6. Proposed commit messages provided for all uncommitted work
7. Summary of what's ready to merge and what's still in progress

Note: version is **not** bumped mid-session. Version bumps happen only at PR creation.
