# PSI Pre-Game Features Summary — aoestats

**spec:** reports/specs/01_05_preregistration.md@7e259dd8
**Step:** 01_05_02
*(conditional on ≥10 matches in reference period; see §6 for sensitivity)*

## Primary Reference: 2022-08-29..2022-10-27 (patch 66692; spec §7 corrected v1.0.3)

Features analyzed: focal_old_rating, avg_elo, faction, opponent_faction, mirror, p0_is_unrated, p1_is_unrated, map

## Rating Drift (focal_old_rating, avg_elo)

Quarters with PSI >= 0.10: **6** of 8

## Faction Stability

Quarters with PSI >= 0.25: **7** of 8

## B3 Coincidence Note

Primary reference window start (2022-08-29) coincides with dataset's earliest date.
Counterfactual reference (2023-Q1) CSV: `psi_aoestats_counterfactual_2023Q1ref.csv`.
See gate memo for B3 verdict.

## M4 Note (Critique fix)

`focal_old_rating = CASE WHEN player_id = p0_profile_id THEN p0_old_rating ELSE p1_old_rating END`
is used as the symmetric rating feature. Per-slot (p0/p1) analysis not emitted in
primary PSI; would carry [PRE-canonical_slot] tag.

## Falsifier verdict

**Q2 rating-drift hypothesis:** PASSED
