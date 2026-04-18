# reports/specs/

This directory holds **cross-dataset pre-registered protocol artifacts** for the
thesis project "A comparative analysis of methods for predicting game results in
real-time strategy games."

## Purpose

Pre-registration specs lock analysis parameters *before* notebooks run, so that
all cross-dataset comparisons in Phase 06 (Cross-Domain Transfer) can be traced
back to a declared, immutable protocol.  They are distinct from post-hoc
research-log entries:

| Artifact | Location | Written when |
|----------|----------|--------------|
| Pre-registration spec | `reports/specs/` | Before analysis begins |
| CROSS research-log entry | `reports/research_log.md` | After findings are recorded |
| Per-dataset research log | `src/.../reports/research_log.md` | After each dataset-specific step |

## Naming convention

`<phase>_<step>_preregistration.md` — e.g. `01_05_preregistration.md`.

Each spec carries a `spec_id` (e.g. `CROSS-01-05-v1`) and a `spec_version` that
is bumped on any parameter change per the amendment procedure in the spec's §14.

## Binding enforcement

Notebooks that implement a pre-registered analysis cite the spec SHA in their
docstring.  The pre-commit hook `scripts/check_01_05_binding.py` validates that
the SHA resolves in git history.  See `01_05_preregistration.md §13` for details.
