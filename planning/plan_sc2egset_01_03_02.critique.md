## Critique: plan_sc2egset_01_03_02

Adversarial Review — Plan
Plan: planning/plan_sc2egset_01_03_02.md
Phase: 01 / 01_03_02
Date: 2026-04-16

Invariant compliance:
  I3 (temporal < T):        RESPECTED — No features computed. APM/MMR used only for diagnostic printouts in T05, not as classification criteria.
  I6 (SQL verbatim):        RESPECTED — All SQL stored in sql_queries dict and written verbatim to both JSON and MD artifacts (T08).
  I7 (no magic numbers):    AT RISK — See W1 below.
  I9 (step scope):          RESPECTED — Plan explicitly defers all row dropping to 01_04. Classification is read-only profiling.
  I10 (relative filename):  RESPECTED — All joins use filename column as native key on raw tables.


### Blockers (must fix before execution)

None.


### Warnings (should fix)

**W1. `STANDARD_RACES` is hardcoded despite the plan's own instruction to derive it at runtime (I7 tension).**

Line 291 hardcodes `STANDARD_RACES = ['Prot', 'Zerg', 'Terr', 'Rand']` with a comment "derived
from census selectedRace distribution." The plan's own commentary says "The `STANDARD_RACES`
constant must be derived from the census at runtime." But the code does not dynamically extract
this list from the census JSON — it is a manually transcribed constant.

The census JSON at `categorical_profiles.selectedRace` contains the full distribution from which
this list can be programmatically extracted. Fix: replace hardcoded list with dynamic extraction,
e.g.:

```python
STANDARD_RACES = [
    r['selectedRace'] for r in census['categorical_profiles']['selectedRace']
    if r['selectedRace'] != '' and not r['selectedRace'].startswith('BW')
]
```

**W2. Classification label `non_1v1_no_decisive_result` is semantically misleading — will propagate to thesis.**

A replay with exactly 2 players and an Undecided or Tie result IS a genuine 1v1 match. It lacks
a usable prediction target, but it is not "non-1v1." The label conflates game format with result
completeness. This label appears in the classification criteria table, the JSON artifact, and will
propagate to the research log (T09) and data cleaning step (01_04).

An examiner would challenge: "These are 1v1 matches; you excluded them for result quality, not game
format." A more defensible taxonomy:
- `true_1v1_decisive` — 2 players, 1 win + 1 loss
- `true_1v1_indecisive` — 2 players, no decisive outcome
- `non_1v1_too_many_players` — > 2 player rows
- `non_1v1_too_few_players` — < 2 player rows
- `unclassified` — everything else

The criteria themselves are correct — only the labels need adjustment before they propagate to
downstream artifacts and the thesis.


### Suggestions (nice-to-have)

**S1. Divergent CTEs between Cell 14 and Cell 15 in T07 — unnecessary inconsistency.**

Cell 14's `per_replay` CTE uses `GROUP BY rp.filename, max_players, observer_setting` and
includes `bw_race_count`, `standard_race_count`. Cell 15's re-execution uses
`GROUP BY rp.filename, max_players` and drops those columns. The GROUP BY divergence is harmless
because `replays_meta_raw` has exactly 1 row per filename (verified from 01_03_01). But it is
gratuitous inconsistency. Simpler: compute the summary in Python from `classification_df`
(already materialized in Cell 14) rather than re-executing an almost-identical CTE in SQL.

**S2. Add an explicit I3 annotation to Cell 11 (T05) noting that APM/MMR are post-game diagnostic columns.**

The empty-selectedRace analysis uses APM and MMR distributions as signals for the observer
hypothesis. These are in-game/post-game columns per 01_03_01 classification. Their use for
diagnostic printouts is acceptable under I9, but add a brief comment or markdown annotation
("Note: APM and MMR are in-game/post-game columns — used here for diagnostic
observer-vs-active-player discrimination only, NOT as classification inputs") to preempt any
future reviewer questioning whether post-game information leaked into the classification logic.


### Verdict

**PASS WITH WARNINGS**

The plan is methodologically sound for its stated scope. The classification logic is correctly
defined, gate conditions are rigorous (halt on `non_1v1_other > 0` is exactly right), all SQL
is stored verbatim (I6), no rows are dropped (I9), no temporal features are computed (I3), and
the predecessor chain is valid (01_03_01 complete, artifacts on disk).

The two warnings are real but non-blocking: W1 is fixable in 3 lines, W2 is a naming correction
that should happen before these labels reach the thesis.
