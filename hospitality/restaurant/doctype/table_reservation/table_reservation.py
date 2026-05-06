import frappe
from frappe.model.document import Document


class TableReservation(Document):
    def before_insert(self):
        self.reservation_no = self.name

    def after_insert(self):
        from hospitality.utils.notification_utils import send_reservation_confirmation
        send_reservation_confirmation(self.name)
        self.db_set("confirmation_sent", 1)

    def on_update(self):
        if self.table and self.status == "Confirmed":
            frappe.db.set_value("Dining Table", self.table, "current_status", "Reserved")
        if self.status in ("Cancelled", "No Show", "Completed") and self.table:
            frappe.db.set_value("Dining Table", self.table, "current_status", "Available")
