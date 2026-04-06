# Cross-Domain Transfer Experiments: SC2 ↔ AoE2

> **The most appropriate transfer framework for comparing win prediction between StarCraft II and Age of Empires II is heterogeneous feature-representation transfer**, where manually constructed abstract features bridge two structurally different domains that share no raw features.

This is a fundamentally harder problem than standard domain adaptation because SC2 and AoE2 differ not just in distributions but in feature spaces entirely — a distinction [Pan & Yang (2010)][pan-yang] classify as heterogeneous transfer and [Ben-David et al. (2010)][ben-david] show is bounded by both domain divergence and irreducible joint hypothesis error. No existing work has attempted direct model transfer between RTS titles, making this a genuine research contribution.

---

## 1. Transfer Learning Taxonomy: Positioning the SC2 ↔ AoE2 Problem

[Pan & Yang's (2010)][pan-yang] foundational survey defines transfer learning around two primitives: a **domain** D = {X, P(X)} and a **task** T = {Y, P(Y|X)}. Transfer learning improves learning of the target predictive function using knowledge from a source domain where either D_S ≠ D_T or T_S ≠ T_T.

The taxonomy identifies three settings: **inductive transfer** (tasks differ, some target labels available), **transductive transfer** (domains differ, task is the same — standard domain adaptation), and **unsupervised transfer** (no labels in either domain). SC2-to-AoE2 prediction is best classified as **inductive transfer with heterogeneous feature spaces**: both games have labeled outcomes, the task is conceptually identical, but feature spaces are entirely different.

The critical distinction is between **homogeneous transfer** (X_S = X_T, bridging distribution gaps) and **heterogeneous transfer** (X_S ≠ X_T, requiring feature space alignment). [Weiss, Khoshgoftaar & Wang (2016)][weiss-2016] extended this taxonomy with practical guidance on symmetric vs. asymmetric transformation. [Day & Khoshgoftaar (2017)][day-2017] provided a dedicated survey of heterogeneous methods including feature-space remapping and manifold alignment.

Three distinct forms of "transfer" apply to this thesis, in increasing ambition:

| Level | What transfers | Evidence strength |
|-------|---------------|-------------------|
| **Methodological pipeline** | Feature engineering philosophy, model families, evaluation protocol | Defensible from n=2 domains |
| **Feature representation** | Shared abstract feature space enabling direct model application | Requires Tier 2 experiments |
| **Model weights** | Trained parameters from one game applied to another | Strongest claim, highest risk |

---

## 2. Ben-David's Bound: When Is Transfer Theoretically Possible?

The theoretical foundation comes from [Ben-David et al.'s (2010)][ben-david] paper in *Machine Learning*. Their central theorem bounds target domain error:

$$\varepsilon_T(h) \leq \varepsilon_S(h) + \frac{1}{2} d_{H\Delta H}(D_S, D_T) + \lambda^*$$

where ε_S(h) is source error, $d_{H\Delta H}$ is the symmetric difference divergence between domains, and **λ\*** is the combined error of the ideal joint hypothesis — the best classifier that performs well on *both* domains simultaneously.

This λ\* term is critical: **if no single hypothesis works well in both domains, adaptation is fundamentally limited regardless of divergence minimization.** For SC2↔AoE2, λ\* captures the irreducible difference in how Elo gaps, matchup asymmetry, and form translate into win probability across games with different mechanics.

Four domain distance measures are standard:

| Measure | What it captures | Connection to theory |
|---------|-----------------|---------------------|
| **Proxy A-distance (PAD)** | d̂_A = 2(1 − 2ε) from a domain classifier | Directly approximates Ben-David's d_{H∆H} |
| **Maximum Mean Discrepancy (MMD)** | Distance between mean embeddings in RKHS | Used in Transfer Component Analysis |
| **Wasserstein distance** | Optimal transport cost | Geometrically meaningful |
| **H-divergence** | Theoretical quantity from the bound | Approximated by PAD in practice |

For the thesis, computing **PAD and MMD** on the shared abstract feature representations would quantify how "far apart" SC2 and AoE2 are in the aligned space, providing empirical grounding for transfer expectations.

---

## 3. Types of Distribution Shift Between SC2 and AoE2

The [dataset shift taxonomy][dataset-shift] catalogues three types. **Covariate shift** (P(X) differs while P(Y|X) stays constant) would occur if SC2 and AoE2 players simply had different skill distributions but skill predicted wins identically. **Prior probability shift** (P(Y) differs) would occur if one game had systematically different win rates. **[Concept shift][domain-adaptation]** (P(Y|X) differs) — the hardest case — occurs when the same feature values predict different outcomes.

The SC2↔AoE2 comparison likely involves **all three shifts simultaneously** once features are mapped to a shared space: different player skill distributions (covariate), potentially different overall win rates depending on matchmaking quality (prior), and — most critically — a 200-Elo gap may carry different predictive weight across games with different matchmaking systems and player pool sizes (concept). This makes it a **full dataset shift problem**.

---

## 4. Constructing a Shared Feature Space

Since SC2 and AoE2 share no raw features, the thesis must construct a **domain-invariant abstract feature schema**:

| Abstract feature | SC2 instantiation | AoE2 instantiation |
|---|---|---|
| Normalized skill rating | Z-scored MMR within population | Z-scored Elo within population |
| Rating gap | Signed MMR difference | Signed Elo difference |
| Matchup asymmetry | Historical race-pair win rate (6 matchups from 3 races) | Historical civ-pair win rate (1000+ matchups from 45+ civs) |
| Recent form | Rolling win rate over last N matches | Rolling win rate over last N matches |
| Experience level | Log-transformed career games played | Log-transformed career games played |
| Map factor | Race win rate deviation on specific map | Civ win rate deviation on specific map |

This manual construction is itself a form of heterogeneous transfer — **transferring the feature engineering methodology**. Standard automated alignment methods like [CORAL][coral] (Sun, Feng & Saenko, 2016) and [Subspace Alignment][subspace-alignment] (Fernando et al., 2013) require a shared input space and thus cannot operate on raw game data. However, once abstract features are constructed, these methods become applicable for fine-tuning distribution alignment.

[Domain-Adversarial Neural Networks (DANN)][dann] (Ganin et al., 2016) can learn domain-invariant representations through a gradient reversal layer, but require separate encoder heads for each game's raw features. A recent paper on [game-invariant features through contrastive and domain-adversarial learning][game-invariant] explores this direction specifically for competitive games.

### Handling the matchup granularity asymmetry

SC2's 3 races versus AoE2's 45+ civilizations is the hardest structural mismatch. The practical approach: compress AoE2 civilizations into **archetype clusters** (cavalry civs, archer civs, infantry civs) paralleling SC2's race-level categories, then compute matchup asymmetry at the cluster level. This reduces dimensionality while preserving the conceptual parallel.

### Data richness imbalance

SC2 replay files provide frame-by-frame game state reconstruction through libraries like [`sc2reader`][sc2reader]. AoE2's public data is primarily match metadata from aoestats.io: ratings, civilization picks, map, duration, and win/loss. **Cross-game models must therefore operate at the lowest common denominator: pre-match metadata features.** This constraint, counterintuitively, makes the transfer problem cleaner by eliminating replay-specific features.

---

## 5. Negative Transfer: When Transfer Hurts

[Rosenstein et al. (2005)][rosenstein-2005] demonstrated that transfer from dissimilar sources actively hurts performance, particularly with **very few target training examples**. As target data increases, both positive and negative transfer effects diminish.

[Wang et al. (CVPR 2019)][negative-transfer-cvpr] formalized the **Negative Transfer Gap** as NTG = accuracy_without_transfer − accuracy_with_transfer; positive NTG indicates harmful transfer. Prevention strategies from the literature:

- **Always benchmark against a no-transfer baseline** — the single most important experimental control
- **Monitor learning curves** during training for performance degradation
- **Compute domain divergence** (PAD, MMD) before transfer to assess feasibility
- **Use selective/weighted transfer** rather than brute-force source data merging
- **Regularize** the transfer model to constrain deviation from the target-only baseline

For the thesis, negative transfer would itself be a valuable finding — it would reveal that SC2 and AoE2 have sufficiently different P(Y|X) structures that knowledge from one misleads prediction in the other.

---

## 6. Three-Tier Experimental Design

### Tier 1: Parallel pipeline comparison

Run an identical methodology on both games independently: same preprocessing logic, same model families, same evaluation metrics, same statistical tests. Use [temporal train/test splits][sklearn-tss] as established in [03_SPLITTING_AND_BASELINES_MANUAL.md](03_SPLITTING_AND_BASELINES_MANUAL.md). If the same pipeline achieves comparable performance on both games, this demonstrates **methodological generalization**.

### Tier 2: Feature-level transfer experiments

Four conditions isolate transfer benefit:

| Condition | Training data | Tests on | Purpose |
|---|---|---|---|
| **Target-only** | AoE2 | AoE2 | Baseline — what target data alone achieves |
| **Zero-shot** | SC2 (abstract features) | AoE2 | Direct transfer without adaptation |
| **Fine-tuned** | SC2 pretrained → AoE2 fine-tuned | AoE2 | Transfer with target adaptation |
| **Combined** | SC2 + AoE2 pooled | AoE2 | Joint training benefit |

The **transfer ratio** = Performance(transferred) / Performance(target-only) is the headline metric. Ratios above 1.0 indicate positive transfer; below 1.0 indicate negative transfer. Run the symmetric experiment (AoE2 → SC2) as well.

Statistical significance: McNemar's test for accuracy, DeLong's test for AUC, bootstrap CIs for Brier score. [Dietterich's 5×2cv test][dietterich-1998] when budget allows 10 training runs. [Holm-Bonferroni correction][holm] for multiple comparisons.

[Gulrajani & Lopez-Paz (ICLR 2021)][gulrajani-2021] found that simple pooled ERM (combining all domain data with standard training) is surprisingly hard to beat, supporting the value of the combined-training condition.

### Tier 3: Component ablation

Systematically isolate which pipeline components generalize. The ablation matrix varies one component at a time:

- Transfer feature engineering logic but retrain the model
- Transfer model architecture but re-engineer features
- Transfer hyperparameter ranges but re-tune everything else

This identifies whether value lies in feature abstractions, model family choice, or full pipeline configuration.

### Meta-learning: acknowledged but scoped out

[MAML][maml] (Finn, Abbeel & Levine, 2017) and multi-task networks are theoretically applicable but likely **overkill for a master's thesis with only two domains**. MAML requires a distribution over tasks; n=2 is insufficient. Multi-task learning is a reasonable stretch goal if time permits. Cross-game [transfer learning in deep RL][transfer-rl] has been explored for game-playing agents but not for outcome prediction.

---

## 7. Evaluating and Reporting Transfer Results

### Transferability estimation metrics

Before full experiments, **transferability scores** can predict transfer success. [LEEP][leep] (Nguyen et al., ICML 2020) computes a score from source model predictions on target data. [H-score][h-score] (Bao et al., NeurIPS 2019) provides an information-theoretic evaluation. These can be reported as preliminary evidence.

### Cross-domain chapter structure

1. Motivation and research questions
2. Experimental setup with complete reproducibility details
3. Within-domain standalone results for each game
4. Cross-domain feature analysis — distribution comparisons on aligned features
5. Transfer experiment results across all conditions
6. Ablation analysis
7. Statistical significance testing
8. Discussion of limitations

### Essential figures and tables

**Figures**: learning curves showing where transfer reduces target data requirements; feature distribution overlays comparing aligned features between domains; calibration plots for probabilistic predictions; ROC curves overlaid for all conditions.

**Tables**: dataset statistics comparison; feature mapping schema; within-domain performance; transfer condition comparisons with CIs; feature importance rankings per game (do the same features matter in both?).

### Reproducibility

Per the [REFORMS checklist][reforms] and [Pineau et al.'s reproducibility checklist][pineau], report all hyperparameters, random seeds, exact data splits, software versions, and training times. The [ADAPT library][adapt] (de Mathelin et al., 2021) provides scikit-learn-compatible domain adaptation with feature-based, instance-based, and parameter-based modules. The [Transfer Learning Library (TLlib)][tllib] offers PyTorch implementations of DANN, CDAN, and other deep methods.

---

## 8. What Honest Claims Look Like with Two Domains

The most critical framing decision is the distinction between **"the methodology generalizes"** and **"the model generalizes."** Methodological generalization — that the same approach works independently on both games — is defensible from n=2. Model generalization — that a model trained on one game works on the other — is a stronger claim requiring Tier 2 experiments.

With only two domains, external validity is inherently limited. [Gulrajani & Lopez-Paz (2021)][gulrajani-2021] formalized that claims about algorithm generalization across problems require sufficient problem diversity. [Anglin (2024)][anglin-2024] catalogued threats to validity in supervised ML: sample × prediction interaction, setting × prediction interaction (unique game mechanics), time × prediction interaction (patch-driven meta shifts), and **construct validity** (does "economy advantage" mean the same thing in SC2 and AoE2?).

### Defensible language patterns

- "We provide *preliminary evidence* that [methodology/features] transfer across RTS domains"
- "Our results suggest that rating-based and matchup features are predictive *at least* across these two RTS games"
- "The two-domain comparison is *illustrative* rather than *conclusive* regarding generalizability"

The discussion should explicitly recommend extending to additional games (Warcraft III, Command & Conquer, Company of Heroes) as future work to strengthen generalizability claims.

---

## 9. Which Components Are Most Likely to Transfer?

Based on the theoretical framework and structural analysis:

| Component | Transfer likelihood | Rationale |
|-----------|-------------------|-----------|
| **Rating-based features** (Elo gap, normalized rating) | **High** | Both games use logistic win probability models; [Elo/Glicko][trueskill] are game-agnostic by design |
| **Recent form** (rolling win rate) | **High** | Captures universal momentum/confidence dynamics |
| **Experience level** (career games) | **Medium** | Learning curves exist in all games but rates differ |
| **Matchup asymmetry** | **Low** | 3-race hard counters vs. 45-civ soft asymmetries — fundamentally different structure |
| **Map effects** | **Low** | Map pools, design philosophy, and strategic impact differ substantially |
| **Model architecture** (XGBoost, LR) | **Medium** | Model families are domain-agnostic; hyperparameter ranges may not transfer |
| **Evaluation methodology** | **High** | Metrics, statistical tests, and temporal splitting are universal |

This ranking generates testable predictions: if the thesis finds that removing matchup features has little effect on transfer performance but removing rating features causes large degradation, the theoretical expectation is confirmed empirically.

---

## Conclusion

The SC2↔AoE2 transfer problem sits at the intersection of heterogeneous transfer learning, domain adaptation theory, and applied esports analytics — a space with **no existing direct precedent**. The closest prior work is [Shaker et al.'s (2016)][shaker-2016] IEEE CIG paper on cross-game player experience transfer, but no one has attempted to transfer win prediction models between RTS titles.

The [Ben-David bound][ben-david] provides formal justification for measuring domain divergence, while the practical constraint of data asymmetry forces the analysis to pre-match metadata — which makes transfer cleaner by eliminating replay-specific features. The three-tier design (parallel comparison → feature-level transfer → component ablation) creates a graduated evidence structure where **each tier provides value even if subsequent tiers reveal negative transfer**.

Rating-based features are the strongest transfer candidates given that both Elo and MMR implement logistic win probability models. Matchup asymmetry features face the highest transfer risk due to the 3-race versus 45-civilization structural mismatch. The thesis should measure domain distance (PAD, MMD) on aligned features, always benchmark against target-only models, and frame both positive and negative transfer findings as contributions to understanding cross-domain prediction in competitive gaming.

---

## References

<!-- Transfer learning foundations -->
[pan-yang]: https://www.cse.ust.hk/~qyang/Docs/2009/tkde_transfer_learning.pdf "Pan & Yang (2010) — A Survey on Transfer Learning. IEEE TKDE, 22(10):1345–1359"
[ben-david]: https://link.springer.com/article/10.1007/s10994-009-5152-4 "Ben-David et al. (2010) — A Theory of Learning from Different Domains. Machine Learning, 79(1):151–175"
[weiss-2016]: https://link.springer.com/article/10.1186/s40537-016-0043-6 "Weiss, Khoshgoftaar & Wang (2016) — A Survey of Transfer Learning. Journal of Big Data, 3:9"
[day-2017]: https://journalofbigdata.springeropen.com/articles/10.1186/s40537-017-0089-0 "Day & Khoshgoftaar (2017) — A Survey on Heterogeneous Transfer Learning. Journal of Big Data, 4:29"

<!-- Domain shift and adaptation theory -->
[dataset-shift]: https://superwise.ai/blog/everything-you-need-to-know-about-drift-in-machine-learning/ "Dataset shift types — covariate, prior, concept shift overview"
[domain-adaptation]: https://en.wikipedia.org/wiki/Domain_adaptation "Domain Adaptation — Wikipedia"
[dann]: https://medium.com/@prabhs./domain-adversarial-neural-networks-dann-explained-f73c9740ff49 "Domain-Adversarial Neural Networks (DANN) — explained (Ganin et al., 2016)"
[game-invariant]: https://arxiv.org/html/2505.17328 "Game-invariant Features Through Contrastive and Domain-adversarial Learning. arXiv:2505.17328"

<!-- Feature alignment methods -->
[coral]: https://arxiv.org/abs/1612.01939 "Sun, Feng & Saenko (2016) — Correlation Alignment for Unsupervised Domain Adaptation. arXiv:1612.01939"
[subspace-alignment]: https://www.semanticscholar.org/paper/Unsupervised-Visual-Domain-Adaptation-Using-Fernando-Habrard/28ef938aaa312d76df988f636e248a6b267b6352 "Fernando et al. (2013) — Unsupervised Visual Domain Adaptation Using Subspace Alignment. ICCV"

<!-- Negative transfer -->
[rosenstein-2005]: https://web.engr.oregonstate.edu/~tgd/publications/rosenstein-marx-kaelbling-dietterich-hnb-nips2005-transfer-workshop.pdf "Rosenstein et al. (2005) — To Transfer or Not to Transfer. NIPS Workshop on Inductive Transfer"
[negative-transfer-cvpr]: https://openaccess.thecvf.com/content_CVPR_2019/papers/Wang_Characterizing_and_Avoiding_Negative_Transfer_CVPR_2019_paper.pdf "Wang et al. (2019) — Characterizing and Avoiding Negative Transfer. CVPR"

<!-- Game data sources -->
[sc2reader]: https://github.com/GraylinKim/sc2reader "sc2reader — Python library for StarCraft II replay parsing (GitHub)"
[aoe2-resources]: https://github.com/Arkanosis/awesome-aoe2 "Awesome Age of Empires II — curated resource list (GitHub)"

<!-- Experimental design and statistical tests -->
[sklearn-tss]: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html "TimeSeriesSplit — scikit-learn documentation"
[dietterich-1998]: https://pubmed.ncbi.nlm.nih.gov/9744903/ "Dietterich (1998) — Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms. Neural Computation"
[holm]: https://en.wikipedia.org/wiki/Holm%E2%80%93Bonferroni_method "Holm–Bonferroni method — Wikipedia"

<!-- Meta-learning and multi-task -->
[maml]: https://instadeep.com/2021/10/model-agnostic-meta-learning-made-simple/ "Model-Agnostic Meta-Learning (MAML) — InstaDeep introduction"
[transfer-rl]: https://pmc.ncbi.nlm.nih.gov/articles/PMC11018366/ "Zhu et al. (2023) — Transfer Learning in Deep Reinforcement Learning: A Survey. PMC"
[gulrajani-2021]: https://openreview.net/pdf?id=mPducS1MsEK "Gulrajani & Lopez-Paz (2021) — In Search of Lost Domain Generalization. ICLR"

<!-- Transfer evaluation metrics -->
[leep]: https://arxiv.org/pdf/2002.12462 "Nguyen et al. (2020) — LEEP: A New Measure to Evaluate Transferability of Learned Representations. ICML"
[h-score]: https://openreview.net/forum?id=BkxAUjRqY7 "Bao et al. (2019) — An Information-Theoretic Metric of Transferability for Task Transfer Learning. NeurIPS"

<!-- Reproducibility and reporting -->
[reforms]: https://www.science.org/doi/10.1126/sciadv.adk3452 "Kapoor et al. (2024) — REFORMS: Consensus-based Recommendations for ML-based Science. Science Advances"
[pineau]: https://onlinelibrary.wiley.com/doi/10.1002/aaai.70002 "Semmelrock et al. (2025) — Reproducibility in ML-based Research: Overview, Barriers, and Drivers. AI Magazine"
[anglin-2024]: https://journals.sagepub.com/doi/full/10.1177/23328584241303495 "Anglin (2024) — Addressing Threats to Validity in Supervised ML. AERA Open"

<!-- Domain adaptation libraries -->
[adapt]: https://github.com/adapt-python/adapt "ADAPT — Awesome Domain Adaptation Python Toolbox (de Mathelin et al., 2021)"
[tllib]: https://github.com/thuml/Transfer-Learning-Library "Transfer Learning Library (TLlib) — Tsinghua University (GitHub)"

<!-- Cross-game prior work -->
[shaker-2016]: https://ieeexplore.ieee.org/document/7860415 "Shaker et al. (2016) — Transfer Learning for Cross-Game Prediction of Player Experience. IEEE CIG"
[trueskill]: https://en.wikipedia.org/wiki/TrueSkill "TrueSkill rating system — Wikipedia (game-agnostic skill estimation)"
