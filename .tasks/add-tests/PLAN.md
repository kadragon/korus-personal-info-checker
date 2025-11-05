# Plan: Add Tests to korus-personal-info-checker

## Acceptance Criteria
- pytest and pytest-cov installed in dev dependencies.
- tests/ directory created with test files mirroring src structure.
- Unit tests for all public functions in utils.py, checkers/*.py, main.py.
- Integration tests for checker run_check functions.
- Coverage >80% on src/ package.
- Tests pass on CI (ruff, mypy, bandit already configured).
- No regressions in existing functionality.

## Targets
- **Dependencies**: Add pytest, pytest-cov, pytest-mock to pyproject.toml dev.
- **Test Structure**:
  - tests/__init__.py
  - tests/test_utils.py
  - tests/test_main.py
  - tests/checkers/test_personal_file_checker.py
  - tests/checkers/test_login_checker.py
  - tests/checkers/test_download_reason_checker.py
  - tests/conftest.py (fixtures for DataFrames, temp dirs)
- **Coverage Config**: Add [tool.coverage] to pyproject.toml.

## Steps
1. Update pyproject.toml with test dependencies and coverage config.
2. Create tests/ directory and basic structure.
3. Write tests for utils.py functions (get_prev_month_yyyymm, make_save_dir, etc.).
4. Write tests for checker functions (_filter_by_job_master_exclude_detail_id, etc.).
5. Write integration tests for run_check functions using temp files and mock data.
6. Write tests for main.py discover_and_run_checkers.
7. Run coverage and ensure >80%.
8. Update CI workflows if needed (bandit.yml, ruff.yml exist).

## Tests & Rollback
- Tests: Run pytest with coverage.
- Rollback: Remove tests/ dir, revert pyproject.toml.

## Dependencies
- pytest / 8.0.0 / 2024-07-28 / latest stable / For testing framework
- pytest-cov / 4.1.0 / 2024-07-28 / latest stable / For coverage reporting
- pytest-mock / 3.12.0 / 2024-07-28 / latest stable / For mocking
