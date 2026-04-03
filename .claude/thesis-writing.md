# Thesis Writing Standards

**Read this file before any Category F (thesis writing) work.**

This file governs how thesis chapters are drafted, revised, and tracked.
It complements the coding/data workflow — writing is a first-class deliverable,
not an afterthought.

---

## Core principle: write when context is fresh

Each thesis section is drafted **immediately after the roadmap phase that feeds it
completes**, not months later from memory. The research log entry provides raw
material; the thesis section reshapes it into a reader-facing narrative.

The mapping from phases to thesis sections is defined in `thesis/THESIS_STRUCTURE.md`.
The current status of every section is tracked in `thesis/WRITING_STATUS.md`.

---

## Directory structure

```
thesis/
  THESIS_STRUCTURE.md      ← Chapter plan with section descriptions (read-only reference)
  WRITING_STATUS.md        ← Tracks draft status of every section (update after every write)
  chapters/
    01_introduction.md
    02_theoretical_background.md
    03_related_work.md
    04_data_and_methodology.md
    05_experiments_and_results.md
    06_discussion.md
    07_conclusions.md
  figures/                 ← Publication-quality versions of report PNGs
  tables/                  ← Formatted tables derived from report CSVs
  references.bib           ← BibTeX file, updated as citations are added
```

Chapter files use Markdown. Final typesetting (LaTeX, Word, or whatever the
university requires) happens later — content quality comes first. Each chapter
file contains all sections for that chapter, separated by `## Section` headers
matching `THESIS_STRUCTURE.md`.

---

## WRITING_STATUS.md semantics

Every section has exactly one status:

| Status | Meaning |
|--------|---------|
| `SKELETON` | Section header exists with a brief note on what goes here. No prose. |
| `BLOCKED` | Cannot be written yet — the feeding phase is incomplete. |
| `DRAFTABLE` | The feeding phase is complete. This section can be drafted now. |
| `DRAFTED` | First draft exists. May need revision after later phases. |
| `REVISED` | Updated after a later phase provided new context. |
| `FINAL` | Content-complete, reviewed, ready for typesetting. |

**After completing any roadmap phase**, update WRITING_STATUS.md:
- Move the fed sections from `BLOCKED` → `DRAFTABLE`
- If a drafted section needs revision due to new findings, note it

**After drafting or revising a section**, update WRITING_STATUS.md:
- Move the section to `DRAFTED` or `REVISED`
- Record the date

---

## Writing quality standards

Thesis prose is not a research log entry and not code documentation. It must
meet the following standards:

### Voice and register
- Third person or first person plural ("we") — follow university guidelines
- Academic register: precise, concise, no colloquialisms
- Present tense for established facts ("The SC2 engine runs at 22.4 loops/s")
- Past tense for actions taken ("We filtered games shorter than 7 minutes")

### Structure per section
Every substantial section should follow this pattern:
1. **Context sentence** — what this section covers and why it matters
2. **Method** — what was done (briefly — point to appendix for code)
3. **Findings** — results, with reference to tables/figures
4. **Implication** — what this means for downstream phases or the thesis argument

### Figures and tables
- Every figure and table in the thesis must have a caption and a number
- Reference figures/tables from report artifacts: `reports/01_duration_distribution_full.png`
  → `thesis/figures/fig_4_1_duration_distribution.png` (renamed for thesis numbering)
- Do not recreate analyses — reformat existing report artifacts for print quality
- All figures must be reproducible from the code in the repository

### Citations
- Use BibTeX keys in square brackets: `[Bialecki2023]`, `[Vinyals2017]`
- Add every new citation to `thesis/references.bib`
- Prefer primary sources (the original paper) over secondary summaries
- Every numerical claim from external work needs a citation

### Relationship to research_log.md
- The research log is the *lab notebook* — chronological, detailed, code-heavy
- The thesis chapter is the *publication* — thematic, reader-oriented, narrative
- Do not copy-paste from the research log into the thesis. Rewrite for audience.
- The research log entry is cited implicitly (it's in the same repo) — the thesis
  text should be self-contained without requiring the reader to read the log

---

## How to draft a section (step by step)

1. Read the relevant phase entry in `reports/research_log.md`
2. Read the report artifacts that feed this section (CSVs, PNGs, MDs in `reports/`)
3. Read the section description in `thesis/THESIS_STRUCTURE.md`
4. Write the section in the appropriate `thesis/chapters/XX_*.md` file
5. Add any new figures to `thesis/figures/` (renamed with thesis numbering)
6. Add any new BibTeX entries to `thesis/references.bib`
7. Update `thesis/WRITING_STATUS.md`

---

## Critical review checklist (MANDATORY before marking DRAFTED)
 
After writing any section draft, Claude Code must run through this checklist
before the section can move to `DRAFTED` status. This is not optional — a
draft that skips this checklist is incomplete.
 
### 1. Numerical consistency
 
For every number, percentage, count, or statistic stated in the prose:
- Trace it back to a specific report artifact (CSV, JSON, or MD in `reports/`)
- Verify the number matches exactly — not approximately, not rounded differently
- If the number cannot be traced to an artifact, it must either be removed,
  computed now (with code), or flagged as `[UNVERIFIED: source?]`
 
Example failure: The thesis says "APM is available for 98% of player slots."
The report says 97.5%. This is wrong and must be corrected.
 
### 2. Claim-evidence alignment
 
For every interpretive claim (e.g., "MMR is systematically missing due to
tournament organiser practices"), verify:
- The evidence cited actually supports this specific interpretation
- Alternative explanations have been considered (even if dismissed)
- The claim does not overstate the evidence — "consistent with" is safer
  than "proves" or "demonstrates"
 
Flag any claim where the evidence is suggestive but not conclusive with
hedging language: "This pattern is consistent with...", "One plausible
explanation is...", "The data suggest..."
 
### 3. Derivation traceability
 
For every threshold, parameter, or methodological choice stated in the thesis:
- Verify it has a traceable justification (empirical from the data, or cited
  from the literature) per Scientific Invariant #9
- If the justification is empirical, point to the specific Phase finding
- If the justification is from literature, verify the citation exists in
  `thesis/references.bib` and the cited paper actually says what is claimed
 
Flag any unjustified constant with `[NEEDS JUSTIFICATION]`.
 
### 4. Statistical interpretation
 
For any statistical result (p-value, Cohen's d, confidence interval, etc.):
- Verify the interpretation is correct (e.g., a non-significant p-value does
  not mean "no effect" — it means "insufficient evidence to reject H0")
- Verify effect sizes are interpreted alongside significance (a tiny Cohen's d
  with p < 0.001 from a huge sample is statistically significant but practically
  meaningless — say so)
- Verify any multiple comparison corrections are noted (Bonferroni, etc.)
 
### 5. Scope honesty
 
For every finding, verify the text does not:
- Generalise beyond the dataset (e.g., claiming something about "all SC2
  tournaments" when we have 70+ specific tournaments from 2016–2024)
- Imply causation from correlation
- Present a data limitation as a non-issue (if 2016 APM data is all zeros,
  that IS a limitation — acknowledge it, don't minimise it)
 
### 6. Missing context flags
 
For any area where Claude Code suspects the thesis draft might be:
- Inconsistent with standard practice in the field
- Making an unusual methodological choice without sufficient justification
- Missing a comparison to a known benchmark or result
 
Insert an inline flag: `[REVIEW: <specific concern>]`
 
These flags are addressed in Pass 2 (Claude Chat review), not by Claude Code
itself, because resolving them requires literature knowledge and web search.
 
---
 
## Two-pass writing workflow
 
Thesis section writing follows a mandatory two-pass process:
 
### Pass 1 — Draft + internal validation (Claude Code, Category F session)
 
1. Draft the section using research log entries and report artifacts
2. Run the Critical Review Checklist above
3. Insert `[REVIEW: ...]` flags for anything requiring external validation
4. Mark section as `DRAFTED` in WRITING_STATUS.md
5. List all `[REVIEW: ...]` flags in the session summary
 
### Pass 2 — External validation (Claude Chat, with web search)
 
The user brings the drafted section to Claude Chat (this interface) and asks
for a critical review. Claude Chat can:
- Validate interpretations against published literature (via web search)
- Check whether methodology aligns with field norms
- Resolve `[REVIEW: ...]` flags
- Identify missing citations or comparisons
- Catch claims that contradict established results
- Suggest stronger or more precise phrasings
 
After Pass 2, the user applies corrections and the section moves to `REVISED`
in WRITING_STATUS.md.
 
### Why two passes?
 
Claude Code has the codebase and can verify internal consistency, but has no
internet access and limited ability to assess scientific novelty or field norms.
Claude Chat has web search and broad knowledge, but cannot run code or verify
numbers against report artifacts. The two-pass workflow uses each tool's
strengths and compensates for each tool's weaknesses.
 
---
 
## Inline flag format
 
Use this exact format so flags are searchable across all chapter files:
 
```
[REVIEW: Is 7 minutes a defensible minimum duration threshold? Wu et al. 2017
used this but our distribution may suggest a different cutoff.]
```
 
```
[UNVERIFIED: source?] — for numbers that could not be traced to an artifact
```
 
```
[NEEDS JUSTIFICATION] — for thresholds or parameters without derivation
```
 
```
[NEEDS CITATION] — for claims that require a literature reference
```
 
After Pass 2 review, all flags must be resolved. A section with unresolved
flags cannot move to `FINAL` status.

---

## What to write at each project stage

### After Phase 0 (ingestion audit)
- §4.1.1 first draft: corpus size, pipeline architecture, APM/MMR findings

### After Phase 1 (corpus inventory)
- §4.1.1 revision: duration distribution, parse quality, patch landscape
- §2.2 skeleton: SC2 mechanics, game loop timing (now sourced)

### After Phase 2 (player identity)
- §4.2.2 first draft: toon fragmentation, canonical ID design, coverage stats

### After Phase 3 (games table)
- §4.2 expansion: temporal structure, sliding window feasibility

### After Phase 4 (in-game profiling)
- §4.3.2 first draft: PlayerStats fields, separability analysis, unit taxonomy

### After Phase 5 (meta-game analysis)
- §4.3.1 control features section
- §5.1 context paragraphs on matchup and map confounds

### After Phase 6 (cleaning)
- §4.2.3 first draft: cleaning rules with justifications, impact report

### After Phase 7 (feature engineering)
- §4.3 completion: full feature specification, rating system description

### After Phase 8 (split)
- §4.4 first draft: split strategy, validation, comparison with naïve split

### After Phase 9 (baselines)
- §5.1.1 first draft: baseline results table

### After Phase 10 (models)
- §5.1.2–5.1.4 first draft: model results, ablation, per-matchup, cold-start
- §6 first draft: interpretation, comparison with literature
- §7 first draft: conclusions

### Cross-cutting (write anytime)
- §1 Introduction — can be drafted at any point, revised at the end
- §2 Theoretical background — write as you read the literature
- §3 Related work — write as you read papers; revise after experiments

---

## Plan template for Category F sessions

When planning a thesis writing session, the plan must include:

- Section(s) to draft or revise, with exact `thesis/chapters/` file paths
- Which research log entries and report artifacts feed the section
- Whether this is a first draft or a revision (and what triggered the revision)
- Any new figures or tables to create
- Any new BibTeX entries needed
- The WRITING_STATUS.md update that marks this plan as complete
