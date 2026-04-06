# Feature Engineering for Supervised Binary Classification: A Thesis Reference Manual

> **Feature engineering is the single highest-leverage activity in predictive modeling.**

For binary win/loss prediction on observational game data with temporal structure and player-level panels, rigorous feature engineering demands three things: strict temporal discipline (no feature may use information unavailable at prediction time), symmetric treatment of opponents in pairwise settings, and systematic documentation of every feature's definition, lineage, and rationale. This manual synthesizes the methodological frameworks from [Kuhn & Johnson (2019)][kuhn-johnson], [Zheng & Casari (2018)][zheng-casari], the [Bradley-Terry][bradley-terry] paired comparison literature, and published esports/sports prediction research into an opinionated, thesis-ready reference. It covers the full pipeline from candidate generation through quality assessment, selection, and documentation — with specific attention to the pitfalls that invalidate results in temporal prediction tasks.

---

## 1. The Feature Engineering Pipeline: Extraction, Construction, and Selection

Feature engineering transforms raw data into numeric representations that expose predictor-response relationships. [Kuhn & Johnson][kuhn-johnson] frame it candidly: the re-working of predictors is more of an *art*, requiring the right tools and experience. The pipeline has three distinct stages that must not be conflated.

**Feature extraction** projects raw data into a new representational space through mathematical transformations — PCA, autoencoders, spectral methods. The original features are destroyed; new latent features replace them. **Feature construction** creates new variables by combining or transforming existing ones, typically guided by domain knowledge: computing a player's win rate against top-10 opponents, or the ratio of two economic indicators. **Feature selection** prunes the candidate set to retain only informative, non-redundant features using filter, wrapper, or embedded methods. The relationship is sequential: construction and extraction *generate* candidates; selection *prunes* them.

[Zheng & Casari][zheng-casari] organize their taxonomy by data type — numeric transformations (log, Box-Cox, binning), text representations (bag-of-words, TF-IDF), categorical encodings (feature hashing, bin-counting), and model-based features (PCA, k-means stacking). Kuhn & Johnson instead organize by transformation dimensionality: **1:1** (single predictor → single new predictor, e.g., Box-Cox), **1:many** (single predictor → multiple features, e.g., spline basis expansions), and **many:many** (multiple predictors → multiple features, e.g., PCA). Both taxonomies are useful; for a thesis, the Kuhn & Johnson framework maps more cleanly to a methodology chapter.

For systematic candidate generation in game prediction, enumerate all data entities (players, matches, opponents, maps) and their relationships, then categorize by information source: historical performance aggregates, relative/comparative features (rating differences, head-to-head records), contextual features (map, tournament stage, rest days), and trend features (rolling averages, momentum indicators). Apply standard aggregation functions (mean, median, std, min, max, trend slope) over multiple temporal windows (last 3, 5, 10, 20 matches). Then create interaction features: ratios, differences, and products between paired features. Every candidate must pass the question: *"Would this information be available at the moment the prediction must be made?"*

### Domain expertise versus automated generation

Automated tools have a role but do not replace human reasoning. **[Featuretools][featuretools]** uses Deep Feature Synthesis (DFS), recursively applying aggregation and transformation primitives across relational entity sets ([Kanter & Veeramachaneni, 2015][dfs-paper]). **[tsfresh][tsfresh]** extracts 794+ features from time series using 63 characterization methods, with built-in statistical filtering via the Benjamini-Yekutieli procedure. [Heaton (2016)][heaton-2016] demonstrated empirically that ratios and differences are not well synthesized by any model type, confirming these should always be manually engineered.

The recommended approach is hybrid: expert-designed core features from domain knowledge first, automated exploration for discovery of non-obvious patterns second, and feature selection to prune the combined set third.

---

## 2. Pre-Game Versus In-Game: The Temporal Availability Boundary

This distinction is the most important methodological decision in match prediction. **Pre-match features** use only information available before the match begins: player historical statistics, ratings, head-to-head records, matchup compositions, map characteristics, contextual variables (rest days, tournament stage). **In-game features** require the match to be in progress: live economy differentials, kill counts, objective control, spatial positioning.

[Yang, Qin & Lei (2017)][yang-esports] demonstrated this boundary's empirical significance: pre-match features alone achieved **71.5% accuracy** for esports prediction, while adding real-time features at 40 minutes reached **93.7%**. [Hodge et al. (2019)][hodge-esports] achieved **85% accuracy within five minutes** of gameplay using real-time features. These results illustrate that pre-match and in-game prediction are fundamentally different problems with different stakeholders, deployment contexts, and evaluation standards.

### Formal definition and enforcement

For prediction target $Y_t$ (outcome of match at time $t$), a feature $f$ is temporally valid if and only if $f(x) = g(D_{<t})$, where $D_{<t}$ is the set of all data points with timestamps strictly before match start time $t$. No data generated during or after the match may contribute to any feature used to predict that match's outcome.

Enforcement requires four mechanisms. First, **timestamp-based filtering**: every feature computation function accepts a `cutoff_time` parameter and filters strictly with `data[data.timestamp < cutoff_time]`. Second, **feature metadata tagging**: tag each feature with `temporal_category: "pre_match" | "in_game"` and enforce category constraints in the training pipeline. Third, **temporal cross-validation**: use time-based train/test splits that respect chronological ordering — never random splits. Fourth, **feature auditing**: for each feature, explicitly verify the answer to "Would this feature realistically be available at the time of prediction?" Modern [feature stores][feature-stores] (Feast, Tecton, Databricks) implement point-in-time correct retrieval natively.

For a thesis methodology, define three explicit categories: **Category A** (pre-match static: invariant player attributes), **Category B** (pre-match dynamic: historical aggregations computed from all data before match start), and **Category C** (in-game: data generated after match start, excluded from pre-match models).

---

## 3. Symmetry in Pairwise Prediction Demands Difference Features

In a 1v1 game, the assignment of which player occupies the "Player 1" slot is arbitrary. A model that treats `[player1_features, player2_features]` as a standard concatenation will learn different weights for each slot, violating the fundamental requirement that $P(\text{A wins vs B}) = 1 - P(\text{B wins vs A})$. This creates spurious patterns based on listing order.

The **[Bradley-Terry model][bradley-terry]** (1952) provides the canonical solution: each player $i$ has latent strength $\beta_i$, and $P(i > j) = 1 / (1 + e^{\beta_j - \beta_i})$. The key insight is that the logit of the win probability equals the **difference** of latent strengths. The [Elo rating system][elo-wiki] is a special case. This directly motivates **difference features** as the theoretically grounded representation for pairwise prediction.

### Four approaches to symmetric representation

**Difference features** (preferred for most models): for any player-level feature $x$, construct $\Delta x = x_A - x_B$. This is naturally antisymmetric — swapping players negates the feature, which under logistic regression gives $P(\text{B wins}) = 1 - P(\text{A wins})$. It reduces dimensionality by half and connects directly to Bradley-Terry. The full model becomes $P(\text{A wins}) = \sigma(w_0 + \sum_j w_j \cdot (x_{A,j} - x_{B,j}))$.

**Ratio features**: for strictly positive features, use $x_A / x_B$ or equivalently $\log(x_A) - \log(x_B)$. The log-ratio is equivalent to a difference feature on log-transformed values and is useful when multiplicative relationships are more natural.

**Canonical ordering with concatenation**: sort players by a fixed criterion (higher ID, alphabetically, higher rating) and concatenate. This preserves full information but introduces subtle bias — the model may learn "player in slot 1 tends to be stronger." Use only with models that naturally capture interactions (tree-based, deep learning). **Post-hoc symmetrization** can force symmetry on any model: $f_{\text{sym}}(\{A,B\}) = [f(A,B) + (1 - f(B,A))] / 2$.

**Symmetric kernels**: [Hue & Vert (ICML 2010)][hue-vert-2010] unified the theory of learning with unordered pairs, proving that pair duplication with averaging is equivalent to the symmetric kernel approach. [Zaheer et al. (2017, "Deep Sets")][deep-sets] provides the general framework for permutation-invariant architectures.

For a thesis using logistic regression or gradient boosting on tabular features, **difference features are the clear default**. They are simple, theoretically grounded, well-understood, and sufficient for capturing the pairwise structure.

---

## 4. Temporal Features: Windows, Decay, and Cold Starts

Player skill is not static. Capturing both long-term ability and short-term form requires multiple temporal feature horizons computed with strict chronological discipline.

**Expanding window (career) features** use all matches from a player's first match through (but not including) the current one: career win rate, total matches played, overall average performance. These capture baseline skill. **Rolling window (recent form) features** use the last $N$ matches or a fixed time window: last-10 win rate, last-30-day average performance. These capture current form, fitness, and meta adaptation. Best practice is to include both, plus a **momentum feature** defined as the difference: `momentum = last_10_winrate - career_winrate`, where positive values indicate a hot streak.

Common aggregations within any window: mean, median, standard deviation, min, max, count, sum, and trend (slope of a linear fit over the window).

### Decay-weighted statistics

The **[exponentially weighted moving average (EWMA)][ewma]** assigns exponentially decreasing weights to older observations:

$$\text{EWMA}_t = \alpha \cdot x_t + (1 - \alpha) \cdot \text{EWMA}_{t-1}$$

where $\alpha \in (0, 1)$ controls recency weighting. The half-life $H$ (number of periods for weight to decay to 50%) relates to $\alpha$ via $\alpha = 1 - \exp(-\ln 2 / H)$. Practical guidance: $\beta = 1 - \alpha \approx 0.9$ averages over roughly the last 10 observations; $\beta \approx 0.98$ over roughly 50. **Time-based decay** weights by actual elapsed time: $w_i = \exp(-\lambda \cdot (t_{\text{current}} - t_i))$, which is preferable when match frequency varies across players.

### Cold-start players

Players with few or no prior matches require regularization toward a global prior. The standard approach is **Bayesian smoothing**:

$$f_{\text{smooth}} = \frac{n_i \cdot f_{\text{observed}} + m \cdot f_{\text{global}}}{n_i + m}$$

where $n_i$ is the player's match count and $m$ is a pseudocount hyperparameter. This is mathematically identical to the smoothing used in target encoding. Additionally, include `matches_played` as an explicit feature so the model can learn to discount uncertain estimates, and consider a binary `is_new_player` flag. **[Glicko-2][glicko]** handles this natively by tracking rating deviation ($\phi$) that increases during inactivity — high $\phi$ directly encodes uncertainty and serves as a useful feature.

---

## 5. Assessing Feature Quality Before Any Model Is Trained

Feature evaluation should occur before modeling, not after. Three dimensions matter: **separability** (does the feature distinguish classes?), **redundancy** (does it duplicate information already captured?), and **stability** (does the feature-target relationship hold across time?).

### Separability metrics

**Cohen's $d$** measures the standardized mean difference between classes: $d = (\mu_1 - \mu_0) / s_{\text{pooled}}$. Thresholds: $|d| < 0.2$ negligible, $0.2$–$0.5$ small, $0.5$–$0.8$ medium, $\geq 0.8$ large (Cohen, 1988). This is fast, interpretable, and appropriate for continuous features with roughly normal distributions.

**Mutual information** captures both linear and nonlinear dependencies: $\text{MI}(X;Y) = \sum_{x,y} p(x,y) \log[p(x,y) / (p(x)p(y))]$. It equals zero if and only if $X$ and $Y$ are independent, handles mixed data types, and is implemented in [scikit-learn's `mutual_info_classif`][sklearn-mi] using k-nearest neighbors entropy estimation (Kraskov et al., 2004).

**Univariate AUROC** treats each feature as a standalone score and computes the area under the ROC curve. It is threshold-independent, invariant to class priors, and equivalent to the probability that a randomly selected winner has a higher feature value than a randomly selected loser ([Wilcoxon-Mann-Whitney statistic][auroc-explained]). An AUC of 0.5 means no discriminative power; below 0.5 means the feature's sign should be flipped.

### Multicollinearity and redundancy

**Variance Inflation Factor (VIF)**: $\text{VIF}_j = 1 / (1 - R^2_j)$, where $R^2_j$ is obtained by regressing feature $X_j$ on all other predictors. VIF = 1 means no collinearity; **VIF > 5 warrants investigation; VIF > 10 requires correction**. Unlike pairwise correlation, VIF detects when a variable is linearly dependent on *multiple* other variables simultaneously. $\sqrt{\text{VIF}}$ indicates how much the standard error is inflated.

**Correlation clustering** groups features using hierarchical clustering on the correlation matrix (with $1 - |r|$ as distance), cutting the dendrogram at a threshold (typically $|r| > 0.7$) and selecting one representative per cluster. The **mRMR** (minimum Redundancy Maximum Relevance) algorithm operationalizes conditional mutual information by selecting features that maximize MI with the target while minimizing MI between selected features.

### Temporal stability

For time-dependent data, compute feature distributions and feature-target correlations across different time windows. Use the **Population Stability Index (PSI)** to detect distributional drift, and monitor rolling-window AUC or MI to verify that the feature-target relationship is stable. Features that are strongly predictive in one era but not another may be capturing meta-specific or patch-specific effects that require explicit handling.

**Drop** a feature when VIF exceeds 10 and it contributes minimal unique information, when it has near-zero variance, or when domain knowledge indicates it is irrelevant or leaky. **Combine** features when multiple variables measure the same underlying construct (use PCA, factor scores, or domain-motivated composites like ratios).

---

## 6. Encoding Strategies for Categorical Variables and Interactions

Games produce high-cardinality categoricals: race/civilization (3–20 values), map (7–50+), hero/champion (100+), player ID (thousands). Encoding strategy matters enormously.

**One-hot encoding** works for low cardinality ($< 15$ categories): simple, no leakage risk, interpretable. It fails for high cardinality due to dimensionality explosion and sparsity. **[Target encoding][target-encoding]** replaces each category with the smoothed mean of the target for that category, producing a single column regardless of cardinality. The smoothed formula is:

$$\text{TE}(c) = \frac{n_c \cdot \bar{y}_c + m \cdot \bar{y}_{\text{global}}}{n_c + m}$$

where $n_c$ is the count for category $c$ and $m$ is a smoothing hyperparameter (typically 5–20). This shrinks rare categories toward the global mean, preventing extreme values. [Pargent et al. (2022)][pargent-2022] demonstrated in a large benchmark that **regularized target encoding consistently outperforms traditional methods** across multiple ML algorithms and datasets.

### Preventing target encoding leakage

Naive target encoding creates severe leakage: for a category appearing once, the encoded value equals that row's target. Three prevention strategies exist. **K-fold target encoding** (recommended): split training data into $K$ folds, encode each fold's rows using target statistics from the other $K-1$ folds; encode test data using full training statistics. **Leave-one-out**: subtract each row's target from its category mean; less robust than K-fold. **CatBoost ordered encoding**: process data in random order, each row encoded using only preceding rows' targets; no cross-validation needed, prevents leakage by construction.

[Scikit-learn's `TargetEncoder`][sklearn-target-encoder] (v1.3+) implements internal cross-fitting during `fit_transform()`, with a critical distinction: `fit_transform(X, y)` uses cross-fitting to prevent leakage, but `fit(X, y).transform(X)` does not.

### Categorical interactions

For game matchup prediction, creating a **matchup feature** (e.g., `race_A × race_B`) is standard and highly informative because win rates depend on the specific combination, not just individual values. For 4 races this creates 16 categories (or 10 unique if matchups are symmetric). Apply target encoding with smoothing to the interaction categorical. For higher-order interactions or very high cardinality, **factorization machines** model interactions via latent factor dot products without explicitly creating cross-product features.

Polynomial and cross-product features for continuous variables ($x_i \cdot x_j$, $x_i^2$) capture nonlinear relationships in linear models but cause feature explosion (degree-2 on 50 features creates 1,275 terms). Tree-based models capture interactions naturally and rarely benefit from explicit polynomial features. [Kuhn & Johnson (2019, Ch. 7)][kuhn-johnson] recommend simple screening of all pairwise interactions followed by penalized regression (Lasso) to select relevant ones.

---

## 7. Feature Selection: Filter, Wrapper, and Embedded Methods

Feature selection occurs after candidate generation and quality assessment. The three method families differ in how they evaluate feature subsets.

**Filter methods** rank features by statistical association with the target, independent of any model. Mutual information works for any feature type and captures nonlinear dependencies. The chi-squared test applies only to categorical features (tests independence). ANOVA F-test applies to continuous features (tests whether class means differ), but only captures linear relationships. Filters are fast and model-agnostic but ignore feature interactions.

**Wrapper methods** evaluate feature subsets by training a model and measuring performance. Recursive Feature Elimination (RFE) trains on all features, removes the least important, and repeats — producing a full feature ranking. Forward selection starts empty and adds features greedily; backward elimination starts full and removes greedily. Wrappers find subsets optimized for a specific model but are computationally expensive and risk overfitting to the evaluation metric.

**Embedded methods** perform selection during model training. **L1 regularization (Lasso)** drives coefficients to exactly zero, automatically selecting features; Elastic Net (L1+L2) is preferred when features are correlated. **Tree-based importance** measures mean decrease in impurity (MDI) or [permutation importance][permutation-importance]; MDI is biased toward high-cardinality features, so **permutation importance** is more reliable.

### When to use which

For quick screening of many features, use MI-based filters. For linear models, use Lasso or Elastic Net. For tree-based models, use tree importance plus permutation importance. For high-dimensional settings ($p \gg n$), filter first, then apply embedded methods. [Kuhn & Johnson][kuhn-johnson] recommend combining approaches: filters for initial screening, embedded methods for fine-tuning, always within proper resampling frameworks.

### Selection stability and the cardinal sin of pre-split selection

The **[Nogueira stability index][nogueira-stability]** (Nogueira, Sechidis & Brown, 2018, JMLR) measures how consistently a selection algorithm picks the same features across cross-validation folds. It ranges from −1 to 1 (1 = perfect stability, 0 = random). Higher regularization generally produces fewer selected features with higher stability. Report this metric in your thesis to demonstrate that your selected features are not artifacts of a particular data split.

**Performing feature selection on the full dataset before train/test splitting is one of the most common and devastating mistakes in ML.** The selection algorithm uses information from test samples — their feature values *and* labels — causing wildly optimistic performance estimates. [Scikit-learn's documentation][sklearn-pitfalls] demonstrates that with 250 random, independent features and a random binary target (zero real signal), pre-split selection achieves ~80% accuracy instead of the expected ~50%. The correct approach: split first, select features *inside* each cross-validation fold using only fold-training data. Use `sklearn.pipeline.Pipeline` to enforce this automatically.

### A note on Bayesian model comparison and feature importance

When evaluating whether a feature set change produces a meaningful improvement, the same statistical rigor applies as for classifier comparison. The [Bayesian signed-rank test with ROPE][benavoli-2017] (via the [`baycomp`][baycomp] library) can assess whether the performance difference between two feature sets is practically meaningful or merely noise. This is particularly valuable for ablation-style feature selection: rather than asking "is the difference statistically significant?" ask "what is the probability that this feature set is practically better?" A ROPE of ±1 percentage point accuracy is a reasonable default.

---

## 8. Eight Feature Engineering Mistakes That Invalidate Results

These errors are pervasive in published work and must be explicitly guarded against.

**Feature leakage** uses information unavailable at prediction time. The most common form in sports prediction is using post-game statistics (final kills, score margin) as features for predicting the game those statistics came from. Detection heuristic: suspiciously high accuracy (>95% on a genuinely uncertain task), or feature importance dominated by a single feature that shouldn't be highly predictive. [IBM][ibm-leakage] and [KDnuggets][kdnuggets-mistakes] provide comprehensive taxonomies of leakage sources.

**Normalization before splitting** computes scaling parameters (mean, standard deviation) on the entire dataset, contaminating training with test distribution information. Always fit scalers on training data only, then transform both sets with training statistics. [Scikit-learn's common pitfalls guide][sklearn-pitfalls] demonstrates this explicitly.

**Target encoding leakage** embeds target information in features when encoding is computed on the full dataset or without fold-aware cross-fitting. Use K-fold encoding with smoothing, never naive target encoding.

**Circular features** include the current match's outcome in a feature for that same match — for example, computing a "win streak" that counts the current match, or computing Elo ratings without strict chronological updating.

**Features without causal pathways** are correlated with the outcome but are effects rather than causes — for example, the number of post-match interviews given (correlated with winning, but caused by it). Ask: "Would this feature be available and unchanged regardless of the match outcome?"

**Over-engineering** creates too many features relative to sample size. With $p$ features and $n$ samples, if $p/n > 0.1$–$0.5$ for traditional models, dimensionality becomes problematic. Common culprits: polynomial features on many variables, one-hot encoding high-cardinality categoricals without frequency thresholding, creating rolling window features at every possible window size.

**Validation leakage** occurs when test information influences model selection through iterative re-running of cross-validation after inspecting results. Pre-register your validation protocol.

**Temporal leakage in aggregations** uses season-end or future-match statistics to predict earlier matches. Strict point-in-time computation — using only data with timestamps before the prediction time — is the only prevention.

---

## 9. Rating Systems, Form Indicators, and Esports-Specific Features

### Elo, Glicko-2, and TrueSkill as ML features

The **[Elo system][elo-wiki]** computes expected score as $E_A = 1 / (1 + 10^{(R_B - R_A)/400})$ and updates as $R'_A = R_A + K \cdot (S_A - E_A)$. Elo ratings are mathematically equivalent to weights of a logistic regression learned through stochastic gradient descent on streaming pairwise data. The K-factor controls adaptation speed: K=10–20 for established players, K=30–40 for new players. [Hvattum & Arntzen (2010)][hvattum-2010] demonstrated Elo's effectiveness for football prediction.

**[Glicko-2][glicko]** (Glickman) extends Elo with two additional parameters: rating deviation ($\phi$, the uncertainty in the rating) and volatility ($\sigma$, expected fluctuation based on performance consistency). New or inactive players have high $\phi$, which decreases with more games. Both $\phi$ and $\sigma$ serve as valuable features — high RD indicates unreliable ratings, high volatility indicates inconsistent players prone to upsets. [Yue et al. (2022)][yue-glicko-tennis] used Glicko features for Grand Slam tennis prediction.

**[TrueSkill][trueskill]** (Herbrich, Minka & Graepel, 2006, NeurIPS) represents skill as $N(\mu, \sigma^2)$, using factor graphs and expectation propagation. Use $\mu$ as the primary strength feature, $\sigma$ as uncertainty, and $\mu - 3\sigma$ as the conservative lower bound.

The consensus from the sports analytics literature is clear: **rating systems provide strong base features but are outperformed when incorporated into ML models alongside additional features.** The rating difference between opponents is the most natural single feature. [Bunker et al. (2024)][bunker-2024] found that logistic regression (69.5%) and ADTrees (69.8%) outperformed standalone Elo/WElo (67.5%) on ATP tennis data.

### Sports analytics features

**Form indicators**: last-$N$ match win rates (typically $N$=3, 5, 10), winning/losing streak lengths, momentum (recent form minus career form). **Fatigue and scheduling**: days since last match, matches played in last 7/14/30 days, travel distance. **Tournament stage**: group vs. knockout, seed differential, "must-win" indicator. **Head-to-head**: H2H win rate, H2H performance at specific venues, H2H goal/score differential.

### Esports-specific considerations

**Meta/patch features** are critical in competitive gaming because balance patches fundamentally alter character viability. Patch version should be a categorical or temporal boundary feature, and models should be retrained or explicitly conditioned on patch era.

**Matchup features** encode race/hero/champion interactions. In MOBAs, hero binary vectors (one-hot of all heroes per team), synergy matrices (pairwise allied hero scores), and counter matrices (pairwise opponent hero scores) are standard. [Do et al. (2021)][do-lol-2021] achieved **75.1% accuracy** for League of Legends from pre-game champion selection, finding individual champion mastery matters more than team composition.

**Map features** include team-specific map win rates, side bias per map, and map pick/ban sequence as a proxy for team confidence. In StarCraft II, map topology influences strategy viability through resource distributions and rush distances.

**StarCraft-specific work**: [Chen, Aitchison & Sweetser (2020)][chen-sc2-2020] introduced Spending Quotient as a macro-level performance measure, predicting player league at **61.7% accuracy** (vs. prior 47.3%). [Park et al. (2021)][park-sc2-2021] achieved **75.3% accuracy** for league prediction using KNN and Random Forest on 46,398 replays.

---

## 10. Documentation Standards: Making Features Reproducible and Thesis-Ready

Every feature in a thesis must be documented with enough precision that an independent researcher could recompute it exactly. [Heil et al. (2021, *Nature Methods*)][heil] established Bronze/Silver/Gold reproducibility standards for ML. Target Gold.

### The feature catalog

Present features in a structured table (in the methodology chapter or as an appendix) with these columns:

| Column | Description |
|--------|-------------|
| **ID** | Unique identifier (F001, F002, ...) |
| **Name** | Descriptive, code-compatible identifier (`player_elo_diff`, `h2h_winrate_last10`) |
| **Category** | Organizational group (Rating, Form, Head-to-Head, Matchup, Context) |
| **Data type** | Float, integer, binary, categorical, with value range |
| **Formula** | Precise mathematical definition |
| **Temporal availability** | Pre-match static / Pre-match dynamic / In-game |
| **Window** | Temporal aggregation window (career, last 10, last 30 days) |
| **Expected direction** | Hypothesized sign of relationship with target (+, −, nonlinear) |
| **Missing value treatment** | Imputation strategy for cold-start or incomplete data |
| **Domain justification** | Why this feature should be predictive |

### Integration with the thesis methodology chapter

Structure the methodology chapter as: (1) **Data description**: raw data sources, collection methods, temporal coverage; (2) **Feature engineering**: the systematic methodology, temporal availability boundary definition, feature taxonomy, complete feature catalog; (3) **Feature selection**: methods applied, stability analysis, final feature set; (4) **Experimental setup**: temporal splitting strategy, cross-validation approach, leakage prevention measures; (5) **Reproducibility**: code availability, computational environment, library versions, random seeds.

Feature importance should be reported using **permutation importance on test data** (not training data) and SHAP values for model-agnostic attributions, with stability metrics across cross-validation folds. [Ewald et al. (2024)][ewald-2024] provide a comprehensive guide for selecting feature importance methods matched to specific inferential goals.

### AI-assisted feature engineering disclosure

If AI tools are used during feature engineering — for generating candidate feature ideas, writing transformation code, suggesting encoding strategies, or debugging pipeline logic — this must be documented in the feature catalog or methodology chapter. The emerging academic standard ([KU Leuven framework][kuleuven-genai], [APA 7th edition][apa-chatgpt]) requires specifying which tool was used, for which features or transformations, and how outputs were validated. This is particularly important for feature construction, where AI-suggested features might lack domain justification: every feature must still pass the domain rationale test regardless of whether a human or an AI tool proposed it. Document AI-assisted features in the feature catalog with an additional column or note indicating the feature's origin (domain expertise, automated tool, or AI-suggested) to maintain full analytical traceability.

---

## Conclusion: Principles That Survive Methodology Changes

Five principles anchor this entire framework and should guide every feature engineering decision in a thesis.

First, **temporal integrity is non-negotiable**. Every feature must be computable from information strictly preceding the prediction time. This single constraint, rigorously enforced, prevents the most common and most damaging class of errors in predictive modeling on observational data.

Second, **symmetry must be structural, not accidental**. In 1v1 prediction, use difference features as the default representation. The theoretical connection to [Bradley-Terry models][bradley-terry] and the practical elimination of arbitrary-ordering bias make this the only defensible approach for pairwise tasks with tabular models.

Third, **feature quality before model complexity**. A well-chosen set of 15–30 features with clear domain justification, verified separability, and controlled redundancy will outperform hundreds of poorly vetted candidates fed to a complex model. Cohen's $d$, mutual information, and univariate AUROC should screen every candidate before it enters a model.

Fourth, **all preprocessing happens inside the resampling loop**. Feature selection, normalization, target encoding — everything that touches training labels or test distributions must be computed within cross-validation folds using only fold-training data. [Scikit-learn Pipelines][sklearn-pitfalls] enforce this; manual pipelines must be audited explicitly.

Fifth, **documentation is methodology**. A feature without a formula, temporal availability tag, and domain justification is not a feature — it is technical debt. The feature catalog is not an appendix afterthought; it is the empirical backbone of the thesis.

---

## References

<!-- Textbooks and foundational methodology -->
[kuhn-johnson]: http://www.feat.engineering/ "Kuhn & Johnson (2019) — Feature Engineering and Selection: A Practical Approach for Predictive Models. CRC Press"
[zheng-casari]: https://www.oreilly.com/library/view/feature-engineering-for/9781491953235/ "Zheng & Casari (2018) — Feature Engineering for Machine Learning: Principles and Techniques for Data Scientists. O'Reilly"
[heaton-2016]: https://arxiv.org/pdf/1701.07852 "Heaton (2016) — An Empirical Analysis of Feature Engineering for Predictive Modeling. arXiv:1701.07852"

<!-- Pairwise prediction and symmetry -->
[bradley-terry]: https://en.wikipedia.org/wiki/Bradley%E2%80%93Terry_model "Bradley-Terry model — Wikipedia"
[elo-wiki]: https://en.wikipedia.org/wiki/Elo_rating_system "Elo rating system — Wikipedia"
[hue-vert-2010]: https://icml.cc/Conferences/2010/papers/520.pdf "Hue & Vert (2010) — On Learning with Kernels for Unordered Pairs. ICML 2010"
[deep-sets]: https://arxiv.org/abs/1703.06114 "Zaheer et al. (2017) — Deep Sets. NeurIPS 2017"

<!-- Temporal features and decay -->
[ewma]: https://towardsdatascience.com/time-series-from-scratch-exponentially-weighted-moving-averages-ewma-theory-and-implementation-607661d574fe/ "Time Series From Scratch: EWMA Theory and Implementation — Towards Data Science"

<!-- Rating systems -->
[glicko]: https://en.wikipedia.org/wiki/Glicko_rating_system "Glicko rating system — Wikipedia"
[trueskill]: https://en.wikipedia.org/wiki/TrueSkill "TrueSkill — Wikipedia"
[hvattum-2010]: https://www.bibsonomy.org/bibtex/a0ef8f0c642f671fd027607d2b69ac6a "Hvattum & Arntzen (2010) — Using ELO Ratings for Match Result Prediction in Association Football"
[yue-glicko-tennis]: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0266838 "Yue et al. (2022) — A Study of Forecasting Tennis Matches via the Glicko Model. PLOS ONE"
[bunker-2024]: https://journals.sagepub.com/doi/10.1177/17543371231212235 "Bunker et al. (2024) — A Comparative Evaluation of Elo Ratings- and ML-Based Methods for Tennis Match Result Prediction. SAGE"

<!-- Automated feature engineering tools -->
[featuretools]: https://www.hopsworks.ai/post/automated-feature-engineering-with-featuretools "Automated Feature Engineering with Featuretools — Hopsworks"
[dfs-paper]: https://groups.csail.mit.edu/EVO-DesignOpt/groupWebSite/uploads/Site/DSAA_DSM_2015.pdf "Kanter & Veeramachaneni (2015) — Deep Feature Synthesis: Towards Automating Data Science Endeavors. MIT CSAIL"
[tsfresh]: https://github.com/blue-yonder/tsfresh "tsfresh — Automatic extraction of relevant features from time series (GitHub)"
[feature-stores]: https://www.databricks.com/blog/what-feature-store-complete-guide-ml-feature-engineering "What is a Feature Store? A Complete Guide — Databricks"

<!-- Feature quality and selection -->
[sklearn-mi]: https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.mutual_info_classif.html "mutual_info_classif — scikit-learn documentation"
[auroc-explained]: https://glassboxmedicine.com/2019/02/23/measuring-performance-auc-auroc/ "Measuring Performance: AUC (AUROC) — Glass Box Medicine"
[permutation-importance]: https://academic.oup.com/bioinformatics/article/26/10/1340/193348 "Altmann et al. (2010) — Permutation Importance: A Corrected Feature Importance Measure. Bioinformatics, 26(10)"
[nogueira-stability]: https://jmlr.org/papers/volume18/17-514/17-514.pdf "Nogueira, Sechidis & Brown (2018) — On the Stability of Feature Selection Algorithms. JMLR, 18(174):1–54"
[ewald-2024]: https://link.springer.com/chapter/10.1007/978-3-031-63797-1_22 "Ewald et al. (2024) — A Guide to Feature Importance Methods for Scientific Inference. Springer"

<!-- Encoding -->
[target-encoding]: https://www.blog.trainindata.com/target-encoder-a-powerful-categorical-encoding-method/ "Target Encoder: A Powerful Categorical Encoding Method — Train in Data"
[pargent-2022]: https://arxiv.org/abs/2104.00629 "Pargent et al. (2022) — Regularized Target Encoding Outperforms Traditional Methods in Supervised ML with High Cardinality Features. arXiv:2104.00629"
[sklearn-target-encoder]: https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.TargetEncoder.html "TargetEncoder — scikit-learn documentation"

<!-- Leakage and pitfalls -->
[ibm-leakage]: https://www.ibm.com/think/topics/data-leakage-machine-learning "What is Data Leakage in Machine Learning? — IBM"
[kdnuggets-mistakes]: https://www.kdnuggets.com/5-critical-feature-engineering-mistakes-that-kill-machine-learning-projects "5 Critical Feature Engineering Mistakes That Kill ML Projects — KDnuggets"
[sklearn-pitfalls]: https://scikit-learn.org/stable/common_pitfalls.html "Common Pitfalls and Recommended Practices — scikit-learn documentation"

<!-- Esports prediction literature -->
[yang-esports]: https://arxiv.org/abs/1701.03162 "Yang, Qin & Lei (2017) — Real-time eSports Match Result Prediction. arXiv:1701.03162"
[hodge-esports]: https://arxiv.org/html/2402.15923v1 "Hodge et al. (2019) — Predicting Outcomes in Video Games with LSTM Networks. arXiv:2402.15923"
[do-lol-2021]: https://arxiv.org/abs/2108.02799 "Do et al. (2021) — Using ML to Predict Game Outcomes Based on Player-Champion Experience in League of Legends. arXiv:2108.02799"
[chen-sc2-2020]: https://www.researchgate.net/publication/347202679_Improving_StarCraft_II_Player_League_Prediction_with_Macro-Level_Features "Chen, Aitchison & Sweetser (2020) — Improving StarCraft II Player League Prediction with Macro-Level Features. ResearchGate"
[park-sc2-2021]: https://www.mdpi.com/2079-9292/10/8/909 "Park et al. (2021) — Feature Extraction for StarCraft II League Prediction. Electronics, 10(8):909"

<!-- Bayesian comparison -->
[benavoli-2017]: https://www.jmlr.org/papers/volume18/16-305/16-305.pdf "Benavoli, Corani, Demšar & Zaffalon (2017) — Time for a Change: a Tutorial for Comparing Multiple Classifiers Through Bayesian Analysis. JMLR, 18(77):1–36"
[baycomp]: https://github.com/janezd/baycomp "baycomp — Bayesian comparison of classifiers (Python library by Janez Demšar)"

<!-- Reproducibility -->
[heil]: https://pmc.ncbi.nlm.nih.gov/articles/PMC9131851/ "Heil et al. (2021) — Reproducibility Standards for Machine Learning in the Life Sciences. Nature Methods"

<!-- GenAI transparency -->
[kuleuven-genai]: https://www.kuleuven.be/english/genai/transparency-about-the-use-of-genai "How to be transparent about the use of GenAI — KU Leuven"
[apa-chatgpt]: https://apastyle.apa.org/blog/how-to-cite-chatgpt "How to cite ChatGPT — APA Style (updated September 2025)"
