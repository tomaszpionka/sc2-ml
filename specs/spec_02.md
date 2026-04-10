# Spec 02: Venv Activation Convention

**Category:** C — Chore
**Branch:** `chore/venv-activation-convention`
**Source:** `audit_plan.md` Changes B + F + §6 consistency ripple + memory E.1/E.2
**Depends on:** Nothing — can run in parallel with spec_01/spec_03

---

## Context

The project has two contradictory memories about whether to use
`source .venv/bin/activate &&` before poetry commands. The user has decided
to re-adopt venv activation for cross-machine reproducibility. This spec:
1. Updates CLAUDE.md Critical Rules and Commands table
2. Updates all agent definitions and rule files for consistency
3. Updates `settings.json` shared allow list
4. Updates the hook script that calls poetry
5. Reconciles the contradictory memory files

All changes are mechanical `poetry run` → `source .venv/bin/activate && poetry run`
replacements plus memory file edits. No logic changes.

---

## Step 1: Update CLAUDE.md Critical Rules — poetry line

**File:** `CLAUDE.md`

**Edit:**
```
old_string:
- **ALWAYS** use `poetry run <command>` — NEVER bare `python3` or `pip install`

new_string:
- **ALWAYS** activate the venv first: `source .venv/bin/activate && poetry run <command>` — NEVER bare `python3` or `pip install`
```

---

## Step 2: Update CLAUDE.md Commands table

**File:** `CLAUDE.md`

**Edit:**
```
old_string:
| Run tests | `poetry run pytest tests/ -v --cov=rts_predict --cov-report=term-missing` |
| Lint | `poetry run ruff check src/ tests/` |
| Type check | `poetry run mypy src/rts_predict/` |
| CLI | `poetry run sc2 --help` |

new_string:
| Run tests | `source .venv/bin/activate && poetry run pytest tests/ -v --cov=rts_predict --cov-report=term-missing` |
| Lint | `source .venv/bin/activate && poetry run ruff check src/ tests/` |
| Type check | `source .venv/bin/activate && poetry run mypy src/rts_predict/` |
| CLI | `source .venv/bin/activate && poetry run sc2 --help` |
```

---

## Step 3: Update `.claude/rules/python-code.md` lines 9-11

**File:** `.claude/rules/python-code.md`

**Edit:**
```
old_string:
1. `poetry run ruff check src/ tests/`
2. `poetry run mypy src/rts_predict/`
3. `poetry run pytest tests/ -v`

new_string:
1. `source .venv/bin/activate && poetry run ruff check src/ tests/`
2. `source .venv/bin/activate && poetry run mypy src/rts_predict/`
3. `source .venv/bin/activate && poetry run pytest tests/ -v`
```

---

## Step 4: Update `.claude/rules/git-workflow.md` lines 17-19

**File:** `.claude/rules/git-workflow.md`

The PR Creation Flow checks section. Edit:
```
old_string:
   a. `poetry run ruff check src/ tests/`
   b. `poetry run mypy src/rts_predict/`
   c. `poetry run pytest tests/ -v --cov --cov-report=term-missing | tee coverage.txt`

new_string:
   a. `source .venv/bin/activate && poetry run ruff check src/ tests/`
   b. `source .venv/bin/activate && poetry run mypy src/rts_predict/`
   c. `source .venv/bin/activate && poetry run pytest tests/ -v --cov --cov-report=term-missing | tee coverage.txt`
```

---

## Step 5: Update `.claude/agents/executor.md`

**File:** `.claude/agents/executor.md`

**5a — Line 33 (after-every-code-change instruction):**
```
old_string:
  `poetry run ruff check src/ tests/` and relevant pytest subset.

new_string:
  `source .venv/bin/activate && poetry run ruff check src/ tests/` and relevant pytest subset.
```

**5b — Line 36 (constraint):**
```
old_string:
- Use `poetry run` always. Never bare `python3` or `pip`.

new_string:
- Use `source .venv/bin/activate && poetry run` always. Never bare `python3` or `pip`.
```

**5c — Line 42 (diff-cover command):**
```
old_string:
  `poetry run pytest tests/ --cov=rts_predict --cov-report=xml && poetry run diff-cover coverage.xml`

new_string:
  `source .venv/bin/activate && poetry run pytest tests/ --cov=rts_predict --cov-report=xml && poetry run diff-cover coverage.xml`
```

**5d — Line 69 (nbconvert):**
```
old_string:
   `poetry run jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 {path}`

new_string:
   `source .venv/bin/activate && poetry run jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 {path}`
```

**5e — Line 70-71 (jupytext sync). Find the line starting with "Immediately after":**
```
old_string:
5. **Immediately after `nbconvert --inplace`**, run `poetry run jupytext --sync {path}`.

new_string:
5. **Immediately after `nbconvert --inplace`**, run `source .venv/bin/activate && poetry run jupytext --sync {path}`.
```

---

## Step 6: Update `.claude/agents/reviewer.md`

**File:** `.claude/agents/reviewer.md`

**6a — Lines 22-24 (verification commands):**
```
old_string:
1. `poetry run pytest tests/ -v --cov=rts_predict --cov-report=term-missing`
2. `poetry run ruff check src/ tests/`
3. `poetry run mypy src/rts_predict/`

new_string:
1. `source .venv/bin/activate && poetry run pytest tests/ -v --cov=rts_predict --cov-report=term-missing`
2. `source .venv/bin/activate && poetry run ruff check src/ tests/`
3. `source .venv/bin/activate && poetry run mypy src/rts_predict/`
```

**6b — Line 34 (mirror-drift check):**
```
old_string:
7. **Mirror-drift check:** `poetry run python scripts/check_mirror_drift.py`

new_string:
7. **Mirror-drift check:** `source .venv/bin/activate && poetry run python scripts/check_mirror_drift.py`
```

**6c — Line 37 (diff-cover):**
```
old_string:
   `poetry run pytest tests/ --cov=rts_predict --cov-report=xml && poetry run diff-cover coverage.xml --fail-under=90`

new_string:
   `source .venv/bin/activate && poetry run pytest tests/ --cov=rts_predict --cov-report=xml && poetry run diff-cover coverage.xml --fail-under=90`
```

---

## Step 7: Update `scripts/hooks/lint-on-edit.sh`

**File:** `scripts/hooks/lint-on-edit.sh`

**Edit line 9:**
```
old_string:
  poetry run ruff check "$FILE_PATH" --no-fix 2>&1 | tail -10 || true

new_string:
  source .venv/bin/activate && poetry run ruff check "$FILE_PATH" --no-fix 2>&1 | tail -10 || true
```

---

## Step 8: Update `settings.json` shared allow list

**File:** `.claude/settings.json`

Add one entry to the `permissions.allow` array. Place it after the existing
`Bash(mypy *)` line:

```
old_string:
      "Bash(mypy *)",

new_string:
      "Bash(mypy *)",
      "Bash(source .venv/bin/activate && poetry *)",
```

**Verify:** `jq '.permissions.allow[] | select(contains("source .venv"))' .claude/settings.json`
returns the new entry.

---

## Step 9: Memory reconciliation

**9a — Delete the stale memory:**

Delete file: `~/.claude/projects/-Users-tomaszpionka-Projects-rts-outcome-prediction/memory/feedback_no_source_activate.md`

Use Bash: `rm ~/.claude/projects/-Users-tomaszpionka-Projects-rts-outcome-prediction/memory/feedback_no_source_activate.md`

**9b — Rewrite the venv memory:**

**File:** `~/.claude/projects/-Users-tomaszpionka-Projects-rts-outcome-prediction/memory/feedback_poetry_venv.md`

Overwrite with:
```markdown
---
name: Activate venv before poetry commands
description: Always prefix poetry commands with 'source .venv/bin/activate &&' for reproducibility across machines
type: feedback
---

Always prefix poetry commands with `source .venv/bin/activate &&` in Bash:

```
source .venv/bin/activate && poetry run <command>
```

**Why:** Ensures deterministic Python resolution regardless of system Python
version. Bare `poetry run` can break on machines where system Python differs.
The `settings.local.json` and `settings.json` both whitelist this pattern.

**How to apply:** Every poetry command: `source .venv/bin/activate && poetry <cmd>`.
This is also reflected in CLAUDE.md Critical Rules.
```

**9c — Update MEMORY.md index:**

**File:** `~/.claude/projects/-Users-tomaszpionka-Projects-rts-outcome-prediction/memory/MEMORY.md`

```
old_string:
- [No source activate prefix](feedback_no_source_activate.md) — use bare `poetry run`, not `source .venv/bin/activate &&`, so Bash allow rules match

new_string:
- [Activate venv before poetry](feedback_poetry_venv.md) — always prefix with `source .venv/bin/activate &&` for cross-machine reproducibility
```

---

## Step 10: Run tests to confirm nothing breaks

```bash
source .venv/bin/activate && poetry run pytest tests/ -v --cov=rts_predict --cov-report=term-missing
source .venv/bin/activate && poetry run ruff check src/ tests/
source .venv/bin/activate && poetry run mypy src/rts_predict/
```

No application code changed — only config, agent definitions, and rule docs.

---

## Gate condition

- [ ] `grep "source .venv" CLAUDE.md` matches in Critical Rules AND Commands table
- [ ] `grep "source .venv" .claude/rules/python-code.md` matches 3 times
- [ ] `grep "source .venv" .claude/rules/git-workflow.md` matches 3 times
- [ ] `grep "source .venv" .claude/agents/executor.md` matches 5 times
- [ ] `grep "source .venv" .claude/agents/reviewer.md` matches 5 times
- [ ] `grep "source .venv" scripts/hooks/lint-on-edit.sh` matches 1 time
- [ ] `jq` confirms settings.json has the new allow entry
- [ ] Memory: `feedback_no_source_activate.md` deleted, `feedback_poetry_venv.md` updated, `MEMORY.md` updated
- [ ] All tests pass, lint clean, mypy clean
