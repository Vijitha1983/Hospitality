"""
Table Order — Kivy Mobile App (Android / tablet)
Run locally:  python main.py
Package APK:  buildozer android debug   (from apps/table_order/ on Linux/WSL)

Install:  pip install kivy requests
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import threading

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle

from shared.frappe_client import login_with_password, save_credentials, load_credentials, APIError

Window.size = (420, 820)   # local test size; ignored on device

# ── Palette ───────────────────────────────────────────────────────────────────
BG     = (0.059, 0.059, 0.102, 1)
CARD   = (0.102, 0.102, 0.180, 1)
INPUT  = (0.145, 0.145, 0.251, 1)
ACCENT = (0.231, 0.490, 0.867, 1)
WHITE  = (1, 1, 1, 1)
GRAY   = (0.6, 0.6, 0.73, 1)
ERR    = (1, 0.333, 0.400, 1)
GREEN  = (0.118, 0.494, 0.353, 1)
RED_C  = (0.753, 0.224, 0.169, 1)
ORANGE = (0.784, 0.588, 0.180, 1)


# ── Utilities ─────────────────────────────────────────────────────────────────

def run_async(fn, *args, on_done=None, on_error=None, **kwargs):
    def _run():
        try:
            result = fn(*args, **kwargs)
            if on_done:
                Clock.schedule_once(lambda dt: on_done(result))
        except Exception as e:
            if on_error:
                Clock.schedule_once(lambda dt: on_error(str(e)))
    threading.Thread(target=_run, daemon=True).start()


def alert(title, msg, on_ok=None):
    content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
    content.add_widget(Label(text=msg, color=WHITE, halign="center",
                              text_size=(dp(260), None), valign="top"))
    btn = Button(text="OK", size_hint_y=None, height=dp(44),
                 background_normal="", background_color=ACCENT, color=WHITE)
    popup = Popup(title=title, content=content,
                  size_hint=(0.85, None), height=dp(220),
                  title_color=WHITE,
                  background_color=(*CARD[:3], 1),
                  separator_color=(*ACCENT[:3], 1))
    def _close(*_):
        popup.dismiss()
        if on_ok:
            on_ok()
    btn.bind(on_release=_close)
    content.add_widget(btn)
    popup.open()


def set_bg(widget, color):
    with widget.canvas.before:
        Color(*color)
        rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda *_: setattr(rect, "pos", widget.pos),
                size=lambda *_: setattr(rect, "size", widget.size))
    return rect


def set_bg_rounded(widget, color, radius=dp(14)):
    with widget.canvas.before:
        Color(*color)
        rect = RoundedRectangle(pos=widget.pos, size=widget.size,
                                radius=[radius])
    widget.bind(pos=lambda *_: setattr(rect, "pos", widget.pos),
                size=lambda *_: setattr(rect, "size", widget.size))
    return rect


# ── Login Screen ──────────────────────────────────────────────────────────────

class LoginScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._busy = False
        self._build()
        Clock.schedule_once(lambda dt: self._load_saved(), 0.1)

    def _build(self):
        set_bg(self, BG)

        root = BoxLayout(orientation="vertical",
                         padding=[dp(28), dp(50), dp(28), dp(40)],
                         spacing=0)

        # ── Icon ──────────────────────────────────────────────────────────────
        icon_row = BoxLayout(size_hint_y=None, height=dp(76))
        icon_wrap = BoxLayout(size_hint=(None, None), size=(dp(68), dp(68)))
        set_bg_rounded(icon_wrap, ACCENT, radius=dp(18))
        icon_wrap.add_widget(Label(text="📋", font_size=dp(30), color=WHITE))
        icon_row.add_widget(Widget())
        icon_row.add_widget(icon_wrap)
        icon_row.add_widget(Widget())
        root.add_widget(icon_row)
        root.add_widget(Widget(size_hint_y=None, height=dp(14)))

        # ── Title ─────────────────────────────────────────────────────────────
        root.add_widget(Label(text="Table Order", font_size=dp(24),
                               bold=True, color=WHITE,
                               size_hint_y=None, height=dp(36)))
        root.add_widget(Label(text="Waiter Order Terminal",
                               font_size=dp(12), color=(*ACCENT[:3], 1),
                               size_hint_y=None, height=dp(22)))
        root.add_widget(Widget(size_hint_y=None, height=dp(30)))

        # ── Card ──────────────────────────────────────────────────────────────
        card = BoxLayout(orientation="vertical",
                          padding=[dp(26), dp(26), dp(26), dp(22)],
                          spacing=0, size_hint_y=None, height=dp(390))
        set_bg_rounded(card, CARD, radius=dp(16))

        card.add_widget(Label(text="Sign In", font_size=dp(17), bold=True,
                               color=WHITE, halign="left",
                               size_hint_y=None, height=dp(28),
                               text_size=(dp(340), None)))
        card.add_widget(Widget(size_hint_y=None, height=dp(18)))

        for attr, lbl_text, hint, is_pwd in [
            ("_url",  "ERPNext URL", "https://",  False),
            ("_user", "Username",    "admin",      False),
            ("_pwd",  "Password",    "••••••••",   True),
        ]:
            card.add_widget(Label(text=lbl_text, font_size=dp(11), color=GRAY,
                                   halign="left", size_hint_y=None, height=dp(18),
                                   text_size=(dp(340), None)))
            field = TextInput(hint_text=hint, password=is_pwd, multiline=False,
                              background_normal="", background_color=INPUT,
                              foreground_color=WHITE,
                              hint_text_color=(*GRAY[:3], 0.5),
                              cursor_color=(*ACCENT[:3], 1),
                              padding=[dp(14), dp(13)],
                              font_size=dp(15),
                              size_hint_y=None, height=dp(48))
            setattr(self, attr, field)
            card.add_widget(field)
            card.add_widget(Widget(size_hint_y=None, height=dp(10)))

        card.add_widget(Widget(size_hint_y=None, height=dp(6)))

        self._sign_btn = Button(
            text="Sign In",
            size_hint_y=None, height=dp(50),
            background_normal="", background_color=ACCENT,
            color=WHITE, font_size=dp(15), bold=True,
        )
        self._sign_btn.bind(on_release=self._do_login)
        card.add_widget(self._sign_btn)

        root.add_widget(card)

        self._err_lbl = Label(text="", font_size=dp(12), color=ERR,
                               size_hint_y=None, height=dp(0),
                               halign="center", text_size=(dp(340), None))
        root.add_widget(self._err_lbl)
        root.add_widget(Widget())
        self.add_widget(root)

    def _load_saved(self):
        creds = load_credentials("table_order")
        if creds:
            self._url.text  = creds.get("url", "")
            self._user.text = creds.get("username", "")
            self._pwd.text  = creds.get("password", "")

    def _do_login(self, *_):
        if self._busy:
            return
        url  = self._url.text.strip()
        user = self._user.text.strip()
        pwd  = self._pwd.text
        if not url or not user or not pwd:
            self._show_err("Please fill in all fields.")
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self._url.text = url
        self._busy = True
        self._sign_btn.text = "Signing in…"
        self._sign_btn.background_color = (*ACCENT[:3], 0.5)
        self._err_lbl.text = ""
        self._err_lbl.height = dp(0)
        run_async(login_with_password, url, user, pwd,
                  on_done=self._on_ok, on_error=self._on_err)

    def _on_ok(self, client):
        self._busy = False
        self._reset_btn()
        save_credentials(self._url.text.strip(),
                         self._user.text.strip(),
                         self._pwd.text, "table_order")
        app = App.get_running_app()
        app.api    = client
        app.waiter = self._user.text.strip()
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "outlet"

    def _on_err(self, msg):
        self._busy = False
        self._reset_btn()
        self._show_err(msg)

    def _show_err(self, msg):
        self._err_lbl.text   = msg
        self._err_lbl.height = dp(36)

    def _reset_btn(self):
        self._sign_btn.text = "Sign In"
        self._sign_btn.background_color = ACCENT


# ── Outlet Screen ─────────────────────────────────────────────────────────────

class OutletScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._build()

    def on_enter(self):
        self._load()

    def _build(self):
        set_bg(self, BG)
        root = BoxLayout(orientation="vertical",
                         padding=[dp(28), dp(60), dp(28), dp(40)],
                         spacing=dp(14))
        root.add_widget(Label(text="Select Outlet", font_size=dp(22),
                               bold=True, color=WHITE,
                               size_hint_y=None, height=dp(38)))
        root.add_widget(Label(text="Choose your restaurant outlet",
                               font_size=dp(12), color=GRAY,
                               size_hint_y=None, height=dp(22)))
        self._btn_box = BoxLayout(orientation="vertical", spacing=dp(12))
        root.add_widget(self._btn_box)
        root.add_widget(Widget())
        self.add_widget(root)

    def _load(self):
        self._btn_box.clear_widgets()
        self._btn_box.add_widget(Label(text="Loading…", color=GRAY))
        api = App.get_running_app().api
        run_async(api.restaurant.get_outlets,
                  on_done=self._on_outlets,
                  on_error=lambda e: alert("Error", e))

    def _on_outlets(self, outlets):
        self._btn_box.clear_widgets()
        if not outlets:
            self._btn_box.add_widget(Label(text="No outlets found.", color=ERR))
            return
        for o in outlets:
            name = o.get("outlet_name") or o["name"]
            btn = Button(text=name, size_hint_y=None, height=dp(54),
                          background_normal="", background_color=ACCENT,
                          color=WHITE, font_size=dp(14), bold=True)
            btn.bind(on_release=lambda _, outlet=o: self._pick(outlet))
            self._btn_box.add_widget(btn)

    def _pick(self, outlet):
        App.get_running_app().outlet = outlet["name"]
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "tables"


# ── Tables Screen ─────────────────────────────────────────────────────────────

class TablesScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._build()

    def on_enter(self):
        self._refresh()

    def _build(self):
        set_bg(self, BG)
        root = BoxLayout(orientation="vertical")

        hdr = BoxLayout(size_hint_y=None, height=dp(56), padding=[dp(12), dp(10)])
        set_bg(hdr, ACCENT)
        self._hdr_lbl = Label(text="📋  Tables", font_size=dp(17),
                               bold=True, color=WHITE)
        ref = Button(text="↻", size_hint=(None, None), size=(dp(40), dp(36)),
                     background_normal="", background_color=(1,1,1,0.15),
                     color=WHITE, font_size=dp(18))
        ref.bind(on_release=lambda _: self._refresh())
        logout = Button(text="Log Out", size_hint=(None, None),
                        size=(dp(80), dp(36)),
                        background_normal="", background_color=(1,1,1,0.12),
                        color=WHITE, font_size=dp(12))
        logout.bind(on_release=self._logout)
        hdr.add_widget(self._hdr_lbl)
        hdr.add_widget(ref)
        hdr.add_widget(logout)
        root.add_widget(hdr)

        scroll = ScrollView()
        self._grid = GridLayout(cols=2, spacing=dp(10), padding=dp(12),
                                 size_hint_y=None)
        self._grid.bind(minimum_height=self._grid.setter("height"))
        scroll.add_widget(self._grid)
        root.add_widget(scroll)
        self.add_widget(root)

    def _refresh(self):
        app = App.get_running_app()
        if not app.outlet:
            return
        run_async(app.api.restaurant.get_tables,
                  on_done=self._on_tables,
                  on_error=lambda e: alert("Error", e),
                  outlet=app.outlet)

    def _on_tables(self, tables):
        self._grid.clear_widgets()
        STATUS = {"Available": GREEN, "Occupied": RED_C, "Reserved": ORANGE}
        for t in tables:
            status = t.get("status", "Available")
            color  = STATUS.get(status, ACCENT)
            num    = t.get("table_number", t.get("name", "?"))
            cap    = t.get("capacity", "")
            btn = Button(text=f"Table {num}\n{status}\n({cap} seats)",
                          size_hint_y=None, height=dp(90),
                          background_normal="", background_color=color,
                          color=WHITE, font_size=dp(13), bold=True)
            btn.bind(on_release=lambda _, tbl=t: self._open(tbl))
            self._grid.add_widget(btn)

    def _open(self, table):
        App.get_running_app().selected_table = table
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "order"

    def _logout(self, *_):
        from shared.frappe_client import clear_credentials
        clear_credentials("table_order")
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "login"


# ── Order Screen ──────────────────────────────────────────────────────────────

class OrderScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._menu_items = []
        self._pending    = []
        self._build()

    def on_enter(self):
        app = App.get_running_app()
        tbl = app.selected_table or {}
        num = tbl.get("table_number", tbl.get("name", "?"))
        self._hdr_lbl.text = f"Table {num}  ·  {tbl.get('status','')}"
        self._pending = []
        self._order_box.clear_widgets()
        self._update_total()
        self._load_menu()

    def _build(self):
        set_bg(self, BG)
        root = BoxLayout(orientation="vertical")

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(56), padding=[dp(8), dp(10)])
        set_bg(hdr, ACCENT)
        back = Button(text="← Back", size_hint=(None, None),
                       size=(dp(80), dp(36)),
                       background_normal="", background_color=(1,1,1,0.15),
                       color=WHITE, font_size=dp(12))
        back.bind(on_release=self._go_back)
        self._hdr_lbl = Label(text="", font_size=dp(15), bold=True, color=WHITE)
        hdr.add_widget(back)
        hdr.add_widget(self._hdr_lbl)
        root.add_widget(hdr)

        # Menu
        ms = ScrollView(size_hint_y=0.44)
        self._menu_grid = GridLayout(cols=2, spacing=dp(8), padding=dp(10),
                                      size_hint_y=None)
        self._menu_grid.bind(minimum_height=self._menu_grid.setter("height"))
        ms.add_widget(self._menu_grid)
        root.add_widget(ms)

        # Order list
        root.add_widget(Label(text="Order Items", font_size=dp(12), bold=True,
                               color=(*ACCENT[:3], 1),
                               size_hint_y=None, height=dp(26),
                               halign="left", text_size=(dp(380), None),
                               padding_x=dp(12)))
        os_ = ScrollView(size_hint_y=0.28)
        self._order_box = BoxLayout(orientation="vertical", spacing=dp(4),
                                     padding=[dp(10), dp(4)], size_hint_y=None)
        self._order_box.bind(minimum_height=self._order_box.setter("height"))
        os_.add_widget(self._order_box)
        root.add_widget(os_)

        # Footer
        footer = BoxLayout(size_hint_y=None, height=dp(62),
                            padding=[dp(12), dp(8)], spacing=dp(10))
        set_bg(footer, CARD)
        self._total_lbl = Label(text="Total: 0.00", font_size=dp(16),
                                 bold=True, color=WHITE)
        send = Button(text="Send to Kitchen", size_hint_x=0.5,
                       background_normal="", background_color=ACCENT,
                       color=WHITE, font_size=dp(14), bold=True)
        send.bind(on_release=self._send)
        footer.add_widget(self._total_lbl)
        footer.add_widget(send)
        root.add_widget(footer)
        self.add_widget(root)

    def _load_menu(self):
        app = App.get_running_app()
        run_async(app.api.restaurant.get_menu_items,
                  on_done=self._on_menu,
                  on_error=lambda e: alert("Error", e),
                  outlet=app.outlet)

    def _on_menu(self, items):
        self._menu_items = items
        self._menu_grid.clear_widgets()
        for item in items:
            name  = item.get("item_name", "")
            price = float(item.get("selling_price", 0))
            btn = Button(text=f"{name}\n{price:,.2f}",
                          size_hint_y=None, height=dp(72),
                          background_normal="", background_color=(*CARD[:3], 1),
                          color=WHITE, font_size=dp(12))
            btn.bind(on_release=lambda _, i=item: self._add(i))
            self._menu_grid.add_widget(btn)

    def _add(self, item):
        ex = next((p for p in self._pending if p["menu_item"] == item["name"]), None)
        if ex:
            ex["qty"] += 1
        else:
            self._pending.append({"menu_item": item["name"],
                                   "item_name": item.get("item_name", ""),
                                   "qty": 1,
                                   "rate": float(item.get("selling_price", 0))})
        self._refresh_list()

    def _refresh_list(self):
        self._order_box.clear_widgets()
        for p in self._pending:
            amt = p["qty"] * p["rate"]
            row = BoxLayout(size_hint_y=None, height=dp(30))
            row.add_widget(Label(
                text=f"{p['qty']}×  {p['item_name']}  —  {amt:,.2f}",
                color=WHITE, font_size=dp(13), halign="left",
                text_size=(dp(360), None)))
            self._order_box.add_widget(row)
        self._update_total()

    def _update_total(self):
        self._total_lbl.text = f"Total: {sum(p['qty']*p['rate'] for p in self._pending):,.2f}"

    def _send(self, *_):
        if not self._pending:
            alert("Empty", "Add items first.")
            return
        app   = App.get_running_app()
        table = app.selected_table
        items = list(self._pending)

        def _do():
            active = app.api.restaurant.get_active_order(table=table["name"])
            if active:
                app.api.restaurant.add_items_to_order(order=active["name"], items=items)
            else:
                app.api.restaurant.create_order(table=table["name"],
                                                outlet=app.outlet,
                                                items=items, waiter=app.waiter)
            return True

        run_async(_do, on_done=lambda _: alert("Sent!", "Order sent to kitchen.",
                                                on_ok=self._go_back),
                  on_error=lambda e: alert("Error", e))

    def _go_back(self, *_):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "tables"


# ── App ───────────────────────────────────────────────────────────────────────

class TableOrderApp(App):
    api            = None
    waiter         = ""
    outlet         = ""
    selected_table = None

    def build(self):
        self.title = "Table Order"
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(OutletScreen(name="outlet"))
        sm.add_widget(TablesScreen(name="tables"))
        sm.add_widget(OrderScreen(name="order"))
        return sm


if __name__ == "__main__":
    TableOrderApp().run()
