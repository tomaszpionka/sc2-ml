# Dependency Lineage Audit
Generated: 2026-04-26 by T03 executor (thesis/audit-methodology-lineage-cleanup).

Purpose: Full dependency map from every empirical thesis claim (Chapters 1–4) to its upstream
artifact, notebook, ROADMAP Step, research_log entry, and STEP_STATUS. Status classification
uses the five-class vocabulary: **intact / stale / missing / contradictory / prose-only**.

Edit-class vocabulary (§8 of planning/current_plan.md):
- **A** = thesis-only wording change
- **B** = artifact interpretation change
- **C** = notebook logic change
- **D** = Step design change
- **E** = cross-dataset decision

---

## Pass-2-evidence file relationships

**Strategy: Option B SUPPLEMENT (selected per plan T03 instruction 6)**

The existing v1 Chapter 4 crosswalks (`sec_4_1_crosswalk.md` and `sec_4_2_crosswalk.md`) are
**frozen** per the Pass-2 handoff convention in `thesis/pass2_evidence/README.md`. They are
not mutated, deleted, or replaced.

The new `claim_evidence_matrix.md` (created in this same T03 execution) is a **global
cross-chapter index** covering Chapters 1–3 in detail and **pointing at** the existing v1
crosswalks for Chapter 4 specifics. It does not duplicate Chapter 4 row content.

If T11 (or any downstream task) identifies Chapter 4 numbers requiring new crosswalk entries
beyond what the v1 crosswalks cover, a new file `sec_4_1_v2_crosswalk.md` or
`sec_4_2_v2_crosswalk.md` shall be created per the README versioning convention — the v1 files
shall not be edited.

This decision (Option B SUPPLEMENT) is the binding strategy for any future thesis Pass-2
evidence file creation on this PR.

---

## Taxonomy summary (from docs/TAXONOMY.md)

| Unit | Definition | Identifier format |
|------|-----------|-------------------|
| Phase | One lifecycle manual's worth of work | `01` … `NN` |
| Pipeline Section | Top-level section within a Phase | `{PH}_{PS}` e.g. `01_02` |
| Step | Atomic leaf: one notebook + artifacts | `{PH}_{PS}_{ST}` e.g. `01_02_04` |
| Sandbox notebook | Jupytext `.py` + paired `.ipynb` | `sandbox/<game>/<dataset>/{phase_dir}/{section_dir}/{step_id}_{slug}.py` |
| Artifact | Output under `reports/artifacts/` | mirrors sandbox path |
| Research log | Per-dataset reverse-chronological narrative | `reports/research_log.md` |
| Thesis mapping | Step YAML `thesis_mapping:` field | Chapter §N.N |

All three active datasets (sc2egset, aoestats, aoe2companion) have completed Phase 01 through
Pipeline Section 01_06 as of 2026-04-19. Phase 02+ has not started for any dataset.

---

## Step status summary (all datasets, Phase 01 only)

All steps listed below are `complete` per their respective `STEP_STATUS.yaml` files.

| Dataset | Phase | Steps complete | Steps not_started / in_progress |
|---------|-------|---------------|----------------------------------|
| sc2egset | 01 | 29 (01_01_01 … 01_06_04, including 01_04_04b, 01_05_08, 01_05_09) | 0 |
| aoestats | 01 | 28 (01_01_01 … 01_06_04, including 01_04_05) | 0 |
| aoe2companion | 01 | 28 (01_01_01 … 01_06_04) | 0 |
| **Phase 02+** | **all** | **0** | **all (not started)** |

---

## Chapter 1 — Introduction: empirical claim map

All Chapter 1 claims are either literature-derived (framing claims) or forward-references to
Chapter 4 empirical data. True empirical claims with artifact dependency are limited.

| # | Thesis file + section | Exact claim | Prose location | Claimed value | Artifact path | Notebook path | ROADMAP Step | Research log | STEP_STATUS | Status | Edit class |
|---|----------------------|-------------|---------------|---------------|--------------|--------------|-------------|-------------|------------|--------|------------|
| C1-01 | 01_introduction.md §1.1 | 50 asymetrycznych cywilizacji w trybie rankingowym w analizowanym oknie | Line 13 | 50 | INVARIANTS.md:10 (aoestats) + aoestats p0_civ n_distinct=50 per sec_4_1_crosswalk row | sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_01_data_cleaning.py | 01_04_01 (aoestats) | aoestats research_log.md 2026-04-16 | complete | intact | A |
| C1-02 | 01_introduction.md §1.1 | 1 225 unikalnych par cywilizacji ($\binom{50}{2}$) | Line 15 | 1225 | Derivation from C1-01; no separate artifact | — | — | — | — | intact (derivation) | A |
| C1-03 | 01_introduction.md §1.3 | RQ1 hypothesis: GBDT advantage, margin 2–5 pp over baseline | Line 31 | 2–5 pp | No empirical artifact yet (Phase 02+ BLOCKED) | — | Phase 03/04 (not started) | — | not_started | prose-only | A |
| C1-04 | 01_introduction.md §1.4 | AoE2 civ count 50 in corpus window 2022-08-28 — 2026-02-07 | Line 45 | 50 / 1225 | Same as C1-01 | Same as C1-01 | 01_04_01 (aoestats) | aoestats research_log.md 2026-04-16 | complete | intact | A |

**Chapter 1 empirical claims: 4. All prose-only or intact (no Phase 02+ claims presented as established fact).**

---

## Chapter 2 — Theoretical Background: empirical claim map

Most Chapter 2 claims are literature-derived. Empirical claims reference Phase 01 findings that
were migrated into §2.2 prose ("instrumental" uses per sec_4_1_crosswalk.md §catalog).

| # | Thesis file + section | Exact claim | Prose location | Claimed value | Artifact path | Notebook path | ROADMAP Step | Research log | STEP_STATUS | Status | Edit class |
|---|----------------------|-------------|---------------|---------------|--------------|--------------|-------------|-------------|------------|--------|------------|
| C2-01 | 02_theoretical_background.md §2.2.1 | 555 zestawień z selectedRace='' (Random) | §2.2.1 body | 555 | artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.md (sc2egset) | sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_02_true_1v1_identification.py | 01_03_02 (sc2egset) | sc2egset research_log.md 2026-04-16 | complete | intact |  A |
| C2-02 | 02_theoretical_background.md §2.2.2 | SC2EGSet rozciąga się na lata 2016–2024 | §2.2.2 line 33 | 2016–2024 | artifacts/01_exploration/02_eda/01_02_04_univariate_census.md (sc2egset) | sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py | 01_02_04 (sc2egset) | sc2egset research_log.md 2026-04-14 | complete | intact | A |
| C2-03 | 02_theoretical_background.md §2.2.2 | 188 unikalnych nazw map | §2.2.2 | 188 | artifacts/01_exploration/02_eda/01_02_04_univariate_census.md (sc2egset) | Same as C2-02 | 01_02_04 (sc2egset) | sc2egset research_log.md 2026-04-14 | complete | intact | A |
| C2-04 | 02_theoretical_background.md §2.2.4 | tracker_events_raw 62 003 411 zdarzeń | §2.2.4 | 62003411 | artifacts/01_exploration/03_profiling/01_03_04_event_profiling.md (sc2egset) | sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_04_event_profiling.py | 01_03_04 (sc2egset) | sc2egset research_log.md 2026-04-15 | complete | intact | A |
| C2-05 | 02_theoretical_background.md §2.2.4 | game_events_raw 608 618 823 zdarzeń | §2.2.4 | 608618823 | Same artifact as C2-04 | Same as C2-04 | 01_03_04 (sc2egset) | sc2egset research_log.md 2026-04-15 | complete | intact | A |
| C2-06 | 02_theoretical_background.md §2.2.4 | message_events_raw 52 167 zdarzeń | §2.2.4 | 52167 | Same artifact as C2-04 | Same as C2-04 | 01_03_04 (sc2egset) | sc2egset research_log.md 2026-04-15 | complete | intact | A |
| C2-07 | 02_theoretical_background.md §2.2.4 | PlayerStats period 160 loops / ~7,14 s at Faster | §2.2.4 | 160 / 7.14 | Same artifact as C2-04 | Same as C2-04 | 01_03_04 (sc2egset) | sc2egset research_log.md 2026-04-15 | complete | intact (hedging_needed per crosswalk: rounded) | A |
| C2-08 | 02_theoretical_background.md §2.2.4 | 22,4 game loops/s at Faster | §2.2.4 | 22.4 | Liquipedia_GameSpeed (grey-lit); Vinyals2017 (peer-reviewed secondary anchor) | — | — (literature) | — | — | intact (grey-lit flag; [REVIEW] open) | A |
| C2-09 | 02_theoretical_background.md §2.3.2 | 50 cywilizacji w oknie 2022-08-28 — 2026-02-07 | §2.3.2 line 69 | 50 | Same as C1-01 | Same as C1-01 | 01_04_01 (aoestats) | aoestats research_log.md 2026-04-16 | complete | intact | A |
| C2-10 | 02_theoretical_background.md §2.2.3 | Aligulac FAQ ~80% (kalibracja, nie trafność) | §2.2.3 | ~80% | External: Aligulac FAQ (grey-lit self-validation) | — | — (literature) | — | — | intact ([REVIEW] F4.5 open — Thorrez2024 Table 2 exact value pending) | A |
| C2-11 | 02_theoretical_background.md §2.2.3 | Thorrez2024 Glicko-2 80,13% na 411 030 SC2 meczach | §2.2.3 | 80.13% | External: Thorrez2024 preprint Table 2 (WebFetch partial; [REVIEW] F4.5 flag open) | — | — (literature) | — | — | intact ([REVIEW] F4.5 open — exact value + preferred row unconfirmed) | A |

**Chapter 2 empirical claims: 11. All intact or literature-grounded with open [REVIEW] flags.**

---

## Chapter 3 — Related Work: empirical claim map

Chapter 3 is a literature survey. No artifacts from this repo's pipeline feed Chapter 3 numbers.
All claims below are literature-attributed.

| # | Thesis file + section | Exact claim | Prose location | Claimed value | Artifact path | Notebook path | ROADMAP Step | Research log | STEP_STATUS | Status | Edit class |
|---|----------------------|-------------|---------------|---------------|--------------|--------------|-------------|-------------|------------|--------|------------|
| C3-01 | 03_related_work.md §3.2.2 | SC2EGSet 17 930 plików / 55 turniejów 2016–2024 | §3.2.2 body | 17930 / 55 | Forward-ref to §4.1.3 Tabela 4.4a (actual §4.1.1 artifact: 22390 files / 70 dirs) | — | 01_01_01 (sc2egset) | sc2egset research_log.md 2026-04-09 | complete | **stale** — 17930 / 55 appears to be an earlier count pre-dating 22390 / 70 from 01_01_01_file_inventory.md; §4.1.3 Tabela 4.4a has 22390 files. This is a prose inconsistency between §3.2.2 and §4.1.3. | A |
| C3-02 | 03_related_work.md §3.2.4 | EsportsBench v8.0 (cutoff 2025-12-31) Glicko-2 ~80% (exact 80,13% [REVIEW]) | §3.2.4 | 80.13% / v8.0 | External: Thorrez2024 preprint; [REVIEW] flag open | — | — (literature) | — | — | intact ([REVIEW] open — same as C2-11) | A |
| C3-03 | 03_related_work.md §3.2.4 | EsportsBench lists SC2, SC1, WC3 but NOT AoE2 | §3.2.4 | absence | External: EsportsBench HuggingFace v8.0 title list (verified 2026-04-20 in PR-TG3) | — | — (literature) | — | — | intact | A |
| C3-04 | 03_related_work.md §3.3.1 | Yang2017Dota: 58,69% pre-game / 71,49% full history / 93,73% at 40min | §3.3.1 | 58.69 / 71.49 / 93.73% | External: arXiv:1701.03162; [REVIEW: F6.7] flag for split semantics + numeric attribution open | — | — (literature) | — | — | intact ([REVIEW] F6.7 open — PDF read pending for 9:1 random vs temporal split) | A |
| C3-05 | 03_related_work.md §3.3.1 | Hodge2021 LightGBM 85% at 5 min Dota 2 | §3.3.1 | 85% at 5 min | External: Hodge2021 IEEE Trans. Games | — | — (literature) | — | — | intact | A |
| C3-06 | 03_related_work.md §3.2.3 | BaekKim2022 3D-ResNet 88,6% TvP max trafność | §3.2.3 | 88.6% | External: BaekKim2022 PLOS ONE | — | — (literature) | — | — | intact | A |
| C3-07 | 03_related_work.md §3.4.1 | CetinTas2023 trafność ~86% | §3.4.1 | ~86% | External: CetinTas2023 IEEE UBMK 2023; [REVIEW] IEEE Xplore primary-source verification pending | — | — (literature) | — | — | intact ([REVIEW] open) | A |
| C3-08 | 03_related_work.md §3.4.2 | Lin2024NCT 1 261 288 meczów AoE2 z aoestats.io | §3.4.2 | 1261288 | External: arXiv:2408.17180; [REVIEW] pending verification | — | — (literature) | — | — | intact ([REVIEW] open) | A |

**Chapter 3 empirical claims: 8. One stale claim (C3-01: file count 17930/55 vs artifact 22390/70). Remainder are literature-grounded with some [REVIEW] flags open.**

**Stale-Step count contribution from Chapter 3: 0 Steps (C3-01 is a prose inconsistency fixable by class A edit — no Step redesign needed).**

---

## Chapter 4 — Data and Methodology: empirical claim map

Chapter 4 contains the highest density of empirical claims. Claims in §4.1–§4.2 are fully
covered by `sec_4_1_crosswalk.md` (101 rows) and `sec_4_2_crosswalk.md` (48 main rows + 16
overlap + 10 identity-check + 4 bib). Rather than duplicating those 179 rows here, this audit:

1. Confirms the crosswalk files exist and were created from correct artifact chains.
2. Identifies any Chapter 4 claims NOT covered by the v1 crosswalks (§4.4.4, §4.4.5, §4.4.6,
   §4.1.3, §4.1.4 — sections added 2026-04-19 after the crosswalk was created 2026-04-17/18).
3. Records the status of each uncovered claim.

**For Chapter 4 claims covered by v1 crosswalks:** see `sec_4_1_crosswalk.md` and
`sec_4_2_crosswalk.md` (frozen; all 101 + 48 main rows show `hedging_needed = No` except 3
rows in §4.1 and 3 rows in §4.2).

### §4.4.4 — Evaluation metrics (drafted 2026-04-19, NOT in v1 crosswalks)

All claims in §4.4.4 are methodological (candidate-list framing, protocol design) with no
numerical claims derived from pipeline artifacts. Statistical test references (Demsar2006 §3.1.3
vs §3.2 location — [REVIEW: F5.6 open]) are literature-only. Status: **prose-only** for all
§4.4.4 content.

### §4.4.5 — Wybór estymatora ICC (drafted 2026-04-19, NOT in v1 crosswalks)

| # | Thesis file + section | Exact claim | Prose location | Claimed value | Artifact path | Notebook path | ROADMAP Step | Research log | STEP_STATUS | Status | Edit class |
|---|----------------------|-------------|---------------|---------------|--------------|--------------|-------------|-------------|------------|--------|------------|
| C4-01 | 04_data_and_methodology.md §4.4.5 | sc2egset ICC ANOVA 0,0463 [0,0283; 0,0643], n=4034, n_groups=152 | Tabela 4.7 | 0.0463 / CI | artifacts/01_exploration/05_temporal_panel_eda/icc.json (sc2egset) | sandbox/sc2/sc2egset/01_exploration/05_temporal_panel_eda/01_05_05_variance_icc.py | 01_05_05 (sc2egset) | sc2egset research_log.md 2026-04-18 | complete | intact ([REVIEW] Tabela 4.7 CI method UNVERIFIED per REVIEW_QUEUE; JSON does not name CI method explicitly) | B |
| C4-02 | 04_data_and_methodology.md §4.4.5 | aoe2companion ICC ANOVA 0,003013 [0,001724; 0,004202], n_players_primary=5000, n_obs=360567 | Tabela 4.7 | 0.003013 / CI | artifacts/01_exploration/05_temporal_panel_eda/01_05_05_icc.json (aoe2companion) | sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_05_icc.py | 01_05_05 (aoe2companion) | aoe2companion research_log.md 2026-04-19 | complete | intact | B |
| C4-03 | 04_data_and_methodology.md §4.4.5 | aoestats ICC ANOVA 0,0268 [0,0148; 0,0387], n_players=744, n_obs=7909 | Tabela 4.7 | 0.0268 / CI | artifacts/01_exploration/05_temporal_panel_eda/01_05_05_icc_results.json (aoestats) | sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_05_variance_decomposition_icc.py | 01_05_05 (aoestats) | aoestats research_log.md 2026-04-18 | complete | intact | B |

### §4.4.6 — Flaga [PRE-canonical_slot] (drafted 2026-04-19, NOT in v1 crosswalks)

| # | Thesis file + section | Exact claim | Prose location | Claimed value | Artifact path | Notebook path | ROADMAP Step | Research log | STEP_STATUS | Status | Edit class |
|---|----------------------|-------------|---------------|---------------|--------------|--------------|-------------|-------------|------------|--------|------------|
| C4-04 | 04_data_and_methodology.md §4.4.6 | 80,3% / +11,9 ELO audit aoestats | §4.4.6 body | 80.3% / +11.9 | aoestats research_log.md:107 (commit ab23ab1d) | sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_05_i5_diagnosis.py | 01_04_05 (aoestats) | aoestats research_log.md 2026-04-18 | complete | intact | B |
| C4-05 | 04_data_and_methodology.md §4.4.6 | grep '[PRE-canonical_slot]' = 0 matches on 137 rows of phase06_interface_aoestats.csv | §4.4.6 honest-match paragraph | 0 matches | artifacts/01_exploration/05_temporal_panel_eda/phase06_interface_aoestats.csv (aoestats) | sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/01_05_08_phase06_interface.py | 01_05_08 (aoestats) | aoestats research_log.md 2026-04-18 | complete | intact | B |

### §4.1.3 reference-window paragraph (added 2026-04-20 F5.4, NOT in v1 crosswalks)

| # | Thesis file + section | Exact claim | Prose location | Claimed value | Artifact path | Notebook path | ROADMAP Step | Research log | STEP_STATUS | Status | Edit class |
|---|----------------------|-------------|---------------|---------------|--------------|--------------|-------------|-------------|------------|--------|------------|
| C4-06 | 04_data_and_methodology.md §4.1.3 | Patch 66692: 123 367 meczów wewnątrz / 241 981 across 14-week cycle | §4.1.3 reference-window paragraph line ~207 | 123367 / 241981 | reports/specs/01_05_preregistration.md:580–582 (aoestats) | — (spec document, not notebook artifact) | 01_05 (aoestats spec) | aoestats research_log.md 2026-04-18 | complete | intact (numbers from spec, not from notebook artifact directly — [REVIEW] open per REVIEW_QUEUE) | B |
| C4-07 | 04_data_and_methodology.md §4.1.3 | D3 role matrix: aoe2companion PRIMARY (24 quarters), aoestats SUPPLEMENTARY (9 quarters + crawler confound), sc2egset SUPPLEMENTARY (5/10 quarters, tournament-sparse) | §4.1.3 D3 row | 24 / 9 / 5-10 quarters | cross_dataset_phase01_rollup.md (reports/artifacts or temp/) | — (phase01 gate document) | 01_06_04 (all datasets) | reports/research_log.md 2026-04-19 CROSS entry | complete | intact | E |

### §4.1.4 population scope (drafted 2026-04-19, NOT in v1 crosswalks)

| # | Thesis file + section | Exact claim | Prose location | Claimed value | Artifact path | Notebook path | ROADMAP Step | Research log | STEP_STATUS | Status | Edit class |
|---|----------------------|-------------|---------------|---------------|--------------|--------------|-------------|-------------|------------|--------|------------|
| C4-08 | 04_data_and_methodology.md §4.1.4 | sc2egset: 35/35 rows carry [POP:tournament] tag | §4.1.4 honest-match paragraph | 35/35 | artifacts/01_exploration/05_temporal_panel_eda/phase06_interface_sc2egset.csv | sandbox/sc2/sc2egset/01_exploration/05_temporal_panel_eda/01_05_07_phase06_interface.py | 01_05_07 (sc2egset) | sc2egset research_log.md 2026-04-18 | complete | intact | B |
| C4-09 | 04_data_and_methodology.md §4.1.4 | aoe2companion: 74/74 rows carry [POP:ranked_ladder] tag | §4.1.4 honest-match paragraph | 74/74 | artifacts/01_exploration/05_temporal_panel_eda/01_05_phase06_interface_aoe2companion.csv | sandbox/aoe2/aoe2companion/01_exploration/05_temporal_panel_eda/01_05_07_phase06_interface.py | 01_05_07 (aoe2companion) | aoe2companion research_log.md 2026-04-19 | complete | intact | B |
| C4-10 | 04_data_and_methodology.md §4.1.4 | aoestats: 137 wierszy, [POP:] absent (implicit scope via spec §0 + R02) | §4.1.4 honest-match paragraph | 0 tags / 137 rows | artifacts/01_exploration/05_temporal_panel_eda/phase06_interface_aoestats.csv | Same as C4-05 | 01_05_08 (aoestats) | aoestats research_log.md 2026-04-18 | complete | intact (Rozdźwięk artefakt-spec deferred as Category-D per BACKLOG F6 — no blocking stale) | B |

**Chapter 4 uncovered claims (not in v1 crosswalks): 10 rows (C4-01 through C4-10). All intact.**
**Chapter 4 v1 crosswalk claims: 101 (§4.1) + 48 main (§4.2) = 149 rows. Per halt_log files: zero halt events, all numbers grounded at time of creation.**

---

## Stale-Step count across all three datasets

A "potentially stale Step" = a Step whose artifact is classified as stale, missing, or contradictory
in the claim map above.

### Inventory by classification

| Step | Dataset | Linked claim(s) | Status of artifact claim | Potentially stale? |
|------|---------|----------------|------------------------|-------------------|
| All Phase 01 steps (01_01_01 – 01_06_04) | sc2egset | C2-01 through C2-08, C4-01, C4-08; sec_4_1 + sec_4_2 crosswalk rows | intact | NO |
| All Phase 01 steps (01_01_01 – 01_06_04) | aoestats | C1-01, C1-04, C2-09, C4-03–C4-07, C4-10 | intact | NO |
| All Phase 01 steps (01_01_01 – 01_06_04) | aoe2companion | C4-02, C4-09 | intact | NO |
| Prose claim C3-01 (17930/55 in §3.2.2) | sc2egset (no Step tie) | File count 17930 vs artifact 22390 | **stale prose** — prose inconsistency in §3.2.2; no Step stale | NO Step stale; prose fix is class A edit |

**Potentially stale Steps = 0 across all three datasets.**

The one stale finding (C3-01) is a prose inconsistency in §3.2.2 — the artifact (01_01_01) is
intact and correct (22390 files / 70 dirs); only the prose in §3.2.2 carries an outdated number.
No Step regeneration is needed. This is a class A (thesis-only wording change) edit.

---

## Scope-explosion escape valve evaluation

**Stale + missing + contradictory Steps across all three datasets combined: 0**

Threshold is 10. **Threshold NOT exceeded. Escape valve does NOT fire.**

The `audit_cleanup_summary.md` "Scope-explosion escalation" section is NOT triggered and NOT
added.

---

## Overall claim count summary

| Chapter | Claims audited | intact | stale | missing | contradictory | prose-only |
|---------|---------------|--------|-------|---------|---------------|------------|
| 1 | 4 | 2 | 0 | 0 | 0 | 2 |
| 2 | 11 | 11 | 0 | 0 | 0 | 0 |
| 3 | 8 | 7 | 1 | 0 | 0 | 0 |
| 4 | 10 (uncovered by v1 crosswalks) + 149 (v1 crosswalks) = 159 | 159 | 0 | 0 | 0 | 0 |
| **Total** | **182** | **179** | **1** | **0** | **0** | **2** |

Note: Chapter 4 v1 crosswalk rows (149) are recorded as intact here based on the halt_log
attestations (zero halt events at crosswalk creation time). The 10 post-crosswalk Chapter 4 claims
are individually audited in the tables above.

**One stale claim (C3-01 in §3.2.2)** is a prose inconsistency requiring a class A wording fix
(17930/55 → 22390/70, or restructured as forward-ref to §4.1.3). No artifact or Step is stale.

---

## Chapters 5–7 status note

Chapters 5–7 are BLOCKED on Phases 02–05 (sc2egset) and equivalent AoE2 phases. No empirical
claims exist in these chapters yet. They are outside T03 scope.
