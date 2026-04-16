## Critique: plan_aoestats_01_03_02

**Reviewer:** reviewer-adversarial (claude-opus-4-6)
**Date:** 2026-04-16
**Plan:** `planning/plan_aoestats_01_03_02.md`
**Step:** 01_03_02 — True 1v1 Match Identification (aoestats)
**Invariants checked:** I3, I6, I7, I9, I10

---

### Blockers (must fix before execution)

**B1. Duplicate player rows inflate or deflate true 1v1 counts (I7 traceability, methodological soundness)**

The plan's structural 1v1 criterion is `COUNT(*) ... GROUP BY game_id HAVING COUNT(*) = 2`
(T05, Cell 13, line 517–528). Step 01_03_01 identified 489 duplicate player rows using the
COALESCE string-concatenation key (`game_id || '_' || COALESCE(profile_id, '__NULL__')`),
confirmed at `01_03_01_systematic_profile.json > dataset_level.duplicate_players_rows = 489`.

If any of these 489 duplicates fall in 1v1 matches, a game_id with 2 distinct players could
have 3 raw rows, causing `COUNT(*)` to classify it as a 3-player match (false negative).
Conversely, a solo-player game_id (1 distinct player) with one duplicate would have
`COUNT(*) = 2` and be falsely classified as a true 1v1 (false positive).

The plan does not acknowledge this interaction anywhere. The words "duplicate" and "489" do
not appear in the T03–T06 query cells. The Q1 active-player-definition section (T03)
establishes that all rows are active but does not address whether some rows are active
*duplicates* of each other within the same game_id.

**Required fix:** Either (a) add a diagnostic query that counts how many of the 489 duplicate
rows fall in game_ids that would change classification (player_count = 2 vs player_count != 2)
when counted with vs without deduplication, or (b) use `COUNT(DISTINCT ...)` on a suitable
key (e.g., the COALESCE concatenation from 01_03_01) alongside the raw `COUNT(*)`, and
report both counts. If the difference is zero, document that. If nonzero, the true 1v1 count
is ambiguous until 01_04 resolves deduplication.

This is a blocker because the true 1v1 count is the step's primary deliverable, and an
unquantified error margin — even a small one — undermines the artifact's utility for the
01_04 cleaning decision.

---

### Warnings (should fix)

**W1. `recommended_1v1_definition` is a cleaning recommendation, not a profiling finding (I9 scope violation)**

The plan's summary computation (T08, Cell 23, lines 811–816) includes:

```python
"recommended_1v1_definition": (
    "Use player-count method (exactly 2 rows in players_raw per game_id) "
    "as the structural 1v1 criterion. ..."
)
```

The plan explicitly states "profiling only -- no cleaning decisions" (line 141, 175, 221–224,
1163). Yet `recommended_1v1_definition` tells 01_04 *what method to use*. This is a
recommendation, not a finding. The T13 research log instructions (line 1121) also say to
document "The recommended 1v1 definition for downstream use."

**Suggested fix:** Replace `recommended_1v1_definition` with a neutral
`comparison_conclusion` that states the empirical finding without prescribing action.
For example: "The player-count method and the leaderboard filter produce different sets.
The player-count method captures structural 1v1 matches regardless of ladder type. The
leaderboard filter includes orphaned matches with no verifiable player data. The choice
between them is a 01_04 cleaning decision." The facts are the same; the framing respects
I9.

**W2. Missing cross-validation against existing `players_per_match` census data**

The 01_02_04 census artifact already contains `players_per_match` computed via
`SELECT game_id, COUNT(*) AS player_count FROM players_raw GROUP BY game_id` — the
identical query logic to T05's Q3. The census reports `player_count=2: match_count=18,438,769`.

The plan's T05 will independently recompute this number but includes no assertion that the
result matches the census. This is inconsistent with T04's treatment, where the plan *does*
cross-validate the orphaned match count against the 01_03_01 linkage integrity result
(Cell 11, line 483–486).

**Suggested fix:** Add an assertion after T05's Cell 13:
```python
CENSUS_TRUE_1V1 = sum(
    entry["match_count"] for entry in census.get("players_per_match", [])
    if entry["player_count"] == 2
)
assert true_1v1_count == CENSUS_TRUE_1V1, (
    f"True 1v1 count {true_1v1_count} != census players_per_match[2] {CENSUS_TRUE_1V1}"
)
```
This costs one line and eliminates the possibility of a silent inconsistency between
artifacts.

**W3. The plan does not load `players_per_match` or `num_players_distribution` keys in the Cell 5 validation block**

Cell 5 (lines 266–268) validates `num_players_distribution` and `categorical_matches.leaderboard`
from the census. It does NOT validate `players_per_match`, even though this key contains the
ground truth for Q3's answer. If the executor adds the W2 cross-validation, they will need
`players_per_match` loaded. Even without W2, the validation block should assert the presence
of all keys the step depends on.

**W4. `num_players_distribution` vs `players_per_match` discrepancy is known but not flagged in the plan**

The census data already reveals the answer to Q2 (num_players vs actual player count):

- `num_players_distribution` → `num_players=2`: 18,586,063 matches
- `players_per_match` → `player_count=2`: 18,438,769 matches

Difference: 147,294 matches. This is already established data. The plan treats Q2 as an
open question ("Unknown: Does num_players always equal the count of player rows?" — line 96)
when the census already proves the answer is *no*. While it is valid to produce a full
cross-tabulation, the plan should acknowledge that the mismatch is already known and
quantified, rather than presenting it as a discovery.

---

### Suggestions (nice-to-have)

**S1. Consider a Venn diagram instead of (or alongside) the bar chart**

T09's bar chart (Cell 24) shows four categories. A Venn diagram with two overlapping circles
(True 1v1, Ranked 1v1) would more directly visualize the set relationship that Q4 computes.
The bar chart obscures the containment/overlap structure. This is a presentation suggestion,
not a methodology issue.

**S2. profile_id DOUBLE type creates a latent CAST hazard for downstream steps**

`profile_id` is typed DOUBLE in the schema (players_raw.yaml, line 51). For this step,
`profile_id` is only used in the NULL-pattern diagnostic (T07, Cell 21), so DOUBLE vs
INTEGER does not affect results. However, for any future step that groups by or joins on
`profile_id`, floating-point equality hazards apply (e.g., `12345.0 == 12345.0` is safe,
but large integers beyond 2^53 would lose precision). The plan could add a one-line note
acknowledging this for the research log, since the 01_03_01 duplicate detection already
uses `CAST(profile_id AS VARCHAR)` which would produce `'12345.0'` not `'12345'`.

**S3. The gate condition (lines 1148–1158) does not check for internal arithmetic consistency**

The gate checks for key existence and non-emptiness but does not verify that
`overlap_both + true_only + ranked_only + neither = total_matches`. The plan's T06
verification section (line 730) mentions this check, but it appears only as a prose
verification instruction, not as a Python assertion in the code. Adding an explicit
`assert` would make the gate self-enforcing.

---

### Invariant compliance

| Invariant | Status | Evidence |
|-----------|--------|----------|
| I3 (temporal < T) | N/A | No temporal features computed. Player row counting is atemporal. |
| I6 (SQL verbatim) | RESPECTED | All queries stored in `sql_queries` dict (Cell 6) and written to markdown artifact (T11, Cell 26, lines 1050–1055). |
| I7 (no magic numbers) | RESPECTED with caveat | All runtime constants sourced from census/profile JSON (Cell 5, lines 277–294). The `= 2` in `HAVING COUNT(*) = 2` is definitional (1v1 = 2 players), not a magic number. However, the `<= 1` tolerance in the orphaned count assertion (line 483) is unexplained — why not exact equality? |
| I9 (step scope) | AT RISK | See W1. The `recommended_1v1_definition` field crosses from profiling into prescription. The rest of the step respects I9. |
| I10 (filename relative) | N/A | No filename column operations in this step. |

---

### Verdict

**PASS WITH WARNINGS**

B1 must be addressed before execution. The 489 duplicate player rows are a known data
quality issue from the predecessor step. A plan that counts players per game_id without
acknowledging that some of those counts may be inflated by duplicates has an unquantified
error in its primary deliverable. The fix is a diagnostic query (not a full deduplication —
that belongs to 01_04), which keeps the step within its I9 scope.

W1 should be addressed to maintain clean I9 compliance. W2 and W3 should be addressed
for artifact consistency with the census. W4 is advisory — the plan will still produce
valid findings, but presenting a known answer as an open question weakens thesis
defensibility if an examiner notices the census already had the data.
