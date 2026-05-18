from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QListWidget, QListWidgetItem,
                             QFrame, QScrollArea, QGridLayout, QLineEdit,
                             QComboBox, QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor


class MenuItemButton(QPushButton):
    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self.item_data = item
        name  = item.get("item_name", "")
        price = item.get("selling_price", 0)
        self.setText(f"{name}\n{price:,.2f}")
        self.setFixedSize(120, 70)
        self.setStyleSheet("""
            QPushButton {
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 11px;
                color: #333;
                padding: 4px;
            }
            QPushButton:hover {
                background: #1a3c5e;
                color: white;
                border-color: #1a3c5e;
            }
        """)


class OrderPanel(QWidget):
    """Right-side panel: shows active order items + menu to add from."""
    order_saved   = pyqtSignal()
    bill_requested = pyqtSignal(str)   # emits order name

    def __init__(self, api, outlet, parent=None):
        super().__init__(parent)
        self.api       = api
        self.outlet    = outlet
        self._table    = None
        self._order    = None
        self._pending  = []    # [{menu_item, item_name, qty, rate}]
        self._menu_items = []
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Table header ──────────────────────────────────────────────────────
        self._hdr = QLabel("Select a table")
        self._hdr.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._hdr.setStyleSheet("background:#1a3c5e; color:white; padding:12px 16px;")
        root.addWidget(self._hdr)

        # ── Category filter + search ──────────────────────────────────────────
        cat_row = QHBoxLayout()
        cat_row.setContentsMargins(8, 6, 8, 6)
        self._cat_combo = QComboBox()
        self._cat_combo.setFixedHeight(28)
        self._cat_combo.addItem("All", None)
        self._cat_combo.currentIndexChanged.connect(self._load_menu)
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search menu…")
        self._search_edit.setFixedHeight(28)
        self._search_edit.textChanged.connect(self._filter_menu)
        cat_row.addWidget(self._cat_combo)
        cat_row.addWidget(self._search_edit)
        root.addLayout(cat_row)

        # ── Menu grid ─────────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(260)
        scroll.setStyleSheet("QScrollArea{border:none;}")
        self._menu_container = QWidget()
        self._menu_grid = QGridLayout(self._menu_container)
        self._menu_grid.setSpacing(6)
        self._menu_grid.setContentsMargins(8, 4, 8, 4)
        scroll.setWidget(self._menu_container)
        root.addWidget(scroll)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#ddd;")
        root.addWidget(sep)

        # ── Current order items ───────────────────────────────────────────────
        order_lbl = QLabel("Current Order")
        order_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        order_lbl.setStyleSheet("color:#1a3c5e; padding:8px 16px 4px;")
        root.addWidget(order_lbl)

        self._order_list = QListWidget()
        self._order_list.setStyleSheet("""
            QListWidget { border:none; font-size:12px; }
            QListWidget::item { padding:6px 12px; border-bottom:1px solid #f0f0f0; }
        """)
        root.addWidget(self._order_list)

        # ── Totals ────────────────────────────────────────────────────────────
        totals_frame = QFrame()
        totals_frame.setStyleSheet("background:#f4f6fa; border-top:1px solid #ddd;")
        tot_lay = QVBoxLayout(totals_frame)
        tot_lay.setContentsMargins(16, 8, 16, 8)

        tot_row = QHBoxLayout()
        self._total_lbl = QLabel("Total:  0.00")
        self._total_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._total_lbl.setStyleSheet("color:#1a3c5e;")
        tot_row.addWidget(self._total_lbl)
        tot_row.addStretch()
        tot_lay.addLayout(tot_row)

        # Buttons
        btn_row = QHBoxLayout()
        self._btn_send = QPushButton("Send to Kitchen")
        self._btn_send.setFixedHeight(40)
        self._btn_send.setEnabled(False)
        self._btn_send.setStyleSheet("""
            QPushButton { background:#1a3c5e; color:white; border-radius:7px;
                          font-size:13px; font-weight:bold; }
            QPushButton:hover { background:#2d6a9f; }
            QPushButton:disabled { background:#ccc; color:#888; }
        """)
        self._btn_send.clicked.connect(self._send_order)

        self._btn_bill = QPushButton("Generate Bill")
        self._btn_bill.setFixedHeight(40)
        self._btn_bill.setEnabled(False)
        self._btn_bill.setStyleSheet("""
            QPushButton { background:#c0392b; color:white; border-radius:7px;
                          font-size:13px; font-weight:bold; }
            QPushButton:hover { background:#e74c3c; }
            QPushButton:disabled { background:#ccc; color:#888; }
        """)
        self._btn_bill.clicked.connect(self._generate_bill)
        btn_row.addWidget(self._btn_send)
        btn_row.addWidget(self._btn_bill)
        tot_lay.addLayout(btn_row)
        root.addWidget(totals_frame)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_table(self, table: dict):
        self._table  = table
        self._order  = None
        self._pending = []
        num = table.get("table_number", table.get("name", ""))
        status = table.get("status", "")
        self._hdr.setText(f"Table {num}  ·  {status}")
        self._load_categories()
        self._load_menu()
        self._check_active_order()

    def _load_categories(self):
        self._cat_combo.blockSignals(True)
        self._cat_combo.clear()
        self._cat_combo.addItem("All", None)
        try:
            cats = self.api.restaurant.get_menu_categories(outlet=self.outlet)
            for c in cats:
                self._cat_combo.addItem(c, c)
        except Exception:
            pass
        self._cat_combo.blockSignals(False)

    def _load_menu(self):
        category = self._cat_combo.currentData()
        try:
            self._menu_items = self.api.restaurant.get_menu_items(
                outlet=self.outlet, category=category or ""
            )
        except Exception:
            self._menu_items = []
        self._render_menu(self._menu_items)

    def _filter_menu(self, text):
        q = text.lower()
        filtered = [i for i in self._menu_items
                    if q in (i.get("item_name") or "").lower()]
        self._render_menu(filtered)

    def _render_menu(self, items):
        while self._menu_grid.count():
            w = self._menu_grid.takeAt(0).widget()
            if w:
                w.deleteLater()
        COLS = 3
        for idx, item in enumerate(items):
            btn = MenuItemButton(item)
            btn.clicked.connect(lambda _, i=item: self._add_item(i))
            self._menu_grid.addWidget(btn, idx // COLS, idx % COLS)

    def _check_active_order(self):
        if not self._table:
            return
        try:
            order = self.api.restaurant.get_active_order(
                table=self._table["name"]
            )
            if order:
                self._order = order
                self._rebuild_order_list_from_order()
                self._btn_bill.setEnabled(True)
        except Exception:
            pass

    def _add_item(self, item: dict):
        if not self._table:
            return
        existing = next((p for p in self._pending
                         if p["menu_item"] == item["name"]), None)
        if existing:
            existing["qty"] += 1
        else:
            self._pending.append({
                "menu_item":  item["name"],
                "item_name":  item.get("item_name", ""),
                "qty":        1,
                "rate":       float(item.get("selling_price", 0)),
            })
        self._refresh_order_list()
        self._btn_send.setEnabled(True)

    def _refresh_order_list(self):
        self._order_list.clear()
        total = 0.0
        items = []
        if self._order:
            items += [(i["item_name"], i["qty"], i["rate"], i["status"])
                      for i in self._order.get("items", [])
                      if i.get("status") != "Void"]
        items += [(p["item_name"], p["qty"], p["rate"], "New")
                  for p in self._pending]
        for name, qty, rate, status in items:
            amount = qty * rate
            total += amount
            color = "#888" if status == "Void" else ("#1e7e5a" if status == "New" else "#333")
            lbl = f"{qty}×  {name}  —  {amount:,.2f}"
            item_w = QListWidgetItem(lbl)
            item_w.setForeground(QColor(color))
            self._order_list.addItem(item_w)
        self._total_lbl.setText(f"Total:  {total:,.2f}")

    def _rebuild_order_list_from_order(self):
        self._pending = []
        self._refresh_order_list()

    def _send_order(self):
        if not self._pending:
            return
        try:
            if self._order:
                self.api.restaurant.add_items_to_order(
                    order=self._order["name"],
                    items=self._pending,
                )
            else:
                result = self.api.restaurant.create_order(
                    table=self._table["name"],
                    outlet=self.outlet,
                    items=self._pending,
                )
                self._order = self.api.restaurant.get_order(order=result["name"])

            self._pending = []
            self._rebuild_order_list_from_order()
            self._btn_bill.setEnabled(True)
            self._btn_send.setEnabled(False)
            self.order_saved.emit()
        except Exception as e:
            QMessageBox.critical(self.window(), "Error", str(e))

    def _generate_bill(self):
        if not self._order:
            return
        try:
            result = self.api.restaurant.generate_bill(order=self._order["name"])
            invoice = result.get("pos_invoice", "")
            QMessageBox.information(
                self.window(), "Bill Generated",
                f"POS Invoice created: {invoice}"
            )
            self.bill_requested.emit(self._order["name"])
            self._order  = None
            self._pending = []
            self._order_list.clear()
            self._total_lbl.setText("Total:  0.00")
            self._btn_bill.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self.window(), "Error", str(e))
