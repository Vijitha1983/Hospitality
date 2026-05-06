import frappe
from frappe.model.document import Document


class RoomType(Document):
    def validate(self):
        if self.base_rate <= 0:
            frappe.throw("Base rate must be greater than zero.")
        if self.max_occupancy <= 0:
            frappe.throw("Max occupancy must be greater than zero.")
