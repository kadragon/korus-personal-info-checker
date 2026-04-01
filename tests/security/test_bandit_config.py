from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]


def test_bandit_config_excludes_tests_and_targets_src() -> None:
    pyproject = Path("pyproject.toml")
    config = tomllib.loads(pyproject.read_text())

    bandit = config["tool"]["bandit"]
    assert "src" in bandit["targets"]
    assert "tests" in bandit["exclude_dirs"]
    assert ".venv" in bandit["exclude_dirs"]
