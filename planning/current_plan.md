---
# Layer 1 — fixed frontmatter (mechanically validated)
category: F
branch: docs/thesis-ch4-stat-methodology-residuals
date: 2026-04-19
planner_model: claude-opus-4-7
dataset: null
phase: null
pipeline_section: null
invariants_touched: [I8]
source_artifacts:
  - planning/CHAPTER_4_DEFEND_IN_THESIS.md
  - thesis/chapters/04_data_and_methodology.md
  - thesis/chapters/REVIEW_QUEUE.md
  - thesis/WRITING_STATUS.md
  - thesis/references.bib
  - reports/specs/01_05_preregistration.md
  - src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/phase06_interface_sc2egset.csv
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_phase06_interface_aoe2companion.csv
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/phase06_interface_aoestats.csv
  - src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_05_icc_results.json
  - .claude/scientific-invariants.md
  - .claude/rules/thesis-writing.md
  - docs/templates/plan_template.md
critique_required: true
research_log_ref: null
---

# Plan: Chapter 4 DEFEND-IN-THESIS residuals — stat methodology (PR-2 of 3)

## Scope

Second of three Cat F PRs addressing the six DEFEND-IN-THESIS residuals
from `planning/CHAPTER_4_DEFEND_IN_THESIS.md`. This PR covers **two
methodology residuals (#3, #6)** plus a full draft of the §4.4.4
Evaluation metrics subsection (which was DRAFTABLE skeleton at master
`c5e2a5cf` and whose literature-ready content was pre-drafted in the
skeleton comments). Writer-thesis also creates **NEW §4.4.5 "Wybór
estymatora ICC"** hosting Tabela 4.7 (three-dataset ICC headline
reconciliation) and resolves the forward-refs planted by PR-1 at
§4.1.2.1 and §4.1.4. PR-3 (docs/thesis-ch4-canonical-slot-flag) follows
this PR.

## Problem Statement

PR-1 merged `docs/thesis-ch4-corpus-framing-residuals` (master
`c5e2a5cf`) with three forward-refs pointing at §4.4.4, §4.4.5, and
§4.4.6 — sections that do not yet exist on master. This PR closes two
of those three forward-refs by:

1. **Drafting §4.4.4 Evaluation metrics (DRAFTABLE → DRAFTED).** The
   skeleton comments already name the structure: primary (Brier score
   + Murphy decomposition + log-loss), discrimination (accuracy,
   ROC-AUC, ECE), stratified (per-matchup, cold-start, sharpness),
   within-game (Friedman omnibus + Wilcoxon-Holm + Bayesian
   signed-rank), cross-game (per-game rankings + bootstrapped CIs +
   5×2 cv F-test + qualitative concordance). **Residual #6** (N=2
   cross-game statistical-test inapplicability) is absorbed as the
   closing paragraph of §4.4.4, citing [Demsar2006] (already in
   `references.bib` line 136 — REUSE, do not re-introduce) and
   invariant #8. The examiner question "how do you statistically
   compare your two games?" is answered here.

2. **Creating NEW §4.4.5 Wybór estymatora ICC (including Tabela 4.7).**
   The subsection defends the choice of **observed-scale ANOVA ICC**
   as the cross-dataset-comparable headline estimator despite the
   Nakagawa 2017 theoretical argument that latent-scale GLMM ICC is
   preferable for Bernoulli outcomes under a logit link. The defense
   argument (per DEFEND doc Residual #3): latent-scale GLMM ICC
   requires MCMC estimation that is compute-prohibitive at aoestats
   scale (744 groups achievable; aoe2companion 360,567 observations
   at 5 000 stratified sample intractable under project compute budget)
   and failed convergence on sc2egset (`BayesMixedGLMResults` attribute
   issue). Observed-scale ICC is a **lower bound** on latent-scale ICC
   via `ICC_latent = ICC_observed / (ICC_observed + π²/3)`; the
   directional claim "ICC on `won` is small in all three datasets"
   survives the link transformation. Tabela 4.7 presents the
   three-dataset reconciliation (verified from Phase 06 CSVs):
   sc2egset 0.0463 [0.0283, 0.0643] / aoe2companion 0.003
   [0.0017, 0.0042] / aoestats 0.0268 [0.0148, 0.0387], all at
   cohort_threshold N=10 default per spec §6.3.

3. **Resolving PR-1's §4.1.2.1 forward-ref (Residual #4
   identification-side).** PR-1 forward-referenced §4.4.5 for the
   identification-side ICC defense (Gelman & Hill 2007 §11-12:
   "ICC point estimates reasonable with 20–50 clusters"). PR-2 §4.4.5
   makes this defense explicit: at n=744 aoestats groups the ANOVA
   ICC point estimate is well-identified; the cohort ceiling widens
   the CI, does not bias the point. This is the substantive
   identification argument that PR-1's isolated-reading-vulnerable
   §4.1.2.1 defensive sentence forward-references.

Four new bibtex entries are introduced (Nakagawa2017, Chung2013,
Ukoumunne2012, WuCrespiWong2012, Gelman2007). [Demsar2006] stays
reused from §2.6. Literature Search Protocol mandatory per
`.claude/rules/thesis-writing.md` (Literature variant of Critical
Review Checklist) — writer-thesis must WebSearch each new bibkey
before citing.

## Assumptions & unknowns

- **Assumption:** Tabela 4.7 numbers are post-v1.0.5 spec-locked
  (confirmed from Phase 06 CSVs at master `c5e2a5cf`). The sc2egset
  `metric_ci_low = 0.0283` and `metric_ci_high = 0.0643` — verified
  from row 1 of `phase06_interface_sc2egset.csv`. These CIs may be
  delta-method (per DEFEND doc line 205) rather than cluster-bootstrap;
  writer-thesis must confirm from the sc2egset JSON artifact and
  label the CI method in Tabela 4.7 footnote.
- **Assumption:** aoe2companion ICC 0.003 is the rounded headline;
  the JSON artifact almost certainly carries higher precision
  (0.003013 per DEFEND doc line 206). Writer-thesis prefers JSON
  precision over CSV display precision.
- **Assumption:** §4.4.4 skeleton comments (lines 357–368) capture
  the intended structure accurately. Writer-thesis expands each
  comment into prose, not deviates.
- **Assumption:** [Demsar2006] is already in `references.bib`
  (line 136, verified). Do NOT re-add.
- **Unknown:** Whether §4.4.5 should report latent-scale GLMM ICC
  where convergence succeeded (aoe2companion `icc_lpm` at n=360,567).
  Resolves by: DEFEND doc line 89 "reported only where it converges
  (aoec skipped per spec v1.0.2 §14(c); sc2egset attempted but
  BayesMixedGLMResults attribute issue)" — writer-thesis cites the
  convergence status explicitly in §4.4.5 rather than suppressing
  negative result.
- **Unknown:** Target Polish char count for §4.4.4 vs §4.4.5.
  Planner-science estimated ~6.0k total. Recommended split: ~3.5k
  for §4.4.4 (rich evaluation-metric literature), ~2.5k for §4.4.5
  (tighter methodology). PR-1's round-2 review flagged char overage
  (59% over budget) — budget for PR-2 deliberately includes 30% buffer.

## Literature context

Primary citations (writer-thesis WebSearches each before citing per
Literature Search Protocol):

- **[Nakagawa2017]** — Nakagawa S., Johnson P.C.D., Schielzeth H.,
  "The coefficient of determination R² and intra-class correlation
  coefficient from generalized linear mixed-effects models revisited
  and expanded", *J. R. Soc. Interface* 14(134):20170213 (2017).
  DOI: 10.1098/rsif.2017.0213. Canonical reference for the
  observed-scale vs latent-scale ICC conversion under GLMM. NEW bibkey.

- **[Chung2013]** — Chung Y., Rabe-Hesketh S., Choi I.-H.,
  "Avoiding zero between-study variance estimates in random-effects
  meta-analysis", *Stat. Med.* 32(23):4071–4089 (2013). Canonical
  reference for REML boundary-shrinkage pathology justifying ANOVA
  primary estimator over LMM for small-variance ICC. NEW bibkey.

- **[Ukoumunne2003]** — Ukoumunne O.C., Davison A.C., Gulliford M.C.,
  Chinn S., "Non-parametric bootstrap confidence intervals for the
  intraclass correlation coefficient", *Stat. Med.* 22(24):3805–3821
  (2003). Canonical reference for cluster-bootstrap CI method used
  for aoestats + aoe2companion ICC CIs. **(m3 fix: bibkey resolved
  to `Ukoumunne2003` pre-execution — PMC accession PMC3426610 is a
  2012 free-PMC accession of the 2003 paper, not a distinct 2012
  publication.)** NEW bibkey.

- **[WuCrespiWong2012]** — Wu S., Crespi C.M., Wong W.K., "Comparison
  of methods for estimating the intraclass correlation coefficient
  for binary responses in cancer prevention cluster randomized trials",
  *Contemp. Clin. Trials* 33(5):869–880 (2012). DOI:
  10.1016/j.cct.2012.05.004. Canonical reference for ANOVA ICC for
  Bernoulli outcomes — the primary-estimator methodology citation.
  NEW bibkey.

- **[Gelman2007]** — Gelman A., Hill J., *Data Analysis Using
  Regression and Multilevel/Hierarchical Models*, Cambridge University
  Press (2007). §11-12 on identification of ICC with few clusters.
  Cited for residual #4 identification-side defense (n=744 is reasonable).
  NEW bibkey.

- **[Demsar2006]** (existing) — reused for residual #6 N=2 Friedman
  inapplicability paragraph. Already in §2.6.

`[OPINION]`: the four new-bibkey additions in this PR bring the
Chapter 4 citation density to the planner-science-estimated 2–4
references per page (at ~6.0k Polish chars across §4.4.4 and §4.4.5,
six new or reused bibkeys, this equals ~4 refs per 1k chars
= approximately 2–3 refs per printed page at 2k chars/page).

## Execution Steps

### T01 — §4.4.4 Evaluation metrics full draft (DRAFTABLE → DRAFTED; residual #6 inline)

**Objective:** Expand the §4.4.4 skeleton (lines 357–368 at master
`c5e2a5cf`) into a full Polish-language subsection covering primary
metrics (Brier + Murphy decomposition + log-loss), discrimination
(accuracy, ROC-AUC, ECE), stratified analysis (per-matchup, cold-start,
sharpness), within-game statistical comparison (Friedman omnibus +
Wilcoxon-Holm + Bayesian signed-rank on CV folds), and cross-game
qualitative comparison (per-game rankings with bootstrapped CIs +
5×2 cv F-test + concordance). The closing paragraph absorbs **Residual
#6** (N=2 cross-game statistical-test inapplicability), citing
[Demsar2006] and invariant #8.

**Instructions:**
1. Read §4.4.4 skeleton comments (lines 357–368) in full. Read
   existing §2.6 (Evaluation metrics, Pass 1 calibration draft per
   WRITING_STATUS) to ensure Chapter-2 / Chapter-4 cross-consistency;
   §4.4.4 operationalizes what §2.6 introduces theoretically.
2. Draft 4 Polish subsections under `### 4.4.4 Evaluation metrics`:
   - (a) `**Metryki podstawowe.**` (~700–900 chars) Brier score +
     Murphy decomposition (reliability + resolution + uncertainty);
     log-loss; definitions, motivation, interpretation. Cite
     [Brier1950], [Murphy1973] (both already in §2.6, reuse).
   - (b) `**Metryki dyskryminacyjne.**` (~400–600 chars) accuracy,
     ROC-AUC, calibration curves (ECE). Cite [HanleyMcNeil1982]
     (ROC-AUC; already in §2.6, reuse).
   - (c) `**Analizy stratyfikowane.**` (~600–800 chars) per-matchup
     (SC2 only), cold-start strata (both games), sharpness histograms.
     Forward-refs §4.3 feature engineering (cold-start defined there).
   - (d) `**Porównanie within-game i cross-game.**` (~900–1 100
     chars) Two-level framing:
     - **Within-game (N_folds ≥ 5):** Friedman omnibus +
       Wilcoxon-Holm per-metric post-hoc; Bayesian signed-rank via
       `baycomp` [Benavoli2017]; 5×2 cv F-test [Dietterich1998] or
       Nadeau-Bengio corrected t-test [Nadeau2003] where temporal
       splits violate IID assumption. All bibkeys reused from §2.6.
     - **Cross-game (N=2 games — Residual #6):** per-game rankings
       with bootstrapped CIs + qualitative concordance paragraph.
       **(M4 fix — attribute Demsar claim precisely.)** Cite
       [Demsar2006] §3.2 for the **dataset-count requirement**
       (Friedman asymptotic approximation requires N ≥ 10 datasets
       and k ≥ 5 classifiers); derive the N=2 inapplicability as a
       corollary (Friedman at N=2 reduces to a sign-test with no
       resolving power). Do NOT attribute "N=2 inapplicable" as
       a direct quote from Demsar 2006 — that specific framing is
       absent from §3. Cross-reference invariant #8
       (`.claude/scientific-invariants.md`, cross-game section)
       for project-internal N=2 framing. Frame as "we report
       per-game effect sizes + bootstrapped CIs, then qualitatively
       describe whether conclusions concur across SC2 and AoE2 — no
       cross-game p-values".
3. Plant 2 flags total:
   - `[REVIEW: Pass-2 — 5×2 cv F-test under temporal split; verify
     Polish idiom for "temporal-split IID-violation"]` at end of (d).
   - `[REVIEW: Pass-2 — Demsar 2006 N=2 argument; verify against
     invariant #8 wording]` at the Residual #6 paragraph.
4. Update `thesis/chapters/REVIEW_QUEUE.md`: §4.4.4 row does not yet
   exist (it is DRAFTABLE on master); add a new Pending row for §4.4.4.
5. Update `thesis/WRITING_STATUS.md`: §4.4.4 row status
   `DRAFTABLE → DRAFTED`, extend Notes with 2026-04-19 date + char
   count + flag count + Residual #6 reference.

**Verification:**
- §4.4.4 has 4 bolded subsections (`**Metryki podstawowe.**`,
  `**Metryki dyskryminacyjne.**`, etc.).
- Residual #6 N=2 argument is present as the closing paragraph of
  subsection (d), citing [Demsar2006] and invariant #8.
- No new bibtex entries introduced at this step (T01 reuses existing).
- Total Polish chars: 2 600–3 400 (with 30% buffer from planner-science
  ~3k estimate — widened after PR-1 round-2 char-overage lesson).
- Flag count: 2.
- REVIEW_QUEUE has new §4.4.4 Pending row.
- WRITING_STATUS §4.4.4 row status DRAFTED.

**File scope:**
- `thesis/chapters/04_data_and_methodology.md` (§4.4.4 only)
- `thesis/chapters/REVIEW_QUEUE.md`
- `thesis/WRITING_STATUS.md`

**Read scope:**
- `planning/CHAPTER_4_DEFEND_IN_THESIS.md` Residual #6
- `.claude/scientific-invariants.md` #8
- `thesis/chapters/02_theoretical_background.md` §2.6 (for
  Chapter-2/Chapter-4 cross-consistency)

---

### T02 — NEW §4.4.5 Wybór estymatora ICC + Tabela 4.7 (Residual #3 + Residual #4 identification)

**Objective:** Create new subsection `### 4.4.5 Wybór estymatora ICC`
after §4.4.4. Defends observed-scale ANOVA ICC as the
cross-dataset-comparable headline estimator. Hosts Tabela 4.7
(three-dataset ICC reconciliation). Closes the two forward-refs from
PR-1 (§4.1.2.1 and §4.1.4).

**Instructions:**
1. Read §4.1.2.1 post-PR-1 state (containing the 744-player paragraph
   + M1 defensive sentence forward-ref to §4.4.5). Read §4.1.4 post-
   PR-1 state (containing the forward-ref to §4.4.4 and §4.4.5).
   Confirm the writer-thesis understands what §4.4.5 must resolve.
2. Verify Tabela 4.7 numbers from authoritative JSON artifacts (prefer
   JSON precision over CSV):
   - sc2egset: read `src/rts_predict/games/sc2/datasets/sc2egset/
     reports/artifacts/01_exploration/05_temporal_panel_eda/*.json`
     (find the ICC-results JSON) to confirm 0.0463 and CI method.
   - aoe2companion: read `src/rts_predict/games/aoe2/datasets/
     aoe2companion/reports/artifacts/01_exploration/05_temporal_panel_eda/
     *.json` for full-precision headline (0.003013 per DEFEND doc
     line 206).
   - aoestats: already verified — 0.0268 [0.0148, 0.0387] from
     `01_05_05_icc_results.json` line 38–40 (n_min10).
3. Draft 4 Polish subsections under `### 4.4.5 Wybór estymatora ICC`:
   - (a) `**Motywacja.**` (~500–700 chars) Why ICC on `won` appears
     as a headline — probe for cluster-level variance structure;
     forward-ref to §4.4.4 target estimand; per-dataset ICC hypothesis
     test is the **pre-registered falsifier** from spec §14(b)
     (directional test "ICC(won) ∈ [0.05, 0.20]"; see
     `01_05_05_icc_results.json:12` `"falsifier_verdict": "FALSIFIED"`).
     **(M1 fix — NOT invariant #5; invariant #5 is symmetric player
     treatment, not matchmaking-equalization.)** The
     matchmaking-equalization hypothesis is a *generated hypothesis*
     from aoe2companion research log (2026-04-19,
     `reports/research_log.md:120, 129, 246`); thesis prose cites
     the falsifier mechanism (spec §14(b) pre-registration), not an
     invariant that does not cover the topic. Cite forward-ref
     residual #4 (§4.1.2.1 744-player context).
   - (b) `**Wybór observed-scale vs. latent-scale ICC (Residual #3).**`
     (~800–1 000 chars) The core defense:
     - State observed-scale ANOVA per [WuCrespiWong2012] as primary
       across all three datasets.
     - Cite [Nakagawa2017] for the Bernoulli/logit-link theoretical
       argument that latent-scale ICC is preferable — then
       explicitly argue compute-budget constraints: **(m4 fix —
       corrected attribution)** aoe2companion GLMM was skipped per
       spec v1.0.2 §14(c) (MCMC at 5k-group scale compute-prohibitive,
       note from `01_05_05_icc.json:26` `glmm_skip_note` field);
       sc2egset attempted GLMM but failed on `BayesMixedGLMResults`
       attribute issue; aoestats GLMM status is unspecified in
       `01_05_05_icc_results.json` (writer-thesis checks alternative
       artifact or cites "not attempted").
     - **(B1 fix — NO formula written; directional argument only)**
       Do NOT write a plug-in formula like `ICC_latent = ICC_observed /
       (...)` — such a formula would be dimensionally incoherent and
       would also give the wrong direction. Instead make the
       directional claim only: under a logit link with small cluster
       variance, the **latent-scale ICC is systematically larger than
       the observed-scale ICC** per [Nakagawa2017] §2.2 and Browne
       et al. 2005. Therefore the observed-scale ICC reported as
       headline is a **lower bound** on the latent-scale quantity;
       the directional claim "ICC on `won` is small in all three
       datasets" survives the link transformation.
     - Plant a `[REVIEW: Pass-2 — zweryfikować kierunkowość
       lower-bound claim pod logitowym linkiem; cytowanie
       [Nakagawa2017] §2.2 + Browne 2005 bez plug-in formuły]`
       flag at end of this paragraph.
   - (c) `**REML boundary-shrinkage i primary-estimator fallback
     (Chung 2013).**` (~500–700 chars) Why ANOVA is primary not LMM:
     cite [Chung2013] for the REML boundary-shrinkage pathology that
     makes LMM variance estimates unreliable near zero ICC. The
     aoe2companion ICC (0.003) sits very close to the REML boundary;
     ANOVA is the preferred estimator. [Ukoumunne2003] for the
     cluster-bootstrap CI method used in aoe2companion and aoestats.
   - (d) `**Identyfikacja przy małych kohortach (Residual #4
     cross-reference).**` (~400–600 chars) Closes the §4.1.2.1
     forward-ref. Cite [Gelman2007] §11-12: ICC point estimate is
     well-identified with 20–50 clusters. At aoestats n=744, the
     point is well-identified; the cohort ceiling widens the CI, does
     not bias the point. This is the substantive argument the PR-1
     defensive sentence forward-referenced.
4. Insert **Tabela 4.7** after subsection (b) or (c):

   **Tabela 4.7.** Headline ICC ANOVA observed-scale, trzy korpusy.
   **(M3 fix — split N into graczy vs obs.; M2 fix — spec v1.0.4 not v1.0.5.)**

   | Korpus | ICC punktowa | 95% CI | N (graczy) | N (obs.) | Metoda CI |
   |---|---:|---|---:|---:|---|
   | SC2EGSet | 0,0463 | [0,0283, 0,0643] | [verify from sc2egset JSON during T02; writer-thesis confirms player count] | 4 034 | [verify method from sc2egset JSON; DEFEND doc line 206 suggests delta-method from `variance_icc_sc2egset.csv`] |
   | aoe2companion | 0,003013 | [0,001724, 0,004202] | 5 000 | 360 567 | cluster-bootstrap [Ukoumunne2003] |
   | aoestats | 0,0268 | [0,0148, 0,0387] | 744 | 7 909 | cluster-bootstrap [Ukoumunne2003] |

   Primary estimator: ANOVA observed-scale per [WuCrespiWong2012],
   **spec `reports/specs/01_05_preregistration.md` v1.0.4 §14(b)**
   (introduction carried through v1.0.5; v1.0.5 §14 added
   schema-harmonization rules, not estimator primacy). Directly
   comparable across korpusy mimo różnic w szerokości CI (refleksują
   rozmiar kohorty + różnice metody CI — szczegóły sekcja (c)).
   **(m2 fix — methodology-preview framing strengthened.)**
   Wartości prezentowane tu ilustrują spójność cross-dataset
   estymatora; pełna analiza wyników (w szczególności interpretacja
   znaczenia small ICC dla hipotezy matchmaking-equalization
   omawianej w aoe2companion research log) znajduje się w rozdziale 5.
   §4.4.5 NIE używa języka interpretacyjnego typu "ICC jest mały",
   "matchmaking equalizuje" — wszystkie interpretacje odroczone
   do rozdziału 5.
5. Plant 3 flags:
   - `[REVIEW: Pass-2 — observed-scale jako lower-bound claim pod
     logitowym linkiem; weryfikacja wzoru Nakagawa 2017
     ICC_latent = ICC_observed / (ICC_observed + π²/3)]` at end of (b).
   - `[REVIEW: Pass-2 — Chung 2013 REML boundary-shrinkage przy
     aoe2companion ICC ~0,003; weryfikacja wpływu na wybór
     estymatora primary]` at end of (c).
   - `[REVIEW: Pass-2 — Tabela 4.7 CI method dla sc2egset; JSON
     może nie wskazywać cluster-bootstrap (DEFEND doc line 205
     sugeruje "delta-method")]` at Tabela 4.7 caption.
6. Update `thesis/chapters/REVIEW_QUEUE.md`: add new Pending row for
   §4.4.5.
7. Update `thesis/WRITING_STATUS.md`: add new row for §4.4.5 between
   §4.4.4 and §4.4.6 (placeholder — §4.4.6 does not exist; §4.4.5
   slots between §4.4.4 DRAFTED and the next DRAFTABLE or SKELETON
   row, which is likely §4.4.4 itself followed by end-of-§4.4).

**Verification:**
- §4.4.5 header level is `###` (sibling to §4.4.4). Per post-PR-1 B2
  heuristic.
- Tabela 4.7 has exactly 3 data rows + header + caption.
- Numbers in Tabela 4.7 match JSON artifacts (writer-thesis verifies
  during drafting).
- Five bibkey citations present: [WuCrespiWong2012], [Nakagawa2017],
  [Chung2013], [Ukoumunne2003], [Gelman2007].
- Residual #3 defense (observed-scale → latent-scale) is explicit.
- Residual #4 identification-side forward-ref is closed.
- Flag count: 3.
- REVIEW_QUEUE has new §4.4.5 Pending row.
- WRITING_STATUS has new §4.4.5 row `DRAFTED`.
- Total Polish chars §4.4.5: 2 200 – 3 000 (with 30% buffer from
  planner-science ~2.5k estimate).

**File scope:**
- `thesis/chapters/04_data_and_methodology.md` (NEW §4.4.5)
- `thesis/chapters/REVIEW_QUEUE.md`
- `thesis/WRITING_STATUS.md`

**Read scope:**
- `planning/CHAPTER_4_DEFEND_IN_THESIS.md` Residual #3 + #4
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/` (JSON artifact for sc2egset ICC + CI method)
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/05_temporal_panel_eda/` (JSON artifact for aoe2companion ICC + CI method)
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_05_icc_results.json` (aoestats)
- `reports/specs/01_05_preregistration.md` §14(b) (ANOVA-primary declaration)

---

### T03 — references.bib additions (4 NEW bibkeys + Gelman2007)

**Objective:** Add 4 new bibtex entries (Nakagawa2017, Chung2013,
Ukoumunne2012, WuCrespiWong2012) + [Gelman2007] textbook entry to
`thesis/references.bib`. Writer-thesis WebSearches each entry per
Literature Search Protocol before committing to the bibkey / year.

**Instructions:**
1. WebSearch each of the 4 new entries. Confirm:
   - [Nakagawa2017] — DOI 10.1098/rsif.2017.0213, J. R. Soc. Interface,
     year 2017, all three authors (Nakagawa, Johnson, Schielzeth).
   - [Chung2013] — Stat. Med. 32(23):4071–4089, year 2013, authors
     Chung, Rabe-Hesketh, Choi. Verify title exactly.
   - [Ukoumunne2003] — resolve year discrepancy (paper published 2003
     in Stat. Med.; PMC accession may be 2012). Use publication year,
     not PMC year.
   - [WuCrespiWong2012] — Contemp. Clin. Trials 33(5):869–880, year
     2012, authors Wu, Crespi, Wong.
   - [Gelman2007] — Gelman & Hill, textbook, Cambridge Univ. Press,
     year 2007, chapter citation §11–12.
2. Append entries to `thesis/references.bib` in the existing format
   (alphabetical or chronological — match existing convention). Tag
   each entry with a comment `% Added 2026-04-19 via PR
   docs/thesis-ch4-stat-methodology-residuals (DEFEND-IN-THESIS PR-2)`.
3. If any WebSearch fails to confirm a critical field (DOI, volume,
   pages, year), plant `[UNVERIFIED: WebSearch unavailable]` in the
   draft §4.4.4 or §4.4.5 where the entry is cited and leave a
   `[REVIEW]` flag for Pass-2 resolution. Do NOT invent citations.

**Verification:**
- `thesis/references.bib` has 5 new entries (4 new + Gelman2007).
- Each entry has a YYYY year matching the primary publication year.
- Each entry has a DOI (except Gelman2007 textbook — ISBN acceptable).
- bibkey naming convention matches existing entries (AuthorYear or
  AuthorYearKeyword).

**File scope:**
- `thesis/references.bib`

**Read scope:**
- `thesis/references.bib` (existing entries for style/format match)
- WebSearch (per Literature Search Protocol)

---

### T04 — Wrap-up: version bump + CHANGELOG + DEFEND checkbox flip

**Objective:** Bump `pyproject.toml` 3.24.0 → 3.25.0, add CHANGELOG
`[3.25.0]` entry, and **(m6 fix — flip DEFEND checkboxes)** mark
residuals #3 and #6 as `[x]` done in
`planning/CHAPTER_4_DEFEND_IN_THESIS.md`. No TBD backfills needed
(housekeeping commit on this branch already backfilled `[3.24.0]` →
PR #175).

**Instructions:**
1. Edit `pyproject.toml` line 3: `version = "3.24.0"` → `version = "3.25.0"`.
2. Edit `CHANGELOG.md`:
   - Insert `[3.25.0] — 2026-04-19 (PR #TBD: docs/thesis-ch4-stat-methodology-residuals)`
     block between `[Unreleased]` and `[3.24.0]`.
   - Under `[3.25.0]` `### Changed`, list the residuals addressed
     (#3, #6), the new §4.4.4 DRAFTED subsection, the new §4.4.5
     subsection, Tabela 4.7, and the 5 new bibtex entries.
3. **(m6 fix)** Edit `planning/CHAPTER_4_DEFEND_IN_THESIS.md` — flip
   checkboxes for residuals #3 and #6:
   - `- [ ] Residual #3 — observed- vs latent-scale ICC` → `[x] ... (PR #TBD, §4.4.5)`
   - `- [ ] Residual #6 — N=2 cross-game statistical-test limit` → `[x] ... (PR #TBD, §4.4.4)`
4. Commit with message `chore(release): bump version to 3.25.0`.

**Verification:**
- `pyproject.toml` shows `version = "3.25.0"`.
- CHANGELOG `[3.25.0]` section exists between `[Unreleased]` and
  `[3.24.0]`.
- DEFEND doc checkboxes #3 and #6 flipped to `[x]`.

**File scope:**
- `pyproject.toml`
- `CHANGELOG.md`
- `planning/CHAPTER_4_DEFEND_IN_THESIS.md`

**Read scope:**
- (none — self-contained admin step)

---

## File Manifest

| File | Action |
|------|--------|
| `thesis/chapters/04_data_and_methodology.md` | Update (§4.4.4 DRAFTABLE→DRAFTED; NEW §4.4.5) |
| `thesis/chapters/REVIEW_QUEUE.md` | Update (2 new Pending rows: §4.4.4 + §4.4.5) |
| `thesis/WRITING_STATUS.md` | Update (§4.4.4 DRAFTABLE→DRAFTED + new §4.4.5 row) |
| `thesis/references.bib` | Update (5 new entries: Nakagawa2017, Chung2013, Ukoumunne2003, WuCrespiWong2012, Gelman2007) |
| `pyproject.toml` | Update (version 3.24.0 → 3.25.0) |
| `CHANGELOG.md` | Update (new `[3.25.0]` entry) |
| `planning/CHAPTER_4_DEFEND_IN_THESIS.md` | Update (flip residuals #3 + #6 checkboxes per m6 fix) |
| `planning/current_plan.md` | Update (this file — commit as provenance) |
| `planning/current_plan.critique.md` | Create (reviewer-adversarial output) |

## Gate Condition

- §4.4.4 and §4.4.5 present in `thesis/chapters/04_data_and_methodology.md`
  at the specified slots.
- Residual #3 defense is substantive (observed-scale vs latent-scale
  argument cited via [Nakagawa2017] + Browne 2005 — **directional
  lower-bound only, NO plug-in formula per B1 fix**).
- Residual #6 N=2 argument is substantive ([Demsar2006] §3.2 cited for
  N ≥ 10 requirement; N=2 derived as corollary per M4 fix; invariant #8
  cross-referenced).
- Residual #4 identification-side defense is substantive ([Gelman2007]
  §11-12 at §4.4.5 subsection d, closing PR-1's §4.1.2.1 forward-ref).
- Tabela 4.7 with 3 data rows correctly reflects Phase 06 JSON artifacts;
  M3 fix implemented (separate N_players and N_obs columns); M2 fix
  implemented (v1.0.4 §14(b) citation, not v1.0.5).
- 5 new bibtex entries in `references.bib` (Nakagawa2017, Chung2013,
  Ukoumunne2003 — m3 fix applied, WuCrespiWong2012, Gelman2007).
- Polish char count total §4.4.4 + §4.4.5: **4 500 – 7 500** (widened
  50% buffer per m5 fix after PR-1 59% overage lesson; explicit stop
  rule: if draft exceeds 7 500 trigger targeted tighten before PR-2 close).
- `[REVIEW]` flag count across PR-2 insertions: 5–7 (T01=2, T02=3–4,
  forward-ref flags as mandatory per PR-1 M2 precedent).
- REVIEW_QUEUE has 2 new Pending rows (§4.4.4, §4.4.5).
- WRITING_STATUS has §4.4.4 status DRAFTED + new §4.4.5 row DRAFTED.
- `pyproject.toml` version 3.25.0; CHANGELOG `[3.25.0]` entry present.
- `planning/current_plan.critique.md` exists and has been read by
  user before execution.
- Pre-commit hooks pass (ruff/mypy/jupytext skip for `.md`-only
  changes; planning artifact validation passes).
- New PR opened on branch `docs/thesis-ch4-stat-methodology-residuals`.

## Out of scope

- **Residual #5 (`[PRE-canonical_slot]` flag).** Deferred to PR-3.
- **Residual #1, #2, #4-construction (reference-window, [POP:] scope,
  744-player ceiling).** Already addressed in PR #175 (PR-1). PR-2
  resolves Residual #4 identification-side forward-ref only.
- **Chapter 5 (Experiments and Results) pre-staging.** Tabela 4.7 is a
  Chapter-4 methodology preview; the ICC results themselves live in
  Chapter 5 (post-experiment discussion). PR-2's Tabela 4.7 presents
  numbers to defend the estimator choice, not to conclude about ICC.
  Writer-thesis must frame Tabela 4.7 captions this way — "wartości
  prezentowane tu ilustrują spójność cross-dataset estymatora, pełna
  analiza wyników znajduje się w rozdziale 5".
- **Tabela 4.7 sc2egset CI method verification.** If the sc2egset JSON
  confirms delta-method (not cluster-bootstrap), Tabela 4.7 shows a
  mixed-method CI column — acceptable for PR-2 provided writer-thesis
  flags it clearly. A Category-D chore F7 may be needed to harmonize
  CI methods across the three datasets; flag for planner-science
  rather than blocking PR-2.
- **GLMM latent-scale ICC numerical values.** Where convergence failed
  (sc2egset) or was skipped (aoestats due to patch constraint;
  aoe2companion large-cohort MCMC intractable), PR-2 states the
  convergence status rather than the value. No GLMM numbers in
  Tabela 4.7.
- **LMM observed-scale ICC (diagnostic).** aoestats JSON line 43–49
  reports LMM as diagnostic per spec v1.0.4 §14(b); PR-2 mentions this
  once in §4.4.5 subsection (c) for completeness but does not
  reproduce the LMM numbers in Tabela 4.7.
- **Pre-existing §4.1.2.3 heading bug at line 159 of chapter file.**
  Deferred to Category-E chore per PR-1 Out-of-scope.

## Open questions

- **Q1:** Does §4.4.5 belong as a subsection of §4.4 (Experimental
  protocol) or would §4.4.4.5 / §4.4.4.ext or §4.2.4 make more sense
  given §4.4.5 discusses a single estimator? Resolves by:
  planner-science judgment call — **(m7 fix — traceability
  rationale)** §4.4.5 as sibling to §4.4.4 was chosen over §4.2.4
  (data-characterization placement) for two reasons:
  (1) ICC on `won` is computed at Phase 01 but **motivates
  model-class selection at Phase 04** (matchmaking-equalization
  hypothesis drives the expectation that pre-game features will
  be moderately but not wildly predictive; this is methodology
  for Chapter 5 results interpretation);
  (2) Tabela 4.7 immediately precedes the discussion of within-game
  / cross-game testing in §4.4.4 — section-adjacent placement is
  more readable than cross-section xref. An examiner preferring
  §4.2.4 would need only one xref from §4.4.4 to find it; the
  ordering is a matter of taste, not of methodology. Resolved.
- **Q2:** Should Tabela 4.7 report ICC to 4 decimal places (matching
  aoe2companion 0.003013 precision) or to 3 decimal places (matching
  SC2EGSet 0.0463 display precision)? Resolves by: writer-thesis
  preference + Pass-2. Recommendation: 4 decimal places uniformly
  across rows (shows ICC values with meaningful last digit for all
  three). Resolve at draft time.
- **Q3:** PR-1 round-2 flagged char overage at 59%. Should PR-2 adopt
  stricter char budget OR accept similar overage? **(m5 fix —
  widened buffer)** Resolved: char budget 4 500 – 7 500 Polish chars
  total (50% buffer over planner-science 6k) with explicit stop rule
  "if draft exceeds 7 500, trigger targeted tighten before PR-2
  close". This matches the empirical PR-1 overage pattern more
  honestly than the 30% buffer.
- **Q4:** Does the [Ukoumunne2003] bibkey refer to the 2003 original
  paper (Stat. Med. 22:3805–3821) or a 2012 follow-up? **(m3 fix —
  resolved pre-execution)** Primary paper is Ukoumunne et al. 2003,
  Stat. Med. 22(24):3805–3821. PMC3426610 is a 2012 PubMedCentral
  free-access accession of the 2003 paper, NOT a distinct 2012
  publication. Bibkey `Ukoumunne2003` per publication-year convention.
- **Q5:** Does §4.4.5 need to address LMM demotion-to-diagnostic
  rationale beyond citing [Chung2013]? Resolves by: spec v1.0.4
  §14(b) — LMM was demoted because ANOVA is cross-dataset-comparable
  and LMM is not (different datasets use different MCMC settings,
  different convergence outcomes). PR-2 cites spec §14(b) at §4.4.5
  subsection (c) as project-level decision. Resolved.
