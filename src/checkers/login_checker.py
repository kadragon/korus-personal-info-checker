"""
This module performs checks on user login record data.
It identifies suspicious login patterns such as:
- Logins from multiple IP addresses within a short time.
- Logins outside business hours.
- Logins on holidays and weekends.

The main function `login_checker` coordinates these checks and saves the results
to separate Excel files.
"""

import logging
import os
from datetime import datetime
from functools import partial

import pandas as pd

from .. import config as cfg
from ..config import LoginConfig
from ..display import print_checker_header, print_info
from ..utils import (
    CheckSpec,
    filter_by_time_conditions,
    load_merged_excel,
    run_pipeline,
    save_excel_with_autofit,
)


def run_check(download_dir: str, save_dir: str, prev_month: str) -> int:
    """
    Main function to perform various checks on login record data.

    Reads the login record Excel file and applies the following filters:
    1. IP address changes: Users logging in from multiple IPs within a defined time.
    2. Off-hours access: Logins occurring outside standard business hours.
    3. Holiday/weekend access: Logins occurring on holidays or weekends.

    Each filtered result set is saved to a separate Excel file.

    Parameters:
        download_dir (str): The directory containing the original login
        record Excel files.
        save_dir (str): The directory where the generated report Excel files
        will be saved.
        prev_month (str): The previous month in 'YYYYMM' format, used for
        output file naming.

    Returns:
        int: The number of rows in the processed original data. Returns 0 if
        no files are found.

    Raises:
        ValueError: If the expected 'IP' column is not found in the DataFrame.
    """
    print_checker_header(cfg.LOGIN_CHECK_REPORT_BASE)

    config = LoginConfig()
    file_prefix = f"{cfg.LOGIN_LOG_FILE_PREFIX}{datetime.today().strftime('%Y%m')}"

    df = load_merged_excel(download_dir, file_prefix)
    if df is None:
        print_info(
            f"'{file_prefix}'로 시작하는 파일을 찾을 수 없습니다. 이 검사는 건너뜁니다."
        )
        return 0

    print_info(f"{cfg.LOGIN_CHECK_REPORT_BASE} 원본 데이터: {len(df)}건")
    os.makedirs(save_dir, exist_ok=True)
    merged_path = os.path.join(
        save_dir, f"{cfg.LOGIN_CHECK_REPORT_BASE}_{prev_month}.xlsx"
    )
    save_excel_with_autofit(df, merged_path)
    print_info(
        f"모든 파일을 합쳐 '{os.path.basename(merged_path)}'(으)로 저장했습니다."
    )

    if cfg.COL_IP not in df.columns:
        raise ValueError(f"'{cfg.COL_IP}' 컬럼을 찾을 수 없습니다.")

    _off_hours = partial(
        filter_by_time_conditions,
        time_col=cfg.COL_ACCESS_TIME,
        employee_id_col=cfg.COL_EMPLOYEE_ID,
        check_off_hours=True,
        check_holidays_weekends=False,
        off_hours_start=config.off_hours_start,
        off_hours_end=config.off_hours_end,
    )
    _holiday = partial(
        filter_by_time_conditions,
        time_col=cfg.COL_ACCESS_TIME,
        employee_id_col=cfg.COL_EMPLOYEE_ID,
        check_off_hours=False,
        check_holidays_weekends=True,
        off_hours_start=0,
        off_hours_end=0,
    )

    checks = [
        CheckSpec(
            filter_fn=partial(_filter_ip_switch, config=config),
            suffix=cfg.LOGIN_REPORT_IP_SWITCH_SUFFIX,
            description=(
                f"{config.ip_switch_window_hours}시간 내 "
                f"{config.ip_switch_min_ips}개 이상 IP 사용"
            ),
        ),
        CheckSpec(
            filter_fn=_off_hours,
            suffix=cfg.LOGIN_REPORT_OFF_HOURS_SUFFIX,
            description="업무 시간 외 로그인",
        ),
        CheckSpec(
            filter_fn=_holiday,
            suffix=cfg.LOGIN_REPORT_HOLIDAY_SUFFIX,
            description="휴일/주말 로그인",
        ),
    ]

    run_pipeline(df, checks, cfg.LOGIN_CHECK_REPORT_BASE, save_dir, prev_month)

    return len(df)


def _split_into_clusters(
    group: pd.DataFrame,
    config: LoginConfig | None = None,
) -> list[pd.DataFrame]:
    """Split a sorted group of rows into time-based clusters.

    Consecutive rows with a gap > ip_switch_window_hours form separate clusters.
    """
    if config is None:
        config = LoginConfig()
    sorted_group = group.sort_values(cfg.COL_ACCESS_TIME)
    clusters: list[pd.DataFrame] = []
    cluster_start = 0
    for i in range(1, len(sorted_group)):
        gap = (
            sorted_group.iloc[i][cfg.COL_ACCESS_TIME]
            - sorted_group.iloc[i - 1][cfg.COL_ACCESS_TIME]
        )
        if gap > pd.Timedelta(hours=config.ip_switch_window_hours):
            clusters.append(sorted_group.iloc[cluster_start:i])
            cluster_start = i
    clusters.append(sorted_group.iloc[cluster_start:])
    return clusters


logger = logging.getLogger(__name__)


def _is_private_ip_octets(octets: list[str]) -> bool:
    """Check if parsed IP octets are in RFC 1918 private range."""
    try:
        if len(octets) != 4:
            return False
        nums = [int(o) for o in octets]
        if any(n < 0 or n > 255 for n in nums):
            return False
        first, second = nums[0], nums[1]
    except (ValueError, IndexError):
        return False

    if first == 10:
        return True
    if first == 172 and 16 <= second <= 31:
        return True
    return bool(first == 192 and second == 168)


_RISK_MAP: dict[str, tuple[str, str]] = {
    # reason -> (base_risk, fast_switch_risk)
    cfg.REASON_SAME_SUBNET: (cfg.RISK_LOW, cfg.RISK_MEDIUM),
    cfg.REASON_CAMPUS_MOVE: (cfg.RISK_MEDIUM, cfg.RISK_MEDIUM),
    cfg.REASON_PRIVATE_CROSS_SUBNET: (cfg.RISK_MEDIUM, cfg.RISK_HIGH),
    cfg.REASON_PRIVATE_PUBLIC_MIX: (cfg.RISK_HIGH, cfg.RISK_HIGH),
    cfg.REASON_PUBLIC_CROSS_NETWORK: (cfg.RISK_HIGH, cfg.RISK_HIGH),
}


def _calculate_risk_level(reason: str, has_fast_switch: bool) -> str:
    """Calculate risk level based on reason and fast-switch status."""
    base, fast = _RISK_MAP.get(reason, (cfg.RISK_MEDIUM, cfg.RISK_MEDIUM))
    return fast if has_fast_switch else base


def _estimate_ip_switch_reason(
    df: pd.DataFrame,
    config: LoginConfig | None = None,
) -> pd.DataFrame:
    """Estimate the reason for IP switching patterns per cluster.

    Splits each employee's flagged rows into time-based clusters
    (gap > ip_switch_window_hours), then classifies each cluster:
    - All IPs in same /24 → same network PC change
    - All IPs in same /16 but different /24 → campus move
    - Different /16 → external network access

    Appends a fast-switch suffix if any consecutive different-IP logins
    occur within ip_fast_switch_minutes minutes.

    NaN and malformed IPs (not 4 octets) are skipped during classification.

    Parameters:
        df: DataFrame with COL_EMPLOYEE_ID, COL_ACCESS_TIME, COL_IP columns.
        config: LoginConfig with numeric thresholds. Defaults to LoginConfig().

    Returns:
        DataFrame with added COL_ESTIMATED_REASON column.
    """
    if config is None:
        config = LoginConfig()
    result = df.copy()
    result[cfg.COL_ESTIMATED_REASON] = ""
    result[cfg.COL_RISK_LEVEL] = ""
    result[cfg.COL_UNIQUE_IP_COUNT] = 0
    result[cfg.COL_UNIQUE_SUBNET_COUNT] = 0

    if result.empty:
        return result

    for _emp_id, group in result.groupby(cfg.COL_EMPLOYEE_ID):
        clusters = _split_into_clusters(group, config)

        for cluster in clusters:
            ips = cluster[cfg.COL_IP].dropna().unique()
            octets = []
            for ip in ips:
                parts = str(ip).split(".")
                if len(parts) != 4:
                    logger.warning(
                        "Skipping malformed IP '%s' for employee '%s'",
                        ip,
                        _emp_id,
                    )
                    continue
                octets.append(parts)

            if not octets:
                result.loc[cluster.index, cfg.COL_ESTIMATED_REASON] = ""
                continue

            # Classify by subnet
            slash16_set = {(o[0], o[1]) for o in octets}
            slash24_set = {(o[0], o[1], o[2]) for o in octets}

            if len(slash16_set) > 1:
                # Different /16 — classify by private/public status
                all_private = all(_is_private_ip_octets(o) for o in octets)
                any_private = any(_is_private_ip_octets(o) for o in octets)
                if all_private:
                    reason = cfg.REASON_PRIVATE_CROSS_SUBNET
                elif any_private:
                    reason = cfg.REASON_PRIVATE_PUBLIC_MIX
                else:
                    reason = cfg.REASON_PUBLIC_CROSS_NETWORK
            elif len(slash24_set) > 1:
                reason = cfg.REASON_CAMPUS_MOVE
            else:
                reason = cfg.REASON_SAME_SUBNET

            # Check for fast IP switching within the cluster
            # (cluster is already sorted by _split_into_clusters)
            has_fast_switch = False
            for i in range(1, len(cluster)):
                prev_row = cluster.iloc[i - 1]
                curr_row = cluster.iloc[i]
                prev_ip = prev_row[cfg.COL_IP]
                curr_ip = curr_row[cfg.COL_IP]
                if pd.notna(prev_ip) and pd.notna(curr_ip) and prev_ip != curr_ip:
                    time_diff = (
                        curr_row[cfg.COL_ACCESS_TIME] - prev_row[cfg.COL_ACCESS_TIME]
                    )
                    if time_diff <= pd.Timedelta(minutes=config.ip_fast_switch_minutes):
                        has_fast_switch = True
                        break

            risk = _calculate_risk_level(reason, has_fast_switch)

            if has_fast_switch:
                reason = f"{reason}{cfg.REASON_FAST_SWITCH_SUFFIX}"

            result.loc[cluster.index, cfg.COL_ESTIMATED_REASON] = reason
            result.loc[cluster.index, cfg.COL_RISK_LEVEL] = risk
            result.loc[cluster.index, cfg.COL_UNIQUE_IP_COUNT] = len(octets)
            result.loc[cluster.index, cfg.COL_UNIQUE_SUBNET_COUNT] = len(slash24_set)

    return result


def _filter_ip_switch(
    df: pd.DataFrame,
    config: LoginConfig | None = None,
) -> pd.DataFrame:
    """
    Filters users who logged in from multiple unique IP addresses within a
    defined time window.

    Parameters:
        df (pd.DataFrame): DataFrame containing login records. Expected columns include
                           `COL_ACCESS_TIME` (access timestamp) and
                           `COL_IP` (IP address),
                           and `COL_EMPLOYEE_ID` (employee identifier).
        config: LoginConfig with numeric thresholds. Defaults to LoginConfig().

    Returns:
        pd.DataFrame: DataFrame containing user records that triggered IP change alerts,
                      sorted by employee ID and access time.
                      Returns an empty DataFrame if no such records exist.

    Raises:
        ValueError: If the input DataFrame `df` is None.
    """
    if df is None:
        raise ValueError("Input DataFrame cannot be None.")

    if config is None:
        config = LoginConfig()

    df_copy = df.copy()

    flagged_indices: set[int] = set()

    for _, group in df_copy.groupby(cfg.COL_EMPLOYEE_ID):
        group = group.sort_values(cfg.COL_ACCESS_TIME)

        for i in range(len(group)):
            current_login_time = group.iloc[i][cfg.COL_ACCESS_TIME]
            window_end_time = current_login_time + pd.Timedelta(
                hours=config.ip_switch_window_hours
            )

            logins_in_window = group[
                (group[cfg.COL_ACCESS_TIME] >= current_login_time)
                & (group[cfg.COL_ACCESS_TIME] <= window_end_time)
            ]

            if (
                len(set(logins_in_window[cfg.COL_IP].dropna()))
                >= config.ip_switch_min_ips
            ):
                flagged_indices.update(logins_in_window.index)

    if flagged_indices:
        result_df = df_copy.loc[sorted(flagged_indices)]
        result_df = result_df.sort_values([cfg.COL_EMPLOYEE_ID, cfg.COL_ACCESS_TIME])
        return _estimate_ip_switch_reason(result_df, config)
    else:
        empty_df = pd.DataFrame(columns=df.columns)
        empty_df[cfg.COL_ESTIMATED_REASON] = pd.Series(dtype="str")
        empty_df[cfg.COL_RISK_LEVEL] = pd.Series(dtype="str")
        empty_df[cfg.COL_UNIQUE_IP_COUNT] = pd.Series(dtype="int")
        empty_df[cfg.COL_UNIQUE_SUBNET_COUNT] = pd.Series(dtype="int")
        return empty_df
