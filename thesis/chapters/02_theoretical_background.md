# Chapter 2 — Theoretical Background

## 2.1 Real-time strategy games

<!--
Definition, characteristics (resource gathering, base building, fog of war, etc.),
why RTS is harder to predict than turn-based games.
-->

## 2.2 StarCraft II

<!--
Three asymmetric races, economy model, build orders, map pool rotation, balance patches.
Competitive scene: WCS/ESL circuit, tournament formats, Aligulac.
Game engine timing: 16 loops/game-second, 22.4 loops/real-second at Faster speed.
Sources: s2client-proto, Vinyals et al. 2017, Liquipedia Game Speed.
Replay file format: s2protocol, tracker events, game events.

DRAFTABLE after Phase 01 (Data Exploration) — game loop timing sourced, patch landscape produced.
-->

## 2.3 Age of Empires II

<!--
Civilisation bonuses, age advancement, economy model, map generation.
Competitive scene, Elo rating, data availability via aoestats.io and mgz parser.
BLOCKED — AoE2 roadmap not yet started.
-->

## 2.4 Machine learning methods for binary classification

<!--
For each: formulation, assumptions, strengths, weaknesses, hyperparameters.
Logistic Regression, Random Forests, Gradient Boosted Trees (XGBoost, LightGBM),
SVMs (if used), Neural networks (MLP, LSTM/GRU, GNN).
-->

## 2.5 Player skill rating systems

<!--
Elo (1978), Glicko/Glicko-2 (Glickman 1999, 2001), TrueSkill (Herbrich et al. 2006).
Aligulac's race-matchup-specific variant.
How derived ratings serve as ML features.
-->

## 2.6 Evaluation metrics and statistical comparison

<!--
Accuracy, log-loss, ROC-AUC, Brier score, calibration.
Within-game: Friedman omnibus + Wilcoxon/Holm pairwise + Bayesian signed-rank (ROPE).
Cross-game (N=2): per-game rankings, bootstrapped CIs, 5x2 cv F-test.
Friedman requires N >= 5 blocks (Demsar 2006); inapplicable with 2 games.
Nemenyi deprecated due to pool-dependence (Benavoli et al. 2016).
Critical difference diagrams (Wilcoxon-based). See THESIS_WRITING_MANUAL.md §3.2.
-->
