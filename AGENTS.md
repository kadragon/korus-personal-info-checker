# KORUS Personal Info Checker Agent Rules

Python CLI that analyzes KORUS access logs to detect personal data misuse (suspicious downloads, bulk access, IP anomalies, personnel file access).

## Docs Index (read on demand)

| File | When to read |
|------|--------------|
| `docs/architecture.md` | Before modifying pipeline structure, adding a checker, or changing module layout |
| `docs/conventions.md` | Before writing new code, error handling, or security-sensitive logic |
| `docs/workflows.md` | When starting any implementation cycle |
| `docs/delegation.md` | Delegation routing — before spawning sub-agents or when stuck |
| `docs/eval-criteria.md` | When evaluating completed features |
| `docs/runbook.md` | For build/test/run commands and troubleshooting |

## Golden Principles

Invariants enforced mechanically. Violations block commits or CI.

1. **TDD: failing test first** — RED → GREEN → REFACTOR for every change. Reviewed at PR.
2. **Quality gates green or no merge** — ruff + mypy + bandit + pytest (≥80% line / ≥70% branch). Enforced by `.pre-commit-config.yaml` + `.github/workflows/ci.yml`.
3. **Never log PII** — columns 사용자ID, IP주소, 다운로드사유 are PII. Mask or omit in logs. Bandit + PR review.
4. **Checker contract** — every `src/checkers/*.py` exposes `run_check(download_dir, save_dir, reference_date) -> int`. Enforced by `tests/test_main.py` discovery test.
5. **Output encoding** — Excel reports use UTF-8-BOM via `src/utils.py` helpers. Covered by tests.

## Delegation

| Trigger (objective) | Delegate to | Gate |
|---------------------|-------------|------|
| Exploring a checker module not touched this session | Explore agent | Mandatory before editing |
| Same failure persists after 2 attempts | `codex:rescue` | Mandatory, blocking |
| Non-trivial plan before implementation | `codex:rescue --background --effort low` | Mandatory |

## Token Economy

1. Do not re-read a file already read this session. Check only the diff/region.
2. Do not call tools just to confirm information you already have.
3. Run independent tool calls in parallel (reads, grep + glob, etc.).
4. Delegate any analysis producing >20 lines of output to a sub-agent; return only the conclusion.
5. Do not restate what the user just said.

## Working with Existing Code

- Input files: `개인정보접속기록_*.xls*` in `DOWNLOAD_DIR`; output: `{checker_name}_{YYYYMMDD}.xlsx` in `SAVE_DIR`.
- Required columns (Korean): `사용자ID`, `접속일시`, `작업구분`, `IP주소`, `다운로드사유`.
- New checker: subclass pattern in `src/checkers/`, register automatically via `src/main.py` discovery.
- Run: `uv run korus-checker` (entry point in `pyproject.toml`).
- Env: copy `.env.example` → `.env`, set `DOWNLOAD_DIR` / `SAVE_DIR`.

## Language Policy

- Code, commits, docs: English.
- User-facing console output and Korean column names: Korean (as-is from source data).

## Maintenance

Update this file **only** when ALL of the following are true:

1. Information is not directly discoverable from code / config / manifests / docs
2. It is operationally significant — affects build, test, deploy, or runtime safety
3. It would likely cause mistakes if left undocumented
4. It is stable and not task-specific

**Never add:** architecture summaries, directory overviews, style conventions already enforced by tooling, anything already visible in the repo, or temporary / task-specific instructions.

Prefer modifying or removing outdated entries over appending. When unsure, add a short inline `TODO:` comment rather than inventing guidance.

Size budget: target ≤100 lines, hard warn >200. Move long content to `docs/*.md` and leave a pointer line here.

**Branching exception:** This is a single-maintainer repo. Direct commits to `main` are permitted. Feature branches are encouraged for multi-session work but not required.

**Context anxiety:** Prefer context resets over compaction. At the start of multi-session work, write `handoff-{feature}.md` (see `docs/workflows.md`) — not after context degrades.
