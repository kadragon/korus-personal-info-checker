"""
Main script to execute the data inspection process.

This script dynamically discovers and runs all checker modules within the
`checkers` package.
Each checker must be named in the format `*_checker.py` and contain a main
function named `*_checker`.

After setting up necessary configurations such as environment variables for directories,
it calls the main function of each checker.
This script is designed to be executed as the application's primary entry point.
"""

import importlib
import os
import pkgutil
from types import ModuleType

from dotenv import load_dotenv

from . import checkers
from .config import ZIP_FILE_PREFIXES
from .display import (
    print_error,
    print_header,
    print_info,
    print_summary,
    print_zip_header,
)
from .utils import (
    get_prev_month_yyyymm,
    make_korus_save_dir,
    make_save_dir,
    zip_files_by_prefix,
)

# .env 파일이 있는 경우 환경 변수를 로드합니다.
# DOWNLOAD_DIR 및 SAVE_DIR을 하드코딩하지 않고 구성하는 데 유용합니다.
load_dotenv()
download_dir = os.getenv("DOWNLOAD_DIR")  # 원본 Excel 파일이 있는 디렉토리입니다.
base_save_dir = os.getenv("SAVE_DIR")  # 출력 보고서가 저장될 기본 디렉토리입니다.


def discover_and_run_checkers(
    download_dir: str, reports_save_dir: str, prev_month_str: str
) -> int:
    """
    Dynamically discovers and runs all checker modules within the `checkers` package.
    """
    total_count = 0
    for module_info in pkgutil.iter_modules(checkers.__path__):
        module_name = module_info.name
        if not module_name.endswith("_checker"):
            continue

        try:
            module: ModuleType = importlib.import_module(
                f".{module_name}", package=checkers.__name__
            )
            checker_func_name = "run_check"  # 표준 진입점 함수 이름
            checker_func = getattr(module, checker_func_name, None)

            if callable(checker_func):
                result = checker_func(download_dir, reports_save_dir, prev_month_str)
                # checker_func의 반환값이 None일 경우를 대비하여 0으로 처리
                count = result if isinstance(result, int) else 0
                total_count += count
            else:
                print_error(
                    f"'{module_name}' 모듈에서 '{checker_func_name}' 함수를 "
                    f"찾을 수 없거나 실행할 수 없습니다."
                )

        except Exception as e:
            print_error(f"'{module_name}' 검사 중 예상치 못한 오류 발생: {e}")

    return total_count


def _run_inspection(
    download_dir: str, reports_save_dir: str, prev_month_str: str
) -> None:
    """
    Runs the inspection workflow: prints info, discovers/runs checkers,
    zips results, and prints summary.
    """
    print_header(f"개인정보 처리 현황 자동 점검 ({prev_month_str}월분)")
    print_info(f"원본 데이터 경로: {download_dir}")
    print_info(f"결과 저장 경로: {reports_save_dir}")

    total_count = discover_and_run_checkers(
        download_dir, reports_save_dir, prev_month_str
    )

    print_zip_header()
    try:
        zip_files_by_prefix(reports_save_dir, ZIP_FILE_PREFIXES)
    except Exception as e:
        print_error(f"압축 작업 중 오류 발생: {e}")

    print_summary(reports_save_dir, total_count)


def run_with_download_dir(download_dir: str) -> None:
    """
    Executes the data inspection process using the selected download directory.

    The report directory is created as a `korus_YYYYMM` folder inside the
    selected download directory.
    """
    prev_month_str = get_prev_month_yyyymm()
    reports_save_dir = make_korus_save_dir(download_dir, prev_month_str)
    _run_inspection(download_dir, reports_save_dir, prev_month_str)


def main() -> None:
    """
    Main function to execute the data inspection process.

    Determines the target month for analysis (previous month), creates the
    necessary save directory structure,
    and dynamically discovers and runs all checkers within the `checkers` package.
    """
    if not base_save_dir:
        print_error(
            "SAVE_DIR 환경 변수가 설정되지 않았습니다. "
            ".env 파일이나 환경에서 설정해주세요."
        )
        return
    if not download_dir:
        print_error(
            "DOWNLOAD_DIR 환경 변수가 설정되지 않았습니다. "
            ".env 파일이나 환경에서 설정해주세요."
        )
        return

    prev_month_str = get_prev_month_yyyymm()
    reports_save_dir = make_save_dir(base_save_dir)
    _run_inspection(download_dir, reports_save_dir, prev_month_str)


if __name__ == "__main__":
    main()
