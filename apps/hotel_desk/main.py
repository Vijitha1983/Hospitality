"""
Hotel Front Desk — PyQt6 Windows App
Run: python main.py  (from apps/hotel_desk/)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QVBoxLayout, QLabel, QPushButton, QStackedWidget,
                             QFrame, QInputDialog, QMessageBox, QSplitter)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon

from shared.frappe_client import get_client, reset_client, APIError
from ui.dashboard import DashboardWidget
from ui.arrivals import ArrivalsWidget
from ui.check_in_dialog import CheckInDialog
from ui.folio_dialog import FolioDialog


SIDEBAR_W = 200
NAV_ITEMS = [
    ("🏠", "Dashboard",   "dashboard"),
    ("✈", "Arrivals",    "arrivals"),
    ("🚪", "Departures",  "departures"),
    ("🛏", "Rooms",       "rooms"),
    ("📄", "Folios",      "folios"),
]

STYLE = """
QMainWindow { background: #f4f6fa; }
#sidebar { background: #1a3c5e; }
#nav-btn { background: transparent; color: rgba(255,255,255,0.75);
           border: none; text-align: left; padding: 12px 20px;
           font-size: 14px; border-radius: 0; }
#nav-btn:hover { background: rgba(255,255,255,0.1); color: white; }
#nav-btn[active=true] { background: rgba(255,255,255,0.15); color: white;
                         border-left: 3px solid white; }
#content { background: #f4f6fa; }
"""


class NavButton(QPushButton):
    def __init__(self, icon, label, key, parent=None):
        super().__init__(f"  {icon}  {label}", parent)
        self.key = key
        self.setObjectName("nav-btn")
        self.setFixedHeight(48)
        self.setCheckable(True)

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
        self._nav_buttons = {}
        self._pages = {}
        self._build_ui()
        self._navigate("dashboard")

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_lay = QHBoxLayout(central)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_W)
        sb_lay = QVBoxLayout(sidebar)
        sb_lay.setContentsMargins(0, 0, 0, 0)
        sb_lay.setSpacing(0)

        logo = QLabel("🏨  Hotel Desk")
        logo.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        logo.setStyleSheet("color:white; padding:20px 16px 12px 16px;")
        sb_lay.addWidget(logo)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: rgba(255,255,255,0.2);")
        sb_lay.addWidget(sep)

        for icon, label, key in NAV_ITEMS:
            btn = NavButton(icon, label, key)
            btn.clicked.connect(lambda _, k=key: self._navigate(k))
            self._nav_buttons[key] = btn
            sb_lay.addWidget(btn)

        sb_lay.addStretch()

        # Settings / logout
        btn_settings = QPushButton("⚙  Settings")
        btn_settings.setObjectName("nav-btn")
        btn_settings.setFixedHeight(44)
        btn_settings.clicked.connect(self._open_settings)
        sb_lay.addWidget(btn_settings)

        main_lay.addWidget(sidebar)

        # ── Content stack ────────────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setObjectName("content")
        main_lay.addWidget(self._stack)

        self._build_pages()

    def _build_pages(self):
        # Dashboard
        dash = DashboardWidget(self.api)
        self._register_page("dashboard", dash)

        # Arrivals
        arrivals = ArrivalsWidget(self.api)
        arrivals.check_in_requested.connect(self._open_check_in)
        self._register_page("arrivals", arrivals)

        # Departures (placeholder — shows today's departures list)
        dep_widget = self._placeholder("Departures", "Check-out flow coming soon.")
        self._register_page("departures", dep_widget)

        # Rooms
        rooms_widget = self._placeholder("Rooms", "Room status grid coming soon.")
        self._register_page("rooms", rooms_widget)

        # Folios
        folio_widget = self._folio_search_page()
        self._register_page("folios", folio_widget)

    def _register_page(self, key, widget):
        self._pages[key] = widget
        self._stack.addWidget(widget)

    def _navigate(self, key):
        for k, btn in self._nav_buttons.items():
            btn.set_active(k == key)
        if key in self._pages:
            self._stack.setCurrentWidget(self._pages[key])

    def _open_check_in(self, booking: dict):
        dlg = CheckInDialog(self.api, booking, parent=self)
        if dlg.exec() and dlg.result_data:
            # Refresh arrivals list after successful check-in
            if "arrivals" in self._pages:
                self._pages["arrivals"].refresh()

    def _folio_search_page(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)
        title = QLabel("Guest Folios")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #1a3c5e;")
        lay.addWidget(title)

        search_row = QHBoxLayout()
        from PyQt6.QtWidgets import QLineEdit
        self._folio_search = QLineEdit()
        self._folio_search.setPlaceholderText("Enter Folio name or Room number…")
        self._folio_search.setFixedHeight(34)
        self._folio_search.setStyleSheet(
            "border:1px solid #ccc; border-radius:6px; padding:0 10px; font-size:13px;")
        btn_open = QPushButton("Open Folio")
        btn_open.setFixedHeight(34)
        btn_open.setStyleSheet(
            "QPushButton{background:#1a3c5e;color:white;border-radius:6px;padding:0 14px;}"
            "QPushButton:hover{background:#2d6a9f;}")
        btn_open.clicked.connect(self._open_folio_from_search)
        search_row.addWidget(self._folio_search)
        search_row.addWidget(btn_open)
        lay.addLayout(search_row)
        lay.addStretch()
        return w

    def _open_folio_from_search(self):
        query = self._folio_search.text().strip()
        if not query:
            return
        try:
            # Try by room first, then by folio name
            try:
                folio = self.api.hotel.get_folio_by_room(room=query)
                folio_name = folio["name"]
            except Exception:
                folio_name = query
            dlg = FolioDialog(self.api, folio_name, parent=self)
            dlg.exec()
        except Exception as e:
            QMessageBox.warning(self, "Not Found", str(e))

    def _open_settings(self):
        url, ok = QInputDialog.getText(
            self, "Server URL", "ERPNext URL:", text=self.api.url)
        if ok and url:
            key, ok2 = QInputDialog.getText(
                self, "API Key", "API Key:", text=self.api.api_key)
            if ok2:
                secret, ok3 = QInputDialog.getText(
                    self, "API Secret", "API Secret:", text=self.api.api_secret)
                if ok3:
                    reset_client(url=url, api_key=key, api_secret=secret)
                    QMessageBox.information(self, "Saved", "Connection settings updated.")

    @staticmethod
    def _placeholder(title, subtitle):
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


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Hotel Desk")
    app.setFont(QFont("Segoe UI", 11))

    api = get_client()
    if not api.ping():
        QMessageBox.warning(
            None, "Connection Failed",
            "Could not reach the ERPNext server.\n"
            "Check your config.py (SERVER_URL, API_KEY, API_SECRET).\n\n"
            "The app will open — update settings via ⚙ Settings."
        )

    window = HotelDeskWindow(api)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
