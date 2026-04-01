"""Tests for collect_check_results in report_generator."""

from __future__ import annotations

from pathlib import Path

import openpyxl

from src import config as cfg
from src.report_generator import CheckResults, collect_check_results

PREV_MONTH = "202603"


def _make_filename(base: str, suffix: str, prev_month: str) -> str:
    """Build the expected output filename."""
    return f"{base}({suffix})_{prev_month}.xlsx"


def _create_xlsx_with_data(path: Path) -> None:
    """Create an .xlsx file with a header row and one data row."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Header1", "Header2"])
    ws.append(["data1", "data2"])
    wb.save(path)
    wb.close()


def _create_xlsx_header_only(path: Path) -> None:
    """Create an .xlsx file with only a header row (no data)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Header1", "Header2"])
    wb.save(path)
    wb.close()


class TestCollectCheckResults:
    """Tests for collect_check_results."""

    def test_empty_dir_returns_all_false(self, tmp_path: Path) -> None:
        result = collect_check_results(str(tmp_path), PREV_MONTH)
        assert result == CheckResults()

    def test_off_hours_file_with_data(self, tmp_path: Path) -> None:
        fname = _make_filename(
            cfg.LOGIN_CHECK_REPORT_BASE,
            cfg.LOGIN_REPORT_OFF_HOURS_SUFFIX,
            PREV_MONTH,
        )
        _create_xlsx_with_data(tmp_path / fname)
        result = collect_check_results(str(tmp_path), PREV_MONTH)
        assert result.off_hours is True
        assert result.holiday is False

    def test_holiday_file_with_data(self, tmp_path: Path) -> None:
        fname = _make_filename(
            cfg.LOGIN_CHECK_REPORT_BASE,
            cfg.LOGIN_REPORT_HOLIDAY_SUFFIX,
            PREV_MONTH,
        )
        _create_xlsx_with_data(tmp_path / fname)
        result = collect_check_results(str(tmp_path), PREV_MONTH)
        assert result.holiday is True

    def test_ip_switch_file_with_data(self, tmp_path: Path) -> None:
        fname = _make_filename(
            cfg.LOGIN_CHECK_REPORT_BASE,
            cfg.LOGIN_REPORT_IP_SWITCH_SUFFIX,
            PREV_MONTH,
        )
        _create_xlsx_with_data(tmp_path / fname)
        result = collect_check_results(str(tmp_path), PREV_MONTH)
        assert result.ip_switch is True

    def test_high_volume_views_file_with_data(self, tmp_path: Path) -> None:
        fname = _make_filename(
            cfg.PERSONAL_INFO_REPORT_BASE,
            cfg.PERSONAL_INFO_ACCESS_HIGH_VOLUME_VIEWS_SUFFIX,
            PREV_MONTH,
        )
        _create_xlsx_with_data(tmp_path / fname)
        result = collect_check_results(str(tmp_path), PREV_MONTH)
        assert result.high_volume_views is True

    def test_high_volume_saves_file_with_data(self, tmp_path: Path) -> None:
        fname = _make_filename(
            cfg.PERSONAL_INFO_REPORT_BASE,
            cfg.PERSONAL_INFO_ACCESS_HIGH_VOLUME_SAVES_SUFFIX,
            PREV_MONTH,
        )
        _create_xlsx_with_data(tmp_path / fname)
        result = collect_check_results(str(tmp_path), PREV_MONTH)
        assert result.high_volume_saves is True

    def test_high_download_count_file_with_data(self, tmp_path: Path) -> None:
        fname = _make_filename(
            cfg.DOWNLOAD_REASON_REPORT_BASE,
            cfg.DOWNLOAD_REASON_HIGH_DOWNLOAD_COUNT_SUFFIX,
            PREV_MONTH,
        )
        _create_xlsx_with_data(tmp_path / fname)
        result = collect_check_results(str(tmp_path), PREV_MONTH)
        assert result.high_download_count is True

    def test_high_download_freq_file_with_data(self, tmp_path: Path) -> None:
        fname = _make_filename(
            cfg.DOWNLOAD_REASON_REPORT_BASE,
            cfg.DOWNLOAD_REASON_HIGH_FREQUENCY_SUFFIX,
            PREV_MONTH,
        )
        _create_xlsx_with_data(tmp_path / fname)
        result = collect_check_results(str(tmp_path), PREV_MONTH)
        assert result.high_download_freq is True

    def test_download_off_hours_file_with_data(self, tmp_path: Path) -> None:
        fname = _make_filename(
            cfg.DOWNLOAD_REASON_REPORT_BASE,
            cfg.DOWNLOAD_REASON_OFF_HOURS_SUFFIX,
            PREV_MONTH,
        )
        _create_xlsx_with_data(tmp_path / fname)
        result = collect_check_results(str(tmp_path), PREV_MONTH)
        assert result.download_off_hours is True

    def test_invalid_reason_file_with_data(self, tmp_path: Path) -> None:
        fname = _make_filename(
            cfg.DOWNLOAD_REASON_REPORT_BASE,
            cfg.DOWNLOAD_REASON_INVALID_REASON_SUFFIX,
            PREV_MONTH,
        )
        _create_xlsx_with_data(tmp_path / fname)
        result = collect_check_results(str(tmp_path), PREV_MONTH)
        assert result.invalid_reason is True

    def test_header_only_file_stays_false(self, tmp_path: Path) -> None:
        fname = _make_filename(
            cfg.LOGIN_CHECK_REPORT_BASE,
            cfg.LOGIN_REPORT_OFF_HOURS_SUFFIX,
            PREV_MONTH,
        )
        _create_xlsx_header_only(tmp_path / fname)
        result = collect_check_results(str(tmp_path), PREV_MONTH)
        assert result.off_hours is False
