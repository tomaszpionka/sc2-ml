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

### §4.1 claims (SC2EGSet and AoE2 corpus descriptions)

See `sec_4_1_crosswalk.md` — frozen v1 crosswalk with 101 rows covering all §4.1.1, §4.1.2,
and §4.1.3 prose numbers. Zero halt events at creation; all numbers grounded per
`sec_4_1_halt_log.md`.

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
