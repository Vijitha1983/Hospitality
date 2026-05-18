from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QComboBox, QPushButton,
                             QCheckBox, QMessageBox, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class CheckInDialog(QDialog):
    def __init__(self, api, booking: dict, parent=None):
        super().__init__(parent)
        self.api     = api
        self.booking = booking
        self.result_data = None
        self.setWindowTitle(f"Check-in — {booking.get('booking_no', booking.get('name'))}")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()
        self._load_rooms()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(24, 20, 24, 20)

        # Header
        hdr = QLabel(f"Check-in: {self.booking.get('guest', '')}")
        hdr.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        hdr.setStyleSheet("color: #1a3c5e;")
        root.addWidget(hdr)

        # Summary strip
        info = QFrame()
        info.setStyleSheet("background:#f0f4f8; border-radius:8px; padding:8px;")
        info_layout = QHBoxLayout(info)
        for label, key in [("Room Type", "room_type"), ("Check-in", "check_in_date"),
                            ("Check-out", "check_out_date"), ("Nights", "num_nights")]:
            col = QVBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size:10px; color:#888;")
            val = QLabel(str(self.booking.get(key, "—")))
            val.setStyleSheet("font-size:13px; font-weight:bold; color:#1a3c5e;")
            col.addWidget(lbl)
            col.addWidget(val)
            info_layout.addLayout(col)
        root.addWidget(info)

        # Form
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(10)

        self._room_combo = QComboBox()
        self._room_combo.setFixedHeight(32)
        self._room_combo.setStyleSheet("font-size:13px;")
        form.addRow("Assign Room *", self._room_combo)

        self._adults = QLineEdit(str(self.booking.get("num_adults", 1)))
        self._adults.setFixedHeight(32)
        form.addRow("Adults", self._adults)

        self._children = QLineEdit(str(self.booking.get("num_children", 0)))
        self._children.setFixedHeight(32)
        form.addRow("Children", self._children)

        self._id_verified = QCheckBox("ID / Passport verified")
        self._id_verified.setChecked(True)
        form.addRow("", self._id_verified)

        self._advance = QLineEdit("0")
        self._advance.setFixedHeight(32)
        self._advance.setPlaceholderText("Amount collected at check-in")
        form.addRow("Advance Collected", self._advance)

        root.addLayout(form)

        # Buttons
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        cancel = QPushButton("Cancel")
        cancel.setFixedHeight(36)
        cancel.setFixedWidth(100)
        cancel.setStyleSheet("""
            QPushButton { background:#eee; border-radius:6px; font-size:13px; }
            QPushButton:hover { background:#ddd; }
        """)
        cancel.clicked.connect(self.reject)

        confirm = QPushButton("Confirm Check-in")
        confirm.setFixedHeight(36)
        confirm.setFixedWidth(160)
        confirm.setStyleSheet("""
            QPushButton { background:#1e7e5a; color:white; border-radius:6px;
                          font-size:13px; font-weight:bold; }
            QPushButton:hover { background:#25a06e; }
        """)
        confirm.clicked.connect(self._do_check_in)

        btn_bar.addWidget(cancel)
        btn_bar.addWidget(confirm)
        root.addLayout(btn_bar)

    def _load_rooms(self):
        self._room_combo.clear()
        self._room_combo.addItem("— Select Room —", None)
        try:
            rooms = self.api.hotel.get_available_rooms(
                check_in_date=self.booking.get("check_in_date"),
                check_out_date=self.booking.get("check_out_date"),
                room_type=self.booking.get("room_type"),
            )
            for r in rooms:
                label = f"{r['room_number']} — {r['room_type']}  (Floor {r.get('floor', '?')})"
                self._room_combo.addItem(label, r["name"])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load rooms:\n{e}")

    def _do_check_in(self):
        room = self._room_combo.currentData()
        if not room:
            QMessageBox.warning(self, "Room Required", "Please select a room.")
            return
        try:
            result = self.api.hotel.perform_check_in(
                booking=self.booking.get("name"),
                room=room,
                num_adults=int(self._adults.text() or 1),
                num_children=int(self._children.text() or 0),
                id_verified=int(self._id_verified.isChecked()),
                advance_collected=float(self._advance.text() or 0),
            )
            self.result_data = result
            QMessageBox.information(
                self, "Check-in Complete",
                f"Guest checked in successfully.\n"
                f"Check-in: {result['check_in']}\n"
                f"Folio: {result['folio']}"
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Check-in Failed", str(e))
