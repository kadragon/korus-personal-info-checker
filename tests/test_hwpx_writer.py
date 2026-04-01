"""Tests for HWPX report generation (Phase 2: text replacement, Phase 3: checkboxes)."""

from __future__ import annotations

import re
import zipfile

import pytest

from src.hwpx_writer import generate_hwpx_report
from src.report_generator import CheckResults

# Template default values (must match _TEMPLATE_* constants in hwpx_writer.py)
_TEMPLATE_DATE = "2026. 4. 1."
_TEMPLATE_LOG_COUNT = "123,456"
_TEMPLATE_MONTH_LABEL = "(2026년 3월) "
_NORMAL_CHECKBOX = "☑정상 / □ 비정상"
_MU_CHECKBOX = "□ 유 / ☑ 무"

# The template section0.xml must contain exactly 19 정상/비정상 and 4 유/무 checkboxes.
_SECTION0_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    "<body>"
    f"<p>점검일: {_TEMPLATE_DATE}</p>"
    f"<p>건수: {_TEMPLATE_LOG_COUNT}</p>"
    f"<p>대상월: {_TEMPLATE_MONTH_LABEL}</p>"
    + "".join(f"<p>항목{i}: {_NORMAL_CHECKBOX}</p>" for i in range(19))
    + "".join(f"<p>다운{i}: {_MU_CHECKBOX}</p>" for i in range(4))
    + "</body>"
)


@pytest.fixture()
def template_path(tmp_path):
    """Create a minimal synthetic HWPX template (ZIP with Contents/section0.xml)."""
    path = tmp_path / "template.hwpx"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Contents/section0.xml", _SECTION0_XML.encode("utf-8"))
        zf.writestr("mimetype", b"application/hwpx+zip")
    return str(path)

NORMAL = "☑정상 / □ 비정상"
ABNORMAL = "□정상 / ☑ 비정상"
YU_DETECTED = "☑ 유 / □ 무"
MU_NOT_DETECTED = "□ 유 / ☑ 무"


def _read_section_xml(hwpx_path: str) -> str:
    with zipfile.ZipFile(hwpx_path, "r") as z:
        return z.read("Contents/section0.xml").decode("utf-8")


def _find_normal_abnormal(xml: str) -> list[str]:
    """Return all 정상/비정상 checkbox texts in order."""
    return re.findall(r"[☑□]정상 / [☑□] 비정상", xml)


def _find_yu_mu(xml: str) -> list[str]:
    """Return all 유/무 checkbox texts in order."""
    return re.findall(r"[☑□] 유 / [☑□] 무", xml)


def _generate(tmp_path, tpl_path, **kwargs):
    """Helper: generate with defaults, return XML string."""
    defaults = {
        "template_path": tpl_path,
        "output_path": str(tmp_path / "output.hwpx"),
        "inspection_date": "2026. 5. 1.",
        "log_count": 200000,
        "target_month_label": "(2026년 4월) ",
        "results": CheckResults(),
    }
    defaults.update(kwargs)
    generate_hwpx_report(**defaults)
    return _read_section_xml(defaults["output_path"])


# ── Phase 2: Text replacement ──────────────────────────────────────────


class TestTextReplacement:
    def test_date_replacement(self, tmp_path, template_path):
        xml = _generate(tmp_path, template_path, inspection_date="2026. 5. 1.")
        assert "2026. 5. 1." in xml
        assert "2026. 4. 1." not in xml

    def test_log_count_replacement(self, tmp_path, template_path):
        xml = _generate(tmp_path, template_path, log_count=200000)
        assert "200,000" in xml
        assert "123,456" not in xml

    def test_month_label_replacement(self, tmp_path, template_path):
        xml = _generate(tmp_path, template_path, target_month_label="(2026년 4월) ")
        assert "(2026년 4월) " in xml
        assert "(2026년 3월) " not in xml


# ── Phase 3: Checkbox - 정상/비정상 ─────────────────────────────────────


class TestNormalAbnormalCheckboxes:
    def test_all_false_all_normal(self, tmp_path, template_path):
        """When all results are False, all 19 checkboxes should be 정상."""
        xml = _generate(tmp_path, template_path, results=CheckResults())
        checkboxes = _find_normal_abnormal(xml)
        assert len(checkboxes) == 19
        for i, cb in enumerate(checkboxes):
            assert cb == NORMAL, f"Occurrence {i} should be normal"

    def test_off_hours_true(self, tmp_path, template_path):
        xml = _generate(tmp_path, template_path, results=CheckResults(off_hours=True))
        checkboxes = _find_normal_abnormal(xml)
        for i in (5, 6, 7):
            assert checkboxes[i] == ABNORMAL, f"Occurrence {i}"
        # Others that should stay normal
        for i in (0, 1, 2, 3, 4, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18):
            assert checkboxes[i] == NORMAL, f"Occurrence {i}"

    def test_holiday_true(self, tmp_path, template_path):
        xml = _generate(tmp_path, template_path, results=CheckResults(holiday=True))
        checkboxes = _find_normal_abnormal(xml)
        assert checkboxes[8] == ABNORMAL
        assert checkboxes[7] == NORMAL  # adjacent, should stay normal

    def test_ip_switch_true(self, tmp_path, template_path):
        xml = _generate(tmp_path, template_path, results=CheckResults(ip_switch=True))
        checkboxes = _find_normal_abnormal(xml)
        for i in (11, 18):
            assert checkboxes[i] == ABNORMAL, f"Occurrence {i}"
        assert checkboxes[10] == NORMAL
        assert checkboxes[12] == NORMAL

    def test_high_volume_views_true(self, tmp_path, template_path):
        xml = _generate(tmp_path, template_path, results=CheckResults(high_volume_views=True))
        checkboxes = _find_normal_abnormal(xml)
        for i in (12, 14):
            assert checkboxes[i] == ABNORMAL, f"Occurrence {i}"
        assert checkboxes[13] == NORMAL

    def test_high_download_count_true_normal_abnormal(self, tmp_path, template_path):
        xml = _generate(tmp_path, template_path, results=CheckResults(high_download_count=True))
        checkboxes = _find_normal_abnormal(xml)
        for i in (13, 16):
            assert checkboxes[i] == ABNORMAL, f"Occurrence {i}"
        assert checkboxes[12] == NORMAL

    def test_high_volume_saves_true(self, tmp_path, template_path):
        xml = _generate(tmp_path, template_path, results=CheckResults(high_volume_saves=True))
        checkboxes = _find_normal_abnormal(xml)
        assert checkboxes[15] == ABNORMAL
        assert checkboxes[14] == NORMAL
        assert checkboxes[16] == NORMAL


# ── Phase 3: Checkbox - 유/무 ──────────────────────────────────────────


class TestYuMuCheckboxes:
    def test_all_false_all_mu(self, tmp_path, template_path):
        """When all False, all 4 유/무 checkboxes should be 무."""
        xml = _generate(tmp_path, template_path, results=CheckResults())
        checkboxes = _find_yu_mu(xml)
        assert len(checkboxes) == 4
        for i, cb in enumerate(checkboxes):
            assert cb == MU_NOT_DETECTED, f"유/무 occurrence {i} should be 무"

    def test_high_download_count_true_yu_mu(self, tmp_path, template_path):
        xml = _generate(tmp_path, template_path, results=CheckResults(high_download_count=True))
        checkboxes = _find_yu_mu(xml)
        assert checkboxes[0] == YU_DETECTED
        assert checkboxes[1] == MU_NOT_DETECTED
        assert checkboxes[2] == MU_NOT_DETECTED
        assert checkboxes[3] == MU_NOT_DETECTED

    def test_high_download_freq_true(self, tmp_path, template_path):
        xml = _generate(tmp_path, template_path, results=CheckResults(high_download_freq=True))
        checkboxes = _find_yu_mu(xml)
        assert checkboxes[1] == YU_DETECTED
        assert checkboxes[0] == MU_NOT_DETECTED

    def test_download_off_hours_true(self, tmp_path, template_path):
        xml = _generate(tmp_path, template_path, results=CheckResults(download_off_hours=True))
        checkboxes = _find_yu_mu(xml)
        assert checkboxes[2] == YU_DETECTED
        assert checkboxes[0] == MU_NOT_DETECTED

    def test_invalid_reason_true(self, tmp_path, template_path):
        xml = _generate(tmp_path, template_path, results=CheckResults(invalid_reason=True))
        checkboxes = _find_yu_mu(xml)
        assert checkboxes[3] == YU_DETECTED
        assert checkboxes[0] == MU_NOT_DETECTED


# ── Output validity ───────────────────────────────────────────────────


class TestOutputValidity:
    def test_output_is_valid_zip(self, tmp_path, template_path):
        output = str(tmp_path / "output.hwpx")
        generate_hwpx_report(
            template_path=template_path,
            output_path=output,
            inspection_date="2026. 5. 1.",
            log_count=200000,
            target_month_label="(2026년 4월) ",
            results=CheckResults(),
        )
        assert zipfile.is_zipfile(output)
