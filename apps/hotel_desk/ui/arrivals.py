from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QHeaderView, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor


class ArrivalsWidget(QWidget):
    check_in_requested = pyqtSignal(dict)   # emits booking dict

    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self._bookings = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        title = QLabel("Today's Arrivals")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #1a3c5e;")
        root.addWidget(title)

        # Search bar
        bar = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search guest or booking…")
        self._search.setFixedHeight(34)
        self._search.textChanged.connect(self._filter)
        self._search.setStyleSheet("""
            QLineEdit { border:1px solid #ccc; border-radius:6px;
                        padding:0 10px; font-size:13px; }
        """)
        btn_ref = QPushButton("↻ Refresh")
        btn_ref.setFixedSize(100, 34)
        btn_ref.setStyleSheet("""
            QPushButton { background:#1a3c5e; color:white; border-radius:6px; font-size:12px; }
            QPushButton:hover { background:#2d6a9f; }
        """)
        btn_ref.clicked.connect(self.refresh)
        bar.addWidget(self._search)
        bar.addWidget(btn_ref)
        root.addLayout(bar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Booking", "Guest", "Room Type", "Room", "Adults", "Nights", "Action"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(6, 120)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet("""
            QTableWidget { border:1px solid #ddd; border-radius:6px; font-size:12px; }
            QHeaderView::section { background:#1a3c5e; color:white; padding:6px; font-size:12px; }
            QTableWidget::item:selected { background:#d0e8ff; color:#000; }
        """)
        root.addWidget(self._table)

        self._status = QLabel("")
        self._status.setStyleSheet("color: #888; font-size: 11px;")
        root.addWidget(self._status)

    def refresh(self):
        try:
            self._bookings = self.api.hotel.get_arrivals()
            self._populate(self._bookings)
            self._status.setText(f"{len(self._bookings)} arrival(s) today")
        except Exception as e:
            self._status.setText(f"Error: {e}")

    def _filter(self, text):
        q = text.lower()
        filtered = [b for b in self._bookings
                    if q in (b.get("booking_no") or "").lower()
                    or q in (b.get("guest") or "").lower()]
        self._populate(filtered)

    def _populate(self, bookings):
        self._table.setRowCount(0)
        for b in bookings:
            row = self._table.rowCount()
            self._table.insertRow(row)
            for col, val in enumerate([
                b.get("booking_no", b.get("name", "")),
                b.get("guest", ""),
                b.get("room_type", ""),
                b.get("room") or "—",
                str(b.get("num_adults", 1)),
                str(b.get("num_nights", "?")),
            ]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self._table.setItem(row, col, item)

            btn = QPushButton("Check In")
            btn.setStyleSheet("""
                QPushButton { background:#1e7e5a; color:white; border-radius:5px;
                              font-size:12px; padding:4px 8px; }
                QPushButton:hover { background:#25a06e; }
            """)
            btn.clicked.connect(lambda _, booking=b: self.check_in_requested.emit(booking))
            self._table.setCellWidget(row, 6, btn)
