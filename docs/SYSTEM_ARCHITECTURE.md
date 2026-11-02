# System Architecture

## Architectural separation

The repository separates the statistical engine from the API and browser presentation layers:

```text
                 Experiment data
                       |
                       v
             +-------------------+
             |   Decision Engine |
             | evaluate_experiment|
             +-------------------+
                |      |      |
        +-------+      |      +----------------+
        v              v                       v
   SRM module    Sequential module         CUPED module
        |              |                       |
        +--------------+-----------------------+
                       |
                 Decision result
                       |
              Optional uplift context
                       |
             +---------+----------+
             |                    |
             v                    v
        FastAPI layer        Python caller
             |
             v
      HTML dashboard
```

The diagram describes the responsibilities visible in the repository and README. Exact API routes, request models, response schemas, and dashboard-to-endpoint behavior must be documented after inspecting `api/app.py` and `frontend/dashboard.html`.

## Repository map

### `engine/`

Contains the statistical and decision modules:

- `decision_engine.py`: orchestration and verdict rules.
- `srm.py`: allocation integrity checks and segment diagnostics.
- `sequential.py`: day-by-day sequential evidence calculation.
- `cuped.py`: covariate adjustment and comparison.
- `cate.py`: T-learner uplift model.
- `frequentist.py`: baseline frequentist tests.
- `power_analysis.py`: sample-size and power calculations.

### `data/`

`simulator.py` generates synthetic experiment data. The simulator is used by module-level examples and the methodology notebook. Its precise parameters and generated columns should be documented from the simulator source.

### `api/`

`app.py` provides the FastAPI application. The README describes it as the HTTP backend for the decision engine.

### `frontend/`

`dashboard.html` is the browser-based dashboard. The README describes it as calling the live API.

### `notebooks/`

`methodology_validation.ipynb` contains the project's validation work. PNG figures in this directory are supporting outputs; retain them unless their provenance or relevance is reviewed.

## Decision flow

The inspected `evaluate_experiment` function follows this order:

1. Call `check_srm(df)`.
2. If SRM is detected, return `INVALID_SRM` immediately.
3. If `day_assigned` exists, call `run_sequential_test`.
4. Determine whether the final observed day crossed the sequential threshold and whether planned duration has been reached.
5. Call `compare_raw_vs_cuped(df)`.
6. Append optional `uplift_context` as an advisory string.
7. Apply the verdict rules and return a `Decision` dataclass.

## Import and execution note

Some engine modules use sibling imports such as `from srm import check_srm`. The `decision_engine.py` example adds the engine directory to the Python import path indirectly by being run from within `engine/`. Do not change import conventions as part of a documentation-only change. A later packaging/refactoring task should standardize imports and add tests for supported invocation modes.
