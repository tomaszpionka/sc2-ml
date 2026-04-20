# Adversarial Review — Plan (Mode A) — TG6-PR-6a

**Plan:** `planning/current_plan.md` (TG6-PR-6a — §3.5 Luka 1/2/4 prophylactic strengthening)
**Branch:** `docs/thesis-pass2-tg6a-luka-prophylactic-strengthening`
**Base:** `master` @ `a5dae995` (post-PR #193)
**Date:** 2026-04-20
**Reviewer:** reviewer-adversarial, Mode A (pre-execution)

## Lens summary

| Lens | Verdict |
|---|---|
| Temporal discipline | N/A |
| Statistical methodology | AT RISK — single-witness Luka 1 logically weaker than current universal |
| Feature engineering | N/A |
| Thesis defensibility | WEAK — F6.1 internal contradiction; F6.2 asymmetric hedge + untracked cross-PR dep; F6.3 near-tautological |
| Cross-game comparability | AT RISK — FVG+EEG witness injects modality drift into RTS+pre-game argument |

## Examiner's questions not pre-empted

1. F6.1 single-witness "1 of 6 retrievable" — strengthening or honest-but-visible scope admission?
2. F6.1 modality drift — Minami2024 is FVG+EEG; how does it witness RTS+pre-game gap?
3. F6.1 contradiction — current Luka 1 universal "żadna praca esportowa … nie przeprowadza systematycznego porównania wielu rodzin klasyfikatorów" directly contradicts Minami2024 being cited as a multi-family benchmark.
4. F6.2 asymmetric hedge — method claim conditional, importance claim unconditional; if Pass-2 retracts method, importance orphans.
5. F6.2 §4.4 forward-reference — untracked cross-PR dependency for Lundberg2017 citation in §4.4.
6. F6.3 post-R13 tautology — adds citation for terminology-disambiguation claim nobody disputes; near-padding.

## Methodology risks

1. **[BLOCKER] F6.1 internal contradiction.** Current line 185 asserts universal "żadna praca esportowa nie przeprowadza systematycznego porównania wielu rodzin klasyfikatorów." Planned Minami2024 insertion describes a 9-algorithm multi-family benchmark. Post-insertion paragraph self-contradicts unless the universal is silently reinterpreted. Plan's "insertion-only" discipline incompatible with logical consistency.
   **Fix:** (a) allow one-sentence rewrite of "żadna" clause to condition on "bez pełnej oceny probabilistycznej"; OR (b) reframe Minami2024 as near-miss / adjacent-reference-class witness rather than direct witness.

2. **[BLOCKER] F6.1 modality-gap undermines cross-game framing.** FVG+EEG witness for RTS+pre-game gap. Reference class widening without public acknowledgement.
   **Fix:** Adopt (b) from BLOCKER 1 — explicitly locate Minami2024 as ADJACENT-reference-class evidence.

3. **[WARNING] F6.1 [NEEDS CITATION] hygiene — 4 unverified names inline in thesis prose.** Reputational surface.
   **Fix:** Move names to REVIEW_QUEUE §3.5 row; chapter flag becomes pointer.

4. **[WARNING] F6.2 importance-claim orphan risk.** Method claim conditional, importance claim unconditional.
   **Fix:** conditionalize "jest to rozróżnienie istotne" to match hedge scope.

5. **[WARNING] F6.2 cross-PR dependency untracked.** §4.4 forward-reference not tracked in REVIEW_QUEUE.
   **Fix:** T05 adds REVIEW_QUEUE entry under §4.4 row noting §3.5 Luka 2 dependency on §4.4 SHAP/Lundberg2017 citation.

6. **[NOTE] F6.3 post-R13 near-tautological.** Mode A observation: could drop T03 entirely without loss of Luka 4 defensibility; keeping T03 delivers audit item F6.3 at near-zero argumentative marginal value.

## Verdict: REVISE BEFORE EXECUTION

Required revisions (within 1-revision cap per `feedback_adversarial_cap_execution.md`):

1. **F6.1 reframe Minami2024 as near-miss / adjacent-reference-class evidence** (option b of BLOCKER 1 fix) — preserves insertion-only discipline and addresses both BLOCKERs simultaneously. New prose framing: Minami2024 is adjacent evidence of the accuracy-only-reporting trend, NOT a direct Luka 1 witness (because its modality and game-type place it outside Luka 1's reference class).
2. **Move 4 unverified author names** from T01 [NEEDS CITATION] flag text to REVIEW_QUEUE §3.5 row; chapter flag becomes brief pointer.
3. **Conditionalize F6.2 "rozróżnienie istotne"** to match R14 hedge scope.
4. **Add T05 REVIEW_QUEUE §4.4 dependency entry** for Lundberg2017.
5. **Keep F6.3 as-is** — observation noted; dropping T03 would also be defensible but keeping closes the audit item at acceptable cost.

Post-revision verdict: SOUND/STRONG on Statistical methodology and Thesis defensibility lenses.

**Symmetric 1-revision cap:** this cycle consumes Mode A's allowance. Post-revision proceed to writer-thesis; Mode C remains available post-draft.
