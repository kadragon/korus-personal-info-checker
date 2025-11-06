---
spec_id: SPEC-add-tests-1
agents:
  base_profile: profiles/python-cli.md
  project_profile: profiles/python-cli@2025-11-06.md
  catalogs:
    errors: catalogs/errors.md
    quality: catalogs/quality.md
deltas:
  coverage_target: { line: 80, branch: 70 }
---

# Test Suite Expansion
Intent: Establish automated test coverage for korus-personal-info-checker.
Scope: In: add pytest-based unit and integration tests covering `src` package behaviour, configure coverage tooling. Out: refactoring production code beyond test seams, CI workflow authoring.
Dependencies: [src/main.py], [src/checkers/*], [src/utils.py], [pyproject.toml]

## Behaviour (GWT)
- AC-1: GIVEN project dependencies installed AND `.env` prepared WHEN `pytest --cov=src --cov-report=term` runs THEN the suite exits 0 and line coverage is at least 80%.
- AC-2: GIVEN a checker module exposing `run_check` returning an `int` WHEN `discover_and_run_checkers` executes inside the suite THEN the aggregated total equals the sum of individual checker returns.
- AC-3: GIVEN representative DataFrame fixtures for access, login, and download logs WHEN checker-specific tests execute THEN each detector writes results or remains empty without raising exceptions.

## Examples (Tabular)
| Case | Input | Steps | Expected |
|---|---|---|---|
| coverage-threshold | Installed dev dependencies | Run `pytest --cov=src` | Exit code 0, coverage ≥80% |
| checker-aggregation | Mock checker returning 5 | Invoke `discover_and_run_checkers` | Aggregated total == 5 |
| detector-fixture | Sample login dataframe | Execute `tests/checkers/test_login_checker.py` | No exception, detections generated per thresholds |

## API (Summary)
Surface: `pytest` CLI entry point with `tests/` package, fixtures in `tests/conftest.py`.
Signature: `pytest [OPTIONS]` (default command `pytest --cov=src`), ensures deterministic imports via `src` package.
Errors: Failing assertions or coverage below threshold should break the suite; tests mock filesystem and datetime to avoid side effects.

## Data & State
Entities: Temporary directories and in-memory pandas DataFrames created via fixtures.
Invariants: Test fixtures must avoid mutating production directories; cleanup handled by pytest tmp_path fixtures. No migrations.

## Tracing
Spec-ID: SPEC-add-tests-1
Trace-To: .tasks/task-2025-10-12-add-tests.md; tests/test_utils.py (Trace: TEST-add-tests-AC1); tests/test_main.py (Trace: TEST-add-tests-AC2); tests/checkers/test_personal_file_checker.py (Trace: TEST-add-tests-AC3a); tests/checkers/test_login_checker.py (Trace: TEST-add-tests-AC3b); tests/checkers/test_download_reason_checker.py (Trace: TEST-add-tests-AC3c)
