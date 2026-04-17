---
category: A
branch: feat/01-04-02-aoestats
date: 2026-04-17
planner_model: claude-opus-4-7[1m]
phase: "01"
pipeline_section: "01_04"
step: "01_04_02"
dataset: aoestats
game: aoe2
predecessor_step: "01_04_01"
predecessor_pr: "PR #139 (aoestats matches_1v1_clean column scope) + PR #138 (I3 violation removal)"
template_pr: "PR #142 (sc2egset 01_04_02 — merged 96d6b01)"
sandbox_notebook: "sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py"
artifacts_target: "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/"
source_artifacts:
  - "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv"
  - "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json"
  - "src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md"
  - "src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md  (lines 731-939, 01_04_01 step block, decisions_surfaced DS-AOESTATS-01..08)"
  - "src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/player_history_all.yaml  (current; to be UPDATED)"
  - "sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_01_data_cleaning.py  (current VIEW DDL)"
  - "sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py  (template — PR #142)"
  - "src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/matches_flat_clean.yaml  (template format)"
invariants_touched: ["I3", "I5", "I6", "I7", "I8", "I9", "I10"]
---
```

## Scope

Apply DDL changes to act on **all 8 cleaning decisions (DS-AOESTATS-01..08)** surfaced by the 01_04_01 missingness audit, mirroring the established sc2egset 01_04_02 pattern (PR #142). Modify VIEW DDL for `matches_1v1_clean` and `player_history_all` (no raw table changes per Invariant I9). Produce CONSORT column-flow + cleaning registry + post-cleaning assertion battery + schema YAML files. Aoestats only — aoe2companion follows in an independent planning round + PR.

## Problem Statement

The 01_04_01 missingness audit produced an empirical ledger (34 rows × 17 cols) and surfaced 8 cleaning decisions for downstream resolution. Per Manual §4 + the established pattern from sc2egset PR #142, these decisions must be ACTED on by 01_04_02 via VIEW DDL modifications. Without this step:

1. `matches_1v1_clean` retains 2 zero-information constant columns (`leaderboard`, `num_players` — DS-AOESTATS-08), polluting Phase 02 feature space.
2. Sentinel-encoded ratings (`p0_old_rating`, `p1_old_rating`, `avg_elo` — DS-AOESTATS-02, DS-AOESTATS-03) remain raw `0` integers indistinguishable from genuinely-low ratings, blocking any Phase 02 imputation/encoding pipeline that relies on `IS NULL` semantics.
3. The CONSORT column-flow + cleaning registry required by Manual §4.1 + §4.3 is not produced.
4. No `matches_1v1_clean.yaml` schema YAML exists at all (`player_history_all.yaml` exists but does not yet declare the I3 provenance categories explicitly).

The pipeline cannot transition `01_04` from `in_progress` → `complete` without this work.

## Assumptions & unknowns

**Assumptions (confirmed by reading source artifacts):**

1. **Ledger empirical evidence is authoritative.** All thresholds in this plan derive from `01_04_01_missingness_ledger.csv` rows (per I7), not from prose narrative. Specifically:
   - `matches_1v1_clean` row count = 17,814,947 (asserted in 01_04_01 notebook; matches ledger column 4)
   - `player_history_all` row count = 107,626,399 (asserted in 01_04_01 notebook)
   - `matches_1v1_clean` has 21 columns (set guarded in 01_04_01 notebook lines 534-541); `player_history_all` has 13 columns (lines 593-597).
2. **Row counts are unchanged by 01_04_02.** This is a column-only cleaning step. CONSORT-row tables list the same row counts pre/post (asserted).
3. **No `matches_1v1_clean.yaml` exists yet.** This step CREATES it.
4. **Current `player_history_all.yaml` uses prose-format `notes:` vocabulary** (e.g., `"TARGET. Used as prediction label..."`) — consistent with current aoestats convention. Per the user's CRITICAL ASYMMETRY #2, this PR KEEPS that vocabulary and does NOT migrate to single-token (open question to defer to a CROSS PR).
5. **The `db.con` public attribute is uniform across all three datasets** (W4 fix from 01_04_01).
6. **The DuckDB instance is writable.** Step requires `read_only=False`.

**Unknowns (NOT decided here — flagged as Open Questions):**

- Whether to encode sentinel-bearing ratings via NULLIF (Phase 02-friendly) or retain `0` as an explicit unrated-category encoding alongside an `is_unrated` flag (DS-AOESTATS-02).
- Whether to drop the 7,055-NULL `raw_match_type` column or retain (DS-AOESTATS-04, currently RETAIN_AS_IS in ledger; the column is informationally redundant given the upstream `leaderboard='random_map'` + `COUNT(*)=2` filters in `matches_1v1_clean`).
- Whether to migrate `notes:` to single-token vocabulary (cross-dataset I8 question; defer to CROSS PR).

## Literature context

Same canonical citations as 01_04_01 + sc2egset 01_04_02:

- **Liu, X. et al. (2020).** CONSORT-AI extension for clinical-trial reports. BMJ 370. — Column-count flow tables.
- **Jeanselme, V. et al. (2024).** Participant Flow Diagrams for Health Equity in AI. JBI 152. — Subgroup impact reporting.
- **Schafer, J.L. & Graham, J.W. (2002).** Missing Data: Our View. Psych Methods 7(2). — <5% MCAR boundary citation (justifies leaving `raw_match_type`'s 0.0396% null rate).
- **van Buuren, S. (2018).** Flexible Imputation. CRC. — Warning against rigid global thresholds (justifies non-binding nature of CONVERT_SENTINEL_TO_NULL recommendations where `carries_semantic_content=True`).
- **Sambasivan, N. et al. (2021).** Data Cascades. CHI '21. — Surface decisions explicitly.
- **Rubin, D.B. (1976).** Inference and missing data. Biometrika 63(3). — MCAR/MAR/MNAR taxonomy carried forward from 01_04_01.
- **Manual `01_DATA_EXPLORATION_MANUAL.md` §4.1 (cleaning registry), §4.2 (non-destructive), §4.3 (CONSORT impact), §4.4 (post-validation).**

No new citations introduced — this PR continues the 01_04_01 framework.

## Execution Steps

The plan organizes execution into Sections 1-6 below: per-DS resolutions (1), VIEW DDL changes (2), post-cleaning validation (3), new ROADMAP step entry (4), notebook cell structure (5), and status updates (6). The notebook is implemented as a single ~28-cell artifact at `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py`. Each section below is execution-step content.

## Section 1 — Per-DS resolution proposal (DS-AOESTATS-01..08)

For each DS, recommendation cites the empirical ledger row + the rule from the 01_04_01 framework. **Empirical rates loaded from `01_04_01_missingness_ledger.csv` at notebook runtime** (per I7 — no hard-coded magic numbers).

| DS ID | Column(s) | Ledger evidence | Recommended decision | DDL effect | Justification |
|---|---|---|---|---|---|
| **DS-AOESTATS-01** | `team_0_elo`, `team_1_elo` (sentinel=-1, ABSENT in 1v1 scope) | `n_sentinel=0` in ledger; `pct_missing_total=0.0`. Ledger `recommendation=RETAIN_AS_IS / mechanism=N/A` (F1 zero-missingness override). | **NO-OP (RETAIN_AS_IS).** Both columns kept as-is. Add a documentation comment in the DDL noting that the upstream 1v1 ranked-decisive filter excludes the rows that carried sentinel=-1; if scope ever broadens, re-audit. | None | F1 override fired in ledger; sentinel empirically absent in this VIEW's filtered scope. Spec retains `mechanism=MCAR/sentinel=-1` for design intent (carried from raw matches_raw). |
| **DS-AOESTATS-02** | `p0_old_rating`, `p1_old_rating` in `matches_1v1_clean`; `old_rating` in `player_history_all` (sentinel=0) | Ledger: `n_sentinel=4730` (p0, 0.0266% of 17,814,947 matches_1v1_clean rows) / `n_sentinel=188` (p1, 0.0011% of 17,814,947) / `n_sentinel=5937` (player_history_all old_rating, 0.0055% of 107,626,399 rows); `mechanism=MAR`; `recommendation=CONVERT_SENTINEL_TO_NULL` (non-binding because `carries_semantic_content=True`). | **CONVERT_SENTINEL_TO_NULL via NULLIF + ADD `is_unrated` indicator flag.** Apply to all 3 columns symmetrically. | `matches_1v1_clean`: `NULLIF(p0_old_rating, 0) AS p0_old_rating`, `NULLIF(p1_old_rating, 0) AS p1_old_rating`, `(p0_old_rating = 0) AS p0_is_unrated`, `(p1_old_rating = 0) AS p1_is_unrated`. `player_history_all`: `NULLIF(old_rating, 0) AS old_rating`, `(old_rating = 0) AS is_unrated`. | Mirrors the sc2egset DS-SC2-10 pattern (NULLIF + indicator) at <0.03% rate per ledger. NULLIF makes `IS NULL` semantics consistent for Phase 02 imputation; `is_unrated` flag preserves the missingness-as-signal information per scikit-learn `MissingIndicator` doctrine cited in 01_04_01. **NOTE:** This is the pragmatic recommendation — the alternative "retain as unrated category" remains in the Open Questions section. |
| **DS-AOESTATS-03** | `avg_elo` (sentinel=0) in `matches_1v1_clean` | Ledger: `n_sentinel=118` (0.0007% of 17,814,947 matches_1v1_clean rows; matches_raw scope had n_zero=121 — 3-row delta is the 1v1 filter discarding 3 sentinel rows); `mechanism=MAR`; `recommendation=CONVERT_SENTINEL_TO_NULL` (non-binding because `carries_semantic_content=True`). | **CONVERT_SENTINEL_TO_NULL via NULLIF.** No companion flag (avg_elo is a derived statistic; the underlying p0/p1 unrated-flags already capture the semantic content). | `NULLIF(avg_elo, 0) AS avg_elo` | Lowest sentinel rate (0.0007%); negligible. NULLIF makes the column safely usable in Phase 02 averaging operations without the 0-sentinel skewing means. The `p0_is_unrated`/`p1_is_unrated` indicators (DS-AOESTATS-02) already convey the unrated subgroup membership. |
| **DS-AOESTATS-04** | `raw_match_type` (7,055 NULLs in matches_1v1_clean, 0.0396% of 17,814,947 rows) | Ledger: `n_null=7055`; `mechanism=MCAR`; `recommendation=RETAIN_AS_IS` (rate < 5% Schafer & Graham boundary). Ledger n_distinct=1.0 implies cardinality of the **non-null** values is 1 in the filtered scope. | **DROP_COLUMN** (NOTE-1 critique fix: explicit override of ledger's RETAIN_AS_IS — the constants-detection branch (W7 fix in 01_04_01 framework) is not mutually exclusive with rate-based recommendations and overrides when n_distinct=1 in the cleaned scope). | `matches_1v1_clean`: remove `raw_match_type` from SELECT. | Ledger `n_distinct=1.0` (over non-NULL rows in filtered scope) means the column is effectively constant in the 1v1-ranked-decisive scope; the upstream `leaderboard='random_map'` + `COUNT(*)=2` filters already enforce ranked 1v1, making `raw_match_type` informationally redundant. The 7,055 NULLs are MCAR but contribute no signal beyond what the upstream filter already encodes. Mirror of sc2egset DS-SC2-08 (constants-detection branch → DROP_COLUMN). |
| **DS-AOESTATS-05** | `team1_wins` (target, **BOOLEAN** — verified per ledger row 22 + DDL `p1.winner AS team1_wins`) | Ledger: `n_null=0`; `recommendation=RETAIN_AS_IS / mechanism=N/A`; F1 override fired. | **NO-OP (RETAIN_AS_IS).** | None | Zero NULLs verified. The `WHERE p0.winner != p1.winner` upstream exclusion in 01_04_01 already enforces decisiveness — there is no Undecided/Tie analog in aoestats (CRITICAL ASYMMETRY #5). No `is_decisive_result` flag is needed because the column is already strict 0/1. |
| **DS-AOESTATS-06** | `winner` in `player_history_all` | Ledger: `n_null=0`; `recommendation=RETAIN_AS_IS / mechanism=N/A`. | **NO-OP (RETAIN_AS_IS).** | None | Zero NULLs verified by 01_04_01 (round-2 reviewer-deep B3 fix). Re-asserted in this step's assertion battery. The 01_04_01 audit framework's target-override post-step would automatically flip this to `EXCLUDE_TARGET_NULL_ROWS` if NULLs surface in future loads — no Phase 02 code change required. |
| **DS-AOESTATS-07** | `overviews_raw` (singleton metadata, 1 row) | 01_04_01 audit: out-of-analytical-scope; not used by any VIEW. | **FORMALLY DECLARE OUT-OF-ANALYTICAL-SCOPE in the cleaning registry + JSON artifact.** No DDL change. | None | Documentation-only resolution. The cleaning registry rule records this declaration so downstream Phase 02 / 03 / etc. cannot inadvertently treat the table as a feature source. |
| **DS-AOESTATS-08** | `leaderboard`, `num_players` (constants in `matches_1v1_clean`) | Ledger `n_distinct=1` for both; `recommendation=DROP_COLUMN / mechanism=N/A`. | **DROP_COLUMN both.** | `matches_1v1_clean`: remove `leaderboard` and `num_players` from SELECT. RETAIN both in `player_history_all` (where they are NOT constants — `player_history_all` covers all leaderboards and player_counts). | Ledger constants-detection. Mirrors sc2egset DS-SC2-08 (12 go_* constants) pattern. The upstream `WHERE m.leaderboard='random_map'` and `COUNT(*)=2` filters reduce these columns to single values in this VIEW scope — zero information content, drop. |

**Total per-VIEW DDL impact summary:**
- **`matches_1v1_clean`**: drop 3 (`leaderboard`, `num_players`, `raw_match_type`), modify 3 (`p0_old_rating`, `p1_old_rating`, `avg_elo` → NULLIF), add 2 (`p0_is_unrated`, `p1_is_unrated`). Net: 21 → 21 - 3 + 2 = **20 cols.** (Modified columns retain their slot.)
- **`player_history_all`**: modify 1 (`old_rating` → NULLIF), add 1 (`is_unrated`). Net: 13 → 13 + 1 = **14 cols.**

## Section 2 — VIEW DDL changes (concrete final-state per VIEW)

### 2.1 `matches_1v1_clean` — final 20-column DDL

```sql
CREATE OR REPLACE VIEW matches_1v1_clean AS
-- Purpose: Prediction-target VIEW. Ranked 1v1 decisive matches only.
-- Row multiplicity: 1 row per match (NOT 2-per-match like sc2egset matches_flat_clean).
-- Target column: team1_wins (BOOLEAN; 0/1 strict — no Undecided/Tie analog in aoestats).
-- Column set: 20 PRE_GAME + IDENTITY + TARGET columns (post 01_04_02).
-- All cleaning decisions (DS-AOESTATS-01..08) documented in 01_04_02_post_cleaning_validation.json.
WITH ranked_1v1 AS (
    SELECT m.game_id
    FROM matches_raw m
    INNER JOIN (
        SELECT game_id
        FROM players_raw
        GROUP BY game_id
        HAVING COUNT(*) = 2 AND COUNT(DISTINCT team) = 2
    ) pc ON m.game_id = pc.game_id
    WHERE m.leaderboard = 'random_map'
),
p0 AS (SELECT * FROM players_raw WHERE team = 0),
p1 AS (SELECT * FROM players_raw WHERE team = 1)
SELECT
    -- IDENTITY
    m.game_id,
    m.started_timestamp,

    -- DS-AOESTATS-08: leaderboard DROPPED (constant n_distinct=1 in this scope)
    m.map,
    m.mirror,
    -- DS-AOESTATS-08: num_players DROPPED (constant n_distinct=1 in this scope)
    m.patch,
    -- DS-AOESTATS-04: raw_match_type DROPPED (n_distinct=1 in non-NULL filtered scope; redundant with upstream filter)
    m.replay_enhanced,

    -- ELO (DS-AOESTATS-03: avg_elo NULLIF applied)
    NULLIF(m.avg_elo, 0) AS avg_elo,
    -- DS-AOESTATS-01: team_0_elo / team_1_elo RETAIN_AS_IS (sentinel=-1 absent in this scope per F1 override)
    m.team_0_elo,
    m.team_1_elo,

    -- Player 0 (DS-AOESTATS-02: NULLIF + is_unrated indicator)
    CAST(p0.profile_id AS BIGINT) AS p0_profile_id,
    p0.civ AS p0_civ,
    NULLIF(p0.old_rating, 0) AS p0_old_rating,
    (p0.old_rating = 0) AS p0_is_unrated,
    p0.winner AS p0_winner,

    -- Player 1 (DS-AOESTATS-02: symmetric NULLIF + is_unrated)
    CAST(p1.profile_id AS BIGINT) AS p1_profile_id,
    p1.civ AS p1_civ,
    NULLIF(p1.old_rating, 0) AS p1_old_rating,
    (p1.old_rating = 0) AS p1_is_unrated,
    p1.winner AS p1_winner,

    -- TARGET (DS-AOESTATS-05: RETAIN_AS_IS, F1 override)
    -- WARNING (I5): p0=team=0, p1=team=1. team=1 wins ~52.27% (slot asymmetry from 01_04_01).
    -- Phase 02 feature engineering MUST randomise focal/opponent assignment before training.
    p1.winner AS team1_wins
FROM ranked_1v1 r
INNER JOIN matches_raw m ON m.game_id = r.game_id
INNER JOIN p0 ON p0.game_id = r.game_id
INNER JOIN p1 ON p1.game_id = r.game_id
WHERE p0.winner != p1.winner;
```

**Final column list (20):** `game_id`, `started_timestamp`, `map`, `mirror`, `patch`, `replay_enhanced`, `avg_elo`, `team_0_elo`, `team_1_elo`, `p0_profile_id`, `p0_civ`, `p0_old_rating`, `p0_is_unrated`, `p0_winner`, `p1_profile_id`, `p1_civ`, `p1_old_rating`, `p1_is_unrated`, `p1_winner`, `team1_wins`.

**Forbidden columns (must be absent — assertion battery 3.3a/b):** `leaderboard`, `num_players`, `raw_match_type`, `new_rating`, `p0_new_rating`, `p1_new_rating`, `duration`, `irl_duration`, `match_rating_diff`, `p0_match_rating_diff`, `p1_match_rating_diff`, `game_type`, `game_speed`, `starting_age`, `p0_opening`, `p1_opening`, `p0_feudal_age_uptime`, `p1_feudal_age_uptime`, `p0_castle_age_uptime`, `p1_castle_age_uptime`, `p0_imperial_age_uptime`, `p1_imperial_age_uptime`.

### 2.2 `player_history_all` — final 14-column DDL

```sql
CREATE OR REPLACE VIEW player_history_all AS
-- Purpose: Player feature history VIEW. ALL game types and ALL leaderboards.
-- Row multiplicity: 1 row per player per match (107,626,399 rows pre/post).
-- Column set: 14 columns (was 13; +1 is_unrated indicator from DS-AOESTATS-02).
-- Changes from 01_04_01: old_rating NULLIF; +is_unrated; leaderboard/player_count RETAINED
--   (only constant in matches_1v1_clean, not here).
WITH player_counts AS (
    SELECT game_id, COUNT(*) AS player_count
    FROM players_raw
    GROUP BY game_id
)
SELECT
    -- IDENTITY
    CAST(p.profile_id AS BIGINT) AS profile_id,
    p.game_id,
    m.started_timestamp,

    -- CONTEXT (NOT constant in player_history_all — covers all leaderboards/team-sizes)
    m.leaderboard,
    m.map,
    m.patch,
    pc.player_count,
    m.mirror,
    m.replay_enhanced,
    p.civ,
    p.team,

    -- PRE_GAME rating (DS-AOESTATS-02: NULLIF + is_unrated indicator)
    NULLIF(p.old_rating, 0) AS old_rating,
    (p.old_rating = 0) AS is_unrated,

    -- TARGET (DS-AOESTATS-06: RETAIN_AS_IS, F1 override)
    p.winner
FROM players_raw p
INNER JOIN matches_raw m ON p.game_id = m.game_id
INNER JOIN player_counts pc ON p.game_id = pc.game_id
WHERE p.profile_id IS NOT NULL
  AND m.started_timestamp IS NOT NULL;
```

**Final column list (14):** `profile_id`, `game_id`, `started_timestamp`, `leaderboard`, `map`, `patch`, `player_count`, `mirror`, `replay_enhanced`, `civ`, `team`, `old_rating`, `is_unrated`, `winner`.

### 2.3 `ratings_clean` — NOT IN SCOPE

aoestats has no `ratings_raw` table (asserted in 01_04_01 line 442 — `ratings_raw_exists=0`). All ELO data lives in `players_raw.old_rating` and `matches_raw.team_0/1_elo + avg_elo`. No third VIEW to modify.

### 2.4 `matches_long_raw` — NOT MODIFIED

Per 01_04_00 ROADMAP step (lines 681-728), `matches_long_raw` is the canonical 10-column long-skeleton VIEW from `01_04_00`. It is upstream of 01_04_01/02 cleaning and remains unchanged. Documented as Out of Scope.

## Section 3 — Post-cleaning validation (assertion battery)

Mirroring sc2egset 01_04_02 §3 structure with aoestats-specific differences. All assertions execute via DuckDB SQL embedded in the notebook; SQL strings stored verbatim in artifact JSON `sql_queries` block (Invariant I6).

### 3.1 Zero-NULL identity assertions

```sql
-- matches_1v1_clean: all upstream-asserted zero-NULL cols
SELECT
    COUNT(*) FILTER (WHERE game_id IS NULL) AS null_game_id,
    COUNT(*) FILTER (WHERE started_timestamp IS NULL) AS null_started_timestamp,
    COUNT(*) FILTER (WHERE p0_profile_id IS NULL) AS null_p0_profile_id,
    COUNT(*) FILTER (WHERE p1_profile_id IS NULL) AS null_p1_profile_id,
    COUNT(*) FILTER (WHERE p0_winner IS NULL) AS null_p0_winner,
    COUNT(*) FILTER (WHERE p1_winner IS NULL) AS null_p1_winner,
    COUNT(*) FILTER (WHERE team1_wins IS NULL) AS null_team1_wins
FROM matches_1v1_clean;
-- Expected: all = 0

-- player_history_all
SELECT
    COUNT(*) FILTER (WHERE profile_id IS NULL) AS null_profile_id,
    COUNT(*) FILTER (WHERE game_id IS NULL) AS null_game_id,
    COUNT(*) FILTER (WHERE started_timestamp IS NULL) AS null_started_timestamp,
    COUNT(*) FILTER (WHERE winner IS NULL) AS null_winner
FROM player_history_all;
-- Expected: all = 0
```

### 3.2 No symmetry assertion analog (CRITICAL ASYMMETRY)

**Aoestats `matches_1v1_clean` is 1-row-per-match** (not 2-per-replay like sc2egset `matches_flat_clean`). The sc2egset I5 symmetry assertion (`COUNT(*) FILTER WHERE result='Win' = 1 AND COUNT(*) FILTER WHERE result='Loss' = 1`) does NOT apply.

**Aoestats analog (target consistency):**

```sql
-- Verify 1-row-per-match invariant (no duplicates)
SELECT COUNT(*) AS dup_match_count
FROM (
    SELECT game_id, COUNT(*) AS n
    FROM matches_1v1_clean
    GROUP BY game_id
    HAVING n > 1
) d;
-- Expected: 0

-- Verify p0_winner XOR p1_winner consistency (re-assert post-DDL)
SELECT
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE p0_winner = TRUE AND p1_winner = FALSE) AS p0_wins,
    COUNT(*) FILTER (WHERE p0_winner = FALSE AND p1_winner = TRUE) AS p1_wins,
    COUNT(*) FILTER (WHERE p0_winner = p1_winner) AS inconsistent,
    COUNT(*) FILTER (WHERE team1_wins != p1_winner) AS team1_wins_inconsistent
FROM matches_1v1_clean;
-- Expected: inconsistent=0, team1_wins_inconsistent=0, p0_wins + p1_wins = total
```

### 3.3 Forbidden-column assertions

**3.3a Newly-dropped in 01_04_02 — assert absent from `matches_1v1_clean`:**
- `leaderboard` (DS-AOESTATS-08)
- `num_players` (DS-AOESTATS-08)
- `raw_match_type` (DS-AOESTATS-04)

**3.3b Pre-existing exclusions (still absent — re-assert from prior PRs):**
- `new_rating`, `p0_new_rating`, `p1_new_rating` (POST-GAME, I3)
- `duration`, `irl_duration` (POST-GAME, I3)
- `p0_match_rating_diff`, `p1_match_rating_diff`, `match_rating_diff` (POST-GAME, I3)
- `p0_opening`, `p1_opening` (IN-GAME, I3)
- `p0_feudal_age_uptime`, `p1_feudal_age_uptime`, `p0_castle_age_uptime`, `p1_castle_age_uptime`, `p0_imperial_age_uptime`, `p1_imperial_age_uptime` (IN-GAME, I3)
- `game_type`, `game_speed`, `starting_age` (constant/near-dead from 01_04_01)

**3.3c `player_history_all` retained columns (`leaderboard`, `player_count`) — assert PRESENT.** These were dropped from `matches_1v1_clean` (constants in that scope) but are NOT constants in `player_history_all` and must be retained.

### 3.4 New-column assertions (Section 3.4 from sc2egset template)

```sql
-- p0_is_unrated, p1_is_unrated, is_unrated all BOOLEAN
-- Plus team1_wins type assertion (NOTE-3 critique fix: explicit BOOLEAN
-- assertion catches any executor mistake of writing the schema YAML with
-- wrong type for the prediction target).
SELECT column_name, data_type
FROM information_schema.columns
WHERE (table_name = 'matches_1v1_clean' AND column_name IN ('p0_is_unrated', 'p1_is_unrated', 'team1_wins'))
   OR (table_name = 'player_history_all' AND column_name = 'is_unrated');
-- Expected: 4 rows, all data_type='BOOLEAN'
--   matches_1v1_clean.p0_is_unrated     BOOLEAN
--   matches_1v1_clean.p1_is_unrated     BOOLEAN
--   matches_1v1_clean.team1_wins        BOOLEAN  (target — derived from p1.winner)
--   player_history_all.is_unrated       BOOLEAN
```

### 3.5 No-new-NULLs assertions

For each KEPT column in either VIEW with `n_null=0` per the 01_04_01 ledger, re-assert `n_null=0` post-DDL. Implementation iterates the loaded ledger CSV (per I7) and emits one batched SQL per VIEW.

**Documented exceptions (NEW NULLs are EXPECTED, not violations):**
- `matches_1v1_clean.avg_elo`: expect ~118 new NULLs (NULLIF effect, DS-AOESTATS-03).
- `matches_1v1_clean.p0_old_rating`: expect ~4,730 new NULLs (NULLIF effect, DS-AOESTATS-02).
- `matches_1v1_clean.p1_old_rating`: expect ~188 new NULLs (NULLIF effect, DS-AOESTATS-02).
- `player_history_all.old_rating`: expect ~5,937 new NULLs (NULLIF effect, DS-AOESTATS-02).

### 3.6 NULLIF effect assertions (Section 3 / DS-AOESTATS-02, -03)

```sql
-- matches_1v1_clean: NULLIF on p0_old_rating + is_unrated consistency
SELECT
    COUNT(*) FILTER (WHERE p0_old_rating IS NULL) AS p0_or_null_after,
    COUNT(*) FILTER (WHERE p0_is_unrated = TRUE) AS p0_unrated_flag,
    COUNT(*) FILTER (WHERE p0_is_unrated = FALSE AND p0_old_rating IS NULL) AS p0_inconsistent,
    COUNT(*) FILTER (WHERE p1_old_rating IS NULL) AS p1_or_null_after,
    COUNT(*) FILTER (WHERE p1_is_unrated = TRUE) AS p1_unrated_flag,
    COUNT(*) FILTER (WHERE p1_is_unrated = FALSE AND p1_old_rating IS NULL) AS p1_inconsistent,
    COUNT(*) FILTER (WHERE avg_elo IS NULL) AS avg_elo_null_after
FROM matches_1v1_clean;
-- WARNING-3 critique fix: expected counts are loaded from the 01_04_01
-- ledger CSV at runtime per Invariant I7 — DO NOT hardcode literals here.
-- Sample ledger-derived expectations (placeholders only — values come from
-- ledger row 16/20/11 at notebook runtime):
--   p0_or_null_after  = expected_p0_unrated  (loaded from ledger row 16: matches_1v1_clean.p0_old_rating.n_sentinel)
--   p0_unrated_flag   = expected_p0_unrated  (same source — these MUST be equal post-NULLIF)
--   p0_inconsistent   = 0                     (consistency invariant)
--   p1_or_null_after  = expected_p1_unrated  (loaded from ledger row 20)
--   p1_unrated_flag   = expected_p1_unrated  (same)
--   p1_inconsistent   = 0
--   avg_elo_null_after = expected_avg_elo_sentinel  (loaded from ledger row 11)

-- player_history_all
SELECT
    COUNT(*) FILTER (WHERE old_rating IS NULL) AS or_null_after,
    COUNT(*) FILTER (WHERE is_unrated = TRUE) AS unrated_flag,
    COUNT(*) FILTER (WHERE is_unrated = FALSE AND old_rating IS NULL) AS inconsistent
FROM player_history_all;
-- Expected: or_null_after = expected_unrated  (loaded from ledger row 34: player_history_all.old_rating.n_sentinel)
--           unrated_flag  = expected_unrated  (same)
--           inconsistent  = 0
```

### 3.7 CONSORT column-count flow (Section 3.7 from sc2egset)

| VIEW | Cols before | Cols dropped | Cols added | Cols modified | Cols after |
|---|---|---|---|---|---|
| matches_1v1_clean | 21 | 3 | 2 | 3 (avg_elo, p0_old_rating, p1_old_rating NULLIF) | 20 |
| player_history_all | 13 | 0 | 1 | 1 (old_rating NULLIF) | 14 |

### 3.8 CONSORT row-count flow (column-only step)

| Stage | matches_1v1_clean rows | matches_1v1_clean game_ids | player_history_all rows | player_history_all profile_ids |
|---|---|---|---|---|
| Before 01_04_02 (post 01_04_01) | 17,814,947 | 17,814,947 | 107,626,399 | (variable; not asserted) |
| After 01_04_02 column-only changes | 17,814,947 | 17,814,947 | 107,626,399 | (unchanged) |

### 3.9 Subgroup impact summary (Jeanselme et al. 2024)

| Affected column | Source decision | Subgroup most affected (computed at runtime) | Impact |
|---|---|---|---|
| `leaderboard` (dropped from matches_1v1_clean) | DS-AOESTATS-08 | Constant in scope — none affected | Information neutral (n_distinct=1) |
| `num_players` (dropped from matches_1v1_clean) | DS-AOESTATS-08 | Constant in scope — none affected | Information neutral (n_distinct=1) |
| `raw_match_type` (dropped from matches_1v1_clean) | DS-AOESTATS-04 | n_distinct=1 in non-NULL filtered scope | Information neutral; 7,055 NULL rows still in VIEW |
| `p0_old_rating` NULLIF + is_unrated | DS-AOESTATS-02 | Unrated-team0 players (4,730 of 17.8M = 0.027%) | Sentinel→NULL converts 0-rating to missing-rating; flag preserves rated/unrated signal |
| `p1_old_rating` NULLIF + is_unrated | DS-AOESTATS-02 | Unrated-team1 players (188 of 17.8M = 0.001%) | Same as p0 |
| `old_rating` NULLIF + is_unrated (player_history_all) | DS-AOESTATS-02 | Unrated-player rows (5,937 of 107.6M = 0.0055%) | Same |
| `avg_elo` NULLIF | DS-AOESTATS-03 | Matches with at least one unrated player (118 of 17.8M = 0.0007%) | Sentinel→NULL eliminates 0-skew in averaging operations |

### 3.10 Cleaning registry update (Section 3.8 in sc2egset)

| Rule ID | Condition | Action | Justification | Impact |
|---|---|---|---|---|
| `drop_matches_1v1_clean_constants` | n_distinct=1 in matches_1v1_clean | DROP `leaderboard`, `num_players` from matches_1v1_clean | DS-AOESTATS-08: ledger constants-detection; zero info | -2 cols matches_1v1_clean |
| `drop_raw_match_type_redundant` | n_distinct=1 in non-NULL filtered scope of matches_1v1_clean | DROP `raw_match_type` from matches_1v1_clean | DS-AOESTATS-04: redundant with upstream `leaderboard='random_map'` + `COUNT(*)=2` filters | -1 col matches_1v1_clean |
| `nullif_old_rating_indicator` | `old_rating = 0` in either VIEW | NULLIF + ADD `is_unrated` flag | DS-AOESTATS-02: low-rate sentinel-with-semantic-content; missingness-as-signal pattern (sklearn MissingIndicator) | matches_1v1_clean: -0 / +2 / 2 modified; player_history_all: -0 / +1 / 1 modified |
| `nullif_avg_elo` | `avg_elo = 0` in matches_1v1_clean | NULLIF | DS-AOESTATS-03: low-rate sentinel; semantic content covered by p0/p1_is_unrated | 1 modified, 0 added |
| `declare_overviews_oos` | Always (documentation) | OVERVIEWS_RAW formally declared out-of-analytical-scope | DS-AOESTATS-07: singleton metadata, not used by any VIEW | None (registry-only) |

## Section 4 — New ROADMAP step entry for 01_04_02

Mirror the sc2egset 01_04_02 step block (sc2egset ROADMAP.md lines 999-1115) structure with aoestats-specific contents. The full block to be inserted in `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` immediately after the 01_04_01 step block (after line 939, before the `## Phase 02` placeholder header on line 945).

**WARNING-4 critique fix — fence guidance for executor:** The block below begins with the `### Step 01_04_02 -- Data Cleaning Execution` markdown header on its own line, then a YAML code-fenced block. The plan's outer ` ```yaml ... ``` ` is a plan-typography container ONLY. When pasting into ROADMAP.md, copy from the `### Step 01_04_02` heading through the closing ` ``` ` of the YAML block — do NOT include the plan's outer fence wrapper. The sc2egset 01_04_02 ROADMAP step block is the exact format reference.

```yaml
### Step 01_04_02 -- Data Cleaning Execution

```yaml
step_number: "01_04_02"
name: "Data Cleaning Execution -- Act on DS-AOESTATS-01..08"
description: >
  Acts on the 8 cleaning decisions surfaced by 01_04_01. Modifies VIEW DDL
  for matches_1v1_clean and player_history_all (no raw table changes per
  Invariant I9): drops leaderboard + num_players (DS-AOESTATS-08 constants),
  drops raw_match_type (DS-AOESTATS-04 redundant), applies NULLIF on
  p0/p1/avg_elo + old_rating (DS-AOESTATS-02/03) plus 3 new is_unrated
  indicator flags. Documents DS-AOESTATS-01 (sentinel ABSENT in 1v1 scope,
  RETAIN_AS_IS with scope-expansion contingency), DS-AOESTATS-05/06 (zero
  NULLs verified), DS-AOESTATS-07 (overviews_raw out-of-analytical-scope).
  Reports CONSORT-style column-count flow + subgroup impact + post-cleaning
  invariant re-validation.
phase: "01 -- Data Exploration"
pipeline_section: "01_04 -- Data Cleaning"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 4"
dataset: "aoestats"
question: >
  Which of the 8 decisions surfaced by 01_04_01 (DS-AOESTATS-01..08) are
  resolved by DDL modifications, what is the column-count and subgroup
  impact, and do all post-cleaning invariants still hold?
method: >
  Modify CREATE OR REPLACE VIEW DDL for matches_1v1_clean and
  player_history_all per per-DS resolutions (see plan Section 1). Apply
  column drops, NULLIF transformations, and 3 new derived is_unrated
  indicator columns. Re-run the assertion battery from 01_04_01 plus
  01_04_02-specific assertions on the new column set. Produce a
  CONSORT-style column-count table and per-DS resolution log.
stratification: "By VIEW (matches_1v1_clean vs player_history_all) and by DS-AOESTATS-NN."
predecessors:
  - "01_04_01"
methodology_citations:
  - "Manual 01_DATA_EXPLORATION_MANUAL.md §4.1 (cleaning registry), §4.2 (non-destructive), §4.3 (CONSORT impact), §4.4 (post-validation)"
  - "Liu, X. et al. (2020). CONSORT-AI extension. BMJ, 370."
  - "Jeanselme, V. et al. (2024). Participant Flow Diagrams for Health Equity in AI. JBI, 152."
  - "Schafer, J.L. & Graham, J.W. (2002). Missing data: Our view of the state of the art. Psych Methods, 7(2)."
  - "van Buuren, S. (2018). Flexible Imputation of Missing Data, 2nd ed. CRC Press."
  - "Sambasivan, N. et al. (2021). Data Cascades in High-Stakes AI. CHI '21."
notebook_path: "sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py"
inputs:
  duckdb_views:
    - "matches_1v1_clean (17,814,947 rows / 21 cols -- pre-01_04_02)"
    - "player_history_all (107,626,399 rows / 13 cols -- pre-01_04_02)"
  prior_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json (cleaning_registry, missingness_audit, consort_flow)"
    - "artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv (34 rows, per-DS empirical evidence)"
    - "artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md (decisions_surfaced reference)"
  schema_yamls:
    - "data/db/schemas/views/player_history_all.yaml (current -- to be UPDATED)"
outputs:
  duckdb_views:
    - "matches_1v1_clean (replaced via CREATE OR REPLACE -- 20 cols, 17,814,947 rows)"
    - "player_history_all (replaced via CREATE OR REPLACE -- 14 cols, 107,626,399 rows)"
  schema_yamls:
    - "data/db/schemas/views/matches_1v1_clean.yaml (NEW)"
    - "data/db/schemas/views/player_history_all.yaml (UPDATED)"
  data_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.json"
  report: "artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.md"
reproducibility: >
  Code and output in the paired notebook. All DDL stored verbatim in the
  validation JSON sql_queries block (Invariant I6). All thresholds derived
  from the 01_04_01 ledger CSV at runtime (Invariant I7). Re-runs deterministically.
scientific_invariants_applied:
  - number: "3"
    how_upheld: >
      No new feature computation. matches_1v1_clean retains only PRE_GAME
      + IDENTITY + TARGET columns. player_history_all retains PRE_GAME
      and CONTEXT columns (old_rating PRE_GAME-safe; no IN-GAME or
      POST-GAME columns introduced).
  - number: "5"
    how_upheld: >
      Player-slot symmetry warning preserved as DDL comment (team=1 wins
      ~52.27% per 01_04_01 t1_win_pct finding); the p0/p1 columns are
      symmetrically modified (NULLIF + is_unrated applied to both slots
      identically). Phase 02 must randomise focal/opponent assignment.
  - number: "6"
    how_upheld: >
      All DDL queries stored verbatim in JSON sql_queries. All assertion
      SQL stored verbatim. All per-DS rationale references the ledger row
      + ledger recommendation_justification by view+column.
  - number: "7"
    how_upheld: >
      Thresholds (5/40/80%) come from the 01_04_01 framework block
      (Schafer & Graham 2002 boundary; van Buuren 2018 warning). Per-DS
      empirical evidence (n_sentinel, pct_missing_total, n_distinct) is
      read from the 01_04_01 ledger CSV at runtime, not hardcoded.
  - number: "9"
    how_upheld: >
      No raw tables modified. matches_long_raw (canonical skeleton from
      01_04_00) unmodified. Only matches_1v1_clean and player_history_all
      VIEWs are replaced via CREATE OR REPLACE. All inputs are 01_04_01
      artifacts (predecessor) or this step's own DDL output.
  - number: "10"
    how_upheld: >
      No filename derivation changes. The aoestats raw tables already
      satisfy I10 from 01_02_02 ingestion.
gate:
  artifact_check: >
    artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.json
    and .md exist and are non-empty. Both schema YAMLs
    (matches_1v1_clean.yaml NEW, player_history_all.yaml UPDATED) exist
    with correct column counts.
  continue_predicate: >
    matches_1v1_clean has exactly 20 columns. player_history_all has
    exactly 14 columns. All zero-NULL assertions pass (game_id,
    started_timestamp, p0/p1_profile_id, p0/p1_winner, team1_wins in
    matches_1v1_clean; profile_id, game_id, started_timestamp, winner in
    player_history_all). Forbidden columns absent (DS-AOESTATS-04/-08
    drops + I3 pre-existing exclusions). NULLIF effects match ledger-derived
    expected_p0_unrated / expected_p1_unrated / expected_avg_elo_sentinel /
    expected_unrated values within ±1 row (loaded at runtime per I7).
    is_unrated indicator counts equal NULLIF NULL counts (consistency).
    Row counts unchanged. CONSORT
    column-count table reproduces drop counts per DS-AOESTATS-01..08.
    STEP_STATUS.yaml has 01_04_02: complete. PIPELINE_SECTION_STATUS for
    01_04 transitions to complete (no further 01_04_NN steps defined in
    ROADMAP).
  halt_predicate: >
    Any zero-NULL assertion fails; any inconsistent winner row appears;
    any forbidden column appears; any expected NEW column missing; column
    count off by even one from spec; NULLIF count diverges from ledger
    by more than ±1 row.
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.2 AoE2 Match Data > Data Cleaning Decisions"
research_log_entry: "Required on completion."
```

## Section 5 — Notebook + cell structure

Sandbox notebook path: `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py` (jupytext-paired with `.ipynb`).

Estimated **27 cells** (one cell less than sc2egset's 28 because aoestats has no `is_decisive_result` analog → one fewer cell needed for the decisive-distribution assertion). Mirrors the sc2egset structure cell-for-cell where applicable.

| Cell | Type | Content |
|---|---|---|
| 1 | markdown | Header: Step 01_04_02; Phase / Pipeline Section / Dataset / Step scope / Invariants applied (I3, I5, I6, I7, I9, I10) / Predecessor / Date / ROADMAP ref |
| 2 | code | Imports: `json`, `pathlib.Path`, `numpy`, `pandas`, `yaml`; `from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir, setup_notebook_logging`; logger init |
| 3 | code | DuckDB connection (writable): `db = get_notebook_db("aoe2", "aoestats", read_only=False); con = db.con` |
| 4 | code | Load 01_04_01 ledger CSV via `pd.read_csv(...)`, print row count + column list, extract empirical sentinel rates per DS at runtime (I7 verification) |
| 5 | code | Per-DS resolution log — list of 8 dict entries (DS-AOESTATS-01..08), each with `id`, `column`, `views`, `ledger_rate` (formatted from runtime ledger), `recommendation`, `decision`, `ddl_effect` |
| 6 | code | Pre-cleaning column counts: `DESCRIBE matches_1v1_clean`, `DESCRIBE player_history_all`; assert pre-state (21 / 13) |
| 7 | code | Pre-cleaning row counts: `SELECT COUNT(*)`, `SELECT COUNT(DISTINCT game_id)`; assert canonical 17,814,947 / 107,626,399 |
| 8 | markdown | Define matches_1v1_clean v2 DDL — comment block listing the changes |
| 9 | code | `CREATE_MATCHES_1V1_CLEAN_V2_SQL` constant defined (DDL from Section 2.1 of this plan) |
| 10 | code | `con.execute(CREATE_MATCHES_1V1_CLEAN_V2_SQL)` |
| 11 | markdown | Define player_history_all v2 DDL |
| 12 | code | `CREATE_PLAYER_HISTORY_ALL_V2_SQL` constant defined (DDL from Section 2.2 of this plan) |
| 13 | code | `con.execute(CREATE_PLAYER_HISTORY_ALL_V2_SQL)` |
| 14 | code | Post-cleaning column counts: assert 20 / 14 |
| 15 | code | Forbidden-column assertions (3.3a + 3.3b) — `forbidden_clean_new` set ∩ post_clean_cols must be empty; same for prior I3 exclusions |
| 16 | code | New-column assertions (3.4): `p0_is_unrated`, `p1_is_unrated` BOOLEAN in matches_1v1_clean; `is_unrated` BOOLEAN in player_history_all |
| 17 | code | Zero-NULL identity assertions (3.1): two batched SELECT statements |
| 18 | code | Target consistency assertion (3.2 aoestats analog): no duplicate game_id; p0_winner XOR p1_winner; team1_wins = p1_winner |
| 19 | code | No-new-NULLs assertion (3.5): iterate ledger CSV for each kept-zero-null col, batch SQL per VIEW, exclude documented NULLIF columns |
| 20 | code | NULLIF effect + is_unrated consistency assertions (3.6): one batched SELECT per VIEW; counts loaded from ledger at runtime |
| 21 | code | Post-cleaning row counts: assert unchanged from pre-state |
| 22 | code | Subgroup impact summary (3.9): build list of dicts with runtime-computed counts |
| 23 | code | Cleaning registry (3.10): list of 5 new rule dicts |
| 24 | code | Build and write artifact JSON (`01_04_02_post_cleaning_validation.json`) — `validation_artifact` dict with `cleaning_registry`, `consort_flow_columns`, `consort_flow_replays`, `subgroup_impact`, `validation_assertions`, `sql_queries`, `decisions_resolved`, `all_assertions_pass` boolean. Raise AssertionError on `not all_pass`. |
| 25 | code | Build and write markdown report (`01_04_02_post_cleaning_validation.md`): summary, per-DS table, cleaning registry table, CONSORT column + row tables, subgroup impact table, validation results table, SQL queries pointer |
| 26 | code | Update `player_history_all.yaml` schema YAML — keep prose-format `notes:` vocabulary (per Open Question recommendation); update column list to 14; add `is_unrated`; modify `old_rating` description to mention NULLIF; update `excluded_columns` block; bump `step` to "01_04_02"; populate `row_count`; update invariants block (carry I3 / I5 / I6 / I9 / I10 — keep existing prose-style descriptions). NO `provenance_categories` enumeration (single-token vocabulary deferred to CROSS PR). |
| 27 | code | Create `matches_1v1_clean.yaml` schema YAML (NEW) — mirror `player_history_all.yaml` flat-list shape with prose-format `notes:` vocabulary. 20 column entries with type, nullable, description, prose `notes:`. Provenance block (source_tables = `[matches_raw, players_raw]`; filter = ranked-1v1 CTE; scope = "Ranked 1v1 decisive matches only"). Invariants block (I3 / I5 / I6 / I9 / I10) using prose-style descriptions matching the existing aoestats YAML convention. NOTE: the I3 description includes a brief inline enumeration of provenance tags (e.g., `"PRE_GAME columns: ...; CONTEXT columns: ...; TARGET column: team1_wins"`) but does NOT use the sc2egset-style YAML `provenance_categories:` mapping. The CROSS PR after all 3 datasets land will harmonize. |
| 28 | code | Close DuckDB connection (`db.close()`); print final summary listing CONSORT flow, all assertion results, gate-predicate readiness for STEP_STATUS / PIPELINE_SECTION_STATUS / ROADMAP updates (these last three are PENDING — handled by parent post-execution per established two-session workflow). |

**Note on cell count:** Sc2egset has 28 cells; aoestats has 27 (one fewer — no `is_decisive_result` distribution assertion needed). The matches/sc2egset 1:1 cell-by-cell mapping is preserved everywhere else.

## Section 6 — STEP_STATUS / PIPELINE_SECTION_STATUS / PHASE_STATUS update

After the executor runs the notebook and validates artifacts:

1. **STEP_STATUS.yaml** — append entry for `01_04_02`:

```yaml
  "01_04_02":
    name: "Data Cleaning Execution -- Act on DS-AOESTATS-01..08"
    pipeline_section: "01_04"
    status: complete
    completed_at: "2026-04-XX"  # date of execution
```

2. **PIPELINE_SECTION_STATUS.yaml** — bump `01_04` from `in_progress` → `complete`. **Per WARNING-5 / NOTE-2 lesson from sc2egset round 3:** before bumping, run `grep -n "01_04_" /Users/tomaszpionka/Projects/rts-outcome-prediction/src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` to confirm there are no `01_04_03+` step blocks pre-listed. If a future-step entry exists, the bump is invalid and PIPELINE_SECTION_STATUS must remain `in_progress`. Current state at planning time: only `01_04_00` and `01_04_01` exist in ROADMAP — bump WILL be valid after 01_04_02 is added in T05 and completed.

3. **PHASE_STATUS.yaml** — Phase `01` remains `in_progress` (because `01_05`, `01_06` are still `not_started`). No bump.

## File Manifest

**Files this PR WRITES (executor will touch all of these):**

| File | Operation | Purpose |
|---|---|---|
| `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py` | CREATE | Sandbox notebook (jupytext .py paired) |
| `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.ipynb` | CREATE | jupytext-generated paired ipynb |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.json` | CREATE | Validation JSON artifact (cleaning_registry, CONSORT flow, validation_assertions, sql_queries) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.md` | CREATE | Validation markdown report |
| `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_1v1_clean.yaml` | CREATE | Schema YAML for matches_1v1_clean (20 cols + invariants block, prose-format notes) |
| `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/player_history_all.yaml` | UPDATE | Bump step → 01_04_02; +1 col (is_unrated); modify old_rating description; update excluded_columns + invariants block |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/ROADMAP.md` | UPDATE | Append 01_04_02 step block (Section 4 above) after the 01_04_01 step block (after line 939) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/STEP_STATUS.yaml` | UPDATE | Append `01_04_02: complete` entry |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/PIPELINE_SECTION_STATUS.yaml` | UPDATE | Bump `01_04` `in_progress` → `complete` (after grep check for 01_04_03+) |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md` | UPDATE | New top entry: 2026-04-XX — [Phase 01 / Step 01_04_02] Data Cleaning Execution; ledger evidence cited; per-DS resolutions enumerated |
| `CHANGELOG.md` | UPDATE | New entry under `[Unreleased]`: `### Added` (matches_1v1_clean.yaml; 01_04_02 artifacts), `### Changed` (player_history_all VIEW DDL — NULLIF + is_unrated; player_history_all.yaml updated; matches_1v1_clean VIEW DDL — drops + NULLIF + is_unrated). |

**Files this PR READS but DOES NOT modify:**

- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json`
- `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/matches_long_raw.yaml`
- `.claude/scientific-invariants.md`
- `docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md` §4
- `docs/PHASES.md`
- `docs/templates/duckdb_schema_template.yaml`

## Gate Condition

**ALL of the following MUST hold for 01_04_02 to be marked `complete`:**

1. `01_04_02_post_cleaning_validation.json` and `.md` exist under `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/` and are non-empty.
2. `matches_1v1_clean.yaml` exists at `src/rts_predict/games/aoe2/datasets/aoestats/data/db/schemas/views/` (NEW) with 20 column entries + populated `row_count` + invariants block.
3. `player_history_all.yaml` UPDATED with 14 column entries + populated `row_count` + `is_unrated` entry + modified `old_rating` description.
4. `con.execute("DESCRIBE matches_1v1_clean").df()` returns exactly 20 rows (after notebook execution).
5. `con.execute("DESCRIBE player_history_all").df()` returns exactly 14 rows.
6. All zero-NULL assertions PASS (Section 3.1).
7. All forbidden-column assertions PASS (Section 3.3a + 3.3b).
8. All new-column assertions PASS (Section 3.4): 3 new BOOLEAN columns present.
9. NULLIF effect counts MATCH ledger-derived expected values within ±1 row (Section 3.6): `p0_old_rating IS NULL` count = expected_p0_unrated (ledger row 16); `p1_old_rating IS NULL` count = expected_p1_unrated (ledger row 20); `avg_elo IS NULL` count = expected_avg_elo_sentinel (ledger row 11); `old_rating IS NULL` (player_history_all) = expected_unrated (ledger row 34). All loaded at runtime per Invariant I7.
10. is_unrated indicator counts EQUAL NULLIF NULL counts (consistency).
11. Row counts UNCHANGED: `matches_1v1_clean.COUNT(*) = 17,814,947`; `player_history_all.COUNT(*) = 107,626,399`.
12. CONSORT column-count table in artifact JSON reproduces drop counts: matches_1v1_clean (21→20; -3 +2); player_history_all (13→14; -0 +1 +1 modified).
13. `STEP_STATUS.yaml` has `01_04_02: complete`.
14. `PIPELINE_SECTION_STATUS.yaml` has `01_04: complete` (after grep verification).
15. ROADMAP `01_04_02` step block present (Section 4).
16. `research_log.md` updated with 01_04_02 entry citing artifact paths + ledger row counts + per-DS resolutions.

**HALT predicates** (any one triggers immediate halt):

- Any zero-NULL identity assertion fails.
- Any inconsistent winner row (`p0_winner = p1_winner`) appears in `matches_1v1_clean`.
- Any forbidden column from Section 3.3 appears in either VIEW.
- Any expected new column (`p0_is_unrated`, `p1_is_unrated`, `is_unrated`) is missing.
- Column count off by even one from spec (20 / 14).
- NULLIF count diverges from ledger by more than ±1 row.
- `grep` discovers any `01_04_03+` step block in ROADMAP at status-bump time (forbidden state — bump is invalid).

## Out of scope

The following are explicitly **NOT** in this PR (each gets its own future PR):

1. **aoec (aoe2companion) 01_04_02.** Independent planning round + PR (per user task instructions).
2. **CROSS PR for `notes:` vocabulary harmonization.** Migrating aoestats / aoec from prose-format `notes:` to sc2egset's single-token + `provenance_categories:` enumeration is a cross-dataset I8 question. Defer to a CROSS PR that lands AFTER all three dataset 01_04_02 PRs are merged. This PR keeps aoestats's existing prose-format vocabulary unchanged.
3. **`matches_long_raw` modifications.** Canonical 10-column long-skeleton VIEW from 01_04_00 is upstream of cleaning and remains unchanged.
4. **Raw table modifications.** Per Invariant I9, `matches_raw`, `players_raw`, `overviews_raw` are immutable.
5. **Phase 02 imputation / encoding decisions.** This PR creates `is_unrated` indicator flags (the sklearn `MissingIndicator` pattern) but does NOT decide whether Phase 02 will use median/mean/k-NN/iterative imputation or simply listwise-delete unrated rows. That is a Phase 02 (Pipeline Section 02_02) decision.
6. **`raw_match_type` re-encoding.** This PR drops the column. If Phase 02 finds it unexpectedly informative (unlikely given `n_distinct=1` in scope), restoration is a future-step reversal and out of scope here.
7. **Updating sibling dataset cross-refs.** `reports/research_log.md` (CROSS-level) updates are out of scope; this PR updates only the aoestats-scoped `research_log.md`.
8. **Cross-dataset feature-engineering reconciliation.** Phase 02 entry-point work.
9. **`null_handling_recommendations.md`.** This file was a working-draft document used during 01_04_01 planning; it does not currently exist in the repo. The decision tree rules (S1-S6) are encoded inline in the 01_04_01 audit logic + the missingness ledger justification text. No new working-draft files created.
10. **`coverage.txt` regeneration.** This PR adds no new `.py` source code outside the sandbox notebook (which is excluded from coverage). pre-commit hooks (`ruff`, `mypy`) cover the notebook on commit.

## Open Questions

**STATUS: ALL 4 ANSWERED — RECOMMENDATIONS LOCKED.** User approved all 4 planner recommendations (Q1 NULLIF+flag, Q2 DROP_COLUMN, Q3 KEEP prose-format, Q4 runtime-computed) in chat before plan write. Preserved below as audit trail; no resolution pending.

Genuine judgement calls that require user confirmation BEFORE notebook execution:

### Q1 — DS-AOESTATS-02 (old_rating sentinel disposition)

**Pragmatic recommendation in this plan:** NULLIF + `is_unrated` indicator flag (3 new BOOLEAN cols across both VIEWs). Mirrors the sc2egset DS-SC2-10 pattern (APM NULLIF + `is_apm_unparseable`).

**Alternative:** Retain sentinel `0` as an explicit "unrated" categorical encoding (no NULLIF, no NULL semantics introduced). Phase 02 would treat `old_rating = 0` as a categorical level distinct from low ratings. Pros: simpler downstream; preserves single-column representation. Cons: breaks `IS NULL` semantics for sklearn `SimpleImputer`; conflates rating magnitude with categorical state in regression contexts.

**User decision required:** Approve NULLIF + is_unrated (recommended), or instruct to use the alternative?

### Q2 — DS-AOESTATS-04 (raw_match_type disposition)

**Pragmatic recommendation in this plan:** DROP_COLUMN (constants-detection rationale: `n_distinct=1` over non-NULL rows in the filtered scope; redundant with upstream `leaderboard='random_map'` + `COUNT(*)=2` filters).

**Alternative 1:** Retain via the ledger's RETAIN_AS_IS recommendation (rate < 5% MCAR boundary). Pros: defers the decision to Phase 02. Cons: keeps a column with zero information content in the analytical VIEW.

**Alternative 2:** Listwise-delete the 7,055 NULL rows (treating NULLs as MCAR per Schafer & Graham 2002). Pros: removes a small data-quality wart upstream. Cons: alters row count in 01_04_02 (column-only step expectation breaks), introduces a new CONSORT row-flow line, deviates from the sc2egset pattern.

**User decision required:** Approve DROP_COLUMN (recommended), retain, or listwise-delete?

### Q3 — Schema YAML `notes:` vocabulary (cross-dataset I8 question)

**Pragmatic recommendation in this plan:** KEEP existing aoestats prose-format `notes:` vocabulary unchanged in this PR (e.g., `notes: "TARGET. Used as prediction label..."`). Defer harmonization with sc2egset's single-token vocabulary (e.g., `notes: TARGET`) + `provenance_categories:` YAML mapping to a CROSS PR that lands AFTER all three dataset 01_04_02 PRs are merged.

**Rationale:** Per the round-3 v3-BLOCKER-1 lesson, do NOT change a per-dataset convention mid-PR — it would break I8 cross-game protocol mid-PR. The CROSS PR after all three datasets is the right place to align.

**User decision required:** Confirm KEEP existing prose-format vocabulary in this PR (recommended), or instruct to migrate now?

### Q4 — Subgroup-impact computation: lazy or strict?

**Pragmatic recommendation:** Compute subgroup counts at runtime in cell 22 from actual VIEW data (per I7 — no hardcoded constants), matching the sc2egset cell 20 pattern. The plan's Section 3.9 table shows expected ranges as labels but the notebook computes actual values.

**Alternative:** Hardcode expected counts from the ledger CSV (faster, but violates I7 if any drift occurs).

**User decision required:** Approve runtime-computed (recommended)?

---

## Critique gate notice

This is a **Category A** plan. Per the Plan/Execute Workflow protocol and `docs/templates/planner_output_contract.md`:

> For Category A or F, adversarial critique is required before execution begins. Dispatch reviewer-adversarial to produce `planning/current_plan.critique.md` covering all sections.

The user's pattern (per the task brief) is to approve quickly + run 3 strict adversarial rounds + execute. **Do NOT begin executor work on this plan until at least one adversarial-critique round has produced (and the planner has resolved) a `planning/current_plan.critique.md` file.**

---

## Self-check summary

- [x] `category: A` — Phase work / Pipeline Section 01_04 / Step 01_04_02
- [x] `branch: feat/01-04-02-aoestats` — current branch confirmed
- [x] `date: 2026-04-17`
- [x] `planner_model: claude-opus-4-7[1m]`
- [x] All 9 mandatory Cat A sections present: Scope, Problem Statement, Assumptions & unknowns, Literature context, Execution Steps (Sections 1-7), File Manifest (Section 7), Gate Condition (Section 8), Open Questions (Section 10), Out of scope (Section 9)
- [x] `source_artifacts` non-empty (frontmatter)
- [x] `invariants_touched` populated: I3, I5, I6, I7, I8, I9, I10
- [x] No forbidden taxonomy terms ("Stage", "Experiment" as work-unit, "Milestone", "Workstream", "Component" as work-unit, "Section" unqualified)
- [x] CRITICAL ASYMMETRY items #1-#7 from user task brief addressed: (1) target name `team1_wins` BOOLEAN (per ledger row 22 + DDL `p1.winner AS team1_wins`); (2) `notes:` vocabulary KEPT; (3) DS-AOESTATS-08 listed in resolution table; (4) DS-AOESTATS-01 sentinel-absent + DS-AOESTATS-02/03 NULLIF; (5) no `is_decisive_result` analog; (6) no APM analog; (7) no go_* analog.
- [x] Sandbox notebook path specified: `sandbox/aoe2/aoestats/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py`
- [x] Artifacts target specified: `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/04_cleaning/`
- [x] WARNING-5 / NOTE-2 lesson incorporated (grep ROADMAP for 01_04_03+ before PIPELINE_SECTION_STATUS bump)
- [x] Critique-gate instruction included at the end

---

## Notes on plan-mode compliance

I have NOT modified any files. The system reminder at the top of this turn instructed me to use the Write tool against `/Users/tomaszpionka/.claude/plans/shimmying-sauteeing-corbato-agent-a5e58eb670e145555.md` if a plan file was needed; however, the user's task brief (which is the primary instruction) explicitly states: **"DO NOT modify any files. Plan goes in chat."** I have respected the user's primary instruction and kept the entire plan in chat.

If you want me to also persist this plan to a file (either the system-reminder path or `planning/current_plan.md`), explicitly authorize it and I will do so. Otherwise the plan above is ready for your review and any clarifications, after which the parent session can write `planning/current_plan.md` and dispatch reviewer-adversarial.
