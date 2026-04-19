# 01_05 Decision Gate Memo — aoestats
# spec: reports/specs/01_05_preregistration.md@7e259dd8

**Date:** 2026-04-18
**Pipeline Section:** 01_05 — Temporal & Panel EDA
**Dataset:** aoestats
**Spec SHA:** 7e259dd8 (v1.0.1 LOCKED)

---

## Summary of Findings

| Analysis | Status | Verdict |
|----------|--------|---------|
| Q1 Quarterly grain | complete | PASSED |
| Q2 PSI pre-game features | complete | PASSED |
| Q3 Patch regime stratification | complete | PASSED |
| Q4 Triple survivorship | complete | PASSED |
| Q6 ICC variance decomposition | complete | FALSIFIED |
| Q7 Temporal leakage audit | complete | PASS |
| Q8 DGP diagnostics (duration) | complete | PASSED |
| Q9 Phase 06 interface | complete | see phase06_interface_aoestats.csv |

## Q7 Leakage Audit: PASS

Audit found no temporal leakage in aoestats 01_05. Reference PSI computed exclusively
from data in 2022-08-29..2022-10-27 (patch 66692). No per-player feature windows
were materialised in 01_05.

## B3 Coincidence: Reference Start = Dataset Earliest Date

**IMPORTANT:** Primary reference start 2022-08-29 coincides with the dataset's earliest
data date. Match count jumps ~22x from 2022-Q3 (18k) to 2023-Q1 (404k), reflecting
crawler coverage expansion, not player growth. PSI increases in early tested quarters
may reflect:
  (a) Population drift (genuine)
  (b) Crawler expansion (confound)
  (c) Patch heterogeneity (confound)

Counterfactual reference (2023-Q1) PSI provided in `psi_aoestats_counterfactual_2023Q1ref.csv`.
Verdict: if counterfactual PSI conclusions align with primary, drift interpretation holds.
If they diverge, crawler expansion is a confound warranting BACKLOG item.

## ICC Results (50k stratified sample, M3 fix)

- LMM observed-scale (icc_lpm_observed_scale): None
- ANOVA observed-scale (icc_anova_observed_scale, Wu/Crespi/Wong 2012): 0.0268

**M7 branch-v limitation:**
ICC computed on `profile_id`; per INVARIANTS §2, within-aoestats migration/collision
unevaluable (branch v). aoec namespace bridge (VERDICT A 0.9960) supports stability
but doesn't audit fragmentation. ICC = upper bound on per-player variance share.

## [PRE-canonical_slot] Flag Status

`canonical_slot` column is **ABSENT** from `matches_history_minimal`.
`pre_canonical_slot_flag_active` = **True**.

All per-slot breakdowns produced in 01_05 carry `[PRE-canonical_slot]` in their `notes`.
Symmetric-aggregate outputs (faction, opponent_faction PSI via UNION-ALL) do NOT carry
the flag.

## BACKLOG F1 — canonical_slot: PRIMARY PHASE 02 UNBLOCKER

**BACKLOG item F1 (`canonical_slot`)** is the PRIMARY UNBLOCKER for aoestats Phase 02.
Cite: `planning/BACKLOG.md` F1 block.

Until F1 is resolved:
- Any Phase 02 feature conditioned on raw slot position (team=0 or team=1) is INVALID per I5.
- PSI/ICC/DGP artifacts produced in 01_05 are valid for Phase 06 Decision Gate.
- Phase 02 feature engineering MUST use `focal_old_rating` (CASE-based, slot-symmetric)
  NOT raw `p0_old_rating` or `p1_old_rating` directly.

**Recommendation:**
Adopt F1 (add canonical_slot to matches_history_minimal) BEFORE Phase 02 feature
engineering begins. This unblocks slot-symmetric features and removes the `[PRE-canonical_slot]`
flag from all downstream outputs.

Alternative: proceed with `[PRE-canonical_slot]`-tagged Phase 02 features and amend
post-hoc (higher technical debt).

## Patch-Anchored Reference Asymmetry (spec §7 / §14 locked)

Primary reference window: 9 weeks (2022-08-29..2022-10-27, patch 66692).
sc2egset/aoec reference: ~4 months.
Asymmetry is spec-locked per §7 rationale (within-reference homogeneity prioritisation).
No amendment needed. Documented here per §14 amendment log.

19-patch regime extends to 2026-02-06 (2-year extension beyond cross-dataset window).
This is within-aoestats secondary stratification only per spec §5.
Cross-dataset regime remains: `regime_id ≡ calendar quarter`.

## Artifacts Produced

| File | Description |
|------|-------------|
| quarterly_grain_row_counts.{csv,json,md} | Q1 quarterly grain |
| psi_aoestats_{2023-Q1..2024-Q4}.csv | Q2 PSI (8 files, primary reference) |
| psi_aoestats_counterfactual_2023Q1ref.csv | Q2 PSI counterfactual (B3) |
| 01_05_02_psi_summary.{json,md} | PSI summary + frozen edge fingerprints |
| patch_map.csv | 19-patch map |
| patch_civ_win_rates.csv | Per-civ win rates by patch |
| patch_transitions_flagged.csv | Patch-to-patch Δwin_rate flags |
| patch_heterogeneity_decomposition.csv | M1 Simpson probe |
| 01_05_03_patch_regime_summary.{json,md} | Stratification summary |
| survivorship_unconditional.csv | Q4 survivorship §6.1 |
| survivorship_sensitivity.csv | Q4 survivorship sensitivity N∈{5,10,20} |
| 01_05_04_survivorship_summary.{json,md} | Survivorship summary |
| 01_05_05_icc_results.{json,md} | ICC (LMM + ANOVA + bootstrap CI) |
| icc_sample_profile_ids_{20k,50k,100k}.csv | M3 reservoir sample IDs |
| 01_05_06_temporal_leakage_audit_v1.{json,md} | Q7 leakage audit |
| dgp_diagnostic_aoestats_*.csv | Q8 DGP diagnostics (9 files) |
| 01_05_07_dgp_diagnostic_summary.{json,md} | DGP summary |
| phase06_interface_aoestats.csv | Q9 Phase 06 interface |
| 01_05_08_phase06_interface_schema_validation.{json,md} | Schema validation |
| patch_quarter_distribution.csv | Per-quarter patch share |

Research log anchor: `research_log.md#2026-04-18-01-05-temporal-panel-eda`
