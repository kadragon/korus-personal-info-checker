"""
Tests for display module functions.

GENERATED FROM SPEC-test-coverage-improvement-1
Trace: SPEC-test-coverage-improvement-1, TEST-display-1
"""

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src import display


class TestPrintHeader:
    """Tests for print_header function."""

    def test_print_header(self, mocker):
        """Test that print_header calls console.rule with correct parameters."""
        mock_rule = mocker.patch.object(display.console, "rule")

        display.print_header("Test Title")

        mock_rule.assert_called_once_with(
            "[bold cyan]Test Title[/bold cyan]", style="cyan"
        )


class TestPrintCheckerHeader:
    """Tests for print_checker_header function."""

    def test_print_checker_header(self, mocker):
        """Test that print_checker_header calls console.print with correct Text object."""
        mock_print = mocker.patch.object(display.console, "print")

        display.print_checker_header("로그인")

        # Verify print was called once
        assert mock_print.call_count == 1
        # Get the Text object that was passed
        call_args = mock_print.call_args
        text_obj = call_args[0][0]

        # Verify it's a Text object with correct content and style
        assert isinstance(text_obj, Text)
        assert "로그인 검사" in str(text_obj)
        assert text_obj.style == "bold yellow"


class TestPrintResult:
    """Tests for print_result function."""

    def test_print_result_detected_with_filename(self, mocker):
        """Test print_result when issue is detected with filename."""
        mock_print = mocker.patch.object(display.console, "print")

        display.print_result(
            is_detected=True,
            description="휴일 접근 발견",
            filename="holiday_access.xlsx"
        )

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "[검출]" in call_args
        assert "휴일 접근 발견" in call_args
        assert "holiday_access.xlsx" in call_args

    def test_print_result_not_detected(self, mocker):
        """Test print_result when no issue is detected."""
        mock_print = mocker.patch.object(display.console, "print")

        display.print_result(
            is_detected=False,
            description="정상 접근"
        )

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "[양호]" in call_args
        assert "정상 접근" in call_args

    def test_print_result_detected_without_filename(self, mocker):
        """Test print_result when detected but no filename provided."""
        mock_print = mocker.patch.object(display.console, "print")

        display.print_result(
            is_detected=True,
            description="문제 발견",
            filename=None
        )

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "[검출]" in call_args
        assert "문제 발견" in call_args


class TestPrintSummary:
    """Tests for print_summary function."""

    def test_print_summary_with_count(self, mocker):
        """Test print_summary with total_count provided."""
        mock_print = mocker.patch.object(display.console, "print")

        display.print_summary("/path/to/folder", total_count=150)

        mock_print.assert_called_once()
        # Verify Panel was created with correct content
        call_args = mock_print.call_args[0][0]
        assert isinstance(call_args, Panel)

    def test_print_summary_without_count(self, mocker):
        """Test print_summary without total_count."""
        mock_print = mocker.patch.object(display.console, "print")

        display.print_summary("/path/to/folder", total_count=None)

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert isinstance(call_args, Panel)


class TestPrintError:
    """Tests for print_error function."""

    def test_print_error(self, mocker):
        """Test that print_error formats and prints error message."""
        mock_print = mocker.patch.object(display.console, "print")

        display.print_error("파일을 찾을 수 없습니다")

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "오류" in call_args
        assert "파일을 찾을 수 없습니다" in call_args


class TestPrintInfo:
    """Tests for print_info function."""

    def test_print_info(self, mocker):
        """Test that print_info formats and prints info message."""
        mock_print = mocker.patch.object(display.console, "print")

        display.print_info("처리 중입니다")

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "처리 중입니다" in call_args


class TestPrintZipHeader:
    """Tests for print_zip_header function."""

    def test_print_zip_header(self, mocker):
        """Test that print_zip_header prints correct header."""
        mock_print = mocker.patch.object(display.console, "print")

        display.print_zip_header()

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert isinstance(call_args, Text)
        assert "압축 작업 시작" in str(call_args)


class TestPrintZipResult:
    """Tests for print_zip_result function."""

    def test_print_zip_result(self, mocker):
        """Test that print_zip_result prints correct result message."""
        mock_print = mocker.patch.object(display.console, "print")

        display.print_zip_result("test.zip", 5)

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "test.zip" in call_args
        assert "5개 파일" in call_args
        assert "OK" in call_args


class TestPrintZipWarning:
    """Tests for print_zip_warning function."""

    def test_print_zip_warning(self, mocker):
        """Test that print_zip_warning prints correct warning message."""
        mock_print = mocker.patch.object(display.console, "print")

        display.print_zip_warning("[붙임2]")

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "[붙임2]" in call_args
        assert "WARNING" in call_args
