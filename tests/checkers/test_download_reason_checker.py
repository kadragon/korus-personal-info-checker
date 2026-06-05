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


class TestFilterHighFreqDownloadFreeze:
    """Golden characterization — freezes detection output so the vectorized
    rewrite cannot drift (PIPA: flagged row-set must stay bit-identical).

    Threshold = 20 downloads within a 1-hour window (DOWNLOAD_FREQUENCY_THRESHOLD).
    """

    def _frame(self) -> pd.DataFrame:
        rows = []
        # E1: exactly 20 downloads inside one hour -> the whole burst flags.
        for i in range(20):
            rows.append(("E1", datetime(2026, 5, 1, 9, i)))
        # E2: 19 downloads inside one hour -> below threshold, never flagged.
        for i in range(19):
            rows.append(("E2", datetime(2026, 5, 1, 11, i)))
        # E3: 3 downloads spread across days -> never in a dense window.
        for d in range(3):
            rows.append(("E3", datetime(2026, 5, 1 + d, 14, 0)))
        return pd.DataFrame({
            cfg.COL_EMPLOYEE_ID: [r[0] for r in rows],
            cfg.COL_ACCESS_TIME: [r[1] for r in rows],
            cfg.COL_DOWNLOAD_REASON: ["x"] * len(rows),
            cfg.COL_DOWNLOAD_COUNT: [1] * len(rows),
        })

    def test_frozen_flagged_set(self):
        result = drc._filter_high_freq_download(self._frame())
        # Exactly E1's 20-row burst, nothing else.
        assert len(result) == 20
        assert set(result[cfg.COL_EMPLOYEE_ID]) == {"E1"}
        # Sorted by (employee, time) — first row is the burst start.
        assert result.iloc[0][cfg.COL_ACCESS_TIME] == datetime(2026, 5, 1, 9, 0)

    def test_threshold_boundary_excludes_19(self):
        result = drc._filter_high_freq_download(self._frame())
        assert "E2" not in set(result[cfg.COL_EMPLOYEE_ID])
        assert "E3" not in set(result[cfg.COL_EMPLOYEE_ID])


class TestRunCheck:
    def test_run_check_with_data(self, temp_dir, sample_download_df, mocker):
        mocker.patch("src.checkers.download_reason_checker.print_checker_header")
        mocker.patch(
            "src.checkers.download_reason_checker.load_merged_excel",
            return_value=sample_download_df,
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
        mocker.patch("src.checkers.download_reason_checker.save_excel_with_autofit")
        mocker.patch("src.checkers.download_reason_checker.run_pipeline")

        save_dir = temp_dir
        result = drc.run_check("download_dir", save_dir, "202309")
        assert result == len(sample_download_df)

    def test_run_check_no_data(self, temp_dir, mocker):
        mocker.patch("src.checkers.download_reason_checker.print_checker_header")
        mocker.patch(
            "src.checkers.download_reason_checker.load_merged_excel",
            return_value=None,
        )

        save_dir = temp_dir
        result = drc.run_check("download_dir", save_dir, "202309")
        assert result == 0

    def test_run_check_with_access_logs_enriches(
        self, temp_dir, sample_download_df, mocker
    ):
        access_df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1"],
                cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 2)],
                cfg.COL_PROGRAM_NAME: ["인사조회"],
                cfg.COL_JOB_PERFORMANCE: ["조회"],
            }
        )
        mocker.patch("src.checkers.download_reason_checker.print_checker_header")
        mocker.patch("src.checkers.download_reason_checker.print_info")
        mocker.patch(
            "src.checkers.download_reason_checker.load_merged_excel",
            return_value=sample_download_df,
        )
        mocker.patch(
            "src.checkers.download_reason_checker._load_access_logs",
            return_value=access_df,
        )
        mocker.patch("src.checkers.download_reason_checker.run_pipeline")
        mocker.patch("src.checkers.download_reason_checker.save_excel_with_autofit")

        result = drc.run_check("download_dir", temp_dir, "202309")

        assert result == len(sample_download_df)

    def test_run_check_without_access_logs_graceful(
        self, temp_dir, sample_download_df, mocker
    ):
        mocker.patch("src.checkers.download_reason_checker.print_checker_header")
        mock_print_info = mocker.patch(
            "src.checkers.download_reason_checker.print_info"
        )
        mocker.patch(
            "src.checkers.download_reason_checker.load_merged_excel",
            return_value=sample_download_df,
        )
        mocker.patch(
            "src.checkers.download_reason_checker._load_access_logs",
            return_value=None,
        )
        mocker.patch("src.checkers.download_reason_checker.save_excel_with_autofit")
        mocker.patch("src.checkers.download_reason_checker.run_pipeline")

        result = drc.run_check("download_dir", temp_dir, "202309")
        assert result == len(sample_download_df)
        # Should have logged a warning about missing access logs
        warning_calls = [
            c for c in mock_print_info.call_args_list if "접속기록" in str(c)
        ]
        assert len(warning_calls) > 0


class TestEnrichWithAccessLogSummary:
    def test_empty_access_log_preserves_original(self, sample_download_df):
        access_df = pd.DataFrame(
            columns=[
                cfg.COL_EMPLOYEE_ID,
                cfg.COL_ACCESS_TIME,
                cfg.COL_PROGRAM_NAME,
                cfg.COL_JOB_PERFORMANCE,
            ]
        )
        result = drc._enrich_with_access_log_summary(
            sample_download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        assert len(result) == len(sample_download_df)
        assert cfg.COL_ACCESS_LOG_SUMMARY in result.columns
        assert "최근접속기록거리(분)" not in result.columns
        assert all(result[cfg.COL_ACCESS_LOG_SUMMARY] == "")

    def test_before_window_match_produces_summary_with_prefix(self, sample_download_df):
        # emp1 downloads at 10:00, access at 9:58 (2min before) -> [5분이내]
        access_df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1"],
                cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 9, 58)],
                cfg.COL_PROGRAM_NAME: ["인사조회"],
                cfg.COL_JOB_PERFORMANCE: ["조회"],
            }
        )
        result = drc._enrich_with_access_log_summary(
            sample_download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        summary = result.loc[
            result[cfg.COL_EMPLOYEE_ID] == "emp1", cfg.COL_ACCESS_LOG_SUMMARY
        ].iloc[0]
        assert summary == "[5분이내] 인사조회"

    def test_after_download_time_no_match(self, sample_download_df):
        # emp1 downloads at 10:00, access at 10:02 (after) -> no match
        access_df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1"],
                cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 2)],
                cfg.COL_PROGRAM_NAME: ["인사조회"],
                cfg.COL_JOB_PERFORMANCE: ["조회"],
            }
        )
        result = drc._enrich_with_access_log_summary(
            sample_download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        summary = result.loc[
            result[cfg.COL_EMPLOYEE_ID] == "emp1", cfg.COL_ACCESS_LOG_SUMMARY
        ].iloc[0]
        assert summary == ""

    def test_expands_to_10min_window(self, sample_download_df):
        # emp1 downloads at 10:00, access at 9:52 (8min before)
        # Not in 5min, but in 10min -> [10분이내]
        access_df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1"],
                cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 9, 52)],
                cfg.COL_PROGRAM_NAME: ["인사조회"],
                cfg.COL_JOB_PERFORMANCE: ["조회"],
            }
        )
        result = drc._enrich_with_access_log_summary(
            sample_download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        summary = result.loc[
            result[cfg.COL_EMPLOYEE_ID] == "emp1", cfg.COL_ACCESS_LOG_SUMMARY
        ].iloc[0]
        assert summary == "[10분이내] 인사조회"

    def test_expands_to_15min_window(self, sample_download_df):
        # emp1 downloads at 10:00, access at 9:48 (12min before)
        # Not in 5 or 10min, but in 15min -> [15분이내]
        access_df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1"],
                cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 9, 48)],
                cfg.COL_PROGRAM_NAME: ["인사조회"],
                cfg.COL_JOB_PERFORMANCE: ["조회"],
            }
        )
        result = drc._enrich_with_access_log_summary(
            sample_download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        summary = result.loc[
            result[cfg.COL_EMPLOYEE_ID] == "emp1", cfg.COL_ACCESS_LOG_SUMMARY
        ].iloc[0]
        assert summary == "[15분이내] 인사조회"

    def test_beyond_15min_no_match(self, sample_download_df):
        # emp1 downloads at 10:00, access at 9:44 (16min before) -> no match
        access_df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1"],
                cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 9, 44)],
                cfg.COL_PROGRAM_NAME: ["인사조회"],
                cfg.COL_JOB_PERFORMANCE: ["조회"],
            }
        )
        result = drc._enrich_with_access_log_summary(
            sample_download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        summary = result.loc[
            result[cfg.COL_EMPLOYEE_ID] == "emp1", cfg.COL_ACCESS_LOG_SUMMARY
        ].iloc[0]
        assert summary == ""

    def test_different_employee_no_match(self, sample_download_df):
        access_df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp999"],
                cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 2)],
                cfg.COL_PROGRAM_NAME: ["인사조회"],
                cfg.COL_JOB_PERFORMANCE: ["조회"],
            }
        )
        result = drc._enrich_with_access_log_summary(
            sample_download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        assert all(result[cfg.COL_ACCESS_LOG_SUMMARY] == "")

    def test_duplicate_program_shows_xN(self, sample_download_df):
        # emp1 downloads at 10:00, accesses at 9:57, 9:58, 9:59 (before)
        access_df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1", "emp1", "emp1"],
                cfg.COL_ACCESS_TIME: [
                    datetime(2023, 9, 1, 9, 57),
                    datetime(2023, 9, 1, 9, 58),
                    datetime(2023, 9, 1, 9, 59),
                ],
                cfg.COL_PROGRAM_NAME: ["인사조회", "인사조회", "급여조회"],
                cfg.COL_JOB_PERFORMANCE: ["조회", "조회", "조회"],
            }
        )
        result = drc._enrich_with_access_log_summary(
            sample_download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        summary = result.loc[
            result[cfg.COL_EMPLOYEE_ID] == "emp1", cfg.COL_ACCESS_LOG_SUMMARY
        ].iloc[0]
        assert "[5분이내]" in summary
        assert "인사조회 x2" in summary
        assert "급여조회" in summary

    def test_no_detail_column_still_works(self):
        download_df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1"],
                cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 0)],
                cfg.COL_DOWNLOAD_REASON: ["연구"],
                cfg.COL_DOWNLOAD_COUNT: [10],
            }
        )
        # Access at 9:58 (before download)
        access_df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1"],
                cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 9, 58)],
                cfg.COL_PROGRAM_NAME: ["인사조회"],
                cfg.COL_JOB_PERFORMANCE: ["조회"],
            }
        )
        result = drc._enrich_with_access_log_summary(
            download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        summary = result[cfg.COL_ACCESS_LOG_SUMMARY].iloc[0]
        assert summary == "[5분이내] 인사조회"

    def test_dtype_mismatch_int_vs_str(self):
        download_df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: [12345],
                cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 0)],
                cfg.COL_DOWNLOAD_REASON: ["연구"],
                cfg.COL_DOWNLOAD_COUNT: [10],
            }
        )
        access_df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["12345"],
                cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 9, 58)],
                cfg.COL_PROGRAM_NAME: ["인사조회"],
                cfg.COL_JOB_PERFORMANCE: ["조회"],
            }
        )
        result = drc._enrich_with_access_log_summary(
            download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        summary = result[cfg.COL_ACCESS_LOG_SUMMARY].iloc[0]
        assert summary == "[5분이내] 인사조회"

    def test_dtype_mismatch_float_vs_str(self):
        download_df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: [12345.0],
                cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 0)],
                cfg.COL_DOWNLOAD_REASON: ["연구"],
                cfg.COL_DOWNLOAD_COUNT: [10],
            }
        )
        access_df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["12345"],
                cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 9, 58)],
                cfg.COL_PROGRAM_NAME: ["인사조회"],
                cfg.COL_JOB_PERFORMANCE: ["조회"],
            }
        )
        result = drc._enrich_with_access_log_summary(
            download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        summary = result[cfg.COL_ACCESS_LOG_SUMMARY].iloc[0]
        assert summary == "[5분이내] 인사조회"

    def test_missing_required_columns_graceful(self):
        download_df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1"],
                cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 0)],
                cfg.COL_DOWNLOAD_REASON: ["연구"],
                cfg.COL_DOWNLOAD_COUNT: [10],
            }
        )
        access_df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1"],
                cfg.COL_ACCESS_TIME: [datetime(2023, 9, 1, 10, 2)],
            }
        )
        result = drc._enrich_with_access_log_summary(
            download_df, access_df, cfg.CROSS_REF_TIME_WINDOW_MINUTES
        )
        assert len(result) == len(download_df)
        assert cfg.COL_ACCESS_LOG_SUMMARY in result.columns
        assert all(result[cfg.COL_ACCESS_LOG_SUMMARY] == "")


class TestLoadAccessLogs:
    def test_returns_none_when_no_files(self, temp_dir, mocker):
        mocker.patch(
            "src.checkers.download_reason_checker.load_access_logs_cached",
            return_value=None,
        )
        result = drc._load_access_logs(temp_dir)
        assert result is None

    def test_returns_none_on_environment_error(self, temp_dir, mocker):
        mocker.patch(
            "src.checkers.download_reason_checker.load_access_logs_cached",
            return_value=None,
        )
        result = drc._load_access_logs(temp_dir)
        assert result is None

    def test_returns_none_when_cache_returns_none(self, temp_dir, mocker):
        mocker.patch(
            "src.checkers.download_reason_checker.load_access_logs_cached",
            return_value=None,
        )
        result = drc._load_access_logs(temp_dir)
        assert result is None

    def test_happy_path_returns_deduplicated_df(self, temp_dir, mocker):
        raw_df = pd.DataFrame(
            {
                cfg.COL_EMPLOYEE_ID: ["emp1", "emp1"],
                cfg.COL_ACCESS_TIME: [
                    datetime(2023, 9, 1, 10, 0),
                    datetime(2023, 9, 1, 10, 0),
                ],
                cfg.COL_PROGRAM_NAME: ["인사조회", "인사조회"],
                cfg.COL_JOB_PERFORMANCE: ["조회", "조회"],
            }
        )
        mocker.patch(
            "src.checkers.download_reason_checker.load_access_logs_cached",
            return_value=raw_df,
        )
        result = drc._load_access_logs(temp_dir)
        assert result is not None
        assert len(result) == 1

    def test_searches_with_current_month_date(self, temp_dir, mocker):
        mock_load = mocker.patch(
            "src.checkers.download_reason_checker.load_access_logs_cached",
            return_value=None,
        )
        drc._load_access_logs(temp_dir)
        called_prefix = mock_load.call_args[0][1]
        assert called_prefix.startswith(cfg.PERSONAL_INFO_ACCESS_LOG_PREFIX)
        assert len(called_prefix) == len(cfg.PERSONAL_INFO_ACCESS_LOG_PREFIX) + 6


class TestRunCheckErrorIsolation:
    def test_enrichment_error_does_not_crash_checks(
        self, temp_dir, sample_download_df, mocker
    ):
        mocker.patch("src.checkers.download_reason_checker.print_checker_header")
        mock_info = mocker.patch("src.checkers.download_reason_checker.print_info")
        mocker.patch(
            "src.checkers.download_reason_checker.load_merged_excel",
            return_value=sample_download_df,
        )
        mocker.patch(
            "src.checkers.download_reason_checker._load_access_logs",
            return_value=pd.DataFrame({"dummy": [1]}),
        )
        mocker.patch(
            "src.checkers.download_reason_checker._enrich_with_access_log_summary",
            side_effect=KeyError("missing column"),
        )
        mock_run_pipeline = mocker.patch(
            "src.checkers.download_reason_checker.run_pipeline"
        )
        mocker.patch("src.checkers.download_reason_checker.save_excel_with_autofit")

        result = drc.run_check("download_dir", temp_dir, "202309")

        assert result == len(sample_download_df)
        assert mock_run_pipeline.call_count == 1
        assert any("오류 발생" in str(c) for c in mock_info.call_args_list)
