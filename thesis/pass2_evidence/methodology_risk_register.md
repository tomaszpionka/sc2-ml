# Methodology Risk Register

**Generated:** 2026-04-26
**Task:** T10 (thesis/audit-methodology-lineage-cleanup)
**Branch:** `thesis/audit-methodology-lineage-cleanup`
**HEAD at generation:** `64e08553` (T09 cross-dataset comparability matrix commit)

---

## Top-level wording invariant

> **Thesis wording MUST NOT collapse aoestats source-specific 1v1 random-map records,
> aoe2companion mixed-mode ID 6 + ID 18 records, and SC2 professional/tournament replay
> records into one generic "ranked ladder" or "online multiplayer" population. Each
> population is structurally distinct; the thesis must reflect that distinction.**

This invariant governs Chapters 1, 2, 3, and 4 and every table, caption, and footnote
that refers to the data sources. Violations require a targeted wording fix (T11/T12/T13)
before the chapter is considered FINAL.

Specifically:
- **SC2EGSet** is a professional/tournament replay corpus. It is explicitly NOT a ranked
  ladder population: `leaderboard_raw` is NULL for 100% of SC2EGSet rows.
- **aoestats** (`leaderboard='random_map'`) is a third-party aggregation with Tier 4
  semantic opacity. Queue type (ranked vs quickplay vs custom lobby) cannot be verified
  from available external documentation.
- **aoe2companion** is a mixed-mode corpus. `internalLeaderboardId=6` (`rm_1v1`) is a
  ranked-ladder candidate (Tier 2). `internalLeaderboardId=18` (`qp_rm_1v1`) is a
  quickplay/matchmaking population (Tier 3). The combined scope must never be called
  simply "ranked ladder" without explicit qualification.

---

## Severity / likelihood vocabulary

| Term | Meaning |
|------|---------|
| **blocker** | Must be resolved before thesis chapter is final; examiner-facing factual error risk |
| **major** | Significant methodology risk; requires explicit limitation language or wording fix |
| **minor** | Moderate risk; add hedge/caveat or confirm mitigation is in place |
| **note** | Low risk; record for transparency; no required action before T11 |
| **high** | Near-certain examiner question or reproducibility challenge |
| **medium** | Plausible examiner question; conditional on examiner background |
| **low** | Unlikely to be raised unless examiner is a specialist |

---

## Risk register

---

### RISK-01 — AoE2 ranked ladder terminology: qp_rm_1v1 mis-label propagation (concrete current state)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-01 |
| **Severity** | blocker |
| **Likelihood** | high |
| **Affected thesis sections** | `thesis/chapters/04_data_and_methodology.md:177`, `:187`, `:211`, `:255`; `thesis/chapters/01_introduction.md:45` |
| **Evidence source** | `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` §5 (propagation trace, lines 362–418); `cleanup_flag_ledger.md` F-078 (blocker), F-090 (blocker); commit `9581b053` message: "fix(aoe2companion): repair Step 01_06_02 mixed-mode population wording" |
| **Mitigation already applied** | Commit `9581b053` (T07+T08): repaired the upstream artifact `data_quality_report_aoe2companion.md` R01 description from "Retain 1v1 ranked ladder only" to the correct mixed-mode wording. The generated artifact is now correct. The THESIS PROSE at the five locations listed above still carries the old mis-label. |
| **Residual uncertainty** | Thesis prose at Chapter 4 lines 177, 187, 211, 255 and Chapter 1 line 45 still uses "ranked ladder" language for the combined aoe2companion scope (ID 6 + ID 18) without qualifying that ID 18 is quickplay/matchmaking. These are confirmed locations requiring wording fix by T11/T12. |
| **Wording recommendation** | At every occurrence combining both IDs: "aoe2companion 1v1 Random Map records combining ranked (`rm_1v1`, ID 6, ~54M rows) and quickplay/matchmaking (`qp_rm_1v1`, ID 18, ~7M rows; external API documentation unavailable as of 2026-04-26)". For ID 6 alone: "aoe2companion 1v1 ranked Random Map records (`rm_1v1`, `internalLeaderboardId=6`)". |
| **Downstream task responsible** | T11 (Chapter 4 rewrites at lines 177, 187, 211, 255) -> T12 (Chapter 1 line 45) |
| **Blocking before Chapter 4 rewrite** | yes |

---

### RISK-02 — aoe2companion ID 6 + ID 18 mixed-mode population (combined scope mis-classification)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-02 |
| **Severity** | major |
| **Likelihood** | high |
| **Affected thesis sections** | `thesis/chapters/04_data_and_methodology.md:177`, `:187`, `:211`, `:255` (Tabela 4.4a, 4.4b, 4.5 population rows); `thesis/pass2_evidence/cross_dataset_comparability_matrix.md` §1 population row (aoe2companion) |
| **Evidence source** | `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` §4.2.5 (decision on combining IDs); `cross_dataset_comparability_matrix.md` §1 row "Ranked / ladder / quickplay / matchmaking status" — "Mixed: Tier 2 + Tier 3"; `cleanup_flag_ledger.md` F-090 |
| **Mitigation already applied** | T05 (commit `200d45ff`) classified the combined scope as mixed-mode and produced the four-tier ladder with canonical wording. `cross_dataset_comparability_matrix.md` (commit `64e08553`) records the distinct population characterisation. |
| **Residual uncertainty** | Thesis prose has not yet been rewritten to reflect the T05/T09 classification. The combined scope in tables still reads as "ranked ladder". Examiner may challenge the classification once aoe2companion ID-18 row counts (~7M, ~11.5% of the scope) are visible. |
| **Wording recommendation** | "1v1 Random Map records combining ranked (ID 6, ~54M rows) and quickplay/matchmaking (ID 18, ~7M rows)" — never "ranked ladder" without explicit qualification. See `aoe2_ladder_provenance_audit.md` §4.2.5 for the full recommended framing. |
| **Downstream task responsible** | T11 -> T12 |
| **Blocking before Chapter 4 rewrite** | yes |

---

### RISK-03 — aoe2companion ID 18 / qp_rm_1v1: quickplay/matchmaking status (Tier 3; external API unavailable)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-03 |
| **Severity** | major |
| **Likelihood** | medium |
| **Affected thesis sections** | `thesis/chapters/04_data_and_methodology.md` §4.1.2.2 (aoe2companion section); Tabela 4.4b row "Liczba meczów" |
| **Evidence source** | `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` §4.2.3 (on-disk evidence for ID 18 = qp_rm_1v1), §4.2.4 (external verification: all 8 URL probes returned HTTP 404 as of 2026-04-26), §4.2.4a (aoe2.net as documentation probe only, not a data source); `cleanup_flag_ledger.md` F-078 |
| **Mitigation already applied** | T05 fallback rule recorded in `aoe2_ladder_provenance_audit.md` §1: "If external documentation is ambiguous or unavailable regarding the queue semantics of an internalLeaderboardId, treat that ID as quickplay/matchmaking-derived, NOT ranked ladder." Fallback applied consistently. |
| **Residual uncertainty** | External API documentation for aoe2companion / aoe2.net leaderboard IDs is unavailable as of 2026-04-26. The ID-18 classification rests on the on-disk `qp_rm_1v1` label and the fallback rule. A future re-emergence of the aoe2.net API or a new aoe2companion source documentation could potentially overturn or confirm the classification. Snapshot date must be cited. |
| **Wording recommendation** | "quickplay/matchmaking 1v1 Random Map records (`qp_rm_1v1`, `internalLeaderboardId=18`; external API documentation unavailable as of 2026-04-26; on-disk classification retained per fallback rule)". |
| **Downstream task responsible** | T11 |
| **Blocking before Chapter 4 rewrite** | yes |

---

### RISK-04 — aoestats leaderboard='random_map' semantic opacity (Tier 4)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-04 |
| **Severity** | major |
| **Likelihood** | medium |
| **Affected thesis sections** | `thesis/chapters/04_data_and_methodology.md:177` (Tabela 4.4a aoestats row), `:255` (Tabela 4.5 "Populacja scope" aoestats row); `thesis/chapters/01_introduction.md:45`; `thesis/chapters/03_related_work.md:143` (source-specific attribution only) |
| **Evidence source** | `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` §4.1.3 (external documentation lookup: aoestats.io homepage labels content as "ranked matches" but provides no schema documentation; no API docs, no GitHub link found); §4.1.5 (residual risks: quickplay contamination, custom-lobby contamination, missing queue metadata); §4.1.6 (evidence strength: WEAK/OPAQUE); `cleanup_flag_ledger.md` F-079 |
| **Mitigation already applied** | T05 established Tier 4 classification. `aoe2_ladder_provenance_audit.md` §4.1.7 provides the canonical wording. `cross_dataset_comparability_matrix.md` records Tier 4 status in the comparability matrix. |
| **Residual uncertainty** | aoestats.io does not expose API documentation mapping `leaderboard='random_map'` to the official AoE2 DE queue type. The upstream crawl from aoe2insights.com adds a second layer of opacity. Queue-type contamination (quickplay, custom lobbies under `random_map` label) is unquantifiable. |
| **Wording recommendation** | "aoestats 1v1 Random Map records (source label `leaderboard='random_map'`; queue semantics unverified against upstream API documentation; Tier 4 semantic opacity)". Thesis must NOT use "ranked ladder" for aoestats without this qualification. |
| **Downstream task responsible** | T11 -> T12 |
| **Blocking before Chapter 4 rewrite** | yes |

---

### RISK-05 — SC2 tournament/professional vs AoE2 public leaderboard/matchmaking population asymmetry

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-05 |
| **Severity** | major |
| **Likelihood** | high |
| **Affected thesis sections** | `thesis/chapters/01_introduction.md` §1.4 lines 43–45; `thesis/chapters/02_theoretical_background.md` §2.2.3 line 37; `thesis/chapters/04_data_and_methodology.md` §4.1 line 5, §4.1.3 lines 177–181, §4.1.4 line 211 |
| **Evidence source** | `thesis/pass2_evidence/cross_dataset_comparability_matrix.md` §1 row "Professional vs public player population"; §2 "Final Comparison Frame"; §2 "Five explicit comparison axes" (axes 2–5); `cleanup_flag_ledger.md` F-080 (cross-cutting external-audit); `cross_dataset_comparability_matrix.md` §3 CX-05 (wording-change-required), CX-08, CX-12 |
| **Mitigation already applied** | T09 (commit `64e08553`) produced the comparability matrix with explicit five-axis framing and the mandatory statement that "Observed differences between SC2 and AoE2 results MUST be interpreted as differences in method, data regime, and population — NOT as pure game-mechanic differences." |
| **Residual uncertainty** | The five comparison axes (game, data-regime, population, feature-availability, inference-limitation) are documented in the evidence file but not yet expressed in thesis prose with this clarity. Chapter 1 line 45 still uses "ladderowych graczy rankingowych" for aoestats (CX-05 wording-change-required). |
| **Wording recommendation** | "SC2EGSet represents a professional/tournament player population (~2,495 distinct player identities; Heckman selection bias toward high skill); AoE2 sources represent public player populations (aoestats: ~641K `profile_id`s; aoe2companion lb=6+18: ~683K `profileId`s in the post-cleaning cohort). Observed differences between SC2 and AoE2 prediction results are conditional on this population asymmetry and cannot be attributed solely to game-mechanic differences." |
| **Downstream task responsible** | T11 -> T12 -> T13 |
| **Blocking before Chapter 4 rewrite** | yes |

---

### RISK-06 — Cross-dataset comparability: data-regime differences vs game-mechanic interpretation

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-06 |
| **Severity** | major |
| **Likelihood** | high |
| **Affected thesis sections** | `thesis/chapters/04_data_and_methodology.md` §4.1.4 line 213; `thesis/chapters/01_introduction.md` §1.3 line 35 (RQ3); `thesis/chapters/02_theoretical_background.md` §2.1 line 15 |
| **Evidence source** | `thesis/pass2_evidence/cross_dataset_comparability_matrix.md` §2 "Final Comparison Frame" (five comparison axes, inference limitation axis 5); §3 CX-03 (supported-with-caveat: RQ3 hypothesis must note data-regime confound), CX-20 (supported-with-caveat); `cleanup_flag_ledger.md` F-080 |
| **Mitigation already applied** | T09 comparability matrix explicitly frames five axes (§2 "Five explicit comparison axes") and mandates that all cross-game comparison claims acknowledge the confound. §4.1.4 line 213 ("Population-scope is a controlled experimental variable") is classified as supported. |
| **Residual uncertainty** | The thesis does not yet have a formal bounded-comparability statement in §6.3 (Chapter 6 not yet drafted). RQ3 hypothesis (CX-03) needs an explicit note that the 1,225-civ-pair vs 9-race-pair comparison is about feature-space cardinality, not a clean game-mechanic comparison. |
| **Wording recommendation** | "All cross-game comparison claims are conditional on four simultaneous asymmetries: game mechanics, data regime (replay telemetry vs aggregated statistics), population (professional tournament vs public matchmaking), and feature availability (full in-game event streams vs pre-game only). No design in this thesis allows these sources to be cleanly separated." |
| **Downstream task responsible** | T11 -> T12 -> T13 |
| **Blocking before Chapter 4 rewrite** | no |

---

### RISK-07 — Unit-of-observation / grain-confusion risk (leaderboard_raw vs match-pair vs player-row vs profileId cardinality)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-07 |
| **Severity** | major |
| **Likelihood** | high |
| **Affected thesis sections** | `thesis/chapters/04_data_and_methodology.md` §4.1.3 Tabela 4.4a (population rows, match counts); §4.1.2.2 (aoe2companion scope description); all tables reporting player counts or match counts |
| **Evidence source** | `thesis/pass2_evidence/cross_dataset_comparability_matrix.md` §1 population row (aoe2companion): "The figure ~3,387,273 is the cross-leaderboard cardinality of `profileId` in `matches_raw` (all leaderboards combined; per `01_03_01_systematic_profile.md`) — distinct from the lb=6+18 cohort and at a different grain"; commit `64e08553` T09 sanity patch |
| **Mitigation already applied** | MITIGATED by T09 sanity patch (commit `64e08553`). The comparability matrix now explicitly distinguishes: (a) leaderboard_raw activity distribution counts (~54M for ID 6, ~7M for ID 18 — leaderboard_raw grain); (b) post-cleaning analytical match-pair count (30,531,196 match-pairs / 61,062,392 player-rows — matches_1v1_clean grain); (c) cross-leaderboard profileId cardinality in matches_raw (3,387,273 — all-leaderboard grain); (d) post-cleaning lb=6+18 cohort profileId cardinality (683,790). |
| **Residual uncertainty** | The four distinct grain levels are now correctly documented in the evidence files, but Chapter 4 tables (Tabela 4.4a, 4.4b, 4.5) must be rewritten to use the correct grain for each row. Examiner confusion is likely if a single table row mixes leaderboard_raw counts with post-cleaning match-pair counts without explicit grain labels. |
| **Wording recommendation** | Every table row reporting counts must carry a grain label: "leaderboard_raw activity entries (all leaderboards)", "post-cleaning match-pairs (`matches_1v1_clean`)", "post-cleaning player-rows", or "distinct `profileId`s in lb=6+18 cohort". Never report 3,387,273 as the post-cleaning aoe2companion player count. |
| **Downstream task responsible** | T11 |
| **Blocking before Chapter 4 rewrite** | yes |

---

### RISK-08 — Temporal leakage in history features (same-match leakage, future-rating imputation, rolling windows spanning prediction target)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-08 |
| **Severity** | blocker |
| **Likelihood** | medium |
| **Affected thesis sections** | `thesis/chapters/04_data_and_methodology.md` §4.2.3 (cleaning rules, missingness strategy); §4.4 (Phase 02 feature engineering — not yet drafted); all feature-computation notebooks for Phase 02 |
| **Evidence source** | `.claude/scientific-invariants.md` Invariant I1 (temporal discipline: "Use strictly `match_time < T`"), I2 (feature cut-off), I3 (rolling aggregate guard); `cleanup_flag_ledger.md` F-072 (I7 reference in thesis prose); `cross_dataset_comparability_matrix.md` §1 row "Rating availability": `new_rating` is POST-GAME, excluded (aoestats: CONDITIONAL_PRE_GAME condition documented); aoe2companion: `ratings_raw` has zero rows for lb=6 — pre-game rating derived from `matches_raw.rating` |
| **Mitigation already applied** | Scientific Invariants I1–I3 codified in `.claude/scientific-invariants.md`. `01_04_01_data_cleaning.md` (aoestats) excludes `new_rating` (POST-GAME). `01_04_07_old_rating_conditional_annotation.md` (aoestats, commit PR #203) applies CONDITIONAL_PRE_GAME annotation to `old_rating`. No Phase 02 feature-engineering code exists yet — the leakage guard is pre-emptive at this stage. |
| **Residual uncertainty** | Phase 02 has not yet been executed. Rolling-window feature computation must be validated against Invariants I1–I3 for all three datasets. The I7 reference in thesis prose (§4.2.3 line 303: `.claude/scientific-invariants.md:86` — a workflow-leakage issue per F-072) must also be replaced with academic language. |
| **Wording recommendation** | "All historical features are computed using only match records strictly prior to the prediction target game (match_time < T). Post-game rating changes, same-game statistics, and rolling windows that include the target game are excluded per the temporal discipline protocol." |
| **Downstream task responsible** | T11 (Chapter 4 §4.2.3 prose repair: workflow-leakage F-072 academic-language replacement of `.claude/scientific-invariants.md:86`; refactor temporal-discipline language to academic register) -> T16 (Phase 02 feature implementation guard: enforce Invariants I1–I3 in rolling-window code). T11 owns the prose work; any purely final-consistency residue (e.g., terminology unification across chapters) may flow to T18, but T11 must NOT silently defer the §4.2.3 prose issue to T18. T18 may perform final cleanup but must not be the first stage to notice or own §4.2.3 prose work. |
| **Blocking before Chapter 4 rewrite** | yes (resolves BLOCKER-B from Round 2 adversarial gate; flipped from `no` on 2026-04-26 because affected sections + wording recommendation + workflow-leakage F-072 explicitly land in T11 §4.2.3 scope, contradicting the prior `no` value) |

---

### RISK-09 — Match/series grouping leakage (series structure in tournaments, multiple matches between same opponents in close succession)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-09 |
| **Severity** | major |
| **Likelihood** | medium |
| **Affected thesis sections** | `thesis/chapters/04_data_and_methodology.md` §4.2.3 (temporal split strategy discussion); §4.4 (Phase 02/03 feature engineering + splitting — not yet drafted) |
| **Evidence source** | SC2EGSet tournament structure: 22,390 replays across 70 tournament directories (`01_01_01_file_inventory.md` sc2egset); multiple matches between the same pair of players within a single tournament (best-of-N series) creates a grouping structure that can leak information if a random train/test split separates games from the same series; `cross_dataset_comparability_matrix.md` §1 row "Sampling mechanism" (SC2EGSet: tournament-structured, non-contiguous) |
| **Mitigation already applied** | `processing.py → create_temporal_split()` is flagged in `CLAUDE.md` as using wrong split strategy (superseded by Phase 03). Phase 03 (Splitting & Baselines) will implement the correct temporal split. |
| **Residual uncertainty** | Phase 03 has not yet been executed. The SC2EGSet tournament series structure is not yet formally guarded in Phase 02. AoE2 public datasets (aoestats, aoe2companion) have lower risk because professional series structure is absent, but repeated matchups between the same players over short time windows remain possible. |
| **Wording recommendation** | "Train/test split is strictly temporal (all test matches post-date all training matches). For SC2EGSet tournament structure, matches from the same series are assigned to the same split partition to prevent within-series information leakage." |
| **Downstream task responsible** | T15 (Phase 03 split implementation) -> T11 (prose update once Phase 03 is complete) |
| **Blocking before Chapter 4 rewrite** | no |

---

### RISK-10 — Rating missingness and sentinel semantics (SC2 MMR=0, aoestats old_rating~0, aoe2companion rating ~26% NULL)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-10 |
| **Severity** | major |
| **Likelihood** | high |
| **Affected thesis sections** | `thesis/chapters/04_data_and_methodology.md` §4.2.3 (cleaning rules, missingness table Tabela 4.6); §4.4.5 (ICC Tabela 4.7); `thesis/chapters/01_introduction.md` §1.4 |
| **Evidence source** | SC2EGSet MMR=0 sentinel: 83.95% of rows per `01_04_01_data_cleaning.md` (sc2egset) — confirmed in `cross_dataset_comparability_matrix.md` §1 row "Rating availability"; aoestats `old_rating` sentinel=0: <0.03% of rows (near-zero sentinel per `aoe2_ladder_provenance_audit.md` §4.1.1); aoe2companion `rating` ~26% NULL (MAR mechanism — schema evolution / leaderboard boundary; per `cross_dataset_comparability_matrix.md` §1 row "Rating availability"); `cleanup_flag_ledger.md` F-054 (MMR MAR-primary/MNAR-sensitivity), F-055 (80% threshold heuristic) |
| **Mitigation already applied** | SC2EGSet: `is_mmr_missing` binary flag adopted as Phase 02 feature (supersedes MMR scalar); `01_04_01_data_cleaning.md` (sc2egset) documents R01 decisive filter (only 0–1v1 outcomes retained) and R03 (MMR<0 exclusion). Aoestats: CONDITIONAL_PRE_GAME annotation via `01_04_07`. Aoe2companion: MAR mechanism documented; 80% operational heuristic applied. |
| **Residual uncertainty** | F-054: MAR-primary/MNAR-sensitivity framing for SC2EGSet MMR must be verified against Rubin1976 strict reading (Pass-2). F-055: 80% threshold heuristic derivation must be confirmed from `01_04_01_data_cleaning.json:2436`. aoe2companion `ratings_raw` zero rows for lb=6 is an unusual schema property requiring explicit acknowledgement in the thesis. |
| **Wording recommendation** | "SC2EGSet MMR is absent (sentinel value = 0) for 83.95% of rows, reflecting the unrated-professional convention on Battle.net. MMR is classified as MISSING_NOT_MEANINGFUL for this population and replaced by the `is_mmr_missing` binary flag as a Phase 02 feature. Aoestats `old_rating` sentinel values (<0.03%) are excluded. Aoe2companion `rating` is ~26% NULL (missing at random; schema evolution); imputation strategy follows the 80% completeness heuristic documented in the cleaning protocol." |
| **Downstream task responsible** | T11 -> T13 (Pass-2 Rubin1976 verification) |
| **Blocking before Chapter 4 rewrite** | no |

---

### RISK-11 — Patch/version drift (46 SC2EGSet patches, 19 aoestats patches, aoe2companion multi-DLC temporal coverage)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-11 |
| **Severity** | major |
| **Likelihood** | medium |
| **Affected thesis sections** | `thesis/chapters/04_data_and_methodology.md` §4.1.1 (SC2EGSet acquisition), §4.1.2 (aoestats acquisition), §4.1.2.2 (aoe2companion), §4.4 (Phase 02 features — not yet drafted) |
| **Evidence source** | SC2EGSet: 46 distinct `metadata.gameVersion` values; PSI analysis (01_05_02) shows faction/matchup drift across quarters (`cross_dataset_comparability_matrix.md` §1 row "Patch / version drift handling"); aoestats: 19 distinct patches (2022-08-29 to 2025-12-02, per `overviews_raw`); PSI on rating features elevated (>=0.10) in 6 of 8 quarters; aoe2companion: no explicit patch_id column; temporal coverage 2020–2026 spans many DLC releases |
| **Mitigation already applied** | SC2EGSet: `01_05_02_quarterly_psid.md` (sc2egset) documents PSI elevation. Aoestats reference window locked to single-patch 66692 per `01_05_05_icc_results.json`. |
| **Residual uncertainty** | aoe2companion has no patch_id column, making patch-level PSI analysis impossible without external patch timeline cross-reference. The 2023-Q3 duration drift (|d|=0.544, 122 matches) identified in `modeling_readiness_sc2egset.md` SC-R07 is not yet referenced in thesis prose. |
| **Wording recommendation** | "Patch-level distributional drift is documented for SC2EGSet (46 patch versions; PSI elevated across quarters in faction and matchup features) and aoestats (19 patches; PSI >= 0.10 in 6 of 8 quarters). All temporal split protocols lock test partitions to later time periods to avoid train-test distributional leakage via patch version." |
| **Downstream task responsible** | T11 -> T16 |
| **Blocking before Chapter 4 rewrite** | no |

---

### RISK-12 — AoE2 civilization roster changes over the data window (DLC drops changing civ space; n_distinct=50 claim)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-12 |
| **Severity** | major |
| **Likelihood** | medium |
| **Affected thesis sections** | `thesis/chapters/04_data_and_methodology.md` Tabela 4.4a "Encje" row (civ count); `thesis/chapters/02_theoretical_background.md` §2.3.2 line 65 (DLC chronology) |
| **Evidence source** | `src/rts_predict/games/aoe2/datasets/aoestats/reports/INVARIANTS.md` §1: `p0_civ n_distinct=50`; `cleanup_flag_ledger.md` F-084 (major): "Must confirm final count 50 is correct through 2026-02-07. Last Chieftains DLC (2026-02-17) is exactly at or after corpus cutoff 2026-02-07"; F-013 (map pool for corpus window); F-014 (DLC chronology: Three Kingdoms 2025-05-06, Chronicles: Alexander 2025-10-14, Last Chieftains 2026-02-17) |
| **Mitigation already applied** | INVARIANTS.md §1 records `n_distinct=50` (on-disk, confirmed by aoestats data). The corpus window ends 2026-02-07; Last Chieftains DLC is 2026-02-17 (after cutoff), so this DLC's civs should be absent. Three Kingdoms (2025-05-06) and Chronicles: Alexander (2025-10-14) are within the window — their civs are included in the 50. |
| **Residual uncertainty** | F-084: the exact boundary depends on whether civs from DLCs released near the cutoff date (within days or weeks) appear in the crawled data. Pass-2 must verify the 50-civ count against the DLC timeline. The claim "50 civs" in §2.3.2 line 69 must be conditional on the observation window. |
| **Wording recommendation** | "The aoestats corpus (2022-08-28 to 2026-02-07) contains 50 distinct civilizations (per INVARIANTS.md §1 `p0_civ n_distinct=50`). This count reflects the AoE2 DE civilization roster as of the corpus end date; DLC-introduced civilizations released after 2026-02-07 (e.g., Last Chieftains, 2026-02-17) are not represented." |
| **Downstream task responsible** | T11 -> T13 (Pass-2 DLC chronology verification, F-014) |
| **Blocking before Chapter 4 rewrite** | no |

---

### RISK-13 — Feature importance interpreted causally (SHAP / classifier feature importance is correlational)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-13 |
| **Severity** | minor |
| **Likelihood** | medium |
| **Affected thesis sections** | `thesis/chapters/01_introduction.md` §1.1 line 11 (coaching tools); `thesis/chapters/01_introduction.md` §1.4 (causal disclaimer); `thesis/chapters/04_data_and_methodology.md` §4.4 (planned SHAP analysis — not yet drafted) |
| **Evidence source** | `cleanup_flag_ledger.md` F-088 (external-audit, minor): "feature importance from classifiers is correlational, not causal — §1.4 explicitly disclaims causal claims, but §1.1's coaching-tools sentence implies causality"; `cross_dataset_comparability_matrix.md` §3 CX-03 (supported-with-caveat), CX-18 (supported) |
| **Mitigation already applied** | §1.4 carries an explicit causal disclaimer. The comparability matrix classifies CX-18 ("Population-scope is a controlled experimental variable") as supported. |
| **Residual uncertainty** | §1.1 coaching-tools sentence needs explicit hedging. SHAP analysis has not yet been implemented; the hedge must be in place before §4.4 SHAP results are written. |
| **Wording recommendation** | "SHAP values and feature importance rankings from classifiers reflect correlation with the outcome in the training data, not causal relationships. Feature importance identifies statistical associations that may be useful for coaching analysis but cannot establish game-theoretic causality." |
| **Downstream task responsible** | T12 (Chapter 1 §1.1 hedge) -> T14 (Chapter 3 §3.3.5) -> T11 (§4.4 SHAP analysis once drafted) |
| **Blocking before Chapter 4 rewrite** | no |

---

### RISK-14 — ECE/binning instability (ECE is not a proper scoring rule; do not equate with Brier/log-loss)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-14 |
| **Severity** | minor |
| **Likelihood** | medium |
| **Affected thesis sections** | `thesis/chapters/02_theoretical_background.md` §2.6.2 (ECE as calibration diagnostic); `thesis/chapters/04_data_and_methodology.md` §4.4.4 (planned — not yet fully drafted) |
| **Evidence source** | `cleanup_flag_ledger.md` F-087 (external-audit, minor): "ECE is not itself a 'proper scoring rule' (it is a descriptive calibration metric) — the section may overclaim if ECE is positioned alongside Brier/log-loss as a 'proper rule'"; Gneiting2007 (proper scoring rules); no in-text flag currently guards this distinction |
| **Mitigation already applied** | None yet. F-087 identifies the risk but no correction has been applied to the thesis text. |
| **Residual uncertainty** | §2.6.2 and §4.4.4 must be checked to ensure ECE is not equated with proper scoring rules. Binning sensitivity (number of bins, equal-width vs equal-mass) is not yet discussed. |
| **Wording recommendation** | "Expected Calibration Error (ECE) is a descriptive calibration diagnostic, not a proper scoring rule in the sense of Gneiting and Raftery (2007). It is reported alongside the Brier score and log-loss (which are proper rules) to characterise calibration independently of sharpness. ECE estimates are sensitive to the number of bins; we use [N] equal-width bins." |
| **Downstream task responsible** | T13 (Chapter 2 §2.6.2) -> T11 (§4.4.4 once drafted) |
| **Blocking before Chapter 4 rewrite** | no |

---

### RISK-15 — Overuse of ICC / variance partitioning (observed-scale ANOVA ICC as lower-bound under logit link)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-15 |
| **Severity** | minor |
| **Likelihood** | medium |
| **Affected thesis sections** | `thesis/chapters/04_data_and_methodology.md` §4.4.5 lines 383–397 (ICC analysis, Tabela 4.7) |
| **Evidence source** | `cleanup_flag_ledger.md` F-058 (in-text-flag: "[REVIEW: kierunkowość lower-bound claim under logit link (Nakagawa2017 §2.2 + Browne2005)]"), F-086 (external-audit, major: "ICC overcentrality and latent-vs-observed-scale risk"), F-061 (Gelman2007 §11-12 744-cohort argument); `cross_dataset_comparability_matrix.md` §1 row "Cold-start behaviour" (ICC values: SC2 0.0463 INCONCLUSIVE, aoestats 0.0268 FALSIFIED, aoe2companion 0.003013 FALSIFIED) |
| **Mitigation already applied** | §4.4.5 cites Nakagawa2017 and Browne2005 as lower-bound argument (flagged in F-058 for Pass-2 verification). Gelman2007 §11-12 cited for 744-cohort aoestats small-cohort argument (F-061). |
| **Residual uncertainty** | Pass-2 must verify: (a) Nakagawa2017 §2.2 + Browne2005 unambiguously establish the lower-bound direction for binary outcome data under logit link; (b) Gelman2007 §11-12 argument applies to the 744-cohort size; (c) F-060: ICC CI method (delta-method for sc2egset per DEFEND doc line 205) is consistent across all three datasets. |
| **Wording recommendation** | "Observed-scale ANOVA ICC is a conservative lower bound for the latent-scale ICC under the logit link [Nakagawa2017 §2.2; Browne2005]. All three datasets yield ICC values below 0.05 (SC2EGSet: 0.0463 INCONCLUSIVE; aoestats: 0.0268 FALSIFIED; aoe2companion: 0.003013 FALSIFIED), indicating that per-player variance explains at most ~4.6% of total outcome variance." |
| **Downstream task responsible** | T11 |
| **Blocking before Chapter 4 rewrite** | no |

---

### RISK-16 — Overstrong literature-gap claim (Chapter 3 "luki" framing; Elbert2025EC and EsportsBench)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-16 |
| **Severity** | minor |
| **Likelihood** | medium |
| **Affected thesis sections** | `thesis/chapters/03_related_work.md` §3.5 lines 185–189 (Luki 1–3 framing); §3.4.3 (Elbert2025EC discussion); §3.4.4 (Xie2020 grey-lit) |
| **Evidence source** | `cleanup_flag_ledger.md` F-036 (NEEDS CITATION: 4 additional author candidates), F-037 (Elbert2025EC attribution method), F-038 (EsportsBench narrowing — check for AoE2 or ML-classifier addition); `cross_dataset_comparability_matrix.md` §3 CX-09 (supported: faction/civ comparison is factual), CX-10 (supported: feature-availability comparison) |
| **Mitigation already applied** | None. F-036–F-038 are open, deferred to T14 (Chapter 3 Pass-2 work). |
| **Residual uncertainty** | Luka 2 (Elbert2025EC arXiv:2506.04475) must be verified via PDF read (F-035, F-037). Luka 3 (EsportsBench) may have been updated with AoE2 or ML-classifier coverage that narrows the gap claim (F-038). Four 2025 author candidates (Brookhouse & Buckley, Caldeira et al., Alhumaid & Tur, Ferraz et al.) have not been located (F-036). |
| **Wording recommendation** | "Chapter 3 gap framing must remain as relative gaps (areas where existing work is limited, sparse, or absent in comparable scope) rather than absolute absences. Specifically, Luka 2 must acknowledge Elbert2025EC as partial coverage; Luka 3 must acknowledge EsportsBench version at time of writing and note any AoE2/ML-classifier coverage added." |
| **Downstream task responsible** | T14 |
| **Blocking before Chapter 4 rewrite** | no |

---

### RISK-17 — Grey-literature overreliance (three-tier policy: peer-reviewed / conference / grey-lit)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-17 |
| **Severity** | minor |
| **Likelihood** | medium |
| **Affected thesis sections** | `thesis/chapters/03_related_work.md` §3.4.4 (Xie2020, Porcpine2020); `thesis/chapters/02_theoretical_background.md` §2.2.4 (Liquipedia, Battle.net MMR); PJAIT thesis guidelines acceptance |
| **Evidence source** | `cleanup_flag_ledger.md` F-033 (external-audit, minor: "grey-literature acceptability — Pass 2 reconciliation with §2.2/§2.5 grey-lit decisions"), F-034 (Xie2020 Medium post), F-089 (external-audit: tier structure labelled but may not be consistently enforced) |
| **Mitigation already applied** | §3.4.4 applies tier labelling. `thesis-writing.md` rules mandate "Non-peer-reviewed sources are permitted only when no peer-reviewed alternative exists. Tag with `[REVIEW: grey-literature — <url>]`." |
| **Residual uncertainty** | Consistent enforcement must be verified across §2.2.4 (Liquipedia game-speed), §2.5.4 (Battle.net MMR), and §3.4.4 (Xie2020, Porcpine2020). Xie2020 Medium post content must be verified directly (F-034). PJAIT guidelines on grey-lit acceptability are not yet confirmed (F-033). |
| **Wording recommendation** | "Grey-literature sources (Xie2020, Porcpine2020, Liquipedia game-speed claim, Battle.net MMR documentation) are cited only where no peer-reviewed alternative exists and are explicitly marked as grey literature per the three-tier policy. The tier assignment is: (1) peer-reviewed journal/conference; (2) preprint with arXiv identifier; (3) grey literature with explicit [grey-lit] tag." |
| **Downstream task responsible** | T14 (§3.4.4) -> T13 (§2.2.4) |
| **Blocking before Chapter 4 rewrite** | no |

---

### RISK-18 — Reproducibility of third-party API / aggregator data (aoestats.io and aoe2companion API; no public SLA; snapshot date)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-18 |
| **Severity** | major |
| **Likelihood** | medium |
| **Affected thesis sections** | `thesis/chapters/04_data_and_methodology.md` §4.1.2 (aoestats acquisition), §4.1.2.2 (aoe2companion acquisition) |
| **Evidence source** | `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` §10 (external documentation probes — all aoe2companion/aoe2.net API endpoints returned HTTP 404 as of 2026-04-26); §4.1.3 (aoestats.io: no API documentation, no GitHub link); `cleanup_flag_ledger.md` F-041 (aoestats ToS and 172/171 file asymmetry), F-044 (aoe2companion ToS) |
| **Mitigation already applied** | Both datasets are stored as on-disk Parquet snapshots in the repository's `data/` directories, so the data itself is reproducible from the stored copies. However, the crawl methodology for aoestats and the aoe2insights.com API client for aoe2companion are third-party and not documented within the thesis. |
| **Residual uncertainty** | aoestats.io and aoe2companion API SLAs are undocumented. Re-crawl would yield different data if the sources change their API or historical records. ToS for both sources have not been confirmed (F-041, F-044 open). The snapshot date (aoestats: 2022-08-28 to 2026-02-07; aoe2companion: 2020-07 to 2026-04) must be cited explicitly in the thesis for reproducibility. |
| **Wording recommendation** | "Data from aoestats.io was collected as weekly Parquet snapshots via automated crawl (2022-08-28 to 2026-02-07; 172 match + 171 player files). Data from aoe2companion was collected as daily Parquet and CSV snapshots from the aoe2insights.com REST API (2020-07 to 2026-04; 2,073 match Parquets + 2,072 rating CSVs). These sources carry no public SLA; re-crawl may yield different data. Thesis analysis relies on the stored snapshot copies." |
| **Downstream task responsible** | T11 |
| **Blocking before Chapter 4 rewrite** | no |

---

### RISK-19 — External documentation probe confusion (aoe2.net probes NOT thesis data sources)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-19 |
| **Severity** | minor |
| **Likelihood** | low |
| **Affected thesis sections** | `thesis/chapters/04_data_and_methodology.md` §4.1.2.2 (aoe2companion section — any prose that might mention the external lookup) |
| **Evidence source** | `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` §4.2.4a: "aoe2.net is NOT an input data source in this thesis. The thesis uses only aoestats and aoe2companion as AoE2 data sources, and no dataset lineage is attributed to aoe2.net in any ROADMAP, schema, research_log, or thesis chapter. aoe2.net URLs were consulted in §4.2.4 only as a historical/external-ecosystem documentation probe." §10 (external probes table — 8 URLs listed, all clearly labelled as probes, NOT data sources) |
| **Mitigation already applied** | T05 (commit `200d45ff`) included explicit scoping note §4.2.4a. The distinction is clearly documented in the audit file. |
| **Residual uncertainty** | If thesis prose in §4.1.2.2 mentions the external documentation lookup, it could be misread as adding a third AoE2 data source. The probe context must never appear in thesis prose as data lineage. |
| **Wording recommendation** | "AoE2 data sources used in this thesis are: aoestats (Parquet snapshots from aoestats.io crawl) and aoe2companion (Parquet/CSV snapshots from aoe2insights.com API). aoe2.net and other historical API endpoints were consulted only as documentation probes to verify leaderboard ID semantics; they are not data sources and do not contribute any rows to the analytical datasets." |
| **Downstream task responsible** | T11 |
| **Blocking before Chapter 4 rewrite** | no |

---

### RISK-20 — SC2 cross-region fragmentation sample-size collapse (is_cross_region_fragmented flag; empirical retention threshold)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-20 |
| **Severity** | major |
| **Likelihood** | medium |
| **Affected thesis sections** | `thesis/chapters/04_data_and_methodology.md` §4.2.2 (identity resolution), §4.4 (Phase 02 feature scope — not yet drafted) |
| **Evidence source** | `src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md` §1 cross-region note (2026-04-21): 1,923 cross-region toon_ids; 246 distinct nicknames × regional variants; FAIL verdict against 3-threshold gate at window=30 (median undercount 16.0 games, p95 29.0 games); `modeling_readiness_sc2egset.md` SC-R01 [MEDIUM]; commit `7b6c7119` WP-7 (feat/sc2egset-cross-region-annotation); `cleanup_flag_ledger.md` F-095 (notebook `01_04_05_cross_region_annotation.py` not-yet-assessed for thesis claims), F-097 (notebook `01_05_10` not-yet-assessed) |
| **Mitigation already applied** | Commit `7b6c7119` (PR #204) implemented the `is_cross_region_fragmented` flag in `player_history_all` VIEW. The empirical impact analysis (`01_05_10_cross_region_history_impact.py`) yielded a FAIL verdict, documented in INVARIANTS.md and `cross_region_history_impact_sc2egset.md`. |
| **Residual uncertainty** | The parent instruction notes the "17% strict filter retention" figure must come from `modeling_readiness_sc2egset.md` §5 or the `01_05_10` cross-region analysis. Searching `modeling_readiness_sc2egset.md` §5 (Phase 02 Go/No-Go) — SC-R01 is listed as [MEDIUM] bias (~12% cross-region migration accepted) but a "17% retention" figure is not present in the accessed section. The precise sample-size collapse under strict `WHERE NOT is_cross_region_fragmented` filtering is not quantified in the evidence files checked. Per Invariant I7 (no magic numbers without empirical derivation), this threshold must not be hard-coded in thesis prose until Phase 02 provides the empirical retention figure. Treat as DEFERRED for quantification until Phase 02. |
| **Wording recommendation** | "The `is_cross_region_fragmented` flag (TRUE for 1,923 toon_ids / 246 distinct nicknames with cross-region aliases) identifies players whose rolling-window history features may be systematically undercounted. Phase 02 analysis will determine the appropriate handling strategy (strict exclusion, dual feature paths, or sensitivity indicator). The sample-size impact of strict exclusion is reported in §[Phase02 results]." Do NOT hard-code a retention percentage until Phase 02 quantifies it. |
| **Downstream task responsible** | T16 (Phase 02 feature scope decision) -> T11 (§4.2.2 prose update) |
| **Blocking before Chapter 4 rewrite** | no |

---

### RISK-21 — SC2 tracker_events_raw field-semantics uncertainty (final-tick PlayerStats minerals/vespene not necessarily cumulative)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-21 |
| **Severity** | major |
| **Likelihood** | low |
| **Affected thesis sections** | `thesis/chapters/04_data_and_methodology.md` §4.4 (Phase 02 in-game features — not yet drafted); applies only IF in-game features are retained per T15 decision |
| **Evidence source** | `thesis/pass2_evidence/cross_dataset_comparability_matrix.md` §1 row "In-game features available": "Full three-stream event telemetry: tracker_events (62M events: UnitBorn, UnitDied, PlayerStats, etc.), game_events (608M events), message_events (52K events). PlayerStats at ~160 game-loop intervals (~7.14s at Faster speed). Economic, military, and technological state series extractable per replay." Row "Replay availability": "All features beyond pre-game require parsing the three event streams." |
| **Mitigation already applied** | None yet. The in-game feature scope is not yet fixed (T15 decision pending). |
| **Residual uncertainty** | IF in-game features are retained: the semantics of `PlayerStats` event fields (minerals, vespene, army_value, workers_active_count, etc.) must be verified per-event-type. The specific risk is that final-tick values may represent instantaneous (not cumulative) counts for some fields. SC2 protocol documentation (SC2Protocol GitHub) and/or Vinyals2017 SC2LE §3 are the authoritative sources. |
| **Wording recommendation** | "Per-event field semantics for `tracker_events.PlayerStats` (e.g., minerals spent, vespene collected) were verified against the SC2 protocol documentation [cite SC2Protocol GitHub or Vinyals2017 §3] to confirm whether values are cumulative totals or instantaneous snapshots at each game-loop tick. [CONDITIONAL: add this sentence only if in-game features are retained per T15 decision.]" |
| **Downstream task responsible** | T15 (in-game feature scope decision) -> T11 (if in-game features included) |
| **Blocking before Chapter 4 rewrite** | no |

---

### RISK-22 — PR scope / stale-artifact risk (20 tasks, three datasets, four chapters, two LOCKED specs)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-22 |
| **Severity** | note |
| **Likelihood** | low |
| **Affected thesis sections** | All (cross-cutting PR-level risk) |
| **Evidence source** | `cleanup_flag_ledger.md` escape-valve evaluation (line 207–211): "Stale Steps discovered by T04: 0. The only stale finding (C3-01, §3.2.2 file count 17930/55 vs 22390/70) was already identified in T03. T04 does not surface any new stale Steps or stale artifacts beyond T03's findings. The >10 stale-Step escape valve is NOT triggered."; `thesis/pass2_evidence/dependency_lineage_audit.md` T03: stale Step count = 0 additional beyond C3-01 (prose-stale, not Step-stale) |
| **Mitigation already applied** | RESOLVED by T03. The `>10 stale-Step` escape valve did NOT fire. T03 confirmed stale Step count at 0 (only C3-01 prose-stale, which is a prose wording issue, not a STEP_STATUS stale finding). The PR continues at full scope. |
| **Residual uncertainty** | None. Risk is resolved. Recorded for historical completeness as mandated by the plan. |
| **Wording recommendation** | No thesis wording required. Internal PR-scoping risk only. |
| **Downstream task responsible** | resolved (T03) |
| **Blocking before Chapter 4 rewrite** | no |

---

### RISK-23 — Generated-artifact wording propagation risk (Step 01_06_02 aoe2companion data-quality-report mis-label)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-23 |
| **Severity** | major |
| **Likelihood** | medium |
| **Affected thesis sections** | `thesis/chapters/04_data_and_methodology.md` §4.1.2.2 (aoe2companion CONSORT flow table); all Chapter 4 tables that previously echoed the artifact's R01 wording |
| **Evidence source** | `thesis/pass2_evidence/aoe2_ladder_provenance_audit.md` §5 propagation trace (lines 362–418): origin at `data_quality_report_aoe2companion.md:29` R01 description "Retain 1v1 ranked ladder only"; §6 generated-artifact repair determination; commit `9581b053` ("fix(aoe2companion): repair Step 01_06_02 mixed-mode population wording") |
| **Mitigation already applied** | MITIGATED by commit `9581b053` (T07+T08 lineage repair). The upstream notebook `01_06_02_data_quality_report.py` was corrected and the artifact `data_quality_report_aoe2companion.md` was regenerated with the correct wording: "Retain 1v1 rm_1v1 (ID 6) and qp_rm_1v1 (ID 18) scope". The generated artifact is now correct on the current branch. |
| **Residual uncertainty** | This is a historical propagation risk. The artifact mis-label existed before commit `9581b053` and was echoed into Chapter 4 tables at lines 177, 187, 211, 255. Those thesis chapter locations still carry the old wording — they were NOT updated by the artifact repair commit, which only fixed the generated artifact. Chapter 4 (T11) must not regress by copying language from the artifact's old wording. The T11 rewrite must use the new wording sourced from the corrected artifact and from `aoe2_ladder_provenance_audit.md` §4.2.5. |
| **Wording recommendation** | "T11 must source Chapter 4 table wording for the aoe2companion R01 rule from the corrected artifact (`data_quality_report_aoe2companion.md` post-commit `9581b053`) and from `aoe2_ladder_provenance_audit.md` §4.2.5. The correct wording is: 'Retain 1v1 rm_1v1 (ID 6) and qp_rm_1v1 (ID 18) scope (internalLeaderboardId IN (6, 18))'. Chapter 4 tables must not re-introduce 'ranked ladder only' from any cached or pre-repair version of the artifact." |
| **Downstream task responsible** | T11 |
| **Blocking before Chapter 4 rewrite** | yes |

---

### RISK-24 — Focal/opponent slot asymmetry across dataset table shapes (added 2026-04-26 to resolve BLOCKER-A from Round 2)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-24 |
| **Severity** | major |
| **Likelihood** | high |
| **Affected thesis sections** | `thesis/chapters/04_data_and_methodology.md` §4.1 (CONSORT flow tables Tabela 4.4a / 4.4b), §4.2 (data sources description and operational identity resolution), §4.3 (analytical-table specification — when drafted), and any thesis prose that compares "row counts", "match counts", "player-row counts", "match-pairs", "focal/opponent" construction, or side/team semantics across the three datasets |
| **Evidence source** | `thesis/pass2_evidence/cross_dataset_comparability_matrix.md` §1 row "Unit of observation" (line 22): SC2EGSet = "player-match: one row per player per replay (`matches_flat_clean` is 2-row-per-match); 22,209 match-pairs (44,418 rows) after cleaning"; aoestats = "match: one row per match (1-row-per-match; both players encoded as `p0_*` / `p1_*` columns); 17,814,947 matches after cleaning"; aoe2companion = "player-match: one row per player per match (2-row-per-match); 30,531,196 match-pairs (61,062,392 rows) after cleaning". `aoe2_ladder_provenance_audit.md` Inference-limitations row notes aoestats has "no player name column — cross-dataset identity bridge to aoe2companion required for nickname access". `cleanup_flag_ledger.md` (no direct entry; surfaced by Round 2 adversarial gate Dimension 5 BLOCKER-A). |
| **Mitigation already applied** | None directly. `cross_dataset_comparability_matrix.md` documents the three table shapes side-by-side in §1 line 22, and the grain-disambiguation patch (T09 sanity patch, commit `64e08553`) clarified count grains. But focal/opponent construction symmetry across the three shapes is NOT yet formalized in any contract. |
| **Residual uncertainty** | The thesis comparative protocol depends on symmetric focal/opponent treatment (Invariant #5 spirit). With three different table shapes — SC2EGSet 2-row-per-match, aoestats 1-row-per-match (`p0_*`/`p1_*`), aoe2companion 2-row-per-match — the focal-construction step is heterogeneous. If Phase 02 features are computed independently per shape without an explicit symmetric-construction contract, comparable per-player metrics may diverge for non-empirical reasons. Examiner question route: "Why is the focal/opponent feature construction defensible across three differently-shaped tables?" — the thesis must have an answer. |
| **Wording recommendation** | "Each dataset uses a dataset-specific analytical unit ('row', 'match', 'match-pair', and 'player-row' are NOT interchangeable across the three sources unless explicitly normalized). Chapter 4 must label every cross-dataset table with its unit of observation and grain. Where focal/opponent feature construction is used, the construction step must be described per dataset and any normalization to a comparable per-player or per-match grain must be made explicit." |
| **Downstream task responsible** | T11 (Chapter 4 §4.1 / §4.2 / §4.3 prose: label every comparison-table cell with grain; describe focal/opponent construction per dataset) -> T16 (Phase 02 feature engineering contract: guarantee symmetric focal/opponent operationalization across the three table shapes; verify identity-resolution step does not collapse aoestats `p0_*` / `p1_*` into the wrong slot) |
| **Blocking before Chapter 4 rewrite** | yes |

---

### RISK-25 — AoE2 civilization-pair feature-engineering cardinality (added 2026-04-26 to resolve BLOCKER-A from Round 2)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-25 |
| **Severity** | minor |
| **Likelihood** | medium |
| **Affected thesis sections** | `thesis/chapters/01_introduction.md` §1.3 (RQ3 hypothesis if it mentions civ-pair cardinality or 1,225 pairings), `thesis/chapters/02_theoretical_background.md` §2.3.2 (AoE2 system description; current civ count claim of 50), `thesis/chapters/04_data_and_methodology.md` §4.4 (feature-engineering plan, when drafted, if civ-pair features are described) |
| **Evidence source** | `thesis/pass2_evidence/cross_dataset_comparability_matrix.md` §3 claim CX-03 (`01_introduction.md` §1.3 line 35) "AoE2 civ matchup features will be stronger than SC2 race matchup features due to the 1,225-pair space" labelled supported-with-caveat; `aoe2_ladder_provenance_audit.md` and `cleanup_flag_ledger.md` F-014 / F-084 (DLC chronology and corpus-window civ count); `INVARIANTS.md §1` (aoestats) `p0_civ n_distinct=50` |
| **Mitigation already applied** | None. The 50-civ count is observed in `INVARIANTS.md`, but no risk register entry previously tied this to feature-engineering cardinality risk. CX-03's "supported-with-caveat" classification mentions feature-space cardinality but does not translate to a risk-register entry. |
| **Residual uncertainty** | 50 civilizations imply 1,225 unordered pairings only under a fixed-roster assumption. The roster changed across the data window (DLC drops; Three Kingdoms 2025-05-06; Last Chieftains 2026-02-17 at corpus cutoff). Even within a fixed roster, most pairs are sparsely observed (pair frequency follows skewed distributions); cold-start at the pair level (most pairs unobserved or under-observed) is a real Phase 02 risk that no register entry currently guards. Chapter 1 RQ3 hypothesis must hedge against the implication that all 1,225 pairings are equally observable or estimable. |
| **Wording recommendation** | Use phrasing such as "up to / observed by the end of the analysed window" or "high-cardinality civilization-pair space (up to 1,225 unordered pairs under a fixed roster assumption; the roster changed across the data window)" rather than asserting an exact, timeless 1,225-pair feature space. Where Chapter 4 §4.4 describes feature engineering, explicitly note that civ-pair encoding must use the date-valid roster and that the empirical observation distribution over pairs is highly uneven. |
| **Downstream task responsible** | T12 (Chapter 1 RQ3 hypothesis hedge; Chapter 1 motivation phrasing) -> T16 (Phase 02 feature engineering: civ-pair encoding must use date-valid observed categories, not a timeless final roster) |
| **Blocking before Chapter 4 rewrite** | no |

---

### RISK-26 — SC2 Random race semantics for pre-game features (added 2026-04-26 to resolve BLOCKER-A from Round 2)

| Field | Value |
|-------|-------|
| **Risk ID** | RISK-26 |
| **Severity** | minor |
| **Likelihood** | medium |
| **Affected thesis sections** | `thesis/chapters/04_data_and_methodology.md` §4.1.1 (SC2EGSet description, race / faction encoding); §4.2.3 (cleaning rules, missingness strategy, race/matchup feature encoding); `thesis/chapters/04_data_and_methodology.md` §4.4 (feature-engineering plan when drafted, if race or matchup features are materialized) |
| **Evidence source** | `aoe2_ladder_provenance_audit.md` §4.1.4 line 89 mentions 555 replays with `Random` race declaration in SC2EGSet; `cross_dataset_comparability_matrix.md` §1 row "Map / civ / race encoding" (line 31): "Race: 3 + Random (4 values after normalization; `selectedRace` column). 555 replays with `Random` race declaration"; `cleanup_flag_ledger.md` (no direct entry; surfaced by Round 2 adversarial gate Dimension 5 BLOCKER-A). |
| **Mitigation already applied** | None. The 555-replay / `Random` count is documented in the matrix and the audit, but no risk register entry previously distinguished pre-game `Random` (a chosen pre-game category in the `selectedRace` column) from the actual in-game race derived after game start. |
| **Residual uncertainty** | For pre-game prediction (Invariant I3 strict), the focal race feature for Random-pickers is `Random` at game-start time — NOT the eventual race the player commits to once the game begins. If feature engineering or thesis prose conflates these (e.g., by using a "race played" feature derived from in-game state), Random-pickers introduce a leakage path because the in-game race resolution is post-game-start information. Affects 555 replays / 1,110 player-rows in SC2EGSet. The thesis must state explicitly how Random is treated: retained as a distinct pre-game category, excluded, or handled separately. |
| **Wording recommendation** | "`Random` is a pre-game selected-race category (or sentinel) where applicable; actual in-game race resolution is dataset- and artifact-dependent and constitutes post-game-start information per Invariant I3. For pre-game prediction, the focal race feature for Random-pickers is the pre-game `Random` value, not the eventual race; alternative treatments (exclusion, separate handling) must be documented if used." |
| **Downstream task responsible** | T11 (Chapter 4 §4.1.1 / §4.2.3 prose: state Random treatment explicitly if race distributions or race feature encoding are enumerated; if §4.1.1 / §4.2.3 do NOT enumerate race feature engineering, the risk routes to T16 only) -> T16 (Phase 02 feature engineering: specify race / matchup encoding rules; ensure Random-pickers do not introduce pre-game-vs-in-game leakage) |
| **Blocking before Chapter 4 rewrite** | yes (with note: register schema supports yes/no only — RISK-26 is conditional in spirit; flagged YES so T11 dispatch must check whether §4.1.1 / §4.2.3 enumerate SC2 race distributions, Random race treatment, or race/matchup feature encoding. If T11 confirms those topics are NOT in §4.1.1 / §4.2.3 scope, the blocking flag may be relaxed at T11 dispatch time and the risk routes purely to T16) |

---

### T11 dispatch warnings (carried over from Round 2 adversarial gate)

The following four WARNINGs from Round 2 are NOT new BLOCKERs but must be carried into the T11 dispatch instructions so the T11 executor can mitigate them inline. Source: `audit_cleanup_summary.md` "Mid-PR adversarial gate (T10, Round 2 of 3)" section, WARNINGs (1)–(4).

1. **WARNING-1 (T05 shorthand echo).** T11 read scope must explicitly forbid echoing the `aoe2companion` `INVARIANTS.md §2` shorthand `rm_1v1 analytical scope` without the `(ID 6 + ID 18)` qualifier. The shorthand is dataset-internal convention and not a mis-label, but copying it verbatim into Chapter 4 prose would re-introduce the same ambiguity that T05/T07 corrected.
2. **WARNING-2 (aoestats artifact asymmetry).** `aoestats` `data_quality_report_aoestats.md` R02 wording "Restrict to ranked 1v1 ladder" remains uncorrected (the T07/T08 lineage repair was scoped to aoe2companion only). T11 must apply a prose-level Tier-4 hedge per `aoe2_ladder_provenance_audit.md` §8 step 4 wherever Chapter 4 references the aoestats R02 wording. Optionally raise as a separate risk register entry if the asymmetry becomes more severe at draft time.
3. **WARNING-3 (matrix Population grain visual differentiator).** The matrix Population row uses bold for post-cleaning numbers but not for `leaderboard_raw` activity counts (~54M, ~7M). When T11 transcribes counts into Tabela 4.4a / 4.4b / 4.5, every count cell must carry an explicit grain label per RISK-07's wording recommendation — bold or no bold is irrelevant if the grain label is missing.
4. **WARNING-4 (matrix Unit-of-observation rows-per-match annotation).** The matrix Unit-of-observation row reports SC2EGSet "(44,418 rows)" and aoe2companion "(61,062,392 rows)" but aoestats has no parenthetical (1-row-per-match). When T11 places these three numbers in adjacent table cells, an explicit "rows-per-match" annotation must accompany each cell, otherwise the examiner will challenge why aoestats has no row-multiplier.

---

## Summary

### Counts by severity

| Severity | Count | Risk IDs |
|----------|-------|----------|
| blocker | 2 | RISK-01, RISK-08 |
| major | 15 | RISK-02, RISK-03, RISK-04, RISK-05, RISK-06, RISK-07, RISK-09, RISK-10, RISK-11, RISK-12, RISK-18, RISK-20, RISK-21, RISK-23, RISK-24 |
| minor | 7 | RISK-13, RISK-14, RISK-15, RISK-16, RISK-17, RISK-25, RISK-26 |
| note | 2 | RISK-19, RISK-22 |
| **Total** | **26** | RISK-01 through RISK-26 |

### Counts by blocking-before-Chapter-4-rewrite status

| Status | Count | Risk IDs |
|--------|-------|----------|
| **Blocking (yes)** | 9 | RISK-01, RISK-02, RISK-03, RISK-04, RISK-07, RISK-08 (flipped 2026-04-26), RISK-23, RISK-24, RISK-26 (conditional — see RISK-26 detail) |
| **Non-blocking (no)** | 17 | RISK-05, RISK-06, RISK-09, RISK-10, RISK-11, RISK-12, RISK-13, RISK-14, RISK-15, RISK-16, RISK-17, RISK-18, RISK-19, RISK-20, RISK-21, RISK-22, RISK-25 |

Note (post-2026-04-26 BLOCKER-B resolution): Both blocker-severity risks (RISK-01, RISK-08) are now correctly recorded as blocking-before-T11. RISK-08 was flipped from `no` to `yes` on 2026-04-26 because its Affected sections + Wording recommendation explicitly include T11-scope §4.2.3 prose work (workflow-leakage F-072 academic-language replacement of `.claude/scientific-invariants.md:86`); the prior `no` value was inconsistent with that scope. The Phase 02 implementation work (Invariants I1–I3 leakage guard) still routes to T16, but the §4.2.3 prose repair is owned by T11 and must not be silently deferred to T18.

### Task routing summary

| Downstream task | Risks routed |
|-----------------|-------------|
| **T11** (Chapter 4 rewrite) | RISK-01 (partial), RISK-02 (partial), RISK-03, RISK-07, RISK-08 (prose repair: §4.2.3 academic-language replacement of `.claude/scientific-invariants.md:86`), RISK-10, RISK-11, RISK-12 (partial), RISK-14 (partial), RISK-15, RISK-18, RISK-19, RISK-20 (partial), RISK-21 (conditional), RISK-23, RISK-24 (label every cross-dataset table with grain; describe focal/opponent construction per dataset), RISK-26 (conditional: §4.1.1 / §4.2.3 Random race treatment if those sections enumerate race feature engineering) |
| **T12** (Chapter 1 rewrite) | RISK-01 (partial), RISK-02 (partial), RISK-04 (partial), RISK-05 (partial), RISK-06 (partial), RISK-13, RISK-25 (RQ3 hypothesis hedge for civ-pair feature space cardinality) |
| **T13** (Chapter 2 rewrite) | RISK-05 (partial), RISK-06 (partial), RISK-12 (partial), RISK-13 (partial), RISK-14 |
| **T14** (Chapter 3 rewrite) | RISK-13 (partial), RISK-16, RISK-17 (partial) |
| **T15** (Phase 03 split implementation) | RISK-09, RISK-21 (decision gate) |
| **T16** (Phase 02 feature implementation) | RISK-08 (leakage guard: Invariants I1–I3 in rolling-window code), RISK-11 (partial), RISK-20 (empirical retention threshold), RISK-24 (symmetric focal/opponent operationalization across the three table shapes), RISK-25 (date-valid civ roster in feature engineering), RISK-26 (race / matchup encoding rules; Random-picker leakage prevention) |
| **T18** (Final consistency pass) | only as final-cleanup residue from T11 — NOT first-stage owner of any §4.2.3 prose work; RISK-08 explicitly forbids T18 from being the first stage to notice or own the §4.2.3 issue |
| **resolved** | RISK-22 (T03) |

### One-line severity summary of all 26 risks

| Risk ID | Severity | One-line summary |
|---------|----------|-----------------|
| RISK-01 | blocker | qp_rm_1v1 mis-label propagated from artifact into Chapter 4 thesis prose (concrete pre-9581b053 state; artifact repaired, prose not yet) |
| RISK-02 | major | Combined aoe2companion ID 6+18 scope mis-classified as "ranked ladder" in Chapter 4 tables |
| RISK-03 | major | aoe2companion ID 18 qp_rm_1v1 status rests on on-disk label and fallback rule; external API unavailable |
| RISK-04 | major | aoestats leaderboard='random_map' is Tier 4 semantic opacity; never call "ranked ladder" without qualification |
| RISK-05 | major | SC2 professional tournament vs AoE2 public matchmaking population asymmetry not yet fully expressed in thesis prose |
| RISK-06 | major | Observed SC2 vs AoE2 result differences conflate game-mechanics, data-regime, population, and feature-availability confounds |
| RISK-07 | major | Grain confusion between leaderboard_raw activity counts, match-pairs, player-rows, and profileId cardinalities (MITIGATED by T09 sanity patch; prose fix pending) |
| RISK-08 | blocker | Temporal leakage guard (match_time < T strict, no same-match leakage) is pre-emptive; Phase 02 implementation must enforce Invariants I1–I3 |
| RISK-09 | major | SC2 tournament series grouping leakage; temporal split must assign series to same partition |
| RISK-10 | major | SC2 MMR=0 sentinel (83.95%), aoestats old_rating~0, aoe2companion rating ~26% NULL — distinct missingness mechanisms |
| RISK-11 | major | 46 SC2 patch versions + 19 aoestats patches create distributional drift; temporal split essential |
| RISK-12 | major | AoE2 civ count 50 must be verified as correct within the 2022–2026-02-07 corpus window |
| RISK-13 | minor | SHAP/feature importance is correlational; §1.1 coaching-tools sentence needs causal hedge |
| RISK-14 | minor | ECE is not a proper scoring rule; must not be equated with Brier/log-loss in §2.6.2 |
| RISK-15 | minor | Observed-scale ANOVA ICC is a lower bound under logit link; ICC lower-bound direction needs Pass-2 literature verification |
| RISK-16 | minor | Chapter 3 literature-gap claims must remain relative gaps, not absolute absences (Elbert2025EC, EsportsBench) |
| RISK-17 | minor | Grey-literature tier policy must be enforced consistently across §2.2.4, §2.5.4, §3.4.4 |
| RISK-18 | major | aoestats/aoe2companion have no SLA; re-crawl may yield different data; snapshot date must be cited |
| RISK-19 | note | aoe2.net documentation probes must NOT be mistaken for thesis input data sources |
| RISK-20 | major | is_cross_region_fragmented strict-filter sample-size collapse must be quantified empirically in Phase 02; no hard-coded percentage |
| RISK-21 | major | SC2 PlayerStats field semantics (cumulative vs instantaneous) must be verified IF in-game features retained (conditional on T15) |
| RISK-22 | note | PR scope / stale-artifact risk — RESOLVED at T03; stale Step count = 0; escape valve NOT triggered |
| RISK-23 | major | Step 01_06_02 artifact wording mis-label — MITIGATED by commit 9581b053; Chapter 4 must not regress to pre-repair wording |
| RISK-24 | major | Focal/opponent slot asymmetry across three dataset table shapes (SC2EGSet 2-row-per-match, aoestats 1-row-per-match `p0_*`/`p1_*`, aoe2companion 2-row-per-match); blocking-before-T11 |
| RISK-25 | minor | AoE2 civ-pair feature-engineering cardinality (1,225 unordered pairs only under fixed-roster assumption; cold-start at the pair level) |
| RISK-26 | minor | SC2 Random race semantics for pre-game features; Random-pickers must not be conflated with eventual race (post-game-start info) |
