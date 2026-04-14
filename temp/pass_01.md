You are the planner-science agent. Your task is a PROGRESS ASSESSMENT, not a plan. Do not propose new work in this pass — only establish where the project currently stands.

## Task

For each of the three datasets — `sc2egset`, `aoe2companion`, `aoestats` — determine the current completion state of **Phase 01 (Data Exploration)** against:

1. The Step definitions enumerated in that dataset's `src/rts_predict/games/<game>/datasets/<dataset>/reports/ROADMAP.md`.
2. The actual artifacts produced under `sandbox/<game>/<dataset>/NN_NN_NN_*.{py,ipynb}`, including notebooks with the SQL / DuckDB queries and EDA operations they contain.
3. The Phase 01 exit criteria implied by `docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md`, which covers four sub-arcs: **Data Acquisition & Source Inventory**, **Data Profiling (column-level and dataset-level)**, **Exploratory Data Analysis (univariate → bivariate → multivariate)**, and **Data Cleaning & Validation**.

The three datasets are independent scientific entities. Produce **three separate assessments**. Do not average, aggregate, or compare them in Pass 1.

## Sources of truth (consult in this order, flag any drift)

1. `docs/TAXONOMY.md` — Phase / Pipeline Section / Step vocabulary. Do not use forbidden terms.
2. `docs/PHASES.md` — canonical Phase 01 Pipeline Sections.
3. `.claude/scientific-invariants.md` — binding rules. Invariants #6 (SQL shipped with findings) and #7 (no magic numbers) are central to this assessment.
4. `docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md` — the target state.
5. `src/rts_predict/games/<game>/datasets/<dataset>/reports/ROADMAP.md` — per-dataset Step index with definitions.
6. `sandbox/<game>/<dataset>/` — actual executed artifacts.

## What counts as evidence

A Step is **Done** only if ALL of the following hold:
- Its spec exists and validates against the Step template.
- A notebook at the matching `NN_NN_NN` path under `sandbox/` exists and has been executed end-to-end (outputs/artifacts present).
- The empirical claims in that notebook are accompanied by the SQL or code that produced them (invariant #6).
- Any thresholds or cutoffs appearing in the notebook trace back to a config file, not an inline literal (invariant #7).
- The notebook's findings map to at least one exit criterion of its Pipeline Section.

A Step is **Partial** if the step definition and notebook exist but one of: execution incomplete, SQL missing for some claim, magic numbers present, findings do not close the Pipeline Section's exit criterion.

A Step is **Missing** if either the definition in Roadmap or the notebook does not exist.

A Step is **Specified-only** if placeholder in ROADMAP exists but no notebook exists under `sandbox/`.

A Step is **Orphan** if a notebook exists under `sandbox/` but no ROADMAP Step defines it — this is a taxonomy violation and must be flagged.

## Output format

Produce a single Markdown document and extras like jsons or png charts. No prose paragraphs longer than 4 lines. Use the following structure verbatim.

### Header
- Date, assessor ("planner-science"), scope ("Phase 01 progress assessment").

### For each dataset (three top-level sections: sc2egset, aoe2companion, aoestats)

**1. Step inventory table**

| Step ID | Step name | Notebook? | Executed? | SQL present? | Magic-number clean? | Status |
|---|---|---|---|---|---|---|

Status ∈ {Done, Partial, Specified-only, Missing, Orphan}.

**2. Pipeline Section coverage**

For each Pipeline Section listed in `docs/PHASES.md` under Phase 01, state:
- Section name.
- Number of Steps defined / Done / Partial / Missing.
- Whether the Section's exit criterion (per the Phase 01 manual) is met, partially met, or not met. One sentence of justification per verdict.

**3. Manual-level gap analysis**

Map the dataset's current state onto the four sub-arcs of `01_DATA_EXPLORATION_MANUAL.md`:
- **Source inventory (Datasheets / Data Cards):** present? sufficient? what's missing?
- **Column-level profiling:** coverage of null/cardinality/distribution/outlier checks.
- **Dataset-level profiling:** row counts, duplicates, temporal coverage, class balance, completeness matrix, correlation matrix.
- **EDA layers:** univariate done? bivariate done? multivariate done?
- **Cleaning & validation:** documented cleaning rules? raw-data immutability respected? staging layer present?

For each sub-arc, one of: Complete / Partial / Not started / Not applicable (with justification).

**4. Invariant violations observed**

List concrete violations, each as: invariant number, file path, one-line description. No speculation — only observed violations.

**5. Distance-to-Phase-Completion summary**

A final block per dataset with:
- Single-line verdict: one of {Phase 01 complete, Phase 01 substantially complete with gaps, Phase 01 partially complete, Phase 01 barely started, Phase 01 not started}.
- Numbered list of the concrete remaining items needed to reach Phase 01 completion, in dependency order. Each item references a Step ID or a manual sub-arc.
- Explicit statement of any hard blockers (e.g., raw data not yet acquired, schema capture failed).

### Cross-dataset summary (final section, strictly factual)

A 3-row table: dataset | verdict | number of remaining items. No editorial comparison, no "most advanced" ranking.

## Rules

- Do not propose new Steps or new Phase structure. This is assessment only.
- Do not draft thesis prose or methodology claims.
- If a source of truth is missing or inconsistent, flag it and continue — do not invent contents.
- Every non-trivial claim must cite a file path. Paths only, no reconstructed content.
- If you cannot determine a Step's status from available evidence, mark it Unknown and state what would be needed to resolve it.
- Honesty clause: if a dataset is essentially at zero, say so plainly. Do not inflate preliminary scaffolding into "progress".