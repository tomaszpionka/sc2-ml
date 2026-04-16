# Adversarial Gate Review — Fixes & Next Steps

Date: 2026-04-16
Scope: 01_02 (EDA) and 01_03 (Systematic Data Profiling) completeness across all three datasets
Reviewers: 3x reviewer-adversarial (Opus), one per dataset
Cross-dataset verdict: **PROCEED WITH CONDITIONS**

Rule: ALL retroactive fixes must be completed before any forward-looking 01_04
planning begins. The retroactive fixes correct artifacts from completed steps
that would otherwise poison downstream work.

---

## Part 1 — Retroactive Fixes (completed step artifacts)

These items correct errors, contradictions, or gaps in artifacts produced by
already-completed steps (01_02_01–01_02_07, 01_03_01). They must be applied
to the existing artifacts on disk — not deferred to future steps.

### 1A. Tracking file corrections [Category C chore]

#### R01. PIPELINE_SECTION_STATUS.yaml stale (all 3 datasets)

All three files show `01_02: in_progress` and `01_03: in_progress` despite
STEP_STATUS showing all steps complete. The derivation chain
(`STEP_STATUS -> PIPELINE_SECTION_STATUS -> PHASE_STATUS`) is broken.

**Action:** Update all three files to `01_02: complete` and `01_03: complete`.
Also verify PHASE_STATUS.yaml is consistent.

**Files to edit:**
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/PIPELINE_SECTION_STATUS.yaml`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/PIPELINE_SECTION_STATUS.yaml`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/PIPELINE_SECTION_STATUS.yaml`

---

### 1B. Research log corrections [Category D fix]

#### R02. aoe2companion: research log contradicts its own artifact on duplicates [BLOCKER]

The 01_03_01 research log entry states:
> **Primary key integrity (matchId, profileId):** No duplicates -- primary key is clean.

The profile JSON from the same step shows:
```json
"duplicate_detection": {
    "has_duplicates": true,
    "dup_groups": 3589428,
    "total_dup_rows": 12401433
}
```

This is an Invariant #9 violation. A 01_04 planner reading the research log
would skip deduplication entirely.

**Action:** Rewrite the research log 01_03_01 duplicate section to match the
artifact. Add a reconciliation note explaining the two different duplicate
metrics across steps:
- 01_02_04 census: 8,812,005 = total_rows - distinct_pairs (excess rows)
- 01_03_01 profile: 12,401,433 = all rows in groups with count > 1 (includes first occurrence)
Both measure the same phenomenon; the 01_03_01 count is strictly larger.

**File:** `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md`

#### R03. aoestats: `mirror` I3 classification contradiction [WARNING]

01_02_04 research log (line 362) lists `mirror` under "Safe pre-game features."
01_03_01 profile classifies it as POST-GAME. These directly contradict.

POST-GAME is the more defensible classification: whether a matchup is a mirror
(same civ both sides) is only knowable after both players lock civ choices.
In ranked queue with pre-selected civs it could be argued pre-game, but the
conservative classification is POST-GAME.

**Action:** Update the 01_02_04 research log entry to remove `mirror` from
the "Safe pre-game features" list. Add a note: "mirror reclassified POST-GAME
in 01_03_01 — same-civ determination requires both players' selections."

**File:** `src/rts_predict/games/aoe2/datasets/aoestats/reports/research_log.md`

#### R04. aoe2companion: rating deferral destination inconsistent [WARNING]

The rating ambiguity resolution is deferred to three different destinations:
- 01_02_07 research log: "deferred to Phase 02"
- 01_02_06 research log: "Phase 02 row-level verification"
- 01_03_01 research log: "Resolution deferred to 01_04"

**Action:** Standardize to "01_04" (Data Cleaning). The temporal join with
ratings_raw is a data investigation that must happen before feature engineering.
Add a clarification note to the 01_03_01 entry: "Rating ambiguity resolution
assigned to 01_04, not Phase 02 — the temporal join is a data investigation
prerequisite, not a feature engineering decision."

**File:** `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md`

#### R05. sc2egset: isInClan open question partially answered but not cross-referenced [WARNING]

01_02_04 research log asks "Do isInClan and clanTag carry win-rate signal?"
and defers to Phase 02. However, 01_02_06 already tested isInClan with
chi-square (p=0.0054, small effect) — partially answering the question.
The 01_02_04 open question was never updated with this cross-reference.

**Action:** Add a note to the 01_02_04 research log open questions section:
"Partially resolved in 01_02_06: isInClan chi-square p=0.0054, small effect.
Full clanTag signal analysis deferred to Phase 02."

**File:** `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md`

---

### 1C. Profile artifact corrections (01_03_01) [Category D fix]

These require updating the 01_03_01 notebook, re-executing it, and verifying
the updated artifacts. Group as a single fix PR per dataset.

#### R06. aoestats: I3 table missing 2 columns [WARNING]

The I3 classification table in `01_03_01_systematic_profile.md` has 30 rows.
Missing: `filename` and `game_id` from matches_raw (both classified IDENTIFIER
in the profile JSON but absent from the MD table and completeness_matrix).
The research log claims "All 32 columns annotated" — inaccurate.

**Action:** Add `filename` (IDENTIFIER) and `game_id` (IDENTIFIER) to the
markdown I3 table and completeness_matrix array in the profile JSON.
Update the research log count claim.

**Files:**
- `sandbox/aoe2/aoestats/01_exploration/03_profiling/01_03_01_systematic_profiling.py`
- Re-execute to regenerate `.md` and `.json` artifacts

#### R07. sc2egset: stale elapsed_game_loops reclassification claim [NOTE]

01_03_01 MD (line 12) states "The census artifact (01_02_04) still shows it
as `in_game`" — but the census JSON already has it in `post_game`. This
creates a misleading correction narrative.

**Action:** Update the MD text to: "elapsed_game_loops classified POST-GAME,
consistent with the census artifact."

**File:** `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md`

#### R08. sc2egset: sentinel summary incomplete in profile JSON [WARNING]

Profile documents only 2 sentinel patterns (MMR=0, SQ=INT32_MIN). Five
additional sentinel-like patterns known from 01_02_04 are not in the formal
profiling artifact:

| Pattern | Count | % | Source |
|---------|-------|---|--------|
| APM=0 | 1,132 | 2.53% | 01_02_04: "very short games or parse artifacts" |
| MMR<0 (min=-36,400) | unknown | unknown | 01_02_04: "may represent another sentinel convention" |
| map_size_x=0, map_size_y=0 | 273 | 1.22% of replays | 01_02_04: open question |
| handicap=0 | 2 | 0.0045% | 01_02_04: "dead column, only 2 rows at 0" |
| selectedRace="" (empty string) | 1,110 | 2.48% | 01_02_04: "Random resolved post-game" |

**Action:** Add these 5 patterns to the `sentinel_summary` section of the
01_03_01 notebook. Re-execute to update the profile JSON and MD. For MMR<0,
compute the actual count dynamically in the notebook.

**Files:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`
- Re-execute to regenerate `.json` and `.md` artifacts

#### R09. sc2egset: temporal coverage absent from profile JSON [WARNING]

Manual §3.2 requires "temporal coverage (date range, gaps)" as a dataset-level
metric. The `time_utc` field is profiled for null_count and cardinality but
no min/max date or gap analysis appears in the profile JSON or MD.

**Action:** Add a `temporal_coverage` section to the profile JSON containing
min/max `time_utc`, distinct month count, and any gaps. Add corresponding
summary to the MD.

**Files:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`
- Re-execute to regenerate artifacts

#### R10. aoe2companion: temporal coverage absent from profile JSON [WARNING]

Same gap as R09. The date range exists in 01_01_01 (file inventory: 2020-08
to 2026-04) but the definitive profiling artifact does not include it.

**Action:** Add a `temporal_coverage` section from `matches_raw.started`
(min/max, distinct month count).

**Files:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py`
- Re-execute to regenerate artifacts

#### R11. aoe2companion: near-constant 50/55 needs stratification [WARNING]

The uniqueness_ratio < 0.001 threshold flags 50 of 55 columns as near-constant,
including the target variable `won`, `civ` (68 distinct), `map` (261 distinct).
At 277M rows, any column with fewer than 277K distinct values is flagged. This
is mechanically correct but produces a classification with no discriminative
power (91% of columns flagged).

**Action:** Add a `near_constant_stratification` sub-section to the profile
JSON that separates:
- **Genuinely uninformative** (IQR=0 or >95% single value): speedFactor,
  population, treatyLength, etc.
- **Low-cardinality categorical** (meaningful variation despite small
  uniqueness ratio): civ, map, leaderboard, won, etc.

This can be computed from existing profile data (IQR and top-k) without new
SQL queries.

**Files:**
- `sandbox/aoe2/aoe2companion/01_exploration/03_profiling/01_03_01_systematic_profiling.py`
- Re-execute to regenerate artifacts

#### R12. aoe2companion: profiles_raw 7 dead columns not in systematic profile [NOTE]

01_02_04 found 7 completely dead columns in profiles_raw (100% NULL). 01_03_01
profiles only matches_raw, so it reports "Dead fields (0): None" — technically
correct for its scope but misleading as a dataset-level statement. The 01_03_01
profile is positioned as the definitive consolidation of all prior EDA findings.

**Action:** Add a `cross_table_notes` section to the profile JSON referencing
the profiles_raw dead columns finding from 01_02_04:
"profiles_raw: 7 dead columns (100% NULL) confirmed in 01_02_04 census —
sharedHistory, twitchChannel, youtubeChannel, youtubeChannelName, discordId,
discordName, discordInvitation. Not re-profiled here (matches_raw scope)."

**File:** Update the notebook to add this note to the JSON output.

#### R13. sc2egset: startLocX/startLocY are VARCHAR containing numeric values [NOTE]

These coordinate columns are stored as INTEGER per the schema YAML but no
format analysis or type-correctness check was performed in 01_03_01 profiling.
If they contain non-numeric values, 01_04 will need a type correction step.

**Action:** Add a verification cell to the notebook confirming these columns
contain only valid integers, or flag any anomalous values.

**File:** `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_01_systematic_profiling.py`

---

### 1D. Missing KDE justification (all 3 datasets) [NOTE]

Manual §3.4 lists four distribution analysis methods: histograms, KDE, QQ
plots, ECDFs. QQ and ECDF are present in all three 01_03_01 profiles.
Histograms were produced in 01_02_05. KDE is absent from all steps.

**Action:** Add a documented justification to each 01_03_01 profile MD:
"KDE omitted: histograms (01_02_05) and QQ plots provide equivalent shape
assessment for these distributions. KDE adds smoothing artifacts on discrete
integer columns (MMR, APM, SQ) and bounded distributions (supplyCappedPercent).
QQ plots are the stronger diagnostic tool per Tukey (1977)."

This does NOT require re-running notebooks — it is a one-line addition to
each MD artifact.

**Files:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md`
- `src/rts_predict/games/aoe2/datasets/aoestats/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.md`

---

### 1E. Retroactive fix summary

| ID | Dataset | Type | Requires notebook re-run? |
|----|---------|------|--------------------------|
| R01 | all | tracking YAML | no |
| R02 | aoe2companion | research log | no |
| R03 | aoestats | research log | no |
| R04 | aoe2companion | research log | no |
| R05 | sc2egset | research log | no |
| R06 | aoestats | 01_03_01 notebook | yes |
| R07 | sc2egset | profile MD only | no |
| R08 | sc2egset | 01_03_01 notebook | yes |
| R09 | sc2egset | 01_03_01 notebook | yes |
| R10 | aoe2companion | 01_03_01 notebook | yes |
| R11 | aoe2companion | 01_03_01 notebook | yes |
| R12 | aoe2companion | 01_03_01 notebook | yes (minor) |
| R13 | sc2egset | 01_03_01 notebook | yes (minor) |
| 1D | all | profile MD only | no |

**Execution grouping (3 PRs):**

- **PR 1 — Tracking + research log fixes (no notebook re-runs):**
  R01, R02, R03, R04, R05, R07, 1D
  All text edits. Can be done in a single session.

- **PR 2 — sc2egset 01_03_01 notebook update + re-execution:**
  R08, R09, R13
  Requires notebook re-run (sc2egset is small — ~45K rows, fast).

- **PR 3 — aoe2companion + aoestats 01_03_01 notebook updates + re-execution:**
  R06 (aoestats), R10, R11, R12 (aoe2companion)
  Requires notebook re-runs. aoe2companion is 277M rows (slow — budget 30 min).
  aoestats is 30M rows (moderate — budget 10 min).

---

## Part 2 — Forward-Looking Work (01_04+)

These items are NOT fixes to existing artifacts. They are new work that
should be planned and executed only AFTER Part 1 is complete.

### 2A. Structural prerequisites for 01_04

#### F01. sc2egset: create `matches_flat` VIEW [BLOCKER for 01_04]

Pre-game features are split across two tables:
- `replay_players_raw`: player-level (MMR, race, selectedRace, etc.)
- `replays_meta_raw` struct_flat: match-level (time_utc, map_name, etc.)

Any model needs both. The AoE2 datasets already have this joined structure.
Cross-table linkage verified: 22,390 matched replays, 0 orphans.

**Action:** First task in 01_04 for sc2egset. Create a `matches_flat` VIEW
(not materialized table) joining `replay_players_raw` with struct-extracted
fields from `replays_meta_raw` via `replay_id`. Produces 44,817 rows
(2 per match) with all player + match fields.

#### F02. Consolidated deferred-questions inventory (all 3 datasets)

No single document lists what 01_04 must address per dataset. Open questions
are scattered across 4+ research log entries each. The 01_04 planner must
reconstruct the list and may miss items (see R02 — the most recent entry
actively misled on duplicates).

**Action:** As part of each 01_04 plan's "Prerequisites" section, include
a consolidated open-question inventory with source step and resolution scope.

### 2B. 01_04 planning inputs per dataset

#### aoe2companion

- Rating ambiguity temporal join with ratings_raw (R04 standardized to 01_04)
- Deduplication with profileId=-1 stratified analysis (R02 corrected)
- 4.4M internally inconsistent 2-row matches root cause
- 428K NULL co-occurrence cluster investigation
- ratings_raw.games max outlier (1,775,260,795 vs p95 4,736) capping strategy
- Scope decision: 1v1 ranked only vs all team sizes

#### aoestats

- 212,890 orphan matches (0.69%) — cleaning decision
- profile_id DOUBLE precision-loss check (explicitly deferred to 01_04)
- Opening/age uptime NULL handling (86-91% NULL schema-change pattern)
- Odd player counts (1,3,5,7): 1,067 rows — filter decision

#### sc2egset

- `matches_flat` VIEW creation (F01)
- MMR=0 sentinel treatment (84% of rows): impute, exclude, or flag
- MMR negative values (-36,400 to 0): sentinel or legitimate
- 3 BW-prefixed race entries: merge with SC2 counterparts or exclude
- 273 replays with map_size=0: parse artifact or real
- 26 Undecided/Tie results: exclude from modeling
- 2 SQ INT32_MIN sentinels: exclude or impute
- 1,132 APM=0 rows: genuine or parse artifact
- 1,110 selectedRace="" rows: treatment strategy

### 2C. Before Phase 02

- Document Invariant #2 compliance path for aoestats (no nickname field —
  only numeric profile_id). Needs explicit thesis limitation statement.
- Document overviews_raw closure for aoestats: civs/openings already VARCHAR,
  no decoding needed.
- Verify cross-dataset profile JSON structural alignment (Invariant #8).
- Document aoestats join multiplicity for game_id across tables.

---

## Source Reviews

Full adversarial review transcripts were produced by three independent
reviewer-adversarial agents (Opus). Key statistics:

| Dataset | Findings | Blockers | Warnings | Notes |
|---------|----------|----------|----------|-------|
| sc2egset | 8 risks | 2 | 4 | 2 |
| aoestats | 6 risks | 1 | 4 | 1 |
| aoe2companion | 8 risks | 2 | 5 | 1 |
