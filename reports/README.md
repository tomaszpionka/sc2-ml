# reports/

This directory contains the root research log index and cross-cutting (`CROSS`) entries only.

## Structure

```
reports/
  research_log.md          # Index + CROSS-scoped entries (architecture, tooling, planning)
  README.md                # This file
```

Per-dataset research logs live alongside the datasets they describe:

```
src/rts_predict/games/<game>/datasets/<dataset>/reports/research_log.md
```

For example:

- `src/rts_predict/games/sc2/datasets/sc2egset/reports/research_log.md`
- `src/rts_predict/games/aoe2/datasets/aoe2companion/reports/research_log.md`

## Research log template

New entries must conform to the canonical entry schema at:

`docs/templates/research_log_template.yaml`

## What belongs here vs. per-dataset logs

| Entry type | Location |
|---|---|
| Architectural decisions, tooling, planning | `reports/research_log.md` (scope: CROSS) |
| Data acquisition, feature engineering, model results for a specific dataset | `src/rts_predict/games/<game>/datasets/<dataset>/reports/research_log.md` |
