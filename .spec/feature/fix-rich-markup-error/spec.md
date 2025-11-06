---
spec_id: SPEC-fix-rich-markup-error-1
agents:
  base_profile: profiles/python-cli.md
  project_profile: profiles/python-cli@2025-11-06.md
  catalogs:
    errors: catalogs/errors.md
deltas:
  rich_version: ">=13.0.0"
---

# Rich Markup Compatibility Fix
Intent: Ensure Rich-based summary rendering supports `Text(markup=True)` without raising constructor errors.
Scope: In: upgrade Rich dependency, verify console instantiation supports markup. Out: redesigning output formatting beyond enabling markup support.
Dependencies: [pyproject.toml], [src/display.py]

## Behaviour (GWT)
- AC-1: GIVEN the project installs dependencies WHEN `python -c "from rich.text import Text; Text('ok', markup=True)"` executes THEN no `TypeError` is raised.
- AC-2: GIVEN the CLI prints a summary panel WHEN `print_summary` runs THEN Rich renders styled text without crashing.

## Examples (Tabular)
| Case | Input | Steps | Expected |
|---|---|---|---|
| import-check | Clean venv | Install project via `pip install .` | `rich.__version__ ≥ 13.0.0` |
| summary-run | Configured `.env` | Run `python src/main.py` with mocks | Styled summary prints successfully |

## API (Summary)
Surface: Dependency declaration `rich>=13.0.0` in `pyproject.toml`; `Console(markup=True)` usage in `src/display.py`.
Signature: N/A – ensures constructor signature compatibility.
Errors: Precondition failure manifests as `TypeError: Text.__init__() got an unexpected keyword argument 'markup'`; resolution ensures absence.

## Data & State
Entities: None beyond dependency metadata.
Invariants: Rich version constraint maintained; console initialised once per run with markup enabled.

## Tracing
Spec-ID: SPEC-fix-rich-markup-error-1
Trace-To: .tasks/_archive/2025-Q4/task-2025-10-01-fix-rich-markup-error.md; pyproject.toml (Trace: SPEC-fix-rich-markup-error-1); src/display.py (Trace: SPEC-fix-rich-markup-error-1)
