# How to Write an Excellent ML Master's Thesis

> **A data science master's thesis succeeds or fails on three pillars: rigorous experimental methodology, clear scientific writing, and honest critical analysis.**

For a comparative study of game prediction methods across StarCraft II and Age of Empires II, the stakes are high — you're navigating three distinct literatures (esports analytics, ML methodology, game AI), comparing multiple model families (tabular ML, GNNs, baselines) across two domains, and must demonstrate that your evaluation is statistically sound. This document distills academic standards, structural requirements, workflow strategies, and common pitfalls drawn from European university guidelines (including Polish institutions), ML research methodology literature, and published esports prediction theses.

The single most important insight: **structure and scientific quality are the two criteria most predictive of thesis grade**. Everything below is oriented toward maximizing both.

---

## 1. The Anatomy of a Data Science Thesis

A data science master's thesis follows a rigid, reproducibility-oriented structure that prioritizes experimental transparency over argumentation. The canonical European structure contains six to seven main chapters, each with a distinct purpose.

### 1.1 Introduction (3–5 pages, ~5–7% of the thesis)

Frames the research problem using a **Context → Problem → Strategy** arc. It must contain:

- A motivation paragraph establishing real-world relevance
- A precise problem statement identifying the gap in existing work
- **Explicitly numbered research questions** (e.g., RQ1: "Do GNNs outperform tabular methods for RTS game prediction?")
- A contributions statement (novel dataset, comparative framework, cross-domain analysis)
- A thesis outline describing each subsequent chapter

The [University of Helsinki data science thesis guide][helsinki] emphasizes that the introduction should be accessible to any peer in the program, even non-specialists.

### 1.2 Background and Literature Review (12–18 pages, ~20–25%)

Establishes the theoretical foundation and positions the thesis within existing research. Unlike a humanities literature review that engages philosophically with sources, an ML literature review is **functional** — it must explain the technical background readers need, survey competing approaches, and build a clear argument for why your specific study is needed. This chapter ends by identifying the gap your thesis fills.

### 1.3 Methodology (12–18 pages, ~20–25%)

The backbone of an ML thesis and the chapter most scrutinized by committees. It must describe:

- Problem formalization (mathematical definition of the learning task)
- Data sources and preprocessing pipeline
- Each model's architecture and rationale
- Training procedures and hyperparameter tuning strategy
- Evaluation protocol and baseline methods

**Every design decision requires justification** — not "we used XGBoost" but "we selected XGBoost because its gradient boosting framework handles heterogeneous tabular features effectively and has demonstrated strong performance on similar structured prediction tasks." The standard of detail is that **another student could reproduce your experiments from the description alone**.

### 1.4 Experiments and Results (12–18 pages, ~20–25%)

Presents findings systematically with comparison tables, performance curves, statistical tests, and ablation results. [FAU Erlangen-Nürnberg's thesis guidelines][fau] state firmly: each result and graph must be discussed — what's the reason for this peak or why have you observed this effect? Raw tables without interpretation are a common failure mode.

### 1.5 Discussion (5–8 pages)

Interprets results, explicitly answers each research question, compares findings with prior literature, analyzes failure cases, and addresses limitations and threats to validity. Some theses merge Results and Discussion — both approaches are acceptable, but the discussion content must exist somewhere.

### 1.6 Conclusion (2–3 pages)

Summarizes contributions, evaluates whether results are conclusive, and outlines future work directions briefly. [FAU][fau] recommends keeping this to roughly one page.

### Structural balance: the equal-thirds rule

An ML thesis follows **FAU's equal-thirds rule** — Background, Methods, and Results/Discussion should each comprise roughly one-third of the main body. A humanities thesis might dedicate 50%+ to literature engagement, while a technical thesis is weighted toward methodology and empirical results. Total length for a Polish master's thesis is typically **60–90 pages** excluding appendices, with [WSB University][wsb] specifying 70–90 pages and the [University of Warsaw][uw] citing approximately 80 standard pages.

---

## 2. Writing and Experimenting: An Iterative Loop, Not a Waterfall

The most common workflow mistake is treating thesis writing as a phase that happens after all experiments are complete. The recommended approach is **iterative co-development** of writing and experimentation, where each activity informs the other.

[Prof. Luigi Acerbi's Helsinki guide][helsinki] offers the critical principle: start writing before you start writing. Even before officially starting the writing period, write down what you do in a scrap LaTeX document — partial results, derivations, notes. If you already have bits and pieces written down, it will make your life much easier later. He recommends finishing at least one or two chapters early (Introduction and Background) and sharing them with the supervisor to catch structural problems before they propagate.

### 2.1 Recommended 6-month timeline

| Month | Experimentation | Writing |
|-------|----------------|---------|
| **1** | Literature survey, data pipeline setup, EDA | Preliminary literature review draft |
| **2** | Baseline implementation, initial experiments | Literature review refinement |
| **3** | Main method implementation (tabular ML, GNNs), pilot experiments | **Methods chapter draft** — writing methodology forces clarity in experimental design |
| **4** | Full experimental campaign incl. cross-domain experiments | Results chapter writing |
| **5** | Supplementary experiments, ablations | Discussion writing, full draft assembly, first revision cycle |
| **6** | Final reproducibility checks | Supervisor feedback integration, polishing, defense preparation |

For a 9–12 month project, stretch the experimental phase proportionally and allow **2–3 months** for revision.

### 2.2 Key workflow principles

- The **literature review should be drafted early** (months 1–3) because it directly informs experimental design, but **revised after experiments** to properly motivate findings and incorporate papers discovered during the research phase.
- **Core decisions** (research questions, primary methods, datasets, main evaluation metrics) should be locked by month 2–3. **Flexible details** (hyperparameter search ranges, additional ablation studies) can remain open until month 4–5.
- The [Helsinki guide][helsinki] warns that the writing phase alone takes at the very minimum a full month, probably more. Plan for experiments taking **2–3× longer** than your initial estimate.

---

## 3. Statistical Rigor: The Non-Negotiable Standards

The expectations for ML thesis evaluation methodology are well-defined in the academic literature, anchored by three authoritative sources: [Lones 2024][lones] in *Patterns* (Cell Press), [Heil et al. 2021][heil] in *Nature Methods*, and [Demšar 2006][demsar] in *JMLR*.

### 3.1 Reproducibility

[Heil et al.][heil]'s tiered framework defines three levels:

- **Bronze** (minimum): all data, trained models, and source code publicly available.
- **Silver** (expected by most committees): all dependencies installable via a single command (`requirements.txt` or `environment.yml`), **all random seeds explicitly set and reported**, hardware/software environments documented (GPU type, CUDA version, framework versions).
- **Gold**: full workflow automation from data download to final results via a Makefile or similar.

Sobering context: [Semmelrock et al. 2025][semmelrock] (*AI Magazine*) found that only one-third of ML researchers share data, and even fewer share source code — exceeding this low bar meaningfully strengthens a thesis.

### 3.2 Statistical testing for model comparison

A bigger accuracy number does not mean a better model — differences may reflect random variation. For your thesis comparing 3+ methods across 2 games, the statistical comparison framework has evolved significantly since [Demšar's 2006 landmark paper][demsar], and modern best practice incorporates corrections from subsequent research.

**The Friedman test** remains the correct omnibus test for comparing multiple classifiers across multiple datasets or evaluation conditions. It is nonparametric, does not assume normality of performance metrics, and tests whether all algorithms perform equally.

**The Nemenyi post-hoc test is no longer recommended.** [Benavoli, Corani & Mangili (2016)][benavoli-2016] demonstrated a fundamental flaw: the Nemenyi test suffers from **pool-dependence**, meaning the outcome of a comparison between classifiers A and B can change depending on which other classifiers are included in the experiment. This occurs because mean ranks are computed across all algorithms in the pool, so adding or removing an unrelated classifier C shifts the ranks assigned to A and B. [García & Herrera (2008)][garcia-herrera-2008] had earlier shown the Nemenyi test is excessively conservative compared to step-down alternatives.

**Current frequentist best practice** for pairwise comparisons is the **Wilcoxon signed-rank test** applied to each pair independently, with **Holm's step-down correction** for multiple comparisons. This avoids pool-dependence entirely because each pairwise test considers only the two classifiers involved. [García et al. (2010)][garcia-2010] provide experimental power analysis confirming this recommendation. Report **effect sizes alongside p-values** — a statistically significant but tiny improvement may lack practical meaning.

**Bayesian alternative (recommended for modern theses).** [Benavoli, Corani, Demšar & Zaffalon (2017)][benavoli-2017] — notably co-authored by Demšar himself — propose replacing frequentist NHST with **Bayesian classifier comparison**. Instead of a binary reject/fail-to-reject decision, the Bayesian signed-rank test outputs three probabilities: P(A better), P(practically equivalent), and P(B better). The **Region of Practical Equivalence (ROPE)** — typically ±1 percentage point for accuracy — defines a zone where differences are too small to matter, enabling the test to affirmatively declare practical equivalence (impossible with frequentist tests). The [`baycomp`][baycomp] Python library implements all four tests from the paper. This approach directly answers the question researchers actually care about: "What is the probability that my classifier is practically better?"

For a thesis comparing tabular ML vs. GNNs across two games, the recommended approach is:

1. **Friedman test** as omnibus check across all methods
2. **Pairwise Wilcoxon signed-rank tests with Holm correction** as the primary frequentist comparison
3. **Bayesian signed-rank test with ROPE** (via `baycomp`) as the complementary analysis — reporting three-way probabilities alongside traditional p-values demonstrates statistical sophistication
4. **Critical difference diagrams** for visualization, but computed from the Wilcoxon-based pairwise comparisons, not Nemenyi

### 3.3 Evaluation protocol

- Use k-fold cross-validation (typically 5 or 10 folds) with **mean ± standard deviation reported across folds**.
- Run models with multiple random seeds (minimum 5, ideally 10+).
- Maintain a truly held-out test set used **only once** for final evaluation.
- Report multiple complementary metrics: accuracy, F1, AUROC, log-loss, per-class metrics.
- Confidence intervals via bootstrap methods when analytical formulas are unavailable.

### 3.4 Data leakage: the most devastating methodological error

[Lones 2024][lones] and [Heil et al.][heil] identify common sources:

- Fitting scalers/normalizers on the entire dataset before splitting
- Performing feature selection using test labels
- Applying data augmentation before splitting
- Using future timestamps in training for time-series data

Use scikit-learn Pipelines to ensure preprocessing only uses training data.

---

## 4. Comparative Study Design: Fair Experiments Across Methods and Games

Your thesis faces the specific challenge of comparing multiple ML method families across two game domains. The academic standards for this type of work are exacting.

### 4.1 Fair comparison principles

All models must share:

- The same data splits
- The same preprocessing pipeline
- The same evaluation protocol
- Comparable hyperparameter tuning budgets

"Comparable" doesn't mean identical methods — grid search for a random forest and Bayesian optimization for a GNN are both acceptable — but each method should receive **equivalent computational effort** for optimization. [Lones 2024][lones] warns specifically: don't always believe results from community benchmarks — published numbers may have been obtained under different conditions.

### 4.2 Baselines must be meaningful

Always include simple baselines (majority-class classifier, logistic regression, random prediction) alongside established methods from the literature. A model that doesn't beat a simple baseline has limited value. **Ablation studies** are essential — systematically remove or replace elements (e.g., specific feature groups, graph structure, attention mechanisms) to demonstrate what drives performance.

### 4.3 Cross-domain generalization (SC2 → AoE2)

Frame this as a **transfer learning / domain generalization** problem. The two games represent distinct but related domains sharing abstract strategic concepts (resource gathering, unit production, combat). The research question becomes: do learned representations transfer across structurally different RTS games?

- Frame as zero-shot cross-domain evaluation
- Be transparent about **expected performance degradation** — negative results here are valuable and anticipated
- GNNs are particularly interesting for this angle because they can learn from structural relationships that may generalize better than raw tabular features

### 4.4 Results presentation for multi-method, multi-domain studies

- **Structured comparison tables**: performance metrics per method × per game, with mean ± std, bold for best results
- **Friedman test results** with CD diagrams
- **Performance-over-game-time curves**: prediction accuracy improving as the game progresses is the standard finding in RTS prediction literature — [Sánchez-Ruiz & Miranda][sanchez-ruiz] achieved >80% accuracy after game midpoint
- ROC curves per method
- **Cross-domain transfer matrix** showing performance degradation patterns

---

## 5. Literature Review: Three Research Streams, One Argument

For an interdisciplinary thesis, **thematic organization** is superior to chronological ordering. [Multiple university writing centers recommend this approach][thematic-review] for research with multiple facets requiring direct comparison of competing approaches.

### 5.1 Recommended thematic structure

1. **Esports analytics and game outcome prediction** — the broader field of computational game analysis, including StarCraft prediction work ([Sánchez-Ruiz & Miranda 2016][sanchez-ruiz], the [3D-ResNet paper in PLOS ONE 2022][plos-sc2]) and MOBA prediction parallels.
2. **Tabular machine learning for structured prediction** — XGBoost, random forests, LightGBM, and their strengths on structured data.
3. **Graph neural networks for relational data** — message passing networks, their theoretical advantages for structured/relational prediction.
4. **RTS games as ML domains** — StarCraft II ([SC2LE][sc2le], [AlphaStar][alphastar]) and AoE II specifics, available datasets, and prior prediction work.
5. **Cross-domain transfer and generalization** — theoretical foundations and practical approaches.

Within each theme, a brief chronological ordering can show field evolution (e.g., from logistic regression → CNN → GNN approaches for StarCraft).

### 5.2 Source count and quality

An interdisciplinary ML master's thesis should target **50–80 sources**, with the higher end appropriate given three distinct literature streams. The [Helsinki guide][helsinki] sets a floor: if your thesis cites fewer than ten articles, conference papers, or books, you could probably do a bit more of literature review. Prioritize peer-reviewed journal articles and top-tier conference papers (NeurIPS, ICML, AAAI for ML; IEEE CoG for game AI).

### 5.3 Gap identification

Your thesis addresses several identifiable gaps:

- Most win-prediction studies focus on a single game, with **very few comparing methods across multiple games**
- GNN application to real-time win prediction using game-state graphs is relatively underexplored
- Direct comparison of tabular versus graph-based approaches on the same game data is rarely done
- **Age of Empires II prediction literature is thin** — the field is heavily StarCraft-focused

Use the gap-statement structure: "While X has been studied extensively... and Y has shown promise in... there remains a lack of work that Z."

---

## 6. The Ten Mistakes That Sink ML Theses

Drawing from [Lones 2024][lones], [Lones (earlier) in *Patterns*][lones], and European thesis evaluation criteria, the most common failure modes cluster into three categories.

### 6.1 Methodological sins (most common cause of committee rejection)

1. **Data leakage** — fitting preprocessors on the full dataset, doing feature selection with test labels, or augmenting before splitting. ([Lones 2024][lones], [Heil et al.][heil])
2. **Accuracy as the sole metric** — a model predicting the majority class 95% of the time "achieves 95% accuracy" but is useless for imbalanced data. ([GeeksforGeeks ML mistakes][gfg-mistakes], [Capital One ML mistakes][capitalone-mistakes])
3. **Single split, no variance** — reporting results from one train/test split gives no indication of reliability.
4. **Overfitting to the test set** — repeated evaluation and tuning on the test set (sequential overfitting) invalidates all conclusions.
5. **Black-box treatment** — no feature importance analysis, no error analysis, no inspection of what the model learned.

### 6.2 Writing and presentation failures

6. **Results without interpretation** — tables of numbers with no discussion of what they mean, why one approach outperforms another, or what was learned. ([FAU guidelines][fau])
7. **Unjustified choices** — describing what was done without explaining why.
8. **Missing baselines and missing limitations** — claims not supported by statistical evidence.

The [Helsinki guide][helsinki] warns explicitly against AI-recognizable writing style — avoid "leverage," "innovative," "groundbreaking," and similar inflated language.

### 6.3 Structural imbalances

9. **Too much background, not enough analysis** — spending 30+ pages on literature review and 5 pages on actual contributions. The background should cover only what is needed for the thesis.
10. **Disconnected questions and conclusions** — the conclusion must connect back to the research questions stated in the introduction.

---

## 7. Appendices: Proving Rigor Without Cluttering the Narrative

The governing principle from [Dynamic Ecology's widely-cited guide][dynamic-ecology]: if removing the material would make your paper's argument harder to follow, it belongs in the main text. If it supports or documents your argument without being essential to reading it, move it to the appendix.

### 7.1 Main text placement

- Key results tables (best model performance across methods and games)
- Summary dataset statistics
- High-level preprocessing descriptions
- The 1–2 most important confusion matrices
- Final chosen hyperparameters
- Top feature importances
- Representative training curves

### 7.2 Appendix placement

- Full data dictionaries with feature types and ranges
- Complete hyperparameter search grids and results
- All confusion matrices across all models
- Supplementary experiments and ablation details
- Detailed step-by-step preprocessing pipeline
- Complete software environment specifications
- Per-class metrics for all configurations
- Extended mathematical derivations

### 7.3 Recommended appendix structure

| Appendix | Content |
|----------|---------|
| **A** | Complete Dataset Description / Data Dictionary |
| **B** | Detailed Preprocessing Steps |
| **C** | Full Hyperparameter Search Results |
| **D** | Additional Experimental Results |
| **E** | Code Listings or GitHub Repository Link |

Code belongs primarily in a **linked repository**, not in the thesis text. Main-text code should be limited to short pseudocode or critical algorithm snippets. Full implementation details go in the appendix or — preferably — a properly documented GitHub repository with a README covering installation, reproduction instructions, directory structure, and expected outputs. Version the repository with meaningful commits throughout the project, and consider archiving to [Zenodo](https://zenodo.org/) for permanent scholarly access. See [SFU Library's thesis appendix guide][sfu-appendix] and [PhD Assistance's code formatting guide][phd-code] for additional formatting conventions.

---

## 8. GenAI Transparency and Attribution

Since this thesis uses AI tools (Claude Code, Claude Chat) extensively for code development,
data exploration, and manuscript review, transparent disclosure is both an ethical requirement
and a methodological strength. The academic consensus as of 2025–2026 is clear: AI tool usage
is permitted and increasingly expected, but must be disclosed with specificity.

### 8.1 What to disclose and where

**Methodology chapter** — disclose AI usage when it served as a research tool: coding assistance,
data pipeline development, statistical computation, literature screening, or data analysis.
Specify the tool name and version (e.g., "Claude Opus 4, Anthropic, via Claude Code CLI"),
the specific tasks it performed, the extent of its contribution, and the verification procedures
applied to its outputs. This follows the [KU Leuven framework][kuleuven-genai], which treats
AI disclosure as analogous to reporting software like SPSS — routine methodological reporting,
not confession.

**Acknowledgments section** — disclose AI usage for writing assistance: language editing, grammar
improvement, brainstorming, or structural suggestions. Basic spelling/grammar checkers are
universally exempt from disclosure.

### 8.2 Citation formats

[APA 7th edition][apa-chatgpt] treats AI-generated content as software output. When a shareable
URL exists, cite the specific conversation. When it does not, cite the tool generically with
version and date. AI tools cannot be listed as co-authors — this is universally agreed across
all major publishers ([Elsevier][elsevier-ai], Springer Nature, IEEE, ACM, Nature, Science).

### 8.3 Polish university context

Polish universities have adopted structured but institution-specific policies. The
[University of Warsaw guidelines][uw-ai-guidelines] require AI use to be agreed upon with the
thesis supervisor and documented in the introduction or methodology chapter. The Uniform
Anti-Plagiarism System (JSA), mandatory for all Polish universities since February 2024,
includes an AI content detection module. **Check PJAIT's specific policy** with your supervisor
— institutional guidelines may impose additional constraints or require a specific declaration
format.

### 8.4 Practical recommendation for this thesis

Include a subsection in the Methodology chapter titled "Use of AI-Assisted Tools" that states:
(1) which tools were used (Claude Code, Claude Chat, with model versions),
(2) for what purposes (code generation, data exploration pipeline development, literature
review assistance, manuscript drafting review),
(3) how outputs were verified (code review, unit testing, manual validation of statistical
results, cross-referencing of cited sources),
(4) a responsibility statement confirming all intellectual contributions, experimental design
decisions, and scientific conclusions are the author's own.

---

## 9. What Separates an Excellent Thesis from a Passing One

The evidence from European evaluation criteria converges on a clear hierarchy. An excellent thesis has:

- A clear, well-scoped research question
- A literature review that **critically positions** the contribution rather than summarizing papers
- A methodology chapter where every choice is justified and reproducible
- Results that are **statistically validated** with appropriate tests (Friedman + Wilcoxon/Holm for multi-method comparison, with Bayesian signed-rank as complement)
- Honest discussion of limitations
- Writing that is concise, precise, and narratively coherent

For your specific topic — comparing prediction methods across StarCraft II and Age of Empires II — the thesis has natural strengths to leverage:

- The **cross-game comparative angle** is genuinely novel (most work focuses on a single game)
- The **AoE II prediction literature is thin**, creating a clear contribution
- The **tabular-versus-GNN comparison** addresses a live methodological debate in ML

Frame these advantages clearly in the introduction, build the literature review to demonstrate these gaps exist, execute the experiments with statistical discipline, and discuss the results with intellectual honesty about what worked, what didn't, and why. That combination — novelty, rigor, and honesty — is what evaluators consistently reward with top marks.

---

## References

<!-- University thesis guidelines -->
[helsinki]: https://www.helsinki.fi/en/researchgroups/machine-and-human-intelligence/luigis-guide-to-writing-masters-theses-in-data-science "Luigi Acerbi — Guide to writing Master's theses in Data Science (University of Helsinki)"
[fau]: https://www.cs7.tf.fau.eu/teaching/student-theses/writing-your-thesis/ "Writing Your Thesis — FAU Erlangen-Nürnberg, Computer Science 7"
[wsb]: https://wsb.edu.pl/files/pages/3221/rules_for_writing_diploma_theses.pdf "Rules for Writing Diploma Theses — WSB University (Poland)"
[uw]: https://www.wne.uw.edu.pl/en/students/diploma-thesis/guidelines-regarding-thesis "Guidelines Regarding Thesis — University of Warsaw, Faculty of Economic Sciences"

<!-- ML methodology and reproducibility -->
[lones]: https://pmc.ncbi.nlm.nih.gov/articles/PMC11573893/ "Lones (2024) — Avoiding common machine learning pitfalls. Patterns (Cell Press) / PMC"
[heil]: https://pmc.ncbi.nlm.nih.gov/articles/PMC9131851/ "Heil et al. (2021) — Reproducibility standards for machine learning in the life sciences. Nature Methods"
[demsar]: https://jmlr.org/papers/v7/demsar06a.html "Demšar (2006) — Statistical Comparisons of Classifiers over Multiple Data Sets. JMLR 7:1–30"
[semmelrock]: https://onlinelibrary.wiley.com/doi/10.1002/aaai.70002 "Semmelrock et al. (2025) — Reproducibility in ML-based research: Overview, barriers, and drivers. AI Magazine"
[raschka]: https://sebastianraschka.com/blog/2018/model-evaluation-selection-part4.html "Raschka (2018) — Model evaluation, model selection, and algorithm selection in ML"

<!-- Esports / RTS prediction literature -->
[sanchez-ruiz]: https://files.gitter.im/Reithan/PACAnalyzer/PPF2/A-machine-learning-approach-to-predict-the-winner-in-StarCraft-based-on-influence-maps.pdf "Sánchez-Ruiz & Miranda — A machine learning approach to predict the winner in StarCraft based on influence maps"
[plos-sc2]: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0264550 "3-Dimensional CNNs for predicting StarCraft II results and extracting key game situations. PLOS ONE (2022)"
[sc2le]: https://arxiv.org/abs/1708.04782 "Vinyals et al. (2017) — StarCraft II: A New Challenge for Reinforcement Learning. arXiv:1708.04782"
[alphastar]: https://www.nature.com/articles/s41586-019-1724-z "Vinyals et al. (2019) — Grandmaster level in StarCraft II using multi-agent reinforcement learning. Nature"

<!-- Writing and structure guides -->
[thematic-review]: https://www.cwauthors.com/article/how-to-structure-and-write-a-thematic-literature-review "How to write a Thematic Literature Review — CW Authors"
[dynamic-ecology]: https://dynamicecology.wordpress.com/2014/09/24/what-belongs-in-the-appendices-vs-the-main-text-in-scientific-papers/ "What belongs in the appendices vs. the main text in scientific papers? — Dynamic Ecology"
[sfu-appendix]: https://www.lib.sfu.ca/help/publish/thesis/format/appendices "Formatting your thesis: Appendices & supplemental material — SFU Library"
[phd-code]: https://www.phdassistance.com/how-do-you-present-computer-code-in-a-thesis/ "How to Format Programming Codes in a Thesis — PhD Assistance"

<!-- Common ML mistakes -->
[gfg-mistakes]: https://www.geeksforgeeks.org/blogs/common-machine-learning-mistakes/ "Top 10 Common Machine Learning Mistakes and How to Avoid Them — GeeksforGeeks"
[capitalone-mistakes]: https://www.capitalone.com/tech/machine-learning/10-common-machine-learning-mistakes/ "10 Common Machine Learning Mistakes and How to Avoid Them — Capital One"

<!-- Thesis timeline -->
[pressbooks-timeline]: https://ecampusontario.pressbooks.pub/craftingresearchnarratives/front-matter/the-thesis-timeline/ "The Thesis Timeline — Crafting Research Narratives (eCampusOntario Pressbooks)"

<!-- Statistical testing evolution (Nemenyi → Wilcoxon → Bayesian) -->
[benavoli-2016]: https://jmlr.org/papers/v17/benavoli16a.html "Benavoli, Corani & Mangili (2016) — Should We Really Use Post-Hoc Tests Based on Mean-Ranks? JMLR, 17(5):1–10"
[benavoli-2017]: https://www.jmlr.org/papers/volume18/16-305/16-305.pdf "Benavoli, Corani, Demšar & Zaffalon (2017) — Time for a Change: a Tutorial for Comparing Multiple Classifiers Through Bayesian Analysis. JMLR, 18(77):1–36"
[garcia-herrera-2008]: https://jmlr.org/papers/v9/garcia08a.html "García & Herrera (2008) — An Extension on 'Statistical Comparisons of Classifiers over Multiple Data Sets' for all Pairwise Comparisons. JMLR, 9:2677–2694"
[garcia-2010]: http://dl.acm.org/citation.cfm?id=1750831 "García, Fernández, Luengo & Herrera (2010) — Advanced Nonparametric Tests for Multiple Comparisons. Information Sciences, 180(10):2044–2064"
[baycomp]: https://github.com/janezd/baycomp "baycomp — Bayesian comparison of classifiers (Python library by Janez Demšar)"
[corani-2017]: https://link.springer.com/article/10.1007/s10994-017-5641-9 "Corani, Benavoli, Demšar, Mangili & Zaffalon (2017) — Statistical Comparison of Classifiers Through Bayesian Hierarchical Modelling. Machine Learning, 106:1817–1837"

<!-- GenAI transparency and attribution -->
[kuleuven-genai]: https://www.kuleuven.be/english/genai/transparency-about-the-use-of-genai "How to be transparent about the use of GenAI — KU Leuven"
[apa-chatgpt]: https://apastyle.apa.org/blog/how-to-cite-chatgpt "How to cite ChatGPT — APA Style (updated September 2025)"
[elsevier-ai]: https://www.elsevier.com/about/policies-and-standards/the-use-of-generative-ai-and-ai-assisted-technologies-in-writing-for-elsevier "The use of AI and AI-assisted technologies in writing for Elsevier"
[uw-ai-guidelines]: https://www.uw.edu.pl/wytyczne-urk-dotyczace-sztucznej-inteligencji-w-procesie-ksztalcenia/ "Wytyczne URK dotyczące sztucznej inteligencji w procesie kształcenia — Uniwersytet Warszawski"