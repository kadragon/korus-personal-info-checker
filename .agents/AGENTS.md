# korus-personal-info-checker

## Intent

This agent analyzes access log records from the 'KORUS Personal Information
Processing System' to detect suspected cases of personal information misuse
and generate reports. The main goals are to check download reasons, login IPs,
and patterns of bulk queries/storage.

## Constraints

- **Environment Variables**: Must create a `.env` file in the project root
  before execution, setting `DOWNLOAD_DIR` (log file location) and `SAVE_DIR`
  (report save location).
- **Input Data**: Analysis target logs must be Excel files with a specific
  format. Follow the filename prefix rule (e.g., `개인정보접속기록_`, meaning
  `Personal Information Access Log_`).
- **Execution Environment**: Requires Python 3.12 and installation of
  dependencies listed in `pyproject.toml`.

## Context

### Project Overview

- **Purpose**: A Python-based CLI tool that analyzes Excel logs from the KORUS
  system to identify potential cases of personal information misuse
  (inappropriate access, bulk queries/storage, etc.).
- **Key Features**: Download reason checking, login IP pattern analysis,
  personnel master access record analysis.

### Tech Stack

- **Language**: Python 3.12
- **Core Libraries**: `pandas`, `openpyxl` (Excel processing), `python-dotenv`
  (environment variable management), `rich` (terminal UI)

### Architecture

- **`src/main.py`**: Main entry point. Sequentially calls each inspection
  module.
- **`src/checkers/`**: Module directory containing core analysis logic such as
  `personal_file_checker.py`, `login_checker.py`, etc.
- **`src/utils.py`**: Provides common utility functions for file system
  handling, date calculations, etc.

### Setup & Execution

1. **Install Dependencies**:

   ```bash
   pip install .
   ```

2. **Environment Variable Setup**: Copy `.env.example` to create a `.env` file
   and specify `DOWNLOAD_DIR` and `SAVE_DIR` paths.

3. **Execution**:

   ```bash
   python src/main.py
   ```

### Development Conventions

- **Static Analysis**: Uses `ruff` (linting/formatting), `mypy` (type checking),
  `bandit` (security scanning).
- **Documentation**: All major functions and modules include detailed
  English-language Docstrings. Docstrings must be written in English for consistency.
- **Configuration Management**: Key settings (file paths, thresholds, etc.)
  are defined as constants at the beginning of each module.

## Changelog

- **2025-10-10**: Translated all Korean docstrings to English across all Python files (src/ and checkers/) to ensure consistency and improve maintainability.
- **2025-10-01**: Modified data count summation display and output style. Each
  checker function returns data count, main.py calculates sum, display.py
  enables markup.
- **2025-10-01**: Added Rich library (terminal UI improvement). Fixed summary
  output error by supporting `markup` parameter in `Text` class.
- **2025-10-01**: Comprehensive README.md writing. Added project overview,
  features, installation, usage, structure, development info.
