# RTS Game Result Prediction — Master's Thesis

Predicting match outcomes in StarCraft II (and later AoE2) from replay data.
Classical ML on pre-game features, with optional in-game and GNN comparisons.

## Critical Rules

- **ALWAYS** read `.claude/scientific-invariants.md` before any data/feature/model work
- **ALWAYS** read `PHASE_STATUS.yaml` before any Category A or F work
- **ALWAYS** activate the venv first: `source .venv/bin/activate && poetry run <command>` — NEVER bare `python3` or `pip install`
- Running Python via the activated venv (`source .venv/bin/activate && poetry run python ...`) is permitted for testing, data exploration, and validation
- **NEVER** use data from game T or later to compute features for game T
- **NEVER** begin a new phase until all prior phase artifacts exist on disk
- **NEVER** skip the plan/execute two-session workflow for non-trivial work
- **NEVER** read `current_plan.md` or spec files when dispatching executors during DAG execution — read ONLY `DAG.yaml` and pass the `spec_file` path as a pointer

## Planning Protocol

When asked to create a plan or run a read-only/planning session:
1. NEVER use Write, Edit, or any file-modifying tool until the user explicitly
   approves the plan
2. Present the plan in chat first and wait for confirmation
3. If user says "read-only", "plan only", or "planning session", do NOT modify
   any files — only use Read, Grep, Bash (read-only commands), and TodoWrite
4. When executing steps from `planning/current_plan.md`, execute ONLY the steps the user
   specifies (e.g., "steps 3-5") — do not skip ahead or do extra work
5. When wrapping up a PR, move quickly — do not re-explore the repo

## Commands

| Action | Command |
|------|---------|
| Run tests | `source .venv/bin/activate && poetry run pytest tests/ -v --cov=rts_predict --cov-report=term-missing` |
| Lint | `source .venv/bin/activate && poetry run ruff check src/ tests/` |
| Type check | `source .venv/bin/activate && poetry run mypy src/rts_predict/` |
| CLI | `source .venv/bin/activate && poetry run sc2 --help` |

> `ruff` (lint) and `mypy` (type check) also run automatically as pre-commit hooks on every `git commit`. Manual runs above are for diagnosing errors, not routine post-change checks.

## Plan / Execute Workflow

All non-trivial work uses three phases. `planning/current_plan.md` is the
handoff artifact; `planning/dags/DAG.yaml` and `planning/specs/spec_*.md`
are the execution contract.

See `planning/README.md` for the full planning and materialization protocol.
Key rule: execution MUST NOT begin until DAG + specs exist on disk.

**Execution:** Read `planning/dags/DAG.yaml` → dispatch agents per task groups →
agents read their assigned spec file, not the full plan → review gates after
groups that configure one (optional) → run tests after each logical unit →
report which gate condition is met.

**Dispatch rules:**
- *Executor dispatch:* The prompt MUST be a pointer — the `spec_file` path +
  at most a 1-2 line context summary. MUST NOT restate spec content. The spec
  is the sole source of truth and the executor reads it via tool call.
- *Review gate dispatch:* After each task group, check if the group has a
  `review_gate` configured. If yes, dispatch the specified agent — the prompt
  passes the diff scope and the reviewer reads the diff itself, not the specs.
  If no `review_gate` is present, proceed to the next task group without review.
- *Final review dispatch:* Dispatch the agent specified in the DAG's
  `final_review` section with: (a) `plan_ref` path from the DAG, (b) all
  `spec_file` paths from the DAG, (c) `base_ref` for the diff, (d) the
  session context header (see below). **Review agent by category:**
  reviewer-adversarial for Cat A phase work and multi-job DAGs;
  reviewer-deep for Cat B/D; **reviewer (Sonnet) for Cat C/E** — no
  science reads needed for chores and docs. The final reviewer reads the
  plan, all specs, and the full diff. The orchestrator passes these paths
  from DAG metadata — it does NOT read them itself.
- *General:* "Execute the DAG" means: read `DAG.yaml`, dispatch per its graph,
  nothing more. The orchestrator does NOT read `current_plan.md` or spec
  files when dispatching.

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

See `ARCHITECTURE.md` for the full cross-cutting files table and source-of-truth
hierarchy. Quick pointers for the most common lookups:

- Step status: `src/rts_predict/games/<game>/datasets/<dataset>/reports/STEP_STATUS.yaml`
- Phase status: `src/rts_predict/games/<game>/datasets/<dataset>/reports/PHASE_STATUS.yaml`
- Scientific invariants: `.claude/scientific-invariants.md`
- Canonical phase list: `docs/PHASES.md`
- Directory map: `docs/INDEX.md`

## Phase Work Execution

See `sandbox/README.md` for the full notebook contract. Key rule:
all Category A code execution happens in jupytext-paired notebooks under
`sandbox/<game>/<dataset>/`.

## Agent Architecture

8 sub-agents in `.claude/agents/` — see `docs/agents/AGENT_MANUAL.md` for
usage, model assignments, and routing rules.

## Permissions

**Autonomous:** Read/write within repo, poetry/pytest commands, read-only git ops, `git add`, `git commit`, `git rebase` (non-interactive), `rm .github/tmp/*`, `gh pr create`, `gh issue`
**Ask first:** `git push`, destructive git ops (`reset --hard`, `clean`, `checkout --`), `rm -r`, reading outside repo (except system libs/pip packages for debugging)
**User executes:** System installs, DuckDB schema modifications

## Project Status

Legacy code cleaned in v0.13.2. Surviving caution: `processing.py` →
`create_temporal_split()` uses wrong split strategy (superseded by Phase 03, Splitting & Baselines — see docs/PHASES.md).
AoE2 placeholder exists at `src/rts_predict/games/aoe2/` — do not add implementation
code until instructed.

## Progress Tracking

See `ARCHITECTURE.md` for the full tracking protocol. Key rules:
- **Session start:** Read active STEP_STATUS.yaml and PHASE_STATUS.yaml, then scientific-invariants.md
- **After Category A step:** Update the active dataset's `research_log.md`
- **After phase gate:** Update PHASE_STATUS.yaml, check `thesis/WRITING_STATUS.md`
- **After Category F:** Update `thesis/chapters/REVIEW_QUEUE.md`
- **Session end:** See git-workflow rule (loads on PR/commit operations)
