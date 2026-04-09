# Archive: Pre-Notebook-Reset Phase 0/1 Artifacts

**Archived:** 2026-04-09
**Branch:** `chore/phase1-sc2-archive-pre-reset`

---

## 1. What is this directory

This directory holds every numbered Phase 0 and Phase 1 artifact that existed
under `src/rts_predict/sc2/reports/sc2egset/artifacts/` before the Stage 3b
notebook reset. The files were moved here via `git mv` on 2026-04-09 as part of
Spec 3 (Stage 3a). They are preserved for historical reference and must not be
treated as current or valid results.

---

## 2. Why these were archived

**Stage 1 rebuilt Phase 0 and removed two key components.** The Stage 1 rebuild
replaced the `map_translation` table (a silent-merge structure) with
`raw_map_alias_files` (a row-per-file table), and removed ML view construction
(`create_ml_views`, `_MATCHES_VIEW_QUERY`, `matches_flat`, `flat_players`) from
`init_database`. The database now contains exactly six raw tables. Any artifact
that was generated before this rebuild either referenced a schema that no longer
exists or was produced under assumptions that the rebuild invalidated. The
`00_09_map_translation_coverage.csv` artifact is one direct example: it
describes coverage for a table that was removed.

**Tomasz's decision was to redo all Phase 1 work with notebooks.** Rather than
attempting a per-artifact assessment of which findings might still be valid,
all numbered Phase 0 and Phase 1 artifacts are archived wholesale. Phase 1 will
be redone from scratch using jupytext-paired sandbox notebooks writing to
`artifacts/`, with each step explicitly grounded in the current six-table schema.
This ensures no finding from the pre-rebuild state silently carries forward into
the analysis.

---

## 3. Inventory

The full inventory is in `01_00_phase1_audit_inventory.csv` (one row per
archived artifact, sorted by `artifact_path`).

**Summary counts:**

- Total artifacts archived: 36
- Artifacts referencing deleted symbols (`map_translation`, `load_map_translations`,
  `validate_map_translation_coverage`, `create_ml_views`, `_MATCHES_VIEW_QUERY`,
  `matches_flat`, `flat_players`): 0 (none of the numbered artifacts contained
  these references; the only file containing such references was
  `00_99_post_rebuild_verification.md`, which documents the rebuild itself and
  was explicitly excluded from archiving)
- Artifacts archived despite no deleted-symbol references: 36 (archived by
  policy, not by content — the rebuild invalidates the context, not necessarily
  the text)

---

## 4. What was NOT archived

The following files were explicitly excluded and remain at their original
locations:

- `artifacts/00_99_post_rebuild_verification.md` — produced by the Stage 1
  rebuild itself, not before it; documents the current post-rebuild state
- `INVARIANTS.md` — non-numbered top-level governance file
- `ROADMAP.md` — non-numbered top-level roadmap (to be updated in Spec 4)
- `SUPERSEDED.md` — non-numbered top-level file documenting legacy superseded work
- `archive/ARCHIVE_SUMMARY.md` — the pre-existing legacy archive (separate from
  this `_archive_2026-04_pre_notebook_reset/` directory)

---

## 5. Recovery

To access an archived artifact for reference purposes, read it in place. Do not
copy or move files out of this directory without explicit reason — they are
historical, not current.
