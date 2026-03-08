from datetime import datetime

import pandas as pd
import pytest

from src import config as cfg
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
        df.loc[2, "교직원ID"] = "emp1"

        result = lc._filter_ip_switch(df)
        assert len(result) == 3  # all flagged

    def test_filter_ip_switch_includes_reason_column(self, sample_login_df):
        df = sample_login_df.copy()
        df.loc[0, "접속일시"] = datetime(2023, 9, 1, 9, 0)
        df.loc[0, "IP"] = "192.168.1.1"
        df.loc[1, "접속일시"] = datetime(2023, 9, 1, 9, 30)
        df.loc[1, "IP"] = "192.168.1.2"
        df.loc[2, "접속일시"] = datetime(2023, 9, 1, 9, 45)
        df.loc[2, "IP"] = "192.168.1.3"
        df.loc[2, "교직원ID"] = "emp1"

        result = lc._filter_ip_switch(df)
        assert cfg.COL_ESTIMATED_REASON in result.columns
        assert (result[cfg.COL_ESTIMATED_REASON] != "").all()

    def test_filter_ip_switch_empty_result_has_reason_column(self, sample_login_df):
        df = sample_login_df.copy()
        df["IP"] = "192.168.1.1"  # All same IP → no flags
        result = lc._filter_ip_switch(df)
        assert result.empty
        assert cfg.COL_ESTIMATED_REASON in result.columns

    def test_filter_ip_switch_no_multiple_ips(self, sample_login_df):
        df = sample_login_df.copy()
        # All same IP
        df["IP"] = "192.168.1.1"

        result = lc._filter_ip_switch(df)
        assert result.empty

    def test_filter_ip_switch_none_df(self):
        with pytest.raises(ValueError):
            lc._filter_ip_switch(None)


class TestEstimateIpSwitchReason:
    def test_empty_input_has_reason_column(self):
        empty_df = pd.DataFrame(
            columns=[cfg.COL_EMPLOYEE_ID, cfg.COL_ACCESS_TIME, cfg.COL_IP]
        )
        result = lc._estimate_ip_switch_reason(empty_df)
        assert cfg.COL_ESTIMATED_REASON in result.columns
        assert result.empty

    def test_same_24_subnet_classified_as_pc_change(self):
        df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1", "emp1", "emp1"],
                cfg.COL_ACCESS_TIME: [
                    datetime(2023, 9, 1, 9, 0),
                    datetime(2023, 9, 1, 9, 30),
                    datetime(2023, 9, 1, 9, 45),
                ],
                cfg.COL_IP: ["192.168.1.10", "192.168.1.20", "192.168.1.30"],
            }
        )
        result = lc._estimate_ip_switch_reason(df)
        reasons = result[cfg.COL_ESTIMATED_REASON].unique()
        assert len(reasons) == 1
        assert reasons[0] == cfg.REASON_SAME_SUBNET

    def test_same_16_different_24_classified_as_campus_move(self):
        df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1", "emp1", "emp1"],
                cfg.COL_ACCESS_TIME: [
                    datetime(2023, 9, 1, 9, 0),
                    datetime(2023, 9, 1, 9, 30),
                    datetime(2023, 9, 1, 9, 45),
                ],
                cfg.COL_IP: ["10.1.1.10", "10.1.2.20", "10.1.3.30"],
            }
        )
        result = lc._estimate_ip_switch_reason(df)
        reasons = result[cfg.COL_ESTIMATED_REASON].unique()
        assert len(reasons) == 1
        assert reasons[0] == cfg.REASON_CAMPUS_MOVE

    def test_different_16_classified_as_external_network(self):
        df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1", "emp1", "emp1"],
                cfg.COL_ACCESS_TIME: [
                    datetime(2023, 9, 1, 9, 0),
                    datetime(2023, 9, 1, 9, 30),
                    datetime(2023, 9, 1, 9, 45),
                ],
                cfg.COL_IP: ["192.168.1.10", "10.0.1.20", "172.16.1.30"],
            }
        )
        result = lc._estimate_ip_switch_reason(df)
        reasons = result[cfg.COL_ESTIMATED_REASON].unique()
        assert len(reasons) == 1
        assert reasons[0] == cfg.REASON_EXTERNAL_NETWORK

    def test_fast_switch_appends_suffix(self):
        df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1", "emp1", "emp1"],
                cfg.COL_ACCESS_TIME: [
                    datetime(2023, 9, 1, 9, 0),
                    datetime(2023, 9, 1, 9, 3),
                    datetime(2023, 9, 1, 9, 45),
                ],
                cfg.COL_IP: ["192.168.1.10", "192.168.1.20", "192.168.1.30"],
            }
        )
        result = lc._estimate_ip_switch_reason(df)
        reasons = result[cfg.COL_ESTIMATED_REASON].unique()
        assert len(reasons) == 1
        assert cfg.REASON_FAST_SWITCH_SUFFIX in reasons[0]
        assert cfg.REASON_SAME_SUBNET in reasons[0]

    def test_nan_ip_skipped_no_crash(self):
        df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1", "emp1", "emp1"],
                cfg.COL_ACCESS_TIME: [
                    datetime(2023, 9, 1, 9, 0),
                    datetime(2023, 9, 1, 9, 30),
                    datetime(2023, 9, 1, 9, 45),
                ],
                cfg.COL_IP: ["192.168.1.10", float("nan"), "192.168.1.30"],
            }
        )
        result = lc._estimate_ip_switch_reason(df)
        assert cfg.COL_ESTIMATED_REASON in result.columns
        assert (result[cfg.COL_ESTIMATED_REASON] != "").all()

    def test_malformed_ip_skipped_no_crash(self):
        df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1", "emp1", "emp1"],
                cfg.COL_ACCESS_TIME: [
                    datetime(2023, 9, 1, 9, 0),
                    datetime(2023, 9, 1, 9, 30),
                    datetime(2023, 9, 1, 9, 45),
                ],
                cfg.COL_IP: ["192.168.1.10", "10.1", "192.168.1.30"],
            }
        )
        result = lc._estimate_ip_switch_reason(df)
        assert cfg.COL_ESTIMATED_REASON in result.columns
        assert (result[cfg.COL_ESTIMATED_REASON] != "").all()

    def test_per_cluster_reason_independent(self):
        """Two separate time clusters for one employee get independent reasons."""
        df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1"] * 6,
                cfg.COL_ACCESS_TIME: [
                    # Cluster 1: same /24 subnet, 9:00-9:45
                    datetime(2023, 9, 1, 9, 0),
                    datetime(2023, 9, 1, 9, 30),
                    datetime(2023, 9, 1, 9, 45),
                    # Cluster 2: different /16, 15:00-15:45 (gap > 1 hour)
                    datetime(2023, 9, 1, 15, 0),
                    datetime(2023, 9, 1, 15, 30),
                    datetime(2023, 9, 1, 15, 45),
                ],
                cfg.COL_IP: [
                    "192.168.1.10",
                    "192.168.1.20",
                    "192.168.1.30",
                    "10.0.1.10",
                    "172.16.1.20",
                    "192.168.1.40",
                ],
            }
        )
        result = lc._estimate_ip_switch_reason(df)
        cluster1 = result[result[cfg.COL_ACCESS_TIME] < datetime(2023, 9, 1, 12, 0)]
        cluster2 = result[result[cfg.COL_ACCESS_TIME] > datetime(2023, 9, 1, 12, 0)]
        assert cluster1[cfg.COL_ESTIMATED_REASON].unique()[0] == cfg.REASON_SAME_SUBNET
        assert (
            cluster2[cfg.COL_ESTIMATED_REASON].unique()[0]
            == cfg.REASON_EXTERNAL_NETWORK
        )

    def test_multi_employee_different_classifications(self):
        """Two employees get independently classified."""
        df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1", "emp1", "emp1", "emp2", "emp2", "emp2"],
                cfg.COL_ACCESS_TIME: [
                    datetime(2023, 9, 1, 9, 0),
                    datetime(2023, 9, 1, 9, 30),
                    datetime(2023, 9, 1, 9, 45),
                    datetime(2023, 9, 1, 9, 0),
                    datetime(2023, 9, 1, 9, 30),
                    datetime(2023, 9, 1, 9, 45),
                ],
                cfg.COL_IP: [
                    "192.168.1.10",
                    "192.168.1.20",
                    "192.168.1.30",
                    "10.0.1.10",
                    "172.16.1.20",
                    "192.168.1.40",
                ],
            }
        )
        result = lc._estimate_ip_switch_reason(df)
        emp1 = result[result[cfg.COL_EMPLOYEE_ID] == "emp1"]
        emp2 = result[result[cfg.COL_EMPLOYEE_ID] == "emp2"]
        assert emp1[cfg.COL_ESTIMATED_REASON].unique()[0] == cfg.REASON_SAME_SUBNET
        assert emp2[cfg.COL_ESTIMATED_REASON].unique()[0] == cfg.REASON_EXTERNAL_NETWORK

    def test_same_ip_rapid_logins_no_fast_switch(self):
        """Same IP within 5 min should NOT trigger fast-switch suffix."""
        df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1", "emp1", "emp1"],
                cfg.COL_ACCESS_TIME: [
                    datetime(2023, 9, 1, 9, 0),
                    datetime(2023, 9, 1, 9, 2),
                    datetime(2023, 9, 1, 9, 45),
                ],
                cfg.COL_IP: ["192.168.1.10", "192.168.1.10", "192.168.1.20"],
            }
        )
        result = lc._estimate_ip_switch_reason(df)
        reason = result[cfg.COL_ESTIMATED_REASON].unique()[0]
        assert cfg.REASON_FAST_SWITCH_SUFFIX not in reason

    def test_fast_switch_not_triggered_above_threshold(self):
        """Different IPs but gap > 5 min should NOT trigger fast-switch suffix."""
        df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1", "emp1", "emp1"],
                cfg.COL_ACCESS_TIME: [
                    datetime(2023, 9, 1, 9, 0),
                    datetime(2023, 9, 1, 9, 6),
                    datetime(2023, 9, 1, 9, 45),
                ],
                cfg.COL_IP: ["192.168.1.10", "192.168.1.20", "192.168.1.30"],
            }
        )
        result = lc._estimate_ip_switch_reason(df)
        reason = result[cfg.COL_ESTIMATED_REASON].unique()[0]
        assert cfg.REASON_FAST_SWITCH_SUFFIX not in reason


class TestFilterIpSwitchNaN:
    def test_nan_ip_excluded_from_unique_count(self, sample_login_df):
        """NaN IPs should not count toward the unique IP threshold."""
        df = sample_login_df.copy()
        df.loc[0, "접속일시"] = datetime(2023, 9, 1, 9, 0)
        df.loc[0, "IP"] = "192.168.1.1"
        df.loc[1, "접속일시"] = datetime(2023, 9, 1, 9, 30)
        df.loc[1, "IP"] = "192.168.1.2"
        df.loc[2, "접속일시"] = datetime(2023, 9, 1, 9, 45)
        df.loc[2, "IP"] = float("nan")
        df.loc[2, "교직원ID"] = "emp1"

        result = lc._filter_ip_switch(df)
        # Only 2 real unique IPs (< threshold of 3), should not be flagged
        assert result.empty


class TestRunCheck:
    def test_run_check_with_data(self, temp_dir, sample_login_df, mocker):
        mocker.patch("src.checkers.login_checker.print_checker_header")
        mocker.patch(
            "src.checkers.login_checker.find_and_prepare_excel_file",
            return_value=(sample_login_df, "path"),
        )
        mocker.patch(
            "src.checkers.login_checker._filter_ip_switch", return_value=pd.DataFrame()
        )
        mocker.patch(
            "src.checkers.login_checker.filter_by_time_conditions",
            return_value=pd.DataFrame(),
        )
        mocker.patch("src.checkers.login_checker.run_and_save_check")

        save_dir = temp_dir
        result = lc.run_check("download_dir", save_dir, "202309")
        assert result == len(sample_login_df)

    def test_run_check_no_data(self, temp_dir, mocker):
        mocker.patch("src.checkers.login_checker.print_checker_header")
        mocker.patch(
            "src.checkers.login_checker.find_and_prepare_excel_file",
            return_value=(None, None),
        )

        save_dir = temp_dir
        result = lc.run_check("download_dir", save_dir, "202309")
        assert result == 0

    def test_run_check_missing_ip_column(self, temp_dir, sample_login_df, mocker):
        mocker.patch("src.checkers.login_checker.print_checker_header")
        mocker.patch(
            "src.checkers.login_checker.find_and_prepare_excel_file",
            return_value=(sample_login_df.drop(columns=["IP"]), "path"),
        )

        save_dir = temp_dir
        with pytest.raises(ValueError):
            lc.run_check("download_dir", save_dir, "202309")
