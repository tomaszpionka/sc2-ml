# SC2EGSet — Game Settings and Replay Field Completeness Audit

**Phase:** 1 — Corpus Inventory and Data Exploration  
**Step:** 1.8 — Game settings and replay field completeness audit  
**Date:** 2026-04-07  
**Corpus:** 22,390 replays across 70 tournaments (SC2EGSet v2.1.0)

> **Note on error flags:** The fields `gameEventsErr`, `messageEventsErr`, and
> `trackerEvtsErr` are present in the source `.SC2Replay.json` files inside
> each tournament `.zip` archive but were not loaded into the DuckDB `raw` table
> during Phase 0 ingestion (the raw table stores only: `header`, `initData`,
> `details`, `metadata`, `ToonPlayerDescMap`). Sub-step C therefore reads these
> flags directly from the 70 ZIP archives via Python/zipfile rather than via SQL.

---

## Sub-step A — Game Speed Verification (CRITICAL)

**Expectation:** 100% of replays at "Faster" speed. Any non-Faster replay would
require a cleaning rule in Phase 6.

### Query A1 — initData game speed

```sql
SELECT
    initData->'$.gameDescription'->>'$.gameSpeed' AS init_game_speed,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1
ORDER BY 2 DESC;
```

**Result:**

| init_game_speed | n_replays |
|-----------------|-----------|
| Faster          | 22390     |

### Query A2 — details game speed (cross-check)

```sql
SELECT
    details->>'$.gameSpeed' AS details_game_speed,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1
ORDER BY 2 DESC;
```

**Result:**

| details_game_speed | n_replays |
|--------------------|-----------|
| Faster             | 22390     |

### Query A3 — Consistency between fields

```sql
SELECT
    initData->'$.gameDescription'->>'$.gameSpeed' AS init_speed,
    details->>'$.gameSpeed' AS details_speed,
    COUNT(*) AS n
FROM raw
GROUP BY 1, 2
HAVING init_speed != details_speed;
```

**Result:** 0 rows (no mismatches).

**Verdict:** PASS — 100% of replays are at Faster speed. Both `initData` and
`details` agree. No cleaning rule needed for game speed.

---

## Sub-step B — Handicap Check (CRITICAL)

**Expectation:** 100% of player slots at handicap = 100. Any player at a
non-standard handicap would invalidate the economic balance of the game.

### Query B1 — Handicap distribution

```sql
SELECT
    (entry.value->>'$.handicap')::INTEGER AS handicap,
    COUNT(*) AS n_player_slots
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1
ORDER BY 1;
```

**Result:**

| handicap | n_player_slots |
|----------|----------------|
| 0        | 2              |
| 100      | 44815          |

**Investigation of handicap = 0 entries:**

Two player slots have handicap = 0. Inspection of the underlying `ToonPlayerDescMap`
JSON for both affected replays reveals these are phantom/anonymous player entries
with an empty toon key (`""`), empty nickname, `playerID` values not matching
standard player slots (but still active with results), zero `APM`, zero `MMR`,
and `color.a = 0`. Both replays have exactly one normal player slot at handicap = 100.

Affected replays:

| replay_id | tournament_dir | notes |
|-----------|----------------|-------|
| `63a9f9bf14012cd277787af4ab9d9e96` | 2017_IEM_XI_World_Championship_Katowice | Phantom slot: `selectedRace=Rand`, `race=Zerg`, `APM=20` |
| `0eba71d4cdcf5a159a818a4c83bbb9d2` | 2019_HomeStory_Cup_XIX | Phantom slot: `selectedRace=Rand`, `race=Prot`, `APM=6` |

**Verdict:** NEAR-PASS — 44,815 / 44,817 real player slots (99.996%) are at
handicap = 100. The 2 exceptional slots correspond to phantom anonymous entries
with empty toon keys; they are not real players and will be excluded naturally
during the player identity resolution step (Phase 2), as they have no canonical
nickname. No separate Phase 6 cleaning rule required beyond the existing empty-nickname filter.

---

## Sub-step C — Error Flags Audit (CRITICAL)

**Method:** The fields `gameEventsErr`, `messageEventsErr`, and `trackerEvtsErr`
are not stored in the DuckDB `raw` table. They were read directly from the source
`.SC2Replay.json` files contained in all 70 tournament ZIP archives.

**Python scan code:**

```python
import zipfile, json
from pathlib import Path

raw_dir = Path("src/rts_predict/sc2/data/sc2egset/raw")
zip_files = sorted(raw_dir.glob("*/*.zip"))
# Found 70 zip files

error_rows = []
totals = {"gameEventsErr": 0, "messageEventsErr": 0, "trackerEvtsErr": 0}
total_checked = 0

for zpath in zip_files:
    tournament_dir = zpath.parent.name
    with zipfile.ZipFile(zpath) as z:
        json_names = [
            n for n in z.namelist()
            if n.endswith(".SC2Replay.json") and not n.startswith("._")
        ]
        for name in json_names:
            replay_id = Path(name).stem.replace(".SC2Replay", "")
            with z.open(name) as f:
                d = json.load(f)
            ge = bool(d.get("gameEventsErr", False))
            me = bool(d.get("messageEventsErr", False))
            te = bool(d.get("trackerEvtsErr", False))
            total_checked += 1
            if ge: totals["gameEventsErr"] += 1
            if me: totals["messageEventsErr"] += 1
            if te: totals["trackerEvtsErr"] += 1
            if ge or me or te:
                error_rows.append({
                    "replay_id": replay_id,
                    "tournament_dir": tournament_dir,
                    "gameEventsErr": ge,
                    "messageEventsErr": me,
                    "trackerEvtsErr": te,
                })
```

**Result:**

| metric | value |
|--------|-------|
| Total replays scanned | 22,390 |
| gameEventsErr = true | 0 |
| messageEventsErr = true | 0 |
| trackerEvtsErr = true | 0 |
| Total replays with any error | 0 |

**Verdict:** PASS — Zero replays have any parse error flag set. The artifact
`01_error_flags_audit.csv` contains only the header row (no data rows).
No Phase 6 exclusion rule needed for error flags.

---

## Sub-step D — Victory/Defeat and Game Mode Settings (CRITICAL)

**Expectation:** All replays should have `noVictoryOrDefeat=false`, `competitive=false`,
`cooperative=false`, `practice=false`. These flags confirm the game was played as a
standard ranked or tournament match where a real outcome was recorded.

### Query D1 — Game mode flag distribution

```sql
SELECT
    initData->'$.gameDescription'->'$.gameOptions'->>'$.noVictoryOrDefeat' AS no_victory,
    initData->'$.gameDescription'->'$.gameOptions'->>'$.competitive' AS competitive,
    initData->'$.gameDescription'->'$.gameOptions'->>'$.cooperative' AS cooperative,
    initData->'$.gameDescription'->'$.gameOptions'->>'$.practice' AS practice,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1, 2, 3, 4
ORDER BY 5 DESC;
```

**Result:**

| no_victory | competitive | cooperative | practice | n_replays |
|-----------|-------------|-------------|----------|-----------|
| false     | false       | false       | false    | 22387     |
| false     | true        | false       | false    | 3         |

**Investigation of competitive = true entries:**

Three replays have `competitive=true` (and additionally `amm=true`, `battleNet=true`),
all from the same tournament: `2017_IEM_XI_World_Championship_Katowice`.

| replay_id | tournament_dir | amm | battleNet |
|-----------|----------------|-----|-----------|
| `89095a8e23c0e0281efc6c523e2c6226` | 2017_IEM_XI_World_Championship_Katowice | true | true |
| `e410ce15d10ca834063db573a85e292d` | 2017_IEM_XI_World_Championship_Katowice | true | true |
| `9d42de7ebcf7c26a2ea192da177252b6` | 2017_IEM_XI_World_Championship_Katowice | true | true |

The combination of `competitive=true`, `amm=true` (automated matchmaking), and
`battleNet=true` strongly suggests these are Battle.net ladder replays accidentally
bundled with the tournament dataset for IEM Katowice 2017 — not actual IEM match
replays. The standard IEM games use `competitive=false` (custom lobbies).

**Verdict:** NEAR-PASS — 22,387 / 22,390 replays (99.987%) have the expected flag
combination. The 3 outlier replays (competitive/amm/battleNet = true) are anomalous;
they appear to be ladder replays mislabelled as tournament replays.

**Cleaning rule for Phase 6 (Rule C-D1):** Exclude the 3 replays with `competitive=true`
(`amm=true`, `battleNet=true`) from the modelling corpus. These are not tournament games.
They come from `2017_IEM_XI_World_Championship_Katowice` only.

---

## Sub-step E — Random Race Detection (IMPORTANT)

**Expectation:** Most players should have `selectedRace` matching their `assigned_race`.
Empty `selectedRace` indicates the player selected Random; the assigned_race is then
drawn at game start. Explicit `Rand` in `selectedRace` confirms a Random selection.

### Query E1 — Selected race vs assigned race cross-tabulation

```sql
SELECT
    (entry.value->>'$.selectedRace') AS selected_race,
    (entry.value->>'$.race') AS assigned_race,
    COUNT(*) AS n_player_slots
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1, 2
ORDER BY 3 DESC;
```

**Result:**

| selected_race | assigned_race | n_player_slots |
|---------------|---------------|----------------|
| Prot          | Prot          | 15948          |
| Zerg          | Zerg          | 15123          |
| Terr          | Terr          | 12623          |
| (empty)       | Zerg          | 569            |
| (empty)       | Prot          | 276            |
| (empty)       | Terr          | 265            |
| Rand          | Prot          | 4              |
| Rand          | Zerg          | 3              |
| Rand          | Terr          | 3              |
| BWTe          | BWTe          | 1              |
| BWPr          | BWPr          | 1              |
| BWZe          | BWZe          | 1              |

**Observations:**

1. **Non-random locked races** (selectedRace in {Prot, Zerg, Terr} and matches
   assigned_race): 43,694 player slots — standard competitive play.

2. **Random race (empty selectedRace):** 1,110 player slots selected Random
   (empty `selectedRace` = Random picker in the game client). Assigned to Zerg
   (569), Prot (276), Terr (265). For feature engineering in Phase 7, the
   `assigned_race` (resolved at game start) is the correct race to use; the
   `selectedRace` field should NOT be used as a feature (it is null for Random
   players, not the actual race played).

3. **Explicit Rand in selectedRace:** 10 player slots with `selectedRace=Rand`.
   These overlap with the Random group above. Assigned to Prot (4), Zerg (3),
   Terr (3).

4. **BW race codes (BWTe, BWPr, BWZe):** 3 player slots with Brood War race codes.
   These are anomalous and likely correspond to the legacy Katowice replays or
   cross-version compatibility artefacts.

**Verdict:** INFORMATIONAL — Random race selection occurs in 1,120 player slots
(~2.5% of all slots). Feature engineering must use `assigned_race` (resolved race)
not `selectedRace`. The 3 BW race code slots are flagged for investigation.

**Cleaning rule for Phase 6 (Rule C-E1):** Flag replays containing BW race codes
(BWTe, BWPr, BWZe) for manual review; likely candidates for exclusion.

---

## Sub-step G — Map and Lobby Metadata Profiling (MINOR)

### Query G1 — maxPlayers distribution

```sql
SELECT
    (initData->'$.gameDescription'->>'$.maxPlayers')::INTEGER AS max_players,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1;
```

**Result:**

| max_players | n_replays |
|-------------|-----------|
| 2           | 21981     |
| 4           | 403       |
| 6           | 1         |
| 8           | 3         |
| 9           | 2         |

**Observation:** 409 replays have `maxPlayers > 2`. Standard 1v1 competitive maps
have `maxPlayers = 2`. The 409 non-2-player replays are on maps with more than 2
starting positions (4-player maps used for 1v1 are common in SC2 — players take
diagonally opposite positions). `maxPlayers` is a map-slot count, not a player-count;
it does not indicate these games were 2v2 or team games. The actual number of
active players can be confirmed via `ToonPlayerDescMap` key count.

### Query G2 — isBlizzardMap distribution

```sql
SELECT
    initData->'$.gameDescription'->>'$.isBlizzardMap' AS is_blizzard,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1;
```

**Result:**

| is_blizzard | n_replays |
|-------------|-----------|
| true        | 17515     |
| false       | 4875      |

**Observation:** 4,875 replays (21.8%) use non-Blizzard (community-made) maps.
This is expected for the SC2EGSet tournament corpus, which spans multiple eras
including periods where community maps were widely used in the GSL and WCS circuits.

### Query G3 — Fog of war

```sql
SELECT
    (initData->'$.gameDescription'->'$.gameOptions'->>'$.fog')::INTEGER AS fog,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1;
```

**Result:**

| fog | n_replays |
|-----|-----------|
| 0   | 22390     |

**Observation:** 100% of replays have fog = 0 (standard fog of war). PASS.

### Query G4 — Random races flag

```sql
SELECT
    initData->'$.gameDescription'->'$.gameOptions'->>'$.randomRaces' AS random_races,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1;
```

**Result:**

| random_races | n_replays |
|--------------|-----------|
| false        | 22390     |

**Observation:** 100% have `randomRaces=false`. This is the lobby-level random
races toggle (distinct from individual player random selection). PASS.

### Query G5 — Observers count

```sql
SELECT
    (initData->'$.gameDescription'->'$.gameOptions'->>'$.observers')::INTEGER AS observers,
    COUNT(*) AS n_replays
FROM raw
GROUP BY 1;
```

**Result:**

| observers | n_replays |
|-----------|-----------|
| 0         | 22390     |

**Observation:** 100% have 0 observers. PASS.

---

## Sub-step H — Version Consistency Check (MINOR)

**Expectation:** `header.version` and `metadata.gameVersion` should agree for all replays.

### Query H1 — Version mismatch detection

```sql
SELECT
    header->>'$.version' AS header_version,
    metadata->>'$.gameVersion' AS meta_version,
    COUNT(*) AS n
FROM raw
GROUP BY 1, 2
HAVING header_version != meta_version;
```

**Result:** 0 rows (no mismatches).

**Verdict:** PASS — `header.version` and `metadata.gameVersion` are consistent across
all 22,390 replays. No cleaning rule needed.

---

## Summary of Findings

| Sub-step | Topic | Status | Cleaning rule needed |
|----------|-------|--------|---------------------|
| A | Game speed | PASS — 100% Faster | None |
| B | Handicap | NEAR-PASS — 2/44817 phantom slots | Exclude by empty nickname (Phase 2) |
| C | Error flags | PASS — 0/22390 replays flagged | None |
| D | Game mode flags | NEAR-PASS — 3/22390 competitive | Rule C-D1: exclude competitive=true |
| E | Random race | INFORMATIONAL — 2.5% Random slots | Rule C-E1: use assigned_race; flag BW codes |
| G | Map/lobby metadata | PASS (all sub-queries nominal) | None |
| H | Version consistency | PASS — 0 mismatches | None |

### Phase 6 Cleaning Rules from this step

| Rule ID | Condition | Action |
|---------|-----------|--------|
| C-D1 | `competitive = true` (3 replays, all IEM Katowice 2017) | Exclude from modelling corpus |
| C-E1 | Player slot has BW race code (BWTe, BWPr, BWZe) — 3 slots | Flag for manual review / exclude host replay |

### Feature Engineering Notes (Phase 7)

- Use `assigned_race` (field: `ToonPlayerDescMap.race`) as the race feature, not
  `selectedRace`. The `selectedRace` is empty for Random players.
- The `maxPlayers` field reflects map slot count, not number of players; do not
  use it as a feature without validation against actual player count.
