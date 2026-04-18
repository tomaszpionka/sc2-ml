# Research Log

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

This log contains CROSS-dataset entries only. Dataset-specific findings
live in per-dataset logs — one per game/dataset combination.

| Dataset | Log | Last entry |
|---------|-----|------------|
| sc2 / sc2egset | [sc2egset research log](../src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md) | 2026-04-16 (01_04_00) |
| aoe2 / aoe2companion | [aoe2companion research log](../src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md) | 2026-04-18 (01_04_04) |
| aoe2 / aoestats | [aoestats research log](../src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md) | 2026-04-16 (01_04_00) |

---

## [CROSS] 2026-04-18 — [Phase 01 / Step 01_04_04] Identity Resolution — aoec/aoestats shared namespace confirmed

**Source:** aoe2companion 01_04_04 (this step); aoestats cross-dataset feasibility preview
**Invariant:** I8 (cross-game comparability via shared identity namespace)

**Finding:** aoec `profileId` (INTEGER) and aoestats `profile_id` (DOUBLE/BIGINT) share the
same namespace (both sourced from the aoe2insights.com API).

Empirical evidence (2026-01-25..2026-01-31 window, rm_1v1 filter both sides):
- Full-window: 100% of aoestats profiles (28,921) appear in aoec matches_raw.
- Reservoir sample (1,000 aoec matches, seed=20260418): p_hat=0.8818, 95% CI=[0.8671, 0.8964].
- VERDICT A: STRONG -- CI lower bound (0.867) > 0.50 threshold.

**Implication for Phase 02:**
1. aoestats (which has no name column) can obtain I2-compliant canonical nicknames via
   a LEFT JOIN on `aoec.matches_raw.profileId = aoestats.players_raw.profile_id`.
2. Both AoE2 datasets may use `profileId`/`profile_id` as the Phase 02 primary identity key.
3. A formal cross-dataset identity mapping table is feasible (deferred until Phase 02 scope is set).

**Pending:** aoestats 01_04_04 executor must confirm the same VERDICT (per plan cross-dataset
gate 6: "aoestats T03 and aoec T06 feasibility verdicts agree"). If aoestats executor finds
VERDICT B or C, dispatch adversarial review per plan gate instructions.

---

## [CROSS] 2026-04-16 — [Phase 01 / Step 01_04_00] Canonical long skeleton normalization

Schema: 10 columns (match_id, started_timestamp, side, player_id,
chosen_civ_or_race, outcome_raw, rating_pre_raw, map_id_raw, patch_raw, leaderboard_raw)

All three datasets now expose a structurally identical long skeleton VIEW (`matches_long_raw`).
Downstream cleaning in all datasets operates against this common 10-column contract.

  - **aoe2companion:** 277,099,059 rows (lossless from matches_raw).
    Full dataset: side=0 449 rows win_pct=4.45% (source encoding artifact; team=0 is not a 1v1 side).
    side=1 win_pct=49.58%.
    1v1 scoped (leaderboard_raw IN (6, 18)): side=0 29,921,254 rows win_pct=47.18%;
    side=1 29,920,914 rows win_pct=52.81%. ~5pp slot asymmetry documented, deferred to Phase 02.
    leaderboard_raw = internalLeaderboardId (INTEGER); 1v1 values: 6 (rm_1v1), 18 (qp_rm_1v1).
    patch_raw = NULL (no patch column in source).

  - **aoestats:** 107,626,399 rows (lossless via independent anchor: 107,627,584 - 1,185 null_profile - 0 orphans).
    side 0 win_pct = 48.97% (53,813,160 rows).
    side 1 win_pct = 51.03% (53,813,239 rows).
    1v1 scoped (leaderboard_raw = 'random_map'): side 0 win_pct = 47.73%, side 1 win_pct = 52.27%.
    Known asymmetry from 01_04_01 confirmed.
    leaderboard_raw = leaderboard (VARCHAR); 1v1 value: 'random_map'.

  - **sc2egset:** 44,817 rows (lossless JOIN count).
    side 0 win_pct = 51.96% (22,390 rows, 13 null outcome).
    side 1 win_pct = 47.97% (22,387 rows, 13 null outcome).
    Mild asymmetry (3.99pp deviation, below 10pp alert threshold). Documented, not corrected.
    leaderboard_raw = NULL (tournament data, no matchmaking ladder).
    started_timestamp type = VARCHAR (details.timeUTC); type unification deferred to Phase 02.

> **Phase migration note (2026-04-09):** This log was reset as part of the
> Phase 01-07 migration. Prior entries were removed in v2.0.0 (archive
> cleanup); historical context is preserved in git history.
> All new entries use the Phase XX / Step XX_YY_ZZ format per docs/PHASES.md.

---

## CROSS-Dataset Entries

---

## 2026-04-15 -- [CROSS] [Phase 01 / Step 01_03_04] In-game event data asymmetry

**Datasets affected:** sc2egset (has event data), aoe2companion and aoestats (no equivalent)

SC2EGSet provides three in-game event streams: tracker_events_raw (62M rows,
10 types), game_events_raw (608M rows, 23 types), message_events_raw (52K rows,
3 types). Deep profiling confirms PlayerStats fires at a 160-loop periodic
interval (per player), UnitBorn spans 232 distinct unit types, and Cmd/SelectionDelta
carry structured action data.

Neither AoE2 dataset has in-game event logs. This asymmetry is the controlled
experimental variable for Invariant #8: "Do the same methods work equally well
with and without in-game data?" Pre-game feature sets can be compared directly;
SC2 additionally enables in-game feature comparison.

---

## 2026-04-14 -- [Phase 01 / Step 01_02_02] Invariant I10 fix: inline filename relativization

**Datasets affected:** aoe2companion, aoestats (sc2egset was already correct)

### What

Both AoE2 dataset ingestion modules (`ingestion.py`) were storing absolute file paths in the `filename` provenance column, violating Invariant I10. The fix was applied to all CTAS and INSERT queries by replacing `SELECT *` with `SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)`, where `prefix_len = len(str(raw_dir)) + 2`.

### Why this approach

The original fix used a post-load `UPDATE SET filename = substr(filename, prefix_len)`. This caused `OutOfMemoryException` on aoestats `players_raw` (107.6M rows) and would have done the same on aoe2companion `matches_raw` (277M rows). Moving the transformation inline into the SELECT means DuckDB writes relative paths on the first pass — no second pass over the full table.

sc2egset already handled this correctly via explicit `substr(filename, {prefix_len}) AS filename` in its column list (it cannot use `SELECT *` due to its custom schema).

### Protocol decision (applies to all future datasets)

**Never use a post-load UPDATE to relativize filenames.** Always use `SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)` inline in the CTAS/INSERT query. This is the canonical I10 implementation for AoE2 ingestion going forward.

### Additional fix: aoestats OOM (file-level batching)

aoestats `load_matches_raw` and `load_players_raw` now load in file-level batches (default `batch_size=10`): `CREATE TABLE ... AS SELECT` for the first batch, `INSERT INTO ... BY NAME SELECT` for subsequent batches. This mirrors the per-tournament batching sc2egset uses for `replays_meta_raw`. Peak RSS stays manageable regardless of total file count.

### Additional fix: aoestats table rename

aoestats tables were renamed from `raw_matches`/`raw_players`/`raw_overviews` → `matches_raw`/`players_raw`/`overviews_raw` to align with the `*_raw` suffix convention used across all datasets.

### References

- aoestats ingestion: `src/rts_predict/games/aoe2/datasets/aoestats/ingestion.py`
- aoe2companion ingestion: `src/rts_predict/games/aoe2/datasets/aoe2companion/ingestion.py`
- Per-dataset entries: aoestats 01_02_02, aoe2companion 01_02_02

---

## [CROSS] 2026-04-18 — §4.2 Data preprocessing draft + §4.1 MMR classification repair

**Primary scope:** Drafted §4.2.1 (Ingestion i walidacja, ~6.8k chars), §4.2.2 (Rozpoznanie tożsamości gracza, ~7.5k chars), §4.2.3 (Reguły czyszczenia i ważny korpus, ~13.2k chars) in `thesis/chapters/04_data_and_methodology.md`, combined ~27.5k Polish chars within plan target 24.0–30.5k. Produced `thesis/pass2_evidence/sec_4_2_crosswalk.md` (78 rows: 48 main + 10 identity-check + 16 scope-overlap + 4 classification) and `thesis/pass2_evidence/sec_4_2_halt_log.md` (zero halt events).

**Secondary scope (§4.1 MMR MAR/MNAR repair per plan B1 closure):** Repaired §4.1.1.4 line 41 narrative and Tabela 4.4b line 195 cell to MAR-primary / MNAR-sensitivity classification per ledger row 35 of `01_04_01_missingness_ledger.csv`. §4.1 previously stated "MNAR" standalone; §4.2.3 commits to MAR-primary, with MNAR retained as documented sensitivity branch. Routing action (DROP_COLUMN + MissingIndicator at ≥80%) invariant under both classifications.

**New bib entries added to `thesis/references.bib`:** 4 total.
(a) `FellegiSunter1969` — JASA 64(328):1183–1210 (DOI 10.1080/01621459.1969.10501049), §4.2.2 classical record-linkage framing.
(b) `Christen2012DataMatching` — Springer, ISBN 978-3-642-31163-5, §4.2.2 standard introductory textbook per W1 reframe.
(c) `Jakobsen2017` — BMC Med Res Method 17:162 (DOI 10.1186/s12874-017-0442-1), §4.2.3 40% threshold peer-reviewed anchor (per R2 N2).
(d) `MadleyDowd2019` — J Clin Epidemiol 110:63–73 (DOI 10.1016/j.jclinepi.2019.02.016), §4.2.3 FMI-based-routing rebuttal subject (per R2 N2).
`Wilson2017GoodEnough` DEFERRED to Appendix A per W2 (not added to body).

**Structural decisions:** Tabela 4.6 restructured per W3 — 8 rows × 3 corpora, every non-(nd) row ≥2-dataset EXCEPT row 5 (FLAG_FOR_IMPUTATION 5–40% MAR aoe2companion-only) which is explicitly acknowledged in caption as canonical mechanism class retained for typological coherence (per R2 N5). Tabela 4.6a singleton footnote captures per-corpus specific reguły. DS-AOEC-04 "exception" phrasing acknowledged in §4.2.3 prose (~400 chars) as cosmetic taxonomy inconsistency between ledger narrative and registry band (per R2 N1); no Phase 01 artifact modification proposed (I9 discipline). Madley-Dowd 2019 rebuttal paragraph (~350 chars) argues Phase 01 fold-agnostic constraint forces rate-based routing; FMI reserved for Phase 02 (per R2 N2).

**Invariants touched:** I2 (§4.2.2 canonical-nickname deferral), I3 (§4.2.3 MissingIndicator fold-agnostic defence), I4 (§4.2.3 target-row consistency: POST_GAME exclusion + decisive-winner filter), I5 (§4.2.3 slot symmetry preserved), I6 (§4.2.1 reproducibility via single-process DuckDB), I7 (§4.2.3 threshold provenance 5/40/80% with explicit operational-heuristic status for 80%), I8 (§4.2.1+§4.2.3 unified preprocessing layer across three corpora), I9 (§4.2.1–§4.2.3 raw-table immutability, including explicit non-modification of Phase 01 artifact for DS-AOEC-04), I10 (§4.2.1 inline-CTAS canonical substr convention).

**Plan provenance:** `planning/current_plan.md` (v3 after 3-round plan-side adversarial); `temp/plan_4_2_v1.md`, `temp/plan_4_2_v2.md`, `temp/plan_4_2_v3.md`, `temp/critique_4_2_r1.md`, `temp/critique_4_2_r2.md`, `temp/r2_user_decisions.md` preserved as audit trail.

---

## [CROSS] 2026-04-18 — §3.4 AoE2 prediction literature + §3.5 Research gap (Chapter 3 closure)

**Primary scope:** Drafted §3.4 "Predykcja wyników w Age of Empires II" (~8.2k chars Polish) and §3.5 "Luka badawcza i pozycjonowanie niniejszej pracy" (~6.7k chars Polish) in `thesis/chapters/03_related_work.md`. Chapter 3 is now content-complete pending Pass 2. Combined ~14.9k Polish chars within plan target 14.5–19.0k.

**Literature sweep:** Three peer-reviewed AoE2-related papers confirmed as the complete set: CetinTas2023 (sole dedicated AoE2 1v1 outcome-prediction paper, IEEE UBMK 2023), Lin2024NCT (AoE2-adjacent balance analysis, TMLR 2024, arXiv:2408.17180), Elbert2025EC (AoE2 team-game prediction as instrument for team-player-effect identification, ACM EC'25, arXiv:2506.04475). Two grey-literature sources retained as Tier 3: Xie2020MediumAoE (~77% XGB on Voobly 1v1) and Porcpine2020EloAoE (r=0.96 Elo-linearity, aoe2.net). No new 2025–2026 peer-reviewed AoE2 prediction paper surfaced. Lin2025Online preprint (arXiv:2502.03998, RPS setting not AoE2) confirmed as single-sentence prose mention only — not added to bib.

**Bib entries added/fixed:** 4 total.
(a) `CetinTas2023` — author-list fixed: `Çetin Taş, İsmail and Müngen, Ahmet Anıl` (was placeholder "Emre and others"); booktitle corrected to "2023 8th International Conference on Computer Science and Engineering (UBMK)"; publisher added.
(b) `Elbert2025EC` — new `@inproceedings` entry. ACM EC'25, Stanford. Full paper arXiv:2506.04475 + SSRN:5283300. [REVIEW] flag in prose for citation convention (extended abstract @inproceedings vs @misc).
(c) `Xie2020MediumAoE` — new `@misc` entry. Medium blog post, Jan 2020. Tier 3 grey literature.
(d) `Porcpine2020EloAoE` — new `@misc` entry. GitHub Pages community analysis. Tier 3 grey literature.
`CircoBayesAoE` NOT added (dropped per plan W5 decision). `Lin2025Online` NOT added (preprint, prose-only mention).

**Voice calibration:** §3.4 and §3.5 drafted to match §3.1–§3.3 Polish academic register — impersonal passive, argumentative framing, anglicisms italicized on first use, no em-dashes as argumentative connectives.

**Structural decisions:** §3.4 has five sub-sections (opening + §3.4.1 CetinTas2023 + §3.4.2 Lin2024NCT + §3.4.3 Elbert2025EC + §3.4.4 Grey-lit + §3.4.5 Gap enumeration) mirroring §3.2 per-game structure. §3.5 presents four gaps mapped 1-to-1 to RQ1–RQ4. Luka 3 hedge uses full Q_adv_2 formulation: "pierwsza znana nam praca porównująca rodzinę klasyfikatorów uczenia maszynowego w zadaniu benchmarkowania metod predykcji wyniku meczu między dwiema grami RTS z jawną oceną probabilistyczną w grach 1v1".

**Key distinguishers articulated:** Elbert2025EC uses outcome prediction as instrument (not as research goal), operates on team games 2v2/3v3/4v4 (not 1v1), reports accuracy + pseudo-R² without calibration; Lin2024NCT performs balance analysis (not prediction benchmarking); CetinTas2023 operates on one game (AoE2), uses NB/DT without calibration or temporal split.

**WRITING_STATUS.md:** §3.4 and §3.5 updated from BLOCKED → DRAFTED.

**REVIEW_QUEUE.md:** Two new Pending rows added (§3.4 with 5 [REVIEW] flags; §3.5 with 1 [REVIEW] flag).

**Halt events:** Zero. No claim encountered that could not be anchored to the verified source set from T01 pre-verification.

**Flags total:** §3.4: 5 [REVIEW] (grey-lit acceptability; 86% primary-source CetinTas2023; author-list primary-source; EC'25 citation convention; acceptance-rate figure). §3.5: 1 [REVIEW] (Luka 3 novelty hedge — Pass 2 verification). Combined: 6 [REVIEW], 0 [NEEDS CITATION].

**Plan provenance:** `planning/current_plan.md` (v2 after 1-round plan-side adversarial); `temp/plan_3_4_3_5_v1.md`, `temp/critique_3_4_3_5_r1.md`, `temp/plan_3_4_3_5_v2.md` preserved as audit trail. Dispatched as fallback executor (writer-thesis agent tool-config issue); deliverables identical to plan spec.
