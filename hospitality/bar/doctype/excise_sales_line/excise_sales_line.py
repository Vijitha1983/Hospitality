import frappe
from frappe.model.document import Document


class ExciseSalesLine(Document):
    def validate(self):
        self.value = (self.qty_bottles or 0) * (self.rate or 0)
