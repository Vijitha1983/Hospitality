frappe.ui.form.on("Drink Menu Item", {
    refresh(frm) {
        if (frm.doc.recipe) {
            frm.add_custom_button(__("View Recipe"), () => {
                frappe.set_route("Form", "Cocktail Recipe", frm.doc.recipe);
            });
        }
    },

    cost_price(frm) { frm.trigger("_calc_gp"); },
    selling_price(frm) { frm.trigger("_calc_gp"); },

    _calc_gp(frm) {
        if (frm.doc.selling_price && frm.doc.cost_price) {
            const gp = ((frm.doc.selling_price - frm.doc.cost_price) / frm.doc.selling_price * 100).toFixed(2);
            frm.set_value("gp_percent", parseFloat(gp));
        }
    }
});
