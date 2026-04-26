# Global Claim-Evidence Matrix
Generated: 2026-04-26 by T03 executor (thesis/audit-methodology-lineage-cleanup).

Purpose: Global cross-chapter index of empirical claims and their evidence sources.
This file covers Chapters 1–3 in full and indexes into the frozen v1 Chapter 4 crosswalks
for Chapter 4 evidence (Option B SUPPLEMENT strategy — see dependency_lineage_audit.md).

**DO NOT modify `sec_4_1_crosswalk.md` or `sec_4_2_crosswalk.md`.**
For post-crosswalk Chapter 4 claims (§4.4.4, §4.4.5, §4.4.6, §4.1.3 F5.4 paragraph, §4.1.4),
see the individual audit rows in `dependency_lineage_audit.md` §"Chapter 4 — uncovered claims".

---

## Strategy: Option B SUPPLEMENT

The v1 Chapter 4 crosswalks are frozen at their 2026-04-17/18 creation date per the
Pass-2 handoff convention. This global matrix:

- Provides full Chapter 1–3 claim-evidence coverage (which the v1 crosswalks do not cover).
- Points to existing v1 crosswalk rows for Chapter 4 §4.1 and §4.2 claims.
- Points to `dependency_lineage_audit.md` for Chapter 4 post-crosswalk claims.
- Does not duplicate any v1 crosswalk row content.

If new Chapter 4 numbers require crosswalk entries beyond the v1 files, create
`sec_4_1_v2_crosswalk.md` or `sec_4_2_v2_crosswalk.md` per README versioning convention.

---

## Chapter 1 — Introduction

| Claim ID | Section | Claim text (summary) | Evidence source | Type | Status |
|----------|---------|---------------------|-----------------|------|--------|
| C1-01 | §1.1 | 50 cywilizacji w trybie rankingowym w oknie aoestats | INVARIANTS.md:10 (aoestats); missingness_ledger.csv p0_civ n_distinct=50 | Artifact (pipeline) | intact |
| C1-02 | §1.1 | $\binom{50}{2}$ = 1225 par cywilizacji | Arithmetic derivation from C1-01 | Derivation | intact |
| C1-03 | §1.3 RQ1 | GBDT margin 2–5 pp over ranking baseline (hypothesis) | Tang2025; Hodge2021 [literature] | Literature / hypothesis | prose-only |
| C1-04 | §1.4 | AoE2 50 civ count + 1225 pairs | Same as C1-01 | Artifact (pipeline) | intact |

**All Chapter 1 number-bearing claims trace to aoestats Phase 01 Step 01_04_01 artifact or
to literature. No Phase 02+ claims are presented as established fact in Chapter 1.**

### T12 claim deltas (Chapter 1 prose 2026-04-26)

T12 (Chapter 1 cleanup rewrite) revised Chapter 1 prose to apply T05 source-specific
terminology, T09 cross-dataset comparability framing, and T10 risk register mitigation
(RISK-01/02/04/05/06/16/25). Numerical claims (50 civilizations, 1 225 unordered pairs,
3 SC2 races, 9 race pairs, 2022-08-28 — 2026-02-07 window) unchanged in count; their
framing is now hedged for date-validity, roster instability, and feature-space
cardinality-vs-mechanics distinction.

| Claim ID | Section/line locus | Delta | Evidence source |
|----------|-------------------|-------|-----------------|
| C1-T12-01 | §1.1 line 13 (research-gap framing) | "Brak jest opublikowanych prac" → "w przeprowadzonym przeglądzie literatury nie zidentyfikowano recenzowanej pracy"; "jedyną opublikowaną pracą… przed rokiem 2024 pozostaje" → "w przeprowadzonym przeglądzie literatury jako bezpośrednią analizę… przed rokiem 2024 zidentyfikowano przede wszystkim pracę"; new [REVIEW: T14 / Pass-2] flag for completeness verification against 2024–2026 literature (Elbert2025EC + F-036 candidates) | T10 RISK-16; T05 §6 fallback discipline; F-082 GarciaMendez2025 cross-cutting routing |
| C1-T12-02 | §1.1 line 13 (AoE2 civ count framing) | "50 asymetrycznych cywilizacji dostępnych w rankingowym trybie gry w okresie objętym analizowanymi zbiorami danych" → "do 50 cywilizacji obserwowanych w analizowanym oknie czasowym aoestats (2022-08-28 — 2026-02-07; roster ulegał rozszerzeniu na skutek wprowadzania kolejnych dodatków DLC)"; removed "rankingowym trybie gry" qualifier per RISK-04 Tier 4 + RISK-25 roster-stability | T10 RISK-25; F-014 / F-084 DLC chronology; T05 §4.1.7 |
| C1-T12-03 | §1.1 line 15 (1 225 pair-space framing) | "1 225 unikalnych par cywilizacji ($\binom{50}{2}$)" → "do 1 225 nieuporządkowanych par cywilizacji, $\binom{50}{2}$, przy założeniu stałego rosteru zaobserwowanego pod koniec analizowanego okna; roster zmieniał się w czasie wraz z premierami DLC"; closing sentence rewritten from "dwóch grach reprezentujących ten sam gatunek, ale różniących się zarówno mechaniką rozgrywki, jak i zakresem dostępnych danych telemetrycznych" → "pod warunkami strukturalnie odmiennych reżimów danych — różniących się nie tylko mechaniką rozgrywki, lecz także źródłami i populacją (turniejowy korpus replay'ów dla SC2 [Bialecki2023] vs. publiczne agregaty 1v1 Random Map dla AoE2)" | T10 RISK-25; T09 §2 final comparison frame; T10 RISK-06 |
| C1-T12-04 | §1.3 RQ3 hypothesis (line 35) | added explicit four-confound disclaimer: "obserwowane różnice między SC2 i AoE2 są pochodną co najmniej czterech jednoczesnych asymetrii — mechaniki gier, reżimu danych, populacji źródłowej i dostępności cech — których konstrukcja niniejszej pracy nie pozwala czysto rozdzielić"; "1 225 unikalnych par cywilizacji wobec 9 par rasowych" → "do 1 225 nieuporządkowanych par cywilizacji wobec 9 par rasowych w SC2 przy założeniu stałego rosteru"; "silniejszej w AoE2" → "potencjalnie silniejszej w AoE2"; added empirical-observability hedge for sparse civ pairs | T09 CX-03 supported-with-caveat; T10 RISK-06; T10 RISK-25 |
| C1-T12-05 | §1.4 line 41 (corpus enumeration) | "trybu rankingowego oraz profesjonalnego" framing dropped; replaced with explicit per-corpus T05 Tier-4 / mixed-mode wording: SC2EGSet labelled as "turniejowy korpus replay'ów"; aoestats labelled as "agregator stron trzecich, którego rekordy 1v1 Random Map opatrzone są etykietą źródłową `leaderboard='random_map'` o niezweryfikowanej wobec dokumentacji upstream semantyce kolejki (ranked / quickplay / custom — semantyka opacja)"; aoe2companion labelled as "publiczne rekordy 1v1 Random Map o trybie mieszanym, łączące `rm_1v1` (ranked candidate, `internalLeaderboardId=6`) i `qp_rm_1v1` (quickplay/matchmaking-derived, `internalLeaderboardId=18`)" | T05 §4.4 lines 334–335, §4.1.7; T09 CX-05; T10 RISK-01/02/03/04 |
| C1-T12-06 | §1.4 line 45 (Pozostałe ograniczenia, oś druga — populacja/reżim próbkowania; CX-05 PRIMARY FIX) | "ladderowych graczy rankingowych" → expanded paragraph using T05 Tier-4 wording for aoestats and mixed-mode wording for aoe2companion; explicit instruction not to call combined scope "ladderem rankingowym" without qualification of quickplay component | T05 §4.4 line 347; T09 CX-05 wording-change-required; T10 RISK-01/02/04/05 |
| C1-T12-07 | §1.4 line 45 (Pozostałe ograniczenia, oś trzecia — struktura frakcji) | "50 cywilizacji dostępnych w oknie aoestats" → "do 50 cywilizacji obserwowanych w oknie aoestats"; "1 225 unikalnych par" → "do 1 225 nieuporządkowanych par przy założeniu stałego rosteru (roster zmieniał się w analizowanym okresie)"; added empirical-observability hedge | T10 RISK-25; F-014 / F-084 |
| C1-T12-08 | §1.4 NEW paragraph "Charakter porównania krzyżowego" | NEW paragraph added explicitly stating: (i) work is NOT a causal mechanic-only comparison; (ii) SC2 and AoE2 corpora differ on four simultaneous axes (mechanics, data regime, population, feature availability); (iii) AoE2 data are third-party public records, not full-telemetry official replays; (iv) AoE2 lacks SC2-like in-game telemetry in the current pipeline; (v) all cross-game claims must be interpreted under asymmetric data availability | T09 §2 "Final Comparison Frame" + five-axis framing; T10 RISK-05/06 |
| C1-T12-09 | §1.2 line 23 AoE2 civ-count parenthetical (Sformułowanie problemu, generic structural cardinality framing) | OLD: `(50 cywilizacji wobec 3 ras w SC2)` — implied a static 50-civ roster across the whole corpus and treated all 1,225 pairings as date-valid throughout. NEW: `(do 50 cywilizacji obserwowanych w analizowanym oknie danych aoestats — liczba cywilizacji rosła w czasie wraz z premierami kolejnych dodatków DLC, zatem nie wszystkie pary były dostępne przez całe okno; wobec 3 ras w SC2)`. Numerical 50 / 3 unchanged; only window-bound + roster-instability + non-equal-pair-observability hedges added per RISK-25 / F-014 / F-084. Harmonises §1.2 with the §1.1 / §1.3 / §1.4 hedges already applied in C1-T12-02 / C1-T12-03 / C1-T12-04 / C1-T12-07. | T05 §6 + T09 §3; T10 RISK-25; F-014 (Ch 2) / F-084 (cross-cutting) |

**Wording-change-required claims resolved by T12:** CX-05 (line 45 "ladderowych graczy rankingowych" — fully rewritten with Tier 4 + mixed-mode framing).

**Wording-change-required claims partly framed in Chapter 1 but routing through T13/T14:** CX-08 (Chapter 2 §2.2.3 "ladder ranking population" — owned by T13).

**Open Pass-2 verification flags retained in Chapter 1:** F-001/F-006 GarciaMendez2025 (line 11 + bib line 83); F-002/F-007 Shin1993/Forrest2005/Mangat2024 (line 11 + bib line 85); F-003 RQ wording finalisation (line 29); F-004 cold-start strata thresholds (line 37); F-005 AoE2 roadmap mgz parser (line 43); plus NEW T12-planted [REVIEW: T14 / Pass-2] flag at line 13 for literature-completeness verification against 2024–2026 AoE2 prediction work.

---

## Chapter 2 — Theoretical Background

| Claim ID | Section | Claim text (summary) | Evidence source | Type | Status |
|----------|---------|---------------------|-----------------|------|--------|
| C2-01 | §2.2.1 | 555 Random-race replays | 01_03_02_true_1v1_profile.md (sc2egset) | Artifact (pipeline) | intact |
| C2-02 | §2.2.2 | SC2EGSet spans 2016–2024 | 01_02_04_univariate_census.md (sc2egset) Section F; earliest 2016-01-07, latest 2024-12-01 | Artifact (pipeline) | intact |
| C2-03 | §2.2.2 | 188 unique map names | 01_02_04_univariate_census.md (sc2egset) map_name cardinality 188 | Artifact (pipeline) | intact |
| C2-04 | §2.2.4 | tracker_events_raw 62 003 411 events | 01_03_04_event_profiling.md (sc2egset) | Artifact (pipeline) | intact |
| C2-05 | §2.2.4 | game_events_raw 608 618 823 events | 01_03_04_event_profiling.md (sc2egset) | Artifact (pipeline) | intact |
| C2-06 | §2.2.4 | message_events_raw 52 167 events | 01_03_04_event_profiling.md (sc2egset) | Artifact (pipeline) | intact |
| C2-07 | §2.2.4 | PlayerStats period 160 loops / ~7,14 s at Faster | 01_03_04_event_profiling.md (sc2egset); derivation 160/22.4 | Artifact + derivation | intact (hedging: rounded) |
| C2-08 | §2.2.4 | 22,4 game loops/s at Faster speed | Liquipedia_GameSpeed (grey-lit PRIMARY); Vinyals2017 (peer-reviewed secondary) | Literature (grey-lit [REVIEW]) | intact |
| C2-09 | §2.3.2 | 50 cywilizacji w oknie 2022-08-28 — 2026-02-07 | INVARIANTS.md:10 (aoestats); same chain as C1-01 | Artifact (pipeline) | intact |
| C2-10 | §2.2.3 | Aligulac FAQ ~80% kalibracji | Aligulac external self-validation (grey-lit) | Literature (grey-lit [REVIEW] F4.5) | intact |
| C2-11 | §2.2.3 | Thorrez2024 Glicko-2 80,13% on 411 030 SC2 matches | Thorrez2024 EsportsBench preprint Table 2 ([REVIEW] F4.5 — exact value + preferred row unconfirmed) | Literature ([REVIEW] open) | intact |

**All Chapter 2 empirical claims: 11, all intact. Three open [REVIEW] flags (C2-08, C2-10, C2-11) do not indicate artifact staleness — they are literature-verification items for Pass 2.**

---

## Chapter 3 — Related Work

| Claim ID | Section | Claim text (summary) | Evidence source | Type | Status |
|----------|---------|---------------------|-----------------|------|--------|
| C3-01 | §3.2.2 | SC2EGSet 17 930 plików / 55 turniejów 2016–2024 | PROSE INCONSISTENCY: artifact 01_01_01_file_inventory.md shows 22390 files / 70 dirs; §4.1.3 Tabela 4.4a correct | Prose vs artifact mismatch | **stale** (prose fix needed: class A) |
| C3-02 | §3.2.4 | EsportsBench v8.0 Glicko-2 80,13% on SC2 corpus | Thorrez2024 preprint Table 2 ([REVIEW] open) | Literature ([REVIEW]) | intact |
| C3-03 | §3.2.4 | EsportsBench does NOT include AoE2 (verified in title list) | HuggingFace EsportsBench v8.0 title list verified 2026-04-20 (PR-TG3) | External verification | intact |
| C3-04 | §3.3.1 | Yang2017Dota 58,69% / 71,49% / 93,73% at 40min | arXiv:1701.03162 [REVIEW: F6.7 — split semantics + 60,07% numeric attribution pending PDF read] | Literature ([REVIEW] F6.7) | intact |
| C3-05 | §3.3.1 | Hodge2021 LightGBM ~85% at 5 min Dota 2 | Hodge2021 IEEE Trans. Games | Literature | intact |
| C3-06 | §3.2.3 | BaekKim2022 3D-ResNet 88,6% TvP | BaekKim2022 PLOS ONE | Literature | intact |
| C3-07 | §3.4.1 | CetinTas2023 ~86% | CetinTas2023 IEEE UBMK 2023 ([REVIEW] IEEE Xplore primary-source verification pending) | Literature ([REVIEW]) | intact |
| C3-08 | §3.4.2 | Lin2024NCT 1 261 288 AoE2 matches from aoestats.io | arXiv:2408.17180 ([REVIEW] pending) | Literature ([REVIEW]) | intact |

**Chapter 3 claims: 8. One stale (C3-01 — prose inconsistency). Seven intact (with some open [REVIEW] flags for literature verification).**

**Note on C3-01:** §3.2.2 says "17 930 plików z 55 paczek turniejowych". The pipeline artifact
01_01_01_file_inventory.md (sc2egset) reports 22 390 files in 70 tournament directories.
The §4.1.3 Tabela 4.4a correctly reflects 22 390 / 70. The §3.2.2 number appears to be an
earlier corpus estimate (possibly from the published SC2EGSet paper's original release or from a
draft estimate). Fix = class A wording change in §3.2.2, forwarding to §4.1.3 Tabela 4.4a.

---

## Chapter 4 — Data and Methodology

**T11 update (2026-04-26):** Chapter 4 prose was revised in T11 (cleanup rewrite) to apply
T05 source-specific terminology, T09 grain-disambiguation patches, T10 risk register
mitigation (RISK-01/02/03/04/07/08/23/24/26), and to remove workflow-leakage prose. The
v1 crosswalks remain frozen and unchanged. Below: T11-induced claim deltas (numerical
values unchanged; framing/grain clarified).

### T11 claim deltas (Chapter 4 prose 2026-04-26)

| Claim ID | Section/line locus | Delta | Evidence source |
|----------|-------------------|-------|-----------------|
| C4-T11-01 | §4.1.2.0 line 79 (closing rationale dual-corpus) | wording: "rankingowa ladderowa (dwa korpusy AoE2)" → "publiczna populacja 1v1 Random Map (dwa korpusy AoE2 o niejednorodnej kompozycji rankingu i quickplay/matchmakingu)" | T05 §4.4 (line 340); T09 CX-12 |
| C4-T11-02 | §4.1.3 Tabela 4.4a Populacja row | aoestats: "Ladder rankingowy 1v1 random_map" → Tier 4 wording with grain (~641K profile_id post-cleaning); aoe2companion: "Ladder rankingowy 1v1 (rm_1v1 + qp_rm_1v1)" → mixed-mode wording; SC2: added grain (~2 495 player_id_worldwide, Heckman selection) | T05 §4.4 lines 334–335; T09 CX-13/CX-14 |
| C4-T11-03 | §4.1.3 Tabela 4.4b Liczba meczów row | added grain labels: SC2 22 209 par meczowych / 44 418 player-rows; aoestats 17 814 947 meczów (1-row-per-match); aoe2companion 30 531 196 par meczowych / 61 062 392 player-rows / 683 790 distinct profileId in lb=6+18 cohort | T09 §1 row "Unit of observation"; T10 RISK-07/24; T10 WARNING-3/4 |
| C4-T11-04 | §4.1.3 Tabela 4.4b new row "Konstrukcja focal/opponent" | NEW row added to table describing per-dataset focal/opponent construction; explicitly differentiates SC2EGSet 2-row, aoestats 1-row UNION-ALL, aoe2companion 2-row | T10 RISK-24 |
| C4-T11-05 | §4.1.4 line 211 Twierdzenia dataset-conditional | replaced "rankingowe ladderowe (`[POP:ranked_ladder]`)" with mixed-mode + Tier 4 framing + new operational tags `[POP:rm_1v1_and_qp_rm_1v1]` and `[POP:1v1_random_map]`; explicit four-asymmetry framing of cross-game claims | T05 §4.4 line 337; T09 CX-17; T10 RISK-05/06 |
| C4-T11-06 | §4.2.5 Tabela 4.5 Populacja scope row | aoestats "ladder 1v1 random_map" → Tier 4 wording; aoe2companion "ladder 1v1 (rm_1v1 + qp_rm_1v1)" → explicit ranked candidate + quickplay/matchmaking-derived | T05 §4.4 lines 338–339; T09 CX-21 |
| C4-T11-07 | §4.2.5 Tabela 4.5 Kardynalność row | added grain labels: SC2 2 495 toon_id (post-cleaning); aoestats 641 662 profile_id (post-cleaning matches_1v1_clean); aoe2companion 3 387 273 profileId from `matches_raw` cross-leaderboard cardinality (NOT lb=6+18 cohort, which has 683 790 distinct profileId per `01_04_04_identity_resolution`) | T10 RISK-07; T09 §1 row "Population" line 19 |
| C4-T11-08 | §4.2.5 Uwaga do Tabeli 4.5 | rephrased "rankingowej (pełne historie kontowe)" → "publicznych rekordach z głębokimi historiami kontowymi (zarówno meczów rankingowych, jak i quickplay/matchmakingu)"; added grain caveat for ~78 figure | T10 RISK-07 |
| C4-T11-09 | §4.4.6 closure paragraph | removed `PR #TBD` (post-F1 already merged), `BACKLOG.md F1/F6` references, shell `grep` literal, Phase 02 references; added neutral closure phrasing tying flag to Pass-2 historical-narrative rewrite | T10 RISK-23; F-065/F-066/F-070/F-071/F-077 |
| C4-T11-10 | §4.2.3 line 303 (workflow-leakage) | replaced `.claude/scientific-invariants.md:86` file-path reference with academic phrasing "zasada prowenancji liczb (każda stała numeryczna musi być uzasadniona literaturą lub empirycznie, z dokumentacją derywacji w trwałym artefakcie)" | T10 RISK-08 (BLOCKER-B resolution); F-072 |
| C4-T11-11 | §4.4.4 Metryki podstawowe + Metryki dyskryminacyjne i kalibracyjne | tightened ECE framing: now explicitly stated as opisowa diagnostyka kalibracji (binning-dependent), NOT proper scoring rule per [Gneiting2007]; not equated with Brier/log-loss | T10 RISK-14 |
| C4-T11-12 | §4.4.5 Wybór observed-scale vs latent-scale ICC | softened "observed-scale headline stanowi zatem **dolne oszacowanie** latent-scale wielkości" → cautious "może być systematycznie nie mniejsza"; ICC reframed as "diagnostyka uzupełniająca", not main methodological measure | T10 RISK-15 |
| C4-T11-13 | Multiple §4.1, §4.2, §4.4 paragraphs (workflow-leakage) | systematic replacement of `Phase 01` / `Phase 02` / `Phase 03/04` workflow codes with academic phrasing ("etap eksploracji danych", "etap czyszczenia danych", "faza inżynierii cech", "faza splittingu i baselines", "faza treningu modeli"); invariant codes I3/I5/I7/I8/I9/I10 rephrased as named scientific principles ("zasada dyscypliny temporalnej", "zasada symetrycznego traktowania graczy", "zasada prowenancji liczb", "zasada jednolitego protokołu preprocessingu", "zasada niemodyfikowalności surowych tabel", "zasada prowenancji surowych tabel") | T10 RISK-08 / WARNING-3/4; F-066–F-076 |

### §4.1 claims (SC2EGSet and AoE2 corpus descriptions)

See `sec_4_1_crosswalk.md` — frozen v1 crosswalk with 101 rows covering all §4.1.1, §4.1.2,
and §4.1.3 prose numbers. Zero halt events at creation; all numbers grounded per
`sec_4_1_halt_log.md`. **Numerical values unchanged by T11; only framing/grain/terminology
revised.**

Quick reference to key claim clusters:

| §4.1 sub-section | Crosswalk row count | Key numbers | Status |
|-----------------|-------------------|-------------|--------|
| §4.1.1 SC2EGSet scale | ~14 rows | 22390 files / 70 dirs / 214 GB / 2016–2024 | intact → see sec_4_1_crosswalk.md rows 1–14 |
| §4.1.1 event streams | ~8 rows | 62 003 411 / 608 618 823 / 52 167 events; 10/23/3 event types | intact → see sec_4_1_crosswalk.md rows 15–24 |
| §4.1.1 cleaning | ~10 rows | matches_flat_clean 22209 / 44418; R01 -24; R03 -157; 28 cols | intact → see sec_4_1_crosswalk.md rows 25–35 |
| §4.1.1 missingness | ~8 rows | MMR=0 83.95%/83.65%; APM=0 2.53%; highestLeague 72.04%; clanTag 73.93% | intact → see sec_4_1_crosswalk.md rows 36–44 |
| §4.1.2 aoestats scale | ~12 rows | 172/171 files / 3773.61 MB / 17815944 final matches | intact → see sec_4_1_crosswalk.md rows 45–60 |
| §4.1.2 aoestats cleaning | ~8 rows | R08 -997; 20 cols; 107626399 rows player_history | intact → see sec_4_1_crosswalk.md rows 61–70 |
| §4.1.2 aoec scale | ~12 rows | 2073/2072 files / 9387.80 MB / 30531196 matches | intact → see sec_4_1_crosswalk.md rows 71–88 |
| §4.1.2 aoec cleaning | ~10 rows | R01 -216M rows; R03 -5052 matches; rating NULL 26.20% | intact → see sec_4_1_crosswalk.md rows 89–101 |

### §4.2 claims (preprocessing decisions)

See `sec_4_2_crosswalk.md` — frozen v1 crosswalk with 48 main rows + 10 identity checks +
16 scope-overlap rows + 4 bib classification rows (78 total rows). Zero halt events at creation
per `sec_4_2_halt_log.md`.

Quick reference:

| §4.2 sub-section | Crosswalk rows | Key numbers | Status |
|-----------------|---------------|-------------|--------|
| §4.2.1 ingestion | ~8 rows | 22390/44817/104160 DuckDB tables; 367.6 GB streams | intact → see sec_4_2_crosswalk.md rows 1–10 |
| §4.2.2 identity resolution | ~10 rows | toon_id 2495; nickname 1106; mean 18/40 games/player; profileId 641662/3387273 | intact → see sec_4_2_crosswalk.md rows 11–22 |
| §4.2.3 cleaning rules | ~20 rows | threshold 5%/40%/80%; MAR/MCAR classification; all Tabela 4.6 identity checks | intact → see sec_4_2_crosswalk.md rows 23–48 |

### Post-v1-crosswalk Chapter 4 claims

See `dependency_lineage_audit.md` §"Chapter 4 — Data and Methodology: empirical claim map"
for audit rows C4-01 through C4-10 covering:

- §4.4.5 Tabela 4.7 ICC values (C4-01, C4-02, C4-03)
- §4.4.6 [PRE-canonical_slot] audit numbers (C4-04, C4-05)
- §4.1.3 reference-window patch 66692 numbers (C4-06, C4-07)
- §4.1.4 population scope tag counts (C4-08, C4-09, C4-10)

All 10 post-v1-crosswalk claims are **intact**.

---

## Summary counts

| Chapter | Claims in this matrix | Pointing to v1 crosswalk | Directly audited | Stale | Prose-only |
|---------|-----------------------|-------------------------|-----------------|-------|------------|
| 1 | 4 | 0 | 4 | 0 | 2 |
| 2 | 11 | 0 | 11 | 0 | 0 |
| 3 | 8 | 0 | 8 | 1 | 0 |
| 4 | 10 post-crosswalk + ~149 v1 | 149 | 10 | 0 | 0 |
| **Total** | **182** | **149** | **33** | **1** | **2** |
