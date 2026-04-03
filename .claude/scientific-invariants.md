## Scientific Invariants (read before any data or ML work)

These are not implementation preferences — they are thesis methodology commitments.
Violating them produces results that cannot be defended at examination.

1. **The split is per-player, not per-game.** Player A's test set is their last
   tournament. Player B may be in training for the same physical game. This is
   correct and intentional.

2. **For StarCraft 2 the Nickname (lowercased?) is the canonical player identifier, not toon.**
   Toons are server-scoped. A player switching from KR to EU server gets a new
   toon but keeps their nickname. Any feature indexed by toon instead of
   canonical nickname is silently wrong.

3. **No feature for game T may use information from game T or later.**
   Strictly match_time < T. This applies to rolling averages, win rates,
   head-to-head counts — everything. Violations here are fatal to the thesis.

4. **The prediction target is game M+1 given games 1..M within tournament T+1,**
   where the history window includes all cross-tournament history plus
   within-tournament games 1..M. This is not the same as predicting tournament
   outcomes.

5. **APM and MMR from ToonPlayerDescMap are suspected to be zero across the corpus.**
   Do not build features from these fields before verifying the zero-rate in
   Phase 1. If confirmed, document them as dead fields.
