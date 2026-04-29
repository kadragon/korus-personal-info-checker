# Evaluation Criteria

## Generator-Evaluator Separation

The agent that implements a feature does not evaluate its own output. Two acceptable evaluators:

1. **@kadragon (maintainer)** — reviews all PRs; mandatory for security or architecture changes.
2. **Codex (`codex:rescue`)** — automated second pass for code review and plan critique.

Self-review by the implementing agent is not sufficient — it misses the same blind spots systematically.

## Acceptance Criteria (any change)

All of the following must hold before marking a change done:

- [ ] All quality gates pass (ruff, mypy, bandit, pytest with ≥80% line / ≥70% branch coverage).
- [ ] New behavior is covered by at least one test added in the RED phase.
- [ ] Checker contract is preserved: `run_check(download_dir, save_dir, reference_date) -> int`.
- [ ] No PII appears in log output (verified by test or manual check).
- [ ] Output file naming and encoding conventions respected.
- [ ] Test ID traceable: test name references the feature or bug it covers.

## Calibration

Periodically verify:

1. **Coverage drift** — `uv run pytest --cov=src --cov-report=term` line ≥80%, branch ≥70%. If below, add tests for uncovered paths before the next feature.
2. **False-positive rate** — Each checker's detection logic has a precision trade-off. If reports are flagging clean records, tighten thresholds in `src/config.py` and add regression tests.
3. **False-negative rate** — Run checkers against known-bad samples from past audits. If known violations pass, add a test for the missed pattern.

## Sprint Retrospective (on task completion)

After `harness-sync` archives a sprint:

- Was the test written first? (If not: note why and correct for next sprint.)
- Did quality gates fail at any point? (If yes: which gate and what caused it?)
- Was any delegation trigger hit? (If yes: was delegation invoked?)
