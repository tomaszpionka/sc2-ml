# From Raw Data to Clean Data: A Methodological Guide for Pre-Modeling ML Phases

> **The quality of a machine learning model is bounded by the quality of the analyst's understanding of the data.**

For a supervised binary classification task on observational game data with temporal structure and player-level panel properties, the pre-feature-engineering phases — acquisition, profiling, EDA, and cleaning — are not mere bookkeeping. They form the epistemic foundation on which every downstream decision rests. Getting these phases right means the difference between a model that generalizes and one that memorizes artifacts of data collection. This guide synthesizes academic standards, established frameworks, and practitioner wisdom into a structured methodology for these critical early phases.

The intellectual lineage here runs through [Tukey's 1977 *Exploratory Data Analysis*][tukey-eda-wiki], [Gebru et al.'s *Datasheets for Datasets*][gebru-datasheets] (2021), [Gelman's Bayesian reformulation of EDA][gelman-eda-2004], the [CRISP-DM process model][crisp-dm], and recent work on [dataset shift][data-distribution-debugging] and [sports analytics methodology][davis-sports-2024]. What unites them is a single conviction: **you cannot responsibly model what you do not understand**.

### Where this manual sits in the full experiment lifecycle

This document covers phases 1–4 below. Subsequent manuals will address phases 5 onward.

1. **Data Acquisition & Source Inventory** ← this manual
2. **Data Profiling** ← this manual
3. **Exploratory Data Analysis (EDA)** ← this manual
4. **Data Cleaning & Validation** ← this manual
5. Feature Engineering
6. Train/Validation/Test Splitting
7. Baseline Establishment
8. Model Training & Hyperparameter Tuning
9. Evaluation & Statistical Comparison
10. Error Analysis & Ablation Studies
11. Cross-Domain Transfer Experiments
12. Results Synthesis & Thesis Integration

---

## 1. Data Acquisition Begins with a Source Inventory, Not a DataFrame

Before writing a single line of analysis code, a rigorous project documents every data source in a structured inventory. This practice, formalized in [Gebru et al.'s *Datasheets for Datasets*][gebru-datasheets] (Communications of the ACM, 2021), asks **57 questions across seven categories**: Motivation, Composition, Collection Process, Preprocessing/Cleaning/Labeling, Uses, Distribution, and Maintenance. The framework draws an analogy to electronics datasheets — every component ships with documentation; every dataset should too.

For each data source in your game data project, the inventory should record: **collection method** (API pull, database export, web scrape), **temporal coverage** (exact date range, granularity), **sampling mechanism** (census vs. sample, any filtering applied upstream), **known biases** (selection effects, survivorship, measurement error), **schema information** (column names, types, constraints, relationships), **update frequency and freshness**, and **licensing or access restrictions**. [Google's *Data Cards* framework][data-cards] (Pushkarna et al., FAccT 2022) extends this with a participatory process organized around the **OFTEn framework** — Origins, Factuals, Transformations, Experience, and n=1 samples — designed to surface institutional knowledge that technical documentation misses.

Schema discovery should combine automated type inference (tools like [TensorFlow Data Validation][tfdv] infer Protocol Buffer schemas automatically) with manual semantic validation. A column typed as `float64` might actually represent a categorical ID that was never cast properly. Pattern analysis using regex can detect semantic types — emails, timestamps, encoded categoricals — that automated tools miss. Functional dependency discovery reveals implicit schema relationships (e.g., `map_id` → `map_name`) that matter for deduplication and consistency checks.

**Provenance tracking** — recording every transformation from raw source to analysis-ready data — is essential for reproducibility. The [W3C PROV standard][provenance-tracking] provides a formal ontology. Practically, tools like DVC (Data Version Control) version data files alongside code, while MLflow logs parameters, metrics, and artifacts for experiment tracking. The key principle: **raw data is sacred and must be preserved alongside any cleaned or transformed derivatives**.

---

## 2. Tukey's EDA Philosophy: Detective Work, Not Box-Ticking

[John Tukey's 1977 book][tukey-eda-wiki] opened with: *"Exploratory data analysis is detective work — numerical detective work or counting detective work — or graphical detective work."* His core insight was that statistics had become excessively confirmatory — focused on testing pre-specified hypotheses — at the expense of actually looking at data. As [Nightingale's retrospective][nightingale-eda] documents, Tukey's EDA is **an attitude, not a set of techniques**, characterized by four principles: emphasis on graphical display, emphasis on successively better fits by examining residuals, use of robust statistics (medians and quartiles over means and standard deviations), and deliberate avoidance of premature probability models.

The modern operationalization of Tukey's philosophy, best articulated in [Wickham's *R for Data Science*][wickham-eda], treats EDA as an **iterative cycle**: generate questions, search for answers through visualization and transformation, then use findings to refine questions or generate new ones. Wickham identifies two foundational questions that always apply: *"What type of variation occurs within my variables?"* and *"What type of covariation occurs between my variables?"* This maps directly to the standard phasing of univariate → bivariate → multivariate analysis.

### 2.1 The three EDA layers

**Univariate analysis** answers: What is each variable's distribution? What are its central tendency, spread, modality, and outliers? Tools include histograms, boxplots, QQ plots, and descriptive statistics. **Bivariate analysis** asks: How do pairs of variables relate? What associations exist? Tools include scatterplots, correlation coefficients (Pearson for linear, Spearman for monotonic), cross-tabulations, and conditional boxplots. **Multivariate analysis** explores complex interactions and latent structure through heatmaps, pair plots, PCA, and dimensionality reduction. Each phase builds on the previous — univariate findings (e.g., a bimodal distribution in a feature) generate hypotheses that bivariate analysis can investigate (e.g., does the bimodality correspond to two player segments?).

The [Georgia Tech OMSCS ML guide][gatech-eda] provides a practical EDA structure for ML coursework, recommending that analysts begin with descriptive statistics, proceed to univariate distributions with histograms and boxplots, then examine pairwise relationships with scatterplots and correlation heatmaps, and finally perform multivariate analysis using pair plots or dimensionality reduction. [CMU's statistical methods chapter on EDA][cmu-eda] adds formal checks: probability plots (QQ plots) for distributional assessment, lag plots for serial correlation, and run-sequence plots for detecting shifts and trends.

### 2.2 EDA as hypothesis generation, not confirmation

[Andrew Gelman's work][gelman-eda-2004] bridges Tukey's exploratory philosophy with formal statistical modeling. In "Exploratory Data Analysis for Complex Models" (*Journal of Computational and Graphical Statistics*, 2004), Gelman argues that EDA and confirmatory analysis are two aspects of the same thing — both compare observed data to what would be expected under a model. His Bayesian posterior predictive checks create formal reference distributions for EDA graphs, giving Tukey's visual approach a rigorous inferential foundation. Critically, [Gelman and Loken's "Garden of Forking Paths"][gelman-forking-paths] (2013) warns that **exploratory findings are inherently fragile**: there can be a large number of potential comparisons when the details of data analysis are highly contingent on data, even without conscious p-hacking. The [FORRT glossary entry][forrt-forking] provides an accessible summary of this concept and its implications for research transparency.

---

## 3. Systematic Data Profiling: The Automated and the Human

[Data profiling][data-profiling-wiki] operates at two levels: **column-level** and **dataset-level**.

### 3.1 Column-level profiling

For every variable, compute: null/missing count and percentage, zero count, cardinality (distinct values), uniqueness ratio, descriptive statistics (min, max, mean, median, standard deviation, percentiles), distribution shape (skewness, kurtosis), outlier detection (IQR fences, z-scores), pattern/format frequency for strings, and top-k frequent values.

### 3.2 Dataset-level profiling

Assess: total row count, duplicate row count and percentage, temporal coverage (date range, gaps), class balance of the target variable, a feature completeness matrix (heatmap of missingness across all columns), correlation matrices, and memory footprint.

### 3.3 Critical detection tasks

Three specific detection tasks deserve emphasis. **Dead fields** are columns that are 100% null — they carry zero information and should be flagged immediately. **Constant columns** contain a single unique value across all rows and are equally uninformative for classification. **Near-constant columns** (e.g., 99.9% one value) may appear informative but typically contribute noise; the threshold for flagging depends on context but a uniqueness ratio below 0.001 is a reasonable starting point.

### 3.4 Distribution analysis methods

Distribution analysis should combine multiple visual methods. **Histograms** provide quick shape assessment but are sensitive to bin width. **Kernel density estimation (KDE)** offers smooth probability density approximations better suited for comparing distributions. **QQ plots** are the gold standard for assessing distributional fit — Tukey championed them specifically because points falling on the diagonal indicate conformance to the reference distribution, while systematic departures reveal the nature of deviation (heavy tails curve upward, light tails curve downward). **Empirical CDFs** enable formal two-sample comparison via the Kolmogorov-Smirnov test. The [NCBI EDA chapter][ncbi-eda] and [CMU's EDA chapter][cmu-eda] both provide worked examples of applying these methods systematically.

### 3.5 The profiling toolkit

The modern profiling toolkit includes several powerful libraries:

- **[ydata-profiling][ydata-profiling]** (formerly pandas-profiling) generates comprehensive HTML reports from a single line of code, covering type inference, univariate analysis, correlations (Pearson, Spearman, Kendall, Phi-K, Cramér's V), missing value analysis, and duplicate detection. It automatically flags high correlation, missing values, constant columns, zeros, and skewness. Its limitation is performance on large datasets (mitigated via sampling or `minimal=True` mode) and its single-table focus.

- **[Great Expectations][great-expectations]** is less an EDA tool than a **data validation framework** — it defines declarative "expectations" (e.g., `expect_column_values_to_not_be_null`, `expect_column_values_to_be_between`) and validates data against them, producing pass/fail results with auto-generated documentation. It excels at codifying profiling insights into persistent, testable assertions.

- **[whylogs][whylogs]** (WhyLabs) creates lightweight statistical profiles in a single pass, designed for production monitoring. Profiles are mergeable across partitions and time windows, making it ideal for tracking distribution drift. It uses Apache DataSketches for approximate cardinality and distribution estimation.

- **[TensorFlow Data Validation (TFDV)][tfdv]** infers schemas as Protocol Buffers, detects anomalies (unexpected types, out-of-domain values, missing features), and supports skew/drift detection between training and serving data. It scales via Apache Beam. The [TFDV ACM paper][tfdv-acm] describes its architecture for production-scale validation.

- **[Amazon Deequ][deequ]** provides Spark-based "unit tests for data" with metrics computation, constraint verification, and constraint suggestion.

However, [Gebru et al.][gebru-datasheets] explicitly warn that **automated documentation runs counter to the goal of encouraging careful reflection**. Automated profilers confirm data types and distributions but cannot verify semantic correctness (a perfectly formatted date that's wrong), cannot supply business context (an "anomalous" spike might be a holiday), and miss cross-table inconsistencies. The profiling report is a starting point for human investigation, not a certificate of data quality.

---

## 4. Data Cleaning as a Documented, Non-Destructive, Auditable Process

[CRISP-DM's Data Preparation phase][crisp-dm] (Phase 3) specifies that cleaning should produce a **data-cleaning report** documenting in excruciating detail every decision and action used to clean the data. This report should reference every data quality problem identified during profiling and explain the resolution. Practitioners estimate that **50–80% of project effort** falls in this phase.

### 4.1 The cleaning registry

A **cleaning registry** (or data quality log) formalizes this by recording each rule with five fields:

| Field | Description |
|-------|-------------|
| **Rule ID** | Unique identifier for traceability (e.g., `R01`, `R02`) |
| **Condition** | What triggers it (e.g., `player_count != 2`) |
| **Action** | Flag, impute, remove, or correct |
| **Justification** | Domain rationale, referencing a specific profiling/EDA finding |
| **Impact** | Number and percentage of records affected, with subgroup breakdown |

This structure enables sensitivity analysis — you can quantify exactly how each cleaning decision changes the dataset — and supports audit trails for reproducibility.

### 4.2 Non-destructive cleaning

**Non-destructive cleaning** is the preferred approach. Instead of deleting rows, mark them with exclusion flags or datetime-valued soft-delete columns. Create cleaned views that filter flagged records, leaving original data intact. Add binary indicator columns (`is_missing_X`, `is_outlier_X`) that preserve missingness information — models can learn from the pattern of absence itself. The rationale is threefold: deletion is irreversible, flagging enables sensitivity analysis on cleaning decisions, and preserved raw data supports re-evaluation when domain understanding changes.

### 4.3 Measuring cleaning impact

Measuring cleaning impact requires tracking counts at each stage, ideally visualized as a **CONSORT-style flow diagram** — borrowed from clinical trial reporting ([Consolidated Standards of Reporting Trials][consort-ai]). The **CONSORT-AI Extension** (Liu et al., 2020) adds input-data-level criteria specifically for AI studies. Critically, cleaning impact must be assessed **across subgroups**: does a cleaning rule disproportionately remove records from specific player segments, time periods, or outcome classes? The [mlinspect library][mlinspect] (Schelter et al., VLDB Journal) extracts DAG representations of preprocessing pipelines and uses annotation propagation to detect exactly these "data distribution bugs." [Jeanselme et al.][jeanselme-flow] (2024, *Journal of Biomedical Informatics*) advocate adding demographic breakdowns to flow diagrams to identify potential algorithmic biases before deployment.

### 4.4 Post-cleaning validation

After cleaning, **re-validate all data invariants**. Re-run profiling to compare before/after statistics (null rates, cardinality, distributions). Verify that relationships between variables still hold. Check that cleaning hasn't introduced new issues (e.g., imputation creating impossible value combinations). [Great Expectations][great-expectations] is particularly well-suited here: codify pre-cleaning invariants as expectation suites and re-run them post-cleaning.

### 4.5 Missing data handling

For missing data handling, the decision framework follows [Rubin's 1976 classification][rubin-missing]:

- **MCAR** (Missing Completely At Random) — missingness is independent of all data; listwise deletion is safe if the proportion is small (<5%), and simple imputation is acceptable.
- **MAR** (Missing At Random) — missingness depends on observed data; multiple imputation (MICE) or KNN imputation is appropriate, while listwise deletion [introduces bias][missing-data-bias].
- **MNAR** (Missing Not At Random) — missingness depends on the missing value itself; no standard imputation fully corrects this, requiring selection models, sensitivity analysis, or explicit missingness modeling.

Detection relies on [Little's MCAR test][mcar-mar-mnar] and comparing characteristics between missing and non-missing groups. In game data, MNAR is common: players who perform poorly may have missing post-match data precisely because they disconnected or rage-quit.

### 4.6 Reporting standards

The **[reforms checklist][reforms]** (Kapoor et al., arXiv 2308.07832) provides an 8-module reporting standard for ML-based science, with dedicated modules for Data Quality and Data Preprocessing. Gundersen and Kjensmo found that **none of 400 papers at leading ML conferences satisfied all reproducibility criteria**, with papers only meeting 20–30% of criteria — underscoring how frequently cleaning and preprocessing documentation is neglected.

---

## 5. Temporal and Panel Structure Demand Specialized EDA

Game data with player-level repeated observations is **panel data** (also called longitudinal data) — combining cross-sectional variation across players with time-series variation within each player. This dual structure creates analytical requirements that standard EDA checklists miss entirely.

### 5.1 Stationarity assessment

If the statistical properties of features or the target variable change over time, a model trained on historical data may fail on future data. The Augmented Dickey-Fuller (ADF) test (null hypothesis: non-stationarity, reject at p ≤ 0.05) and KPSS test (null hypothesis: stationarity) should be used complementarily — if ADF rejects and KPSS does not, there is strong evidence of stationarity. Visual inspection via ACF plots supplements formal testing: slowly decaying autocorrelation indicates non-stationarity. In game data, non-stationarity is often **engineered by design** through patches that change game mechanics, character balance, and item properties.

### 5.2 Concept drift

[Chitayat et al. (2023)][chitayat-esports] document that esports titles change so rapidly that analytics models can have a short life-span — a problem largely ignored in the literature. The meta (most effective tactics available) shifts with each patch, causing sudden changes in the relationship between features and outcomes. [Davis et al. (2024)][davis-sports-2024] — the most comprehensive recent paper on sports analytics methodology — identify that sports/game data present **nested dependencies** (matches within seasons, players within teams, games within patches) that if not properly addressed can lead to overly optimistic performance estimates. They emphasize that non-stationarity is inherent in competitive contexts.

Detection methods include:

- **Population Stability Index (PSI)**: Compares binned feature distributions between reference and current periods. PSI < 0.1 indicates no significant shift; 0.1–0.2 is moderate; ≥ 0.2 requires model review.
- **Kolmogorov-Smirnov test**: Non-parametric comparison of continuous distributions across time windows.
- **Wasserstein distance**: Measures the "cost" of transforming one distribution into another, with greater sensitivity to tail differences.
- **Visual methods**: Feature distribution overlays by time period, time-indexed boxplots, and target rate (win rate) plotted over time.

### 5.3 Panel data variance decomposition

Decomposing total variance into **between-player** (differences in player averages) and **within-player** (a single player's variation over time) components reveals what the data can actually teach a model. If most variation is between-player, the model is essentially profiling player types. If within-player variation dominates, temporal dynamics matter more. In Python, this is straightforward with grouped operations on DataFrames.

### 5.4 Survivorship bias

**Survivorship bias** is the single most dangerous threat to validity in game panel data. If players who lose frequently stop playing, the dataset overrepresents improving or winning players, biasing win-rate estimates upward and making classification models appear more accurate than they are. [Czeisler et al. (2021)][survivorship-bias] demonstrated that restricting to "survivors" in longitudinal surveys led to systematically overly optimistic conclusions. Detection requires: comparing baseline characteristics of active vs. churned players, testing whether dropout correlates with the outcome variable, and analyzing attrition patterns over time. The [STRATOS Initiative's IDA checklist][stratos-ida] for longitudinal studies (Lusa et al., 2024, *PLOS ONE*) formalizes five screening explorations: participation profiles, missing data evaluation, univariate descriptions stratified by time, multivariate descriptions, and longitudinal-specific aspects.

### 5.5 Temporal leakage audit

**Temporal leakage** must be audited during EDA, not discovered after modeling. Common causes include: features computed from future data (a player's career average that includes post-prediction games), normalization fitted on the entire dataset before splitting, and features that wouldn't be available at actual prediction time. The audit is simple in principle: for every feature, ask *"Could this value be computed from information available strictly before the prediction timestamp?"* A large discrepancy between random-split and temporal-split model performance is a strong signal of leakage.

---

## 6. Decision Gates: Knowing When You Know Enough

The concept of **epistemic readiness** — knowing enough about the data to make informed downstream decisions — lacks a formal definition in the literature but is operationalized across several frameworks.

### 6.1 Required deliverables before modeling

The [Georgia Tech OMSCS framework][gatech-eda] specifies four deliverables that must exist before proceeding to modeling:

1. **Data dictionary** — each column's meaning, units, valid ranges, and assumptions
2. **Data quality report** — missingness, duplicates, outliers, parsing issues, cleaning actions taken
3. **Risk register** — leakage risk, confounds, target ambiguity
4. **Modeling readiness decision** — explicit go/no-go with justification

### 6.2 Quality gates

[CRISP-ML(Q)][crisp-mlq] extends CRISP-DM with **quality gates** at each phase transition. Quality assurance requirements and constraints are defined before each phase; reaching and satisfying criteria is necessary to advance. For the data-understanding-to-data-preparation transition, this means documented data quality assessment and verified fitness for purpose. For data-preparation-to-modeling, it means a clean dataset with documented exclusions, validated invariants, and confirmed absence of leakage.

### 6.3 Warning signs that exploration was insufficient

Warning signs include: models producing suspiciously perfect results (leakage), dramatic performance degradation on new data (undetected distribution shifts), inability to explain what features mean (missing data dictionary), ad-hoc undocumented cleaning decisions, analysis conducted only at aggregate level ([Simpson's Paradox][simpsons-paradox] risk), and no formalized outlier or missing-data policy.

A practical heuristic: **if you cannot write a one-page summary of your data's key properties, quirks, and risks from memory, EDA is not complete**.

---

## 7. Seven Pitfalls That Undermine Exploratory Analysis

**Confirmation bias** is the most insidious threat: the tendency to gravitate toward patterns matching expectations while ignoring anomalies. The mitigation is deliberate: actively seek disconfirming evidence, and treat every "obvious" pattern with the same skepticism as a surprising one.

**Cherry-picking visualizations** — selecting only plots that support a narrative — is its visual manifestation. The remedy is documenting all visualizations attempted, not just compelling ones, and reporting distributions and relationships comprehensively rather than selectively.

**Over-aggregation** is particularly dangerous for game data. [Simpson's Paradox][simpsons-paradox] demonstrates that trends in aggregated data can reverse entirely when stratified by subgroups. The canonical example: UC Berkeley admissions appeared to show gender bias in aggregate, but stratifying by department revealed women applied to more competitive programs. In game data, a feature might correlate positively with winning overall but negatively within specific matchups, rank tiers, or patches. **Always analyze at multiple levels of aggregation.**

**Treating EDA as box-ticking** rather than genuine discovery turns a creative investigative process into bureaucratic compliance. [Wickham's][wickham-eda] reminder: EDA is fundamentally a creative process — the key to asking quality questions is to generate a large quantity of questions. Anscombe's Quartet (1973) — four datasets with identical summary statistics but dramatically different visual patterns — permanently demonstrates why mechanical statistic computation without visualization is insufficient.

**Ignoring the exploratory-confirmatory boundary** leads to the [Garden of Forking Paths][gelman-forking-paths]. Every pattern discovered during EDA is a hypothesis, not a confirmed result. Treating exploratory findings as established facts — especially when the same data will be used for model evaluation — inflates confidence and undermines statistical validity.

**Not checking assumptions** before applying statistical methods invalidates downstream conclusions. The [NIST/SEMATECH Engineering Statistics Handbook][nist-handbook] notes that classical tests depend on underlying assumptions (e.g., normality), and hence the validity of test conclusions depends on the validity of those assumptions. EDA's purpose includes verifying these assumptions.

**Failing to document decisions** makes EDA unreproducible. Without records of what was examined, what was found, and what was decided, the analytical chain from raw data to model input is opaque — to collaborators, reviewers, and future-you.

**Not documenting AI-assisted exploration** is an emerging eighth pitfall. If AI tools
(Claude, ChatGPT, Copilot) are used during EDA — for generating visualization code, suggesting
statistical tests, identifying patterns, or writing SQL queries — this must be documented in
the EDA notebook or report. The [KU Leuven GenAI framework][kuleuven-genai] treats AI tool
usage as analogous to reporting any other software instrument: state what tool was used, for
what task, and how outputs were verified. Undisclosed AI assistance during exploration creates
an unreproducible analytical chain — another researcher cannot retrace your reasoning if they
don't know which steps involved AI-generated code or AI-suggested hypotheses.

---

## 8. Conclusion: The Phases Before Modeling Are the Model's Foundation

The methodology outlined here is not bureaucratic overhead — it is the infrastructure that determines whether an ML model produces genuine insight or structured noise. Three principles tie these phases together.

First, **documentation is not optional**. [Gebru et al.'s Datasheets][gebru-datasheets], cleaning registries with rule-level traceability, CONSORT-style flow diagrams, and EDA notebooks are not academic luxuries. They are the mechanisms by which analytical decisions become auditable, reproducible, and improvable. The [reforms checklist's][reforms] finding that zero out of 400 ML papers met all reproducibility criteria is a measure of how far the field falls short.

Second, **temporal structure is not a nuisance to handle — it is the central analytical constraint**. For game data with panel properties, random splits are invalid, concept drift is engineered by design through patches, survivorship bias systematically distorts the sample, and every feature must pass a temporal availability audit. These are not edge cases; they are the defining characteristics of the data.

Third, **EDA is a stance of genuine curiosity, not compliance**. [Tukey's][tukey-eda-wiki] deepest insight was not any specific technique but the conviction that data should be interrogated before being modeled. The modern adaptation of this insight — formalized through structured checklists, [decision gates][crisp-mlq], and quality assurance frameworks — preserves the spirit of open-ended investigation while providing the rigor that production ML demands. The goal is not to complete a checklist but to achieve epistemic readiness: the analyst's confident understanding that they know the data well enough to make every downstream decision responsibly.

---

## References

<!-- Foundational EDA methodology -->
[tukey-eda-wiki]: https://en.wikipedia.org/wiki/Exploratory_data_analysis "Exploratory Data Analysis — Wikipedia (overview of Tukey's 1977 methodology)"
[nightingale-eda]: https://nightingaledvs.com/remembrances-of-things-eda/ "Remembrances of Things EDA — Nightingale (Data Visualization Society)"
[wickham-eda]: https://r4ds.had.co.nz/exploratory-data-analysis.html "Wickham & Grolemund — Exploratory Data Analysis, Chapter 7 of R for Data Science"
[gelman-eda-2004]: https://www.tandfonline.com/doi/abs/10.1198/106186004X11435 "Gelman (2004) — Exploratory Data Analysis for Complex Models. Journal of Computational and Graphical Statistics, 13(4)"
[gelman-forking-paths]: https://sites.stat.columbia.edu/gelman/research/unpublished/p_hacking.pdf "Gelman & Loken (2013) — The Garden of Forking Paths. Columbia University"
[forrt-forking]: https://forrt.org/glossary/english/garden_of_forking_paths/ "Garden of Forking Paths — FORRT (Framework for Open and Reproducible Research Training)"
[cmu-eda]: https://www.stat.cmu.edu/~hseltman/309/Book/chapter4.pdf "Seltman — Chapter 4: Exploratory Data Analysis. Carnegie Mellon University"
[gatech-eda]: https://sites.gatech.edu/omscs7641/2026/01/26/eda-for-cs7641/ "Beginner's Guide to Exploratory Data Analysis — Georgia Tech OMSCS 7641: Machine Learning"
[ncbi-eda]: https://www.ncbi.nlm.nih.gov/books/NBK543641/ "Exploratory Data Analysis — Secondary Analysis of Electronic Health Records (NCBI Bookshelf)"
[nist-handbook]: https://searchworks.stanford.edu/view/6914822 "NIST/SEMATECH e-Handbook of Statistical Methods"
[simpsons-paradox]: https://en.wikipedia.org/wiki/Simpson%27s_paradox "Simpson's Paradox — Wikipedia"

<!-- Dataset documentation frameworks -->
[gebru-datasheets]: https://cacm.acm.org/research/datasheets-for-datasets/ "Gebru et al. (2021) — Datasheets for Datasets. Communications of the ACM, 64(12)"
[data-cards]: https://dl.acm.org/doi/fullHtml/10.1145/3531146.3533231 "Pushkarna et al. (2022) — Data Cards: Purposeful and Transparent Dataset Documentation for Responsible AI. FAccT '22, ACM"
[data-profiling-wiki]: https://en.wikipedia.org/wiki/Data_profiling "Data Profiling — Wikipedia"

<!-- Profiling and validation tools -->
[ydata-profiling]: https://www.geeksforgeeks.org/data-analysis/unlocking-insights-with-exploratory-data-analysis-eda-the-role-of-ydata-profiling/ "YData Profiling overview — GeeksforGeeks"
[great-expectations]: https://paul-fry.medium.com/data-profiling-using-great-expectations-17776f140cdc "Fry — Data Profiling Using Great Expectations. Medium"
[whylogs]: https://docs.whylogs.com/en/latest/ "whylogs documentation — WhyLabs"
[tfdv]: https://www.tensorflow.org/tfx/guide/tfdv "TensorFlow Data Validation: Checking and Analyzing Your Data — TFX Guide"
[tfdv-acm]: https://dl.acm.org/doi/pdf/10.1145/3318464.3384707 "Breck et al. — TensorFlow Data Validation: Data Analysis and Validation in Continuous ML Pipelines. ACM SIGMOD 2019"
[deequ]: https://github.com/awslabs/deequ "Deequ: Unit Tests for Data — AWS Labs (GitHub)"

<!-- Process models and reporting standards -->
[crisp-dm]: https://rstudio-connect.hu.nl/redamoi_test/crisp-dm-as-a-guide-for-data-mining-and-eda.html "CRISP-DM as a Guide for Data Mining and EDA — HU University of Applied Sciences"
[crisp-mlq]: https://ml-ops.org/content/crisp-ml "CRISP-ML(Q): The ML Lifecycle Process — ML-Ops.org"
[reforms]: https://arxiv.org/html/2308.07832 "Kapoor et al. (2023) — reforms: Reporting Standards for Machine Learning Based Science. arXiv:2308.07832"
[provenance-tracking]: https://arxiv.org/html/2507.01075v1 "Provenance Tracking in Large-Scale Machine Learning Systems. arXiv"

<!-- Data cleaning and missing data -->
[consort-ai]: https://www.researchgate.net/figure/CONSORT-2010-flow-diagram-adapted-for-AI-clinical-trials-AIartificial-intelligence_fig2_344449884 "CONSORT 2010 flow diagram adapted for AI clinical trials — ResearchGate"
[mlinspect]: https://link.springer.com/article/10.1007/s00778-021-00726-w "Schelter et al. — Data Distribution Debugging in Machine Learning Pipelines. VLDB Journal, Springer"
[jeanselme-flow]: https://www.sciencedirect.com/science/article/pii/S1532046424000492 "Jeanselme et al. (2024) — Participant Flow Diagrams for Health Equity in AI. Journal of Biomedical Informatics"
[rubin-missing]: https://stefvanbuuren.name/fimd/sec-MCAR.html "Van Buuren — Concepts of MCAR, MAR and MNAR (Flexible Imputation of Missing Data)"
[mcar-mar-mnar]: https://apxml.com/courses/intro-feature-engineering/chapter-2-handling-missing-data/missing-data-mechanisms "Mechanisms of Missing Data (MCAR, MAR, MNAR) — APXML"
[missing-data-bias]: https://letsdatascience.com/blog/missing-data-strategies-how-to-handle-gaps-without-biasing-your-model "Missing Data Strategies: Why Deletion Fails — Let's Data Science"
[data-distribution-debugging]: https://link.springer.com/article/10.1007/s00778-021-00726-w "Schelter et al. — Data Distribution Debugging in ML Pipelines. VLDB Journal"

<!-- Temporal, panel, and sports-specific -->
[davis-sports-2024]: https://link.springer.com/article/10.1007/s10994-024-06585-0 "Davis et al. (2024) — Methodology and Evaluation in Sports Analytics: Challenges, Approaches, and Lessons Learned. Machine Learning, 113: 6977–7010"
[chitayat-esports]: https://arxiv.org/abs/2305.18477 "Chitayat et al. (2023) — Beyond the Meta: Leveraging Game Design Parameters for Patch-Agnostic Esport Analytics. arXiv:2305.18477"
[survivorship-bias]: https://pmc.ncbi.nlm.nih.gov/articles/PMC8207539/ "Czeisler et al. (2021) — Uncovering Survivorship Bias in Longitudinal Mental Health Surveys. Epidemiology and Psychiatric Sciences, PMC"
[stratos-ida]: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0295726 "Lusa et al. (2024) — Initial Data Analysis for Longitudinal Studies to Build a Solid Foundation for Reproducible Analysis. PLOS ONE"

<!-- GenAI transparency -->
[kuleuven-genai]: https://www.kuleuven.be/english/genai/transparency-about-the-use-of-genai "How to be transparent about the use of GenAI — KU Leuven"