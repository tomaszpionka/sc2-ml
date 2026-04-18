# Step 01_04_04 -- Identity Resolution (aoestats)

**Date:** 2026-04-18
**Phase:** 01 -- Data Exploration
**Pipeline Section:** 01_04 -- Data Cleaning
**Dataset:** aoestats
**Step scope:** Exploratory census of aoestats identity structure.
No new VIEWs, no raw-table modifications, no schema YAML changes (I9).

---

## Structural asymmetry

aoestats has **no nickname column** in any raw table. `players_raw` has 14
columns; no `name`, `display`, or `nickname` field exists. Invariant I2
(lowercased in-game nickname as canonical player identifier) is **natively
unmeetable** for this dataset without a cross-dataset bridge.

`profile_id` (DOUBLE in `players_raw`; BIGINT in views) is the sole identity
signal. This step characterises its health, probes behavioural surrogates, and
assesses cross-dataset bridge feasibility.

---

## Task A -- Sentinel + NULL audit

| Column | Table/View | Type | n_rows | n_null | n_zero | n_negative | n_minus_one | min | max | cardinality |
|---|---|---|---|---|---|---|---|---|---|---|
| profile_id | players_raw | DOUBLE | 107,627,584 | 1,185 | 0 | 0 | 0 | 18 | 24853897 | 641,662 |
| profile_id | player_history_all | BIGINT | 107,626,399 | 0 | 0 | 0 | 0 | 18 | 24,853,897 | 641,662 |
| p0_profile_id | matches_1v1_clean | BIGINT | 17,814,947 | 0 | 0 | 0 | 0 | 18 | 24,853,897 | 310,670 |
| p1_profile_id | matches_1v1_clean | BIGINT | 17,814,947 | 0 | 0 | 0 | 0 | 18 | 24,853,301 | 309,727 |

**Finding:** All views are clean -- no NULL, zero, negative, or -1 sentinel
values. The 1,185 NULLs in `players_raw.profile_id` are already excluded by
the `player_history_all` filter (`profile_id IS NOT NULL`).
DOUBLE type in `players_raw` is a DuckDB Arrow-promotion artifact; integer
values are exact for the observed range (max=24,853,897 << 2^53).

---

## Task B -- Per-profile activity distribution

| Metric | q25 | q50 | q75 | q90 | q99 | max |
|---|---|---|---|---|---|---|
| match_count | 2 | 13 | 116 | 479 | 2152 | 15075 |
| active_days | 1 | 6 | 41 | 148 | 519 | 1064 |

- **Total profiles:** 641,662
- **Single-day profiles:** 160,163 (casual/one-off players)
- **Single-ladder profiles:** 372,555
- **Multi-ladder profiles:** 269,107 (appear in > 1 leaderboard)
- **Max leaderboards per profile:** 4

---

## Task C -- Duplicate (game_id, profile_id) census

Census-aligned COALESCE key: `CAST(game_id AS VARCHAR) || '_' ||
COALESCE(CAST(profile_id AS VARCHAR), '__NULL__')`.

- **Duplicate rows:** 489 (anchor: 489 from 01_03_01; drift=+0)
- **Gate:** PASS -- within 489 ± 10 tolerance.

---

## Task D -- Rating-trajectory monotonicity probe

10,000-profile reservoir sample, seed=20260418. LAG(old_rating) deltas.

| Metric | Value |
|---|---|
| n_deltas | 11,311,282 |
| n_large_delta (\|Δ\| > 500) | 12,047 (0.107%) |
| median_abs_delta | 16 |
| p75_abs_delta | 17 |
| p99_abs_delta | 226 |
| max_abs_delta | 1444 |

**I7 hedge:** The 500-ELO threshold is an anecdotal RTS convention (~15x
expected K-factor swing). This is a first-cut sanity bound, not a calibrated
threshold. The 12,047 large-delta observations (0.107%)
may represent season resets, provisional periods, or data ingestion artifacts.

---

## Task E -- replay_summary_raw parseability probe

Sample: 1,000 rows (seed=20260418) from non-empty `replay_summary_raw` entries.

- **Non-empty rows in sample:** 146
- **Format:** Python dict (single-quote keys) -- **NOT valid JSON**
- **Parseable (ast.literal_eval):** 146 / 146
- **Mean length:** 1288.5 chars
- **Max length:** 2236 chars
- **Top keys:** {'age_stats': 146, 'opening_name': 146}

**Feasibility verdict:** `opening_name` key is present in all parseable rows.
Name extraction via `ast.literal_eval` is technically feasible.
**DEFERRED -- out of scope for this step.** A dedicated step would be needed
to extract and validate player names from replay_summary_raw.

---

## Task F -- Civ-fingerprint JSD analysis

**Qualifying threshold:** >= 20 matches AND >= 180 active days.
**Qualifying profiles:** 52,455 of 641,662 total.

### Within-profile JSD (first-half vs second-half, 50-dim civ distribution)

| p5 | p25 | p50 | p75 | p95 | p99 |
|---|---|---|---|---|---|
| 0.027 | 0.0725 | 0.1262 | 0.1993 | 0.3472 | 0.48 |

Threshold breakdown (JSD < 0.10 = stable; 0.10-0.30 = moderate drift;
0.30-0.50 = substantial; >= 0.50 = high drift):

| JSD < 0.10 | 0.10 -- 0.30 | 0.30 -- 0.50 | >= 0.50 |
|---|---|---|---|
| 19,976 (38.1%) | 27,984 (53.3%) | 4,113 (7.8%) | 382 (0.7%) |

### Cross-profile JSD (10,000 random pairs, control)

| p5 | p25 | p50 | p75 | p95 | p99 |
|---|---|---|---|---|---|
| 0.0998 | 0.2288 | 0.3606 | 0.4885 | 0.6257 | 0.6711 |

**Separation:** Within-profile median (0.1262) <<
cross-profile median (0.3606), confirming temporal stability
of individual civ preferences relative to random pairs.

### 10-profile example table (top by match_count)

| profile_id | match_count | active_days | JSD | top_civ_1st | % | top_civ_2nd | % |
|---|---|---|---|---|---|---|---|
| 3288518 | 15,075 | 741 | 0.2419 | malay | 36.7% | malay | 32.3% |
| 4216671 | 11,230 | 977 | 0.1320 | franks | 19.1% | vikings | 18.9% |
| 14527552 | 10,949 | 834 | 0.1334 | saracens | 8.1% | dravidians | 19.5% |
| 15369793 | 10,205 | 693 | 0.1131 | mongols | 47.7% | spanish | 27.6% |
| 5600740 | 10,199 | 881 | 0.1856 | goths | 20.9% | celts | 10.1% |
| 11962723 | 10,151 | 729 | 0.1448 | khmer | 14.7% | ethiopians | 14.6% |
| 9958595 | 9,398 | 871 | 0.0425 | spanish | 48.6% | spanish | 34.1% |
| 6297927 | 9,167 | 919 | 0.0789 | franks | 16.2% | franks | 10.2% |
| 15802329 | 8,861 | 543 | 0.1137 | gurjaras | 20.4% | gurjaras | 27.1% |
| 5864544 | 8,752 | 1009 | 0.1352 | persians | 16.2% | koreans | 15.9% |

### Hedge (I7 + R1-WARNING-6 fix)

Hahn et al. 2020 (SC2 APM/build-order) is **adjacent literature, not direct**.
Civ-marginal JSD over <= 50 civs with meta drift is a **coarse proxy** for
identity resolution. Thresholds 0.10/0.30/0.50 are symmetric KL divergence
interpretations; per-corpus calibration is required before operational use.
**Rename/multi-account resolution for aoestats remains unsolved pending the
cross-dataset bridge evaluated in Task G.**

---

## Task G -- Cross-dataset feasibility preview

**Window:** 2026-01-25..2026-01-31 (aoestats × aoec coverage intersection).
**aoestats filter:** `leaderboard='random_map'` (matches_1v1_clean).
**aoec filter:** `internalLeaderboardId IN (6, 18)` (rm_1v1 equivalent).
**Blocker:** 60s temporal + civ-set equality + 50-ELO proximity.

| Metric | Value |
|---|---|
| n_aoestats_sample | 1,000 |
| n_aoec_1v1_matches_in_window | 193,009 |
| block_hits (<=60s) | 41,998 (41.9980 per sampled match) |
| filtered_matches (civ+ELO) | 993 |
| filtered_match_rate | 0.9930 |
| n_with_profile_comparison | 993 |
| profile_id_agreement_rate | 0.9960 |
| n_agreements | 989 |
| 95% bootstrap CI | [0.9919, 0.9990] |
| **Verdict** | **A** |

**Verdict rubric (CI-aware):**
- A = strong if CI lower bound > 0.85 AND >= 30 filtered matches
- B = partial if CI overlaps [0.10, 0.85] OR 10 <= filtered < 30
- C = disjoint if CI upper bound < 0.10 OR < 10 filtered

**Verdict: A -- CI lower bound 0.9919 > 0.85 AND filtered >= 30 (strong namespace overlap)**

**I7 provenance for blocking thresholds:**
- 60s temporal: conventional API submission delay (exploratory heuristic).
- 50-ELO band: derived from 01_03_03 finding (max_abs_deviation=0.0 for 1v1
  scope); 50 is ~100x conservative.

---

## Decision Ledger -- DS-AOESTATS-IDENTITY-01..05

### DS-AOESTATS-IDENTITY-01 (identity-key)

**Column:** profile_id (players_raw DOUBLE; player_history_all BIGINT; matches_1v1_clean p0/p1_profile_id BIGINT)

**Finding:** profile_id is the sole identity signal. No nickname column exists in any raw table (14 cols in players_raw, 0 name/display/nick fields). I2 canonical-nickname invariant is natively unmeetable for aoestats. profile_id is free of NULL (in player_history_all), zero, negative, and -1 sentinel values. Cardinality: 641,662 distinct profiles. Type asymmetry: DOUBLE in players_raw (DuckDB promotion artifact); BIGINT in all views (safe for integer comparison after CAST).

**Recommendation:** USE profile_id (BIGINT) as the Phase 02 entity key for aoestats. Document absence of nickname. Do not attempt to merge profiles via handle similarity -- no handle data exists.

**Action:** Phase 02 design uses profile_id as identity key for aoestats.

---

### DS-AOESTATS-IDENTITY-02 (NULL/sentinel)

**Column:** players_raw.profile_id (1,185 NULLs)

**Finding:** players_raw has 1,185 NULL profile_id rows (0.001% of 107.6M rows). These are excluded by the player_history_all filter (profile_id IS NOT NULL). No zero, negative, or -1 sentinel detected in any profile_id column across all 3 objects audited. Task C confirms 489 duplicate (game_id, profile_id) rows via census-aligned COALESCE key -- matching 01_03_01 anchor (drift=0).

**Recommendation:** No additional sentinel handling required. The 01_04_00 filter (profile_id IS NOT NULL) already resolves the NULL population. 489 duplicates are negligible (< 0.001%) and carry no signal for identity resolution.

**Action:** No VIEW DDL changes needed. Document in Phase 02 as known clean.

---

### DS-AOESTATS-IDENTITY-03 (rename-detection-substitute)

**Column:** civ distribution (player_history_all); replay_summary_raw (players_raw)

**Finding:** Without nickname: civ-fingerprint JSD serves as the best available behavioural surrogate. Within-profile JSD (first-half vs second-half): median=0.1262, p95=0.3472. Cross-profile JSD control (random pairs): median=0.3606, p95=0.6257. The within-profile distribution is consistently lower than cross-profile, confirming temporal stability. However: Hahn et al. 2020 (SC2 APM/build-order) is adjacent, not direct. Civ-marginal JSD over <= 50 civs with meta drift is a coarse proxy. replay_summary_raw is 13.95% non-empty; content is Python dict format (not JSON); contains 'opening_name' key (name extraction feasible via ast.literal_eval but deferred -- out of scope for this step).

**Recommendation:** Rename/multi-account resolution for aoestats remains unsolved. Civ-fingerprint JSD is NOT sufficient as a standalone rename detector. Flag for CROSS PR if cross-dataset bridge (Task G verdict) is pursued. replay_summary_raw name extraction deferred to dedicated step.

**Action:** Phase 02 uses profile_id as-is. Record I2 limitation in thesis §4.2.2.

---

### DS-AOESTATS-IDENTITY-04 (collision)

**Column:** profile_id (cross-table type collision: DOUBLE vs BIGINT)

**Finding:** players_raw stores profile_id as DOUBLE (DuckDB Arrow promotion from Parquet mixed-type weekly files). All analytical views cast to BIGINT. Range: min=18, max=24,853,897 -- well within BIGINT safe range (no precision loss in DOUBLE-to-BIGINT cast for integers <= 2^53). Multi-ladder profiles: 269,107 of 641,662 profiles appear in > 1 leaderboard (random_map, team_random_map, co_random_map, co_team_rm). Profile-level collision risk: negligible (global namespace, no region-scoped ID like sc2egset toon_id).

**Recommendation:** Always CAST(profile_id AS BIGINT) when joining players_raw to views. Multi-ladder profiles are expected -- the same player may have different rating trajectories per leaderboard. Phase 02 should scope rating computation to leaderboard='random_map' for 1v1 RM.

**Action:** Document type cast in Phase 02 feature pipeline docstring.

---

### DS-AOESTATS-IDENTITY-05 (cross-dataset-bridge)

**Column:** profile_id (aoestats) vs profileId (aoec)

**Finding:** Cross-dataset feasibility (Task G): 1,000-match reservoir from 2026-01-25..2026-01-31. Blocking: 60s temporal + civ-set + 50-ELO. filtered_hits=993, profile_id_agreement_rate=0.9960, 95% bootstrap CI=[0.9919, 0.9990]. Verdict: A -- CI lower bound 0.9919 > 0.85 AND filtered >= 30 (strong namespace overlap). aoestats profile_id and aoe2companion profileId appear to share the same integer namespace (both from aoe2insights.com API lineage). This enables a cross-dataset name bridge: aoe2companion.name can serve as I2 canonical nickname for aoestats via profile_id=profileId join.

**Recommendation:** Proceed with cross-dataset profile_id bridge for the name resolution path. Full mapping deferred to CROSS PR (not Phase 01 scope). Conditional on aoec T06 verdict agreement (symmetric rubric).

**Action:** Flag for CROSS PR. Thesis §4.2.2 can note namespace-sharing as empirically supported by Task G agreement rate.

---

## Synthesis

1. **Identity key:** `profile_id` (BIGINT) is clean, sentinel-free, and globally
   scoped (no region sharding unlike sc2egset toon_id). Use as Phase 02 entity key.

2. **I2 limitation:** aoestats has no nickname column. I2 is natively unmeetable
   without a cross-dataset bridge. This is documented as a dataset characteristic.

3. **Civ-fingerprint stability:** Within-profile JSD (median=0.1262)
   is substantially lower than cross-profile control (median=0.3606),
   confirming temporal civ-preference stability. However, this cannot serve as a
   rename detector without ground truth labels.

4. **replay_summary_raw:** Contains `opening_name` (Python dict format). Name
   extraction is feasible but deferred to a dedicated step.

5. **Cross-dataset bridge (Task G):** Verdict A. aoestats `profile_id`
   and aoe2companion `profileId` appear to share the same integer namespace
   (agreement rate 0.9960, 95% CI [0.9919, 0.9990]).
   A direct join on profile_id=profileId would provide aoe2companion player names
   for aoestats profiles. Full cross-dataset mapping is a CROSS PR deliverable.

**Scientific invariants:** I2 (natively unmeetable -- documented). I6 (all SQL
verbatim in JSON). I7 (all thresholds provenance documented). I9 (no upstream
modification).
