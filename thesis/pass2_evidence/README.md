# Pass-2 evidence

This directory holds durable evidence artifacts produced during thesis drafting
(Pass 1) that are cited by `thesis/chapters/REVIEW_QUEUE.md` or that future
Pass-2 reviewers in Claude Chat must be able to inspect.

Contents live here (rather than under `temp/`) when a downstream process or a
queue entry references them as audit evidence — losing them would weaken
defensibility of a drafted section.

## Index

| File | Produced | Cited by | Purpose |
|------|---------|----------|---------|
| `sec_4_1_crosswalk.md` | 2026-04-17 | REVIEW_QUEUE.md §4.1.1 / §4.1.2 / §4.1.3 | Numerical crosswalk: every number in §4.1 prose traces to a Phase 01 artifact line (8-column schema) |
| `sec_4_1_halt_log.md` | 2026-04-17 | §4.1 drafting audit trail | Halt-protocol log for §4.1 execution — attests zero halt events during T03–T06b |
| `sec_4_2_crosswalk.md` | 2026-04-18 | REVIEW_QUEUE.md §4.2.1 / §4.2.2 / §4.2.3 | Numerical crosswalk for §4.2 (78 rows: 48 main + 10 identity-check + 16 scope-overlap with §4.1 + 4 classification of new bib entries) |
| `sec_4_2_halt_log.md` | 2026-04-18 | §4.2 drafting audit trail | Halt-protocol log for §4.2 execution — attests zero halt events during T01–T04 |

## Conventions

- File names use `sec_<section_id>_<artifact_type>.md` pattern for traceability.
- Each artifact must be cited from at least one thesis chapter or tracking file;
  uncited artifacts should be either cited or removed.
- Contents are frozen at Pass-2 handoff time. If a section is re-drafted, add a
  new `sec_<id>_vN_<type>.md` rather than overwriting.
