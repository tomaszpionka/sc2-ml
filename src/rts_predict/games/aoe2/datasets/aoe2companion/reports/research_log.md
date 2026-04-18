# Research Log — AoE2 / aoe2companion

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

AoE2 / aoe2companion findings. Reverse chronological.

---

## 2026-04-18 — [Phase 01 / Step 01_04_04] Identity Resolution

**Category:** A (science)
**Dataset:** aoe2companion
**Branch:** feat/01-04-04-identity-resolution
**Scope:** Empirical characterisation of identity signals (profileId, name, country)
across matches_raw, ratings_raw, profiles_raw. Rename detection, alias collision,
join integrity, country stability, cross-dataset feasibility preview vs aoestats.

### Key Findings

**Cardinality baseline:**
- matches_raw: 277,099,059 rows; 2,659,039 distinct profileIds; 12,966,310 sentinel=-1
  (AI/anonymized); 0 NULL; 0 INT32 overflow.
- ratings_raw: 58,317,433 rows; 821,662 distinct profile_ids; 0 sentinel; 0 NULL.
- profiles_raw: 3,609,686 rows (1 sentinel=-1 row); 3,609,686 distinct profileIds.
- Distinct names in matches_raw (non-sentinel): 2,468,341; NULL names: 625.

**Name history per profileId (rm_1v1, player_history_all):**
- Total profiles: 683,790
- Stable (1 name): 666,225 (97.42%)
- 2 names: 14,079 (2.06%)
- 3-5 names: 2,975 (0.44%)
- 6+ names: 501 (0.07%)
- Max names per profile: 75
- Rename timing (for renaming profiles): rapid_30d=6,862; within_180d=5,085; after_180d=5,935

**Name->profileId collision:**
- Unique names (1 profileId): 631,620 (96.3%)
- Collision names (2+ profileIds): 22,186 (3.7%)
- Common names (>10 profileIds): top collider has 249 distinct profileIds

**Join integrity:**
- matches_raw profileIds NOT IN profiles_raw: 0 (complete subset)
- profiles_raw profileIds NOT IN matches_raw: 950,647 (historical profiles)
- matches_raw profileIds NOT IN ratings_raw: 2,029,201 (mostly non-ranked players)
- rm_1v1 ratings_raw coverage: 262,372 / 683,790 = 38.4%

**Country stability (rm_1v1):**
- 1 country (stable): 552,409 (80.8%)
- 0 countries (all NULL): 131,141 (19.2%)
- 2+ countries (oscillating/transition): 240 (0.035%)

**Cross-dataset feasibility (2026-01-25..2026-01-31 window, rm_1v1 filter both sides):**
- VERDICT A -- STRONG -- shared namespace confirmed. CI lower bound > 0.50.
- Full window: aoec 37,495 profiles; aoestats 28,921 profiles; intersection 28,921 (100% of aoestats)
- Reservoir sample (1,000 matches, seed=20260418): ~~p_hat=0.8818, 95% CI=[0.8671, 0.8964]~~ → p_hat=0.8782, 95% CI=[0.8634, 0.8931] (canonical, from artifact JSON) [^ci-drift-2026-04-18]
- Rating agreement (50-ELO): 95.3% of 60s-window pairs

### DS-AOEC-IDENTITY Decisions

- DS-AOEC-IDENTITY-01: profileId is the primary key for Phase 02 (stable across renames)
- DS-AOEC-IDENTITY-02: sentinel=-1 confirmed; all Phase 02 features filter WHERE profileId != -1
- DS-AOEC-IDENTITY-03: 2.6% of profiles renamed; name cannot serve as primary key alone
- DS-AOEC-IDENTITY-04: 3.7% name collision; name alone is NOT safe; profileId required
- DS-AOEC-IDENTITY-05: VERDICT A -- aoec profileId and aoestats profile_id share a namespace;
  cross-dataset name-bridge feasible for Invariant I2

### Gate summary -- ALL PASS (HALTING)

- Gate 1 (JSON + MD exist): PASS
- Gate 2 (all 6 JSON blocks populated + sql_queries verbatim I6): PASS (20 SQL queries)
- Gate 3 (5+ DS-AOEC-IDENTITY-* decisions): PASS (5 decisions)
- Gate 4 (I9 empty diff: aoestats ATTACH READ_ONLY only): PASS
- Gate 5 (cross-dataset verdict with CI + sample size): PASS (VERDICT A, CI=[0.863, 0.893] [was: 0.8818, CI=[0.867, 0.896]] [^ci-drift-2026-04-18])
- Gate 6 (status files correct): PASS

### Artifacts

- `artifacts/01_exploration/04_cleaning/01_04_04_identity_resolution.json`
- `artifacts/01_exploration/04_cleaning/01_04_04_identity_resolution.md`
- `sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_04_identity_resolution.py` + `.ipynb`

**[CROSS]** VERDICT A (shared namespace) has cross-dataset implications: aoestats profile_id
and aoec profileId are the same namespace, enabling a name-bridge for Invariant I2 in aoestats.
See `reports/research_log.md` for the CROSS entry.

[^ci-drift-2026-04-18]: **Reconciliation — CI drift (2026-04-18 → 2026-04-19).** The artifact JSON `reports/artifacts/01_exploration/04_cleaning/01_04_04_identity_resolution.json` reports `p_hat = 0.8782, 95% CI = [0.8634, 0.8931]`, differing from the narrative as originally written by Δp̂ = 0.0036. Both triples clear Christen (2012) VERDICT A (CI-lower ≫ 0.50 threshold). The disagreement is attributable to DuckDB's `USING SAMPLE reservoir(N ROWS) REPEATABLE(seed)` being deterministic only for fixed input order: `matches_raw` physical/segment order shifts on any rebuild, so the same seed yields a different sample. `stat -f '%m'` evidence at reconciliation time showed `data/db/db.duckdb` mtime preceded the artifact mtime by ~1h24m on 2026-04-18, indicating a rebuild between the narrative-run and artifact-run. Bit-exact reproduction of either triple across rebuilds is not guaranteed; the artifact JSON is now canonical because it was produced by the last post-rebuild pass before commit. The VERDICT A identity-resolution conclusion is preserved under either triple. See aoec `INVARIANTS.md` §3 for the permanent reproducibility caveat.

---

## 2026-04-18 — [Phase 01 / Step 01_04_02] Data Cleaning Execution — ADDENDUM: duration_seconds + outlier flags (48 -> 51 cols)

**Category:** A (science)
**Dataset:** aoe2companion
**Branch:** feat/01-04-02-duration-augmentation
**Scope:** Extended `matches_1v1_clean` VIEW from 48 to 51 columns by adding `duration_seconds` BIGINT, `is_duration_suspicious` BOOLEAN, `is_duration_negative` BOOLEAN. Centralizes duration provenance at cleaning stage so all downstream consumers inherit outlier flags without re-deriving.

### Derivation

```sql
CAST(EXTRACT(EPOCH FROM (r.finished - d.started)) AS BIGINT) AS duration_seconds
(duration_seconds > 86400) AS is_duration_suspicious
(duration_seconds < 0)     AS is_duration_negative  -- strict < 0 per Q2 resolution
```

JOIN pattern: `LEFT JOIN (SELECT matchId, MIN(finished) AS finished FROM matches_raw GROUP BY matchId) r ON r.matchId = d.matchId` — avoids cartesian blow-up. DuckDB 1.5.1 VIEW works for this pattern (empirically verified via pre-flight test: 61,062,392 rows returned).

### Duration stats (aoec matches_1v1_clean)

- min: -3,041s
- p50: 1,433s (~24 min)
- p99: 3,458s (~58 min)
- max: 3,279,303s (~38 days — 142 bogus wall-clock rows)
- null_count: 0 (0.0%)
- suspicious_count (>86400): 142
- negative_count (strict <0): 342
- zero_duration_count: 16 (UNFLAGGED by both flags — known state for Phase 02)

### Gate summary — ALL 13 PASS (HALTING)

- Gate 1 (DESCRIBE 51 cols; last 3 = duration_seconds BIGINT + is_duration_suspicious BOOLEAN + is_duration_negative BOOLEAN): PASS
- Gate 2 (row count 61,062,392; distinct matchId 30,531,196): PASS
- Gate 3 (NULL fraction <= 1%): PASS (0.0%)
- Gate 4 (MAX duration_seconds <= 1,000,000,000): PASS (max 3,279,303)
- Gate 5 (is_duration_suspicious == 142, HALTING): PASS
- Gate 6 (is_duration_negative == 342, strict <0, HALTING): PASS
- Gate 7 (schema YAML 51 cols + schema_version ADDENDUM + I3 extended): PASS
- Gate 8 (I9: upstream YAMLs untouched): PASS
- Gate 9 (validation JSON all_assertions_pass: true + sql_queries verbatim): PASS
- Gate 10 (R03 complementarity intact; legacy cols present): PASS

### I7 provenance

86,400s threshold: from 01_04_03 Gate+5b empirical precedent (~25x p99=3,458s); Tukey (1977) EDA sanity bound; I8 cross-dataset canonical (identical threshold across sc2egset/aoestats/aoe2companion).

### STEP_STATUS

stays `complete` (addendum pattern per 01_04_03 ADDENDUM precedent; no phase-gate regression).

### Artifacts

- `artifacts/01_exploration/04_cleaning/01_04_02_duration_augmentation.json`
- `artifacts/01_exploration/04_cleaning/01_04_02_duration_augmentation.md`
- `data/db/schemas/views/matches_1v1_clean.yaml` (51 cols, schema_version ADDENDUM 2026-04-18)

---

## 2026-04-18 — [Phase 01 / Step 01_04_03] Minimal Cross-Dataset History View — ADDENDUM: duration_seconds (9-col extension)

**Category:** A (science)
**Dataset:** aoe2companion
**Branch:** feat/01-04-03-aoe2-minimal-history
**Scope:** Extended `matches_history_minimal` TABLE from 8 cols → 9 cols by adding `duration_seconds` BIGINT (POST_GAME_HISTORICAL). DuckDB 1.5.1 workaround (TABLE instead of VIEW) preserved.

### Derivation (R1-WARNING-A6 fix — in-place, no new JOIN)
`CAST(EXTRACT(EPOCH FROM (r.finished - r.started)) AS BIGINT)` — added to `_mhm_base` staging SELECT list (matches_raw `r` already joined there; no additional JOIN needed). Self-join in final TABLE propagates duration_seconds symmetrically between the 2 rows per match.

### Gate split
- **Gate +5a (HALTING)** — unit regression canary: `max(duration_seconds) <= 1_000_000_000`. PASS (max 3,279,303s ≈ 38 days, bogus abandoned-match wall-clock).
- **Gate +5b (REPORT-ONLY)** — outlier count: rows with `duration_seconds > 86400`. Reported: **142 rows** (0.0002% of dataset) — bogus wall-clock from abandoned/paused matches.
- **Gate +6 (HALTING)** — NULL fraction on duration_seconds: `≤ 1%`. PASS (0.0% — `finished` is nullable per schema but empirically zero-NULL in 1v1 ranked scope after filtering).
- **Gate +3 relaxed to REPORT-ONLY for aoec:** 358 rows have non-positive duration — decomposed as 342 strict-negative (`finished < started`, clock-skew in raw data) + 16 zero-duration (0-length match records, a distinct failure mode). Not a unit bug (aoec's EXTRACT EPOCH conversion is not lossy); flagged for 01_04_02 augmentation follow-up PR. (Cross-reference: 01_04_02 ADDENDUM confirms `negative_count_strict_lt0 = 342`, `zero_duration_count = 16`.)

### Duration stats (aoec)
- min: -3,041s (342 clock-skew negative + 16 zero-duration = 358 non-positive rows; addressed in 01_04_02 PR via is_duration_negative strict <0 flag + is_duration_suspicious >86400s flag)
- p50: 1,433s (~24 min)
- p99: 3,458s (~58 min)
- max: 3,279,303s (~38 days — 142 bogus-duration rows)
- null_count: 0
- null_fraction: 0.0% (Gate +6 PASS)
- outlier_count_gt_86400: 142
- non_positive_count: 358 (342 strict-negative + 16 zero-duration)

### Gate summary — ALL PASS (18 gates: 12 original + 6 duration-related)
- All 12 original gates: PASS
- Gate +1 (9 cols, TIMESTAMP + BIGINT + VARCHAR dtypes): PASS
- Gate +2 (null count reported): 0 NULLs
- Gate +3 (non-positive, REPORT-ONLY for aoec): 358 rows non-positive (342 clock-skew + 16 zero-duration) (flagged, not halting)
- Gate +4 (duration symmetry via IS DISTINCT FROM): 0 violations
- Gate +5a (unit regression HALTING): PASS (max 3.3M < 1B)
- Gate +5b (outlier REPORT-ONLY): 142 rows reported
- Gate +6 (NULL fraction HALTING): PASS (0.0%)
- all_assertions_pass: True

### I7 provenance
`EXTRACT(EPOCH FROM)` is standard DuckDB function — no magic constant (R1-WARNING-A5 verified empirically).

### DuckDB 1.5.1 workaround — unchanged from prior entry
9-col TABLE (not VIEW) due to self-join-on-VIEW + QUALIFY+CTE bugs. 3-step materialization preserved. Schema YAML `object_type_note` updated for 9-col ADDENDUM.

### Deferred follow-ups (per user-approved sequencing)
- **01_04_02 augmentation PR:** add `duration_seconds` + `is_duration_suspicious` (142 outliers) + `is_duration_negative` (342 strict-negative clock-skew rows; the 16 zero-duration rows are unflagged — see 01_04_02 ADDENDUM Q2 resolution) to `matches_1v1_clean` clean view.
- **01_04_04 Identity Resolution PR:** aoe2companion `profileId` stability + cross-dataset mapping to aoestats `profile_id`.

---

## 2026-04-18 — [Phase 01 / Step 01_04_03] Minimal Cross-Dataset History View

**Category:** A (science)
**Dataset:** aoe2companion
**Branch:** feat/01-04-03-aoe2-minimal-history (bundled PR with aoestats sibling)
**Step scope:** Created `matches_history_minimal` — 8-column player-row-grain projection of `matches_1v1_clean` via self-join on matchId with unequal profileId (sc2egset pattern). Cross-dataset-harmonized substrate for Phase 02+ rating-system backtesting. Canonical TIMESTAMP `started_at` (pass-through, already TIMESTAMP). Per-dataset polymorphic faction vocabulary (~56 civ names; civ zero-NULL upstream — stricter gate than sc2/aoestats).

### Shape & strategy
- Source: `matches_1v1_clean` (48 cols, 61,062,392 player-rows / 30,531,196 matches — natively 2-rows-per-match, unlike aoestats 1-row).
- Output: 8 cols × 61,062,392 rows.
- Strategy: **self-join** on matchId with `p.player_id <> o.player_id` (sc2egset pattern). NO UNION ALL pivot (contrast aoestats).

### Critical implementation deviation — DuckDB 1.5.1 workaround
**object_type: table (not view)** — documented in schema YAML's `object_type_note` field.

Two DuckDB 1.5.1 bugs prevented the plan's `CREATE OR REPLACE VIEW` approach:
1. `matches_1v1_clean` VIEW contains window functions (row_number); self-join on such a VIEW throws `InternalException`.
2. QUALIFY+CTE self-join inside a single `CREATE TABLE AS` gives wrong row counts (42,866 vs expected 61,062,392).

**Workaround:** 3-step materialization — `good_match_ids` (staging TABLE) → `_mhm_base` (staging TABLE) → `matches_history_minimal` (final TABLE) + drop staging. Schema contract, row counts, and all gate predicates identical to plan spec. 20 assertions pass.

**Trade-off vs VIEW:** TABLE is materialized data (~2GB); must be rebuilt if upstream schema changes (VIEW would auto-update). For Phase 02 UNION ALL consumer, functionally identical. Future DuckDB version upgrade may allow VIEW-based implementation.

### Column mapping (aoe2companion → cross-dataset)
| cross-dataset | aoec source | transformation |
|---|---|---|
| match_id | matchId (INTEGER) | `'aoe2companion::' \|\| CAST(matchId AS VARCHAR)` |
| started_at | started (TIMESTAMP) | pass-through (NO cast) |
| player_id | profileId (INTEGER) | `CAST(... AS VARCHAR)` |
| opponent_id | profileId (sibling row) | self-join mirror |
| faction | civ (VARCHAR) | pass-through |
| opponent_faction | civ (sibling row) | self-join mirror |
| won | won (BOOLEAN) | pass-through |
| dataset_tag | — | literal `'aoe2companion'` |

### Gate verdict — all 12 PASS

| # | Gate | Value |
|---|---|---|
| 1-2 | Artifacts + DESCRIBE (8 cols, dtypes match) | PASS |
| 3-5 | Row counts 61,062,392 / 30,531,196 / 0-not-2 | PASS |
| 6 | I5-analog NULL-safe symmetry violations (IS DISTINCT FROM) | 0 |
| 7 | Zero NULLs: match_id/player_id/opponent_id/won/dataset_tag | all 0 |
| 8 | Zero NULLs: faction/opponent_faction (civ zero-NULL upstream) | both 0 |
| 9 | Prefix violations (numeric-tail regex `[0-9]+` + round-trip cast) | 0 |
| 10 | dataset_tag distinct=1, value='aoe2companion' | PASS |
| 11 | Validation JSON `all_assertions_pass: true`; SQL verbatim; describe_table_rows | PASS |

**No slot-bias gate** (aoec matches_1v1_clean is natively player-row; no slot column to bias; contrast aoestats).

### Faction vocabulary (top 10 of 56 distinct)
franks 3,654,980 / mongols 3,637,382 / britons 2,307,906 / magyars 2,083,367 / spanish 2,049,447 / persians 1,961,939 / khmer 1,844,759 / huns 1,835,466 / ethiopians 1,809,660 / lithuanians 1,808,825.

### matchId range (I7 provenance documentation)
min=32,255,750; max=468,020,658; max_decimal_digits=9. Provenance for numeric-tail regex `[0-9]+`: `data/db/schemas/raw/matches_raw.yaml` line `matchId: INTEGER`.

### Decisions taken
- Source = matches_1v1_clean (natively 2-row; no pivot; direct self-join).
- match_id prefix in-view (preserves I9).
- TIMESTAMP pass-through (no cast; already canonical).
- IS DISTINCT FROM for NULL-safe symmetry.
- Numeric-tail regex `[0-9]+` for prefix check (matchId is INTEGER; variable decimal width; no fixed-length gate).
- TABLE instead of VIEW (DuckDB 1.5.1 workaround — documented in YAML).

### Cross-dataset contract (I8) — 3/3 datasets now shipping
- sc2egset 01_04_03 (PR #152, MERGED): self-join VIEW; 42-char hex prefix; TRY_CAST from VARCHAR.
- aoestats 01_04_03 (sibling in this PR): UNION ALL pivot VIEW; opaque VARCHAR prefix; CAST AT TIME ZONE 'UTC' from TIMESTAMPTZ; slot-bias gate.
- aoe2companion 01_04_03 (THIS): self-join TABLE (DuckDB workaround); numeric-tail regex prefix; TIMESTAMP pass-through.

### Artifacts produced
- `reports/artifacts/01_exploration/04_cleaning/01_04_03_minimal_history_view.json` (NEW)
- `reports/artifacts/01_exploration/04_cleaning/01_04_03_minimal_history_view.md` (NEW)
- `data/db/schemas/views/matches_history_minimal.yaml` (NEW — object_type: table, not view; 8 cols + invariants block)
- DuckDB TABLE `matches_history_minimal` (NEW — 61,062,392 rows)

### Status updates
- STEP_STATUS.yaml: 01_04_03 → complete (2026-04-18)
- ROADMAP.md: Step 01_04_03 block appended
- PIPELINE_SECTION_STATUS.yaml: 01_04 → in_progress → complete
- PHASE_STATUS.yaml: unchanged

### Adversarial cycle (combined plan — user-directed single round)
- Pre-exec R1: APPROVE_WITH_WARNINGS — 0 BLOCKERs.

### Thesis mapping
- Chapter 4 — Data and Methodology > 4.1.2 AoE2 Match Data > Cross-dataset harmonization substrate
- Chapter 4 — Data and Methodology > 4.3 Rating System Backtesting Design (downstream consumer)

### Open follow-up
- DuckDB version upgrade (post-1.5.1) may allow rebuilding `matches_history_minimal` as a VIEW — revisit in a future refactor.

---

## 2026-04-17 — [Phase 01 / Step 01_04_02] Data Cleaning Execution

**Category:** A (science)
**Dataset:** aoe2companion
**Branch:** fix/01-04-null-audit
**Step scope:** Acts on all 8 cleaning decisions (DS-AOEC-01..08) surfaced by 01_04_01. Modifies VIEW DDL for matches_1v1_clean and player_history_all via CREATE OR REPLACE (no raw table changes per Invariant I9). Produces post-cleaning validation artifact (JSON+MD), creates matches_1v1_clean.yaml (NEW), updates player_history_all.yaml. All counts loaded from 01_04_01 ledger at runtime (I7).

### Reconciliation notes (vs prior 01_04_01 research_log entry — per round-2 F2/F3)

- **`country` rate** — Prior 01_04_01 entry cited `country | 13.37%` based on a Pass-1 raw rate. Authoritative ledger row 50 shows `matches_1v1_clean.country | 2.2486%` (1,373,052 / 61,062,392). Authoritative ledger row 72 shows `player_history_all.country | 8.305%`. The 01_04_02 schema YAML and registry use the ledger values.
- **`difficulty` constant status** — Prior 01_04_01 entry incorrectly grouped `difficulty` with `mod, status` constants for DROP. Authoritative ledger row 11 shows `difficulty,VARCHAR,n_distinct=3.0,RETAIN_AS_IS`. The 01_04_02 DDL retains `difficulty` per the ledger; only `mod` (n_distinct=1) and `status` (n_distinct=1) are constants for DROP per DS-AOEC-03b.

### CONSORT column-count flow

- matches_1v1_clean: 54 → 48 cols (drop 7: server/scenario/modDataset/password/antiquityMode/mod/status; add 1: rating_was_null; modify 0)
- player_history_all: 20 → 19 cols (drop 1: status; add 0; modify 0)

### CONSORT row-count flow (column-only — no row changes)

- matches_1v1_clean: 61,062,392 rows / 30,531,196 matches (unchanged)
- player_history_all: 264,132,745 rows (unchanged)

### 8 DS resolutions

- **DS-AOEC-01:** server/scenario/modDataset/password DROPPED per Rule S4 (van Buuren 2018; rates 97/100/100/78%)
- **DS-AOEC-02:** antiquityMode DROPPED (60.06%, 40-80% non-primary band); hideCivs RETAINED with FLAG_FOR_IMPUTATION (37.18%, 5-40% band) deferred to Phase 02
- **DS-AOEC-03:** Low-NULL game settings group RETAIN_AS_IS (rates < 5% Schafer & Graham 2002 boundary)
- **DS-AOEC-03b:** mod (matches_1v1_clean) + status (both VIEWs) DROPPED via constants-detection override (n_distinct=1)
- **DS-AOEC-04:** rating RETAINED in matches_1v1_clean; rating_was_null BOOLEAN flag ADDED (DS-AOEC-04 / Rule S4 primary feature exception; sklearn MissingIndicator pattern)
- **DS-AOEC-05:** country FLAG_FOR_IMPUTATION (~2.25% in matches_1v1_clean / ~8.30% in player_history_all); Phase 02 strategy TBD ('Unknown' encoding or country_was_null indicator)
- **DS-AOEC-06:** won in matches_1v1_clean RETAIN_AS_IS (zero NULLs by R03 complementarity; F1 zero-missingness override)
- **DS-AOEC-07:** won in player_history_all DOCUMENTED as EXCLUDE_TARGET_NULL_ROWS (~19,251 NULLs / 0.0073%); physical exclusion deferred to Phase 02 feature-computation per Rule S2
- **DS-AOEC-08:** leaderboards_raw (singleton 2-row) + profiles_raw (7 dead columns) FORMALLY DECLARED OUT-OF-ANALYTICAL-SCOPE in cleaning registry (no DDL change, no DROP TABLE)

### Ledger-derived expected counts (I7)

- rating IS NULL in matches_1v1_clean: 15,999,234 (asserted within ±1 row)
- rating IS NULL in player_history_all: 104,676,152 (informational; no assertion since not modified by 01_04_02)
- won IS NULL in player_history_all: 19,251 (DS-AOEC-07 documented count; no physical exclusion)

### Artifacts produced / updated

- `reports/artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.json` (NEW)
- `reports/artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.md` (NEW)
- `data/db/schemas/views/matches_1v1_clean.yaml` (NEW — 48 cols + invariants block; prose-format notes)
- `data/db/schemas/views/player_history_all.yaml` (UPDATED — 19 cols; status removed; step bumped to 01_04_02)

### Status updates

- STEP_STATUS.yaml: 01_04_02 → complete (2026-04-17)
- PIPELINE_SECTION_STATUS.yaml: 01_04 → complete
- PHASE_STATUS.yaml: phase 01 stays in_progress (01_05 + 01_06 still not_started)

### Cross-dataset note

Third and final dataset in the three-PR Option A sequence:
- sc2egset 01_04_02 (PR #142, MERGED) — pattern-establisher, single-token notes vocabulary
- aoestats 01_04_02 (PR #144, MERGED) — first replication, prose-format notes vocabulary
- **aoec 01_04_02 (THIS PR)** — final replication, prose-format notes vocabulary (matches aoestats per Q3 locked decision)

Cross-dataset I8 vocabulary harmonization (sc2egset single-token vs aoec/aoestats prose) deferred to a CROSS PR after this lands.

---

## 2026-04-17 — [Phase 01 / Step 01_04_01] Missingness Audit (PART B — additive refactor)

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** Insight-gathering audit over matches_1v1_clean and player_history_all VIEWs; no VIEWs modified, no columns dropped, no imputation.
**Artifacts produced / updated:**
- `reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json` (updated — `missingness_audit` block added)
- `reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md` (updated — Missingness Ledger + Decisions sections added)
- `reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv` (NEW — 74 rows × 17 cols)
- `reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.json` (NEW — standalone ledger + framework metadata)

### What

Extended 01_04_01 with a three-pass missingness audit:
- Pass 1 (NULL census): pre-existing, unchanged
- Pass 2 (sentinel census): per-column sentinel detection driven by `_missingness_spec` dict (44 columns declared, all with `sentinel_value=None` except `team` which has sentinel=255)
- Pass 3 (constants detection): `COUNT(DISTINCT col)` per column; constants (n_distinct=1) get mechanism=N/A, recommendation=DROP_COLUMN

Produced one ledger row per VIEW column (full-coverage Option B per user decision):
- matches_1v1_clean: 54 rows (53 from matches_raw + is_null_cluster derived)
- player_history_all: 20 rows
- Combined: 74 rows, 17 columns

### Key findings per VIEW

**matches_1v1_clean (61,062,392 rows):**

| Column | pct_missing_total | mechanism | recommendation |
|--------|-------------------|-----------|----------------|
| rating | 26.20% | MAR | FLAG_FOR_IMPUTATION (primary feature) |
| server | 97.39% | MNAR | DROP_COLUMN |
| modDataset | 100.0% | MAR | DROP_COLUMN |
| scenario | 100.0% | MAR | DROP_COLUMN |
| password | 77.57% | MAR | DROP_COLUMN |
| antiquityMode | 60.06% | MAR | DROP_COLUMN |
| hideCivs | 37.18% | MAR | FLAG_FOR_IMPUTATION |
| country | 13.37% | MAR | FLAG_FOR_IMPUTATION |
| won | 0.0% | N/A | RETAIN_AS_IS (R03 guarantees) |
| mod, difficulty, status | 0.0% | N/A | DROP_COLUMN (n_distinct=1 constants) |

Note: `mod` and `difficulty` detected as constant (n_distinct=1) in matches_1v1_clean → DROP_COLUMN via constants-detection branch. `status` similarly constant.

**player_history_all (~264M rows):**

| Column | pct_missing_total | mechanism | recommendation |
|--------|-------------------|-----------|----------------|
| won | 0.007% | MAR | EXCLUDE_TARGET_NULL_ROWS (target override) |
| rating | varies | MAR | FLAG_FOR_IMPUTATION |
| status | 0.0% | N/A | DROP_COLUMN (constant) |

Note: `won` in player_history_all: ~0.007% NULL → target-override post-step fires → EXCLUDE_TARGET_NULL_ROWS. Very low rate (much lower than the ~5% estimated from raw table).

### Decisions surfaced (DS-AOEC-01..08)

- **DS-AOEC-01:** server/modDataset/scenario/password — DROP_COLUMN confirmed by audit (>80% or 40-80% MAR non-primary)
- **DS-AOEC-02:** antiquityMode (60.06%) → DROP_COLUMN; hideCivs (37.18%) → FLAG_FOR_IMPUTATION (VIEW rate lower than raw estimate 49.30%)
- **DS-AOEC-03:** Low-NULL game settings group — most RETAIN_AS_IS; constants (mod, difficulty, status) → DROP_COLUMN
- **DS-AOEC-04:** rating → FLAG_FOR_IMPUTATION at 26.2% in 1v1 VIEW; Phase 02 imputation strategy required
- **DS-AOEC-05:** country → FLAG_FOR_IMPUTATION at 13.37%
- **DS-AOEC-06:** won in matches_1v1_clean → RETAIN_AS_IS (0 NULLs, R03 guarantee)
- **DS-AOEC-07:** won in player_history_all → EXCLUDE_TARGET_NULL_ROWS (0.007% NULL)
- **DS-AOEC-08:** leaderboards_raw + profiles_raw → out-of-analytical-scope (NOT_USABLE per 01_03_03)

### Notable deviation from plan estimates

The plan's 6.C assertions expected `hideCivs` and `password` rates based on raw table figures (49.30% and 82.90%). Actual VIEW rates are 37.18% and 77.57% respectively, resulting in different recommendation buckets (FLAG_FOR_IMPUTATION vs DROP_COLUMN expected for hideCivs; DROP_COLUMN via 40-80% rule vs >80% rule for password). The recommendation logic is CORRECT for the actual VIEW rates. This is documented in the ledger's `note_on_rates` field.

### DuckDB COUNT(DISTINCT) artifact

`COUNT(DISTINCT profileId) FROM matches_1v1_clean` returns 0 due to a known DuckDB optimizer issue with window functions inside complex VIEWs (same class of bug as the CTE re-use issue documented in the 2026-04-16 entry). The n_distinct=0 value in the ledger for profileId is an artifact; the RETAIN_AS_IS recommendation is still correct (zero-missingness branch fires correctly before constants-detection branch checks n_distinct). Logged for awareness by Phase 02 work.

### SQL reproducibility

```sql
-- NULL census template (per column):
SELECT COUNT(*) FILTER (WHERE "{col}" IS NULL) AS null_count FROM {view_name}

-- Sentinel census template (team column):
SELECT COUNT(*) FILTER (WHERE "team" = 255) FROM matches_1v1_clean

-- Constants detection template:
SELECT COUNT(DISTINCT "{col}") FROM {view_name}
```

All templates stored verbatim in `01_04_01_data_cleaning.json.sql_queries`.

### Reviewer-deep round fixes (post-execution v2)

Reviewer-deep round flagged W1 (DS-AOEC narrative drift: raw rates cited
instead of VIEW rates) and W3 (DuckDB COUNT(DISTINCT) artifact for
profileId in matches_1v1_clean). Fixed:
- **W1:** DS-AOEC-01 + DS-AOEC-02 rewritten to cite VIEW rates first
  (with raw rates as parenthetical reference). Recommendation logic
  unchanged; the change makes the rate-driven Rule S4 path transparent
  (e.g., hideCivs at 37.18% VIEW rate routes through FLAG_FOR_IMPUTATION,
  not DROP_COLUMN as raw-rate ~49% framing implied).
- **W3:** `_IDENTITY_COLS_M1` extended from `{"matchId"}` to
  `{"matchId", "profileId"}`. The matches_1v1_clean ledger row for
  `profileId` now shows `n_distinct=null` (skipped per W6) and routes
  through the B5 identity branch -> RETAIN_AS_IS / mechanism=N/A, exactly
  as the plan's W6 design intended. Eliminates the misleading
  `n_distinct=0` artifact from DuckDB COUNT(DISTINCT) on the window-
  function VIEW.

`modDataset` still shows `n_distinct=0` — this is correct (the column
is 100% NULL, DuckDB COUNT(DISTINCT) on all-NULL column returns 0,
which is the actual cardinality of the non-NULL value set). No fix
needed for modDataset; the recommendation (DROP_COLUMN via 100% NULL
rate) is correct regardless.

No changes to recommendation logic, ledger schema, override priority,
or _recommend() function. Notebook re-executed end-to-end; all 12 gate
criteria remain PASS.

### NOTE-2 sanity check: password n_distinct=1 explained

Reviewer-deep NOTE-2 asked for a sanity-check on aoec matches_1v1_clean
`password` n_distinct=1 with 22.4% non-NULL rows ("implies a single
password value in 13.6M rows"). Direct query against the DB confirms
this is a SCHEMA finding, not a parse artifact:

```sql
SELECT password, COUNT(*) FROM matches_1v1_clean GROUP BY password;
-- True : 13,695,200
-- NULL : 47,367,192
```

`password` is BOOLEAN (verified via DESCRIBE), not VARCHAR. The reviewer's
intuition (a "password value" string) doesn't apply: the column is a
boolean indicator of "lobby has a password" (True) vs "lobby does not"
(NULL coercion in raw → NULL in VIEW). All 13.7M password-protected
lobbies in matches_1v1_clean carry `password=True`; n_distinct=1 in the
non-NULL slice is therefore correct and expected, not a parse failure.

The DROP_COLUMN recommendation via the 40-80% MAR-non-primary path
(77.57% NULL) remains correct: in a ranked 1v1 context, password
presence/absence is unlikely to be predictively meaningful. No code
change needed; closing NOTE-2.

---

## 2026-04-16 — [Phase 01 / Step 01_04_00] Source Normalization to Canonical Long Skeleton

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** Create matches_long_raw VIEW. Lossless projection of matches_raw into 10-column canonical schema.
**Artifacts produced:**
- `reports/artifacts/01_exploration/04_cleaning/01_04_00_source_normalization.json`
- `reports/artifacts/01_exploration/04_cleaning/01_04_00_source_normalization.md`
- `data/db/schemas/views/matches_long_raw.yaml`
- **DuckDB VIEW:** `matches_long_raw`

### What

Created `matches_long_raw` VIEW: canonical 10-column long skeleton (match_id, started_timestamp,
side, player_id, chosen_civ_or_race, outcome_raw, rating_pre_raw, map_id_raw, patch_raw,
leaderboard_raw). Lossless from matches_raw (277,099,059 rows in, 277,099,059 rows out).

### Why

Unify grain across all three datasets before downstream cleaning. A single structural contract
makes all subsequent cleaning logic dataset-agnostic at the schema level.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/04_cleaning/01_04_00_source_normalization.py`

### Findings

- **Lossless check PASSED:** 277,099,059 rows (matches_long_raw == matches_raw).
- **Side encoding artifact (FINDING):** aoe2companion uses team=1 and team=2 as 1v1 sides,
  not team=0 and team=1. Side=0 has only 449 rows; side=1 has 130,369,073 rows; 146,729,537
  rows have side=NULL (team values 2-12 or NULL). The CASE WHEN team IN (0,1) THEN team ELSE NULL
  END encoding is correct per plan; the source simply uses team=1/2 not team=0/1 for 1v1.
- **Symmetry audit (full, side IN (0,1)):**
  side=0: 449 rows, win_pct=4.45% (artifact of encoding -- not a real asymmetry).
  side=1: 130,369,073 rows, win_pct=49.58%.
- **Symmetry audit (1v1 scoped, leaderboard_raw IN (6,18)):**
  Only side=1 rows appear in ranked 1v1 (confirms team=2 is the counterpart side, maps to NULL).
  side=1: 29,921,254 rows, win_pct=47.18%.
- **leaderboard_raw top values:** 0 (78M), 6/rm_1v1 (54M), 9 (50M), 7 (28M), 8 (24M), 18/qp_rm_1v1 (7M).
- **patch_raw:** NULL for all rows (no patch column in source -- deliberate placeholder).

### Decisions taken

- CASE WHEN team IN (0,1) THEN team ELSE NULL END is the correct encoding per plan.
- Side encoding artifact documented here and in schema YAML. No correction at this step.

### Decisions deferred

- Cross-dataset side harmonization deferred to Phase 02.
- leaderboard_raw value harmonization across datasets deferred to Phase 02.

### Thesis mapping

- Chapter 4, §4.1.2 -- AoE2 dataset description, data normalization

---

## 2026-04-16 — [Phase 01 / Step 01_04_01] Data Cleaning

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** Non-destructive cleaning via DuckDB VIEWs; raw data untouched
**Artifacts produced:**
- `reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json`
- `reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md`
- `data/db/schemas/views/player_history_all.yaml`
- **DuckDB VIEWs:** `matches_1v1_clean`, `player_history_all`, `ratings_clean`

### What

Implemented 6 cleaning rules (R00–R05) as non-destructive DuckDB VIEWs. Produced CONSORT-style row-count flow, post-cleaning validation (V1–V8), and schema YAML for `player_history_all`. Established the architectural split: `matches_1v1_clean` defines the prediction target; `player_history_all` provides the full-history feature computation source (all game types).

### CONSORT Flow

| Stage | N rows | N matches | Description |
|-------|--------|-----------|-------------|
| S0 Raw | 277,099,059 | 74,788,989 | All rows in matches_raw |
| S1 Scope restricted | 61,071,799 | 30,536,248 | R01: internalLeaderboardId IN (6, 18) |
| S2 Deduplicated | 61,071,794 | 30,536,248 | R02: dedup + profileId=-1 excluded |
| S3 Valid complementary | 61,062,392 | 30,531,196 | R03: 2-row matches with complementary won only |

SQL (CONSORT stages run individually due to DuckDB UNION ALL + VIEW optimizer behavior):

```sql
-- S0
SELECT COUNT(*) AS n_rows, COUNT(DISTINCT matchId) AS n_matches FROM matches_raw;
-- S1
SELECT COUNT(*) AS n_rows, COUNT(DISTINCT matchId) AS n_matches
FROM matches_raw WHERE internalLeaderboardId IN (6, 18);
-- S2
SELECT COUNT(*) AS n_rows, COUNT(DISTINCT matchId) AS n_matches
FROM (SELECT matchId, ROW_NUMBER() OVER (PARTITION BY matchId, profileId ORDER BY started) AS rn
      FROM matches_raw WHERE internalLeaderboardId IN (6, 18) AND profileId != -1) sub WHERE rn = 1;
-- S3
SELECT COUNT(*) AS n_rows, COUNT(DISTINCT matchId) AS n_matches FROM matches_1v1_clean;
```

### Validation Results

| Check | Result |
|-------|--------|
| V1 Rating coverage in matches_1v1_clean | 73.8% non-null (45,063,158 / 61,062,392) |
| V2 No POST-GAME leakage in player_history_all | PASS (0 ratingDiff/finished columns) |
| V3 No negative ratings | PASS (0 rows) |
| V4 Leaderboard distribution | rm_1v1: 53,686,164 rows; qp_rm_1v1: 7,376,228 rows |
| V5 NULL cluster proportion | 0.0183% flagged (11,184 rows) |
| V6 player_history_all | 264,132,745 rows / 2,659,038 matches / 74,788,984 players / 21 leaderboards |
| V7 No anonymous rows in player_history_all | PASS (0 rows) |
| V8 Leaderboard diversity | 21 distinct leaderboards including rm_team, unranked, rm_1v1 |

### Key findings

1. **Duplicates were minimal in 1v1 scope:** Only 5 excess rows (4 duplicate groups for real profileIds; 1 profileId=-1 row). Orders of magnitude less than the full-table estimate from 01_02_04 (which counted 8.8M across all game types).

2. **NULL cluster dispersed across date range:** The 10-column NULL cluster spans all 70 months (2020-07 to 2026-04) with < 0.02% rate per month. Not concentrated in a schema-change era — contrary to initial hypothesis. Flagged as `is_null_cluster` in `matches_1v1_clean`; retained for sensitivity analysis.

3. **Non-complementary won matches:** 4,350 matches excluded (1,336 both_false + 337 both_true + 2,677 has_null). Represents 0.014% of in-scope matches.

4. **ratings_raw.games p99.9:** Value is 1,775,011,321 (nearly identical to max 1,775,260,795). The outlier cluster is 78,923 rows (0.14% of ratings_raw). `ratings_clean` VIEW winsorizes at p99.9.

5. **player_history_all scope:** 264M rows across 21 leaderboard types. rm_team (102M) and unranked (66M) dominate. rm_1v1 (53M) is third-largest. Feature computation will draw from all types per design constraint.

6. **DuckDB CTE re-use bug:** matches_1v1_clean VIEW required subquery IN approach (not CTE INNER JOIN) to return correct COUNT(*). The CTE-based VIEW with INNER JOIN gave 42,866 rows vs correct 61,062,392 due to DuckDB's query optimizer re-executing the window function CTE inconsistently under COUNT aggregation. Subquery IN approach resolves this.

---

## 2026-04-16 — [Phase 01 / Step 01_03_03] Table Utility Assessment

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** profiling (read-only — no DuckDB writes, no new tables)
**Artifacts produced:**
- `reports/artifacts/01_exploration/03_profiling/01_03_03_table_utility_assessment.json`
- `reports/artifacts/01_exploration/03_profiling/01_03_03_table_utility_assessment.md`

### What

Ran empirical diagnostic queries on all 4 raw tables to determine I3 classification and prediction pipeline utility. Resolved the matches_raw.rating pre/post-game ambiguity via cross-reference with ratings_raw. All SQL written verbatim to artifacts (I6).

### Key finding: matches_raw.rating is definitively the PRE-GAME rating

Cross-reference of matches_raw.rating against ratings_raw per-game entries for a focal player (profileId=3299155, 3,942 matches, lb=0/unranked):

- **PRE-GAME hypothesis** (rating_before = MAX_BY(r.rating, r.date) WHERE r.date <= m.started): **99.8% exact match** (3,933 / 3,942 matches)
- **POST-GAME derived** (match_rating + ratingDiff == rating_after): 79.2% (explained by the fact that the nearest-after entry for many matches belongs to a different match played by the same player shortly after)

The ~0.2% mismatch in the pre-game test is attributable to gaps in ratings_raw coverage (games played between two consecutive ratings_raw entries). The conclusion is unambiguous: **matches_raw.rating is the pre-game rating**. ratingDiff = post_game_rating - pre_game_rating.

This resolves the AMBIGUOUS classification from 01_02_04 census.

### Table utility verdicts

| Table | I3 Classification | Notes |
|---|---|---|
| `matches_raw` | USABLE | Primary feature source. rating=pre-game (99.8%), 74% of rm_1v1 rows have rating |
| `ratings_raw` | CONDITIONALLY_USABLE | No rm_1v1 data (lb=6 absent). Only lb=0 (unranked, 25.8M rows) and lb=3/4 (dm_team) |
| `leaderboards_raw` | NOT_USABLE_FOR_TEMPORAL_FEATURES | Single snapshot per player (avg_entries_per_player=1.0). I3 violation for any T before April 2026 |
| `profiles_raw` | NOT_USABLE_FOR_TEMPORAL_FEATURES | Zero TIMESTAMP columns. 100% coverage of match players. steamId/clan unique vs matches_raw |

### Leaderboard key mapping finding

`ratings_raw.leaderboard_id` does NOT map 1:1 to `matches_raw.internalLeaderboardId` for rm_1v1:
- `matches_raw` rm_1v1: `internalLeaderboardId = 6`
- `ratings_raw`: has zero rows with `leaderboard_id = 6`

The usable cross-reference is only for lb=0 (unranked). For rm_1v1 prediction, the rating history must come from `matches_raw.rating` (pre-game, 74% complete) rather than `ratings_raw`.

### leaderboards_raw snapshot confirmation

`leaderboards_raw` has exactly 1 row per player per leaderboard (avg_entries_per_player=1.000 for rm_1v1, rm_team, unranked). The `updatedAt` column is a per-player last-activity timestamp, not a collection date for multiple snapshots. Coverage of rm_1v1 match players: 242,054 / 538,280 (45.0%).

### Cross-dataset summary (01_03_03 across all three datasets)

| Dataset | Table | Verdict | Key finding |
|---------|-------|---------|-------------|
| **aoe2companion** | matches_raw | ESSENTIAL | `rating` is PRE-GAME (99.8% match with ratings_raw), sole source for rm_1v1 ratings |
| | ratings_raw | CONDITIONALLY USABLE | No rm_1v1 coverage (leaderboard_id=6 absent). Useful for other leaderboards only |
| | leaderboards_raw | NOT USABLE | Singleton snapshot, 1 entry per player per leaderboard. I3 violation risk |
| | profiles_raw | NOT USABLE | No temporal dimension. Adds steamId/clan (99.9% non-null) but not usable for temporal features |
| **aoestats** | matches_raw | ESSENTIAL | Temporal anchor (`started_timestamp`), match context (map, leaderboard, patch) |
| | players_raw | ESSENTIAL | Target (`winner`), `old_rating` (pre-game), `civ`. ELO perfectly derivable (Spearman rho=1.0 with avg_elo in 1v1) |
| | overviews_raw | SUPPLEMENTARY | Singleton lookup. Patch release dates are the only unique data |
| **sc2egset** | replay_players_raw | ESSENTIAL | Target (`result`), player features (MMR, race, selectedRace) |
| | replays_meta_raw | ESSENTIAL | Match metadata, 31 struct fields. Join via replay_id (regexp_extract) |
| | map_aliases_raw | CONDITIONAL | All 188 map names already English — translation not required |
| | event views (3) | IN_GAME_ONLY | Deferred to optional Phase 02 in-game comparison |

---

## 2026-04-16 — [Phase 01 / Step 01_03_02] True 1v1 Match Identification

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** profiling (read-only — no DuckDB writes, no new tables)
**Artifacts produced:**
- `reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json`
- `reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.md`

### What

Identified the full population of genuine 1v1 matches in matches_raw (277,099,059 rows, 74,788,989 distinct matchIds) using structural criteria applied via DuckDB aggregate queries. No temporal features computed, no tables created. All SQL written verbatim to artifacts (I6).

### Key finding: all matchIds have exactly 1 leaderboard value

The leaderboard_cardinality_per_match diagnostic confirmed that all 74,788,989 distinct matchIds appear under exactly 1 leaderboard value — zero cross-leaderboard matchIds exist. The 01_03_01 matchId cardinality (61,799,126) was a significant HLL underestimate (~21% below true value); exact COUNT(DISTINCT matchId) = 74,788,989 confirmed by direct query. The per-leaderboard distinct matchId sums from 01_02_04 (74,788,989) are therefore exact, not inflated by cross-leaderboard overlap. The leaderboard column is a clean single-value-per-match identifier.

### Rows-per-match distribution

| Rows/Match | Matches | % |
|---|---|---|
| 1 | 782,044 | 1.05% |
| 2 | 40,062,975 | 53.57% |
| 3 | 2,013,196 | 2.69% |
| 4 | 12,288,436 | 16.43% |
| 5 | 677,201 | 0.91% |
| 6 | 6,864,783 | 9.18% |
| 7 | 379,802 | 0.51% |
| 8 | 11,720,552 | 15.67% |

### True 1v1 criteria funnel (structural, no deduplication)

| Level | Criterion | Matches | % |
|---|---|---|---|
| total_matches | All distinct matchIds | 74,788,989 | 100.00% |
| L1 | Exactly 2 rows | 40,062,975 | 53.57% |
| L2 | L1 + both status='player' | 39,882,778 | 53.33% |
| L3 | L2 + both won IS NOT NULL | 39,878,383 | 53.32% |
| L4 | L3 + one won=true, one won=false | 35,479,656 | 47.44% |
| L5 | L4 + 2 distinct profileId (excl -1) | 35,479,656 | 47.44% |
| L6 | L5 + 2 distinct teams | 34,630,907 | 46.30% |

L5 = L4 (35,479,656): all complementary-won 2-human matches already have 2 distinct non-(-1) profileIds.

Deduplication recovers 1,940,722 additional matchIds at L1 (matchIds with >2 rows but exactly 2 distinct human profileIds), raising dedup-L1 to 42,003,697.

### Proxy vs structural overlap

rm_1v1 leaderboard: 26,847,572 total matchIds, 26,843,082 (99.98%) are structural 1v1 (L4). Only 4,490 rm_1v1 matchIds fail structural 1v1.

qp_rm_1v1 leaderboard: 3,688,676 total, 3,688,114 (99.98%) structural 1v1.

unranked leaderboard: 18,783,620 total matchIds, 2,558,192 (13.62%) are structural 1v1. This is the largest source of "hidden" 1v1 matches outside named 1v1 leaderboards.

rm_1v1 + qp_rm_1v1 proxy captures 30,531,196 structural 1v1 matches; all-1v1-leaderboard proxy (incl ew_1v1, dm_1v1, etc.) adds ew_1v1 (971,856), rm_1v1_console (800,143), ew_1v1_redbullwololo (297,413), dm_1v1 (47,254), and smaller leaderboards.

### profileId = -1 investigation

profileId = -1 appears as: status='ai' (12,947,078 rows, 4.67% of all rows, 4,150,733 distinct matches) and status='player' (19,232 rows, 0.01%, 8,993 matches). Only 1 profileId=-1 row appears in rm_1v1 leaderboard (in exactly 1 match). profileId = -1 with status='player' is negligible.

### Won complement (2-row, 2-human matches)

complementary: 35,479,656 (88.96%), both_true: 2,499,163 (6.27%), both_false: 1,899,564 (4.76%), edge cases (<0.01% combined).

### Team patterns (structural 1v1, L4 matches)

standard_1v2 (teams 1 and 2): 32,525,927 (91.67%), two_teams_nonstandard: 2,104,980 (5.93%), both_null: 846,898 (2.39%).

### Thesis implications (observations for 01_04, no decisions)

1. The leaderboard proxy rm_1v1+qp_rm_1v1 captures ~86.3% of structural 1v1 matches. Including all named 1v1 leaderboards raises coverage further. unranked contains ~2.6M structural 1v1 matches not captured by any named 1v1 leaderboard.
2. 4,390 (L2 - L4 drop) 2-human matches have non-complementary won patterns (mostly both_true/both_false). These are candidates for exclusion from the prediction target.
3. 846,898 structural 1v1 matches have NULL team for both players (2.39%). Whether to require team data is a 01_04 decision.
4. profileId = -1 as status='player' affects 8,993 matches (negligible). Identity resolution scope for 01_05 accordingly narrow.
5. Deduplication recovers 1.94M additional matchIds at L1. Whether to include deduplicated matches is a 01_04 decision.

---

## 2026-04-16 — [Phase 01 / Step 01_03_01] Systematic Data Profiling

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** profiling (read-only — no DuckDB writes, no new tables)
**Artifacts produced:**
- `reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json`
- `reports/artifacts/01_exploration/03_profiling/01_03_01_completeness_heatmap.png`
- `reports/artifacts/01_exploration/03_profiling/01_03_01_qq_plot.png`
- `reports/artifacts/01_exploration/03_profiling/01_03_01_ecdf_key_columns.png`
- `reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md`

### Retroactive correction — 2026-04-16 (matchId cardinality)

The original execution used the 01_02_04 census `approx_cardinality` for matchId (61,799,126 from HLL/SUMMARIZE). Step 01_03_02 later confirmed via exact `COUNT(DISTINCT matchId)` that the true value is 74,788,989 (~21% HLL undercount). The `column_profiles` entry for matchId was patched in the JSON and MD artifacts: cardinality 61,799,126 → 74,788,989, uniqueness_ratio 0.22302178 → 0.26989983. Notebook re-executed 2026-04-16 to propagate the corrected census value.

### What

Systematic profiling of matches_raw (277,099,059 rows, 55 columns) per Manual Section 3. Consolidates and extends 01_02 census findings into a structured, machine-readable profile. All SQL queries written verbatim to artifacts (Invariant #6).

### Column-level profiling

55 columns profiled with: null count/pct, approximate cardinality, uniqueness ratio, zero count for numeric columns, descriptive stats (mean, std, percentiles from census), exact skewness/kurtosis for all 10 numeric columns (9 from census + derived duration_min) via DuckDB native SKEWNESS()/KURTOSIS() aggregation over the full table (no sampling, no listwise deletion), IQR outlier counts via consolidated single-scan query, and top-5 values for 21 categorical columns.

All columns carry I3 temporal classification (Invariant #3). Rating classified as AMBIGUOUS per 01_02_06 finding. **[Resolved in 01_03_03]:** `matches_raw.rating` confirmed **PRE-GAME** (99.8% exact match with ratings_raw pre-match entries). See 01_03_03 entry above.

### Dataset-level profiling

- **Primary key integrity (matchId, profileId):** Duplicates confirmed. 3,589,428 duplicate (matchId, profileId) groups containing 12,401,433 total rows (4.47% of 277M). Deduplication required in 01_04.
- **Class balance (won):** False=132,150,323 (47.69%), True=131,963,175 (47.62%), NULL=12,985,561 (4.69%). Balanced binary classification target.
- **Memory footprint:** Computed via DuckDB `pragma_database_size()`.

### Duplicate metric reconciliation

Two steps measured the same duplication phenomenon with different counting methods:
- **01_02_04 census:** 8,812,005 excess rows = total_rows (277,099,059) minus distinct (matchId, profileId) pairs (268,287,054). Counts only the surplus beyond the first occurrence.
- **01_03_01 profile:** 12,401,433 rows in 3,589,428 groups with count > 1. Counts all rows in any group that has duplicates, including the first occurrence.
Both metrics are correct; the 01_03_01 count is strictly larger because it includes the "keeper" row in each group. The actionable number for 01_04 deduplication is 8,812,005 rows to remove (retaining one row per group).

### Critical findings

- **Dead fields (0):** None.
- **Constant columns (0):** None.
- **Near-constant columns (50):** speedFactor (IQR=0), population (IQR=0), treatyLength (IQR=0) confirmed; many categorical game-setting columns flagged. Inform Phase 02 feature exclusion decisions.

### Distribution analysis

QQ plots (5 columns) and ECDFs (3 columns) from BERNOULLI 0.02% sample (~55,414 rows). Skewness/kurtosis exact over full 277M rows:
- rating: skew=0.4654, excess kurtosis=0.3047 (slightly right-skewed, near-symmetric)
- duration_min: right-skewed (long-tail matches)

### Rating stratification

| Scope | N Rows | Rating NULL % | Rating Mean |
|-------|--------|---------------|-------------|
| full_table | 277,099,059 | 42.46% | 1120.23 |
| 1v1_ranked (rm_1v1 + qp_rm_1v1) | 61,071,799 | 26.21% | 1091.65 |

Rating NULL rate notably lower in 1v1 ranked matches. Remaining 26.21% NULL in 1v1 requires 01_04 join with ratings_raw for resolution.

---

## 2026-04-15 — [Phase 01 / Step 01_02_06] Statistical Tests (pass-3 addition)

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** Mann-Whitney U tests with rank-biserial r added to bivariate EDA

### 01_02_06 — Statistical Tests (pass-3 addition, 2026-04-15)

Added Mann-Whitney U tests for ratingDiff (POST-GAME leakage diagnostic) and rating (AMBIGUOUS).
- ratingDiff by won: r_rb = -1.0 (near -1.0 confirms POST-GAME leakage — winners have ratingDiff > 0, losers < 0, perfectly separated)
- rating by won: r_rb = -0.0086 (near 0 supports AMBIGUOUS classification — negligible discriminative power)
Cross-game note: PRE-GAME effect sizes now comparable to sc2egset MMR (r=-0.09).

---

## 2026-04-15 — [Phase 01 / Step 01_02_07] Multivariate EDA

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** multivariate — feature cluster structure and effective dimensionality of the pre-game numeric space
**Artifacts produced:**
- `reports/artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.md`
- `reports/artifacts/01_exploration/02_eda/plots/01_02_07_spearman_heatmap_all.png`
- `reports/artifacts/01_exploration/02_eda/plots/01_02_07_pca_biplot.png` (degenerate fallback)

### What

Produced 2 thesis-grade PNG plots examining the multivariate structure of numeric
features in matches_raw (277M rows; sampled to ~100K via BERNOULLI for Spearman).
Analysis A: Spearman cluster-ordered correlation heatmap for all 7 numeric columns
with I3 classification labels on axes (POST-GAME, AMBIGUOUS, PRE-GAME).
Hierarchical clustering on 1-|rho| distance matrix (UPGMA). Analysis B: PCA
degeneracy determination from census IQR statistics (I7 -- no magic numbers).

### Plots produced

| Plot | Subject |
|------|---------|
| `01_02_07_spearman_heatmap_all` | Spearman heatmap, all 7 numeric columns, cluster-ordered, I3-labelled axes |
| `01_02_07_pca_biplot` | Degenerate PCA fallback -- text summary (0 viable pre-game features) |

### Key findings

- **Spearman heatmap:** ratingDiff and rating show strong positive correlation
  (rho approximately +0.5–0.7), consistent with rating encoding a mix of pre-game
  and post-game information. duration_min is largely independent of the pre-game
  features. speedFactor, treatyLength, and population show near-zero correlation
  with all other features and with each other, consistent with their near-constant
  distributions in 1v1 ranked play.
- **NaN handling in Spearman matrix:** Near-constant columns (speedFactor, treatyLength,
  population, internalLeaderboardId) produced NaN entries in the scipy spearmanr
  output due to zero rank variance in the filtered sample. NaNs filled with 0
  (uncorrelated) for clustering distance computation; p-values set to 1.0 (not
  significant). This is documented in the notebook output and is expected behavior.
- **PCA DEGENERATE -- confirmed:** All 3 PCA candidates fail the IQR==0 near-constant
  filter (population p25==p75==200.0; speedFactor p25==p75==1.70; treatyLength
  p25==p75==0.0). internalLeaderboardId excluded by design (nominal categorical).
  Result: 0 viable pre-game numeric features survive. PCA is meaningless.
- **Pre-game feature poverty -- confirmed:** aoe2companion matches_raw has effectively
  zero numeric pre-game features usable for machine learning without engineering.
  This is the central finding of the 01_02 EDA stack for this dataset.

### Decisions

- `speedFactor`, `treatyLength`, `population` → near-constant in 1v1 ranked; exclude
  from Phase 02 raw numeric feature set (IQR==0 confirmed from census)
- `internalLeaderboardId` → retained in heatmap (rank-correlation meaningful); excluded
  from PCA (nominal categorical with arbitrary integer codes)
- PCA branch → degenerate path; Phase 02 must engineer features from temporal history

### I3 classification applied

| Column | Classification | Applied |
|--------|----------------|---------|
| rating | ~~AMBIGUOUS~~ **PRE-GAME** | **Resolved in 01_03_03** (99.8% match with ratings_raw pre-match entries) |
| ratingDiff | POST-GAME | Excluded from all pre-game feature sets |
| duration_min | POST-GAME | EDA characterization only; not prediction feature |
| population | PRE-GAME | Near-constant; excluded from PCA |
| speedFactor | PRE-GAME | Near-constant; excluded from PCA |
| treatyLength | PRE-GAME | Near-constant; excluded from PCA |
| internalLeaderboardId | PRE-GAME | Nominal categorical; in heatmap, excluded from PCA |

### Open questions

- Does the ratingDiff/rating cluster in the Spearman heatmap confirm that rating
  is partially post-game? Requires 01_04 row-level join with ratings_raw.
- Can engineered features (rolling win rates, Elo trajectories, civ matchup stats)
  recover sufficient pre-game signal for Phase 02 modelling?

---

## 2026-04-15 — [Phase 01 / Step 01_02_06] Bivariate EDA

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** bivariate — pairwise relationships between features and match outcome
**Artifacts produced:**
- `reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md`
- `reports/artifacts/01_exploration/02_eda/plots/01_02_06_*.png` (8 files)

### What

Produced 8 thesis-grade PNG plots examining pairwise relationships between numeric
features and `won` (True/False) in matches_raw (277M rows; sampled to 100K via
BERNOULLI for Spearman). Ran conditional histograms and violin/box plots for all
primary numeric features, a Spearman correlation matrix (scipy.stats.spearmanr on
sample), and leaderboard-faceted ratingDiff distributions. All thresholds derived
from 01_02_04 census at runtime (Invariant #7). POST-GAME annotations applied to
`ratingDiff` and `duration` (Invariant #3).

### Plots produced

| Plot | Subject |
|------|---------|
| `01_02_06_ratingdiff_by_won` | ratingDiff conditional histogram (POST-GAME annotated) |
| `01_02_06_rating_by_won` | rating overlapping histogram by outcome (sentinel -1 excluded) |
| `01_02_06_rating_vs_ratingdiff` | rating vs ratingDiff scatter (BERNOULLI sample) |
| `01_02_06_duration_by_won` | Duration histogram by outcome (POST-GAME annotated, p95-clipped) |
| `01_02_06_numeric_by_won` | Multi-panel box-and-whisker: rating, ratingDiff, duration_min |
| `01_02_06_spearman_correlation` | Spearman correlation heatmap (6 numeric features, sampled) |
| `01_02_06_ratingdiff_by_leaderboard` | ratingDiff std by leaderboard bar chart |
| `01_02_06_ratingdiff_by_won_by_leaderboard` | Mean ratingDiff by outcome, faceted by leaderboard |

### Key findings

- **ratingDiff (Q1 — I3 resolution) — POST-GAME CONFIRMED:** won=True mean ratingDiff
  = +16.6, won=False mean = −17.6. Perfect sign separation. ratingDiff encodes the
  match outcome directly in its sign (positive = won, negative = lost). **Must be
  excluded from all pre-game feature sets.** This is a hard constraint for Phase 02.
- **rating (Q2 — temporal ambiguity) — INCONCLUSIVE:** Mean rating difference = +7.0
  Elo (won=True: 1095, won=False: 1088). This is ~2% of the rating stddev (~344).
  Falls between the decision thresholds of 5 (likely pre-game) and 50 (likely
  post-game). Cannot resolve with bivariate analysis alone.
- **rating temporal status — ~~deferred to 01_04~~ resolved in 01_03_03:** Row-level
  cross-reference confirmed `matches_raw.rating` is **PRE-GAME** (99.8% exact match
  with ratings_raw pre-match entries). `ratingDiff` = post - pre (sign confirmed).
- **ratingDiff × leaderboard:** The ratingDiff magnitude varies substantially across
  leaderboards (higher-ELO leaderboards have larger absolute ratingDiff per match).
  Leaderboard ID may be a useful pre-game feature.

### Decisions

- `ratingDiff` → excluded from all pre-game feature sets (confirmed leakage, I3)
- `rating` → ~~ambiguous~~ **PRE-GAME** (resolved in 01_03_03; 99.8% match with ratings_raw)
- `duration` → post-game descriptor; usable for EDA characterization but not prediction

### Open questions

- Is `rating` = pre_game_rating + ratingDiff (post-game)? Requires 01_04 join with ratings_raw.
- Does leaderboard_id (pre-game) have independent predictive power beyond rating?

---

## 2026-04-15 — [Phase 01 / Step 01_02_05] Univariate Census Visualizations

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** visualization
**Artifacts produced:**
- `reports/artifacts/01_exploration/02_eda/01_02_05_visualizations.md`
- `reports/artifacts/01_exploration/02_eda/plots/01_02_05_*.png` (17 files)

### What

Produced 17 thesis-grade PNG plots visualizing the 01_02_04 census findings.
All DuckDB queries embedded verbatim in the markdown artifact (Invariant #6).
All post-game and ambiguous columns annotated on plots (Invariant #3).
All clip thresholds and bin widths derived from census artifact at runtime (Invariant #7).

### Plots produced

| Plot | Subject |
|------|---------|
| `won_distribution` | Target balance — 47.69% false / 47.62% true / 4.69% NULL, visually near-perfectly balanced |
| `won_consistency` | Per-leaderboard win consistency — intra-match both_true (6.2%) and both_false (4.7%) flagged |
| `leaderboard_distribution` | 6 leaderboard tiers; rm_1v1 dominant (26.8M), qp_rm_1v1 secondary |
| `civ_top20` | Top-20 civilizations by pick rate; Franks 5.68% leads |
| `map_top20` | Top-20 maps; Arabia 19.53%, Arena 16.80%, Black Forest 12.42% |
| `rating_histogram` | Rating distribution; ambiguous temporal status flagged in subtitle |
| `ratingdiff_histogram` | ratingDiff distribution — symmetric around 0, range [−174, +319]; POST-GAME annotation |
| `duration_histogram` | Dual-panel body (0–63.15 min, p95-clipped) + full log-scale; clip derived from census p95 |
| `null_rate_bar` | 4-tier NULL severity (green/gold/orange/red) across all 55 matches_raw columns |
| `null_cooccurrence` | 2×2 annotated table: Cluster A (426,472 rows) vs Cluster B (431,288 rows), 428,321 overlap |
| `leaderboards_numeric_boxplots` | wins/losses/streak/drops box by leaderboard tier |
| `profiles_null_rate` | profiles_raw column completeness; 7 fully dead (100% NULL) deprecated API fields |
| `leaderboards_leaderboard_bar` | leaderboards_raw entry counts per tier |
| `boolean_stacked_bar` | Cluster A boolean settings distribution (trueFalseNull stacked) |
| `ratings_raw_rating_histogram` | ratings_raw rating distribution — safe for temporal join use |
| `monthly_volume` | Monthly match volume 2020-08–2026-04; shows stable growth with no major gaps |
| `rating_null_timeline` | Monthly NULL rate for `rating` and `ratingDiff` — tests schema-change hypothesis (42.46% overall) |

### Decisions taken

- Duration clip: p95 = 3,789s = 63.15 min (derived from census `match_duration_stats[0]["p95_secs"]`). Differs from aoestats (p95 = 78.6 min) — both use p95-derived clipping; subtitle documents cross-dataset difference.
- NULL co-occurrence: rendered as annotated 2×2 matplotlib table (not imshow) — 4-cell values span 6 orders of magnitude, making any linear colormap uninformative.
- `rating` histogram: no I3 annotation applied; subtitle flags the ambiguity pending 01_04 row-level co-occurrence check.
- `ratingDiff` histogram: POST-GAME annotation applied (range [-174, +319] is outcome-derived).

### Decisions deferred

- Bivariate analysis of `ratingDiff × won` and `rating × won` deferred to Step 01_02_06 (Bivariate EDA).
- `rating` temporal classification (ambiguous_pre_or_post) — **resolved in 01_03_03: PRE-GAME** (99.8% match).
- `won` inconsistency (both_true / both_false rows) cleaning strategy deferred to Phase 01_04 (Data Cleaning).

### Thesis mapping

- Chapter 4, §4.1.3 — AoE2 feature landscape, target balance, NULL structure visualized
- Chapter 4, §4.1.4 — temporal leakage annotation for ratingDiff

### Open questions / follow-ups

- Does `rating_null_timeline` show a step-function (schema change) or gradual missingness? Visual inspection of the artifact determines whether pre-change rows need special handling.
- Cross-dataset: aoestats duration body at p95 = 78.6 min vs aoe2companion at 63.15 min — difference noted in plot subtitle for thesis comparability.

---

## 2026-04-15 — [Phase 01 / Step 01_02_04] Univariate Census & Target Variable EDA

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** query
**Artifacts produced:**
- `reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md`
- `reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`

### Retroactive correction — 2026-04-16 (matchId cardinality)

DuckDB `SUMMARIZE` (HyperLogLog) significantly underestimated matchId cardinality: HLL reported 61,799,126 vs exact `COUNT(DISTINCT matchId)` = 74,788,989 (~21% undercount). A correction cell was added to the notebook after the existing `won` null-count patch: it runs `SELECT COUNT(DISTINCT matchId)` and overwrites the `approx_cardinality` for matchId in `matches_raw_null_census`. The `exact_matchid_cardinality_note` key was added to the artifact JSON to document the old and new values. Notebook re-executed 2026-04-16.

### What

Full univariate profiling of all four raw tables (NULL census, cardinality, numeric descriptive statistics, skewness/kurtosis, categorical frequency distributions, boolean census, temporal ranges, duplicate detection, NULL co-occurrence analysis), plus target variable analysis and preliminary temporal field classification per Invariant #3. All SQL embedded in the .md artifact (Invariant #6).

### Tables profiled

| Table | Rows | Columns |
|-------|------|---------|
| `matches_raw` | 277,099,059 | 55 |
| `ratings_raw` | 58,317,433 | 8 |
| `leaderboards_raw` | 2,381,227 | 19 |
| `profiles_raw` | 3,609,686 | 14 |

### NULL landscape

**matches_raw — high-NULL columns (>5%):**
- `server`: 97.99% NULL — populated for only ~2% of matches; near-dead for feature use
- `modDataset`: 99.72% NULL — scenario-specific, effectively dead
- `scenario`: 98.27% NULL — custom scenario matches only
- `password`: 82.90% NULL — password-protected lobby indicator
- `antiquityMode`: 68.66% NULL — recently added setting, absent from older matches
- `hideCivs`: 49.30% NULL — similarly phased in over time
- `rating` and `ratingDiff`: both 42.46% NULL — identical null rate confirms co-occurrence; NULLs = unranked matches
- `country`: 12.60% NULL; `regicideMode`: 7.39% NULL
- `team`: 4.90% NULL; `won` (target): 4.69% NULL (12,985,561 rows)

**NULL co-occurrence clusters:**
- Cluster A (8 boolean game-setting columns: allowCheats, lockSpeed, lockTeams, recordGame, sharedExploration, teamPositions, teamTogether, turboMode): 426,472 rows all eight NULL simultaneously — API schema change
- Cluster B (fullTechTree, population): 431,288 rows jointly NULL; cross-cluster overlap 428,321 rows — single underlying cause

**profiles_raw — 7 completely dead columns (100% NULL):** sharedHistory, twitchChannel, youtubeChannel, youtubeChannelName, discordId, discordName, discordInvitation — deprecated API fields, exclude from all feature engineering.

**leaderboards_raw — block NULL at 25.61%:** rank, wins, losses, streak, drops, active, rankLevel all co-NULL (unranked entries lack these fields).

**ratings_raw:** Zero NULLs except `rating_diff` (1.85% NULL, 1,078,873 rows).

### Target variable (`won`)

Near-perfectly balanced: 47.69% false (132.15M), 47.62% true (131.96M), 4.69% NULL (12.99M). All ranked queues show exact 50/50 balance. NULLs concentrated in `unranked` (15.74% NULL) and `unknown` (17.21% NULL) leaderboards.

Intra-match consistency check (2-row matches): 88.6% have proper complementary outcomes. However, 6.2% have `both_true` and 4.7% have `both_false` — internally inconsistent; flagged for Phase 02 investigation.

Primary prediction scope: rm_1v1 (26.8M matches) + qp_rm_1v1 (3.7M matches) = 30.5M 1v1 matches.

### Cardinality highlights

- `civ`: 68 distinct — full AoE2:DE roster. Top: Franks 5.68%, Mongols 4.45%, Britons 4.26%
- `map`: 261 distinct — Arabia 19.53%, Arena 16.80%, Black Forest 12.42% (top 3 = 49%)
- `name`: ~2.47M distinct player names

**Near-constant / dead fields:** `season` constant -1 across ratings_raw and leaderboards_raw; `rankLevel` constant 1; `treatyLength` 96.56% zero; `status` only 2 values (player/ai).

### Temporal leakage audit (Invariant #3)

**Confirmed post_game:** `ratingDiff` (range [-174, 319], direct leakage); `finished`; `won` (target).

**~~Critical ambiguity~~ Resolved — `matches_raw.rating`:** Originally classified `ambiguous_pre_or_post` due to identical 42.46% NULL rate with `ratingDiff`. **Resolved in 01_03_03:** cross-reference with `ratings_raw` confirmed `matches_raw.rating` is the **PRE-GAME** rating (99.8% exact match with nearest pre-match ratings_raw entry). `ratingDiff` = post_game_rating - pre_game_rating.

**ratings_raw:** Time-series ratings safe only with strict temporal join (`rating.date < match.started`).

**leaderboards_raw cumulative stats** (wins, losses, games, streak, drops): Singleton snapshots, not a time series — usable only as static context features, not dynamic features.

### Sentinel and anomaly values

- `matches_raw.rating`: min -1 (sentinel), max 5,001
- `ratings_raw.games`: max 1,775,260,795 — obvious data error; p95 is 4,736
- `matches_raw.population`: min 0, max 9,999 — sentinels at extremes; median 200
- `matches_raw.team`: max 255 — sentinel given median 2, p95 5
- **8,812,005 duplicate (matchId, profileId) pairs** (3.18%) — deduplication required in Phase 02

### Histogram findings

- **Match duration:** median 1,678s (28 min), mean 1,815s, p05 145s, p95 3,789s, max 3.28M s (38 days — bugged). Right-skewed.
- **matches_raw.rating** (non-NULL): mean 1,120, median 1,093, std 290 — bell-shaped around Elo anchor.
- **leaderboards_raw.games**: mean 174, median 45, skewness 8.51 — heavy right tail of active players.

### Decisions taken

- 7 dead columns in profiles_raw identified for exclusion
- 10 constant/dead fields catalogued across all tables
- `matches_raw.rating` flagged as ambiguous — **resolved in 01_03_03: PRE-GAME** (99.8% match)
- 4,398,727 internally inconsistent 2-row matches flagged for investigation

### Decisions deferred

- Row-level `rating`/`ratingDiff` co-occurrence check — 01_04 (verify: does `rating - ratingDiff` = prior rating in time series?)
- Deduplication of 8.8M duplicate (matchId, profileId) pairs
- Root cause of internally inconsistent won values (both_true, both_false)
- `ratings_raw.games` max outlier capping/exclusion strategy

### Thesis mapping

- Chapter 4, section 4.1.2 — AoE2 univariate profiles, NULL landscape, target balance, temporal classification
- Chapter 4, section 4.2.2 — Data quality: duplicates, sentinels, inconsistent outcomes

### Open questions / follow-ups

- Is `matches_raw.rating` pre-match or post-match Elo? Answering this gates the entire aoe2companion feature set.
- Root cause of 4.4M internally inconsistent 2-row matches?
- The 428K NULL co-occurrence cluster — early data before API fields existed?

### Plots (not in ROADMAP)

The following 5 PNGs were generated as exploratory visualization supplements during the univariate
census run. They are not declared in ROADMAP Step 01_02_04 (which is not plot-gated) and are not
gate-critical, but exist on disk under `reports/artifacts/01_exploration/02_eda/plots/`:

- `01_02_04_categorical_topk.png`
- `01_02_04_numeric_boxplots.png`
- `01_02_04_numeric_histograms.png`
- `01_02_04_temporal_match_counts.png`
- `01_02_04_won_distribution.png`

---

## 2026-04-14 — [Phase 01 / Step 01_02_03] Raw schema DESCRIBE

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** query
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_03_raw_schema_describe.json`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/matches_raw.yaml`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/ratings_raw.yaml`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/leaderboards_raw.yaml`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/profiles_raw.yaml`

### What

Captured the exact DuckDB column names and types for all four aoe2companion raw sources. Since step 01_02_02 had not yet been executed, no persistent DuckDB exists; the notebook uses in-memory DuckDB and reads source files directly with `LIMIT 0` to obtain schema without loading row data. Same read parameters as planned for 01_02_02 ingestion (`binary_as_string=true`, `union_by_name=true`, `filename=true` for Parquet; explicit `dtypes=` for CSV).

### Why

Establish the source-of-truth bronze-layer schema before full ingestion runs. The `data/db/schemas/raw/*.yaml` files are consumed by all downstream steps (feature engineering, cleaning, documentation). Invariant #6 — all DESCRIBE SQL embedded in artifact.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_03_raw_schema_describe.py`

- matches: `read_parquet(glob, binary_as_string=true, union_by_name=true, filename=true) LIMIT 0`
- ratings: `read_csv(glob, dtypes={profile_id: BIGINT, games: BIGINT, rating: BIGINT, date: TIMESTAMP, leaderboard_id: BIGINT, rating_diff: BIGINT, season: BIGINT}, union_by_name=true, filename=true) LIMIT 0`
- leaderboards, profiles: `read_parquet(singleton, binary_as_string=true, filename=true) LIMIT 0`

### Findings

| Source | Columns | Notable types |
|--------|---------|---------------|
| matches | 55 | `won` BOOLEAN (prediction target); `matchId`/`profileId` INTEGER; `started`/`finished` TIMESTAMP; `speedFactor` FLOAT |
| ratings | 8 | `profile_id` BIGINT; `date` TIMESTAMP; all numerics BIGINT |
| leaderboards | 19 | `profileId` INTEGER; `lastMatchTime`/`updatedAt` TIMESTAMP |
| profiles | 14 | `profileId` INTEGER; all string columns VARCHAR |

Key observations:
- `won` (BOOLEAN, nullable) confirmed as prediction target column
- Naming inconsistency cross-confirmed: `profileId` (camelCase, INTEGER) in matches and leaderboards vs `profile_id` (snake_case, BIGINT) in ratings — noted for Phase 02 join design
- `speedFactor` is FLOAT (only non-integer numeric in matches)
- All four schema YAMLs populated in `data/db/schemas/raw/`

### Decisions taken

- Schema YAMLs populated from this DESCRIBE output — source-of-truth for all downstream steps
- No ingestion or schema changes at this step — read-only

### Decisions deferred

- Column descriptions (`TODO: fill`) in `*.yaml` files — deferred to systematic profiling (01_03)

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset: bronze-layer schema catalog

### Open questions / follow-ups

- None — schema fully captured

---

## 2026-04-14 — [Phase 01 / Step 01_02_02] DuckDB ingestion

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** ingest
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.json`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.md`

### What

Materialised four `*_raw` DuckDB tables from the full aoe2companion corpus (2,073 daily match Parquets, 2,072 daily rating CSVs, 1 leaderboard Parquet, 1 profile Parquet) into the persistent database at `src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/db.duckdb`.

### Why

Enable SQL-based EDA for subsequent profiling (01_03) and cleaning (01_04). Invariants #6 (reproducibility), #9 (step scope), #10 (relative filenames) upheld.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_02_duckdb_ingestion.py`
Module: `src/rts_predict/games/aoe2/datasets/aoe2companion/ingestion.py`

### Findings

**Table row counts:**
| Table | Rows |
|-------|------|
| `matches_raw` | 277,099,059 |
| `ratings_raw` | 58,317,433 |
| `leaderboards_raw` | 2,381,227 |
| `profiles_raw` | 3,609,686 |

**Dtype strategy for `ratings_raw`:** Explicit `dtypes=` map (BIGINT/TIMESTAMP) required — `read_csv_auto` infers all 7 columns as VARCHAR at scale (2,072 files). Strategy established in Step 01_02_01.

**NULL rates (key fields):**
- `matches_raw.won`: 12,985,561 NULLs / 277,099,059 rows (4.69%) — root cause established in 01_02_01 won=NULL investigation
- `matches_raw.matchId`: 0 NULLs
- `matches_raw.filename`: 0 NULLs
- `ratings_raw.profile_id`: 0 NULLs
- `ratings_raw.filename`: 0 NULLs

**Invariant I10 (relative filenames):** All four tables pass — filenames stored relative to `raw_dir`. Enforced inline via `SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)` in every CTAS. No post-load UPDATE (would OOM on 277M-row `matches_raw`).

**Parquet binary columns:** All Parquet reads use `binary_as_string=true` for the unannotated BYTE_ARRAY columns in matches/leaderboards/profiles. Established in 01_02_01.

### Decisions taken

- All tables use `*_raw` suffix convention (bronze layer)
- Inline `SELECT * REPLACE` for I10 relativization — never post-load UPDATE
- Explicit dtype map for ratings CSV ingestion — never `read_csv_auto` at scale
- `binary_as_string=true` for all Parquet sources

### Decisions deferred

- Handling of 12.99M NULL `won` values — deferred to Step 01_04 (data cleaning)

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset: four-table ingestion, dtype strategy, I10 compliance

### Artifact note

The `.json` artifact `sql` key records pre-fix SQL (`SELECT * FROM read_parquet(...)` without `REPLACE`). The actual ingestion code uses `SELECT * REPLACE (substr(filename, {prefix_len}) AS filename)`. The DuckDB on disk is correct; the artifact should be regenerated from a fresh notebook run to reflect the inline I10 pattern.

### Open questions / follow-ups

- Full NULL profiles for all 55 `matches_raw` columns — deferred to 01_03 (systematic profiling)

---

## 2026-04-14 — [Phase 01 / Step 01_02_01] won=NULL root-cause investigation

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** query (amendment to 01_02_01)
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json` (extended with `won_null_root_cause` key)

### What

Diagnosed why 12,985,561 rows (4.69%) have `won=NULL` in the full matches
corpus. Added section 8 (Q1–Q4) to the 01_02_01 pre-ingestion notebook to
distinguish between two hypotheses: H1 (Parquet schema heterogeneity causing
DuckDB type promotion to inject NULLs) and H2 (genuine NULL values in source
files).

### Why

The `won` column is the prediction target for this thesis. Before any cleaning
decisions can be made in later steps, the root cause of NULLs must be
understood. Invariant #6 (reproducibility) — all diagnostic queries embedded
in the artifact.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py`

Q1: `parquet_schema()` metadata-only scan — counts distinct `won` Parquet types
across all 2,073 files without loading row data.

Q2: Per-type-group value census without `union_by_name` — reads each type group
independently to observe native values and genuine NULLs.

Q3: Type promotion NULL injection test — compares per-file NULL counts before
and after `union_by_name=true` on a mixed-type sample (runs only if Q1 finds
multiple types).

Q4: Per-file NULL distribution — identifies which files contribute NULLs and
their date range under `union_by_name=true`.

### Findings

**H1 REJECTED.** `parquet_schema()` scan across all 2,073 match files found a
single `won` Parquet type: `BOOLEAN`. There is no schema heterogeneity. DuckDB
type promotion under `union_by_name=true` is not the cause of NULLs.

**H2 SUPPORTED.** 12,985,561 genuine NULL `won` values exist in the source
files. Every single file (2,073 of 2,073) contributes NULLs — the date range
of affected files is 2020-08-01 to 2026-04-04, i.e., the entire corpus
history. There is no temporal step-change or isolated bad period: NULLs are
a structural property of the dataset from day one.

Additional context from the existing artifact:
- `avg_rows_per_match = 3.71` — the dataset contains substantial team-game
  data beyond 1v1 (expected avg would be 2.0 for pure 1v1). This means
  `won=NULL` cannot be attributed to a single-player record issue.
- NULL rate: 4.69% of 277,099,059 total rows = 12,985,561 NULL `won` values.
- The aoe2companion API simply does not record a winner for some matches — the
  root cause is upstream (API-level recording gap), not a data engineering
  artefact.

### Decisions taken

- H1 definitively rejected: no INT64-to-BOOLEAN cast recovery needed.
- H2 confirmed: NULLs are genuine and uniformly distributed across the entire
  dataset history — not concentrated in a time window that could be excluded.
- Investigation scope limited to diagnosis only — no cleaning decisions made
  at this step.

### Decisions deferred

- Handling strategy for NULL `won` rows (row-level drop, match-level drop,
  or leaderboard-filtered subset) deferred to Step 01_04 (data cleaning).
- Impact on thesis scope: whether to restrict analysis to the 95.31% of rows
  with recorded winners, or characterise the NULL population separately.
- Whether `avg_rows_per_match = 3.71` implies a leaderboard filter is needed
  to isolate 1v1 matches before the prediction task is scoped.

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 data quality: won column NULL analysis
- Chapter 4, §4.2.1 — Ingestion validation methodology

### Open questions / follow-ups

- What leaderboard value(s) correspond to ranked 1v1 in aoe2companion? Does
  filtering to that leaderboard reduce the NULL rate?
- Is `avg_rows_per_match = 3.71` driven by FFA/team-game leaderboards only,
  or does it affect the ranked 1v1 population too?

---

## 2026-04-13 — [Phase 01 / Step 01_02_01] DuckDB pre-ingestion investigation

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** query
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json`

### What

Pre-ingestion investigation using in-memory DuckDB and direct Parquet/CSV
queries to characterise the four aoe2companion data sources before committing
to a DuckDB ingestion design. Binary column inspection, smoke test, full-corpus
NULL rate census, and match_id uniqueness check. No DuckDB tables were created
at this step — that is step 01_02_02.

### Why

Determine ingestion strategy before materialising 277M rows. Invariants #7
(type fidelity) and #9 (step scope) — pre-ingestion characterisation is a
distinct step from ingest. The binary column issue (unannotated BYTE_ARRAY)
and the CSV type inference pitfall at scale must be resolved before 01_02_02.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py`

### Findings

**Binary column inspection** (metadata read on `match-2020-08-01.parquet` sample):
- matches: 22 of 54 columns are BYTE_ARRAY with no logical type annotation
  (no UTF-8 annotation) — strings stored without Parquet STRING annotation
- leaderboards: 4 of 18 columns BYTE_ARRAY unannotated
- profiles: 11 of 13 columns BYTE_ARRAY unannotated
- All require `binary_as_string=true` at ingestion to resolve to VARCHAR

**Smoke test** (sampled subset of files):
- matches sample: 491,099 rows × 55 columns
- ratings sample: 266,508 rows × 8 columns

**Full-corpus NULL rates** (direct Parquet queries on all 2,073 match files):
- Total rows: 277,099,059; `matchId` and `profileId` 100% populated
- `won` column: 12,985,561 NULLs (4.69%) — see 2026-04-14 won-NULL root-cause entry

**Match_id uniqueness** (full corpus):
- 74,788,989 distinct `matchId` values; avg 3.71 rows per match
- avg > 2.0 indicates substantial team-game data beyond 1v1

**CSV ratings at scale:**
- `read_csv_auto` infers all 7 columns as VARCHAR when scanning all 2,072 files
  simultaneously — explicit `types=` required for correct BIGINT/TIMESTAMP types
- Missing file: `rating-2025-07-11.csv` — 2,073 match files vs 2,072 rating files

### Decisions taken

- All Parquet reads require `binary_as_string=true`
- CSV ratings require explicit column type map — never `read_csv_auto` at scale
- Raw layer uses `SELECT *` with `filename=true`; no explicit DDL at this step
- Full row counts for ratings/leaderboards/profiles deferred to 01_02_02

### Decisions deferred

- Handling of 12.99M NULL `won` values — see 2026-04-14 root-cause entry;
  cleaning decision deferred to Step 01_04
- Whether missing `rating-2025-07-11.csv` is recoverable or a permanent gap
- `profileId` vs `profile_id` naming inconsistency across tables — deferred
  to Phase 02 join design

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset: binary column handling, CSV type pitfall
- Chapter 4, §4.2.1 — Ingestion validation methodology

### Open questions / follow-ups

- Full row counts for ratings_raw, leaderboards_raw, profiles_raw — confirmed
  in 01_02_02 artifact
- Does restricting to ranked 1v1 leaderboard reduce the won=NULL rate and
  bring avg_rows_per_match close to 2.0? — investigate in 01_03 or 01_04

---

## 2026-04-13 — [Phase 01 / Step 01_01_02] Schema discovery

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** content
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json`

### What

Full census of all 4,147 data files: Parquet metadata-only reads for matches,
leaderboards, and profiles; CSV header + 50-row samples for ratings.
Catalogued column names, physical types, and nullability.

### Why

Map the exact schema of each source before ingestion. Invariant #6 requires
knowing field names and types for reproducibility.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_02_schema_discovery.py`

### Findings

- Matches: 54 columns per Parquet file, consistent schema across all 2,073 daily files. 22 columns have unannotated BYTE_ARRAY physical type (no logical type annotation — Parquet files were written without UTF8 annotation)
- Ratings: 7 CSV columns (`profile_id`, `games`, `rating`, `date`, `leaderboard_id`, `rating_diff`, `season`), consistent across 2,072 files
- Leaderboards: 18 columns (singleton Parquet), 4 unannotated BYTE_ARRAY columns
- Profiles: 13 columns (singleton Parquet), 11 unannotated BYTE_ARRAY columns
- Schema is consistent within each file type — no variant columns detected

### Decisions taken

- Full census (not sampling) used because file counts are manageable (<4,200 files)
- BYTE_ARRAY without annotation flagged for `binary_as_string=true` at ingestion

### Decisions deferred

- Ingestion strategy deferred to 01_02_01

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset schema description

### Open questions / follow-ups

- Why do Parquet files lack UTF8 annotation on string columns? (upstream data source issue)

---

## 2026-04-13 — [Phase 01 / Step 01_01_01] File inventory

**Category:** A (science)
**Dataset:** aoe2companion
**Step scope:** filesystem
**Artifacts produced:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`

### What

Catalogued the aoe2companion raw data directory: 4 subdirectories (matches,
ratings, leaderboards, profiles), file counts, sizes, extensions, and
temporal coverage via filename date parsing.

### Why

Establish the data landscape. Invariant #9 — filesystem-level inventory before
content inspection.

### How (reproducibility)

Notebook: `sandbox/aoe2/aoe2companion/01_exploration/01_acquisition/01_01_01_file_inventory.py`

### Findings

- 4,153 total files across 4 subdirectories, 9.2 GB total
- Matches: 2,073 daily Parquet files (6.6 GB), 2020-08-01 to 2026-04-04, no date gaps
- Ratings: 2,072 daily CSV files (2.5 GB), 2020-08-01 to 2026-04-04, no date gaps
- Leaderboards: 1 singleton Parquet (83 MB)
- Profiles: 1 singleton Parquet (162 MB)
- 1 file count gap: matches has 2,073 files, ratings has 2,072 (missing 2025-07-11)

### Decisions taken

- Temporal coverage spans ~5.7 years — sufficient for longitudinal analysis
- File count mismatch between matches and ratings noted for investigation

### Decisions deferred

- Internal file structure deferred to 01_01_02

### Thesis mapping

- Chapter 4, §4.1.2 — AoE2 dataset description, temporal coverage, data volume

### Open questions / follow-ups

- None — straightforward inventory step
