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
from collections.abc import Callable
from datetime import datetime

import pandas as pd

from .. import config as cfg
from ..display import print_checker_header
from ..utils import (
    filter_by_time_conditions,
    find_and_prepare_excel_file,
    run_and_save_check,
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

    file_prefix = f"{cfg.LOGIN_LOG_FILE_PREFIX}{datetime.today().strftime('%Y%m')}"

    df, _ = find_and_prepare_excel_file(
        download_dir,
        file_prefix,
        save_dir,
        cfg.LOGIN_CHECK_REPORT_BASE,
        prev_month,
    )

    if df is None:
        return 0

    if cfg.COL_IP not in df.columns:
        raise ValueError(f"'{cfg.COL_IP}' 컬럼을 찾을 수 없습니다.")

    checks_to_run: list[dict[str, Callable[[pd.DataFrame], pd.DataFrame] | str]] = [
        {
            "function": _filter_ip_switch,
            "suffix": cfg.LOGIN_REPORT_IP_SWITCH_SUFFIX,
            "description": (
                f"{cfg.LOGIN_IP_SWITCH_WINDOW_HOURS}시간 내 "
                f"{cfg.LOGIN_IP_SWITCH_MIN_IPS}개 이상 IP 사용"
            ),
        },
        {
            "function": lambda df: filter_by_time_conditions(
                df,
                time_col=cfg.COL_ACCESS_TIME,
                employee_id_col=cfg.COL_EMPLOYEE_ID,
                check_off_hours=True,
                check_holidays_weekends=False,
                off_hours_start=cfg.LOGIN_OFF_HOURS_START,
                off_hours_end=cfg.LOGIN_OFF_HOURS_END,
            ),
            "suffix": cfg.LOGIN_REPORT_OFF_HOURS_SUFFIX,
            "description": "업무 시간 외 로그인",
        },
        {
            "function": lambda df: filter_by_time_conditions(
                df,
                time_col=cfg.COL_ACCESS_TIME,
                employee_id_col=cfg.COL_EMPLOYEE_ID,
                check_off_hours=False,
                check_holidays_weekends=True,
                off_hours_start=0,  # Not used
                off_hours_end=0,  # Not used
            ),
            "suffix": cfg.LOGIN_REPORT_HOLIDAY_SUFFIX,
            "description": "휴일/주말 로그인",
        },
    ]

    for check in checks_to_run:
        save_path = os.path.join(
            save_dir,
            f"{cfg.LOGIN_CHECK_REPORT_BASE}({check['suffix']})_{prev_month}.xlsx",
        )
        check_func = check["function"]
        if not callable(check_func):
            # Skip non-callable entries (should not happen with current structure)
            continue
        run_and_save_check(
            df=df,
            check_func=check_func,
            save_path=save_path,
            result_description=str(check["description"]),
        )

    return len(df)


def _split_into_clusters(
    group: pd.DataFrame,
) -> list[pd.DataFrame]:
    """Split a sorted group of rows into time-based clusters.

    Consecutive rows with a gap > LOGIN_IP_SWITCH_WINDOW_HOURS form
    separate clusters.
    """
    sorted_group = group.sort_values(cfg.COL_ACCESS_TIME)
    clusters: list[pd.DataFrame] = []
    cluster_start = 0
    for i in range(1, len(sorted_group)):
        gap = (
            sorted_group.iloc[i][cfg.COL_ACCESS_TIME]
            - sorted_group.iloc[i - 1][cfg.COL_ACCESS_TIME]
        )
        if gap > pd.Timedelta(hours=cfg.LOGIN_IP_SWITCH_WINDOW_HOURS):
            clusters.append(sorted_group.iloc[cluster_start:i])
            cluster_start = i
    clusters.append(sorted_group.iloc[cluster_start:])
    return clusters


logger = logging.getLogger(__name__)


def _estimate_ip_switch_reason(df: pd.DataFrame) -> pd.DataFrame:
    """Estimate the reason for IP switching patterns per cluster.

    Splits each employee's flagged rows into time-based clusters
    (gap > LOGIN_IP_SWITCH_WINDOW_HOURS), then classifies each cluster:
    - All IPs in same /24 → same network PC change
    - All IPs in same /16 but different /24 → campus move
    - Different /16 → external network access

    Appends a fast-switch suffix if any consecutive different-IP logins
    occur within LOGIN_IP_FAST_SWITCH_MINUTES minutes.

    NaN and malformed IPs (not 4 octets) are skipped during classification.

    Parameters:
        df: DataFrame with COL_EMPLOYEE_ID, COL_ACCESS_TIME, COL_IP columns.

    Returns:
        DataFrame with added COL_ESTIMATED_REASON column.
    """
    result = df.copy()
    result[cfg.COL_ESTIMATED_REASON] = ""

    if result.empty:
        return result

    for _emp_id, group in result.groupby(cfg.COL_EMPLOYEE_ID):
        clusters = _split_into_clusters(group)

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
                reason = cfg.REASON_EXTERNAL_NETWORK
            elif len(slash24_set) > 1:
                reason = cfg.REASON_CAMPUS_MOVE
            else:
                reason = cfg.REASON_SAME_SUBNET

            # Check for fast IP switching within the cluster
            sorted_cluster = cluster.sort_values(cfg.COL_ACCESS_TIME)
            has_fast_switch = False
            for i in range(1, len(sorted_cluster)):
                prev_row = sorted_cluster.iloc[i - 1]
                curr_row = sorted_cluster.iloc[i]
                prev_ip = prev_row[cfg.COL_IP]
                curr_ip = curr_row[cfg.COL_IP]
                if pd.notna(prev_ip) and pd.notna(curr_ip) and prev_ip != curr_ip:
                    time_diff = (
                        curr_row[cfg.COL_ACCESS_TIME]
                        - prev_row[cfg.COL_ACCESS_TIME]
                    )
                    if time_diff <= pd.Timedelta(
                        minutes=cfg.LOGIN_IP_FAST_SWITCH_MINUTES
                    ):
                        has_fast_switch = True
                        break

            if has_fast_switch:
                reason = f"{reason}{cfg.REASON_FAST_SWITCH_SUFFIX}"

            result.loc[cluster.index, cfg.COL_ESTIMATED_REASON] = reason

    return result


def _filter_ip_switch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters users who logged in from multiple unique IP addresses within a
    defined time window.

    Parameters:
        df (pd.DataFrame): DataFrame containing login records. Expected columns include
                           `COL_ACCESS_TIME` (access timestamp) and
                           `COL_IP` (IP address),
                           and `COL_EMPLOYEE_ID` (employee identifier).

    Returns:
        pd.DataFrame: DataFrame containing user records that triggered IP change alerts,
                      sorted by employee ID and access time.
                      Returns an empty DataFrame if no such records exist.

    Raises:
        ValueError: If the input DataFrame `df` is None.
    """
    if df is None:
        raise ValueError("Input DataFrame cannot be None.")

    df_copy = df.copy()

    flagged_indices = (
        set()
    )  # 중복을 피하기 위해 플래그가 지정된 행의 인덱스를 저장하는 데 세트를 사용합니다.

    # 직원 ID별로 그룹화하여 각 사용자의 로그인 패턴을 분석합니다.
    for _, group in df_copy.groupby(cfg.COL_EMPLOYEE_ID):
        group = group.sort_values(cfg.COL_ACCESS_TIME)

        # 사용자의 각 로그인 이벤트를 반복합니다.
        for i in range(len(group)):
            current_login_time = group.iloc[i][cfg.COL_ACCESS_TIME]
            # 후속 로그인을 확인하기 위한 시간 창을 정의합니다.
            window_end_time = current_login_time + pd.Timedelta(
                hours=cfg.LOGIN_IP_SWITCH_WINDOW_HOURS
            )

            # 이 창 내의 로그인을 선택합니다.
            logins_in_window = group[
                (group[cfg.COL_ACCESS_TIME] >= current_login_time)
                & (group[cfg.COL_ACCESS_TIME] <= window_end_time)
            ]

            # 이 창 내의 고유 IP 수가 임계값을 충족하는지 확인합니다.
            if (
                len(set(logins_in_window[cfg.COL_IP].dropna()))
                >= cfg.LOGIN_IP_SWITCH_MIN_IPS
            ):
                flagged_indices.update(
                    logins_in_window.index
                )  # 이 창의 모든 기록을 추가합니다.

    if flagged_indices:
        result_df = df_copy.loc[sorted(flagged_indices)]
        result_df = result_df.sort_values([cfg.COL_EMPLOYEE_ID, cfg.COL_ACCESS_TIME])
        return _estimate_ip_switch_reason(result_df)
    else:
        empty_df = pd.DataFrame(columns=df.columns)
        empty_df[cfg.COL_ESTIMATED_REASON] = pd.Series(dtype="str")
        return empty_df
