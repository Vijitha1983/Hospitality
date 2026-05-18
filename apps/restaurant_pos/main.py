"""
Restaurant POS — PyQt6 Windows App
Run: python main.py  (from apps/restaurant_pos/)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QVBoxLayout, QLabel, QPushButton, QComboBox,
                             QFrame, QSplitter, QMessageBox, QInputDialog)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from shared.frappe_client import get_client, reset_client, APIError
from ui.table_grid import TableGridWidget
from ui.order_panel import OrderPanel


STYLE = """
QMainWindow { background: #f4f6fa; }
QSplitter::handle { background: #ddd; width: 2px; }
"""


class RestaurantPOSWindow(QMainWindow):
    def __init__(self, api, outlet):
        super().__init__()
        self.api    = api
        self.outlet = outlet
        self.setWindowTitle(f"Restaurant POS — {outlet}")
        self.resize(1280, 800)
        self.setStyleSheet(STYLE)
        self._build_ui()

        # Auto-refresh table grid every 30 s
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._table_grid.refresh)
        self._timer.start(30_000)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ───────────────────────────────────────────────────────────
        topbar = QFrame()
        topbar.setStyleSheet("background:#c8962e;")
        topbar.setFixedHeight(52)
        tb_lay = QHBoxLayout(topbar)
        tb_lay.setContentsMargins(16, 0, 16, 0)

        logo = QLabel("🍽  Restaurant POS")
        logo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        logo.setStyleSheet("color:white;")
        tb_lay.addWidget(logo)
        tb_lay.addStretch()

        self._pending_lbl = QLabel("")
        self._pending_lbl.setStyleSheet("color:white; font-size:12px;")
        tb_lay.addWidget(self._pending_lbl)

        btn_kots = QPushButton("Pending KOTs")
        btn_kots.setStyleSheet("""
            QPushButton { background:rgba(255,255,255,0.15); color:white;
                          border:1px solid rgba(255,255,255,0.3); border-radius:6px;
                          padding:4px 12px; font-size:12px; }
            QPushButton:hover { background:rgba(255,255,255,0.25); }
        """)
        btn_kots.clicked.connect(self._show_pending_kots)
        tb_lay.addWidget(btn_kots)

        btn_settings = QPushButton("⚙")
        btn_settings.setFixedSize(36, 36)
        btn_settings.setStyleSheet("""
            QPushButton { background:rgba(255,255,255,0.1); color:white;
                          border:1px solid rgba(255,255,255,0.2); border-radius:6px; }
            QPushButton:hover { background:rgba(255,255,255,0.2); }
        """)
        btn_settings.clicked.connect(self._open_settings)
        tb_lay.addWidget(btn_settings)

        root.addWidget(topbar)

        # ── Main splitter ─────────────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Table grid
        self._table_grid = TableGridWidget(api=self.api, outlet=self.outlet)
        self._table_grid.table_selected.connect(self._on_table_selected)
        splitter.addWidget(self._table_grid)

        # Right: Order panel
        self._order_panel = OrderPanel(api=self.api, outlet=self.outlet)
        self._order_panel.order_saved.connect(self._table_grid.refresh)
        self._order_panel.bill_requested.connect(lambda _: self._table_grid.refresh())
        splitter.addWidget(self._order_panel)

        splitter.setSizes([700, 500])
        root.addWidget(splitter)

        self._refresh_pending_kots()

    def _on_table_selected(self, table: dict):
        self._order_panel.set_table(table)

    def _refresh_pending_kots(self):
        try:
            kots = self.api.restaurant.get_pending_kots(outlet=self.outlet)
            count = len(kots) if kots else 0
            self._pending_lbl.setText(f"Pending KOTs: {count}" if count else "")
        except Exception:
            pass

    def _show_pending_kots(self):
        try:
            kots = self.api.restaurant.get_pending_kots(outlet=self.outlet)
            if not kots:
                QMessageBox.information(self, "KOTs", "No pending KOTs.")
                return
            lines = "\n".join(
                f"{k['name']}  |  Table {k.get('table','?')}  |  "
                f"{k.get('kitchen_station','')}  |  {k.get('status','')}"
                for k in kots
            )
            QMessageBox.information(self, f"Pending KOTs ({len(kots)})", lines)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _open_settings(self):
        url, ok = QInputDialog.getText(
            self, "Server URL", "ERPNext URL:", text=self.api.url)
        if ok and url:
            key, ok2 = QInputDialog.getText(
                self, "API Key", "API Key:", text=self.api.api_key)
            if ok2:
                secret, ok3 = QInputDialog.getText(
                    self, "API Secret", "API Secret:")
                if ok3:
                    reset_client(url=url, api_key=key, api_secret=secret)


def _choose_outlet(api) -> str | None:
    try:
        outlets = api.restaurant.get_outlets()
    except Exception as e:
        QMessageBox.critical(None, "Connection Error",
                             f"Cannot reach ERPNext:\n{e}\n\n"
                             "Check your config.py settings.")
        return None
    if not outlets:
        QMessageBox.warning(None, "No Outlets",
                            "No Restaurant outlets found in ERPNext.")
        return None
    if len(outlets) == 1:
        return outlets[0]["name"]
    names = [o["outlet_name"] or o["name"] for o in outlets]
    choice, ok = QInputDialog.getItem(
        None, "Select Outlet", "Restaurant Outlet:", names, 0, False)
    if not ok:
        return None
    return outlets[names.index(choice)]["name"]


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Restaurant POS")
    app.setFont(QFont("Segoe UI", 11))

    api = get_client()
    outlet = _choose_outlet(api)
    if not outlet:
        sys.exit(0)

    window = RestaurantPOSWindow(api, outlet)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
