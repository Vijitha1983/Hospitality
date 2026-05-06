import frappe
from frappe.model.document import Document


class FoodMenu(Document):
    def validate(self):
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            frappe.throw("Valid From must be before Valid To.")
