# Planning Index

## Active plan
- `planning/current_plan.md` — Post-PR-#209 cleanup, DRAFT → LOCKED activation, and planning purge for CROSS-02-02 / CROSS-02-03 (Category C, branch `docs/phase02-contracts-lock-and-planning-cleanup`).

## Agent routing

| Role | Reads |
|------|-------|
| Executor | `planning/current_plan.md` (task T01, T02, … as directed) |
| Reviewer-adversarial (final gate, Cat A/F) | `planning/current_plan.md` + diff |
| Reviewer-deep (final gate, Cat B/D) | `planning/current_plan.md` + diff |
| Reviewer (final gate, Cat C/E) | diff only |
