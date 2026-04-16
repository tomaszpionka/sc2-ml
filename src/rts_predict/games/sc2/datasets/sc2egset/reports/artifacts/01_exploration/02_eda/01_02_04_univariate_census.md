# Step 01_02_04 -- Metadata STRUCT Extraction & Replay-Level EDA

**Dataset:** sc2egset
**Generated:** 2026-04-15 22:27

---

## Section A: STRUCT Field Extraction

```sql
SELECT
    details.gameSpeed AS game_speed,
    details.isBlizzardMap AS is_blizzard_map,
    details.timeUTC AS time_utc,
    header.elapsedGameLoops AS elapsed_game_loops,
    header."version" AS game_version_header,
    metadata.baseBuild AS base_build,
    metadata.dataBuild AS data_build,
    metadata.gameVersion AS game_version_meta,
    metadata.mapName AS map_name,
    initData.gameDescription.maxPlayers AS max_players,
    initData.gameDescription.gameSpeed AS game_speed_init,
    initData.gameDescription.isBlizzardMap AS is_blizzard_map_init,
    initData.gameDescription.mapSizeX AS map_size_x,
    initData.gameDescription.mapSizeY AS map_size_y,
    gameEventsErr,
    messageEventsErr,
    trackerEvtsErr,
    filename
FROM replays_meta_raw
```

Result shape: (22390, 18)

## Database Memory Footprint

DuckDB file size: 12,333,056 bytes (11.76 MB)

## Section B: Full NULL Census

### replay_players_raw

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(filename) AS filename_null,
    COUNT(*) - COUNT(toon_id) AS toon_id_null,
    COUNT(*) - COUNT(nickname) AS nickname_null,
    COUNT(*) - COUNT(playerID) AS playerID_null,
    COUNT(*) - COUNT(userID) AS userID_null,
    COUNT(*) - COUNT(isInClan) AS isInClan_null,
    COUNT(*) - COUNT(clanTag) AS clanTag_null,
    COUNT(*) - COUNT(MMR) AS MMR_null,
    COUNT(*) - COUNT(race) AS race_null,
    COUNT(*) - COUNT(selectedRace) AS selectedRace_null,
    COUNT(*) - COUNT(handicap) AS handicap_null,
    COUNT(*) - COUNT(region) AS region_null,
    COUNT(*) - COUNT(realm) AS realm_null,
    COUNT(*) - COUNT(highestLeague) AS highestLeague_null,
    COUNT(*) - COUNT(result) AS result_null,
    COUNT(*) - COUNT(APM) AS APM_null,
    COUNT(*) - COUNT(SQ) AS SQ_null,
    COUNT(*) - COUNT(supplyCappedPercent) AS supplyCappedPercent_null,
    COUNT(*) - COUNT(startDir) AS startDir_null,
    COUNT(*) - COUNT(startLocX) AS startLocX_null,
    COUNT(*) - COUNT(startLocY) AS startLocY_null,
    COUNT(*) - COUNT(color_a) AS color_a_null,
    COUNT(*) - COUNT(color_b) AS color_b_null,
    COUNT(*) - COUNT(color_g) AS color_g_null,
    COUNT(*) - COUNT(color_r) AS color_r_null
FROM replay_players_raw
```

| column              |   null_count |   null_pct |
|:--------------------|-------------:|-----------:|
| filename            |            0 |          0 |
| highestLeague       |            0 |          0 |
| color_g             |            0 |          0 |
| color_b             |            0 |          0 |
| color_a             |            0 |          0 |
| startLocY           |            0 |          0 |
| startLocX           |            0 |          0 |
| startDir            |            0 |          0 |
| supplyCappedPercent |            0 |          0 |
| SQ                  |            0 |          0 |
| APM                 |            0 |          0 |
| result              |            0 |          0 |
| realm               |            0 |          0 |
| toon_id             |            0 |          0 |
| region              |            0 |          0 |
| handicap            |            0 |          0 |
| selectedRace        |            0 |          0 |
| race                |            0 |          0 |
| MMR                 |            0 |          0 |
| clanTag             |            0 |          0 |
| isInClan            |            0 |          0 |
| userID              |            0 |          0 |
| playerID            |            0 |          0 |
| nickname            |            0 |          0 |
| color_r             |            0 |          0 |

### replays_meta_raw.filename

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(filename) AS filename_null,
    ROUND(100.0 * (COUNT(*) - COUNT(filename)) / COUNT(*), 2) AS filename_null_pct
FROM replays_meta_raw
```

|   total_rows |   filename_null |   filename_null_pct |
|-------------:|----------------:|--------------------:|
|        22390 |               0 |                   0 |

### struct_flat NULL census

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(time_utc) AS time_utc_null,
    COUNT(*) - COUNT(elapsed_game_loops) AS elapsed_game_loops_null,
    COUNT(*) - COUNT(game_version_header) AS game_version_header_null,
    COUNT(*) - COUNT(base_build) AS base_build_null,
    COUNT(*) - COUNT(data_build) AS data_build_null,
    COUNT(*) - COUNT(game_version_meta) AS game_version_meta_null,
    COUNT(*) - COUNT(map_name) AS map_name_null,
    COUNT(*) - COUNT(max_players) AS max_players_null,
    COUNT(*) - COUNT(game_speed) AS game_speed_null,
    COUNT(*) - COUNT(game_speed_init) AS game_speed_init_null,
    COUNT(*) - COUNT(is_blizzard_map) AS is_blizzard_map_null,
    COUNT(*) - COUNT(is_blizzard_map_init) AS is_blizzard_map_init_null,
    COUNT(*) - COUNT(map_size_x) AS map_size_x_null,
    COUNT(*) - COUNT(map_size_y) AS map_size_y_null,
    COUNT(*) - COUNT(gameEventsErr) AS gameEventsErr_null,
    COUNT(*) - COUNT(messageEventsErr) AS messageEventsErr_null,
    COUNT(*) - COUNT(trackerEvtsErr) AS trackerEvtsErr_null
FROM struct_flat
```

| column               |   null_count |   null_pct |
|:---------------------|-------------:|-----------:|
| time_utc             |            0 |          0 |
| game_speed_init      |            0 |          0 |
| messageEventsErr     |            0 |          0 |
| gameEventsErr        |            0 |          0 |
| map_size_y           |            0 |          0 |
| map_size_x           |            0 |          0 |
| is_blizzard_map_init |            0 |          0 |
| is_blizzard_map      |            0 |          0 |
| game_speed           |            0 |          0 |
| elapsed_game_loops   |            0 |          0 |
| max_players          |            0 |          0 |
| map_name             |            0 |          0 |
| game_version_meta    |            0 |          0 |
| data_build           |            0 |          0 |
| base_build           |            0 |          0 |
| game_version_header  |            0 |          0 |
| trackerEvtsErr       |            0 |          0 |

### struct_flat completeness note

All 17 struct_flat columns have 0 NULLs. No missingness co-occurrence to analyze.

## Section C: Target Variable

```sql
SELECT result, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM replay_players_raw
GROUP BY result
ORDER BY cnt DESC
```

| result    |   cnt |   pct |
|:----------|------:|------:|
| Loss      | 22409 | 50    |
| Win       | 22382 | 49.94 |
| Undecided |    24 |  0.05 |
| Tie       |     2 |  0    |

### Non-2-player replay results

```sql
SELECT rp.result, COUNT(*) AS cnt
FROM replay_players_raw rp
JOIN replays_meta_raw rm ON rp.filename = rm.filename
WHERE rm.initData.gameDescription.maxPlayers != 2
   OR rm.filename IN (
       SELECT filename FROM replay_players_raw
       GROUP BY filename HAVING COUNT(*) != 2
   )
GROUP BY rp.result
ORDER BY cnt DESC
```

| result   |   cnt |
|:---------|------:|
| Loss     |   444 |
| Win      |   417 |

### Undecided/Tie replay context (corrective query)

```sql
SELECT
    rp.result,
    rp.filename,
    rm.initData.gameDescription.maxPlayers AS max_players,
    player_counts.player_row_count
FROM replay_players_raw rp
LEFT JOIN replays_meta_raw rm ON rp.filename = rm.filename
JOIN (
    SELECT filename, COUNT(*) AS player_row_count
    FROM replay_players_raw
    GROUP BY filename
) player_counts ON rp.filename = player_counts.filename
WHERE rp.result IN ('Undecided', 'Tie')
ORDER BY rp.result, rp.filename
```

| result    | filename                                                                                                                                   |   max_players |   player_row_count |
|:----------|:-------------------------------------------------------------------------------------------------------------------------------------------|--------------:|-------------------:|
| Tie       | 2022_Dreamhack_SC2_Masters_Valencia/2022_Dreamhack_SC2_Masters_Valencia_data/cab0125665bd7ccf10270d10cf214463.SC2Replay.json               |             2 |                  2 |
| Tie       | 2022_Dreamhack_SC2_Masters_Valencia/2022_Dreamhack_SC2_Masters_Valencia_data/cab0125665bd7ccf10270d10cf214463.SC2Replay.json               |             2 |                  2 |
| Undecided | 2017_WESG_Barcelona/2017_WESG_Barcelona_data/d71ff1dbe2f741f150d9baeee55346b9.SC2Replay.json                                               |             2 |                  2 |
| Undecided | 2017_WESG_Barcelona/2017_WESG_Barcelona_data/d71ff1dbe2f741f150d9baeee55346b9.SC2Replay.json                                               |             2 |                  2 |
| Undecided | 2018_HomeStory_Cup_XVII/2018_HomeStory_Cup_XVII_data/5f058ca29de7ffa86d82064bc990834f.SC2Replay.json                                       |             2 |                  2 |
| Undecided | 2018_HomeStory_Cup_XVII/2018_HomeStory_Cup_XVII_data/5f058ca29de7ffa86d82064bc990834f.SC2Replay.json                                       |             2 |                  2 |
| Undecided | 2018_IEM_Katowice/2018_IEM_Katowice_data/6b31fbc28a82b0f86468ff4bd2f1b805.SC2Replay.json                                                   |             2 |                  2 |
| Undecided | 2018_IEM_Katowice/2018_IEM_Katowice_data/6b31fbc28a82b0f86468ff4bd2f1b805.SC2Replay.json                                                   |             2 |                  2 |
| Undecided | 2018_WCS_Leipzig/2018_WCS_Leipzig_data/f259535a56778d1e8bf0a1929a385beb.SC2Replay.json                                                     |             2 |                  2 |
| Undecided | 2018_WCS_Leipzig/2018_WCS_Leipzig_data/f259535a56778d1e8bf0a1929a385beb.SC2Replay.json                                                     |             2 |                  2 |
| Undecided | 2018_WCS_Valencia/2018_WCS_Valencia_data/2cac85d113fa17f1d93f205cd0761200.SC2Replay.json                                                   |             2 |                  2 |
| Undecided | 2018_WCS_Valencia/2018_WCS_Valencia_data/2cac85d113fa17f1d93f205cd0761200.SC2Replay.json                                                   |             2 |                  2 |
| Undecided | 2019_HomeStory_Cup_XIX/2019_HomeStory_Cup_XIX_data/6dfa603380ce2b5a7519fb930f95722f.SC2Replay.json                                         |             2 |                  2 |
| Undecided | 2019_HomeStory_Cup_XIX/2019_HomeStory_Cup_XIX_data/6dfa603380ce2b5a7519fb930f95722f.SC2Replay.json                                         |             2 |                  2 |
| Undecided | 2019_IEM_Katowice/2019_IEM_Katowice_data/ca15f60729b21ff6d79d3d50d83126e9.SC2Replay.json                                                   |             2 |                  2 |
| Undecided | 2019_IEM_Katowice/2019_IEM_Katowice_data/ca15f60729b21ff6d79d3d50d83126e9.SC2Replay.json                                                   |             2 |                  2 |
| Undecided | 2020_Dreamhack_SC2_Masters_Fall/2020_Dreamhack_SC2_Masters_Fall_data/ed7d0c672db2e16c3780886a8dab8425.SC2Replay.json                       |             2 |                  2 |
| Undecided | 2020_Dreamhack_SC2_Masters_Fall/2020_Dreamhack_SC2_Masters_Fall_data/ed7d0c672db2e16c3780886a8dab8425.SC2Replay.json                       |             2 |                  2 |
| Undecided | 2020_Dreamhack_SC2_Masters_Summer/2020_Dreamhack_SC2_Masters_Summer_data/8c32501ae0ec4cfaecd8d1b44faeeea3.SC2Replay.json                   |             2 |                  2 |
| Undecided | 2020_Dreamhack_SC2_Masters_Summer/2020_Dreamhack_SC2_Masters_Summer_data/8c32501ae0ec4cfaecd8d1b44faeeea3.SC2Replay.json                   |             2 |                  2 |
| Undecided | 2021_ASUS_ROG_Fall/2021_ASUS_ROG_Fall_data/0b659be670879662b5f2c4fd6f17a528.SC2Replay.json                                                 |             2 |                  2 |
| Undecided | 2021_ASUS_ROG_Fall/2021_ASUS_ROG_Fall_data/0b659be670879662b5f2c4fd6f17a528.SC2Replay.json                                                 |             2 |                  2 |
| Undecided | 2021_Cheeseadelphia_Winter_Championship/2021_Cheeseadelphia_Winter_Championship_data/1b5eefedd2d017fa8ff8bacbd1bc51fb.SC2Replay.json       |             2 |                  2 |
| Undecided | 2021_Cheeseadelphia_Winter_Championship/2021_Cheeseadelphia_Winter_Championship_data/1b5eefedd2d017fa8ff8bacbd1bc51fb.SC2Replay.json       |             2 |                  2 |
| Undecided | 2022_Dreamhack_SC2_Masters_Last_Chance2021/2022_Dreamhack_SC2_Masters_Last_Chance2021_data/07ac0d02e1ae65efb2c08f04066d2212.SC2Replay.json |             2 |                  2 |
| Undecided | 2022_Dreamhack_SC2_Masters_Last_Chance2021/2022_Dreamhack_SC2_Masters_Last_Chance2021_data/07ac0d02e1ae65efb2c08f04066d2212.SC2Replay.json |             2 |                  2 |

Finding: All 26 rows (Undecided and Tie) came from replays with player_row_count=[2] and max_players=[2].

Note: The OR-condition non-2-player query above returned only Win/Loss. Undecided/Tie rows are present in standard 2-player replays per this corrective query.

## Section D: Categorical Field Profiles

### race

```sql
SELECT race, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM replay_players_raw
GROUP BY race
ORDER BY cnt DESC
```

| race   |   cnt |   pct |
|:-------|------:|------:|
| Prot   | 16228 | 36.21 |
| Zerg   | 15695 | 35.02 |
| Terr   | 12891 | 28.76 |
| BWTe   |     1 |  0    |
| BWZe   |     1 |  0    |
| BWPr   |     1 |  0    |

### selectedRace

```sql
SELECT selectedRace, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM replay_players_raw
GROUP BY selectedRace
ORDER BY cnt DESC
```

| selectedRace   |   cnt |   pct |
|:---------------|------:|------:|
| Prot           | 15948 | 35.58 |
| Zerg           | 15123 | 33.74 |
| Terr           | 12623 | 28.17 |
|                |  1110 |  2.48 |
| Rand           |    10 |  0.02 |
| BWTe           |     1 |  0    |
| BWZe           |     1 |  0    |
| BWPr           |     1 |  0    |

### highestLeague

```sql
SELECT highestLeague, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM replay_players_raw
GROUP BY highestLeague
ORDER BY cnt DESC
```

| highestLeague   |   cnt |   pct |
|:----------------|------:|------:|
| Unknown         | 32338 | 72.16 |
| Master          |  6458 | 14.41 |
| Grandmaster     |  4745 | 10.59 |
| Diamond         |   718 |  1.6  |
| Unranked        |   224 |  0.5  |
| Platinum        |   131 |  0.29 |
| Gold            |   119 |  0.27 |
| Bronze          |    73 |  0.16 |
| Silver          |     9 |  0.02 |
|                 |     2 |  0    |

### region

```sql
SELECT region, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM replay_players_raw
GROUP BY region
ORDER BY cnt DESC
```

| region   |   cnt |   pct |
|:---------|------:|------:|
| Europe   | 21022 | 46.91 |
| US       | 12699 | 28.34 |
| Unknown  |  5748 | 12.83 |
| Korea    |  3604 |  8.04 |
| China    |  1742 |  3.89 |
|          |     2 |  0    |

### realm

```sql
SELECT realm, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM replay_players_raw
GROUP BY realm
ORDER BY cnt DESC
```

| realm         |   cnt |   pct |
|:--------------|------:|------:|
| Europe        | 20777 | 46.36 |
| North America | 12490 | 27.87 |
| Unknown       |  5748 | 12.83 |
| Korea         |  2835 |  6.33 |
| China         |  1742 |  3.89 |
| Taiwan        |   769 |  1.72 |
| Russia        |   245 |  0.55 |
| Latin America |   209 |  0.47 |
|               |     2 |  0    |

### isInClan distribution

```sql
SELECT
    isInClan,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM replay_players_raw
GROUP BY isInClan
ORDER BY cnt DESC
```

| isInClan   |   cnt |   pct |
|:-----------|------:|------:|
| False      | 33210 |  74.1 |
| True       | 11607 |  25.9 |

### clanTag top-20

```sql
SELECT
    clanTag,
    COUNT(*) AS cnt,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct_of_total,
    ROUND(100.0 * COUNT(*) / (
        SELECT COUNT(*) FROM replay_players_raw
        WHERE clanTag != ''
    ), 2) AS pct_of_non_empty
FROM replay_players_raw
WHERE clanTag != ''
GROUP BY clanTag
ORDER BY cnt DESC
LIMIT 20
```

| clanTag   |   cnt |   pct_of_total |   pct_of_non_empty |
|:----------|------:|---------------:|-------------------:|
| αX        |   778 |           6.7  |               6.7  |
| PSISTM    |   532 |           4.58 |               4.58 |
| mouz      |   513 |           4.42 |               4.42 |
| RBLN      |   466 |           4.01 |               4.01 |
| QLASH     |   454 |           3.91 |               3.91 |
| ENCE      |   443 |           3.82 |               3.82 |
| Ex0n      |   322 |           2.77 |               2.77 |
| Kaizi     |   219 |           1.89 |               1.89 |
| mlem      |   214 |           1.84 |               1.84 |
| xkom      |   212 |           1.83 |               1.83 |
| TeamNV    |   197 |           1.7  |               1.7  |
| сSсǃ      |   188 |           1.62 |               1.62 |
| Mkers     |   179 |           1.54 |               1.54 |
| IxGeu     |   170 |           1.46 |               1.46 |
| ROOT      |   162 |           1.4  |               1.4  |
| Ting      |   160 |           1.38 |               1.38 |
| BASKGG    |   157 |           1.35 |               1.35 |
| ASTsc     |   139 |           1.2  |               1.2  |
| St0rmG    |   138 |           1.19 |               1.19 |
| GGGSC2    |   128 |           1.1  |               1.1  |

### game_speed

```sql
SELECT game_speed, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM struct_flat
GROUP BY game_speed
ORDER BY cnt DESC
```

| game_speed   |   cnt |   pct |
|:-------------|------:|------:|
| Faster       | 22390 |   100 |

### game_speed_init

```sql
SELECT game_speed_init, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM struct_flat
GROUP BY game_speed_init
ORDER BY cnt DESC
```

| game_speed_init   |   cnt |   pct |
|:------------------|------:|------:|
| Faster            | 22390 |   100 |

### map_name

```sql
SELECT map_name, COUNT(*) AS cnt
FROM struct_flat
GROUP BY map_name
ORDER BY cnt DESC
LIMIT 20
```

| map_name            |   cnt |
|:--------------------|------:|
| 2000 Atmospheres LE |   966 |
| Acid Plant LE       |   667 |
| Catalyst LE         |   586 |
| Oxide LE            |   570 |
| Romanticide LE      |   568 |
| Eternal Empire LE   |   528 |
| King's Cove LE      |   509 |
| Lightshade LE       |   508 |
| Kairos Junction LE  |   496 |
| Abyssal Reef LE     |   481 |
| Ever Dream LE       |   471 |
| Lost and Found LE   |   461 |
| Jagannatha LE       |   440 |
| Deathaura LE        |   438 |
| Acropolis LE        |   419 |
| Pillars of Gold LE  |   390 |
| [ESL] Data-C        |   387 |
| Port Aleksander LE  |   381 |
| Blackpink LE        |   370 |
| Cyber Forest LE     |   364 |

### game_version_meta

```sql
SELECT game_version_meta, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM struct_flat
GROUP BY game_version_meta
ORDER BY cnt DESC
```

| game_version_meta   |   cnt |   pct |
|:--------------------|------:|------:|
| 5.0.7.84643         |  2511 | 11.21 |
| 5.0.9.87702         |  1094 |  4.89 |
| 5.0.8.86383         |  1071 |  4.78 |
| 5.0.10.88500        |   988 |  4.41 |
| 4.8.3.72282         |   933 |  4.17 |
| 5.0.10.89165        |   865 |  3.86 |
| 5.0.12.91115        |   859 |  3.84 |
| 5.0.11.90136        |   820 |  3.66 |
| 5.0.2.81433         |   799 |  3.57 |
| 4.11.4.78285        |   795 |  3.55 |
| 4.12.0.80188        |   783 |  3.5  |
| 4.9.3.75025         |   765 |  3.42 |
| 4.4.0.65895         |   753 |  3.36 |
| 4.10.2.76052        |   601 |  2.68 |
| 4.8.6.73620         |   540 |  2.41 |
| 4.1.4.61545         |   482 |  2.15 |
| 5.0.6.83830         |   444 |  1.98 |
| 4.2.0.62347         |   444 |  1.98 |
| 4.6.0.67926         |   442 |  1.97 |
| 5.0.13.92174        |   439 |  1.96 |
| 4.10.4.76811        |   428 |  1.91 |
| 4.7.1.70326         |   416 |  1.86 |
| 3.10.1.49957        |   409 |  1.83 |
| 4.3.2.65384         |   406 |  1.81 |
| 3.12.0.51702        |   405 |  1.81 |
| 3.14.0.53644        |   332 |  1.48 |
| 4.9.2.74741         |   330 |  1.47 |
| 3.19.1.58600        |   294 |  1.31 |
| 4.8.2.71663         |   289 |  1.29 |
| 5.0.5.82893         |   278 |  1.24 |
| 5.0.11.89720        |   260 |  1.16 |
| 5.0.13.92440        |   249 |  1.11 |
| 3.1.2.40384         |   241 |  1.08 |
| 4.12.0.79998        |   237 |  1.06 |
| 3.17.1.57218        |   236 |  1.05 |
| 3.16.0.55505        |   188 |  0.84 |
| 5.0.14.93272        |   171 |  0.76 |
| 4.2.1.62848         |   165 |  0.74 |
| 4.0.2.59877         |   135 |  0.6  |
| 5.0.4.82457         |   107 |  0.48 |
| 3.1.1.39948         |   105 |  0.47 |
| 4.6.2.69232         |    72 |  0.32 |
| 3.4.0.44401         |    60 |  0.27 |
| 3.1.3.41128         |    58 |  0.26 |
| 3.1.0.39576         |    49 |  0.22 |
| 3.1.4.41219         |    42 |  0.19 |

### base_build

```sql
SELECT base_build, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM struct_flat
GROUP BY base_build
ORDER BY cnt DESC
```

| base_build   |   cnt |   pct |
|:-------------|------:|------:|
| Base84643    |  2511 | 11.21 |
| Base87702    |  1094 |  4.89 |
| Base86383    |  1071 |  4.78 |
| Base88500    |   988 |  4.41 |
| Base72282    |   933 |  4.17 |
| Base89165    |   865 |  3.86 |
| Base91115    |   859 |  3.84 |
| Base90136    |   820 |  3.66 |
| Base81433    |   799 |  3.57 |
| Base78285    |   795 |  3.55 |
| Base80188    |   783 |  3.5  |
| Base75025    |   765 |  3.42 |
| Base65895    |   753 |  3.36 |
| Base76052    |   601 |  2.68 |
| Base73620    |   540 |  2.41 |
| Base60321    |   482 |  2.15 |
| Base62347    |   444 |  1.98 |
| Base83830    |   444 |  1.98 |
| Base67926    |   442 |  1.97 |
| Base92174    |   439 |  1.96 |
| Base76811    |   428 |  1.91 |
| Base70154    |   416 |  1.86 |
| Base49716    |   409 |  1.83 |
| Base65384    |   406 |  1.81 |
| Base51702    |   405 |  1.81 |
| Base53644    |   332 |  1.48 |
| Base74741    |   330 |  1.47 |
| Base58400    |   294 |  1.31 |
| Base71663    |   289 |  1.29 |
| Base82893    |   278 |  1.24 |
| Base89720    |   260 |  1.16 |
| Base92440    |   249 |  1.11 |
| Base40384    |   241 |  1.08 |
| Base79998    |   237 |  1.06 |
| Base56787    |   236 |  1.05 |
| Base55505    |   188 |  0.84 |
| Base93272    |   171 |  0.76 |
| Base62848    |   165 |  0.74 |
| Base59587    |   135 |  0.6  |
| Base82457    |   107 |  0.48 |
| Base39948    |   105 |  0.47 |
| Base69232    |    72 |  0.32 |
| Base44401    |    60 |  0.27 |
| Base41128    |    58 |  0.26 |
| Base39576    |    49 |  0.22 |
| Base41219    |    42 |  0.19 |

### data_build

```sql
SELECT data_build, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM struct_flat
GROUP BY data_build
ORDER BY cnt DESC
```

|   data_build |   cnt |   pct |
|-------------:|------:|------:|
|        84643 |  2511 | 11.21 |
|        87702 |  1094 |  4.89 |
|        86383 |  1071 |  4.78 |
|        88500 |   988 |  4.41 |
|        72282 |   933 |  4.17 |
|        89165 |   865 |  3.86 |
|        91115 |   859 |  3.84 |
|        90136 |   820 |  3.66 |
|        81433 |   799 |  3.57 |
|        78285 |   795 |  3.55 |
|        80188 |   783 |  3.5  |
|        75025 |   765 |  3.42 |
|        65895 |   753 |  3.36 |
|        76052 |   601 |  2.68 |
|        73620 |   540 |  2.41 |
|        61545 |   482 |  2.15 |
|        62347 |   444 |  1.98 |
|        83830 |   444 |  1.98 |
|        67926 |   442 |  1.97 |
|        92174 |   439 |  1.96 |
|        76811 |   428 |  1.91 |
|        70326 |   416 |  1.86 |
|        49957 |   409 |  1.83 |
|        65384 |   406 |  1.81 |
|        51702 |   405 |  1.81 |
|        53644 |   332 |  1.48 |
|        74741 |   330 |  1.47 |
|        58600 |   294 |  1.31 |
|        71663 |   289 |  1.29 |
|        82893 |   278 |  1.24 |
|        89720 |   260 |  1.16 |
|        92440 |   249 |  1.11 |
|        40384 |   241 |  1.08 |
|        79998 |   237 |  1.06 |
|        57218 |   236 |  1.05 |
|        55505 |   188 |  0.84 |
|        93272 |   171 |  0.76 |
|        62848 |   165 |  0.74 |
|        59877 |   135 |  0.6  |
|        82457 |   107 |  0.48 |
|        39948 |   105 |  0.47 |
|        69232 |    72 |  0.32 |
|        44401 |    60 |  0.27 |
|        41128 |    58 |  0.26 |
|        39576 |    49 |  0.22 |
|        41219 |    42 |  0.19 |

### Game Speed Assertion

```python
assert set(speed_counts["game_speed"].dropna()) == {"Faster"}
```

**PASSED** -- all replays confirmed Faster speed.

## Section E: Numeric Descriptive Statistics

Note: APM, SQ, and supplyCappedPercent are in-game-only fields. See `field_classification` in the JSON artifact for the full pre-game/in-game/post-game/identifier/target/constant taxonomy.

### MMR

```sql
SELECT
    MIN(MMR) AS min_val, MAX(MMR) AS max_val,
    ROUND(AVG(MMR), 2) AS mean_val,
    ROUND(MEDIAN(MMR), 2) AS median_val,
    ROUND(STDDEV(MMR), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY MMR) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY MMR) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY MMR) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY MMR) AS p95
FROM replay_players_raw
WHERE MMR IS NOT NULL
```

|   min_val |   max_val |   mean_val |   median_val |   stddev_val |   p05 |   p25 |   p75 |   p95 |
|----------:|----------:|-----------:|-------------:|-------------:|------:|------:|------:|------:|
|    -36400 |      7464 |     738.71 |            0 |      3035.53 |     0 |     0 |     0 |  6493 |

### APM

```sql
SELECT
    MIN(APM) AS min_val, MAX(APM) AS max_val,
    ROUND(AVG(APM), 2) AS mean_val,
    ROUND(MEDIAN(APM), 2) AS median_val,
    ROUND(STDDEV(APM), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY APM) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY APM) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY APM) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY APM) AS p95
FROM replay_players_raw
WHERE APM IS NOT NULL
```

|   min_val |   max_val |   mean_val |   median_val |   stddev_val |   p05 |   p25 |   p75 |   p95 |
|----------:|----------:|-----------:|-------------:|-------------:|------:|------:|------:|------:|
|         0 |      1248 |     355.57 |          349 |       104.87 |   219 |   303 |   410 |   523 |

### SQ

```sql
SELECT
    MIN(SQ) AS min_val, MAX(SQ) AS max_val,
    ROUND(AVG(SQ), 2) AS mean_val,
    ROUND(MEDIAN(SQ), 2) AS median_val,
    ROUND(STDDEV(SQ), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY SQ) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY SQ) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY SQ) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY SQ) AS p95
FROM replay_players_raw
WHERE SQ IS NOT NULL
```

|      min_val |   max_val |   mean_val |   median_val |   stddev_val |   p05 |   p25 |   p75 |   p95 |
|-------------:|----------:|-----------:|-------------:|-------------:|------:|------:|------:|------:|
| -2.14748e+09 |       187 |   -95711.1 |          123 |  1.43456e+07 |    91 |   110 |   136 |   152 |

### supplyCappedPercent

```sql
SELECT
    MIN(supplyCappedPercent) AS min_val, MAX(supplyCappedPercent) AS max_val,
    ROUND(AVG(supplyCappedPercent), 2) AS mean_val,
    ROUND(MEDIAN(supplyCappedPercent), 2) AS median_val,
    ROUND(STDDEV(supplyCappedPercent), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY supplyCappedPercent) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY supplyCappedPercent) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY supplyCappedPercent) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY supplyCappedPercent) AS p95
FROM replay_players_raw
WHERE supplyCappedPercent IS NOT NULL
```

|   min_val |   max_val |   mean_val |   median_val |   stddev_val |   p05 |   p25 |   p75 |   p95 |
|----------:|----------:|-----------:|-------------:|-------------:|------:|------:|------:|------:|
|         0 |       100 |       7.24 |            6 |         4.71 |     2 |     4 |     9 |    16 |

### handicap

```sql
SELECT
    MIN(handicap) AS min_val, MAX(handicap) AS max_val,
    ROUND(AVG(handicap), 2) AS mean_val,
    ROUND(MEDIAN(handicap), 2) AS median_val,
    ROUND(STDDEV(handicap), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY handicap) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY handicap) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY handicap) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY handicap) AS p95
FROM replay_players_raw
WHERE handicap IS NOT NULL
```

|   min_val |   max_val |   mean_val |   median_val |   stddev_val |   p05 |   p25 |   p75 |   p95 |
|----------:|----------:|-----------:|-------------:|-------------:|------:|------:|------:|------:|
|         0 |       100 |        100 |          100 |         0.67 |   100 |   100 |   100 |   100 |

### elapsed_game_loops (duration)

```sql
SELECT
    MIN(elapsed_game_loops) AS min_val,
    MAX(elapsed_game_loops) AS max_val,
    ROUND(AVG(elapsed_game_loops), 2) AS mean_val,
    ROUND(MEDIAN(elapsed_game_loops), 2) AS median_val,
    ROUND(STDDEV(elapsed_game_loops), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY elapsed_game_loops) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY elapsed_game_loops) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY elapsed_game_loops) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY elapsed_game_loops) AS p95,
    ROUND(MIN(elapsed_game_loops) / 22.4, 2) AS min_seconds,
    ROUND(MAX(elapsed_game_loops) / 22.4, 2) AS max_seconds,
    ROUND(AVG(elapsed_game_loops) / 22.4, 2) AS mean_seconds,
    ROUND(MEDIAN(elapsed_game_loops) / 22.4, 2) AS median_seconds
FROM struct_flat
WHERE elapsed_game_loops IS NOT NULL
```

|   min_val |   max_val |   mean_val |   median_val |   stddev_val |     p05 |     p25 |     p75 |     p95 |   min_seconds |   max_seconds |   mean_seconds |   median_seconds |
|----------:|----------:|-----------:|-------------:|-------------:|--------:|--------:|--------:|--------:|--------------:|--------------:|---------------:|-----------------:|
|        12 |    136028 |    16105.3 |        14580 |      7795.59 | 6640.45 | 11111.2 | 19390.8 | 30270.1 |          0.54 |       6072.68 |         718.98 |           650.89 |

### Map Dimensions

```sql
SELECT
    map_size_x, map_size_y, COUNT(*) AS cnt
FROM struct_flat
GROUP BY map_size_x, map_size_y
ORDER BY cnt DESC
```

|   map_size_x |   map_size_y |   cnt |
|-------------:|-------------:|------:|
|          168 |          184 |  1624 |
|          176 |          176 |  1615 |
|          176 |          184 |  1052 |
|          160 |          168 |  1030 |
|          224 |          224 |   966 |
|          192 |          208 |   886 |
|          216 |          216 |   868 |
|          168 |          168 |   858 |
|          184 |          184 |   800 |
|          200 |          176 |   783 |
|          152 |          168 |   765 |
|          200 |          184 |   754 |
|          184 |          176 |   727 |
|          168 |          176 |   617 |
|          192 |          176 |   612 |
|          200 |          192 |   583 |
|          192 |          192 |   528 |
|          200 |          216 |   471 |
|          184 |          168 |   465 |
|          144 |          160 |   459 |
|          200 |          200 |   449 |
|          168 |          200 |   441 |
|          184 |          144 |   394 |
|          176 |          160 |   384 |
|          192 |          168 |   362 |
|          176 |          152 |   309 |
|          192 |          184 |   308 |
|          208 |          208 |   304 |
|          184 |          192 |   287 |
|          216 |          192 |   276 |
|            0 |            0 |   273 |
|          168 |          160 |   260 |
|          160 |          176 |   209 |
|          160 |          184 |   208 |
|          152 |          152 |   197 |
|          224 |          168 |   169 |
|          248 |          224 |   160 |
|          208 |          168 |   155 |
|          152 |          160 |   154 |
|          200 |          168 |   113 |
|          224 |          192 |    81 |
|          144 |          176 |    69 |
|          184 |          208 |    66 |
|          152 |          184 |    39 |
|          224 |          184 |    38 |
|          176 |          168 |    32 |
|          168 |          192 |    31 |
|          168 |          152 |    30 |
|          224 |          160 |    27 |
|          192 |          128 |    24 |
|          152 |          208 |    18 |
|          200 |            0 |    17 |
|          160 |          152 |    17 |
|          208 |          200 |     7 |
|          136 |          208 |     6 |
|          168 |          144 |     4 |
|          160 |          208 |     3 |
|          136 |          160 |     3 |
|          248 |            0 |     2 |
|          200 |          224 |     1 |

### SQ stats excluding INT32_MIN sentinel

```sql
SELECT
    MIN(SQ) AS min_val,
    MAX(SQ) AS max_val,
    ROUND(AVG(SQ), 2) AS mean_val,
    ROUND(MEDIAN(SQ), 2) AS median_val,
    ROUND(STDDEV(SQ), 2) AS stddev_val,
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY SQ) AS p05,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY SQ) AS p25,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY SQ) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY SQ) AS p95,
    COUNT(*) AS n_rows
FROM replay_players_raw
WHERE SQ IS NOT NULL AND SQ != -2147483648
```

|   min_val |   max_val |   mean_val |   median_val |   stddev_val |   p05 |   p25 |   p75 |   p95 |   n_rows |
|----------:|----------:|-----------:|-------------:|-------------:|------:|------:|------:|------:|---------:|
|       -51 |       187 |     122.38 |          123 |        18.91 |    91 |   110 |   136 |   152 |    44815 |

The main SQ descriptive statistics (Section E) are contaminated by 2 rows containing the INT32_MIN sentinel value (-2147483648). The stats above exclude those rows. The sentinel causes the main SQ mean and stddev to be misleading. Refer to the sentinel-excluded stats above for the clean SQ distribution's actual median and range.

## Section E1: Skewness and Kurtosis (EDA Manual 3.1)

SQL template (one query per column):

```sql
SELECT
    ROUND(SKEWNESS({col}), 4) AS skewness,
    ROUND(KURTOSIS({col}), 4) AS kurtosis
FROM {table}
WHERE {col} IS NOT NULL
```

| column              |   skewness |   kurtosis |
|:--------------------|-----------:|-----------:|
| MMR                 |    -5.759  |    77.8914 |
| APM                 |    -0.2024 |     3.6247 |
| SQ                  |  -149.69   | 22406      |
| supplyCappedPercent |     2.2456 |    18.1756 |
| handicap            |  -149.69   | 22406      |
| startDir            |    -0.0206 |    -1.3235 |
| startLocX           |     0.0563 |    -1.7766 |
| startLocY           |     0.0527 |    -1.7663 |
| color_a             |  -149.69   | 22406      |
| color_b             |     0.0025 |    -1.9367 |
| color_g             |     2.1054 |     7.8214 |
| color_r             |     0.0429 |    -1.9807 |
| playerID            |     0.6305 |     5.2759 |
| userID              |     1.2019 |     1.6383 |
| elapsed_game_loops  |     2.0331 |    10.6597 |

## Section E2: Zero Counts (EDA Manual 3.1)

### replay_players_raw zero counts

```sql
SELECT
    COUNT(*) FILTER (WHERE MMR = 0) AS MMR_zero,
    COUNT(*) FILTER (WHERE APM = 0) AS APM_zero,
    COUNT(*) FILTER (WHERE SQ = 0) AS SQ_zero,
    COUNT(*) FILTER (WHERE SQ = -2147483648) AS SQ_sentinel,
    COUNT(*) FILTER (WHERE supplyCappedPercent = 0) AS supplyCappedPercent_zero,
    COUNT(*) FILTER (WHERE handicap = 0) AS handicap_zero,
    COUNT(*) FILTER (WHERE startDir = 0) AS startDir_zero,
    COUNT(*) FILTER (WHERE startLocX = 0) AS startLocX_zero,
    COUNT(*) FILTER (WHERE startLocY = 0) AS startLocY_zero,
    COUNT(*) FILTER (WHERE color_a = 0) AS color_a_zero,
    COUNT(*) FILTER (WHERE color_b = 0) AS color_b_zero,
    COUNT(*) FILTER (WHERE color_g = 0) AS color_g_zero,
    COUNT(*) FILTER (WHERE color_r = 0) AS color_r_zero,
    COUNT(*) FILTER (WHERE playerID = 0) AS playerID_zero,
    COUNT(*) FILTER (WHERE userID = 0) AS userID_zero
FROM replay_players_raw
```

|   MMR_zero |   APM_zero |   SQ_zero |   SQ_sentinel |   supplyCappedPercent_zero |   handicap_zero |   startDir_zero |   startLocX_zero |   startLocY_zero |   color_a_zero |   color_b_zero |   color_g_zero |   color_r_zero |   playerID_zero |   userID_zero |
|-----------:|-----------:|----------:|--------------:|---------------------------:|----------------:|----------------:|-----------------:|-----------------:|---------------:|---------------:|---------------:|---------------:|----------------:|--------------:|
|      37489 |       1132 |         0 |             2 |                        298 |               2 |               5 |                5 |                5 |              2 |          21191 |            547 |            530 |               0 |          8611 |

### elapsed_game_loops zero count

```sql
SELECT
    COUNT(*) FILTER (WHERE elapsed_game_loops = 0) AS elapsed_game_loops_zero
FROM struct_flat
```

|   elapsed_game_loops_zero |
|--------------------------:|
|                         0 |

### MMR zero-spike interpretation

```sql
SELECT
    result,
    COUNT(*) FILTER (WHERE MMR = 0) AS mmr_zero_cnt,
    COUNT(*) AS total_cnt,
    ROUND(100.0 * COUNT(*) FILTER (WHERE MMR = 0) / COUNT(*), 2)
        AS mmr_zero_pct
FROM replay_players_raw
GROUP BY result
ORDER BY total_cnt DESC
```

| result    |   mmr_zero_cnt |   total_cnt |   mmr_zero_pct |
|:----------|---------------:|------------:|---------------:|
| Loss      |          18597 |       22409 |          82.99 |
| Win       |          18876 |       22382 |          84.34 |
| Undecided |             14 |          24 |          58.33 |
| Tie       |              2 |           2 |         100    |

```sql
SELECT
    highestLeague,
    COUNT(*) FILTER (WHERE MMR = 0) AS mmr_zero_cnt,
    COUNT(*) AS total_cnt,
    ROUND(100.0 * COUNT(*) FILTER (WHERE MMR = 0) / COUNT(*), 2)
        AS mmr_zero_pct
FROM replay_players_raw
GROUP BY highestLeague
ORDER BY total_cnt DESC
```

| highestLeague   |   mmr_zero_cnt |   total_cnt |   mmr_zero_pct |
|:----------------|---------------:|------------:|---------------:|
| Unknown         |          30116 |       32338 |          93.13 |
| Master          |           3743 |        6458 |          57.96 |
| Grandmaster     |           2860 |        4745 |          60.27 |
| Diamond         |            376 |         718 |          52.37 |
| Unranked        |            224 |         224 |         100    |
| Platinum        |             60 |         131 |          45.8  |
| Gold            |             64 |         119 |          53.78 |
| Bronze          |             41 |          73 |          56.16 |
| Silver          |              3 |           9 |          33.33 |
|                 |              2 |           2 |         100    |

Interpretation: If MMR=0 rate is uniform across all result categories (~83%), that supports the 'sentinel = not reported' hypothesis rather than a loss-correlated sentinel.

## Section E3: Duplicate Detection

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT filename || '|' || toon_id) AS distinct_player_rows,
    COUNT(*) - COUNT(DISTINCT filename || '|' || toon_id) AS duplicate_rows
FROM replay_players_raw
```

|   total_rows |   distinct_player_rows |   duplicate_rows |
|-------------:|-----------------------:|-----------------:|
|        44817 |                  44817 |                0 |

## Section F: Temporal Range

```sql
SELECT
    MIN(details.timeUTC) AS earliest,
    MAX(details.timeUTC) AS latest,
    COUNT(DISTINCT SUBSTR(details.timeUTC, 1, 7)) AS distinct_months
FROM replays_meta_raw
```

| earliest                 | latest                       |   distinct_months |
|:-------------------------|:-----------------------------|------------------:|
| 2016-01-07T02:21:46.002Z | 2024-12-01T23:48:45.2511615Z |                76 |

### Monthly Replay Counts

```sql
SELECT
    SUBSTR(details.timeUTC, 1, 7) AS month,
    COUNT(*) AS cnt
FROM replays_meta_raw
GROUP BY month
ORDER BY month
```

| month   |   cnt |
|:--------|------:|
| 2016-01 |   139 |
| 2016-02 |   256 |
| 2016-03 |   100 |
| 2016-07 |    60 |
| 2017-02 |   222 |
| 2017-03 |   187 |
| 2017-04 |   391 |
| 2017-05 |    14 |
| 2017-06 |   332 |
| 2017-07 |   188 |
| 2017-09 |   236 |
| 2017-10 |    30 |
| 2017-11 |   399 |
| 2018-01 |   420 |
| 2018-02 |   315 |
| 2018-03 |   356 |
| 2018-06 |   709 |
| 2018-07 |   450 |
| 2018-09 |   442 |
| 2018-10 |    44 |
| 2018-11 |   380 |
| 2018-12 |    64 |
| 2019-01 |     2 |
| 2019-02 |   612 |
| 2019-03 |   562 |
| 2019-04 |    46 |
| 2019-05 |   540 |
| 2019-06 |   330 |
| 2019-07 |   596 |
| 2019-08 |   169 |
| 2019-09 |   601 |
| 2019-10 |    82 |
| 2019-11 |   346 |
| 2020-02 |   423 |
| 2020-03 |    15 |
| 2020-04 |   172 |
| 2020-05 |   157 |
| 2020-06 |   547 |
| 2020-07 |   501 |
| 2020-08 |   250 |
| 2020-09 |   549 |
| 2020-11 |   107 |
| 2020-12 |   121 |
| 2021-01 |   157 |
| 2021-02 |   261 |
| 2021-03 |   183 |
| 2021-05 |   587 |
| 2021-06 |   258 |
| 2021-07 |   297 |
| 2021-08 |   495 |
| 2021-09 |   272 |
| 2021-10 |   812 |
| 2021-11 |   143 |
| 2021-12 |   371 |
| 2022-01 |    84 |
| 2022-02 |   263 |
| 2022-05 |   592 |
| 2022-06 |   107 |
| 2022-07 |   541 |
| 2022-08 |    68 |
| 2022-09 |   212 |
| 2022-10 |   562 |
| 2022-11 |   580 |
| 2022-12 |   285 |
| 2023-02 |   260 |
| 2023-05 |   441 |
| 2023-06 |   257 |
| 2023-08 |   122 |
| 2023-12 |   672 |
| 2024-02 |   187 |
| 2024-05 |    72 |
| 2024-06 |   367 |
| 2024-08 |   154 |
| 2024-09 |    95 |
| 2024-11 |   133 |
| 2024-12 |    38 |

## Section G: Error Column Census

```sql
SELECT
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE gameEventsErr = TRUE) AS game_err,
    COUNT(*) FILTER (WHERE messageEventsErr = TRUE) AS msg_err,
    COUNT(*) FILTER (WHERE trackerEvtsErr = TRUE) AS tracker_err
FROM replays_meta_raw
```

|   total |   game_err |   msg_err |   tracker_err |
|--------:|-----------:|----------:|--------------:|
|   22390 |          0 |         0 |             0 |

## Section H: Dead/Constant/Near-Constant Field Detection

Cardinality query (per column):

```sql
SELECT '{col}' AS column_name,
       COUNT(DISTINCT {col}) AS cardinality,
       COUNT(*) AS total_rows,
       ROUND(COUNT(DISTINCT {col})::DOUBLE / COUNT(*)::DOUBLE, 6) AS uniqueness_ratio
FROM {table}
```

### Full Cardinality Table

| table                          | column               |   cardinality |   total_rows |   uniqueness_ratio |
|:-------------------------------|:---------------------|--------------:|-------------:|-------------------:|
| replay_players_raw             | filename             |         22390 |        44817 |           0.499587 |
| replay_players_raw             | toon_id              |          2495 |        44817 |           0.055671 |
| replay_players_raw             | nickname             |          1106 |        44817 |           0.024678 |
| replay_players_raw             | playerID             |             9 |        44817 |           0.000201 |
| replay_players_raw             | userID               |            16 |        44817 |           0.000357 |
| replay_players_raw             | isInClan             |             2 |        44817 |           4.5e-05  |
| replay_players_raw             | clanTag              |           257 |        44817 |           0.005734 |
| replay_players_raw             | MMR                  |          1031 |        44817 |           0.023005 |
| replay_players_raw             | race                 |             6 |        44817 |           0.000134 |
| replay_players_raw             | selectedRace         |             8 |        44817 |           0.000179 |
| replay_players_raw             | handicap             |             2 |        44817 |           4.5e-05  |
| replay_players_raw             | region               |             6 |        44817 |           0.000134 |
| replay_players_raw             | realm                |             9 |        44817 |           0.000201 |
| replay_players_raw             | highestLeague        |            10 |        44817 |           0.000223 |
| replay_players_raw             | result               |             4 |        44817 |           8.9e-05  |
| replay_players_raw             | APM                  |           556 |        44817 |           0.012406 |
| replay_players_raw             | SQ                   |           171 |        44817 |           0.003816 |
| replay_players_raw             | supplyCappedPercent  |            51 |        44817 |           0.001138 |
| replay_players_raw             | startDir             |            13 |        44817 |           0.00029  |
| replay_players_raw             | startLocX            |           117 |        44817 |           0.002611 |
| replay_players_raw             | startLocY            |           115 |        44817 |           0.002566 |
| replay_players_raw             | color_a              |             2 |        44817 |           4.5e-05  |
| replay_players_raw             | color_b              |            18 |        44817 |           0.000402 |
| replay_players_raw             | color_g              |            18 |        44817 |           0.000402 |
| replay_players_raw             | color_r              |            18 |        44817 |           0.000402 |
| replays_meta_raw (struct_flat) | game_speed           |             1 |        22390 |           4.5e-05  |
| replays_meta_raw (struct_flat) | is_blizzard_map      |             2 |        22390 |           8.9e-05  |
| replays_meta_raw (struct_flat) | time_utc             |         22344 |        22390 |           0.997946 |
| replays_meta_raw (struct_flat) | elapsed_game_loops   |         14045 |        22390 |           0.627289 |
| replays_meta_raw (struct_flat) | game_version_header  |            46 |        22390 |           0.002054 |
| replays_meta_raw (struct_flat) | base_build           |            46 |        22390 |           0.002054 |
| replays_meta_raw (struct_flat) | data_build           |            46 |        22390 |           0.002054 |
| replays_meta_raw (struct_flat) | game_version_meta    |            46 |        22390 |           0.002054 |
| replays_meta_raw (struct_flat) | map_name             |           188 |        22390 |           0.008397 |
| replays_meta_raw (struct_flat) | max_players          |             5 |        22390 |           0.000223 |
| replays_meta_raw (struct_flat) | game_speed_init      |             1 |        22390 |           4.5e-05  |
| replays_meta_raw (struct_flat) | is_blizzard_map_init |             2 |        22390 |           8.9e-05  |
| replays_meta_raw (struct_flat) | map_size_x           |            14 |        22390 |           0.000625 |
| replays_meta_raw (struct_flat) | map_size_y           |            13 |        22390 |           0.000581 |
| replays_meta_raw (struct_flat) | gameEventsErr        |             1 |        22390 |           4.5e-05  |
| replays_meta_raw (struct_flat) | messageEventsErr     |             1 |        22390 |           4.5e-05  |
| replays_meta_raw (struct_flat) | trackerEvtsErr       |             1 |        22390 |           4.5e-05  |
| replays_meta_raw (struct_flat) | filename             |         22390 |        22390 |           1        |

### Flagged Columns

### Interpretation Note

The uniqueness_ratio < 0.001 threshold (EDA Manual Section 3.3) flags all low-cardinality columns mechanically. This includes:

- **Expected categoricals** (race, selectedRace, highestLeague, region, realm, result, isInClan, color_*, startDir): These are inherently low-cardinality fields in any game dataset. Flagging them is a consequence of the threshold definition, not a data quality concern. Their value distributions are profiled in Section D.

- **Genuinely constant/degenerate** (game_speed, game_speed_init, gameEventsErr, messageEventsErr, trackerEvtsErr): cardinality=1 fields that carry zero information and should be excluded from feature engineering.

- **Low-cardinality numerics** (playerID, userID, handicap): playerID ranges 1-16 (slot index within replay, not a player identifier); userID is similarly replay-scoped; handicap is 100 for all but 1 row. These warrant investigation in cleaning (01_04) but are not data quality defects per se.

Downstream steps should use the `field_classification` in the JSON artifact rather than the near-constant flag to decide feature eligibility.

**Threshold sensitivity note:** The uniqueness_ratio < 0.001 threshold is appropriate for this dataset (N=44,817 rows). For larger datasets (N > 1M), the same threshold would flag more columns as near-constant because uniqueness_ratio = cardinality / N decreases with N even for columns with stable cardinality. Re-evaluate the threshold for each dataset based on its row count and the cardinality distribution.

| table                          | column               |   cardinality |   total_rows |   uniqueness_ratio | flag          |
|:-------------------------------|:---------------------|--------------:|-------------:|-------------------:|:--------------|
| replay_players_raw             | playerID             |             9 |        44817 |           0.000201 | near-constant |
| replay_players_raw             | userID               |            16 |        44817 |           0.000357 | near-constant |
| replay_players_raw             | isInClan             |             2 |        44817 |           4.5e-05  | near-constant |
| replay_players_raw             | race                 |             6 |        44817 |           0.000134 | near-constant |
| replay_players_raw             | selectedRace         |             8 |        44817 |           0.000179 | near-constant |
| replay_players_raw             | handicap             |             2 |        44817 |           4.5e-05  | near-constant |
| replay_players_raw             | region               |             6 |        44817 |           0.000134 | near-constant |
| replay_players_raw             | realm                |             9 |        44817 |           0.000201 | near-constant |
| replay_players_raw             | highestLeague        |            10 |        44817 |           0.000223 | near-constant |
| replay_players_raw             | result               |             4 |        44817 |           8.9e-05  | near-constant |
| replay_players_raw             | startDir             |            13 |        44817 |           0.00029  | near-constant |
| replay_players_raw             | color_a              |             2 |        44817 |           4.5e-05  | near-constant |
| replay_players_raw             | color_b              |            18 |        44817 |           0.000402 | near-constant |
| replay_players_raw             | color_g              |            18 |        44817 |           0.000402 | near-constant |
| replay_players_raw             | color_r              |            18 |        44817 |           0.000402 | near-constant |
| replays_meta_raw (struct_flat) | game_speed           |             1 |        22390 |           4.5e-05  | constant      |
| replays_meta_raw (struct_flat) | is_blizzard_map      |             2 |        22390 |           8.9e-05  | near-constant |
| replays_meta_raw (struct_flat) | max_players          |             5 |        22390 |           0.000223 | near-constant |
| replays_meta_raw (struct_flat) | game_speed_init      |             1 |        22390 |           4.5e-05  | constant      |
| replays_meta_raw (struct_flat) | is_blizzard_map_init |             2 |        22390 |           8.9e-05  | near-constant |
| replays_meta_raw (struct_flat) | map_size_x           |            14 |        22390 |           0.000625 | near-constant |
| replays_meta_raw (struct_flat) | map_size_y           |            13 |        22390 |           0.000581 | near-constant |
| replays_meta_raw (struct_flat) | gameEventsErr        |             1 |        22390 |           4.5e-05  | constant      |
| replays_meta_raw (struct_flat) | messageEventsErr     |             1 |        22390 |           4.5e-05  | constant      |
| replays_meta_raw (struct_flat) | trackerEvtsErr       |             1 |        22390 |           4.5e-05  | constant      |
