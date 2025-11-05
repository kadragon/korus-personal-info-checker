"""
Tests for personal_file_checker module.

GENERATED FROM SPEC-test-coverage-improvement-1
Trace: SPEC-test-coverage-improvement-1, TEST-personal-file-checker-1
"""

import os

import pandas as pd
import pytest

from src.checkers import personal_file_checker as pfc
from src import config as cfg


class TestFilterByJobMasterExcludeDetailId:
    def test_filter_hr_master_exclude_self(self, sample_personal_access_df):
        # Modify sample data to have HR master access
        df = sample_personal_access_df.copy()
        df.loc[0, "프로그램명"] = "인사마스터"
        df.loc[0, "상세내용"] = "emp1 details"  # self access, should be excluded
        df.loc[1, "프로그램명"] = "인사마스터"
        df.loc[1, "상세내용"] = "other details"  # not self, should be included

        result = pfc._filter_by_job_master_exclude_detail_id(df)
        assert len(result) == 1
        assert result.iloc[0]["교직원ID"] == "emp2"

    def test_filter_no_hr_master(self, sample_personal_access_df):
        df = sample_personal_access_df.copy()
        df["프로그램명"] = "기타"

        result = pfc._filter_by_job_master_exclude_detail_id(df)
        assert result.empty

    def test_filter_missing_columns(self, sample_personal_access_df):
        df = sample_personal_access_df.drop(columns=["프로그램명"])

        with pytest.raises(ValueError):
            pfc._filter_by_job_master_exclude_detail_id(df)


class TestExtractAndSaveByJob:
    def test_extract_and_save_by_job_above_threshold(
        self, temp_dir, sample_personal_access_df, mocker
    ):
        mock_print_result = mocker.patch(
            "src.checkers.personal_file_checker.print_result"
        )

        df = sample_personal_access_df.copy()
        # Add more rows to exceed threshold
        for _ in range(1000):
            new_row = df.iloc[0].copy()
            new_row["교직원ID"] = "emp1"
            new_row["수행업무"] = "조회"
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        save_path = os.path.join(temp_dir, "test.xlsx")
        pfc._extract_and_save_by_job(df, save_path, "조회", 100, "수행업무")

        # Verify file was created
        assert os.path.exists(save_path)
        # Verify print_result was called with detection
        mock_print_result.assert_called_once()
        assert mock_print_result.call_args[1]["is_detected"] is True

    def test_extract_and_save_by_job_below_threshold(
        self, temp_dir, sample_personal_access_df, mocker
    ):
        mock_print_result = mocker.patch(
            "src.checkers.personal_file_checker.print_result"
        )

        df = sample_personal_access_df.copy()
        save_path = os.path.join(temp_dir, "test.xlsx")
        pfc._extract_and_save_by_job(df, save_path, "조회", 1000, "수행업무")

        # Verify file was NOT created
        assert not os.path.exists(save_path)
        # Verify print_result was called with no detection
        mock_print_result.assert_called_once_with(
            is_detected=False, description="조회 1000건 이상"
        )

    def test_extract_and_save_by_job_missing_columns(self, sample_personal_access_df):
        df = sample_personal_access_df.drop(columns=["교직원ID"])

        with pytest.raises(ValueError):
            pfc._extract_and_save_by_job(df, "path", "조회", 100, "수행업무")

    def test_extract_and_save_by_job_long_sheet_name(
        self, temp_dir, sample_personal_access_df, mocker
    ):
        """Test _extract_and_save_by_job with very long employee name (line 236)."""
        mock_print_result = mocker.patch(
            "src.checkers.personal_file_checker.print_result"
        )

        df = sample_personal_access_df.copy()
        # Create a very long name that will exceed SHEET_NAME_MAX_CHARS (31)
        very_long_name = "매우긴이름을가진직원입니다정말로긴이름"
        df.loc[0, "성명"] = very_long_name
        df.loc[0, "교직원ID"] = "employee123456"

        # Add more rows to exceed threshold
        for _ in range(1000):
            new_row = df.iloc[0].copy()
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        save_path = os.path.join(temp_dir, "test.xlsx")
        pfc._extract_and_save_by_job(df, save_path, "조회", 100, "수행업무")

        # Verify file was created
        assert os.path.exists(save_path)

        # Verify sheet name was truncated
        # Read the Excel file and check sheet names
        import openpyxl
        wb = openpyxl.load_workbook(save_path)
        sheet_names = wb.sheetnames

        # At least one sheet should exist
        assert len(sheet_names) > 0

        # Check that all sheet names are within the max length
        for sheet_name in sheet_names:
            assert len(sheet_name) <= cfg.SHEET_NAME_MAX_CHARS

        wb.close()


class TestRunCheck:
    def test_run_check_with_data(self, temp_dir, sample_personal_access_df, mocker):
        mocker.patch("src.checkers.personal_file_checker.print_checker_header")
        mocker.patch(
            "src.checkers.personal_file_checker.find_and_prepare_excel_file",
            return_value=(sample_personal_access_df, "path"),
        )
        mocker.patch(
            "src.checkers.personal_file_checker._filter_by_job_master_exclude_detail_id",
            return_value=pd.DataFrame(),
        )
        mocker.patch("src.checkers.personal_file_checker._extract_and_save_by_job")
        mocker.patch("src.checkers.personal_file_checker.run_and_save_check")

        save_dir = temp_dir
        result = pfc.run_check("download_dir", save_dir, "202309")
        assert result == len(sample_personal_access_df)

    def test_run_check_no_data(self, temp_dir, mocker):
        mocker.patch("src.checkers.personal_file_checker.print_checker_header")
        mocker.patch(
            "src.checkers.personal_file_checker.find_and_prepare_excel_file",
            return_value=(None, None),
        )

        save_dir = temp_dir
        result = pfc.run_check("download_dir", save_dir, "202309")
        assert result == 0
