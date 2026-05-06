import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class DrinkMenuItem(Document):
    def validate(self):
        if self.recipe:
            cost = frappe.db.get_value("Cocktail Recipe", self.recipe, "cost_per_serve")
            if cost:
                self.cost_price = cost


def check_happy_hour():
    """Hourly scheduler — set is_happy_hour flag if within happy hour window."""
    pass
