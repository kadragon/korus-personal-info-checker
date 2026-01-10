"""
Tests for GitHub Actions workflows.
"""

from pathlib import Path


def test_ci_workflow_runs_quality_checks():
    workflow_path = Path(".github/workflows/ci.yml")
    assert workflow_path.exists()
    contents = workflow_path.read_text(encoding="utf-8")
    assert "ruff check src" in contents
    assert "ruff format --check" in contents
    assert "mypy src" in contents
    assert "pytest" in contents


def test_release_workflow_builds_and_releases_exe():
    workflow_path = Path(".github/workflows/release.yml")
    assert workflow_path.exists()
    contents = workflow_path.read_text(encoding="utf-8")
    assert "windows-latest" in contents
    assert "build_windows.ps1" in contents
    assert "korus-checker.exe" in contents
    assert "action-gh-release" in contents
    assert "refs/tags" in contents
    assert "generate_release_notes" in contents
