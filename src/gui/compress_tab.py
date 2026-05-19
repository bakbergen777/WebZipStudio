"""Compress tab — file selection, strategy preview, batch compression.

Workflow:
    1. Add files / folder
    2. Pick output folder
    3. Pick quality and mode
    4. Press "Compress now" — produces both a package folder AND a
       single-file `.webzip` archive that can be shared in one click.
"""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.manager import CompressionResult
from src.core.strategy import StrategySelector
from src.gui.workers import CompressWorker
from src.utils.formatting import format_size


# ---------------------------------------------------------------------
def open_in_native_browser(path: Path) -> None:
    """Open a folder (or reveal a file) in the user's native file browser."""
    p = Path(path).resolve()
    p_str = str(p)
    try:
        system = platform.system()
        if system == "Windows":
            if p.is_file():
                subprocess.Popen(["explorer", "/select,", p_str])
            else:
                os.startfile(p_str)  # type: ignore[attr-defined]
        elif system == "Darwin":
            if p.is_file():
                subprocess.Popen(["open", "-R", p_str])
            else:
                subprocess.Popen(["open", p_str])
        else:
            target = p if p.is_dir() else p.parent
            subprocess.Popen(["xdg-open", str(target)])
    except Exception:
        pass


# ---------------------------------------------------------------------
class FileTable(QTableWidget):
    """Table that shows the queued files; supports drag and drop."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(0, 4, parent)
        self.setHorizontalHeaderLabels(["File", "Type", "Size", "Strategy"])
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 4):
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.setAcceptDrops(True)
        self.setMinimumHeight(220)

        self.selector = StrategySelector()
        self.paths: List[Path] = []

    def add_paths(self, paths: List[Path]) -> int:
        added = 0
        for raw in paths:
            p = Path(raw)
            if p.is_dir():
                for child in sorted(p.rglob("*")):
                    if child.is_file():
                        if self._add_one(child):
                            added += 1
            elif p.is_file():
                if self._add_one(p):
                    added += 1
        return added

    def _add_one(self, path: Path) -> bool:
        if path in self.paths:
            return False
        self.paths.append(path)
        row = self.rowCount()
        self.insertRow(row)
        ext = path.suffix.lower().lstrip(".")
        strategy = self.selector.for_path(path)
        self.setItem(row, 0, QTableWidgetItem(str(path)))
        self.setItem(row, 1, QTableWidgetItem(ext or "-"))
        try:
            size_str = format_size(path.stat().st_size)
        except OSError:
            size_str = "-"
        self.setItem(row, 2, QTableWidgetItem(size_str))
        item = QTableWidgetItem(strategy)
        if strategy == "skip":
            item.setForeground(Qt.darkGray)
        self.setItem(row, 3, item)
        return True

    def clear_paths(self) -> None:
        self.paths.clear()
        self.setRowCount(0)

    # Drag & drop
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        paths: List[Path] = []
        for u in urls:
            if isinstance(u, QUrl):
                local = u.toLocalFile()
                if local:
                    paths.append(Path(local))
        if paths:
            self.add_paths(paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


# ---------------------------------------------------------------------
class CompressTab(QWidget):
    compression_finished = Signal(object)  # CompressionResult

    def __init__(self, default_output_dir: Path, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.default_output_dir = Path(default_output_dir)
        self.worker: Optional[CompressWorker] = None
        self._last_output_dir: Optional[Path] = None
        self._last_archive: Optional[Path] = None
        self._build_ui()

    # -----------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        title = QLabel("Compress webpage resources")
        title.setObjectName("title")
        subtitle = QLabel(
            "Add HTML / CSS / JS / JPG / PNG files (or a whole folder), pick an output "
            "folder, then press Compress now. The result is a shareable .webzip archive."
        )
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Step 1
        layout.addWidget(self._step_label("STEP 1 · ADD FILES"))
        picker_row = QHBoxLayout()
        picker_row.setSpacing(10)
        btn_files = QPushButton("📄  Add files")
        btn_files.clicked.connect(self._pick_files)
        btn_folder = QPushButton("📁  Add folder")
        btn_folder.clicked.connect(self._pick_folder)
        btn_sample = QPushButton("✨  Use sample")
        btn_sample.setObjectName("secondary")
        btn_sample.clicked.connect(self._use_sample)
        btn_clear = QPushButton("🗑  Clear list")
        btn_clear.setObjectName("secondary")
        btn_clear.clicked.connect(self._clear_list)
        picker_row.addWidget(btn_files)
        picker_row.addWidget(btn_folder)
        picker_row.addWidget(btn_sample)
        picker_row.addWidget(btn_clear)
        picker_row.addStretch()
        layout.addLayout(picker_row)

        self.table = FileTable()
        layout.addWidget(self.table, stretch=1)
        self.count_label = QLabel("0 files queued.")
        self.count_label.setObjectName("subtitle")
        layout.addWidget(self.count_label)

        # Step 2
        layout.addWidget(self._step_label("STEP 2 · OUTPUT FOLDER"))
        out_row = QHBoxLayout()
        out_row.setSpacing(10)
        self.output_edit = QLineEdit(str(self.default_output_dir))
        self.output_edit.setPlaceholderText("e.g. C:/Users/me/Desktop/MySite_Compressed")
        out_row.addWidget(self.output_edit, 2)
        btn_choose_out = QPushButton("Browse…")
        btn_choose_out.setObjectName("secondary")
        btn_choose_out.clicked.connect(self._pick_output)
        out_row.addWidget(btn_choose_out)
        btn_open_out = QPushButton("Open")
        btn_open_out.setObjectName("secondary")
        btn_open_out.clicked.connect(self._open_output)
        out_row.addWidget(btn_open_out)
        layout.addLayout(out_row)

        # Step 3
        layout.addWidget(self._step_label("STEP 3 · QUALITY AND MODE"))
        opts_row = QHBoxLayout()
        opts_row.setSpacing(10)
        opts_row.addWidget(QLabel("Quality:"))
        self.quality = QComboBox()
        self.quality.addItems(["High", "Balanced", "Strong"])
        self.quality.setCurrentText("Balanced")
        self.quality.setMinimumWidth(120)
        opts_row.addWidget(self.quality)

        opts_row.addSpacing(20)
        self.archive_box = QCheckBox("Produce single .webzip archive")
        self.archive_box.setChecked(True)
        opts_row.addWidget(self.archive_box)

        opts_row.addSpacing(20)
        self.incremental_box = QCheckBox("Incremental (skip unchanged files)")
        opts_row.addWidget(self.incremental_box)
        opts_row.addStretch()
        layout.addLayout(opts_row)

        # Step 4
        layout.addWidget(self._step_label("STEP 4 · COMPRESS"))
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        self.progress.setMinimumHeight(24)
        self.progress_label = QLabel("Ready. Add files, pick a folder, then press Compress now.")
        self.progress_label.setObjectName("subtitle")
        layout.addWidget(self.progress)
        layout.addWidget(self.progress_label)

        run_row = QHBoxLayout()
        run_row.addStretch()

        self.btn_run = QPushButton("⚡  Compress now")
        self.btn_run.setObjectName("success")
        self.btn_run.setMinimumHeight(50)
        self.btn_run.setMinimumWidth(220)
        self.btn_run.setShortcut("Ctrl+Return")
        self.btn_run.setToolTip("Run the compression pipeline (Ctrl+Enter)")
        self.btn_run.clicked.connect(self._start)
        run_row.addWidget(self.btn_run)

        self.btn_reveal = QPushButton("📦  Reveal archive")
        self.btn_reveal.setObjectName("secondary")
        self.btn_reveal.setMinimumHeight(50)
        self.btn_reveal.setEnabled(False)
        self.btn_reveal.setToolTip("Show the resulting .webzip archive in the file browser")
        self.btn_reveal.clicked.connect(self._reveal_archive)
        run_row.addWidget(self.btn_reveal)
        layout.addLayout(run_row)

    # -----------------------------------------------------------------
    @staticmethod
    def _step_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("step")
        return label

    # -----------------------------------------------------------------
    def _pick_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select files to compress",
            str(Path.home()),
            "Webpage resources (*.html *.htm *.css *.js *.json *.txt *.svg *.jpg *.jpeg *.png);;All files (*.*)",
        )
        if files:
            added = self.table.add_paths([Path(f) for f in files])
            self._update_count(added=added)

    def _pick_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Select folder to compress", str(Path.home())
        )
        if folder:
            added = self.table.add_paths([Path(folder)])
            self._update_count(added=added)

    def _use_sample(self) -> None:
        here = Path(__file__).resolve().parents[2]
        candidates = [
            here / "data" / "sample_webpage",
            here / "data" / "sample_large_case",
            Path.cwd() / "data" / "sample_webpage",
        ]
        for c in candidates:
            if c.exists():
                added = self.table.add_paths([c])
                self._update_count(added=added)
                self.progress_label.setText(f"Loaded sample from {c}")
                return
        QMessageBox.information(
            self,
            "Sample not found",
            "Could not find data/sample_webpage. Please add files manually.",
        )

    def _pick_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Select output folder", self.output_edit.text() or str(Path.home())
        )
        if folder:
            self.output_edit.setText(folder)

    def _open_output(self) -> None:
        target = self._last_output_dir or Path(self.output_edit.text() or str(Path.home()))
        target = Path(target).expanduser()
        if not target.exists():
            try:
                target.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                QMessageBox.warning(self, "Cannot open folder", str(exc))
                return
        open_in_native_browser(target)

    def _reveal_archive(self) -> None:
        if self._last_archive and self._last_archive.exists():
            open_in_native_browser(self._last_archive)
        elif self._last_output_dir:
            open_in_native_browser(self._last_output_dir)

    def _clear_list(self) -> None:
        self.table.clear_paths()
        self.progress.setValue(0)
        self.progress_label.setText("Ready.")
        self.btn_reveal.setEnabled(False)
        self._update_count()

    def _update_count(self, added: int = 0) -> None:
        n = len(self.table.paths)
        self.count_label.setText(f"{n} file{'s' if n != 1 else ''} queued.")
        if added:
            self.progress_label.setText(f"Added {added} file{'s' if added != 1 else ''}.")

    # -----------------------------------------------------------------
    def _start(self) -> None:
        if not self.table.paths:
            QMessageBox.warning(
                self,
                "No files",
                "No files queued. Click 'Add files' or 'Add folder' first.",
            )
            return
        out_text = self.output_edit.text().strip()
        if not out_text:
            QMessageBox.warning(
                self,
                "Output folder needed",
                "Please choose an output folder (Step 2).",
            )
            return
        out_dir = Path(out_text).expanduser()
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Cannot create output folder",
                f"Could not create:\n{out_dir}\n\n{exc}",
            )
            return

        self._last_output_dir = out_dir
        self._last_archive = None
        self.btn_run.setEnabled(False)
        self.btn_reveal.setEnabled(False)
        self.progress.setValue(0)
        self.progress_label.setText("Starting…")

        self.worker = CompressWorker(
            sources=list(self.table.paths),
            output_dir=out_dir,
            preset=self.quality.currentText(),
            package_label=out_dir.name,
            incremental=self.incremental_box.isChecked(),
            make_archive=self.archive_box.isChecked(),
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_ok.connect(self._on_done)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(self._on_thread_finished)
        self.worker.start()

    def _on_progress(self, index: int, total: int, name: str) -> None:
        if total <= 0:
            return
        pct = int(index / total * 100)
        self.progress.setValue(pct)
        self.progress_label.setText(f"[{index}/{total}] {name}")

    def _on_done(self, result: CompressionResult) -> None:
        self.progress.setValue(100)
        totals = result.manifest.totals
        ratio = totals.get("ratio", 1.0)
        savings = totals.get("savings_pct", 0.0)
        n = int(totals.get("file_count", 0))

        self._last_archive = result.archive_path
        self.btn_reveal.setEnabled(result.archive_path is not None and result.archive_path.exists())

        archive_str = ""
        if result.archive_path:
            archive_str = (
                f"\nArchive:    {format_size(result.archive_size)}\n"
                f"            {result.archive_path}"
            )
            self.progress_label.setText(
                f"Done — {n} files, ratio {ratio:.3f} ({savings:.1f}% saved). "
                f"Archive: {result.archive_path.name}"
            )
        else:
            self.progress_label.setText(
                f"Done. {n} file(s) compressed — ratio {ratio:.3f} ({savings:.1f}% saved)."
            )
        self.compression_finished.emit(result)

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Compression complete")
        msg.setText(
            f"Compressed {n} file(s).\n\n"
            f"Original:   {format_size(totals.get('original_size', 0))}\n"
            f"Compressed: {format_size(totals.get('compressed_size', 0))}\n"
            f"Ratio:      {ratio:.3f}\n"
            f"Savings:    {savings:.1f}%\n"
            f"{archive_str}\n\n"
            f"Output folder:\n{result.output_dir}"
        )
        reveal_btn = None
        if result.archive_path and result.archive_path.exists():
            reveal_btn = msg.addButton("Reveal archive", QMessageBox.ActionRole)
        open_btn = msg.addButton("Open folder", QMessageBox.ActionRole)
        msg.addButton(QMessageBox.Ok)
        msg.exec()
        clicked = msg.clickedButton()
        if clicked is reveal_btn and result.archive_path:
            open_in_native_browser(result.archive_path)
        elif clicked is open_btn:
            open_in_native_browser(result.output_dir)

    def _on_failed(self, message: str) -> None:
        self.progress_label.setText(f"Error: {message[:120]}")
        QMessageBox.critical(
            self,
            "Compression failed",
            f"The compression step raised an error:\n\n{message}\n\n"
            f"Run `python tests/run_all.py` to verify the pipeline works "
            f"on the bundled sample data.",
        )

    def _on_thread_finished(self) -> None:
        self.btn_run.setEnabled(True)
        self.worker = None
