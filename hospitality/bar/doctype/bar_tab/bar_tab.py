import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class BarTab(Document):
    def before_insert(self):
        self.tab_no = self.name
        if not self.open_time:
            self.open_time = now_datetime()

    def recalculate_total(self):
        total = frappe.db.sql("""
            SELECT COALESCE(SUM(bo.total_amount), 0)
            FROM `tabBar Order` bo
            WHERE bo.tab = %s AND bo.status != 'Cancelled'
        """, self.name)[0][0]
        self.db_set("total_amount", total)

    def on_submit(self):
        self.db_set("close_time", now_datetime())
        self.db_set("status", "Settled")
