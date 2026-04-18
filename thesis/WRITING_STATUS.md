# Thesis Writing Status

Last updated: 2026-04-17

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
| §3.4 AoE2 prediction | `BLOCKED` | AoE2 lit review | Future |
| §3.5 Research gap | `BLOCKED` | §3.1-§3.4 | Skeleton draftable from §3.1-§3.3; full draft blocked on §3.4 (AoE2 lit review) |

## Chapter 4 — Data and Methodology

| Section | Status | Feeds from | Notes |
|---------|--------|------------|-------|
| §4.1 Opening framing + §4.1.1 SC2EGSet description | `DRAFTED` | Phase 01 (Data Exploration, sections 01_01–01_04 for sc2egset) | Drafted 2026-04-17. ~18.5k znaków polskich. 5 [REVIEW] flags. Phase 01 sections 01_01–01_04 fully cited; sections 01_05 (Temporal & Panel EDA), 01_06 (Decision Gates) deferred — flagged where claims await them. Tabela 4.1 (CONSORT flow) present. **2026-04-18: §4.1.1.4 line 41 narrative + Tabela 4.4b line 195 cell repaired to MAR-primary / MNAR-sensitivity per ledger row 35 (MMR classification consistency with §4.2.3).** |
| §4.1.2 AoE2 datasets (aoestats + aoe2companion) | `DRAFTED` | Phase 01 (Data Exploration, sections 01_01–01_04 for both AoE2 datasets) | Drafted 2026-04-17. ~22.5k znaków polskich. 4 [REVIEW] flags. Dual-corpus framing §4.1.2.0 + aoestats §4.1.2.1 + aoe2companion §4.1.2.2 + closing forward-ref to §4.1.3. Tabela 4.2 + 4.3 (CONSORT flows) present. |
| §4.1.3 Data asymmetry acknowledgement | `DRAFTED` | Phase 01 (cross-corpus synthesis) | Drafted 2026-04-17. ~5.7k znaków polskich. 1 [REVIEW] flag. Hosts canonical Tabela 4.4a (Skala i akwizycja) + Tabela 4.4b (Asymetria analityczna). 3 new bibtex entries added: Rubin1976, vanBuuren2018, SchaferGraham2002. |
| §4.2.1 Ingestion i walidacja | `DRAFTED` | Phase 01 (Data Exploration, sections 01_01–01_02 all three corpora) | Drafted 2026-04-18. ~6.8k znaków polskich. 1 [REVIEW] flag. No new bib entries (all reused). Argues two-path ingestion (SC2 nested-JSON→DuckDB; aoestats union_by_name variant-Parquet; aoe2companion Parquet+CSV) as preprocessing decision; defends I6/I9/I10. |
| §4.2.2 Rozpoznanie tożsamości gracza | `DRAFTED` | Phase 01 (Data Exploration, sections 01_02–01_03 all three corpora) | Drafted 2026-04-18. ~7.5k znaków polskich. 3 [REVIEW] flags. Bib entries added: FellegiSunter1969, Christen2012DataMatching. Classifies three identifier schemes (toon_id / profile_id / profileId), argues trust-the-ID + defer canonicalization per I2; Tabela 4.5 cross-dataset identifier matrix. |
| §4.2.3 Reguły czyszczenia i ważny korpus | `DRAFTED` | Phase 01 (Data Exploration, section 01_04 all three corpora) | Drafted 2026-04-18. ~13.2k znaków polskich. 3 [REVIEW] flags. Bib entries added: Jakobsen2017, MadleyDowd2019. Tabela 4.6 typology (8 rows × 3 corpora) + Tabela 4.6a singleton footnote. MissingIndicator I3-compliance defence; Madley-Dowd 2019 rebuttal (Phase 01 fold-agnostic). I7 threshold provenance: 5% Schafer & Graham 2002; 40% Jakobsen 2017; 80% operational heuristic. MMR MAR-primary / MNAR-sensitivity per ledger. DS-AOEC-04 "exception" phrasing prose acknowledgment (cosmetic taxonomy divergence, not routing error). |
| §4.4.4 Evaluation metrics | `DRAFTABLE` | — | Literature |

Remaining 6 sections all `BLOCKED` — waiting on Phase 01 (01_05+), Phase 02–04 (SC2) and AoE2 roadmap phases.

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
