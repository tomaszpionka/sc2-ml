# Model Training and Hyperparameter Tuning

> **Binary classification on temporal game data demands training pipelines that prevent leakage, hyperparameter tuning that respects chronological ordering, and reproducibility practices that meet modern academic standards.**

This manual covers every methodological decision in the training workflow — from sklearn Pipeline construction and GNN training loops through Bayesian hyperparameter optimization to random seed management — synthesized from foundational ML literature, framework documentation, and esports prediction research. The guidance applies directly to a thesis comparing logistic regression, XGBoost, LightGBM, random forests, and Graph Neural Networks on StarCraft II and Age of Empires II match data.

---

## 1. Training Pipelines Must Enforce Preprocessing Inside the Resampling Loop

The most consequential architectural decision in any tabular ML pipeline is ensuring that **all preprocessing — scaling, encoding, imputation, feature selection — occurs inside the cross-validation loop**, never before it. When a `StandardScaler` is fit on the full dataset before splitting, it computes μ and σ using test-fold samples, leaking future information into training features. The same applies to `SimpleImputer` (test-fold values influence the imputed mean), `OneHotEncoder` (test-only categories enter the vocabulary), and `SelectKBest` (feature importance scores incorporate test-fold targets).

[Cawley & Talbot (2010)][cawley-2010] established that this form of overfitting during model selection produces bias often of comparable magnitude to differences in performance between learning algorithms — meaning the leakage can be larger than the signal you are trying to measure when comparing models.

### 1.1 The sklearn Pipeline + ColumnTransformer pattern

The canonical solution is [sklearn's `Pipeline`][sklearn-pipeline] combined with `ColumnTransformer` for heterogeneous feature types. A properly structured pipeline for esports data with numeric game statistics and categorical features (race, map, civilization) wraps numeric preprocessing (imputation → scaling) and categorical preprocessing (imputation → one-hot encoding) into separate sub-pipelines, merges them via `ColumnTransformer`, then chains feature selection and the classifier.

When this pipeline is passed to `cross_val_score` or `GridSearchCV`, sklearn automatically calls `fit_transform` only on training folds and `transform` on validation folds. The double-underscore naming convention (`classifier__max_depth`) enables hyperparameter access through the pipeline for tuning.

For [Optuna integration][optuna], the `OptunaSearchCV` wrapper provides a drop-in replacement for `GridSearchCV`, while a custom objective function offers more flexibility for switching entire model architectures within the same study.

### 1.2 Pipeline serialization

[Pipeline serialization][sklearn-persistence] with `joblib.dump(pipeline, path, compress=3)` saves the entire preprocessing-plus-model artifact as a single file. Critical companion artifacts include a `requirements.txt` with pinned package versions, the random seeds used, data file checksums, and cross-validation fold indices. The `skops.io` package provides a more secure alternative to pickle-based serialization for deployment contexts.

---

## 2. GNN Training Differs Fundamentally from Tabular Workflows

Graph Neural Networks require explicit decisions about graph construction, mini-batching strategy, and message-passing depth that have no analogue in tabular ML.

### 2.1 Graph formulation for esports data

For esports match prediction, three graph formulations are viable. A **player-game bipartite graph** creates player nodes (with Elo, win rate, historical APM features) and match nodes (map, duration, patch), connected by "participated-in" edges carrying in-game statistics. A **temporal match graph** — the approach used by [Bisberg & Ferrara (2022)][gcn-wp] for League of Legends — represents each match as a node with edges connecting consecutive matches by the same player/team, enabling the GCN to propagate information along match history. A **within-match graph** models players as nodes in a single game with teammate/opponent edges, more suitable for real-time prediction. For heterogeneous node types, [PyTorch Geometric's][pyg-loader] `HeteroData` object and `to_hetero()` model conversion handle the type system.

### 2.2 Mini-batching strategies

Mini-batching strategy depends on graph structure. For graph-level classification where each match is a separate small graph, [PyTorch Geometric's standard `DataLoader`][pyg-batching] batches graphs by stacking adjacency matrices in block-diagonal format — the `batch.batch` tensor maps each node to its parent graph, essential for global pooling.

For a single large temporal graph, [`NeighborLoader`][pyg-neighbor] samples fixed-size neighborhoods per seed node ([Hamilton et al., 2017][pyg-neighbor-tutorial]), with the critical rule that the number of sampled hops must equal the number of GNN layers. [`ClusterLoader`][pyg-loader] (Chiang et al., 2019) partitions the graph into communities and is appropriate when natural cluster structure exists.

### 2.3 Training loop structure

The GNN training loop follows the standard PyTorch pattern: forward pass through message-passing layers, loss computation with `F.cross_entropy` or `BCEWithLogitsLoss`, backward pass, gradient clipping via `torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)`, and optimizer step. For graph-level prediction (the natural formulation for match outcome), a **global pooling readout** — `global_mean_pool`, `global_add_pool`, or `global_max_pool` — aggregates node representations into a single graph embedding before the classification head. The [UvA Deep Learning tutorial][uva-gnn] provides an excellent reference implementation.

### 2.4 Over-smoothing is the binding constraint on GNN depth

Li et al. (2018) proved that graph convolution is a form of Laplacian smoothing; stacking layers repeatedly smooths features until all node representations converge to indistinguishable vectors. Performance typically peaks at **2–3 layers** and degrades rapidly beyond 4.

Solutions include [residual connections][oversmoothing-residual] (`x_out = x_in + GNNLayer(x_in)`), Jumping Knowledge Networks (Xu et al., 2018) that concatenate representations from all layers, [DropEdge][dropout-gnn] (Rong et al., 2020) that randomly removes edges during training, and PairNorm (Zhao & Akoglu, 2020) that prevents feature convergence through normalization. [Eliasof et al. (2024)][oversmoothing-proof] provide formal guarantees that residual connections with normalization can provably prevent over-smoothing.

For esports GNNs, the practical recommendation is **2–3 GNN layers with residual connections and batch normalization**.

---

## 3. Loss Functions for Binary Classification

**Binary cross-entropy (log loss)** is the standard training objective for all model families. It is mathematically equivalent to the negative log-likelihood of a Bernoulli distribution, making it the maximum-likelihood-optimal loss for binary classification. XGBoost uses it internally as `binary:logistic`, LightGBM as `objective='binary'`, and PyTorch provides `BCEWithLogitsLoss` which fuses the sigmoid and BCE computation for numerical stability.

**[Focal loss][focal-loss]** (Lin et al., 2017) adds a modulating factor $(1 - p_t)^\gamma$ that downweights well-classified examples. With γ = 2, an easy example classified at $p_t = 0.9$ receives 100× less loss weight than a hard example at $p_t = 0.1$. For esports data where win/loss classes are typically near-balanced, focal loss is unnecessary unless specific matchup categories are systematically harder to classify.

**[Label smoothing][label-smoothing]** replaces hard targets {0, 1} with soft targets {ε/2, 1−ε/2} (typically ε = 0.1), preventing logit saturation and improving calibration ([Müller, Kornblith & Hinton, 2019][label-smoothing]). This is primarily relevant for GNNs since tree-based models do not use sigmoid outputs during training.

A critical conceptual distinction: the training loss and evaluation metrics need not be identical, but they must be compatible. You train with BCE (differentiable, strong gradients) and evaluate with AUC-ROC (ranking quality), Brier score (calibration), accuracy, and F1. [Guo et al. (2017)][calibration-deep] demonstrated that modern neural networks trained with cross-entropy are often poorly calibrated despite high accuracy — post-hoc temperature scaling or Platt scaling can address this for GNN models. [Cieslak et al. (2024)][loss-survey] provide a comprehensive taxonomy of loss functions and their relationship to evaluation metrics.

---

## 4. Early Stopping

[Early stopping][early-stopping] must use a temporally ordered validation set — **never the test set**, which constitutes a form of leakage that optimistically biases reported metrics.

**For XGBoost**: set `n_estimators=1000` (or higher) with `early_stopping_rounds=50` and pass a temporal `eval_set`; the model automatically restores the best iteration via `model.best_iteration`.

**For LightGBM**: use the [`lgb.early_stopping(stopping_rounds=50)`][lightgbm-tuning] callback (the older parameter-based API is deprecated).

**For PyTorch GNNs**: implement manual early stopping by tracking `best_val_loss`, saving `model.state_dict()` via `copy.deepcopy`, and restoring best weights when patience is exhausted.

Typical patience values are **10–50 rounds for boosting** (since each round adds only one tree at low cost) and **10–20 epochs for GNNs**. Monitor validation log loss for stability or validation AUC if discrimination is the primary concern.

---

## 5. Learning Rate Scheduling

[Learning rate scheduling][lr-scheduling] is relevant primarily for GNNs; tree-based models use a constant shrinkage rate with early stopping.

**Cosine annealing** ([Loshchilov & Hutter, 2017][lr-scheduling]) smoothly decays the learning rate following a half-cosine curve. The **one-cycle policy** (Smith & Topin, 2019) warms up the LR to a maximum, decays it, then annihilates it in the final 10–20% of training — achieving "super-convergence" because large learning rates act as implicit regularizers.

The **learning rate range test** (Smith, 2017) empirically identifies the optimal maximum LR by exponentially increasing LR over one epoch and selecting the value at the steepest loss decrease.

For Adam/AdamW with GNNs, a constant LR of **1e-3** is a strong default. When varying batch size, use the square root scaling rule (scale LR by √k when batch size scales by k), as the [linear scaling rule][goyal-2017] from Goyal et al. (2017) applies primarily to SGD with momentum.

---

## 6. Hyperparameter Tuning Strategies

### 6.1 Random search as the baseline

**Random search outperforms grid search** in high-dimensional spaces. [Bergstra & Bengio (2012)][bergstra-2012] demonstrated that real-world objective functions have **low effective dimensionality** — only a few hyperparameters truly matter. A 3×3 grid of 9 trials tests only 3 unique values of the important parameter, while 9 random trials test 9 unique values. Their rough budget heuristic: **10×d trials** (where d is the number of hyperparameters).

### 6.2 Bayesian optimization via Optuna

[Optuna][optuna] ([Akiba et al., 2019][optuna-github]) is the recommended approach for thesis-scale work. Its Tree-Parzen Estimator (TPE) models the distribution of hyperparameters conditioned on good vs. bad objective values, selecting configurations that maximize the ratio of "good" to "bad" density. Built-in pruning via `MedianPruner` terminates unpromising trials early. A budget of **100–200 trials** per model is the community-standard recommendation.

### 6.3 Multi-fidelity methods

[Hyperband][hyperband] (Li et al., 2017) runs many configurations at low budget, keeps only the top 1/η fraction, doubles their budget, and repeats. [BOHB][bohb] (Falkner et al., 2018) replaces Hyperband's random configuration sampling with TPE-based proposals, combining early-stopping efficiency with informed search. [Feurer & Hutter (2019)][automl-book] provide the definitive survey of the hyperparameter optimization landscape.

### 6.4 Key hyperparameters per model family

**Logistic regression** is dominated by a single hyperparameter: the inverse regularization strength **C**, searched on a log-uniform scale from 1e-4 to 1e4. The `penalty` and `solver` parameters form a conditional dependency that Optuna handles naturally. Importance ranking: C >> penalty > solver.

**Random forests** are most sensitive to `max_features` (0.3–0.8 or `sqrt`), followed by `min_samples_leaf` (1–20) and `max_depth` (None or 3–20). Set `n_estimators` high (500–1000) rather than tuning it — random forests do not overfit with more trees.

**[XGBoost][xgboost-hp] and [LightGBM][lightgbm-tuning]** require tuning `learning_rate` (0.01–0.3, log-uniform) jointly with `n_estimators` (via early stopping, not direct tuning), `subsample` (0.6–1.0), `colsample_bytree` (0.6–1.0), and regularization terms `reg_alpha` and `reg_lambda` (1e-8 to 10, log-uniform). XGBoost's primary complexity parameter is `max_depth` (3–10), interacting with `min_child_weight` (1–10). LightGBM's leaf-wise growth uses `num_leaves` (20–300) with the critical constraint that **num_leaves < 2^max_depth** to prevent overfitting.

Most important interaction pairs: learning_rate × n_estimators (inversely related), max_depth × min_child_weight (XGBoost), num_leaves × max_depth (LightGBM). [Weerts et al. (2022)][hp-study] provide a large-scale empirical study of hyperparameter importance across model families.

**[GNN hyperparameters][gnn-tuning]** center on: `hidden_dim` (32–256), `num_layers` (2–4, constrained by [over-smoothing][oversmoothing-acm]), `dropout` (0.1–0.5), `learning_rate` (1e-4 to 1e-2, log-uniform), `weight_decay` (1e-5 to 1e-2), and `aggregation` function (mean, sum, max — where sum preserves structural information per the GIN paper by Xu et al., 2019). The num_layers × hidden_dim interaction is critical: over-smoothing at depth > 4 means increasing hidden_dim cannot compensate for too many layers.

---

## 7. Temporal Cross-Validation with Nested Inner and Outer Loops

Standard k-fold cross-validation is invalid for esports match data because random shuffling allows future information to leak into training folds. The correct approach uses **expanding-window (forward-chaining) splits**: train on months 1–6, validate on month 7; train on months 1–7, validate on month 8; and so on.

Hyperparameter tuning must be embedded within a **nested temporal cross-validation** structure per the framework established in [03_SPLITTING_AND_BASELINES_MANUAL.md](03_SPLITTING_AND_BASELINES_MANUAL.md). The outer loop provides unbiased performance estimation. For each outer fold, the inner loop performs hyperparameter optimization. Without this nesting, the hyperparameters are tuned on the same data used for evaluation, producing selection bias that [Cawley & Talbot (2010)][cawley-2010] demonstrated can equal inter-model differences. See also [scikit-learn's nested CV example][sklearn-nested] and [Cochrane's temporal nested CV walkthrough][cochrane-nested].

The computational cost is substantial: 5 outer folds × 100 Optuna trials × 3 inner folds = **1,500 model fits per model type**. Mitigation strategies include Optuna's `MedianPruner` for early trial termination, early stopping for boosting models, limiting inner folds to 2–3, and parallelizing with `n_jobs`.

To ensure a fair comparison across model families, each model must receive **equivalent tuning effort** — the same number of Optuna trials, the same inner CV structure, and the same computational budget. Comparing a heavily-tuned XGBoost against a default-hyperparameter GNN invalidates the comparison entirely.

---

## 8. Reproducibility: Seeds, Logging, and Environment Control

### 8.1 Random seed management

A canonical `seed_everything()` function must set seeds for Python's `random` module, NumPy (`np.random.seed`), [PyTorch][pytorch-repro] (`torch.manual_seed`, `torch.cuda.manual_seed_all`), and the `PYTHONHASHSEED` environment variable. Scikit-learn lacks a global seed mechanism — pass `random_state=seed` to every estimator and splitting function.

**Setting seeds does not guarantee exact GPU reproducibility.** CUDA's `atomicAdd` operations introduce non-deterministic rounding errors. Setting `torch.backends.cudnn.deterministic = True` and `torch.backends.cudnn.benchmark = False` partially addresses this. The strongest guarantee is [`torch.use_deterministic_algorithms(True)`][pytorch-deterministic], which forces all operations to use deterministic implementations and raises `RuntimeError` when none exists — but at a [significant performance cost][pytorch-determ-perf] (benchmarks show **2–3× slowdown**). The `CUBLAS_WORKSPACE_CONFIG=:4096:8` environment variable is required for cuBLAS determinism on CUDA ≥10.2.

### 8.2 The Heil et al. (2021) reproducibility tiers

[Heil et al. (2021)][heil-2021] in *Nature Methods* proposed a three-tier system for ML reproducibility:

| Tier | Requirements |
|------|-------------|
| **Bronze** | All data, trained models, and code publicly available on persistent repositories |
| **Silver** | Adds version control, documentation, dependency management, unit tests |
| **Gold** | Full workflow automation — single command regenerates all results from raw data |

A master's thesis should target **Silver standard** at minimum. The [ML Reproducibility Checklist v2.0][pineau-checklist] (Pineau et al., 2021) and the [REFORMS checklist][reforms] (Kapoor et al., 2024, *Science Advances*) provide additional structured frameworks.

### 8.3 Experiment logging requirements

Every training run must log: all hyperparameters and optimizer settings, random seeds, training and validation loss curves, all final metrics, model checkpoints at best validation performance, dataset file hashes (SHA-256), git commit hash, hardware specifications, full package versions (`pip freeze`), and wall-clock training time.

For a thesis, structured JSON logs and a CSV results tracker (one row per experiment) provide a lightweight but sufficient solution. [MLflow and Weights & Biases][mlflow-wandb] provide richer experiment management if overhead is justified.

Results should be presented as **mean ± standard deviation across at least 5 random seeds**. Essential thesis figures include: a model comparison table, a hyperparameter table listing final tuned values, a computational cost table, training/validation loss curves, overlaid ROC curves, and box plots showing metric distributions across seeds.

---

## 9. Twelve Common Training Mistakes

### Leakage errors

1. **Fitting preprocessing on the full dataset before splitting** — inflates CV scores by allowing test-fold statistics into training
2. **Using post-match statistics as features** — anything unavailable one second before match start is leakage
3. **Performing early stopping on the test set** rather than a separate validation set

### Evaluation errors

4. **Using default hyperparameters and claiming fair comparison** — different algorithms have different tuning sensitivities ([Weerts et al., 2022][hp-study])
5. **Reporting single-seed results** without variance estimates
6. **Not monitoring training/validation curves** for overfitting
7. **Shuffling data across temporal boundaries** — within-fold shuffling for mini-batching is acceptable; across-fold shuffling is not

### GNN-specific errors

8. **Gradient explosion** from unstable training dynamics — mitigate with gradient clipping at `max_norm=1.0`, Xavier/Kaiming initialization, and batch normalization
9. **Over-smoothing from too many message-passing layers** — keep to 2–3 layers with residual connections
10. **Failing to distinguish node-level vs. graph-level prediction** when the problem structure clearly calls for one formulation

### Reporting errors

11. **Not reporting training time and computational resources** — a model that takes 100× longer to train for 0.5% accuracy gain is not practically superior
12. **Claiming significance without statistical tests** — use Wilcoxon signed-rank across seeds and outer CV folds

---

## Conclusion

The training and tuning methodology for this thesis rests on three non-negotiable principles.

**All preprocessing must live inside sklearn Pipelines** for tabular models and within the training loop for GNNs — any preprocessing outside the resampling loop constitutes data leakage that can bias results by margins larger than inter-model performance differences.

**Hyperparameter optimization must respect temporal structure** through nested cross-validation with `TimeSeriesSplit` in both inner and outer loops, using Optuna's TPE sampler with 100–200 trials per model family and equal tuning budgets across all models being compared.

**Reproducibility demands systematic seed management, comprehensive logging, and variance reporting** — single-seed results are insufficient for drawing conclusions, and the [Heil et al.][heil-2021] Silver standard provides the appropriate target for a master's thesis.

The key architectural insight for GNNs on esports data is that **over-smoothing, not underfitting, is the binding constraint**: 2–3 message-passing layers with residual connections, cosine annealing or one-cycle LR scheduling, and graph-level pooling constitute the empirically grounded starting configuration. For tree-based models, early stopping on a temporal validation set effectively removes `n_estimators` from the search space, allowing tuning budget to focus on the genuinely important parameters. The [Bergstra & Bengio (2012)][bergstra-2012] insight that random search outperforms grid search due to low effective dimensionality provides the theoretical foundation, while Bayesian optimization via [Optuna][optuna] provides the practical efficiency gain.

---

## References

<!-- Pipeline architecture and leakage prevention -->
[cawley-2010]: https://www.jmlr.org/papers/volume11/cawley10a/cawley10a.pdf "Cawley & Talbot (2010) — On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation. JMLR, 11:2079–2107"
[sklearn-pipeline]: https://scikit-learn.org/stable/modules/compose.html "Pipelines and composite estimators — scikit-learn documentation"
[sklearn-persistence]: https://scikit-learn.org/1.3/model_persistence.html "Model persistence — scikit-learn documentation"

<!-- GNN training -->
[gcn-wp]: https://ieeexplore.ieee.org/document/9893671/ "Bisberg & Ferrara (2022) — GCN-WP: Semi-Supervised Graph Convolutional Networks for Win Prediction in Esports. IEEE"
[pyg-loader]: https://pytorch-geometric.readthedocs.io/en/latest/modules/loader.html "torch_geometric.loader — PyTorch Geometric documentation"
[pyg-batching]: https://pytorch-geometric.readthedocs.io/en/2.5.2/advanced/batching.html "Advanced Mini-Batching — PyTorch Geometric documentation"
[pyg-neighbor]: https://pytorch-geometric.readthedocs.io/en/2.5.2/tutorial/neighbor_loader.html "Scaling GNNs via Neighbor Sampling — PyTorch Geometric tutorial"
[pyg-neighbor-tutorial]: https://github.com/pyg-team/pytorch_geometric/blob/master/docs/source/tutorial/neighbor_loader.rst "NeighborLoader tutorial source — PyTorch Geometric (GitHub)"
[uva-gnn]: https://uvadlc-notebooks.readthedocs.io/en/latest/tutorial_notebooks/tutorial7/GNN_overview.html "Tutorial 7: Graph Neural Networks — UvA Deep Learning Notebooks"

<!-- Over-smoothing -->
[oversmoothing-residual]: https://link.springer.com/article/10.1007/s10994-025-06822-0 "Analyzing the effect of residual connections to oversmoothing in GNNs. Machine Learning (Springer, 2025)"
[oversmoothing-proof]: https://arxiv.org/html/2406.02997v2 "Eliasof et al. (2024) — Residual Connections and Normalization Can Provably Prevent Oversmoothing in GNNs. arXiv:2406.02997"
[dropout-gnn]: https://dl.acm.org/doi/fullHtml/10.1145/3487553.3524725 "Understanding Dropout for Graph Neural Networks. ACM Web Conference 2022"
[oversmoothing-acm]: https://dl.acm.org/doi/10.1145/3627673.3679776 "Beyond Over-smoothing: Uncovering the Trainability Challenges in Deep GNNs. CIKM 2024"

<!-- Loss functions -->
[focal-loss]: https://skscope.readthedocs.io/en/0.1.7/gallery/Miscellaneous/focal-loss-with-imbalanced-data.html "Classification on imbalanced labels with focal loss — skscope documentation"
[label-smoothing]: https://medium.com/@shekhar.manna83/ml-ai-label-smoothing-for-regularization-a-comprehensive-guide-ae7412022a3d "Label Smoothing for Regularization: A Comprehensive Guide"
[loss-survey]: https://arxiv.org/html/2307.02694v5 "Cieslak et al. (2024) — Loss Functions and Metrics in Deep Learning. arXiv:2307.02694"
[calibration-deep]: http://alondaks.com/2017/12/31/the-importance-of-calibrating-your-deep-model/ "Guo et al. (2017) — On Calibration of Modern Neural Networks (via Daks overview)"

<!-- Early stopping -->
[early-stopping]: https://machinelearningmastery.com/early-stopping-to-avoid-overtraining-neural-network-models/ "Brownlee — A Gentle Introduction to Early Stopping. MachineLearningMastery"
[lightgbm-tuning]: https://lightgbm.readthedocs.io/en/latest/Parameters-Tuning.html "Parameters Tuning — LightGBM documentation"

<!-- Learning rate scheduling -->
[lr-scheduling]: https://d2l.ai/chapter_optimization/lr-scheduler.html "Learning Rate Scheduling — Dive into Deep Learning"
[goyal-2017]: https://www.researchgate.net/publication/317418674_Accurate_Large_Minibatch_SGD_Training_ImageNet_in_1_Hour "Goyal et al. (2017) — Accurate, Large Minibatch SGD: Training ImageNet in 1 Hour"

<!-- Hyperparameter optimization -->
[bergstra-2012]: https://jmlr.org/papers/v13/bergstra12a.html "Bergstra & Bengio (2012) — Random Search for Hyper-Parameter Optimization. JMLR, 13:281–305"
[optuna]: https://optuna.org/ "Optuna — A hyperparameter optimization framework"
[optuna-github]: https://github.com/optuna/optuna "Optuna GitHub repository (Akiba et al., 2019)"
[automl-book]: https://link.springer.com/chapter/10.1007/978-3-030-05318-5_1 "Feurer & Hutter (2019) — Hyperparameter Optimization. In: AutoML: Methods, Systems, Challenges (Springer)"
[hyperband]: https://papers.neurips.cc/paper_files/paper/2022/file/57b694fef23ae7b9308eb4d46342595d-Paper-Conference.pdf "Li et al. — Hyperband and multi-fidelity optimization (NeurIPS)"
[bohb]: https://arxiv.org/html/2402.13641v1 "BOHB and FlexHB: efficient multi-fidelity hyperparameter optimization. arXiv:2402.13641"

<!-- Hyperparameter ranges per model -->
[xgboost-hp]: https://xgboosting.com/most-important-xgboost-hyperparameters-to-tune/ "Most Important XGBoost Hyperparameters to Tune — XGBoosting"
[gnn-tuning]: https://www.analyticsvidhya.com/blog/2021/05/tuning-the-hyperparameters-and-layers-of-neural-network-deep-learning/ "Tuning the Hyperparameters and Layers of Neural Networks — Analytics Vidhya"
[hp-study]: https://www.mdpi.com/1999-4893/15/9/315 "Weerts et al. (2022) — A Large-Scale Study of Hyperparameter Tuning for ML Algorithms. Algorithms, 15(9):315"

<!-- Temporal nested CV -->
[sklearn-nested]: https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html "Nested versus non-nested cross-validation — scikit-learn documentation"
[cochrane-nested]: https://medium.com/data-science/time-series-nested-cross-validation-76adba623eb9 "Cochrane — Time Series Nested Cross-Validation. Towards Data Science"

<!-- Reproducibility -->
[pytorch-repro]: https://docs.pytorch.org/docs/stable/notes/randomness.html "Reproducibility — PyTorch documentation"
[pytorch-deterministic]: https://docs.pytorch.org/docs/stable/generated/torch.use_deterministic_algorithms.html "torch.use_deterministic_algorithms — PyTorch documentation"
[pytorch-determ-perf]: https://github.com/pytorch/pytorch/issues/109856 "Severe performance regression on deterministic algorithms — PyTorch GitHub Issue #109856"
[heil-2021]: https://pubmed.ncbi.nlm.nih.gov/34462593/ "Heil et al. (2021) — Reproducibility Standards for Machine Learning in the Life Sciences. Nature Methods, 18:1132–1135"
[pineau-checklist]: https://www.cs.mcgill.ca/~jpineau/ReproducibilityChecklist.pdf "Pineau et al. (2021) — The Machine Learning Reproducibility Checklist v2.0. McGill University"
[reforms]: https://www.science.org/doi/10.1126/sciadv.adk3452 "Kapoor et al. (2024) — REFORMS: Consensus-based Recommendations for ML-based Science. Science Advances"
[mlflow-wandb]: https://www.zenml.io/blog/mlflow-vs-weights-and-biases "MLflow vs Weights & Biases — ZenML comparison"