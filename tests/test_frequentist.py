import math
import pandas as pd

from frequentist import two_proportion_ztest, chi_square_test


def make_experiment(control_conversions, treatment_conversions, n=1000):
    return pd.DataFrame({
        "group": (
            ["control"] * n
            + ["treatment"] * n
        ),
        "converted": (
            [1] * control_conversions
            + [0] * (n - control_conversions)
            + [1] * treatment_conversions
            + [0] * (n - treatment_conversions)
        )
    })


def test_equal_conversion_rates_are_not_significant():
    df = make_experiment(100, 100)

    result = two_proportion_ztest(df)

    assert result.control_rate == 0.1
    assert result.treatment_rate == 0.1
    assert result.absolute_lift == 0.0
    assert result.significant == False


def test_higher_treatment_conversion_has_positive_lift():
    df = make_experiment(100, 200)

    result = two_proportion_ztest(df)

    assert result.absolute_lift > 0
    assert result.relative_lift > 0
    assert result.treatment_rate > result.control_rate


def test_lower_treatment_conversion_has_negative_lift():
    df = make_experiment(200, 100)

    result = two_proportion_ztest(df)

    assert result.absolute_lift < 0
    assert result.relative_lift < 0
    assert result.treatment_rate < result.control_rate


def test_strong_effect_is_statistically_significant():
    df = make_experiment(100, 250)

    result = two_proportion_ztest(df, alpha=0.05)

    assert result.significant == True
    assert result.p_value < 0.05


def test_confidence_interval_contains_observed_lift():
    df = make_experiment(100, 200)

    result = two_proportion_ztest(df)

    assert result.ci_lower < result.absolute_lift
    assert result.ci_upper > result.absolute_lift


def test_zero_control_rate_returns_nan_relative_lift():
    df = make_experiment(0, 100)

    result = two_proportion_ztest(df)

    assert math.isnan(result.relative_lift)
    assert result.absolute_lift > 0


def test_chi_square_returns_expected_fields():
    df = make_experiment(100, 250)

    result = chi_square_test(df)

    assert "chi2_statistic" in result
    assert "p_value" in result
    assert "degrees_of_freedom" in result
    assert "significant" in result
    assert "contingency_table" in result


def test_chi_square_detects_strong_conversion_difference():
    df = make_experiment(100, 250)

    result = chi_square_test(df)

    assert result["significant"] == True
    assert result["p_value"] < 0.05
    assert result["degrees_of_freedom"] == 1
