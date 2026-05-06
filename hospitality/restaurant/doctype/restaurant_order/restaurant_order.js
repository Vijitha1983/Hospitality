frappe.ui.form.on("Restaurant Order", {
    refresh(frm) {
        frm.set_query("table", () => ({
            filters: { outlet: frm.doc.outlet, is_active: 1 }
        }));

        if (!frm.is_new() && frm.doc.status === "Served") {
            frm.add_custom_button(__("Generate Bill"), () => {
                frappe.confirm("Generate POS Invoice for this order?", () => {
                    frappe.call({
                        method: "hospitality.restaurant.doctype.restaurant_order.restaurant_order.create_pos_invoice",
                        args: { order: frm.doc.name },
                        callback(r) { if (r.message) frm.reload_doc(); }
                    });
                });
            });
        }
    },

    outlet(frm) {
        frm.set_query("table", () => ({
            filters: { outlet: frm.doc.outlet, is_active: 1 }
        }));
    }
});

frappe.ui.form.on("KOT Item", {
    menu_item(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.menu_item) {
            frappe.db.get_doc("Menu Item", row.menu_item).then(mi => {
                frappe.model.set_value(cdt, cdn, "item_name", mi.item_name);
                frappe.model.set_value(cdt, cdn, "rate", mi.price);
            });
        }
    },
    qty(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "amount", (row.qty || 0) * (row.rate || 0));
        frm.trigger("_calc_totals");
    },
    _calc_totals(frm) {
        let sub = 0;
        (frm.doc.items || []).forEach(r => { sub += r.amount || 0; });
        frm.set_value("sub_total", sub);
        frm.set_value("total_amount", sub + (frm.doc.tax_amount || 0));
    }
});
