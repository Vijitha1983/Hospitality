import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class BarOrder(Document):
    def before_insert(self):
        self.order_no = self.name
        if not self.order_time:
            self.order_time = now_datetime()

    def validate(self):
        total = sum((row.qty or 0) * (row.rate or 0) for row in self.items)
        self.total_amount = total

    def on_submit(self):
        self._fire_bot()
        self._update_tab_total()
        self._consume_stock()
        self._log_excise()

    def _fire_bot(self):
        stations = {}
        for item in self.items:
            station = item.bar_station or "Main Bar"
            if station not in stations:
                stations[station] = []
            stations[station].append(item)

        for station, items in stations.items():
            bot = frappe.get_doc({
                "doctype": "BOT",
                "bar_order": self.name,
                "tab": self.tab,
                "outlet": self.outlet,
                "bar_station": station,
                "fired_at": now_datetime(),
                "status": "Pending",
                "items": [
                    {"drink_item": i.drink_item, "item_name": i.item_name,
                     "qty": i.qty, "modifiers": i.modifiers, "status": "Pending"}
                    for i in items
                ],
            })
            bot.insert(ignore_permissions=True)
            self.db_set("bot", bot.name)
        self.db_set("status", "BOT Sent")

    def _update_tab_total(self):
        tab = frappe.get_doc("Bar Tab", self.tab)
        tab.recalculate_total()

    def _consume_stock(self):
        from hospitality.utils.stock_utils import create_material_issue, get_bom_items
        outlet = frappe.get_doc("Outlet", self.outlet)
        all_items = []
        for item in self.items:
            recipe = frappe.db.get_value("Drink Menu Item", item.drink_item, "recipe")
            if recipe:
                bom = frappe.db.get_value("Cocktail Recipe", recipe, "bom")
                if bom:
                    all_items.extend(get_bom_items(bom, item.qty))
            else:
                item_code = frappe.db.get_value("Drink Menu Item", item.drink_item, "item_code")
                if item_code and item.qty:
                    ml = frappe.db.get_value("Drink Menu Item", item.drink_item, "measure_ml") or 0
                    all_items.append({"item_code": item_code, "qty": ml * item.qty / 1000, "uom": "Litre"})
        if all_items:
            create_material_issue(all_items, outlet.default_warehouse, outlet.property, self.name, "Bar Order")

    def _log_excise(self):
        pass
