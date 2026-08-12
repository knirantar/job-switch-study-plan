# Mathematics and Statistics for Machine Learning from Scratch

Parent subject: `07-python-mlops`
Study time: 3–4 hours
Target: senior AI platform / MLOps / backend interviews

## 1. FOUNDATIONS

### Why ML needs mathematics

Machine learning maps inputs to predictions by fitting parameters from data. Algebra represents relationships, linear algebra represents batches/features/transformations, calculus explains how parameters change loss, probability models uncertainty, and statistics tells us what can be inferred from finite samples. Libraries compute these operations, but engineers must recognize leakage, misleading metrics, unstable optimization, invalid experiments, and unfair/unsafe thresholds.

The goal is operational literacy, not theorem memorization. You should derive dimensions, calculate metrics, explain assumptions, choose evidence, and know when an estimate breaks. A model platform that serves an invalid experiment faster is still wrong.

### Numbers, variables, functions, and notation

A **scalar** is one number. A **variable** represents a value. A **function** maps input to output: `f(x)=2x+3`. A **parameter** is learned/fixed within a model; a **hyperparameter** controls learning/model configuration. For linear prediction `ŷ=w·x+b`, x is feature vector, w weights, b intercept, and ŷ prediction.

Subscripts index values: `x_i` ith observation or feature depending context; state it. Sigma `Σ` denotes sum. Mean of n values is `x̄=(1/n)Σx_i`. A superscript may mean power, not index; ML notation varies, so dimensions are your defense.

### Algebra and logarithms

Solve equations by applying the same valid operation to both sides. Linear functions have constant slope. Exponents represent repeated multiplication; logarithm is inverse. `log(ab)=log a+log b`, letting products become sums. Log-likelihood sums sample log probabilities, avoiding multiplication underflow and simplifying optimization.

Probability 0 can make log loss infinite; implementations clip predictions for numerical stability, but excessive clipping can hide invalid outputs. Log base e is natural log, conventional in ML; base choice scales values.

### Vectors and matrices

A **vector** is ordered numbers, e.g. claim features `x=[age, amount, prior_claims]`. Its dimension is 3. A **matrix** is rows and columns; an n×d design matrix X has n examples and d features. A tensor generalizes to more axes.

Vector addition and scalar multiplication are elementwise. **Dot product** `w·x=Σw_i x_i` produces scalar and measures weighted combination/geometric alignment. For w=[.2,.001,-.5], x=[40,100000,2], dot=8+100-1=107 (scales make it dominated by amount).

Matrix multiplication `(m×n)(n×p)→m×p` composes linear transforms. Inner dimensions must match. `Xw` with X n×d and w d×1 gives n predictions. Transpose `Xᵀ` swaps axes. Identity matrix leaves vectors unchanged. Inverse exists only for square nonsingular matrices, and explicit inversion is often numerically inferior to solving systems.

### Norms, distance, and similarity

L1 norm `Σ|x_i|`; L2 norm `sqrt(Σx_i²)`. Euclidean distance is L2 of difference. Cosine similarity `(a·b)/(||a||||b||)` measures angle and is common for embeddings. It is undefined for zero vector. Similarity choice must match embedding training/index normalization; “cosine 0.8” has no universal semantic meaning.

Feature scale matters for distance/gradient. Standardization `(x-mean)/std` makes mean near zero/std one; min-max maps a range but is outlier-sensitive and future min/max can shift. Fit transformations only on training data, then apply to validation/test/production.

### Calculus intuition

A **derivative** is local rate of change/slope. If `f(w)=w²`, derivative `2w`; at w=3, increasing w slightly increases f about 6 times the change. A **partial derivative** varies one parameter while others fixed. The **gradient** collects partial derivatives and points toward steepest increase; gradient descent moves opposite it.

Update `w_next=w-η∇L(w)`, where η learning rate. Too small converges slowly; too large overshoots/diverges. A **convex** loss has no bad local minima under domain; deep networks are non-convex, yet stochastic optimization works empirically.

The chain rule propagates derivatives through composed functions and underpins backpropagation. Automatic differentiation tracks operations and computes gradients; it does not guarantee the objective/data/model is correct.

### Probability foundations

A **sample space** is possible outcomes; an **event** is a subset. Probability P(A) is 0–1. Complement `P(not A)=1-P(A)`. Conditional `P(A|B)=P(A∩B)/P(B)`. Independence means `P(A∩B)=P(A)P(B)`, not merely “different components.”

Bayes' theorem:

`P(Disease|Positive)=P(Positive|Disease)P(Disease)/P(Positive)`.

Base rate matters. With prevalence 1%, sensitivity 90%, specificity 95%, among 10,000 people: 100 diseased→90 true positives; 9,900 healthy→495 false positives. Positive predictive value=90/(90+495)=15.38%, despite 90% sensitivity.

### Random variables and distributions

A random variable maps outcomes to numbers. Discrete examples: Bernoulli (0/1), binomial count of successes. Continuous examples: normal, exponential. A **probability mass function** gives discrete probabilities; density for continuous values integrates to probability and can exceed 1 locally.

Expected value `E[X]` is probability-weighted mean. Variance `E[(X-μ)²]`; standard deviation is square root in original units. Covariance shows joint linear variation; correlation normalizes to -1..1. Correlation does not imply causation and zero correlation does not imply independence generally.

Normal distribution is symmetric bell-shaped, but latency/income/claim amounts are often skewed/heavy-tailed. Mean and standard deviation are sensitive to outliers; median/quantiles/robust measures can be better.

### Population, sample, bias, and variance

A **population** is the target set; a **sample** is observed subset. Sampling must represent deployment population. Selection bias, survivorship, measurement error, missingness, label delay, and dataset shift invalidate inference.

An estimator is **unbiased** if expected estimate equals true parameter under assumptions. Variance describes estimate fluctuation. Model bias/variance also describe underfitting versus sensitivity. More data often reduces variance but does not fix systematic bias or label leakage.

Sample variance uses denominator n−1 for an unbiased population variance estimator under IID assumptions. Standard error of mean is `s/sqrt(n)`; it shrinks with sample size, unlike standard deviation of individual observations.

### Confidence intervals and hypothesis tests

A 95% confidence interval procedure covers the fixed true parameter in 95% of repeated samples under assumptions. It does not mean a computed frequentist interval has 95% probability containing the parameter. Approximate mean interval with large n is `x̄ ±1.96 SE`.

A null hypothesis represents baseline; p-value is probability, assuming null/model, of data at least as extreme. It is not probability null is true, effect importance, or replication probability. Choose significance before viewing results, report effect size and interval, account for multiple testing and experiment validity.

Type I error rejects true null (false positive); Type II fails to reject false null (false negative); power=1−Type II probability. Larger samples detect tiny effects that may be operationally irrelevant. Define minimum detectable/practically significant effect.

### Supervised learning metrics

Binary confusion matrix:

- TP predicted positive and actually positive;
- FP predicted positive, actually negative;
- TN predicted negative, actually negative;
- FN predicted negative, actually positive.

Accuracy=(TP+TN)/N. Precision=TP/(TP+FP). Recall/sensitivity=TP/(TP+FN). Specificity=TN/(TN+FP). F1=harmonic mean precision/recall. Metrics depend on threshold and prevalence. In 1% fraud, predicting all negative gives 99% accuracy and zero recall.

ROC curve plots recall vs false-positive rate across thresholds; ROC AUC is probability a random positive ranks above random negative under interpretation assumptions. Precision-recall is often more informative for rare positives. Neither chooses a threshold or captures calibration/business costs.

**Calibration** means predictions near p occur about p fraction of time for a defined population. A perfectly ranking model can be miscalibrated. Brier score is mean squared probability error; log loss strongly penalizes confident wrong predictions.

Regression metrics: MAE mean absolute error, MSE mean squared, RMSE square root, R² relative variance explanation. MSE emphasizes outliers; MAPE breaks/behaves badly near zero. Evaluate business units and slices.

## 2. CORE MECHANICS

### 2.1 Shape a linear model

X has 4 claims ×3 features, shape (4,3). w shape (3,), b scalar. `X@w+b` broadcasts b and returns (4,). If y shape (4,), residual aligns. If y accidentally shape (4,1), subtracting `(4,)-(4,1)` broadcasts to (4,4), silently wrong. Assert shapes.

### 2.2 Standardize without leakage

Training amounts [100,200,300]: mean 200, population std≈81.65. Transform train [-1.225,0,1.225]. Validation amount 400 transforms 2.449 using training stats. Recomputing mean/std including validation leaks its distribution and changes deployed transform.

Store transform parameters with model pipeline and handle zero-variance feature (drop or defined scaling).

### 2.3 Gradient descent by hand

One point x=2,y=10; model ŷ=wx, loss `(wx-y)²`. Derivative `2(wx-y)x`. Start w=1: prediction2, residual−8, gradient−32. η=.1 gives w=4.2. Prediction 8.4, loss 2.56 versus initial64. Next gradient `2(8.4-10)2=-6.4`, w=4.84. Too-large η=1 gives w=33, severe overshoot.

### 2.4 Bayes table

Prevalence .01, sensitivity .90, specificity .95, N=10,000. TP90,FN10,TN9405,FP495. Precision/PPV15.38%, NPV=9405/(9405+10)=99.89%. A positive result needs confirmatory workflow; base rates dominate.

### 2.5 Mean, variance, standard error

Sample [10,12,14,16,18], mean14. Deviations -4,-2,0,2,4; squared sum40. Sample variance=40/(5−1)=10; s≈3.162; SE≈1.414. Approx 95% normal interval 14±2.772=[11.228,16.772], but n=5 should use t distribution (df4 critical≈2.776), interval≈[10.074,17.926]. Assumptions/normality matter.

### 2.6 Confusion metrics

TP=80,FP=20,FN=40,TN=860,N=1000. Accuracy94%; precision80%; recall66.67%; specificity97.73%; F1≈72.73%. Whether good depends on cost of 40 misses versus 20 false investigations.

Lowering threshold usually increases TP and FP (recall up, precision may fall). Evaluate exact policy on validation/test representing deployment and protected slices.

### 2.7 Expected cost threshold

False negative costs ₹10,000, false positive review ₹100. Current confusion FN40,FP20 → expected sample cost ₹402,000. Alternative FN10,FP200 → ₹120,000, much better despite lower accuracy. Costs can be uncertain/nonlinear; include capacity and ethics/regulation.

### 2.8 Log loss

For true y=1 and predicted p=.9, loss `-ln(.9)=.1053`; p=.1 gives 2.3026; p=.001 gives 6.9078. Confident wrong predictions are heavily penalized. Clip only at machine-safe epsilon and investigate saturation.

### 2.9 A/B conversion interval

Control 10,000 users, 1,000 convert=10%; treatment 10,000, 1,080=10.8%; absolute lift .8 percentage points. Approx SE difference=`sqrt(.1*.9/10000 + .108*.892/10000)=.004317`; 95% CI .008±.00846≈[-.00046,.01646]. Not conventionally significant at .05; data compatible with tiny negative to 1.65 pp positive.

Do not stop experiment when p first crosses .05 without sequential design; repeated peeking inflates false positives.

### 2.10 Data split

Random split assumes exchangeability and can leak same patient/time/entity. For future deployment use temporal split: train before date, validation later, final test latest; group patient/account to prevent duplicates across sets; fit preprocessing only train. Preserve test as final unbiased estimate, not repeated tuning set.

## 3. WORKED PROBLEMS

### Problem 1 — Matrix shape (easy)

X (500,20), W (20,8). Output?

**Solution.** (500,8); inner dimensions 20 match.

**Trap:** elementwise multiplication.

### Problem 2 — Dot product (easy)

[1,2,3]·[4,-1,2].

**Solution.** 4−2+6=8.

**Trap:** returning vector of products.

### Problem 3 — Standard error (easy)

s=20,n=400.

**Solution.** 20/sqrt400=1. Standard deviation remains20; SE describes mean estimate.

**Trap:** dividing by n.

### Problem 4 — Base rate (medium)

Prevalence .1%, sensitivity99%, specificity99%, N=100,000. PPV?

**Solution.** Diseased100→99 TP; healthy99,900→999 FP. PPV=99/1098≈9.02%.

**Trap:** saying positive is 99% likely true.

### Problem 5 — Accuracy imbalance (medium)

50 positives, 9,950 negatives; all-negative model.

**Solution.** Accuracy99.5%, recall0, no useful positive detection. Report confusion/PR and business cost.

**Trap:** selecting by accuracy.

### Problem 6 — F1 (medium)

Precision .75, recall .60.

**Solution.** `2*.75*.60/(1.35)=.6667`.

**Trap:** arithmetic mean .675.

### Problem 7 — Leakage (hard)

Feature “claim approved reason” predicts approval at submission.

**Solution.** It is generated after decision, unavailable at prediction time, direct target leakage. Remove; create point-in-time feature available before submission; audit lineage/timestamps.

**Trap:** accepting high validation AUC.

### Problem 8 — P-value (hard)

p=.03. Is null 3% likely?

**Solution.** No. Under null/model, probability of result at least this extreme is3%. Need prior/design/effect/CI/multiplicity; p does not give P(null|data).

**Trap:** posterior interpretation.

### Problem 9 — Calibration (hard)

Among 1,000 predictions around .8, only 500 positive.

**Solution.** Model is overconfident/miscalibrated for that bin/population; observed frequency .5. Investigate shift/slicing and recalibrate on representative validation; don't simply change labels.

**Trap:** claiming threshold ranking proves probability accuracy.

## 4. REAL-WORLD / APPLIED CONTEXT

### Logistic regression

Logistic regression maps linear score through sigmoid to 0–1 and minimizes log loss. Coefficient exponent gives odds ratio per unit holding others fixed, not probability-point change. Scaling, multicollinearity, regularization, calibration, and causal misinterpretation matter.

### Embedding retrieval

Embedding systems compare vectors with dot product/cosine/L2. Index choice must match model normalization; approximate nearest-neighbor trades recall for latency/memory. Offline retrieval recall and downstream answer grounding must both be measured.

### Clinical diagnostic testing

Sensitivity/specificity are conditional on true status; predictive values depend on prevalence. Population shift changes PPV even when sensitivity/specificity remain. This is directly relevant to healthcare model deployment and human oversight.

## 5. COMPARISON TABLE

| Measure | Formula/focus | Best when | Limitation |
|---|---|---|---|
| Accuracy | correct/N | balanced equal costs | hides rare class |
| Precision | TP/(TP+FP) | false positives costly | prevalence/threshold dependent |
| Recall | TP/(TP+FN) | misses costly | ignores FP |
| Specificity | TN/(TN+FP) | false-positive control | ignores FN |
| F1 | harmonic P/R | need one balance | ignores TN/cost/calibration |
| ROC AUC | ranking across thresholds | general discrimination | optimistic-looking on rare class |
| PR AUC | precision-recall ranking | rare positive focus | baseline depends prevalence |
| Log loss | probability likelihood | calibrated probabilities | sensitive confident errors |
| Brier | squared probability error | calibration+accuracy | decomposition/slices needed |
| MAE | absolute regression error | interpretable/robust | nondifferentiable at zero |
| RMSE | sqrt squared error | punish large errors | outlier-sensitive |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. Matrix multiply is elementwise—it is sum over inner dimension.
2. Inverse is default solve—numerically use solve/factorization.
3. Gradient descent always finds global optimum—not nonconvex generally.
4. Independence means different services—shared causes break it.
5. Correlation implies cause—confounding/reverse/selection exist.
6. Standard deviation and standard error are same—individual spread vs estimate uncertainty.
7. 95% CI means 95% probability parameter inside—not frequentist interpretation.
8. p-value is probability null true—it is conditional extremeness.
9. Accuracy works on imbalance—it can reward useless model.
10. ROC AUC selects threshold—it does not.
11. High AUC means calibrated probabilities—ranking and calibration differ.
12. Random split is always valid—time/entity leakage can dominate.

## 7. CHEAT SHEET — REVIEW ONLY

Review only, not a substitute for the lesson.

- X `(n,d)`, w `(d,)` → predictions `(n,)`; assert shapes.
- Dot=sum products; cosine=dot/(norms).
- Fit scaling on train only.
- Gradient descent: parameter minus learning rate×gradient.
- Bayes: posterior ∝ likelihood×prior; base rate matters.
- Variance spread squared; SD original unit; SE=s/sqrt(n).
- CI procedure coverage, not posterior probability.
- p-value=P(extreme data|null), not P(null|data).
- Precision FP-sensitive; recall FN-sensitive; threshold changes both.
- Accuracy fails on rare positives.
- Ranking ≠ calibration ≠ threshold utility.
- Split by deployment time/entity and prevent leakage.

## 8. PRACTICE SET FOR SELF-TEST

1. Multiply shapes `(100,12)` and `(12,1)`.
2. Compute L2 norm [3,4].
3. Standardize x=130 with training mean100,std15.
4. Compute Bayes PPV for prevalence2%, sensitivity95%, specificity90% over10,000.
5. Calculate sample mean/variance for [2,4,6].
6. Confusion TP30,FP10,FN20,TN940: precision,recall,accuracy.
7. Calculate false-cost FN×5000+FP×50.
8. Interpret 95% CI treatment lift [-.2pp,1.4pp].
9. Identify leakage in “future 30-day spend” predicting approval today.
10. Explain calibration test for predictions 0.7–0.8.

## 9. CURATED RESOURCES

- Gilbert Strang, *Introduction to Linear Algebra*, 6th ed., Chapters 1–4 — vectors, matrices, systems, spaces, orthogonality, least squares.
- James et al., *An Introduction to Statistical Learning*, 2nd ed., Chapters 2–5 — supervised learning, regression/classification, resampling and evaluation.
- Kevin Murphy, *Probabilistic Machine Learning: An Introduction*, Chapters 2–5 and 10 — probability, distributions, inference, linear/logistic models.
- Wasserman, *All of Statistics*, Chapters 1–10 — probability, expectation, convergence, estimation, confidence, hypothesis tests.
- Google Machine Learning Crash Course modules on linear/logistic regression, classification, data, and overfitting — worked interactive intuition.
- scikit-learn official User Guide, “Model selection and evaluation,” “Preprocessing,” “Calibration,” and “Common pitfalls” — executable metric/split/leakage guidance.
- David Hand, “Measuring classifier performance: a coherent alternative to the area under the ROC curve,” 2009 — critical understanding of AUC assumptions.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Discrete Math/Complexity:** functions, logs, counting, probability basics.
2. **Python Tooling/Data:** arrays, tables, numerical tolerance, reproducibility.

### After

1. **ML Fundamentals:** applies these mechanics to models, evaluation, fairness, thresholds.
2. **Generative AI Foundations:** uses vectors, softmax/probability, loss, similarity.
3. **ML Lifecycle:** uses statistical gates, drift, experiments, delayed labels.
4. **Model Serving:** connects metrics/calibration/cost to online decisions.

---ANSWER KEY BELOW---

1. `(100,1)`.
2. 5.
3. 2.
4. 200 diseased→190 TP;9800 healthy→980 FP; PPV190/1170≈16.24%.
5. Mean4; squared deviations8; sample variance8/(3−1)=4.
6. Precision75%; recall60%; accuracy970/1000=97%.
7. For given confusion:20×5000+10×50=100,500.
8. Data compatible with small harm to 1.4pp lift; includes zero, not conventionally significant; assess design/power/practical decision.
9. Feature uses information after prediction time/possibly outcome consequences; point-in-time leakage.
10. Bin/estimate predictions in range on representative held-out population; observed positive fraction should approximate average predicted probability, with uncertainty/slices.
