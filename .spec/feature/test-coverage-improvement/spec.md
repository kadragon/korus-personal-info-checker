# Test Coverage Improvement (84% → 90%)

**Intent:** Increase test coverage from 84% to 90% by adding tests for uncovered code paths in display.py, main.py, and utils.py

**Scope:**
- In: Unit tests for display functions, main() function edge cases, utils error handling branches
- Out: Integration tests, performance tests, UI/visual validation

**Dependencies:**
- Existing pytest infrastructure
- pytest-cov for coverage measurement
- pytest-mock for mocking
- Linked Task: `.tasks/task-2025-10-12-add-tests.md`

---

## Behaviour (GWT)

### AC-1: display.py coverage increases from 41% to 90%
- **GIVEN** display.py with 19 uncovered lines (17, 22, 30-37, 43-51, 62, 67, 72, 77, 84)
- **WHEN** tests are added for all output functions
- **THEN** coverage increases to at least 90%

### AC-2: main.py coverage increases from 59% to 90%
- **GIVEN** main.py with uncovered lines in main() function (69-70, 83-113, 117)
- **WHEN** tests are added for environment variable validation and full workflow
- **THEN** coverage increases to at least 90%

### AC-3: utils.py coverage increases from 82% to 90%
- **GIVEN** utils.py with 26 uncovered lines in error handling paths
- **WHEN** tests are added for error branches and edge cases
- **THEN** coverage increases to at least 90%

### AC-4: personal_file_checker.py reaches 100%
- **GIVEN** personal_file_checker.py at 98% (line 236 uncovered)
- **WHEN** test is added for the missing line
- **THEN** coverage increases to 100%

---

## Examples (Tabular)

| Module | Current Coverage | Target | Uncovered Lines | Test Strategy |
|--------|-----------------|--------|-----------------|---------------|
| display.py | 41% (19 lines) | 90% | 17,22,30-37,43-51,62,67,72,77,84 | Mock console, verify function calls |
| main.py | 59% (21 lines) | 90% | 69-70,83-113,117 | Mock env vars, test main() end-to-end |
| utils.py | 82% (26 lines) | 90% | Multiple error paths | Test error scenarios, edge cases |
| personal_file_checker.py | 98% (1 line) | 100% | 236 | Test specific edge case |

---

## API (Summary)

**Public Surface:**
- New test files: `tests/test_display.py` (create)
- Extended: `tests/test_main.py`, `tests/test_utils.py`

**Error Contract:**
- All tests must pass with GREEN status
- No regressions in existing tests (47 tests must remain passing)

---

## Data & State

**Entities:**
- Test fixtures: Mock console objects, temporary directories, sample DataFrames
- Environment: Mocked environment variables for main.py tests

**Invariants:**
- Coverage threshold: ≥90% line coverage
- All existing 47 tests remain GREEN
- No new external dependencies

**Migrations:** N

---

## Test Strategy

### Phase 1: display.py (41% → 90%)
**Files:** Create `tests/test_display.py`

**Tests to add:**
1. `test_print_header` - Test header printing with mocked console
2. `test_print_checker_header` - Test checker header formatting
3. `test_print_result_detected` - Test detected result with filename
4. `test_print_result_good` - Test good result without filename
5. `test_print_summary_with_count` - Test summary with total count
6. `test_print_summary_without_count` - Test summary without count
7. `test_print_error` - Test error message formatting
8. `test_print_info` - Test info message formatting
9. `test_print_zip_header` - Test zip header formatting
10. `test_print_zip_result` - Test zip result message
11. `test_print_zip_warning` - Test zip warning message

### Phase 2: main.py (59% → 90%)
**Files:** Extend `tests/test_main.py`

**Tests to add:**
1. `test_main_missing_save_dir` - Test main() with no SAVE_DIR env var
2. `test_main_missing_download_dir` - Test main() with no DOWNLOAD_DIR env var
3. `test_main_full_workflow_success` - Test complete main() execution path
4. `test_main_zip_error_handling` - Test zip error handling in main()
5. `test_main_as_script` - Test `if __name__ == "__main__"` block

### Phase 3: utils.py (82% → 90%)
**Files:** Extend `tests/test_utils.py`

**Tests to add:**
1. `test_save_excel_with_autofit_no_worksheet` - Test when ws is None (lines 82-84)
2. `test_save_excel_with_autofit_cell_exception` - Test cell processing exception (lines 95-96)
3. `test_find_excel_files_invalid_dir` - Test EnvironmentError for invalid dir (line 109)
4. `test_merge_preprocess_xlsx_exception` - Test file read exception (lines 132-134)
5. `test_merge_preprocess_no_files` - Test empty file list (line 143)
6. `test_merge_preprocess_both_id_columns` - Test warning for both ID columns (lines 162-166)
7. `test_merge_preprocess_sinbun_only` - Test sinbun column only (lines 169-170)
8. `test_find_and_prepare_env_error` - Test EnvironmentError handling (lines 198-200)
9. `test_find_and_prepare_save_exception` - Test save exception (lines 219-221)
10. `test_zip_files_no_matches` - Test zip with no matching files (line 238)
11. `test_filter_by_time_none_df` - Test ValueError for None DataFrame (line 280)

### Phase 4: personal_file_checker.py (98% → 100%)
**Files:** Extend `tests/checkers/test_personal_file_checker.py`

**Test to add:**
1. Identify and test line 236 scenario

---

## Tracing

**Spec-ID:** SPEC-test-coverage-improvement-1
**Trace-To:**
- Tests: `tests/test_display.py` (new)
- Tests: `tests/test_main.py` (extended)
- Tests: `tests/test_utils.py` (extended)
- Tests: `tests/checkers/test_personal_file_checker.py` (extended)
- Task: `.tasks/task-2025-10-12-add-tests.md`

---

## DoD Checklist

- [ ] All new tests written and passing (RED → GREEN)
- [ ] Overall coverage ≥ 90% (pytest --cov=src)
- [ ] All 47 existing tests still passing
- [ ] No new linting or type errors
- [ ] Task file updated with completion status
