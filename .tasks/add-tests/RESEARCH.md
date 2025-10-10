# Research: Adding Tests to korus-personal-info-checker

## Project Overview
The project is a Python CLI tool that processes Excel files containing personal information access logs, login records, and download reasons. It performs automated checks for compliance and security issues, generating reports in Excel format.

## Code Structure
- `main.py`: Entry point, discovers and runs checker modules dynamically.
- `checkers/`: Package with three checker modules:
  - `personal_file_checker.py`: Checks personal info access logs for HR master access, bulk queries/saves.
  - `login_checker.py`: Checks login records for IP switches, off-hours, holidays.
  - `download_reason_checker.py`: Checks download reasons for invalid reasons, high counts, frequency, off-hours.
- `utils.py`: Utility functions for date handling, Excel processing, file merging, filtering.
- `config.py`: Constants for column names, thresholds, file prefixes.
- `display.py`: Functions for console output formatting.

## Testing Needs
- **Unit Tests**: Test individual functions in isolation.
- **Integration Tests**: Test checker modules end-to-end with mock data.
- **Error Handling**: Test invalid inputs, missing files, malformed data.
- **Edge Cases**: Empty DataFrames, single row, threshold boundaries.
- **Mocking**: File I/O, pandas operations, datetime.

## Testing Framework
- **pytest**: Standard for Python testing, fixtures, parametrization.
- **pytest-cov**: For coverage reporting.
- **pytest-mock**: For mocking.
- Dependencies: Add to pyproject.toml dev section.

## Coverage Goals
- Target: >80% coverage.
- Focus on: utils.py (high complexity), checkers (business logic), main.py (orchestration).

## Hypotheses
- Most functions are pure or can be tested with DataFrame fixtures.
- File operations need mocking to avoid real I/O.
- Time-dependent functions need injectable clocks.
- Excel reading/writing can be mocked at pandas level.

## Evidence
- No existing tests directory.
- pyproject.toml has dev deps for linting (ruff, mypy, bandit) but no testing.
- Code uses pandas heavily, so tests need DataFrame creation.
- Functions have clear inputs/outputs, testable.
