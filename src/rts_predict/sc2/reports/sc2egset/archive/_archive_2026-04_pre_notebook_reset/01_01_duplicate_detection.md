# Duplicate Detection

## Exact duplicate replay IDs

### Query
```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(
        DISTINCT regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1)
    ) AS distinct_replay_ids
FROM raw
```

### Results

|   total_rows |   distinct_replay_ids |
|-------------:|----------------------:|
|        22390 |                 22390 |

## Near-duplicates (same players, same map, <60s apart)

### Query
```sql
WITH raw_entries AS (
    SELECT
        filename,
        regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1) AS replay_id,
        (details->>'$.timeUTC')::TIMESTAMP AS match_time,
        metadata->>'$.mapName' AS map_name,
        CAST(entry.value->>'$.nickname' AS VARCHAR) AS nickname,
        CAST(entry.value->>'$.result' AS VARCHAR) AS result_val
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
),
players_per_game AS (
    SELECT
        filename,
        ANY_VALUE(replay_id) AS replay_id,
        ANY_VALUE(match_time) AS match_time,
        ANY_VALUE(map_name) AS map_name,
        LIST(LOWER(nickname) ORDER BY LOWER(nickname)) AS player_names
    FROM raw_entries
    WHERE nickname IS NOT NULL
      AND (result_val = 'Win' OR result_val = 'Loss')
    GROUP BY filename
)
SELECT
    a.replay_id AS replay_id_a,
    b.replay_id AS replay_id_b,
    a.map_name,
    a.match_time AS time_a,
    b.match_time AS time_b,
    ABS(EPOCH(a.match_time) - EPOCH(b.match_time)) AS time_diff_seconds,
    a.player_names
FROM players_per_game a
JOIN players_per_game b
    ON a.player_names = b.player_names
    AND a.map_name = b.map_name
    AND a.replay_id < b.replay_id
    AND ABS(EPOCH(a.match_time) - EPOCH(b.match_time)) <= 60
ORDER BY time_diff_seconds
```

| replay_id_a                      | replay_id_b                      | map_name                   | time_a                     | time_b                     |   time_diff_seconds | player_names                                         |
|:---------------------------------|:---------------------------------|:---------------------------|:---------------------------|:---------------------------|--------------------:|:-----------------------------------------------------|
| 025072b076a425713d7678e663e23fa0 | 348935a659936931cad0865cadcf51f7 | Proxima Station LE         | 2017-04-29 05:51:29.943599 | 2017-04-29 05:51:29.943599 |            0        | ['iaguz' 'toodming']                                 |
| 10de96de1f27a2c3b92a72a169cdf43a | 9436e97d8535b0b3e9989805401a8cc8 | Ruins of Seras             | 2016-01-09 04:31:32.261400 | 2016-01-09 04:31:32.261400 |            0        | ['<spm>expect' '<口凸口>fist']                          |
| abfb5a3279e03004c8a21cfd2976d787 | b29c275ed18fac5013430d1b4a0534f3 | Lerilak Crest              | 2016-01-16 04:21:26.388504 | 2016-01-16 04:21:26.388504 |            0        | ['<spm>expect' '<教我玩蟲族>rex']                         |
| 005862e429755272999cfc59b5928d78 | faefaad468286fc4e96bf6ad45e1f929 | Honorgrounds LE            | 2017-04-29 04:32:59.663624 | 2017-04-29 04:32:59.663624 |            0        | ['masa' 'uthermal']                                  |
| 1c683a067db4c7b63357838117a3c4b4 | 8422b356c720afe36dd5eafcbb7ac0e9 | Abyssal Reef LE            | 2017-06-17 10:46:55.075006 | 2017-06-17 10:46:55.075006 |            0        | ['multi' 'pappijoe']                                 |
| b2213740709b53ffc0fdc014f4758e45 | c1ce9410322c4408b21ee8bcd0b8c0bf | Proxima Station LE         | 2017-04-29 00:25:50.934730 | 2017-04-29 00:25:50.934730 |            0        | ['bails' 'true']                                     |
| b80a9394c646bc22f7ad0181aea95292 | daba8329336a0741bc14b69183ee4cd3 | Acid Plant LE              | 2018-06-02 02:25:46.983702 | 2018-06-02 02:25:46.983702 |            0        | ['crimson' 'tugboat']                                |
| 81f9e2aeec990be7b0e6338f6dc12b69 | edadc764710ff8dae57d3cf71ac974c0 | Newkirk Precinct TE (Void) | 2017-04-29 04:17:40.263054 | 2017-04-29 04:17:40.263054 |            0        | ['masa' 'uthermal']                                  |
| 59217ea672b7dfc2e666961309e643dd | cdcf71141fc2533ad5021d0fc76b5a81 | Ice and Chrome LE          | 2020-06-24 23:15:48.464033 | 2020-06-24 23:15:48.464033 |            0        | ['&lt;lgcanz&gt;nxz' '&lt;lionz&gt;risky']           |
| 1ecddd570cf8c7ab6ab151713f37a841 | 5fde295c006b4da7d5f56af1feeda016 | Simulacrum LE              | 2020-04-10 17:05:56.358800 | 2020-04-10 17:05:56.358800 |            0        | ['&lt;ew0lfz&gt;liquidthermy' '&lt;tlng&gt;neeblet'] |
| 8c2e475b5df62031379b8e917d875208 | ea219184715c84572fd369dd808630e5 | Acropolis LE               | 2019-09-07 21:17:58.085676 | 2019-09-07 21:17:58.085676 |            0        | ['butalways' 'probe']                                |
| 3f215ec2204770555e5375d1e2f27936 | 8c5d2fc04fd21da4f0a790c0d5f346eb | Ephemeron LE               | 2019-09-07 21:25:57.285351 | 2019-09-07 21:25:57.285351 |            0        | ['butalways' 'probe']                                |
| be988855ce74b9a84507811c14d3f63c | cc899b6ec3e461c8673f82e2f9516bb6 | Oxide LE                   | 2021-05-28 00:46:35.464001 | 2021-05-28 00:46:35.464001 |            0        | ['&lt;ex0n&gt;nina' 'purelegacy']                    |
| 2022c5fb13a2275bffb5756381b270d6 | c021f1b89478464074a9e7073e176187 | Port Aleksander LE         | 2019-03-11 21:05:21.381828 | 2019-03-11 21:05:21.381828 |            0        | ['probe' 'ptitdrogo']                                |
| 2542f0eb81590f9b34cc896da4195829 | ce1ebca2a82862c333fa78c57110d913 | Ascension to Aiur LE       | 2017-06-17 10:34:55.815879 | 2017-06-17 10:34:55.815879 |            0        | ['holyhit' 'sluskis']                                |
| 314477e5c10011113e584371f0307709 | 91f7a3cadc1e8f637cdd520daea3bcc6 | Bel'Shir Vestige LE (Void) | 2017-04-29 03:13:41.777557 | 2017-04-29 03:13:41.777557 |            0        | ['benttwig' 'pono']                                  |
| 52a419539a03a92b048dbd74d60f6044 | 56eef031540c0c21f931938acedb2a1c | Prion Terraces             | 2016-01-09 04:21:44.085400 | 2016-01-09 04:21:44.085400 |            0        | ['<spm>expect' '<口凸口>fist']                          |
| 768eb9f9277efe22b6bf636ffdfa8550 | 96e2dd7fea67653449c4f0781a57309e | Deathaura LE               | 2020-06-25 16:52:38.311863 | 2020-06-25 16:52:38.311863 |            0        | ['&lt;ence&gt;serral' '&lt;mkers&gt;soul']           |
| 584083f4a6c1fdb35e2e66fd66702df4 | d34dc3769e2554a829e980a9bdc3d927 | Thunderbird LE             | 2019-09-07 01:17:28.376818 | 2019-09-07 01:17:28.376818 |            0        | ['&lt;lcy&gt;mode' 'dolan']                          |
| 26cfeff1691a653e09a9ed1144447c56 | 555161783fcc9924207f3084ce1ff307 | Pillars of Gold LE         | 2020-06-25 23:12:24.564108 | 2020-06-25 23:12:24.564108 |            0        | ['&lt;lionz&gt;risky' '&lt;mfsc2&gt;seither']        |
| 6a908e11e409e998bf326e217e9e504f | f8fceae1d463bd2cf8b2921e7ea8b149 | Ever Dream LE              | 2020-04-10 17:22:07.531800 | 2020-04-10 17:22:07.531800 |            0        | ['&lt;ew0lfz&gt;liquidthermy' '&lt;tlng&gt;neeblet'] |
| 00f5d46a1476b02c87e5f0d100b895f9 | 048d1879518352fc1cb96dd7354cfd64 | Eternal Empire LE          | 2020-06-25 23:49:39.115961 | 2020-06-25 23:49:39.115961 |            0        | ['&lt;lionz&gt;risky' '&lt;mfsc2&gt;seither']        |
| 53488c12d6bff0682c95a22aa099ac78 | e85b852d41f67f65e58c892d49122966 | Bel'Shir Vestige LE (Void) | 2017-04-29 04:49:53.051858 | 2017-04-29 04:49:53.051858 |            0        | ['masa' 'uthermal']                                  |
| 34acd727d551e7f7a112a374a1ee0566 | 772857f1f279a9e44367d20e3ebb7420 | Abyssal Reef LE            | 2017-06-17 10:36:39.401387 | 2017-06-17 10:36:39.401387 |            0        | ['helten' 'lovecrit']                                |
| 290fd5e7867d2d3f540f106deddd6017 | f21f7810126ec2d29742fd4af3ae8489 | Orbital Shipyard           | 2016-01-16 03:45:03.966504 | 2016-01-16 03:45:03.966504 |            0        | ['<spm>expect' '<教我玩蟲族>rex']                         |
| c0b8d15386f2c1b31e3adc8805b84f5b | d20ff013d7229bad1f27ef2610062418 | World of Sleepers LE       | 2019-09-07 21:38:40.574928 | 2019-09-07 21:38:40.574928 |            0        | ['butalways' 'probe']                                |
| 533fbb39fade08d69016c88fd64dc232 | edca838a3ccb6def46fa0b0a26f61acb | Proxima Station LE         | 2017-02-28 14:25:10.476229 | 2017-02-28 14:25:10.476229 |            0        | ['alo' 'namshar']                                    |
| 9c0814dc9601b1745c3c35364db0b27d | ad43cbea647a24493973c22f8ce2aa80 | Lost and Found LE          | 2018-06-02 02:30:44.444512 | 2018-06-02 02:30:44.444512 |            0        | ['crimson' 'tugboat']                                |
| a8a0559c0717ce4993aabb31954c94c2 | c57fd84df2473ae6ff563aae7e98bb88 | Prion Terraces             | 2016-01-16 03:20:51.030504 | 2016-01-16 03:20:51.030504 |            0        | ['<spm>expect' '<教我玩蟲族>rex']                         |
| 16722af101fdbf12ff96939689219ec8 | a5b6f3d8da3d170892049e9368f110df | Ruins of Seras             | 2016-01-16 03:57:27.393504 | 2016-01-16 03:57:27.393504 |            0        | ['<spm>expect' '<教我玩蟲族>rex']                         |
| 1d91c410f59284680e1b56747b8bfc33 | b8903e2f316c71f61233fded1e8dfc98 | Acropolis LE               | 2019-09-07 01:25:27.501750 | 2019-09-07 01:25:27.501750 |            0        | ['&lt;lcy&gt;mode' 'dolan']                          |
| 06635288d579023d2f6853338f291f29 | 837125c785dd344b8da4c6e36466cb92 | Ulrena                     | 2016-01-09 04:42:28.980400 | 2016-01-09 04:42:28.980400 |            0        | ['<spm>expect' '<口凸口>fist']                          |
| 1a1b4bab691b12bd459d9ee85f0b533a | 3d298fcd9f4d4498e1e0645629684f08 | Ever Dream LE              | 2020-06-25 23:32:35.068722 | 2020-06-25 23:32:35.068722 |            0        | ['&lt;lionz&gt;risky' '&lt;mfsc2&gt;seither']        |
| 0ed7502ac90ce94e47a29545052ced2b | bd737723a15f0d6589de37b87df14f8a | Dusk Towers                | 2016-01-16 03:30:52.468504 | 2016-01-16 03:30:52.468504 |            0        | ['<spm>expect' '<教我玩蟲族>rex']                         |
| 4da9516efb4daae99a5da3e6ab67e04f | 8a53f65cbae522fcb6f4eba85bfb9b32 | Bel'Shir Vestige LE (Void) | 2017-04-29 04:19:32.423769 | 2017-04-29 04:19:32.423769 |            0        | ['nony' 'xkawaiian']                                 |
| 7b708d290f83150b106ab78d25d763a7 | df3a96649b753209da651f0e37a49811 | Deathaura LE               | 2020-06-24 23:40:40.872787 | 2020-06-24 23:40:40.872787 |            0        | ['&lt;lgcanz&gt;nxz' '&lt;lionz&gt;risky']           |
| 5cbd5df99854ed5d9bff4b673fa9ae48 | 9171be3bc2ccb0aab57a89b6085e078d | Kairos Junction LE         | 2019-03-11 21:20:33.183467 | 2019-03-11 21:20:33.183467 |            0        | ['probe' 'ptitdrogo']                                |
| 6ca3a65d44404d3f4608413d59009932 | db32500e107d9451fc89c80b90bccae8 | Proxima Station LE         | 2017-06-17 10:50:53.813193 | 2017-06-17 10:50:53.813193 |            0        | ['helten' 'lovecrit']                                |
| 4bba8d19de372e835771a8f78c0ead8c | 9134ecda0bc2c4dad7a38f8a5ef96a40 | Proxima Station LE         | 2017-04-29 06:03:50.635876 | 2017-04-29 06:03:50.635876 |            0        | ['snute' 'sortof']                                   |
| 183382215400c58e99a7a33f695ab07f | 2000d3503d5709870e92abb2535bbfec | Ever Dream LE              | 2020-06-24 23:28:38.231930 | 2020-06-24 23:28:38.231930 |            0        | ['&lt;lgcanz&gt;nxz' '&lt;lionz&gt;risky']           |
| 285e54f082869fe522046b73e1258f1b | bbe5c709eff40e075ece818029634aff | Abyssal Reef LE            | 2017-04-29 09:12:19.154451 | 2017-04-29 09:12:19.154451 |            0        | ['harstem' 'jonsnow']                                |
| c8dcc7dfd68b2b93ced16ca72209a97d | ee9c8e0a7c287802de6c94ccf5c9e232 | Newkirk Precinct TE (Void) | 2017-04-29 08:56:53.552741 | 2017-04-29 08:56:53.552741 |            0        | ['neeb' 'tlo']                                       |
| 28f9c05c82453769a2d15c47c05f2192 | 4ace7e8bb8e7c2a42e7bd025f417ed93 | Ice and Chrome LE          | 2020-06-26 00:08:01.196562 | 2020-06-26 00:08:01.196562 |            0        | ['&lt;lionz&gt;risky' '&lt;mfsc2&gt;seither']        |
| 9300bd529d86a03bc0ac884769814e00 | 9a4682a7b5a982a6942c5be7fd7f5fae | Eternal Empire LE          | 2020-06-25 16:33:47.682465 | 2020-06-25 16:33:47.682465 |            0        | ['&lt;ence&gt;serral' '&lt;mkers&gt;soul']           |
| 5b978dce648adea612304fed277efb1e | e6762cbecf49f74e95258db1c1f53f30 | Simulacrum LE              | 2020-04-10 12:54:36.368118 | 2020-04-10 12:54:36.368118 |            0        | ['&lt;rye&gt;blyonfire' '&lt;rye1&gt;ptitdrogo']     |
| 9e38b5477faf00b8a6bb00ebc0cb0338 | f11ada48aee0b8f250a085567ddc8c0c | Golden Wall LE             | 2020-04-10 17:33:54.214800 | 2020-04-10 17:33:54.214800 |            0        | ['&lt;ew0lfz&gt;liquidthermy' '&lt;tlng&gt;neeblet'] |
| 18fcc499139c67f29f48b019a0235e25 | b8158ba64a99495da2806dcfe4c77a4d | Ascension to Aiur LE       | 2017-06-17 14:16:25.387119 | 2017-06-17 14:16:25.311388 |            0.075731 | ['lillekanin' 'stephano']                            |
| 80b3bd9a15fa570b243a2c31e10f46f6 | a1b13a938960cb2d875c24d305a1b6b8 | Abyssal Reef LE            | 2017-06-17 14:06:33.434132 | 2017-06-17 14:06:33.322606 |            0.111526 | ['bly' 'kebabking']                                  |
| 69c16bbf4a695d629af927285415c10a | bb66616c47193b8fa1b318bae19ce7ee | Bel'Shir Vestige LE (Void) | 2017-02-28 16:28:24.400775 | 2017-02-28 16:28:24.522493 |            0.121718 | ['ptitdrogo' 'ryung']                                |
| 3556c069ddb9d659f17ba50812ae98b6 | b9c515bff8c56d3d4cbcfd7c8ec6cfb1 | Odyssey LE                 | 2017-06-17 11:54:27.603341 | 2017-06-17 11:54:27.367889 |            0.235452 | ['hymy' 'shadown']                                   |
| 5102379983a7c04a39d97b6e79240a3b | 6f607c4f14512bfba70acc0b457b4d7e | Dreamcatcher LE            | 2018-06-02 11:02:57.970294 | 2018-06-02 11:02:57.686257 |            0.284037 | ['&lt;root&gt;puck' 'semper']                        |
| 242e717738d1f395891835e45f749e04 | c55bb71b7533495b9e9b5220b426f6c5 | Sequencer LE               | 2017-06-17 15:19:18.368410 | 2017-06-17 15:19:18.733713 |            0.365303 | ['dns' 'minato']                                     |
| 46b46129e7212ccadbe2431d8a968a62 | ee06bdf41f206ba0fa3d629180c876c2 | Sequencer LE               | 2017-06-17 19:20:25.149169 | 2017-06-17 19:20:24.725907 |            0.423262 | ['iasonu' 'stephano']                                |
| 12bdecca606a4c06093011bcbc6097e0 | 86629e27628d1b896ad48ba68f1d1904 | Odyssey LE                 | 2017-06-17 19:37:45.622712 | 2017-06-17 19:37:45.177306 |            0.445406 | ['iasonu' 'stephano']                                |
| 698efa20a66e1addc055ce364a3be17d | eebbbe00aff72230298d0767629b195d | Proxima Station LE         | 2017-06-17 12:07:50.247459 | 2017-06-17 12:07:49.801189 |            0.44627  | ['hymy' 'shadown']                                   |
| 99595a98f8f6372d5e0127ed6212b9a7 | adc261850fe0113586fa94ec97e049f3 | Odyssey LE                 | 2017-06-17 17:50:48.257591 | 2017-06-17 17:50:47.798549 |            0.459042 | ['iasonu' 'stephano']                                |
| 130ee589619d883dbba7558f5b2b992e | 83b3c7d749269db59b520bbc54741db6 | Ascension to Aiur LE       | 2017-06-17 15:00:55.655202 | 2017-06-17 15:00:55.192446 |            0.462756 | ['dns' 'minato']                                     |
| 0e9a057b2ced13021ffc604bca68ee2f | d38f9d5ca281bf2e06551ecf134bb4fd | Ascension to Aiur LE       | 2017-06-17 14:32:38.290759 | 2017-06-17 14:32:38.981222 |            0.690463 | ['awers' 'shadown']                                  |
| 56fcef962db8278d16b7fbac1efee7c3 | bf10f99d10a2ab9d08ecf8f16b93445e | Newkirk Precinct TE (Void) | 2017-04-29 06:17:20.982745 | 2017-04-29 06:17:21.954419 |            0.971674 | ['puck' 'uthermal']                                  |
| 0ebd35b54ad14850f254bf0ff95046c9 | e6c5dcab1b894a8c61012daa2fcc8fc5 | Cactus Valley LE (Void)    | 2017-04-29 06:12:53.211156 | 2017-04-29 06:12:54.242156 |            1.031    | ['snute' 'sortof']                                   |
| 5b1ce113270da1c9e10bb700494f37f8 | 5e3a7cbee9e580f93742141bb1e2eaef | Abyssal Reef LE            | 2017-04-29 05:37:54.089973 | 2017-04-29 05:37:55.369838 |            1.27987  | ['time' 'true']                                      |
| 11ab8cd4a564b3646efa0260a6b6a14e | 1621cb39fa35eef99b907c67f7f7a75d | Abyssal Reef LE            | 2017-04-29 06:26:59.984861 | 2017-04-29 06:27:01.709330 |            1.72447  | ['snute' 'sortof']                                   |
| 27f7f7ac43276498cffda245b5921f98 | 54fb2c4b80d6f82c3a27dc1bcf980555 | Abyssal Reef LE            | 2017-04-29 08:43:18.329675 | 2017-04-29 08:43:20.054707 |            1.72503  | ['lambo' 'special']                                  |
| 347bdf6cc4b24dbeb80eae08fc43e738 | c748870a363c1082ebe673889a0b2eb9 | Odyssey LE                 | 2017-06-17 11:13:09.877070 | 2017-06-17 11:13:08.137657 |            1.73941  | ['dns' 'spaceduck']                                  |
| 4b6831dbff5a3c1dbb4060ee208fb74a | 81620566886bc19150275173ed98731e | Sequencer LE               | 2017-06-17 11:07:24.191380 | 2017-06-17 11:07:26.018816 |            1.82744  | ['dns' 'spaceduck']                                  |
| 05018bcc4af37b9b46a2708d330f9d08 | 0f28b3761262f778ab3825323bac45e3 | Acid Plant LE              | 2018-06-29 12:13:45.119684 | 2018-06-29 12:13:46.980976 |            1.86129  | ['&lt;mouz&gt;heromarine' '&lt;revogg&gt;fear']      |
| 6464b02315494997c7a80d6c8405ddb6 | 64731feb731aab59be3e2c3f5f714374 | Abyssal Reef LE            | 2017-03-02 14:49:02.554139 | 2017-03-02 14:49:00.638162 |            1.91598  | ['harstem' 'neeb']                                   |
| a6f01196428032f90279d6b8f49987bd | f8ecb4dfdc7321e26a677508df4d69da | Bel'Shir Vestige LE (Void) | 2017-04-29 06:08:28.851876 | 2017-04-29 06:08:26.862925 |            1.98895  | ['time' 'true']                                      |
| 32d70eb46d1dbb35c951bb47b2ec1593 | d94d84918ed56138e631b651b5bb32ba | Ascension to Aiur LE       | 2017-06-17 17:56:55.464959 | 2017-06-17 17:56:57.727009 |            2.26205  | ['iasonu' 'stephano']                                |
| 96f1ccd2178c8da2307b3da92f64a889 | f90bb91e129ca2614b98e58a9c1836ad | Abyssal Reef LE            | 2017-06-17 14:42:04.833627 | 2017-06-17 14:42:02.529286 |            2.30434  | ['dns' 'minato']                                     |
| 3402ec98011bf911abbd88d66506e954 | abf53d4b6ebabdd2e2c0e2da0e7e0918 | Abyssal Reef LE            | 2017-06-17 13:52:10.147500 | 2017-06-17 13:52:12.512715 |            2.36522  | ['dns' 'gerald']                                     |
| 34aecccc3af61e3098dbda1bd8052944 | af4be61542fb4b77ff162b41e2919277 | Proxima Station LE         | 2017-06-17 14:56:00.093614 | 2017-06-17 14:56:02.493448 |            2.39983  | ['awers' 'shadown']                                  |
| 57eb0b1279cbaf269930cc8c72912aba | e1101a849ca3356be8bb9110c29ecf13 | Sequencer LE               | 2017-06-17 14:19:27.464524 | 2017-06-17 14:19:25.000759 |            2.46377  | ['dns' 'gerald']                                     |
| c72bba0767e7badd6256b337ef2021d9 | e11efd24e6206a453d0ca56d13d9428a | Catalyst LE                | 2018-06-02 05:07:59.697802 | 2018-06-02 05:07:57.218024 |            2.47978  | ['nice' 'snute']                                     |
| 7a2e1e895bd205a510592ec7b752d72a | 7e9960e0fc30e5ef8c91d5ae3501f815 | Acid Plant LE              | 2018-11-23 18:16:08.766555 | 2018-11-23 18:16:11.288643 |            2.52209  | ['bly' 'gostephano']                                 |
| 07ed49c740751d59ee0e2218e1a3c624 | bf0ee5bb07054bfe584f097522b631d4 | Newkirk Precinct TE (Void) | 2017-04-29 05:48:29.068538 | 2017-04-29 05:48:31.608567 |            2.54003  | ['time' 'true']                                      |
| a7f92e768508b6605cd1b5d89817aa6b | cc8d6c86517efa9d3e87bcff06844906 | Lost and Found LE          | 2018-11-23 18:06:26.335023 | 2018-11-23 18:06:28.899754 |            2.56473  | ['bly' 'gostephano']                                 |
| 8201b9e80767f8ef7b98739047665532 | 90d995e9744260c7c94c6a8abad47822 | Sequencer LE               | 2017-06-17 11:02:00.582778 | 2017-06-17 11:01:57.414057 |            3.16872  | ['dns' 'spaceduck']                                  |
| 5bd1f9db49b3b05b55a24fd22d45ee9b | f7f323c97c2da3d029aacfbca4503c11 | Lost and Found LE          | 2018-06-02 10:44:29.429485 | 2018-06-02 10:44:32.790316 |            3.36083  | ['&lt;root&gt;puck' 'semper']                        |
| 8a8b705132753c937572b1ca2ebe82a1 | 93ab390645cd839d57ecbd06a2c0190a | Newkirk Precinct TE (Void) | 2017-04-29 02:27:01.802485 | 2017-04-29 02:27:05.391075 |            3.58859  | ['fear' 'warren']                                    |
| c240ee37a030d0dafdc718c147040290 | ebf2173b86aaf1107b37123a6430fe4a | Abyssal Reef LE            | 2017-06-17 15:20:25.915464 | 2017-06-17 15:20:22.223863 |            3.6916   | ['awers' 'shadown']                                  |
| c0e340fabce94b9704909a4912002860 | c5f57aa2be25ff4abbbbd41c961b74b7 | Golden Wall LE             | 2020-09-04 15:26:09.272210 | 2020-09-04 15:26:13.006724 |            3.73451  | ['&lt;mouz&gt;heromarine' '&lt;xkom&gt;agoelazer']   |
| 1049076c69062dd468a5396f4c7d9894 | 95f34105f8dd15e3cdaf256893bd0799 | Proxima Station LE         | 2017-02-28 16:48:52.394723 | 2017-02-28 16:48:48.539792 |            3.85493  | ['ptitdrogo' 'ryung']                                |
| 21f9b1ff524a6f2a33b08ebeff593716 | 4f34c33829cf33e22db86538d0ea2d84 | Abyssal Reef LE            | 2017-06-17 17:43:16.203811 | 2017-06-17 17:43:11.955901 |            4.24791  | ['kelazhur' 'showtime']                              |
| be7c6e46c3bc8a92825227d2d86ff030 | eaf9808a2938619ba0011fd647496f41 | Abyssal Reef LE            | 2017-06-17 11:33:07.646658 | 2017-06-17 11:33:12.170995 |            4.52434  | ['shadown' 'ziggy']                                  |
| 0277717666cf217f924bd28fac74d589 | 9a385406eaded9a5a53c9fd7c0d51429 | Proxima Station LE         | 2017-06-17 14:04:20.127769 | 2017-06-17 14:04:15.602191 |            4.52558  | ['shadown' 'uthermal']                               |
| 47f56812504c1b480213f3e97955ff88 | d8c312efff2826abbf417233cac7b87d | Ascension to Aiur LE       | 2017-06-17 13:51:36.460544 | 2017-06-17 13:51:40.989272 |            4.52873  | ['shadown' 'uthermal']                               |
| 16e37ce1641cf8d95280def4792052b5 | 3036bc5e078d69e628b1d000eb38a210 | Sequencer LE               | 2017-06-17 11:19:33.169256 | 2017-06-17 11:19:28.301976 |            4.86728  | ['shadown' 'ziggy']                                  |
