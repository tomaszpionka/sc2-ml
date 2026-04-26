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
| `dependency_lineage_audit.md` | 2026-04-26 | audit_cleanup_summary.md; claim_evidence_matrix.md | Full claim-lineage audit for Chapters 1–4: 182 claims, 11-column schema; stale Step count = 0; escape-valve NOT fired |
| `claim_evidence_matrix.md` | 2026-04-26 | REVIEW_QUEUE.md; dependency_lineage_audit.md | Global cross-chapter claim-evidence index (Option B SUPPLEMENT): Chapters 1–3 fully covered; Chapter 4 points to v1 crosswalks for §4.1/§4.2 and to dependency_lineage_audit.md for 10 post-crosswalk claims |
| `notebook_regeneration_manifest.md` | 2026-04-26 | dependency_lineage_audit.md | Per-notebook status for all Phase 01 notebooks across sc2egset/aoestats/aoe2companion: 85 confirmed_intact, 7 not_yet_assessed, 0 flagged_stale |
| `audit_cleanup_summary.md` | 2026-04-26 | T01 preflight + T02 critique gate | Preflight and critique gate closure records; tracks escape-valve and T03–T06 gate decisions |

## Relationship between v1 Chapter 4 crosswalks and the global claim-evidence matrix

The v1 crosswalks (`sec_4_1_crosswalk.md`, `sec_4_2_crosswalk.md`) are the
**primary** audit evidence for all §4.1 and §4.2 numerical claims. They are frozen
at their 2026-04-17/18 creation dates and must not be modified in place.

`claim_evidence_matrix.md` is the global index that covers Chapters 1–3 directly
and **delegates** to the v1 crosswalks for Chapter 4 §4.1/§4.2 claims rather than
duplicating them (Option B SUPPLEMENT strategy). For the 10 post-crosswalk Chapter 4
claims (§4.4.4–§4.4.6, §4.1.3 F5.4 paragraph, §4.1.4) that were drafted after the
v1 crosswalk creation date, `claim_evidence_matrix.md` points to the individual
audit rows in `dependency_lineage_audit.md`.

If future re-drafting requires new Chapter 4 crosswalk entries:
- Create `sec_4_1_v2_crosswalk.md` or `sec_4_2_v2_crosswalk.md` — do NOT edit v1 files.
- Update `claim_evidence_matrix.md` to point to the v2 file for the affected rows.
- Add a corresponding index row to this README.

## Conventions

- File names use `sec_<section_id>_<artifact_type>.md` pattern for traceability.
- Each artifact must be cited from at least one thesis chapter or tracking file;
  uncited artifacts should be either cited or removed.
- Contents are frozen at Pass-2 handoff time. If a section is re-drafted, add a
  new `sec_<id>_vN_<type>.md` rather than overwriting.
