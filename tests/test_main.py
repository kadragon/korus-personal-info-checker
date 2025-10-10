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
