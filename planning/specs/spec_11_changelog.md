---
task_id: "T11"
task_name: "Update CHANGELOG"
agent: "executor"
dag_ref: "planning/dags/DAG.yaml"
group_id: "TG03"
file_scope:
  - "CHANGELOG.md"
read_scope: []
category: "B"
---

# Spec: Update CHANGELOG

## Objective

Document the package restructure in CHANGELOG.md under `[Unreleased]`.

## Instructions

Under the `[Unreleased]` section, add to `Changed` and `Removed`:

```markdown
### Changed
- Package structure: `src/rts_predict/<game>/data/<dataset>/` and
  `src/rts_predict/<game>/reports/<dataset>/` replaced by
  `src/rts_predict/games/<game>/datasets/<dataset>/{data,reports}`
- All imports updated (68 statements across ~18 files) to new `rts_predict.games.*` namespace
- Both `config.py` files rewritten with new `__file__`-relative path derivation (4 levels to root)
- `.gitignore` patterns updated for new `datasets/*/data/` paths
- `.claude/settings.json` deny rules updated for new data paths
- 6 shell scripts in `scripts/sc2egset/` updated with new hardcoded paths
- 3 sandbox notebooks updated (imports + jupytext sync)
- ~42 documentation files updated (~126 path references)
- `pyproject.toml` entry points updated to `rts_predict.games.*`

### Removed
- Colocated test directories inside `src/` (were empty): `src/rts_predict/sc2/data/tests/`,
  `src/rts_predict/aoe2/data/aoestats/tests/`, `src/rts_predict/common/tests/`
```

## Verification

- `[Unreleased]` section in CHANGELOG.md contains the above Changed and Removed entries
- No other sections modified

## Context

- This task depends on T10 (final verification passed) — run only after T10 confirms
  the restructure is complete and clean.
