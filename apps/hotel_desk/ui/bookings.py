from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QMessageBox,
    QDialog, QFormLayout, QDateEdit, QSpinBox, QTextEdit, QListWidget,
    QListWidgetItem, QFrame, QSplitter, QSizePolicy,
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor

# ── Shared styles ─────────────────────────────────────────────────────────────

_BTN_PRIMARY = """
    QPushButton { background:#1a3c5e; color:white; border-radius:6px;
                  padding:0 16px; font-size:13px; }
    QPushButton:hover { background:#2d6a9f; }
    QPushButton:disabled { background:#ccc; color:#888; }
"""
_BTN_SUCCESS = """
    QPushButton { background:#1e7e5a; color:white; border-radius:6px;
                  padding:0 16px; font-size:13px; font-weight:bold; }
    QPushButton:hover { background:#25a06e; }
    QPushButton:disabled { background:#ccc; color:#888; }
"""
_BTN_NEUTRAL = """
    QPushButton { background:#eee; border-radius:6px;
                  padding:0 14px; font-size:13px; }
    QPushButton:hover { background:#ddd; }
"""
_INPUT = "border:1px solid #ccc; border-radius:6px; padding:0 10px; font-size:13px;"
_TABLE = """
    QTableWidget { border:1px solid #ddd; border-radius:6px; font-size:12px; }
    QHeaderView::section { background:#1a3c5e; color:white; padding:6px;
                           font-size:12px; border:none; }
    QTableWidget::item:selected { background:#d0e8ff; color:#000; }
    QTableWidget::item:alternate { background:#f8fafc; }
"""

STATUS_COLORS = {
    "Confirmed":  "#1e7e5a",
    "Checked In": "#2d6a9f",
    "Checked Out":"#888",
    "Cancelled":  "#c0392b",
    "No Show":    "#c0392b",
}


# ── New Booking Dialog ────────────────────────────────────────────────────────

class NewBookingDialog(QDialog):
    booking_created = pyqtSignal(dict)

    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self._selected_guest = None
        self._guests_found   = []
        self._room_types     = []
        self._rate_plans     = []
        self.setWindowTitle("New Booking")
        self.setMinimumSize(620, 680)
        self.setModal(True)
        self._build_ui()
        self._load_lookups()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        title = QLabel("New Booking")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color:#1a3c5e;")
        root.addWidget(title)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#ddd;")
        root.addWidget(sep)

        # ── Guest section ─────────────────────────────────────────────────────
        guest_grp = self._group("Guest")
        g_lay = QVBoxLayout(guest_grp)

        search_row = QHBoxLayout()
        self._guest_search = QLineEdit()
        self._guest_search.setPlaceholderText("Search by name or phone…")
        self._guest_search.setFixedHeight(32)
        self._guest_search.setStyleSheet(_INPUT)
        btn_search = QPushButton("Search")
        btn_search.setFixedHeight(32)
        btn_search.setStyleSheet(_BTN_PRIMARY)
        btn_search.clicked.connect(self._search_guests)
        self._guest_search.returnPressed.connect(self._search_guests)
        search_row.addWidget(self._guest_search)
        search_row.addWidget(btn_search)
        g_lay.addLayout(search_row)

        self._guest_list = QListWidget()
        self._guest_list.setFixedHeight(90)
        self._guest_list.setStyleSheet("font-size:12px; border:1px solid #ddd; border-radius:5px;")
        self._guest_list.itemClicked.connect(self._on_guest_selected)
        g_lay.addWidget(self._guest_list)

        self._guest_lbl = QLabel("No guest selected")
        self._guest_lbl.setStyleSheet("color:#888; font-size:12px; font-style:italic;")
        g_lay.addWidget(self._guest_lbl)

        root.addWidget(guest_grp)

        # ── Booking details ───────────────────────────────────────────────────
        det_grp = self._group("Booking Details")
        form = QFormLayout(det_grp)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(10)

        self._room_type_combo = QComboBox()
        self._room_type_combo.setFixedHeight(32)
        form.addRow("Room Type *", self._room_type_combo)

        today = QDate.currentDate()
        self._checkin = QDateEdit(today)
        self._checkin.setCalendarPopup(True)
        self._checkin.setDisplayFormat("yyyy-MM-dd")
        self._checkin.setFixedHeight(32)
        self._checkin.dateChanged.connect(self._on_date_changed)
        form.addRow("Check-in *", self._checkin)

        self._checkout = QDateEdit(today.addDays(1))
        self._checkout.setCalendarPopup(True)
        self._checkout.setDisplayFormat("yyyy-MM-dd")
        self._checkout.setFixedHeight(32)
        self._checkout.dateChanged.connect(self._on_date_changed)
        form.addRow("Check-out *", self._checkout)

        self._nights_lbl = QLabel("1 night")
        self._nights_lbl.setStyleSheet("color:#1a3c5e; font-weight:bold; font-size:12px;")
        form.addRow("", self._nights_lbl)

        self._rate_plan_combo = QComboBox()
        self._rate_plan_combo.setFixedHeight(32)
        form.addRow("Rate Plan", self._rate_plan_combo)

        adults_row = QHBoxLayout()
        self._adults = QSpinBox(); self._adults.setRange(1, 10); self._adults.setValue(1)
        self._adults.setFixedHeight(32)
        self._children = QSpinBox(); self._children.setRange(0, 10); self._children.setValue(0)
        self._children.setFixedHeight(32)
        adults_row.addWidget(self._adults)
        adults_row.addWidget(QLabel("Children:"))
        adults_row.addWidget(self._children)
        adults_row.addStretch()
        form.addRow("Adults *", adults_row)

        self._notes = QTextEdit()
        self._notes.setPlaceholderText("Special requests or notes…")
        self._notes.setFixedHeight(60)
        self._notes.setStyleSheet("border:1px solid #ccc; border-radius:6px; padding:4px; font-size:12px;")
        form.addRow("Notes", self._notes)

        root.addWidget(det_grp)

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(38)
        btn_cancel.setFixedWidth(100)
        btn_cancel.setStyleSheet(_BTN_NEUTRAL)
        btn_cancel.clicked.connect(self.reject)

        self._btn_confirm = QPushButton("Confirm Booking")
        self._btn_confirm.setFixedHeight(38)
        self._btn_confirm.setFixedWidth(160)
        self._btn_confirm.setStyleSheet(_BTN_SUCCESS)
        self._btn_confirm.clicked.connect(self._confirm)

        btn_bar.addWidget(btn_cancel)
        btn_bar.addWidget(self._btn_confirm)
        root.addLayout(btn_bar)

    def _group(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame { border:1px solid #e0e0e0; border-radius:8px; }
            QLabel { border:none; }
        """)
        lay = QVBoxLayout(frame)
        lbl = QLabel(title)
        lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl.setStyleSheet("color:#1a3c5e; border:none; padding-bottom:4px;")
        lay.insertWidget(0, lbl)
        return frame

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _load_lookups(self):
        try:
            self._room_types = self.api.hotel.get_room_types()
            self._room_type_combo.clear()
            self._room_type_combo.addItem("— Select room type —", None)
            for rt in self._room_types:
                label = rt.get("type_name") or rt.get("name", "")
                self._room_type_combo.addItem(label, rt["name"])
        except Exception as e:
            self._room_type_combo.addItem(f"Error: {e}", None)

        try:
            self._rate_plans = self.api.hotel.get_rate_plans()
            self._rate_plan_combo.clear()
            self._rate_plan_combo.addItem("— Default rate —", None)
            for rp in self._rate_plans:
                self._rate_plan_combo.addItem(rp.get("plan_name") or rp["name"], rp["name"])
        except Exception:
            pass

    def _search_guests(self):
        q = self._guest_search.text().strip()
        if not q:
            return
        try:
            self._guests_found = self.api.hotel.search_guests(query=q)
            self._guest_list.clear()
            if not self._guests_found:
                self._guest_list.addItem("No guests found.")
                return
            for g in self._guests_found:
                label = f"{g['guest_name']}  |  {g.get('mobile_no','')}"
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, g)
                self._guest_list.addItem(item)
        except Exception as e:
            QMessageBox.warning(self, "Search Error", str(e))

    def _on_guest_selected(self, item: QListWidgetItem):
        g = item.data(Qt.ItemDataRole.UserRole)
        if g:
            self._selected_guest = g
            self._guest_lbl.setText(
                f"Selected: {g['guest_name']}  |  {g.get('mobile_no','')}  |  {g.get('email','')}"
            )
            self._guest_lbl.setStyleSheet("color:#1e7e5a; font-size:12px; font-weight:bold;")

    def _on_date_changed(self):
        ci = self._checkin.date()
        co = self._checkout.date()
        if co <= ci:
            self._checkout.setDate(ci.addDays(1))
        nights = ci.daysTo(self._checkout.date())
        self._nights_lbl.setText(f"{nights} night{'s' if nights != 1 else ''}")

    def _confirm(self):
        if not self._selected_guest:
            QMessageBox.warning(self, "Guest Required", "Please search and select a guest.")
            return
        if not self._room_type_combo.currentData():
            QMessageBox.warning(self, "Room Type Required", "Please select a room type.")
            return

        ci = self._checkin.date().toString("yyyy-MM-dd")
        co = self._checkout.date().toString("yyyy-MM-dd")
        if ci >= co:
            QMessageBox.warning(self, "Invalid Dates",
                                "Check-out must be after check-in.")
            return

        self._btn_confirm.setEnabled(False)
        self._btn_confirm.setText("Creating…")
        try:
            result = self.api.hotel.create_booking(
                guest=self._selected_guest["name"],
                room_type=self._room_type_combo.currentData(),
                check_in_date=ci,
                check_out_date=co,
                num_adults=self._adults.value(),
                num_children=self._children.value(),
                rate_plan=self._rate_plan_combo.currentData() or "",
                special_requests=self._notes.toPlainText().strip(),
            )
            QMessageBox.information(
                self, "Booking Confirmed",
                f"Booking created successfully!\n\n"
                f"Booking No: {result.get('booking_no', result.get('name', ''))}\n"
                f"Status: {result.get('status', 'Confirmed')}"
            )
            self.booking_created.emit(result)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Booking Failed", str(e))
        finally:
            self._btn_confirm.setEnabled(True)
            self._btn_confirm.setText("Confirm Booking")


# ── Bookings Widget (main page) ───────────────────────────────────────────────

class BookingsWidget(QWidget):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self._bookings = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # ── Header row ────────────────────────────────────────────────────────
        hdr_row = QHBoxLayout()
        title = QLabel("Bookings")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color:#1a3c5e;")
        hdr_row.addWidget(title)
        hdr_row.addStretch()

        btn_new = QPushButton("＋  New Booking")
        btn_new.setFixedHeight(36)
        btn_new.setStyleSheet(_BTN_SUCCESS)
        btn_new.clicked.connect(self._open_new_booking)
        hdr_row.addWidget(btn_new)
        root.addLayout(hdr_row)

        # ── Filter row ────────────────────────────────────────────────────────
        filter_row = QHBoxLayout()

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search guest, booking no…")
        self._search.setFixedHeight(34)
        self._search.setStyleSheet(_INPUT)
        self._search.textChanged.connect(self._filter)

        self._status_combo = QComboBox()
        self._status_combo.setFixedHeight(34)
        self._status_combo.setFixedWidth(160)
        self._status_combo.addItems(["All Statuses", "Confirmed", "Checked In",
                                     "Checked Out", "Cancelled"])
        self._status_combo.currentIndexChanged.connect(self._apply_filters)

        btn_refresh = QPushButton("↻ Refresh")
        btn_refresh.setFixedHeight(34)
        btn_refresh.setFixedWidth(100)
        btn_refresh.setStyleSheet(_BTN_PRIMARY)
        btn_refresh.clicked.connect(self.refresh)

        filter_row.addWidget(self._search)
        filter_row.addWidget(self._status_combo)
        filter_row.addWidget(btn_refresh)
        root.addLayout(filter_row)

        # ── Table ─────────────────────────────────────────────────────────────
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "Booking No", "Guest", "Room Type", "Room",
            "Check-in", "Check-out", "Nights", "Status"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet(_TABLE)
        self._table.setSortingEnabled(True)
        root.addWidget(self._table)

        # ── Status bar ────────────────────────────────────────────────────────
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet("color:#888; font-size:11px;")
        root.addWidget(self._status_lbl)

    # ── Data ──────────────────────────────────────────────────────────────────

    def refresh(self):
        status = self._status_combo.currentText()
        status = None if status == "All Statuses" else status
        query  = self._search.text().strip()
        try:
            self._bookings = self.api.hotel.search_bookings(
                query=query, status=status
            )
            self._populate(self._bookings)
            self._status_lbl.setText(f"{len(self._bookings)} booking(s) found")
        except Exception as e:
            self._status_lbl.setText(f"Error: {e}")

    def _filter(self, text):
        self._apply_filters()

    def _apply_filters(self):
        q      = self._search.text().lower()
        status = self._status_combo.currentText()
        rows   = self._bookings
        if q:
            rows = [b for b in rows
                    if q in (b.get("booking_no") or "").lower()
                    or q in (b.get("guest") or "").lower()]
        if status != "All Statuses":
            rows = [b for b in rows if b.get("status") == status]
        self._populate(rows)

    def _populate(self, bookings):
        from datetime import date as _date
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)
        for b in bookings:
            row = self._table.rowCount()
            self._table.insertRow(row)

            ci = b.get("check_in_date", "")
            co = b.get("check_out_date", "")
            try:
                nights = (_date.fromisoformat(co) - _date.fromisoformat(ci)).days
                nights_str = str(nights)
            except Exception:
                nights_str = "—"

            values = [
                b.get("booking_no") or b.get("name", ""),
                b.get("guest", ""),
                b.get("room_type", ""),
                b.get("room") or "—",
                ci, co,
                nights_str,
                b.get("status", ""),
            ]
            status = b.get("status", "")
            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                if col == 7 and status in STATUS_COLORS:
                    item.setForeground(QColor(STATUS_COLORS[status]))
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self._table.setItem(row, col, item)

        self._table.setSortingEnabled(True)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _open_new_booking(self):
        dlg = NewBookingDialog(self.api, parent=self)
        dlg.booking_created.connect(lambda _: self.refresh())
        dlg.exec()
