import configparser
from pathlib import Path

import yaml


def test_bandit_config_excludes_tests_and_targets_src() -> None:
    parser = configparser.ConfigParser()
    parser.read(".bandit")

    bandit_section = parser["bandit"]
    assert bandit_section["configfile"] == "bandit.yaml"
    assert bandit_section["targets"].strip() == "src"

    config_path = Path("bandit.yaml")
    config = yaml.safe_load(config_path.read_text())

    exclude_dirs = config.get("exclude_dirs", [])
    assert "tests" in exclude_dirs
    assert any(entry.endswith("tests/*") for entry in exclude_dirs)
    assert ".venv" in exclude_dirs
