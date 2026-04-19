# Data Dictionary — aoestats

**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0
**Date:** 2026-04-19

## Temporal Classification: {'IDENTIFIER': 9, 'METADATA': 9, 'PRE_GAME': 18, 'TARGET': 6, 'POST_GAME_HISTORICAL': 3}

## Key Notes
- `team=0/1` slot columns carry `[PRE-canonical_slot]` flag per W3 ARTEFACT_EDGE (01_04_05).
  Direct slot-conditioned features are forbidden until BACKLOG F1 + W4 resolve.
- `patch` (BIGINT) present in matches_1v1_clean and player_history_all — D5 PRIMARY role for aoestats.
- `duration_seconds` is POST_GAME_HISTORICAL; DO NOT use as PRE_GAME feature (I3).
- `avg_elo` sentinel=0 → NULL via NULLIF in 01_04_02.

## Full Dictionary
See `data_dictionary_aoestats.csv`.
