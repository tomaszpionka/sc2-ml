# Step 01_04_03b — canonical_slot Amendment (aoestats)

**Generated:** 2026-04-20
**Dataset:** aoestats
**Game:** AoE2
**Step:** 01_04_03b (Amendment to 01_04_03)
**Branch:** `feat/aoestats-canonical-slot`
**Resolves:** BACKLOG F1 (Phase 02 unblocker) + coupled W4 (INVARIANTS §5 I5 PARTIAL → HOLDS)

---

## Summary

Adds `canonical_slot VARCHAR` at position 7 (after `won`, before `duration_seconds`)
to `matches_history_minimal` via `CREATE OR REPLACE VIEW`. The VIEW is now a 10-column
schema (was 9-column from step 01_04_03). All 7 assertions pass. Row count preserved at
35,629,894 (17,814,947 matches × 2 rows/match).

---

## Derivation Choice — hash-on-match_id (user-selected 2026-04-20, U1 RESOLVED)

```sql
-- In p0_half (focal_team = 0):
CASE WHEN (hash('aoestats::' || m.game_id) + 0) % 2 = 0 THEN 'slot_A' ELSE 'slot_B' END AS canonical_slot,

-- In p1_half (focal_team = 1):
CASE WHEN (hash('aoestats::' || m.game_id) + 1) % 2 = 0 THEN 'slot_A' ELSE 'slot_B' END AS canonical_slot,
```

**Skill-orthogonality (structural argument, not empirical).**

Both rows of any single match share the same `match_id` value (the VIEW's UNION-ALL pivot
rebuilds from a 1-row-per-match source `matches_1v1_clean`). Therefore `hash(match_id)` is
identical for both rows of a match. The binary splitter `(hash + focal_team) % 2` with
`focal_team ∈ {0, 1}` distributes them into complementary slots: `0 % 2 = 0 ≠ 1 % 2 = 1`.

The argument is **independent of `match_id`'s semantic content**: even if `match_id` encoded
player identity, within-match distinct slots would still hold by the `focal_team` pivot alone.
Skill-orthogonality across matches follows from the hash function's avalanche property — no
player attribute enters the derivation.

**W3 ARTEFACT_EDGE → canonical_slot mapping.**

The upstream `matches_raw` API assigns `team=1` to the higher-ELO player in 80.3% of matches
(mean +11.9 ELO; `01_04_05_i5_diagnosis.json`). This is the W3 ARTEFACT_EDGE verdict
(BACKLOG F1 predecessor). `canonical_slot` replaces `team` as the I5-compliant slot label:
it does not carry any skill signal because `hash(match_id)` does not encode any player property.

**Alternatives rejected.**

| Candidate | Rejection reason |
|-----------|-----------------|
| `profile_id`-ordered | 01_04_05 Q4: `lower_id_first_win_rate = 0.5066 (+0.66pp)`. Account age correlates with skill (early-adopter effect). MUST NOT be used as slot-neutralizing technique. |
| `old_rating`-ordered | Skill-coupled by construction. Does not neutralize W3 artefact. |
| Hash on sorted `(min, max)` `profile_id` tuple | Inherits skill correlation; sort operates on player-property magnitudes. |

---

## Baseline Re-Verification (Pass 2 fix — guards against stale-baseline drift)

Re-ran cached `01_04_03` SQL queries against the **current live DuckDB state** before
executing the amended DDL. All values match the 2026-04-18 cached baseline exactly.

| Metric | Cached 2026-04-18 | Live 2026-04-20 | Match |
|--------|-------------------|-----------------|-------|
| total_rows | 35,629,894 | 35,629,894 | PASS |
| distinct_match_ids | 17,814,947 | 17,814,947 | PASS |
| symmetry_violations | 0 | 0 | PASS |
| overall_won_rate | 0.5 | 0.5 | PASS |
| min_duration_seconds | 3 | 3 | PASS |
| max_duration_seconds | 5,574,815 | 5,574,815 | PASS |
| avg_duration_seconds | 2418.094 | 2418.094 | PASS |

**Baseline reverification status: PASS**

---

## Schema After Amendment (10 columns)

| # | Column | Type | Semantics |
|---|--------|------|-----------|
| 1 | `match_id` | VARCHAR | `'aoestats::'` + game_id |
| 2 | `started_at` | TIMESTAMP | UTC match start time |
| 3 | `player_id` | VARCHAR | Focal player |
| 4 | `opponent_id` | VARCHAR | Opposing player |
| 5 | `faction` | VARCHAR | Focal player's civilization |
| 6 | `opponent_faction` | VARCHAR | Opposing player's civilization |
| 7 | `won` | BOOLEAN | Focal player's outcome |
| 8 | `canonical_slot` | VARCHAR | Skill-orthogonal slot label (`slot_A` or `slot_B`) |
| 9 | `duration_seconds` | BIGINT | POST_GAME_HISTORICAL |
| 10 | `dataset_tag` | VARCHAR | Constant `'aoestats'` |

---

## Assertions (all 7 pass)

| Assertion | Result | Value |
|-----------|--------|-------|
| row_count_preserved | PASS | 35,629,894 |
| canonical_slot_binary_cardinality | PASS | `['slot_A', 'slot_B']` |
| canonical_slot_symmetry (per-match distinct slots) | PASS | 0 violations |
| canonical_slot_null_count | PASS | 0 NULLs |
| canonical_slot_balance (report-only) | REPORT | slot_A=17,814,947; slot_B=17,814,947 (exactly 50/50) |
| canonical_slot_win_rate (report-only) | REPORT | slot_A=0.4999; slot_B=0.5001 |
| canonical_slot_I9_invariance | PASS | All existing-column stats identical before/after |

**All assertions passed: True**

---

## Downstream Phase 02 Usage Pattern

Phase 02 per-slot feature engineering MUST use `canonical_slot` (not raw `team`, not `p0_civ`/`p1_civ`
split) as the slot label for any feature conditioned on slot identity:

```sql
-- Per-slot win rate (Phase 02 example):
SELECT canonical_slot, AVG(CAST(won AS INT)) AS win_rate
FROM matches_history_minimal
GROUP BY canonical_slot;

-- Per-slot faction feature (Phase 02 example):
SELECT canonical_slot, faction, COUNT(*) AS n
FROM matches_history_minimal
GROUP BY canonical_slot, faction
ORDER BY canonical_slot, n DESC;
```

The `team` field from `matches_1v1_clean` MUST NOT be used as a Phase 02 feature
(W3 ARTEFACT_EDGE; see `01_04_05_i5_diagnosis.{json,md}`).

---

## Cross-link to §4.4.6 Flag Closure

This amendment operationally closes the `[PRE-canonical_slot]` flag defined at
`reports/specs/01_05_preregistration.md` §1 line 71 and at thesis §4.4.6. Pre-amendment
01_05 artifacts bearing `[PRE-canonical_slot]` tags remain as historical markers; future
Phase 02 outputs will not require the flag.

See also:
- INVARIANTS.md §5 I5 row: transitions PARTIAL → HOLDS (W4)
- `reports/specs/01_05_preregistration.md` §14 v1.1.0 amendment
- `risk_register_aoestats.csv` AO-R01: OPEN → RESOLVED
- `modeling_readiness_aoestats.md`: READY_CONDITIONAL → READY_WITH_DECLARED_RESIDUALS

---

## Artifact

Validation JSON: `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_03b_canonical_slot_amendment.json`

---

## T06 Downstream Notebook Safety Audit (2026-04-20)

Audited all existing aoestats 01_05 and 01_06 notebooks for `matches_history_minimal` references
to confirm zero `SELECT *` patterns (which would implicitly pull the new column and potentially
affect existing notebook outputs).

**Scope audited:**
- `sandbox/aoe2/aoestats/01_exploration/05_temporal_panel_eda/` — 8 .py notebooks
- `sandbox/aoe2/aoestats/01_exploration/06_decision_gates/` — 4 .py notebooks
- `src/rts_predict/games/aoe2/datasets/aoestats/` — production .py files

**Grep results:**
- `SELECT * FROM matches_history_minimal` patterns: **0 found** (zero across all scopes)
- `matches_history_minimal` references total: 39 (all use explicit column projections or DESCRIBE)
- Production code (`analysis/survivorship.py`): 3 references, all using explicit `SELECT <cols>`
- 01_06 decision gates: 12 references — all schema-YAML reads and DESCRIBE patterns

**Conclusion:** Zero impact. All existing 01_05 and 01_06 aoestats notebooks use explicit
column projections. Adding `canonical_slot` as column 8 does not affect any existing query
or output. No notebook re-run is required.

**Hard stop condition (T06a):** None triggered. Zero `SELECT *` patterns found.
