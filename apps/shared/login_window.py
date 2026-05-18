"""
Dark-themed login window shared by Hotel Desk and Restaurant POS.

Usage:
    from shared.login_window import LoginWindow
    win = LoginWindow(
        app_name="Hotel Desk",
        subtitle="Hotel Front Desk Terminal",
        icon_char="🏨",
        accent="#3b7ddd",
    )
    if win.exec() == LoginWindow.DialogCode.Accepted:
        api = win.client
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QGraphicsDropShadowEffect, QSizePolicy,
    QCheckBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon

from shared.frappe_client import login_with_password, APIError, save_credentials, load_credentials
from shared.config import DEFAULT_SERVER_URL

# ── Palette ───────────────────────────────────────────────────────────────────
BG       = "#0f0f1a"
CARD     = "#1a1a2e"
INPUT_BG = "#252540"
INPUT_BD = "#3a3a58"
FOCUS_BD = "#3b7ddd"
BTN      = "#3b7ddd"
BTN_HOV  = "#2d6bcf"
BTN_DIS  = "#1e3a6e"
WHITE    = "#ffffff"
LABEL    = "#9999bb"
ERROR    = "#ff5566"
SUCCESS  = "#44dd88"


# ── Worker thread for login (keeps UI responsive) ─────────────────────────────
class _LoginWorker(QThread):
    succeeded = pyqtSignal(object)   # FrappeClient
    failed    = pyqtSignal(str)

    def __init__(self, url, username, password):
        super().__init__()
        self.url, self.username, self.password = url, username, password

    def run(self):
        try:
            client = login_with_password(self.url, self.username, self.password)
            self.succeeded.emit(client)
        except APIError as e:
            self.failed.emit(str(e))
        except Exception as e:
            self.failed.emit(f"Unexpected error: {e}")


# ── Login Window ──────────────────────────────────────────────────────────────
class LoginWindow(QDialog):
    def __init__(self, app_name: str, subtitle: str,
                 icon_char: str = "⬛", accent: str = "#3b7ddd",
                 app_key: str = "default", parent=None):
        super().__init__(parent)
        self.app_name  = app_name
        self.app_key   = app_key
        self.accent    = accent
        self.client    = None
        self._worker   = None

        self.setWindowTitle(app_name)
        self.setModal(True)
        self.setFixedSize(460, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._build_ui(icon_char, subtitle)
        self._load_saved()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build_ui(self, icon_char, subtitle):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(0)

        # ── Outer card ────────────────────────────────────────────────────────
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(f"""
            QFrame#card {{
                background: {CARD};
                border-radius: 18px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 160))
        card.setGraphicsEffect(shadow)

        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(36, 36, 36, 36)
        card_lay.setSpacing(0)

        # ── Icon ──────────────────────────────────────────────────────────────
        icon_wrap = QHBoxLayout()
        icon_lbl = QLabel(icon_char)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setFixedSize(68, 68)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 26))
        icon_lbl.setStyleSheet(f"""
            QLabel {{
                background: {self.accent};
                border-radius: 18px;
                color: white;
            }}
        """)
        icon_wrap.addStretch()
        icon_wrap.addWidget(icon_lbl)
        icon_wrap.addStretch()
        card_lay.addLayout(icon_wrap)
        card_lay.addSpacing(14)

        # ── App name ──────────────────────────────────────────────────────────
        name_lbl = QLabel(self.app_name)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {WHITE};")
        card_lay.addWidget(name_lbl)
        card_lay.addSpacing(4)

        sub_lbl = QLabel(subtitle)
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setFont(QFont("Segoe UI", 10))
        sub_lbl.setStyleSheet(f"color: {self.accent};")
        card_lay.addWidget(sub_lbl)
        card_lay.addSpacing(28)

        # ── Sign In header ────────────────────────────────────────────────────
        sign_lbl = QLabel("Sign In")
        sign_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        sign_lbl.setStyleSheet(f"color: {WHITE};")
        card_lay.addWidget(sign_lbl)
        card_lay.addSpacing(16)

        # ── Fields ────────────────────────────────────────────────────────────
        self._url_edit  = self._field(card_lay, "ERPNext URL",  "https://",       False)
        card_lay.addSpacing(12)
        self._user_edit = self._field(card_lay, "Username",     "admin",          False)
        card_lay.addSpacing(12)
        self._pass_edit = self._field(card_lay, "Password",     "••••••••",       True)
        card_lay.addSpacing(10)

        # ── Remember me ───────────────────────────────────────────────────────
        rem_row = QHBoxLayout()
        self._remember = QCheckBox("Remember me")
        self._remember.setStyleSheet(f"color: {LABEL}; font-size: 11px;")
        self._remember.setChecked(True)
        rem_row.addWidget(self._remember)
        rem_row.addStretch()
        card_lay.addLayout(rem_row)
        card_lay.addSpacing(18)

        # ── Sign In button ────────────────────────────────────────────────────
        self._btn = QPushButton("Sign In")
        self._btn.setFixedHeight(48)
        self._btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.accent};
                color: white;
                border: none;
                border-radius: 10px;
            }}
            QPushButton:hover  {{ background: {BTN_HOV}; }}
            QPushButton:pressed {{ background: #1f509e; }}
            QPushButton:disabled {{ background: {BTN_DIS}; color: #5566aa; }}
        """)
        self._btn.clicked.connect(self._do_login)
        card_lay.addWidget(self._btn)
        card_lay.addSpacing(12)

        # ── Error label ───────────────────────────────────────────────────────
        self._err_lbl = QLabel("")
        self._err_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._err_lbl.setWordWrap(True)
        self._err_lbl.setFont(QFont("Segoe UI", 10))
        self._err_lbl.setStyleSheet(f"color: {ERROR};")
        self._err_lbl.setVisible(False)
        card_lay.addWidget(self._err_lbl)

        root.addWidget(card)

        # ── Window background ─────────────────────────────────────────────────
        self.setStyleSheet(f"QDialog {{ background: {BG}; border-radius: 18px; }}")

        # Enter key triggers login
        self._pass_edit.returnPressed.connect(self._do_login)
        self._url_edit.returnPressed.connect(self._user_edit.setFocus)
        self._user_edit.returnPressed.connect(self._pass_edit.setFocus)

    def _field(self, parent_layout, label_text, placeholder, is_password):
        lbl = QLabel(label_text)
        lbl.setFont(QFont("Segoe UI", 9))
        lbl.setStyleSheet(f"color: {LABEL};")
        parent_layout.addWidget(lbl)
        parent_layout.addSpacing(4)

        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setFixedHeight(46)
        edit.setFont(QFont("Segoe UI", 12))
        if is_password:
            edit.setEchoMode(QLineEdit.EchoMode.Password)
        edit.setStyleSheet(f"""
            QLineEdit {{
                background: {INPUT_BG};
                color: {WHITE};
                border: 1.5px solid {INPUT_BD};
                border-radius: 9px;
                padding: 0 14px;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {self.accent};
            }}
            QLineEdit::placeholder {{
                color: #44445a;
            }}
        """)
        parent_layout.addWidget(edit)
        return edit

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _load_saved(self):
        creds = load_credentials(self.app_key)
        if creds:
            self._url_edit.setText(creds.get("url", ""))
            self._user_edit.setText(creds.get("username", ""))
            self._pass_edit.setText(creds.get("password", ""))
        elif DEFAULT_SERVER_URL and DEFAULT_SERVER_URL != "https://":
            self._url_edit.setText(DEFAULT_SERVER_URL)

    def _do_login(self):
        url  = self._url_edit.text().strip()
        user = self._user_edit.text().strip()
        pwd  = self._pass_edit.text()

        if not url or not user or not pwd:
            self._show_error("Please fill in all fields.")
            return

        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self._url_edit.setText(url)

        self._set_busy(True)
        self._err_lbl.setVisible(False)

        self._worker = _LoginWorker(url, user, pwd)
        self._worker.succeeded.connect(self._on_success)
        self._worker.failed.connect(self._on_failure)
        self._worker.start()

    def _on_success(self, client):
        self.client = client
        self._set_busy(False)
        if self._remember.isChecked():
            save_credentials(
                self._url_edit.text().strip(),
                self._user_edit.text().strip(),
                self._pass_edit.text(),
                self.app_key,
            )
        self.accept()

    def _on_failure(self, msg: str):
        self._set_busy(False)
        self._show_error(msg)

    def _show_error(self, msg: str):
        self._err_lbl.setText(msg)
        self._err_lbl.setVisible(True)

    def _set_busy(self, busy: bool):
        self._btn.setEnabled(not busy)
        self._btn.setText("Signing in…" if busy else "Sign In")
        self._url_edit.setEnabled(not busy)
        self._user_edit.setEnabled(not busy)
        self._pass_edit.setEnabled(not busy)

    # Allow dragging the frameless window
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton and hasattr(self, "_drag_pos"):
            self.move(e.globalPosition().toPoint() - self._drag_pos)
