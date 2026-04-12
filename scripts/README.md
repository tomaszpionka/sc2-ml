# Scripts

Utility and maintenance scripts for the project. These are not part of the
importable `rts_predict` package; they are invoked directly from the repo root.

## Directory Map

| Path | Purpose |
|------|---------|
| `hooks/` | Git hook scripts (e.g., pre-commit helpers installed by `pre-commit`) |
| `sc2egset/` | Data acquisition and staging helpers specific to the SC2 EGSet dataset |
| `debug/` | One-off diagnostic scripts; not intended for production use |
| `check_mirror_drift.py` | Detects drift between paired directories (e.g., matches/ vs players/) |
| `session_audit.py` | Audits research-log entries and STEP_STATUS timestamps for consistency |
