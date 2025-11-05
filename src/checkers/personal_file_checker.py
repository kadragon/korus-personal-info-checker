"""
This module checks personal information access logs.
It processes Excel files containing user personal data access records,
merges them if multiple files are found, and performs the following checks:
- Access to 'HR Master' (HR master) program (excluding self-access).
- User's bulk data queries.
- User's bulk data saves.

Filtered results for each check are saved to separate Excel files, and
bulk access reports may
have sheets created per user exceeding the threshold.
"""

import os
from datetime import datetime

import pandas as pd

from .. import config as cfg
from ..display import print_checker_header, print_result
from ..utils import find_and_prepare_excel_file, run_and_save_check


def run_check(download_dir: str, save_dir: str, prev_month: str) -> int:
    """
    Main function to check personal information access logs.

    Finds all relevant Excel files in `download_dir`, merges them into a
    single DataFrame,
    and applies the following filters:
    1. Access to 'HR Master' (HR master) program (excluding cases where the
       user accesses their own records).
    2. Users who queried an abnormally large number of records
       (`VIEW_THRESHOLD` exceeded).
    3. Users who saved an abnormally large number of records
       (`SAVE_THRESHOLD` exceeded).

    Results of each check are saved to separate Excel files. Reports for bulk access are
    multi-sheet Excel files containing all records of specific users
    exceeding the threshold.

    Parameters:
        download_dir (str): The directory containing the original personal
        information access log Excel files.
        save_dir (str): The directory where the generated report Excel files
        will be saved.
        prev_month (str): The previous month in 'YYYYMM' format, used for
        output file naming.

    Returns:
    int: The number of rows in the processed original data. Returns 0 if
    no files are found.

    Raises:
        ValueError: If valid Excel files cannot be merged or required
        columns are missing.
    """
    print_checker_header(cfg.PERSONAL_INFO_REPORT_BASE)

    file_prefix = (
        f"{cfg.PERSONAL_INFO_ACCESS_LOG_PREFIX}{datetime.today().strftime('%Y%m')}"
    )

    df, _ = find_and_prepare_excel_file(
        download_dir,
        file_prefix,
        save_dir,
        cfg.PERSONAL_INFO_REPORT_BASE,
        prev_month,
    )

    if df is None:
        return 0

    df_to_analyze = df

    # 필터 1: '인사마스터'(HR 마스터) 접근, 본인 접근 제외.
    base_report_name = cfg.MERGED_PERSONAL_INFO_ACCESS_FILENAME_TEMPLATE.split(".")[
        0
    ].format(prev_month)
    save_path_master = os.path.join(
        save_dir,
        f"{base_report_name}({cfg.PERSONAL_INFO_ACCESS_MASTER_SUFFIX}).xlsx",
    )
    run_and_save_check(
        df=df_to_analyze,
        check_func=_filter_by_job_master_exclude_detail_id,
        save_path=save_path_master,
        result_description="인사마스터 타인 조회",
    )

    # 필터 2: 대량의 기록을 조회하는 사용자.
    save_path_high_views = os.path.join(
        save_dir,
        f"{base_report_name}({cfg.PERSONAL_INFO_ACCESS_HIGH_VOLUME_VIEWS_SUFFIX}).xlsx",
    )
    _extract_and_save_by_job(
        df_to_analyze,
        save_path_high_views,
        job="조회",
        threshold=cfg.VIEW_THRESHOLD,
        job_column_name=cfg.COL_JOB_PERFORMANCE,
    )

    # 필터 3: 대량의 기록을 저장하는 사용자.
    save_path_high_saves = os.path.join(
        save_dir,
        f"{base_report_name}({cfg.PERSONAL_INFO_ACCESS_HIGH_VOLUME_SAVES_SUFFIX}).xlsx",
    )
    _extract_and_save_by_job(
        df_to_analyze,
        save_path_high_saves,
        job="저장",
        threshold=cfg.SAVE_THRESHOLD,
        job_column_name=cfg.COL_JOB_PERFORMANCE,
    )

    return len(df)


def _filter_by_job_master_exclude_detail_id(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters access records to the 'HR Master' (HR master) program,
    excluding cases where the user's ID
    appears in the 'Detail Content' field (i.e., self-access).

    Parameters:
    df (pd.DataFrame): DataFrame containing personal information access logs.
                       Expected columns: `COL_PROGRAM_NAME`,
                       `COL_EMPLOYEE_ID`,
                       `COL_ACCESS_TIME`, `COL_DETAIL_CONTENT`.

    Returns:
        pd.DataFrame: DataFrame containing filtered records, sorted by
        employee ID and access time.
                      Returns an empty DataFrame if no such records exist.

    Raises:
        ValueError: If required columns for filtering are missing.
    """
    employee_id_col_to_use = cfg.COL_EMPLOYEE_ID

    required_cols = [
        cfg.COL_PROGRAM_NAME,
        employee_id_col_to_use,
        cfg.COL_ACCESS_TIME,
        cfg.COL_DETAIL_CONTENT,
    ]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(
                f"'{col}' 컬럼을 찾을 수 없어 HR 마스터 필터링을 할 수 없습니다."
            )

    # '인사마스터' 프로그램 접근 기록 중, 본인 조회가 아닌 경우만 필터링합니다.
    # 조건 1: '프로그램명'이 '인사마스터'인 기록만 선택합니다.
    hr_master_df = df[df[cfg.COL_PROGRAM_NAME] == "인사마스터"].copy()

    if hr_master_df.empty:
        return hr_master_df

    # 조건 2: '상세내용'에 자신의 '직원ID'가 포함되어 있지 않은 기록만 남깁니다.
    #         (즉, 타인 조회 기록만 필터링)
    # 각 행을 순회하며 '직원ID'와 '상세내용'을 비교해야 하므로 apply 함수를 사용합니다.
    is_not_self_access = [
        str(emp_id) not in str(detail)
        for emp_id, detail in zip(
            hr_master_df[employee_id_col_to_use],
            hr_master_df[cfg.COL_DETAIL_CONTENT],
            strict=True,
        )
    ]
    filtered_df = hr_master_df[is_not_self_access]

    # 결과를 정렬합니다.
    return filtered_df.sort_values([employee_id_col_to_use, cfg.COL_ACCESS_TIME])


def _extract_and_save_by_job(
    df: pd.DataFrame, save_path: str, job: str, threshold: int, job_column_name: str
) -> None:
    """
    Identifies users who performed a specific `job` (e.g., 'query', 'save')
    more than `threshold` times.
    For each such user, saves not only records matching that job but all records
    to separate sheets in the specified Excel file.

    Parameters:
        df (pd.DataFrame): DataFrame containing all personal information access logs.
        save_path (str): The full path to the Excel file where results will be saved.
        job (str): The specific job type to count (e.g., 'query', 'save').
        threshold (int): The minimum number of times the `job` must be
        performed to flag the user.
        job_column_name (str): The name of the column in `df` containing the job type
                               (e.g., `COL_JOB_PERFORMANCE`).

    Raises:
        ValueError: If required columns (`COL_EMPLOYEE_ID`, `COL_EMPLOYEE_NAME`,
                       `job_column_name`) are missing.
    """
    employee_id_col_to_use = cfg.COL_EMPLOYEE_ID

    required_cols_check = [
        employee_id_col_to_use,
        cfg.COL_EMPLOYEE_NAME,
        job_column_name,
    ]
    for col in required_cols_check:
        if col not in df.columns:
            raise ValueError(f"'{col}' 컬럼을 찾을 수 없어 작업을 추출할 수 없습니다.")

    job_specific_df = df[df[job_column_name] == job]
    job_counts_per_user = job_specific_df.groupby(employee_id_col_to_use).size()
    target_user_ids = job_counts_per_user[
        job_counts_per_user >= threshold
    ].index.tolist()

    description = f"{job} {threshold}건 이상"

    if not target_user_ids:
        print_result(is_detected=False, description=description)
        return

    with pd.ExcelWriter(save_path) as writer:
        for employee_id in target_user_ids:
            user_all_records_df = df[df[employee_id_col_to_use] == employee_id]
            user_name = ""
            if (
                not user_all_records_df.empty
                and cfg.COL_EMPLOYEE_NAME in user_all_records_df.columns
            ):
                user_name = user_all_records_df[cfg.COL_EMPLOYEE_NAME].iloc[0]

            sheet_name = f"{employee_id}_{user_name}"
            if len(sheet_name) > cfg.SHEET_NAME_MAX_CHARS:
                sheet_name = sheet_name[: cfg.SHEET_NAME_MAX_CHARS]

            user_all_records_df.to_excel(writer, sheet_name=sheet_name, index=False)

    print_result(
        is_detected=True,
        description=f"{description} ({len(target_user_ids)}명)",
        filename=os.path.basename(save_path),
    )
