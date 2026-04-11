# Pre-Commit Hook Audit: What Should Be Automated

**Date:** 2026-04-11
**Author:** reviewer-adversarial (engineering audit mode)
**Commit frequency:** ~30 commits/day (agent-driven; 320 commits in 11 days)

---

## 1. Executive Summary

The repo has a single pre-commit hook (jupytext sync) and two Claude Code
PostToolUse hooks (lint-on-edit, guard-write-path). Agents are instructed to
run **five** checks manually on every code change: ruff, mypy, pytest,
mirror-drift, and diff-cover. Measured wall-clock times show ruff (~0.5s) and
mypy (~2.2s) are fast enough for pre-commit; pytest (~7.8s without coverage,
~22s with) and mirror-drift (~4s) are borderline; diff-cover requires a prior
pytest run and is too slow. At 30 commits/day, even a 3-second hook costs
~90 seconds of cumulative friction — acceptable only if the signal is high.
**Promote ruff-check and mypy as pre-commit hooks.** Keep pytest and
diff-cover agent-side. Fix the existing jupytext and mirror-drift issues
before promoting them.

---

## 2. Audit Findings — What Exists Today

### 2.1 Git pre-commit hooks (`.pre-commit-config.yaml`)

| Hook | Source | Status |
|------|--------|--------|
| jupytext `--sync` | mwouts/jupytext v1.19.1, scoped to `^sandbox/.*\.(ipynb\|py)$` | **Installed but currently BROKEN.** `pre-commit run --all-files` exits 4 because SC2 notebooks have unstaged paired files. The hook fires on every commit touching sandbox/, but its failure message ("git index is outdated") requires the agent to re-stage — no auto-fix. |

### 2.2 Claude Code hooks (`settings.json`)

| Hook | Trigger | What it does |
|------|---------|-------------|
| `lint-on-edit.sh` | PostToolUse on Write\|Edit | Runs `ruff check` on the single edited `.py` file. Output is informational only — does not block the edit. |
| `guard-write-path.sh` | PreToolUse on Write\|Edit | Blocks writes outside home dir, asks for writes inside home but outside repo. |
| `log-subagent.sh` | SubagentStart/SubagentStop | Logs agent lifecycle events. No validation function. |

### 2.3 Agent-mandated manual checks

These are documented across three sources: `python-code.md` (Pre-Commit
Checks section), `git-workflow.md` (PR Creation Flow), and per-agent
definitions (`executor.md`, `reviewer.md`, `reviewer-deep.md`).

| Check | Where documented | When run |
|-------|-----------------|----------|
| `ruff check src/ tests/` | python-code.md step 1, executor.md, reviewer.md step 2, git-workflow.md step 1a | After every code change + PR wrap-up |
| `mypy src/rts_predict/` | python-code.md step 2, reviewer.md step 3, git-workflow.md step 1b | After every code change + PR wrap-up |
| `pytest tests/ -v --cov` | python-code.md step 3, executor.md, reviewer.md step 1, git-workflow.md step 1c | After every code change + PR wrap-up |
| `check_mirror_drift.py` | reviewer.md step 7, reviewer-deep.md step 9 | Reviewer pass only |
| `diff-cover coverage.xml` | reviewer.md step 8, reviewer-deep.md step 10 | Reviewer pass only |
| jupytext pair sync check | executor.md step 6, reviewer.md notebook step 2, reviewer-deep.md notebook step 1 | After notebook changes |

### 2.4 Existing problems discovered during audit

1. **Ruff is failing on archive files.** 9 E501 errors in
   `src/rts_predict/sc2/reports/sc2egset/archive/` — these are jupytext-paired
   .py files from old notebook runs. They live inside `src/rts_predict/` so
   ruff scans them. Adding a ruff pre-commit hook without excluding this path
   will block every commit.

2. **Mirror drift is failing.** The same two archive `.py` files are detected
   as source files missing tests. The `exempt_sources` list in
   `pyproject.toml` does not include them.

3. **Ruff format is not enforced.** 38/63 files would be reformatted by
   `ruff format`. No agent is instructed to run it. This is unrelated to
   pre-commit but worth noting.

---

## 3. Candidate Analysis

Measured on Apple M4 Max, Poetry 1.x, Python 3.12, 455 tests.

| Check | Wall time | Scopeable to staged? | Signal quality | Agent skip risk | FP risk | Verdict |
|-------|-----------|---------------------|---------------|----------------|---------|---------|
| **ruff check** (lint) | 0.5s (full repo) | YES — pass file list | HIGH: catches syntax errors, import ordering, undefined names. F and E rules are real bugs. | MEDIUM: lint-on-edit catches single files, but agents forget to lint tests/ after editing src/. | LOW if archive excluded | **YES** |
| **ruff format** (formatter) | 0.5s (full repo) | YES — pass file list | MEDIUM: style consistency. 38 files currently non-conformant. | HIGH: no agent instruction exists. | HIGH initially (38 dirty files) | **NO — adopt separately first** |
| **mypy** | 2.2s (full repo) | PARTIAL — mypy needs full project context for import resolution; file-scoped mypy misses cross-module issues | MEDIUM-HIGH: catches type errors in function signatures, None-handling | LOW: agents do run it, but only at PR time, not after every commit | LOW (currently 0 errors) | **YES** |
| **pytest** (no coverage) | 7.8s | NO — scoping by changed file is unreliable (test A may break because module B changed) | HIGH: catches real regressions | LOW: agents run it consistently | LOW | **NO** |
| **pytest + coverage** | 22.4s | NO | HIGH but redundant with no-coverage run for regression catching | N/A (same as above) | N/A | **NO** |
| **mirror drift** | 4.1s | NO — needs full tree scan | MEDIUM: catches orphaned tests and missing test files | MEDIUM: only reviewers run it | **HIGH right now** (2 false positives from archive) | **MAYBE — after fixing FPs** |
| **jupytext sync** (existing) | 1.3s per file, ~3s for all | YES — scoped to `^sandbox/` | HIGH: prevents paired-file desync | LOW for executor (runs jupytext explicitly), HIGH for other agents | MEDIUM (requires both files staged — tricky for agents) | **KEEP — already installed** |
| **diff-cover** | ~25s (needs pytest + coverage first) | NO | MEDIUM: confirms new code is tested | LOW: only reviewer runs it | LOW | **NO** |
| **notebook cell-size check** | <1s if scripted | YES — scope to staged `.py` in sandbox/ | LOW: convention, not correctness | HIGH: no automated check exists, reviewer does AST walk manually | LOW | **MAYBE — write script first** |
| **notebook inline-def check** | <1s if scripted | YES — scope to staged `.py` in sandbox/ | HIGH: inline defs in notebooks violate the sandbox contract | HIGH: same — manual AST walk only | LOW | **MAYBE — write script first** |

---

## 4. Recommended Pre-Commit Config

Replace the current `.pre-commit-config.yaml` with:

```yaml
# .pre-commit-config.yaml
# Hooks fire on every `git commit`. Agents no longer need to run these manually.
# Wall time budget: <5s total for non-notebook commits, <8s for notebook commits.

repos:
  # ── Ruff lint (staged .py files only) ──────────────────────────────────

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.10  # Match pyproject.toml: ruff = "^0.9.0"
    hooks:
      - id: ruff
        args: [--no-fix]
        # Exclude archive .py files that are jupytext outputs from old notebooks.
        # These live in src/ but are not maintained code.
        exclude: ^src/rts_predict/.*/reports/.*/archive/

  # ── Mypy type check (full src/ — needs project context) ───────────────
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.14.0  # Match pyproject.toml: mypy = "^1.14.0"
    hooks:
      - id: mypy
        args: [--config-file=pyproject.toml]
        # Mypy needs the project's dependencies to resolve imports.
        # additional_dependencies must mirror the runtime deps, or use
        # pass_filenames: false with entry pointing to the venv mypy.
        # OPTION A (simpler, recommended): use local hook instead.
        pass_filenames: false
        entry: poetry run mypy src/rts_predict/
        language: system

  # ── Jupytext sync (notebook pairs in sandbox/) ────────────────────────
  - repo: https://github.com/mwouts/jupytext
    rev: v1.19.1
    hooks:
      - id: jupytext
        args: [--sync]
        files: ^sandbox/.*\.(ipynb|py)$
```

**IMPORTANT implementation note on mypy:** The `mirrors-mypy` repo approach
requires listing every dependency in `additional_dependencies`, which is
fragile and duplicative. The recommended pattern is a **local system hook**
that calls the venv's mypy directly:

```yaml
  # OPTION B (preferred for this project — avoids dependency duplication):
  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: poetry run mypy src/rts_predict/
        language: system
        types: [python]
        # Only run when .py files are staged, but always check full src/
        pass_filenames: false
```

---

## 5. What Stays Agent-Side

| Check | Rationale |
|-------|-----------|
| **pytest** (with or without coverage) | 7.8–22s per commit is unacceptable at 30 commits/day. Pytest is not scopeable to staged files without fragile heuristics. Agents already run it reliably. Keep as executor post-change and reviewer gate. |
| **diff-cover** | Depends on pytest+coverage output. Only meaningful at PR review time, not per-commit. |
| **mirror-drift** | Currently broken (2 FPs). Fix the `exempt_sources` list first, then reconsider. Even when fixed, 4s is borderline for a check that catches errors only when new modules are added (rare vs. ~30 commits/day). Better as a reviewer gate. |
| **ruff format** | 38 files currently non-conformant. Adopting it as a hook now would block every commit until bulk-formatted. Adopt as a separate chore: (1) bulk-format, (2) commit, (3) then add hook. |
| **Notebook cell-size / inline-def checks** | No automated script exists yet. Writing one is a prerequisite. Once written, these are excellent pre-commit candidates (~instant, high signal). Track as future work. |
| **Fresh-kernel notebook execution** | 600s timeout. Obviously not a pre-commit candidate. Stays in executor workflow. |

---

## 6. Implementation Notes

### 6.1 Ruff hook

- **Must exclude** `^src/rts_predict/.*/reports/.*/archive/` to avoid
  blocking on legacy notebook-paired .py files. Alternatively, fix those
  9 E501 errors in a prep commit.
- The `ruff-pre-commit` repo runs ruff in its own environment, decoupled
  from the project venv. This is fine because ruff is a standalone binary
  with no Python import needs.
- The `--no-fix` flag is intentional: auto-fix in pre-commit modifies
  staged files after staging, which produces confusing diffs for agents
  that expect their staged content to be committed as-is.
- `args: [--no-fix]` means the hook blocks but does not modify. The agent
  must fix and re-stage.

### 6.2 Mypy hook

- **Must use `language: system`** with `poetry run mypy`. Mypy needs the
  full project dependency graph to resolve imports (`duckdb`, `pandas`,
  `pyarrow`, etc.). The mirrors-mypy approach would require mirroring all
  34 dependencies in `additional_dependencies` — fragile.
- `pass_filenames: false` is required because mypy `--incremental` works
  best on the full `src/rts_predict/` tree. Passing individual files loses
  cross-module type checking.
- The 2.2s runtime is acceptable but will grow as the codebase grows. If
  it exceeds 5s, switch to `dmypy` (daemon mode) or scope to changed
  packages only.
- `ignore_missing_imports = true` is already set in pyproject.toml,
  which prevents mypy from failing on uninstalled stubs.

### 6.3 Jupytext hook (existing — fix needed)

- The hook is currently failing because the SC2 notebook pair has unstaged
  changes. This is a one-time fix: stage both files or run `jupytext --sync`
  and commit.
- The hook's failure mode ("git index is outdated") is confusing for agents.
  The agent must understand that both `.py` and `.ipynb` must be staged
  together. Document this in `sandbox/README.md` (already partially done
  at rule 4: "Always stage both .ipynb and .py of a pair").
- The hook fires once per matching file, so it processes each .py and each
  .ipynb — doubling work. With 3 notebook pairs this is ~3s, acceptable.
  At 20+ pairs, consider adding `require_serial: true` to avoid duplicate
  processing.

### 6.4 Agent documentation updates needed

After installing the hooks, update these files to remove redundant manual
instructions:

1. **`.claude/rules/python-code.md`** — remove "Pre-Commit Checks
   (MANDATORY)" section or change to "Verified automatically by
   pre-commit hooks."
2. **`.claude/agents/executor.md`** — change "After every code change,
   run ruff check..." to "ruff and mypy run automatically on commit.
   After every code change, run the relevant pytest subset."
3. **`.claude/rules/git-workflow.md`** — steps 1a (ruff) and 1b (mypy)
   in PR Creation Flow can note "enforced by pre-commit hook; manual
   run not required."
4. **`CLAUDE.md` Commands table** — add note that ruff and mypy are
   also enforced via pre-commit hooks.

### 6.5 Pre-requisite cleanup (do before installing hooks)

1. Fix ruff errors in archive files: either exclude the path from ruff in
   `pyproject.toml` (`[tool.ruff] extend-exclude = ["src/rts_predict/*/reports/*/archive/"]`)
   or fix the 9 E501 violations.
2. Fix mirror-drift false positives: add the two archive `.py` files to
   `[tool.mirror_drift] exempt_sources` in `pyproject.toml`.
3. Fix jupytext desync: run `jupytext --sync` on the SC2 notebook pair
   and commit both files.
4. Run `pre-commit install` to ensure the hooks are active (currently
   installed based on `.git/hooks/pre-commit` content).

### 6.6 Risk: hook disablement

Agents that encounter a failing pre-commit hook may be tempted to use
`--no-verify`. The `settings.json` deny list does not currently block
`git commit --no-verify`. Consider adding `Bash(git commit*--no-verify*)`
to the deny list, or adding a note to agent definitions that `--no-verify`
is prohibited.

### 6.7 Estimated time budget

| Commit type | Hooks that fire | Estimated wall time |
|-------------|-----------------|---------------------|
| Python-only (src/ or tests/) | ruff + mypy | ~2.7s |
| Notebook + Python | ruff + mypy + jupytext | ~5.5s |
| Docs/config only (no .py) | none | 0s |
| Mixed | ruff + mypy + jupytext | ~5.5s |

All within the 5–8s budget. Acceptable for the current commit frequency.
