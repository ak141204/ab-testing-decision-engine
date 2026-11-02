"""
Decision Engine
=================
Combines every module built so far (SRM, sequential testing, CUPED, CATE)
into ONE function that a non-technical stakeholder can actually use:
given an experiment's data, return a single verdict - SHIP, KILL, HOLD,
or NEEDS_MORE_DATA - with the reasoning spelled out.

Why this is the step that makes it "a tool" and not "a stats library":
Nobody wants to run six scripts and interpret six separate outputs
themselves. A PM wants one answer they can act on. This is that answer.

Decision priority order (and why this order, specifically):
1. SRM check FIRST, always. If the traffic split is broken, every
   downstream result is potentially biased - there is no point running
   any other test until the instrumentation bug is fixed. This is a
   hard gate, not a soft warning.
2. Sequential test status - tells us whether it's statistically SAFE to
   stop yet, given that the team may be checking this dashboard daily.
3. CUPED-adjusted effect estimate is preferred over the raw one whenever
   available, since it's strictly lower-variance for the same data.
4. CATE/uplift context is attached as an ADVISORY note, not a gate - it
   informs a ship decision (e.g. "ship, but consider targeting only the
   responsive segment") rather than blocking one.
"""

from dataclasses import dataclass, field
import pandas as pd

from srm import check_srm
from frequentist import two_proportion_ztest
from sequential import run_sequential_test
from cuped import compare_raw_vs_cuped


@dataclass
class Decision:
    verdict: str  # "SHIP" | "KILL" | "HOLD" | "NEEDS_MORE_DATA" | "INVALID_SRM"
    reasoning: list[str] = field(default_factory=list)
    effect_estimate: float | None = None
    confidence_interval: tuple | None = None
    p_value: float | None = None
    srm_check_passed: bool = True
    sequential_safe_to_stop: bool = False


def evaluate_experiment(
    df: pd.DataFrame,
    alpha: float = 0.05,
    min_practical_effect: float = 0.0,
    uplift_context: str | None = None,
    planned_duration_days: int | None = None,
) -> Decision:

    reasoning = []

    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1.")

    if min_practical_effect < 0:
        raise ValueError("min_practical_effect cannot be negative.")

    if planned_duration_days is not None and planned_duration_days <= 0:
        raise ValueError("planned_duration_days must be positive.")

    # --- Gate 1: SRM check ---
    srm_result = check_srm(df)

    if srm_result.srm_detected:
        reasoning.append(
            f"SRM DETECTED: observed split "
            f"{srm_result.observed_split:.2%} vs expected 50% "
            f"(p={srm_result.p_value}). Results are potentially biased."
        )

        return Decision(
            verdict="INVALID_SRM",
            reasoning=reasoning,
            srm_check_passed=False,
        )

    reasoning.append("SRM check passed - traffic allocation is acceptable.")

    # --- Gate 2: Sequential statistical evidence ---
    sequential_safe = False
    reached_planned_duration = False
    sequential_effect = None
    decision_p_value = None

    if "day_assigned" in df.columns:

        seq_results = run_sequential_test(df, alpha=alpha)

        if not seq_results:
            raise ValueError("Sequential testing returned no results.")

        final_result = seq_results[-1]

        # Preserve a rejection reached at ANY earlier monitoring look.
        crossing_results = [
            result for result in seq_results
            if result.reject_null
        ]

        sequential_safe = bool(crossing_results)

        # The adjusted p-value is the running minimum across looks.
        decision_p_value = final_result.anytime_valid_p_value

        # Use the final cumulative observed effect for direction.
        sequential_effect = final_result.observed_lift

        reached_planned_duration = (
            planned_duration_days is not None
            and final_result.day >= planned_duration_days - 1
        )

        if sequential_safe:
            first_crossing = crossing_results[0]

            reasoning.append(
                f"Fisher-based alpha-spending test crossed its "
                f"significance boundary on day {first_crossing.day}. "
                f"Adjusted sequential p-value: {decision_p_value:.6f}."
            )

        elif reached_planned_duration:
            reasoning.append(
                f"No sequential significance was detected, but the "
                f"planned duration of {planned_duration_days} days "
                f"has been reached. Treating the result as inconclusive."
            )

        else:
            reasoning.append(
                f"No sequential significance detected by day "
                f"{final_result.day}. Continue collecting data."
            )

    else:
        reasoning.append(
            "No day-level data provided - sequential testing skipped. "
            "Using the ordinary CUPED analysis instead."
        )

    # --- Effect estimation using CUPED ---
    cuped_result = compare_raw_vs_cuped(df, alpha=alpha)

    effect = cuped_result.cuped_absolute_lift

    reasoning.append(
        f"CUPED-adjusted effect estimate: {effect:.2%}. "
        f"Reported variance reduction: "
        f"{cuped_result.variance_reduction_pct:.1f}%."
    )

    # --- Advisory uplift context ---
    if uplift_context:
        reasoning.append(
            f"Uplift model context (advisory): {uplift_context}"
        )

    # --- Final decision ---
    if "day_assigned" in df.columns:

        if not sequential_safe and not reached_planned_duration:
            verdict = "NEEDS_MORE_DATA"

        elif not sequential_safe:
            verdict = "HOLD"
            reasoning.append(
                "The experiment reached its planned duration without "
                "sequential statistical significance."
            )

        elif sequential_effect < 0:
            verdict = "KILL"
            reasoning.append(
                "The sequential test detected a significant negative effect."
            )

        elif abs(effect) < min_practical_effect:
            verdict = "HOLD"
            reasoning.append(
                "The estimated effect is below the minimum practical "
                "effect threshold."
            )

        else:
            verdict = "SHIP"
            reasoning.append(
                "The sequential test detected a significant positive effect."
            )

    else:
        # Fixed-horizon fallback when day-level data is unavailable.
        decision_p_value = cuped_result.p_value_cuped

        if decision_p_value >= alpha:
            verdict = "HOLD"
            reasoning.append(
                "The CUPED-adjusted result is not statistically significant."
            )

        elif effect < 0:
            verdict = "KILL"
            reasoning.append(
                "The CUPED-adjusted effect is significantly negative."
            )

        elif abs(effect) < min_practical_effect:
            verdict = "HOLD"
            reasoning.append(
                "The effect is below the minimum practical threshold."
            )

        else:
            verdict = "SHIP"
            reasoning.append(
                "The CUPED-adjusted effect is significantly positive."
            )

    return Decision(
        verdict=verdict,
        reasoning=reasoning,
        effect_estimate=effect,
        p_value=decision_p_value,
        srm_check_passed=True,
        sequential_safe_to_stop=sequential_safe,
    )


def print_decision(decision: Decision):
    print(f"\n{'=' * 55}")
    print(f"VERDICT: {decision.verdict}")
    print(f"{'=' * 55}")
    for i, line in enumerate(decision.reasoning, 1):
        print(f"{i}. {line}")
    if decision.effect_estimate is not None:
        print(f"\nEffect estimate: {decision.effect_estimate:.2%}  |  p-value: {decision.p_value}")


if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "data"))
    from simulator import simulate_experiment, SimulationConfig

    print("### SCENARIO 1: Clean experiment, clear positive effect ###")
    cfg1 = SimulationConfig(n_users=50_000, true_control_rate=0.10, true_lift=0.02, seed=42)
    df1 = simulate_experiment(cfg1)
    decision1 = evaluate_experiment(df1, planned_duration_days=14,
                                     uplift_context="44% of users show positive predicted uplift (Step 7 model)")
    print_decision(decision1)

    print("\n\n### SCENARIO 2: Broken traffic split (SRM bug on iOS) ###")
    cfg2 = SimulationConfig(n_users=50_000, biased_platform="iOS", segment_bias_strength=0.08, seed=1)
    df2 = simulate_experiment(cfg2)
    decision2 = evaluate_experiment(df2, planned_duration_days=14)
    print_decision(decision2)

    print("\n\n### SCENARIO 3: No real effect (null), experiment has run its full course ###")
    cfg3 = SimulationConfig(n_users=50_000, true_control_rate=0.10, true_lift=0.0, seed=99)
    df3 = simulate_experiment(cfg3)
    decision3 = evaluate_experiment(df3, planned_duration_days=14)
    print_decision(decision3)

    print("\n\n### SCENARIO 4: Early days, effect real but not enough data yet ###")
    cfg4 = SimulationConfig(n_users=3_000, true_control_rate=0.10, true_lift=0.02, n_days=14, seed=7)
    df4 = simulate_experiment(cfg4)
    # only look at the first 2 days worth of data to simulate an early check
    df4_early = df4[df4["day_assigned"] <= 1]
    decision4 = evaluate_experiment(df4_early, planned_duration_days=14)
    print_decision(decision4)
