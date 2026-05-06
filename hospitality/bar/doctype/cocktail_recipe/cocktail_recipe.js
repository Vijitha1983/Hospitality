frappe.ui.form.on("Cocktail Recipe", {
    refresh(frm) {
        if (frm.doc.bom) {
            frm.add_custom_button(__("View BOM"), () => {
                frappe.set_route("Form", "BOM", frm.doc.bom);
            });
        }
        frm.add_custom_button(__("Calculate Cost"), () => {
            frappe.call({
                method: "hospitality.bar.doctype.cocktail_recipe.cocktail_recipe.calculate_cost",
                args: { recipe: frm.doc.name },
                callback(r) { if (r.message !== undefined) frm.reload_doc(); }
            });
        });
    }
});

frappe.ui.form.on("Cocktail Ingredient", {
    qty_ml(frm) { frm.trigger("_calc_cost"); },
    item(frm) { frm.trigger("_calc_cost"); },
    _calc_cost(frm) {
        // Server-side cost calculation triggered on save
    }
});
