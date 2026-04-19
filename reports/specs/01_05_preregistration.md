---
spec_id: CROSS-01-05-v1
spec_version: "1.0.5"
created: 2026-04-18
invariants_touched: [I3, I6, I7, I8, I9]
datasets_bound: [sc2egset, aoe2companion, aoestats]
overlap_window_anchor: "2022-Q3 through 2024-Q4"
status: LOCKED
---

# Pre-registration Spec — 01_05 Temporal & Panel EDA
## CROSS-01-05-v1  (version 1.0.1)

This document is a **pre-registered protocol**. Parameters declared here are
binding for all notebooks that implement Step 01_05 across the three datasets.
Any deviation requires a CROSS research-log entry, an amendment log entry in
§14, and a `spec_version` minor-bump.

---

## §0 Scope

**What this spec covers.**

This spec governs the cross-dataset temporal and panel EDA step (01_05) for
three datasets: `sc2egset`, `aoe2companion` (aoec), and `aoestats`. It locks:

- the time-window grain and comparison anchor (§2, §3)
- PSI binning parameters and thresholds (§4)
- the stratification variable and its relationship to Q1 grain (§5)
- the survivorship cohort design and sensitivity range (§6)
- reference and tested period definitions (§7)
- variance decomposition method (§8)
- temporal leakage audit query structure (§9)
- data-generating-process diagnostic scope and output naming (§10)
- aoestats patch-anchored reference and W3 binding (§11)
- Phase 06 interface schema (§12)
- binding enforcement mechanism (§13)

**What this spec does not cover.**

- Per-dataset raw-ingest or cleaning steps (Phases 01_01 through 01_04).
- Phase 02 feature engineering decisions (deferred; W3's `canonical_slot`
  requirement is flagged here but implemented in a follow-up).
- Model training, evaluation, or hyperparameter selection (Phase 03+).
- AoE2 datasets whose Phase 01_04 cleaning has not yet completed.

---

## §1 `matches_history_minimal` 9-column contract

All three datasets expose a VIEW or table named `matches_history_minimal` with
the following 9 columns. Column names and semantics are shared across datasets.

| # | Column | Type | Shared meaning |
|---|--------|------|----------------|
| 1 | `match_id` | VARCHAR / BIGINT | Unique match identifier within the dataset namespace |
| 2 | `started_at` | TIMESTAMP | UTC match start time; used as the temporal anchor |
| 3 | `player_id` | BIGINT | Canonical player identity per I2 decision (dataset-specific branch) |
| 4 | `team` | INTEGER | Raw team/slot assignment from source API (1 or 2 for 1v1) |
| 5 | `chosen_civ_or_race` | VARCHAR | Faction/race chosen by the player |
| 6 | `rating_pre` | DOUBLE | Pre-match rating/ELO (NULL if not available) |
| 7 | `won` | BOOLEAN | Match outcome from this player's perspective |
| 8 | `map_id` | VARCHAR | Map identifier (raw; may be NULL) |
| 9 | `patch_id` | VARCHAR | Game version/patch string (raw; may be NULL) |

**Cross-dataset note.** The `team` column carries a known bias in aoestats: per
the W3 verdict (ARTEFACT_EDGE, commit `ab23ab1d`), `team=1` is assigned to the
higher-ELO player by the upstream API. A `canonical_slot` column will be added
in a Phase 02 amendment (§14). Until then, any feature or statistic conditioned
on `team` in aoestats is marked `[PRE-canonical_slot]`.

---

## §2 Overlap window

The cross-dataset comparison anchor is **2022-Q3 through 2024-Q4** (10 quarters
inclusive).

Dataset-specific coverage context:

| Dataset | Full temporal range | Overlap window |
|---------|---------------------|----------------|
| sc2egset | ~2016 – 2024 | 2022-Q3 → 2024-Q4 |
| aoe2companion (aoec) | ~2020 – 2026 | 2022-Q3 → 2024-Q4 |
| aoestats | ~2022 – 2026 | 2022-Q3 → 2024-Q4 |

**Justification.** 2022-Q3 is the earliest quarter for which all three datasets
have substantial match volume. 2024-Q4 is the last complete quarter present in
sc2egset (the dataset with the earliest cutoff). The 10-quarter window gives
sufficient length for PSI comparisons while respecting the sc2egset data
boundary.

Quarters outside this window may be used for within-dataset secondary analyses
(e.g., aoec's extended window in §3) but are NOT included in cross-dataset
comparisons.

---

## §3 Q1 Time-window grain

**Grain:** Calendar quarter (Q1–Q4 of each year, ISO-aligned).

**Cross-dataset permitted metrics.**

| Metric | Scope | Formula reference |
|--------|-------|-------------------|
| PSI | Distribution shift | Siddiqi (2006); see §4 |
| Cohen's h | Binary outcome drift | Cohen (1988) §6.2 |
| Cohen's d | Continuous feature drift | Cohen (1988) §2.2 |
| KS statistic (descriptive) | Non-parametric magnitude | Breck et al. (2019) |

**Forbidden cross-dataset metrics.**

ADF and KPSS stationarity tests are **forbidden** for cross-dataset or
cross-period comparisons in this step.

Rationale: the overlap window yields N=8 tested quarters (2023-Q1 through
2024-Q4). Hamilton (1994) §17.7 establishes that standard ADF/KPSS critical
values and power properties require T ≥ 50 observations with adequate
information content; N=8 time-aggregated points fall well below this
threshold, making test decisions unreliable. Effect sizes (Cohen's h/d) and
PSI provide magnitude without misleading p-value inference.

**Within-dataset secondary ADF (flagged non-comparable).**

For aoec only, a within-dataset secondary ADF/KPSS analysis is permitted on
the extended window 2022-08..2026-02 (~14 quarters of monthly data if using
monthly grain). Any such result MUST be clearly labeled
`[WITHIN-AOEC-SECONDARY; NOT CROSS-DATASET]` and referenced with the
Hamilton (1994) caveats.

---

## §4 Q2 PSI binning

**Method:** Equal-frequency binning, N=10 bins.

**Thresholds:**

| PSI | Interpretation |
|-----|----------------|
| < 0.10 | No meaningful shift |
| 0.10 – 0.25 | Moderate shift — flag for review |
| ≥ 0.25 | Significant shift — escalate |

**Bin edges:** Computed from the reference period (§7) only. Edges are **frozen**
after the reference computation and applied read-only to all tested quarters.

**Scope:** Pre-game features only. Features classified as `POST_GAME_HISTORICAL`
or `TARGET` in the feature schema MUST NOT appear in Q2 PSI computation. They
are handled separately in §10 (Q8).

**Unseen categoricals:** If a tested quarter contains a categorical value not
present in the reference period, it is assigned to a synthetic `__unseen__` bin.
The `__unseen__` bin count is recorded in the output notes column (§12).

---

## §5 Q3 Stratification + `regime_id`

**Honest statement:**

> `regime_id ≡ calendar quarter`. Cross-dataset stratification by `regime_id`
> IS stratification by time, identical to the Q1 grain. It provides no
> additional variance reduction beyond Q1.

This equivalence is declared explicitly to prevent any future reader from
interpreting `regime_id` as an independent stratification variable that adds
analytical power to the cross-dataset comparison.

**Per-dataset secondary regimes (non-binding, within-dataset only).**

Each dataset may define a secondary within-dataset regime variable for
exploratory purposes. These are NEVER merged cross-dataset and carry no
cross-dataset inferential weight.

| Dataset | Secondary regime | Variable name |
|---------|-----------------|---------------|
| sc2egset | Tournament era (Bronze/Silver/Gold/Platinum) | `tournament_era` |
| aoe2companion | Leaderboard segment (rm_1v1 / rm_team) | `leaderboard_id` |
| aoestats | Game patch | `patch_id` |

---

## §6 Q4 Survivorship cohort (triple analysis)

Three parallel survivorship analyses are required. All three must appear in the
01_05 output artifacts.

**6.1 Unconditional** — All players with ≥1 match in the overlap window.

Compute `fraction_active` per quarter (fraction of ever-seen players who played
at least once in that quarter). Saved to:
`sandbox/<game>/<dataset>/01_exploration/05_temporal_panel_eda/artifacts/survivorship_unconditional.csv`

Active span definition: a player is "active in quarter Q" if they have ≥1
match with `started_at` in Q. Churn: 90-day sliding window; a player is
"churned" if no match in the trailing 90-day window.

**6.2 Sensitivity** — N ∈ {5, 10, 20} minimum-match thresholds.

For each threshold N, restrict the cohort to players with ≥N matches in the
reference period (§7), then rerun Q2 PSI and Q5 drift computations. Saved to:
`sandbox/<game>/<dataset>/01_exploration/05_temporal_panel_eda/artifacts/survivorship_sensitivity.csv`

Active span ≥30 days (player must have played across a 30-day range in the
reference period to count toward the N-match cohort).

**6.3 Conditional labels** — Every Q2/Q5 drift figure and table MUST carry the
caption suffix:

> *(conditional on ≥10 matches in reference period; see §6 for sensitivity)*

The N=10 threshold is the default for all drift outputs.

---

## §7 Q5 Drift reference period

Reference period definitions are non-overlapping with the tested quarters
(2023-Q1 through 2024-Q4) to eliminate artifactual stability.

| Dataset | Reference period | Rationale |
|---------|-----------------|-----------|
| sc2egset | 2022-08-29 to 2022-12-31 | 4 months, 1 quarter (2022-Q3/Q4 pre-tested), zero overlap with 2023-Q1 |
| aoe2companion | 2022-08-29 to 2022-12-31 | Same anchor; aoec coverage begins ~2020 so this period has adequate volume |
| aoestats | 2022-08-29 to 2022-10-27 | Single patch window (patch 66692, path-c); ~9 weekly files, ~800k matches. Patch ID corrected v1.0.3 — see §14. |

**aoestats rationale.** The aoestats reference is shortened to a single-patch
window (patch 66692, ~9 weekly ingestion files) to avoid patch-heterogeneity
within the reference distribution. This makes the aoestats reference window
asymmetric with sc2egset/aoec (9 weeks vs. 4 months). Cross-dataset
comparability is therefore asymmetric but justified: the priority is a
homogeneous reference over a comparable-length reference.

**Tested quarters:** 2023-Q1 to 2024-Q4 (8 quarters, all three datasets).

---

## §8 Q6 Variance decomposition

**Primary decomposition:** Between-player vs. within-player variance.

**Secondary decomposition:** Player × faction interaction.

**Target feature:** `won` (primary); per-dataset native rating (`rating_pre`)
as secondary if exposed and non-NULL in ≥80% of rows.

**Minimum cluster size:** 10 observations per player to contribute to the
random-intercept fit.

**Method:** `statsmodels.mixedlm` (Python) — random-intercept model with
player as the grouping variable:

```
won ~ 1 + (1 | player_id)
```

**Reporting:** Intraclass Correlation Coefficient (ICC) = between-player
variance / (between-player + within-player variance). Point estimate + 95% CI
via delta method (Gelman & Hill 2007, §12.5).

---

## §9 Q7 Temporal leakage audit (`temporal_leakage_audit_v1`)

Three queries per dataset, nine total. Each query is implemented as a named
check in the corresponding audit notebook.

**Per-dataset notebook paths:**

```
sandbox/sc2/sc2egset/01_exploration/05_temporal_panel_eda/01_05_sc2_leakage_audit.py
sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_aoec_leakage_audit.py
sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_aoestats_leakage_audit.py
```

**Query 1 — Future-data check (gate = 0 rows):**

```sql
SELECT COUNT(*) AS future_leak_count
FROM feature_source
WHERE observation_time >= match_time
```

If `future_leak_count > 0`, the step is blocked.

**Query 2 — POST_GAME token scan (gate = 0 violations):**

Perform a YAML/SQL AST scan of the feature-input list for any column
classified as `POST_GAME_HISTORICAL` or `TARGET` in the feature schema. If
any such token appears in the feature-input list, the step is blocked.

**Query 3 — Normalization-fit-window assertion:**

Assert that the fit window used for any normalization or binning (e.g., PSI
bin edges) equals the reference period defined in §7. This check is implemented
as a manual assertion in the notebook cell that computes reference statistics:

```python
assert ref_start == datetime(2022, 8, 29), f"Bad ref_start: {ref_start}"
assert ref_end == datetime(2022, 12, 31), f"Bad ref_end: {ref_end}"
# aoestats only:
# assert ref_end == datetime(2022, 10, 27), f"Bad ref_end: {ref_end}"
```

**aoestats-specific addition — `canonical_slot`-aware audit.**

Per the W3 verdict ARTEFACT_EDGE (commit `ab23ab1d`, artifact at
`src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_05_i5_diagnosis.json`):

The aoestats `matches_history_minimal` UNION-ALL mirror propagates a
skill-correlated slot assignment (`team=1` is assigned to the higher-ELO player
by the upstream API, not by local row ordering). This is NOT a game-mechanical
asymmetry — it is an upstream artifact requiring canonicalization.

Phase 02 feature engineering MUST consume a `canonical_slot` column (to be
added by a follow-up amendment; see §14). Until `canonical_slot` exists in the
`matches_history_minimal` schema:

- Any feature that conditions on `team` or any mirror-propagated row position
  is flagged `[PRE-canonical_slot]` in the notebook output.
- The aoestats leakage audit must include a fourth check:

```sql
-- Query 4 (aoestats only): canonical_slot readiness
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'matches_history_minimal'
  AND column_name = 'canonical_slot'
```

If `canonical_slot` is absent, log `[PRE-canonical_slot]` and continue (do not
block); the flag propagates to all downstream outputs.

---

## §10 Q8 Data-generating-process (DGP) diagnostics

DGP diagnostics cover features that are **NOT** pre-game in nature. These are
explicitly separated from the pre-game PSI outputs (§4) to avoid audit
confusion.

**Scope:**

- `duration_seconds` — post-game, DGP diagnostic.
- sc2egset extension: `is_duration_suspicious` (boolean corruption flag) if
  available in the dataset.

**Output per dataset × quarter:**

For each dataset and each tested quarter (plus the reference period):

1. Summary statistics: mean, median, p5, p95, IQR.
2. Cohen's d vs. reference period distribution.
3. Corruption flag rate (`is_duration_suspicious` if available; else `NULL`).

**Output file naming:** Outputs MUST use the `dgp_diagnostic_` prefix:

```
artifacts/dgp_diagnostic_<dataset_tag>_<quarter>.csv
```

The `dgp_diagnostic_` prefix distinguishes these outputs from pre-game PSI
outputs (`psi_<dataset_tag>_<quarter>.csv`) in automated artifact audits.

POST_GAME features must NOT appear in Q2 PSI files.

---

## §11 Q9 aoestats patch-anchored reference + W3 binding

**W3 verdict citation.**

The W3 diagnostic step (commit `ab23ab1d`, branch `feat/pre-01-05-cleanup`)
produced verdict **ARTEFACT_EDGE** for the aoestats team-slot asymmetry:

- Q2 CMH stratified win rate: `civ_lex_first_win_rate = 0.4928` (−0.72pp after
  stratification; below the 0.5pp ARTEFACT_EDGE ceiling).
- ELO audit: `team=1` has higher ELO in 80.3% of games (mean diff +11.9 pts).
- Root cause: upstream API assigns `team=1` to the invite-initiating /
  higher-ELO player. This is NOT a game-mechanical effect.
- Artifact: `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_05_i5_diagnosis.json`

**Patch-anchored reference justification.**

The aoestats reference period (§7) is restricted to a single game patch
(patch 66692, 2022-08-29 to 2022-10-27) to ensure a homogeneous reference
distribution. (Patch ID corrected from 125283 → 66692 in v1.0.3, see §14.) Cross-dataset comparability with sc2egset and aoec is asymmetric
on reference period length but justified by the priority of within-reference
homogeneity.

**Canonical slot requirement (binding for Phase 02).**

Per the ARTEFACT_EDGE verdict, the aoestats `matches_history_minimal` mirror
propagates the upstream skill-correlated slot assignment. The CROSS research log
entry dated 2026-04-18 records this as a cross-dataset finding. A `canonical_slot`
column must be added before any feature that conditions on player position is
used in Phase 02.

All aoestats Q1/Q2/Q5 outputs incorporate the `canonical_slot`-aware filter
once that column is added. Until then, any slot-conditioned finding is marked
`[PRE-canonical_slot]` pending the follow-up amendment.

**Lock status.** The W3 verdict is locked per commit `ab23ab1d`. If a future
re-run of the W3 diagnostic produces a different verdict (e.g., GENUINE_EDGE),
§9 and §11 of this spec would require revision under the amendment procedure
(§13, §14). Currently locked.

---

## §12 Phase 06 interface

All 01_05 outputs intended for Phase 06 (Cross-Domain Transfer) must conform
to the following flat schema. One row per (dataset × quarter × feature × metric).

**Column schema:**

| Column | Type | Notes |
|--------|------|-------|
| `dataset_tag` | VARCHAR | `sc2egset`, `aoe2companion`, `aoestats` |
| `quarter` | VARCHAR | ISO quarter string, e.g. `2023-Q1` |
| `feature_name` | VARCHAR | Column name in `matches_history_minimal` |
| `metric_name` | VARCHAR | Closed enumeration — `psi`, `cohen_h`, `cohen_d`, `ks_stat`, `icc_anova_observed_scale`, `icc_lpm_observed_scale`, `icc_glmm_latent_scale`. CI bounds are NOT valid `metric_name` values; they live in the `metric_ci_low`/`metric_ci_high` columns on the same row. |
| `metric_value` | DOUBLE | 4 decimal places; NaN encoded as `NULL` |
| `metric_ci_low` | DOUBLE NULL | Lower bound of the 95% CI for `metric_value`. NULL when no CI is computed (e.g. PSI, Cohen's h/d, KS). Populated for ICC rows with cluster-bootstrap CI (ANOVA) or delta-method CI (LMM). Spec v1.0.4. |
| `metric_ci_high` | DOUBLE NULL | Upper bound of the 95% CI for `metric_value`. Same population rule as `metric_ci_low`. Spec v1.0.4. |
| `reference_window_id` | VARCHAR | `2022-Q3Q4` or `2022-Q3-patch66692` for aoestats (corrected v1.0.3) |
| `cohort_threshold` | INTEGER NULL | Minimum-match threshold (default 10; sensitivity: 5, 20). **`0` = uncohort-filtered primary analysis** (e.g. sc2egset B2 PSI). NULL is reserved for missing metadata and MUST be fixed before Phase 06 consumption. Clarified v1.0.4. |
| `sample_size` | INTEGER | Number of (player × match) observations in this cell |
| `notes` | VARCHAR | Free-text; e.g. `[PRE-canonical_slot]`, `__unseen__: 3 rows` |

**Schema version.** 11 columns (was 9 pre-v1.0.4). A Phase 06 consumer
should assert `set(csv.columns) == 11-column-set-above` at ingest time
and reject rows with `metric_name` outside the enumerated set.

**Numeric formatting.** All `metric_value`, `metric_ci_low`, and
`metric_ci_high` entries use 4 decimal places. NaN / undefined values
are stored as SQL NULL (not strings).

**Sign conventions.** PSI ≥ 0 (always). Cohen's h and Cohen's d are signed
(positive = tested > reference on the focal statistic). KS statistic is
unsigned magnitude.

**References.** This schema feeds Manual 06 §4 (abstract feature table) and
§7 (metric registry). Manual 06 must accept this schema without transformation.

---

## §13 Binding mechanism

**Notebook docstring requirement.**

Every Python file under
`sandbox/<game>/<dataset>/01_exploration/05_temporal_panel_eda/*.py`
that implements any Q1–Q9 analysis MUST contain the following line in its
first 40 lines:

```python
# spec: reports/specs/01_05_preregistration.md@<git-SHA>
```

where `<git-SHA>` is the full or abbreviated (≥7-char) SHA of the commit that
introduced or last modified this spec file. Use `git log --oneline -1 reports/specs/01_05_preregistration.md`
to obtain the SHA after this file is committed.

**Pre-commit hook.**

The hook `scripts/check_01_05_binding.py` is registered in `.pre-commit-config.yaml`
with:

```yaml
- id: check-01-05-binding
  name: Check 01_05 notebook spec-binding
  entry: python scripts/check_01_05_binding.py --check
  language: system
  files: ^sandbox/.+/01_exploration/05_temporal_panel_eda/.+\.py$
  pass_filenames: false
  stages: [commit]
```

The hook is a no-op when no matching files are staged (Phase 01_05 not yet
begun). It exits 1 only when a matching file lacks a valid spec-binding line.

**Deviation procedure.**

Any deviation from a parameter in §3–§11 requires:

(a) A CROSS research-log entry in `reports/research_log.md` explaining the
    deviation and its scientific justification.
(b) An amendment log entry in §14 of this file.
(c) A `spec_version` minor bump (e.g. 1.0 → 1.1) committed atomically with
    the deviation.

Minor wording clarifications that do not change any parameter do not require
a version bump.

---

## §14 Amendment log

```
v1.0  — 2026-04-18 — Initial spec. 9 parameter groups locked (Q1–Q9). aoestats
                      provisions included placeholder language pending W3 verdict.

v1.0.1 — 2026-04-18 — Records W3 ARTEFACT_EDGE verdict as binding input to
                       §9/§11 aoestats provisions. No spec parameters changed.
                       Placeholder language replaced with concrete W3 citations:
                       - §9: aoestats-specific Query 4 (canonical_slot readiness)
                         added; [PRE-canonical_slot] flag protocol defined.
                       - §11: Explicit W3 verdict citation (commit ab23ab1d,
                         artifact path, ELO audit result −0.72pp CMH,
                         80.3% team=1 higher-ELO).
                       Source: W3 executor report, branch feat/pre-01-05-cleanup.

v1.0.2 — 2026-04-19 — aoe2companion-specific §8 adaptations following post-hang
                       adversarial review of PR #162 (feat/01-05-aoe2companion).
                       Reason: aoec reference window contains 54,113 eligible
                       players vs. ~750 in aoestats; `statsmodels.mixedlm`
                       cost is O(G × iter), intractable at ≥20k groups.
                       Three binding adaptations, applicable ONLY to
                       aoe2companion (sc2egset + aoestats unaffected):

                       (a) Sample-size cap for LMM fit.
                           aoec fits LMM on a stratified-reservoir sample of
                           5,000 players (primary) and 10,000 (sensitivity).
                           LMM at 20,000+ is skipped as cost-prohibitive.
                           Sample profile IDs persisted at {5k, 10k, 20k} for
                           reproducibility. Stratification: n_matches_in_ref
                           deciles (aoestats M3 pattern).

                       (b) ANOVA ICC promoted from secondary to
                           robust primary estimator at scale.
                           Rationale: REML LMM on Bernoulli outcomes near
                           τ²-boundary is known to pin at zero (Chung et al.
                           2013, Psychometrika 78(4):685-709); observed-scale
                           ANOVA ICC per Wu/Crespi/Wong 2012 CCT 33(5):869-880
                           is consistent under moment-based variance
                           decomposition and robust to boundary shrinkage.
                           aoec reports both; the ANOVA estimate is the
                           headline for cross-dataset comparison; the LMM
                           estimate is reported as a diagnostic with explicit
                           boundary-shrinkage disclosure.

                       (c) GLMM (BinomialBayesMixedGLM, latent-scale ICC) is
                           explicitly skipped for aoe2companion.
                           Rationale: MCMC/Laplace-approximated GLMM at
                           5k-group scale is compute-prohibitive (> 2h
                           wall-clock per fit on the project's hardware);
                           the ANOVA estimator (observed scale) combined
                           with explicit interpretation of `icc_lpm` as
                           Linear Probability Model ICC covers the
                           methodological gap that GLMM was to address.
                           A GLMM latent-scale cross-check remains a
                           Phase 02+ follow-up when a rating-informed model
                           is fit on a smaller cohort.

                       aoestats / sc2egset parameters unchanged:
                       aoestats runs unsampled LMM + ANOVA on ~750 players;
                       sc2egset per its existing §8 binding.

                       Source: adversarial review of PR #162, reviewer-
                       adversarial transcript 2026-04-19; executor B-01
                       critique at planning/current_plan.critique.md:15-17.

v1.0.3 — 2026-04-19 — aoestats reference-patch ID correction: 125283 → 66692.

                       Reason: empirical verification against aoestats
                       matches_raw showed that patch 125283 covers
                       2024-10-15 .. 2025-04-11 (over two years AFTER the
                       declared reference window), while patch 66692 is
                       the only patch present during the spec §7 reference
                       window [2022-08-29, 2022-10-27] (123,367 matches
                       within window, 241,981 total matches across patch
                       lifetime 2022-08-29 .. 2022-12-08). The original
                       v1.0 spec cited 125283 as the reference-window
                       patch; this was a pre-empirical-validation error
                       caught post-hoc during the pre-01_06 adversarial
                       review (2026-04-19).

                       Scope of correction — three textual edits, zero
                       parameter changes:
                       - §7 table row: "patch 125283" → "patch 66692".
                       - §7 aoestats-rationale paragraph: "patch 125283"
                         → "patch 66692".
                       - §11 patch-anchored reference justification:
                         "patch 125283" → "patch 66692".
                       - §12 Phase 06 interface reference_window_id
                         example: "2022-Q3-patch125283" → "2022-Q3-patch66692".

                       No changes to the reference-window date bounds
                       [2022-08-29, 2022-10-27] or to any other §3-§11
                       parameter. Scientific conclusions of the
                       aoestats 01_05 analyses are unchanged (they were
                       computed against patch 66692 data from the start;
                       only the spec text was drifted).

                       Flagged by: 2026-04-19 pre-01_06 reviewer-
                       adversarial transcript as I9 VIOLATION (spec
                       drift without §14 amendment). The
                       `01_05_02_psi_pre_game_features.py:67` inline
                       comment already documented the drift; this
                       amendment is the formal §13 remediation.

                       Empirical evidence (matches_raw, 2026-04-19):
                       - patch=66692: n=241,981 across
                         2022-08-29 02:00:34+02 .. 2022-12-08 00:54:29+01,
                         with 123,367 matches in window
                         [2022-08-29, 2022-10-27].
                       - patch=125283: n=5,472,044 across
                         2024-10-15 02:00:00+02 .. 2025-04-11 07:35:26+02,
                         with 0 matches in window
                         [2022-08-29, 2022-10-27].

v1.0.4 — 2026-04-19 — Cross-dataset ANOVA-primary ICC headline convention
                       (extends v1.0.2 §14(b) from aoe2companion-only to
                       sc2egset and aoestats).

                       Reason: v1.0.2 §14(b) promoted the Wu/Crespi/Wong
                       2012 ANOVA ICC estimator to primary for
                       aoe2companion on the grounds that REML LMM on
                       Bernoulli outcomes near the τ²-boundary shrinks
                       toward zero (Chung et al. 2013, Psychometrika
                       78(4):685-709). That argument is dataset-agnostic:
                       it applies equally to any Bernoulli outcome
                       (`won`) on any player cohort. Leaving sc2egset
                       and aoestats with different headline estimators
                       creates a cross-game comparability problem
                       (per I8) that the data does not justify — all
                       three datasets' notebooks already compute both
                       LMM and ANOVA; only the *headline convention*
                       differed. The 2026-04-19 pre-01_06 adversarial
                       review (DEFEND-IN-THESIS #1) flagged this as a
                       soft risk for Chapter 4.

                       Binding change: the Phase 06 interface CSV
                       headline ICC row per dataset uses
                       `metric_name = icc_anova_observed_scale`.
                       Per-dataset CSVs continue to carry
                       `icc_lpm_observed_scale` and
                       `icc_glmm_latent_scale` as diagnostics.

                       Scope — zero code change required:
                       - sc2egset: already emits `icc_anova_observed_scale`
                         in `variance_icc_sc2egset.csv` (0.0463) and in
                         `phase06_interface_sc2egset.csv`.
                       - aoe2companion: headline already ANOVA since
                         v1.0.2 §14(b); no change.
                       - aoestats: already emits
                         `icc_anova_observed_scale` in
                         `phase06_interface_aoestats.csv` (0.0268 post-
                         PR #167 cluster-bootstrap fix).

                       The three datasets' headline ICC numbers under
                       v1.0.4 are:
                       - sc2egset: 0.0463 (ANOVA)
                       - aoe2companion: 0.003013 (ANOVA, bootstrap CI
                         [0.001724, 0.004202])
                       - aoestats: 0.0268 (ANOVA, bootstrap CI
                         [0.0145, 0.0407])

                       These are directly comparable as observed-scale
                       ICCs on the same outcome (`won`) under the same
                       estimator (Wu/Crespi/Wong 2012 ANOVA). LMM
                       estimates remain recorded in per-dataset
                       artifacts as diagnostics, with disclosure of
                       the boundary-shrinkage caveat (Chung 2013).

                       Chapter 4 framing: the observed-scale ANOVA
                       ICC is reported as the cross-game headline
                       because (a) it is the consistent moment
                       estimator for the one-way random-effects ANOVA
                       model, (b) it does not suffer REML
                       boundary-shrinkage on Bernoulli outcomes with
                       small τ², and (c) all three datasets compute
                       it natively. The latent-scale conversion
                       (Nakagawa et al. 2017) is noted as a caveat in
                       the methods paragraph; a thesis examiner asking
                       for latent-scale ICC is answered with "observed-
                       scale is a lower bound on the latent-scale
                       quantity under a logit link with small τ²; the
                       cross-game *directional* claim survives the
                       transformation."

                       Source: 2026-04-19 pre-01_06 adversarial review
                       (DEFEND-IN-THESIS #1) + planner-science
                       consolidated methodology plan 2026-04-19.

v1.0.5 — 2026-04-19 — Phase 06 interface schema harmonization: 9 → 11
                       columns; `cohort_threshold=0` sentinel for
                       uncohort-filtered primary analyses.

                       Reason: 2026-04-19 pre-01_06 adversarial review
                       flagged Phase 06 CSV semantic drift across datasets
                       (DEFEND-IN-THESIS #3a, #3b):

                       (a) sc2egset emitted `cohort_threshold=""` (empty /
                           NULL) on 24 PSI rows, ambiguous between
                           "uncohort-filtered B2-primary" and "missing
                           metadata". NULL-is-a-semantic-value is an
                           antipattern.

                       (b) aoe2companion encoded CI bounds as separate
                           rows with `metric_name=icc_lpm_ci_low` and
                           `metric_name=icc_lpm_ci_high`. These names
                           were not in the spec §12 enumerated set. A
                           schema-validating consumer that filtered
                           `metric_name IN (spec_enum)` silently dropped
                           the CI rows. Schema-valid but semantically
                           broken.

                       Binding schema changes (scoped to §12):

                       1. Add two columns: `metric_ci_low DOUBLE NULL`
                          and `metric_ci_high DOUBLE NULL`. CI bounds
                          for a metric now live in these columns on the
                          same row as the metric, not as separate rows.

                       2. `metric_name` enumeration is now CLOSED:
                          `{psi, cohen_h, cohen_d, ks_stat,
                          icc_anova_observed_scale, icc_lpm_observed_scale,
                          icc_glmm_latent_scale}`. Consumers MUST reject
                          rows with out-of-enumeration values.

                       3. `cohort_threshold=0` = uncohort-filtered
                          primary analysis (e.g. sc2egset B2 PSI).
                          Positive values (5/10/20) = §6.2 thresholds.
                          NULL = missing metadata (block at ingest).

                       Notebook changes (three emitters + one consumer-
                       side validator):

                       - sc2egset Phase 06 notebook emits
                         `cohort_threshold=0` on all B2-uncohort rows;
                         populates `metric_ci_low`/`metric_ci_high`
                         from `variance_icc_sc2egset.csv` on ICC rows.
                       - aoe2companion Phase 06 notebook stops emitting
                         `icc_lpm_ci_low`/`icc_lpm_ci_high` as separate
                         rows; inlines CI bounds into the primary ICC
                         row's CI columns.
                       - aoestats Phase 06 notebook populates
                         `metric_ci_low`/`metric_ci_high` for each of
                         the 6 per-threshold ICC rows (post-v1.0.4
                         structure) from the cluster-bootstrap CI
                         (ANOVA) or delta-method CI (LMM).

                       Impact on downstream Phase 06 consumption:
                       the three emitted CSVs now join cleanly on
                       `(dataset_tag, quarter, feature_name, metric_name)`
                       with CI semantics uniform; `cohort_threshold`
                       values distinguishable.

                       Source: 2026-04-19 pre-01_06 adversarial review
                       (DEFEND-IN-THESIS #3a, #3b) + planner-science
                       consolidated methodology plan 2026-04-19.
```

---

## §15 W3/follow-up trigger

The aoestats provisions in §9 and §11 are locked per commit `ab23ab1d` of the
W3 diagnostic. If a future re-run of the W3 diagnostic (e.g., after schema
changes or data updates) produces a verdict other than ARTEFACT_EDGE, the
following sections would require revision under the §13 amendment procedure:

- §9 — aoestats-specific Query 4 and `[PRE-canonical_slot]` protocol.
- §11 — W3 verdict citation, CMH result, ELO audit figures.

No other sections are affected by a W3 verdict change.

The `canonical_slot` column follow-up (Phase 02 amendment) is tracked
separately and does not require a spec revision — it will be recorded as a
follow-up step in the Phase 02 plan.

---

## §16 Literature references

Where possible, BibTeX keys below match entries in `thesis/references.bib`.

| Reference | BibTeX key | Relevance |
|-----------|-----------|-----------|
| Hamilton, J.D. (1994). *Time Series Analysis*. Princeton UP. §17.7. | `hamilton1994` | ADF/KPSS power properties; justification for N=8 cross-dataset prohibition. |
| Siddiqi, N. (2006). *Credit Risk Scorecards*. Wiley. | `siddiqi2006` | PSI definition, equal-frequency binning, threshold table (0.1/0.25). |
| Breck, E. et al. (2019). Data Validation for Machine Learning. *SysML*. | `breck2019` | TFDV PSI implementation reference; KS descriptive magnitude. |
| Gelman, A. & Hill, J. (2007). *Data Analysis Using Regression and Multilevel/Hierarchical Models*. Cambridge UP. | `gelman2007` | ICC definition and delta-method CI (§12.5). |
| Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). LEA. | `cohen1988` | h (binary, §6.2) and d (continuous, §2.2) effect-size definitions and thresholds. |
| Mantel, N. & Haenszel, W. (1959). Statistical aspects of the analysis of data from retrospective studies of disease. *JNCI* 22(4), 719–748. | `mantel1959` | CMH test used in W3 diagnostic. |
| Robins, J.M., Breslow, N.E., & Greenland, S. (1986). Estimators of the Mantel-Haenszel variance consistent in both sparse data and large-strata limiting models. *Biometrics* 42(2), 311–323. | `robins1986` | CMH confidence interval method used in W3 diagnostic. |
