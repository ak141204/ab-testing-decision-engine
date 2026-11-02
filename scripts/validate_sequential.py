import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data"))
sys.path.insert(0, str(ROOT / "engine"))

from simulator import SimulationConfig, simulate_experiment
from sequential import run_sequential_test, naive_peeking_test


N_EXPERIMENTS = 1000
N_USERS = 2000
ALPHA = 0.05


def wilson_interval(successes, total):
    z = 1.96
    p = successes / total

    denominator = 1 + z**2 / total

    center = (
        p + z**2 / (2 * total)
    ) / denominator

    margin = (
        z * np.sqrt(
            p * (1 - p) / total
            + z**2 / (4 * total**2)
        ) / denominator
    )

    return center - margin, center + margin


sequential_false_positives = 0
naive_false_positives = 0

print(f"Running {N_EXPERIMENTS} A/A experiments...")

for seed in range(N_EXPERIMENTS):

    config = SimulationConfig(
        n_users=N_USERS,
        true_control_rate=0.10,
        true_lift=0.0,
        n_days=14,
        seed=seed,
    )

    df = simulate_experiment(config)

    sequential_results = run_sequential_test(
        df,
        alpha=ALPHA,
    )

    if any(result.reject_null for result in sequential_results):
        sequential_false_positives += 1

    if naive_peeking_test(df, alpha=ALPHA):
        naive_false_positives += 1

    if (seed + 1) % 100 == 0:
        print(f"Completed {seed + 1}/{N_EXPERIMENTS}")


for name, count in [
    ("Alpha-spending", sequential_false_positives),
    ("Naive daily peeking", naive_false_positives),
]:

    rate = count / N_EXPERIMENTS
    lower, upper = wilson_interval(count, N_EXPERIMENTS)

    print(f"\n{name}")
    print(f"False positives: {count}/{N_EXPERIMENTS}")
    print(f"False-positive rate: {rate:.2%}")
    print(f"95% Wilson interval: [{lower:.2%}, {upper:.2%}]")

print("\nNominal significance level:", f"{ALPHA:.0%}")