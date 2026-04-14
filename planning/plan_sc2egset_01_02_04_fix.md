# Plan: sc2egset 01_02_04 Fix Pass

**Category:** A
**Step reference:** sc2egset Phase 01, Pipeline Section 01_02, Step 01_02_04 — Metadata STRUCT Extraction & Replay-Level EDA (corrective pass)
**Branch:** `chore/roadmap-researchlog-step-01-02-03` (current branch; no new branch needed)
**Planner model:** claude-opus-4-6
**Date:** 2026-04-14
**Critique required:** yes — dispatch reviewer-adversarial before execution

---

## Scope

Fix five defects found by adversarial review of step 01_02_04. Two blockers (research log had fabricated numbers; Undecided/Tie association claim was unsupported), two warnings (missing zero counts; misleading near-constant flags), and one structural gap (no structured pre-game/in-game field classification in the JSON artifact). The notebook, both artifacts (JSON and markdown), and the research log must be updated. No new data is introduced; all fixes derive from queries against the existing `db.duckdb`.

## Problem Statement

The initial execution of 01_02_04 produced artifacts with correct data, but the research log was written from planning-time expectations rather than actual artifact output. Additionally, the notebook omitted zero-count queries required by EDA Manual Section 3.1, the near-constant flag in the markdown lacked interpretive context, the Undecided/Tie claim was unsupported by the executed query, and downstream-facing metadata (pre-game vs in-game field classification) was absent from the JSON artifact.

## Assumptions and Unknowns

1. The DuckDB database at `data/db/db.duckdb` is unchanged since the initial 01_02_04 run.
2. The notebook can be re-run end-to-end in a single session. All new cells are additive; no existing cells are deleted.
3. The 24 Undecided and 2 Tie rows exist in `replay_players_raw` as shown in the JSON artifact `result_distribution`. The corrective query will reveal their replay context.

## Literature Context

EDA Manual Section 3.1 (column-level profiling): requires "zero count" for every variable.
EDA Manual Section 3.3 (dead/near-constant detection): uniqueness ratio < 0.001 threshold. Does not distinguish expected-low-cardinality categoricals from degenerate fields — the interpretive note is our addition.

## Invariants Touched

- **I6** (Reproducibility): New SQL queries must appear verbatim in the markdown artifact.
- **I7** (No magic numbers): Zero-count thresholds are exact equality checks (col = 0, col = -2147483648); sentinel value comes from INT32_MIN.
- **I9** (Step scope): No cleaning actions; all changes are profiling additions and artifact corrections.

---

## T01 — Add zero-count queries to the notebook and both artifacts

**Objective:** Compute the number of exact-zero values for each numeric column in `replay_players_raw` and the INT32_MIN sentinel count for SQ. Satisfies EDA Manual Section 3.1 "zero count" requirement.

**Instructions:**

1. In `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py`, add a new Section E2 cell block between Section E (numeric descriptive statistics) and Section F (temporal range). Header: `## Section E2: Zero Counts (EDA Manual 3.1)`.

2. Add SQL constant `ZERO_COUNT_SQL`:
```sql
SELECT
    COUNT(*) FILTER (WHERE MMR = 0) AS MMR_zero,
    COUNT(*) FILTER (WHERE APM = 0) AS APM_zero,
    COUNT(*) FILTER (WHERE SQ = 0) AS SQ_zero,
    COUNT(*) FILTER (WHERE SQ = -2147483648) AS SQ_sentinel,
    COUNT(*) FILTER (WHERE supplyCappedPercent = 0) AS supplyCappedPercent_zero,
    COUNT(*) FILTER (WHERE handicap = 0) AS handicap_zero,
    COUNT(*) FILTER (WHERE startDir = 0) AS startDir_zero,
    COUNT(*) FILTER (WHERE startLocX = 0) AS startLocX_zero,
    COUNT(*) FILTER (WHERE startLocY = 0) AS startLocY_zero,
    COUNT(*) FILTER (WHERE color_a = 0) AS color_a_zero,
    COUNT(*) FILTER (WHERE color_b = 0) AS color_b_zero,
    COUNT(*) FILTER (WHERE color_g = 0) AS color_g_zero,
    COUNT(*) FILTER (WHERE color_r = 0) AS color_r_zero,
    COUNT(*) FILTER (WHERE playerID = 0) AS playerID_zero,
    COUNT(*) FILTER (WHERE userID = 0) AS userID_zero
FROM replay_players_raw
```

3. Add SQL constant `DURATION_ZERO_COUNT_SQL`:
```sql
SELECT
    COUNT(*) FILTER (WHERE elapsed_game_loops = 0) AS elapsed_game_loops_zero
FROM struct_flat
```

4. Add SQL constant `DUPLICATE_CHECK_SQL`:
```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT filename || '|' || toon_id) AS distinct_player_rows,
    COUNT(*) - COUNT(DISTINCT filename || '|' || toon_id) AS duplicate_rows
FROM replay_players_raw
```

5. Execute all three queries and store results as DataFrames (`zero_counts`, `duration_zero_counts`, `duplicate_check`).

6. In the JSON artifact assembly cell, add top-level keys `"zero_counts"` and `"duplicate_check"`:
```json
{
  "zero_counts": {
    "replay_players_raw": {
      "MMR_zero": <value>,
      "APM_zero": <value>,
      "SQ_zero": <value>,
      "SQ_sentinel": <value>,
      "supplyCappedPercent_zero": <value>,
      "handicap_zero": <value>,
      "startDir_zero": <value>,
      "startLocX_zero": <value>,
      "startLocY_zero": <value>,
      "color_a_zero": <value>,
      "color_b_zero": <value>,
      "color_g_zero": <value>,
      "color_r_zero": <value>,
      "playerID_zero": <value>,
      "userID_zero": <value>
    },
    "replays_meta_raw": {
      "elapsed_game_loops_zero": <value>
    }
  },
  "duplicate_check": {
    "total_rows": <value>,
    "distinct_player_rows": <value>,
    "duplicate_rows": <value>
  }
}
```

7. In the markdown artifact assembly, add `## Section E2: Zero Counts` block with all SQL queries verbatim (I6), result tables, and `## Section E3: Duplicate Detection`.

**Verification:**
```bash
source .venv/bin/activate && poetry run python3 -c "
import json
d = json.load(open('src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json'))
assert 'zero_counts' in d
assert 'SQ_sentinel' in d['zero_counts']['replay_players_raw']
assert 'elapsed_game_loops_zero' in d['zero_counts']['replays_meta_raw']
assert 'duplicate_check' in d
print('zero_counts and duplicate_check OK')
"
```

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json` (regenerated by notebook)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md` (regenerated by notebook)

---

## T02 — Add structured pre-game/in-game field annotation to JSON artifact

**Objective:** Encode a structured classification of all 25 `replay_players_raw` columns and extracted `struct_flat` fields as a `field_classification` key in the JSON artifact, so downstream steps can programmatically distinguish field categories without parsing prose.

**Instructions:**

1. In the notebook, add a new cell after Section H (dead/constant detection) but before the artifact assembly. Define `FIELD_CLASSIFICATION`:

```python
FIELD_CLASSIFICATION = {
    "replay_players_raw": {
        "identifier": ["filename", "toon_id", "nickname", "playerID", "userID"],
        "pre_game": [
            "MMR", "race", "selectedRace", "handicap", "region", "realm",
            "highestLeague", "isInClan", "clanTag", "startDir", "startLocX",
            "startLocY", "color_a", "color_b", "color_g", "color_r"
        ],
        "in_game": ["APM", "SQ", "supplyCappedPercent"],
        "target": ["result"],
    },
    "replays_meta_raw_struct_flat": {
        "identifier": ["filename"],
        "pre_game": [
            "time_utc", "game_version_header", "base_build", "data_build",
            "game_version_meta", "map_name", "max_players", "map_size_x",
            "map_size_y", "is_blizzard_map", "is_blizzard_map_init"
        ],
        "in_game": ["elapsed_game_loops"],
        "constant": ["game_speed", "game_speed_init", "gameEventsErr", "messageEventsErr", "trackerEvtsErr"],
    },
    "classification_notes": {
        "pre_game": "Available before match start. Usable as prediction features without temporal leakage.",
        "in_game": "Computed from replay actions; available only post-game. Using these as features requires in-game prediction framing (Phase 02 decision).",
        "identifier": "Player/replay identity columns. Not features.",
        "target": "Prediction target. Never a feature.",
        "constant": "Single-value columns. No predictive information.",
    },
}
```

2. In the artifact assembly cell, add `"field_classification": FIELD_CLASSIFICATION` to the findings dict.

3. Update the existing Section E markdown note (currently "Note: APM, SQ, and supplyCappedPercent are in-game-only fields.") to add: "See `field_classification` in the JSON artifact for the full pre-game/in-game/identifier/target/constant taxonomy."

**Verification:**
```bash
source .venv/bin/activate && poetry run python3 -c "
import json
d = json.load(open('src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json'))
fc = d['field_classification']
assert 'replay_players_raw' in fc
assert set(fc['replay_players_raw']['in_game']) == {'APM', 'SQ', 'supplyCappedPercent'}
assert 'result' in fc['replay_players_raw']['target']
total = sum(len(v) for k, v in fc['replay_players_raw'].items() if k != 'classification_notes')
assert total == 25, f'Expected 25 columns, got {total}'
print('field_classification OK')
"
```

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json` (regenerated)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md` (regenerated)

**Read scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replay_players_raw.yaml` (verify column completeness)

---

## T03 — Fix near-constant flag interpretation in markdown artifact

**Objective:** Add an interpretive note to Section H of the markdown artifact distinguishing expected-low-cardinality categoricals from genuinely problematic near-constant fields.

**Instructions:**

1. In the notebook markdown assembly for Section H, insert the following interpretive paragraph between the "Flagged Columns" header and the flagged table:

```
### Interpretation Note

The uniqueness_ratio < 0.001 threshold (EDA Manual Section 3.3) flags all
low-cardinality columns mechanically. This includes:

- **Expected categoricals** (race, selectedRace, highestLeague, region, realm,
  result, isInClan, color_*, startDir): These are inherently low-cardinality
  fields in any game dataset. Flagging them is a consequence of the threshold
  definition, not a data quality concern. Their value distributions are profiled
  in Section D.

- **Genuinely constant/degenerate** (game_speed, game_speed_init,
  gameEventsErr, messageEventsErr, trackerEvtsErr): cardinality=1 fields
  that carry zero information and should be excluded from feature engineering.

- **Low-cardinality numerics** (playerID, userID, handicap):
  playerID ranges 1-16 (slot index within replay, not a player identifier);
  userID is similarly replay-scoped; handicap is 100 for all but 1 row.
  These warrant investigation in cleaning (01_04) but are not data quality
  defects per se.

Downstream steps should use the `field_classification` in the JSON artifact
rather than the near-constant flag to decide feature eligibility.
```

**Verification:**
- After notebook re-run, grep markdown artifact for "Interpretation Note" between the Section H header and the flagged table.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md` (regenerated)

---

## T04 — Run corrective query for Undecided/Tie result context

**Objective:** Determine the actual replay context (maxPlayers, player row count, replayId) for the 24 Undecided and 2 Tie result rows. The prior OR-condition query returned only Win and Loss, meaning Undecided/Tie rows are likely in 2-player replays. This must be documented with a corrective query.

**Instructions:**

1. In the notebook, add a new cell immediately after the non-2-player results cell in Section C (after the existing non-2-player query). Header: `# Corrective query: Undecided/Tie replay context`.

2. Add SQL constant `UNDECIDED_TIE_CONTEXT_SQL`:
```sql
-- Note: Joins on filename per sql-data.md rule 15 deviation — unavoidable at this
-- pipeline stage (replay_id not yet derived). Migrates to replay_id in 01_04.
SELECT
    rp.result,
    rp.filename,
    rm.initData.gameDescription.maxPlayers AS max_players,
    player_counts.player_row_count
FROM replay_players_raw rp
LEFT JOIN replays_meta_raw rm ON rp.filename = rm.filename
JOIN (
    SELECT filename, COUNT(*) AS player_row_count
    FROM replay_players_raw
    GROUP BY filename
) player_counts ON rp.filename = player_counts.filename
WHERE rp.result IN ('Undecided', 'Tie')
ORDER BY rp.result, rp.filename
```

3. Execute and store as `undecided_tie_context`. Print the full result (>= 24 rows).

4. In the JSON artifact assembly, add top-level key `"undecided_tie_context"` with the DataFrame as records.

5. In the markdown assembly, add a subsection under Section C "Non-2-player replay results":

```
### Undecided/Tie replay context (corrective query)
[SQL verbatim per I6]
[Result table]

Finding: [derived from actual query output — e.g. "All 26 rows come from standard
2-player replays" or "N of 26 come from non-2-player replays"]

Note: The OR-condition non-2-player query above returned only Win/Loss.
Undecided/Tie rows are [not / partially] associated with non-2-player replays
per this corrective query.
```

**Verification:**
- JSON artifact contains `undecided_tie_context` key.
- `len(undecided_tie_context) >= 24` (26 expected; LEFT JOIN on `replays_meta_raw` allows fewer if filename absent).
- Markdown contains the corrective SQL block.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json` (regenerated)
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md` (regenerated)

---

## File Manifest

| File | Action | Task(s) |
|------|--------|---------|
| `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_04_univariate_census.py` | UPDATE | T01, T02, T03, T04 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json` | REGENERATE | T01, T02, T04 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.md` | REGENERATE | T01, T02, T03, T04 |

No schema YAMLs modified. No STEP_STATUS.yaml changes. No cleaning actions.

---

## Gate Conditions

1. JSON artifact contains `zero_counts.replay_players_raw` with keys for MMR_zero, SQ_zero, SQ_sentinel, APM_zero, handicap_zero, and `zero_counts.replays_meta_raw.elapsed_game_loops_zero`; and `duplicate_check.duplicate_rows`.
2. JSON artifact contains `field_classification.replay_players_raw` and `field_classification.replays_meta_raw_struct_flat`, each with category lists. Total replay_players_raw column count = 25.
3. Markdown artifact contains "Interpretation Note" in Section H.
4. JSON artifact contains `undecided_tie_context` with `len >= 24` rows (26 expected; LEFT JOIN allows fewer if filename absent from `replays_meta_raw`).

## Out of Scope

- Skewness/kurtosis/outlier detection (deferred to 01_03)
- Bivariate analysis
- Schema YAML description updates
- STEP_STATUS.yaml / PHASE_STATUS.yaml changes (step remains `complete`)
- gameOptions STRUCT sub-field extraction (deferred, documented)
- Research log rewrite for 01_02_04 (deferred until notebook is fully polished)

## Deferred Debt

| Item | Deferred To |
|------|-------------|
| Skewness, kurtosis, IQR outlier detection | Pipeline Section 01_03 |
| MMR=0 sentinel interpretation and cleaning | Step 01_04 |
| SQ=INT32_MIN cleaning strategy | Step 01_04 |
| Undecided/Tie row disposition | Step 01_04 |
| gameOptions sub-fields (competitive, practice flags) | Step 01_04 |
| 22.4 loops/sec external citation | Thesis chapter (cite SC2EGSet paper or Blizzard tech docs) |
| Bivariate analysis (MMR vs result, race vs win rate) | Future 01_02 or 01_03 step |
| Completeness matrix (column-pair missingness co-occurrence) | Pipeline Section 01_03 (all columns are 0% NULL — trivially uniform; note explicitly in artifact) |
| Memory footprint of `replay_players_raw` in DuckDB | Informational; any step |
| `toon_id` format analysis (structure, region codes) | Step 01_04 / identity resolution |
