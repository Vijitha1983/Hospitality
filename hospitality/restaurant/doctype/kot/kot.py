import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class KOT(Document):
    def before_insert(self):
        self.kot_no = self.name

    def on_update(self):
        if self.status == "Ready":
            self.db_set("ready_at", now_datetime())
            self._notify_steward()
        self._sync_order_status()

    def _notify_steward(self):
        from hospitality.utils.notification_utils import send_kot_ready_notification
        send_kot_ready_notification(self.name)

    def _sync_order_status(self):
        all_kots = frappe.get_all("KOT",
            filters={"restaurant_order": self.restaurant_order},
            fields=["status"])
        statuses = [k.status for k in all_kots]
        if all(s == "Ready" for s in statuses):
            frappe.db.set_value("Restaurant Order", self.restaurant_order, "status", "Served")
        elif any(s == "Ready" for s in statuses):
            frappe.db.set_value("Restaurant Order", self.restaurant_order, "status", "Partially Served")
