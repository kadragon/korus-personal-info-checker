"""
Tests for README content.
"""

from pathlib import Path


def test_readme_includes_run_instructions():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "uv run korus-checker" in readme
