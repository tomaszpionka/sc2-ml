---
reviewer: reviewer-adversarial
model: claude-opus-4-6
date: 2026-04-15
plan: planning/plan_sc2egset_01_03_01.md
verdict: PROCEED (1 blocker, 4 warnings to address before or during execution)
---

# Adversarial Review — plan_sc2egset_01_03_01.md

## Lens Assessments

- **Temporal discipline:** SOUND — elapsed_game_loops correctly annotated as POST-GAME throughout (T01 ROADMAP YAML, T04 SQL comment, T08 QQ panel title, T10 JSON field_classification). APM, SQ, supplyCappedPercent annotated as IN-GAME. Census field_classification at line 2558-2559 confirms elapsed_game_loops in post_game and in_game is empty for replays_meta_raw struct-flat. The 2026-04-15 reclassification is correctly reflected. No temporal leakage risk in a profiling-only step.
- **Statistical methodology:** AT RISK — The QQ data query (T08) applies a composite WHERE filter that conflates MMR sentinel exclusion with SQ sentinel exclusion, silently restricting APM and supplyCappedPercent distributions to the rated-only subpopulation (see B-01). IQR outlier detection for MMR-all is degenerate (Q1=Q3=0 means IQR=0, fences are both 0, so every MMR>0 row is an "outlier") — the plan acknowledges this but does not propose a guard or alternate interpretation.
- **Feature engineering:** N/A — Profiling only (I9). Out of Scope section explicitly defers cleaning and feature decisions.
- **Thesis defensibility:** ADEQUATE — Near-constant list in T06 is incomplete (see W-01), and the UNPIVOT fallback is speculative (see W-02), but the overall design is defensible. Literature citations (Abedjan 2015, Tukey 1977, D'Agostino & Stephens 1986) are appropriate.
- **Cross-game comparability:** N/A — SC2-only profiling step. The profiling template (column-level stats, cross-table linkage, completeness heatmap) is game-agnostic and will transfer to AoE2 datasets without structural modification.

---

## Blockers

### B-01 — QQ data query silently filters APM/SQ/supplyCappedPercent to rated-only players

**Location:** T08, Cell 21, `sql_queries["qq_data"]` (plan line ~962-969)

**Finding:** The QQ data query applies `WHERE result IN ('Win', 'Loss') AND SQ > {INT32_MIN} AND MMR > 0`. The `MMR > 0` filter is necessary for the MMR QQ plot (rated-only). However, this same filter is applied to the APM, SQ, and supplyCappedPercent columns fetched in the same query. This means the QQ plots for APM, SQ, and supplyCappedPercent show distributions for only ~16.35% of the data (the rated subpopulation), silently discarding 83.65% of rows. The QQ panel titles say "APM [IN-GAME (Inv. #3)]" and "SQ [IN-GAME (Inv. #3), sentinel excluded]" without noting this is the rated-only subset. This is a silent sample bias in the distribution analysis.

**Evidence:** Census field_classification (line 2506-2530) shows 37,489 MMR=0 rows. The QQ data query would return ~7,328 rows (44,817 total - 37,489 MMR=0 - 2 SQ sentinel - unknown Undecided/Tie overlap) instead of ~44,791 (44,817 - 24 Undecided - 2 Tie).

**Required fix:** Split into two queries:
1. `qq_mmr_data`: `SELECT MMR FROM replay_players_raw WHERE result IN ('Win', 'Loss') AND MMR > 0`
2. `qq_ingame_data`: `SELECT APM, SQ, supplyCappedPercent FROM replay_players_raw WHERE result IN ('Win', 'Loss') AND SQ > {INT32_MIN}`

This ensures APM and supplyCappedPercent QQ plots use the full Win/Loss population, SQ excludes only its own sentinel, and MMR excludes only its own sentinel. Panel titles must match the actual filter applied.

**What breaks if ignored:** The QQ plots for APM, SQ, and supplyCappedPercent would depict a biased subpopulation. If cited in the thesis, an examiner could ask "why does your normality assessment only use 16% of the data for in-game features?" and the answer would be "accidental query coupling," which is not defensible.

---

## Warnings

### W-01 — T06 near-constant candidate list is incomplete

**Location:** T06, plan lines 886-890

**Finding:** The plan lists 5 near-constant candidates: playerID (ratio=0.000201), handicap (ratio=0.000045), isInClan (ratio=0.000045), color_a (ratio=0.000045), result (ratio=0.000089). The census flagged_columns (JSON lines 1940-2139) shows 15 near-constant columns in replay_players_raw alone: playerID, userID, isInClan, race, selectedRace, handicap, region, realm, highestLeague, result, startDir, color_a, color_b, color_g, color_r. Plus 5 from replays_meta_raw struct-flat: is_blizzard_map, max_players, is_blizzard_map_init, map_size_x, map_size_y. The plan's enumeration omits 15 of 20 near-constant columns.

**Impact:** Low execution risk — the code should scan profiles programmatically, not rely on the plan's enumeration. But if the executor treats the plan's list as exhaustive and hardcodes it, the JSON artifact will be incomplete. The plan should clarify that T06 logic must derive the list from profile data at runtime, not from the hardcoded candidates.

**Suggested fix:** Add a sentence to T06: "The list above is illustrative, not exhaustive. The detection logic must scan ALL column profiles programmatically and collect every column matching the criteria."

---

### W-02 — UNPIVOT fallback for mixed-type columns is underspecified

**Location:** T03, Cell 7, `sql_queries["rp_null_cardinality"]` (plan lines 501-515) and Open Questions (line 1323-1325)

**Finding:** The UNPIVOT query attempts to unpivot all 25 columns of replay_players_raw into a single `col_val` column. The table has VARCHAR, INTEGER, BIGINT, and BOOLEAN columns (per schema YAML). DuckDB's UNPIVOT coerces all values to a common type (VARCHAR). While this will likely work for NULL counting and COUNT(DISTINCT), the plan says "If UNPIVOT causes type issues across mixed columns, fall back to per-column UNION ALL approach" — this is a runtime gamble. The executor has no concrete fallback SQL to implement.

**Impact:** If UNPIVOT fails, the executor must improvise 25-column UNION ALL SQL mid-execution. This wastes time and risks inconsistency.

**Suggested fix:** Either (a) provide the fallback UNION ALL SQL in the plan, or (b) use the per-column UNION ALL approach from the start (it is more explicit and matches the census approach). Since the numeric profiling (Cell 6) already uses explicit per-column SQL, consistency favors approach (b).

---

### W-03 — IQR outlier detection for MMR-all is degenerate and unreported

**Location:** T03, Cell 9, plan lines 548-582, especially the note at line 578-582

**Finding:** The plan acknowledges that MMR has Q1=Q3=0 for all rows, so IQR=0, making both fences equal to 0. This means every row with MMR > 0 is flagged as an IQR outlier — approximately 7,328 rows (16.35%). The plan says "the IQR outlier count will reflect the zero-dominated distribution" and suggests computing "MMR_rated_only" IQR separately. However, the actual SQL in Cell 9 only computes MMR IQR outliers on all rows (not a rated-only variant). The plan's note says "add a second query with WHERE MMR > 0" but does not provide the SQL.

**Impact:** The JSON artifact will report an MMR IQR outlier count that is misleading (it equals the count of rated players) without a rated-only counterpart for comparison. An examiner reading the profile would see ~7,328 "outliers" for MMR and question the methodology.

**Suggested fix:** Add a second IQR query block in Cell 9 with `WHERE MMR > 0` for the rated-only variant, or explicitly document in the output that IQR is degenerate for MMR-all and report only the rated-only variant.

---

### W-04 — Duplicate detection key changed without justification

**Location:** T05, Cell 14, plan lines 769-781

**Finding:** The plan uses `(filename, toon_id)` as the natural key for duplicate detection. The 01_02_04 census (JSON line 2499-2502) used `(replayId, playerId)` — which the plan acknowledges. However, the `sql-data.md` rule file states: "replay_id is the canonical join key. ALL downstream tables use replay_id as FK to raw. NEVER join on filename or match_id directly." The plan's duplicate detection query uses `filename` directly rather than deriving `replay_id` first.

**Impact:** Functionally, `filename` is a superset of `replay_id` (filename contains the full path, replay_id is the 32-char hex extracted from it), so the dedup result will be identical. But this is a convention break from the SQL rules. More importantly, `toon_id` is not the same as `playerId` — the plan should verify these identify the same entity before claiming the check "confirms the same from a different angle." The schema YAML shows both `toon_id` (VARCHAR) and `playerID` (INTEGER) as separate columns. The census used `playerId` (likely `playerID`), while the plan uses `toon_id`. These are different identity keys — one is global (toon_id), the other is per-replay slot (playerID 1-8).

**Suggested fix:** Either (a) use the same key as the census (`replay_id` derived from filename + `playerID`) for direct comparability, or (b) document explicitly why `(filename, toon_id)` is a stronger/different dedup check and what it tests that the census check did not.

---

## Passed Checks

- **I3 temporal classification — elapsed_game_loops POST-GAME:** Correctly annotated in T01 ROADMAP YAML (line 167), T04 SQL comment (line 635: "elapsed_game_loops (POST-GAME)"), T08 QQ panel title (line 985: "elapsed_game_loops [POST-GAME (Inv. #3)]"), and T10 JSON field_classification (inherited from census). The 2026-04-15 reclassification is fully propagated.
- **I3 — all 25 replay_players_raw columns classified:** Census field_classification (JSON lines 2505-2538) covers all 25 columns: 5 identifier, 16 pre_game, 3 in_game, 1 target. The plan inherits this classification via `FIELD_CLASSIFICATION = census["field_classification"]` (line 279).
- **I3 — replays_meta_raw struct-flat fields classified:** Census (JSON lines 2540-2567) covers all 17 struct-flat fields: 1 identifier, 11 pre_game, 0 in_game, 1 post_game (elapsed_game_loops), 5 constant.
- **I6 — SQL verbatim to artifact:** Plan stores all queries in `sql_queries` dict (T02 Cell 5) and writes them to both JSON (T10) and markdown (T11) artifacts.
- **I7 — IQR fence 1.5:** Cited to Tukey (1977) at plan lines 117 and 578. Manual Section 3.4 references QQ plots; Section 3.3 provides the 0.001 near-constant threshold. All runtime constants derived from census JSON (T02 Cell 4).
- **I7 — near-constant threshold 0.001:** Manual Section 3.3 (line 62) says "a uniqueness ratio below 0.001 is a reasonable starting point." The plan uses this exact threshold.
- **I9 — no cleaning decisions in output:** Out of Scope section (lines 1301-1318) explicitly defers cleaning, feature engineering, and event table profiling.
- **I10 — no absolute paths in filename:** Not directly tested by this step, but cross-table linkage (T05) derives replay_id from filename via regex, which is consistent with sql-data.md rules.
- **DuckDB STRUCT dot-access syntax:** The plan uses `header.elapsedGameLoops`, `metadata.mapName`, `details.gameSpeed`, `initData.gameDescription.maxPlayers` etc. Per the replays_meta_raw schema YAML, the STRUCT types confirm these paths exist. DuckDB supports dot-notation for STRUCT field access. The quoted `header."version"` handles the reserved keyword correctly.
- **Connection pattern:** `conn.fetch_df(sql)` is the correct method — confirmed in `src/rts_predict/common/db.py` line 160 (`DuckDBClient.fetch_df`) and in the 01_02_07 notebook (line 155: `conn.fetch_df(sql_queries["spearman_all"])`). The plan explicitly notes this at line 1361.
- **ROADMAP format:** The plan's T01 uses `### Step 01_03_01 -- Systematic Data Profiling` which matches the existing convention (`### Step XX_XX_XX — Name` at ROADMAP lines 62, 100, 144, etc.). The em-dash vs double-dash inconsistency (existing steps use both `—` and `--`) is cosmetic.
- **No RESERVOIR sampling:** The plan does not use RESERVOIR sampling for QQ plots, addressing the concern that sampling is unnecessary at N=44,817. Data is fetched via full SELECT queries (T08 Cell 21).
- **MMR dual reporting:** The plan provides both MMR-all and MMR_rated_only stats in the numeric profiling SQL (T03 Cell 6, lines 324-374). Census compliance confirmed.
- **SQ sentinel exclusion:** SQ stats computed both including and excluding INT32_MIN sentinel (T03 Cell 6, lines 402-447). SQ IQR uses `FILTER (WHERE SQ > {INT32_MIN})` (line 554).
- **Constant columns gate:** Gate condition asserts exactly 5 constant columns (T12, line 1191). Census flagged_columns confirms 5 constant entries: game_speed, game_speed_init, gameEventsErr, messageEventsErr, trackerEvtsErr (JSON lines 2061-2139).
- **map_aliases_raw columns:** Plan profiles all 4 columns (tournament, foreign_name, english_name, filename) with null counts and cardinality (T04 Cell 12, lines 705-728).

---

## Verdict

**PROCEED** — after fixing B-01 (split QQ data query) and addressing W-01 through W-04 before or during execution.

B-01 is classified as a blocker because it produces silently biased distribution plots that could be cited in the thesis. The fix is a 2-minute query split. W-01 through W-04 are addressable during execution without plan redesign.
