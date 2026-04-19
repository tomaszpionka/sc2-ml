# Adversarial Review — planning/current_plan.md

**Plan:** `planning/current_plan.md`
**Category:** F (thesis writing)
**Date:** 2026-04-19
**Branch:** `docs/thesis-4.2.2-identity-meta-rule`
**Reviewer:** reviewer-adversarial (pre-execution, thesis methodology focus)

## Verdict: **REVISE BEFORE EXECUTION**

The plan's framework application is methodologically sound and the 3-round /critic cycle has clearly improved the scope boundary and hedging. However, BLOCKER #1 is a thesis-defensibility risk that the current escalation fallback does not address — it must be resolved upstream (in the aoe2companion artifacts) before §4.2.2 can cite any collision rate. MAJOR #2, #3, and #4 each create examiner-attack surface that a single additional drafting pass can eliminate.

## Invariant compliance

- **I2 (canonical nickname / 5-branch procedure):** RESPECTED at framework level. Each dataset correctly mapped to its declared branch. **But:** plan cites rates that are internally inconsistent across upstream artifacts (see BLOCKER #1). I2 *compliance* fine; I2 *evidence* broken.
- **I3 (temporal < T):** N/A — identity resolution is pre-Phase-02 cleanup. Plan correctly notes (4b) Branch (iii) fragmentation does not propagate leakage because no cross-region joins occur.
- **I6 (reproducibility):** AT RISK. Citation surface (INVARIANTS.md §2) disagrees with primary SQL artifact for aoe2companion — a figure cited in thesis must trace to a derivation that produces exactly that figure; three different derivations produce three different figures.
- **I7 (no magic numbers):** RESPECTED — dropped "5% blocking threshold" framing.

## BLOCKERS

### BLOCKER #1 — aoe2companion collision-rate arithmetic is artifact-inconsistent, not merely arithmetically inconsistent

Plan (lines 77–81, 171–175) flags "3.7% vs 3.39%" and proposes escalation fallback during T01. This fallback is **insufficient**. Upstream artifacts disagree on the underlying counts themselves:

- `INVARIANTS.md:47` → "Result: 3.7% (22,186 collision names / 631,620 + 22,186 total)" → 22,186 / 653,806 = **3.393%**
- `research_log.md:337` → "Collision names (2+ profileIds): 22,186 (3.7%)"
- `01_04_04_identity_resolution.md:100–104` → "Total 654,841; Unique 631,620 (96.45%); Collision **23,221** (3.55%)" → 23,221 / 654,841 = **3.546%**

**Three artifacts report four different values.** Numerators disagree (22,186 vs 23,221), denominators disagree (653,806 vs 654,841). This is an upstream data-provenance contradiction, not a typo.

**Consequence:** An examiner cross-reading §4.2.2's "3.7% collision" claim against the primary SQL artifact will find 3.55% derived from different operands. The thesis will cite a number the pipeline does not produce. Direct I6 violation.

**Recommended action:** Pre-execution resolution, not T01-escalation:
1. Re-run SQL in `01_04_04_identity_resolution.md:112–126` on current DuckDB state.
2. Reconcile INVARIANTS.md §2 with primary artifact (correct whichever is stale).
3. Only then cite the reconciled figure in §4.2.2.

This is Category A/D fix in the aoe2companion pipeline, not a thesis edit.

## MAJOR concerns

### MAJOR #2 — Chess.com counterfactual stress-test has defensibility surface larger than acknowledged

Three problems examiners will exploit:

**(a) Counterfactual undermines real comparison.** Real chess.com exposes stable `user_id` through public API (api.chess.com). An examiner with basic web-scraping experience knows this. Demšar 2006 §2: "no-free-lunch example choice" — exemplar whose real instance contradicts argumentative frame weakens demonstration.

**(b) Branch (ii) empirically unreachable in thesis corpora.** None of the three corpora select Branch (ii). Counterfactual demonstrates decidability in a region where it does not have to be decidable for the thesis's actual claims.

**(c) "Rename-stability from handle policy" smuggles non-rate evidence.** I2 Step 3 Branch (ii) preconditions require "collision rate below project-set tolerance" — an *empirical* rate. Substituting ToS policy guarantee for empirical rate shifts the framework's standard of evidence.

**Recommended action** — pick one:
- **Option A:** Replace with real handle-only dataset (UAlbertaBot Replay Dataset, MSC).
- **Option B:** Reframe as *framework-completeness note*, not stress-test. "Branch (ii) exists to accommodate datasets that will not arise in this thesis's corpora but may arise in replication work."
- **Option C:** Drop entirely — three real examples are sufficient for framework demonstration.

### MAJOR #3 — sc2egset Branch (iii) "accepted bias" justification has one weak leg

Step 4(b) leg (1): "no stable worldwide alternative exists without manual curation" reads as *resource constraint*, not methodology justification. An examiner will ask: "Did you try?"

sc2egset INVARIANTS.md §2 line 55 has the stronger form: "The 294 Class A cross-region candidate pairs are deferred to a future manual-curation upgrade path." This framing acknowledges bias is *known-recoverable-but-deferred* — stronger than "no alternative exists."

**Recommended action:** Replace "no stable worldwide alternative exists without manual curation" with "manual record-linkage recovery of the 294 Class A cross-region candidate pairs is deferred to future work (sc2egset INVARIANTS.md §2 line 55)."

### MAJOR #4 — Branch (i) "rate first, property second" decomposition not in I2 text

Step 4(c) states: "rate comparison... as the Branch (i) precondition... rename-stability... is a downstream property, not the decision criterion." But `.claude/scientific-invariants.md:76–79`:

> "(i) API-namespace ID — preferred when `migration_rate < collision_rate` on the visible handle. The API-issued identifier is rename-stable and globally scoped within the provider's system."

I2 lists rename-stability *as part of the branch definition*, not as a downstream property. Plan decomposition is thesis's own restructuring. Not applied to Branch (iii) at step 4(b) — asymmetric application reads as *ex post* rationalization.

**Recommended action:** Either (a) apply decomposition consistently to all three branches, or (b) drop decomposition and let branch definition do the work.

## MINOR concerns

### MINOR #5 — Branch (v) aoestats example should cite aoec namespace bridge

Step 4(d) defends Branch (v) by structural unavailability. Weaker than possible: aoestats `profile_id` and aoec `profileId` share namespace (aoestats INVARIANTS.md:44–61, VERDICT A, 0.9960 agreement). Bridge gives aoestats an *indirect* rate measurement.

**Recommended action:** Add one sentence in step 4(d): "Direct rate measurement within aoestats is structurally unevaluable (Branch v), but cross-dataset namespace alignment to aoec (aoestats INVARIANTS.md:46–61, VERDICT A, 0.9960 agreement) validates that the same profile_id key is the correct identity choice."

### MINOR #6 — Polish prose load-bearing terms should be resolved before T01

Four terms (tolerance gate, API namespace ID, visible handle, rename-stable) appear in every branch example. Deferring to Pass 2 forces global re-edit if idiom changes.

**Candidate renderings for user review before T01:**
- `tolerance gate` → `próg tolerancji`
- `API namespace ID` → `identyfikator przestrzeni nazw API`
- `visible handle` → `pseudonim widoczny` (already used elsewhere in §4.2.2)
- `rename-stable` → `odporny na zmianę pseudonimu`

### MINOR #7 — T03 REVIEW_QUEUE update should specify post-rewrite line anchors

T03 step 1 does not specify that REVIEW_QUEUE.md must carry post-rewrite line anchors for the two *new* flags. Pass 2 will have to re-locate them.

### MINOR #8 — Verify no orphan `Plan Phase 02` references outside Tabela 4.5

T02 renames `Plan Phase 02 (I2)` → `Klucz kanoniczny (I2 §2)`. Grep the thesis tree before T02 to check for orphan prose references.

### MINOR #9 — Citation-surface convention should be made conditional on numerical concordance

Convention "read primary artifact, cite INVARIANTS.md §2 summary" works for sc2egset (numbers agree) but fails for aoe2companion (numbers disagree). Plan should add assumption: "Citation-surface convention holds only when INVARIANTS.md §2 numerically matches the primary derivation artifact."

## Weakest link

**The weakest link is not the chess.com stress-test (visible risk); it is BLOCKER #1 — the silent upstream data-provenance contradiction in the aoe2companion rate figures.**

The chess.com example is visible and can be cut. The aoe2companion rate discrepancy is invisible until an examiner cross-reads the primary artifact — and then the thesis carries a number (3.7%) that its own SQL artifact does not produce (3.55%). This is exactly the kind of defect that survives 3 rounds of /critic workflow and emerges at defense.

## Required pre-execution actions

1. **[BLOCKER #1]** Resolve aoe2companion 22,186/23,221 numerator discrepancy in INVARIANTS.md vs 01_04_04_identity_resolution.md. Category A/D fix, not a thesis edit.
2. **[MAJOR #2]** Choose one of three alternatives for chess.com example (replace / reframe / drop).
3. **[MAJOR #3]** Rewrite Branch (iii) justification to prefer "deferred to future work" framing.
4. **[MAJOR #4]** Reconcile I2 Step 3 framing across all three real examples (consistent decomposition or no decomposition).

## Recommended pre-execution actions

5. **[MINOR #5]** Cite aoec namespace bridge in Branch (v) example.
6. **[MINOR #6]** Resolve four Polish terms before T01.
7. **[MINOR #7]** Specify post-rewrite line anchors in T03 instructions.

## After these are addressed

The plan as revised would be DEFENSIBLE and likely to produce a §4.2.2 that survives committee scrutiny without need for Pass 2 remediation of the BLOCKER class.

---

# Pass 2 (post-revision) — 2026-04-19

## Verdict: **EXECUTE**

All Pass 1 findings (1 BLOCKER + 4 MAJORs + 5 MINORs) genuinely resolved in substance, not only in wording.

### Resolution verification

- **BLOCKER #1** — aoec INVARIANTS.md §2 SQL now rm_1v1-scoped; numbers 2.57%/3.55% consistent with `01_04_04_identity_resolution.md` primary artifact. Operand arithmetic self-checks: 23,221/654,841 = 3.546%. Research_log 2026-04-19 entry records the reconciliation with root-cause audit.
- **MAJOR #2** — chess.com reframed as framework-completeness note (not stress-test). Branch (ii) explicitly not instantiated by any thesis corpus; chess.com is named as indicative class only. Three sub-problems closed: counterfactual-undermines-real, empirically-unreachable, non-rate-evidence-smuggling.
- **MAJOR #3** — sc2egset acceptance clause now cites INVARIANTS.md §2 line 55 "deferred to future manual-curation upgrade path" framing + Phase 02 leakage-non-propagation. Both legs methodology-grounded.
- **MAJOR #4** — Branch (i) decomposition dropped. T01 step 4(c) mirrors I2 Step 3 Branch (i) verbatim.
- **MINOR #5/#6/#7/#8/#9** — all applied; verified on disk.

### Fresh residuals (MINOR/NOTE — none require pre-execution remediation)

- **N1** — `01_04_04_identity_resolution.md` prose at lines 262/276 (+ JSON mirror) still reads 3.7% vs data row 3.55%. **Resolved:** 3-line addendum appended to artifact documenting the reconciliation.
- **N2** — Branch (v) "cross-validated" wording subtly stronger than VERDICT A proves (bridge proves namespace coincidence, not rate transitivity). **Resolved:** T01 step 4(d) softened to "corroborates namespace alignment"; explicit caveat that rates remain structurally unevaluable within aoestats.
- **N3** — No bridge sentence between paragraph 1 (Fellegi-Sunter) and paragraphs 2–4 (5-branch). **Resolved:** T01 step 4(a) instruction now mandates a bridge sentence framing I2 as *a priori* schema selection reducing the classical match/non-match/possible-match decision.
- **N4/N5** — NOTEs, no action required (version bump convention correct; Polish dictionary entry implicitly mapped).

### Invariant compliance (fresh)

- I2: RESPECTED (each dataset correctly mapped; rates consistent across artifacts).
- I3: N/A (identity resolution is pre-Phase-02).
- I6: RESPECTED (primary-internal discrepancy closed by N1 addendum).
- I7: RESPECTED (5% threshold framing dropped throughout).
- I8: RESPECTED (framework-symmetric application to all three corpora).
- I9: RESPECTED (historical research_log entries preserved).

### Remaining attack surface

None load-bearing. Thesis §4.2.2 will be defensible at committee examination.

**Plan is cleared for executor dispatch.**
