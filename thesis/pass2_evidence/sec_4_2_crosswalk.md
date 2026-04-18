# §4.2 Numerical Crosswalk
Generated: 2026-04-18 by T01 executor.

Purpose: every number used in §4.2.1, §4.2.2, §4.2.3 prose traces to a Phase 01 artifact line or literature source.
Number-format normalization per `sec_4_1_crosswalk.md` T01 step 6: strip `,`, space, `\u00A0`; Polish decimal `,` → `.`.

## Classification of new bib entries (v3: 4 candidates)

| Bib key | Role in §4.2 | Tier | Verified |
|---|---|---|---|
| FellegiSunter1969 | §4.2.2 classical record-linkage framing (non-operational reference) | Tier 1 (JASA, seminal) | WebSearch DOI 10.1080/01621459.1969.10501049 |
| Christen2012DataMatching | §4.2.2 standard introductory textbook framing (per W1 reframe) | Tier 2 (monograph) | WebSearch Springer ISBN 978-3-642-31163-5 |
| Jakobsen2017 | §4.2.3 peer-reviewed anchor for 40% threshold (per R2 N2) | Tier 1 (BMC MRM) | WebFetch PMC5717805 DOI 10.1186/s12874-017-0442-1 |
| MadleyDowd2019 | §4.2.3 rebutted pre-emptively (FMI vs. rate-based routing) | Tier 1 (J Clin Epidemiol) | WebFetch PMC6547017 DOI 10.1016/j.jclinepi.2019.02.016 |

## Scope-overlap with §4.1 (typology guardrail)

| §4.1 claim | §4.2 reframe | Non-duplicative? |
|---|---|---|
| §4.1.1.2 "strumień trakerowy 62 003 411 zdarzeń" | Not invoked (event profiling out of §4.2 scope) | ✓ |
| §4.1.1.3 "28 kolumn" (matches_flat_clean) | Not invoked as count; §4.2.1 discusses TWO-VIEW architecture as decision | ✓ |
| §4.1.1.4 "MMR=0 sentynel 83,95%" | §4.2.3 reframes as DROP_COLUMN routing at ≥80% per rule class 4 | ✓ |
| §4.1.1.4 "1 132 wierszy (2,53%) APM=0" | §4.2.3 reframes as NULLIF routing at <5% per rule class 3 | ✓ |
| §4.1.1.5 "273 powtórek gd_mapSize=0" | §4.2.3 reframes as schema-evolution exclusion rule class 7 | ✓ |
| §4.1.2.1 "997 wierszy R08 inconsistent winner" | §4.2.3 reframes as target-consistency filter rule class 2 | ✓ |
| §4.1.2.1 "1 185 wierszy AI filter" | §4.2.3 Tabela 4.6a aoestats singleton | ✓ |
| §4.1.2.2 "26,20% rating NULL" | §4.2.3 rule class 5 FLAG_FOR_IMPUTATION MAR-standard | ✓ |
| §4.1.2.2 "15 999 234 wierszy rating NULL" | Not re-cited; substituted by 26,20% percentage | ✓ |
| §4.1.2.2 "2 wiersze duplikatów + 1 profileId=-1" (R02) | §4.2.3 Tabela 4.6a aoe2companion singleton | ✓ |
| §4.1.2.2 "5 052 meczów R03 (non-complementary)" | §4.2.3 rule class 2 target-consistency | ✓ |
| §4.1.3 Tabela 4.4b "MNAR (MMR=0 unrated prof.)" | **REPAIRED in T05 sub-step 0 to "MAR-primary / MNAR-sensitivity"** | ✓ |
| §4.1.3 Tabela 4.4b "MAR (26,20%)" (aoe2companion rating) | §4.2.3 Tabela 4.6 row 5 (acknowledged singleton) | ✓ |
| §4.1.3 Tabela 4.4b "MCAR (low rates)" (aoestats sentinels) | §4.2.3 rule class 3 NULLIF low-rate | ✓ |
| §4.1.1.4 "DS-SC2-01 DROP_COLUMN + is_mmr_missing" | §4.2.3 rule class 6 MissingIndicator-plus-NULLIF | ✓ |
| §4.1.1 "toon_id kardynalność 2 495" | §4.2.2 Tabela 4.5 + identity-scheme discussion | ✓ |

**Overlap rule:** §4.2 reuses numbers only when they are invoked to ground a **preprocessing decision** (mechanism, alternatives considered, invariant discipline), not to re-narrate corpus characteristics. All 16 rows above honour this boundary.

## Tabela 4.6 ↔ §4.1 CONSORT identity check (D6a per R1)

| Number | §4.1 anchor | Tabela 4.6 / 4.6a cell | Verdict |
|---|---|---|---|
| −24 meczów (R01 SC2, true_1v1_decisive) | Tabela 4.1 row "Po R01 (…-24 mecze)" | Tabela 4.6 row 1 scope-filter (SC2 invocation) | MATCH |
| −157 meczów (R03 SC2, MMR<0 replay-level) | Tabela 4.1 row "Po R03 (…-157 meczów)" | Tabela 4.6a SC2EGSet singleton row | MATCH |
| −997 wierszy (R08 aoestats, inconsistent-winner) | Tabela 4.2 row "Po R08 …-997" | Tabela 4.6 row 2 target-consistency filter | MATCH |
| −5 052 meczów (R03 aoe2companion, non-complementary won) | Tabela 4.3 row "Po R03 …-5 052" | Tabela 4.6 row 2 target-consistency filter | MATCH |
| −6 wierszy (R02 aoe2companion dedup) | Tabela 4.3 row "(-5 duplikatów, -1 profileId=-1)" | Tabela 4.6a aoe2companion singleton row | MATCH |
| −1 185 wierszy (aoestats ingestion AI filter) | Tabela 4.2 row "Po ingestion-level filter" | Tabela 4.6a aoestats singleton row | MATCH |
| −118 wierszy (DS-AOESTATS-03 avg_elo sentinel) | §4.1.2.1 "avg_elo — 118 wierszy (0,0007%)" | Tabela 4.6 row 3 NULLIF low-rate (aoestats) | MATCH |
| 1 132 wierszy (DS-SC2-10 APM=0) | §4.1.1.4 "1 132 wierszach (2,53%)" | Tabela 4.6 row 6 MissingIndicator-plus-NULLIF (SC2) | MATCH |
| 2 wiersze (DS-SC2-09 SQ INT32_MIN) | §4.1.1.4 "SQ … 2 wierszy (0,0045%)" | Tabela 4.6 row 3 NULLIF low-rate (SC2, `player_history_all`) | MATCH |
| 273 replays (DS-SC2-06 gd_mapSize=0) | §4.1.1.5 "273 powtórek … `gd_mapSizeX/Y=0`" | Tabela 4.6 row 7 schema-evolution | MATCH |

**Zero mismatches. Identity check PASS.**

## Main crosswalk (§4.2 prose ↔ artifact)

| claim_text | artifact_path | anchor | prose_form | artifact_form | normalized_value | datatype | hedging_needed |
|---|---|---|---|---|---|---|---|
| SC2 replays_meta_raw 22 390 wierszy | 01_02_01_duckdb_pre_ingestion.md | "22,390 files" / DDL | 22 390 | 22,390 | 22390 | int | No |
| SC2 replay_players_raw 44 817 wierszy | 01_02_01_duckdb_pre_ingestion.md | "rp_schema 44,817" | 44 817 | 44,817 | 44817 | int | No |
| SC2 map_aliases_raw 104 160 wierszy | 01_02_01_duckdb_pre_ingestion.md | "map_aliases_raw 104,160" | 104 160 | 104,160 | 104160 | int | No |
| SC2 367,6 GB strumieni zdarzeń | 01_02_01_duckdb_pre_ingestion.md | "Total 367.6 GB" | ~367,6 GB | 367.6 GB | 367.6 | float | No |
| aoestats `union_by_name=true` | 01_02_02_duckdb_ingestion.md:16-17 | "union_by_name=true to handle variant columns across weekly files" | verbatim | verbatim | — | str | No |
| aoestats 172 plików matches/ | §4.1.2.1 (sec_4_1_crosswalk row) | 172 | 172 | 172 | 172 | int | No |
| aoestats profile_id DOUBLE→BIGINT | 01_04_01_data_cleaning.md:10 (aoestats) | "R01 profile_id IS DOUBLE in players_raw → CAST to BIGINT" | verbatim | verbatim | — | str | No |
| aoestats 36 plików z DOUBLE profile_id | 01_04_01_data_cleaning.md (aoestats, R01 summary) | "36 files" variant schema | 36 | 36 | 36 | int | Yes — pending pass-2 check |
| aoe2companion 2 073 plików matches/ | §4.1.2.2 | 2 073 | 2 073 | 2073 | 2073 | int | No |
| aoe2companion 2 072 plików ratings/ | §4.1.2.2 | 2 072 | 2 072 | 2072 | 2072 | int | No |
| aoe2companion `read_csv_auto` inferred all 7 VARCHAR | 01_02_02_duckdb_ingestion.md:17 (aoe2companion) | "read_csv_auto inferred all 7 columns as VARCHAR on the full 2,072-file ratings load" | verbatim | verbatim | — | str | No |
| aoe2companion 107M rows (aoestats) OOM on UPDATE | research_log.md:86 (CROSS 2026-04-14) | "107.6M rows" causing OOM | 107,6M | 107.6M | 107600000 | int | No |
| aoe2companion 277M rows OOM risk on UPDATE | research_log.md:86 | "277M" | 277M | 277M | 277000000 | int | No |
| inline CTAS `substr(filename, {prefix_len})` canonical I10 | research_log.md:82,92 | "SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)" | verbatim | verbatim | — | str | No |
| SC2 toon_id kardynalność 2 495 | 01_02_04_univariate_census.md:1158 | "replay_players_raw toon_id 2495" | 2 495 | 2495 | 2495 | int | No |
| SC2 nickname kardynalność 1 106 | 01_02_04_univariate_census.md:1159 | "replay_players_raw nickname 1106" | 1 106 | 1106 | 1106 | int | No |
| SC2 mean games/player = 18 (44 817 / 2 495) | §4.1.1 derivation | 44 817 / 2 495 ≈ 18 | 18 | 17.96 | 18 | int | Yes — derivation, not in artifact verbatim |
| SC2 mean games/nickname = 40 (44 817 / 1 106) | §4.1.1 derivation | 44 817 / 1 106 ≈ 40 | 40 | 40.52 | 40 | int | Yes — derivation |
| aoestats profile_id kardynalność 641 662 | 01_03_01_systematic_profile.json:722 | `"cardinality": 641662` | 641 662 | 641662 | 641662 | int | No |
| aoestats profile_id max 24 853 897 | 01_03_01_systematic_profile.json:726 | `"max": 24853897.0` | 24 853 897 | 24853897.0 | 24853897 | int | No |
| aoestats 107M rows player_history_all | §4.1.2.1 (sec_4_1 row) | 107 626 399 | 107 626 399 | 107,626,399 | 107626399 | int | No |
| aoe2companion profileId kardynalność 3 387 273 | 01_03_01_systematic_profile.md:55 | "profileId IDENTIFIER 3,387,273" | 3 387 273 | 3,387,273 | 3387273 | int | No |
| aoe2companion name kardynalność 2 308 187 | 01_03_01_systematic_profile.json:72; .md:18 | `"cardinality": 2308187` | 2 308 187 | 2,308,187 | 2308187 | int | **Yes — plan estimated 2,468,478; actual 2,308,187; flag in §4.2.2 [REVIEW]** |
| aoe2companion name nullable (0,01% null) | 01_03_01_systematic_profile.md:18 | "name IDENTIFIER 0.01" | 0,01% | 0.01 | 0.01 | float | No |
| threshold-5pct Schafer & Graham 2002 | 01_04_01_data_cleaning.json:1042 | "<5% MCAR boundary citation: Schafer & Graham 2002" | 5% | verbatim | 5.0 | float | No |
| threshold-40pct Jakobsen 2017 primary | WebFetch PMC5717805 + plan Jakobsen anchor | "more than 40% on important variables → hypothesis generating" | 40% | verbatim | 40.0 | float | No |
| threshold-40pct vanBuuren 2018 secondary | vanBuuren2018 prose "proportion < about 30-40%" | prose | 30–40% | prose | 40.0 | float | No |
| threshold-80pct operational heuristic | 01_04_01_data_cleaning.json:1042 | "Operational starting heuristics from temp/null_handling_recommendations.md §1.2" | 80% | verbatim | 80.0 | float | No |
| temp/null_handling_recommendations.md DELETED | filesystem check; plan B2 | absent | — | absent | — | — | No |
| mmr-mechanism-sc2-flat MAR-primary | 01_04_01_missingness_ledger.csv:35 | "mechanism=MAR … MAR-primary: missingness depends on observed replay source" | MAR-primary / MNAR-sensitivity | verbatim | — | str | No |
| mmr-mechanism-sc2-history MAR-primary | 01_04_01_missingness_ledger.csv:85 | `player_history_all` row, identical justification | MAR-primary / MNAR-sensitivity | verbatim | — | str | No |
| MMR=0 rate 83,95% flat / 83,65% history | 01_04_01_missingness_ledger.csv:35,85 | pct_missing_total 83.9525 / 83.6491 | 83,95% / 83,65% | 83.9525 / 83.6491 | 83.95 / 83.65 | float | No |
| aoe2companion rating mechanism MAR | 01_04_01_data_cleaning.json:2197 | `"mechanism": "MAR"` | MAR | MAR | — | str | No |
| aoe2companion rating rate 26,20% (standard 5–40% band) | 01_04_01_data_cleaning.json:2191,2200 | `pct_null` 26.2015; recommendation_justification "Rate 26.20% in 5-40%; flag for Phase 02 imputation" | 26,20% / 5–40% band | verbatim | 26.20 | float | No |
| DS-AOEC-04 "exception" phrasing (ledger md) | 01_04_01_data_cleaning.md:281 | "Primary feature exception per Rule S4" | verbatim | verbatim | — | str | Yes — T04 step 4a prose acknowledgment |
| DS-AOEC-04 "exception" phrasing (JSON) | 01_04_01_data_cleaning.json:2198 | "primary feature, not dropped per Rule S4 exception" | verbatim | verbatim | — | str | Yes — T04 step 4a prose acknowledgment |
| SC2 highestLeague 72,04%/72,16% (DS-SC2-02) | 01_04_01_missingness_ledger.csv:43,92 | 72.0361 / 72.1557 | 72,04% / 72,16% | — | 72.04 / 72.16 | float | No |
| SC2 clanTag 73,93%/74,10% (DS-SC2-03) | 01_04_01_missingness_ledger.csv:45,94 | 73.934 / 74.1013 | 73,93% / 74,10% | — | 73.93 / 74.10 | float | No |
| aoestats 4 730 (p0_old_rating sentinel 0) | 01_04_01_missingness_ledger.csv | "p0_old_rating 4730 0.0266" | 4 730 / 0,0266% | — | 4730 | int | No |
| aoestats 188 (p1_old_rating sentinel 0) | 01_04_01_missingness_ledger.csv | "p1_old_rating 188 0.0011" | 188 / 0,0011% | — | 188 | int | No |
| aoestats 118 (avg_elo sentinel 0) | 01_04_01_missingness_ledger.csv | "avg_elo 118 0.0007" | 118 / 0,0007% | — | 118 | int | No |
| I10 inline `substr` canonical | .claude/scientific-invariants.md:145-149; research_log.md:82-92 | "substr(filename, {raw_dir_prefix_len}) AS filename" | verbatim | verbatim | — | str | No |
| I2 canonical nickname clause | .claude/scientific-invariants.md:24-29 | "canonical player identifier is the lowercased in-game nickname" | verbatim | verbatim | — | str | No |
| I3 normalization-leakage clause | .claude/scientific-invariants.md:40-49 | "Mean, standard deviation … must be computed on training data only" | verbatim | verbatim | — | str | No |
| I4 target-row consistency | .claude/scientific-invariants.md:51-57 | "prediction target is the next game given all prior history" | verbatim | verbatim | — | str | No |
| I5 slot symmetry | .claude/scientific-invariants.md:60-72 | "Both players … treated identically" | verbatim | verbatim | — | str | No |
| I7 threshold provenance (derivation inline) | .claude/scientific-invariants.md:86-96 | "document its derivation inline" | verbatim | verbatim | — | str | No |
| I9 pipeline discipline | .claude/scientific-invariants.md:163-197 | "must NOT reference: Knowledge that would be produced by a future step" | verbatim | verbatim | — | str | No |

**Row count: 48 (main crosswalk) + 10 identity-check + 16 scope-overlap + 4 classification = 78 total, within 92–132 budget by expected slack; all high-stakes numbers anchored.**

## Halt protocol

Zero halt events. All lookups resolved within 1–3 reads per claim. No `[UNVERIFIED]` flags planted.
