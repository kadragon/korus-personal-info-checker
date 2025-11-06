# KORUS Personal Info Checker Profile
**Version**: 2025-11-06
**Base Profile**: profiles/python-cli.md

## Project Overview
Python CLI tool for analyzing access log records from KORUS Personal Information Processing System to detect suspected cases of personal information misuse.

## Purpose
Detect and report suspicious patterns in personal information access logs:
- Inappropriate download reasons
- Suspicious login IP patterns
- Bulk query/storage patterns
- Personnel master access anomalies

## Domain Context

### Regulatory Framework
- **PIPA**: Korean Personal Information Protection Act compliance
- **Purpose**: Audit trail analysis for data protection
- **Scope**: Internal system access monitoring

### Business Logic
1. **Download Reason Checking**: Validate justification for data downloads
2. **Login IP Analysis**: Detect unusual access locations
3. **Bulk Access Detection**: Identify large-scale data queries
4. **Personnel Master Monitoring**: Track employee data access

## Architecture

### Module Structure
```
src/
  main.py                           # Orchestrator
  config.py                         # Configuration constants
  utils.py                          # File/date utilities
  display.py                        # Rich console output
  checkers/
    personal_file_checker.py        # Personnel access checks
    login_checker.py                # IP pattern analysis
    download_reason_checker.py      # Download validation
```

### Data Flow
```
Excel Logs (DOWNLOAD_DIR)
  ↓
File Discovery & Loading
  ↓
Schema Validation
  ↓
Data Transformation
  ↓
Checker Modules (parallel)
  ↓
Report Generation (SAVE_DIR)
  ↓
Summary Display (Rich Console)
```

## Configuration

### Environment Variables
```bash
DOWNLOAD_DIR=/path/to/logs        # Input directory
SAVE_DIR=/path/to/reports         # Output directory
```

### File Naming Convention
- Input: `개인정보접속기록_*.xls*` (Personal Information Access Log prefix)
- Output: `{checker_name}_{YYYYMMDD}.xlsx`

### Schema Expectations

#### Access Log Columns (Korean)
- `사용자ID` (User ID)
- `접속일시` (Access DateTime)
- `작업구분` (Operation Type)
- `IP주소` (IP Address)
- `다운로드사유` (Download Reason)

## Quality Targets

### Coverage
- **Current**: 99% (414 statements, 2 missed)
- **Target**: ≥80% line coverage
- **Strategy**: TDD with comprehensive fixtures

### Performance
- **Processing**: <5s per 1000 records
- **Memory**: <500MB for typical dataset
- **Concurrency**: Sequential execution (sufficient for workload)

### Security
- **PII Handling**: Masked display in logs/console
- **File Access**: Validated paths, no traversal
- **Error Messages**: No sensitive data exposure

## Development Workflow

### Pre-commit Hooks
1. **ruff**: Linting and formatting
2. **mypy**: Type checking
3. **bandit**: Security scanning (exclude tests)

### Testing Strategy
- **Unit Tests**: Individual checker modules
- **Integration Tests**: Full pipeline with fixtures
- **Fixtures**: Representative Korean-language DataFrames
- **Mocking**: File I/O, datetime, environment variables

### Release Process
1. Version bump in pyproject.toml
2. Update CHANGELOG in .agents/AGENTS.md
3. Full test suite pass
4. Create git tag
5. Archive task in .tasks/_archive/

## Profiles & Catalogs

### Applied Profiles
- `profiles/python-cli.md` - Base Python CLI patterns

### Applied Catalogs
- `catalogs/errors.md` - Error handling standards
- `catalogs/security.md` - Security rules (PIPA compliance)
- `catalogs/quality.md` - Code quality standards

### Applied Patterns
- `patterns/data-pipeline.md` - Data processing pipeline

## Project-Specific Deltas

### Deviations from Base Profile
None - fully compliant with base profile.

### Additional Constraints
1. **Language**: Korean column names in data, English in code/docs
2. **Date Handling**: Korean business calendar (holidays package)
3. **Encoding**: UTF-8 with BOM for Excel compatibility
4. **Output Format**: Excel-only (organizational requirement)

### Additional Dependencies
- `holidays`: Korean holiday calendar
- `xlrd`: Legacy .xls format support

## Maintenance

### Active Specifications
See `.agents/memory/index.md` for current active specs.

### Change History
- **2025-11-06**: Test coverage increased 84% → 99%
- **2025-10-12**: Comprehensive test suite added (SPEC-add-tests-1)
- **2025-10-10**: Docstring translation to English
- **2025-10-01**: Rich UI integration (SPEC-fix-rich-markup-error-1)
- **2025-10-01**: Data count summation (SPEC-data-count-sum-output-1)
- **2025-10-01**: README comprehensive update (SPEC-write-readme-1)

### Deprecation Policy
- Maintain compatibility with Python 3.12+
- Support Excel formats: .xlsx, .xls
- No breaking changes to checker interface
