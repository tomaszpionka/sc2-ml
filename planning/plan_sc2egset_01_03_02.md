---
category: A
branch: feat/census-pass3
date: 2026-04-16
planner_model: claude-opus-4-6
dataset: sc2egset
phase: "01"
pipeline_section: "01_03 -- Systematic Data Profiling"
invariants_touched: [3, 6, 7, 9]
critique_required: true
source_artifacts:
  - "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
  - "src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json"
  - "src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replay_players_raw.yaml"
  - "src/rts_predict/games/sc2/datasets/sc2egset/data/db/schemas/raw/replays_meta_raw.yaml"
research_log_ref: "src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md#2026-04-16-phase01-01_03_02"
---

# Plan: sc2egset Step 01_03_02 -- True 1v1 Match Identification

## Scope

**Phase/Step:** 01 / 01_03_02
**Branch:** feat/census-pass3
**Action:** CREATE (new step within pipeline section 01_03 -- Systematic Data Profiling)
**Predecessor:** 01_03_01 (Systematic Data Profiling -- complete, artifacts on disk)

Identify which replays in the sc2egset dataset are genuine 1v1 matches -- exactly
two active human players with a decisive Win/Loss result. The sc2egset replay
corpus is sourced from esport tournaments that are predominantly 1v1, but the
ToonPlayerDescMap extraction (01_02_02) inserted all player entries from each
replay file, including potential observers, spectators, and additional slots from
team games. This step must separate signal (true 1v1) from noise (non-1v1) before
the data cleaning step (01_04) can define the final analysis population.

This step does NOT drop or filter rows (I9 -- profiling only, no cleaning
decisions). It produces a classification of every replay into one of:
`true_1v1_decisive`, `non_1v1_too_many_players`, `non_1v1_too_few_players`,
`true_1v1_indecisive`, with the counts and full replay lists stored
in the JSON artifact. The actual exclusion is deferred to the data cleaning step.

## Problem Statement

### Evidence from prior steps

The following quantitative evidence, all from completed steps with artifacts
on disk, motivates this profiling step:

**playerID distribution (from 01_02_04 census JSON, `column_profiles.playerID.top_n`):**

| playerID | count | pct |
|----------|-------|-----|
| 1 | 22,390 | 49.96% |
| 2 | 22,387 | 49.95% |
| 3 | 8 | 0.02% |
| 4 | 8 | 0.02% |
| 5 | 6 | 0.01% |
| 6 | 6 | 0.01% |
| 7 | 5 | 0.01% |
| 8 | 5 | 0.01% |
| 9 | 2 | 0.004% |

Total rows: 44,817. "Extra" rows beyond ideal 2-per-replay: 44,817 - (2 * 22,390) = 37.
Three replays have playerID=2 missing (22,390 - 22,387 = 3), meaning 3 replays
may have only 1 player row. The 37 extra rows (playerID 3-9) indicate replays
with 3+ player rows in replay_players_raw.

**max_players struct field (from 01_03_01 systematic profile JSON):**
Cardinality = 5, IQR = 0.0, uniqueness_ratio = 0.000223. This means max_players
takes 5 distinct values but the overwhelming majority are the same value.
The exact value distribution is an unknown to be resolved during execution.

**non_2p_results (from 01_02_04 census JSON):**
The query `WHERE rm.initData.gameDescription.maxPlayers != 2 OR actual
player-row count != 2` returned 861 player rows (444 Loss, 417 Win).
This is the superset -- replays that fail EITHER criterion.

**selectedRace distribution (from 01_02_04 census JSON):**
Empty string `''`: 1,110 rows (2.48%). These are potential observer/spectator
entries. Standard races (Prot, Zerg, Terr, Rand): 43,704. BW variants
(BWTe, BWZe, BWPr): 3 rows (1 each).

**result distribution (from 01_02_04 census JSON):**
Win: 22,382; Loss: 22,409; Undecided: 24; Tie: 2. Total: 44,817.

**observers field in replays_meta_raw initData struct:**
The replays_meta_raw schema shows `initData.gameDescription.gameOptions.observers`
as a BIGINT field. This directly encodes the observer setting for each lobby.

**Cross-table linkage (from 01_03_01):**
Perfect referential integrity: 22,390 replays in both tables, 0 orphans.

### Key unknowns to resolve

1. **Is this dataset already exclusively 1v1?** The playerID data suggests the
   vast majority are 1v1 (playerID 1 = 22,390, playerID 2 = 22,387 -- nearly
   all replays have exactly 2 player rows). But the 37 extra rows (playerID 3-9)
   and the 1,110 empty-string selectedRace values require investigation.

2. **What does `max_players` encode?** In SC2, `maxPlayers` is the lobby slot
   count, not the count of active players. A 1v1 match on a map with observer
   slots could have maxPlayers > 2. This means maxPlayers alone is NOT a reliable
   1v1 filter -- it must be cross-referenced with actual player row counts.

3. **Are the 1,110 empty-selectedRace rows observers?** If observers are
   extracted as player rows during ToonPlayerDescMap parsing, they would
   lack a selectedRace. But if all 1,110 appear in 2-player replays, they
   are likely real players with a data quality issue, not observers.

4. **What is the relationship between empty selectedRace and non-2-player replays?**
   Do the 37 extra player rows overlap with the 1,110 empty-selectedRace entries?
   Are the 3 replays with only 1 player row related to the empty selectedRace?

5. **What does `initData.gameDescription.gameOptions.observers` tell us?**
   SC2 lobby settings record an observer mode (0 = no observers, 1+ = observers
   allowed). If the extracted player rows include observers, this field helps
   confirm the hypothesis.

## Assumptions & Unknowns

- **Assumption:** replay_players_raw has 44,817 rows across 22,390 distinct
  filenames (from 01_02_04 census).
- **Assumption:** replays_meta_raw has 22,390 rows (from 01_02_04 census).
- **Assumption:** playerID cardinality = 9 (values 1 through 9) with zero
  playerID=0 entries (from 01_02_04 census `zero_counts.playerID_zero = 0`).
- **Assumption:** selectedRace values `['Prot', 'Zerg', 'Terr', 'Rand']` constitute
  standard playable races. Derived from 01_02_04 census race distribution where
  these 4 values account for 43,704 of 44,817 rows.
- **Assumption:** All SQL joins use the canonical `filename` column (I10).
  Note: the sql-data rule says to use `replay_id` for downstream tables, but
  `*_raw` tables use `filename` as their native key. This step works entirely
  with raw tables.
- **Unknown (resolved during execution):** The exact `max_players` value
  distribution across 22,390 replays.
- **Unknown (resolved during execution):** Whether the 1,110 empty-selectedRace
  rows belong to 2-player replays or non-2-player replays.
- **Unknown (resolved during execution):** Whether players with empty
  selectedRace also have result='Win' or result='Loss' (active players) or
  result='Undecided' (possibly observers).

## Literature Context

- SC2 replay file format: Białecki, A. et al. (2023). SC2EGSet: StarCraft II
  Esport Replay and Game-state Dataset. Scientific Data 10(1), 600. The paper
  describes the dataset as derived from "1v1 esport replays" but does not
  explicitly state whether team game or observer replays were excluded.
- SC2 replay structure: The s2protocol library (Blizzard, GitHub) documents that
  the ToonPlayerDescMap contains entries for all players including observers and
  referees. Observer entries typically have a player type or missing race data.
- This step follows the systematic profiling methodology of Abedjan et al. (2015)
  for population definition -- identifying which records belong to the analysis
  population before any filtering occurs.

## Execution Steps

### T01 -- ROADMAP Patch

**Objective:** Add the step 01_03_02 definition to the sc2egset ROADMAP.

**Instructions:**
1. Open `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`.
2. After the step 01_03_01 definition block and before any Phase 02 content, insert:

```yaml
### Step 01_03_02 -- True 1v1 Match Identification

step_number: "01_03_02"
name: "True 1v1 Match Identification"
description: "Profile every replay to determine which are genuine 1v1 matches (exactly 2 active player rows with decisive Win/Loss results) vs non-1v1 (team games, observer contamination, incomplete replays). Produces a replay-level classification without dropping any rows (cleaning deferred to 01_04)."
phase: "01 -- Data Exploration"
pipeline_section: "01_03 -- Systematic Data Profiling"
manual_reference: "01_DATA_EXPLORATION_MANUAL.md, Section 3"
dataset: "sc2egset"
question: "Which of the 22,390 replays are genuine 1v1 matches, and what characterises the non-1v1 replays?"
method: "DuckDB SQL: per-replay player row counts, cross-reference with max_players struct field, selectedRace/result analysis of non-2-player rows, observer setting profiling. Multi-signal classification of each replay."
predecessors: "01_03_01"
notebook_path: "sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_02_true_1v1_identification.py"
inputs:
  duckdb_tables:
    - "replay_players_raw"
    - "replays_meta_raw"
  prior_artifacts:
    - "artifacts/01_exploration/02_eda/01_02_04_univariate_census.json"
    - "artifacts/01_exploration/03_profiling/01_03_01_systematic_profile.json"
  external_references:
    - ".claude/scientific-invariants.md"
outputs:
  data_artifacts:
    - "artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json"
  report: "artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.md"
reproducibility: "Code and output in the paired notebook."
scientific_invariants_applied:
  - number: "6"
    how_upheld: "All SQL queries stored in sql_queries dict and written verbatim to markdown artifact."
  - number: "7"
    how_upheld: "Standard race list derived dynamically from 01_02_04 census categorical_profiles.selectedRace at runtime (list comprehension + assertion guard). All other thresholds from census JSON."
  - number: "9"
    how_upheld: "Classification and profiling only. No rows dropped, no new features computed, no cleaning decisions made."
  - number: "3"
    how_upheld: "elapsed_game_loops annotated as POST-GAME wherever referenced. No temporal features computed."
gate:
  artifact_check: "artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json and .md exist and are non-empty."
  continue_predicate: "JSON contains: true_1v1_decisive_count, true_1v1_indecisive_count, total_replay_count, observer_row_analysis, players_per_replay_distribution, max_players_distribution, replay_classification. MD contains comparison summary table. true_1v1_decisive_count + true_1v1_indecisive_count + sum(non_1v1 categories) = total_replay_count."
  halt_predicate: "Any artifact is missing, or classification totals do not sum to 22,390."
thesis_mapping:
  - "Chapter 4 -- Data and Methodology > 4.1.1 SC2EGSet (StarCraft II)"
research_log_entry: "Required on completion."
```

**Verification:**
- ROADMAP.md contains a `### Step 01_03_02` section with the full YAML block.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md`

---

### T02 -- Notebook Setup

**Objective:** Create the notebook file with imports, DuckDB connection, census JSON
load, and all runtime constants derived from census (I7). Create the artifact
output directory if needed.

**Instructions:**
1. Verify directory `sandbox/sc2/sc2egset/01_exploration/03_profiling/` exists (created in 01_03_01).
2. Create `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`
   as a jupytext percent-format notebook.

**Cell 1 -- markdown header:**
```
# Step 01_03_02 -- True 1v1 Match Identification
#
# **Phase:** 01 -- Data Exploration
# **Pipeline Section:** 01_03 -- Systematic Data Profiling
# **Dataset:** sc2egset
# **Question:** Which of the 22,390 replays are genuine 1v1 matches?
# **Invariants applied:** #6 (all SQL stored verbatim), #7 (all thresholds
# data-derived from census), #9 (profiling only, no cleaning decisions)
# **Predecessor:** 01_03_01 (Systematic Data Profiling -- complete)
# **Type:** Read-only -- no DuckDB writes
```

**Cell 2 -- imports:**
```python
import json
from pathlib import Path

import pandas as pd

from rts_predict.common.notebook_utils import (
    get_notebook_db,
    get_reports_dir,
    setup_notebook_logging,
)

logger = setup_notebook_logging()
```

**Cell 3 -- DuckDB connection:**
```python
conn = get_notebook_db("sc2", "sc2egset")
```

**Cell 4 -- census load and runtime constants (I7):**
```python
reports_dir = get_reports_dir("sc2", "sc2egset")
census_json_path = (
    reports_dir / "artifacts" / "01_exploration" / "02_eda"
    / "01_02_04_univariate_census.json"
)
with open(census_json_path) as f:
    census = json.load(f)

profile_json_path = (
    reports_dir / "artifacts" / "01_exploration" / "03_profiling"
    / "01_03_01_systematic_profile.json"
)
with open(profile_json_path) as f:
    profile = json.load(f)

# --- Runtime constants from census (Invariant #7) ---
RP_TOTAL_ROWS = census["null_census"]["replay_players_raw"]["total_rows"]
print(f"replay_players_raw total rows: {RP_TOTAL_ROWS}")

RM_TOTAL_ROWS = census["null_census"]["replays_meta_raw_filename"]["total_rows"]
print(f"replays_meta_raw total rows: {RM_TOTAL_ROWS}")

# Derive STANDARD_RACES dynamically from census -- I7: no magic numbers
STANDARD_RACES = sorted([
    entry['selectedRace']
    for entry in census['categorical_profiles']['selectedRace']
    if entry['selectedRace'] != '' and not entry['selectedRace'].startswith('BW')
])
# Assert expected values match (guard against census change)
assert set(STANDARD_RACES) == {'Prot', 'Zerg', 'Terr', 'Rand'}, \
    f"Unexpected STANDARD_RACES from census: {STANDARD_RACES}"
print(f"Standard races (derived from census at runtime): {STANDARD_RACES}")

# Non-2p results from census
non_2p_total = sum(r["cnt"] for r in census["non_2p_results"])
print(f"non_2p player rows (census): {non_2p_total}")

# Result distribution from census
result_dist = {r["result"]: r["cnt"] for r in census["result_distribution"]}
N_WIN = result_dist["Win"]
N_LOSS = result_dist["Loss"]
N_UNDECIDED = result_dist.get("Undecided", 0)
N_TIE = result_dist.get("Tie", 0)
print(f"Win: {N_WIN}, Loss: {N_LOSS}, Undecided: {N_UNDECIDED}, Tie: {N_TIE}")

# playerID cardinality from census
PLAYER_ID_CARDINALITY = census["cardinality"][3]["cardinality"]  # playerID entry
print(f"playerID cardinality: {PLAYER_ID_CARDINALITY}")

# Output directories
artifact_dir = (
    reports_dir / "artifacts" / "01_exploration" / "03_profiling"
)
artifact_dir.mkdir(parents=True, exist_ok=True)
print(f"Artifact dir: {artifact_dir}")
```

Note: `STANDARD_RACES` is now dynamically derived from the census at runtime via a
list comprehension over `categorical_profiles.selectedRace`, filtering out the
empty-string entry and BW-prefixed variants. The census shows Prot (15,948),
Zerg (15,123), Terr (12,623), empty-string (1,110), Rand (10), BWTe (1), BWZe (1),
BWPr (1). The 4 standard races exclude empty-string and BW variants. An assertion
guard catches any future census change. This is justified by the census data, not
by domain knowledge (I7, I9).

**Cell 5 -- SQL queries dict (I6):**
```python
sql_queries = {}
```

**Verification:**
- Notebook runs through T02 cells without error.
- Census and profile JSON load. All constants printed.
- `conn`, `census`, `profile`, `sql_queries`, `artifact_dir` all defined.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T03 -- Players-Per-Replay Distribution

**Objective:** Compute the exact distribution of player row counts per replay file,
answering: how many replays have exactly 2 player rows, how many have 1, 3, 4, etc.?

**Instructions:**

**Cell 6 -- players_per_replay distribution:**
```python
sql_queries["players_per_replay"] = """
SELECT
    players_per_replay,
    COUNT(*) AS replay_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS pct
FROM (
    SELECT
        filename,
        COUNT(*) AS players_per_replay
    FROM replay_players_raw
    GROUP BY filename
)
GROUP BY players_per_replay
ORDER BY players_per_replay
"""

players_per_replay_df = conn.execute(sql_queries["players_per_replay"]).fetch_df()
print("=== Players per replay distribution ===")
print(players_per_replay_df.to_string(index=False))
total_replays_check = players_per_replay_df["replay_count"].sum()
print(f"\nTotal replays: {total_replays_check} (expected: {RM_TOTAL_ROWS})")
assert total_replays_check == RM_TOTAL_ROWS, (
    f"Replay count mismatch: {total_replays_check} != {RM_TOTAL_ROWS}"
)
```

**Cell 7 -- replays with non-2 player rows (detail):**
```python
sql_queries["non_2p_replay_detail"] = """
SELECT
    rp.filename,
    COUNT(*) AS player_row_count,
    LIST(rp.playerID ORDER BY rp.playerID) AS player_ids,
    LIST(rp.selectedRace ORDER BY rp.playerID) AS selected_races,
    LIST(rp.result ORDER BY rp.playerID) AS results,
    LIST(rp.nickname ORDER BY rp.playerID) AS nicknames,
    rm.initData.gameDescription.maxPlayers AS max_players_setting,
    rm.initData.gameDescription.gameOptions.observers AS observer_setting
FROM replay_players_raw rp
JOIN replays_meta_raw rm ON rp.filename = rm.filename
GROUP BY rp.filename, max_players_setting, observer_setting
HAVING COUNT(*) != 2
ORDER BY COUNT(*) DESC, rp.filename
"""

non_2p_detail_df = conn.execute(sql_queries["non_2p_replay_detail"]).fetch_df()
print(f"=== Replays with != 2 player rows: {len(non_2p_detail_df)} ===")
print(non_2p_detail_df.to_string(index=False))
```

This query reveals every anomalous replay: its playerID list, races, results,
max_players lobby setting, and observer setting. The list aggregations let us
inspect each case individually.

**Verification:**
- players_per_replay_df shows the complete distribution.
- Assert that the sum of replay_count equals 22,390.
- non_2p_detail_df is populated (may be empty if all replays have exactly 2 rows).

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T04 -- max_players Distribution and Observer Setting Analysis

**Objective:** Profile the `max_players` struct field from replays_meta_raw and
the `observers` game option, both critical for understanding lobby configuration.

**Instructions:**

**Cell 8 -- max_players value distribution:**
```python
sql_queries["max_players_distribution"] = """
SELECT
    initData.gameDescription.maxPlayers AS max_players,
    COUNT(*) AS replay_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS pct
FROM replays_meta_raw
GROUP BY max_players
ORDER BY max_players
"""

max_players_df = conn.execute(sql_queries["max_players_distribution"]).fetch_df()
print("=== max_players distribution ===")
print(max_players_df.to_string(index=False))
```

**Cell 9 -- observer setting distribution:**
```python
sql_queries["observer_setting_distribution"] = """
SELECT
    initData.gameDescription.gameOptions.observers AS observer_setting,
    COUNT(*) AS replay_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS pct
FROM replays_meta_raw
GROUP BY observer_setting
ORDER BY observer_setting
"""

observer_df = conn.execute(sql_queries["observer_setting_distribution"]).fetch_df()
print("=== Observer setting distribution ===")
print(observer_df.to_string(index=False))
```

**Cell 10 -- cross-tabulation of max_players vs actual player row count:**
```python
sql_queries["max_players_vs_actual"] = """
SELECT
    rm.initData.gameDescription.maxPlayers AS max_players,
    pc.players_per_replay,
    COUNT(*) AS replay_count
FROM replays_meta_raw rm
JOIN (
    SELECT filename, COUNT(*) AS players_per_replay
    FROM replay_players_raw
    GROUP BY filename
) pc ON rm.filename = pc.filename
GROUP BY max_players, players_per_replay
ORDER BY max_players, players_per_replay
"""

cross_tab_df = conn.execute(sql_queries["max_players_vs_actual"]).fetch_df()
print("=== max_players vs actual player row count ===")
print(cross_tab_df.to_string(index=False))
```

This cross-tabulation is the core analysis: it reveals whether `max_players = 2`
reliably means 2 actual player rows, and what happens for `max_players > 2`.

**Verification:**
- max_players_df shows all 5 distinct values and their counts.
- observer_df shows the observer setting distribution.
- cross_tab_df shows every (max_players, players_per_replay) combination.
- Sum of replay_count in each distribution = 22,390.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T05 -- Empty-selectedRace Analysis (Observer Hypothesis)

**Objective:** Investigate the 1,110 rows with `selectedRace = ''` to determine
whether they are observers, data quality issues, or something else.

**Instructions:**

**Cell 11 -- empty selectedRace profile:**
```python
sql_queries["empty_race_profile"] = """
SELECT
    rp.filename,
    rp.playerID,
    rp.nickname,
    rp.selectedRace,
    rp.race,
    rp.result,
    rp.MMR,
    rp.APM,
    rp.highestLeague,
    rm.initData.gameDescription.maxPlayers AS max_players,
    rm.initData.gameDescription.gameOptions.observers AS observer_setting,
    pc.players_per_replay
FROM replay_players_raw rp
JOIN replays_meta_raw rm ON rp.filename = rm.filename
JOIN (
    SELECT filename, COUNT(*) AS players_per_replay
    FROM replay_players_raw
    GROUP BY filename
) pc ON rp.filename = pc.filename
WHERE rp.selectedRace = ''
ORDER BY pc.players_per_replay DESC, rp.filename, rp.playerID
"""

empty_race_df = conn.execute(sql_queries["empty_race_profile"]).fetch_df()
print(f"=== Empty selectedRace rows: {len(empty_race_df)} ===")
print(f"Unique replays with empty selectedRace: {empty_race_df['filename'].nunique()}")
print(f"\nPlayers_per_replay distribution for these rows:")
print(empty_race_df["players_per_replay"].value_counts().sort_index().to_string())
print(f"\nResult distribution for empty selectedRace:")
print(empty_race_df["result"].value_counts().to_string())
print(f"\nRace (resolved) distribution for empty selectedRace:")
print(empty_race_df["race"].value_counts().to_string())
print(f"\nAPM distribution for empty selectedRace:")
print(empty_race_df["APM"].describe().to_string())
print(f"\nMMR distribution for empty selectedRace:")
print(empty_race_df["MMR"].describe().to_string())
print(f"\nFirst 20 rows:")
print(empty_race_df.head(20).to_string(index=False))
```

Key diagnostic signals:
- If empty-selectedRace rows have `result='Win'` or `result='Loss'` and
  `APM > 0`, they are active players who selected Random (race resolved post-game).
- If they have `result='Undecided'` and `APM = 0`, they are likely observers.
- If their `players_per_replay = 2`, they are in 2-player replays and the
  empty race is a data quality issue, not an observer issue.
- The `race` column may be populated even when `selectedRace` is empty (race
  is resolved after the game; selectedRace is the pre-game selection).

**Verification:**
- empty_race_df has 1,110 rows (from census).
- Result, APM, and players_per_replay distributions printed and interpretable.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T06 -- BW Race Variant and Undecided/Tie Analysis

**Objective:** Profile the 3 BW-race variant rows and the 26 Undecided/Tie rows
in the context of their replays' 1v1 status.

**Instructions:**

**Cell 12 -- BW race variant context:**
```python
sql_queries["bw_race_context"] = """
SELECT
    rp.filename,
    rp.playerID,
    rp.selectedRace,
    rp.race,
    rp.result,
    rp.APM,
    pc.players_per_replay,
    rm.initData.gameDescription.maxPlayers AS max_players
FROM replay_players_raw rp
JOIN replays_meta_raw rm ON rp.filename = rm.filename
JOIN (
    SELECT filename, COUNT(*) AS players_per_replay
    FROM replay_players_raw
    GROUP BY filename
) pc ON rp.filename = pc.filename
WHERE rp.selectedRace IN ('BWTe', 'BWZe', 'BWPr')
ORDER BY rp.filename, rp.playerID
"""

bw_df = conn.execute(sql_queries["bw_race_context"]).fetch_df()
print(f"=== BW race variant rows: {len(bw_df)} ===")
print(bw_df.to_string(index=False))
```

**Cell 13 -- Undecided/Tie replays in 1v1 context:**
```python
sql_queries["undecided_tie_1v1_context"] = """
SELECT
    rp.filename,
    rp.playerID,
    rp.selectedRace,
    rp.result,
    pc.players_per_replay,
    rm.initData.gameDescription.maxPlayers AS max_players
FROM replay_players_raw rp
JOIN replays_meta_raw rm ON rp.filename = rm.filename
JOIN (
    SELECT filename, COUNT(*) AS players_per_replay
    FROM replay_players_raw
    GROUP BY filename
) pc ON rp.filename = pc.filename
WHERE rp.result IN ('Undecided', 'Tie')
ORDER BY rp.result, rp.filename, rp.playerID
"""

undecided_df = conn.execute(sql_queries["undecided_tie_1v1_context"]).fetch_df()
print(f"=== Undecided/Tie rows: {len(undecided_df)} ===")
print(f"Unique replays: {undecided_df['filename'].nunique()}")
print(f"\nPlayers_per_replay for Undecided/Tie replays:")
print(undecided_df["players_per_replay"].value_counts().sort_index().to_string())
```

Note: The 01_02_04 census already showed that all Undecided/Tie replays have
`max_players=2` and `player_row_count=2`. This query confirms that finding and
adds the selectedRace dimension.

**Verification:**
- bw_df has exactly 3 rows.
- undecided_df has exactly 26 rows (24 Undecided + 2 Tie).

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T07 -- Replay-Level Classification

**Objective:** Classify every replay into one of four categories based on the
multi-signal analysis from T03-T06. Produce the final replay-level classification
that will feed the data cleaning step (01_04).

**Instructions:**

**Cell 14 -- comprehensive replay classification:**
```python
sql_queries["replay_classification"] = """
WITH per_replay AS (
    SELECT
        rp.filename,
        COUNT(*) AS player_row_count,
        COUNT(*) FILTER (
            WHERE rp.selectedRace IN ('Prot', 'Zerg', 'Terr', 'Rand')
        ) AS standard_race_count,
        COUNT(*) FILTER (WHERE rp.result IN ('Win', 'Loss')) AS decisive_count,
        COUNT(*) FILTER (WHERE rp.result = 'Win') AS win_count,
        COUNT(*) FILTER (WHERE rp.result = 'Loss') AS loss_count,
        COUNT(*) FILTER (WHERE rp.result = 'Undecided') AS undecided_count,
        COUNT(*) FILTER (WHERE rp.result = 'Tie') AS tie_count,
        COUNT(*) FILTER (WHERE rp.selectedRace = '') AS empty_race_count,
        COUNT(*) FILTER (
            WHERE rp.selectedRace IN ('BWTe', 'BWZe', 'BWPr')
        ) AS bw_race_count,
        rm.initData.gameDescription.maxPlayers AS max_players,
        rm.initData.gameDescription.gameOptions.observers AS observer_setting
    FROM replay_players_raw rp
    JOIN replays_meta_raw rm ON rp.filename = rm.filename
    GROUP BY rp.filename, max_players, observer_setting
)
SELECT
    filename,
    player_row_count,
    standard_race_count,
    decisive_count,
    win_count,
    loss_count,
    undecided_count,
    tie_count,
    empty_race_count,
    bw_race_count,
    max_players,
    observer_setting,
    CASE
        WHEN player_row_count = 2
             AND decisive_count = 2
             AND win_count = 1
             AND loss_count = 1
        THEN 'true_1v1_decisive'
        WHEN player_row_count < 2
        THEN 'non_1v1_too_few_players'
        WHEN player_row_count > 2
        THEN 'non_1v1_too_many_players'
        WHEN player_row_count = 2
             AND (undecided_count > 0 OR tie_count > 0)
        THEN 'true_1v1_indecisive'
        ELSE 'non_1v1_other'
    END AS classification
FROM per_replay
ORDER BY classification, filename
"""

classification_df = conn.execute(sql_queries["replay_classification"]).fetch_df()
print(f"=== Replay classification ===")
class_summary = classification_df["classification"].value_counts()
print(class_summary.to_string())
print(f"\nTotal classified: {len(classification_df)} (expected: {RM_TOTAL_ROWS})")
assert len(classification_df) == RM_TOTAL_ROWS, (
    f"Classification count mismatch: {len(classification_df)} != {RM_TOTAL_ROWS}"
)
```

**Cell 15 -- classification summary with detail counts:**
```python
sql_queries["classification_summary"] = """
-- Summary aggregation over the per-replay classification
-- (derived from the replay_classification CTE above, re-executed for clarity)
WITH per_replay AS (
    SELECT
        rp.filename,
        COUNT(*) AS player_row_count,
        COUNT(*) FILTER (WHERE rp.result IN ('Win', 'Loss')) AS decisive_count,
        COUNT(*) FILTER (WHERE rp.result = 'Win') AS win_count,
        COUNT(*) FILTER (WHERE rp.result = 'Loss') AS loss_count,
        COUNT(*) FILTER (WHERE rp.result = 'Undecided') AS undecided_count,
        COUNT(*) FILTER (WHERE rp.result = 'Tie') AS tie_count,
        COUNT(*) FILTER (WHERE rp.selectedRace = '') AS empty_race_count,
        rm.initData.gameDescription.maxPlayers AS max_players
    FROM replay_players_raw rp
    JOIN replays_meta_raw rm ON rp.filename = rm.filename
    GROUP BY rp.filename, max_players
),
classified AS (
    SELECT *,
        CASE
            WHEN player_row_count = 2
                 AND decisive_count = 2
                 AND win_count = 1
                 AND loss_count = 1
            THEN 'true_1v1_decisive'
            WHEN player_row_count < 2
            THEN 'non_1v1_too_few_players'
            WHEN player_row_count > 2
            THEN 'non_1v1_too_many_players'
            WHEN player_row_count = 2
                 AND (undecided_count > 0 OR tie_count > 0)
            THEN 'true_1v1_indecisive'
            ELSE 'non_1v1_other'
        END AS classification
    FROM per_replay
)
SELECT
    classification,
    COUNT(*) AS replay_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS pct,
    MIN(player_row_count) AS min_players,
    MAX(player_row_count) AS max_players_actual,
    SUM(empty_race_count) AS total_empty_race_rows
FROM classified
GROUP BY classification
ORDER BY replay_count DESC
"""

summary_df = conn.execute(sql_queries["classification_summary"]).fetch_df()
print("=== Classification summary ===")
print(summary_df.to_string(index=False))
```

The `true_1v1_decisive` criterion is strict and verifiable:
- Exactly 2 player rows per replay
- Exactly 1 Win and 1 Loss (decisive outcome)
- No requirement on selectedRace (a player can have empty selectedRace and still
  be a legitimate Random player with a resolved race post-game)
- No requirement on max_players (lobby slots can exceed player count)

The `true_1v1_indecisive` category captures replays that ARE genuine 1v1 matches
(exactly 2 player rows) but lack a decisive Win/Loss outcome (Undecided or Tie).
These are excluded from the prediction pipeline because they have no usable
prediction target -- not because of a game-format issue. The thesis-relevant
population is `true_1v1_decisive`.

**Verification:**
- classification_df has exactly 22,390 rows.
- All classification values are one of: `true_1v1_decisive`, `non_1v1_too_few_players`,
  `non_1v1_too_many_players`, `true_1v1_indecisive`, `non_1v1_other`.
- summary_df replay_count sums to 22,390.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

---

### T08 -- Artifact Assembly (JSON + MD)

**Objective:** Assemble all profiling results into the JSON and markdown artifacts
with all SQL queries verbatim (I6).

**Instructions:**

**Cell 16 -- JSON artifact assembly:**
```python
# Build JSON artifact
artifact = {
    "step": "01_03_02",
    "dataset": "sc2egset",
    "total_replay_count": int(RM_TOTAL_ROWS),
    "total_player_rows": int(RP_TOTAL_ROWS),
    "players_per_replay_distribution": players_per_replay_df.to_dict(orient="records"),
    "max_players_distribution": max_players_df.to_dict(orient="records"),
    "observer_setting_distribution": observer_df.to_dict(orient="records"),
    "max_players_vs_actual_cross_tab": cross_tab_df.to_dict(orient="records"),
    "empty_selectedRace_analysis": {
        "total_rows": len(empty_race_df),
        "unique_replays": int(empty_race_df["filename"].nunique()),
        "players_per_replay_distribution": (
            empty_race_df["players_per_replay"]
            .value_counts()
            .sort_index()
            .to_dict()
        ),
        "result_distribution": (
            empty_race_df["result"].value_counts().to_dict()
        ),
        "race_resolved_distribution": (
            empty_race_df["race"].value_counts().to_dict()
        ),
        "apm_stats": {
            k: float(v)
            for k, v in empty_race_df["APM"].describe().to_dict().items()
        },
    },
    "bw_race_analysis": {
        "total_rows": len(bw_df),
        "detail": bw_df.to_dict(orient="records"),
    },
    "undecided_tie_analysis": {
        "total_rows": len(undecided_df),
        "unique_replays": int(undecided_df["filename"].nunique()),
        "players_per_replay_distribution": (
            undecided_df["players_per_replay"]
            .value_counts()
            .sort_index()
            .to_dict()
        ),
    },
    "replay_classification": {
        "summary": summary_df.to_dict(orient="records"),
        "true_1v1_decisive_count": int(
            summary_df.loc[
                summary_df["classification"] == "true_1v1_decisive", "replay_count"
            ].iloc[0]
        ),
        "true_1v1_indecisive_count": int(
            summary_df.loc[
                summary_df["classification"] == "true_1v1_indecisive", "replay_count"
            ].sum()
        ),
    },
    "non_1v1_replay_detail": non_2p_detail_df.to_dict(orient="records"),
    "classification_criteria": {
        "true_1v1_decisive": "player_row_count == 2 AND win_count == 1 AND loss_count == 1",
        "non_1v1_too_few_players": "player_row_count < 2",
        "non_1v1_too_many_players": "player_row_count > 2",
        "true_1v1_indecisive": (
            "player_row_count == 2 AND (undecided_count > 0 OR tie_count > 0)"
        ),
        "non_1v1_other": "all remaining (should be 0 if classification is exhaustive)",
    },
    "standard_races_used": STANDARD_RACES,
    "sql_queries": sql_queries,
}

# Validation
true_1v1_decisive_count = artifact["replay_classification"]["true_1v1_decisive_count"]
true_1v1_indecisive_count = artifact["replay_classification"]["true_1v1_indecisive_count"]
total_classified = sum(
    r["replay_count"] for r in artifact["replay_classification"]["summary"]
)
assert total_classified == RM_TOTAL_ROWS, (
    f"Classification total {total_classified} != {RM_TOTAL_ROWS}"
)
print(f"true_1v1_decisive: {true_1v1_decisive_count} / {RM_TOTAL_ROWS} "
      f"({100.0 * true_1v1_decisive_count / RM_TOTAL_ROWS:.2f}%)")
print(f"true_1v1_indecisive: {true_1v1_indecisive_count} / {RM_TOTAL_ROWS} "
      f"({100.0 * true_1v1_indecisive_count / RM_TOTAL_ROWS:.2f}%)")

json_path = artifact_dir / "01_03_02_true_1v1_profile.json"
with open(json_path, "w") as f:
    json.dump(artifact, f, indent=2, default=str)
print(f"JSON artifact written to: {json_path}")
```

**Cell 17 -- markdown artifact:**
```python
md_lines = [
    "# Step 01_03_02 -- True 1v1 Match Identification",
    "",
    "**Dataset:** sc2egset",
    "**Phase:** 01 -- Data Exploration",
    "**Pipeline Section:** 01_03 -- Systematic Data Profiling",
    f"**Total replays:** {RM_TOTAL_ROWS}",
    f"**Total player rows:** {RP_TOTAL_ROWS}",
    "",
    "---",
    "",
    "## Players-per-replay distribution",
    "",
    "```sql",
    sql_queries["players_per_replay"].strip(),
    "```",
    "",
    players_per_replay_df.to_markdown(index=False),
    "",
    "## max_players lobby setting distribution",
    "",
    "```sql",
    sql_queries["max_players_distribution"].strip(),
    "```",
    "",
    max_players_df.to_markdown(index=False),
    "",
    "## Observer setting distribution",
    "",
    "```sql",
    sql_queries["observer_setting_distribution"].strip(),
    "```",
    "",
    observer_df.to_markdown(index=False),
    "",
    "## max_players vs actual player row count (cross-tabulation)",
    "",
    "```sql",
    sql_queries["max_players_vs_actual"].strip(),
    "```",
    "",
    cross_tab_df.to_markdown(index=False),
    "",
    "## Empty selectedRace analysis",
    "",
    f"Total rows with selectedRace = '': {len(empty_race_df)}",
    f"Unique replays: {empty_race_df['filename'].nunique()}",
    "",
    "```sql",
    sql_queries["empty_race_profile"].strip(),
    "```",
    "",
    "### Result distribution for empty-selectedRace rows",
    "",
    empty_race_df["result"].value_counts().to_frame().to_markdown(),
    "",
    "### Race (resolved) distribution for empty-selectedRace rows",
    "",
    empty_race_df["race"].value_counts().to_frame().to_markdown(),
    "",
    "## BW race variant context",
    "",
    "```sql",
    sql_queries["bw_race_context"].strip(),
    "```",
    "",
    bw_df.to_markdown(index=False),
    "",
    "## Undecided/Tie replay context",
    "",
    "```sql",
    sql_queries["undecided_tie_1v1_context"].strip(),
    "```",
    "",
    f"Total Undecided/Tie rows: {len(undecided_df)}",
    f"Unique replays: {undecided_df['filename'].nunique()}",
    "",
    "## Replay classification summary",
    "",
    "```sql",
    sql_queries["classification_summary"].strip(),
    "```",
    "",
    summary_df.to_markdown(index=False),
    "",
    "### Classification criteria",
    "",
    "| Classification | Criterion |",
    "|----------------|-----------|",
    "| true_1v1_decisive | player_row_count == 2 AND win_count == 1 AND loss_count == 1 |",
    "| non_1v1_too_few_players | player_row_count < 2 |",
    "| non_1v1_too_many_players | player_row_count > 2 |",
    "| true_1v1_indecisive | player_row_count == 2 AND (undecided_count > 0 OR tie_count > 0) |",
    "| non_1v1_other | Residual category (should be 0) |",
    "",
    f"**true_1v1_decisive replays: {true_1v1_decisive_count} / {RM_TOTAL_ROWS} "
    f"({100.0 * true_1v1_decisive_count / RM_TOTAL_ROWS:.2f}%)**",
    "",
    "The `true_1v1_indecisive` category captures replays that ARE genuine 1v1 matches"
    " (exactly 2 player rows) but lack a decisive Win/Loss outcome (Undecided or Tie).",
    "These are excluded from the prediction pipeline because they have no usable"
    " prediction target -- not because of a game-format issue. The thesis-relevant"
    " population is `true_1v1_decisive`.",
    "",
    "---",
    "",
    "## Observations and thesis implications",
    "",
    "1. **Observation:** [to be filled based on execution results]",
    "   **Thesis implication:** [to be filled]",
    "   **Next action:** Feed classification to 01_04 (Data Cleaning).",
    "",
    "---",
    "",
    "*All SQL queries above are the exact code used to produce these results (I6).*",
    f"*Standard races {STANDARD_RACES} derived from 01_02_04 census (I7).*",
    "*This step classifies replays but does not drop any rows (I9).*",
]

md_path = artifact_dir / "01_03_02_true_1v1_profile.md"
with open(md_path, "w") as f:
    f.write("\n".join(md_lines))
print(f"MD artifact written to: {md_path}")
```

Note: The "Observations and thesis implications" section template is
intentionally left with placeholders. The executor must fill these in based on
the actual execution results. The observations must follow the structure:
observation (what the data shows) -> thesis implication (what it means for the
prediction task) -> next action (what the cleaning step should do about it).

**Verification:**
- JSON artifact exists and contains: `true_1v1_decisive_count`, `true_1v1_indecisive_count`,
  `total_replay_count`, `observer_setting_distribution` (new finding),
  `players_per_replay_distribution`, `max_players_distribution`, `replay_classification`,
  `sql_queries`.
- MD artifact exists and contains all SQL queries verbatim, all tables, and the
  comparison summary.
- `true_1v1_decisive_count + true_1v1_indecisive_count + sum(non_1v1 categories) == 22,390`.

**File scope:**
- `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_02_true_1v1_identification.py`

**Read scope:**
- All dataframes from T03-T07 (used in artifact assembly)

---

### T09 -- STEP_STATUS Update and Research Log Entry

**Objective:** Update STEP_STATUS.yaml and add a research log entry.

**Instructions:**
1. Add to `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml`:
```yaml
  "01_03_02":
    name: "True 1v1 Match Identification"
    pipeline_section: "01_03"
    status: complete
    completed_at: "2026-04-16"
```

2. Add a research log entry to
   `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md`
   at the top (reverse chronological), following the format of the 01_03_01 entry:

```markdown
## 2026-04-16 -- [Phase 01 / Step 01_03_02] True 1v1 Match Identification

**Category:** A (science)
**Dataset:** sc2egset
**Step scope:** profiling -- replay-level 1v1 classification
**Artifacts produced:**
- `reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json`
- `reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.md`

### What

[To be filled by executor with actual findings. Must include: true_1v1 count,
total replays, non-1v1 category breakdown, empty-selectedRace findings,
max_players interpretation, observer setting interpretation.]

### Key finding

[To be filled: is the dataset already exclusively 1v1? What is the actual
attrition from applying the true_1v1 filter?]

### Implications for data cleaning (01_04)

[To be filled: which replays will need to be excluded, and how many player rows
does that represent?]
```

Note: The research log entry template has placeholders because the actual
findings depend on execution. The executor must fill them in with the concrete
numbers from the notebook output.

**Verification:**
- STEP_STATUS.yaml contains `01_03_02` entry with status `complete`.
- Research log has a dated entry at the top.

**File scope:**
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml`
- `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md`

---

## File Manifest

| File | Action | Task |
|------|--------|------|
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/ROADMAP.md` | UPDATE | T01 |
| `sandbox/sc2/sc2egset/01_exploration/03_profiling/01_03_02_true_1v1_identification.py` | CREATE | T02-T08 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.json` | CREATE | T08 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.md` | CREATE | T08 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/STEP_STATUS.yaml` | UPDATE | T09 |
| `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md` | UPDATE | T09 |

## Gate Condition

**Artifact check:** Both `.json` and `.md` files exist at
`reports/artifacts/01_exploration/03_profiling/01_03_02_true_1v1_profile.*`
and are non-empty.

**Continue predicate:** JSON artifact contains all of:
- `true_1v1_decisive_count` (integer)
- `true_1v1_indecisive_count` (integer)
- `total_replay_count` (integer, == 22,390)
- `players_per_replay_distribution` (list with at least 1 entry)
- `max_players_distribution` (list with 5 entries per 01_03_01 cardinality)
- `observer_setting_distribution` (list)
- `replay_classification.summary` (list)
- `sql_queries` (dict with all 9+ queries)
- `true_1v1_decisive_count + true_1v1_indecisive_count + sum(non_1v1 categories) == 22,390`

The thesis-relevant population is `true_1v1_decisive` -- these replays pass to 01_04
as the viable pool for the prediction pipeline. `true_1v1_indecisive` is documented
for completeness but excluded from the pipeline (missing prediction target, not a
game-format issue).

**Halt predicate:** Any artifact is missing, classification totals do not sum
to 22,390, or `non_1v1_other` count > 0 (would indicate the classification
logic has a gap).

## Out of Scope

- Dropping any rows from DuckDB tables (deferred to 01_04 -- Data Cleaning).
- Creating derived tables or views (deferred to 01_04 or Phase 02).
- Analysis of in-game event data (game_events, tracker_events, message_events).
- Cross-game comparison with AoE2 (AoE2 has no observer/team-game issue since
  its API returns only 1v1 ranked matches).
- Identity resolution (player nickname deduplication) -- separate step.

## Open Questions

1. **Will `non_1v1_other` be non-zero?** The CASE-WHEN logic in T07 should be
   exhaustive: every replay is either < 2 players, > 2 players, == 2 players
   with decisive result, or == 2 players without decisive result. But if there
   are replays with exactly 2 players, 2 decisive results, but not exactly 1 Win
   + 1 Loss (e.g., 2 Wins or 2 Losses -- data corruption), they would fall into
   `non_1v1_other`. This would be a significant finding.

2. **Are the 1,110 empty-selectedRace rows all "Random" players?** If `race`
   (resolved post-game) shows standard races for all 1,110 rows while
   `selectedRace` is empty, this is likely a representation of "Random"
   selection where the pre-game choice was intentionally left blank in the
   replay data. The 10 explicit `selectedRace='Rand'` rows may represent a
   different code path in different SC2 versions.

3. **How many replays will the true_1v1 filter actually remove?** Based on
   the playerID distribution (37 extra rows = ~11-37 non-2-player replays) plus
   13 Undecided/Tie replays, the expected attrition is small (< 50 replays out
   of 22,390 = < 0.22%). But execution will provide the exact count.
```

---

**Critique gate:** For Category A, adversarial critique is required before execution begins. Dispatch `reviewer-adversarial` to produce `planning/current_plan.critique.md`.
