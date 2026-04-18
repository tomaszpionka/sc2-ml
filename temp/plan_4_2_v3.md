# Plan v3: Category F — §4.2 Data preprocessing (Polish)

## Change log — R1 critique responses

| Critique item | Verdict | Fix applied | Plan section updated |
|---|---|---|---|
| **B1 — MMR MAR/MNAR inconsistency** | **ACCEPTED.** Verified: ledger row 35 says `mechanism=MAR` with "MNAR documented as sensitivity branch"; `04_data_and_methodology.md` line 41 says MNAR ("…*nie losowo*") and Tabela 4.4b line 195 says MNAR. §4.2 as drafted per v1 would contradict §4.1. | Adopt **MAR-primary, MNAR-sensitivity** classification (per ledger). Extend T05 Integration scope with explicit §4.1 repair sub-step 0 that (a) rewrites line 41 MMR narrative, (b) updates Tabela 4.4b line 195 cell, (c) updates REVIEW_QUEUE §4.1.1 row. §4.2.3 uses the same framing. The v1 "dispute doesn't invalidate the cleaning decision" argument is retained as a SECONDARY defence (correct on merits) but is no longer the primary response. | Change log, Problem statement (§4.1 repair scope), T04 v2 JUSTIFY #4, T05 v2 sub-step 0, Adversarial-defence rehearsal §4.2.3 BLOCKER 3. |
| **B2 — "primary-feature exception" misreading + I7 threshold provenance** | **ACCEPTED on both counts.** Verified: `01_04_01_data_cleaning.json:2200` reads "Rate 26.20% in **5-40%**; flag for Phase 02 imputation" — 26.20% is in the STANDARD MAR-FLAG band. Verified: same JSON line 1042 says thresholds "from `temp/null_handling_recommendations.md §1.2`"; file confirmed absent from `/Users/tomaszpionka/Projects/rts-outcome-prediction/temp/`. | (1) Remove "primary-feature exception" framing from T04 JUSTIFY #6; re-cite 26.20% as standard MAR-FLAG routing at 5-40% band. (2) Re-cite I7 thresholds with literal provenance: 5% → Schafer & Graham 2002; 30-40% → van Buuren 2018 prose ("can be trusted when proportion < about 30-40%"); 80% → **operational heuristic traceable to the deleted internal doc**, framed explicitly, not as a peer-reviewed constant. Option (c): explicitly name the heuristic's provenance in thesis prose. | Change log, T04 v2 JUSTIFY #2 (reframed), T04 v2 JUSTIFY #6 (standard-band, not exception), T04 v2 I7 discipline check, Adversarial-defence rehearsal §4.2.3 BLOCKER 2. |
| **B3 — 18–22k budget too small** | **ACCEPTED.** Verified from `WRITING_STATUS.md`: §4.1.1 = 18.5k (one dataset); §4.1.2 = 22.5k (two datasets); §4.1.3 = 5.7k. Total §4.1 = ~46.7k. | Raise targets per task with rationale: T02 §4.2.1 = 6.0–7.5k; T03 §4.2.2 = 6.5–8.0k; T04 §4.2.3 = 10.0–13.0k. **Total: 22.5–28.5k.** | Change log, Executive summary, T02/T03/T04 budgets, Gate Condition item 2, Execution ordering table. |
| **W1 — Christen 2012 framing** | **ACCEPTED partial.** Christen 2012 is a 2012 monograph; contemporary surveys (Papadakis et al. 2020) cite it as foundational + supplement with 2018+ neural-ER. | Reframe T03 JUSTIFY #1 as **"standard introductory textbook for entity-resolution framing"** (not "canonical"). Add hedging sentence acknowledging neural-ER extensions as out-of-scope. No new bib entries for neural-ER. | T03 v2 JUSTIFY #1, Literature context table. |
| **W2 — Wilson 2017 placement** | **ACCEPTED.** Wilson 2017 is grey-literature methodology editorial; §4.2.1 BLOCKER 2 already flags DuckDB as implementation-not-methodology — citing Wilson 2017 double-burdens. | **Move** `Wilson2017GoodEnough` cite from §4.2.1 body to **Appendix A forward-reference** per W2. §4.2.1 v2 defends DuckDB via pure architectural reasoning. | T02 v2 Must cite (remove), T02 v2 JUSTIFY #1 (no citation appeal), Literature context table, T01 classification table. |
| **W3 — Tabela 4.6 sparsity** | **ACCEPTED with restructure.** v1 Tabela 4.6 had ~12 rows × 3 datasets with ~10 `(nd)` cells. | **Restructure** Tabela 4.6: every retained row invoked in ≥2 datasets (7-8 rows). Singletons move to new compact **Tabela 4.6a** footnote table (one row per dataset). Add fourth §4.2.3 BLOCKER rehearsal (I8 sparsity). | T04 v2 Tabela 4.6 restructure, T04 v2 new BLOCKER 4, Gate Condition item 7. |
| **D6a — Tabela 4.6 grep-identity check** | **ACCEPTED.** | T01 crosswalk adds a "Tabela 4.6 ↔ Tabela 4.1/4.2/4.3 identity check" sub-section. Every rule-impact number (−24, −157, −997, −5 052, −1 185, −118, −6, etc.) grep-matched. Mismatch = halt. | T01 v2 Instructions step 6 (new), T01 v2 Verification, Halt protocol. |
| **D6b — "I9 forbids identity resolution at Phase 01" mis-cite** | **ACCEPTED.** Verified: `.claude/scientific-invariants.md` I9 (lines 163-197) is research-pipeline step discipline; I2 (lines 24-29) is canonical-nickname rule. Deferral of identity resolution is an **I2 feature-time** placement decision, not an I9 claim. | Replace I9 invocation in T03 v2 JUSTIFY #5 and Invariant-discipline check with **I2**. I9 retained only where genuinely applicable (raw-table immutability). | T03 v2 JUSTIFY #5, T03 v2 Invariant-discipline checks, Adversarial-defence rehearsal §4.2.2 BLOCKER 3. |
| **D6c — `read_csv_auto` VARCHAR claim** | **PARTIAL ACCEPT.** v1 "all 7 columns as VARCHAR" narrative is specific. | T01 v2 adds crosswalk row requiring artifact anchor. If anchoring fails, T02 softens to "CSV dtype inference produced incorrect numeric types under full multi-file scan" + `[REVIEW]` flag. | T01 v2 Instructions step 7 (new), T02 v2 JUSTIFY #4 (conditional wording). |

**Rejected critique items:** none. Two items (W2 drop-vs-defer; B2 options a/b/c) had multiple acceptable resolutions; selected options annotated above.

---

## Change log — R2 critique responses (applied in autonomous mode per `temp/r2_user_decisions.md`)

| R2 item | Severity | Decision | Fix applied | Plan section updated |
|---|---|---|---|---|
| **N1 — Artifact-prose contradiction (DS-AOEC-04 "exception" language)** | BLOCKER | **Option B: prose acknowledgment, not artifact repair.** Rationale: modifying Phase 01 artifact post-completion-gate weakens I9 research-pipeline discipline; prose acknowledgment is more honest and I9-compliant. | T04 Instructions gain a dedicated bullet + a ~400-char acknowledgment paragraph near the 26.20% routing discussion. §4.2.3 Voice note gets a one-sentence reminder. Acknowledges that the ledger artifact (DS-AOEC-04) uses "exception per Rule S4" phrasing while 26.20% is factually in the 5-40% FLAG_FOR_IMPUTATION band, framing the divergence as a cosmetic inconsistency in the ledger's taxonomy label, not a substantive routing error. Non-apologetic tone. No Phase 01 artifact modification proposed. | T04 JUSTIFY #6, T04 Instructions step 4a (new), T04 Voice note, Adversarial-defence rehearsal §4.2.3 BLOCKER 2. |
| **N2 — Jakobsen 2017 + Madley-Dowd 2019 missing** | WARNING | **Accept both: add to `references.bib`, cite Jakobsen 2017 for 40%, insert ~300-char rebuttal against Madley-Dowd 2019.** Rationale: Jakobsen 2017 is a peer-reviewed anchor stronger than van Buuren prose for 40%; Madley-Dowd 2019 is a direct challenge to proportion-driven routing that an examiner will raise. | Two new bib keys: `Jakobsen2017`, `MadleyDowd2019`. Both verified via WebFetch (DOIs, authors, years, journals below). Literature context table extended. T04 JUSTIFY #2 cites Jakobsen 2017 for the 40% threshold. T04 Instructions add a ~300-char rebuttal paragraph against Madley-Dowd 2019: (a) Madley-Dowd advocates FMI-based routing; (b) FMI requires fold-aware imputation-model fitting; (c) Phase 01 is fold-agnostic (splits in Phase 03/04); (d) rate-based routing is the only I3-compliant Phase 01 option; (e) FMI-based approaches are reserved for Phase 02 preprocessing. | Literature context table, T04 JUSTIFY #2, T04 Instructions step 3a (new — Madley-Dowd rebuttal), T04 Must cite, T04 Verification, Gate Condition item 6, File Manifest. |
| **N3 — Branch-name scope mismatch** | WARNING | **Accept: document §4.1 repair in commit message + PR body.** Rationale: renaming `docs/thesis-4.2-session` post-hoc is churn; explicit documentation prevents reviewer surprise. | T05 Integration Instructions gains an explicit directive: commit message must note §4.1 lines 41 + 195 are modified as part of the MMR MAR/MNAR consistency repair (B1 closure); PR body (if created) lists this modification as a secondary objective. | T05 Integration Instructions, Execution ordering note. |
| **N4 — T04 upper bound 13k too tight** | WARNING | **Accept: raise T04 upper bound to 15k.** Rationale: §4.1.2 consumed 22.5k for two datasets without typology; §4.2.3 at 15k upper for three datasets + typology + defence + I7 provenance + MMR-MAR commitment + two tables + §4.1 repair is ~66% per-dataset density — still terse but feasible. | T04 char budget: 10.0-15.0k (was 10.0-13.0k). Executive summary total: 24.0-30.5k (was 22.5-28.5k). Front matter `target_length_polish_chars`: 24000-30500. T04 heading, T04 Verification, Gate Condition item 2, Execution ordering table. | Executive summary, Front matter, T04 heading, T04 Instructions, T04 Verification, Gate Condition item 2, Execution ordering table. |
| **N5 — Tabela 4.6 row 5 singleton** | NIT | **Accept: retain row 5 in main table with explicit caption acknowledgment.** Rationale: fragmenting the typology by moving a canonical mechanism class (FLAG_FOR_IMPUTATION 5-40% MAR) out of Tabela 4.6 would weaken the typology's coherence more than the singleton weakens the ≥2-dataset heuristic. | Tabela 4.6 caption gains a sentence: "Wiersz FLAG_FOR_IMPUTATION 5–40% MAR jest inwokowany tylko w korpusie aoe2companion (DS-AOEC-04); zachowany w głównej tabeli jako kanoniczna klasa mechanizmu dla cechy głównej, nie jako wiersz wielokorpusowy." T04 BLOCKER 4 I8 sparsity rehearsal notes the single exception is declared in the caption. | T04 Tabela 4.6 caption text, T04 BLOCKER 4 rehearsal, Gate Condition item 7. |
| **N6 — `invariants_touched` missing I4** | NIT | **Accept: add I4.** Rationale: §4.2.3 discusses target-row consistency (POST_GAME exclusion and decisive winner filter) — I4 territory. | Front matter `invariants_touched`: `[I2, I3, I4, I5, I6, I7, I8, I9, I10]` (was `[I2, I3, I5, I6, I7, I8, I9, I10]`). T04 Invariant-discipline checks explicitly reference I4 for target-row consistency. | Front matter, T04 Invariant-discipline checks. |

**Rejected R2 items:** none. All 6 items closed per autonomous decisions.

**Bibliography verification (R2 N2):**
- **Jakobsen et al. 2017** — VERIFIED via WebFetch of https://pmc.ncbi.nlm.nih.gov/articles/PMC5717805/. Authors: Jakobsen JC, Gluud C, Wetterslev J, Winkel P. Title: "When and how should multiple imputation be used for handling missing data in randomised clinical trials – a practical guide with flowcharts." Journal: BMC Medical Research Methodology 17:162 (2017). DOI: 10.1186/s12874-017-0442-1. Key claim anchor for 40% threshold: *"If the proportions of missing data are very large (for example, more than 40%) on important variables, then trial results may only be considered as hypothesis generating results."*
- **Madley-Dowd et al. 2019** — VERIFIED via WebFetch of https://pmc.ncbi.nlm.nih.gov/articles/PMC6547017/. Authors: Madley-Dowd P, Hughes R, Tilling K, Heron J. Title: "The proportion of missing data should not be used to guide decisions on multiple imputation." Journal: Journal of Clinical Epidemiology 110:63–73 (2019). DOI: 10.1016/j.jclinepi.2019.02.016. Key claim anchor for rebuttal: advocates FMI-based routing, arguing proportion-of-missingness provides "limited information about bias and efficiency gains" from MI; simulation demonstrates unbiased results possible even at 90% missing given proper imputation-model specification.

---

## Executive summary

This plan drafts Polish-language thesis section §4.2 Data preprocessing (three subsections: §4.2.1 Ingestion & validation, §4.2.2 Player identity resolution, §4.2.3 Cleaning rules & valid corpus) in `thesis/chapters/04_data_and_methodology.md`, feeding from Phase 01 artifacts for all three datasets. Combined Polish-character target **24.0–30.5k** (revised upward from 22.5-28.5k per R2 N4; evidence: §4.1.1 alone consumed 18.5k; §4.2.3 is the richest subsection with typology + defence + I7 provenance + MMR-MAR commitment + two tables + §4.1 repair). The core methodological risk is **scope bleed from already-drafted §4.1**: §4.1 already narrates CONSORT flows, missingness ledgers, and the existence of the `*_clean` / `player_history_all` VIEWs as corpus characteristics. §4.2 must reframe the same artifacts as **preprocessing decisions** with alternatives-considered and I3/I5/I2 discipline. The plan pre-commits T01 to building a `sec_4_2_crosswalk.md` evidence file AND a mechanical Tabela 4.6 ↔ Tabela 4.1/4.2/4.3 identity-check; T02-T04 draft the three subsections at revised budgets 6.0/6.5/10.0-15.0k; T05 integrates cross-refs AND **repairs §4.1 MMR MAR/MNAR inconsistency** (line 41 narrative + Tabela 4.4b line 195 cell) to commit to a single classification; T06 polishes.

Key shifts from v1 (retained):
- **MMR classification commits to MAR-primary / MNAR-sensitivity** (per ledger row 35); §4.1 repair extends T05 scope.
- **Drops "primary-feature exception" for aoe2companion rating**; re-cites as standard MAR-FLAG routing at 5-40% band.
- **Re-cites 80% threshold as operational heuristic**, not van Buuren codified cutoff; preserves I7 traceability via literal provenance statement.
- **Re-budgets** T02/T03/T04 upward.
- **Restructures Tabela 4.6** to ≥2-dataset invocation per row; singletons in footnote Tabela 4.6a (with N5 exception: row 5 retained with caption acknowledgment).
- **Moves Wilson 2017 cite out of §4.2.1** into Appendix A forward-reference.
- **Replaces I9 mis-cite in §4.2.2 with I2**; I9 retained only for raw-table immutability.
- **Adds T01 grep-identity check** between Tabela 4.6 and §4.1 CONSORT flows.

Key shifts from v2 (new in v3):
- **Adds ~400-char prose acknowledgment paragraph in §4.2.3** reconciling the DS-AOEC-04 ledger's "exception per Rule S4" phrasing with the 5-40% FLAG_FOR_IMPUTATION band routing. Non-apologetic, non-artifact-modifying. (N1 closure.)
- **Adds two peer-reviewed bib entries: `Jakobsen2017` and `MadleyDowd2019`.** Jakobsen 2017 anchors the 40% threshold with peer-reviewed authority stronger than van Buuren prose. Madley-Dowd 2019 is pre-emptively rebutted via a ~300-char paragraph explaining Phase-01-fold-agnostic constraint forces rate-based routing over FMI-based routing. (N2 closure.)
- **T05 commit/PR scope explicitly documents §4.1 repair** to prevent reviewer surprise. (N3 closure.)
- **T04 char budget raised to 10.0-15.0k.** Total §4.2 budget now 24.0-30.5k. (N4 closure.)
- **Tabela 4.6 caption acknowledges row 5 singleton** (FLAG_FOR_IMPUTATION 5-40% MAR invoked only in aoe2companion) with explicit reasoning (canonical mechanism class, retained in main table for typological coherence). (N5 closure.)
- **`invariants_touched` gains I4** (target-row consistency: POST_GAME exclusion + decisive winner filter). T04 Invariant-discipline checks explicitly reference I4. (N6 closure.)

v3 maintains load-bearing v1/v2 strengths: Fellegi-Sunter framing, crosswalk protocol, scope-overlap table, Tabela 4.5 identifier matrix, halt protocol, symmetric 3-round adversarial cap, §4.1 repair scope, MMR MAR-primary commitment.

---

## Front matter

```yaml
category: F
branch: docs/thesis-4.2-session
plan_id: thesis-4.2-data-preprocessing-v3
target_sections:
  - §4.2.1 Ingestion i walidacja
  - §4.2.2 Rozpoznanie tożsamości gracza
  - §4.2.3 Reguły czyszczenia i ważny korpus
target_file: thesis/chapters/04_data_and_methodology.md
target_lines: 205-229 (skeleton to be replaced)
  PLUS §4.1 repair at line 41 (MMR narrative) and line 195 (Tabela 4.4b MMR mechanism cell)
feeding_phases:
  - sc2egset Phase 01 Steps 01_01-01_04 (complete)
  - aoestats Phase 01 Steps 01_01-01_04 (complete)
  - aoe2companion Phase 01 Steps 01_01-01_04 (complete)
source_artifacts: 30 files + 3 missingness ledger CSVs + 3 YAML view schemas
invariants_touched: [I2, I3, I4, I5, I6, I7, I8, I9, I10]
target_length_polish_chars: 24000-30500 (combined; v2 was 22500-28500; v1 was 18000-22000)
voice: argumentacyjna, bezosobowa polska proza akademicka
adversarial_required: yes — reviewer-adversarial R3 NOT required (autonomous-mode R2 closed all 6 items); execution-side adversarial reserved per symmetric 3-round cap
```

---

## Problem statement

Section §4.2 must narrate the transformation from raw distributed files (SC2Replay JSON; aoestats weekly Parquet; aoe2companion daily Parquet+CSV) to canonical view families (`matches_long_raw`, `matches_flat_clean` / `matches_1v1_clean`, `player_history_all`). §4.1 describes **what** the corpora look like; §4.2 describes **how** they were produced, **which alternatives** were considered, and **how I3/I4/I5/I6/I2/I9/I10 are upheld**. Four contributions distinguish §4.2 from §4.1:

1. **Two-path pipeline design for heterogeneous sources** — SC2 (nested JSON→DuckDB) vs. aoestats (variant-Parquet union_by_name) vs. aoe2companion (daily Parquet+CSV + ratings). §4.1 mentions corpus sizes; §4.2 justifies why each source needs its own ingestion pattern and shows I10 enforcement identically across all three.
2. **Identity resolution across three schemes** — SC2 `toon_id` (cardinality 2,495) vs. aoestats `profile_id` (641,662; max 24,853,897) vs. aoe2companion `profileId` (3,387,273; name-nickname 2,468,478). §4.2 classifies the schemes, defends per-dataset canonical-identifier decision, forward-references §4.3.1 for the thesis-level canonical-nickname rule (**I2**, not I9 — corrected per D6b).
3. **Cleaning-rule derivation from missingness taxonomy** — §4.2.3 defends the MCAR/MAR/MNAR classification per column, the DROP_COLUMN vs. NULLIF+flag vs. FLAG_FOR_IMPUTATION routing, and the **MissingIndicator defer** (Phase 01 produces indicators losslessly; imputation is fold-aware Phase 02 work per I3). The 5% threshold is cited to Schafer & Graham 2002; the 40% threshold to **Jakobsen 2017 (new v3 per R2 N2)** as the peer-reviewed anchor (with van Buuren 2018 prose retained as secondary general guidance); the 80% threshold is explicitly an **operational heuristic of this pipeline**. Madley-Dowd 2019's anti-proportion-threshold argument is pre-emptively rebutted via Phase-01-fold-agnostic constraint.
4. **Classification consistency repair for §4.1 MMR narrative (v2 new per B1; retained v3)** — §4.1 line 41 states MMR is MNAR while ledger row 35 classifies MMR as MAR-primary with MNAR-sensitivity. §4.2 execution must repair §4.1 narrative to commit to one classification (MAR-primary per ledger); otherwise §4.2 and §4.1 contradict each other. **v3 addition per R2 N3:** T05 commit message + PR body explicitly document this §4.1 repair to prevent diff-reviewer surprise.

Out-of-scope: corpus descriptive stats (§4.1), feature engineering (§4.3), split design (§4.4), MMR/Elo mechanism (§2.5).

---

## Assumptions & unknowns

### Assumptions (validated during investigation)

1. **§4.2.1–§4.2.3 DRAFTABLE after Phase 01 01_01–01_04 complete for all three datasets.** Verified — 30 artifacts on disk. Phase 01 Steps 01_05/01_06 deferred; any claim needing 01_05 flagged `[REVIEW]`.

2. **The crosswalk pattern from §4.1 is load-bearing.** `sec_4_1_crosswalk.md` anchors 101 rows. v2/v3 extends with `sec_4_2_crosswalk.md` + mechanical Tabela 4.6 ↔ §4.1 CONSORT identity check.

3. **Polish voice calibrated to §4.1, §2.1–§2.6, §3.1–§3.3.** Data-fed, argumentative, bezosobowa.

4. **§4.2 is section-final in §4 chapter that is DRAFTABLE now.** §4.3/§4.4 BLOCKED.

5. **The ledger's MAR-primary / MNAR-sensitivity framing is authoritative** — §4.1 line 41 and Tabela 4.4b line 195 must align to this. The ledger is the artifact committed in Phase 01 Step 01_04_01 (authoritative per I9: Phase 01 artifacts are source of truth for Phase 01 findings).

6. **(v3 per R2 N1) The DS-AOEC-04 ledger's "exception per Rule S4" phrasing is a cosmetic taxonomy label inconsistency, not a substantive routing error.** 26.20% falls in the 5-40% FLAG_FOR_IMPUTATION band; routing is substantively correct. §4.2.3 acknowledges the divergence in prose without proposing Phase 01 artifact modification (I9 discipline).

### Unknowns (flag; do not stall)

1. Polish translation conventions — adopt §4.1 verbatim.
2. §4.2.3 duplicate vs. reference decision — §4.2.3 presents **one** consolidated Tabela 4.6 (restructured per W3; row-5 singleton acknowledged in caption per R2 N5). Other singletons in Tabela 4.6a footnote.
3. Whether §4.2.1 needs a figure — no; defer to Appendix A.
4. **aoe2companion rating 26.20% mechanism — RESOLVED per B2/R2 N1.** `01_04_01_data_cleaning.json:2197` says MAR; rate in 5-40% band; standard MAR-FLAG routing (NOT exception). `[REVIEW]` flag retained since primary-feature MAR at 26% is high-stakes. v3 prose paragraph reconciles DS-AOEC-04 artifact language with factual routing.
5. Scope creep around §2.5 MMR mechanics — every MMR appearance gets forward-ref to §2.5 or §4.3.1.
6. Whether §4.1 MMR repair in T05 is scope-acceptable — **v2/v3 commits yes**: inconsistency is drafting defect; leaving uncorrected is visible on examination. **v3 addition per R2 N3:** commit/PR text documents the repair to prevent reviewer surprise.

---

## Literature context

### Already in `references.bib` (reuse)

| Key | Role in §4.2 |
|---|---|
| `Rubin1976` | §4.2.3 taxonomy backbone; Tabela 4.6 classifies rules by mechanism |
| `vanBuuren2018` | §4.2.3 prose guidance "proportion < about 30-40%"; MissingIndicator strategy; hedging reference for 80% operational heuristic |
| `SchaferGraham2002` | §4.2.3 5% MCAR boundary (unambiguous literature-backed threshold) |
| `Bialecki2023` | §4.2.1 SC2EGSet source format + ToonPlayerDescMap structure |
| `AoEStats` | §4.2.1 aoestats source |
| `AoeCompanion` | §4.2.1 aoe2companion source |
| `BlizzardS2Protocol` | §4.2.1 optional s2protocol decode cite |
| `MgzParser` | §4.2.1 deliberate non-use cite |

### New bib entries to add (4 total in v3; v2 had 2; v1 had 5)

| Key | Citation | Where | State |
|---|---|---|---|
| `FellegiSunter1969` | Fellegi & Sunter 1969, JASA 64(328), 1183-1210, DOI:10.1080/01621459.1969.10501049 | §4.2.2 framing | **VERIFIED** canonical |
| `Christen2012DataMatching` | Christen 2012, Springer, ISBN 978-3-642-31163-5 | §4.2.2 reframed as **standard introductory textbook** per W1 | **VERIFIED** |
| `Jakobsen2017` (v3 new per R2 N2) | Jakobsen JC, Gluud C, Wetterslev J, Winkel P (2017). "When and how should multiple imputation be used for handling missing data in randomised clinical trials – a practical guide with flowcharts." BMC Medical Research Methodology 17:162. DOI:10.1186/s12874-017-0442-1. URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC5717805/ | §4.2.3 40% threshold peer-reviewed anchor (stronger than van Buuren 2018 prose) | **VERIFIED via WebFetch** (2026-04-18 session) |
| `MadleyDowd2019` (v3 new per R2 N2) | Madley-Dowd P, Hughes R, Tilling K, Heron J (2019). "The proportion of missing data should not be used to guide decisions on multiple imputation." Journal of Clinical Epidemiology 110:63–73. DOI:10.1016/j.jclinepi.2019.02.016. URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC6547017/ | §4.2.3 rebutted pre-emptively (FMI-based routing requires fold-aware imputation model fitting — Phase 01 is fold-agnostic per I3, so rate-based routing is the only I3-compliant Phase 01 posture) | **VERIFIED via WebFetch** (2026-04-18 session) |

### Deferred / removed per v2/v3

| Key | v1 disposition | v3 disposition | Rationale |
|---|---|---|---|
| `Wilson2017GoodEnough` | proposed for §4.2.1 | **DEFERRED to Appendix A forward-reference** per W2 | Grey-literature editorial; citing inside DuckDB paragraph double-burdens thin "implementation is methodology" argument |
| `LittleRubin2019` | optional | Deferred unchanged | Redundant with Rubin1976+vanBuuren2018 |
| `Pedregosa2011Sklearn` | optional | Deferred unchanged | vanBuuren2018 covers indicator strategy directly |

### Citation gaps and flags

- **CONSORT/STROBE/RECORD for flow tables.** §4.1 uses "CONSORT-style" for flow tables (not Tabela 4.6 typology). Tabela 4.6 is a typology matrix so the label does not apply there — footnote.
- **Parquet/Arrow validation.** No peer-reviewed paper; narrative argues as general reproducibility principle.

---

## Execution Steps

### T01 — Build §4.2 numerical crosswalk + Tabela 4.6 identity check

**Objective:** Produce `thesis/pass2_evidence/sec_4_2_crosswalk.md` following `sec_4_1_crosswalk.md` 8-column schema. Every §4.2 number anchored. Plus "Tabela 4.6 ↔ Tabela 4.1/4.2/4.3 identity check" section (D6a).

**Instructions:**
1. Read `sec_4_1_crosswalk.md` header/format; reproduce 8-column schema + number-format normalization rule.
2. Enumerate candidate numbers from 30 artifacts (paths below, absolute):
   - SC2: `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/` — 01_01_01, 01_01_02, 01_02_01-04, 01_03_01-02, 01_04_00-02 `.md` files + `01_04_01_missingness_ledger.csv` (**CRITICAL: row 35 for MMR mechanism classification**).
   - aoestats: analogous 10 artifacts under `src/rts_predict/games/aoe2/datasets/aoestats/`.
   - aoe2companion: analogous 10 artifacts under `src/rts_predict/games/aoe2/datasets/aoe2companion/` (**CRITICAL: `01_04_01_data_cleaning.json` lines 2180-2220 for rating classification; lines 1030-1050 for threshold provenance; lines ~2197-2200 for DS-AOEC-04 "exception" phrasing anchor per R2 N1**).
   - `data/db/schemas/views/*.yaml` per dataset.
3. For each number, populate row: `claim_text | artifact_path | anchor | prose_form (PL) | artifact_form (raw) | normalized_value | datatype | hedging_needed`.
4. Classification-of-new-citations header table: **4** candidates in v3 (up from 2 v2, down from 5 v1): `FellegiSunter1969`, `Christen2012DataMatching`, **`Jakobsen2017` (new v3)**, **`MadleyDowd2019` (new v3)**.
5. "Scope-overlap with §4.1" table (≥15 rows expected).
6. **(D6a): "Tabela 4.6 ↔ §4.1 CONSORT flows identity check" table.** Candidate list: −24 meczów R01 SC2; −157 meczów R03 SC2; −997 meczów R08 aoestats; −5 052 meczów R03 aoe2companion; −6 wierszy R02 aoe2companion; −1 185 wierszy aoestats ingestion filter; −118 wierszy DS-AOESTATS-03; 1 132 DS-SC2-10; 2 DS-SC2-09; 273 DS-SC2-06. Grep-match each against §4.1 prose + Tabela 4.1/4.2/4.3. Any mismatch → HALT.
7. **(D6c): Anchor aoe2companion `read_csv_auto` claim** against `01_02_02_duckdb_ingestion.md`. If "all 7 VARCHAR" phrasing isn't in artifact, row records actual artifact phrasing and T02 softens.
8. **(B2): Three threshold-provenance rows:**
   - `threshold-5pct`: `01_04_01_data_cleaning.json:1042` → Schafer & Graham 2002.
   - `threshold-40pct` (v3 reframed per R2 N2): primary anchor `Jakobsen2017` ("more than 40% … only hypothesis generating results"); secondary anchor van Buuren 2018 prose.
   - `threshold-80pct`: `01_04_01_data_cleaning.json:1042` "Operational starting heuristics from `temp/null_handling_recommendations.md §1.2`"; file verified absent.
9. **(B1): Two MMR mechanism rows:**
   - `mmr-mechanism-sc2-flat`: `01_04_01_missingness_ledger.csv:35` `mechanism=MAR`, MAR-primary w/ MNAR-sensitivity branch.
   - `mmr-mechanism-sc2-history`: `01_04_01_missingness_ledger.csv:85` same classification for `player_history_all`.
10. **(v3 new per R2 N1): DS-AOEC-04 "exception" phrasing anchor row** in crosswalk: records verbatim artifact prose (`01_04_01_data_cleaning.json:~2198` mechanism_justification AND `01_04_01_data_cleaning.md:~281` DS-AOEC-04 Question) alongside factual 5-40% routing; row flagged as "cosmetic taxonomy inconsistency" for T04 acknowledgment paragraph.
11. **Halt predicate:** >5 numbers unanchored within 5 lookups each, OR identity-check mismatch.

**Verification:**
- File exists; 92-132 rows (v2 was 90-130; v1 was 80-120; +2 v3 for DS-AOEC-04 phrasing row and possible Jakobsen/Madley-Dowd anchor rows).
- Scope-overlap table ≥15 rows.
- Identity-check table all resolved or halt-flagged.
- Classification table has 4 new bib entries (v3: Fellegi-Sunter, Christen, Jakobsen, Madley-Dowd).
- Three threshold-provenance rows anchored (with v3 N2 Jakobsen addition for 40%).
- Two MMR-mechanism rows anchored.
- One DS-AOEC-04 phrasing row anchored (v3 new).

**File scope:** writes `thesis/pass2_evidence/sec_4_2_crosswalk.md`.

**Read scope:** 30 artifact .md files; 3 missingness CSVs; aoe2companion `01_04_01_data_cleaning.json` (lines 1030-1050, 2180-2220, and `01_04_01_data_cleaning.md:~281`); `sec_4_1_crosswalk.md`; `04_data_and_methodology.md` §4.1.

**Char budget:** 7-11k Markdown (v2 was 7-11k; v1 was 6-10k; v3 retains v2 range — +1 row is negligible).

**Risk:** Low-medium. Mechanical + new identity-check logic.

---

### T02 — Draft §4.2.1 Ingestion i walidacja (Polish)

**Objective:** Draft §4.2.1 arguing two-path ingestion. **Target 6.0-7.5k Polish chars** (v2/v3 widened from 5-7k per B3).

**Must justify:**
1. **DuckDB over Postgres/BigQuery.** Alternative = columnar DW. Decision = embedded DuckDB w/ `tmp/` spill. Reason: I6 reproducibility via single-process per notebook, free at ~300M rows, native Parquet/JSON, WAL-free CTAS. **(v2/v3 per W2): no Wilson 2017 cite. Forward-ref to Appendix A.**
2. **Split SC2 metadata/events into separate tables.** Alt = single wide w/ STRUCT[]. Decision = `replays_meta_raw` (22,390) + `replay_players_raw` (44,817) + `map_aliases_raw` (104,160) + 3 Parquet-backed event VIEWs. Reason: 367.6 GB events vs. ~1 GB metadata (01_02_01). Cite `01_02_01_duckdb_pre_ingestion.md`.
3. **`union_by_name=true` for aoestats variant schemas.** Alt = first-file schema force-cast. Decision = `union_by_name=true` + post-ingest type unification (`profile_id` DOUBLE→BIGINT in 36 files; `started_timestamp` us/ns promotion). Reason: 172-week schema drift; force-cast would lose variants or silently coerce IDs >2^53.
4. **aoe2companion explicit dtype for ratings CSVs.** Alt = `read_csv_auto`. Decision = explicit BIGINT/TIMESTAMP on 2,072 CSVs. Reason = CSV dtype inference produced incorrect numeric types under full multi-file scan `[REVIEW: D6c — verify exact column-count and dtype mapping against 01_02_02_duckdb_ingestion.md]`. Conditional wording preserves decision rationale without unverifiable specificity.
5. **I10 inline CTAS substring vs. post-load UPDATE.** Alt = UPDATE. Decision = `substr(filename, {prefix_len})` in CTAS. Reason: OOM on 107M (aoestats) and 277M (aoe2companion) with UPDATE; inline is canonical across all three.

**Must contrast:** DuckDB vs. Airflow/Prefect/Dagster orchestrators. Hedge: "Dla większych obciążeń produkcyjnych preferowane byłyby orkiestratory; wymagania reprodukowalności pracy magisterskiej faworyzują architekturę jednoprocesową."

**Must cite:** `Bialecki2023`, `AoEStats`, `AoeCompanion`, `BlizzardS2Protocol` (optional). **No `Wilson2017GoodEnough` in body text per W2.**

**Tables/Figures:** None. Prose + cross-refs to §4.1 Tabela 4.1/4.2/4.3.

**Cross-references:** Back §4.1.1.2, §4.1.2.0. Forward §4.3, §4.4, **Appendix A (Wilson 2017 forward-ref per v2 W2)**, §4.2.2, §4.2.3.

**Invariant checks:** I6 (reproducibility via preserved SQL in JSON artifacts), I9 (raw immutability — correct use: `.claude/scientific-invariants.md:163-197`), I10 (inline CTAS protocol), I3 (flagged as view-construction layer).

**Out-of-scope:** corpus stats; `*_clean` views; event extraction detail; player-history vs. target split; §2.2.4 PlayerStats periodicity.

**Voice:** argumentative; each paragraph closes with "Decyzja o X wynika z Y cytowany z Z; alternatywą byłoby W, odrzucone z powodu reason".

**Instructions:**
1. Three paragraphs per dataset (~1.8-2.3k chars each subsection): source format, ingestion decision w/ alternatives, validation check.
2. Closing cross-cutting paragraph (~900 chars) — I6/I9/I10 enforced identically across three sources = I8 preprocessing layer.
3. Every number anchored to crosswalk.
4. Polish typography.
5. `[REVIEW]` flags: (a) I10 CROSS research_log narrative acceptability; (b) D6c `read_csv_auto` exact claim.

**Verification:**
- §4.2.1 exists; **6,000 ≤ len ≤ 7,500 chars** (v2/v3).
- Every number in crosswalk.
- ≥4 "decyzja wynika z / alternatywą byłoby" patterns.
- 2-4 `[REVIEW]` flags.
- **No Wilson 2017 citation in §4.2.1 body (W2 compliance).**

**File scope:** writes `thesis/chapters/04_data_and_methodology.md` §4.2.1 only.

**Read scope:** crosswalk; SC2/aoestats/aoe2companion 01_01-01_02 artifacts; `/Users/tomaszpionka/Projects/rts-outcome-prediction/reports/research_log.md` CROSS 2026-04-14; §4.1 lines 1-203; `thesis/references.bib`.

**Char budget:** 6,000-7,500 Polish chars.

**Risk:** Medium. Scope-creep into corpus stats + DuckDB oversell. Mitigations: scope-overlap table consulted per paragraph; DuckDB paragraphs ≤3 sentences; W2 removes Wilson 2017 grey-lit exposure.

---

### T03 — Draft §4.2.2 Rozpoznanie tożsamości gracza (Polish)

**Objective:** Draft §4.2.2 arguing per-dataset canonical-identifier decisions against record-linkage literature, forward-ref to thesis-level canonical-nickname rule (**I2** per D6b correction, not I9). **Target 6.5-8.0k Polish chars** (v2/v3 widened).

**Must justify:**
1. **`toon_id` as SC2 identifier in `matches_flat_clean`.** Alt = nickname (2,495 distinct toon_id vs. 1,106 nicks → 18 games/player vs. 40 games/nick). Reason: 2,495 > 1,106 means nicks REUSE across accounts (alias "Serral", generic "Player"). Phase 01 decision = `toon_id`; I2 canonical nickname deferred to Phase 02. Cite `01_02_04_univariate_census.md` + `Christen2012DataMatching` (**reframed per W1 as "standard introductory textbook"**, not "canonical").
2. **aoestats `profile_id` treated as strong globally-unique.** Alt = record linkage. Decision = trust. Reason: 641,662 distinct in 107M plausible; API stability; max 24,853,897 < 2^53.
3. **aoe2companion `profileId` treated authoritative despite name-fragmentation.** Alt = nickname reconciliation. Decision = `profileId` authoritative; name-fragmentation (3,387,273 IDs vs. 2,468,478 names) is source characteristic. Reason = inferring multiple profileIds per player is Phase 02 per **I2** (D6b correction); raw-table immutability per **I9** (correct narrow use).
4. **Multi-dataset identity NOT unified across SC2/AoE2.** Alt = cross-game player graph. Decision = per-game. Reason: RQ scope is method-level cross-game, not player-level; no public Battle.net/aoe2.net mapping; linkage would explode scope. Cite `FellegiSunter1969` as framing + hedge per W1: "Współczesne rozszerzenia neuronowe (DeepMatcher et al.) w tradycji [Christen2012DataMatching] nie są używane."
5. **Identity-resolution deferred to Phase 02 (§4.3.1).** Alt = resolve at cleaning time. Decision = `*_clean` retains raw identifiers; canonical key assigned per-target-row Phase 02. **Reason per D6b correction: Invariant I2** operationalizes canonical nickname at feature-engineering time, not cleaning time. I9 applies to raw-table immutability only. Cite `.claude/scientific-invariants.md:24-29` I2 definition.

**Must contrast:** "Trust-the-ID + lowercase-nickname later" vs. classic Fellegi-Sunter / Christen 2012 record-linkage pipeline. Argument: our IDs are high-quality; linkage addresses no-stable-ID scenarios. Hedge: "Zagadnienie pozostaje referencyjne, nie operacyjne."

**Must cite:** `FellegiSunter1969` (new), `Christen2012DataMatching` (new — standard textbook per W1), `Bialecki2023`, `AoEStats`, `AoeCompanion`.

**Tables:** **Tabela 4.5** (retained from v1) — cross-dataset identifier comparison (10 rows: id column name, raw type, cardinality, population scope, mean games/player, nickname cardinality, id-to-nick ratio, multi-account inference, status in `*_clean`, Phase 02 plan).

**Citations needed:** 2 new + 3 existing.

**Cross-references:** Back §4.1.1.5 (single-sentence), §1.2. Forward §4.3.1 (symmetric feature engineering grounded in **I2**), §4.4.1 (per-player temporal split).

**Invariant checks (v2/v3 corrected per D6b):**
- **I2 (primary for §4.2.2):** Phase 01 defers I2 operationalization to Phase 02. Cite `.claude/scientific-invariants.md:24-29` verbatim.
- **I9 (narrow scope):** no identity resolution modifies `*_raw` tables.
- **(v1's erroneous "I9 forbids feature-layer transformations" framing REMOVED — correct invariant is I2.)**

**Out-of-scope:** multi-account resolution; player-coverage histogram; Elo/MMR (§2.5/§4.2.3).

**Voice:** argumentative; "consciously minimal — sufficient IDs, no over-engineering".

**Instructions:**
1. Opening (~700 chars): frame identity problem, cite Fellegi-Sunter + Christen, pre-announce I2 deferral.
2. One paragraph per dataset (~1,200-1,500 chars): identifier, cardinality evidence, fragmentation observability, Phase 01 decision.
3. Closing (~900 chars): coherent strategy (ID trust + deferred canonicalization), cite **I2** (not I9).
4. Tabela 4.5 after paragraph 4.
5. `[REVIEW]` flags: (a) aoe2companion 2,468,478 nicknames vs artifact; (b) SC2 toon_id > nickname multi-account interpretation; (c) Christen 2012 "introductory textbook" framing per W1.

**Verification:**
- §4.2.2 exists; **6,500 ≤ len ≤ 8,000 chars** (v2/v3).
- Tabela 4.5 present.
- 5 citations resolved.
- Forward-ref grounded in **I2**, not I9.
- No Phase 02 computation.
- **Christen 2012 framed per W1.**

**File scope:** `04_data_and_methodology.md` §4.2.2 + Tabela 4.5; `references.bib` adds `FellegiSunter1969`, `Christen2012DataMatching` (T04 adds `Jakobsen2017`, `MadleyDowd2019` — total +4 new bib entries under v3).

**Read scope:** crosswalk; 01_02_04 census + 01_03_01 profile JSON per dataset; 01_01_02 schema for SC2; §4.1 voice; `references.bib`; `.claude/scientific-invariants.md:24-29`.

**Char budget:** 6,500-8,000.

**Risk:** Medium-high. Over-claiming multi-account, new bib Pass 2 verification, Phase 02 creep. Mitigations: hedged language, `[REVIEW]` flags, explicit I2 forward-ref.

---

### T04 — Draft §4.2.3 Reguły czyszczenia i ważny korpus (Polish) — 10.0-15.0k chars

**Objective:** Draft §4.2.3 cross-dataset cleaning-rule typology, MissingIndicator I3-compliance defence, per-dataset invocations. **Target 10.0-15.0k Polish chars** (v3 widened from 10.0-13.0k per R2 N4; richest subsection: typology + defence + I7 provenance + MMR-MAR commitment + two tables + §4.1 repair + N1 acknowledgment + N2 rebuttal).

**Must justify:**
1. **Rule-based registry vs. ad-hoc fixes.** Decision = formal registry w/ R/DS IDs. Reason: reviewability, I6, I8 (unified typology).
2. **Classify by Rubin1976 taxonomy BEFORE routing (v2/v3 reframed per B2/R2 N2).** Decision = mechanism first, then rate-band routing under **operational-heuristic thresholds**. Thresholds provenance (v3 explicit):
   - **<5% MCAR → RETAIN_AS_IS.** Provenance: Schafer & Graham 2002 (literature-backed, unambiguous).
   - **5–40% MAR → FLAG_FOR_IMPUTATION.** Provenance: **`Jakobsen2017` as primary peer-reviewed anchor (new v3 per R2 N2) — "more than 40% on important variables → results only hypothesis-generating"**; van Buuren 2018 prose "can be trusted when proportion missing < about 30-40%" retained as secondary general guidance (convergent authority).
   - **≥80% MAR/MNAR → DROP_COLUMN + MissingIndicator flag.** Provenance: **operational heuristic of this pipeline**, traceable internally to now-deleted `temp/null_handling_recommendations.md §1.2` (`01_04_01_data_cleaning.json:1042`). NOT a peer-reviewed constant; operationalizes Jakobsen's/van Buuren's general guidance conservatively. §4.2.3 prose paragraph: "Próg 80% sentynelu jest heurystyką operacyjną niniejszego pipeline'u, konsekwentnie stosowaną we wszystkich trzech korpusach. Nie jest to konstanta cytowana wprost z [Jakobsen2017, vanBuuren2018], lecz konserwatywne zaostrzenie ogólnej rekomendacji [Jakobsen2017], że powyżej 40% wyniki analiz są wyłącznie hipotezo-generujące." Cite `.claude/scientific-invariants.md:86-96` I7 — compliance via documentation-inline.
3. **MissingIndicator I3-compliant.** Alternatives: impute at cleaning / drop rows. Decision = NULLIF + binary flag (`is_mmr_missing`, `p0_is_unrated`, `rating_was_null`). Reason: (a) I3 forbids computing features from time-T-or-later info; cleaning-time imputation leaks future statistics; (b) missingness carries signal (MMR=0 = "unrated professional" subgroup); (c) Phase 02 fold-aware imputation preserves I3. Cite `Rubin1976`, `vanBuuren2018`, `.claude/scientific-invariants.md:40-49` I3 normalization-leakage clause.
4. **SC2 MMR=0 classification MAR-primary / MNAR-sensitivity (v2/v3 per B1).** Ledger: `01_04_01_missingness_ledger.csv:35` says MAR with "MAR-primary: missingness depends on observed replay source (tournament replays lack ladder MMR). MNAR (private pro accounts) documented as sensitivity branch." Interpretation: "tournament replay" is observable attribute (replay source/context), so MAR per strict Rubin taxonomy. MNAR retained as sensitivity branch for partially-unobservable player-type signal. §4.2.3 commits to MAR-primary, acknowledges MNAR branch, hedges. Flag `[REVIEW: MAR-primary vs MNAR-sensitivity — primary feature]`. **Key: routing (DROP_COLUMN + MissingIndicator) identical under both — both MAR and MNAR at ≥80% route to DROP. Key v2/v3 fix: §4.1.1.4 line 41 + Tabela 4.4b line 195 say MNAR; T05 repairs both.**
5. **Per-dataset rule counts differ.** Decision = per-dataset tailoring on dataset-specific sentinels. Reason: typology unified (mechanism × rate × action); invocations differ. I8 at methodology layer.
6. **aoe2companion `rating` 26.20% → FLAG_FOR_IMPUTATION (v2/v3 reframed per B2).** Ledger: `01_04_01_data_cleaning.json:2197` says `mechanism=MAR`. Rate 26.20% in **5-40% MAR band** (NOT 40-80%). Routing per standard rule S3: FLAG_FOR_IMPUTATION + `rating_was_null` indicator. This is **standard MAR-FLAG routing**, NOT an exception. v1's "primary-feature exception" framing was based on misread and is removed. Cite `01_04_01_data_cleaning.json:2200` verbatim: "Rate 26.20% in 5-40%; flag for Phase 02 imputation." No appeal to non-existent van Buuren exception. **(v3 new per R2 N1):** §4.2.3 also includes a ~400-char prose acknowledgment that the DS-AOEC-04 ledger artifact itself (`01_04_01_data_cleaning.json:~2198` mechanism_justification + `01_04_01_data_cleaning.md:~281` Question cell) uses the phrasing "exception per Rule S4"; §4.2.3 frames this as cosmetic inconsistency in the ledger's taxonomy label (not a substantive routing error), since 26.20% is factually in the 5-40% FLAG_FOR_IMPUTATION band where FLAG is the standard (not exceptional) routing. Non-apologetic, non-artifact-modifying. See Instructions step 4a.

**Must contrast:**
- MissingIndicator vs. MICE (van Buuren 2018). MICE requires fit-on-training-only → I3. Phase 01 `*_clean` VIEWs are fold-agnostic; imputation defers to Phase 02. MissingIndicator losslessly preserves signal.
- **Rate-based routing vs. FMI-based routing (Madley-Dowd 2019) — v3 new per R2 N2.** Madley-Dowd 2019 argues proportion-of-missingness is a poor guide to imputation decisions; advocates Fraction of Missing Information (FMI) as an alternative. Rebuttal (~300 chars, Instructions step 3a): (a) FMI requires fitting an imputation model to estimate; (b) imputation model fitting is fold-aware work (imputation parameters must not leak across train/test folds per I3); (c) Phase 01 is explicitly fold-agnostic (folds are constructed in Phase 03/04); (d) therefore rate-based routing is the only I3-compliant decision procedure available at Phase 01; (e) FMI-based approaches are reserved for Phase 02 fold-aware preprocessing, where they remain compatible with this pipeline's architecture.
- Three-threshold system vs. single 30% drop threshold. Three-threshold is mechanism-defensible: 5% Schafer & Graham, **40% Jakobsen 2017 peer-reviewed (v3 new)**, **80% pipeline operational heuristic documented inline per I7**. Single threshold ignores mechanism.

**Must cite:** `Rubin1976`, `vanBuuren2018`, `SchaferGraham2002`, **`Jakobsen2017` (v3 new)**, **`MadleyDowd2019` (v3 new, in rebuttal)**. `.claude/scientific-invariants.md` I3/I7 clauses.

**Tables:**
- **Tabela 4.6 (v2/v3 restructured per W3; v3 caption extended per R2 N5)** — 8-row cross-dataset typology; every row has ≥2-dataset invocations EXCEPT row 5 (explicitly acknowledged in caption):
  1. Scope-filter (zakresowy filtr korpusu) — SC2 R01 / aoestats R02 / aoe2companion R01
  2. Target-consistency filter — SC2 R01-część / aoestats R08 / aoe2companion R03
  3. Sentinel → NULLIF (<5% MCAR low-rate) — SC2 DS-SC2-09/10 / aoestats DS-AOESTATS-02/03 / — aoe2companion singleton (none)
  4. DROP_COLUMN ≥80% (operational heuristic) — SC2 DS-SC2-01/02/03 / aoestats DS-AOESTATS constants / aoe2companion DS-AOEC-01
  5. FLAG_FOR_IMPUTATION 5-40% MAR — (SC2 nd) / (aoestats nd) / aoe2companion DS-AOEC-02/04/05 (**rating 26.20% standard-band routing, NOT exception per B2; row acknowledged in caption per R2 N5 as single-corpus invocation retained for typological coherence**)
  6. MissingIndicator-plus-NULLIF — SC2 DS-SC2-01/10 / aoestats DS-AOESTATS-02 / aoe2companion DS-AOEC-04
  7. Schema-evolution exclusion — SC2 DS-SC2-06 / aoestats opening/age_uptime / aoe2companion R04
  8. Constants/duplicates drop — SC2 DS-SC2-08 / aoestats DS-AOESTATS-04/08 / (aoe2companion inlined)

  **Caption (v3, Polish, per R2 N5):** "Tabela 4.6. Typologia reguł czyszczenia stosowanych w trzech korpusach, klasyfikowana wg mechanizmu missingness × pasma częstości × akcji. Wiersz FLAG_FOR_IMPUTATION 5–40% MAR jest inwokowany tylko w korpusie aoe2companion (DS-AOEC-04); zachowany w głównej tabeli jako kanoniczna klasa mechanizmu dla cechy głównej, nie jako wiersz wielokorpusowy. Pozostałe invokacje jedno-korpusowe umieszczono w Tabeli 4.6a."

  Rows with one `(nd)` are retained (still ≥2-dataset); rows with two `(nd)` move to Tabela 4.6a — except row 5 per caption.

- **Tabela 4.6a (v2/v3 per W3)** — compact per-dataset singleton footnote (3 rows, one per dataset):
  - SC2EGSet: R03 MMR<0 replay-level exclusion (−157); implicit POST_GAME I3 (`elapsedGameLoops` in `player_history_all` only).
  - aoestats: ingestion-level `profile_id`/`started_timestamp IS NOT NULL` (−1 185 wierszy AI-przeciwnicy); R06 (`new_rating` excluded both VIEWs — POST_GAME I3).
  - aoe2companion: R02 dedup matchId×profileId (−6 wierszy); implicit `ratingDiff` POST_GAME I3.

**Citations needed:** 5 primary (3 existing + 2 new v3) + intra-doc invariants.

**Cross-refs:** Back §4.1.1.4, §4.1.2.1, §4.1.2.2, §2.5.4. Forward §4.3.1, §4.4.2, §6.5, §2.5.

**Crosswalk entries:** 35-50 rows (per-dataset impacts, rates, column flows, assertions) + 3 threshold-provenance + 2 MMR-mechanism + 1 DS-AOEC-04 phrasing row (v3 new).

**Invariant checks:**
- **I3 (primary defence):** Phase 01 fold-agnostic → any Phase 01 imputation leaks future-fold info → Phase 02 fold-aware imputation preserves I3 → MissingIndicator losslessly preserves signal. Cite `:40-49`. **v3 extension per R2 N2:** Madley-Dowd 2019 rebuttal is a direct I3 application — FMI requires imputation-model fitting which must be fold-aware.
- **I4 (target-row consistency, v3 new per R2 N6):** §4.2.3 enforces I4 at two points: (a) POST_GAME column exclusion (`elapsedGameLoops`, `new_rating`, `ratingDiff` etc. excluded from `*_clean` VIEWs — Tabela 4.6a explicitly lists these); (b) decisive-winner filter (target-consistency filter in Tabela 4.6 row 2 excludes rows without unambiguous outcome labels). Cite `.claude/scientific-invariants.md` I4 section.
- **I5:** slot symmetry preserved (asymmetries documented, not corrected).
- **I6:** SQL verbatim in `01_04_01_data_cleaning.json`.
- **I7 (v2/v3 explicit per B2/R2 N2):** every threshold carries provenance inline. 5% → Schafer & Graham 2002 (literature). **40% → Jakobsen 2017 peer-reviewed anchor (v3 new) + van Buuren 2018 prose (secondary)**. **80% → operational heuristic of this pipeline, documented inline per I7's "document its derivation inline" requirement** — traceable to deleted internal doc. §4.2.3 states explicitly: 80% is operational, not peer-reviewed.
- **I8:** typology unified (Tabela 4.6 ≥2-dataset; row 5 exception acknowledged in caption per R2 N5); singletons explicit (Tabela 4.6a). Methodology identical across datasets.
- **I9:** rules operate on VIEWs; raw tables never modified. Cite `:163-197`. **v3 addition per R2 N1:** §4.2.3's acknowledgment of DS-AOEC-04 artifact "exception" phrasing does NOT propose Phase 01 artifact modification — I9 discipline preserved; acknowledgment is prose-only.

**Out-of-scope:** Phase 02 imputation detail; §4.1 CONSORT re-narration (identity check confirms no drift); column-count detail; §2.5 mechanics; 01_05 findings.

**Voice:** argumentative; every rule-class: mechanism + rate + action + alternative + rejection + cite. MissingIndicator defence forward-leaning. **v3 addition per R2 N1:** the DS-AOEC-04 "exception" acknowledgment is framed non-apologetically as a good-faith divergence between ledger taxonomy label and factual routing band — the thesis commits to the factual 5-40% FLAG classification and explains why without implying the Phase 01 artifact is wrong on substance (the routing itself IS standard FLAG_FOR_IMPUTATION at 26.20%).

**Instructions:**
1. Opening (~1,100 chars): typology-before-invocation; cite three taxonomy references (Rubin 1976, van Buuren 2018, Schafer & Graham 2002) + Jakobsen 2017 (v3 new for 40% threshold); pre-announce MissingIndicator I3 defence; pre-announce MMR MAR-primary/MNAR-sensitivity commitment.
2. Paragraph per rule class (~600-900 chars each, 7-8 classes from Tabela 4.6).
3. **I7 threshold-provenance paragraph (~900 chars; v3 extended per R2 N2):** state 5% literature-backed (Schafer & Graham 2002), **40% peer-reviewed Jakobsen 2017 (primary) + van Buuren 2018 prose (secondary convergent guidance)**, 80% operational-heuristic inline-documented. I7 compliance footer.
3a. **Madley-Dowd 2019 rebuttal paragraph (~300 chars; v3 new per R2 N2).** Structure: (a) Madley-Dowd 2019 argues against proportion-driven imputation routing, advocating FMI-based alternative; (b) FMI requires fitting an imputation model to estimate; (c) imputation-model fitting is fold-aware work (parameters cannot leak across folds per I3); (d) Phase 01 is explicitly fold-agnostic (splits are constructed in Phase 03/04); (e) therefore rate-based routing is the only I3-compliant decision procedure available at Phase 01; FMI-based approaches remain available and compatible at Phase 02. Cite `MadleyDowd2019` + `.claude/scientific-invariants.md` I3 clause.
4. **MMR MAR-primary / MNAR-sensitivity paragraph (~600 chars):** commit to ledger, acknowledge MNAR branch, routing-invariant at ≥80%, `[REVIEW]` flag.
4a. **DS-AOEC-04 "exception" acknowledgment paragraph (~400 chars; v3 new per R2 N1).** Structure: (a) note that the Phase 01 ledger artifact `01_04_01_data_cleaning.md` DS-AOEC-04 Question cell and the underlying `01_04_01_data_cleaning.json:~2198` mechanism_justification use the phrasing "exception per Rule S4"; (b) observe that at 26.20% the rate is factually in the 5-40% band where FLAG_FOR_IMPUTATION is the standard routing per the registry (not an exceptional routing); (c) frame the "exception" language as a cosmetic inconsistency in the ledger's taxonomy label — reflecting the primary-feature importance of `rating` in aoe2companion rather than a non-standard rule application; (d) the thesis commits to the factual 5-40% FLAG classification; the Phase 01 ledger artifact is preserved unchanged per I9 research-pipeline discipline. Non-apologetic tone throughout — this is a good-faith divergence between ledger narrative phrasing and registry taxonomy, not an error.
5. Closing defence (~1,100 chars): MissingIndicator I3-compliance + mechanism-first routing + I7 provenance + Madley-Dowd rebuttal + I3 fold-aware Phase 02 + I4 target-row consistency all cohere.
6. Tabela 4.6 between opening and per-rule paragraphs. Caption per R2 N5 acknowledges row 5 singleton.
7. Tabela 4.6a as compact footnote after Tabela 4.6.
8. `[REVIEW]` flags: (a) MAR-primary vs MNAR-sensitivity for MMR; (b) 80% operational-heuristic framing acceptability; (c) I8 unified-typology post-restructure; (d) §4.1 repair prose integrity; (e) rating 26.20% standard-band framing Pass 2; (f) DS-AOEC-04 "exception" acknowledgment wording Pass 2 (v3 new); (g) Jakobsen 2017 + Madley-Dowd 2019 bib-entry Pass 2 verification (v3 new).

**Verification:**
- §4.2.3 exists; **10,000 ≤ len ≤ 15,000** (v3; v2 was 10,000-13,000).
- Tabela 4.6 present; every non-`(nd)` row ≥2-dataset EXCEPT row 5 explicitly acknowledged in caption per R2 N5.
- Tabela 4.6a present as footnote.
- 5 primary citations resolved (Rubin 1976, van Buuren 2018, Schafer & Graham 2002, Jakobsen 2017, Madley-Dowd 2019).
- ≥5 "alternatywą byłoby / decyzja wynika z" patterns.
- ≥2 MissingIndicator defence sentences citing I3.
- I7 threshold-provenance paragraph present; all three thresholds have provenance statements; Jakobsen 2017 cited for 40%.
- Madley-Dowd 2019 rebuttal paragraph present (~300 chars).
- DS-AOEC-04 "exception" acknowledgment paragraph present (~400 chars).
- MMR paragraph commits MAR-primary, acknowledges MNAR, states routing invariance.
- I4 discipline checks referenced (POST_GAME exclusion + decisive-winner filter).
- ≥3 `[REVIEW]` flags (v3 expected closer to 5-7 given new flags f, g).

**File scope:** `04_data_and_methodology.md` §4.2.3 + Tabela 4.6 + Tabela 4.6a. `references.bib` adds `Jakobsen2017` and `MadleyDowd2019` (T03 adds `FellegiSunter1969` and `Christen2012DataMatching` — total +4 new bib entries across v3; v2 was +2).

**Read scope:** crosswalk; all three 01_04_01 `data_cleaning.md`; all three `missingness_ledger.csv` (SC2 row 35 CRITICAL); aoe2companion `01_04_01_data_cleaning.json` lines 1030-1050 + 2180-2220 + `01_04_01_data_cleaning.md:~281`; all three 01_04_02; 01_04_00 source-normalization; §4.1 lines 41-43, 89-94, 124-132, 195; `.claude/scientific-invariants.md` I3:40-49, I4 (target-row consistency section), I7:86-96, I9:163-197; Jakobsen 2017 abstract (verified via WebFetch); Madley-Dowd 2019 abstract (verified via WebFetch).

**Char budget:** 10,000-15,000 (v3; v2 was 10,000-13,000).

**Risk:** **High.** Mitigations per v2/v3: typology framing + scope-overlap check; explicit closing defence; MAR-primary/MNAR-sensitivity commitment + T05 §4.1 repair; I7 threshold-provenance paragraph; Tabela 4.6 restructure + 4.6a footnote + row-5 caption acknowledgment; T01 identity-check halt; v3 N1 prose acknowledgment pre-empts artifact-contradiction critique; v3 N2 Jakobsen 2017 + Madley-Dowd rebuttal strengthens threshold defence.

---

### T05 — Integrate cross-refs, REPAIR §4.1 MMR classification, update tracking

**Objective:** Cross-reference integration + **§4.1 MMR MAR/MNAR inconsistency repair (v2 new per B1)** + tracking-files updates. **v3 addition per R2 N3:** explicit commit message + PR body documentation of §4.1 repair scope.

**Sub-step 0 (v2 per B1) — §4.1 MMR classification repair.** Runs BEFORE cross-reference validation.
- **Line 41 rewrite:** "Mechanizm tej missingness jest klasyfikowany jako MNAR … nie losowo." → "Mechanizm tej missingness jest klasyfikowany w ledgerze missingness (`01_04_01_missingness_ledger.csv`) jako **MAR-primary z gałęzią sensitywną MNAR** wg taksonomii [Rubin1976] — missingness zależy od obserwowalnego atrybutu (źródło powtórki turniejowe, w którym brak przypisania ladderowego), z równoległą gałęzią MNAR dla graczy z prywatnymi kontami zawodowymi (niedostępność MMR zależna od typu konta, wartość częściowo nieobserwowalna). §4.2.3 rozwija uzasadnienie klasyfikacji i operacjonalizuje routing DROP_COLUMN + MissingIndicator, identyczny dla obu interpretacji na tym poziomie sentynelu (≥80%)."
- **Line 195 rewrite:** Tabela 4.4b SC2 "Mechanizm dominującej missingness" cell: "MNAR (MMR=0 unrated prof.)" → "MAR-primary / MNAR-sensitivity (MMR=0 unrated prof.; per ledger)".
- Diff scope ~400 chars; net ~+250 chars to §4.1.
- Verification: grep `MNAR` post-repair — expected zero standalone "MNAR (MMR=0 …" references outside §4.2.3's MAR-primary/MNAR-sensitivity framing.
- REVIEW_QUEUE §4.1.1 row updated: append "v2 §4.2 drafting surfaced MMR MAR/MNAR inconsistency; §4.1.1.4 line 41 + Tabela 4.4b line 195 repaired per ledger."

**Sub-step 1 — cross-reference validation.** Scan §4.2.1/§4.2.2/§4.2.3 references; resolve to §4.1 (post-repair), §2.5/§2.2, BLOCKED §4.3/§4.4 (flag).

**Sub-step 2 — WRITING_STATUS.md update.** Append three new §4.2.x DRAFTED rows w/ char counts. Update §4.1.1 row per sub-step 0.

**Sub-step 3 — REVIEW_QUEUE.md update.** Append three new §4.2.x Pending rows; update §4.1.1 row.

**Sub-step 4 — CROSS research_log entry.** `/Users/tomaszpionka/Projects/rts-outcome-prediction/reports/research_log.md` — heading `[CROSS] 2026-04-18 — §4.2 Data preprocessing draft + §4.1 MMR classification repair`; narrate 3 subsections, §4.1 repair, new bib entries (v3: `FellegiSunter1969`, `Christen2012DataMatching`, `Jakobsen2017`, `MadleyDowd2019`; Wilson2017 deferred to Appendix A per W2), Tabela 4.6 restructure + row-5 caption acknowledgment, DS-AOEC-04 prose acknowledgment in §4.2.3 (per R2 N1), Madley-Dowd rebuttal paragraph (per R2 N2).

**Sub-step 5 — Halt log.** Append to new `thesis/pass2_evidence/sec_4_2_halt_log.md`.

**Integration Instructions (v3 per R2 N3):**
- **T05 commit message** must explicitly note that §4.1 lines 41 and 195 are modified as part of the MMR MAR/MNAR consistency repair (B1 closure). Draft wording for commit message (example): "docs(thesis): §4.2 Data preprocessing draft + §4.1 MMR classification repair (B1). Primary scope: §4.2.1/2/3 in `04_data_and_methodology.md`. Secondary scope: §4.1.1.4 line 41 narrative and Tabela 4.4b line 195 cell repaired to MAR-primary / MNAR-sensitivity per ledger row 35 (resolves §4.1 ↔ §4.2 classification inconsistency surfaced during §4.2 drafting)." Commit-message file path follows user memory directive: write to `.github/tmp/commit.txt` then `git commit -F`.
- **PR body (if created)** must list the §4.1 repair as a secondary objective in a dedicated section (Summary: Primary objective — §4.2 draft; Secondary objective — §4.1 MMR MAR/MNAR consistency repair per ledger authority) to avoid surprising diff reviewers. PR-body file path follows user memory directive: write to `.github/tmp/pr.txt` then `gh pr create --body-file`; delete after PR creation.

**Verification:**
- §4.1 line 41 + Tabela 4.4b line 195 updated to MAR-primary/MNAR-sensitivity.
- WRITING_STATUS has 3 new §4.2.x + §4.1.1 repair note.
- REVIEW_QUEUE has 3 new + §4.1.1 update.
- CROSS research_log entry present; documents §4.1 repair + DS-AOEC-04 prose acknowledgment (v3 N1) + Madley-Dowd rebuttal (v3 N2).
- halt log exists.
- All `[REVIEW]` → corresponding REVIEW_QUEUE row.
- **v3 per R2 N3:** commit message (and PR body if applicable) explicitly narrates §4.1 repair scope.

**File scope:** `04_data_and_methodology.md` (§4.1 repair + §4.2 cross-ref fixes); `WRITING_STATUS.md`; `REVIEW_QUEUE.md`; `research_log.md`; `sec_4_2_halt_log.md` (new); `pass2_evidence/README.md`; `.github/tmp/commit.txt` (commit message file per user memory); `.github/tmp/pr.txt` (PR body file per user memory, if PR created).

**Read scope:** §4.2 drafts; tracking files; `01_04_01_missingness_ledger.csv` row 35 verbatim for repair anchor.

**Char budget:** metadata + ~250 chars §4.1 repair + commit message + PR body.

**Risk:** Low-medium. Repair text must match ledger wording — read row 35 verbatim. Regex scan for REVIEW_QUEUE completeness. T05 sub-step 0 scope-creep guard: >500 net chars of §4.1 change = HALT.

---

### T06 — Lexical and typographic polish

**Objective:** Per `.claude/author-style-brief-pl.md` operational checklist.

**Instructions:**
1. Anglicism pass.
2. Doubled-word scan across §4.2.x + repaired §4.1.1.4 paragraph.
3. Interpunction audit for sentences >30 words.
4. Dopełniacz chain audit.
5. Polish typography.
6. Cross-ref sanity rerun.
7. **v2 check:** verify §4.1 repair integrates smoothly w/ surrounding §4.1.1.4 prose.
8. **v3 check:** verify DS-AOEC-04 acknowledgment paragraph (T04 step 4a) is non-apologetic in tone and does not imply artifact-is-wrong.
9. **v3 check:** verify Madley-Dowd 2019 rebuttal paragraph (T04 step 3a) does not overstate rebuttal strength (acknowledge Madley-Dowd argument on its merits for fold-aware contexts).

**Verification:** no -ować calques; no doubled words; italicized/glossed/retained anglicisms; no >3-element dopełniacz chain; Polish typography; §4.1 repair seamless; DS-AOEC-04 acknowledgment non-apologetic; Madley-Dowd rebuttal measured.

**File scope:** `04_data_and_methodology.md` polish within §4.2 + §4.1.1.4 repair.

**Risk:** Low.

---

## File Manifest

| File | Task | Role |
|---|---|---|
| `thesis/pass2_evidence/sec_4_2_crosswalk.md` | T01 writes | Crosswalk + Tabela 4.6 ↔ §4.1 identity check + MMR/threshold-provenance rows + DS-AOEC-04 phrasing row (v3 new) |
| `thesis/chapters/04_data_and_methodology.md` | T02/T03/T04/T05/T06 | §4.2.1/§4.2.2/§4.2.3 + §4.1.1.4 line 41 repair + Tabela 4.4b line 195 cell repair |
| `thesis/references.bib` | T03, T04 | **+4 entries in v3** (v2 was +2): `FellegiSunter1969` + `Christen2012DataMatching` (T03); `Jakobsen2017` + `MadleyDowd2019` (T04 per R2 N2). Wilson2017 DEFERRED to Appendix A per W2. |
| `thesis/WRITING_STATUS.md` | T05 | +3 DRAFTED rows; §4.1.1 row updated |
| `thesis/chapters/REVIEW_QUEUE.md` | T05 | +3 Pending rows; §4.1.1 row updated |
| `reports/research_log.md` | T05 | CROSS 2026-04-18 entry (narrates §4.1 repair + DS-AOEC-04 acknowledgment + Madley-Dowd rebuttal) |
| `thesis/pass2_evidence/sec_4_2_halt_log.md` | T05 writes (new) | Halt log |
| `thesis/pass2_evidence/README.md` | T05 | Index table +2 rows |
| `.github/tmp/commit.txt` | T05 writes (ephemeral) | Commit message per user memory directive; explicit §4.1 repair scope narration (v3 per R2 N3) |
| `.github/tmp/pr.txt` | T05 writes (ephemeral, if PR created) | PR body per user memory directive; explicit secondary-objective §4.1 repair section (v3 per R2 N3); deleted after PR creation |

---

## Gate Condition

§4.2 is DRAFTED when all hold:

1. §4.2.1/2/3 populated in `04_data_and_methodology.md`, HTML-comment skeletons replaced.
2. Combined §4.2 Polish char count ∈ **[24,000 − 30,500]** (v3; v2 was 22,500-28,500).
3. `sec_4_2_crosswalk.md` exists w/ all numerical claims anchored; "Tabela 4.6 ↔ §4.1 CONSORT" identity-check table zero-mismatch; threshold-provenance + MMR-mechanism + DS-AOEC-04 phrasing rows populated; `sec_4_2_halt_log.md` exists.
4. WRITING_STATUS lists §4.2.1/2/3 DRAFTED; §4.1.1 row reflects MMR repair.
5. REVIEW_QUEUE has 3 new Pending + §4.1.1 update.
6. `references.bib` has **4 new entries** (v3: `FellegiSunter1969`, `Christen2012DataMatching`, **`Jakobsen2017`**, **`MadleyDowd2019`**); **no Wilson2017** in v3 body text. Both new v3 entries verified via WebFetch with DOIs recorded (Jakobsen: 10.1186/s12874-017-0442-1; Madley-Dowd: 10.1016/j.jclinepi.2019.02.016).
7. Tabela 4.5 and Tabela 4.6 w/ Polish captions; Tabela 4.6 ≥2-dataset per row EXCEPT row 5 explicitly acknowledged in caption as single-corpus invocation retained for typological coherence (per R2 N5); Tabela 4.6a singleton footnote present.
8. Every threshold has provenance: 5% → `SchaferGraham2002` cite; **40% → `Jakobsen2017` primary peer-reviewed anchor (v3) + `vanBuuren2018` prose secondary**; **80% → explicitly operational heuristic of this pipeline, documented inline per I7**. No "van Buuren 80% codified" claim. No "40% is unsourced" claim (Jakobsen 2017 anchors it).
9. MissingIndicator has explicit I3-compliance defence paragraph.
10. **Madley-Dowd 2019 rebuttal paragraph present** (~300 chars, per R2 N2), citing Phase-01-fold-agnostic I3 constraint; does not overstate rebuttal.
11. **§4.1 MMR repair completed:** line 41 + Tabela 4.4b line 195 aligned to MAR-primary/MNAR-sensitivity per ledger row 35.
12. **aoe2companion rating 26.20% framed as standard MAR-FLAG at 5-40% band**, NOT "primary-feature exception".
13. **DS-AOEC-04 "exception" acknowledgment paragraph present** (~400 chars, per R2 N1): non-apologetic prose framing of ledger artifact's "exception per Rule S4" phrasing as cosmetic taxonomy inconsistency with factual 5-40% FLAG routing. No Phase 01 artifact modification proposed.
14. **§4.2.2 cites I2 for Phase 02 deferral**, not I9 (except for raw-table immutability narrow use).
15. **`invariants_touched` includes I4** (v3 per R2 N6); T04 I4 discipline checks explicitly reference POST_GAME exclusion + decisive-winner filter.
16. **T05 commit message** (and PR body if PR created) explicitly narrates §4.1 repair as secondary objective (v3 per R2 N3).
17. CROSS 2026-04-18 entry in research_log narrates §4.1 repair + DS-AOEC-04 acknowledgment + Madley-Dowd rebuttal + all 4 new bib entries.
18. No `[UNVERIFIED]` flags; `[REVIEW]` allowed.
19. Critical-review checklist (data variant) passes.

---

## Out of scope

1. Phase 02 feature engineering (§4.3).
2. Split design (§4.4.1).
3. Model configs (§4.4.2).
4. Evaluation metrics (§4.4.4 — already DRAFTABLE; not §4.2).
5. MMR mechanism / Glicko theory (§2.5 DRAFTED).
6. Corpus descriptive stats (§4.1.x DRAFTED).
7. In-game feature engineering (§4.3.2).
8. AoE2 civilization encoding (§4.3.3).
9. Figure generation (Appendix A).
10. Cross-game identity unification (§7.3).
11. 01_05 Temporal & Panel EDA outputs.
12. 01_06 Decision Gates.
13. **Wilson 2017 citation** (deferred to Appendix A per v2 W2).
14. **§4.1 sections beyond MMR repair** — only line 41 + Tabela 4.4b line 195; no other §4.1 text touched.
15. **(v3 per R2 N1): Phase 01 artifact modification** — §4.2.3 prose acknowledges DS-AOEC-04 "exception" phrasing divergence without proposing artifact rewrite. Phase 01 artifacts remain immutable per I9 discipline.
16. **(v3 per R2 N2): FMI-based imputation design** — Madley-Dowd 2019 rebuttal explains why FMI is Phase 02 work, not Phase 01 work; actual FMI design is out-of-scope for §4.2.
17. **(v3 per R2 N3): branch rename** — `docs/thesis-4.2-session` retained; §4.1 repair scope surfaced via commit message + PR body instead.

---

## Open questions

All R1/R2 items closed by user and autonomous decisions. No unresolved items for v3. The 7 open questions from v2 are archived here for traceability:

1. **Scope overlap with §4.1.** Accepted — typology framing.
2. **§4.1 MMR repair scope.** Accepted — line 41 + Tabela 4.4b line 195.
3. **80% operational-heuristic framing.** Accepted — explicit "pipeline heuristic, not peer-reviewed cutoff".
4. **New bib entries.** v3 = 4 (v2 = 2; v1 = 5): `FellegiSunter1969`, `Christen2012DataMatching`, `Jakobsen2017` (v3 new), `MadleyDowd2019` (v3 new).
5. **CONSORT/STROBE/RECORD.** Footnote flagging Tabela 4.6 typology inapplicability.
6. **Halt protocol.** §4.1 had 3+3 cap; §4.2 R1→v2→v3 substantive revisions completed; R3 plan-side adversarial reserved (autonomous-mode R2 closed all 6 items). Execution-side adversarial budget preserved.
7. **Repair narration in research_log.** Explicit narration accepted; v3 extends to explicit commit message + PR body narration per R2 N3.

No new open questions introduced by v3.

---

## Adversarial-defence rehearsal (top BLOCKERs per subsection)

### §4.2.1

**BLOCKER 1 — Scope creep re-narrating §4.1.** Pre-emption: scope-overlap table per paragraph; §4.2.1 reuses numbers only for decision framing.

**BLOCKER 2 — DuckDB is implementation, not methodology.** Pre-emption: ≤3-sentence DuckDB paragraphs; explicit "nie jest kontrybucją metodologiczną" acknowledgment. **v2: no Wilson 2017 cite (W2).**

**BLOCKER 3 — I10 research_log narrative is historic noise.** Pre-emption: ≤2 sentences; `[REVIEW]` flag.

### §4.2.2

**BLOCKER 1 — Multi-account interpretation is speculation.** Pre-emption: hedging ("sugeruje"/"spójne z"), `[REVIEW]` flag, forward-ref §4.3.1.

**BLOCKER 2 — Fellegi-Sunter cite is gratuitous.** Pre-emption: frame as non-use ("referencyjne, nie operacyjne") + Christen 2012 as **standard introductory textbook** (W1).

**BLOCKER 3 — Deferral is non-work.** Pre-emption (v2 per D6b): **justify via I2** (canonical-nickname at feature-engineering time), not I9. §4.2.2 classifies + commits to boundary.

### §4.2.3

**BLOCKER 1 — MissingIndicator is a cop-out.** Pre-emption: explicit closing defence. Structure: Phase 01 fold-agnostic → Phase 01 imputation leaks future → Phase 02 fold-aware preserves I3 → MissingIndicator lossless → MissingIndicator is only I3-compliant Phase 01 posture. Cite Rubin1976, vanBuuren2018, I3 clause verbatim.

**BLOCKER 2 — Thresholds are magic numbers (I7 violation).** Pre-emption (v2/v3 per B2/R2 N2): explicit I7 threshold-provenance paragraph. 5% → Schafer & Graham 2002 literature. **40% → Jakobsen 2017 peer-reviewed primary anchor (v3) + van Buuren 2018 prose secondary.** **80% → operational heuristic of this pipeline, documented inline per I7's "document derivation inline" requirement**, traceable to deleted internal doc. Compliance via documentation-inline, not pseudo-citation. **v3 addition: Madley-Dowd 2019 rebuttal paragraph pre-empts "you should use FMI" examiner question** — FMI requires fold-aware imputation-model fitting, Phase 01 is fold-agnostic per I3, so rate-based routing is the only I3-compliant Phase 01 option; FMI reserved for Phase 02. **v3 per R2 N1: DS-AOEC-04 "exception" acknowledgment paragraph pre-empts "your thesis contradicts your ledger artifact" examiner question** — divergence framed as cosmetic taxonomy inconsistency between ledger narrative phrasing and factual routing; ledger artifact preserved per I9 discipline.

**BLOCKER 3 — MAR for MMR is wrong, should be MNAR.** Pre-emption (v2 per B1): **commit to MAR-primary / MNAR-sensitivity per ledger row 35.** MMR paragraph explicit: "MAR-primary pochodzi z ledgera — missingness zależy od obserwowalnego atrybutu. MNAR-sensitivity dla prywatnych kont zawodowych. [REVIEW]." **Routing identical at ≥80% under both.** Key v2 addition: **§4.1.1.4 line 41 + Tabela 4.4b line 195 REPAIRED in T05 — §4.2 and §4.1 agree.** **v3 per R2 N3: repair scope surfaced in commit message + PR body to prevent diff-reviewer surprise.**

**BLOCKER 4 (v2 per W3; v3 extended per R2 N5) — Tabela 4.6 sparsity undermines I8.** Pre-emption: **Tabela 4.6 restructured** ≥2-dataset invocations per row; singletons in Tabela 4.6a footnote. I8 claim rests on MCAR/MAR/MNAR × rate × action typology (genuinely unified, demonstrated post-restructure). Singletons admitted as dataset-specific (honest rather than fragile). **v3 single exception (row 5 FLAG_FOR_IMPUTATION 5-40% MAR, aoe2companion-only) declared explicitly in table caption** as canonical mechanism class retained for typological coherence — not hidden. Closing paragraph: "Typologia (Tabela 4.6) wspólna; singletonowe invokacje (Tabela 4.6a) nie podważają jedności metodologii — są invokacjami tego samego typu reguły na dataset-specific sentynelu. Wiersz 5 (Tabela 4.6) jest wyjątkiem deklarowanym jawnie w nagłówku tabeli."

---

## Halt protocol

Mirrors §4.1 halt protocol (see `sec_4_1_halt_log.md`):

- **Per-task:** number unanchored within 5 lookups → `[UNVERIFIED]` inline.
- **Aggregate:** >5 `[UNVERIFIED]` per subsection → halt + user handoff.
- **v2 per D6a:** T01 identity-check mismatch → halt until resolved (Tabela 4.6 wording change / §4.1 correction / artifact re-extraction).
- **v2 per B1:** T05 sub-step 0 §4.1 MMR repair alters §4.1.1.4 >500 net chars → halt (scope creep).
- **v3 per R2 N1:** T04 DS-AOEC-04 acknowledgment paragraph ≥600 chars OR implies artifact-is-wrong-on-substance → halt (scope/tone creep).
- **v3 per R2 N2:** T04 Madley-Dowd rebuttal paragraph ≥500 chars OR overstates rebuttal (e.g., claims FMI is "wrong" rather than "out-of-scope for fold-agnostic Phase 01") → halt.
- **v3 per R2 N3:** T05 commit message omits §4.1 repair narration → halt (reviewer-surprise prevention violated).
- Every halt appended to `sec_4_2_halt_log.md`; zero-halt drafts attest zero events explicitly.

---

## Execution ordering and risk summary

| Task | Char budget (v3) | Risk | Depends on |
|---|---|---|---|
| T01 Crosswalk + identity check | 7-11k MD | Low-medium (new identity-check) | — |
| T02 §4.2.1 | 6.0-7.5k PL | Medium | T01 |
| T03 §4.2.2 | 6.5-8.0k PL | Medium-High | T01 |
| T04 §4.2.3 | **10.0-15.0k PL** (v3; v2 was 10.0-13.0k per R2 N4) | High | T01 |
| T05 Integration + §4.1 repair + commit/PR narration | ~250 chars §4.1 + metadata + commit.txt + pr.txt | Low-medium (§4.1 scope + commit/PR text accuracy per R2 N3) | T02/T03/T04 |
| T06 Polish | — (edits) | Low | T05 |

**Total §4.2: 24.0-30.5k Polish chars** (v3; v2 was 22.5-28.5k; v1 was 18-22k). Plus ~250 chars §4.1 repair.

---

## Critical self-check

- [x] category F
- [x] Sequential T01-T06
- [x] File Manifest captures §4.1 repair + commit.txt + pr.txt (v3)
- [x] No forbidden taxonomy terms
- [x] `invariants_touched`: **[I2, I3, I4, I5, I6, I7, I8, I9, I10]** (v3: I4 added per R2 N6)
- [x] R1 Change log at top of plan
- [x] **R2 Change log immediately below R1 (v3 new)**
- [x] Every R1 BLOCKER has verdict + fix + pointer
- [x] Every R1 WARNING has verdict + fix + pointer
- [x] Every R2 item (6 total: 1 BLOCKER, 3 WARNINGs, 2 NITs) has autonomous-mode decision + fix + pointer
- [x] B1/B2 artifact-claim verifications executed (ledger row 35; JSON line 2200; JSON line 1042)
- [x] B3 budget evidence referenced (§4.1.1=18.5k, §4.1.2=22.5k, §4.1.3=5.7k)
- [x] R2 N2 bib entries verified via WebFetch (Jakobsen 2017 DOI 10.1186/s12874-017-0442-1; Madley-Dowd 2019 DOI 10.1016/j.jclinepi.2019.02.016)
- [x] Tabela 4.6 restructured per W3; row-5 caption acknowledgment added per R2 N5
- [x] Wilson 2017 deferred per W2 (not removed; moved to Appendix A)
- [x] I9→I2 correction per D6b
- [x] D6a identity-check added to T01
- [x] D6c conditional wording planned for T02
- [x] **v3 R2 N1**: DS-AOEC-04 prose acknowledgment paragraph (~400 chars) added to T04 step 4a; no artifact modification proposed
- [x] **v3 R2 N2**: Jakobsen 2017 cited for 40% in T04 step 3 I7 paragraph; Madley-Dowd 2019 rebuttal paragraph (~300 chars) added to T04 step 3a; both bib entries verified
- [x] **v3 R2 N3**: T05 Integration Instructions direct commit message + PR body to narrate §4.1 repair
- [x] **v3 R2 N4**: T04 budget raised to 10.0-15.0k; executive summary total 24.0-30.5k; front matter updated
- [x] **v3 R2 N5**: Tabela 4.6 caption acknowledges row 5 singleton as canonical-mechanism retention
- [x] **v3 R2 N6**: I4 added to `invariants_touched`; T04 Invariant-discipline checks reference I4 (POST_GAME + decisive-winner)
- [x] Category F → R3 plan-side adversarial NOT required per autonomous-mode R2 closure; execution-side adversarial budget preserved per symmetric 3-round cap
- [x] v2 line count 760 + projected growth ~60 lines for N1/N2/R2 change log ≈ 820-850 lines (within requested 800-1400 target)

---

## Critique instruction (Category F — mandatory)

**R3 plan-side adversarial NOT required.** Per `temp/r2_user_decisions.md`, autonomous pilot has closed all 6 R2 items with concrete decisions applied in v3. Per symmetric 3-round cap, plan-side adversarial budget is exhausted; execution-side adversarial budget is preserved.

**Next step:** parent persists this plan to `planning/current_plan.md` and dispatches executor(s) for T01-T06 sequential execution. Execution-side reviewer-adversarial runs after execution completes (not before), per Category F protocol. If execution surfaces substantive methodology concerns not anticipated by R1/R2 (e.g., new artifact contradictions discovered during crosswalk build), executor halts per halt protocol and parent escalates.

---

## Paths referenced (absolute)

- Plan file (v3): `/Users/tomaszpionka/.claude/plans/nested-meandering-octopus-agent-a1fd9df3fb4b603fa.md` (current session)
- Plan file (v2): referenced from `/Users/tomaszpionka/Projects/rts-outcome-prediction/temp/plan_4_2_v2.md`
- v1 plan: `/Users/tomaszpionka/Projects/rts-outcome-prediction/temp/plan_4_2_v1.md`
- R1 critique: `/Users/tomaszpionka/Projects/rts-outcome-prediction/temp/critique_4_2_r1.md`
- **R2 critique: `/Users/tomaszpionka/Projects/rts-outcome-prediction/temp/critique_4_2_r2.md`**
- **R2 autonomous-mode decisions: `/Users/tomaszpionka/Projects/rts-outcome-prediction/temp/r2_user_decisions.md`**
- Thesis chapter: `/Users/tomaszpionka/Projects/rts-outcome-prediction/thesis/chapters/04_data_and_methodology.md` (lines 41, 195 targeted for repair in T05)
- Scientific invariants: `/Users/tomaszpionka/Projects/rts-outcome-prediction/.claude/scientific-invariants.md` (I2:24-29; I3:40-49; I4 target-row consistency; I7:86-96; I9:163-197; I10:131-159)
- SC2 ledger row 35 (B1 anchor): `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv`
- aoe2companion rating artifact (B2 + R2 N1 anchor): `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json` lines 1030-1050 (threshold provenance), 2180-2220 (rating row), ~2198 (DS-AOEC-04 "exception" phrasing anchor per R2 N1)
- aoe2companion DS-AOEC-04 markdown anchor (R2 N1): `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md` line ~281
- Jakobsen 2017 (v3 R2 N2): https://pmc.ncbi.nlm.nih.gov/articles/PMC5717805/ (DOI 10.1186/s12874-017-0442-1)
- Madley-Dowd 2019 (v3 R2 N2): https://pmc.ncbi.nlm.nih.gov/articles/PMC6547017/ (DOI 10.1016/j.jclinepi.2019.02.016)
- Writing status: `/Users/tomaszpionka/Projects/rts-outcome-prediction/thesis/WRITING_STATUS.md`
- Review queue: `/Users/tomaszpionka/Projects/rts-outcome-prediction/thesis/chapters/REVIEW_QUEUE.md`
- Commit message file (T05 per user memory): `/Users/tomaszpionka/Projects/rts-outcome-prediction/.github/tmp/commit.txt`
- PR body file (T05 per user memory, if PR created): `/Users/tomaszpionka/Projects/rts-outcome-prediction/.github/tmp/pr.txt`

---

End of plan v3. Ready for parent to persist to `temp/plan_4_2_v3.md` (and thereafter to `planning/current_plan.md`), then dispatch T01-T06 execution per sequential ordering.