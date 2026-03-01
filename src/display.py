"""
This module handles styled output to the terminal using the rich library.
It provides centralized functions for outputting headers, results,
summaries, error messages, etc.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# 전역 콘솔 객체 생성
# legacy_windows=False to ensure proper Unicode support in PyInstaller builds
# force_terminal=True to prevent cell_len issues in PyInstaller builds
console = Console(markup=True, legacy_windows=False, force_terminal=True)


def print_header(title: str) -> None:
    """Prints the program's main header."""
    console.rule(f"[bold cyan]{title}[/bold cyan]", style="cyan")


def print_checker_header(title: str) -> None:
    """Prints the header for each checker."""
    console.print(Text(f"\n--- {title} 검사 ---", style="bold yellow"), justify="left")


def print_result(
    is_detected: bool, description: str, filename: str | None = None
) -> None:
    """
    Outputs the inspection result in [Good] or [Detected] format.
    If detected, also outputs the related filename.
    """
    if is_detected:
        status = Text("[검출]", style="bold red")
        message = f"{description} -> 저장 파일: {filename}"
    else:
        status = Text("[양호]", style="bold green")
        message = description

    console.print(f"  {status} {message}")


def print_summary(folder_path: str, total_count: int | None = None) -> None:
    """Outputs the final summary message after all tasks are completed."""

    summary_text = "[bold green]모든 작업이 완료되었습니다.[/bold green]\n\n"

    if total_count is not None:
        summary_text += f"붙임2, 3, 4 원본 데이터 건수 합계: {total_count}건\n\n"

    summary_text += "최종 결과는 아래 폴더를 확인해주세요.\n"
    summary_text += f"[underline blue]{folder_path}[/underline blue]"

    console.print(
        Panel(
            summary_text,
            title="[bold]작업 완료[/bold]",
            border_style="green",
        )
    )


def print_error(message: str) -> None:
    """Outputs an error message."""
    console.print(f"[bold red]오류:[/bold red] {message}")


def print_info(message: str) -> None:
    """Outputs a simple information message."""
    console.print(f"[cyan]▶[/cyan] {message}")


def print_zip_header() -> None:
    """Outputs the compression task header."""
    console.print(Text("\n--- 압축 작업 시작 ---", style="bold yellow"), justify="left")


def print_zip_result(zip_name: str, num_files: int) -> None:
    """Outputs the compression task result."""
    console.print(
        f"  [bold green]OK[/bold green] {zip_name} 생성 ({num_files}개 파일 포함)"
    )


def print_zip_warning(prefix: str) -> None:
    """Outputs a warning when there are no files to compress."""
    console.print(f"  [yellow]WARNING[/yellow] {prefix}로 시작하는 파일 없음")


def wait_for_exit() -> None:
    """Waits for user input before exiting. Useful for GUI launchers."""
    console.print()
    console.input("[dim]종료하려면 Enter 키를 누르세요...[/dim]")
