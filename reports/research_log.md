# Research Log

Thesis: "A comparative analysis of methods for predicting game results
in real-time strategy games, based on the examples of StarCraft II and
Age of Empires II."

Reverse chronological entries.

> This log continues from `reports/_archive/research_log_pre_notebook_sandbox.md`,
> covering all work through 2026-04-07. The pivot to a notebook-based exploration
> sandbox is documented in the first entry below. Pre-pivot entries remain citable
> as methodology-history but not as findings sources for Phase 1+.

---

## 2026-04-08 — [PHASE 0 / Step 0.9] Map alias file ingestion — raw_map_alias_files table

**Category:** A (science)
**Branch:** `feat/phase0-map-alias-ingestion`
**Dataset:** sc2egset
**Artifacts produced:**
- `sandbox/sc2/sc2egset/00_99_post_rebuild_verification.ipynb` (executed notebook)
- `sandbox/sc2/sc2egset/00_99_post_rebuild_verification.py` (jupytext source)
- `src/rts_predict/sc2/reports/sc2egset/artifacts/00_99_post_rebuild_verification.md` (report)

### What

Replaced the old `load_map_translations()` / `map_translation` table design with
`ingest_map_alias_files()` / `raw_map_alias_files` table. The old approach merged
all per-tournament alias JSON files via `dict.update()` (filesystem-order-dependent)
and stored flat triplets (tournament_dir, foreign_name, english_name). The new
approach stores one row per alias file, with the raw JSON verbatim plus SHA1
checksum, `n_bytes`, and `ingested_at`. Downstream Phase 1 work will parse the JSON
via DuckDB json_extract / ->> operators.

Also deleted `create_ml_views()` and `_MATCHES_VIEW_QUERY` from `processing.py`
and removed `validate_map_translation_coverage()` from `audit.py`. After this PR,
`poetry run sc2 init` produces two raw tables only: `raw` and `raw_map_alias_files`.
ML views (`flat_players`, `matches_flat`) are deferred to Phase 1/2 once cleaning
rules and race normalisation are established.

### Architectural change: ML views removed from Phase 0

**What was removed:** `create_ml_views()` and `_MATCHES_VIEW_QUERY` from
`processing.py`; the corresponding call and imports in `cli.py`.

**Why:** These views depended on `map_translation` (now superseded) and applied
race normalisation and map name translation — cleaning decisions that belong to
Phase 1/2, not Phase 0 ingestion.

**Where the replacement will live:** Phase 2 (player identity resolution) will
establish canonical player/race references; Phase 3 (games table construction)
will rebuild `flat_players` and `matches_flat` with correct cleaning rules.

**Developer/notebook impact:** Any notebook or script that previously called
`create_ml_views(con)` or queried `flat_players`/`matches_flat` must be updated
in Phase 2/3. The `raw_enriched` view (adds `tournament_dir`, `replay_id`) is
still created by `create_raw_enriched_view(con)` and remains available.

### Verification report

`src/rts_predict/sc2/reports/sc2egset/artifacts/00_99_post_rebuild_verification.md`

---

## 2026-04-08 — [PHASE 1 / Step 1.8] SC2 game settings and replay field completeness audit (notebook re-run)

**Category:** A (science)
**Dataset:** sc2egset
**Artifacts produced:** `sandbox/sc2/sc2egset/01_08_game_settings_audit.ipynb`, `sandbox/sc2/sc2egset/01_08_game_settings_audit.py`, `src/rts_predict/sc2/reports/sc2egset/artifacts/01_08_error_flags_audit.csv` (read; unchanged), `src/rts_predict/sc2/reports/sc2egset/artifacts/01_08_game_settings_audit.md` (original Pattern B report; superseded by notebook)

### What

Re-ran the Step 1.8 game settings and replay field completeness audit in the new
notebook sandbox. The original Step 1.8 report (`src/rts_predict/sc2/reports/sc2egset/artifacts/01_08_game_settings_audit.md`,
2026-04-07) was a Pattern B markdown-only artifact containing embedded SQL but no
backing function in `exploration.py`. The notebook (`sandbox/sc2/sc2egset/01_08_game_settings_audit.ipynb`)
ports all SQL from the original report into executable cells, cross-checks the
results against the original, and adds cell-level interpretation narrative. Seven
sub-steps were audited: game speed (A), handicap (B), error flags (C), game mode
flags (D), random race detection (E), map and lobby metadata (G), and version
consistency (H).

### Why

The original Step 1.8 entry had no backing function in `exploration.py` (Discovery
Gap 1 in `_current_plan.md` A.1). The finding was citable but not reproducible:
the SQL could be re-run manually, but there was no executable artifact — no cell
execution record, no output capture, no cell-level reasoning chain. Scientific
Invariant 6 (query/code co-located with results) required that every finding be
backed by a derivation that can be mechanically re-executed. The notebook restart
closes this gap and demonstrates end-to-end that the sandbox infrastructure
works as designed.

### How (reproducibility)

Notebook: `sandbox/sc2/sc2egset/01_08_game_settings_audit.ipynb` (committed with
cell outputs). Paired `.py` file: `sandbox/sc2/sc2egset/01_08_game_settings_audit.py`
(jupytext percent-format, diff-review artifact).

To re-execute from a fresh kernel:

```bash
poetry run jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=600 \
    sandbox/sc2/sc2egset/01_08_game_settings_audit.ipynb
```

Key SQL examples (game speed and mode flag queries):

```sql
-- Query A1: game speed from initData
SELECT initData->'$.gameDescription'->>'$.gameSpeed' AS init_game_speed, COUNT(*) AS n_replays
FROM raw GROUP BY 1 ORDER BY 2 DESC;

-- Query D1: game mode flags
SELECT
    initData->'$.gameDescription'->'$.gameOptions'->>'$.noVictoryOrDefeat' AS no_victory,
    initData->'$.gameDescription'->'$.gameOptions'->>'$.competitive' AS competitive,
    initData->'$.gameDescription'->'$.gameOptions'->>'$.cooperative' AS cooperative,
    initData->'$.gameDescription'->'$.gameOptions'->>'$.practice' AS practice,
    COUNT(*) AS n_replays
FROM raw GROUP BY 1, 2, 3, 4 ORDER BY 5 DESC;
```

The error flags sub-step (C) loads the archived CSV
(`src/rts_predict/sc2/reports/sc2egset/artifacts/01_08_error_flags_audit.csv`) rather than
re-running the original ZIP-archive scan (that scan required direct filesystem
access to 70 ZIP archives and produced a zero-row CSV; the result is confirmed
by reading the artifact). All other sub-steps execute SQL directly against the
DuckDB `raw` table via `get_notebook_db("sc2", "sc2egset")`.

### Findings

- **Sub-step A (Game speed):** 22,390/22,390 replays at "Faster" speed. Both
  `initData` and `details` fields agree. 0 mismatches. PASS.
- **Sub-step B (Handicap):** 44,815/44,817 player slots at handicap = 100. 2
  exceptional slots at handicap = 0 are phantom/anonymous entries (empty toon
  key `""`, zero APM, zero MMR, `color.a = 0`) in replays from
  `2017_IEM_XI_World_Championship_Katowice` and `2019_HomeStory_Cup_XIX`. NEAR-PASS.
- **Sub-step C (Error flags):** `01_08_error_flags_audit.csv` contains 0 data rows.
  `gameEventsErr`, `messageEventsErr`, `trackerEvtsErr` = false for all 22,390
  replays. PASS.
- **Sub-step D (Game mode flags):** 22,387/22,390 replays have the expected all-false
  flag combination. 3 replays (`competitive=true`, `amm=true`, `battleNet=true`)
  are Battle.net ladder replays accidentally bundled with the IEM Katowice 2017
  tournament directory. NEAR-PASS. Phase 6 cleaning rule C-D1 required.
- **Sub-step E (Random race):** 1,110/44,817 player slots (2.5%) have empty
  `selectedRace` (Random selection). `assigned_race` is the correct race field
  for all modelling purposes. 10 additional slots have explicit `Rand` in
  `selectedRace`. 3 anomalous slots have BW race codes (BWTe, BWPr, BWZe).
  INFORMATIONAL.
- **Sub-step G (Map/lobby metadata):** `maxPlayers` ranges 2–9 (map slot count,
  not player count; 409 replays on >2-slot maps — normal for 1v1 on 4-player-slot
  maps). 17,515 Blizzard maps, 4,875 community maps (21.8%). 100% fog=0, 100%
  `randomRaces=false` (lobby-level toggle), 100% observers=0. PASS.
- **Sub-step H (Version consistency):** 0 mismatches between `header.version` and
  `metadata.gameVersion` across all 22,390 replays. PASS.
- **Numbers vs. original report:** All numbers match the original
  `01_08_game_settings_audit.md` (2026-04-07) exactly. No data has shifted. The
  notebook re-run confirms the original findings are reproducible.
- **This is the first notebook executed end-to-end in the new sandbox.** Execution
  completed without error on a fresh kernel.

### What this means

The SC2EGSet corpus is clean from a game-settings perspective. Game speed is 100%
consistent (Faster), version fields agree, error flags are zero, and fog/observer
settings match expectation. Only two cleaning rules are required downstream: C-D1
(exclude 3 Battle.net ladder replays with `competitive=true`) and C-E1 (flag 3
BW race code slots for manual review). The random-race finding (2.5% of slots)
does not require a cleaning rule but constrains feature engineering: `assigned_race`
must be used, not `selectedRace`, because the latter is null for Random players.

This is also the first demonstration that the notebook sandbox works end-to-end:
`get_notebook_db`, jupytext sync, fresh-kernel nbconvert execution, and the
Category A research log entry cycle all functioned as designed. The infrastructure
is validated for subsequent Phase 1 restarts.

### Decisions taken

- **Use `assigned_race` (`ToonPlayerDescMap.race`) as the race feature in Phase 7,
  not `selectedRace`.** Rationale: `selectedRace` is null for ~2.5% of player
  slots (Random race selection); `assigned_race` is always populated.
- **Phase 6 Cleaning Rule C-D1: exclude replays with `competitive=true`.**
  Rationale: 3 replays are Battle.net ladder replays, not tournament matches.
- **Phase 6 Cleaning Rule C-E1: flag player slots with BW race codes (BWTe, BWPr,
  BWZe) for manual review.** Rationale: 3 anomalous slots, likely IEM Katowice
  2017 legacy artifacts; host replay candidate.
- **Step 1.8 is now citable under the reproducibility invariant.** The notebook
  constitutes the executable derivation required by Scientific Invariant 6.

### Decisions deferred

- **Phase 6 implementation of rules C-D1 and C-E1:** Not in scope for Phase 1.
  Will be addressed when the cleaning pipeline is built.
- **Phase 2 phantom slot handling:** The 2 handicap-0 phantom slots (empty toon
  key) will be excluded naturally during player identity resolution via the
  empty-nickname filter. No separate cleaning rule is added at this stage.
- **BW race code root-cause investigation:** Whether the 3 BWTe/BWPr/BWZe slots
  are from a single host replay or multiple replays was not investigated in this
  step. Deferred to Phase 6 manual review.

### Thesis mapping

- `thesis/THESIS_STRUCTURE.md` Chapter 4 (Data) — dataset quality and cleaning
  pipeline: game speed, error flag, and mode flag audit results feed the
  "data quality" subsection.
- Methodology chapter — "how exploration was conducted" narrative: this entry is
  the first example of the notebook-sandbox workflow applied to a scientific step,
  demonstrating the exploratory-to-citable pipeline.

### Open questions / follow-ups

- Why are 3 Battle.net ladder replays present in the `2017_IEM_XI_World_Championship_Katowice`
  tournament directory of SC2EGSet? Was this a dataset packaging error, or is it
  a known issue documented in the SC2EGSet paper?
- Do the 3 BW race code slots originate from a single replay, or are they spread
  across multiple replays? (Relevant for deciding whether to exclude one replay or
  three separate cleaning actions.)
- Phase 1 Steps 1.1–1.7 and 1.9 notebook restarts are pending. Those steps have
  Pattern A functions in `exploration.py`; the notebooks will call those functions
  and add interpretation narrative.

---

## 2026-04-08 — [PHASE N/A / Chore] Notebook exploration sandbox — tooling, template contract, agent workflow updates

**Category:** C (chore)
**Dataset:** —
**Artifacts produced:** `sandbox/` (directory tree), `sandbox/README.md`, `jupytext.toml`, `sandbox/notebook_config.toml`, `.pre-commit-config.yaml`, `src/rts_predict/common/notebook_utils.py`, `src/rts_predict/common/notebook_utils_test.py`, `reports/_archive/research_log_pre_notebook_sandbox.md`, `src/rts_predict/sc2/reports/sc2egset/SUPERSEDED.md`, `.claude/agents/executor.md` (updated), `.claude/agents/reviewer.md` (updated)

### What

Established a Jupyter notebook exploration sandbox for the thesis codebase.
Key actions:

- Archived the original `reports/research_log.md` to `reports/_archive/research_log_pre_notebook_sandbox.md` and created this fresh log.
- Created `sandbox/sc2/sc2egset/` for SC2EGSet Phase 1 notebooks, with AoE2 placeholders (`sandbox/aoe2/aoe2companion/.gitkeep`, `sandbox/aoe2/aoestats/.gitkeep`).
- Added `jupytext.toml` at repo root (pairs all `sandbox/**/*.ipynb` with `.py:percent` files).
- Added `sandbox/notebook_config.toml` (`[cells] max_lines = 50`, `[execution] timeout_seconds = 600`).
- Implemented `src/rts_predict/common/notebook_utils.py` with `get_notebook_db()` and `get_reports_dir()` and co-located tests.
- Added `.pre-commit-config.yaml` with the jupytext sync hook (`--sync` on `sandbox/**/*.{ipynb,py}`).
- Updated `.claude/agents/executor.md` and `.claude/agents/reviewer.md` with notebook workflow rules.
- Marked Phase 1 SC2EGSet report artifacts as superseded in `src/rts_predict/sc2/reports/sc2egset/SUPERSEDED.md`.
- Executed the Step 1.8 proof-of-concept notebook as the first sandbox run.

### Why

Discovery Section 4 of `_current_plan.md` documented six reproducibility gaps in
the existing exploration workflow. The most critical for Phase 1 restart were:

- **Gap 1 (Pattern B, Step 1.8):** Step 1.8 existed only as markdown with embedded
  SQL — not re-runnable, not testable. No backing function in `exploration.py`.
- **Gap 3 (thin reasoning chains):** Research log entries lacked intermediate query
  results and cell-level interpretation. Only post-hoc summaries were captured.
- **Gap 6 (ephemeral exploration):** No mechanism to capture intermediate executor
  observations. Ad-hoc queries run during investigation were lost.

The notebook sandbox addresses all three gaps structurally: every cell execution is
captured in order with its output; the jupytext `.py` pair provides a clean diff
for review; and Scientific Invariant 6 (query/code co-located with results) is
naturally satisfied by the cell-output pairing. The authoritative design is in
`_current_plan.md` (Phase B).

### How (reproducibility)

The migration was executed in sequence across six specs (spec_01 through spec_06),
each committed atomically on the `chore/notebook-sandbox` branch. The full design
is in `_current_plan.md` (Phase B, sections B.1–B.9). The archived research log
(`reports/_archive/research_log_pre_notebook_sandbox.md`) preserves all pre-pivot
entries verbatim and remains citable as methodology-history.

Key hard rules established by this chore (from `_current_plan.md` B.3 and B.4):

1. No inline function/class definitions in any notebook cell.
2. Cell size cap: `[cells] max_lines = 50` (from `sandbox/notebook_config.toml`).
3. DuckDB connections are read-only by default (`get_notebook_db` helper).
4. Jupytext sync enforced by pre-commit hook and reviewer agent check.

### Findings

N/A — this is an infrastructure chore. No data was analysed; no scientific findings
were produced directly. The Step 1.8 proof-of-concept notebook (documented in the
Category A entry above) validated the toolchain end-to-end: fresh-kernel nbconvert
execution completed without error, jupytext sync ran cleanly, pre-commit hook
verified correctly, and test coverage remained above the 95% threshold.

### What this means

Future exploration work in Phase 1 (Steps 1.1–1.9) and beyond has a structured,
reproducible medium. Every SQL query, every computation, and every interpretation
step is captured in an executable notebook cell, committed with its output, and
linked from a research log entry. The "How (reproducibility)" section of every
future log entry can point at the notebook path rather than inlining all SQL,
reducing the log maintenance burden while preserving the full derivation chain.
The hard rules (no inline definitions, 50-line cap, read-only DB, jupytext sync)
prevent the notebook workflow from drifting back toward the ephemeral ad-hoc
pattern that motivated this chore.

### Decisions taken

- **`sandbox/` at repo root** (not inside `src/rts_predict/`): mirrors the
  `reports/` cross-cutting pattern; does not modify the `ARCHITECTURE.md` game
  package contract. Rationale: notebooks are not source code, data, or reports.
- **Commit both `.ipynb` and `.py` pair:** the `.py` is the diff-review artifact;
  the `.ipynb` is the executable-with-outputs artifact. Uncommitted notebooks
  recreate Gap 6. Rationale: reproducibility requires a persistent record.
- **Research log survives as lightweight index:** each entry points at the notebook
  path under "How (reproducibility)". The 10-section template is unchanged; its
  usage becomes lighter. Rationale: the log provides cross-game chronological
  narrative that notebooks cannot replace.
- **`SUPERSEDED.md` marker (not archive) for Phase 1 artifacts:** the Pattern A
  functions still reference the same paths; moving artifacts would break them.
  Rationale: the `SUPERSEDED.md` lists `will_be_regenerated` / `will_be_replaced`
  semantics per artifact; it is removed after Phase 1 restart completes.
- **Naming convention `{PHASE:02d}_{STEP}_{name}.ipynb`:** mirrors the existing
  report naming pattern for visual correspondence. Rationale: Discovery Section 1.

### Decisions deferred

- **Phase 1 Steps 1.1–1.7 and 1.9 notebook restart:** deferred to subsequent
  notebook work (not in scope for this chore). Those steps have Pattern A functions
  in `exploration.py`; the notebooks will call those functions and add narrative.
- **AoE2 notebook sandbox population:** deferred until AoE2 Phase 1 begins.
  Placeholder directories are in place.
- **Broader pre-commit hook setup beyond jupytext sync:** a separate future thread
  per user decision. The jupytext hook is the only hook added in this chore.
- **Tests tree migration:** a separate chore, already spec'd but explicitly
  deferred (out of scope for this chore).

### Thesis mapping

- Methodology chapter — "how exploration was conducted" narrative: the sandbox
  migration and its rationale (Discovery Section 4 gaps, Pattern B elimination,
  Invariant 6 satisfaction) feed the methodology description of how SC2 Phase 1
  exploration was conducted.
- The archived research log (`reports/_archive/research_log_pre_notebook_sandbox.md`)
  remains citable as methodology-history for the decision to restart Phase 1
  exploration.

### Open questions / follow-ups

- Phase 1 Steps 1.1–1.7 and 1.9 notebook restarts: when these are completed, the
  `SUPERSEDED.md` marker can be removed and the full Phase 1 artifact set will be
  current-authoritative.
- AoE2 notebook sandbox population: to be scheduled when AoE2 Phase 1 begins.

