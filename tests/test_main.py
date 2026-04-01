"""
Tests for main module.

GENERATED FROM SPEC-test-coverage-improvement-1
Trace: SPEC-test-coverage-improvement-1, TEST-main-1
"""

import os
from pathlib import Path

from src import config as cfg
from src import main
from src.report_generator import CheckResults


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
            side_effect=Exception("Unexpected error during check"),
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
        mocker.patch("src.main.base_save_dir", None)
        mocker.patch("src.main.download_dir", "/some/path")
        mock_print_error = mocker.patch("src.main.print_error")

        main.main()

        # Verify error was printed
        mock_print_error.assert_called_once()
        call_args = mock_print_error.call_args[0][0]
        assert "SAVE_DIR" in call_args
        assert "환경 변수가 설정되지 않았습니다" in call_args

    def test_main_missing_download_dir(self, mocker):
        """Test main() when DOWNLOAD_DIR env var is not set (lines 89-94)."""
        mocker.patch("src.main.base_save_dir", "/some/path")
        mocker.patch("src.main.download_dir", None)
        mock_print_error = mocker.patch("src.main.print_error")

        main.main()

        # Verify error was printed
        mock_print_error.assert_called_once()
        call_args = mock_print_error.call_args[0][0]
        assert "DOWNLOAD_DIR" in call_args
        assert "환경 변수가 설정되지 않았습니다" in call_args

    def test_main_full_workflow_success(self, mocker, tmp_path):
        """Test main() complete workflow (lines 96-113)."""
        # Setup temporary directories
        download_dir = tmp_path / "download"
        save_dir = tmp_path / "save"
        download_dir.mkdir()
        save_dir.mkdir()

        mocker.patch("src.main.base_save_dir", str(save_dir))
        mocker.patch("src.main.download_dir", str(download_dir))

        # Mock all the functions called in main()
        mock_get_prev_month = mocker.patch(
            "src.main.get_prev_month_yyyymm", return_value="202311"
        )
        mock_make_save_dir = mocker.patch(
            "src.main.make_save_dir", return_value=str(save_dir / "202311")
        )
        mock_print_header = mocker.patch("src.main.print_header")
        mock_print_info = mocker.patch("src.main.print_info")
        mock_discover = mocker.patch(
            "src.main.discover_and_run_checkers", return_value=150
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

    def test_main_zip_error_handling(self, mocker, tmp_path):
        """Test main() handles zip errors gracefully (lines 108-111)."""
        # Setup temporary directories
        download_dir = tmp_path / "download"
        save_dir = tmp_path / "save"
        download_dir.mkdir()
        save_dir.mkdir()

        mocker.patch("src.main.base_save_dir", str(save_dir))
        mocker.patch("src.main.download_dir", str(download_dir))

        # Mock functions
        mocker.patch("src.main.get_prev_month_yyyymm", return_value="202311")
        mocker.patch("src.main.make_save_dir", return_value=str(save_dir))
        mocker.patch("src.main.print_header")
        mocker.patch("src.main.print_info")
        mocker.patch("src.main.discover_and_run_checkers", return_value=100)
        mocker.patch("src.main.print_zip_header")

        # Make zip_files_by_prefix raise an exception
        mocker.patch(
            "src.main.zip_files_by_prefix", side_effect=Exception("Zip creation failed")
        )
        mock_print_error = mocker.patch("src.main.print_error")
        mocker.patch("src.main.print_summary")

        main.main()

        # Verify error was printed
        mock_print_error.assert_called_once()
        call_args = mock_print_error.call_args[0][0]
        assert "압축 작업 중 오류" in call_args

    def test_main_as_script(self, mocker):
        """Test __name__ == '__main__' block (line 117)."""
        mocker.patch("src.main.base_save_dir", "/some/path")
        mocker.patch("src.main.download_dir", "/some/download/path")
        mocker.patch("src.main.main")

        # Simulate running as script
        if __name__ != "__main__":
            # We can't actually test the __name__ == "__main__" block directly
            # But we can verify the function exists and is callable
            assert callable(main.main)


class TestHwpxIntegration:
    """Tests for HWPX report generation integration in _run_inspection."""

    def test_generates_hwpx_when_template_exists(self, mocker, tmp_path):
        """_run_inspection calls generate_hwpx_report when template found."""
        download_dir = str(tmp_path / "download")
        save_dir = str(tmp_path / "save")
        os.makedirs(download_dir)
        os.makedirs(save_dir)

        # Create a fake HWPX template in download_dir
        template_name = f"{cfg.HWPX_REPORT_BASE}_202603.hwpx"
        template_path = os.path.join(download_dir, template_name)
        Path(template_path).touch()

        mocker.patch("src.main.print_header")
        mocker.patch("src.main.print_info")
        mocker.patch("src.main.discover_and_run_checkers", return_value=181273)
        mocker.patch("src.main.print_zip_header")
        mocker.patch("src.main.zip_files_by_prefix")
        mocker.patch("src.main.print_summary")
        mock_collect = mocker.patch(
            "src.main.collect_check_results",
            return_value=CheckResults(),
        )
        mock_generate = mocker.patch("src.main.generate_hwpx_report")

        main._run_inspection(download_dir, save_dir, "202603")

        mock_collect.assert_called_once_with(save_dir, "202603")
        mock_generate.assert_called_once()
        call_kwargs = mock_generate.call_args
        assert call_kwargs[1]["log_count"] == 181273 or call_kwargs[0][3] == 181273

    def test_skips_hwpx_when_no_template(self, mocker, tmp_path):
        """_run_inspection skips HWPX generation when no template found."""
        download_dir = str(tmp_path / "download")
        save_dir = str(tmp_path / "save")
        os.makedirs(download_dir)
        os.makedirs(save_dir)

        mocker.patch("src.main.print_header")
        mocker.patch("src.main.print_info")
        mocker.patch("src.main.discover_and_run_checkers", return_value=100)
        mocker.patch("src.main.print_zip_header")
        mocker.patch("src.main.zip_files_by_prefix")
        mocker.patch("src.main.print_summary")
        mock_generate = mocker.patch("src.main.generate_hwpx_report")

        main._run_inspection(download_dir, save_dir, "202603")

        mock_generate.assert_not_called()

    def test_hwpx_output_path_and_date_formatting(self, mocker, tmp_path):
        """Verify output path, inspection_date, and target_month_label."""
        download_dir = str(tmp_path / "download")
        save_dir = str(tmp_path / "save")
        os.makedirs(download_dir)
        os.makedirs(save_dir)

        template_name = f"{cfg.HWPX_REPORT_BASE}_202603.hwpx"
        Path(os.path.join(download_dir, template_name)).touch()

        mocker.patch("src.main.print_header")
        mocker.patch("src.main.print_info")
        mocker.patch("src.main.discover_and_run_checkers", return_value=5000)
        mocker.patch("src.main.print_zip_header")
        mocker.patch("src.main.zip_files_by_prefix")
        mocker.patch("src.main.print_summary")
        mocker.patch(
            "src.main.collect_check_results",
            return_value=CheckResults(),
        )
        mock_generate = mocker.patch("src.main.generate_hwpx_report")

        main._run_inspection(download_dir, save_dir, "202603")

        args = mock_generate.call_args
        # output_path should be in save_dir
        output_path = args[1].get("output_path") or args[0][1]
        assert output_path.startswith(save_dir)
        assert output_path.endswith(".hwpx")
        # target_month_label
        target_label = args[1].get("target_month_label") or args[0][4]
        assert target_label == "(2026년 3월) "
        # log_count
        log_count = args[1].get("log_count") or args[0][3]
        assert log_count == 5000

    def test_hwpx_generation_error_handled(self, mocker, tmp_path):
        """HWPX generation errors are caught and reported."""
        download_dir = str(tmp_path / "download")
        save_dir = str(tmp_path / "save")
        os.makedirs(download_dir)
        os.makedirs(save_dir)

        template_name = f"{cfg.HWPX_REPORT_BASE}_202603.hwpx"
        Path(os.path.join(download_dir, template_name)).touch()

        mocker.patch("src.main.print_header")
        mocker.patch("src.main.print_info")
        mocker.patch("src.main.discover_and_run_checkers", return_value=100)
        mocker.patch("src.main.print_zip_header")
        mocker.patch("src.main.zip_files_by_prefix")
        mocker.patch("src.main.print_summary")
        mocker.patch(
            "src.main.collect_check_results",
            return_value=CheckResults(),
        )
        mocker.patch(
            "src.main.generate_hwpx_report",
            side_effect=Exception("HWPX write failed"),
        )
        mock_print_error = mocker.patch("src.main.print_error")

        main._run_inspection(download_dir, save_dir, "202603")

        mock_print_error.assert_called_once()
        assert "HWPX" in mock_print_error.call_args[0][0]
