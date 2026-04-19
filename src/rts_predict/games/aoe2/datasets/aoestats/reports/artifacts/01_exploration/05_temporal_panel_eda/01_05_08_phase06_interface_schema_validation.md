# Phase 06 Interface Schema Validation -- aoestats

**spec:** reports/specs/01_05_preregistration.md@7e259dd8
**Step:** 01_05_08

## Schema checks

- Column count: 9 (expected 9): OK
- All dataset_tag == 'aoestats': True
- No string 'NaN': True
- Total rows: 136 (>= 64: True)

## M5 note

aoestats analyzes 15 columns (spec §1 has 9 core columns; extended with focal_old_rating, faction, opponent_faction, p0_is_unrated, p1_is_unrated, map, patch for aoestats-specific richness). metric_name values: psi, cohen_h, cohen_d, icc -- overlap with sibling plans.

## B3 Counterfactual reference

Rows with reference_window_id = '2023-Q1-alt': 56
