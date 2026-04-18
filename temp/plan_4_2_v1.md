# Plan: Category F — §4.2 Data preprocessing (Polish)

## Executive summary

This plan drafts Polish-language thesis section §4.2 Data preprocessing (three subsections: §4.2.1 Ingestion & validation, §4.2.2 Player identity resolution, §4.2.3 Cleaning rules & valid corpus) in `thesis/chapters/04_data_and_methodology.md`, feeding from Phase 01 artifacts for all three datasets (sc2egset, aoestats, aoe2companion). Target length 18–22k Polish characters combined. The core methodological risk is **scope bleed from the already-drafted §4.1**: §4.1 already narrates CONSORT flows, missingness ledgers, and the existence of the `*_clean` / `player_history_all` VIEWs as corpus characteristics. §4.2 must therefore reframe the same artifacts as **preprocessing decisions** — *how and why* raw bytes become the analytic corpus, with alternatives-considered and I3/I5/I9 discipline — rather than re-describing the *what*. The plan pre-commits T01 to building a `sec_4_2_crosswalk.md` evidence file (following the `sec_4_1_crosswalk.md` precedent) and T02–T04 to drafting the three subsections with per-subsection 5–8k-char budgets, then T05 integrates cross-refs and T06 polishes. Three adversarial-defence axes are anticipated per subsection, learning from the §4.1 BLOCKER history (Sprint 7 scope-creep to corpus stats; the §2.2 BLOCKER on Korpus SC2EGSet subsection). The plan also flags that one user-prompt assumption is partially misaligned with the existing chapter state and proposes a scope-narrowing that avoids duplication with §4.1.1.3/§4.1.2.1/§4.1.2.2 "Schemat analityczny" paragraphs already on the page.

---

## Front matter

```yaml
category: F
branch: docs/thesis-4.2-session
plan_id: thesis-4.2-data-preprocessing
target_sections:
  - §4.2.1 Ingestion i walidacja (Ingestion & validation)
  - §4.2.2 Rozpoznanie tożsamości gracza (Player identity resolution)
  - §4.2.3 Reguły czyszczenia i ważny korpus (Cleaning rules & valid corpus)
target_file: thesis/chapters/04_data_and_methodology.md
target_lines: 205-229 (existing skeleton, to be replaced)
feeding_phases:
  - sc2egset Phase 01 Steps 01_01, 01_02, 01_03, 01_04 (complete)
  - aoestats Phase 01 Steps 01_01, 01_02, 01_03, 01_04 (complete)
  - aoe2companion Phase 01 Steps 01_01, 01_02, 01_03, 01_04 (complete)
source_artifacts: 30 files (~10 per dataset × 3) + missingness ledgers (CSV) + YAML view schemas
invariants_touched: [I3, I5, I6, I7, I8, I9, I10]
target_length_polish_chars: 18000-22000 (combined §4.2.1+§4.2.2+§4.2.3)
voice: argumentacyjna, bezosobowa polska proza akademicka; hedging idiomatyczny ("Na podstawie...", "Zaobserwowano...", "Decyzja o... wynika z..."); anglicyzmy techniczne kursywą przy pierwszym wystąpieniu
adversarial_required: yes — reviewer-adversarial before execution
```

---

## Problem statement

Section §4.2 must narrate the transformation from raw distributed files (SC2Replay JSON tournament archives; aoestats weekly Parquet dumps; aoe2companion daily Parquet+CSV snapshots) to the three canonical view families (`matches_long_raw`, `matches_flat_clean` / `matches_1v1_clean`, `player_history_all`) that downstream Phase 02+ consumes. §4.1 has already described **what** the cleaned corpora look like; §4.2 must describe **how** they were produced, **which alternatives** were considered, and **how invariants I3/I5/I6/I9/I10 are upheld by the preprocessing design**. Three specific contributions distinguish §4.2 from §4.1:

1. **Two-path pipeline design for heterogeneous sources** — SC2 (nested JSON→DuckDB CTAS) vs. aoestats (variant-Parquet union_by_name) vs. aoe2companion (daily Parquet+CSV + ratings snapshot). §4.1 mentions corpus sizes; §4.2 justifies why each source needs its own ingestion pattern and shows how I10 (relative `filename`) is enforced identically across all three despite the different source formats.
2. **Identity resolution across three fundamentally different schemes** — SC2 `toon_id` (server-scoped Battle.net ID, cardinality 2,495) vs. aoestats `profile_id` (globally unique BIGINT aoe2.net, cardinality 641,662, max 24,853,897) vs. aoe2companion `profileId` (INTEGER, cardinality 3,387,273, with `name`-nickname cardinality 2,468,478 implying rename/alias pressure). §4.1 mentions the identifier columns; §4.2 classifies the three identity schemes, defends a per-dataset canonical-identifier decision, and forward-references §4.3.1 for the thesis-level nickname-as-canonical-player rule (I2).
3. **Cleaning-rule derivation from missingness taxonomy** — §4.2.3 must defend the MCAR/MAR/MNAR classification per column (Rubin 1976 / Schafer & Graham 2002 / van Buuren 2018 thresholds at 5% / 40% / 80%), the DROP_COLUMN vs. NULLIF+flag vs. FLAG_FOR_IMPUTATION routing (decisions DS-SC2-01…10 / DS-AOESTATS-01…08 / DS-AOEC-01…08), and crucially the **MissingIndicator defer** — that Phase 01 produces the indicator flags losslessly but does **not** impute values (imputation is fold-aware Phase 02 work per I3's normalization-leakage clause). This is the most likely adversarial-challenge surface (reviewers often read deferral as failure to act).

Out-of-scope conventions: no re-narration of corpus descriptive statistics (that is §4.1), no feature engineering (§4.3), no split design or baselines (§4.4), no MMR/Elo mechanism (§2.5).

---

## Assumptions & unknowns

### Assumptions (validated during investigation)

1. **§4.2.1–§4.2.3 are all three DRAFTABLE after Phase 01 01_01–01_04 complete for all three datasets.** Verified — 30 artifacts exist on disk (10 per dataset × 3), covering 01_01_01 file_inventory + 01_01_02 schema_discovery + 01_02_01…07 EDA + 01_03_01…04 profiling + 01_04_00…02 cleaning. Phase 01 Steps 01_05 (Temporal & Panel EDA) and 01_06 (Decision Gates) are deferred across all three datasets; any §4.2.3 claim needing a duration-distribution threshold (e.g., short-game exclusion) must be flagged `[REVIEW: awaiting 01_05]` and the rule itself listed as "not yet operationalized" in the cleaning registry rather than invented. This follows the precedent from §4.1.1.4 (`header_elapsedGameLoops` is in `player_history_all`, but its empirical distribution profiling is deferred).

2. **The crosswalk pattern from §4.1 is the load-bearing evidence protocol.** `thesis/pass2_evidence/sec_4_1_crosswalk.md` already anchors 101 rows of prose-to-artifact mappings. The plan extends it with `sec_4_2_crosswalk.md` (parallel 8-column schema). A Category F draft without the crosswalk would fail adversarial review on halt-protocol grounds (see §4.1 halt log precedent).

3. **Polish voice is calibrated to the already-written §4.1, §2.1–§2.6, and §3.1–§3.3.** Not a literature-fed section — data-fed. The author-style-brief prescribes argumentacyjna (not opisowa) prose, bezosobowa register, hedging idiomatic constructs, anglicyzmy techniczne italicized on first use.

4. **§4.2 is section-final in the §4 chapter that is DRAFTABLE right now.** §4.3/§4.4 require Phase 02+ artifacts and remain BLOCKED. WRITING_STATUS.md currently shows §4.2.x as SKELETON (implicit — entries not in the status table yet); draft lifts them to DRAFTED with `[REVIEW]` flags.

### Unknowns (flag and work around; do NOT stall)

1. **Exact Polish translation conventions for English technical terms.** The existing §4.1 uses a mix: "widok" for VIEW, "sentynel" for sentinel, "missingness" left in English italic, "MissingIndicator" left in English with "wzorzec scikit-learn" qualifier. The plan adopts these §4.1 conventions verbatim for §4.2 to maintain intra-chapter consistency. No new translation decisions needed.

2. **Whether §4.2.3 should duplicate or merely reference the Cleaning Registry tables that already live in the 01_04_01 and 01_04_02 artifacts.** Decision: §4.2.3 presents **one** consolidated cross-dataset table ("Tabela 4.5 — Rejestr reguł czyszczenia, trzy korpusy") as a typology, NOT full ledgers per dataset. Per-dataset full registries are cited in-line to the artifact, not reproduced. Rationale: Tabela 4.5 is a synthesis exhibit; full ledgers are evidentiary artifacts (already on disk). This mirrors Tabela 4.4b's synthesis posture in §4.1.3.

3. **Whether the §4.2.1 narrative needs a figure.** Tentative answer: **no**. A pipeline diagram (raw → staging → DuckDB → view) risks adding a production-quality asset the pipeline does not yet render automatically. Defer any figure to Phase 01 Step 01_05 or to Appendix A (per THESIS_STRUCTURE.md §4.1-Appendix A mapping). Prose alone, with cross-references to Tabela 4.1/4.2/4.3 (already in §4.1), is sufficient.

4. **Whether aoe2companion's `rating_was_null` 26.20% MAR classification holds.** The 01_04_01 artifact classifies it MAR. §4.2.3 adopts that classification verbatim but adds a `[REVIEW: Pass 2 verification — rating missingness mechanism interpretation]` flag, since MAR-vs-MNAR for a primary feature is the highest-stakes taxonomy call in the entire preprocessing design and will be challenged by reviewer-adversarial.

5. **Whether scope creep will occur around §2.5 MMR mechanics during §4.2.3 drafting.** Confirmed risk (this was the Sprint 7 / §2.2 BLOCKER pattern). Pre-emptive rule: every appearance of "MMR" or "rating" in §4.2 prose is accompanied by a forward-ref to §2.5 (mechanism) or §4.3.1 (feature use). §4.2 itself says nothing about how MMR is computed or why it updates — only how its missingness is handled as a preprocessing decision.

---

## Literature context

§4.2 is a DATA-FED section, but — per the author-style brief — every methodological decision must be argued against its alternative, which requires citing the methodological literature that frames the alternatives. Citations split into three categories:

### Already in `references.bib` (reuse, no new entry)

| Key | Used in §4.1 | Role in §4.2 |
|---|---|---|
| `Rubin1976` | §4.1.1.4 (MMR MNAR), §4.1.2.1 (aoestats Elo MAR), §4.1.2.2 (aoe2companion MAR) | §4.2.3 — MCAR/MAR/MNAR taxonomy as the backbone of the cleaning registry; §4.2.3 Tabela 4.5 classifies each rule by mechanism |
| `vanBuuren2018` | §4.1.1.4 (DROP_COLUMN >80% defense), §4.1.2.2 (FLAG_FOR_IMPUTATION 26% exception) | §4.2.3 — the 80% / 40% / 5% thresholds and the primary-feature exception are direct citations; §4.2.3 uses them to defend the per-column DROP vs. FLAG routing |
| `SchaferGraham2002` | §4.1.1.4 (5% MCAR boundary) | §4.2.3 — the <5% MCAR-listwise-deletion threshold for low-rate sentinels (SC2 handicap=0 2 rows, APM=0 1,132 rows, aoestats avg_elo=0 118 rows) |
| `Bialecki2023` | §4.1.1.0 | §4.2.1 — cite as source of the `.SC2Replay` JSON format and ToonPlayerDescMap structure |
| `AoEStats` | §4.1.2.1 | §4.2.1 — cite as source of weekly Parquet pattern with variant schemas |
| `AoeCompanion` | §4.1.2.2 | §4.2.1 — cite as source of daily Parquet+CSV+snapshot pattern |
| `BlizzardS2Protocol` | §2.2.4, §4.1.1.4 | §4.2.1 — optional cite for the s2protocol decode step preceding our DuckDB ingestion |
| `MgzParser` | §2.3, §4.1.2.0 | §4.2.1 — cite only to say we do NOT parse `.aoe2record` files (out-of-scope per §2.3.4, §7.3); preprocessing uses API-agregated sources only |

### New bib entries to add (verify during execution, do not commit without Pass 2)

| Proposed key | Full citation | Where cited | Verification state (from WebSearch) |
|---|---|---|---|
| `FellegiSunter1969` | Fellegi, I.P. and Sunter, A.B. (1969). A Theory for Record Linkage. *Journal of the American Statistical Association*, 64(328), 1183–1210. DOI: 10.1080/01621459.1969.10501049 | §4.2.2 — foundational citation when framing "rozpoznanie tożsamości" as the record-linkage problem class; contrast our simple-identifier approach against the Fellegi-Sunter probabilistic framework | **VERIFIED** — canonical foundational paper; appears in virtually every record-linkage survey |
| `Christen2012DataMatching` | Christen, P. (2012). *Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution, and Duplicate Detection*. Springer (Data-Centric Systems and Applications series). ISBN: 978-3-642-31163-5 | §4.2.2 — canonical textbook reference for "entity resolution" as the task our `profile_id`/`toon_id`/`profileId` strategies approximate; cite when justifying the decision to NOT do probabilistic matching (rely on dataset-provided IDs + a future-work flag for nickname reconciliation) | **VERIFIED** — standard textbook; cited in §2.3 of every record-linkage survey paper since 2012 |
| `LittleRubin2019` | Little, R.J.A. and Rubin, D.B. (2019). *Statistical Analysis with Missing Data* (3rd ed.). Wiley (Wiley Series in Probability and Statistics). ISBN: 978-0-470-52679-8 | §4.2.3 — **optional** second reference for the MCAR/MAR/MNAR taxonomy when a third-edition citation is preferred over the 1976 paper; use ONLY if §4.2.3 needs a textbook-level citation alongside the journal paper. Risk: adds a bib entry whose coverage already is in `Rubin1976`+`vanBuuren2018`. Recommendation: defer unless specifically asked by Pass 2 | **VERIFIED** — third edition exists, Wiley Series |
| `Pedregosa2011Sklearn` | Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830. | §4.2.3 — cite for the `MissingIndicator` pattern used when justifying the "flag missingness, defer imputation" decision. Note: the 2011 paper does not describe `MissingIndicator` specifically (that feature was added later); citation is for the library itself. If §4.2.3 needs a more-specific citation, see `VanBuuren2018` (already in bib, which covers indicator-variable strategy directly) | **PARTIALLY VERIFIED** — paper exists, but `MissingIndicator` is not documented in the paper itself. Recommendation: cite `vanBuuren2018` for the indicator-variable strategy, and only add `Pedregosa2011Sklearn` if a library citation is specifically needed |
| `Wilson2017GoodEnough` | Wilson, G., Bryan, J., Cranston, K., Kitzes, J., Nederbragt, L., and Teal, T.K. (2017). Good Enough Practices in Scientific Computing. *PLOS Computational Biology*, 13(6), e1005510. DOI: 10.1371/journal.pcbi.1005510 | §4.2.1 — cite as a justification for I6 (reproducibility through SQL-stored-alongside-result) and for the raw/staging/db directory separation | **VERIFIED** — open-access PLOS paper, well-cited reproducibility guidance |

### Citation gaps and flags (shortlist for user if ambiguous)

- **CONSORT vs. STROBE vs. RECORD for our flow tables.** Our existing Tabela 4.1 / 4.2 / 4.3 in §4.1 are captioned "CONSORT-style". WebSearch confirms CONSORT is for **trials**, STROBE (2007) is for **observational studies**, and RECORD (2015) is for **routinely-collected observational data** — the closest fit for our corpus. Recommendation for §4.2.3: retain "CONSORT-style" framing for intra-thesis consistency with §4.1 but **flag to the user for Pass 2**: "should captions cite STROBE 2007 or RECORD 2015 rather than CONSORT? All three are guidance, not strict schemas; the existing §4.1 tables already use 'CONSORT-style' — changing one without changing all three would produce inconsistency." Do not commit a bib change unilaterally.
- **Parquet / Arrow validation reference.** WebSearch on "Parquet schema-on-read type coercion" returned only Apache Arrow documentation, no peer-reviewed paper suitable for thesis citation. Recommendation: §4.2.1 does **not** cite a specific ingestion-validation paper; instead, the narrative argues the type-unification decisions (aoestats `profile_id` DOUBLE→BIGINT CAST, `started_timestamp` [us]↔[ns] precision unification) as application of the principle "type-coerced ingestion with explicit dtype override when auto-inference yields incorrect type" — cite `Wilson2017GoodEnough` for the general reproducibility principle, no Parquet-specific reference needed.

---

## Execution Steps

The plan orders six tasks. T01 builds the evidence crosswalk (pre-requisite for all drafting). T02, T03, T04 draft the three subsections in descending dependency order (T04 first of the drafting tasks since §4.2.3 is the richest). T05 integrates cross-references and WRITING_STATUS.md / REVIEW_QUEUE.md updates. T06 is the final polish pass (lexical anglicisms, doubled-word scan, Polish typography).

### T01 — Build §4.2 numerical crosswalk

**Objective:** Produce `thesis/pass2_evidence/sec_4_2_crosswalk.md` following the 8-column schema from `sec_4_1_crosswalk.md`. Every number intended for §4.2.1/§4.2.2/§4.2.3 prose must have a row in this file before it can be written.

**Instructions:**
1. Read `sec_4_1_crosswalk.md` header/format precisely — reproduce the 8-column schema and the "Number-format normalization" rule (strip `,`, space, `\u00A0`; Polish decimal `,`→`.`).
2. Enumerate every candidate number for §4.2 from the following artifact paths (all absolute):
   - `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md` (top-level counts, tournament distribution, size)
   - `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.md` (11 root keys, 7,350 keypaths, ToonPlayerDescMap structure)
   - `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.md` (367.6 GB event-array estimate; split-table strategy)
   - `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.md` (22,390 replays_meta / 44,817 replay_players / 104,160 map_aliases rows; 0 orphans in cross-table integrity check)
   - `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_03_raw_schema_describe.md` (column counts per table/view)
   - `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md` (toon_id=2,495, nickname=1,106, uniqueness ratios — **identity fragmentation finding**)
   - `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md` (column-level profile with nulls, cardinality, constants)
   - `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.md` (players-per-replay distribution; 555 random-race replays; 22,379 clean 1v1 replays; 26 Undecided/Tie rows)
   - `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_00_source_normalization.md` (matches_long_raw 10-column schema; side symmetry audit)
   - `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md` (full R01–R07 registry, 22,209/44,418 final rows, DS-SC2-01…10 decisions, ledger rates)
   - `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv` (per-column taxonomy with mechanism/recommendation)
   - `/Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.md` (49→28 / 51→37 column-count flow; 18 assertions PASS)
   - Same 10 artifacts under `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/` — key numbers: 30,690,651 matches_raw; 107,627,584 players_raw; 641,662 distinct profile_id; max 24,853,897; 172/171 Parquet file asymmetry; R00–R08 registry; 17,814,947 final matches; 20/14 column counts; 33 assertions PASS
   - Same 10 artifacts under `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/` — key numbers: 277,099,059 matches_raw; 74,788,989 distinct matchIds; 3,387,273 distinct profileIds; 2,468,478 distinct name; 264,132,745 player_history_all; R00–R05 registry; 30,531,196 / 61,062,392 final rows; 48/19 column counts
   - `data/db/schemas/views/*.yaml` — view schemas for each dataset (column-count validation source)
3. For each number, populate a crosswalk row with: `claim_text | artifact_path | anchor | prose_form (Polish) | artifact_form (raw) | normalized_value | datatype | hedging_needed`
4. Include a "Classification of new citations" header table (Christen2012, FellegiSunter1969, Wilson2017GoodEnough, optional LittleRubin2019/Pedregosa2011Sklearn) with disposition.
5. Include a "Scope-overlap with §4.1" table at the top — flag every fact that §4.1 already cites (CONSORT flows, view row counts, view column counts) and explicitly mark whether §4.2 re-uses with a NEW framing (preprocessing decision) or omits entirely. This is the primary mechanism for preventing scope-creep violations at adversarial review.
6. **Halt predicate (T01):** more than 5 numbers cannot be anchored to an artifact line within 5 lookups each. If halt, list the un-anchored numbers and stop — user decides whether to produce missing artifacts (e.g., run a one-off SQL) or narrow the §4.2 scope.

**Verification:**
- File `thesis/pass2_evidence/sec_4_2_crosswalk.md` exists.
- Row count: target 80–120 rows (§4.1 crosswalk had 101 — §4.2 has slightly less distinct numerical density because it narrates decisions rather than magnitudes).
- "Scope-overlap with §4.1" table present and non-empty (expected ≥15 rows — CONSORT-flow numbers, view row counts, view column counts all re-appear).
- Classification table has exactly 5 candidate new bib entries, each with verification state.

**File scope:** writes
- `thesis/pass2_evidence/sec_4_2_crosswalk.md`

**Read scope:**
- 30 per-dataset 01_04-and-prior artifact .md files (paths above)
- 3 missingness ledger CSV files
- `thesis/pass2_evidence/sec_4_1_crosswalk.md` (format reference)
- `thesis/chapters/04_data_and_methodology.md` (to enumerate §4.1 scope-overlap)

**Char budget:** T01 produces a crosswalk artifact (not thesis prose) — expect 6–10k characters of Markdown, mostly tabular.

**Risk:** Low. Mechanical extraction. Main failure mode is mis-reading a Polish-typography number (e.g., "17 814 947" read as two fields). Mitigation: the normalization column forces every writer to record the raw form.

---

### T02 — Draft §4.2.1 Ingestion i walidacja (Polish, first pass)

**Objective:** Draft §4.2.1 in Polish academic register, arguing the two-path ingestion pattern (metadata path + events path for SC2; agregat-Parquet path for aoestats; dual-cadence Parquet+CSV path for aoe2companion) as preprocessing decisions with alternatives considered. Target 5–7k Polish characters.

**Must justify (alternatives-considered list):**
1. **Why DuckDB over a relational warehouse (Postgres/BigQuery).** Alternative = columnar DW with managed schema. Decision = DuckDB embedded with `tmp/` spill-to-disk. Reason = (a) reproducibility via one Python process per notebook (I6), no shared DB state; (b) free at laptop scale up to ~300M rows; (c) native Parquet/JSON read without an ETL step; (d) WAL-free — every ingestion is idempotent CTAS. Cite `Wilson2017GoodEnough` as reproducibility reference.
2. **Why split SC2 metadata and events into separate DuckDB tables.** Alternative = single wide table with STRUCT[] event arrays. Decision = split into `replays_meta_raw` (22,390 rows) + `replay_players_raw` (44,817 rows) + `map_aliases_raw` (104,160 rows) + three Parquet-backed event VIEWS (tracker/game/message). Reason = 367.6 GB estimated event-array storage (01_02_01) vs. ~1 GB metadata; column-oriented scans on events do not need to hydrate full JSON rows. Cite `01_02_01_duckdb_pre_ingestion.md`.
3. **Why `union_by_name=true` for aoestats Parquet variant schemas.** Alternative = force-cast to first-file schema. Decision = `union_by_name=true` + post-ingest type-unification (`profile_id` DOUBLE promoted in 36 files, int64 in 135 files → BIGINT in analytical views; `started_timestamp` us/ns precision auto-promoted to highest). Reason = aoestats schema drifted across the 172-week history; forcing first-file schema would lose variant columns or silently coerce integer IDs to float (precision risk for profile_ids >2^53 — flagged in 01_02_01). Cite `01_02_01_duckdb_pre_ingestion.md` ("**FLAG:** Player IDs as float64 may cause join precision issues for IDs > 2^53").
4. **Why aoe2companion needs explicit dtype for ratings.** Alternative = `read_csv_auto`. Decision = explicit BIGINT/TIMESTAMP types on 2,072 CSV files. Reason = `read_csv_auto` inferred all 7 columns as VARCHAR on the full load — would lose numeric fidelity (01_02_02 artifact).
5. **Why I10 (relative `filename`) enforced inline in CTAS rather than post-load UPDATE.** Alternative = UPDATE after load. Decision = `SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)` in the CTAS. Reason = OOM on aoestats `players_raw` (107M rows) and aoe2companion `matches_raw` (277M rows) with the UPDATE approach (CROSS research_log entry 2026-04-14). Inline transformation is the canonical I10 protocol across all three datasets.

**Must contrast (literature comparison):**
- Contrast our DuckDB-based ingestion with the alternative of a dedicated workflow orchestrator (Airflow / Prefect / Dagster). Argument: for a thesis-scale reproducibility requirement (I6), a single-process notebook pipeline is strictly more traceable than a DAG runner. Hedge: "Dla większych obciążeń produkcyjnych preferowane byłyby rozwiązania orkiestracji zadań, lecz wymagania reprodukowalności pracy magisterskiej faworyzują architekturę jednoprocesową." No direct literature cite; forward-ref to Appendix A for architecture details.

**Must cite (bib key list):**
- `Bialecki2023` (SC2EGSet source format)
- `AoEStats` (aoestats source)
- `AoeCompanion` (aoe2companion source)
- `BlizzardS2Protocol` (optional — s2protocol layer preceding our ingestion)
- `Wilson2017GoodEnough` (reproducibility principle)

**Tables to produce:**
- **Tabela 4.5** (pre-reserved numbering if §4.2.3 does not use it; see task T04 note) — skip here; §4.2.1 uses prose+inline cross-refs to §4.1 Tabela 4.1/4.2/4.3. No new tables.

**Figures:** None. (See Unknown #3.)

**Citations needed:** 5 keys above. All already in `references.bib` except `Wilson2017GoodEnough` — add to T01 bib-addition list.

**Cross-references:**
- Back-ref: §4.1.1.2 (event-stream structure), §4.1.2.0 (dwukorpusowa strategia AoE2 rationale)
- Forward-ref: §4.3 (feature engineering), §4.4 (split protocol), Appendix A (pipeline architecture diagram — future)
- Intra-§4.2 forward-ref: §4.2.2 (identity resolution — once IDs are ingested), §4.2.3 (cleaning rules — once raw tables exist)

**Crosswalk entries:** Row type "ingestion-strategy" — likely 15–20 rows in the T01 crosswalk (file counts, size totals, row counts per raw table, 0-orphan / 0-null-filename assertions).

**Invariant-discipline checks:**
- **I6 (reproducibility):** §4.2.1 narrates that every ingestion query is preserved verbatim in the `01_02_02_duckdb_ingestion.json` artifact.
- **I9 (raw immutability):** §4.2.1 states explicitly that raw files are never modified — all transformations happen at CTAS into DuckDB or into VIEWs.
- **I10 (relative filename):** §4.2.1 must narrate the inline-substring I10 protocol AND the historical context (the research_log 2026-04-14 entry documents that both AoE2 datasets initially stored absolute paths and were corrected).
- **I3 (temporal discipline):** §4.2.1 should flag that the ingestion step does NOT yet enforce I3; I3 enforcement happens at view construction (§4.2.3).

**Out-of-scope items (prevent scope creep):**
- Do NOT describe corpus statistics (those are in §4.1).
- Do NOT describe the `matches_flat_clean` / `matches_1v1_clean` / `player_history_all` views here — those are products of §4.2.3 cleaning. §4.2.1 ends at `*_raw` tables (raw ingestion output).
- Do NOT describe event extraction in detail — §4.2.1 mentions that event VIEWs exist over Parquet subdirectories, forward-refs to §4.3.2 for their use.
- Do NOT describe the player-history vs. prediction-target split — that is §4.2.3 design.
- Do NOT re-narrate §2.2.4 PlayerStats periodicity — it is §2.2 material.

**Voice note:** Argumentative. Each paragraph must close with a decision statement grounding the narrative in a preprocessing choice. Example pattern (from §4.1 voice): "Decyzja o (X) wynika z (observation Y cytowany z artefaktu Z); alternatywą byłoby (W), odrzucone z powodu (reason — empirical or I-cited)."

**Instructions:**
1. Draft three paragraphs per dataset (~1.5–2k chars each subsection): (a) source format and acquisition pattern, (b) ingestion decision with alternatives, (c) validation check (0-null / 0-orphan assertions).
2. Add a closing cross-cutting paragraph (~800 chars) arguing that I6/I9/I10 are enforced identically across the three disparate source formats — this is the "cross-game comparability" thread (I8) at the preprocessing layer.
3. Every numerical claim references a row in `sec_4_2_crosswalk.md`; missing-anchor → halt per T01 halt protocol.
4. Use Polish typography: space as thousand separator, comma as decimal, italic for first occurrence of technical anglicisms.
5. Flag `[REVIEW]`: (a) whether `Wilson2017GoodEnough` citation is appropriate for I6 context in academic thesis or merely "grey-literature acceptable"; (b) whether the CROSS research_log I10 correction narrative merits disclosure at thesis level or is historic-process noise.

**Verification:**
- Section 4.2.1 exists in `thesis/chapters/04_data_and_methodology.md`.
- Character count: 5,000 ≤ len ≤ 7,000 Polish chars.
- Every number in §4.2.1 appears in `sec_4_2_crosswalk.md` (grep check).
- At least 4 "decyzja wynika z / alternatywą byłoby" argumentation patterns present.
- 2–4 `[REVIEW:]` flags inserted (Pass-2-appropriate).

**File scope:** writes
- `thesis/chapters/04_data_and_methodology.md` (section §4.2.1 only, replacing the HTML-comment skeleton at lines ~207–212)

**Read scope:**
- `thesis/pass2_evidence/sec_4_2_crosswalk.md` (from T01)
- SC2 artifacts 01_01_01, 01_01_02, 01_02_01, 01_02_02, 01_02_03 (paths in T01 instructions)
- aoestats artifacts 01_01_01, 01_01_02, 01_02_01, 01_02_02, 01_02_03 (analogous paths)
- aoe2companion artifacts 01_01_01, 01_01_02, 01_02_01, 01_02_02, 01_02_03 (analogous paths)
- `/Users/tomaszpionka/Projects/rts-outcome-prediction/reports/research_log.md` (CROSS entry 2026-04-14 for I10 correction context)
- `thesis/chapters/04_data_and_methodology.md` lines 1–203 (§4.1 voice calibration, forward-ref validation)
- `thesis/references.bib` (verify all 5 citation keys resolve)

**Char budget:** 5,000–7,000 Polish characters in the draft. T01-produced crosswalk does not count.

**Risk:** **Medium.** Primary risk: scope-creep into corpus-statistics narration. Pre-mitigation: the "Scope-overlap with §4.1" table from T01 is consulted before each paragraph. Secondary risk: overselling DuckDB as a methodology contribution — it is not; it is an implementation choice. Keep DuckDB-justification paragraphs minimal (~3 sentences).

---

### T03 — Draft §4.2.2 Rozpoznanie tożsamości gracza (Polish, first pass)

**Objective:** Draft §4.2.2 arguing the per-dataset canonical player identifier decisions against the backdrop of record-linkage literature, and forward-referencing the thesis-level canonical nickname rule (Invariant I2). Target 5–7k Polish characters.

**Must justify (alternatives-considered list):**
1. **Why `toon_id` (Battle.net) is the SC2 identifier of record in `matches_flat_clean`.** Alternative = nickname (2,495 distinct `toon_id` vs. 1,106 distinct nickname — 44,817 rows / 2,495 ≈ 18 games/player on average, while 44,817 / 1,106 ≈ 40 games/nickname). Reason = fewer distinct toon_ids than nicknames would suggest players have MULTIPLE accounts (rename/server-switch pattern — one nickname "serral" would collapse multiple account IDs). But actually the observed inequality is **2495 > 1106**, meaning nicknames REUSE (common alias "Serral" or generic "Player"), reinforcing that nickname alone is ambiguous. Decision in Phase 01 = use `toon_id` as the raw-table identifier; defer the **thesis-level canonical rule** (I2: lowercased nickname) to Phase 02 identity resolution, where multi-toon classification (server-switch vs. rename vs. ambiguous) happens. Cite `01_02_04_univariate_census.md` (cardinality evidence) and `Christen2012DataMatching` (framing).
2. **Why aoestats `profile_id` is treated as a strong globally-unique identifier.** Alternative = assume `profile_id` is ambiguous and perform record linkage. Decision = trust `profile_id` as unique across the aoe2.net ladder. Reason = (a) 641,662 distinct IDs in 107M rows is plausible for ranked 1v1 population; (b) aoestats API guarantees profile_id stability across the crawl (documentation); (c) max = 24,853,897 < 2^53 = precision-safe in DOUBLE (this matters because 01_02_01 promoted `profile_id` to DOUBLE). Cite `01_03_01_systematic_profile.json` (cardinality 641662, max 24853897) and `Bialecki2023`-analogous trust posture for a known-authoritative API source.
3. **Why aoe2companion `profileId` is also treated as authoritative despite higher name-fragmentation.** Alternative = nickname reconciliation across aoe2companion. Decision = `profileId` is authoritative; name fragmentation (3,387,273 distinct profileIds but only 2,468,478 distinct `name`) is framed as a CHARACTERISTIC of the source (REST API exposes both), not a cleaning-layer defect. Reason = inferring multiple profileIds per player is a Phase 02 feature-engineering task per I2, not a Phase 01 data-cleaning task per I9. Cite `01_03_01_systematic_profile.json` (cardinality 3,387,273) and the derived 2,468,478 distinct names from 01_02_04 census.
4. **Why multi-dataset identity is NOT unified across SC2/AoE2.** Alternative = a cross-game player graph (e.g., a streamer who plays both SC2 and AoE2). Decision = identities are per-game; no cross-game join attempted. Reason = (a) scope (RQ1–RQ4 are within-game; RQ3 is method-level cross-game, not player-level); (b) no public mapping between Battle.net `toon_id` and aoe2.net `profile_id`; (c) attempting it would inflate entity-resolution scope to thesis-breaking dimensions. Cite `FellegiSunter1969` as the framing and argue explicitly that the thesis takes the **non-linkage** path.
5. **Why identity-resolution is deferred to Phase 02 (§4.3.1), not Phase 01 (§4.2).** Alternative = resolve identities at cleaning time (01_04). Decision = `matches_flat_clean` / `matches_1v1_clean` retain raw identifiers; canonical player key (nickname lowered; aoe2 profile_id; sc2 toon_id) is assigned per-target-row in Phase 02. Reason = I2 (nickname as canonical) is thesis-level methodology; I9 (raw immutability) restricts what Phase 01 can compute. Phase 01 surfaces the fragmentation pattern but does not unify it. Forward-ref to §4.3.1.

**Must contrast (literature comparison):**
- Contrast our "trust the API/dataset-provided ID + lowercase-nickname later" decision against the classic record-linkage pipeline (Fellegi-Sunter 1969; Christen 2012). Argument: our three datasets each carry a high-quality numeric identifier; the foundational record-linkage literature addresses scenarios where no stable ID exists (registers of persons, duplicate-detection of medical records). We do not need probabilistic matching because the ID quality is sufficient. We acknowledge the framework and explain why it does not apply.
- Hedge: "Zastosowanie probabilistycznego rozpoznania rekordów w rozumieniu [FellegiSunter1969] i [Christen2012DataMatching] byłoby uzasadnione, gdyby identyfikatory źródłowe nie były wiarygodne. W niniejszej pracy trzy zbiory danych dostarczają wiarygodnych, globalnie unikalnych identyfikatorów liczbowych; zagadnienie rozpoznania pozostaje referencyjne, nie operacyjne."

**Must cite:**
- `FellegiSunter1969` (new — foundational record linkage)
- `Christen2012DataMatching` (new — canonical textbook)
- `Bialecki2023` (SC2 source, ToonPlayerDescMap structure authority)
- `AoEStats`, `AoeCompanion` (AoE2 source identifier authority)

**Tables to produce:**
- **Tabela 4.5** (§4.2.2 table) — cross-dataset identifier comparison:
  | Wymiar | SC2EGSet | aoestats | aoe2companion |
  |---|---|---|---|
  | Nazwa kolumny identyfikatora | `toon_id` | `profile_id` | `profileId` |
  | Typ surowy | VARCHAR (string) | DOUBLE (precision-risked) → BIGINT | INTEGER |
  | Kardynalność w `*_raw` | 2 495 | 641 662 | 3 387 273 |
  | Łączny rozmiar populacji | Profesjonalna turniejowa | Ladderowa 1v1 random_map | Ladderowa 1v1 (rm_1v1 + qp_rm_1v1) |
  | Średnia liczba meczów na gracza | 44 817 / 2 495 ≈ 17,96 | 107 626 399 / 641 662 ≈ 167,7 | 264 132 745 / 3 387 273 ≈ 77,98 |
  | Kardynalność pola `nickname` / `name` | 1 106 | n/d (brak kolumny nicknames) | 2 468 478 |
  | Stosunek id-do-nick | 2 495 / 1 106 = 2,26 | n/d | 3 387 273 / 2 468 478 = 1,37 |
  | Wnioskowana struktura wielokontowa | Prawdopodobna — 2× więcej ID niż nicków sugeruje aliasing/rename | Nie ewaluowane (brak danych) | Możliwa — 1,37× więcej ID niż nicków |
  | Status w `*_clean` | Zachowany jako kanoniczny dla warstwy `matches_flat_clean` | Pivotowany do `p0_profile_id`/`p1_profile_id` | Zachowany na wiersz gracza |
  | Rozpoznanie Phase 02 | Nick-level canonicalization (I2) | Prawdopodobne do pominięcia (stabilny `profile_id`) | Nick-level canonicalization (I2) |

  **Caption (Polish):** "Tabela 4.5. Porównanie schematów identyfikacji graczy w trzech korpusach po wstępnej akwizycji (Phase 01, Pipeline Section 01_02–01_04). Źródła liczb: `01_02_04_univariate_census.md` (kardynalności), `01_03_01_systematic_profile.json` (profile_id min/max), oraz pochodne arytmetyczne wierszy i kardynalności."

**Figures:** None.

**Citations needed:** 2 new keys (`FellegiSunter1969`, `Christen2012DataMatching`) + 3 existing (`Bialecki2023`, `AoEStats`, `AoeCompanion`). T01 crosswalk records both new keys for verification.

**Cross-references:**
- Back-ref: §4.1.1.5 (SC2 zawodowa turniejowa populacja) — but only a one-sentence cross-ref, NOT re-narration.
- Forward-ref: §4.3.1 (symmetric feature engineering with nickname canonical key I2), §4.4.1 (per-player temporal split operates on canonical player), §4.3.1 identity-resolution placement.
- Back-ref to §1.2 (problem statement — predicting the next game for a player requires a canonical player).

**Crosswalk entries:** Row type "identity-cardinality" — likely 8–12 rows (3 id cardinalities, 2 nickname cardinalities, 3 id-to-nick ratios, 3 averages per player, max profile_id value).

**Invariant-discipline checks:**
- **I2 (canonical nickname):** §4.2.2 must explicitly state that Phase 01 defers I2 operationalization to Phase 02 and narrates why (I9 forbids feature-layer transformations at cleaning time).
- **I9 (raw immutability):** §4.2.2 must state that no identity resolution modifies `*_raw` tables.

**Out-of-scope items:**
- Do NOT resolve multi-account cases here (Phase 02 work per I2).
- Do NOT compute a player-coverage distribution histogram (Phase 02 — that is "cold-start analysis", §5.x domain).
- Do NOT discuss Elo/MMR (§2.5 domain; §4.2.3 for MMR missingness only).

**Voice note:** Argumentative. The framing gymnastic is: §4.2.2 positions the three identifier schemes in a matrix, acknowledges the record-linkage literature, argues we don't need it, and defers canonicalization. Tone = "consciously minimal — we have sufficient IDs and we do not over-engineer."

**Instructions:**
1. Open paragraph (~600 chars): frame the identity problem, introduce the three schemes, cite Fellegi-Sunter + Christen as the theoretical frame, pre-announce the "deferral to Phase 02" posture.
2. One paragraph per dataset (~1,000–1,200 chars each): (a) what the identifier is, (b) cardinality evidence, (c) whether nickname-vs-ID fragmentation is observable, (d) what the Phase 01 decision is.
3. Closing paragraph (~800 chars): frame the per-dataset decisions as a single coherent strategy (identifier trust + deferred canonicalization), state what Phase 02 adds, cite I2.
4. Tabela 4.5 as a structural exhibit, inserted after paragraph 4 (the closing paragraph); table caption is Polish academic prose.
5. Flag `[REVIEW]` on: (a) the nickname-cardinality 2,468,478 for aoe2companion (verify against the JSON artifact, `01_02_04_univariate_census.json` name_cardinality row); (b) the interpretation that SC2 toon_id > nickname cardinality indicates multi-account (could also be random server accounts creating noise).

**Verification:**
- Section 4.2.2 exists; 5,000 ≤ len ≤ 7,000 chars.
- Tabela 4.5 present with caption.
- All 5 citations resolved; 2 new keys flagged for `references.bib` addition.
- Forward-ref to §4.3.1 and §4.4.1 present.
- No Phase 02 computation performed (verified by absence of any "najwięcej meczów" sentence).

**File scope:** writes
- `thesis/chapters/04_data_and_methodology.md` (section §4.2.2 + Tabela 4.5)
- `thesis/references.bib` (2 new entries: `FellegiSunter1969`, `Christen2012DataMatching`)

**Read scope:**
- `thesis/pass2_evidence/sec_4_2_crosswalk.md`
- `01_02_04_univariate_census.md` and `.json` for all three datasets (identifier cardinality)
- `01_03_01_systematic_profile.json` for aoestats (profile_id max=24853897) and aoe2companion (profileId cardinality=3387273)
- `01_01_02_schema_discovery.md` for SC2 (ToonPlayerDescMap structure confirming toon_id as nested key)
- `thesis/chapters/04_data_and_methodology.md` §4.1 for voice/cross-ref validation
- `thesis/references.bib` (verify current entries before appending)

**Char budget:** 5,000–7,000 Polish chars.

**Risk:** **Medium-high.** Risks: (1) over-claiming multi-account patterns from cardinality ratios alone (the 2.26× ratio for SC2 could have other explanations — hedge heavily); (2) the new bib entries need Pass 2 verification (neither has been used before in this thesis); (3) inadvertently proposing identity-resolution work that belongs to Phase 02.

---

### T04 — Draft §4.2.3 Reguły czyszczenia i ważny korpus (Polish, first pass)

**Objective:** Draft §4.2.3 presenting the cross-dataset cleaning-rule registry as a typology (MCAR/MAR/MNAR → DROP/NULLIF/FLAG routing), defending the MissingIndicator pattern as I3-compliant (NOT an apology for deferral), and narrating per-dataset invocations of the rule types. Target 8–10k Polish characters (richest subsection).

**Must justify (alternatives-considered list):**
1. **Why we use a rule-based registry rather than ad-hoc per-column fixes.** Alternative = inline column-by-column patching in the notebook. Decision = formal registry with rule IDs (R01–R08 in SC2, R00–R08 in aoestats, R00–R05 in aoe2companion) and per-rule condition/action/impact/justification. Reason = (a) reviewability — every decision has a rule ID that surfaces in post-cleaning validation; (b) reproducibility (I6) — the registry is serialized to the cleaning artifact JSON; (c) invariance across datasets — same taxonomy across three sources enforces I8. Cite `01_04_01_data_cleaning.md` for each dataset.
2. **Why missingness is classified MCAR/MAR/MNAR per `Rubin1976` taxonomy BEFORE routing to DROP/NULLIF/FLAG.** Alternative = routing on rate alone (e.g., "drop if >30%"). Decision = mechanism first, then rate-thresholded routing (DROP at ≥80% per van Buuren; FLAG_FOR_IMPUTATION at 5–40% MAR; listwise NULLIF at <5% MCAR). Reason = the mechanism changes what imputation is even defensible (MNAR can't be safely imputed; MAR can with the right conditioning; MCAR is the easy case). Cite `Rubin1976`, `vanBuuren2018`, `SchaferGraham2002`.
3. **Why the MissingIndicator pattern for primary features (MMR, rating, old_rating) is I3-compliant, NOT a cop-out.** Alternative A = impute rating at cleaning time with median-within-rating. Alternative B = drop rows with missing rating. Decision = NULLIF (or RETAIN) + binary flag (`is_mmr_missing`, `p0_is_unrated`, `rating_was_null`). Reason = (a) I3 forbids computing features (imputation is a feature) from data at time T using time-T or later information; cleaning-time imputation would leak future statistics (the median in 2024 is distributionally different from 2016); (b) the missingness itself carries signal (MMR=0 in SC2 means "unrated professional" per Battle.net schema, a subgroup-membership signal, not a zero-skill signal — it cannot be imputed, only flagged); (c) Phase 02 fold-aware imputation preserves I3 because the fit happens on each fold's training data only (reference I3-normalization-leakage clause in `.claude/scientific-invariants.md`). Cite `Rubin1976`, `vanBuuren2018`.
4. **Why SC2 MMR=0 is MAR, not MNAR (Rubin 1976 taxonomy).** Alternative interpretation = MNAR (value zeroed because player is of certain type — professional unrated). Decision in the 01_04_01 ledger = MAR (the missingness is CONDITIONED on observable attributes: account type, tournament participation). Reason = MAR/MNAR distinction hinges on whether the missingness depends on the MISSING VALUE ITSELF vs. on OBSERVABLE ATTRIBUTES; "unrated professional" is an observable attribute (account type/tournament context), so MAR applies per strict Rubin taxonomy. Hedge heavily: some taxonomists would argue MNAR. Flag `[REVIEW: MAR vs MNAR interpretation — primary feature]`. Cite `Rubin1976`.
5. **Why the per-dataset rule counts differ (SC2: 7 rules R01–R07 + 10 DS decisions; aoestats: 8 rules R00–R08; aoe2companion: 5 rules R00–R05 + 8 DS decisions).** Alternative = unified rule set across all three. Decision = per-dataset tailoring (each source has idiosyncratic sentinel patterns; forcing a unified rule set would produce rules that are inactive in one dataset). Reason = (a) different source APIs use different sentinels (SC2: MMR=0 for unrated, APM=0 for parse-failure, INT32_MIN for SQ parse; aoestats: Elo=0, Elo=-1; aoe2companion: NULL); (b) the rule typology (MCAR/MAR/MNAR × rate band × action) IS unified, while the specific invocations differ. Frame this as I8-consistent: the methodology is identical; the parameters bind to per-dataset observations.
6. **Why aoe2companion's `rating` MAR at 26.20% is FLAG_FOR_IMPUTATION rather than DROP_COLUMN (Rule S4 exception).** The 40–80% band maps to DROP per default, but `rating` is a PRIMARY feature — dropping it would halt the entire pre-game feature class for AoE2. van Buuren's primary-feature exception allows FLAG_FOR_IMPUTATION above the default cutoff when the feature's predictive value justifies it. Cite `vanBuuren2018` explicitly for the exception.

**Must contrast (literature comparison):**
- Contrast our MissingIndicator pattern against multiple imputation (MICE) per van Buuren 2018. Argument: MICE requires fit-on-training-only discipline to preserve I3. Our Phase 01 `*_clean` VIEWs are fold-agnostic (they must be, since splits happen in Phase 03), so imputation is deferred to the Phase 02 fold-aware preprocessing stage. The MissingIndicator in Phase 01 preserves the missingness signal losslessly for Phase 02 to consume.
- Contrast our 5%/40%/80% threshold framework against the alternative of a single 30% "drop threshold" (common ad-hoc rule in ML tutorials). Argument: the three-threshold system is defensible by mechanism; a single threshold ignores mechanism entirely.

**Must cite:**
- `Rubin1976` (already in bib — taxonomy)
- `vanBuuren2018` (already in bib — 80% threshold + primary-feature exception)
- `SchaferGraham2002` (already in bib — 5% MCAR threshold)
- Optional: `Pedregosa2011Sklearn` OR `LittleRubin2019` — evaluate during drafting; do not commit unless a specific claim requires them.

**Tables to produce:**
- **Tabela 4.6** (§4.2.3 cross-dataset cleaning-rule typology). Five rule types × three datasets × outcome.
  | Typ reguły (mechanizm + rate) | SC2EGSet | aoestats | aoe2companion |
  |---|---|---|---|
  | Scope-filter (true 1v1 decisive / leaderboard filter) | R01 (−24 meczów) | R02 (filter to random_map) + R01 (BIGINT cast) | R01 (filter to leaderboardId IN 6,18) |
  | Target-consistency filter (decisive winner) | R01 część (Result ∈ {Win, Loss}) | R08 (inconsistent winner, −997 meczów) | R03 (won complementarity, −5 052 meczów) |
  | Deduplication | (nd — struktura nie dopuszcza duplikatów) | (nd) | R02 (dedup matchId×profileId, −6 wierszy) |
  | Replay-level exclusion (ANY player with anomaly) | R03 (MMR<0 → exclude replay, −157 meczów) | (nd — per-row filter wystarczy) | (nd) |
  | Sentinel → NULLIF (<5% MCAR) | DS-SC2-09 (handicap=0, 2 rows), DS-SC2-10 (APM=0, 1132 rows) | DS-AOESTATS-02 (p0/p1 old_rating=0), DS-AOESTATS-03 (avg_elo=0, 118 rows) | (nd — brak niskokwotowych sentyneli) |
  | DROP_COLUMN high-sentinel (≥80% MNAR/MAR) | DS-SC2-01 (MMR 83,95%), DS-SC2-02 (highestLeague 72,04%), DS-SC2-03 (clanTag 73,93%) | DS-AOESTATS-08 (leaderboard, num_players constants) | DS-AOEC-01 (server 97,39%, scenario 100%, modDataset 100%, password 77,57%) |
  | FLAG_FOR_IMPUTATION (5–40% MAR non-primary) | (nd — middle-band kolumny już wydropowane w DS-SC2-02/-03) | (nd) | DS-AOEC-02 (hideCivs 37,18%), DS-AOEC-05 (country 8,30% history) |
  | FLAG_FOR_IMPUTATION (>40% MAR primary — exception S4) | (nd) | (nd) | DS-AOEC-04 (rating 26,20% — primary-feature exception per vanBuuren2018) |
  | MissingIndicator-plus-NULLIF (missingness-as-signal) | DS-SC2-01 (`is_mmr_missing`), DS-SC2-10 (`is_apm_unparseable`) | DS-AOESTATS-02 (`p0_is_unrated`, `p1_is_unrated`, `is_unrated`) | DS-AOEC-04 (`rating_was_null`) |
  | Constants/duplicates drop | DS-SC2-08 (12 go_* constants), DS-SC2-06 (gd_mapSize) | DS-AOESTATS-04 (raw_match_type), DS-AOESTATS-08 (leaderboard/num_players) | (inlined in schema; no explicit DS) |
  | Schema-evolution exclusion | DS-SC2-06 (gd_mapSizeX/Y=0 anomaly, 273 replays) | DS-AOESTATS (implicit — opening/age_uptime absent post-2024-03-10 per I3 cleanup) | R04 (10-col NULL cluster flag), DS-AOEC-02 (antiquityMode 60,06%) |
  | POST_GAME exclusion (I3 violation) | (implicit — elapsedGameLoops kept in player_history_all only) | R06 (new_rating excluded from both VIEWs) | (implicit — ratingDiff excluded from long skeleton) |

  **Caption (Polish):** "Tabela 4.6. Typologia reguł czyszczenia danych stosowanych w Phase 01 Pipeline Section 01_04 we wszystkich trzech korpusach. Każdy wiersz to klasa reguły (mechanizm missingness wg taksonomii [Rubin1976] + pasmo rate per [vanBuuren2018] / [SchaferGraham2002] + akcja); kolumny dataset-specific podają konkretne invokacje reguły z identyfikatorami R lub DS. Odwołanie (nd) = reguła nie ma zastosowania w danym korpusie (typologia unifikowana, invokacje dataset-specific). Źródła: `01_04_01_data_cleaning.md`, `01_04_01_missingness_ledger.csv`, `01_04_02_post_cleaning_validation.md` we właściwych katalogach artefaktów."

**Figures:** None.

**Citations needed:** 3 existing (Rubin1976, vanBuuren2018, SchaferGraham2002). Pedregosa2011Sklearn and LittleRubin2019 evaluated during drafting — flag for Pass 2 consideration if added.

**Cross-references:**
- Back-ref: §4.1.1.4 (SC2 missingness findings), §4.1.2.1 (aoestats NULLIF+flag), §4.1.2.2 (aoe2companion 26.20% rating NULL) — these provide the empirical substrate. §4.2.3 must add the typology-and-argument layer that §4.1 did not.
- Back-ref to §2.5.4 (Battle.net MMR mechanism — explains why MMR=0 is a Battle.net sentinel, not a skill value).
- Forward-ref: §4.3.1 (feature engineering — consumes the cleaned views + flags), §4.4.2 (hyperparameter tuning — imputation strategy selection), §6.5 (threats to validity — generalization limits given MNAR/MAR/MCAR mechanism mix).
- Forward-ref to §2.5 for Elo/Glicko — why retrospective Glicko-2 computed in Phase 02 is a strictly better signal than trusting MMR field.

**Crosswalk entries:** Row type "cleaning-rule" — likely 35–45 rows in T01 (per-dataset rule impacts, ledger rates, column-count flows, assertion counts).

**Invariant-discipline checks:**
- **I3 (temporal discipline):** §4.2.3 MUST defend MissingIndicator as I3-compliant, not apologize for deferral. Specifically: Phase 01 does not know the fold structure; any imputation at Phase 01 would leak future-fold statistics into past-fold imputation. Deferring to Phase 02 with fold-aware imputation is the ONLY I3-compliant path. This is the primary adversarial-defence point for §4.2.3.
- **I5 (symmetry):** §4.2.3 narrates how the cleaning preserves slot symmetry — no rule privileges `p0` over `p1` or `side=0` over `side=1`; the observed slot asymmetries (SC2 51.96/47.97, aoestats 52.27/47.73, aoe2companion 52.82/47.18 for team=2/team=1) are DOCUMENTED, not corrected, to avoid feature leakage. Cite the 01_04_00 source normalization audit per dataset.
- **I6 (reproducibility):** every rule has its SQL stored verbatim in the JSON artifact (`01_04_01_data_cleaning.json` etc.).
- **I7 (no magic numbers):** every threshold (5%, 40%, 80%) is cited to van Buuren 2018 or Schafer & Graham 2002. No unjustified constant appears in §4.2.3.
- **I8 (cross-game consistency):** the rule typology is unified; invocations differ per dataset by observation. §4.2.3 states this explicitly.
- **I9 (raw immutability):** every rule operates on VIEWs; raw tables are never modified.

**Out-of-scope items:**
- Do NOT propose Phase 02 imputation strategies in detail (forward-ref only).
- Do NOT re-narrate the §4.1 corpus-level CONSORT flow numbers (Tabela 4.1/4.2/4.3 are already in §4.1 and cross-referenced here by pointer).
- Do NOT discuss `*_flat_clean` column counts in detail (those are §4.1.x material).
- Do NOT propose changes to cleaning rules based on §2.5 MMR mechanics — the Phase 01 rule set is final as of 01_04_02 validation; §4.2.3 describes, not revises.
- Do NOT introduce the 01_05 Temporal & Panel EDA findings (deferred).

**Voice note:** Argumentative throughout. Each rule-class discussion must include (a) mechanism, (b) rate-band, (c) action, (d) alternative, (e) rejection reason, (f) cite. The MissingIndicator defence must be FORWARD-LEANING — argue that the pattern is a deliberate methodological discipline, not a deferral.

**Instructions:**
1. Opening paragraph (~800 chars): establish the typology-before-invocation structure; cite Rubin 1976 + van Buuren 2018 + Schafer & Graham 2002; pre-announce the MissingIndicator I3-compliance defence.
2. Paragraph per rule class (~400–700 chars each): scope-filter, target-consistency, sentinel-low, DROP-high, FLAG_FOR_IMPUTATION, MissingIndicator pattern, schema-evolution, POST_GAME-I3. 6–8 paragraphs total.
3. Closing defence paragraph (~1,200 chars): explicitly argue why MissingIndicator is I3-compliant and why the 5%/40%/80% thresholds are not magic numbers (I7). This is the adversarial-defence centrepiece.
4. Tabela 4.6 inserted between opening and per-rule paragraphs as a structural scaffold.
5. Flag `[REVIEW]`: (a) MAR-vs-MNAR for MMR (high-stakes taxonomy call); (b) primary-feature exception at 26.20% — confirm against van Buuren's exact wording; (c) the unified-typology claim at I8 level — confirm no rule-level divergence that undermines I8.

**Verification:**
- Section 4.2.3 exists; 8,000 ≤ len ≤ 10,000 Polish chars.
- Tabela 4.6 present with caption.
- All 3 primary citations resolved.
- Minimum 4 "alternatywą byłoby / decyzja wynika z" patterns in the rule-class paragraphs.
- Minimum 2 MissingIndicator defence sentences in the closing paragraph, citing I3.
- Minimum 3 `[REVIEW]` flags (Pass-2-appropriate).

**File scope:** writes
- `thesis/chapters/04_data_and_methodology.md` (section §4.2.3 + Tabela 4.6)

**Read scope:**
- `thesis/pass2_evidence/sec_4_2_crosswalk.md`
- All three 01_04_01 `data_cleaning.md` files
- All three 01_04_01 `missingness_ledger.csv` files
- All three 01_04_02 `post_cleaning_validation.md` files
- `01_04_00_source_normalization.md` for slot-asymmetry numbers
- `thesis/chapters/04_data_and_methodology.md` §4.1 lines 41–43 (SC2 MMR text), lines 89–94 (aoestats Elo text), lines 124–132 (aoe2companion rating text) for voice precedent and cross-ref targets
- `.claude/scientific-invariants.md` (I3 normalization-leakage clause verbatim) for the defence paragraph

**Char budget:** 8,000–10,000 Polish chars.

**Risk:** **High.** This is the richest and most adversarial-sensitive subsection. Risks: (1) accidentally re-narrating §4.1.1.4 MMR text — mitigated by strict typology framing and a "§4.1 scope-overlap" check before each paragraph; (2) under-defending MissingIndicator — mitigated by the explicit closing defence paragraph; (3) MAR/MNAR taxonomy dispute on MMR — mitigated by `[REVIEW]` flag and explicit hedging; (4) introducing unjustified thresholds — mitigated by I7 discipline check at the closing paragraph.

---

### T05 — Integrate cross-references and update tracking files

**Objective:** After T02–T04 drafts exist, perform the cross-reference integration pass: validate all forward-refs resolve (or plant `[REVIEW]` flags for §4.3/§4.4 sections still BLOCKED), verify all back-refs to §4.1/§2.5 point to actual text, update `thesis/WRITING_STATUS.md`, append entries to `thesis/chapters/REVIEW_QUEUE.md`, update `reports/research_log.md` with a CROSS entry documenting the §4.2 draft.

**Instructions:**
1. Open the drafted §4.2.1/§4.2.2/§4.2.3 and scan every reference. Resolve each to its target: existing §4.1 subsection, existing §2.5/§2.2, BLOCKED §4.3/§4.4 (flag with `[REVIEW: forward-ref to §4.3.1 — BLOCKED Phase 02]`).
2. Update `thesis/WRITING_STATUS.md` → §4.2.1, §4.2.2, §4.2.3 → DRAFTED with notes:
   - `§4.2.1 Ingestion and validation | DRAFTED | Phase 01 (01_01–01_02 for all three datasets) | Drafted 2026-04-18. ~6.0k znaków polskich. N [REVIEW] flags. Bib: Wilson2017GoodEnough added.`
   - `§4.2.2 Player identity resolution | DRAFTED | Phase 01 (01_02_04, 01_03_01 for all three datasets) | Drafted 2026-04-18. ~6.5k znaków polskich. N [REVIEW] flags. Tabela 4.5 present. Bib: FellegiSunter1969 + Christen2012DataMatching added.`
   - `§4.2.3 Cleaning rules and valid corpus | DRAFTED | Phase 01 (01_04_01, 01_04_02 for all three datasets) | Drafted 2026-04-18. ~9.0k znaków polskich. N [REVIEW] flags. Tabela 4.6 present. No new bib entries.`
3. Append three new rows to `thesis/chapters/REVIEW_QUEUE.md` Pending Pass 2 table — one per subsection, using the existing column schema (Section | Chapter file | Drafted date | Flag count | Key artifacts | Pass 2 status).
4. Append a CROSS entry to `/Users/tomaszpionka/Projects/rts-outcome-prediction/reports/research_log.md`:
   - Date: 2026-04-18
   - Phase: 01
   - Heading: `[CROSS] 2026-04-18 — §4.2 Data preprocessing draft (Polish, 3 subsections)`
   - Narrate: crosswalk created at `thesis/pass2_evidence/sec_4_2_crosswalk.md`; 3 subsections drafted; new bib entries (Wilson2017GoodEnough, FellegiSunter1969, Christen2012DataMatching); pending Pass 2.
5. Append a halt log entry to `thesis/pass2_evidence/sec_4_2_halt_log.md` (new file, matches §4.1 precedent) attesting zero halt events during T02–T04, OR listing halt events with resolution.

**Verification:**
- `thesis/WRITING_STATUS.md` lists all 3 §4.2.x subsections as DRAFTED.
- `thesis/chapters/REVIEW_QUEUE.md` has 3 new Pending rows.
- `reports/research_log.md` has a CROSS 2026-04-18 entry referencing §4.2.
- `thesis/pass2_evidence/sec_4_2_halt_log.md` exists.
- All `[REVIEW]` flags in the chapter body have corresponding REVIEW_QUEUE rows.

**File scope:** writes/updates
- `thesis/WRITING_STATUS.md`
- `thesis/chapters/REVIEW_QUEUE.md`
- `reports/research_log.md`
- `thesis/pass2_evidence/sec_4_2_halt_log.md`
- `thesis/pass2_evidence/README.md` (append entry to Index table for the two new evidence files)

**Read scope:**
- Drafted §4.2 text (from T02–T04)
- Existing tracking files (for format/voice calibration)

**Char budget:** Metadata-layer; no thesis-prose budget.

**Risk:** **Low.** Mechanical bookkeeping. Primary failure = missing a `[REVIEW]` flag in REVIEW_QUEUE; mitigated by a regex scan at verification time.

---

### T06 — Lexical and typographic polish (Polish academic standard)

**Objective:** Final polish pass per `.claude/author-style-brief-pl.md` operational checklist: anglicisms, doubled-word scan, interpunction in multi-clause sentences, dopełniacz-chain length audit. Do not re-draft content; fix surface layer only.

**Instructions:**
1. **Anglicism pass:** scan for technical terms and verify each is either (a) italicized on first use with Polish equivalent, (b) retained in English as a settled technical term, or (c) replaced with Polish. Reference list: pipeline → *pipeline* italicized; schema → schemat; batch → batch (ML context); trigger → wyzwalacz (SQL) / trigger (ML); commit → zatwierdzenie (process) / commit (git); deployment → wdrożenie. Reject any `-ować` verb from English business roots (*statusować*, *eskalować*, *priorytetyzować*, *onboardować*).
2. **Doubled-word scan:** grep for `(\w+) \1\b` in the 3 drafted subsections. Document any hits for user review.
3. **Interpunction audit:** manual review of sentences >30 words. Verify comma before *który/która/które*, *że*, *ponieważ*, around imiesłowowe równoważniki zdań. Shorten or split any 10-line sentence cascade.
4. **Dopełniacz chain audit:** scan for noun-chains with >3 consecutive genitive nominals before a main verb. Rewrite via active-voice or split-sentence.
5. **Polish typography:** every number uses space as thousand separator, comma as decimal. Verify with targeted grep.
6. **Cross-ref sanity:** run the resolution validator from T05 once more.

**Verification:**
- No `-ować` business-verb calques.
- No doubled-word false positives.
- All technical anglicisms are either italicized on first use, glossed, or retained with context.
- No >3-element dopełniacz chain before main verb.
- All numbers use Polish typography.

**File scope:** updates
- `thesis/chapters/04_data_and_methodology.md` (polish edits only within §4.2.1/§4.2.2/§4.2.3)

**Read scope:**
- `.claude/author-style-brief-pl.md`
- Drafted §4.2 text

**Char budget:** No additions; edits reduce or keep length unchanged.

**Risk:** **Low.** Pure polish layer.

---

## File Manifest

| File | Task | Role |
|------|------|------|
| `thesis/pass2_evidence/sec_4_2_crosswalk.md` | T01 writes | Numerical crosswalk evidence |
| `thesis/chapters/04_data_and_methodology.md` | T02/T03/T04/T05/T06 write/update | §4.2.1/§4.2.2/§4.2.3 content |
| `thesis/references.bib` | T02/T03 write | +3 entries: Wilson2017GoodEnough, FellegiSunter1969, Christen2012DataMatching |
| `thesis/WRITING_STATUS.md` | T05 updates | Status → DRAFTED for 3 subsections |
| `thesis/chapters/REVIEW_QUEUE.md` | T05 appends | 3 new Pending Pass 2 rows |
| `reports/research_log.md` | T05 appends | CROSS 2026-04-18 entry |
| `thesis/pass2_evidence/sec_4_2_halt_log.md` | T05 writes (new) | Halt protocol log |
| `thesis/pass2_evidence/README.md` | T05 updates | Index table +2 rows |

---

## Gate Condition

§4.2 is DRAFTED when all of the following hold:

1. All three subsections (§4.2.1, §4.2.2, §4.2.3) are populated in `thesis/chapters/04_data_and_methodology.md`, replacing the current HTML-comment skeletons.
2. Combined §4.2 Polish character count ∈ [18,000 − 22,000].
3. `thesis/pass2_evidence/sec_4_2_crosswalk.md` exists with all numerical claims anchored; `sec_4_2_halt_log.md` exists.
4. `thesis/WRITING_STATUS.md` lists §4.2.1/§4.2.2/§4.2.3 as DRAFTED.
5. `thesis/chapters/REVIEW_QUEUE.md` has three new Pending rows.
6. `thesis/references.bib` includes the 3 new entries (Wilson2017GoodEnough, FellegiSunter1969, Christen2012DataMatching).
7. Tabela 4.5 and Tabela 4.6 are present with Polish captions citing their source artifacts.
8. Every threshold (5%, 40%, 80%) has an inline citation (I7 discipline).
9. The MissingIndicator pattern has an explicit I3-compliance defence paragraph in §4.2.3.
10. `reports/research_log.md` has the CROSS 2026-04-18 entry.
11. No `[UNVERIFIED]` flags remain (every number anchored in crosswalk). `[REVIEW]` flags allowed.
12. The critical-review checklist (data variant) from `.claude/rules/thesis-writing.md` passes self-assessment.

---

## Out of scope

1. **Phase 02 feature engineering.** §4.3 domain. Specifically out-of-scope: Glicko-2 retrospective rating computation, win-rate rolling windows, symmetric focal/opponent feature pairing, Elo normalization, imputation strategy selection, cold-start stratification.
2. **Split design.** §4.4.1 domain. Per-player temporal split, val/test windowing, stratification by tournament.
3. **Model configurations.** §4.4.2 domain.
4. **Evaluation metrics.** §4.4.4 domain — already DRAFTABLE per WRITING_STATUS; not §4.2.
5. **MMR mechanism and Glicko theory.** §2.5 domain (already DRAFTED).
6. **Corpus descriptive statistics.** §4.1.x domain (already DRAFTED). §4.2 re-uses at most numbers that frame preprocessing decisions, and only as pointers to §4.1 tables.
7. **In-game feature engineering.** §4.3.2 domain.
8. **AoE2 civilization feature encoding.** §4.3.3 domain.
9. **Figure generation.** Deferred to Appendix A or Phase 01 Step 01_05 output. §4.2 uses prose + existing §4.1 tables.
10. **Cross-game player identity unification.** §7.3 future work (forward-ref only).
11. **Phase 01 Step 01_05 Temporal & Panel EDA outputs.** Deferred per PHASE_STATUS; any claim requiring 01_05 is flagged `[REVIEW]`.
12. **Phase 01 Step 01_06 Decision Gates.** Deferred.

---

## Open questions

1. **Q1 for user — scope overlap with §4.1.1.3/§4.1.2.1/§4.1.2.2.** §4.1 already narrates view schemas and cleaning impacts (22,209 matches, 28 columns, `is_mmr_missing` flag, etc.). §4.2.3 proposes typology framing to avoid duplication. Does the user accept this framing, or should §4.2 be narrowed further (e.g., §4.2.3 focuses exclusively on the MissingIndicator defence + MCAR/MAR/MNAR taxonomy, omitting the cross-dataset rule typology)? Recommended default: accept typology framing; flag for reviewer-adversarial to validate the non-overlap.
2. **Q2 for user — MAR vs MNAR for MMR=0.** Current 01_04_01 artifact classifies MMR=0 as MAR. §4.2.3 draft will follow this, but `[REVIEW]` flag for Pass 2. Does the user want a pre-emptive revision to MNAR (which would ripple into §4.1.1.4 as well)? Recommended default: retain MAR per artifact; Pass 2 decides.
3. **Q3 for user — 3 new bib entries or minimum.** Proposed: `Wilson2017GoodEnough`, `FellegiSunter1969`, `Christen2012DataMatching`. Optional additions: `LittleRubin2019`, `Pedregosa2011Sklearn`. Does the user prefer minimalism (3) or fuller citation coverage (5)? Recommended default: 3; add optional only if Pass 2 demands.
4. **Q4 for user — CONSORT/STROBE/RECORD convention.** §4.1 tables use "CONSORT-style". §4.2.3's Tabela 4.6 typology is NOT a CONSORT flow — it's a rule-classification matrix, so the label does not apply. Should we add a footnote in §4.2.3 flagging this distinction? Recommended default: yes, one-sentence footnote.
5. **Q5 for user — halt protocol.** §4.1 had 3-round plan-side adversarial + 3-round execution-side adversarial. Based on plan complexity, §4.2 is smaller but richer in argumentation. Expected: 2-round plan-side + 2-round execution-side. Cap at 3-3 per `feedback_adversarial_cap_execution.md` symmetric rule. Recommended default: 2+2 with cap at 3+3 if substantive BLOCKERs surface.
6. **Q6 for user — whether the plan should include §4.2 being followed immediately by §4.4.4 (Evaluation metrics, literature-fed, DRAFTABLE).** §4.4.4 is independent of §4.2 and could be a sibling F-session. Not part of this plan's scope; flag only.

---

## Adversarial-defence rehearsal (per-subsection, top 3 likely BLOCKERs)

### §4.2.1 Ingestion i walidacja

**BLOCKER 1 — "Scope creep: §4.2.1 re-narrates §4.1 ingestion numbers."**
Pre-emption: The "Scope-overlap with §4.1" table in `sec_4_2_crosswalk.md` flags every overlap explicitly. §4.2.1 reuses file counts / row counts only to frame a **decision** (e.g., 367 GB estimated event-array size → split-table strategy), not as standalone corpus description. Close with forward-ref to §4.1 Tabela 4.1 / 4.2 / 4.3.

**BLOCKER 2 — "DuckDB justification is implementation, not methodology."**
Pre-emption: Keep DuckDB-justification paragraphs ≤3 sentences each; frame them as reproducibility (I6) + embedded-process (I9-adjacent) arguments, cite `Wilson2017GoodEnough`. Explicitly acknowledge: "Wybór DuckDB nie jest kontrybucją metodologiczną — jest konsekwencją wymagań reprodukowalności."

**BLOCKER 3 — "I10 research_log narrative is historic process noise, not thesis-level."**
Pre-emption: Keep the I10 narrative to ~2 sentences total. Cite the protocol decision (inline CTAS) as an I10 example without dwelling on the OOM-failure history. Flag `[REVIEW]` for Pass 2 to decide whether to strip further.

### §4.2.2 Rozpoznanie tożsamości gracza

**BLOCKER 1 — "Multi-account interpretation of toon_id/nickname ratios is speculation without evidence."**
Pre-emption: Every ratio is accompanied by "sugeruje" / "jest spójne z" hedging, never "dowodzi" / "wynika". Forward-ref to §4.3.1 where the multi-toon classification (server-switch / rename / ambiguous) is OPERATIONALIZED, not just observed. `[REVIEW]` flag on the interpretation.

**BLOCKER 2 — "Fellegi-Sunter citation is gratuitous — we're not doing record linkage."**
Pre-emption: The framing of why we DO NOT need record linkage is explicitly argued — trust-the-ID posture — with Christen 2012 cited as the canonical textbook that formally defines the problem class we explicitly do not solve. Hedge: "Zagadnienie [FellegiSunter1969] / [Christen2012DataMatching] pozostaje referencyjne, nie operacyjne". This turns a gratuitous cite into a justified non-use.

**BLOCKER 3 — "Deferral to Phase 02 is an admission of non-work."**
Pre-emption: The deferral is justified by I9 (raw immutability at Phase 01) and the operational definition of I2 (nickname canonical at feature time, not raw time). §4.2.2 is not deferring work — it is CLASSIFYING the problem and committing to the classification boundary.

### §4.2.3 Reguły czyszczenia i ważny korpus

**BLOCKER 1 — "MissingIndicator is a cop-out for not doing imputation; flag it as incomplete Phase 01 work."**
Pre-emption: Explicit closing defence paragraph argues I3-compliance. Structure: (a) Phase 01 is fold-agnostic → (b) any imputation at Phase 01 leaks future-fold distributional info → (c) Phase 02 fold-aware imputation preserves I3 → (d) MissingIndicator losslessly preserves the missingness signal for Phase 02 to consume → (e) therefore MissingIndicator is the ONLY I3-compliant Phase 01 posture. Cite `Rubin1976`, `vanBuuren2018`, and the I3 normalization-leakage clause verbatim.

**BLOCKER 2 — "5% / 40% / 80% thresholds are magic numbers (I7 violation)."**
Pre-emption: Every threshold carries an inline citation to `SchaferGraham2002` (5%) or `vanBuuren2018` (40% / 80%). The closing paragraph explicitly addresses I7 compliance: "Stałe progowe 5%, 40% i 80% są cytowane operacyjnie z literatury — nie są magic numbers w rozumieniu I7."

**BLOCKER 3 — "MAR classification for MMR is wrong; should be MNAR, and that changes the routing."**
Pre-emption: Explicit hedging in the MMR paragraph: "Klasyfikacja MAR pochodzi z ledgera `01_04_01` i opiera się na argumentie, że missingness zależy od obserwowalnego atrybutu (typ konta turniejowego). Alternatywna interpretacja MNAR byłaby zgodna z nieobserwowalnym 'nieuczestniczeniem gracza w ladderze' jako ukrytą zmienną. [REVIEW: MAR vs MNAR]". If Pass 2 reclassifies to MNAR, the routing (DROP_COLUMN + flag) DOES NOT CHANGE — both MAR and MNAR at ≥80% route to DROP per van Buuren. The flag `is_mmr_missing` preserves the signal in both interpretations. This is the key defensive insight: the MAR/MNAR dispute does not invalidate the cleaning decision.

---

## Halt protocol

Mirrors the §4.1 halt protocol exactly (see `thesis/pass2_evidence/sec_4_1_halt_log.md`):

- **Per-task halt predicate:** during T02/T03/T04, if a number cannot be anchored to an artifact within 5 lookups, the draft halts and plants `[UNVERIFIED: <claim>]` inline.
- **Aggregate halt predicate:** if >5 `[UNVERIFIED]` flags accumulate across a single subsection, halt the subsection and surface the un-anchored claims to the user in a chat handoff before continuing.
- **Logging:** every halt event appended to `thesis/pass2_evidence/sec_4_2_halt_log.md` with task ID + claim + resolution. Zero-halt drafts attest zero events explicitly (per §4.1 precedent).

---

## Execution ordering and risk summary

| Task | Char budget | Risk | Depends on |
|---|---|---|---|
| T01 Crosswalk | 6–10k (Markdown) | Low | — |
| T02 §4.2.1 draft | 5–7k (Polish prose) | Medium | T01 |
| T03 §4.2.2 draft | 5–7k (Polish prose) | Medium-High | T01 |
| T04 §4.2.3 draft | 8–10k (Polish prose) | High | T01 |
| T05 Integration | — (metadata) | Low | T02, T03, T04 |
| T06 Polish | — (edits) | Low | T05 |

**Total §4.2 character budget: 18–24k Polish characters.** (Target from user: 18–22k. Upper bound 24k with some slack for polish pass adjustments.)

---

## Critical self-check (per planner_output_contract)

- [x] `category` is F
- [x] Execution Steps tasks are sequential T01–T06
- [x] File Manifest lists every file any task touches
- [x] No forbidden taxonomy terms used as work-unit names ("Section" used only in "thesis section", "Pipeline Section")
- [x] `invariants_touched` populated: [I3, I5, I6, I7, I8, I9, I10]
- [x] Category F → critique instruction: **after producing this plan, the parent must dispatch reviewer-adversarial to produce `planning/current_plan.critique.md` covering all sections (Scope, Problem Statement, Assumptions, Literature context, Execution Steps, File Manifest, Gate Condition, Out of scope, Open questions). Do NOT begin execution (T01) until the critique is resolved.**

---

## Critique instruction (Category F — mandatory)

**For Category F, adversarial critique is required before execution. Dispatch reviewer-adversarial to produce `planning/current_plan.critique.md` before any of T01–T06 runs.** The symmetric 3-round cap applies to both plan-side critique (up to 3 BLOCKER/revision rounds) and execution-side critique (up to 3 rounds after T04 drafting). Target verdict: `READY_FOR_EXECUTION` after ≤2 rounds; escalate to user if round 3 still yields BLOCKER.

---

Sources:
- [A Theory for Record Linkage — Fellegi & Sunter 1969](https://www.tandfonline.com/doi/abs/10.1080/01621459.1969.10501049)
- [Data Matching: Concepts and Techniques — Christen 2012](https://link.springer.com/book/10.1007/978-3-642-31164-2)
- [Statistical Analysis with Missing Data, 3rd ed. — Little & Rubin 2019](https://onlinelibrary.wiley.com/doi/book/10.1002/9781119482260)
- [Scikit-learn: Machine Learning in Python — Pedregosa et al. 2011](https://jmlr.org/papers/volume12/pedregosa11a/pedregosa11a.pdf)
- [Good Enough Practices in Scientific Computing — Wilson et al. 2017](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005510)
- [STROBE statement (2007)](https://pmc.ncbi.nlm.nih.gov/articles/PMC2636253/)
- [CONSORT 2010](https://en.wikipedia.org/wiki/Consolidated_Standards_of_Reporting_Trials)
- [RECORD statement (2015)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4595218/)
- [Apache Arrow / Parquet documentation](https://arrow.apache.org/docs/python/parquet.html)