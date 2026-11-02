import numpy as np
import pandas as pd

from cuped import apply_cuped, compare_raw_vs_cuped


def make_experiment(n=10000, seed=42):
    rng = np.random.default_rng(seed)

    # Equal covariate distributions in both groups
    x = rng.normal(0, 1, size=2 * n)

    groups = np.array(
        ["control"] * n + ["treatment"] * n
    )

    # Conversion probability depends on pre-experiment activity
    probabilities = np.clip(
        0.10 + 0.04 * x
        + np.where(groups == "treatment", 0.02, 0),
        0.01,
        0.50,
    )

    converted = rng.binomial(1, probabilities)

    return pd.DataFrame({
        "group": groups,
        "converted": converted,
        "pre_experiment_activity": x,
    })


def test_apply_cuped_creates_adjusted_column():
    df = make_experiment()

    adjusted_df, theta = apply_cuped(df)

    assert "cuped_adjusted" in adjusted_df.columns
    assert np.isfinite(theta)


def test_apply_cuped_does_not_modify_original_dataframe():
    df = make_experiment()
    original = df.copy(deep=True)

    adjusted_df, theta = apply_cuped(df)

    pd.testing.assert_frame_equal(df, original)
    assert "cuped_adjusted" not in df.columns


def test_cuped_adjustment_uses_shared_coefficient():
    df = make_experiment()

    adjusted_df, theta = apply_cuped(df)

    expected = (
        df["converted"].to_numpy()
        - theta * (
            df["pre_experiment_activity"].to_numpy()
            - df["pre_experiment_activity"].mean()
        )
    )

    np.testing.assert_allclose(
        adjusted_df["cuped_adjusted"].to_numpy(),
        expected,
    )


def test_constant_covariate_produces_zero_theta():
    df = make_experiment()
    df["pre_experiment_activity"] = 10.0

    adjusted_df, theta = apply_cuped(df)

    assert theta == 0.0

    np.testing.assert_allclose(
        adjusted_df["cuped_adjusted"],
        df["converted"],
    )


def test_compare_raw_vs_cuped_returns_correct_sample_sizes():
    df = make_experiment(n=5000)

    result = compare_raw_vs_cuped(df)

    assert result.control_n == 5000
    assert result.treatment_n == 5000


def test_compare_raw_vs_cuped_returns_valid_statistics():
    df = make_experiment()

    result = compare_raw_vs_cuped(df)

    assert np.isfinite(result.theta)
    assert result.raw_ci_width > 0
    assert result.cuped_ci_width > 0
    assert 0 <= result.p_value_raw <= 1
    assert 0 <= result.p_value_cuped <= 1
    assert np.isfinite(result.variance_reduction_pct)


def test_predictive_covariate_reduces_variance():
    df = make_experiment(n=20000)

    result = compare_raw_vs_cuped(df)

    assert result.variance_reduction_pct > 0


def test_cuped_and_raw_effect_estimates_are_reasonably_close():
    df = make_experiment(n=20000)

    result = compare_raw_vs_cuped(df)

    assert abs(
        result.raw_absolute_lift - result.cuped_absolute_lift
    ) < 0.02
