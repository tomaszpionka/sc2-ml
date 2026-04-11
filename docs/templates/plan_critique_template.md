---
plan_id:            # MUST match the sibling current_plan.md plan_id
created:            # ISO-8601
reviewer_model:     # e.g. claude-opus-4-6 (adversarial reviewer role)
scope:              # mirrors plan scope
---

# Critique: <short title matching plan>

> Sibling to `planning/current_plan.md`. Not consumed by executors.
> Audience: Tomasz + future viva prep.

## Invariants check
<One line per invariant in .claude/scientific-invariants.md. Format:>
- **#6 SQL shipped with findings** — yes/no/n-a — <pointer to plan section or why n-a>
- **#7 No magic numbers** — ...
- ...

## Defensibility check
<For each major choice in the plan, strongest objection + what would rebut it.>
- **Choice:** <what the plan decided>
  - **Strongest objection:** <the honest attack>
  - **Rebuttal evidence needed:** <what would close the gap>

## Likely supervisor / committee questions
<Grouped by plan section they target. Concrete questions, not vague worries.>
- On methodology:
- On data:
- On evaluation:

## Known weaknesses
<The planner's own honest-uncertainty register. Things it is NOT confident about.>

## Alternatives considered and rejected
<Future-thesis gold. Each entry: alternative, reason rejected, conditions under which it would be reconsidered.>
- **Alternative:**
  - **Rejected because:**
  - **Reconsider if:**