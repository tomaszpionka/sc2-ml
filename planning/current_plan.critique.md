# Adversarial Review — Plan (Mode A) — WP-3

**Plan:** `planning/current_plan.md` — WP-3 sc2egset cross-region history-fragmentation quantification
**Branch:** `feat/sc2egset-cross-region-history-impact`
**Base:** master `000251f0` (v3.40.0 post PR #199)
**Date:** 2026-04-21
**Reviewer:** reviewer-adversarial, Mode A (pre-execution)

## Lens summary

| Lens | Verdict |
|---|---|
| Temporal discipline (I3) | AT RISK — measured quantity misrepresents real Phase 02 bias |
| Statistical methodology | FLAWED — power/threshold asymmetry; median masks tail |
| Feature engineering realism | AT RISK — static-aggregate simulation vs rolling-prefix reality |
| Thesis defensibility | WEAK — binary PASS/FAIL from underpowered test is brittle |
| Cross-game comparability | ADEQUATE — asymmetry defensible if stated |
| SQL correctness / verifiability | AT RISK — 4 SQLs described, not specified |
| Reproducibility (I6) | ADEQUATE — specify percentile engine |
| Invariant compliance | AT RISK — I7 self-referential (30-game window); I2 drift risk |
| Cat A plan completeness | ADEQUATE — notebook-steps substitute for functions |
| Out-of-scope discipline | SOUND |
| Execution realism | AT RISK — 6 tasks in 1 session optimistic |

## BLOCKER / WARNING / NOTE findings

**1. [BLOCKER] The measurement does not model the Phase 02 bias it claims to quantify.** T02 Analysis §3 operationalises "undercount" as `total_games − max_games` per cross-region nickname — a **static lifetime aggregate**. Phase 02 rolling features at match T for player-ID X see the **prefix of X's timeline up to T**, not X's lifetime total. A player with 100 lifetime games split 50/50 EU/NA at their 25th EU match has a rolling feature over games 1–24 in EU — the "50-game undercount" is hypothetical. The right quantity is **per-(cross-region player, match T) rolling-window undercount**. The current metric overstates bias by counting late-life matches that can never leak into early-life features. Fix: T02 Analysis §3 computes per-match rolling-window undercount at a stated primary window (e.g., 30 games) with sensitivity across {5, 10, 30, 100}; OR §5 explicitly reframes as a loose upper bound.

**2. [BLOCKER] Spearman ρ threshold is underpowered.** Plan requires `|ρ| < 0.1` for PASS. At n≈200 (246 minus the MMR-filtered subset), Spearman ρ with |ρ|=0.1 at α=0.05 has ~30% power. The threshold PASSES vacuously in ~70% of worlds where a real ρ=0.1 exists. The test literally cannot reject H0. Fix: raise threshold to |ρ|<0.2 (~80% power at n=200) citing a power calculation in the notebook; OR replace binary threshold with bootstrap 95% CI on ρ for graded interpretation.

**3. [BLOCKER] Median-only threshold hides right-tail bias.** Gate Condition requires `median_undercount ≤ 1`. For right-skewed distributions typical of "some players migrate a lot, most don't," median can be 0 while p95 is 50. The 5% subpopulation with high fragmentation produces heavily biased rolling features — they're Phase 02 feature outliers exactly where they matter. Median-only verdict invites "your verdict missed the 5% of players who are the entire problem." Fix: add `p95_undercount_games ≤ K` alongside median; PASS iff BOTH cross thresholds.

**4. [WARNING] 30-game rolling-window rationale is self-referential per I7.** Gate §Threshold derivation justifies `median ≤ 1 game` by "3.3% relative error against a rolling-30-games feature." No artifact establishes 30 as the chosen Phase 02 window — Phase 02 hasn't been designed. The rationale grounds a threshold in a future step's magic number. Fix: cite window size as hypothetical with sensitivity across {5, 10, 30, 100}; OR drop relative-error framing and argue against concrete external reference.

**5. [WARNING] T01 ±5 drift tolerance is a magic number.** "Arbitrary but documented" is what I7 forbids. Fix: state "proceed on any count; supersede 01_04_04 authoritatively"; OR justify ±5 as a specific fraction (e.g., 2% of 246).

**6. [WARNING] Binary PASS/FAIL cannot map to graded thesis prose.** An examiner asking "what if ρ=0.15?" gets no answer from binary verdict. Cat F author downstream must improvise. Fix: T03 §5 emits three pre-drafted paragraphs (clean PASS / marginal / FAIL) selected by verdict.

**7. [NOTE] Reproducibility: specify percentile computation engine.** DuckDB `PERCENTILE_CONT(0.95)` and pandas `quantile(0.95)` can differ at small n. Specify in T02 which engine computes each statistic so I6 SQL-verbatim applies to the JSON numbers.

**8. [NOTE] "Same physical player" assumption unverified.** T02 Analysis §3 treats all matches of a cross-region nickname as the same physical player. INVARIANTS.md §2 warns 30.6% within-region handle collision rate exists; across regions, some 246 nicknames are **different physical players** (common handles like "Zerg", gamertags <6 chars). Counting their matches as one player inflates apparent undercount. Fix: T02 Analysis §4 additionally reports results restricted to "rare-handle" subsample (e.g., nickname length ≥ 8) to control for within-region handle collision confound.

**9. [NOTE] Execution realism: 6 tasks in 1 session is optimistic.** T02 hypothesis-driven SQL iteration + T03–T06 artifact/INVARIANTS/log/version. Per `feedback_notebook_iterative_testing.md`, T02 alone expects iteration cycles. Realistic: session 1 = T01+T02; session 2 = T03–T06. Fix: Dispatch sequence acknowledges 2-session budget OR compresses T04–T06 into wrap-up.

## Verdict

**REVISE BEFORE EXECUTION.** Three methodological flaws combine to make the executed artifact fragile under examiner scrutiny: measured quantity doesn't model real Phase 02 bias (BLOCKER-1); MMR correlation threshold is underpowered to falsify (BLOCKER-2); median-only verdict hides the tail where bias lives (BLOCKER-3). Any one alone survives with hedged prose; all three together invite a reviewer to dismiss the quantitative claim as not actually measuring Phase 02 bias.

## If REVISE: required revisions (enumerated list)

1. **BLOCKER-1:** T02 Analysis §3 computes per-(cross-region player, match) rolling-window undercount at one primary window size with sensitivity report across {5, 10, 30, 100}; OR §5 explicitly states lifetime aggregate is a loose upper bound. Pick one — current framing claims Phase 02 relevance the measurement doesn't support.

2. **BLOCKER-2:** Raise |ρ| threshold to 0.2 citing power analysis, OR replace with bootstrap 95% CI interpretation. Notebook includes the power calculation verbatim.

3. **BLOCKER-3:** Gate Condition adds `p95_undercount_games ≤ K` with empirical K justification. Verdict PASS iff BOTH median AND p95 cross thresholds.

4. **WARNING-4:** Rewrite Gate "Threshold derivation" to cite concrete reference (or sensitivity sweep across windows), not a hypothetical single Phase 02 window.

5. **WARNING-5:** Justify ±5 drift tolerance empirically, OR remove and record whatever count is current.

6. **WARNING-6:** T03 §5 emits three pre-drafted paragraphs selected by verdict.

7. **NOTE-7:** T02/T03 specify percentile computation engine (DuckDB SQL vs pandas) per statistic.

8. **NOTE-8:** T02 Analysis §4 additionally reports results restricted to "rare-handle" subsample (nickname length ≥ 8) to control for within-region handle collision.

9. **NOTE-9:** Dispatch sequence acknowledges 2-session execution budget, OR compresses T04–T06 into a single wrap-up task.
