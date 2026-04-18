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

**Tolerance and accepted bias:** The ~12% cross-region duplication (same physical player under multiple `player_id_worldwide` values) is accepted bias because no stable worldwide alternative exists without manual curation. The 294 Class A cross-region candidate pairs are deferred to a future manual-curation upgrade path. (01_04_04b)

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

Populated by 01_05 (Temporal & Panel EDA) and Phase 02. No pre-wired subsections.

## §5 Cross-reference to `.claude/scientific-invariants.md`

See the universal invariants file linked above for the full I1–I10+ list. Exceptions (VIOLATED or PARTIAL status) for this dataset are enumerated below; rows with no deviation are omitted by design.

| Invariant | Status | Notes |
|---|---|---|
| I2 | PARTIAL | Deviates to branch (iii): `player_id_worldwide` (full `R-S2-G-P`) used as the canonical key instead of `LOWER(nickname)`. Within-region collision 30.6%; cross-region duplication ~12% accepted bias. See §2. |
