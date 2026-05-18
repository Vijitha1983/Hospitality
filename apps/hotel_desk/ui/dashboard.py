from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QGridLayout, QPushButton, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class StatCard(QFrame):
    def __init__(self, title, value="—", color="#1a3c5e", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background: {color};
                border-radius: 10px;
                min-width: 160px;
                min-height: 100px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)

        self._value_lbl = QLabel(str(value))
        self._value_lbl.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        self._value_lbl.setStyleSheet("color: white;")
        self._value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._title_lbl = QLabel(title)
        self._title_lbl.setFont(QFont("Segoe UI", 10))
        self._title_lbl.setStyleSheet("color: rgba(255,255,255,0.8);")
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_lbl.setWordWrap(True)

        layout.addWidget(self._value_lbl)
        layout.addWidget(self._title_lbl)

    def set_value(self, v):
        self._value_lbl.setText(str(v))


class DashboardWidget(QWidget):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self._build_ui()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start(60_000)  # refresh every 60 s
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(20)

        title = QLabel("Front Desk Dashboard")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #1a3c5e;")
        root.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(16)

        self._cards = {
            "total":      StatCard("Total Rooms",      color="#1a3c5e"),
            "occupied":   StatCard("Occupied",          color="#2d6a9f"),
            "available":  StatCard("Available",         color="#1e7e5a"),
            "occ_pct":    StatCard("Occupancy %",       color="#8b5e1a"),
            "arrivals":   StatCard("Arrivals Today",    color="#c0392b"),
            "departures": StatCard("Departures Today",  color="#7d3c98"),
        }

        positions = [
            (0, 0, "total"),     (0, 1, "occupied"),   (0, 2, "available"),
            (1, 0, "occ_pct"),   (1, 1, "arrivals"),   (1, 2, "departures"),
        ]
        for row, col, key in positions:
            grid.addWidget(self._cards[key], row, col)

        root.addLayout(grid)

        btn_refresh = QPushButton("↻  Refresh")
        btn_refresh.setFixedWidth(120)
        btn_refresh.setStyleSheet("""
            QPushButton { background:#1a3c5e; color:white; border-radius:6px;
                          padding:6px 12px; font-size:12px; }
            QPushButton:hover { background:#2d6a9f; }
        """)
        btn_refresh.clicked.connect(self.refresh)
        root.addWidget(btn_refresh, alignment=Qt.AlignmentFlag.AlignLeft)
        root.addStretch()

    def refresh(self):
        try:
            s = self.api.hotel.get_dashboard_stats()
            self._cards["total"].set_value(s.get("total_rooms", "—"))
            self._cards["occupied"].set_value(s.get("occupied", "—"))
            self._cards["available"].set_value(s.get("available", "—"))
            self._cards["occ_pct"].set_value(f"{s.get('occupancy_pct', 0):.1f}%")
            self._cards["arrivals"].set_value(s.get("arrivals_today", "—"))
            self._cards["departures"].set_value(s.get("departures_today", "—"))
        except Exception as e:
            print(f"Dashboard refresh error: {e}")
