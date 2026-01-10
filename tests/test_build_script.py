"""
Tests for build scripts.
"""

from pathlib import Path


def test_build_windows_script_contains_pyinstaller_args():
    script_path = Path("scripts/build_windows.ps1")
    assert script_path.exists()
    contents = script_path.read_text(encoding="utf-8")
    assert "pyinstaller" in contents
    assert "--collect-submodules src.checkers" in contents
    assert "src.launcher" in contents
