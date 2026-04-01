"""Generate HWPX inspection report by filling a template with dynamic values.

HWPX files are ZIP archives containing XML. This module copies a template,
modifies ``Contents/section0.xml`` to replace placeholder text and set
checkboxes, then writes the result back into the ZIP.
"""

from __future__ import annotations

import re
import shutil
import zipfile
from collections.abc import Mapping

from .report_generator import CheckResults

# Checkbox text patterns
_NORMAL = "☑정상 / □ 비정상"
_ABNORMAL = "□정상 / ☑ 비정상"
_YU = "☑ 유 / □ 무"
_MU = "□ 유 / ☑ 무"

# Regex that matches either form of each checkbox type
_RE_NORMAL_ABNORMAL = re.compile(r"[☑□]정상 / [☑□] 비정상")
_RE_YU_MU = re.compile(r"[☑□] 유 / [☑□] 무")

# Mapping: occurrence index -> CheckResults field name (or None for "always 정상")
_NORMAL_ABNORMAL_MAP: dict[int, str | None] = {
    0: None,
    1: None,
    2: None,
    3: None,
    4: None,
    5: "off_hours",
    6: "off_hours",
    7: "off_hours",
    8: "holiday",
    9: None,
    10: None,
    11: "ip_switch",
    12: "high_volume_views",
    13: "high_download_count",
    14: "high_volume_views",
    15: "high_volume_saves",
    16: "high_download_count",
    17: None,
    18: "ip_switch",
}

_YU_MU_MAP: dict[int, str] = {
    0: "high_download_count",
    1: "high_download_freq",
    2: "download_off_hours",
    3: "invalid_reason",
}


def _replace_checkboxes(
    xml: str,
    pattern: re.Pattern[str],
    mapping: Mapping[int, str | None],
    results: CheckResults,
    true_text: str,
    false_text: str,
) -> str:
    """Replace checkbox occurrences based on the mapping and results."""
    occurrence_idx = 0

    def _replacer(match: re.Match[str]) -> str:
        nonlocal occurrence_idx
        idx = occurrence_idx
        occurrence_idx += 1
        field = mapping.get(idx)
        if field is None:
            return false_text  # "always normal" / "always 무"
        detected = getattr(results, field, False)
        return true_text if detected else false_text

    return pattern.sub(_replacer, xml)


def generate_hwpx_report(
    template_path: str,
    output_path: str,
    inspection_date: str,
    log_count: int,
    target_month_label: str,
    results: CheckResults,
) -> None:
    """Generate a filled HWPX report from a template.

    Args:
        template_path: Path to the HWPX template file.
        output_path: Path where the generated HWPX will be written.
        inspection_date: Inspection date string (e.g. "2026. 5. 1.").
        log_count: Total access log count to display.
        target_month_label: Target month label (e.g. "(2026년 4월) ").
        results: Boolean flags for each check category.
    """
    # Step 1: Copy template to output
    shutil.copy2(template_path, output_path)

    # Step 2: Read section0.xml from the ZIP
    with zipfile.ZipFile(output_path, "r") as zin:
        xml = zin.read("Contents/section0.xml").decode("utf-8")
        all_names = zin.namelist()
        section = "Contents/section0.xml"
        other_files = {name: zin.read(name) for name in all_names if name != section}

    # Step 3: Text replacements
    xml = xml.replace("2026. 4. 1.", inspection_date)
    xml = xml.replace("181,273", f"{log_count:,}")
    xml = xml.replace("(2026년 3월) ", target_month_label)

    # Step 4: Checkbox replacements - 정상/비정상
    xml = _replace_checkboxes(
        xml,
        _RE_NORMAL_ABNORMAL,
        _NORMAL_ABNORMAL_MAP,
        results,
        true_text=_ABNORMAL,
        false_text=_NORMAL,
    )

    # Step 5: Checkbox replacements - 유/무
    xml = _replace_checkboxes(
        xml,
        _RE_YU_MU,
        _YU_MU_MAP,
        results,
        true_text=_YU,
        false_text=_MU,
    )

    # Step 6: Write modified XML back into the ZIP
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in other_files.items():
            zout.writestr(name, data)
        zout.writestr("Contents/section0.xml", xml.encode("utf-8"))
