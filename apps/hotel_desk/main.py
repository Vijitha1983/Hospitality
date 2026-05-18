"""
Hotel Front Desk — PyQt6 Windows App
Run: python main.py  (from apps/hotel_desk/)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QVBoxLayout, QLabel, QPushButton, QStackedWidget,
                             QFrame, QMessageBox, QLineEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from shared.frappe_client import get_client, set_client, clear_credentials
from shared.login_window import LoginWindow
from ui.dashboard import DashboardWidget
from ui.arrivals import ArrivalsWidget
from ui.check_in_dialog import CheckInDialog
from ui.folio_dialog import FolioDialog


SIDEBAR_W = 200
NAV_ITEMS = [
    ("🏠", "Dashboard",  "dashboard"),
    ("✈",  "Arrivals",   "arrivals"),
    ("🚪", "Departures", "departures"),
    ("🛏",  "Rooms",      "rooms"),
    ("📄", "Folios",     "folios"),
]

STYLE = """
QMainWindow, QWidget#root { background: #f4f6fa; }
QWidget#sidebar { background: #1a3c5e; }
QPushButton#nav-btn {
    background: transparent; color: rgba(255,255,255,0.75);
    border: none; text-align: left; padding: 12px 20px;
    font-size: 14px; border-radius: 0;
}
QPushButton#nav-btn:hover { background: rgba(255,255,255,0.1); color: white; }
QPushButton#nav-btn[active=true] {
    background: rgba(255,255,255,0.15); color: white;
    border-left: 3px solid white;
}
"""


class NavButton(QPushButton):
    def __init__(self, icon, label, key, parent=None):
        super().__init__(f"  {icon}  {label}", parent)
        self.key = key
        self.setObjectName("nav-btn")
        self.setFixedHeight(48)

    def set_active(self, active: bool):
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


class HotelDeskWindow(QMainWindow):
    def __init__(self, api):
        super().__init__()
        self.api = api
        self.setWindowTitle("Hotel Front Desk")
        self.resize(1200, 750)
        self.setStyleSheet(STYLE)
        self._nav_buttons: dict[str, NavButton] = {}
        self._pages: dict[str, QWidget] = {}
        self._build_ui()
        self._navigate("dashboard")

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("root")
        self.setCentralWidget(central)
        lay = QHBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._build_sidebar())
        lay.addWidget(self._build_stack())

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_W)
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(0, 0, 0, 0)
        sb.setSpacing(0)

        # Logo
        logo = QLabel("🏨  Hotel Desk")
        logo.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        logo.setStyleSheet("color:white; padding:20px 16px 12px 16px;")
        sb.addWidget(logo)

        # Logged-in user label
        user = self.api.get_logged_user()
        user_lbl = QLabel(f"  👤 {user}")
        user_lbl.setStyleSheet("color:rgba(255,255,255,0.55); font-size:11px; padding:0 16px 10px;")
        sb.addWidget(user_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background:rgba(255,255,255,0.15); max-height:1px;")
        sb.addWidget(sep)

        # Nav buttons
        for icon, label, key in NAV_ITEMS:
            btn = NavButton(icon, label, key)
            btn.clicked.connect(lambda _, k=key: self._navigate(k))
            self._nav_buttons[key] = btn
            sb.addWidget(btn)

        sb.addStretch()

        # Logout
        logout_btn = QPushButton("  🔓  Log Out")
        logout_btn.setObjectName("nav-btn")
        logout_btn.setFixedHeight(46)
        logout_btn.clicked.connect(self._logout)
        sb.addWidget(logout_btn)

        return sidebar

    def _build_stack(self) -> QStackedWidget:
        self._stack = QStackedWidget()
        self._stack.setObjectName("content")

        self._register("dashboard", DashboardWidget(self.api))

        arrivals = ArrivalsWidget(self.api)
        arrivals.check_in_requested.connect(self._open_check_in)
        self._register("arrivals", arrivals)

        self._register("departures", self._placeholder("Departures",
                        "Check-out workflow — coming in next release."))
        self._register("rooms",      self._placeholder("Rooms",
                        "Room status grid — coming in next release."))
        self._register("folios",     self._folio_page())

        return self._stack

    def _register(self, key: str, widget: QWidget):
        self._pages[key] = widget
        self._stack.addWidget(widget)

    # ── Navigation ────────────────────────────────────────────────────────────

    def _navigate(self, key: str):
        for k, btn in self._nav_buttons.items():
            btn.set_active(k == key)
        if key in self._pages:
            self._stack.setCurrentWidget(self._pages[key])

    # ── Pages ─────────────────────────────────────────────────────────────────

    def _folio_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        title = QLabel("Guest Folios")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color:#1a3c5e;")
        lay.addWidget(title)

        row = QHBoxLayout()
        self._folio_search = QLineEdit()
        self._folio_search.setPlaceholderText("Enter Folio name or Room number…")
        self._folio_search.setFixedHeight(34)
        self._folio_search.setStyleSheet(
            "border:1px solid #ccc; border-radius:6px; padding:0 10px; font-size:13px;")
        self._folio_search.returnPressed.connect(self._open_folio)

        btn = QPushButton("Open Folio")
        btn.setFixedHeight(34)
        btn.setStyleSheet(
            "QPushButton{background:#1a3c5e;color:white;border-radius:6px;padding:0 14px;}"
            "QPushButton:hover{background:#2d6a9f;}")
        btn.clicked.connect(self._open_folio)

        row.addWidget(self._folio_search)
        row.addWidget(btn)
        lay.addLayout(row)
        lay.addStretch()
        return w

    @staticmethod
    def _placeholder(title: str, subtitle: str) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t = QLabel(title)
        t.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        t.setStyleSheet("color:#1a3c5e;")
        s = QLabel(subtitle)
        s.setStyleSheet("color:#888; font-size:14px;")
        lay.addWidget(t, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(s, alignment=Qt.AlignmentFlag.AlignCenter)
        return w

    # ── Actions ───────────────────────────────────────────────────────────────

    def _open_check_in(self, booking: dict):
        dlg = CheckInDialog(self.api, booking, parent=self)
        if dlg.exec() and dlg.result_data:
            self._pages["arrivals"].refresh()

    def _open_folio(self):
        query = self._folio_search.text().strip()
        if not query:
            return
        try:
            try:
                folio = self.api.hotel.get_folio_by_room(room=query)
                name = folio["name"]
            except Exception:
                name = query
            FolioDialog(self.api, name, parent=self).exec()
        except Exception as e:
            QMessageBox.warning(self, "Not Found", str(e))

    def _logout(self):
        clear_credentials("hotel_desk")
        self.close()
        _show_login_and_run(QApplication.instance())


# ── Entry point ───────────────────────────────────────────────────────────────

def _show_login_and_run(app: QApplication):
    login = LoginWindow(
        app_name="Hotel Desk",
        subtitle="Hotel Front Desk Terminal",
        icon_char="🏨",
        accent="#1a3c5e",
        app_key="hotel_desk",
    )
    if login.exec() != LoginWindow.DialogCode.Accepted:
        sys.exit(0)

    set_client(login.client)
    window = HotelDeskWindow(login.client)
    window.show()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Hotel Desk")
    app.setFont(QFont("Segoe UI", 11))
    _show_login_and_run(app)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
