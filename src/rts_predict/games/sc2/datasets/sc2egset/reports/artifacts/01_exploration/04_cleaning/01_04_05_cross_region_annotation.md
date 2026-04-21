# Step 01_04_05 — Cross-Region Fragmentation Phase 01 Annotation

**Dataset:** sc2egset
**Phase:** 01 — Data Exploration
**Pipeline Section:** 01_04 — Data Cleaning
**Date:** 2026-04-21
**Artifact type:** Step report (MD)
**Paired JSON:** `01_04_05_cross_region_annotation.json`
**Notebook:** `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_05_cross_region_annotation.py`

---

## §1 Scope and Motivation

WP-3 (step 01_05_10) empirically FAILed the Phase 01 "accepted bias" framing for
cross-region fragmentation:

- At window=30: median rolling-window undercount = 16.0 games, p95 = 29.0 games
  (thresholds: median ≤ 1, p95 ≤ 5 — both FAIL).
- MMR-fragmentation Spearman ρ bootstrap 95% CI upper = 0.2913 (threshold < 0.20 — FAIL).
- Rare-handle subsample (length ≥ 8, n=96 nicknames): median=7.0, p95=29.0 — consistent
  FAIL verdict; bias is genuine fragmentation, not solely short-handle collision.

User directive 2026-04-21: address issues in the responsible phase rather than spilling
responsibilities between phases (`docs/PHASES.md` §Phase 01 01_04 discipline). This step
adds `is_cross_region_fragmented` BOOLEAN to `player_history_all` VIEW so Phase 02
consumers can operationalize the accepted-bias framing without re-deriving the cross-region
set per query. The classification remains "accepted bias" — this step adds the
operationalization mechanism, not a revision of the I2 branch choice.

---

## §2 SQL Verbatim (I6)

### Cross-region toon identification

```sql
-- CTE: identify toon_ids whose LOWER(nickname) appears in 2+ regions
WITH cross_region_toons AS (
    SELECT DISTINCT toon_id
    FROM replay_players_raw
    WHERE LOWER(nickname) IN (
        SELECT LOWER(nickname)
        FROM replay_players_raw
        GROUP BY LOWER(nickname)
        HAVING COUNT(DISTINCT region) > 1
    )
)
```

### Before amendment (player_history_all v2 — 37 cols, from 01_04_02)

```sql
CREATE OR REPLACE VIEW player_history_all AS
-- Column set: 37 columns. Source: FROM matches_flat mf WHERE mf.replay_id IS NOT NULL.
SELECT
    mf.replay_id, mf.filename, mf.toon_id, mf.nickname, mf.playerID, mf.userID,
    mf.result, (mf.result IN ('Win', 'Loss')) AS is_decisive_result,
    CASE WHEN mf.MMR = 0 THEN TRUE ELSE FALSE END AS is_mmr_missing,
    mf.race,
    CASE WHEN mf.selectedRace = '' THEN 'Random' ELSE mf.selectedRace END AS selectedRace,
    mf.region, mf.realm, mf.isInClan,
    NULLIF(mf.APM, 0) AS APM, (mf.APM = 0) AS is_apm_unparseable,
    CASE WHEN mf.SQ = -2147483648 THEN NULL ELSE mf.SQ END AS SQ,
    mf.supplyCappedPercent, mf.header_elapsedGameLoops,
    mf.startDir, mf.startLocX, mf.startLocY,
    mf.metadata_mapName,
    CASE WHEN mf.gd_mapSizeX = 0 THEN NULL ELSE mf.gd_mapSizeX END AS gd_mapSizeX,
    CASE WHEN mf.gd_mapSizeY = 0 THEN NULL ELSE mf.gd_mapSizeY END AS gd_mapSizeY,
    mf.gd_maxPlayers, mf.details_isBlizzardMap, mf.gd_mapAuthorName,
    mf.gd_mapFileSyncChecksum, mf.details_timeUTC,
    mf.header_version, mf.metadata_baseBuild, mf.metadata_dataBuild, mf.metadata_gameVersion,
    mf.go_amm, mf.go_clientDebugFlags, mf.go_competitive
FROM matches_flat mf
WHERE mf.replay_id IS NOT NULL;
```

### After amendment (player_history_all v3 — 38 cols, this step)

```sql
CREATE OR REPLACE VIEW player_history_all AS
WITH cross_region_toons AS (
    SELECT DISTINCT toon_id
    FROM replay_players_raw
    WHERE LOWER(nickname) IN (
        SELECT LOWER(nickname)
        FROM replay_players_raw
        GROUP BY LOWER(nickname)
        HAVING COUNT(DISTINCT region) > 1
    )
)
-- Column set: 38 columns (37 from 01_04_02 + is_cross_region_fragmented from 01_04_05).
SELECT
    mf.replay_id, mf.filename, mf.toon_id, mf.nickname, mf.playerID, mf.userID,
    mf.result, (mf.result IN ('Win', 'Loss')) AS is_decisive_result,
    CASE WHEN mf.MMR = 0 THEN TRUE ELSE FALSE END AS is_mmr_missing,
    mf.race,
    CASE WHEN mf.selectedRace = '' THEN 'Random' ELSE mf.selectedRace END AS selectedRace,
    mf.region, mf.realm, mf.isInClan,
    NULLIF(mf.APM, 0) AS APM, (mf.APM = 0) AS is_apm_unparseable,
    CASE WHEN mf.SQ = -2147483648 THEN NULL ELSE mf.SQ END AS SQ,
    mf.supplyCappedPercent, mf.header_elapsedGameLoops,
    mf.startDir, mf.startLocX, mf.startLocY,
    mf.metadata_mapName,
    CASE WHEN mf.gd_mapSizeX = 0 THEN NULL ELSE mf.gd_mapSizeX END AS gd_mapSizeX,
    CASE WHEN mf.gd_mapSizeY = 0 THEN NULL ELSE mf.gd_mapSizeY END AS gd_mapSizeY,
    mf.gd_maxPlayers, mf.details_isBlizzardMap, mf.gd_mapAuthorName,
    mf.gd_mapFileSyncChecksum, mf.details_timeUTC,
    mf.header_version, mf.metadata_baseBuild, mf.metadata_dataBuild, mf.metadata_gameVersion,
    mf.go_amm, mf.go_clientDebugFlags, mf.go_competitive,
    (mf.toon_id IN (SELECT toon_id FROM cross_region_toons)) AS is_cross_region_fragmented
FROM matches_flat mf
WHERE mf.replay_id IS NOT NULL;
```

---

## §3 Column Definition

| Property | Value |
|----------|-------|
| Column name | `is_cross_region_fragmented` |
| Type | `BOOLEAN` |
| Nullable | `false` |
| Classification | `CONTEXT` |
| Position | 38th column (last) |

**Semantics:** TRUE iff the row's `toon_id` belongs to the set of cross-region toon_ids.
A toon_id is cross-region if its LOWER(nickname) appears in 2 or more distinct `region`
values within `replay_players_raw`. The flag is populated by construction for all rows
(no NULL). The derivation is purely from `replay_players_raw` — no temporal dependency,
no circular use of the target variable.

**Derivation:** Sub-select IN clause filters to toon_ids matched by nickname-based
cross-region detection. The CTE `cross_region_toons` is prepended to the VIEW DDL so the
computation runs once per query execution within the VIEW scope.

---

## §4 Flag Population Statistics

| Metric | Value |
|--------|-------|
| `rows_flagged_true` | 37,101 |
| `rows_flagged_false` | 7,716 |
| Total rows (row count preserved) | 44,817 |
| `flagged_toons_distinct` | 1,923 |
| `toon_id_count` (from cross_region_toons CTE) | 1,923 |
| NULL in `is_cross_region_fragmented` | 0 |

Row count invariance: 37,101 + 7,716 = 44,817. Confirmed.
`flagged_toons_distinct` == `toon_id_count` (1,923). Confirmed.

---

## §5 Handle-Length Breakdown

Distribution of distinct flagged toon_ids by minimum nickname length
(using minimum across all nicknames observed for that toon_id):

| Bucket | Toon count |
|--------|-----------|
| length < 5 | 636 |
| length 5–7 | 831 |
| length ≥ 8 | 456 |
| **Total flagged toons** | **1,923** |

Note: breakdown is per distinct (toon_id, nickname) pair count = 2,294 total pairs
(some toons observed with multiple nicknames across regions). The per-toon-id breakdown
above uses the minimum nickname length as the representative measure.

---

## §6 Blanket-Flag Conservatism Argument

The flag is blanket (no handle-length filter) by design.

**Rationale:** Length-filtered flags (e.g., length ≥ 8 per WP-3 §6 rare-handle subsample)
could miss genuine cross-region players with short handles. The false-positive rate is
bounded by the length-<5 count (636 toons with minimum nickname length < 5): these
short-handle toons are more likely handle-collision artifacts than genuine same-player
fragmentation. However, WP-3 §6 itself showed that even the rare-handle (length ≥ 8)
subsample FAILed both rolling-window thresholds (median=7.0, p95=29.0) — confirming the
bias is not solely a short-handle issue.

**Phase 02 flexibility:** Phase 02 may subset to `LENGTH(nickname) ≥ 8` via an additional
JOIN for strict sensitivity analysis; the blanket flag is the conservative default.

**Trade-off:** Under-flagging misses real bias; over-flagging dilutes sensitivity signal.
This step chooses over-flagging as the safer Phase-02-informing default, because Phase 02
planners have full visibility into the breakdown (§5 above) to make an informed filtering
choice. The 636 lt_5 toons (33% of 1,923) represent the upper bound on potential
false-positives; the actual false-positive rate is likely lower since some short handles
are genuine cross-region players.

---

## §7 Phase 02 Usage Guidance

Phase 02 rolling-window features computed over `player_id_worldwide` (= `toon_id`) should
account for cross-region fragmentation using one of three strategies:

1. **Safe-subset filter:** `WHERE NOT is_cross_region_fragmented` — restricts history
   to non-fragmented players; cleanest rolling-window estimates but reduces the training
   population to **7,716 / 44,817 rows = 17.2%** of the corpus (tournament players are
   over-represented among the 1,923 flagged toons; see §4 flag distribution). This is a
   material data loss; strategy (2) or (3) are usually preferable for non-catastrophic
   bias levels.

2. **Dual feature paths:** Compute rolling-window features for all players, then add
   `is_cross_region_fragmented` as a covariate in the model. The model learns to adjust
   for the known fragmentation bias.

3. **Sensitivity indicator:** Use the flag to partition evaluation metrics by
   `is_cross_region_fragmented` and report differential model performance. Documents
   remaining bias for the thesis.

**Phase 02 planning decision:** Which strategy to apply is Phase 02's responsibility;
this annotation provides the necessary operationalization at Phase 01 level.
