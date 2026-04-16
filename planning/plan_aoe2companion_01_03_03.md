---
category: A
branch: feat/table-utility-assessment
date: 2026-04-16
planner_model: claude-opus-4-6
dataset: aoe2companion
phase: "01"
pipeline_section: "01_03 -- Systematic Data Profiling"
invariants_touched: [I3, I6, I7, I9]
source_artifacts:
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/matches_raw.yaml
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/ratings_raw.yaml
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/leaderboards_raw.yaml
  - src/rts_predict/games/aoe2/datasets/aoe2companion/data/db/schemas/raw/profiles_raw.yaml
critique_required: true
research_log_ref: null
---

# Plan: aoe2companion 01_03_03 -- Table Utility Assessment

## Scope

Systematically evaluate all 4 raw tables (matches_raw, ratings_raw,
leaderboards_raw, profiles_raw) for prediction pipeline utility. Produce
per-table KEEP/DROP verdicts with empirical evidence, resolve the
matches_raw.rating AMBIGUOUS I3 classification, and define the pipeline
scope for 01_04.

## Problem Statement

aoe2companion has 4 raw tables of vastly different character. Two are time
series (matches_raw, ratings_raw) and two are singleton snapshots
(leaderboards_raw, profiles_raw). Singleton snapshots cannot safely
contribute pre-game features under I3 because their values reflect the
player's state at crawl time, not at match time. This step formalizes the
evidence and produces actionable verdicts before 01_04.

The `matches_raw.rating` column has been AMBIGUOUS since 01_02_04. This
step resolves it by cross-referencing with ratings_raw.

## Execution Steps

### T01 -- Investigate leaderboards_raw and profiles_raw (DROP candidates)

**Objective:** Produce empirical evidence for KEEP/DROP verdicts.

**Instructions:**

1. Create notebook `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_03_table_utility_assessment.py`.

2. **leaderboards_raw -- source file count:**
   ```sql
   SELECT COUNT(DISTINCT filename) AS n_files FROM leaderboards_raw
   ```
   Expected: 1 (singleton).

3. **leaderboards_raw -- temporal dimension:**
   ```sql
   SELECT MIN(updatedAt) AS min_updated, MAX(updatedAt) AS max_updated,
          COUNT(DISTINCT DATE_TRUNC('day', updatedAt)) AS distinct_days
   FROM leaderboards_raw
   ```

4. **leaderboards_raw -- staleness:**
   ```sql
   SELECT
       PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY
           EXTRACT(EPOCH FROM (updatedAt - lastMatchTime))) AS median_gap_secs,
       PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY
           EXTRACT(EPOCH FROM (updatedAt - lastMatchTime))) AS p95_gap_secs
   FROM leaderboards_raw
   WHERE lastMatchTime IS NOT NULL AND updatedAt IS NOT NULL
   ```

5. **leaderboards_raw -- player overlap:**
   Fraction of leaderboard players in matches_raw and vice versa.

6. **leaderboards_raw -- redundancy check:**
   Sample 10K matched rows (join on profileId), compare rating/country values.

7. **leaderboards_raw -- I3 verdict:** Singleton snapshot, no temporal
   attribution possible. Cumulative stats reflect crawl-time state.
   Verdict: DROP, I3 risk HIGH.

8. **profiles_raw -- dead columns:** Confirm 7 columns are 100% NULL.

9. **profiles_raw -- non-dead column inventory:** Which of the remaining 7
   are already in matches_raw? (Expected redundant: name, country)

10. **profiles_raw -- clan population:** % of players with non-empty clan.

11. **profiles_raw -- country redundancy:** Compare with matches_raw.country.

12. **profiles_raw -- I3 verdict:** Singleton snapshot. Non-dead columns
    either redundant or non-predictive. Verdict: DROP, I3 risk MODERATE.

---

### T02 -- Investigate ratings_raw and resolve matches_raw.rating

**Objective:** Produce evidence for ratings_raw KEEP verdict and resolve
the matches_raw.rating AMBIGUOUS classification.

**Instructions:**

1. **Time series verification:**
   ```sql
   WITH consecutive AS (
       SELECT profile_id, leaderboard_id, date, rating, rating_diff,
              LAG(rating) OVER (
                  PARTITION BY profile_id, leaderboard_id ORDER BY date
              ) AS prev_rating
       FROM ratings_raw
       WHERE rating IS NOT NULL AND rating_diff IS NOT NULL
   )
   SELECT
       COUNT(*) AS total_with_prev,
       SUM(CASE WHEN prev_rating IS NOT NULL
                AND rating = prev_rating + rating_diff THEN 1 ELSE 0 END) AS matches_formula,
       ROUND(100.0 * SUM(CASE WHEN prev_rating IS NOT NULL
                AND rating = prev_rating + rating_diff THEN 1 ELSE 0 END) /
           NULLIF(SUM(CASE WHEN prev_rating IS NOT NULL THEN 1 ELSE 0 END), 0), 2) AS pct_match
   FROM consecutive
   ```
   Expected: >99% match → ratings_raw.rating is POST-GAME.

2. **Pre-game derivation:** Show sample rows demonstrating
   `pre_game_rating = rating - rating_diff`.

3. **Temporal join feasibility:** Sample join of ratings_raw with
   matches_raw via profileId/profile_id with `date < started`.

4. **Coverage:** Fraction of match players with rating entries.
   Temporal coverage gap (ratings starts 2022-09 vs matches 2020-08).

5. **matches_raw.rating resolution:** Sample 100K rm_1v1 matches, find
   closest ratings_raw entry with `date <= started`, compare values.
   If >80% match → matches_raw.rating is POST-GAME.
   Reclassify from AMBIGUOUS to POST_GAME with evidence.

6. **matches_raw -- brief confirmation:** Target (won), timestamps
   (started, finished), core features present. Verdict: KEEP.

---

### T03 -- Produce artifacts and update tracking

**Objective:** Consolidate into JSON/MD artifacts. Update ROADMAP,
STEP_STATUS, research_log.

**Instructions:**

1. Build JSON artifact:
   ```json
   {
     "step": "01_03_03",
     "dataset": "aoe2companion",
     "tables": {
       "matches_raw": {"verdict": "KEEP", "i3_risk": "MODERATE", "reasoning": "..."},
       "ratings_raw": {"verdict": "KEEP", "i3_risk": "LOW", "reasoning": "..."},
       "leaderboards_raw": {"verdict": "DROP", "i3_risk": "HIGH", "reasoning": "..."},
       "profiles_raw": {"verdict": "DROP", "i3_risk": "MODERATE", "reasoning": "..."}
     },
     "rating_classification_resolved": {
       "column": "matches_raw.rating",
       "old_classification": "AMBIGUOUS",
       "new_classification": "POST_GAME",
       "evidence": "...",
       "pre_game_derivation": "matches_raw.rating - matches_raw.ratingDiff"
     },
     "pipeline_scope": ["matches_raw", "ratings_raw"],
     "excluded_tables": ["leaderboards_raw", "profiles_raw"],
     "sql_queries": { ... }
   }
   ```

2. Write JSON to `reports/artifacts/01_exploration/03_profiling/01_03_03_table_utility_assessment.json`.
3. Write MD report to same directory.
4. Add 01_03_03 step to ROADMAP.md.
5. Add 01_03_03 to STEP_STATUS.yaml.
6. Write research_log.md entry.

---

## File Manifest

| File | Action |
|------|--------|
| `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_03_table_utility_assessment.py` | Create |
| `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_03_table_utility_assessment.ipynb` | Create |
| `src/.../aoe2companion/reports/artifacts/.../01_03_03_table_utility_assessment.json` | Create |
| `src/.../aoe2companion/reports/artifacts/.../01_03_03_table_utility_assessment.md` | Create |
| `src/.../aoe2companion/reports/ROADMAP.md` | Update |
| `src/.../aoe2companion/reports/STEP_STATUS.yaml` | Update |
| `src/.../aoe2companion/reports/research_log.md` | Update |

## Gate Condition

- JSON artifact exists with verdicts for all 4 tables
- JSON contains `rating_classification_resolved` with `new_classification: POST_GAME`
- JSON contains `pipeline_scope` and `excluded_tables`
- All SQL queries in `sql_queries` dict (I6)
- MD report exists and is non-empty
- STEP_STATUS.yaml shows 01_03_03 complete
- Notebook executes end-to-end without error

## Out of scope

- Data cleaning decisions (01_04)
- Feature engineering from ratings_raw (Phase 02)
- Re-profiling matches_raw (01_03_01 already covers this)
- DuckDB schema changes (no tables/views created)
