# RTS Game Result Prediction — Master's Thesis

Predicting match outcomes in StarCraft II (and later AoE2) from replay data.
Classical ML on pre-game features, with optional in-game and GNN comparisons.

## Critical Rules

- **ALWAYS** read `.claude/scientific-invariants.md` before any data/feature/model work
- **ALWAYS** read `PHASE_STATUS.yaml` at session start to know the current phase
- **ALWAYS** use `poetry run <command>` — NEVER bare `python3` or `pip install`
- **NEVER** use data from game T or later to compute features for game T
- **NEVER** begin a new phase until all prior phase artifacts exist on disk
- **NEVER** skip the plan/execute two-session workflow for non-trivial work

## Planning Protocol

When asked to create a plan or run a read-only/planning session:
1. NEVER use Write, Edit, or any file-modifying tool until the user explicitly
   approves the plan
2. Present the plan in chat first and wait for confirmation
3. If user says "read-only", "plan only", or "planning session", do NOT modify
   any files — only use Read, Grep, Bash (read-only commands), and TodoWrite
4. When executing steps from `_current_plan.md`, execute ONLY the steps the user
   specifies (e.g., "steps 3-5") — do not skip ahead or do extra work
5. When wrapping up a PR, move quickly — do not re-explore the repo

## Commands

| Task | Command |
|------|---------|
| Run tests | `poetry run pytest tests/ -v --cov=rts_predict --cov-report=term-missing` |
| Lint | `poetry run ruff check src/ tests/` |
| Type check | `poetry run mypy src/rts_predict/` |
| CLI | `poetry run sc2 --help` |

## Plan / Execute Workflow

All non-trivial work uses two sessions. `_current_plan.md` is the handoff artifact.

**Planning session:** Identify category (A–F), read required context, write plan
to `_current_plan.md`. No code changes. End by asking for approval.

**Execution session:** Read `_current_plan.md` → execute exactly as written → run
tests after each logical unit → report which gate condition is met.

| Category | Branch prefix | Read before planning |
|----------|--------------|---------------------|
| A — Phase work | `feat/` | scientific-invariants.md, docs/PHASES.md, active dataset ROADMAP.md |
| B — Refactor | `refactor/` | (rules load automatically on .py touch) |
| C — Chore | `chore/` | (rules load automatically) |
| D — Bug fix | `fix/` | scientific-invariants.md if data/feature code |
| E — Docs only | `docs/` | — |
| F — Thesis | `docs/thesis-` | thesis-writing rule loads on thesis/ touch |

Category A plan must include: phase/step ref, branch, files, functions with signatures,
SQL queries, test cases, gate condition. Category F: section paths, feeding artifacts,
draft vs revision, figures/tables, WRITING_STATUS.md update.

## Key File Locations

| What | Where |
|------|-------|
| Phase status | `src/rts_predict/<game>/reports/<dataset>/PHASE_STATUS.yaml` |
| Canonical phase list | `docs/PHASES.md` |
| SC2 dataset roadmap | `src/rts_predict/sc2/reports/sc2egset/ROADMAP.md` |
| SC2 game roadmap | `src/rts_predict/sc2/reports/ROADMAP.md` |
| Scientific invariants | `.claude/scientific-invariants.md` |
| Architecture | `ARCHITECTURE.md` |
| Methodology manuals index | `docs/INDEX.md` |
| Research log | `reports/research_log.md` |
| Thesis status | `thesis/WRITING_STATUS.md` |
| Review queue | `thesis/chapters/REVIEW_QUEUE.md` |
| Dev constraints | `.claude/dev-constraints.md` (legacy warnings, ordering, platform) |
| ML experiment protocol | `.claude/ml-protocol.md` |
| Per-dataset invariants | `src/rts_predict/<game>/reports/<dataset>/INVARIANTS.md` |

## Phase Work Execution (Sandbox Notebooks)

All Category A (phase work) code execution happens in Jupyter notebooks under
`sandbox/<game>/<dataset>/`. Each notebook is a jupytext-paired `.py` (percent
format) + `.ipynb` file. The `.py` file is the diff-reviewable source of truth;
the `.ipynb` file carries cell outputs for audit.

**Naming:** `{PHASE}_{PIPELINE_SECTION}_{STEP}_{descriptive_slug}.{py,ipynb}`
**Example:** `sandbox/sc2/sc2egset/01_01_01_source_inventory.py`

**Artifacts:** Notebooks save report artifacts (CSV, JSON, MD, PNG) to
`src/rts_predict/<game>/reports/<dataset>/artifacts/` — never to the dataset
report root directly. Use `get_reports_dir("sc2", "sc2egset") / "artifacts/"`
from `rts_predict.common.notebook_utils`.

**Hard rules:** See `sandbox/README.md` for the full contract (no inline
definitions, 50-line cell cap, read-only DuckDB, both files committed).

## Agent Architecture

5 sub-agents in `.claude/agents/` — see `docs/agents/AGENT_MANUAL.md` for usage.

| Agent | Model | Effort | Role |
|-------|-------|--------|------|
| `planner-science` | opus | max | Thesis methodology, Phase architecture, data science |
| `planner` | sonnet | high | Code refactoring, chores, test planning |
| `executor` | sonnet | high | All implementation (use `/model opus` for hard steps) |
| `reviewer` | sonnet | high | Post-change validation, catches regressions |
| `lookup` | haiku | low | Quick git/shell/file questions |

## Permissions

**Autonomous:** Read/write within repo, poetry/pytest commands, read-only git ops
**Ask first:** Reading outside repo
**User executes:** All git write ops, system installs, DuckDB modifications

## Project Status

Legacy code cleaned in v0.13.2. Surviving caution: `processing.py` →
`create_temporal_split()` uses wrong split strategy (superseded by Phase 03, Splitting & Baselines — see docs/PHASES.md).
AoE2 placeholder exists at `src/rts_predict/aoe2/` — do not add implementation
code until instructed.

## Progress Tracking

- **Session start:** Read the active dataset's PHASE_STATUS.yaml, then scientific-invariants.md
- **After each step:** Update `reports/research_log.md` (mandatory for Category A)
- **After phase gate:** Update PHASE_STATUS.yaml, check thesis/WRITING_STATUS.md
- **After Category F:** Update thesis/chapters/REVIEW_QUEUE.md
- **Session end:** See git-workflow rule (loads on PR/commit operations)
