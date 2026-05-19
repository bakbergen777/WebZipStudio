"""Modernised stylesheet — bigger touch targets, layered surfaces, soft shadows."""

STYLESHEET = """
QMainWindow, QWidget {
    background: #F4F6FB;
    color: #0F172A;
    font-family: "SF Pro Text", "Helvetica Neue", "Segoe UI", "Inter", "Arial";
    font-size: 13px;
}

/* ---- Tabs ---- */
QTabWidget::pane {
    border: 1px solid #E2E8F0;
    background: #FFFFFF;
    border-radius: 12px;
    margin-top: 6px;
}
QTabBar::tab {
    background: transparent;
    padding: 10px 18px;
    margin-right: 6px;
    color: #475569;
    border: none;
    border-bottom: 2px solid transparent;
}
QTabBar::tab:hover { color: #1E40AF; }
QTabBar::tab:selected {
    color: #2563EB;
    border-bottom: 3px solid #2563EB;
    font-weight: 700;
}

/* ---- Buttons (default = primary action) ---- */
QPushButton {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    padding: 9px 18px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 13px;
    min-height: 18px;
}
QPushButton:hover { background-color: #1D4ED8; }
QPushButton:pressed { background-color: #1E40AF; }
QPushButton:disabled { background-color: #94A3B8; color: #E2E8F0; }

/* Secondary — subtle, used for utility actions */
QPushButton#secondary {
    background-color: #FFFFFF;
    color: #1E293B;
    border: 1px solid #CBD5E1;
}
QPushButton#secondary:hover {
    background-color: #F1F5F9;
    border-color: #94A3B8;
    color: #0F172A;
}
QPushButton#secondary:pressed { background-color: #E2E8F0; }

/* Success — green, used for the main "Compress now" button */
QPushButton#success {
    background-color: #10B981;
    color: #FFFFFF;
    border: none;
    padding: 14px 28px;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.3px;
}
QPushButton#success:hover { background-color: #059669; }
QPushButton#success:pressed { background-color: #047857; }
QPushButton#success:disabled { background-color: #A7F3D0; color: #FFFFFF; }

/* Danger — red, used for destructive actions */
QPushButton#danger {
    background-color: #EF4444;
    color: #FFFFFF;
}
QPushButton#danger:hover { background-color: #DC2626; }

/* ---- Inputs ---- */
QLineEdit, QComboBox {
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 8px 10px;
    background: #FFFFFF;
    selection-background-color: #BFDBFE;
}
QLineEdit:focus, QComboBox:focus {
    border-color: #2563EB;
    background: #FFFFFF;
}
QComboBox::drop-down { border: none; width: 22px; }

QCheckBox { spacing: 8px; padding: 4px 0; }
QCheckBox::indicator {
    width: 18px; height: 18px;
    border: 1px solid #94A3B8;
    border-radius: 4px;
    background: #FFFFFF;
}
QCheckBox::indicator:hover { border-color: #2563EB; }
QCheckBox::indicator:checked {
    background: #2563EB;
    border-color: #2563EB;
    image: none;
}

/* ---- Tables ---- */
QHeaderView::section {
    background: #F8FAFC;
    border: none;
    border-right: 1px solid #E2E8F0;
    border-bottom: 1px solid #E2E8F0;
    padding: 8px;
    font-weight: 700;
    color: #1E293B;
}
QTableWidget {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    gridline-color: #E2E8F0;
    alternate-background-color: #F8FAFC;
    selection-background-color: #DBEAFE;
    selection-color: #0F172A;
}
QTableWidget::item { padding: 6px; }
QTableWidget::item:selected { background: #DBEAFE; color: #0F172A; }

/* ---- Progress + status ---- */
QProgressBar {
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    background: #F1F5F9;
    height: 22px;
    text-align: center;
    font-weight: 600;
    color: #1E293B;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #3B82F6, stop:1 #2563EB);
    border-radius: 7px;
}

QStatusBar { background: #FFFFFF; border-top: 1px solid #E2E8F0; }

/* ---- Typography helpers ---- */
QLabel#title { font-size: 20px; font-weight: 800; color: #0F172A; }
QLabel#subtitle { color: #64748B; }
QLabel#step {
    color: #2563EB;
    font-weight: 700;
    font-size: 13px;
    padding: 6px 0 2px 0;
    text-transform: uppercase;
    letter-spacing: 1px;
}
QFrame#card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
}
QLabel#stat_value { font-size: 24px; font-weight: 800; color: #2563EB; }
QLabel#stat_label { color: #64748B; font-size: 12px; }
"""
