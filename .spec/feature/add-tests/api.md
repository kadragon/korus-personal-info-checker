Surface: Test runner invoked via `pytest` CLI from project root.
Signature: `pytest --cov=src --cov-report=term-missing`
Errors: Non-zero exit codes indicate failing assertions, import errors, or unmet coverage threshold (failure message includes coverage summary).
Rate/Perf: Suite expected runtime < 60 s on developer laptops; uses in-memory DataFrames and pytest tmp_path fixtures to avoid heavy I/O.
