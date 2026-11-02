# A/B Testing Decision Engine — Project Overview

## Purpose

The A/B Testing Decision Engine is a Python experimentation toolkit that combines statistical checks and treatment-effect analysis into an experiment-level recommendation. Its central goal is to help teams assess whether an experiment's traffic allocation is trustworthy, whether there is enough sequential evidence to conclude, and whether the observed effect is practically meaningful.

The current decision engine can return `SHIP`, `KILL`, `HOLD`, `NEEDS_MORE_DATA`, or `INVALID_SRM`.

## Problems addressed

1. **Sample Ratio Mismatch (SRM):** detects deviations between expected and observed control/treatment allocation and can inspect available segments.
2. **Repeated peeking:** includes a sequential-testing implementation intended for monitoring data over time.
3. **Noisy effect estimates:** applies CUPED-style adjustment using a pre-experiment covariate.
4. **Heterogeneous effects:** trains separate treatment and control outcome models to estimate user-level predicted uplift.
5. **Underpowered experiments:** estimates sample size and achieved power for two-proportion comparisons.

## Current repository components

| Path | Responsibility |
|---|---|
| `engine/decision_engine.py` | Combines checks and produces an experiment-level verdict |
| `engine/srm.py` | Overall and segment-level SRM checks |
| `engine/sequential.py` | Day-by-day mixture likelihood-ratio calculation and naive-peeking comparison |
| `engine/cuped.py` | Pre-experiment covariate adjustment and raw-versus-adjusted comparison |
| `engine/cate.py` | T-learner uplift model |
| `engine/frequentist.py` | Two-proportion z-test and chi-square test |
| `engine/power_analysis.py` | Sample-size and achieved-power approximations |
| `data/simulator.py` | Synthetic experiment data generation (inspect source for exact schema/configuration) |
| `api/app.py` | FastAPI application |
| `frontend/dashboard.html` | Browser dashboard |
| `notebooks/methodology_validation.ipynb` | Methodology validation notebook and associated figures |

## Main workflow

1. Prepare experiment data with the expected schema.
2. Check allocation integrity with SRM.
3. If `day_assigned` is available, calculate sequential results over observed days.
4. Calculate raw and CUPED-adjusted effect estimates.
5. Optionally attach externally generated CATE/uplift context.
6. Apply the decision rules and return a structured `Decision`.

## Expected decision-engine input

The `evaluate_experiment` docstring specifies these columns:

- `group`: values `control` and `treatment`
- `converted`: binary outcome used by the statistical modules
- `pre_experiment_activity`: pre-experiment covariate used by CUPED
- `day_assigned`: day index used for sequential monitoring (optional for that gate)

The SRM module can also inspect segment columns such as `platform` when called through its segment-diagnosis functions. The decision-engine entry point currently calls the overall SRM check; it does not itself pass segment columns to the diagnostic function.

## Decision outputs

| Verdict | Meaning in current implementation |
|---|---|
| `INVALID_SRM` | SRM was detected; the function returns early |
| `NEEDS_MORE_DATA` | Day-level data exists, the sequential boundary has not been crossed, and planned duration has not been reached |
| `HOLD` | No statistically significant CUPED-adjusted effect, or significant effect is below the configured practical threshold |
| `KILL` | Significant negative CUPED-adjusted effect |
| `SHIP` | Significant positive effect meeting the configured practical threshold |

These are software decision rules, not a substitute for product, safety, legal, or business review.

## Scope and status

This documentation describes the inspected source code. It does not certify the statistical guarantees of the sequential method, causal validity of uplift estimates, or production readiness. See `STATISTICAL_METHODOLOGY.md` and `VALIDATION_AND_LIMITATIONS.md` before relying on results for real decisions.
