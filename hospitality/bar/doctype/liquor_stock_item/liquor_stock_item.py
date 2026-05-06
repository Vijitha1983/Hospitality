import frappe
from frappe.model.document import Document


class LiquorStockItem(Document):
    def validate(self):
        self.closing_qty = (self.opening_qty or 0) + (self.received_qty or 0) - (self.sales_qty or 0)
        physical = self.closing_qty
        if self.par_level:
            self.variance = physical - (self.par_level or 0)
