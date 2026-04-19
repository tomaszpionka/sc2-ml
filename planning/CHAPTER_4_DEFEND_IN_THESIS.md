# Chapter 4 — DEFEND-IN-THESIS Residuals

**Source:** planner-science consolidated methodology plan, 2026-04-19
(post-PR-#172 merge; spec `CROSS-01-05-v1` v1.0.5; master `fc89efa6`).

These are the six **irreducible** residuals after the 7-PR pre-01_06
remediation cycle (PRs #162–#172). They cannot be resolved in code; they
must be addressed as **methodology paragraphs in Chapter 4 of the thesis**.
Each item carries a defense framing sketched by `planner-science` — those
sketches are *starting points* for the prose, not finished text.

The hard BLOCKERS that previously sat on this list are all closed:
- I3 leakage-audit substance: PR #166 (sc2egset) + PR #168 (aoestats).
- I9 spec deviation procedure: PR #169 (aoestats §14 v1.0.3) + PR #170
  (cross-dataset §14 v1.0.4) + PR #172 (§12 v1.0.5).
- ICC math: PR #167 (aoestats `.ngroups` + cluster-bootstrap CI).
- Cross-game ICC estimator asymmetry: PR #170.
- aoestats sensitivity-axis confusion: PR #171.
- Phase 06 CSV schema drift: PR #172.

What remains below is **prose work for the thesis**, not code work for
the pipeline.

---

## Residual #1 — Reference-window asymmetry

**The fact.** sc2egset and aoe2companion use a 4-month reference period
(2022-08-29..2022-12-31, spec §7). aoestats uses a 9-week single-patch
window (2022-08-29..2022-10-27, patch 66692, spec §7 + §11 W3
ARTEFACT_EDGE binding). The cross-dataset comparison is therefore
asymmetric on reference-period length.

**Examiner question.** "Why doesn't aoestats use a comparable-length
reference?"

**Defense framing.** The aoestats reference is patch-anchored to enforce
within-reference distributional homogeneity. Extending the window
across a patch boundary would confound the reference distribution with
patch-regime shift — the spec §7 aoestats-rationale paragraph is
explicit that homogeneity is the priority over comparable length. The
asymmetry is a known, locked, and justified design choice; it is not
something that emerged post-hoc to rescue a result. Cite spec §7 and
§11 directly. Note that PSI/ICC findings do not depend on reference
length per se — they depend on reference distribution, which is what
the homogeneity constraint protects.

**Where in Chapter 4.** Methodology section on reference selection;
should appear before the cross-game results table.

---

## Residual #2 — Population-scope differences

**The fact.** sc2egset is `[POP:tournament]` (curated tournament
replays). aoe2companion is `[POP:ranked_ladder]` (online ladder with
broad skill range). aoestats is also `[POP:ranked_ladder]` but with a
different upstream crawler that has a different selection bias on which
matches it ingests. PSI / ICC values are not strictly commensurable
across these scopes.

**Examiner question.** "What does it mean to compare ICC between
'AoE2 players' and 'SC2 players' when your samples are differently
scoped?"

**Defense framing.** The thesis does NOT claim universal statements
about "AoE2 players" or "SC2 players." It claims **dataset-conditional
statements** — the `[POP:]` tag in the `notes` column of every Phase 06
row scopes every finding. Cross-dataset comparisons are framed as
*"do the same analytic patterns appear across differently-sampled
populations?"* rather than *"do populations agree on their aggregate?"*
This is the comparative-methodology framing per scientific-invariant #8;
explicitly note that population-scope is a **controlled experimental
variable** in the cross-game design, not a confound.

**Where in Chapter 4.** Cross-game discussion section; should appear
once and be referenced from each per-dataset interpretation paragraph.

---

## Residual #3 — Observed-scale vs latent-scale ICC

**The fact.** All three datasets report `icc_anova_observed_scale` as
the headline (spec v1.0.4 §14(b)). Observed-scale ICC on Bernoulli
outcomes underestimates the latent-scale ICC when the logit link is
non-linear at the margins (Nakagawa et al. 2017,
royalsocietypublishing.org/doi/10.1098/rsif.2017.0213). GLMM
latent-scale ICC is reported only where it converges (aoec skipped per
spec v1.0.2 §14(c); sc2egset attempted but `BayesMixedGLMResults`
attribute issue).

**Examiner question.** "Shouldn't your headline ICC be latent-scale for
a Bernoulli outcome?"

**Defense framing.** Latent-scale ICC requires GLMM estimation, which is
compute-prohibitive at aoec scale (5k+ groups MCMC) and failed
convergence on sc2egset under the project's compute budget. We report
observed-scale ICC as the **cross-dataset-comparable** estimator
(consistent across all three datasets). The Nakagawa 2017 conversion
formula `ICC_latent = ICC_observed / (ICC_observed + π²/3)` is cited as
a methods-paragraph caveat: observed-scale is a **lower bound** on the
latent-scale quantity under a logit link with small τ². The thesis's
*directional* claim — "ICC on `won` is small in all three datasets" —
survives the link transformation.

**Where in Chapter 4.** Methodology subsection on ICC estimator choice;
~3 sentences; cite Nakagawa 2017 and Chung et al. 2013 (REML
boundary-shrinkage justification for ANOVA primary).

---

## Residual #4 — aoestats 744-player reference cohort

**The fact.** Spec §11 W3 ARTEFACT_EDGE binding forces aoestats to
restrict its reference to a single patch (66692, 9 weeks, ~800k
matches). At the §6.3 default cohort threshold N=10, this gives only
**744 eligible players**. PR #171's cohort-threshold sensitivity table
shows this is a hard ceiling: N=20 reduces the cohort to 3 players;
relaxing the patch constraint would re-introduce patch heterogeneity
(forbidden by §11).

**Examiner question.** "Your aoestats ICC is computed on 744 players.
Why so small? Doesn't that limit identification?"

**Defense framing.** This is a **window-size ceiling**, not a method
limitation. The single-patch constraint is the cost of within-reference
homogeneity (spec §7 + §11). At 744 clusters the ANOVA ICC point
estimate is well-identified per Gelman & Hill 2007 §11-12 (which note
ICC point estimates are reasonable with as few as 20-50 clusters). The
PR #171 sensitivity table documents that the ICC point is roughly
stable at ~0.025-0.027 across N=5 (4,325 players) and N=10 (744
players); the cohort-size ceiling does not bias the ICC, it widens
the CI. Chapter 4 reports the bootstrap CI honestly. A
larger-window supplementary analysis (multi-patch aoestats) is
explicitly **out of preregistered scope**; running it would be
unregistered exploration.

**Where in Chapter 4.** aoestats per-dataset section; mention once
when reporting the 0.0268 ANOVA ICC; reference spec §11 explicitly.

---

## Residual #5 — W3 ARTEFACT_EDGE / `canonical_slot` deferral

**The fact.** aoestats's `team` column carries a known upstream-API
bias (W3 ARTEFACT_EDGE verdict, commit `ab23ab1d`): `team=1` is the
higher-ELO player in 80.3% of games, mean ELO diff +11.9. This is NOT
game-mechanical. A `canonical_slot` column is required before any
Phase 02 feature engineering on aoestats team-conditioned features.
Spec §11 binding: any 01_05 finding conditioned on `team` is flagged
`[PRE-canonical_slot]` in the `notes` column.

**Examiner question.** "Your aoestats team-conditioned features are
flagged `[PRE-canonical_slot]`. What does that flag mean for Chapter 4
interpretation?"

**Defense framing.** The flag indicates that any team-conditional
interpretation is **provisional** pending the Phase 02 amendment that
adds `canonical_slot` to `matches_history_minimal`. The 01_05 PSI / ICC
/ DGP outputs are valid for cross-dataset comparison as long as the
flag is honored: aggregate (UNION-ALL-symmetric) features are unaffected
(`faction`, `opponent_faction`, `won` aggregate); only per-slot
breakdowns carry the flag. Chapter 4 must enumerate the flag at every
appearance and explicitly defer team-conditional claims to a
post-`canonical_slot` re-analysis. The W3 commit `ab23ab1d` provides
the empirical evidence the examiner can audit.

**Where in Chapter 4.** Chapter 4 footnote at every aoestats
team-conditioned table; one paragraph in the methodology section
defining the flag and its scope; `BACKLOG.md F1` cites this as the
**primary Phase 02 unblocker**.

---

## Residual #6 — N=2 cross-game statistical-test limit

**The fact.** Per scientific-invariant #8 and Demsar 2006
(JMLR 7:1-30), Friedman / Wilcoxon-Holm cross-dataset tests require
N ≥ 5 datasets/games. Our cross-game comparison is N=2 (SC2 + AoE2).
Formal statistical tests at the cross-game level are therefore
inapplicable.

**Examiner question.** "How do you statistically compare your two
games?"

**Defense framing.** Already addressed by invariant #8 — the thesis
follows the documented per-game/per-dataset pairwise testing
methodology (5×2 cv F-test or Nadeau-Bengio corrected t-test
within-game; Bayesian comparison via `baycomp` where applicable;
qualitative cross-game concordance discussion). The thesis does NOT
claim a Friedman-equivalent statistical comparison **across games** —
only **within-game**, where N_folds ≥ 5 is achievable. The cross-game
finding is framed as effect-size + bootstrapped-CI per game, with a
qualitative concordance paragraph. This is the methodologically
honest framing for N=2; cite Demsar 2006 explicitly when defending.

**Where in Chapter 4.** Methodology section on statistical comparison;
~1 paragraph; reference invariant #8 and `docs/ml_experiment_lifecycle/06_CROSS_DOMAIN_TRANSFER_MANUAL.md`.

---

## Cross-cutting Chapter 4 numbers (post-v1.0.5 master)

| Dataset | Headline ICC (ANOVA observed-scale) | Bootstrap CI | N (obs) |
|---------|-------------------------------------|--------------|---------|
| sc2egset | 0.0463 | (delta-method in `variance_icc_sc2egset.csv`) | 4,034 |
| aoe2companion | 0.003013 | [0.001724, 0.004202] | 360,567 (5k stratified sample) |
| aoestats | 0.0268 | [0.0148, 0.0387] | 7,909 (744 eligible @ N=10) |

All directly comparable: observed-scale ANOVA on `won` per Wu/Crespi/Wong
2012 CCT 33(5):869-880, with cluster-bootstrap CI per Ukoumunne et al.
2012 PMC3426610. Differences in CI width reflect cohort size, not
estimator inconsistency.

---

## Spec / artifact provenance

- **Spec:** `reports/specs/01_05_preregistration.md` v1.0.5 (master `fc89efa6`).
- **Phase 06 CSVs (11-column v1.0.5 schema):**
  - `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/phase06_interface_sc2egset.csv` (35 rows)
  - `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_phase06_interface_aoe2companion.csv` (74 rows)
  - `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/phase06_interface_aoestats.csv` (136 rows)
- **Adversarial transcripts:**
  - 2026-04-19 pre-01_06 review (DEFEND-IN-THESIS items 1–3): see session
    transcript on `master` branch context.
  - 2026-04-19 PR #162 review (BLOCKERs 1–3): see PR #163 commit message.
- **Planner-science consolidated plan:** see Section 5 of the
  2026-04-19 planning agent transcript (this document is its
  serialised form).

---

## Status flags for the next session

- [x] Residual #1 — reference-window asymmetry (PR #175, §4.1.3 tail)
- [x] Residual #2 — population-scope differences (PR #175, NEW §4.1.4)
- [x] Residual #3 — observed- vs latent-scale ICC (PR #176, §4.4.5)
- [x] Residual #4 — aoestats 744-player ceiling (PR #175, §4.1.2.1)
- [x] Residual #5 — `canonical_slot` deferral (PR #TBD, §4.4.6 + §4.1.2.1 footnote; BACKLOG F1 Predecessors updated)
- [x] Residual #6 — N=2 cross-game statistical-test limit (PR #176, §4.4.4)

Mark each as `[x]` once the corresponding Chapter 4 paragraph is drafted
and reviewed.
