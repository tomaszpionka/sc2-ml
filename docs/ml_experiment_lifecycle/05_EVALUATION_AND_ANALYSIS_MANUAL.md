# Evaluation, Statistical Comparison, Error Analysis, and Ablation Studies

> **This manual provides a complete methodological framework for evaluating and comparing supervised ML models in binary classification**, specifically designed for a thesis comparing tabular models and Graph Neural Networks on StarCraft II and Age of Empires II win/loss prediction.

Every metric, test, and technique below is grounded in the academic literature and includes implementation guidance. The framework addresses a persistent gap in applied ML research: most theses report accuracy and AUC alone, missing calibration quality, statistical rigor, interpretability, and sensitivity — the four pillars that separate strong empirical work from weak.

---

## Part I — Evaluation Metrics for Binary Classification

### 1. Threshold-Dependent Metrics

All threshold-dependent metrics derive from the **2×2 confusion matrix** of true positives (TP), true negatives (TN), false positives (FP), and false negatives (FN).

**Accuracy** = (TP + TN) / N gives overall proportion correct. It is the most intuitive metric but **insufficient even for balanced classes** for three reasons: it hides how errors distribute between classes, it cannot assess probability calibration, and two models with identical accuracy can have very different precision/recall tradeoffs. In game prediction with ~50/50 base rates, accuracy still fails to distinguish a model predicting 0.52 for every game from one that genuinely discriminates.

**F1-score** = 2 × precision × recall / (precision + recall) is the **harmonic mean** of precision and recall. The harmonic mean penalizes extreme imbalances more severely than the arithmetic mean: if precision = 1.0 and recall = 0.01, the arithmetic mean is a misleading 0.505, while the harmonic mean correctly returns ≈0.02. Implementation: [`sklearn.metrics.f1_score`][sklearn-f1].

**Matthews Correlation Coefficient (MCC)** = (TP×TN − FP×FN) / √((TP+FP)(TP+FN)(TN+FP)(TN+FN)) ranges from −1 (perfectly wrong) through 0 (random) to +1 (perfect). [Chicco & Jurman (2020)][chicco-mcc] demonstrated that **MCC produces a high score only if the model achieves good results in all four confusion matrix categories**, proportionally to both class sizes. Unlike accuracy and F1, MCC cannot show overoptimistic results on imbalanced data. Implementation: `sklearn.metrics.matthews_corrcoef`.

### 2. Probabilistic Metrics and Proper Scoring Rules

For game outcome prediction, the quality of probability estimates matters as much as binary decisions. A predicted 70% win probability should correspond to 70% actual wins. This requires **[proper scoring rules][proper-scoring]**: scoring functions minimized when the forecaster reports their true beliefs.

**Log loss** (binary cross-entropy) = −(1/N) Σ [yᵢ·log(p̂ᵢ) + (1−yᵢ)·log(1−p̂ᵢ)] measures average "surprise." It **heavily penalizes confident wrong predictions**: predicting 0.99 for a true 0 yields penalty ≈ 4.6, versus 0.92 for predicting 0.6. Baseline for 50% base rate: log(2) ≈ 0.693. Implementation: `sklearn.metrics.log_loss`.

**[Brier score][brier-wiki]** = (1/N) Σ (p̂ᵢ − yᵢ)² is the MSE of probability predictions against binary outcomes, introduced by [Brier (1950)][brier-wiki]. Range [0, 1], lower is better, with 50%-base-rate baseline of 0.25. **Brier Skill Score (BSS)** = 1 − BS/BS_ref, where BS_ref = p̄(1 − p̄), measures improvement over always predicting the base rate.

The **[Murphy (1973) decomposition][brier-decomposition]** partitions Brier score into three components: **BS = REL − RES + UNC**. Reliability (REL) measures calibration error. Resolution (RES) measures discriminative ability. Uncertainty (UNC) = p̄(1 − p̄) is inherent problem difficulty. A good model minimizes reliability and maximizes resolution. This decomposition explains *why* one model outperforms another.

[DeGroot & Fienberg (1983)][degroot-1983] formalized the key insight that forecast quality decomposes into **calibration** (agreement between predictions and frequencies) and **refinement/resolution** (how much forecasts vary). A model predicting 0.5 for every game is perfectly calibrated but useless — zero refinement. The scoring rule literature ([Gneiting & Raftery, 2007][proper-scoring-cran]) crystallizes this as: **"maximize sharpness subject to calibration."**

### 3. ROC Analysis and Precision-Recall Curves

The **ROC curve** plots TPR versus FPR across all thresholds. **AUC-ROC** = probability that a random positive ranks higher than a random negative (= Mann-Whitney U statistic). AUC = 0.5 is random; 1.0 is perfect. AUC is threshold-independent but does not capture calibration.

**[Precision-Recall curves][davis-goadrich]** are **more informative than ROC when classes are imbalanced**, as they focus on the positive class. [Davis & Goadrich (2006)][davis-goadrich] proved that dominance in ROC space implies dominance in PR space and vice versa, but PR curves require nonlinear interpolation.

The **[DeLong test][delong]** (DeLong, DeLong & Clarke-Pearson, 1988) compares AUCs of two correlated ROC curves. Appropriate for non-nested model comparisons but [can be conservative for nested models][delong-misuse]. Implementation: `MLstatkit.Delong_test` in Python or `pROC::roc.test(method="delong")` in R.

**Confidence intervals for AUC** via [stratified bootstrap][bootstrap-auc] (resample B ≥ 2,000 times maintaining class proportions, take percentile CI) or analytically via the DeLong variance formula.

### 4. Calibration Assessment and Post-Hoc Correction

**[Reliability diagrams][sklearn-calibration]** show mean predicted probability per bin versus observed frequency. A perfectly calibrated model follows y = x.

**Expected Calibration Error (ECE)** = Σₘ (nₘ/N)|acc(m) − conf(m)| is a weighted average of per-bin calibration gaps. **Maximum Calibration Error (MCE)** captures worst-case failure. Both were popularized by [Guo et al. (2017)][guo-calibration].

Post-hoc calibration methods:

| Method | Mechanism | Best for |
|--------|-----------|----------|
| **Platt scaling** | Logistic sigmoid on scores | Boosted trees, SVMs |
| **Isotonic regression** | Non-parametric monotonic mapping (needs ≥1K samples) | Random forests |
| **[Temperature scaling][guo-calibration]** | Single scalar T divides logits before sigmoid | Neural networks, GNNs |

Implementation: [`sklearn.calibration.CalibratedClassifierCV`][sklearn-calibration].

**Which models need calibration?** [Niculescu-Mizil & Caruana (2005)][niculescu-2005] empirically established: **logistic regression is naturally well-calibrated**; **random forests push probabilities toward 0.5** (underconfident); **boosted trees produce sigmoid-distorted probabilities**; **neural networks tend to be overconfident** ([Guo et al., 2017][guo-calibration]). For the thesis, apply and report calibration for all model families.

**Why calibration matters for game prediction**: a [sports betting study (arXiv:2303.06021)][sports-calibration] found that selecting models by calibration (classwise-ECE) rather than accuracy yielded **ROI of +34.69% versus −35.17%** for accuracy-based selection.

### 5. Prediction Sharpness and Confidence Analysis

Plot the **histogram of predicted probabilities** across test samples. This reveals whether the model makes sharp predictions (concentrated near 0 and 1) or clusters near 0.5.

**Shannon entropy** H(p̂) = −[p̂·log₂(p̂) + (1−p̂)·log₂(1−p̂)] ranges from 0 (max confidence) to 1 bit (max uncertainty). Mean entropy measures overall sharpness.

A model predicting 0.52 for every game has **zero practical value** even with >50% accuracy. Its Brier score is barely above 0.25, but it has **zero resolution**: it cannot distinguish easy from hard games. For the thesis, report not just aggregate metrics but the distribution of predictions across models — if all cluster near 0.5, this signals inherent predictive limits, a legitimate and publishable finding.

---

## Part II — Statistical Comparison of Classifiers

### 6. Pairwise Comparison of Two Classifiers

**[McNemar's test][mcnemar]** (1947) operates on the 2×2 contingency table of paired predictions. Only discordant pairs matter: χ² = (|B − C| − 1)² / (B + C). When B + C < 25, use the exact binomial test. Appropriate for a **single train/test split**. Implementation: `mlxtend.evaluate.mcnemar`.

The **[Nadeau-Bengio corrected t-test][nadeau-bengio]** (2003) addresses the critical flaw that training sets overlap across CV folds, violating independence. [Dietterich (1998)][dietterich-1998] showed standard paired t-tests produce inflated Type I error. The correction: t = x̄ / √((1/n + n₂/n₁) × σ²). Use for **k-fold CV comparisons**. Implementation: `correctipy.kfold_ttest`.

**[Dietterich's 5×2cv test][raschka-5x2cv]** (1998) avoids overlap entirely: 5 repeats of random 50/50 splits. Low Type I error, good power, requires 10 model refits. Implementation: [`mlxtend.evaluate.paired_ttest_5x2cv`][mlxtend-5x2cv].

**Wilcoxon signed-rank test** is the non-parametric alternative. [Demšar (2006)][demsar] recommends it over paired t-tests when comparing across multiple datasets. Implementation: `scipy.stats.wilcoxon`.

**Effect sizes must accompany all significance tests.** Cohen's d for parametric (|d| benchmarks: 0.2 small, 0.5 medium, 0.8 large). Rank-biserial correlation r for Wilcoxon (|r| benchmarks: 0.1, 0.3, 0.5). The [ASA statement (Wasserstein & Lazar, 2016)][asa-pvalue] holds that **p-values alone do not convey the magnitude of an effect**.

### 7. Comparing Multiple Classifiers Simultaneously

The **Friedman test** is the non-parametric equivalent of repeated-measures ANOVA, recommended by [Demšar (2006)][demsar]. The **Iman-Davenport correction** is more powerful and should be preferred. If the omnibus test is not significant, **do not proceed with post-hoc tests**.

Post-hoc procedures:

- **Nemenyi test**: Two classifiers differ significantly if average ranks differ by at least CD = q_α × √(k(k+1)/(6N)). Lower power than control-based tests.
- **[Holm correction][garcia-2008]** (step-down): more powerful than Bonferroni and Nemenyi. Recommended by [García & Herrera (2008)][garcia-2008].
- **Bonferroni-Dunn** (against a control): compare all to one designated model at adjusted α/(k−1).

**[Critical Difference (CD) diagrams][demsar]** are the gold-standard visualization: a number line of average ranks with bars connecting statistically indistinguishable groups. Implementation: [`autorank`][autorank] (Herbold, 2020) automatically selects the appropriate test and generates the diagram.

The **[Bayesian alternative (Benavoli et al., 2017)][benavoli-rope]** computes P(model A wins), P(practical equivalence), P(model B wins) using a **ROPE (Region of Practical Equivalence)** — typically ±0.01 for accuracy. This framework can **conclude equivalence**, which is impossible with frequentist tests. Implementation: `baycomp`.

### 8. Reporting Standards

The [ASA Statement][asa-pvalue] established: p-values do not measure hypothesis truth, science should not rest on p < 0.05 alone, and p-values do not measure effect size. For the thesis, **never say "significant" without context**; always accompany with effect sizes and [confidence intervals][ci-vs-pvalue].

**Recommended result presentation**: a main performance table (mean ± SD per metric per model with average rank column); a statistical comparison table (test, statistic, p-value, effect size); a CD diagram; box plots of per-fold metrics; and optionally Bayesian posterior plots.

---

## Part III — Error Analysis

### 9. Beyond the Aggregate Confusion Matrix

Compute **per-subgroup confusion matrices** along every stratification axis: per matchup (TvZ, PvP, cavalry vs. infantry civ), per rating bracket, per map, per patch era. Implementation: filter test set by subgroup and call `sklearn.metrics.confusion_matrix`.

**High-confidence errors** deserve special attention. Filter predictions where p̂ > 0.85 but wrong. These cases often cluster around specific matchups or anomalous games — they reveal systematic misunderstanding, not noise.

### 10. Error Stratification and Simpson's Paradox

Stratify errors across skill level, matchup type, duration, and patch era. Typical patterns: models fail on **upsets** (lower-rated player wins), **mirror matchups** (~50/50), and **post-patch transitions**.

**Simpson's paradox** — aggregate metrics hiding subgroup reversals — is a real risk. A model at 75% overall might be 90% for common matchups, 50% for rare ones. The check: for each subgroup g, compare accuracy(g) with overall accuracy. If model rankings reverse across subgroups, Simpson's paradox is present.

### 11. Feature Importance and Model Explanation

**[SHAP values][shap-paper]** ([Lundberg & Lee, 2017][shap-paper]) unify explanation methods under Shapley values from cooperative game theory. For each prediction, SHAP assigns feature importance satisfying local accuracy, missingness, and consistency axioms.

**[TreeSHAP][treeshap]** ([Lundberg et al., 2020][treeshap]) computes exact SHAP values for tree models in O(TLD²). Use `shap.TreeExplainer(model)` for XGBoost, LightGBM, random forests. Present beeswarm plots for global importance, dependence plots for nonlinear relationships, and waterfall plots for individual predictions.

**[Permutation importance][strobl-2007]** shuffles one feature at a time and measures accuracy drop without retraining. Unlike built-in importance, it is **unbiased with respect to feature cardinality**. [Strobl et al. (2007)][strobl-2007] demonstrated that built-in RF importance is biased toward high-cardinality and continuous features. Implementation: `sklearn.inspection.permutation_importance(model, X_test, y_test, n_repeats=30)`.

**[Partial Dependence Plots (PDPs)][sklearn-pdp]** show marginal effect of features on predictions. **[Individual Conditional Expectation (ICE) plots][ice-plots]** disaggregate PDPs per instance, revealing heterogeneous effects. Use `kind='both'` in [scikit-learn][sklearn-pdp-example] to overlay PDP on ICE curves.

**[LIME][lime-shap]** (Ribeiro et al., 2016) generates local explanations via interpretable surrogate models. SHAP is generally preferred (theoretically grounded), but LIME provides a complementary sanity check.

For **GNN explanations**: **GNNExplainer** (Ying et al., 2019) identifies influential subgraph structures. **[Integrated Gradients][integrated-gradients]** (Sundararajan et al., 2017) provide feature attributions satisfying sensitivity and implementation invariance axioms. Implementation: `captum.attr.IntegratedGradients`.

For the thesis, **use at least 2–3 methods** (SHAP + permutation importance + PDP) and show agreement/disagreement. [Molnar (2022)][molnar-book], *Interpretable Machine Learning*, provides the definitive reference.

### 12. Residual Analysis

The classification "residual" is r = p̂ − y. Plot residual histograms — a well-calibrated model has residuals centered near zero. Scatter residuals against each feature to detect systematic bias.

Biases to investigate: **civilization/race bias** (overestimating popular civilizations), **matchup-specific bias** (favoring one side at ~50% true rate), **Elo-dependent bias** (overestimating high-Elo players). For each matchup, compute mean residual — non-zero means reveal subgroup miscalibration.

Residual analysis connects directly to calibration: reliability diagrams are binned residual-vs-predicted plots, and Brier decomposition quantifies total calibration error.

---

## Part IV — Ablation Studies and Sensitivity Analysis

### 13. Feature Ablation Methodology

[Feature ablation][ablation-wiki] systematically removes feature groups to measure marginal contribution. The term originates from neuroscience; [Meyes et al. (2019)][meyes-2019] formalized it for neural networks.

**Subtractive (leave-one-group-out)**: train full model, remove one group, retrain, measure drop. Shows contribution conditional on all other groups. Can mask importance of correlated groups.

**Additive (forward)**: start minimal, add groups, measure gain. Different insertion orders produce different results — follow a logical narrative (e.g., Elo → matchup → form).

**Best practice: present both directions.** Discrepancies indicate interactions or redundancy. With k = 5 feature groups, the full 2^k = 32 combinations are computationally feasible and provide complete interaction coverage.

Feature ablation and SHAP answer complementary questions: ablation captures the true counterfactual ("what if this feature didn't exist?"), SHAP measures attribution without retraining. **Use SHAP for within-model interpretation, ablation for rigorous contribution measurement; present both.**

### 14. GNN Component Ablation

The most critical ablation: **remove all edges** so the GNN processes only node features with no message passing. If performance drops vs. the full GNN, graph structure provides value; if similar, the GNN adds nothing over tabular models. This single experiment is the strongest evidence for or against the graph approach.

Beyond graph structure, ablate:

- **Residual connections**: can account for significant accuracy improvements on heterophilous graphs
- **Normalization** (BatchNorm/LayerNorm): typically critical for stability
- **Aggregation function**: mean vs. sum vs. max (sum is more expressive per GIN theory)
- **Number of layers**: vary 1–4+, present as line plot
- **Edge types**: separately remove temporal vs. opponent edges
- **Attention mechanism** (if using GAT): replace with uniform weights

Present as a table with rows per configuration, columns per metric, across both games. Include significance indicators (* p < 0.05, ** p < 0.01).

### 15. Ablation Study Design Principles

**Statistical rigor is non-negotiable.** Every configuration must be repeated across CV folds and multiple seeds. Report mean ± SD. Apply paired statistical tests between full model and each variant.

**Ablation ≠ hyperparameter tuning.** Tuning seeks the best configuration; ablation seeks to understand components. First tune hyperparameters, then fix them, then ablate one component at a time — this isolates component effects from hyperparameter confounds.

**Document negative results.** What didn't help is as informative as what did. If graph structure adds nothing, or form features contribute nothing beyond Elo, these findings are valuable and publishable.

### 16. Sensitivity Analysis of Design Choices

Sensitivity analysis quantifies how **methodological choices** — not hyperparameters — affect results. Four choices demand analysis in this thesis:

- **Temporal split point**: vary train/test boundary (70/30 through 85/15). If the "winning" model changes with the cut point, the conclusion is fragile.
- **Elo K-factor**: vary 10–40 (standard chess range). K is a domain modeling choice.
- **Feature window length**: vary lookback (5, 10, 20, 50 past games for form features).
- **Minimum games threshold**: vary 5–50 minimum games for player inclusion.

**One-at-a-time (OAT) analysis** varies one choice while holding others at default. For richer analysis, the **Morris method** computes mean (μ*) and standard deviation (σ) of elementary effects. Implementation: `SALib.sample.morris` and `SALib.analyze.morris`.

Present as **line plots** (x = design choice, y = metric, multiple model lines with confidence bands) and a **summary table** (choice, range tested, metric range, max Δ, robustness verdict).

---

## Recommended Metric and Analysis Tiers

| Tier | Focus | Components |
|------|-------|-----------|
| **1** | Threshold-dependent discrimination | Accuracy, balanced accuracy, precision, recall, F1, MCC |
| **2** | Threshold-free discrimination | AUC-ROC, AUC-PR, curves |
| **3** | Probabilistic quality | Brier score, log loss, BSS, ECE, reliability diagrams |
| **4** | Statistical comparison | Friedman, Nemenyi/Holm, CD diagrams, DeLong, Nadeau-Bengio, Bayesian ROPE |
| **5** | Diagnostic depth | SHAP, permutation importance, PDP/ICE, prediction histograms, residual analysis, subgroup stratification |

All five tiers are necessary for a strong thesis. Tiers 1–2 are standard. **Tier 3 (calibration) separates competent from excellent evaluation.** Tier 4 ensures claims are statistically justified. Tier 5 transforms model comparison into genuine scientific contribution.

---

## Conclusion

Three insights emerge beyond standard textbook advice.

**Calibration is the most underrated evaluation dimension** — models with identical AUC can differ dramatically in probability quality. The [Murphy decomposition][brier-decomposition] of Brier score into reliability, resolution, and uncertainty provides the diagnostic tool to explain *why* one model outperforms another.

**Statistical comparison requires the right test for the right design** — standard paired t-tests on CV folds produce inflated Type I error, and the [Nadeau-Bengio correction][nadeau-bengio] or [Bayesian alternatives with ROPE][benavoli-rope] are essential.

**Ablation studies move the thesis from "model X beats model Y" to "model X beats model Y *because of* feature Z and component W"** — and for GNNs specifically, the single most important ablation removes all edges to test whether graph structure provides any value.

---

## References

<!-- Threshold-dependent metrics -->
[sklearn-f1]: https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html "f1_score — scikit-learn documentation"
[sklearn-metrics]: https://scikit-learn.org/stable/modules/model_evaluation.html "Metrics and scoring — scikit-learn documentation"
[chicco-mcc]: https://link.springer.com/article/10.1186/s12864-019-6413-7 "Chicco & Jurman (2020) — The Advantages of MCC over F1 Score and Accuracy. BMC Genomics, 21:6"

<!-- Probabilistic metrics and proper scoring -->
[proper-scoring]: https://en.wikipedia.org/wiki/Scoring_rule "Scoring Rule — Wikipedia"
[proper-scoring-cran]: https://cran.r-project.org/web/packages/scoringutils/vignettes/scoring-rules.html "Scoring rules in scoringutils — CRAN (Gneiting & Raftery framework)"
[brier-wiki]: https://en.wikipedia.org/wiki/Brier_score "Brier Score — Wikipedia (Brier, 1950)"
[brier-decomposition]: https://medium.com/@eligoz/some-notes-on-probabilistic-classifiers-iii-brier-score-decomposition-eee5f847d87f "Murphy (1973) Brier Score Decomposition (via Goz overview)"
[degroot-1983]: https://rss.onlinelibrary.wiley.com/doi/abs/10.2307/2987588 "DeGroot & Fienberg (1983) — The Comparison and Evaluation of Forecasters. JRSS-D, 32(1):12–22"

<!-- ROC and PR curves -->
[davis-goadrich]: https://minds.wisconsin.edu/handle/1793/60482 "Davis & Goadrich (2006) — The Relationship Between Precision-Recall and ROC Curves. ICML"
[delong]: https://pypi.org/project/MLstatkit/ "MLstatkit — DeLong test implementation (Python)"
[delong-misuse]: https://pmc.ncbi.nlm.nih.gov/articles/PMC3684152/ "Misuse of DeLong Test to Compare AUCs for Nested Models. Statistics in Medicine (2013)"
[bootstrap-auc]: https://rdrr.io/cran/pROC/man/ci.auc.html "ci.auc — Bootstrap confidence intervals for AUC (pROC, R)"

<!-- Calibration -->
[sklearn-calibration]: https://scikit-learn.org/stable/modules/calibration.html "Probability calibration — scikit-learn documentation"
[guo-calibration]: https://arxiv.org/abs/1706.04599 "Guo et al. (2017) — On Calibration of Modern Neural Networks. ICML"
[niculescu-2005]: https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf "Niculescu-Mizil & Caruana (2005) — Predicting Good Probabilities with Supervised Learning. ICML"
[sports-calibration]: https://arxiv.org/pdf/2303.06021 "Wheatcroft (2023) — Machine Learning for Sports Betting: Should Model Selection Be Based on Accuracy or Calibration? arXiv:2303.06021"

<!-- Pairwise classifier comparison -->
[mcnemar]: https://machinelearningmastery.com/mcnemars-test-for-machine-learning/ "Brownlee — How to Calculate McNemar's Test. MachineLearningMastery"
[nadeau-bengio]: https://cran.r-project.org/web/packages/correctR/vignettes/correctR.html "Nadeau & Bengio (2003) corrected t-test — correctR introduction (CRAN)"
[dietterich-1998]: https://www.semanticscholar.org/paper/Approximate-Statistical-Tests-for-Comparing-Dietterich/22f0579f212dfb568fbda317cba67c8654d84ccd "Dietterich (1998) — Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms. Neural Computation"
[raschka-5x2cv]: https://sebastianraschka.com/blog/2018/model-evaluation-selection-part4.html "Raschka (2018) — Model Evaluation, Model Selection, and Algorithm Selection in ML, Part 4"
[mlxtend-5x2cv]: https://rasbt.github.io/mlxtend/user_guide/evaluate/paired_ttest_5x2cv/ "paired_ttest_5x2cv — mlxtend documentation"

<!-- Multiple classifier comparison -->
[demsar]: https://www.jmlr.org/papers/volume7/demsar06a/demsar06a.pdf "Demšar (2006) — Statistical Comparisons of Classifiers over Multiple Data Sets. JMLR, 7:1–30"
[garcia-2008]: https://jmlr.csail.mit.edu/papers/volume9/garcia08a/garcia08a.pdf "García & Herrera (2008) — An Extension on Statistical Comparisons of Classifiers over Multiple Data Sets. JMLR, 9:2677–2694"
[autorank]: https://sherbold.github.io/autorank/ "Autorank — Automated statistical pipeline with CD diagrams (Herbold, 2020)"
[benavoli-rope]: https://alessiobenavoli.com/2016/11/19/the-importance-of-the-region-of-practical-equivalence-rope/ "Benavoli et al. — The Importance of the Region of Practical Equivalence (ROPE)"

<!-- Reporting standards -->
[asa-pvalue]: https://www.tandfonline.com/doi/full/10.1080/00031305.2016.1154108 "Wasserstein & Lazar (2016) — The ASA Statement on p-Values. The American Statistician, 70(2):129–133"
[ci-vs-pvalue]: https://pmc.ncbi.nlm.nih.gov/articles/PMC2689604/ "du Prel et al. (2009) — Confidence Interval or P-Value? Deutsches Ärzteblatt International"

<!-- Feature importance and explanation -->
[shap-paper]: https://arxiv.org/abs/1705.07874 "Lundberg & Lee (2017) — A Unified Approach to Interpreting Model Predictions. NeurIPS"
[treeshap]: https://www.semanticscholar.org/paper/From-local-explanations-to-global-understanding-AI-Lundberg-Erion/81600fd653a828d69f6160705be6814dd101beb7 "Lundberg et al. (2020) — From Local Explanations to Global Understanding with Explainable AI for Trees. Nature Machine Intelligence"
[strobl-2007]: https://pmc.ncbi.nlm.nih.gov/articles/PMC1796903/ "Strobl et al. (2007) — Bias in Random Forest Variable Importance Measures. BMC Bioinformatics, 8:25"
[sklearn-pdp]: https://scikit-learn.org/stable/modules/partial_dependence.html "Partial Dependence and ICE plots — scikit-learn documentation"
[ice-plots]: https://www.firmai.org/bit/ice.html "Individual Conditional Expectation (ICE) — Interpretable ML reference"
[sklearn-pdp-example]: https://scikit-learn.org/stable/auto_examples/inspection/plot_partial_dependence.html "PDP and ICE example — scikit-learn documentation"
[lime-shap]: https://www.lanchuhuong.com/data-and-code/2022-07-22_model-explainability-shap-vs-lime-vs-permutation-feature-importance-98484efba066/ "Model Explainability: SHAP vs. LIME vs. Permutation Feature Importance"
[integrated-gradients]: https://arxiv.org/abs/1703.01365 "Sundararajan et al. (2017) — Axiomatic Attribution for Deep Networks. ICML"
[molnar-book]: https://christophmolnar.com/books/interpretable-machine-learning "Molnar (2022) — Interpretable Machine Learning (3rd edition, book)"

<!-- Ablation studies -->
[ablation-wiki]: https://en.wikipedia.org/wiki/Ablation_(artificial_intelligence) "Ablation (artificial intelligence) — Wikipedia"
[meyes-2019]: https://arxiv.org/abs/1901.08644 "Meyes et al. (2019) — Ablation Studies in Artificial Neural Networks. arXiv:1901.08644"