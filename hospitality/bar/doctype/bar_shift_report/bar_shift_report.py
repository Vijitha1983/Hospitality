import frappe
from frappe.model.document import Document


class BarShiftReport(Document):
    def validate(self):
        expected_cash = (self.opening_cash or 0) + (self.cash_collected or 0)
        self.cash_variance = (self.closing_cash or 0) - expected_cash
