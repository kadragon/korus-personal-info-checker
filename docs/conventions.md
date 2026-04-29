# Conventions

## Naming

- Snake_case for all Python identifiers.
- `_` prefix for module-private helpers (not enforced by tools, but enforced at PR).
- Output column names: Korean (must match source data column names exactly).
- Constants in `src/config.py`: `UPPER_SNAKE_CASE`, prefixed by category (`COL_`, `THRESHOLD_`, `DIR_`, etc.).

## Docstrings

Google-style English for all public functions and classes:

```python
def run_check(download_dir: str, save_dir: str, reference_date: date) -> int:
    """Run this checker and write output file if findings exist.

    Args:
        download_dir: Path to directory containing input xls* files.
        save_dir: Path to directory where output xlsx is written.
        reference_date: Date used to name the output file.

    Returns:
        Count of records inspected.
    """
```

Private helpers need one-line docstrings only if the purpose is non-obvious.

## Error Handling

### Error Catalog

| Code | Category | Meaning | Exit code |
|------|----------|---------|-----------|
| CFG-001 | Configuration | DOWNLOAD_DIR not set | 1 |
| CFG-002 | Configuration | SAVE_DIR not set | 1 |
| CFG-003 | Configuration | Invalid env var value | 1 |
| FS-001 | File System | Input directory not found | 2 |
| FS-002 | File System | No matching input files | 2 |
| FS-003 | File System | Cannot write output directory | 2 |
| FS-004 | File System | Input file read error | 2 |
| DATA-001 | Data | Missing required column | 3 |
| DATA-002 | Data | Unparseable date/time value | 3 |
| DATA-003 | Data | Empty input file | 3 |
| DATA-004 | Data | Schema version mismatch | 3 |
| RT-001 | Runtime | Unexpected pandas error | 4 |
| RT-002 | Runtime | Output write failure | 4 |
| RT-003 | Runtime | Checker raised unexpected exception | 4 |

Exit codes: 0 success, 1 config, 2 filesystem, 3 data, 4 runtime, 5 unexpected.

### Logging Pattern

- `logging.error()` — fatal; always results in non-zero exit.
- `logging.warning()` — non-fatal; checker skips the record and continues.
- `logging.info()` — progress milestones.
- `logging.debug()` — dev-only; never committed with `level=DEBUG` as default.

## PIPA / Security Conventions

- **Never log PII.** The columns `사용자ID`, `IP주소`, `다운로드사유` are personal information. Do not include raw values in log messages. Mask with `***` if a value must appear.
- **Path traversal.** Validate that `DOWNLOAD_DIR` and `SAVE_DIR` are absolute paths and do not contain `..` before use. `src/utils.py` handles this.
- **No unsafe deserialization.** Never load user-supplied data with Python's native binary object serialization formats. Use pandas / openpyxl for Excel files only.
- **No weak hashes.** Do not use MD5 or SHA-1 for any integrity or comparison purpose; prefer SHA-256 if hashing is needed.
- **Dependency security.** Run `uv run bandit -r src` before every commit. Dependabot handles version updates; do not downgrade packages to resolve alerts without checking impact.

## What Tooling Already Enforces

Do not re-document these — the linters are the source of truth:

- Import order, unused imports, whitespace: `ruff`
- Type correctness: `mypy` (strict on public APIs)
- Security patterns: `bandit`
- Markdown lint: `markdownlint`
