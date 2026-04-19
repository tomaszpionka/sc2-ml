# Data Dictionary — sc2egset

**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0 (CROSS-01-06-v1)
**Produced by:** 01_06_01 (Phase 01 Decision Gates)
**Date:** 2026-04-19

## Temporal Classification Summary

- **IDENTIFIER:** 16 column(s)
- **IN_GAME_HISTORICAL:** 5 column(s)
- **METADATA:** 17 column(s)
- **POST_GAME_HISTORICAL:** 4 column(s)
- **PRE_GAME:** 31 column(s)
- **TARGET:** 3 column(s)

## Tables covered

- `matches_history_minimal` — 9-column Phase-02-ready cross-dataset view (I8 contract)
- `matches_flat_clean` — sc2egset-specific cleaned flat replay table
- `player_history_all` — sc2egset per-player history table (includes IN_GAME_HISTORICAL cols)

## I3 Temporal Discipline Check

- No POST_GAME_HISTORICAL column is classified PRE_GAME. **PASS.**
- `duration_seconds` and `is_duration_suspicious` are POST_GAME_HISTORICAL; Phase 02 feature extractors that drop POST_GAME_HISTORICAL tokens will auto-exclude them.
- `APM`, `SQ`, `supplyCappedPercent`, `is_decisive_result` are IN_GAME_HISTORICAL (sc2egset-specific; not available for AoE2 comparison datasets).

## Columns with Invariant Notes

- **match_id** (`matches_history_minimal`): `IDENTITY. Prefix applied in this VIEW only; upstream replay_id unchanged (I9).`
- **started_at** (`matches_history_minimal`): `CONTEXT. Temporal anchor for Phase 02 rating-update loops. Chronologically faithful (TIMESTAMP ordering, not lex).`
- **player_id** (`matches_history_minimal`): `IDENTITY. Per-dataset identifier; cross-dataset identity resolution is a future step (Phase 01_05+).`
- **faction** (`matches_history_minimal`): `PRE_GAME. Raw vocabulary (race actually played, not selectedRace which includes 'Random'). Polymorphic I8 contract -- see description.`
- **opponent_faction** (`matches_history_minimal`): `PRE_GAME. Mirror of faction from the opponent row.`
- **won** (`matches_history_minimal`): `TARGET. Direct projection of matches_flat_clean.result; prediction label for downstream experiments.`
- **duration_seconds** (`matches_history_minimal`): `POST_GAME_HISTORICAL. Available only after match end. DO NOT use as PRE_GAME feature for predicting match T outcome (I3 violation). Useful for retrosp`
- **dataset_tag** (`matches_history_minimal`): `IDENTITY. Matches the prefix before '::' in match_id.`
- **replay_id** (`matches_flat_clean`): `IDENTITY. Canonical join key extracted via regexp. NULLIF empty-string guard applied.`
- **filename** (`matches_flat_clean`): `IDENTITY. Replay file path relative to raw_dir. Invariant I10.`
- **toon_id** (`matches_flat_clean`): `IDENTITY. Battle.net toon/account identifier. Player identity key.`
- **nickname** (`matches_flat_clean`): `IDENTITY. Player nickname.`
- **playerID** (`matches_flat_clean`): `IDENTITY. In-game player id.`
- **userID** (`matches_flat_clean`): `IDENTITY. User id.`
- **result** (`matches_flat_clean`): `TARGET. Game result (Win or Loss only -- Undecided/Tie excluded by true_1v1_decisive CTE). Prediction target.`
- **is_mmr_missing** (`matches_flat_clean`): `PRE_GAME. TRUE if MMR=0 (unrated professional). MNAR. MMR dropped in 01_04_02 (DS-SC2-01); this flag preserves the rated/unrated signal.`
- **race** (`matches_flat_clean`): `PRE_GAME. Actual race played (Protoss, Zerg, Terran abbreviated).`
- **selectedRace** (`matches_flat_clean`): `PRE_GAME. Selected race. Empty string normalised to 'Random'.`
- **region** (`matches_flat_clean`): `PRE_GAME. Battle.net region label.`
- **realm** (`matches_flat_clean`): `PRE_GAME. Realm label.`
- **isInClan** (`matches_flat_clean`): `PRE_GAME. Whether the player is in a clan.`
- **startDir** (`matches_flat_clean`): `PRE_GAME. Starting direction code (lobby assignment).`
- **startLocX** (`matches_flat_clean`): `PRE_GAME. Starting x location on map.`
- **startLocY** (`matches_flat_clean`): `PRE_GAME. Starting y location on map.`
- **metadata_mapName** (`matches_flat_clean`): `PRE_GAME. Human-readable map name.`
- **gd_maxPlayers** (`matches_flat_clean`): `PRE_GAME. Max players in game description.`
- **gd_mapFileSyncChecksum** (`matches_flat_clean`): `PRE_GAME. Map file sync checksum.`
- **details_isBlizzardMap** (`matches_flat_clean`): `PRE_GAME. Blizzard-authored map flag (from details struct).`
- **details_timeUTC** (`matches_flat_clean`): `CONTEXT. UTC timestamp of game. Temporal anchor for I3 ordering.`
- **header_version** (`matches_flat_clean`): `CONTEXT. SC2 version string.`
- **metadata_baseBuild** (`matches_flat_clean`): `CONTEXT. Base build string.`
- **metadata_dataBuild** (`matches_flat_clean`): `CONTEXT. Data build string.`
- **metadata_gameVersion** (`matches_flat_clean`): `CONTEXT. Game version.`
- **go_amm** (`matches_flat_clean`): `CONTEXT. Game option: automated match making. Variable cardinality (n_distinct=2).`
- **go_clientDebugFlags** (`matches_flat_clean`): `CONTEXT. Game option: client debug flags. Variable cardinality (n_distinct=2).`
- **go_competitive** (`matches_flat_clean`): `CONTEXT. Game option: competitive mode. Variable cardinality (n_distinct=2).`
- **duration_seconds** (`matches_flat_clean`): `POST_GAME_HISTORICAL. Game duration in seconds. Derived from player_history_all.header_elapsedGameLoops / 22.4 (I7: details.gameSpeed cardinality=1 in`
- **is_duration_suspicious** (`matches_flat_clean`): `POST_GAME_HISTORICAL. TRUE where duration_seconds > 86400s. Threshold: ~25x p99 for sc2egset (p99=1,884s, max=6,073s); identical across all 3 datasets`
- **replay_id** (`player_history_all`): `IDENTITY. Canonical join key extracted via regexp. NULLIF empty-string guard applied.`
- **filename** (`player_history_all`): `IDENTITY. Replay file path relative to raw_dir. Invariant I10.`
- **toon_id** (`player_history_all`): `IDENTITY. Battle.net toon/account identifier. Player identity key.`
- **nickname** (`player_history_all`): `IDENTITY. Player nickname.`
- **playerID** (`player_history_all`): `IDENTITY. In-game player id.`
- **userID** (`player_history_all`): `IDENTITY. User id.`
- **result** (`player_history_all`): `TARGET. Game result (Win, Loss, Undecided, Tie). Unfiltered in history.`
- **is_decisive_result** (`player_history_all`): `POST_GAME_HISTORICAL. TRUE if result IN ('Win','Loss'). Added in 01_04_02 (DS-SC2-04). Enables Phase 02 win-rate denominator selection without VIEW ch`
- **is_mmr_missing** (`player_history_all`): `PRE_GAME. TRUE if MMR=0 (unrated professional). MNAR. MMR dropped in 01_04_02 (DS-SC2-01); this flag preserves the rated/unrated signal.`
- **race** (`player_history_all`): `PRE_GAME. Actual race played (Protoss, Zerg, Terran abbreviated).`
- **selectedRace** (`player_history_all`): `PRE_GAME. Selected race. Empty string normalised to 'Random'.`
- **region** (`player_history_all`): `PRE_GAME. Battle.net region label.`
- **realm** (`player_history_all`): `PRE_GAME. Realm label.`
- **isInClan** (`player_history_all`): `PRE_GAME. Whether the player is in a clan.`
- **APM** (`player_history_all`): `IN_GAME_HISTORICAL. Actions per minute. Sentinel APM=0 converted to NULL via NULLIF (01_04_02, DS-SC2-10). 1132 rows affected.`
- **is_apm_unparseable** (`player_history_all`): `IN_GAME_HISTORICAL. TRUE if original APM=0 (parse failure / empty replay). Added in 01_04_02 (DS-SC2-10).`
- **SQ** (`player_history_all`): `IN_GAME_HISTORICAL. Spending Quotient. Parse-failure sentinel INT32_MIN corrected to NULL.`
- **supplyCappedPercent** (`player_history_all`): `IN_GAME_HISTORICAL. % game time supply-capped.`
- **header_elapsedGameLoops** (`player_history_all`): `IN_GAME_HISTORICAL. Game duration in loops. Post-game observable.`
- **startDir** (`player_history_all`): `PRE_GAME. Starting direction code (lobby assignment).`
- **startLocX** (`player_history_all`): `PRE_GAME. Starting x location on map.`
- **startLocY** (`player_history_all`): `PRE_GAME. Starting y location on map.`
- **metadata_mapName** (`player_history_all`): `PRE_GAME. Human-readable map name.`
- **gd_mapSizeX** (`player_history_all`): `PRE_GAME. Map width (0 corrected to NULL; parse artifact). Retained in player_history_all per DS-SC2-06.`
- **gd_mapSizeY** (`player_history_all`): `PRE_GAME. Map height (0 corrected to NULL; parse artifact). Retained in player_history_all per DS-SC2-06.`
- **gd_maxPlayers** (`player_history_all`): `PRE_GAME. Max players in game description.`
- **details_isBlizzardMap** (`player_history_all`): `PRE_GAME. Blizzard-authored map flag (from details struct). Preferred over gd_isBlizzardMap (confirmed identical, duplicate dropped).`
- **gd_mapAuthorName** (`player_history_all`): `PRE_GAME. Map author name. Retained in player_history_all per DS-SC2-07.`
- **gd_mapFileSyncChecksum** (`player_history_all`): `PRE_GAME. Map file sync checksum.`
- **details_timeUTC** (`player_history_all`): `CONTEXT. UTC timestamp of game. Temporal anchor for I3 ordering.`
- **header_version** (`player_history_all`): `CONTEXT. SC2 version string.`
- **metadata_baseBuild** (`player_history_all`): `CONTEXT. Base build string.`
- **metadata_dataBuild** (`player_history_all`): `CONTEXT. Data build string.`
- **metadata_gameVersion** (`player_history_all`): `CONTEXT. Game version.`
- **go_amm** (`player_history_all`): `CONTEXT. Game option: automated match making. Variable cardinality (n_distinct=2).`
- **go_clientDebugFlags** (`player_history_all`): `CONTEXT. Game option: client debug flags. Variable cardinality (n_distinct=2).`
- **go_competitive** (`player_history_all`): `CONTEXT. Game option: competitive mode. Variable cardinality (n_distinct=2).`

## Full Dictionary

See `data_dictionary_sc2egset.csv` for the full column-level dictionary.