# Master's Thesis: RTS Game Result Prediction

**Thesis:** "A comparative analysis of methods for predicting game results in real-time strategy games, based on the examples of StarCraft II and Age of Empires II."

This project builds ML models (classical baselines, graph embeddings, and Graph Neural Networks) to predict match outcomes from replay data. All code and methodology must meet Master's thesis standards.

---

## ⚠️ Read First: Scientific Invariants

**Before doing any work in this repository — data exploration, feature engineering,
modelling, evaluation, or even reading other files — read `.claude/scientific-invariants.md`.**

It contains the non-negotiable thesis methodology constraints. They take precedence over
any implementation convenience described elsewhere. Violating them produces results that
cannot be defended at examination.

---

## Plan / Execute Workflow (MANDATORY)

All non-trivial work follows a two-session pattern to preserve context quality.
Planning and execution always happen in separate sessions. `_current_plan.md` is
the handoff artifact between them.

### Session type 1: Planning

Triggered when you ask Claude to "plan", "think through", or "design" something.

1. Identify the work category (see table below) — this determines which context
   files to read and what the plan template looks like.
2. Think through the approach. Ask clarifying questions if needed.
3. Write the finalised plan to `_current_plan.md`, overwriting any previous content.
   The plan must be self-contained — the execution session reads only this file
   and the codebase, not this conversation.
4. Do not write any code or modify any source files during a planning session.
5. End by asking: "Does this plan look correct? I will wait for your approval
   before writing anything to `_current_plan.md`."

### Session type 2: Execution

Triggered when you open a new session and say "execute the current plan" or
"implement `_current_plan.md`".

1. Read `_current_plan.md` in full before doing anything else.
2. Read `.claude/scientific-invariants.md`.
3. Execute exactly what the plan specifies — no design decisions, no additions,
   no improvements beyond what is written. If something is ambiguous or impossible,
   stop and report the specific issue rather than improvising.
4. Follow `.claude/coding-standards.md` when writing code.
5. Run tests after each logical unit of work, not only at the end.
6. When execution is complete, report which gate condition from the plan is now met.

---

### Work categories and what each plan must contain

#### Category A — Phase work (SC2 or AoE2 data pipeline, features, models)

Read before planning:
- `.claude/scientific-invariants.md`
- The relevant phase of `reports/SC2ML_THESIS_ROADMAP.md`

Plan must include:
- Phase and step reference from the roadmap
- Branch name
- Every file to create or modify, with exact paths
- Every function to write, with full signature, docstring, and implementation
  detail sufficient to write without further design decisions
- Every query, with full SQL
- Test cases to write
- The gate condition that defines this plan as complete

#### Category B — Refactoring

Read before planning:
- `.claude/coding-standards.md`
- `.claude/testing-standards.md`

Plan must include:
- Branch name (`refactor/...`)
- What is being restructured and why
- Which files change and what specifically changes in each
- Confirmation that external behaviour is preserved (what tests prove this)
- Any new tests needed to cover previously untested paths exposed by the refactor
- Explicit statement: no new features, no bug fixes — behaviour is unchanged

#### Category C — Chore / maintenance

Read before planning:
- `.claude/coding-standards.md`

Plan must include:
- Branch name (`chore/...`)
- Exact changes (dependency versions, config updates, directory moves, etc.)
- Any test or lint commands needed to verify the change is safe
- Confirmation of scope: what this does NOT touch

#### Category D — Bug fix

Read before planning:
- `.claude/coding-standards.md`
- `.claude/testing-standards.md`
- `.claude/scientific-invariants.md` if the bug is in data or feature code

Plan must include:
- Branch name (`fix/...`)
- Root cause statement
- Exact change to make
- A regression test that fails before the fix and passes after
- Confirmation that the fix does not affect any other behaviour

#### Category E — Documentation only

No mandatory pre-reads beyond understanding the current state of the relevant doc.

Plan must include:
- Branch name (`docs/...`)
- Which files change and what changes in each
- Confirmation that no source code changes

---

### Session type trigger words

| You say | Claude does |
|---------|-------------|
| "Plan ...", "Think through ...", "Design ..." | Planning session — identifies category, then plans |
| "Execute the plan", "Implement `_current_plan.md`" | Execution session |
| "Wrap up into a PR" | PR creation flow from `.claude/git-workflow.md` |
| Anything else | Read `_current_plan.md` first — if it exists and is relevant to the request, treat this as an execution session. If it does not exist or is not relevant, ask whether this is a planning or execution session before starting. |

### Why this separation exists

Planning consumes context with exploration and reasoning. Execution needs that
context budget for reading source files. Mixing them in one session means execution
happens with a partially displaced plan and reduced file-reading capacity.
`_current_plan.md` is the handoff artifact that lets each session start clean.

---

## Project Status: Starting from Correct Foundations

The repository contains existing code written before proper data exploration was conducted.
**Treat all existing modules as legacy drafts, not as correct implementations.**

The authoritative execution plan is `reports/SC2ML_THESIS_ROADMAP.md`. Every session
must begin by reading it to understand which phase is current and what the gate condition
is for advancing. Do not implement features, models, or splits until the phase that
motivates them is complete and its artifacts exist.

The old `reports/ROADMAP.md` is superseded. Do not use it to determine what to work on. Special subdir `reports/archive/` has been created to store no longer valid plans that only might be helpful in future when some legacy code or specific decision understanding is needed.

AoE2 integration is planned after SC2 exploration and modelling is complete.
Do not create any `src/aoe2ml/` structure or AoE2-related files until explicitly
instructed. When AoE2 work begins, a separate roadmap and updated `.claude/` files
will be provided.

---

## Permissions & Safety Boundaries

### Autonomous (no confirmation needed)
- Read and write any files within `/Users/tomaszpionka/Projects/sc2-ml/`
- Run Python scripts, pytest, and poetry commands within the project
- Read-only git operations: `git status`, `git log`, `git diff`, `git branch`, `git show`

### Ask before proceeding
- Reading files outside the repo directory (e.g. `~/duckdb_work/`, `~/Downloads/SC2_Replays/`) — state which path and why, then wait for acknowledgment

### User review required (pass the command, wait for explicit confirmation)
- All git write operations: `git add`, `git commit`, `git push`, `git rebase`, etc. — Claude proposes exact commands; user reviews and executes
- Writing files outside `/Users/tomaszpionka/Projects/sc2-ml/`
- System-level installs (`brew install`, global pip installs)
- Any operation that modifies the DuckDB database at `~/duckdb_work/test_sc2.duckdb`

> **Future:** These permissions will be revised when Docker/Colima container isolation is configured.

---

## Python Execution (MANDATORY)

- **ALWAYS** use `poetry run <command>` or activate `.venv/` first
- **NEVER** use bare `python3`, `python3 -c`, or `pip install`
- Run scripts: `poetry run python -m sc2ml.cli`
- Run tests: `poetry run pytest tests/ src/ -v --cov=sc2ml --cov-report=term-missing`
- **Test location:** Tests are co-located with source — `x/y/z/module.py` → `x/y/z/tests/test_module.py`. Package-internal `tests/` = unit/component tests only. Root `tests/integration/` = cross-package integration tests. Root `tests/` also holds general infra tests and shared helpers. Package-root tests (cli, validation) go in `src/sc2ml/tests/`.
- Lint before commits: `poetry run ruff check src/ tests/`
- Type check: `poetry run mypy src/sc2ml/`

---

## Tech Stack

Python 3.12 | Poetry | PyTorch + PyG | DuckDB | scikit-learn, XGBoost, LightGBM | pandas, numpy | matplotlib | NetworkX, Gensim | Apple M4 Max (36GB RAM, MPS-capable)

---

## Reference Files (sub-files in `.claude/`)

| File | Contents |
|------|----------|
| `.claude/scientific-invariants.md` | **Thesis methodology constraints — read before any work** |
| `.claude/project-architecture.md` | Structural guidance: package layout, patterns, identifier design, legacy code warnings |
| `.claude/ml-protocol.md` | Experiment methodology, leakage rules, documentation artifacts |
| `.claude/python-workflow.md` | Venv, Poetry, execution rules, MPS/GPU, build deps |
| `.claude/testing-standards.md` | Coverage, test patterns, edge cases, commit gates |
| `.claude/coding-standards.md` | Style, type hints, linting, docstrings, pre-commit checks |
| `.claude/git-workflow.md` | Branches, commits, end-of-session checklist |
| `.claude/aoe2-plan.md` | AoE2 integration notes (upcoming) |
| `reports/SC2ML_THESIS_ROADMAP.md` | **The authoritative phase-by-phase execution plan** |

---

## Progress Tracking (MANDATORY)

- **Before starting any work:** Read `.claude/scientific-invariants.md`. For
  Category A (phase work), also read `reports/SC2ML_THESIS_ROADMAP.md` to
  identify the current phase and its gate condition before planning anything.
- **Do not begin a new phase** until all artifacts from the previous phase
  exist on disk.
- **After completing any step:** Update `reports/research_log.md` with findings,
  decisions, and any deviations — for Category A work this is mandatory, for
  other categories only if something non-obvious was decided.
- **After code changes:** Follow `.claude/git-workflow.md`.

## End-of-Session Checklist

> See `.claude/git-workflow.md` for full details on branches, commits, and conventions.

**If wrapping up into a PR:** follow the full PR creation flow in `.claude/git-workflow.md`
— this includes autonomous version bump in `pyproject.toml`, `CHANGELOG.md`, and
`src/sc2ml/__init__.py` before proposing the push.

**If not wrapping up into a PR:**

1. All tests pass with coverage report
2. Ruff and mypy clean
3. `CHANGELOG.md` updated — current work documented under `[Unreleased]`; version is
   not bumped until PR creation
4. Phase artifacts from `reports/SC2ML_THESIS_ROADMAP.md` verified to exist on disk
5. `reports/research_log.md` updated with findings, decisions, and any issues encountered
6. Proposed commit messages for all uncommitted work
7. Summary of what's ready to merge and what's still in progress
