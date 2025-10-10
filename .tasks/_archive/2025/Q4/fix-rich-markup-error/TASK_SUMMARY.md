# Fix Rich Markup Error

**Goal**: Fix the `Text(markup=True)` parameter error in the `print_summary` function in `src/display.py` to ensure summary output works normally.

**Key Changes**:
- Added `rich>=13.0.0` dependency to `pyproject.toml`.
- Installed library with `uv add rich` (version 14.1.0).

**Test and Validation**:
- Confirmed `Text(markup=True)` parameter works after Rich library installation.
- Error reproduction attempt: Previously `TypeError: Text.__init__() got an unexpected keyword argument 'markup'`, resolved after fix.

**Commit**: [Structural] Add Rich library and fix markup error
