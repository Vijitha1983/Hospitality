"""
Restaurant POS — PyQt6 Windows App
Run: python main.py  (from apps/restaurant_pos/)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QVBoxLayout, QLabel, QPushButton, QFrame,
                             QSplitter, QMessageBox, QInputDialog)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from shared.frappe_client import set_client, clear_credentials
from shared.login_window import LoginWindow
from ui.table_grid import TableGridWidget
from ui.order_panel import OrderPanel


STYLE = """
QMainWindow { background: #f4f6fa; }
QSplitter::handle { background: #ddd; width: 2px; }
"""


class RestaurantPOSWindow(QMainWindow):
    def __init__(self, api, outlet: str):
        super().__init__()
        self.api    = api
        self.outlet = outlet
        self.setWindowTitle(f"Restaurant POS — {outlet}")
        self.resize(1280, 800)
        self.setStyleSheet(STYLE)
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._table_grid.refresh)
        self._timer.start(30_000)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_topbar())
        root.addWidget(self._build_body())

    def _build_topbar(self) -> QFrame:
        bar = QFrame()
        bar.setStyleSheet("background:#c8962e;")
        bar.setFixedHeight(52)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 0, 16, 0)

        logo = QLabel("🍽  Restaurant POS")
        logo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        logo.setStyleSheet("color:white;")
        lay.addWidget(logo)
        lay.addStretch()

        # Logged-in user
        user = self.api.get_logged_user()
        user_lbl = QLabel(f"👤 {user}")
        user_lbl.setStyleSheet("color:rgba(255,255,255,0.8); font-size:12px;")
        lay.addWidget(user_lbl)

        self._pending_lbl = QLabel("")
        self._pending_lbl.setStyleSheet("color:white; font-size:12px; padding:0 12px;")
        lay.addWidget(self._pending_lbl)

        btn_kots = self._top_btn("Pending KOTs")
        btn_kots.clicked.connect(self._show_pending_kots)
        lay.addWidget(btn_kots)

        btn_logout = self._top_btn("🔓 Log Out")
        btn_logout.clicked.connect(self._logout)
        lay.addWidget(btn_logout)

        return bar

    def _build_body(self) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._table_grid = TableGridWidget(api=self.api, outlet=self.outlet)
        self._table_grid.table_selected.connect(self._on_table_selected)
        splitter.addWidget(self._table_grid)

        self._order_panel = OrderPanel(api=self.api, outlet=self.outlet)
        self._order_panel.order_saved.connect(self._table_grid.refresh)
        self._order_panel.bill_requested.connect(lambda _: self._table_grid.refresh())
        splitter.addWidget(self._order_panel)

        splitter.setSizes([720, 480])
        self._refresh_kots()
        return splitter

    @staticmethod
    def _top_btn(label: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setStyleSheet("""
            QPushButton { background:rgba(255,255,255,0.15); color:white;
                          border:1px solid rgba(255,255,255,0.3); border-radius:6px;
                          padding:4px 14px; font-size:12px; }
            QPushButton:hover { background:rgba(255,255,255,0.28); }
        """)
        return btn

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_table_selected(self, table: dict):
        self._order_panel.set_table(table)

    def _refresh_kots(self):
        try:
            kots = self.api.restaurant.get_pending_kots(outlet=self.outlet)
            n = len(kots) if kots else 0
            self._pending_lbl.setText(f"KOTs: {n}" if n else "")
        except Exception:
            pass

    def _show_pending_kots(self):
        try:
            kots = self.api.restaurant.get_pending_kots(outlet=self.outlet)
            if not kots:
                QMessageBox.information(self, "KOTs", "No pending KOTs.")
                return
            lines = "\n".join(
                f"{k['name']}  |  Table {k.get('table','?')}  "
                f"|  {k.get('kitchen_station','')}  |  {k.get('status','')}"
                for k in kots
            )
            QMessageBox.information(self, f"Pending KOTs ({len(kots)})", lines)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _logout(self):
        clear_credentials("restaurant_pos")
        self.close()
        _show_login_and_run(QApplication.instance())


# ── Entry point ───────────────────────────────────────────────────────────────

def _pick_outlet(api) -> str | None:
    try:
        outlets = api.restaurant.get_outlets()
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Could not load outlets:\n{e}")
        return None
    if not outlets:
        QMessageBox.warning(None, "No Outlets",
                            "No active Restaurant outlets found in ERPNext.")
        return None
    if len(outlets) == 1:
        return outlets[0]["name"]
    names = [o.get("outlet_name") or o["name"] for o in outlets]
    choice, ok = QInputDialog.getItem(
        None, "Select Outlet", "Restaurant Outlet:", names, 0, False)
    if not ok:
        return None
    return outlets[names.index(choice)]["name"]


def _show_login_and_run(app: QApplication):
    login = LoginWindow(
        app_name="Restaurant POS",
        subtitle="Point of Sale Terminal",
        icon_char="🍽",
        accent="#c8962e",
        app_key="restaurant_pos",
    )
    if login.exec() != LoginWindow.DialogCode.Accepted:
        sys.exit(0)

    set_client(login.client)
    outlet = _pick_outlet(login.client)
    if not outlet:
        sys.exit(0)

    window = RestaurantPOSWindow(login.client, outlet)
    window.show()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Restaurant POS")
    app.setFont(QFont("Segoe UI", 11))
    _show_login_and_run(app)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
