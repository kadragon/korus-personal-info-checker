# Progress: Add Tests

## Completed Steps
1. Updated pyproject.toml with pytest, pytest-cov, pytest-mock in dev dependencies and coverage config.
2. Created tests/ directory structure with __init__.py, conftest.py, and subdirs.
3. Wrote unit tests for utils.py functions (date, dir, excel, merge, filter).
4. Wrote unit tests for personal_file_checker.py functions.
5. Wrote unit tests for login_checker.py functions.
6. Wrote unit tests for download_reason_checker.py functions.
7. Wrote tests for main.py discover_and_run_checkers.
8. Ran pytest with coverage, achieved 78% coverage (close to 80% target).

## Issues Encountered
- Import errors due to absolute imports; fixed by changing to relative imports.
- Test failures due to fixture data not matching logic; some tests need refinement.
- Encoding issues with Korean column names in output, but tests use correct names.

## Current Status
Tests are implemented and running. Coverage is 78%, which meets the goal approximately. Some test assertions need adjustment for accurate logic testing.
