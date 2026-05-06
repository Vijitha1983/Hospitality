import frappe
from frappe.model.document import Document


class KOTItem(Document):
    def validate(self):
        if self.menu_item and not self.item_name:
            self.item_name = frappe.db.get_value("Menu Item", self.menu_item, "item_name")
        self.amount = (self.qty or 0) * (self.rate or 0)
        if self.status == "Void" and not self.void_reason:
            frappe.throw("Void Reason is required when voiding an item.")
