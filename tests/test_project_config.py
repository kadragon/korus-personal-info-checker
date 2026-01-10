"""
Tests for project configuration files.
"""

from pathlib import Path
import tomllib


def test_pyproject_dev_dependencies_include_pyinstaller():
    pyproject_path = Path("pyproject.toml")
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    dev_deps = data["project"]["optional-dependencies"]["dev"]
    assert any(dep.lower().startswith("pyinstaller") for dep in dev_deps)
