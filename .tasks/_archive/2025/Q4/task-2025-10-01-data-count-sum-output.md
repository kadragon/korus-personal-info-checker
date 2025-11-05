# Task 2025-10-01: Data Count Sum and Output Fix
Linked Spec: SPEC-data-count-sum-output-1
Goal: Return per-checker row counts and display aggregate totals with Rich styling.
Steps:
- Adjust each `run_check` to return `int` counts.
- Sum totals in `discover_and_run_checkers` and feed to `print_summary`.
- Ensure Rich `Console(markup=True)` renders styled panel.
DoD Checklist:
- [x] Failing test exists (RED)
- [x] Minimal change passes (GREEN)
- [x] Refactor with GREEN preserved
- [x] Trace links updated

## Outcome
- Completed: 2025-10-01
- Validation: Manual execution confirmed totals and styled summary; lint clean (minor long-line warning accepted).

## Notes
- Aggregator treats non-integer checker returns as zero to guard legacy behaviour.
- No regressions observed in checker detection logic.
