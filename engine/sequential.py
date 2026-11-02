"""
Sequential Testing using Fisher's Exact Test and Alpha Spending.

At each scheduled monitoring look, Fisher's exact test is applied
to cumulative binary conversion outcomes.

Alpha spending:
    alpha_t = alpha / (t * (t + 1))

The total significance budget across all looks is bounded by alpha.

This is an alpha-spending procedure, NOT an mSPRT.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact


@dataclass
class SequentialTestResult:
    day: int
    n_control: int
    n_treatment: int
    observed_lift: float
    p_value: float
    alpha_spent: float
    anytime_valid_p_value: float
    reject_null: bool


def _validate_data(df):
    required = {"day_assigned", "group", "converted"}

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if df.empty:
        raise ValueError("Experiment data cannot be empty.")

    if df[list(required)].isnull().any().any():
        raise ValueError("Required columns cannot contain missing values.")

    if set(df["group"].unique()) != {"control", "treatment"}:
        raise ValueError("Both control and treatment groups are required.")

    if not df["converted"].isin([0, 1]).all():
        raise ValueError("Conversion outcomes must be binary (0 or 1).")

    days = pd.to_numeric(df["day_assigned"], errors="coerce")

    if days.isnull().any() or not np.isfinite(days).all():
        raise ValueError("Assignment days must be finite numeric values.")

    if not np.equal(days, np.floor(days)).all():
        raise ValueError("Assignment days must be integers.")


def run_sequential_test(df, alpha=0.05):
    """
    Perform cumulative daily Fisher exact tests with alpha spending.

    Assumptions:
      - Independent users.
      - One binary outcome per user.
      - Randomized treatment assignment.
      - A fixed, prespecified monitoring schedule.
    """

    if not 0 < alpha < 1:
        raise ValueError("alpha must be strictly between 0 and 1.")

    _validate_data(df)

    data = df.copy()
    data["day_assigned"] = data["day_assigned"].astype(int)

    first_day = int(data["day_assigned"].min())
    last_day = int(data["day_assigned"].max())

    results = []
    best_adjusted_p = 1.0

    for look_number, day in enumerate(
        range(first_day, last_day + 1),
        start=1,
    ):
        alpha_look = alpha / (
            look_number * (look_number + 1)
        )

        current = data[data["day_assigned"] <= day]

        control = current[
            current["group"] == "control"
        ]["converted"]

        treatment = current[
            current["group"] == "treatment"
        ]["converted"]

        n_control = len(control)
        n_treatment = len(treatment)

        if n_control == 0 or n_treatment == 0:
            continue

        control_converted = int(control.sum())
        treatment_converted = int(treatment.sum())

        table = [
            [
                treatment_converted,
                n_treatment - treatment_converted,
            ],
            [
                control_converted,
                n_control - control_converted,
            ],
        ]

        _, p_value = fisher_exact(
            table,
            alternative="two-sided",
        )

        lift = float(
            treatment.mean() - control.mean()
        )

        weight = 1 / (
            look_number * (look_number + 1)
        )

        adjusted_p = min(
            1.0,
            p_value / weight,
        )

        best_adjusted_p = min(
            best_adjusted_p,
            adjusted_p,
        )

        results.append(
            SequentialTestResult(
                day=day,
                n_control=n_control,
                n_treatment=n_treatment,
                observed_lift=round(lift, 6),
                p_value=float(p_value),
                alpha_spent=alpha_look,
                anytime_valid_p_value=best_adjusted_p,
                reject_null=bool(p_value <= alpha_look),
            )
        )

    return results


def naive_peeking_test(df, alpha=0.05):
    """
    Comparison method: repeatedly run ordinary two-sided z-tests
    without correcting for repeated monitoring.
    """

    from scipy import stats

    if not 0 < alpha < 1:
        raise ValueError("alpha must be strictly between 0 and 1.")

    _validate_data(df)

    for day in sorted(df["day_assigned"].unique()):
        current = df[df["day_assigned"] <= day]

        control = current[
            current["group"] == "control"
        ]["converted"]

        treatment = current[
            current["group"] == "treatment"
        ]["converted"]

        n1, n2 = len(control), len(treatment)

        if n1 < 30 or n2 < 30:
            continue

        pooled = (
            control.sum() + treatment.sum()
        ) / (n1 + n2)

        se = np.sqrt(
            pooled * (1 - pooled) * (1 / n1 + 1 / n2)
        )

        if se == 0:
            continue

        z = (treatment.mean() - control.mean()) / se
        p_value = 2 * stats.norm.sf(abs(z))

        if p_value < alpha:
            return True

    return False


def mspt_ever_rejects(df, alpha=0.05):
    """
    Legacy compatibility helper.

    Uses Fisher-based alpha spending, not mSPRT.
    """

    return any(
        result.reject_null
        for result in run_sequential_test(df, alpha=alpha)
    )