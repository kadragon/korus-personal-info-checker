"""
This module provides utility functions for common tasks such as date
manipulation, directory creation,
Excel file processing (saving with auto-fit column widths), searching for
and preparing specific Excel files to process.
"""

import os
import zipfile
from datetime import datetime

import holidays
import openpyxl
import pandas as pd
from dateutil.relativedelta import relativedelta
from openpyxl.utils import get_column_letter

from . import config as cfg
from .display import (
    print_error,
    print_info,
    print_result,
    print_zip_result,
    print_zip_warning,
)


def get_prev_month_yyyymm() -> str:
    """
    Calculates the previous month from the current date and returns it as a
    string in 'YYYYMM' format.

    Returns:
        str: The previous month in 'YYYYMM' format.
    """
    today = datetime.today()
    prev_month_date = today - relativedelta(months=1)
    return prev_month_date.strftime("%Y%m")


def make_save_dir(base_save_dir: str) -> str:
    """
    Creates a subdirectory named after the previous month (YYYYMM) within
    `base_save_dir`.
    If the subdirectory already exists, no action is taken.

    Parameters:
        base_save_dir (str): The base directory where the new subdirectory
        will be created.
                             This path must be an existing directory.

    Returns:
        str: The full path to the created or existing subdirectory for the
        previous month.
    """
    prev_month_str = get_prev_month_yyyymm()
    save_dir = os.path.join(base_save_dir, prev_month_str)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)
        # 이 함수는 메인 헤더가 인쇄되기 전에 호출되므로 간단한 인쇄가 더 좋습니다.
        print(f"폴더 생성: {save_dir}")

    return save_dir


def save_excel_with_autofit(df: pd.DataFrame, path: str):
    """
    Saves a Pandas DataFrame to an Excel file and auto-fits the column widths.

    Parameters:
        df (pd.DataFrame): The DataFrame to save.
        path (str): The full path (including filename) where the Excel file
        will be saved.
    """
    df.to_excel(path, index=False)
    wb = openpyxl.load_workbook(path)
    ws = wb.active

    if ws is None:
        wb.close()
        print_error("활성 워크시트를 찾을 수 없어 열 너비를 자동 맞춤할 수 없습니다.")
        return

    for idx, column_cells in enumerate(ws.columns):  # type: ignore
        max_length = 0
        column_letter = get_column_letter(idx + 1)

        for cell in column_cells:
            try:
                if cell.value is not None:
                    cell_value_str = str(cell.value)
                    max_length = max(max_length, len(cell_value_str))
            except Exception as e:
                print_error(f"[열 너비 자동 맞춤] {cell.coordinate}에서 예외 발생: {e}")

        adjusted_width = max_length + 2 if max_length > 0 else 10
        ws.column_dimensions[column_letter].width = adjusted_width  # type: ignore

    wb.save(path)
    wb.close()


def _find_excel_files(download_dir: str, file_prefix: str) -> list[str]:
    """Finds a list of Excel files in the specified directory based on prefix
    and extension."""
    if not download_dir or not os.path.isdir(download_dir):
        raise EnvironmentError(f"다운로드 디렉토리를 찾을 수 없습니다: {download_dir}")

    return [
        f
        for f in os.listdir(download_dir)
        if f.startswith(file_prefix) and f.lower().endswith(cfg.EXCEL_EXTENSIONS)
    ]


def _merge_and_preprocess_files(
    excel_files: list[str], download_dir: str
) -> pd.DataFrame | None:
    """Reads the list of Excel files, merges them into a single DataFrame,
    and preprocesses it."""
    all_dfs = []
    for file_name in excel_files:
        file_path = os.path.join(download_dir, file_name)
        try:
            if file_path.lower().endswith(".xlsx"):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_excel(file_path, engine="xlrd")
            all_dfs.append(df)
        except Exception as e:
            print_error(f"'{file_name}' 파일 처리 중 오류 발생: {e}")
            return None

    if not all_dfs:
        return None

    merged_df = pd.concat(all_dfs, ignore_index=True)

    # Standardize access time columns ("접근일시", "일시") to the standard name
    if cfg.COL_ALT_ACCESS_TIME_1 in merged_df.columns:
        merged_df.rename(
            columns={cfg.COL_ALT_ACCESS_TIME_1: cfg.COL_ACCESS_TIME},
            inplace=True,
        )
    elif cfg.COL_ALT_ACCESS_TIME_2 in merged_df.columns:
        merged_df.rename(
            columns={cfg.COL_ALT_ACCESS_TIME_2: cfg.COL_ACCESS_TIME},
            inplace=True,
        )

    # 표준화된 "접속일시" 컬럼이 존재하면 datetime으로 변환
    if cfg.COL_ACCESS_TIME in merged_df.columns:
        merged_df[cfg.COL_ACCESS_TIME] = pd.to_datetime(merged_df[cfg.COL_ACCESS_TIME])

    # "교번" 또는 "신분번호" 컬럼을 "교직원ID"로 표준화
    has_gyobeon = "교번" in merged_df.columns
    has_sinbun = "신분번호" in merged_df.columns

    if has_gyobeon and has_sinbun:
        print_info(
            "경고: 입력 파일에 '교번'과 '신분번호' 컬럼이 모두 존재합니다. "
            "'교번'을 '교직원ID'로 우선 사용합니다."
        )
        merged_df.rename(columns={"교번": cfg.COL_EMPLOYEE_ID}, inplace=True)
    elif has_gyobeon:
        merged_df.rename(columns={"교번": cfg.COL_EMPLOYEE_ID}, inplace=True)
    elif has_sinbun:
        merged_df.rename(columns={"신분번호": cfg.COL_EMPLOYEE_ID}, inplace=True)

    return merged_df


def find_and_prepare_excel_file(
    download_dir: str,
    file_prefix: str,
    save_dir: str,
    output_file_basename: str,
    prev_month: str,
) -> tuple[pd.DataFrame | None, str | None]:
    """
    Finds, merges, preprocesses, and saves Excel files from the specified folder.

    This function performs the following:
    1. Uses `_find_excel_files` to find relevant files.
    2. Uses `_merge_and_preprocess_files` to merge and preprocess the files.
    3. Saves the merged DataFrame as an intermediate result.
    """
    try:
        excel_files = _find_excel_files(download_dir, file_prefix)
        if not excel_files:
            print_info(
                f"'{file_prefix}'로 시작하는 파일을 찾을 수 없습니다. "
                f"이 검사는 건너뜁니다."
            )
            return None, None
    except EnvironmentError as e:
        print_error(str(e))
        return None, None

    merged_df = _merge_and_preprocess_files(excel_files, download_dir)
    if merged_df is None:
        return None, None

    print_info(f"{output_file_basename} 원본 데이터: {len(merged_df)}건")

    os.makedirs(save_dir, exist_ok=True)
    destination_save_path = os.path.join(
        save_dir, f"{output_file_basename}_{prev_month}.xlsx"
    )
    try:
        merged_df.to_excel(destination_save_path, index=False)
        save_msg = (
            f"모든 파일을 합쳐 '{os.path.basename(destination_save_path)}'"
            f"(으)로 저장했습니다."
        )
        print_info(save_msg)
    except Exception as e:
        print_error(f"병합된 파일 저장 중 오류 발생: {e}")
        return None, None

    return merged_df, destination_save_path


def zip_files_by_prefix(target_dir: str, prefix_list: list[str]):
    """
    Creates zip archives using the part before '_' in filenames
    (e.g., Attachment N ...) as the zip name.
    """
    files = [f for f in os.listdir(target_dir) if f.endswith(".xlsx")]

    for prefix in prefix_list:
        matched = [f for f in files if f.startswith(prefix)]
        if not matched:
            print_zip_warning(prefix)
            continue

        group_name = matched[0].split("_")[0].split("(")[0]
        zip_name = f"{group_name}.zip"
        zip_path = os.path.join(target_dir, zip_name)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for filename in matched:
                zipf.write(os.path.join(target_dir, filename), arcname=filename)

        print_zip_result(zip_name, len(matched))


def filter_by_time_conditions(
    df: pd.DataFrame,
    time_col: str,
    employee_id_col: str,
    check_off_hours: bool,
    check_holidays_weekends: bool,
    off_hours_start: int,
    off_hours_end: int,
) -> pd.DataFrame:
    """
    Filters the DataFrame based on time conditions (off-hours, holidays/weekends).

    Parameters:
        df (pd.DataFrame): The DataFrame to filter.
        time_col (str): The column name containing timestamp information.
        employee_id_col (str): The column name containing employee ID.
        check_off_hours (bool): Whether to enable off-hours checking.
        check_holidays_weekends (bool): Whether to enable holidays and
        weekends checking.
        off_hours_start (int): The start time for off-hours.
        off_hours_end (int): The end time for off-hours.

    Returns:
        pd.DataFrame: The filtered DataFrame meeting the specified time conditions.
    """
    if df is None:
        raise ValueError("Input DataFrame cannot be None.")

    df_copy = df.copy()

    final_mask = pd.Series(False, index=df.index)

    if check_off_hours:
        hour = df_copy[time_col].dt.hour
        is_off_hour = (hour < off_hours_end) | (hour >= off_hours_start)
        final_mask |= is_off_hour

    if check_holidays_weekends:
        years = df_copy[time_col].dt.year.unique()
        kr_holidays = holidays.KR(years=years)  # type: ignore [attr-defined]
        weekday = df_copy[time_col].dt.weekday
        date_only = df_copy[time_col].dt.date

        is_weekend = weekday >= 5  # Monday is 0, Sunday is 6
        is_holiday = date_only.isin(kr_holidays)
        final_mask |= is_weekend
        final_mask |= is_holiday

    return df_copy[final_mask].sort_values([employee_id_col, time_col])


def run_and_save_check(
    df: pd.DataFrame,
    check_func,
    save_path: str,
    result_description: str,
):
    """
    Runs the check function, saves the result to an Excel file if any, and
    outputs a status message.

    Parameters:
        df (pd.DataFrame): The input DataFrame to perform the check on.
        check_func (function): A function that takes a DataFrame and returns
        a filtered DataFrame.
        save_path (str): The path where the result Excel file will be saved.
        result_description (str): The description to use in the output message
        when results are found or not found.
    """
    filtered_df = check_func(df)
    if not filtered_df.empty:
        save_excel_with_autofit(filtered_df, save_path)
        print_result(
            is_detected=True,
            description=result_description,
            filename=os.path.basename(save_path),
        )
    else:
        print_result(is_detected=False, description=result_description)
