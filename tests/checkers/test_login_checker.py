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


class TestFilterIpSwitchFreeze:
    """Golden characterization — freezes detection output (flagged rows AND the
    derived 사유추정/위험도/고유IP수/고유서브넷수 columns) so the vectorized
    rewrite cannot drift. PIPA: detection output must stay bit-identical.

    Threshold = 3 distinct IPs within a 1-hour window (LOGIN_IP_SWITCH_MIN_IPS).
    """

    def _frame(self) -> pd.DataFrame:
        rows = [
            # E1: 3 distinct private /16s within 1h, 20-min gaps -> flagged.
            ("E1", datetime(2026, 5, 1, 9, 0), "192.168.1.1"),
            ("E1", datetime(2026, 5, 1, 9, 20), "10.0.0.1"),
            ("E1", datetime(2026, 5, 1, 9, 40), "172.16.0.1"),
            # E2: 3 logins, all the same IP -> never flagged.
            ("E2", datetime(2026, 5, 1, 10, 0), "192.168.5.5"),
            ("E2", datetime(2026, 5, 1, 10, 20), "192.168.5.5"),
            ("E2", datetime(2026, 5, 1, 10, 40), "192.168.5.5"),
            # E3: only 2 distinct IPs -> below threshold.
            ("E3", datetime(2026, 5, 1, 11, 0), "192.168.9.1"),
            ("E3", datetime(2026, 5, 1, 11, 20), "192.168.9.2"),
        ]
        return pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: [r[0] for r in rows],
            cfg.COL_ACCESS_TIME: [r[1] for r in rows],
            cfg.COL_IP: [r[2] for r in rows],
        })

    def test_frozen_flagged_set(self):
        result = lc._filter_ip_switch(self._frame())
        assert len(result) == 3
        assert set(result[cfg.COL_EMPLOYEE_ID]) == {"E1"}

    def test_frozen_reason_columns(self):
        result = lc._filter_ip_switch(self._frame())
        # all three private /16s, gaps > fast-switch window -> stable classification
        assert list(result[cfg.COL_ESTIMATED_REASON]) == [
            cfg.REASON_PRIVATE_CROSS_SUBNET
        ] * 3
        assert list(result[cfg.COL_RISK_LEVEL]) == [cfg.RISK_MEDIUM] * 3
        assert list(result[cfg.COL_UNIQUE_IP_COUNT]) == [3] * 3
        assert list(result[cfg.COL_UNIQUE_SUBNET_COUNT]) == [3] * 3


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

    def test_all_private_different_16_classified_as_private_cross_subnet(self):
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
        assert reasons[0] == cfg.REASON_PRIVATE_CROSS_SUBNET

    def test_private_public_mix_classified_correctly(self):
        df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1", "emp1", "emp1"],
                cfg.COL_ACCESS_TIME: [
                    datetime(2023, 9, 1, 9, 0),
                    datetime(2023, 9, 1, 9, 30),
                    datetime(2023, 9, 1, 9, 45),
                ],
                cfg.COL_IP: ["10.0.1.10", "8.8.8.8", "192.168.1.30"],
            }
        )
        result = lc._estimate_ip_switch_reason(df)
        reasons = result[cfg.COL_ESTIMATED_REASON].unique()
        assert len(reasons) == 1
        assert reasons[0] == cfg.REASON_PRIVATE_PUBLIC_MIX

    def test_all_public_classified_as_public_cross_network(self):
        df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1", "emp1", "emp1"],
                cfg.COL_ACCESS_TIME: [
                    datetime(2023, 9, 1, 9, 0),
                    datetime(2023, 9, 1, 9, 30),
                    datetime(2023, 9, 1, 9, 45),
                ],
                cfg.COL_IP: ["8.8.8.8", "1.1.1.1", "203.0.113.5"],
            }
        )
        result = lc._estimate_ip_switch_reason(df)
        reasons = result[cfg.COL_ESTIMATED_REASON].unique()
        assert len(reasons) == 1
        assert reasons[0] == cfg.REASON_PUBLIC_CROSS_NETWORK

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
            == cfg.REASON_PRIVATE_CROSS_SUBNET
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
        assert (
            emp2[cfg.COL_ESTIMATED_REASON].unique()[0]
            == cfg.REASON_PRIVATE_CROSS_SUBNET
        )

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


class TestIsPrivateIpOctets:
    def test_10_range_is_private(self):
        assert lc._is_private_ip_octets(["10", "0", "0", "1"]) is True
        assert lc._is_private_ip_octets(["10", "255", "255", "255"]) is True

    def test_172_range_is_private_with_boundaries(self):
        assert lc._is_private_ip_octets(["172", "16", "0", "1"]) is True
        assert lc._is_private_ip_octets(["172", "31", "255", "255"]) is True
        # Boundaries: 172.15 and 172.32 are NOT private
        assert lc._is_private_ip_octets(["172", "15", "0", "1"]) is False
        assert lc._is_private_ip_octets(["172", "32", "0", "1"]) is False

    def test_192_168_range_is_private(self):
        assert lc._is_private_ip_octets(["192", "168", "0", "1"]) is True
        assert lc._is_private_ip_octets(["192", "168", "255", "255"]) is True
        assert lc._is_private_ip_octets(["192", "169", "0", "1"]) is False

    def test_public_ip_returns_false(self):
        assert lc._is_private_ip_octets(["8", "8", "8", "8"]) is False
        assert lc._is_private_ip_octets(["203", "0", "113", "1"]) is False
        assert lc._is_private_ip_octets(["1", "1", "1", "1"]) is False

    def test_malformed_input_returns_false(self):
        assert lc._is_private_ip_octets(["malformed"]) is False
        assert lc._is_private_ip_octets([]) is False


class TestCalculateRiskLevel:
    def test_same_subnet_low_and_fast_switch_medium(self):
        assert lc._calculate_risk_level(cfg.REASON_SAME_SUBNET, False) == cfg.RISK_LOW
        assert lc._calculate_risk_level(cfg.REASON_SAME_SUBNET, True) == cfg.RISK_MEDIUM

    def test_campus_move_and_private_cross_are_medium(self):
        assert (
            lc._calculate_risk_level(cfg.REASON_CAMPUS_MOVE, False) == cfg.RISK_MEDIUM
        )
        assert (
            lc._calculate_risk_level(cfg.REASON_PRIVATE_CROSS_SUBNET, False)
            == cfg.RISK_MEDIUM
        )

    def test_private_cross_fast_switch_is_high(self):
        assert (
            lc._calculate_risk_level(cfg.REASON_PRIVATE_CROSS_SUBNET, True)
            == cfg.RISK_HIGH
        )

    def test_mixed_and_public_cross_are_high(self):
        assert (
            lc._calculate_risk_level(cfg.REASON_PRIVATE_PUBLIC_MIX, False)
            == cfg.RISK_HIGH
        )
        assert (
            lc._calculate_risk_level(cfg.REASON_PUBLIC_CROSS_NETWORK, False)
            == cfg.RISK_HIGH
        )


class TestRiskAndAnalysisColumns:
    def test_same_24_has_risk_low(self):
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
        assert cfg.COL_RISK_LEVEL in result.columns
        assert (result[cfg.COL_RISK_LEVEL] == cfg.RISK_LOW).all()

    def test_private_cross_fast_switch_risk_high(self):
        df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1", "emp1", "emp1"],
                cfg.COL_ACCESS_TIME: [
                    datetime(2023, 9, 1, 9, 0),
                    datetime(2023, 9, 1, 9, 3),
                    datetime(2023, 9, 1, 9, 45),
                ],
                cfg.COL_IP: ["10.0.1.10", "172.16.1.20", "192.168.1.30"],
            }
        )
        result = lc._estimate_ip_switch_reason(df)
        assert (result[cfg.COL_RISK_LEVEL] == cfg.RISK_HIGH).all()

    def test_unique_ip_and_subnet_count_columns(self):
        df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1", "emp1", "emp1"],
                cfg.COL_ACCESS_TIME: [
                    datetime(2023, 9, 1, 9, 0),
                    datetime(2023, 9, 1, 9, 30),
                    datetime(2023, 9, 1, 9, 45),
                ],
                cfg.COL_IP: ["10.1.1.10", "10.1.2.20", "10.1.2.30"],
            }
        )
        result = lc._estimate_ip_switch_reason(df)
        assert cfg.COL_UNIQUE_IP_COUNT in result.columns
        assert cfg.COL_UNIQUE_SUBNET_COUNT in result.columns
        assert (result[cfg.COL_UNIQUE_IP_COUNT] == 3).all()
        assert (result[cfg.COL_UNIQUE_SUBNET_COUNT] == 2).all()

    def test_empty_and_filter_empty_have_new_columns(self):
        empty_df = pd.DataFrame(
            columns=[cfg.COL_EMPLOYEE_ID, cfg.COL_ACCESS_TIME, cfg.COL_IP]
        )
        result = lc._estimate_ip_switch_reason(empty_df)
        for col in [
            cfg.COL_RISK_LEVEL,
            cfg.COL_UNIQUE_IP_COUNT,
            cfg.COL_UNIQUE_SUBNET_COUNT,
        ]:
            assert col in result.columns

        # Also test _filter_ip_switch empty path
        non_flagged = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1", "emp1"],
                cfg.COL_ACCESS_TIME: [
                    datetime(2023, 9, 1, 9, 0),
                    datetime(2023, 9, 1, 9, 30),
                ],
                cfg.COL_IP: ["192.168.1.1", "192.168.1.2"],
            }
        )
        result2 = lc._filter_ip_switch(non_flagged)
        for col in [
            cfg.COL_RISK_LEVEL,
            cfg.COL_UNIQUE_IP_COUNT,
            cfg.COL_UNIQUE_SUBNET_COUNT,
        ]:
            assert col in result2.columns


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
            "src.checkers.login_checker.load_merged_excel",
            return_value=sample_login_df,
        )
        mocker.patch(
            "src.checkers.login_checker._filter_ip_switch", return_value=pd.DataFrame()
        )
        mocker.patch(
            "src.checkers.login_checker.filter_by_time_conditions",
            return_value=pd.DataFrame(),
        )
        mocker.patch("src.checkers.login_checker.save_excel_with_autofit")
        mocker.patch("src.checkers.login_checker.print_info")
        mocker.patch("src.checkers.login_checker.run_pipeline")

        save_dir = temp_dir
        result = lc.run_check("download_dir", save_dir, "202309")
        assert result == len(sample_login_df)

    def test_run_check_no_data(self, temp_dir, mocker):
        mocker.patch("src.checkers.login_checker.print_checker_header")
        mocker.patch(
            "src.checkers.login_checker.load_merged_excel",
            return_value=None,
        )
        mocker.patch("src.checkers.login_checker.print_info")

        save_dir = temp_dir
        result = lc.run_check("download_dir", save_dir, "202309")
        assert result == 0

    def test_run_check_missing_ip_column(self, temp_dir, sample_login_df, mocker):
        mocker.patch("src.checkers.login_checker.print_checker_header")
        mocker.patch(
            "src.checkers.login_checker.load_merged_excel",
            return_value=sample_login_df.drop(columns=["IP"]),
        )
        mocker.patch("src.checkers.login_checker.save_excel_with_autofit")
        mocker.patch("src.checkers.login_checker.print_info")

        save_dir = temp_dir
        with pytest.raises(ValueError):
            lc.run_check("download_dir", save_dir, "202309")
