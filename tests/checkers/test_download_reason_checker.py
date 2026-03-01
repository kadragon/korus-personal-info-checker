from datetime import datetime

import pandas as pd
import pytest

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
