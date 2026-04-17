---
verdict: REVISE_BEFORE_EXECUTION
plan_reviewed: planning/current_plan.md
revision_reviewed: 2
reviewer_model: claude-opus-4-7[1m]
date: 2026-04-17
v1_findings_resolved:
  BLOCKER-1: pass
  BLOCKER-2: pass
  BLOCKER-3: pass
  BLOCKER-4: fail (see v2-BLOCKER-1 — lexical fix only; structural enforcement gap persists)
  BLOCKER-5: fail (same — IN_GAME_HISTORICAL inheritance from APM convention not used)
  WARNING-1: pass
  WARNING-2: pass
  WARNING-3: pass
  WARNING-4: pass
  WARNING-5: pass
  NOTE-1: pass
  NOTE-2: pass
findings:
  - id: v2-BLOCKER-1
    severity: BLOCKER
    title: "BLOCKER-4/5 fix puts I3 enforcement in non-load-bearing field; pattern inconsistency with existing 51 columns"
    description: |
      Existing player_history_all.yaml uses single-token notes: provenance
      categories on all 51 columns (vocabulary: IDENTITY, TARGET, PRE_GAME,
      IN_GAME_HISTORICAL, CONTEXT). The plan's BLOCKER-4/5 fix prescribes
      multi-sentence operational prose in notes: for 2 new columns while
      leaving the 35 surviving columns with bare tags. Two defects:

      (D-1 Pattern asymmetry) Only 2 of 37 columns would carry "Phase 02
      MUST filter match_time < T" prose; the other 35 — including 4
      IN_GAME_HISTORICAL columns and the TARGET — keep bare tags. By
      implication, a Phase 02 implementer concludes the constraint applies
      only to the tagged 2.

      (D-2 Non-load-bearing enforcement) Concern D enumerated stronger
      enforcement options: (a) assertion battery, (b) column rename, (c)
      machine-readable invariants block. The plan provides ZERO of (a)/(b)/(c).
      A Phase 02 implementer reading data via DuckDB does NOT see YAML
      notes. The fix is comment-text in a file Phase 02 may never open.

      Correct fix follows the project's existing convention:
      - Use `notes: POST_GAME_HISTORICAL` (single token) on is_decisive_result
      - Use `notes: IN_GAME_HISTORICAL` (single token) on is_apm_unparseable
      - Document operational meaning ONCE in the file's existing invariants:
        block (lines 271-282 — the project's machine-readable container)
      - Extend invariants.I3 entry to enumerate all 5 provenance categories
        and state the match_time < T filter requirement
    investigated_concern: D

  - id: v2-WARNING-1
    severity: WARNING
    title: "Source `result` not updated to POST_GAME_HISTORICAL alongside derived flag"
    description: |
      §5 cell 25 prescribes POST_GAME_HISTORICAL provenance for is_decisive_result
      but does NOT instruct cell 25 to update `result.notes` (currently TARGET
      at player_history_all.yaml line 44) analogously. Per plan's own logic —
      POST_GAME_HISTORICAL means "derived from result IN ('Win','Loss')" — the
      source `result` itself carries the same temporal-leakage risk when used
      as a feature input to historical aggregations. Asymmetric treatment
      leaves an enforcement gap on the column that already has a longer
      history of consumption.

      Fix: cell 25 also updates `result.notes` from TARGET to POST_GAME_HISTORICAL
      (TARGET is, by definition, a sub-class of POST_GAME_HISTORICAL).
    investigated_concern: E

  - id: v2-NOTE-1
    severity: NOTE
    title: "matches_flat_clean.yaml NEW lacks invariants block; only column data planned"
    description: |
      §5 cell 26 instructs the executor to write column data only — no analog
      to player_history_all.yaml invariants block (lines 271-282) is prescribed.
      matches_flat_clean is the prediction-target VIEW where I3, I5, I9
      enforcement is most critical, yet the new YAML will land with zero
      machine-readable invariant documentation.

      Fix: cell 26 also writes an invariants block with at least: I3
      (PRE_GAME-only column set), I5 (1 Win + 1 Loss per replay_id), I9
      (no feature computation), I10 (filename relative to raw_dir).
    investigated_concern: E

  - id: v2-NOTE-2
    severity: NOTE
    title: "§3.8 cleaning_registry impact column has hedged count for handicap"
    description: |
      Line 527: `drop_handicap_near_constant` impact reads "-1 (or -2) cols".
      Per §1 DS-SC2-09 line 294, the per-VIEW counts are determinable: -2 from
      matches_flat_clean (handicap + is_handicap_anomalous), -1 from
      player_history_all (handicap only). Replace "-1 (or -2)" with explicit
      per-VIEW breakdown.
    investigated_concern: E

verified_correct:
  - "Concern A (BLOCKER-1 reach): zero surviving NULLIF MMR or convert MMR to NULL references; remaining NULLIF mentions are APM-only or rejected-alternative prose"
  - "Concern B (BLOCKER-2 propagation): 28-cols/21-drops consistent across §2/§3.6/§4 ROADMAP gate/Gate Condition; drop count by source sums to 21; player_history_all 16 drops sum verified"
  - "Concern C (BLOCKER-3 restructure): 3.3a contains exactly 21/16 newly-dropped cols; 3.3b explicitly tagged NOT counted in cleaning_registry; §3.8 has 9 rules per actionable DS — no leakage"
  - "WARNING-1 fix: line 290 cites DS-SC2-08 not DS-SC2-09 itself"
  - "WARNING-2 fix: line 159 cites B6 deferral framework explicitly"
  - "WARNING-3 fix: §5 cell 26 declares flat-list shape canonical, rejects template Section A shape"
  - "WARNING-4 fix: §5 cell 26 specifies column ordering matches DDL SELECT-list verbatim"
  - "WARNING-5 fix: §6 line 726 adds ROADMAP grep, prior-revert context, per-dataset scope note"
  - "POST_GAME_HISTORICAL is verifiably a NEW provenance category in the file (zero pre-existing occurrences)"
  - "ROADMAP grep confirms no 01_04_03+ pre-listed; WARNING-5 empirical premise holds"
  - "Schema YAML notes: field can technically carry multi-line strings (matches_long_raw.yaml line 19); v2-BLOCKER-1 is a pattern-consistency + enforcement-gap defect, not a YAML format issue"
  - "9 cleaning_registry rules cover all actionable DS resolutions; no double-counting"
---

# Adversarial Review Round 2 — sc2egset 01_04_02 plan v2

## Verdict: REVISE_BEFORE_EXECUTION

The v2 edits **correctly and completely resolve 10 of 12 round-1 findings** (BLOCKER-1, BLOCKER-2, BLOCKER-3, all 5 WARNINGs, both NOTEs). Two remain unresolved (BLOCKER-4 and BLOCKER-5) — addressed in wording but not in substance: the round-1 risk (Phase 02 implementer aggregating a POST_GAME or IN_GAME flag without filtering `match_time < T`) is unchanged.

**1 NEW BLOCKER** (v2-BLOCKER-1) consolidates the residual structural defect; **1 new WARNING** (v2-WARNING-1) and **2 new NOTEs** surface from delta inspection.

## Path to APPROVE

1. **v2-BLOCKER-1 fix:** Rewrite §5 cell 25 instruction so notes: field for both new columns uses single-token tags (`POST_GAME_HISTORICAL` / `IN_GAME_HISTORICAL`) consistent with the file's 51-column convention. Move operational `match_time < T` requirement into the file's invariants: block as an extension of the existing I3 entry. Expanded I3 should enumerate PRE_GAME / IN_GAME_HISTORICAL / POST_GAME_HISTORICAL / IDENTITY / CONTEXT with the filter requirement stated once.

2. **v2-WARNING-1 fix (recommended same revision):** §5 cell 25 also updates `result.notes` from TARGET to POST_GAME_HISTORICAL.

3. **v2-NOTE-1 fix (recommended):** §5 cell 26 also writes an invariants block to matches_flat_clean.yaml with I3, I5, I9, I10.

4. **v2-NOTE-2 fix (recommended):** §3.8 line 527 — replace "-1 (or -2)" with explicit per-VIEW breakdown.

After fix #1, verdict moves to APPROVE. Fixes #2-#4 are non-blocking but recommended for audit-clean delivery.

## Reproducibility note

Review verified ground truth via direct file reads against player_history_all.yaml, matches_long_raw.yaml, ROADMAP.md, and the v2 plan body. All claims about 51-column notes vocabulary, invariants block structure, and POST_GAME_HISTORICAL net-newness are inspectable.
