---
spec_id: SPEC-write-readme-1
agents:
  base_profile: profiles/python-cli.md
  project_profile: profiles/python-cli@2025-11-06.md
deltas: {}
---

# README Overhaul
Intent: Provide comprehensive English documentation so operators can install and run korus-personal-info-checker confidently.
Scope: In: rewrite `README.md` with project overview, setup, usage, structure, development practices. Out: generating additional guides or API references.
Dependencies: [README.md], [src/main.py], [.env.example], [pyproject.toml]

## Behaviour (GWT)
- AC-1: GIVEN a new contributor WHEN they read `README.md` THEN they can install dependencies and configure `.env` without needing external context.
- AC-2: GIVEN an operator following the usage section WHEN they execute `python src/main.py` THEN the described behaviour matches runtime expectations (environment variables, outputs).

## Examples (Tabular)
| Case | Input | Steps | Expected |
|---|---|---|---|
| install-guide | Fresh environment | Follow README Install section | Project installs via `pip install .` |
| usage-guide | Configured `.env` | Follow Usage steps | CLI runs, reports stored under SAVE_DIR |

## API (Summary)
Surface: Markdown README covering overview, features, installation, configuration, execution, structure, development conventions.
Signature: N/A – narrative documentation.
Errors: Missing setup details should be caught and amended; doc must stay in sync with environment variables and dependencies.

## Data & State
Entities: None; documentation only.
Invariants: README remains authoritative for setup; language set to English per documentation policy.

## Tracing
Spec-ID: SPEC-write-readme-1
Trace-To: .tasks/_archive/2025-Q4/task-2025-10-01-write-readme.md; README.md (Trace: SPEC-write-readme-1)
