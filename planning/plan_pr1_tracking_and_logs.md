---
category: D
branch: fix/retroactive-tracking-and-logs
date: 2026-04-16
planner_model: claude-opus-4-6
dataset: all
phase: "01"
pipeline_section: null
invariants_touched: [9]
source_artifacts:
  - planning/fixes_and_next_steps.md
  - src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json
critique_required: false
research_log_ref: null
---

# Plan: Retroactive tracking and research log corrections (PR 1/3)

## Scope

Fix stale PIPELINE_SECTION_STATUS.yaml files, research log contradictions,
cross-reference gaps, and KDE omission justification across all three datasets.
All items are text edits to completed-step artifacts -- no notebook re-runs,
no data queries, no new analysis. Covers items R01-R05 and 1D from
`planning/fixes_and_next_steps.md`.

> **[Critique fix: R07 cross-PR]** R07 (stale elapsed_game_loops claim)
> removed from PR1 scope. PR2 re-executes the sc2egset profiling notebook,
> which regenerates the MD from the .py source -- any MD-only edit made by
> PR1 would be overwritten. R07 is now handled by PR2 (T00), which fixes
> the .py source directly. See `planning/plan_pr2_sc2egset_profile_gaps.md`.

## Out of scope

- Notebook modifications (PR 2: sc2egset; PR 3: aoe2companion/aoestats)
- PHASE_STATUS.yaml changes (all three correctly show Phase 01 in_progress)
- STEP_STATUS.yaml changes (all steps already correctly marked complete)
- Any new data exploration or analysis
- R07 elapsed_game_loops stale text fix (moved to PR2 -- see note above)

## Execution Steps

### T01 -- R01: Update PIPELINE_SECTION_STATUS.yaml (all 3 datasets)

**Objective:** Correct the stale `in_progress` status for pipeline sections
01_02 and 01_03 in all three datasets.

**Instructions:**

1. In each of the three PIPELINE_SECTION_STATUS.yaml files, change:
   - `01_02` status from `in_progress` to `complete`
   - `01_03` status from `in_progress` to `complete`

2. Verify all three PHASE_STATUS.yaml files correctly show Phase 01 as
   `in_progress` (no change needed -- 01_04 through 01_06 are not_started).

**Verification:**
- `grep 'status:' <file>` shows `complete` for 01_01, 01_02, 01_03 and
  `not_started` for 01_04, 01_05, 01_06.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/PIPELINE_SECTION_STATUS.yaml`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/PIPELINE_SECTION_STATUS.yaml`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/PIPELINE_SECTION_STATUS.yaml`

---

### T02 -- R02: Fix aoe2companion research log duplicate contradiction [BLOCKER]

**Objective:** Rewrite the 01_03_01 entry so the duplicate section matches
the profile JSON artifact. Current text (line 35) says:
```
- **Primary key integrity (matchId, profileId):** No duplicates — primary key is clean.
```

The profile JSON shows `dup_groups: 3589428, total_dup_rows: 12401433`.

**Instructions:**

1. Replace line 35 with:
   ```
   - **Primary key integrity (matchId, profileId):** Duplicates confirmed. 3,589,428 duplicate (matchId, profileId) groups containing 12,401,433 total rows (4.47% of 277M). Deduplication required in 01_04.
   ```

2. After the "### Critical findings" section (line 39), add before the next
   subsection:
   ```

   ### Duplicate metric reconciliation

   Two steps measured the same duplication phenomenon with different counting methods:
   - **01_02_04 census:** 8,812,005 excess rows = total_rows (277,099,059) minus distinct (matchId, profileId) pairs (268,287,054). Counts only the surplus beyond the first occurrence.
   - **01_03_01 profile:** 12,401,433 rows in 3,589,428 groups with count > 1. Counts all rows in any group that has duplicates, including the first occurrence.
   Both metrics are correct; the 01_03_01 count is strictly larger because it includes the "keeper" row in each group. The actionable number for 01_04 deduplication is 8,812,005 rows to remove (retaining one row per group).
   ```

**Verification:**
- `grep "No duplicates" <file>` returns zero matches.
- `grep "3,589,428" <file>` returns at least one match.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md`

---

### T03 -- R03: Fix aoestats research log `mirror` I3 contradiction

**Objective:** Remove `mirror` from the "Safe pre-game features" list in the
aoestats 01_02_04 research log entry.

**Instructions:**

1. Find the safe pre-game features line (currently contains `, \`mirror\`,`):
   ```
   **Safe pre-game features:** `map`, `started_timestamp`, `num_players`, `avg_elo`, `team_0_elo`, `team_1_elo`, `leaderboard`, `patch`, `raw_match_type`, `mirror`, `starting_age` (matches_raw); `team`, `civ`, `old_rating` (players_raw)
   ```
   Replace with (remove `mirror`):
   ```
   **Safe pre-game features:** `map`, `started_timestamp`, `num_players`, `avg_elo`, `team_0_elo`, `team_1_elo`, `leaderboard`, `patch`, `raw_match_type`, `starting_age` (matches_raw); `team`, `civ`, `old_rating` (players_raw)

   > **[Retroactive correction 2026-04-16]:** `mirror` removed from safe pre-game list. Reclassified POST-GAME in 01_03_01 -- same-civ determination requires both players' civ selections, which are finalized only at match start.
   ```

**Verification:**
- The safe pre-game features line no longer contains `mirror`.
- Grep for "Retroactive correction" returns at least one match.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md`

---

### T04 -- R04: Standardize aoe2companion rating deferral destination

**Objective:** Standardize all rating ambiguity deferral references to 01_04.

**Instructions:**

In `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md`,
apply the following replacements (search for exact strings):

1. Find `| rating | AMBIGUOUS | Deferred to Phase 02` and replace
   `Phase 02` with `01_04` in that table cell.

2. Find `**rating temporal status -- deferred to Phase 02:**` and replace
   `Phase 02` with `01_04`.

3. Find `rating` temporal classification (ambiguous_pre_or_post) resolution
   deferred to Phase 02` and replace `Phase 02` with `01_04`.

4. Find `matches_raw.rating` flagged as ambiguous; resolution deferred to
   Phase 02` and replace `Phase 02` with `01_04`.

5. In the 01_03_01 entry (line 31), after the existing text
   `Resolution deferred to 01_04.`, append:
   `**[Note]:** Rating ambiguity resolution is assigned to 01_04 (Data Cleaning), not Phase 02 -- the temporal join with ratings_raw is a data investigation prerequisite, not a feature engineering decision.`

**Verification:**
- `grep "deferred to Phase 02" <file>` returns zero matches in
  rating-related contexts.
- `grep "deferred to 01_04" <file>` returns at least 4 matches.

**File scope:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md`

---

### T05 -- R05: Add isInClan cross-reference to sc2egset research log

**Objective:** Cross-reference the 01_02_06 chi-square finding back to the
01_02_04 open question about isInClan/clanTag win-rate signal.

**Instructions:**

1. In `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md`,
   find the open question:
   ```
   - Do isInClan and clanTag carry win-rate signal beyond player identity? (Phase 02)
   ```
   Replace with:
   ```
   - Do isInClan and clanTag carry win-rate signal beyond player identity? **Partially resolved in 01_02_06:** isInClan chi-square = 7.75, p=0.0054, small effect -- clan membership is a very weak proxy for engagement. Full clanTag signal analysis (257 distinct tags) deferred to Phase 02.
   ```

**Verification:**
- Grep for "Partially resolved in 01_02_06" returns at least one match.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md`

---

### T06 -- 1D: Add KDE omission justification to all 3 profile MDs

**Objective:** Add a documented justification for omitting KDE from
distribution analysis per Manual Section 3.4.

**Instructions:**

Add the following text to each profile MD, after the plot index / artifact
index table:

Dataset-specific justifications:
- sc2egset: `**Distribution methods applied:** Histograms (01_02_05), QQ plots, ECDFs. KDE omitted: histograms and QQ plots provide equivalent shape assessment for these distributions; KDE adds smoothing artifacts on discrete integer columns (MMR, APM, SQ) and bounded distributions (supplyCappedPercent). QQ plots are the stronger diagnostic tool per Tukey (1977).`
- aoe2companion: `**Distribution methods applied:** Histograms (01_02_05), QQ plots, ECDFs. KDE omitted: histograms and QQ plots provide equivalent shape assessment for these distributions; KDE adds smoothing artifacts on discrete integer columns (rating) and bounded/near-constant distributions (population, speedFactor). QQ plots are the stronger diagnostic tool per Tukey (1977).`
- aoestats: `**Distribution methods applied:** Histograms (01_02_05), QQ plots, ECDFs. KDE omitted: histograms and QQ plots provide equivalent shape assessment for these distributions; KDE adds smoothing artifacts on discrete integer columns (old_rating, new_rating, match_rating_diff) and bounded distributions (age uptimes). QQ plots are the stronger diagnostic tool per Tukey (1977).`

> **Note:** For sc2egset, this text will be overwritten when PR2 re-executes
> the notebook. The PR2 executor must ensure this justification is also
> present in the notebook .py source's MD template. If PR1 executes before
> PR2, the sc2egset KDE text is a temporary placeholder.

**Verification:**
- `grep "KDE omitted" <file>` returns exactly 1 match per file (3 total).

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md`

---

## File Manifest

| File | Action | Task |
|------|--------|------|
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/PIPELINE_SECTION_STATUS.yaml` | Update | T01 |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/PIPELINE_SECTION_STATUS.yaml` | Update | T01 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/PIPELINE_SECTION_STATUS.yaml` | Update | T01 |
| `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md` | Update | T02, T04 |
| `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md` | Update | T03 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` | Update | T05 |
| `src/.../sc2egset/.../01_03_01_systematic_profile.md` | Update | T06 |
| `src/.../aoe2companion/.../01_03_01_systematic_profile.md` | Update | T06 |
| `src/.../aoestats/.../01_03_01_systematic_profile.md` | Update | T06 |

## Gate Condition

- All three PIPELINE_SECTION_STATUS.yaml files show 01_02 and 01_03 as `complete`.
- All three PHASE_STATUS.yaml files remain unchanged (Phase 01 = `in_progress`).
- No occurrence of "No duplicates" in aoe2companion research log 01_03_01 entry.
- No occurrence of `mirror` in the aoestats safe pre-game features line.
- No "deferred to Phase 02" in aoe2companion research log rating-related lines.
- All three profile MDs contain a KDE omission justification.
- No notebooks modified. No new data queries executed.
