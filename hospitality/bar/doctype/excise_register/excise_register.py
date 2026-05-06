import frappe
from frappe.model.document import Document
from frappe.utils import today


class ExciseRegister(Document):
    def validate(self):
        if self.is_submitted:
            frappe.throw("This Excise Register has been submitted and cannot be modified.")
        self._calculate_totals()

    def _calculate_totals(self):
        total_val = sum(row.value or 0 for row in self.sales_lines)
        total_ml = sum(row.qty_ml or 0 for row in self.sales_lines)
        self.total_value = total_val
        self.total_qty_ml = total_ml

    def on_submit(self):
        self.db_set("is_submitted", 1)
        self.db_set("submitted_by", frappe.session.user)


def compile_daily_register():
    outlets = frappe.get_all("Outlet",
        filters={"outlet_type": "Bar", "is_active": 1},
        fields=["name"])
    for outlet in outlets:
        if frappe.db.exists("Excise Register", {"register_date": today(), "outlet": outlet.name}):
            continue
        permit = frappe.db.get_value("Outlet", outlet.name, "name")
        reg = frappe.get_doc({
            "doctype": "Excise Register",
            "register_date": today(),
            "outlet": outlet.name,
            "permit_no": "PENDING",
            "sales_lines": [],
        })
        reg.insert(ignore_permissions=True)
