
# Adversarial Architecture & Documentation Audit

**Date:** 2026-04-11
**Scope:** Full repository documentation architecture, templates, contracts, token economy
**Phase:** Cross-cutting (Phase 01 in_progress)
**Agent:** reviewer-adversarial (Opus)

---

## Invariant Compliance Snapshot

```
#1 (per-player split):    N/A — no split code exists yet
#2 (canonical nickname):  N/A — no identity code exists yet
#3 (temporal < T):        AT RISK — see Finding 1.1, 1.2
#4 (prediction target):   N/A — no feature code exists yet
#5 (symmetric treatment): N/A — no feature code exists yet
#6 (reproducibility):     RESPECTED — notebook template mandates logging + artifact listing
#7 (no magic numbers):    RESPECTED — template and invariant file both mandate justification
#8 (cross-game protocol): AT RISK — see Finding 2.1, Finding 5.1
```

---

## EXECUTIVE SUMMARY

This repository has an unusually disciplined documentation architecture for an MSc thesis -- the 8-tier source-of-truth hierarchy, the per-dataset ROADMAP system, and the notebook template with enforcement tiers are well above the norm. The problems are not in the design intent but in three categories:

1. **Redundancy tax.** The same information is stated in too many places, creating drift surfaces. The architecture is ~125 KB of mandatory context before any actual work begins, plus ~50 KB in agent definitions, plus ~185 KB in methodology manuals. This is roughly 90,000 tokens at session start for a comprehensive read, which is a significant fraction of even the 200K context window.

2. **Convention drift already present.** Two naming conventions are documented but only one is implemented on disk. The chapter numbering error has already propagated to 7 files. The common/CONTRACT.md references "Invariant #10" which does not exist in scientific-invariants.md (the invariants were renumbered to 8 but the CONTRACT was not updated).

3. **Premature commitment.** Phase 06 (Cross-Domain Transfer) has 9 Pipeline Sections defined, but the thesis is still in step 01_01_01 of Phase 01. The thesis structure locks in 7 chapters with detailed subsection numbering before a single model has been trained. WRITING_STATUS.md has 39 entries, 35 of which are BLOCKED. This creates rigidity that will cost rework when Phase 01 findings inevitably reshape the plan.

---

## 1. TEMPORAL DISCIPLINE

### Finding 1.1 -- ml-protocol.md activates "from Phase 04 onward" but temporal leakage risks begin in Phase 02

**Evidence:** `.claude/ml-protocol.md` line 1: `> **Phase activation:** Active from Phase 04 (Model Training) onward.` The notebook template mandates leakage verification `condition: phase_02_plus` (notebook_template.yaml, cell_leakage_verification). But the ml-protocol.md file -- which contains the most concrete leakage rules (the three failure modes, the expanding window requirement) -- explicitly tells agents not to read it until Phase 04.

**Risk:** An executor agent working on Phase 02 feature engineering will read scientific-invariants.md (Invariant #3, high-level) but skip ml-protocol.md (where the three specific failure modes are enumerated). The notebook template catches this partially via the leakage verification cell, but the protocol's "rolling aggregates computed using the target game's own value" check is more actionable than the invariant's "strictly `match_time < T`."

**Recommendation [WARNING]:** Either remove the Phase 04 activation gate from ml-protocol.md, or extract the "Three leakage failure modes" section into scientific-invariants.md where it is unconditionally read. The three failure modes are invariant-grade constraints, not implementation details.

### Finding 1.2 -- No normalization leakage guard documented anywhere

**Evidence:** Scientific Invariant #3 covers rolling averages, win rates, head-to-head, and ratings. The ml-protocol covers the same three failure modes. Neither document mentions the normalization leakage vector: computing feature mean/std on the full dataset (including test data) and using those statistics to scale features. This is a well-known leak in temporal cross-validation settings (Arlot & Celisse, 2010; de Prado, 2018, "Advances in Financial Machine Learning", Ch. 7).

**Risk:** When Phase 03-04 work begins, an executor could compute global z-scores across the entire dataset, contaminating test-set predictions with distributional information from the test period. The python-code.md rule "Fit scalers/encoders ONLY on training split" covers this indirectly, but it is a `.claude/rules/` file that loads only when `.py` files are edited -- it does not load for ROADMAP planning or notebook markdown cells.

**Recommendation [WARNING]:** Add normalization/scaling leakage to Invariant #3 or ml-protocol.md. Explicitly: "Mean, standard deviation, min/max, and any other summary statistics used for feature scaling must be computed on training data only. The scaler object must be fit on the training fold and applied (transform only) to validation and test folds."

---

## 2. STATISTICAL METHODOLOGY

### Finding 2.1 -- Friedman N=2 problem identified but not yet fixed

**Evidence:** `_current_plan.md` Step 3 correctly identifies that the Friedman test is inappropriate with only 2 datasets as blocks (N must be >= 5 per Demsar 2006). The fix is queued as a P1 change to Invariant #8. However, the fix has NOT been executed yet. The current Invariant #8 (`.claude/scientific-invariants.md`) still says "Friedman omnibus test, then pairwise Wilcoxon signed-rank with Holm correction, complemented by Bayesian signed-rank with ROPE."

**Risk:** Any agent reading Invariant #8 today (which every agent does at session start) receives incorrect statistical methodology guidance. If Phase 03+ work begins before this fix lands, the evaluation protocol will be built on a method the thesis itself has already identified as inappropriate.

**Recommendation [BLOCKER]:** Execute `_current_plan.md` Step 3 before any Phase 03+ work. The invariant file is the highest-precedence document in the repository (ARCHITECTURE.md tier 1). An error there contaminates every downstream artifact.

### Finding 2.2 -- Evaluation hierarchy partially contradicts itself

**Evidence:** THESIS_STRUCTURE.md section 4.4.4 lists "Primary: accuracy, log-loss, ROC-AUC." The evaluation manual (05_EVALUATION_AND_ANALYSIS_MANUAL.md) and `_current_plan.md` Step 4 both argue that Brier score with Murphy decomposition should be primary. The fix is queued but not executed.

**Risk:** Same as 2.1 -- the thesis structure is a reference document agents consult. Until corrected, an executor writing baseline evaluation code will implement accuracy as the primary metric rather than proper calibration assessment.

**Recommendation [WARNING]:** Execute `_current_plan.md` Step 4 alongside Step 3. Metric hierarchy decisions made before Phase 03 are load-bearing.

---

## 3. FEATURE ENGINEERING SOUNDNESS

### Finding 3.1 -- N/A at this phase

Phase 02 has not started. No feature code exists. The abstractions in scientific-invariants.md #5 (symmetric treatment) are game-agnostic as required.

### Finding 3.2 -- common/CONTRACT.md references nonexistent Invariant #10

**Evidence:** `src/rts_predict/common/CONTRACT.md` references "Invariant #10 (shared evaluation protocol, identical metrics, matched experimental conditions)." The current scientific-invariants.md has only 8 invariants, numbered 1-8. The CHANGELOG.md confirms this was a historical numbering that has been superseded.

**Risk:** An agent reading CONTRACT.md and looking for Invariant #10 will find nothing and may conclude the constraint does not exist or was removed intentionally.

**Recommendation [WARNING]:** Update CONTRACT.md to reference Invariant #8. This is a 10-second edit.

---

## 4. THESIS DEFENSIBILITY

### Finding 4.1 -- Chapter numbering error propagated to 7 files

**Evidence:** `_current_plan.md` Step 1 documents this comprehensively. All three ROADMAPs and the research log map to "Chapter 3 -- Data & Methodology" but THESIS_STRUCTURE.md defines Chapter 3 as "Related Work" and Chapter 4 as "Data and Methodology." The error exists in:
- `src/rts_predict/sc2/reports/sc2egset/ROADMAP.md:90`
- `src/rts_predict/aoe2/reports/aoe2companion/ROADMAP.md:100`
- `src/rts_predict/aoe2/reports/aoestats/ROADMAP.md:107`
- `reports/research_log.md:98`
- Three notebook .py files (the Conclusion cells)

**Risk:** Every future step that executes 01_01_XX through 01_06_XX will copy this wrong chapter reference into its thesis_mapping field. The longer it stays unfixed, the more files accumulate the error.

**Recommendation [BLOCKER]:** Execute `_current_plan.md` Step 1 immediately. This was already identified as a P0 blocker in the plan.

### Finding 4.2 -- THESIS_STRUCTURE.md locks in detail prematurely

**Evidence:** THESIS_STRUCTURE.md is 444 lines. It specifies detailed subsection structure for Chapters 5 and 6 (Experiments, Discussion) including specific analyses (e.g., "ZvT, ZvP, TvP, mirrors" at line 293, "SHAP values or permutation importance" at line 285). Phase 01 has completed exactly 1 step out of at least 6 Pipeline Sections. No data profiling, no cleaning, no EDA has been done.

**What an examiner would ask:** "Section 5.1.4 says you will do per-matchup analysis for ZvT, ZvP, TvP, and mirrors. What if your data quality assessment in Phase 01 reveals that mirror matchups have too few games for meaningful analysis? Would you remove that subsection, or force a result anyway?"

**Risk:** The thesis structure creates implicit commitments. When Phase 01 reveals data limitations, the team must either update the 444-line structure file (which has downstream references in WRITING_STATUS.md, notebook thesis_mapping fields, and REVIEW_QUEUE.md) or leave the structure aspirational and ignore the mismatch.

**Recommendation [NOTE]:** This is a design choice, not a bug. Consider adding a revision date and a note at the top: "This structure is aspirational and will be revised as phases complete. Chapters 5-7 subsection detail is provisional."

### Finding 4.3 -- WRITING_STATUS.md has 39 entries, 35 BLOCKED

**Evidence:** WRITING_STATUS.md contains entries for every thesis subsection. 35 of 39 entries are BLOCKED, 4 are SKELETON. None are DRAFTABLE, DRAFTED, REVISED, or FINAL.

**Risk:** The file is well-designed for tracking but gives an illusion of completeness when it is a wishlist. It takes up 115 lines of context for the information "nothing is writable yet."

**Recommendation [NOTE]:** Consider suppressing BLOCKED entries until the feeding phase reaches in_progress, expanding them lazily. This saves ~100 lines of context per session while preserving tracking fidelity once sections become actionable.

---

## 5. CROSS-GAME COMPARABILITY

### Finding 5.1 -- AoE2 dataset strategy not yet formalized

**Evidence:** `_current_plan.md` Step 2 proposes that aoe2companion is PRIMARY and aoestats is SUPPLEMENTARY VALIDATION. This decision is queued but not executed. Currently, both AoE2 datasets have identical ROADMAP structures and PHASE_STATUS.yaml files both showing `in_progress` for Phase 01 -- implying equal treatment.

**Risk:** Without the formalized strategy, an executor working on AoE2 Phase 01 may invest equal effort in both datasets, potentially wasting 50% of AoE2 effort.

**Recommendation [BLOCKER]:** Execute `_current_plan.md` Step 2 before further AoE2 Phase 01 work.

### Finding 5.2 -- Artifact directory naming convention drift

**Evidence:** `docs/TAXONOMY.md` defines the mirroring rule with slug-named directories:
```
sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_source_inventory.py
-> artifacts/01_exploration/01_acquisition/
```

The actual artifact directories on disk use numeric-only names:
```
artifacts/01_01/01_01_01_file_inventory.json
```

The notebook code creates `ARTIFACTS_DIR = get_reports_dir("sc2", "sc2egset") / "artifacts" / "01_01"`, which produces the numeric-only path. The ROADMAP step definition also specifies `"artifacts/01_01/01_01_01_file_inventory.json"`.

**Root cause:** TAXONOMY.md was written with the slug-directory convention. The notebook template was written (or revised) with the numeric-only convention. The template won because it is what executors actually use.

**Risk:** An auditor comparing TAXONOMY.md to the filesystem will see a contradiction. If a future executor reads TAXONOMY.md and creates `artifacts/01_exploration/01_acquisition/`, the artifacts will be in a non-standard location that breaks step gate checks.

**Recommendation [WARNING]:** Update TAXONOMY.md mirroring rule to match the implemented convention (numeric-only artifact paths). Code and ROADMAP agree; TAXONOMY.md should yield.

---

## 6. TOKEN ECONOMY ANALYSIS

### What Claude must read at session start

For a typical Category A (Phase work) session on the SC2 sc2egset dataset:

| File | Bytes | ~Tokens | Required? |
|------|-------|---------|-----------|
| CLAUDE.md (auto-loaded) | 7,932 | ~2,000 | Always |
| ARCHITECTURE.md | 9,578 | ~2,400 | Always |
| scientific-invariants.md | 5,633 | ~1,400 | Always (mandatory) |
| PHASE_STATUS.yaml | 869 | ~220 | Always (mandatory) |
| ROADMAP.md (sc2egset) | 6,622 | ~1,650 | Always (mandatory) |
| dev-constraints.md | 1,795 | ~450 | Always |
| ml-protocol.md | 3,583 | ~900 | Phase 04+ only |
| docs/PHASES.md | 11,110 | ~2,780 | Usually |
| docs/INDEX.md | 3,773 | ~940 | Usually |
| docs/TAXONOMY.md | 9,943 | ~2,490 | Rarely needed |
| reports/research_log.md | 5,313 | ~1,330 | Always (mandatory) |
| **Subtotal: essential reads** | **~66K** | **~16,600** | |

### Rule files (auto-loaded based on path patterns):

| File | Bytes | ~Tokens | Triggered by |
|------|-------|---------|-------------|
| python-code.md | 2,961 | ~740 | Any .py edit |
| sql-data.md | 1,344 | ~340 | src/*/data/**/*.py edit |
| thesis-writing.md | 3,580 | ~900 | thesis/** touch |
| git-workflow.md | 2,917 | ~730 | CHANGELOG/pyproject touch |

### Agent system prompts (loaded when agent is invoked):

| Agent | Bytes | ~Tokens |
|-------|-------|---------|
| reviewer-adversarial | 13,237 | ~3,300 |
| reviewer-deep | 16,081 | ~4,000 |
| executor | 6,947 | ~1,740 |
| planner-science | 4,045 | ~1,010 |
| writer-thesis | 2,674 | ~670 |
| reviewer | 4,475 | ~1,120 |
| planner | 1,351 | ~340 |
| lookup | 623 | ~160 |

### Methodology manuals (one loaded per active phase):

| Manual | Bytes | ~Tokens |
|--------|-------|---------|
| 01_DATA_EXPLORATION | 35,254 | ~8,800 |
| 02_FEATURE_ENGINEERING | 40,505 | ~10,100 |
| 03_SPLITTING_AND_BASELINES | 29,095 | ~7,270 |
| 04_MODEL_TRAINING | 28,939 | ~7,230 |
| 05_EVALUATION_AND_ANALYSIS | 27,993 | ~7,000 |
| 06_CROSS_DOMAIN_TRANSFER | 23,001 | ~5,750 |

### Templates (loaded when creating notebooks):

| Template | Bytes | ~Tokens |
|----------|-------|---------|
| notebook_template.yaml | 20,902 | ~5,230 |
| raw_data_readme_template.yaml | 27,668 | ~6,920 |
| step_template.yaml | 4,895 | ~1,220 |

### Total context cost for a full Category A session:

- Essential reads: ~16,600 tokens
- Active methodology manual (Phase 01): ~8,800 tokens
- Agent prompt (executor): ~1,740 tokens
- Rule files (python-code on .py edit): ~740 tokens
- Notebook template (if creating): ~5,230 tokens
- **Total: ~33,000 tokens minimum before any actual work**

This is manageable for Opus 1M context but represents ~16% of a 200K Sonnet context.

### Finding 6.1 -- Redundancy between CLAUDE.md, ARCHITECTURE.md, and docs/

**Evidence:** CLAUDE.md (152 lines) duplicates several items from ARCHITECTURE.md (173 lines):
- Key file locations table in CLAUDE.md vs. Cross-cutting files table in ARCHITECTURE.md
- Progress tracking section in CLAUDE.md vs. Progress tracking section in ARCHITECTURE.md
- Phase Work Execution in CLAUDE.md vs. sandbox/README.md (and ARCHITECTURE.md)
- Agent table in CLAUDE.md vs. the full AGENT_MANUAL.md

The CLAUDE.md version is a summary, ARCHITECTURE.md is the full version. But both are always loaded. The CLAUDE.md summary doesn't save tokens if ARCHITECTURE.md is also read.

**Recommendation [NOTE]:** CLAUDE.md should be the only auto-loaded file and should contain pointers to everything else, not summaries. Currently it is 152 lines of mixed summary + pointers. If it were pure pointers, it would save ~80 lines of redundant context. ARCHITECTURE.md should be on-demand, not always-read.

### Finding 6.2 -- docs/TAXONOMY.md is 241 lines and rarely needed

**Evidence:** TAXONOMY.md defines what "Phase", "Pipeline Section", "Step", "Spec", "PR", "Category", and "Session" mean. These are stable terms. The file is 9,943 bytes (~2,490 tokens). It is referenced frequently but rarely needs to be read in full.

**Recommendation [NOTE]:** Make TAXONOMY.md reference-only (not auto-read). An agent that needs to know what a "Step" is can read it on demand. At 2,490 tokens per session over dozens of sessions, this adds up.

### Finding 6.3 -- raw_data_readme_template.yaml is 748 lines / 27.7 KB

**Evidence:** The template has 389 lines of examples (Section Z) that double the file size. The examples are useful exactly once per dataset.

**Recommendation [NOTE]:** Split Section Z (examples appendix) into a separate file or fold it behind an explicit "read examples only if creating a new raw README" note.

---

## 7. DRIFT PREVENTION vs. FLEXIBILITY

### Load-bearing constraints (keep as-is):

1. **Scientific invariants #1-#8** -- prevent methodology errors that would fail the thesis defense. Every word is load-bearing.
2. **Source-of-truth hierarchy** (ARCHITECTURE.md) -- the single most valuable architectural artifact. Without it, conflicting files create silent confusion.
3. **Notebook template hard rules** (no inline defs, cell cap, read-only DuckDB, both files committed) -- enforced by pre-commit hooks, prevent common notebook anti-patterns.
4. **Per-dataset PHASE_STATUS.yaml** -- lightweight (~35 lines), machine-readable, answers "which phase are we in?" instantly.

### Speculative constraints (creating false confidence or premature lock-in):

1. **Phase 02-07 Pipeline Section lists in each ROADMAP** -- copy-pasted from docs/PHASES.md into every dataset ROADMAP. If a Pipeline Section is renamed in PHASES.md, all 4 ROADMAPs must be updated. Since Phases 02-07 have no Steps defined yet, they add no information beyond what PHASES.md already provides.

   **Recommendation [NOTE]:** Consider whether placeholder Phase sections should be a one-line pointer to PHASES.md rather than a full copy of the section list. Reduces ROADMAP length by ~60 lines per dataset and eliminates a drift surface.

2. **THESIS_STRUCTURE.md subsection detail for Chapters 5-7** -- locks in experimental design decisions before data exploration is complete.

3. **Phase 06 with 9 Pipeline Sections** -- the most aggressive speculation. The `_current_plan.md` Step 5 already proposes reducing to 3 required + 6 stretch sections. But until executed, the full 9-section plan sits in docs/PHASES.md as if settled.

### Missing drift prevention:

1. **No automated consistency check between ROADMAP thesis_mapping fields and THESIS_STRUCTURE.md.** The Chapter 3 vs. 4 error survived multiple sessions because nothing validates that the referenced chapter actually exists. A simple grep-based pre-commit check would catch this.

2. **No staleness detection for PHASE_STATUS.yaml.** The file says "If this file disagrees with the ROADMAP, this file is wrong." But nothing detects the disagreement. If a step is completed but PHASE_STATUS.yaml is not updated, the next session starts with stale state.

---

## 8. TEMPLATE ENFORCEMENT ANALYSIS

### Template: `step_template.yaml` (160 lines)
- **Enforcement:** Documentation + reviewer discipline (Tier 1). The planner-science agent uses this schema when defining steps.
- **Actual compliance:** The one defined step (01_01_01) conforms. But conformance is manual -- no validator exists.
- **Gap:** A malformed step definition (e.g., missing gate conditions) would not be caught until a reviewer reads the ROADMAP.
- **Recommendation [P2]:** A lightweight YAML schema validator would provide Tier 2 enforcement cheaply.

### Template: `notebook_template.yaml` (517 lines)
- **Enforcement:** Documentation + reviewer discipline (Tier 1). Pre-commit hooks cover jupytext sync but not cell structure.
- **Actual compliance:** The existing 01_01_01 notebook conforms well.
- **Gap:** The template is 517 lines. An executor creating a notebook must read and follow all of it. There is no skeleton generator.
- **Recommendation [P1]:** Build a `create_notebook(step_number, dataset)` CLI command that generates a conforming skeleton from the template + ROADMAP step definition. This would make Tier 1 enforcement near-automatic.

### Template: `raw_data_readme_template.yaml` (748 lines)
- **Enforcement:** Documentation only. No validator, no hook, no generator.
- **Actual compliance:** Unknown -- no raw README has been written using this template yet.
- **Recommendation [P2]:** Add a `validate_raw_readme(path)` function or wait until first use to evaluate.

### Missing templates:
- **Research log entry template.** The format is described in ml-protocol.md with structured fields (Objective, Approach, Issues encountered, Resolution/Outcome, Thesis notes). The actual research log entry (2026-04-09) uses different field names (What, Why, How, Findings, Decisions taken, Decisions deferred, Thesis mapping, Open questions). The format has drifted from the specification.
  - **Recommendation [P1]:** Either update ml-protocol.md to match the actual format, or add a template and make the executor use it.

---

## 9. PHASE_STATUS.yaml AND ROADMAP.md INTERACTION

### Finding 9.1 -- Redundancy is intentional and acceptable

PHASE_STATUS.yaml is a 35-line derivative of the ROADMAP. The ROADMAP for sc2egset is 182 lines. The PHASE_STATUS exists so agents can determine the current phase without parsing the full ROADMAP. This is a good design pattern -- analogous to a database index.

### Finding 9.2 -- No mechanism to detect PHASE_STATUS drift from ROADMAP

**Evidence:** PHASE_STATUS.yaml says "If this file disagrees with the ROADMAP, this file is wrong -- regenerate from the ROADMAP." But there is no tool to regenerate it and no check to detect drift.

**Scenario:** When Phase 01 is complete, someone must manually change it to "complete." If they forget, the next session still thinks Phase 01 is in_progress, and Phase 02 work cannot begin.

**Recommendation [P2]:** Add a `validate_phase_status` command that reads the ROADMAP, checks for step gate artifacts on disk, and reports whether the PHASE_STATUS.yaml is stale.

---

## 10. EXAMINER'S QUESTIONS

Questions an examiner would ask at the thesis defense, based on what the architecture reveals:

1. **"You have 6 methodology manuals totaling ~185 KB. Did you write these before or after your experiments? If before, how did you know they would be applicable?"**
   - The manuals cite academic references and describe methods abstractly. This is fine -- but an examiner will want to know they were updated based on experimental reality, not treated as sacred text.

2. **"Your Phase 06 has 9 Pipeline Sections for cross-domain transfer. You have two games, one with rich replay data and one with only match metadata. What exactly are you transferring?"**
   - The `_current_plan.md` Step 5 already acknowledges this is over-scoped. But until executed, the full 9-section plan sits in docs/PHASES.md as if settled.

3. **"You claim your contribution is a cross-game comparison framework. But your SC2 dataset has ~22K curated esports replays, and your AoE2 dataset has ~277M matches from all skill levels. How is that a fair comparison?"**
   - The scale asymmetry is enormous. SC2: professional-only curated replays. AoE2: all skill levels from a CDN dump. This is not just a data asymmetry -- it is a population asymmetry. Must be addressed explicitly in Chapter 6.5 as a threat to validity.

---

## CONCRETE RECOMMENDATIONS (Prioritized)

### P0 -- Do now (blocks current work)
1. Execute `_current_plan.md` Steps 1-2 (chapter numbering fix, AoE2 dataset strategy). These are identified blockers.
2. Execute `_current_plan.md` Step 3 (Friedman N=2 fix in Invariant #8). The invariant is the highest-precedence file and is read at every session start.

### P1 -- Do soon (prevents drift)
3. Update `common/CONTRACT.md`: change "Invariant #10" to "Invariant #8."
4. Update TAXONOMY.md mirroring rule to match the implemented artifact path convention (`artifacts/01_01/` not `artifacts/01_exploration/01_acquisition/`).
5. Add normalization leakage to Invariant #3 or ml-protocol.md.
6. Reconcile research log entry format (ml-protocol.md vs. actual usage).
7. Remove the Phase 04 activation gate from ml-protocol.md, or extract the three leakage failure modes into scientific-invariants.md.
8. Build a `create_notebook` CLI tool that generates conforming notebook skeletons from templates + ROADMAP step definitions.

### P2 -- Do eventually (reduces friction)
9. Reduce CLAUDE.md from summary+pointers to pointers-only. Make ARCHITECTURE.md on-demand.
10. Replace placeholder Phase 02-07 Pipeline Section lists in ROADMAPs with one-line pointers to PHASES.md.
11. Add a `validate_phase_status` CLI command.
12. Split raw_data_readme_template.yaml Section Z (examples) into a separate file.
13. Mark THESIS_STRUCTURE.md Chapters 5-7 subsection detail as "provisional -- will be revised after Phase 03."
14. Add a consistency check (grep-based) between ROADMAP thesis_mapping fields and THESIS_STRUCTURE.md chapter headings.

---

## WEAKEST LINK

The Friedman N=2 error in Invariant #8. The invariant file is the highest-precedence document in the entire repository and is read at every session start. It currently prescribes a statistical test that the thesis itself has identified as inappropriate for its experimental design. Until `_current_plan.md` Step 3 is executed, every session starts with incorrect statistical methodology guidance.

**Verdict: REVISE** -- execute `_current_plan.md` Steps 1-3 before further Phase work.

---

## Sources

- Demsar, J. (2006). Statistical Comparisons of Classifiers over Multiple Data Sets. JMLR, 7, 1-30.
- de Prado, M. L. (2018). Advances in Financial Machine Learning. Wiley. Ch. 7 (Cross-Validation in Finance).
- Arlot, S., & Celisse, A. (2010). A Survey of Cross-Validation Procedures for Model Selection. Statistics Surveys, 4, 40-79.
- Benavoli, A., et al. (2017). Time for a Change: a Tutorial for Comparing Multiple Classifiers Through Bayesian Analysis. JMLR, 18(77), 1-36.
- [Spec-Driven Development with AI -- GitHub Blog](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)
- [How to Write a Good Spec for AI Agents -- Addy Osmani](https://addyosmani.com/blog/good-spec/)
