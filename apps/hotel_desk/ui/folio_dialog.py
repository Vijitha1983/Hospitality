from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QComboBox, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QFrame, QSplitter)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor


class FolioDialog(QDialog):
    def __init__(self, api, folio_name: str, parent=None):
        super().__init__(parent)
        self.api        = api
        self.folio_name = folio_name
        self.setWindowTitle(f"Guest Folio — {folio_name}")
        self.setMinimumSize(760, 560)
        self.setModal(True)
        self._charge_types = []
        self._build_ui()
        self._load_charge_types()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        hdr = QLabel(f"Folio: {self.folio_name}")
        hdr.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        hdr.setStyleSheet("color: #1a3c5e;")
        root.addWidget(hdr)

        # Summary strip
        self._summary = QFrame()
        self._summary.setStyleSheet("background:#f0f4f8; border-radius:8px;")
        sum_lay = QHBoxLayout(self._summary)
        self._lbl_guest   = self._info_col(sum_lay, "Guest", "—")
        self._lbl_room    = self._info_col(sum_lay, "Room", "—")
        self._lbl_balance = self._info_col(sum_lay, "Balance Due", "—")
        self._lbl_status  = self._info_col(sum_lay, "Status", "—")
        root.addWidget(self._summary)

        # Postings table
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Date", "Description", "Type", "Amount"])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet("""
            QTableWidget { border:1px solid #ddd; border-radius:6px; font-size:12px; }
            QHeaderView::section { background:#1a3c5e; color:white; padding:6px; }
        """)
        root.addWidget(self._table)

        # Add charge section
        charge_frame = QFrame()
        charge_frame.setStyleSheet("background:#f9fafb; border-radius:8px; border:1px solid #ddd;")
        cf_lay = QVBoxLayout(charge_frame)
        cf_title = QLabel("Post Charge")
        cf_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        cf_title.setStyleSheet("color:#1a3c5e;")
        cf_lay.addWidget(cf_title)

        form = QHBoxLayout()
        self._ct_combo = QComboBox()
        self._ct_combo.setFixedHeight(30)
        self._ct_combo.setMinimumWidth(200)

        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("Description")
        self._desc_edit.setFixedHeight(30)

        self._rate_edit = QLineEdit()
        self._rate_edit.setPlaceholderText("Amount")
        self._rate_edit.setFixedWidth(100)
        self._rate_edit.setFixedHeight(30)

        btn_post = QPushButton("Post")
        btn_post.setFixedSize(80, 30)
        btn_post.setStyleSheet("""
            QPushButton { background:#c0392b; color:white; border-radius:5px; font-weight:bold; }
            QPushButton:hover { background:#e74c3c; }
        """)
        btn_post.clicked.connect(self._post_charge)

        for w in [self._ct_combo, self._desc_edit, self._rate_edit, btn_post]:
            form.addWidget(w)
        cf_lay.addLayout(form)
        root.addWidget(charge_frame)

        # Bottom buttons
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()
        btn_refresh = QPushButton("↻ Refresh")
        btn_refresh.clicked.connect(self.refresh)
        btn_refresh.setFixedSize(100, 32)
        btn_refresh.setStyleSheet("QPushButton{background:#eee;border-radius:5px;font-size:12px;}"
                                   "QPushButton:hover{background:#ddd;}")
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_close.setFixedSize(80, 32)
        btn_close.setStyleSheet("QPushButton{background:#1a3c5e;color:white;border-radius:5px;}"
                                 "QPushButton:hover{background:#2d6a9f;}")
        btn_bar.addWidget(btn_refresh)
        btn_bar.addWidget(btn_close)
        root.addLayout(btn_bar)

    def _info_col(self, parent_layout, label, default):
        col = QVBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet("font-size:10px; color:#888;")
        val = QLabel(default)
        val.setStyleSheet("font-size:13px; font-weight:bold; color:#1a3c5e;")
        col.addWidget(lbl)
        col.addWidget(val)
        col.setContentsMargins(10, 8, 10, 8)
        parent_layout.addLayout(col)
        return val

    def _load_charge_types(self):
        try:
            types = self.api.hotel.get_charge_types()
            self._charge_types = types
            self._ct_combo.clear()
            for ct in types:
                self._ct_combo.addItem(ct["charge_name"], ct["name"])
        except Exception:
            pass

    def refresh(self):
        try:
            folio = self.api.hotel.get_folio(folio=self.folio_name)
            self._lbl_guest.setText(folio.get("guest_name") or folio.get("guest", ""))
            self._lbl_room.setText(folio.get("room") or "—")
            self._lbl_balance.setText(f"{folio.get('balance_due', 0):,.2f}")
            self._lbl_status.setText(folio.get("status", ""))
            self._populate_postings(folio.get("postings", []))
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _populate_postings(self, postings):
        self._table.setRowCount(0)
        for p in postings:
            row = self._table.rowCount()
            self._table.insertRow(row)
            is_payment = p.get("posting_type") == "Payment"
            for col, val in enumerate([
                p.get("posting_date", ""),
                p.get("description", ""),
                p.get("posting_type", ""),
                f"{p.get('amount', 0):,.2f}",
            ]):
                item = QTableWidgetItem(str(val))
                if is_payment:
                    item.setForeground(QColor("#1e7e5a"))
                self._table.setItem(row, col, item)

    def _post_charge(self):
        ct = self._ct_combo.currentData()
        desc = self._desc_edit.text().strip()
        try:
            rate = float(self._rate_edit.text() or 0)
        except ValueError:
            QMessageBox.warning(self, "Invalid", "Amount must be a number.")
            return
        if not ct or not desc or rate <= 0:
            QMessageBox.warning(self, "Incomplete", "Fill in all fields with a positive amount.")
            return
        try:
            self.api.hotel.post_folio_charge(
                folio=self.folio_name, charge_type=ct,
                description=desc, rate=rate,
            )
            self._desc_edit.clear()
            self._rate_edit.clear()
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
