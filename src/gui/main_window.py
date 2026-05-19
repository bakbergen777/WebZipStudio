"""Main window for WebZip Studio."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QStatusBar,
    QTabWidget,
)

from src.core.manager import CompressionResult
from src.gui.analytics_tab import AnalyticsTab
from src.gui.compress_tab import CompressTab
from src.gui.decompress_tab import DecompressTab
from src.gui.incremental_tab import IncrementalTab
from src.gui.style import STYLESHEET
from src.gui.visualizer_tab import VisualizerTab


class MainWindow(QMainWindow):
    def __init__(self, default_output_dir: Optional[Path] = None) -> None:
        super().__init__()
        self.setWindowTitle("WebZip Studio — Webpage Compression System")
        self.resize(1200, 760)
        self.setStyleSheet(STYLESHEET)

        if default_output_dir is None:
            default_output_dir = Path.home() / "WebZipStudio_output"
        self.default_output_dir = default_output_dir

        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.compress_tab = CompressTab(default_output_dir, self)
        self.decompress_tab = DecompressTab(self)
        self.analytics_tab = AnalyticsTab(self)
        self.visualizer_tab = VisualizerTab(self)
        self.incremental_tab = IncrementalTab(self)

        self.tabs.addTab(self.compress_tab, "Compress")
        self.tabs.addTab(self.decompress_tab, "Decompress")
        self.tabs.addTab(self.analytics_tab, "Analytics")
        self.tabs.addTab(self.visualizer_tab, "Visualizer")
        self.tabs.addTab(self.incremental_tab, "Incremental")

        self.compress_tab.compression_finished.connect(self._on_compression_done)

        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Ready.")

        self._build_menu()

    # -----------------------------------------------------------------
    def _build_menu(self) -> None:
        menu = self.menuBar()
        file_menu: QMenu = menu.addMenu("&File")

        open_pkg = QAction("Open package…", self)
        open_pkg.triggered.connect(self._open_package_dialog)
        file_menu.addAction(open_pkg)

        file_menu.addSeparator()
        quit_act = QAction("Quit", self)
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

        help_menu: QMenu = menu.addMenu("&Help")
        about = QAction("About", self)
        about.triggered.connect(self._show_about)
        help_menu.addAction(about)

    def _open_package_dialog(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select package folder", "")
        if folder:
            self.decompress_tab.pkg_edit.setText(folder)
            self.tabs.setCurrentWidget(self.decompress_tab)

    def _show_about(self) -> None:
        QMessageBox.information(
            self,
            "About WebZip Studio",
            "WebZip Studio — Webpage Compression System\n\n"
            "Final project for the Data Structure and its Algorithms course.\n\n"
            "Group:\n"
            "  Bakbergen Amir   202469990559\n"
            "  Bakbergen Alen   202469990562\n"
            "  Huang Liu Diego David  202469990549\n",
        )

    # -----------------------------------------------------------------
    def _on_compression_done(self, result: CompressionResult) -> None:
        self.analytics_tab.update_with_result(result)
        self.visualizer_tab.update_with_result(result)
        self.incremental_tab.update_with_result(result)
        self.statusBar().showMessage(
            f"Last run: {result.manifest.totals.get('file_count', 0)} files, "
            f"ratio {result.manifest.totals.get('ratio', 1.0):.3f}"
        )
        self.tabs.setCurrentWidget(self.analytics_tab)
