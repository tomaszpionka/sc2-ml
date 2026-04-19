# Data Dictionary — aoe2companion

**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0
**Date:** 2026-04-19

## Temporal Classification: {'IDENTIFIER': 16, 'METADATA': 16, 'PRE_GAME': 38, 'TARGET': 5, 'POST_GAME_HISTORICAL': 4}

## Key Notes
- `profileId` / `player_id`: Branch (i) API-namespace identifier. Identity-rate reconciliation
  2026-04-19: 2.57% / 3.55% rename-rate in rm_1v1 scope. Cross-dataset
  aoe2companion-aoestats namespace bridge VERDICT A (0.9960 agreement). See §4.2.2.
- `duration_seconds` is POST_GAME_HISTORICAL; DO NOT use as PRE_GAME feature (I3).
- `won` is the TARGET variable; also used as drift-proxy in PSI (W2) — stable in all quarters.
- `faction` and `map_id`: both show substantive drift from 2023-Q3 (DLC map-pool rotation);
  Phase 02 temporal CV must handle unseen categories for map_id.
- No `[PRE-canonical_slot]` flag needed: aoe2companion does not assign team slots by skill rank
  (no equivalent of aoestats W3 ARTEFACT_EDGE).
- `country` column: 2.25% NULL retention (MAR primary / MNAR sensitivity per §4.2.3);
  MissingIndicator route applied in cleaning.

## Full Dictionary
See `data_dictionary_aoe2companion.csv`.
