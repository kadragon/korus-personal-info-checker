from datetime import datetime

import pandas as pd
import pytest

from src.checkers import login_checker as lc


class TestFilterIpSwitch:
    def test_filter_ip_switch_multiple_ips(self, sample_login_df):
        # Modify sample to have multiple IPs within window
        df = sample_login_df.copy()
        df.loc[0, "접속일시"] = datetime(2023, 9, 1, 9, 0)
        df.loc[0, "IP"] = "192.168.1.1"
        df.loc[1, "접속일시"] = datetime(2023, 9, 1, 9, 30)  # within 1 hour
        df.loc[1, "IP"] = "192.168.1.2"
        df.loc[2, "접속일시"] = datetime(2023, 9, 1, 9, 45)
        df.loc[2, "IP"] = "192.168.1.3"

        result = lc._filter_ip_switch(df)
        assert len(result) == 3  # all flagged

    def test_filter_ip_switch_no_multiple_ips(self, sample_login_df):
        df = sample_login_df.copy()
        # All same IP
        df["IP"] = "192.168.1.1"

        result = lc._filter_ip_switch(df)
        assert result.empty

    def test_filter_ip_switch_none_df(self):
        with pytest.raises(ValueError):
            lc._filter_ip_switch(None)


class TestRunCheck:
    def test_run_check_with_data(self, temp_dir, sample_login_df, mocker):
        mocker.patch("src.checkers.login_checker.print_checker_header")
        mocker.patch(
            "src.utils.find_and_prepare_excel_file",
            return_value=(sample_login_df, "path"),
        )
        mocker.patch(
            "src.checkers.login_checker._filter_ip_switch", return_value=pd.DataFrame()
        )
        mocker.patch("src.utils.filter_by_time_conditions", return_value=pd.DataFrame())
        mocker.patch("src.utils.run_and_save_check")

        save_dir = temp_dir
        result = lc.run_check("download_dir", save_dir, "202309")
        assert result == len(sample_login_df)

    def test_run_check_no_data(self, temp_dir, mocker):
        mocker.patch("src.checkers.login_checker.print_checker_header")
        mocker.patch("src.utils.find_and_prepare_excel_file", return_value=(None, None))

        save_dir = temp_dir
        result = lc.run_check("download_dir", save_dir, "202309")
        assert result == 0

    def test_run_check_missing_ip_column(self, temp_dir, sample_login_df, mocker):
        mocker.patch("src.checkers.login_checker.print_checker_header")
        mocker.patch(
            "src.utils.find_and_prepare_excel_file",
            return_value=(sample_login_df.drop(columns=["IP"]), "path"),
        )

        save_dir = temp_dir
        with pytest.raises(ValueError):
            lc.run_check("download_dir", save_dir, "202309")
