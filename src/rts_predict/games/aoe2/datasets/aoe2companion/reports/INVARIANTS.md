# Empirical Invariants — aoe2/aoe2companion

Dataset-specific empirical findings. Counterpart to `.claude/scientific-invariants.md` (universal invariants) per L206–207.

## §1 Data-source invariants

(Seeded from 01_01/01_02 research_log entries: schema facts, raw cardinality, NULL/sentinel policies.)

- **File layout:** 2,073 daily match Parquets, 2,072 daily rating CSVs, 1 leaderboard Parquet, 1 profile Parquet. Sourced from the aoe2insights.com / aoe2companion API. (01_02_02)
- **Raw tables:** `matches_raw` (277,099,059 rows, 55 columns); `ratings_raw` (58,317,433 rows, 8 columns); `leaderboards_raw` (2,381,227 rows, 19 columns); `profiles_raw` (3,609,686 rows, 14 columns). (01_02_02, 01_02_03)
- **Key types:** `profileId` (INTEGER, camelCase) in `matches_raw`, `leaderboards_raw`, `profiles_raw`. `profile_id` (BIGINT, snake_case) in `ratings_raw`. Naming inconsistency noted for Phase 02 join design. (01_02_03)
- **NULL policy:** `matches_raw.won` has 12,985,561 NULLs (4.69%) — root cause established in 01_02_01: non-1v1 or abandoned matches. `matchId` and `filename` are zero-NULL. `ratings_raw.profile_id` and `filename` are zero-NULL. (01_02_02)
- **Sentinel:** `profileId = -1` appears as: `status='ai'` (12,947,078 rows, 4.67%) and `status='player'` (19,232 rows, negligible). All Phase 02 features filter `WHERE profileId != -1`. (DS-AOEC-IDENTITY-02; 01_04_04)
- **Duplicate policy:** 8,812,005 excess rows on `(matchId, profileId)` primary key across full table (01_02_04 census). In rm_1v1 1v1 scope only 5 excess rows — deduplication applied in `matches_1v1_clean` VIEW. (01_04_01, 01_04_02)
- **Cleaned prediction table:** `matches_1v1_clean` — 61,062,392 rows / 30,531,196 match-pairs (rm_1v1 + qp_rm_1v1 leaderboards, deduplicated, profileId=-1 excluded). `player_history_all` retains 264,132,745 rows across 21 leaderboard types for feature computation. (01_04_01, 01_04_02)
- **NULL cluster:** A 10-column NULL cluster spans all 70 months (2020-07 to 2026-04) at <0.02% per month. Not concentrated in a schema-change era. Flagged as `is_null_cluster` in `matches_1v1_clean`; retained for sensitivity analysis. (01_04_01)
- **Duration:** `duration_seconds` computed as `CAST(EXTRACT(EPOCH FROM (finished - started)) AS BIGINT)`. 142 suspicious rows (>86,400s); 342 strict-negative rows (clock-skew); 16 zero-duration rows. Max legitimate: 3,279,303s (~38 days wall-clock from abandoned/paused matches). (01_04_02 ADDENDUM)

## §2 Identity invariants

(Cites I2 meta-rule in `.claude/scientific-invariants.md`.)

**I2 decision for aoe2companion: Branch (i) — API-namespace ID.**

- **Chosen key:** `profileId` (INTEGER) from the aoe2insights.com API. Rename-stable: a player who changes their visible name retains the same `profileId`. (DS-AOEC-IDENTITY-01; 01_04_04)
- **Identity scope:** Global aoe2insights.com namespace.

**Measured rates (Step 2):**

```sql
-- rename_rate: profileIds that appear under more than one name in their history
SELECT COUNT(*) FILTER (WHERE name_count > 1) * 1.0 / COUNT(*) AS rename_rate
FROM (
    SELECT profileId, COUNT(DISTINCT name) AS name_count
    FROM player_history_all
    GROUP BY profileId
) sub;
-- Result: ~2.6% (DS-AOEC-IDENTITY-03; 01_04_04)

-- cross_scope_collision_rate: names that map to more than one profileId
SELECT COUNT(*) FILTER (WHERE id_count > 1) * 1.0 / COUNT(*) AS collision_rate
FROM (
    SELECT name, COUNT(DISTINCT profileId) AS id_count
    FROM player_history_all
    GROUP BY name
) sub;
-- Result: 3.7% (22,186 collision names / 631,620 + 22,186 total; DS-AOEC-IDENTITY-04; 01_04_04)
```

- `migration_rate` (rename instability): ~2.6% of profiles renamed (name cannot serve as primary key alone; DS-AOEC-IDENTITY-03)
- `cross_scope_collision_rate` (name-to-profileId collision): 3.7% — 22,186 names map to 2+ profileIds; top collider has 249 distinct profileIds. (DS-AOEC-IDENTITY-04; 01_04_04)

**Branch selected:** (i) — API-namespace ID. `profileId` is rename-stable and yields lower `max(migration_rate, cross_scope_collision_rate)` than any name-based alternative.

**Tolerance:** `profileId` is rename-stable — no tolerance threshold needed for the identifier itself. The 3.7% collision rate applies to `name` alone, not to `profileId`.

**Rejected candidates:**

| Candidate | Reason for rejection |
|---|---|
| `name` alone | 2.6% rename instability; 3.7% collision rate — fails for both migration and collision (DS-AOEC-IDENTITY-03/04; 01_04_04) |
| `(name, country)` composite | country has 2.25% NULL in matches_1v1_clean; does not resolve collision on rename; adds join complexity without rate benefit (01_04_04) |

## §3 Temporal invariants

(Seeded from 01_04_01.)

- **Temporal anchor:** `started` (TIMESTAMP) in `matches_raw` — zero NULLs. Pass-through as `started_at` in `matches_history_minimal` (no cast required). (01_04_03)
- **Coverage:** 2020-07 to 2026-04. NULL cluster at <0.02%/month spans the full period uniformly. (01_04_01)
- **rating temporal status:** `matches_raw.rating` confirmed PRE-GAME at 99.8% exact match with `ratings_raw` pre-match entries (01_03_03 row-level validation). No leakage risk.
- **`ratings_raw`:** Has zero rows with `leaderboard_id = 6` (rm_1v1). Provides only lb=0 (unranked) and lb=3/4 (dm_team) rating trajectories. Phase 02 rating features must derive from `matches_raw.rating` for rm_1v1. (01_03_03)
- **`profiles_raw`:** No temporal dimension — not usable for temporal features. Adds steamId/clan (99.9% non-null) but excluded from feature computation. (01_03_03)
- **duration_seconds is POST_GAME_HISTORICAL:** Derived from `finished - started`; only known after match ends. Excluded from PRE_GAME feature sets by default via I3 token. (01_04_02 ADDENDUM; 01_04_03)
- **Reservoir-sample reproducibility caveat**: DuckDB `USING SAMPLE reservoir(N ROWS) REPEATABLE(seed)` is deterministic only for fixed input row-order. `matches_raw` physical/segment order shifts on rebuild; the same seed can yield different samples across rebuilds. Consequence: bit-exact reproduction of 01_04_04 reservoir-based findings across DB rebuilds is NOT guaranteed. Findings remain methodologically equivalent (conclusions preserved), but specific numeric triples are post-rebuild-specific. Document the rebuild state (DB mtime vs artifact mtime) when citing reservoir-derived numbers.

## §4 Per-dataset empirical findings

Populated by 01_05 (Temporal & Panel EDA) and Phase 02. No pre-wired subsections.

## §5 Cross-reference to `.claude/scientific-invariants.md`

See the universal invariants file linked above for the full I1–I10+ list. Exceptions (VIOLATED or PARTIAL status) for this dataset are enumerated below; rows with no deviation are omitted by design.

| Invariant | Status | Notes |
|---|---|---|
| I2 | PARTIAL | Deviates to branch (i): `profileId` (API-namespace INTEGER) used instead of `LOWER(nickname)`. Rename rate ~2.6%; name collision rate 3.7%. `profileId` is rename-stable — lower `max(rate)` than any name-based key. See §2. |
