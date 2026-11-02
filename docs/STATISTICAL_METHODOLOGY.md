# Statistical Methodology

This document distinguishes the methods present in the inspected source from claims that still require independent validation.

## 1. Sample Ratio Mismatch (SRM)

**Implementation:** `engine/srm.py`

The module counts control and treatment observations and applies SciPy's chi-square goodness-of-fit test against an expected allocation. The default expected treatment share is `0.5`; the module-level `SRM_ALPHA` is `0.001`.

If the overall check detects SRM, `full_srm_report` can run checks for each value in caller-supplied segment columns and sort the diagnoses by ascending p-value.

Important qualifications:

- The decision engine currently calls `check_srm(df)` with its default 50/50 allocation.
- Segment diagnostics are available as a separate function; they are not automatically attached by `evaluate_experiment`.
- Multiple segment checks create a multiple-testing issue. The current inspected implementation does not apply a multiplicity correction.
- Validate non-empty groups, missing labels, expected split bounds, and small expected counts before production use.

## 2. Frequentist two-proportion testing

**Implementation:** `engine/frequentist.py`

The module calculates control and treatment conversion rates, absolute lift, relative lift, a pooled standard error for the null test statistic, a two-sided normal-approximation p-value, and an unpooled standard-error confidence interval.

It also provides a chi-square test of independence for the group-by-conversion contingency table.

The code comments identify the two-proportion z-test and 2x2 chi-square test as mathematically equivalent under the usual conditions. The implementation should be tested for empty groups, zero baseline conversion, degenerate variance, missing values, and small samples.

## 3. Sequential testing

**Implementation:** `engine/sequential.py`

The module computes a daily mixture log-likelihood-ratio-like statistic using a Gaussian mixture parameterized by `tau`. It compares the statistic to `log(1 / alpha)` and returns one result per observed day. It also includes a naive daily-peeking baseline that repeatedly runs a conventional two-proportion z-test.

The code describes this as mSPRT / always-valid testing. That guarantee must not be treated as established solely from the function name or comments. Before claiming formal always-valid inference, independently verify the likelihood construction, assumptions, boundary, handling of time-varying allocation and outcomes, and calibration across null and alternative simulations. Report Monte Carlo uncertainty and simulation configuration with any false-positive-rate result.

## 4. CUPED

**Implementation:** `engine/cuped.py`

The module estimates:

\[
\theta = \frac{\operatorname{Cov}(Y,X)}{\operatorname{Var}(X)}
\]

and creates:

\[
Y_{\text{adjusted}} = Y - \theta(X-\bar X)
\]

It estimates one shared coefficient using the combined dataset, then compares raw and adjusted outcomes between groups. The result includes lift, confidence-interval width, p-values, and a variance-reduction percentage inferred from the squared ratio of interval widths.

Important qualifications:

- The covariate must be measured before treatment assignment.
- The inspected function uses `np.cov` for covariance and `np.var` for variance; their default degrees-of-freedom conventions differ slightly.
- The comparison uses a normal critical value and normal-tail p-value on adjusted outcomes. Validate inference for binary outcomes and the intended experimental design.
- Guard against empty groups, zero variance, missing values, and invalid alpha.
- Do not claim that every adjusted interval is guaranteed to be narrower.

## 5. CATE / uplift modelling

**Implementation:** `engine/cate.py`

The code implements a T-learner with two `GradientBoostingClassifier` models:

- A control model trained only on control observations.
- A treatment model trained only on treatment observations.

For each row, predicted uplift is:

\[
\widehat{\tau}(x)=\widehat{P}(Y=1\mid X=x,T=1)-\widehat{P}(Y=1\mid X=x,T=0)
\]

The evaluator splits the data with treatment-stratified train/test splitting, reports separate model AUC values, computes predicted uplift on the test set, and calculates a simplified top-20%-versus-bottom-20% observed-lift proxy.

Important qualifications:

- AUC evaluates outcome discrimination within each arm; it does not directly measure CATE accuracy or uplift ranking quality.
- The `qini_like_score` is explicitly a simplified proxy, not a full Qini curve.
- Causal interpretation depends on the data design and assumptions; the code's use of a randomized Criteo dataset is relevant context, but the evaluator itself does not prove those assumptions for arbitrary input.
- The decision engine accepts an optional text `uplift_context`; it does not call or fit the CATE model itself.

## 6. Sample size and power

**Implementation:** `engine/power_analysis.py`

The module uses a normal-approximation formula for a two-sided two-proportion comparison. Inputs include baseline rate, absolute minimum detectable effect, alpha, target power, and optional daily traffic. It returns required sample size per group and total sample size. `achieved_power` estimates power for a supplied sample size.

Important qualifications:

- The current formula assumes a two-group comparison and equal allocation.
- Validate baseline rate, MDE, alpha, power, and traffic inputs.
- The duration estimate uses total required sample size divided by `daily_traffic`; users must interpret `daily_traffic` as total eligible experiment traffic per day under the assumed allocation.
- Validate the achieved-power approximation against a trusted statistical reference across edge cases.

## General interpretation

Statistical significance is not equivalent to business value or causal certainty. The decision output should be interpreted alongside experiment design, data quality, guardrail metrics, practical effect thresholds, and domain-specific risks.
