frappe.ui.form.on("Liquor Stock Entry", {
    refresh(frm) {
        frm.set_query("outlet", () => ({
            filters: { outlet_type: "Bar", is_active: 1 }
        }));

        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("View Variance Report"), () => {
                frappe.set_route("query-report", "Bar Variance Report", {
                    from_date: frm.doc.entry_date,
                    to_date: frm.doc.entry_date,
                    outlet: frm.doc.outlet
                });
            });
        }
    }
});

frappe.ui.form.on("Liquor Stock Item", {
    opening_qty(frm, cdt, cdn) { frm.trigger("_calc_row", cdt, cdn); },
    received_qty(frm, cdt, cdn) { frm.trigger("_calc_row", cdt, cdn); },
    sales_qty(frm, cdt, cdn) { frm.trigger("_calc_row", cdt, cdn); },
    _calc_row(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const closing = (row.opening_qty || 0) + (row.received_qty || 0) - (row.sales_qty || 0);
        frappe.model.set_value(cdt, cdn, "closing_qty", closing);
        if (row.par_level) {
            frappe.model.set_value(cdt, cdn, "variance", closing - row.par_level);
        }
    }
});
