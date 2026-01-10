"""
Tests for launcher module.
"""

import pytest

try:
    from src import launcher

    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False
    launcher = None  # type: ignore[assignment]

pytestmark = pytest.mark.skipif(not HAS_TKINTER, reason="tkinter not available")


def test_launcher_main_runs_when_selected(mocker):
    mock_root = mocker.MagicMock()
    mocker.patch("src.launcher.Tk", return_value=mock_root)
    mocker.patch(
        "src.launcher.filedialog.askdirectory",
        return_value="C:/Downloads",
    )
    mock_run = mocker.patch("src.launcher.run_with_download_dir")

    launcher.main()

    mock_run.assert_called_once_with("C:/Downloads")
    mock_root.withdraw.assert_called_once()
    mock_root.destroy.assert_called_once()


def test_launcher_main_exits_when_canceled(mocker):
    mock_root = mocker.MagicMock()
    mocker.patch("src.launcher.Tk", return_value=mock_root)
    mocker.patch("src.launcher.filedialog.askdirectory", return_value="")
    mock_run = mocker.patch("src.launcher.run_with_download_dir")

    launcher.main()

    mock_run.assert_not_called()
    mock_root.withdraw.assert_called_once()
    mock_root.destroy.assert_called_once()
