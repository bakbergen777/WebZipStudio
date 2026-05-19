"""Incremental tab — show which files were unchanged/recompressed/added/removed."""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.manager import CompressionResult


def _section(label: str, color: str) -> QWidget:
    box = QWidget()
    box.setStyleSheet(f"background:{color};border-radius:8px;padding:8px;")
    return box


class IncrementalTab(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)
        title = QLabel("Incremental mode")
        title.setObjectName("title")
        sub = QLabel(
            "Tick the 'Incremental' box on the Compress tab to skip files whose SHA-256 "
            "hash has not changed since the last run."
        )
        sub.setObjectName("subtitle")
        sub.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(sub)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Status", "File"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, stretch=1)

    def update_with_result(self, result: CompressionResult) -> None:
        summary = result.incremental_summary
        rows: List = []
        for label, key in (
            ("UNCHANGED", "unchanged"),
            ("RECOMPRESSED", "recompressed"),
            ("ADDED", "added"),
            ("REMOVED", "removed"),
        ):
            for path in summary.get(key, []):
                rows.append((label, path))
        self.table.setRowCount(len(rows))
        for row, (status, path) in enumerate(rows):
            self.table.setItem(row, 0, QTableWidgetItem(status))
            self.table.setItem(row, 1, QTableWidgetItem(path))
