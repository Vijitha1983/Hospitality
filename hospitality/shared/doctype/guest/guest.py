import frappe
from frappe.model.document import Document


class Guest(Document):
    def after_insert(self):
        self.create_customer()

    def create_customer(self):
        if self.customer:
            return
        customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": self.full_name,
            "customer_type": "Individual",
            "customer_group": frappe.db.get_single_value("Selling Settings", "customer_group") or "Individual",
            "territory": frappe.db.get_single_value("Selling Settings", "territory") or "All Territories",
            "mobile_no": self.mobile,
            "email_id": self.email or "",
        })
        customer.insert(ignore_permissions=True)
        self.db_set("customer", customer.name)

    def on_update(self):
        self._update_loyalty_tier()

    def _update_loyalty_tier(self):
        points = self.loyalty_points or 0
        if points >= 10000:
            tier = "Platinum"
        elif points >= 5000:
            tier = "Gold"
        elif points >= 1000:
            tier = "Silver"
        else:
            tier = "Standard"
        if self.loyalty_tier != tier:
            self.db_set("loyalty_tier", tier)
