# KORUS Personal Info Checker - Unified AGENTS

Last Updated: 2025-11-06
Framework: SDD x TDD (Spec-Driven Development x Test-Driven Development)

## Project Overview
Python CLI tool that analyzes KORUS Personal Information Processing System access logs to detect suspected personal data misuse (download reason issues, suspicious IPs, bulk access, personnel master access anomalies).

## Operating Principles (Constitution)
- Spec is SSOT: all behavior traces back to a SPEC-ID.
- TDD first: RED -> GREEN -> REFACTOR for every change.
- Profiles govern: quality, security, and error-handling standards are mandatory.
- Trace required: commits/tests/files reference SPEC-ID and TEST-ID.
- No over-generation: produce the minimum artifacts needed.
- Ambiguity = halt: stop and record the gap before proceeding.
- Memory hygiene: keep active tracking concise and current.
- Rollback on failure: shrink scope and log the cause.

## Architecture & Data Flow
- Pipeline: INPUT -> EXTRACT -> TRANSFORM -> DETECT -> OUTPUT.
- Checker interface: run_check(download_dir, save_dir, reference_date) -> int (count of records inspected).
- Orchestration: main() loads config, discovers checkers, runs each, aggregates totals, prints summary.
- Modules:
  - src/main.py (orchestrator)
  - src/config.py (constants)
  - src/utils.py (file/date utilities)
  - src/display.py (Rich console output)
  - src/checkers/* (business logic)

## Configuration & Data Contract
- Environment variables:
  - DOWNLOAD_DIR: input directory
  - SAVE_DIR: output directory
- Input files: prefix `개인정보접속기록_*.xls*`.
- Output files: `{checker_name}_{YYYYMMDD}.xlsx`.
- Required access log columns (Korean): 사용자ID, 접속일시, 작업구분, IP주소, 다운로드사유.
- Encoding: UTF-8 with BOM for Excel compatibility.

## Quality Gates (Must Pass)
- Lint: `ruff check src`
- Type check: `mypy src`
- Security: `bandit -r src` (tests excluded)
- Tests: `pytest --cov=src --cov-report=term` (line >=80%, branch >=70%)
- Current health (2025-11-06): 99% line coverage, 80 tests passing.

## Documentation Standards
- Docstrings: English, Google style for all public APIs.
- Comments: explain WHY, not WHAT.
- README remains authoritative for setup and usage.

## Error Handling (Catalog Summary)
- Categories: Configuration (CFG-001..003), File System (FS-001..004), Data (DATA-001..004), Runtime (RT-001..003).
- Exit codes: 0 success, 1 config, 2 filesystem, 3 data, 4 runtime, 5 unexpected.
- Logging: Error (fatal), Warning (non-fatal), Info (progress), Debug (dev only).

## Security & Compliance (Catalog Summary)
- PIPA compliance: never log PII; mask if needed.
- Validate paths (no traversal) and required env vars.
- Avoid insecure primitives (pickle, MD5/SHA1, weak crypto, injection risks).
- Dependency security: scan and keep lockfiles updated.

## Patterns (Data Pipeline)
- Use a consistent checker pattern with schema validation, transformation, detection, and report output.
- Orchestrator sums checker counts; non-int counts treated as 0.
- Prefer resilient execution: log recoverable errors, raise unexpected errors.

## Specs (SSOT)
Active/Implemented:
- SPEC-add-tests-1 (COMPLETED 2025-11-06): pytest-based tests with coverage >=80%; traces in tests/test_*.py and tests/checkers/*.
- SPEC-test-coverage-improvement-1 (COMPLETED 2025-11-06): display.py, main.py, utils.py coverage >=90%; personal_file_checker 100%.
- SPEC-bandit-config-1 (IMPLEMENTED): Bandit excludes tests/ and .venv; configs in .bandit and bandit.yaml.

Archived:
- SPEC-data-count-sum-output-1 (2025-10-01): checkers return int counts; summary shows aggregate count with Rich markup.
- SPEC-fix-rich-markup-error-1 (2025-10-01): rich >=13.0.0; Text(markup=True) supported.
- SPEC-write-readme-1 (2025-10-01): README overhaul for setup and usage.

## Tasks
Active/Backlog:
- None (as of 2025-11-06).

Recent Completed:
- 2025-11-06: Test coverage improvement to 99%; lint/mypy/bandit clean.
- 2025-10-12: Comprehensive tests (SPEC-add-tests-1, SPEC-test-coverage-improvement-1).
- 2025-10-01: Data count aggregation, Rich markup fix, README rewrite.

DoD Checklist (TDD): failing test (RED) -> minimal pass (GREEN) -> refactor -> trace links updated.

## Ownership & Review
- Maintainer: @kadragon (Project Lead).
- All changes require maintainer review; security/architecture changes require extended review.

