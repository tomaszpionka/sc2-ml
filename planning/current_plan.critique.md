# Adversarial Review — Plan (Mode A) — WP-5

**Plan:** `planning/current_plan.md` — aoestats "43-day post-patch gap" provenance citation-hardening chore
**Branch:** `chore/aoestats-43-day-gap-provenance`
**Base:** master `ef6a863d` (post PR #201; version 3.41.1)
**Category:** C (chore)
**Date:** 2026-04-21
**Reviewer:** reviewer-adversarial, Mode A (pre-execution)

## Lens summary

| Lens | Verdict |
|------|---------|
| Audit-correction integrity | SOUND |
| Scope choice (citation-hardening vs full derivation) | DEFENSIBLE |
| INVARIANTS.md cross-reference target section | FLAWED — plan points at wrong § |
| Audit summary rewording tone | AT RISK — inconsistent with plan's own Q3 |
| Out-of-scope discipline | SOUND |
| Closure statistics update task | PHANTOM SCOPE |
| Thesis anchor chain | INTACT (crosswalk row 81 cites `01_01_01`) |

## Pre-verification facts

- `01_01_01_file_inventory.md`: CONFIRMED — "2024-07-20 -> 2024-09-01 (43 days)" at line 29 (matches/) + line 38 (players/).
- Audit summary §3 aoestats NOTE 2: line 64; closure table row: line 100. No top-level closure statistics exist (§5 table is the only count structure).
- INVARIANTS.md §1 is "Data-source invariants" (file layout, NULL policy). Temporal range with `min=2022-08-29, max=2026-02-06` lives in **§3 Temporal invariants** (lines 72-79). T03's file-read premise is wrong.
- `sec_4_1_crosswalk.md:81` CONFIRMED cites `01_01_01_file_inventory.md` with value "43 dni"/"43".

## BLOCKER / WARNING / NOTE findings

### BLOCKER 1 — T03 targets the wrong INVARIANTS.md section

T03 step 2 says: "Locate the §1 'Temporal range' paragraph (should contain '2022-08-28' and '2026-02-07' boundary dates)." **These dates do not appear in §1.** §1 is "Data-source invariants" (file layout, NULL policies). Temporal range lives in **§3 Temporal invariants** (INVARIANTS.md:72-79). The plan's file-read premise is falsified. Executor following the plan literally will grep §1 for "2022-08-28" and find nothing, then improvise.

**Secondary:** The proposed anchor sentence is ~100 words with embedded line-number placeholders — scope creep for a §3 paragraph averaging ~30 words per bullet. Consider a 2-sentence form.

**Tertiary:** Plan §Scope body line 26 uses `2022-08-28`; INVARIANTS.md §3 uses `2022-08-29` (filename-scan extent vs observed-timestamp extent). T03 must reconcile or distinguish these.

**Fix:** change T03 target to §3 Temporal invariants; tighten anchor sentence; label filename-scan vs timestamp-content range distinction.

### WARNING 1 — T02 step 5 closure statistics are phantom scope

Grep of audit summary for `open|closed|Total|summary|N open` returns only the §5 closure table. There is no top-level "N open — scheduled; N closed" roll-up statistic to update. T02 step 5's "-1 open, +1 closed delta" has nothing to land on.

**Fix:** strike T02 step 5, OR redirect to add a one-line tally at §5 table's head (probably not in scope for a chore).

### WARNING 2 — Rewording tone inconsistent between T02/T05 and plan's own Q3

Plan §Open-questions Q3 recommends **neutral framing** ("follow-up verification located existing provenance"). T02 step 3 executes neutral at first, then drifts: **"The audit's 'no artifact provenance' finding was an artifact-scope miss, not a true gap."** T05 CHANGELOG escalates: **"The audit's original finding was a grep-scope miss, not a real gap."** 

Two problems: (a) inconsistent with Q3's own recommendation; (b) the hypothesized mechanism ("grep-scope miss") is unverifiable — the original reviewer could have used different search terms, missed line 29, or applied a stricter definition of provenance (e.g., requiring derivation SQL **in the MD**, not merely the figure). Since `01_01_01_file_inventory.md` shows **the figure** (43 days) but not **the derivation** (filename-scanning logic is in `01_01_01_file_inventory.py`, not the .md), the original audit's concern about "SQL query establishing its provenance" is **partially valid**.

**Fix:** rewrite T02 step 3's last sentence and T05's CHANGELOG bullet to drop "miss"/"not a real gap" framing; replace with "follow-up verification located the filename-derived figure at `01_01_01_file_inventory.md:29,38`; the underlying derivation logic resides in the corresponding notebook `01_01_01_file_inventory.py`."

### NOTE 3 — Partial-provenance honesty

The closure is a citation of **output**, not of **derivation**. An examiner asking "how was 43 computed from the filename list?" has to read the .py notebook. Acceptable for LOW-severity closure but deserves acknowledgement — either in T02 step 3's closure prose or as a one-line plan §Assumptions caveat.

**Fix:** T02 step 3 adds "derivation logic resides in the corresponding `.py` notebook; MD artifact documents the resulting figure and the filename-range scan inputs."

### NOTE 4 — INVARIANTS §3 date reconciliation

`01_01_01` uses filename-range `2022-08-28 to 2026-02-07`; INVARIANTS.md §3 uses content-range `2022-08-29 to 2026-02-06`; plan §Scope body uses `2022-08-28`. If T03 edits §3, readers see two ranges in the same paragraph unless labeled. Minor, worth a one-line scope clarification.

**Fix:** T03 anchor sentence explicitly labels "filename-scan extent" vs "observed match-timestamp extent" OR omits the 2022-08-28/2026-02-07 dates and references only the 3+4 inter-file gap intervals.

## Verdict

**REVISE BEFORE EXECUTION.** BLOCKER 1 (wrong section) would cause executor trip at T03. WARNING 1 (phantom task) wastes executor effort. WARNING 2 (tone drift) commits a blame-assigning judgment to the audit record. Post-fix, the plan is sound for the declared citation-hardening scope.

## If REVISE: required revisions (enumerated)

1. **BLOCKER 1:** T03 step 2 — change "§1 'Temporal range'" to "§3 Temporal invariants" (lines 72-79). Tighten proposed anchor sentence to ≤ 2 sentences. Either label filename-scan vs timestamp-content date ranges OR drop dates from the added sentence entirely (refer to inter-file gaps only).

2. **WARNING 1:** Strike T02 step 5 entirely. Keep steps 1-4 (reword NOTE 2 description + update closure table row).

3. **WARNING 2:** Rewrite T02 step 3's closing sentence to neutral framing (no "miss"/"not a real gap" language). Rewrite T05 CHANGELOG bullet in the same neutral register. Honor plan's own Q3 recommendation.

4. **NOTE 3:** T02 step 3 adds derivation-location acknowledgement: "derivation logic resides in the corresponding `.py` notebook; the `.md` artifact documents the resulting figure."

5. **NOTE 4:** T03 anchor sentence explicitly labels "filename-scan extent" vs "observed match-timestamp extent" if dates are retained; alternatively, omit dates and refer only to the 7 inter-file gaps.
