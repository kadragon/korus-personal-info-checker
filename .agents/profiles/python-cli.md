# Python CLI Tool Profile

## Overview
Profile for Python-based command-line interface tools focused on data processing and analysis.

## Core Principles
1. **Explicit Configuration**: Use environment variables via `.env` files
2. **Rich Terminal Output**: Leverage modern terminal UI libraries for user experience
3. **Type Safety**: Enforce static type checking at development time
4. **Documentation**: Comprehensive English docstrings for all public APIs

## Technology Stack

### Language
- **Python**: 3.12+
- **Packaging**: Modern pyproject.toml-based configuration

### Core Dependencies
- **Data Processing**: pandas, openpyxl (Excel), xlrd
- **Configuration**: python-dotenv (environment management)
- **CLI/UI**: rich (terminal formatting and progress)
- **Date Handling**: python-dateutil, holidays

### Development Tools
- **Linter**: ruff (linting + formatting)
- **Type Checker**: mypy (static type analysis)
- **Security**: bandit (security vulnerability scanning)
- **Testing**: pytest, pytest-cov, pytest-mock
- **Pre-commit**: Automated quality gates

## Architecture Patterns

### Entry Point
- Single `main.py` as entry point
- Sequential execution of independent modules
- Centralized error handling and logging

### Module Organization
```
src/
  main.py           # Entry point
  config.py         # Configuration constants
  utils.py          # Shared utilities
  display.py        # Output formatting
  checkers/         # Business logic modules
    module_a.py
    module_b.py
```

### Configuration Management
- Environment variables for paths and settings
- Module-level constants for thresholds and defaults
- Centralized config module for shared settings

### Error Handling
- Exceptions propagate to main error handler
- Rich console for user-friendly error messages
- Graceful degradation where possible

## Quality Standards

### Static Analysis
- **Linting**: ruff with rules E, F, I, B, C4, SIM
- **Type Checking**: mypy with strict configs
- **Security**: bandit for vulnerability scanning
- **Line Length**: 88 characters (Black-compatible)

### Testing
- **Coverage Target**: ≥80% line coverage
- **Test Organization**: Mirror src/ structure in tests/
- **Fixtures**: Centralized in conftest.py
- **Methodology**: TDD (RED → GREEN → REFACTOR)

### Documentation
- **Language**: English for all docstrings
- **Format**: Google-style docstrings
- **Scope**: All public functions and modules

## Performance Considerations
- Lazy loading of large datasets
- Streaming processing for Excel files where possible
- Progress indicators for long-running operations

## Security Considerations
- No sensitive data in version control
- Environment variables for paths and credentials
- Input validation for file paths
- Safe file operations with proper error handling

## Observability
- Rich console output with structured formatting
- Progress bars for long operations
- Summary reports with key metrics
- Error messages with actionable guidance
