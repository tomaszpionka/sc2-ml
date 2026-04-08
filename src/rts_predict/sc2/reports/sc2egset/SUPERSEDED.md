# Superseded Phase 1 Artifacts

This file marks Phase 1 (`01_*`) artifacts that will be regenerated or replaced
by the notebook-sandbox restart. Created as part of `chore/notebook-sandbox`
(see `_current_plan.md` B.9.4 for rationale).

Phase 0 artifacts (`00_*`) are **not listed** — they are current-authoritative.

This file is removed after the Phase 1 restart is complete and all artifacts
have been regenerated.

---

## Status key

| Status | Meaning |
|--------|---------|
| `will_be_regenerated` | Notebook restart re-runs the existing `exploration.py` function and produces the same artifact. |
| `will_be_replaced` | Notebook restart produces a new artifact superseding this one (no `exploration.py` function exists). |

---

## Phase 1 artifact inventory

| Artifact | Status | Reason |
|----------|--------|--------|
| `01_01_corpus_summary.json` | `will_be_regenerated` | `run_corpus_summary()` exists in `exploration.py`. |
| `01_01_duplicate_detection.md` | `will_be_regenerated` | `run_corpus_summary()` / `_write_duplicate_detection_md()` exists in `exploration.py`. |
| `01_01_player_count_anomalies.csv` | `will_be_regenerated` | `run_corpus_summary()` exists in `exploration.py`. |
| `01_01_result_field_audit.md` | `will_be_regenerated` | `run_corpus_summary()` / `_write_result_field_audit_md()` exists in `exploration.py`. |
| `01_02_parse_quality_by_tournament.csv` | `will_be_regenerated` | `run_parse_quality_by_tournament()` exists in `exploration.py`. |
| `01_02_parse_quality_summary.md` | `will_be_regenerated` | `run_parse_quality_by_tournament()` exists in `exploration.py`. |
| `01_03_duration_distribution.csv` | `will_be_regenerated` | `run_duration_distribution()` exists in `exploration.py`. |
| `01_03_duration_distribution_full.png` | `will_be_regenerated` | `run_duration_distribution()` / `_plot_duration_full()` exists in `exploration.py`. |
| `01_03_duration_distribution_short_tail.png` | `will_be_regenerated` | `run_duration_distribution()` / `_plot_duration_short_tail()` exists in `exploration.py`. |
| `01_04_apm_mmr_audit.md` | `will_be_regenerated` | `run_apm_mmr_audit()` exists in `exploration.py`. |
| `01_05_patch_landscape.csv` | `will_be_regenerated` | `run_patch_landscape()` exists in `exploration.py`. |
| `01_06_event_count_distribution.csv` | `will_be_regenerated` | `run_event_type_inventory()` exists in `exploration.py`. |
| `01_06_event_density_by_tournament.csv` | `will_be_regenerated` | `run_event_type_inventory()` exists in `exploration.py`. |
| `01_06_event_density_by_year.csv` | `will_be_regenerated` | `run_event_type_inventory()` exists in `exploration.py`. |
| `01_06_event_type_inventory.csv` | `will_be_regenerated` | `run_event_type_inventory()` exists in `exploration.py`. |
| `01_07_playerstats_sampling_check.csv` | `will_be_regenerated` | `run_playerstats_sampling_check()` exists in `exploration.py`. |
| `01_08_error_flags_audit.csv` | `will_be_replaced` | No function in `exploration.py`; Step 1.8 was Pattern B (ad-hoc markdown only). |
| `01_08_game_settings_audit.md` | `will_be_replaced` | No function in `exploration.py`; Step 1.8 was Pattern B (ad-hoc markdown only). |
| `01_09D_playerstats_stats_field_inventory.csv` | `will_be_regenerated` | `run_tracker_event_data_inventory()` exists in `exploration.py`. |
| `01_09D_tracker_event_data_field_inventory.csv` | `will_be_regenerated` | `run_tracker_event_data_inventory()` exists in `exploration.py`. |
| `01_09D_tracker_event_data_key_constancy.csv` | `will_be_regenerated` | `run_tracker_event_data_inventory()` exists in `exploration.py`. |
| `01_09E_game_event_data_field_inventory.csv` | `will_be_regenerated` | `run_game_event_data_inventory()` exists in `exploration.py`. |
| `01_09E_game_event_data_key_constancy.csv` | `will_be_regenerated` | `run_game_event_data_inventory()` exists in `exploration.py`. |
| `01_09F_event_schema_reference.md` | `will_be_regenerated` | `run_event_schema_document()` exists in `exploration.py`. |
| `01_09F_parquet_duckdb_schema_reconciliation.md` | `will_be_regenerated` | `run_parquet_duckdb_reconciliation()` exists in `exploration.py`. |
| `01_09_toplevel_field_inventory.csv` | `will_be_regenerated` | `run_toplevel_field_inventory()` exists in `exploration.py`. |
| `01_09_tpdm_field_inventory.csv` | `will_be_regenerated` | `run_tpdm_field_inventory()` exists in `exploration.py`. |
| `01_09_tpdm_key_set_constancy.csv` | `will_be_regenerated` | `run_tpdm_key_set_constancy()` exists in `exploration.py`. |
