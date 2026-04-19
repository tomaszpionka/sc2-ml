# Variance Decomposition ICC — aoestats

**spec:** reports/specs/01_05_preregistration.md v1.0.4 §14(b) (ANOVA-primary headline)
**Step:** 01_05_05

## Primary Result (ANOVA @ N=10, spec v1.0.4 §14(b))

| Metric | Value |
|---|---|
| `icc_anova_observed_scale` | **0.0268** |
| `icc_anova_ci_low` | 0.0148 |
| `icc_anova_ci_high` | 0.0387 |
| `icc_lpm_observed_scale` (diagnostic) | 0.0259 |

## Falsifier verdict

**Q6 skill-signal hypothesis:** FALSIFIED
(Hypothesis range per spec §8: ICC ∈ [0.05, 0.20]; ANOVA primary estimate
0.0268 is below the lower bound 0.05.)

## Cohort-threshold sensitivity (§6.2)

| Threshold | n_players | ANOVA ICC | ANOVA CI | LMM ICC (diagnostic) |
|---|---|---|---|---|
| N= 5 | 4,325 | 0.0251 | [0.0183, 0.0324] | 0.0248 |
| N=10 | 744 | 0.0268 | [0.0148, 0.0387] | 0.0259 |
| N=20 | 3 | 0.0176 | [0.0, 0.0226] | 0.0172 |

**Bootstrap CI** per Ukoumunne et al. 2012 PMC3426610 (n=200).
**Cohort-threshold axis** (§6.2): each N produces a distinct cohort of
players with ≥N prior matches in the reference window [2022-08-29,
2022-10-27] (patch 66692). Larger N = smaller but more-active cohort.

## Restructure note (v1.0.4)

Prior to v1.0.4 this notebook requested player-count samples `{20k, 50k,
100k}` via stratified reservoir sampling. aoestats's single-patch reference
window has only ~744 eligible players at N=10, so all three "sample sizes"
degenerated to the full population — producing three identical ICC rows
labeled as sensitivity. The 2026-04-19 pre-01_06 adversarial review flagged
this as DEFEND-IN-THESIS #2 (axis confusion between §6.2 cohort-threshold
and variance-decomposition sample-group size). v1.0.4 realigns the
sensitivity axis to spec §6.2 cohort match-count thresholds.

## M7 Branch-v Limitation

ICC computed on `profile_id`; per INVARIANTS §2, within-aoestats migration/collision unevaluable (branch v). aoec namespace bridge (VERDICT A 0.9960) supports stability but doesn't audit fragmentation. ICC = upper bound on per-player variance share.
