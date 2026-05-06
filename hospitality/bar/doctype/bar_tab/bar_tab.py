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


@frappe.whitelist()
def close_and_bill(tab):
    doc = frappe.get_doc("Bar Tab", tab)
    if doc.status != "Open":
        frappe.throw(f"Tab is already {doc.status}.")

    outlet = frappe.get_doc("Outlet", doc.outlet)
    pos_profile = outlet.pos_profile
    if not pos_profile:
        frappe.throw(f"No POS Profile configured on Outlet {doc.outlet}.")

    customer = frappe.db.get_value("Guest", doc.guest, "customer") if doc.guest else None
    if not customer:
        customer = frappe.db.get_value("Outlet", doc.outlet, "walk_in_customer") or "Walk-in Customer"

    # Collect all bar order items for this tab
    orders = frappe.get_all("Bar Order",
        filters={"tab": tab, "docstatus": 1, "status": ["!=", "Cancelled"]},
        fields=["name"])

    line_items = []
    for o in orders:
        order_doc = frappe.get_doc("Bar Order", o.name)
        for item in order_doc.items:
            item_code = frappe.db.get_value("Drink Menu Item", item.drink_item, "item_code")
            if item_code:
                line_items.append({
                    "item_code": item_code,
                    "item_name": item.drink_item,
                    "qty": item.qty,
                    "rate": item.rate,
                    "amount": item.amount,
                })

    if not line_items:
        frappe.throw("No billable items found on this tab.")

    invoice = frappe.get_doc({
        "doctype": "POS Invoice",
        "pos_profile": pos_profile,
        "customer": customer,
        "items": line_items,
    })
    invoice.insert(ignore_permissions=True)

    doc.db_set("pos_invoice", invoice.name)
    doc.db_set("status", "Billed")
    doc.db_set("close_time", now_datetime())
    frappe.db.commit()
    return invoice.name
