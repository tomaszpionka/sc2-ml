# Phase 06 Interface CSV — sc2egset

**spec:** reports/specs/01_05_preregistration.md@7e259dd8 §12
**Date:** 2026-04-18

## Summary

- Total rows: 35
- PSI rows: 24 (T03; uncohort-filtered per B2 fix)
- ICC rows: 3 (T06; 3 metric_names per B3 fix)
- Cohen's d DGP rows: 8 (T08; POST_GAME)

## M3 note

Spec §1 9-col contract differs from actual VIEW schema for sc2egset.
Per INVARIANTS §5 I8 partial: feature_name values match actual VIEW schema.
Phase 06 UNION joins on metric_name only (cross-dataset alignment).

## M7 note

All rows tagged [POP:tournament]: sc2egset is tournament-scraped.

## Schema (9 columns per spec §12)

| Column | Type | Nullable | Notes |
|---|---|---|---|
| dataset_tag | VARCHAR | No | 'sc2egset' constant |
| quarter | VARCHAR | No | YYYY-QN or 'overlap_window' |
| feature_name | VARCHAR | No | Actual VIEW column name |
| metric_name | VARCHAR | No | psi/cohen_d/icc_* |
| metric_value | DOUBLE | Yes | NULL = not applicable |
| reference_window_id | VARCHAR | Yes | '2022-Q3Q4' |
| cohort_threshold | INTEGER | Yes | NULL = uncohort-filtered |
| sample_size | INTEGER | Yes | N rows in tested period |
| notes | VARCHAR | Yes | Free-text tags |

## Sample rows

| dataset_tag   | quarter   | feature_name     | metric_name   |   metric_value |   metric_ci_low |   metric_ci_high | reference_window_id   |   cohort_threshold |   sample_size | notes                                                       |
|:--------------|:----------|:-----------------|:--------------|---------------:|----------------:|-----------------:|:----------------------|-------------------:|--------------:|:------------------------------------------------------------|
| sc2egset      | 2023-Q1   | faction          | psi           |         0.1769 |             nan |              nan | 2022-Q3Q4             |                  0 |           520 | PRIMARY:uncohort-filtered;epsilon=0.000306;[POP:tournament] |
| sc2egset      | 2023-Q1   | opponent_faction | psi           |         0.1769 |             nan |              nan | 2022-Q3Q4             |                  0 |           520 | PRIMARY:uncohort-filtered;epsilon=0.000306;[POP:tournament] |
| sc2egset      | 2023-Q1   | matchup          | psi           |         0.3631 |             nan |              nan | 2022-Q3Q4             |                  0 |           520 | PRIMARY:uncohort-filtered;epsilon=0.000306;[POP:tournament] |
| sc2egset      | 2023-Q2   | faction          | psi           |         0.0012 |             nan |              nan | 2022-Q3Q4             |                  0 |          1396 | PRIMARY:uncohort-filtered;epsilon=0.000306;[POP:tournament] |
| sc2egset      | 2023-Q2   | opponent_faction | psi           |         0.0012 |             nan |              nan | 2022-Q3Q4             |                  0 |          1396 | PRIMARY:uncohort-filtered;epsilon=0.000306;[POP:tournament] |
| sc2egset      | 2023-Q2   | matchup          | psi           |         0.0246 |             nan |              nan | 2022-Q3Q4             |                  0 |          1396 | PRIMARY:uncohort-filtered;epsilon=0.000306;[POP:tournament] |
| sc2egset      | 2023-Q3   | faction          | psi           |         0.2786 |             nan |              nan | 2022-Q3Q4             |                  0 |           244 | PRIMARY:uncohort-filtered;epsilon=0.000306;[POP:tournament] |
| sc2egset      | 2023-Q3   | opponent_faction | psi           |         0.2786 |             nan |              nan | 2022-Q3Q4             |                  0 |           244 | PRIMARY:uncohort-filtered;epsilon=0.000306;[POP:tournament] |
| sc2egset      | 2023-Q3   | matchup          | psi           |         0.6959 |             nan |              nan | 2022-Q3Q4             |                  0 |           244 | PRIMARY:uncohort-filtered;epsilon=0.000306;[POP:tournament] |
| sc2egset      | 2023-Q4   | faction          | psi           |         0.0328 |             nan |              nan | 2022-Q3Q4             |                  0 |          1344 | PRIMARY:uncohort-filtered;epsilon=0.000306;[POP:tournament] |
