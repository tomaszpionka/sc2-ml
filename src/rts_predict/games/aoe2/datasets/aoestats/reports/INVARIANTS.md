# Empirical Invariants — aoe2/aoestats

Dataset-specific empirical findings. Counterpart to `.claude/scientific-invariants.md` (universal invariants) per L206–207.

## §1 Data-source invariants

(Seeded from 01_01/01_02 research_log entries: schema facts, raw cardinality, NULL/sentinel policies.)

- **File layout:** 171 Parquet files for `players_raw` (107.6M rows); Parquet files for `matches_raw` (30,690,651 rows); 1 JSON file `overview.json` for `overviews_raw` (1 row). Sourced from aoestats.io (aoe2insights.com API). (01_02_02)
- **Raw tables:** `matches_raw` (30,690,651 rows, 18 columns); `players_raw` (107,627,584 rows, 14 columns); `overviews_raw` (1 row) — singleton lookup for 19 patches (release dates 2022-08-29 to 2025-12-02), 50 civs, 10 openings. (01_02_02, 01_03_03)
- **Key types:** `profile_id` in `players_raw` ingested as DOUBLE (promoted from mixed int64/double variant across 171 files). Precision-loss risk assessed in 01_04_01: all actual `profile_id` values fall below 2^53 (min=18, max=24,853,897), so `CAST(profile_id AS BIGINT)` is lossless. Always apply `CAST(profile_id AS BIGINT)` before use. (DS-AOESTATS-IDENTITY-04; 01_04_04)
- **NULL policy:** `players_raw.profile_id` has 1,185 NULLs (0.0011%); all other identity columns zero-NULL. `matches_1v1_clean` filters `profile_id IS NOT NULL`. `player_history_all` applies the same filter. (01_04_01, 01_04_02)
- **No `name` column:** Neither `matches_raw` nor `players_raw` exposes a visible handle (player name). Identity resolution is structurally forced to use `profile_id` alone. (01_04_04)
- **No `ratings_raw` table:** `ratings_raw` does not exist for aoestats. Rating signals are available only via `players_raw.old_rating` and `players_raw.new_rating`. (01_02_02)
- **Duplicate policy:** 489 duplicate `(game_id, profile_id)` rows in `players_raw` (negligible; 0.00045%). Handled by deduplication in `player_history_all`. (01_04_01)
- **Cleaned prediction table:** `matches_1v1_clean` — 17,814,947 rows (rm_1v1 scope, `leaderboard='random_map'`). Natively one-row-per-match-half; UNION ALL pivot used in `matches_history_minimal`. (01_04_02)
- **Slot asymmetry:** Upstream `matches_raw` shows `team1_wins ≈ 52.27%` slot asymmetry (documented in `matches_1v1_clean.yaml` lines 118–125). The UNION ALL pivot in `matches_history_minimal` erases this: `overall_won_rate = 0.5` exactly post-pivot. (01_04_03)
- **Duration:** `duration_seconds` computed as `CAST(duration / 1_000_000_000 AS BIGINT)` — source is `matches_raw.duration` in Arrow `duration[ns]` mapped to BIGINT NANOSECONDS by DuckDB 1.5.1 (cites `aoestats/pre_ingestion.py:271`). 28 corrupted matches (56 player-rows, 0.00016%) with `duration > 86,400s`. Max: 5,574,815s. (01_04_02 ADDENDUM)

## §2 Identity invariants

(Cites I2 meta-rule in `.claude/scientific-invariants.md`.)

**I2 decision for aoestats: Branch (v) — structurally-forced API-namespace ID.**

- **Chosen key:** `profile_id` (BIGINT after cast) — sole identity signal in the dataset. (DS-AOESTATS-IDENTITY-01; 01_04_04)
- **Identity scope:** Global aoe2insights.com namespace (same as aoe2companion `profileId`, confirmed by VERDICT A cross-dataset bridge; 01_04_04).

**Measured rates (Step 2):**

No `name` or visible handle column exists in aoestats. Steps 2 and 3 of the I2 operational procedure are unevaluable for this dataset: there is no candidate other than `profile_id` to measure rates against. Branch (v) applies.

```sql
-- Confirm: no name column in players_raw or matches_raw
SELECT column_name FROM information_schema.columns
WHERE table_name IN ('players_raw', 'matches_raw')
  AND column_name ILIKE '%name%';
-- Result: 0 rows (no name column exists) — 01_04_04
```

- `migration_rate`: N/A — no visible handle to compare against.
- `cross_scope_collision_rate`: N/A — no visible handle to compare against.

**Cross-dataset bridge to aoe2companion:**

The aoestats `profile_id` and aoe2companion `profileId` share the same namespace (both sourced from the aoe2insights.com API). Empirical validation (01_04_04):

```sql
-- Reservoir sample (seed=20260418): 1,000 aoec matches, 2026-01-25..2026-01-31, rm_1v1
-- filtered_hits = 993, profile_id_agreement_rate = 0.9960
-- 95% CI lower bound = 0.867 > 0.50 threshold → VERDICT A: STRONG
SELECT
    COUNT(*) FILTER (WHERE a.profile_id = c.profileId) * 1.0 / COUNT(*) AS agreement_rate
FROM aoestats_sample a
JOIN aoec_matches_raw c
  ON CAST(a.profile_id AS BIGINT) = c.profileId
 AND c.started BETWEEN '2026-01-25' AND '2026-01-31';
-- Result: 0.9960, CI lower bound 0.867 — 01_04_04
```

This bridge means aoestats can obtain I2-compliant canonical nicknames via a LEFT JOIN on `aoec.matches_raw.profileId = aoestats.players_raw.profile_id` when a visible handle is needed. (DS-AOESTATS-IDENTITY-05; 01_04_04)

**Branch selected:** (v) — structurally forced. No visible handle column exists in aoestats. `profile_id` is the only identity signal; its namespace alignment with aoec `profileId` is empirically confirmed (VERDICT A).

**Tolerance:** N/A (branch (v) — no comparison candidate exists within the dataset).

**Rejected candidates:** None evaluable — dataset lacks columns required to compare candidates (no `name` column; no visible handle of any kind).

## §3 Temporal invariants

(Seeded from 01_04_01.)

- **Temporal anchor:** `started_timestamp` (TIMESTAMPTZ) in `matches_raw` — zero NULLs in rm_1v1 scope. Cast to TIMESTAMP via `CAST(started_timestamp AT TIME ZONE 'UTC' AS TIMESTAMP)` in `matches_history_minimal`. (01_04_03)
- **Coverage:** min=2022-08-29, max=2026-02-06. Zero NULL `started_at`. (01_04_03)
- **Inter-file temporal gaps:** matches/ directory contains 3 gaps (2024-07-20 → 2024-09-01 = 43 days; 2024-09-28 → 2024-10-06 = 8 days; 2025-03-22 → 2025-03-30 = 8 days); players/ directory adds a fourth 8-day gap (2025-11-15 → 2025-11-23). Filename-scan derivation at `reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md:29,38`; scanning logic at `sandbox/aoe2/aoestats/01_exploration/01_acquisition/01_01_01_file_inventory.py`. The 43-day gap is cited in thesis §4.1.2 with an in-place [REVIEW] flag on the post-patch API-schema interpretive claim. (01_01_01)
- **`overviews_raw` patch map:** 19 patches with release dates 2022-08-29 to 2025-12-02. Useful for temporal version stratification in Phase 02. (01_03_03)
- **`old_rating` PRE-GAME classification — structurally supported, empirically uncertain (FAIL):** Classified PRE-GAME structurally. **Structural evidence:** `matches_1v1_clean.yaml:excluded_columns` excludes `new_rating`/`p*_new_rating` as POST-GAME. **Empirical evidence (01_04_06, 2026-04-21):** leaderboard-partitioned consecutive-match test on `leaderboard='random_map'` (primary, n=35,275,197 pairs) yields `agreement_rate=0.9210` (Wilson 95% CI [0.9209, 0.9211]; max disagreement=1,118 rating units; median disagreement among disagreeing pairs=16). **3-gate verdict: FAIL.** Gate (a): rate 0.9210 < 0.95 AND max_disagreement 1,118 >> 50 units. Gate (b): leaderboard strata failures — `team_random_map`=0.860, `co_random_map`=0.855, `co_team_random_map`=0.787 (all < 0.90). Gate (c): time-gap failures — `1-7d`=0.859, `7-30d`=0.708, `>30d`=0.634 (all < 0.90). Short-gap (<1d) agreement=0.944 is close to 0.95, suggesting the convention holds for dense play and disagreements arise from rating resets / seasonal updates between longer gaps. **Three follow-up candidates:** (1) retain with caveat; (2) demote to CONDITIONAL_PRE_GAME pending reset-mechanism investigation; (3) filter disagreeing pairs in Phase 02 feature engineering. Decision deferred to Phase 02 planner. (01_03_01 + 01_04_06)
- **Age uptimes (feudal/castle/imperial) are IN-GAME:** High NULL rate (~87–91%) and bounded to in-match execution. Excluded from pre-game feature sets. (01_03_01)
- **duration_seconds is POST_GAME_HISTORICAL:** Derived from `duration` (NANOSECONDS); only known after match ends. Excluded from PRE_GAME feature sets by default via I3 token. (01_04_02 ADDENDUM; 01_04_03)
- **Slot bias:** Upstream `team1_wins ≈ 52.27%` documented in `matches_1v1_clean.yaml`. UNION ALL pivot in `matches_history_minimal` corrects to `won_rate = 0.5` exactly. (01_04_03)

## §4 Per-dataset empirical findings

### I5 finding from 01_04_05 (Team-Slot Asymmetry Diagnosis)

The upstream 52.27% team=1 win rate in `matches_1v1_clean` is an API-assigned ordering
artifact (ARTEFACT_EDGE verdict, Step 01_04_05). Team=1 has higher ELO in 80.3% of games
(mean +11.9 ELO points), consistent with the aoestats API assigning team=1 to the
invite-initiating or better-matched player. After stratifying by civ-pair and year-quarter
(13,509 strata, Mantel-Haenszel CMH), the civ-lexicographic-first win rate is 0.4928
(effect = -0.72pp), well below the 1.5pp GENUINE_EDGE floor. The `team` field reflects
upstream API ordering, NOT a game-mechanical slot identity; it must NOT be used as a
Phase 02 feature. The UNION-ALL pivot in `matches_history_minimal` (produces `won_rate = 0.5`
exactly) is confirmed correct and I5-compliant. Source: `01_04_05_i5_diagnosis.{json,md}`.

**Amendment (2026-04-20 — BACKLOG F1 + W4).** The `canonical_slot VARCHAR`
column is added to `matches_history_minimal` via hash-on-match_id derivation
(`CASE WHEN (hash(match_id) + focal_team) % 2 = 0 THEN 'slot_A' ELSE 'slot_B' END`).
Skill-orthogonal by structural construction: both rows of any match share the
same match_id (UNION-ALL of a 1-row-per-match source), hence the same
hash(match_id); the binary splitter with focal_team ∈ {0,1} pivot distributes
them into complementary slots. The argument is independent of match_id's
semantic content — no empirical claim about its origin is required.
Profile_id-ordered and old_rating-ordered alternatives were both explicitly
rejected (profile_id correlates with account age per Q4 of this same artifact;
old_rating is skill-coupled by construction). I5 transitions PARTIAL → HOLDS
in §5. Artifact: `01_04_03b_canonical_slot_amendment.{json,md}`.

### 01_05 findings (Pipeline Section 01_05 -- Temporal & Panel EDA)

**Reference window:** 2022-Q3, 2022-08-29..2022-10-27, patch 66692 (corrected from spec plan's 125283; empirically verified from `overviews_raw`). 744 cohort players (>=10 matches in reference period), 37,632 reference rows.

**PSI verdict (01_05_02): PASSED.**
Rating features (focal_old_rating, avg_elo) show PSI >= 0.10 in 6 of 8 quarters (2023-Q1..2024-Q4), indicating meaningful distributional drift warranting feature engineering attention. Faction and map PSI < 0.25 in all quarters (no hard shift). Counterfactual reference (2023-Q1) confirms drift direction is consistent (B3 critique fix).

**Patch heterogeneity / Simpson probe (01_05_03): EXAMINED.**
19 patches across the study period. Patch-specific win rates vary (Chitayat et al. 2023 probe). patch_heterogeneity_decomposition.csv emitted. No cross-patch uniform-confounding falsifier triggered; patch heterogeneity is a feature engineering concern for Phase 02.

**Survivorship (01_05_04): DOCUMENTED.**
Unconditional survivorship CSV (10 quarters) emitted. Attrition pattern documented. No survivorship block (no falsifier triggered).

**ICC (01_05_05): FALSIFIED.**
ANOVA ICC (50k stratified sample) = 0.0268, below the 0.05 threshold. LMM failed to converge (small reference cohort, 744 players). Interpretation: per-player variance explains ~2.7% of total variance in `won` in the reference period. This reflects the EARLY CRAWLER PERIOD (2022-Q3) with very few active players captured. ICC should be re-evaluated in a later, denser quarter. M7 limitation: ICC = upper bound on per-player variance share; within-aoestats migration/collision unevaluable (branch v).

**Leakage audit (01_05_06): PASS.**
Q7.1: no future-data leakage in reference edges. Q7.2: no POST_GAME/TARGET tokens in feature list. Q7.3: reference window assertion confirmed. Q7.4: canonical_slot absent ([PRE-canonical_slot] flag ACTIVE). All four queries pass.

**DGP diagnostics (01_05_07): PASSED.**
duration_seconds excluded from PSI per spec §4. DGP diagnostic CSVs emitted for 2022-Q3Q4ref + 8 primary quarters.

**Phase 06 interface (01_05_08): 134 rows, 9 columns.**
reference_window_id = "2022-Q3-patch66692" for primary rows. Counterfactual rows carry reference_window_id = "2023-Q1-alt". Schema validation: column_count_ok=True, no string NaN, n_rows >= 64.

**BACKLOG F1:** canonical_slot column absent from matches_history_minimal -- required before per-slot breakdown in Phase 02. Must be resolved as a Phase 02 prerequisite. Gate memo (01_05_09) documents this explicitly.

## §5 Cross-reference to `.claude/scientific-invariants.md`

See the universal invariants file linked above for the full I1–I10+ list. Exceptions (VIOLATED or PARTIAL status) for this dataset are enumerated below; rows with no deviation are omitted by design.

| Invariant | Status | Notes |
|---|---|---|
| I2 | PARTIAL | Structurally forced to branch (v): `profile_id` is the sole identity signal — no visible handle column exists. Migration/collision rates are unevaluable within aoestats alone. Cross-dataset namespace bridge to aoec `profileId` confirmed at VERDICT A (agreement 0.9960, CI-lower 0.867; 01_04_04). See §2. |
| I5 | HOLDS (post-2026-04-20 canonical_slot amendment) | Upstream `matches_raw` slot asymmetry `team1_wins ≈ 52.27%` diagnosed as ARTEFACT_EDGE (01_04_05): API assigns team=1 to higher-ELO player in 80.3% of games. UNION-ALL pivot in `matches_history_minimal` produces `won_rate = 0.5` exactly; canonical_slot column (hash-on-match_id, 01_04_03b) provides skill-orthogonal slot labelling by construction — the hash depends only on `match_id` (a stable per-match identifier independent of player properties). `team` field MUST NOT be used as a Phase 02 feature; canonical_slot is the I5-compliant slot label. Spec §14 v1.1.0 registers this amendment. |
| I8 | PARTIAL — ICC FALSIFIED in 2022-Q3 reference | ANOVA ICC (50k) = 0.0268, below 0.05 threshold (01_05_05). Early crawler period (744 active players in 2022-Q3). ICC should be re-evaluated in a later, denser quarter before concluding lack of skill signal. Phase 02 may proceed with per-player features, but thesis must document this limitation. |
