import frappe
from frappe.model.document import Document


class RatePlan(Document):
    def validate(self):
        if self.valid_from and self.valid_to:
            if self.valid_from > self.valid_to:
                frappe.throw("Valid From date must be before Valid To date.")

    def get_rate_for_room_type(self, room_type):
        for row in self.room_rates:
            if row.room_type == room_type:
                return row.rate_per_night
        return None
