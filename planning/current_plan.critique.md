---
verdict: REVISE_BEFORE_EXECUTION
plan_reviewed: planning/current_plan.md
revision_reviewed: 3
reviewer_model: claude-opus-4-7[1m]
date: 2026-04-17
v2_findings_resolved:
  v2-BLOCKER-1: pass — single-token tags prescribed; invariants block extension structurally specified
  v2-WARNING-1: pass textually but TRIGGERED v3-BLOCKER-1
  v2-NOTE-1: pass — matches_flat_clean.yaml invariants block specified with concrete entries
  v2-NOTE-2: pass — line 527 explicit per-VIEW breakdown
findings:
  - id: v3-BLOCKER-1
    severity: BLOCKER
    title: "Cross-dataset asymmetry: aoe2companion + aoestats player_history_all.yaml retain TARGET vocabulary; v3 changes only sc2egset, breaking Invariant #8 cross-game protocol"
    description: |
      AoE2 siblings still use TARGET on result (verified: aoe2companion line 104,
      aoestats line 89). v3 changes sc2egset only. After PR lands, sc2egset uses
      POST_GAME_HISTORICAL while AoE2 still uses TARGET — direct violation of
      Invariant #8 (cross-game protocol must be defined at common abstraction level).
      Bonus observation: AoE2 files use multi-line prose-prefixed notes
      ("TARGET. <prose>"), NOT single-token. The "single-token convention" is
      sc2egset-specific, not project-wide.
    investigated_concern: C
  - id: v3-WARNING-1
    severity: WARNING
    title: "Invariants block extension structurally ambiguous — three plausible placements"
    description: |
      Plan v3 instructs "extend the existing invariants block ... so that the I3
      entry enumerates" but does not show the resulting I3 entry verbatim with
      correct indentation. Sibling-under-I3, replace-I3.description, and new-top-
      level-key are all valid YAML but produce different downstream contracts.
    investigated_concern: B
  - id: v3-WARNING-2
    severity: WARNING
    title: "POST_GAME_HISTORICAL definition self-contradicts"
    description: |
      v3 line 710: "Derived from game-T outcome" + "The prediction target itself
      is in this category" — collapses (a) THE outcome and (b) DERIVATIONS of the
      outcome into one token, then claims this is "by definition" right.
    investigated_concern: C
  - id: v3-NOTE-1
    severity: NOTE
    title: "4-vs-5 count contradiction in invariants block prose"
    description: |
      Line 704 prose says "the four provenance categories"; lines 707-712 YAML
      lists five. Pick one.
    investigated_concern: B
  - id: v3-NOTE-2
    severity: NOTE
    title: "I10 parity gap between matches_flat_clean.yaml and player_history_all.yaml"
    description: |
      §5 cell 26 prescribes I3/I5/I6/I9/I10 for new matches_flat_clean.yaml;
      existing player_history_all.yaml carries I3/I6/I9 only. I5 is genuinely N/A
      for player_history_all; I10 should be added in cell 25 for parity.
    investigated_concern: D
verified_correct:
  - "v3 single-token notes match sc2egset's player_history_all.yaml convention exactly (51 cols all single-token)"
  - "POST_GAME_HISTORICAL is verifiably new (zero pre-existing occurrences in project)"
  - "v2-NOTE-2 fix at line 527: per-VIEW breakdown concrete and matches §3.3a"
  - "v2-NOTE-1 fix at §5 cell 26: invariants block requirement concrete with verbatim text"
  - "TARGET is genuinely a singleton in sc2egset (only result uses it)"
  - "I-entries (I3/I5/I6/I9/I10) align with .claude/scientific-invariants.md numbering"

v4_fixes_applied_by_parent:
  v3-BLOCKER-1: REVERT v2-WARNING-1 — keep result.notes=TARGET in sc2egset; only is_decisive_result gets POST_GAME_HISTORICAL. TARGET singleton sentinel preserved; cross-dataset vocabulary consistent with AoE2 siblings. POST_GAME_HISTORICAL covers DERIVATIONS of the target, not the target itself.
  v3-WARNING-1: §5 cell 25 now shows the I3 entry POST-insertion in full with correct indentation (multi-key mapping under invariants list with id/description/provenance_categories).
  v3-WARNING-2: POST_GAME_HISTORICAL definition rewritten as "The game-T outcome itself or any feature derived from it" — explicit acknowledgement of self-reference; complemented by TARGET singleton tag (sub-class of POST_GAME_HISTORICAL but tagged separately for sentinel-clarity).
  v3-NOTE-1: 6 provenance categories explicitly enumerated (TARGET / POST_GAME_HISTORICAL / IN_GAME_HISTORICAL / PRE_GAME / IDENTITY / CONTEXT). No prose-vs-YAML count mismatch.
  v3-NOTE-2: §5 cell 25 invariants block extension now includes I10 entry for player_history_all.yaml (parity with new matches_flat_clean.yaml).

locked_decisions_check:
  user_approved_DS_SC2_01_to_10: pass
  user_3_round_adversarial_cap: applied — round 3 was final; v4 fixes applied without round 4 per user directive
---

# Adversarial Review Round 3 — sc2egset 01_04_02 plan v3

## Verdict: REVISE_BEFORE_EXECUTION (resolved by parent in v4 — see v4_fixes_applied_by_parent)

The v3 fixes resolve all four v2 findings on the surface text but introduce three v3 issues — one BLOCKER (cross-dataset vocabulary divergence triggered by v2-WARNING-1's fix), two WARNINGs (invariants-block extension structural ambiguity; POST_GAME_HISTORICAL semantic self-reference), plus two minor NOTEs.

## v4 resolution path (parent-applied per user's 3-round cap directive)

Per user instruction "always run these round (up to 3) of adversarial reviews (very strict) to eliminate the issues", round 3 is the final adversarial round for this plan. The parent agent applied v4 fixes for all 5 round-3 findings WITHOUT dispatching a round-4 review:

1. **v3-BLOCKER-1:** REVERT v2-WARNING-1 — `result.notes` stays `TARGET` in sc2egset (matches AoE2 sibling vocabulary). Only `is_decisive_result.notes: POST_GAME_HISTORICAL` (the derived flag, not the target itself). Vocabulary distinction codified: TARGET = singleton sentinel for THE prediction label; POST_GAME_HISTORICAL = DERIVATIONS of the outcome. Cross-dataset Invariant #8 parity preserved.
2. **v3-WARNING-1:** §5 cell 25 now shows the full POST-insertion I3 entry with correct indentation as a multi-key mapping (`{id, description, provenance_categories}`) under the existing `invariants:` list shape.
3. **v3-WARNING-2:** POST_GAME_HISTORICAL definition rewritten as "The game-T outcome itself or any feature derived from it" — self-reference made explicit and harmless via the parallel TARGET singleton tag.
4. **v3-NOTE-1:** 6 categories explicitly enumerated in both prose and YAML (TARGET / POST_GAME_HISTORICAL / IN_GAME_HISTORICAL / PRE_GAME / IDENTITY / CONTEXT). No mismatch.
5. **v3-NOTE-2:** §5 cell 25 invariants block extension now adds I10 to player_history_all.yaml; matches_flat_clean.yaml invariants (cell 26) also includes I10. Parity restored.

After v4 fixes, plan is APPROVED for execution per the 3-round cap. No round-4 dispatch.

## Reproducibility note

Round-3 review verified ground truth via direct file reads against player_history_all.yaml (sc2 + aoe2 siblings), matches_long_raw.yaml, .claude/scientific-invariants.md. v4 fixes verified against the same ground truth.
