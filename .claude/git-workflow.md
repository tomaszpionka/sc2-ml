# Git Workflow & Session Management

## Feature Branches

Each work session maps to a feature branch. Claude proposes a branch name at session start using conventional prefixes:
- `feat/` — new functionality (e.g. `feat/aoe2-data-pipeline`)
- `fix/` — bug fixes (e.g. `fix/elo-dedup-race-condition`)
- `refactor/` — code restructuring (e.g. `refactor/poetry-setup`)
- `docs/` — documentation only (e.g. `docs/claude-md-guidelines`)
- `test/` — adding or improving tests (e.g. `test/feature-leakage-checks`)
- `chore/` — maintenance tasks (e.g. `chore/gitignore-cleanup`)

## Commit Messages

[Conventional Commits](https://www.conventionalcommits.org/) format:
```
type(scope): short description

Optional body with context.
```
Examples: `feat(gnn): add temporal edge masking`, `fix(elo): prevent duplicate updates per match`

## Atomic Commits

Each commit should be a single logical unit — don't bundle unrelated changes. Prefer multiple small commits over one large one.

## End-of-Session Checklist

Before wrapping up a work session, ensure:
1. All tests pass: `poetry run pytest tests/ -v --cov=sc2ml --cov-report=term-missing`
2. Ruff clean: `poetry run ruff check src/ tests/`
3. Mypy clean: `poetry run mypy src/sc2ml/`
4. `CHANGELOG.md` updated — current work under `[Unreleased]`; on merge, promote to versioned section and bump `__version__`
5. `reports/research_log.md` updated if the session involved experimentation, methodology decisions, issues, or breakthroughs
6. Proposed commit messages provided for all uncommitted work
7. Summary of what's ready to merge and what's still in progress
