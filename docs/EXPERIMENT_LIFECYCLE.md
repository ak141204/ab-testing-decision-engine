# Experiment Lifecycle

## Purpose

This document describes how the current application moves from user input to an A/B testing decision.

## End-to-end flow

1. A user opens `frontend/dashboard.html`.
2. The user enters experiment settings and selects **Run experiment**.
3. JavaScript builds a JSON payload.
4. The dashboard sends a `POST` request to `/simulate-and-analyze`.
5. FastAPI validates the request against the `ExperimentRequest` model.
6. The API creates a `SimulationConfig`.
7. `simulate_experiment()` generates a synthetic user-level DataFrame.
8. `evaluate_experiment()` evaluates the generated data.
9. FastAPI serializes selected decision fields into `DecisionResponse`.
10. The dashboard renders the verdict, effect estimate, p-value, reasoning, SRM status, and sequential status.

## Simulator output

The simulator creates one row per user. Its DataFrame includes:

| Column | Description |
|---|---|
| `user_id` | Generated user identifier |
| `day_assigned` | Randomly assigned experiment day |
| `platform` | iOS, Android, or Web |
| `group` | `control` or `treatment` |
| `pre_experiment_activity` | Pre-experiment covariate used by CUPED |
| `converted` | Binary conversion outcome (0 or 1) |

## Assignment and injected bias

The simulator first assigns platforms using probabilities of 35% iOS, 35% Android, and 30% Web. It then assigns users to control or treatment within each platform.

The treatment assignment probability is based on `traffic_split`, `srm_bias`, and (for the selected platform) `segment_bias_strength`, clipped to the interval 0.01 to 0.99.

This permits simulation of global assignment imbalance and platform-specific assignment imbalance.

## Outcome generation

The simulator generates a pre-experiment activity covariate, computes conversion propensities using a logistic expression, applies a treatment bump, rescales probabilities using the control group, and samples binary conversion outcomes.

The `true_lift` parameter is used to construct the treatment bump. The resulting observed treatment rate is stochastic; it is not guaranteed to equal the configured baseline plus lift exactly in every generated dataset.

The `covariate_correlation` setting is a coefficient in the logit expression. It should not be interpreted as a guarantee of a particular empirical correlation coefficient.

## Decision pipeline

The decision engine's inspected implementation follows this broad order:

1. Sample Ratio Mismatch (SRM) check.
2. Sequential test when `day_assigned` is available.
3. Raw versus CUPED-adjusted comparison.
4. Verdict logic using statistical significance, effect direction, practical-effect threshold, and sequential/duration gates.

The exact behavior and assumptions are documented in `ENGINE_REFERENCE.md` and `STATISTICAL_METHODOLOGY.md`.

## Dashboard output

The current dashboard displays:

- Verdict
- Effect estimate
- p-value
- Reasoning messages
- SRM pass/fail status
- Sequential stopping status

The current API response does not include a confidence interval, so the dashboard cannot display one yet.

## Reproducibility

If a numeric `seed` is provided, the simulator initializes NumPy's random generator with that seed. This supports repeatable generated datasets for the same configuration and software environment.

## Important distinction

The current application is a self-contained simulator-backed demonstration. It does not ingest live assignment logs, production conversion events, or an existing experiment dataset through the API.
