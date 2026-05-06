import frappe
from frappe.model.document import Document


class MenuItem(Document):
    def validate(self):
        self._update_cost_from_bom()
        self._calc_gp()

    def _update_cost_from_bom(self):
        if not self.bom:
            return
        bom_cost = frappe.db.get_value("BOM", self.bom, "total_cost")
        if bom_cost:
            self.cost_price = bom_cost

    def _calc_gp(self):
        if self.price and self.cost_price:
            self.gross_profit_pct = ((self.price - self.cost_price) / self.price) * 100


@frappe.whitelist()
def fetch_bom_cost(menu_item):
    doc = frappe.get_doc("Menu Item", menu_item)
    doc._update_cost_from_bom()
    doc._calc_gp()
    doc.save(ignore_permissions=True)
    return doc.cost_price
