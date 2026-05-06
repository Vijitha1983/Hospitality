import frappe
from frappe.model.document import Document


class CocktailRecipe(Document):
    def validate(self):
        self._update_costs()

    def _update_costs(self):
        if self.bom:
            bom_cost = frappe.db.get_value("BOM", self.bom, "total_cost")
            if bom_cost:
                self.cost_per_serve = bom_cost

        if self.drink_menu_item:
            self.selling_price = frappe.db.get_value("Drink Menu Item", self.drink_menu_item, "price") or 0

        if self.selling_price and self.cost_per_serve:
            self.gp_percent = ((self.selling_price - self.cost_per_serve) / self.selling_price) * 100
