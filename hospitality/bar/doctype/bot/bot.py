import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class BOT(Document):
    def before_insert(self):
        self.bot_no = self.name

    def on_update(self):
        if self.status == "Ready":
            self.db_set("ready_at", now_datetime())
        if self.status == "Served":
            frappe.db.set_value("Bar Order", self.bar_order, "status", "Served")
