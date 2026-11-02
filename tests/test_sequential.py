import pandas as pd
import pytest

from sequential import (
    run_sequential_test,
    naive_peeking_test,
    mspt_ever_rejects,
)


def make_data(n=1000, control_rate=0.10, treatment_rate=0.10):
    control_conversions = int(n * control_rate)
    treatment_conversions = int(n * treatment_rate)

    return pd.DataFrame({
        "group": (
            ["control"] * n + ["treatment"] * n
        ),
        "converted": (
            [1] * control_conversions
            + [0] * (n - control_conversions)
            + [1] * treatment_conversions
            + [0] * (n - treatment_conversions)
        ),
        "day_assigned": (
            [day for day in range(10) for _ in range(n // 10)]
            + [day for day in range(10) for _ in range(n // 10)]
        ),
    })


def test_returns_one_result_per_day():
    results = run_sequential_test(make_data())
    assert len(results) == 10


def test_daily_sample_counts_are_cumulative():
    results = run_sequential_test(make_data())

    assert results[-1].n_control == 1000
    assert results[-1].n_treatment == 1000
    assert results[-1].n_control > results[0].n_control


def test_small_sample_does_not_reject():
    results = run_sequential_test(make_data(n=20))

    assert all(not result.reject_null for result in results)


def test_fisher_p_values_are_between_zero_and_one():
    results = run_sequential_test(
        make_data(n=1000, control_rate=0.10, treatment_rate=0.15)
    )

    for result in results:
        assert 0 <= result.p_value <= 1

def test_strong_effect_can_cross_threshold():
    df = make_data(
        n=1000,
        control_rate=0.10,
        treatment_rate=0.30,
    )

    results = run_sequential_test(df)

    assert any(result.reject_null for result in results)





def test_alpha_spending_is_within_total_alpha():
    alpha = 0.05
    results = run_sequential_test(make_data(), alpha=alpha)

    assert sum(result.alpha_spent for result in results) <= alpha


def test_anytime_p_value_is_between_zero_and_one():
    results = run_sequential_test(make_data())

    assert all(
        0 <= result.anytime_valid_p_value <= 1
        for result in results
    )


def test_invalid_alpha_is_rejected():
    with pytest.raises(ValueError):
        run_sequential_test(make_data(), alpha=0)


def test_missing_required_column_is_rejected():
    df = make_data().drop(columns=["day_assigned"])

    with pytest.raises(ValueError):
        run_sequential_test(df)


def test_helper_matches_sequential_results():
    df = make_data(
        n=1000,
        control_rate=0.10,
        treatment_rate=0.30,
    )

    expected = any(
        result.reject_null
        for result in run_sequential_test(df)
    )

    assert mspt_ever_rejects(df) == expected


def test_naive_peeking_returns_boolean():
    assert isinstance(naive_peeking_test(make_data()), bool)