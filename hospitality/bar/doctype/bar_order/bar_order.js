frappe.ui.form.on("Bar Order", {
    refresh(frm) {
        frm.set_query("tab", () => ({
            filters: { outlet: frm.doc.outlet, status: "Open" }
        }));

        if (frm.doc.docstatus === 1 && frm.doc.status === "Served") {
            frm.add_custom_button(__("View BOT"), () => {
                frappe.set_route("List", "BOT", { bar_order: frm.doc.name });
            });
        }
    },

    outlet(frm) {
        frm.set_query("tab", () => ({
            filters: { outlet: frm.doc.outlet, status: "Open" }
        }));
    }
});

frappe.ui.form.on("Bar Order Item", {
    drink_item(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.drink_item) {
            frappe.db.get_doc("Drink Menu Item", row.drink_item).then(di => {
                frappe.model.set_value(cdt, cdn, "rate", di.selling_price);
                frappe.model.set_value(cdt, cdn, "amount", (row.qty || 1) * di.selling_price);
            });
        }
    },
    qty(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.is_complimentary) {
            frappe.model.set_value(cdt, cdn, "amount", (row.qty || 0) * (row.rate || 0));
        }
        frm.trigger("_calc_total");
    },
    is_complimentary(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "amount", row.is_complimentary ? 0 : (row.qty || 0) * (row.rate || 0));
        frm.trigger("_calc_total");
    },
    _calc_total(frm) {
        let total = 0;
        (frm.doc.items || []).forEach(r => { total += r.amount || 0; });
        frm.set_value("total_amount", total);
    }
});
