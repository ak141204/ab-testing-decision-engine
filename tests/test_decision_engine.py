from types import SimpleNamespace

import pandas as pd

import decision_engine
from decision_engine import evaluate_experiment


def make_experiment(control_n=5000, treatment_n=5000):
    return pd.DataFrame({
        "group": (
            ["control"] * control_n
            + ["treatment"] * treatment_n
        ),
        "converted": (
            [1] * 500 + [0] * (control_n - 500)
            + [1] * 600 + [0] * (treatment_n - 600)
        ),
        "pre_experiment_activity": [10.0] * (control_n + treatment_n),
    })


def mock_cuped(monkeypatch, effect, p_value):
    monkeypatch.setattr(
        decision_engine,
        "compare_raw_vs_cuped",
        lambda df, alpha=0.05: SimpleNamespace(
            cuped_absolute_lift=effect,
            p_value_cuped=p_value,
            variance_reduction_pct=10.0,
        ),
    )


def mock_sequential(monkeypatch, day, reject_null):
    monkeypatch.setattr(
        decision_engine,
        "run_sequential_test",
        lambda df, alpha=0.05: [
            SimpleNamespace(
                day=day,
                reject_null=reject_null,
                anytime_valid_p_value=0.001 if reject_null else 0.20,
                observed_lift=0.02,
            )
        ],
    )

def test_srm_failure_blocks_decision(monkeypatch):
    df = make_experiment(3000, 7000)

    # SRM must return before CUPED or sequential analysis.
    def unexpected_cuped(*args, **kwargs):
        raise AssertionError("CUPED should not run after SRM failure")

    monkeypatch.setattr(
        decision_engine,
        "compare_raw_vs_cuped",
        unexpected_cuped,
    )

    result = evaluate_experiment(df)

    assert result.verdict == "INVALID_SRM"
    assert result.srm_check_passed == False


def test_positive_significant_effect_produces_ship(monkeypatch):
    df = make_experiment()
    mock_cuped(monkeypatch, effect=0.02, p_value=0.001)

    result = evaluate_experiment(df)

    assert result.verdict == "SHIP"
    assert result.effect_estimate == 0.02


def test_negative_significant_effect_produces_kill(monkeypatch):
    df = make_experiment()
    mock_cuped(monkeypatch, effect=-0.02, p_value=0.001)

    result = evaluate_experiment(df)

    assert result.verdict == "KILL"


def test_insignificant_effect_produces_hold(monkeypatch):
    df = make_experiment()
    mock_cuped(monkeypatch, effect=0.02, p_value=0.20)

    result = evaluate_experiment(df)

    assert result.verdict == "HOLD"


def test_small_significant_effect_respects_practical_threshold(monkeypatch):
    df = make_experiment()
    mock_cuped(monkeypatch, effect=0.005, p_value=0.001)

    result = evaluate_experiment(
        df,
        min_practical_effect=0.01,
    )

    assert result.verdict == "HOLD"


def test_early_sequential_result_needs_more_data(monkeypatch):
    df = make_experiment()
    df["day_assigned"] = 1

    mock_sequential(monkeypatch, day=1, reject_null=False)
    mock_cuped(monkeypatch, effect=0.02, p_value=0.001)

    result = evaluate_experiment(
        df,
        planned_duration_days=14,
    )

    assert result.verdict == "NEEDS_MORE_DATA"
    assert result.sequential_safe_to_stop == False


def test_reached_duration_with_insignificant_result_produces_hold(monkeypatch):
    df = make_experiment()
    df["day_assigned"] = 13

    mock_sequential(monkeypatch, day=13, reject_null=False)
    mock_cuped(monkeypatch, effect=0.01, p_value=0.20)

    result = evaluate_experiment(
        df,
        planned_duration_days=14,
    )

    assert result.verdict == "HOLD"


def test_sequential_significance_allows_ship(monkeypatch):
    df = make_experiment()
    df["day_assigned"] = 5

    mock_sequential(monkeypatch, day=5, reject_null=True)
    mock_cuped(monkeypatch, effect=0.02, p_value=0.001)

    result = evaluate_experiment(df)

    assert result.verdict == "SHIP"
    assert result.sequential_safe_to_stop == True


def test_uplift_context_is_advisory(monkeypatch):
    df = make_experiment()
    mock_cuped(monkeypatch, effect=0.02, p_value=0.001)

    result = evaluate_experiment(
        df,
        uplift_context="Positive uplift predicted for a user segment",
    )

    assert result.verdict == "SHIP"
    assert any(
        "Positive uplift predicted" in line
        for line in result.reasoning
    )


def test_sequential_gate_is_skipped_without_day_column(monkeypatch):
    df = make_experiment()
    mock_cuped(monkeypatch, effect=0.02, p_value=0.001)

    def unexpected_sequential(*args, **kwargs):
        raise AssertionError("Sequential test should be skipped")

    monkeypatch.setattr(
        decision_engine,
        "run_sequential_test",
        unexpected_sequential,
    )

    result = evaluate_experiment(df)

    assert result.verdict == "SHIP"
    assert result.sequential_safe_to_stop == False
    assert any(
    "sequential testing skipped" in line.lower()
    for line in result.reasoning
)
