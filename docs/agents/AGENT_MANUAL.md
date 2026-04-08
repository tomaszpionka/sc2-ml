# Agent Manual — RTS Thesis Workflow

How to use the 5-agent Claude Code architecture for the master's thesis.

---

## Quick Reference

| What you want to do | What to type |
|---------------------|--------------|
| Quick question (git, files, commands) | `@lookup what branch am I on?` |
| Plan a Phase step or thesis methodology | `@planner-science plan Phase 2 step 2.1` |
| Plan a refactoring or chore | `@planner plan test coverage for exploration.py` |
| Execute any plan steps | `@executor execute steps 3-5 from _current_plan.md` |
| Hard step needing Opus reasoning | `/model opus` then work normally, `/model sonnet` after |
| Validate work after execution | `@reviewer review changes` |

---

## Decision Flowchart

Don't overthink agent selection. Three questions:

```
1. Quick lookup?
   YES → @lookup
   NO  ↓

2. Planning or executing?
   PLANNING ↓                    EXECUTING ↓
   
3a. Thesis science or           3b. Just use @executor.
    Phase work?                      Switch /model opus
    YES → @planner-science           for genuinely hard
    NO  → @planner                   steps if needed.

After execution → @reviewer
```

---

## The 5 Agents

### `planner-science` — Thesis Architect (Opus, max effort)

**When to use:** Planning anything touching thesis methodology.

- Phase work design (any of Phases 0-10)
- Data exploration / cleaning rule strategy
- Feature engineering or evaluation framework design
- Statistical methodology, temporal discipline decisions
- Cross-game comparability protocol
- Thesis chapter structure and content planning

**What it does:** Reads your roadmap, scientific invariants, and research log.
Produces a detailed plan with phase/step references, file lists, function
signatures, SQL queries, test cases, and gate conditions.

**What it does NOT do:** Write any files. It's read-only. You approve the plan,
then write it to `_current_plan.md` (or let the parent session do it).

**Example:**
```
@planner-science plan Phase 1 step 1.8 — game settings and field completeness audit
```

### `planner` — Code Architect (Sonnet, high effort)

**When to use:** Planning non-scientific infrastructure work.

- Refactoring, renaming, module reorganization
- Test coverage expansion
- Documentation restructuring
- Dependency updates, CI/CD, tooling chores

**Example:**
```
@planner plan test coverage expansion for exploration.py edge cases
```

### `executor` — The Workhorse (Sonnet, high effort)

**When to use:** All implementation work — both science and code.

This is a single agent that handles everything from Phase work DuckDB queries
to test writing to thesis chapter drafting. For the 2-3 genuinely complex steps
per session (subtle temporal leakage prevention, tricky SQL window functions,
thesis prose requiring deep domain reasoning), switch to Opus mid-session:

```
/model opus          ← switch for the hard step
[do the complex work]
/model sonnet        ← switch back for routine steps
```

This preserves full session context across the switch. An agent restart would
lose it.

**Example:**
```
@executor execute steps 1-3 from _current_plan.md
```

### `reviewer` — Quality Gate (Sonnet, high effort)

**When to use:** After any significant executor work. Runs the full verification
battery and produces a structured APPROVE / REQUEST_CHANGES verdict.

**What it checks for code:**
- Full test suite, lint, type check
- Every modified file: type hints, docstrings, no magic numbers
- Temporal leakage patterns (features at T using data >= T)
- Silent row drops without logging

**What it checks for thesis chapters:**
- Critical Review Checklist (numerical traceability, claim-evidence alignment)
- Every number traces to a report artifact
- Academic register, citation formatting

**Invoke with scope when possible:**
```
@reviewer review src/rts_predict/sc2/data/exploration.py
@reviewer review thesis/chapters/03_data.md
@reviewer review changes                    ← reviews everything modified
```

**Important caveat:** The reviewer runs on Sonnet. For Phase 7+ data science
code with subtle temporal leakage risks, the reviewer will flag for Pass 2
review in Claude Chat (this Project, on Opus). Sonnet catches mechanical
errors reliably; subtle statistical reasoning issues need Opus review.

### `lookup` — Speed Dial (Haiku)

**When to use:** Any question answerable in 30 seconds.

```
@lookup how many tests do we have?
@lookup what's in PHASE_STATUS.yaml?
@lookup which file defines DATASET_DIR?
@lookup git log --oneline -5
```

---

## Standard Workflows

### Workflow A: Phase Work (most common)

Phase work executes in `sandbox/` notebooks. The plan specifies the notebook path
(`sandbox/<game>/<dataset>/XX_XX_<name>.py`). The executor creates the jupytext
`.py` + `.ipynb` pair, runs the analysis, and saves artifacts to
`src/rts_predict/<game>/reports/<dataset>/artifacts/`.

```
Step 1:  @planner-science plan Phase N step N.X
Step 2:  [review plan in chat, request adjustments]
Step 3:  [approved plan → write to _current_plan.md]
Step 4:  @executor execute steps 1-3
         (notebook in sandbox/, artifacts to reports/<dataset>/artifacts/)
         (use /model opus for hard analytical steps)
Step 5:  @reviewer review changes
Step 6:  [fix issues from reviewer]
Step 7:  [wrap up PR when reviewer approves]
```

### Workflow B: Thesis Chapter

```
Step 1:  @planner-science plan chapter §X.Y writing
Step 2:  [approve plan]
Step 3:  @executor execute chapter draft
         (use /model opus — thesis writing benefits from deep reasoning)
Step 4:  @reviewer review changes
         (mechanical checks: numbers, citations, register)
Step 5:  [fix issues]
Step 6:  [bring to Claude Chat for Pass 2 — literature validation]
```

### Workflow C: Code Chore

```
Step 1:  @planner plan the refactoring
Step 2:  [approve plan]
Step 3:  @executor execute steps 1-5
Step 4:  @reviewer review changes
Step 5:  [wrap up PR]
```

### Workflow D: Quick Question

```
@lookup what branch am I on?
```

No planning, no execution, no review.

---

## Permission Model

Three layers protect your work:

### Layer 1: Deny rules (always blocked)
- Writes to raw data (`src/**/data/*/raw/**`) — immutable source
- `rm -rf`, `rm -r` — destructive file deletion
- `git push`, `git reset --hard`, `git checkout --`, `git clean`

### Layer 2: Allow rules (zero friction)
- All reads everywhere (Read, Grep, Glob)
- Bash read-only commands (cat, find, ls, grep, head, tail, wc)
- Poetry, ruff, mypy, git status/log/diff/branch/show
- Write/Edit to all repo paths (src/, tests/, thesis/, reports/, docs/, etc.)

### Layer 3: Guard hook (catches the rest)
- Write inside repo → allowed silently
- Write inside `~/` but outside repo → asks you for permission
- Write outside `~/` → blocked with error message

**Result:** Normal work flows without any permission prompts. Dangerous
operations are blocked. Edge cases ask you first.

---

## Model & Cost Strategy

| Agent | Model | When Opus is used |
|-------|-------|-------------------|
| `planner-science` | Opus (always) | Every invocation — thesis methodology needs it |
| `planner` | Sonnet | Never — code planning doesn't need Opus |
| `executor` | Sonnet (default) | Only when you `/model opus` for hard steps |
| `reviewer` | Sonnet | Never — mechanical checks don't need Opus |
| `lookup` | Haiku | Never — quick questions don't need Sonnet |

**Session default (`opusplan`):** Opus activates automatically in `/plan` mode
(Shift+Tab). Regular interaction uses Sonnet. Sub-agents override this with
their frontmatter model setting.

**Cost optimization rules of thumb:**
- Use `@lookup` for quick questions, not the main session
- Default to `@executor` on Sonnet; switch `/model opus` only for the step
  that actually needs deep reasoning, then switch back
- `@planner-science` is expensive — don't use it for code planning
- `@reviewer` is cheaper than re-doing work because of missed bugs

---

## Hooks: What Runs Automatically

### PostToolUse: Auto-lint (after every .py edit)
Ruff runs automatically on the changed file. If there are lint errors, Claude
sees them and self-corrects. No manual `ruff check` between edits.

### PreToolUse: Write Guard (before every Write/Edit)
Checks the target path. Inside repo = silent. Outside repo in home = asks you.
Outside home = blocked. Protects your system from accidental writes.

---

## When to Use `/model` vs Agents

**Use agents when:**
- Starting a new task (planner or executor)
- You want tool restrictions (planners can't write, reviewer can't edit)
- You want a specific model tier guaranteed (planner-science = always Opus)

**Use `/model` switch when:**
- You're mid-execution and one step needs deeper reasoning
- You want to keep session context (agent invocation starts fresh)
- The task mixes easy and hard sub-steps in one session

**Both work together:** You can be in an `@executor` session and the user
can also `/model opus` to upgrade the main session for ad-hoc questions
between agent invocations.

---

## Future: Autonomous Long Sessions

The current architecture is designed for interactive, human-steered sessions.
A future enhancement will add support for autonomous multi-hour sessions
where an agent works through an entire Phase independently:

- Uses `maxTurns` in agent frontmatter to allow extended execution
- Uses `isolation: worktree` for safe parallel work
- Implements test gates as mandatory checkpoints between steps
- Records decisions and restarts in research_log.md
- May use Docker for reproducible environments

The 5-agent architecture is forward-compatible with this. The planner produces
the plan, the executor runs it with high maxTurns, and the reviewer validates
at the end. The only additions needed are the test-gate mechanism and worktree
isolation — no architectural changes.

---

## Troubleshooting

**Agent not being invoked:** Claude sometimes handles tasks in the main
session instead of delegating. Three fixes, in order of reliability:

1. Use the `@` typeahead picker (type `@`, select from dropdown) — this
   *guarantees* invocation, unlike typing `@agent-name` as plain text.
2. Use explicit phrasing: "Use the planner-science agent to plan..."
3. Nuclear option: `claude --agent planner-science` from the integrated
   terminal to run the entire session as that agent.

**How to verify an agent actually ran:**

1. Check `/tmp/rts-agent-log.txt` — our SubagentStart/Stop hooks log
   every invocation with timestamps and transcript paths.
2. Run `./scripts/debug/find-session.sh` to find subagent transcripts (stored under
   `<session_id>/subagents/agent-<agent_id>.jsonl`). The `transcript=` value in
   `/tmp/rts-agent-log.txt` gives the exact path.
3. Look for the agent's color badge in the UI (purple = planner-science,
   blue = planner, green = executor, orange = reviewer, cyan = lookup).
4. Press Ctrl+O to toggle verbose mode — subagent spawning shows in the
   tool call stream.

**Permission prompt appearing for read-only agents:** If planner-science
shows "Allow this bash command?", the agent wasn't invoked as a subagent
(planners use `permissionMode: plan` which is read-only). You're seeing
the main session's permission mode. Fix: use `@` typeahead or `--agent`.

**Agent loaded but using wrong model:** Run `claude agents` from the
terminal. The model should show next to each agent name. If it shows
`inherit`, the frontmatter `model:` field isn't being picked up —
check YAML syntax. For definitive testing, set
`export CLAUDE_CODE_SUBAGENT_MODEL=opus` before launching.

**VSCode extension vs integrated terminal:** The extension panel and the
integrated terminal (`Ctrl+\``) share the same engine but the extension
has limited TTY support. For agent-heavy work, prefer the integrated
terminal. Run `claude` directly to get full subagent support.

**Agent colors:**
| Agent | Color | Model |
|-------|-------|-------|
| planner-science | purple | Opus |
| planner | blue | Sonnet |
| executor | green | Sonnet |
| reviewer | orange | Sonnet |
| lookup | cyan | Haiku |

**Performance notes:**

**PostToolUse lint latency:** `lint-on-edit.sh` adds ~300–800 ms per `.py` write
due to Poetry venv startup. During executor sessions writing many files, this is
expected — not a hang.

**Write guard and relative paths:** `guard-write-path.sh` resolves relative paths
from CWD. All agents use absolute paths by default, so this is transparent.
