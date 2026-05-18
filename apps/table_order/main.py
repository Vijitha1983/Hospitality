"""
Table Order — Kivy Mobile App (Android / tablet)
Run locally:  python main.py
Package for Android: buildozer android debug

Install deps: pip install kivy requests
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import threading
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window

from shared.frappe_client import get_client, APIError

# Force portrait-ish window for local testing
Window.size = (420, 780)

BRAND  = (0.102, 0.235, 0.369, 1)   # #1a3c5e
GREEN  = (0.118, 0.494, 0.353, 1)   # #1e7e5a
RED    = (0.753, 0.224, 0.169, 1)   # #c0392b
WHITE  = (1, 1, 1, 1)
LIGHT  = (0.957, 0.965, 0.980, 1)


def alert(title, msg):
    content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
    content.add_widget(Label(text=msg, text_size=(dp(280), None),
                             halign="left", valign="top"))
    btn = Button(text="OK", size_hint_y=None, height=dp(42),
                 background_color=BRAND)
    popup = Popup(title=title, content=content,
                  size_hint=(0.88, None), height=dp(200))
    btn.bind(on_release=popup.dismiss)
    content.add_widget(btn)
    popup.open()


def run_async(fn, *args, callback=None):
    """Run fn(*args) in a background thread; call callback(result) on main thread."""
    def _target():
        try:
            result = fn(*args)
            if callback:
                Clock.schedule_once(lambda dt: callback(result))
        except Exception as e:
            Clock.schedule_once(lambda dt: alert("Error", str(e)))
    threading.Thread(target=_target, daemon=True).start()


# ─── Screens ──────────────────────────────────────────────────────────────────

class LoginScreen(Screen):
    """Waiter enters their name and selects outlet."""
    def __init__(self, **kw):
        super().__init__(**kw)
        self.api = get_client()
        self._outlets = []
        self._build()
        self._load_outlets()

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(14))

        logo = Label(text="🍽  Table Order", font_size=dp(26),
                     bold=True, color=BRAND, size_hint_y=None, height=dp(60))
        root.add_widget(logo)

        self._waiter_input = TextInput(hint_text="Your name (waiter)",
                                       multiline=False, font_size=dp(15),
                                       size_hint_y=None, height=dp(44))
        root.add_widget(self._waiter_input)

        self._outlet_spinner = Spinner(text="Select Outlet",
                                       values=[],
                                       font_size=dp(14),
                                       size_hint_y=None, height=dp(44))
        root.add_widget(self._outlet_spinner)

        btn = Button(text="Continue →", size_hint_y=None, height=dp(50),
                     background_color=BRAND, font_size=dp(15), bold=True)
        btn.bind(on_release=self._continue)
        root.add_widget(btn)
        root.add_widget(Label())
        self.add_widget(root)

    def _load_outlets(self):
        def _cb(outlets):
            self._outlets = outlets
            self._outlet_spinner.values = [
                o.get("outlet_name") or o["name"] for o in outlets
            ]
        run_async(self.api.restaurant.get_outlets, callback=_cb)

    def _continue(self, *_):
        waiter = self._waiter_input.text.strip()
        sel    = self._outlet_spinner.text
        if not waiter or sel == "Select Outlet":
            alert("Required", "Enter your name and select an outlet.")
            return
        outlet_obj = next(
            (o for o in self._outlets
             if (o.get("outlet_name") or o["name"]) == sel), None)
        if not outlet_obj:
            return
        app = App.get_running_app()
        app.waiter = waiter
        app.outlet = outlet_obj["name"]
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "tables"


class TablesScreen(Screen):
    """Grid of all tables — tap to open order."""
    def __init__(self, **kw):
        super().__init__(**kw)
        self._tables = []
        self._build()

    def on_enter(self):
        self._refresh()

    def _build(self):
        root = BoxLayout(orientation="vertical")

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(52),
                        padding=(dp(12), dp(8)), spacing=dp(8))
        hdr.canvas.before.add_Color(*BRAND)
        from kivy.graphics import Color, Rectangle
        with hdr.canvas.before:
            Color(*BRAND)
            self._hdr_rect = Rectangle(pos=hdr.pos, size=hdr.size)
        hdr.bind(pos=self._update_rect, size=self._update_rect)
        title = Label(text="Tables", font_size=dp(18), bold=True, color=WHITE)
        hdr.add_widget(title)
        btn_ref = Button(text="↻", size_hint=(None, None),
                         size=(dp(40), dp(36)),
                         background_color=(1, 1, 1, 0.2))
        btn_ref.bind(on_release=lambda _: self._refresh())
        hdr.add_widget(btn_ref)
        root.add_widget(hdr)

        scroll = ScrollView()
        self._grid = GridLayout(cols=2, spacing=dp(10), padding=dp(12),
                                size_hint_y=None)
        self._grid.bind(minimum_height=self._grid.setter("height"))
        scroll.add_widget(self._grid)
        root.add_widget(scroll)
        self.add_widget(root)

    def _update_rect(self, instance, value):
        self._hdr_rect.pos  = instance.pos
        self._hdr_rect.size = instance.size

    def _refresh(self):
        app = App.get_running_app()
        run_async(get_client().restaurant.get_tables,
                  callback=self._on_tables,
                  outlet=app.outlet)

    def _on_tables(self, tables):
        self._tables = tables
        self._grid.clear_widgets()
        STATUS_COLOR = {
            "Available": GREEN,
            "Occupied":  RED,
            "Reserved":  (0.545, 0.369, 0.098, 1),
        }
        for t in tables:
            status = t.get("status", "Available")
            color  = STATUS_COLOR.get(status, BRAND)
            num    = t.get("table_number", t.get("name", ""))
            cap    = t.get("capacity", "")
            btn = Button(
                text=f"Table {num}\n{status}\n({cap} seats)",
                size_hint_y=None, height=dp(90),
                background_color=color,
                font_size=dp(13), bold=True,
            )
            btn.bind(on_release=lambda _, tbl=t: self._open_table(tbl))
            self._grid.add_widget(btn)

    def _open_table(self, table: dict):
        app = App.get_running_app()
        app.selected_table = table
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "order"


class OrderScreen(Screen):
    """Take order for the selected table."""
    def __init__(self, **kw):
        super().__init__(**kw)
        self._menu_items = []
        self._pending    = []
        self._build()

    def on_enter(self):
        app = App.get_running_app()
        tbl = app.selected_table or {}
        self._table_lbl.text = (
            f"Table {tbl.get('table_number', tbl.get('name', ''))}  ·  {tbl.get('status','')}"
        )
        self._pending = []
        self._order_list.clear_widgets()
        self._update_total()
        self._load_menu()

    def _build(self):
        root = BoxLayout(orientation="vertical")

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(52),
                        padding=(dp(12), dp(8)), spacing=dp(8))
        with hdr.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*BRAND)
            self._hdr_bg = Rectangle(pos=hdr.pos, size=hdr.size)
        hdr.bind(pos=lambda i, v: setattr(self._hdr_bg, "pos", v),
                 size=lambda i, v: setattr(self._hdr_bg, "size", v))

        btn_back = Button(text="← Back", size_hint=(None, None),
                          size=(dp(70), dp(36)),
                          background_color=(1, 1, 1, 0.15))
        btn_back.bind(on_release=self._go_back)
        self._table_lbl = Label(text="", font_size=dp(15), bold=True, color=WHITE)
        hdr.add_widget(btn_back)
        hdr.add_widget(self._table_lbl)
        root.add_widget(hdr)

        # Menu (top half)
        menu_scroll = ScrollView(size_hint_y=0.5)
        self._menu_grid = GridLayout(cols=2, spacing=dp(8), padding=dp(10),
                                      size_hint_y=None)
        self._menu_grid.bind(minimum_height=self._menu_grid.setter("height"))
        menu_scroll.add_widget(self._menu_grid)
        root.add_widget(menu_scroll)

        from kivy.uix.widget import Widget
        root.add_widget(Widget(size_hint_y=None, height=dp(1)))

        # Order list (bottom half)
        order_lbl = Label(text="Order Items", bold=True, color=BRAND,
                          font_size=dp(13), size_hint_y=None, height=dp(28),
                          halign="left")
        root.add_widget(order_lbl)

        order_scroll = ScrollView(size_hint_y=0.3)
        self._order_list = BoxLayout(orientation="vertical", spacing=dp(4),
                                      padding=dp(6), size_hint_y=None)
        self._order_list.bind(minimum_height=self._order_list.setter("height"))
        order_scroll.add_widget(self._order_list)
        root.add_widget(order_scroll)

        # Footer
        footer = BoxLayout(size_hint_y=None, height=dp(60),
                           padding=(dp(10), dp(8)), spacing=dp(8))
        self._total_lbl = Label(text="Total: 0.00", font_size=dp(16),
                                 bold=True, color=BRAND)
        btn_send = Button(text="Send to Kitchen", size_hint_x=0.5,
                           background_color=BRAND, font_size=dp(14), bold=True)
        btn_send.bind(on_release=self._send_order)
        footer.add_widget(self._total_lbl)
        footer.add_widget(btn_send)
        root.add_widget(footer)
        self.add_widget(root)

    def _load_menu(self):
        app = App.get_running_app()
        run_async(get_client().restaurant.get_menu_items,
                  callback=self._on_menu,
                  outlet=app.outlet)

    def _on_menu(self, items):
        self._menu_items = items
        self._menu_grid.clear_widgets()
        for item in items:
            name  = item.get("item_name", "")
            price = item.get("selling_price", 0)
            btn   = Button(
                text=f"{name}\n{price:,.2f}",
                size_hint_y=None, height=dp(70),
                background_color=(0.95, 0.97, 1, 1),
                color=BRAND, font_size=dp(12),
            )
            btn.bind(on_release=lambda _, i=item: self._add_item(i))
            self._menu_grid.add_widget(btn)

    def _add_item(self, item: dict):
        existing = next((p for p in self._pending
                         if p["menu_item"] == item["name"]), None)
        if existing:
            existing["qty"] += 1
        else:
            self._pending.append({
                "menu_item": item["name"],
                "item_name": item.get("item_name", ""),
                "qty":       1,
                "rate":      float(item.get("selling_price", 0)),
            })
        self._refresh_order_list()

    def _refresh_order_list(self):
        self._order_list.clear_widgets()
        for p in self._pending:
            amount = p["qty"] * p["rate"]
            row = BoxLayout(size_hint_y=None, height=dp(32))
            row.add_widget(Label(
                text=f"{p['qty']}×  {p['item_name']}  —  {amount:,.2f}",
                font_size=dp(13), halign="left", color=(0.2, 0.2, 0.2, 1),
            ))
            self._order_list.add_widget(row)
        self._update_total()

    def _update_total(self):
        total = sum(p["qty"] * p["rate"] for p in self._pending)
        self._total_lbl.text = f"Total: {total:,.2f}"

    def _send_order(self, *_):
        if not self._pending:
            alert("Empty", "Add items before sending.")
            return
        app     = App.get_running_app()
        table   = app.selected_table
        outlet  = app.outlet
        waiter  = app.waiter
        items   = list(self._pending)

        def _do_send():
            try:
                active = get_client().restaurant.get_active_order(
                    table=table["name"])
                if active:
                    get_client().restaurant.add_items_to_order(
                        order=active["name"], items=items)
                else:
                    get_client().restaurant.create_order(
                        table=table["name"], outlet=outlet,
                        items=items, waiter=waiter)
                return True
            except APIError as e:
                raise e

        def _done(ok):
            if ok:
                alert("Sent!", "Order sent to kitchen.")
                self._pending = []
                self._order_list.clear_widgets()
                self._update_total()

        run_async(_do_send, callback=_done)

    def _go_back(self, *_):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "tables"


# ─── App ──────────────────────────────────────────────────────────────────────

class TableOrderApp(App):
    waiter         = ""
    outlet         = ""
    selected_table = None

    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(TablesScreen(name="tables"))
        sm.add_widget(OrderScreen(name="order"))
        return sm


if __name__ == "__main__":
    TableOrderApp().run()
