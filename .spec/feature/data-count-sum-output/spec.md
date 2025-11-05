---
spec_id: SPEC-data-count-sum-output-1
agents:
  base_profile: profiles/python-cli.md
  project_profile: profiles/python-cli@2025-11-06.md
  catalogs:
    errors: catalogs/errors.md
  patterns:
    data-pipeline: global/patterns/data-pipeline.md
deltas: {}
---

# Data Count Summary Output
Intent: Surface total original record counts in the CLI summary for attachments 2–4.
Scope: In: adjust checker return contracts, aggregate counts in `main.py`, enable styled summary output. Out: modifying checker detection logic or additional report formats.
Dependencies: [src/checkers/personal_file_checker.py], [src/checkers/login_checker.py], [src/checkers/download_reason_checker.py], [src/main.py], [src/display.py]

## Behaviour (GWT)
- AC-1: GIVEN each checker processes its dataset WHEN `run_check` completes THEN it returns the number of original records inspected as an `int`.
- AC-2: GIVEN all checkers run AND return counts WHEN `main.main()` renders the summary THEN the panel includes the aggregate count and renders Rich markup without escaping.

## Examples (Tabular)
| Case | Input | Steps | Expected |
|---|---|---|---|
| personal-access-rows | DataFrame with 150 rows | Invoke `personal_file_checker.run_check` | Returns 150 |
| summary-panel | All checkers return {100, 50, 25} | Run `python -m src.main` | Summary shows `총합: 175건` with styled panel |

## API (Summary)
Surface: Checker `run_check(download_dir, save_dir, prev_month) -> int`; summary printer `print_summary(folder_path, total_count)`.
Signature: Returns integer count; non-integer results treated as zero in aggregator.
Errors: Exceptions within checkers bubble up to error handler; summary resilient to `None` counts by omitting aggregate line.

## Data & State
Entities: In-memory pandas DataFrames per checker; aggregate totals stored only during execution.
Invariants: Return types remain integers; Rich console accepts markup-enabled text.

## Tracing
Spec-ID: SPEC-data-count-sum-output-1
Trace-To: .tasks/_archive/2025-Q4/task-2025-10-01-data-count-sum-output.md; src/main.py (Trace: SPEC-data-count-sum-output-1); src/display.py (Trace: SPEC-data-count-sum-output-1); src/checkers/personal_file_checker.py (Trace: SPEC-data-count-sum-output-1); src/checkers/login_checker.py (Trace: SPEC-data-count-sum-output-1); src/checkers/download_reason_checker.py (Trace: SPEC-data-count-sum-output-1)
