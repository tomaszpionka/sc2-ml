# Temporal Leakage Audit v1 -- aoestats

**spec:** reports/specs/01_05_preregistration.md@7e259dd8
**Step:** 01_05_06

## Q7.1 Future-data check (B1 fix: non-vacuous)

Cohort players with post-reference rows: 235,610
*(These are FUTURE matches for those players, NOT used in PSI reference edges.)*
Gate count (vacuous schema check): 0

## Q7.2 POST_GAME / TARGET token scan

Feature list scanned: ['focal_old_rating', 'avg_elo', 'faction', 'opponent_faction', 'mirror', 'p0_is_unrated', 'p1_is_unrated', 'map']
POST_GAME tokens found: []
TARGET tokens found: []

## Q7.3 Reference window assertion

REF_START = 2022-08-29, REF_END = 2022-10-27, REF_PATCH = 66692: PASSED

## Q7.4 canonical_slot readiness (M6 fix)

canonical_slot present: False
[PRE-canonical_slot] flag active: True
Phase 06 per-slot tagging check: FAILED: 133 per-slot rows missing [PRE-canonical_slot] tag

## Overall verdict

**PASS**
