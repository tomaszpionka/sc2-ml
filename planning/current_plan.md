---
category: A
branch: feat/01-04-02-sc2egset
date: 2026-04-17
planner_model: claude-opus-4-7[1m]
dataset: sc2egset
phase: "01"
pipeline_section: "01_04 — Data Cleaning"
invariants_touched: ["3", "5", "6", "7", "9"]
source_artifacts:
  - "src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md (01_04_01 step block: decisions_surfaced DS-SC2-01..10)"
  - "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv (100 rows, 17 cols — empirical evidence per DS)"
  - "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json (missingness_audit block, ledger framework)"
  - "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md"
  - "src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md (2026-04-17 entry — DS-SC2-01..10 summary; 2026-04-16 entry — original cleaning rules)"
  - "sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_01_data_cleaning.py (current VIEW DDL — matches_flat, matches_flat_clean, player_history_all)"
  - "src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_history_all.yaml (current schema YAML)"
  - "src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/matches_long_raw.yaml (canonical 10-col skeleton)"
  - "docs/ml_experiment_lifecycle/01_DATA_EXPLORATION_MANUAL.md §4 (Data Cleaning — registry, non-destructive, CONSORT, post-validation)"
  - ".claude/scientific-invariants.md (I3, I5, I6, I7, I9)"
  - ".claude/rules/sql-data.md (replay_id pattern, view design, schema source-of-truth)"
critique_required: true
research_log_ref: src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md#2026-04-17-phase01-step01_04_02-sc2egset
---

# Plan: sc2egset 01_04_02 — Data Cleaning Execution (act on DS-SC2-01..10)

## Scope

This plan covers **Phase 01 / Pipeline Section 01_04 / Step 01_04_02** for the **sc2egset** dataset: applying the cleaning decisions surfaced (but not executed) by the 01_04_01 missingness audit. Step 01_04_01 produced a 100-row missingness ledger and 10 open decisions (DS-SC2-01..10); 01_04_02 resolves each decision, modifies the analytical VIEW DDL non-destructively (Invariant I9 — raw tables untouched), measures cleaning impact via CONSORT-style row counts before/after, and re-validates that all post-cleaning invariants still hold. The output is a final-state `matches_flat_clean` and `player_history_all` whose columns are defensible for Phase 02 feature engineering, accompanied by a CONSORT artifact and updated schema YAMLs. **Sandbox notebook:** `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py`. **Artifacts target:** `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/`. Cross-game work (aoestats, aoe2companion) is **out of scope** — pattern-establisher PR per Option A; sibling datasets follow in independent planning rounds.

## Problem Statement

Step 01_04_01 (PR #140) explicitly produced **recommendations only** — the audit ledger flagged 10 cleaning decisions (DS-SC2-01..10) but, per Invariant I9 and the audit's own gate condition, performed no DDL changes, no column drops, and no sentinel conversions. The current VIEWs (`matches_flat_clean`, `player_history_all`) therefore still contain:

1. **High-rate sentinel columns** (MMR=0 at 83.95%, highestLeague='Unknown' at 72.04%, clanTag='' at 73.93% in `matches_flat_clean`) that the ledger flags `DROP_COLUMN` per Rule S4 but which the VIEW DDL still SELECTs as-is.
2. **True constants** (10 `go_*` columns in `matches_flat_clean` and 10 in `player_history_all` with `n_distinct=1` per ledger constants-detection) that the DDL SELECTs but which carry zero predictive information.
3. **Low-rate sentinels** (handicap=0 at 0.0045% in both VIEWs; APM=0 at 2.53% in `player_history_all`) that the ledger flags `CONVERT_SENTINEL_TO_NULL` per Rule S3 but for which `carries_semantic_content=True` makes the recommendation non-binding — the planner must adjudicate.
4. **Target-NULL rows** in `player_history_all.result` (26 Undecided/Tie rows, 0.058%) flagged `EXCLUDE_TARGET_NULL_ROWS` per Rule S2 — the player_history_all VIEW currently retains them with `result IN ('Undecided', 'Tie')` because the audit drew no conclusion about how downstream feature computation should treat NULL targets.
5. **Domain-judgement columns** (DS-SC2-07 `gd_mapAuthorName` — non-predictive metadata) that the ledger flagged with mechanism=N/A and `RETAIN_AS_IS` (zero missingness) but which the planner must decide on independent of the missingness lens.

The window for fixing these is **now**, before Phase 02 begins feature engineering. Once Phase 02 fits scalers, computes rolling aggregates, and trains baselines, every analytical artifact downstream encodes the column set frozen at the end of Phase 01. Per Manual 01 §4 the cleaning step must produce a **defensible final column set** with documented rationale per column — leaving DS-SC2-01..10 unresolved means Phase 02 inherits ambiguity. Per Manual 01 §4.2 (Non-destructive cleaning), per Manual 01 §4.3 (Measuring cleaning impact) and per Manual 01 §4.4 (Post-cleaning validation), the canonical 01_04_02 deliverables are: (a) updated VIEW DDL implementing the resolutions, (b) a CONSORT artifact with row counts before/after each rule, (c) re-run profiling assertions confirming invariants still hold, (d) updated schema YAMLs reflecting the new column set, and (e) a cleaning registry table updated with the new rules per Manual §4.1.

## Assumptions & unknowns

- **Assumption:** The 01_04_01 ledger CSV (100 rows × 17 cols, recovered above) is the authoritative empirical evidence base. Every per-DS resolution in this plan cites a specific ledger row (view, column, n_sentinel, pct_missing_total, n_distinct, mechanism, recommendation_justification). No new census passes are required; this step **acts on** the audit, it does not re-audit.
- **Assumption:** Sentinel-to-NULL conversions and column drops occur via VIEW DDL modification only; raw tables (`replay_players_raw`, `replays_meta_raw`) are not touched. This upholds Invariant I9 (research pipeline discipline) and Manual §4.2 (non-destructive cleaning).
- **Assumption:** `matches_flat` (the structural JOIN VIEW) is **not** modified in this step — it stays as-is so that any future re-audit or re-derivation can reach back to the structural pre-cleaning state. Only `matches_flat_clean` and `player_history_all` change. This matches the Manual §4.2 principle that cleaned VIEWs filter the original, leaving raw/structural intact.
- **Assumption:** `matches_long_raw` (canonical 10-col skeleton from 01_04_00) is **not** modified. It is a cross-dataset normalisation layer; sentinel handling on its `rating_pre_raw` column belongs to Phase 02 per its existing schema YAML provenance note ("Value 0 is an unrated sentinel — handling deferred to Phase 02").
- **Assumption:** The CONSORT impact must be reported in **REPLAY units** (not row units) consistent with the 01_04_01 CONSORT flow already in the artifact, because every cleaning rule in `matches_flat_clean` is replay-level (the 2-per-replay invariant must be preserved).
- **Assumption:** Schema YAML for `matches_flat_clean` does not currently exist (`ls data/db/schemas/views/` returns only `matches_long_raw.yaml` and `player_history_all.yaml`). 01_04_02 will create it, mirroring the structure of `player_history_all.yaml`.
- **Unknown — DS-SC2-01 (MMR drop vs retain):** ledger recommends `DROP_COLUMN` (rate 83.95%, Rule S4 / van Buuren 2018), but `carries_semantic_content=True` (MMR=0 unranked vs MMR=NULL truly missing); resolved here by planner judgement (see Section 1).
- **Unknown — DS-SC2-09 (handicap), DS-SC2-10 (APM):** ledger recommends `CONVERT_SENTINEL_TO_NULL` (Rule S3) but flags both as `carries_semantic_content=True` ⇒ recommendation explicitly non-binding; resolved here by planner judgement (see Section 1).
- **Unknown — DS-SC2-04 (player_history_all.result Undecided/Tie):** ledger recommends `EXCLUDE_TARGET_NULL_ROWS` (Rule S2). For `player_history_all` (a feature-history VIEW, not a target VIEW), this needs a Phase-02-aware decision: drop, mark as DRAW category, or retain with NULL outcome. Resolved here per planner judgement; final user veto in Open Questions.

## Literature context

- **Manual 01_DATA_EXPLORATION_MANUAL.md §4 (Data Cleaning):** authoritative methodology for this step. §4.1 mandates a five-field cleaning registry (Rule ID / Condition / Action / Justification / Impact). §4.2 mandates non-destructive cleaning (raw preserved, cleaned VIEWs filter). §4.3 mandates CONSORT-style flow (Liu et al., 2020 CONSORT-AI Extension; Jeanselme et al. 2024 for subgroup breakdown). §4.4 mandates post-cleaning validation re-running pre-cleaning invariants.
- **Rubin (1976); Little & Rubin (2019, 3rd ed.):** MCAR/MAR/MNAR taxonomy. The ledger classifies MMR as MAR-primary (tournament dataset selection effect), highestLeague as MAR, clanTag as MAR. These mechanism classifications are inherited from 01_04_01 ledger; this step does not re-derive them.
- **van Buuren (2018, *Flexible Imputation of Missing Data*, 2nd ed.):** warns against rigid global thresholds; the 5/40/80% thresholds in the audit are operational starting heuristics, not hard rules. Per van Buuren, primary-feature MMR at 83.95% is **dropped not imputed** because imputation would carry no information. **[OPINION]** Retaining MMR via `is_mmr_missing + MMR coalesced to median` would mask the dominant signal (rated vs unrated) under arbitrary noise; cleaner to drop and surface `is_mmr_missing` only.
- **Schafer & Graham (2002, *Psychological Methods* 7(2):147-177):** <5% MCAR boundary for safe listwise deletion. handicap=0 at 0.0045% (2 rows) and APM=0 at 2.53% are both well within this bound — listwise deletion or simple imputation is methodologically safe.
- **Sambasivan et al. (2021, CHI '21, "Data Cascades in High-Stakes AI"):** rationale for surfacing decisions explicitly. The DS-SC2-01..10 list is a direct application of this principle. **[OPINION]** The fact that the 01_04_01 audit produced 10 surfaced decisions instead of 10 silent imputations is itself a cascade-prevention measure; 01_04_02 closes those decisions with traceable rationale.
- **Davis et al. (2024, *Machine Learning* 113:6977-7010):** sports-analytics methodology paper; nested dependencies (matches within seasons within patches) are the central concern. Map-author and game-version columns are non-predictive metadata at the player level; dropping them does not lose signal.
- **CRISP-DM Phase 3 (Wirth & Hipp 2000):** cleaning-report convention. The 01_04_02 markdown artifact will follow the cleaning-registry table format already established in 01_04_01 markdown.
- **Manual 02_FEATURE_ENGINEERING_MANUAL.md:** referenced only for Phase boundary discipline. 01_04_02 produces the **column set Phase 02 will operate on**; any imputation, scaling, or encoding belongs to Phase 02 (per the Phase 02 manual's pipeline-overview section excluded from PIPELINE_SECTIONS but methodologically authoritative).

---

## Execution Steps

The plan organizes execution into Sections 1-6 below: per-DS resolutions (1), VIEW DDL changes (2), post-cleaning validation (3), new ROADMAP step entry (4), notebook cell structure (5), and status updates (6). The notebook is implemented as a single 28-cell artifact at `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py`. Each section below is execution-step content.

## Section 1: Per-DS resolution proposal (the heart of the plan)

For each DS-SC2-NN, I cite the ledger row (view + column + n_sentinel + pct_missing_total + n_distinct), the recommendation_justification text from the ledger, and propose ONE recommended resolution with rationale. The DDL effect (modify VIEW / drop column / convert sentinel / no-op) is explicit. Open user-judgement calls are listed in Section 8.

### DS-SC2-01 — MMR (sentinel=0)

| VIEW | n_sentinel | pct_missing_total | n_distinct | Ledger rec | carries_semantic_content |
|---|---|---|---|---|---|
| matches_flat_clean | 37,290 | **83.95%** | 1,026 | DROP_COLUMN | True |
| player_history_all | 37,489 | **83.65%** | 1,031 | DROP_COLUMN | True |

**Question (from ROADMAP):** Convert MMR=0 to NULL and drop, OR retain MMR=0 as explicit `unranked` categorical alongside `is_mmr_missing`, OR run rated-subset only as sensitivity arm?

**Decision:** **DROP `MMR` from both VIEWs; RETAIN `is_mmr_missing` as a derived boolean.** Remove `mf.MMR` from the SELECT list of both VIEWs; do NOT use NULLIF (MMR is dropped, so converting it to NULL first would be a no-op). The `is_mmr_missing` derived column reads directly from `mf.MMR` in the source `matches_flat` VIEW (which is unchanged per I9 and the structural-reference assumption), so the boolean signal is preserved without needing MMR in the cleaned VIEWs. The boolean captures the rated vs unrated distinction, which is the dominant axis at 83.95%.

**Rationale:**
- Ledger justification text: *"NULL+sentinel rate 83.95% exceeds 80% (Rule S4 / van Buuren 2018). Imputation indefensible at this rate."*
- Retaining a 16% rated cohort's MMR as a continuous feature alongside an 84%-NULL column degenerates downstream models — most splits would be on `is_mmr_missing` and `MMR` would only carry signal in the rated subset. This is precisely the rated-subset-as-sensitivity-arm path, but **without dropping MMR, Phase 02 must impute** (median, mean, or constant), which van Buuren (2018) classifies as indefensible at this rate.
- Alternative considered (retain MMR + keep `is_mmr_missing` + Phase 02 imputes 0 → median): rejected because median of the rated subset (~3,500 MMR) would be assigned to 84% of rows and become an arbitrary distributional shift. **[OPINION]** This is worse than dropping the column — at least dropping is honest about the limited signal available.
- Alternative considered (retain MMR=0 as explicit "unranked" categorical bucket via `MMR_bucket` discrete column): rejected for `matches_flat_clean` because the meaningful bucketing is binary (rated/unrated) and `is_mmr_missing` already captures this; for `player_history_all` the same logic applies.
- **Sensitivity arm note:** A future Phase 02 ablation may wish to restrict to `is_mmr_missing=FALSE` and use the raw rated MMR. The raw MMR is recoverable from `replay_players_raw.MMR` (raw table untouched per I9), so dropping from cleaned VIEWs does not foreclose this.

**DDL effect:**
- `matches_flat_clean`: remove `mf.MMR` from SELECT; keep `CASE WHEN mf.MMR = 0 THEN TRUE ELSE FALSE END AS is_mmr_missing` (already present).
- `player_history_all`: remove `mf.MMR` from SELECT; keep `is_mmr_missing` (already present).
- Schema YAML: drop MMR row from `player_history_all.yaml`; create `matches_flat_clean.yaml` without MMR.

### DS-SC2-02 — highestLeague (sentinel='Unknown')

| VIEW | n_sentinel | pct_missing_total | n_distinct | Ledger rec |
|---|---|---|---|---|
| matches_flat_clean | 31,997 | **72.04%** | 10 | DROP_COLUMN |
| player_history_all | 32,338 | **72.16%** | 10 | DROP_COLUMN |

**Question (from ROADMAP):** Drop entirely, OR retain 'Unknown' as its own category?

**Decision:** **DROP `highestLeague` from both VIEWs.**

**Rationale:**
- Ledger justification: *"Rate 72.04% in 40-80%; non-primary feature; cost/benefit favors simplicity per Rule S4."* `is_primary_feature=False` per spec.
- The 10-bucket cardinality (Bronze..GrandMaster + Unknown) is a categorical with 72% mass on a single sentinel value — encoding it as a one-hot or ordinal would create an effectively binary `is_unknown` flag plus 9 sparse buckets covering only 28% of rows.
- League information for the rated 28% is already partially captured by MMR (via the rated subset, even though MMR is dropped from the VIEW, the underlying skill ordering is observable in the raw table). Retaining `highestLeague` would not improve a Phase 02 feature set; it would just add a high-cardinality categorical with mostly-missing semantics.
- **Alternative considered** (retain as 11-level categorical including 'Unknown'): rejected — Manual §4.1 favours simplicity; Phase 02 categorical encoding cost (one-hot expansion to 11 cols, or target encoding requiring CV-aware leakage prevention) outweighs the marginal signal in 28% of rows.
- **Alternative considered** (derive `is_known_league` boolean only): rejected as dominated by `is_mmr_missing` (the two are highly correlated — both reflect tournament-replay vs ladder-replay provenance per ledger mechanism justification).

**DDL effect:**
- `matches_flat_clean`: remove `mf.highestLeague` from SELECT.
- `player_history_all`: remove `mf.highestLeague` from SELECT.
- Schema YAML: drop highestLeague row.

### DS-SC2-03 — clanTag (sentinel='')

| VIEW | n_sentinel | pct_missing_total | n_distinct | Ledger rec |
|---|---|---|---|---|
| matches_flat_clean | 32,840 | **73.93%** | 255 | DROP_COLUMN |
| player_history_all | 33,210 | **74.10%** | 257 | DROP_COLUMN |

**Question (from ROADMAP):** Drop entirely, OR retain as derived `is_in_clan` boolean only?

**Decision:** **DROP `clanTag` from both VIEWs; RETAIN `isInClan` (already present in raw, BOOLEAN).** The raw table already supplies an `isInClan` boolean (line 87 in player_history_all.yaml: "Whether the player is in a clan"); the clanTag VARCHAR is redundant given the boolean.

**Rationale:**
- Ledger justification: *"Rate 73.93% in 40-80%; non-primary feature; cost/benefit favors simplicity per Rule S4."*
- Retaining the 255-cardinality clan-tag categorical at 26% non-empty would require either target encoding (CV-aware, costly) or one-hot (255-col expansion). Neither is justified by the marginal signal — clan identity does not predict 1v1 outcome at the player level.
- The redundant boolean `isInClan` already encodes the only useful axis (in-clan vs not). It has zero missingness in both VIEWs (ledger rows: `isInClan` n_null=0, n_sentinel=0, mechanism=N/A, recommendation=RETAIN_AS_IS).
- **Alternative considered** (derive `is_in_clan` from clanTag instead of using raw `isInClan`): rejected because raw `isInClan` is already present — adding a derived alternative would create a duplicate. The current VIEW DDL passes `mf.isInClan` through unchanged.

**DDL effect:**
- `matches_flat_clean`: remove `mf.clanTag` from SELECT; keep `mf.isInClan`.
- `player_history_all`: remove `mf.clanTag` from SELECT; keep `mf.isInClan`.
- Schema YAML: drop clanTag row.

### DS-SC2-04 — result in player_history_all (Undecided/Tie sentinel)

| VIEW | n_sentinel | pct_missing_total | n_distinct | Ledger rec |
|---|---|---|---|---|
| player_history_all | 26 | **0.058%** | 4 | EXCLUDE_TARGET_NULL_ROWS |

**Note:** `matches_flat_clean.result` has 0 NULLs and 0 Undecided/Tie rows because the upstream `true_1v1_decisive` CTE filters them out; ledger row mechanism=N/A, recommendation=RETAIN_AS_IS. The decision applies to `player_history_all` only.

**Question (from ROADMAP):** How should NULL-target rows in `player_history_all` be handled when computing player history features (drop / mark as DRAW / retain with NaN target)?

**Decision:** **RETAIN the 26 Undecided/Tie rows in `player_history_all.result` as-is (string literal 'Undecided' / 'Tie'); add a derived BOOLEAN column `is_decisive_result` defined as `(result IN ('Win', 'Loss'))`. Phase 02 win-rate features filter on `is_decisive_result = TRUE` for the win-rate denominator and use `(result IN ('Win', 'Loss', 'Undecided', 'Tie'))` for the games-played denominator.**

**Rationale:**
- Ledger recommendation `EXCLUDE_TARGET_NULL_ROWS` is correct **for the target VIEW** (`matches_flat_clean`, where these rows are already excluded). For the **history VIEW**, excluding the rows entirely would lose 26 games of valid context (player skill, race chosen, opponent encountered, map played, started_timestamp) — context that should still feed feature engineering even when the outcome was technically a draw.
- Per Manual §4.2 (preserve raw + flag rather than delete) AND per the audit's **B6 deferral framing** (sentinel-with-semantic-content cases — `result IN ('Undecided', 'Tie')` carries genuine game-state meaning), the audit explicitly marks `EXCLUDE_TARGET_NULL_ROWS` as non-binding and surfaces the question for downstream resolution. The planner here exercises that B6 deferral by choosing the retain-with-flag arm: preserve the literal result + add `is_decisive_result` so Phase 02 can choose its denominator policy without modifying the VIEW.
- Alternative considered (NULLIF result to NULL when `result NOT IN ('Win','Loss')`): rejected because it conflates `Win/Loss with NULL outcome` (which can mean either Undecided or Tie or true data missingness) and loses the Undecided-vs-Tie distinction. Keeping the literal string preserves provenance.
- Alternative considered (re-encode `Undecided`/`Tie` to a single 'DRAW' bucket via CASE WHEN): rejected because it makes the 4-distinct-value column 3-valued for no clear analytical gain; Phase 02 can map to 'DRAW' on read if needed.
- Alternative considered (drop rows with target IN ('Undecided','Tie')): rejected per the rationale above — losing 26 games of context.

**DDL effect:**
- `player_history_all`: keep `mf.result` unchanged; add `(mf.result IN ('Win', 'Loss')) AS is_decisive_result` as a new column.
- `matches_flat_clean`: no change (the upstream CTE already filters; ledger F1 override applies).
- Schema YAML: add `is_decisive_result` BOOLEAN row.

### DS-SC2-05 — selectedRace (sentinel='', already converted to 'Random' upstream)

| VIEW | n_sentinel | pct_missing_total | n_distinct | Ledger rec |
|---|---|---|---|---|
| matches_flat_clean | 0 | **0.00%** | 5 | RETAIN_AS_IS |
| player_history_all | 0 | **0.00%** | 8 | RETAIN_AS_IS |

**Question:** Audit confirms zero residual; is any further action needed?

**Decision:** **NO-OP.** The 01_04_01 VIEW DDL already applies `CASE WHEN mf.selectedRace = '' THEN 'Random' ELSE mf.selectedRace END AS selectedRace` and the audit confirms zero empty strings remain in either VIEW. No DDL change.

**Rationale:** Ledger F1 override (zero missingness) ⇒ mechanism=N/A, recommendation=RETAIN_AS_IS. The upstream normalisation is the cleaning rule; nothing to add.

**DDL effect:** None. (Cleaning registry will reference the existing `random_race_normalisation` rule from 01_04_01 for traceability.)

### DS-SC2-06 — gd_mapSizeX / gd_mapSizeY (sentinel=0, already CASE-WHEN'd to NULL upstream)

| VIEW | column | n_sentinel | pct_null | pct_missing_total | Ledger rec |
|---|---|---|---|---|---|
| matches_flat_clean | gd_mapSizeX | 0 | 1.22% | 1.22% | RETAIN_AS_IS |
| matches_flat_clean | gd_mapSizeY | 0 | 1.30% | 1.30% | RETAIN_AS_IS |
| player_history_all | gd_mapSizeX | 0 | 1.24% | 1.24% | RETAIN_AS_IS |
| player_history_all | gd_mapSizeY | 0 | 1.35% | 1.35% | RETAIN_AS_IS |

**Question:** VIEWs already CASE-WHEN to NULL; is anything else needed?

**Decision:** **NO-OP on the sentinel handling. PROPOSE secondary action: drop both `gd_mapSizeX` and `gd_mapSizeY` from `matches_flat_clean` only**, retaining `metadata_mapName` as the sole map identifier in the prediction-target VIEW. Retain in `player_history_all` for context.

**Rationale (no-op on sentinel):** Ledger justification: *"Rate 1.22% < 5% (Schafer & Graham 2002 boundary citation). Listwise deletion or simple imputation acceptable in Phase 02."* The CASE-WHEN already converted parse-artifact zeros to NULL.

**Rationale (drop from matches_flat_clean):** Map size is a derived attribute of the map name. `metadata_mapName` (n_distinct=181 in matches_flat_clean) is the canonical identifier; map size is a second-order feature of the map. Including both invites multicollinearity and adds two columns with 1.22-1.30% NULL rates whose information content is fully captured by the map name. **[OPINION]** Phase 02 will encode the map categorically (target encoding or top-N + 'other') and recover map-size signal indirectly through that categorical's effect.

**Alternative considered (retain map size for explicit map-area features):** rejected for `matches_flat_clean` — Phase 02 can derive `map_area = mapSizeX * mapSizeY` from raw if needed via a separate Phase 02 step. The cleaning-VIEW does not need to pre-compute it.

**Retained in player_history_all** because the historical view should be richer to support Phase 02 feature exploration.

**DDL effect:**
- `matches_flat_clean`: remove `mf.gd_mapSizeX`, `mf.gd_mapSizeY`, `mf.is_map_size_missing` (the flag becomes meaningless without the column it flags).
- `player_history_all`: no change.
- Schema YAML: drop the three columns from `matches_flat_clean.yaml`; keep them in `player_history_all.yaml`.

### DS-SC2-07 — gd_mapAuthorName (non-predictive metadata)

| VIEW | n_sentinel | n_null | pct_missing_total | n_distinct | Ledger rec |
|---|---|---|---|---|---|
| matches_flat_clean | 0 | 0 | 0.00% | 26 | RETAIN_AS_IS |
| player_history_all | 0 | 0 | 0.00% | 28 | RETAIN_AS_IS |

**Question (from ROADMAP):** Drop on grounds of being non-predictive metadata even before missingness considered?

**Decision:** **DROP `gd_mapAuthorName` from `matches_flat_clean`. RETAIN in `player_history_all` for context.**

**Rationale:**
- 26 distinct map authors across 22,209 replays. The author of a map is not a function of player skill, opponent, or game state — it is a labelling artifact of map curation. Including it in the prediction-target VIEW would add a 26-cardinality categorical with no plausible causal link to outcome.
- Ledger mechanism is N/A (zero missingness) and ledger recommendation is RETAIN_AS_IS — but this recommendation is **based on missingness alone**; the planner correctly applies a domain-judgement override (Manual §4.1 cleaning-registry justification field allows domain rationale).
- Dropping is a "domain knowledge" override that must be documented in the cleaning registry's Justification field.
- **[OPINION]** Including author names in a prediction VIEW would also introduce subtle leakage risk: if a map author is correlated with a tournament era (some authors were prolific in 2018-2019, others in 2022-2023), the categorical could become a temporal proxy. Best to drop.

**Retained in player_history_all** for the same reason as map size — feature exploration richness.

**DDL effect:**
- `matches_flat_clean`: remove `mf.gd_mapAuthorName` from SELECT.
- `player_history_all`: no change.
- Schema YAML: drop from `matches_flat_clean.yaml`; keep in `player_history_all.yaml`.

### DS-SC2-08 — go_* constants (n_distinct=1)

Per ledger constants-detection branch, the following columns are reported `n_distinct=1` (mechanism=N/A, recommendation=DROP_COLUMN, justification "True constant column; no information content"):

**In `matches_flat_clean` (10 constants):**
1. `go_advancedSharedControl` (BOOLEAN)
2. `go_battleNet` (BOOLEAN)
3. `go_cooperative` (BOOLEAN)
4. `go_fog` (BIGINT)
5. `go_heroDuplicatesAllowed` (BOOLEAN)
6. `go_lockTeams` (BOOLEAN)
7. `go_noVictoryOrDefeat` (BOOLEAN)
8. `go_observers` (BIGINT)
9. `go_practice` (BOOLEAN)
10. `go_randomRaces` (BOOLEAN)
11. `go_teamsTogether` (BOOLEAN)
12. `go_userDifficulty` (BIGINT)

**Verified count:** 12 `go_*` constant columns in matches_flat_clean (direct CSV grep: ledger rows where `n_distinct == 1.0` and column name starts with `go_` returns exactly the 12 listed above). Identical 12 in player_history_all.

**In `player_history_all` (12 constants):** same set.

**Variable-cardinality `go_*` retained:** `go_amm` (n_distinct=2), `go_clientDebugFlags` (n_distinct=2), `go_competitive` (n_distinct=2). Ledger mechanism=N/A, recommendation=RETAIN_AS_IS.

**Question (from ROADMAP):** Confirm which exact go_* are constant in each VIEW; drop in 01_04_02?

**Decision:** **DROP all 12 constant `go_*` columns from BOTH `matches_flat_clean` AND `player_history_all`.** Keep the 3 variable-cardinality `go_*` columns (`go_amm`, `go_clientDebugFlags`, `go_competitive`) for Phase 02 to assess.

**Rationale:**
- Ledger justification: *"True constant column; n_distinct=1 across N rows; no information content."* This is a corpus-derived empirical fact, not a domain assumption.
- Constants cannot contribute to prediction (they have zero variance ⇒ zero correlation with outcome; sklearn's `VarianceThreshold(0)` filter would drop them automatically). Pre-dropping at the cleaning step makes the column set defensible at the Phase 01 gate.
- Per Manual §3.3 (constant columns are equally uninformative for classification) and per the runtime constants-detection backstop in the 01_04_01 audit framework.
- Retaining variable `go_*` (amm, clientDebugFlags, competitive) gives Phase 02 the option to test whether AMM/competitive flags interact with outcome — these capture meaningful tournament-format variation.

**DDL effect:**
- `matches_flat_clean`: remove the 12 constants from SELECT.
- `player_history_all`: remove the 12 constants from SELECT.
- Schema YAML: drop the 12 rows from each.

### DS-SC2-09 — handicap (sentinel=0, 2 anomalous rows; carries_semantic_content=True)

| VIEW | n_sentinel | pct_missing_total | n_distinct | Ledger rec | carries_semantic_content |
|---|---|---|---|---|---|
| matches_flat_clean | 2 | 0.0045% | 2 | CONVERT_SENTINEL_TO_NULL | True (non-binding) |
| player_history_all | 2 | 0.0045% | 2 | CONVERT_SENTINEL_TO_NULL | True (non-binding) |

**Question (from ROADMAP):** NULLIF + listwise deletion (Rule S3 / negligible rate), OR retain 0 as `is_handicap_anomalous` flag?

**Decision:** **DROP `handicap` from BOTH VIEWs; DROP `is_handicap_anomalous` from `matches_flat_clean` (currently present per 01_04_01 DDL line 537) since it becomes meaningless without `handicap`.**

**Rationale:**
- The `handicap` column has `n_distinct=2` (values 100 and 0) across 44,418 rows, with 99.9955% being the standard value (100). This is effectively a near-constant column with 2 anomalies.
- Neither converting to NULL (Rule S3 path, recommended by audit) nor retaining as a flag gives Phase 02 useful signal: at 2 anomalies in a 44k corpus, the column is functionally a constant.
- **Alternative considered (NULLIF → NULL, retain column):** rejected because column becomes 99.9955% one value + 0.0045% NULL — effectively constant.
- **Alternative considered (retain 0 + `is_handicap_anomalous` flag):** the flag is currently in the VIEW but its base rate is 0.0045% — it would never be selected as a feature by any reasonable Phase 02 pipeline. Dropping the column avoids carrying a near-constant.
- **Alternative considered (drop the 2 anomalous replays entirely via replay-level CTE):** rejected as too aggressive — these replays are otherwise valid 1v1_decisive records; flagging or dropping the column is sufficient.
- **Override of audit recommendation rationale:** The audit's `CONVERT_SENTINEL_TO_NULL` recommendation is explicitly tagged "non-binding" because `carries_semantic_content=True` (B6 deferral). DROP is the right resolution here per the same logic that drives DS-SC2-08 (constants policy): a column with `n_distinct=1` (or n_distinct=2 with 99.9955% one value, as here) is effectively a TRUE-constant by W7's relaxed definition. The 12 go_* columns flagged by W7 are dropped wholesale; handicap belongs to that family — 2 outliers do not justify carrying a column that's otherwise constant. The B6 deferral framework allows planner overrides for semantic-content sentinels; this override applies the constants-policy reasoning rather than the low-rate-NULLIF reasoning.

**DDL effect:**
- `matches_flat_clean`: remove `mf.handicap` and `is_handicap_anomalous` from SELECT.
- `player_history_all`: remove `mf.handicap` from SELECT (the player_history VIEW does not currently have `is_handicap_anomalous`; per the existing DDL only matches_flat_clean has it).
- Schema YAML: drop `handicap` and `is_handicap_anomalous` rows.

### DS-SC2-10 — APM in player_history_all (sentinel=0, 2.53%; carries_semantic_content=True)

| VIEW | n_sentinel | pct_missing_total | n_distinct | Ledger rec | carries_semantic_content |
|---|---|---|---|---|---|
| player_history_all | 1,132 | **2.53%** | 556 | CONVERT_SENTINEL_TO_NULL | True (non-binding) |

**APM is excluded from `matches_flat_clean` (Invariant I3) — decision applies to `player_history_all` only.**

**Question (from ROADMAP):** Convert APM=0 to NULL via NULLIF, OR retain APM=0 as a categorical encoding for "extremely short / unparseable game"?

**Decision:** **CONVERT APM=0 to NULL via `NULLIF(mf.APM, 0) AS APM` in `player_history_all`. Add a derived `is_apm_unparseable` BOOLEAN column = `(mf.APM = 0)` so the missingness-as-signal information is preserved per Manual §4.2 ("Add binary indicator columns").**

**Rationale:**
- The 97.9% overlap between APM=0 and selectedRace='' (research log 2026-04-16, finding: "97.9% of APM=0 rows coincide with selectedRace=''") indicates these are unparseable replays — APM=0 is a measurement artifact, not a genuine zero-action game.
- Listwise deletion is methodologically safe at 2.53% per Schafer & Graham (2002), but Phase 02 may want to keep these rows for context features (race, map, opponent) while excluding them from APM-derived features. Sentinel-to-NULL preserves both options.
- The `is_apm_unparseable` flag preserves the signal "this row's APM cannot be trusted" so Phase 02 can decide its policy per-feature.
- **Alternative considered (retain APM=0 as numeric):** rejected because Phase 02 mean/median calculations would be biased downward by 1,132 zero entries. Worse, any APM-derived feature (e.g., difference between focal and opponent APM) would have spurious 0-vs-positive contrasts.
- **Alternative considered (drop APM column entirely):** rejected because APM is a valid IN_GAME_HISTORICAL signal for the rated subset (97.5% of rows have APM > 0, with `n_distinct=556`); dropping forfeits a strong skill signal for 43,685 valid rows.
- **Override of audit "non-binding" tag:** The plan accepts the audit recommendation because the rate is low (2.53% < 5% MCAR boundary), the data-quality interpretation is unambiguous (parse failure for empty selectedRace), and the indicator-column pattern preserves missingness-as-signal.

**DDL effect:**
- `player_history_all`: replace `mf.APM` with `NULLIF(mf.APM, 0) AS APM`; add `(mf.APM = 0) AS is_apm_unparseable`.
- `matches_flat_clean`: no change (APM is excluded per I3).
- Schema YAML: update `APM` description noting NULLIF; add `is_apm_unparseable` BOOLEAN row.

---

## Section 2: VIEW DDL changes (concrete final-state per VIEW)

### `matches_flat` — UNCHANGED

Per Assumption above, `matches_flat` (the structural JOIN VIEW) is preserved as-is so re-derivation is possible from a single SQL pass.

### `matches_flat_clean` — final column set

Columns currently present (per current DDL, Section 1 lines 519-590) → cleaning action:

| Column | Action | Source DS |
|---|---|---|
| replay_id | KEEP (identity) | — |
| filename | KEEP (identity, I10) | — |
| toon_id | KEEP (identity) | — |
| nickname | KEEP (identity) | — |
| playerID | KEEP (identity) | — |
| userID | KEEP (identity) | — |
| result | KEEP (target) | — |
| **MMR** | **DROP** | DS-SC2-01 |
| is_mmr_missing | KEEP (derived from MMR before drop) | DS-SC2-01 |
| race | KEEP | — |
| selectedRace | KEEP (already normalised) | DS-SC2-05 |
| **handicap** | **DROP** | DS-SC2-09 |
| **is_handicap_anomalous** | **DROP** | DS-SC2-09 |
| region | KEEP | — |
| realm | KEEP | — |
| **highestLeague** | **DROP** | DS-SC2-02 |
| isInClan | KEEP | DS-SC2-03 |
| **clanTag** | **DROP** | DS-SC2-03 |
| startDir | KEEP | — |
| startLocX | KEEP | — |
| startLocY | KEEP | — |
| metadata_mapName | KEEP | — |
| **gd_mapSizeX** | **DROP** | DS-SC2-06 |
| **gd_mapSizeY** | **DROP** | DS-SC2-06 |
| **is_map_size_missing** | **DROP** | DS-SC2-06 |
| gd_maxPlayers | KEEP | — |
| **gd_mapAuthorName** | **DROP** | DS-SC2-07 |
| gd_mapFileSyncChecksum | KEEP | — |
| details_isBlizzardMap | KEEP | — |
| details_timeUTC | KEEP (I3 temporal anchor) | — |
| header_version | KEEP (CONTEXT) | — |
| metadata_baseBuild | KEEP (CONTEXT) | — |
| metadata_dataBuild | KEEP (CONTEXT) | — |
| metadata_gameVersion | KEEP (CONTEXT) | — |
| **go_advancedSharedControl** | **DROP** (constant) | DS-SC2-08 |
| go_amm | KEEP (n_distinct=2) | DS-SC2-08 |
| **go_battleNet** | **DROP** (constant) | DS-SC2-08 |
| go_clientDebugFlags | KEEP (n_distinct=2) | DS-SC2-08 |
| go_competitive | KEEP (n_distinct=2) | DS-SC2-08 |
| **go_cooperative** | **DROP** (constant) | DS-SC2-08 |
| **go_fog** | **DROP** (constant) | DS-SC2-08 |
| **go_heroDuplicatesAllowed** | **DROP** (constant) | DS-SC2-08 |
| **go_lockTeams** | **DROP** (constant) | DS-SC2-08 |
| **go_noVictoryOrDefeat** | **DROP** (constant) | DS-SC2-08 |
| **go_observers** | **DROP** (constant) | DS-SC2-08 |
| **go_practice** | **DROP** (constant) | DS-SC2-08 |
| **go_randomRaces** | **DROP** (constant) | DS-SC2-08 |
| **go_teamsTogether** | **DROP** (constant) | DS-SC2-08 |
| **go_userDifficulty** | **DROP** (constant) | DS-SC2-08 |

**Total cleaning: 49 cols → 28 cols (drop 21, no new cols added).**

Drop count by source:
- DS-SC2-01 (MMR): 1
- DS-SC2-02 (highestLeague): 1
- DS-SC2-03 (clanTag): 1
- DS-SC2-06 (gd_mapSizeX, gd_mapSizeY, is_map_size_missing): 3
- DS-SC2-07 (gd_mapAuthorName): 1
- DS-SC2-08 (12 go_* constants): 12
- DS-SC2-09 (handicap, is_handicap_anomalous): 2

**Total drops: 21. Final column count: 49 − 21 = 28.**

### `player_history_all` — final column set

51 columns currently present per existing schema YAML → cleaning action:

| Column | Action | Source DS |
|---|---|---|
| replay_id, filename, toon_id, nickname, playerID, userID | KEEP (6 identity cols) | — |
| result | KEEP (string-literal Win/Loss/Undecided/Tie) | DS-SC2-04 |
| **is_decisive_result** (NEW) | **ADD** = `(result IN ('Win','Loss'))` | DS-SC2-04 |
| **MMR** | **DROP** | DS-SC2-01 |
| is_mmr_missing | KEEP | DS-SC2-01 |
| race, selectedRace | KEEP | DS-SC2-05 |
| **handicap** | **DROP** | DS-SC2-09 |
| region, realm | KEEP | — |
| **highestLeague** | **DROP** | DS-SC2-02 |
| isInClan | KEEP | DS-SC2-03 |
| **clanTag** | **DROP** | DS-SC2-03 |
| **APM** | **MODIFY** to `NULLIF(mf.APM, 0) AS APM` | DS-SC2-10 |
| **is_apm_unparseable** (NEW) | **ADD** = `(mf.APM = 0)` | DS-SC2-10 |
| SQ | KEEP (already corrected via NULLIF in 01_04_01) | — |
| supplyCappedPercent | KEEP (IN_GAME_HISTORICAL) | — |
| header_elapsedGameLoops | KEEP (IN_GAME_HISTORICAL) | — |
| startDir, startLocX, startLocY | KEEP | — |
| metadata_mapName | KEEP | — |
| gd_mapSizeX, gd_mapSizeY | KEEP (history retains map area context per DS-SC2-06 differential) | DS-SC2-06 |
| gd_maxPlayers | KEEP | — |
| details_isBlizzardMap | KEEP | — |
| gd_mapAuthorName | KEEP (history retains, per DS-SC2-07 differential) | DS-SC2-07 |
| gd_mapFileSyncChecksum | KEEP | — |
| details_timeUTC | KEEP (I3 anchor) | — |
| header_version, metadata_baseBuild, metadata_dataBuild, metadata_gameVersion | KEEP (CONTEXT) | — |
| **go_advancedSharedControl, go_battleNet, go_cooperative, go_fog, go_heroDuplicatesAllowed, go_lockTeams, go_noVictoryOrDefeat, go_observers, go_practice, go_randomRaces, go_teamsTogether, go_userDifficulty** | **DROP** (12 constants) | DS-SC2-08 |
| go_amm, go_clientDebugFlags, go_competitive | KEEP (variable cardinality) | DS-SC2-08 |

**Net: 51 cols + 2 new (is_decisive_result, is_apm_unparseable) − 16 drops (MMR, handicap, highestLeague, clanTag, 12 go_* constants) − APM modified in place = 37 cols.**

(Verify: 51 − 16 + 2 = 37. APM is modified, not dropped.)

### `matches_long_raw` — UNCHANGED

Out of scope per Assumption.

---

## Section 3: Post-cleaning validation

Per Manual §4.4 (re-run all data invariants post-cleaning). The notebook will execute:

### 3.1 Zero-NULL identity assertions (MUST pass)

- `matches_flat_clean.replay_id IS NULL` count == 0
- `matches_flat_clean.toon_id IS NULL` count == 0
- `matches_flat_clean.result IS NULL` count == 0
- `matches_flat_clean.result NOT IN ('Win', 'Loss')` count == 0
- `player_history_all.replay_id IS NULL` count == 0
- `player_history_all.toon_id IS NULL` count == 0
- `player_history_all.result IS NULL` count == 0

### 3.2 Symmetry assertion (matches_flat_clean — Invariant I5)

- For every replay_id in matches_flat_clean: `COUNT(*) = 2 AND COUNT(*) FILTER (WHERE result='Win') = 1 AND COUNT(*) FILTER (WHERE result='Loss') = 1`. Asserted via `0 symmetry violations`.

### 3.3 Forbidden-column assertions

**Two sub-categories** to keep the cleaning_registry honest:

**(3.3a) Newly dropped in 01_04_02** — assert these are absent post-DDL:
- For `matches_flat_clean` (21 cols): `MMR`, `handicap`, `is_handicap_anomalous`, `highestLeague`, `clanTag`, `gd_mapSizeX`, `gd_mapSizeY`, `is_map_size_missing`, `gd_mapAuthorName`, and the 12 `go_*` constants.
- For `player_history_all` (16 cols): `MMR`, `handicap`, `highestLeague`, `clanTag`, and the 12 `go_*` constants.

**(3.3b) Verify still absent — pre-existing exclusions from prior PRs / 01_04_01** (NOT counted as 01_04_02 actions in the cleaning_registry):
- For `matches_flat_clean` only: 4 I3 cols (APM, SQ, supplyCappedPercent, header_elapsedGameLoops) excluded by PRs #138/#139 and 01_04_01; `details_gameSpeed`, `gd_gameSpeed` (constants from prior cleaning); `gd_isBlizzardMap` (duplicate); 4 cosmetic colour cols. These were never SELECTed in the current matches_flat_clean DDL — assertions are defense-in-depth verification, not new cleaning actions.

### 3.4 New-column assertions

- For `player_history_all`: assert `is_decisive_result` and `is_apm_unparseable` are present and BOOLEAN.

### 3.5 No-new-NULLs assertion

- For each KEPT column in `matches_flat_clean` that previously had `n_null=0` per the 01_04_01 ledger, assert `n_null` is still 0 after cleaning.
- For each KEPT column in `player_history_all` that previously had `n_null=0`, assert `n_null` is still 0.
- Exception: `APM` in `player_history_all` is expected to gain 1,132 NULLs (from `NULLIF(APM, 0)`); this is documented in the cleaning registry.

### 3.6 CONSORT-style flow (replay units)

Per Manual §4.3, produce a flow table:

| Stage | Replays in matches_flat_clean | Rows in matches_flat_clean | Replays in player_history_all | Rows in player_history_all |
|---|---|---|---|---|
| Before 01_04_02 (post 01_04_01) | 22,209 | 44,418 | 22,390 | 44,817 |
| After 01_04_02 column drops | 22,209 | 44,418 | 22,390 | 44,817 |

**Critical observation:** No row-level filtering happens in 01_04_02. All rule applications are column-level (DROP, MODIFY, ADD). The replay/row counts are identical before and after; the cleaning impact is measured in the **column count** delta:

| VIEW | Cols before | Cols dropped | Cols added | Cols modified | Cols after |
|---|---|---|---|---|---|
| matches_flat_clean | 49 | 21 | 0 | 0 | 28 |
| player_history_all | 51 | 16 | 2 | 1 (APM) | 37 |

This is the relevant CONSORT-style impact for a column-only cleaning step (Manual §4.3 explicitly accommodates non-row-based cleaning impact reporting).

### 3.7 Subgroup impact (Jeanselme et al. 2024)

For each dropped column from `matches_flat_clean`, document the subgroup impact: which player segments lose information. Required because Manual §4.3 mandates subgroup breakdown to surface algorithmic bias.

| Dropped column | Subgroup most affected | Impact |
|---|---|---|
| MMR (DS-SC2-01) | Rated players (16% of matches_flat_clean rows) — lose precise skill signal | `is_mmr_missing` retained as proxy |
| highestLeague (DS-SC2-02) | Players who appeared on ladder before tournament play (28%) — lose league-tier context | None retained (drop is final) |
| clanTag (DS-SC2-03) | Players in clans (~26%) — lose clan-identity feature | `isInClan` retained as proxy |
| gd_mapSizeX/Y (DS-SC2-06) | All players — lose explicit map-area; recoverable from metadata_mapName | None retained in matches_flat_clean; retained in player_history_all |
| gd_mapAuthorName (DS-SC2-07) | All players — lose author identity | None retained in matches_flat_clean; retained in player_history_all |
| 12 `go_*` constants (DS-SC2-08) | None — constant cols carry no information | N/A |
| handicap (DS-SC2-09) | 2 anomalous-game rows | Effectively no-op |

### 3.8 Cleaning registry update (Manual §4.1)

The 01_04_01 cleaning registry has 7 rules. 01_04_02 adds the following rules:

| Rule ID | Condition | Action | Justification | Impact |
|---|---|---|---|---|
| drop_mmr_high_sentinel | Always (column drop) | DROP MMR from matches_flat_clean and player_history_all | DS-SC2-01: ledger rate 83.95%/83.65%, Rule S4 / van Buuren 2018 | -1 col each VIEW; rated subset signal preserved via is_mmr_missing |
| drop_highestleague_mid_sentinel | Always | DROP highestLeague from both VIEWs | DS-SC2-02: ledger rate 72.04%/72.16%, Rule S4 non-primary | -1 col each VIEW |
| drop_clantag_mid_sentinel | Always | DROP clanTag from both VIEWs | DS-SC2-03: ledger rate 73.93%/74.10%, Rule S4 non-primary; isInClan retained | -1 col each VIEW |
| add_is_decisive_result | result IN ('Win','Loss') | ADD is_decisive_result BOOLEAN to player_history_all | DS-SC2-04: preserve Undecided/Tie context per Manual §4.2 | +1 col player_history_all |
| drop_mapsize_pred_view | Always | DROP gd_mapSizeX/Y/is_map_size_missing from matches_flat_clean | DS-SC2-06: redundant with metadata_mapName; retained in history | -3 cols matches_flat_clean |
| drop_mapauthor_pred_view | Always | DROP gd_mapAuthorName from matches_flat_clean | DS-SC2-07: domain-judgement non-predictive metadata | -1 col matches_flat_clean |
| drop_go_constants | n_distinct=1 in either VIEW | DROP 12 constant go_* cols from both VIEWs | DS-SC2-08: ledger constants-detection; zero information | -12 cols each VIEW |
| drop_handicap_near_constant | Always | DROP handicap + is_handicap_anomalous | DS-SC2-09: 2 anomalies in 44k = effectively constant | -2 cols matches_flat_clean (handicap + is_handicap_anomalous); -1 col player_history_all (handicap only — is_handicap_anomalous not present in player_history_all DDL) |
| nullif_apm_history | APM = 0 in player_history_all | APM → NULL via NULLIF; ADD is_apm_unparseable flag | DS-SC2-10: low-rate sentinel + indicator pattern (Manual §4.2) | 1,132 APM values → NULL; +1 col player_history_all |

### 3.9 Artifact: 01_04_02_post_cleaning_validation.json

Single JSON artifact capturing:
- `step`: "01_04_02"
- `dataset`: "sc2egset"
- `cleaning_registry`: list of new rules per §3.8
- `consort_flow_columns`: dict per §3.6 (cols before / dropped / added / modified / after per VIEW)
- `consort_flow_replays`: dict per §3.6 (replay/row counts unchanged)
- `subgroup_impact`: list per §3.7
- `validation_assertions`: dict per §3.1-3.5 with PASS/FAIL booleans
- `sql_queries`: full DDL for both VIEWs verbatim, plus all assertion SQL (Invariant I6)
- `decisions_resolved`: list of 10 entries DS-SC2-01..10 each with: `id`, `column`, `decision`, `rationale`, `ddl_effect` (mirroring Section 1)

---

## Section 4: New ROADMAP step entry for 01_04_02

```yaml
step_number: "01_04_02"
name: "Data Cleaning Execution — Act on DS-SC2-01..10"
description: >
  Acts on the 10 cleaning decisions surfaced by 01_04_01. Modifies VIEW DDL
  for matches_flat_clean and player_history_all (no raw table changes per
  Invariant I9): drops MMR (Rule S4 / 83.95%), highestLeague (Rule S4 / 72%),
  clanTag (Rule S4 / 74%), 12 go_* constants (DS-SC2-08), gd_mapAuthorName
  (DS-SC2-07 domain), gd_mapSizeX/Y from matches_flat_clean (DS-SC2-06),
  handicap (DS-SC2-09 near-constant). Modifies APM in player_history_all
  via NULLIF (DS-SC2-10) + adds is_apm_unparseable indicator. Adds
  is_decisive_result to player_history_all (DS-SC2-04). Reports CONSORT-style
  column-count flow + subgroup impact + post-cleaning invariant re-validation.
phase: "01 -- Data Exploration"
pipeline_section: "01_04 -- Data Cleaning"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 4"
dataset: "sc2egset"
question: >
  Which of the 10 decisions surfaced by 01_04_01 (DS-SC2-01..10) are
  resolved by DDL modifications, what is the column-count and subgroup
  impact, and do all post-cleaning invariants still hold?
method: >
  Modify CREATE OR REPLACE VIEW DDL for matches_flat_clean and player_history_all
  per per-DS resolutions (see plan Section 1). Apply column drops, the APM NULLIF,
  and two new derived columns (is_decisive_result, is_apm_unparseable). Re-run
  the assertion battery from 01_04_01 plus 01_04_02-specific assertions on the
  new column set. Produce a CONSORT-style column-count table and per-DS
  resolution log.
stratification: "By VIEW (matches_flat_clean vs player_history_all) and by DS-SC2-NN."
predecessors:
  - "01_04_01"
methodology_citations:
  - "Manual 01_DATA_EXPLORATION_MANUAL.md §4.1 (cleaning registry), §4.2 (non-destructive), §4.3 (CONSORT impact), §4.4 (post-validation)"
  - "Liu, X. et al. (2020). Reporting guidelines for clinical trial reports for interventions involving artificial intelligence: the CONSORT-AI extension. BMJ, 370."
  - "Jeanselme, V. et al. (2024). Participant Flow Diagrams for Health Equity in AI. Journal of Biomedical Informatics, 152."
  - "Schafer, J.L. & Graham, J.W. (2002). Missing data: Our view of the state of the art. Psychological Methods, 7(2)."
  - "van Buuren, S. (2018). Flexible Imputation of Missing Data, 2nd ed. CRC Press."
  - "Sambasivan, N. et al. (2021). Data Cascades in High-Stakes AI. CHI '21."
notebook_path: "sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py"
inputs:
  duckdb_views:
    - "matches_flat (44,817 rows -- structural JOIN, unchanged)"
    - "matches_flat_clean (44,418 rows / 22,209 replays -- pre-01_04_02)"
    - "player_history_all (44,817 rows / 22,390 replays -- pre-01_04_02)"
  prior_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.json (cleaning_registry, missingness_audit, consort_flow)"
    - "artifacts/01_exploration/04_cleaning/01_04_01_missingness_ledger.csv (100 rows, per-DS empirical evidence)"
    - "artifacts/01_exploration/04_cleaning/01_04_01_data_cleaning.md (decisions_surfaced reference)"
  schema_yamls:
    - "data/db/schemas/views/player_history_all.yaml (current — to be updated)"
outputs:
  duckdb_views:
    - "matches_flat_clean (replaced via CREATE OR REPLACE — 28 cols, 44,418 rows)"
    - "player_history_all (replaced via CREATE OR REPLACE — 37 cols, 44,817 rows)"
  schema_yamls:
    - "data/db/schemas/views/matches_flat_clean.yaml (NEW)"
    - "data/db/schemas/views/player_history_all.yaml (UPDATED)"
  data_artifacts:
    - "artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.json"
  report: "artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.md"
reproducibility: >
  Code and output in the paired notebook. All DDL stored verbatim in the
  validation JSON sql_queries block (Invariant I6). All thresholds derived
  from the 01_04_01 ledger CSV at runtime (Invariant I7). Re-runs deterministically.
scientific_invariants_applied:
  - number: "3"
    how_upheld: >
      No new feature computation. matches_flat_clean retains only PRE_GAME
      columns. player_history_all retains IN_GAME_HISTORICAL columns (APM, SQ,
      supplyCappedPercent, header_elapsedGameLoops) which are valid for
      historical computation per the I3 design constraint established in 01_04_01.
  - number: "5"
    how_upheld: >
      Symmetry assertion re-run: every replay_id in matches_flat_clean has
      exactly 1 Win + 1 Loss row. The is_decisive_result derivation in
      player_history_all is symmetric (depends only on result, not on player slot).
  - number: "6"
    how_upheld: >
      All DDL queries stored verbatim in JSON sql_queries. All assertion SQL
      stored verbatim. All per-DS rationale references the ledger row + ledger
      recommendation_justification by view+column.
  - number: "7"
    how_upheld: >
      Thresholds (5/40/80%) come from the 01_04_01 framework block (Schafer &
      Graham 2002 boundary; van Buuren 2018 warning). Per-DS empirical evidence
      (n_sentinel, pct_missing_total, n_distinct) is read from the 01_04_01
      ledger CSV at runtime, not hardcoded.
  - number: "9"
    how_upheld: >
      No raw tables modified. matches_flat (structural JOIN) unmodified.
      matches_long_raw (canonical skeleton from 01_04_00) unmodified. Only
      matches_flat_clean and player_history_all VIEWs are replaced via
      CREATE OR REPLACE. All inputs are 01_04_01 artifacts (predecessor) or
      this step's own DDL output.
gate:
  artifact_check: >
    artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.json
    and .md exist and are non-empty. Both schema YAMLs
    (matches_flat_clean.yaml NEW, player_history_all.yaml UPDATED) exist with
    correct column counts.
  continue_predicate: >
    matches_flat_clean has exactly 28 columns. player_history_all has exactly
    37 columns. All zero-NULL assertions pass (replay_id, toon_id, result in
    both VIEWs). Symmetry violations = 0 in matches_flat_clean. CONSORT column-
    count table reproduces drop counts per DS-SC2-01..10. STEP_STATUS.yaml has
    01_04_02: complete. PIPELINE_SECTION_STATUS for 01_04 transitions to complete
    if no further 01_04_NN steps are defined.
  halt_predicate: >
    Any zero-NULL assertion fails; any symmetry violation; any forbidden column
    appears in matches_flat_clean; any expected NEW column missing from
    player_history_all; column count off by even one from spec.
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.1 SC2EGSet (StarCraft II) > Data Cleaning Decisions"
research_log_entry: "Required on completion."
```

---

## Section 5: Notebook + cell structure

**Path:** `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py` (jupytext-paired `.ipynb` committed alongside per sandbox contract).

**Cell-by-cell outline:**

1. **Header markdown** — title, phase/section/dataset, invariants applied (I3, I5, I6, I7, I9), predecessor (01_04_01), revision marker.
2. **Cell — Imports** — `json`, `pathlib.Path`, `pandas as pd`, `numpy as np`, `from rts_predict.common.notebook_utils import get_notebook_db, get_reports_dir, setup_notebook_logging`. Set up logger.
3. **Cell — DuckDB writable connection** — `db = get_notebook_db("sc2", "sc2egset", read_only=False); con = db.con`.
4. **Cell — Load 01_04_01 ledger** — Read `01_04_01_missingness_ledger.csv` into a pandas DataFrame; print per-DS summary (rows for MMR, highestLeague, clanTag, etc., per VIEW). Establishes the empirical evidence base at the top of the notebook.
5. **Cell — Per-DS resolution log** — Print a markdown-formatted table of DS-SC2-01..10 with the planner's resolution and the ledger row that justifies it. (Documentation cell — no SQL.)
6. **Cell — Pre-cleaning column counts** — `DESCRIBE matches_flat_clean` and `DESCRIBE player_history_all`; assert 49 and 51 columns. (Failure here means DDL drift since 01_04_01.)
7. **Cell — Pre-cleaning row counts (CONSORT before)** — Capture `COUNT(*)` and `COUNT(DISTINCT replay_id)` for both VIEWs.
8. **Cell — Define new matches_flat_clean DDL** — Module-level `CREATE_MATCHES_FLAT_CLEAN_V2_SQL` constant per Section 2 column list. Comment block per `.claude/rules/sql-data.md` (purpose + row multiplicity).
9. **Cell — Replace matches_flat_clean** — `con.execute(CREATE_MATCHES_FLAT_CLEAN_V2_SQL)`; print confirmation.
10. **Cell — Define new player_history_all DDL** — Module-level `CREATE_PLAYER_HISTORY_ALL_V2_SQL` per Section 2 column list, including `NULLIF(mf.APM, 0) AS APM`, `(mf.APM = 0) AS is_apm_unparseable`, `(mf.result IN ('Win','Loss')) AS is_decisive_result`.
11. **Cell — Replace player_history_all** — `con.execute(CREATE_PLAYER_HISTORY_ALL_V2_SQL)`; print confirmation.
12. **Cell — Post-cleaning column counts** — `DESCRIBE matches_flat_clean` (assert 28); `DESCRIBE player_history_all` (assert 37). Print column lists for both.
13. **Cell — Forbidden-column assertions** (Section 3.3) — Build forbidden sets, assert intersection with column set is empty.
14. **Cell — New-column assertions** (Section 3.4) — Assert `is_decisive_result` in player_history_all and is BOOLEAN; assert `is_apm_unparseable` in player_history_all and is BOOLEAN.
15. **Cell — Zero-NULL identity assertions** (Section 3.1) — replay_id, toon_id, result on both VIEWs.
16. **Cell — Symmetry assertion** (Section 3.2) — Reuse SYMMETRY_SQL pattern from 01_04_01.
17. **Cell — No-new-NULLs assertion** (Section 3.5) — Iterate over kept-cols, assert n_null still 0 (skip APM in player_history_all, expect 1,132 NULLs there).
18. **Cell — APM NULLIF effect** — `SELECT COUNT(*) FILTER (WHERE APM IS NULL) AS apm_null, COUNT(*) FILTER (WHERE is_apm_unparseable) AS apm_unparseable FROM player_history_all`. Assert both equal 1,132.
19. **Cell — is_decisive_result distribution** — `SELECT result, is_decisive_result, COUNT(*) FROM player_history_all GROUP BY 1, 2 ORDER BY 1`. Print 4-row result; assert TRUE for Win/Loss, FALSE for Undecided/Tie.
20. **Cell — Post-cleaning row counts (CONSORT after)** — Same queries as step 7; assert unchanged.
21. **Cell — Subgroup impact summary** (Section 3.7) — Build the table, derived from the ledger CSV (e.g., MMR drop affects 16% rated rows; clanTag drop affects 26% in-clan rows).
22. **Cell — Cleaning registry update** (Section 3.8) — Build the 9 new rule-rows.
23. **Cell — Build artifact JSON** (Section 3.9) — Single dict with all sections; write to `artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.json`.
24. **Cell — Build markdown report** — Mirror 01_04_01 markdown format; write to `01_04_02_post_cleaning_validation.md`. Sections: Summary, Per-DS Resolutions (table + rationale), Cleaning Registry (table), CONSORT Column-Count Flow, Subgroup Impact, Validation Results.
25. **Cell — Update player_history_all schema YAML** — Re-run `DESCRIBE player_history_all`; rewrite `data/db/schemas/views/player_history_all.yaml` with new column list (drop MMR, handicap, highestLeague, clanTag, 12 go_* constants; add is_decisive_result, is_apm_unparseable; update APM description). Generated_date 2026-04-17. Step "01_04_02".

    **Schema YAML I3 enforcement (v2-BLOCKER-1 fix per round-2 critique):** The project's existing convention uses **single-token** `notes:` provenance categories on each column (vocabulary in current YAML: IDENTITY, TARGET, PRE_GAME, IN_GAME_HISTORICAL, CONTEXT). Operational instructions (e.g., "Phase 02 MUST filter match_time < T before aggregation") belong in the file's machine-readable `invariants:` block, NOT in per-column `notes:` prose. Round-1 BLOCKER-4/5 was correctly raised; the round-1 verbose-notes fix violated the file's convention without adding enforcement. v3 fix (per round-2 v2-BLOCKER-1):

    **(a) Per-column notes — single-token tags only:**
    - `is_decisive_result.notes`: `POST_GAME_HISTORICAL` (single token; new provenance category for outcome-DERIVED features)
    - `is_apm_unparseable.notes`: `IN_GAME_HISTORICAL` (single token; matches APM's existing tag)
    - **`result.notes`: `TARGET` (UNCHANGED per round-3 v3-BLOCKER-1 fix).** Round-2 v2-WARNING-1 proposed updating `result.notes` from TARGET to POST_GAME_HISTORICAL for "vocabulary parity"; round-3 review surfaced this as cross-dataset divergence (AoE2 sibling files at aoe2companion player_history_all.yaml:104 and aoestats player_history_all.yaml:89 retain TARGET vocabulary; changing only sc2egset would violate Invariant #8 cross-game protocol). v3-BLOCKER-1 fix: REVERT v2-WARNING-1 — KEEP TARGET on result. **Vocabulary distinction codified:** TARGET is a singleton sentinel for THE prediction label (the game-T outcome itself); POST_GAME_HISTORICAL is for DERIVATIONS of the outcome (the new is_decisive_result flag, future Phase 02 win-rate aggregates, etc.). The two tokens are NOT synonyms — the distinction is load-bearing for any tool that wants to "exclude all outcome-derived columns from features while keeping the outcome itself as the label".

    **(b) Invariants block extension — single-source operational meaning:** Extend the existing `invariants:` block (currently lines 271-282 of player_history_all.yaml carrying I3/I6/I9 entries) so that the I3 entry enumerates **all 5 provenance categories** (TARGET / IDENTITY / PRE_GAME / IN_GAME_HISTORICAL / POST_GAME_HISTORICAL / CONTEXT — note CONTEXT counts as a 6th category technically, but it's PRE_GAME-equivalent for temporal purposes; treat the distinct temporal-discipline categories as 5: TARGET, PRE_GAME, IN_GAME_HISTORICAL, POST_GAME_HISTORICAL, IDENTITY+CONTEXT-grouped) and states the filter requirement once.

    **Concrete I3 entry POST-insertion (executor copies verbatim into player_history_all.yaml invariants block, replacing the current single-string I3 description with this multi-key mapping):**

    ```yaml
    invariants:
      - id: I3
        description: >
          Temporal discipline / no future leakage. Each column carries a single-token
          provenance category in its notes: field. The vocabulary, with operational
          rules, is enumerated under provenance_categories below. Phase 02 MUST
          filter by match_time < T (the prediction target's started_timestamp)
          before aggregating ANY column tagged TARGET, IN_GAME_HISTORICAL, or
          POST_GAME_HISTORICAL into a feature for game T.
        provenance_categories:
          - TARGET: "THE prediction label itself (Win/Loss/Undecided/Tie). Singleton sentinel — only the result column carries this tag. Never aggregate without temporal exclusion (match_time < T); using it as a direct game-T feature IS target leakage."
          - POST_GAME_HISTORICAL: "The game-T outcome itself or any feature derived from it (e.g., is_decisive_result, future Phase-02 win-rate aggregates). SAFE only when used as a player-history aggregate FILTERED by match_time < T. UNSAFE as direct game-T feature. The TARGET singleton is conceptually a sub-class of this category but tagged separately for sentinel-clarity."
          - IN_GAME_HISTORICAL: "Available during/after game completion (e.g., APM, SQ, supplyCappedPercent, header_elapsedGameLoops, is_apm_unparseable). SAFE only when used as a player-history aggregate FILTERED by match_time < T. UNSAFE as direct game-T feature."
          - PRE_GAME: "Available before game T starts (e.g., MMR, leaderboard, race, map). Safe to use as feature for game T without temporal filtering."
          - IDENTITY: "Stable identifiers (replay_id, toon_id, profileId). No temporal constraint; not a feature input but a join key."
          - CONTEXT: "Game/match metadata (started_timestamp, mapName, gameLoops). PRE_GAME-equivalent for temporal purposes; available before game T."
      - id: I6
        description: "<existing I6 text — preserve verbatim>"
      - id: I9
        description: "<existing I9 text — preserve verbatim>"
      - id: I10
        description: "All replay_id derivation traces back to filename relative to raw_dir (per Invariant I10). Both VIEWs in this dataset (matches_flat_clean and player_history_all) share this constraint."
    ```

    **Notes on this YAML:**
    - 6 provenance categories listed (TARGET / POST_GAME_HISTORICAL / IN_GAME_HISTORICAL / PRE_GAME / IDENTITY / CONTEXT) — round-3 v3-WARNING-1 / v3-NOTE-1 fix: count is now explicit and consistent.
    - POST_GAME_HISTORICAL definition (round-3 v3-WARNING-2 fix) explicitly says "outcome itself or any feature derived from it" — eliminates the self-derivation contradiction.
    - I10 added as new entry to player_history_all.yaml invariants (round-3 v3-NOTE-2 fix) — parity with new matches_flat_clean.yaml which also gets I10 (cell 26).

26. **Cell — Create matches_flat_clean schema YAML (NEW)** — Mirror **the existing `player_history_all.yaml` flat-list shape** (top-level `table:`, `dataset:`, `columns: - name: ...` entries); the richer `docs/templates/duckdb_schema_template.yaml` Section A/`value:`/`required:` shape is NOT used here because no current schema YAML in the project follows it. `DESCRIBE matches_flat_clean`; write to `data/db/schemas/views/matches_flat_clean.yaml`. **Column ordering in YAML:** match the DDL SELECT-list order from `CREATE OR REPLACE matches_flat_clean` cell 14 verbatim (no re-sorting); this gives downstream reviewers a line-by-line diff that mirrors the SQL.

    **Invariants block (v2-NOTE-1 fix per round-2 critique):** The new YAML MUST include a top-level `invariants:` block analogous to the player_history_all.yaml structure (currently lines 271-282 there). Required entries:
    - **I3** (PRE_GAME-only column set): "matches_flat_clean is the prediction-target VIEW. ALL columns must be PRE_GAME (available before game T starts). IN_GAME_HISTORICAL and POST_GAME_HISTORICAL columns are excluded by construction. Verified by §3.3a/§3.3b assertions: APM/SQ/supplyCappedPercent/header_elapsedGameLoops/result-derived-flags absent."
    - **I5** (symmetry): "Every replay_id has exactly 2 rows: 1 with result='Win', 1 with result='Loss'. Verified by §3.2 assertion."
    - **I6** (reproducibility): "DDL is reproducible from raw + 01_04_00 + 01_04_01 + this notebook (01_04_02). All SQL stored verbatim in 01_04_02_post_cleaning_validation.json sql_queries block."
    - **I9** (no feature computation in cleaning step): "01_04_02 modifies the column SET (drops/adds), never the values. No imputation, scaling, or encoding. Phase 02 owns those transforms."
    - **I10** (filename relative to raw_dir): "All replay_id derivation traces back to filename relative to raw_dir per Invariant I10."

    Also use single-token `notes:` provenance categories per the v2-BLOCKER-1 convention. matches_flat_clean's column-by-category breakdown after 01_04_02:
    - **TARGET** (1 col): `result` (the prediction label)
    - **IDENTITY** (2 cols): `replay_id`, `toon_id`
    - **CONTEXT** (~6 cols): `started_timestamp`, `mapName`, `gameLoops`, etc. (PRE_GAME-equivalent for temporal purposes)
    - **PRE_GAME** (~19 cols): all remaining feature-eligible columns (race, leaderboard, etc.)
    - **IN_GAME_HISTORICAL**: NONE (excluded by I3 — APM, SQ, supplyCappedPercent, header_elapsedGameLoops are absent)
    - **POST_GAME_HISTORICAL**: NONE (excluded by I3 — is_decisive_result and other outcome-derivations are in player_history_all only, not in the prediction VIEW)

    matches_flat_clean.yaml invariants block must include the same `provenance_categories:` enumeration as player_history_all.yaml (above) for vocabulary consistency, even though only 4 of the 6 categories appear in this VIEW. Single source of truth for the vocabulary.
27. **Cell — Close connection** — `db.close()`.
28. **Cell — Final summary print** — Column counts before/after, drops applied, 9 new cleaning registry rules, gate predicate verdict.

**Total cells: ~28.** Following the 01_04_01 notebook structure (which is ~2100 lines, ~80+ cells). The notebook is shorter because no new census passes are required — the audit work is done; this notebook **executes** the resolutions.

**Notebook contract notes:**
- All DDL constants module-level with `_SQL` suffix (per `.claude/rules/python-code.md`).
- `print()` for data exploration and assertions; `logger` only for connection diagnostics.
- All SQL embedded verbatim in JSON `sql_queries` block (Invariant I6).
- Notebook will pair with `.ipynb` automatically via jupytext (no manual conversion).

---

## Section 6: STEP_STATUS / PIPELINE_SECTION_STATUS / PHASE_STATUS update

**After 01_04_02 completes:**

1. **STEP_STATUS.yaml** — append:
```yaml
  "01_04_02":
    name: "Data Cleaning Execution"
    pipeline_section: "01_04"
    status: complete
    completed_at: "2026-04-17"
```

2. **PIPELINE_SECTION_STATUS.yaml** — Per the derivation comments in the file ("Pipeline section is complete when ALL its steps are complete"), 01_04 transitions from `in_progress` to `complete` **iff no further 01_04_NN steps are planned**. Per Manual 01 §4 the canonical Pipeline Section 01_04 contents are: cleaning registry (§4.1), non-destructive cleaning (§4.2), CONSORT impact (§4.3), post-validation (§4.4), missing data handling (§4.5), reporting standards (§4.6). Steps 01_04_00 (canonical normalisation), 01_04_01 (audit), 01_04_02 (execution + post-validation) cover all six manual sections. **WARNING-5 critique fix:** the executor MUST grep `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` for any pre-listed 01_04_03+ step block before bumping PIPELINE_SECTION_STATUS — if any such block exists (currently believed to be none), 01_04 stays `in_progress` and the gate condition's PIPELINE_SECTION line is dropped from this PR. **Prior-revert context:** commit 7d0463d reverted a premature 01_04 closure because notebooks were not re-run after IN-GAME removals; this PR addresses that by re-executing the notebook end-to-end as part of 01_04_02 (cell 27+), so the prior reversion's reasoning no longer applies. **Per-dataset scope note:** PIPELINE_SECTION_STATUS.yaml is per-dataset (sc2egset only); the 01_04 closure here applies to sc2egset alone — aoestats and aoec datasets keep `01_04: in_progress` until their own 01_04_02 work lands in independent PRs (per user Option A).

```yaml
  "01_04":
    name: "Data Cleaning"
    phase: "01"
    status: complete
```

3. **PHASE_STATUS.yaml** — Phase 01 stays `in_progress` because Pipeline Sections 01_05 (Temporal & Panel EDA) and 01_06 (Decision Gates) remain `not_started`.

(No PHASE_STATUS change in this PR.)

**Research log entry** — append a new top-of-file entry under `2026-04-17` (or completion date):

```markdown
## 2026-04-17 -- [Phase 01 / Step 01_04_02] Data Cleaning Execution

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** Acts on DS-SC2-01..10. Modifies matches_flat_clean and player_history_all VIEW DDL. No raw changes (I9). Closes Pipeline Section 01_04.
[CONSORT column-count summary, decisions resolved table, gate verdict]
```

---

## File Manifest

| File | Action |
|---|---|
| `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.py` | Create |
| `sandbox/sc2/sc2egset/01_exploration/04_cleaning/01_04_02_data_cleaning_execution.ipynb` | Create (jupytext-paired) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.json` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/04_cleaning/01_04_02_post_cleaning_validation.md` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/matches_flat_clean.yaml` | Create |
| `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/views/player_history_all.yaml` | Update |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` | Update (append 01_04_02) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/PIPELINE_SECTION_STATUS.yaml` | Update (01_04: in_progress → complete) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` | Update (add 01_04_02 step block per Section 4) |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` | Update (prepend 2026-04-17 [01_04_02] entry) |

## Gate Condition

- **Both DuckDB VIEWs replaced**: `matches_flat_clean` has 28 columns; `player_history_all` has 37 columns; both queryable; both have correct row counts (44,418 and 44,817 respectively).
- **Both schema YAMLs present**: `matches_flat_clean.yaml` (NEW) and `player_history_all.yaml` (UPDATED) on disk with the correct column manifest.
- **Both artifacts present**: `01_04_02_post_cleaning_validation.json` contains `cleaning_registry`, `consort_flow_columns`, `subgroup_impact`, `validation_assertions` (all PASS), `sql_queries` (verbatim DDL), `decisions_resolved` (10 entries). `01_04_02_post_cleaning_validation.md` contains: Summary, Per-DS Resolutions table, Cleaning Registry table, CONSORT Column-Count Flow, Subgroup Impact table, Validation Results.
- **All assertions pass**: zero-NULL on identity cols (matches_flat_clean: replay_id, toon_id, result); symmetry violations = 0; forbidden cols absent; new cols present; APM NULLIF count = 1,132 in player_history_all; is_decisive_result FALSE-count = 26 in player_history_all.
- **STEP_STATUS.yaml** has `01_04_02: complete`. **PIPELINE_SECTION_STATUS.yaml** has `01_04: complete`. **PHASE_STATUS.yaml** unchanged (Phase 01 still in_progress).
- **ROADMAP.md** has a new `### Step 01_04_02` block matching the YAML in Section 4.
- **research_log.md** has a 2026-04-17 [01_04_02] entry summarising the resolutions and CONSORT flow.

## Out of scope

- **aoestats and aoe2companion datasets**: per user Option A, sc2egset is the pattern-establisher PR. aoestats and aoec follow in independent planning rounds + PRs (see Open Questions).
- **matches_long_raw modification**: out of scope per Assumption — its `rating_pre_raw` (MMR=0 sentinel) handling is deferred to Phase 02 per the schema YAML provenance note.
- **matches_flat modification**: out of scope per Assumption — it is the structural JOIN VIEW and stays as the audit-stable reference.
- **Imputation, scaling, encoding**: deferred to Phase 02. 01_04_02 produces the **column set** Phase 02 will operate on; it does not transform values.
- **Feature engineering on the new flag columns** (`is_decisive_result`, `is_apm_unparseable`): deferred to Phase 02.
- **Cross-game decision arbitration** (does aoestats use the same `is_decisive_result` pattern? does aoec use the same `is_apm_unparseable` pattern?): each dataset's planning round addresses its own analogue independently. Cross-cutting decisions get a CROSS entry in `reports/research_log.md` *after* all three dataset PRs land.
- **Schema YAML for `matches_flat`**: The structural JOIN VIEW does not currently have a schema YAML and 01_04_02 does not create one. Could be a future minor cleanup.
- **DuckDB persistent backup**: VIEWs are CREATE OR REPLACE in the persistent DB. No backup of the prior VIEW state is required because 01_04_01 is fully reproducible from raw + the predecessor notebook.

---

## Open Questions

**STATUS: ALL 8 ANSWERED — RECOMMENDATIONS LOCKED.** User reviewed each option in chat before plan write and approved the planner's recommendation for every item (1-8). The list below is preserved as audit trail; no resolution remains pending.

These are user-judgement calls where two arms are equally defensible. The plan records the recommended resolution but the user may prefer the alternative; please respond before execution begins.

1. **DS-SC2-01 (MMR drop vs retain):** Plan recommends DROP MMR from both VIEWs (rationale: 83.95% sentinel, van Buuren 2018 warning against imputation at this rate; signal preserved via `is_mmr_missing`). Alternative: retain MMR + `is_mmr_missing`, defer imputation choice to Phase 02. **Resolves by:** user decision. If user prefers retention, swap DDL accordingly; downstream Phase 02 inherits the imputation decision.
2. **DS-SC2-04 (player_history_all.result handling):** Plan recommends RETAIN literal Win/Loss/Undecided/Tie strings + add `is_decisive_result` flag (rationale: preserve game context). Alternatives: (a) drop Undecided/Tie rows entirely, (b) recode to a 'DRAW' bucket. **Resolves by:** user decision. Phase 02 win-rate denominator policy depends on this.
3. **DS-SC2-06 (gd_mapSizeX/Y in matches_flat_clean):** Plan recommends DROP from matches_flat_clean (retained in player_history_all). Alternative: retain in both, let Phase 02 decide. **Resolves by:** user decision. If retain, change is purely additive (one less DDL change in matches_flat_clean).
4. **DS-SC2-07 (gd_mapAuthorName in matches_flat_clean):** Plan recommends DROP from matches_flat_clean (domain judgement: non-predictive metadata; subtle temporal-leakage risk). Alternative: retain. **Resolves by:** user decision.
5. **DS-SC2-09 (handicap drop vs NULLIF):** Plan recommends DROP (effectively constant — 2 anomalies in 44k). Alternative: NULLIF + retain (audit's original recommendation, marked non-binding due to carries_semantic_content=True). **Resolves by:** user decision. If NULLIF, change DDL accordingly and keep `is_handicap_anomalous`.
6. **DS-SC2-10 (APM NULLIF behaviour):** Plan recommends NULLIF + add `is_apm_unparseable` flag. Alternative: retain APM=0 as numeric, defer to Phase 02. **Resolves by:** user decision.
7. **PIPELINE_SECTION_STATUS for 01_04 — close after 01_04_02?** Plan recommends marking 01_04 complete after 01_04_02 lands (no 01_04_03 envisioned). Alternative: keep 01_04 in_progress in case a follow-up is needed. **Resolves by:** user decision. Recommend close — Manual §4 contents are fully covered by 01_04_00 + 01_04_01 + 01_04_02.
8. **aoestats / aoec pattern deferral acknowledgement:** Per user Option A, this PR is sc2egset-only. Confirm aoestats and aoec follow in subsequent planning rounds + PRs (planner needs explicit confirmation that the pattern this plan establishes is the one to replicate, possibly with cross-dataset adjustments). **Resolves by:** user decision.

---

> **For Category A or F, adversarial critique is required before execution.** After user approval of this plan, dispatch **reviewer-adversarial** to produce `planning/current_plan.critique.md`. Do not begin execution until critique is complete and addressed.

