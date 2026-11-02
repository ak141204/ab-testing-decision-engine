import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data"))
sys.path.insert(0, str(ROOT / "engine"))

from simulator import SimulationConfig, simulate_experiment
from sequential import run_sequential_test

N_EXPERIMENTS = 200
N_USERS = 20000
ALPHA = 0.05

detections = 0

print("Running positive-effect experiments...")

for seed in range(N_EXPERIMENTS):
    config = SimulationConfig(
        n_users=N_USERS,
        true_control_rate=0.10,
        true_lift=0.02,
        n_days=14,
        seed=seed + 10000,
    )

    df = simulate_experiment(config)

    results = run_sequential_test(df, alpha=ALPHA)

    if any(result.reject_null for result in results):
        detections += 1

    if (seed + 1) % 20 == 0:
        print(f"Completed {seed + 1}/{N_EXPERIMENTS}")

power = detections / N_EXPERIMENTS

print("\n=== STATISTICAL POWER RESULTS ===")
print(f"Experiments: {N_EXPERIMENTS}")
print(f"Detected genuine effects: {detections}")
print(f"Estimated statistical power: {power:.2%}")
print("Target power: 80%")