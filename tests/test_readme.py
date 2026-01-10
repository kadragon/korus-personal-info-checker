"""
Tests for README content.
"""

from pathlib import Path


def test_readme_includes_windows_build_instructions():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "build_windows.ps1" in readme
    assert "korus-checker.exe" in readme
