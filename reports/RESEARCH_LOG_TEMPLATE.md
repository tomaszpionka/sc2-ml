> **Canonical schema:** `docs/templates/research_log_entry_template.yaml`
> This markdown version is a human-readable rendering. The YAML template
> is the authoritative field list.

# Research log entry template

Copy this block to the top of `reports/research_log.md` for every new
entry. Required for Category A (science) work, recommended for Category
F (writing) sessions.

## YYYY-MM-DD — [Phase XX / Step XX_YY_ZZ] Short descriptive title

**Category:** A (science) | F (writing) | C (chore)
**Dataset:** sc2egset | aoestats | aoe2companion | —
**Artifacts produced:** `path/to/file1.csv`, `path/to/file2.md`

### What
One paragraph. What did you do, concretely. No why yet. Just actions.

### Why
One paragraph. What question were you trying to answer. Which Manual
section or Scientific Invariant motivated it. What was the hypothesis
or the specific uncertainty you were trying to reduce.

### How (reproducibility)
The literal SQL or Python that produced the core result. Per Scientific
Invariant: a finding without its derivation cannot be cited in the thesis.
If the code is more than ~30 lines, link to the committed file and quote
the key block inline.

### Findings
Bullet list of factual observations. Numbers with units. No interpretation.

### What this means
Two or three sentences of interpretation. How does this change what we
think about the dataset? What assumption did it confirm or break?

### Decisions taken
- Decision 1 (if any) + one-sentence rationale
- Decision 2 (if any)
- "None — observation only" is a valid entry.

### Decisions deferred
What this finding implies we will need to decide later, and at which
phase/step that decision will be made. This is the section that becomes
the methodology chapter's "we chose X because of Y observed in Z" later.

### Thesis mapping
Target section(s) in `thesis/THESIS_STRUCTURE.md` that this entry feeds.

### Open questions / follow-ups
Anything surprising, anything that did not make sense, anything worth
returning to. Do not self-censor.
