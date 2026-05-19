"""WebZip Studio entry point.

Run the desktop GUI:
    python main.py

Or use the command-line interface:
    python -m src.cli compress data/sample_webpage -o build/sample_pkg
    python -m src.cli decompress build/sample_pkg -o build/sample_restored
"""

from __future__ import annotations

import sys
from pathlib import Path


def _print_install_hint() -> None:
    print(
        "PySide6 is not installed. Install dependencies with:\n"
        "    pip install -r requirements.txt\n\n"
        "You can still use the command line interface:\n"
        "    python -m src.cli compress data/sample_webpage -o build/sample_pkg\n"
        "    python -m src.cli decompress build/sample_pkg -o build/sample_restored\n"
    )


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except Exception:
        _print_install_hint()
        return 1

    from src.gui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("WebZip Studio")
    default_out = Path.home() / "WebZipStudio_output"
    window = MainWindow(default_output_dir=default_out)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
