import pandas as pd

from simulator import SimulationConfig, simulate_experiment


def test_simulator_generates_expected_columns():
    config = SimulationConfig(n_users=1000, seed=42)

    df = simulate_experiment(config)

    expected_columns = {
        "user_id",
        "day_assigned",
        "platform",
        "group",
        "pre_experiment_activity",
        "converted",
    }

    assert expected_columns.issubset(df.columns)


def test_simulator_generates_correct_number_of_users():
    config = SimulationConfig(n_users=2000, seed=42)

    df = simulate_experiment(config)

    assert len(df) == 2000
    assert df["user_id"].nunique() == 2000


def test_simulator_generates_valid_experiment_groups():
    config = SimulationConfig(n_users=1000, seed=42)

    df = simulate_experiment(config)

    assert set(df["group"].unique()) == {"control", "treatment"}


def test_simulator_generates_binary_conversion_values():
    config = SimulationConfig(n_users=1000, seed=42)

    df = simulate_experiment(config)

    assert set(df["converted"].unique()).issubset({0, 1})


def test_same_seed_produces_identical_data():
    config = SimulationConfig(n_users=1000, seed=42)

    df1 = simulate_experiment(config)
    df2 = simulate_experiment(config)

    pd.testing.assert_frame_equal(df1, df2)


def test_different_seeds_produce_different_data():
    df1 = simulate_experiment(
        SimulationConfig(n_users=1000, seed=42)
    )
    df2 = simulate_experiment(
        SimulationConfig(n_users=1000, seed=100)
    )

    assert not df1.equals(df2)


def test_simulator_generates_valid_platforms():
    config = SimulationConfig(n_users=1000, seed=42)

    df = simulate_experiment(config)

    assert set(df["platform"].unique()).issubset(
        {"iOS", "Android", "Web"}
    )


def test_simulator_assigns_valid_experiment_days():
    config = SimulationConfig(n_users=1000, n_days=14, seed=42)

    df = simulate_experiment(config)

    assert df["day_assigned"].min() >= 0
    assert df["day_assigned"].max() < 14
