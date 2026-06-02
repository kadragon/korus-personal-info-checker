"""Regression tests for scripts/validate-harness.sh maturity level logic.

Focus: WARN count must NOT gate maturity levels — only FAIL does.
See tasks.md PR #109 items and docs/runbook.md for script purpose.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


def _find_bash() -> str | None:
    """Find a bash binary that can execute scripts and navigate Windows paths.

    On Linux/macOS, the system bash is used.
    On Windows, Git Bash is preferred over WSL bash because:
    - Git Bash understands ``C:/...`` (forward-slash) Windows paths for ``cd``.
    - ``subprocess.run(["bash", ...])`` may resolve to WSL bash first in PATH,
      but WSL bash cannot access certain Windows temp paths via ``/mnt/c/``.
    """
    if sys.platform != "win32":
        return shutil.which("bash")
    candidates = [
        r"C:\Program Files\Git\usr\bin\bash.exe",
        r"C:\Program Files (x86)\Git\usr\bin\bash.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\usr\bin\bash.exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return shutil.which("bash")


_BASH = _find_bash()

pytestmark = pytest.mark.skipif(
    _BASH is None, reason="bash not available in this environment"
)


def _scaffold(root: Path) -> None:
    """Build a minimal structurally-complete Level 3 harness tree under *root*.

    Level 1 requirements:
      - AGENTS.md (≤100 lines, golden principles, delegation, maintenance, docs refs)
      - CLAUDE.md == "@AGENTS.md"
      - docs/{architecture,runbook}.md + backlog.md

    Level 2 adds:
      - .github/workflows/ci.yml (CI presence)
      - docs/delegation.md (reference integrity)

    Level 3 adds:
      - .claude/settings.json with PostToolUse hook
      - .pre-commit-config.yaml

    All six docs/ files are present so the base scaffold has 0 WARNs.
    """
    root.mkdir(parents=True, exist_ok=True)

    # AGENTS.md — satisfies checks 2-5, 10; references five docs/ in backticks.
    # docs/eval-criteria.md is intentionally NOT backtick-quoted: check 1 warns if
    # it is missing, but check 3 (reference integrity) does not fail for it.
    # This lets tests delete docs/eval-criteria.md to inject exactly one benign WARN
    # without triggering a FAIL.
    agents_md = """\
# Test Harness

## Docs Index (read on demand)

| File | When to read |
|------|--------------|
| `docs/architecture.md` | Before modifying pipeline |
| `docs/conventions.md` | Before writing new code |
| `docs/workflows.md` | When starting any implementation |
| `docs/delegation.md` | Before spawning sub-agents |
| docs/eval-criteria.md | When evaluating completed features |
| `docs/runbook.md` | For build/test/run commands |

## Golden Principles

1. TDD: failing test first.
2. Quality gates green or no merge.
3. Never log PII.
4. Checker contract enforced.
5. Output encoding consistent.

## Delegation

| Trigger | Delegate to | Gate |
|---------|-------------|------|
| Stuck 2+ attempts | codex:rescue | Mandatory |

## Working with Existing Code

Placeholder section.

## Language Policy

Code: English. Output: Korean.

## Maintenance

Update this file only when ALL of the following are true:

1. Information not directly discoverable from code.
2. Operationally significant.
3. Would likely cause mistakes if undocumented.
4. Stable and not task-specific.

Never add architecture summaries or style conventions enforced by tooling.
"""
    (root / "AGENTS.md").write_text(agents_md, encoding="utf-8")

    # CLAUDE.md — sync B invariant
    (root / "CLAUDE.md").write_text("@AGENTS.md", encoding="utf-8")

    # backlog.md — sync D-1 schema
    backlog_md = """\
# Backlog

## Security

- [ ] Monitor Pygments for patch when available.
"""
    (root / "backlog.md").write_text(backlog_md, encoding="utf-8")

    # docs/ — all six required by reference integrity + level gates
    docs = root / "docs"
    docs.mkdir()
    for name in (
        "architecture.md",
        "conventions.md",
        "workflows.md",
        "delegation.md",
        "eval-criteria.md",
        "runbook.md",
    ):
        (docs / name).write_text(f"# {name}\n\nPlaceholder.\n", encoding="utf-8")

    # .github/workflows/ — CI presence (Level 2)
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: CI\n", encoding="utf-8")

    # .claude/settings.json — PostToolUse hook (Level 3)
    claude_dir = root / ".claude"
    claude_dir.mkdir()
    settings = {"hooks": {"PostToolUse": [{"matcher": "*", "hooks": []}]}}
    (claude_dir / "settings.json").write_text(
        json.dumps(settings, indent=2), encoding="utf-8"
    )

    # .pre-commit-config.yaml — pre-commit presence (Level 3)
    (root / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")

    # .agents/skills — git text-symlink (sync E; Windows-safe)
    agents_dir = root / ".agents"
    agents_dir.mkdir()
    (agents_dir / "skills").write_text("../.claude/skills", encoding="utf-8")


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    # Use forward-slash Windows paths (C:/...) — Git Bash accepts them for
    # both the script argument and the PROJ_DIR passed to ``cd``.
    assert _BASH is not None, (
        "bash not found; test should have been skipped by pytestmark"
    )
    script = str(REPO_ROOT / "scripts" / "validate-harness.sh").replace("\\", "/")
    root_arg = str(root).replace("\\", "/")
    return subprocess.run(
        [_BASH, script, root_arg],
        capture_output=True,
        text=True,
    )


class TestWarnDoesNotGateLevel:
    """WARN count must not downgrade maturity levels — only FAIL does."""

    def test_level3_with_zero_warns(self, tmp_path: Path) -> None:
        """Fully-complete scaffold (0 WARN, 0 FAIL) reports LEVEL 3."""
        _scaffold(tmp_path)
        result = _run(tmp_path)
        assert "LEVEL 3" in result.stdout, (
            f"Expected LEVEL 3 for a clean scaffold. stdout:\n{result.stdout}"
        )
        assert "WARN: 0" in result.stdout

    def test_level3_with_one_benign_warn(self, tmp_path: Path) -> None:
        """A benign WARN (missing optional doc) must NOT drop the level to 2.

        This is the regression case for tasks.md PR #109:
          'validate-harness.sh: Level 3 WARN gate may be too strict'

        Before the fix: script printed LEVEL 2 when WARN > 0 → this test FAILED.
        After the fix:  script prints LEVEL 3 regardless of WARN count → PASSES.
        """
        _scaffold(tmp_path)
        # Remove docs/eval-criteria.md to inject exactly one benign WARN.
        # Check 1 warns "docs/eval-criteria.md missing" (not fail).
        # Check 3 does NOT fail for it — the scaffold's AGENTS.md deliberately
        # omits backticks around docs/eval-criteria.md so it is not a backtick
        # reference and reference integrity is unaffected.
        (tmp_path / "docs" / "eval-criteria.md").unlink()

        result = _run(tmp_path)
        assert "WARN: 1" in result.stdout, (
            f"Expected exactly 1 WARN. stdout:\n{result.stdout}"
        )
        assert "LEVEL 3" in result.stdout, (
            "WARN must not gate Level 3 — only FAIL should downgrade levels.\n"
            f"stdout:\n{result.stdout}"
        )

    def test_fail_still_downgrades_all_levels(self, tmp_path: Path) -> None:
        """A FAIL (e.g. CLAUDE.md not pure pointer) drops to LEVEL 0."""
        _scaffold(tmp_path)
        # Break sync B invariant → FAIL
        (tmp_path / "CLAUDE.md").write_text(
            "@AGENTS.md\nextra line\n", encoding="utf-8"
        )

        result = _run(tmp_path)
        assert "FAIL" in result.stdout
        # Should NOT reach Level 2 or 3
        assert "LEVEL 3" not in result.stdout
        assert "LEVEL 2" not in result.stdout
