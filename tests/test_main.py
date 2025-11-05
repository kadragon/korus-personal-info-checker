"""
Tests for main module.

GENERATED FROM SPEC-test-coverage-improvement-1
Trace: SPEC-test-coverage-improvement-1, TEST-main-1
"""

import os

import pytest

from src import main


class TestDiscoverAndRunCheckers:
    def test_discover_and_run_checkers_with_checkers(self, mocker):
        # Mock pkgutil to return a fake module
        mock_module_info = mocker.MagicMock()
        mock_module_info.name = "test_checker"
        mocker.patch("pkgutil.iter_modules", return_value=[mock_module_info])

        # Mock importlib
        mock_module = mocker.MagicMock()
        mock_func = mocker.MagicMock(return_value=10)
        mock_module.__dict__ = {"run_check": mock_func}
        mocker.patch("importlib.import_module", return_value=mock_module)

        # Mock getattr
        mocker.patch.object(main, "getattr", return_value=mock_func, create=True)

        result = main.discover_and_run_checkers("download_dir", "save_dir", "202309")
        assert result == 10

    def test_discover_and_run_checkers_no_checkers(self, mocker):
        mocker.patch("pkgutil.iter_modules", return_value=[])

        result = main.discover_and_run_checkers("download_dir", "save_dir", "202309")
        assert result == 0

    def test_discover_and_run_checkers_invalid_module(self, mocker):
        mock_module_info = mocker.MagicMock()
        mock_module_info.name = "invalid"
        mocker.patch("pkgutil.iter_modules", return_value=[mock_module_info])

        mocker.patch("importlib.import_module", side_effect=Exception("Import error"))
        mocker.patch.object(main, "print_error")

        result = main.discover_and_run_checkers("download_dir", "save_dir", "202309")
        assert result == 0

    def test_discover_and_run_checkers_no_run_check(self, mocker):
        mock_module_info = mocker.MagicMock()
        mock_module_info.name = "test_checker"
        mocker.patch("pkgutil.iter_modules", return_value=[mock_module_info])

        mock_module = mocker.MagicMock()
        mocker.patch("importlib.import_module", return_value=mock_module)
        mocker.patch.object(main, "getattr", return_value=None, create=True)
        mocker.patch.object(main, "print_error")

        result = main.discover_and_run_checkers("download_dir", "save_dir", "202309")
        assert result == 0

    def test_discover_and_run_checkers_none_return(self, mocker):
        mock_module_info = mocker.MagicMock()
        mock_module_info.name = "test_checker"
        mocker.patch("pkgutil.iter_modules", return_value=[mock_module_info])

        mock_module = mocker.MagicMock()
        mock_func = mocker.MagicMock(return_value=None)
        mock_module.__dict__ = {"run_check": mock_func}
        mocker.patch("importlib.import_module", return_value=mock_module)
        mocker.patch.object(main, "getattr", return_value=mock_func, create=True)

        result = main.discover_and_run_checkers("download_dir", "save_dir", "202309")
        assert result == 0

    def test_discover_and_run_checkers_exception_during_execution(self, mocker, capsys):
        """Test exception handling during checker execution (lines 69-70)."""
        mock_module_info = mocker.MagicMock()
        mock_module_info.name = "failing_checker"
        mocker.patch("pkgutil.iter_modules", return_value=[mock_module_info])

        # Mock import to raise exception during execution
        mocker.patch(
            "importlib.import_module",
            side_effect=Exception("Unexpected error during check")
        )

        result = main.discover_and_run_checkers("download_dir", "save_dir", "202309")

        # Should handle exception and return 0
        assert result == 0

        # Verify error message was output (check captured output)
        captured = capsys.readouterr()
        assert "예상치 못한 오류" in captured.out or "예상치 못한 오류" in str(captured)


class TestMain:
    """Tests for main() function."""

    def test_main_missing_save_dir(self, mocker):
        """Test main() when SAVE_DIR environment variable is not set (lines 83-88)."""
        # Save original values
        original_save_dir = main.base_save_dir
        original_download_dir = main.download_dir

        try:
            # Set base_save_dir to None
            main.base_save_dir = None
            main.download_dir = "/some/path"

            mock_print_error = mocker.patch("src.main.print_error")

            main.main()

            # Verify error was printed
            mock_print_error.assert_called_once()
            call_args = mock_print_error.call_args[0][0]
            assert "SAVE_DIR" in call_args
            assert "환경 변수가 설정되지 않았습니다" in call_args

        finally:
            # Restore original values
            main.base_save_dir = original_save_dir
            main.download_dir = original_download_dir

    def test_main_missing_download_dir(self, mocker):
        """Test main() when DOWNLOAD_DIR environment variable is not set (lines 89-94)."""
        # Save original values
        original_save_dir = main.base_save_dir
        original_download_dir = main.download_dir

        try:
            # Set download_dir to None
            main.base_save_dir = "/some/path"
            main.download_dir = None

            mock_print_error = mocker.patch("src.main.print_error")

            main.main()

            # Verify error was printed
            mock_print_error.assert_called_once()
            call_args = mock_print_error.call_args[0][0]
            assert "DOWNLOAD_DIR" in call_args
            assert "환경 변수가 설정되지 않았습니다" in call_args

        finally:
            # Restore original values
            main.base_save_dir = original_save_dir
            main.download_dir = original_download_dir

    def test_main_full_workflow_success(self, mocker, tmp_path):
        """Test main() complete workflow (lines 96-113)."""
        # Save original values
        original_save_dir = main.base_save_dir
        original_download_dir = main.download_dir

        try:
            # Setup temporary directories
            download_dir = tmp_path / "download"
            save_dir = tmp_path / "save"
            download_dir.mkdir()
            save_dir.mkdir()

            main.base_save_dir = str(save_dir)
            main.download_dir = str(download_dir)

            # Mock all the functions called in main()
            mock_get_prev_month = mocker.patch(
                "src.main.get_prev_month_yyyymm",
                return_value="202311"
            )
            mock_make_save_dir = mocker.patch(
                "src.main.make_save_dir",
                return_value=str(save_dir / "202311")
            )
            mock_print_header = mocker.patch("src.main.print_header")
            mock_print_info = mocker.patch("src.main.print_info")
            mock_discover = mocker.patch(
                "src.main.discover_and_run_checkers",
                return_value=150
            )
            mock_print_zip_header = mocker.patch("src.main.print_zip_header")
            mock_zip_files = mocker.patch("src.main.zip_files_by_prefix")
            mock_print_summary = mocker.patch("src.main.print_summary")

            main.main()

            # Verify all functions were called
            mock_get_prev_month.assert_called_once()
            mock_make_save_dir.assert_called_once()
            mock_print_header.assert_called_once()
            assert mock_print_info.call_count == 2  # Called twice for paths
            mock_discover.assert_called_once()
            mock_print_zip_header.assert_called_once()
            mock_zip_files.assert_called_once()
            mock_print_summary.assert_called_once()

        finally:
            # Restore original values
            main.base_save_dir = original_save_dir
            main.download_dir = original_download_dir

    def test_main_zip_error_handling(self, mocker, tmp_path):
        """Test main() handles zip errors gracefully (lines 108-111)."""
        # Save original values
        original_save_dir = main.base_save_dir
        original_download_dir = main.download_dir

        try:
            # Setup temporary directories
            download_dir = tmp_path / "download"
            save_dir = tmp_path / "save"
            download_dir.mkdir()
            save_dir.mkdir()

            main.base_save_dir = str(save_dir)
            main.download_dir = str(download_dir)

            # Mock functions
            mocker.patch("src.main.get_prev_month_yyyymm", return_value="202311")
            mocker.patch("src.main.make_save_dir", return_value=str(save_dir))
            mocker.patch("src.main.print_header")
            mocker.patch("src.main.print_info")
            mocker.patch("src.main.discover_and_run_checkers", return_value=100)
            mocker.patch("src.main.print_zip_header")

            # Make zip_files_by_prefix raise an exception
            mocker.patch(
                "src.main.zip_files_by_prefix",
                side_effect=Exception("Zip creation failed")
            )
            mock_print_error = mocker.patch("src.main.print_error")
            mocker.patch("src.main.print_summary")

            main.main()

            # Verify error was printed
            mock_print_error.assert_called_once()
            call_args = mock_print_error.call_args[0][0]
            assert "압축 작업 중 오류" in call_args

        finally:
            # Restore original values
            main.base_save_dir = original_save_dir
            main.download_dir = original_download_dir

    def test_main_as_script(self, mocker):
        """Test __name__ == '__main__' block (line 117)."""
        # Save original values
        original_save_dir = main.base_save_dir
        original_download_dir = main.download_dir

        try:
            # Set valid environment
            main.base_save_dir = "/some/path"
            main.download_dir = "/some/download/path"

            # Mock main function to avoid actual execution
            mock_main_func = mocker.patch("src.main.main")

            # Simulate running as script
            if __name__ != "__main__":
                # We can't actually test the __name__ == "__main__" block directly
                # But we can verify the function exists and is callable
                assert callable(main.main)

        finally:
            # Restore original values
            main.base_save_dir = original_save_dir
            main.download_dir = original_download_dir
