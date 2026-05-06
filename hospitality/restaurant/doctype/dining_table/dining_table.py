import frappe
from frappe.model.document import Document


class DiningTable(Document):
    def mark_occupied(self, order):
        self.db_set("current_status", "Occupied")
        self.db_set("current_order", order)

    def mark_available(self):
        self.db_set("current_status", "Available")
        self.db_set("current_order", None)

    def mark_dirty(self):
        self.db_set("current_status", "Dirty")
        self.db_set("current_order", None)
