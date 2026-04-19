# Thesis Writing Status

Last updated: 2026-04-19 (F3: §4.2.2 DRAFTED → REVISED)

---

## Status key

| Status | Meaning |
|--------|---------|
| `SKELETON` | Header and brief note exist. No prose. |
| `BLOCKED` | Feeding phase incomplete — cannot write yet. |
| `DRAFTABLE` | Feeding phase complete — ready to draft. |
| `DRAFTED` | First draft exists. May need revision later. |
| `REVISED` | Updated after later phase provided new context. |
| `FINAL` | Content-complete, ready for typesetting. |

---

## Formatting targets

Minimum length: **72,000 characters with spaces** (~40 normalized pages, typical 60–80).
Abstract: 400–1500 characters. Keywords: 3–5.
Full validation rules: `.claude/thesis-formatting-rules.yaml` → `content_thresholds`.
Source: `docs/thesis/PJAIT_THESIS_REQUIREMENTS.md`.

---

## Chapter 1 — Introduction

| Section | Status | Feeds from | Notes |
|---------|--------|------------|-------|
| §1.1 Background and motivation | `DRAFTED` | — | Literature + framing. Gate 0 voice calibration draft. |
| §1.2 Problem statement | `DRAFTABLE` | — | Literature + framing |
| §1.3 Research questions | `DRAFTED` | — | Literature + framing. Drafted 2026-04-17. 4 RQs operationalized; 9 inline citations; 2 [REVIEW] flags. ~5.0k chars Polish. Finalize after Phase 03–04. |
| §1.4 Scope and limitations | `DRAFTED` | — | Literature + framing. Drafted 2026-04-17. 7 inline citations; 1 [REVIEW] flag (AoE2 roadmap). ~4.6k chars Polish. Revise after AoE2 lit review. |
| §1.5 Thesis outline | `BLOCKED` | All chapters | Write last |

## Chapter 2 — Theoretical Background

| Section | Status | Feeds from | Notes |
|---------|--------|------------|-------|
| §2.1 Gry strategiczne czasu rzeczywistego | `DRAFTED` | — | Literature; Pass 1 + post-adversarial revision (2026-04-17). Adversarial WARNING applied: "operacjonalizuje RQ2/RQ3" softened to "motywuje RQ2/RQ3" (§1.3 owns operationalization). 9 distinct keys, 1 [REVIEW] flag. ~12.0k chars Polish. 1 new bibtex entry (Buro2003; URL fixed post-review). |
| §2.2 StarCraft II | `DRAFTED` | Phase 01 (Data Exploration — timing + mechanics only; corpus details moved to §4.1.1 staging) | Mixed Literature + Data-fed; Pass 1 + post-adversarial revision (2026-04-17). Adversarial verdict REQUIRE_SUBSTANTIAL_REVISION caught BLOCKER scope creep — §2.2.5 "Korpus SC2EGSet" subsection deleted; corpus statistics deferred to §4.1.1. 12 distinct keys, 1 [REVIEW] flag (grey-literature acceptability). ~12.5k chars Polish (was 14.5k pre-fix). 4 new bibtex entries from Sprint 7 retained. |
| §2.3 Age of Empires II | `DRAFTED` | Phase 01 (aoestats + aoe2companion — game theory only; corpus details moved to §4.1.2 staging) | Mixed Literature + Data-fed; Pass 1 + post-adversarial revision (2026-04-17). Adversarial verdict REQUIRE_SUBSTANTIAL_REVISION caught BLOCKERs: §2.3.4 trimmed to ≤500 chars (corpus numbers moved to §4.1.2 staging); §2.3.3 first paragraph cut (player roster + commentator list + Red Bull Wololo Londinium narrative removed); K=32 paragraph collapsed to forward-ref to §2.5.4. 7 distinct keys, 2 [REVIEW] flags. ~9.5k chars Polish (was 13.8k pre-fix). 5 new bibtex entries retained (AoE2DE, MgzParser, AoEStats, AoeCompanion, AoE2MapPool); RedBullWololoLondinium retained but no longer cited in §2.3 — flag for future cleanup. |
| §2.4 ML methods for classification | `DRAFTED` | — | Literature; Pass 1 calibration draft (2026-04-17). 17 distinct keys, 3 [REVIEW] flags. ~14.7k chars Polish. 13 new bibtex entries appended (Hastie2009ESL, Friedman2001GBM, Chen2016XGBoost, Ke2017LightGBM, Goodfellow2016DL, Breiman2001, CortesVapnik1995, Hochreiter1997LSTM, KipfWelling2017, NiculescuMizil2005, etc.). |
| §2.5 Player skill rating systems | `DRAFTED` | — | Literature; Gate 0.5 calibration draft (2026-04-17). 14 distinct keys / 24 inline citations, 4 [REVIEW] flags. ~20.9k chars Polish. **Gate 0.5: PASS_FOR_PRODUCTION_SCALING.** |
| §2.6 Evaluation metrics | `DRAFTED` | — | Literature; Pass 1 calibration draft (2026-04-17). 14 distinct keys, 2 [REVIEW] flags. ~12.8k chars Polish. 10 new bibtex entries appended (Brier1950, Murphy1973, HanleyMcNeil1982, Friedman1937, Wilcoxon1945, Holm1979, GarciaHerrera2008, Garcia2010, Benavoli2016, Benavoli2017, Nadeau2003, Dietterich1998, Bouckaert2003). |

## Chapter 3 — Related Work

| Section | Status | Feeds from | Notes |
|---------|--------|------------|-------|
| §3.1 Traditional sports prediction | `DRAFTED` | — | Literature; Pass 1 calibration draft (2026-04-17). 11 distinct keys, 0 [REVIEW] flags. ~7.8k chars Polish. 5 new bibtex entries appended (Dixon1997, Maher1982, Constantinou2013, Bunker2024, Glickman1995). |
| §3.2 StarCraft prediction literature | `DRAFTED` | — | Literature; Pass 1 calibration draft (2026-04-17). 28 distinct keys / ~46 inline citations, 6 [REVIEW] flags. ~14.8k chars Polish. 15 new bibtex entries appended. Tarassoli2024 flagged as SC-Phi2 misattribution; deferred to user morning review. |
| §3.3 MOBA and other esports | `DRAFTED` | — | Literature; Pass 1 calibration draft (2026-04-17). 13 distinct keys, 2 [REVIEW] flags. ~11.4k chars Polish. 5 new bibtex entries appended (Yang2017Dota, Bahrololloomi2023, Akhmedov2021, Silva2018LoL, Yangibaev2025). |
| §3.4 AoE2 prediction | `DRAFTED` | AoE2 lit review | Literature; Pass 1 calibration draft (2026-04-18). 5 distinct keys (CetinTas2023, Lin2024NCT, Elbert2025EC, Xie2020MediumAoE, Porcpine2020EloAoE) + cross-refs. 5 [REVIEW] flags. ~8.2k chars Polish. 4 new bibtex entries appended (Elbert2025EC new; Xie2020MediumAoE + Porcpine2020EloAoE Tier 3; CetinTas2023 author-list fixed). |
| §3.5 Research gap | `DRAFTED` | §3.1-§3.4 | Literature synthesis; Pass 1 calibration draft (2026-04-18). 1 [REVIEW] flag. ~6.7k chars Polish. No new bib entries (pure synthesis). Luka 3 hedge strengthened per v2 plan (Q_adv_2). |

## Chapter 4 — Data and Methodology

| Section | Status | Feeds from | Notes |
|---------|--------|------------|-------|
| §4.1 Opening framing + §4.1.1 SC2EGSet description | `DRAFTED` | Phase 01 (Data Exploration, sections 01_01–01_04 for sc2egset) | Drafted 2026-04-17. ~18.5k znaków polskich. 5 [REVIEW] flags. Phase 01 sections 01_01–01_04 fully cited; sections 01_05 (Temporal & Panel EDA), 01_06 (Decision Gates) deferred — flagged where claims await them. Tabela 4.1 (CONSORT flow) present. **2026-04-18: §4.1.1.4 line 41 narrative + Tabela 4.4b line 195 cell repaired to MAR-primary / MNAR-sensitivity per ledger row 35 (MMR classification consistency with §4.2.3).** |
| §4.1.2 AoE2 datasets (aoestats + aoe2companion) | `DRAFTED` | Phase 01 (Data Exploration, sections 01_01–01_04 for both AoE2 datasets) | Drafted 2026-04-17. ~22.5k znaków polskich. 4 [REVIEW] flags. Dual-corpus framing §4.1.2.0 + aoestats §4.1.2.1 + aoe2companion §4.1.2.2 + closing forward-ref to §4.1.3. Tabela 4.2 + 4.3 (CONSORT flows) present. **2026-04-19:** cohort ceiling paragraph added (Residual #4 of CHAPTER_4_DEFEND_IN_THESIS — 744 graczy @ N=10 w oknie patch 66692; sensitivity axis N ∈ {5, 10, 20}); flag count 4 → 6. **2026-04-19:** `[PRE-canonical_slot]` footnote added at team=1 52,27% sentence (Residual #5); flag count 6 → 7. |
| §4.1.3 Data asymmetry acknowledgement | `DRAFTED` | Phase 01 (cross-corpus synthesis) | Drafted 2026-04-17. ~5.7k znaków polskich. 1 [REVIEW] flag. Hosts canonical Tabela 4.4a (Skala i akwizycja) + Tabela 4.4b (Asymetria analityczna). 3 new bibtex entries added: Rubin1976, vanBuuren2018, SchaferGraham2002. **2026-04-19:** defense paragraph added for reference-window asymmetry (Residual #1 of CHAPTER_4_DEFEND_IN_THESIS — `Ramy okna referencyjnego`, cytujący spec §7 + §11 W3 ARTEFACT_EDGE); flag count 1 → 2. |
| §4.1.4 Zakres populacji — ramy porównawcze dataset-conditional | `DRAFTED` | Phase 01 (cross-corpus synthesis) | Drafted 2026-04-19 via Residual #2 of CHAPTER_4_DEFEND_IN_THESIS. ~2.1k znaków polskich (header + 2 akapity). 2 [REVIEW] flags. Scopes all cross-dataset claims in §4.4 as dataset-conditional per invariant #8. Honest-match to artifact state: sc2egset + aoe2companion carry explicit `[POP:]` tag (35/35 + 74/74 rows); aoestats does NOT (137 rows, 0 tags) — scope implicit via spec §0 + cleaning rule R02 (`leaderboard = 'random_map'`). Rozdźwięk artefakt-spec deferred as Category-D in `planning/BACKLOG.md` F6 per B1 resolution. |
| §4.2.1 Ingestion i walidacja | `DRAFTED` | Phase 01 (Data Exploration, sections 01_01–01_02 all three corpora) | Drafted 2026-04-18. ~6.8k znaków polskich. 1 [REVIEW] flag. No new bib entries (all reused). Argues two-path ingestion (SC2 nested-JSON→DuckDB; aoestats union_by_name variant-Parquet; aoe2companion Parquet+CSV) as preprocessing decision; defends I6/I9/I10. |
| §4.2.2 Rozpoznanie tożsamości gracza | `REVISED` | Phase 01 (Data Exploration, sections 01_02–01_04 all three corpora + each dataset's INVARIANTS.md §2) | Drafted 2026-04-18. **Revised 2026-04-19 via F3 (closes BACKLOG F3; plan `planning/current_plan.md`).** ~9.5k znaków polskich (grown from 7.5k by F3 rewrite). 4 [REVIEW] flags (2 new + 2 retained; 1 pruned). Bib entries (no new): FellegiSunter1969, Christen2012DataMatching. Paragraphs 2–4 rewritten to reflect I2 extended 5-branch procedure (`.claude/scientific-invariants.md:31–127`): (a) Formal operationalisation bridging Fellegi–Sunter → *a priori* schema selection; (b) sc2egset Branch (iii) `player_id_worldwide`; (c) aoe2companion Branch (i) `profileId`; (d) aoestats Branch (v) structurally-forced + cross-dataset aoec namespace bridge; (e) Branch (ii) framework-completeness note. Paragraph 1 preserved; paragraph 5 retained + cross-ref sentence added; Forward reference preserved with revised flag wording. Tabela 4.5 row `Plan Phase 02 (I2)` renamed to `Klucz kanoniczny (I2 §2)` with per-corpus branch values from INVARIANTS.md §2. aoe2companion rates 2,57% / 3,55% post-rm_1v1-scope reconciliation (2026-04-19). |
| §4.2.3 Reguły czyszczenia i ważny korpus | `DRAFTED` | Phase 01 (Data Exploration, section 01_04 all three corpora) | Drafted 2026-04-18. ~13.2k znaków polskich. 3 [REVIEW] flags. Bib entries added: Jakobsen2017, MadleyDowd2019. Tabela 4.6 typology (8 rows × 3 corpora) + Tabela 4.6a singleton footnote. MissingIndicator I3-compliance defence; Madley-Dowd 2019 rebuttal (Phase 01 fold-agnostic). I7 threshold provenance: 5% Schafer & Graham 2002; 40% Jakobsen 2017; 80% operational heuristic. MMR MAR-primary / MNAR-sensitivity per ledger. DS-AOEC-04 "exception" phrasing prose acknowledgment (cosmetic taxonomy divergence, not routing error). |
| §4.4.4 Evaluation metrics | `DRAFTED` | — | Literature; Pass 1 draft (2026-04-19) via DEFEND-IN-THESIS Residual #6. ~3.5k znaków polskich. 2 [REVIEW] flags. Reused §2.6 bibkeys: Brier1950, Murphy1973, HanleyMcNeil1982, Friedman1937, Wilcoxon1945, Holm1979, Benavoli2017, Dietterich1998, Nadeau2003, Demsar2006, Gneiting2007, GarciaHerrera2008 (no new bib). 4 bolded subsections (Metryki podstawowe / Metryki dyskryminacyjne / Analizy stratyfikowane / Porównanie within-game i cross-game). Residual #6 N=2 Friedman-inapplicable argument absorbed into subsection (d) closing paragraph, cited Demsar2006 §3.2 corollary + invariant #8. |
| §4.4.5 Wybór estymatora ICC | `DRAFTED` | Phase 01 (cross-corpus ICC artifacts: sc2egset `icc.json`; aoe2companion `01_05_05_icc.json`; aoestats `01_05_05_icc_results.json`) | Drafted 2026-04-19 via DEFEND-IN-THESIS Residual #3 + #4-identification. ~4.7k znaków polskich. 4 [REVIEW] flags. 5 new bib entries added: Nakagawa2017, Chung2013, Ukoumunne2003, WuCrespiWong2012, Gelman2007. 4 bolded subsections (Motywacja / Wybór observed-scale vs latent-scale / REML boundary-shrinkage i primary-estimator fallback / Identyfikacja przy małych kohortach). Tabela 4.7 (3 datasets × 5 columns: korpus, ICC punktowa, 95% CI, N graczy, N obs., metoda CI) cytująca v1.0.4 §14(b). Closes §4.1.2.1 forward-ref (aoestats 744-gracz cohort, Gelman2007 §11-12) and §4.1.4 forward-ref. Nakagawa 2017 latent-scale ICC cytowany wyłącznie jako argument kierunkowy lower-bound (observed-scale ≤ latent-scale under logit link with small between-cluster variance), bez plug-in formuły (B1 fix). Sc2egset metoda CI jest [UNVERIFIED] w Tabeli 4.7 — JSON `icc.json` nie nazywa metody explicite (m1/m1-M1 ostrzeżenia z critique). |
| §4.4.6 Flaga `[PRE-canonical_slot]` dla aoestats per-slot analyz | `DRAFTED` | Phase 01 (01_05 W3 ARTEFACT_EDGE finding + spec §11 binding) | Drafted 2026-04-19 via DEFEND-IN-THESIS Residual #5. ~5.2k znaków polskich. 2 [REVIEW] flags. Definiuje scope flagi `[PRE-canonical_slot]` (per-slot vs. aggregate); cross-refs BACKLOG F1 (Phase 02 unblocker) i F6 (artefact backfill). M1 fix (reviewer-adversarial round 1): rozróżnienie raw-schema `p0_civ`/`p1_civ` w `matches_1v1_clean` vs. post-Phase-02 UNION-ALL aggregate `faction`/`opponent_faction`/`won` per-gracz uczynione explicite. Invariant I5 (symmetric player treatment) cytowany w formie krótkiej (m3 fix). Honest-match do stanu artefaktu: `grep '[PRE-canonical_slot]'` = 0 dopasowań na 137 wierszach `phase06_interface_aoestats.csv`; flaga pozostaje konwencją metodologiczną na poziomie spec §1 linia 71, zamknięcie operacyjne via BACKLOG F6. |

Remaining 4 sections all `BLOCKED` — waiting on Phase 02–04 (SC2) and AoE2 roadmap phases.

## Chapter 5 — Experiments and Results

All 6 sections `BLOCKED` — waiting on Phases 03-05 (SC2) and AoE2 phases.

## Chapter 6 — Discussion

| Section | Status | Feeds from | Notes |
|---------|--------|------------|-------|
| §6.5 Threats to validity | `DRAFTABLE` | — | Start listing known threats; expand after experiments |

Remaining 4 sections all `BLOCKED` — waiting on Chapter 5.

## Chapter 7 — Conclusions

| Section | Status | Feeds from | Notes |
|---------|--------|------------|-------|
| §7.3 Future work | `DRAFTABLE` | — | Accumulate ideas; finalize last |

Remaining 2 sections all `BLOCKED` — waiting on Chapters 5–6.

## Appendices

| Section | Status | Feeds from | Notes |
|---------|--------|------------|-------|
| Appendix E — Code repository | `SKELETON` | — | Repo structure description |

Remaining 4 appendices all `BLOCKED` — waiting on Phase 01–05 artifacts.
