import os
from datetime import datetime

import pandas as pd

from src import utils


class TestGetPrevMonthYyyymm:
    def test_get_prev_month_yyyymm(self, mocker):
        # Mock datetime.today to return a fixed date
        mock_today = mocker.patch("src.utils.datetime")
        mock_today.today.return_value = datetime(2023, 10, 15)
        mock_today.return_value = datetime

        result = utils.get_prev_month_yyyymm()
        assert result == "202309"


class TestMakeSaveDir:
    def test_make_save_dir_creates_dir(self, temp_dir, mocker):
        mocker.patch("src.utils.get_prev_month_yyyymm", return_value="202309")
        base_dir = temp_dir
        result = utils.make_save_dir(base_dir)
        expected = os.path.join(base_dir, "202309")
        assert result == expected
        assert os.path.exists(expected)

    def test_make_save_dir_existing_dir(self, temp_dir, mocker):
        mocker.patch("src.utils.get_prev_month_yyyymm", return_value="202309")
        base_dir = temp_dir
        existing_dir = os.path.join(base_dir, "202309")
        os.makedirs(existing_dir)
        result = utils.make_save_dir(base_dir)
        assert result == existing_dir


class TestSaveExcelWithAutofit:
    def test_save_excel_with_autofit(self, temp_dir, sample_personal_access_df):
        path = os.path.join(temp_dir, "test.xlsx")
        utils.save_excel_with_autofit(sample_personal_access_df, path)
        assert os.path.exists(path)
        # Check if it's a valid Excel file by reading it back
        df_read = pd.read_excel(path)
        pd.testing.assert_frame_equal(df_read, sample_personal_access_df)


class TestFindExcelFiles:
    def test_find_excel_files(self, temp_dir):
        # Create test files
        os.makedirs(temp_dir)
        open(os.path.join(temp_dir, "test.xlsx"), "w").close()
        open(os.path.join(temp_dir, "test.xls"), "w").close()
        open(os.path.join(temp_dir, "other.txt"), "w").close()

        result = utils._find_excel_files(temp_dir, "test")
        assert len(result) == 2
        assert "test.xlsx" in result
        assert "test.xls" in result

    def test_find_excel_files_no_files(self, temp_dir):
        result = utils._find_excel_files(temp_dir, "test")
        assert result == []


class TestMergeAndPreprocessFiles:
    def test_merge_and_preprocess_files(self, temp_dir, sample_personal_access_df):
        # Create a test Excel file
        file_path = os.path.join(temp_dir, "test.xlsx")
        sample_personal_access_df.to_excel(file_path, index=False)

        result = utils._merge_and_preprocess_files(["test.xlsx"], temp_dir)
        assert result is not None
        pd.testing.assert_frame_equal(result, sample_personal_access_df)

    def test_merge_and_preprocess_files_no_files(self, temp_dir):
        result = utils._merge_and_preprocess_files([], temp_dir)
        assert result is None


class TestFindAndPrepareExcelFile:
    def test_find_and_prepare_excel_file(
        self, temp_dir, sample_personal_access_df, mocker
    ):
        # Mock print functions
        mocker.patch("src.utils.print_info")
        mocker.patch("src.utils.print_error")

        # Create test file
        file_path = os.path.join(temp_dir, "prefix_202309.xlsx")
        sample_personal_access_df.to_excel(file_path, index=False)

        save_dir = os.path.join(temp_dir, "save")
        os.makedirs(save_dir)

        df, saved_path = utils.find_and_prepare_excel_file(
            temp_dir, "prefix_", save_dir, "test", "202309"
        )
        assert df is not None
        assert saved_path is not None
        assert os.path.exists(saved_path)

    def test_find_and_prepare_excel_file_no_files(self, temp_dir, mocker):
        mocker.patch("src.utils.print_info")
        save_dir = os.path.join(temp_dir, "save")
        os.makedirs(save_dir)

        df, saved_path = utils.find_and_prepare_excel_file(
            temp_dir, "prefix_", save_dir, "test", "202309"
        )
        assert df is None
        assert saved_path is None


class TestZipFilesByPrefix:
    def test_zip_files_by_prefix(self, temp_dir, mocker):
        mocker.patch("src.utils.print_zip_result")
        mocker.patch("src.utils.print_zip_warning")

        # Create test files
        save_dir = temp_dir
        open(os.path.join(save_dir, "[붙임2]file1.xlsx"), "w").close()
        open(os.path.join(save_dir, "[붙임2]file2.xlsx"), "w").close()
        open(os.path.join(save_dir, "other.xlsx"), "w").close()

        utils.zip_files_by_prefix(save_dir, ["[붙임2"])

        zip_path = os.path.join(save_dir, "[붙임2.zip")
        assert os.path.exists(zip_path)


class TestFilterByTimeConditions:
    def test_filter_by_time_conditions_off_hours(self, sample_login_df):
        result = utils.filter_by_time_conditions(
            sample_login_df, "접속일시", "교직원ID", True, False, 23, 7
        )
        # Sample data has times in business hours, result should be empty or filtered
        assert isinstance(result, pd.DataFrame)

    def test_filter_by_time_conditions_holidays(self, sample_login_df, mocker):
        # Mock holidays
        mock_holidays = mocker.patch("src.utils.holidays.KR")
        mock_holidays.return_value = []

        result = utils.filter_by_time_conditions(
            sample_login_df, "접속일시", "교직원ID", False, True, 23, 7
        )
        assert isinstance(result, pd.DataFrame)


class TestRunAndSaveCheck:
    def test_run_and_save_check_with_results(
        self, temp_dir, sample_personal_access_df, mocker
    ):
        mocker.patch("src.utils.print_result")
        mocker.patch("src.utils.save_excel_with_autofit")

        def dummy_check(df):
            return df.head(1)

        path = os.path.join(temp_dir, "test.xlsx")
        utils.run_and_save_check(sample_personal_access_df, dummy_check, path, "test")

    def test_run_and_save_check_no_results(
        self, temp_dir, sample_personal_access_df, mocker
    ):
        mocker.patch("src.utils.print_result")

        def dummy_check(df):
            return pd.DataFrame()

        path = os.path.join(temp_dir, "test.xlsx")
        utils.run_and_save_check(sample_personal_access_df, dummy_check, path, "test")
