import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class RestaurantOrder(Document):
    def before_insert(self):
        self.order_no = self.name
        if not self.order_time:
            self.order_time = now_datetime()

    def validate(self):
        self._calculate_totals()

    def _calculate_totals(self):
        sub = sum((row.qty or 0) * (row.rate or 0) for row in self.items)
        self.sub_total = sub
        self.total_amount = sub + (self.tax_amount or 0)
        for row in self.items:
            row.amount = (row.qty or 0) * (row.rate or 0)

    def on_submit(self):
        self._fire_kot()
        self._update_table_status()
        if self.is_room_service and self.folio:
            self._post_to_folio()
        else:
            self._create_stock_entry()

    def _fire_kot(self):
        stations = {}
        for item in self.items:
            if item.status == "Void":
                continue
            station = frappe.db.get_value("Menu Item", item.menu_item, "kitchen_station") or "Hot Kitchen"
            if station not in stations:
                stations[station] = []
            stations[station].append(item)

        for station, items in stations.items():
            kot = frappe.get_doc({
                "doctype": "KOT",
                "restaurant_order": self.name,
                "table": self.table,
                "outlet": self.outlet,
                "kitchen_station": station,
                "fired_at": now_datetime(),
                "status": "Pending",
                "items": [
                    {
                        "menu_item": i.menu_item,
                        "item_name": i.item_name,
                        "qty": i.qty,
                        "rate": i.rate,
                        "amount": i.amount,
                        "modifiers": i.modifiers,
                        "special_instructions": i.special_instructions,
                        "course": i.course,
                        "status": "Pending",
                    }
                    for i in items
                ],
            })
            kot.insert(ignore_permissions=True)

        self.db_set("status", "KOT Sent")

    def _update_table_status(self):
        table = frappe.get_doc("Dining Table", self.table)
        table.mark_occupied(self.name)

    def _post_to_folio(self):
        folio = frappe.get_doc("Guest Folio", self.folio)
        charge_type = frappe.db.get_value("Charge Type", {"charge_category": "Food and Beverage"}, "name")
        folio.post_charge(
            charge_type=charge_type,
            description=f"Room Service — Order {self.order_no}",
            qty=1,
            rate=self.total_amount,
            reference_doc=self.name,
        )

    def _create_stock_entry(self):
        from hospitality.utils.stock_utils import create_material_issue, get_bom_items
        outlet = frappe.get_doc("Outlet", self.outlet)
        warehouse = outlet.default_warehouse
        company = outlet.property
        all_items = []
        for item in self.items:
            if item.status == "Void":
                continue
            bom = frappe.db.get_value("Menu Item", item.menu_item, "bom")
            if bom:
                bom_items = get_bom_items(bom, item.qty)
                all_items.extend(bom_items)
        if all_items:
            create_material_issue(all_items, warehouse, company, self.name, "Restaurant Order")
