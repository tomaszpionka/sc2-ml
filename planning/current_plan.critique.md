# Adversarial Critique: Plan 01_02_02 — DuckDB Ingestion

## Verdict: APPROVE

Critical Issue #1 (filename provenance mismatch) resolved by design decision
(2026-04-13): all `filename` columns store paths relative to `raw_dir`, not
absolute paths. See plan "Filename strategy" section. No blockers remain.
Significant concerns are addressable inline during execution.

---

## Critical Issues (must fix before execution)

~~1. Cross-table filename provenance mismatch~~ — **RESOLVED BY DESIGN (2026-04-13).**
All `filename` columns now store paths relative to `raw_dir` (e.g.
`TournamentX/TournamentX_data/match.SC2Replay.json`). Stream 1 strips the
prefix in SQL via `substr(filename, {raw_dir_prefix_len})`; Stream 2 uses
`str(fpath.relative_to(raw_dir))`; map aliases use
`str(mapping_file.relative_to(raw_dir))`. Cross-stream join is reliable by
construction. T04 adds assertions that no `filename` value starts with `/`.

---

## Significant Concerns (should address)

1. **T01 rename scope under-specified; upstream naming inconsistency.**

   The T01 grep verification does not specify the path scope in the body of
   the task (only in gate condition #7). The executor could run repo-wide greps
   and get false positives from ROADMAP.md, research_log.md, and 01_02_01
   artifacts. Specify `src/ tests/` explicitly in T01's verification block.

   More importantly: the 01_02_01 artifact refers to the table as
   `replays_metadata_raw` (with an extra `data`), while the plan uses
   `replays_meta_raw`. This is a deliberate deviation from the upstream
   recommendation. The research log entry (T05) must document this decision
   explicitly so the examiner can trace the name change.

2. **Cross-table integrity check tests only one join direction.**

   The plan's SQL in T02 section 4b checks for `replay_players_raw` rows
   orphaned from `replays_meta_raw`. It does not check the reverse: replays
   in `replays_meta_raw` with zero rows in `replay_players_raw`. This can
   happen silently because `load_replay_players_raw` skips files with
   `json.JSONDecodeError`/`OSError` and skips replays where
   `ToonPlayerDescMap` is absent or empty. Add a reverse-direction check
   and report `orphan_meta_files` in the artifact.

3. **`map_aliases_raw` loads all 70 identical files without justification.**

   The 01_02_01 artifact confirms all 70 mapping files are identical (1,488
   keys each). The plan creates 104,160 rows (70 × 1,488) where 1,488 would
   suffice. This is defensible for provenance tracing, but the thesis must
   justify it. The research log entry (T05) should record the decision:
   "All 70 files loaded to preserve per-tournament provenance, not because
   the files differ."

4. **`batch_size=500` in `load_replay_players_raw` is a magic number (Invariant I7).**

   The default `batch_size=500` (ingestion.py:261) has no documented derivation.
   Since it is an implementation constant (not a scientific parameter), an inline
   comment with the rationale suffices: chosen to balance memory overhead and
   DuckDB insert throughput; ~25K tuples per batch at this replay size.

5. **`_DEFAULT_MAX_OBJECT_SIZE = 536_870_912` headroom unvalidated against full corpus.**

   The 01_02_01 sample found the largest file at 143.1 MB — 512 MB provides
   3.6× headroom. But the 01_02_01 sample covers only 7 files. If the full
   22,390-file corpus contains outliers above 512 MB, DuckDB will error. The
   plan's assumption section (plan line 49) mentions "100% on sampled files" but
   does not flag this as a residual risk for T03. The executor should log the
   actual max file size encountered during T03 and record it in the research log.

---

## Minor Notes (optional fixes)

1. **3600s timeout (T03) is tight but probably sufficient.**

   Linear extrapolation from 01_02_01 batch timing: `load_replay_players_raw`
   at ~50ms per file × 22,390 files ≈ 1,120s. Adding `load_replays_meta_raw`
   (~580s extrapolated) plus validation cells, total approaches 3,600s. If
   the notebook times out, the correct fix is to increase the timeout, not to
   abandon Python-based extraction. Note this in T03 instructions.

2. **Unused import of `extract_events_to_parquet` in notebook.**

   If section 5 remains commented out, the import of `extract_events_to_parquet`
   at the top of the notebook is unused and may trigger a linter warning. The
   executor should either remove it or add `# noqa: F401` (since it is
   intentionally kept for future use).

3. **This file replaces a stale critique from a prior plan iteration.**

   The prior `planning/current_plan.critique.md` discussed AoE2 datasets
   (aoe2companion, aoestats) and was entirely irrelevant to the current plan.
   This file supersedes it.

---

## Scientific Invariant Audit

| # | Invariant | Status | Reasoning |
|---|-----------|--------|-----------|
| 1 | Per-player split | N/A | No splitting at Phase 01. |
| 2 | Canonical nickname | N/A | `toon_id` and `nickname` stored as-is; identity resolution deferred to Phase 02 (correctly noted in Out of Scope). |
| 3 | Temporal < T | SATISFIED | No features computed; raw data ingested as-is. No temporal leakage vector. |
| 4 | Prediction target | N/A | No predictions at this step. |
| 5 | Symmetric treatment | N/A | Both players extracted identically by `_extract_player_row`; no asymmetric treatment. |
| 6 | Reproducibility | AT RISK | The existing skeleton writes `"See ingestion.py for all SQL constants"` rather than inlining the SQL. Invariant I6 requires the literal code, not a reference. T02 instruction #6 correctly mandates inline SQL in the artifact — executor must ensure this overrides the current skeleton pattern. |
| 7 | No magic numbers | AT RISK | `batch_size=500` and `max_object_size=512 MB` lack documented derivation. See Significant Concerns #4 and #5. `filename` provenance is correctly required. |
| 8 | Cross-game protocol | SATISFIED | `*_raw` naming convention and three-stream strategy parallel the AoE2 pipeline. |
| 9 | Step scope | SATISFIED | Plan limits conclusions to ingestion success, row counts, column types, and NULL rates. No content-level analysis. |

---

## Gate Condition Assessment

| # | Gate Condition | Status | Assessment |
|---|---------------|--------|------------|
| 1 | Three `*_raw` tables with non-zero row counts | TESTABLE | Expected counts (~22,390 / ~44,780 / ~104,160) are estimates; treat as lower-bound sanity checks, not exact targets. |
| 2 | `filename` column in all three tables | TESTABLE | DESCRIBE query suffices. |
| 3 | `ToonPlayerDescMap` is VARCHAR | TESTABLE | information_schema query or DESCRIBE. |
| 4 | `orphan_player_files = 0` | TESTABLE BUT INCOMPLETE | One join direction only. Does not catch orphan `replays_meta_raw` entries. See Significant Concern #2. |
| 5 | Artifact files non-empty | AMBIGUOUS | Trivially satisfiable with a near-empty JSON. T02's detailed enrichment spec mitigates this, but the gate condition itself is weak. Consider adding a minimum-key check. |
| 6 | All tests pass | TESTABLE | Standard pytest gate. |
| 7 | No stale table names in `src/ tests/` | TESTABLE | Valid grep check — but executor must scope to `src/ tests/` to avoid false positives in docs (see Significant Concern #1). |
| 8 | `STEP_STATUS.yaml` updated | TESTABLE | Trivially satisfiable; correct. |
| 9 | `research_log.md` entry exists | TESTABLE | T05 template is detailed enough to prevent a vacuous entry. |

---

## Recommendation

Critical Issue #1 resolved by design. No blockers.

**During execution,** the executor should:
- Add the reverse-direction orphan check (Significant Concern #2) to T02 section 4b.
- Document the `replays_meta_raw` vs `replays_metadata_raw` naming deviation from
  01_02_01 in the research log (Significant Concern #1).
- Add inline derivation comments for `batch_size=500` and `max_object_size` (Significant
  Concerns #4 and #5; Invariant I7).
- Replace `"See ingestion.py"` references in the artifact builder with inline SQL (Invariant I6).
- Remove or `# noqa` the unused `extract_events_to_parquet` import in the notebook.

---

## Second-Pass Review (2026-04-13) — artifact-grounded

### Verdict: APPROVE WITH CONDITIONS

One new blocker found by reading the actual notebook source. Two significant
concerns elevated from first pass based on notebook content. All other
first-pass findings stand.

### Critical Issues

**1. [BLOCKER] `db.close()` at notebook line 135 will break T02 validation sections.**

File: `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.py`, line 135.

The skeleton closes the DuckDB connection after section 4 (`db.close()` at
line 135), before section 5 (commented events) and section 6 (artifacts).
The plan instructs T02 to add sections 4b/4c/4d "after existing section 4" —
if inserted after line 134 but before line 135, they would run before close
and work. But if inserted after `db.close()`, they raise `ConnectionException`.

**Fix (added to T02 in plan):** Move `db.close()` from line 135 to after
section 6 (artifact writing). The connection is not needed in section 6
(which only reads Python variables already computed), but moving it to the
end makes the execution order unambiguous and keeps all validation queries
safe regardless of where they are inserted.

**2. [BLOCKER] Stale `.ipynb` cell outputs from prior execution contaminate T02/T03.**

File: `sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.ipynb`.

The notebook was previously executed. Its `.ipynb` contains cell outputs
showing old table names (`replays_meta`, `replay_players`, `map_aliases`)
and prior row counts. When the executor modifies the `.py` source and syncs
to `.ipynb` via jupytext, jupytext updates source cells but preserves
existing outputs in unchanged cells. The result is a mixed-state notebook:
new source cells (with `_raw` names) alongside stale outputs (with bare names).
This creates a context-leak risk where the executor or a subsequent reader
cannot distinguish actual execution results from stale artifacts.

**Fix (added to T00 in plan):** Clear all `.ipynb` outputs before any T01/T02
modifications:
```
source .venv/bin/activate && poetry run jupyter nbconvert \
  --clear-output --inplace \
  sandbox/sc2/sc2egset/01_exploration/02_eda/01_02_02_duckdb_ingestion.ipynb
```

### Significant Concerns (new or elevated from first pass)

**3. `load_all_raw_tables` must NOT be renamed — plan instruction is ambiguous.**

T02 instruction #1 says "Update all references to old table names and function
names to the `*_raw` variants." The wrapper function `load_all_raw_tables`
keeps its name (T01 only renames the three individual loaders). The notebook
imports `load_all_raw_tables` at line 38 — this import must NOT change. The
plan must explicitly exempt `load_all_raw_tables` from the rename instruction
to prevent the executor from over-applying it.

**4. Stale table names in notebook markdown and artifact builder (lines 47–48, 188–201).**

The skeleton's markdown cell (line 47–48) reads:
`- \`replays_meta\` -- one row per replay...`
The artifact markdown builder (lines 188–201) uses bare names
(`**replays_meta**:`, `**replay_players**:`, `**map_aliases**:`). T02
instruction #1 covers SQL strings but does not explicitly call out these
prose/markdown strings. If missed, the artifact will carry stale table names,
violating Invariant I6.

### Empirical Verifications (challenges from second-pass brief)

| Challenge | Result |
|-----------|--------|
| I10 `substr` correctness vs `pathlib.relative_to` | VERIFIED — produces identical strings including `tmp_path` fixtures |
| `_extract_player_row` tuple order vs DDL column order | VERIFIED — 25 columns, positionally aligned |
| `json_each` correctness for MAP iteration | VERIFIED — `SELECT u.key, u.value FROM json_each(?) u` correct in DuckDB 1.5.1 |
| `_REPLAYS_META_QUERY` columns vs schema discovery | VERIFIED — 8 of 11 root keys selected; `trackerEvtsErr` spelling matches actual field name |
| T04 relative-path assertions on fixtures | VERIFIED — not vacuous; exercises actual stripping logic |
| Gate condition row count defensibility | SOUND — 22,390 from 01_01_01 exact count; ±variance acceptable |

### Invariant Audit (changes from first pass)

| # | Change | Reason |
|---|--------|--------|
| 6 | AT RISK → AT RISK (elevated) | Stale "See ingestion.py" applies to ALL section 6 text, not just new validation checks. Plan updated to mandate full replacement. |
| 10 | Added | SOUND — `substr` implementation verified empirically. |

### Recommendation

**Two blockers must be addressed in T00/T02 (plan already updated):**
1. Clear `.ipynb` outputs in T00 before any notebook modification.
2. Move `db.close()` to end of notebook in T02 (after section 6).

**Executor must also:**
- Explicitly exempt `load_all_raw_tables` from the rename sweep (not just individual loaders).
- Update all prose/markdown strings referencing bare table names (lines 47–48, 188–201), not only SQL strings.
