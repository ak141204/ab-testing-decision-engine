# Contributing

Thank you for considering a contribution to the A/B Testing Decision Engine.

The project is being prepared for open-source collaboration. Contributions that improve correctness, clarity, reproducibility, testing, documentation, and usability are welcome.

## Before you start

1. Read the root `README.md`.
2. Review the documents in `docs/`.
3. Search existing GitHub Issues and Pull Requests to avoid duplicating work.
4. For a substantial change, open an issue first to discuss the proposed approach.

## Development setup

```bash
git clone https://github.com/ak141204/ab-testing-decision-engine.git
cd ab-testing-decision-engine

python -m venv .venv
```

Activate the environment:

**Windows Git Bash**
```bash
source .venv/Scripts/activate
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Branch workflow

Create a focused branch from the current `main` branch:

```bash
git switch main
git pull origin main
git switch -c feature/short-description
```

Suggested branch prefixes:

- `feature/` for new functionality
- `fix/` for bug fixes
- `docs/` for documentation
- `test/` for tests
- `refactor/` for code restructuring

## Contribution expectations

- Keep changes focused and explain why they are needed.
- Preserve existing behavior unless the change intentionally modifies it.
- Do not commit secrets, API keys, credentials, virtual environments, or cache files.
- Add or update tests for behavior changes.
- Update documentation when interfaces, assumptions, or workflows change.
- Use clear names and comments where they help explain non-obvious logic.
- Do not claim statistical guarantees unless supported by appropriate derivations and validation.

## Statistical changes

Changes to statistical methods require special care. A contribution should explain:

- The estimand and assumptions.
- The test statistic and decision boundary.
- Type-I error and power validation approach.
- Behavior under edge cases and invalid inputs.
- Comparison with a trusted reference implementation where appropriate.

Simulation results should state the configuration, number of repetitions, randomization method, and uncertainty around estimated error rates.

## Pull requests

A Pull Request should include:

1. A clear summary of the change.
2. The motivation and related issue, if any.
3. Tests or validation performed.
4. Screenshots for visible dashboard changes, where useful.
5. Documentation updates, where applicable.
6. Known limitations or follow-up work.

Keep Pull Requests focused and reasonably small. Be prepared to discuss feedback and revise the contribution.

## Current testing status

Automated test coverage and continuous integration are planned project improvements. Until a test suite is present, contributors should describe the exact manual checks or scripts they ran and should not imply that an automated test suite passed.

## Questions

For questions about a proposed contribution, open a GitHub Issue with enough context for maintainers and other contributors to understand the problem.
