# Planning Index

## Active plan
- [Current Plan](current_plan.md) — NOTE-3 + W2 missingness-audit refactor (Cat B; PR #140)

## Agent routing

| Role | Reads |
|------|-------|
| Executor | `planning/current_plan.md` (task T01, T02, … as directed) |
| Reviewer-adversarial (final gate, Cat A/F) | `planning/current_plan.md` + diff |
| Reviewer-deep (final gate, Cat B/D) | `planning/current_plan.md` + diff |
| Reviewer (final gate, Cat C/E) | diff only |
