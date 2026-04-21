# Empirical Invariants — sc2/sc2egset

Dataset-specific empirical findings. Counterpart to `.claude/scientific-invariants.md` (universal invariants) per L206–207.

## §1 Data-source invariants

(Seeded from 01_01/01_02 research_log entries: schema facts, raw cardinality, NULL/sentinel policies.)

- **File layout:** Two-level directory tree: `raw/TOURNAMENT/TOURNAMENT_data/*.SC2Replay.json`. 70 top-level tournament directories spanning 2016–2024. 22,390 replay JSON files totalling 209 GB; 431 metadata files at tournament root level. (01_01_01)
- **Raw tables:** `replay_players_raw` (44,817 rows, 25 columns); `replays_meta_raw` (22,390 rows, 17 struct leaf fields extracted); `map_aliases_raw` (104,160 rows = 70 tournaments × 1,488 entries, 4 columns). Three event views (`game_events_raw`, `tracker_events_raw`, `message_events_raw`) share identical 4-column schema. (01_02_03)
- **NULL policy:** Zero NULLs across all columns in every table and view — unique among the three datasets. Sentinel detection required instead of NULL-based imputation. (01_02_04)
- **Sentinels:** MMR=0 is "not reported" (83.65% of rows; uniform across Win/Loss — not outcome-correlated). SQ contains 2 rows with INT32_MIN sentinel (-2,147,483,648). `handicap`=0 in exactly 2 rows (observer-profile ghost entries). (01_02_04)
- **Target variable:** `result` (VARCHAR) — 4 distinct values: Loss 50.00% (22,409), Win 49.94% (22,382), Undecided 0.05% (24), Tie 0.00% (2). The 26 Undecided/Tie rows come from 13 replays with no definitive outcome. (01_02_04)
- **leaderboard_raw:** NULL for all 44,817 rows — tournament dataset, no matchmaking ladder. Deliberate placeholder in the canonical long skeleton. (01_04_00)
- **Cleaned prediction table:** `matches_flat_clean` — 44,418 rows / 22,209 replays (after R01: -24 Undecided/Tie/multi-player replays; R03: -157 MMR<0 replays). `player_history_all` retains 44,817 rows / 22,390 replays (all replays). (01_04_02)
- **Duration:** `duration_seconds` computed as `CAST(header_elapsedGameLoops / 22.4 AS BIGINT)` (game-speed "Faster" constant; `details.gameSpeed` cardinality=1 confirmed). Zero suspicious outliers (>86,400s) in sc2egset. (01_04_02 ADDENDUM)
- **Temporal range:** `started_at` (TIMESTAMP via TRY_CAST of `details.timeUTC`): min=2016-01-07, max=2024-12-01. Zero TRY_CAST failures. (01_04_03)

## §2 Identity invariants

(Cites I2 meta-rule in `.claude/scientific-invariants.md`.)

**I2 decision for sc2egset: Branch (iii) — server/region-scoped ID.**

- **Chosen key:** `player_id_worldwide` = full `R-S2-G-P` Battle.net toon_id (e.g., `1-S2-1-12345`). Implemented as the `player_identity_worldwide` VIEW. (01_04_04b)
- **Identity scope:** Per-region Battle.net account namespace. A physical player with accounts across multiple regions generates multiple `player_id_worldwide` values by design (Blizzard replay-format invariant).

**Measured rates (Step 2):**

```sql
-- within-region collision rate: distinct (nick, region) pairs that map to multiple toon_ids
SELECT COUNT(*) FILTER (WHERE toon_count > 1) * 1.0 / COUNT(*) AS collision_rate
FROM (
    SELECT LOWER(nickname), region, COUNT(DISTINCT toon_id) AS toon_count
    FROM replay_players_raw
    GROUP BY 1, 2
) sub;
-- Result: 30.6% (451 / 1,473 (nick, region) pairs) — established in 01_04_04

-- cross-region duplication upper bound: toon_ids appearing in multiple regions
SELECT COUNT(*) FILTER (WHERE region_count > 1) * 1.0 / COUNT(*) AS migration_rate
FROM (
    SELECT LOWER(nickname), COUNT(DISTINCT region) AS region_count
    FROM replay_players_raw
    GROUP BY 1
) sub;
-- Result: upper bound ~12% (246 cross-region nickname cases / 2,495 distinct toon_ids) — 01_04_04
```

- `migration_rate` (cross-region duplication bound): ~12% (246 case-sensitive nicknames observed across multiple regions; 01_04_04)
- `cross_scope_collision_rate` (within-region handle collision): 30.6% (451 / 1,473 `(nick, region)` pairs; 01_04_04)

**Branch selected:** (iii) — server/region-scoped ID. `player_id_worldwide` (full `R-S2-G-P`) delivers lower `max(migration_rate, cross_scope_collision_rate)` than any nickname-based alternative for within-scope use.

**Tolerance and accepted bias:** The ~12% cross-region duplication (same physical player under multiple `player_id_worldwide` values) is accepted bias because no stable worldwide alternative exists without manual curation. The 294 Class A cross-region candidate pairs are deferred to a future manual-curation upgrade path. (01_04_04b) Empirical impact on Phase 02 rolling-window features (01_05_10, 2026-04-21): at window=30, median undercount is 16.0 games, p95 is 29.0 games; sensitivity at windows {5, 10, 100} shows consistent FAIL (median 0/0/61, p95 5/9/98) — only W=5 has median=0 but p95 is already at the boundary. MMR-fragmentation Spearman ρ = 0.1384 (bootstrap 95% CI [-0.0086, 0.2913], n=157). Verdict: FAIL against 3-threshold gate (median_rolling30 ≤ 1 AND p95_rolling30 ≤ 5 AND |bootstrap_CI_upper(ρ)| < 0.2). Rare-handle subsample (nickname length ≥ 8, n=96) shows lower median (7 games) but equal p95 (29 games), consistent with full-sample FAIL verdict — the bias is a genuine fragmentation effect, not solely a short-handle-collision artifact. See `reports/artifacts/01_exploration/05_temporal_panel_eda/cross_region_history_impact_sc2egset.md`.

**Rejected candidates:**

| Candidate | Reason for rejection |
|---|---|
| `LOWER(nickname)` alone | 30.6% within-region collision rate — violates any reasonable threshold (01_04_04) |
| `(LOWER(nickname), server-hash)` composite | 30.6% collision persists; composite adds maintenance cost with no rate improvement over `player_id_worldwide` (01_04_04b) |
| Behavioral fingerprint (APM-JSD, race, clanTag, MMR, temporal) | Over-engineering; statistically weak at available sample sizes; circularity risk (01_04_04) |
| External bridge (Liquipedia, Aligulac, sc2pulse, Blizzard OAuth) | Web-verified infeasible: no public source exposes (nickname → region-scoped profile-id) at bulk scale (01_04_04b) |

## §3 Temporal invariants

(Seeded from 01_04_01.)

- **Temporal anchor:** `details.timeUTC` (VARCHAR in `replays_meta_raw`; TRY_CAST to TIMESTAMP in `matches_history_minimal`). Zero TRY_CAST failures across 22,390 replays. (01_04_03)
- **Coverage:** 2016-01-07 to 2024-12-01. Tournament activity peaks visible in yearly/monthly distribution. (01_02_05 plots; 01_04_03)
- **leaderboard_raw = NULL** for all rows: no matchmaking timestamp anchor exists. Temporal ordering relies exclusively on `details.timeUTC`. (01_04_00)
- **MMR is PRE-GAME:** Confirmed as ladder-rating snapshot at game time (01_02_04). No leakage risk. The 83.65% zero-MMR rate is a data-availability problem, not temporal leakage.
- **duration_seconds is POST_GAME_HISTORICAL:** Derived from `header_elapsedGameLoops`; only known after match ends. Excluded from PRE_GAME feature sets by default via I3 token. (01_04_02 ADDENDUM; 01_04_03)

## §4 Per-dataset empirical findings

Populated by 01_05 (Temporal & Panel EDA) and Phase 02.

### 01_05 Temporal & Panel EDA findings (2026-04-18)

- **Q1 Quarterly grain & overlap window:** 10 quarters 2022-Q3..2024-Q4. Overlap window:
  10,076 rows / 5,038 matches. Per-quarter counts:
  2022-Q3=1642, 2022-Q4=2844, 2023-Q1=520, 2023-Q2=1396, 2023-Q3=244, 2023-Q4=1344,
  2024-Q1=374, 2024-Q2=874, 2024-Q3=496, 2024-Q4=342. Peak-to-trough ratio: 11.7x.
  M1 correction: plan cited "2,200 obs per N=10 bin" (full dataset); overlap window
  has ~1,008 obs per bin. SQL: see artifacts/01_exploration/05_temporal_panel_eda/quarterly_row_counts_sc2egset.md (I6).

- **Q2 PSI for faction/opponent_faction/matchup:** PRIMARY = uncohort-filtered (B2 fix).
  Reference: 2022-Q3Q4 (3,268 rows). Faction PSI range: 0.001..0.220; matchup PSI range:
  0.025..0.696. FALSIFIED hypothesis: >= 3 feature-quarters exceed PSI 0.25 threshold.
  High PSI in small quarters (2023-Q3: 244 rows, 2024-Q4: 342 rows) likely driven by
  tournament-specific race composition. ε=1/3268=0.000306 (Yurdakul 2018 WMU #3208).
  SQL: see psi_quarterly_sc2egset.md (I6).

- **Q3 tournament_era (secondary regime):** Hand-mapped 70 tournament dirs via Liquipedia
  tier heuristics (tournament_tier_lookup.csv). Tier distribution: Platinum=27, Gold=37,
  Silver=4, Bronze=2. In overlap window: Gold=17044 rows, Platinum=2728, Silver=380, Bronze=0
  (no Bronze events in 2022-Q3..2024-Q4). Win-rate per tier = exactly 0.500 (symmetric
  by construction: each match has 1 winner + 1 loser in 2-row schema). Tournament tier
  is not a discriminating regime for win rate. SQL: see tournament_era_sc2egset.md (I6).

- **Q4 Cohort sizes N∈{5,10,20} (survivorship):** Reference period (2022-08-29..2022-12-31)
  has 204 distinct players. Cohort N>=10 WITHOUT span filter: 152 players (adequate).
  Cohort N>=10 WITH span>=30d: only 9 players (tournament events are 3-5 days; span filter
  inappropriate for this data structure). Uncohort-filtered overlap window: 679 distinct players,
  fraction_active per quarter 3.2%..27.7%. SQL: see survivorship_sc2egset.md (I6).

- **Q6 ICC on won:** Primary (LPM): ICC=0.0456 (95% CI [0.0058, 0.0854]). Secondary (ANOVA,
  Wu/Crespi/Wong 2012): ICC=0.0463 (95% CI [0.0283, 0.0643]). Tertiary (GLMM latent scale):
  convergence failed. Verdict: INCONCLUSIVE (0.01 < ICC < 0.05). Per-faction: Zerg ICC=0.1095
  notably higher. Spec §8 caveat: LPM ICC is at observed scale; latent-scale ICC would be higher.
  Cohort: 4,034 observations / 152 players. SQL: see variance_icc_sc2egset.md (I6).

- **Q7 Leakage audit:** future_leak_count=0; post_game_token_violations=0;
  reference_window_assertion=PASS. All reference rows confirmed within [2022-08-29, 2023-01-01).
  Features faction/opponent_faction classified PRE_GAME; duration_seconds classified
  POST_GAME_HISTORICAL (excluded from PSI). halt_triggered=False. Artifact: leakage_audit_sc2egset.json (I6).

- **Q8 duration_seconds drift:** Reference mean=725.3s, sd=358.9s. Max |Cohen's d| across
  8 tested quarters: 0.544 (2023-Q3: mean=928s, only 122 matches — likely a marathon-format
  tournament like HomeStory Cup XXIV). Verdict: FALSIFIED hypothesis (|d| > 0.2 in 3 quarters).
  is_duration_suspicious rate: 0.000 across all periods (confirmed: zero outliers > 86,400s,
  consistent with 01_04_03 ADDENDUM). SQL: see dgp_diagnostic_sc2egset.md (I6).

## §5 Cross-reference to `.claude/scientific-invariants.md`

See the universal invariants file linked above for the full I1–I10+ list. Exceptions (VIOLATED or PARTIAL status) for this dataset are enumerated below; rows with no deviation are omitted by design.

| Invariant | Status | Notes |
|---|---|---|
| I2 | PARTIAL | Deviates to branch (iii): `player_id_worldwide` (full `R-S2-G-P`) used as the canonical key instead of `LOWER(nickname)`. Within-region collision 30.6%; cross-region duplication ~12% accepted bias. See §2. |
| I8 (Spec §1) | PARTIAL | Spec §1 9-col contract (`match_id, started_at, player_id, team, chosen_civ_or_race, rating_pre, won, map_id, patch_id`) differs from actual `matches_history_minimal` VIEW schema for sc2egset: `match_id, started_at, player_id, opponent_id, faction, opponent_faction, won, duration_seconds, dataset_tag` (5 of 9 columns differ). Per M3 critique fix decision (user pre-authorized): NOT a spec amendment. Documented here as partial deviation. Phase 06 UNION joins on `metric_name` only (cross-dataset alignment). `feature_name` values in Phase 06 CSV match actual VIEW schema. |

**sc2egset scope (M7):** sc2egset is a tournament-scraped dataset. Between-player variance
estimates (ICC, PSI) reflect the **competitive/professional player population**, not the
general StarCraft II playerbase. All Phase 06 CSV rows are tagged `[POP:tournament]`.
Cross-dataset comparisons involving sc2egset should acknowledge this scope restriction.
Heckman (1979) selection bias framework applies: tournament participation is self-selected
on skill, so population-average estimates derived from sc2egset are not representative of
the full playerbase distribution.
