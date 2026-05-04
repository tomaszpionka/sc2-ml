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

### T13 claim deltas (Chapter 2 prose 2026-04-26)

T13 (Chapter 2 cleanup rewrite) revised Chapter 2 prose to apply T05 source-specific
terminology (CX-08 PRIMARY FIX), T09 cross-dataset comparability framing, and T10
risk register mitigation (RISK-04 / RISK-05 / RISK-12 / RISK-14 / RISK-25). Numerical
claims (50 civilizations, 1 225 unordered pairs, 9 race pairs, 555 Random-race
replays, 22.4 game loops/s, 80.13% Glicko-2, 411 030 SC2 matches) unchanged in count;
their framing is now hedged for date-validity, roster instability, ECE-vs-proper-
scoring-rule distinction, and SC2EGSet-not-being-ladder.

| Claim ID | Section/line locus | Delta | Evidence source |
|----------|-------------------|-------|-----------------|
| C2-T13-01 | §2.2.3 line 37 (CX-08 PRIMARY FIX, RISK-01/02/03/04/05) | "ladderowa populacja rankingowa" → expanded paragraph using T05 Tier-4 wording for aoestats and mixed-mode wording for aoe2companion; explicit disclaimer that SC2EGSet is "turniejowy korpus replay'ów profesjonalnych (`leaderboard_raw` jest NULL dla 100% rekordów), nie próba meczów rankingowych z systemu matchmakingu"; added "w których uczestniczy znacznie szersza populacja graczy" qualifier on Battle.net ladder reference | T05 §4.4 lines 334–337, §4.1.7; T09 §1 row "Ranked / ladder / quickplay / matchmaking status"; T09 CX-08 wording-change-required; T10 RISK-01/02/03/04/05 |
| C2-T13-02 | §2.3.2 line 69 (DLC chronology + roster instability framing, RISK-12 / RISK-25) | "W okresie objętym analizowanymi danymi… oferuje pięćdziesiąt cywilizacji dostępnych w trybie rankingowym" → "W oknie czasowym analizowanych danych aoestats (2022-08-28 — 2026-02-07, Tabela 4.4a) Age of Empires II: Definitive Edition zawierał do 50 cywilizacji obserwowanych w korpusie"; appended sentence "Roster ulegał rozszerzeniu w trakcie analizowanego okna czasowego wraz z premierami kolejnych dodatków DLC, zatem nie wszystkie cywilizacje były dostępne przez całe okno; wartość 50 odzwierciedla stan końcowy obserwowany pod koniec analizowanego okresu"; "trybie rankingowym" qualifier dropped per RISK-04 Tier 4 framing for aoestats. [REVIEW: DLC chronology completeness] flag retained verbatim. | T10 RISK-12 / RISK-25; F-014 / F-084; T05 §4.1.7; consistency with T12 hedges in §1.1 / §1.2 / §1.3 / §1.4 |
| C2-T13-03 | §2.3.2 line 71 (1 225 pair-space framing, RISK-25) | "pięćdziesiąt cywilizacji generuje $\binom{50}{2} + 50 = 1\,275$ uporządkowanych par (lub 1 225 jeśli wyłączyć pojedynki tej samej cywilizacji), co jest o dwa rzędy wielkości większe niż dziewięć możliwych zestawień rasowych w SC2" → preserved core arithmetic but framed it under the explicit hedge "przy założeniu stałego rosteru zaobserwowanego pod koniec analizowanego okna" + "do 1 225 nieuporządkowanych par"; appended interpretation paragraph "Liczby te należy interpretować jako górne ograniczenie wysokowymiarowej przestrzeni par cywilizacji obowiązujące przy stałym roster — w trakcie analizowanego okna premiery kolejnych dodatków DLC powiększały dostępny zestaw cywilizacji, w konsekwencji nie wszystkie pary były obserwowalne przez całe okno"; "średnia liczba meczów na uporządkowaną parę cywilizacji wynosi około 17 200" → "wynosiłaby około 17 200" (conditional on uniform roster); skewness paragraph extended with "oraz na zmienną dostępność cywilizacji w czasie" | T10 RISK-25; consistency with T12 §1.3 RQ3 hypothesis hedge; F-014 / F-084 |
| C2-T13-04 | §2.5.4 line 173 (1 225 pair-space framing in rating-system context, RISK-25) | "przestrzeń 1 225 par cywilizacji (dla 50 cywilizacji dostępnych w okresie objętym analizowanymi danymi)" → "wysokowymiarowa przestrzeń par cywilizacji (do 1 225 nieuporządkowanych par przy założeniu stałego rosteru zaobserwowanego pod koniec analizowanego okna danych aoestats)" | T10 RISK-25; consistency with C2-T13-02 / C2-T13-03 + §2.3.2 |
| C2-T13-05 | §2.6.2 final ¶ (ECE not a proper scoring rule, RISK-14 / F-087) | Original prose "operacyjną ramą diagnostyki agregatowej w niniejszej pracy jest zestaw trzech elementów: Expected Calibration Error (ECE) w standardowym binningu dziesięciokwantylowym, diagram rzetelności…, oraz dekompozycja Murphy'ego" reframed: wynik Briera + strata logarytmiczna explicitly named jako właściwe reguły punktacji (Gneiting2007); ECE explicitly demarked as "funkcję pomocniczą, opisową — w odróżnieniu od wyniku Briera i straty logarytmicznej, sama wartość ECE nie jest właściwą regułą punktacji w sensie Gneitinga i Raftery [Gneiting2007], ponieważ jej wartość oczekiwana nie jest minimalizowana wyłącznie przez raportowanie prawdziwej dystrybucji warunkowej, a estymacja zależy od arbitralnego wyboru schematu binningu"; operational frame redescribed jako "dwie właściwe reguły punktacji jako miary główne plus zestaw diagnostyczny ECE + diagram rzetelności + dekompozycja Murphy'ego". Reliability diagram annotated "graficznym, niezależnym od wyboru binningu w jego ciągłej wersji bandwidth-aware". | T10 RISK-14; F-087 cross-cutting external-audit; Gneiting2007 (already in bib); consistency with T11 §4.4.4 ECE framing |

**Wording-change-required claims resolved by T13:** CX-08 (line 37 "ladder ranking population" — fully rewritten with Tier 4 + mixed-mode framing for aoestats and aoe2companion respectively, plus explicit SC2EGSet not-ladder disclaimer).

**Open Pass-2 verification flags retained verbatim in Chapter 2 (per T13 instructions):**
- F-008 §2.1 line 15 (post-Phase-04 difficulty-asymmetry claim revisit)
- F-009 §2.2.3 line 39 (Thorrez2024 / Aligulac F4.5 — exact value + Aligulac row check)
- F-010 §2.2.4 line 49 (Liquipedia_GameSpeed / BlizzardS2Protocol grey-lit policy)
- F-011 §2.2.4 line 51 (Patch 2.0.8 release date citation)
- F-012 §2.3.2 line 61 (epoch-time peer-reviewed source)
- F-013 §2.3.2 line 65 (map pool representativeness for corpus window)
- F-014 §2.3.2 line 69 (DLC chronology completeness — Three Kingdoms / Chronicles: Alexander / Last Chieftains)
- F-015 §2.4.4 line 117 (SVM-linear inclusion decision after Phase 03)
- F-016 §2.4.6 line 131 (GNN exclusion decision after Phase 04/05)
- F-017 §2.4.7 line 135 (method hierarchy reordering after Phase 04)
- F-018 §2.5.3 line 163 (TrueSkill 2 RTS independent validation)
- F-019 §2.5.5 lines 185–186 (Aligulac historical snapshots + F4.5/F5.3 closure)
- F-020 §2.6.3 line 213 (Demšar §3.1.3 vs §3.2 section verification)
- F-021 §2.6.4 lines 229–230 (Phase 04 cross-game concordance + Phase 03 IID assumption check)

All 14 retained flags route to Pass 2 / T14 territory; T13 does not perform external literature verification.

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

### T14 claim deltas (Chapter 3 prose 2026-04-26)

T14 (Chapter 3 cleanup rewrite + bulk Pass-2 literature verification) revised
Chapter 3 prose to apply bounded literature-gap framing per RISK-16, mirror the
Chapter 1 §1.1 register established by T12, sharpen the Elbert2025EC attribution
method to verified linear FE residualization (RISK-13 / F-037 closure), update the
EsportsBench version reference from v8.0 / 2025-12-31 to verified v9.0 / 2026-03-31
(F-038 partial closure), and reframe the Yang2017Dota 9:1-split flag to reflect that
the proportion is documented but split-method (random vs temporal) is not (F-026
substantive closure on the 60.07% / Kinkade attribution; split-method retention).
Numerical claims (78 362 / 20 631 / 58.69 / 71.49 / 93.73 / 85 / 88.6 / 86 /
1 261 288 / 14 000 / 1 623 828 / pseudo-R² 0.0744, 0.1004) unchanged in count.

| Claim ID | Section/line locus | Delta | Evidence source |
|----------|-------------------|-------|-----------------|
| C3-T14-01 | §3.2.4 line 77 (EsportsBench version reference) | "wersja HuggingFace v8.0, cutoff 2025-12-31" → "wersja HuggingFace v9.0, cutoff 2026-03-31, dostęp 2026-04-26"; "20 tytułów… AoE2 w żadnej wersji EsportsBench wydanej do 2025-12-31 nie występuje" → "20 tytułów (zweryfikowanym 2026-04-26 na karcie zbioru danych HuggingFace dla wersji v9.0)"; existing [REVIEW] flag for 80.13% Pass-2 PDF read reworded to note "binarny strumień FlateDecode" failure mode | F-038 partial closure; Thorrez2024 dataset card v9.0 verified 2026-04-26; literature_verification_log.md row Thorrez2024 |
| C3-T14-02 | §3.3.1 line 91 (Yang2017Dota split-method + 58.69% attribution) | "podział 9:1 dobierany losowo, a nie temporalnie [REVIEW: F6.7 Pass-2 audit — zweryfikować arXiv:1701.03162 pod kątem semantyki podziału 9:1 (random vs temporal); numeric reclassification (czy 58,69% jest reimplementacją Kinkade vs własnym LR Yanga = 60,07%) odroczona…]" → "proporcja 9:1; semantyka tego podziału (losowa wobec temporalnej) nie jest jawnie wymieniona w treści preprintu (weryfikacja przez `https://ar5iv.labs.arxiv.org/html/1701.03162`, dostęp 2026-04-26)"; flag rewording with bounded scope; 58.69% reattributed to "reimplementacji wcześniejszej linii bazowej Conleya/Kinkade'a wykonanej przez autorów Yang i in. na ich własnym zbiorze danych przy użyciu regresji logistycznej, nie niezależnemu wynikowi z innej pracy" | F-026 substantive closure (60.07%/Kinkade closed); arXiv:1701.03162 ar5iv HTML accessed 2026-04-26; literature_verification_log.md row Yang2017Dota |
| C3-T14-03 | §3.2.3 line 69 (SC-Phi2 metadata + qualitative-superiority claim) | bibliographic metadata expanded inline: "opublikowane w czasopiśmie MDPI AI (vol. 5, iss. 4, ss. 2338–2352, listopad 2024; preprint arXiv:2409.18989, wrzesień 2024)"; qualitative dominance over GRU/Transformer added with explicit hedge "Według metadanych dostępnych na karcie publikacji MDPI (dostęp 2026-04-26)"; existing [REVIEW] flag rewritten to scope to exact accuracy values, not metadata | Khan2024SCPhi2 MDPI page verified 2026-04-26; arXiv:2409.18989 verified 2026-04-26; literature_verification_log.md row Khan2024SCPhi2 |
| C3-T14-04 | §3.4.1 line 129 (CetinTas2023 framing — bounded register) | "Jedyną opublikowaną pracą recenzowaną" → "W przeprowadzonym przeglądzie literatury jako recenzowaną pracę… zidentyfikowano"; "reprezentuje jedyną recenzowaną linię bezpośrednio porównywalną" → "reprezentuje jedyną zidentyfikowaną w przeglądzie recenzowaną linię"; consistent with Chapter 1 §1.1 / §1.4 T12 register | RISK-16 mitigation; T12 §1.1 framing precedent; CetinTas2023 IEEE Xplore verified 2026-04-26 |
| C3-T14-05 | §3.4.1 line 137 (CetinTas2023 successor-absence framing) | "nie ma — przynajmniej w piśmiennictwie recenzowanym — udokumentowanego następnika" → "— w przeprowadzonym przeglądzie piśmiennictwa recenzowanego — nie ma udokumentowanego następnika" | RISK-16 mitigation; bounded register |
| C3-T14-06 | §3.4.2 line 145 (Lin2024NCT positioning — bounded register) | "brakuje pracy recenzowanej, która w AoE2 podejmuje predykcję wyniku jako zadanie podstawowe" → "w przeprowadzonym przeglądzie literatury nie zidentyfikowano pracy recenzowanej, która w AoE2 podejmuje predykcję wyniku jako zadanie podstawowe" | RISK-16 mitigation |
| C3-T14-07 | §3.4.3 line 155 (Elbert2025EC data source verification) | "dane pochodzą z platformy aoe2insights.com (14 000 graczy ogniskowych, 1 623 828 meczów drużynowych, listopad 2019–grudzień 2023)" → same numerics with explicit citation hedge "(weryfikacja przez wersję HTML preprintu `https://arxiv.org/html/2506.04475v1`, dostęp 2026-04-26)" | F-035 closure; literature_verification_log.md row Elbert2025EC |
| C3-T14-08 | §3.4.4 line 163 (aoe2insights.com / Elbert2025EC source-confirmation) | "[REVIEW: verify czy aoe2insights.com jest faktycznym źródłem danych Elbert2025EC poprzez bezpośredni odczyt PDF z arXiv:2506.04475; obecnie cytowane jako obserwacja pomocnicza, nie potwierdzenie źródła]" → REMOVED. Replaced with "potwierdzona jako źródło danych Elbert2025EC w wersji HTML preprintu na `https://arxiv.org/html/2506.04475v1`, dostęp 2026-04-26" | F-035 closure; literature_verification_log.md row Elbert2025EC |
| C3-T14-09 | §3.4.5 lines 167–179 (six luki — bounded register) | "żadna praca recenzowana nie raportuje" / "żadna praca recenzowana nie stosuje" / "żadna praca — recenzowana ani szara — nie podejmuje" / "żadna praca recenzowana nie stosuje" / "brak prac" / "żadna praca recenzowana nie podejmuje" → all six rewritten to "w przeprowadzonym przeglądzie nie zidentyfikowano…" / "w przeprowadzonym przeglądzie — zarówno literatury recenzowanej, jak i szarej — nie zidentyfikowano…" register; new opening sentence added: "W każdym z poniższych punktów stwierdzenia odnoszą się do prac zidentyfikowanych w przeprowadzonym przeglądzie literatury — nie roszczą sobie prawa do absolutnej kompletności wobec całego dorobku światowego" | RISK-16 mitigation; T12 / Chapter 1 §1.1 precedent; bounded register established by Chapter 1 |
| C3-T14-10 | §3.5 Luka 1 line 185 ("brak kalibracji jest absolutny" + "żadna praca esportowa") | "brak kalibracji jest absolutny" → "w przeprowadzonym przeglądzie nie zidentyfikowano pracy raportującej kalibrację"; "żadna praca esportowa — ani dla SC2, ani dla AoE2, ani dla MOBA — nie przeprowadza systematycznego porównania" → "w przeprowadzonym przeglądzie literatury esportowej — obejmującym SC2, AoE2, MOBA i pozostałe gatunki — nie zidentyfikowano pracy przeprowadzającej systematyczne porównanie" | RISK-16 mitigation |
| C3-T14-11 | §3.5 Luka 2 line 187 (Elbert2025EC attribution method — verified) | "zgodnie z naszym odczytaniem ich §3.4.3 oraz architektury ekonometrycznej ACM EC '25 — linearną regresją z efektami stałymi" + speculative hedge "jeśli nasze odczytanie jest poprawne, rozróżnienie to jest istotne" + [REVIEW: F6.2 Pass-2 audit] flag → Replaced with verified statement: "zgodnie z weryfikacją wersji HTML preprintu na `https://arxiv.org/html/2506.04475v1` (dostęp 2026-04-26) — rezydualizacją regresją z efektami stałymi (ang. *linear fixed-effects residualization*): autorzy szacują logistyczny model bazowy z mierzalnych wskaźników umiejętności, a następnie agregują rezydua jako miarę efektu drużynowego, nie stosując warunkowej atrybucji marginalnej typu metoda SHAP". F6.2 [REVIEW] flag removed (verification complete). Closing summary "pozostaje empirycznie niezbadane" → "w przeprowadzonym przeglądzie literatury pozostaje empirycznie niezbadane" | F-037 closure; RISK-13 mitigation (Chapter 3 portion); literature_verification_log.md row Elbert2025EC |
| C3-T14-12 | §3.5 Luka 3 line 189 (EsportsBench narrowing — version refresh) | EsportsBench version reference updated v8.0 / 2025-12-31 → v9.0 / 2026-03-31 throughout (three occurrences in same paragraph); HuggingFace dataset card access date 2026-04-26 explicit; "publicznie dostępna dokumentacja EsportsBench (HuggingFace dataset README v8.0 2025-12-31)" → "(karta zbioru danych HuggingFace v9.0 oraz README repozytorium GitHub, dostęp 2026-04-26)"; "w przestrzeni wyznaczonej koniunkcją tych czterech ograniczeń przedmiot niniejszej pracy stanowi… układ nie obecny" → "konfiguracja badawcza niniejszej pracy stanowi — w przeprowadzonym przeglądzie literatury recenzowanej i po bezpośredniej weryfikacji składu tytułów EsportsBench w wersji v9.0 (cutoff 2026-03-31, dostęp 2026-04-26) — układ niezidentyfikowany w istniejących publikacjach". Existing [REVIEW] flag preserved verbatim (Pass-2 still verifies post-2026-04-26 EsportsBench versions + Table 2 metric coverage) | F-038 partial closure (v9.0 verified); RISK-16 mitigation; HuggingFace dataset card 2026-04-26; literature_verification_log.md row Thorrez2024 |
| C3-T14-13 | §3.5 Luka 4 line 191 (cold-start register + GarciaMendez2025 streaming context) | "żadna z wymienionych prac (§3.2.1–§3.2.3) nie stratyfikuje" → "w przeprowadzonym przeglądzie nie zidentyfikowano pracy stratyfikującej"; "żadna z prac cytowanych w §3.2–§3.4 nie stratyfikuje" → "w przeprowadzonym przeglądzie literatury cytowanej w §3.2–§3.4 nie zidentyfikowano pracy stratyfikującej"; "luka ta jest absolutna — nie istnieje żadna praca" → "w przeprowadzonym przeglądzie — zarówno literatury recenzowanej, jak i szarej — nie zidentyfikowano pracy"; GarciaMendez2025 inline parenthetical refined to reflect verified streaming-CS:GO context: "streaming-ML kontekst w [GarciaMendez2025], cytowanym w §1.1 z powodu ramowania streaming-ML win prediction w środowiskach typu Counter-Strike, gdzie cechy są pozyskiwane przez API platformy strumieniowej" | RISK-16 mitigation; F-082 partial closure (Chapter 3 portion); literature_verification_log.md row GarciaMendez2025 |
| C3-T14-14 | §3.2.4 line 79 ("konfiguracja badawcza bez precedensu") | "stanowi konfigurację badawczą bez precedensu w obrębie istniejących publikacji" → "stanowi konfigurację badawczą, której nie zidentyfikowano w istniejących publikacjach recenzowanych" with bounded "w zakresie objętym przeprowadzonym przeglądem literatury" hedge | RISK-16 mitigation; T12 register precedent |

**Resolved by T14:**
- F-022 (Vinyals2017 baseline scope): preserved verbatim — Vinyals2017 confirmed as primarily RL/agent paper; chapter prose already correctly hedges. Pass-2 reviewer can close after rereading PDF.
- F-023 / F-024 (C3-01 SC2EGSet 17 930 vs 22 390 prose inconsistency): preserved as Pass-2 wording-fix candidate — T14 did NOT rewrite this number because Bialecki2023 paper does carry "17 930" historical figure pre-corpus expansion (chapter prose correctly traces the 17 930 / 55 number to that source via the [Bialecki2023] citation, with §4.1.3 Tabela 4.4a holding the post-merge 22 390 / 70 figure for the live corpus). Forward-ref to §4.1.3 already present in chapter prose.
- F-025 (EsportsBench 80.13% Pass-2 PDF verification): preserved with refined flag wording (binary FlateDecode failure mode noted); manual PDF read still required for Pass-2.
- F-026 (Yang2017Dota): substantively addressed — 9:1 proportion confirmed; split-method (random vs temporal) confirmed not specified in preprint text; 58.69% attribution closed (= Yang's own LR reimplementation of Conley/Kinkade baseline, not separate reading at 60.07%). Refined chapter-prose [REVIEW] flag retained for Pass-2 final PDF read.
- F-027 (CS:GO peer-reviewed selection): preserved — T14 did not select Xenopoulos et al. (out of scope per current chapter framing of §3.3.3 as "wystąpienia konferencyjne IEEE oraz rosnąca liczba prac dyplomowych"); flag still routes to Pass-2.
- F-028 (Valorant peer-reviewed 2025–2026): preserved — same reason as F-027.
- F-029 / F-030 (CetinTas2023 86% + NB/DT vs "Regression Analysis" title): preserved — IEEE Xplore DOI verified; exact 86% value still pending Pass-2 PDF read; methodology vs title tension preserved as in-prose [REVIEW].
- F-031 (EC'25 citation convention extended-abstract @inproceedings vs @misc): preserved — bib retains @inproceedings with `note` clarifying extended-abstract format; Pass-2 librarian decision.
- F-032 (ACM EC 2025 acceptance-rate): preserved as note (optional addition).
- F-033 (grey-literature acceptability — PJAIT): preserved — out of T14 scope.
- F-034 (Xie2020 R²-vs-accuracy interpretation): preserved — Medium post text still requires Pass-2 manual read.
- F-035 (Elbert2025EC data source aoe2insights.com): RESOLVED — verified via arXiv HTML 2026-04-26; chapter prose now reflects verified source with explicit citation hedge.
- F-036 (4 author candidates Brookhouse/Caldeira/Alhumaid/Ferraz): preserved — WebSearch 2026-04-26 still does not surface these candidates; flag remains [NEEDS CITATION] in §3.5 Luka 1.
- F-037 (Elbert2025EC attribution method — SHAP vs linear FE residualization): RESOLVED — verified as linear FE residualization (NOT SHAP); chapter prose updated with verified method description and original [REVIEW] flag removed.
- F-038 (EsportsBench narrowing + Thorrez Table 2 calibration metrics): partially resolved — version refreshed to v9.0 / 2026-03-31; AoE2-not-in-benchmark verified; calibration-metric coverage in benchmark protocol still requires Pass-2 PDF read.

**Open Pass-2 verification flags retained verbatim in Chapter 3 (per T14 instructions 7–9):**
- F-022 §3.2.2 line 49 (Vinyals2017 baseline scope hedge — preserved)
- F-023 §3.2.2 line 55 (SC2EGSet corpus structure forward-ref to §4.1.1 — preserved)
- F-025 §3.2.4 line 77 (EsportsBench 80.13% — preserved with refined flag wording per C3-T14-01)
- F-026 §3.3.1 line 91 (Yang2017Dota — preserved with substantive scope-narrowing per C3-T14-02)
- F-027 §3.3.3 line 107 (CS:GO peer-reviewed selection — preserved)
- F-028 §3.3.4 line 111 (Valorant peer-reviewed 2025–2026 — preserved)
- F-029 §3.4.1 line 131 (CetinTas2023 86% IEEE Xplore verification — preserved)
- F-030 §3.4.1 line 133 (CetinTas2023 NB/DT vs title — preserved)
- F-031 §3.4.3 line 151 (EC'25 citation convention — preserved)
- F-032 §3.4.3 line 151 (ACM EC 2025 acceptance-rate — preserved)
- F-033 §3.4.4 line 159 (grey-literature acceptability — preserved)
- F-034 §3.4.4 line 161 (Xie2020 R²-vs-accuracy — preserved)
- F-035 §3.4.4 line 163 (aoe2insights.com / Elbert2025EC source) — RESOLVED via C3-T14-08; flag removed from prose
- F-036 §3.5 line 185 (4 author candidates) — preserved verbatim
- F-037 §3.5 line 187 (Elbert2025EC attribution method) — RESOLVED via C3-T14-11; flag removed from prose
- F-038 §3.5 line 189 (EsportsBench narrowing) — preserved with refined flag wording per C3-T14-12; v9.0 sub-claim resolved
- F-088 §3.3.5 (SHAP causal interpretation Chapter 3 portion) — chapter prose already hedges (via §1.4 cross-ref); no Chapter 3 prose change required

Total Chapter 3 [REVIEW] / [NEEDS CITATION] flags pre-T14: 13 (per F-022 through F-038 + F-036). Post-T14: 11 (F-035 and F-037 removed via prose verification; F-026 reframed but retained).

**Wording-change-required claims from T05/T09 affecting Chapter 3:** None. Per T05 §4.4 line 348 and T09 §3 (Chapter routing summary), `03_related_work.md:143` use of "ranked matches" referring to the Lin2024NCT paper's data is **source-specific** (citing another paper's terminology) and is preserved verbatim. T14 explicitly does NOT edit this line per plan T14 instruction 6.

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
