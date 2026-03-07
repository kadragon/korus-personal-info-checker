import os
from datetime import datetime

import pandas as pd
import pytest

from src import config as cfg
from src.checkers import download_reason_checker as drc


class TestUniqueCharCountBelow5:
    def test_unique_char_count_below_5_true(self):
        assert drc._unique_char_count_below_5("asdfg")
        assert drc._unique_char_count_below_5("12345")

    def test_unique_char_count_below_5_false(self):
        assert not drc._unique_char_count_below_5("research project")
        assert not drc._unique_char_count_below_5("valid reason")

    def test_unique_char_count_below_5_nan(self):
        assert not drc._unique_char_count_below_5(pd.NA)


class TestHasKoreanJamo:
    def test_detects_consonants(self):
        assert drc._has_korean_jamo("ㄱㄴㄷ")

    def test_detects_vowels(self):
        assert drc._has_korean_jamo("ㅏㅓㅗ")

    def test_detects_mixed_jamo_and_syllables(self):
        assert drc._has_korean_jamo("ㄹㄹㅇ러ㅏ너덜딘ㅇ")

    def test_normal_korean_not_flagged(self):
        assert not drc._has_korean_jamo("연구 목적으로 필요합니다")

    def test_latin_not_flagged(self):
        assert not drc._has_korean_jamo("research project")

    def test_empty_string_not_flagged(self):
        assert not drc._has_korean_jamo("")

    def test_nan_not_flagged(self):
        assert not drc._has_korean_jamo(pd.NA)


class TestIsLatinGibberish:
    def test_keyboard_mashing_detected(self):
        assert drc._is_latin_gibberish("rodsldfwifdk vjnklavjvecss")

    def test_normal_english_not_flagged(self):
        assert not drc._is_latin_gibberish("research project")

    def test_short_string_skipped(self):
        # Fewer than 8 latin chars — skip check even if consonant-heavy
        assert not drc._is_latin_gibberish("asdfg")

    def test_low_vowel_ratio_detected(self):
        # "bcdfghjk" has 0 vowels → ratio 0.0 < 0.2
        assert drc._is_latin_gibberish("bcdfghjkl")

    def test_consonant_cluster_detected(self):
        # 5 consecutive consonants with otherwise normal vowel ratio
        assert drc._is_latin_gibberish("the strngth of words")

    def test_nan_not_flagged(self):
        assert not drc._is_latin_gibberish(pd.NA)


class TestIsSuspiciousReason:
    def test_triggers_via_unique_char_check(self):
        assert drc._is_suspicious_reason("asdfg")

    def test_triggers_via_jamo_check(self):
        assert drc._is_suspicious_reason("ㄹㄹㅇ러ㅏ너덜딘ㅇ")

    def test_triggers_via_latin_gibberish_check(self):
        assert drc._is_suspicious_reason("rodsldfwifdk vjnklavjvecss")

    def test_normal_korean_not_flagged(self):
        assert not drc._is_suspicious_reason("연구 목적으로 필요합니다")

    def test_normal_english_not_flagged(self):
        assert not drc._is_suspicious_reason("research project")

    def test_nan_not_flagged(self):
        assert not drc._is_suspicious_reason(pd.NA)

    def test_none_not_flagged(self):
        assert not drc._is_suspicious_reason(None)


class TestCheckDownloadSayu:
    def test_check_download_sayu_invalid_reasons(self, sample_download_df):
        df = sample_download_df.copy()
        df.loc[0, "다운로드사유"] = "asdfg"  # invalid
        df.loc[1, "다운로드사유"] = "research"  # valid

        result = drc._check_download_sayu(df)
        assert len(result) == 1
        assert result.iloc[0]["교직원ID"] == "emp1"

    def test_check_download_sayu_missing_column(self, sample_download_df):
        df = sample_download_df.drop(columns=["다운로드사유"])

        with pytest.raises(ValueError):
            drc._check_download_sayu(df)

    def test_check_download_sayu_catches_jamo_gibberish(self, sample_download_df):
        df = sample_download_df.copy()
        df.loc[0, "다운로드사유"] = "ㄹㄹㅇ러ㅏ너덜딘ㅇ"  # jamo mashing
        df.loc[1, "다운로드사유"] = "연구 목적으로 필요합니다"  # valid

        result = drc._check_download_sayu(df)
        assert len(result) == 1
        assert result.iloc[0]["교직원ID"] == "emp1"

    def test_check_download_sayu_catches_latin_gibberish(self, sample_download_df):
        df = sample_download_df.copy()
        df.loc[0, "다운로드사유"] = "rodsldfwifdk vjnklavjvecss"  # latin mashing
        df.loc[1, "다운로드사유"] = "연구 목적으로 필요합니다"  # valid

        result = drc._check_download_sayu(df)
        assert len(result) == 1
        assert result.iloc[0]["교직원ID"] == "emp1"

    def test_check_download_sayu_multiple_suspicious(self, sample_download_df):
        df = sample_download_df.copy()
        df.loc[0, "다운로드사유"] = "ㄹㄹㅇ러ㅏ너덜딘ㅇ"  # jamo
        df.loc[1, "다운로드사유"] = "rodsldfwifdk vjnklavjvecss"  # latin gibberish

        result = drc._check_download_sayu(df)
        assert len(result) == 2


class TestFilterHighDownloadUsers:
    def test_filter_high_download_users_above_threshold(self, sample_download_df):
        df = sample_download_df.copy()
        df["다운로드데이터수(건)"] = 50
        df.loc[0, "다운로드데이터수(건)"] = 150  # above 100

        result = drc._filter_high_download_users(df)
        assert len(result) == 1

    def test_filter_high_download_users_below_threshold(self, sample_download_df):
        df = sample_download_df.copy()
        df["다운로드데이터수(건)"] = 50  # below

        result = drc._filter_high_download_users(df)
        assert result.empty

    def test_filter_high_download_users_missing_column(self, sample_download_df):
        df = sample_download_df.drop(columns=["다운로드데이터수(건)"])

        with pytest.raises(ValueError):
            drc._filter_high_download_users(df)


class TestFilterHighFreqDownload:
    def test_filter_high_freq_download_high_freq(self, sample_download_df):
        df = sample_download_df.copy()
        # Add multiple downloads within 1 hour
        for i in range(20):
            new_row = df.iloc[0].copy()
            new_row["접속일시"] = datetime(2023, 9, 1, 10, i)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        result = drc._filter_high_freq_download(df)
        assert len(result) > 0

    def test_filter_high_freq_download_low_freq(self, sample_download_df):
        result = drc._filter_high_freq_download(sample_download_df)
        assert result.empty

    def test_filter_high_freq_download_none_df(self):
        with pytest.raises(ValueError):
            drc._filter_high_freq_download(None)


class TestRunCheck:
    def test_run_check_with_data(self, temp_dir, sample_download_df, mocker):
        mocker.patch("src.checkers.download_reason_checker.print_checker_header")
        mocker.patch(
            "src.checkers.download_reason_checker.find_and_prepare_excel_file",
            return_value=(sample_download_df, "path"),
        )
        mocker.patch(
            "src.checkers.download_reason_checker._load_access_logs",
            return_value=None,
        )
        mocker.patch("src.checkers.download_reason_checker.print_info")
        mocker.patch(
            "src.checkers.download_reason_checker._check_download_sayu",
            return_value=pd.DataFrame(),
        )
        mocker.patch(
            "src.checkers.download_reason_checker._filter_high_download_users",
            return_value=pd.DataFrame(),
        )
        mocker.patch(
            "src.checkers.download_reason_checker._filter_high_freq_download",
            return_value=pd.DataFrame(),
        )
        mocker.patch(
            "src.checkers.download_reason_checker.filter_by_time_conditions",
            return_value=pd.DataFrame(),
        )
        mocker.patch("src.checkers.download_reason_checker.run_and_save_check")

        save_dir = temp_dir
        result = drc.run_check("download_dir", save_dir, "202309")
        assert result == len(sample_download_df)

    def test_run_check_no_data(self, temp_dir, mocker):
        mocker.patch("src.checkers.download_reason_checker.print_checker_header")
        mocker.patch(
            "src.checkers.download_reason_checker.find_and_prepare_excel_file",
            return_value=(None, None),
        )

        save_dir = temp_dir
        result = drc.run_check("download_dir", save_dir, "202309")
        assert result == 0

    def test_run_check_with_access_logs_enriches(
        self, temp_dir, sample_download_df, mocker
    ):
        merged_path = os.path.join(temp_dir, "merged.xlsx")
        access_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: ["emp1"],
            cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 2)],
            cfg.COL_PROGRAM_NAME: ["인사조회"],
            cfg.COL_JOB_PERFORMANCE: ["조회"],
        })
        mocker.patch("src.checkers.download_reason_checker.print_checker_header")
        mocker.patch("src.checkers.download_reason_checker.print_info")
        mocker.patch(
            "src.checkers.download_reason_checker.find_and_prepare_excel_file",
            return_value=(sample_download_df, merged_path),
        )
        mocker.patch(
            "src.checkers.download_reason_checker._load_access_logs",
            return_value=access_df,
        )
        mock_save = mocker.patch(
            "src.checkers.download_reason_checker.run_and_save_check"
        )

        drc.run_check("download_dir", temp_dir, "202309")

        # The df passed to run_and_save_check should have the summary column
        first_call_df = mock_save.call_args_list[0][1]["df"]
        assert cfg.COL_ACCESS_LOG_SUMMARY in first_call_df.columns
        # The merged workbook should be re-saved with enrichment columns
        assert os.path.exists(merged_path)
        saved_df = pd.read_excel(merged_path)
        assert cfg.COL_ACCESS_LOG_SUMMARY in saved_df.columns
        assert cfg.COL_NEAREST_ACCESS_GAP in saved_df.columns

    def test_run_check_without_access_logs_graceful(
        self, temp_dir, sample_download_df, mocker
    ):
        mocker.patch("src.checkers.download_reason_checker.print_checker_header")
        mock_print_info = mocker.patch(
            "src.checkers.download_reason_checker.print_info"
        )
        mocker.patch(
            "src.checkers.download_reason_checker.find_and_prepare_excel_file",
            return_value=(sample_download_df, "path"),
        )
        mocker.patch(
            "src.checkers.download_reason_checker._load_access_logs",
            return_value=None,
        )
        mocker.patch("src.checkers.download_reason_checker.run_and_save_check")

        result = drc.run_check("download_dir", temp_dir, "202309")
        assert result == len(sample_download_df)
        # Should have logged a warning about missing access logs
        warning_calls = [
            c for c in mock_print_info.call_args_list
            if "접속기록" in str(c)
        ]
        assert len(warning_calls) > 0


class TestEnrichWithAccessLogSummary:
    def test_empty_access_log_preserves_original(self, sample_download_df):
        access_df = pd.DataFrame(
            columns=[cfg.COL_EMPLOYEE_ID, cfg.COL_ACCESS_TIME,
                     cfg.COL_PROGRAM_NAME, cfg.COL_JOB_PERFORMANCE]
        )
        result = drc._enrich_with_access_log_summary(
            sample_download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        assert len(result) == len(sample_download_df)
        assert cfg.COL_ACCESS_LOG_SUMMARY in result.columns
        assert cfg.COL_NEAREST_ACCESS_GAP in result.columns
        assert all(result[cfg.COL_ACCESS_LOG_SUMMARY] == "")

    def test_window_match_produces_summary(self, sample_download_df):
        access_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: ["emp1"],
            cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 2)],
            cfg.COL_PROGRAM_NAME: ["인사조회"],
            cfg.COL_JOB_PERFORMANCE: ["조회"],
        })
        result = drc._enrich_with_access_log_summary(
            sample_download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        summary = result.loc[
            result[cfg.COL_EMPLOYEE_ID] == "emp1", cfg.COL_ACCESS_LOG_SUMMARY
        ].iloc[0]
        assert summary == "인사조회(조회)"

    def test_matched_gap_is_zero(self, sample_download_df):
        access_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: ["emp1"],
            cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 2)],
            cfg.COL_PROGRAM_NAME: ["인사조회"],
            cfg.COL_JOB_PERFORMANCE: ["조회"],
        })
        result = drc._enrich_with_access_log_summary(
            sample_download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        gap = result.loc[
            result[cfg.COL_EMPLOYEE_ID] == "emp1", cfg.COL_NEAREST_ACCESS_GAP
        ].iloc[0]
        assert gap == 0

    def test_outside_window_no_match(self, sample_download_df):
        access_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: ["emp1"],
            cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 10)],
            cfg.COL_PROGRAM_NAME: ["인사조회"],
            cfg.COL_JOB_PERFORMANCE: ["조회"],
        })
        result = drc._enrich_with_access_log_summary(
            sample_download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        summary = result.loc[
            result[cfg.COL_EMPLOYEE_ID] == "emp1", cfg.COL_ACCESS_LOG_SUMMARY
        ].iloc[0]
        assert summary == ""

    def test_different_employee_no_match(self, sample_download_df):
        access_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: ["emp999"],
            cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 2)],
            cfg.COL_PROGRAM_NAME: ["인사조회"],
            cfg.COL_JOB_PERFORMANCE: ["조회"],
        })
        result = drc._enrich_with_access_log_summary(
            sample_download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        assert all(result[cfg.COL_ACCESS_LOG_SUMMARY] == "")

    def test_duplicate_program_job_shows_xN(self, sample_download_df):
        access_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: ["emp1", "emp1", "emp1"],
            cfg.COL_ACCESS_TIME: [
                datetime(2023, 9, 1, 10, 1),
                datetime(2023, 9, 1, 10, 2),
                datetime(2023, 9, 1, 10, 3),
            ],
            cfg.COL_PROGRAM_NAME: ["인사조회", "인사조회", "급여조회"],
            cfg.COL_JOB_PERFORMANCE: ["조회", "조회", "조회"],
        })
        result = drc._enrich_with_access_log_summary(
            sample_download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        summary = result.loc[
            result[cfg.COL_EMPLOYEE_ID] == "emp1", cfg.COL_ACCESS_LOG_SUMMARY
        ].iloc[0]
        assert "인사조회(조회) x2" in summary
        assert "급여조회(조회)" in summary

    def test_unmatched_gap_shows_minutes(self, sample_download_df):
        # Access log at 10:10 is 10 min away from download at 10:00
        access_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: ["emp1"],
            cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 10)],
            cfg.COL_PROGRAM_NAME: ["인사조회"],
            cfg.COL_JOB_PERFORMANCE: ["조회"],
        })
        result = drc._enrich_with_access_log_summary(
            sample_download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        gap = result.loc[
            result[cfg.COL_EMPLOYEE_ID] == "emp1", cfg.COL_NEAREST_ACCESS_GAP
        ].iloc[0]
        assert gap == 10.0
        # Summary should be empty (outside window)
        summary = result.loc[
            result[cfg.COL_EMPLOYEE_ID] == "emp1", cfg.COL_ACCESS_LOG_SUMMARY
        ].iloc[0]
        assert summary == ""

    def test_no_employee_in_access_gap_is_nan(self, sample_download_df):
        access_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: ["emp999"],
            cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 2)],
            cfg.COL_PROGRAM_NAME: ["인사조회"],
            cfg.COL_JOB_PERFORMANCE: ["조회"],
        })
        result = drc._enrich_with_access_log_summary(
            sample_download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        gap_emp1 = result.loc[
            result[cfg.COL_EMPLOYEE_ID] == "emp1", cfg.COL_NEAREST_ACCESS_GAP
        ].iloc[0]
        assert pd.isna(gap_emp1)

    def test_summary_includes_detail_content(self):
        download_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: ["emp1"],
            cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 0)],
            cfg.COL_DOWNLOAD_REASON: ["연구"],
            cfg.COL_DOWNLOAD_COUNT: [10],
        })
        access_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: ["emp1"],
            cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 2)],
            cfg.COL_PROGRAM_NAME: ["인사조회"],
            cfg.COL_JOB_PERFORMANCE: ["조회"],
            cfg.COL_DETAIL_CONTENT: ["sklstfNo=12345&param=value"],
        })
        result = drc._enrich_with_access_log_summary(
            download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        summary = result[cfg.COL_ACCESS_LOG_SUMMARY].iloc[0]
        assert "인사조회(조회)" in summary
        assert "[sklstfNo=12345&param=value]" in summary

    def test_detail_content_truncated_at_50(self):
        long_detail = "A" * 80
        download_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: ["emp1"],
            cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 0)],
            cfg.COL_DOWNLOAD_REASON: ["연구"],
            cfg.COL_DOWNLOAD_COUNT: [10],
        })
        access_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: ["emp1"],
            cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 2)],
            cfg.COL_PROGRAM_NAME: ["인사조회"],
            cfg.COL_JOB_PERFORMANCE: ["조회"],
            cfg.COL_DETAIL_CONTENT: [long_detail],
        })
        result = drc._enrich_with_access_log_summary(
            download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        summary = result[cfg.COL_ACCESS_LOG_SUMMARY].iloc[0]
        assert "[" + "A" * 50 + "...]" in summary

    def test_no_detail_column_still_works(self):
        download_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: ["emp1"],
            cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 0)],
            cfg.COL_DOWNLOAD_REASON: ["연구"],
            cfg.COL_DOWNLOAD_COUNT: [10],
        })
        # Access log without 상세내용 column
        access_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: ["emp1"],
            cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 2)],
            cfg.COL_PROGRAM_NAME: ["인사조회"],
            cfg.COL_JOB_PERFORMANCE: ["조회"],
        })
        result = drc._enrich_with_access_log_summary(
            download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        summary = result[cfg.COL_ACCESS_LOG_SUMMARY].iloc[0]
        assert summary == "인사조회(조회)"
        assert "[" not in summary

    def test_dtype_mismatch_int_vs_str(self):
        download_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: [12345],
            cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 0)],
            cfg.COL_DOWNLOAD_REASON: ["연구"],
            cfg.COL_DOWNLOAD_COUNT: [10],
        })
        access_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: ["12345"],
            cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 2)],
            cfg.COL_PROGRAM_NAME: ["인사조회"],
            cfg.COL_JOB_PERFORMANCE: ["조회"],
        })
        result = drc._enrich_with_access_log_summary(
            download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        summary = result[cfg.COL_ACCESS_LOG_SUMMARY].iloc[0]
        assert summary == "인사조회(조회)"

    def test_dtype_mismatch_float_vs_str(self):
        download_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: [12345.0],
            cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 0)],
            cfg.COL_DOWNLOAD_REASON: ["연구"],
            cfg.COL_DOWNLOAD_COUNT: [10],
        })
        access_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: ["12345"],
            cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 2)],
            cfg.COL_PROGRAM_NAME: ["인사조회"],
            cfg.COL_JOB_PERFORMANCE: ["조회"],
        })
        result = drc._enrich_with_access_log_summary(
            download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        summary = result[cfg.COL_ACCESS_LOG_SUMMARY].iloc[0]
        assert summary == "인사조회(조회)"

    def test_missing_required_columns_graceful(self):
        download_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: ["emp1"],
            cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 0)],
            cfg.COL_DOWNLOAD_REASON: ["연구"],
            cfg.COL_DOWNLOAD_COUNT: [10],
        })
        access_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: ["emp1"],
            cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 2)],
        })
        result = drc._enrich_with_access_log_summary(
            download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        assert len(result) == len(download_df)
        assert cfg.COL_ACCESS_LOG_SUMMARY in result.columns
        assert all(result[cfg.COL_ACCESS_LOG_SUMMARY] == "")


class TestLoadAccessLogs:
    def test_returns_none_when_no_files(self, temp_dir, mocker):
        mocker.patch(
            "src.checkers.download_reason_checker._find_excel_files",
            return_value=[],
        )
        mocker.patch("src.checkers.download_reason_checker.print_info")
        result = drc._load_access_logs(temp_dir, "202309")
        assert result is None

    def test_returns_none_on_environment_error(self, temp_dir, mocker):
        mocker.patch(
            "src.checkers.download_reason_checker._find_excel_files",
            side_effect=EnvironmentError("bad dir"),
        )
        mock_info = mocker.patch(
            "src.checkers.download_reason_checker.print_info"
        )
        result = drc._load_access_logs(temp_dir, "202309")
        assert result is None
        assert any("오류 발생" in str(c) for c in mock_info.call_args_list)

    def test_returns_none_on_merge_failure(self, temp_dir, mocker):
        mocker.patch(
            "src.checkers.download_reason_checker._find_excel_files",
            return_value=["file.xlsx"],
        )
        mocker.patch(
            "src.checkers.download_reason_checker._merge_and_preprocess_files",
            return_value=None,
        )
        mock_info = mocker.patch(
            "src.checkers.download_reason_checker.print_info"
        )
        result = drc._load_access_logs(temp_dir, "202309")
        assert result is None
        assert any("실패" in str(c) for c in mock_info.call_args_list)

    def test_happy_path_returns_deduplicated_df(self, temp_dir, mocker):
        raw_df = pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: ["emp1", "emp1"],
            cfg.COL_ACCESS_TIME: [
                datetime(2023, 9, 1, 10, 0),
                datetime(2023, 9, 1, 10, 0),
            ],
            cfg.COL_PROGRAM_NAME: ["인사조회", "인사조회"],
            cfg.COL_JOB_PERFORMANCE: ["조회", "조회"],
        })
        mocker.patch(
            "src.checkers.download_reason_checker._find_excel_files",
            return_value=["file.xlsx"],
        )
        mocker.patch(
            "src.checkers.download_reason_checker._merge_and_preprocess_files",
            return_value=raw_df,
        )
        mocker.patch("src.checkers.download_reason_checker.print_info")
        result = drc._load_access_logs(temp_dir, "202309")
        assert result is not None
        assert len(result) == 1

    def test_uses_prev_month_for_prefix(self, temp_dir, mocker):
        mock_find = mocker.patch(
            "src.checkers.download_reason_checker._find_excel_files",
            return_value=[],
        )
        mocker.patch("src.checkers.download_reason_checker.print_info")
        drc._load_access_logs(temp_dir, "202512")
        called_prefix = mock_find.call_args[0][1]
        assert "202512" in called_prefix


class TestRunCheckErrorIsolation:
    def test_enrichment_error_does_not_crash_checks(
        self, temp_dir, sample_download_df, mocker
    ):
        mocker.patch("src.checkers.download_reason_checker.print_checker_header")
        mock_info = mocker.patch(
            "src.checkers.download_reason_checker.print_info"
        )
        mocker.patch(
            "src.checkers.download_reason_checker.find_and_prepare_excel_file",
            return_value=(sample_download_df, None),
        )
        mocker.patch(
            "src.checkers.download_reason_checker._load_access_logs",
            return_value=pd.DataFrame({"dummy": [1]}),
        )
        mocker.patch(
            "src.checkers.download_reason_checker._enrich_with_access_log_summary",
            side_effect=KeyError("missing column"),
        )
        mock_run_save = mocker.patch(
            "src.checkers.download_reason_checker.run_and_save_check"
        )

        result = drc.run_check("download_dir", temp_dir, "202309")

        assert result == len(sample_download_df)
        assert mock_run_save.call_count == 4
        assert any("오류 발생" in str(c) for c in mock_info.call_args_list)
