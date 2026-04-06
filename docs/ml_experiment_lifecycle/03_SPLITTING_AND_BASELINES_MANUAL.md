# Splitting and Baselines: A Methodological Guide for Temporal ML on Game Data

> **Proper train/validation/test splitting and baseline establishment are the two methodological pillars that determine whether a supervised learning study produces trustworthy results.**

For binary win/loss prediction on observational game data — where matches have temporal ordering and players appear repeatedly — standard random splits violate i.i.d. assumptions and inflate performance dramatically. [Kapoor & Narayanan (2023)][kapoor-2023] found data leakage across 294 papers in 17 scientific fields, with effect sizes up to **d = 0.93** — large enough to transform a meaningless model into one that appears state-of-the-art. This manual synthesizes academic standards for splitting temporal panel data and establishing meaningful baselines, specifically for a thesis comparing tabular models and GNNs on StarCraft II and Age of Empires II match data.

---

## 1. Why Random Splits Produce Dangerously Optimistic Results

Standard k-fold cross-validation assumes observations are independently and identically distributed. Match-level game data violates this assumption in two fundamental ways: **temporal autocorrelation** (consecutive matches from the same player are correlated, and meta/patches shift over time) and **entity-level dependence** (multiple observations per player create within-group correlation). When these violations are ignored and data is shuffled randomly into folds, models exploit information from the future to predict the past and memorize player-specific patterns rather than learning generalizable predictors.

[Roberts et al. (2017)][roberts-2017], in a seminal *Ecography* paper, demonstrated that random CV with structured data causes serious underestimation of predictive error. Their experiments showed random k-fold CV appeared to explain over 50% of variation, but models completely failed to predict at remote locations when proper blocking was applied. [Ploton et al. (2020)][ploton-2020] confirmed this in ecological mapping: spatial CV revealed that models previously considered reliable had near-zero predictive power at unsampled locations. The core insight applies directly to panel game data: **block cross-validation should be used wherever dependence structures exist, even if no correlation is visible in residuals.**

[Kapoor & Narayanan (2023)][kapoor-2023] formalized a taxonomy of eight leakage types, with temporal leakage being especially relevant: when ML models predict future outcomes, test data must not contain observations from dates before training data. Their civil war prediction case study showed that after correcting leakage, complex ML models did not perform substantively better than decades-old logistic regression models. A [companion Nature Communications (2024) study][leakage-nature] on neuroimaging provides a direct analogy: when subject overlap between train and test was ignored (paralleling player overlap), prediction performance inflated by Δr = 0.04 — the model memorized subject-specific patterns rather than learning generalizable relationships.

---

## 2. Temporal Splitting Strategies and When to Use Each

Three main temporal splitting approaches exist, each suited to different data characteristics.

### 2.1 Chronological holdout

The simplest approach: order all matches by timestamp, assign the earliest portion to training, middle to validation, and most recent to testing. This mirrors deployment (train on past, predict future) and prevents look-ahead bias entirely. The disadvantage is high variance from a single split. For a thesis, this should serve as the **primary evaluation strategy**, with the most recent season or tournament period reserved as the final hold-out test set.

### 2.2 Expanding window (walk-forward) validation

Training starts with an initial window and grows to include all data up to a rolling test boundary. [Scikit-learn's `TimeSeriesSplit`][sklearn-tss] implements this directly with the `gap` parameter providing an embargo buffer. This is what [Brownlee][brownlee-backtest] calls the gold standard of model evaluation for time series. The trade-off is that later folds have substantially more training data, creating evaluation imbalance.

### 2.3 Sliding window (rolling window) validation

Fixes the training window size, dropping older observations as the window advances. Preferable when data is non-stationary and **recent behavior matters more than long-term history** — which is often the case in RTS games where patches fundamentally alter balance. [Cerqueira, Torgo & Mozetič (2020)][cerqueira-2020] compared these approaches across 174 real-world time series and found that for non-stationary data, out-of-sample methods preserving temporal order provide the most accurate performance estimates.

### 2.4 Global versus per-entity temporal splits

A critical distinction for panel game data. **Global chronological splits** place all data before time T in training and after T in testing — simple but some players may have no test data. **Per-entity temporal splits** allocate each player's earlier matches to training and later matches to testing, ensuring every player contributes to both sets with temporal integrity. For SC2/AoE2 ladder data, a hybrid approach works well: use a global chronological cutoff while documenting player coverage statistics.

---

## 3. Purge and Embargo Periods Prevent Subtle Leakage

[López de Prado (2018)][purged-cv] introduced **purging** and **embargoing** for financial time series, and both concepts apply directly to game data with engineered features.

**Purging** removes training observations whose feature windows overlap temporally with test observations — if a "last-10-games win rate" feature is computed for a test match, the training matches used in that computation must be excluded. **Embargoing** adds a fixed buffer after each test fold boundary, addressing autocorrelated features that could leak information even without direct overlap.

In [scikit-learn][sklearn-tss], the `gap` parameter in `TimeSeriesSplit` implements basic embargoing. For combinatorial purged cross-validation (CPCV), the [`skfolio` library][skfolio-cpcv] provides a full implementation following López de Prado's framework.

---

## 4. Handling the Dual Structure of Panel Data with Grouped Splits

Game match data is panel data with two dimensions: cross-sectional (across players) and longitudinal (within each player over time). Splitting must address both.

[Scikit-learn][sklearn-cv] provides [`GroupKFold`][sklearn-groupkfold], which ensures the same group (player) never appears in both training and test within a single fold, and the newer [`StratifiedGroupKFold`][sklearn-stratgroupkfold] which attempts to preserve class balance while maintaining group integrity.

**When player overlap is acceptable versus problematic** depends on the deployment scenario. If the model will predict future outcomes for **known players** already in the system, temporal splitting alone suffices — player overlap is acceptable because the model should learn player-specific patterns, but must not see future matches. If the model must generalize to **unseen players** (tournament newcomers, new accounts), group-aware splitting is essential to prevent entity memorization from inflating estimates.

Scikit-learn lacks a built-in splitter combining group integrity with temporal ordering. [Raschka's `mlxtend` library][mlxtend-gtss] provides `GroupTimeSeriesSplit`, which groups data before splitting to ensure group-level temporal ordering while supporting both rolling and expanding windows.

For the thesis, the recommended approach is:

1. Sort groups (players or matches) chronologically within each game
2. Use expanding window with a gap for primary temporal CV
3. Document whether player overlap occurs and report performance separately for established vs. new players
4. **Compare results from random CV vs. temporal CV vs. group-aware temporal CV**, reporting the performance gaps to quantify leakage sensitivity

---

## 5. Nested Cross-Validation Separates Tuning from Evaluation

When a study both tunes hyperparameters and estimates generalization performance, **nested cross-validation** prevents the selection bias that arises from using the same data for both purposes. The inner loop performs hyperparameter optimization within each outer training fold; the outer loop provides unbiased performance estimation.

[Varma & Simon (2006)][varma-2006] demonstrated this bias concretely: on null datasets with no real signal, non-nested CV error estimates fell below 30% for nearly 20% of simulations — despite zero actual predictive power. [Cawley & Talbot (2010)][cawley-2010] showed that overfitting the model selection criterion produces degradation often of comparable magnitude to differences in performance between learning algorithms.

However, [Wainer & Cawley (2021)][wainer-2021] tested nested versus flat CV across 115 datasets and found flat CV does not incur worse selections for most practical purposes — the bias primarily affects performance estimation, not model choice. The practical recommendation: **if the goal is reporting unbiased performance estimates (as in a thesis), nested CV is necessary; if only selecting the best model, flat CV often suffices.**

For temporal panel data, both inner and outer loops must respect temporal ordering. The [scikit-learn nested CV example][sklearn-nested] provides the implementation pattern: pass `TimeSeriesSplit` as both the inner CV strategy in `GridSearchCV` and the outer CV in `cross_val_score`. Computational cost scales multiplicatively (outer folds × inner folds × hyperparameter configurations), so practical shortcuts include using 5×3 instead of 10×10.

---

## 6. Validating That Your Splits Are Sound

Several concrete checks should be performed after constructing splits.

**Temporal integrity**: no test observation should have a timestamp earlier than any training observation within the same fold, and feature lookback windows must not extend into the test period. Plot train/test distributions over time to visually confirm separation.

**Leakage detection through performance gap analysis**: run the same model with random CV, temporal CV, and group-aware temporal CV. Large drops when moving to more restrictive splitting indicate the random split was exploiting leakage. [Kapoor & Narayanan][kapoor-2023] note that suspiciously high performance and unrealistic stability across folds are primary leakage indicators.

**Class balance preservation**: for win/loss prediction with competitive matchmaking, overall balance should be near 50/50, but temporal shifts in balance represent genuine non-stationarity that should be documented rather than corrected.

**Feature distribution consistency** between splits using KS tests or visual comparison — significant covariate shift means the model is tested under very different conditions than trained.

**Sanity check baselines**: a model trained on permuted labels should achieve ~50% accuracy; a "cheat" feature (copy of the target) should yield ~100%. Deviations from either signal pipeline errors.

### Sample size conventions and their limits

The **60/20/20** (train/validation/test) and **80/10/10** splits are widely used conventions. For large datasets (millions of records), even 1% test sets provide reliable estimates. These conventions break down for **small datasets** — a [Nature Digital Medicine (2024) study][sample-size] found that performance estimates don't stabilize until **N = 750–1,500**. For the thesis, with tens of thousands of matches per game, an 80/10/10 temporal split provides adequate test set sizes; the key constraint is ensuring the test period captures meaningful variation in meta shifts.

---

## 7. What Makes a Baseline Meaningful

A baseline establishes the **lower bound** that any proposed model must exceed to justify its complexity. The concept connects directly to the [Bayes error rate][bayes-error] — the theoretical minimum misclassification rate achievable by any classifier. For matchmade games where the system targets 50/50 outcomes, the Bayes error rate is substantial: even a perfect model cannot predict the outcome of a perfectly balanced match.

The recommended baseline hierarchy for a game prediction thesis has four tiers:

| Tier | Baseline | What it tests |
|------|----------|--------------|
| **0 — Sanity floor** | `DummyClassifier(strategy='most_frequent')` | Absolute minimum (~50% for balanced data) |
| **1 — Domain heuristic** | Elo expected win probability, matchup win rates, last-N win rate | Whether ML adds value over domain knowledge |
| **2 — Simple ML** | Logistic regression with regularization | Whether complex models outperform interpretable ones |
| **3 — Reference ceiling** | Best published results for the specific games | How the thesis results compare to prior work |

A [2022 NeurIPS study by Grinsztajn et al.][grinsztajn-2022] found that tree-based models outperform deep learning on medium-sized tabular data, and **in 40% of benchmarks simple baselines were competitive with much more complex architectures**. [Kadra et al. (2024)][deep-tabular] confirmed that properly tuned logistic regression sometimes beats XGBoost and deep learning on tabular datasets. These findings make logistic regression not merely a formality but a genuine competitor that contextualizes the added value of GNNs and gradient boosting.

---

## 8. Elo and Domain-Specific Baselines for RTS Prediction

Elo-based prediction is the single most important baseline for game match prediction because **Elo ratings are formally equivalent to logistic regression weights learned via stochastic gradient descent** on pairwise comparison data ([Morse, 2019][elo-lr]). The expected win probability formula $E(A) = 1/(1 + 10^{-(R_A - R_B)/400})$ is a logistic function of rating difference. The K-factor is the learning rate. This means Elo is not merely a heuristic — it is a constrained ML model, and any richer model must outperform it to justify additional features.

Empirical benchmarks establish what Elo-level prediction looks like across competitive games. In CS:GO, Elo achieves **62.8%** accuracy while player-decomposed [Glicko-2][glicko-csgo] reaches **63.1%**. For StarCraft II, pre-game prediction from features achieves roughly **63–71%** depending on feature richness, while mid-game prediction exceeds **80%** after the midpoint ([Park et al., 2022][park-sc2]). AoE2 academic literature is sparse — [Cetin Tas et al. (2023)][cetin-aoe2] demonstrated civilization/map interaction as a meaningful predictor — making the thesis a genuine contribution.

**Race/civilization matchup baselines** are RTS-specific and capture inherent game balance asymmetries. In SC2, matchup-specific win rates (PvZ, TvZ, PvT) fluctuate with patches by 1–5%. Computing historical matchup win rates and using them as a baseline tests whether ML models learn anything beyond raw game balance statistics.

**Recent form baselines** (exponentially weighted moving average of a player's last N results) capture short-term performance trends without any ML machinery.

---

## 9. The Evaluation Protocol Must Be Identical Across All Models

Baselines must use the **exact same splits, metrics, preprocessing pipeline, and evaluation protocol** as complex models. This requirement is violated more often than one might expect. Common errors include giving the main model more hyperparameter tuning budget, applying different feature engineering, or evaluating baselines on different partitions. As [Schweighofer et al. (2024)][stronger-baselines] note: the common practice of omitting baselines or comparing against weak baseline models obscures the value of ML methods proposed in research.

For the thesis, every model — from DummyClassifier through Elo through logistic regression through XGBoost through GNN — should be evaluated on identically constructed temporal folds with the same metrics reported:

| Metric | Purpose | Why it matters |
|--------|---------|---------------|
| **Accuracy** | Easily interpretable | Primary for near-balanced data |
| **Log loss** | Penalizes confident wrong predictions | Captures probability calibration quality |
| **Brier score** | Combines calibration and discrimination | Proper scoring rule |
| **AUC-ROC** | Threshold-independent discrimination | Standard for binary classification |
| **Brier Skill Score** | BSS = 1 − BS_model / BS_Elo | Directly quantifies improvement over Elo baseline |

[Davis et al. (2024)][davis-sports] emphasize that proper scoring rules should always be combined with reliability diagrams because high discrimination can obscure poor calibration.

---

## 10. Statistical Tests for Determining If Improvements Are Real

Reporting that Model A achieves 64.2% accuracy and Model B achieves 63.8% is insufficient without statistical testing.

### 10.1 Frequentist framework

[Demšar (2006)][demsar] established the standard framework with over 12,000 citations. For comparing two classifiers, use the **Wilcoxon signed-rank test** (non-parametric, robust). For comparing multiple classifiers across multiple conditions, use the **Friedman test** as an omnibus test, followed by pairwise Wilcoxon tests with Holm correction. Demšar introduced **Critical Difference (CD) diagrams** for visual presentation — these should appear in the thesis. [McNemar's test][mcnemar] is preferred when comparing predictions on a single test set, as it focuses on disagreement patterns.

A critical caveat from [Nadeau & Bengio (2003)][nadeau-bengio]: **all variance estimators based solely on cross-validation results are biased**. The standard paired t-test grossly underestimates variance when applied to CV folds because training sets overlap. Their corrected resampled t-test adjusts for this non-independence and is available in `mlxtend`.

### 10.2 Bayesian framework

[Benavoli et al. (2017)][benavoli-2017] argue compellingly for **Bayesian comparison methods** over null hypothesis significance testing. Their approach computes three posterior probabilities — P(model A wins), P(practical equivalence), P(model B wins) — using a **Region of Practical Equivalence (ROPE)**. If two classifiers differ by less than the ROPE threshold (e.g., 1% accuracy), they are considered practically equivalent. The [`baycomp`][baycomp] Python library implements the Bayesian correlated t-test and Bayesian signed-rank test.

### 10.3 Recommended protocol for the thesis

1. Report per-fold metrics from temporal CV for all models
2. Use Wilcoxon signed-rank tests for pairwise comparisons
3. Use Friedman test with Holm-corrected post-hoc for the full model comparison
4. Include CD diagrams
5. Apply [Bayesian comparison with ROPE][benavoli-2017] for the key comparisons (e.g., GNN vs. XGBoost)
6. Always report confidence intervals alongside point estimates
7. Set the ROPE threshold **before** running experiments — for game prediction, a difference of less than **1 percentage point in accuracy** or **0.005 in Brier score** constitutes practical equivalence

---

## 11. The "Bet on Sparsity" Principle: Why Simple Models Come First

Hastie, Tibshirani & Friedman coined the ["bet on sparsity" principle][bet-on-sparsity] in *The Elements of Statistical Learning*: if the true model is sparse (few important features), L1-regularized methods will efficiently recover it; if the truth is dense, **no method will succeed without massive data per parameter**. Starting with sparse, interpretable models is therefore a rational default.

This principle has strong empirical support. [Grinsztajn et al. (2022)][grinsztajn-2022] showed tree-based models outperform deep learning on typical tabular data. A [comprehensive 2024 benchmark][deep-tabular] across hundreds of datasets found several datasets where naive baselines and linear models achieve the best results. For a thesis comparing tabular models against GNNs, demonstrating the marginal improvement of each complexity step — from logistic regression to gradient boosting to graph neural networks — tells a far more compelling story than simply reporting GNN performance in isolation.

---

## 12. Common Baseline Mistakes to Avoid

**Six errors appear repeatedly in the ML literature** and must be explicitly guarded against:

**Not including baselines at all** — surprisingly common and methodologically indefensible. [Schweighofer et al. (2024)][stronger-baselines] found this is a widespread pattern even in clinical ML.

**Using unrealistically weak baselines** (a "strawman") to inflate apparent improvement. Properly optimized logistic regression often closes the gap to ensemble methods.

**Copying baseline numbers from other papers** without re-implementing on the same data and splits. Performance numbers from different experimental setups are fundamentally incomparable.

**Not reporting confidence intervals**, leaving readers unable to assess whether differences are meaningful.

**Claiming significance without statistical tests** — [Demšar (2006)][demsar] and [Raschka (2018)][raschka-2018] both emphasize this is unacceptable.

**Ignoring when a simple model achieves comparable performance** to a complex one. In such cases, the simple model should be preferred for interpretability and deployability. This is a finding, not a failure.

---

## Conclusion: Putting It All Together for the Thesis

The methodological framework for comparing ML methods on SC2 and AoE2 match data rests on three non-negotiable foundations.

**Temporal integrity in splitting**: use expanding window validation with a gap parameter for embargo, sorted chronologically, with performance gap analysis comparing random vs. temporal vs. group-aware splits to quantify leakage.

**A meaningful baseline hierarchy**: DummyClassifier → Elo expected win probability → race/civilization matchup rates → logistic regression → progressively complex models, all evaluated identically.

**Rigorous statistical comparison**: Friedman test with post-hoc corrections and CD diagrams for the full model comparison, Bayesian comparison with ROPE for key pairwise tests, and confidence intervals for every reported metric.

---

## References

<!-- Leakage and reproducibility -->
[kapoor-2023]: https://www.sciencedirect.com/science/article/pii/S2666389923001599 "Kapoor & Narayanan (2023) — Leakage and the Reproducibility Crisis in ML-Based Science. Patterns, 4(9)"
[leakage-nature]: https://www.nature.com/articles/s41467-024-46150-w "Rosenblatt et al. (2024) — Data Leakage Inflates Prediction Performance in Connectome-Based ML Models. Nature Communications"

<!-- Structured/temporal cross-validation -->
[roberts-2017]: https://ui.adsabs.harvard.edu/abs/2017Ecogr..40..913R/abstract "Roberts et al. (2017) — Cross-Validation Strategies for Data with Temporal, Spatial, Hierarchical, or Phylogenetic Structure. Ecography, 40:913–929"
[ploton-2020]: https://pmc.ncbi.nlm.nih.gov/articles/PMC7486894/ "Ploton et al. (2020) — Spatial Validation Reveals Poor Predictive Performance of Large-Scale Ecological Mapping Models. Nature Communications"
[cerqueira-2020]: https://machinelearningmastery.com/5-ways-to-use-cross-validation-to-improve-time-series-models/ "Cerqueira, Torgo & Mozetič (2020) — Evaluating Time Series Forecasting Models: An Empirical Study (via Brownlee overview)"
[purged-cv]: https://en.wikipedia.org/wiki/Purged_cross-validation "Purged Cross-Validation — Wikipedia (López de Prado 2018, Advances in Financial Machine Learning)"

<!-- scikit-learn splitting tools -->
[sklearn-cv]: https://scikit-learn.org/stable/modules/cross_validation.html "Cross-validation: evaluating estimator performance — scikit-learn documentation"
[sklearn-tss]: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html "TimeSeriesSplit — scikit-learn documentation"
[sklearn-groupkfold]: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html "GroupKFold — scikit-learn documentation"
[sklearn-stratgroupkfold]: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html "StratifiedGroupKFold — scikit-learn documentation"
[sklearn-nested]: https://scikit-learn.org/1.5/auto_examples/model_selection/plot_nested_cross_validation_iris.html "Nested versus non-nested cross-validation — scikit-learn example"
[skfolio-cpcv]: https://skfolio.org/generated/skfolio.model_selection.CombinatorialPurgedCV.html "CombinatorialPurgedCV — skfolio documentation"
[mlxtend-gtss]: https://rasbt.github.io/mlxtend/user_guide/evaluate/GroupTimeSeriesSplit/ "GroupTimeSeriesSplit — mlxtend (Sebastian Raschka)"

<!-- Nested CV literature -->
[varma-2006]: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0224365 "Varma & Simon (2006) — Bias in Error Estimation When Using Cross-Validation for Model Selection. BMC Bioinformatics (referenced via PLOS ONE review)"
[cawley-2010]: https://www.jmlr.org/papers/v11/cawley10a.html "Cawley & Talbot (2010) — On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation. JMLR, 11:2079–2107"
[wainer-2021]: https://www.sciencedirect.com/science/article/abs/pii/S0957417421006540 "Wainer & Cawley (2021) — Nested Cross-Validation When Selecting Classifiers Is Overzealous for Most Practical Applications. Expert Systems with Applications"

<!-- Backtesting and time series evaluation -->
[brownlee-backtest]: https://machinelearningmastery.com/backtest-machine-learning-models-time-series-forecasting/ "Brownlee — How To Backtest Machine Learning Models for Time Series Forecasting. MachineLearningMastery"

<!-- Sample size -->
[sample-size]: https://www.nature.com/articles/s41746-024-01360-w "Tummers et al. (2024) — Estimation of Minimal Data Set Sizes for ML Predictions. npj Digital Medicine"

<!-- Baselines and model comparison -->
[bayes-error]: https://en.wikipedia.org/wiki/Bayes_error_rate "Bayes Error Rate — Wikipedia"
[grinsztajn-2022]: https://arxiv.org/html/2407.00956v1/ "Grinsztajn et al. (2022/2024) — Why Do Tree-Based Models Still Outperform Deep Learning on Tabular Data? NeurIPS (extended benchmark)"
[deep-tabular]: https://m-clark.github.io/posts/2022-04-01-more-dl-for-tabular/ "Clark (2022) — Deep Learning for Tabular Data (literature review and benchmarks)"
[stronger-baselines]: https://arxiv.org/html/2409.12116v1 "Schweighofer et al. (2024) — Stronger Baseline Models: A Key Requirement for Aligning ML Research with Clinical Utility. arXiv:2409.12116"
[bet-on-sparsity]: https://statmodeling.stat.columbia.edu/2013/12/16/whither-the-bet-on-sparsity-principle-in-a-nonsparse-world/ "Gelman (2013) — Whither the 'Bet on Sparsity' Principle? (discussion of Hastie, Tibshirani & Friedman's ESL)"

<!-- Elo and game-specific baselines -->
[elo-lr]: https://stmorse.github.io/journal/Elo.html "Morse (2019) — Elo as a Statistical Learning Model"
[glicko-csgo]: https://www.emergentmind.com/topics/glicko2-rating-system "Glicko-2 Rating System overview (Bober-Irizar et al. CS:GO benchmarks referenced)"
[park-sc2]: https://www.academia.edu/70116503/Predicting_the_Winner_in_Two_Player_StarCraft_Games "Park et al. — Predicting the Winner in Two Player StarCraft Games"
[cetin-aoe2]: https://www.researchgate.net/publication/377541570_Regression_Analysis_of_Age_of_Empires_II_DE_Match_Results_with_Machine_Learning "Cetin Tas et al. (2023) — Regression Analysis of Age of Empires II DE Match Results with Machine Learning. IEEE"

<!-- Statistical comparison of classifiers -->
[demsar]: https://www.jmlr.org/papers/volume7/demsar06a/demsar06a.pdf "Demšar (2006) — Statistical Comparisons of Classifiers over Multiple Data Sets. JMLR, 7:1–30"
[mcnemar]: https://machinelearningmastery.com/mcnemars-test-for-machine-learning/ "Brownlee — How to Calculate McNemar's Test to Compare Two ML Classifiers. MachineLearningMastery"
[nadeau-bengio]: https://link.springer.com/article/10.1023/A:1024068626366 "Nadeau & Bengio (2003) — Inference for the Generalization Error. Machine Learning, 52(3):239–281"
[benavoli-2017]: https://www.jmlr.org/papers/volume18/16-305/16-305.pdf "Benavoli, Corani, Demšar & Zaffalon (2017) — Time for a Change: a Tutorial for Comparing Multiple Classifiers Through Bayesian Analysis. JMLR, 18(77):1–36"
[baycomp]: https://github.com/janezd/baycomp "baycomp — Bayesian comparison of classifiers (Python library by Janez Demšar)"
[raschka-2018]: https://arxiv.org/abs/1811.12808 "Raschka (2018) — Model Evaluation, Model Selection, and Algorithm Selection in Machine Learning. arXiv:1811.12808"

<!-- Sports analytics methodology -->
[davis-sports]: https://link.springer.com/article/10.1007/s10994-024-06585-0 "Davis et al. (2024) — Methodology and Evaluation in Sports Analytics: Challenges, Approaches, and Lessons Learned. Machine Learning, 113:6977–7010"