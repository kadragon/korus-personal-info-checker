"""
Generates HWPX inspection report from checker results.

Reads the HWPX template, fills in inspection date, log count,
and dynamically sets checkboxes based on checker output files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import openpyxl

from . import config as cfg


@dataclass
class CheckResults:
    """Boolean flags indicating whether each check category detected issues."""

    off_hours: bool = False
    holiday: bool = False
    ip_switch: bool = False
    high_volume_views: bool = False
    high_volume_saves: bool = False
    high_download_count: bool = False
    high_download_freq: bool = False
    download_off_hours: bool = False
    invalid_reason: bool = False


# Maps CheckResults field names to (report_base, suffix) for file detection.
_RESULT_FILE_MAP: dict[str, tuple[str, str]] = {
    "off_hours": (cfg.LOGIN_CHECK_REPORT_BASE, cfg.LOGIN_REPORT_OFF_HOURS_SUFFIX),
    "holiday": (cfg.LOGIN_CHECK_REPORT_BASE, cfg.LOGIN_REPORT_HOLIDAY_SUFFIX),
    "ip_switch": (cfg.LOGIN_CHECK_REPORT_BASE, cfg.LOGIN_REPORT_IP_SWITCH_SUFFIX),
    "high_volume_views": (
        cfg.PERSONAL_INFO_REPORT_BASE,
        cfg.PERSONAL_INFO_ACCESS_HIGH_VOLUME_VIEWS_SUFFIX,
    ),
    "high_volume_saves": (
        cfg.PERSONAL_INFO_REPORT_BASE,
        cfg.PERSONAL_INFO_ACCESS_HIGH_VOLUME_SAVES_SUFFIX,
    ),
    "high_download_count": (
        cfg.DOWNLOAD_REASON_REPORT_BASE,
        cfg.DOWNLOAD_REASON_HIGH_DOWNLOAD_COUNT_SUFFIX,
    ),
    "high_download_freq": (
        cfg.DOWNLOAD_REASON_REPORT_BASE,
        cfg.DOWNLOAD_REASON_HIGH_FREQUENCY_SUFFIX,
    ),
    "download_off_hours": (
        cfg.DOWNLOAD_REASON_REPORT_BASE,
        cfg.DOWNLOAD_REASON_OFF_HOURS_SUFFIX,
    ),
    "invalid_reason": (
        cfg.DOWNLOAD_REASON_REPORT_BASE,
        cfg.DOWNLOAD_REASON_INVALID_REASON_SUFFIX,
    ),
}


def collect_check_results(save_dir: str, prev_month: str) -> CheckResults:
    """Scan *save_dir* for checker output files and return detection flags.

    For each field in ``_RESULT_FILE_MAP`` the expected filename is
    ``{base}({suffix})_{prev_month}.xlsx``.  A flag is set to ``True``
    only when the file exists **and** contains at least one data row
    beyond the header.

    Args:
        save_dir: Directory that contains checker output Excel files.
        prev_month: Year-month string such as ``"202603"``.

    Returns:
        A ``CheckResults`` instance with boolean flags.
    """
    flags: dict[str, bool] = {}

    for field_name, (base, suffix) in _RESULT_FILE_MAP.items():
        filename = f"{base}({suffix})_{prev_month}.xlsx"
        filepath = os.path.join(save_dir, filename)

        if not os.path.isfile(filepath):
            flags[field_name] = False
            continue

        wb = openpyxl.load_workbook(filepath, read_only=True)
        try:
            ws = wb.active
            row_count = 0
            for _ in ws.iter_rows(min_row=1, max_row=2):  # type: ignore[union-attr]
                row_count += 1
            flags[field_name] = row_count > 1
        finally:
            wb.close()

    return CheckResults(**flags)
