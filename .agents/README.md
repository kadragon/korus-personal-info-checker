# KORUS Personal Info Checker Project

## Overview
Python CLI tool analyzing KORUS Personal Information Processing System access logs to detect potential misuse of personal data.

## Project Status
- **Status**: Active Development
- **Coverage**: 99%
- **Python**: 3.12+
- **Last Updated**: 2025-11-06

## Key Features
1. Download reason validation
2. Login IP pattern analysis
3. Bulk query detection
4. Personnel master access monitoring

## Quick Start

### Installation
```bash
# Install dependencies
pip install .

# Setup environment
cp .env.example .env
# Edit .env with your paths
```

### Usage
```bash
python src/main.py
```

## Project Structure

### Directories
- `/src` - Source code
- `/tests` - Test suite (99% coverage)
- `/.spec` - Feature specifications
- `/.tasks` - Task tracking and history
- `/.agents` - Project profiles and catalogs

### Key Files
- `src/main.py` - Entry point
- `src/config.py` - Configuration
- `src/checkers/` - Analysis modules
- `pyproject.toml` - Dependencies and tools

## Development

### Prerequisites
- Python 3.12+
- uv (recommended) or pip

### Setup Dev Environment
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Setup pre-commit hooks
pre-commit install
```

### Running Tests
```bash
# Run tests with coverage
pytest --cov=src --cov-report=term

# Run specific test
pytest tests/test_main.py

# Run with verbose output
pytest -v
```

### Quality Checks
```bash
# Lint
ruff check src

# Type check
mypy src

# Security scan
bandit -r src
```

## Specifications
Active specs in `.spec/feature/`:
- `add-tests/` - Test suite expansion (COMPLETED)
- `test-coverage-improvement/` - 99% coverage achievement (COMPLETED)
- `data-count-sum-output/` - Count aggregation (ARCHIVED)
- `fix-rich-markup-error/` - Rich UI fix (ARCHIVED)
- `write-readme/` - Documentation (ARCHIVED)

## Profiles & Standards
See `.agents/projects/korus-personal-info-checker/profiles/python-cli@2025-11-06.md` for:
- Architecture patterns
- Quality standards
- Security requirements
- Development workflow

## Team
See `OWNERS` file for maintainer information.

## License
Internal use only - KORUS organization.
