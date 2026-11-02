from power_analysis import required_sample_size, achieved_power


def test_required_sample_size_returns_positive_values():
    result = required_sample_size(0.10, 0.02)

    assert result.required_n_per_group > 0
    assert result.required_n_total > 0


def test_total_sample_size_is_twice_per_group():
    result = required_sample_size(0.10, 0.02)

    assert result.required_n_total == 2 * result.required_n_per_group


def test_smaller_mde_requires_more_users():
    small_mde = required_sample_size(0.10, 0.01)
    large_mde = required_sample_size(0.10, 0.03)

    assert small_mde.required_n_total > large_mde.required_n_total


def test_higher_power_requires_more_users():
    normal_power = required_sample_size(0.10, 0.02, power=0.80)
    high_power = required_sample_size(0.10, 0.02, power=0.90)

    assert high_power.required_n_total > normal_power.required_n_total


def test_stricter_alpha_requires_more_users():
    normal_alpha = required_sample_size(0.10, 0.02, alpha=0.05)
    strict_alpha = required_sample_size(0.10, 0.02, alpha=0.01)

    assert strict_alpha.required_n_total > normal_alpha.required_n_total


def test_daily_traffic_calculates_estimated_days():
    result = required_sample_size(
        0.10,
        0.02,
        daily_traffic=5000,
    )

    assert result.estimated_days is not None
    assert result.estimated_days > 0


def test_no_daily_traffic_returns_none_for_days():
    result = required_sample_size(0.10, 0.02)

    assert result.estimated_days is None


def test_achieved_power_is_between_zero_and_one():
    power = achieved_power(
        baseline_rate=0.10,
        mde_absolute=0.02,
        n_per_group=5000,
    )

    assert 0 <= power <= 1


def test_larger_sample_size_increases_achieved_power():
    low_power = achieved_power(0.10, 0.02, 1000)
    high_power = achieved_power(0.10, 0.02, 10000)

    assert high_power > low_power


def test_calculated_sample_size_gives_approximately_target_power():
    result = required_sample_size(
        baseline_rate=0.10,
        mde_absolute=0.02,
        alpha=0.05,
        power=0.80,
    )

    actual_power = achieved_power(
        baseline_rate=0.10,
        mde_absolute=0.02,
        n_per_group=result.required_n_per_group,
        alpha=0.05,
    )

    assert 0.75 <= actual_power <= 0.85
