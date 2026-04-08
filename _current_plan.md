# Plan: Notebook-Based Exploration Sandbox

**Category:** C (chore / infrastructure)
**Branch:** `chore/notebook-sandbox`
**Status:** Phase A complete, awaiting approval before Phase B

---

## Phase A — Synthesis and Challenge

### A.1 Hypothesis Validation

**Working hypothesis:** A Jupyter notebook sandbox where each exploration step
is an executable artifact (query + output + narrative + interpretation), paired
with jupytext `.py` files for clean diffs, with all non-trivial Python imported
from `src/rts_predict/`.

**Verdict: The hypothesis is sound and fits the evidence. I accept it with
three refinements.**

The evidence for the hypothesis is strong:

1. **The reproducibility problem is real and structural.** Discovery Section 4
   documents five concrete gaps. The most damaging is Gap 6: "No mechanism to
   capture intermediate executor observations." When an executor runs 10 ad-hoc
   queries to investigate an anomaly, the intermediate results and reasoning
   thread are lost. The research log captures only a post-hoc summary. Notebooks
   solve this structurally: every cell execution is captured in order, with its
   output, in the same file.

2. **The code-first pattern (Pattern A) works well; the ad-hoc pattern
   (Pattern B) does not.** Steps 1.1-1.7 and 1.9 are backed by Python
   functions in `exploration.py`, are CLI-runnable, tested, and produce
   artifacts that satisfy Invariant 6. Step 1.8, the sole Pattern B step,
   exists only as markdown with embedded SQL — not re-runnable, not testable
   (Discovery Section 3). Notebooks would eliminate Pattern B by making every
   exploration step an executable artifact, even the ad-hoc ones.

3. **Invariant 6 (query/code co-located with results) is naturally satisfied
   by notebooks.** A notebook cell containing SQL + its result output is
   precisely what the invariant demands. The current approach requires
   discipline to manually transcribe SQL into markdown reports; a notebook
   captures this automatically (Discovery Section 2).

4. **The jupytext pairing is justified by the absence of CI and pre-commit
   hooks.** The repo has no CI, no pre-commit hooks, and no `.ipynb` files
   today (Discovery Section 5). Jupytext `.py:percent` files provide clean
   diffs in PRs without requiring any CI infrastructure. The PostToolUse lint
   hook (`lint-on-edit.sh`) would fire on the `.py` pair files, providing
   automatic Ruff checking of notebook code — a net positive.

**Refinements to the hypothesis:**

**(R1) Notebooks complement Pattern A; they do not replace it.** Discovery
Section 7 (Conflict 3) identifies the risk that if future steps are notebooks
instead of `exploration.py` functions, the CLI orchestrator becomes incomplete.
The correct design is: notebooks are the exploration and documentation medium;
any reusable computation (SQL queries, data transformations) must be extracted
to `src/rts_predict/` modules and imported back into the notebook. The CLI
orchestrator remains the canonical execution path for fully-formed steps.
Notebooks are the workspace where steps are developed and documented before
(or instead of, for purely investigative work) being promoted to `src/`.

**(R2) The notebook is not a report artifact.** Discovery Section 7
(Conflict 1) raises the dual-artifact question. The answer: notebooks are
working documents. The authoritative report artifacts remain in
`reports/<dataset>/` as CSV, MD, PNG files, produced either by `src/` module
functions or by explicit notebook cells that write to that directory. The
notebook itself is committed for reproducibility and audit trail purposes, but
it is not the thing cited in the thesis. This preserves the existing `ROADMAP.md`
artifact expectations unchanged.

**(R3) The `research_log.md` survives as an index, not a replacement.**
Discovery Section 7 (Conflict 2) raises narrative duplication. The research log
becomes a concise index: for each step, a brief entry pointing at the notebook
as the full record. The 10-section template still applies but the "How
(reproducibility)" section can point at the notebook rather than inlining
all SQL. The template is not changed; its usage becomes lighter because the
notebook carries the detailed derivation.

---

### A.2 Top Risks

**Risk 1: Coverage erosion from notebook glue code.**
Discovery Section 7 (Conflict 4) identifies that the 95% coverage threshold
(`pyproject.toml` line 77) would be affected if notebooks contain non-trivial
Python. Jupytext `.py` files are not collected by pytest unless explicitly
included, and `nbval` is not in the toolchain.

*Mitigation:* Enforce the hard rule: notebooks contain only imports, calls to
`src/` functions, SQL strings, and light display logic (pandas `.head()`,
`plt.show()`). Any cell exceeding the line cap defined in `sandbox/notebook_config.toml`
(`[cells] max_lines`) is a signal that logic should be extracted to a
`src/rts_predict/` module. Combined with the no-inline-definitions rule,
this forces all non-trivial Python out of notebooks by construction. The
reviewer agent enforces this mechanically.
The `.py` pair files are excluded from coverage collection via `pyproject.toml`
`[tool.coverage.run] omit` patterns. Coverage measures `src/rts_predict/` only,
which is already the case.

**Risk 2: DuckDB connection conflicts between notebook and CLI.**
Discovery Section 8 (Question 4) raises this. DuckDB uses a single-writer lock
in read-write mode. A notebook holding a read-write connection blocks all CLI
usage.

*Mitigation:* Notebooks open DuckDB in **read-only mode** by default. The
existing `DuckDBClient` context manager supports `read_only=True`. If a
notebook needs write access (rare — only for creating temporary views or
tables), it must explicitly request it and release the connection before any
CLI invocation. A helper function in `common/notebook_utils.py` wraps the
connection with appropriate defaults. This also prevents notebooks from
accidentally modifying the database.

**Risk 3: Jupytext sync drift — `.ipynb` and `.py` pair diverge.**
Without pre-commit hooks or CI, there is no automated enforcement that the
`.py` file is synced with the `.ipynb` when committing. An executor could
edit the notebook, commit only the `.ipynb`, and leave the `.py` stale.

*Mitigation:* The reviewer agent is updated to check that for every modified
`.ipynb` under `sandbox/`, a corresponding modified `.py` file exists in the
same commit. This is a mechanical check (file-list comparison). Additionally,
the jupytext config uses the `notebook_metadata_filter` to strip volatile
metadata (execution counts, widget state) from the `.ipynb`, reducing spurious
diffs and making sync easier to verify visually. A pre-commit hook using jupytext's official `--sync` mode is added in `B.2`
and `B.9` to mechanically regenerate the `.py` pair on every commit that
touches an `.ipynb` (and vice versa). The reviewer check remains as defense
in depth in case the hook is bypassed (`--no-verify`).

**Risk 4: Notebooks enable epistemic-ordering violations.**
The spec's hard constraint says the sandbox must not enable workflows where
feature engineering runs ahead of profiling. Notebooks are free-form by nature;
nothing stops someone from importing `processing.py` and running feature
engineering in a Phase 1 notebook.

*Mitigation:* The notebook template contract (Phase B, Section B.3) requires a
header cell with `phase_id` and `step_id`. The reviewer agent validates that
imports in a Phase 1 notebook do not reference Phase 7+ modules (feature
engineering) or Phase 9+ modules (models). This is a filename-pattern check on
the import lines. Additionally, the `processing.py` module's
`create_temporal_split()` function is already flagged as superseded in
`CLAUDE.md`; the reviewer should warn if any notebook imports from
`processing.py`.

**Risk 5: Notebook execution time may be unpredictable.**
Some exploration queries (e.g., scanning 62M tracker rows or 609M game event
rows) take minutes. A fresh-kernel reproducibility check that re-runs all
cells could hit timeouts.

*Mitigation:* The reproducibility enforcement (Phase B, Section B.5) uses a
configurable timeout per notebook. Heavy notebooks can set a higher timeout in
their front-matter. The default timeout is generous (10 minutes). Notebooks
that query very large tables should use `USING SAMPLE N ROWS` (already
established practice in Step 1.9) to keep execution times bounded. The
reviewer checks that notebooks complete within their declared timeout but does
not require sub-second execution.

---

### A.3 Key Design Decisions

#### Directory location: `sandbox/` at repo root

**Decision:** Create `sandbox/sc2/sc2egset/` and (later) `sandbox/aoe2/<dataset>/`
at the repo root.

**Justification:** Discovery Section 8 (Question 6) notes that `ARCHITECTURE.md`
defines five standard subdirectories for game packages (`data/`, `reports/`,
`models/`, `logs/`, `tests/`) with no slot for `notebooks/`. Placing notebooks
inside `src/rts_predict/sc2/` would violate the package contract — notebooks
are not source code, not data, and not reports. Placing them inside `reports/`
conflicts with the artifact naming convention (Discovery Section 1: reports
follow `{PHASE:02d}_{STEP:02d}_{name}.{ext}`). A top-level `sandbox/`
directory:

- Mirrors the `reports/` cross-cutting pattern (repo-root, game-scoped within).
- Does not modify the `ARCHITECTURE.md` game package contract.
- Makes the sandbox/production boundary unambiguous: `src/` is production code,
  `sandbox/` is working documents.
- Supports game-scoped isolation without nesting inside game packages.

The directory tree:
```
sandbox/
  sc2/
    sc2egset/       # Notebooks for SC2EGSet dataset, Phases 0-2
  aoe2/
    aoe2companion/  # (future) Notebooks for aoe2companion dataset
    aoestats/       # (future) Notebooks for aoestats dataset
```

#### Git policy: commit both `.ipynb` and `.py` pair

**Decision:** Commit both files. The `.py` is the diff-review artifact; the
`.ipynb` is the executable-with-outputs artifact.

**Justification:** The user has indicated a preference for keeping notebooks
locally until stable. However, the purpose of this sandbox is reproducibility
(Discovery Section 4, all six gaps). A notebook that is not committed is not
reproducible by anyone other than its creator. The `.ipynb` must be committed
because it contains cell outputs (query results, plots) that constitute the
exploration record. The `.py` file must be committed because it is what
reviewers diff. Uncommitted notebooks would recreate exactly the Gap 6 problem
(ephemeral exploration with no persistent record) that motivated this work.

**Compromise with the user's preference:** Notebooks may live on feature
branches uncommitted during active development. They must be committed before
the PR is merged. This matches the existing workflow where `exploration.py`
changes are developed on a branch and committed at PR time.

#### Relationship to `reports/`: independent artifacts, different audiences

**Decision:** Notebooks and reports are independent artifacts. Notebooks are
the exploration workspace (audience: the researcher, thesis methodology
narrative). Reports are the distilled findings (audience: the thesis results
chapters, ROADMAP gate checks).

**Justification:** Discovery Section 7 (Conflict 1) identifies the dual-artifact
risk. The resolution: a notebook is the *derivation* of a finding, not the
finding itself. The report artifact (CSV, MD, PNG) in `reports/<dataset>/` is
what the ROADMAP expects and what the thesis cites. Notebooks link to the
reports they produce (via front-matter); reports do not link back to notebooks
(they are self-contained per Invariant 6 because the SQL is embedded in both
places — the notebook cell and the report file).

For Phase 1 steps that already have Pattern A functions, the notebook calls
the function and captures the output with narrative. For new steps or ad-hoc
investigation, the notebook contains the SQL/code directly; if the finding
warrants a report artifact, a cell writes it to `reports/`.

#### Relationship to `research_log.md`: survives as lightweight index

**Decision:** `research_log.md` survives. Each entry becomes shorter: the
"How (reproducibility)" section points at the notebook path instead of inlining
all SQL. All other template sections remain.

**Justification:** Discovery Section 7 (Conflict 2). The research log serves
a different purpose from notebooks: it is a *chronological narrative* across
all games and all phases, providing the macro view. Notebooks are per-step
deep dives. The log answers "what happened this week across the project";
the notebook answers "how exactly was Step 1.8 investigated." Replacing the
log with notebooks would lose the cross-game chronological narrative. Reducing
the log to an index preserves its purpose while eliminating the duplication
that made it hard to maintain.

The `RESEARCH_LOG_TEMPLATE.md` is not changed. The "How (reproducibility)"
section's content shifts from inline SQL to a notebook path reference, but the
section heading and purpose remain.

#### Numbering and naming convention

**Decision:** Mirror the existing report naming pattern:
`{PHASE:02d}_{STEP}_{descriptive_name}.ipynb`

Examples:
- `01_01_corpus_summary.ipynb` (Phase 1, Step 1.1)
- `01_08_game_settings_audit.ipynb` (Phase 1, Step 1.8 — the restart candidate)
- `01_10_next_step.ipynb` (Phase 1, Step 1.10)

**Justification:** Discovery Section 1 documents the existing report naming
pattern as `{PHASE:02d}_{STEP:02d}_{descriptive_name}.{ext}`. Using the same
scheme for notebooks makes the correspondence between a notebook and its report
artifacts visually obvious. The step component uses the ROADMAP step ID (e.g.,
`1.8` becomes `08`, `1.9D` becomes `09D`), matching the report convention.

For investigative notebooks that do not correspond to a specific ROADMAP step
(ad-hoc exploration), use `{PHASE:02d}_XX_{descriptive_name}.ipynb` where `XX`
is an incrementing number starting from 90 (to sort after ROADMAP steps).

---

### A.4 Open Questions Resolved

**Q1 (Scope boundary): Should notebooks cover only ad-hoc exploration or also
structured Phase steps?**

*Resolution:* Both. Notebooks are the primary exploration medium for all future
Phase work. For structured steps (Pattern A), the notebook calls the `src/`
function and documents the interpretation. For ad-hoc investigation (Pattern B),
the notebook contains the queries directly. The distinction between Pattern A
and Pattern B dissolves: all work happens in notebooks, but reusable code is
always extracted to `src/`. (See Refinement R1 in A.1.)

**Q2 (Artifact authority): Which artifact is authoritative for thesis citation?**

*Resolution:* The report artifact in `reports/<dataset>/` remains authoritative.
Notebooks are not cited in the thesis as findings sources. They may be
referenced as methodology documentation ("the exploration was conducted in
notebook X, which is committed at path Y"). This preserves the existing
ROADMAP artifact expectations and satisfies Invariant 6 because report
artifacts continue to embed their derivation SQL. (See Refinement R2 in A.1.)

**Q3 (AoE2 parity): Does the notebook workflow apply to AoE2?**

*Resolution:* Yes, but not immediately. The `common/CONTRACT.md` rule ("build
once, build twice, then extract") applies. The sandbox directory structure
includes AoE2 placeholders (`sandbox/aoe2/aoe2companion/`, `sandbox/aoe2/aoestats/`),
but no AoE2 notebooks are created until AoE2 Phase 1 begins. The notebook
template, helper utilities, and reviewer checks are designed game-agnostically
from the start because they carry zero game-domain content (they are
infrastructure, like `DuckDBClient`). This is consistent with the
`CONTRACT.md` exemption for game-agnostic infrastructure.

**Q4 (DuckDB connection management): How do notebooks manage connections?**

*Resolution:* A helper function in `common/notebook_utils.py` returns a
read-only `DuckDBClient` connection scoped to the notebook's dataset. The
helper reads the dataset config to get the DB path and applies sensible pragmas
(memory limit, threads). Read-only mode avoids the single-writer lock issue.
For the rare case where write access is needed, the helper accepts an explicit
`read_only=False` flag and the notebook must close the connection in a
finally-block. (See Risk 2 in A.2.)

**Q5 (Git diff strategy): Which mechanism enforces jupytext sync?**

*Resolution:* A pre-commit hook (jupytext `--sync` mode, see B.2.5) is the primary mechanical guardrail. The reviewer agent performs a defense-in-depth check at PR review time in case the hook is bypassed with `--no-verify`. (See Risk 3 in A.2.)

**Q6 (Directory tree location): Where in the tree?**

*Resolution:* `sandbox/` at repo root. (See A.3 above.)

**Q7 (Coverage implications): What is notebook glue vs. analytical logic?**

*Resolution:* Orchestration only — imports, function calls, SQL strings, and display logic. Any cell approaching `[cells] max_lines` from `sandbox/notebook_config.toml` is a signal to extract logic to `src/rts_predict/`. No function, class, or lambda-assigned-to-name definitions in any cell (see B.3 Cell complexity rules). The `.py` pair files are excluded from coverage via `pyproject.toml` `omit`
patterns. (See Risk 1 in A.2.)

**Q8 (Reviewer agent integration): How does the reviewer handle notebooks?**

*Resolution:* The reviewer is updated with three new checks:
(a) Jupytext sync check — modified `.ipynb` must have a modified `.py` pair.
(b) No inline definitions — flag `ast.FunctionDef`, `ast.AsyncFunctionDef`, `ast.ClassDef` in any code cell (AST-based, no imports-cell exception).
(c) Phase boundary check — notebook imports must not reference modules from
    later phases than the notebook's declared `phase_id`.
The reviewer does not run `nbval` or execute notebooks. Notebook execution is
a manual or semi-automated reproducibility check, not a reviewer gate.

---

### A.5 Research Log and Prior Artifact Handling

#### Scope of restart: Phase 1 only. Phase 0 does not need restarting.

**Evidence:**

SC2 Phase 0 is fully reproducible under Pattern A. Every step (0.1-0.9) is
backed by a function in `audit.py` (665 lines, 5 `run_*` functions), orchestrated
by `run_phase_0_audit`, and re-runnable via the CLI. The Phase 0 research log
entries (lines 1200-1376 of `research_log.md`) embed literal SQL with results.
The Phase 0 gate (5 conditions, all documented at lines 1356-1368) was met on
2026-04-03. There are no Pattern B gaps in Phase 0 — it was built entirely
as executable code.

AoE2 Phase 0 for both datasets is also backed by functions in `audit.py`
(aoe2companion: 1,499+ lines, aoestats: 1,053+ lines). Both have `run_phase_0_audit`
orchestrators. The research log entries (lines 280-398) are compressed (both
datasets done in a single session) but the *code* is re-runnable. The
compression of the log narrative is a documentation gap, not a reproducibility
gap — the functions can be re-executed to regenerate all artifacts.

The non-reproducible work is:
- SC2 Phase 1 Step 1.8 (Pattern B, no function, not re-runnable — Discovery
  Section 4, Gap 1).
- The *narrative interpretation* in some Phase 1 entries (thin reasoning chains —
  Discovery Section 4, Gap 3, specifically Step 1.2 at lines 546-551).
- The pre-restart legacy entries (lines 1379-1502) which document the
  methodology restart itself, prior feature engineering, and prior pipeline
  work. These are historical records, not Phase 0/1 findings.

**Conclusion:** The restart covers SC2 Phase 1 only. Phase 0 is sound.
Phase 0 report artifacts are current-authoritative. The Phase 1 restart
re-does Steps 1.1-1.9 in the notebook format, producing both the notebook
exploration record and the (already-existing) report artifacts. For steps
like 1.1-1.7 and 1.9 where Pattern A functions exist, the notebook calls
those functions and adds narrative. For Step 1.8, the notebook replaces the
ad-hoc markdown-only report with an executable notebook.

#### Research log disposition

**Decision:** Accept the working recommendation from `spec_planning.md` A.5.

Concrete steps:
1. Move `reports/research_log.md` to
   `reports/_archive/research_log_pre_notebook_sandbox.md`.
2. Create a fresh `reports/research_log.md` with front-matter:
   ```markdown
   # Research Log

   Thesis: "A comparative analysis of methods for predicting game results
   in real-time strategy games, based on the examples of StarCraft II and
   Age of Empires II."

   Reverse chronological entries. Each entry documents the reasoning and
   learning behind code changes — intended as source material for thesis
   writing.

   > This log continues from `reports/_archive/research_log_pre_notebook_sandbox.md`,
   > which covers all work through 2026-04-07. The pivot to a notebook-based
   > exploration sandbox is documented in the first entry below. Entries before
   > the pivot are preserved verbatim in the archive and remain citable as
   > methodology-history sources (what was tried and why it changed), but are
   > no longer citable as findings sources for Phase 1+.

   ---
   ```
3. The first entry in the fresh log is the notebook-sandbox infrastructure
   work itself (this Category C chore).
4. Subsequent entries cover the Phase 1 restart steps.

**Validation against discovery:** Discovery Section 4 (Gap 2) documents that
pre-restart entries lack the structured template. The archive preserves them
verbatim as required. The fresh log starts clean with the current template.
Discovery Section 4 (Gap 3) documents thin reasoning chains in some Phase 1
entries. The restart addresses this by producing notebooks that carry the full
reasoning chain, with the research log entry pointing at the notebook.

**Why not edit the existing log?** The existing log is 1,502 lines with
entries from the entire project history, including the methodology restart
narrative (lines 1379-1414) which is itself thesis-relevant. Editing it risks
introducing inconsistencies. A clean break with an archive pointer is safer
and produces a clearer signal to the reviewer: anything in the archive is
historical, anything in the fresh log is current.

#### Superseded report artifacts

**Decision:** Add a `SUPERSEDED.md` marker to the `src/rts_predict/sc2/reports/sc2egset/`
directory, listing specific Phase 1 artifacts that will be regenerated by the
restart. Do NOT move artifacts to an archive directory.

**Justification:** The Phase 1 artifacts (all `01_*` files) were produced by
Pattern A functions that still exist in `exploration.py`. They are currently
correct — the functions are tested and the data has not changed. What is being
restarted is not the artifacts themselves but the *exploration narrative*
around them. Moving them to an archive would create confusion because the
functions that generate them still reference `DATASET_REPORTS_DIR`. The
`SUPERSEDED.md` marker lists each `01_*` artifact with its status:
- `will_be_regenerated` — the notebook restart will re-run the function and
  produce the same (or updated) artifact.
- `will_be_replaced` — the notebook restart will produce a new artifact that
  supersedes this one (applies to `01_08_game_settings_audit.md` which will
  go from markdown-only to function-backed).

Phase 0 artifacts (`00_*`) are NOT listed in `SUPERSEDED.md`. They are
current-authoritative.

The `SUPERSEDED.md` file is removed after the Phase 1 restart is complete and
all artifacts are regenerated.

The reviewer agent can distinguish current from superseded by checking: if a
file is listed in `SUPERSEDED.md` and has not been regenerated since the
notebook sandbox was introduced, it is not citable as a current finding.

#### Thesis continuity

**Explicit statement:** The archived research log
(`reports/_archive/research_log_pre_notebook_sandbox.md`) and all report
artifacts in their current state remain under version control and are citable
as **methodology-history** sources. They document:
- The initial methodology restart (lines 1379-1414): why exploration-first
  ordering is necessary.
- The pre-restart pipeline results (lines 1489-1502): what the baseline
  looked like before proper data exploration.
- The feature engineering decisions that were later invalidated (lines 1418-1437):
  what happens when you build features before understanding data.

These are not citable as **findings** sources because the underlying data
exploration was incomplete at the time they were written. The distinction is:
methodology-history ("we tried X and observed Y, which motivated Z") vs.
findings ("the dataset has property W, which implies V"). The archived log
is the former; the notebook restart produces the latter.

---

## Phase B — Implementation Plan

### B.1 Directory and File Layout

```
sandbox/
  README.md                         # Purpose, conventions, link to this plan
  sc2/
    sc2egset/                       # Notebooks for SC2EGSet dataset, Phases 0-2
      01_08_game_settings_audit.ipynb       # Proof-of-concept (B.7)
      01_08_game_settings_audit.py          # Jupytext percent-format pair
  aoe2/
    aoe2companion/                  # Placeholder — populated when AoE2 Phase 1 begins
      .gitkeep
    aoestats/                       # Placeholder — populated when AoE2 Phase 1 begins
      .gitkeep
```

New module stubs (see B.4 for signatures):

```
src/rts_predict/
  common/
    notebook_utils.py               # DuckDB connection helper for notebooks
    notebook_utils_test.py          # Co-located test (or common/tests/ if dir exists)
```

No changes to the `src/rts_predict/sc2/` or `src/rts_predict/aoe2/` package
structure. Notebooks import from existing modules; no new game-scoped modules
are created in this chore.

The `reports/` tree is unchanged. A new `reports/_archive/` directory is created
for the research log archive (see B.9).

### B.2 Tooling Setup

#### B.2.1 `pyproject.toml` additions

Add to `[tool.poetry.group.dev.dependencies]`:

```toml
jupyterlab = "^4.4.0"
ipykernel = "^6.30.0"
jupytext = "^1.16.0"
nbconvert = "^7.16.0"
pre-commit = "^3.7.0"
```

These are dev-only dependencies. They are not required for `poetry run sc2`
or any production code path.

#### B.2.2 Jupytext configuration

Create `jupytext.toml` at repo root:

```toml
# Jupytext configuration — pairs .ipynb with .py:percent for clean diffs.
# See: https://jupytext.readthedocs.io/en/latest/config.html

[formats]
"sandbox//" = "ipynb,py:percent"

[notebook_metadata_filter]
# Strip volatile metadata from .ipynb to reduce diff noise.
# Keep only: kernelspec, jupytext config.
selected = "jupytext,kernelspec"
```

This configuration:
- Pairs every `.ipynb` under `sandbox/` with a `.py:percent` file in the same
  directory.
- Strips execution counts, widget state, and cell IDs from the `.ipynb` on save,
  reducing diff noise.
- The `.py:percent` format uses `# %%` cell markers, which Ruff can lint
  (the PostToolUse `lint-on-edit.sh` hook fires on `.py` writes).

#### B.2.3 `.gitignore` additions

Add to `.gitignore`:

```gitignore
# Notebook sandbox — checkpoint artifacts (if not already present)
sandbox/**/.ipynb_checkpoints/
```

No `.ipynb` files are gitignored. Both `.ipynb` and `.py` pairs are committed
(see A.3 Git policy decision).

#### B.2.4 `.claude/settings.json` additions

Add to the `allow` list:

```json
"Write(sandbox/**)",
"Edit(sandbox/**)",
"Write(jupytext.toml)",
"Edit(jupytext.toml)"
```

#### B.2.5 Pre-commit hook for jupytext sync

Add to `.pre-commit-config.yaml` (create the file if it does not exist):

```yaml
- repo: https://github.com/mwouts/jupytext
  rev: v1.16.0  # Match the version pinned in pyproject.toml
  hooks:
    - id: jupytext
      args: [--sync]
      files: ^sandbox/.*\.(ipynb|py)$
```

This hook runs on any commit that modifies a file under `sandbox/` matching
`.ipynb` or `.py`. In `--sync` mode, jupytext regenerates the paired file so
the two are guaranteed to be consistent at commit time. The `files` pattern
scopes the hook to `sandbox/` only — it does not touch `src/` or `tests/`.

Add `pre-commit` to dev dependencies in `B.2.1` if not already present.

#### B.2.6 `pyproject.toml` coverage omit

Add `"sandbox/**"` to `[tool.coverage.run] omit` so jupytext `.py` pair files
are not collected by coverage. Coverage measures `src/rts_predict/` only.

### B.3 Notebook Template Contract

Every exploration notebook must follow this structure. The reviewer agent
(updated in B.6) checks compliance mechanically.

#### Cell 1: Front-matter (markdown)

```markdown
# {Phase X / Step X.Y} — {Descriptive Title}

| Field | Value |
|-------|-------|
| Phase | {phase_id, e.g. 1} |
| Step | {step_id, e.g. 1.8} |
| Dataset | {sc2egset / aoe2companion / aoestats} |
| Game | {sc2 / aoe2} |
| Date | {YYYY-MM-DD} |
| Report artifacts | `{path/to/artifact1.csv}`, `{path/to/artifact2.md}` |
| Scientific question | {One sentence: what are we trying to learn?} |
| ROADMAP reference | `{path/to/ROADMAP.md}` Step X.Y |
```

**Reviewer check:** Cell 1 must contain the `| Phase |` and `| Step |` rows.
`phase_id` must be a valid integer. `step_id` must match pattern `\d+\.\d+[A-Z]?`.

#### Cell 2: Imports (code)

```python
# %% [markdown]
# ## Setup

# %%
from rts_predict.common.notebook_utils import get_notebook_db
# ... other imports from src/rts_predict/ ...

con = get_notebook_db("sc2", "sc2egset")
```

**Reviewer check:** No `import processing`. All imports from `rts_predict.*` or
stdlib/installed packages. (The no-inline-definitions rule applies to all cells —
see "Cell complexity rules" below.)

#### Cells 3–N: Query/computation cells (code + markdown)

Each analytical step is a pair:
1. A **code cell** containing the SQL query and its execution via `con.fetch_df(query)`.
2. A **markdown cell** containing the interpretation.

**Reviewer check:** Every code cell that executes a query must be followed by
a markdown cell within 2 cells.

#### Cell N+1: Conclusion (markdown)

```markdown
## Conclusion

### Artifacts produced
- `{path/to/artifact1.csv}` — {one-line description}

### Follow-ups
- {Follow-up 1: what and where it feeds}

### Thesis mapping
- {Target section in `thesis/THESIS_STRUCTURE.md`}
```

**Reviewer check:** Must contain the `## Conclusion` heading and at least one
artifact path or a note "No artifacts — exploratory only."

#### Cell N+2: Cleanup (code)

```python
# %%
con.close()
```

**Reviewer check:** Last code cell must call `.close()` on the connection.

#### Cell complexity rules (configured in `sandbox/notebook_config.toml`)

The reviewer enforces these via AST-based checks reading config from
`sandbox/notebook_config.toml`:

- **`[cells] max_lines = 50`** — No cell may exceed 50 lines (matches the existing
  `python-code.md` convention of "Max ~50 lines per function"; a cell should not
  exceed one function's worth of logic).
- **No inline definitions** — `ast.FunctionDef`, `ast.AsyncFunctionDef`,
  `ast.ClassDef` anywhere in any code cell. `ast.Assign`/`ast.AnnAssign`
  where the value is `ast.Lambda` anywhere. All functions and classes live in
  `src/rts_predict/` and are imported.
- **Single config location** — `sandbox/notebook_config.toml` is the only place
  these thresholds live. No magic numbers in reviewer code or prose.

### B.4 Library Module Stubs

#### B.4.1 `src/rts_predict/common/notebook_utils.py`

```python
"""Notebook helpers — DuckDB connection factory for sandbox notebooks.

Zero game-domain content. Provides a read-only DuckDB connection
pre-configured for the specified dataset.
"""

from __future__ import annotations

import logging
from pathlib import Path

from rts_predict.common.db import DuckDBClient

logger = logging.getLogger(__name__)


def get_notebook_db(
    game: str,
    dataset: str,
    *,
    read_only: bool = True,
) -> DuckDBClient:
    """Return a DuckDBClient for use in a Jupyter notebook.

    Resolves the dataset config from the game package's config module
    and returns an open connection. The connection is read-only by default
    to avoid single-writer lock conflicts with the CLI.

    Args:
        game: Game identifier ("sc2" or "aoe2").
        dataset: Dataset identifier (e.g. "sc2egset", "aoe2companion").
        read_only: Open in read-only mode. Default True.

    Returns:
        An open DuckDBClient. Caller must close it (use as context manager
        or call .close() explicitly).

    Raises:
        ValueError: If game or dataset is not recognized.
    """
    ...


def get_reports_dir(game: str, dataset: str) -> Path:
    """Return the absolute path to the dataset's reports directory.

    Args:
        game: Game identifier ("sc2" or "aoe2").
        dataset: Dataset identifier (e.g. "sc2egset").

    Returns:
        Absolute Path to the reports directory.

    Raises:
        ValueError: If game or dataset is not recognized.
    """
    ...
```

**Implementation notes:**
- `get_notebook_db` imports the game config module dynamically via
  `importlib.import_module(f"rts_predict.{game}.config")`, looks up `DATASETS`
  for the requested dataset, creates a `DuckDBClient(config, read_only=read_only)`,
  calls `__enter__()`, and returns the open client.
- `get_reports_dir` resolves `DATASET_REPORTS_DIR` from the config module.

**Test:** Tests that `get_notebook_db("sc2", "sc2egset")` returns a `DuckDBClient`
in read-only mode, that `SELECT 1 AS x` succeeds, and `ValueError` for invalid
game/dataset.

#### B.4.2 No new game-scoped modules

`src/rts_predict/sc2/data/exploration.py` already contains all Phase 1 functions.
No new game-scoped exploration module is created in this chore.

### B.5 Reproducibility Enforcement

#### B.5.1 Fresh-kernel execution command

```bash
poetry run jupyter nbconvert \
    --to notebook \
    --execute \
    --inplace \
    --ExecutePreprocessor.timeout=600 \
    sandbox/sc2/sc2egset/01_08_game_settings_audit.ipynb
```

**Timeout justification:** The largest known Phase 1 query (Step 1.6, scanning
~62M tracker rows) takes approximately 2 minutes on current hardware (M4 Max,
36 GB). 600 seconds is a 5× safety margin accommodating future heavier queries
without hiding performance regressions. The value lives in
`sandbox/notebook_config.toml` as `[execution] timeout_seconds = 600` and is
measured/updated during B.9.16 (proof-of-concept run). If Step 1.8 execution
time materially exceeds 120 s, the default will be revised upward with a
comment citing the measured value.

#### B.5.2 Seed policy

Notebooks that use random operations must import from config:
`from rts_predict.sc2.config import RANDOM_SEED` and pass it to `np.random.seed()`.

#### B.5.3 Research log update protocol

After completing a notebook, the executor adds an entry to `reports/research_log.md`
following `RESEARCH_LOG_TEMPLATE.md`. The "How (reproducibility)" section contains
the notebook path. Key SQL is inlined for quick reference.

### B.6 Subagent Updates

#### B.6.1 `.claude/agents/executor.md` addition

Add after "Category-specific rules":

```markdown
## Notebook workflow (sandbox/)

1. Use the template from `_current_plan.md` B.3.
2. All functions and classes must live in `src/rts_predict/` and be imported.
   Cells are capped at `[cells] max_lines` from `sandbox/notebook_config.toml`.
   Notebooks are thin orchestration only — SQL strings, function calls, and
   display logic.
3. After completing the notebook, run fresh-kernel execution:
   `poetry run jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 {path}`
4. Verify both `.ipynb` and `.py` pair files are present and synced.
5. Update `reports/research_log.md` with a new entry.
6. DuckDB connections are read-only by default. Document any write-access need
   in the front-matter.
7. Do NOT import from `processing.py` in any notebook.
```

#### B.6.2 `.claude/agents/reviewer.md` addition

Add after "For code changes":

```markdown
## For notebook changes (sandbox/)

1. **Template compliance:** Cell 1 has `| Phase |` and `| Step |`; Cell 2 is
   imports-only; final markdown cell has `## Conclusion`; final code cell has
   `.close()`.
2. **Jupytext sync:** Every modified `.ipynb` has a corresponding modified `.py`
   in the same directory.
3. **No inline definitions (AST-based):** Flag any `ast.FunctionDef`,
   `ast.AsyncFunctionDef`, `ast.ClassDef` in any code cell, and any
   `ast.Assign`/`ast.AnnAssign` where the value is `ast.Lambda` anywhere.
   All helpers must live in `src/rts_predict/`.
4. **Cell size (AST-based):** Flag any cell exceeding `[cells] max_lines` from
   `sandbox/notebook_config.toml` (default 50).
5. **Phase boundary check:** Imports in a Phase 1 notebook must not reference
   `features/`, `feature_`, `models/`, or `model_` modules. Flag `import processing`.
6. **Research log entry:** A new entry in `reports/research_log.md` references
   the notebook path.
7. **Report artifact consistency:** If the notebook front-matter lists artifacts,
   verify those files are present in the changeset.
```

### B.7 Migration Proof-of-Concept

**Step 1.8 (Game settings and replay field completeness audit)** is the
proof-of-concept notebook.

Justification:
- Only Phase 1 step that followed Pattern B (no function in `exploration.py`).
- Existing `01_08_game_settings_audit.md` (456 lines) contains embedded SQL
  ready to port.
- Has companion CSV (`01_08_error_flags_audit.csv`).
- Demonstrates the full notebook workflow without requiring a new Pattern A function.

Concrete steps:
1. Create `sandbox/sc2/sc2egset/01_08_game_settings_audit.ipynb` per B.3 template.
2. Cell 1: front-matter for Phase 1 / Step 1.8.
3. Cell 2: `get_notebook_db("sc2", "sc2egset")`.
4. Port each SQL block from the existing report into code+interpretation cell pairs.
5. Conclusion cell linking to the existing report artifacts.
6. Cleanup cell with `con.close()`.
7. Run fresh-kernel execution (B.5.1 command) and record timing.
8. Update `[execution] timeout_seconds` in `sandbox/notebook_config.toml` if
   measured time warrants revision.
9. Verify `.py` pair exists.

### B.8 Gate Conditions

All 14 must be true before the executor declares the chore complete:

1. `sandbox/sc2/sc2egset/` exists with the proof-of-concept `.ipynb` + `.py` pair.
2. `sandbox/aoe2/aoe2companion/.gitkeep` and `sandbox/aoe2/aoestats/.gitkeep` exist.
3. `sandbox/README.md` exists.
4. `jupytext.toml` exists at repo root.
5. `sandbox/notebook_config.toml` exists with `[cells] max_lines`, `[execution] timeout_seconds`, and supporting keys.
6. `src/rts_predict/common/notebook_utils.py` exists with `get_notebook_db()` and `get_reports_dir()` implemented and tested.
7. Fresh-kernel execution of the proof-of-concept notebook completes without error.
8. `poetry run pytest tests/ src/ -v --cov=rts_predict --cov-report=term-missing` passes with coverage ≥ 95%.
9. `poetry run ruff check src/ tests/` and `poetry run mypy src/rts_predict/` are clean.
10. `.claude/agents/executor.md` and `.claude/agents/reviewer.md` are updated per B.6.
11. `reports/_archive/research_log_pre_notebook_sandbox.md` exists (archived log).
12. `reports/research_log.md` is the fresh log with ≥ 2 entries.
13. `src/rts_predict/sc2/reports/sc2egset/SUPERSEDED.md` exists.
14. `.pre-commit-config.yaml` exists with the jupytext sync hook. `poetry run pre-commit run jupytext --all-files` exits cleanly after the proof-of-concept notebook is committed.

### B.9 Archival and Restart Execution Steps

Execute in order. Each step is atomic.

#### B.9.1 Create archive directory
```bash
mkdir -p reports/_archive
```

#### B.9.2 Archive the current research log
```bash
git mv reports/research_log.md reports/_archive/research_log_pre_notebook_sandbox.md
```
Do not modify the archive after this point.

#### B.9.3 Create the fresh research log

At this point `reports/research_log.md` does not exist (it was moved in B.9.2).
Create it fresh with the content below.

Write `reports/research_log.md` with front-matter pointing to the archive:

```markdown
# Research Log

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

Reverse chronological entries.

> This log continues from `reports/_archive/research_log_pre_notebook_sandbox.md`,
> covering all work through 2026-04-07. The pivot to a notebook-based exploration
> sandbox is documented in the first entry below. Pre-pivot entries remain citable
> as methodology-history but not as findings sources for Phase 1+.

---
```

#### B.9.4 Create SUPERSEDED.md

Write `src/rts_predict/sc2/reports/sc2egset/SUPERSEDED.md` listing Phase 1
artifacts with `will_be_regenerated` or `will_be_replaced` semantics.
Phase 0 artifacts (`00_*`) are NOT listed.

Key entries:
- `01_08_error_flags_audit.csv` — `will_be_replaced` (no function)
- `01_08_game_settings_audit.md` — `will_be_replaced` (no function)
- All `01_01_*` through `01_07_*` and `01_09_*` artifacts — `will_be_regenerated`
  (functions exist in `exploration.py`)

#### B.9.5 Create sandbox directory structure
```bash
mkdir -p sandbox/sc2/sc2egset
mkdir -p sandbox/aoe2/aoe2companion
mkdir -p sandbox/aoe2/aoestats
touch sandbox/aoe2/aoe2companion/.gitkeep
touch sandbox/aoe2/aoestats/.gitkeep
```

#### B.9.6 Create `sandbox/README.md` (see B.2 for content outline)

#### B.9.7 Create `jupytext.toml` at repo root (see B.2.2)

#### B.9.8 Create `sandbox/notebook_config.toml`

```toml
# Notebook sandbox configuration — single source for all tooling thresholds.

[cells]
# Maximum lines per notebook cell. Matches python-code.md "Max ~50 lines per function".
# Enforced by AST-based reviewer check.
max_lines = 50

[execution]
# Default timeout in seconds for fresh-kernel nbconvert execution.
# Justified by Step 1.6 (~2 min on M4 Max 36 GB) * 5x safety margin.
# Update after measuring proof-of-concept (B.9.16).
timeout_seconds = 600

```

#### B.9.9 Install dev dependencies
```bash
poetry add --group dev "jupyterlab>=4.4.0,<5" "ipykernel>=6.30.0,<7" "jupytext>=1.16.0,<2" "nbconvert>=7.16.0,<8" "pre-commit>=3.7.0,<4"
```

#### B.9.10 Install and configure pre-commit

```bash
poetry run pre-commit install
```

Create or update `.pre-commit-config.yaml` with the jupytext sync hook
(see B.2.5). Verify by running:

```bash
poetry run pre-commit run jupytext --all-files
```

This should exit cleanly on a fresh repo (no `.ipynb` files exist yet) and
will activate when the proof-of-concept notebook is created in the later step.

#### B.9.11 Implement `notebook_utils.py` and tests (see B.4.1)

#### B.9.12 Update `.claude/settings.json` (see B.2.4)

#### B.9.13 Update `.gitignore` (see B.2.3)

#### B.9.14 Update `pyproject.toml` coverage omit (see B.2.6)

#### B.9.15 Update subagent configs (see B.6)

#### B.9.16 Create the proof-of-concept notebook (see B.7)

Includes: run fresh-kernel execution, record timing, update
`notebook_config.toml` `timeout_seconds` if warranted.

#### B.9.17 Write research log entries

Two entries in `reports/research_log.md`:
1. Infrastructure entry (Category C): sandbox dirs, jupytext, notebook_utils,
   subagent config updates.
2. Step 1.8 re-run entry (Category A, Phase 1, sc2egset): notebook replaces
   the Pattern B report.

#### B.9.18 Run all gate checks (B.8)

---

## Execution Batches

| Batch | Steps | Description |
|-------|-------|-------------|
| 1 | B.9.1–B.9.3 | Archive and fresh log |
| 2 | B.9.4–B.9.6 | SUPERSEDED marker, dirs, README |
| 3 | B.9.7–B.9.10 | Config files, install deps, pre-commit |
| 4 | B.9.11 | Implement notebook_utils + tests |
| 5 | B.9.12–B.9.15 | Config updates, coverage, subagent configs |
| 6 | B.9.16 | Proof-of-concept notebook |
| 7 | B.9.17 | Research log entries |
| 8 | B.9.18 | Gate checks |

**Branch:** `chore/notebook-sandbox`
**Version bump:** 0.23.0 (chore → patch)

---

## References

| Shorthand | Path |
|-----------|------|
| Discovery report | `_discovery_notebook_sandbox.md` |
| Scientific invariants | `.claude/scientific-invariants.md` |
| Architecture | `ARCHITECTURE.md` |
| Agent manual | `docs/agents/AGENT_MANUAL.md` |
| Common contract | `src/rts_predict/common/CONTRACT.md` |
| Research log template | `reports/RESEARCH_LOG_TEMPLATE.md` |
| SC2 PHASE_STATUS | `src/rts_predict/sc2/PHASE_STATUS.yaml` |
| AoE2 PHASE_STATUS | `src/rts_predict/aoe2/PHASE_STATUS.yaml` |
| SC2 exploration.py | `src/rts_predict/sc2/data/exploration.py` |
| SC2 audit.py | `src/rts_predict/sc2/data/audit.py` |
| SC2 config.py | `src/rts_predict/sc2/config.py` |
| Common db.py | `src/rts_predict/common/db.py` |
| Spec (planning) | `spec_planning.md` |
| Spec (discovery) | `spec_discovery.md` |
| Spec (general) | `spec_general.md` |
| DuckDB Client | `src/rts_predict/common/db.py` (DuckDBClient class) |
| Step 1.8 report | `src/rts_predict/sc2/reports/sc2egset/01_08_game_settings_audit.md` |
| pyproject.toml | `pyproject.toml` |
| .gitignore | `.gitignore` |
| settings.json | `.claude/settings.json` |
| executor.md | `.claude/agents/executor.md` |
| reviewer.md | `.claude/agents/reviewer.md` |
| notebook_config.toml | `sandbox/notebook_config.toml` |
