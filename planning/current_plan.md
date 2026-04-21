---
category: C
branch: chore/aoestats-43-day-gap-provenance
date: 2026-04-21
planner_model: claude-opus-4-7
dataset: aoestats
phase: null
pipeline_section: null
invariants_touched: []
source_artifacts:
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md
  - sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md
  - reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md
  - thesis/chapters/04_data_and_methodology.md
  - thesis/pass2_evidence/sec_4_1_crosswalk.md
critique_required: true
research_log_ref: null
---

# Plan: WP-5 — aoestats "43-day post-patch gap" provenance citation-hardening chore (REVISED 2026-04-21 post Mode A)

## Scope

Close aoestats Phase 01 audit NOTE 2 ("43-day post-patch gap figure no artifact provenance" per `reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md §3 + closure table row`) as a citation-hardening chore. Grep-based scope decision (2026-04-21):

- **Thesis hit at `thesis/chapters/04_data_and_methodology.md:85`** — §4.1.2 aoestats narrative makes both a factual claim (43-day gap at 2024-07-20 → 2024-09-01) AND an interpretive claim (post-patch API schema correlation). The interpretive claim is already flagged inline `[REVIEW: ...]`.
- **Figure provenance at `01_01_01_file_inventory.md:29 + :38`** — derived from filename date-range inventory (`{date}_{date}_matches.parquet` pattern scan; gap = calendar days between filename-anchored window edges). Already committed.
- **Derivation logic at `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py`** — the filename-scanning notebook that produced the figure. The `.md` artifact documents the resulting numbers; the `.py` notebook documents the derivation.
- **Thesis pass-2 crosswalk at `thesis/pass2_evidence/sec_4_1_crosswalk.md:81`** — ALREADY cites `01_01_01_file_inventory.md` as the anchor.

Retract variant does NOT apply: thesis depends on the figure. Full-derivation variant (new Cat A notebook + artifact) is redundant: the derivation already exists across the `.md` (output) + `.py` (logic) pair. **Correct task: citation-hardening.** Update the audit summary to point at the existing two-part provenance; add an inline anchor in INVARIANTS.md §3 Temporal invariants adjacent to the coverage bullet; spot-check crosswalk consistency.

Scope: 4 git-diff-scope files. No new notebook. No new empirical work. No thesis-chapter writes.

**Post-Mode-A revision summary (2026-04-21):** Mode A surfaced 1 BLOCKER + 2 WARNINGs + 2 NOTEs. All 5 revisions applied within symmetric 1-revision cap:
- **BLOCKER 1:** T03 target corrected from (non-existent) §1 "Temporal range" to actual §3 Temporal invariants at line 74 adjacent to the Coverage bullet. Anchor sentence tightened to 2 sentences. Date reconciliation handled (filename-scan extent vs timestamp-content extent).
- **WARNING 1:** T02 step 5 (phantom closure-stats task) struck — no top-level tally exists in the audit summary.
- **WARNING 2:** T02 step 3 + T05 CHANGELOG rewritten to neutral framing ("follow-up verification located existing provenance"), honoring the plan's own Q3 recommendation; dropped "miss"/"not a real gap" judgment-assigning prose.
- **NOTE 3:** T02 step 3 cites `01_01_01_file_inventory.py` as the derivation-logic location; `.md` documents the figure; both together constitute the provenance.
- **NOTE 4:** T03 sentence labels "filename-scan extent" vs "observed match-timestamp extent" OR omits the range dates and references only the inter-file gaps (adopted option: omit range dates; reference gaps only).

Symmetric 1-revision cap consumed.

## Problem Statement

The 2026-04-21 Phase 01 audit NOTE 2 for aoestats read: "'43-day post-patch gap' figure no artifact provenance... The figure appears in the research log without a corresponding notebook or artifact output." The concern was partially legitimate: the `.md` artifact at `01_01_01_file_inventory.md` documents the figure (line 29 matches/, line 38 players/) but does not contain the derivation SQL/Python inline — the filename-scanning logic lives in the paired `.py` notebook. The audit's concern about "no SQL query establishing its provenance" was half-right: the figure IS in a committed artifact, but the derivation is split between `.md` (output) + `.py` (logic). An examiner wanting to see "how 43 is computed from filenames" reads the `.py`.

Follow-up verification (this PR) establishes:
1. The `.md` artifact carries the figure at `01_01_01_file_inventory.md:29,38`.
2. The `.py` notebook carries the filename-scanning derivation logic (filename date-range parsing + inter-file gap computation).
3. Together they satisfy the I9 traceability requirement.

Consequences of leaving unaddressed:
- Audit summary closure table shows aoestats NOTE 2 "OPEN — SCHEDULED" pointing at WP-5 — false pendency.
- `INVARIANTS.md §3 Temporal invariants` doesn't cite the gap anchor inline; future reader must re-derive.
- Pass-2 reviewers reading thesis §4.1.2 line 85's 43-day claim may re-open "is this derivable?" question.

This PR updates the audit summary to reflect the located provenance; adds an inline anchor in INVARIANTS.md §3; spot-checks crosswalk consistency.

## Assumptions & unknowns

- **Assumption (`.md` + `.py` constitutes sufficient provenance):** Together they satisfy I9. The `.md` reports the figure; the `.py` shows the derivation. This is acceptable for a LOW-severity documentation closure; an examiner asking "where is the derivation" gets directed to the `.py`.
- **Assumption (crosswalk row 81 is correct):** Spot-check only; no rewrite expected.
- **Assumption (thesis §4.1.2 interpretive claim is adequately hedged):** The [REVIEW: ...] flag on the post-patch API-schema correlation is correctly scoped to Chat workflow. No thesis prose edit in this PR.
- **Unknown (none substantive).** Pure citation-hardening.

## Literature context

Not applicable — internal documentation chore. References:
- `.claude/scientific-invariants.md` I9 (artifact traceability; this chore closes the I9 gap for the 43-day figure by documenting its `.md` + `.py` split provenance).
- `reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md §3` + closure table — the audit entry being corrected.

## Execution Steps

### T01 — Verify anchor artifacts and line numbers

**Objective:** Confirm `01_01_01_file_inventory.md` contains the 43-day gap at the cited lines (29 matches/, 38 players/) and that the paired `.py` notebook exists at the expected path.

**Instructions:**
1. Read `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md` lines 20-50.
2. Record exact line numbers for "2024-07-20 -> 2024-09-01 (43 days)" in matches/ and players/ sections.
3. Confirm `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py` exists.
4. If the figure is absent from the `.md` or the `.py` is missing, HALT — scope changes.

**Verification:**
- Executor notes exact line numbers used in T02 and T03 edits.

**File scope:** None.
**Read scope:** `01_01_01_file_inventory.md`; sandbox `01_01_01_file_inventory.py` (existence check).

---

### T02 — Correct `phase01_audit_summary_2026-04-21.md` aoestats NOTE 2

**Objective:** Update the audit summary to reflect located provenance. **Tone: neutral framing per plan Q3; no blame-assigning prose.**

**Instructions:**
1. Edit `reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md`.
2. Locate aoestats NOTE 2 in §3 (line 64). Reword the bullet to:

   "**aoestats NOTE 2 — '43-day post-patch gap' figure provenance.** The 43-day post-patch gap (2024-07-20 → 2024-09-01) referenced in aoestats temporal analysis was flagged at initial audit as lacking artifact provenance. Follow-up verification 2026-04-21 (WP-5) located the existing provenance: the figure is documented in `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md:<matches-line>` (matches/ section) and `:<players-line>` (players/ section); the filename-scanning derivation logic resides in the paired sandbox notebook `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py`. Together the `.md` (output) + `.py` (derivation) pair constitute the I9-compliant provenance. Severity: LOW (audit-time documentation gap; resolved by citation). Closure: WP-5 (2026-04-21) via citation-hardening."

3. Locate the closure table row for aoestats NOTE 2 (line 100). Change "WP-5 (scheduled)" to "WP-5 (PR #TBD, 2026-04-21)" and "OPEN — SCHEDULED" to "CLOSED (`.md` + `.py` provenance located)".

**Verification:**
- `grep "aoestats NOTE 2" reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md` returns the reworded bullet.
- Closure table row no longer says "OPEN — SCHEDULED" for aoestats NOTE 2; shows "CLOSED" with citation.
- No "miss" or "not a real gap" judgmental prose.

**File scope:**
- `reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md` (Update)

**Read scope:** T01 line numbers.

---

### T03 — Inline anchor in `INVARIANTS.md §3 Temporal invariants`

**Objective:** Add a cross-reference to the 43-day gap in §3 Temporal invariants (NOT §1 — that is "Data-source invariants"). Place the new bullet adjacent to the existing "Coverage" bullet at line 74.

**Instructions:**
1. Edit `src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md`.
2. Locate §3 Temporal invariants (heading at line 69). Identify the "**Coverage:**" bullet at line 74.
3. After the Coverage bullet, add a new bullet (keeps §3's existing ~30-word-per-bullet pattern):

   "**Inter-file temporal gaps:** matches/ directory contains 3 gaps (2024-07-20 → 2024-09-01 = 43 days; 2024-09-28 → 2024-10-06 = 8 days; 2025-03-22 → 2025-03-30 = 8 days); players/ directory adds a fourth 8-day gap (2025-11-15 → 2025-11-23). Filename-scan derivation at `reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md:<matches-line>,<players-line>`; scanning logic at `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py`. The 43-day gap is cited in thesis §4.1.2 with an in-place [REVIEW] flag on the post-patch API-schema interpretive claim. (01_01_01)"

4. Fill `<matches-line>` and `<players-line>` from T01 notes. Do NOT include the 2022-08-28/2026-02-07 filename-scan extent range dates in the new bullet — the `.md` reports those, and the Coverage bullet already carries the timestamp-content extent; including both in a single bullet risks reader confusion between extents.

**Verification:**
- `grep "01_01_01_file_inventory.md\|01_01_01_file_inventory.py" src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md` returns the new citations.
- New bullet is placed after the Coverage bullet (line 74), before the `overviews_raw` bullet (currently line 75).
- Existing §3 content is preserved (no destructive edits).

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md` (Update)

**Read scope:** T01 line numbers.

---

### T04 — Spot-check `sec_4_1_crosswalk.md` row 81

**Objective:** Confirm the Pass-2 evidence crosswalk row for the 43-day gap is consistent with the audit summary closure. Read-only verification.

**Instructions:**
1. Read `thesis/pass2_evidence/sec_4_1_crosswalk.md` line 81 in its table context.
2. Verify the row cites `01_01_01_file_inventory.md` and reports "43 days" / "43 dni" consistently.
3. If an inconsistency is found, flag it in executor output; edit only if the correction is a < 2-line trivial fix. Otherwise defer to a separate Pass-2 chore.

**Verification:** executor confirms crosswalk row consistent.

**File scope:** None (read-only; conditional update only if trivial inconsistency found).
**Read scope:** `sec_4_1_crosswalk.md`.

---

### T05 — Version bump + CHANGELOG

**Objective:** Version 3.41.1 → 3.41.2 (patch, chore).

**Instructions:**
1. Edit `pyproject.toml`: `version = "3.41.1"` → `version = "3.41.2"`.
2. Edit `CHANGELOG.md`: move `[Unreleased]` aside; add `[3.41.2] — 2026-04-21 (PR #TBD: chore/aoestats-43-day-gap-provenance)`:
   - `### Fixed`: "Corrected aoestats Phase 01 audit NOTE 2 ('43-day post-patch gap figure no artifact provenance'). Follow-up verification 2026-04-21 located the existing provenance at `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md` (reports the figure) + `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py` (filename-scanning derivation). `phase01_audit_summary_2026-04-21.md` aoestats NOTE 2 closure updated: OPEN-SCHEDULED → CLOSED with `.md` + `.py` provenance citation. `INVARIANTS.md §3 Temporal invariants` adds a cross-reference bullet listing all 7 inter-file gaps with anchor paths. Thesis §4.1.2 interpretive claim (post-patch API-schema correlation) retains its existing in-place [REVIEW] flag — Pass-2 Chat workflow territory, not in scope here. All 5 WPs closing the 2026-04-21 Phase 01 audit findings are now complete."
3. Reset `[Unreleased]` to empty.

**Verification:**
- `pyproject.toml` `version = "3.41.2"`.
- `CHANGELOG.md` `[3.41.2]` populated; `[Unreleased]` reset.

**File scope:**
- `pyproject.toml` (Update)
- `CHANGELOG.md` (Update)

---

## File Manifest

| File | Action |
|------|--------|
| `reports/artifacts/01_exploration/06_decision_gates/phase01_audit_summary_2026-04-21.md` | Update |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md` | Update |
| `pyproject.toml` | Update |
| `CHANGELOG.md` | Update |
| `planning/current_plan.md` | (this plan; tracked separately) |
| `planning/current_plan.critique.md` | (Mode A) |

4 git-diff-scope files (all modified) + 2 planning meta.

## Gate Condition

- Audit summary aoestats NOTE 2 reworded in §3 with neutral tone + `.md` + `.py` provenance citation.
- Closure table row CLOSED.
- `INVARIANTS.md §3 Temporal invariants` adds an "Inter-file temporal gaps" bullet at/near line 74 after Coverage, citing `.md` + `.py`; no range-date duplication with the existing Coverage bullet.
- `sec_4_1_crosswalk.md` row 81 confirmed consistent.
- `pyproject.toml` 3.41.2; CHANGELOG `[3.41.2]` populated; `[Unreleased]` reset.
- Three `PHASE_STATUS.yaml` unchanged.
- `git diff --stat` touches exactly 4 files + planning meta.
- All 5 WPs closing 2026-04-21 Phase 01 audit findings complete.

## Out of scope

- Thesis §4.1.2 prose edits — Pass-2 Chat workflow.
- Dedicated temporal-gap SQL artifact — redundant (`.md` + `.py` already exist).
- Investigation of interpretive claim (post-patch API schema) — community archives; Chat workflow.
- Amendments to `01_01_01_file_inventory.md` or `.py` — functional as-is.
- Changes to other research_log entries that mention the 43-day gap — consistent with `01_01_01` provenance.
- Any top-level closure statistics update in `phase01_audit_summary_2026-04-21.md` — no such statistic exists (verified in Mode A pre-check).

## Open questions

- **Q1 (resolved by grep):** Does thesis prose use the 43-day figure? — YES at `04_data_and_methodology.md:85`. Retract does NOT apply.
- **Q2 (resolved by artifact check):** Does `01_01_01_file_inventory.md` contain the figure? — YES at lines 29 + 38. Does the `.py` exist? — YES. Full-derivation variant does NOT apply.
- **Q3 (resolved; honored in T02/T05):** Audit summary tone — **neutral framing**. No blame-assigning prose.

## Dispatch sequence

1. This plan written at `planning/current_plan.md` on branch `chore/aoestats-43-day-gap-provenance`.
2. `reviewer-adversarial` Mode A invoked 2026-04-21 — verdict REVISE with 1 BLOCKER + 2 WARNINGs + 2 NOTEs. **Revision round applied 2026-04-21:** all 5 findings addressed (T03 §1→§3 fix; T02 phantom step 5 struck; neutral framing; derivation-location acknowledgement; date-range distinction handled). Critique preserved. Symmetric 1-revision cap consumed.
3. Execute T01–T05 directly (plan scope is trivially small; parent does edits; no executor agent needed).
4. `reviewer` (Cat C default) post-execution spot-check — verdict APPROVE expected given scope.
5. Pre-commit validation (all hooks skip; planning-drift passes).
6. Commit + PR + merge.
7. **WP-plan backlog empty** post-merge. User chooses next move.
