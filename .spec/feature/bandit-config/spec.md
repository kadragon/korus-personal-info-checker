# Bandit Test Exclusion Configuration
Intent: Prevent Bandit runs from analysing test fixtures that intentionally use `assert`, avoiding false positives while keeping application code fully scanned.
Scope: In: Bandit configuration files (`.bandit`, `bandit.yaml`). Out: Runtime behaviour changes, production code modifications.
Dependencies: `bandit` pre-commit hook; `.pre-commit-config.yaml`.

## Behaviour (GWT)
- AC-1: GIVEN the developer runs `bandit -r .` WHEN Bandit discovers files THEN only files under `src/` are analysed and no issues originate from `tests/`.
- AC-2: GIVEN pre-commit executes the Bandit hook WHEN it runs against staged changes THEN it honours the same exclusion rules so test files do not trigger `B101` findings.

## Examples (Tabular)
| Case | Command | Expected Outcome |
|---|---|---|
| manual-scan | `bandit -r .` | Exit 0 with zero issues from `tests/` |
| pre-commit | `pre-commit run bandit --all-files` | Scan limited to `src/`, no test assertion warnings |

## API (Summary)
- Surfaces: `.bandit` INI file referencing `bandit.yaml` (exclude directories), Bandit CLI.
- Errors: Misconfiguration should fail with non-zero exit and logged warnings about missing `[bandit]` section or missing config file.

## Data & State
- Entities: Bandit configuration files.
- Invariants: Exclusion list must include `tests` and virtual environment directories; targets remain `src`.

## Tracing
Spec-ID: SPEC-bandit-config-1
Trace-To: tests/security/test_bandit_config.py::test_bandit_config_excludes_tests_and_targets_src (Trace: TEST-bandit-config-AC1); .bandit (Trace: SPEC-bandit-config-1); bandit.yaml (Trace: SPEC-bandit-config-1)
