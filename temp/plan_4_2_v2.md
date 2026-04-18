# Plan v2: Category F — §4.2 Data preprocessing (Polish)

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

## Executive summary

This plan drafts Polish-language thesis section §4.2 Data preprocessing (three subsections: §4.2.1 Ingestion & validation, §4.2.2 Player identity resolution, §4.2.3 Cleaning rules & valid corpus) in `thesis/chapters/04_data_and_methodology.md`, feeding from Phase 01 artifacts for all three datasets. Combined Polish-character target **22.5–28.5k** (revised upward from 18-22k per B3; evidence: §4.1.1 alone consumed 18.5k). The core methodological risk is **scope bleed from already-drafted §4.1**: §4.1 already narrates CONSORT flows, missingness ledgers, and the existence of the `*_clean` / `player_history_all` VIEWs as corpus characteristics. §4.2 must reframe the same artifacts as **preprocessing decisions** with alternatives-considered and I3/I5/I2 discipline. The plan pre-commits T01 to building a `sec_4_2_crosswalk.md` evidence file AND a mechanical Tabela 4.6 ↔ Tabela 4.1/4.2/4.3 identity-check; T02-T04 draft the three subsections at revised budgets 6.0/6.5/10.0-13.0k; T05 integrates cross-refs AND **repairs §4.1 MMR MAR/MNAR inconsistency** (line 41 narrative + Tabela 4.4b line 195 cell) to commit to a single classification; T06 polishes.

Key shifts from v1:
- **MMR classification commits to MAR-primary / MNAR-sensitivity** (per ledger row 35); §4.1 repair extends T05 scope.
- **Drops "primary-feature exception" for aoe2companion rating**; re-cites as standard MAR-FLAG routing at 5-40% band.
- **Re-cites 80% threshold as operational heuristic**, not van Buuren codified cutoff; preserves I7 traceability via literal provenance statement.
- **Re-budgets** T02/T03/T04 upward; total 22.5-28.5k.
- **Restructures Tabela 4.6** to ≥2-dataset invocation per row; singletons in footnote Tabela 4.6a.
- **Moves Wilson 2017 cite out of §4.2.1** into Appendix A forward-reference.
- **Replaces I9 mis-cite in §4.2.2 with I2**; I9 retained only for raw-table immutability.
- **Adds T01 grep-identity check** between Tabela 4.6 and §4.1 CONSORT flows.

v2 maintains load-bearing v1 strengths: Fellegi-Sunter framing, crosswalk protocol, scope-overlap table, Tabela 4.5 identifier matrix, halt protocol, symmetric 3-round adversarial cap.

---

## Front matter

```yaml
category: F
branch: docs/thesis-4.2-session
plan_id: thesis-4.2-data-preprocessing-v2
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
invariants_touched: [I2, I3, I5, I6, I7, I8, I9, I10]
target_length_polish_chars: 22500-28500 (combined; v1 was 18-22k)
voice: argumentacyjna, bezosobowa polska proza akademicka
adversarial_required: yes — reviewer-adversarial R2 required before execution
```

---

## Problem statement

Section §4.2 must narrate the transformation from raw distributed files (SC2Replay JSON; aoestats weekly Parquet; aoe2companion daily Parquet+CSV) to canonical view families (`matches_long_raw`, `matches_flat_clean` / `matches_1v1_clean`, `player_history_all`). §4.1 describes **what** the corpora look like; §4.2 describes **how** they were produced, **which alternatives** were considered, and **how I3/I5/I6/I2/I9/I10 are upheld**. Four contributions distinguish §4.2 from §4.1:

1. **Two-path pipeline design for heterogeneous sources** — SC2 (nested JSON→DuckDB) vs. aoestats (variant-Parquet union_by_name) vs. aoe2companion (daily Parquet+CSV + ratings). §4.1 mentions corpus sizes; §4.2 justifies why each source needs its own ingestion pattern and shows I10 enforcement identically across all three.
2. **Identity resolution across three schemes** — SC2 `toon_id` (cardinality 2,495) vs. aoestats `profile_id` (641,662; max 24,853,897) vs. aoe2companion `profileId` (3,387,273; name-nickname 2,468,478). §4.2 classifies the schemes, defends per-dataset canonical-identifier decision, forward-references §4.3.1 for the thesis-level canonical-nickname rule (**I2**, not I9 — corrected per D6b).
3. **Cleaning-rule derivation from missingness taxonomy** — §4.2.3 defends the MCAR/MAR/MNAR classification per column, the DROP_COLUMN vs. NULLIF+flag vs. FLAG_FOR_IMPUTATION routing, and the **MissingIndicator defer** (Phase 01 produces indicators losslessly; imputation is fold-aware Phase 02 work per I3). The 5% threshold is cited to Schafer & Graham 2002; the 30-40% range to van Buuren 2018 prose; the 80% threshold is explicitly an **operational heuristic of this pipeline**.
4. **Classification consistency repair for §4.1 MMR narrative (v2 new per B1)** — §4.1 line 41 states MMR is MNAR while ledger row 35 classifies MMR as MAR-primary with MNAR-sensitivity. §4.2 execution must repair §4.1 narrative to commit to one classification (MAR-primary per ledger); otherwise §4.2 and §4.1 contradict each other.

Out-of-scope: corpus descriptive stats (§4.1), feature engineering (§4.3), split design (§4.4), MMR/Elo mechanism (§2.5).

---

## Assumptions & unknowns

### Assumptions (validated during investigation)

1. **§4.2.1–§4.2.3 DRAFTABLE after Phase 01 01_01–01_04 complete for all three datasets.** Verified — 30 artifacts on disk. Phase 01 Steps 01_05/01_06 deferred; any claim needing 01_05 flagged `[REVIEW]`.

2. **The crosswalk pattern from §4.1 is load-bearing.** `sec_4_1_crosswalk.md` anchors 101 rows. v2 extends with `sec_4_2_crosswalk.md` + mechanical Tabela 4.6 ↔ §4.1 CONSORT identity check.

3. **Polish voice calibrated to §4.1, §2.1–§2.6, §3.1–§3.3.** Data-fed, argumentative, bezosobowa.

4. **§4.2 is section-final in §4 chapter that is DRAFTABLE now.** §4.3/§4.4 BLOCKED.

5. **The ledger's MAR-primary / MNAR-sensitivity framing is authoritative** — §4.1 line 41 and Tabela 4.4b line 195 must align to this. The ledger is the artifact committed in Phase 01 Step 01_04_01 (authoritative per I9: Phase 01 artifacts are source of truth for Phase 01 findings).

### Unknowns (flag; do not stall)

1. Polish translation conventions — adopt §4.1 verbatim.
2. §4.2.3 duplicate vs. reference decision — §4.2.3 presents **one** consolidated Tabela 4.6 (restructured per W3). Singletons in Tabela 4.6a footnote.
3. Whether §4.2.1 needs a figure — no; defer to Appendix A.
4. **aoe2companion rating 26.20% mechanism — RESOLVED per B2.** `01_04_01_data_cleaning.json:2197` says MAR; rate in 5-40% band; standard MAR-FLAG routing (NOT exception). `[REVIEW]` flag retained since primary-feature MAR at 26% is high-stakes.
5. Scope creep around §2.5 MMR mechanics — every MMR appearance gets forward-ref to §2.5 or §4.3.1.
6. Whether §4.1 MMR repair in T05 is scope-acceptable — **v2 commits yes**: inconsistency is drafting defect; leaving uncorrected is visible on examination.

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

### New bib entries to add (2, down from 5 in v1)

| Key | Citation | Where | State |
|---|---|---|---|
| `FellegiSunter1969` | Fellegi & Sunter 1969, JASA 64(328), 1183-1210, DOI:10.1080/01621459.1969.10501049 | §4.2.2 framing | **VERIFIED** canonical |
| `Christen2012DataMatching` | Christen 2012, Springer, ISBN 978-3-642-31163-5 | §4.2.2 reframed as **standard introductory textbook** per W1 | **VERIFIED** |

### Deferred / removed per v2

| Key | v1 disposition | v2 disposition | Rationale |
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
   - aoe2companion: analogous 10 artifacts under `src/rts_predict/games/aoe2/datasets/aoe2companion/` (**CRITICAL: `01_04_01_data_cleaning.json` lines 2180-2220 for rating classification; lines 1030-1050 for threshold provenance**).
   - `data/db/schemas/views/*.yaml` per dataset.
3. For each number, populate row: `claim_text | artifact_path | anchor | prose_form (PL) | artifact_form (raw) | normalized_value | datatype | hedging_needed`.
4. Classification-of-new-citations header table: **2** candidates (not 5): `FellegiSunter1969`, `Christen2012DataMatching`.
5. "Scope-overlap with §4.1" table (≥15 rows expected).
6. **NEW (D6a): "Tabela 4.6 ↔ §4.1 CONSORT flows identity check" table.** Candidate list: −24 meczów R01 SC2; −157 meczów R03 SC2; −997 meczów R08 aoestats; −5 052 meczów R03 aoe2companion; −6 wierszy R02 aoe2companion; −1 185 wierszy aoestats ingestion filter; −118 wierszy DS-AOESTATS-03; 1 132 DS-SC2-10; 2 DS-SC2-09; 273 DS-SC2-06. Grep-match each against §4.1 prose + Tabela 4.1/4.2/4.3. Any mismatch → HALT.
7. **NEW (D6c): Anchor aoe2companion `read_csv_auto` claim** against `01_02_02_duckdb_ingestion.md`. If "all 7 VARCHAR" phrasing isn't in artifact, row records actual artifact phrasing and T02 softens.
8. **NEW (B2): Three threshold-provenance rows:**
   - `threshold-5pct`: `01_04_01_data_cleaning.json:1042` → Schafer & Graham 2002.
   - `threshold-30-40pct`: van Buuren 2018 prose verified against book.
   - `threshold-80pct`: `01_04_01_data_cleaning.json:1042` "Operational starting heuristics from `temp/null_handling_recommendations.md §1.2`"; file verified absent.
9. **NEW (B1): Two MMR mechanism rows:**
   - `mmr-mechanism-sc2-flat`: `01_04_01_missingness_ledger.csv:35` `mechanism=MAR`, MAR-primary w/ MNAR-sensitivity branch.
   - `mmr-mechanism-sc2-history`: `01_04_01_missingness_ledger.csv:85` same classification for `player_history_all`.
10. **Halt predicate:** >5 numbers unanchored within 5 lookups each, OR identity-check mismatch.

**Verification:**
- File exists; 90-130 rows (v1 was 80-120; +10 B1/B2 rows).
- Scope-overlap table ≥15 rows.
- Identity-check table all resolved or halt-flagged.
- Classification table has 2 new bib entries.
- Three threshold-provenance rows anchored.
- Two MMR-mechanism rows anchored.

**File scope:** writes `thesis/pass2_evidence/sec_4_2_crosswalk.md`.

**Read scope:** 30 artifact .md files; 3 missingness CSVs; aoe2companion `01_04_01_data_cleaning.json`; `sec_4_1_crosswalk.md`; `04_data_and_methodology.md` §4.1.

**Char budget:** 7-11k Markdown (v1 was 6-10k; +1k for B1/B2/D6a/D6c rows).

**Risk:** Low-medium. Mechanical + new identity-check logic.

---

### T02 — Draft §4.2.1 Ingestion i walidacja (Polish)

**Objective:** Draft §4.2.1 arguing two-path ingestion. **Target 6.0-7.5k Polish chars** (v2 widened from 5-7k per B3).

**Must justify:**
1. **DuckDB over Postgres/BigQuery.** Alternative = columnar DW. Decision = embedded DuckDB w/ `tmp/` spill. Reason: I6 reproducibility via single-process per notebook, free at ~300M rows, native Parquet/JSON, WAL-free CTAS. **(v2 per W2): no Wilson 2017 cite. Forward-ref to Appendix A.**
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
- §4.2.1 exists; **6,000 ≤ len ≤ 7,500 chars** (v2).
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

**Objective:** Draft §4.2.2 arguing per-dataset canonical-identifier decisions against record-linkage literature, forward-ref to thesis-level canonical-nickname rule (**I2** per D6b correction, not I9). **Target 6.5-8.0k Polish chars** (v2 widened).

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

**Invariant checks (v2 corrected per D6b):**
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
- §4.2.2 exists; **6,500 ≤ len ≤ 8,000 chars** (v2).
- Tabela 4.5 present.
- 5 citations resolved.
- Forward-ref grounded in **I2**, not I9.
- No Phase 02 computation.
- **Christen 2012 framed per W1.**

**File scope:** `04_data_and_methodology.md` §4.2.2 + Tabela 4.5; `references.bib` +2 entries.

**Read scope:** crosswalk; 01_02_04 census + 01_03_01 profile JSON per dataset; 01_01_02 schema for SC2; §4.1 voice; `references.bib`; `.claude/scientific-invariants.md:24-29`.

**Char budget:** 6,500-8,000.

**Risk:** Medium-high. Over-claiming multi-account, new bib Pass 2 verification, Phase 02 creep. Mitigations: hedged language, `[REVIEW]` flags, explicit I2 forward-ref.

---

### T04 — Draft §4.2.3 Reguły czyszczenia i ważny korpus (Polish)

**Objective:** Draft §4.2.3 cross-dataset cleaning-rule typology, MissingIndicator I3-compliance defence, per-dataset invocations. **Target 10.0-13.0k Polish chars** (v2 widened from 8-10k per B3; richest subsection).

**Must justify:**
1. **Rule-based registry vs. ad-hoc fixes.** Decision = formal registry w/ R/DS IDs. Reason: reviewability, I6, I8 (unified typology).
2. **Classify by Rubin1976 taxonomy BEFORE routing (v2 reframed per B2).** Decision = mechanism first, then rate-band routing under **operational-heuristic thresholds**. Thresholds provenance (v2 explicit):
   - **<5% MCAR → RETAIN_AS_IS.** Provenance: Schafer & Graham 2002 (literature-backed, unambiguous).
   - **5–40% MAR → FLAG_FOR_IMPUTATION.** Provenance: van Buuren 2018 prose "can be trusted when proportion missing < about 30-40%" (general guidance, not rigid cutoff).
   - **≥80% MAR/MNAR → DROP_COLUMN + MissingIndicator flag.** Provenance: **operational heuristic of this pipeline**, traceable internally to now-deleted `temp/null_handling_recommendations.md §1.2` (`01_04_01_data_cleaning.json:1042`). NOT a peer-reviewed constant; operationalizes van Buuren's general guidance conservatively. §4.2.3 prose paragraph: "Próg 80% sentynelu jest heurystyką operacyjną niniejszego pipeline'u, konsekwentnie stosowaną we wszystkich trzech korpusach. Nie jest to konstanta cytowana wprost z [vanBuuren2018], lecz konserwatywne zaostrzenie ogólnej rekomendacji van Buurena, że powyżej 30–40% imputacja traci gwarancje." Cite `.claude/scientific-invariants.md:86-96` I7 — compliance via documentation-inline.
3. **MissingIndicator I3-compliant.** Alternatives: impute at cleaning / drop rows. Decision = NULLIF + binary flag (`is_mmr_missing`, `p0_is_unrated`, `rating_was_null`). Reason: (a) I3 forbids computing features from time-T-or-later info; cleaning-time imputation leaks future statistics; (b) missingness carries signal (MMR=0 = "unrated professional" subgroup); (c) Phase 02 fold-aware imputation preserves I3. Cite `Rubin1976`, `vanBuuren2018`, `.claude/scientific-invariants.md:40-49` I3 normalization-leakage clause.
4. **SC2 MMR=0 classification MAR-primary / MNAR-sensitivity (v2 per B1).** Ledger: `01_04_01_missingness_ledger.csv:35` says MAR with "MAR-primary: missingness depends on observed replay source (tournament replays lack ladder MMR). MNAR (private pro accounts) documented as sensitivity branch." Interpretation: "tournament replay" is observable attribute (replay source/context), so MAR per strict Rubin taxonomy. MNAR retained as sensitivity branch for partially-unobservable player-type signal. §4.2.3 commits to MAR-primary, acknowledges MNAR branch, hedges. Flag `[REVIEW: MAR-primary vs MNAR-sensitivity — primary feature]`. **Key: routing (DROP_COLUMN + MissingIndicator) identical under both — both MAR and MNAR at ≥80% route to DROP. Key v2 fix: §4.1.1.4 line 41 + Tabela 4.4b line 195 say MNAR; T05 repairs both.**
5. **Per-dataset rule counts differ.** Decision = per-dataset tailoring on dataset-specific sentinels. Reason: typology unified (mechanism × rate × action); invocations differ. I8 at methodology layer.
6. **aoe2companion `rating` 26.20% → FLAG_FOR_IMPUTATION (v2 reframed per B2).** Ledger: `01_04_01_data_cleaning.json:2197` says `mechanism=MAR`. Rate 26.20% in **5-40% MAR band** (NOT 40-80%). Routing per standard rule S3: FLAG_FOR_IMPUTATION + `rating_was_null` indicator. This is **standard MAR-FLAG routing**, NOT an exception. v1's "primary-feature exception" framing was based on misread and is removed. Cite `01_04_01_data_cleaning.json:2200` verbatim: "Rate 26.20% in 5-40%; flag for Phase 02 imputation." No appeal to non-existent van Buuren exception.

**Must contrast:**
- MissingIndicator vs. MICE (van Buuren 2018). MICE requires fit-on-training-only → I3. Phase 01 `*_clean` VIEWs are fold-agnostic; imputation defers to Phase 02. MissingIndicator losslessly preserves signal.
- Three-threshold system vs. single 30% drop threshold. Three-threshold is mechanism-defensible: 5% Schafer & Graham, 30-40% van Buuren prose, **80% pipeline operational heuristic documented inline per I7**. Single threshold ignores mechanism.

**Must cite:** `Rubin1976`, `vanBuuren2018`, `SchaferGraham2002`. `.claude/scientific-invariants.md` I3/I7 clauses.

**Tables:**
- **Tabela 4.6 (v2 restructured per W3)** — 8-row cross-dataset typology; every row has ≥2-dataset invocations:
  1. Scope-filter (zakresowy filtr korpusu) — SC2 R01 / aoestats R02 / aoe2companion R01
  2. Target-consistency filter — SC2 R01-część / aoestats R08 / aoe2companion R03
  3. Sentinel → NULLIF (<5% MCAR low-rate) — SC2 DS-SC2-09/10 / aoestats DS-AOESTATS-02/03 / — aoe2companion singleton (none)
  4. DROP_COLUMN ≥80% (operational heuristic) — SC2 DS-SC2-01/02/03 / aoestats DS-AOESTATS constants / aoe2companion DS-AOEC-01
  5. FLAG_FOR_IMPUTATION 5-40% MAR — (SC2 nd) / (aoestats nd) / aoe2companion DS-AOEC-02/04/05 (**rating 26.20% standard-band routing, NOT exception per B2**)
  6. MissingIndicator-plus-NULLIF — SC2 DS-SC2-01/10 / aoestats DS-AOESTATS-02 / aoe2companion DS-AOEC-04
  7. Schema-evolution exclusion — SC2 DS-SC2-06 / aoestats opening/age_uptime / aoe2companion R04
  8. Constants/duplicates drop — SC2 DS-SC2-08 / aoestats DS-AOESTATS-04/08 / (aoe2companion inlined)

  Rows with one `(nd)` are retained (still ≥2-dataset); rows with two `(nd)` move to Tabela 4.6a.

- **Tabela 4.6a (NEW per W3)** — compact per-dataset singleton footnote (3 rows, one per dataset):
  - SC2EGSet: R03 MMR<0 replay-level exclusion (−157); implicit POST_GAME I3 (`elapsedGameLoops` in `player_history_all` only).
  - aoestats: ingestion-level `profile_id`/`started_timestamp IS NOT NULL` (−1 185 wierszy AI-przeciwnicy); R06 (`new_rating` excluded both VIEWs — POST_GAME I3).
  - aoe2companion: R02 dedup matchId×profileId (−6 wierszy); implicit `ratingDiff` POST_GAME I3.

**Citations needed:** 3 primary + intra-doc invariants.

**Cross-refs:** Back §4.1.1.4, §4.1.2.1, §4.1.2.2, §2.5.4. Forward §4.3.1, §4.4.2, §6.5, §2.5.

**Crosswalk entries:** 35-50 rows (per-dataset impacts, rates, column flows, assertions) + 3 threshold-provenance + 2 MMR-mechanism.

**Invariant checks:**
- **I3 (primary defence):** Phase 01 fold-agnostic → any Phase 01 imputation leaks future-fold info → Phase 02 fold-aware imputation preserves I3 → MissingIndicator losslessly preserves signal. Cite `:40-49`.
- **I5:** slot symmetry preserved (asymmetries documented, not corrected).
- **I6:** SQL verbatim in `01_04_01_data_cleaning.json`.
- **I7 (v2 explicit per B2):** every threshold carries provenance inline. 5% → Schafer & Graham 2002 (literature). 30-40% → van Buuren 2018 prose (general guidance). **80% → operational heuristic of this pipeline, documented inline per I7's "document its derivation inline" requirement** — traceable to deleted internal doc. §4.2.3 states explicitly: 80% is operational, not peer-reviewed.
- **I8:** typology unified (Tabela 4.6 ≥2-dataset); singletons explicit (Tabela 4.6a). Methodology identical across datasets.
- **I9:** rules operate on VIEWs; raw tables never modified. Cite `:163-197`.

**Out-of-scope:** Phase 02 imputation detail; §4.1 CONSORT re-narration (identity check confirms no drift); column-count detail; §2.5 mechanics; 01_05 findings.

**Voice:** argumentative; every rule-class: mechanism + rate + action + alternative + rejection + cite. MissingIndicator defence forward-leaning.

**Instructions:**
1. Opening (~1,100 chars): typology-before-invocation; cite three taxonomy references; pre-announce MissingIndicator I3 defence; pre-announce MMR MAR-primary/MNAR-sensitivity commitment.
2. Paragraph per rule class (~600-900 chars each, 7-8 classes from Tabela 4.6).
3. **I7 threshold-provenance paragraph (~800 chars):** state 5% literature-backed, 30-40% prose-guidance, 80% operational-heuristic inline-documented. I7 compliance footer.
4. **MMR MAR-primary / MNAR-sensitivity paragraph (~600 chars):** commit to ledger, acknowledge MNAR branch, routing-invariant at ≥80%, `[REVIEW]` flag.
5. Closing defence (~1,000 chars): MissingIndicator I3-compliance + mechanism-first routing + I7 provenance + I3 fold-aware Phase 02 all cohere.
6. Tabela 4.6 between opening and per-rule paragraphs.
7. Tabela 4.6a as compact footnote after Tabela 4.6.
8. `[REVIEW]` flags: (a) MAR-primary vs MNAR-sensitivity for MMR; (b) 80% operational-heuristic framing acceptability; (c) I8 unified-typology post-restructure; (d) §4.1 repair prose integrity; (e) rating 26.20% standard-band framing Pass 2.

**Verification:**
- §4.2.3 exists; **10,000 ≤ len ≤ 13,000** (v2).
- Tabela 4.6 present; every non-`(nd)` row ≥2-dataset.
- Tabela 4.6a present as footnote.
- 3 primary citations resolved.
- ≥5 "alternatywą byłoby / decyzja wynika z" patterns.
- ≥2 MissingIndicator defence sentences citing I3.
- I7 threshold-provenance paragraph present; all three thresholds have provenance statements.
- MMR paragraph commits MAR-primary, acknowledges MNAR, states routing invariance.
- ≥3 `[REVIEW]` flags.

**File scope:** `04_data_and_methodology.md` §4.2.3 + Tabela 4.6 + Tabela 4.6a.

**Read scope:** crosswalk; all three 01_04_01 `data_cleaning.md`; all three `missingness_ledger.csv` (SC2 row 35 CRITICAL); aoe2companion `01_04_01_data_cleaning.json` lines 1030-1050 + 2180-2220; all three 01_04_02; 01_04_00 source-normalization; §4.1 lines 41-43, 89-94, 124-132, 195; `.claude/scientific-invariants.md` I3:40-49, I7:86-96, I9:163-197.

**Char budget:** 10,000-13,000.

**Risk:** **High.** Mitigations per v2: typology framing + scope-overlap check; explicit closing defence; MAR-primary/MNAR-sensitivity commitment + T05 §4.1 repair; I7 threshold-provenance paragraph; Tabela 4.6 restructure + 4.6a footnote; T01 identity-check halt.

---

### T05 — Integrate cross-refs, REPAIR §4.1 MMR classification, update tracking

**Objective:** Cross-reference integration + **§4.1 MMR MAR/MNAR inconsistency repair (v2 new per B1)** + tracking-files updates.

**Sub-step 0 (NEW per B1) — §4.1 MMR classification repair.** Runs BEFORE cross-reference validation.
- **Line 41 rewrite:** "Mechanizm tej missingness jest klasyfikowany jako MNAR … nie losowo." → "Mechanizm tej missingness jest klasyfikowany w ledgerze missingness (`01_04_01_missingness_ledger.csv`) jako **MAR-primary z gałęzią sensitywną MNAR** wg taksonomii [Rubin1976] — missingness zależy od obserwowalnego atrybutu (źródło powtórki turniejowe, w którym brak przypisania ladderowego), z równoległą gałęzią MNAR dla graczy z prywatnymi kontami zawodowymi (niedostępność MMR zależna od typu konta, wartość częściowo nieobserwowalna). §4.2.3 rozwija uzasadnienie klasyfikacji i operacjonalizuje routing DROP_COLUMN + MissingIndicator, identyczny dla obu interpretacji na tym poziomie sentynelu (≥80%)."
- **Line 195 rewrite:** Tabela 4.4b SC2 "Mechanizm dominującej missingness" cell: "MNAR (MMR=0 unrated prof.)" → "MAR-primary / MNAR-sensitivity (MMR=0 unrated prof.; per ledger)".
- Diff scope ~400 chars; net ~+250 chars to §4.1.
- Verification: grep `MNAR` post-repair — expected zero standalone "MNAR (MMR=0 …" references outside §4.2.3's MAR-primary/MNAR-sensitivity framing.
- REVIEW_QUEUE §4.1.1 row updated: append "v2 §4.2 drafting surfaced MMR MAR/MNAR inconsistency; §4.1.1.4 line 41 + Tabela 4.4b line 195 repaired per ledger."

**Sub-step 1 — cross-reference validation.** Scan §4.2.1/§4.2.2/§4.2.3 references; resolve to §4.1 (post-repair), §2.5/§2.2, BLOCKED §4.3/§4.4 (flag).

**Sub-step 2 — WRITING_STATUS.md update.** Append three new §4.2.x DRAFTED rows w/ char counts. Update §4.1.1 row per sub-step 0.

**Sub-step 3 — REVIEW_QUEUE.md update.** Append three new §4.2.x Pending rows; update §4.1.1 row.

**Sub-step 4 — CROSS research_log entry.** `/Users/tomaszpionka/Projects/rts-outcome-prediction/reports/research_log.md` — heading `[CROSS] 2026-04-18 — §4.2 Data preprocessing draft + §4.1 MMR classification repair`; narrate 3 subsections, §4.1 repair, new bib entries (FellegiSunter1969 + Christen2012DataMatching; Wilson2017 deferred to Appendix A per W2), Tabela 4.6 restructure.

**Sub-step 5 — Halt log.** Append to new `thesis/pass2_evidence/sec_4_2_halt_log.md`.

**Verification:**
- §4.1 line 41 + Tabela 4.4b line 195 updated to MAR-primary/MNAR-sensitivity.
- WRITING_STATUS has 3 new §4.2.x + §4.1.1 repair note.
- REVIEW_QUEUE has 3 new + §4.1.1 update.
- CROSS research_log entry present.
- halt log exists.
- All `[REVIEW]` → corresponding REVIEW_QUEUE row.

**File scope:** `04_data_and_methodology.md` (§4.1 repair + §4.2 cross-ref fixes); `WRITING_STATUS.md`; `REVIEW_QUEUE.md`; `research_log.md`; `sec_4_2_halt_log.md` (new); `pass2_evidence/README.md`.

**Read scope:** §4.2 drafts; tracking files; `01_04_01_missingness_ledger.csv` row 35 verbatim for repair anchor.

**Char budget:** metadata + ~250 chars §4.1 repair.

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
7. **NEW v2:** verify §4.1 repair integrates smoothly w/ surrounding §4.1.1.4 prose.

**Verification:** no -ować calques; no doubled words; italicized/glossed/retained anglicisms; no >3-element dopełniacz chain; Polish typography; §4.1 repair seamless.

**File scope:** `04_data_and_methodology.md` polish within §4.2 + §4.1.1.4 repair.

**Risk:** Low.

---

## File Manifest

| File | Task | Role |
|---|---|---|
| `thesis/pass2_evidence/sec_4_2_crosswalk.md` | T01 writes | Crosswalk + Tabela 4.6 ↔ §4.1 identity check + MMR/threshold-provenance rows |
| `thesis/chapters/04_data_and_methodology.md` | T02/T03/T04/T05/T06 | §4.2.1/§4.2.2/§4.2.3 + §4.1.1.4 line 41 repair + Tabela 4.4b line 195 cell repair |
| `thesis/references.bib` | T03 | +2 entries: FellegiSunter1969, Christen2012DataMatching. **Wilson2017 DEFERRED to Appendix A per v2 W2.** |
| `thesis/WRITING_STATUS.md` | T05 | +3 DRAFTED rows; §4.1.1 row updated |
| `thesis/chapters/REVIEW_QUEUE.md` | T05 | +3 Pending rows; §4.1.1 row updated |
| `reports/research_log.md` | T05 | CROSS 2026-04-18 entry |
| `thesis/pass2_evidence/sec_4_2_halt_log.md` | T05 writes (new) | Halt log |
| `thesis/pass2_evidence/README.md` | T05 | Index table +2 rows |

---

## Gate Condition

§4.2 is DRAFTED when all hold:

1. §4.2.1/2/3 populated in `04_data_and_methodology.md`, HTML-comment skeletons replaced.
2. Combined §4.2 Polish char count ∈ **[22,500 − 28,500]** (v2).
3. `sec_4_2_crosswalk.md` exists w/ all numerical claims anchored; "Tabela 4.6 ↔ §4.1 CONSORT" identity-check table zero-mismatch; threshold-provenance + MMR-mechanism rows populated; `sec_4_2_halt_log.md` exists.
4. WRITING_STATUS lists §4.2.1/2/3 DRAFTED; §4.1.1 row reflects MMR repair.
5. REVIEW_QUEUE has 3 new Pending + §4.1.1 update.
6. `references.bib` has 2 new entries (FellegiSunter1969, Christen2012DataMatching); **no Wilson2017** in v2.
7. Tabela 4.5 and Tabela 4.6 w/ Polish captions; Tabela 4.6 ≥2-dataset per row; Tabela 4.6a singleton footnote present.
8. Every threshold has provenance: 5% → `SchaferGraham2002` cite; 30-40% → `vanBuuren2018` prose cite; **80% → explicitly operational heuristic of this pipeline, documented inline per I7**. No "van Buuren 80% codified" claim.
9. MissingIndicator has explicit I3-compliance defence paragraph.
10. **§4.1 MMR repair completed:** line 41 + Tabela 4.4b line 195 aligned to MAR-primary/MNAR-sensitivity per ledger row 35.
11. **aoe2companion rating 26.20% framed as standard MAR-FLAG at 5-40% band**, NOT "primary-feature exception".
12. **§4.2.2 cites I2 for Phase 02 deferral**, not I9 (except for raw-table immutability narrow use).
13. CROSS 2026-04-18 entry in research_log.
14. No `[UNVERIFIED]` flags; `[REVIEW]` allowed.
15. Critical-review checklist (data variant) passes.

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

---

## Open questions

1. **Scope overlap with §4.1.** Accept typology framing? Recommended: yes.
2. **§4.1 MMR repair scope.** v2 commits to repairing line 41 + Tabela 4.4b line 195 per B1. Approve? Recommended: yes.
3. **80% operational-heuristic framing.** v2 explicit "pipeline heuristic, not peer-reviewed cutoff". Comfort with candour? Alternative: soften to "konserwatywne rozszerzenie rekomendacji van Buurena" without "heurystyka operacyjna" language. Recommended: explicit — more defensible under adversarial review.
4. **2 new bib entries** (down from 3 v1). Optional: LittleRubin2019, Pedregosa2011Sklearn. Recommended: 2.
5. **CONSORT/STROBE/RECORD.** Tabela 4.6 typology not a flow table — footnote flagging inapplicability? Recommended: yes.
6. **Halt protocol.** §4.1 had 3+3; §4.2 expected 2+2 w/ cap 3+3. R1→v2 substantive revisions; R2 target READY_FOR_EXECUTION.
7. **Repair narration in research_log.** Explicit narrative of §4.2-discovering-§4.1-inconsistency, or quiet correction? Recommended: explicit — documents pass-1-to-pass-2 feedback loop.

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

**BLOCKER 2 — Thresholds are magic numbers (I7 violation).** Pre-emption (v2 per B2): explicit I7 threshold-provenance paragraph. 5% → Schafer & Graham 2002 literature. 30-40% → van Buuren 2018 prose general guidance (not codified). **80% → operational heuristic of this pipeline, documented inline per I7's "document derivation inline" requirement**, traceable to deleted internal doc. Compliance via documentation-inline, not pseudo-citation.

**BLOCKER 3 — MAR for MMR is wrong, should be MNAR.** Pre-emption (v2 per B1): **commit to MAR-primary / MNAR-sensitivity per ledger row 35.** MMR paragraph explicit: "MAR-primary pochodzi z ledgera — missingness zależy od obserwowalnego atrybutu. MNAR-sensitivity dla prywatnych kont zawodowych. [REVIEW]." **Routing identical at ≥80% under both.** Key v2 addition: **§4.1.1.4 line 41 + Tabela 4.4b line 195 REPAIRED in T05 — §4.2 and §4.1 agree.**

**BLOCKER 4 (NEW v2 per W3) — Tabela 4.6 sparsity undermines I8.** Pre-emption: **Tabela 4.6 restructured** ≥2-dataset invocations per row; singletons in Tabela 4.6a footnote. I8 claim rests on MCAR/MAR/MNAR × rate × action typology (genuinely unified, demonstrated post-restructure). Singletons admitted as dataset-specific (honest rather than fragile). Closing paragraph: "Typologia (Tabela 4.6) wspólna; singletonowe invokacje (Tabela 4.6a) nie podważają jedności metodologii — są invokacjami tego samego typu reguły na dataset-specific sentynelu."

---

## Halt protocol

Mirrors §4.1 halt protocol (see `sec_4_1_halt_log.md`):

- **Per-task:** number unanchored within 5 lookups → `[UNVERIFIED]` inline.
- **Aggregate:** >5 `[UNVERIFIED]` per subsection → halt + user handoff.
- **NEW v2 per D6a:** T01 identity-check mismatch → halt until resolved (Tabela 4.6 wording change / §4.1 correction / artifact re-extraction).
- **NEW v2 per B1:** T05 sub-step 0 §4.1 MMR repair alters §4.1.1.4 >500 net chars → halt (scope creep).
- Every halt appended to `sec_4_2_halt_log.md`; zero-halt drafts attest zero events explicitly.

---

## Execution ordering and risk summary

| Task | Char budget (v2) | Risk | Depends on |
|---|---|---|---|
| T01 Crosswalk + identity check | 7-11k MD | Low-medium (new identity-check) | — |
| T02 §4.2.1 | 6.0-7.5k PL | Medium | T01 |
| T03 §4.2.2 | 6.5-8.0k PL | Medium-High | T01 |
| T04 §4.2.3 | 10.0-13.0k PL | High | T01 |
| T05 Integration + §4.1 repair | ~250 chars §4.1 + metadata | Low-medium (§4.1 scope) | T02/T03/T04 |
| T06 Polish | — (edits) | Low | T05 |

**Total §4.2: 22.5-28.5k Polish chars** (v2; v1 was 18-22k). Plus ~250 chars §4.1 repair.

---

## Critical self-check

- [x] category F
- [x] Sequential T01-T06
- [x] File Manifest captures §4.1 repair
- [x] No forbidden taxonomy terms
- [x] `invariants_touched`: [I2, I3, I5, I6, I7, I8, I9, I10] (v2: I2 added per D6b)
- [x] Change log at top of plan
- [x] Every BLOCKER has verdict + fix + pointer
- [x] Every WARNING has verdict + fix + pointer
- [x] B1/B2 artifact-claim verifications executed (ledger row 35; JSON line 2200; JSON line 1042)
- [x] B3 budget evidence referenced (§4.1.1=18.5k, §4.1.2=22.5k, §4.1.3=5.7k)
- [x] Tabela 4.6 restructured per W3
- [x] Wilson 2017 deferred per W2 (not removed; moved to Appendix A)
- [x] I9→I2 correction per D6b
- [x] D6a identity-check added to T01
- [x] D6c conditional wording planned for T02
- [x] Category F → reviewer-adversarial R2 required before execution

---

## Critique instruction (Category F — mandatory)

**Dispatch reviewer-adversarial to produce `temp/critique_4_2_r2.md` before any T01-T06 runs.** Symmetric 3-round cap: plan-side R1 done, R2 required after v2, R3 only if substantive BLOCKER persists. Target verdict: `READY_FOR_EXECUTION` after R2. If R2 still yields substantive BLOCKER, escalate to user for R3 decision.

---

## Paths referenced (absolute)

- Plan file: `/Users/tomaszpionka/.claude/plans/nested-meandering-octopus-agent-ac6eee700b00b5511.md`
- v1 plan: `/Users/tomaszpionka/Projects/rts-outcome-prediction/temp/plan_4_2_v1.md`
- R1 critique: `/Users/tomaszpionka/Projects/rts-outcome-prediction/temp/critique_4_2_r1.md`
- Thesis chapter: `/Users/tomaszpionka/Projects/rts-outcome-prediction/thesis/chapters/04_data_and_methodology.md` (lines 41, 195 targeted for repair in T05)
- Scientific invariants: `/Users/tomaszpionka/Projects/rts-outcome-prediction/.claude/scientific-invariants.md` (I2:24-29; I3:40-49; I7:86-96; I9:163-197; I10:131-159)
- SC2 ledger row 35 (B1 anchor): `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv`
- aoe2companion rating artifact (B2 anchor): `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json` lines 1030-1050 (threshold provenance) + 2180-2220 (rating row)
- Writing status: `/Users/tomaszpionka/Projects/rts-outcome-prediction/thesis/WRITING_STATUS.md`
- Review queue: `/Users/tomaszpionka/Projects/rts-outcome-prediction/thesis/chapters/REVIEW_QUEUE.md`