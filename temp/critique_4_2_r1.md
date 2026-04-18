# Adversarial Critique R1 — temp/plan_4_2_v1.md

## Executive verdict: REQUIRES_REVISION_R2

Plan is structurally sound and self-aware, but ships with **three BLOCKER-grade methodology defects** that correct execution cannot fix, **three framing risks** the rehearsal missed, and several WARNINGs. Single R2 round resolves them.

## BLOCKERs

**B1 — MAR/MNAR classification for MMR is internally inconsistent across shipped §4.1 and planned §4.2.**
- `thesis/chapters/04_data_and_methodology.md:41` states MMR is **MNAR** (*"nie losowo"*).
- `thesis/chapters/04_data_and_methodology.md:195` (Tabela 4.4b) also says **MNAR**.
- Ledger `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv:35` says `mechanism=MAR` ("MAR-primary ... MNAR documented as sensitivity branch").
- The plan (line 340) proposes drafting §4.2.3 as **MAR** with hedging, claiming the MAR/MNAR dispute doesn't invalidate the cleaning decision — but the dispute is with already-shipped prose, not with a hypothetical reviewer. If §4.2.3 says MAR, it directly contradicts §4.1.1.4 and Tabela 4.4b.
- **Fix:** The plan must commit to ONE classification (recommend: MAR-primary per ledger, MNAR as documented sensitivity branch) AND extend §4.2 execution scope to repair §4.1 inconsistency at lines 41 + 195 + REVIEW_QUEUE §4.1 entries.

**B2 — The "primary-feature exception" citation for the 26.20% rating decision is unverifiable, AND the plan misreads its own artifact.**
- Plan claims: "aoe2companion's `rating` MAR at 26.20% is FLAG_FOR_IMPUTATION rather than DROP_COLUMN (Rule S4 exception). The 40–80% band maps to DROP per default, but `rating` is a PRIMARY feature..."
- Actual artifact `01_04_01_data_cleaning.json:2200`: "Rate 26.20% in **5-40%**; flag for Phase 02 imputation". 26.20% is not in the 40–80% band; no exception is needed.
- WebSearch on "van Buuren 2018 threshold 40 80 percent primary feature exception" returned no codified rule. Van Buuren's own text says imputation "can be trusted in general when the proportion of missing data is less than about 30-40%" — a warning, not a 40–80% exception.
- The 80% threshold the ledgers attribute to "Rule S4 / van Buuren 2018" is framed internally as "Operational starting heuristics from temp/null_handling_recommendations.md §1.2" (`01_04_01_data_cleaning.json:1042`) — this is exactly the I7 (no magic numbers) violation the plan claims to avoid.
- **Fix:** Drop the "primary-feature exception" framing; re-cite 5/40/80 as operational heuristics traceable to the (now-deleted) internal recommendations doc OR to van Buuren's "general guidance" language; do not invent a codified exception.

**B3 — 18–22k character budget is demonstrably too small.**
- §4.1.1 consumed ~18.5k Polish chars for ONE dataset.
- §4.1.2 consumed ~22.5k for two datasets.
- §4.2 must cover three datasets + unifying typology + two new tables + I3 defence + Fellegi-Sunter framing + I10 narrative.
- **Fix:** Raise gate to 22–28k total; T04 to 10–13k; OR cut Tabela 4.6 and defer per-dataset registry to artifact cross-references.

## WARNINGs

**W1** — Christen 2012 cited as "canonical textbook" without checking; no 2020+ edition exists. Contemporary surveys co-cite modern extensions. Reframe as "introductory reference" or add forward-ref to modern ecosystem.

**W2** — `Wilson2017GoodEnough` cited for *methodology* in a DuckDB paragraph is thin. The plan's own §4.2.1 BLOCKER 2 acknowledges DuckDB is implementation not methodology. Move to Appendix A (`THESIS_STRUCTURE.md:429`) or drop.

**W3** — Tabela 4.6's 12 rule-classes × 3 datasets matrix contains ~10 `(nd)` cells. The "unified typology, dataset-specific invocations" I8 claim is fragile — examiner may read as three side-by-side per-dataset tables. Add a fourth §4.2.3 BLOCKER rehearsal for I8 sparsity + restructure Tabela 4.6 so every row is invoked in ≥2 datasets (move singleton rules to a per-dataset footnote).

## Unanticipated BLOCKERs (D6)

**D6a** — T01 should verify every Tabela 4.6 number against already-shipped §4.1 Tabela 4.1/4.2/4.3 *mechanically* (grep identity), not manually. Add to crosswalk spec.

**D6b** — The "I9 forbids identity resolution at Phase 01" argument (plan lines 291, 593) invokes the wrong invariant. I9 is research-pipeline discipline; deferring to Phase 02 is a scope decision citing §4.3.1's thesis-level I2 rule, not I9 compliance. Re-cite the correct invariant (I2 deferral to feature-time).

**D6c** — The claim that `read_csv_auto` inferred "all 7 columns as VARCHAR on the full load" for aoe2companion ratings (plan line 166) is narrative-specific. T01 should verify against `aoe2companion/.../01_02_02_duckdb_ingestion.md`; if unanchored, becomes `[UNVERIFIED]`.

## Confirmed OK

1. Crosswalk pattern is load-bearing (sec_4_1_crosswalk.md has 101 well-formed rows). T01 extension is sound.
2. Spot-check of 10 numerical claims all matched cited artifacts (22,390; 44,817; 2,495; 1,106; 107,626,399; 17,814,947; 277,099,059; 30,531,196; 26.20%; 15,999,234).
3. Fellegi-Sunter 1969 remains canonical per 2022–2024 survey literature.
4. I10 invariant application matches `.claude/scientific-invariants.md:131-159` verbatim.
5. MissingIndicator I3-deferral argument is conceptually sound regardless of MAR/MNAR dispute.
6. Scope-overlap with §4.1 is genuinely flagged in T01 protocol.
7. Forward-ref to Appendix A is valid — defined at `THESIS_STRUCTURE.md:429`.
8. The 9 pre-rehearsed BLOCKERs show genuine maturity.

## Lens assessments

| Lens | Verdict |
|---|---|
| Temporal discipline (I3/I4) | SOUND with caveat (B2 adjacent) |
| Statistical methodology | N/A — §4.2 does not touch evaluation |
| Feature engineering (I2/I5/I7) | AT RISK — I7 actively compromised by B2 |
| Thesis defensibility | WEAK but fixable — B1 is the largest risk |
| Cross-game comparability (I8) | AT RISK — W3 Tabela 4.6 sparsity |
