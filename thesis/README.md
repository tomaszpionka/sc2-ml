# Thesis

This directory contains all thesis writing artifacts.

## Key Files

| Path | Purpose |
|------|---------|
| `THESIS_STRUCTURE.md` | Chapter outline, section plan, and overall document structure |
| `WRITING_STATUS.md` | Tracks draft/revision status per chapter; updated after every Category F session |
| `chapters/` | LaTeX (or Markdown) source for each chapter |
| `figures/` | Figures referenced in the thesis; generated outputs from notebooks |
| `tables/` | Standalone table files referenced in the thesis |
| `references.bib` | BibTeX bibliography |

## Category F Workflow

All thesis writing follows the Category F workflow:

1. Read `.claude/scientific-invariants.md` and the active `PHASE_STATUS.yaml` before drafting.
2. Run the Critical Review Checklist from `.claude/rules/thesis-writing.md`.
3. Plant `[REVIEW:]` flags for any claim that needs a second pass.
4. After each session, update `WRITING_STATUS.md` and `chapters/REVIEW_QUEUE.md`.
5. Do NOT assert quantitative findings that are not backed by a report artifact — halt and report the gap instead.
