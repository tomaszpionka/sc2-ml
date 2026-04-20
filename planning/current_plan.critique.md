# Adversarial Review — Plan (Mode A) — TG5-PR-5b

**Plan:** `planning/current_plan.md` (TG5-PR-5b — §4.1.3 reference-window defence + §2.2.3 Thorrez proxy insertion)
**Branch:** `docs/thesis-pass2-tg5b-circular-spec-thorrez-proxy` (base: master @ `d640711a`)
**Date:** 2026-04-20
**Reviewer:** reviewer-adversarial agent, Mode A (pre-execution)

## Lens summary

| Lens | Verdict |
|---|---|
| Temporal discipline | N/A — no feature/model computation |
| Statistical methodology | AT RISK — 3 of 4 F5.4 anchors support defence argument analogically, not directly; precision-axis claim qualitatively defensible but not quantitatively supported by Tabela 4.7 numbers |
| Feature engineering | N/A |
| Thesis defensibility | ADEQUATE — T01 orthogonal-axes reframe is structurally stronger than audit ask but opens new angle of attack (bias-variance coupling at ICC ≈ 0.003) plan does not anticipate; T02 proxy sentence preserves calibration/accuracy distinction but overreaches on "strukturalnie zbliżony" and miscategorizes ~80% vs 80.13% as "rounding" difference |
| Cross-game comparability | AT RISK — three-corpus ICC comparison is window-length-confounded; defence claims axis-orthogonality without quantitative support |

## Examiner's questions the plan does not pre-empt

1. **T02:** Why cite Thorrez 2024's Glicko-2 entry rather than any Aligulac-variant entry from the same Table 2? EsportsBench evaluates 11 rating systems.
2. **T01:** Orthogonal-axes defence — in small-ICC regimes (aoe2companion ICC ≈ 0.003), bias and variance effects couple near boundary. How defend clean axis-separation?
3. **T01:** Four-anchor defence reuses §4.4.5 citations for a claim (patch-regime non-stationarity biases ICC) that none of them make directly. Analogical stretch.
4. **T01:** Tabela 4.7 shows aoestats CI width is relatively *narrower* than aoe2companion's (89% vs 82% relative to point). Where is the precision penalty actually visible?
5. **T01:** Could all three corpora have been matched to a 9-week window for ICC comparability? Counterfactual not addressed.
6. **T02:** "Strukturalnie zbliżony" (Glicko-2 vs Aligulac matchup-conditioned): overreaches — Glicko-2 is 3-parameter (rating+RD+volatility); Aligulac is per-matchup Elo variant.

## Methodology risks

1. **[WARNING] T01 [REVIEW] flag understates literature gap.** Three of four anchors (Nakagawa2017, Gelman2007, WuCrespiWong2012) support defence argument analogically, not directly. Plan acknowledges the gap but the flag language is too soft.
2. **[WARNING] T02 proxy "strukturalnie zbliżony" overreaches.** Aligulac is matchup-conditioned Elo variant; Glicko-2 is 3-parameter (rating+RD+volatility). If Thorrez Table 2 reports Aligulac-variant, that would be the tighter proxy.
3. **[WARNING] T02 [REVIEW] flag says "rozbieżność między '~80%' a '80,13%' jest w granicach rounding" — category error.** ~80% (calibration bin label) and 80.13% (classification accuracy) are different measurements; numerical proximity coincidental.
4. **[WARNING] Cross-corpus ICC comparison with window-length asymmetry not quantitatively defended.** Tabela 4.7 numbers do not visibly support a precision penalty of the shorter window.
5. **[NOTE] R22 residual (patch 66692 uniqueness as outer-level circular)** partially addressed; chapter prose should state explicitly that patch 66692 exists independently of the spec.
6. **[NOTE] Hybrid-of-audit-options not declared in [REVIEW] tag.**
7. **[NOTE] Invariant #9 compliance respected.**
8. **[NOTE] Orthogonal-axes framing exceeds audit option (i) "dominance" scope; structurally stronger but logically different.**

## Verdict: REVISE BEFORE EXECUTION

Four prose-level plan edits required before writer-thesis dispatch:

1. **T02 proxy sentence:** Replace "strukturalnie zbliżony do rozszerzenia warunkowanego na zestawienie ras zaimplementowanego w Aligulac" with weaker phrasing (e.g., "z rodziny paired-comparison rating systems, z której wywodzi się także Aligulac").
2. **T02 [REVIEW] flag:** Replace "rozbieżność między '~80%' a '80,13%' jest w granicach rounding" with explicit disclaimer that the two numbers measure different quantities; numerical proximity is coincidental.
3. **T01 [REVIEW] flag:** Strengthen literature-gap acknowledgement — explicitly state "brak bezpośredniego źródła dla twierdzenia o biasie non-stationarity-patchowej; cztery kotwice są użyte analogicznie z §4.4.5."
4. **T01 paragraph:** Add sentence disclaiming CI widths in Tabela 4.7 are not cross-corpus comparable due to kohorta-size confounding (152/744/5000), so "precision penalty" is a qualitative design commitment, not a quantitatively-demonstrated trade-off.

If these 4 edits are made, plan graduates to SOUND/STRONG on Statistical methodology and Thesis defensibility lenses.

## Symmetric 1-revision cap (per `feedback_adversarial_cap_execution.md`)

This revision cycle consumes the 1-round allowance for Mode A. Post-revision, proceed to writer-thesis without re-running Mode A. Mode C (post-draft review) remains available for a post-execution stress test.
