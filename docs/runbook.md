# Runbook

## Setup

```bash
uv sync --extra dev       # install all dependencies including dev tools
cp .env.example .env      # copy env template
# Edit .env: set DOWNLOAD_DIR and SAVE_DIR to absolute paths
```

## Run

```bash
uv run korus-checker      # uses DOWNLOAD_DIR and SAVE_DIR from .env
```

The tool reads all `개인정보접속기록_*.xls*` files from `DOWNLOAD_DIR`, runs all checkers, and writes output files to `SAVE_DIR`.

## Quality Gates

Run in this order before every commit:

```bash
uv run ruff check src                               # lint
uv run ruff format --check src                      # format check
uv run mypy src                                     # type check
uv run bandit -r src                                # security scan
uv run pytest --cov=src --cov-report=term           # tests (≥80% line, ≥70% branch)
```

The pre-commit hook (`uv run pre-commit run --all-files`) runs the same chain automatically on commit.

CI (`.github/workflows/ci.yml`) runs ruff, mypy, and pytest on every push/PR to `main`.

## Sweep

**Trigger policy: manual.** Run between features or after any batch of checker changes.

```bash
bash scripts/sweep.sh         # full sweep (lint + doc drift + golden principles + harness freshness)
bash scripts/sweep.sh --quick # lint only
```

## Harness Scripts

| Script | Purpose |
|--------|---------|
| `scripts/validate-harness.sh` | Full structural validation + maturity level report |
| `scripts/sweep.sh` | Lint, doc drift, golden principle spot-check |
| `scripts/reconcile-harness.py` | Sync completed tasks.md items into backlog.md |
| `scripts/check-context-size.sh` | Warn if AGENTS.md > 200 lines |
| `scripts/sync-claude-md.sh` | Repair CLAUDE.md → @AGENTS.md (if manually broken) |
| `scripts/symlink-guard.sh` | Repair .agents/skills symlink (if manually broken) |

## Common Failure Modes

| Error | Code | Resolution |
|-------|------|------------|
| `DOWNLOAD_DIR not set` | CFG-001 | Set `DOWNLOAD_DIR` in `.env` or environment |
| `SAVE_DIR not set` | CFG-002 | Set `SAVE_DIR` in `.env` or environment |
| `Input directory not found` | FS-001 | Verify the path in `DOWNLOAD_DIR` exists |
| `No matching input files` | FS-002 | Check files are named `개인정보접속기록_*.xls*` |
| `Missing required column` | DATA-001 | Source file is missing a required Korean column; verify schema |
| `Unparseable date/time` | DATA-002 | `접속일시` column has unexpected format; check source file |

## Dependency Updates

Dependabot opens PRs for dependency updates. Before merging:

1. Confirm CI passes on the PR.
2. Check if the update resolves any open Dependabot security alert.
3. For major version bumps, read the changelog and verify no API breakage in `src/`.

## Development Environment

- Python: 3.12 (see `.python-version`)
- Package manager: `uv` (`uv sync` installs all deps)
- Pre-commit hooks: `uv run pre-commit install` to activate
