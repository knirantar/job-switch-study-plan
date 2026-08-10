# Machine Learning Fundamentals for Platform Engineers

**Parent:** 07 — Python and MLOps  
**Target:** senior backend / AI-platform / MLOps engineering  
**Study time:** 3–4 hours plus the executable evaluation lab

## 1. FOUNDATIONS

Machine learning estimates a useful relationship from examples rather than encoding every rule manually. A **feature vector** x represents information available at prediction time. A **target/label** y is the outcome to predict. A model f with learned parameters maps x to a prediction. **Training** chooses parameters using historical data and an objective; **inference** applies the fitted model to new examples.

In **supervised learning**, examples include labels. Classification predicts categories/probabilities; regression predicts numeric values; ranking orders candidates; survival/time-to-event models include censoring/time. **Unsupervised learning** finds structure without direct labels—clustering, density, representation, anomaly methods. **Self-supervised** objectives create labels from data; reinforcement learning learns action policies from rewards/interactions. The business question determines formulation, not algorithm popularity.

The goal is **generalization**: performance on future data drawn from the deployment process, not memorization of training examples. **Empirical risk minimization** selects a function minimizing average loss on observed samples. Because many functions fit finite data, assumptions, regularization, architecture and validation control which generalizes.

A **parameter** is learned (linear coefficient, tree split, neural weight). A **hyperparameter** is selected outside fitting (regularization strength, depth, learning rate). A **loss** trains/compares per example or batch; a **metric** communicates evaluation aligned to product decisions. Cross-entropy may optimize a classifier while recall at a policy threshold and expected investigation cost determine deployment.

Statistical learning assumes training/evaluation/deployment data relationships. **Independent and identically distributed (IID)** is an approximation: examples independent and drawn from the same distribution. Healthcare claims from one member repeat, time changes policy/coding, and hospitals/regions differ, violating naïve random-split assumptions. Split design must simulate deployment.

**Data leakage** occurs when training uses information unavailable at prediction time or evaluation contaminates model selection. A feature named paid_amount computed after claim adjudication trivially predicts adjudication. Fitting normalization/imputation on all data lets test distribution influence training. Repeated member rows across train/test let a model memorize patient patterns. Leakage yields impressive offline numbers and production failure.

ML systems exist to support decisions. A score is not a decision until a threshold/action/cost/capacity policy is applied. A model can rank well yet be poorly calibrated; be accurate overall yet fail a subgroup; improve metric while worsening downstream operations; reflect historical inequity. Platform engineers must understand these boundaries to build correct training, registry, serving and monitoring systems.

## 2. CORE MECHANICS

### 2.1 Frame the problem and prediction time

Write: decision/action, unit of prediction, timestamp, available information, label definition/window, delay, costs, users and success constraints. Example: “At claim submission, estimate probability that expert review confirms high-risk billing within 60 days; route limited review capacity. Exclude post-adjudication features.”

The unit might be claim, member-month, encounter or provider. Multiple rows per unit create dependence. Define positive event precisely, including ambiguous/unobserved outcomes. Labels delayed 60 days mean newest training period lacks complete labels; negative today may become positive later. Define censoring/maturation.

Decide whether automation, prioritization or decision support is appropriate. High-stakes denial may require human review and causal/legal policy, while prioritizing an audit queue may tolerate ranking errors. Model objective is subordinate to clinical/financial/product policy.

### 2.2 Data splits

Training data fits parameters. Validation data selects features/hyperparameters/threshold. Test data is untouched until final estimate. Reusing test feedback for iterations turns it into validation and makes results optimistic.

Random split works only when future units are exchangeable and leakage groups do not cross. Use **group split** so one member/provider/customer appears in only one partition. Use **time split** to train before cutoff, validate/test afterward, respecting feature/label availability. For deployment to unseen hospitals, use site/domain holdout. Sometimes combine: chronological cutoff plus group constraints.

K-fold cross-validation rotates validation folds within training data, improving data efficiency and measuring variability. Every preprocessing/feature selection/calibration step must fit inside each fold. Stratification preserves approximate class ratios for engineering feasibility but can understate natural rare-class variability; scikit-learn documentation explicitly notes it is an engineering workaround, not a statistical solution.

### 2.3 Baselines

Start with a non-ML/product baseline: predict majority, historical prevalence, simple rule, current human/workflow, random ranking and a linear model. A 99% negative dataset gives 99% accuracy by always negative and zero recall. A complex model must beat a relevant baseline by a practically meaningful amount after cost, latency and maintenance.

Baselines validate the pipeline. If a simple rule is perfect, inspect leakage. If complex model underperforms, features/data/formulation may be wrong. Report confidence/variation, not one score.

### 2.4 Features and preprocessing

Features must be available with the same semantics online/offline. Numerical transforms include scaling, log transform, winsorization/robust statistics and missing indicators. Categorical encoding includes one-hot, ordinal only when order real, hashing/target encoding with leakage controls and embeddings. Dates become age/season/elapsed using a prediction timestamp; free text requires tokenization/representation and privacy.

Missingness can carry signal but may reflect access inequity or pipeline failure. Fit imputation on training only. A global mean computed before split leaks evaluation distribution. Keep preprocessing and estimator in one pipeline artifact. Version schema, feature definition, source time and code.

Avoid identifiers as predictive features unless justified; they enable memorization/proxy discrimination and poor generalization. Provider ID may legitimately matter operationally but also encode site demographics; evaluate unseen provider and policy constraints.

### 2.5 Linear regression

Linear regression models y_hat = β0 + Σβj xj and commonly minimizes mean squared error. Least squares has closed-form under conditions or gradient optimization. Coefficients express conditional linear association given representation, not causality.

MSE squares residuals and heavily penalizes outliers. Mean absolute error is more robust but has different optimization/statistical target. R-squared compares squared error to predicting mean; it can be negative on test and does not communicate clinical units. Inspect residuals, heteroscedasticity, nonlinearity and segment performance.

Multicollinearity makes coefficients unstable even when prediction remains adequate. Scaling affects regularization/optimization. Never extrapolate beyond training range blindly.

### 2.6 Logistic regression

For binary classification, logistic regression models log odds as linear: log(p/(1−p)) = β0 + β·x, so p = sigmoid(z). It optimizes log loss rather than squared classification error. A coefficient exp(βj) is an odds multiplier per feature unit holding others fixed, not a probability increase and not causal.

Log loss strongly penalizes confident wrong predictions. Perfect separation can drive unregularized coefficients toward infinity. Regularization and solver behavior matter. Scaling helps optimization and makes regularization comparable. Logistic regression is a strong interpretable baseline and can model nonlinearity through engineered transformations/interactions.

### 2.7 Loss, gradient descent and learning rate

Gradient descent updates parameters opposite the loss gradient: θ_next = θ − η∇L. Learning rate too high diverges/oscillates; too low converges slowly. Stochastic/mini-batch gradients estimate full gradient, enabling large datasets and injecting noise. Epoch means one pass; batch size affects memory, gradient noise and hardware utilization.

Optimization loss decreasing does not prove generalization. Track train/validation curves. Early stopping is regularization/model selection and must use validation only. Feature scale/conditioning affects descent. Adaptive optimizers change step computation but do not remove tuning/data issues.

### 2.8 Bias, variance and regularization

**Underfitting/high bias** means model class/training cannot capture signal: train and validation poor. **Overfitting/high variance** means train excellent, validation worse and results unstable. More capacity/features/training can reduce bias but increase variance.

L2 regularization adds squared coefficient penalty, shrinking smoothly; L1 adds absolute penalty, encouraging zeros/sparsity. Elastic net combines. Regularization strength is selected on validation/CV after scaling inside pipeline. Tree depth/min samples, boosting learning rate/rounds, dropout/weight decay and early stopping are analogous complexity controls.

More data often reduces variance if representative and correctly labeled. It does not fix target leakage, biased labels or distribution mismatch.

### 2.9 Decision trees

A classification tree greedily selects splits reducing impurity (Gini/entropy), creating piecewise constant regions. Trees capture nonlinear interactions, tolerate monotonic transforms and require less scaling. Deep trees memorize; small data changes can choose different splits. Optimal tree search is generally intractable, so implementations are greedy heuristics.

Control depth, min samples leaf/split, max leaves/features and pruning. Leaf probability is label fraction and may be poorly calibrated, especially small leaves. Trees extrapolate poorly and split high-cardinality features opportunistically.

### 2.10 Ensembles

**Bagging/random forests** train trees on resampled data and random feature subsets, averaging to reduce variance/decorrelate. They parallelize and are robust baselines but can be large and probabilities biased.

**Boosting** adds weak learners sequentially to correct residuals/gradients. Gradient-boosted trees (XGBoost/LightGBM/CatBoost variants) excel on tabular data, handling nonlinear interactions/missing/categorical depending implementation. They need depth/leaves, learning rate, rounds, sampling and regularization tuning; leakage and threshold economics still dominate.

Stacking/blending combines model outputs using out-of-fold predictions. Training meta-model on in-sample base predictions leaks. Ensemble diversity matters; averaging identical errors does little.

### 2.11 Neural networks

A feed-forward network composes affine transforms and nonlinear activations into expressive functions. Backpropagation computes gradients by chain rule. Depth/width enable representation learning; optimization uses mini-batches. Networks need initialization, normalization, activation, optimizer, regularization, data/compute and reproducibility controls.

For small structured tabular claims data, gradient-boosted trees/logistic baselines often deserve priority. Deep learning is compelling for text, images, audio, sequences and huge interactions, but higher serving cost/latency and calibration/interpretability burden must be justified.

### 2.12 Confusion matrix

For positive label: true positive predicted positive correctly; false positive predicted positive but actually negative; true negative correctly negative; false negative missed positive. At threshold 0.60, the lab’s 20 rows yield TP=7, FP=0, TN=11, FN=2.

Accuracy=(TP+TN)/N=18/20=90%. Precision=TP/(TP+FP)=100%. Recall/sensitivity=TP/(TP+FN)=7/9=77.78%. Specificity=TN/(TN+FP)=100%. F1=harmonic precision/recall=0.875. Metrics require denominator handling and confidence; tiny N is demonstration, not evidence for deployment.

### 2.13 Thresholds and decision costs

Scores become labels at threshold. Lower threshold usually raises recall and false positives; higher raises precision/specificity and false negatives. Threshold belongs to policy/deployment artifact, not necessarily model training.

Lab at 0.50 yields TP=8, FP=2, TN=9, FN=1. If FP review costs ₹100 and missed positive costs ₹1,000, expected sample cost is 2×100+1×1000=₹1,200. Threshold 0.70 gives TP=5, FP=0, TN=11, FN=4, cost ₹4,000. This simplified matrix ignores downstream capacity, benefit, uncertainty and harm distribution; derive costs with stakeholders.

Capacity-constrained review may choose top K or threshold satisfying workload. A threshold tuned on validation must be tested unchanged. Prevalence/score drift changes precision and workload even if conditional performance remains.

### 2.14 ROC, PR and AUC

ROC plots true-positive rate against false-positive rate across thresholds. ROC AUC equals probability that a randomly selected positive scores above a randomly selected negative, with ties half. Lab pairwise calculation has 9 positives×11 negatives=99 pairs and AUC=97/99≈0.979798.

AUC is threshold-independent ranking, not probability calibration or operational value. It can look strong under extreme imbalance while precision is poor. Precision–recall curve focuses positive retrieval and prevalence; average precision summarizes but also needs baseline prevalence and threshold/capacity view.

Do not compare AUCs from different populations casually. Confidence intervals/dependent tests and segment evaluation matter. AUC ignores magnitude of ranking gaps.

### 2.15 Calibration and proper scoring

A classifier is calibrated if among predictions near 0.7, about 70% become positive. Discrimination ranks; calibration assigns probability meaning. A monotonic transform can preserve AUC while ruin calibration.

Brier score averages (p−y)^2; lower better. Lab Brier is 0.104135. Log loss is another proper score, harsher on confident errors. Compare to prevalence baseline and decompose/reliability plots; one scalar can hide local miscalibration.

Fit Platt/sigmoid or isotonic calibrator on data independent of base-model fitting (often out-of-fold/calibration split). Calibrating training predictions is optimistically extreme. Isotonic flexible but overfits small data; sigmoid restrictive. Recheck under prevalence/time/domain shift and subgroups.

### 2.16 Class imbalance

Imbalance affects metric variance, training and decisions. Accuracy is misleading. Use stratification for fold feasibility but group/time constraints first. Class weights alter loss; resampling changes training distribution; synthetic methods risk unrealistic/leaky examples. Apply resampling inside training folds only.

Weighting/oversampling can distort raw probabilities, requiring calibration on natural-prevalence data. Evaluate PR, recall at precision, precision at capacity, expected cost and subgroup false-negative rates. Collecting more informative positives may beat algorithm tuning.

### 2.17 Uncertainty and statistical inference

Metrics on finite test data are estimates. Bootstrap over independent units/groups (not rows when patients repeat) to form intervals; time/block bootstrap for dependence. Rare-event recall with nine positives has huge uncertainty despite 7/9 point estimate.

Compare paired predictions on same examples. Do not declare improvement from 0.901 to 0.903 without practical/statistical uncertainty and decision impact. Repeated hyperparameter search overfits validation. Record all trials, nested CV when honest selection estimate needed, and one final test.

Prediction uncertainty includes aleatoric noise and epistemic/model uncertainty; methods vary. A high confidence score is not causal certainty. Out-of-distribution detection is imperfect. Design abstention/human review and safe fallback.

### 2.18 Data drift and concept drift

Covariate drift changes P(x); prior/label shift changes P(y); concept drift changes P(y|x). Feature distribution change does not guarantee quality degradation; no drift does not guarantee correctness. Monitor input/schema/missing/range, prediction/prevalence, performance after delayed labels and business outcome.

Training-serving skew is implementation mismatch: different code, clock, joins, defaults or feature freshness. Feature parity tests and point-in-time correct retrieval are essential. Label feedback can be selective: only reviewed claims receive outcomes, creating bias.

### 2.19 Fairness, causality and high-stakes use

Evaluate performance/calibration/error rates by legally/clinically relevant groups with sufficient sample and privacy safeguards. Aggregate fairness can hide intersectional harm; tiny groups yield uncertain metrics. Equal calibration, equalized error rates and equal selection rates can conflict when base rates differ. Choose based on use/law/ethics, not a universal metric.

Historical labels reflect access and policy; removing protected attribute does not remove proxies. Human-in-loop can inherit automation bias. Provide contest/appeal and measure downstream decisions, not just model.

Prediction answers association under observed process, not treatment effect. “Patients taking drug X have worse outcomes” does not imply drug causes harm due to confounding. Intervention decisions need causal design/domain trials, not predictive feature importance.

### 2.20 Reproducibility and security

Fix and record data snapshot/query, code, environment, random seeds, split IDs, feature schema, parameters, model/threshold/calibration and evaluation. Seed helps but parallel/native/GPU operations can remain nondeterministic; quantify.

Model artifact is executable/sensitive supply chain. Avoid untrusted pickle, sign/attest, restrict registry, scan dependencies, protect training data/labels and audit promotion. Membership/privacy leakage and model inversion are possible. Do not publish tiny subgroup metrics or raw records.

## 3. WORKED PROBLEMS

### Problem 1 — Leakage-safe split

**Statement.** Claims repeat per member; model predicts at submission using 60-day outcome. Design split.

**Solution.** Choose prediction cutoff and label maturation. Train earlier fully matured claims, validate later, final test latest matured. Ensure each member/provider leakage group stays one partition (or evaluate explicit returning-member deployment separately). Fit all preprocessing/calibration in training folds. Exclude post-submission fields.

**Mistake caught:** random row split treats correlated/future information as generalization.

### Problem 2 — Majority accuracy

**Statement.** 1% positives; all-negative model.

**Solution.** Accuracy=99%, specificity=100%, recall=0%, precision undefined/0 by convention. It misses every positive. Compare PR/recall/cost and product baseline.

**Mistake caught:** accuracy means useful rare-event model.

### Problem 3 — Lab confusion matrix

**Statement.** At 0.60, TP=7, FP=0, TN=11, FN=2. Compute metrics.

**Solution.** Accuracy 18/20=.90; precision 7/7=1; recall 7/9=.7778; specificity 11/11=1; F1=2×1×.7778/(1+.7778)=.875. Report N and class counts.

**Mistake caught:** swapping FP/FN denominators.

### Problem 4 — Threshold cost

**Statement.** Compare threshold .50 matrix (8,2,9,1) with .70 (5,0,11,4), FP ₹100, FN ₹1,000.

**Solution.** .50 cost=₹1,200; .70 cost=₹4,000. Choose .50 under simplified costs. Also verify review capacity: .50 flags 10/20 versus .70 5/20; include benefit, uncertainty and subgroup harm.

**Mistake caught:** maximizing precision without decision cost/capacity.

### Problem 5 — AUC pairwise

**Statement.** Nine positives, eleven negatives, 97 correctly ordered positive-negative pairs and no ties.

**Solution.** Total 99; AUC=97/99=.979798. It means ranking probability, not 97.98% accuracy or calibrated probability.

**Mistake caught:** interpreting AUC as accuracy.

### Problem 6 — Brier

**Statement.** One positive predicted .9 and one negative predicted .4. Compute Brier.

**Solution.** ((.9−1)^2+(.4−0)^2)/2=(.01+.16)/2=.085. Model with predictions .7/.2 gives (.09+.04)/2=.065, better Brier despite both classify correctly at .5.

**Mistake caught:** threshold accuracy measures probability quality.

### Problem 7 — Regularization

**Statement.** Train accuracy 99%, validation 72%, coefficients huge and correlated features.

**Solution.** High variance/separation/multicollinearity likely. Verify leakage/split first; scale within pipeline; increase L2 or elastic-net regularization, simplify/remove unstable redundant features, collect representative data and tune via group/time CV. Do not inspect test repeatedly.

**Mistake caught:** blindly increase model capacity/epochs.

### Problem 8 — Calibration leakage

**Statement.** Gradient booster fit and isotonic calibrator both use same training predictions.

**Solution.** Training predictions are overconfident; calibrator learns biased extremes. Use held-out calibration or out-of-fold predictions; reserve final test. Ensure classes in calibration folds, then evaluate reliability/Brier/log loss and decision metrics.

**Mistake caught:** calibration is harmless postprocessing on training data.

### Problem 9 — Drift response

**Statement.** Score distribution shifts after policy change but delayed labels unavailable.

**Solution.** Validate schema/feature pipeline and cohort/traffic mix; compare training/previous distributions with practical thresholds; inspect missing/freshness and model version. Do not auto-retrain solely on drift. Apply guardrails/manual review, wait for matured labels, evaluate outcome/performance and investigate causal product change.

**Mistake caught:** any drift means model degraded and retraining fixes it.

## 4. REAL-WORLD / APPLIED CONTEXT

Scikit-learn’s current cross-validation guidance explicitly warns that fitting/testing same data overfits and that repeated test-set tuning leaks. It also notes chronological data should not be shuffled when future differs and stratification can artificially reduce variability.

The calibration guide states calibrators should fit predictions independent of base training and describes cross-validation calibration. The decision-tree guide describes greedy non-global optimization, instability, piecewise-constant prediction and ensemble mitigation.

The executable lab uses 20 dated claims, 18 unique members, 9 positives and 11 negatives. At threshold .60 it verifies (7,0,11,2), accuracy .90, recall 7/9 and F1 .875. It verifies .50 cost ₹1,200 versus .70 ₹4,000 under stated matrix, AUC 97/99 and Brier .104135. Five standard-library tests pass. Dataset is realistic teaching data, not clinical evidence.

## 5. COMPARISON TABLE

| Model | Strength | Weakness | Use |
|---|---|---|---|
| Logistic regression | strong baseline, odds, fast/calibratable | linear log-odds unless features | sparse/tabular interpretable baseline |
| Decision tree | nonlinear rules/interactions | unstable/overfits/piecewise | small rules/explanation prototype |
| Random forest | variance reduction, robust | large/slower, weak extrapolation/calibration | tabular baseline |
| Gradient boosting | strong tabular accuracy | tuning/serial training/overfit | production structured data |
| Neural network | representation/nonlinear scale | data/compute/calibration/debug | text/image/large complex signals |

| Metric | Answers | Key dependency | Failure |
|---|---|---|---|
| Accuracy | fraction correct | prevalence/threshold | hides minority |
| Precision | flagged fraction truly positive | prevalence/threshold | ignores missed positives |
| Recall | positive fraction found | threshold/labels | ignores workload false positives |
| ROC AUC | pairwise ranking | population | not calibration/decision; imbalance opacity |
| PR curve/AP | positive retrieval | prevalence | cross-population comparison |
| Brier/log loss | probability quality | calibration/prevalence | scalar hides local/subgroup |
| Expected cost | policy value | valid cost/capacity estimates | costs uncertain/nonlinear |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Algorithm before decision framing.** Define action/unit/time/label/cost first.
2. **Random rows always valid.** Groups/time/sites leak.
3. **Test set used repeatedly.** It becomes validation and optimistic.
4. **Preprocess before split.** Statistics/selection leak evaluation.
5. **Feature exists historically so available online.** Enforce point-in-time availability.
6. **More data fixes all.** It can replicate bias/leakage/mismatch.
7. **Accuracy enough.** Imbalance can yield useless 99%.
8. **AUC is accuracy.** It is pairwise ranking.
9. **AUC means calibrated probabilities.** Monotonic transforms preserve AUC.
10. **F1 captures business cost.** It weights precision/recall symmetrically by formula.
11. **Threshold .5 is natural.** Choose from cost/capacity on validation.
12. **Class weighting preserves probabilities.** It can alter calibration.
13. **Oversample before split.** Duplicates/synthetic neighbors leak.
14. **Stratification solves statistics.** It can hide rare-class variability.
15. **Coefficient is causal/probability increase.** It is conditional log-odds association.
16. **Tree interpretable by default.** Deep/unstable trees and proxy features complicate.
17. **Feature importance means causal contribution.** It is model/data dependent.
18. **Training loss down means better.** Validation/generalization may worsen.
19. **Calibration on training predictions.** It is biased; use independent predictions.
20. **Drift equals performance drop.** Need labels/outcome and pipeline diagnosis.
21. **No drift equals safe.** Concept/correctness can fail without marginal change.
22. **Remove protected field removes bias.** Proxies/historical labels remain.
23. **One aggregate metric protects groups.** Evaluate relevant intersections/uncertainty.
24. **Seed guarantees reproducibility.** Native/GPU parallelism may remain nondeterministic.
25. **Model artifact is inert data.** Formats/dependencies can execute code and leak.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

- Frame: decision, unit, prediction timestamp, available features, label/window/delay, action/cost.
- Split to simulate deployment: time + group/site as needed; test once.
- Fit preprocessing, selection, resampling and calibration inside training folds.
- Start majority/rule/current-process/logistic baselines.
- Underfit: train+validation poor. Overfit: train high, validation gap/variance.
- Logistic: linear log odds; tree: greedy piecewise; forest bags; boosting corrects residuals.
- TP/FP/TN/FN. Precision TP/(TP+FP); recall TP/(TP+FN); specificity TN/(TN+FP).
- Threshold is policy; optimize validated cost/capacity, not default .5.
- ROC AUC is pairwise ranking; PR reflects positives/prevalence; Brier/log loss probability.
- Calibration uses independent/out-of-fold predictions.
- Evaluate uncertainty, time/site/tenant/subgroups and delayed labels.
- Prediction is association, not intervention causality.

## 8. PRACTICE SET FOR SELF-TEST

1. Frame a 30-day hospital readmission model including prediction time, label maturity, action and leakage fields.
2. Design time/group/site train-validation-test for claims with repeat members/providers and new region deployment.
3. For TP=240, FP=160, TN=9,340, FN=260 calculate all core metrics and prevalence.
4. Choose threshold between matrices A=(90,210,8,790,10) and B=(70,60,8,940,30) for FP ₹200/FN ₹5,000 plus review capacity 250.
5. Compute pairwise AUC for positive scores [.9,.6,.5] and negative [.7,.5,.2], including ties.
6. Compare Brier/log loss intuition for calibrated moderate predictions versus overconfident errors.
7. Diagnose train .98, group-CV .71, random-CV .94 and propose experiments.
8. Design a leakage-free boosting pipeline with imputation, categorical encoding, weighting, tuning and calibration.
9. Create subgroup/uncertainty/fairness evaluation for a regulated triage model without leaking small-group identities.
10. Design monitoring/retraining decision when input drift appears today and labels arrive after 60 days.

## 9. CURATED RESOURCES

1. James, Witten, Hastie, Tibshirani and Taylor, *An Introduction to Statistical Learning*, 2nd ed., Chapters 2–8. First-principles supervised learning, resampling, linear/tree/ensemble explanations.
2. Hastie, Tibshirani and Friedman, *The Elements of Statistical Learning*, 2nd ed., Chapters 2, 3, 4, 7, 9, 10. Mathematical depth on generalization, regularization, trees and boosting.
3. Shalev-Shwartz and Ben-David, *Understanding Machine Learning*, Chapters 2–7. ERM, learnability, bias/complexity and generalization foundations.
4. scikit-learn 1.9 User Guide, *Cross-validation*, *Common pitfalls*, *Metrics and scoring*, *Threshold tuning*, *Calibration*. Current implementation guidance and caveats.
5. Breiman, “Random Forests,” Machine Learning 45 (2001). Canonical bagging/random-feature ensemble.
6. Friedman, “Greedy Function Approximation: A Gradient Boosting Machine,” Annals of Statistics 29 (2001). Gradient boosting foundation.
7. Chen and Guestrin, “XGBoost: A Scalable Tree Boosting System,” KDD 2016. Systems/regularization innovations for production tabular boosting.
8. Guo, Pleiss, Sun and Weinberger, “On Calibration of Modern Neural Networks,” ICML 2017. Temperature scaling and neural miscalibration evidence.
9. Davis and Goadrich, “The Relationship Between Precision-Recall and ROC Curves,” ICML 2006. Correct curve relationships under imbalance.
10. Sculley et al., “Hidden Technical Debt in Machine Learning Systems,” NeurIPS 2015. System-level boundary beyond model score.
11. NIST AI Risk Management Framework 1.0 and Playbook. High-stakes validity, monitoring, transparency and risk governance.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Probability and Statistics:** supplies distributions, estimation, uncertainty and hypothesis reasoning.
2. **Production Python:** supplies exact numeric/data/testing boundaries.
3. **Data Systems:** supplies point-in-time joins, schema and lineage foundations.
4. **FastAPI:** exposes model scores and decision contracts.

### After

1. **ML Lifecycle:** operationalizes datasets, experiments, registry and deployment.
2. **Model Serving and LLMOps:** turns evaluated model into bounded production inference.
3. **Monitoring:** extends SLO/drift/quality with delayed labels.
4. **Regulated Design:** governs fairness, explainability, validation and human oversight.

---ANSWER KEY BELOW---

1. Unit=index discharge, prediction before discharge using information available by cutoff; label unplanned all-cause readmission within 30 days with transfer/death rules and 30-day maturation; action care-management review with capacity/cost; exclude follow-up encounters, readmission indicators, post-discharge claims and future-coded fields; evaluate hospitals/time/groups.
2. Use earlier matured time for train, later for validation, newest fully matured final test; keep member and perhaps provider groups from crossing according to deployment; hold target region/sites entirely for domain test if unseen-region claim. Fit preprocessing/tuning/calibration only train/validation, freeze then test. Report returning-member and unseen-member separately if both operational.
3. N=10,000; positives=500 prevalence 5%. Accuracy (240+9340)/10000=95.8%; precision 240/400=60%; recall 240/500=48%; specificity 9340/9500=98.3158%; F1=2×.6×.48/1.08=53.333%.
4. A appears TP90 FP210 TN8790 FN10, flags300 and violates capacity250; cost 42,000+50,000=₹92,000. B flags130 within capacity; cost 12,000+150,000=₹162,000. If capacity hard, B is feasible among choices despite higher cost; alternatively optimize/select top 250 and quantify cost, or expand capacity if marginal benefit justifies. Matrix tuple order must be stated.
5. Compare 3×3=9: .9 beats all 3; .6 loses .7, beats .5/.2 =2; .5 loses .7, ties .5=.5, beats .2=1.5. Credit 6.5/9=.7222.
6. Brier/log loss reward probability truth, not just side of .5. Moderate .6 positive/.4 negative incur modest penalties; .99 wrong positive/negative creates huge log loss and near-one squared error. Evaluate calibration bins plus proper score; Brier is prevalence-sensitive and log loss especially punishes confidence.
7. Random split leaks member/provider/time identity, while group-CV estimates unseen groups. Audit duplicates/identifiers/post-outcome features; compare group+time/site splits, baseline, memorization ablation and new-group performance. Treat .71 as closer until deployment mix proves returning groups; do not tune to random .94.
8. Outer group/time splits; inside training pipeline fit imputation/missing indicator and encoding (unknown category handling), optional class weights/resampling only fold, boosting tune via inner CV/validation, generate out-of-fold scores for calibrator/threshold, freeze and evaluate untouched temporal/group test. Save split IDs/schema/code/data/model/calibrator/threshold and negative leakage tests.
9. Predeclare clinically/legal groups/intersections and decision metrics including calibration, recall/false positives, workload/outcome; bootstrap independent patient/site units and suppress/aggregate tiny cells; use restricted analysis, no identity in metrics. Investigate label/access bias, compare uncertainty and appeal/human effects. Fairness choice documented with domain/legal stakeholders; no single parity metric is universally achievable.
10. Immediately verify schema/source/missing/freshness/serving parity/version/traffic mix and apply safe guardrails/abstention/manual review if out-of-range. Monitor score/workload and synthetics. Do not retrain on immature labels. When 60-day outcomes mature, evaluate fixed cohorts/time/subgroups, calibration/cost; retrain only through versioned data/validation if evidence and policy trigger, with shadow/canary and rollback.
