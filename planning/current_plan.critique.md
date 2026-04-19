---
plan_ref: planning/current_plan.md
spec_ref: reports/specs/01_05_preregistration.md @ master c5e2a5cf
reviewer: reviewer-adversarial
date: 2026-04-19
round: 1
---

# Critique: Chapter 4 DEFEND-IN-THESIS residuals — stat methodology (PR-2)

## Summary

Plan addresses Residuals #3 and #6 plus §4.4.4 draft and new §4.4.5 with
Tabela 4.7. Scope, file manifest, flag counts, and Literature Search
Protocol invocation are well-specified. However, **one BLOCKER is
fatal if executed as written**: the Nakagawa 2017 conversion formula
is mathematically incorrect — executing T02 (b) as written would plant
a formula error into the thesis. Four MAJORs and seven MINORs compound.
Verdict: **REVISE**.

## Blockers

### B1 — Nakagawa 2017 conversion formula is mathematically wrong (T02 subsection (b))

**Location:** `planning/current_plan.md:75`, `:305–308`, `:340` and the
DEFEND doc text propagating into §4.4.5 (b).

The plan (lines 74–75 and 305) writes:

> `ICC_latent = ICC_observed / (ICC_observed + π²/3)`

This is **not** the Nakagawa 2017 formula. The canonical latent-scale
ICC under a logit link is

`ICC_latent = σ²_between / (σ²_between + π²/3)`

where σ²_between is the **random-intercept variance on the logit
scale**, not the observed-scale ICC. Browne et al. 2005 (cited
approvingly by Nakagawa 2017) demonstrate that ICC_latent > ICC_observed
— the observed-scale ICC is a lower bound. Substituting the plan's
formula with ICC_observed = 0.05 yields 0.05 / (0.05 + 3.29) ≈ 0.015,
which is **smaller** than ICC_observed — contradicting the very
lower-bound claim the plan uses to defend the headline. Direction
inversion would embarrass the author at examination: one pointed
question ("what is π²/3 in that denominator — a variance or a
probability?") exposes that the formula mixes incompatible scales.

**Fix.** Either (i) rewrite the formula to `ICC_latent = σ²_u / (σ²_u +
π²/3)` and cite Nakagawa 2017 §2.2 / eq. (10) for the latent-scale
decomposition — while noting that the project does not estimate σ²_u
except via the failed GLMM attempt, so the formula is cited, not
applied, as a scale-relationship argument rather than a plug-in
conversion; or (ii) re-ground the lower-bound argument on the Browne
et al. 2005 / Nakagawa 2017 empirical finding ("latent-scale ICC is
systematically larger than observed-scale ICC under a logit link with
small cluster variance") without writing a formula. **Option (ii) is
safer given that no σ²_u estimate exists for sc2egset or aoe2companion
in current artifacts.**

Add a plan-level instruction to writer-thesis: "formula must be
mathematically verified against Nakagawa 2017 eq. (10) and Browne et
al. 2005 before committing to prose; if the formula cannot be restated
consistently with on-disk σ²_between / σ²_within values, omit the
formula and keep only the directional argument." Without this
instruction T02 will translate the plan's error into the thesis
verbatim.

## Majors

### M1 — Invariant #5 is misattributed as the "matchmaking-equalization falsification target"

**Location:** `current_plan.md:289–291` ("invariant #5
'matchmaking-equalization' falsification target").

`.claude/scientific-invariants.md:157–171` defines invariant #5 as
**"Both players in every game must be treated identically by the
feature pipeline"** (symmetric player treatment). The
matchmaking-equalization hypothesis (that per-player ICC on `won` is
small because matchmaking systems equalize outcomes) is a *generated
hypothesis* from PR #163's aoe2companion research log
(`reports/research_log.md:120, 129, 246`); it is **not** the content of
invariant #5.

**Fix:** Either (i) replace "invariant #5" with "the
matchmaking-equalization hypothesis documented in the aoe2companion
research log (2026-04-19, `reports/research_log.md:120`)", or (ii)
drop the invariant reference entirely and frame it as "the falsifier
pre-registered in spec §14(b) where the directional test 'ICC(won) ∈
[0.05, 0.20]' was stated". Artifact `01_05_05_icc_results.json`
line 12 shows `"falsifier_verdict": "FALSIFIED"`, which is the more
defensible provenance.

### M2 — Spec version citation inconsistency (v1.0.5 vs v1.0.4 §14(b))

**Location:** `current_plan.md:81, 334`.

The ANOVA-primary cross-dataset declaration lives in **v1.0.4** §14
(`reports/specs/01_05_preregistration.md:616–621`), not in v1.0.5.
v1.0.5 is the schema-harmonization amendment (merged `d90b600f`).
The aoestats JSON at `01_05_05_icc_results.json:3` explicitly cites
v1.0.4 §14(b). The plan's Tabela 4.7 footnote proposes citing "spec
v1.0.5 §14(b)" which an examiner could trace to a schema-amendment
log entry that says nothing about ANOVA primacy.

**Fix:** T02 step 4 should cite **v1.0.4 §14(b)** in the Tabela 4.7
footnote and §4.4.5 (b) prose, or cite v1.0.5 AS-OF date while noting
the underlying §14(b) rule was introduced at v1.0.4.

### M3 — aoe2companion N=5 000 is players, not observations (Tabela 4.7 column semantic mismatch)

**Location:** Tabela 4.7 row 2 (`current_plan.md:330`).

aoe2companion JSON `01_05_05_icc.json:8, 27–28` shows
`"n_players_primary": 5000` and **`"n_obs_primary": 360 567`**. Phase 06
CSV `sample_size=5000` refers to the *stratified player sample*, not
observations.

If Tabela 4.7 labels its column "N (obs.)" to match sc2egset (4 034
obs) and aoestats (7 909 obs) — both player×match observations — then
5 000 is *players*, not observations, and is not on the same axis as
the other two rows. An examiner cross-checking CI tightness against
the three "N" values would legitimately ask "why is aoe2companion's
CI tighter than sc2egset's despite similar N?" — the real answer is
aoe2companion's effective observation count is 360 567.

**Fix:** Either (i) add column `N (graczy) / N (obs.)` and split —
sc2egset 152 / 4 034; aoestats 744 / 7 909; aoe2companion 5 000 /
360 567 — or (ii) relabel "N (sample)" with footnote. Option (i) is
the defensible one.

### M4 — Demsar 2006 is cited for a claim the paper does not directly make

**Location:** `current_plan.md:191–193, 220–222`.

Demsar 2006 §3 argues Friedman requires **N ≥ 10 datasets and k ≥ 5
classifiers** for reasonable asymptotic approximation. Demsar does
not explicitly state "Friedman is inapplicable at N=2"; the N=2 result
is a trivial corollary but that specific framing is not in Demsar's §3.

**Fix:** Rewrite T01 step 2(d) to cite Demsar 2006 for the
**dataset-count requirement** (N ≥ 10 per §3.2) and derive N=2
inapplicability as a corollary. Alternatively cite **Garcia & Herrera
2008** (JMLR 9:2677-2694) which revisits Demsar with more tractable N
thresholds. Attributing "N=2 inapplicability" directly to Demsar
invites examiner to open §3 and challenge the paraphrase.

## Minors

### m1 — Tabela 4.7 CI-method asymmetry is a credibility hazard

sc2egset JSON has no `method_ci` field; DEFEND doc line 206 says
"delta-method in `variance_icc_sc2egset.csv`" — which is NOT the
cluster-bootstrap method used for aoe2companion + aoestats. Mixing CI
methods in one table undermines cross-comparability claims.

**Fix:** Either split Tabela 4.7 into a point-estimate table + CI
sensitivity footnote, or add an explicit caveat.

### m2 — "Methodology preview not headline" framing is thin

Plan asks writer-thesis to frame Tabela 4.7 as "illustrating estimator
consistency, not concluding about ICC" but three numbers with CIs in
a table read as headline results, not a conceptual diagram.

**Fix:** Strengthen T02 step 4: caption must explicitly cross-ref
§5.x where headline interpretation lives; §4.4.5 prose MUST NOT
include interpretive language like "ICC jest mały", "matchmaking
equalizuje" — all interpretation deferred to Chapter 5.

### m3 — Ukoumunne 2012 vs 2003 year

Primary paper is **Ukoumunne et al. 2003, Stat. Med. 22(24):3805–3821**.
PMC3426610 is a 2012 PubMedCentral free-access accession for the 2003
paper, not a distinct 2012 publication.

**Fix:** Pre-resolve bibkey to `Ukoumunne2003` in T03. Leave flag only
on "if a 2012 methodology revision exists".

### m4 — aoestats vs aoe2companion GLMM skip rationale swapped

Plan says "aoec skipped per spec v1.0.2 §14(c); sc2egset attempted but
BayesMixedGLMResults attribute issue". Actually aoe2companion has the
compute-skip note; aoestats JSON is silent on GLMM.

**Fix:** Correct attribution in T02 step 3(b): aoe2companion skipped
per spec v1.0.2 §14(c) (compute); aoestats GLMM status unspecified.

### m5 — Char budget 30% buffer insufficient after PR-1 lesson

PR-1 overage was 59%, not 30%. Plan-2 retains 30% buffer for larger
6k target. Realistic expected overage: 50–70%.

**Fix:** Widen to 4 500–7 500 Polish chars total with explicit stop
rule: "if draft exceeds 7 500, trigger targeted tighten before PR-2
close". Or tighten T01+T02 scope to save ~400 chars per subsection.

### m6 — DEFEND-IN-THESIS checkbox flip not scheduled

Plan File Manifest does not include `planning/CHAPTER_4_DEFEND_IN_THESIS.md`.
Residuals #3 and #6 should flip to `[x]` at PR close.

**Fix:** Add housekeeping step to T04 (or defer explicitly to PR-3 open).

### m7 — §4.4.5 placement rationale thin

Q1 resolution ("ICC estimator is first-class methodology") is reasonable
but unsupported. An alternative placement (§4.2.4 within
data-characterization) has its own merit.

**Fix:** Add a sentence to plan recording why §4.4.5 won over §4.2.4 for
traceability.

## Verdict

**REVISE** — The plan is substantively sound on scope but the Nakagawa
2017 formula error (B1) would plant math-incorrect formula into the
thesis. B1 is a single-paragraph fix at the plan level. M1–M4 are
citation-accuracy fixes each requiring a one-line adjustment. Fix all
five issues then proceed to execution.

## Resolutions applied at review time (verified PASSes)

- **Tabela 4.7 aoestats row values** (0.0268 / [0.0148, 0.0387] / N=7 909):
  verified from `01_05_05_icc_results.json:37–40` at cohort `n_min10`. PASS.
- **Tabela 4.7 sc2egset point estimate and CI** (0.0463 / [0.0283, 0.0643]):
  verified from both JSON and CSV. PASS.
- **Tabela 4.7 aoe2companion full-precision 0.003013 / [0.001724, 0.004202]:**
  verified from JSON. Plan's JSON-precision-over-CSV rule correct. PASS.
- **[Demsar2006] already in references.bib at line 136:** verified. PASS.
- **[Nakagawa2017] DOI 10.1098/rsif.2017.0213, J. R. Soc. Interface:**
  verified via WebSearch. PASS.
- **[WuCrespiWong2012] Contemp. Clin. Trials 33(5):869–880:** verified
  across project artifacts. PASS.
- **No pre-existing Nakagawa/Chung/Ukoumunne/WuCrespi/Gelman bibkeys in
  `references.bib`:** verified — no conflicts for T03 additions. PASS.


---

## Round 2 — execution-side

**Reviewer:** reviewer-adversarial
**Date:** 2026-04-19
**Base ref:** master c5e2a5cf
**Branch:** docs/thesis-ch4-stat-methodology-residuals

### Summary

0 BLOCKERs, 1 MAJOR, 5 MINORs, plus 1 NOTE. **Verdict: PASS.** All five
Round-1 issues (B1/M1/M2/M3/M4) and seven minors correctly addressed.
Single MAJOR is cross-chapter consistency (§2.6 Demsar N≥5 vs §4.4.4
Demsar N≥10). MINORs are tightening candidates around char overage
and cross-chapter residues. None block PR close.

### Blockers

None — B1 regression check clean. §4.4.5 (b) uses Nakagawa 2017 eq. (10)
`ICC_latent = σ²_u / (σ²_u + π²/3)` with σ²_u explicitly defined as
logit-scale random-intercept variance. Prose says "cytowany jest jako
argument skali, nie plug-in konwersja". Bad formula from R1
(`ICC_observed / (ICC_observed + π²/3)`) appears nowhere.

### Majors

#### M_r2_1 — §2.6 cites Demsar N≥5 as Friedman threshold; §4.4.4 cites Demsar N≥10

Both thresholds exist in Demsar 2006 (§3.1 small-sample power vs §3.2
asymptotic approximation). Both derive N=2 inapplicability. An examiner
reading both chapters sequentially will ask "which threshold applies in
your protocol — 5 or 10?". Defensible answer exists but requires
on-the-spot recall of Demsar §3.1 vs §3.2.

**Fix:** Either (i) one parenthetical in §4.4.4 line 367 (e.g. "por.
§2.6: kryterium N ≥ 5 z §3.1 prowadzi do tego samego korolarium"), or
(ii) Pass-2 flag. Option (i) is preferred.

### Minors

#### m_r2_1 — PR-1 §4.1.4 residue still attributes "N=2 inapplicable" directly to Demsar

`04_data_and_methodology.md:213` (frozen PR-1 text) has the direct-quote
construction that M4 critiqued. PR-2 could have added a forward-ref
("formalna derywacja korolarium — §4.4.4"). ~30 chars; defensibly
out-of-scope for PR-2 but proactive close would have strengthened.

#### m_r2_2 — Char overage: combined 8 138 chars (my count) vs 7 500 hard stop

Writer-thesis reported 7 950; independent count 8 138 (638 over stop).
Tightening candidates (~400-500 chars): dedupe "interpretacja — rozdział 5"
sentences; move σ²_u explanation to footnote; drop redundant Tabela 4.7
footer claim.

#### m_r2_3 — Tabela 4.7 footer "różnice w szerokości CI odzwierciedlają rozmiar kohorty (152–5 000)" oversimplifies

CI widths driven by N (obs.) not N (graczy) for aoe2companion.

**Fix:** "rozmiar kohorty (152–5 000 graczy, 4 034–360 567 obs.)"
(~28 chars added).

#### m_r2_4 — aoestats GLMM attribution under-specified

Prose says "status GLMM nie jest raportowany" but JSON does report
explicit null at `01_05_05_icc_results.json:50`. Under-specified.

**Fix:** "wartość GLMM jest explicite null (`01_05_05_icc_results.json:50`)
— praca odnotowuje brak attempted estymaty."

#### m_r2_5 — Subsection (d) flag is self-confirming, not Pass-2 actionable

`:377` flag reads as status-confirmation not review request. Either
remove or rewrite to actionable.

### Passes (verified)

- B1 regression: Nakagawa formula correct (σ²_u explicitly on logit
  scale; cited as scale argument not plug-in).
- Invariant #5: §14(b) falsifier + aoe2companion research log cited
  for matchmaking-equalization; no invariant #5 misattribution.
- Spec v1.0.4 §14(b) throughout; v1.0.5 nowhere.
- Tabela 4.7: 6 columns, 3 rows, sc2egset n_groups=152 verified via
  `icc.json:14,28,42`; aoe2companion 5 000/360 567 verified via
  `01_05_05_icc.json:27-28`; aoestats 744/7 909 verified via
  `01_05_05_icc_results.json:35-36`.
- Demsar §3.2 N≥10 corollary framing correct.
- aoe2companion GLMM compute-skip via `glmm_skip_note` field correctly
  attributed.
- Numerical accuracy: all ICC + CI values + Polish typography verified
  against artifacts.
- Ukoumunne2003 bibkey correct (m3 fix applied).
- 5 new bibtex entries well-formed (DOI/ISBN, author, year, provenance).
- Flag inventory complete: 7 flags (6 [REVIEW] + 1 [UNVERIFIED]).
- Forward-ref closure from PR-1: §4.1.2.1 + §4.1.4 anchored by §4.4.4 /
  §4.4.5; §4.4.6 correctly unclosed (PR-3 closes it).
- REVIEW_QUEUE + WRITING_STATUS updates correct.
- Invariants #5, #6, #7, #8, #9: RESPECTED.

### Lens assessments

- **Statistical methodology:** SOUND (one cross-chapter threshold
  inconsistency flagged as M_r2_1; Demsar hierarchy + Nakagawa
  directional + Chung REML + Ukoumunne cluster-bootstrap all correctly
  cited).
- **Thesis defensibility:** STRONG (observed-scale choice presented as
  explicit compute-constrained + lower-bound-preserving defense;
  identification argument substantive).
- **Cross-game comparability:** MAINTAINED (M3 fix applied correctly;
  spec v1.0.4 §14(b) cross-dataset basis).
- **Temporal discipline / Feature engineering:** N/A for this PR.

### Weakest link

**M_r2_1** — cross-chapter Demsar N-threshold inconsistency. Most likely
to surface under examination pressure. One-line parenthetical in §4.4.4
eliminates the vulnerability.

### Verdict

**PASS** — ready for T04 wrap-up + PR close. Optional inline fix
(M_r2_1, m_r2_3, m_r2_4) would strengthen further; the rest defer to
Pass-2.
