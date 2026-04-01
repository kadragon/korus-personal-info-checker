import tomllib
from pathlib import Path


def test_bandit_config_excludes_tests_and_targets_src() -> None:
    with Path("pyproject.toml").open("rb") as f:
        config = tomllib.load(f)

    bandit = config["tool"]["bandit"]
    assert "src" in bandit["targets"]
    assert "tests" in bandit["exclude_dirs"]
    assert ".venv" in bandit["exclude_dirs"]
