"""
Launcher script that prompts the user to select a download folder.
"""

from tkinter import Tk, filedialog

from src.display import wait_for_exit
from src.main import run_with_download_dir


def main() -> None:
    """
    Prompts the user to select the download directory and runs the checker.
    """
    root = Tk()
    root.withdraw()
    try:
        download_dir = filedialog.askdirectory(title="다운로드 폴더 선택")

        if not download_dir:
            return

        run_with_download_dir(download_dir)
        wait_for_exit()
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
