# Task 2025-10-12: Add Comprehensive Tests
Linked Spec: SPEC-add-tests-1
Goal: Stand up pytest-based unit and integration coverage ≥80% across `src`.
Steps:
- Finalise fixtures for checker modules (DataFrames, temp dirs).
- Raise line coverage from 78% → ≥80% with focused assertions.
- Integrate coverage gate into routine developer workflow.
DoD Checklist:
- [x] Failing test exists (RED)
- [x] Minimal change passes (GREEN)
- [ ] Refactor with GREEN preserved
- [x] Trace links updated

## Status
- Current State: In progress (coverage 78% vs 80% target).
- Latest Run: `pytest --cov=src` (pass, coverage 78%).
- Blockers: Needs assertion refinement for checker fixtures; confirm imports use package-relative paths.

## Notes
- Dependencies added: pytest, pytest-cov, pytest-mock.
- Test layout mirrors `src` package; `tests/conftest.py` hosts shared fixtures.
- Encoding considerations for Korean column names require fixture parity with real data.
