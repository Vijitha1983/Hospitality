from PyQt6.QtWidgets import (QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QComboBox, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

STATUS_COLORS = {
    "Available": ("#1e7e5a", "#e8f8f0"),
    "Occupied":  ("#c0392b", "#fdecea"),
    "Reserved":  ("#8b5e1a", "#fef9ec"),
    "Cleaning":  ("#2d6a9f", "#e8f0fb"),
}


class TableButton(QPushButton):
    def __init__(self, table: dict, parent=None):
        super().__init__(parent)
        self.table_data = table
        status = table.get("status", "Available")
        border_color, bg_color = STATUS_COLORS.get(status, ("#555", "#f0f0f0"))

        number = table.get("table_number", table.get("name", ""))
        cap    = table.get("capacity", "?")

        self.setText(f"Table {number}\n{status}\n({cap} seats)")
        self.setFixedSize(130, 90)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg_color};
                border: 2px solid {border_color};
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
                color: {border_color};
                padding: 6px;
            }}
            QPushButton:hover {{
                background: {border_color};
                color: white;
            }}
        """)


class TableGridWidget(QWidget):
    table_selected = pyqtSignal(dict)

    def __init__(self, api, outlet, parent=None):
        super().__init__(parent)
        self.api     = api
        self.outlet  = outlet
        self._tables = []
        self._section_filter = None
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        # Section filter
        top = QHBoxLayout()
        lbl = QLabel("Section:")
        lbl.setStyleSheet("font-size:13px; color:#555;")
        self._section_combo = QComboBox()
        self._section_combo.setFixedHeight(30)
        self._section_combo.addItem("All Sections", None)
        self._section_combo.currentIndexChanged.connect(self._on_section_change)
        self._load_sections()

        btn_ref = QPushButton("↻")
        btn_ref.setFixedSize(30, 30)
        btn_ref.setStyleSheet("QPushButton{background:#eee;border-radius:5px;font-size:14px;}"
                               "QPushButton:hover{background:#ddd;}")
        btn_ref.clicked.connect(self.refresh)
        top.addWidget(lbl)
        top.addWidget(self._section_combo)
        top.addStretch()
        top.addWidget(btn_ref)
        root.addLayout(top)

        # Legend
        legend = QHBoxLayout()
        for status, (color, bg) in STATUS_COLORS.items():
            dot = QLabel(f"● {status}")
            dot.setStyleSheet(f"color:{color}; font-size:11px;")
            legend.addWidget(dot)
        legend.addStretch()
        root.addLayout(legend)

        # Grid
        self._grid_frame = QWidget()
        self._grid = QGridLayout(self._grid_frame)
        self._grid.setSpacing(10)
        root.addWidget(self._grid_frame)
        root.addStretch()

    def _load_sections(self):
        try:
            sections = self.api.restaurant.get_table_sections(outlet=self.outlet)
            for s in sections:
                self._section_combo.addItem(s["section_name"], s["name"])
        except Exception:
            pass

    def _on_section_change(self):
        self._section_filter = self._section_combo.currentData()
        self._render_tables()

    def refresh(self):
        try:
            self._tables = self.api.restaurant.get_tables(outlet=self.outlet)
        except Exception as e:
            print(f"Table grid refresh error: {e}")
        self._render_tables()

    def _render_tables(self):
        # Clear grid
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tables = self._tables
        if self._section_filter:
            tables = [t for t in tables if t.get("section") == self._section_filter]

        COLS = 5
        for idx, table in enumerate(tables):
            btn = TableButton(table)
            btn.clicked.connect(lambda _, t=table: self.table_selected.emit(t))
            self._grid.addWidget(btn, idx // COLS, idx % COLS)
