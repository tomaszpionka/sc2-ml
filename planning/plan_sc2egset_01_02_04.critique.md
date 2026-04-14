# Adversarial Critique — sc2egset Step 01_02_04
Date: 2026-04-14
Plan: planning/plan_sc2egset_01_02_04.md
Reviewer: reviewer-adversarial

## Verdict
PASS WITH CONDITIONS

## Critical Issues (must fix before execution)

1. **T02 instruction to backfill 01_02_03 in STEP_STATUS.yaml is stale and will cause executor confusion.**
   The plan states: "STEP_STATUS.yaml currently lists steps through 01_02_02 only — step 01_02_03 is defined in the ROADMAP and has a research log entry dated 2026-04-14, but was never added to STEP_STATUS.yaml." However, `STEP_STATUS.yaml` already contains:

   ```yaml
   "01_02_03":
     name: "Raw Schema DESCRIBE"
     pipeline_section: "01_02"
     status: complete
     completed_at: "2026-04-14"
   ```

   The `if not already present` clause in T02 should protect against duplication, but the prose framing is factually wrong as of disk state. An executor who trusts the plan's description of current state may waste time investigating a discrepancy that does not exist.

   **Fix:** Remove the incorrect assertion. Replace with: "Verify 01_02_03 is listed in STEP_STATUS.yaml (it should already be present as complete). Then add 01_02_04."

## Significant Concerns (should address)

1. **The plan pulls result-distinct-value analysis and NULL census from 01_03 (Systematic Data Profiling) into 01_02 without documenting the scope transfer.**
   The 01_02_03 research log explicitly defers "Full NULL profile for all 25 replay_players_raw columns" and "Distinct values for result column" to "01_03 (systematic profiling)." The 01_02_04 plan now claims these under pipeline section 01_02. This is methodologically defensible — the EDA manual Section 2.1 covers univariate analysis and NULL censusing is a natural EDA activity — but without acknowledging the scope adjustment, a future reader comparing the research log entries will see a contradiction. The plan's "Out of Scope" section defers "Full Section 3.1/3.2 profiling" to 01_03, which partially mitigates this, but the NULL census (Section B) is clearly 3.1 work, and the plan itself cites "Manual Section 3.1" for it. Either add an explicit note to the plan ("scope adjusted forward from prior 01_03 deferral") or document it in the T02 research log template.

2. **`replays_meta_raw.filename` is nullable (YES) per DESCRIBE, but the plan does not account for NULL filenames in Section A STRUCT extraction.**
   The DESCRIBE output shows `"null": "YES"` for `replays_meta_raw.filename`, while `replay_players_raw.filename` is `"null": "NO"`. The Section A SQL includes `filename` in the SELECT without any NULL filter. If any `filename` is NULL in `replays_meta_raw`, subsequent cross-table joins would silently lose rows. The 01_02_02 research log records "zero NULLs across all 6 checked columns" for `replays_meta_raw`, so this is likely a DuckDB nullable-metadata artifact rather than actual NULLs — but the plan should either include `filename` in the Section B NULL census for `replays_meta_raw`, or add an explicit note that the nullable=YES flag is a DuckDB metadata property and empirically zero NULLs exist per 01_02_02 findings.

3. **Section H dead/constant/near-constant detection defines "uniqueness ratio" without specifying denominator.**
   Plan says "uniqueness ratio < 0.001" but does not define whether the ratio is `n_distinct / n_total` or `n_distinct / n_non_null`. For a column with 95% NULLs and 3 distinct non-NULL values among 44,817 rows, these give very different results: 3/44817 = 0.00007 (flagged) vs 3/2241 = 0.001 (borderline). The EDA manual Section 3.3 does not define the denominator either. The executor needs this clarified, or the gate for Section H is ambiguous.

4. **APM and SQ are post-game summary statistics, not pre-game features — the plan does not flag this distinction.**
   APM, SQ, and supplyCappedPercent are computed from in-game actions and are available only in the replay — they are post-hoc summaries of game performance, not pre-game features. The plan's scientific rationale says this step answers whether fields "support outcome prediction." An examiner will ask: "You profiled APM/SQ alongside MMR, but MMR is available before the game and APM is not. Did you distinguish pre-game from in-game features during EDA?" The plan should document that these are flagged as in-game-only fields for the pre-game/in-game boundary (Invariant #5 context), not that their presence implies they will become pre-game features. The "Out of Scope" section does not mention this distinction.

5. **No explicit handling of the 11 non-2-player replays in the target variable analysis.**
   The 01_02_02 research log documents "11 total non-2-player replays" (3 with 1 player, 2 with 4, etc.). Section C (target variable analysis) computes result distribution over ALL rows in `replay_players_raw` without filtering. This is correct for a first-pass EDA census, but the plan should set the expectation that the 11 non-2-player replays will contribute anomalous rows (potentially unusual result values). These are known anomalies from 01_02_02, not new discoveries — the research log template in T02 should acknowledge them.

## Minor Notes

- **The 22.4 game-loops-per-second constant (plan line ~176) is correctly derived** (16 base loops/second at Normal speed × Faster multiplier ≈ 1.4). However, the plan cites the multiplier as "5734/4096" — Liquipedia presents this as approximately 7/5 or 1.4, not as the exact fraction 5734/4096. The plan should either cite a source for the exact ratio 5734/4096 or use 7/5 (= 1.4) with a note that 22.4 = 16 × 1.4 exactly.

- **Section D assertion correctly gates Section E on all replays being Faster speed.** This is well-designed. If the assertion fails, the plan correctly halts. No methodology flaw identified in this gate logic.

- **The plan appropriately defers `gameOptions` sub-fields to 01_04 (cleaning)** and documents this in T02. The deferred fields include potential filters for non-competitive replays (`competitive`, `observers`, `practice`, `randomRaces`). This is reasonable scope management.

- **No visualization (histograms, boxplots) is included.** The "Out of Scope" section explicitly defers this. For a Tukey-style EDA step, the absence of any visual exploration is methodologically unusual — Tukey's philosophy emphasises graphical display as primary. However, the plan explicitly positions this as a "univariate census layer," not a full Tukey-style EDA pass, and defers visualization to a subsequent step. This is acceptable as a conscious scope decision, not an oversight.

## Schema Verification

| Plan SQL Reference | Actual Schema | Match? | Notes |
|---|---|---|---|
| `details.gameSpeed` (VARCHAR) | `STRUCT(gameSpeed VARCHAR, ...)` in `replays_meta_raw` | YES | |
| `details.isBlizzardMap` (BOOLEAN) | `STRUCT(...isBlizzardMap BOOLEAN...)` | YES | |
| `details.timeUTC` (VARCHAR) | `STRUCT(...timeUTC VARCHAR)` | YES | |
| `header.elapsedGameLoops` (BIGINT) | `STRUCT(elapsedGameLoops BIGINT, ...)` | YES | |
| `header."version"` (VARCHAR) | `STRUCT(...\"version\" VARCHAR)` | YES | Plan correctly notes quoting requirement |
| `metadata.baseBuild` (VARCHAR) | `STRUCT(baseBuild VARCHAR, ...)` | YES | |
| `metadata.dataBuild` (VARCHAR) | `STRUCT(...dataBuild VARCHAR...)` | YES | |
| `metadata.gameVersion` (VARCHAR) | `STRUCT(...gameVersion VARCHAR...)` | YES | |
| `metadata.mapName` (VARCHAR) | `STRUCT(...mapName VARCHAR)` | YES | |
| `initData.gameDescription.maxPlayers` (BIGINT) | Deep STRUCT path confirmed | YES | |
| `initData.gameDescription.gameSpeed` (VARCHAR) | Confirmed | YES | |
| `initData.gameDescription.isBlizzardMap` (BOOLEAN) | Confirmed | YES | |
| `initData.gameDescription.mapSizeX` (BIGINT) | Confirmed | YES | |
| `initData.gameDescription.mapSizeY` (BIGINT) | Confirmed | YES | |
| `gameEventsErr` (BOOLEAN) | Top-level column in `replays_meta_raw` | YES | |
| `messageEventsErr` (BOOLEAN) | Top-level column | YES | |
| `trackerEvtsErr` (BOOLEAN) | Top-level column — note asymmetric naming (no 'n') | YES | |
| All 25 columns in `replay_players_raw` | DESCRIBE JSON lists exactly 25 | YES | All names match |

**All SQL field references in the plan match the actual schema.** No schema mismatches identified.

## Gate Condition Assessment

| # | Gate Condition | Assessment | Reasoning |
|---|---|---|---|
| 1 | JSON artifact exists and is valid JSON | VERIFIABLE | File existence + `json.loads()` check |
| 2 | Markdown contains inline SQL for every reported result | WEAK | "Every reported result" is subjective. Suggest specifying minimum count: "at least 8 SQL blocks corresponding to Sections A–H." |
| 3 | JSON contains NULL counts for all 25 columns, result distribution, temporal range, error counts, descriptive stats for MMR/APM/elapsed_game_loops | VERIFIABLE | Specific field names checkable in JSON structure |
| 4 | At least 3 extracted STRUCT fields have non-NULL rate > 0% | VERIFIABLE | Guards against wrong STRUCT paths, but "non-NULL rate > 0%" is trivially satisfied by a single non-NULL value. Catches total extraction failure, not partial failure. |
| 5 | STEP_STATUS.yaml lists 01_02_04 as complete | VERIFIABLE | Direct YAML check |
| 6 | Research log has entry with gameOptions deferral | VERIFIABLE | Grep for "gameOptions" in entry |
| 7 | ROADMAP has 01_02_04 block with predecessors: [01_02_03] | VERIFIABLE | YAML parsing within markdown |
| 8 | No fabricated numbers | UNTESTABLE | Requires human judgment — cannot be automated. A process norm, not a gate condition. |

## Lens Assessments

**Temporal discipline: SOUND.** This is a univariate profiling step. No features are computed, no rolling aggregates are created, no prediction targets are assembled. The temporal range finding correctly limits itself to MIN/MAX of a string column. Invariant #3 is not at risk.

**Statistical methodology: N/A.** No statistical tests, no model evaluation, no cross-game comparison. This is pre-statistical EDA.

**Feature engineering: N/A.** No features are constructed. However, Significant Concern #4 above notes that the plan does not distinguish pre-game fields (MMR, race, highestLeague) from in-game fields (APM, SQ, supplyCappedPercent) during profiling. The research log entry should document this distinction for downstream feature engineering.

**Thesis defensibility: ADEQUATE.** The plan is thorough for its scope. The main defensibility risk is the pre-game/in-game boundary not being flagged (Significant Concern #4). An examiner who reads the EDA artifacts and sees APM profiled alongside MMR without annotation may conclude the author did not understand the distinction until later.

**Cross-game comparability: N/A.** SC2-only step. The plan does not create SC2-specific assumptions that would break AoE2 comparability. The field categories being profiled (skill rating, race/faction, game duration, map) have natural AoE2 analogs.

## Recommendation

The plan is methodologically sound for a univariate EDA census step. The single critical issue (stale T02 instruction about STEP_STATUS.yaml) is a factual error that must be corrected to avoid executor confusion — not a methodology flaw, but a plan accuracy flaw. The significant concerns should be addressed before execution: correct T02 prose about STEP_STATUS state; add a note about `replays_meta_raw.filename` nullable status; define "uniqueness ratio" denominator in Section H; add a sentence distinguishing pre-game from in-game fields in the T02 research log template; note the 11 non-2-player replays as known anomalies in Section C expectations. None of these block execution, but addressing them will save a correction cycle afterward.
