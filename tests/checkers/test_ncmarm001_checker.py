"""Tests for ncmarm001_checker: unauthorized permission grant detection."""

import pandas as pd
import pytest

import src.checkers.ncmarm001_checker as nc
from src import config as cfg


class TestLoadAllowlist:
    def test_returns_empty_set_when_env_unset(self, monkeypatch):
        monkeypatch.delenv("NCMARM001_AUTHORIZED_IDS", raising=False)
        assert nc._load_allowlist() == set()

    def test_parses_comma_separated_ids(self, monkeypatch):
        monkeypatch.setenv("NCMARM001_AUTHORIZED_IDS", "10001234,10005678")
        assert nc._load_allowlist() == {"10001234", "10005678"}

    def test_trims_whitespace(self, monkeypatch):
        monkeypatch.setenv("NCMARM001_AUTHORIZED_IDS", " 10001234 , 10005678 ")
        assert nc._load_allowlist() == {"10001234", "10005678"}

    def test_drops_empty_tokens(self, monkeypatch):
        monkeypatch.setenv("NCMARM001_AUTHORIZED_IDS", "10001234,,10005678,")
        assert nc._load_allowlist() == {"10001234", "10005678"}


class TestFilterUnauthorizedGrants:
    def test_raises_when_registrant_id_column_missing(self):
        df = pd.DataFrame({"other_col": ["A"]})
        with pytest.raises(ValueError, match=cfg.COL_REGISTRANT_ID):
            nc._filter_unauthorized_grants(df, {"10001234"})

    def test_returns_rows_not_in_allowlist(self):
        df = pd.DataFrame({cfg.COL_REGISTRANT_ID: ["10001234", "10005678", "10009999"]})
        result = nc._filter_unauthorized_grants(df, {"10001234"})
        assert list(result[cfg.COL_REGISTRANT_ID]) == ["10005678", "10009999"]

    def test_treats_ids_as_strings(self):
        df = pd.DataFrame({cfg.COL_REGISTRANT_ID: [10001234, 10005678]})
        result = nc._filter_unauthorized_grants(df, {"10001234"})
        assert len(result) == 1
        assert str(result[cfg.COL_REGISTRANT_ID].iloc[0]) == "10005678"

    def test_empty_allowlist_returns_all_rows(self):
        df = pd.DataFrame({cfg.COL_REGISTRANT_ID: ["10001234", "10005678"]})
        result = nc._filter_unauthorized_grants(df, set())
        assert len(result) == 2

    def test_normalizes_float_ids_from_excel(self):
        # Excel reads numeric cols with blanks as float; strip trailing .0.
        df = pd.DataFrame({cfg.COL_REGISTRANT_ID: [10001234.0, 10005678.0]})
        result = nc._filter_unauthorized_grants(df, {"10001234"})
        assert len(result) == 1


class TestRunCheck:
    def test_returns_0_when_no_data(self, temp_dir, monkeypatch, mocker):
        monkeypatch.delenv("NCMARM001_AUTHORIZED_IDS", raising=False)
        mocker.patch("src.checkers.ncmarm001_checker.print_checker_header")
        mocker.patch(
            "src.checkers.ncmarm001_checker.find_and_prepare_excel_file",
            return_value=(None, None),
        )

        result = nc.run_check("download_dir", temp_dir, "202603")
        assert result == 0

    def test_returns_len_df_and_calls_run_and_save_check(
        self, temp_dir, sample_ncmarm001_df, monkeypatch, mocker
    ):
        monkeypatch.delenv("NCMARM001_AUTHORIZED_IDS", raising=False)
        mocker.patch("src.checkers.ncmarm001_checker.print_checker_header")
        mocker.patch("src.checkers.ncmarm001_checker.print_info")
        mocker.patch(
            "src.checkers.ncmarm001_checker.find_and_prepare_excel_file",
            return_value=(sample_ncmarm001_df, "merged_path"),
        )
        mock_run_and_save = mocker.patch(
            "src.checkers.ncmarm001_checker.run_and_save_check"
        )

        result = nc.run_check("download_dir", temp_dir, "202603")

        assert result == len(sample_ncmarm001_df)
        mock_run_and_save.assert_called_once()
        _, kwargs = mock_run_and_save.call_args
        assert "승인없는권한상승" in kwargs["save_path"]
        assert kwargs["result_description"] == "승인 없는 권한 상승"
