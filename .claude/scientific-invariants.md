## Scientific Invariants (read before any data or ML work)

These invariants are dataset-agnostic and game-agnostic. For methodology
guidance see docs/INDEX.md. For dataset-specific empirical findings see the
per-dataset invariants file under each game package.

These are not implementation preferences — they are thesis methodology commitments.
Violating them produces results that cannot be defended at examination.

---

### Identity and splitting

1. **The split is per-player, not per-game.** Player A's test set is their last
   tournament. Player B may be in training for the same physical game. This is
   correct and intentional — the prediction task is "given what we know about
   this player's history, predict their next game," not "predict this game
   from a god's-eye view."

   See docs/INDEX.md → Manual 03_SPLITTING_AND_BASELINES for the authoritative
   methodology.

2. **The canonical player identifier is the lowercased in-game nickname, not
   any server-scoped account ID.** Account IDs are server-scoped: a player
   switching servers gets a new ID but keeps their nickname. Any feature indexed
   by account ID instead of canonical nickname is silently wrong. Multi-account
   cases must be classified (server switch, rename, ambiguous) during the
   identity resolution phase.

### Temporal discipline

3. **No feature for game T may use information from game T or later.**
   Strictly `match_time < T`. This applies to rolling averages, win rates,
   head-to-head counts, Elo/Glicko ratings — everything. The rating used
   as a feature is the rating **before** the game, not after. Violations
   here are fatal to the thesis. Verify with explicit temporal leakage
   checks.

   **Normalization leakage.** Mean, standard deviation, min/max, and any
   other summary statistics used for feature scaling must be computed on
   training data only. The scaler object must be fit on the training fold
   and applied (transform only) to validation and test folds. Computing
   global z-scores across the entire dataset contaminates test-set
   predictions with distributional information from the test period
   (de Prado 2018, Ch. 7; Arlot & Celisse 2010).

   See docs/INDEX.md → Manual 03_SPLITTING_AND_BASELINES for the authoritative
   methodology.

4. **The prediction target is the next game given all prior history.**
   For a given focal player and target game at time T, the feature window
   includes all cross-tournament history (`match_time < T`) plus
   within-tournament games already played (`match_time < T`, same tournament).
   This is not the same as predicting tournament outcomes — it is per-game
   prediction with a growing context window.

### Symmetric player treatment

5. **Both players in every game must be treated identically by the feature
   pipeline.** The same function that computes features for the focal player
   also computes features for the opponent. No player slot receives privileged
   treatment. The model input is always structured as
   `(focal_player_features, opponent_features, context_features)` and this
   structure is identical regardless of which player is focal.

   This invariant ensures that the prediction `P(A wins | A focal)` and
   `P(B wins | B focal)` = `1 - P(A wins | A focal)` are consistent.
   Asymmetric feature computation would break this relationship.

   See docs/INDEX.md → Manual 02_FEATURE_ENGINEERING for the authoritative
   methodology.

### Reproducibility and rigour

6. **All analytical results must be reported alongside the query or code
   that produced them.** Any distribution, count, rate, or validation result
   written to a report artifact must include the exact SQL query or Python
   code used to compute it — not a description of it, the literal code.
   A finding without its derivation cannot be audited, reproduced, or cited
   in the thesis.

   See docs/INDEX.md → Manual 01_DATA_EXPLORATION for the authoritative
   methodology.

7. **No magic numbers.** Every threshold used in data cleaning, feature
   engineering, or model configuration must be justified by either:
   (a) empirical evidence from the dataset (e.g., a duration threshold
   derived from the observed distribution during profiling), or
   (b) a cited precedent from the literature.
   Unjustified constants are not acceptable in a thesis-grade analysis.
   If a constant is used, document its derivation inline.

   See docs/INDEX.md → Manual 01_DATA_EXPLORATION for cleaning thresholds,
   Manual 02_FEATURE_ENGINEERING for feature engineering thresholds.

### Cross-game comparability

8. **The SC2 and AoE2 experiments must share a common evaluation protocol.**
   Both games use the same ML methods (logistic regression, random forest,
   gradient boosted trees), the same evaluation metrics, and a common
   statistical comparison methodology.

   **Within-game comparison** (k classifiers on one game's temporal CV
   folds, where N_folds >= 5): Friedman omnibus test, then pairwise
   Wilcoxon signed-rank with Holm correction, complemented by Bayesian
   signed-rank with ROPE via baycomp (per Benavoli et al. 2017, Garcia
   & Herrera 2008).

   **Cross-game comparison** (N = 2 games — insufficient for Friedman;
   Demsar 2006 requires N >= 5): Per-game method rankings with effect
   sizes and bootstrapped confidence intervals; per-dataset pairwise
   tests (5×2 cv F-test or Nadeau-Bengio corrected t-test); Bayesian
   comparison via baycomp where applicable; qualitative cross-game
   concordance discussion.

   Feature sets differ by necessity, but the common pre-game feature
   categories (skill rating, win rate, activity, faction matchup, map,
   head-to-head) must be defined at a level of abstraction that applies
   to both games.

   The AoE2 data asymmetry (no in-game state) is not a flaw — it is a
   controlled experimental variable. The cross-game comparison answers:
   "Do the same methods work equally well with and without in-game data?"

   See docs/ml_experiment_lifecycle/06_CROSS_DOMAIN_TRANSFER_MANUAL.md for
   the authoritative cross-domain methodology.

---

## Per-dataset findings

Empirical findings about specific datasets (field availability, derived
constants, observed distributions) live in per-dataset invariants files,
not here. See:
  - src/rts_predict/sc2/reports/sc2egset/INVARIANTS.md (when created)
  - src/rts_predict/aoe2/reports/<dataset>/INVARIANTS.md (when created)

These per-dataset files are populated as Phase 01 (Data Exploration) surfaces
verifiable findings.
