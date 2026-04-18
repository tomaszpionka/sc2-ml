# Step 01_04_04 -- Identity Resolution (sc2egset)

**Generated:** 2026-04-18
**Dataset:** sc2egset
**Step:** 01_04_04

## I0 Sanity Checks

| Table/View | Row count | Expected |
|---|---|---|
| matches_flat | 44,817 | 44,817 |
| matches_flat_clean | 44,418 | 44,418 |
| matches_long_raw | 44,817 | 44,817 |

## Single-key Census (K1..K5)

Source: `replay_players_raw` (44,817 rows)

| Key | Cardinality |
|---|---|
| K1: toon_id | 2,495 |
| K2: (region, realm, toon_id) | 2,495 |
| K3: LOWER(nickname) | 1,045 |
| K4: (LOWER(nickname), region) | 1,473 |
| K5: (LOWER(nickname), region, realm) | 1,487 |
| K_cs: nickname (case-sensitive) | 1,106 |

**I7 ratio baseline (case-sensitive, per 01_02_04):**
K1/K_cs = 2495/1106 = 2.2559 (expected 2.257 +/- 0.05) -- **PASS**

**Finding:** LOWER(nickname) merges 61 case variants (1106 -> 1045), shifting ratio to 2.3876 (outside 2.26 +/- 0.05 bounds using lowercased denominator). Gate uses case-sensitive baseline per 01_02_04 artifact.

## toon_id Cross-Region Audit

Cross-region toon_ids: **0** (expected 0)

All 2,495 toon_ids appear in exactly 1 (region, realm) tuple. Confirms Battle.net scoping model: toon_id is region-scoped.

## Nickname Cross-Region Audit

Nicknames appearing in >1 region: **246** / 1,045 total

| n_regions | n_nicknames |
|---|---|
| 1 | 799 |
| 2 | 141 |
| 3 | 53 |
| 4 | 27 |
| 5 | 25 |

Top 5 cross-region nicknames (by n_toon_ids):

| lower_nick | n_toon_ids | n_regions | regions |
|---|---|---|---|
| serral | 42 | 5 | China,Europe,Korea,US,Unknown |
| showtime | 39 | 5 | China,Europe,Korea,US,Unknown |
| scarlett | 36 | 5 | China,Europe,Korea,US,Unknown |
| special | 35 | 5 | China,Europe,Korea,US,Unknown |
| elazer | 35 | 5 | China,Europe,Korea,US,Unknown |

## Temporal Overlap Classification (Fellegi-Sunter A/B/C)

For each pair of toon_ids sharing LOWER(nickname), classify temporal windows.
1-day minimum threshold: tournament-day granularity convention.

| Class | Count | Pct |
|---|---|---|
| A_overlap (concurrent play) | 294 | 1.8% |
| B_disjoint (sequential) | 15,474 | 96.2% |
| C_degenerate (<2 games) | 317 | 2.0% |
| **Total pairs** | **16,085** | |

**Finding:** Majority of cross-region pairs are B_disjoint (sequential server use), consistent with tournament participation patterns. Class A overlap pairs are strong same-player candidates.

## Within-Region Handle Collision Audit

Within-region nickname collisions: **451** / 1,473 distinct (nick, region) pairs
Collision rate: **30.62%**
Threshold (Christen 2012 Ch. 5 -- acceptable false-merge rate): **5%**
Above threshold: **True** (>5% -- COMMON-HANDLE EVIDENCE)

Top within-region collisions (sample):

| lower_nick | region | n_toon_ids |
|---|---|---|
| showtime | Europe | 17 |
| reynor | Europe | 16 |
| clem | Europe | 16 |
| heromarine | Europe | 16 |
| serral | Europe | 15 |
| scarlett | US | 14 |
| elazer | Europe | 14 |
| lambo | Europe | 13 |
| special | US | 12 |
| kelazhur | US | 12 |

## userID Refutation

userID cardinality: **16** (range 0..15)
Interpretation: slot index per game session. **Cannot serve as player identity key.**

## Region/Realm Sanity

Unknown region: **12.83%** of replay_players_raw rows (~5,750 rows)
Unknown toon_ids are each scoped to exactly 1 (Unknown, Unknown) tuple -- treated as valid region by Battle.net metadata extractor.

## Robustness Cross-Check (matches_flat_clean)

Rows removed by cleaning: **399** (0.89%)
Delta tolerance: +/-1% (empirical basis: 399/44,817=0.89%)

| Key | matches_flat | matches_flat_clean | Delta |
|---|---|---|---|
| K1 | 2,495 | 2,470 | 1.00% |
| K2 | 2,495 | 2,470 | 1.00% |
| K3 | 1,045 | 1,022 | 2.20% |
| K4 | 1,473 | 1,446 | 1.83% |
| K5 | 1,487 | 1,460 | 1.82% |

## Decision Ledger (DS-SC2-IDENTITY-01..05)

### DS-SC2-IDENTITY-01
**Question:** Can toon_id alone serve as the canonical player identity key for sc2egset Phase 02 rating backtesting?
**Recommendation:** REJECT toon_id-alone as canonical key. Use as a component in composite key.
**Routed to:** Phase 02 -- canonical identity VIEW design

### DS-SC2-IDENTITY-02
**Question:** Can LOWER(nickname) alone serve as the canonical player identity key for sc2egset?
**Recommendation:** REJECT LOWER(nickname)-alone as canonical key. Within-region collision rate far exceeds acceptable threshold.
**Routed to:** Phase 02 -- blocking strategy design (must add temporal or region disambiguation)

### DS-SC2-IDENTITY-03
**Question:** Do temporal windows of cross-region nickname pairs support a server-switch (disjoint) or concurrent-play (overlap) interpretation?
**Recommendation:** Treat Class A (overlap) pairs as SAME physical player (merge). Class B (disjoint) as ambiguous -- defer to Phase 02 classifier. Class C insufficient evidence.
**Routed to:** Phase 02 -- entity resolution classifier design

### DS-SC2-IDENTITY-04
**Question:** Does the Unknown region cluster (~12.83%) require special handling in identity resolution?
**Recommendation:** Treat Unknown as a valid region value for identity key scoping. Do NOT merge Unknown-region toon_ids with same-named known-region toon_ids without temporal evidence.
**Routed to:** Phase 02 -- Unknown region handling in rating history grouping

### DS-SC2-IDENTITY-05
**Question:** What composite key strategy should Phase 02 adopt as the canonical player identity for sc2egset?
**Recommendation:** Phase 02 canonical identity: use toon_id as granular entity; apply LOWER(nickname)-based merging only for Class A temporal overlap pairs. Class B pairs: use separate Elo entities (conservative). Document as Phase 02 decision gate -- requires empirical Elo cold-start sensitivity analysis to validate merge strategy impact.
**Routed to:** Phase 02 -- canonical player_identity_canonical VIEW design + Elo cold-start sensitivity analysis

## Synthesis

**Primary finding:** Neither toon_id alone nor LOWER(nickname) alone satisfies Invariant I2 (canonical player identity) for sc2egset.

- `toon_id` over-splits: one physical player across N servers = N cold-start Elo entities.
- `LOWER(nickname)` over-merges: 30.6% within-region collision rate far exceeds Christen 2012 Ch. 5 5% threshold.

**Recommended Phase 02 strategy:** Use `toon_id` as the granular entity. Apply `LOWER(nickname)`-based merging only for Class A temporal overlap pairs (294 pairs = 1.8% of cross-nickname pairs). Class B disjoint pairs remain as separate Elo entities (conservative).

**Thesis §4.2.2 [REVIEW]:** This step provides the empirical basis for the identity resolution section. Phase 02 design will determine the final canonical key -- the [REVIEW] marker closure is deferred to Category F after Phase 02 completes.

## Plots

1. `plots/01_04_04_key_cardinality_bars.png` -- K1..K5 cardinality comparison
2. `plots/01_04_04_toon_region_heatmap.png` -- distinct toon_ids per (region, realm)
3. `plots/01_04_04_nickname_cross_region_stacked.png` -- nickname distribution by n_regions

## SQL Queries (I6)

All 8 SQL queries are embedded verbatim in `01_04_04_identity_resolution.json` under the `sql_queries` key.

## Literature

- Fellegi, I. P. & Sunter, A. B. (1969). A theory for record linkage. JASA 64(328).
- Christen, P. (2012). Data Matching: Concepts and Techniques for Record Linkage,   Entity Resolution, and Duplicate Detection. Springer. Ch. 5.
