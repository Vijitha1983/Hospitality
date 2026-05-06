frappe.ui.form.on("Bar Shift Report", {
    refresh(frm) {
        frm.set_query("outlet", () => ({
            filters: { outlet_type: "Bar", is_active: 1 }
        }));
        frm.set_query("bartender", () => ({
            filters: { status: "Active" }
        }));
    },

    opening_cash(frm) { frm.trigger("_calc_variance"); },
    cash_collected(frm) { frm.trigger("_calc_variance"); },
    closing_cash(frm) { frm.trigger("_calc_variance"); },

    _calc_variance(frm) {
        const expected = (frm.doc.opening_cash || 0) + (frm.doc.cash_collected || 0);
        frm.set_value("cash_variance", (frm.doc.closing_cash || 0) - expected);
    }
});
