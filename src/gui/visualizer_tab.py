"""Visualizer tab — Huffman codes, top tokens, sample LZ77 matches."""

from __future__ import annotations

from typing import Dict, List, Optional

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


class VisualizerTab(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel("Algorithm visualizer")
        title.setObjectName("title")
        sub = QLabel(
            "Inspect the data structures behind a representative text file: "
            "frequency table, Huffman code book, and sample LZ77 matches."
        )
        sub.setObjectName("subtitle")
        sub.setWordWrap(True)
        self.source_label = QLabel("Source file: (run a compression first)")
        self.source_label.setObjectName("subtitle")
        root.addWidget(title)
        root.addWidget(sub)
        root.addWidget(self.source_label)

        body = QHBoxLayout()
        body.setSpacing(12)
        root.addLayout(body, stretch=1)

        # Top tokens
        left = QVBoxLayout()
        left.addWidget(QLabel("Top tokens (frequency)"))
        self.token_table = QTableWidget(0, 2)
        self.token_table.setHorizontalHeaderLabels(["Token", "Frequency"])
        self.token_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.token_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.token_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.token_table.setAlternatingRowColors(True)
        left.addWidget(self.token_table)
        body.addLayout(left, stretch=1)

        # Huffman codes
        mid = QVBoxLayout()
        mid.addWidget(QLabel("Huffman code book (preview)"))
        self.code_table = QTableWidget(0, 2)
        self.code_table.setHorizontalHeaderLabels(["Token", "Code"])
        self.code_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.code_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.code_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.code_table.setAlternatingRowColors(True)
        mid.addWidget(self.code_table)
        body.addLayout(mid, stretch=1)

        # LZ77 matches
        right = QVBoxLayout()
        right.addWidget(QLabel("Sample LZ77 matches"))
        self.match_table = QTableWidget(0, 3)
        self.match_table.setHorizontalHeaderLabels(["Offset", "Length", "Next byte"])
        for i in range(3):
            self.match_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        self.match_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.match_table.setAlternatingRowColors(True)
        right.addWidget(self.match_table)
        body.addLayout(right, stretch=1)

    # -----------------------------------------------------------------
    def update_with_result(self, result: CompressionResult) -> None:
        viz = result.text_visualizer_data
        if not viz:
            self.source_label.setText("Source file: (no text file in last run)")
            self.token_table.setRowCount(0)
            self.code_table.setRowCount(0)
            self.match_table.setRowCount(0)
            return
        self.source_label.setText(
            f"Source file: {viz.get('source_file', '?')} — "
            f"{viz.get('token_count', 0)} tokens, "
            f"{viz.get('unique_symbols', 0)} unique symbols"
        )
        tops: List = viz.get("top_tokens", [])
        self.token_table.setRowCount(len(tops))
        for row, (label, freq) in enumerate(tops):
            self.token_table.setItem(row, 0, QTableWidgetItem(str(label)))
            self.token_table.setItem(row, 1, QTableWidgetItem(str(freq)))

        codes: Dict = viz.get("huffman_codes", {})
        self.code_table.setRowCount(len(codes))
        for row, (label, code) in enumerate(codes.items()):
            self.code_table.setItem(row, 0, QTableWidgetItem(str(label)))
            self.code_table.setItem(row, 1, QTableWidgetItem(str(code)))

        matches: List = viz.get("sample_matches", [])
        self.match_table.setRowCount(len(matches))
        for row, (offset, length, next_byte) in enumerate(matches):
            self.match_table.setItem(row, 0, QTableWidgetItem(str(offset)))
            self.match_table.setItem(row, 1, QTableWidgetItem(str(length)))
            human = chr(next_byte) if 32 <= next_byte < 127 else f"0x{next_byte:02x}"
            self.match_table.setItem(row, 2, QTableWidgetItem(f"{next_byte} ({human})"))
