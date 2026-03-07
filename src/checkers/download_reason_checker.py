"""
This module checks the reasons for downloading personal information.
It analyzes personal data download logs and flags suspicious activities such as:
- Downloads with very short or simple reasons (e.g., "asdfg", "12345").
- Users downloading an excessive total number of records.
- Users downloading data at abnormally high frequency within a short time.
- Downloads outside standard business hours or on holidays/weekends.

The main function `sayu_checker` ("Reason Checker") performs these checks and
saves the filtered results to separate Excel files.
"""

import os
import re
from collections.abc import Callable
from datetime import datetime
from typing import Any, cast

import numpy as np
import pandas as pd

from .. import config as cfg
from ..display import print_checker_header, print_info
from ..utils import (
    _find_excel_files,
    _merge_and_preprocess_files,
    filter_by_time_conditions,
    find_and_prepare_excel_file,
    run_and_save_check,
)

_JAMO_PATTERN = re.compile(r"[\u3131-\u3163]")
_LATIN_CHARS_PATTERN = re.compile(r"[a-zA-Z]")
_CONSONANT_CLUSTER_PATTERN = re.compile(r"[bcdfghjklmnpqrstvwxyz]{5,}", re.IGNORECASE)
_LATIN_VOWEL_MIN_RATIO = 0.2
_LATIN_MIN_LENGTH = 8


def _unique_char_count_below_5(text_input: Any) -> bool:
    """
    Checks if the number of unique characters in the given string is 5 or fewer.
    This is used to identify potentially suspicious or insufficiently explained
    download reasons.

    Parameters:
        text_input: The string to check. Typically the download reason.

    Returns:
        bool: True if the number of unique characters is 5 or fewer, False otherwise.
              Returns False if the input is NaN (Not a Number).
    """
    if pd.isna(text_input):
        return False
    return len(set(str(text_input))) <= 5


def _has_korean_jamo(text_input: Any) -> bool:
    """
    Checks if the text contains independent Korean jamo (U+3131–U+3163).

    Normal Korean text uses complete syllable blocks (가-힣). Independent jamo
    indicate keyboard mashing or invalid input.

    Parameters:
        text_input: The string to check.

    Returns:
        bool: True if independent jamo are found, False otherwise.
              Returns False if the input is NaN.
    """
    if pd.isna(text_input):
        return False
    return bool(_JAMO_PATTERN.search(str(text_input)))


def _is_latin_gibberish(text_input: Any) -> bool:
    """
    Checks if the text is likely Latin keyboard mashing (gibberish).

    Only applies when the text contains at least _LATIN_MIN_LENGTH Latin characters.
    Detects gibberish via vowel ratio below _LATIN_VOWEL_MIN_RATIO or a consonant
    cluster of 5 or more consecutive consonants.

    Parameters:
        text_input: The string to check.

    Returns:
        bool: True if the text appears to be Latin gibberish, False otherwise.
              Returns False if the input is NaN or has fewer than _LATIN_MIN_LENGTH
              Latin characters.
    """
    if pd.isna(text_input):
        return False
    text = str(text_input)
    latin_chars = _LATIN_CHARS_PATTERN.findall(text)
    if len(latin_chars) < _LATIN_MIN_LENGTH:
        return False
    vowel_count = sum(1 for c in latin_chars if c in "aeiouAEIOU")
    vowel_ratio = vowel_count / len(latin_chars)
    if vowel_ratio < _LATIN_VOWEL_MIN_RATIO:
        return True
    return bool(_CONSONANT_CLUSTER_PATTERN.search(text))


def _is_suspicious_reason(text_input: Any) -> bool:
    """
    Master function combining all suspicious download reason checks.

    Returns True if any of the following conditions are met:
    - Unique character count is 5 or fewer (_unique_char_count_below_5)
    - Contains independent Korean jamo (_has_korean_jamo)
    - Appears to be Latin keyboard mashing (_is_latin_gibberish)

    Parameters:
        text_input: The string to check.

    Returns:
        bool: True if the download reason is suspicious, False otherwise.
    """
    return (
        _unique_char_count_below_5(text_input)
        or _has_korean_jamo(text_input)
        or _is_latin_gibberish(text_input)
    )


def _normalize_employee_id(s: pd.Series) -> pd.Series:
    """Normalize employee IDs to handle float-to-string conversion."""
    return s.astype(str).str.replace(r"\.0$", "", regex=True)


def _load_access_logs(download_dir: str, prev_month: str) -> pd.DataFrame | None:
    """Load and merge access log files for the given month."""
    file_prefix = f"{cfg.PERSONAL_INFO_ACCESS_LOG_PREFIX}{prev_month}"
    try:
        excel_files = _find_excel_files(download_dir, file_prefix)
    except EnvironmentError as e:
        print_info(f"접속기록 파일 검색 중 오류 발생: {e}")
        return None

    if not excel_files:
        return None

    merged_df = _merge_and_preprocess_files(excel_files, download_dir)
    if merged_df is None:
        print_info("접속기록 파일 병합/전처리 실패. 교차 검증을 건너뜁니다.")
        return None

    merged_df.drop_duplicates(inplace=True)
    print_info(f"접속기록 로드 완료: {len(merged_df)}건 (중복 제거 후)")
    return merged_df


_REQUIRED_ACCESS_LOG_COLS = frozenset(
    {
        cfg.COL_EMPLOYEE_ID,
        cfg.COL_ACCESS_TIME,
        cfg.COL_PROGRAM_NAME,
        cfg.COL_JOB_PERFORMANCE,
    }
)


def _enrich_with_access_log_summary(
    download_df: pd.DataFrame,
    access_log_df: pd.DataFrame,
    window_minutes: int,
) -> pd.DataFrame:
    """Enrich download records with access log summary within ±window_minutes."""
    result = download_df.copy()
    result[cfg.COL_ACCESS_LOG_SUMMARY] = ""
    result[cfg.COL_NEAREST_ACCESS_GAP] = np.nan

    if access_log_df.empty:
        return result

    missing = _REQUIRED_ACCESS_LOG_COLS - set(access_log_df.columns)
    if missing:
        print_info(f"접속기록에 필수 컬럼 누락: {missing}. 교차 검증을 건너뜁니다.")
        return result

    access_log_df = access_log_df.copy()
    access_log_df[cfg.COL_EMPLOYEE_ID] = _normalize_employee_id(
        access_log_df[cfg.COL_EMPLOYEE_ID]
    )
    result[cfg.COL_EMPLOYEE_ID] = _normalize_employee_id(result[cfg.COL_EMPLOYEE_ID])

    window_ns = np.timedelta64(window_minutes, "m")

    has_detail = cfg.COL_DETAIL_CONTENT in access_log_df.columns

    # Pre-group: sorted timestamps + labels + details as numpy arrays per employee
    grouped: dict[str, tuple[Any, Any, Any]] = {}
    for emp_id, group in access_log_df.groupby(cfg.COL_EMPLOYEE_ID):
        sorted_group = group.sort_values(cfg.COL_ACCESS_TIME)
        timestamps = sorted_group[cfg.COL_ACCESS_TIME].values
        labels = (
            sorted_group[cfg.COL_PROGRAM_NAME].astype(str)
            + "("
            + sorted_group[cfg.COL_JOB_PERFORMANCE].astype(str)
            + ")"
        ).values
        if has_detail:
            details = sorted_group[cfg.COL_DETAIL_CONTENT].fillna("").astype(str).values
        else:
            details = np.full(len(sorted_group), "", dtype=object)
        grouped[str(emp_id)] = (timestamps, labels, details)

    summaries = result[cfg.COL_ACCESS_LOG_SUMMARY].to_numpy(copy=True)
    gaps = result[cfg.COL_NEAREST_ACCESS_GAP].to_numpy(copy=True, dtype=float)

    emp_ids = result[cfg.COL_EMPLOYEE_ID].values
    access_times = result[cfg.COL_ACCESS_TIME].values

    for i in range(len(result)):
        emp_id = str(emp_ids[i])
        if emp_id not in grouped:
            continue

        timestamps, labels, details = grouped[emp_id]
        download_time = access_times[i]

        diffs = np.abs(timestamps - download_time)
        min_gap_minutes = round(
            diffs.min().astype("timedelta64[s]").astype(float) / 60, 1
        )

        lo = np.searchsorted(timestamps, download_time - window_ns, side="left")
        hi = np.searchsorted(timestamps, download_time + window_ns, side="right")

        if lo >= hi:
            gaps[i] = min_gap_minutes
            continue

        gaps[i] = 0

        matched_labels = labels[lo:hi]
        matched_details = details[lo:hi]

        # Build summary with detail snippets
        entries: dict[str, dict[str, Any]] = {}
        for label, detail in zip(matched_labels, matched_details, strict=True):
            label_str = str(label)
            if label_str not in entries:
                entries[label_str] = {"count": 0, "detail": ""}
            entries[label_str]["count"] += 1
            if detail and not entries[label_str]["detail"]:
                truncated = detail[: cfg.DETAIL_TRUNCATE_LEN]
                if len(detail) > cfg.DETAIL_TRUNCATE_LEN:
                    truncated += "..."
                entries[label_str]["detail"] = truncated

        parts = []
        for label_str, info in entries.items():
            part = label_str
            if info["count"] > 1:
                part += f" x{info['count']}"
            if info["detail"]:
                part += f" [{info['detail']}]"
            parts.append(part)

        summaries[i] = "; ".join(parts)

    result[cfg.COL_ACCESS_LOG_SUMMARY] = summaries
    result[cfg.COL_NEAREST_ACCESS_GAP] = gaps
    return result


def run_check(download_dir: str, save_dir: str, prev_month: str) -> int:
    """
    Main function to check for suspicious patterns in personal information
    download reasons.

    Reads the download reason log file and applies multiple filters:
    1. Invalid or short download reasons.
    2. High total download count per user.
    3. High download frequency per user within one hour.
    4. Downloads outside business hours or on holidays/weekends.

    Each filtered result set is saved to a separate Excel file.

    Parameters:
        download_dir (str): The directory containing the original download
        reason Excel files.
        save_dir (str): The directory where the generated report Excel files
        will be saved.
        prev_month (str): The previous month in 'YYYYMM' format, used for
        output file naming.

    Returns:
        int: The number of rows in the processed original data. Returns 0 if
        no files are found.
    """
    print_checker_header(cfg.DOWNLOAD_REASON_REPORT_BASE)

    file_prefix = (
        f"{cfg.PERSONAL_INFO_DOWNLOAD_REASON_PREFIX}{datetime.today().strftime('%Y%m')}"
    )

    df, merged_save_path = find_and_prepare_excel_file(
        download_dir,
        file_prefix,
        save_dir,
        cfg.DOWNLOAD_REASON_REPORT_BASE,
        prev_month,
    )

    if df is None:
        return 0

    access_log_df = _load_access_logs(download_dir, prev_month)
    if access_log_df is not None:
        try:
            df = _enrich_with_access_log_summary(
                df, access_log_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
            )
            if merged_save_path is not None:
                df.to_excel(merged_save_path, index=False)
        except Exception as e:
            print_info(
                f"접속기록 교차 검증 중 오류 발생: {e}. 교차 검증 없이 진행합니다."
            )
    else:
        print_info("접속기록 파일을 찾을 수 없어 교차 검증을 건너뜁니다.")

    checks_to_run: list[dict[str, Callable[[pd.DataFrame], pd.DataFrame] | str]] = [
        {
            "function": _check_download_sayu,
            "suffix": cfg.DOWNLOAD_REASON_INVALID_REASON_SUFFIX,
            "description": "다운로드 사유 비정상",
        },
        {
            "function": _filter_high_download_users,
            "suffix": cfg.DOWNLOAD_REASON_HIGH_DOWNLOAD_COUNT_SUFFIX,
            "description": f"다운로드 {cfg.DOWNLOAD_COUNT_THRESHOLD}건 초과",
        },
        {
            "function": _filter_high_freq_download,
            "suffix": cfg.DOWNLOAD_REASON_HIGH_FREQUENCY_SUFFIX,
            "description": (
                f"1시간 내 {cfg.DOWNLOAD_FREQUENCY_THRESHOLD}건 이상 다운로드"
            ),
        },
        {
            "function": lambda df: filter_by_time_conditions(
                df,
                time_col=cfg.COL_ACCESS_TIME,
                employee_id_col=cfg.COL_EMPLOYEE_ID,
                check_off_hours=True,
                check_holidays_weekends=True,
                off_hours_start=cfg.DOWNLOAD_OFF_HOURS_START,
                off_hours_end=cfg.DOWNLOAD_OFF_HOURS_END,
            ),
            "suffix": cfg.DOWNLOAD_REASON_OFF_HOURS_SUFFIX,
            "description": "업무 시간 외/휴일 다운로드",
        },
    ]

    for check in checks_to_run:
        save_path = os.path.join(
            save_dir,
            f"{cfg.DOWNLOAD_REASON_REPORT_BASE}({check['suffix']})_{prev_month}.xlsx",
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


def _check_download_sayu(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters records with suspicious download reasons (too short or simple).
    Uses the `_unique_char_count_below_5` helper function for the check.

    Parameters:
        df (pd.DataFrame): DataFrame containing download records. Expected columns:
                           `COL_DOWNLOAD_REASON` (download reason),
                           `COL_EMPLOYEE_ID` (employee ID),
                           `COL_ACCESS_TIME` (access timestamp).

    Returns:
        pd.DataFrame: Filtered DataFrame containing records with suspicious
        download reasons,
                      sorted by employee ID and access time.

    Raises:
        ValueError: If the expected download reason column
        (`COL_DOWNLOAD_REASON`) is not found in the DataFrame.
    """
    if cfg.COL_DOWNLOAD_REASON not in df.columns:
        raise ValueError(f"'{cfg.COL_DOWNLOAD_REASON}' 컬럼을 찾을 수 없습니다.")

    # 다운로드 사유의 고유 문자 수에 대한 필터를 적용합니다.
    # 원본 주석: "5. 고유 문자 개수 5개 이하인 row 필터링"
    filtered_df = df[df[cfg.COL_DOWNLOAD_REASON].apply(_is_suspicious_reason)]
    return filtered_df.sort_values([cfg.COL_EMPLOYEE_ID, cfg.COL_ACCESS_TIME])


def _filter_high_download_users(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters users whose total download record count exceeds the defined threshold.

    Parameters:
        df (pd.DataFrame): DataFrame containing download records. Expected columns:
                           `COL_DOWNLOAD_COUNT` (number of downloaded records),
                           `COL_EMPLOYEE_ID` (employee ID),
                           `COL_ACCESS_TIME` (access timestamp).

    Returns:
        pd.DataFrame: DataFrame containing all download records of users
        exceeding the threshold,
                      sorted by employee ID and access time.

    Raises:
        ValueError: If the `COL_DOWNLOAD_COUNT` column is missing.
    """
    if cfg.COL_DOWNLOAD_COUNT not in df.columns:
        raise ValueError(f"'{cfg.COL_DOWNLOAD_COUNT}' 컬럼을 찾을 수 없습니다.")

    # 직원 ID별로 그룹화하고 다운로드 수를 합산합니다.
    download_sum_per_user = df.groupby(cfg.COL_EMPLOYEE_ID)[
        cfg.COL_DOWNLOAD_COUNT
    ].sum()
    # 다운로드 수 임계값을 충족하거나 초과하는 사용자를 식별합니다.
    target_users = download_sum_per_user[
        download_sum_per_user >= cfg.DOWNLOAD_COUNT_THRESHOLD
    ].index

    # 식별된 사용자의 모든 기록을 반환합니다.
    return df[df[cfg.COL_EMPLOYEE_ID].isin(target_users)].sort_values(
        [cfg.COL_EMPLOYEE_ID, cfg.COL_ACCESS_TIME]
    )


def _filter_high_freq_download(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters users who downloaded data at high frequency (threshold or more
    times within one hour).

    Parameters:
        df (pd.DataFrame): DataFrame containing download records. Expected columns:
                           `COL_ACCESS_TIME` (access timestamp),
                           `COL_EMPLOYEE_ID` (employee ID).

    Returns:
        pd.DataFrame: DataFrame containing records corresponding to
        high-frequency download bursts,
                      sorted by employee ID and access time.
                      Returns an empty DataFrame if no such bursts exist.

    Raises:
        ValueError: If the input DataFrame `df` is None.
    """
    if df is None:
        raise ValueError("Input DataFrame cannot be None.")

    df_copy = df.copy()

    flagged_indices = (
        set()
    )  # 높은 빈도의 다운로드 폭주에 속하는 기록의 원본 인덱스를 저장합니다.

    # 직원 ID별로 그룹화하여 각 사용자의 다운로드 패턴을 분석합니다.
    for _, group in df_copy.groupby(cfg.COL_EMPLOYEE_ID):
        # 정수 인덱스 i와 함께 .loc를 사용하기 위해 인덱스를 재설정합니다.
        group = group.sort_values(cfg.COL_ACCESS_TIME).reset_index()

        for i in range(len(group)):
            current_download_time = cast(
                pd.Timestamp, group.loc[i, cfg.COL_ACCESS_TIME]
            )
            # 현재 다운로드 시간으로부터 1시간 창을 정의합니다.
            window_end_time = current_download_time + pd.Timedelta(hours=1)

            # 이 1시간 창 내의 다운로드를 선택합니다.
            downloads_in_window = group[
                (group[cfg.COL_ACCESS_TIME] >= current_download_time)
                & (group[cfg.COL_ACCESS_TIME] <= window_end_time)
            ]

            # 이 창 내의 다운로드 수가 빈도 임계값을 충족하면 플래그를 지정합니다.
            if len(downloads_in_window) >= cfg.DOWNLOAD_FREQUENCY_THRESHOLD:
                flagged_indices.update(
                    downloads_in_window["index"].tolist()
                )  # reset_index() 후 저장된 원본 인덱스를 사용합니다.

    if flagged_indices:
        result_df = df_copy.loc[
            sorted(flagged_indices)
        ]  # 원본 인덱스를 사용하여 선택합니다.
        return result_df.sort_values([cfg.COL_EMPLOYEE_ID, cfg.COL_ACCESS_TIME])
    else:
        return pd.DataFrame(columns=df.columns)  # 동일한 열을 가진 빈 DataFrame 반환
