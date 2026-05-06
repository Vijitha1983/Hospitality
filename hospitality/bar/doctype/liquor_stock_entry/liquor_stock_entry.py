import frappe
from frappe.model.document import Document


class LiquorStockEntry(Document):
    def validate(self):
        self._calculate_variance()

    def _calculate_variance(self):
        total = 0
        for row in self.items:
            row.consumption = (row.opening_qty or 0) - (row.closing_qty or 0)
            row.variance = row.consumption - (row.theoretical_consumption or 0)
            cost = frappe.db.get_value("Item", row.item_code, "valuation_rate") or 0
            total += abs(row.variance) * cost
        self.total_variance = total

    def on_submit(self):
        self.db_set("status", "Submitted")
        check_par_level(self)


def check_par_level(stock_entry):
    from hospitality.utils.stock_utils import check_par_level_and_create_po
    below_par = []
    for row in stock_entry.items:
        par = frappe.db.get_value("Item", row.item_code, "reorder_level") or 0
        if (row.closing_qty or 0) < par:
            supplier = frappe.db.get_value("Item Default",
                {"parent": row.item_code}, "default_supplier")
            below_par.append({
                "item_code": row.item_code,
                "closing_qty": row.closing_qty,
                "par_level": par,
                "supplier": supplier,
            })
    if below_par:
        check_par_level_and_create_po(stock_entry.outlet, below_par)
