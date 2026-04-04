## Scientific Invariants (read before any data or ML work)

These are not implementation preferences — they are thesis methodology commitments.
Violating them produces results that cannot be defended at examination.

---

### Identity and splitting

1. **The split is per-player, not per-game.** Player A's test set is their last
   tournament. Player B may be in training for the same physical game. This is
   correct and intentional — the prediction task is "given what we know about
   this player's history, predict their next game," not "predict this game
   from a god's-eye view."

2. **For StarCraft II, the lowercased nickname is the canonical player identifier,
   not the toon.** Toons are server-scoped. A player switching from KR to EU
   server gets a new toon but keeps their nickname. Any feature indexed by toon
   instead of canonical nickname is silently wrong. Multi-toon cases must be
   classified (server switch, rename, ambiguous) in Phase 2.

### Temporal discipline

3. **No feature for game T may use information from game T or later.**
   Strictly `match_time < T`. This applies to rolling averages, win rates,
   head-to-head counts, Elo/Glicko ratings — everything. The rating used
   as a feature is the rating **before** the game, not after. Violations
   here are fatal to the thesis. Verify with explicit temporal leakage
   checks (Phase 7.5).

4. **The prediction target is the next game given all prior history.**
   For a given focal player and target game at time T, the feature window
   includes all cross-tournament history (`match_time < T`) plus
   within-tournament games already played (`match_time < T`, same tournament).
   This is not the same as predicting tournament outcomes — it is per-game
   prediction with a growing context window.

### Symmetric player treatment

5. **Both players in every game must be treated identically by the feature
   pipeline.** The same function that computes features for the focal player
   also computes features for the opponent. No player slot (player_a vs.
   player_b, or player 1 vs. player 2 in the replay) receives privileged
   treatment. The model input is always structured as
   `(focal_player_features, opponent_features, context_features)` and this
   structure is identical regardless of which player is focal.

   This invariant ensures that the prediction `P(A wins | A focal)` and
   `P(B wins | B focal)` = `1 - P(A wins | A focal)` are consistent.
   Asymmetric feature computation would break this relationship.

### Domain constants

6. **The SC2 game loop to real-time conversion is 22.4 loops per second
   at Faster (competitive) speed.** The engine runs at 16 loops per
   game-second; the Faster speed multiplier is 1.4×; thus
   `real_time_seconds = game_loops / 22.4`. The formula
   `game_loops / 16 / 60` produces **game-minutes** (engine time),
   which is 1.4× longer than real-time minutes. Both representations
   are valid but must be clearly labelled in all reports and artifacts.

   Sources: Blizzard s2client-proto (`protocol.md`: "22.4 gameloops per
   second"), Vinyals et al. 2017 (arXiv:1708.04782), Liquipedia Game Speed
   article.

### Data field status (updated after Phase 0 audit)

7. **APM from ToonPlayerDescMap is usable from 2017 onward.** Phase 0 found
   97.5% of player slots have non-zero APM. The 2.5% zeros are concentrated
   in 2016 tournaments (systematic — entire year missing) plus 22 sporadic
   slots in 2017–2024. For feature engineering: use APM from 2017+ directly;
   impute or exclude 2016 rows.

   **MMR from ToonPlayerDescMap is NOT usable as a direct feature.** Phase 0
   found 83.6% of slots have zero MMR. The missingness is systematic: driven
   by tournament organiser (lobby vs. ladder replays), year (near-zero from
   2021+), and `highestLeague` field availability. Player skill must instead
   be derived from match history (Elo, Glicko-2, or rolling win rate).

### Reproducibility and rigour

8. **All analytical results must be reported alongside the query or code
   that produced them.** Any distribution, count, rate, or validation result
   written to a report artifact must include the exact SQL query or Python
   code used to compute it — not a description of it, the literal code.
   This applies to every artifact generated in Phases 0 through 6 in
   `SC2_THESIS_ROADMAP.md`. A finding without its derivation cannot be
   audited, reproduced, or cited in the thesis.

9. **No magic numbers.** Every threshold used in data cleaning, feature
   engineering, or model configuration must be justified by either:
   (a) empirical evidence from the dataset (e.g., a duration threshold
   derived from the observed distribution in Phase 1.3), or
   (b) a cited precedent from the literature (e.g., Wu et al. 2017 used
   10,000 game frames ≈ 7 real-time minutes as a minimum).
   Unjustified constants (e.g., "1120 game loops" without derivation)
   are not acceptable in a thesis-grade analysis. If a constant is used,
   document its derivation inline.

### Cross-game comparability

10. **The SC2 and AoE2 experiments must share a common evaluation protocol.**
    Both games use the same ML methods (logistic regression, random forest,
    gradient boosted trees), the same evaluation metrics (accuracy, log-loss,
    ROC-AUC, calibration), and the same statistical comparison methodology
    (Friedman test with Nemenyi post-hoc, per Demšar 2006). Feature sets
    differ by necessity (SC2 has in-game state, AoE2 does not), but the
    common pre-game feature categories (skill rating, win rate, activity,
    faction matchup, map, head-to-head) must be defined at a level of
    abstraction that applies to both games.

    The AoE2 data asymmetry (no in-game state) is not a flaw — it is a
    controlled experimental variable. The cross-game comparison answers:
    "Do the same methods work equally well with and without in-game data?"
   