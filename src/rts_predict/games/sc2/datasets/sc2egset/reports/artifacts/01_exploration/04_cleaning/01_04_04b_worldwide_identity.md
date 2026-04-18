# Step 01_04_04b -- Worldwide Player Identity VIEW (sc2egset)

**Date:** 2026-04-18
**Phase:** 01 -- Data Exploration
**Pipeline Section:** 01_04 -- Data Cleaning
**Dataset:** sc2egset
**Plan version:** R4

---

## Problem Restatement

Steps R1 (5-signal Fellegi-Sunter classifier), R2 (external bridge catalog), and
R3 (sha256 composite hash) were each rejected after deeper investigation of the
actual data.

**Actual finding:** `replay_players_raw.toon_id` is already stored as the full
Battle.net qualified identifier in `R-S2-G-P` format (e.g., `2-S2-1-315071` = Serral
on EU region, realm 1, profile 315071). The four segments are:
- Segment 1: region code (1=US, 2=Europe, 3=Korea, 5=China, 6=SEA, 98=Unknown/local)
- Segment 2: literal string "S2" (game identifier)
- Segment 3: realm/gateway code
- Segment 4: Blizzard-assigned profile ID (region-scoped integer)

`region` and `realm` columns in `replay_players_raw` are redundant derivations of
segments 1 and 3. **No hashing, no composite encoding, no external bridge needed.**
A thin decomposition VIEW is the honest answer.

---

## T01 -- Decomposition VIEW: `player_identity_worldwide`

### Column audit

| Column | Cardinality | Inferred Role |
|--------|----------:|---------------|
| toon_id | 2,495 (incl. 1 empty-string) | PRIMARY KEY (Battle.net R-S2-G-P qualifier) |
| nickname | 1,106 | DISPLAY NAME (not globally unique; changes with clan tag) |
| region | 6 | DERIVED LABEL (redundant with toon_id segment 1) |
| realm | 9 | DERIVED LABEL (redundant with toon_id segment 3) |
| userID | 16 | LOCAL PROFILE SLOT INDEX (0..15 = SC2 client slots; NOT player ID) |
| playerID | 9 | IN-GAME SLOT (1=player1, 2=player2 for 1v1) |

**userID cardinality=16 resolved empirically:** userID values 0-15 are the local
Battle.net profile slot indices stored in the replay header. SC2 clients support
up to 16 locally registered profiles. Cardinality=16 = the maximum number of
slots. userID is context metadata only, not useful as a player identifier.

### Format consistency probe

| Metric | Value |
|--------|------:|
| total rows | 44,817 |
| n_null | 0 |
| n_empty | 2 |
| n_canonical_format (LIKE '%-S2-%-%') | 44,815 |
| n_region_consistent | 44,815 |

All 44,815 canonical-format rows have region-code matching the `region` column label.
Zero inconsistencies.

### Nickname multiplicity discovery

The naive `SELECT DISTINCT` on all 7 columns yields 2,942 rows (not 2,494) because
273 toon_ids appear under multiple nicknames (clan-tag changes, renames over time).
The corrected DDL uses a `ROW_NUMBER()` CTE to pick the most-frequently-observed
nickname per toon_id (tie-broken alphabetically).

### Gate results

| Gate | Expected | Actual | Result |
|------|---------|--------|--------|
| Row count | 2,494 | 2,494 | PASS |
| Distinct player_id_worldwide | 2,494 | 2,494 | PASS |
| DESCRIBE 7 cols + dtypes | VARCHAR,INT,INT,BIGINT,VARCHAR,VARCHAR,VARCHAR | matches | PASS |
| Serral spot-check (2-S2-1-315071) | region=2, realm=1, profile=315071, Europe, 'Serral' | confirmed | PASS |
| Format probe n_canonical | 44,815 | 44,815 | PASS |
| Format probe n_empty | 2 | 2 | PASS |
| Region consistency | 0 inconsistencies | 0 | PASS |

**Note on row count vs plan:** Plan expected 2,495 (= 01_04_04 K1 =
`COUNT(DISTINCT toon_id)` including the empty-string toon_id counted as one
distinct value). The VIEW excludes empty-string rows via `LIKE '%-S2-%-%'` filter
→ 2,494 distinct player_id_worldwide values. This is correct behavior.

---

## T02 -- Outlier Investigation: 2 Empty-toon_id Rows

### Outlier context table

| Field | Outlier 1 | Outlier 2 |
|-------|-----------|-----------|
| filename | 2017_IEM_XI_World.../63a9f9bf...SC2Replay.json | 2019_HomeStory_Cup_XIX/.../0eba71d4...SC2Replay.json |
| tournament | 2017_IEM_XI_World_Championship_Katowice | 2019_HomeStory_Cup_XIX |
| date | 2017-02-27T11:10:20Z | 2019-06-27T14:49:26Z |
| map | Bel'Shir Vestige LE (Void) | Thunderbird LE |
| game_version | 3.10.1.49957 | 4.9.2.74741 |
| toon_id | '' (empty) | '' (empty) |
| nickname | '' (empty) | '' (empty) |
| region / realm | '' / '' | '' / '' |
| handicap | 0 | 0 |
| color_rgba | 0,0,0,0 | 0,0,0,0 |
| selectedRace | Rand | Rand |
| playerID | 2 | 2 |
| userID | 0 | 0 |
| APM | 20 | 6 |
| result | Win | Win |
| opponent_toon_id | 2-S2-1-3074703 | 2-S2-1-3437681 |
| opponent_nickname | <dPix>Optimus | <QLASH>Lambo |
| opponent_result | Loss | Loss |

### Narrative assessment

Both rows share a unique fingerprint: `handicap=0` and `color_rgba=(0,0,0,0)` are
**exclusive to these 2 rows** in the entire 44,817-row dataset. Combined with empty
string (not NULL) for all identity fields and `selectedRace='Rand'`, this pattern
is consistent with **observer-profile ghost entries**: the sc2egset replay parser
captured the replay-viewer's own local Battle.net profile (accessible to the parser
via the `ToonPlayerDescMap` stored in the replay header, indexed by `userID=0`) as
a second "player" row when no server-resolved identity was available.

The `result='Win'` for both ghost rows is the structural inverse of the opponent's
`result='Loss'` in the two-row-per-replay model -- not a genuine game outcome.

**Not a systematic tournament issue:** The two events (IEM Katowice 2017 and
HomeStory Cup XIX 2019) are separated by ~850 days, use different maps, and have
different game versions. These are isolated data-quality quirks from two distinct
replay files, not evidence of a pipeline-wide parsing defect in any one tournament.

**Disposition:** Filtered from `player_identity_worldwide` via the `LIKE '%-S2-%-%'`
clause. No upstream raw table modification (I9 preserved). Flagged for future
data-quality documentation.

---

## Region-Scoping Limitation

Blizzard assigns `profile_id` within each Battle.net region independently.
A physical player active on both EU and KR servers will have two distinct
`player_id_worldwide` values (e.g., `2-S2-1-315071` for EU and `3-S2-1-XXXXX` for
KR). This is a structural property of the replay format, not a data-quality defect.

**Why no external bridge exists:** R2 web-adversarial research (2026-04-18) confirmed
that no external source (Liquipedia, Aligulac, Blizzard OAuth, sc2pulse) delivers
cross-region profile-id linkage at bulk scale. Liquipedia ToS prohibits bulk scraping;
Aligulac uses internal IDs; Blizzard deprecated community API endpoints.

**Upgrade path:** A future manual tournament-roster PR could supply a supplemental
cross-region merge-mapping table for the handful of top-tier players (e.g., Serral,
Maru) known to compete under multiple regional accounts.

---

## Artifacts

- `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_04b_worldwide_identity.{py,ipynb}`
- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_identity_worldwide.yaml`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_04b_worldwide_identity.json`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_04b_worldwide_identity.md`
