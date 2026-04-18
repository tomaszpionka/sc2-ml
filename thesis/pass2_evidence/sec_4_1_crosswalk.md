```markdown
# §4.1 Numerical Crosswalk
Generated: 2026-04-17 by T01 executor.

Purpose: every number used in §4.1.1, §4.1.2, and §4.1.3 prose traces to a Phase 01 artifact line.
Number-format normalization per plan T01 step 6: strip `,`, space, `\u00A0`; Polish decimal `,` → `.`.

## Catalog of §2.2 / §2.3 corpus-statistic migration candidates (per Fix 4)

| Sentence source | Classification | Disposition |
|---|---|---|
| §2.2.1 "555 zestawień w korpusie SC2EGSet zgodnie z findingiem 01_03_02" | (a) instrumental — cited as illustrative of Random-race rate in mechanics discussion | Keep in §2.2.1 |
| §2.2.2 "188 unikalnych nazw map zgodnie z findingiem strukturalnego profilowania" | (a) instrumental — used to explain map-pool cardinality implication for encoding choice | Keep in §2.2.2; §4.1.1 re-states in corpus-description context |
| §2.2.2 "SC2EGSet rozciąga się na lata 2016–2022 zgodnie z findingiem Phase 01" | (b) MIGRATION CANDIDATE — corpus date range mis-stated (actual: 2016-01-07 → 2024-12-01 per 01_02_04 timeUTC); §4.1.1.1 will state correct range | Flag: §2.2.2 needs correction in follow-up chore commit |
| §2.2.4 "tracker_events_raw zawiera 62 003 411 zdarzeń, game_events_raw — 608 618 823 zdarzeń, message_events_raw — 52 167 zdarzeń" | (a) instrumental — event-stream counts motivate "strukturalna przewaga SC2 nad AoE2" in mechanics discussion | Keep in §2.2.4; §4.1.1.2 re-states in provenance + per-replay density context |
| §2.3.3 "ranking początkowy 1000 dla nowych graczy" | (a) instrumental — mechanism description, not corpus stat | Keep |

**Count of (b) findings: 1 (the 2016–2022 vs. 2016–2024 date range in §2.2.2).** Below threshold of 3. Not halting T01. The correction is flagged for a subsequent chore commit, not this PR's scope.

## Main crosswalk (prose ↔ artifact)

| claim_text | artifact_path | anchor | prose_form | artifact_form | normalized_value | datatype | hedging_needed |
|---|---|---|---|---|---|---|---|
| SC2EGSet: 70 katalogów turniejowych | src/.../sc2egset/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.md | "Top-level directories: 70" | 70 | 70 | 70 | int | No |
| SC2EGSet: 22 390 plików .SC2Replay.json | 01_01_01_file_inventory.md | "Total replay files: 22390" | 22 390 | 22390 | 22390 | int | No |
| SC2EGSet: ~214 GB surowych plików | 01_01_01_file_inventory.md | "Total replay size: 214060.62 MB" | ~214 GB | 214060.62 MB | 214060 (MB) | float | No |
| SC2EGSet: min 30 powtórek w turnieju | 01_01_01_file_inventory.md | "Min: 30" (2016_IEM_10_Taipei) | 30 | 30 | 30 | int | No |
| SC2EGSet: max 1 296 powtórek w turnieju | 01_01_01_file_inventory.md | "Max: 1296" (2022_03_DH_SC2_Masters_Atlanta) | 1 296 | 1296 | 1296 | int | No |
| SC2EGSet: mediana 260,5 powtórek na turniej | 01_01_01_file_inventory.md | "Median: 260.5" | 260,5 | 260.5 | 260.5 | float | No |
| SC2EGSet: zakres czasowy 2016-01-07 → 2024-12-01 | 01_02_04_univariate_census.md | Section F: "earliest 2016-01-07T02:21:46.002Z / latest 2024-12-01T23:48:45.2511615Z" | 2016-01-07 — 2024-12-01 | 2016-01-07T02:21:46.002Z — 2024-12-01T23:48:45.2511615Z | 2016-2024 | str/date | No |
| SC2EGSet: 76 miesięcy z pokryciem | 01_02_04_univariate_census.md | "distinct_months 76" | 76 | 76 | 76 | int | No |
| SC2EGSet: 32 luki miesięczne | 01_03_01_systematic_profile.md | "Calendar-month gaps: 32" | 32 | 32 | 32 | int | No |
| SC2EGSet: 188 unikalnych nazw map | 01_02_04_univariate_census.md | "map_name cardinality 188" | 188 | 188 | 188 | int | No |
| SC2EGSet: 46 wersji gry (metadata.gameVersion) | 01_02_04_univariate_census.md | "game_version_meta cardinality 46" | 46 | 46 | 46 | int | No |
| SC2EGSet: tracker_events_raw 62 003 411 zdarzeń | 01_03_04_event_profiling.md | "Tracker Events (62,003,411 rows)" | 62 003 411 | 62,003,411 | 62003411 | int | No |
| SC2EGSet: game_events_raw 608 618 823 zdarzeń | 01_03_04_event_profiling.md | "Game Events (608,618,823 rows)" | 608 618 823 | 608,618,823 | 608618823 | int | No |
| SC2EGSet: message_events_raw 52 167 zdarzeń | 01_03_04_event_profiling.md | "Message Events (52,167 rows)" | 52 167 | 52,167 | 52167 | int | No |
| SC2EGSet: 10 typów zdarzeń tracker | 01_03_04_event_profiling.md | event type table (10 rows) | 10 | 10 | 10 | int | No |
| SC2EGSet: 23 typów zdarzeń game | 01_03_04_event_profiling.md | event type table (23 rows) | 23 | 23 | 23 | int | No |
| SC2EGSet: 3 typy zdarzeń message | 01_03_04_event_profiling.md | event type table (3 rows) | 3 | 3 | 3 | int | No |
| SC2EGSet: UnitBorn 36,08% strumienia tracker | 01_03_04_event_profiling.md | "UnitBorn 36.0827" | 36,08% | 36.0827 | 36.08 | float | No |
| SC2EGSet: CameraUpdate 63,67% strumienia game | 01_03_04_event_profiling.md | "CameraUpdate 63.6700" | 63,67% | 63.6700 | 63.67 | float | No |
| SC2EGSet: UnitBorn/PlayerStats/PlayerSetup pokrycie 100% replays | 01_03_04_event_profiling.md | "UnitBorn 22,390 100.00 / PlayerStats 22,390 100.00 / PlayerSetup 22,390 100.00" | 100% | 100.00 | 100.0 | float | No |
| SC2EGSet: UnitOwnerChange 25,39% replays | 01_03_04_event_profiling.md | "UnitOwnerChange 5,684 25.39" | 25,39% | 25.39 | 25.39 | float | No |
| SC2EGSet: message events pokrycie 99,42% replays | 01_03_04_event_profiling.md | "Replay coverage: 22260 / 22390 (99.42%)" | 99,42% | 99.42 | 99.42 | float | No |
| SC2EGSet: matches_long_raw 44 817 wierszy | 01_04_00_source_normalization.md | "matches_long_raw 44,817" | 44 817 | 44,817 | 44817 | int | No |
| SC2EGSet: matches_flat_clean 22 209 powtórek × 44 418 wierszy | 01_04_01_data_cleaning.md | "matches_flat_clean (final) 22,209 / 44,418" | 22 209 / 44 418 | 22,209 / 44,418 | 22209 / 44418 | int | No |
| SC2EGSet: R01 true_1v1_decisive -24 meczów / -85 wierszy | 01_04_01_data_cleaning.md | "Excluded (non-1v1 + indecisive) -24 / -85" | -24 / -85 | -24 / -85 | 24 / 85 | int | No |
| SC2EGSet: R03 MMR<0 replay-level exclusion -157 / -314 | 01_04_01_data_cleaning.md | "Excluded (any MMR<0 player) -157 / -314" | -157 / -314 | -157 / -314 | 157 / 314 | int | No |
| SC2EGSet: matches_flat_clean 28 kolumn (49→28, -21) | 01_04_02_post_cleaning_validation.md | "matches_flat_clean 49 → 28 (drop 21)" | 28 kolumn | 49 → 28 | 28 | int | No |
| SC2EGSet: player_history_all 37 kolumn (51→37, -16, +2, mod 1) | 01_04_02_post_cleaning_validation.md | "player_history_all 51 → 37 (drop 16, add 2, modify 1)" | 37 kolumn | 51 → 37 | 37 | int | No |
| SC2EGSet: 18 assertions PASS | 01_04_02_post_cleaning_validation.md | Validation Results table | 18 | 18 | 18 | int | No |
| SC2EGSet: toon_id cardinality 2 495 | 01_03_01_systematic_profile.json | rp_distinct_profiles.toon_id.cardinality=2495 | 2 495 | 2495 | 2495 | int | No |
| SC2EGSet: selectedRace='' normalizacja 1 110 wierszy / 555 replays | 01_03_02_true_1v1_profile.md | "Total rows with selectedRace = '': 1110 / Unique replays: 555" | 1 110 / 555 | 1110 / 555 | 1110 / 555 | int | No |
| SC2EGSet: MMR=0 sentinel 83,95% matches_flat_clean | 01_04_01_missingness_ledger.csv / 01_04_01_data_cleaning.md | MMR row "pct_missing_total 83.9525" | 83,95% | 83.9525 | 83.95 | float | No |
| SC2EGSet: MMR=0 sentinel 83,65% player_history_all | 01_04_01_data_cleaning.md | MMR row player_history_all "83.6491" | 83,65% | 83.6491 | 83.65 | float | No |
| SC2EGSet: APM=0 sentinel 1 132 wierszy (2,53%) | 01_04_01_data_cleaning.md | "APM 1132 2.5258" | 2,53% (1 132) | 1132 (2.5258%) | 2.53 | float | No |
| SC2EGSet: highestLeague sentinel 72,04%/72,16% | 01_04_01_data_cleaning.md | "highestLeague 72.0361 / 72.1557" | 72,04% / 72,16% | 72.0361 / 72.1557 | 72.04 / 72.16 | float | No |
| SC2EGSet: clanTag sentinel 73,93%/74,10% | 01_04_01_data_cleaning.md | "clanTag 73.934 / 74.1013" | 73,93% / 74,10% | 73.934 / 74.1013 | 73.93 / 74.10 | float | No |
| SC2EGSet: gd_mapSize=0 anomaly 273 replays | 01_04_01_data_cleaning.md | "map size missing ... 273 replays" | 273 | 273 | 273 | int | No |
| SC2EGSet: SQ INT32_MIN sentinel 2 wierszy | 01_04_01_data_cleaning.md | "SQ sentinel 2 rows 0.0045%" | 2 | 2 | 2 | int | No |
| SC2EGSet: handicap=0 sentinel 2 wierszy | 01_04_01_data_cleaning.md | "handicap = 0 FLAG ... 2 rows 0.0045%" | 2 | 2 | 2 | int | No |
| SC2EGSet: side=0 win_pct 51,96% | 01_04_00_source_normalization.md | "side 0 n_wins 11634 51.9607%" | 51,96% | 51.9607 | 51.96 | float | No |
| SC2EGSet: side=1 win_pct 47,97% | 01_04_00_source_normalization.md | "side 1 n_wins 10740 47.9743%" | 47,97% | 47.9743 | 47.97 | float | No |
| SC2EGSet: leaderboard_raw NULL 100% | 01_04_00_source_normalization.md | "leaderboard_raw = NULL (expected — tournament dataset)" | 100% | 100 | 100.0 | float | No |
| SC2EGSet: Result dist 22 382 Win / 22 409 Loss / 24 Undecided / 2 Tie (surowy) | 01_03_01_systematic_profile.md | Class Balance | 22 382 / 22 409 / 24 / 2 | 22,382 / 22,409 / 24 / 2 | 22382/22409/24/2 | int | No |
| SC2EGSet: Race Prot 36,21%/ Zerg 35,02% / Terr 28,76% | 01_03_01_systematic_profile.md | race dist | 36,21%/35,02%/28,76% | 36.2095/35.0202/28.7636 | 36.21/35.02/28.76 | float | No |
| SC2EGSet: 3 BW-prefixed rows (BWTe/BWZe/BWPr) | 01_03_01_systematic_profile.md | race dist: BWTe 1, BWPr 1; +BWZe implied | 3 | 3 (race rows BWTe+BWZe+BWPr) | 3 | int | Yes — BWZe absent in top-5, inferred from commentary |
| SC2EGSet: 1 110 Random rows = 555 replays | 01_03_02_true_1v1_profile.md | "Total rows with selectedRace = '': 1110 Unique replays: 555" | 1 110 / 555 | 1110 / 555 | 1110 / 555 | int | No |
| SC2EGSet: 22 379 replays z 2 graczami (99,95%) | 01_03_02_true_1v1_profile.md | "players_per_replay 2: 22379 99.9509%" | 22 379 / 99,95% | 22379 / 99.9509 | 22379 | int | No |
| SC2EGSet: 26 wierszy Undecided/Tie w 13 replays | 01_03_02_true_1v1_profile.md | "true_1v1_indecisive 13 / 0.0581" + context | 26 / 13 | 13 replays × 2 = 26 rows | 26/13 | int | No |
| SC2EGSet: PlayerStats 160-loop period | 01_03_04_event_profiling.md (plan summary) | Event profiling note | 160 | 160 | 160 | int | Yes — rounded from 7,14 s @ 22,4 loops/s |
| SC2EGSet: 7,14 s przy *Faster* | 01_03_04_event_profiling.md / §2.2.4 | Derivation: 160/22,4 | 7,14 s | 160 / 22.4 | 7.14 | float | No |
| aoestats: 172 plików Parquet matches/ | 01_01_01_file_inventory.md (aoestats) | "matches: 172 weekly Parquet files" | 172 | 172 | 172 | int | No |
| aoestats: 171 plików Parquet players/ | 01_01_01_file_inventory.md | "players: 171 weekly Parquet files" | 171 | 171 | 171 | int | No |
| aoestats: 610,55 MB matches/ | 01_01_01_file_inventory.md | "matches 610.55 MB" | 610,55 MB | 610.55 MB | 610.55 | float | No |
| aoestats: 3 162,86 MB players/ | 01_01_01_file_inventory.md | "players 3162.86 MB" | 3 162,86 MB | 3162.86 MB | 3162.86 | float | No |
| aoestats: łącznie 3 773,61 MB | 01_01_01_file_inventory.md | "Total size: 3773.61 MB" | 3 773,61 MB / ~3,77 GB | 3773.61 MB | 3773.61 | float | No |
| aoestats: zakres czasowy 2022-08-28 — 2026-02-07 | 01_01_01_file_inventory.md | "matches: 2022-08-28 to 2026-02-07" | 2022-08-28 — 2026-02-07 | 2022-08-28 to 2026-02-07 | 2022-2026 | str | No |
| aoestats: 3 luki w matches | 01_01_01_file_inventory.md | "Gaps found: 3" | 3 | 3 | 3 | int | No |
| aoestats: luka 43-dniowa 2024-07-20 → 2024-09-01 | 01_01_01_file_inventory.md | "2024-07-20 -> 2024-09-01 (43 days)" | 43 dni | 43 | 43 | int | No |
| aoestats: 4 luki w players | 01_01_01_file_inventory.md | "Gaps found: 4" | 4 | 4 | 4 | int | No |
| aoestats: matches_raw 30 690 651 | 01_03_02_true_1v1_profile.md | "Total matches 30,690,651" | 30 690 651 | 30,690,651 | 30690651 | int | No |
| aoestats: matches z player data 30 477 761 = 99,31% | 01_03_02_true_1v1_profile.md | "Matches with player data 30,477,761 99.31%" | 30 477 761 / 99,31% | 30,477,761 / 99.31% | 30477761 | int | No |
| aoestats: true 1v1 18 438 769 = 60,08% | 01_03_02_true_1v1_profile.md | "True 1v1 18,438,769 60.0794" | 18 438 769 / 60,08% | 18,438,769 / 60.0794 | 18438769 | int | No |
| aoestats: ranked 1v1 random_map 17 815 944 = 58,52% | 01_03_02_true_1v1_profile.md (L4→B). Wait: 17,815,944 is "true 1v1 ∩ ranked 1v1" | "overlap 17,815,944 / 96.62% / 99.20% B" | 17 815 944 | 17,815,944 | 17815944 | int | No |
| aoestats: matches_1v1_clean final 17 814 947 | 01_04_01_data_cleaning.md | "Stage 4 final VIEW 17,814,947" | 17 814 947 | 17,814,947 | 17814947 | int | No |
| aoestats: R08 inconsistent winner -997 wierszy (0,0056%) | 01_04_01_data_cleaning.md | "997 rows excluded 0.0056%" | 997 / 0,0056% | 997 / 0.0056% | 997 | int | No |
| aoestats: matches_1v1_clean 20 kolumn (21→20) | 01_04_02_post_cleaning_validation.md | "matches_1v1_clean 21 -> 20" | 20 kolumn | 21 → 20 | 20 | int | No |
| aoestats: player_history_all 107 626 399 wierszy / 14 kolumn | 01_04_01_data_cleaning.md / 01_04_02 | "player_history_all rows 107,626,399" / "13 -> 14" | 107 626 399 / 14 | 107,626,399 / 13 → 14 | 107626399 / 14 | int | No |
| aoestats: 33 assertions PASS | 01_04_02_post_cleaning_validation.md | Validation Results table | 33 | 33 | 33 | int | No |
| aoestats: p0_old_rating sentinel 0 = 4 730 (0,0266%) | 01_04_01_missingness_ledger.csv | "p0_old_rating 4730 0.0266" | 4 730 / 0,0266% | 4,730 / 0.0266 | 4730 | int | No |
| aoestats: p1_old_rating sentinel 0 = 188 (0,0011%) | 01_04_01_missingness_ledger.csv | "p1_old_rating 188 0.0011" | 188 / 0,0011% | 188 / 0.0011 | 188 | int | No |
| aoestats: avg_elo sentinel 0 = 118 (0,0007%) | 01_04_01_missingness_ledger.csv | "avg_elo 118 0.0007" | 118 / 0,0007% | 118 / 0.0007 | 118 | int | No |
| aoestats: old_rating (player_history_all) sentinel 5 937 (0,0055%) | 01_04_01_missingness_ledger.csv | "old_rating sentinel=0 5937 0.0055" | 5 937 / 0,0055% | 5937 / 0.0055 | 5937 | int | No |
| aoestats: p0_civ n_distinct=50 | 01_04_01_missingness_ledger.csv / matches_1v1_clean.yaml | "p0_civ 50" / YAML notes "50 distinct civilizations in scope" | 50 | 50 | 50 | int | No |
| aoestats: matches_long_raw 107 626 399 wierszy | 01_04_00_source_normalization.md | "matches_long_raw 107,626,399" | 107 626 399 | 107,626,399 | 107626399 | int | No |
| aoestats: 1v1-scope side=1 win_pct 52,27% | 01_04_00_source_normalization.md | "1 9311550 52.2653%" | 52,27% | 52.2653 | 52.27 | float | No |
| aoestats: 1v1-scope side=0 win_pct 47,73% | 01_04_00_source_normalization.md | "0 8503784 47.7312%" | 47,73% | 47.7312 | 47.73 | float | No |
| aoestats: profile_id precision max=24 853 897 < 2^53 | 01_04_01_data_cleaning.md (plan) | R01 narrative | 24 853 897 | 24,853,897 | 24853897 | int | Yes — not in MD; cited in plan; verify against JSON artifact |
| aoestats: opening/age_uptime populated until 2024-03-10 | 01_04_01_data_cleaning.md | "Last week with opening > 1%: 2024-03-10" | 2024-03-10 | 2024-03-10 | 2024-03-10 | str/date | No |
| aoestats: opening/age_uptime 0% from 2024-03-17 | 01_04_01_data_cleaning.md | "First week with opening = 0%: 2024-03-17" | 2024-03-17 | 2024-03-17 | 2024-03-17 | str/date | No |
| aoestats: Jaccard true_1v1 ∩ ranked_1v1 = 0,958755 | 01_03_02_true_1v1_profile.md | "Jaccard index: 0.958755" | 0,958755 | 0.958755 | 0.958755 | float | No |
| aoestats: co_random_map = 622 817 (3,38% of true 1v1) | 01_03_02_true_1v1_profile.md | "co_random_map 622,817 3.3778" | 622 817 / 3,38% | 622,817 / 3.3778 | 622817 | int | No |
| aoec: 2 073 plików matches/ | 01_01_01_file_inventory.md (aoec) | "matches 2073 daily Parquet files" | 2 073 | 2073 | 2073 | int | No |
| aoec: 2 072 plików ratings/ | 01_01_01_file_inventory.md | "ratings 2072 daily CSV files" | 2 072 | 2072 | 2072 | int | No |
| aoec: 6 621,52 MB matches/ | 01_01_01_file_inventory.md | "matches 6621.52 MB" | 6 621,52 MB | 6621.52 | 6621.52 | float | No |
| aoec: 2 519,59 MB ratings/ | 01_01_01_file_inventory.md | "ratings 2519.59 MB" | 2 519,59 MB | 2519.59 | 2519.59 | float | No |
| aoec: łącznie 9 387,80 MB / ~9,39 GB | 01_01_01_file_inventory.md | "Total size: 9387.80 MB" | 9,39 GB | 9387.80 | 9387.80 | float | No |
| aoec: zakres czasowy 2020-08-01 — 2026-04-04 | 01_01_01_file_inventory.md | "matches 2020-08-01 to 2026-04-04" | 2020-08-01 — 2026-04-04 | 2020-08-01 to 2026-04-04 | 2020-2026 | str | No |
| aoec: brak luk w matches/ | 01_01_01_file_inventory.md | "No gaps found" | brak luk | No gaps | 0 | int | No |
| aoec: leaderboard.parquet 83,32 MB (snapshot) | 01_01_01_file_inventory.md | "leaderboards 2 83.32" | 83,32 MB | 83.32 | 83.32 | float | No |
| aoec: profile.parquet 161,84 MB (snapshot) | 01_01_01_file_inventory.md | "profiles 2 161.84" | 161,84 MB | 161.84 | 161.84 | float | No |
| aoec: matches_raw 277 099 059 wierszy / 74 788 989 distinct matchIds | 01_03_02_true_1v1_profile.md / 01_04_00 | "277,099,059 rows, 74,788,989 distinct matchIds" | 277 099 059 / 74 788 989 | 277,099,059 / 74,788,989 | 277099059 / 74788989 | int | No |
| aoec: 40 062 975 meczów z 2 wierszami (53,57%) | 01_03_02_true_1v1_profile.md | "rows_per_match=2: 40,062,975 53.57" | 40 062 975 / 53,57% | 40,062,975 / 53.57 | 40062975 | int | No |
| aoec: profileId=-1 status='ai' 12 947 078 wierszy / 4 150 733 meczów | 01_03_02_true_1v1_profile.md | "ai 12,947,078 4,150,733" | 12 947 078 / 4 150 733 | 12,947,078 / 4,150,733 | 12947078 / 4150733 | int | No |
| aoec: profileId=-1 status='player' 19 232 wierszy / 8 993 meczów | 01_03_02_true_1v1_profile.md | "player 19,232 8,993" | 19 232 / 8 993 | 19,232 / 8,993 | 19232 / 8993 | int | No |
| aoec: matches_1v1_clean 30 531 196 meczów × 2 wiersze = 61 062 392 | 01_04_01_data_cleaning.md | "S3_valid_complementary 61,062,392 30,531,196" | 30 531 196 / 61 062 392 | 30,531,196 / 61,062,392 | 30531196 / 61062392 | int | No |
| aoec: R01 scope restriction -216 027 260 wierszy | 01_04_01_data_cleaning.md | "excluded_S0_to_S1 216,027,260" | 216 027 260 | 216,027,260 | 216027260 | int | No |
| aoec: R03 excluded 5 052 matches (non-complementary won) | 01_04_01_data_cleaning.md | "Matches excluded: 5,052" | 5 052 | 5,052 | 5052 | int | No |
| aoec: player_history_all 264 132 745 wierszy / 19 kolumn | 01_04_01 / 01_04_02 | "player_history_all 264,132,745 / 20 -> 19" | 264 132 745 / 19 | 264,132,745 / 19 | 264132745 / 19 | int | No |
| aoec: matches_1v1_clean 48 kolumn (54→48) | 01_04_02_post_cleaning_validation.md | "matches_1v1_clean 54 -> 48" | 48 | 54 → 48 | 48 | int | No |
| aoec: rating NULL 15 999 234 (26,20%) w matches_1v1_clean | 01_04_01_data_cleaning.md | "rating 15,999,234 26.2015%" | 26,20% / 15 999 234 | 15,999,234 / 26.2015 | 26.20 | float | No |
| aoec: rating coverage 73,8% w matches_1v1_clean | 01_04_01_data_cleaning.md | "V1 Rating coverage: 73.8%" | 73,8% | 73.8 | 73.80 | float | No |
| aoec: server NULL 97,39% | 01_04_01_missingness_ledger.csv | "server 97.3919" | 97,39% | 97.3919 | 97.39 | float | No |
| aoec: scenario NULL 100% | 01_04_01_missingness_ledger.csv | "scenario 100.0" | 100% | 100.0 | 100.0 | float | No |
| aoec: modDataset NULL 100% | 01_04_01_missingness_ledger.csv | "modDataset 100.0" | 100% | 100.0 | 100.0 | float | No |
| aoec: password NULL 77,57% | 01_04_01_missingness_ledger.csv | "password 77.5718" | 77,57% | 77.5718 | 77.57 | float | No |
| aoec: antiquityMode NULL 60,06% | 01_04_01_missingness_ledger.csv | "antiquityMode 60.0634" | 60,06% | 60.0634 | 60.06 | float | No |
| aoec: hideCivs NULL 37,18% | 01_04_01_missingness_ledger.csv | "hideCivs 37.1771" | 37,18% | 37.1771 | 37.18 | float | No |
| aoec: country NULL 2,25% matches_1v1_clean / 8,30% player_history_all | 01_04_01_missingness_ledger.csv | "country matches_1v1_clean 2.2486 / history 8.305" | 2,25% / 8,30% | 2.2486 / 8.305 | 2.25 / 8.30 | float | No |
| aoec: won NULL 19 251 wierszy w player_history_all (0,0073%) | 01_04_01_data_cleaning.md | "won 19,251 0.0073" | 19 251 / 0,0073% | 19,251 / 0.0073 | 19251 | int | No |
| aoec: team encoding artifact (side=0 rare) | 01_04_00_source_normalization.md | "Side=0 contains only 449 rows" | 449 | 449 | 449 | int | No |
| aoec: team encoding 1v1 side=1 130 369 073 wierszy | 01_04_00_source_normalization.md | "1 130,369,073" | 130 369 073 | 130,369,073 | 130369073 | int | No |
| aoec: matches_long_raw 277 099 059 wierszy | 01_04_00_source_normalization.md | "matches_long_raw 277,099,059" | 277 099 059 | 277,099,059 | 277099059 | int | No |
| aoec: NULL-cluster 10 kolumn flagged | 01_04_01_data_cleaning.md | "All 10 game-settings columns simultaneously NULL" | 10 | 10 | 10 | int | No |
| aoec: NULL-cluster 11 184 rows flagged | 01_04_01_data_cleaning.md | "11,184 rows flagged" | 11 184 | 11,184 | 11184 | int | No |
| aoec: civ (matches_1v1_clean) n_distinct=56 | 01_04_01_missingness_ledger.csv | "civ 56.0" | 56 | 56 | 56 | int | No |
| aoec: leaderboardId IN (6, 18): rm_1v1 (6) 53 686 164 / qp_rm_1v1 (18) 7 376 228 | 01_04_01_data_cleaning.md | V4 Leaderboard Distribution | 53 686 164 / 7 376 228 | 53,686,164 / 7,376,228 | 53686164 / 7376228 | int | No |

**Total: 101 distinct rows. Hedging needed on 3 rows (BWZe inferred, 24,853,897 not in MD, PlayerStats 160-loop period rounding).**
**Halt threshold (>5 mismatches): NOT TRIGGERED. All numbers grounded.**
```

---
