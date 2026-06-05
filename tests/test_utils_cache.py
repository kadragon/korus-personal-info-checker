"""Tests for load_access_logs_cached and clear_access_log_cache in utils."""

import pandas as pd

from src import utils


class TestLoadAccessLogsCached:
    def test_cache_hit_returns_same_data(self, temp_dir, mocker):
        """Second call with same args returns cached data without re-reading disk."""
        df = pd.DataFrame({"교직원ID": ["emp1"], "접속일시": ["2024-01-01"]})
        mock_find = mocker.patch("src.utils._find_excel_files", return_value=["a.xlsx"])
        mocker.patch("src.utils._merge_and_preprocess_files", return_value=df)

        utils.load_access_logs_cached(temp_dir, "prefix_202501")
        utils.load_access_logs_cached(temp_dir, "prefix_202501")

        assert mock_find.call_count == 1

    def test_cache_miss_returns_merged_df(self, temp_dir, mocker):
        """First call loads from disk and returns the DataFrame."""
        df = pd.DataFrame({"교직원ID": ["emp1"]})
        mocker.patch("src.utils._find_excel_files", return_value=["a.xlsx"])
        mocker.patch("src.utils._merge_and_preprocess_files", return_value=df)

        result = utils.load_access_logs_cached(temp_dir, "prefix_202501")

        assert result is not None
        assert list(result["교직원ID"]) == ["emp1"]

    def test_no_files_returns_none_and_not_cached(self, temp_dir, mocker):
        """When no files found, returns None and does not populate the cache."""
        mock_find = mocker.patch("src.utils._find_excel_files", return_value=[])

        result = utils.load_access_logs_cached(temp_dir, "prefix_202501")
        utils.load_access_logs_cached(temp_dir, "prefix_202501")

        assert result is None
        assert mock_find.call_count == 2

    def test_returned_df_is_copy_not_reference(self, temp_dir, mocker):
        """Mutating the returned DataFrame does not corrupt the cache."""
        df = pd.DataFrame({"val": [1, 2, 3]})
        mocker.patch("src.utils._find_excel_files", return_value=["a.xlsx"])
        mocker.patch("src.utils._merge_and_preprocess_files", return_value=df)

        result1 = utils.load_access_logs_cached(temp_dir, "prefix_202501")
        result1["val"] = 99

        result2 = utils.load_access_logs_cached(temp_dir, "prefix_202501")

        assert list(result2["val"]) == [1, 2, 3]

    def test_different_prefixes_cached_independently(self, temp_dir, mocker):
        """Different prefixes are cached under separate keys."""
        df_a = pd.DataFrame({"교직원ID": ["empA"]})
        df_b = pd.DataFrame({"교직원ID": ["empB"]})
        mock_find = mocker.patch(
            "src.utils._find_excel_files", side_effect=[["a.xlsx"], ["b.xlsx"]]
        )
        mocker.patch("src.utils._merge_and_preprocess_files", side_effect=[df_a, df_b])

        result_a = utils.load_access_logs_cached(temp_dir, "prefixA_202501")
        result_b = utils.load_access_logs_cached(temp_dir, "prefixB_202501")

        assert list(result_a["교직원ID"]) == ["empA"]
        assert list(result_b["교직원ID"]) == ["empB"]
        assert mock_find.call_count == 2

    def test_environment_error_returns_none(self, mocker):
        """EnvironmentError from _find_excel_files is caught -> returns None.

        Matches load_merged_excel: a missing/unreadable dir is a skippable
        condition, not a crash (the orchestrator continues with other checkers).
        """
        mocker.patch(
            "src.utils._find_excel_files",
            side_effect=EnvironmentError("bad dir"),
        )
        assert utils.load_access_logs_cached("/bad/path", "prefix_202501") is None


class TestClearAccessLogCache:
    def test_clear_causes_next_call_to_reload(self, temp_dir, mocker):
        """After clear, the next call re-reads from disk."""
        df = pd.DataFrame({"교직원ID": ["emp1"]})
        mock_find = mocker.patch("src.utils._find_excel_files", return_value=["a.xlsx"])
        mocker.patch("src.utils._merge_and_preprocess_files", return_value=df)

        utils.load_access_logs_cached(temp_dir, "prefix_202501")
        utils.clear_access_log_cache()
        utils.load_access_logs_cached(temp_dir, "prefix_202501")

        assert mock_find.call_count == 2
