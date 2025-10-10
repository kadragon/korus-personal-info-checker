from datetime import datetime

import pandas as pd
import pytest

from src.checkers import download_reason_checker as drc


class TestUniqueCharCountBelow5:
    def test_unique_char_count_below_5_true(self):
        assert drc._unique_char_count_below_5("asdfg")
        assert drc._unique_char_count_below_5("12345")

    def test_unique_char_count_below_5_false(self):
        assert not drc._unique_char_count_below_5("research project")
        assert not drc._unique_char_count_below_5("valid reason")

    def test_unique_char_count_below_5_nan(self):
        assert not drc._unique_char_count_below_5(pd.NA)


class TestCheckDownloadSayu:
    def test_check_download_sayu_invalid_reasons(self, sample_download_df):
        df = sample_download_df.copy()
        df.loc[0, "다운로드사유"] = "asdfg"  # invalid
        df.loc[1, "다운로드사유"] = "research"  # valid

        result = drc._check_download_sayu(df)
        assert len(result) == 1
        assert result.iloc[0]["교직원ID"] == "emp1"

    def test_check_download_sayu_missing_column(self, sample_download_df):
        df = sample_download_df.drop(columns=["다운로드사유"])

        with pytest.raises(ValueError):
            drc._check_download_sayu(df)


class TestFilterHighDownloadUsers:
    def test_filter_high_download_users_above_threshold(self, sample_download_df):
        df = sample_download_df.copy()
        df.loc[0, "다운로드데이터수(건)"] = 150  # above 100

        result = drc._filter_high_download_users(df)
        assert len(result) == 1

    def test_filter_high_download_users_below_threshold(self, sample_download_df):
        df = sample_download_df.copy()
        df["다운로드데이터수(건)"] = 50  # below

        result = drc._filter_high_download_users(df)
        assert result.empty

    def test_filter_high_download_users_missing_column(self, sample_download_df):
        df = sample_download_df.drop(columns=["다운로드데이터수(건)"])

        with pytest.raises(ValueError):
            drc._filter_high_download_users(df)


class TestFilterHighFreqDownload:
    def test_filter_high_freq_download_high_freq(self, sample_download_df):
        df = sample_download_df.copy()
        # Add multiple downloads within 1 hour
        for i in range(20):
            new_row = df.iloc[0].copy()
            new_row["접속일시"] = datetime(2023, 9, 1, 10, i)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        result = drc._filter_high_freq_download(df)
        assert len(result) > 0

    def test_filter_high_freq_download_low_freq(self, sample_download_df):
        result = drc._filter_high_freq_download(sample_download_df)
        assert result.empty

    def test_filter_high_freq_download_none_df(self):
        with pytest.raises(ValueError):
            drc._filter_high_freq_download(None)


class TestRunCheck:
    def test_run_check_with_data(self, temp_dir, sample_download_df, mocker):
        mocker.patch("src.checkers.download_reason_checker.print_checker_header")
        mocker.patch(
            "src.utils.find_and_prepare_excel_file",
            return_value=(sample_download_df, "path"),
        )
        mocker.patch(
            "src.checkers.download_reason_checker._check_download_sayu",
            return_value=pd.DataFrame(),
        )
        mocker.patch(
            "src.checkers.download_reason_checker._filter_high_download_users",
            return_value=pd.DataFrame(),
        )
        mocker.patch(
            "src.checkers.download_reason_checker._filter_high_freq_download",
            return_value=pd.DataFrame(),
        )
        mocker.patch("src.utils.filter_by_time_conditions", return_value=pd.DataFrame())
        mocker.patch("src.utils.run_and_save_check")

        save_dir = temp_dir
        result = drc.run_check("download_dir", save_dir, "202309")
        assert result == len(sample_download_df)

    def test_run_check_no_data(self, temp_dir, mocker):
        mocker.patch("src.checkers.download_reason_checker.print_checker_header")
        mocker.patch("src.utils.find_and_prepare_excel_file", return_value=(None, None))

        save_dir = temp_dir
        result = drc.run_check("download_dir", save_dir, "202309")
        assert result == 0
