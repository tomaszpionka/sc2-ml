# Category C Plan: Sandbox and Artifacts Guidance Hardening

**Branch:** `chore/sandbox-and-artifacts-guidance`
**Date:** 2026-04-08
**Category:** C — Chore
**Scope:** Documentation-only changes to 8 files. No code, no tests.

---

## Problem statement

Two structural invariants are not documented consistently across all guidance
files that a future Claude session or human would consult:

1. **All phase work code execution must happen in `sandbox/`** — specifically
   as a `.py` (jupytext percent format) + `.ipynb` pair at
   `sandbox/<game>/<dataset>/XX_XX_<name>.{py,ipynb}`.

2. **Artifacts produced by those notebooks must be saved to
   `src/rts_predict/<game>/reports/<dataset>/artifacts/`** — not into the
   dataset report root directly.

The canonical example is `sandbox/sc2/sc2egset/01_08_game_settings_audit.py`
and its `.ipynb` pair. These conventions were established in PR #58
(`chore/notebook-sandbox`) but the guidance was only added to agent files
(`executor.md`, `reviewer.md`) and `sandbox/README.md`. Several upstream
documents that Claude sessions read first were not updated.

---

## Audit results

| File | sandbox/ guidance | jupytext pair | artifacts/ subdir | Action needed |
|------|-------------------|---------------|-------------------|---------------|
| CLAUDE.md | MISSING | MISSING | MISSING | Add section |
| ARCHITECTURE.md | MISSING from layout | N/A | Row exists, correct | Add sandbox/ to layout |
| sandbox/README.md | Present | Present | WRONG (says root, not artifacts/) | Fix path |
| .claude/agents/executor.md | Present | Present | MISSING | Add to notebook workflow |
| .claude/agents/reviewer.md | Present | Present | MISSING | Add check |
| .claude/agents/reviewier-deep.md | Present | Present | MISSING | Add check |
| .claude/agents/planner-science.md | MISSING | N/A | N/A | Add guidance |
| docs/agents/AGENT_MANUAL.md | MISSING from Workflow A | N/A | N/A | Add to workflow |
| .claude/dev-constraints.md | MISSING | N/A | N/A | Add section |

Files where no change is needed:
- `.claude/scientific-invariants.md` — methodology, not workflow
- `docs/INDEX.md` — documentation index only
- `.claude/rules/git-workflow.md` — commit/PR workflow only
- `.claude/rules/python-code.md` — Python style only
- `.claude/rules/sql-data.md` — SQL conventions only
- `.claude/agents/planner.md` — code chores, not phase work
- `.claude/agents/lookup.md` — quick lookups only
- `.claude/agents/writer-thesis.md` — thesis writing only

---

## Steps

### Step 1 — CLAUDE.md: Add sandbox and artifacts guidance

Add a new section after "## Key File Locations" and before "## Agent Architecture".

**BEFORE** (lines 73-76):
```markdown
| Per-dataset invariants | `src/rts_predict/<game>/reports/<dataset>/INVARIANTS.md` |

## Agent Architecture
```

**AFTER:**
```markdown
| Per-dataset invariants | `src/rts_predict/<game>/reports/<dataset>/INVARIANTS.md` |

## Phase Work Execution (Sandbox Notebooks)

All Category A (phase work) code execution happens in Jupyter notebooks under
`sandbox/<game>/<dataset>/`. Each notebook is a jupytext-paired `.py` (percent
format) + `.ipynb` file. The `.py` file is the diff-reviewable source of truth;
the `.ipynb` file carries cell outputs for audit.

**Naming:** `{PHASE:02d}_{STEP}_{descriptive_name}.{py,ipynb}`
**Example:** `sandbox/sc2/sc2egset/01_08_game_settings_audit.py`

**Artifacts:** Notebooks save report artifacts (CSV, MD, PNG) to
`src/rts_predict/<game>/reports/<dataset>/artifacts/` — never to the dataset
report root directly. Use `get_reports_dir("sc2", "sc2egset") / "artifacts"`
from `rts_predict.common.notebook_utils`.

**Hard rules:** See `sandbox/README.md` for the full contract (no inline
definitions, 50-line cell cap, read-only DuckDB, both files committed).

## Agent Architecture
```

**Verification:**
```bash
grep -c 'sandbox/' CLAUDE.md  # expect >= 3
grep -c 'artifacts/' CLAUDE.md  # expect >= 2
grep 'jupytext' CLAUDE.md  # expect match
```

---

### Step 2 — ARCHITECTURE.md: Add sandbox/ to top-level layout

Add `sandbox/` to the package layout tree at the top of the file.

**BEFORE** (lines 8-14):
```markdown
## Package layout

```
src/rts_predict/
├── __init__.py          # Docstring only — no __version__
├── sc2/                 # StarCraft II — complete game package
├── aoe2/                # Age of Empires II — placeholder, mirrors sc2/ when populated
└── common/              # Shared evaluation code — see common/CONTRACT.md
```
```

**AFTER:**
```markdown
## Package layout

```
rts-outcome-prediction/
├── src/rts_predict/
│   ├── __init__.py          # Docstring only — no __version__
│   ├── sc2/                 # StarCraft II — complete game package
│   ├── aoe2/                # Age of Empires II — placeholder, mirrors sc2/ when populated
│   └── common/              # Shared evaluation code — see common/CONTRACT.md
├── sandbox/                 # Jupyter notebook exploration — see sandbox/README.md
│   ├── sc2/sc2egset/        # SC2EGSet notebooks (Phases 0–2)
│   └── aoe2/                # AoE2 placeholders
├── tests/                   # Mirrored test tree — see .claude/rules/python-code.md
├── thesis/                  # Thesis chapters and figures
├── reports/                 # Cross-cutting research log and archives
└── docs/                    # Methodology manuals and agent documentation
```
```

Also add a row to the "Cross-cutting files" table (around line 62):

**Add row after the last row of the table:**
```markdown
| Sandbox notebooks | `sandbox/<game>/<dataset>/` | Phase work execution (jupytext `.py` + `.ipynb` pairs) |
```

**Verification:**
```bash
grep -c 'sandbox/' ARCHITECTURE.md  # expect >= 3
```

---

### Step 3 — sandbox/README.md: Fix artifacts path

**BEFORE** (lines 57-61):
```markdown
## Report artifacts

Notebooks write report artifacts (CSV, MD, PNG) to
`src/rts_predict/<game>/reports/<dataset>/`. Notebooks themselves are not
cited as findings sources — only the report artifacts are.
```

**AFTER:**
```markdown
## Report artifacts

Notebooks write report artifacts (CSV, MD, PNG) to
`src/rts_predict/<game>/reports/<dataset>/artifacts/` — always the `artifacts/`
subdirectory, never the dataset report root directly. Use
`get_reports_dir("sc2", "sc2egset") / "artifacts"` from
`rts_predict.common.notebook_utils`. Notebooks themselves are not cited as
findings sources — only the report artifacts are.
```

**Verification:**
```bash
grep 'artifacts/' sandbox/README.md  # expect match containing "artifacts/"
grep -c 'never.*root\|never.*directly' sandbox/README.md  # expect >= 1
```

---

### Step 4 — .claude/agents/executor.md: Add artifacts path rule

Add a new item to the "Notebook workflow (sandbox/)" numbered list, after
item 1 (template) and before item 2 (functions in src/).

**BEFORE** (lines 60-62):
```markdown
1. Use the template from `_current_plan.md` B.3.
2. All functions and classes must live in `src/rts_predict/` and be imported.
```

**AFTER:**
```markdown
1. Use the template from `_current_plan.md` B.3.
2. Save all report artifacts to `get_reports_dir(game, dataset) / "artifacts"` —
   never to the dataset report root directly. The `artifacts/` subdirectory is
   the only valid target for machine-generated outputs (CSV, MD, PNG).
3. All functions and classes must live in `src/rts_predict/` and be imported.
```

(Renumber subsequent items: old 2 becomes 3, old 3 becomes 4, etc. through old 8 becoming 9.)

**Verification:**
```bash
grep 'artifacts/' .claude/agents/executor.md  # expect match
```

---

### Step 5 — .claude/agents/reviewer.md: Add artifacts path check

Add a new item to the "For notebook changes (sandbox/)" numbered list, after
item 7 (report artifact consistency).

**BEFORE** (line 59):
```markdown
7. **Report artifact consistency:** If the notebook front-matter lists artifacts,
   verify those files are present in the changeset.
```

**AFTER:**
```markdown
7. **Report artifact consistency:** If the notebook front-matter lists artifacts,
   verify those files are present in the changeset.
8. **Artifact path check:** All report artifacts must be written to
   `reports/<dataset>/artifacts/`, never to the dataset report root. Flag
   any artifact path missing the `artifacts/` subdirectory.
```

**Verification:**
```bash
grep 'Artifact path check' .claude/agents/reviewer.md  # expect match
```

---

### Step 6 — .claude/agents/reviewier-deep.md: Add artifacts path check

Add a new item to "Mandatory checks -- sandbox notebooks" after item 13
(sub-step coverage).

**BEFORE** (lines 175-176):
```markdown
13. **Sub-step coverage.** When porting an audit with labeled sub-steps
    (A, B, C, ...), verify every sub-step in the source is present in
    the notebook. Missing sub-steps without explanation are a porting
    bug.
14. **Research log entry.** If expected, verify it follows
```

**AFTER:**
```markdown
13. **Sub-step coverage.** When porting an audit with labeled sub-steps
    (A, B, C, ...), verify every sub-step in the source is present in
    the notebook. Missing sub-steps without explanation are a porting
    bug.
14. **Artifact output path.** All report artifacts must be written to
    `reports/<dataset>/artifacts/`, never to the dataset report root.
    Verify every `to_csv()`, `savefig()`, or file-write call targets a
    path containing `/artifacts/`. Flag any write to the report root as
    a blocker.
15. **Research log entry.** If expected, verify it follows
```

**Verification:**
```bash
grep 'Artifact output path' .claude/agents/reviewier-deep.md  # expect match
```

---

### Step 7 — .claude/agents/planner-science.md: Add sandbox guidance

Add to the "Constraints" section, after the existing Category A plan
requirements bullet.

**BEFORE** (lines 42-44):
```markdown
- For Category A plans: phase/step ref, branch, files, function signatures,
  SQL queries, test cases, gate condition.
- For Category F plans: section paths, feeding artifacts, draft vs revision,
```

**AFTER:**
```markdown
- For Category A plans: phase/step ref, branch, files, function signatures,
  SQL queries, test cases, gate condition. The plan MUST specify the sandbox
  notebook path (`sandbox/<game>/<dataset>/XX_XX_<name>.py`) and confirm that
  artifacts target `reports/<dataset>/artifacts/`.
- For Category F plans: section paths, feeding artifacts, draft vs revision,
```

**Verification:**
```bash
grep 'sandbox/' .claude/agents/planner-science.md  # expect match
grep 'artifacts/' .claude/agents/planner-science.md  # expect match
```

---

### Step 8 — docs/agents/AGENT_MANUAL.md: Add sandbox to Workflow A

Update Workflow A (Phase Work) to mention the sandbox notebook.

**BEFORE** (lines 149-158):
```markdown
### Workflow A: Phase Work (most common)

```
Step 1:  @planner-science plan Phase N step N.X
Step 2:  [review plan in chat, request adjustments]
Step 3:  [approved plan → write to _current_plan.md]
Step 4:  @executor execute steps 1-3
         (use /model opus for hard analytical steps)
Step 5:  @reviewer review changes
Step 6:  [fix issues from reviewer]
Step 7:  [wrap up PR when reviewer approves]
```
```

**AFTER:**
```markdown
### Workflow A: Phase Work (most common)

Phase work executes in sandbox notebooks. The plan specifies the notebook path
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
```

**Verification:**
```bash
grep -c 'sandbox/' docs/agents/AGENT_MANUAL.md  # expect >= 3
grep 'artifacts/' docs/agents/AGENT_MANUAL.md  # expect match
```

---

### Step 9 — .claude/dev-constraints.md: Add sandbox execution rule

Add a new section after "## Data Layout" and before "## Platform".

**BEFORE** (lines 25-28):
```markdown
- `src/rts_predict/sc2/data/sc2egset/tmp/` — DuckDB spill-to-disk temp directory

## Platform
```

**AFTER:**
```markdown
- `src/rts_predict/sc2/data/sc2egset/tmp/` — DuckDB spill-to-disk temp directory

## Phase Work Execution

All Category A (phase work) code runs in sandbox notebooks, not in `src/`
modules or ad-hoc scripts. Path: `sandbox/<game>/<dataset>/XX_XX_<name>.{py,ipynb}`.
Artifacts are saved to `reports/<dataset>/artifacts/`, never to the report root.
See `sandbox/README.md` for the full contract.

## Platform
```

**Verification:**
```bash
grep 'sandbox/' .claude/dev-constraints.md  # expect match
grep 'artifacts/' .claude/dev-constraints.md  # expect match
```

---

## Files touched (summary)

| # | File | Change type |
|---|------|-------------|
| 1 | `CLAUDE.md` | Add section (~15 lines) |
| 2 | `ARCHITECTURE.md` | Expand layout tree, add table row |
| 3 | `sandbox/README.md` | Fix 4-line paragraph |
| 4 | `.claude/agents/executor.md` | Add 1 numbered item, renumber |
| 5 | `.claude/agents/reviewer.md` | Add 1 numbered item |
| 6 | `.claude/agents/reviewier-deep.md` | Add 1 numbered item, renumber |
| 7 | `.claude/agents/planner-science.md` | Extend 1 bullet (2 sentences) |
| 8 | `docs/agents/AGENT_MANUAL.md` | Add paragraph + modify code block |
| 9 | `.claude/dev-constraints.md` | Add section (~5 lines) |

No code changes. No test changes. No version bump needed (docs-only).

---

## Gate condition

All 9 grep checks pass. Combined verification script:

```bash
# Step 1 — CLAUDE.md
test "$(grep -c 'sandbox/' CLAUDE.md)" -ge 3 && echo "PASS 1a" || echo "FAIL 1a"
test "$(grep -c 'artifacts/' CLAUDE.md)" -ge 2 && echo "PASS 1b" || echo "FAIL 1b"
grep -q 'jupytext' CLAUDE.md && echo "PASS 1c" || echo "FAIL 1c"

# Step 2 — ARCHITECTURE.md
test "$(grep -c 'sandbox/' ARCHITECTURE.md)" -ge 3 && echo "PASS 2" || echo "FAIL 2"

# Step 3 — sandbox/README.md
grep -q 'reports/<dataset>/artifacts/' sandbox/README.md && echo "PASS 3a" || echo "FAIL 3a"
grep -qE 'never.*(root|directly)' sandbox/README.md && echo "PASS 3b" || echo "FAIL 3b"

# Step 4 — executor.md
grep -q 'artifacts/' .claude/agents/executor.md && echo "PASS 4" || echo "FAIL 4"

# Step 5 — reviewer.md
grep -q 'Artifact path check' .claude/agents/reviewer.md && echo "PASS 5" || echo "FAIL 5"

# Step 6 — reviewier-deep.md
grep -q 'Artifact output path' .claude/agents/reviewier-deep.md && echo "PASS 6" || echo "FAIL 6"

# Step 7 — planner-science.md
grep -q 'sandbox/' .claude/agents/planner-science.md && echo "PASS 7a" || echo "FAIL 7a"
grep -q 'artifacts/' .claude/agents/planner-science.md && echo "PASS 7b" || echo "FAIL 7b"

# Step 8 — AGENT_MANUAL.md
test "$(grep -c 'sandbox/' docs/agents/AGENT_MANUAL.md)" -ge 3 && echo "PASS 8a" || echo "FAIL 8a"
grep -q 'artifacts/' docs/agents/AGENT_MANUAL.md && echo "PASS 8b" || echo "FAIL 8b"

# Step 9 — dev-constraints.md
grep -q 'sandbox/' .claude/dev-constraints.md && echo "PASS 9a" || echo "FAIL 9a"
grep -q 'artifacts/' .claude/dev-constraints.md && echo "PASS 9b" || echo "FAIL 9b"
```

All 15 checks must output PASS. Any FAIL blocks the PR.
