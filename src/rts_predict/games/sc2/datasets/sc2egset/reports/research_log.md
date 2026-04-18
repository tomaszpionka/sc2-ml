# Research Log — SC2 / sc2egset

---

## 2026-04-18 -- [Phase 01 / Step 01_04_04b] Worldwide Identity VIEW — COMPLETE

**Category:** A (science)
**Dataset:** sc2egset
**Branch:** feat/01-04-04-sc2egset-worldwide-identity
**Scope:** Create player_identity_worldwide VIEW (decomposition of toon_id = full Battle.net R-S2-G-P qualifier). Investigate 2 empty-toon_id outlier rows.

### Key findings

| Finding | Value |
|---|---|
| VIEW row count | 2,494 (1 per distinct toon_id; 2 empty-string rows excluded) |
| Plan expected | 2,495 -- plan K1 counted empty-string as 1 distinct value; VIEW correctly excludes it |
| Distinct player_id_worldwide | 2,494 |
| DESCRIBE 7 cols + dtypes | VARCHAR, INTEGER, INTEGER, BIGINT, VARCHAR, VARCHAR, VARCHAR -- PASS |
| Serral spot-check | 2-S2-1-315071 -> region=2, realm=1, profile=315071, region_label='Europe' -- PASS |
| Format probe n_canonical | 44,815 -- PASS |
| Format probe n_empty | 2 -- PASS |
| Region consistency | 44,815/44,815 (0 inconsistencies) -- PASS |
| toon_ids with multiple nicknames | 273 (clan-tag changes); VIEW picks modal nickname |
| userID cardinality=16 | Local Battle.net profile slot indices (0..15); NOT player ID |
| Outlier 1 tournament | 2017_IEM_XI_World_Championship_Katowice |
| Outlier 1 date | 2017-02-27 |
| Outlier 1 opponent | <dPix>Optimus (toon_id 2-S2-1-3074703, EU, Terr, MMR 6603) |
| Outlier 2 tournament | 2019_HomeStory_Cup_XIX |
| Outlier 2 date | 2019-06-27 |
| Outlier 2 opponent | <QLASH>Lambo (toon_id 2-S2-1-3437681, EU, Zerg, MMR 6891) |
| Outlier fingerprint | handicap=0, color_rgba=0,0,0,0 -- UNIQUE in 44,817-row dataset |
| Outlier assessment | Observer-profile ghost entries (replay viewer's local profile captured by parser) |
| Temporal gap between outliers | ~850 days -- NOT clustered; isolated incidents |

### Outlier investigation verdict

Both empty-toon_id rows are observer-profile ghost entries: the sc2egset replay parser
captured the replay-viewer's local Battle.net profile (via ToonPlayerDescMap, userID=0 slot)
as a second player when no server-resolved identity was available. Unique fingerprint:
handicap=0 and color_rgba=(0,0,0,0) exclusive to these 2 rows. From different tournaments
(IEM 2017 vs HSC 2019), different maps, different game versions -- not a systematic issue.
Filtered from VIEW by LIKE filter; raw table untouched (I9).

### Artifacts produced

- `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_04b_worldwide_identity.py` + `.ipynb`
- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_identity_worldwide.yaml`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_04b_worldwide_identity.json` (8 SQL queries -- I6, 6 literature URLs)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_04b_worldwide_identity.md`

### Gate summary -- ALL PASS

- Gate 1 (VIEW row count = 2,494): PASS
- Gate 2 (DESCRIBE 7 cols + dtypes): PASS
- Gate 3 (Serral spot-check): PASS
- Gate 4 (format consistency probe): PASS
- Gate 5 (outlier JSON block with concrete values): PASS
- Gate 6 (schema YAML 7 cols + invariants + limitation note): PASS
- Gate 7 (JSON >= 6 SQL + >= 5 URLs): PASS (8 SQL, 6 URLs)
- Gate 8 (I9: no mutation of existing raw/view YAMLs): PASS
- Gate 9 (STEP_STATUS 01_04_04b = complete): PASS

### Observations & recommendations for Phase 02

**What this step delivers operationally:** `player_identity_worldwide` VIEW provides the
per-player-history key for Phase 02 rating-system backtesting (Elo, Glicko, Glicko-2,
TrueSkill, Aligulac-style BTL) and per-player feature engineering (rolling win rate,
head-to-head, streak, activity tempo).

#### Recommended per-player-history key per dataset

| dataset | key | source | namespace scope |
|---|---|---|---|
| sc2egset | `player_id_worldwide` (= full `R-S2-G-P` toon_id) | `player_identity_worldwide` VIEW | **region × realm × profile scoped (Blizzard design)** |
| aoestats | `profile_id` | `matches_1v1_clean` | global (same namespace as aoec per 01_04_04 VERDICT A) |
| aoe2companion | `profileId` | `matches_1v1_clean` | global (Microsoft-account-based) |
| cross-dataset | `(dataset_tag, player_id)` composite | `matches_history_minimal` | already in place from 01_04_03 |

#### KNOWN BIAS — cross-region player-split (sc2egset only)

`player_id_worldwide` is region-scoped by Blizzard's replay-format design. A physical human
active on multiple Battle.net regions is counted as **N distinct Elo entities** (one per
region). Empirical upper bound from 01_04_04 findings:

- **246 case-sensitive nicknames** observed across multiple regions
- **294 Class A pairs** (temporal overlap >= 1 day across regions) — strongest multi-account candidates
- **Upper bound: ~294 / 2,494 ≈ 12% of sc2egset entities are likely multi-region artifacts**

This is **accepted as a documented thesis-level corpus limitation**, analogous to the missing-
offline-games limitation (also structural, also inherited from upstream data). Thesis
Chapter 4 §4.2.2 must disclose both limitations as scope caveats. Neither blocks Phase 02
methodology.

#### What NOT to use as player-history key (empirically rejected)

| anti-pattern | rejection reason |
|---|---|
| `nickname` alone | 30.6% within-region collision rate (451 / 1,473 pairs) → merges distinct physical players |
| `LOWER(nickname)` alone | 6x Christen 2012 Ch. 5 threshold (5%); user directive: case-sensitive only |
| `(nickname, region)` | Still has within-region collisions (30.6% rate) |
| sha256 composite of `(region, realm, toon_id)` | Redundant encoding (toon_id already contains these segments); destroys human-readable form |
| Behavioral fingerprint (APM-JSD, race, clanTag, MMR, temporal) | Over-engineering; statistically weak null/control at available sample sizes; circularity (identity-null assumes same-toon_id = same human) |
| External bridge (Liquipedia, Aligulac, sc2pulse, Blizzard OAuth) | Web-verified infeasible: no public source exposes (nickname → region-scoped profile-id) at bulk scale |

#### External-bridge infeasibility summary (R2 web-verified adversarial)

- **Liquipedia pages** do not expose region-scoped Battle.net profile-ids (only aliases + ratings). ToS: HTML scraping forbidden; LiquipediaDB API capped at 60 req/hr.
- **Blizzard Community API / OAuth** cannot bulk-resolve third-party battletag → profile-id (requires each player's own consent via OAuth).
- **Aligulac API** exposes internal IDs only, not Battle.net profile-ids.
- **sc2pulse** is ladder-only + a Blizzard API consumer (inherits region-scoping).

Cited sources in artifact JSON `literature` block.

#### Upgrade path (documented, not blocking)

Future manual tournament-roster curation PR could add a supplemental
`player_identity_merge_map(player_id_worldwide, canonical_human_id)` table for the ~294
Class A multi-region candidates. Manual work (~week of hand-curation via Liquipedia Serral-
style player pages + ESL/HSC/WCS roster publications), high confidence. Current VIEW design
is forward-compatible: adding a supplemental merge map does not break existing joins on
`player_id_worldwide`. Deferred unless thesis defense feedback surfaces need.

#### Phase 02 guidance

- **Elo/Glicko/TrueSkill backtesting:** GROUP BY `player_id_worldwide`. Parallel independent trajectories for multi-region humans. Matches Aligulac / sc2pulse / Liquipedia industry standard.
- **Activity features** (recent-games, win rate, head-to-head, streak): compute per `player_id_worldwide`. No cross-region leakage risk.
- **Cross-dataset experiments:** `(dataset_tag, player_id)` composite via `matches_history_minimal` (already in place from 01_04_03).
- **Sensitivity analysis candidate** (post-hoc, optional in thesis): how would Elo trajectories change if all 294 Class A pairs were manually merged? Quantifies the 12% bias's magnitude on downstream metrics.

#### Connection to 01_04_04 decision ledger

`DS-SC2-IDENTITY-05` recommended "toon_id as granular entity + LOWER(nickname) merge only for Class A overlap pairs." This step (01_04_04b) **inverts the LOWER(nickname) part** of that recommendation — behavioral fingerprinting proved over-engineered and external-bridge inaccessible, so the simpler honest answer is: **granular toon_id only, document the 12% bias**. The Class A merge is deferred to the future manual-curation upgrade path, not attempted programmatically here.

---

## 2026-04-18 -- [Phase 01 / Step 01_04_04] Identity Resolution — COMPLETE

**Category:** A (science)
**Dataset:** sc2egset
**Branch:** fix/01-04-null-audit
**Scope:** Exploratory identity-resolution census. No new VIEWs (I9). Routes 5 DS-SC2-IDENTITY-* decisions to Phase 02.

### Key findings

| Finding | Value |
|---|---|
| K1: n_distinct(toon_id) | 2,495 |
| K2: n_distinct((region,realm,toon_id)) | 2,495 (= K1, confirming region-scoping) |
| K3: n_distinct(LOWER(nickname)) | 1,045 |
| K4: n_distinct((LOWER(nick),region)) | 1,473 |
| K5: n_distinct((LOWER(nick),region,realm)) | 1,487 |
| K_cs: n_distinct(nickname) case-sensitive | 1,106 |
| I7 ratio (case-sensitive, per 01_02_04) | 2495/1106 = 2.2559 -- PASS (target 2.257 +/- 0.05) |
| LOWER(nickname) ratio | 2495/1045 = 2.3876 (outside gate; 61 case variants merged) |
| Cross-region toon_ids | 0 (Battle.net scoping confirmed) |
| Temporal Class A (overlap >=1d) | 294 pairs |
| Temporal Class B (disjoint) | 15,474 pairs |
| Temporal Class C (degenerate) | 317 pairs |
| Within-region collisions | 451 / 1,473 (nick,region) pairs = 30.6% |
| Christen 2012 Ch. 5 threshold | 5% (EXCEEDED by 6x) |
| userID cardinality | 16 (confirmed slot index 0..15) |
| Unknown region | 12.83% of rows |

### DS-SC2-IDENTITY-01..05 Decision ledger

- **DS-SC2-IDENTITY-01:** REJECT toon_id-alone. Over-splits multi-server players (Serral has 42 toon_ids). Routed to Phase 02 canonical identity VIEW design.
- **DS-SC2-IDENTITY-02:** REJECT LOWER(nickname)-alone. Within-region collision rate 30.6% >> 5% threshold (Christen 2012). Routed to Phase 02 blocking strategy design.
- **DS-SC2-IDENTITY-03:** Class A overlap pairs (294) are strong same-player candidates. Class B disjoint (15,474) are ambiguous -- conservative = separate Elo entities. Routed to Phase 02 entity resolution classifier.
- **DS-SC2-IDENTITY-04:** Treat 'Unknown' as a valid region value. Do NOT merge Unknown-region toon_ids with known-region toon_ids without temporal evidence. Routed to Phase 02 Unknown region handling.
- **DS-SC2-IDENTITY-05:** Recommended Phase 02 strategy: toon_id as granular entity + LOWER(nickname) merge only for Class A overlap pairs. Routed to Phase 02 canonical player_identity_canonical VIEW + Elo cold-start sensitivity analysis.

### Thesis §4.2.2 [REVIEW] marker status

Not closable at this step (Category F follow-up after Phase 02 design lands).
Empirical basis is now established by this step's artifacts.

### Artifacts produced

- `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_04_identity_resolution.py` + `.ipynb`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_04_identity_resolution.json` (8 SQL queries -- I6)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_04_identity_resolution.md`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_04_cross_region_nicknames.csv` (246 rows)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_04_within_region_handle_collisions.csv` (451 rows)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/plots/01_04_04_key_cardinality_bars.png`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/plots/01_04_04_toon_region_heatmap.png`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/plots/01_04_04_nickname_cross_region_stacked.png`

### Gate summary -- ALL PASS

- Gate 1 (artifacts non-empty): PASS (JSON 14.6KB, MD 7.3KB, 2 CSVs, 3 PNGs ~60KB each)
- Gate 2 (8 SQL queries in JSON, I6): PASS
- Gate 3 (5 DS-SC2-IDENTITY-* decisions): PASS
- Gate 4 (I9 -- no schema YAML diff): PASS
- Gate 5 (ratio 2.2559 within 2.257+/-0.05): PASS
- Gate 6 (STEP_STATUS 01_04_04=complete, PIPELINE_SECTION 01_04=complete): PASS

---

## 2026-04-18 -- [Phase 01 / Step 01_04_02] Data Cleaning Execution — ADDENDUM: duration_seconds + is_duration_suspicious (28 → 30 cols)

**Category:** A (science)
**Dataset:** sc2egset
**Branch:** feat/01-04-02-duration-augmentation
**Scope:** ADDENDUM to 01_04_02. Extended `matches_flat_clean` VIEW from 28 → 30 columns by adding `duration_seconds` BIGINT and `is_duration_suspicious` BOOLEAN (both POST_GAME_HISTORICAL). STEP_STATUS stays complete per addendum precedent.

### Columns added

| col | dtype | token | derivation |
|---|---|---|---|
| `duration_seconds` | BIGINT | POST_GAME_HISTORICAL | `CAST(ANY_VALUE(header_elapsedGameLoops) / 22.4 AS BIGINT)` per replay_id via LEFT JOIN to aggregated `player_history_all` |
| `is_duration_suspicious` | BOOLEAN | POST_GAME_HISTORICAL | `duration_seconds > 86400` |

### I7 provenance (22.4 loops/sec)
SC2 "Faster" game-speed constant — empirically justified by `details.gameSpeed` cardinality=1 in sc2egset (W02 census, research_log.md:424) + Blizzard SC2 documentation. Established in 01_04_03 ADDENDUM.

### I8 provenance (86,400s threshold)
Cross-dataset canonical sanity bound (~25x p99 for sc2egset). Identical across sc2egset, aoestats, aoe2companion.

### Duration stats (sc2egset)
- min: 1s
- p50: 651s (~10.9 min)
- p99: 1,876s (~31 min)
- max: 6,073s (~1.7 hours)
- null_count: 0
- suspicious_count (>86400s): 0 (sc2egset has no duration outliers)

### Gate summary — ALL 9 GATES PASS
- Gate 1 (30 cols): PASS
- Gate 2 (last 2 = duration_seconds BIGINT + is_duration_suspicious BOOLEAN): PASS
- Gate 3 (row count 44,418 unchanged): PASS
- Gate 4 (null duration_seconds = 0): PASS
- Gate 5 (MAX <= 1e9 unit canary): PASS (max=6,073)
- Gate 6 (I5 symmetry, IS DISTINCT FROM violations = 0): PASS
- Gate 6b (suspicious_count = 0, sc2egset HALTING): PASS
- Gate 7 (schema YAML: 30 cols + schema_version + I3/I7 invariants): PASS
- Gate 8 (I9: upstream YAMLs untouched): PASS
- Gate 9 (JSON all_assertions_pass: true + SQL verbatim): PASS

### Artifacts produced
- `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_02_duration_augmentation.py` + `.ipynb`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_02_duration_augmentation.json`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_02_duration_augmentation.md`
- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/matches_flat_clean.yaml` (UPDATED to 30 cols + schema_version)

---

## 2026-04-18 -- [Phase 01 / Step 01_04_03] Minimal Cross-Dataset History View — ADDENDUM: duration_seconds (9-col extension)

**Category:** A (science)
**Dataset:** sc2egset
**Branch:** feat/01-04-03-aoe2-minimal-history (cross-dataset PR; extends PR #152 sibling)
**Scope:** Extended `matches_history_minimal` VIEW from 8 cols → 9 cols by adding `duration_seconds` BIGINT (POST_GAME_HISTORICAL). Sibling extension simultaneous across aoestats + aoe2companion (same PR).

### Column added

| col | dtype | derivation |
|---|---|---|
| `duration_seconds` | BIGINT | `CAST(ANY_VALUE(header_elapsedGameLoops) / 22.4 AS BIGINT)` per replay_id, via JOIN to aggregated `player_history_all` (R1-BLOCKER-A2 fix — `header_elapsedGameLoops` is NOT in `matches_flat_clean` or `matches_long_raw`; only `player_history_all` retains it at line 112). |

### I7 provenance (sc2egset)
22.4 loops/sec SC2 "Faster" game-speed constant — empirically justified by `details.gameSpeed` cardinality=1 in sc2egset (W02 census, research_log.md:424 in this dataset) + Blizzard SC2 documentation.

### Duration stats (sc2egset)
- min: 1s
- max: 6,073s (~1.7 hours)
- avg: ~720s (~12 min)
- null_count: 0
- outlier_count_gt_86400: 0 (sc2egset has no data-quality outliers — contrast aoestats 56 rows, aoec 142 rows flagged for 01_04_02 augmentation follow-up PR)

### Gate summary — ALL PASS (17 gates: 12 original + 5 duration)
- Gate +1 (9 cols): PASS
- Gate +2 (null_duration): 0
- Gate +3 (non-positive): 0
- Gate +4 (duration symmetry via IS DISTINCT FROM): 0 violations
- Gate +5a (max ≤ 1e9 — unit regression canary, HALTING): PASS (max 6,073)
- Gate +5b (outliers > 86400, REPORT-ONLY): 0 rows

### Cross-dataset I8 contract update
9-col contract sealed across 3/3 datasets (sc2egset + aoestats + aoe2companion) with identical column names, dtypes, grain, and `POST_GAME_HISTORICAL` token on duration_seconds. Consumers that drop POST_GAME_HISTORICAL tokens will auto-exclude duration from PRE_GAME feature sets (I3-safe default).

### Deferred follow-up PRs (per user-approved scope sequencing 2026-04-18)
- **01_04_02 augmentation PR:** add `duration_seconds` + `is_duration_suspicious` to all 3 clean views (would make 01_04_03 a pure pass-through and centralize outlier flagging).
- **01_04_04 Identity Resolution PR:** empirical census of sc2egset `toon_id` cross-region uniqueness (toon_id is region-scoped per Battle.net account model — not globally unique), aoestats `profile_id` stability, aoe2companion `profileId` stability, cross-dataset identity mapping. Per user directive 2026-04-18: "sc2 for example cannot have constant toon_ids over multiple servers/regions".

### Adversarial cycle for this extension
Pre-exec R1: 3 BLOCKERs found (A1 aoestats unit, A2 sc2egset source, A3 multiplicity) + 4 WARNINGs — all fixed in plan before execution. Post-exec: not run separately (sibling datasets' execution = empirical adversarial; all 54+ gates PASS across 3 datasets confirms plan correctness).

---

## 2026-04-18 -- [Phase 01 / Step 01_04_03] Minimal Cross-Dataset History View

**Category:** A (science)
**Dataset:** sc2egset (pattern-establisher)
**Step scope:** Create `matches_history_minimal` VIEW — 8-column player-row-grain projection of `matches_flat_clean` with canonical TIMESTAMP temporal dtype. Cross-dataset-harmonized substrate for Phase 02+ rating-system backtesting (Elo, Glicko, Glicko-2, TrueSkill, Aligulac race-conditioned, Bradley–Terry, Neural BTL). Non-destructive (I9); reverted 01_04 to `in_progress` during execution, back to `complete` on gate pass.

### Schema (8 columns, 2 rows per match)

| column | dtype | semantics |
|---|---|---|
| match_id | VARCHAR | `'sc2egset::' + 32-char hex replay_id` (length = 42) |
| started_at | TIMESTAMP | `TRY_CAST` of `details_timeUTC`; canonical cross-dataset dtype |
| player_id | VARCHAR | Battle.net toon_id |
| opponent_id | VARCHAR | Opposing toon_id |
| faction | VARCHAR | Raw race stems `Prot`/`Terr`/`Zerg` (4-char; NOT full names). PER-DATASET POLYMORPHIC |
| opponent_faction | VARCHAR | Opposing race (mirror) |
| won | BOOLEAN | Focal player's outcome (complementary between the 2 rows) |
| dataset_tag | VARCHAR | Constant `'sc2egset'` |

### Row-count flow
- Source `matches_flat_clean`: 44,418 rows / 22,209 replays (1v1 decisive)
- `matches_history_minimal`: 44,418 rows / 22,209 distinct match_ids / 2 rows per match_id

### Gate verdict — all PASS

| # | Criterion | Result |
|---|---|---|
| G1 | Artifacts exist (.py, .ipynb, .json, .md, .yaml) | PASS |
| G2 | DESCRIBE 8 cols; dtypes `[VARCHAR, TIMESTAMP, VARCHAR, VARCHAR, VARCHAR, VARCHAR, BOOLEAN, VARCHAR]` | PASS |
| G3 | Row counts 44,418 / 22,209 / 22,209 / 0 | PASS |
| G4 | I5-analog symmetry violations (IS DISTINCT FROM, NULL-safe) | 0 |
| G5 | I8 prefix violations (length == 42) | 0 |
| G6 | dataset_tag distinct == 1, value `'sc2egset'` | PASS |
| G7 | Zero NULLs in match_id / player_id / opponent_id / won / dataset_tag | PASS |
| G8 | started_at dtype TIMESTAMP; null_started_at reported (=0) | PASS |
| G9 | I9 upstream YAML byte-identical (`git diff --stat` empty for matches_flat_clean.yaml, player_history_all.yaml, matches_long_raw.yaml) | PASS |
| G11 | Validation JSON `all_assertions_pass: true`; `sql_queries` block verbatim; `describe_table_rows` captured | PASS |

### Faction vocabulary (empirical)

| faction | count |
|---|---|
| `Prot` | 16,121 |
| `Zerg` | 15,527 |
| `Terr` | 12,770 |

4-char stems confirmed (not full `Protoss`/`Terran`/`Zerg`). Upstream `matches_flat_clean.race` nullable semantics preserved; faction nullable: true.

### Temporal sanity
- `min_started_at`: `2016-01-07 02:21:46.002000`
- `max_started_at`: `2024-12-01 23:48:45.251161`
- `null_started_at`: 0 (zero TRY_CAST failures)
- `distinct_started_at`: 22,164

### Cross-dataset contract established (I8) — limits explicit
aoestats and aoe2companion follow-up PRs must emit views with:
- identical 8-column names and order
- canonical TIMESTAMP `started_at` (aoestats CAST AT TIME ZONE 'UTC' from TIMESTAMPTZ; aoe2companion pass-through)
- same grain (2 rows per match) — aoestats UNIONs `p0/p1` halves of its 1-row-per-match clean view (team1_wins ~52.27% slot-asymmetry awareness required)
- NULL-safe IS DISTINCT FROM symmetry assertion
- dataset_tag literals `'aoestats'` / `'aoe2companion'`
- match_id prefixes `'aoestats::'` / `'aoe2companion::'`
- `faction` values per-dataset polymorphic (SC2 race stems vs AoE2 civ names); consumers MUST game-condition

### aoestats sibling PR column mapping (deferred execution)
- `aoestats.p{0,1}_profile_id → player_id`
- `aoestats.p{0,1}_civ → faction` (raw per-dataset polymorphic civ vocabulary)
- `aoestats.p{0,1}_winner → won` (TARGET — aoestats YAML flags `p_winner` as POST_GAME_HISTORICAL; acceptable here since `won` IS the prediction target in `matches_history_minimal`)

### Decisions taken
- Source = `matches_flat_clean` (built-in 1v1-decisive filter; avoids double projection).
- match_id prefix applied in-view (not upstream) — preserves I9.
- `faction = race` (actual), NOT `selectedRace` (which includes `'Random'`).
- `started_at` TIMESTAMP-cast in-view (R1-BLOCKER-2 fix; resolves 3-way dtype split VARCHAR/TIMESTAMPTZ/TIMESTAMP at the contract level).
- I5-analog symmetry SQL uses `IS DISTINCT FROM` (R1-BLOCKER-3 fix; NULL-safe).
- Minimal view excludes MMR / is_mmr_missing / map / version: Phase 02 consumers join from `matches_flat_clean` on `(match_id, player_id)`.
- Polymorphic `faction` column chosen over separate `sc2_race` / `aoe2_civ` for substrate simplicity; game-conditional encoding happens in Phase 02 feature extractors (dataset_tag is the ontological disambiguator).

### Decisions deferred
- Faction enum harmonization (Phase 02; current contract is explicit polymorphism).
- Canonical nickname resolution (Phase 01_05+).

### Adversarial review cycle (Cat A, up-to-3 cap per user directive)
- R1: 5 BLOCKERs / 7 WARNINGs → REQUIRE_REVISION
- R2: all R1 fixes FIX-VERIFIED; 3 new WARNINGs + 5 NOTEs → APPROVE_WITH_WARNINGS
- R3: all R2 fixes FIX-VERIFIED; 2 cosmetic NOTEs → APPROVE_WITH_WARNINGS

### Artifacts produced
- `reports/artifacts/01_exploration/04_cleaning/01_04_03_minimal_history_view.json` (NEW)
- `reports/artifacts/01_exploration/04_cleaning/01_04_03_minimal_history_view.md` (NEW)
- `data/db/schemas/views/matches_history_minimal.yaml` (NEW)
- DuckDB VIEW `matches_history_minimal` (NEW)

### Thesis mapping
- Chapter 4 — Data and Methodology > 4.1.1 SC2EGSet > Cross-dataset harmonization substrate
- Chapter 4 — Data and Methodology > 4.3 Rating System Backtesting Design (downstream consumer)

### Open follow-ups
- aoestats, aoe2companion sibling PRs produce matching views.
- Phase 02 defines canonical UNION ALL view.

---

## 2026-04-17 -- [Phase 01 / Step 01_04_02] Data Cleaning Execution

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** Acts on DS-SC2-01..10. Modifies matches_flat_clean and player_history_all VIEW DDL. No raw changes (I9). Closes Pipeline Section 01_04.

### CONSORT column-count flow

| VIEW | Cols before | Cols dropped | Cols added | Cols modified | Cols after |
|---|---|---|---|---|---|
| matches_flat_clean | 49 | 21 | 0 | 0 | 28 |
| player_history_all | 51 | 16 | 2 | 1 (APM) | 37 |

Row counts unchanged (column-only cleaning step):
- matches_flat_clean: 44,418 rows / 22,209 replays (before and after)
- player_history_all: 44,817 rows / 22,390 replays (before and after)

### Decisions resolved

| DS ID | Column | Decision |
|---|---|---|
| DS-SC2-01 | MMR | DROP from both VIEWs; retain is_mmr_missing flag |
| DS-SC2-02 | highestLeague | DROP from both VIEWs |
| DS-SC2-03 | clanTag | DROP from both VIEWs; retain isInClan |
| DS-SC2-04 | result | RETAIN literal strings; ADD is_decisive_result = (result IN ('Win','Loss')) |
| DS-SC2-05 | selectedRace | NO-OP (upstream normalisation already applied) |
| DS-SC2-06 | gd_mapSizeX/gd_mapSizeY | DROP from matches_flat_clean; RETAIN in player_history_all |
| DS-SC2-07 | gd_mapAuthorName | DROP from matches_flat_clean; RETAIN in player_history_all |
| DS-SC2-08 | go_* constants (12) | DROP all 12 from both VIEWs |
| DS-SC2-09 | handicap | DROP handicap + is_handicap_anomalous (near-constant) |
| DS-SC2-10 | APM | NULLIF(mf.APM, 0) + ADD is_apm_unparseable flag |

### Gate verdict

All 18 validation assertions PASS. Key invariants confirmed:
- matches_flat_clean: 28 columns, 44,418 rows, 22,209 replays, 0 symmetry violations
- player_history_all: 37 columns, 44,817 rows, 22,390 replays, 1132 APM NULLs (expected), 26 non-decisive rows (expected)
- All forbidden columns absent (21 from matches_flat_clean, 16 from player_history_all)
- New columns present: is_decisive_result (BOOLEAN), is_apm_unparseable (BOOLEAN)

### Artifacts produced

- `reports/artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.json` (NEW)
- `reports/artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.md` (NEW)
- `data/db/schemas/views/matches_flat_clean.yaml` (NEW — 28 cols + I3/I5/I6/I9/I10 invariants block)
- `data/db/schemas/views/player_history_all.yaml` (UPDATED — 37 cols + extended I3 provenance_categories + I10)
- **DuckDB VIEWs:** matches_flat_clean (28 cols), player_history_all (37 cols)

### Status update

- STEP_STATUS.yaml: 01_04_02 -> complete
- PIPELINE_SECTION_STATUS.yaml: 01_04 -> complete (no 01_04_03+ steps defined in ROADMAP)

---

## 2026-04-17 -- [Phase 01 / Step 01_04_01 — PART B] Missingness Audit (insight-gathering)

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** Consolidated missingness audit over matches_flat_clean and player_history_all.
Two coordinated census passes (NULL + sentinel) per VIEW plus runtime constants detection,
feeding one missingness ledger (CSV+JSON) per VIEW. Audit is read-only (I9);
no VIEWs modified, no columns dropped or imputed.

### Ledger summary

| VIEW | Total columns | With missingness | Constants (DROP) |
|------|--------------|-----------------|------------------|
| matches_flat_clean | 49 | per ledger | 0 |
| player_history_all | 51 | per ledger | 0 |

(Combined ledger: 100 rows, 17 columns per Deliverable 5.B)

### Key sentinel findings (from ledger)

- **MMR**: sentinel=0, n_sentinel=37,290 in matches_flat_clean (83.95%), n_sentinel=37,489 in player_history_all (83.65%). Recommendation: DROP_COLUMN (>80% Rule S4). Source: 01_03_01 MAR-primary mechanism.
- **highestLeague**: sentinel='Unknown', ~72% in both VIEWs. Recommendation: DROP_COLUMN.
- **clanTag**: sentinel='', ~73.93% in player_history_all. Recommendation: DROP_COLUMN.
- **result** in matches_flat_clean: 0 NULLs, 0 sentinels → F1 override → mechanism=N/A, recommendation=RETAIN_AS_IS.
- **result** in player_history_all: n_sentinel=26 (Undecided/Tie rows, 0.058%) → target-override (B4) → EXCLUDE_TARGET_NULL_ROWS.
- **gd_mapSizeX/Y**: n_sentinel=0 in both VIEWs (VIEW CASE-WHEN converts 0 to NULL; audit sees the NULLs not the original 0s).
- **handicap**: sentinel=0, n_sentinel=2 (0.0045%) → CONVERT_SENTINEL_TO_NULL (W3 branch, carries_semantic_content=True — non-binding).
- **APM** (player_history_all only): sentinel=0, n_sentinel=1,132 (2.53%) → CONVERT_SENTINEL_TO_NULL (non-binding; DS-SC2-10).
- **go_*** columns: no constants detected (all have n_distinct > 1 in both VIEWs per runtime detection).

### Decisions surfaced for 01_04_02+

DS-SC2-01 through DS-SC2-10 — see artifact and ROADMAP `decisions_surfaced` block.
New decisions added in this revision: DS-SC2-09 (handicap anomalous 0) and DS-SC2-10 (APM=0 sentinel).

### Artifacts produced

- `artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv` (NEW)
- `artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.json` (NEW)
- `artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json` (extended with `missingness_audit` block)
- `artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md` (extended with Missingness Ledger + Decisions sections)
- `ROADMAP.md` 01_04_01 step block replaced with Deliverable 1.A (decisions_surfaced DS-SC2-01..10)

### Connection normalization (W4)

All 58 existing `con.con.execute(...)` calls in the sc2egset notebook converted to `con.execute(...)`
via the two-step rename: `con = get_notebook_db(...)` → `db = get_notebook_db(...)` + `con = db.con`.
Verified: `grep -c 'con.con.execute'` returns 0.

### Schema YAML cleanup (N1, post-reviewer-deep)

Plan-code annotations (`R02`/`R04`/`R05`/`R07`/`W03`/`W04`) stripped from
`data/db/schemas/views/player_history_all.yaml` column descriptions per
`feedback_no_plan_codes_in_docs`. Description-only edits — no DDL, type, or
nullability changes. Flagged by reviewer-deep NOTE-1; documented here for
audit-trail completeness.

---

## 2026-04-16 -- [Phase 01 / Step 01_04_00] Source Normalization to Canonical Long Skeleton

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** Create matches_long_raw VIEW. INNER JOIN replay_players_raw x replays_meta_raw into 10-column canonical schema.
**Artifacts produced:**
- `reports/artifacts/01_exploration/04_cleaning/01_04_00_source_normalization.json`
- `reports/artifacts/01_exploration/04_cleaning/01_04_00_source_normalization.md`
- `data/db/schemas/views/matches_long_raw.yaml`
- **DuckDB VIEW:** `matches_long_raw`

### What

Created `matches_long_raw` VIEW: canonical 10-column long skeleton (match_id, started_timestamp,
side, player_id, chosen_civ_or_race, outcome_raw, rating_pre_raw, map_id_raw, patch_raw,
leaderboard_raw). Structural INNER JOIN of replay_players_raw x replays_meta_raw via
hex-hash regexp key (same as matches_flat). 44,817 rows. leaderboard_raw = NULL for all rows.

### Why

Unify grain across all three datasets before downstream cleaning.

### How (reproducibility)

Notebook: `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_00_source_normalization.py`

### Findings

- **Lossless check PASSED:** 44,817 rows (matches_long_raw == direct JOIN count).
- **Side values:** Distinct values 0-8. Side=0: 22,390 rows (playerID=1); side=1: 22,387 rows (playerID=2).
  Values 2-8: 37 rows total (rare multi-player/observer slots).
- **Symmetry audit (side IN (0,1)):**
  side=0: 22,390 rows, win_pct=51.96%, n_null=13.
  side=1: 22,387 rows, win_pct=47.97%, n_null=13.
  Mild asymmetry: side=0 wins ~52% (3.99pp deviation). Alert threshold (10pp) not breached.
- **leaderboard_raw:** NULL for all 44,817 rows (tournament dataset, no matchmaking ladder).
- **NULL match_id:** 0 rows (NULLIF guard effective; all filenames match the hex-hash pattern).
- **started_timestamp type:** VARCHAR (details.timeUTC struct dot notation). Type unification deferred to Phase 02.

### Decisions taken

- details.timeUTC accessed via struct dot notation (rm.details.timeUTC).
- NULLIF guard included for match_id (consistent with matches_flat in 01_04_01).
- leaderboard_raw = NULL constant (deliberate; tournament data).

### Decisions deferred

- started_timestamp type unification (VARCHAR -> TIMESTAMP) deferred to Phase 02.
- MMR sentinel 0 (unrated) handling deferred to Phase 02.
- Side=0 win asymmetry (51.96% vs 47.97%) documented; not corrected at this step.

### Thesis mapping

- Chapter 4, §4.1.1 -- SC2EGSet dataset description, data normalization

---

## 2026-04-16 -- [Phase 01 / Step 01_04_01] Data Cleaning

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** Non-destructive cleaning -- creates 3 DuckDB VIEWs (matches_flat,
matches_flat_clean, player_history_all)
**Revision:** 1 (incorporates critique BLOCKER F01, WARNINGS W02-W05)
**Artifacts produced:**
- `reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json`
- `reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md`
- `data/db/schemas/views/player_history_all.yaml`

### What

Created three DuckDB VIEWs resolving the F01 structural blocker (matches_flat
JOIN) and implementing the dual-scope cleaning design:

1. **matches_flat** (44,817 rows / 22,390 replays): Structural JOIN of
   replay_players_raw x replays_meta_raw via NULLIF-guarded regexp_extract.
   No filters. All columns retained.

2. **matches_flat_clean** (44,418 rows / 22,209 replays): Prediction target
   VIEW. True 1v1 decisive only (R01: -24 replays). MMR<0 replays excluded
   at REPLAY level (R03: -157 replays, BLOCKER F01 fix). PRE-GAME features
   only (I3: APM, SQ, supplyCappedPercent, header_elapsedGameLoops excluded).
   Constant columns excluded (W02: gameSpeed). Duplicate column excluded
   (W03: gd_isBlizzardMap). No APM-derived flags (W05).

3. **player_history_all** (44,817 rows / 22,390 replays): Player feature
   history VIEW. All replays retained (including non-1v1 and indecisive).
   APM, SQ, supplyCappedPercent, header_elapsedGameLoops RETAINED as valid
   IN_GAME_HISTORICAL signals for prior matches.

### CONSORT Flow (REPLAY units)

| Stage | Replays | Rows |
|-------|---------|------|
| Raw (replays_meta_raw) | 22,390 | -- |
| Raw (replay_players_raw) | -- | 44,817 |
| matches_flat (JOIN) | 22,390 | 44,817 |
| After R01 (true_1v1_decisive) | 22,366 | 44,732 |
| R01 excluded (non-1v1 + indecisive) | -24 | -85 |
| After R03 (MMR<0 replay-level) | 22,209 | 44,418 |
| R03 excluded (any MMR<0 player) | -157 | -314 |
| **matches_flat_clean (final)** | **22,209** | **44,418** |
| player_history_all (all replays) | 22,390 | 44,817 |

R03 is a REPLAY-LEVEL exclusion (BLOCKER F01 fix). Row-level filtering would
orphan the opponent's row, breaking the 2-per-replay invariant.

### Key Findings

- isBlizzardMap duplication: gd_isBlizzardMap == details_isBlizzardMap for
  all 44,817 rows (mismatch=0). gd_isBlizzardMap excluded from downstream VIEWs.
- gameSpeed constant: cardinality=1 for both details_gameSpeed and gd_gameSpeed.
  Both excluded from downstream VIEWs (W02).
- NULLIF guard: null_replay_id=0 in matches_flat (W04 fix verified).
- R03 scope: all 157 MMR<0-containing replays are in true_1v1_decisive scope
  (not already excluded by R01).
- Result distribution in matches_flat_clean: 50.0% Win / 50.0% Loss (perfect).
- Symmetry: 0 violations (every clean replay has exactly 1 Win + 1 Loss row).
- Unique players in player_history_all: 2,495 distinct toon_ids.
- selectedRace normalization: 1,110 empty strings normalized to 'Random' (R04).
- SQ sentinel: 2 rows with INT32_MIN -> NULL in player_history_all (R05).
- map_size=0: 273 replays (271 also in 1v1_decisive scope); flagged, not excluded.

### Critique Fixes Applied

- **F01 (BLOCKER):** R03 replay-level CTE (mmr_valid). 157 replays excluded.
- **W02:** gameSpeed columns excluded (verified constant, cardinality=1).
- **W03:** gd_isBlizzardMap excluded (verified identical, mismatch=0).
- **W04:** NULLIF wrapper on regexp_extract. null_replay_id=0 confirmed.
- **W05:** No APM-derived columns in any VIEW.

---

## 2026-04-15 -- [Phase 01 / Step 01_03_04] Event Table Profiling

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** profiling -- deep structural profile of 3 event views
**Artifacts produced:**
- `reports/artifacts/01_exploration/03_profiling/01_03_04_event_profiling.json`
- `reports/artifacts/01_exploration/03_profiling/01_03_04_event_profiling.md`

### What

Deep structural profiling of all three event views unique to sc2egset:
tracker_events_raw (62,003,411 rows, 10 event types), game_events_raw
(608,618,823 rows, 23 event types), message_events_raw (52,167 rows, 3
event types). Profiled event type distributions, per-replay density,
replay coverage per event type, temporal distribution, PlayerStats
periodicity, UnitBorn unit-type diversity, and event_data JSON schemas.
All SQL stored verbatim (I6). No cleaning decisions, no tables created (I9).

### Key findings

**Tracker events (62M rows):**
- 10 event types. UnitBorn dominates (36.08%), followed by UnitDied
  (25.89%) and UnitTypeChange (17.74%). PlayerStats is 7.35%.
- Per-replay density: mean 2,769, median 1,920 (right-skewed). Range
  140--66,984.
- UnitBorn, PlayerStats, and PlayerSetup appear in 100% of replays.
  UnitOwnerChange in only 25.39% (Neural Parasites, mind control).
- PlayerStats periodicity: gap=0 is the mode (50.58%) because both
  players emit PlayerStats at the same loop. True period is 160 loops
  (2,197,401 occurrences, ~98% of non-zero gaps). This is the standard
  SC2 tracker interval (~10 real-time seconds at Faster speed).
- UnitBorn: 232 distinct unit types. Top: Larva (3.9M), InvisibleTargetDummy
  (2.8M), Zergling (2.5M), Drone (1.4M), Probe (1.1M), Marine (1.0M).
  InvisibleTargetDummy is a hidden game-engine entity, not a player unit.

**Game events (608M rows):**
- 23 event types. CameraUpdate dominates (63.67%, 387.5M rows).
  Non-CameraUpdate events total 221.1M.
- Key action types: ControlGroupUpdate (11.37%), CommandManagerState
  (7.22%), SelectionDelta (6.71%), Cmd (5.13%), CmdUpdateTargetPoint
  (4.25%).
- Per-replay density (CTE-based 10% filename sample, true counts):
  mean 27,191, median 21,910.
- Cmd event_data keys: abil, cmdFlags, data, evtTypeName, id, loop,
  otherUnit, sequence, unitGroup, userid. SelectionDelta: controlGroupId,
  delta, evtTypeName, id, loop, userid.

**Message events (52K rows):**
- 3 event types: Chat (98.55%), Ping (1.37%), ReconnectNotify (0.08%).
- Coverage: 22,260 of 22,390 replays (99.42%). 130 replays have no
  message events.

### Implications for Phase 02

All three event views remain classified IN_GAME_ONLY per I3. PlayerStats
at 160-loop periodicity provides a natural time-series for in-game
features (resource counts, army value, worker count). UnitBorn with 232
unit types enables unit composition features. CameraUpdate could enable
attention/multitasking metrics (if in-game comparison is pursued). The
Cmd event stream provides APM-like action density per time window.

### [CROSS] Cross-game note

SC2EGSet provides in-game event streams (tracker 62M, game 608M,
message 52K rows). Neither AoE2 dataset has equivalent in-game event
data. This asymmetry is the controlled experimental variable for
Invariant #8: "Do the same methods work equally well with and without
in-game data?"

---

## 2026-04-16 -- [Phase 01 / Step 01_03_03] Table Utility Assessment

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** profiling -- all 6 raw data objects utility verdict
**Artifacts produced:**
- `reports/artifacts/01_exploration/03_profiling/01_03_03_table_utility.json`
- `reports/artifacts/01_exploration/03_profiling/01_03_03_table_utility.md`

### What

Empirical assessment of all 6 raw data objects (replay_players_raw,
replays_meta_raw, map_aliases_raw, game_events_raw, tracker_events_raw,
message_events_raw). Verified the replay_id join key between the two core
tables. Enumerated all 31 struct leaf fields of replays_meta_raw.
Characterized loop=0 initialization events in game_events_raw and
tracker_events_raw. Cross-referenced metadata.mapName against
map_aliases_raw foreign/english name columns. All SQL stored verbatim (I6).
Verdicts derived from query results (I9).

### Key findings

**Join key (CONFIRMED):** `replay_id` derived via
`regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1)` gives
a perfect 22,390-to-22,390 match between replay_players_raw and
replays_meta_raw. Zero orphans in either direction. This is the canonical
join key per sql-data.md rule.

**Struct leaf fields (CONFIRMED 31):** replays_meta_raw contains exactly 31
struct leaf fields across 4 STRUCT columns (details: 3, header: 2,
initData.gameDescription: 22 including 15 gameOptions sub-fields, metadata:
4). The assertion `len == 31` passed.

**Map names already English (T02):** All 188 distinct `metadata.mapName`
values in replays_meta_raw appear in BOTH the `foreign_name` AND
`english_name` columns of map_aliases_raw. Zero map names are in neither
column. 14.4% of alias pairs have `foreign_name == english_name` (i.e., the
alias table maps some English names to themselves). Conclusion: map names in
replays_meta_raw are already in English; `map_aliases_raw` is not required
for translation of observed map names. It may still be retained as a
reference for completeness, but is `UTILITY_CONDITIONAL` for the pipeline.

**Event views -- all IN_GAME (T03/T04):**
- `game_events_raw`: 608,618,823 rows (schema YAML count). Loop=0 events are
  game initialization (PlayerSetup, NNet.Game.SCommandManagerStateEvent etc).
  Min loop = 0. No pre-game events (loop < 0).
- `tracker_events_raw`: 62,003,411 rows (live COUNT confirmed). Loop=0
  events include PlayerSetup and UnitBorn initialization events. Min loop = 0,
  max loop = 109,287. All 22,390 replays covered.
- `message_events_raw`: 52,167 rows (live COUNT confirmed). Covers 22,260 of
  22,390 replays (99.42% coverage). Chat/ping messages during game.
  All three event views classified IN_GAME per Invariant #3.

### Table utility verdicts (all data-derived)

| Table/View | Verdict | Reason |
|---|---|---|
| replay_players_raw | ESSENTIAL | Per-player features + prediction target |
| replays_meta_raw | ESSENTIAL | Timestamp, game version, map name, struct fields for temporal ordering |
| map_aliases_raw | UTILITY_CONDITIONAL | All 188 meta map names already in English; translation not required |
| game_events_raw | IN_GAME_ONLY | 608M rows, loop >= 0, excluded from Phase 02 pre-game pipeline per I3 |
| tracker_events_raw | IN_GAME_ONLY | 62M rows, loop >= 0, excluded from Phase 02 pre-game pipeline per I3 |
| message_events_raw | LOW_UTILITY | 52K rows, chat/ping, IN_GAME, 99.42% coverage but no pre-game signal |

### Implications for Phase 02

The `matches_flat` VIEW should join replay_players_raw and replays_meta_raw
using `replay_id` (regexp_extract) as the key. The join is guaranteed to be
complete (0 orphans). Event views (game/tracker/message) are excluded from
Phase 02 pre-game features per I3. map_aliases_raw may be skipped since
map names in replays_meta_raw are already in English.

### Cross-dataset summary (01_03_03 across all three datasets)

| Dataset | Table | Verdict | Key finding |
|---------|-------|---------|-------------|
| **aoe2companion** | matches_raw | ESSENTIAL | `rating` is PRE-GAME (99.8% match with ratings_raw), sole source for rm_1v1 ratings |
| | ratings_raw | CONDITIONALLY USABLE | No rm_1v1 coverage (leaderboard_id=6 absent). Useful for other leaderboards only |
| | leaderboards_raw | NOT USABLE | Singleton snapshot, 1 entry per player per leaderboard. I3 violation risk |
| | profiles_raw | NOT USABLE | No temporal dimension. Adds steamId/clan (99.9% non-null) but not usable for temporal features |
| **aoestats** | matches_raw | ESSENTIAL | Temporal anchor (`started_timestamp`), match context (map, leaderboard, patch) |
| | players_raw | ESSENTIAL | Target (`winner`), `old_rating` (pre-game), `civ`. ELO perfectly derivable (Spearman rho=1.0 with avg_elo in 1v1) |
| | overviews_raw | SUPPLEMENTARY | Singleton lookup. Patch release dates are the only unique data |
| **sc2egset** | replay_players_raw | ESSENTIAL | Target (`result`), player features (MMR, race, selectedRace) |
| | replays_meta_raw | ESSENTIAL | Match metadata, 31 struct fields. Join via replay_id (regexp_extract) |
| | map_aliases_raw | CONDITIONAL | All 188 map names already English — translation not required |
| | event views (3) | IN_GAME_ONLY | Deferred to optional Phase 02 in-game comparison |

---

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

SC2 / sc2egset findings. Reverse chronological.

---

## 2026-04-16 -- [Phase 01 / Step 01_03_02] True 1v1 Match Identification

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** profiling -- replay-level 1v1 classification
**Artifacts produced:**
- `reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json`
- `reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.md`

### What

Classified all 22,390 sc2egset replays into one of four categories based on player row count and result decisiveness: `true_1v1_decisive`, `true_1v1_indecisive`, `non_1v1_too_few_players`, `non_1v1_too_many_players`. Multi-signal analysis: per-replay player row counts (DuckDB GROUP BY), cross-reference with max_players struct field, observer setting, selectedRace/result profiling of anomalous rows. All SQL stored verbatim (I6). Standard races derived dynamically from 01_02_04 census (I7). No rows dropped (I9).

### Key finding

The dataset is overwhelmingly 1v1: **22,366 / 22,390 replays (99.89%) are `true_1v1_decisive`** (exactly 2 player rows, 1 Win + 1 Loss). Only 24 replays are to be excluded:
- `non_1v1_too_many_players`: 8 replays (4-9 player rows; genuine team games)
- `non_1v1_too_few_players`: 3 replays (1 player row)
- `true_1v1_indecisive`: 13 replays (2 players, Undecided/Tie result -- no prediction target)
- `non_1v1_other`: 0 (classification is exhaustive)

Gate condition verified: 22,366 + 13 + 8 + 3 = 22,390.

### Secondary findings

- **Empty selectedRace (1,110 rows, 555 replays):** All belong to `true_1v1_decisive` replays (players_per_replay = 2 for all 1,110; result = 555 Win + 555 Loss; APM = 0 for all). Race resolved post-game (Zerg 569, Prot 276, Terr 265). This is a data quality issue in the `selectedRace` field, not an observer issue. APM = 0 sentinel warrants investigation in 01_04.
- **Observer setting:** 0 (no observers) for all 22,390 replays. Non-1v1 replays are genuine multi-player games, not observer-contaminated 1v1s.
- **max_players vs actual count:** 403 replays have max_players = 4 but only 2 actual player rows -- all `true_1v1_decisive`. The max_players field encodes lobby slot capacity, not active players. Not a reliable 1v1 filter.
- **BW race variants (3 rows):** All 3 (BWTe, BWPr, BWZe) belong to the single 6-player replay -- a team game in the 2024 ESL SC2 Masters Spring Finals corpus.

### Implications for data cleaning (01_04)

Exclude 24 replays from the analysis population:
- 3 `non_1v1_too_few_players` (filename list in artifact)
- 8 `non_1v1_too_many_players` (filename list in artifact)
- 13 `true_1v1_indecisive` (filename list in artifact)

The 22,366 `true_1v1_decisive` replays form the viable pool for the prediction pipeline. Investigate APM = 0 and empty-selectedRace sentinel in 01_04.

---

## 2026-04-16 — [Phase 01 / Step 01_03_01] Systematic Data Profiling

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** profiling (column-level + dataset-level)
**Artifacts produced:**
- `reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json`
- `reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md`
- `reports/artifacts/01_exploration/03_profiling/01_03_01_completeness_heatmap.png`
- `reports/artifacts/01_exploration/03_profiling/01_03_01_qq_plots.png`
- `reports/artifacts/01_exploration/03_profiling/01_03_01_ecdf_key_columns.png`

### What

Systematic column-level and dataset-level profiling of all three sc2egset raw tables (replay_players_raw 25 cols / 44,817 rows; replays_meta_raw 17 struct-flat fields / 22,390 rows; map_aliases_raw 4 cols / 104,160 rows). Formal detection of dead fields, constant columns, near-constant columns, IQR outliers (Tukey fence 1.5×IQR). QQ plots and ECDFs for key numeric columns. Cross-table linkage verified via replayId. All SQL stored verbatim (I6).

### Constant columns — exactly 5

`game_speed`, `game_speed_init`, `gameEventsErr`, `messageEventsErr`, `trackerEvtsErr` (all in replays_meta_raw). **Phase 02 action: drop all 5.**

### Near-constant columns — 21 detected programmatically

Includes MMR (IQR=0 for all rows, 83.65% zero-sentinel), color_r/g/b/a, selectedRace, highestLeague, region, realm, result, startDir, handicap, playerID, and others. MMR near-constant detection is technically correct but NOT a drop candidate — requires sentinel-aware handling.

### Sentinel columns

| Column | Sentinel | Count | % | Meaning |
|--------|----------|-------|---|---------|
| MMR | 0 | 37,489 | 83.65% | Unrated player |
| SQ | INT32_MIN | 2 | 0.0045% | Missing SQ |

MMR rated-only IQR (P25=4,203, P75=6,584, IQR=2,381) has 0 Tukey outliers among 7,328 rated players.

### Cross-table linkage

Perfect referential integrity: 22,390 matched replays in both tables, 0 orphans in either direction. 0 duplicate (filename, playerID) rows.

### Class balance

Win 49.94% / Loss 50.00% — no class imbalance. Undecided (24) and Tie (2) excluded from modelling.

---

## 2026-04-15 — [Phase 01 / Step 01_02_07] Multivariate EDA

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** multivariate — cluster-ordered Spearman heatmap + pre-game feature space visualization
**Artifacts produced:**
- `reports/artifacts/01_exploration/02_eda/plots/01_02_07_spearman_heatmap_all.png`
- `reports/artifacts/01_exploration/02_eda/plots/01_02_07_pregame_multivariate_faceted.png`
- `reports/artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.md`
- `reports/artifacts/01_exploration/02_eda/01_02_07_multivariate_analysis.json`

### What

Produced 2 thesis-grade PNG files comprising the full multivariate EDA for sc2egset.
Part A: two-panel cluster-ordered Spearman correlation heatmap across all 4 numeric
columns (MMR, APM, SQ, supplyCappedPercent), without result_binary (pure feature-feature
covariance view). Two panels: all rows (SQ sentinel excluded, N=44,789) and rated
players only (MMR>0, N=7,159). Hierarchical clustering (UPGMA linkage on 1-|rho|
distance) applied to reorder axes and reveal correlation blocks. Part B: MMR
distribution faceted by selectedRace x highestLeague (MMR>0, standard races only) —
the scientifically defensible alternative to degenerate PCA (p=1 numeric pre-game
feature). All sentinel thresholds from 01_02_04 census at runtime (I7). I3
classification on all heatmap axis labels.

### Plots produced

| Plot | Subject |
|------|---------|
| `01_02_07_spearman_heatmap_all.png` | Two-panel cluster-ordered Spearman heatmap; left=all rows, right=rated (MMR>0) |
| `01_02_07_pregame_multivariate_faceted.png` | MMR distribution by selectedRace x highestLeague (PCA alternative) |

### Key findings

**Spearman heatmap — all rows (N=44,789, MMR includes zero sentinel):**
- APM-SQ form a strong correlation block: rho=0.405. This is the dominant structure
  in the all-rows matrix. Both are in-game metrics measuring player activity.
- MMR is effectively decorrelated from all other features in the all-rows panel:
  MMR vs APM=-0.013, MMR vs SQ=-0.009, MMR vs supplyCappedPercent=0.012. The zero
  sentinel contamination (83.65% of MMR rows are zero) suppresses any real correlation.
- supplyCappedPercent is near-zero correlated with APM (-0.002) but weakly
  anti-correlated with SQ (-0.125). Spending efficiently (high SQ) associates with
  spending less time supply-capped — a plausible in-game relationship.
- Cluster order (all rows): [MMR, supplyCappedPercent, APM, SQ] — MMR is isolated
  from the in-game cluster (APM+SQ).

**Spearman heatmap — rated players (N=7,159, MMR>0):**
- APM-SQ correlation drops from 0.405 to 0.345 in the rated subset — the in-game
  block persists but is less dominant.
- MMR now shows detectable positive correlations with in-game features: MMR vs APM=0.206,
  MMR vs SQ=0.159. Higher-ranked players are more active (APM) and more efficient (SQ)
  — consistent with the known skill-rating relationship.
- supplyCappedPercent vs SQ anti-correlation strengthens: -0.161 (vs -0.125 all-rows),
  consistent with the in-game skill relationship being cleaner in the rated subset.
- Cluster order (rated): [supplyCappedPercent, MMR, APM, SQ] — supplyCappedPercent
  migrates to join MMR away from the APM-SQ block when rated players dominate.
- Key shift: The MMR zero-sentinel contamination in the all-rows panel completely
  suppresses the real MMR-to-in-game correlations. This confirms that zero-sentinel
  rows should be excluded from any MMR-related analysis.

**Pre-game multivariate faceted view (PCA alternative):**
- Standard PCA skipped: sc2egset has exactly 1 numeric pre-game feature (MMR).
  With p=1, PCA produces trivial PC1=100% — uninformative (Jolliffe 2002, §2.2).
- MMR distributions vary meaningfully across league tiers: Grandmaster players
  cluster at the high end (~6,000-7,000 MMR), while Unknown/unranked players
  span the full range. This confirms league tier is correlated with MMR.
- Within a given league tier, race (Prot/Terr/Zerg) shows minimal effect on MMR
  distribution — distributions largely overlap. Race and MMR are approximately
  independent conditioning on league.
- Several race x league combinations have very sparse data (N<5) — notably
  Grandmaster in lower-tier leagues, reflecting the small absolute count of
  Grandmaster-tier players in the dataset.

### PCA decision (documented)

Standard PCA was skipped because the pre-game numeric feature space contains
exactly 1 column (MMR). Including in-game features (APM, SQ, supplyCappedPercent)
in PCA with I3 annotation was rejected: dominant PCs would be driven by the APM-SQ
in-game correlation (rho~0.40), making results uninterpretable for Phase 02 pre-game
feature engineering. The faceted distribution directly answers the multivariate
question for the pre-game space.

### Phase 02 implications

- Pre-game feature space is extremely sparse: 1 numeric (MMR, 83.65% zero-sentinel
  contaminated), 2 categorical (selectedRace, highestLeague). Feature engineering
  in Phase 02 must either (a) handle the zero-sentinel imputation explicitly, or
  (b) restrict pre-game modeling to the ~16% rated-player subset.
- The MMR-to-in-game correlations (MMR vs APM=0.206, MMR vs SQ=0.159 in rated subset)
  suggest MMR has predictive signal. The practical question for Phase 02 is how to
  handle the 83.65% unrated rows without discarding them.
- Race x league joint structure shows reasonable density for most combinations except
  sparse Grandmaster cells. Interaction terms (race x league) are likely sparse and
  may need regularization or collapsing.

### Decisions taken

- All sentinel thresholds derived from census JSON at runtime (I7). No hardcoded numbers.
- UPGMA linkage on (1-|rho|) distance used for cluster ordering — standard choice
  for correlation matrices (Sokal & Michener 1958).
- MIN_LEAGUE_ROWS=50 derived from Cleveland (1993) 2 obs/bin recommendation with
  30 histogram bins.

### Decisions deferred

- MMR zero-sentinel treatment (impute/exclude/flag) deferred to Phase 01_04 Data Cleaning.
- Race x league interaction encoding strategy deferred to Phase 02 Feature Engineering.
- Whether the MMR-APM/SQ correlation in rated players is stable across league tiers
  deferred to targeted follow-up analysis.

### Open questions

- Does the cluster ordering of [supplyCappedPercent, MMR, APM, SQ] in the rated
  panel have a game-theoretic interpretation? (Why does supply-cap efficiency
  cluster closer to MMR than to APM in the rated subset?)
- Is the sparse Grandmaster x race cell count a data quality issue or a genuine
  reflection of population sparsity? Relevant for Phase 02 imputation decisions.

### Thesis mapping

- Chapter 4, §4.1.1 — multivariate EDA, PCA alternative decision, pre-game sparsity
- Chapter 5 (Results) — feature correlation structure, pre-game vs in-game distinction

### Invariants applied

- **I3:** All Spearman heatmap axis labels carry "[IN-GAME (Inv. #3)]" or "[PRE-GAME]"
  classification. Pre-game faceted plot uses only pre-game features.
- **I6:** All 3 SQL queries stored in `sql_queries` dict and written verbatim to
  `01_02_07_multivariate_analysis.md`.
- **I7:** All thresholds (MMR_zero_count=37,489, SQ_sentinel=2, Undecided=24, Tie=2)
  derived from census JSON at runtime.
- **I9:** Multivariate visualization of existing columns only; no new feature
  computation.

---

## 2026-04-15 — [Phase 01 / Step 01_02_06] Bivariate EDA

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** bivariate — pairwise relationships between features and match result
**Artifacts produced:**
- `reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.json`
- `reports/artifacts/01_exploration/02_eda/01_02_06_bivariate_eda.md`
- `reports/artifacts/01_exploration/02_eda/plots/01_02_06_*.png` (9 files)

### What

Produced 9 thesis-grade PNG plots examining pairwise relationships between features
and match result (Win vs Loss) in replay_players_raw (44,791 Win/Loss rows; 24
Undecided and 2 Tie rows excluded per census). Ran Mann-Whitney U tests for all
continuous features, chi-square tests for categorical features, and a two-panel
Spearman correlation heatmap (all rows and MMR>0 rated players only). All sentinel
thresholds derived from 01_02_04 census at runtime (Invariant #7). All three in-game
columns carry mandatory red-bbox annotation (Invariant #3).

### Plots produced

| Plot | Subject |
|------|---------|
| `01_02_06_mmr_by_result` | MMR violin (non-zero only, N=7,319 Win/Loss); Mann-Whitney U test annotated |
| `01_02_06_race_winrate` | Win rate per race (Prot/Zerg/Terr); chi-square test annotated |
| `01_02_06_apm_by_result` | APM violin by result (IN-GAME); Mann-Whitney U annotated |
| `01_02_06_sq_by_result` | SQ violin by result (IN-GAME, INT32_MIN excluded); Mann-Whitney U annotated |
| `01_02_06_supplycapped_by_result` | supplyCappedPercent violin (IN-GAME); Mann-Whitney U annotated |
| `01_02_06_league_winrate` | Win rate per highestLeague tier; bar chart with n annotations |
| `01_02_06_clan_winrate` | Win rate by isInClan (2x2); chi-square annotated |
| `01_02_06_numeric_by_result` | Multi-panel violin: all numeric features by result (MMR non-zero, SQ sentinel excluded) |
| `01_02_06_spearman_correlation` | Two-panel Spearman heatmap — all rows (MMR includes zero sentinel) and rated players (MMR>0) |

### Key findings

- **MMR (pre-game feature):** Among rated players (MMR>0, ~16.35% of rows), winners
  have marginally higher MMR (median Win=6151, Loss=5945). Mann-Whitney U p=2.4e-11
  but rank-biserial r=-0.090 (small effect, Cohen 1988). Despite statistical
  significance due to large n, the practical effect size is small — matchmaking is
  doing its job pairing similarly-rated players.
- **Race (pre-game feature):** Chi-square = 39.84, p=2.2e-09, dof=2. Win rates by
  race show statistically significant differences, though win rates cluster near 50%
  for all three races. Race is a valid pre-game feature with detectable but modest
  predictive signal.
- **APM (IN-GAME only):** Median Win=356, Loss=344. p=2.0e-73, r=-0.099 (small
  effect). High APM correlates weakly with winning — interesting but unusable at
  prediction time (Invariant #3).
- **SQ (IN-GAME only):** Spending Quotient shows the strongest in-game signal.
  Median Win=127, Loss=120. p=2.8e-248, r=-0.184 (medium effect). SQ is the most
  discriminative in-game metric, consistent with its design as a skill-efficiency
  measure.
- **supplyCappedPercent (IN-GAME only):** No meaningful separation. Median Win=6,
  Loss=6. p=0.074 (not significant at conventional threshold), r=-0.010. Supply
  cap time is not discriminative between winners and losers in this dataset.
- **Clan membership (pre-game feature):** Chi-square = 7.75, p=0.0054 (marginal).
  The effect is very small but statistically significant. Clan membership may be a
  very weak proxy for engagement/commitment.
- **League tier (pre-game feature):** Visual inspection shows win rates close to 50%
  across all tiers. The massive "Unknown" and "(empty)" categories (many unranked
  players) dominate the distribution. Grandmaster-tier players show near-50% win
  rate — expected given match quality at the top.
- **Spearman correlation:** In the all-rows matrix, MMR is near-zero for all other
  features (zero-sentinel contamination). In the rated-players (MMR>0) matrix, MMR
  shows a detectable positive rho with result_binary (~0.09), consistent with the
  Mann-Whitney finding. SQ and APM are moderately correlated (~0.5 rho), as expected
  — both measure player activity/efficiency.

### Decisions taken

- All sentinel exclusions (MMR=0, SQ INT32_MIN) derived from census JSON at runtime
  — no hardcoded constants (Invariant #7).
- Two Spearman matrices computed to explicitly expose MMR zero-sentinel contamination
  rather than silently hiding it with a single filtered matrix.
- All statistical tests declared as EXPLORATORY (Tukey-style). No multiple comparison
  correction applied — findings are hypothesis-generating for Phase 02, not
  confirmatory.

### Decisions deferred

- MMR zero-row treatment (include/exclude/impute) deferred to Phase 01_04 Data
  Cleaning. Bivariate analysis confirms that zero-sentinel contamination visibly
  distorts Spearman correlation.
- Race encoding strategy (one-hot vs ordinal) deferred to Phase 02 Feature Engineering.
- Whether supplyCappedPercent's lack of discriminative power is dataset-specific or
  game-wide deferred to AoE2 comparison (Invariant #8 — cross-game comparability).

### Thesis mapping

- Chapter 4, §4.1.1 — bivariate EDA results, pre-game vs in-game feature separation
- Chapter 5 (Results) — feature importance discussion, especially SQ vs pre-game MMR
- Appendix — Invariant #3 compliance evidence (in-game annotations on all 5 relevant plots)

### Open questions / follow-ups

- SQ is the most predictive feature but is IN-GAME — is there a pre-game proxy
  (e.g., historical SQ average for a player)? This is a Phase 02 feature
  engineering question.
- The Spearman heatmap shows APM and SQ are correlated (~0.5). If both are in-game
  and correlated, do we need both? Phase 02 will address feature redundancy.
- Race chi-square significant but small effect — does race interaction with
  opponent race (matchup) produce stronger signal? This is a Phase 02 question
  (matchup encoding).

---

## 2026-04-15 — [Phase 01 / Step 01_02_05] Univariate EDA Visualizations

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** visualization
**Artifacts produced:**
- `reports/artifacts/01_exploration/02_eda/01_02_05_visualizations.md`
- `reports/artifacts/01_exploration/02_eda/plots/01_02_05_*.png` (14 files)

### What

Produced 14 thesis-grade PNG plots visualizing the 01_02_04 census findings for
replay_players_raw (44,817 rows) and replays_meta_raw (22,390 replays). sc2egset
is unique among the three datasets: zero NULLs, esports-focused (tournament replays
only), and contains in-game metrics not available in AoE2 datasets. All four in-game
columns carry identical mandatory annotation (Invariant #3). All thresholds
data-derived from census (Invariant #7).

### Plots produced

| Plot | Subject |
|------|---------|
| `result_bar` | Target balance — Win/Loss/Undecided/Tie; 24 Undecided and 2 Tie rows confirmed from census |
| `categorical_bars` | 3-panel: highestLeague, region, game_type frequency distributions |
| `selectedrace_bar` | Race pick rates including empty-string anomaly (8 rows) flagged in tomato red |
| `mmr_split` | MMR split view (all vs. non-zero); 83.65% sentinel zero confirmed; non-zero body is bell-shaped ~1,500–5,000 |
| `apm_hist` | APM histogram; right-skewed with professional-level tail; IN-GAME annotated |
| `sq_split` | SQ split view excluding 2 INT32_MIN sentinels; shows narrow distribution 60–90; IN-GAME annotated |
| `supplycapped_hist` | supplyCappedPercent histogram; bimodal structure; IN-GAME annotated |
| `duration_hist` | Dual-panel body (0–22.5 min, p95-derived from `census["duration_stats"]["p95"] / 22.4`) + full log; POST-GAME annotated |
| `mmr_zero_interpretation` | Cross-tab of MMR=0 vs result and vs highestLeague; shows zero-MMR is not outcome-correlated |
| `temporal_coverage` | Match count by year/month 2016–2024; shows tournament activity peaks |
| `isinclan_bar` | Clan membership — majority of tournament players in clans |
| `clantag_top20` | Top-20 clans by player count |
| `map_top20` | Top-20 of 188 maps by replay count; top-20 covers 44.7% of all replays |
| `player_repeat_frequency` | Games per toon_id distribution (log-y); 2,495 unique players over 44,817 rows; heavily right-skewed with a long tail of tournament regulars |

### Key findings

- **MMR sentinel:** 83.65% of rows have MMR=0 (unrated / not tracked in this dataset). The non-zero MMR body is approximately bell-shaped around 2,000–3,000, consistent with professional ladder MMR ranges. Zero-MMR rows are not outcome-correlated (confirmed via cross-tab).
- **In-game columns:** APM, SQ, and supplyCappedPercent are all in-game metrics unavailable at prediction time. All annotated with mandatory red-bbox warning (Invariant #3). supplyCappedPercent shows bimodal structure suggesting two player behavioral modes.
- **Player concentration:** `player_repeat_frequency` shows a highly right-skewed distribution — many players appear 1–5 times, but a core of ~50–100 tournament regulars appear 100–500+ times. This means a replay-based train/val split leaks player-level information, confirming that Phase 03 must use player-stratified splitting.
- **Map concentration:** Top-20 maps (of 188 total) account for only 44.7% of replays — map space is far less concentrated than in AoE2 (where top-3 maps = 49%). Phase 02 map encoding strategy must handle 188 categories.
- **Duration (game loops):** LOOPS_PER_SECOND = 22.4 (SC2 Faster speed). p95 = 30,270.1 loops = 22.5 min body clip. Full range shows extreme outlier replays (likely paused/abandoned games).
- **Race balance:** All three races (Terran/Protoss/Zerg) relatively balanced in the tournament pool; selectedRace empty-string anomaly (8 rows) is negligible.

### Decisions taken

- Duration clip: `CLIP_SECONDS = census["duration_stats"]["p95"] / 22.4` — fully data-derived, no hardcoded threshold.
- SQ INT32_MIN sentinel (2 rows): excluded from main histogram — too few to affect distribution, retained in dataset until Phase 01_04 cleaning decision.
- `player_repeat_frequency` y-axis: log-scale mandatory — without it, the single-game majority hides all structure in the tail.

### Decisions deferred

- Player-stratified vs replay-stratified split decision deferred to Phase 03. The `player_repeat_frequency` plot provides the visual evidence for the Phase 03 planning session.
- MMR zero-row treatment (include/exclude/impute) deferred to Phase 01_04 Data Cleaning.
- Map encoding strategy (top-k grouping vs embedding) deferred to Phase 02 Feature Engineering.

### Thesis mapping

- Chapter 4, §4.1.1 — SC2EGSet dataset description, target balance, feature overview
- Chapter 4, §4.1.2 — in-game column annotations, MMR sentinel analysis
- Chapter 5 (methodology) — player-repeat evidence motivating Phase 03 splitting strategy

### Open questions / follow-ups

- Does player-stratified splitting materially change model performance vs replay-stratified? Evidence gathered here; answer deferred to Phase 03.
- Are the 24 Undecided results from specific tournaments or distributed across the dataset? Visual inspection of temporal coverage may reveal clustering.

---

## 2026-04-15 — [Phase 01 / Step 01_02_04] Univariate Census & Target Variable EDA

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** query
**Artifacts produced:**
- `reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md`
- `reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json`

### What

Extracted 17 fields from the STRUCT columns in `replays_meta_raw` (details, header, initData, metadata) into a flat `struct_flat` working table, then ran a full univariate census across all six sc2egset data objects: NULL rates, cardinality, numeric descriptive statistics, sentinel detection, value distributions, temporal range, duplicate detection, and field-level pre-game/in-game/identifier/target/constant classification per Invariant #3. All SQL embedded in .md artifact (Invariant #6).

### Tables profiled

| Object | Type | Rows | Columns |
|--------|------|------|---------|
| `replay_players_raw` | table | 44,817 | 25 |
| `struct_flat` (from replays_meta_raw) | derived | 22,390 | 18 |
| `map_aliases_raw` | table | 104,160 | 4 |
| `game_events_raw` | view | 608,618,823 | 4 |
| `tracker_events_raw` | view | 62,003,411 | 4 |
| `message_events_raw` | view | 52,167 | 4 |

### NULL landscape

Remarkably clean: **0% NULLs across all columns in every table and view.** This includes replay_players_raw (all 25 cols), struct_flat (all 18 extracted fields), map_aliases_raw, and all three event views. Zero-NULL data requires sentinel detection rather than NULL-based imputation strategies.

### Target variable (`result`)

- 4 distinct values: **Loss 50.00%** (22,409 rows), **Win 49.94%** (22,382 rows), Undecided 0.05% (24 rows), Tie 0.00% (2 rows)
- Near-perfect 50/50 balance is structural: each game produces one Win and one Loss row. No class imbalance mitigation needed.
- All 26 Undecided/Tie rows come from standard 2-player replays — these 13 replays lack a definitive outcome and must be excluded in cleaning (01_04).
- Zero duplicate rows on the `filename || '|' || toon_id` composite key.

### MMR analysis

- **83.65% of rows have MMR=0** (37,489 / 44,817). MMR=0 rate is uniform across Win (84.34%) and Loss (82.99%) — confirming zero is "not reported" not outcome-correlated.
- MMR=0 by league: Unknown 93.13%, Unranked 100%, even Master 57.96% and Grandmaster 60.27% majority zero. Consistent with SC2EGSet being tournament replays where MMR is often not exposed.
- Among the **7,328 non-zero rows (16.35%):** range -36,400 to 7,464. The negative minimum may represent another sentinel convention.
- MMR is a **pre-game feature** (ladder-rating snapshot at game time) — no leakage risk. The zero-MMR issue is a data-availability problem, not temporal leakage.
- Feature engineering options: (a) use MMR only for the 16% valid subset, (b) impute from historical player averages, (c) add binary missing-MMR indicator. Strategy deferred to Phase 02.

### SQ (Spending Quotient)

- 2 rows contain the INT32_MIN sentinel (-2,147,483,648), destroying raw statistics (raw mean: -95,711). Sentinel-excluded (N=44,815): **median 123, mean 122.38, std 18.91, range [-51, 187], IQR [110, 136].**
- SQ measures macro-economic efficiency (resource spending relative to income) computed from in-game actions — **post-game metric**, classified as `in_game`. Cannot be used as a pre-game feature.

### APM (Actions Per Minute)

- No sentinel issues. 1,132 rows (2.53%) with APM=0 (very short games or parse artifacts). **Median 349, mean 355.57, std 104.87, range [0, 1,248].**
- Post-game metric computed from full replay — classified as `in_game`.

### supplyCappedPercent

- **Median 6%, mean 7.24%, range [0, 100]**, 298 rows (0.67%) at zero. Right-skewed (skewness 2.25). Post-game metric — classified as `in_game`.

### game_events_raw scale

- 608.6M rows across 22,390 replays. **23 distinct evtTypeNames.** CameraUpdate alone: 387.5M rows (63.67%).
- `event_data` column has 528.5M distinct values (extreme cardinality); excluded from top_n/bottom_n profiling to avoid OOM.
- Histograms deferred for event tables per EDA Manual (608M rows, semantically heterogeneous — univariate histograms on `loop` are not analytically meaningful without event-type stratification).

### Temporal leakage classification (Invariant #3)

**Pre-game** (replay_players_raw): MMR, race, selectedRace, handicap, region, realm, highestLeague, isInClan, clanTag, startDir, startLocX, startLocY, color channels — all available before match start.

**In-game** (replay_players_raw): APM, SQ, supplyCappedPercent — computed from replay actions, post-game only.

**Pre-game** (struct_flat): time_utc, game_version_header/meta, base_build, data_build, map_name, max_players, map_size_x/y, is_blizzard_map.

**Post-game** (struct_flat): elapsed_game_loops — total match duration; only known after match ends (same semantic class as AoE2 duration_sec / duration_min).

**Constant / dead** (no predictive information): game_speed, game_speed_init (always "Faster"); gameEventsErr, messageEventsErr, trackerEvtsErr (always FALSE).

### Categorical highlights

- `race`: Protoss 36.21%, Zerg 35.02%, Terran 28.76%. 3 BW-prefixed anomalous entries.
- `selectedRace`: 1,110 rows (2.48%) with empty string (Random resolved post-game); 10 explicit "Rand" rows.
- `highestLeague`: 72.16% "Unknown" — esports replays rarely expose ladder rank.
- `region`: Europe 46.91%, US 28.34%, Unknown 12.83%, Korea 8.04%.
- `isInClan`: 25.9% True; 257 distinct clan tags.
- `handicap`: effectively constant at 100 (only 2 rows at 0) — dead column.

### map_aliases_raw

104,160 rows = 70 tournaments × 1,488 foreign names each. Maps foreign/localized tournament map names to English equivalents. Join key is `map_name` from struct_flat matched against `english_name` or `foreign_name` — **not via `filename`.** All tournaments have identical key sets.

### Decisions taken

- Field classification taxonomy established for all 25 replay_players_raw columns and 18 struct_flat columns; stored in JSON artifact under `field_classification`
- MMR=0 treated as "not reported" sentinel based on uniform distribution across result categories and league correlation
- SQ INT32_MIN sentinel identified (2 rows); sentinel-excluded statistics documented
- Event tables profiled for null/cardinality only; histogram profiling deferred

### Decisions deferred

- MMR imputation or filtering strategy — requires player identity resolution (Phase 02)
- Whether isInClan/clanTag carry win-rate signal — Phase 02 correlation analysis
- Cleaning of 13 Undecided/Tie replays, 11 non-2-player replays, 3 BW-prefixed race entries, 2 SQ sentinel rows — deferred to 01_04
- Whether to include in-game fields (APM, SQ, supplyCappedPercent) for an in-game prediction comparison framing — Phase 02 decision

### Thesis mapping

- Chapter 4, section 4.1.1 — SC2EGSet: data quality profile, target distribution, MMR availability, sentinel conventions
- Chapter 4, section 4.2.1 — Pre-game vs in-game field classification methodology

### Open questions / follow-ups

- Optimal MMR handling for 84% missing rows: imputation vs. indicator vs. subsetting (Phase 02)
- Do isInClan and clanTag carry win-rate signal beyond player identity? **Partially resolved in 01_02_06:** isInClan chi-square = 7.75, p=0.0054, small effect -- clan membership is a very weak proxy for engagement. Full clanTag signal analysis (257 distinct tags) deferred to Phase 02.
- The 3 BW-prefixed race entries — merge with SC2 counterparts or exclude? (01_04)
- 273 replays with map_size_x=0 and map_size_y=0 — parse artifact or real map configuration? (01_04)

---

## 2026-04-14 — [Phase 01 / Step 01_02_03] Raw schema DESCRIBE

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** query
**Artifacts produced:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_03_raw_schema_describe.json`
- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replays_meta_raw.yaml`
- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replay_players_raw.yaml`
- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/map_aliases_raw.yaml`
- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/game_events_raw.yaml`
- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/tracker_events_raw.yaml`
- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/message_events_raw.yaml`

### What

Captured the exact DuckDB column names and types for all six sc2egset `*_raw` objects — three persistent tables and three event views — by connecting read-only to the persistent DuckDB populated in 01_02_02 and running `DESCRIBE` on each object.

### Why

Establish the source-of-truth bronze-layer schema for downstream steps. The `data/db/schemas/raw/*.yaml` files are consumed by feature engineering and documentation. Invariant #6 — DESCRIBE SQL embedded in artifact.

### How (reproducibility)

Notebook: `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_03_raw_schema_describe.py`

Read-only connection to `data/db/db.duckdb`. `DESCRIBE <object>` for all six `*_raw` tables and views.

### Findings

| Object | Type | Columns | Notable types |
|--------|------|---------|---------------|
| replays_meta_raw | table | 9 | STRUCT columns for details/header/initData/metadata; `ToonPlayerDescMap` VARCHAR; error flags BOOLEAN |
| replay_players_raw | table | 25 | `result` VARCHAR (prediction target); `MMR`/`APM`/`SQ`/`supplyCappedPercent` INTEGER; `highestLeague` VARCHAR; color channels INTEGER |
| map_aliases_raw | table | 4 | `tournament`/`foreign_name`/`english_name`/`filename` all VARCHAR, all NOT NULL |
| game_events_raw | view | 4 | `filename` VARCHAR, `loop` BIGINT, `evtTypeName` VARCHAR, `event_data` VARCHAR |
| tracker_events_raw | view | 4 | Identical 4-column schema to game_events_raw |
| message_events_raw | view | 4 | Identical 4-column schema to game_events_raw |

Key observations:
- `result` (VARCHAR, nullable) in `replay_players_raw` is the prediction target — stores string values, not a boolean; distinct values to be confirmed in 01_03
- `replay_players_raw` has 25 columns total — the full set including SQ, supplyCappedPercent, highestLeague, color channels; only 7 columns were NULL-checked in 01_02_02
- `ToonPlayerDescMap` confirmed VARCHAR (JSON text blob) in `replays_meta_raw`, as decided in 01_02_01
- All three event views share the identical 4-column generic schema; event type discriminated via `evtTypeName`
- `replay_players_raw.filename` and `map_aliases_raw` key columns all NOT NULL (confirmed by nullable=NO)
- All six schema YAMLs populated in `data/db/schemas/raw/`

### Decisions taken

- Schema YAMLs populated from this DESCRIBE output — source-of-truth for all downstream steps
- No schema modifications — read-only step

### Decisions deferred

- Full NULL profile for all 25 `replay_players_raw` columns
- Distinct values for `result` column
- Column descriptions (`TODO: fill`) in `*.yaml` — deferred to 01_03

### Thesis mapping

- Chapter 4, §4.1.1 — SC2EGSet: bronze-layer schema catalog

### Open questions / follow-ups

- What are the actual distinct values of `result`? Are 'Win'/'Loss' the only values, or are there draws/unknowns? (Investigate in 01_03)

---

## 2026-04-14 — [Phase 01 / Step 01_02_02] DuckDB ingestion

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** ingest
**Artifacts produced:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.json`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_02_duckdb_ingestion.md`

### What

Materialised three `*_raw` DuckDB tables and three event DuckDB views from the
full 22,390-file sc2egset corpus (209 GB raw JSON) into the persistent database
at `src/rts_predict/games/sc2/datasets/sc2egset/data/db/db.duckdb`. Event data
extracted to zstd-compressed Parquet under `IN_GAME_PARQUET_DIR` and registered
as DuckDB views for SQL access.

### Why

Enable SQL-based EDA for subsequent profiling (01_03) and cleaning (01_04).
All data — metadata, player stats, and in-game events — now accessible via
DuckDB queries without reading raw JSON files on every access. Invariants #6
(reproducibility), #7 (provenance), #9 (step scope), #10 (relative filenames)
upheld.

### How (reproducibility)

Notebook: `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.py`
Module: `src/rts_predict/games/sc2/datasets/sc2egset/ingestion.py`

### Findings

**Table row counts:**
| Table | Rows |
|-------|------|
| replays_meta_raw | 22,390 |
| replay_players_raw | 44,817 |
| map_aliases_raw | 104,160 |

**Event view row counts:**
| View | Rows |
|------|------|
| game_events_raw | 608,618,823 |
| tracker_events_raw | 62,003,411 |
| message_events_raw | 52,167 |

**NULL rates (tables):**
- replays_meta_raw: zero NULLs across all 6 checked columns (details, header,
  initData, metadata, ToonPlayerDescMap, filename)
- replay_players_raw: zero NULLs across all 7 checked columns (toon_id,
  nickname, MMR, race, result, APM, filename)
- map_aliases_raw: zero NULLs across all 4 columns; 70 distinct tournaments

**NULL rates (event views):**
- All three event views: zero NULLs across all 4 columns (filename, loop,
  evtTypeName, event_data)

**ToonPlayerDescMap type:** Confirmed VARCHAR (JSON text blob), not STRUCT.

**Cross-table integrity:** `orphan_player_files = 0` in both directions
(every replay_players_raw file exists in replays_meta_raw, and vice versa).
Event views also have zero orphan files — all 22,390 replay filenames
present in game_events_raw and tracker_events_raw; message_events_raw covers
22,260 files (130 replays have no message events, which is expected).

**Player count per replay:** 22,379 replays have exactly 2 players (99.95%),
3 replays have 1 player, 2 have 4, 1 has 6, 3 have 8, and 2 have 9.
11 total non-2-player replays — likely team games, FFA, or incomplete
replays; flagged for investigation in 01_04 (cleaning).

**map_aliases_raw dedup profile:** 1,488 unique foreign names, 215 unique
English names, 70 unique tournaments, 104,160 total rows. As expected from
01_02_01 — all 70 tournament mapping files have identical 1,488-entry key
sets.

**Top event types (game_events_raw):** CameraUpdate dominates at 387M events
(63.7%), followed by ControlGroupUpdate (69M), CommandManagerState (44M),
SelectionDelta (41M), Cmd (31M). These are mechanical-skill signals.

**Top event types (tracker_events_raw):** UnitBorn (22.4M), UnitDied (16.1M),
UnitTypeChange (11.0M), PlayerStats (4.6M). These are game-state signals
likely most relevant for outcome prediction features in Phase 02.

**Top event types (message_events_raw):** Chat (51.4K), Ping (714),
ReconnectNotify (41). Low volume; limited predictive value expected.

**filename column (Invariant I10):** All three tables and all three event
views store paths relative to `raw_dir` (no leading `/`). Cross-table and
cross-view join on `filename` has zero orphans, confirming the relative-path
strategy is consistent across all six data objects.

### Decisions taken

- Tables use `*_raw` suffix convention (bronze layer naming)
- `replays_meta_raw` loaded per-tournament (70 batch INSERT operations) to
  avoid OOM: a single CTAS over 22,390 files peaked at 22 GB RSS and triggered
  OS kills on a 36 GB machine. Per-tournament batching keeps peak RSS under
  5 GB.
- `_MAP_ALIASES_INSERT_QUERY` (SQL with `json_each`) replaced by pure Python
  `json.loads` + `executemany` for correctness and simplicity
- `_DEFAULT_MAX_OBJECT_SIZE` set to 160 MB (1.12x headroom over largest
  observed file at 143.1 MB)
- Event extraction uses single-pass batched approach: each JSON file read
  once, events routed to gameEvents/trackerEvents/messageEvents accumulators
  in the same loop iteration (3x I/O reduction vs sequential extraction)
- Events stored as zstd-compressed Parquet (not DuckDB tables) to avoid
  doubling storage; registered as DuckDB views for SQL access
- Event schema: 4 columns (filename, loop, evtTypeName, event_data) with
  event_data as JSON VARCHAR — flexible for downstream parsing without
  committing to a schema prematurely
- 11 non-2-player replays (3 single, 2 quad, 1 hex, 3 oct, 2 nona) retained
  as-is; deferred to cleaning step

### Decisions deferred

- Data cleaning (NULL rates and anomalies documented, not acted on). Deferred
  to pipeline section 01_04.
- Identity resolution (toon_id stored as-is). Deferred to Phase 02.
- NULL rate coverage for replay_players_raw extended columns (SQ,
  supplyCappedPercent, highestLeague, etc.) — only 7 of 25 columns checked.
  Full profiling deferred to pipeline section 01_03.

### Thesis mapping

Chapter 4, Section 4.1.1 — SC2EGSet: three-stream ingestion design,
ToonPlayerDescMap normalisation, `*_raw` bronze-layer convention, event
Parquet extraction rationale.

### Open questions

- What are the 11 non-2-player replays? Are they team games, FFA,
  observers, disconnects, or parse failures? (Investigate in 01_04)
- 130 replays have no message events — is this expected (players who never
  chatted/pinged) or a parse artefact?
- Are SQ, supplyCappedPercent, highestLeague columns fully populated or do
  they have NULLs? (Profiling in 01_03)

---

## 2026-04-13 — [Phase 01 / Step 01_02_01] DuckDB pre-ingestion investigation

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** query
**Artifacts produced:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.json`

### What

Investigated how DuckDB's `read_json_auto` handles SC2EGSet replay JSON files.
Tested single-file and batch (union_by_name) ingestion, measured event array
storage costs, probed ToonPlayerDescMap behaviour, and assessed mapping file
structure.

### Why

Determine the ingestion strategy for 22,390 replay files before committing to
a table layout. Invariant #7 (type fidelity) and #9 (step scope) apply.

### How (reproducibility)

Notebook: `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_01_duckdb_pre_ingestion.py`

### Findings

- `read_json_auto` succeeds on all 7 sampled files (100% success rate), producing 11 root-level columns
- ToonPlayerDescMap is inferred as STRUCT with dynamic player-ID keys per file; with `union_by_name=true` it promotes to `MAP(VARCHAR, STRUCT(...))`
- Event arrays dominate file size: gameEvents ~327 GB, trackerEvents ~41 GB, messageEvents ~0.1 GB (total ~368 GB estimated across 22,390 files)
- Batch ingestion of 64 files from one tournament completed in 1.66 seconds within 24 GB memory limit
- Mean vs median storage estimates diverge significantly (right-skewed distribution) — median is the conservative estimate
- Mapping files (`map_foreign_to_english_mapping.json`): all 70 are flat `{str: str}` dicts with 1,488 entries each; cross-file consistency confirmed (all identical key sets)
- `read_json_auto` misinterprets mapping files as a single row with 1,488 columns — not suitable for direct DuckDB ingestion

### Decisions taken

- Three-stream split strategy: replay scalars (DuckDB), players normalised from ToonPlayerDescMap (DuckDB), events to zstd Parquet (not DuckDB)
- ToonPlayerDescMap stored as VARCHAR in `replays_meta` (text blob for provenance); normalised to per-player rows in `replay_players`
- Event Parquet extraction uses Python+PyArrow (not DuckDB) due to the heterogeneous STRUCT[] problem
- Every raw table includes `filename` column for provenance tracing

### Decisions deferred

- Whether mapping files need a DuckDB table at all — pending cross-tournament variation analysis and superset check (added to notebook section 7b)
- `profile_id` DOUBLE→BIGINT precision check deferred to aoestats investigation
- Filename uniqueness across tournaments — added as notebook section 1b, pending execution

### Thesis mapping

- Chapter 4, §4.1.1 — SC2EGSet dataset description, three-stream ingestion rationale
- Chapter 4, §4.2.1 — Ingestion and validation methodology

### Open questions / follow-ups

- Are replay filenames (MD5 hashes) unique across all 70 tournament directories? (section 1b)
- Do mapping files grow over time or are all 70 identical? (section 7b)
- What is the actual zstd compression ratio at scale? Smoke test showed 16.88x on one file.

---

## 2026-04-13 — [Phase 01 / Step 01_01_02] Schema discovery

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** content
**Artifacts produced:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.json`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition/01_01_02_schema_discovery.md`

### What

Examined internal structure of SC2EGSet JSON replay files and mapping files.
Catalogued root-level keys, enumerated full keypath tree, analysed event array
struct heterogeneity, and checked schema consistency across all 70 tournament
directories.

### Why

Understand the data shape before designing ingestion. Invariant #6
(reproducibility) requires knowing exact field names and types.

### How (reproducibility)

Notebook: `sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_02_schema_discovery.py`

### Findings

- 11 root-level keys per replay: ToonPlayerDescMap, details, gameEvents, gameEventsErr, header, initData, messageEvents, messageEventsErr, metadata, trackerEvents, trackerEvtsErr
- Schema consistent across all 70 directories (no era-dependent variation)
- 70 files checked for root schema, 210 for keypath enumeration
- Event arrays contain heterogeneous structs — gameEvents has 10+ distinct event types (CameraUpdate, SelectionDelta, Cmd, etc.), trackerEvents has 9+ (PlayerSetup, UnitBorn, PlayerStats, etc.)
- Nested sub-structures present within events (e.g., target positions, unit types)

### Decisions taken

- Systematic temporal stratification sampling: 1 file per directory for root schema, 3 per directory for keypaths
- Event array heterogeneity confirms that DuckDB's STRUCT[] union approach creates unusably wide schemas — separate extraction needed

### Decisions deferred

- Mapping file schema discovery added in this session (cell 5b) — pending notebook re-execution
- Ingestion strategy deferred to 01_02_01

### Thesis mapping

- Chapter 4, §4.1.1 — SC2EGSet schema description
- Appendix A — Full field catalog

### Open questions / follow-ups

- ToonPlayerDescMap field stability across eras (2016–2024)
- Exact sub-field types for metadata STRUCTs (details, header, initData, metadata)

---

## 2026-04-13 — [Phase 01 / Step 01_01_01] File inventory

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** filesystem
**Artifacts produced:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/01_acquisition/01_01_01_file_inventory.json`

### What

Catalogued the SC2EGSet raw data directory: directory structure, file counts,
sizes, and extensions across all 70 tournament directories.

### Why

Establish the data landscape before any content inspection. Invariant #9
requires sequential step discipline.

### How (reproducibility)

Notebook: `sandbox/sc2/sc2egset/01_exploration/01_acquisition/01_01_01_file_inventory.py`

### Findings

- Two-level layout: `raw/TOURNAMENT/TOURNAMENT_data/*.SC2Replay.json`
- 70 top-level tournament directories spanning 2016–2024
- 22,390 replay JSON files totalling 209 GB
- 431 metadata files (mapping files, summaries, processed mappings) at tournament root level
- All replay files have `.json` extension (no mixed formats)
- No directories missing `_data` subdirectory

### Decisions taken

- Layout confirmed as suitable for glob-based ingestion (`*/*_data/*.SC2Replay.json`)
- Tournament directory name serves as temporal/provenance key

### Decisions deferred

- Internal file structure deferred to 01_01_02

### Thesis mapping

- Chapter 4, §4.1.1 — SC2EGSet dataset description, data volume

### Open questions / follow-ups

- None — straightforward inventory step
