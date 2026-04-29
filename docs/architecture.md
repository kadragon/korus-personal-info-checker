# Architecture

## Pipeline

```
INPUT (xls*/xlsx files in DOWNLOAD_DIR)
  -> EXTRACT  (read_excel via xlrd/openpyxl, schema validation)
  -> TRANSFORM (normalize columns, compute derived fields)
  -> DETECT   (checker-specific business rules)
  -> OUTPUT   (write xlsx to SAVE_DIR, Rich console summary)
```

## Module Map

| Module | Role |
|--------|------|
| `src/main.py` | Orchestrator — discovers checkers, runs each, aggregates counts, prints summary |
| `src/config.py` | Constants — column names, thresholds, output naming templates |
| `src/utils.py` | File/date utilities — load_input_files(), write_output_excel(), validate_env() |
| `src/display.py` | Rich console output — tables, progress, summary panel |
| `src/checkers/download_reason_checker.py` | Detects missing, invalid, or gibberish download reasons |
| `src/checkers/login_checker.py` | Detects suspicious IP switches and after-hours logins |
| `src/checkers/personal_file_checker.py` | Detects bulk access to personnel master records |

## Checker Interface Contract

Every file in `src/checkers/` must expose:

```python
def run_check(download_dir: str, save_dir: str, reference_date: date) -> int:
    """Run this checker and write output file if findings exist.

    Returns:
        Count of records inspected (not findings — total records).
    """
```

The orchestrator (`src/main.py`) discovers checkers by importing `src/checkers/` and calling `run_check` on each. Non-int returns are treated as 0.

## Data Contract

- **Input file glob:** `개인정보접속기록_*.xls*` (both `.xls` and `.xlsx` accepted)
- **Required columns (Korean):** `사용자ID`, `접속일시`, `작업구분`, `IP주소`, `다운로드사유`
- **Output file naming:** `{checker_name}_{YYYYMMDD}.xlsx` (date = reference_date)
- **Output encoding:** UTF-8-BOM for Excel compatibility (written via `src/utils.py`)
- **Env vars:** `DOWNLOAD_DIR` (input), `SAVE_DIR` (output) — validated at startup

## Dependency Directions

```
main.py  ->  checkers/*  ->  config.py
         ->  utils.py
         ->  display.py
```

No circular imports. `config.py` imports nothing from this project.
`utils.py` and `display.py` are utilities — they do not import from `checkers/`.
