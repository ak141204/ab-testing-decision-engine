# Validation Status and Known Limitations

## Evidence currently present in the repository

The README reports validation results from `notebooks/methodology_validation.ipynb`, including:

- A naive daily-peeking false-positive rate of 22.7% versus 1.0% for the project's sequential method under the reported simulation.
- A reported 11.6% CUPED confidence-interval width reduction in one demonstration.
- A CATE analysis using the Criteo uplift dataset and a reported positive-uplift fraction.
- An injected iOS traffic-allocation issue identified by SRM segmentation.

These are project-reported results, not independently reproduced in this documentation pass. Preserve the notebook and its figures, and record the exact notebook version, random seeds, number of repetitions, dataset sample, and environment when reproducing them.

## Limitations stated by the project

The README explicitly notes:

1. The sequential method's reported false-positive rate was below nominal alpha in the described simulation (conservative behavior).
2. CUPED's benefit can be smaller for binary conversion outcomes than for continuous outcomes.
3. The CATE ranking score is a simplified proxy rather than a full Qini curve.

## Additional code-review items

The inspected modules suggest the following validation work:

- Add input checks for required columns, group labels, missing values, empty groups, and valid parameter ranges.
- Check SRM behavior for non-50/50 allocation and segment-level multiple testing.
- Independently validate the sequential likelihood-ratio derivation and its claimed stopping-time guarantee.
- Test CUPED inference on binary and continuous outcomes, including zero-variance covariates.
- Evaluate uplift ranking with established uplift metrics and avoid interpreting outcome AUC as causal-effect accuracy.
- Test sample-size and power calculations against a trusted reference over a grid of baseline rates, MDEs, alpha levels, and powers.
- Verify decision-engine behavior when `day_assigned` is absent, when no sequential rows are produced, and when planned duration is reached.
- Populate or remove the currently unpopulated `Decision.confidence_interval` field after deciding the intended API contract.

## Validation policy for future contributions

A statistical feature should not be described as validated merely because it runs. A contribution should include:

1. A clear statement of assumptions and estimand.
2. Unit tests for ordinary and edge cases.
3. Simulation tests with known ground truth where appropriate.
4. Comparison against a trusted reference implementation or derivation.
5. Reproducible seeds and configuration for reported simulation results.
6. Documentation of failure modes and interpretation limits.
