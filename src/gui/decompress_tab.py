"""Decompress tab — restore a package (folder or .webzip) and verify integrity."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.integrity import sha256_file
from src.core.manifest import Manifest
from src.gui.workers import DecompressWorker
from src.utils.formatting import format_size


class DecompressTab(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.worker: Optional[DecompressWorker] = None
        self._last_output: Optional[Path] = None
        self._last_manifest: Optional[Manifest] = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        title = QLabel("Decompress and verify")
        title.setObjectName("title")
        subtitle = QLabel(
            "Pick either a .webzip archive file or a package folder. Files restore to your "
            "chosen folder; text restoration is verified by SHA-256 against the manifest."
        )
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addWidget(self._step_label("STEP 1 · CHOOSE PACKAGE"))
        pkg_row = QHBoxLayout()
        pkg_row.setSpacing(10)
        self.pkg_edit = QLineEdit("")
        self.pkg_edit.setPlaceholderText("…/MySite_Compressed.webzip  or  …/MySite_Compressed/")
        pkg_row.addWidget(self.pkg_edit, 2)
        btn_pkg_file = QPushButton("📦  Choose archive…")
        btn_pkg_file.clicked.connect(self._pick_archive)
        pkg_row.addWidget(btn_pkg_file)
        btn_pkg_dir = QPushButton("📁  Choose folder…")
        btn_pkg_dir.setObjectName("secondary")
        btn_pkg_dir.clicked.connect(self._pick_folder)
        pkg_row.addWidget(btn_pkg_dir)
        layout.addLayout(pkg_row)

        layout.addWidget(self._step_label("STEP 2 · RESTORE TO"))
        out_row = QHBoxLayout()
        out_row.setSpacing(10)
        self.out_edit = QLineEdit("")
        self.out_edit.setPlaceholderText("e.g. /Users/me/Desktop/MySite_Restored")
        out_row.addWidget(self.out_edit, 2)
        btn_out = QPushButton("Browse…")
        btn_out.setObjectName("secondary")
        btn_out.clicked.connect(self._pick_output)
        out_row.addWidget(btn_out)
        layout.addLayout(out_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        self.progress.setMinimumHeight(24)
        layout.addWidget(self.progress)

        run_row = QHBoxLayout()
        run_row.addStretch()
        self.btn_run = QPushButton("⚡  Decompress")
        self.btn_run.setObjectName("success")
        self.btn_run.setMinimumHeight(46)
        self.btn_run.setMinimumWidth(180)
        self.btn_run.clicked.connect(self._start)
        run_row.addWidget(self.btn_run)
        layout.addLayout(run_row)

        # Verification table
        self.table = QTableWidget(0, 5, self)
        self.table.setHorizontalHeaderLabels(
            ["File", "Strategy", "Original size", "Compressed size", "Verification"]
        )
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 5):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        layout.addWidget(self.table, stretch=1)

    @staticmethod
    def _step_label(text: str):
        label = QLabel(text)
        label.setObjectName("step")
        return label

    # -----------------------------------------------------------------
    def _pick_archive(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select .webzip archive",
            self.pkg_edit.text() or str(Path.home()),
            "WebZip archive (*.webzip *.zip);;All files (*.*)",
        )
        if path:
            self.pkg_edit.setText(path)

    def _pick_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Select package folder",
            self.pkg_edit.text() or str(Path.home())
        )
        if folder:
            self.pkg_edit.setText(folder)

    def _pick_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Select restore folder",
            self.out_edit.text() or str(Path.home())
        )
        if folder:
            self.out_edit.setText(folder)

    def _start(self) -> None:
        pkg_text = self.pkg_edit.text().strip()
        if not pkg_text:
            QMessageBox.warning(self, "Pick a package", "Choose a .webzip archive or a package folder.")
            return
        package = Path(pkg_text).expanduser()
        if not package.exists():
            QMessageBox.warning(self, "Missing package", f"Path does not exist:\n{package}")
            return

        out_text = self.out_edit.text().strip()
        if not out_text:
            QMessageBox.warning(self, "Pick a restore folder", "Choose where to put the restored files.")
            return
        out = Path(out_text).expanduser()
        try:
            out.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            QMessageBox.critical(self, "Cannot create folder", str(exc))
            return

        self.btn_run.setEnabled(False)
        self.progress.setValue(0)
        self.table.setRowCount(0)
        self._last_output = out

        self.worker = DecompressWorker(package, out)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_ok.connect(self._on_done)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(lambda: self.btn_run.setEnabled(True))
        self.worker.start()

    def _on_progress(self, index: int, total: int, name: str) -> None:
        if total <= 0:
            return
        self.progress.setValue(int(index / total * 100))

    def _on_done(self, manifest: Manifest) -> None:
        self.progress.setValue(100)
        self._last_manifest = manifest
        self._render_verification()
        QMessageBox.information(self, "Restored", f"Restored {len(manifest.files)} files.")

    def _on_failed(self, msg: str) -> None:
        QMessageBox.critical(self, "Decompression failed", msg)

    def _render_verification(self) -> None:
        if not self._last_manifest or not self._last_output:
            return
        self.table.setRowCount(len(self._last_manifest.files))
        for row, entry in enumerate(self._last_manifest.files):
            restored = self._last_output / entry.relative_path
            verification = "—"
            if entry.strategy == "text" and restored.exists():
                actual_hash = sha256_file(restored)
                verification = "MATCH" if actual_hash == entry.sha256_original else "MISMATCH"
            elif entry.strategy in ("image", "copy"):
                verification = "OK" if restored.exists() else "MISSING"

            self.table.setItem(row, 0, QTableWidgetItem(entry.relative_path))
            self.table.setItem(row, 1, QTableWidgetItem(entry.strategy))
            self.table.setItem(row, 2, QTableWidgetItem(format_size(entry.original_size)))
            self.table.setItem(row, 3, QTableWidgetItem(format_size(entry.compressed_size)))
            v_item = QTableWidgetItem(verification)
            if verification in ("MATCH", "OK"):
                v_item.setForeground(Qt.darkGreen)
            elif verification in ("MISMATCH", "MISSING"):
                v_item.setForeground(Qt.red)
            self.table.setItem(row, 4, v_item)
