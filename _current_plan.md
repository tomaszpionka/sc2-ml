SC2EGSet Phase 1 Scientific Augmentation Plan

Context

Phase 1 (Corpus inventory and data exploration) for the SC2EGSet dataset is in progress. Steps 1.1 through 1.7 are complete with 16 report artifacts produced.
Step 1.8 (game settings and field completeness audit) is defined in the roadmap but not yet executed. This plan performs a systematic gap analysis of the
existing Phase 1 scope against the methodology prescribed by Manual 01 (Data Exploration), identifies what is missing, and specifies new steps (1.9 onward) to
close those gaps. Existing Steps 1.1 through 1.8 remain byte-identical.

---
DELIVERABLE 1 — Gap Analysis Table

Manual Section: §1 — Source inventory (Datasheets-for-Datasets)
Status: PARTIAL
Existing Step(s): Steps 1.1, 1.2, 1.5
Gap Description: Steps 1.1–1.2 cover corpus dimensions, tournament counts, date range, event coverage. Step 1.5 covers patch landscape. However, no structured
  Datasheets-for-Datasets artifact exists. Missing: formal documentation of collection method, sampling mechanism, known biases (survivorship, selection effects

  from tournament-only coverage), licensing, update frequency, and the 57-question framework.
Thesis Impact: Cannot write §4.1.1 (SC2EGSet description) without a citable structured source inventory. Examiners may challenge the dataset description as
  incomplete.
────────────────────────────────────────
Manual Section: §3.1 — Column-level profiling for every extractable JSON key
Status: PARTIAL
Existing Step(s): Steps 1.4, 1.8 (pending)
Gap Description: Step 1.4 profiles APM and MMR with full year/league breakdowns. Step 1.8 specifies profiling for SQ, supplyCappedPercent, handicap, and several

  game settings fields. But only 4–5 of the ~39 known ToonPlayerDescMap fields have been profiled or are scheduled. Fields like highestLeague, race, nickname,
  clanTag, isInClan, startDir, startLocX, startLocY, playerID lack the §3.1 battery (null rate, zero rate, cardinality, distribution summary, head/tail
samples).
   The top-level JSON columns (header, initData, details, metadata) contain many sub-keys beyond what 1.8 covers.
Thesis Impact: Unaudited fields may contain dead fields mistakenly used as features, or usable fields missed entirely. Violates the "uniform treatment"
principle
  of the Manual and Scientific Invariant 7 (cherry-picking which fields to profile introduces an implicit threshold at "I looked at it").
────────────────────────────────────────
Manual Section: §3.2 — Dataset-level profiling
Status: PARTIAL
Existing Step(s): Steps 1.1, 1.2, 1.3, 1.4
Gap Description: Duplicates: covered (1.1D — 0 exact, 88 near-duplicates). Temporal coverage: covered (1.1A — 2016-01 to 2024-12). Class balance of the target:
  NOT covered — no step counts Win vs Loss at the replay level (we only have slot-level counts: 22,382 Win vs 22,409 Loss, but this is not the same as
per-replay
   class balance given the 13 anomalous replays). Feature completeness heatmap: NOT produced. Correlation matrix: NOT produced.
Thesis Impact: Class balance is the most fundamental dataset-level property for a binary classification thesis. A heatmap of field completeness across all JSON
  keys is needed to visually confirm which fields are usable. Without correlations, multicollinearity risks are invisible.
────────────────────────────────────────
Manual Section: §3.3 — Dead / constant / near-constant field detection
Status: PARTIAL
Existing Step(s): Step 1.4 (MMR classified as dead); Step 1.8F (SQ, supplyCappedPercent pending)
Gap Description: MMR was classified as unusable (83.6% zero). But a systematic scan of ALL ToonPlayerDescMap fields for dead/constant/near-constant status has
  not been done. The test should be applied uniformly to all 39 fields, not selectively.
Thesis Impact: A field that is 99.9% constant would be missed entirely if we only profile the fields we already know about. This is the definition of
  cherry-picking (Manual §7).
────────────────────────────────────────
Manual Section: §3.4 — Distribution analysis (histograms, KDE, QQ, ECDFs)
Status: PARTIAL
Existing Step(s): Step 1.3 (duration: histogram + short-tail zoom)
Gap Description: Duration has two histograms (full range, short tail). APM has a year-by-year zero rate table but no histogram of its actual value distribution.

  No KDE, QQ plot, or ECDF has been produced for any field. The distribution analysis has been limited to percentile tables and bin counts, not the visual
  methods prescribed by the Manual.
Thesis Impact: The thesis Data chapter needs visual distribution characterization, not just percentile tables. QQ plots are specifically called "the gold
  standard" in the Manual. Without them, distributional assumptions (e.g., normality of APM residuals, shape of SQ distribution) are untested.
────────────────────────────────────────
Manual Section: §4 — Bivariate and multivariate analysis
Status: PARTIAL
Existing Step(s): None (existing), Steps 1.13 and 1.14 (planned)
Gap Description: No correlations between any pair of fields have been computed. No cross-tabulations (e.g., race vs result, matchup vs win rate). No
  Simpson's-paradox stratification by year or tournament. Steps 1.13 (cat-cat: race x matchup x result) and 1.14 (num-num: Spearman correlations) partially
  close this gap by covering the bivariate cases most relevant to pre-game feature engineering. However, true multivariate stratification (e.g., race x map x
  era x result interaction) is NOT covered by these steps and is deferred to Phase 2, where the player appearances table enables richer multi-factor analysis.
  No PCA or dimensionality reduction is included.
Thesis Impact: Bivariate analysis reveals confounds before feature engineering. Without it, Phase 7 features may include redundant or confounded variables. The
  Manual explicitly warns against skipping this (§7 — over-aggregation pitfall). The bivariate coverage from Steps 1.13–1.14 addresses the most critical
  confound risks; the remaining multivariate gap is acceptable at this phase because Phase 1 operates on raw JSON fields that lack the structured player-game
  grain needed for full multi-factor stratification.
────────────────────────────────────────
Manual Section: §5 — Temporal leakage risk audit
Status: MISSING
Existing Step(s): None
Gap Description: No systematic audit of which fields carry temporal leakage risk. SQ and supplyCappedPercent are computed from the replay itself (post-hoc
  metrics), so they are NOT pre-game features — they are computed from the outcome. APM is also a post-game aggregate. These fields cannot be used as pre-game
  features without violating Scientific Invariant 3. No step currently documents which ToonPlayerDescMap fields are pre-game vs. post-game.
Thesis Impact: This is the single most dangerous gap. If SQ or supplyCappedPercent are used as pre-game features in Phase 7, the model would have access to
  in-game information, producing inflated accuracy. Scientific Invariant 3 states violations here are "fatal to the thesis."
────────────────────────────────────────
Manual Section: §6.1 — Four required deliverables
Status: MISSING
Existing Step(s): None
Gap Description: No data dictionary artifact exists. No data quality report artifact exists (individual step reports exist but no consolidated report). No risk
  register exists. No modeling readiness decision has been articulated. The current Phase 1 gate definition (ROADMAP.md) lists 10 factual statements (a–j) but
  does not map to the §6.1 deliverables.
Thesis Impact: These four deliverables are the formal output of the pre-modeling phases. Without them, Phase 2+ lacks a documented basis. The thesis methodology

  chapter cannot claim compliance with CRISP-ML(Q) frameworks without producing them.

---
DELIVERABLE 2 — Augmented Step List

All existing Steps 1.1 through 1.8 remain unchanged. The following new steps are numbered 1.9 onward.

### Status of Step 1.8

**Recommendation: Option A — Step 1.8 is SUPERSEDED by Steps 1.9 and 1.10.**

Step 1.8 as defined in the ROADMAP contains two kinds of work: (1) critical game-settings verifications (sub-steps A through E, G, H — game speed, handicap, error flags, victory/defeat mode, random race, map metadata, version consistency) and (2) per-field profiling of SQ, supplyCappedPercent, and a field completeness summary (sub-steps F, I). The first kind is self-contained verification work that produces `01_game_settings_audit.md` and `01_error_flags_audit.csv`. The second kind — profiling selected ToonPlayerDescMap fields and producing a completeness summary — is a strict subset of what Step 1.10 does uniformly for ALL fields. Running Step 1.8F before Step 1.10 would produce redundant artifacts: SQ and supplyCappedPercent would be profiled twice, once ad-hoc in 1.8F and once systematically in 1.10A–D.

Therefore: **Step 1.8 sub-steps A–E, G, H execute as originally defined** (they are game-settings checks, not field profiling). **Step 1.8 sub-steps F and I are closed without execution**; their planned artifacts (`01_field_completeness_summary.csv` and the SQ/supplyCappedPercent sections of `01_game_settings_audit.md`) are superseded by Step 1.10's uniform profiling outputs (`01_10_tpdm_column_profile.csv`, `01_10_tpdm_field_status.csv`). PHASE_STATUS.yaml should be updated when this plan is applied to note Step 1.8F/I as superseded by Step 1.10.

---
Step 1.9 — Systematic ToonPlayerDescMap field inventory and JSON structure verification

Context: The ToonPlayerDescMap column is a JSON object keyed by toon string, where each value is a JSON object containing player-level metadata. Steps 1.4 and
1.8 profile selected fields (APM, MMR, SQ, supplyCappedPercent, handicap, race, selectedRace, result, highestLeague). However, the full set of keys in these
per-player objects has never been enumerated from the data itself. Manual 01 §3.1 requires column-level profiling for every extractable field, and constraint 9
requires verifying JSON structure constancy before profiling values. This step satisfies Manual 01 §1 (schema discovery) and §3.1 (column-level profiling
prerequisite). Feeds thesis §4.1.1 (SC2EGSet description).

Inputs: raw table.

Sub-steps:

1.9A — Enumerate all distinct keys in ToonPlayerDescMap player objects

SELECT DISTINCT json_key
FROM (
    SELECT unnest(json_keys(entry.value)) AS json_key
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
)
ORDER BY json_key;

poetry run sc2 db --dataset sc2egset query "SELECT DISTINCT json_key FROM (SELECT unnest(json_keys(entry.value)) AS json_key FROM raw, LATERAL json_each(\"ToonPlayerDescMap\") AS entry) ORDER BY json_key" --format table

1.9B — Verify key-set constancy across all player slots

WITH key_sets AS (
    SELECT
        filename,
        entry.key AS toon,
        LIST(k ORDER BY k) AS key_list
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry,
         LATERAL unnest(json_keys(entry.value)) AS t(k)
    GROUP BY filename, entry.key
)
SELECT key_list, COUNT(*) AS n_slots
FROM key_sets
GROUP BY key_list
ORDER BY n_slots DESC;

poetry run sc2 db --dataset sc2egset query "WITH key_sets AS (SELECT filename, entry.key AS toon, LIST(k ORDER BY k) AS key_list FROM raw, LATERAL json_each(\"ToonPlayerDescMap\") AS entry, LATERAL unnest(json_keys(entry.value)) AS t(k) GROUP BY filename, entry.key) SELECT key_list, COUNT(*) AS n_slots FROM key_sets GROUP BY key_list ORDER BY n_slots DESC" --format csv

1.9C — Enumerate all distinct keys in top-level JSON columns (header, initData, details, metadata)

For each of header, initData, details, metadata:

SELECT DISTINCT json_key
FROM (
    SELECT unnest(json_keys(header)) AS json_key FROM raw
)
ORDER BY json_key;

poetry run sc2 db --dataset sc2egset query "SELECT DISTINCT json_key FROM (SELECT unnest(json_keys(header)) AS json_key FROM raw) ORDER BY json_key" --format table

Repeat for initData, details, metadata. For nested objects (e.g., initData->'$.gameDescription'), recursively enumerate one level deeper.

Artifacts:
- 01_09_tpdm_field_inventory.csv
- 01_09_tpdm_key_set_constancy.csv
- 01_09_toplevel_field_inventory.csv

Thesis mapping: §4.1.1 — SC2EGSet schema documentation

Gate condition:
- Artifact check: All three CSV files exist and are non-empty.
- Continue predicate: If the key-set is constant (one variant with 100% of slots) or nearly constant (dominant variant covers >99% of slots), continue to Step
1.10.
- Halt predicate: If more than 5 distinct key-set variants exist each covering >5% of slots, halt Phase 1 and escalate, because the assumption that all player
slots have identical schema (which all downstream JSON path extraction depends on) would be violated.

[CROSS-GAME]

---
Step 1.10 — Uniform column-level profiling of all ToonPlayerDescMap fields

Context: Manual 01 §3.1 prescribes a standard profiling battery for every variable. Step 1.9 will have enumerated the complete field list. This step applies the
 §3.1 battery uniformly to all fields (constraint 6: treat all fields symmetrically, no cherry-picking). Feeds thesis §4.1.1 (field descriptions) and §4.1.2 (data quality).

Inputs: raw table. Complete field list from Step 1.9.

Sub-steps:

1.10A — Null/missing rate, zero rate, cardinality, distinct-value count

For each field F from Step 1.9A (via a generated UNION ALL query):

SELECT
    '{field_name}' AS field_name,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'{json_path}') IS NULL THEN 1 ELSE 0 END) AS null_count,
    ROUND(100.0 * SUM(CASE WHEN (entry.value->>'{json_path}') IS NULL
        THEN 1 ELSE 0 END) / COUNT(*), 2) AS null_pct,
    SUM(CASE WHEN (entry.value->>'{json_path}') = '0'
        OR (entry.value->>'{json_path}') = '' THEN 1 ELSE 0 END) AS zero_or_empty_count,
    ROUND(100.0 * SUM(CASE WHEN (entry.value->>'{json_path}') = '0'
        OR (entry.value->>'{json_path}') = '' THEN 1 ELSE 0 END) / COUNT(*), 2) AS zero_or_empty_pct,
    COUNT(DISTINCT (entry.value->>'{json_path}')) AS distinct_count,
    ROUND(COUNT(DISTINCT (entry.value->>'{json_path}'))::DOUBLE / COUNT(*), 6) AS uniqueness_ratio
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry;

The full UNION ALL query is generated by build_tpdm_profiling_query(field_list: list[str]) -> str in exploration.py. CLI invocation:

poetry run sc2 db --dataset sc2egset query "<generated SQL>" --format csv

1.10B — Distribution summary for numeric fields (min/max/mean/median/percentiles)

For each field classified as numeric in 1.10A (distinct_count > 2, values parse as numbers):

SELECT
    '{field_name}' AS field_name,
    MIN(val) AS min_val, MAX(val) AS max_val,
    ROUND(AVG(val), 2) AS mean_val,
    ROUND(MEDIAN(val), 2) AS median_val,
    ROUND(STDDEV(val), 2) AS std_val,
    ROUND(QUANTILE_CONT(val, 0.01), 2) AS p01,
    ROUND(QUANTILE_CONT(val, 0.05), 2) AS p05,
    ROUND(QUANTILE_CONT(val, 0.25), 2) AS p25,
    ROUND(QUANTILE_CONT(val, 0.75), 2) AS p75,
    ROUND(QUANTILE_CONT(val, 0.95), 2) AS p95,
    ROUND(QUANTILE_CONT(val, 0.99), 2) AS p99,
    ROUND((QUANTILE_CONT(val, 0.75) - QUANTILE_CONT(val, 0.25)), 2) AS iqr
FROM (
    SELECT (entry.value->>'{json_path}')::DOUBLE AS val
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
    WHERE (entry.value->>'{json_path}') IS NOT NULL
      AND TRY_CAST((entry.value->>'{json_path}') AS DOUBLE) IS NOT NULL
)
WHERE val != 0;

1.10C — Top-k frequent values for categorical/string fields

For each field with distinct_count <= 100:

SELECT
    '{field_name}' AS field_name,
    (entry.value->>'{json_path}') AS value,
    COUNT(*) AS frequency,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 2
ORDER BY 3 DESC
LIMIT 20;

1.10D — Dead / constant / near-constant detection (Manual 01 §3.3)

Applied as a Python classification from 1.10A results:

def classify_field_status(
    null_pct: float, distinct_count: int, uniqueness_ratio: float, total_slots: int
) -> str:
    """Classify field as dead, constant, near-constant, or active.

    Threshold source: Manual 01 §3.3 — "a uniqueness ratio below 0.001 is a
    reasonable starting point" for flagging near-constant columns.
    """
    if null_pct == 100.0:
        return "dead"
    if distinct_count == 1:
        return "constant"
    # Threshold: uniqueness_ratio < 0.001 (Manual 01 §3.3)
    if uniqueness_ratio < 0.001:
        return "near-constant"
    return "active"

1.10E — Year-stratified zero/null rates for all fields (Manual 01 §7)

SELECT
    EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year,
    '{field_name}' AS field_name,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN (entry.value->>'{json_path}') IS NULL
        OR (entry.value->>'{json_path}') = '0' THEN 1 ELSE 0 END) AS zero_or_null,
    ROUND(100.0 * SUM(CASE WHEN (entry.value->>'{json_path}') IS NULL
        OR (entry.value->>'{json_path}') = '0' THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_zero_or_null
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1, 2
ORDER BY 2, 1;

poetry run sc2 db --dataset sc2egset query "<generated UNION ALL SQL per field>" --format csv

Artifacts:
- 01_10_tpdm_column_profile.csv
- 01_10_tpdm_numeric_distributions.csv
- 01_10_tpdm_categorical_topk.csv
- 01_10_tpdm_field_status.csv
- 01_10_tpdm_availability_by_year.csv

Thesis mapping: §4.1.1 — field descriptions; §4.1.2 — data quality summary

Gate condition:
- Artifact check: All five CSV files exist and are non-empty.
- Continue predicate: If every field from Step 1.9 has a complete profiling row in 01_10_tpdm_column_profile.csv, continue to Step 1.11.
- Halt predicate: Halt and escalate to user if the number of "active" fields (per the classify_field_status classification) is insufficient to construct any reasonable pre-game feature set. Specifically: halt if, after excluding fields classified as "dead" or "constant", fewer than 3 fields remain with classification PRE_GAME (as determined in the subsequent Step 1.11). The premise being tested is that ToonPlayerDescMap contains sufficient per-player metadata for pre-game feature construction. If this premise is violated, no downstream feature engineering is possible from this data source alone.

[CROSS-GAME]

---
Step 1.11 — Temporal leakage risk classification for all fields

Context: Manual 01 §5 requires a temporal leakage risk audit for every field that may feed Phase 7 (feature engineering). Scientific Invariant 3 states that no
feature for game T may use information from game T or later, and that violations are "fatal to the thesis." Several ToonPlayerDescMap fields are computed from
the replay itself (post-game aggregates), not from the player's pre-game profile. This step classifies every field by temporal availability. Feeds thesis §3.3
(methodology — temporal discipline).

Inputs: Field inventory from Step 1.9. Field profiles from Step 1.10. SC2EGSet documentation (Bialecki et al. 2023). Blizzard s2client-proto documentation.

Sub-steps:

1.11A — Classify each field by temporal availability

Domain-knowledge annotation step. Each field receives one label:

- PRE_GAME: Value is known before the game starts and does not change during the game. Safe for pre-game features. Examples: race, selectedRace, nickname,
highestLeague, MMR (the rating before the game).
- POST_GAME: Value is computed from in-game events after the game ends. Using this as a pre-game feature violates Invariant 3. Examples: APM, SQ,
supplyCappedPercent, result.
- AMBIGUOUS: Cannot be definitively classified without further investigation. Document the specific uncertainty. AMBIGUOUS fields are conservatively excluded from pre-game features (safe_for_pre_game_features = False) and recorded in the risk register produced by Step 1.16.

def classify_temporal_availability(field_name: str) -> dict:
    """Classify a ToonPlayerDescMap field by temporal availability.
    Returns dict with keys: field_name, classification, rationale,
    safe_for_pre_game_features, source_documentation.

    For AMBIGUOUS fields, safe_for_pre_game_features is always False
    and rationale is set to "ambiguous — conservatively excluded pending
    documentation."
    """
    ...

1.11B — Verify POST_GAME classification empirically for APM and SQ

APM–duration correlation (APM is a post-game aggregate per game clock, not a pre-game profile value):

SELECT
    ROUND(CORR(
        (entry.value->>'$.APM')::DOUBLE,
        (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0
    ), 4) AS apm_duration_correlation,
    COUNT(*) AS n
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
WHERE (entry.value->>'$.APM')::DOUBLE > 0;

poetry run sc2 db --dataset sc2egset query "SELECT ROUND(CORR((entry.value->>'$.APM')::DOUBLE, (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0), 4) AS apm_duration_correlation, COUNT(*) AS n FROM raw, LATERAL json_each(\"ToonPlayerDescMap\") AS entry WHERE (entry.value->>'$.APM')::DOUBLE > 0" --format table

SQ–duration correlation:

SELECT
    ROUND(CORR(
        (entry.value->>'$.SQ')::DOUBLE,
        (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0
    ), 4) AS sq_duration_correlation,
    COUNT(*) AS n
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
WHERE TRY_CAST((entry.value->>'$.SQ') AS DOUBLE) IS NOT NULL
  AND (entry.value->>'$.SQ')::DOUBLE > 0;

poetry run sc2 db --dataset sc2egset query "SELECT ROUND(CORR((entry.value->>'$.SQ')::DOUBLE, (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0), 4) AS sq_duration_correlation, COUNT(*) AS n FROM raw, LATERAL json_each(\"ToonPlayerDescMap\") AS entry WHERE TRY_CAST((entry.value->>'$.SQ') AS DOUBLE) IS NOT NULL AND (entry.value->>'$.SQ')::DOUBLE > 0" --format table

1.11C — Document the classification in a structured table

AMBIGUOUS fields are written to the output CSV with `safe_for_pre_game_features = False` and rationale marked `"ambiguous — conservatively excluded pending documentation."`.

Artifacts:
- 01_11_temporal_leakage_classification.csv (field_name, classification [PRE_GAME/POST_GAME/AMBIGUOUS], rationale, safe_for_pre_game_features [true/false],
source)
- 01_11_leakage_empirical_checks.md (APM-duration and SQ-duration correlation results with the SQL that produced them)

Thesis mapping: §3.3 — temporal discipline methodology; §4.1.3 — temporal leakage risk audit

Gate condition:
- Artifact check: Both files exist and are non-empty.
- Continue predicate: If every field from Step 1.9 has a classification and all POST_GAME fields are clearly documented with rationale, continue to Step 1.12.
- Halt predicate: Continue if every AMBIGUOUS field can be conservatively excluded from pre-game features (i.e., classified safe_for_pre_game_features = False by default) and recorded in the risk register produced by Step 1.16. Halt and escalate only if a field is both AMBIGUOUS and so structurally central to Phase 3 feature engineering that conservative exclusion would block the construction of any reasonable pre-game feature set.

[CROSS-GAME]

---
Step 1.12 — Dataset-level class balance and feature completeness heatmap

Context: Manual 01 §3.2 requires dataset-level profiling including class balance of the target variable and a feature completeness heatmap. Step 1.1 counted Win
 (22,382) vs Loss (22,409) at the player-slot level, but the target variable for prediction is replay-level outcome. This step produces the correct replay-level
 class balance and a visual heatmap of field completeness. Feeds thesis §4.1.2 (data quality).

Inputs: raw table. Field profiles from Step 1.10.

Sub-steps:

1.12A — Replay-level class balance (after excluding structural anomalies)

WITH valid_replays AS (
    SELECT
        filename,
        SUM(CASE WHEN entry.value->>'$.result' = 'Win' THEN 1 ELSE 0 END) AS win_count,
        SUM(CASE WHEN entry.value->>'$.result' = 'Loss' THEN 1 ELSE 0 END) AS loss_count,
        COUNT(*) AS player_count
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
    GROUP BY filename
)
SELECT
    SUM(CASE WHEN win_count = 1 AND loss_count = 1 AND player_count = 2
        THEN 1 ELSE 0 END) AS valid_1v1_replays,
    SUM(CASE WHEN win_count != 1 OR loss_count != 1 OR player_count != 2
        THEN 1 ELSE 0 END) AS excluded_replays,
    COUNT(*) AS total_replays
FROM valid_replays;

poetry run sc2 db --dataset sc2egset query "WITH valid_replays AS (SELECT filename, SUM(CASE WHEN entry.value->>'$.result' = 'Win' THEN 1 ELSE 0 END) AS win_count, SUM(CASE WHEN entry.value->>'$.result' = 'Loss' THEN 1 ELSE 0 END) AS loss_count, COUNT(*) AS player_count FROM raw, LATERAL json_each(\"ToonPlayerDescMap\") AS entry GROUP BY filename) SELECT SUM(CASE WHEN win_count = 1 AND loss_count = 1 AND player_count = 2 THEN 1 ELSE 0 END) AS valid_1v1_replays, SUM(CASE WHEN win_count != 1 OR loss_count != 1 OR player_count != 2 THEN 1 ELSE 0 END) AS excluded_replays, COUNT(*) AS total_replays FROM valid_replays" --format table

1.12B — Class balance stratified by year and tournament

SELECT
    EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year,
    split_part(filename, '/', -3) AS tournament_dir,
    COUNT(*) AS total_replays,
    SUM(CASE WHEN entry.value->>'$.result' = 'Win' THEN 1 ELSE 0 END) AS win_slots,
    SUM(CASE WHEN entry.value->>'$.result' = 'Loss' THEN 1 ELSE 0 END) AS loss_slots,
    SUM(CASE WHEN entry.value->>'$.result' NOT IN ('Win', 'Loss')
        OR entry.value->>'$.result' IS NULL THEN 1 ELSE 0 END) AS anomalous_slots
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1, 2
ORDER BY 1, 2;

poetry run sc2 db --dataset sc2egset query "<SQL above>" --format csv

1.12C — Feature completeness heatmap (Python)

def plot_field_completeness_heatmap(
    profile_df: pd.DataFrame,
    output_path: Path,
) -> None:
    """Generate a heatmap of field availability rates across years.
    Args:
        profile_df: DataFrame from 01_10_tpdm_availability_by_year.csv
        output_path: Path for the output PNG
    """
    ...

Uses the year-stratified availability data from Step 1.10E to create a (field x year) heatmap where cell color represents the percentage of non-null, non-zero
values.

Artifacts:
- 01_12_class_balance.csv
- 01_12_class_balance_stratified.csv
- 01_12_field_completeness_heatmap.png

Thesis mapping: §4.1.2 — data quality; §4.1.1 — dataset summary statistics

Gate condition:
- Artifact check: All three files exist and are non-empty.
- Continue predicate: If valid_1v1_replays / total_replays > 0.999, continue to Step 1.13. (Threshold source: Step 1.1 established that 13 out of 22,390 replays are anomalous, yielding a 99.94% valid rate. The 99.9% threshold is derived from this empirical baseline — any significant drop below the established rate indicates a regression or a data-processing error introduced between Step 1.1 and Step 1.12.)
- Halt predicate: If valid_1v1_replays / total_replays drops to 0.999 or below, halt Phase 1 and escalate, because the valid replay rate would have degraded significantly relative to the 99.94% baseline established by Step 1.1, indicating that the assumption that SC2EGSet is predominantly a 1v1 tournament dataset (which the entire prediction task definition rests on) may be violated or that a processing error has been introduced.

[CROSS-GAME]


---
Step 1.13 — Bivariate analysis: race, matchup, and result

Context: Manual 01 §4 requires bivariate and multivariate analysis. For the pre-game prediction task, the most important bivariate relationships are between
race/matchup and win rate, stratified by year and tournament to mitigate Simpson's paradox (Manual 01 §7). This step produces the cross-tabulations that Phase 7
 matchup features will depend on. True multivariate stratification (e.g., race x map x era x result interaction) is deferred to Phase 2, where the player appearances table provides the structured player-game grain necessary for multi-factor analysis; Phase 1 operates on raw JSON and covers bivariate cases only. Feeds thesis §4.2 (exploratory analysis).

Inputs: raw table.

Sub-steps:

1.13A — Race distribution (overall and by year)

SELECT
    entry.value->>'$.race' AS race,
    COUNT(*) AS n_slots,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1
ORDER BY 2 DESC;

poetry run sc2 db --dataset sc2egset query "SELECT entry.value->>'$.race' AS race, COUNT(*) AS n_slots, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct FROM raw, LATERAL json_each(\"ToonPlayerDescMap\") AS entry GROUP BY 1 ORDER BY 2 DESC" --format table

Year-stratified:

SELECT
    EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year,
    entry.value->>'$.race' AS race,
    COUNT(*) AS n_slots,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY
        EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP)), 2) AS pct
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
GROUP BY 1, 2
ORDER BY 1, 3 DESC;

poetry run sc2 db --dataset sc2egset query "<SQL above>" --format csv

1.13B — Matchup win rates (overall and by year)

WITH game_pairs AS (
    SELECT
        filename,
        EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year,
        split_part(filename, '/', -3) AS tournament_dir,
        MAX(CASE WHEN entry.value->>'$.result' = 'Win'
            THEN entry.value->>'$.race' END) AS winner_race,
        MAX(CASE WHEN entry.value->>'$.result' = 'Loss'
            THEN entry.value->>'$.race' END) AS loser_race
    FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
    GROUP BY filename, 2, 3
    HAVING COUNT(*) = 2
       AND SUM(CASE WHEN entry.value->>'$.result' = 'Win' THEN 1 ELSE 0 END) = 1
       AND SUM(CASE WHEN entry.value->>'$.result' = 'Loss' THEN 1 ELSE 0 END) = 1
),
matchups AS (
    SELECT *,
        CASE WHEN winner_race <= loser_race
            THEN winner_race || 'v' || loser_race
            ELSE loser_race || 'v' || winner_race
        END AS matchup,
        CASE WHEN winner_race <= loser_race
            THEN winner_race ELSE loser_race
        END AS first_race
    FROM game_pairs
)
SELECT
    matchup, first_race,
    COUNT(*) AS total_games,
    SUM(CASE WHEN winner_race = first_race THEN 1 ELSE 0 END) AS first_race_wins,
    ROUND(100.0 * SUM(CASE WHEN winner_race = first_race THEN 1 ELSE 0 END) / COUNT(*), 1) AS first_race_win_pct
FROM matchups
GROUP BY 1, 2
ORDER BY 1;

poetry run sc2 db --dataset sc2egset query "<SQL above>" --format csv

Year-stratified version: add year to the GROUP BY and SELECT.

1.13C — Race win rate by tournament tier (Simpson's-paradox check)

Same as 1.13B with tournament_dir added to GROUP BY.

Artifacts:
- 01_13_race_distribution.csv
- 01_13_matchup_win_rates.csv
- 01_13_matchup_win_rates_by_year.csv
- 01_13_matchup_win_rates_by_tournament.csv

Thesis mapping: §4.2.1 — race and matchup analysis; §4.3 — balance meta-analysis

Gate condition:
- Artifact check: All four CSV files exist and are non-empty.
- Continue predicate: If all six matchups (TvZ, TvP, ZvP, TvT, ZvZ, PvP) have at least 100 games each and aggregate win rates are between 30% and 70%, continue
to Step 1.14. (Threshold source: Agresti 2002, Categorical Data Analysis — 100 games minimum for stable proportion estimates; 30–70% range reflects competitive
balance.)
- Halt predicate: If any matchup has fewer than 20 games total, halt Phase 1 and escalate, because matchup-stratified feature engineering in Phase 7 would be
unreliable due to insufficient sample size per stratum.

[CROSS-GAME]

---
Step 1.14 — Correlation analysis of numeric ToonPlayerDescMap fields

Context: Manual 01 §4 prescribes bivariate correlation analysis. For numeric fields in ToonPlayerDescMap (APM, SQ, supplyCappedPercent, MMR where available),
pairwise correlations reveal redundancy and potential multicollinearity before feature engineering. This step is observational — no feature selection decisions
are made. Feeds thesis §4.2 (exploratory analysis).

Inputs: raw table. Numeric field list from Step 1.10.

Sub-steps:

1.14A — Extract numeric fields for Spearman correlation (Python)

Spearman is preferred over Pearson because distributions are likely non-normal (Manual 01 §2.1: "Spearman for monotonic relationships"). DuckDB does not have a
built-in SPEARMAN_CORR, so data is extracted and computed in Python via scipy.stats.spearmanr.

SELECT
    (entry.value->>'$.APM')::DOUBLE AS apm,
    (entry.value->>'$.SQ')::DOUBLE AS sq,
    (entry.value->>'$.supplyCappedPercent')::DOUBLE AS supply_capped_pct,
    (entry.value->>'$.MMR')::DOUBLE AS mmr,
    (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0 AS duration_minutes,
    entry.value->>'$.race' AS race,
    entry.value->>'$.result' AS result,
    EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
WHERE (entry.value->>'$.APM')::DOUBLE > 0;

poetry run sc2 db --dataset sc2egset query "SELECT (entry.value->>'$.APM')::DOUBLE AS apm, (entry.value->>'$.SQ')::DOUBLE AS sq, (entry.value->>'$.supplyCappedPercent')::DOUBLE AS supply_capped_pct, (entry.value->>'$.MMR')::DOUBLE AS mmr, (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0 AS duration_minutes, entry.value->>'$.race' AS race, entry.value->>'$.result' AS result, EXTRACT(YEAR FROM (details->>'$.timeUTC')::TIMESTAMP) AS year FROM raw, LATERAL json_each(\"ToonPlayerDescMap\") AS entry WHERE (entry.value->>'$.APM')::DOUBLE > 0" --format csv

1.14B — Pairwise Spearman correlation matrix

def compute_spearman_matrix(
    df: pd.DataFrame,
    numeric_cols: list[str],
) -> pd.DataFrame:
    """Compute pairwise Spearman correlations with p-values.
    Returns DataFrame with columns: var1, var2, rho, p_value, n.
    Uses scipy.stats.spearmanr.
    """
    ...

1.14C — Correlation stratified by race

Same Spearman matrix computed separately for Terran, Protoss, and Zerg, to check whether aggregate correlations mask race-specific patterns.

1.14D — Correlation heatmap (Python, matplotlib)

def plot_correlation_heatmap(
    corr_matrix: pd.DataFrame,
    output_path: Path,
    title: str,
) -> None:
    """Render annotated Spearman correlation heatmap."""
    ...

Artifacts:
- 01_14_spearman_correlations.csv
- 01_14_spearman_by_race.csv
- 01_14_correlation_heatmap.png

Thesis mapping: §4.2.2 — bivariate analysis of pre-game metadata fields

Gate condition:
- Artifact check: All three files exist and are non-empty.
- Continue predicate: If the correlation matrix is computed for all available numeric field pairs, continue to Step 1.15.
- Halt predicate: If any pair of fields that would both be used as features shows |rho| > 0.95, halt Phase 1 and escalate, because near-perfect collinearity
between planned features would make independent feature contribution uninterpretable and violate the thesis requirement for feature importance analysis.
(Threshold source: Dormann et al. 2013, "Collinearity: a review of methods to deal with it" — 0.95 is the escalate level; values between 0.7 and 0.95 are noted
but do not halt.)

[CROSS-GAME]

---
Step 1.15 — Distribution visualizations for numeric fields classified as active (QQ plots, KDE, ECDFs)

Context: Manual 01 §3.4 prescribes histograms, KDE, QQ plots, and ECDFs as the standard distribution analysis toolkit. Step 1.3 produced histograms for game
duration only. This step extends visual distribution analysis to every field from Step 1.10 whose status is "active" (per the Step 1.10D classification) AND whose type is numeric (per the Step 1.10B distribution profiling). The exact field count is determined by Step 1.10's findings; the gate condition is one PNG triplet per qualifying field, no exceptions. Feeds thesis §4.2 (exploratory analysis) and Appendix B (supplementary figures).

Inputs: Numeric field data extracted in Step 1.14A. Field status from Step 1.10D.

Sub-steps:

1.15A — Histograms + KDE, QQ plot, and ECDF per active numeric field

def plot_distribution_panel(
    series: pd.Series,
    field_name: str,
    output_dir: Path,
) -> None:
    """Generate histogram+KDE, QQ plot, and ECDF for a single numeric field.
    Produces three PNG files:
      {output_dir}/01_15_{field_name}_hist_kde.png
      {output_dir}/01_15_{field_name}_qq.png
      {output_dir}/01_15_{field_name}_ecdf.png
    """
    ...

For each field that is both "active" in Step 1.10D's classification AND numeric in Step 1.10B's distribution profiling:
- Histogram with KDE overlay (matplotlib + scipy.stats.gaussian_kde)
- QQ plot against normal distribution (scipy.stats.probplot) — the Manual calls this "the gold standard"
- ECDF (statsmodels ECDF or matplotlib step function)

1.15B — Duration distribution by race

SELECT
    entry.value->>'$.race' AS race,
    (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0 AS duration_minutes
FROM raw, LATERAL json_each("ToonPlayerDescMap") AS entry
WHERE entry.value->>'$.result' = 'Win';

poetry run sc2 db --dataset sc2egset query "SELECT entry.value->>'$.race' AS race, (header->>'$.elapsedGameLoops')::DOUBLE / 22.4 / 60.0 AS duration_minutes FROM raw, LATERAL json_each(\"ToonPlayerDescMap\") AS entry WHERE entry.value->>'$.result' = 'Win'" --format csv

Produces overlaid KDE plots by race.

Artifacts:
- One (hist_kde, qq, ecdf) PNG triplet per field that is both "active" (Step 1.10D) and numeric (Step 1.10B). The exact field list is determined at execution time by Step 1.10's findings.
- 01_15_duration_by_race_kde.png

Thesis mapping: §4.2 — main exploratory figures; Appendix B — supplementary distribution plots

Gate condition:
- Artifact check: One (histogram+KDE, QQ, ECDF) PNG triplet exists for every field that Step 1.10D classifies as "active" AND Step 1.10B confirms as numeric. Zero exceptions. The expected fields include at minimum APM and duration; SQ, supplyCappedPercent, and any additional numeric active fields are included if Step 1.10 classifies them accordingly.
- Continue predicate: If all qualifying fields have complete visualization triplets, continue to Step 1.16.
- Halt predicate: If any active numeric field classified as PRE_GAME in Step 1.11 shows a QQ plot indicating a degenerate distribution (all values identical, or
 bimodal with >90% in one mode), halt Phase 1 and escalate, because a pre-game feature with degenerate distribution would have near-zero predictive value and
its inclusion in the feature set must be reconsidered before Phase 7.

[CROSS-GAME]

---
Step 1.16 — Phase 1 consolidation: data dictionary, data quality report, risk register, modeling readiness decision

Context: Manual 01 §6.1 requires four deliverables before proceeding to modeling phases. This step consolidates all findings from Steps 1.1 through 1.15 into
these four structured artifacts. No new analysis is performed — synthesis only. Feeds thesis §4.1 (dataset description), §3 (methodology), and the Phase 1 gate.

Inputs: All artifacts from Steps 1.1 through 1.15.

Sub-steps:

**Deliverable 1 of 4 — Data dictionary**

Filename: `01_16_data_dictionary.md` (under `src/rts_predict/sc2/reports/sc2egset/`)

Required sections:
1. Overview (one paragraph summarizing the SC2EGSet schema and this dictionary's scope)
2. Top-level columns table (one row per raw table column: filename, header, initData, details, metadata, ToonPlayerDescMap, error flags)
3. ToonPlayerDescMap fields table (one row per field from Step 1.9 inventory, with columns: field name, JSON path, data type, semantic meaning, null/zero rate from Step 1.10, temporal classification from Step 1.11, field status from Step 1.10D)
4. Top-level JSON sub-keys table (one row per sub-key discovered in Step 1.9C for header, initData, details, metadata)

Feeding artifacts: 01_09_tpdm_field_inventory.csv, 01_09_tpdm_key_set_constancy.csv, 01_09_toplevel_field_inventory.csv, 01_10_tpdm_column_profile.csv, 01_10_tpdm_field_status.csv, 01_11_temporal_leakage_classification.csv

Sign-off criterion: Every field enumerated in Step 1.9 (both ToonPlayerDescMap fields and top-level JSON sub-keys) appears in the dictionary with all required columns populated. No field has a blank data type, temporal classification, or field status cell.

def compile_data_dictionary(
    field_inventory: pd.DataFrame,
    column_profiles: pd.DataFrame,
    temporal_classifications: pd.DataFrame,
) -> str:
    """Compile a data dictionary from Phase 1 profiling artifacts.
    Returns markdown string with one section per field containing:
    - Field name and JSON path
    - Data type (inferred from profiling)
    - Semantic meaning (from SC2EGSet documentation)
    - Valid range (from min/max in profiling)
    - Null/zero rate
    - Temporal classification (PRE_GAME / POST_GAME)
    - Field status (dead / constant / near-constant / active)
    - Notes and assumptions
    """
    ...

**Deliverable 2 of 4 — Data quality report**

Filename: `01_16_data_quality_report.md` (under `src/rts_predict/sc2/reports/sc2egset/`)

Required sections:
1. Executive summary (one paragraph with key quality metrics)
2. Missingness summary (per-field null rates, referencing 01_10_tpdm_column_profile.csv)
3. Duplicate inventory (exact and near-duplicate counts, referencing 01_01_duplicate_detection.md)
4. Structural anomaly inventory (13 anomalous replays from Step 1.1, error-flagged replays from Step 1.8)
5. Field status classification counts (dead / constant / near-constant / active breakdown, referencing 01_10_tpdm_field_status.csv)
6. Year-stratified completeness summary (referencing 01_10_tpdm_availability_by_year.csv and 01_12_field_completeness_heatmap.png)
7. Class balance confirmation (referencing 01_12_class_balance.csv)
8. Game settings verification results (referencing 01_game_settings_audit.md from Step 1.8)

Feeding artifacts: 01_01_corpus_summary.json, 01_01_duplicate_detection.md, 01_01_player_count_anomalies.csv, 01_04_apm_mmr_audit.md, 01_game_settings_audit.md, 01_error_flags_audit.csv, 01_10_tpdm_column_profile.csv, 01_10_tpdm_field_status.csv, 01_10_tpdm_availability_by_year.csv, 01_12_class_balance.csv, 01_12_field_completeness_heatmap.png

Sign-off criterion: Every section contains at least one quantified finding traceable to a named source artifact. No section is empty or contains only placeholder text.

**Deliverable 3 of 4 — Risk register**

Filename: `01_16_risk_register.md` (under `src/rts_predict/sc2/reports/sc2egset/`)

Required sections:
1. Overview (one paragraph explaining the register's purpose and severity scale)
2. Risk table (columns: Risk ID, Description, Severity [Critical/High/Medium/Low], Affected Phase, Mitigation, Source Step)
3. AMBIGUOUS fields appendix (one row per field classified as AMBIGUOUS in Step 1.11, with the conservative exclusion rationale from 01_11_temporal_leakage_classification.csv)

Feeding artifacts: 01_01_duplicate_detection.md (near-duplicate risk), 01_01_player_count_anomalies.csv (anomalous replay risk), 01_04_apm_mmr_audit.md (MMR missingness, APM 2016 risk), 01_11_temporal_leakage_classification.csv (temporal leakage risk, AMBIGUOUS field risk), 01_12_class_balance.csv (class balance risk if applicable), 01_error_flags_audit.csv (error flag risk)

Sign-off criterion: At minimum the following risks are documented: (1) temporal leakage from post-game fields (Source: Step 1.11), (2) MMR systematic missingness (Source: Step 1.4), (3) near-duplicate replay pairs (Source: Step 1.1), (4) every AMBIGUOUS field from Step 1.11. Every risk has all six table columns populated.

Seed entries:

| Risk ID | Description | Severity | Affected Phase | Mitigation | Source |
|---------|-------------|----------|----------------|------------|--------|
| R01 | Temporal leakage from post-game fields (APM, SQ, supplyCappedPercent) used as pre-game features | Critical | Phase 7 | Step 1.11 classification; Phase 7 must exclude POST_GAME fields | Step 1.11 |
| R02 | MMR systematic missingness (83.6% zero) | High | Phase 7 | Derive skill from match history (Elo/Glicko-2) | Step 1.4 |
| R03 | 88 near-duplicate replay pairs | Medium | Phase 6 | Deduplication in Phase 6 cleaning | Step 1.1 |
| R04 | 2016 APM all-zero (systematic, not MCAR) | Medium | Phase 7 | Exclude 2016 from APM features or impute | Step 1.4 |
| R05 | 13 replays with player_count != 2 | Low | Phase 6 | Exclusion rule in Phase 6 | Step 1.1 |

**Deliverable 4 of 4 — Modeling readiness decision**

Filename: `01_16_modeling_readiness.md` (under `src/rts_predict/sc2/reports/sc2egset/`)

Required sections:
1. Decision header (GO / NO-GO / CONDITIONAL GO)
2. Gate conditions checklist (explicit reference to each original gate condition (a)-(j) from the ROADMAP, stating whether met, with the artifact or finding that confirms it)
3. Risk assessment summary (reference each risk from the risk register and its mitigation status: mitigated, accepted, or unresolved)
4. Conditions for proceeding (if CONDITIONAL GO: list specific conditions that must be met before Phase 2)
5. Recommended Phase 2 priorities (based on risk register, what should Phase 2 focus on first)

Feeding artifacts: 01_16_data_dictionary.md, 01_16_data_quality_report.md, 01_16_risk_register.md (all three prior deliverables)

Sign-off criterion: The document contains an explicit GO / NO-GO / CONDITIONAL-GO decision. If GO or CONDITIONAL-GO, every original gate condition (a)-(j) is addressed with a pass/fail status and artifact reference. If CONDITIONAL-GO, at least one condition for proceeding is listed with a concrete resolution path. If NO-GO, the specific blocking finding is named.

## Modeling readiness assessment for SC2EGSet

### Decision: [GO / NO-GO / CONDITIONAL GO]

### Justification:
- [Reference each gate condition (a)–(j) from the roadmap]
- [Reference each risk from the risk register and its mitigation status]

### Conditions for proceeding (if CONDITIONAL GO):
- [List any conditions that must be met before Phase 2]

### Recommended Phase 2 priorities:
- [Based on risk register, what should Phase 2 focus on first]

Thesis mapping: §4.1 — dataset description; §4.1.2 — data quality; §3.3 — risk management; §4.1.4 — modeling readiness assessment

Gate condition:
- Artifact check: All four markdown files exist and are non-empty.
- Continue predicate: If 01_16_modeling_readiness.md contains a GO or CONDITIONAL GO decision, continue to Phase 2.
- Halt predicate: If 01_16_modeling_readiness.md contains a NO-GO decision, halt the pipeline and escalate, because the data has been assessed as unfit for the
prediction task and no downstream phase can produce valid results.

[CROSS-GAME]
---
  DELIVERABLE 3 — Revised Phase 1 Gate Definition

The current Phase 1 gate (ROADMAP.md, conditions a–j) lists ten factual statements. The revised gate replaces these with the four Manual 01 §6.1 deliverables as
 the formal closure condition, with existing conditions (a)–(j) subsumed as prerequisites.

Revised Phase 1 closure gate

Phase 1 is complete when ALL of the following named artifacts exist under src/rts_predict/sc2/reports/sc2egset/ and satisfy their stated quality criteria:

1. Data Dictionary — 01_16_data_dictionary.md
- Produced by: Step 1.16A
- Depends on: Steps 1.9, 1.10, 1.11
- Quality criterion: Every field discovered in Step 1.9 has an entry. Every entry includes: field name, JSON path, data type, semantic meaning, valid range,
null/zero rate, temporal classification, field status.

2. Data Quality Report — 01_16_data_quality_report.md
- Produced by: Step 1.16B
- Depends on: Steps 1.1, 1.2, 1.4, 1.8, 1.10, 1.12
- Quality criterion: Report includes the following quantified sections: missingness summary (per-field null rates), duplicate inventory, structural anomaly
inventory, field status classification counts, year-stratified completeness summary, error flag rates, game settings verification results. Every number
traceable to a named artifact from an earlier step.

3. Risk Register — 01_16_risk_register.md
- Produced by: Step 1.16C
- Depends on: Steps 1.1, 1.4, 1.8, 1.11, 1.12, 1.13
- Quality criterion: Every risk has an ID, description, severity, affected phase, mitigation strategy, and source step reference. At minimum: temporal leakage
risk (Step 1.11), MMR missingness risk (Step 1.4), near-duplicate risk (Step 1.1), and all AMBIGUOUS fields from Step 1.11 must be documented.

4. Modeling Readiness Decision — 01_16_modeling_readiness.md
- Produced by: Step 1.16D
- Depends on: Steps 1.16A–C (all other deliverables)
- Quality criterion: Contains an explicit GO / NO-GO / CONDITIONAL-GO decision with narrative justification referencing the risk register and data quality
report. If CONDITIONAL-GO, lists the specific conditions.

Prerequisite artifacts (Steps 1.1–1.15)

| Step | Artifacts |
|------|-----------|
| 1.1 | 01_01_corpus_summary.json, 01_01_player_count_anomalies.csv, 01_01_result_field_audit.md, 01_01_duplicate_detection.md |
| 1.2 | 01_02_parse_quality_by_tournament.csv, 01_02_parse_quality_summary.md |
| 1.3 | 01_03_duration_distribution.csv, 01_03_duration_distribution_full.png, 01_03_duration_distribution_short_tail.png |
| 1.4 | 01_04_apm_mmr_audit.md |
| 1.5 | 01_05_patch_landscape.csv |
| 1.6 | 01_06_event_type_inventory.csv, 01_06_event_count_distribution.csv, 01_06_event_density_by_year.csv, 01_06_event_density_by_tournament.csv |
| 1.7 | 01_07_playerstats_sampling_check.csv |
| 1.8 | 01_game_settings_audit.md, 01_error_flags_audit.csv (note: 01_field_completeness_summary.csv superseded by Step 1.10) |
| 1.9 | 01_09_tpdm_field_inventory.csv, 01_09_tpdm_key_set_constancy.csv, 01_09_toplevel_field_inventory.csv |
| 1.10 | 01_10_tpdm_column_profile.csv, 01_10_tpdm_numeric_distributions.csv, 01_10_tpdm_categorical_topk.csv, 01_10_tpdm_field_status.csv, 01_10_tpdm_availability_by_year.csv |
| 1.11 | 01_11_temporal_leakage_classification.csv, 01_11_leakage_empirical_checks.md |
| 1.12 | 01_12_class_balance.csv, 01_12_class_balance_stratified.csv, 01_12_field_completeness_heatmap.png |
| 1.13 | 01_13_race_distribution.csv, 01_13_matchup_win_rates.csv, 01_13_matchup_win_rates_by_year.csv, 01_13_matchup_win_rates_by_tournament.csv |
| 1.14 | 01_14_spearman_correlations.csv, 01_14_spearman_by_race.csv, 01_14_correlation_heatmap.png |
| 1.15 | One (hist_kde, qq, ecdf) PNG triplet per field that Step 1.10D classifies as "active" AND Step 1.10B confirms as numeric. Zero exceptions. |

Relationship to existing gate conditions (a)–(j)

The existing conditions are subsumed, not replaced:
- (a)–(f): Factual statements derived from Steps 1.1–1.7 artifacts. Remain prerequisites.
- (g)–(j): Factual statements derived from Step 1.8 artifacts. Remain prerequisites.
- New gate adds: temporal leakage classification (Step 1.11), class balance confirmation (Step 1.12), bivariate analysis (Steps 1.13–1.14), distribution
visualizations (Step 1.15), and the four §6.1 consolidation deliverables (Step 1.16).

---
Summary

| Step | Title | Manual § | New Artifacts | CROSS-GAME |
|------|-------|----------|---------------|------------|
| 1.9 | ToonPlayerDescMap field inventory and JSON structure verification | §1, §3.1 (prerequisite) | 3 CSV | Yes |
| 1.10 | Uniform column-level profiling of all TPDM fields | §3.1, §3.3 | 5 CSV | Yes |
| 1.11 | Temporal leakage risk classification for all fields | §5 | 1 CSV, 1 MD | Yes |
| 1.12 | Dataset-level class balance and feature completeness heatmap | §3.2 | 2 CSV, 1 PNG | Yes |
| 1.13 | Bivariate analysis: race, matchup, and result | §4 | 4 CSV | Yes |
| 1.14 | Correlation analysis of numeric TPDM fields | §4 | 2 CSV, 1 PNG | Yes |
| 1.15 | Distribution visualizations (QQ, KDE, ECDF) | §3.4 | 3+ PNG triplets | Yes |
| 1.16 | Phase 1 consolidation (four §6.1 deliverables) | §6.1 | 4 MD | Yes |

Total new artifacts: ~22 CSV/MD files and 12+ PNG files.

Dependency order

1.8 (pending, already defined — sub-steps A–E, G, H only; F and I superseded)
  |
1.9 (field inventory)
  |
1.10 (uniform profiling) ──────► 1.11 (leakage classification)
  |                                        |
1.12 (class balance)                       |
  |                                        |
1.13 (race/matchup bivariate)              |
  |                                        |
1.14 (correlations)                        |
  |                                        |
1.15 (distributions)                       |
  └────────────────────────────────────────┘
                    |
               1.16 (consolidation)

Steps 1.12–1.15 can execute in parallel once Step 1.10 is complete. Step 1.16 depends on all prior steps.
