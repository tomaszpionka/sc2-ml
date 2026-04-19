# Cross-Dataset Phase 01 Rollup — Decision Gates

**Spec:** `reports/specs/01_06_readiness_criteria.md` v1.0 (CROSS-01-06-v1)
**Produced at:** T08 of feat/phase01-decision-gates-01-06
**Date:** 2026-04-19
**Datasets:** sc2egset · aoestats · aoe2companion

---

## §1 — Three-Dataset Verdict Table

| Dataset | Verdict | Flip-predicate | Phase 02 go/no-go |
|---------|---------|----------------|-------------------|
| sc2egset | READY_WITH_DECLARED_RESIDUALS | N/A (residuals landed in thesis) | **GO** — full scope |
| aoestats | READY_CONDITIONAL | BACKLOG F1 (`canonical_slot`) AND W4 (INVARIANTS §5 I5 PARTIAL→HOLDS). If F1 lands without W4, verdict remains READY_CONDITIONAL. | **GO-NARROW** (aggregate / UNION-ALL-symmetric features; per-slot deferred until F1+W4) |
| aoe2companion | READY_WITH_DECLARED_RESIDUALS | N/A (residuals landed in thesis) | **GO** — full scope |

**Evidence artifacts:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_sc2egset.md`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoestats.md`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/modeling_readiness_aoe2companion.md`

---

## §2 — Dimension × Dataset Role Matrix

Each cell carries the underlying metric value plus the role label. D6 is a flag-only column;
it does NOT count toward role tally.

| Dimension | sc2egset | aoestats | aoe2companion | Comparability note |
|-----------|----------|----------|---------------|-------------------|
| **D1 Sample-scale** | SUPPLEMENTARY — 22,209 clean matches (matches_flat_clean) | SUPPLEMENTARY — 17,814,947 clean matches (matches_1v1_clean) | **PRIMARY** — 30,531,196 clean matches (matches_1v1_clean) | Yes — all counts derived from the same CONSORT pipeline with structural 1v1 filter applied uniformly |
| **D2 Skill-signal (ICC)** | **PRIMARY** — ICC ANOVA=0.046 [0.028, 0.064]. Passes F1 (0.046 ≥ 0.01) AND F2 (INVARIANTS §5 I8 = **PARTIAL**, passes per spec §3 D2 F2 which admits HOLDS/PARTIAL). Largest point-estimate ICC among F1+F2 passers | SUPPLEMENTARY — ICC ANOVA=0.0268 [0.0148, 0.0387]. Passes F1 (0.0268 ≥ 0.01) AND F2 (INVARIANTS §5 I8 = **PARTIAL**, passes per spec §3 D2 F2). Not largest among F1+F2 passers (sc2egset 0.046 > 0.0268). Note: I8 row text references "ICC FALSIFIED in 2022-Q3 reference" as the PARTIAL cause | SUPPLEMENTARY — ICC ANOVA=0.003013 [0.001724, 0.004202]. Fails F1 (0.003 < 0.01) AND F2 (INVARIANTS §5 I8 = **FALSIFIED**, fails per spec §3 D2 F2 which rejects FALSIFIED/DEVIATES) | Yes — all 3 used ANOVA ICC primary estimator (Wu/Crespi/Wong 2012); reference window spec §7; observed-scale; bootstrap CI. F2 filter reads INVARIANTS §5 I8 uniform token (not ICC JSON `verdict` field) per spec §3 D2 |
| **D3 Temporal coverage** | SUPPLEMENTARY — 5 of 10 quarters above density floor (≥300 matches/quarter); tournament-sparse (2 tournaments per quarter typical); span 2022-Q3 to 2024-Q4 | SUPPLEMENTARY — 9 full quarters (2022-Q3 through 2024-Q4, exc. ref window) above density floor; crawler expansion confound in early 2022-Q3; span from 2022-Q3 | **PRIMARY** — 24 quarters (2020-Q3 to 2026-Q2); all 8 overlap-window quarters well above density floor (>1.8M matches/quarter); longest span of 3 datasets | Yes — density floor 100 matches/month (≈300/quarter) applied uniformly; overlap window 2022-Q3 to 2024-Q4 used for cross-dataset comparisons |
| **D4a Identity rename-stability** | SUPPLEMENTARY — Branch (iii): region-scoped nickname; ~12% cross-region accepted | SUPPLEMENTARY — Branch (v): API-namespace structurally-forced; no rename-stability measurable within aoestats alone | **co-PRIMARY** — Branch (i): API-namespace profileId, rename-stable; 2.57% rename-rate (97.43% profiles stable); VERDICT A 0.9960 cross-dataset bridge | Yes — all 3 follow INVARIANTS §5 I2 extended procedure; Branch classification from 01_04_04 per dataset |
| **D4b Identity within-scope rigor** | **co-PRIMARY** — within-region: 30.6% same-name collisions documented in SQL (INVARIANTS §5 I7 HOLDS); ~12% cross-region accepted and documented | SUPPLEMENTARY — Branch (v) structurally-forced; within-scope collision/rename rates unevaluable; cross-dataset bridge VERDICT A 0.9960 | **co-PRIMARY** — global: 3.55% name-collision-rate; 2.57% rename-rate; both below 15% threshold; SQL-documented in 01_04_04 | Yes — rate thresholds 15% applied uniformly per spec §3 D4b definition; orthogonal to D4a (sc2egset wins on rigor; aoe2companion wins on stability) |
| **D5 Patch resolution** | SUPPLEMENTARY — no patch_id column; tournament version string available but not anchored to patch timeline | **PRIMARY** — `patch` column (BIGINT) in matches_1v1_clean AND player_history_all; sole dataset with patch_id binding; D5 PRIMARY | SUPPLEMENTARY — no patch_id column; version string available in separate non-joined table | No (aoestats is sole PRIMARY candidate; comparison not meaningful for this dimension) |
| **D6 Controlled-asymmetry flag** (NOT role-bearing) | FLAG — in-game events parseable (APM, SQ, supplyCappedPercent); D6 asymmetry flag noted for Phase 02 scope discussion only | N/A | N/A | No (flag only; not counted toward PRIMARY-role tally; documented for I8 transparency) |

**ICC artifact paths:**
- sc2egset: `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/icc.json`
- aoestats: `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_05_icc_results.json`
- aoe2companion: `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_05_icc.json`

---

## §3 — Role Assignment with Evidence Citations

### D1 PRIMARY: aoe2companion

**Metric:** 30,531,196 clean matches (CONSORT S3 row count).
**Ratio:** aoe2companion:aoestats = 30.5M:17.8M = 1.71×; aoe2companion:sc2egset = 30.5M:22k = ~1375×.
**Justification:** aoe2companion exceeds both other datasets in absolute count. At N=22k,
sc2egset is tournament-sparse and not scale-comparable.
**Evidence:** `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/06_decision_gates/data_quality_report_aoe2companion.md`
**Falsifier:** If a new dataset were ingested with > 30.5M clean 1v1 matches, D1 PRIMARY
would flip to that dataset. Within current 3-dataset scope, this falsifier is inactive.

### D2 PRIMARY: sc2egset

**Metric:** ICC ANOVA = 0.046 [0.028, 0.064]; INVARIANTS §5 I8 row = PARTIAL.
**F1 test (ICC point estimate ≥ 0.01):** 0.046 ≥ 0.01 — PASSES.
**F2 test (INVARIANTS §5 I8 verdict NOT FALSIFIED/DEVIATES per spec §3 D2):** I8 = PARTIAL
— PASSES (spec admits HOLDS and PARTIAL tokens).
**Contrast:**
- aoestats ICC=0.0268 passes F1 AND F2 (I8 = PARTIAL, ICC FALSIFIED in 2022-Q3 reference is
  the cause of PARTIAL but the §5 token remains PARTIAL, which passes F2). Ranked
  SUPPLEMENTARY because 0.0268 < sc2egset's 0.046, not because of F2 failure.
- aoe2companion ICC=0.003013 fails F1 AND F2 (I8 = FALSIFIED per §5 row added 2026-04-19).
sc2egset is the largest point-estimate ICC among F1+F2 passers.
**Evidence:**
- ICC value: `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/05_temporal_panel_eda/icc.json`
- F2 source: `src/rts_predict/games/sc2/datasets/sc2egset/reports/INVARIANTS.md` §5 I8 row (uniform token set `{HOLDS, PARTIAL, FALSIFIED, DEVIATES}`)
- Note on ICC JSON `verdict` fields (sc2egset INCONCLUSIVE, aoestats FALSIFIED,
  aoe2companion "falsified (below range)"): these are **evidence** that feed into the §5
  row authoring, but the F2 filter reads the §5 row directly per spec §3 D2, not the JSON.
**Falsifier:** If a SUPPLEMENTARY dataset's ICC rises above sc2egset's AND its INVARIANTS §5
I8 row transitions out of FALSIFIED/DEVIATES (to HOLDS or PARTIAL), D2 PRIMARY would flip.
For aoestats, requires BACKLOG F1 resolution + ICC re-evaluation in a denser quarter.
For aoe2companion, requires a new ICC derivation showing skill-signal emerges (unlikely
per 01_05_05 sensitivity analysis).

### D3 PRIMARY: aoe2companion

**Metric:** 24 quarters (2020-Q3 to 2026-Q2); all 8 overlap-window quarters > 1.8M matches.
**Density floor:** 100 matches/month = 300 matches/quarter applied uniformly.
**Contrast:** sc2egset 5/10 quarters above floor (tournament-sparse); aoestats 9 quarters
with crawler expansion confound in 2022-Q3.
**Evidence:** `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/05_temporal_panel_eda/01_05_01_quarterly_grain.json`
**Falsifier:** If density-filtered SQL shows another dataset exceeds aoe2companion's
quarter count with months above the density floor applied uniformly.

### D4a co-PRIMARY: aoe2companion

**Metric:** Branch (i) API-namespace; 2.57% rename-rate; 97.43% profiles stable; VERDICT A
0.9960 cross-dataset namespace bridge.
**Contrast:** sc2egset Branch (iii) region-scoped nickname (~12% cross-region); aoestats
Branch (v) structurally-forced (rename-stability unmeasurable within dataset).
**Evidence:** `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/04_cleaning/01_04_04_identity_resolution.json`
**Falsifier:** If aoestats transitions to Branch (i) via BACKLOG F1 schema amendment (W4),
D4a would become co-PRIMARY between aoe2companion and aoestats. Current state: aoe2companion
is sole D4a PRIMARY.

### D4b co-PRIMARY: sc2egset + aoe2companion

**Metric sc2egset:** within-region collision 30.6% (documented via SQL in 01_04_04); ~12%
cross-region accepted and documented. INVARIANTS §5 I7 HOLDS (within-region SQL confirmed).
**Metric aoe2companion:** global collision 3.55%; global rename 2.57%; both below 15% threshold.
**Orthogonality to D4a:** sc2egset wins on within-region rigor (documented SQL collision
quantification even at 30.6%); aoe2companion wins on rename-stability (2.57% < 15%).
**Evidence:** sc2egset `01_04_04_identity_resolution.json`; aoe2companion `01_04_04_identity_resolution.json`
**Falsifier:** If aoestats Branch (v) → Branch (i/ii/iii) via schema amendment, aoestats
could enter co-PRIMARY on D4b if rates are measured and fall below 15%.

### D5 PRIMARY: aoestats

**Metric:** `patch` column (BIGINT) present in matches_1v1_clean and player_history_all;
N=19 distinct patch values (per aoestats INVARIANTS.md lines 10, 75, 103); patch change
boundary artifacts documented in 01_05_03.
**Contrast:** sc2egset tournament version string available but not patch-anchored to
game-version timeline; aoe2companion no patch metadata in joined tables.
**Evidence:** `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/06_decision_gates/data_dictionary_aoestats.csv` (patch column row)
**Falsifier:** If sc2egset or aoe2companion gains a patch_id column bound to the AoE2/SC2
game-version timeline with equivalent granularity to aoestats, D5 would become co-PRIMARY.

### D6: Flag-only (not role-bearing)

sc2egset in-game event data (APM, SQ, supplyCappedPercent) creates a controlled-asymmetry
research design opportunity. This is documented for I8 transparency (INVARIANTS §5 I8 row)
but does NOT constitute a PRIMARY/SUPPLEMENTARY role assignment. Cross-dataset comparisons
using D6 features are prohibited (sc2egset-only).

---

## §4 — Cross-Dataset I8 Compliance: Permitted and Blocked Checks

### Permitted cross-checks

1. **[PERMITTED] D1+D3 pair: distribution of clean matches per quarter, sc2egset ↔ aoe2companion.**
   Both datasets have quarterly grain data with comparable CONSORT pipelines. Temporal CV
   design can use aoe2companion as the high-density primary timeline; sc2egset as
   tournament-sparse supplementary. Different density scales but same quarter labels in
   2022-Q3 to 2024-Q4 overlap window.

2. **[PERMITTED] D2 ICC comparison: sc2egset (I8=PARTIAL, ICC 0.046) vs aoestats (I8=PARTIAL, ICC 0.0268) vs aoe2companion (I8=FALSIFIED, ICC 0.003).**
   All three measured using ANOVA ICC primary estimator (Wu/Crespi/Wong 2012) with
   observed-scale on the same outcome variable (`won`), same reference window spec §7,
   same bootstrap CI method. The ~15× difference between sc2egset (0.046) and
   aoe2companion (0.003) is a legitimate scientific finding (tournament-selection vs
   ranked-ladder heterogeneity); citable in §4.4.5. F2 filter per spec §3 D2 reads
   INVARIANTS §5 I8 uniform tokens (HOLDS/PARTIAL/FALSIFIED/DEVIATES).

3. **[PERMITTED] D4a+D4b combined: namespace bridge verification aoe2companion ↔ aoestats.**
   VERDICT A (0.9960 agreement) measured in 01_04_04 cross-dataset identity bridge. Justifies
   that profile_id (aoestats) and profileId (aoe2companion) refer to the same player namespace
   despite Branch (v) vs Branch (i) classification difference. Safe to use for cross-dataset
   player-history aggregation in Phase 02.

4. **[PERMITTED] D5 patch-epoch analysis: aoestats-only, supplemented by cross-dataset timing.**
   Aoestats patch-epoch boundaries (01_05_03) can be correlated with aoe2companion temporal
   drift signals (01_05_02 PSI by quarter) to disambiguate whether drift is patch-driven or
   population-drift. This is a causal inference cross-check, not a feature cross-check.

5. **[PERMITTED] Faction/civilization win-rate comparison: aoestats ↔ aoe2companion, aggregate.**
   Both datasets have `faction` (aoe2companion) / `p0_civ`/`p1_civ` (aoestats) columns.
   Aggregate (UNION-ALL-symmetric) faction win-rates can be computed for both datasets in the
   2022-Q3 to 2024-Q4 overlap window. aoestats per-slot features are BLOCKED (see below),
   but aggregate faction features are permitted.

6. **[PERMITTED] Survivorship / player-retention comparison: sc2egset ↔ aoe2companion.**
   Both have survivorship analysis at 01_05_04 with monotonic-attrition test. sc2egset
   shows tournament-structured cohort retention; aoe2companion shows rho=0.067 (no monotonic
   attrition). Cross-dataset comparison is legitimate for §4.1.3 (population scope framing).

### Blocked cross-checks

7. **[BLOCKED] Per-slot win-rate features across all three datasets.**
   aoestats `team=0/1` slot assignment is skill-correlated (W3 ARTEFACT_EDGE: 80.3% team=1
   assigned to higher-ELO player). Per-slot cross-dataset comparison is BLOCKED until BACKLOG
   F1 (canonical_slot schema addition) AND W4 (INVARIANTS §5 I5 PARTIAL→HOLDS) both land.

8. **[BLOCKED] D6 in-game features in any cross-dataset model.**
   sc2egset APM/SQ/supplyCappedPercent features are sc2egset-exclusive (no equivalent in
   aoestats or aoe2companion). Cross-dataset models cannot include D6 features; any model
   using D6 must be sc2egset-only with an explicit asymmetry flag.

9. **[BLOCKED] ICC re-comparison for aoestats pending BACKLOG F1.**
   aoestats ICC=0.0268 was measured in the 2022-Q3 reference window (744 active players in
   the crawler-expansion period). The true ICC in a denser quarter is unknown until BACKLOG F1
   resolves canonical_slot. Cross-dataset ICC claims comparing aoestats to sc2egset or
   aoe2companion must note this FALSIFIED-in-reference-window caveat explicitly.

---

## §5 — Phase 02 Kickoff Readiness

Phase 02 (Feature Engineering & Modeling) planning may commence immediately for all three
datasets, subject to scope constraints below.

| Dataset | Phase 02 scope | Scope constraint | Feature categories permitted |
|---------|---------------|-----------------|------------------------------|
| sc2egset | Full | None | PRE_GAME skill (MMR proxy, win-rate, faction/race), map, region, historical activity, IN_GAME_HISTORICAL (APM, SQ, supplyCappedPercent — sc2egset-exclusive) |
| aoestats | GO-NARROW | F1+W4 required for full scope | Aggregate / UNION-ALL-symmetric: faction win-rate, average ELO from player_history_all, match counts, patch features. Per-slot (p0_civ, p1_civ, p0_old_rating, p1_old_rating) DEFERRED |
| aoe2companion | Full | None | PRE_GAME skill (rating, is_unrated_proxy, win-rate), faction (with unknown-category handling for map_id), historical activity, profileId-based player history |

**Phase 01 gate closure:** All three datasets have completed Pipeline Section 01_06
(Decision Gates). Phase 01 is officially COMPLETE for all three datasets. Phase 01 outputs
(CONSORT flows, risk registers, INVARIANTS §5 rows, data dictionaries) constitute the
authoritative pre-Phase-02 baseline for the thesis.

---

*All metric values in §2 are traceable to T05–T07 artifact paths cited in §3.*
*Cross-check list in §4 is exhaustive at the time of writing; new cross-checks require
amendment to this document per spec §4 amendment protocol.*
