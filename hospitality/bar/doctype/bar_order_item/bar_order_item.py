import frappe
from frappe.model.document import Document


class BarOrderItem(Document):
    def validate(self):
        if self.is_complimentary:
            self.amount = 0
        else:
            self.amount = (self.qty or 0) * (self.rate or 0)
