# Workflows

## TDD Cycle (Constitution)

Every change follows RED → GREEN → REFACTOR:

1. **RED** — Write a failing test that specifies the new behavior. Run `uv run pytest` and confirm failure.
2. **GREEN** — Write the minimum code to make the test pass. Do not over-engineer.
3. **REFACTOR** — Clean up without changing behavior. All tests must still pass.

No production code without a failing test first. This applies to bug fixes, new features, and refactors.

## Adding a New Checker

1. Create `tests/checkers/test_{name}_checker.py` with the RED test first.
2. Create `src/checkers/{name}_checker.py` exposing `run_check(download_dir, save_dir, reference_date) -> int`.
3. The orchestrator (`src/main.py`) auto-discovers checkers — no manual registration needed.
4. Run quality gates: `uv run ruff check src && uv run mypy src && uv run bandit -r src && uv run pytest --cov=src --cov-report=term`.
5. Commit with `[FEAT] Add {name} checker`.

## Sprint Flow (backlog → tasks → done)

1. Pick a `[ ]` item from `backlog.md` and promote it to `[>]`.
2. Copy schema from `references/tasks-template.md` (at `/Users/kadragon/.claude/plugins/cache/cc-plugins/kadragon-tools/1.6.2/skills/harness-init/references/tasks-template.md`) into `tasks.md` at repo root.
3. Implement via TDD cycle above.
4. When done: set `tasks.md` `status: done`. `harness-sync` reconciles on next session.

## Handoff (multi-session work)

At the **start** of a multi-session feature, create `handoff-{feature}.md` at repo root:

```markdown
# Handoff: {feature name}

## Objective
{What we're trying to accomplish}

## State at handoff
{What's done, what's in progress, what's blocked}

## Next action
{Exact next step for the new session}

## Boundaries
{What files / modules are in scope; what to leave alone}
```

Write the handoff when you start, not after context degrades. Delete the file when the feature is committed and tested.

## Context Anxiety

Prefer a context reset over compaction. If the session is getting long:

1. Write or update `handoff-{feature}.md` with current state.
2. Note the last completed test ID and the next failing test to write.
3. Start a fresh session pointing at the handoff file.

## Quality Gate Sequence

Run in this order (each gate's output informs the next):

```bash
uv run ruff check src          # lint
uv run ruff format --check src # format
uv run mypy src                # types
uv run bandit -r src           # security
uv run pytest --cov=src --cov-report=term  # tests (≥80% line, ≥70% branch)
```

All five must be green before a commit. The pre-commit hook runs the same chain automatically.
