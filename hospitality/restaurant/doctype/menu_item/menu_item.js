frappe.ui.form.on("Menu Item", {
    refresh(frm) {
        if (frm.doc.bom) {
            frm.add_custom_button(__("View BOM"), () => {
                frappe.set_route("Form", "BOM", frm.doc.bom);
            });
        }
        frm.add_custom_button(__("Fetch BOM Cost"), () => {
            frappe.call({
                method: "hospitality.restaurant.doctype.menu_item.menu_item.fetch_bom_cost",
                args: { menu_item: frm.doc.name },
                callback(r) { if (r.message !== undefined) frm.reload_doc(); }
            });
        });
    },

    selling_price(frm) { frm.trigger("_calc_gp"); },
    food_cost(frm) { frm.trigger("_calc_gp"); },

    _calc_gp(frm) {
        if (frm.doc.selling_price && frm.doc.food_cost) {
            const gp = ((frm.doc.selling_price - frm.doc.food_cost) / frm.doc.selling_price * 100).toFixed(2);
            frm.set_value("gp_percent", parseFloat(gp));
        }
    }
});
