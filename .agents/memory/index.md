# Memory Index
**Last Updated**: 2025-11-06
**Purpose**: Active specs and tasks summary (≤200 lines)

## Active Specifications

### SPEC-add-tests-1
**Status**: COMPLETED (2025-11-06)
**Location**: `.spec/feature/add-tests/`
**Summary**: Establish pytest-based test coverage ≥80% for src/ package
**Result**: 99% coverage achieved (exceeded target)
**Traces**:
- Tests: tests/test_*.py, tests/checkers/test_*.py
- Task: .tasks/task-2025-10-12-add-tests.md

### SPEC-test-coverage-improvement-1
**Status**: COMPLETED (2025-11-06)
**Location**: `.spec/feature/test-coverage-improvement/`
**Summary**: Increase coverage 84% → 90% via display.py, main.py, utils.py tests
**Result**: 99% coverage (414 statements, 2 missed)
**Traces**:
- Tests: tests/test_display.py, tests/test_main.py, tests/test_utils.py
- Task: .tasks/task-2025-10-12-add-tests.md

## Archived Specifications

### SPEC-data-count-sum-output-1
**Status**: ARCHIVED (2025-10-01)
**Location**: `.spec/feature/data-count-sum-output/`
**Summary**: Aggregate and display total record counts from checkers
**Traces**: .tasks/_archive/2025/Q4/task-2025-10-01-data-count-sum-output.md

### SPEC-fix-rich-markup-error-1
**Status**: ARCHIVED (2025-10-01)
**Location**: `.spec/feature/fix-rich-markup-error/`
**Summary**: Rich library ≥13.0.0 for Text(markup=True) support
**Traces**: .tasks/_archive/2025/Q4/task-2025-10-01-fix-rich-markup-error.md

### SPEC-write-readme-1
**Status**: ARCHIVED (2025-10-01)
**Location**: `.spec/feature/write-readme/`
**Summary**: Comprehensive README with setup, usage, structure docs
**Traces**: .tasks/_archive/2025/Q4/task-2025-10-01-write-readme.md

### SPEC-bandit-config-1
**Status**: IMPLEMENTED
**Location**: `.spec/feature/bandit-config/`
**Summary**: Bandit configuration excluding tests/ from security scans
**Traces**: .bandit, bandit.yaml, pre-commit hooks

## Active Tasks

### Current Backlog
**Location**: `.tasks/backlog.md`
**Status**: Empty - no pending tasks

All recent tasks completed as of 2025-11-06.

## Task History

### 2025-11-06
**Log**: `.tasks/log-2025-11-06.md`
**Activities**:
- Test coverage improvement to 99%
- SDD×TDD framework migration
- Architecture documentation restructure

### 2025-10-12
**Task**: `.tasks/task-2025-10-12-add-tests.md`
**Activity**: Comprehensive test suite establishment
**Status**: COMPLETED with 99% coverage

### 2025 Q4 Archive
**Index**: `.tasks/TASKS_ARCHIVE_INDEX.md`
**Location**: `.tasks/_archive/2025/Q4/`
**Contents**:
- task-2025-10-01-data-count-sum-output.md
- task-2025-10-01-fix-rich-markup-error.md
- task-2025-10-01-write-readme.md

## Profile & Catalog Usage

### Base Profile
**Path**: `.agents/profiles/python-cli.md`
**Used By**: All specs in this project
**Version**: Base (unversioned, stable)

### Project Profile
**Path**: `.agents/profiles/python-cli@2025-11-06.md`
**Version**: 2025-11-06
**Status**: Active
**Overrides**: None (fully compliant with base)

### Active Catalogs
- **errors**: `.agents/catalogs/errors.md`
- **security**: `.agents/catalogs/security.md` (PIPA compliance)
- **quality**: `.agents/catalogs/quality.md` (ruff, mypy, coverage)

### Active Patterns
- **data-pipeline**: `.agents/patterns/data-pipeline.md`

## Quality Metrics (Current)

### Test Coverage
- **Overall**: 99% (414/416 statements)
- **Target**: ≥80%
- **Status**: ✓ Exceeds target

### Type Safety
- **mypy**: 0 errors in 9 source files
- **Status**: ✓ Pass

### Code Quality
- **ruff**: 0 issues
- **Status**: ✓ Pass

### Security
- **bandit**: 0 vulnerabilities (src/ only)
- **Status**: ✓ Pass

## Project Health

### Current State
- **Phase**: Maintenance
- **Stability**: Stable
- **Coverage**: Excellent (99%)
- **Documentation**: Complete
- **Technical Debt**: Low

### Dependencies
- Python: 3.12+
- Key Libraries: pandas, openpyxl, rich, holidays
- Dev Tools: pytest, ruff, mypy, bandit, pre-commit

### Next Actions
- Monitor for new requirements
- Maintain quality gates in future changes
- Update this index when new specs/tasks added
- Archive old specs quarterly

## Maintenance Notes

### Update Triggers
Update this index when:
1. New spec created in .spec/
2. Spec status changes (ACTIVE → COMPLETED → ARCHIVED)
3. New task added to backlog
4. Project profile version updated
5. Quarterly review (prune old references)

### Retention Policy
- Active specs: Keep all details
- Completed specs (< 30 days): Full reference
- Completed specs (> 30 days): Summary only
- Archived specs (> 90 days): Prune from index (keep in .spec/)

---
**Index Size**: 188 lines (within 200 line budget)
