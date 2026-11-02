# Engine Module Reference

## `engine/decision_engine.py`

### `evaluate_experiment(df, alpha=0.05, min_practical_effect=0.0, uplift_context=None, planned_duration_days=None)`

Main orchestration function. Returns a `Decision` dataclass.

`Decision` fields:

- `verdict`
- `reasoning`
- `effect_estimate`
- `confidence_interval`
- `p_value`
- `srm_check_passed`
- `sequential_safe_to_stop`

The inspected return paths populate the effect estimate and p-value for the non-SRM path, but do not currently populate `confidence_interval`.

### `print_decision(decision)`

Prints the verdict and reasoning.

## `engine/srm.py`

- `check_srm(df, expected_split=0.5)`: overall allocation check.
- `diagnose_srm_by_segment(df, segment_columns, expected_split=0.5)`: independent checks by segment value.
- `full_srm_report(df, segment_columns, expected_split=0.5)`: overall check and conditional segment diagnosis.

Result dataclasses: `SRMResult`, `SegmentDiagnosis`.

## `engine/sequential.py`

- `run_sequential_test(df, alpha=0.05, tau=0.05)`: returns daily `SequentialTestResult` entries.
- `naive_peeking_test(df, alpha=0.05)`: returns whether a conventional daily test ever crosses alpha.
- `mspt_ever_rejects(df, alpha=0.05, tau=0.05)`: returns whether any sequential result crosses the boundary.

The helper `_daily_mixture_llr` is internal.

## `engine/cuped.py`

- `apply_cuped(df, outcome_col="converted", covariate_col="pre_experiment_activity")`: returns an adjusted dataframe and theta.
- `compare_raw_vs_cuped(df, alpha=0.05)`: returns a `CUPEDResult`.

## `engine/cate.py`

- `TLearnerUplift(**model_kwargs)`: two-model estimator.
- `.fit(X, treatment, y)`: trains arm-specific models.
- `.predict_uplift(X)`: returns treatment-model probability minus control-model probability.
- `evaluate_uplift_model(X, treatment, y, test_size=0.3, random_state=42)`: returns fitted model, summary result, and test-set dataframe with uplift scores.

## `engine/frequentist.py`

- `two_proportion_ztest(df, alpha=0.05)`: two-proportion test and confidence interval.
- `chi_square_test(df, alpha=0.05)`: group-by-outcome chi-square test.

## `engine/power_analysis.py`

- `required_sample_size(baseline_rate, mde_absolute, alpha=0.05, power=0.80, daily_traffic=None)`: sample-size estimate.
- `achieved_power(baseline_rate, mde_absolute, n_per_group, alpha=0.05)`: achieved-power approximation.

## Data contracts

The decision engine docstring expects `group`, `converted`, and `pre_experiment_activity`; `day_assigned` is needed for its sequential gate. The CATE evaluator accepts feature, treatment, and outcome objects separately. Segment diagnosis accepts caller-selected segment column names.

Exact API request/response schemas are not included here; inspect `api/app.py` before publishing API reference details.
