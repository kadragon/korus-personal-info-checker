"""Tests for scripts/reconcile-harness.py utility functions."""

import importlib.util
from pathlib import Path

# Load module directly (hyphenated filename, not on sys.path)
_SCRIPT = Path(__file__).parent.parent / "scripts" / "reconcile-harness.py"
_spec = importlib.util.spec_from_file_location("reconcile_harness", _SCRIPT)
_rh = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_rh)  # type: ignore[union-attr]

remove_empty_headings = _rh.remove_empty_headings
append_changelog = _rh.append_changelog


class TestRemoveEmptyHeadings:
    def test_preserves_trailing_newline(self):
        """Input ending in \\n must produce output ending in \\n (POSIX)."""
        text = "# Section\n\n- item one\n- item two\n"
        result = remove_empty_headings(text)
        assert result.endswith("\n"), (
            "remove_empty_headings dropped the trailing newline — non-POSIX output"
        )

    def test_no_trailing_newline_unchanged(self):
        """Input without trailing newline must not gain one."""
        text = "# Section\n\n- item"
        result = remove_empty_headings(text)
        assert not result.endswith("\n")

    def test_removes_empty_heading_before_eof(self):
        """Heading with no following non-empty content is dropped."""
        text = "# Occupied\n\n- item\n\n# Empty\n"
        result = remove_empty_headings(text)
        assert "# Empty" not in result

    def test_keeps_occupied_heading(self):
        """Heading followed by content is kept."""
        text = "# Occupied\n\n- item\n"
        result = remove_empty_headings(text)
        assert "# Occupied" in result

    def test_empty_string(self):
        """Empty string returns empty string."""
        assert remove_empty_headings("") == ""

    def test_all_headings_stripped_returns_empty_not_newline(self):
        """All content stripped from \\n-terminated input must return '' not '\\n'."""
        text = "## Active\n"
        result = remove_empty_headings(text)
        assert result == "", f"expected '' but got {result!r}"


class TestAppendChangelog:
    def test_uses_append_mode(self, tmp_path, monkeypatch):
        """append_changelog must not overwrite existing content."""
        changelog = tmp_path / "CHANGELOG.md"
        existing = "# Existing entry\n\nsome content\n"
        changelog.write_text(existing, encoding="utf-8")

        monkeypatch.setattr(_rh, "CHANGELOG", changelog)
        append_changelog("Test Sprint", "summary text")

        result = changelog.read_text(encoding="utf-8")
        assert result.startswith(existing), (
            "append_changelog overwrote existing content instead of appending"
        )
        assert "Test Sprint" in result
        assert "summary text" in result

    def test_skips_when_changelog_missing(self, tmp_path, monkeypatch):
        """append_changelog is a no-op when CHANGELOG does not exist."""
        monkeypatch.setattr(_rh, "CHANGELOG", tmp_path / "nonexistent.md")
        # Should not raise
        append_changelog("Sprint", "summary")
